"""
CryptoSphere Analytics Platform - Pipeline Orchestrator
======================================================

Main orchestration engine for the entire cryptocurrency analytics pipeline.
Manages data acquisition, processing, ML model training, and reporting workflows.

Features:
- Multi-stage pipeline execution with dependency management
- Error handling and retry mechanisms
- Resource monitoring and optimization
- Parallel processing capabilities
- Integration with external systems (APIs, databases, ML platforms)

Author: CryptoSphere Analytics Team
Created: 2025-10-07
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json
import yaml

import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Import custom modules
from ..02-monitoring.health_monitor import HealthMonitor
from ..03-alerting.alert_manager import AlertManager
from ..04-deployment.deployment_manager import DeploymentManager
from ...config.config_manager import ConfigManager


class PipelineStatus(Enum):
    """Pipeline execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """Individual task definition within a pipeline."""
    id: str
    name: str
    function: Callable
    dependencies: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout: int = 300  # seconds
    retry_count: int = 3
    retry_delay: int = 60  # seconds
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: PipelineStatus = PipelineStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Any = None


@dataclass
class Pipeline:
    """Pipeline definition containing multiple tasks."""
    id: str
    name: str
    description: str
    tasks: List[Task] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    success_count: int = 0
    failure_count: int = 0


class PipelineOrchestrator:
    """
    Main orchestrator for managing cryptocurrency analytics pipelines.
    
    Coordinates data acquisition, processing, ML training, and reporting workflows
    with advanced scheduling, monitoring, and error handling capabilities.
    """
    
    def __init__(self, config_path: str = "config/main_config.yaml"):
        """Initialize the pipeline orchestrator."""
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Initialize logging
        self.logger = self._setup_logging()
        
        # Initialize components
        self.scheduler = AsyncIOScheduler()
        self.health_monitor = HealthMonitor(self.config)
        self.alert_manager = AlertManager(self.config)
        self.deployment_manager = DeploymentManager(self.config)
        
        # Pipeline management
        self.pipelines: Dict[str, Pipeline] = {}
        self.active_pipelines: Dict[str, asyncio.Task] = {}
        
        # Execution pools
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.get('orchestrator', {}).get('max_threads', 10)
        )
        self.process_pool = ProcessPoolExecutor(
            max_workers=self.config.get('orchestrator', {}).get('max_processes', 4)
        )
        
        # Database connections
        self.db_engine = self._create_db_engine()
        
        # Performance metrics
        self.metrics = {
            'pipelines_executed': 0,
            'tasks_completed': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0,
            'success_rate': 0.0,
            'last_execution': None
        }
        
        self.logger.info("Pipeline Orchestrator initialized successfully")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('pipeline_orchestrator')
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            # Set log level from config
            log_level = self.config.get('logging', {}).get('level', 'INFO')
            logger.setLevel(getattr(logging, log_level))
        
        return logger
    
    def _create_db_engine(self):
        """Create database engine for pipeline metadata."""
        db_config = self.config.get('database', {})
        connection_string = (
            f"postgresql://{db_config.get('user')}:{db_config.get('password')}"
            f"@{db_config.get('host')}:{db_config.get('port')}/{db_config.get('database')}"
        )
        return create_engine(connection_string)
    
    def register_pipeline(self, pipeline: Pipeline) -> None:
        """Register a new pipeline for orchestration."""
        self.pipelines[pipeline.id] = pipeline
        self.logger.info(f"Registered pipeline: {pipeline.name} ({pipeline.id})")
    
    def create_data_acquisition_pipeline(self) -> Pipeline:
        """Create the main data acquisition pipeline."""
        pipeline = Pipeline(
            id="data_acquisition",
            name="Cryptocurrency Data Acquisition",
            description="Fetches cryptocurrency data from CoinMarketCap API and stores in Bronze layer"
        )
        
        # Task 1: API Health Check
        api_health_task = Task(
            id="api_health_check",
            name="API Health Check",
            function=self._check_api_health,
            priority=TaskPriority.HIGH,
            timeout=30
        )
        
        # Task 2: Fetch Cryptocurrency Listings
        fetch_listings_task = Task(
            id="fetch_listings",
            name="Fetch Cryptocurrency Listings",
            function=self._fetch_crypto_listings,
            dependencies=["api_health_check"],
            priority=TaskPriority.HIGH,
            timeout=120
        )
        
        # Task 3: Fetch Quote Data
        fetch_quotes_task = Task(
            id="fetch_quotes",
            name="Fetch Cryptocurrency Quotes",
            function=self._fetch_crypto_quotes,
            dependencies=["fetch_listings"],
            priority=TaskPriority.HIGH,
            timeout=180
        )
        
        # Task 4: Data Validation
        validation_task = Task(
            id="data_validation",
            name="Validate Raw Data",
            function=self._validate_raw_data,
            dependencies=["fetch_quotes"],
            priority=TaskPriority.MEDIUM,
            timeout=60
        )
        
        pipeline.tasks = [api_health_task, fetch_listings_task, fetch_quotes_task, validation_task]
        return pipeline
    
    def create_data_processing_pipeline(self) -> Pipeline:
        """Create the data processing pipeline (Bronze -> Silver -> Gold)."""
        pipeline = Pipeline(
            id="data_processing",
            name="Data Processing Pipeline",
            description="Processes raw data through Bronze, Silver, and Gold layers"
        )
        
        # Task 1: Bronze to Silver ETL
        bronze_to_silver_task = Task(
            id="bronze_to_silver",
            name="Bronze to Silver ETL",
            function=self._run_bronze_to_silver_etl,
            priority=TaskPriority.HIGH,
            timeout=300
        )
        
        # Task 2: Data Quality Assessment
        quality_assessment_task = Task(
            id="quality_assessment",
            name="Data Quality Assessment",
            function=self._assess_data_quality,
            dependencies=["bronze_to_silver"],
            priority=TaskPriority.MEDIUM,
            timeout=120
        )
        
        # Task 3: Silver to Gold ETL
        silver_to_gold_task = Task(
            id="silver_to_gold",
            name="Silver to Gold ETL",
            function=self._run_silver_to_gold_etl,
            dependencies=["quality_assessment"],
            priority=TaskPriority.HIGH,
            timeout=600
        )
        
        # Task 4: Generate Analytics
        analytics_task = Task(
            id="generate_analytics",
            name="Generate Analytics",
            function=self._generate_analytics,
            dependencies=["silver_to_gold"],
            priority=TaskPriority.MEDIUM,
            timeout=300
        )
        
        pipeline.tasks = [bronze_to_silver_task, quality_assessment_task, silver_to_gold_task, analytics_task]
        return pipeline
    
    def create_ml_pipeline(self) -> Pipeline:
        """Create the machine learning pipeline."""
        pipeline = Pipeline(
            id="ml_pipeline",
            name="Machine Learning Pipeline",
            description="Trains and deploys ML models for cryptocurrency prediction"
        )
        
        # Task 1: Feature Engineering
        feature_engineering_task = Task(
            id="feature_engineering",
            name="Feature Engineering",
            function=self._run_feature_engineering,
            priority=TaskPriority.HIGH,
            timeout=300
        )
        
        # Task 2: Model Training
        model_training_task = Task(
            id="model_training",
            name="Model Training",
            function=self._train_models,
            dependencies=["feature_engineering"],
            priority=TaskPriority.HIGH,
            timeout=1800  # 30 minutes
        )
        
        # Task 3: Model Evaluation
        model_evaluation_task = Task(
            id="model_evaluation",
            name="Model Evaluation",
            function=self._evaluate_models,
            dependencies=["model_training"],
            priority=TaskPriority.HIGH,
            timeout=300
        )
        
        # Task 4: Model Deployment
        model_deployment_task = Task(
            id="model_deployment",
            name="Model Deployment",
            function=self._deploy_models,
            dependencies=["model_evaluation"],
            priority=TaskPriority.CRITICAL,
            timeout=180
        )
        
        pipeline.tasks = [feature_engineering_task, model_training_task, model_evaluation_task, model_deployment_task]
        return pipeline
    
    async def execute_pipeline(self, pipeline_id: str) -> bool:
        """Execute a specific pipeline."""
        if pipeline_id not in self.pipelines:
            self.logger.error(f"Pipeline {pipeline_id} not found")
            return False
        
        pipeline = self.pipelines[pipeline_id]
        pipeline.status = PipelineStatus.RUNNING
        pipeline.start_time = datetime.now()
        
        self.logger.info(f"Starting pipeline execution: {pipeline.name}")
        
        try:
            # Execute tasks based on dependencies
            completed_tasks = set()
            
            while len(completed_tasks) < len(pipeline.tasks):
                # Find tasks ready to execute
                ready_tasks = [
                    task for task in pipeline.tasks
                    if task.status == PipelineStatus.PENDING
                    and all(dep in completed_tasks for dep in task.dependencies)
                ]
                
                if not ready_tasks:
                    # Check if we're stuck (circular dependencies or all remaining tasks failed)
                    remaining_tasks = [
                        task for task in pipeline.tasks
                        if task.status not in [PipelineStatus.SUCCESS, PipelineStatus.FAILED]
                    ]
                    
                    if remaining_tasks:
                        self.logger.error("Pipeline stuck - possible circular dependencies or all tasks failed")
                        pipeline.status = PipelineStatus.FAILED
                        return False
                    break
                
                # Execute ready tasks in parallel
                task_futures = []
                for task in ready_tasks:
                    future = asyncio.create_task(self._execute_task(task))
                    task_futures.append((task, future))
                
                # Wait for tasks to complete
                for task, future in task_futures:
                    try:
                        success = await future
                        if success:
                            completed_tasks.add(task.id)
                            pipeline.success_count += 1
                        else:
                            pipeline.failure_count += 1
                            
                            # Check if this is a critical task
                            if task.priority == TaskPriority.CRITICAL:
                                self.logger.error(f"Critical task {task.name} failed - stopping pipeline")
                                pipeline.status = PipelineStatus.FAILED
                                return False
                                
                    except Exception as e:
                        self.logger.error(f"Task {task.name} execution error: {str(e)}")
                        pipeline.failure_count += 1
            
            pipeline.status = PipelineStatus.SUCCESS
            pipeline.end_time = datetime.now()
            pipeline.total_duration = (pipeline.end_time - pipeline.start_time).total_seconds()
            
            self.logger.info(f"Pipeline {pipeline.name} completed successfully in {pipeline.total_duration:.2f} seconds")
            
            # Update metrics
            self._update_metrics(pipeline)
            
            # Send success notification
            await self.alert_manager.send_notification(
                "Pipeline Success",
                f"Pipeline {pipeline.name} completed successfully",
                "info"
            )
            
            return True
            
        except Exception as e:
            pipeline.status = PipelineStatus.FAILED
            pipeline.end_time = datetime.now()
            self.logger.error(f"Pipeline {pipeline.name} failed: {str(e)}")
            
            # Send failure alert
            await self.alert_manager.send_alert(
                "Pipeline Failure",
                f"Pipeline {pipeline.name} failed: {str(e)}",
                "error"
            )
            
            return False
    
    async def _execute_task(self, task: Task) -> bool:
        """Execute an individual task with retry logic."""
        task.status = PipelineStatus.RUNNING
        task.start_time = datetime.now()
        
        self.logger.info(f"Executing task: {task.name}")
        
        for attempt in range(task.retry_count + 1):
            try:
                # Execute task function
                if asyncio.iscoroutinefunction(task.function):
                    result = await task.function(**task.parameters)
                else:
                    # Run in thread pool for sync functions
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.thread_pool, 
                        lambda: task.function(**task.parameters)
                    )
                
                task.result = result
                task.status = PipelineStatus.SUCCESS
                task.end_time = datetime.now()
                
                self.logger.info(f"Task {task.name} completed successfully")
                return True
                
            except Exception as e:
                task.error_message = str(e)
                
                if attempt < task.retry_count:
                    self.logger.warning(f"Task {task.name} failed (attempt {attempt + 1}), retrying in {task.retry_delay}s")
                    task.status = PipelineStatus.RETRYING
                    await asyncio.sleep(task.retry_delay)
                else:
                    task.status = PipelineStatus.FAILED
                    task.end_time = datetime.now()
                    self.logger.error(f"Task {task.name} failed after {task.retry_count} retries: {str(e)}")
                    return False
        
        return False
    
    def schedule_pipeline(self, pipeline_id: str, cron_expression: str) -> None:
        """Schedule a pipeline to run on a cron schedule."""
        if pipeline_id not in self.pipelines:
            self.logger.error(f"Cannot schedule unknown pipeline: {pipeline_id}")
            return
        
        trigger = CronTrigger.from_crontab(cron_expression)
        
        self.scheduler.add_job(
            func=self.execute_pipeline,
            args=[pipeline_id],
            trigger=trigger,
            id=f"pipeline_{pipeline_id}",
            replace_existing=True
        )
        
        self.logger.info(f"Scheduled pipeline {pipeline_id} with cron: {cron_expression}")
    
    def schedule_interval_pipeline(self, pipeline_id: str, interval_minutes: int) -> None:
        """Schedule a pipeline to run at regular intervals."""
        if pipeline_id not in self.pipelines:
            self.logger.error(f"Cannot schedule unknown pipeline: {pipeline_id}")
            return
        
        trigger = IntervalTrigger(minutes=interval_minutes)
        
        self.scheduler.add_job(
            func=self.execute_pipeline,
            args=[pipeline_id],
            trigger=trigger,
            id=f"pipeline_{pipeline_id}",
            replace_existing=True
        )
        
        self.logger.info(f"Scheduled pipeline {pipeline_id} every {interval_minutes} minutes")
    
    def start_scheduler(self) -> None:
        """Start the pipeline scheduler."""
        self.scheduler.start()
        self.logger.info("Pipeline scheduler started")
    
    def stop_scheduler(self) -> None:
        """Stop the pipeline scheduler."""
        self.scheduler.shutdown()
        self.logger.info("Pipeline scheduler stopped")
    
    def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """Get the current status of a pipeline."""
        if pipeline_id not in self.pipelines:
            return {"error": "Pipeline not found"}
        
        pipeline = self.pipelines[pipeline_id]
        
        return {
            "id": pipeline.id,
            "name": pipeline.name,
            "status": pipeline.status.value,
            "start_time": pipeline.start_time.isoformat() if pipeline.start_time else None,
            "end_time": pipeline.end_time.isoformat() if pipeline.end_time else None,
            "duration": pipeline.total_duration,
            "success_count": pipeline.success_count,
            "failure_count": pipeline.failure_count,
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status.value,
                    "error_message": task.error_message
                }
                for task in pipeline.tasks
            ]
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        return {
            "orchestrator_metrics": self.metrics,
            "health_status": self.health_monitor.get_health_status(),
            "active_pipelines": len(self.active_pipelines),
            "scheduled_jobs": len(self.scheduler.get_jobs()),
            "thread_pool_active": self.thread_pool._threads,
            "process_pool_active": len(self.process_pool._processes) if hasattr(self.process_pool, '_processes') else 0
        }
    
    def _update_metrics(self, pipeline: Pipeline) -> None:
        """Update orchestrator performance metrics."""
        self.metrics['pipelines_executed'] += 1
        self.metrics['tasks_completed'] += pipeline.success_count
        self.metrics['total_execution_time'] += pipeline.total_duration or 0
        self.metrics['average_execution_time'] = (
            self.metrics['total_execution_time'] / self.metrics['pipelines_executed']
        )
        self.metrics['success_rate'] = (
            (self.metrics['pipelines_executed'] - pipeline.failure_count) / 
            self.metrics['pipelines_executed'] * 100
        )
        self.metrics['last_execution'] = datetime.now().isoformat()
    
    # Task Implementation Methods
    async def _check_api_health(self) -> bool:
        """Check CoinMarketCap API health."""
        try:
            api_config = self.config.get('coinmarketcap_api', {})
            headers = {'X-CMC_PRO_API_KEY': api_config.get('api_key')}
            
            response = requests.get(
                f"{api_config.get('base_url')}/v1/key/info",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("API health check passed")
                return True
            else:
                self.logger.error(f"API health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"API health check error: {str(e)}")
            return False
    
    async def _fetch_crypto_listings(self) -> bool:
        """Fetch cryptocurrency listings from API."""
        # Implementation would call the API client
        self.logger.info("Fetching cryptocurrency listings")
        await asyncio.sleep(2)  # Simulate API call
        return True
    
    async def _fetch_crypto_quotes(self) -> bool:
        """Fetch cryptocurrency quotes from API."""
        # Implementation would call the API client
        self.logger.info("Fetching cryptocurrency quotes")
        await asyncio.sleep(3)  # Simulate API call
        return True
    
    async def _validate_raw_data(self) -> bool:
        """Validate raw data in Bronze layer."""
        # Implementation would run data validation
        self.logger.info("Validating raw data")
        await asyncio.sleep(1)  # Simulate validation
        return True
    
    async def _run_bronze_to_silver_etl(self) -> bool:
        """Run Bronze to Silver ETL process."""
        # Implementation would execute SQL procedures
        self.logger.info("Running Bronze to Silver ETL")
        await asyncio.sleep(5)  # Simulate ETL
        return True
    
    async def _assess_data_quality(self) -> bool:
        """Assess data quality in Silver layer."""
        # Implementation would run quality checks
        self.logger.info("Assessing data quality")
        await asyncio.sleep(2)  # Simulate quality assessment
        return True
    
    async def _run_silver_to_gold_etl(self) -> bool:
        """Run Silver to Gold ETL process."""
        # Implementation would execute analytical procedures
        self.logger.info("Running Silver to Gold ETL")
        await asyncio.sleep(8)  # Simulate complex ETL
        return True
    
    async def _generate_analytics(self) -> bool:
        """Generate analytics and reports."""
        # Implementation would create reports and dashboards
        self.logger.info("Generating analytics")
        await asyncio.sleep(3)  # Simulate analytics generation
        return True
    
    async def _run_feature_engineering(self) -> bool:
        """Run feature engineering for ML."""
        # Implementation would create ML features
        self.logger.info("Running feature engineering")
        await asyncio.sleep(4)  # Simulate feature engineering
        return True
    
    async def _train_models(self) -> bool:
        """Train ML models."""
        # Implementation would train various ML models
        self.logger.info("Training ML models")
        await asyncio.sleep(15)  # Simulate model training
        return True
    
    async def _evaluate_models(self) -> bool:
        """Evaluate trained ML models."""
        # Implementation would evaluate model performance
        self.logger.info("Evaluating ML models")
        await asyncio.sleep(3)  # Simulate model evaluation
        return True
    
    async def _deploy_models(self) -> bool:
        """Deploy ML models to production."""
        # Implementation would deploy models
        self.logger.info("Deploying ML models")
        await asyncio.sleep(2)  # Simulate model deployment
        return True


async def main():
    """Main function to demonstrate pipeline orchestration."""
    # Initialize orchestrator
    orchestrator = PipelineOrchestrator()
    
    # Create and register pipelines
    data_acquisition_pipeline = orchestrator.create_data_acquisition_pipeline()
    data_processing_pipeline = orchestrator.create_data_processing_pipeline()
    ml_pipeline = orchestrator.create_ml_pipeline()
    
    orchestrator.register_pipeline(data_acquisition_pipeline)
    orchestrator.register_pipeline(data_processing_pipeline)
    orchestrator.register_pipeline(ml_pipeline)
    
    # Schedule pipelines
    orchestrator.schedule_interval_pipeline("data_acquisition", 15)  # Every 15 minutes
    orchestrator.schedule_pipeline("data_processing", "0 */2 * * *")  # Every 2 hours
    orchestrator.schedule_pipeline("ml_pipeline", "0 6 * * *")  # Daily at 6 AM
    
    # Start scheduler
    orchestrator.start_scheduler()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(60)  # Check every minute
            metrics = orchestrator.get_system_metrics()
            print(f"System Status: {metrics}")
    except KeyboardInterrupt:
        print("Shutting down orchestrator...")
        orchestrator.stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())

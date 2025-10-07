"""
CryptoSphere Analytics Platform - Deployment Manager
====================================================

Automated deployment management for the cryptocurrency analytics platform.
Handles model deployment, configuration updates, service management, and rollback procedures.

Features:
- ML model deployment automation
- Configuration management
- Service health monitoring during deployment
- Rollback capabilities
- Blue-green deployment support
- Container orchestration integration

Author: CryptoSphere Analytics Team
Created: 2025-10-07
"""

import asyncio
import logging
import os
import json
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import tempfile
import tarfile
import hashlib

import docker
import yaml


class DeploymentStatus(Enum):
    """Deployment status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeploymentStrategy(Enum):
    """Deployment strategy options."""
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    IMMEDIATE = "immediate"


@dataclass
class DeploymentArtifact:
    """Deployment artifact definition."""
    name: str
    version: str
    artifact_type: str  # 'model', 'config', 'service'
    file_path: str
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DeploymentJob:
    """Deployment job definition."""
    id: str
    name: str
    artifacts: List[DeploymentArtifact]
    strategy: DeploymentStrategy
    target_environment: str
    status: DeploymentStatus = DeploymentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    rollback_info: Optional[Dict[str, Any]] = None


class DeploymentManager:
    """
    Comprehensive deployment management system for the CryptoSphere Analytics Platform.
    
    Manages automated deployment of ML models, configuration updates, and service deployments
    with support for multiple deployment strategies and rollback capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the deployment manager."""
        self.config = config
        self.logger = self._setup_logging()
        
        # Deployment configuration
        self.deployment_config = config.get('deployment', {})
        self.environments = self.deployment_config.get('environments', {})
        
        # Storage paths
        self.artifact_storage = self.deployment_config.get('artifact_storage', './artifacts')
        self.backup_storage = self.deployment_config.get('backup_storage', './backups')
        
        # Create storage directories
        os.makedirs(self.artifact_storage, exist_ok=True)
        os.makedirs(self.backup_storage, exist_ok=True)
        
        # Job tracking
        self.active_deployments: Dict[str, DeploymentJob] = {}
        self.deployment_history: List[DeploymentJob] = []
        
        # Docker client (if using containers)
        self.docker_client = None
        if self.deployment_config.get('use_docker', False):
            try:
                self.docker_client = docker.from_env()
                self.logger.info("Docker client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Docker client: {str(e)}")
        
        # Model registry configuration
        self.model_registry = self.deployment_config.get('model_registry', {})
        
        self.logger.info("Deployment Manager initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('deployment_manager')
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _generate_deployment_id(self) -> str:
        """Generate unique deployment ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
        return f"deploy_{timestamp}_{random_suffix}"
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file."""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def create_model_artifact(self, 
                            model_name: str, 
                            model_version: str, 
                            model_path: str,
                            metadata: Optional[Dict[str, Any]] = None) -> DeploymentArtifact:
        """Create a deployment artifact for an ML model."""
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Calculate checksum
        checksum = self._calculate_checksum(model_path)
        
        # Create artifact
        artifact = DeploymentArtifact(
            name=model_name,
            version=model_version,
            artifact_type="model",
            file_path=model_path,
            checksum=checksum,
            metadata=metadata or {}
        )
        
        # Copy to artifact storage
        artifact_filename = f"{model_name}_{model_version}_{checksum[:8]}.pkl"
        artifact_storage_path = os.path.join(self.artifact_storage, artifact_filename)
        shutil.copy2(model_path, artifact_storage_path)
        
        artifact.file_path = artifact_storage_path
        
        self.logger.info(f"Created model artifact: {model_name} v{model_version}")
        return artifact
    
    def create_config_artifact(self, 
                             config_name: str, 
                             config_version: str, 
                             config_data: Dict[str, Any]) -> DeploymentArtifact:
        """Create a deployment artifact for configuration."""
        
        # Save configuration to temporary file
        config_filename = f"{config_name}_{config_version}.yaml"
        config_path = os.path.join(self.artifact_storage, config_filename)
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        # Calculate checksum
        checksum = self._calculate_checksum(config_path)
        
        artifact = DeploymentArtifact(
            name=config_name,
            version=config_version,
            artifact_type="config",
            file_path=config_path,
            checksum=checksum,
            metadata={'config_keys': list(config_data.keys())}
        )
        
        self.logger.info(f"Created config artifact: {config_name} v{config_version}")
        return artifact
    
    async def deploy_models(self, 
                           artifacts: List[DeploymentArtifact],
                           environment: str = "production",
                           strategy: DeploymentStrategy = DeploymentStrategy.ROLLING) -> str:
        """Deploy ML models to the specified environment."""
        
        deployment_id = self._generate_deployment_id()
        
        # Create deployment job
        job = DeploymentJob(
            id=deployment_id,
            name=f"Model Deployment - {environment}",
            artifacts=artifacts,
            strategy=strategy,
            target_environment=environment
        )
        
        self.active_deployments[deployment_id] = job
        
        try:
            job.status = DeploymentStatus.IN_PROGRESS
            job.started_at = datetime.now()
            
            self.logger.info(f"Starting model deployment {deployment_id} to {environment}")
            
            # Backup current models
            backup_info = await self._backup_current_models(environment)
            job.rollback_info = backup_info
            
            # Deploy based on strategy
            if strategy == DeploymentStrategy.ROLLING:
                await self._deploy_rolling(job)
            elif strategy == DeploymentStrategy.BLUE_GREEN:
                await self._deploy_blue_green(job)
            elif strategy == DeploymentStrategy.IMMEDIATE:
                await self._deploy_immediate(job)
            else:
                raise ValueError(f"Unsupported deployment strategy: {strategy}")
            
            job.status = DeploymentStatus.COMPLETED
            job.completed_at = datetime.now()
            
            self.logger.info(f"Model deployment {deployment_id} completed successfully")
            
            # Send deployment notification
            await self._send_deployment_notification(job, "success")
            
        except Exception as e:
            job.status = DeploymentStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            
            self.logger.error(f"Model deployment {deployment_id} failed: {str(e)}")
            
            # Send failure notification
            await self._send_deployment_notification(job, "failure")
            
            raise
        
        finally:
            # Move to history
            self.deployment_history.append(job)
            if deployment_id in self.active_deployments:
                del self.active_deployments[deployment_id]
        
        return deployment_id
    
    async def _backup_current_models(self, environment: str) -> Dict[str, Any]:
        """Backup current models before deployment."""
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(self.backup_storage, backup_id)
        os.makedirs(backup_path, exist_ok=True)
        
        env_config = self.environments.get(environment, {})
        model_directory = env_config.get('model_directory', './models')
        
        if os.path.exists(model_directory):
            # Create tar archive of current models
            backup_archive = os.path.join(backup_path, 'models_backup.tar.gz')
            
            with tarfile.open(backup_archive, 'w:gz') as tar:
                tar.add(model_directory, arcname='models')
            
            backup_info = {
                'backup_id': backup_id,
                'backup_path': backup_archive,
                'environment': environment,
                'created_at': datetime.now().isoformat(),
                'model_directory': model_directory
            }
            
            # Save backup metadata
            metadata_path = os.path.join(backup_path, 'backup_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            self.logger.info(f"Created backup {backup_id} for environment {environment}")
            return backup_info
        
        return {'backup_id': backup_id, 'message': 'No existing models to backup'}
    
    async def _deploy_rolling(self, job: DeploymentJob) -> None:
        """Execute rolling deployment strategy."""
        self.logger.info(f"Executing rolling deployment for job {job.id}")
        
        env_config = self.environments.get(job.target_environment, {})
        model_directory = env_config.get('model_directory', './models')
        
        # Ensure model directory exists
        os.makedirs(model_directory, exist_ok=True)
        
        # Deploy each artifact
        for artifact in job.artifacts:
            if artifact.artifact_type == "model":
                await self._deploy_model_artifact(artifact, model_directory)
            elif artifact.artifact_type == "config":
                await self._deploy_config_artifact(artifact, env_config)
        
        # Restart services if configured
        if env_config.get('auto_restart_services', False):
            await self._restart_services(job.target_environment)
        
        # Health check
        await self._perform_health_check(job.target_environment)
    
    async def _deploy_blue_green(self, job: DeploymentJob) -> None:
        """Execute blue-green deployment strategy."""
        self.logger.info(f"Executing blue-green deployment for job {job.id}")
        
        env_config = self.environments.get(job.target_environment, {})
        
        # Create green environment
        green_directory = env_config.get('model_directory', './models') + '_green'
        os.makedirs(green_directory, exist_ok=True)
        
        # Deploy to green environment
        for artifact in job.artifacts:
            if artifact.artifact_type == "model":
                await self._deploy_model_artifact(artifact, green_directory)
        
        # Health check on green environment
        await self._perform_health_check(job.target_environment, green_directory)
        
        # Switch blue and green
        blue_directory = env_config.get('model_directory', './models')
        temp_directory = blue_directory + '_temp'
        
        if os.path.exists(blue_directory):
            os.rename(blue_directory, temp_directory)
        
        os.rename(green_directory, blue_directory)
        
        if os.path.exists(temp_directory):
            shutil.rmtree(temp_directory)
        
        self.logger.info("Blue-green switch completed")
    
    async def _deploy_immediate(self, job: DeploymentJob) -> None:
        """Execute immediate deployment strategy."""
        self.logger.info(f"Executing immediate deployment for job {job.id}")
        
        env_config = self.environments.get(job.target_environment, {})
        model_directory = env_config.get('model_directory', './models')
        
        # Ensure model directory exists
        os.makedirs(model_directory, exist_ok=True)
        
        # Deploy all artifacts immediately
        for artifact in job.artifacts:
            if artifact.artifact_type == "model":
                await self._deploy_model_artifact(artifact, model_directory)
            elif artifact.artifact_type == "config":
                await self._deploy_config_artifact(artifact, env_config)
        
        # Quick health check
        await self._perform_health_check(job.target_environment)
    
    async def _deploy_model_artifact(self, artifact: DeploymentArtifact, target_directory: str) -> None:
        """Deploy a model artifact to the target directory."""
        target_path = os.path.join(target_directory, f"{artifact.name}_v{artifact.version}.pkl")
        
        # Verify checksum before deployment
        current_checksum = self._calculate_checksum(artifact.file_path)
        if current_checksum != artifact.checksum:
            raise ValueError(f"Checksum mismatch for artifact {artifact.name}")
        
        # Copy model file
        shutil.copy2(artifact.file_path, target_path)
        
        # Create/update symbolic link for latest version
        latest_link = os.path.join(target_directory, f"{artifact.name}_latest.pkl")
        if os.path.exists(latest_link):
            os.remove(latest_link)
        os.symlink(os.path.basename(target_path), latest_link)
        
        # Save artifact metadata
        metadata_path = os.path.join(target_directory, f"{artifact.name}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump({
                'name': artifact.name,
                'version': artifact.version,
                'checksum': artifact.checksum,
                'deployed_at': datetime.now().isoformat(),
                'metadata': artifact.metadata
            }, f, indent=2)
        
        self.logger.info(f"Deployed model artifact: {artifact.name} v{artifact.version}")
    
    async def _deploy_config_artifact(self, artifact: DeploymentArtifact, env_config: Dict[str, Any]) -> None:
        """Deploy a configuration artifact."""
        config_directory = env_config.get('config_directory', './config')
        os.makedirs(config_directory, exist_ok=True)
        
        target_path = os.path.join(config_directory, f"{artifact.name}.yaml")
        
        # Copy configuration file
        shutil.copy2(artifact.file_path, target_path)
        
        self.logger.info(f"Deployed config artifact: {artifact.name} v{artifact.version}")
    
    async def _restart_services(self, environment: str) -> None:
        """Restart services in the specified environment."""
        env_config = self.environments.get(environment, {})
        services = env_config.get('services', [])
        
        for service in services:
            try:
                if self.docker_client and service.get('type') == 'docker':
                    # Restart Docker container
                    container = self.docker_client.containers.get(service.get('name'))
                    container.restart()
                    self.logger.info(f"Restarted Docker service: {service.get('name')}")
                
                elif service.get('type') == 'systemd':
                    # Restart systemd service
                    result = subprocess.run([
                        'systemctl', 'restart', service.get('name')
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.logger.info(f"Restarted systemd service: {service.get('name')}")
                    else:
                        self.logger.error(f"Failed to restart service {service.get('name')}: {result.stderr}")
                
                elif service.get('type') == 'process':
                    # Restart process using custom command
                    restart_command = service.get('restart_command', [])
                    if restart_command:
                        result = subprocess.run(restart_command, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            self.logger.info(f"Restarted process service: {service.get('name')}")
                        else:
                            self.logger.error(f"Failed to restart service {service.get('name')}: {result.stderr}")
                
            except Exception as e:
                self.logger.error(f"Error restarting service {service.get('name')}: {str(e)}")
    
    async def _perform_health_check(self, environment: str, model_directory: Optional[str] = None) -> None:
        """Perform health check after deployment."""
        env_config = self.environments.get(environment, {})
        health_check_config = env_config.get('health_check', {})
        
        if not health_check_config.get('enabled', True):
            return
        
        # Check if models are loadable
        check_directory = model_directory or env_config.get('model_directory', './models')
        
        if os.path.exists(check_directory):
            model_files = [f for f in os.listdir(check_directory) if f.endswith('.pkl')]
            
            for model_file in model_files:
                model_path = os.path.join(check_directory, model_file)
                try:
                    # Basic check - ensure file is readable
                    with open(model_path, 'rb') as f:
                        f.read(1024)  # Read first 1KB
                    
                    self.logger.info(f"Health check passed for model: {model_file}")
                    
                except Exception as e:
                    raise RuntimeError(f"Health check failed for model {model_file}: {str(e)}")
        
        # Additional health checks can be added here
        await asyncio.sleep(health_check_config.get('delay_seconds', 5))
    
    async def rollback_deployment(self, deployment_id: str) -> bool:
        """Rollback a deployment to the previous state."""
        # Find deployment in history
        deployment = None
        for job in self.deployment_history:
            if job.id == deployment_id:
                deployment = job
                break
        
        if not deployment or not deployment.rollback_info:
            self.logger.error(f"Cannot rollback deployment {deployment_id}: no backup info found")
            return False
        
        try:
            self.logger.info(f"Starting rollback for deployment {deployment_id}")
            
            backup_info = deployment.rollback_info
            env_config = self.environments.get(deployment.target_environment, {})
            model_directory = env_config.get('model_directory', './models')
            
            # Remove current models
            if os.path.exists(model_directory):
                shutil.rmtree(model_directory)
            
            # Restore from backup
            if os.path.exists(backup_info.get('backup_path', '')):
                with tarfile.open(backup_info['backup_path'], 'r:gz') as tar:
                    tar.extractall(path=os.path.dirname(model_directory))
            
            # Restart services
            if env_config.get('auto_restart_services', False):
                await self._restart_services(deployment.target_environment)
            
            # Update deployment status
            deployment.status = DeploymentStatus.ROLLED_BACK
            
            self.logger.info(f"Rollback completed for deployment {deployment_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed for deployment {deployment_id}: {str(e)}")
            return False
    
    async def _send_deployment_notification(self, job: DeploymentJob, status: str) -> None:
        """Send deployment notification."""
        # This would integrate with the AlertManager
        message = f"Deployment {job.id} {status}"
        
        if status == "success":
            self.logger.info(f"✅ {message}")
        else:
            self.logger.error(f"❌ {message}: {job.error_message}")
    
    def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific deployment."""
        # Check active deployments
        if deployment_id in self.active_deployments:
            job = self.active_deployments[deployment_id]
        else:
            # Check deployment history
            job = None
            for historical_job in self.deployment_history:
                if historical_job.id == deployment_id:
                    job = historical_job
                    break
            
            if not job:
                return None
        
        return {
            'id': job.id,
            'name': job.name,
            'status': job.status.value,
            'strategy': job.strategy.value,
            'environment': job.target_environment,
            'artifacts': [
                {
                    'name': artifact.name,
                    'version': artifact.version,
                    'type': artifact.artifact_type,
                    'checksum': artifact.checksum
                }
                for artifact in job.artifacts
            ],
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error_message': job.error_message,
            'has_rollback_info': bool(job.rollback_info)
        }
    
    def get_deployment_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get deployment history."""
        recent_deployments = sorted(
            self.deployment_history, 
            key=lambda x: x.created_at, 
            reverse=True
        )[:limit]
        
        return [
            {
                'id': job.id,
                'name': job.name,
                'status': job.status.value,
                'environment': job.target_environment,
                'created_at': job.created_at.isoformat(),
                'duration_seconds': (
                    (job.completed_at - job.started_at).total_seconds()
                    if job.started_at and job.completed_at else None
                )
            }
            for job in recent_deployments
        ]
    
    def cleanup_old_artifacts(self, retention_days: int = 30) -> None:
        """Clean up old deployment artifacts."""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Clean artifact storage
        if os.path.exists(self.artifact_storage):
            for filename in os.listdir(self.artifact_storage):
                file_path = os.path.join(self.artifact_storage, filename)
                if os.path.getctime(file_path) < cutoff_date.timestamp():
                    try:
                        os.remove(file_path)
                        self.logger.info(f"Removed old artifact: {filename}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove artifact {filename}: {str(e)}")
        
        # Clean backup storage
        if os.path.exists(self.backup_storage):
            for backup_dir in os.listdir(self.backup_storage):
                backup_path = os.path.join(self.backup_storage, backup_dir)
                if os.path.isdir(backup_path) and os.path.getctime(backup_path) < cutoff_date.timestamp():
                    try:
                        shutil.rmtree(backup_path)
                        self.logger.info(f"Removed old backup: {backup_dir}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove backup {backup_dir}: {str(e)}")


async def main():
    """Main function for testing deployment manager."""
    config = {
        'deployment': {
            'artifact_storage': './test_artifacts',
            'backup_storage': './test_backups',
            'use_docker': False,
            'environments': {
                'staging': {
                    'model_directory': './models_staging',
                    'config_directory': './config_staging',
                    'auto_restart_services': False,
                    'health_check': {'enabled': True, 'delay_seconds': 2}
                },
                'production': {
                    'model_directory': './models_production',
                    'config_directory': './config_production',
                    'auto_restart_services': True,
                    'services': [
                        {'name': 'prediction_service', 'type': 'process', 'restart_command': ['echo', 'restart']}
                    ],
                    'health_check': {'enabled': True, 'delay_seconds': 10}
                }
            }
        }
    }
    
    deployment_manager = DeploymentManager(config)
    
    # Create test model artifact
    test_model_path = './test_model.pkl'
    with open(test_model_path, 'wb') as f:
        f.write(b'test model data')
    
    try:
        # Create model artifact
        model_artifact = deployment_manager.create_model_artifact(
            'price_predictor',
            '1.2.3',
            test_model_path,
            {'accuracy': 0.85, 'features': ['price', 'volume']}
        )
        
        # Create config artifact
        config_artifact = deployment_manager.create_config_artifact(
            'prediction_config',
            '1.0.1',
            {'batch_size': 32, 'threshold': 0.8}
        )
        
        # Deploy to staging
        deployment_id = await deployment_manager.deploy_models(
            [model_artifact, config_artifact],
            environment='staging',
            strategy=DeploymentStrategy.ROLLING
        )
        
        print(f"Deployment ID: {deployment_id}")
        
        # Get deployment status
        status = deployment_manager.get_deployment_status(deployment_id)
        print(json.dumps(status, indent=2))
        
        # Get deployment history
        history = deployment_manager.get_deployment_history()
        print("Deployment History:")
        print(json.dumps(history, indent=2))
        
    finally:
        # Cleanup
        if os.path.exists(test_model_path):
            os.remove(test_model_path)


if __name__ == "__main__":
    asyncio.run(main())
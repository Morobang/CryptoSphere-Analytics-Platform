# Model Persistence and Versioning System
# Purpose: Manage model lifecycle, versioning, and deployment readiness
# 
# This module provides:
# - Model versioning and metadata management
# - Model registry for production deployment
# - A/B testing framework for model comparison
# - Model performance monitoring and drift detection
# - Automated model retirement and rollback capabilities

import os
import json
import pickle
import joblib
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import sqlite3
from pathlib import Path
import logging
import shutil
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import warnings
warnings.filterwarnings('ignore')

class ModelStatus(Enum):
    """Enum for model status in the registry."""
    TRAINING = "training"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"

@dataclass
class ModelMetadata:
    """Data class for model metadata."""
    model_id: str
    model_name: str
    version: str
    algorithm: str
    task_type: str
    status: ModelStatus
    created_at: datetime
    created_by: str
    performance_metrics: Dict[str, float]
    hyperparameters: Dict[str, Any]
    feature_names: List[str]
    training_data_hash: str
    model_size_mb: float
    dependencies: Dict[str, str]
    tags: List[str]
    description: str
    
class ModelRegistry:
    """
    Comprehensive model registry for managing ML model lifecycle.
    
    This class provides:
    - Model versioning and metadata tracking
    - Performance comparison across model versions
    - Deployment status management
    - Model lineage and audit trails
    - Integration with CI/CD pipelines
    
    Example usage:
        registry = ModelRegistry(registry_path="./model_registry")
        model_id = registry.register_model(
            model=trained_model,
            model_name="customer_churn_predictor",
            algorithm="random_forest",
            performance_metrics={"accuracy": 0.85, "f1": 0.78}
        )
    """
    
    def __init__(self, registry_path: str = "./model_registry"):
        """
        Initialize the model registry.
        
        Args:
            registry_path: Path to store registry database and model files
        """
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.models_path = self.registry_path / "models"
        self.models_path.mkdir(exist_ok=True)
        
        self.metadata_path = self.registry_path / "metadata"
        self.metadata_path.mkdir(exist_ok=True)
        
        # Initialize database
        self.db_path = self.registry_path / "registry.db"
        self._initialize_database()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
    def _initialize_database(self):
        """Initialize SQLite database for model registry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Models table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    model_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    algorithm TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    model_path TEXT NOT NULL,
                    metadata_path TEXT NOT NULL,
                    training_data_hash TEXT,
                    model_size_mb REAL,
                    description TEXT,
                    UNIQUE(model_name, version)
                )
            """)
            
            # Performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    model_id TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    dataset_type TEXT,
                    recorded_at TEXT,
                    FOREIGN KEY (model_id) REFERENCES models (model_id)
                )
            """)
            
            # Model features table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_features (
                    model_id TEXT,
                    feature_name TEXT,
                    feature_importance REAL,
                    FOREIGN KEY (model_id) REFERENCES models (model_id)
                )
            """)
            
            # Deployment history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deployment_history (
                    deployment_id TEXT PRIMARY KEY,
                    model_id TEXT,
                    environment TEXT,
                    deployed_at TEXT,
                    deployed_by TEXT,
                    rollback_at TEXT,
                    rollback_reason TEXT,
                    FOREIGN KEY (model_id) REFERENCES models (model_id)
                )
            """)
            
            # A/B testing table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ab_tests (
                    test_id TEXT PRIMARY KEY,
                    test_name TEXT,
                    control_model_id TEXT,
                    treatment_model_id TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    traffic_split REAL,
                    status TEXT,
                    winner_model_id TEXT,
                    created_by TEXT,
                    FOREIGN KEY (control_model_id) REFERENCES models (model_id),
                    FOREIGN KEY (treatment_model_id) REFERENCES models (model_id)
                )
            """)
            
            conn.commit()
    
    def register_model(self,
                      model: Any,
                      model_name: str,
                      algorithm: str,
                      task_type: str,
                      performance_metrics: Dict[str, float],
                      hyperparameters: Dict[str, Any] = None,
                      feature_names: List[str] = None,
                      training_data_hash: str = None,
                      created_by: str = "system",
                      tags: List[str] = None,
                      description: str = "",
                      auto_version: bool = True) -> str:
        """
        Register a new model in the registry.
        
        Args:
            model: Trained model object
            model_name: Name of the model
            algorithm: Algorithm used (e.g., 'random_forest', 'xgboost')
            task_type: Type of ML task ('classification' or 'regression')
            performance_metrics: Dictionary of performance metrics
            hyperparameters: Model hyperparameters
            feature_names: List of feature names used in training
            training_data_hash: Hash of training data for lineage tracking
            created_by: User who created the model
            tags: Tags for categorizing the model
            description: Model description
            auto_version: Automatically generate version number
            
        Returns:
            Unique model ID
        """
        # Generate model ID and version
        model_id = str(uuid.uuid4())
        
        if auto_version:
            version = self._generate_version(model_name)
        else:
            version = "1.0.0"
        
        # Calculate model size
        model_size_mb = self._calculate_model_size(model)
        
        # Save model file
        model_filename = f"{model_name}_v{version}_{model_id}.pkl"
        model_path = self.models_path / model_filename
        joblib.dump(model, model_path)
        
        # Create metadata
        metadata = ModelMetadata(
            model_id=model_id,
            model_name=model_name,
            version=version,
            algorithm=algorithm,
            task_type=task_type,
            status=ModelStatus.TRAINING,
            created_at=datetime.now(),
            created_by=created_by,
            performance_metrics=performance_metrics,
            hyperparameters=hyperparameters or {},
            feature_names=feature_names or [],
            training_data_hash=training_data_hash or "",
            model_size_mb=model_size_mb,
            dependencies=self._get_dependencies(),
            tags=tags or [],
            description=description
        )
        
        # Save metadata
        metadata_filename = f"{model_name}_v{version}_{model_id}_metadata.json"
        metadata_path = self.metadata_path / metadata_filename
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, indent=2, default=str)
        
        # Store in database
        self._store_model_in_db(metadata, str(model_path), str(metadata_path))
        
        self.logger.info(f"Registered model {model_name} v{version} with ID: {model_id}")
        return model_id
    
    def _generate_version(self, model_name: str) -> str:
        """Generate next version number for a model."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT version FROM models WHERE model_name = ? ORDER BY created_at DESC LIMIT 1",
                (model_name,)
            )
            result = cursor.fetchone()
            
            if result:
                last_version = result[0]
                # Simple versioning: increment minor version
                major, minor, patch = map(int, last_version.split('.'))
                return f"{major}.{minor + 1}.{patch}"
            else:
                return "1.0.0"
    
    def _calculate_model_size(self, model: Any) -> float:
        """Calculate model size in MB."""
        try:
            # Save to temporary file to get size
            temp_path = "temp_model_size_check.pkl"
            joblib.dump(model, temp_path)
            size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            os.remove(temp_path)
            return round(size_mb, 2)
        except Exception:
            return 0.0
    
    def _get_dependencies(self) -> Dict[str, str]:
        """Get current environment dependencies."""
        try:
            import pkg_resources
            dependencies = {}
            for package in ['scikit-learn', 'pandas', 'numpy', 'xgboost', 'lightgbm']:
                try:
                    version = pkg_resources.get_distribution(package).version
                    dependencies[package] = version
                except pkg_resources.DistributionNotFound:
                    pass
            return dependencies
        except Exception:
            return {}
    
    def _store_model_in_db(self, metadata: ModelMetadata, model_path: str, metadata_path: str):
        """Store model information in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert model record
            cursor.execute("""
                INSERT INTO models (
                    model_id, model_name, version, algorithm, task_type, status,
                    created_at, created_by, model_path, metadata_path,
                    training_data_hash, model_size_mb, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.model_id, metadata.model_name, metadata.version,
                metadata.algorithm, metadata.task_type, metadata.status.value,
                metadata.created_at.isoformat(), metadata.created_by,
                model_path, metadata_path, metadata.training_data_hash,
                metadata.model_size_mb, metadata.description
            ))
            
            # Insert performance metrics
            for metric_name, metric_value in metadata.performance_metrics.items():
                cursor.execute("""
                    INSERT INTO performance_metrics 
                    (model_id, metric_name, metric_value, dataset_type, recorded_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    metadata.model_id, metric_name, metric_value,
                    "training", datetime.now().isoformat()
                ))
            
            # Insert feature information if available
            if hasattr(metadata, 'feature_importance') and metadata.feature_importance:
                for feature_name, importance in metadata.feature_importance.items():
                    cursor.execute("""
                        INSERT INTO model_features (model_id, feature_name, feature_importance)
                        VALUES (?, ?, ?)
                    """, (metadata.model_id, feature_name, importance))
            
            conn.commit()
    
    def load_model(self, model_id: str = None, model_name: str = None, version: str = None) -> Tuple[Any, ModelMetadata]:
        """
        Load a model from the registry.
        
        Args:
            model_id: Unique model ID
            model_name: Model name (if model_id not provided)
            version: Model version (if model_id not provided, defaults to latest)
            
        Returns:
            Tuple of (model_object, metadata)
        """
        if not model_id and not model_name:
            raise ValueError("Either model_id or model_name must be provided")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if model_id:
                cursor.execute(
                    "SELECT model_path, metadata_path FROM models WHERE model_id = ?",
                    (model_id,)
                )
            else:
                if version:
                    cursor.execute(
                        "SELECT model_path, metadata_path FROM models WHERE model_name = ? AND version = ?",
                        (model_name, version)
                    )
                else:
                    # Get latest version
                    cursor.execute(
                        "SELECT model_path, metadata_path FROM models WHERE model_name = ? ORDER BY created_at DESC LIMIT 1",
                        (model_name,)
                    )
            
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Model not found: {model_id or model_name}")
            
            model_path, metadata_path = result
        
        # Load model and metadata
        model = joblib.load(model_path)
        
        with open(metadata_path, 'r') as f:
            metadata_dict = json.load(f)
            # Convert back to ModelMetadata object
            metadata_dict['created_at'] = datetime.fromisoformat(metadata_dict['created_at'])
            metadata_dict['status'] = ModelStatus(metadata_dict['status'])
            metadata = ModelMetadata(**metadata_dict)
        
        self.logger.info(f"Loaded model: {metadata.model_name} v{metadata.version}")
        return model, metadata
    
    def update_model_status(self, model_id: str, new_status: ModelStatus, updated_by: str = "system"):
        """
        Update model status in the registry.
        
        Args:
            model_id: Model ID to update
            new_status: New status for the model
            updated_by: User making the update
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE models SET status = ? WHERE model_id = ?",
                (new_status.value, model_id)
            )
            conn.commit()
        
        self.logger.info(f"Updated model {model_id} status to {new_status.value}")
    
    def list_models(self, model_name: str = None, status: ModelStatus = None) -> pd.DataFrame:
        """
        List models in the registry.
        
        Args:
            model_name: Filter by model name
            status: Filter by status
            
        Returns:
            DataFrame with model information
        """
        query = "SELECT * FROM models"
        params = []
        
        conditions = []
        if model_name:
            conditions.append("model_name = ?")
            params.append(model_name)
        if status:
            conditions.append("status = ?")
            params.append(status.value)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)
        
        return df
    
    def compare_models(self, model_ids: List[str]) -> pd.DataFrame:
        """
        Compare performance metrics across multiple models.
        
        Args:
            model_ids: List of model IDs to compare
            
        Returns:
            DataFrame with comparison metrics
        """
        comparison_data = []
        
        for model_id in model_ids:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get model info
                cursor.execute(
                    "SELECT model_name, version, algorithm, status FROM models WHERE model_id = ?",
                    (model_id,)
                )
                model_info = cursor.fetchone()
                
                if not model_info:
                    continue
                
                # Get performance metrics
                cursor.execute(
                    "SELECT metric_name, metric_value FROM performance_metrics WHERE model_id = ?",
                    (model_id,)
                )
                metrics = dict(cursor.fetchall())
                
                row = {
                    'model_id': model_id,
                    'model_name': model_info[0],
                    'version': model_info[1],
                    'algorithm': model_info[2],
                    'status': model_info[3]
                }
                row.update(metrics)
                comparison_data.append(row)
        
        return pd.DataFrame(comparison_data)
    
    def deploy_model(self, model_id: str, environment: str, deployed_by: str = "system") -> str:
        """
        Record model deployment.
        
        Args:
            model_id: Model ID to deploy
            environment: Deployment environment (e.g., 'staging', 'production')
            deployed_by: User deploying the model
            
        Returns:
            Deployment ID
        """
        deployment_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO deployment_history 
                (deployment_id, model_id, environment, deployed_at, deployed_by)
                VALUES (?, ?, ?, ?, ?)
            """, (
                deployment_id, model_id, environment,
                datetime.now().isoformat(), deployed_by
            ))
            conn.commit()
        
        # Update model status if deploying to production
        if environment.lower() == 'production':
            self.update_model_status(model_id, ModelStatus.PRODUCTION, deployed_by)
        
        self.logger.info(f"Deployed model {model_id} to {environment}")
        return deployment_id
    
    def rollback_deployment(self, deployment_id: str, rollback_reason: str, rolled_back_by: str = "system"):
        """
        Rollback a model deployment.
        
        Args:
            deployment_id: Deployment ID to rollback
            rollback_reason: Reason for rollback
            rolled_back_by: User performing rollback
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE deployment_history 
                SET rollback_at = ?, rollback_reason = ?
                WHERE deployment_id = ?
            """, (datetime.now().isoformat(), rollback_reason, deployment_id))
            conn.commit()
        
        self.logger.info(f"Rolled back deployment {deployment_id}: {rollback_reason}")
    
    def create_ab_test(self,
                      test_name: str,
                      control_model_id: str,
                      treatment_model_id: str,
                      traffic_split: float = 0.5,
                      duration_days: int = 14,
                      created_by: str = "system") -> str:
        """
        Create an A/B test for model comparison.
        
        Args:
            test_name: Name of the A/B test
            control_model_id: Model ID for control group
            treatment_model_id: Model ID for treatment group
            traffic_split: Percentage of traffic for treatment (0.0 to 1.0)
            duration_days: Duration of test in days
            created_by: User creating the test
            
        Returns:
            Test ID
        """
        test_id = str(uuid.uuid4())
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ab_tests 
                (test_id, test_name, control_model_id, treatment_model_id,
                 start_date, end_date, traffic_split, status, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_id, test_name, control_model_id, treatment_model_id,
                start_date.isoformat(), end_date.isoformat(),
                traffic_split, "running", created_by
            ))
            conn.commit()
        
        self.logger.info(f"Created A/B test: {test_name} ({test_id})")
        return test_id
    
    def conclude_ab_test(self, test_id: str, winner_model_id: str, conclusion_reason: str = ""):
        """
        Conclude an A/B test and declare a winner.
        
        Args:
            test_id: Test ID to conclude
            winner_model_id: Model ID of the winning model
            conclusion_reason: Reason for conclusion
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ab_tests 
                SET status = 'completed', winner_model_id = ?, end_date = ?
                WHERE test_id = ?
            """, (winner_model_id, datetime.now().isoformat(), test_id))
            conn.commit()
        
        self.logger.info(f"Concluded A/B test {test_id}, winner: {winner_model_id}")
    
    def archive_old_models(self, model_name: str, keep_versions: int = 5):
        """
        Archive old model versions, keeping only the most recent ones.
        
        Args:
            model_name: Name of the model to clean up
            keep_versions: Number of recent versions to keep
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get models to archive (excluding production models)
            cursor.execute("""
                SELECT model_id, model_path, metadata_path 
                FROM models 
                WHERE model_name = ? AND status != 'production'
                ORDER BY created_at DESC
                OFFSET ?
            """, (model_name, keep_versions))
            
            models_to_archive = cursor.fetchall()
            
            for model_id, model_path, metadata_path in models_to_archive:
                # Update status to archived
                cursor.execute(
                    "UPDATE models SET status = 'archived' WHERE model_id = ?",
                    (model_id,)
                )
                
                # Optionally move files to archive directory
                archive_dir = self.registry_path / "archived"
                archive_dir.mkdir(exist_ok=True)
                
                try:
                    shutil.move(model_path, archive_dir / Path(model_path).name)
                    shutil.move(metadata_path, archive_dir / Path(metadata_path).name)
                except Exception as e:
                    self.logger.warning(f"Could not move files for model {model_id}: {e}")
            
            conn.commit()
        
        self.logger.info(f"Archived {len(models_to_archive)} old versions of {model_name}")
    
    def get_model_lineage(self, model_id: str) -> Dict[str, Any]:
        """
        Get lineage information for a model.
        
        Args:
            model_id: Model ID to trace
            
        Returns:
            Dictionary with lineage information
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get model info
            cursor.execute("""
                SELECT model_name, version, algorithm, created_at, created_by, training_data_hash
                FROM models WHERE model_id = ?
            """, (model_id,))
            model_info = cursor.fetchone()
            
            if not model_info:
                return {}
            
            # Get deployment history
            cursor.execute("""
                SELECT environment, deployed_at, deployed_by, rollback_at, rollback_reason
                FROM deployment_history WHERE model_id = ?
                ORDER BY deployed_at DESC
            """, (model_id,))
            deployments = cursor.fetchall()
            
            # Get A/B test history
            cursor.execute("""
                SELECT test_name, start_date, end_date, status, winner_model_id
                FROM ab_tests WHERE control_model_id = ? OR treatment_model_id = ?
            """, (model_id, model_id))
            ab_tests = cursor.fetchall()
        
        lineage = {
            'model_info': {
                'model_name': model_info[0],
                'version': model_info[1],
                'algorithm': model_info[2],
                'created_at': model_info[3],
                'created_by': model_info[4],
                'training_data_hash': model_info[5]
            },
            'deployments': [
                {
                    'environment': dep[0],
                    'deployed_at': dep[1],
                    'deployed_by': dep[2],
                    'rollback_at': dep[3],
                    'rollback_reason': dep[4]
                } for dep in deployments
            ],
            'ab_tests': [
                {
                    'test_name': test[0],
                    'start_date': test[1],
                    'end_date': test[2],
                    'status': test[3],
                    'winner_model_id': test[4]
                } for test in ab_tests
            ]
        }
        
        return lineage
    
    def export_registry(self, export_path: str):
        """
        Export the entire registry to a backup file.
        
        Args:
            export_path: Path to export the registry
        """
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'models': [],
            'deployments': [],
            'ab_tests': []
        }
        
        with sqlite3.connect(self.db_path) as conn:
            # Export models
            models_df = pd.read_sql_query("SELECT * FROM models", conn)
            export_data['models'] = models_df.to_dict('records')
            
            # Export deployments
            deployments_df = pd.read_sql_query("SELECT * FROM deployment_history", conn)
            export_data['deployments'] = deployments_df.to_dict('records')
            
            # Export A/B tests
            ab_tests_df = pd.read_sql_query("SELECT * FROM ab_tests", conn)
            export_data['ab_tests'] = ab_tests_df.to_dict('records')
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Registry exported to {export_path}")


class ModelMonitor:
    """
    Model performance monitoring and drift detection system.
    
    This class provides:
    - Performance degradation detection
    - Data drift monitoring
    - Concept drift detection
    - Automated alerts and notifications
    - Performance trend analysis
    """
    
    def __init__(self, registry: ModelRegistry):
        """
        Initialize the model monitor.
        
        Args:
            registry: ModelRegistry instance for accessing models
        """
        self.registry = registry
        self.logger = logging.getLogger(__name__)
        
    def monitor_model_performance(self,
                                model_id: str,
                                new_predictions: np.ndarray,
                                true_labels: np.ndarray,
                                dataset_type: str = "production") -> Dict[str, Any]:
        """
        Monitor model performance against new data.
        
        Args:
            model_id: Model ID to monitor
            new_predictions: Recent model predictions
            true_labels: Actual labels for the predictions
            dataset_type: Type of dataset ('production', 'validation', etc.)
            
        Returns:
            Dictionary with monitoring results
        """
        # Load model metadata to get baseline performance
        _, metadata = self.registry.load_model(model_id=model_id)
        baseline_metrics = metadata.performance_metrics
        
        # Calculate current performance
        if metadata.task_type == 'classification':
            from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
            current_metrics = {
                'accuracy': accuracy_score(true_labels, new_predictions),
                'f1': f1_score(true_labels, new_predictions, average='weighted'),
                'precision': precision_score(true_labels, new_predictions, average='weighted'),
                'recall': recall_score(true_labels, new_predictions, average='weighted')
            }
        else:  # regression
            from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
            current_metrics = {
                'mse': mean_squared_error(true_labels, new_predictions),
                'r2': r2_score(true_labels, new_predictions),
                'mae': mean_absolute_error(true_labels, new_predictions)
            }
        
        # Calculate performance degradation
        degradation_alerts = []
        for metric_name, current_value in current_metrics.items():
            if metric_name in baseline_metrics:
                baseline_value = baseline_metrics[metric_name]
                
                # Calculate percentage change
                if baseline_value != 0:
                    pct_change = ((current_value - baseline_value) / baseline_value) * 100
                else:
                    pct_change = 0
                
                # Check for significant degradation (>5% for most metrics)
                degradation_threshold = -5 if metric_name in ['accuracy', 'f1', 'precision', 'recall', 'r2'] else 5
                
                if pct_change < degradation_threshold or pct_change > abs(degradation_threshold):
                    degradation_alerts.append({
                        'metric': metric_name,
                        'baseline_value': baseline_value,
                        'current_value': current_value,
                        'percentage_change': pct_change,
                        'severity': 'high' if abs(pct_change) > 10 else 'medium'
                    })
        
        # Store current metrics in database
        self._store_performance_metrics(model_id, current_metrics, dataset_type)
        
        monitoring_result = {
            'model_id': model_id,
            'monitoring_timestamp': datetime.now().isoformat(),
            'dataset_type': dataset_type,
            'sample_size': len(new_predictions),
            'baseline_metrics': baseline_metrics,
            'current_metrics': current_metrics,
            'degradation_alerts': degradation_alerts,
            'overall_health': 'good' if not degradation_alerts else 'degraded'
        }
        
        if degradation_alerts:
            self.logger.warning(f"Performance degradation detected for model {model_id}")
        
        return monitoring_result
    
    def detect_data_drift(self,
                         model_id: str,
                         reference_data: pd.DataFrame,
                         current_data: pd.DataFrame,
                         feature_columns: List[str]) -> Dict[str, Any]:
        """
        Detect data drift between reference and current datasets.
        
        Args:
            model_id: Model ID being monitored
            reference_data: Historical reference dataset
            current_data: Current production dataset
            feature_columns: List of feature columns to analyze
            
        Returns:
            Dictionary with drift detection results
        """
        from scipy import stats
        
        drift_results = {}
        significant_drifts = []
        
        for column in feature_columns:
            if column not in reference_data.columns or column not in current_data.columns:
                continue
            
            ref_values = reference_data[column].dropna()
            current_values = current_data[column].dropna()
            
            if len(ref_values) == 0 or len(current_values) == 0:
                continue
            
            # Perform statistical tests based on data type
            if ref_values.dtype in ['int64', 'float64']:
                # Numerical data: use Kolmogorov-Smirnov test
                statistic, p_value = stats.ks_2samp(ref_values, current_values)
                test_type = 'kolmogorov_smirnov'
            else:
                # Categorical data: use Chi-square test
                ref_counts = ref_values.value_counts()
                current_counts = current_values.value_counts()
                
                # Align categories
                all_categories = set(ref_counts.index) | set(current_counts.index)
                ref_aligned = [ref_counts.get(cat, 0) for cat in all_categories]
                current_aligned = [current_counts.get(cat, 0) for cat in all_categories]
                
                if sum(ref_aligned) > 0 and sum(current_aligned) > 0:
                    statistic, p_value = stats.chisquare(current_aligned, ref_aligned)
                    test_type = 'chi_square'
                else:
                    statistic, p_value = 0, 1
                    test_type = 'insufficient_data'
            
            # Determine drift significance
            is_drift = p_value < 0.05
            drift_severity = 'high' if p_value < 0.001 else 'medium' if p_value < 0.01 else 'low'
            
            drift_results[column] = {
                'test_statistic': statistic,
                'p_value': p_value,
                'is_drift': is_drift,
                'drift_severity': drift_severity,
                'test_type': test_type
            }
            
            if is_drift:
                significant_drifts.append({
                    'feature': column,
                    'p_value': p_value,
                    'severity': drift_severity,
                    'test_type': test_type
                })
        
        drift_summary = {
            'model_id': model_id,
            'detection_timestamp': datetime.now().isoformat(),
            'total_features_tested': len(feature_columns),
            'features_with_drift': len(significant_drifts),
            'drift_percentage': (len(significant_drifts) / len(feature_columns)) * 100 if feature_columns else 0,
            'significant_drifts': significant_drifts,
            'detailed_results': drift_results,
            'overall_drift_status': 'high' if len(significant_drifts) > len(feature_columns) * 0.3 else 'medium' if significant_drifts else 'low'
        }
        
        if significant_drifts:
            self.logger.warning(f"Data drift detected for model {model_id} in {len(significant_drifts)} features")
        
        return drift_summary
    
    def _store_performance_metrics(self, model_id: str, metrics: Dict[str, float], dataset_type: str):
        """Store performance metrics in the registry database."""
        with sqlite3.connect(self.registry.db_path) as conn:
            cursor = conn.cursor()
            
            for metric_name, metric_value in metrics.items():
                cursor.execute("""
                    INSERT INTO performance_metrics 
                    (model_id, metric_name, metric_value, dataset_type, recorded_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    model_id, metric_name, metric_value,
                    dataset_type, datetime.now().isoformat()
                ))
            
            conn.commit()
    
    def generate_monitoring_report(self, model_id: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Generate a comprehensive monitoring report for a model.
        
        Args:
            model_id: Model ID to report on
            days_back: Number of days to look back for metrics
            
        Returns:
            Dictionary with monitoring report
        """
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        with sqlite3.connect(self.registry.db_path) as conn:
            # Get recent performance metrics
            metrics_df = pd.read_sql_query("""
                SELECT metric_name, metric_value, dataset_type, recorded_at
                FROM performance_metrics 
                WHERE model_id = ? AND recorded_at >= ?
                ORDER BY recorded_at DESC
            """, conn, params=(model_id, cutoff_date))
        
        # Load model metadata
        _, metadata = self.registry.load_model(model_id=model_id)
        
        # Calculate metric trends
        trends = {}
        for metric_name in metrics_df['metric_name'].unique():
            metric_data = metrics_df[metrics_df['metric_name'] == metric_name].copy()
            metric_data['recorded_at'] = pd.to_datetime(metric_data['recorded_at'])
            metric_data = metric_data.sort_values('recorded_at')
            
            if len(metric_data) > 1:
                # Simple linear trend
                from scipy.stats import linregress
                x = np.arange(len(metric_data))
                y = metric_data['metric_value'].values
                slope, intercept, r_value, p_value, std_err = linregress(x, y)
                
                trends[metric_name] = {
                    'slope': slope,
                    'trend_direction': 'improving' if slope > 0 else 'declining' if slope < 0 else 'stable',
                    'r_squared': r_value ** 2,
                    'significance': p_value
                }
        
        report = {
            'model_id': model_id,
            'model_name': metadata.model_name,
            'model_version': metadata.version,
            'report_period_days': days_back,
            'report_generated_at': datetime.now().isoformat(),
            'total_monitoring_events': len(metrics_df),
            'baseline_performance': metadata.performance_metrics,
            'recent_performance': metrics_df.groupby('metric_name')['metric_value'].last().to_dict(),
            'performance_trends': trends,
            'recommendations': self._generate_recommendations(trends, metadata)
        }
        
        return report
    
    def _generate_recommendations(self, trends: Dict[str, Any], metadata: ModelMetadata) -> List[str]:
        """Generate recommendations based on monitoring results."""
        recommendations = []
        
        for metric_name, trend_info in trends.items():
            if trend_info['trend_direction'] == 'declining' and trend_info['significance'] < 0.05:
                recommendations.append(f"Consider retraining the model - {metric_name} is significantly declining")
            
            if trend_info['r_squared'] < 0.1:
                recommendations.append(f"Monitor {metric_name} more closely - trend is unstable")
        
        # Check model age
        model_age_days = (datetime.now() - metadata.created_at).days
        if model_age_days > 90:
            recommendations.append("Model is over 90 days old - consider retraining with fresh data")
        
        if not recommendations:
            recommendations.append("Model performance is stable - continue monitoring")
        
        return recommendations


# =============================================================================
# EXAMPLE USAGE AND TESTING
# =============================================================================

if __name__ == "__main__":
    """
    Example usage of the model persistence and monitoring system.
    """
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create sample model for demonstration
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score
    
    # Generate sample data
    X, y = make_classification(n_samples=1000, n_features=10, n_classes=2, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train sample model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test)
    performance_metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred)
    }
    
    print("Sample model trained with performance:")
    for metric, value in performance_metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # Initialize registry
    print("\n" + "="*50)
    print("MODEL REGISTRY EXAMPLE")
    print("="*50)
    
    registry = ModelRegistry(registry_path="./example_registry")
    
    # Register the model
    model_id = registry.register_model(
        model=model,
        model_name="sample_classifier",
        algorithm="random_forest",
        task_type="classification",
        performance_metrics=performance_metrics,
        hyperparameters={'n_estimators': 100, 'random_state': 42},
        feature_names=[f'feature_{i}' for i in range(10)],
        created_by="example_user",
        tags=['example', 'classification'],
        description="Sample random forest classifier for demonstration"
    )
    
    print(f"Registered model with ID: {model_id}")
    
    # List models
    models_df = registry.list_models()
    print(f"\nRegistered models:")
    print(models_df[['model_name', 'version', 'algorithm', 'status', 'created_at']])
    
    # Update model status
    registry.update_model_status(model_id, ModelStatus.STAGING)
    print(f"\nUpdated model status to STAGING")
    
    # Deploy model
    deployment_id = registry.deploy_model(model_id, environment="production", deployed_by="example_user")
    print(f"Deployed model to production with deployment ID: {deployment_id}")
    
    # Create A/B test (register second model first)
    model2 = RandomForestClassifier(n_estimators=200, random_state=42)
    model2.fit(X_train, y_train)
    y_pred2 = model2.predict(X_test)
    performance_metrics2 = {
        'accuracy': accuracy_score(y_test, y_pred2),
        'f1': f1_score(y_test, y_pred2)
    }
    
    model_id_2 = registry.register_model(
        model=model2,
        model_name="sample_classifier",
        algorithm="random_forest",
        task_type="classification",
        performance_metrics=performance_metrics2,
        hyperparameters={'n_estimators': 200, 'random_state': 42},
        created_by="example_user",
        description="Improved version with more estimators"
    )
    
    # Create A/B test
    test_id = registry.create_ab_test(
        test_name="Estimators Comparison",
        control_model_id=model_id,
        treatment_model_id=model_id_2,
        traffic_split=0.5,
        duration_days=7,
        created_by="example_user"
    )
    print(f"Created A/B test with ID: {test_id}")
    
    # Compare models
    comparison_df = registry.compare_models([model_id, model_id_2])
    print(f"\nModel comparison:")
    print(comparison_df[['model_name', 'version', 'accuracy', 'f1']])
    
    # Model monitoring example
    print("\n" + "="*50)
    print("MODEL MONITORING EXAMPLE")
    print("="*50)
    
    monitor = ModelMonitor(registry)
    
    # Simulate new production data (slightly degraded performance)
    X_new = X_test + np.random.normal(0, 0.1, X_test.shape)  # Add some noise
    y_new_pred = model.predict(X_new)
    
    # Monitor performance
    monitoring_result = monitor.monitor_model_performance(
        model_id=model_id,
        new_predictions=y_new_pred,
        true_labels=y_test,
        dataset_type="production"
    )
    
    print(f"Monitoring results:")
    print(f"  Overall health: {monitoring_result['overall_health']}")
    print(f"  Number of alerts: {len(monitoring_result['degradation_alerts'])}")
    
    if monitoring_result['degradation_alerts']:
        print("  Performance alerts:")
        for alert in monitoring_result['degradation_alerts']:
            print(f"    - {alert['metric']}: {alert['percentage_change']:.2f}% change ({alert['severity']} severity)")
    
    # Generate monitoring report
    report = monitor.generate_monitoring_report(model_id, days_back=1)
    print(f"\nMonitoring report generated:")
    print(f"  Monitoring events: {report['total_monitoring_events']}")
    print(f"  Recommendations: {len(report['recommendations'])}")
    for rec in report['recommendations']:
        print(f"    - {rec}")
    
    # Get model lineage
    lineage = registry.get_model_lineage(model_id)
    print(f"\nModel lineage:")
    print(f"  Model: {lineage['model_info']['model_name']} v{lineage['model_info']['version']}")
    print(f"  Created by: {lineage['model_info']['created_by']}")
    print(f"  Deployments: {len(lineage['deployments'])}")
    print(f"  A/B tests: {len(lineage['ab_tests'])}")
    
    # Archive old models (demonstration)
    registry.archive_old_models("sample_classifier", keep_versions=1)
    print(f"\nArchived old model versions")
    
    # Export registry
    registry.export_registry("registry_backup.json")
    print(f"Registry exported to backup file")
    
    print(f"\nModel persistence and monitoring example completed!")
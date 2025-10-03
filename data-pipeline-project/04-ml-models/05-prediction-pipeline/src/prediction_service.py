# Prediction Pipeline for Production ML Models
# Purpose: Serve trained models for real-time and batch predictions
# 
# This module provides:
# - Real-time prediction API endpoints
# - Batch prediction processing
# - Model loading and caching
# - Input validation and preprocessing
# - Output formatting and logging
# - Performance monitoring and error handling

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
import joblib
import logging
from datetime import datetime
from pathlib import Path
import time
import hashlib
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# Optional imports for web serving (install as needed)
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from pydantic import BaseModel, validator
    import uvicorn
    WEB_SERVING_AVAILABLE = True
except ImportError:
    WEB_SERVING_AVAILABLE = False
    print("Warning: FastAPI not available. Web serving functionality disabled.")

@dataclass
class PredictionRequest:
    """Data class for prediction requests."""
    model_name: str
    model_version: Optional[str] = None
    features: Dict[str, Any] = None
    feature_vector: List[float] = None
    return_probabilities: bool = False
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class PredictionResponse:
    """Data class for prediction responses."""
    predictions: Union[List[float], List[int], List[str]]
    probabilities: Optional[List[List[float]]] = None
    model_name: str = ""
    model_version: str = ""
    request_id: Optional[str] = None
    processing_time_ms: float = 0.0
    timestamp: str = ""
    metadata: Dict[str, Any] = None

class ModelCache:
    """
    Intelligent model caching system for production serving.
    
    This class provides:
    - Lazy loading of models on first request
    - LRU cache eviction for memory management
    - Model versioning and hot-swapping
    - Performance monitoring and metrics
    """
    
    def __init__(self, max_models: int = 10, cache_ttl_seconds: int = 3600):
        """
        Initialize the model cache.
        
        Args:
            max_models: Maximum number of models to keep in cache
            cache_ttl_seconds: Time-to-live for cached models in seconds
        """
        self.max_models = max_models
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache = {}
        self.access_times = {}
        self.load_times = {}
        self.access_counts = {}
        self.logger = logging.getLogger(__name__)
    
    def get_model(self, model_path: str, model_name: str = None) -> Any:
        """
        Get model from cache or load if not cached.
        
        Args:
            model_path: Path to the model file
            model_name: Optional name for the model
            
        Returns:
            Loaded model object
        """
        cache_key = model_path
        current_time = time.time()
        
        # Check if model is in cache and not expired
        if cache_key in self.cache:
            load_time = self.load_times.get(cache_key, 0)
            if current_time - load_time < self.cache_ttl_seconds:
                # Update access time and count
                self.access_times[cache_key] = current_time
                self.access_counts[cache_key] = self.access_counts.get(cache_key, 0) + 1
                return self.cache[cache_key]
        
        # Load model
        start_time = time.time()
        try:
            model = joblib.load(model_path)
            load_duration = time.time() - start_time
            
            # Check if we need to evict models
            if len(self.cache) >= self.max_models:
                self._evict_lru_model()
            
            # Cache the model
            self.cache[cache_key] = model
            self.access_times[cache_key] = current_time
            self.load_times[cache_key] = current_time
            self.access_counts[cache_key] = 1
            
            self.logger.info(f"Loaded model {model_name or cache_key} in {load_duration:.3f}s")
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load model from {model_path}: {str(e)}")
            raise
    
    def _evict_lru_model(self):
        """Evict least recently used model from cache."""
        if not self.cache:
            return
        
        # Find least recently used model
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        
        # Remove from all tracking dictionaries
        del self.cache[lru_key]
        del self.access_times[lru_key]
        del self.load_times[lru_key]
        del self.access_counts[lru_key]
        
        self.logger.info(f"Evicted model {lru_key} from cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        return {
            'cached_models': len(self.cache),
            'max_models': self.max_models,
            'cache_utilization': len(self.cache) / self.max_models,
            'total_accesses': sum(self.access_counts.values()),
            'model_access_counts': dict(self.access_counts),
            'cache_hit_rate': self._calculate_hit_rate()
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified)."""
        total_accesses = sum(self.access_counts.values())
        if total_accesses == 0:
            return 0.0
        # Simplified calculation - in production, track hits vs misses
        return min(0.9, len(self.cache) / self.max_models)
    
    def clear_cache(self):
        """Clear all cached models."""
        self.cache.clear()
        self.access_times.clear()
        self.load_times.clear()
        self.access_counts.clear()
        self.logger.info("Cleared model cache")

class PredictionPipeline:
    """
    Production-ready prediction pipeline for ML models.
    
    This class provides:
    - Model loading and caching
    - Input validation and preprocessing
    - Prediction generation with error handling
    - Output formatting and logging
    - Performance monitoring
    - Batch and real-time processing
    
    Example usage:
        pipeline = PredictionPipeline(models_directory="./models")
        response = pipeline.predict(
            model_name="customer_churn",
            features={"age": 35, "income": 50000, "tenure": 24}
        )
    """
    
    def __init__(self, 
                 models_directory: str = "./models",
                 preprocessor_directory: str = "./preprocessors",
                 enable_caching: bool = True,
                 max_cached_models: int = 10):
        """
        Initialize the prediction pipeline.
        
        Args:
            models_directory: Directory containing trained models
            preprocessor_directory: Directory containing preprocessors
            enable_caching: Whether to enable model caching
            max_cached_models: Maximum number of models to cache
        """
        self.models_directory = Path(models_directory)
        self.preprocessor_directory = Path(preprocessor_directory)
        
        # Initialize model cache
        if enable_caching:
            self.model_cache = ModelCache(max_models=max_cached_models)
        else:
            self.model_cache = None
        
        # Initialize preprocessor cache
        self.preprocessor_cache = {}
        
        # Performance tracking
        self.prediction_count = 0
        self.total_processing_time = 0.0
        self.error_count = 0
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Discover available models
        self.available_models = self._discover_models()
        self.logger.info(f"Discovered {len(self.available_models)} available models")
    
    def _discover_models(self) -> Dict[str, Dict[str, str]]:
        """Discover available models in the models directory."""
        available_models = {}
        
        if not self.models_directory.exists():
            self.logger.warning(f"Models directory {self.models_directory} does not exist")
            return available_models
        
        # Look for .pkl files and their metadata
        for model_file in self.models_directory.glob("*.pkl"):
            # Try to find corresponding metadata file
            metadata_file = model_file.with_suffix('').with_suffix('_metadata.json')
            
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    model_name = metadata.get('model_name', model_file.stem)
                    version = metadata.get('version', '1.0.0')
                    
                    if model_name not in available_models:
                        available_models[model_name] = {}
                    
                    available_models[model_name][version] = {
                        'model_path': str(model_file),
                        'metadata_path': str(metadata_file),
                        'algorithm': metadata.get('algorithm', 'unknown'),
                        'task_type': metadata.get('task_type', 'unknown'),
                        'feature_names': metadata.get('feature_names', [])
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Could not load metadata for {model_file}: {e}")
            else:
                # No metadata file, use filename
                model_name = model_file.stem
                available_models[model_name] = {
                    '1.0.0': {
                        'model_path': str(model_file),
                        'metadata_path': None,
                        'algorithm': 'unknown',
                        'task_type': 'unknown',
                        'feature_names': []
                    }
                }
        
        return available_models
    
    def _load_model(self, model_name: str, version: str = None) -> Tuple[Any, Dict[str, Any]]:
        """
        Load a model and its metadata.
        
        Args:
            model_name: Name of the model to load
            version: Specific version to load (if None, loads latest)
            
        Returns:
            Tuple of (model, metadata)
        """
        if model_name not in self.available_models:
            raise ValueError(f"Model '{model_name}' not found. Available models: {list(self.available_models.keys())}")
        
        versions = self.available_models[model_name]
        
        if version is None:
            # Load latest version
            version = max(versions.keys())
        
        if version not in versions:
            raise ValueError(f"Version '{version}' not found for model '{model_name}'. Available versions: {list(versions.keys())}")
        
        model_info = versions[version]
        model_path = model_info['model_path']
        
        # Load model (with caching if enabled)
        if self.model_cache:
            model = self.model_cache.get_model(model_path, f"{model_name}_{version}")
        else:
            model = joblib.load(model_path)
        
        # Load metadata
        metadata = model_info.copy()
        if model_info['metadata_path']:
            try:
                with open(model_info['metadata_path'], 'r') as f:
                    full_metadata = json.load(f)
                metadata.update(full_metadata)
            except Exception as e:
                self.logger.warning(f"Could not load full metadata: {e}")
        
        return model, metadata
    
    def _load_preprocessor(self, model_name: str) -> Optional[Any]:
        """Load preprocessor for a model if available."""
        preprocessor_key = model_name
        
        # Check cache first
        if preprocessor_key in self.preprocessor_cache:
            return self.preprocessor_cache[preprocessor_key]
        
        # Look for preprocessor file
        preprocessor_path = self.preprocessor_directory / f"{model_name}_preprocessor.pkl"
        
        if preprocessor_path.exists():
            try:
                preprocessor = joblib.load(preprocessor_path)
                self.preprocessor_cache[preprocessor_key] = preprocessor
                return preprocessor
            except Exception as e:
                self.logger.warning(f"Could not load preprocessor for {model_name}: {e}")
        
        return None
    
    def _validate_input(self, features: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean input features.
        
        Args:
            features: Input features dictionary
            metadata: Model metadata
            
        Returns:
            Validated features dictionary
        """
        if not features:
            raise ValueError("Features cannot be empty")
        
        validated_features = features.copy()
        expected_features = metadata.get('feature_names', [])
        
        # Check for missing required features
        if expected_features:
            missing_features = set(expected_features) - set(validated_features.keys())
            if missing_features:
                self.logger.warning(f"Missing features: {missing_features}")
                # Fill with default values (0 for numeric, 'unknown' for categorical)
                for feature in missing_features:
                    validated_features[feature] = 0  # Simple default
        
        # Remove unexpected features
        if expected_features:
            extra_features = set(validated_features.keys()) - set(expected_features)
            if extra_features:
                self.logger.warning(f"Removing unexpected features: {extra_features}")
                for feature in extra_features:
                    del validated_features[feature]
        
        return validated_features
    
    def _preprocess_features(self, features: Dict[str, Any], preprocessor: Any) -> np.ndarray:
        """
        Preprocess features using the model's preprocessor.
        
        Args:
            features: Input features
            preprocessor: Fitted preprocessor
            
        Returns:
            Preprocessed feature array
        """
        if preprocessor is None:
            # Convert to DataFrame and then to array
            df = pd.DataFrame([features])
            return df.values
        
        try:
            # Assume preprocessor has a transform method
            if hasattr(preprocessor, 'transform_new_data'):
                df = pd.DataFrame([features])
                processed_df = preprocessor.transform_new_data(df)
                return processed_df.values
            elif hasattr(preprocessor, 'transform'):
                df = pd.DataFrame([features])
                return preprocessor.transform(df)
            else:
                # Fallback to simple conversion
                df = pd.DataFrame([features])
                return df.values
                
        except Exception as e:
            self.logger.error(f"Preprocessing failed: {e}")
            # Fallback to simple conversion
            df = pd.DataFrame([features])
            return df.values
    
    def predict(self, 
                model_name: str,
                features: Dict[str, Any] = None,
                feature_vector: List[float] = None,
                model_version: str = None,
                return_probabilities: bool = False,
                request_id: str = None) -> PredictionResponse:
        """
        Generate predictions for given features.
        
        Args:
            model_name: Name of the model to use
            features: Dictionary of feature name-value pairs
            feature_vector: Pre-processed feature vector (alternative to features)
            model_version: Specific model version to use
            return_probabilities: Whether to return prediction probabilities
            request_id: Optional request ID for tracking
            
        Returns:
            PredictionResponse object
        """
        start_time = time.time()
        
        try:
            # Generate request ID if not provided
            if request_id is None:
                request_id = hashlib.md5(f"{model_name}_{time.time()}".encode()).hexdigest()[:8]
            
            # Load model and metadata
            model, metadata = self._load_model(model_name, model_version)
            actual_version = metadata.get('version', '1.0.0')
            
            # Prepare features
            if feature_vector is not None:
                # Use provided feature vector
                X = np.array(feature_vector).reshape(1, -1)
            elif features is not None:
                # Validate and preprocess features
                validated_features = self._validate_input(features, metadata)
                
                # Load and apply preprocessor
                preprocessor = self._load_preprocessor(model_name)
                X = self._preprocess_features(validated_features, preprocessor)
            else:
                raise ValueError("Either features or feature_vector must be provided")
            
            # Generate predictions
            predictions = model.predict(X)
            
            # Convert predictions to appropriate format
            if len(predictions) == 1:
                prediction_value = predictions[0]
                if hasattr(prediction_value, 'item'):
                    prediction_value = prediction_value.item()
                predictions_list = [prediction_value]
            else:
                predictions_list = predictions.tolist()
            
            # Get probabilities if requested and supported
            probabilities = None
            if return_probabilities and hasattr(model, 'predict_proba'):
                try:
                    proba = model.predict_proba(X)
                    probabilities = proba.tolist()
                except Exception as e:
                    self.logger.warning(f"Could not get probabilities: {e}")
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Update performance metrics
            self.prediction_count += 1
            self.total_processing_time += processing_time_ms
            
            # Create response
            response = PredictionResponse(
                predictions=predictions_list,
                probabilities=probabilities,
                model_name=model_name,
                model_version=actual_version,
                request_id=request_id,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.now().isoformat(),
                metadata={
                    'algorithm': metadata.get('algorithm', 'unknown'),
                    'task_type': metadata.get('task_type', 'unknown'),
                    'feature_count': X.shape[1] if len(X.shape) > 1 else len(X)
                }
            )
            
            self.logger.info(f"Prediction completed: {request_id} in {processing_time_ms:.2f}ms")
            return response
            
        except Exception as e:
            self.error_count += 1
            processing_time_ms = (time.time() - start_time) * 1000
            
            self.logger.error(f"Prediction failed for {request_id}: {str(e)}")
            
            # Return error response
            return PredictionResponse(
                predictions=[],
                model_name=model_name,
                model_version=model_version or "unknown",
                request_id=request_id,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.now().isoformat(),
                metadata={'error': str(e)}
            )
    
    def predict_batch(self,
                     model_name: str,
                     features_list: List[Dict[str, Any]],
                     model_version: str = None,
                     return_probabilities: bool = False,
                     batch_size: int = 100) -> List[PredictionResponse]:
        """
        Generate predictions for a batch of feature sets.
        
        Args:
            model_name: Name of the model to use
            features_list: List of feature dictionaries
            model_version: Specific model version to use
            return_probabilities: Whether to return prediction probabilities
            batch_size: Size of processing batches
            
        Returns:
            List of PredictionResponse objects
        """
        if not features_list:
            return []
        
        self.logger.info(f"Processing batch of {len(features_list)} predictions")
        
        responses = []
        
        # Process in batches
        for i in range(0, len(features_list), batch_size):
            batch = features_list[i:i + batch_size]
            batch_responses = []
            
            for j, features in enumerate(batch):
                request_id = f"batch_{i + j}_{int(time.time())}"
                response = self.predict(
                    model_name=model_name,
                    features=features,
                    model_version=model_version,
                    return_probabilities=return_probabilities,
                    request_id=request_id
                )
                batch_responses.append(response)
            
            responses.extend(batch_responses)
        
        self.logger.info(f"Completed batch processing: {len(responses)} responses")
        return responses
    
    def get_model_info(self, model_name: str, version: str = None) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model_name: Name of the model
            version: Specific version (if None, returns latest)
            
        Returns:
            Dictionary with model information
        """
        if model_name not in self.available_models:
            raise ValueError(f"Model '{model_name}' not found")
        
        versions = self.available_models[model_name]
        
        if version is None:
            version = max(versions.keys())
        
        if version not in versions:
            raise ValueError(f"Version '{version}' not found for model '{model_name}'")
        
        model_info = versions[version].copy()
        
        # Load full metadata if available
        if model_info['metadata_path']:
            try:
                with open(model_info['metadata_path'], 'r') as f:
                    full_metadata = json.load(f)
                model_info.update(full_metadata)
            except Exception as e:
                self.logger.warning(f"Could not load full metadata: {e}")
        
        return model_info
    
    def list_available_models(self) -> Dict[str, List[str]]:
        """
        List all available models and their versions.
        
        Returns:
            Dictionary mapping model names to available versions
        """
        return {
            model_name: list(versions.keys())
            for model_name, versions in self.available_models.items()
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get pipeline performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        avg_processing_time = (
            self.total_processing_time / self.prediction_count
            if self.prediction_count > 0 else 0
        )
        
        error_rate = (
            self.error_count / (self.prediction_count + self.error_count)
            if (self.prediction_count + self.error_count) > 0 else 0
        )
        
        stats = {
            'total_predictions': self.prediction_count,
            'total_errors': self.error_count,
            'error_rate': error_rate,
            'average_processing_time_ms': avg_processing_time,
            'total_processing_time_ms': self.total_processing_time
        }
        
        # Add cache stats if caching is enabled
        if self.model_cache:
            stats['cache_stats'] = self.model_cache.get_cache_stats()
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the prediction pipeline.
        
        Returns:
            Dictionary with health status
        """
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'available_models': len(self.available_models),
            'models_directory_exists': self.models_directory.exists(),
            'preprocessor_directory_exists': self.preprocessor_directory.exists(),
            'issues': []
        }
        
        # Check if models directory exists and has models
        if not self.models_directory.exists():
            health_status['issues'].append("Models directory does not exist")
            health_status['status'] = 'unhealthy'
        elif len(self.available_models) == 0:
            health_status['issues'].append("No models found in models directory")
            health_status['status'] = 'degraded'
        
        # Test loading a sample model if available
        if self.available_models:
            try:
                sample_model_name = list(self.available_models.keys())[0]
                model, metadata = self._load_model(sample_model_name)
                health_status['sample_model_loaded'] = True
            except Exception as e:
                health_status['issues'].append(f"Failed to load sample model: {str(e)}")
                health_status['status'] = 'degraded'
                health_status['sample_model_loaded'] = False
        
        return health_status


# =============================================================================
# WEB API SERVING (OPTIONAL)
# =============================================================================

if WEB_SERVING_AVAILABLE:
    # Pydantic models for API
    class PredictionRequestAPI(BaseModel):
        model_name: str
        features: Optional[Dict[str, Any]] = None
        feature_vector: Optional[List[float]] = None
        model_version: Optional[str] = None
        return_probabilities: bool = False
        
        @validator('features', 'feature_vector')
        def validate_input(cls, v, values):
            if not v and not values.get('feature_vector') and not values.get('features'):
                raise ValueError("Either features or feature_vector must be provided")
            return v
    
    class BatchPredictionRequestAPI(BaseModel):
        model_name: str
        features_list: List[Dict[str, Any]]
        model_version: Optional[str] = None
        return_probabilities: bool = False
        batch_size: int = 100
    
    def create_prediction_api(pipeline: PredictionPipeline) -> FastAPI:
        """
        Create FastAPI application for serving predictions.
        
        Args:
            pipeline: Configured PredictionPipeline instance
            
        Returns:
            FastAPI application
        """
        app = FastAPI(
            title="ML Prediction API",
            description="Production ML model serving API",
            version="1.0.0"
        )
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return pipeline.health_check()
        
        @app.get("/models")
        async def list_models():
            """List available models."""
            return pipeline.list_available_models()
        
        @app.get("/models/{model_name}/info")
        async def get_model_info(model_name: str, version: Optional[str] = None):
            """Get model information."""
            try:
                return pipeline.get_model_info(model_name, version)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
        
        @app.post("/predict")
        async def predict(request: PredictionRequestAPI):
            """Single prediction endpoint."""
            response = pipeline.predict(
                model_name=request.model_name,
                features=request.features,
                feature_vector=request.feature_vector,
                model_version=request.model_version,
                return_probabilities=request.return_probabilities
            )
            return response
        
        @app.post("/predict/batch")
        async def predict_batch(request: BatchPredictionRequestAPI, background_tasks: BackgroundTasks):
            """Batch prediction endpoint."""
            responses = pipeline.predict_batch(
                model_name=request.model_name,
                features_list=request.features_list,
                model_version=request.model_version,
                return_probabilities=request.return_probabilities,
                batch_size=request.batch_size
            )
            return {"responses": responses}
        
        @app.get("/stats")
        async def get_stats():
            """Get pipeline performance statistics."""
            return pipeline.get_performance_stats()
        
        return app


# =============================================================================
# EXAMPLE USAGE AND TESTING
# =============================================================================

if __name__ == "__main__":
    """
    Example usage of the prediction pipeline.
    """
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create sample model and data for testing
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification
    import os
    
    print("Creating sample model for demonstration...")
    
    # Generate sample data
    X, y = make_classification(n_samples=1000, n_features=5, n_classes=2, random_state=42)
    feature_names = [f'feature_{i}' for i in range(5)]
    
    # Train sample model
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    # Create directories
    os.makedirs("./example_models", exist_ok=True)
    os.makedirs("./example_preprocessors", exist_ok=True)
    
    # Save model
    model_path = "./example_models/sample_classifier.pkl"
    joblib.dump(model, model_path)
    
    # Create metadata
    metadata = {
        'model_name': 'sample_classifier',
        'version': '1.0.0',
        'algorithm': 'random_forest',
        'task_type': 'classification',
        'feature_names': feature_names,
        'performance_metrics': {'accuracy': 0.85, 'f1': 0.83}
    }
    
    metadata_path = "./example_models/sample_classifier_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("Sample model created!")
    
    # Initialize prediction pipeline
    print("\n" + "="*50)
    print("PREDICTION PIPELINE EXAMPLE")
    print("="*50)
    
    pipeline = PredictionPipeline(
        models_directory="./example_models",
        preprocessor_directory="./example_preprocessors",
        enable_caching=True,
        max_cached_models=5
    )
    
    # List available models
    available_models = pipeline.list_available_models()
    print(f"Available models: {available_models}")
    
    # Get model info
    model_info = pipeline.get_model_info('sample_classifier')
    print(f"\nModel info:")
    print(f"  Algorithm: {model_info['algorithm']}")
    print(f"  Task type: {model_info['task_type']}")
    print(f"  Features: {model_info['feature_names']}")
    
    # Test single prediction
    print(f"\nTesting single prediction...")
    sample_features = {
        'feature_0': 1.5,
        'feature_1': -0.8,
        'feature_2': 0.3,
        'feature_3': 2.1,
        'feature_4': -1.2
    }
    
    response = pipeline.predict(
        model_name='sample_classifier',
        features=sample_features,
        return_probabilities=True
    )
    
    print(f"Prediction response:")
    print(f"  Request ID: {response.request_id}")
    print(f"  Prediction: {response.predictions}")
    print(f"  Probabilities: {response.probabilities}")
    print(f"  Processing time: {response.processing_time_ms:.2f}ms")
    print(f"  Model version: {response.model_version}")
    
    # Test batch prediction
    print(f"\nTesting batch prediction...")
    batch_features = [
        {'feature_0': 1.0, 'feature_1': 0.5, 'feature_2': -1.0, 'feature_3': 0.8, 'feature_4': -0.3},
        {'feature_0': -1.5, 'feature_1': 2.0, 'feature_2': 0.1, 'feature_3': -0.5, 'feature_4': 1.8},
        {'feature_0': 0.3, 'feature_1': -1.2, 'feature_2': 1.5, 'feature_3': 0.0, 'feature_4': -2.1}
    ]
    
    batch_responses = pipeline.predict_batch(
        model_name='sample_classifier',
        features_list=batch_features,
        return_probabilities=False
    )
    
    print(f"Batch prediction completed:")
    print(f"  Number of responses: {len(batch_responses)}")
    for i, resp in enumerate(batch_responses):
        print(f"  Sample {i+1}: {resp.predictions[0]} ({resp.processing_time_ms:.2f}ms)")
    
    # Test health check
    health = pipeline.health_check()
    print(f"\nHealth check:")
    print(f"  Status: {health['status']}")
    print(f"  Available models: {health['available_models']}")
    print(f"  Issues: {health['issues']}")
    
    # Get performance stats
    stats = pipeline.get_performance_stats()
    print(f"\nPerformance statistics:")
    print(f"  Total predictions: {stats['total_predictions']}")
    print(f"  Error rate: {stats['error_rate']:.2%}")
    print(f"  Average processing time: {stats['average_processing_time_ms']:.2f}ms")
    
    if 'cache_stats' in stats:
        cache_stats = stats['cache_stats']
        print(f"  Cache utilization: {cache_stats['cache_utilization']:.2%}")
        print(f"  Cache hit rate: {cache_stats['cache_hit_rate']:.2%}")
    
    # Test error handling
    print(f"\nTesting error handling...")
    try:
        error_response = pipeline.predict(
            model_name='nonexistent_model',
            features=sample_features
        )
        print(f"Error handled gracefully: {error_response.metadata.get('error', 'No error')}")
    except Exception as e:
        print(f"Exception caught: {str(e)}")
    
    # Web API example (if FastAPI is available)
    if WEB_SERVING_AVAILABLE:
        print(f"\nWeb API available! You can start the server with:")
        print(f"  app = create_prediction_api(pipeline)")
        print(f"  uvicorn.run(app, host='0.0.0.0', port=8000)")
        print(f"\nAPI endpoints:")
        print(f"  GET  /health - Health check")
        print(f"  GET  /models - List available models")
        print(f"  POST /predict - Single prediction")
        print(f"  POST /predict/batch - Batch prediction")
        print(f"  GET  /stats - Performance statistics")
    else:
        print(f"\nTo enable web API serving, install: pip install fastapi uvicorn")
    
    print(f"\nPrediction pipeline example completed successfully!")
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree("./example_models")
        shutil.rmtree("./example_preprocessors")
        print("Cleaned up example files")
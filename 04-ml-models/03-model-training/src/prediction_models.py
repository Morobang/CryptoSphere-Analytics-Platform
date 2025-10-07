"""
Cryptocurrency Price Prediction Models

This module contains various machine learning models specifically designed 
for cryptocurrency price prediction, including traditional ML and deep learning models.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import lightgbm as lgb
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')


class CryptoPredictionModels:
    """
    Collection of machine learning models for cryptocurrency price prediction.
    """
    
    def __init__(self):
        """Initialize the model collection."""
        self.models = {}
        self.model_configs = self._get_default_configs()
        self.trained_models = {}
        
    def _get_default_configs(self) -> Dict:
        """
        Get default configurations for all models.
        
        Returns:
            Dictionary with default model configurations
        """
        return {
            'linear_regression': {},
            'ridge': {'alpha': 1.0},
            'lasso': {'alpha': 1.0},
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 2,
                'min_samples_leaf': 1,
                'random_state': 42
            },
            'gradient_boosting': {
                'n_estimators': 100,
                'learning_rate': 0.1,
                'max_depth': 3,
                'random_state': 42
            },
            'xgboost': {
                'n_estimators': 100,
                'learning_rate': 0.1,
                'max_depth': 6,
                'random_state': 42,
                'eval_metric': 'rmse'
            },
            'lightgbm': {
                'n_estimators': 100,
                'learning_rate': 0.1,
                'max_depth': -1,
                'random_state': 42,
                'verbose': -1
            },
            'svr': {
                'kernel': 'rbf',
                'C': 1.0,
                'gamma': 'scale'
            },
            'mlp': {
                'hidden_layer_sizes': (100, 50),
                'activation': 'relu',
                'solver': 'adam',
                'max_iter': 1000,
                'random_state': 42
            }
        }
    
    def create_model(self, model_type: str, config: Dict = None) -> Any:
        """
        Create a model instance.
        
        Args:
            model_type: Type of model to create
            config: Model configuration (optional)
            
        Returns:
            Model instance
        """
        if config is None:
            config = self.model_configs.get(model_type, {})
        
        if model_type == 'linear_regression':
            return LinearRegression(**config)
        elif model_type == 'ridge':
            return Ridge(**config)
        elif model_type == 'lasso':
            return Lasso(**config)
        elif model_type == 'random_forest':
            return RandomForestRegressor(**config)
        elif model_type == 'gradient_boosting':
            return GradientBoostingRegressor(**config)
        elif model_type == 'xgboost':
            return xgb.XGBRegressor(**config)
        elif model_type == 'lightgbm':
            return lgb.LGBMRegressor(**config)
        elif model_type == 'svr':
            return SVR(**config)
        elif model_type == 'mlp':
            return MLPRegressor(**config)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def train_model(self, model_type: str, X_train: pd.DataFrame, y_train: pd.Series,
                   X_val: pd.DataFrame = None, y_val: pd.Series = None,
                   config: Dict = None) -> Dict:
        """
        Train a specific model.
        
        Args:
            model_type: Type of model to train
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
            config: Model configuration (optional)
            
        Returns:
            Dictionary with training results
        """
        print(f"Training {model_type} model...")
        
        # Create model
        model = self.create_model(model_type, config)
        
        # Special handling for XGBoost and LightGBM with validation
        if model_type == 'xgboost' and X_val is not None:
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=10,
                verbose=False
            )
        elif model_type == 'lightgbm' and X_val is not None:
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=10,
                callbacks=[lgb.early_stopping(10, verbose=False)]
            )
        else:
            model.fit(X_train, y_train)
        
        # Store trained model
        self.trained_models[model_type] = model
        
        # Make predictions
        train_pred = model.predict(X_train)
        train_metrics = self._calculate_metrics(y_train, train_pred)
        
        results = {
            'model_type': model_type,
            'model': model,
            'train_metrics': train_metrics
        }
        
        # Validation metrics if available
        if X_val is not None:
            val_pred = model.predict(X_val)
            val_metrics = self._calculate_metrics(y_val, val_pred)
            results['val_metrics'] = val_metrics
        
        return results
    
    def train_multiple_models(self, X_train: pd.DataFrame, y_train: pd.Series,
                            X_val: pd.DataFrame = None, y_val: pd.Series = None,
                            model_types: List[str] = None) -> Dict:
        """
        Train multiple models and compare performance.
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
            model_types: List of model types to train
            
        Returns:
            Dictionary with results for all models
        """
        if model_types is None:
            model_types = ['linear_regression', 'random_forest', 'xgboost', 'lightgbm']
        
        results = {}
        
        for model_type in model_types:
            try:
                result = self.train_model(model_type, X_train, y_train, X_val, y_val)
                results[model_type] = result
                print(f"✓ {model_type} trained successfully")
            except Exception as e:
                print(f"✗ Error training {model_type}: {str(e)}")
                results[model_type] = {'error': str(e)}
        
        return results
    
    def get_best_model(self, results: Dict, metric: str = 'rmse') -> Tuple[str, Any]:
        """
        Get the best performing model based on validation metrics.
        
        Args:
            results: Training results from train_multiple_models
            metric: Metric to use for selection ('rmse', 'mae', 'r2')
            
        Returns:
            Tuple of (best_model_name, best_model_instance)
        """
        best_score = float('inf') if metric in ['rmse', 'mae'] else float('-inf')
        best_model_name = None
        best_model = None
        
        for model_name, result in results.items():
            if 'error' in result or 'val_metrics' not in result:
                continue
            
            score = result['val_metrics'][metric]
            
            if metric in ['rmse', 'mae']:
                if score < best_score:
                    best_score = score
                    best_model_name = model_name
                    best_model = result['model']
            else:  # r2
                if score > best_score:
                    best_score = score
                    best_model_name = model_name
                    best_model = result['model']
        
        return best_model_name, best_model
    
    def predict(self, model_name: str, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using a trained model.
        
        Args:
            model_name: Name of the trained model
            X: Features for prediction
            
        Returns:
            Predictions array
        """
        if model_name not in self.trained_models:
            raise ValueError(f"Model {model_name} not trained")
        
        model = self.trained_models[model_name]
        return model.predict(X)
    
    def get_feature_importance(self, model_name: str, feature_names: List[str] = None) -> pd.DataFrame:
        """
        Get feature importance from a trained model.
        
        Args:
            model_name: Name of the trained model
            feature_names: List of feature names
            
        Returns:
            DataFrame with feature importance
        """
        if model_name not in self.trained_models:
            raise ValueError(f"Model {model_name} not trained")
        
        model = self.trained_models[model_name]
        
        # Check if model has feature importance
        if not hasattr(model, 'feature_importances_'):
            return pd.DataFrame({'message': [f'{model_name} does not provide feature importance']})
        
        importance = model.feature_importances_
        
        if feature_names is None:
            feature_names = [f'feature_{i}' for i in range(len(importance))]
        
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def _calculate_metrics(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict:
        """
        Calculate regression metrics.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Dictionary with metrics
        """
        return {
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'mse': mean_squared_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred)
        }
    
    def create_ensemble_model(self, model_names: List[str], weights: List[float] = None) -> 'EnsembleModel':
        """
        Create an ensemble model from trained models.
        
        Args:
            model_names: List of model names to ensemble
            weights: Weights for each model (optional)
            
        Returns:
            Ensemble model instance
        """
        models = []
        for name in model_names:
            if name in self.trained_models:
                models.append(self.trained_models[name])
            else:
                raise ValueError(f"Model {name} not trained")
        
        return EnsembleModel(models, weights)


class EnsembleModel:
    """
    Ensemble model that combines predictions from multiple models.
    """
    
    def __init__(self, models: List[Any], weights: List[float] = None):
        """
        Initialize ensemble model.
        
        Args:
            models: List of trained models
            weights: Weights for each model
        """
        self.models = models
        if weights is None:
            self.weights = [1.0 / len(models)] * len(models)
        else:
            self.weights = weights
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make ensemble predictions.
        
        Args:
            X: Features for prediction
            
        Returns:
            Ensemble predictions
        """
        predictions = []
        
        for model in self.models:
            pred = model.predict(X)
            predictions.append(pred)
        
        # Weighted average of predictions
        ensemble_pred = np.average(predictions, axis=0, weights=self.weights)
        return ensemble_pred


if __name__ == "__main__":
    # Example usage
    print("Crypto Prediction Models")
    print("This module contains various ML models for crypto price prediction")
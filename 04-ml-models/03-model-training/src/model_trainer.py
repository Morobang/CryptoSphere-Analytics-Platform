# Model Training Pipeline
# Purpose: Train, evaluate, and tune machine learning models
# 
# This module provides:
# - Multiple ML algorithms for different use cases
# - Automated hyperparameter tuning
# - Cross-validation and model evaluation
# - Model comparison and selection
# - Experiment tracking and logging

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union
import joblib
import logging
from datetime import datetime
import json
import os
from sklearn.metrics import *
from sklearn.model_selection import cross_val_score, GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.svm import SVC, SVR
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
import xgboost as xgb
import lightgbm as lgb
from sklearn.neural_network import MLPClassifier, MLPRegressor
import warnings
warnings.filterwarnings('ignore')

class ModelTrainer:
    """
    Comprehensive model training and evaluation pipeline.
    
    This class provides:
    - Training multiple algorithms with automatic model selection
    - Hyperparameter optimization using grid search and random search
    - Cross-validation and robust model evaluation
    - Model comparison and performance tracking
    - Automated experiment logging and model persistence
    
    Example usage:
        trainer = ModelTrainer(task_type='classification')
        best_model = trainer.train_and_evaluate(
            X_train, y_train, X_val, y_val,
            models=['random_forest', 'xgboost', 'logistic_regression']
        )
    """
    
    def __init__(self, task_type: str = 'classification', random_state: int = 42):
        """
        Initialize the ModelTrainer.
        
        Args:
            task_type: Type of ML task ('classification' or 'regression')
            random_state: Random seed for reproducible results
        """
        self.task_type = task_type.lower()
        self.random_state = random_state
        self.models = {}
        self.results = {}
        self.best_model = None
        self.best_params = None
        self.experiment_log = []
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize model configurations
        self._initialize_model_configs()
    
    def _initialize_model_configs(self):
        """Initialize default configurations for different ML algorithms."""
        
        if self.task_type == 'classification':
            self.model_configs = {
                'logistic_regression': {
                    'model': LogisticRegression,
                    'params': {
                        'C': [0.001, 0.01, 0.1, 1, 10, 100],
                        'penalty': ['l1', 'l2', 'elasticnet'],
                        'solver': ['liblinear', 'saga'],
                        'max_iter': [1000]
                    }
                },
                'random_forest': {
                    'model': RandomForestClassifier,
                    'params': {
                        'n_estimators': [100, 200, 300],
                        'max_depth': [None, 10, 20, 30],
                        'min_samples_split': [2, 5, 10],
                        'min_samples_leaf': [1, 2, 4],
                        'max_features': ['auto', 'sqrt', 'log2']
                    }
                },
                'gradient_boosting': {
                    'model': GradientBoostingClassifier,
                    'params': {
                        'n_estimators': [100, 200, 300],
                        'learning_rate': [0.01, 0.1, 0.2],
                        'max_depth': [3, 5, 7],
                        'min_samples_split': [2, 5, 10],
                        'min_samples_leaf': [1, 2, 4]
                    }
                },
                'xgboost': {
                    'model': xgb.XGBClassifier,
                    'params': {
                        'n_estimators': [100, 200, 300],
                        'learning_rate': [0.01, 0.1, 0.2],
                        'max_depth': [3, 5, 7],
                        'min_child_weight': [1, 3, 5],
                        'subsample': [0.8, 0.9, 1.0],
                        'colsample_bytree': [0.8, 0.9, 1.0]
                    }
                },
                'lightgbm': {
                    'model': lgb.LGBMClassifier,
                    'params': {
                        'n_estimators': [100, 200, 300],
                        'learning_rate': [0.01, 0.1, 0.2],
                        'max_depth': [3, 5, 7],
                        'num_leaves': [31, 63, 127],
                        'feature_fraction': [0.8, 0.9, 1.0],
                        'bagging_fraction': [0.8, 0.9, 1.0]
                    }
                },
                'svm': {
                    'model': SVC,
                    'params': {
                        'C': [0.1, 1, 10, 100],
                        'kernel': ['rbf', 'poly', 'sigmoid'],
                        'gamma': ['scale', 'auto', 0.001, 0.01, 0.1],
                        'probability': [True]
                    }
                },
                'naive_bayes': {
                    'model': GaussianNB,
                    'params': {
                        'var_smoothing': [1e-9, 1e-8, 1e-7, 1e-6]
                    }
                },
                'knn': {
                    'model': KNeighborsClassifier,
                    'params': {
                        'n_neighbors': [3, 5, 7, 9, 11],
                        'weights': ['uniform', 'distance'],
                        'algorithm': ['auto', 'ball_tree', 'kd_tree', 'brute']
                    }
                },
                'decision_tree': {
                    'model': DecisionTreeClassifier,
                    'params': {
                        'max_depth': [None, 10, 20, 30],
                        'min_samples_split': [2, 5, 10],
                        'min_samples_leaf': [1, 2, 4],
                        'criterion': ['gini', 'entropy']
                    }
                },
                'neural_network': {
                    'model': MLPClassifier,
                    'params': {
                        'hidden_layer_sizes': [(50,), (100,), (50, 50), (100, 50)],
                        'activation': ['relu', 'tanh', 'logistic'],
                        'alpha': [0.0001, 0.001, 0.01],
                        'learning_rate': ['constant', 'adaptive'],
                        'max_iter': [500]
                    }
                }
            }
            
            # Default scoring metric for classification
            self.scoring_metric = 'accuracy'
            
        else:  # regression
            self.model_configs = {
                'linear_regression': {
                    'model': LinearRegression,
                    'params': {}
                },
                'ridge_regression': {
                    'model': Ridge,
                    'params': {
                        'alpha': [0.001, 0.01, 0.1, 1, 10, 100]
                    }
                },
                'lasso_regression': {
                    'model': Lasso,
                    'params': {
                        'alpha': [0.001, 0.01, 0.1, 1, 10, 100],
                        'max_iter': [1000]
                    }
                },
                'random_forest': {
                    'model': RandomForestRegressor,
                    'params': {
                        'n_estimators': [100, 200, 300],
                        'max_depth': [None, 10, 20, 30],
                        'min_samples_split': [2, 5, 10],
                        'min_samples_leaf': [1, 2, 4]
                    }
                },
                'gradient_boosting': {
                    'model': GradientBoostingRegressor,
                    'params': {
                        'n_estimators': [100, 200, 300],
                        'learning_rate': [0.01, 0.1, 0.2],
                        'max_depth': [3, 5, 7],
                        'min_samples_split': [2, 5, 10]
                    }
                },
                'xgboost': {
                    'model': xgb.XGBRegressor,
                    'params': {
                        'n_estimators': [100, 200, 300],
                        'learning_rate': [0.01, 0.1, 0.2],
                        'max_depth': [3, 5, 7],
                        'min_child_weight': [1, 3, 5]
                    }
                },
                'lightgbm': {
                    'model': lgb.LGBMRegressor,
                    'params': {
                        'n_estimators': [100, 200, 300],
                        'learning_rate': [0.01, 0.1, 0.2],
                        'max_depth': [3, 5, 7],
                        'num_leaves': [31, 63, 127]
                    }
                },
                'svm': {
                    'model': SVR,
                    'params': {
                        'C': [0.1, 1, 10, 100],
                        'kernel': ['rbf', 'poly', 'sigmoid'],
                        'gamma': ['scale', 'auto', 0.001, 0.01, 0.1]
                    }
                },
                'knn': {
                    'model': KNeighborsRegressor,
                    'params': {
                        'n_neighbors': [3, 5, 7, 9, 11],
                        'weights': ['uniform', 'distance']
                    }
                },
                'decision_tree': {
                    'model': DecisionTreeRegressor,
                    'params': {
                        'max_depth': [None, 10, 20, 30],
                        'min_samples_split': [2, 5, 10],
                        'min_samples_leaf': [1, 2, 4]
                    }
                },
                'neural_network': {
                    'model': MLPRegressor,
                    'params': {
                        'hidden_layer_sizes': [(50,), (100,), (50, 50), (100, 50)],
                        'activation': ['relu', 'tanh'],
                        'alpha': [0.0001, 0.001, 0.01],
                        'max_iter': [500]
                    }
                }
            }
            
            # Default scoring metric for regression
            self.scoring_metric = 'neg_mean_squared_error'
    
    def train_single_model(self,
                          model_name: str,
                          X_train: pd.DataFrame,
                          y_train: pd.Series,
                          X_val: pd.DataFrame = None,
                          y_val: pd.Series = None,
                          hyperparameter_tuning: bool = True,
                          cv_folds: int = 5,
                          tuning_method: str = 'random_search',
                          n_iter: int = 50) -> Dict[str, Any]:
        """
        Train a single model with optional hyperparameter tuning.
        
        Args:
            model_name: Name of the model to train
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)
            hyperparameter_tuning: Whether to perform hyperparameter tuning
            cv_folds: Number of cross-validation folds
            tuning_method: Method for hyperparameter tuning ('grid_search' or 'random_search')
            n_iter: Number of iterations for random search
            
        Returns:
            Dictionary containing model, parameters, and performance metrics
        """
        if model_name not in self.model_configs:
            raise ValueError(f"Model '{model_name}' not supported. Available models: {list(self.model_configs.keys())}")
        
        config = self.model_configs[model_name]
        model_class = config['model']
        param_grid = config['params']
        
        self.logger.info(f"Training {model_name}...")
        
        # Initialize base model
        base_model = model_class(random_state=self.random_state)
        
        if hyperparameter_tuning and param_grid:
            # Hyperparameter tuning
            self.logger.info(f"Performing hyperparameter tuning using {tuning_method}")
            
            if tuning_method == 'grid_search':
                search = GridSearchCV(
                    estimator=base_model,
                    param_grid=param_grid,
                    cv=cv_folds,
                    scoring=self.scoring_metric,
                    n_jobs=-1,
                    verbose=0,
                    return_train_score=True
                )
            else:  # random_search
                search = RandomizedSearchCV(
                    estimator=base_model,
                    param_distributions=param_grid,
                    n_iter=n_iter,
                    cv=cv_folds,
                    scoring=self.scoring_metric,
                    n_jobs=-1,
                    verbose=0,
                    random_state=self.random_state,
                    return_train_score=True
                )
            
            # Fit the search
            search.fit(X_train, y_train)
            best_model = search.best_estimator_
            best_params = search.best_params_
            cv_score = search.best_score_
            
        else:
            # Train without hyperparameter tuning
            best_model = base_model
            best_model.fit(X_train, y_train)
            best_params = {}
            
            # Get cross-validation score
            cv_scores = cross_val_score(best_model, X_train, y_train, cv=cv_folds, scoring=self.scoring_metric)
            cv_score = cv_scores.mean()
        
        # Evaluate on validation set if provided
        val_metrics = {}
        if X_val is not None and y_val is not None:
            val_predictions = best_model.predict(X_val)
            val_metrics = self._calculate_metrics(y_val, val_predictions)
        
        # Training set evaluation
        train_predictions = best_model.predict(X_train)
        train_metrics = self._calculate_metrics(y_train, train_predictions)
        
        # Feature importance (if available)
        feature_importance = None
        if hasattr(best_model, 'feature_importances_'):
            feature_importance = dict(zip(X_train.columns, best_model.feature_importances_))
        elif hasattr(best_model, 'coef_'):
            feature_importance = dict(zip(X_train.columns, abs(best_model.coef_.flatten())))
        
        result = {
            'model': best_model,
            'model_name': model_name,
            'best_params': best_params,
            'cv_score': cv_score,
            'train_metrics': train_metrics,
            'val_metrics': val_metrics,
            'feature_importance': feature_importance,
            'training_time': datetime.now(),
            'sample_size': len(X_train)
        }
        
        self.models[model_name] = result
        self.logger.info(f"Completed training {model_name}. CV Score: {cv_score:.4f}")
        
        return result
    
    def train_multiple_models(self,
                             X_train: pd.DataFrame,
                             y_train: pd.Series,
                             X_val: pd.DataFrame = None,
                             y_val: pd.Series = None,
                             models: List[str] = None,
                             hyperparameter_tuning: bool = True,
                             cv_folds: int = 5) -> Dict[str, Any]:
        """
        Train multiple models and compare their performance.
        
        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)
            models: List of model names to train (if None, trains all available models)
            hyperparameter_tuning: Whether to perform hyperparameter tuning
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dictionary containing results for all trained models
        """
        if models is None:
            models = list(self.model_configs.keys())
        
        self.logger.info(f"Training {len(models)} models: {models}")
        
        results = {}
        for model_name in models:
            try:
                result = self.train_single_model(
                    model_name=model_name,
                    X_train=X_train,
                    y_train=y_train,
                    X_val=X_val,
                    y_val=y_val,
                    hyperparameter_tuning=hyperparameter_tuning,
                    cv_folds=cv_folds
                )
                results[model_name] = result
            except Exception as e:
                self.logger.error(f"Error training {model_name}: {str(e)}")
                continue
        
        self.results = results
        
        # Select best model based on validation score or CV score
        best_model_name = self._select_best_model(results)
        if best_model_name:
            self.best_model = results[best_model_name]['model']
            self.best_params = results[best_model_name]['best_params']
            self.logger.info(f"Best model: {best_model_name}")
        
        return results
    
    def _select_best_model(self, results: Dict[str, Any]) -> str:
        """
        Select the best model based on performance metrics.
        
        Args:
            results: Dictionary of model results
            
        Returns:
            Name of the best performing model
        """
        if not results:
            return None
        
        best_score = -np.inf if 'accuracy' in self.scoring_metric or 'f1' in self.scoring_metric else np.inf
        best_model = None
        
        for model_name, result in results.items():
            # Use validation metrics if available, otherwise use CV score
            if result['val_metrics']:
                if self.task_type == 'classification':
                    score = result['val_metrics'].get('accuracy', result['cv_score'])
                else:
                    score = result['val_metrics'].get('r2', -result['val_metrics'].get('mse', np.inf))
            else:
                score = result['cv_score']
            
            # Handle negative scores (like neg_mean_squared_error)
            if 'neg_' in self.scoring_metric:
                score = -score
            
            if (best_score < score and ('accuracy' in self.scoring_metric or 'f1' in self.scoring_metric)) or \
               (best_score > score and 'error' in self.scoring_metric):
                best_score = score
                best_model = model_name
        
        return best_model
    
    def _calculate_metrics(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calculate performance metrics based on task type.
        
        Args:
            y_true: True labels/values
            y_pred: Predicted labels/values
            
        Returns:
            Dictionary of performance metrics
        """
        metrics = {}
        
        if self.task_type == 'classification':
            # Classification metrics
            metrics['accuracy'] = accuracy_score(y_true, y_pred)
            metrics['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
            metrics['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
            metrics['f1'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
            
            # For binary classification, add additional metrics
            if len(np.unique(y_true)) == 2:
                metrics['auc'] = roc_auc_score(y_true, y_pred)
                metrics['precision_binary'] = precision_score(y_true, y_pred, zero_division=0)
                metrics['recall_binary'] = recall_score(y_true, y_pred, zero_division=0)
                metrics['f1_binary'] = f1_score(y_true, y_pred, zero_division=0)
        
        else:  # regression
            # Regression metrics
            metrics['mse'] = mean_squared_error(y_true, y_pred)
            metrics['rmse'] = np.sqrt(metrics['mse'])
            metrics['mae'] = mean_absolute_error(y_true, y_pred)
            metrics['r2'] = r2_score(y_true, y_pred)
            
            # Additional regression metrics
            metrics['mape'] = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
            metrics['explained_variance'] = explained_variance_score(y_true, y_pred)
        
        return metrics
    
    def evaluate_model(self,
                      model: Any,
                      X_test: pd.DataFrame,
                      y_test: pd.Series,
                      model_name: str = 'model') -> Dict[str, Any]:
        """
        Evaluate a trained model on test data.
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test target
            model_name: Name of the model for logging
            
        Returns:
            Dictionary containing evaluation results
        """
        self.logger.info(f"Evaluating {model_name} on test data...")
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        test_metrics = self._calculate_metrics(y_test, y_pred)
        
        # Get prediction probabilities for classification
        y_proba = None
        if self.task_type == 'classification' and hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test)
        
        evaluation_result = {
            'model_name': model_name,
            'test_metrics': test_metrics,
            'predictions': y_pred,
            'probabilities': y_proba,
            'test_size': len(X_test),
            'evaluation_time': datetime.now()
        }
        
        self.logger.info(f"Test evaluation completed for {model_name}")
        if self.task_type == 'classification':
            self.logger.info(f"Test Accuracy: {test_metrics['accuracy']:.4f}")
            self.logger.info(f"Test F1 Score: {test_metrics['f1']:.4f}")
        else:
            self.logger.info(f"Test R² Score: {test_metrics['r2']:.4f}")
            self.logger.info(f"Test RMSE: {test_metrics['rmse']:.4f}")
        
        return evaluation_result
    
    def create_model_comparison(self) -> pd.DataFrame:
        """
        Create a comparison table of all trained models.
        
        Returns:
            DataFrame comparing model performance
        """
        if not self.results:
            return pd.DataFrame()
        
        comparison_data = []
        
        for model_name, result in self.results.items():
            row = {
                'Model': model_name,
                'CV_Score': result['cv_score'],
                'Sample_Size': result['sample_size']
            }
            
            # Add training metrics
            for metric, value in result['train_metrics'].items():
                row[f'Train_{metric.upper()}'] = value
            
            # Add validation metrics if available
            if result['val_metrics']:
                for metric, value in result['val_metrics'].items():
                    row[f'Val_{metric.upper()}'] = value
            
            comparison_data.append(row)
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Sort by validation score or CV score
        if self.task_type == 'classification':
            sort_column = 'Val_ACCURACY' if 'Val_ACCURACY' in comparison_df.columns else 'CV_Score'
            comparison_df = comparison_df.sort_values(sort_column, ascending=False)
        else:
            sort_column = 'Val_R2' if 'Val_R2' in comparison_df.columns else 'CV_Score'
            comparison_df = comparison_df.sort_values(sort_column, ascending=False)
        
        return comparison_df
    
    def get_feature_importance(self, model_name: str = None, top_n: int = 20) -> pd.DataFrame:
        """
        Get feature importance for a specific model or the best model.
        
        Args:
            model_name: Name of the model (if None, uses best model)
            top_n: Number of top features to return
            
        Returns:
            DataFrame with feature importance rankings
        """
        if model_name is None:
            # Use best model
            if not self.best_model:
                raise ValueError("No best model available. Train models first.")
            
            # Find the name of the best model
            for name, result in self.results.items():
                if result['model'] == self.best_model:
                    model_name = name
                    break
        
        if model_name not in self.results:
            raise ValueError(f"Model '{model_name}' not found in results.")
        
        feature_importance = self.results[model_name]['feature_importance']
        
        if feature_importance is None:
            return pd.DataFrame()
        
        # Convert to DataFrame and sort
        importance_df = pd.DataFrame([
            {'Feature': feature, 'Importance': importance}
            for feature, importance in feature_importance.items()
        ])
        
        importance_df = importance_df.sort_values('Importance', ascending=False).head(top_n)
        importance_df['Rank'] = range(1, len(importance_df) + 1)
        
        return importance_df[['Rank', 'Feature', 'Importance']]
    
    def save_model(self, model_name: str, filepath: str, include_metadata: bool = True):
        """
        Save a trained model to disk.
        
        Args:
            model_name: Name of the model to save
            filepath: Path to save the model
            include_metadata: Whether to save additional metadata
        """
        if model_name not in self.results:
            raise ValueError(f"Model '{model_name}' not found in results.")
        
        result = self.results[model_name]
        model = result['model']
        
        # Save the model
        joblib.dump(model, filepath)
        
        if include_metadata:
            # Save metadata
            metadata = {
                'model_name': model_name,
                'task_type': self.task_type,
                'best_params': result['best_params'],
                'cv_score': result['cv_score'],
                'train_metrics': result['train_metrics'],
                'val_metrics': result['val_metrics'],
                'feature_importance': result['feature_importance'],
                'training_time': result['training_time'].isoformat(),
                'sample_size': result['sample_size']
            }
            
            metadata_path = filepath.replace('.pkl', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
        
        self.logger.info(f"Model '{model_name}' saved to {filepath}")
    
    def load_model(self, filepath: str, metadata_path: str = None) -> Any:
        """
        Load a saved model from disk.
        
        Args:
            filepath: Path to the saved model
            metadata_path: Path to metadata file (optional)
            
        Returns:
            Loaded model
        """
        model = joblib.load(filepath)
        
        if metadata_path:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            self.logger.info(f"Loaded model with metadata: {metadata['model_name']}")
            return model, metadata
        
        return model
    
    def log_experiment(self, experiment_name: str, additional_info: Dict = None):
        """
        Log experiment details for tracking.
        
        Args:
            experiment_name: Name of the experiment
            additional_info: Additional information to log
        """
        experiment_log = {
            'experiment_name': experiment_name,
            'timestamp': datetime.now().isoformat(),
            'task_type': self.task_type,
            'models_trained': list(self.results.keys()) if self.results else [],
            'best_model': self._select_best_model(self.results) if self.results else None,
            'additional_info': additional_info or {}
        }
        
        self.experiment_log.append(experiment_log)
        self.logger.info(f"Logged experiment: {experiment_name}")
    
    def save_experiment_log(self, filepath: str):
        """
        Save experiment log to a JSON file.
        
        Args:
            filepath: Path to save the experiment log
        """
        with open(filepath, 'w') as f:
            json.dump(self.experiment_log, f, indent=2)
        
        self.logger.info(f"Experiment log saved to {filepath}")


# =============================================================================
# SPECIALIZED TRAINERS FOR COMMON USE CASES
# =============================================================================

class CustomerChurnPredictor(ModelTrainer):
    """
    Specialized trainer for customer churn prediction.
    
    This class extends ModelTrainer with domain-specific features:
    - Optimized for imbalanced churn datasets
    - Custom feature engineering for customer behavior
    - Business-relevant evaluation metrics
    """
    
    def __init__(self, random_state: int = 42):
        super().__init__(task_type='classification', random_state=random_state)
        
        # Override scoring metric for imbalanced churn data
        self.scoring_metric = 'f1'
        
        # Add class balancing to model configs
        for model_config in self.model_configs.values():
            if hasattr(model_config['model'], '__init__'):
                # Add class_weight parameter for applicable models
                if 'class_weight' in model_config['model'].__init__.__code__.co_varnames:
                    model_config['params']['class_weight'] = ['balanced', None]
    
    def calculate_business_impact(self, y_true: pd.Series, y_pred: np.ndarray, 
                                 avg_customer_value: float = 1000,
                                 retention_cost: float = 50) -> Dict[str, float]:
        """
        Calculate business impact metrics for churn prediction.
        
        Args:
            y_true: True churn labels (1 = churned, 0 = retained)
            y_pred: Predicted churn labels
            avg_customer_value: Average annual customer value
            retention_cost: Cost to retain a customer
            
        Returns:
            Dictionary with business impact metrics
        """
        # Confusion matrix components
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        # Business calculations
        prevented_churn_value = tp * avg_customer_value  # Correctly identified churners
        false_positive_cost = fp * retention_cost  # Cost of unnecessary retention efforts
        missed_churn_loss = fn * avg_customer_value  # Lost revenue from missed churners
        
        total_impact = prevented_churn_value - false_positive_cost - missed_churn_loss
        
        business_metrics = {
            'prevented_churn_value': prevented_churn_value,
            'false_positive_cost': false_positive_cost, 
            'missed_churn_loss': missed_churn_loss,
            'total_business_impact': total_impact,
            'roi': (prevented_churn_value - false_positive_cost) / false_positive_cost if false_positive_cost > 0 else 0,
            'customers_to_target': tp + fp,  # Customers to target with retention campaigns
            'retention_efficiency': tp / (tp + fp) if (tp + fp) > 0 else 0  # Success rate of retention targeting
        }
        
        return business_metrics


class SalesForecaster(ModelTrainer):
    """
    Specialized trainer for sales forecasting models.
    
    This class extends ModelTrainer with time-series specific features:
    - Time-aware cross-validation
    - Seasonality handling
    - Forecast-specific evaluation metrics
    """
    
    def __init__(self, random_state: int = 42):
        super().__init__(task_type='regression', random_state=random_state)
        
        # Override scoring metric for forecasting
        self.scoring_metric = 'neg_mean_absolute_error'
    
    def create_time_features(self, df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """
        Create time-based features for sales forecasting.
        
        Args:
            df: Input DataFrame with date column
            date_column: Name of the date column
            
        Returns:
            DataFrame with additional time features
        """
        df_enhanced = df.copy()
        date_col = pd.to_datetime(df_enhanced[date_column])
        
        # Time-based features
        df_enhanced['year'] = date_col.dt.year
        df_enhanced['month'] = date_col.dt.month
        df_enhanced['quarter'] = date_col.dt.quarter
        df_enhanced['day_of_year'] = date_col.dt.dayofyear
        df_enhanced['week_of_year'] = date_col.dt.isocalendar().week
        df_enhanced['day_of_week'] = date_col.dt.dayofweek
        df_enhanced['is_weekend'] = date_col.dt.dayofweek.isin([5, 6])
        df_enhanced['is_month_start'] = date_col.dt.is_month_start
        df_enhanced['is_month_end'] = date_col.dt.is_month_end
        df_enhanced['is_quarter_start'] = date_col.dt.is_quarter_start
        df_enhanced['is_quarter_end'] = date_col.dt.is_quarter_end
        
        # Seasonal features using sine/cosine transformations
        df_enhanced['month_sin'] = np.sin(2 * np.pi * df_enhanced['month'] / 12)
        df_enhanced['month_cos'] = np.cos(2 * np.pi * df_enhanced['month'] / 12)
        df_enhanced['day_of_year_sin'] = np.sin(2 * np.pi * df_enhanced['day_of_year'] / 365)
        df_enhanced['day_of_year_cos'] = np.cos(2 * np.pi * df_enhanced['day_of_year'] / 365)
        
        return df_enhanced
    
    def calculate_forecast_metrics(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calculate forecast-specific evaluation metrics.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Dictionary with forecast metrics
        """
        metrics = self._calculate_metrics(y_true, y_pred)
        
        # Additional forecast-specific metrics
        metrics['mape'] = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        metrics['smape'] = np.mean(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred))) * 100
        
        # Directional accuracy (percentage of correct direction predictions)
        if len(y_true) > 1:
            true_direction = np.diff(y_true) > 0
            pred_direction = np.diff(y_pred) > 0
            metrics['directional_accuracy'] = np.mean(true_direction == pred_direction) * 100
        
        return metrics


# =============================================================================
# EXAMPLE USAGE AND TESTING
# =============================================================================

if __name__ == "__main__":
    """
    Example usage of the ModelTrainer classes.
    This section demonstrates how to use the trainers in practice.
    """
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Example: Create sample data for testing
    np.random.seed(42)
    n_samples = 1000
    
    # Classification example data
    classification_data = pd.DataFrame({
        'feature_1': np.random.normal(0, 1, n_samples),
        'feature_2': np.random.normal(2, 1.5, n_samples),
        'feature_3': np.random.exponential(1, n_samples),
        'feature_4': np.random.choice(['A', 'B', 'C'], n_samples),
        'feature_5': np.random.randint(0, 10, n_samples),
    })
    
    # Create synthetic target with some correlation to features
    classification_data['target'] = (
        (classification_data['feature_1'] > 0).astype(int) +
        (classification_data['feature_2'] > 2).astype(int) +
        np.random.choice([0, 1], n_samples, p=[0.7, 0.3])
    ) % 2
    
    print("Classification Dataset Created:")
    print(f"Shape: {classification_data.shape}")
    print(f"Target distribution:\n{classification_data['target'].value_counts()}")
    
    # Prepare data for ML
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    classification_data['feature_4_encoded'] = le.fit_transform(classification_data['feature_4'])
    
    X = classification_data.drop(['target', 'feature_4'], axis=1)
    y = classification_data['target']
    
    # Split data
    from sklearn.model_selection import train_test_split
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)
    
    print(f"\nData splits created:")
    print(f"Training: {X_train.shape[0]} samples")
    print(f"Validation: {X_val.shape[0]} samples")
    print(f"Test: {X_test.shape[0]} samples")
    
    # Example 1: Standard ModelTrainer
    print("\n" + "="*50)
    print("EXAMPLE 1: Standard Classification Trainer")
    print("="*50)
    
    trainer = ModelTrainer(task_type='classification', random_state=42)
    
    # Train multiple models
    models_to_train = ['logistic_regression', 'random_forest', 'xgboost']
    results = trainer.train_multiple_models(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        models=models_to_train,
        hyperparameter_tuning=True,
        cv_folds=3  # Reduced for faster execution
    )
    
    # Show model comparison
    comparison = trainer.create_model_comparison()
    print("\nModel Comparison:")
    print(comparison.round(4))
    
    # Get feature importance for best model
    feature_importance = trainer.get_feature_importance(top_n=10)
    print(f"\nTop Features for Best Model:")
    print(feature_importance)
    
    # Evaluate best model on test set
    if trainer.best_model:
        test_evaluation = trainer.evaluate_model(
            model=trainer.best_model,
            X_test=X_test,
            y_test=y_test,
            model_name="best_model"
        )
        print(f"\nTest Set Evaluation:")
        for metric, value in test_evaluation['test_metrics'].items():
            print(f"{metric}: {value:.4f}")
    
    # Example 2: Customer Churn Predictor
    print("\n" + "="*50)
    print("EXAMPLE 2: Customer Churn Predictor")
    print("="*50)
    
    churn_trainer = CustomerChurnPredictor(random_state=42)
    
    # Train churn models (using same data for demonstration)
    churn_results = churn_trainer.train_single_model(
        model_name='random_forest',
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        hyperparameter_tuning=False  # Skip tuning for faster execution
    )
    
    # Calculate business impact
    val_predictions = churn_results['model'].predict(X_val)
    business_impact = churn_trainer.calculate_business_impact(
        y_true=y_val,
        y_pred=val_predictions,
        avg_customer_value=1200,
        retention_cost=75
    )
    
    print(f"\nBusiness Impact Analysis:")
    for metric, value in business_impact.items():
        if 'value' in metric or 'cost' in metric or 'loss' in metric or 'impact' in metric:
            print(f"{metric}: ${value:,.2f}")
        else:
            print(f"{metric}: {value:.4f}")
    
    # Save models and experiment log
    print(f"\nSaving models and experiment logs...")
    
    # Create directory for saving models
    os.makedirs('saved_models', exist_ok=True)
    
    # Save best model
    if trainer.best_model:
        best_model_name = None
        for name, result in trainer.results.items():
            if result['model'] == trainer.best_model:
                best_model_name = name
                break
        
        if best_model_name:
            trainer.save_model(
                model_name=best_model_name,
                filepath=f'saved_models/{best_model_name}_model.pkl',
                include_metadata=True
            )
    
    # Log experiment
    trainer.log_experiment(
        experiment_name='model_training_example',
        additional_info={
            'dataset_size': len(X),
            'models_compared': len(models_to_train),
            'best_model_score': trainer.results[best_model_name]['cv_score'] if best_model_name else None
        }
    )
    
    # Save experiment log
    trainer.save_experiment_log('experiment_log.json')
    
    print("\nModel training pipeline completed successfully!")
    print("Models saved to 'saved_models/' directory")
    print("Experiment log saved to 'experiment_log.json'")
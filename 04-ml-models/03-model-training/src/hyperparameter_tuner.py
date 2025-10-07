"""
Hyperparameter Tuning for Cryptocurrency ML Models

This module handles automated hyperparameter optimization for cryptocurrency 
prediction models using various search strategies.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, cross_val_score
from sklearn.metrics import make_scorer, mean_squared_error
import optuna
from typing import Dict, List, Tuple, Optional, Any, Callable
import warnings
warnings.filterwarnings('ignore')


class CryptoHyperparameterTuner:
    """
    Automated hyperparameter tuning for cryptocurrency prediction models.
    """
    
    def __init__(self, cv_folds: int = 5, scoring: str = 'neg_mean_squared_error'):
        """
        Initialize the hyperparameter tuner.
        
        Args:
            cv_folds: Number of cross-validation folds
            scoring: Scoring metric for optimization
        """
        self.cv_folds = cv_folds
        self.scoring = scoring
        self.best_params = {}
        self.tuning_results = {}
        
    def get_parameter_grids(self) -> Dict:
        """
        Get parameter grids for different model types.
        
        Returns:
            Dictionary with parameter grids for each model type
        """
        return {
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'max_features': ['auto', 'sqrt', 'log2']
            },
            'xgboost': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 6, 9],
                'min_child_weight': [1, 3, 5],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0]
            },
            'lightgbm': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [-1, 5, 10],
                'num_leaves': [31, 50, 100],
                'min_data_in_leaf': [10, 20, 30],
                'feature_fraction': [0.8, 0.9, 1.0]
            },
            'svr': {
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.01, 0.1, 1],
                'kernel': ['rbf', 'poly', 'sigmoid'],
                'epsilon': [0.01, 0.1, 0.2]
            },
            'ridge': {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            },
            'lasso': {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            }
        }
    
    def get_parameter_distributions(self) -> Dict:
        """
        Get parameter distributions for randomized search.
        
        Returns:
            Dictionary with parameter distributions for each model type
        """
        from scipy.stats import uniform, randint
        
        return {
            'random_forest': {
                'n_estimators': randint(50, 300),
                'max_depth': randint(5, 20),
                'min_samples_split': randint(2, 20),
                'min_samples_leaf': randint(1, 10),
                'max_features': ['auto', 'sqrt', 'log2']
            },
            'xgboost': {
                'n_estimators': randint(50, 300),
                'learning_rate': uniform(0.01, 0.3),
                'max_depth': randint(3, 10),
                'min_child_weight': randint(1, 10),
                'subsample': uniform(0.6, 0.4),
                'colsample_bytree': uniform(0.6, 0.4)
            },
            'lightgbm': {
                'n_estimators': randint(50, 300),
                'learning_rate': uniform(0.01, 0.3),
                'max_depth': randint(-1, 15),
                'num_leaves': randint(20, 200),
                'min_data_in_leaf': randint(5, 50),
                'feature_fraction': uniform(0.4, 0.6)
            }
        }
    
    def grid_search_tuning(self, model, param_grid: Dict, X_train: pd.DataFrame, 
                          y_train: pd.Series) -> Dict:
        """
        Perform grid search hyperparameter tuning.
        
        Args:
            model: Model instance
            param_grid: Parameter grid to search
            X_train: Training features
            y_train: Training targets
            
        Returns:
            Dictionary with tuning results
        """
        print("Performing grid search...")
        
        grid_search = GridSearchCV(
            estimator=model,
            param_grid=param_grid,
            cv=self.cv_folds,
            scoring=self.scoring,
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        results = {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'best_estimator': grid_search.best_estimator_,
            'cv_results': grid_search.cv_results_
        }
        
        return results
    
    def random_search_tuning(self, model, param_distributions: Dict, X_train: pd.DataFrame,
                           y_train: pd.Series, n_iter: int = 100) -> Dict:
        """
        Perform randomized search hyperparameter tuning.
        
        Args:
            model: Model instance
            param_distributions: Parameter distributions to sample from
            X_train: Training features
            y_train: Training targets
            n_iter: Number of parameter settings to sample
            
        Returns:
            Dictionary with tuning results
        """
        print(f"Performing randomized search with {n_iter} iterations...")
        
        random_search = RandomizedSearchCV(
            estimator=model,
            param_distributions=param_distributions,
            n_iter=n_iter,
            cv=self.cv_folds,
            scoring=self.scoring,
            n_jobs=-1,
            verbose=1,
            random_state=42
        )
        
        random_search.fit(X_train, y_train)
        
        results = {
            'best_params': random_search.best_params_,
            'best_score': random_search.best_score_,
            'best_estimator': random_search.best_estimator_,
            'cv_results': random_search.cv_results_
        }
        
        return results
    
    def optuna_tuning(self, model_factory: Callable, X_train: pd.DataFrame,
                     y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series,
                     n_trials: int = 100) -> Dict:
        """
        Perform Optuna-based hyperparameter optimization.
        
        Args:
            model_factory: Function that creates model with given parameters
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            n_trials: Number of optimization trials
            
        Returns:
            Dictionary with tuning results
        """
        print(f"Performing Optuna optimization with {n_trials} trials...")
        
        def objective(trial):
            # This would need to be customized for each model type
            # Example for XGBoost:
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0)
            }
            
            model = model_factory(**params)
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_val)
            mse = mean_squared_error(y_val, y_pred)
            
            return mse
        
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=n_trials)
        
        results = {
            'best_params': study.best_params,
            'best_score': study.best_value,
            'study': study
        }
        
        return results
    
    def tune_model(self, model_type: str, model, X_train: pd.DataFrame, y_train: pd.Series,
                  X_val: pd.DataFrame = None, y_val: pd.Series = None,
                  method: str = 'grid_search') -> Dict:
        """
        Tune hyperparameters for a specific model.
        
        Args:
            model_type: Type of model being tuned
            model: Model instance
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
            method: Tuning method ('grid_search', 'random_search', 'optuna')
            
        Returns:
            Dictionary with tuning results
        """
        param_grids = self.get_parameter_grids()
        param_distributions = self.get_parameter_distributions()
        
        if method == 'grid_search':
            if model_type in param_grids:
                results = self.grid_search_tuning(
                    model, param_grids[model_type], X_train, y_train
                )
            else:
                raise ValueError(f"No parameter grid defined for {model_type}")
                
        elif method == 'random_search':
            if model_type in param_distributions:
                results = self.random_search_tuning(
                    model, param_distributions[model_type], X_train, y_train
                )
            else:
                raise ValueError(f"No parameter distribution defined for {model_type}")
                
        elif method == 'optuna':
            if X_val is None or y_val is None:
                raise ValueError("Validation data required for Optuna tuning")
            
            # This would need model-specific factory functions
            # For now, return placeholder
            results = {'message': 'Optuna tuning not fully implemented yet'}
            
        else:
            raise ValueError(f"Unknown tuning method: {method}")
        
        # Store results
        self.tuning_results[model_type] = results
        if 'best_params' in results:
            self.best_params[model_type] = results['best_params']
        
        return results
    
    def tune_multiple_models(self, models: Dict, X_train: pd.DataFrame, y_train: pd.Series,
                           X_val: pd.DataFrame = None, y_val: pd.Series = None,
                           method: str = 'grid_search') -> Dict:
        """
        Tune hyperparameters for multiple models.
        
        Args:
            models: Dictionary of {model_name: model_instance}
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
            method: Tuning method to use
            
        Returns:
            Dictionary with results for all models
        """
        results = {}
        
        for model_name, model in models.items():
            try:
                print(f"\nTuning {model_name}...")
                result = self.tune_model(
                    model_name, model, X_train, y_train, X_val, y_val, method
                )
                results[model_name] = result
                print(f"✓ {model_name} tuning completed")
            except Exception as e:
                print(f"✗ Error tuning {model_name}: {str(e)}")
                results[model_name] = {'error': str(e)}
        
        return results
    
    def get_best_parameters(self, model_type: str) -> Dict:
        """
        Get best parameters for a specific model type.
        
        Args:
            model_type: Type of model
            
        Returns:
            Dictionary with best parameters
        """
        return self.best_params.get(model_type, {})
    
    def create_tuned_models(self) -> Dict:
        """
        Create model instances with tuned parameters.
        
        Returns:
            Dictionary of tuned model instances
        """
        from .prediction_models import CryptoPredictionModels
        
        model_factory = CryptoPredictionModels()
        tuned_models = {}
        
        for model_type, best_params in self.best_params.items():
            try:
                tuned_model = model_factory.create_model(model_type, best_params)
                tuned_models[model_type] = tuned_model
            except Exception as e:
                print(f"Error creating tuned {model_type}: {str(e)}")
        
        return tuned_models
    
    def generate_tuning_report(self) -> Dict:
        """
        Generate comprehensive tuning report.
        
        Returns:
            Dictionary with tuning summary
        """
        report = {
            'tuning_summary': {
                'models_tuned': list(self.best_params.keys()),
                'total_models': len(self.tuning_results),
                'cv_folds': self.cv_folds,
                'scoring_metric': self.scoring
            },
            'best_parameters': self.best_params,
            'performance_improvements': {}
        }
        
        # Calculate performance improvements if available
        for model_type, results in self.tuning_results.items():
            if 'best_score' in results:
                report['performance_improvements'][model_type] = {
                    'best_cv_score': results['best_score']
                }
        
        return report


if __name__ == "__main__":
    # Example usage
    print("Crypto Hyperparameter Tuner")
    print("This module handles automated hyperparameter optimization")
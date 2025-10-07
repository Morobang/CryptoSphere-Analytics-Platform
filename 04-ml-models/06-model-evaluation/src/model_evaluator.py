"""
Model Performance Evaluator for Cryptocurrency Predictions

This module provides comprehensive evaluation metrics and analysis tools
for cryptocurrency prediction models.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')


class CryptoModelEvaluator:
    """
    Comprehensive evaluation of cryptocurrency prediction models.
    """
    
    def __init__(self):
        """Initialize the model evaluator."""
        self.evaluation_results = {}
        self.models = {}
        self.predictions = {}
        
    def evaluate_model(self, model_name: str, model: Any, X_test: pd.DataFrame, 
                      y_test: pd.Series, y_pred: np.ndarray = None) -> Dict:
        """
        Evaluate a single model's performance.
        
        Args:
            model_name: Name of the model
            model: Trained model instance
            X_test: Test features
            y_test: True test targets
            y_pred: Predictions (optional, will be generated if not provided)
            
        Returns:
            Dictionary with evaluation results
        """
        if y_pred is None:
            y_pred = model.predict(X_test)
        
        # Store for later use
        self.models[model_name] = model
        self.predictions[model_name] = y_pred
        
        # Calculate basic regression metrics
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Calculate additional crypto-specific metrics
        directional_accuracy = self._calculate_directional_accuracy(y_test, y_pred)
        mape = self._calculate_mape(y_test, y_pred)
        max_error = np.max(np.abs(y_test - y_pred))
        
        # Calculate prediction bias
        bias = np.mean(y_pred - y_test)
        
        # Calculate volatility metrics
        prediction_volatility = np.std(y_pred)
        actual_volatility = np.std(y_test)
        volatility_ratio = prediction_volatility / actual_volatility if actual_volatility != 0 else np.inf
        
        results = {
            'model_name': model_name,
            'rmse': rmse,
            'mae': mae,
            'mse': mse,
            'r2_score': r2,
            'directional_accuracy': directional_accuracy,
            'mape': mape,
            'max_error': max_error,
            'bias': bias,
            'prediction_volatility': prediction_volatility,
            'actual_volatility': actual_volatility,
            'volatility_ratio': volatility_ratio,
            'num_predictions': len(y_pred)
        }
        
        self.evaluation_results[model_name] = results
        return results
    
    def evaluate_multiple_models(self, models: Dict, X_test: pd.DataFrame, 
                                y_test: pd.Series) -> pd.DataFrame:
        """
        Evaluate multiple models and return comparison DataFrame.
        
        Args:
            models: Dictionary of {model_name: model_instance}
            X_test: Test features
            y_test: True test targets
            
        Returns:
            DataFrame with evaluation results for all models
        """
        results = []
        
        for model_name, model in models.items():
            try:
                result = self.evaluate_model(model_name, model, X_test, y_test)
                results.append(result)
                print(f"✓ Evaluated {model_name}")
            except Exception as e:
                print(f"✗ Error evaluating {model_name}: {str(e)}")
                # Add error result
                error_result = {
                    'model_name': model_name,
                    'error': str(e)
                }
                results.append(error_result)
        
        return pd.DataFrame(results)
    
    def rank_models(self, metric: str = 'rmse', ascending: bool = True) -> pd.DataFrame:
        """
        Rank models by specified metric.
        
        Args:
            metric: Metric to rank by
            ascending: Whether to rank in ascending order
            
        Returns:
            DataFrame with ranked models
        """
        if not self.evaluation_results:
            raise ValueError("No evaluation results available. Run evaluation first.")
        
        results_df = pd.DataFrame(self.evaluation_results).T
        
        if metric not in results_df.columns:
            raise ValueError(f"Metric '{metric}' not found in evaluation results")
        
        ranked_df = results_df.sort_values(metric, ascending=ascending)
        ranked_df['rank'] = range(1, len(ranked_df) + 1)
        
        return ranked_df
    
    def calculate_trading_metrics(self, model_name: str, y_test: pd.Series, 
                                price_data: pd.Series) -> Dict:
        """
        Calculate trading-specific metrics.
        
        Args:
            model_name: Name of the model
            y_test: True price changes/returns
            price_data: Actual price data
            
        Returns:
            Dictionary with trading metrics
        """
        if model_name not in self.predictions:
            raise ValueError(f"No predictions found for {model_name}")
        
        y_pred = self.predictions[model_name]
        
        # Create trading signals based on predictions
        # Buy signal when predicted return > threshold, sell when < threshold
        threshold = 0.01  # 1% threshold
        
        predicted_signals = np.where(y_pred > threshold, 1, 
                                   np.where(y_pred < -threshold, -1, 0))
        actual_returns = y_test.values
        
        # Calculate strategy returns
        strategy_returns = predicted_signals * actual_returns
        
        # Calculate cumulative returns
        cumulative_strategy_returns = np.cumprod(1 + strategy_returns) - 1
        cumulative_market_returns = np.cumprod(1 + actual_returns) - 1
        
        # Calculate Sharpe ratio (assuming risk-free rate = 0)
        if np.std(strategy_returns) != 0:
            sharpe_ratio = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # Calculate maximum drawdown
        strategy_cumulative = np.cumprod(1 + strategy_returns)
        rolling_max = np.maximum.accumulate(strategy_cumulative)
        drawdown = (strategy_cumulative - rolling_max) / rolling_max
        max_drawdown = np.min(drawdown)
        
        # Calculate hit rate (percentage of correct directional predictions)
        correct_direction = np.sign(y_pred) == np.sign(actual_returns)
        hit_rate = np.mean(correct_direction[actual_returns != 0])  # Exclude zero returns
        
        return {
            'model_name': model_name,
            'total_strategy_return': cumulative_strategy_returns[-1],
            'total_market_return': cumulative_market_returns[-1],
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'hit_rate': hit_rate,
            'num_trades': np.sum(predicted_signals != 0),
            'avg_trade_return': np.mean(strategy_returns[predicted_signals != 0])
        }
    
    def analyze_prediction_errors(self, model_name: str, y_test: pd.Series, 
                                 feature_names: List[str] = None) -> Dict:
        """
        Analyze prediction errors in detail.
        
        Args:
            model_name: Name of the model
            y_test: True test targets
            feature_names: List of feature names
            
        Returns:
            Dictionary with error analysis
        """
        if model_name not in self.predictions:
            raise ValueError(f"No predictions found for {model_name}")
        
        y_pred = self.predictions[model_name]
        errors = y_test - y_pred
        
        # Error statistics
        error_stats = {
            'mean_error': np.mean(errors),
            'std_error': np.std(errors),
            'median_error': np.median(errors),
            'q75_error': np.percentile(errors, 75),
            'q25_error': np.percentile(errors, 25),
            'max_positive_error': np.max(errors),
            'max_negative_error': np.min(errors)
        }
        
        # Identify patterns in errors
        large_errors_idx = np.abs(errors) > np.percentile(np.abs(errors), 95)
        large_errors = errors[large_errors_idx]
        
        # Error distribution analysis
        positive_errors = errors[errors > 0]
        negative_errors = errors[errors < 0]
        
        analysis = {
            'model_name': model_name,
            'error_statistics': error_stats,
            'large_errors_count': len(large_errors),
            'large_errors_percentage': len(large_errors) / len(errors) * 100,
            'positive_errors_count': len(positive_errors),
            'negative_errors_count': len(negative_errors),
            'error_skewness': self._calculate_skewness(errors),
            'error_kurtosis': self._calculate_kurtosis(errors)
        }
        
        return analysis
    
    def create_evaluation_visualizations(self, model_names: List[str] = None, 
                                       save_path: str = None) -> None:
        """
        Create comprehensive evaluation visualizations.
        
        Args:
            model_names: List of model names to visualize
            save_path: Path to save visualizations
        """
        if model_names is None:
            model_names = list(self.evaluation_results.keys())
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Model Evaluation Dashboard', fontsize=16)
        
        # 1. Model comparison bar chart
        metrics_df = pd.DataFrame(self.evaluation_results).T
        metrics_to_plot = ['rmse', 'mae', 'r2_score', 'directional_accuracy']
        
        for i, metric in enumerate(metrics_to_plot):
            if metric in metrics_df.columns:
                ax = axes[i//2, i%2]
                metrics_df[metric].plot(kind='bar', ax=ax, title=f'{metric.upper()} by Model')
                ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(f"{save_path}/model_evaluation_dashboard.png", dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def generate_evaluation_report(self, output_file: str = None) -> Dict:
        """
        Generate comprehensive evaluation report.
        
        Args:
            output_file: Optional file path to save report
            
        Returns:
            Dictionary with evaluation report
        """
        if not self.evaluation_results:
            raise ValueError("No evaluation results available")
        
        # Best models by different metrics
        metrics_df = pd.DataFrame(self.evaluation_results).T
        
        report = {
            'evaluation_summary': {
                'total_models_evaluated': len(self.evaluation_results),
                'metrics_calculated': list(metrics_df.columns),
                'evaluation_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'best_models': {
                'lowest_rmse': metrics_df['rmse'].idxmin(),
                'lowest_mae': metrics_df['mae'].idxmin(),
                'highest_r2': metrics_df['r2_score'].idxmax(),
                'highest_directional_accuracy': metrics_df['directional_accuracy'].idxmax()
            },
            'model_rankings': {
                'by_rmse': self.rank_models('rmse', ascending=True)['model_name'].tolist(),
                'by_r2': self.rank_models('r2_score', ascending=False)['model_name'].tolist()
            },
            'detailed_results': self.evaluation_results
        }
        
        # Save report if requested
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        
        return report
    
    def _calculate_directional_accuracy(self, y_true: pd.Series, y_pred: np.ndarray) -> float:
        """Calculate directional accuracy (percentage of correct trend predictions)."""
        if len(y_true) < 2:
            return 0.0
        
        true_direction = np.diff(y_true) > 0
        pred_direction = np.diff(y_pred) > 0
        
        return np.mean(true_direction == pred_direction)
    
    def _calculate_mape(self, y_true: pd.Series, y_pred: np.ndarray) -> float:
        """Calculate Mean Absolute Percentage Error."""
        return np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of data."""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std) ** 3)
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of data."""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std) ** 4) - 3


if __name__ == "__main__":
    # Example usage
    print("Crypto Model Evaluator")
    print("This module provides comprehensive evaluation of crypto prediction models")
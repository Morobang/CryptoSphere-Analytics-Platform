"""
Data Scaling and Normalization for Cryptocurrency ML Models

This module handles scaling and normalization of cryptocurrency features
to prepare them for machine learning algorithms.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, PowerTransformer
from sklearn.model_selection import train_test_split
from typing import Dict, List, Tuple, Optional, Any
import pickle
import warnings
warnings.filterwarnings('ignore')


class CryptoDataScaler:
    """
    Comprehensive data scaling and normalization for cryptocurrency features.
    """
    
    def __init__(self, scaling_method: str = 'standard'):
        """
        Initialize the data scaler.
        
        Args:
            scaling_method: Type of scaling ('standard', 'minmax', 'robust', 'power')
        """
        self.scaling_method = scaling_method
        self.scalers = {}
        self.feature_columns = []
        self.target_columns = []
        
        # Initialize scaler based on method
        if scaling_method == 'standard':
            self.base_scaler = StandardScaler()
        elif scaling_method == 'minmax':
            self.base_scaler = MinMaxScaler()
        elif scaling_method == 'robust':
            self.base_scaler = RobustScaler()
        elif scaling_method == 'power':
            self.base_scaler = PowerTransformer(method='yeo-johnson')
        else:
            raise ValueError(f"Unknown scaling method: {scaling_method}")
    
    def identify_feature_types(self, data: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Identify different types of features for appropriate scaling.
        
        Args:
            data: Input DataFrame
            
        Returns:
            Dictionary with feature types and column names
        """
        feature_types = {
            'price_features': [],
            'volume_features': [],
            'technical_indicators': [],
            'time_features': [],
            'percentage_features': [],
            'ratio_features': [],
            'target_features': []
        }
        
        for col in data.columns:
            col_lower = col.lower()
            
            if col.startswith('target_'):
                feature_types['target_features'].append(col)
            elif any(x in col_lower for x in ['price', 'close', 'open', 'high', 'low']):
                feature_types['price_features'].append(col)
            elif any(x in col_lower for x in ['volume', 'obv']):
                feature_types['volume_features'].append(col)
            elif any(x in col_lower for x in ['rsi', 'macd', 'bb_', 'sma', 'ema', 'atr', 'cci', 'mfi', 'stoch', 'williams']):
                feature_types['technical_indicators'].append(col)
            elif any(x in col_lower for x in ['hour', 'day', 'month', 'year', 'sin', 'cos', 'weekend']):
                feature_types['time_features'].append(col)
            elif any(x in col_lower for x in ['change', 'return', 'pct']):
                feature_types['percentage_features'].append(col)
            elif any(x in col_lower for x in ['ratio', 'position', 'dominance']):
                feature_types['ratio_features'].append(col)
        
        return feature_types
    
    def fit_scalers(self, data: pd.DataFrame, feature_types: Dict[str, List[str]] = None) -> None:
        """
        Fit scalers for different feature types.
        
        Args:
            data: Training data
            feature_types: Dictionary of feature types (optional)
        """
        if feature_types is None:
            feature_types = self.identify_feature_types(data)
        
        # Fit different scalers for different feature types
        for feature_type, columns in feature_types.items():
            if not columns or feature_type == 'target_features':
                continue
            
            # Select appropriate scaler for feature type
            if feature_type == 'price_features':
                scaler = StandardScaler()  # Price features often need standard scaling
            elif feature_type == 'volume_features':
                scaler = RobustScaler()  # Volume can have extreme outliers
            elif feature_type == 'technical_indicators':
                scaler = MinMaxScaler()  # Many indicators are bounded
            elif feature_type == 'time_features':
                scaler = StandardScaler()  # Time features are usually well-behaved
            elif feature_type == 'percentage_features':
                scaler = StandardScaler()  # Returns and changes
            elif feature_type == 'ratio_features':
                scaler = RobustScaler()  # Ratios can have outliers
            else:
                scaler = self.base_scaler
            
            # Fit scaler on available columns
            available_columns = [col for col in columns if col in data.columns]
            if available_columns:
                scaler.fit(data[available_columns].fillna(0))
                self.scalers[feature_type] = {
                    'scaler': scaler,
                    'columns': available_columns
                }
    
    def transform_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform data using fitted scalers.
        
        Args:
            data: Data to transform
            
        Returns:
            Scaled DataFrame
        """
        if not self.scalers:
            raise ValueError("Scalers not fitted. Call fit_scalers first.")
        
        df = data.copy()
        
        # Apply scaling for each feature type
        for feature_type, scaler_info in self.scalers.items():
            scaler = scaler_info['scaler']
            columns = scaler_info['columns']
            
            # Only transform columns that exist in current data
            available_columns = [col for col in columns if col in df.columns]
            if available_columns:
                df[available_columns] = scaler.transform(df[available_columns].fillna(0))
        
        return df
    
    def inverse_transform_data(self, data: pd.DataFrame, feature_types: List[str] = None) -> pd.DataFrame:
        """
        Inverse transform scaled data back to original scale.
        
        Args:
            data: Scaled data
            feature_types: Types of features to inverse transform
            
        Returns:
            Data in original scale
        """
        if not self.scalers:
            raise ValueError("Scalers not fitted. Call fit_scalers first.")
        
        df = data.copy()
        
        # If no specific feature types specified, inverse transform all
        if feature_types is None:
            feature_types = list(self.scalers.keys())
        
        for feature_type in feature_types:
            if feature_type in self.scalers:
                scaler = self.scalers[feature_type]['scaler']
                columns = self.scalers[feature_type]['columns']
                
                available_columns = [col for col in columns if col in df.columns]
                if available_columns:
                    df[available_columns] = scaler.inverse_transform(df[available_columns])
        
        return df
    
    def prepare_ml_datasets(self, data: pd.DataFrame, 
                           target_columns: List[str],
                           test_size: float = 0.2,
                           validation_size: float = 0.1,
                           time_split: bool = True) -> Dict[str, Any]:
        """
        Prepare train, validation, and test datasets for ML.
        
        Args:
            data: Full dataset
            target_columns: List of target column names
            test_size: Proportion of test data
            validation_size: Proportion of validation data
            time_split: Whether to use time-based splitting
            
        Returns:
            Dictionary with train, validation, test datasets
        """
        # Remove rows with NaN in target columns
        clean_data = data.dropna(subset=target_columns)
        
        # Separate features and targets
        feature_columns = [col for col in clean_data.columns if col not in target_columns]
        X = clean_data[feature_columns]
        y = clean_data[target_columns]
        
        if time_split:
            # Time-based split for time series data
            n_samples = len(clean_data)
            
            # Calculate split indices
            train_end = int(n_samples * (1 - test_size - validation_size))
            val_end = int(n_samples * (1 - test_size))
            
            # Split data
            X_train = X.iloc[:train_end]
            X_val = X.iloc[train_end:val_end]
            X_test = X.iloc[val_end:]
            
            y_train = y.iloc[:train_end]
            y_val = y.iloc[train_end:val_end]
            y_test = y.iloc[val_end:]
            
        else:
            # Random split
            X_temp, X_test, y_temp, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Further split into train and validation
            val_size_adjusted = validation_size / (1 - test_size)
            X_train, X_val, y_train, y_val = train_test_split(
                X_temp, y_temp, test_size=val_size_adjusted, random_state=42
            )
        
        # Fit scalers on training data only
        feature_types = self.identify_feature_types(X_train)
        self.fit_scalers(X_train, feature_types)
        
        # Transform all datasets
        X_train_scaled = self.transform_data(X_train)
        X_val_scaled = self.transform_data(X_val)
        X_test_scaled = self.transform_data(X_test)
        
        return {
            'X_train': X_train_scaled,
            'X_val': X_val_scaled,
            'X_test': X_test_scaled,
            'y_train': y_train,
            'y_val': y_val,
            'y_test': y_test,
            'feature_columns': feature_columns,
            'target_columns': target_columns,
            'train_indices': X_train.index,
            'val_indices': X_val.index,
            'test_indices': X_test.index
        }
    
    def handle_missing_values(self, data: pd.DataFrame, 
                            strategy: str = 'forward_fill') -> pd.DataFrame:
        """
        Handle missing values in the data.
        
        Args:
            data: Input data
            strategy: Strategy for handling missing values
            
        Returns:
            Data with missing values handled
        """
        df = data.copy()
        
        if strategy == 'forward_fill':
            df = df.fillna(method='ffill').fillna(method='bfill')
        elif strategy == 'interpolate':
            df = df.interpolate(method='linear').fillna(method='bfill')
        elif strategy == 'zero':
            df = df.fillna(0)
        elif strategy == 'mean':
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].mean())
        elif strategy == 'median':
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())
        
        return df
    
    def save_scalers(self, filepath: str) -> None:
        """
        Save fitted scalers to file.
        
        Args:
            filepath: Path to save scalers
        """
        with open(filepath, 'wb') as f:
            pickle.dump({
                'scalers': self.scalers,
                'scaling_method': self.scaling_method
            }, f)
    
    def load_scalers(self, filepath: str) -> None:
        """
        Load scalers from file.
        
        Args:
            filepath: Path to load scalers from
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.scalers = data['scalers']
            self.scaling_method = data['scaling_method']
    
    def get_scaling_summary(self) -> Dict:
        """
        Get summary of scaling applied to features.
        
        Returns:
            Dictionary with scaling summary
        """
        summary = {
            'scaling_method': self.scaling_method,
            'feature_types_scaled': list(self.scalers.keys()),
            'total_features_scaled': sum(len(info['columns']) for info in self.scalers.values())
        }
        
        for feature_type, scaler_info in self.scalers.items():
            summary[f'{feature_type}_count'] = len(scaler_info['columns'])
        
        return summary


if __name__ == "__main__":
    # Example usage
    print("Crypto Data Scaler")
    print("This module handles scaling and normalization of crypto features")
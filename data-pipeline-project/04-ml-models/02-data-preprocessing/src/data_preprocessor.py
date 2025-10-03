# Data Preprocessing for Machine Learning Pipeline
# Purpose: Prepare data from the silver layer for machine learning models
# 
# This module handles:
# - Feature engineering and selection
# - Data scaling and normalization  
# - Handling missing values and outliers
# - Creating train/validation/test splits
# - Generating ML-ready datasets

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Optional, Any
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from scipy import stats
import joblib
import logging
import warnings
warnings.filterwarnings('ignore')

class DataPreprocessor:
    """
    Main class for data preprocessing operations in the ML pipeline.
    
    This class provides comprehensive preprocessing capabilities including:
    - Data cleaning and validation
    - Feature engineering and transformation
    - Missing value imputation
    - Outlier detection and handling
    - Feature scaling and encoding
    - Data splitting for ML workflows
    
    Example usage:
        preprocessor = DataPreprocessor()
        X_train, X_test, y_train, y_test = preprocessor.prepare_ml_dataset(
            data=customer_data,
            target_column='churn_flag',
            test_size=0.2
        )
    """
    
    def __init__(self, random_state: int = 42):
        """
        Initialize the DataPreprocessor.
        
        Args:
            random_state: Random seed for reproducible results
        """
        self.random_state = random_state
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
        self.feature_names = []
        self.target_name = None
        self.preprocessing_steps = []
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
    def load_silver_data(self, table_name: str, connection_params: Dict) -> pd.DataFrame:
        """
        Load data from silver layer tables for ML processing.
        
        Args:
            table_name: Name of the silver layer table
            connection_params: Database connection parameters
            
        Returns:
            DataFrame with silver layer data
        """
        # TODO: Implement database connection logic
        # This would connect to your data warehouse and pull silver layer data
        
        # For now, return sample data structure
        # In production, replace with actual database query
        self.logger.info(f"Loading data from silver layer table: {table_name}")
        
        # Example query structure:
        # query = f"SELECT * FROM {table_name} WHERE is_current = TRUE"
        # return pd.read_sql(query, connection)
        
        # Sample data for demonstration
        return pd.DataFrame()
    
    def detect_data_types(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Automatically detect and categorize column data types.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary categorizing columns by type
        """
        column_types = {
            'numeric': [],
            'categorical': [],
            'datetime': [],
            'text': [],
            'binary': []
        }
        
        for col in df.columns:
            # Check for datetime columns
            if df[col].dtype in ['datetime64[ns]', 'datetime64[ns, UTC]']:
                column_types['datetime'].append(col)
            
            # Check for numeric columns
            elif df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                # Check if it's actually categorical (few unique values)
                if df[col].nunique() <= 10 and df[col].nunique() < len(df) * 0.05:
                    column_types['categorical'].append(col)
                # Check if it's binary (only 0s and 1s)
                elif set(df[col].dropna().unique()).issubset({0, 1}):
                    column_types['binary'].append(col)
                else:
                    column_types['numeric'].append(col)
            
            # Check for text columns
            elif df[col].dtype == 'object':
                # Check if it's actually categorical (reasonable number of unique values)
                if df[col].nunique() <= 50:
                    column_types['categorical'].append(col)
                else:
                    column_types['text'].append(col)
        
        self.logger.info(f"Detected column types: {column_types}")
        return column_types
    
    def handle_missing_values(self, df: pd.DataFrame, strategy: Dict[str, str] = None) -> pd.DataFrame:
        """
        Handle missing values using various imputation strategies.
        
        Args:
            df: Input DataFrame
            strategy: Dictionary mapping column types to imputation strategies
                     Options: 'drop', 'mean', 'median', 'mode', 'knn', 'forward_fill'
        
        Returns:
            DataFrame with missing values handled
        """
        if strategy is None:
            strategy = {
                'numeric': 'median',
                'categorical': 'mode',
                'datetime': 'forward_fill',
                'binary': 'mode'
            }
        
        df_processed = df.copy()
        column_types = self.detect_data_types(df)
        
        for col_type, columns in column_types.items():
            if not columns or col_type not in strategy:
                continue
                
            impute_strategy = strategy[col_type]
            
            for col in columns:
                missing_pct = (df_processed[col].isnull().sum() / len(df_processed)) * 100
                
                if missing_pct == 0:
                    continue
                    
                self.logger.info(f"Handling {missing_pct:.1f}% missing values in {col} using {impute_strategy}")
                
                if impute_strategy == 'drop':
                    df_processed = df_processed.dropna(subset=[col])
                
                elif impute_strategy == 'mean' and col_type == 'numeric':
                    imputer = SimpleImputer(strategy='mean')
                    df_processed[col] = imputer.fit_transform(df_processed[[col]]).ravel()
                    self.imputers[col] = imputer
                
                elif impute_strategy == 'median' and col_type == 'numeric':
                    imputer = SimpleImputer(strategy='median')
                    df_processed[col] = imputer.fit_transform(df_processed[[col]]).ravel()
                    self.imputers[col] = imputer
                
                elif impute_strategy == 'mode':
                    imputer = SimpleImputer(strategy='most_frequent')
                    df_processed[col] = imputer.fit_transform(df_processed[[col]]).ravel()
                    self.imputers[col] = imputer
                
                elif impute_strategy == 'knn':
                    imputer = KNNImputer(n_neighbors=5)
                    df_processed[col] = imputer.fit_transform(df_processed[[col]]).ravel()
                    self.imputers[col] = imputer
                
                elif impute_strategy == 'forward_fill':
                    df_processed[col] = df_processed[col].fillna(method='ffill')
        
        return df_processed
    
    def detect_outliers(self, df: pd.DataFrame, method: str = 'iqr', threshold: float = 1.5) -> Dict[str, np.ndarray]:
        """
        Detect outliers in numeric columns.
        
        Args:
            df: Input DataFrame
            method: Method for outlier detection ('iqr', 'zscore', 'isolation_forest')
            threshold: Threshold for outlier detection
            
        Returns:
            Dictionary mapping column names to boolean arrays indicating outliers
        """
        column_types = self.detect_data_types(df)
        numeric_columns = column_types['numeric']
        outliers = {}
        
        for col in numeric_columns:
            if method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                outliers[col] = (df[col] < lower_bound) | (df[col] > upper_bound)
                
            elif method == 'zscore':
                z_scores = np.abs(stats.zscore(df[col].dropna()))
                outliers[col] = z_scores > threshold
                
            outlier_count = outliers[col].sum()
            outlier_pct = (outlier_count / len(df)) * 100
            self.logger.info(f"Detected {outlier_count} outliers ({outlier_pct:.1f}%) in {col}")
        
        return outliers
    
    def handle_outliers(self, df: pd.DataFrame, outliers: Dict[str, np.ndarray], method: str = 'cap') -> pd.DataFrame:
        """
        Handle outliers using various strategies.
        
        Args:
            df: Input DataFrame
            outliers: Dictionary of outlier indicators from detect_outliers()
            method: Method for handling outliers ('cap', 'remove', 'transform')
            
        Returns:
            DataFrame with outliers handled
        """
        df_processed = df.copy()
        
        for col, outlier_mask in outliers.items():
            if method == 'cap':
                # Cap outliers at 5th and 95th percentiles
                lower_cap = df[col].quantile(0.05)
                upper_cap = df[col].quantile(0.95)
                df_processed[col] = np.clip(df_processed[col], lower_cap, upper_cap)
                
            elif method == 'remove':
                # Remove rows with outliers
                df_processed = df_processed[~outlier_mask]
                
            elif method == 'transform':
                # Apply log transformation to reduce outlier impact
                if (df_processed[col] > 0).all():
                    df_processed[col] = np.log1p(df_processed[col])
        
        return df_processed
    
    def engineer_features(self, df: pd.DataFrame, target_column: str = None) -> pd.DataFrame:
        """
        Create engineered features from existing data.
        
        Args:
            df: Input DataFrame
            target_column: Name of target column (excluded from feature engineering)
            
        Returns:
            DataFrame with engineered features
        """
        df_engineered = df.copy()
        column_types = self.detect_data_types(df)
        
        # Date/time feature engineering
        for col in column_types['datetime']:
            if col != target_column:
                df_engineered[f'{col}_year'] = df_engineered[col].dt.year
                df_engineered[f'{col}_month'] = df_engineered[col].dt.month
                df_engineered[f'{col}_day'] = df_engineered[col].dt.day
                df_engineered[f'{col}_dayofweek'] = df_engineered[col].dt.dayofweek
                df_engineered[f'{col}_is_weekend'] = df_engineered[col].dt.dayofweek.isin([5, 6])
                
                # Time since features (if current date is meaningful)
                df_engineered[f'days_since_{col}'] = (pd.Timestamp.now() - df_engineered[col]).dt.days
        
        # Numeric feature engineering
        numeric_cols = [col for col in column_types['numeric'] if col != target_column]
        
        # Create interaction features for important numeric columns (limit to avoid explosion)
        if len(numeric_cols) >= 2:
            important_cols = numeric_cols[:5]  # Limit to first 5 numeric columns
            for i, col1 in enumerate(important_cols):
                for col2 in important_cols[i+1:]:
                    # Ratio features
                    if (df_engineered[col2] != 0).all():
                        df_engineered[f'{col1}_{col2}_ratio'] = df_engineered[col1] / df_engineered[col2]
                    
                    # Product features
                    df_engineered[f'{col1}_{col2}_product'] = df_engineered[col1] * df_engineered[col2]
        
        # Binning continuous variables
        for col in numeric_cols[:3]:  # Limit to avoid too many features
            df_engineered[f'{col}_binned'] = pd.qcut(df_engineered[col], q=5, labels=['low', 'low_med', 'med', 'med_high', 'high'], duplicates='drop')
        
        # Categorical feature engineering
        for col in column_types['categorical']:
            if col != target_column:
                # Frequency encoding
                freq_encoding = df_engineered[col].value_counts().to_dict()
                df_engineered[f'{col}_frequency'] = df_engineered[col].map(freq_encoding)
                
                # Target encoding (if target is provided and categorical/binary)
                if target_column and target_column in df.columns:
                    target_mean = df_engineered.groupby(col)[target_column].mean()
                    df_engineered[f'{col}_target_encoded'] = df_engineered[col].map(target_mean)
        
        self.logger.info(f"Feature engineering completed. Original features: {df.shape[1]}, New features: {df_engineered.shape[1]}")
        return df_engineered
    
    def encode_categorical_features(self, df: pd.DataFrame, method: str = 'onehot', max_categories: int = 20) -> pd.DataFrame:
        """
        Encode categorical features for machine learning.
        
        Args:
            df: Input DataFrame
            method: Encoding method ('onehot', 'label', 'target')
            max_categories: Maximum number of categories for one-hot encoding
            
        Returns:
            DataFrame with encoded categorical features
        """
        df_encoded = df.copy()
        column_types = self.detect_data_types(df)
        categorical_columns = column_types['categorical']
        
        for col in categorical_columns:
            unique_count = df_encoded[col].nunique()
            
            if method == 'onehot' and unique_count <= max_categories:
                # One-hot encoding for low cardinality categories
                encoder = OneHotEncoder(drop='first', sparse=False)
                encoded_features = encoder.fit_transform(df_encoded[[col]])
                
                # Create column names for encoded features
                feature_names = [f'{col}_{category}' for category in encoder.categories_[0][1:]]
                encoded_df = pd.DataFrame(encoded_features, columns=feature_names, index=df_encoded.index)
                
                # Add encoded features and remove original
                df_encoded = pd.concat([df_encoded, encoded_df], axis=1)
                df_encoded = df_encoded.drop(columns=[col])
                self.encoders[col] = encoder
                
            elif method == 'label':
                # Label encoding for high cardinality categories
                encoder = LabelEncoder()
                df_encoded[col] = encoder.fit_transform(df_encoded[col].astype(str))
                self.encoders[col] = encoder
            
            elif unique_count > max_categories:
                # For high cardinality, use frequency encoding
                freq_encoding = df_encoded[col].value_counts().to_dict()
                df_encoded[col] = df_encoded[col].map(freq_encoding)
        
        return df_encoded
    
    def scale_features(self, df: pd.DataFrame, method: str = 'standard', exclude_columns: List[str] = None) -> pd.DataFrame:
        """
        Scale numeric features for machine learning.
        
        Args:
            df: Input DataFrame
            method: Scaling method ('standard', 'minmax', 'robust')
            exclude_columns: Columns to exclude from scaling
            
        Returns:
            DataFrame with scaled features
        """
        if exclude_columns is None:
            exclude_columns = []
            
        df_scaled = df.copy()
        column_types = self.detect_data_types(df)
        numeric_columns = [col for col in column_types['numeric'] if col not in exclude_columns]
        
        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler()
        elif method == 'robust':
            scaler = RobustScaler()
        else:
            raise ValueError(f"Unknown scaling method: {method}")
        
        if numeric_columns:
            df_scaled[numeric_columns] = scaler.fit_transform(df_scaled[numeric_columns])
            self.scalers['numeric'] = scaler
            self.logger.info(f"Scaled {len(numeric_columns)} numeric features using {method} scaling")
        
        return df_scaled
    
    def select_features(self, X: pd.DataFrame, y: pd.Series, method: str = 'mutual_info', k: int = 20) -> pd.DataFrame:
        """
        Select the most important features for modeling.
        
        Args:
            X: Feature DataFrame
            y: Target Series
            method: Feature selection method ('mutual_info', 'f_test', 'correlation')
            k: Number of features to select
            
        Returns:
            DataFrame with selected features
        """
        if method == 'mutual_info':
            # Use mutual information for feature selection
            if y.dtype in ['object', 'category'] or y.nunique() <= 10:
                # Classification
                selector = SelectKBest(score_func=mutual_info_classif, k=k)
            else:
                # Regression
                from sklearn.feature_selection import mutual_info_regression
                selector = SelectKBest(score_func=mutual_info_regression, k=k)
                
        elif method == 'f_test':
            selector = SelectKBest(score_func=f_classif, k=k)
        
        elif method == 'correlation':
            # Simple correlation-based selection
            correlations = X.corrwith(y).abs().sort_values(ascending=False)
            selected_features = correlations.head(k).index.tolist()
            return X[selected_features]
        
        X_selected = selector.fit_transform(X, y)
        selected_features = X.columns[selector.get_support()].tolist()
        
        self.logger.info(f"Selected {len(selected_features)} features using {method}")
        return pd.DataFrame(X_selected, columns=selected_features, index=X.index)
    
    def prepare_ml_dataset(self, 
                          data: pd.DataFrame, 
                          target_column: str,
                          test_size: float = 0.2,
                          validation_size: float = 0.1,
                          preprocessing_config: Dict = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """
        Complete preprocessing pipeline to prepare ML-ready dataset.
        
        Args:
            data: Raw input data
            target_column: Name of target variable column
            test_size: Proportion of data for test set
            validation_size: Proportion of data for validation set
            preprocessing_config: Configuration for preprocessing steps
            
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        if preprocessing_config is None:
            preprocessing_config = {
                'handle_missing': True,
                'handle_outliers': True,
                'engineer_features': True,
                'encode_categorical': True,
                'scale_features': True,
                'select_features': False,
                'feature_selection_k': 20
            }
        
        self.logger.info("Starting ML dataset preparation pipeline")
        df = data.copy()
        
        # Store target and features
        y = df[target_column]
        X = df.drop(columns=[target_column])
        self.target_name = target_column
        
        # Step 1: Handle missing values
        if preprocessing_config.get('handle_missing', True):
            X = self.handle_missing_values(X)
            self.preprocessing_steps.append('missing_values_handled')
        
        # Step 2: Handle outliers
        if preprocessing_config.get('handle_outliers', True):
            outliers = self.detect_outliers(X)
            X = self.handle_outliers(X, outliers, method='cap')
            self.preprocessing_steps.append('outliers_handled')
        
        # Step 3: Feature engineering
        if preprocessing_config.get('engineer_features', True):
            X = self.engineer_features(X, target_column)
            self.preprocessing_steps.append('features_engineered')
        
        # Step 4: Encode categorical features
        if preprocessing_config.get('encode_categorical', True):
            X = self.encode_categorical_features(X)
            self.preprocessing_steps.append('categorical_encoded')
        
        # Step 5: Scale features
        if preprocessing_config.get('scale_features', True):
            X = self.scale_features(X)
            self.preprocessing_steps.append('features_scaled')
        
        # Step 6: Feature selection (optional)
        if preprocessing_config.get('select_features', False):
            k = preprocessing_config.get('feature_selection_k', 20)
            X = self.select_features(X, y, k=k)
            self.preprocessing_steps.append('features_selected')
        
        # Store final feature names
        self.feature_names = X.columns.tolist()
        
        # Split data into train/validation/test sets
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state, stratify=y if y.nunique() <= 10 else None
        )
        
        val_size_adjusted = validation_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_size_adjusted, random_state=self.random_state, stratify=y_temp if y_temp.nunique() <= 10 else None
        )
        
        self.logger.info(f"""
        Dataset preparation completed:
        - Total samples: {len(data)}
        - Features: {len(self.feature_names)}
        - Train set: {len(X_train)} samples
        - Validation set: {len(X_val)} samples  
        - Test set: {len(X_test)} samples
        - Preprocessing steps: {', '.join(self.preprocessing_steps)}
        """)
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def save_preprocessor(self, filepath: str):
        """
        Save the fitted preprocessor for later use.
        
        Args:
            filepath: Path to save the preprocessor
        """
        preprocessor_data = {
            'scalers': self.scalers,
            'encoders': self.encoders,
            'imputers': self.imputers,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'preprocessing_steps': self.preprocessing_steps,
            'random_state': self.random_state
        }
        
        joblib.dump(preprocessor_data, filepath)
        self.logger.info(f"Preprocessor saved to {filepath}")
    
    def load_preprocessor(self, filepath: str):
        """
        Load a previously saved preprocessor.
        
        Args:
            filepath: Path to the saved preprocessor
        """
        preprocessor_data = joblib.load(filepath)
        
        self.scalers = preprocessor_data['scalers']
        self.encoders = preprocessor_data['encoders']
        self.imputers = preprocessor_data['imputers']
        self.feature_names = preprocessor_data['feature_names']
        self.target_name = preprocessor_data['target_name']
        self.preprocessing_steps = preprocessor_data['preprocessing_steps']
        self.random_state = preprocessor_data['random_state']
        
        self.logger.info(f"Preprocessor loaded from {filepath}")
    
    def transform_new_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform new data using fitted preprocessors.
        
        Args:
            df: New data to transform
            
        Returns:
            Transformed DataFrame
        """
        df_transformed = df.copy()
        
        # Apply same preprocessing steps as training data
        if 'missing_values_handled' in self.preprocessing_steps:
            # Apply fitted imputers
            for col, imputer in self.imputers.items():
                if col in df_transformed.columns:
                    df_transformed[col] = imputer.transform(df_transformed[[col]]).ravel()
        
        if 'features_engineered' in self.preprocessing_steps:
            df_transformed = self.engineer_features(df_transformed)
        
        if 'categorical_encoded' in self.preprocessing_steps:
            # Apply fitted encoders
            for col, encoder in self.encoders.items():
                if col in df_transformed.columns:
                    if hasattr(encoder, 'transform'):
                        df_transformed[col] = encoder.transform(df_transformed[col])
        
        if 'features_scaled' in self.preprocessing_steps:
            # Apply fitted scalers
            numeric_scaler = self.scalers.get('numeric')
            if numeric_scaler:
                numeric_columns = [col for col in df_transformed.columns if col in self.feature_names]
                if numeric_columns:
                    df_transformed[numeric_columns] = numeric_scaler.transform(df_transformed[numeric_columns])
        
        # Ensure same columns as training data
        missing_cols = set(self.feature_names) - set(df_transformed.columns)
        for col in missing_cols:
            df_transformed[col] = 0  # Add missing columns with default value
        
        # Remove extra columns and reorder
        df_transformed = df_transformed[self.feature_names]
        
        return df_transformed


# =============================================================================
# HELPER FUNCTIONS AND UTILITIES
# =============================================================================

def create_data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a comprehensive data quality report.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with data quality metrics
    """
    report = []
    
    for col in df.columns:
        missing_count = df[col].isnull().sum()
        missing_pct = (missing_count / len(df)) * 100
        unique_count = df[col].nunique()
        unique_pct = (unique_count / len(df)) * 100
        
        quality_score = 1.0
        if missing_pct > 0:
            quality_score -= missing_pct / 100 * 0.5  # Penalize missing values
        
        if df[col].dtype in ['int64', 'float64']:
            # Numeric column stats
            mean_val = df[col].mean()
            std_val = df[col].std()
            min_val = df[col].min()
            max_val = df[col].max()
            
            # Check for outliers using IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
            outlier_pct = (outliers / len(df)) * 100
            
            if outlier_pct > 5:
                quality_score -= 0.1  # Penalize high outlier percentage
        else:
            mean_val = std_val = min_val = max_val = outliers = outlier_pct = None
        
        report.append({
            'column': col,
            'dtype': str(df[col].dtype),
            'missing_count': missing_count,
            'missing_pct': missing_pct,
            'unique_count': unique_count,
            'unique_pct': unique_pct,
            'mean': mean_val,
            'std': std_val,
            'min': min_val,
            'max': max_val,
            'outliers': outliers,
            'outlier_pct': outlier_pct,
            'quality_score': quality_score
        })
    
    return pd.DataFrame(report)


def validate_data_splits(X_train: pd.DataFrame, X_val: pd.DataFrame, X_test: pd.DataFrame,
                        y_train: pd.Series, y_val: pd.Series, y_test: pd.Series) -> Dict:
    """
    Validate that data splits are properly balanced and representative.
    
    Args:
        X_train, X_val, X_test: Feature DataFrames
        y_train, y_val, y_test: Target Series
        
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'split_sizes': {
            'train': len(X_train),
            'validation': len(X_val),
            'test': len(X_test)
        },
        'feature_consistency': {
            'train_features': set(X_train.columns),
            'val_features': set(X_val.columns),
            'test_features': set(X_test.columns)
        },
        'target_distribution': {}
    }
    
    # Check feature consistency
    all_features_match = (
        validation_results['feature_consistency']['train_features'] == 
        validation_results['feature_consistency']['val_features'] == 
        validation_results['feature_consistency']['test_features']
    )
    validation_results['features_consistent'] = all_features_match
    
    # Check target distribution for classification tasks
    if y_train.nunique() <= 10:  # Likely classification
        validation_results['target_distribution'] = {
            'train': y_train.value_counts(normalize=True).to_dict(),
            'validation': y_val.value_counts(normalize=True).to_dict(),
            'test': y_test.value_counts(normalize=True).to_dict()
        }
    
    return validation_results


# =============================================================================
# EXAMPLE USAGE AND TESTING
# =============================================================================

if __name__ == "__main__":
    """
    Example usage of the DataPreprocessor class.
    This section demonstrates how to use the preprocessor in practice.
    """
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Example: Create sample customer churn data
    np.random.seed(42)
    n_samples = 1000
    
    sample_data = pd.DataFrame({
        'customer_id': range(1, n_samples + 1),
        'age': np.random.normal(45, 12, n_samples),
        'income': np.random.lognormal(10, 1, n_samples),
        'tenure_months': np.random.randint(1, 60, n_samples),
        'monthly_charges': np.random.normal(65, 20, n_samples),
        'total_charges': np.random.normal(2000, 1000, n_samples),
        'gender': np.random.choice(['M', 'F'], n_samples),
        'contract_type': np.random.choice(['Month-to-month', 'One year', 'Two year'], n_samples),
        'payment_method': np.random.choice(['Credit card', 'Bank transfer', 'Electronic check'], n_samples),
        'internet_service': np.random.choice(['DSL', 'Fiber optic', 'No'], n_samples),
        'churn_flag': np.random.choice([0, 1], n_samples, p=[0.7, 0.3])  # Target variable
    })
    
    # Add some missing values for demonstration
    sample_data.loc[np.random.choice(sample_data.index, 50, replace=False), 'age'] = np.nan
    sample_data.loc[np.random.choice(sample_data.index, 30, replace=False), 'income'] = np.nan
    
    print("Sample data shape:", sample_data.shape)
    print("\nSample data info:")
    print(sample_data.info())
    
    # Initialize preprocessor
    preprocessor = DataPreprocessor(random_state=42)
    
    # Generate data quality report
    quality_report = create_data_quality_report(sample_data.drop(['customer_id', 'churn_flag'], axis=1))
    print("\nData Quality Report:")
    print(quality_report[['column', 'missing_pct', 'unique_count', 'quality_score']].round(2))
    
    # Prepare ML dataset
    X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.prepare_ml_dataset(
        data=sample_data.drop('customer_id', axis=1),  # Remove ID column
        target_column='churn_flag',
        test_size=0.2,
        validation_size=0.1
    )
    
    # Validate data splits
    validation_results = validate_data_splits(X_train, X_val, X_test, y_train, y_val, y_test)
    print(f"\nData split validation:")
    print(f"Features consistent: {validation_results['features_consistent']}")
    print(f"Split sizes: {validation_results['split_sizes']}")
    
    # Save preprocessor for later use
    preprocessor.save_preprocessor('preprocessor_model.pkl')
    
    print(f"\nPreprocessing completed successfully!")
    print(f"Training set shape: {X_train.shape}")
    print(f"Validation set shape: {X_val.shape}")
    print(f"Test set shape: {X_test.shape}")
    print(f"Features: {len(preprocessor.feature_names)}")
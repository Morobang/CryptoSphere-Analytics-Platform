"""
Feature Engineering for Cryptocurrency ML Models

This module creates comprehensive features for cryptocurrency price prediction models,
including technical indicators, market signals, and time-based features.
"""

import pandas as pd
import numpy as np
import talib as ta
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class CryptoFeatureEngineer:
    """
    Comprehensive feature engineering for cryptocurrency data.
    """
    
    def __init__(self):
        """Initialize the feature engineer."""
        self.feature_columns = []
        self.scalers = {}
    
    def create_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create technical indicators for cryptocurrency data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with technical indicators added
        """
        df = data.copy()
        
        # Price-based indicators
        df['sma_7'] = ta.SMA(df['close'], timeperiod=7)
        df['sma_14'] = ta.SMA(df['close'], timeperiod=14)
        df['sma_30'] = ta.SMA(df['close'], timeperiod=30)
        df['sma_90'] = ta.SMA(df['close'], timeperiod=90)
        
        df['ema_7'] = ta.EMA(df['close'], timeperiod=7)
        df['ema_14'] = ta.EMA(df['close'], timeperiod=14)
        df['ema_30'] = ta.EMA(df['close'], timeperiod=30)
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = ta.BBANDS(
            df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # RSI
        df['rsi_14'] = ta.RSI(df['close'], timeperiod=14)
        df['rsi_30'] = ta.RSI(df['close'], timeperiod=30)
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = ta.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        # Stochastic
        df['stoch_k'], df['stoch_d'] = ta.STOCH(
            df['high'], df['low'], df['close'], 
            fastk_period=14, slowk_period=3, slowd_period=3
        )
        
        # Williams %R
        df['williams_r'] = ta.WILLR(df['high'], df['low'], df['close'], timeperiod=14)
        
        # Average True Range
        df['atr_14'] = ta.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        
        # Commodity Channel Index
        df['cci_14'] = ta.CCI(df['high'], df['low'], df['close'], timeperiod=14)
        
        # Money Flow Index
        df['mfi_14'] = ta.MFI(df['high'], df['low'], df['close'], df['volume'], timeperiod=14)
        
        return df
    
    def create_price_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create price-based features.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            DataFrame with price features added
        """
        df = data.copy()
        
        # Price changes
        df['price_change_1d'] = df['close'].pct_change(1)
        df['price_change_3d'] = df['close'].pct_change(3)
        df['price_change_7d'] = df['close'].pct_change(7)
        df['price_change_14d'] = df['close'].pct_change(14)
        df['price_change_30d'] = df['close'].pct_change(30)
        
        # Log returns
        df['log_return_1d'] = np.log(df['close'] / df['close'].shift(1))
        df['log_return_3d'] = np.log(df['close'] / df['close'].shift(3))
        df['log_return_7d'] = np.log(df['close'] / df['close'].shift(7))
        
        # Volatility features
        df['volatility_7d'] = df['price_change_1d'].rolling(window=7).std()
        df['volatility_14d'] = df['price_change_1d'].rolling(window=14).std()
        df['volatility_30d'] = df['price_change_1d'].rolling(window=30).std()
        
        # Price position relative to historical ranges
        df['price_position_7d'] = (df['close'] - df['close'].rolling(7).min()) / (
            df['close'].rolling(7).max() - df['close'].rolling(7).min()
        )
        df['price_position_30d'] = (df['close'] - df['close'].rolling(30).min()) / (
            df['close'].rolling(30).max() - df['close'].rolling(30).min()
        )
        
        # High-Low spread
        df['hl_spread'] = (df['high'] - df['low']) / df['close']
        df['hl_spread_ma_7'] = df['hl_spread'].rolling(window=7).mean()
        
        # Open-Close relationship
        df['open_close_ratio'] = df['open'] / df['close']
        df['body_size'] = abs(df['close'] - df['open']) / df['close']
        
        return df
    
    def create_volume_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create volume-based features.
        
        Args:
            data: DataFrame with volume data
            
        Returns:
            DataFrame with volume features added
        """
        df = data.copy()
        
        # Volume moving averages
        df['volume_ma_7'] = df['volume'].rolling(window=7).mean()
        df['volume_ma_14'] = df['volume'].rolling(window=14).mean()
        df['volume_ma_30'] = df['volume'].rolling(window=30).mean()
        
        # Volume ratios
        df['volume_ratio_7d'] = df['volume'] / df['volume_ma_7']
        df['volume_ratio_14d'] = df['volume'] / df['volume_ma_14']
        df['volume_ratio_30d'] = df['volume'] / df['volume_ma_30']
        
        # Volume changes
        df['volume_change_1d'] = df['volume'].pct_change(1)
        df['volume_change_7d'] = df['volume'].pct_change(7)
        
        # Volume-price relationship
        df['vp_ratio'] = df['volume'] * df['close']
        df['vp_ratio_ma_7'] = df['vp_ratio'].rolling(window=7).mean()
        
        # On-Balance Volume
        df['obv'] = ta.OBV(df['close'], df['volume'])
        df['obv_ma_7'] = df['obv'].rolling(window=7).mean()
        
        # Volume Profile
        df['volume_profile'] = df['volume'] / df['volume'].rolling(window=30).max()
        
        return df
    
    def create_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create time-based features.
        
        Args:
            data: DataFrame with datetime index
            
        Returns:
            DataFrame with time features added
        """
        df = data.copy()
        
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
        
        # Time components
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        df['year'] = df.index.year
        
        # Cyclical encoding for time features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Business day indicator
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Days since significant events (you can customize these)
        df['days_since_year_start'] = (df.index - pd.to_datetime(df.index.year, format='%Y')).days
        
        return df
    
    def create_market_features(self, data: pd.DataFrame, market_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Create market-wide features if market data is available.
        
        Args:
            data: Individual cryptocurrency data
            market_data: Market-wide data (optional)
            
        Returns:
            DataFrame with market features added
        """
        df = data.copy()
        
        if market_data is not None:
            # Market correlation features
            df['market_correlation'] = df['price_change_1d'].rolling(window=30).corr(
                market_data['total_market_cap'].pct_change()
            )
            
            # Market dominance
            if 'market_cap' in df.columns and 'total_market_cap' in market_data.columns:
                df['market_dominance'] = df['market_cap'] / market_data['total_market_cap']
                df['dominance_change'] = df['market_dominance'].pct_change()
        
        # Relative strength compared to market average
        # This would require market-wide price data
        
        return df
    
    def create_lag_features(self, data: pd.DataFrame, target_col: str = 'close', 
                           lags: List[int] = [1, 2, 3, 7, 14]) -> pd.DataFrame:
        """
        Create lagged features for time series prediction.
        
        Args:
            data: DataFrame with time series data
            target_col: Column to create lags for
            lags: List of lag periods
            
        Returns:
            DataFrame with lag features added
        """
        df = data.copy()
        
        for lag in lags:
            df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
            df[f'{target_col}_pct_change_lag_{lag}'] = df[target_col].pct_change().shift(lag)
        
        # Rolling statistics of lagged features
        for window in [7, 14, 30]:
            df[f'{target_col}_rolling_mean_{window}'] = df[target_col].rolling(window=window).mean()
            df[f'{target_col}_rolling_std_{window}'] = df[target_col].rolling(window=window).std()
            df[f'{target_col}_rolling_min_{window}'] = df[target_col].rolling(window=window).min()
            df[f'{target_col}_rolling_max_{window}'] = df[target_col].rolling(window=window).max()
        
        return df
    
    def create_target_variables(self, data: pd.DataFrame, 
                              prediction_horizons: List[int] = [1, 3, 7]) -> pd.DataFrame:
        """
        Create target variables for prediction.
        
        Args:
            data: DataFrame with price data
            prediction_horizons: List of prediction horizons in days
            
        Returns:
            DataFrame with target variables added
        """
        df = data.copy()
        
        for horizon in prediction_horizons:
            # Future price
            df[f'target_price_{horizon}d'] = df['close'].shift(-horizon)
            
            # Future return
            df[f'target_return_{horizon}d'] = df['close'].pct_change(horizon).shift(-horizon)
            
            # Direction (up/down)
            df[f'target_direction_{horizon}d'] = (df[f'target_return_{horizon}d'] > 0).astype(int)
            
            # Volatility target
            df[f'target_volatility_{horizon}d'] = df['close'].pct_change().rolling(window=horizon).std().shift(-horizon)
        
        return df
    
    def process_features(self, data: pd.DataFrame, crypto_symbol: str = None) -> pd.DataFrame:
        """
        Apply all feature engineering steps.
        
        Args:
            data: Raw cryptocurrency data
            crypto_symbol: Symbol for identification
            
        Returns:
            DataFrame with all features created
        """
        print(f"Processing features for {crypto_symbol}...")
        
        # Apply all feature engineering steps
        df = self.create_technical_indicators(data)
        df = self.create_price_features(df)
        df = self.create_volume_features(df)
        df = self.create_time_features(df)
        df = self.create_lag_features(df)
        df = self.create_target_variables(df)
        
        # Add symbol identifier
        if crypto_symbol:
            df['symbol'] = crypto_symbol
        
        # Store feature column names
        self.feature_columns = [col for col in df.columns if not col.startswith('target_')]
        
        print(f"Created {len(self.feature_columns)} features")
        return df
    
    def get_feature_importance_names(self) -> List[str]:
        """
        Get list of feature names for importance analysis.
        
        Returns:
            List of feature column names
        """
        return self.feature_columns


if __name__ == "__main__":
    # Example usage
    print("Crypto Feature Engineer")
    print("This module creates comprehensive features for ML models")
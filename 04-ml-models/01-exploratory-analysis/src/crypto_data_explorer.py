"""
Cryptocurrency Data Explorer

This module provides comprehensive analysis of cryptocurrency market data
to understand patterns, trends, and relationships that inform ML model development.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class CryptoDataExplorer:
    """
    Comprehensive cryptocurrency data exploration and analysis.
    """
    
    def __init__(self, data: pd.DataFrame = None):
        """
        Initialize the crypto data explorer.
        
        Args:
            data: DataFrame with cryptocurrency data
        """
        self.data = data
        self.cryptocurrencies = []
        if data is not None:
            self.prepare_data()
    
    def prepare_data(self):
        """Prepare and validate the input data."""
        if 'symbol' in self.data.columns:
            self.cryptocurrencies = self.data['symbol'].unique().tolist()
        
        # Ensure datetime index
        if 'timestamp' in self.data.columns:
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            self.data.set_index('timestamp', inplace=True)
    
    def analyze_price_patterns(self, crypto_symbol: str = 'BTC') -> Dict:
        """
        Analyze price patterns for a specific cryptocurrency.
        
        Args:
            crypto_symbol: Symbol of cryptocurrency to analyze
            
        Returns:
            Dictionary with price pattern analysis results
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        crypto_data = self.data[self.data['symbol'] == crypto_symbol].copy()
        
        analysis = {
            'symbol': crypto_symbol,
            'daily_returns': crypto_data['price'].pct_change(),
            'volatility': crypto_data['price'].pct_change().std() * np.sqrt(365),
            'max_drawdown': self._calculate_max_drawdown(crypto_data['price']),
            'price_range': {
                'min': crypto_data['price'].min(),
                'max': crypto_data['price'].max(),
                'current': crypto_data['price'].iloc[-1]
            }
        }
        
        return analysis
    
    def correlation_analysis(self) -> pd.DataFrame:
        """
        Analyze correlations between different cryptocurrencies.
        
        Returns:
            Correlation matrix DataFrame
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        # Pivot data to have cryptocurrencies as columns
        price_data = self.data.pivot(columns='symbol', values='price')
        
        # Calculate daily returns
        returns = price_data.pct_change().dropna()
        
        # Calculate correlation matrix
        correlation_matrix = returns.corr()
        
        return correlation_matrix
    
    def volume_price_relationship(self, crypto_symbol: str = 'BTC') -> Dict:
        """
        Analyze relationship between volume and price movements.
        
        Args:
            crypto_symbol: Symbol of cryptocurrency to analyze
            
        Returns:
            Dictionary with volume-price analysis
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        crypto_data = self.data[self.data['symbol'] == crypto_symbol].copy()
        
        # Calculate price changes and volume changes
        crypto_data['price_change'] = crypto_data['price'].pct_change()
        crypto_data['volume_change'] = crypto_data['volume'].pct_change()
        
        # Correlation between volume and price changes
        volume_price_corr = crypto_data['volume_change'].corr(crypto_data['price_change'])
        
        analysis = {
            'symbol': crypto_symbol,
            'volume_price_correlation': volume_price_corr,
            'avg_volume': crypto_data['volume'].mean(),
            'volume_volatility': crypto_data['volume'].std(),
            'high_volume_days': len(crypto_data[crypto_data['volume'] > crypto_data['volume'].quantile(0.9)])
        }
        
        return analysis
    
    def seasonal_analysis(self, crypto_symbol: str = 'BTC') -> Dict:
        """
        Analyze seasonal patterns in cryptocurrency prices.
        
        Args:
            crypto_symbol: Symbol of cryptocurrency to analyze
            
        Returns:
            Dictionary with seasonal analysis results
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        crypto_data = self.data[self.data['symbol'] == crypto_symbol].copy()
        crypto_data = crypto_data.reset_index()
        
        # Extract time components
        crypto_data['month'] = crypto_data['timestamp'].dt.month
        crypto_data['day_of_week'] = crypto_data['timestamp'].dt.dayofweek
        crypto_data['hour'] = crypto_data['timestamp'].dt.hour
        
        # Calculate returns
        crypto_data['returns'] = crypto_data['price'].pct_change()
        
        # Monthly analysis
        monthly_returns = crypto_data.groupby('month')['returns'].mean()
        
        # Day of week analysis
        dow_returns = crypto_data.groupby('day_of_week')['returns'].mean()
        
        analysis = {
            'symbol': crypto_symbol,
            'monthly_patterns': monthly_returns.to_dict(),
            'day_of_week_patterns': dow_returns.to_dict(),
            'best_month': monthly_returns.idxmax(),
            'worst_month': monthly_returns.idxmin(),
            'best_day_of_week': dow_returns.idxmax(),
            'worst_day_of_week': dow_returns.idxmin()
        }
        
        return analysis
    
    def market_cap_analysis(self) -> Dict:
        """
        Analyze market capitalization patterns across cryptocurrencies.
        
        Returns:
            Dictionary with market cap analysis
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        # Get latest data for each cryptocurrency
        latest_data = self.data.groupby('symbol').last()
        
        # Calculate market cap if not present
        if 'market_cap' not in latest_data.columns:
            if 'circulating_supply' in latest_data.columns:
                latest_data['market_cap'] = latest_data['price'] * latest_data['circulating_supply']
        
        if 'market_cap' in latest_data.columns:
            analysis = {
                'total_market_cap': latest_data['market_cap'].sum(),
                'market_cap_distribution': latest_data['market_cap'].describe().to_dict(),
                'top_5_by_market_cap': latest_data.nlargest(5, 'market_cap')[['price', 'market_cap']].to_dict(),
                'market_dominance': (latest_data['market_cap'] / latest_data['market_cap'].sum()).to_dict()
            }
        else:
            analysis = {'error': 'Market cap data not available'}
        
        return analysis
    
    def _calculate_max_drawdown(self, price_series: pd.Series) -> float:
        """
        Calculate maximum drawdown for a price series.
        
        Args:
            price_series: Series of prices
            
        Returns:
            Maximum drawdown as percentage
        """
        # Calculate running maximum
        running_max = price_series.expanding().max()
        
        # Calculate drawdown
        drawdown = (price_series - running_max) / running_max
        
        # Return maximum drawdown (most negative value)
        return drawdown.min()
    
    def generate_exploration_report(self, output_file: str = None) -> Dict:
        """
        Generate comprehensive exploration report for all cryptocurrencies.
        
        Args:
            output_file: Optional file path to save the report
            
        Returns:
            Dictionary containing all analysis results
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        report = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_period': {
                'start': self.data.index.min().strftime('%Y-%m-%d'),
                'end': self.data.index.max().strftime('%Y-%m-%d'),
                'total_days': (self.data.index.max() - self.data.index.min()).days
            },
            'cryptocurrencies_analyzed': self.cryptocurrencies,
            'correlation_matrix': self.correlation_analysis().to_dict(),
            'market_cap_analysis': self.market_cap_analysis(),
            'individual_crypto_analysis': {}
        }
        
        # Analyze each cryptocurrency individually
        for crypto in self.cryptocurrencies[:5]:  # Limit to top 5 for performance
            try:
                report['individual_crypto_analysis'][crypto] = {
                    'price_patterns': self.analyze_price_patterns(crypto),
                    'volume_analysis': self.volume_price_relationship(crypto),
                    'seasonal_patterns': self.seasonal_analysis(crypto)
                }
            except Exception as e:
                report['individual_crypto_analysis'][crypto] = {'error': str(e)}
        
        # Save report if requested
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        
        return report


def load_crypto_data(source: str = 'database') -> pd.DataFrame:
    """
    Load cryptocurrency data from specified source.
    
    Args:
        source: Data source ('database', 'csv', 'api')
        
    Returns:
        DataFrame with cryptocurrency data
    """
    # TODO: Implement data loading from different sources
    print(f"Loading crypto data from {source}...")
    
    # Placeholder for actual implementation
    return pd.DataFrame()


if __name__ == "__main__":
    # Example usage
    print("Cryptocurrency Data Explorer")
    print("Loading data...")
    
    # data = load_crypto_data('database')
    # explorer = CryptoDataExplorer(data)
    # report = explorer.generate_exploration_report('crypto_exploration_report.json')
    # print("Exploration report generated!")
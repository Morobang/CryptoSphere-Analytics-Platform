"""
Market Pattern Analyzer

This module identifies and analyzes recurring patterns in cryptocurrency markets
such as support/resistance levels, trend channels, and breakout patterns.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional
from scipy import stats
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')


class MarketPatternAnalyzer:
    """
    Analyzes market patterns in cryptocurrency data.
    """
    
    def __init__(self, data: pd.DataFrame = None):
        """
        Initialize the market pattern analyzer.
        
        Args:
            data: DataFrame with cryptocurrency data
        """
        self.data = data
        self.patterns = {}
    
    def identify_support_resistance(self, crypto_symbol: str, window: int = 20, 
                                  threshold: float = 0.02) -> Dict:
        """
        Identify support and resistance levels.
        
        Args:
            crypto_symbol: Cryptocurrency symbol
            window: Rolling window for local extrema
            threshold: Minimum price difference threshold
            
        Returns:
            Dictionary with support and resistance levels
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        crypto_data = self.data[self.data['symbol'] == crypto_symbol].copy()
        prices = crypto_data['price']
        
        # Find local minima (support) and maxima (resistance)
        local_min_indices = []
        local_max_indices = []
        
        for i in range(window, len(prices) - window):
            # Check for local minimum
            if prices.iloc[i] == prices.iloc[i-window:i+window+1].min():
                local_min_indices.append(i)
            
            # Check for local maximum
            if prices.iloc[i] == prices.iloc[i-window:i+window+1].max():
                local_max_indices.append(i)
        
        # Cluster similar price levels
        support_levels = self._cluster_price_levels(
            [prices.iloc[i] for i in local_min_indices], threshold
        )
        resistance_levels = self._cluster_price_levels(
            [prices.iloc[i] for i in local_max_indices], threshold
        )
        
        return {
            'symbol': crypto_symbol,
            'support_levels': support_levels,
            'resistance_levels': resistance_levels,
            'current_price': prices.iloc[-1],
            'nearest_support': min(support_levels, key=lambda x: abs(x - prices.iloc[-1])),
            'nearest_resistance': min(resistance_levels, key=lambda x: abs(x - prices.iloc[-1]))
        }
    
    def detect_trend_channels(self, crypto_symbol: str, lookback_days: int = 60) -> Dict:
        """
        Detect trend channels using linear regression.
        
        Args:
            crypto_symbol: Cryptocurrency symbol
            lookback_days: Number of days to look back
            
        Returns:
            Dictionary with trend channel information
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        crypto_data = self.data[self.data['symbol'] == crypto_symbol].copy()
        recent_data = crypto_data.tail(lookback_days)
        
        # Prepare data for linear regression
        x = np.arange(len(recent_data))
        y = recent_data['price'].values
        
        # Calculate trend line
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        trend_line = slope * x + intercept
        
        # Calculate channel bounds
        residuals = y - trend_line
        upper_bound = trend_line + 2 * np.std(residuals)
        lower_bound = trend_line - 2 * np.std(residuals)
        
        # Determine trend direction
        if slope > 0:
            trend_direction = 'upward'
        elif slope < 0:
            trend_direction = 'downward'
        else:
            trend_direction = 'sideways'
        
        return {
            'symbol': crypto_symbol,
            'trend_direction': trend_direction,
            'slope': slope,
            'r_squared': r_value ** 2,
            'current_position': 'upper' if y[-1] > trend_line[-1] else 'lower',
            'trend_strength': abs(r_value),
            'channel_width': np.mean(upper_bound - lower_bound)
        }
    
    def identify_breakout_patterns(self, crypto_symbol: str, 
                                 consolidation_days: int = 14) -> Dict:
        """
        Identify potential breakout patterns.
        
        Args:
            crypto_symbol: Cryptocurrency symbol
            consolidation_days: Minimum days of consolidation
            
        Returns:
            Dictionary with breakout pattern information
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        crypto_data = self.data[self.data['symbol'] == crypto_symbol].copy()
        
        # Calculate volatility and price range
        crypto_data['volatility'] = crypto_data['price'].rolling(window=consolidation_days).std()
        crypto_data['price_range'] = (crypto_data['price'].rolling(window=consolidation_days).max() - 
                                    crypto_data['price'].rolling(window=consolidation_days).min())
        
        # Identify consolidation periods (low volatility)
        volatility_threshold = crypto_data['volatility'].quantile(0.3)
        consolidation_mask = crypto_data['volatility'] < volatility_threshold
        
        # Current market state
        current_volatility = crypto_data['volatility'].iloc[-1]
        recent_range = crypto_data['price_range'].iloc[-1]
        
        # Determine breakout potential
        if current_volatility < volatility_threshold:
            breakout_potential = 'high'
        elif current_volatility < crypto_data['volatility'].median():
            breakout_potential = 'medium'
        else:
            breakout_potential = 'low'
        
        return {
            'symbol': crypto_symbol,
            'breakout_potential': breakout_potential,
            'current_volatility': current_volatility,
            'volatility_percentile': stats.percentileofscore(crypto_data['volatility'].dropna(), 
                                                           current_volatility),
            'consolidation_days': consolidation_days,
            'recent_price_range': recent_range
        }
    
    def analyze_volume_patterns(self, crypto_symbol: str) -> Dict:
        """
        Analyze volume patterns and their relationship to price movements.
        
        Args:
            crypto_symbol: Cryptocurrency symbol
            
        Returns:
            Dictionary with volume pattern analysis
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        crypto_data = self.data[self.data['symbol'] == crypto_symbol].copy()
        
        # Calculate price and volume changes
        crypto_data['price_change'] = crypto_data['price'].pct_change()
        crypto_data['volume_change'] = crypto_data['volume'].pct_change()
        
        # Volume moving averages
        crypto_data['volume_ma_7'] = crypto_data['volume'].rolling(window=7).mean()
        crypto_data['volume_ma_21'] = crypto_data['volume'].rolling(window=21).mean()
        
        # Volume patterns
        high_volume_up = crypto_data[
            (crypto_data['volume'] > crypto_data['volume_ma_21']) & 
            (crypto_data['price_change'] > 0)
        ]
        high_volume_down = crypto_data[
            (crypto_data['volume'] > crypto_data['volume_ma_21']) & 
            (crypto_data['price_change'] < 0)
        ]
        
        return {
            'symbol': crypto_symbol,
            'avg_volume': crypto_data['volume'].mean(),
            'volume_trend': 'increasing' if crypto_data['volume_ma_7'].iloc[-1] > crypto_data['volume_ma_21'].iloc[-1] else 'decreasing',
            'high_volume_up_days': len(high_volume_up),
            'high_volume_down_days': len(high_volume_down),
            'volume_price_correlation': crypto_data['volume_change'].corr(crypto_data['price_change']),
            'current_volume_vs_avg': crypto_data['volume'].iloc[-1] / crypto_data['volume'].mean()
        }
    
    def _cluster_price_levels(self, prices: List[float], threshold: float) -> List[float]:
        """
        Cluster similar price levels together.
        
        Args:
            prices: List of price levels
            threshold: Maximum distance threshold for clustering
            
        Returns:
            List of clustered price levels
        """
        if not prices:
            return []
        
        prices = np.array(prices).reshape(-1, 1)
        
        # Use KMeans clustering
        n_clusters = min(len(prices), 5)  # Limit to 5 clusters
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(prices)
        
        # Get cluster centers
        centers = kmeans.cluster_centers_.flatten()
        
        # Filter out clusters that are too close
        filtered_centers = []
        for center in sorted(centers):
            if not filtered_centers or min(abs(center - fc) / fc for fc in filtered_centers) > threshold:
                filtered_centers.append(center)
        
        return sorted(filtered_centers)
    
    def generate_pattern_report(self, crypto_symbols: List[str] = None) -> Dict:
        """
        Generate comprehensive pattern analysis report.
        
        Args:
            crypto_symbols: List of symbols to analyze
            
        Returns:
            Dictionary with pattern analysis for all symbols
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        if crypto_symbols is None:
            crypto_symbols = self.data['symbol'].unique()[:5]  # Limit to 5 for performance
        
        report = {
            'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbols_analyzed': crypto_symbols,
            'pattern_analysis': {}
        }
        
        for symbol in crypto_symbols:
            try:
                report['pattern_analysis'][symbol] = {
                    'support_resistance': self.identify_support_resistance(symbol),
                    'trend_channels': self.detect_trend_channels(symbol),
                    'breakout_patterns': self.identify_breakout_patterns(symbol),
                    'volume_patterns': self.analyze_volume_patterns(symbol)
                }
            except Exception as e:
                report['pattern_analysis'][symbol] = {'error': str(e)}
        
        return report


if __name__ == "__main__":
    # Example usage
    print("Market Pattern Analyzer")
    print("This module analyzes market patterns in cryptocurrency data")
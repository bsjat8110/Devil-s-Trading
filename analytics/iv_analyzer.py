"""
IV (Implied Volatility) Analyzer
Tracks IV percentile and IV rank
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IVAnalyzer:
    """
    Analyze Implied Volatility metrics
    """
    
    def __init__(self):
        """Initialize IV Analyzer"""
        self.iv_history = {}  # symbol -> list of (date, iv) tuples
        logger.info("✅ IV Analyzer initialized")
    
    def add_iv_data(self, symbol: str, iv: float, timestamp: Optional[datetime] = None):
        """
        Add IV data point
        
        Args:
            symbol: Symbol name (e.g., 'NIFTY')
            iv: IV value in %
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if symbol not in self.iv_history:
            self.iv_history[symbol] = []
        
        self.iv_history[symbol].append((timestamp, iv))
        
        # Keep only last 365 days
        cutoff_date = datetime.now() - timedelta(days=365)
        self.iv_history[symbol] = [
            (ts, iv_val) for ts, iv_val in self.iv_history[symbol]
            if ts >= cutoff_date
        ]
    
    def calculate_iv_percentile(self, symbol: str, current_iv: float, days: int = 252) -> float:
        """
        Calculate IV Percentile (0-100)
        
        IV Percentile = % of time IV was below current IV
        
        Args:
            symbol: Symbol name
            current_iv: Current IV value
            days: Lookback period (default 252 = 1 year)
            
        Returns:
            IV Percentile (0-100)
        """
        if symbol not in self.iv_history or len(self.iv_history[symbol]) < 10:
            return 50.0  # Default to midpoint if not enough data
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_ivs = [
            iv_val for ts, iv_val in self.iv_history[symbol]
            if ts >= cutoff_date
        ]
        
        if not recent_ivs:
            return 50.0
        
        below_count = sum(1 for iv in recent_ivs if iv < current_iv)
        percentile = (below_count / len(recent_ivs)) * 100
        
        return percentile
    
    def calculate_iv_rank(self, symbol: str, current_iv: float, days: int = 252) -> float:
        """
        Calculate IV Rank (0-100)
        
        IV Rank = (Current IV - Min IV) / (Max IV - Min IV) * 100
        
        Args:
            symbol: Symbol name
            current_iv: Current IV value
            days: Lookback period
            
        Returns:
            IV Rank (0-100)
        """
        if symbol not in self.iv_history or len(self.iv_history[symbol]) < 10:
            return 50.0
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_ivs = [
            iv_val for ts, iv_val in self.iv_history[symbol]
            if ts >= cutoff_date
        ]
        
        if not recent_ivs:
            return 50.0
        
        min_iv = min(recent_ivs)
        max_iv = max(recent_ivs)
        
        if max_iv == min_iv:
            return 50.0
        
        iv_rank = ((current_iv - min_iv) / (max_iv - min_iv)) * 100
        
        return iv_rank
    
    def interpret_iv_percentile(self, percentile: float) -> Dict[str, str]:
        """
        Interpret IV Percentile
        
        Returns:
            Dictionary with interpretation and recommendation
        """
        if percentile < 20:
            return {
                'status': 'VERY LOW',
                'description': 'IV is extremely low -Options are cheap',
                'recommendation': 'Good time to BUY options (Long Straddle/Strangle)'
            }
        elif percentile < 40:
            return {
                'status': 'LOW',
                'description': 'IV is below average',
                'recommendation': 'Consider buying options'
            }
        elif percentile < 60:
            return {
                'status': 'NORMAL',
                'description': 'IV is around average',
                'recommendation': 'Neutral - No strong IV edge'
            }
        elif percentile < 80:
            return {
                'status': 'HIGH',
                'description': 'IV is above average',
                'recommendation': 'Consider selling options (Credit Spreads)'
            }
        else:
            return {
                'status': 'VERY HIGH',
                'description': 'IV is extremely high - Options are expensive',
                'recommendation': 'Good time to SELL options (Iron Condor/Credit Spreads)'
            }
    
    def get_iv_analysis(self, symbol: str, current_iv: float) -> Dict:
        """
        Get complete IV analysis
        
        Args:
            symbol: Symbol name
            current_iv: Current IV value
            
        Returns:
            Complete IV analysis dictionary
        """
        percentile = self.calculate_iv_percentile(symbol, current_iv)
        rank = self.calculate_iv_rank(symbol, current_iv)
        interpretation = self.interpret_iv_percentile(percentile)
        
        return {
            'symbol': symbol,
            'current_iv': current_iv,
            'iv_percentile': percentile,
            'iv_rank': rank,
            'status': interpretation['status'],
            'description': interpretation['description'],
            'recommendation': interpretation['recommendation']
        }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING IV ANALYZER")
    print("="*60 + "\n")
    
    analyzer = IVAnalyzer()
    
    # Simulate historical IV data
    print("Generating dummy IV history...")
    for i in range(100):
        days_ago = 100 - i
        iv = 15 + np.random.randn() * 3  # IV around 15% with some variation
        timestamp = datetime.now() - timedelta(days=days_ago)
        analyzer.add_iv_data('NIFTY', iv, timestamp)
    
    # Analyze current IV
    current_iv = 18.5
    analysis = analyzer.get_iv_analysis('NIFTY', current_iv)
    
    print("NIFTY IV Analysis:")
    print("-" * 60)
    print(f"Current IV:      {analysis['current_iv']:.2f}%")
    print(f"IV Percentile:   {analysis['iv_percentile']:.1f}%")
    print(f"IV Rank:         {analysis['iv_rank']:.1f}%")
    print(f"Status:          {analysis['status']}")
    print(f"Description:     {analysis['description']}")
    print(f"Recommendation:  {analysis['recommendation']}")
    print()
    
    print("="*60 + "\n")

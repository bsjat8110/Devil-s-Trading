"""
Base Strategy Class
All strategies inherit from this
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict
from datetime import datetime


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies
    """
    
    def __init__(self, name: str):
        self.name = name
        self.trades = []
        self.signals_history = []
        
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """
        Generate trading signal
        
        Returns:
            {
                'signal': 'BUY', 'SELL', or 'NEUTRAL',
                'strength': 0-100,
                'reason': 'explanation',
                'entry_price': float,
                'stop_loss': float,
                'target': float
            }
        """
        pass
    
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate strategy-specific indicators"""
        pass
    
    def get_position_size(self, capital: float, risk_pct: float = 2) -> int:
        """
        Calculate position size based on risk
        
        capital: Total capital
        risk_pct: Risk per trade (default 2%)
        """
        risk_amount = capital * (risk_pct / 100)
        # Simple position sizing (can be enhanced)
        return int(risk_amount / 100)  # Assuming ₹100 risk per unit
    
    def log_signal(self, signal: Dict):
        """Log signal for analysis"""
        signal['timestamp'] = datetime.now()
        signal['strategy'] = self.name
        self.signals_history.append(signal)
    
    def get_performance_summary(self) -> Dict:
        """Get strategy performance summary"""
        if not self.signals_history:
            return {'total_signals': 0}
        
        df = pd.DataFrame(self.signals_history)
        
        buy_signals = (df['signal'] == 'BUY').sum()
        sell_signals = (df['signal'] == 'SELL').sum()
        neutral_signals = (df['signal'] == 'NEUTRAL').sum()
        
        avg_strength = df['strength'].mean()
        
        return {
            'total_signals': len(self.signals_history),
            'buy_signals': int(buy_signals),
            'sell_signals': int(sell_signals),
            'neutral_signals': int(neutral_signals),
            'avg_strength': round(avg_strength, 2)
        }

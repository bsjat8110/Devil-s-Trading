"""
RSI Reversal Strategy
Mean-reversion based on RSI
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy


class RSIReversalStrategy(BaseStrategy):
    """
    RSI Reversal Strategy
    
    - Buy: RSI < 30 (oversold)
    - Sell: RSI > 70 (overbought)
    """
    
    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__("RSI Reversal")
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        
    def calculate_rsi(self, df: pd.DataFrame) -> pd.Series:
        """Calculate RSI"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI"""
        df = df.copy()
        df['rsi'] = self.calculate_rsi(df)
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate RSI reversal signal"""
        
        df = self.calculate_indicators(df)
        
        if len(df) < self.rsi_period + 5:
            return {
                'signal': 'NEUTRAL',
                'strength': 0,
                'reason': 'Insufficient data',
                'entry_price': 0,
                'stop_loss': 0,
                'target': 0
            }
        
        current = df.iloc[-1]
        current_price = current['close']
        rsi = current['rsi']
        
        # Oversold - Buy signal
        if rsi < self.oversold:
            signal = 'BUY'
            strength = (self.oversold - rsi) / self.oversold * 100
            reason = f'RSI oversold at {rsi:.1f}'
            
            stop_loss = current_price * 0.97
            target = current_price * 1.05
        
        # Overbought - Sell signal
        elif rsi > self.overbought:
            signal = 'SELL'
            strength = (rsi - self.overbought) / (100 - self.overbought) * 100
            reason = f'RSI overbought at {rsi:.1f}'
            
            stop_loss = current_price * 1.03
            target = current_price * 0.95
        
        # Neutral zone
        else:
            signal = 'NEUTRAL'
            strength = 0
            reason = f'RSI in neutral zone at {rsi:.1f}'
            
            stop_loss = current_price * 0.98
            target = current_price * 1.02
        
        result = {
            'signal': signal,
            'strength': round(min(100, strength), 2),
            'reason': reason,
            'entry_price': round(current_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2),
            'rsi': round(rsi, 2)
        }
        
        self.log_signal(result)
        return result

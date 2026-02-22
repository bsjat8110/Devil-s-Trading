"""
MACD Momentum Strategy
Momentum-based trading with MACD
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy


class MACDMomentumStrategy(BaseStrategy):
    """
    MACD Momentum Strategy
    
    - Buy: MACD crosses above signal line
    - Sell: MACD crosses below signal line
    """
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__("MACD Momentum")
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD"""
        df = df.copy()
        
        ema_fast = df['close'].ewm(span=self.fast).mean()
        ema_slow = df['close'].ewm(span=self.slow).mean()
        
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=self.signal_period).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate MACD signal"""
        
        df = self.calculate_indicators(df)
        
        if len(df) < self.slow + self.signal_period + 2:
            return {
                'signal': 'NEUTRAL',
                'strength': 0,
                'reason': 'Insufficient data',
                'entry_price': 0,
                'stop_loss': 0,
                'target': 0
            }
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        current_price = current['close']
        macd = current['macd']
        macd_signal = current['macd_signal']
        macd_hist = current['macd_hist']
        
        prev_macd = previous['macd']
        prev_signal = previous['macd_signal']
        
        # Bullish crossover
        if prev_macd <= prev_signal and macd > macd_signal:
            signal = 'BUY'
            strength = min(100, abs(macd_hist) * 10 + 60)
            reason = f'MACD bullish crossover'
            
            stop_loss = current_price * 0.98
            target = current_price * 1.05
        
        # Bearish crossover
        elif prev_macd >= prev_signal and macd < macd_signal:
            signal = 'SELL'
            strength = min(100, abs(macd_hist) * 10 + 60)
            reason = f'MACD bearish crossover'
            
            stop_loss = current_price * 1.02
            target = current_price * 0.95
        
        # MACD above signal (bullish momentum)
        elif macd > macd_signal and macd_hist > 0:
            signal = 'NEUTRAL'
            strength = 40
            reason = 'Bullish momentum but no fresh cross'
            
            stop_loss = current_price * 0.98
            target = current_price * 1.03
        
        # MACD below signal (bearish momentum)
        elif macd < macd_signal and macd_hist < 0:
            signal = 'NEUTRAL'
            strength = 40
            reason = 'Bearish momentum but no fresh cross'
            
            stop_loss = current_price * 1.02
            target = current_price * 0.97
        
        else:
            signal = 'NEUTRAL'
            strength = 0
            reason = 'No clear MACD signal'
            
            stop_loss = current_price * 0.98
            target = current_price * 1.02
        
        result = {
            'signal': signal,
            'strength': round(strength, 2),
            'reason': reason,
            'entry_price': round(current_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2),
            'macd': round(macd, 2),
            'macd_signal': round(macd_signal, 2),
            'macd_hist': round(macd_hist, 2)
        }
        
        self.log_signal(result)
        return result

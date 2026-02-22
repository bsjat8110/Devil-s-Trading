"""
EMA Crossover Strategy
Classic trend-following strategy
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy


class EMACrossoverStrategy(BaseStrategy):
    """
    EMA Crossover Strategy
    
    - Buy: Fast EMA crosses above Slow EMA
    - Sell: Fast EMA crosses below Slow EMA
    """
    
    def __init__(self, fast_period: int = 9, slow_period: int = 21):
        super().__init__("EMA Crossover")
        self.fast_period = fast_period
        self.slow_period = slow_period
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMAs"""
        df = df.copy()
        df['ema_fast'] = df['close'].ewm(span=self.fast_period).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_period).mean()
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate EMA crossover signal"""
        
        df = self.calculate_indicators(df)
        
        if len(df) < self.slow_period + 2:
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
        ema_fast_curr = current['ema_fast']
        ema_slow_curr = current['ema_slow']
        ema_fast_prev = previous['ema_fast']
        ema_slow_prev = previous['ema_slow']
        
        # Bullish crossover
        if ema_fast_prev <= ema_slow_prev and ema_fast_curr > ema_slow_curr:
            signal = 'BUY'
            distance = abs(ema_fast_curr - ema_slow_curr) / ema_slow_curr * 100
            strength = min(100, distance * 50)
            reason = f'Fast EMA crossed above Slow EMA'
            
            stop_loss = current_price * 0.98  # 2% stop loss
            target = current_price * 1.04  # 4% target
        
        # Bearish crossover
        elif ema_fast_prev >= ema_slow_prev and ema_fast_curr < ema_slow_curr:
            signal = 'SELL'
            distance = abs(ema_fast_curr - ema_slow_curr) / ema_slow_curr * 100
            strength = min(100, distance * 50)
            reason = f'Fast EMA crossed below Slow EMA'
            
            stop_loss = current_price * 1.02
            target = current_price * 0.96
        
        # Trending
        elif ema_fast_curr > ema_slow_curr:
            signal = 'NEUTRAL'
            strength = 30
            reason = 'Uptrend but no fresh crossover'
            stop_loss = current_price * 0.98
            target = current_price * 1.04
        
        elif ema_fast_curr < ema_slow_curr:
            signal = 'NEUTRAL'
            strength = 30
            reason = 'Downtrend but no fresh crossover'
            stop_loss = current_price * 1.02
            target = current_price * 0.96
        
        else:
            signal = 'NEUTRAL'
            strength = 0
            reason = 'No clear signal'
            stop_loss = current_price * 0.98
            target = current_price * 1.02
        
        result = {
            'signal': signal,
            'strength': round(strength, 2),
            'reason': reason,
            'entry_price': round(current_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2),
            'ema_fast': round(ema_fast_curr, 2),
            'ema_slow': round(ema_slow_curr, 2)
        }
        
        self.log_signal(result)
        return result

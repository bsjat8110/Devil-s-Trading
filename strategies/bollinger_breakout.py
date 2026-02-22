"""
Bollinger Breakout Strategy
Breakout trading with Bollinger Bands
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy


class BollingerBreakoutStrategy(BaseStrategy):
    """
    Bollinger Breakout Strategy
    
    - Buy: Price breaks above upper band
    - Sell: Price breaks below lower band
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__("Bollinger Breakout")
        self.period = period
        self.std_dev = std_dev
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        df = df.copy()
        
        df['bb_middle'] = df['close'].rolling(window=self.period).mean()
        rolling_std = df['close'].rolling(window=self.period).std()
        df['bb_upper'] = df['bb_middle'] + (rolling_std * self.std_dev)
        df['bb_lower'] = df['bb_middle'] - (rolling_std * self.std_dev)
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate Bollinger breakout signal"""
        
        df = self.calculate_indicators(df)
        
        if len(df) < self.period + 2:
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
        bb_upper = current['bb_upper']
        bb_lower = current['bb_lower']
        bb_middle = current['bb_middle']
        
        # Upward breakout
        if previous['close'] <= previous['bb_upper'] and current_price > bb_upper:
            signal = 'BUY'
            distance = (current_price - bb_upper) / bb_upper * 100
            strength = min(100, distance * 100 + 50)
            reason = f'Price broke above upper band'
            
            stop_loss = bb_middle
            target = current_price + (current_price - bb_middle)
        
        # Downward breakout
        elif previous['close'] >= previous['bb_lower'] and current_price < bb_lower:
            signal = 'SELL'
            distance = (bb_lower - current_price) / bb_lower * 100
            strength = min(100, distance * 100 + 50)
            reason = f'Price broke below lower band'
            
            stop_loss = bb_middle
            target = current_price - (bb_middle - current_price)
        
        # Price near upper band
        elif current_price > bb_middle and current_price >= bb_upper * 0.98:
            signal = 'NEUTRAL'
            strength = 40
            reason = 'Near upper band, watch for breakout'
            
            stop_loss = bb_middle
            target = bb_upper * 1.02
        
        # Price near lower band
        elif current_price < bb_middle and current_price <= bb_lower * 1.02:
            signal = 'NEUTRAL'
            strength = 40
            reason = 'Near lower band, watch for breakdown'
            
            stop_loss = bb_middle
            target = bb_lower * 0.98
        
        else:
            signal = 'NEUTRAL'
            strength = 0
            reason = 'Price in middle zone'
            
            stop_loss = current_price * 0.98
            target = current_price * 1.02
        
        result = {
            'signal': signal,
            'strength': round(strength, 2),
            'reason': reason,
            'entry_price': round(current_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2),
            'bb_upper': round(bb_upper, 2),
            'bb_middle': round(bb_middle, 2),
            'bb_lower': round(bb_lower, 2)
        }
        
        self.log_signal(result)
        return result

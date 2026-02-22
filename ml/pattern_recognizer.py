"""
Candlestick Pattern Recognition
Detects bullish/bearish patterns automatically
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class PatternRecognizer:
    """
    Recognize candlestick patterns
    """
    
    def __init__(self):
        self.patterns_found = []
        
    def is_bullish_engulfing(self, df: pd.DataFrame, idx: int = -1) -> bool:
        """Detect bullish engulfing pattern"""
        
        if len(df) < abs(idx) + 2:
            return False
        
        curr = df.iloc[idx]
        prev = df.iloc[idx - 1]
        
        # Previous candle is bearish (red)
        prev_bearish = prev['close'] < prev['open']
        
        # Current candle is bullish (green)
        curr_bullish = curr['close'] > curr['open']
        
        # Current candle engulfs previous
        engulfs = (curr['open'] < prev['close'] and 
                   curr['close'] > prev['open'])
        
        return prev_bearish and curr_bullish and engulfs
    
    def is_bearish_engulfing(self, df: pd.DataFrame, idx: int = -1) -> bool:
        """Detect bearish engulfing pattern"""
        
        if len(df) < abs(idx) + 2:
            return False
        
        curr = df.iloc[idx]
        prev = df.iloc[idx - 1]
        
        # Previous candle is bullish
        prev_bullish = prev['close'] > prev['open']
        
        # Current candle is bearish
        curr_bearish = curr['close'] < curr['open']
        
        # Current candle engulfs previous
        engulfs = (curr['open'] > prev['close'] and 
                   curr['close'] < prev['open'])
        
        return prev_bullish and curr_bearish and engulfs
    
    def is_hammer(self, df: pd.DataFrame, idx: int = -1) -> bool:
        """Detect hammer pattern (bullish reversal)"""
        
        if len(df) < abs(idx) + 1:
            return False
        
        candle = df.iloc[idx]
        
        body = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        # Lower shadow is at least 2x the body
        # Upper shadow is small
        return (lower_shadow > 2 * body and 
                upper_shadow < body and 
                body > 0)
    
    def is_shooting_star(self, df: pd.DataFrame, idx: int = -1) -> bool:
        """Detect shooting star pattern (bearish reversal)"""
        
        if len(df) < abs(idx) + 1:
            return False
        
        candle = df.iloc[idx]
        
        body = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        # Upper shadow is at least 2x the body
        # Lower shadow is small
        return (upper_shadow > 2 * body and 
                lower_shadow < body and 
                body > 0)
    
    def is_doji(self, df: pd.DataFrame, idx: int = -1) -> bool:
        """Detect doji pattern (indecision)"""
        
        if len(df) < abs(idx) + 1:
            return False
        
        candle = df.iloc[idx]
        
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        
        # Body is very small compared to total range
        return body < (total_range * 0.1) and total_range > 0
    
    def is_morning_star(self, df: pd.DataFrame, idx: int = -1) -> bool:
        """Detect morning star pattern (bullish reversal)"""
        
        if len(df) < abs(idx) + 3:
            return False
        
        first = df.iloc[idx - 2]
        second = df.iloc[idx - 1]
        third = df.iloc[idx]
        
        # First candle is bearish
        first_bearish = first['close'] < first['open']
        
        # Second candle is small (doji-like)
        second_small = abs(second['close'] - second['open']) < abs(first['close'] - first['open']) * 0.5
        
        # Third candle is bullish and closes above midpoint of first
        third_bullish = third['close'] > third['open']
        closes_high = third['close'] > (first['open'] + first['close']) / 2
        
        return first_bearish and second_small and third_bullish and closes_high
    
    def is_evening_star(self, df: pd.DataFrame, idx: int = -1) -> bool:
        """Detect evening star pattern (bearish reversal)"""
        
        if len(df) < abs(idx) + 3:
            return False
        
        first = df.iloc[idx - 2]
        second = df.iloc[idx - 1]
        third = df.iloc[idx]
        
        # First candle is bullish
        first_bullish = first['close'] > first['open']
        
        # Second candle is small
        second_small = abs(second['close'] - second['open']) < abs(first['close'] - first['open']) * 0.5
        
        # Third candle is bearish and closes below midpoint of first
        third_bearish = third['close'] < third['open']
        closes_low = third['close'] < (first['open'] + first['close']) / 2
        
        return first_bullish and second_small and third_bearish and closes_low
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        Analyze all patterns
        """
        
        patterns = {
            'bullish_engulfing': self.is_bullish_engulfing(df),
            'bearish_engulfing': self.is_bearish_engulfing(df),
            'hammer': self.is_hammer(df),
            'shooting_star': self.is_shooting_star(df),
            'doji': self.is_doji(df),
            'morning_star': self.is_morning_star(df),
            'evening_star': self.is_evening_star(df)
        }
        
        self.patterns_found = [name for name, found in patterns.items() if found]
        
        return patterns
    
    def get_signal(self, patterns: Dict[str, bool]) -> Dict:
        """
        Get trading signal from patterns
        """
        
        bullish_patterns = ['bullish_engulfing', 'hammer', 'morning_star']
        bearish_patterns = ['bearish_engulfing', 'shooting_star', 'evening_star']
        
        bullish_count = sum(1 for p in bullish_patterns if patterns.get(p, False))
        bearish_count = sum(1 for p in bearish_patterns if patterns.get(p, False))
        
        if bullish_count > bearish_count:
            signal = 'BUY'
            strength = bullish_count * 30
        elif bearish_count > bullish_count:
            signal = 'SELL'
            strength = bearish_count * 30
        else:
            signal = 'NEUTRAL'
            strength = 0
        
        found_patterns = [name for name, detected in patterns.items() if detected]
        
        return {
            'signal': signal,
            'strength': min(100, strength),
            'patterns': found_patterns,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count
        }


if __name__ == "__main__":
    print("📊 Testing Pattern Recognizer...\n")
    
    # Generate sample data with a bullish engulfing
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='1D')
    
    close = 100 + np.cumsum(np.random.randn(100))
    
    sample_df = pd.DataFrame({
        'open': close - np.random.rand(100) * 2,
        'high': close + np.random.rand(100) * 3,
        'low': close - np.random.rand(100) * 3,
        'close': close,
        'volume': np.random.randint(100000, 500000, 100)
    }, index=dates)
    
    # Manually create a bullish engulfing
    sample_df.iloc[-2, sample_df.columns.get_loc('open')] = 100
    sample_df.iloc[-2, sample_df.columns.get_loc('close')] = 98
    sample_df.iloc[-1, sample_df.columns.get_loc('open')] = 97
    sample_df.iloc[-1, sample_df.columns.get_loc('close')] = 102
    
    recognizer = PatternRecognizer()
    patterns = recognizer.analyze(sample_df)
    signal = recognizer.get_signal(patterns)
    
    print("📊 PATTERN RECOGNITION RESULTS:")
    print("=" * 60)
    print(f"Signal: {signal['signal']}")
    print(f"Strength: {signal['strength']}/100")
    print(f"\nPatterns Detected:")
    for pattern in signal['patterns']:
        print(f"   ✅ {pattern.replace('_', ' ').title()}")
    
    if not signal['patterns']:
        print("   No patterns detected")

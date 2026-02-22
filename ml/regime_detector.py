"""
Market Regime Detection
Identifies if market is trending, ranging, or volatile
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Detect current market regime
    """
    
    REGIMES = {
        'trending_up': 'Strong uptrend - Follow the trend',
        'trending_down': 'Strong downtrend - Follow the trend',
        'ranging': 'Sideways/ranging - Mean reversion strategies',
        'volatile': 'High volatility - Reduce position size',
        'calm': 'Low volatility - Can increase size'
    }
    
    def __init__(self):
        self.current_regime = None
        
    def calculate_atr_normalized(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate normalized ATR (as % of price)"""
        
        if len(df) < period:
            return 0.0
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        # Normalize by price
        atr_pct = (atr / close * 100).iloc[-1]
        
        return atr_pct
    
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate ADX (trend strength indicator)"""
        
        if len(df) < period + 1:
            return 0.0
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Plus/Minus Directional Movement
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Smoothed TR and DM
        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx.iloc[-1] if not adx.empty else 0.0
    
    def detect_regime(self, df: pd.DataFrame) -> Dict:
        """
        Detect current market regime
        
        Returns dict with regime type and confidence
        """
        
        if df.empty or len(df) < 30:
            return {'regime': 'unknown', 'confidence': 0}
        
        # Calculate indicators
        atr_pct = self.calculate_atr_normalized(df)
        adx = self.calculate_adx(df)
        
        # Price trend
        sma_20 = df['close'].rolling(20).mean()
        sma_50 = df['close'].rolling(50).mean()
        
        current_price = df['close'].iloc[-1]
        sma_20_val = sma_20.iloc[-1] if len(sma_20) > 0 else current_price
        sma_50_val = sma_50.iloc[-1] if len(sma_50) > 0 else current_price
        
        # Price momentum
        returns = df['close'].pct_change()
        recent_returns = returns.tail(20).mean() * 100
        
        # Regime detection logic
        regime = 'ranging'
        confidence = 0
        
        # High volatility regime
        if atr_pct > 2.5:
            regime = 'volatile'
            confidence = min(100, atr_pct * 20)
        
        # Low volatility regime
        elif atr_pct < 0.8:
            regime = 'calm'
            confidence = min(100, (1 - atr_pct) * 60)
        
        # Trending regime (ADX > 25 indicates trend)
        elif adx > 25:
            if current_price > sma_20_val > sma_50_val and recent_returns > 0:
                regime = 'trending_up'
                confidence = min(100, adx)
            elif current_price < sma_20_val < sma_50_val and recent_returns < 0:
                regime = 'trending_down'
                confidence = min(100, adx)
            else:
                regime = 'ranging'
                confidence = 50
        
        # Ranging regime
        else:
            regime = 'ranging'
            confidence = min(100, (25 - adx) * 4)
        
        self.current_regime = regime
        
        result = {
            'regime': regime,
            'confidence': round(confidence, 2),
            'description': self.REGIMES.get(regime, 'Unknown'),
            'atr_pct': round(atr_pct, 2),
            'adx': round(adx, 2),
            'trend_direction': 'up' if recent_returns > 0 else 'down'
        }
        
        logger.info(f"Detected regime: {regime} ({confidence:.1f}% confidence)")
        
        return result
    
    def get_strategy_recommendation(self, regime: str) -> Dict:
        """
        Get trading strategy recommendation based on regime
        """
        
        recommendations = {
            'trending_up': {
                'strategy': 'Trend Following',
                'signals': ['Buy dips', 'Hold winners', 'Trail stop loss'],
                'avoid': ['Counter-trend trades', 'Mean reversion']
            },
            'trending_down': {
                'strategy': 'Trend Following',
                'signals': ['Short rallies', 'Exit longs quickly'],
                'avoid': ['Buying dips', 'Bottom picking']
            },
            'ranging': {
                'strategy': 'Mean Reversion',
                'signals': ['Buy support', 'Sell resistance', 'Quick profits'],
                'avoid': ['Breakout trades', 'Trend following']
            },
            'volatile': {
                'strategy': 'Reduce Risk',
                'signals': ['Smaller positions', 'Wider stops', 'Wait for calm'],
                'avoid': ['Large positions', 'Tight stops']
            },
            'calm': {
                'strategy': 'Normal Trading',
                'signals': ['Standard position size', 'Normal stops'],
                'avoid': ['Over-trading']
            }
        }
        
        return recommendations.get(regime, {})


if __name__ == "__main__":
    print("🤖 Testing Regime Detector...\n")
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=200, freq='1D')
    
    # Create trending data
    trend = np.cumsum(np.random.randn(200) * 0.02 + 0.01)
    close = 100 * (1 + trend)
    
    sample_df = pd.DataFrame({
        'open': close * 0.99,
        'high': close * 1.02,
        'low': close * 0.98,
        'close': close,
        'volume': np.random.randint(100000, 500000, 200)
    }, index=dates)
    
    detector = RegimeDetector()
    regime = detector.detect_regime(sample_df)
    
    print("📊 REGIME DETECTION RESULTS:")
    print("=" * 60)
    print(f"Regime: {regime['regime'].upper()}")
    print(f"Confidence: {regime['confidence']:.1f}%")
    print(f"Description: {regime['description']}")
    print(f"ATR: {regime['atr_pct']:.2f}%")
    print(f"ADX: {regime['adx']:.1f}")
    print(f"Trend: {regime['trend_direction'].upper()}")
    
    recommendation = detector.get_strategy_recommendation(regime['regime'])
    
    if recommendation:
        print(f"\n💡 RECOMMENDED STRATEGY: {recommendation['strategy']}")
        print(f"\n✅ DO:")
        for signal in recommendation['signals']:
            print(f"   • {signal}")
        print(f"\n❌ AVOID:")
        for avoid in recommendation['avoid']:
            print(f"   • {avoid}")

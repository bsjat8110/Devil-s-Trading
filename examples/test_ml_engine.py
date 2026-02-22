import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from ml.regime_detector import RegimeDetector
from ml.pattern_recognizer import PatternRecognizer
from ml.signal_predictor import SimpleMLPredictor

print("=" * 80)
print("TESTING AI/ML STRATEGY ENGINE")
print("=" * 80)

# Generate sample data
np.random.seed(42)
dates = pd.date_range(end=pd.Timestamp.now(), periods=500, freq='1D')

# Create trending data
trend = np.cumsum(np.random.randn(500) * 0.02 + 0.005)
close = 100 * (1 + trend)

sample_df = pd.DataFrame({
    'open': close * 0.99,
    'high': close * 1.02,
    'low': close * 0.98,
    'close': close,
    'volume': np.random.randint(100000, 500000, 500)
}, index=dates)

# 1. Market Regime Detection
print("\n" + "🤖" * 40)
print("1. MARKET REGIME DETECTION")
print("🤖" * 40 + "\n")

detector = RegimeDetector()
regime = detector.detect_regime(sample_df)

print(f"📊 Regime: {regime['regime'].upper()}")
print(f"📊 Confidence: {regime['confidence']:.1f}%")
print(f"📊 Description: {regime['description']}")
print(f"📊 ATR: {regime['atr_pct']:.2f}%")
print(f"📊 ADX: {regime['adx']:.1f}")
print(f"📊 Trend: {regime['trend_direction'].upper()}")

recommendation = detector.get_strategy_recommendation(regime['regime'])

if recommendation:
    print(f"\n💡 RECOMMENDED STRATEGY: {recommendation['strategy']}")
    print(f"\n✅ DO:")
    for signal in recommendation['signals']:
        print(f"   • {signal}")
    print(f"\n❌ AVOID:")
    for avoid in recommendation['avoid']:
        print(f"   • {avoid}")

# 2. Pattern Recognition
print("\n" + "📊" * 40)
print("2. CANDLESTICK PATTERN RECOGNITION")
print("📊" * 40 + "\n")

recognizer = PatternRecognizer()
patterns = recognizer.analyze(sample_df)
signal = recognizer.get_signal(patterns)

print(f"🎯 Signal: {signal['signal']}")
print(f"🎯 Strength: {signal['strength']}/100")
print(f"\n📈 Patterns Detected:")
if signal['patterns']:
    for pattern in signal['patterns']:
        print(f"   ✅ {pattern.replace('_', ' ').title()}")
else:
    print("   No patterns detected")

# 3. ML Prediction
print("\n" + "🧠" * 40)
print("3. MACHINE LEARNING PREDICTION")
print("🧠" * 40 + "\n")

predictor = SimpleMLPredictor()

print("Training model...")
predictor.train(sample_df)

prediction = predictor.predict(sample_df)

print(f"\n🤖 ML Signal: {prediction['signal']}")
print(f"🤖 Confidence: {prediction['confidence']:.1f}%")
print(f"\n📊 Probabilities:")
print(f"   Buy:  {prediction['probabilities']['buy']*100:.1f}%")
print(f"   Sell: {prediction['probabilities']['sell']*100:.1f}%")
print(f"   Hold: {prediction['probabilities']['hold']*100:.1f}%")

# Combined Analysis
print("\n" + "🎯" * 40)
print("4. COMBINED SIGNAL ANALYSIS")
print("🎯" * 40 + "\n")

signals = {
    'Regime': regime['regime'],
    'Pattern': signal['signal'],
    'ML': prediction['signal']
}

print("📊 Individual Signals:")
for source, sig in signals.items():
    emoji = "🟢" if sig in ['trending_up', 'BUY'] else "🔴" if sig in ['trending_down', 'SELL'] else "⚪"
    print(f"   {emoji} {source:10s}: {sig}")

# Consensus
buy_count = sum(1 for s in signals.values() if s in ['trending_up', 'BUY'])
sell_count = sum(1 for s in signals.values() if s in ['trending_down', 'SELL'])

if buy_count > sell_count:
    consensus = "🟢 BULLISH CONSENSUS"
    confidence = buy_count / len(signals) * 100
elif sell_count > buy_count:
    consensus = "🔴 BEARISH CONSENSUS"
    confidence = sell_count / len(signals) * 100
else:
    consensus = "⚪ NEUTRAL - NO CONSENSUS"
    confidence = 50

print(f"\n💡 FINAL SIGNAL: {consensus}")
print(f"💡 Confidence: {confidence:.0f}%")

print("\n" + "✅" * 40)
print("ALL ML TESTS COMPLETED!")
print("✅" * 40)

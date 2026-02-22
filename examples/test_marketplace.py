import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from strategies.marketplace import StrategyMarketplace

print("=" * 80)
print("TESTING STRATEGY MARKETPLACE")
print("=" * 80)

# Generate sample data
np.random.seed(42)
dates = pd.date_range(end=pd.Timestamp.now(), periods=200, freq='1D')

trend = np.cumsum(np.random.randn(200) * 0.01 + 0.002)
close = 23000 * (1 + trend)

sample_df = pd.DataFrame({
    'open': close * 0.99,
    'high': close * 1.02,
    'low': close * 0.98,
    'close': close,
    'volume': np.random.randint(100000, 500000, 200)
}, index=dates)

current_price = float(sample_df['close'].iloc[-1])

marketplace = StrategyMarketplace()

print(f"\n📊 Current Price: ₹{current_price:.2f}")
print(f"📊 Analyzing with {len(marketplace.strategies)} strategies...")

# Get all signals
print("\n" + "🎯" * 40)
print("INDIVIDUAL STRATEGY SIGNALS")
print("🎯" * 40 + "\n")

signals = marketplace.get_all_signals(sample_df)

for name, signal in signals.items():
    emoji = "🟢" if signal['signal'] == 'BUY' else "🔴" if signal['signal'] == 'SELL' else "⚪"
    
    print(f"{emoji} {name.upper().replace('_', ' ')}")
    print(f"   Signal: {signal['signal']}")
    print(f"   Strength: {signal['strength']:.1f}/100")
    print(f"   Reason: {signal['reason']}")
    print(f"   Entry: ₹{signal['entry_price']:.2f}")
    print(f"   Stop Loss: ₹{signal['stop_loss']:.2f}")
    print(f"   Target: ₹{signal['target']:.2f}")
    print()

# Get consensus
print("🏆" * 40)
print("CONSENSUS SIGNAL")
print("🏆" * 40 + "\n")

consensus = marketplace.get_consensus_signal(sample_df, current_price)

consensus_emoji = "🟢" if consensus['consensus'] == 'BUY' else "🔴" if consensus['consensus'] == 'SELL' else "⚪"

print(f"{consensus_emoji} CONSENSUS: {consensus['consensus']}")
print(f"📊 Agreement: {consensus['agreement']:.1f}%")
print(f"📊 Avg Strength: {consensus['avg_strength']:.1f}/100")
print(f"📊 Buy Signals: {consensus['buy_signals']}")
print(f"📊 Sell Signals: {consensus['sell_signals']}")
print(f"📊 Neutral Signals: {consensus['neutral_signals']}")
print(f"📊 Recommended Stop Loss: ₹{consensus['stop_loss']:.2f}")
print(f"📊 Recommended Target: ₹{consensus['target']:.2f}")

# Trading recommendation
print("\n" + "💡" * 40)
print("TRADING RECOMMENDATION")
print("💡" * 40 + "\n")

if consensus['agreement'] >= 75:
    confidence = "VERY HIGH"
elif consensus['agreement'] >= 50:
    confidence = "HIGH"
elif consensus['agreement'] >= 25:
    confidence = "MODERATE"
else:
    confidence = "LOW"

print(f"Confidence Level: {confidence}")

if consensus['consensus'] == 'BUY' and consensus['agreement'] >= 50:
    print("✅ RECOMMENDATION: ENTER LONG POSITION")
    print(f"   Entry: ₹{current_price:.2f}")
    print(f"   Stop Loss: ₹{consensus['stop_loss']:.2f} (-{((current_price - consensus['stop_loss']) / current_price * 100):.2f}%)")
    print(f"   Target: ₹{consensus['target']:.2f} (+{((consensus['target'] - current_price) / current_price * 100):.2f}%)")
    
elif consensus['consensus'] == 'SELL' and consensus['agreement'] >= 50:
    print("✅ RECOMMENDATION: ENTER SHORT POSITION")
    print(f"   Entry: ₹{current_price:.2f}")
    print(f"   Stop Loss: ₹{consensus['stop_loss']:.2f} (+{((consensus['stop_loss'] - current_price) / current_price * 100):.2f}%)")
    print(f"   Target: ₹{consensus['target']:.2f} (-{((current_price - consensus['target']) / current_price * 100):.2f}%)")
    
else:
    print("⚪ RECOMMENDATION: STAY OUT / WAIT FOR BETTER SETUP")
    print(f"   Reason: Low agreement ({consensus['agreement']:.1f}%) or neutral signals")

print("\n" + "✅" * 40)
print("STRATEGY MARKETPLACE TEST COMPLETED!")
print("✅" * 40)

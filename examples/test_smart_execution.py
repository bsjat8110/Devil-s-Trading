import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from execution.smart_executor import SmartExecutor
from execution.slippage_optimizer import SlippageOptimizer

print("=" * 80)
print("TESTING SMART ORDER EXECUTION")
print("=" * 80)

executor = SmartExecutor()

# 1. Market Order
print("\n" + "⚡" * 40)
print("1. MARKET ORDER EXECUTION")
print("⚡" * 40 + "\n")

result = executor.execute_market('NIFTY', 50, 'BUY', 23450)
print(f"Strategy: {result.strategy.value.upper()}")
print(f"Quantity: {result.filled_quantity}")
print(f"Avg Price: ₹{result.avg_execution_price:.2f}")
print(f"Slippage: ₹{result.total_slippage:.2f}")
print(f"Execution Time: {result.execution_time:.3f}s")

# 2. TWAP Order
print("\n" + "⏱️" * 40)
print("2. TWAP EXECUTION (Time-Weighted)")
print("⏱️" * 40 + "\n")

result = executor.execute_twap('NIFTY', 100, 'BUY', 23450, duration_minutes=30, num_slices=10)
print(f"Strategy: {result.strategy.value.upper()}")
print(f"Quantity: {result.filled_quantity}")
print(f"Avg Price: ₹{result.avg_execution_price:.2f}")
print(f"Slippage: ₹{result.total_slippage:.2f}")
print(f"Number of Slices: {len(result.slices)}")
print(f"\n📊 Slice Details:")
for slice_info in result.slices[:3]:
    print(f"   Slice {slice_info['slice_num']}: {slice_info['quantity']} @ ₹{slice_info['price']:.2f}")

# 3. VWAP Order
print("\n" + "📊" * 40)
print("3. VWAP EXECUTION (Volume-Weighted)")
print("📊" * 40 + "\n")

# Sample volume data
sample_volume = pd.DataFrame({
    'volume': np.random.randint(100000, 500000, 10)
})

result = executor.execute_vwap('NIFTY', 100, 'BUY', 23450, sample_volume, num_slices=8)
print(f"Strategy: {result.strategy.value.upper()}")
print(f"Quantity: {result.filled_quantity}")
print(f"Avg Price: ₹{result.avg_execution_price:.2f}")
print(f"Slippage: ₹{result.total_slippage:.2f}")
print(f"\n📊 Slice Details:")
for slice_info in result.slices[:3]:
    print(f"   Slice {slice_info['slice_num']}: {slice_info['quantity']} @ ₹{slice_info['price']:.2f} (Vol%: {slice_info.get('volume_pct', 0):.1f}%)")

# 4. Iceberg Order
print("\n" + "🧊" * 40)
print("4. ICEBERG EXECUTION (Hidden Size)")
print("🧊" * 40 + "\n")

result = executor.execute_iceberg('NIFTY', 200, 'BUY', 23450, visible_quantity=40, num_slices=5)
print(f"Strategy: {result.strategy.value.upper()}")
print(f"Total Quantity: {result.total_quantity}")
print(f"Filled: {result.filled_quantity}")
print(f"Avg Price: ₹{result.avg_execution_price:.2f}")
print(f"Slippage: ₹{result.total_slippage:.2f}")
print(f"\n🔒 Hidden Execution:")
for slice_info in result.slices:
    print(f"   Slice {slice_info['slice_num']}: {slice_info['quantity']} (visible: {slice_info['visible_quantity']}) @ ₹{slice_info['price']:.2f}")

# 5. Slippage Optimization
print("\n" + "🎯" * 40)
print("5. SLIPPAGE OPTIMIZATION")
print("🎯" * 40 + "\n")

optimizer = SlippageOptimizer()

scenarios = [
    ('Small Order', 50, 1000000, 1.5, 'normal'),
    ('Medium Order', 500, 1000000, 2.0, 'normal'),
    ('Large Order', 5000, 1000000, 1.8, 'low'),
    ('Urgent Order', 2000, 1000000, 2.5, 'high'),
]

for name, size, volume, volatility, urgency in scenarios:
    print(f"\n📌 {name}:")
    print(f"   Size: {size} | Volume: {volume:,} | Volatility: {volatility}% | Urgency: {urgency}")
    
    recommendation = optimizer.recommend_execution_strategy(size, volume, volatility, urgency)
    
    print(f"   💡 Strategy: {recommendation['recommended_strategy']}")
    print(f"   📊 Impact: {recommendation['estimated_impact_pct']:.4f}%")
    print(f"   📈 Size/Volume: {recommendation['size_vs_volume_pct']:.2f}%")

# Summary
print("\n" + "📊" * 40)
print("6. EXECUTION SUMMARY")
print("📊" * 40 + "\n")

summary = executor.get_execution_summary()

print(f"Total Executions: {summary['total_executions']}")
print(f"Total Quantity: {summary['total_quantity']}")
print(f"Total Slippage: ₹{summary['total_slippage']:.2f}")
print(f"Avg Slippage/Order: ₹{summary['avg_slippage_per_order']:.2f}")
print(f"\n📈 Strategy Breakdown:")
for strategy, count in summary['strategy_breakdown'].items():
    print(f"   {strategy.upper()}: {count} orders")

print("\n" + "✅" * 40)
print("SMART EXECUTION TESTS COMPLETED!")
print("✅" * 40)

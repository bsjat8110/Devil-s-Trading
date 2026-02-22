import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from analytics.monte_carlo import StrategyMonteCarloSimulator
from analytics.strategy_tester import StrategyComparison
from analytics.time_analysis import TimeOfDayAnalyzer

print("=" * 80)
print("TESTING ADVANCED ANALYTICS")
print("=" * 80)

# Generate sample data
np.random.seed(42)

# Sample trade history
trade_history = pd.DataFrame({
    'pnl': np.random.randn(150) * 1000 + 200,
    'return_pct': np.random.randn(150) * 2 + 0.5,
    'timestamp': pd.date_range(end=pd.Timestamp.now(), periods=150, freq='1H')
})

# 1. Monte Carlo Simulation
print("\n" + "🎲" * 40)
print("1. MONTE CARLO SIMULATION")
print("🎲" * 40)

simulator = StrategyMonteCarloSimulator(trade_history)
results = simulator.run_simulation(num_simulations=5000, num_trades=252, initial_capital=100000)
print(simulator.generate_report(results))

# 2. Strategy Comparison
print("\n" + "📊" * 40)
print("2. STRATEGY A/B TESTING")
print("📊" * 40)

strategy1 = pd.DataFrame({
    'pnl': np.random.randn(100) * 1000 + 300,
    'return_pct': np.random.randn(100) * 2 + 0.8,
    'timestamp': pd.date_range(end=pd.Timestamp.now(), periods=100)
})

strategy2 = pd.DataFrame({
    'pnl': np.random.randn(80) * 800 + 200,
    'return_pct': np.random.randn(80) * 1.5 + 0.5,
    'timestamp': pd.date_range(end=pd.Timestamp.now(), periods=80)
})

comparison = StrategyComparison()
comparison.add_strategy("EMA Crossover", strategy1)
comparison.add_strategy("RSI Reversal", strategy2)

print(comparison.generate_comparison_report())

test_result = comparison.run_statistical_test("EMA Crossover", "RSI Reversal")
print(f"\n🧪 Statistical Test: {test_result['better_strategy']} is better (p={test_result['p_value']:.4f})")

# 3. Time-of-Day Analysis
print("\n" + "⏰" * 40)
print("3. TIME-OF-DAY ANALYSIS")
print("⏰" * 40)

time_analyzer = TimeOfDayAnalyzer(trade_history)
print(time_analyzer.generate_report())

print("\n" + "✅" * 40)
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("✅" * 40)

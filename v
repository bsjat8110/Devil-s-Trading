"""
Test Advanced Analytics Features
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analytics.monte_carlo import MonteCarloSimulator, StrategyMonteCarloSimulator
from analytics.strategy_tester import StrategyComparison
from analytics.time_analysis import TimeOfDayAnalyzer


def generate_sample_trades(num_trades=100, strategy_name="Test Strategy"):
    """Generate sample trade data for testing"""
    np.random.seed(42)
    
    base_time = datetime.now() - timedelta(days=30)
    
    trades = []
    for i in range(num_trades):
        entry_time = base_time + timedelta(hours=i*2)
        exit_time = entry_time + timedelta(minutes=30)
        
        # Random P&L (60% win rate)
        if np.random.random() < 0.6:
            pnl = np.random.uniform(500, 2000)
        else:
            pnl = np.random.uniform(-1500, -300)
        
        trades.append({
            'entry_time': entry_time,
            'exit_time': exit_time,
            'symbol': 'NIFTY',
            'pnl': pnl,
            'strategy': strategy_name
        })
    
    return pd.DataFrame(trades)


def test_monte_carlo():
    """Test Monte Carlo simulation"""
    print("\n" + "=" * 70)
    print("TESTING MONTE CARLO SIMULATION")
    print("=" * 70)
    
    # Generate sample returns
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.02, 252))  # Daily returns
    
    # Create simulator
    mc = MonteCarloSimulator(returns, initial_capital=100000)
    
    # Run simulation
    print("\n🔄 Running 10,000 simulations...")
    mc.run_simulation(num_simulations=10000, num_days=252)
    
    # Print report
    print(mc.generate_report())
    
    # Statistics
    stats = mc.calculate_statistics()
    print(f"\n💡 Key Insight: {stats['probability_profit']:.1f}% chance of profit")
    print(f"   Expected Return: {stats['expected_return']:.2f}%")


def test_strategy_monte_carlo():
    """Test Monte Carlo with actual trades"""
    print("\n" + "=" * 70)
    print("TESTING STRATEGY MONTE CARLO")
    print("=" * 70)
    
    # Generate sample trades
    trades_df = generate_sample_trades(50)
    
    # Create simulator
    smc = StrategyMonteCarloSimulator(trades_df, initial_capital=100000)
    
    # Run simulation
    print("\n🔄 Running trade-based simulation...")
    smc.run_trade_simulation(num_simulations=5000, num_trades=100)
    
    # Print report
    print(smc.generate_report())


def test_strategy_comparison():
    """Test strategy A/B testing"""
    print("\n" + "=" * 70)
    print("TESTING STRATEGY COMPARISON")
    print("=" * 70)
    
    # Generate sample data for multiple strategies
    strategy_a = generate_sample_trades(80, "Strategy A")
    strategy_b = generate_sample_trades(80, "Strategy B")
    strategy_b['pnl'] = strategy_b['pnl'] * 1.2  # Make B slightly better
    
    strategy_c = generate_sample_trades(80, "Strategy C")
    strategy_c['pnl'] = strategy_c['pnl'] * 0.8  # Make C worse
    
    # Create comparison
    comparison = StrategyComparison()
    comparison.add_strategy("Strategy A", strategy_a)
    comparison.add_strategy("Strategy B", strategy_b)
    comparison.add_strategy("Strategy C", strategy_c)
    
    # Generate report
    print(comparison.generate_comparison_report())
    
    # Get comparison table
    print("\n📊 Comparison Table:")
    df = comparison.compare_all()
    print(df[['total_trades', 'win_rate', 'total_pnl', 'sharpe_ratio', 'profit_factor']])


def test_time_analysis():
    """Test time-of-day analysis"""
    print("\n" + "=" * 70)
    print("TESTING TIME-OF-DAY ANALYSIS")
    print("=" * 70)
    
    # Generate sample trades
    trades_df = generate_sample_trades(200)
    
    # Create analyzer
    analyzer = TimeOfDayAnalyzer(trades_df)
    
    # Generate report
    print(analyzer.generate_report())
    
    # Best times
    best_times = analyzer.find_best_trading_times()
    print(f"\n💡 Trade at {best_times['best_hour']}:00 on {best_times['best_day']}s for best results!")


def run_all_tests():
    """Run all analytics tests"""
    print("\n" + "🚀" * 35)
    print("ADVANCED ANALYTICS DASHBOARD - FULL TEST SUITE")
    print("🚀" * 35)
    
    test_monte_carlo()
    test_strategy_monte_carlo()
    test_strategy_comparison()
    test_time_analysis()
    
    print("\n" + "✅" * 35)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("✅" * 35)


if __name__ == "__main__":
    run_all_tests()

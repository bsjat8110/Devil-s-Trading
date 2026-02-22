"""
Example backtest with dummy data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backtest.backtester import Backtester
from backtest.report_generator import generate_html_report


# Generate dummy OHLC data
def generate_dummy_data(days=30):
    """Generate fake OHLC data for testing"""
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=days),
        end=datetime.now(),
        freq='5min'
    )
    
    # Filter only market hours (9:15 AM to 3:30 PM)
    dates = dates[(dates.hour >= 9) & (dates.hour < 16)]
    dates = dates[~((dates.hour == 9) & (dates.minute < 15))]
    dates = dates[~((dates.hour == 15) & (dates.minute > 30))]
    
    base_price = 150  # Start with lower price for options
    
    data = []
    for i, ts in enumerate(dates):
        # Random walk
        change = np.random.randn() * 2
        base_price += change
        base_price = max(100, min(200, base_price))  # Keep in range
        
        high = base_price + abs(np.random.randn() * 5)
        low = base_price - abs(np.random.randn() * 5)
        close = base_price + np.random.randn() * 2
        
        data.append({
            'timestamp': ts,
            'open': base_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.randint(1000, 10000)
        })
    
    return pd.DataFrame(data)


# Simple strategy example
def dummy_strategy(backtester, row):
    """
    Dummy strategy: Buy when price > MA, Sell when price < MA
    """
    # Calculate simple moving average (last 20 candles)
    idx = backtester.data[backtester.data['timestamp'] == row['timestamp']].index[0]
    
    if idx < 20:
        return
    
    recent_data = backtester.data.iloc[max(0, idx-20):idx]
    ma = recent_data['close'].mean()
    
    # Dynamic quantity based on capital
    max_quantity = int(backtester.capital / (row['close'] * 2))  # Use only 50% capital
    quantity = min(50, max(1, max_quantity))  # Between 1 and 50
    
    # Entry signal
    if row['close'] > ma and not backtester.position:
        backtester.enter_trade(row, quantity=quantity)
    
    # Exit signal
    elif row['close'] < ma and backtester.position:
        backtester.exit_trade(row, reason='MA Cross')


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING BACKTEST ENGINE")
    print("="*60 + "\n")
    
    # Generate dummy data
    print("1️⃣  Generating dummy OHLC data...")
    data = generate_dummy_data(days=30)
    print(f"   Generated {len(data)} candles\n")
    
    # Initialize backtester
    print("2️⃣  Initializing backtester...")
    bt = Backtester(
        data=data,
        initial_capital=100000,
        commission=20,
        slippage=0.1
    )
    print()
    
    # Run backtest
    print("3️⃣  Running backtest with dummy strategy...")
    results = bt.run(dummy_strategy)
    print()
    
    # Display results
    print("4️⃣  Results:")
    print("─" * 60)
    print(f"Initial Capital:  ₹{results['initial_capital']:,.0f}")
    print(f"Final Capital:    ₹{results['final_capital']:,.0f}")
    print(f"Total P&L:        ₹{results['total_pnl']:+,.2f}")
    print(f"Total Trades:     {results['total_trades']}")
    print(f"Win Rate:         {results['win_rate']:.1f}%")
    print(f"Max Drawdown:     ₹{results['max_drawdown']:,.0f} ({results['max_drawdown_pct']:.1f}%)")
    print(f"Sharpe Ratio:     {results['sharpe_ratio']:.2f}")
    print("─" * 60)
    print()
    
    # Generate HTML report
    print("5️⃣  Generating HTML report...")
    generate_html_report(results, output_file='data/backtest_report.html')
    print()
    
    print("="*60)
    print("✅ BACKTEST TEST COMPLETED!")
    print("📄 Open data/backtest_report.html in your browser")
    print("="*60 + "\n")

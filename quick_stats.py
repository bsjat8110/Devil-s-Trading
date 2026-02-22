"""
Quick Trading Statistics
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from analytics.trade_database import TradeDatabase
from analytics.performance_tracker import PerformanceTracker
from datetime import datetime

print("\n" + "="*60)
print("📊 QUICK STATS")
print("="*60 + "\n")

db = TradeDatabase()

# Today's trades
today = datetime.now().strftime('%Y-%m-%d')
trades_today = db.get_trades(start_date=today, end_date=today)

print(f"📅 Today: {today}")
print(f"📈 Today's Trades: {len(trades_today)}")

# All time trades
all_trades = db.get_trades()
print(f"📊 Total Trades: {len(all_trades)}")

if not all_trades.empty:
    tracker = PerformanceTracker(all_trades)
    metrics = tracker.calculate_all()
    
    print(f"\n🎯 Overall Performance:")
    print("-" * 40)
    print(f"   Win Rate:     {metrics.get('win_rate', 0):.1f}%")
    print(f"   Total P&L:    ₹{metrics.get('net_pnl', 0):+,.2f}")
    print(f"   Total Profit: ₹{metrics.get('total_profit', 0):,.2f}")
    print(f"   Total Loss:   ₹{metrics.get('total_loss', 0):,.2f}")
    print(f"   Best Trade:   ₹{metrics.get('best_trade', 0):,.2f}")
    print(f"   Worst Trade:  ₹{metrics.get('worst_trade', 0):,.2f}")
    print("-" * 40)
    
    print(f"\n📈 Trade Breakdown:")
    print(f"   Winning: {metrics.get('winning_trades', 0)}")
    print(f"   Losing:  {metrics.get('losing_trades', 0)}")
    
else:
    print("\n⚠️  No trades found in database\n")

print("\n" + "="*60 + "\n")

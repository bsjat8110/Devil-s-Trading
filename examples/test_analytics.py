"""
Test script for the complete analytics engine
"""

import sys
from pathlib import Path
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analytics.trade_database import TradeDatabase
from analytics.performance_tracker import PerformanceTracker
from analytics.report_generator import generate_cli_report, export_to_csv

def generate_dummy_trades(db, num_trades=50):
    """Generate and log some dummy trades"""
    print(f"Generating {num_trades} dummy trades...")
    symbols = ['NIFTY_DUMMY_CE', 'BANKNIFTY_DUMMY_PE']
    
    for i in range(num_trades):
        entry_price = random.uniform(100, 200)
        pnl = random.uniform(-1500, 3000)
        exit_price = entry_price + (pnl / 50)
        
        trade = {
            'symbol': random.choice(symbols),
            'strategy': 'DummyStrategy',
            'entry_time': datetime.now() - timedelta(days=random.randint(1, 30)),
            'exit_time': datetime.now(),
            'action': 'BUY',
            'quantity': 50,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_percent': (pnl / (entry_price * 50)) * 100,
            'exit_reason': random.choice(['Target Hit', 'Stop Loss', 'EOD'])
        }
        db.log_trade(trade)

if __name__ == "__main__":
    test_db_path = 'data/analytics_test.db'
    
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        
    db = TradeDatabase(db_path=test_db_path)
    
    generate_dummy_trades(db, num_trades=45)
    
    print("\n" + "="*50)
    print("🔥 GENERATING REPORT FROM DUMMY DATA 🔥")
    print("="*50 + "\n")
    
    trades = db.get_trades()
    
    tracker = PerformanceTracker(trades)
    metrics = tracker.calculate_all()
    
    generate_cli_report(metrics)
    
    export_to_csv(trades, file_path='data/dummy_trades_report.csv')
    
    del db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        
    print("\n✅ Analytics test completed successfully!\n")

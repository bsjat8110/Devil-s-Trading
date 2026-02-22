"""
Real-time Trading Monitor
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from analytics.trade_database import TradeDatabase
from datetime import datetime
import time
import os

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def show_dashboard():
    db = TradeDatabase()
    
    while True:
        clear_screen()
        
        print("="*70)
        print("📊 DEVIL TRADING AGENT - LIVE MONITOR")
        print("="*70)
        print(f"🕐 {datetime.now().strftime('%d %b %Y, %I:%M:%S %p')}")
        print("="*70)
        
        # Today's trades
        today = datetime.now().strftime('%Y-%m-%d')
        trades_today = db.get_trades(start_date=today, end_date=today)
        
        print(f"\n📅 TODAY'S PERFORMANCE:")
        print("-"*70)
        
        if not trades_today.empty:
            total_pnl = trades_today['pnl'].sum()
            winning = len(trades_today[trades_today['pnl'] > 0])
            losing = len(trades_today[trades_today['pnl'] < 0])
            
            print(f"   Total Trades: {len(trades_today)}")
            print(f"   Winning: {winning} | Losing: {losing}")
            print(f"   Total P&L: ₹{total_pnl:+,.2f}")
            
            if len(trades_today) > 0:
                print(f"\n📈 Recent Trades:")
                for _, trade in trades_today.tail(3).iterrows():
                    status_icon = "✅" if trade['pnl'] > 0 else "❌"
                    print(f"   {status_icon} {trade['symbol']}: ₹{trade['pnl']:+.2f}")
        else:
            print("   No trades today")
        
        print("\n" + "="*70)
        print("Press CTRL+C to exit")
        
        time.sleep(5)  # Refresh every 5 seconds

if __name__ == "__main__":
    try:
        show_dashboard()
    except KeyboardInterrupt:
        print("\n\n✅ Monitor stopped\n")

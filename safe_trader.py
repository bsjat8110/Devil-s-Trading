"""
Safe Auto Trader with Risk Controls
"""

from master_system import DevilTradingMasterSystem
import schedule
import time
from datetime import datetime, time as dt_time

# Configuration
MAX_DAILY_LOSS = 5000  # Max loss per day
MAX_POSITIONS = 3       # Max concurrent positions
TRADING_START = dt_time(9, 20)
TRADING_END = dt_time(15, 20)

system = DevilTradingMasterSystem(500000)
system.portfolio.add_strategy("EMA Crossover", 30)

daily_pnl = 0
daily_trades = 0


def is_trading_hours():
    """Check if within trading hours"""
    now = datetime.now().time()
    return TRADING_START <= now <= TRADING_END


def can_trade():
    """Check if we can trade (risk controls)"""
    
    # Check trading hours
    if not is_trading_hours():
        print("⏰ Outside trading hours")
        return False
    
    # Check daily loss limit
    summary = system.portfolio.get_portfolio_summary()
    if summary['total_pnl'] < -MAX_DAILY_LOSS:
        print(f"🛑 Daily loss limit hit: ₹{summary['total_pnl']:.2f}")
        return False
    
    # Check max positions
    if summary['active_positions'] >= MAX_POSITIONS:
        print(f"🛑 Max positions reached: {summary['active_positions']}")
        return False
    
    return True


def trade():
    """Safe trading with risk controls"""
    
    if not can_trade():
        return
    
    print(f"\n{'='*80}")
    print(f"🤖 TRADING - {datetime.now()}")
    print(f"{'='*80}\n")
    
    try:
        analysis = system.analyze_market('NIFTY')
        consensus = analysis['strategy_consensus']
        
        if consensus['agreement'] > 75 and consensus['consensus'] == 'BUY':
            print("✅ Trading signal detected")
            # Your trading logic here
        
        # Check SL/Targets
        to_close = system.portfolio.check_stop_loss_targets()
        for position_id, price, reason in to_close:
            system.portfolio.close_position(position_id, price, reason)
            print(f"🎯 {reason} hit")
            
    except Exception as e:
        print(f"❌ Error: {e}")


# Schedule
schedule.every(15).minutes.do(trade)

print("🤖 SAFE AUTO TRADER STARTED")

while True:
    schedule.run_pending()
    time.sleep(1)

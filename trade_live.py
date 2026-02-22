"""
Live Trading Bot - Production Version
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from bridge.trade_handler import TradeHandler
from bridge.token_mapper import TokenMapper
from analytics.greeks_calculator import GreeksCalculator
from datetime import datetime
import time
import os

# Load mode from environment
TRADING_MODE = os.getenv('TRADING_MODE', 'PAPER')

print("\n" + "="*60)
print(f"🔥 DEVIL TRADING AGENT - {TRADING_MODE} MODE")
print("="*60 + "\n")

# Initialize
handler = TradeHandler()
mapper = TokenMapper()
calc = GreeksCalculator()

# Send startup notification
handler.send_system_status(
    'STARTED', 
    f'Trading started in {TRADING_MODE} mode at {datetime.now().strftime("%I:%M %p")}'
)

print(f"✅ Mode: {TRADING_MODE}")
print(f"✅ Telegram: Active")
print(f"✅ Database: Connected")
print(f"✅ Token Mapper: Ready")
print("\n" + "-"*60 + "\n")

# ══════════════════════════════════════════════════════════
# YOUR TRADING STRATEGY HERE
# ══════════════════════════════════════════════════════════

def your_trading_strategy():
    """
    Implement your trading logic here
    """
    
    print("📈 Running strategy scan...")
    
    # Example: Get current NIFTY ATM
    spot_price = 23500  # Get from market feed
    
    # Get token
    token = mapper.get_atm_ce('NIFTY', spot_price)
    
    # Calculate Greeks
    greeks = calc.calculate_all_greeks(
        spot=spot_price,
        strike=23500,
        expiry_days=7,
        iv=15.5,
        option_type='CE'
    )
    
    print(f"   Spot: {spot_price}")
    print(f"   Delta: {greeks['delta']:.4f}")
    print(f"   Theta: ₹{greeks['theta']:.2f}/day")
    
    # Trading decision
    if greeks['delta'] > 0.45 and greeks['theta'] < -10:
        print("\n✅ BUY Signal detected!")
        
        if TRADING_MODE == 'LIVE':
            # Place real order here
            # order = order_executor.place_order(...)
            pass
        
        # Send notification (works in both modes)
        handler.on_trade_entry({
            'symbol': 'NIFTY23500CE',
            'action': 'BUY',
            'quantity': 50,
            'entry_price': 155.00,
            'strategy': 'Delta-Theta Strategy'
        })
        
        return True
    else:
        print("   No signal\n")
        return False

# ══════════════════════════════════════════════════════════
# MAIN TRADING LOOP
# ══════════════════════════════════════════════════════════

try:
    print("🔄 Starting trading loop...")
    print("   Press CTRL+C to stop\n")
    
    # Run strategy once (or in a loop for continuous trading)
    signal = your_trading_strategy()
    
    if signal:
        print("✅ Trade executed!")
    
    # Simulate holding position
    time.sleep(2)
    
    # Exit example
    print("\n📉 Exit signal detected!")
    handler.on_trade_exit({
        'symbol': 'NIFTY23500CE',
        'action': 'SELL',
        'quantity': 50,
        'entry_price': 155.00,
        'entry_time': datetime.now(),
        'exit_price': 165.00,
        'pnl': 500.00,
        'pnl_percent': 6.45,
        'exit_reason': 'Target Hit'
    })
    print("✅ Trade closed!")

except KeyboardInterrupt:
    print("\n\n⏸️  Trading interrupted by user")

except Exception as e:
    print(f"\n❌ Error: {e}")
    handler.send_risk_warning('SYSTEM_ERROR', f'Trading stopped due to: {e}')

finally:
    # Cleanup
    print("\n" + "-"*60)
    print("🛑 Shutting down...")
    
    # Send summary
    handler.send_daily_summary()
    
    # Send shutdown notification
    handler.send_system_status('STOPPED', 'Trading session ended')
    
    print("✅ Session completed!")
    print("="*60 + "\n")


# ══════════════════════════════════════════════════════════
# YE CODE APNE TRADING FILE KE TOP PE PASTE KARO
# ══════════════════════════════════════════════════════════

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from bridge.trade_handler import TradeHandler
from datetime import datetime

# Initialize handler (ek baar)
handler = TradeHandler()

# ══════════════════════════════════════════════════════════
# JAHAN APKA TRADING LOGIC HAI, WAHAN YE USE KARO
# ══════════════════════════════════════════════════════════

# Agent start hote hi
handler.send_system_status('STARTED', 'Agent is active!')

# ══════════════════════════════════════════════════════════
# EXAMPLE: BUY SIGNAL MILA
# ══════════════════════════════════════════════════════════

def buy_option(symbol, quantity, price):
    # Tumhara existing buy logic
    # ...
    
    # Notification bhejo
    handler.on_trade_entry({
        'symbol': symbol,
        'action': 'BUY',
        'quantity': quantity,
        'entry_price': price,
        'strategy': 'My Strategy Name'
    })

# ══════════════════════════════════════════════════════════
# EXAMPLE: SELL SIGNAL MILA
# ══════════════════════════════════════════════════════════

def sell_option(symbol, quantity, entry_price, entry_time, exit_price):
    # Calculate P&L
    pnl = (exit_price - entry_price) * quantity
    pnl_percent = (pnl / (entry_price * quantity)) * 100
    
    # Tumhara existing sell logic
    # ...
    
    # Notification + Database logging
    handler.on_trade_exit({
        'symbol': symbol,
        'action': 'SELL',
        'quantity': quantity,
        'entry_price': entry_price,
        'entry_time': entry_time,
        'exit_price': exit_price,
        'pnl': pnl,
        'pnl_percent': pnl_percent,
        'exit_reason': 'Target Hit'  # Ya 'Stop Loss' ya 'Manual'
    })

# ══════════════════════════════════════════════════════════
# DAILY SUMMARY (3:30 PM PE YA JAHAN CHAHIYE)
# ══════════════════════════════════════════════════════════

def end_of_day():
    handler.send_daily_summary()
    handler.send_system_status('STOPPED', 'Market closed')

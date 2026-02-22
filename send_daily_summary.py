"""
Send Daily Summary at 3:30 PM
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from bridge.trade_handler import TradeHandler
from datetime import datetime

print(f"\n📊 Generating Daily Summary - {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n")

handler = TradeHandler()
handler.send_daily_summary()

print("✅ Daily summary sent to Telegram!")
print("📱 Check your phone!\n")

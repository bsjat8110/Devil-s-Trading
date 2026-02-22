#!/bin/bash

echo "🔥 DEVIL TRADING AGENT - STARTING..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Check if market is open (9:15 AM - 3:30 PM)
HOUR=$(date +%H)
if [ $HOUR -lt 9 ] || [ $HOUR -gt 15 ]; then
    echo "⏰ Market is closed!"
    echo "Trading hours: 9:15 AM - 3:30 PM"
    exit 1
fi

echo "✅ Market is open"
echo "✅ Virtual environment activated"
echo ""

# Send startup notification
python << 'PYEOF'
from bridge.trade_handler import TradeHandler
handler = TradeHandler()
handler.send_system_status('STARTED', 'Trading session started! 🔥')
print("📱 Startup notification sent to Telegram")
PYEOF

echo ""
echo "🚀 Starting main trading agent..."
echo ""

# Run your main agent
python my_trading_bot.py

# Send shutdown notification
python << 'PYEOF'
from bridge.trade_handler import TradeHandler
handler = TradeHandler()
handler.send_daily_summary()
handler.send_system_status('STOPPED', 'Trading session ended')
print("📱 Shutdown notification sent to Telegram")
PYEOF

echo ""
echo "✅ Trading session completed!"

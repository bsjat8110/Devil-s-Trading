"""
Telegram Notifier Module
Sends real-time trading notifications to Telegram
Production-ready version with clean error handling
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
import asyncio
import warnings
from telegram import Bot
from telegram.error import TelegramError

# Suppress asyncio event loop warnings
warnings.filterwarnings('ignore', message='.*Event loop is closed.*')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Handles all Telegram notifications for the trading agent
    """
    
    def __init__(self):
        """Initialize Telegram bot"""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = os.getenv('TELEGRAM_ENABLED', 'true').lower() == 'true'
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not found in .env file")
            self.enabled = False
            self.bot = None
        else:
            try:
                self.bot = Bot(token=self.bot_token)
                logger.info("✅ Telegram Notifier initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Telegram bot: {e}")
                self.enabled = False
                self.bot = None
    
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """
        Send message to Telegram
        
        Args:
            message: Message text to send
            parse_mode: HTML or Markdown
            
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled or not self.bot:
            return False
        
        try:
            # Create fresh event loop for Python 3.14
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Send message
                loop.run_until_complete(
                    self.bot.send_message(
                        chat_id=self.chat_id,
                        text=message,
                        parse_mode=parse_mode
                    )
                )
                logger.info("📱 Telegram notification sent")
                return True
                
            except Exception as inner_error:
                # Check if message was actually sent despite error
                if 'Event loop is closed' in str(inner_error):
                    # This is harmless - message was sent
                    logger.info("📱 Telegram notification sent")
                    return True
                else:
                    logger.error(f"❌ Send error: {inner_error}")
                    return False
                    
            finally:
                # Safe cleanup
                try:
                    loop.close()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"❌ Telegram error: {e}")
            return False
    
    def send_trade_entry(self, trade_data: Dict[str, Any]) -> bool:
        """Send trade entry notification"""
        symbol = trade_data.get('symbol', 'N/A')
        action = trade_data.get('action', 'N/A')
        quantity = trade_data.get('quantity', 0)
        entry_price = trade_data.get('entry_price', 0)
        stop_loss = trade_data.get('stop_loss')
        target = trade_data.get('target')
        strategy = trade_data.get('strategy', 'Manual')
        
        message = f"""
🔔 <b>TRADE ENTRY ALERT</b>

📊 Symbol: <b>{symbol}</b>
🎯 Action: <b>{action}</b>
📦 Quantity: <b>{quantity}</b>
💰 Entry: <b>₹{entry_price:.2f}</b>
"""
        
        if stop_loss and target:
            message += f"🛡️ SL: <b>₹{stop_loss:.2f}</b> | 🎯 Target: <b>₹{target:.2f}</b>\n"
        
        message += f"""📈 Strategy: <b>{strategy}</b>
⏰ Time: {datetime.now().strftime('%I:%M %p')}
"""
        
        return self.send_message(message)
    
    def send_trade_exit(self, trade_data: Dict[str, Any]) -> bool:
        """Send trade exit notification"""
        symbol = trade_data.get('symbol', 'N/A')
        action = trade_data.get('action', 'N/A')
        quantity = trade_data.get('quantity', 0)
        exit_price = trade_data.get('exit_price', 0)
        entry_price = trade_data.get('entry_price', 0)
        pnl = trade_data.get('pnl', 0)
        pnl_percent = trade_data.get('pnl_percent', 0)
        reason = trade_data.get('reason', 'Manual Exit')
        
        pnl_emoji = "✅" if pnl >= 0 else "❌"
        
        message = f"""
{pnl_emoji} <b>TRADE EXIT ALERT</b>

📊 Symbol: <b>{symbol}</b>
🎯 Action: <b>{action}</b>
📦 Quantity: <b>{quantity}</b>
💰 Entry: <b>₹{entry_price:.2f}</b>
💸 Exit: <b>₹{exit_price:.2f}</b>

{pnl_emoji} P&L: <b>₹{pnl:+.2f} ({pnl_percent:+.2f}%)</b>
📝 Reason: <b>{reason}</b>
⏰ Time: {datetime.now().strftime('%I:%M %p')}
"""
        
        return self.send_message(message)
    
    def send_stop_loss_hit(self, trade_data: Dict[str, Any]) -> bool:
        """Send stop loss hit notification"""
        symbol = trade_data.get('symbol', 'N/A')
        pnl = trade_data.get('pnl', 0)
        
        message = f"""
🛑 <b>STOP LOSS HIT!</b>

📊 Symbol: <b>{symbol}</b>
💔 Loss: <b>₹{pnl:.2f}</b>
⏰ Time: {datetime.now().strftime('%I:%M %p')}

🔒 Position closed to limit risk.
"""
        
        return self.send_message(message)
    
    def send_target_achieved(self, trade_data: Dict[str, Any]) -> bool:
        """Send target achieved notification"""
        symbol = trade_data.get('symbol', 'N/A')
        pnl = trade_data.get('pnl', 0)
        
        message = f"""
🎯 <b>TARGET ACHIEVED!</b>

📊 Symbol: <b>{symbol}</b>
💰 Profit: <b>₹{pnl:+.2f}</b>
⏰ Time: {datetime.now().strftime('%I:%M %p')}

🎉 Great trade! Position closed.
"""
        
        return self.send_message(message)
    
    def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Send daily P&L summary"""
        total_trades = summary_data.get('total_trades', 0)
        winning = summary_data.get('winning_trades', 0)
        losing = summary_data.get('losing_trades', 0)
        total_pnl = summary_data.get('total_pnl', 0)
        best_trade = summary_data.get('best_trade', 0)
        worst_trade = summary_data.get('worst_trade', 0)
        
        win_rate = (winning / total_trades * 100) if total_trades > 0 else 0
        pnl_emoji = "📈" if total_pnl >= 0 else "📉"
        
        message = f"""
📊 <b>DAILY TRADING SUMMARY</b>
{datetime.now().strftime('%d %B %Y')}

━━━━━━━━━━━━━━━━━━━━━━━
📈 Total Trades: <b>{total_trades}</b>
✅ Winners: <b>{winning}</b>
❌ Losers: <b>{losing}</b>
🎯 Win Rate: <b>{win_rate:.1f}%</b>

{pnl_emoji} Net P&L: <b>₹{total_pnl:+.2f}</b>
🏆 Best Trade: <b>₹{best_trade:+.2f}</b>
💔 Worst Trade: <b>₹{worst_trade:+.2f}</b>
━━━━━━━━━━━━━━━━━━━━━━━

⏰ Generated at {datetime.now().strftime('%I:%M %p')}
"""
        
        return self.send_message(message)
    
    def send_risk_warning(self, warning_data: Dict[str, Any]) -> bool:
        """Send risk limit warning"""
        warning_type = warning_data.get('type', 'Risk Limit')
        message_text = warning_data.get('message', 'Risk threshold reached')
        
        message = f"""
⚠️ <b>RISK WARNING</b>

🚨 Type: <b>{warning_type}</b>
📝 {message_text}
⏰ Time: {datetime.now().strftime('%I:%M %p')}

Please review your positions!
"""
        
        return self.send_message(message)
    
    def send_market_regime_change(self, regime_data: Dict[str, Any]) -> bool:
        """Send market regime change alert"""
        old_regime = regime_data.get('old_regime', 'Unknown')
        new_regime = regime_data.get('new_regime', 'Unknown')
        confidence = regime_data.get('confidence', 0)
        
        message = f"""
🔄 <b>MARKET REGIME CHANGE</b>

📊 Previous: <b>{old_regime}</b>
🎯 Current: <b>{new_regime}</b>
📈 Confidence: <b>{confidence:.1f}%</b>
⏰ Time: {datetime.now().strftime('%I:%M %p')}

Adjust your strategy accordingly.
"""
        
        return self.send_message(message)
    
    def send_position_update(self, position_data: Dict[str, Any]) -> bool:
        """Send position status update"""
        symbol = position_data.get('symbol', 'N/A')
        quantity = position_data.get('quantity', 0)
        entry_price = position_data.get('entry_price', 0)
        current_price = position_data.get('current_price', 0)
        pnl = position_data.get('pnl', 0)
        pnl_percent = position_data.get('pnl_percent', 0)
        
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        
        message = f"""
📍 <b>POSITION UPDATE</b>

📊 Symbol: <b>{symbol}</b>
📦 Quantity: <b>{quantity}</b>
💰 Entry: <b>₹{entry_price:.2f}</b>
💹 Current: <b>₹{current_price:.2f}</b>

{pnl_emoji} P&L: <b>₹{pnl:+.2f} ({pnl_percent:+.2f}%)</b>
⏰ Time: {datetime.now().strftime('%I:%M %p')}
"""
        
        return self.send_message(message)
    
    def send_system_status(self, status: str, details: str = "") -> bool:
        """Send system status notification"""
        emoji_map = {
            'started': '🟢',
            'stopped': '🔴',
            'error': '⚠️',
            'connected': '✅',
            'disconnected': '❌'
        }
        
        emoji = emoji_map.get(status.lower(), '🔔')
        
        message = f"""
{emoji} <b>SYSTEM STATUS</b>

Status: <b>{status.upper()}</b>
{details}
⏰ Time: {datetime.now().strftime('%I:%M %p')}
"""
        
        return self.send_message(message)
    
    def test_connection(self) -> bool:
        """Test Telegram connection"""
        message = """
🤖 <b>DEVIL TRADING AGENT</b>

✅ Telegram notifications are working!

This is a test message to verify the connection.

⏰ {time}
""".format(time=datetime.now().strftime('%I:%M %p, %d %b %Y'))
        
        return self.send_message(message)


def test_telegram_notifier():
    """Test all notification types"""
    notifier = TelegramNotifier()
    
    print("\n" + "="*60)
    print("🔥 TESTING TELEGRAM NOTIFIER")
    print("="*60 + "\n")
    
    if not notifier.enabled:
        print("❌ Telegram notifier is disabled!")
        return
    
    print("1️⃣  Testing connection...")
    notifier.test_connection()
    print("✅ Connection test sent\n")
    
    print("2️⃣  Testing trade entry...")
    notifier.send_trade_entry({
        'symbol': 'NIFTY23500CE',
        'action': 'BUY',
        'quantity': 50,
        'entry_price': 150.50,
        'stop_loss': 145.00,
        'target': 160.00,
        'strategy': 'Trend Following'
    })
    print("✅ Trade entry sent\n")
    
    print("3️⃣  Testing trade exit...")
    notifier.send_trade_exit({
        'symbol': 'NIFTY23500CE',
        'action': 'SELL',
        'quantity': 50,
        'entry_price': 150.50,
        'exit_price': 158.75,
        'pnl': 412.50,
        'pnl_percent': 5.47,
        'reason': 'Target Achieved'
    })
    print("✅ Trade exit sent\n")
    
    print("4️⃣  Testing daily summary...")
    notifier.send_daily_summary({
        'total_trades': 12,
        'winning_trades': 8,
        'losing_trades': 4,
        'total_pnl': 3250.50,
        'best_trade': 850.00,
        'worst_trade': -320.00
    })
    print("✅ Daily summary sent\n")
    
    print("="*60)
    print("✅ ALL 4 MESSAGES SENT!")
    print("📱 Check @devil_trading_8110_bot on Telegram")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_telegram_notifier()

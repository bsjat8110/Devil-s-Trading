"""
Trade Handler - Central Integration
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bridge.telegram_notifier import TelegramNotifier
from analytics.trade_database import TradeDatabase
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeHandler:
    def get_mtf_signals(self, symbol: str) -> Dict:
    """
    Get multi-timeframe analysis before placing trade
    """
    try:
        from analytics.mtf_analyzer import MultiTimeframeAnalyzer
        
        analyzer = MultiTimeframeAnalyzer(symbol)
        analyzer.analyze_all_timeframes()
        analyzer.find_confluence_zones()
        
        bias = analyzer.get_trading_bias()
        
        return {
            'bias': bias['bias'],
            'confidence': bias['confidence'],
            'signals': analyzer.signals,
            'confluence_zones': analyzer.confluence_zones
        }
    except Exception as e:
        logger.error(f"Error getting MTF signals: {e}")
        return {'bias': 'neutral', 'confidence': 0}
    
    def on_trade_entry(self, trade_data: dict):
        self.telegram.send_trade_entry(trade_data)
        logger.info(f"📱 Entry notification sent for {trade_data['symbol']}")
    
    def on_trade_exit(self, trade_data: dict):
        self.telegram.send_trade_exit(trade_data)
        db_data = {
            'symbol': trade_data.get('symbol'),
            'strategy': trade_data.get('strategy', 'Default'),
            'entry_time': trade_data.get('entry_time', datetime.now()),
            'exit_time': datetime.now(),
            'action': trade_data.get('action', 'BUY'),
            'quantity': trade_data.get('quantity'),
            'entry_price': trade_data.get('entry_price'),
            'exit_price': trade_data.get('exit_price'),
            'pnl': trade_data.get('pnl'),
            'pnl_percent': trade_data.get('pnl_percent'),
            'exit_reason': trade_data.get('exit_reason', 'Manual')
        }
        self.db.log_trade(db_data)
        logger.info(f"📱 Exit notification sent for {trade_data['symbol']}")
    
    def send_daily_summary(self):
        today = datetime.now().strftime('%Y-%m-%d')
        trades = self.db.get_trades(start_date=today, end_date=today)
        if trades.empty:
            self.telegram.send_message("📊 No trades today!")
            return
        from analytics.performance_tracker import PerformanceTracker
        tracker = PerformanceTracker(trades)
        metrics = tracker.calculate_all()
        self.telegram.send_daily_summary({
            'total_trades': metrics.get('total_trades', 0),
            'winning_trades': metrics.get('winning_trades', 0),
            'losing_trades': metrics.get('losing_trades', 0),
            'total_pnl': metrics.get('total_pnl', 0),
            'best_trade': metrics.get('best_trade', 0),
            'worst_trade': metrics.get('worst_trade', 0)
        })
    
    def send_system_status(self, status: str, details: str = ""):
        self.telegram.send_system_status(status, details)

if __name__ == "__main__":
    print("\n🧪 TESTING TRADE HANDLER\n")
    handler = TradeHandler()
    
    print("1️⃣  Entry notification...")
    handler.on_trade_entry({
        'symbol': 'NIFTY_TEST_CE',
        'action': 'BUY',
        'quantity': 50,
        'entry_price': 150.50,
        'strategy': 'Test'
    })
    print("✅ Entry sent!\n")
    
    print("2️⃣  Exit notification...")
    handler.on_trade_exit({
        'symbol': 'NIFTY_TEST_CE',
        'action': 'SELL',
        'quantity': 50,
        'entry_price': 150.50,
        'entry_time': datetime.now(),
        'exit_price': 160.00,
        'pnl': 475.00,
        'pnl_percent': 6.3,
        'exit_reason': 'Target'
    })
    print("✅ Exit sent!\n")
    
    print("3️⃣  System status...")
    handler.send_system_status('STARTED', 'Working!')
    print("✅ Status sent!\n")
    
    print("📱 CHECK YOUR TELEGRAM!\n")

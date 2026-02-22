#!/usr/bin/env python3
"""
DEVIL TRADING AGENT - COMMAND CENTER
Main control interface for the trading agent
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bridge.auth_manager import AngelAuthManager
from bridge.market_feed import MarketFeedListener
from bridge.order_executor import OrderExecutor
from bridge.position_manager import PositionManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/agent_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DevilCommandCenter:
    """Main command center for Devil Trading Agent"""
    
    def __init__(self):
        """Initialize command center"""
        self.mode = os.getenv('TRADING_MODE', 'PAPER').upper()
        self.auth = AngelAuthManager()
        self.feed = None
        self.executor = None
        self.position_manager = None
        
        self.print_banner()
    
    def print_banner(self):
        """Print welcome banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║           🔥 DEVIL TRADING AGENT - COMMAND CENTER 🔥              ║
║                                                                   ║
║              Professional AI-Powered Trading System               ║
║                      Angel One Integration                        ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        print(f"📊 Mode: {self.mode}")
        print(f"🔐 Client: {os.getenv('CLIENT_ID')}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 70 + "\n")
    
    def test_authentication(self):
        """Test all API authentications"""
        print("\n" + "="*70)
        print("🔐 AUTHENTICATION TEST")
        print("="*70 + "\n")
        
        api_types = ['market', 'publisher', 'historical', 'trading']
        results = {}
        
        for api_type in api_types:
            print(f"Testing {api_type.upper()} API...")
            connection = self.auth.login(api_type)
            
            if connection:
                print(f"  ✅ {api_type.upper()} API: SUCCESS")
                results[api_type] = True
                self.auth.logout(api_type)
            else:
                print(f"  ❌ {api_type.upper()} API: FAILED")
                results[api_type] = False
        
        print("\n" + "-"*70)
        success_count = sum(1 for v in results.values() if v)
        print(f"✅ {success_count}/{len(api_types)} APIs authenticated successfully")
        print("="*70 + "\n")
        
        return all(results.values())
    
    def test_market_feed(self, duration=30):
        """Test market feed connection"""
        print("\n" + "="*70)
        print(f"📊 MARKET FEED TEST ({duration}s)")
        print("="*70 + "\n")
        
        feed = MarketFeedListener()
        
        # NIFTY 50 token
        test_tokens = [{
            "exchangeType": 1,
            "tokens": ["99926000"]
        }]
        
        print("🔄 Starting market feed...")
        if feed.start_feed(test_tokens):
            print(f"✅ Feed started! Running for {duration} seconds...\n")
            
            import time
            try:
                time.sleep(duration)
            except KeyboardInterrupt:
                print("\n⚠️  Stopped by user")
            
            feed.stop_feed()
            print("\n✅ Market feed test completed!")
            return True
        else:
            print("❌ Market feed test failed!")
            return False
    
    def test_order_execution(self):
        """Test order execution (paper mode)"""
        print("\n" + "="*70)
        print("🚀 ORDER EXECUTION TEST (PAPER MODE)")
        print("="*70 + "\n")
        
        executor = OrderExecutor(mode='PAPER')
        
        if executor.connect():
            # Place test order
            order_id = executor.place_order(
                symbol='NIFTY23FEB23500CE',
                exchange='NFO',
                transaction_type='BUY',
                quantity=50,
                order_type='MARKET',
                price=150.00,
                stop_loss=145.00,
                target=160.00
            )
            
            if order_id:
                print(f"\n✅ Test order placed: {order_id}")
                
                # Check order status
                status = executor.get_order_status(order_id)
                print(f"\nOrder Status:")
                print(json.dumps(status, indent=2, default=str))
                
                return True
            else:
                print("❌ Order execution test failed!")
                return False
        else:
            print("❌ Executor connection failed!")
            return False
    
    def test_position_manager(self):
        """Test position management"""
        print("\n" + "="*70)
        print("📊 POSITION MANAGER TEST")
        print("="*70 + "\n")
        
        pm = PositionManager(mode='PAPER')
        
        if pm.connect():
            # Add test position
            pm.add_position(
                symbol='NIFTY23FEB23500CE',
                quantity=50,
                entry_price=150.00,
                order_type='BUY',
                stop_loss=145.00,
                target=160.00
            )
            
            # Update price
            pm.update_price('NIFTY23FEB23500CE', 155.00)
            
            # Print portfolio
            pm.print_portfolio()
            pm.print_statistics()
            
            return True
        else:
            print("❌ Position manager test failed!")
            return False
    
    def run_full_system_test(self):
        """Run complete system test"""
        print("\n" + "="*70)
        print("🧪 COMPLETE SYSTEM TEST")
        print("="*70 + "\n")
        
        tests = [
            ("Authentication", lambda: self.test_authentication()),
            ("Market Feed", lambda: self.test_market_feed(20)),
            ("Order Execution", lambda: self.test_order_execution()),
            ("Position Manager", lambda: self.test_position_manager())
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                print(f"\n{'='*70}")
                print(f"Running: {test_name}")
                print(f"{'='*70}")
                results[test_name] = test_func()
            except Exception as e:
                logger.error(f"Test failed: {test_name} - {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70 + "\n")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        success_count = sum(1 for v in results.values() if v)
        total_tests = len(results)
        
        print(f"\n{'='*70}")
        print(f"Final Score: {success_count}/{total_tests} tests passed")
        print(f"{'='*70}\n")
        
        return all(results.values())
    
    def show_status(self):
        """Show current system status"""
        print("\n" + "="*70)
        print("📊 SYSTEM STATUS")
        print("="*70 + "\n")
        
        print(f"Trading Mode: {self.mode}")
        print(f"Client ID: {os.getenv('CLIENT_ID')}")
        print(f"Risk per Trade: {os.getenv('RISK_PER_TRADE')}%")
        print(f"Max Daily Loss: {os.getenv('MAX_DAILY_LOSS')}%")
        print(f"Max Positions: {os.getenv('MAX_POSITIONS')}")
        
        print("\n" + "-"*70)
        print("API STATUS:")
        print("-"*70)
        
        api_keys = {
            'Market Feed': os.getenv('MARKET_API_KEY'),
            'Publisher': os.getenv('PUBLISHER_API_KEY'),
            'Historical': os.getenv('HISTORICAL_API_KEY'),
            'Trading': os.getenv('TRADING_API_KEY')
        }
        
        for name, key in api_keys.items():
            status = "✅ Configured" if key else "❌ Missing"
            masked_key = key[:4] + "****" if key else "None"
            print(f"{status} - {name}: {masked_key}")
        
        print("\n" + "="*70 + "\n")
    
    def show_help(self):
        """Show available commands"""
        help_text = """
╔═══════════════════════════════════════════════════════════════════╗
║                    AVAILABLE COMMANDS                             ║
╚═══════════════════════════════════════════════════════════════════╝

📊 SYSTEM COMMANDS:
  --status              Show system status and configuration
  --test-auth           Test all API authentications
  --test-feed           Test market feed connection (30s)
  --test-order          Test order execution (paper mode)
  --test-position       Test position management
  --test-all            Run complete system test

🔧 CONFIGURATION:
  --set-mode <MODE>     Set trading mode (PAPER/LIVE)
  --show-config         Show current configuration

📈 TRADING:
  --start               Start trading agent
  --stop                Stop trading agent
  
ℹ️  INFORMATION:
  --help                Show this help message
  --version             Show version information

═══════════════════════════════════════════════════════════════════

Examples:
  python run_agent.py --status
  python run_agent.py --test-all
  python run_agent.py --start

⚠️  WARNING: Always test in PAPER mode before going LIVE!

═══════════════════════════════════════════════════════════════════
        """
        print(help_text)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Devil Trading Agent - Command Center',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--test-auth', action='store_true', help='Test authentication')
    parser.add_argument('--test-feed', action='store_true', help='Test market feed')
    parser.add_argument('--test-order', action='store_true', help='Test order execution')
    parser.add_argument('--test-position', action='store_true', help='Test position manager')
    parser.add_argument('--test-all', action='store_true', help='Run all tests')
    parser.add_argument('--help-commands', action='store_true', help='Show detailed help')
    
    args = parser.parse_args()
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    cc = DevilCommandCenter()
    
    if args.status:
        cc.show_status()
    elif args.test_auth:
        cc.test_authentication()
    elif args.test_feed:
        cc.test_market_feed(30)
    elif args.test_order:
        cc.test_order_execution()
    elif args.test_position:
        cc.test_position_manager()
    elif args.test_all:
        cc.run_full_system_test()
    elif args.help_commands:
        cc.show_help()
    else:
        cc.show_help()


if __name__ == "__main__":
    main()

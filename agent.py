"""
DEVIL TRADING AGENT - MAIN AI BRAIN
Core decision engine with market analysis, signal generation, risk management
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from collections import deque
from dotenv import load_dotenv

# Import our bridge modules
from ..bridge.auth_manager import AngelAuthManager
from ..bridge.market_feed import MarketFeedListener
from ..bridge.order_executor import OrderExecutor
from ..bridge.position_manager import PositionManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DevilTradingAgent:
    """Main AI trading agent with full market intelligence"""
    
    def __init__(self):
        """Initialize the Devil Trading Agent"""
        self.mode = os.getenv('TRADING_MODE', 'PAPER').upper()
        self.risk_per_trade = float(os.getenv('RISK_PER_TRADE', 0.5))
        self.max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', 2.5))
        
        # Initialize components
        self.auth = AngelAuthManager()
        self.feed = MarketFeedListener()
        self.executor = OrderExecutor(mode=self.mode)
        self.position_manager = PositionManager(mode=self.mode)
        
        # Market state
        self.market_regime = "UNKNOWN"
        self.nifty_bias = "NEUTRAL"
        self.options_bias = "NEUTRAL"
        self.volatility_state = "NORMAL"
        
        # Data buffers
        self.price_buffer = deque(maxlen=100)  # Last 100 prices
        self.volume_buffer = deque(maxlen=100)  # Last 100 volumes
        
        # Trading flags
        self.is_running = False
        self.trading_enabled = True
        self.paper_mode = self.mode == 'PAPER'
        
        logger.info(f"🔥 DEVIL TRADING AGENT INITIALIZED in {self.mode} mode")
    
    def initialize(self):
        """Initialize all components"""
        try:
            logger.info("🔄 Initializing components...")
            
            # Connect position manager
            if not self.position_manager.connect():
                logger.error("❌ Position Manager initialization failed")
                return False
            
            # Connect order executor
            if not self.executor.connect():
                logger.error("❌ Order Executor initialization failed")
                return False
            
            # Connect market feed (will connect when started)
            logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization error: {e}")
            return False
    
    def analyze_market(self):
        """Perform comprehensive market analysis"""
        try:
            logger.info("📊 Performing market analysis...")
            
            # Get latest NIFTY candle (placeholder - implement real analysis)
            latest_candle = self.feed.get_latest_candle("NIFTY")
            
            if not latest_candle:
                logger.warning("⚠️  No candle data available")
                return False
            
            # Simple trend analysis (replace with your complex logic)
            open_price = latest_candle.get('open', 0)
            close_price = latest_candle.get('close', 0)
            high_price = latest_candle.get('high', 0)
            low_price = latest_candle.get('low', 0)
            
            # Trend detection
            if close_price > open_price and close_price > (high_price + low_price) / 2:
                self.nifty_bias = "BULLISH"
                self.market_regime = "TREND_UP"
            elif close_price < open_price and close_price < (high_price + low_price) / 2:
                self.nifty_bias = "BEARISH"
                self.market_regime = "TREND_DOWN"
            else:
                self.nifty_bias = "NEUTRAL"
                self.market_regime = "SIDEWAYS"
            
            # Volatility detection
            price_range = high_price - low_price
            avg_range = sum([c['high'] - c['low'] for c in self.feed.candle_builder.current_candles.values()]) / max(1, len(self.feed.candle_builder.current_candles))
            
            if price_range > avg_range * 1.5:
                self.volatility_state = "HIGH"
            elif price_range < avg_range * 0.7:
                self.volatility_state = "LOW"
            else:
                self.volatility_state = "NORMAL"
            
            # Options bias (simple version)
            if self.nifty_bias == "BULLISH":
                self.options_bias = "CE"
            elif self.nifty_bias == "BEARISH":
                self.options_bias = "PE"
            else:
                self.options_bias = "NEUTRAL"
            
            logger.info(
                f"📈 MARKET ANALYSIS COMPLETE\n"
                f"   Regime: {self.market_regime}\n"
                f"   NIFTY Bias: {self.nifty_bias}\n"
                f"   Options Bias: {self.options_bias}\n"
                f"   Volatility: {self.volatility_state}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Market analysis error: {e}")
            return False
    
    def generate_signal(self):
        """Generate trading signal based on analysis"""
        try:
            logger.info("🎯 Generating trading signal...")
            
            # Check if trading allowed
            if not self.trading_enabled:
                logger.warning("⚠️  Trading disabled by user")
                return None
            
            # Check risk limits
            if not self.position_manager.check_risk_limits():
                logger.warning("⚠️  Risk limits breached - no new trades")
                return None
            
            # Generate signal based on market analysis
            if self.nifty_bias == "BULLISH" and self.options_bias == "CE":
                signal = {
                    'action': 'BUY',
                    'symbol': 'NIFTY_CURRENT_CE',  # Replace with actual ATM CE
                    'exchange': 'NFO',
                    'type': 'OPTIONS',
                    'direction': 'CALL',
                    'confidence': 85,
                    'reason': 'Bullish trend with strong momentum',
                    'strategy': 'Trend Following'
                }
            elif self.nifty_bias == "BEARISH" and self.options_bias == "PE":
                signal = {
                    'action': 'BUY',
                    'symbol': 'NIFTY_CURRENT_PE',  # Replace with actual ATM PE
                    'exchange': 'NFO',
                    'type': 'OPTIONS',
                    'direction': 'PUT',
                    'confidence': 80,
                    'reason': 'Bearish trend with strong momentum',
                    'strategy': 'Trend Following'
                }
            else:
                logger.info("💤 No clear signal - waiting for better setup")
                return None
            
            logger.info(
                f"✅ SIGNAL GENERATED\n"
                f"   Action: {signal['action']} {signal['direction']}\n"
                f"   Confidence: {signal['confidence']}%\n"
                f"   Reason: {signal['reason']}"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Signal generation error: {e}")
            return None
    
    def execute_trade(self, signal):
        """Execute trade based on signal"""
        try:
            logger.info("🚀 Executing trade...")
            
            # Get current capital (placeholder - replace with real calculation)
            capital = 100000  # ₹1 lakh
            
            # Calculate position size
            entry_price = 150.0  # Placeholder - get from market data
            stop_loss = entry_price * 0.98  # 2% stop loss
            
            quantity = self.executor.calculate_position_size(
                capital=capital,
                risk_percent=self.risk_per_trade,
                entry_price=entry_price,
                stop_loss_price=stop_loss
            )
            
            if quantity <= 0:
                logger.error("❌ Invalid position size - trade cancelled")
                return False
            
            # Execute order
            order_id = self.executor.place_order(
                symbol=signal['symbol'],
                exchange=signal['exchange'],
                transaction_type=signal['action'],
                quantity=quantity,
                order_type='MARKET',
                price=entry_price,
                stop_loss=stop_loss,
                target=entry_price * 1.04  # 4% target
            )
            
            if order_id:
                # Add to position manager
                self.position_manager.add_position(
                    symbol=signal['symbol'],
                    quantity=quantity,
                    entry_price=entry_price,
                    order_type=signal['action'],
                    stop_loss=stop_loss,
                    target=entry_price * 1.04,
                    metadata={
                        'signal_confidence': signal['confidence'],
                        'strategy': signal['strategy'],
                        'reason': signal['reason']
                    }
                )
                
                logger.info(f"✅ Trade executed successfully - Order ID: {order_id}")
                return True
            else:
                logger.error("❌ Trade execution failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
            return False
    
    def monitor_positions(self):
        """Monitor open positions and manage risk"""
        try:
            logger.info("👀 Monitoring positions...")
            
            # Get current positions
            positions = self.position_manager.get_all_positions()
            
            for symbol, position in positions.items():
                # Update price (get from market feed)
                latest_candle = self.feed.get_latest_candle(symbol)
                if latest_candle:
                    current_price = latest_candle.get('close', position['current_price'])
                    self.position_manager.update_price(symbol, current_price)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Position monitoring error: {e}")
            return False
    
    def start_trading(self):
        """Start the trading agent"""
        try:
            logger.info("🔥 STARTING DEVIL TRADING AGENT...")
            
            if not self.initialize():
                logger.error("❌ Initialization failed - aborting")
                return False
            
            self.is_running = True
            
            # Start market feed (subscribe to NIFTY)
            test_tokens = [{
                "exchangeType": 1,
                "tokens": ["99926000"]  # NIFTY 50
            }]
            
            if not self.feed.start_feed(test_tokens):
                logger.error("❌ Market feed failed to start")
                return False
            
            logger.info("✅ Trading agent started successfully!")
            logger.info(f"Mode: {self.mode}")
            logger.info(f"Risk per trade: {self.risk_per_trade}%")
            logger.info(f"Max daily loss: {self.max_daily_loss}%")
            
            # Main trading loop
            while self.is_running:
                try:
                    # Wait for market data (in live trading, this would be event-driven)
                    time.sleep(5)
                    
                    # Analyze market
                    if not self.analyze_market():
                        continue
                    
                    # Generate signal
                    signal = self.generate_signal()
                    if signal:
                        # Execute trade
                        self.execute_trade(signal)
                    
                    # Monitor positions
                    self.monitor_positions()
                    
                    # Print status every 30 seconds
                    if int(time.time()) % 30 == 0:
                        self.position_manager.print_portfolio()
                        
                except KeyboardInterrupt:
                    logger.info("🛑 Stopping trading agent (Ctrl+C)")
                    break
                except Exception as e:
                    logger.error(f"❌ Trading loop error: {e}")
                    time.sleep(10)  # Wait before retrying
            
            self.stop_trading()
            return True
            
        except Exception as e:
            logger.error(f"❌ Start trading error: {e}")
            return False
    
    def stop_trading(self):
        """Stop the trading agent"""
        try:
            logger.info("🔄 Stopping trading agent...")
            
            self.is_running = False
            
            # Close all positions if needed
            if not self.paper_mode:
                self.position_manager.close_all_positions('SYSTEM_SHUTDOWN')
            
            # Stop market feed
            self.feed.stop_feed()
            
            # Disconnect components
            self.position_manager.disconnect()
            self.executor.disconnect()
            
            logger.info("✅ Trading agent stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Stop trading error: {e}")


# ==============================================================================
# TEST FUNCTION
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 DEVIL TRADING AGENT - MAIN BRAIN TEST")
    print("="*80 + "\n")
    
    agent = DevilTradingAgent()
    
    # Test initialization
    if agent.initialize():
        print("\n✅ Agent initialized successfully!")
        
        # Test market analysis
        print("\n" + "-"*80)
        print("TEST 1: Market Analysis")
        print("-"*80)
        agent.analyze_market()
        
        # Test signal generation
        print("\n" + "-"*80)
        print("TEST 2: Signal Generation")
        print("-"*80)
        signal = agent.generate_signal()
        if signal:
            print(f"Generated signal: {json.dumps(signal, indent=2)}")
        else:
            print("No signal generated (normal in sideways market)")
        
        # Test position manager
        print("\n" + "-"*80)
        print("TEST 3: Position Manager")
        print("-"*80)
        agent.position_manager.print_statistics()
        
        print("\n" + "="*80)
        print("✅ MAIN BRAIN TEST COMPLETED!")
        print("="*80 + "\n")
    else:
        print("\n❌ Agent initialization failed!\n")

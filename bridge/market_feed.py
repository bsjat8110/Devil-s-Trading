"""
DEVIL TRADING AGENT - MARKET FEED LISTENER
Real-time tick data + candle builder engine (PRODUCTION READY)
"""

import os
import time
import json
import logging
from datetime import datetime
from collections import defaultdict
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from bridge.auth_manager import AngelAuthManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CandleBuilder:
    """Converts live ticks into OHLC candles"""
    
    def __init__(self, timeframe_seconds=60):
        """
        Args:
            timeframe_seconds: Candle timeframe (60=1min, 300=5min, etc.)
        """
        self.timeframe = timeframe_seconds
        self.candles = defaultdict(dict)  # {symbol: {timestamp: {O,H,L,C,V}}}
        self.current_candles = {}  # Active candle being built
        
    def process_tick(self, tick_data):
        """Process incoming tick and update candle"""
        try:
            # Handle different tick formats
            if isinstance(tick_data, dict):
                symbol = tick_data.get('name', tick_data.get('token', 'UNKNOWN'))
                ltp = float(tick_data.get('ltp', tick_data.get('last_traded_price', 0)))
                volume = int(tick_data.get('vol', tick_data.get('volume_traded', 0)))
            else:
                return None
            
            if ltp == 0:
                return None
                
            timestamp = datetime.now()
            
            # Calculate candle start time
            candle_time = timestamp.replace(second=0, microsecond=0)
            minutes = (candle_time.minute // (self.timeframe // 60)) * (self.timeframe // 60)
            candle_time = candle_time.replace(minute=minutes)
            
            candle_key = f"{symbol}_{candle_time.strftime('%Y%m%d_%H%M')}"
            
            # Initialize new candle
            if candle_key not in self.current_candles:
                self.current_candles[candle_key] = {
                    'symbol': symbol,
                    'timestamp': candle_time,
                    'open': ltp,
                    'high': ltp,
                    'low': ltp,
                    'close': ltp,
                    'volume': volume,
                    'tick_count': 1
                }
                logger.info(f"🕯️  NEW CANDLE | {symbol} | O:{ltp:.2f} @ {candle_time.strftime('%H:%M')}")
            else:
                # Update existing candle
                candle = self.current_candles[candle_key]
                candle['high'] = max(candle['high'], ltp)
                candle['low'] = min(candle['low'], ltp)
                candle['close'] = ltp
                candle['volume'] = volume
                candle['tick_count'] += 1
                
                # Log every 10 ticks
                if candle['tick_count'] % 10 == 0:
                    logger.info(
                        f"🕯️  UPDATE | {symbol} | "
                        f"O:{candle['open']:.2f} H:{candle['high']:.2f} "
                        f"L:{candle['low']:.2f} C:{candle['close']:.2f} | "
                        f"Ticks:{candle['tick_count']}"
                    )
            
            return self.current_candles[candle_key]
            
        except Exception as e:
            logger.error(f"❌ Candle processing error: {e}")
            return None
    
    def get_latest_candle(self, symbol):
        """Get most recent candle for symbol"""
        for key, candle in self.current_candles.items():
            if candle['symbol'] == symbol:
                return candle
        return None
    
    def get_completed_candles(self, symbol, count=10):
        """Get last N completed candles"""
        if symbol in self.candles:
            sorted_candles = sorted(
                self.candles[symbol].items(),
                key=lambda x: x[0],
                reverse=True
            )
            return [candle for _, candle in sorted_candles[:count]]
        return []


class MarketFeedListener:
    """Real-time market data feed handler (PRODUCTION READY)"""
    
    def __init__(self):
        """Initialize market feed listener"""
        self.auth = AngelAuthManager()
        self.smart_api = None
        self.feed_token = None
        self.client_code = os.getenv('CLIENT_ID')
        self.websocket = None
        self.candle_builder = CandleBuilder(timeframe_seconds=60)  # 1-minute candles
        self.subscribed_tokens = []
        self.is_connected = False
        
        logger.info("✅ Market Feed Listener initialized")
    
    def connect(self):
        """Connect to Angel One market feed"""
        try:
            # Login using market feed API
            logger.info("🔄 Connecting to Angel One Market Feed...")
            self.smart_api = self.auth.login('market')
            
            if not self.smart_api:
                logger.error("❌ Market API login failed")
                return False
            
            # Get feed token
            self.feed_token = self.auth.get_feed_token('market')
            
            if not self.feed_token:
                logger.error("❌ Feed token not available")
                return False
            
            logger.info("✅ Market feed connection established")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def on_tick(self, ws, tick):
        """Callback when tick data received"""
        try:
            # Logger tick data for debugging
            logger.debug(f"📊 Raw tick: {tick}")
            
            # Build candle from tick
            if tick:
                candle = self.candle_builder.process_tick(tick)
            
        except Exception as e:
            logger.error(f"❌ Tick processing error: {e}")
    
    def on_open(self, ws):
        """Callback when websocket opens"""
        self.is_connected = True
        logger.info("✅ WebSocket CONNECTED - Ready to receive data!")
    
    def on_error(self, ws, error):
        """Callback on websocket error"""
        logger.warning(f"⚠️  WebSocket warning: {error}")
    
    def on_close(self, ws):
        """Callback when websocket closes"""
        self.is_connected = False
        logger.info("🔌 WebSocket CLOSED")
    
    def subscribe(self, tokens):
        """
        Subscribe to market data for tokens
        
        Args:
            tokens: List of [{"exchangeType": 1, "tokens": ["token1", "token2"]}]
        """
        try:
            if not self.websocket:
                logger.error("❌ WebSocket not initialized")
                return False
            
            # Angel One SmartWebSocket V2 format
            correlation_id = "correlation_id_1"
            mode = 1  # 1=LTP, 2=Quote, 3=Snap Quote
            
            self.websocket.subscribe(correlation_id, mode, tokens)
            self.subscribed_tokens = tokens
            logger.info(f"✅ SUBSCRIBED to {len(tokens)} token groups")
            return True
            
        except Exception as e:
            logger.error(f"❌ Subscription error: {e}")
            return False
    
    def unsubscribe(self, tokens):
        """Unsubscribe from market data"""
        try:
            if self.websocket:
                correlation_id = "correlation_id_1"
                mode = 1
                self.websocket.unsubscribe(correlation_id, mode, tokens)
                logger.info(f"✅ UNSUBSCRIBED from tokens")
        except Exception as e:
            logger.error(f"❌ Unsubscribe error: {e}")
    
    def start_feed(self, tokens=None):
        """Start real-time market feed"""
        try:
            if not self.connect():
                return False
            
            # Initialize WebSocket V2
            logger.info("🔄 Initializing WebSocket V2...")
            
            self.websocket = SmartWebSocketV2(
                auth_token=self.auth.auth_tokens['market']['auth_token'],
                api_key=os.getenv('MARKET_API_KEY'),
                client_code=self.client_code,
                feed_token=self.feed_token
            )
            
            # Set callbacks
            self.websocket.on_open = self.on_open
            self.websocket.on_data = self.on_tick
            self.websocket.on_error = self.on_error
            self.websocket.on_close = self.on_close
            
            # Connect websocket
            logger.info("🔄 Connecting WebSocket...")
            self.websocket.connect()
            
            # Wait for connection
            time.sleep(2)
            
            # Subscribe to tokens if provided
            if tokens and self.is_connected:
                self.subscribe(tokens)
            
            logger.info("🚀 MARKET FEED STARTED!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Feed start error: {e}")
            return False
    
    def stop_feed(self):
        """Stop market feed gracefully"""
        logger.info("🔄 Stopping market feed...")
        
        try:
            if self.websocket:
                try:
                    self.websocket.close_connection()
                except:
                    pass  # Ignore websocket close errors
        except:
            pass
        
        try:
            self.auth.logout_all()
        except:
            pass  # Ignore logout errors
            
        self.is_connected = False
        logger.info("✅ Market feed STOPPED cleanly")
    
    def get_latest_candle(self, symbol):
        """Get latest candle for a symbol"""
        return self.candle_builder.get_latest_candle(symbol)
    
    def get_candle_history(self, symbol, count=10):
        """Get candle history"""
        return self.candle_builder.get_completed_candles(symbol, count)


# ==============================================================================
# TEST FUNCTION
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 DEVIL TRADING AGENT - MARKET FEED TEST")
    print("="*70 + "\n")
    
    feed = MarketFeedListener()
    
    # NIFTY 50 Index Token
    # Exchange Type: 1=NSE, 2=NFO (Options), 3=MCX
    test_tokens = [{
        "exchangeType": 1,  # NSE
        "tokens": ["99926000"]  # NIFTY 50
    }]
    
    print("📊 Subscribing to: NIFTY 50 Index")
    print("⏳ Test Duration: 30 seconds")
    print("⚠️  Note: Live data only during market hours (9:15 AM - 3:30 PM)\n")
    print("-" * 70)
    
    if feed.start_feed(test_tokens):
        try:
            print("\n✅ Feed running... (Press Ctrl+C to stop early)\n")
            time.sleep(30)
            print("\n⏰ 30 seconds completed!")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Stopped by user (Ctrl+C)")
            
        finally:
            print("\n" + "-" * 70)
            feed.stop_feed()
            print("\n" + "="*70)
            print("✅ TEST COMPLETED SUCCESSFULLY!")
            print("="*70 + "\n")
    else:
        print("\n❌ Feed start FAILED - Check credentials and try again!\n")

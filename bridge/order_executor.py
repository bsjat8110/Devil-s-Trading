"""
DEVIL TRADING AGENT - ORDER EXECUTOR
Handles order placement, modification, cancellation (Paper + Live Mode)
"""

import os
import json
import logging
from datetime import datetime
from bridge.auth_manager import AngelAuthManager
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrderExecutor:
    """Professional order execution engine with paper + live trading"""
    
    def __init__(self, mode='PAPER'):
        """
        Initialize order executor
        
        Args:
            mode: 'PAPER' or 'LIVE'
        """
        self.mode = mode.upper()
        self.auth = AngelAuthManager()
        self.smart_api = None
        self.client_code = os.getenv('CLIENT_ID')
        
        # Order tracking
        self.orders = {}  # {order_id: order_details}
        self.positions = {}  # {symbol: position_details}
        self.paper_order_counter = 1000
        
        # Risk settings
        self.risk_per_trade = float(os.getenv('RISK_PER_TRADE', 0.5))
        self.max_positions = int(os.getenv('MAX_POSITIONS', 2))
        
        logger.info(f"✅ Order Executor initialized in {self.mode} mode")
        
        if self.mode == 'LIVE':
            logger.warning("⚠️  LIVE TRADING MODE - Real money at risk!")
        else:
            logger.info("📄 PAPER TRADING MODE - No real money")
    
    def connect(self):
        """Connect to trading API"""
        try:
            if self.mode == 'PAPER':
                logger.info("📄 Paper mode - No API connection needed")
                return True
            
            logger.info("🔄 Connecting to Trading API...")
            self.smart_api = self.auth.login('trading')
            
            if not self.smart_api:
                logger.error("❌ Trading API login failed")
                return False
            
            logger.info("✅ Trading API connected")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def calculate_position_size(self, capital, risk_percent, entry_price, stop_loss_price):
        """
        Calculate position size based on risk management
        
        Args:
            capital: Total capital available
            risk_percent: Risk per trade (0.5 = 0.5%)
            entry_price: Entry price
            stop_loss_price: Stop loss price
            
        Returns:
            quantity: Number of lots/shares to buy
        """
        try:
            risk_amount = capital * (risk_percent / 100)
            price_diff = abs(entry_price - stop_loss_price)
            
            if price_diff == 0:
                logger.error("❌ Invalid stop loss - same as entry price")
                return 0
            
            quantity = int(risk_amount / price_diff)
            
            logger.info(
                f"📊 Position Size: {quantity} units | "
                f"Risk: ₹{risk_amount:.2f} ({risk_percent}%) | "
                f"Risk/Unit: ₹{price_diff:.2f}"
            )
            
            return quantity
            
        except Exception as e:
            logger.error(f"❌ Position size calculation error: {e}")
            return 0
    
    def place_order(self, symbol, exchange, transaction_type, quantity, 
                    order_type='MARKET', price=0, stop_loss=None, target=None):
        """
        Place order (Paper or Live)
        
        Args:
            symbol: Trading symbol (e.g., 'NIFTY23FEB23500CE')
            exchange: 'NSE', 'NFO', 'BSE', etc.
            transaction_type: 'BUY' or 'SELL'
            quantity: Number of lots/shares
            order_type: 'MARKET', 'LIMIT', 'STOPLOSS_LIMIT'
            price: Limit price (for LIMIT orders)
            stop_loss: Stop loss price
            target: Target price
            
        Returns:
            order_id: Order ID if successful, None otherwise
        """
        try:
            # Validation
            if len(self.positions) >= self.max_positions:
                logger.warning(f"⚠️  Max positions ({self.max_positions}) reached!")
                return None
            
            order_details = {
                'symbol': symbol,
                'exchange': exchange,
                'transaction_type': transaction_type,
                'quantity': quantity,
                'order_type': order_type,
                'price': price,
                'stop_loss': stop_loss,
                'target': target,
                'timestamp': datetime.now(),
                'status': 'PENDING'
            }
            
            if self.mode == 'PAPER':
                return self._place_paper_order(order_details)
            else:
                return self._place_live_order(order_details)
                
        except Exception as e:
            logger.error(f"❌ Order placement error: {e}")
            return None
    
    def _place_paper_order(self, order_details):
        """Place paper order (simulated)"""
        try:
            order_id = f"PAPER_{self.paper_order_counter}"
            self.paper_order_counter += 1
            
            # Simulate instant execution for market orders
            if order_details['order_type'] == 'MARKET':
                order_details['status'] = 'COMPLETE'
                order_details['executed_price'] = order_details.get('price', 0)
                order_details['executed_qty'] = order_details['quantity']
            
            self.orders[order_id] = order_details
            
            logger.info(
                f"📄 PAPER ORDER PLACED\n"
                f"   Order ID: {order_id}\n"
                f"   {order_details['transaction_type']} {order_details['quantity']} x {order_details['symbol']}\n"
                f"   Type: {order_details['order_type']} @ ₹{order_details['price']}\n"
                f"   SL: {order_details['stop_loss']} | Target: {order_details['target']}"
            )
            
            # Update positions
            self._update_position(order_id, order_details)
            
            return order_id
            
        except Exception as e:
            logger.error(f"❌ Paper order error: {e}")
            return None
    
    def _place_live_order(self, order_details):
        """Place live order via Angel One API"""
        try:
            if not self.smart_api:
                logger.error("❌ Trading API not connected")
                return None
            
            # Angel One order parameters
            order_params = {
                "variety": "NORMAL",
                "tradingsymbol": order_details['symbol'],
                "symboltoken": self._get_symbol_token(order_details['symbol']),
                "transactiontype": order_details['transaction_type'],
                "exchange": order_details['exchange'],
                "ordertype": order_details['order_type'],
                "producttype": "INTRADAY",  # or "DELIVERY"
                "duration": "DAY",
                "price": str(order_details['price']) if order_details['price'] > 0 else "0",
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(order_details['quantity'])
            }
            
            # Place order
            logger.info(f"🔄 Placing LIVE order...")
            response = self.smart_api.placeOrder(order_params)
            
            if response and response.get('status'):
                order_id = response['data']['orderid']
                order_details['status'] = 'PLACED'
                order_details['order_id'] = order_id
                self.orders[order_id] = order_details
                
                logger.info(
                    f"✅ LIVE ORDER PLACED\n"
                    f"   Order ID: {order_id}\n"
                    f"   {order_details['transaction_type']} {order_details['quantity']} x {order_details['symbol']}\n"
                    f"   Type: {order_details['order_type']} @ ₹{order_details['price']}"
                )
                
                return order_id
            else:
                logger.error(f"❌ Order failed: {response.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Live order error: {e}")
            return None
    
    def _update_position(self, order_id, order_details):
        """Update position tracking"""
        try:
            symbol = order_details['symbol']
            
            if symbol not in self.positions:
                self.positions[symbol] = {
                    'symbol': symbol,
                    'quantity': 0,
                    'avg_price': 0,
                    'pnl': 0,
                    'orders': []
                }
            
            position = self.positions[symbol]
            
            if order_details['transaction_type'] == 'BUY':
                total_value = (position['quantity'] * position['avg_price']) + \
                             (order_details['quantity'] * order_details['price'])
                total_qty = position['quantity'] + order_details['quantity']
                position['avg_price'] = total_value / total_qty if total_qty > 0 else 0
                position['quantity'] = total_qty
            else:  # SELL
                position['quantity'] -= order_details['quantity']
            
            position['orders'].append(order_id)
            
            logger.info(
                f"📊 POSITION UPDATED: {symbol}\n"
                f"   Quantity: {position['quantity']}\n"
                f"   Avg Price: ₹{position['avg_price']:.2f}"
            )
            
        except Exception as e:
            logger.error(f"❌ Position update error: {e}")
    
    def get_order_status(self, order_id):
        """Get order status"""
        if order_id in self.orders:
            return self.orders[order_id]
        return None
    
    def get_all_orders(self):
        """Get all orders"""
        return self.orders
    
    def get_positions(self):
        """Get all positions"""
        return self.positions
    
    def cancel_order(self, order_id):
        """Cancel pending order"""
        try:
            if order_id not in self.orders:
                logger.error(f"❌ Order {order_id} not found")
                return False
            
            order = self.orders[order_id]
            
            if order['status'] == 'COMPLETE':
                logger.warning(f"⚠️  Cannot cancel completed order {order_id}")
                return False
            
            if self.mode == 'PAPER':
                order['status'] = 'CANCELLED'
                logger.info(f"✅ Paper order {order_id} cancelled")
                return True
            else:
                # Cancel live order
                response = self.smart_api.cancelOrder(order_id, "NORMAL")
                if response and response.get('status'):
                    order['status'] = 'CANCELLED'
                    logger.info(f"✅ Live order {order_id} cancelled")
                    return True
                else:
                    logger.error(f"❌ Cancel failed: {response.get('message')}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Cancel error: {e}")
            return False
    
    def _get_symbol_token(self, symbol):
        """Get symbol token (placeholder - implement token mapping)"""
        # TODO: Implement proper symbol to token mapping
        # This requires master contract download
        return "99926000"  # NIFTY 50 example
    
    def disconnect(self):
        """Disconnect and cleanup"""
        logger.info("🔄 Disconnecting order executor...")
        
        if self.mode == 'LIVE':
            try:
                self.auth.logout_all()
            except:
                pass
        
        logger.info("✅ Order executor disconnected")


# ==============================================================================
# TEST FUNCTION
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 DEVIL TRADING AGENT - ORDER EXECUTOR TEST")
    print("="*70 + "\n")
    
    # Test in PAPER mode
    executor = OrderExecutor(mode='PAPER')
    
    if executor.connect():
        print("\n" + "-"*70)
        print("📊 TEST 1: Calculate Position Size")
        print("-"*70)
        
        qty = executor.calculate_position_size(
            capital=100000,
            risk_percent=0.5,
            entry_price=23500,
            stop_loss_price=23450
        )
        print(f"✅ Calculated quantity: {qty} units\n")
        
        print("-"*70)
        print("📊 TEST 2: Place Paper Order (BUY)")
        print("-"*70)
        
        order_id = executor.place_order(
            symbol='NIFTY23FEB23500CE',
            exchange='NFO',
            transaction_type='BUY',
            quantity=qty,
            order_type='MARKET',
            price=150.50,
            stop_loss=145.00,
            target=160.00
        )
        
        if order_id:
            print(f"\n✅ Order placed: {order_id}")
            
            print("\n" + "-"*70)
            print("📊 TEST 3: Check Order Status")
            print("-"*70)
            
            status = executor.get_order_status(order_id)
            print(f"Order Status: {json.dumps(status, indent=2, default=str)}")
            
            print("\n" + "-"*70)
            print("📊 TEST 4: Check Positions")
            print("-"*70)
            
            positions = executor.get_positions()
            print(f"Positions: {json.dumps(positions, indent=2, default=str)}")
        
        executor.disconnect()
        
        print("\n" + "="*70)
        print("✅ ORDER EXECUTOR TEST COMPLETED!")
        print("="*70 + "\n")
    else:
        print("❌ Connection failed!\n")

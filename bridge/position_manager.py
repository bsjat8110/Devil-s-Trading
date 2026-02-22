"""
DEVIL TRADING AGENT - POSITION MANAGER
Real-time portfolio tracking, P&L calculation, risk monitoring
"""

import os
import json
import logging
from datetime import datetime
from collections import defaultdict
from bridge.auth_manager import AngelAuthManager
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PositionManager:
    """Professional position and portfolio management"""
    
    def __init__(self, mode='PAPER'):
        """
        Initialize position manager
        
        Args:
            mode: 'PAPER' or 'LIVE'
        """
        self.mode = mode.upper()
        self.auth = AngelAuthManager()
        self.smart_api = None
        self.client_code = os.getenv('CLIENT_ID')
        
        # Portfolio tracking
        self.positions = {}  # Active positions
        self.closed_positions = []  # Trade history
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        
        # Risk limits
        self.max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', 2.5))
        self.max_positions = int(os.getenv('MAX_POSITIONS', 2))
        
        # Statistics
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'expectancy': 0.0
        }
        
        logger.info(f"✅ Position Manager initialized in {self.mode} mode")
    
    def connect(self):
        """Connect to Angel One API"""
        try:
            if self.mode == 'PAPER':
                logger.info("📄 Paper mode - Simulated positions")
                return True
            
            logger.info("🔄 Connecting to Trading API for positions...")
            self.smart_api = self.auth.login('trading')
            
            if not self.smart_api:
                logger.error("❌ Trading API login failed")
                return False
            
            # Fetch existing positions
            self._sync_positions()
            
            logger.info("✅ Position Manager connected")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def _sync_positions(self):
        """Sync positions from broker (Live mode only)"""
        try:
            if self.mode == 'PAPER':
                return
            
            logger.info("🔄 Syncing positions from broker...")
            response = self.smart_api.position()
            
            if response and response.get('status'):
                broker_positions = response.get('data', [])
                
                for pos in broker_positions:
                    if int(pos.get('netqty', 0)) != 0:
                        symbol = pos.get('tradingsymbol')
                        self.positions[symbol] = {
                            'symbol': symbol,
                            'quantity': int(pos.get('netqty')),
                            'avg_price': float(pos.get('avgprice', 0)),
                            'ltp': float(pos.get('ltp', 0)),
                            'pnl': float(pos.get('pnl', 0)),
                            'exchange': pos.get('exchange'),
                            'product': pos.get('producttype')
                        }
                
                logger.info(f"✅ Synced {len(self.positions)} positions from broker")
            else:
                logger.warning("⚠️  No positions found or API error")
                
        except Exception as e:
            logger.error(f"❌ Position sync error: {e}")
    
    def add_position(self, symbol, quantity, entry_price, order_type='BUY', 
                     stop_loss=None, target=None, metadata=None):
        """
        Add new position to tracking
        
        Args:
            symbol: Trading symbol
            quantity: Position size
            entry_price: Entry price
            order_type: 'BUY' or 'SELL'
            stop_loss: Stop loss price
            target: Target price
            metadata: Additional data (strategy, setup, etc.)
        """
        try:
            if symbol in self.positions:
                logger.warning(f"⚠️  Position {symbol} already exists - updating...")
                self._update_existing_position(symbol, quantity, entry_price, order_type)
                return
            
            position = {
                'symbol': symbol,
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': entry_price,
                'order_type': order_type,
                'stop_loss': stop_loss,
                'target': target,
                'entry_time': datetime.now(),
                'pnl': 0.0,
                'pnl_percent': 0.0,
                'status': 'OPEN',
                'metadata': metadata or {}
            }
            
            self.positions[symbol] = position
            
            logger.info(
                f"✅ POSITION ADDED\n"
                f"   Symbol: {symbol}\n"
                f"   Type: {order_type}\n"
                f"   Quantity: {quantity}\n"
                f"   Entry: ₹{entry_price:.2f}\n"
                f"   SL: ₹{stop_loss} | Target: ₹{target}"
            )
            
        except Exception as e:
            logger.error(f"❌ Add position error: {e}")
    
    def _update_existing_position(self, symbol, quantity, price, order_type):
        """Update existing position (averaging or reducing)"""
        try:
            position = self.positions[symbol]
            
            if order_type == position['order_type']:
                # Averaging (adding to position)
                total_value = (position['quantity'] * position['entry_price']) + \
                             (quantity * price)
                total_qty = position['quantity'] + quantity
                position['entry_price'] = total_value / total_qty
                position['quantity'] = total_qty
                logger.info(f"📊 Position averaged: {symbol} @ ₹{position['entry_price']:.2f}")
            else:
                # Reducing/Closing position
                position['quantity'] -= quantity
                if position['quantity'] <= 0:
                    self._close_position(symbol, price)
                else:
                    logger.info(f"📊 Position reduced: {symbol} - Remaining qty: {position['quantity']}")
                    
        except Exception as e:
            logger.error(f"❌ Update position error: {e}")
    
    def update_price(self, symbol, current_price):
        """
        Update current price and calculate P&L
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
        """
        try:
            if symbol not in self.positions:
                return
            
            position = self.positions[symbol]
            position['current_price'] = current_price
            
            # Calculate P&L
            if position['order_type'] == 'BUY':
                pnl = (current_price - position['entry_price']) * position['quantity']
            else:  # SELL
                pnl = (position['entry_price'] - current_price) * position['quantity']
            
            position['pnl'] = pnl
            position['pnl_percent'] = (pnl / (position['entry_price'] * position['quantity'])) * 100
            
            # Check stop loss
            if position['stop_loss']:
                if position['order_type'] == 'BUY' and current_price <= position['stop_loss']:
                    logger.warning(f"🛑 STOP LOSS HIT: {symbol} @ ₹{current_price}")
                    self._close_position(symbol, current_price, reason='STOP_LOSS')
                    return
                elif position['order_type'] == 'SELL' and current_price >= position['stop_loss']:
                    logger.warning(f"🛑 STOP LOSS HIT: {symbol} @ ₹{current_price}")
                    self._close_position(symbol, current_price, reason='STOP_LOSS')
                    return
            
            # Check target
            if position['target']:
                if position['order_type'] == 'BUY' and current_price >= position['target']:
                    logger.info(f"🎯 TARGET HIT: {symbol} @ ₹{current_price}")
                    self._close_position(symbol, current_price, reason='TARGET')
                    return
                elif position['order_type'] == 'SELL' and current_price <= position['target']:
                    logger.info(f"🎯 TARGET HIT: {symbol} @ ₹{current_price}")
                    self._close_position(symbol, current_price, reason='TARGET')
                    return
            
        except Exception as e:
            logger.error(f"❌ Price update error: {e}")
    
    def _close_position(self, symbol, exit_price, reason='MANUAL'):
        """Close position and move to history"""
        try:
            if symbol not in self.positions:
                logger.error(f"❌ Position {symbol} not found")
                return
            
            position = self.positions[symbol]
            position['exit_price'] = exit_price
            position['exit_time'] = datetime.now()
            position['exit_reason'] = reason
            position['status'] = 'CLOSED'
            
            # Calculate final P&L
            if position['order_type'] == 'BUY':
                final_pnl = (exit_price - position['entry_price']) * position['quantity']
            else:
                final_pnl = (position['entry_price'] - exit_price) * position['quantity']
            
            position['pnl'] = final_pnl
            position['pnl_percent'] = (final_pnl / (position['entry_price'] * position['quantity'])) * 100
            
            # Update statistics
            self._update_statistics(position)
            
            # Move to closed positions
            self.closed_positions.append(position)
            del self.positions[symbol]
            
            logger.info(
                f"{'🟢' if final_pnl > 0 else '🔴'} POSITION CLOSED\n"
                f"   Symbol: {symbol}\n"
                f"   Entry: ₹{position['entry_price']:.2f} → Exit: ₹{exit_price:.2f}\n"
                f"   P&L: ₹{final_pnl:.2f} ({position['pnl_percent']:.2f}%)\n"
                f"   Reason: {reason}\n"
                f"   Duration: {position['exit_time'] - position['entry_time']}"
            )
            
        except Exception as e:
            logger.error(f"❌ Close position error: {e}")
    
    def _update_statistics(self, closed_position):
        """Update trading statistics"""
        try:
            pnl = closed_position['pnl']
            
            self.stats['total_trades'] += 1
            
            if pnl > 0:
                self.stats['winning_trades'] += 1
                self.stats['total_profit'] += pnl
                self.stats['largest_win'] = max(self.stats['largest_win'], pnl)
            else:
                self.stats['losing_trades'] += 1
                self.stats['total_loss'] += abs(pnl)
                self.stats['largest_loss'] = max(self.stats['largest_loss'], abs(pnl))
            
            # Calculate metrics
            total_trades = self.stats['total_trades']
            winning_trades = self.stats['winning_trades']
            losing_trades = self.stats['losing_trades']
            
            self.stats['win_rate'] = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            self.stats['avg_win'] = (self.stats['total_profit'] / winning_trades) if winning_trades > 0 else 0
            self.stats['avg_loss'] = (self.stats['total_loss'] / losing_trades) if losing_trades > 0 else 0
            
            # Profit factor
            if self.stats['total_loss'] > 0:
                self.stats['profit_factor'] = self.stats['total_profit'] / self.stats['total_loss']
            
            # Expectancy
            win_rate = self.stats['win_rate'] / 100
            loss_rate = 1 - win_rate
            self.stats['expectancy'] = (win_rate * self.stats['avg_win']) - (loss_rate * self.stats['avg_loss'])
            
            # Update daily P&L
            self.daily_pnl += pnl
            self.total_pnl += pnl
            
        except Exception as e:
            logger.error(f"❌ Statistics update error: {e}")
    
    def get_position(self, symbol):
        """Get specific position"""
        return self.positions.get(symbol)
    
    def get_all_positions(self):
        """Get all active positions"""
        return self.positions
    
    def get_portfolio_summary(self):
        """Get portfolio summary"""
        try:
            total_value = 0
            total_pnl = 0
            
            for symbol, pos in self.positions.items():
                position_value = pos['current_price'] * pos['quantity']
                total_value += position_value
                total_pnl += pos['pnl']
            
            summary = {
                'total_positions': len(self.positions),
                'total_value': total_value,
                'unrealized_pnl': total_pnl,
                'daily_pnl': self.daily_pnl,
                'total_pnl': self.total_pnl,
                'positions': self.positions
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Portfolio summary error: {e}")
            return {}
    
    def get_statistics(self):
        """Get trading statistics"""
        return self.stats
    
    def check_risk_limits(self):
        """Check if risk limits breached"""
        try:
            # Check max daily loss
            if abs(self.daily_pnl) >= self.max_daily_loss:
                logger.error(
                    f"🚨 DAILY LOSS LIMIT BREACHED!\n"
                    f"   Loss: ₹{abs(self.daily_pnl):.2f}\n"
                    f"   Limit: ₹{self.max_daily_loss:.2f}\n"
                    f"   🛑 TRADING BLOCKED FOR TODAY!"
                )
                return False
            
            # Check max positions
            if len(self.positions) >= self.max_positions:
                logger.warning(
                    f"⚠️  MAX POSITIONS REACHED!\n"
                    f"   Current: {len(self.positions)}\n"
                    f"   Limit: {self.max_positions}"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Risk check error: {e}")
            return True
    
    def close_all_positions(self, reason='MANUAL_EXIT'):
        """Close all open positions"""
        try:
            symbols = list(self.positions.keys())
            
            for symbol in symbols:
                position = self.positions[symbol]
                self._close_position(symbol, position['current_price'], reason)
            
            logger.info(f"✅ All positions closed - Reason: {reason}")
            
        except Exception as e:
            logger.error(f"❌ Close all error: {e}")
    
    def print_portfolio(self):
        """Print formatted portfolio"""
        print("\n" + "="*80)
        print("📊 PORTFOLIO SUMMARY")
        print("="*80)
        
        summary = self.get_portfolio_summary()
        
        print(f"\n💼 Total Positions: {summary['total_positions']}")
        print(f"💰 Total Value: ₹{summary['total_value']:.2f}")
        print(f"📈 Unrealized P&L: ₹{summary['unrealized_pnl']:.2f}")
        print(f"📅 Daily P&L: ₹{summary['daily_pnl']:.2f}")
        print(f"📊 Total P&L: ₹{summary['total_pnl']:.2f}")
        
        if self.positions:
            print("\n" + "-"*80)
            print("ACTIVE POSITIONS:")
            print("-"*80)
            
            for symbol, pos in self.positions.items():
                pnl_emoji = "🟢" if pos['pnl'] > 0 else "🔴"
                print(f"\n{pnl_emoji} {symbol}")
                print(f"   Type: {pos['order_type']} | Qty: {pos['quantity']}")
                print(f"   Entry: ₹{pos['entry_price']:.2f} | Current: ₹{pos['current_price']:.2f}")
                print(f"   P&L: ₹{pos['pnl']:.2f} ({pos['pnl_percent']:.2f}%)")
                if pos['stop_loss']:
                    print(f"   SL: ₹{pos['stop_loss']} | Target: ₹{pos['target']}")
        
        print("\n" + "="*80 + "\n")
    
    def print_statistics(self):
        """Print trading statistics"""
        print("\n" + "="*80)
        print("📊 TRADING STATISTICS")
        print("="*80)
        
        stats = self.stats
        
        print(f"\n📈 Total Trades: {stats['total_trades']}")
        print(f"✅ Winning Trades: {stats['winning_trades']}")
        print(f"❌ Losing Trades: {stats['losing_trades']}")
        print(f"🎯 Win Rate: {stats['win_rate']:.2f}%")
        print(f"\n💰 Total Profit: ₹{stats['total_profit']:.2f}")
        print(f"💸 Total Loss: ₹{stats['total_loss']:.2f}")
        print(f"📊 Net P&L: ₹{stats['total_profit'] - stats['total_loss']:.2f}")
        print(f"\n🏆 Largest Win: ₹{stats['largest_win']:.2f}")
        print(f"💔 Largest Loss: ₹{stats['largest_loss']:.2f}")
        print(f"📊 Average Win: ₹{stats['avg_win']:.2f}")
        print(f"📉 Average Loss: ₹{stats['avg_loss']:.2f}")
        print(f"\n⚡ Profit Factor: {stats['profit_factor']:.2f}")
        print(f"🎲 Expectancy: ₹{stats['expectancy']:.2f}")
        
        print("\n" + "="*80 + "\n")
    
    def disconnect(self):
        """Cleanup and disconnect"""
        logger.info("🔄 Disconnecting position manager...")
        
        if self.mode == 'LIVE':
            try:
                self.auth.logout_all()
            except:
                pass
        
        logger.info("✅ Position manager disconnected")


# ==============================================================================
# TEST FUNCTION
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 DEVIL TRADING AGENT - POSITION MANAGER TEST")
    print("="*80 + "\n")
    
    pm = PositionManager(mode='PAPER')
    
    if pm.connect():
        print("\n" + "-"*80)
        print("TEST 1: Add Positions")
        print("-"*80 + "\n")
        
        # Add position 1
        pm.add_position(
            symbol='NIFTY23FEB23500CE',
            quantity=50,
            entry_price=150.50,
            order_type='BUY',
            stop_loss=145.00,
            target=160.00,
            metadata={'strategy': 'Breakout', 'setup': 'Bullish Engulfing'}
        )
        
        # Add position 2
        pm.add_position(
            symbol='BANKNIFTY23FEB47000PE',
            quantity=25,
            entry_price=180.75,
            order_type='BUY',
            stop_loss=175.00,
            target=195.00,
            metadata={'strategy': 'Reversal', 'setup': 'Support Bounce'}
        )
        
        print("\n" + "-"*80)
        print("TEST 2: Update Prices (Simulate Market Movement)")
        print("-"*80 + "\n")
        
        # Simulate price updates
        pm.update_price('NIFTY23FEB23500CE', 155.25)  # Profit
        pm.update_price('BANKNIFTY23FEB47000PE', 178.50)  # Small loss
        
        pm.print_portfolio()
        
        print("-"*80)
        print("TEST 3: Hit Target (Auto Close)")
        print("-"*80 + "\n")
        
        pm.update_price('NIFTY23FEB23500CE', 160.50)  # Hit target
        
        print("\n" + "-"*80)
        print("TEST 4: Manual Close Remaining Position")
        print("-"*80 + "\n")
        
        pm._close_position('BANKNIFTY23FEB47000PE', 177.00, 'MANUAL')
        
        pm.print_portfolio()
        pm.print_statistics()
        
        pm.disconnect()
        
        print("="*80)
        print("✅ POSITION MANAGER TEST COMPLETED!")
        print("="*80 + "\n")
    else:
        print("❌ Connection failed!\n")

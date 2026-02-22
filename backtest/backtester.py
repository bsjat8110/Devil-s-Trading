"""
Backtesting Engine
Simulates trading strategies on historical data
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Callable, Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Backtester:
    """
    Core backtesting engine
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        initial_capital: float = 100000,
        commission: float = 20,
        slippage: float = 0.1
    ):
        """
        Initialize backtester
        
        Args:
            data: DataFrame with OHLC data
            initial_capital: Starting capital
            commission: Commission per trade (in rupees)
            slippage: Slippage percentage
        """
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.starting_capital = initial_capital  # Store original
        self.commission = commission
        self.slippage_pct = slippage
        
        self.capital = initial_capital
        self.position = None
        self.trades = []
        self.equity_curve = []
        
        logger.info(f"✅ Backtester initialized with ₹{initial_capital:,.0f}")
    
    def apply_slippage(self, price: float, side: str) -> float:
        """
        Apply slippage to execution price
        
        Args:
            price: Original price
            side: 'BUY' or 'SELL'
            
        Returns:
            Price after slippage
        """
        slippage_amount = price * (self.slippage_pct / 100)
        
        if side == 'BUY':
            return price + slippage_amount
        else:
            return price - slippage_amount
    
    def enter_trade(self, row: pd.Series, quantity: int):
        """
        Enter a new position
        
        Args:
            row: Current candle data
            quantity: Number of lots/shares
        """
        if self.position:
            logger.debug("Already in position, skipping entry")
            return
        
        entry_price = self.apply_slippage(row['close'], 'BUY')
        total_cost = (entry_price * quantity) + self.commission
        
        if total_cost > self.capital:
            logger.warning(f"Insufficient capital for trade (need ₹{total_cost:,.2f})")
            return
        
        self.position = {
            'entry_time': row['timestamp'],
            'entry_price': entry_price,
            'quantity': quantity,
            'capital_used': total_cost
        }
        
        self.capital -= total_cost
        logger.debug(f"🟢 ENTER: {quantity} @ ₹{entry_price:.2f}")
    
    def exit_trade(self, row: pd.Series, reason: str = 'Signal'):
        """
        Exit current position
        
        Args:
            row: Current candle data
            reason: Exit reason
        """
        if not self.position:
            logger.debug("No position to exit")
            return
        
        exit_price = self.apply_slippage(row['close'], 'SELL')
        
        pnl = (exit_price - self.position['entry_price']) * self.position['quantity']
        pnl -= self.commission  # Exit commission
        
        self.capital += (exit_price * self.position['quantity'])
        
        trade_record = {
            'entry_time': self.position['entry_time'],
            'exit_time': row['timestamp'],
            'entry_price': self.position['entry_price'],
            'exit_price': exit_price,
            'quantity': self.position['quantity'],
            'pnl': pnl,
            'exit_reason': reason
        }
        
        self.trades.append(trade_record)
        logger.debug(f"🔴 EXIT: ₹{pnl:+,.2f} ({reason})")
        
        self.position = None
    
    def run(self, strategy_func: Callable) -> Dict:
        """
        Run backtest with a strategy function
        
        Args:
            strategy_func: Function that takes (backtester, row) and makes trades
            
        Returns:
            Dictionary with backtest results
        """
        logger.info("🚀 Starting backtest...")
        
        for idx, row in self.data.iterrows():
            # Call strategy function
            strategy_func(self, row)
            
            # Track equity
            current_equity = self.capital
            if self.position:
                unrealized_pnl = (row['close'] - self.position['entry_price']) * self.position['quantity']
                current_equity += self.position['capital_used'] + unrealized_pnl
            
            self.equity_curve.append({
                'timestamp': row['timestamp'],
                'equity': current_equity
            })
        
        # Close any open position at end
        if self.position:
            self.exit_trade(self.data.iloc[-1], reason='Backtest End')
        
        results = self._calculate_metrics()
        logger.info("✅ Backtest completed")
        
        return results
    
    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        
        if not self.trades:
            return {
                'initial_capital': self.starting_capital,
                'final_capital': self.capital,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
                'sharpe_ratio': 0.0,
                'trades': pd.DataFrame(),
                'equity_curve': pd.DataFrame(self.equity_curve)
            }
        
        trades_df = pd.DataFrame(self.trades)
        
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = trades_df['pnl'].sum()
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].mean()) if losing_trades > 0 else 0
        
        # Max Drawdown
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = equity_df['equity'] - equity_df['peak']
        max_drawdown = abs(equity_df['drawdown'].min())
        max_dd_pct = (max_drawdown / self.starting_capital) * 100 if self.starting_capital > 0 else 0
        
        # Sharpe Ratio (simplified)
        returns = trades_df['pnl'] / self.starting_capital
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() != 0 else 0
        
        return {
            'initial_capital': self.starting_capital,
            'final_capital': self.capital,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_dd_pct,
            'sharpe_ratio': sharpe if not np.isnan(sharpe) else 0.0,
            'trades': trades_df,
            'equity_curve': pd.DataFrame(self.equity_curve)
        }


if __name__ == "__main__":
    print("🧪 Backtester module ready")
    print("Use with historical data from DataDownloader")

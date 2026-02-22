"""
Backtesting Engine for Devil's Trading System
Test strategies on historical data with detailed metrics
"""

import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class Backtester:
    """Strategy backtesting engine"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = [initial_capital]
        
        # Available strategies
        self.strategies = {
            'EMA_CROSSOVER': self._ema_crossover,
            'RSI_REVERSAL': self._rsi_reversal,
            'BOLLINGER_BREAKOUT': self._bollinger_breakout,
            'MACD_MOMENTUM': self._macd_momentum
        }
    
    def _generate_mock_data(self, symbol: str, days: int) -> List[Dict]:
        """Generate mock historical data for testing"""
        data = []
        price = 180  # Starting price
        today = datetime.now()
        
        for i in range(days * 390):  # 390 minutes in trading day
            date = today - timedelta(minutes=days * 390 - i)
            
            # Random walk with trend
            change = random.uniform(-2, 2)
            price = max(100, price + change)
            
            data.append({
                'timestamp': date.isoformat(),
                'open': round(price - random.uniform(0, 1), 2),
                'high': round(price + random.uniform(0, 2), 2),
                'low': round(price - random.uniform(0, 2), 2),
                'close': round(price, 2),
                'volume': random.randint(10000, 100000)
            })
        
        return data
    
    def _calculate_ema(self, data: List, period: int) -> List:
        """Calculate Exponential Moving Average"""
        ema = []
        multiplier = 2 / (period + 1)
        
        # First EMA is SMA
        sma = sum(d['close'] for d in data[:period]) / period
        ema.extend([None] * (period - 1))
        ema.append(sma)
        
        for i in range(period, len(data)):
            ema_value = (data[i]['close'] - ema[i-1]) * multiplier + ema[i-1]
            ema.append(ema_value)
        
        return ema
    
    def _calculate_rsi(self, data: List, period: int = 14) -> List:
        """Calculate RSI"""
        rsi = []
        gains = []
        losses = []
        
        for i in range(1, len(data)):
            change = data[i]['close'] - data[i-1]['close']
            gains.append(max(0, change))
            losses.append(max(0, -change))
            
            if i < period:
                rsi.append(None)
            else:
                avg_gain = sum(gains[-period:]) / period
                avg_loss = sum(losses[-period:]) / period
                
                if avg_loss == 0:
                    rsi.append(100)
                else:
                    rs = avg_gain / avg_loss
                    rsi.append(100 - (100 / (1 + rs)))
        
        return [None] + rsi
    
    def _calculate_bollinger(self, data: List, period: int = 20) -> Dict:
        """Calculate Bollinger Bands"""
        middle = []
        upper = []
        lower = []
        
        for i in range(len(data)):
            if i < period - 1:
                middle.append(None)
                upper.append(None)
                lower.append(None)
            else:
                window = [d['close'] for d in data[i-period+1:i+1]]
                sma = sum(window) / period
                std = (sum((x - sma) ** 2 for x in window) / period) ** 0.5
                
                middle.append(sma)
                upper.append(sma + 2 * std)
                lower.append(sma - 2 * std)
        
        return {'middle': middle, 'upper': upper, 'lower': lower}
    
    def _ema_crossover(self, data: List, i: int) -> Optional[str]:
        """EMA Crossover Strategy"""
        if i < 26:
            return None
        
        ema12 = self._calculate_ema(data[:i+1], 12)
        ema26 = self._calculate_ema(data[:i+1], 26)
        
        if ema12[-1] is None or ema26[-1] is None:
            return None
        
        # Current crossover
        if ema12[-1] > ema26[-1] and ema12[-2] <= ema26[-2]:
            return 'BUY'
        elif ema12[-1] < ema26[-1] and ema12[-2] >= ema26[-2]:
            return 'SELL'
        
        return None
    
    def _rsi_reversal(self, data: List, i: int) -> Optional[str]:
        """RSI Reversal Strategy"""
        if i < 15:
            return None
        
        rsi = self._calculate_rsi(data[:i+1])
        
        if rsi[-1] is None:
            return None
        
        # Oversold = BUY, Overbought = SELL
        if rsi[-1] < 30:
            return 'BUY'
        elif rsi[-1] > 70:
            return 'SELL'
        
        return None
    
    def _bollinger_breakout(self, data: List, i: int) -> Optional[str]:
        """Bollinger Breakout Strategy"""
        if i < 20:
            return None
        
        bb = self._calculate_bollinger(data[:i+1])
        
        if bb['upper'][-1] is None:
            return None
        
        current_price = data[i]['close']
        
        if current_price > bb['upper'][-1]:
            return 'BUY'
        elif current_price < bb['lower'][-1]:
            return 'SELL'
        
        return None
    
    def _macd_momentum(self, data: List, i: int) -> Optional[str]:
        """MACD Momentum Strategy"""
        if i < 26:
            return None
        
        ema12 = self._calculate_ema(data[:i+1], 12)
        ema26 = self._calculate_ema(data[:i+1], 26)
        
        if ema12[-1] is None or ema26[-1] is None:
            return None
        
        macd = ema12[-1] - ema26[-1]
        signal = self._calculate_ema([{'close': macd}], 9)[-1]
        
        if macd > signal and macd > 0:
            return 'BUY'
        elif macd < signal and macd < 0:
            return 'SELL'
        
        return None
    
    def run(self, strategy: str, symbol: str = 'NIFTY', days: int = 30,
            quantity: int = 50) -> Dict:
        """
        Run backtest
        Args:
            strategy: Strategy name (EMA_CROSSOVER, RSI_REVERSAL, etc.)
            symbol: Trading symbol
            days: Number of days to backtest
            quantity: Trade quantity
        Returns: Performance metrics
        """
        # Reset
        self.capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = [self.initial_capital]
        
        if strategy not in self.strategies:
            return {'error': f'Unknown strategy: {strategy}'}
        
        # Generate data
        data = self._generate_mock_data(symbol, days)
        strategy_fn = self.strategies[strategy]
        
        # Run backtest
        position = None
        
        for i in range(50, len(data)):  # Start after warmup
            signal = strategy_fn(data, i)
            
            if signal == 'BUY' and position is None:
                # Buy
                cost = data[i]['close'] * quantity
                if cost <= self.capital:
                    position = {
                        'entry': data[i]['close'],
                        'entry_time': data[i]['timestamp'],
                        'quantity': quantity
                    }
                    self.capital -= cost
            
            elif signal == 'SELL' and position is not None:
                # Sell
                proceeds = data[i]['close'] * position['quantity']
                pnl = proceeds - (position['entry'] * position['quantity'])
                
                self.trades.append({
                    'entry': position['entry'],
                    'exit': data[i]['close'],
                    'pnl': pnl,
                    'return': pnl / (position['entry'] * position['quantity']) * 100,
                    'entry_time': position['entry_time'],
                    'exit_time': data[i]['timestamp']
                })
                
                self.capital += proceeds
                position = None
            
            # Track equity
            if position:
                current_value = self.capital + (position['entry'] * position['quantity'])
            else:
                current_value = self.capital
            self.equity_curve.append(current_value)
        
        # Calculate metrics
        return self._calculate_metrics()
    
    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'profit': 0,
                'win_rate': 0,
                'sharpe_ratio': 0
            }
        
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        
        total_pnl = sum(t['pnl'] for t in self.trades)
        profit = (total_pnl / self.initial_capital) * 100
        
        win_rate = len(winning_trades) / len(self.trades) * 100
        
        # Average returns
        avg_win = sum(t['return'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['return'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Sharpe ratio (simplified)
        returns = [t['return'] for t in self.trades]
        if len(returns) > 1:
            mean_return = sum(returns) / len(returns)
            std_return = (sum((r - mean_return) ** 2 for r in returns) / len(returns)) ** 0.5
            sharpe = mean_return / std_return if std_return > 0 else 0
        else:
            sharpe = 0
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in winning_trades)
        gross_loss = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Max drawdown
        peak = self.equity_curve[0]
        max_dd = 0
        for value in self.equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate, 2),
            'profit': round(profit, 2),
            'total_pnl': round(total_pnl, 2),
            'sharpe_ratio': round(sharpe, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_dd, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'final_capital': round(self.capital, 2)
        }
    
    def print_results(self, results: Dict):
        """Print formatted results"""
        print("\n" + "="*50)
        print("BACKTEST RESULTS")
        print("="*50)
        print(f"Total Trades    : {results['total_trades']}")
        print(f"Win Rate       : {results['win_rate']}%")
        print(f"Profit         : {results['profit']}%")
        print(f"Total P&L      : ₹{results['total_pnl']}")
        print(f"Sharpe Ratio   : {results['sharpe_ratio']}")
        print(f"Profit Factor  : {results['profit_factor']}")
        print(f"Max Drawdown   : {results['max_drawdown']}%")
        print(f"Final Capital  : ₹{results['final_capital']}")
        print("="*50)


# Standalone function
def run_backtest(strategy: str = 'EMA_CROSSOVER', symbol: str = 'NIFTY', days: int = 30):
    """Quick backtest"""
    bt = Backtester()
    results = bt.run(strategy, symbol, days)
    bt.print_results(results)
    return results


if __name__ == '__main__':
    run_backtest()

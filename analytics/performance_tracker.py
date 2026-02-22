"""
Performance Tracker Module
Calculates key performance metrics from a list of trades
"""

import pandas as pd
import numpy as np

class PerformanceTracker:
    """
    Calculates trading performance metrics from a DataFrame of trades
    """
    
    def __init__(self, trades_df: pd.DataFrame):
        """
        Initialize with a DataFrame of trades
        
        Args:
            trades_df: DataFrame from TradeDatabase
        """
        self.df = trades_df if not trades_df.empty else pd.DataFrame()
        self.metrics = {}
    
    def calculate_all(self) -> dict:
        """Calculate all performance metrics"""
        if self.df.empty:
            return self.get_empty_metrics()
            
        # Basic metrics
        self.metrics['total_trades'] = len(self.df)
        self.metrics['winning_trades'] = len(self.df[self.df['pnl'] > 0])
        self.metrics['losing_trades'] = len(self.df[self.df['pnl'] < 0])
        self.metrics['breakeven_trades'] = len(self.df[self.df['pnl'] == 0])
        
        self.metrics['win_rate'] = (
            (self.metrics['winning_trades'] / self.metrics['total_trades']) * 100
            if self.metrics['total_trades'] > 0 else 0
        )
        
        # P&L metrics
        self.metrics['total_profit'] = self.df[self.df['pnl'] > 0]['pnl'].sum()
        self.metrics['total_loss'] = self.df[self.df['pnl'] < 0]['pnl'].sum()
        self.metrics['net_pnl'] = self.df['pnl'].sum()
        
        # Advanced metrics
        self.metrics['profit_factor'] = (
            self.metrics['total_profit'] / abs(self.metrics['total_loss'])
            if self.metrics['total_loss'] != 0 else 0
        )
        
        self.metrics['avg_win'] = (
            self.metrics['total_profit'] / self.metrics['winning_trades']
            if self.metrics['winning_trades'] > 0 else 0
        )
        
        self.metrics['avg_loss'] = (
            abs(self.metrics['total_loss'] / self.metrics['losing_trades'])
            if self.metrics['losing_trades'] > 0 else 0
        )
        
        self.metrics['expectancy'] = (
            (self.metrics['win_rate'] / 100 * self.metrics['avg_win']) -
            ((1 - self.metrics['win_rate'] / 100) * self.metrics['avg_loss'])
            if self.metrics['total_trades'] > 0 else 0
        )
        
        # Best/Worst
        self.metrics['best_trade'] = self.df['pnl'].max()
        self.metrics['worst_trade'] = self.df['pnl'].min()
        
        # Risk metrics
        self.metrics['max_drawdown'], self.metrics['max_drawdown_percent'] = self._calculate_max_drawdown()
        self.metrics['sharpe_ratio'] = self._calculate_sharpe_ratio()
        
        return self.metrics
    
    def _calculate_max_drawdown(self, initial_capital: float = 100000.0) -> (float, float):
        """Calculate max drawdown in absolute and percentage terms"""
        if self.df.empty:
            return 0.0, 0.0
            
        equity_curve = self.df['pnl'].cumsum() + initial_capital
        peak = equity_curve.expanding(min_periods=1).max()
        drawdown = equity_curve - peak
        
        max_drawdown_value = drawdown.min()
        max_drawdown_percent = (
            (max_drawdown_value / peak[drawdown.idxmin()]) * 100
            if peak[drawdown.idxmin()] != 0 else 0
        )
        
        return abs(max_drawdown_value), abs(max_drawdown_percent)
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
        """Calculate annualized Sharpe ratio"""
        if self.df.empty or self.df['pnl'].std() == 0:
            return 0.0
            
        daily_returns = self.df.set_index('exit_time')['pnl_percent'] / 100
        excess_returns = daily_returns - (risk_free_rate / periods_per_year)
        
        sharpe_ratio = (
            excess_returns.mean() / excess_returns.std() * np.sqrt(periods_per_year)
            if excess_returns.std() != 0 else 0
        )
        
        return sharpe_ratio if not np.isnan(sharpe_ratio) else 0.0
        
    @staticmethod
    def get_empty_metrics():
        """Return a dictionary with zeroed-out metrics for when there are no trades"""
        return {
            'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
            'breakeven_trades': 0, 'win_rate': 0.0, 'total_profit': 0.0,
            'total_loss': 0.0, 'net_pnl': 0.0, 'profit_factor': 0.0,
            'avg_win': 0.0, 'avg_loss': 0.0, 'expectancy': 0.0,
            'best_trade': 0.0, 'worst_trade': 0.0, 'max_drawdown': 0.0,
            'max_drawdown_percent': 0.0, 'sharpe_ratio': 0.0
        }

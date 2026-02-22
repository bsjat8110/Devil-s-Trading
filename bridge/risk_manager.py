"""
Advanced Risk Management Module for Devil's Trading System
Handles position sizing, stop loss, daily limits, and drawdown protection
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from pathlib import Path


class RiskManager:
    """Advanced risk management for trading"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), '..', '.env')
        self.settings = self._load_settings()
        
        # Risk parameters
        self.max_daily_loss = float(self.settings.get('MAX_DAILY_LOSS', 5000))
        self.max_position_size = float(self.settings.get('MAX_POSITION_SIZE', 100000))
        self.default_stop_loss_percent = float(self.settings.get('DEFAULT_STOP_LOSS_PERCENT', 1))
        self.max_drawdown_percent = float(self.settings.get('MAX_DRAWDOWN_PERCENT', 10))
        
        # Track daily P&L
        self.daily_pnl_file = Path(__file__).parent.parent / 'data' / 'daily_pnl.json'
        self._init_daily_pnl()
    
    def _load_settings(self) -> Dict:
        """Load settings from .env file"""
        settings = {}
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        settings[key] = value
        return settings
    
    def _init_daily_pnl(self):
        """Initialize daily P&L tracking"""
        if not self.daily_pnl_file.exists():
            self.daily_pnl_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_daily_pnl({'date': datetime.now().strftime('%Y-%m-%d'), 'pnl': 0, 'trades': []})
    
    def _load_daily_pnl(self) -> Dict:
        """Load today's P&L"""
        try:
            with open(self.daily_pnl_file) as f:
                data = json.load(f)
            today = datetime.now().strftime('%Y-%m-%d')
            if data.get('date') != today:
                # New day, reset
                return {'date': today, 'pnl': 0, 'trades': []}
            return data
        except:
            return {'date': datetime.now().strftime('%Y-%m-%d'), 'pnl': 0, 'trades': []}
    
    def _save_daily_pnl(self, data: Dict):
        """Save daily P&L"""
        with open(self.daily_pnl_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def check_risk_limits(self) -> Tuple[bool, str]:
        """
        Check if trading is allowed based on risk limits
        Returns: (can_trade: bool, reason: str)
        """
        daily_data = self._load_daily_pnl()
        current_pnl = daily_data.get('pnl', 0)
        
        # Check daily loss limit
        if current_pnl <= -self.max_daily_loss:
            return False, f"Daily loss limit reached: {current_pnl}/{self.max_daily_loss}"
        
        # Check drawdown
        initial_capital = float(self.settings.get('INITIAL_CAPITAL', 100000))
        current_capital = initial_capital + current_pnl
        drawdown = (initial_capital - current_capital) / initial_capital * 100
        
        if drawdown >= self.max_drawdown_percent:
            return False, f"Max drawdown reached: {drawdown:.2f}%"
        
        return True, "Risk checks passed"
    
    def calculate_position_size(self, capital: float, risk_percent: float = 2) -> float:
        """
        Calculate position size based on risk percentage
        Args:
            capital: Total capital available
            risk_percent: Risk per trade (default 2%)
        Returns: Position size in rupees
        """
        # Don't exceed max position size
        max_size = min(self.max_position_size, capital * 0.2)  # Max 20% of capital
        risk_amount = capital * (risk_percent / 100)
        
        return min(risk_amount, max_size)
    
    def calculate_stop_loss(self, entry_price: float, risk_percent: float = None, 
                          is_buy: bool = True) -> float:
        """
        Calculate stop loss price
        Args:
            entry_price: Entry price of the trade
            risk_percent: Risk percentage (default from settings)
            is_buy: True for BUY, False for SELL
        Returns: Stop loss price
        """
        if risk_percent is None:
            risk_percent = self.default_stop_loss_percent
        
        sl_distance = entry_price * (risk_percent / 100)
        
        if is_buy:
            return round(entry_price - sl_distance, 2)
        else:
            return round(entry_price + sl_distance, 2)
    
    def calculate_target(self, entry_price: float, reward_percent: float = 3,
                       is_buy: bool = True) -> float:
        """
        Calculate profit target (risk:reward 1:3)
        Args:
            entry_price: Entry price
            reward_percent: Target profit percentage
            is_buy: True for BUY, False for SELL
        Returns: Target price
        """
        target_distance = entry_price * (reward_percent / 100)
        
        if is_buy:
            return round(entry_price + target_distance, 2)
        else:
            return round(entry_price - target_distance, 2)
    
    def record_trade(self, symbol: str, action: str, quantity: int, 
                    entry_price: float, exit_price: float = None):
        """Record a trade for P&L tracking"""
        daily_data = self._load_daily_pnl()
        
        pnl = 0
        if exit_price:
            if action.upper() == 'BUY':
                pnl = (exit_price - entry_price) * quantity
            else:
                pnl = (entry_price - exit_price) * quantity
        
        daily_data['pnl'] = daily_data.get('pnl', 0) + pnl
        daily_data['trades'].append({
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'entry': entry_price,
            'exit': exit_price,
            'pnl': pnl,
            'time': datetime.now().isoformat()
        })
        
        self._save_daily_pnl(daily_data)
    
    def get_daily_summary(self) -> Dict:
        """Get today's trading summary"""
        daily_data = self._load_daily_pnl()
        return {
            'date': daily_data.get('date'),
            'pnl': daily_data.get('pnl', 0),
            'total_trades': len(daily_data.get('trades', [])),
            'winning_trades': len([t for t in daily_data.get('trades', []) if t.get('pnl', 0) > 0]),
            'losing_trades': len([t for t in daily_data.get('trades', []) if t.get('pnl', 0) < 0]),
            'remaining_loss_limit': self.max_daily_loss + daily_data.get('pnl', 0)
        }


# Standalone functions for easy use
def check_risk_limits():
    """Quick risk check"""
    rm = RiskManager()
    return rm.check_risk_limits()

def calculate_position_size(capital: float, risk_percent: float = 2):
    """Quick position size calculation"""
    rm = RiskManager()
    return rm.calculate_position_size(capital, risk_percent)

def get_daily_summary():
    """Get today's summary"""
    rm = RiskManager()
    return rm.get_daily_summary()


if __name__ == '__main__':
    rm = RiskManager()
    print("=== Risk Manager ===")
    can_trade, reason = rm.check_risk_limits()
    print(f"Can trade: {can_trade}")
    print(f"Reason: {reason}")
    print(f"\nDaily Summary: {rm.get_daily_summary()}")

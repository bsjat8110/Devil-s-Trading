"""
Portfolio Management System
Manage multiple strategies, capital allocation, risk management
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class StrategyAllocation:
    """Strategy allocation details"""
    strategy_name: str
    allocated_capital: float
    max_risk_per_trade: float
    max_positions: int
    current_positions: int = 0
    current_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    is_active: bool = True


@dataclass
class PortfolioPosition:
    """Portfolio position"""
    position_id: str
    strategy_name: str
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    entry_time: datetime
    stop_loss: float
    target: float
    pnl: float
    pnl_pct: float


class PortfolioManager:
    """
    Manage entire trading portfolio with multiple strategies
    """
    
    def __init__(self, total_capital: float, max_risk_per_strategy: float = 0.02):
        """
        total_capital: Total portfolio capital
        max_risk_per_strategy: Max risk per strategy (2% default)
        """
        self.total_capital = total_capital
        self.available_capital = total_capital
        self.max_risk_per_strategy = max_risk_per_strategy
        
        self.strategy_allocations: Dict[str, StrategyAllocation] = {}
        self.active_positions: Dict[str, PortfolioPosition] = {}
        self.closed_positions: List[PortfolioPosition] = []
        
        self.portfolio_history = []
        self.equity_curve = []
        
    def add_strategy(
        self,
        strategy_name: str,
        allocation_pct: float,
        max_positions: int = 3,
        risk_per_trade_pct: float = 1.0
    ):
        """
        Add strategy to portfolio
        
        allocation_pct: Percentage of capital to allocate (0-100)
        max_positions: Maximum concurrent positions
        risk_per_trade_pct: Risk per trade as % of allocated capital
        """
        if allocation_pct <= 0 or allocation_pct > 100:
            raise ValueError("Allocation must be between 0 and 100")
        
        allocated_capital = self.total_capital * (allocation_pct / 100)
        
        allocation = StrategyAllocation(
            strategy_name=strategy_name,
            allocated_capital=allocated_capital,
            max_risk_per_trade=allocated_capital * (risk_per_trade_pct / 100),
            max_positions=max_positions
        )
        
        self.strategy_allocations[strategy_name] = allocation
        logger.info(f"Added strategy {strategy_name}: ₹{allocated_capital:,.2f} ({allocation_pct}%)")
        
    def can_open_position(self, strategy_name: str) -> bool:
        """Check if strategy can open new position"""
        if strategy_name not in self.strategy_allocations:
            return False
        
        allocation = self.strategy_allocations[strategy_name]
        
        if not allocation.is_active:
            return False
        
        if allocation.current_positions >= allocation.max_positions:
            return False
        
        return True
    
    def calculate_position_size(
        self,
        strategy_name: str,
        entry_price: float,
        stop_loss: float
    ) -> int:
        """
        Calculate optimal position size based on risk
        """
        if strategy_name not in self.strategy_allocations:
            return 0
        
        allocation = self.strategy_allocations[strategy_name]
        
        # Risk per trade
        risk_amount = allocation.max_risk_per_trade
        
        # Distance to stop loss
        sl_distance = abs(entry_price - stop_loss)
        
        if sl_distance == 0:
            return 0
        
        # Position size
        quantity = int(risk_amount / sl_distance)
        
        # Don't risk more than available capital
        max_quantity = int(allocation.allocated_capital / entry_price)
        
        return min(quantity, max_quantity)
    
    def open_position(
        self,
        strategy_name: str,
        symbol: str,
        quantity: int,
        entry_price: float,
        stop_loss: float,
        target: float
    ) -> Optional[str]:
        """
        Open new position
        Returns position_id if successful
        """
        if not self.can_open_position(strategy_name):
            logger.warning(f"Cannot open position for {strategy_name}")
            return None
        
        # Generate position ID
        position_id = f"{strategy_name}_{symbol}_{int(datetime.now().timestamp())}"
        
        position = PortfolioPosition(
            position_id=position_id,
            strategy_name=strategy_name,
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            target=target,
            pnl=0.0,
            pnl_pct=0.0
        )
        
        self.active_positions[position_id] = position
        
        # Update strategy allocation
        self.strategy_allocations[strategy_name].current_positions += 1
        self.strategy_allocations[strategy_name].total_trades += 1
        
        # Update available capital
        self.available_capital -= entry_price * quantity
        
        logger.info(f"Opened position: {position_id} - {quantity} x {symbol} @ ₹{entry_price}")
        
        return position_id
    
    def close_position(
        self,
        position_id: str,
        exit_price: float,
        reason: str = "Manual close"
    ) -> Optional[float]:
        """
        Close position
        Returns P&L
        """
        if position_id not in self.active_positions:
            logger.warning(f"Position {position_id} not found")
            return None
        
        position = self.active_positions[position_id]
        
        # Calculate P&L
        pnl = (exit_price - position.entry_price) * position.quantity
        pnl_pct = (exit_price - position.entry_price) / position.entry_price * 100
        
        position.current_price = exit_price
        position.pnl = pnl
        position.pnl_pct = pnl_pct
        
        # Update strategy allocation
        allocation = self.strategy_allocations[position.strategy_name]
        allocation.current_positions -= 1
        allocation.current_pnl += pnl
        
        if pnl > 0:
            allocation.winning_trades += 1
        
        # Move to closed positions
        self.closed_positions.append(position)
        del self.active_positions[position_id]
        
        # Update available capital
        self.available_capital += exit_price * position.quantity
        
        logger.info(f"Closed position: {position_id} - P&L: ₹{pnl:,.2f} ({pnl_pct:.2f}%)")
        
        return pnl
    
    def update_positions(self, price_data: Dict[str, float]):
        """
        Update all active positions with current prices
        
        price_data: {'SYMBOL': current_price}
        """
        for position in self.active_positions.values():
            if position.symbol in price_data:
                current_price = price_data[position.symbol]
                position.current_price = current_price
                position.pnl = (current_price - position.entry_price) * position.quantity
                position.pnl_pct = (current_price - position.entry_price) / position.entry_price * 100
    
    def check_stop_loss_targets(self) -> List[str]:
        """
        Check all positions for stop loss or target hits
        Returns list of position_ids to close
        """
        to_close = []
        
        for position_id, position in self.active_positions.items():
            # Stop loss hit
            if position.current_price <= position.stop_loss:
                logger.warning(f"Stop loss hit for {position_id}")
                to_close.append((position_id, position.current_price, "Stop Loss"))
            
            # Target hit
            elif position.current_price >= position.target:
                logger.info(f"Target hit for {position_id}")
                to_close.append((position_id, position.current_price, "Target"))
        
        return to_close
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get complete portfolio summary
        """
        total_pnl = sum(p.pnl for p in self.active_positions.values())
        total_pnl += sum(p.pnl for p in self.closed_positions)
        
        current_equity = self.available_capital + sum(
            p.current_price * p.quantity for p in self.active_positions.values()
        )
        
        total_return_pct = (current_equity - self.total_capital) / self.total_capital * 100
        
        # Strategy-wise breakdown
        strategy_summary = {}
        for name, allocation in self.strategy_allocations.items():
            win_rate = (allocation.winning_trades / allocation.total_trades * 100) if allocation.total_trades > 0 else 0
            
            strategy_summary[name] = {
                'allocated_capital': allocation.allocated_capital,
                'current_positions': allocation.current_positions,
                'total_trades': allocation.total_trades,
                'winning_trades': allocation.winning_trades,
                'win_rate': win_rate,
                'current_pnl': allocation.current_pnl,
                'is_active': allocation.is_active
            }
        
        return {
            'total_capital': self.total_capital,
            'current_equity': current_equity,
            'available_capital': self.available_capital,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'active_positions': len(self.active_positions),
            'total_closed_trades': len(self.closed_positions),
            'strategy_summary': strategy_summary
        }
    
    def get_risk_metrics(self) -> Dict:
        """
        Calculate portfolio risk metrics
        """
        if not self.closed_positions:
            return {
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0
            }
        
        # Calculate metrics from closed positions
        pnls = [p.pnl for p in self.closed_positions]
        
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        gross_profit = sum(wins)
        gross_loss = sum(losses)
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Max drawdown
        cumulative_pnl = np.cumsum(pnls)
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = cumulative_pnl - running_max
        max_drawdown = np.min(drawdown)
        
        # Sharpe ratio (simplified)
        returns = np.array(pnls)
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        return {
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }
    
    def rebalance_strategies(self):
        """
        Rebalance capital allocation across strategies
        Based on performance
        """
        logger.info("Rebalancing portfolio...")
        
        # Calculate performance scores
        scores = {}
        for name, allocation in self.strategy_allocations.items():
            if allocation.total_trades == 0:
                scores[name] = 1.0  # Neutral score
                continue
            
            win_rate = allocation.winning_trades / allocation.total_trades
            pnl_ratio = allocation.current_pnl / allocation.allocated_capital
            
            # Performance score (0-2)
            score = win_rate + pnl_ratio
            scores[name] = max(0.5, min(score, 2.0))  # Clamp between 0.5 and 2.0
        
        # Reallocate based on scores
        total_score = sum(scores.values())
        
        for name, score in scores.items():
            new_allocation_pct = (score / total_score) * 100
            new_allocated_capital = self.total_capital * (new_allocation_pct / 100)
            
            old_capital = self.strategy_allocations[name].allocated_capital
            
            self.strategy_allocations[name].allocated_capital = new_allocated_capital
            self.strategy_allocations[name].max_risk_per_trade = new_allocated_capital * 0.01
            
            logger.info(
                f"Rebalanced {name}: ₹{old_capital:,.0f} → ₹{new_allocated_capital:,.0f} "
                f"({new_allocation_pct:.1f}%)"
            )
    
    def generate_report(self) -> str:
        """
        Generate comprehensive portfolio report
        """
        summary = self.get_portfolio_summary()
        risk_metrics = self.get_risk_metrics()
        
        report = []
        report.append("=" * 90)
        report.append("PORTFOLIO MANAGEMENT REPORT")
        report.append("=" * 90)
        report.append("")
        
        # Portfolio overview
        report.append("💼 PORTFOLIO OVERVIEW:")
        report.append("-" * 90)
        report.append(f"   Total Capital:      ₹{summary['total_capital']:,.2f}")
        report.append(f"   Current Equity:     ₹{summary['current_equity']:,.2f}")
        report.append(f"   Available Capital:  ₹{summary['available_capital']:,.2f}")
        report.append(f"   Total P&L:          ₹{summary['total_pnl']:,.2f} ({summary['total_return_pct']:.2f}%)")
        report.append(f"   Active Positions:   {summary['active_positions']}")
        report.append(f"   Closed Trades:      {summary['total_closed_trades']}")
        report.append("")
        
        # Risk metrics
        report.append("⚠️  RISK METRICS:")
        report.append("-" * 90)
        report.append(f"   Max Drawdown:       ₹{risk_metrics['max_drawdown']:,.2f}")
        report.append(f"   Sharpe Ratio:       {risk_metrics['sharpe_ratio']:.2f}")
        report.append(f"   Profit Factor:      {risk_metrics['profit_factor']:.2f}")
        report.append(f"   Avg Win:            ₹{risk_metrics['avg_win']:,.2f}")
        report.append(f"   Avg Loss:           ₹{risk_metrics['avg_loss']:,.2f}")
        report.append("")
        
        # Strategy breakdown
        report.append("📊 STRATEGY BREAKDOWN:")
        report.append("-" * 90)
        for name, stats in summary['strategy_summary'].items():
            status = "🟢 ACTIVE" if stats['is_active'] else "🔴 INACTIVE"
            report.append(f"\n{status} {name}")
            report.append(f"   Allocated Capital:  ₹{stats['allocated_capital']:,.2f}")
            report.append(f"   Current Positions:  {stats['current_positions']}")
            report.append(f"   Total Trades:       {stats['total_trades']}")
            report.append(f"   Win Rate:           {stats['win_rate']:.1f}%")
            report.append(f"   Strategy P&L:       ₹{stats['current_pnl']:,.2f}")
        
        report.append("")
        
        # Active positions
        if self.active_positions:
            report.append("📈 ACTIVE POSITIONS:")
            report.append("-" * 90)
            for position in self.active_positions.values():
                pnl_emoji = "🟢" if position.pnl > 0 else "🔴"
                report.append(f"{pnl_emoji} {position.symbol} ({position.strategy_name})")
                report.append(f"   Entry: ₹{position.entry_price:.2f} | Current: ₹{position.current_price:.2f}")
                report.append(f"   P&L: ₹{position.pnl:,.2f} ({position.pnl_pct:.2f}%)")
                report.append(f"   SL: ₹{position.stop_loss:.2f} | Target: ₹{position.target:.2f}")
                report.append("")
        
        report.append("=" * 90)
        
        return "\n".join(report)


if __name__ == "__main__":
    print("💼 Testing Portfolio Manager...\n")
    
    # Create portfolio
    portfolio = PortfolioManager(total_capital=500000)
    
    # Add strategies
    portfolio.add_strategy("EMA Crossover", allocation_pct=30, max_positions=2)
    portfolio.add_strategy("RSI Reversal", allocation_pct=25, max_positions=3)
    portfolio.add_strategy("Bollinger Breakout", allocation_pct=25, max_positions=2)
    portfolio.add_strategy("MACD Momentum", allocation_pct=20, max_positions=2)
    
    print("\n📊 Initial Portfolio Setup:")
    print(portfolio.generate_report())
    
    # Simulate some trades
    print("\n📈 Simulating trades...")
    
    # Open positions
    portfolio.open_position("EMA Crossover", "NIFTY", 50, 23000, 22800, 23400)
    portfolio.open_position("RSI Reversal", "BANKNIFTY", 20, 45000, 44500, 45800)
    
    # Update prices
    portfolio.update_positions({"NIFTY": 23200, "BANKNIFTY": 45300})
    
    # Close one position
    portfolio.close_position(
        list(portfolio.active_positions.keys())[0],
        23200,
        "Target"
    )
    
    print("\n📊 Portfolio After Trades:")
    print(portfolio.generate_report())

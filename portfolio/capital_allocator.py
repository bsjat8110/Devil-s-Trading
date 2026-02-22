"""
Capital Allocation Optimizer
Smart capital distribution across strategies
"""

import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class CapitalAllocator:
    """
    Optimize capital allocation across strategies
    """
    
    def __init__(self):
        self.allocation_history = []
        
    def equal_weight(self, total_capital: float, num_strategies: int) -> List[float]:
        """Equal weight allocation"""
        allocation_pct = 100 / num_strategies
        return [allocation_pct] * num_strategies
    
    def performance_based(
        self,
        total_capital: float,
        strategy_performance: Dict[str, Dict]
    ) -> Dict[str, float]:
        """
        Allocate based on past performance
        
        strategy_performance: {
            'strategy_name': {
                'win_rate': float,
                'avg_return': float,
                'sharpe_ratio': float
            }
        }
        """
        
        scores = {}
        
        for name, perf in strategy_performance.items():
            # Performance score (0-1)
            win_rate_score = perf.get('win_rate', 50) / 100
            return_score = max(0, min(1, (perf.get('avg_return', 0) + 10) / 20))
            sharpe_score = max(0, min(1, (perf.get('sharpe_ratio', 0) + 1) / 3))
            
            # Weighted average
            score = (win_rate_score * 0.4 + return_score * 0.3 + sharpe_score * 0.3)
            scores[name] = max(0.1, score)  # Minimum 10% score
        
        # Normalize to 100%
        total_score = sum(scores.values())
        allocations = {name: (score / total_score) * 100 for name, score in scores.items()}
        
        return allocations
    
    def risk_parity(
        self,
        total_capital: float,
        strategy_volatilities: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Risk parity allocation
        Allocate inversely to volatility
        
        strategy_volatilities: {'strategy_name': volatility}
        """
        
        # Inverse volatility weights
        inv_vols = {name: 1 / vol if vol > 0 else 1 for name, vol in strategy_volatilities.items()}
        
        total_inv_vol = sum(inv_vols.values())
        
        allocations = {name: (inv_vol / total_inv_vol) * 100 for name, inv_vol in inv_vols.items()}
        
        return allocations
    
    def kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate optimal bet size using Kelly Criterion
        
        Returns: Optimal allocation percentage (0-100)
        """
        if avg_loss == 0:
            return 0
        
        win_loss_ratio = avg_win / avg_loss
        
        # Kelly formula: f = (p * b - q) / b
        # where p = win rate, q = 1 - p, b = win/loss ratio
        kelly_pct = ((win_rate / 100) * win_loss_ratio - (1 - win_rate / 100)) / win_loss_ratio
        
        # Use fractional Kelly (50%) for safety
        fractional_kelly = kelly_pct * 0.5
        
        # Clamp between 0 and 25%
        return max(0, min(25, fractional_kelly * 100))


if __name__ == "__main__":
    print("💰 Testing Capital Allocator...\n")
    
    allocator = CapitalAllocator()
    
    # Test 1: Equal weight
    print("1️⃣  EQUAL WEIGHT ALLOCATION")
    print("-" * 60)
    equal = allocator.equal_weight(500000, 4)
    for i, alloc in enumerate(equal, 1):
        print(f"Strategy {i}: {alloc:.1f}%")
    
    # Test 2: Performance-based
    print("\n2️⃣  PERFORMANCE-BASED ALLOCATION")
    print("-" * 60)
    
    performance = {
        'EMA Crossover': {'win_rate': 65, 'avg_return': 5, 'sharpe_ratio': 1.5},
        'RSI Reversal': {'win_rate': 58, 'avg_return': 3, 'sharpe_ratio': 1.2},
        'Bollinger Breakout': {'win_rate': 62, 'avg_return': 4, 'sharpe_ratio': 1.4},
        'MACD Momentum': {'win_rate': 60, 'avg_return': 3.5, 'sharpe_ratio': 1.3}
    }
    
    perf_alloc = allocator.performance_based(500000, performance)
    for name, alloc in perf_alloc.items():
        print(f"{name}: {alloc:.1f}%")
    
    # Test 3: Risk parity
    print("\n3️⃣  RISK PARITY ALLOCATION")
    print("-" * 60)
    
    volatilities = {
        'EMA Crossover': 0.15,
        'RSI Reversal': 0.20,
        'Bollinger Breakout': 0.18,
        'MACD Momentum': 0.16
    }
    
    risk_alloc = allocator.risk_parity(500000, volatilities)
    for name, alloc in risk_alloc.items():
        print(f"{name}: {alloc:.1f}%")
    
    # Test 4: Kelly Criterion
    print("\n4️⃣  KELLY CRITERION")
    print("-" * 60)
    
    kelly = allocator.kelly_criterion(win_rate=60, avg_win=1500, avg_loss=1000)
    print(f"Optimal allocation: {kelly:.1f}%")

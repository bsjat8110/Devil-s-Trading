"""
Smart Order Execution Engine
TWAP, VWAP, Iceberg, and other advanced execution algorithms
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """Execution strategy types"""
    MARKET = "market"
    TWAP = "twap"
    VWAP = "vwap"
    ICEBERG = "iceberg"
    LIMIT = "limit"


@dataclass
class ExecutionResult:
    """Result of order execution"""
    strategy: ExecutionStrategy
    total_quantity: int
    filled_quantity: int
    avg_execution_price: float
    slices: List[Dict]
    total_slippage: float
    status: Enum
    execution_time: float


class OrderStatus(Enum):
    """Order status"""
    pending = "pending"
    partial = "partial"
    filled = "filled"
    cancelled = "cancelled"
    rejected = "rejected"


class SmartExecutor:
    """
    Smart order execution with multiple algorithms
    """
    
    def __init__(self, commission_per_trade: float = 20):
        """
        commission_per_trade: Commission per order in INR
        """
        self.commission = commission_per_trade
        self.execution_history = []
        
    def execute_market(
        self,
        symbol: str,
        quantity: int,
        side: str,
        price: float
    ) -> ExecutionResult:
        """
        Simple market order execution
        
        side: 'BUY' or 'SELL'
        """
        
        logger.info(f"Executing MARKET order: {side} {quantity} {symbol} @ ₹{price}")
        
        start_time = time.time()
        
        # Simulate market slippage (0.1%)
        slippage_pct = 0.001
        if side == 'BUY':
            execution_price = price * (1 + slippage_pct)
        else:
            execution_price = price * (1 - slippage_pct)
        
        slice_info = {
            'slice_num': 1,
            'quantity': quantity,
            'price': execution_price,
            'timestamp': datetime.now()
        }
        
        result = ExecutionResult(
            strategy=ExecutionStrategy.MARKET,
            total_quantity=quantity,
            filled_quantity=quantity,
            avg_execution_price=execution_price,
            slices=[slice_info],
            total_slippage=abs(execution_price - price) * quantity,
            status=OrderStatus.filled,
            execution_time=time.time() - start_time
        )
        
        self.execution_history.append(result)
        
        logger.info(f"✅ MARKET order filled @ ₹{execution_price:.2f}")
        
        return result
    
    def execute_twap(
        self,
        symbol: str,
        quantity: int,
        side: str,
        price: float,
        duration_minutes: int = 30,
        num_slices: int = 10
    ) -> ExecutionResult:
        """
        Time-Weighted Average Price execution
        Splits order evenly over time
        
        duration_minutes: Total time to execute order
        num_slices: Number of order slices
        """
        
        logger.info(f"Starting TWAP execution: {side} {quantity} {symbol} over {duration_minutes}min in {num_slices} slices")
        
        start_time = time.time()
        
        slice_size = quantity // num_slices
        remaining = quantity % num_slices
        
        slices = []
        total_cost = 0
        filled = 0
        
        for i in range(num_slices):
            # Slice quantity
            slice_qty = slice_size + (1 if i < remaining else 0)
            
            # Simulate price movement
            price_variation = np.random.randn() * 0.001  # 0.1% random variation
            execution_price = price * (1 + price_variation)
            
            # Add market impact (decreases with each slice)
            impact = 0.0005 * (1 - i / num_slices)
            if side == 'BUY':
                execution_price *= (1 + impact)
            else:
                execution_price *= (1 - impact)
            
            slice_info = {
                'slice_num': i + 1,
                'quantity': slice_qty,
                'price': execution_price,
                'timestamp': datetime.now() + timedelta(minutes=i * duration_minutes / num_slices)
            }
            
            slices.append(slice_info)
            total_cost += execution_price * slice_qty
            filled += slice_qty
            
            logger.info(f"TWAP slice {i+1}: {slice_qty} @ ₹{execution_price:.2f}")
        
        avg_price = total_cost / filled if filled > 0 else 0
        
        result = ExecutionResult(
            strategy=ExecutionStrategy.TWAP,
            total_quantity=quantity,
            filled_quantity=filled,
            avg_execution_price=avg_price,
            slices=slices,
            total_slippage=abs(avg_price - price) * filled,
            status=OrderStatus.filled,
            execution_time=time.time() - start_time
        )
        
        self.execution_history.append(result)
        
        logger.info(f"✅ TWAP execution complete. Avg price: ₹{avg_price:.2f}")
        
        return result
    
    def execute_vwap(
        self,
        symbol: str,
        quantity: int,
        side: str,
        price: float,
        historical_volume: pd.DataFrame,
        num_slices: int = 8
    ) -> ExecutionResult:
        """
        Volume-Weighted Average Price execution
        Follows historical volume pattern
        
        historical_volume: DataFrame with 'volume' column
        num_slices: Number of order slices
        """
        
        logger.info(f"Starting VWAP execution: {side} {quantity} {symbol} in {num_slices} volume-weighted slices")
        
        start_time = time.time()
        
        # Calculate volume distribution
        if historical_volume.empty:
            # Fallback to equal distribution
            volume_pcts = [1/num_slices] * num_slices
        else:
            recent_volume = historical_volume['volume'].tail(num_slices).values
            volume_pcts = recent_volume / recent_volume.sum()
        
        slices = []
        total_cost = 0
        filled = 0
        
        for i in range(num_slices):
            # Slice quantity based on volume
            slice_qty = int(quantity * volume_pcts[i])
            
            if slice_qty == 0:
                continue
            
            # Simulate price movement
            price_variation = np.random.randn() * 0.001
            execution_price = price * (1 + price_variation)
            
            # Market impact proportional to slice size
            impact = (slice_qty / quantity) * 0.001
            if side == 'BUY':
                execution_price *= (1 + impact)
            else:
                execution_price *= (1 - impact)
            
            slice_info = {
                'slice_num': i + 1,
                'quantity': slice_qty,
                'price': execution_price,
                'volume_pct': volume_pcts[i] * 100,
                'timestamp': datetime.now()
            }
            
            slices.append(slice_info)
            total_cost += execution_price * slice_qty
            filled += slice_qty
            
            logger.info(f"VWAP slice {i+1}: {slice_qty} @ ₹{execution_price:.2f} (Vol%: {volume_pcts[i]*100:.1f}%)")
        
        # Fill remaining quantity
        if filled < quantity:
            remaining_qty = quantity - filled
            execution_price = price
            
            slice_info = {
                'slice_num': num_slices + 1,
                'quantity': remaining_qty,
                'price': execution_price,
                'volume_pct': 0,
                'timestamp': datetime.now()
            }
            
            slices.append(slice_info)
            total_cost += execution_price * remaining_qty
            filled += remaining_qty
        
        avg_price = total_cost / filled if filled > 0 else 0
        
        result = ExecutionResult(
            strategy=ExecutionStrategy.VWAP,
            total_quantity=quantity,
            filled_quantity=filled,
            avg_execution_price=avg_price,
            slices=slices,
            total_slippage=abs(avg_price - price) * filled,
            status=OrderStatus.filled,
            execution_time=time.time() - start_time
        )
        
        self.execution_history.append(result)
        
        logger.info(f"✅ VWAP execution complete. Avg price: ₹{avg_price:.2f}")
        
        return result
    
    def execute_iceberg(
        self,
        symbol: str,
        quantity: int,
        side: str,
        price: float,
        visible_quantity: int = None,
        num_slices: int = 5
    ) -> ExecutionResult:
        """
        Iceberg order execution
        Hides true order size by showing only small portion
        
        visible_quantity: Quantity visible to market (default: 20% of total)
        num_slices: Number of hidden slices
        """
        
        if visible_quantity is None:
            visible_quantity = max(1, quantity // 5)  # 20% visible
        
        logger.info(f"Starting ICEBERG execution: {side} {quantity} {symbol} (showing only {visible_quantity})")
        
        start_time = time.time()
        
        slice_size = quantity // num_slices
        remaining = quantity % num_slices
        
        slices = []
        total_cost = 0
        filled = 0
        
        for i in range(num_slices):
            slice_qty = slice_size + (1 if i < remaining else 0)
            
            # Reduced market impact due to hidden size
            price_variation = np.random.randn() * 0.0005  # Less price impact
            execution_price = price * (1 + price_variation)
            
            # Very small impact since size is hidden
            impact = 0.0001 * (visible_quantity / quantity)
            if side == 'BUY':
                execution_price *= (1 + impact)
            else:
                execution_price *= (1 - impact)
            
            slice_info = {
                'slice_num': i + 1,
                'quantity': slice_qty,
                'visible_quantity': min(slice_qty, visible_quantity),
                'price': execution_price,
                'timestamp': datetime.now()
            }
            
            slices.append(slice_info)
            total_cost += execution_price * slice_qty
            filled += slice_qty
            
            logger.info(f"Iceberg slice {i+1}: {slice_qty} (visible: {slice_info['visible_quantity']}) @ ₹{execution_price:.2f}")
        
        avg_price = total_cost / filled if filled > 0 else 0
        
        result = ExecutionResult(
            strategy=ExecutionStrategy.ICEBERG,
            total_quantity=quantity,
            filled_quantity=filled,
            avg_execution_price=avg_price,
            slices=slices,
            total_slippage=abs(avg_price - price) * filled,
            status=OrderStatus.filled,
            execution_time=time.time() - start_time
        )
        
        self.execution_history.append(result)
        
        logger.info(f"✅ ICEBERG execution complete. Avg price: ₹{avg_price:.2f}")
        
        return result
    
    def get_execution_summary(self) -> Dict:
        """Get summary of all executions"""
        
        if not self.execution_history:
            return {}
        
        total_executions = len(self.execution_history)
        total_quantity = sum(r.filled_quantity for r in self.execution_history)
        total_slippage = sum(r.total_slippage for r in self.execution_history)
        avg_execution_time = np.mean([r.execution_time for r in self.execution_history])
        
        strategy_counts = {}
        for result in self.execution_history:
            strategy = result.strategy.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            'total_executions': total_executions,
            'total_quantity': total_quantity,
            'total_slippage': total_slippage,
            'avg_slippage_per_order': total_slippage / total_executions if total_executions > 0 else 0,
            'avg_execution_time': avg_execution_time,
            'strategy_breakdown': strategy_counts
        }


if __name__ == "__main__":
    print("⚡ Testing Smart Executor...\n")
    
    executor = SmartExecutor()
    
    # Test 1: Market order
    print("1️⃣  MARKET ORDER")
    print("-" * 60)
    result = executor.execute_market('NIFTY', 50, 'BUY', 23450)
    print(f"Filled: {result.filled_quantity} @ ₹{result.avg_execution_price:.2f}")
    print(f"Slippage: ₹{result.total_slippage:.2f}\n")
    
    # Test 2: TWAP
    print("2️⃣  TWAP ORDER")
    print("-" * 60)
    result = executor.execute_twap('NIFTY', 100, 'BUY', 23450, duration_minutes=30, num_slices=10)
    print(f"Filled: {result.filled_quantity} @ ₹{result.avg_execution_price:.2f}")
    print(f"Slippage: ₹{result.total_slippage:.2f}\n")
    
    # Test 3: VWAP
    print("3️⃣  VWAP ORDER")
    print("-" * 60)
    
    # Create sample volume data
    sample_volume = pd.DataFrame({
        'volume': np.random.randint(100000, 500000, 10)
    })
    
    result = executor.execute_vwap('NIFTY', 100, 'BUY', 23450, sample_volume, num_slices=8)
    print(f"Filled: {result.filled_quantity} @ ₹{result.avg_execution_price:.2f}")
    print(f"Slippage: ₹{result.total_slippage:.2f}\n")
    
    # Test 4: Iceberg
    print("4️⃣  ICEBERG ORDER")
    print("-" * 60)
    result = executor.execute_iceberg('NIFTY', 200, 'BUY', 23450, visible_quantity=40, num_slices=5)
    print(f"Filled: {result.filled_quantity} @ ₹{result.avg_execution_price:.2f}")
    print(f"Slippage: ₹{result.total_slippage:.2f}\n")
    
    # Summary
    print("📊 EXECUTION SUMMARY")
    print("=" * 60)
    summary = executor.get_execution_summary()
    print(f"Total Executions: {summary['total_executions']}")
    print(f"Total Quantity: {summary['total_quantity']}")
    print(f"Total Slippage: ₹{summary['total_slippage']:.2f}")
    print(f"Avg Slippage: ₹{summary['avg_slippage_per_order']:.2f}")

"""
Slippage Optimization Engine
Analyzes and minimizes execution slippage
"""

import pandas as pd
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class SlippageOptimizer:
    """
    Optimize order execution to minimize slippage
    """
    
    def __init__(self):
        self.historical_data = []
        
    def estimate_market_impact(
        self,
        order_size: int,
        avg_daily_volume: int,
        volatility: float
    ) -> float:
        """
        Estimate market impact of an order
        
        order_size: Order quantity
        avg_daily_volume: Average daily trading volume
        volatility: Historical volatility (%)
        
        Returns: Estimated slippage in %
        """
        
        # Order size as % of daily volume
        size_pct = (order_size / avg_daily_volume) * 100
        
        # Kyle's Lambda model (simplified)
        # Impact = volatility * sqrt(order_size / avg_volume)
        impact = volatility * np.sqrt(size_pct / 100) * 0.1
        
        return impact
    
    def recommend_execution_strategy(
        self,
        order_size: int,
        avg_daily_volume: int,
        volatility: float,
        urgency: str = 'normal'
    ) -> Dict:
        """
        Recommend best execution strategy
        
        urgency: 'low', 'normal', 'high'
        """
        
        # Calculate metrics
        size_pct = (order_size / avg_daily_volume) * 100
        estimated_impact = self.estimate_market_impact(order_size, avg_daily_volume, volatility)
        
        # Decision logic
        if urgency == 'high':
            if size_pct < 1:
                strategy = 'MARKET'
                reason = 'Small order with high urgency - use market order'
            else:
                strategy = 'ICEBERG'
                reason = 'Large urgent order - use iceberg to hide size'
        
        elif size_pct < 0.5:
            strategy = 'MARKET'
            reason = 'Very small order relative to volume - low impact expected'
        
        elif size_pct < 2:
            strategy = 'TWAP'
            reason = 'Medium order - spread over time with TWAP'
        
        elif size_pct < 5:
            strategy = 'VWAP'
            reason = 'Large order - follow volume pattern with VWAP'
        
        else:
            strategy = 'ICEBERG'
            reason = 'Very large order - hide size with iceberg'
        
        # Optimal parameters
        if strategy == 'TWAP':
            num_slices = min(20, max(5, int(size_pct * 2)))
            duration = min(60, max(10, int(size_pct * 10)))
            params = {
                'num_slices': num_slices,
                'duration_minutes': duration
            }
        
        elif strategy == 'VWAP':
            num_slices = min(15, max(5, int(size_pct * 1.5)))
            params = {
                'num_slices': num_slices
            }
        
        elif strategy == 'ICEBERG':
            visible_pct = max(10, min(30, 100 / size_pct))
            num_slices = min(10, max(3, int(size_pct)))
            params = {
                'visible_pct': visible_pct,
                'num_slices': num_slices
            }
        
        else:
            params = {}
        
        return {
            'recommended_strategy': strategy,
            'reason': reason,
            'estimated_impact_pct': round(estimated_impact, 4),
            'size_vs_volume_pct': round(size_pct, 2),
            'parameters': params
        }
    
    def analyze_execution_quality(
        self,
        entry_price: float,
        execution_price: float,
        quantity: int,
        strategy: str
    ) -> Dict:
        """
        Analyze quality of execution
        """
        
        slippage = abs(execution_price - entry_price)
        slippage_pct = (slippage / entry_price) * 100
        total_slippage_cost = slippage * quantity
        
        # Quality score (0-100)
        if slippage_pct < 0.05:
            quality = 'Excellent'
            score = 100
        elif slippage_pct < 0.1:
            quality = 'Good'
            score = 80
        elif slippage_pct < 0.2:
            quality = 'Fair'
            score = 60
        elif slippage_pct < 0.5:
            quality = 'Poor'
            score = 40
        else:
            quality = 'Very Poor'
            score = 20
        
        result = {
            'slippage': slippage,
            'slippage_pct': round(slippage_pct, 4),
            'total_cost': total_slippage_cost,
            'quality': quality,
            'score': score,
            'strategy': strategy
        }
        
        self.historical_data.append(result)
        
        return result
    
    def get_optimization_suggestions(self) -> Dict:
        """
        Get suggestions to improve execution quality
        """
        
        if not self.historical_data:
            return {'message': 'No execution data available'}
        
        df = pd.DataFrame(self.historical_data)
        
        avg_slippage = df['slippage_pct'].mean()
        worst_slippage = df['slippage_pct'].max()
        best_strategy = df.groupby('strategy')['score'].mean().idxmax()
        
        suggestions = []
        
        if avg_slippage > 0.2:
            suggestions.append("Consider using TWAP/VWAP for better execution")
        
        if worst_slippage > 0.5:
            suggestions.append("Avoid market orders during volatile periods")
        
        suggestions.append(f"Best performing strategy: {best_strategy}")
        
        return {
            'avg_slippage_pct': round(avg_slippage, 4),
            'worst_slippage_pct': round(worst_slippage, 4),
            'best_strategy': best_strategy,
            'suggestions': suggestions
        }


if __name__ == "__main__":
    print("🎯 Testing Slippage Optimizer...\n")
    
    optimizer = SlippageOptimizer()
    
    # Test different scenarios
    scenarios = [
        {'size': 50, 'volume': 1000000, 'volatility': 1.5, 'urgency': 'normal'},
        {'size': 500, 'volume': 1000000, 'volatility': 2.0, 'urgency': 'normal'},
        {'size': 5000, 'volume': 1000000, 'volatility': 1.8, 'urgency': 'low'},
        {'size': 2000, 'volume': 1000000, 'volatility': 2.5, 'urgency': 'high'},
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}️⃣  SCENARIO {i}")
        print("-" * 70)
        print(f"Order Size: {scenario['size']}")
        print(f"Avg Daily Volume: {scenario['volume']:,}")
        print(f"Volatility: {scenario['volatility']}%")
        print(f"Urgency: {scenario['urgency']}")
        
        recommendation = optimizer.recommend_execution_strategy(
            scenario['size'],
            scenario['volume'],
            scenario['volatility'],
            scenario['urgency']
        )
        
        print(f"\n💡 RECOMMENDATION: {recommendation['recommended_strategy']}")
        print(f"Reason: {recommendation['reason']}")
        print(f"Estimated Impact: {recommendation['estimated_impact_pct']}%")
        print(f"Size vs Volume: {recommendation['size_vs_volume_pct']:.2f}%")
        
        if recommendation['parameters']:
            print(f"Parameters: {recommendation['parameters']}")
        
        print()
    
    # Analyze some executions
    print("📊 EXECUTION QUALITY ANALYSIS")
    print("=" * 70)
    
    optimizer.analyze_execution_quality(23450, 23455, 50, 'MARKET')
    optimizer.analyze_execution_quality(23450, 23452, 100, 'TWAP')
    optimizer.analyze_execution_quality(23450, 23451, 200, 'VWAP')
    
    suggestions = optimizer.get_optimization_suggestions()
    
    print(f"Avg Slippage: {suggestions['avg_slippage_pct']}%")
    print(f"Best Strategy: {suggestions['best_strategy']}")
    print(f"\n💡 Suggestions:")
    for suggestion in suggestions['suggestions']:
        print(f"   • {suggestion}")

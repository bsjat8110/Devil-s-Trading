"""
Strategy A/B Testing and Comparison
Compare multiple strategies scientifically
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class StrategyComparison:
    """
    Compare and test multiple trading strategies
    """
    
    def __init__(self):
        self.strategies = {}
        
    def add_strategy(self, name: str, trades: pd.DataFrame):
        """
        Add strategy for comparison
        
        trades: DataFrame with columns ['pnl', 'return_pct', 'timestamp']
        """
        self.strategies[name] = trades
        logger.info(f"Added strategy '{name}' with {len(trades)} trades")
    
    def calculate_metrics(self, trades: pd.DataFrame) -> Dict:
        """Calculate performance metrics for a strategy"""
        
        if trades.empty:
            return {}
        
        pnls = trades['pnl'].values
        returns = trades['return_pct'].values
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = (pnls > 0).sum()
        losing_trades = (pnls < 0).sum()
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = pnls.sum()
        avg_win = pnls[pnls > 0].mean() if winning_trades > 0 else 0
        avg_loss = abs(pnls[pnls < 0].mean()) if losing_trades > 0 else 0
        
        # Risk metrics
        gross_profit = pnls[pnls > 0].sum()
        gross_loss = abs(pnls[pnls < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Sharpe ratio (annualized)
        if len(returns) > 1:
            sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        else:
            sharpe = 0
        
        # Drawdown
        cumulative = np.cumsum(pnls)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_drawdown = np.min(drawdown)
        
        # Expectancy
        expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * avg_loss)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'expectancy': expectancy
        }
    
    def compare_strategies(self) -> pd.DataFrame:
        """Compare all strategies"""
        
        comparison = []
        
        for name, trades in self.strategies.items():
            metrics = self.calculate_metrics(trades)
            metrics['strategy'] = name
            comparison.append(metrics)
        
        df = pd.DataFrame(comparison)
        
        if not df.empty:
            df = df.set_index('strategy')
        
        return df
    
    def run_statistical_test(self, strategy1: str, strategy2: str) -> Dict:
        """
        Run statistical t-test to compare two strategies
        """
        
        if strategy1 not in self.strategies or strategy2 not in self.strategies:
            logger.error("One or both strategies not found")
            return {}
        
        returns1 = self.strategies[strategy1]['return_pct'].values
        returns2 = self.strategies[strategy2]['return_pct'].values
        
        # T-test
        t_stat, p_value = stats.ttest_ind(returns1, returns2)
        
        # Effect size (Cohen's d)
        mean_diff = returns1.mean() - returns2.mean()
        pooled_std = np.sqrt((returns1.std()**2 + returns2.std()**2) / 2)
        cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0
        
        # Determine significance
        is_significant = p_value < 0.05
        
        better_strategy = strategy1 if returns1.mean() > returns2.mean() else strategy2
        
        return {
            'strategy1': strategy1,
            'strategy2': strategy2,
            'mean_return_1': returns1.mean(),
            'mean_return_2': returns2.mean(),
            't_statistic': t_stat,
            'p_value': p_value,
            'is_significant': is_significant,
            'cohens_d': cohens_d,
            'better_strategy': better_strategy,
            'confidence': (1 - p_value) * 100 if is_significant else 0
        }
    
    def generate_comparison_report(self) -> str:
        """Generate comparison report"""
        
        report = []
        report.append("=" * 80)
        report.append("STRATEGY COMPARISON REPORT")
        report.append("=" * 80)
        
        comparison = self.compare_strategies()
        
        if comparison.empty:
            report.append("\nNo strategies to compare")
            return "\n".join(report)
        
        report.append(f"\n📊 STRATEGIES COMPARED: {len(comparison)}")
        report.append("")
        
        for strategy in comparison.index:
            metrics = comparison.loc[strategy]
            
            report.append(f"🎯 {strategy.upper()}")
            report.append("-" * 80)
            report.append(f"   Total Trades: {int(metrics['total_trades'])}")
            report.append(f"   Win Rate: {metrics['win_rate']:.2f}%")
            report.append(f"   Total P&L: ₹{metrics['total_pnl']:,.2f}")
            report.append(f"   Profit Factor: {metrics['profit_factor']:.2f}")
            report.append(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            report.append(f"   Max Drawdown: ₹{metrics['max_drawdown']:,.2f}")
            report.append(f"   Expectancy: ₹{metrics['expectancy']:,.2f}")
            report.append("")
        
        # Ranking
        report.append("🏆 RANKING BY SHARPE RATIO:")
        report.append("-" * 80)
        ranked = comparison.sort_values('sharpe_ratio', ascending=False)
        for i, (strategy, row) in enumerate(ranked.iterrows(), 1):
            report.append(f"   {i}. {strategy}: {row['sharpe_ratio']:.2f}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


if __name__ == "__main__":
    print("📊 Testing Strategy Comparison...\n")
    
    # Generate sample data for 2 strategies
    np.random.seed(42)
    
    strategy1_trades = pd.DataFrame({
        'pnl': np.random.randn(100) * 1000 + 200,
        'return_pct': np.random.randn(100) * 2 + 0.8,
        'timestamp': pd.date_range(end=pd.Timestamp.now(), periods=100)
    })
    
    strategy2_trades = pd.DataFrame({
        'pnl': np.random.randn(80) * 800 + 150,
        'return_pct': np.random.randn(80) * 1.5 + 0.5,
        'timestamp': pd.date_range(end=pd.Timestamp.now(), periods=80)
    })
    
    # Compare
    comparison = StrategyComparison()
    comparison.add_strategy("EMA Crossover", strategy1_trades)
    comparison.add_strategy("RSI Reversal", strategy2_trades)
    
    print(comparison.generate_comparison_report())
    
    # Statistical test
    test_result = comparison.run_statistical_test("EMA Crossover", "RSI Reversal")
    
    print(f"\n🧪 STATISTICAL TEST:")
    print(f"   Better Strategy: {test_result['better_strategy']}")
    print(f"   P-Value: {test_result['p_value']:.4f}")
    print(f"   Significant: {test_result['is_significant']}")
    print(f"   Confidence: {test_result['confidence']:.1f}%")

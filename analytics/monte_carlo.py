"""
Monte Carlo Simulation for Strategy Analysis
Simulates thousands of potential outcomes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class StrategyMonteCarloSimulator:
    """
    Monte Carlo simulation for trading strategies
    """
    
    def __init__(self, trade_history: pd.DataFrame):
        """
        trade_history: DataFrame with columns ['pnl', 'return_pct', 'timestamp']
        """
        self.trade_history = trade_history
        self.simulations = None
        
    def run_simulation(
        self,
        num_simulations: int = 10000,
        num_trades: int = 252,
        initial_capital: float = 100000
    ) -> Dict:
        """
        Run Monte Carlo simulation
        
        num_simulations: Number of simulation runs
        num_trades: Number of trades per simulation
        initial_capital: Starting capital
        """
        
        if self.trade_history.empty:
            logger.warning("No trade history available")
            return {}
        
        # Extract returns
        returns = self.trade_history['return_pct'].dropna().values
        
        if len(returns) == 0:
            logger.warning("No valid returns in history")
            return {}
        
        # Calculate statistics
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        logger.info(f"Running {num_simulations} simulations with {num_trades} trades each...")
        
        # Run simulations
        simulation_results = []
        
        for _ in range(num_simulations):
            # Generate random returns based on historical distribution
            simulated_returns = np.random.normal(mean_return, std_return, num_trades)
            
            # Calculate equity curve
            equity = initial_capital * np.cumprod(1 + simulated_returns / 100)
            
            final_equity = equity[-1]
            max_equity = np.max(equity)
            min_equity = np.min(equity)
            
            # Calculate drawdown
            running_max = np.maximum.accumulate(equity)
            drawdown = (equity - running_max) / running_max * 100
            max_drawdown = np.min(drawdown)
            
            simulation_results.append({
                'final_equity': final_equity,
                'total_return': (final_equity - initial_capital) / initial_capital * 100,
                'max_drawdown': max_drawdown,
                'max_equity': max_equity,
                'min_equity': min_equity,
                'equity_curve': equity
            })
        
        self.simulations = pd.DataFrame(simulation_results)
        
        # Calculate statistics
        results = {
            'num_simulations': num_simulations,
            'initial_capital': initial_capital,
            
            # Expected outcomes
            'mean_final_equity': self.simulations['final_equity'].mean(),
            'median_final_equity': self.simulations['final_equity'].median(),
            'mean_return': self.simulations['total_return'].mean(),
            'median_return': self.simulations['total_return'].median(),
            
            # Risk metrics
            'mean_max_drawdown': self.simulations['max_drawdown'].mean(),
            'worst_drawdown': self.simulations['max_drawdown'].min(),
            
            # Probability analysis
            'prob_profit': (self.simulations['total_return'] > 0).sum() / num_simulations * 100,
            'prob_10pct_gain': (self.simulations['total_return'] > 10).sum() / num_simulations * 100,
            'prob_20pct_gain': (self.simulations['total_return'] > 20).sum() / num_simulations * 100,
            'prob_10pct_loss': (self.simulations['total_return'] < -10).sum() / num_simulations * 100,
            'prob_20pct_loss': (self.simulations['total_return'] < -20).sum() / num_simulations * 100,
            
            # Percentiles
            'return_5th_percentile': np.percentile(self.simulations['total_return'], 5),
            'return_25th_percentile': np.percentile(self.simulations['total_return'], 25),
            'return_50th_percentile': np.percentile(self.simulations['total_return'], 50),
            'return_75th_percentile': np.percentile(self.simulations['total_return'], 75),
            'return_95th_percentile': np.percentile(self.simulations['total_return'], 95),
            
            # Best/worst cases
            'best_case_return': self.simulations['total_return'].max(),
            'worst_case_return': self.simulations['total_return'].min(),
        }
        
        logger.info(f"✅ Simulation complete. Probability of profit: {results['prob_profit']:.1f}%")
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate Monte Carlo report"""
        
        if not results:
            return "No simulation results available"
        
        report = []
        report.append("=" * 80)
        report.append("MONTE CARLO SIMULATION RESULTS")
        report.append("=" * 80)
        
        report.append(f"\n📊 SIMULATION PARAMETERS:")
        report.append(f"   Number of Simulations: {results['num_simulations']:,}")
        report.append(f"   Initial Capital: ₹{results['initial_capital']:,.2f}")
        
        report.append(f"\n💰 EXPECTED OUTCOMES:")
        report.append(f"   Mean Final Equity: ₹{results['mean_final_equity']:,.2f}")
        report.append(f"   Median Final Equity: ₹{results['median_final_equity']:,.2f}")
        report.append(f"   Mean Return: {results['mean_return']:.2f}%")
        report.append(f"   Median Return: {results['median_return']:.2f}%")
        
        report.append(f"\n⚠️  RISK METRICS:")
        report.append(f"   Mean Max Drawdown: {results['mean_max_drawdown']:.2f}%")
        report.append(f"   Worst Drawdown: {results['worst_drawdown']:.2f}%")
        
        report.append(f"\n📈 PROBABILITY ANALYSIS:")
        report.append(f"   Probability of Profit: {results['prob_profit']:.1f}%")
        report.append(f"   Probability of >10% Gain: {results['prob_10pct_gain']:.1f}%")
        report.append(f"   Probability of >20% Gain: {results['prob_20pct_gain']:.1f}%")
        report.append(f"   Probability of >10% Loss: {results['prob_10pct_loss']:.1f}%")
        report.append(f"   Probability of >20% Loss: {results['prob_20pct_loss']:.1f}%")
        
        report.append(f"\n📊 RETURN DISTRIBUTION (Percentiles):")
        report.append(f"   5th Percentile (Very Bad): {results['return_5th_percentile']:.2f}%")
        report.append(f"   25th Percentile (Bad): {results['return_25th_percentile']:.2f}%")
        report.append(f"   50th Percentile (Median): {results['return_50th_percentile']:.2f}%")
        report.append(f"   75th Percentile (Good): {results['return_75th_percentile']:.2f}%")
        report.append(f"   95th Percentile (Very Good): {results['return_95th_percentile']:.2f}%")
        
        report.append(f"\n🎯 BEST/WORST CASES:")
        report.append(f"   Best Case Return: {results['best_case_return']:.2f}%")
        report.append(f"   Worst Case Return: {results['worst_case_return']:.2f}%")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)


if __name__ == "__main__":
    # Test with sample data
    print("🎲 Testing Monte Carlo Simulator...\n")
    
    # Generate sample trade history
    np.random.seed(42)
    sample_trades = pd.DataFrame({
        'pnl': np.random.randn(100) * 1000,
        'return_pct': np.random.randn(100) * 2 + 0.5,
        'timestamp': pd.date_range(end=pd.Timestamp.now(), periods=100)
    })
    
    # Run simulation
    simulator = StrategyMonteCarloSimulator(sample_trades)
    results = simulator.run_simulation(num_simulations=5000, num_trades=252, initial_capital=100000)
    
    print(simulator.generate_report(results))

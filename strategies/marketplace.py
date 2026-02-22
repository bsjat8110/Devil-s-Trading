"""
Strategy Marketplace
Manage and compare multiple strategies
"""

import pandas as pd
from typing import Dict, List
from strategies.ema_crossover import EMACrossoverStrategy
from strategies.rsi_reversal import RSIReversalStrategy
from strategies.bollinger_breakout import BollingerBreakoutStrategy
from strategies.macd_momentum import MACDMomentumStrategy


class StrategyMarketplace:
    """
    Marketplace for all trading strategies
    """
    
    def __init__(self):
        self.strategies = {
            'ema_crossover': EMACrossoverStrategy(),
            'rsi_reversal': RSIReversalStrategy(),
            'bollinger_breakout': BollingerBreakoutStrategy(),
            'macd_momentum': MACDMomentumStrategy()
        }
        
    def get_all_signals(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Get signals from all strategies"""
        
        signals = {}
        
        for name, strategy in self.strategies.items():
            signals[name] = strategy.generate_signal(df)
        
        return signals
    
    def get_consensus_signal(self, df: pd.DataFrame, current_price: float) -> Dict:
        """
        Get consensus signal from all strategies
        """
        
        signals = self.get_all_signals(df)
        
        buy_count = sum(1 for s in signals.values() if s['signal'] == 'BUY')
        sell_count = sum(1 for s in signals.values() if s['signal'] == 'SELL')
        neutral_count = sum(1 for s in signals.values() if s['signal'] == 'NEUTRAL')
        
        total_strategies = len(signals)
        
        # Weighted strength
        buy_strength = sum(s['strength'] for s in signals.values() if s['signal'] == 'BUY')
        sell_strength = sum(s['strength'] for s in signals.values() if s['signal'] == 'SELL')
        
        # Determine consensus
        if buy_count > sell_count:
            consensus = 'BUY'
            agreement = (buy_count / total_strategies) * 100
            avg_strength = buy_strength / buy_count if buy_count > 0 else 0
        elif sell_count > buy_count:
            consensus = 'SELL'
            agreement = (sell_count / total_strategies) * 100
            avg_strength = sell_strength / sell_count if sell_count > 0 else 0
        else:
            consensus = 'HOLD'
            agreement = (neutral_count / total_strategies) * 100
            avg_strength = 0
        
        # Calculate consensus stop loss and target
        all_stop_losses = [s['stop_loss'] for s in signals.values() if s['stop_loss'] > 0]
        all_targets = [s['target'] for s in signals.values() if s['target'] > 0]
        
        avg_stop_loss = sum(all_stop_losses) / len(all_stop_losses) if all_stop_losses else current_price * 0.98
        avg_target = sum(all_targets) / len(all_targets) if all_targets else current_price * 1.02
        
        return {
            'consensus': consensus,
            'agreement': round(agreement, 2),
            'avg_strength': round(avg_strength, 2),
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'neutral_signals': neutral_count,
            'individual_signals': signals,
            'stop_loss': round(avg_stop_loss, 2),
            'target': round(avg_target, 2)
        }
    
    def compare_strategies(self) -> pd.DataFrame:
        """Compare all strategies"""
        
        comparison = []
        
        for name, strategy in self.strategies.items():
            summary = strategy.get_performance_summary()
            summary['strategy'] = name
            comparison.append(summary)
        
        df = pd.DataFrame(comparison)
        
        if not df.empty:
            df = df.set_index('strategy')
        
        return df

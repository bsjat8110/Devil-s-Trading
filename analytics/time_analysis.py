"""
Time-of-Day Analysis
Find best trading hours
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class TimeOfDayAnalyzer:
    """
    Analyze performance by time of day
    """
    
    def __init__(self, trades: pd.DataFrame):
        """
        trades: DataFrame with 'timestamp' and 'pnl' columns
        """
        self.trades = trades.copy()
        
        if 'timestamp' in self.trades.columns:
            self.trades['hour'] = pd.to_datetime(self.trades['timestamp']).dt.hour
            self.trades['day_of_week'] = pd.to_datetime(self.trades['timestamp']).dt.dayofweek
    
    def analyze_by_hour(self) -> pd.DataFrame:
        """Analyze performance by hour of day"""
        
        if 'hour' not in self.trades.columns:
            return pd.DataFrame()
        
        hourly = self.trades.groupby('hour').agg({
            'pnl': ['count', 'sum', 'mean', 'std'],
            'return_pct': ['mean', 'std']
        }).round(2)
        
        hourly.columns = ['trades', 'total_pnl', 'avg_pnl', 'std_pnl', 'avg_return', 'std_return']
        
        # Win rate
        wins_by_hour = self.trades[self.trades['pnl'] > 0].groupby('hour').size()
        hourly['win_rate'] = (wins_by_hour / hourly['trades'] * 100).fillna(0).round(2)
        
        return hourly
    
    def analyze_by_day(self) -> pd.DataFrame:
        """Analyze performance by day of week"""
        
        if 'day_of_week' not in self.trades.columns:
            return pd.DataFrame()
        
        daily = self.trades.groupby('day_of_week').agg({
            'pnl': ['count', 'sum', 'mean'],
            'return_pct': 'mean'
        }).round(2)
        
        daily.columns = ['trades', 'total_pnl', 'avg_pnl', 'avg_return']
        
        # Map day numbers to names
        day_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday'}
        daily.index = daily.index.map(day_names)
        
        return daily
    
    def get_best_hours(self, top_n: int = 3) -> List[int]:
        """Get best performing hours"""
        
        hourly = self.analyze_by_hour()
        
        if hourly.empty:
            return []
        
        # Filter hours with at least 5 trades
        hourly_filtered = hourly[hourly['trades'] >= 5]
        
        if hourly_filtered.empty:
            return []
        
        best = hourly_filtered.nlargest(top_n, 'avg_pnl')
        return best.index.tolist()
    
    def get_worst_hours(self, bottom_n: int = 3) -> List[int]:
        """Get worst performing hours"""
        
        hourly = self.analyze_by_hour()
        
        if hourly.empty:
            return []
        
        hourly_filtered = hourly[hourly['trades'] >= 5]
        
        if hourly_filtered.empty:
            return []
        
        worst = hourly_filtered.nsmallest(bottom_n, 'avg_pnl')
        return worst.index.tolist()
    
    def generate_report(self) -> str:
        """Generate time analysis report"""
        
        report = []
        report.append("=" * 80)
        report.append("TIME-OF-DAY ANALYSIS")
        report.append("=" * 80)
        
        # Hourly analysis
        hourly = self.analyze_by_hour()
        
        if not hourly.empty:
            report.append("\n⏰ PERFORMANCE BY HOUR:")
            report.append("-" * 80)
            
            for hour, row in hourly.iterrows():
                emoji = "🟢" if row['avg_pnl'] > 0 else "🔴"
                report.append(
                    f"{emoji} {int(hour):02d}:00 | Trades: {int(row['trades']):3d} | "
                    f"Avg P&L: ₹{row['avg_pnl']:7.2f} | Win Rate: {row['win_rate']:.1f}%"
                )
        
        # Best/worst hours
        best_hours = self.get_best_hours()
        worst_hours = self.get_worst_hours()
        
        if best_hours:
            report.append(f"\n🌟 BEST HOURS: {', '.join([f'{h:02d}:00' for h in best_hours])}")
        
        if worst_hours:
            report.append(f"⚠️  WORST HOURS: {', '.join([f'{h:02d}:00' for h in worst_hours])}")
        
        # Daily analysis
        daily = self.analyze_by_day()
        
        if not daily.empty:
            report.append(f"\n📅 PERFORMANCE BY DAY OF WEEK:")
            report.append("-" * 80)
            
            for day, row in daily.iterrows():
                emoji = "🟢" if row['avg_pnl'] > 0 else "🔴"
                # Fixed: Convert day to string explicitly
                day_str = str(day)
                report.append(
                    f"{emoji} {day_str:9s} | Trades: {int(row['trades']):3d} | "
                    f"Total P&L: ₹{row['total_pnl']:8.2f} | Avg: ₹{row['avg_pnl']:6.2f}"
                )
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)


if __name__ == "__main__":
    print("⏰ Testing Time-of-Day Analyzer...\n")
    
    # Generate sample trades
    np.random.seed(42)
    timestamps = pd.date_range(start='2024-01-01', periods=200, freq='1H')
    
    sample_trades = pd.DataFrame({
        'timestamp': timestamps,
        'pnl': np.random.randn(200) * 500 + 100,
        'return_pct': np.random.randn(200) * 2 + 0.5
    })
    
    analyzer = TimeOfDayAnalyzer(sample_trades)
    print(analyzer.generate_report())
    
    print(f"\n🌟 Best trading hours: {analyzer.get_best_hours()}")
    print(f"⚠️  Worst trading hours: {analyzer.get_worst_hours()}")

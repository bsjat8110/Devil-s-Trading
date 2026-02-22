"""
Report Generator Module
Creates CLI reports and exports data
"""

import pandas as pd
from tabulate import tabulate
from datetime import datetime

def generate_cli_report(metrics: dict):
    """
    Display performance metrics in a formatted CLI table
    
    Args:
        metrics: Dictionary of calculated metrics
    """
    
    # Header
    print("═══════════════════════════════════════")
    print("📊 PERFORMANCE ANALYTICS")
    print("═══════════════════════════════════════")
    print(f"Report Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n")
    
    # Overview
    overview_data = [
        ["Total Trades", metrics.get('total_trades', 0)],
        ["Winning Trades", f"{metrics.get('winning_trades', 0)} ({metrics.get('win_rate', 0):.1f}%)"],
        ["Losing Trades", metrics.get('losing_trades', 0)],
        ["Breakeven Trades", metrics.get('breakeven_trades', 0)]
    ]
    print(tabulate(overview_data, tablefmt="plain", colalign=("left", "right")))
    print()
    
    # P&L
    pnl_data = [
        ["Total Profit", f"₹{metrics.get('total_profit', 0):,.2f}"],
        ["Total Loss", f"₹{metrics.get('total_loss', 0):,.2f}"],
        ["Net P&L", f"₹{metrics.get('net_pnl', 0):,.2f}"]
    ]
    print(tabulate(pnl_data, headers=["P&L Breakdown", ""], tablefmt="grid", colalign=("left", "right")))
    print()
    
    # Ratios & Risk
    ratios_data = [
        ["Profit Factor", f"{metrics.get('profit_factor', 0):.2f}"],
        ["Expectancy per Trade", f"₹{metrics.get('expectancy', 0):,.2f}"],
        ["Average Win", f"₹{metrics.get('avg_win', 0):,.2f}"],
        ["Average Loss", f"₹{metrics.get('avg_loss', 0):,.2f}"],
        ["Max Drawdown", f"₹{metrics.get('max_drawdown', 0):,.2f} ({metrics.get('max_drawdown_percent', 0):.1f}%)"],
        ["Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}"]
    ]
    print(tabulate(ratios_data, headers=["Ratios & Risk", ""], tablefmt="grid", colalign=("left", "right")))
    print()
    
    # Best/Worst
    best_worst_data = [
        ["Best Trade", f"₹{metrics.get('best_trade', 0):,.2f}"],
        ["Worst Trade", f"₹{metrics.get('worst_trade', 0):,.2f}"]
    ]
    print(tabulate(best_worst_data, headers=["Extremes", ""], tablefmt="plain", colalign=("left", "right")))
    print("═══════════════════════════════════════\n")

def export_to_csv(trades_df: pd.DataFrame, file_path: str = 'data/trade_report.csv'):
    """
    Export trades DataFrame to a CSV file
    
    Args:
        trades_df: DataFrame of trades
        file_path: Path to save the CSV file
    """
    if trades_df.empty:
        print("No trades to export.")
        return
        
    try:
        trades_df.to_csv(file_path, index=False)
        print(f"✅ Trade report exported successfully to {file_path}")
    except Exception as e:
        print(f"❌ Failed to export report: {e}")

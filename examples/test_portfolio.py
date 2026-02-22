import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio.portfolio_manager import PortfolioManager
from portfolio.capital_allocator import CapitalAllocator

print("=" * 90)
print("TESTING PORTFOLIO MANAGEMENT SYSTEM")
print("=" * 90)

# Initialize portfolio
print("\n💼 Creating portfolio with ₹5,00,000 capital...")
portfolio = PortfolioManager(total_capital=500000)

# Add strategies
print("\n📊 Adding strategies...")
portfolio.add_strategy("EMA Crossover", allocation_pct=30, max_positions=2, risk_per_trade_pct=1.0)
portfolio.add_strategy("RSI Reversal", allocation_pct=25, max_positions=3, risk_per_trade_pct=1.0)
portfolio.add_strategy("Bollinger Breakout", allocation_pct=25, max_positions=2, risk_per_trade_pct=1.0)
portfolio.add_strategy("MACD Momentum", allocation_pct=20, max_positions=2, risk_per_trade_pct=1.0)

print("\n" + portfolio.generate_report())

# Simulate trading
print("\n" + "📈" * 45)
print("SIMULATING TRADING ACTIVITY")
print("📈" * 45 + "\n")

# Open positions
print("Opening positions...")
pos1 = portfolio.open_position("EMA Crossover", "NIFTY", 50, 23000, 22800, 23400)
print(f"✅ Position 1 opened: {pos1}")

pos2 = portfolio.open_position("RSI Reversal", "BANKNIFTY", 20, 45000, 44500, 45800)
print(f"✅ Position 2 opened: {pos2}")

pos3 = portfolio.open_position("Bollinger Breakout", "FINNIFTY", 30, 21500, 21300, 21900)
print(f"✅ Position 3 opened: {pos3}")

# Update prices (simulate market movement)
print("\n📊 Updating market prices...")
portfolio.update_positions({
    "NIFTY": 23200,
    "BANKNIFTY": 45300,
    "FINNIFTY": 21450
})

print("\n" + portfolio.generate_report())

# Check stop loss/targets
print("\n🎯 Checking stop loss and targets...")
to_close = portfolio.check_stop_loss_targets()

if to_close:
    for position_id, price, reason in to_close:
        print(f"⚠️  {reason} triggered for {position_id}")
        portfolio.close_position(position_id, price, reason)
else:
    print("No stop loss or targets hit")

# Close one position manually
print("\n📤 Closing one position manually...")
if portfolio.active_positions:
    first_pos = list(portfolio.active_positions.keys())[0]
    pnl = portfolio.close_position(first_pos, 23200, "Manual close")
    print(f"✅ Closed with P&L: ₹{pnl:,.2f}")

print("\n" + portfolio.generate_report())

# Test capital allocator
print("\n" + "💰" * 45)
print("CAPITAL ALLOCATION OPTIMIZATION")
print("💰" * 45 + "\n")

allocator = CapitalAllocator()

# Performance-based allocation
performance = {
    'EMA Crossover': {'win_rate': 65, 'avg_return': 5, 'sharpe_ratio': 1.5},
    'RSI Reversal': {'win_rate': 58, 'avg_return': 3, 'sharpe_ratio': 1.2},
    'Bollinger Breakout': {'win_rate': 62, 'avg_return': 4, 'sharpe_ratio': 1.4},
    'MACD Momentum': {'win_rate': 60, 'avg_return': 3.5, 'sharpe_ratio': 1.3}
}

print("📊 PERFORMANCE-BASED ALLOCATION:")
print("-" * 90)
perf_alloc = allocator.performance_based(500000, performance)
for name, alloc in perf_alloc.items():
    capital = 500000 * (alloc / 100)
    print(f"   {name:20s}: {alloc:5.1f}% → ₹{capital:,.2f}")

# Risk parity
print("\n📊 RISK PARITY ALLOCATION:")
print("-" * 90)
volatilities = {
    'EMA Crossover': 0.15,
    'RSI Reversal': 0.20,
    'Bollinger Breakout': 0.18,
    'MACD Momentum': 0.16
}

risk_alloc = allocator.risk_parity(500000, volatilities)
for name, alloc in risk_alloc.items():
    capital = 500000 * (alloc / 100)
    print(f"   {name:20s}: {alloc:5.1f}% → ₹{capital:,.2f}")

# Kelly Criterion
print("\n📊 KELLY CRITERION (OPTIMAL BET SIZE):")
print("-" * 90)
kelly = allocator.kelly_criterion(win_rate=60, avg_win=1500, avg_loss=1000)
print(f"   Optimal allocation per trade: {kelly:.1f}%")
print(f"   For ₹5,00,000 portfolio: ₹{500000 * (kelly / 100):,.2f}")

print("\n" + "✅" * 45)
print("PORTFOLIO MANAGEMENT TEST COMPLETED!")
print("✅" * 45)

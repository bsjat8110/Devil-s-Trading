"""
Quick Portfolio Report
"""

from master_system import DevilTradingMasterSystem

system = DevilTradingMasterSystem(500000)

# Setup (same as auto_trader)
system.portfolio.add_strategy("EMA Crossover", 30)
system.portfolio.add_strategy("RSI Reversal", 25)
system.portfolio.add_strategy("Bollinger Breakout", 25)
system.portfolio.add_strategy("MACD Momentum", 20)

# Report
print(system.generate_master_report('NIFTY'))
print("\n" + system.portfolio.generate_report())

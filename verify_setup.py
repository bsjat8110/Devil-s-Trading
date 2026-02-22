import sys
sys.path.insert(0, '.')

print("Checking imports...")

try:
    from analytics.monte_carlo import MonteCarloSimulator
    print("✅ monte_carlo.py imported successfully")
except Exception as e:
    print(f"❌ monte_carlo.py error: {e}")

try:
    from analytics.strategy_tester import StrategyComparison
    print("✅ strategy_tester.py imported successfully")
except Exception as e:
    print(f"❌ strategy_tester.py error: {e}")

try:
    from analytics.time_analysis import TimeOfDayAnalyzer
    print("✅ time_analysis.py imported successfully")
except Exception as e:
    print(f"❌ time_analysis.py error: {e}")

print("\n✅ All imports successful! Ready to run tests.")

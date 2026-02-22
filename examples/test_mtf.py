import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.mtf_analyzer import MultiTimeframeAnalyzer

print("=" * 70)
print("TESTING MULTI-TIMEFRAME ANALYZER")
print("=" * 70)
print()

analyzer = MultiTimeframeAnalyzer('NIFTY')

print("🚀 Running Multi-Timeframe Analysis...\n")

signals = analyzer.analyze_all_timeframes()
zones = analyzer.find_confluence_zones()

print(analyzer.generate_report())

bias = analyzer.get_trading_bias()
print(f"\n💡 TRADING RECOMMENDATION: {bias['bias'].upper()} ({bias['confidence']:.1f}%)")
print(f"📊 Confluence Zones: {len(zones)}")

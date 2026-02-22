"""
Complete Greeks Analytics Test
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analytics.greeks_calculator import GreeksCalculator
from analytics.iv_analyzer import IVAnalyzer
from analytics.option_chain_analyzer import OptionChainAnalyzer
import numpy as np
from datetime import datetime, timedelta


def print_separator(title=""):
    print("\n" + "="*70)
    if title:
        print(f"  {title}")
        print("="*70)
    else:
        print("="*70)


if __name__ == "__main__":
    print_separator("🤖 GREEKS ANALYTICS ENGINE - COMPLETE TEST")
    
    # 1. Greeks Calculator
    print("\n1️⃣  GREEKS CALCULATION")
    print("-" * 70)
    
    calc = GreeksCalculator()
    
    greeks = calc.calculate_all_greeks(
        spot=23485,
        strike=23500,
        expiry_days=7,
        iv=15.8,
        option_type='CE'
    )
    
    print(f"Symbol:         NIFTY23500CE")
    print(f"Spot:           {greeks['spot']}")
    print(f"Strike:         {greeks['strike']}")
    print(f"Days to Expiry: {greeks['expiry_days']}")
    print(f"IV:             {greeks['iv']:.2f}%")
    print()
    print(f"Delta:  {greeks['delta']:.4f}  → {calc.interpret_delta(greeks['delta'])}")
    print(f"Gamma:  {greeks['gamma']:.6f}  → {calc.interpret_gamma(greeks['gamma'])}")
    print(f"Theta:  ₹{greeks['theta']:.2f}/day  → {calc.interpret_theta(greeks['theta'])}")
    print(f"Vega:   ₹{greeks['vega']:.2f}  → {calc.interpret_vega(greeks['vega'])}")
    
    # Position sizing
    print()
    qty = calc.calculate_position_size_with_greeks(
        delta=greeks['delta'],
        capital=100000,
        risk_percent=0.5
    )
    print(f"Recommended Quantity (0.5% risk on ₹1L): {qty} lots")
    
    # 2. IV Analysis
    print_separator("2️⃣  IMPLIED VOLATILITY ANALYSIS")
    
    iv_analyzer = IVAnalyzer()
    
    # Simulate IV history
    print("Simulating 252 days of IV history...")
    for i in range(252):
        days_ago = 252 - i
        iv = 15 + np.random.randn() * 3
        timestamp = datetime.now() - timedelta(days=days_ago)
        iv_analyzer.add_iv_data('NIFTY', iv, timestamp)
    
    current_iv = 18.5
    iv_analysis = iv_analyzer.get_iv_analysis('NIFTY', current_iv)
    
    print()
    print(f"Current IV:      {iv_analysis['current_iv']:.2f}%")
    print(f"IV Percentile:   {iv_analysis['iv_percentile']:.1f}% ({iv_analysis['status']})")
    print(f"IV Rank:         {iv_analysis['iv_rank']:.1f}%")
    print()
    print(f"📝 {iv_analysis['description']}")
    print(f"💡 {iv_analysis['recommendation']}")
    
    # 3. Option Chain Analysis
    print_separator("3️⃣  OPTION CHAIN ANALYSIS")
    
    oc_analyzer = OptionChainAnalyzer()
    
    # PCR Analysis
    total_put_oi = 1250000
    total_call_oi = 1050000
    pcr = oc_analyzer.calculate_pcr(total_put_oi, total_call_oi)
    pcr_interp = oc_analyzer.interpret_pcr(pcr)
    
    print()
    print(f"Total Call OI:   {total_call_oi:,}")
    print(f"Total Put OI:    {total_put_oi:,}")
    print(f"PCR:             {pcr:.2f}")
    print()
    print(f"Sentiment:       {pcr_interp['sentiment']}")
    print(f"Signal:          {pcr_interp['signal']}")
    print(f"📝 {pcr_interp['description']}")
    
    # Gamma Squeeze Detection
    print()
    print("Gamma Squeeze Analysis:")
    print("-" * 70)
    
    option_chain = [
        {'strike': 23000, 'call_oi': 450000, 'put_oi': 320000},
        {'strike': 23200, 'call_oi': 680000, 'put_oi': 550000},
        {'strike': 23400, 'call_oi': 920000, 'put_oi': 780000},
        {'strike': 23500, 'call_oi': 1500000, 'put_oi': 1200000},
        {'strike': 23600, 'call_oi': 850000, 'put_oi': 1600000},
        {'strike': 23800, 'call_oi': 520000, 'put_oi': 980000},
        {'strike': 24000, 'call_oi': 350000, 'put_oi': 1450000},
    ]
    
    gamma_zone = oc_analyzer.detect_gamma_squeeze_zone(option_chain, 23485)
    
    if gamma_zone:
        print(f"Max Call OI Strike: {gamma_zone['max_call_oi_strike']} ({gamma_zone['max_call_oi']:,})")
        print(f"Max Put OI Strike:  {gamma_zone['max_put_oi_strike']} ({gamma_zone['max_put_oi']:,})")
        print(f"Gamma Zone:         {gamma_zone['gamma_zone']}")
        print()
        print("⚠️  Market may face resistance/support in this zone")
    
    # 4. Summary Dashboard
    print_separator("📊 SUMMARY DASHBOARD")
    
    print()
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                    NIFTY GREEKS ANALYTICS                         ║")
    print("╠═══════════════════════════════════════════════════════════════════╣")
    print(f"║  Spot Price:           {greeks['spot']:<45} ║")
    print(f"║  ATM Strike:           {greeks['strike']:<45} ║")
    print(f"║  Days to Expiry:       {greeks['expiry_days']:<45} ║")
    print("╠═══════════════════════════════════════════════════════════════════╣")
    print(f"║  Delta:                {greeks['delta']:.4f} ({calc.interpret_delta(greeks['delta']):<29}) ║")
    print(f"║  Gamma:                {greeks['gamma']:.6f} ({calc.interpret_gamma(greeks['gamma']):<27}) ║")
    print(f"║  Theta:                ₹{greeks['theta']:.2f}/day ({calc.interpret_theta(greeks['theta']):<25}) ║")
    print(f"║  Vega:                 ₹{greeks['vega']:.2f} ({calc.interpret_vega(greeks['vega']):<29}) ║")
    print("╠═══════════════════════════════════════════════════════════════════╣")
    print(f"║  Current IV:           {iv_analysis['current_iv']:.2f}%{'':<41} ║")
    print(f"║  IV Percentile:        {iv_analysis['iv_percentile']:.1f}% ({iv_analysis['status']:<33}) ║")
    print(f"║  IV Rank:              {iv_analysis['iv_rank']:.1f}%{'':<41} ║")
    print("╠═══════════════════════════════════════════════════════════════════╣")
    print(f"║  PCR:                  {pcr:.2f} ({pcr_interp['sentiment']:<35}) ║")
    print(f"║  Gamma Zone:           {gamma_zone['gamma_zone']:<45} ║")
    print("╠═══════════════════════════════════════════════════════════════════╣")
    print(f"║  Recommended Qty:      {qty} lots{'':<41} ║")
    print(f"║  Strategy Hint:        {iv_analysis['recommendation'][:45]:<45} ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    
    print_separator()
    print("✅ GREEKS ANALYTICS TEST COMPLETED!\n")

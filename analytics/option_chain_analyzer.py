"""
Option Chain Analyzer
Analyzes option chain data, calculates PCR, detects gamma zones
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptionChainAnalyzer:
    """
    Analyze option chain data
    """
    
    def __init__(self):
        """Initialize Option Chain Analyzer"""
        logger.info("✅ Option Chain Analyzer initialized")
    
    def calculate_pcr(
        self,
        put_oi: int,
        call_oi: int
    ) -> float:
        """
        Calculate Put-Call Ratio
        
        PCR = Total Put OI / Total Call OI
        
        Args:
            put_oi: Total Put Open Interest
            call_oi: Total Call Open Interest
            
        Returns:
            PCR value
        """
        if call_oi == 0:
            return 0.0
        
        return put_oi / call_oi
    
    def interpret_pcr(self, pcr: float) -> Dict[str, str]:
        """
        Interpret PCR value
        
        Args:
            pcr: Put-Call Ratio
            
        Returns:
            Interpretation dictionary
        """
        if pcr < 0.7:
            return {
                'sentiment': 'BULLISH',
                'description': 'More calls than puts - Market is bullish',
                'signal': 'BUY'
            }
        elif pcr < 1.0:
            return {
                'sentiment': 'NEUTRAL-BULLISH',
                'description': 'Slightly more calls - Mildly bullish',
                'signal': 'HOLD'
            }
        elif pcr < 1.3:
            return {
                'sentiment': 'NEUTRAL-BEARISH',
                'description': 'Slightly more puts - Mildly bearish',
                'signal': 'HOLD'
            }
        else:
            return {
                'sentiment': 'BEARISH',
                'description': 'More puts than calls - Market is bearish',
                'signal': 'SELL'
            }
    
    def detect_gamma_squeeze_zone(
        self,
        option_chain: List[Dict],
        spot_price: float
    ) -> Optional[Dict]:
        """
        Detect gamma squeeze zones
        
        High gamma + high OI = potential squeeze zone
        
        Args:
            option_chain: List of option data dicts
            spot_price: Current spot price
            
        Returns:
            Gamma squeeze zone info or None
        """
        # This is a simplified version
        # In real implementation, you'd get actual gamma values
        
        max_call_oi_strike = None
        max_call_oi = 0
        
        max_put_oi_strike = None
        max_put_oi = 0
        
        for option in option_chain:
            strike = option.get('strike', 0)
            call_oi = option.get('call_oi', 0)
            put_oi = option.get('put_oi', 0)
            
            if call_oi > max_call_oi:
                max_call_oi = call_oi
                max_call_oi_strike = strike
            
            if put_oi > max_put_oi:
                max_put_oi = put_oi
                max_put_oi_strike = strike
        
        if max_call_oi_strike and max_put_oi_strike:
            return {
                'max_call_oi_strike': max_call_oi_strike,
                'max_call_oi': max_call_oi,
                'max_put_oi_strike': max_put_oi_strike,
                'max_put_oi': max_put_oi,
                'gamma_zone': f"{max_put_oi_strike} - {max_call_oi_strike}"
            }
        
        return None
    
    def find_max_pain(self, option_chain: List[Dict]) -> float:
        """
        Calculate Max Pain strike
        
        Max Pain = Strike where most options expire worthless
        
        Args:
            option_chain: List of option data
            
        Returns:
            Max pain strike price
        """
        pain_by_strike = {}
        
        for option in option_chain:
            strike = option.get('strike', 0)
            call_oi = option.get('call_oi', 0)
            put_oi = option.get('put_oi', 0)
            
            if strike not in pain_by_strike:
                pain_by_strike[strike] = 0
            
            # Calculate pain at this strike
            for other_option in option_chain:
                other_strike = other_option.get('strike', 0)
                other_call_oi = other_option.get('call_oi', 0)
                other_put_oi = other_option.get('put_oi', 0)
                
                # Call pain
                if other_strike < strike:
                    pain_by_strike[strike] += (strike - other_strike) * other_call_oi
                
                # Put pain
                if other_strike > strike:
                    pain_by_strike[strike] += (other_strike - strike) * other_put_oi
        
        if pain_by_strike:
            max_pain_strike = min(pain_by_strike, key=pain_by_strike.get)
            return max_pain_strike
        
        return 0.0


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING OPTION CHAIN ANALYZER")
    print("="*60 + "\n")
    
    analyzer = OptionChainAnalyzer()
    
    # Test PCR
    print("1️⃣  Testing PCR Calculation:")
    pcr = analyzer.calculate_pcr(put_oi=1200000, call_oi=1000000)
    interpretation = analyzer.interpret_pcr(pcr)
    
    print(f"   PCR: {pcr:.2f}")
    print(f"   Sentiment: {interpretation['sentiment']}")
    print(f"   Signal: {interpretation['signal']}")
    print()
    
    # Test Gamma Squeeze
    print("2️⃣  Testing Gamma Squeeze Detection:")
    dummy_chain = [
        {'strike': 23000, 'call_oi': 500000, 'put_oi': 300000},
        {'strike': 23500, 'call_oi': 1200000, 'put_oi': 800000},
        {'strike': 24000, 'call_oi': 300000, 'put_oi': 1500000},
    ]
    
    gamma_zone = analyzer.detect_gamma_squeeze_zone(dummy_chain, 23500)
    if gamma_zone:
        print(f"   Max Call OI: {gamma_zone['max_call_oi_strike']} ({gamma_zone['max_call_oi']:,})")
        print(f"   Max Put OI:  {gamma_zone['max_put_oi_strike']} ({gamma_zone['max_put_oi']:,})")
        print(f"   Gamma Zone:  {gamma_zone['gamma_zone']}")
    
    print()
    print("="*60 + "\n")

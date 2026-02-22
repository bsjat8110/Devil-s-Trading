"""
Greeks Calculator Module
Calculates option Greeks using Black-Scholes model
"""

import numpy as np
from scipy.stats import norm
from datetime import datetime
import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GreeksCalculator:
    """
    Calculate option Greeks (Delta, Gamma, Theta, Vega, Rho)
    """
    
    def __init__(self, risk_free_rate: float = 0.07):
        """
        Initialize Greeks calculator
        
        Args:
            risk_free_rate: Annual risk-free rate (default 7% for India)
        """
        self.risk_free_rate = risk_free_rate
        logger.info("✅ Greeks Calculator initialized")
    
    def _d1(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1 for Black-Scholes"""
        return (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    
    def _d2(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d2 for Black-Scholes"""
        return self._d1(S, K, T, r, sigma) - sigma * np.sqrt(T)
    
    def calculate_delta(
        self,
        spot: float,
        strike: float,
        expiry_days: int,
        iv: float,
        option_type: str = 'CE'
    ) -> float:
        """
        Calculate Delta
        
        Args:
            spot: Current spot price
            strike: Strike price
            expiry_days: Days to expiry
            iv: Implied volatility (in %)
            option_type: 'CE' or 'PE'
            
        Returns:
            Delta value
        """
        T = expiry_days / 365.0
        sigma = iv / 100.0
        
        if T <= 0:
            return 1.0 if option_type == 'CE' else -1.0
        
        d1 = self._d1(spot, strike, T, self.risk_free_rate, sigma)
        
        if option_type == 'CE':
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1
        
        return delta
    
    def calculate_gamma(
        self,
        spot: float,
        strike: float,
        expiry_days: int,
        iv: float
    ) -> float:
        """
        Calculate Gamma (same for CE and PE)
        
        Args:
            spot: Current spot price
            strike: Strike price
            expiry_days: Days to expiry
            iv: Implied volatility (in %)
            
        Returns:
            Gamma value
        """
        T = expiry_days / 365.0
        sigma = iv / 100.0
        
        if T <= 0:
            return 0.0
        
        d1 = self._d1(spot, strike, T, self.risk_free_rate, sigma)
        gamma = norm.pdf(d1) / (spot * sigma * np.sqrt(T))
        
        return gamma
    
    def calculate_theta(
        self,
        spot: float,
        strike: float,
        expiry_days: int,
        iv: float,
        option_type: str = 'CE'
    ) -> float:
        """
        Calculate Theta (time decay per day)
        
        Args:
            spot: Current spot price
            strike: Strike price
            expiry_days: Days to expiry
            iv: Implied volatility (in %)
            option_type: 'CE' or 'PE'
            
        Returns:
            Theta value (daily decay)
        """
        T = expiry_days / 365.0
        sigma = iv / 100.0
        r = self.risk_free_rate
        
        if T <= 0:
            return 0.0
        
        d1 = self._d1(spot, strike, T, r, sigma)
        d2 = self._d2(spot, strike, T, r, sigma)
        
        if option_type == 'CE':
            theta = (
                -(spot * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
                - r * strike * np.exp(-r * T) * norm.cdf(d2)
            )
        else:
            theta = (
                -(spot * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
                + r * strike * np.exp(-r * T) * norm.cdf(-d2)
            )
        
        # Return daily theta
        return theta / 365.0
    
    def calculate_vega(
        self,
        spot: float,
        strike: float,
        expiry_days: int,
        iv: float
    ) -> float:
        """
        Calculate Vega (sensitivity to IV change)
        
        Args:
            spot: Current spot price
            strike: Strike price
            expiry_days: Days to expiry
            iv: Implied volatility (in %)
            
        Returns:
            Vega value (change per 1% IV move)
        """
        T = expiry_days / 365.0
        sigma = iv / 100.0
        
        if T <= 0:
            return 0.0
        
        d1 = self._d1(spot, strike, T, self.risk_free_rate, sigma)
        vega = spot * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% change
        
        return vega
    
    def calculate_all_greeks(
        self,
        spot: float,
        strike: float,
        expiry_days: int,
        iv: float,
        option_type: str = 'CE'
    ) -> Dict[str, float]:
        """
        Calculate all Greeks at once
        
        Returns:
            Dictionary with all Greeks
        """
        greeks = {
            'spot': spot,
            'strike': strike,
            'expiry_days': expiry_days,
            'iv': iv,
            'option_type': option_type,
            'delta': self.calculate_delta(spot, strike, expiry_days, iv, option_type),
            'gamma': self.calculate_gamma(spot, strike, expiry_days, iv),
            'theta': self.calculate_theta(spot, strike, expiry_days, iv, option_type),
            'vega': self.calculate_vega(spot, strike, expiry_days, iv)
        }
        
        return greeks
    
    def interpret_delta(self, delta: float) -> str:
        """Interpret Delta value"""
        abs_delta = abs(delta)
        
        if abs_delta < 0.3:
            return "OTM (Low directional)"
        elif abs_delta < 0.5:
            return "Near ATM (Moderate directional)"
        elif abs_delta < 0.7:
            return "ATM (High directional)"
        else:
            return "ITM (Very high directional)"
    
    def interpret_gamma(self, gamma: float) -> str:
        """Interpret Gamma value"""
        if gamma < 0.001:
            return "Low acceleration"
        elif gamma < 0.003:
            return "Moderate acceleration"
        else:
            return "High acceleration (Gamma risk!)"
    
    def interpret_theta(self, theta: float) -> str:
        """Interpret Theta value"""
        if abs(theta) < 5:
            return "Low time decay"
        elif abs(theta) < 15:
            return "Moderate time decay"
        else:
            return "High time decay (Theta burn!)"
    
    def interpret_vega(self, vega: float) -> str:
        """Interpret Vega value"""
        if vega < 5:
            return "Low IV sensitivity"
        elif vega < 15:
            return "Moderate IV sensitivity"
        else:
            return "High IV sensitivity"
    
    def calculate_position_size_with_greeks(
        self,
        delta: float,
        capital: float,
        risk_percent: float = 1.0,
        spot: float = 23500
    ) -> int:
        """
        Calculate optimal position size based on Delta
        
        Args:
            delta: Option delta
            capital: Available capital
            risk_percent: Risk percentage of capital
            spot: Current spot price
            
        Returns:
            Recommended quantity
        """
        risk_amount = capital * (risk_percent / 100)
        
        # Delta-neutral sizing
        delta_adjusted_value = spot * abs(delta)
        
        if delta_adjusted_value == 0:
            return 0
        
        quantity = int(risk_amount / delta_adjusted_value)
        
        return max(1, quantity)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING GREEKS CALCULATOR")
    print("="*60 + "\n")
    
    calc = GreeksCalculator()
    
    # Example: NIFTY ATM Call
    greeks = calc.calculate_all_greeks(
        spot=23500,
        strike=23500,
        expiry_days=7,
        iv=15.5,
        option_type='CE'
    )
    
    print("NIFTY 23500 CE (7 days to expiry, IV=15.5%)")
    print("-" * 60)
    print(f"Delta:  {greeks['delta']:.4f}  ({calc.interpret_delta(greeks['delta'])})")
    print(f"Gamma:  {greeks['gamma']:.6f}  ({calc.interpret_gamma(greeks['gamma'])})")
    print(f"Theta:  ₹{greeks['theta']:.2f}/day  ({calc.interpret_theta(greeks['theta'])})")
    print(f"Vega:   ₹{greeks['vega']:.2f}  ({calc.interpret_vega(greeks['vega'])})")
    print()
    
    # Position sizing
    qty = calc.calculate_position_size_with_greeks(
        delta=greeks['delta'],
        capital=100000,
        risk_percent=0.5
    )
    print(f"Recommended quantity (0.5% risk): {qty} lots")
    print()
    
    print("="*60 + "\n")

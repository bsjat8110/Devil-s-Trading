"""
Volume Profile Analyzer
Identifies high-volume price levels (Point of Control, Value Areas)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class VolumeProfileAnalyzer:
    """
    Analyzes volume distribution at different price levels
    """
    
    def __init__(self, df: pd.DataFrame, num_bins: int = 24):
        """
        df: DataFrame with OHLCV data
        num_bins: Number of price bins for volume profile
        """
        self.df = df
        self.num_bins = num_bins
        self.profile = None
        
    def calculate_volume_profile(self) -> pd.DataFrame:
        """
        Calculate volume profile
        """
        if self.df.empty:
            return pd.DataFrame()
        
        try:
            # Create price bins
            price_min = self.df['low'].min()
            price_max = self.df['high'].max()
            
            bins = np.linspace(price_min, price_max, self.num_bins)
            
            # Calculate volume at each price level
            volume_at_price = []
            
            for i in range(len(bins) - 1):
                price_low = bins[i]
                price_high = bins[i + 1]
                
                # Filter bars that traded in this price range
                mask = (
                    (self.df['low'] <= price_high) & 
                    (self.df['high'] >= price_low)
                )
                
                total_volume = self.df[mask]['volume'].sum()
                
                volume_at_price.append({
                    'price_low': price_low,
                    'price_high': price_high,
                    'price_mid': (price_low + price_high) / 2,
                    'volume': total_volume
                })
            
            profile = pd.DataFrame(volume_at_price)
            self.profile = profile
            
            return profile
            
        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return pd.DataFrame()
    
    def get_point_of_control(self) -> float:
        """
        Get Point of Control (price level with highest volume)
        """
        if self.profile is None or self.profile.empty:
            self.calculate_volume_profile()
        
        if self.profile.empty:
            return 0.0
        
        poc_row = self.profile.loc[self.profile['volume'].idxmax()]
        return float(poc_row['price_mid'])
    
    def get_value_area(self, value_area_pct: float = 70) -> Tuple[float, float]:
        """
        Get Value Area (price range containing X% of volume)
        value_area_pct: Percentage of volume to include (default 70%)
        """
        if self.profile is None or self.profile.empty:
            self.calculate_volume_profile()
        
        if self.profile.empty:
            return 0.0, 0.0
        
        # Sort by volume
        sorted_profile = self.profile.sort_values('volume', ascending=False)
        
        # Calculate cumulative volume percentage
        total_volume = sorted_profile['volume'].sum()
        target_volume = total_volume * (value_area_pct / 100)
        
        cumulative_volume = 0
        value_area_prices = []
        
        for _, row in sorted_profile.iterrows():
            cumulative_volume += row['volume']
            value_area_prices.append(row['price_mid'])
            
            if cumulative_volume >= target_volume:
                break
        
        if value_area_prices:
            vah = max(value_area_prices)  # Value Area High
            val = min(value_area_prices)  # Value Area Low
            return val, vah
        
        return 0.0, 0.0
    
    def get_analysis(self) -> Dict:
        """
        Get complete volume profile analysis
        """
        poc = self.get_point_of_control()
        val, vah = self.get_value_area()
        
        current_price = float(self.df['close'].iloc[-1])
        
        # Determine position relative to value area
        if current_price > vah:
            position = "Above Value Area (Bullish)"
        elif current_price < val:
            position = "Below Value Area (Bearish)"
        else:
            position = "Inside Value Area (Neutral)"
        
        return {
            'poc': poc,
            'val': val,
            'vah': vah,
            'current_price': current_price,
            'position': position,
            'value_area_width': vah - val,
            'distance_from_poc': current_price - poc
        }

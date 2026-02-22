"""
Historical Data Downloader
Downloads OHLC data from Angel One Historical API
"""

import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataDownloader:
    """
    Downloads historical candlestick data from Angel One
    """
    
    def __init__(self, auth_manager):
        """
        Initialize with authenticated Angel One session
        
        Args:
            auth_manager: AngelAuthManager instance
        """
        self.auth_manager = auth_manager
        self.historical_api = auth_manager.get_historical_api()
        
        if not self.historical_api:
            logger.error("❌ Historical API not available")
        else:
            logger.info("✅ Data Downloader initialized")
    
    def download_data(
        self,
        symbol_token: str,
        interval: str = "FIVE_MINUTE",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Download historical data
        
        Args:
            symbol_token: Token of the symbol
            interval: ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, ONE_HOUR, ONE_DAY
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with OHLC data
        """
        if not self.historical_api:
            logger.error("Historical API not initialized")
            return pd.DataFrame()
        
        # Default dates: last 30 days
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            logger.info(f"📥 Downloading data for token {symbol_token}")
            logger.info(f"   Period: {from_date} to {to_date}")
            logger.info(f"   Interval: {interval}")
            
            # Angel One API call
            params = {
                "exchange": "NFO",
                "symboltoken": symbol_token,
                "interval": interval,
                "fromdate": f"{from_date} 09:15",
                "todate": f"{to_date} 15:30"
            }
            
            response = self.historical_api.getCandleData(params)
            
            if response['status'] and response['data']:
                # Convert to DataFrame
                df = pd.DataFrame(
                    response['data'],
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Convert price columns to float
                for col in ['open', 'high', 'low', 'close']:
                    df[col] = df[col].astype(float)
                
                df['volume'] = df['volume'].astype(int)
                
                logger.info(f"✅ Downloaded {len(df)} candles")
                return df
            else:
                logger.error(f"❌ No data received: {response.get('message', 'Unknown error')}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return pd.DataFrame()
    
    def download_multiple_days(
        self,
        symbol_token: str,
        days: int = 30,
        interval: str = "FIVE_MINUTE"
    ) -> pd.DataFrame:
        """
        Download data for multiple days
        
        Args:
            symbol_token: Token of the symbol
            days: Number of days to download
            interval: Candle interval
            
        Returns:
            Combined DataFrame
        """
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        return self.download_data(symbol_token, interval, from_date, to_date)


if __name__ == "__main__":
    # Test with mock auth manager
    print("🧪 Testing Data Downloader...")
    print("⚠️  Need actual auth_manager to download data")
    print("Use this in your main trading agent with real credentials")

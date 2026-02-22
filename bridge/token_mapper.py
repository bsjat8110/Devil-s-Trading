"""
Token Mapper Module
Auto-downloads Angel One master contracts and provides token mapping
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TokenMapper:
    """
    Handles symbol to token mapping for Angel One
    Auto-downloads and updates master contract file
    """
    
    # Angel One master contract URLs
    MASTER_CONTRACT_URLS = {
        'NFO': 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json',
        'NSE': 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
    }
    
    def __init__(self, data_dir: str = 'data'):
        """
        Initialize Token Mapper
        
        Args:
            data_dir: Directory to store token data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.token_file = self.data_dir / 'tokens.json'
        self.contracts_file = self.data_dir / 'master_contracts.csv'
        
        self.tokens_data = {}
        self.contracts_df = None
        
        # Load or download data
        self._initialize_data()
        
        logger.info("✅ Token Mapper initialized")
    
    def _initialize_data(self):
        """Initialize token data - load from file or download fresh"""
        
        # Check if data exists and is recent (less than 1 day old)
        if self.token_file.exists():
            file_age = datetime.now() - datetime.fromtimestamp(
                self.token_file.stat().st_mtime
            )
            
            if file_age < timedelta(days=1):
                logger.info("📂 Loading tokens from cache...")
                self._load_tokens()
                return
        
        # Download fresh data
        logger.info("📥 Downloading fresh master contracts...")
        self.download_master_contracts()
    
    def download_master_contracts(self) -> bool:
        """
        Download master contract file from Angel One
        
        Returns:
            bool: True if successful
        """
        try:
            logger.info("🌐 Fetching master contracts from Angel One...")
            
            response = requests.get(
                self.MASTER_CONTRACT_URLS['NFO'],
                timeout=30
            )
            response.raise_for_status()
            
            # Parse JSON data
            contracts = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(contracts)
            
            # Save raw contracts
            df.to_csv(self.contracts_file, index=False)
            logger.info(f"💾 Saved {len(df)} contracts to {self.contracts_file}")
            
            # Process and build token mappings
            self._process_contracts(df)
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"❌ Failed to download contracts: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error processing contracts: {e}")
            return False
    
    def _process_contracts(self, df: pd.DataFrame):
        """
        Process contracts and build token mappings
        
        Args:
            df: Contracts DataFrame
        """
        self.contracts_df = df
        self.tokens_data = {
            'symbols': {},      # symbol -> token
            'tokens': {},       # token -> symbol info
            'expiries': {},     # symbol -> list of expiries
            'strikes': {},      # symbol -> list of strikes
            'last_updated': datetime.now().isoformat()
        }
        
        for _, row in df.iterrows():
            try:
                token = str(row.get('token', ''))
                symbol = str(row.get('symbol', ''))
                name = str(row.get('name', ''))
                exchange = str(row.get('exch_seg', ''))
                instrument = str(row.get('instrumenttype', ''))
                
                # Skip if essential data missing
                if not token or not symbol:
                    continue
                
                # Store symbol -> token mapping
                self.tokens_data['symbols'][symbol] = token
                
                # Store token -> detailed info
                self.tokens_data['tokens'][token] = {
                    'symbol': symbol,
                    'name': name,
                    'exchange': exchange,
                    'instrument': instrument,
                    'token': token
                }
                
                # For options, extract strike and expiry
                if instrument in ['OPTIDX', 'OPTSTK']:
                    strike = row.get('strike', 0)
                    expiry = row.get('expiry', '')
                    option_type = row.get('symbol', '')[-2:]  # CE or PE
                    
                    # Extract base symbol (NIFTY, BANKNIFTY, etc.)
                    if 'NIFTY' in symbol and 'BANK' not in symbol:
                        base = 'NIFTY'
                    elif 'BANKNIFTY' in symbol:
                        base = 'BANKNIFTY'
                    elif 'FINNIFTY' in symbol:
                        base = 'FINNIFTY'
                    elif 'MIDCPNIFTY' in symbol:
                        base = 'MIDCPNIFTY'
                    else:
                        base = name.split()[0] if name else symbol
                    
                    # Store expiries
                    if base not in self.tokens_data['expiries']:
                        self.tokens_data['expiries'][base] = set()
                    if expiry:
                        self.tokens_data['expiries'][base].add(expiry)
                    
                    # Store strikes
                    strike_key = f"{base}_{expiry}_{option_type}"
                    if strike_key not in self.tokens_data['strikes']:
                        self.tokens_data['strikes'][strike_key] = []
                    
                    if strike and strike > 0:
                        self.tokens_data['strikes'][strike_key].append({
                            'strike': float(strike) / 100,  # Angel gives in paisa
                            'token': token,
                            'symbol': symbol
                        })
                
            except Exception as e:
                logger.debug(f"Skipping row: {e}")
                continue
        
        # Convert sets to sorted lists for JSON serialization
        for symbol in self.tokens_data['expiries']:
            self.tokens_data['expiries'][symbol] = sorted(
                list(self.tokens_data['expiries'][symbol])
            )
        
        # Sort strikes
        for key in self.tokens_data['strikes']:
            self.tokens_data['strikes'][key] = sorted(
                self.tokens_data['strikes'][key],
                key=lambda x: x['strike']
            )
        
        # Save to JSON
        self._save_tokens()
        
        logger.info(f"✅ Processed {len(self.tokens_data['symbols'])} symbols")
    
    def _save_tokens(self):
        """Save tokens data to JSON file"""
        try:
            with open(self.token_file, 'w') as f:
                json.dump(self.tokens_data, f, indent=2)
            logger.info(f"💾 Saved token mappings to {self.token_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save tokens: {e}")
    
    def _load_tokens(self):
        """Load tokens data from JSON file"""
        try:
            with open(self.token_file, 'r') as f:
                self.tokens_data = json.load(f)
            logger.info(f"📂 Loaded {len(self.tokens_data.get('symbols', {}))} symbols from cache")
        except Exception as e:
            logger.error(f"❌ Failed to load tokens: {e}")
            # If load fails, download fresh
            self.download_master_contracts()
    
    def get_token(self, symbol: str) -> Optional[str]:
        """
        Get token for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'NIFTY23JAN24500CE')
            
        Returns:
            Token string or None
        """
        return self.tokens_data.get('symbols', {}).get(symbol)
    
    def get_symbol(self, token: str) -> Optional[str]:
        """
        Get symbol for a token
        
        Args:
            token: Token string
            
        Returns:
            Symbol or None
        """
        token_info = self.tokens_data.get('tokens', {}).get(str(token))
        return token_info.get('symbol') if token_info else None
    
    def get_symbol_info(self, token: str) -> Optional[Dict]:
        """
        Get complete info for a token
        
        Args:
            token: Token string
            
        Returns:
            Dictionary with symbol info
        """
        return self.tokens_data.get('tokens', {}).get(str(token))
    
    def get_current_expiry(self, symbol: str = 'NIFTY') -> Optional[str]:
        """
        Get current month expiry for a symbol
        
        Args:
            symbol: Base symbol (NIFTY, BANKNIFTY, etc.)
            
        Returns:
            Expiry date string (DDMMMYY format)
        """
        expiries = self.tokens_data.get('expiries', {}).get(symbol, [])
        
        if not expiries:
            return None
        
        # Get current date
        today = datetime.now()
        
        # Find nearest expiry that's in the future
        for expiry_str in expiries:
            try:
                # Parse expiry (format: DDMMMYY like 25JAN24)
                expiry_date = datetime.strptime(expiry_str, '%d%b%y')
                
                if expiry_date >= today:
                    return expiry_str
            except:
                continue
        
        # If no future expiry found, return first one
        return expiries[0] if expiries else None
    
    def get_atm_strike(self, symbol: str, spot_price: float, 
                       round_to: int = 50) -> float:
        """
        Calculate ATM strike based on spot price
        
        Args:
            symbol: Base symbol (NIFTY, BANKNIFTY, etc.)
            spot_price: Current spot price
            round_to: Round to nearest (50 for NIFTY, 100 for BANKNIFTY)
            
        Returns:
            ATM strike price
        """
        # Round to nearest strike
        atm = round(spot_price / round_to) * round_to
        return atm
    
    def get_atm_ce(self, symbol: str = 'NIFTY', 
                   spot_price: Optional[float] = None) -> Optional[str]:
        """
        Get ATM Call option token
        
        Args:
            symbol: Base symbol (NIFTY, BANKNIFTY, etc.)
            spot_price: Current spot price (if None, uses middle strike)
            
        Returns:
            Token for ATM CE option
        """
        expiry = self.get_current_expiry(symbol)
        if not expiry:
            logger.error(f"No expiry found for {symbol}")
            return None
        
        strike_key = f"{symbol}_{expiry}_CE"
        strikes = self.tokens_data.get('strikes', {}).get(strike_key, [])
        
        if not strikes:
            logger.error(f"No CE strikes found for {symbol} {expiry}")
            return None
        
        if spot_price is None:
            # Return middle strike if no spot price given
            mid_idx = len(strikes) // 2
            return strikes[mid_idx]['token']
        
        # Find ATM strike
        round_to = 100 if 'BANK' in symbol else 50
        atm_strike = self.get_atm_strike(symbol, spot_price, round_to)
        
        # Find closest strike
        closest = min(strikes, key=lambda x: abs(x['strike'] - atm_strike))
        return closest['token']
    
    def get_atm_pe(self, symbol: str = 'NIFTY', 
                   spot_price: Optional[float] = None) -> Optional[str]:
        """
        Get ATM Put option token
        
        Args:
            symbol: Base symbol (NIFTY, BANKNIFTY, etc.)
            spot_price: Current spot price (if None, uses middle strike)
            
        Returns:
            Token for ATM PE option
        """
        expiry = self.get_current_expiry(symbol)
        if not expiry:
            logger.error(f"No expiry found for {symbol}")
            return None
        
        strike_key = f"{symbol}_{expiry}_PE"
        strikes = self.tokens_data.get('strikes', {}).get(strike_key, [])
        
        if not strikes:
            logger.error(f"No PE strikes found for {symbol} {expiry}")
            return None
        
        if spot_price is None:
            # Return middle strike if no spot price given
            mid_idx = len(strikes) // 2
            return strikes[mid_idx]['token']
        
        # Find ATM strike
        round_to = 100 if 'BANK' in symbol else 50
        atm_strike = self.get_atm_strike(symbol, spot_price, round_to)
        
        # Find closest strike
        closest = min(strikes, key=lambda x: abs(x['strike'] - atm_strike))
        return closest['token']
    
    def get_strike_token(self, symbol: str, strike: float, 
                        option_type: str, expiry: Optional[str] = None) -> Optional[str]:
        """
        Get token for specific strike
        
        Args:
            symbol: Base symbol (NIFTY, BANKNIFTY, etc.)
            strike: Strike price
            option_type: 'CE' or 'PE'
            expiry: Expiry date (if None, uses current month)
            
        Returns:
            Token string
        """
        if expiry is None:
            expiry = self.get_current_expiry(symbol)
        
        if not expiry:
            return None
        
        strike_key = f"{symbol}_{expiry}_{option_type}"
        strikes = self.tokens_data.get('strikes', {}).get(strike_key, [])
        
        # Find exact strike
        for s in strikes:
            if s['strike'] == strike:
                return s['token']
        
        # If exact not found, find closest
        if strikes:
            closest = min(strikes, key=lambda x: abs(x['strike'] - strike))
            logger.warning(f"Exact strike {strike} not found, using {closest['strike']}")
            return closest['token']
        
        return None
    
    def search_symbol(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        Search symbols by keyword
        
        Args:
            keyword: Search keyword
            limit: Maximum results
            
        Returns:
            List of matching symbols
        """
        results = []
        keyword = keyword.upper()
        
        for symbol, token in self.tokens_data.get('symbols', {}).items():
            if keyword in symbol:
                info = self.tokens_data['tokens'].get(token, {})
                results.append(info)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def update_data(self):
        """Force update token data"""
        logger.info("🔄 Forcing token data update...")
        self.download_master_contracts()


def test_token_mapper():
    """Test token mapper functionality"""
    print("\n" + "="*60)
    print("🧪 TESTING TOKEN MAPPER")
    print("="*60 + "\n")
    
    # Initialize mapper
    print("1️⃣  Initializing Token Mapper...")
    mapper = TokenMapper()
    print("✅ Initialized\n")
    
    # Test: Get current expiry
    print("2️⃣  Getting current expiry...")
    nifty_expiry = mapper.get_current_expiry('NIFTY')
    bank_expiry = mapper.get_current_expiry('BANKNIFTY')
    print(f"   NIFTY expiry: {nifty_expiry}")
    print(f"   BANKNIFTY expiry: {bank_expiry}")
    print("✅ Expiry fetched\n")
    
    # Test: Get ATM strikes
    print("3️⃣  Getting ATM strikes (spot: NIFTY=23500)...")
    atm_ce = mapper.get_atm_ce('NIFTY', 23500)
    atm_pe = mapper.get_atm_pe('NIFTY', 23500)
    
    if atm_ce:
        ce_info = mapper.get_symbol_info(atm_ce)
        print(f"   ATM CE: {ce_info.get('symbol')} (Token: {atm_ce})")
    
    if atm_pe:
        pe_info = mapper.get_symbol_info(atm_pe)
        print(f"   ATM PE: {pe_info.get('symbol')} (Token: {atm_pe})")
    
    print("✅ ATM strikes found\n")
    
    # Test: Get specific strike
    print("4️⃣  Getting specific strike (NIFTY 23500 CE)...")
    token = mapper.get_strike_token('NIFTY', 23500, 'CE')
    if token:
        info = mapper.get_symbol_info(token)
        print(f"   Symbol: {info.get('symbol')}")
        print(f"   Token: {token}")
    print("✅ Specific strike found\n")
    
    # Test: Search
    print("5️⃣  Searching for 'NIFTY'...")
    results = mapper.search_symbol('NIFTY', limit=5)
    for r in results[:3]:
        print(f"   {r.get('symbol')} ({r.get('token')})")
    print("✅ Search completed\n")
    
    print("="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_token_mapper()

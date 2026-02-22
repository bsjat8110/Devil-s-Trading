"""
DEVIL TRADING AGENT - AUTHENTICATION MANAGER
Handles Angel One login, session management, and TOTP generation
"""

import os
import pyotp
from SmartApi import SmartConnect
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AngelAuthManager:
    """Manages authentication with Angel One APIs"""
    
    def __init__(self):
        """Initialize auth manager with credentials from .env"""
        load_dotenv()
        
        # Login credentials
        self.client_id = os.getenv('CLIENT_ID')
        self.password = os.getenv('ANGEL_PASSWORD')
        self.totp_secret = os.getenv('TOTP_SECRET')
        
        # API credentials (all 4 APIs)
        self.api_keys = {
            'market': os.getenv('MARKET_API_KEY'),
            'publisher': os.getenv('PUBLISHER_API_KEY'),
            'historical': os.getenv('HISTORICAL_API_KEY'),
            'trading': os.getenv('TRADING_API_KEY')
        }
        
        self.api_secrets = {
            'market': os.getenv('MARKET_SECRET_KEY'),
            'publisher': os.getenv('PUBLISHER_SECRET_KEY'),
            'historical': os.getenv('HISTORICAL_SECRET_KEY'),
            'trading': os.getenv('TRADING_SECRET_KEY')
        }
        
        # SmartConnect instances for each API
        self.connections = {}
        self.auth_tokens = {}
        
        logger.info("✅ Auth Manager initialized")
    
    def generate_totp(self):
        """Generate TOTP code for login"""
        try:
            totp = pyotp.TOTP(self.totp_secret)
            code = totp.now()
            logger.info(f"🔐 TOTP generated: {code}")
            return code
        except Exception as e:
            logger.error(f"❌ TOTP generation failed: {e}")
            return None
    
    def login(self, api_type='trading'):
        """
        Login to Angel One for specific API type
        
        Args:
            api_type: 'market', 'publisher', 'historical', or 'trading'
        
        Returns:
            SmartConnect object if successful, None otherwise
        """
        try:
            api_key = self.api_keys.get(api_type)
            secret_key = self.api_secrets.get(api_type)
            
            if not api_key or not secret_key:
                logger.error(f"❌ Missing credentials for {api_type} API")
                return None
            
            # Create SmartConnect instance
            smart_api = SmartConnect(api_key=api_key)
            
            # Generate TOTP
            totp_code = self.generate_totp()
            if not totp_code:
                return None
            
            # Login
            logger.info(f"🔄 Logging in to {api_type.upper()} API...")
            
            session_data = smart_api.generateSession(
                clientCode=self.client_id,
                password=self.password,
                totp=totp_code
            )
            
            if session_data['status']:
                auth_token = session_data['data']['jwtToken']
                refresh_token = session_data['data']['refreshToken']
                feed_token = session_data['data']['feedToken']
                
                # Store connection and tokens
                self.connections[api_type] = smart_api
                self.auth_tokens[api_type] = {
                    'auth_token': auth_token,
                    'refresh_token': refresh_token,
                    'feed_token': feed_token
                }
                
                logger.info(f"✅ {api_type.upper()} API login successful!")
                logger.info(f"📊 Feed Token: {feed_token[:20]}...")
                
                return smart_api
            else:
                logger.error(f"❌ Login failed: {session_data.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Login exception for {api_type}: {e}")
            return None
    
    def get_connection(self, api_type='trading'):
        """Get existing connection or create new one"""
        if api_type in self.connections:
            return self.connections[api_type]
        else:
            return self.login(api_type)
    
    def get_feed_token(self, api_type='market'):
        """Get feed token for websocket connections"""
        if api_type in self.auth_tokens:
            return self.auth_tokens[api_type]['feed_token']
        return None
    
    def logout(self, api_type='trading'):
        """Logout from specific API"""
        try:
            if api_type in self.connections:
                self.connections[api_type].terminateSession(self.client_id)
                logger.info(f"✅ Logged out from {api_type.upper()} API")
                del self.connections[api_type]
                del self.auth_tokens[api_type]
        except Exception as e:
            logger.error(f"❌ Logout failed: {e}")
    
    def logout_all(self):
        """Logout from all APIs"""
        for api_type in list(self.connections.keys()):
            self.logout(api_type)
        logger.info("✅ Logged out from all APIs")


# Test function
if __name__ == "__main__":
    print("🧪 Testing Angel One Authentication...")
    
    auth = AngelAuthManager()
    
    # Test login for trading API
    connection = auth.login('trading')
    
    if connection:
        print("✅ Authentication test successful!")
        print(f"📊 Feed Token: {auth.get_feed_token('market')}")
        
        # Test logout
        auth.logout_all()
    else:
        print("❌ Authentication test failed!")

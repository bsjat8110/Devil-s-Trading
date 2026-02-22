"""
Error Monitor & Auto-Recovery
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from bridge.trade_handler import TradeHandler
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename='data/trading_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

handler = TradeHandler()

def log_error(error_type, message):
    """Log error and send Telegram alert"""
    logging.error(f"{error_type}: {message}")
    
    handler.send_risk_warning(
        warning_type=error_type,
        message=f"⚠️ {message}"
    )

# Example usage in your trading code:
# try:
#     # Your trading logic
#     pass
# except Exception as e:
#     log_error("TRADING_ERROR", str(e))

print("✅ Error monitor initialized")

"""
Trade Database Module
Manages all trade logs in a SQLite database
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradeDatabase:
    """
    Handles connection and operations with the trades SQLite database
    """
    
    def __init__(self, db_path: str = 'data/trades.db'):
        """
        Initialize database connection
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = None
        
        try:
            self.conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self.conn.row_factory = sqlite3.Row
            logger.info(f"✅ Database connected at {self.db_path}")
            self.create_table()
            
        except sqlite3.Error as e:
            logger.error(f"❌ Database error: {e}")
            self.conn = None
    
    def create_table(self):
        """Create the 'trades' table if it doesn't exist"""
        if not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    strategy TEXT,
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP NOT NULL,
                    action TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    pnl REAL NOT NULL,
                    pnl_percent REAL,
                    status TEXT NOT NULL,
                    exit_reason TEXT
                )
            """)
            self.conn.commit()
            logger.info("Table 'trades' is ready")
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error creating table: {e}")
    
    def log_trade(self, trade_data: Dict) -> bool:
        """
        Log a completed trade to the database
        
        Args:
            trade_data: Dictionary containing trade details
            
        Returns:
            bool: True if successful
        """
        if not self.conn:
            return False
            
        required_keys = [
            'symbol', 'entry_time', 'exit_time', 'action',
            'quantity', 'entry_price', 'exit_price', 'pnl'
        ]
        
        if not all(key in trade_data for key in required_keys):
            logger.error(f"Missing required keys in trade data: {trade_data}")
            return False
        
        # Determine status
        if trade_data['pnl'] > 0:
            status = 'WIN'
        elif trade_data['pnl'] < 0:
            status = 'LOSS'
        else:
            status = 'BREAKEVEN'
        
        sql = """
            INSERT INTO trades (
                symbol, strategy, entry_time, exit_time, action, 
                quantity, entry_price, exit_price, pnl, pnl_percent, 
                status, exit_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            trade_data.get('symbol'),
            trade_data.get('strategy', 'Default'),
            trade_data.get('entry_time'),
            trade_data.get('exit_time'),
            trade_data.get('action'),
            trade_data.get('quantity'),
            trade_data.get('entry_price'),
            trade_data.get('exit_price'),
            trade_data.get('pnl'),
            trade_data.get('pnl_percent'),
            status,
            trade_data.get('exit_reason', 'Closed')
        )
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            self.conn.commit()
            logger.info(f"💾 Trade logged for {trade_data['symbol']}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"❌ Failed to log trade: {e}")
            return False
    
    def get_trades(self, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch trades from the database as a pandas DataFrame
        
        Args:
            start_date: 'YYYY-MM-DD'
            end_date: 'YYYY-MM-DD'
            
        Returns:
            DataFrame of trades
        """
        if not self.conn:
            return pd.DataFrame()
            
        query = "SELECT * FROM trades"
        params = []
        
        if start_date and end_date:
            query += " WHERE entry_time BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        
        query += " ORDER BY entry_time ASC"
        
        try:
            df = pd.read_sql_query(query, self.conn, params=params)
            # Convert time columns to datetime objects
            df['entry_time'] = pd.to_datetime(df['entry_time'])
            df['exit_time'] = pd.to_datetime(df['exit_time'])
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch trades: {e}")
            return pd.DataFrame()
    
    def __del__(self):
        """Close database connection upon object deletion"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


if __name__ == '__main__':
    # Test the database
    print("🧪 Testing TradeDatabase...")
    db = TradeDatabase(db_path='data/test_trades.db')
    
    # Log a dummy trade
    test_trade = {
        'symbol': 'NIFTY_TEST',
        'strategy': 'TestStrategy',
        'entry_time': datetime.now(),
        'exit_time': datetime.now(),
        'action': 'BUY',
        'quantity': 50,
        'entry_price': 150.0,
        'exit_price': 160.0,
        'pnl': 500.0,
        'pnl_percent': 6.67,
        'exit_reason': 'Target Hit'
    }
    db.log_trade(test_trade)
    
    # Fetch trades
    trades_df = db.get_trades()
    print("\nFetched Trades:")
    print(trades_df.tail(1))
    print("\n✅ TradeDatabase test completed")

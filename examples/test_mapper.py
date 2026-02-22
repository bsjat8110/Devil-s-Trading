"""
Token Mapper Usage Examples
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bridge.token_mapper import TokenMapper

# Initialize mapper
mapper = TokenMapper()

print("\n" + "="*60)
print("📖 TOKEN MAPPER USAGE EXAMPLES")
print("="*60 + "\n")

# Example 1: Get ATM CE token
print("Example 1: Get ATM Call Option")
print("-" * 40)
spot_price = 23485  # Current NIFTY spot
token = mapper.get_atm_ce('NIFTY', spot_price)
if token:
    symbol_info = mapper.get_symbol_info(token)
    print(f"Spot Price: {spot_price}")
    print(f"ATM CE Token: {token}")
    print(f"ATM CE Symbol: {symbol_info['symbol']}\n")
else:
    print("⚠️  No ATM CE found\n")

# Example 2: Get ATM PE token
print("Example 2: Get ATM Put Option")
print("-" * 40)
token = mapper.get_atm_pe('NIFTY', spot_price)
if token:
    symbol_info = mapper.get_symbol_info(token)
    print(f"ATM PE Token: {token}")
    print(f"ATM PE Symbol: {symbol_info['symbol']}\n")
else:
    print("⚠️  No ATM PE found\n")

# Example 3: Get specific strike
print("Example 3: Get Specific Strike")
print("-" * 40)
token = mapper.get_strike_token('NIFTY', 23500, 'CE')
if token:
    symbol_info = mapper.get_symbol_info(token)
    print(f"NIFTY 23500 CE Token: {token}")
    print(f"Symbol: {symbol_info['symbol']}\n")
else:
    print("⚠️  Strike not found\n")

# Example 4: BANKNIFTY
print("Example 4: BANKNIFTY Options")
print("-" * 40)
bank_spot = 48750
token_ce = mapper.get_atm_ce('BANKNIFTY', bank_spot)
token_pe = mapper.get_atm_pe('BANKNIFTY', bank_spot)

if token_ce and token_pe:
    ce_info = mapper.get_symbol_info(token_ce)
    pe_info = mapper.get_symbol_info(token_pe)
    
    print(f"BANKNIFTY Spot: {bank_spot}")
    print(f"ATM CE: {ce_info['symbol']} ({token_ce})")
    print(f"ATM PE: {pe_info['symbol']} ({token_pe})\n")
else:
    print("⚠️  BANKNIFTY options not found\n")

# Example 5: Get current expiry
print("Example 5: Current Expiry Dates")
print("-" * 40)
nifty_exp = mapper.get_current_expiry('NIFTY')
bank_exp = mapper.get_current_expiry('BANKNIFTY')
finn_exp = mapper.get_current_expiry('FINNIFTY')

print(f"NIFTY: {nifty_exp}")
print(f"BANKNIFTY: {bank_exp}")
print(f"FINNIFTY: {finn_exp}\n")

# Example 6: Search symbols
print("Example 6: Search Symbols")
print("-" * 40)
results = mapper.search_symbol('NIFTY23', limit=5)
if results:
    for r in results[:3]:
        print(f"{r['symbol']} - {r['exchange']} ({r['token']})")
else:
    print("No results found")

print("\n" + "="*60)
print("✅ ALL EXAMPLES COMPLETED")
print("="*60 + "\n")

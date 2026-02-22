"""
Update Token Mappings Daily
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from bridge.token_mapper import TokenMapper
from datetime import datetime

print(f"\n🔄 Updating Token Data - {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n")

mapper = TokenMapper()
mapper.update_data()

print("\n✅ Token data updated successfully!\n")

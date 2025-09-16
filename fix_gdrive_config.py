#!/usr/bin/env python3
"""
Fix Google Drive configuration to include web_app_url field
"""

import sys
import os
sys.path.append('/app/backend')

from mongodb_database import mongo_db
from datetime import datetime, timezone
import asyncio

async def fix_gdrive_config():
    """Fix Google Drive configuration"""
    try:
        # Get current config
        config = await mongo_db.find_one("gdrive_config", {"id": "system_gdrive"})
        print("Current config:", config)
        
        # Update config with web_app_url field
        apps_script_url = "https://script.google.com/macros/s/AKfycbwphwgJwjyW4V-Y2y0J4uIa40zZwybm7s9maqNemi04EawcOhxRX99rbSXGWxk_D6o/exec"
        
        update_data = {
            "web_app_url": apps_script_url,
            "apps_script_url": apps_script_url,
            "updated_at": datetime.now(timezone.utc)
        }
        
        await mongo_db.update("gdrive_config", {"id": "system_gdrive"}, update_data)
        print("✅ Updated Google Drive config with web_app_url field")
        
        # Verify update
        updated_config = await mongo_db.find_one("gdrive_config", {"id": "system_gdrive"})
        print("Updated config:", updated_config)
        
    except Exception as e:
        print(f"❌ Error fixing config: {e}")

if __name__ == "__main__":
    asyncio.run(fix_gdrive_config())
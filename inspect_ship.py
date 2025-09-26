#!/usr/bin/env python3
"""
Script to inspect ship details
"""

import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to Python path
import sys
sys.path.append(str(Path(__file__).parent / "backend"))

from mongodb_database import mongo_db

async def inspect_ship_details():
    """Inspect ship details to understand structure"""
    
    try:
        # Initialize MongoDB connection
        await mongo_db.connect()
        
        # Find all ships
        ships = await mongo_db.find_all("ships", {})
        
        if ships:
            print("🔍 First ship details:")
            first_ship = ships[0]
            print(json.dumps(first_ship, indent=2, default=str))
            
            # Also check certificates
            ship_id = first_ship.get("id")
            certificates = await mongo_db.find_all("certificates", {"ship_id": ship_id})
            print(f"\n📋 This ship has {len(certificates)} certificates")
            
            if certificates:
                print("First certificate details:")
                print(json.dumps(certificates[0], indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await mongo_db.disconnect()

if __name__ == "__main__":
    load_dotenv(Path(__file__).parent / "backend" / ".env")
    asyncio.run(inspect_ship_details())
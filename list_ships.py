#!/usr/bin/env python3
"""
Script to list all ships in the database
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to Python path
import sys
sys.path.append(str(Path(__file__).parent / "backend"))

from mongodb_database import mongo_db

async def list_all_ships():
    """List all ships in the database"""
    
    try:
        # Initialize MongoDB connection
        await mongo_db.connect()
        
        # Find all ships
        print("🔍 Listing all ships in database...")
        ships = await mongo_db.find_all("ships", {})
        
        if not ships:
            print("ℹ️  No ships found in database")
            return
        
        print(f"📋 Found {len(ships)} ships:")
        for i, ship in enumerate(ships, 1):
            ship_name = ship.get("ship_name", "Unknown Ship")
            ship_id = ship.get("id", "Unknown ID")
            imo = ship.get("imo", "Unknown IMO")
            print(f"  {i}. Name: '{ship_name}' | ID: {ship_id} | IMO: {imo}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Disconnect from MongoDB
        await mongo_db.disconnect()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv(Path(__file__).parent / "backend" / ".env")
    
    # Run the listing
    asyncio.run(list_all_ships())
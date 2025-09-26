#!/usr/bin/env python3
"""
Script to verify that SUNSHINE 01 certificates have been deleted
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to Python path
import sys
sys.path.append(str(Path(__file__).parent / "backend"))

from mongodb_database import mongo_db

async def verify_deletion():
    """Verify that SUNSHINE 01 certificates have been deleted"""
    
    try:
        # Initialize MongoDB connection
        await mongo_db.connect()
        
        # Find the SUNSHINE 01 ship
        sunshine_ship = await mongo_db.find_one("ships", {"name": "SUNSHINE 01"})
        
        if not sunshine_ship:
            print("❌ SUNSHINE 01 ship not found in database")
            return
        
        ship_id = sunshine_ship.get("id")
        print(f"✅ Found SUNSHINE 01 ship with ID: {ship_id}")
        
        # Check for remaining certificates
        certificates = await mongo_db.find_all("certificates", {"ship_id": ship_id})
        
        if not certificates:
            print("✅ SUCCESS: No certificates found for SUNSHINE 01 - deletion was successful!")
        else:
            print(f"⚠️  WARNING: Still found {len(certificates)} certificates for SUNSHINE 01:")
            for i, cert in enumerate(certificates, 1):
                cert_name = cert.get("cert_name", "Unknown Certificate")
                cert_no = cert.get("cert_no", "No Number")
                print(f"  {i}. {cert_name} (No: {cert_no})")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await mongo_db.disconnect()

if __name__ == "__main__":
    load_dotenv(Path(__file__).parent / "backend" / ".env")
    asyncio.run(verify_deletion())
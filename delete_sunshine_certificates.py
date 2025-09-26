#!/usr/bin/env python3
"""
Script to delete all certificates for SUNSHINE 01 ship from the database
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to Python path
import sys
sys.path.append(str(Path(__file__).parent / "backend"))

from mongodb_database import mongo_db

async def delete_sunshine_01_certificates():
    """Delete all certificates for SUNSHINE 01 ship"""
    
    try:
        # Initialize MongoDB connection
        await mongo_db.connect()
        
        # First, find the SUNSHINE 01 ship
        print("🔍 Looking for SUNSHINE 01 ship...")
        sunshine_ship = await mongo_db.find_one("ships", {"name": "SUNSHINE 01"})
        
        if not sunshine_ship:
            print("❌ SUNSHINE 01 ship not found in database")
            return
        
        ship_id = sunshine_ship.get("id")
        print(f"✅ Found SUNSHINE 01 ship with ID: {ship_id}")
        
        # Find all certificates for this ship
        print("🔍 Looking for certificates for SUNSHINE 01...")
        certificates = await mongo_db.find_all("certificates", {"ship_id": ship_id})
        
        if not certificates:
            print("ℹ️  No certificates found for SUNSHINE 01")
            return
        
        print(f"📋 Found {len(certificates)} certificates for SUNSHINE 01:")
        for i, cert in enumerate(certificates, 1):
            cert_name = cert.get("cert_name", "Unknown Certificate")
            cert_no = cert.get("cert_no", "No Number")
            print(f"  {i}. {cert_name} (No: {cert_no})")
        
        # Ask for confirmation
        print("\n⚠️  WARNING: This will permanently delete all certificates for SUNSHINE 01!")
        confirm = input("Type 'DELETE' to confirm deletion: ")
        
        if confirm != "DELETE":
            print("❌ Deletion cancelled")
            return
        
        # Delete all certificates
        print("🗑️  Deleting certificates...")
        delete_result = await mongo_db.delete_many("certificates", {"ship_id": ship_id})
        
        print(f"✅ Successfully deleted {delete_result.deleted_count} certificates for SUNSHINE 01")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Disconnect from MongoDB
        await mongo_db.disconnect()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv(Path(__file__).parent / "backend" / ".env")
    
    # Run the deletion
    asyncio.run(delete_sunshine_01_certificates())
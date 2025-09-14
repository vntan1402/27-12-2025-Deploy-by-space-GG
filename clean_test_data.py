#!/usr/bin/env python3
"""
Clean Test Data Script
This script removes all test data from the MongoDB database while preserving essential admin user.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to path  
sys.path.append(str(Path(__file__).parent / "backend"))

# Load environment variables
load_dotenv(Path(__file__).parent / "backend" / ".env")

from mongodb_database import mongo_db

async def clean_test_data():
    """Clean all test data from MongoDB collections"""
    
    print("🧹 Starting test data cleanup...")
    
    try:
        # Connect to database first
        if not hasattr(mongo_db, 'db') or mongo_db.db is None:
            print("⚠️ Database not connected, attempting to connect...")
            await mongo_db.connect()
        
        # 1. Clean companies (keep only essential ones or remove all test companies)
        print("\n📋 Cleaning Companies...")
        companies = await mongo_db.find_all("companies")
        companies = companies or []  # Handle None case
        print(f"   Found {len(companies)} companies")
        
        # Remove all companies (or you can specify criteria to keep some)
        for company in companies:
            company_name = company.get('name_en', 'Unknown')
            company_id = company.get('id')
            if company_id:
                await mongo_db.delete("companies", {"id": company_id})
                print(f"   ✅ Deleted company: {company_name}")
        
        # 2. Clean users (keep only essential admin users)
        print("\n👥 Cleaning Users...")
        users = await mongo_db.find_all("users")
        users = users or []  # Handle None case
        print(f"   Found {len(users)} users")
        
        # Keep essential users: admin, admin1 (you can modify this list)
        essential_users = ["admin", "admin1"]
        
        for user in users:
            username = user.get('username', 'Unknown')
            user_id = user.get('id')
            if username not in essential_users and user_id:
                await mongo_db.delete("users", {"id": user_id})
                print(f"   ✅ Deleted test user: {username}")
            else:
                print(f"   ⚠️ Kept essential user: {username}")
        
        # 3. Clean ships
        print("\n🚢 Cleaning Ships...")
        ships = await mongo_db.find_all("ships")
        ships = ships or []  # Handle None case
        print(f"   Found {len(ships)} ships")
        
        for ship in ships:
            ship_name = ship.get('name', 'Unknown')
            ship_id = ship.get('id')
            if ship_id:
                await mongo_db.delete("ships", {"id": ship_id})
                print(f"   ✅ Deleted ship: {ship_name}")
        
        # 4. Clean certificates
        print("\n📜 Cleaning Certificates...")
        certificates = await mongo_db.find_all("certificates")
        certificates = certificates or []  # Handle None case
        print(f"   Found {len(certificates)} certificates")
        
        for cert in certificates:
            cert_name = cert.get('name', 'Unknown')
            cert_id = cert.get('id')
            if cert_id:
                await mongo_db.delete("certificates", {"id": cert_id})
                print(f"   ✅ Deleted certificate: {cert_name}")
        
        # 5. Clean usage tracking
        print("\n📊 Cleaning Usage Tracking...")
        usage_data = await mongo_db.find_all("usage_tracking")
        usage_data = usage_data or []  # Handle None case
        print(f"   Found {len(usage_data)} usage tracking records")
        
        for record in usage_data:
            record_id = record.get('id')
            if record_id:
                await mongo_db.delete("usage_tracking", {"id": record_id})
        
        if usage_data:
            print(f"   ✅ Deleted all {len(usage_data)} usage tracking records")
        
        # 6. Clean Google Drive configs (system level)
        print("\n☁️ Cleaning Google Drive Configs...")
        gdrive_configs = await mongo_db.find_all("gdrive_config")
        gdrive_configs = gdrive_configs or []  # Handle None case
        print(f"   Found {len(gdrive_configs)} Google Drive config records")
        
        for config in gdrive_configs:
            config_id = config.get('id')
            if config_id:
                await mongo_db.delete("gdrive_config", {"id": config_id})
        
        if gdrive_configs:
            print(f"   ✅ Deleted all {len(gdrive_configs)} Google Drive config records")
        
        # 7. Clean any temporary OAuth collections
        print("\n🔐 Cleaning OAuth Temp Data...")
        try:
            # Clean known temporary collections
            temp_collections = [
                "oauth_temp", 
                "company_gdrive_oauth_temp",
                "gdrive_oauth_temp"
            ]
            
            for col_name in temp_collections:
                try:
                    collection = mongo_db.db[col_name]
                    result = await collection.delete_many({})
                    if result.deleted_count > 0:
                        print(f"   ✅ Deleted {result.deleted_count} records from {col_name}")
                except Exception:
                    pass  # Collection might not exist
        except Exception as e:
            print(f"   ⚠️ OAuth cleanup warning: {e}")
        
        print("\n🎉 Test data cleanup completed successfully!")
        print("\n📋 Summary:")
        print("   ✅ Companies: Removed all companies")
        print("   ✅ Users: Kept essential users (admin, admin1)")
        print("   ✅ Ships: Removed all ships")
        print("   ✅ Certificates: Removed all certificates") 
        print("   ✅ Usage Tracking: Cleaned all records")
        print("   ✅ Google Drive Configs: Cleaned system configs")
        print("   ✅ OAuth Temp Data: Cleaned temporary data")
        
        # Final verification
        print("\n🔍 Final verification:")
        companies_count = len(await mongo_db.find_all("companies") or [])
        users_count = len(await mongo_db.find_all("users") or [])
        ships_count = len(await mongo_db.find_all("ships") or [])
        certificates_count = len(await mongo_db.find_all("certificates") or [])
        
        print(f"   📋 Companies remaining: {companies_count}")
        print(f"   👥 Users remaining: {users_count}")
        print(f"   🚢 Ships remaining: {ships_count}")
        print(f"   📜 Certificates remaining: {certificates_count}")
        
        print("\n✨ Database is now clean and ready for fresh data!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clean_test_data())
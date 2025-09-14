#!/usr/bin/env python3
"""
Clean Test Data Script
This script removes all test data from the MongoDB database while preserving essential admin user.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent / "backend"))

from mongodb_database import mongo_db

async def clean_test_data():
    """Clean all test data from MongoDB collections"""
    
    print("🧹 Starting test data cleanup...")
    
    try:
        # 1. Clean companies (keep only essential ones or remove all test companies)
        print("\n📋 Cleaning Companies...")
        companies = await mongo_db.find_all("companies")
        print(f"   Found {len(companies)} companies")
        
        # Remove all companies (or you can specify criteria to keep some)
        for company in companies:
            company_name = company.get('name_en', 'Unknown')
            if 'test' in company_name.lower() or 'logo' in company_name.lower():
                await mongo_db.delete("companies", {"id": company["id"]})
                print(f"   ✅ Deleted test company: {company_name}")
        
        # 2. Clean users (keep only essential admin users)
        print("\n👥 Cleaning Users...")
        users = await mongo_db.find_all("users")
        print(f"   Found {len(users)} users")
        
        # Keep essential users: admin, admin1 (you can modify this list)
        essential_users = ["admin", "admin1"]
        
        for user in users:
            username = user.get('username', 'Unknown')
            if username not in essential_users:
                await mongo_db.delete("users", {"id": user["id"]})
                print(f"   ✅ Deleted test user: {username}")
            else:
                print(f"   ⚠️ Kept essential user: {username}")
        
        # 3. Clean ships
        print("\n🚢 Cleaning Ships...")
        ships = await mongo_db.find_all("ships")
        print(f"   Found {len(ships)} ships")
        
        if ships:
            # Remove all test ships
            for ship in ships:
                ship_name = ship.get('name', 'Unknown')
                await mongo_db.delete("ships", {"id": ship["id"]})
                print(f"   ✅ Deleted ship: {ship_name}")
        
        # 4. Clean certificates
        print("\n📜 Cleaning Certificates...")
        certificates = await mongo_db.find_all("certificates")
        print(f"   Found {len(certificates)} certificates")
        
        if certificates:
            # Remove all test certificates
            for cert in certificates:
                cert_name = cert.get('name', 'Unknown')
                await mongo_db.delete("certificates", {"id": cert["id"]})
                print(f"   ✅ Deleted certificate: {cert_name}")
        
        # 5. Clean usage tracking
        print("\n📊 Cleaning Usage Tracking...")
        usage_data = await mongo_db.find_all("usage_tracking")
        print(f"   Found {len(usage_data)} usage tracking records")
        
        if usage_data:
            # Remove all usage tracking data
            for record in usage_data:
                await mongo_db.delete("usage_tracking", {"id": record["id"]})
            print(f"   ✅ Deleted all {len(usage_data)} usage tracking records")
        
        # 6. Clean AI config (optional - might want to keep)
        print("\n🤖 Cleaning AI Config...")
        ai_configs = await mongo_db.find_all("ai_config")
        print(f"   Found {len(ai_configs)} AI config records")
        
        # Uncomment if you want to clean AI configs too
        # if ai_configs:
        #     for config in ai_configs:
        #         await mongo_db.delete("ai_config", {"id": config["id"]})
        #     print(f"   ✅ Deleted all {len(ai_configs)} AI config records")
        
        # 7. Clean Google Drive configs (system level)
        print("\n☁️ Cleaning Google Drive Configs...")
        gdrive_configs = await mongo_db.find_all("gdrive_config")
        print(f"   Found {len(gdrive_configs)} Google Drive config records")
        
        if gdrive_configs:
            for config in gdrive_configs:
                await mongo_db.delete("gdrive_config", {"id": config["id"]})
            print(f"   ✅ Deleted all {len(gdrive_configs)} Google Drive config records")
        
        # 8. Clean any OAuth temp data
        print("\n🔐 Cleaning OAuth Temp Data...")
        try:
            # Find collections that might contain OAuth temp data
            collections = await mongo_db.db.list_collection_names()
            oauth_collections = [col for col in collections if 'oauth' in col.lower() or 'temp' in col.lower()]
            
            for col_name in oauth_collections:
                collection = mongo_db.db[col_name]
                result = await collection.delete_many({})
                if result.deleted_count > 0:
                    print(f"   ✅ Deleted {result.deleted_count} records from {col_name}")
        except Exception as e:
            print(f"   ⚠️ OAuth cleanup warning: {e}")
        
        print("\n🎉 Test data cleanup completed successfully!")
        print("\n📋 Summary:")
        print("   ✅ Companies: Removed test companies")
        print("   ✅ Users: Kept essential users (admin, admin1)")
        print("   ✅ Ships: Removed all ships")
        print("   ✅ Certificates: Removed all certificates") 
        print("   ✅ Usage Tracking: Cleaned all records")
        print("   ✅ Google Drive Configs: Cleaned system configs")
        print("   ✅ OAuth Temp Data: Cleaned temporary data")
        
        # Final verification
        print("\n🔍 Final verification:")
        companies_count = len(await mongo_db.find_all("companies"))
        users_count = len(await mongo_db.find_all("users"))
        ships_count = len(await mongo_db.find_all("ships"))
        certificates_count = len(await mongo_db.find_all("certificates"))
        
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
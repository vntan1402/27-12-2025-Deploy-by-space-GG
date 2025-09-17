import asyncio
import os
import sys
sys.path.append('/app/backend')

from mongodb_database import mongo_db

async def check_mongodb_gdrive_data():
    """Check MongoDB directly for Google Drive configuration data"""
    try:
        # Connect to MongoDB
        await mongo_db.connect()
        
        print("=== MONGODB DIRECT CHECK FOR GOOGLE DRIVE DATA ===")
        
        # Check all collections
        collections = await mongo_db.database.list_collection_names()
        print(f"\n📋 Available collections: {collections}")
        
        # Check company_gdrive_config collection
        print(f"\n🔍 Checking 'company_gdrive_config' collection:")
        try:
            company_configs = await mongo_db.find_all("company_gdrive_config", {})
            print(f"   Found {len(company_configs)} company Google Drive configurations:")
            for config in company_configs:
                print(f"   - Company ID: {config.get('company_id', 'N/A')}")
                print(f"     Web App URL: {config.get('web_app_url', 'N/A')}")
                print(f"     Folder ID: {config.get('folder_id', 'N/A')}")
                print(f"     Auth Method: {config.get('auth_method', 'N/A')}")
                print(f"     Service Account: {config.get('service_account_email', 'N/A')}")
                print(f"     Last Tested: {config.get('last_tested', 'N/A')}")
                print(f"     Test Result: {config.get('test_result', 'N/A')}")
                print(f"     Created At: {config.get('created_at', 'N/A')}")
                print(f"     Updated At: {config.get('updated_at', 'N/A')}")
                print()
        except Exception as e:
            print(f"   Error: {e}")
        
        # Check gdrive_config collection (system-wide)
        print(f"\n🔍 Checking 'gdrive_config' collection (system-wide):")
        try:
            system_configs = await mongo_db.find_all("gdrive_config", {})
            print(f"   Found {len(system_configs)} system Google Drive configurations:")
            for config in system_configs:
                print(f"   - ID: {config.get('id', 'N/A')}")
                print(f"     Configured: {config.get('configured', 'N/A')}")
                print(f"     Folder ID: {config.get('folder_id', 'N/A')}")
                print(f"     Service Account Email: {config.get('service_account_email', 'N/A')}")
                print(f"     Apps Script URL: {config.get('apps_script_url', 'N/A')}")
                print(f"     Created At: {config.get('created_at', 'N/A')}")
                print(f"     Updated At: {config.get('updated_at', 'N/A')}")
                print()
        except Exception as e:
            print(f"   Error: {e}")
        
        # Check companies collection for AMCSC
        print(f"\n🔍 Checking 'companies' collection for AMCSC:")
        try:
            amcsc_company = await mongo_db.find_one("companies", {"id": "cfe73cb0-cc88-4659-92a7-57cb413a5573"})
            if amcsc_company:
                print(f"   ✅ AMCSC company found:")
                print(f"     ID: {amcsc_company.get('id')}")
                print(f"     Name (VN): {amcsc_company.get('name_vn')}")
                print(f"     Name (EN): {amcsc_company.get('name_en')}")
                print(f"     Legacy Name: {amcsc_company.get('name')}")
                print(f"     Created At: {amcsc_company.get('created_at')}")
                print(f"     Updated At: {amcsc_company.get('updated_at')}")
            else:
                print(f"   ❌ AMCSC company not found")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Check for any collections with 'google' or 'drive' in the name
        print(f"\n🔍 Checking for any Google Drive related collections:")
        gdrive_collections = [col for col in collections if 'gdrive' in col.lower() or 'google' in col.lower() or 'drive' in col.lower()]
        if gdrive_collections:
            for col_name in gdrive_collections:
                print(f"\n   📁 Collection: {col_name}")
                try:
                    docs = await mongo_db.find_all(col_name, {})
                    print(f"      Found {len(docs)} documents:")
                    for doc in docs:
                        print(f"      - Document: {doc}")
                except Exception as e:
                    print(f"      Error: {e}")
        else:
            print(f"   No Google Drive related collections found")
        
        # Specific check for AMCSC company Google Drive config
        print(f"\n🎯 Specific check for AMCSC Google Drive configuration:")
        try:
            amcsc_config = await mongo_db.find_one("company_gdrive_config", {"company_id": "cfe73cb0-cc88-4659-92a7-57cb413a5573"})
            if amcsc_config:
                print(f"   ✅ AMCSC Google Drive configuration found:")
                for key, value in amcsc_config.items():
                    print(f"     {key}: {value}")
            else:
                print(f"   ❌ AMCSC Google Drive configuration NOT found")
        except Exception as e:
            print(f"   Error: {e}")
        
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
    finally:
        await mongo_db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_mongodb_gdrive_data())
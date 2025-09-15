#!/usr/bin/env python3
"""
Auto Clean up test data from Ship Management System MongoDB
Safely removes test data while preserving admin accounts and system configuration
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# MongoDB connection
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DATABASE_NAME = 'ship_management'

def cleanup_test_data():
    """Clean up test data from MongoDB"""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URL)
        db = client[DATABASE_NAME]
        
        print("🔗 Connected to MongoDB")
        print(f"📊 Database: {DATABASE_NAME}")
        print("-" * 50)
        
        # Get current data counts
        certificates_count = db.certificates.count_documents({})
        ships_count = db.ships.count_documents({})
        users_count = db.users.count_documents({})
        survey_status_count = db.ship_survey_status.count_documents({})
        usage_tracking_count = db.usage_tracking.count_documents({})
        
        print(f"📋 Current Data Count:")
        print(f"   Certificates: {certificates_count}")
        print(f"   Ships: {ships_count}")
        print(f"   Users: {users_count}")
        print(f"   Survey Status: {survey_status_count}")
        print(f"   Usage Tracking: {usage_tracking_count}")
        print("-" * 50)
        
        print("🧹 Starting cleanup process...")
        
        # 1. Delete all certificates
        print("📋 Deleting certificates...")
        result = db.certificates.delete_many({})
        print(f"   ✅ Deleted {result.deleted_count} certificates")
        
        # 2. Delete all ships
        print("🚢 Deleting ships...")
        result = db.ships.delete_many({})
        print(f"   ✅ Deleted {result.deleted_count} ships")
        
        # 3. Delete test users (keep admin accounts)
        print("👥 Deleting test users (keeping admin accounts)...")
        result = db.users.delete_many({
            "username": {"$nin": ["admin", "admin1"]}  # Keep admin accounts
        })
        print(f"   ✅ Deleted {result.deleted_count} test users (kept admin accounts)")
        
        # 4. Delete ship survey status records
        print("📊 Deleting ship survey status records...")
        result = db.ship_survey_status.delete_many({})
        print(f"   ✅ Deleted {result.deleted_count} survey status records")
        
        # 5. Delete usage tracking records
        print("🔍 Deleting usage tracking records...")
        result = db.usage_tracking.delete_many({})
        print(f"   ✅ Deleted {result.deleted_count} usage tracking records")
        
        # 6. Keep companies, ai_config, and other system data
        print("🏢 Keeping companies and system configuration...")
        companies_count = db.companies.count_documents({})
        ai_config_count = db.ai_config.count_documents({})
        print(f"   ✅ Preserved {companies_count} companies")
        print(f"   ✅ Preserved {ai_config_count} AI config records")
        
        print("-" * 50)
        print("🎉 Cleanup completed successfully!")
        
        # Show final counts
        print(f"\n📊 Final Data Count:")
        print(f"   Certificates: {db.certificates.count_documents({})}")
        print(f"   Ships: {db.ships.count_documents({})}")
        print(f"   Users: {db.users.count_documents({})}")
        print(f"   Survey Status: {db.ship_survey_status.count_documents({})}")
        print(f"   Usage Tracking: {db.usage_tracking.count_documents({})}")
        print(f"   Companies: {db.companies.count_documents({})}")
        print(f"   AI Config: {db.ai_config.count_documents({})}")
        
        # Show remaining admin users
        print(f"\n👥 Remaining Users:")
        users = db.users.find({}, {"username": 1, "company": 1, "role": 1})
        for user in users:
            print(f"   - {user['username']} ({user.get('role', 'N/A')}) - {user.get('company', 'N/A')}")
        
        print("\n✅ Test data cleanup completed!")
        print("💡 System is now clean and ready for production use.")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()
            print("🔒 MongoDB connection closed")

if __name__ == "__main__":
    print("""
🧹 Ship Management System - Auto Test Data Cleanup
==================================================""")
    cleanup_test_data()
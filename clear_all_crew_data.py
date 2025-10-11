#!/usr/bin/env python3
"""
Clear All Crew Data Script

This script will delete ALL crew members from the MongoDB database.
USE WITH CAUTION - this action cannot be undone!
"""

import os
import sys
import asyncio
from pymongo import MongoClient
from datetime import datetime

# Add the backend directory to sys.path to import mongo_db
sys.path.append('/app/backend')

async def clear_all_crew_data():
    """Clear all crew data from MongoDB"""
    try:
        # Get MongoDB URL from environment
        mongo_url = os.environ.get('MONGO_URL')
        if not mongo_url:
            print("❌ MONGO_URL environment variable not found")
            return False
        
        print(f"🔗 Connecting to MongoDB: {mongo_url}")
        
        # Connect to MongoDB
        client = MongoClient(mongo_url)
        db = client.ship_management
        crew_collection = db.crew_members
        
        # Count existing crew members
        crew_count = crew_collection.count_documents({})
        print(f"📊 Found {crew_count} crew members in database")
        
        if crew_count == 0:
            print("✅ No crew members found - database is already clean")
            return True
        
        # Ask for confirmation
        print(f"⚠️  WARNING: This will DELETE ALL {crew_count} crew members!")
        print("⚠️  This action CANNOT be undone!")
        
        confirmation = input("Are you sure you want to proceed? Type 'DELETE ALL CREW' to confirm: ")
        
        if confirmation != 'DELETE ALL CREW':
            print("❌ Operation cancelled - incorrect confirmation")
            return False
        
        # Delete all crew members
        print(f"🗑️ Deleting all {crew_count} crew members...")
        result = crew_collection.delete_many({})
        
        print(f"✅ Successfully deleted {result.deleted_count} crew members")
        print(f"📊 Remaining crew count: {crew_collection.count_documents({})}")
        
        # Log the operation
        audit_collection = db.audit_logs
        audit_entry = {
            "timestamp": datetime.utcnow(),
            "action": "CLEAR_ALL_CREW_DATA",
            "user": "system_admin",
            "details": {
                "deleted_count": result.deleted_count,
                "operation_time": datetime.utcnow().isoformat()
            }
        }
        audit_collection.insert_one(audit_entry)
        print("📝 Audit log entry created")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error clearing crew data: {str(e)}")
        return False

def main():
    """Main function"""
    print("🧹 CREW DATA CLEARING UTILITY")
    print("=" * 50)
    
    # Run the async function
    success = asyncio.run(clear_all_crew_data())
    
    if success:
        print("✅ Crew data clearing completed successfully")
    else:
        print("❌ Crew data clearing failed")
    
    return success

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script to delete ALL Survey Reports from MongoDB
WARNING: This will permanently delete all survey report data
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def delete_all_survey_reports():
    """Delete all survey reports from database"""
    try:
        # Get MongoDB URL from environment
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_url)
        db = client.ship_management
        
        print("🔗 Connected to MongoDB")
        
        # Count existing survey reports
        count_before = await db.survey_reports.count_documents({})
        print(f"📊 Found {count_before} Survey Reports in database")
        
        if count_before == 0:
            print("✅ No Survey Reports to delete")
            return
        
        # Delete all survey reports
        print("🗑️ Deleting all Survey Reports...")
        result = await db.survey_reports.delete_many({})
        
        print(f"✅ Successfully deleted {result.deleted_count} Survey Reports")
        
        # Verify deletion
        count_after = await db.survey_reports.count_documents({})
        print(f"📊 Remaining Survey Reports: {count_after}")
        
        if count_after == 0:
            print("✅ All Survey Reports have been deleted successfully!")
        else:
            print(f"⚠️ Warning: {count_after} Survey Reports still remain")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        client.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    print("=" * 60)
    print("⚠️  DELETE ALL SURVEY REPORTS")
    print("=" * 60)
    print()
    
    asyncio.run(delete_all_survey_reports())
    
    print()
    print("=" * 60)
    print("✅ Script completed")
    print("=" * 60)

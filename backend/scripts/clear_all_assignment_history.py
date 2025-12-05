"""
Script to clear all crew assignment history records
WARNING: This will delete ALL assignment history data permanently!
"""

import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.mongodb import mongo_db
from motor.motor_asyncio import AsyncIOMotorClient


async def clear_all_assignment_history():
    """
    Delete all records from crew_assignment_history collection
    """
    try:
        print("⚠️  WARNING: This will delete ALL assignment history records!")
        print("This action cannot be undone.")
        
        # Connect to database
        print("\n📡 Connecting to MongoDB...")
        await mongo_db.connect()
        print("✅ Connected to MongoDB")
        
        collection = mongo_db.database["crew_assignment_history"]
        
        # Count records before deletion
        count_before = await collection.count_documents({})
        print(f"\n📊 Found {count_before} assignment history records")
        
        if count_before == 0:
            print("ℹ️  No records to delete. Collection is already empty.")
            return
        
        # Confirm deletion
        print("\n❓ Are you sure you want to delete all records?")
        print("Type 'YES' to confirm, or anything else to cancel:")
        confirmation = input().strip()
        
        if confirmation != 'YES':
            print("❌ Operation cancelled by user")
            return
        
        # Delete all records
        print("\n🗑️  Deleting all assignment history records...")
        result = await collection.delete_many({})
        
        # Count records after deletion
        count_after = await collection.count_documents({})
        
        print(f"\n✅ Successfully deleted {result.deleted_count} records")
        print(f"📊 Records remaining: {count_after}")
        
        if count_after == 0:
            print("✅ Assignment history collection is now empty")
        else:
            print(f"⚠️  Warning: {count_after} records still remain")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect from database
        print("\n📡 Disconnecting from MongoDB...")
        await mongo_db.disconnect()
        print("✅ Disconnected")


async def main():
    """Main entry point"""
    await clear_all_assignment_history()


if __name__ == "__main__":
    print("=" * 60)
    print("🗑️  CLEAR ALL ASSIGNMENT HISTORY")
    print("=" * 60)
    asyncio.run(main())

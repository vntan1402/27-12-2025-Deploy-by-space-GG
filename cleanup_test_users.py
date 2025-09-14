#!/usr/bin/env python3
"""
Script to clean up test users while keeping only admin and admin1
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to Python path
import sys
sys.path.append(str(Path(__file__).parent / 'backend'))

from mongodb_database import mongo_db

# Load environment variables
load_dotenv(Path(__file__).parent / 'backend' / '.env')

async def cleanup_test_users():
    """Remove all test users except admin and admin1"""
    
    try:
        print("🔍 Connecting to MongoDB...")
        
        # Get all current users
        all_users = await mongo_db.find_all("users")
        print(f"📊 Found {len(all_users)} total users")
        
        # Show current users
        print("\n📋 Current users:")
        for user in all_users:
            print(f"  - {user.get('username')} ({user.get('full_name')}) - {user.get('role')}")
        
        # Users to keep (admin accounts)
        users_to_keep = ['admin', 'admin1']
        
        # Find users to delete
        users_to_delete = []
        for user in all_users:
            if user.get('username') not in users_to_keep:
                users_to_delete.append(user)
        
        if not users_to_delete:
            print("\n✅ No test users to delete. Only admin accounts found.")
            return
        
        print(f"\n🗑️  Users to be deleted ({len(users_to_delete)}):")
        for user in users_to_delete:
            print(f"  - {user.get('username')} ({user.get('full_name')}) - {user.get('role')}")
        
        # Confirm deletion
        print(f"\n⚠️  About to delete {len(users_to_delete)} test users...")
        print("   Keeping: admin, admin1")
        
        # Delete test users
        deleted_count = 0
        for user in users_to_delete:
            try:
                success = await mongo_db.delete("users", {"id": user["id"]})
                if success:
                    deleted_count += 1
                    print(f"   ✅ Deleted: {user.get('username')}")
                else:
                    print(f"   ❌ Failed to delete: {user.get('username')}")
            except Exception as e:
                print(f"   ❌ Error deleting {user.get('username')}: {e}")
        
        # Verify cleanup
        remaining_users = await mongo_db.find_all("users")
        print(f"\n📊 Cleanup complete!")
        print(f"   Deleted: {deleted_count} users")
        print(f"   Remaining: {len(remaining_users)} users")
        
        print("\n📋 Remaining users:")
        for user in remaining_users:
            print(f"  - {user.get('username')} ({user.get('full_name')}) - {user.get('role')}")
            
        # Update usage tracking to clean up old entries from deleted users
        print("\n🧹 Cleaning up usage tracking records...")
        remaining_user_ids = [user["id"] for user in remaining_users]
        
        # Get all usage tracking records
        all_usage = await mongo_db.find_all("usage_tracking")
        usage_to_delete = []
        
        for usage in all_usage:
            if usage.get("user_id") not in remaining_user_ids:
                usage_to_delete.append(usage)
        
        # Delete orphaned usage records
        deleted_usage = 0
        for usage in usage_to_delete:
            try:
                success = await mongo_db.delete("usage_tracking", {"_id": usage["_id"]})
                if success:
                    deleted_usage += 1
            except Exception as e:
                print(f"   ❌ Error deleting usage record: {e}")
        
        if deleted_usage > 0:
            print(f"   ✅ Cleaned up {deleted_usage} orphaned usage tracking records")
        else:
            print("   ✅ No orphaned usage tracking records found")
            
        print("\n🎉 User cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(cleanup_test_users())
"""
Remove unique constraint on email field to allow multiple users with same email
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def remove_email_unique_index():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('MONGODB_DB_NAME', 'ship_management')
    
    print("🔓 Removing unique constraint on email field")
    print("=" * 60)
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Check current indexes
        indexes = await db.users.index_information()
        print("\n📋 Current indexes:")
        for name, info in indexes.items():
            print(f"  - {name}: {info}")
        
        # Drop email_1 index if exists
        if 'email_1' in indexes:
            print("\n🔄 Dropping email_1 index...")
            await db.users.drop_index('email_1')
            print("✅ Email unique index removed")
            print("   Multiple users can now share the same email")
        else:
            print("\n✅ No email index found - already removed")
        
        # Show final indexes
        final_indexes = await db.users.index_information()
        print("\n📋 Final indexes:")
        for name, info in final_indexes.items():
            print(f"  - {name}: {info}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(remove_email_unique_index())

"""
Recreate email index with proper sparse settings.
MongoDB sparse indexes should allow multiple null values.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def recreate_email_index():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('MONGODB_DB_NAME', 'ship_management')
    
    print(f"Connecting to MongoDB: {mongo_url}")
    print(f"Database: {db_name}")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Drop email index if exists
        print("\n🔄 Dropping email_1 index...")
        try:
            await db.users.drop_index('email_1')
            print("✅ Index dropped")
        except Exception as e:
            print(f"⚠️  Index might not exist: {e}")
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Recreate with sparse option
        print("\n🔄 Creating new sparse unique index...")
        result = await db.users.create_index(
            [("email", 1)], 
            unique=True, 
            sparse=True,
            name="email_1"
        )
        print(f"✅ Index created: {result}")
        
        # Verify
        indexes = await db.users.index_information()
        email_index = indexes.get('email_1', {})
        print(f"\n📋 Email index info: {email_index}")
        print(f"   - Unique: {email_index.get('unique', False)}")
        print(f"   - Sparse: {email_index.get('sparse', False)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(recreate_email_index())

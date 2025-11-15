"""
Fix email index using partial index.
Partial indexes only index documents where the field exists and is not null.
This allows multiple users with null emails while enforcing uniqueness for non-null emails.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_email_index_partial():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('MONGODB_DB_NAME', 'ship_management')
    
    print(f"Connecting to MongoDB: {mongo_url}")
    print(f"Database: {db_name}")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Drop existing email index
        print("\n🔄 Dropping email_1 index...")
        try:
            await db.users.drop_index('email_1')
            print("✅ Index dropped")
        except Exception as e:
            print(f"⚠️  Index might not exist: {e}")
        
        await asyncio.sleep(1)
        
        # Create partial index that only indexes non-null emails
        print("\n🔄 Creating partial unique index on email...")
        print("   This index will:")
        print("   - Only index documents where email is not null")
        print("   - Enforce uniqueness only for non-null email values")
        print("   - Allow unlimited users with null emails")
        
        result = await db.users.create_index(
            [("email", 1)],
            unique=True,
            name="email_1",
            partialFilterExpression={"email": {"$type": "string"}}  # Only index when email is a string (not null)
        )
        print(f"✅ Partial index created: {result}")
        
        # Verify
        indexes = await db.users.index_information()
        email_index = indexes.get('email_1', {})
        print(f"\n📋 Email index info:")
        for key, value in email_index.items():
            print(f"   - {key}: {value}")
        
        print("\n✅ Email index fix completed!")
        print("   You can now create multiple users with null emails.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_email_index_partial())

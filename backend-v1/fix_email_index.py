"""
Migration script to fix email index in users collection.
This script drops the existing non-sparse unique index on email
and recreates it as a sparse unique index to allow multiple null values.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure

async def fix_email_index():
    # Get MongoDB URL from environment
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('MONGODB_DB_NAME', 'ship_management')
    
    print(f"Connecting to MongoDB: {mongo_url}")
    print(f"Database: {db_name}")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # List existing indexes
        indexes = await db.users.index_information()
        print("\n📋 Current indexes on 'users' collection:")
        for index_name, index_info in indexes.items():
            print(f"  - {index_name}: {index_info}")
        
        # Check if email_1 index exists
        if 'email_1' in indexes:
            email_index = indexes['email_1']
            is_sparse = email_index.get('sparse', False)
            
            if not is_sparse:
                print("\n⚠️  Found non-sparse unique index on 'email' field")
                print("🔄 Dropping the old index...")
                
                # Drop the old index
                await db.users.drop_index('email_1')
                print("✅ Old index dropped successfully")
                
                # Create new sparse unique index
                print("🔄 Creating new sparse unique index on 'email'...")
                await db.users.create_index("email", unique=True, sparse=True)
                print("✅ New sparse unique index created successfully")
            else:
                print("\n✅ Email index is already sparse - no changes needed")
        else:
            print("\n⚠️  No email index found")
            print("🔄 Creating sparse unique index on 'email'...")
            await db.users.create_index("email", unique=True, sparse=True)
            print("✅ Sparse unique index created successfully")
        
        # Show final indexes
        print("\n📋 Final indexes on 'users' collection:")
        final_indexes = await db.users.index_information()
        for index_name, index_info in final_indexes.items():
            print(f"  - {index_name}: {index_info}")
        
        print("\n✅ Email index fix completed successfully!")
        
    except OperationFailure as e:
        print(f"\n❌ MongoDB operation failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(fix_email_index())
    exit(0 if success else 1)

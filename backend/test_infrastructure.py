"""Test basic infrastructure"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.mongodb import mongo_db
from app.core.config import settings

async def test_db_connection():
    print(f"Testing MongoDB connection to: {settings.DB_NAME}")
    try:
        await mongo_db.connect()
        print("✅ Database connected successfully")
        
        # Test a simple query
        collections = await mongo_db.list_collections()
        print(f"✅ Found {len(collections)} collections: {collections}")
        
        await mongo_db.disconnect()
        print("✅ Database disconnected successfully")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_config():
    print("\nTesting configuration:")
    print(f"  PROJECT_NAME: {settings.PROJECT_NAME}")
    print(f"  VERSION: {settings.VERSION}")
    print(f"  DB_NAME: {settings.DB_NAME}")
    print(f"  JWT_SECRET: {'***' if settings.JWT_SECRET else 'NOT SET'}")
    print(f"  EMERGENT_LLM_KEY: {'***' if settings.EMERGENT_LLM_KEY else 'NOT SET'}")
    print("✅ Configuration loaded")

async def test_imports():
    print("\nTesting imports:")
    try:
        from app.core.config import settings
        print("✅ app.core.config imported")
        
        from app.core.security import create_access_token, verify_token
        print("✅ app.core.security imported")
        
        from app.db.mongodb import mongo_db
        print("✅ app.db.mongodb imported")
        
        from app.api.v1 import api_router
        print("✅ app.api.v1 imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

async def main():
    print("=" * 60)
    print("INFRASTRUCTURE TEST - Backend V2")
    print("=" * 60)
    
    await test_config()
    
    import_success = await test_imports()
    if not import_success:
        print("\n❌ Import tests failed!")
        return
    
    db_success = await test_db_connection()
    
    print("\n" + "=" * 60)
    if db_success:
        print("ALL TESTS PASSED ✅")
    else:
        print("SOME TESTS FAILED ❌")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

"""
Script to create admin user in production MongoDB
Run this script to initialize admin in the new database
"""
import asyncio
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import hashlib
import os

# Production MongoDB URL
MONGO_URL = "mongodb+srv://shipmanagementmtd_db_user:Natnv1482DB@ship-management-cluster.wdfaecd.mongodb.net/?appName=ship-management-cluster"
DB_NAME = "ship-management-cluster"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123456"
ADMIN_EMAIL = "admin@company.com"
ADMIN_FULL_NAME = "System Administrator"

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

async def create_admin():
    """Create admin user in production database"""
    print(f"🔗 Connecting to MongoDB: {DB_NAME}")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Test connection
    await client.admin.command('ping')
    print("✅ Connected to MongoDB successfully!")
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"username": ADMIN_USERNAME})
    if existing_admin:
        print(f"⚠️ Admin user '{ADMIN_USERNAME}' already exists!")
        client.close()
        return
    
    # Create admin user
    hashed_password = hash_password(ADMIN_PASSWORD)
    
    user_data = {
        'id': str(uuid.uuid4()),
        'username': ADMIN_USERNAME,
        'email': ADMIN_EMAIL,
        'full_name': ADMIN_FULL_NAME,
        'password_hash': hashed_password,
        'password': hashed_password,
        'role': 'system_admin',
        'department': ['technical', 'operations', 'safety', 'commercial', 'crewing'],
        'company': '',
        'ship': None,
        'zalo': '',
        'gmail': ADMIN_EMAIL,
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'created_by': 'system',
        'updated_at': None,
        'updated_by': None
    }
    
    result = await db.users.insert_one(user_data)
    print("=" * 60)
    print("✅ ADMIN USER CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Username:     {ADMIN_USERNAME}")
    print(f"Password:     {ADMIN_PASSWORD}")
    print(f"Email:        {ADMIN_EMAIL}")
    print(f"Role:         system_admin")
    print("=" * 60)
    
    # Also create indexes
    print("📊 Creating indexes...")
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True, sparse=True)
    print("✅ Indexes created!")
    
    client.close()
    print("🔒 Connection closed")

if __name__ == "__main__":
    asyncio.run(create_admin())

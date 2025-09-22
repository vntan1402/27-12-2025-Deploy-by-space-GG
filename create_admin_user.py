#!/usr/bin/env python3

import asyncio
import bcrypt
import uuid
from datetime import datetime, timezone
import sys
import os

# Add the backend directory to Python path
sys.path.append('/app/backend')

from mongodb_database import mongo_db

async def create_admin_user():
    try:
        # Connect to database
        await mongo_db.connect()
        print("✅ Connected to MongoDB")
        
        # Check if admin user already exists
        existing_admin = await mongo_db.find_one("users", {"username": "admin"})
        if existing_admin:
            print("⚠️ Admin user already exists")
            return
        
        # Hash password for admin123
        password = 'admin123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        admin_user = {
            'id': str(uuid.uuid4()),
            'username': 'admin',
            'password_hash': password_hash,
            'role': 'super_admin',
            'full_name': 'System Administrator',
            'email': 'admin@system.com',
            'is_active': True,
            'created_at': datetime.now(timezone.utc)
        }
        
        # Create admin user
        await mongo_db.create("users", admin_user)
        print("✅ Admin user created successfully!")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Role: super_admin")
        print(f"   ID: {admin_user['id']}")
        
        # Also create admin1 user as mentioned in test results
        existing_admin1 = await mongo_db.find_one("users", {"username": "admin1"})
        if not existing_admin1:
            password_hash1 = bcrypt.hashpw('123456'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin1_user = {
                'id': str(uuid.uuid4()),
                'username': 'admin1',
                'password_hash': password_hash1,
                'role': 'admin',
                'full_name': 'Admin User 1',
                'email': 'admin1@system.com',
                'is_active': True,
                'created_at': datetime.now(timezone.utc)
            }
            await mongo_db.create("users", admin1_user)
            print("✅ Admin1 user created successfully!")
            print(f"   Username: admin1")
            print(f"   Password: 123456")
            print(f"   Role: admin")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
    finally:
        await mongo_db.disconnect()

if __name__ == "__main__":
    asyncio.run(create_admin_user())
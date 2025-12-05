"""
Create First Admin User - Interactive version
Run this script ONCE after deploying to create the initial admin account

Usage:
    cd /app/backend
    python3 scripts/create_first_admin.py
"""
import asyncio
import sys
import os
from pathlib import Path
import getpass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.mongodb import mongo_db
from app.core.security import hash_password
from datetime import datetime, timezone
import uuid

async def create_first_admin():
    """Create the first admin user in production"""
    await mongo_db.connect()
    
    print("=" * 60)
    print("🔐 CREATE FIRST ADMIN USER")
    print("=" * 60)
    print()
    
    try:
        # Check if any users already exist
        existing_users = await mongo_db.find_all('users', {})
        if existing_users:
            print("⚠️  WARNING: Users already exist in database!")
            print(f"   Found {len(existing_users)} existing users:")
            for user in existing_users[:5]:  # Show first 5
                print(f"   - {user.get('username', 'N/A')} ({user.get('role', 'N/A')})")
            print()
            response = input("Do you want to continue creating a new admin? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cancelled")
                await mongo_db.disconnect()
                return
            print()
        
        # Get admin information
        print("📝 Enter Admin Information:")
        print("-" * 60)
        
        username = input("Username (e.g., admin): ").strip()
        if not username:
            print("❌ Username cannot be empty!")
            await mongo_db.disconnect()
            return
        
        # Check if username already exists
        existing = await mongo_db.find_one('users', {'username': username})
        if existing:
            print(f"❌ Username '{username}' already exists!")
            await mongo_db.disconnect()
            return
        
        email = input("Email (e.g., admin@company.com): ").strip()
        full_name = input("Full Name (e.g., System Administrator): ").strip()
        
        # Password input
        password = getpass.getpass("Password (will be hidden): ")
        password_confirm = getpass.getpass("Confirm Password: ")
        
        if password != password_confirm:
            print("❌ Passwords do not match!")
            await mongo_db.disconnect()
            return
        
        if len(password) < 6:
            print("❌ Password must be at least 6 characters!")
            await mongo_db.disconnect()
            return
        
        # Create company if needed
        print()
        print("🏢 Company Setup:")
        print("-" * 60)
        create_company = input("Create a new company? (yes/no): ").strip().lower()
        
        company_id = ''
        company_name = None
        if create_company == 'yes':
            company_name = input("Company Name: ").strip()
            company_email = input("Company Email: ").strip()
            company_phone = input("Company Phone (optional): ").strip()
            
            company_id = str(uuid.uuid4())
            company_data = {
                "id": company_id,
                "name": company_name,
                "name_en": company_name,
                "name_vn": company_name,
                "email": company_email,
                "phone": company_phone,
                "address": "",
                "logo_url": "",
                "created_at": datetime.now(timezone.utc),
                "created_by": "system"
            }
            
            await mongo_db.create('companies', company_data)
            print(f"✅ Company '{company_name}' created!")
        
        # Create admin user
        print()
        print("👤 Creating Admin User...")
        print("-" * 60)
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Determine role
        role = "admin" if company_id else "system_admin"
        
        # Create user
        user_data = {
            "id": str(uuid.uuid4()),
            "username": username,
            "email": email,
            "full_name": full_name,
            "password_hash": hashed_password,
            "password": hashed_password,
            "role": role,
            "department": ["technical", "operations"],
            "company": company_id,
            "ship": None,
            "zalo": "",
            "gmail": email,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "created_by": "system"
        }
        
        await mongo_db.create('users', user_data)
        
        # Success message
        print()
        print("=" * 60)
        print("✅ ADMIN USER CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Username:     {username}")
        print(f"Email:        {email}")
        print(f"Full Name:    {full_name}")
        print(f"Role:         {role.upper()}")
        if company_name:
            print(f"Company:      {company_name}")
        print("=" * 60)
        print("🚀 You can now login with these credentials!")
        print("⚠️  IMPORTANT: Change the password after first login!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await mongo_db.disconnect()

if __name__ == "__main__":
    asyncio.run(create_first_admin())

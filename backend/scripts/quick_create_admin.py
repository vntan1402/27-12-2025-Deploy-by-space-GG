"""
Quick Admin Creator - Non-interactive version
Use this if you want to quickly create an admin without prompts

Usage:
1. Edit the values below
2. Run: python3 scripts/quick_create_admin.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.mongodb import mongo_db
from app.core.security import hash_password
from datetime import datetime, timezone
import uuid

# ==========================================
# ⚠️  EDIT THESE VALUES
# ==========================================
ADMIN_USERNAME = "production_admin"
ADMIN_EMAIL = "admin@production.com"
ADMIN_FULL_NAME = "Production Administrator"
ADMIN_PASSWORD = "Admin@2024"  # ⚠️ CHANGE THIS!
COMPANY_NAME = None  # Set to company name or None for system_admin
# ==========================================

async def quick_create_admin():
    """
    Quickly create an admin user
    """
    await mongo_db.connect()
    
    print("=" * 60)
    print("⚡ QUICK ADMIN CREATOR")
    print("=" * 60)
    
    try:
        # Check if username exists
        existing = await mongo_db.find_one('users', {'username': ADMIN_USERNAME})
        if existing:
            print(f"❌ Username '{ADMIN_USERNAME}' already exists!")
            print(f"   Try a different username or delete existing user first.")
            await mongo_db.disconnect()
            return
        
        # Create company if specified
        company_id = ''
        if COMPANY_NAME:
            # Check if company exists
            existing_company = await mongo_db.find_one('companies', {'name': COMPANY_NAME})
            if existing_company:
                company_id = existing_company['id']
                print(f"ℹ️  Using existing company: {COMPANY_NAME}")
            else:
                company_id = str(uuid.uuid4())
                company_data = {
                    "id": company_id,
                    "name": COMPANY_NAME,
                    "name_en": COMPANY_NAME,
                    "name_vn": COMPANY_NAME,
                    "email": ADMIN_EMAIL,
                    "phone": "",
                    "address": "",
                    "logo_url": "",
                    "created_at": datetime.now(timezone.utc),
                    "created_by": "system"
                }
                await mongo_db.create('companies', company_data)
                print(f"✅ Company created: {COMPANY_NAME}")
        
        # Hash password
        hashed_password = hash_password(ADMIN_PASSWORD)
        
        # Determine role
        role = "admin" if company_id else "system_admin"
        
        # Create admin user
        user_data = {
            "id": str(uuid.uuid4()),
            "username": ADMIN_USERNAME,
            "email": ADMIN_EMAIL,
            "full_name": ADMIN_FULL_NAME,
            "password_hash": hashed_password,
            "password": hashed_password,
            "role": role,
            "department": ["technical", "operations"],
            "company": company_id,
            "ship": None,
            "zalo": "",
            "gmail": ADMIN_EMAIL,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "created_by": "system"
        }
        
        await mongo_db.create('users', user_data)
        
        print("=" * 60)
        print("✅ ADMIN USER CREATED!")
        print("=" * 60)
        print(f"Username:     {ADMIN_USERNAME}")
        print(f"Email:        {ADMIN_EMAIL}")
        print(f"Password:     {ADMIN_PASSWORD}")
        print(f"Role:         {role.upper()}")
        if COMPANY_NAME:
            print(f"Company:      {COMPANY_NAME}")
        print("=" * 60)
        print("🚀 Ready to login!")
        print("⚠️  IMPORTANT: Change the password after first login!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await mongo_db.disconnect()

if __name__ == "__main__":
    asyncio.run(quick_create_admin())

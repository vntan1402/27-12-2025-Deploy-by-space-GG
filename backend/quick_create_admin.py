"""
Quick Admin Creator - Non-interactive version
Use this if you want to quickly create an admin without prompts
"""
import asyncio
from mongodb_database import mongo_db
import bcrypt
from datetime import datetime
import uuid

async def quick_create_admin(
    username="production_admin",
    email="admin@production.com",
    full_name="Production Administrator", 
    password="Admin@123",
    company_name=None
):
    """
    Quickly create an admin user
    
    Args:
        username: Admin username
        email: Admin email
        full_name: Full name of admin
        password: Admin password (will be hashed)
        company_name: Optional company name to create
    """
    await mongo_db.connect()
    
    print("=" * 60)
    print("⚡ QUICK ADMIN CREATOR")
    print("=" * 60)
    
    # Check if username exists
    existing = await mongo_db.find_one('users', {'username': username})
    if existing:
        print(f"❌ Username '{username}' already exists!")
        print(f"   Try a different username or delete existing user first.")
        await mongo_db.disconnect()
        return None
    
    # Create company if specified
    company_id = None
    if company_name:
        # Check if company exists
        existing_company = await mongo_db.find_one('companies', {'name': company_name})
        if existing_company:
            company_id = existing_company['id']
            print(f"ℹ️  Using existing company: {company_name}")
        else:
            company_id = str(uuid.uuid4())
            company_data = {
                "id": company_id,
                "name": company_name,
                "email": email,
                "phone": "",
                "address": "",
                "logo_url": "",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            await mongo_db.insert('companies', company_data)
            print(f"✅ Company created: {company_name}")
    
    # Hash password
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # Create admin user
    user_data = {
        "id": str(uuid.uuid4()),
        "username": username,
        "email": email,
        "full_name": full_name,
        "password": hashed_password,
        "role": "super_admin",
        "department": ["technical", "operations"],
        "company": company_id,
        "ship": None,
        "zalo": "",
        "gmail": email,
        "is_active": True,
        "created_at": datetime.now()
    }
    
    await mongo_db.insert('users', user_data)
    
    print("=" * 60)
    print("✅ ADMIN USER CREATED!")
    print("=" * 60)
    print(f"Username:     {username}")
    print(f"Email:        {email}")
    print(f"Password:     {password}")
    print(f"Role:         SUPER_ADMIN")
    if company_name:
        print(f"Company:      {company_name}")
    print("=" * 60)
    print("🚀 Ready to login!")
    print("=" * 60)
    
    await mongo_db.disconnect()
    
    return {
        "username": username,
        "email": email,
        "password": password,
        "company": company_name
    }


# Example usage in script
if __name__ == "__main__":
    print()
    print("🎯 Creating admin with default settings...")
    print("   To customize, edit the values below:")
    print()
    
    # ============================================
    # 🔧 CUSTOMIZE THESE VALUES:
    # ============================================
    ADMIN_USERNAME = "production_admin"           # Change this
    ADMIN_EMAIL = "admin@yourcompany.com"         # Change this
    ADMIN_FULL_NAME = "System Administrator"      # Change this
    ADMIN_PASSWORD = "Admin@2024"                 # Change this - IMPORTANT!
    COMPANY_NAME = "Your Company Ltd"             # Change this or set to None
    # ============================================
    
    result = asyncio.run(quick_create_admin(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        full_name=ADMIN_FULL_NAME,
        password=ADMIN_PASSWORD,
        company_name=COMPANY_NAME
    ))
    
    if result:
        print()
        print("⚠️  IMPORTANT: Save these credentials securely!")
        print()

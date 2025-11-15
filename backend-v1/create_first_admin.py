"""
Create First Admin User in Production
Run this script ONCE after deploying to create the initial admin account
"""
import asyncio
from mongodb_database import mongo_db
import bcrypt
from datetime import datetime
import uuid

async def create_first_admin():
    """Create the first admin user in production"""
    await mongo_db.connect()
    
    print("=" * 60)
    print("🔐 CREATE FIRST ADMIN USER FOR PRODUCTION")
    print("=" * 60)
    print()
    
    # Check if any users already exist
    existing_users = await mongo_db.find_all('users', {})
    if existing_users:
        print("⚠️  WARNING: Users already exist in database!")
        print(f"   Found {len(existing_users)} existing users:")
        for user in existing_users:
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
    import getpass
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
    
    company_id = None
    if create_company == 'yes':
        company_name = input("Company Name: ").strip()
        company_email = input("Company Email: ").strip()
        company_phone = input("Company Phone: ").strip()
        
        company_id = str(uuid.uuid4())
        company_data = {
            "id": company_id,
            "name": company_name,
            "email": company_email,
            "phone": company_phone,
            "address": "",
            "logo_url": "",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        await mongo_db.insert('companies', company_data)
        print(f"✅ Company '{company_name}' created!")
    
    # Create admin user
    print()
    print("👤 Creating Admin User...")
    print("-" * 60)
    
    # Hash password
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    user_data = {
        "id": str(uuid.uuid4()),
        "username": username,
        "email": email,
        "full_name": full_name,
        "password": hashed_password,
        "role": "system_admin",  # Highest permission level - can create all roles
        "department": ["technical", "operations"],
        "company": company_id,
        "ship": None,
        "zalo": "",
        "gmail": email,
        "is_active": True,
        "created_at": datetime.now()
    }
    
    await mongo_db.insert('users', user_data)
    
    print()
    print("=" * 60)
    print("✅ ADMIN USER CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Role: SUPER_ADMIN")
    print(f"Company: {company_name if create_company == 'yes' else 'None'}")
    print()
    print("🚀 You can now login with these credentials!")
    print("=" * 60)
    
    await mongo_db.disconnect()

if __name__ == "__main__":
    print()
    print("⚠️  IMPORTANT: Run this script ONLY ONCE in production!")
    print("   This creates the first admin user with full permissions.")
    print()
    
    try:
        asyncio.run(create_first_admin())
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

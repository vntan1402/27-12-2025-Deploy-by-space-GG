"""
Database Seeding Script
Creates initial test data for the Ship Management System
"""
import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
import uuid

async def seed_database():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.getenv('DB_NAME', 'ship_management')
    db = client[db_name]
    
    print("🌱 Starting database seeding...")
    print(f"📊 Using database: {db_name}")
    
    # 1. Create test company
    company_id = str(uuid.uuid4())
    company = {
        "id": company_id,
        "name_vn": "Công ty Cổ phần Quản lý và Vận hành Tàu biển AMCSC",
        "name_en": "AMCSC Shipping Management Company",
        "code": "AMCSC",
        "address_vn": "Thành phố Hồ Chí Minh, Việt Nam",
        "address_en": "Ho Chi Minh City, Vietnam",
        "tax_id": "0123456789",
        "email": "contact@amcsc.vn",
        "phone": "+84 123 456 789",
        "gmail": "contact@amcsc.vn",
        "zalo": "0123456789",
        "logo_url": "",
        "system_expiry": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    existing_company = await db.companies.find_one({"code": "AMCSC"})
    if not existing_company:
        await db.companies.insert_one(company)
        print(f"✅ Created company: {company['name_en']} (ID: {company_id})")
    else:
        company_id = existing_company['id']
        print(f"ℹ️  Company already exists: {existing_company.get('name_en', existing_company.get('name'))} (ID: {company_id})")
    
    # 2. Create test admin user (admin role)
    password_admin1 = "123456"
    password_hash_admin1 = bcrypt.hashpw(password_admin1.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "username": "admin1@amcsc.vn",
        "password_hash": password_hash_admin1,
        "email": "admin1@amcsc.vn",
        "full_name": "Admin User",
        "role": "admin",  # lowercase to match UserRole enum
        "company": company_id,
        "department": ["operations", "technical"],  # Changed to array
        "zalo": "0123456789",  # Required field
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    existing_user = await db.users.find_one({"username": "admin1@amcsc.vn"})
    if not existing_user:
        await db.users.insert_one(user)
        print(f"✅ Created user: {user['username']} (Password: {password_admin1})")
    else:
        print(f"ℹ️  User already exists: {existing_user['username']}")
    
    # 2b. Create second admin user with simple username (admin role)
    user_id_2 = str(uuid.uuid4())
    user_2 = {
        "id": user_id_2,
        "username": "admin1",
        "password_hash": password_hash_admin1,
        "email": "admin.simple@amcsc.vn",  # Different email to avoid duplicate
        "full_name": "Admin User (Simple Login)",
        "role": "admin",
        "company": company_id,
        "department": ["operations", "commercial"],  # Changed to array
        "zalo": "0123456789",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    existing_user_2 = await db.users.find_one({"username": "admin1"})
    if not existing_user_2:
        await db.users.insert_one(user_2)
        print(f"✅ Created user: {user_2['username']} (Password: {password_admin1})")
    else:
        print(f"ℹ️  User already exists: {existing_user_2['username']}")
    
    # 2c. Create super admin user
    password_super = "admin123"
    password_hash_super = bcrypt.hashpw(password_super.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_id_super = str(uuid.uuid4())
    user_super = {
        "id": user_id_super,
        "username": "admin",
        "password_hash": password_hash_super,
        "email": "admin@amcsc.vn",
        "full_name": "Super Admin",
        "role": "super_admin",  # super_admin role
        "company": company_id,
        "department": "operations",
        "zalo": "0123456789",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    existing_user_super = await db.users.find_one({"username": "admin"})
    if not existing_user_super:
        await db.users.insert_one(user_super)
        print(f"✅ Created user: {user_super['username']} (Password: {password_super}) - Role: {user_super['role']}")
    else:
        print(f"ℹ️  User already exists: {existing_user_super['username']}")
    
    # 3. Create test ships
    ships_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "BROTHER 36",
            "imo": "8743531",
            "ship_type": "DNV GL",  # Changed from "type" to "ship_type" and use class society name
            "flag": "PANAMA",
            "gross_tonnage": 2850,
            "deadweight": 4500,
            "built_year": 1987,
            "company": company_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": str(uuid.uuid4()),
            "name": "PACIFIC STAR",
            "imo": "9234567",
            "ship_type": "ABS",  # American Bureau of Shipping
            "flag": "VIETNAM",
            "gross_tonnage": 5200,
            "deadweight": 8000,
            "built_year": 2005,
            "company": company_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": str(uuid.uuid4()),
            "name": "OCEAN VOYAGER",
            "imo": "9876543",
            "ship_type": "Lloyd's Register",  # Lloyd's Register
            "flag": "MARSHALL ISLANDS",
            "gross_tonnage": 15000,
            "deadweight": 22000,
            "built_year": 2010,
            "company": company_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    ]
    
    for ship_data in ships_data:
        existing_ship = await db.ships.find_one({"imo": ship_data["imo"]})
        if not existing_ship:
            await db.ships.insert_one(ship_data)
            print(f"✅ Created ship: {ship_data['name']} (IMO: {ship_data['imo']})")
        else:
            print(f"ℹ️  Ship already exists: {existing_ship['name']} (IMO: {existing_ship['imo']})")
    
    # Summary
    users_count = await db.users.count_documents({})
    ships_count = await db.ships.count_documents({})
    companies_count = await db.companies.count_documents({})
    
    print("\n📊 Database Summary:")
    print(f"   👥 Users: {users_count}")
    print(f"   🚢 Ships: {ships_count}")
    print(f"   🏢 Companies: {companies_count}")
    print("\n✅ Database seeding completed!")
    print("\n🔑 Login Credentials:")
    print(f"   1. Super Admin:")
    print(f"      Username: admin")
    print(f"      Password: admin123")
    print(f"      Role: super_admin")
    print(f"   2. Admin:")
    print(f"      Username: admin1 (or admin1@amcsc.vn)")
    print(f"      Password: 123456")
    print(f"      Role: admin")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())

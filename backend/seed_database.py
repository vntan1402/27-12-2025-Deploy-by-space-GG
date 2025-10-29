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
    db = client.shipmanagement
    
    print("🌱 Starting database seeding...")
    
    # 1. Create test company
    company_id = str(uuid.uuid4())
    company = {
        "id": company_id,
        "name": "AMCSC",
        "code": "AMCSC",
        "email": "contact@amcsc.vn",
        "phone": "+84 123 456 789",
        "address": "Ho Chi Minh City, Vietnam",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    existing_company = await db.companies.find_one({"code": "AMCSC"})
    if not existing_company:
        await db.companies.insert_one(company)
        print(f"✅ Created company: {company['name']} (ID: {company_id})")
    else:
        company_id = existing_company['id']
        print(f"ℹ️  Company already exists: {existing_company['name']} (ID: {company_id})")
    
    # 2. Create test admin user
    password = "123456"
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "username": "admin1@amcsc.vn",
        "password_hash": password_hash,
        "email": "admin1@amcsc.vn",
        "full_name": "Admin User",
        "role": "ADMIN",
        "company": company_id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    existing_user = await db.users.find_one({"username": "admin1@amcsc.vn"})
    if not existing_user:
        await db.users.insert_one(user)
        print(f"✅ Created user: {user['username']} (Password: {password})")
    else:
        print(f"ℹ️  User already exists: {existing_user['username']}")
    
    # 3. Create test ships
    ships_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "BROTHER 36",
            "imo": "8743531",
            "type": "CARGO",
            "flag": "PANAMA",
            "call_sign": "3EXA2",
            "gross_tonnage": 2850,
            "net_tonnage": 1450,
            "deadweight": 4500,
            "built_year": 1987,
            "company": company_id,
            "status": "ACTIVE",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": str(uuid.uuid4()),
            "name": "PACIFIC STAR",
            "imo": "9234567",
            "type": "TANKER",
            "flag": "VIETNAM",
            "call_sign": "XV1234",
            "gross_tonnage": 5200,
            "net_tonnage": 3100,
            "deadweight": 8000,
            "built_year": 2005,
            "company": company_id,
            "status": "ACTIVE",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": str(uuid.uuid4()),
            "name": "OCEAN VOYAGER",
            "imo": "9876543",
            "type": "CONTAINER",
            "flag": "MARSHALL ISLANDS",
            "call_sign": "V7AB2",
            "gross_tonnage": 15000,
            "net_tonnage": 9000,
            "deadweight": 22000,
            "built_year": 2010,
            "company": company_id,
            "status": "ACTIVE",
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
    print(f"   Username: admin1@amcsc.vn")
    print(f"   Password: 123456")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())

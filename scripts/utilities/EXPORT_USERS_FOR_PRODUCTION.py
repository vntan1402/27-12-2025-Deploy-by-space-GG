#!/usr/bin/env python3
"""
Script export users và companies từ local database để import vào production
"""

import os
import asyncio
import json
from datetime import datetime

os.environ['MONGO_URL'] = 'mongodb://localhost:27017/ship_management'

from mongodb_database import MongoDatabase

async def export_data():
    print("=" * 70)
    print("  EXPORT USERS & COMPANIES TỪ LOCAL DATABASE")
    print("=" * 70)
    print()
    
    mongo_db = MongoDatabase()
    await mongo_db.connect()
    
    # Export Companies
    print("📦 Đang export Companies...")
    companies = await mongo_db.find_all('companies', {})
    companies_list = []
    for company in companies:
        # Remove MongoDB _id field
        if '_id' in company:
            del company['_id']
        companies_list.append(company)
    
    print(f"   ✅ Tìm thấy {len(companies_list)} companies")
    
    # Export Users
    print("👥 Đang export Users...")
    users = await mongo_db.find_all('users', {})
    users_list = []
    for user in users:
        # Remove MongoDB _id field
        if '_id' in user:
            del user['_id']
        users_list.append(user)
    
    print(f"   ✅ Tìm thấy {len(users_list)} users")
    
    # Show user breakdown
    print()
    print("📊 Chi tiết Users:")
    for user in users_list:
        print(f"   - {user.get('username')} ({user.get('role')}) - {user.get('email')}")
    
    print()
    print("📊 Chi tiết Companies:")
    for company in companies_list:
        print(f"   - {company.get('name')} - {company.get('email')}")
    
    # Save to files
    export_data = {
        "export_date": datetime.now().isoformat(),
        "total_companies": len(companies_list),
        "total_users": len(users_list),
        "companies": companies_list,
        "users": users_list
    }
    
    # Save complete export
    with open('/app/production_database_export.json', 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
    
    # Save separate files for easier import
    with open('/app/production_companies_export.json', 'w', encoding='utf-8') as f:
        json.dump(companies_list, f, indent=2, ensure_ascii=False, default=str)
    
    with open('/app/production_users_export.json', 'w', encoding='utf-8') as f:
        json.dump(users_list, f, indent=2, ensure_ascii=False, default=str)
    
    await mongo_db.disconnect()
    
    print()
    print("=" * 70)
    print("✅ EXPORT HOÀN TẤT!")
    print("=" * 70)
    print()
    print("📁 Các file đã tạo:")
    print("   1. /app/production_database_export.json (full export)")
    print("   2. /app/production_companies_export.json (chỉ companies)")
    print("   3. /app/production_users_export.json (chỉ users)")
    print()
    print("=" * 70)
    print("📤 HƯỚNG DẪN IMPORT VÀO PRODUCTION:")
    print("=" * 70)
    print()
    print("Gửi file cho Emergent Support và yêu cầu họ chạy:")
    print()
    print("mongoimport --uri='PRODUCTION_MONGO_URL' \\")
    print("  --collection=companies \\")
    print("  --file=production_companies_export.json \\")
    print("  --jsonArray")
    print()
    print("mongoimport --uri='PRODUCTION_MONGO_URL' \\")
    print("  --collection=users \\")
    print("  --file=production_users_export.json \\")
    print("  --jsonArray")
    print()

if __name__ == "__main__":
    asyncio.run(export_data())

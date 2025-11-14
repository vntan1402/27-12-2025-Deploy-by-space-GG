#!/usr/bin/env python3
"""
Script để tạo admin user và company data để import vào production
Chạy script này trên local, sau đó import JSON vào production database
"""

import json
import bcrypt
import uuid
from datetime import datetime

# Thông tin admin - CẬP NHẬT THEO Ý BẠN
ADMIN_USERNAME = "system_admin"
ADMIN_EMAIL = "admin@nautical-records.com"
ADMIN_PASSWORD = "SecurePass2024!"  # ĐỔI MẬT KHẨU NÀY!
ADMIN_FULL_NAME = "System Administrator"
COMPANY_NAME = "Nautical Records Company"

print("=" * 60)
print("  TẠO DỮ LIỆU ADMIN CHO PRODUCTION")
print("=" * 60)
print()

# Tạo IDs
company_id = str(uuid.uuid4())
user_id = str(uuid.uuid4())

# Hash password
hashed_password = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()

# Tạo company data
company_data = {
    "id": company_id,
    "name": COMPANY_NAME,
    "email": ADMIN_EMAIL,
    "phone": "",
    "address": "",
    "logo_url": "",
    "tax_id": f"AUTO-{company_id[:8]}",
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat()
}

# Tạo user data
user_data = {
    "id": user_id,
    "username": ADMIN_USERNAME,
    "email": ADMIN_EMAIL,
    "full_name": ADMIN_FULL_NAME,
    "password": hashed_password,
    "password_hash": hashed_password,
    "role": "system_admin",
    "department": ["technical", "operations", "safety", "commercial", "crewing"],
    "company": company_id,
    "ship": None,
    "zalo": "",
    "gmail": ADMIN_EMAIL,
    "is_active": True,
    "created_at": datetime.now().isoformat()
}

# Save to files
with open('/app/production_company.json', 'w', encoding='utf-8') as f:
    json.dump(company_data, f, indent=2, ensure_ascii=False)

with open('/app/production_admin.json', 'w', encoding='utf-8') as f:
    json.dump(user_data, f, indent=2, ensure_ascii=False)

print("✅ Đã tạo file dữ liệu:")
print(f"   - /app/production_company.json")
print(f"   - /app/production_admin.json")
print()
print("=" * 60)
print("THÔNG TIN ĐĂNG NHẬP:")
print("=" * 60)
print(f"Username: {ADMIN_USERNAME}")
print(f"Password: {ADMIN_PASSWORD}")
print(f"Email:    {ADMIN_EMAIL}")
print(f"Role:     system_admin")
print(f"Company:  {COMPANY_NAME}")
print()
print("=" * 60)
print("HƯỚNG DẪN IMPORT VÀO PRODUCTION:")
print("=" * 60)
print()
print("1. Gửi 2 file JSON này cho Emergent Support")
print("2. Yêu cầu họ import vào production database:")
print()
print("   MongoDB Commands:")
print(f"   use ship_management")
print(f"   db.companies.insertOne({json.dumps(company_data, indent=4)})")
print(f"   db.users.insertOne({json.dumps(user_data, indent=4)})")
print()
print("⚠️  LƯU Ý: GHI NHỚ PASSWORD!")
print()

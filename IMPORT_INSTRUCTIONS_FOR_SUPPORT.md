# Hướng Dẫn Import Database Vào Production

## 📋 Tổng Quan

Migrate users và companies từ development environment sang production.

- **Domain Production:** https://nautical-records.emergent.cloud/
- **Database:** ship_management
- **Số Users:** 2
- **Số Companies:** 1

---

## 📦 Files Cần Import

1. **production_users_export.json** (1.4 KB)
   - 2 users: `admin1`, `system_admin`
   - Đã có password hash (bcrypt)
   - Role: admin và system_admin

2. **production_companies_export.json** (847 bytes)
   - 1 company: Maritime Technology Development Co., Ltd.

3. **production_database_export.json** (2.5 KB)
   - Full export (bao gồm cả 2 file trên)

---

## 🔧 Cách Import (Cho Emergent Support Team)

### Phương pháp 1: Dùng mongoimport (Khuyến nghị)

```bash
# Import companies
mongoimport --uri="PRODUCTION_MONGO_URL" \
  --db=ship_management \
  --collection=companies \
  --file=production_companies_export.json \
  --jsonArray \
  --drop

# Import users
mongoimport --uri="PRODUCTION_MONGO_URL" \
  --db=ship_management \
  --collection=users \
  --file=production_users_export.json \
  --jsonArray \
  --drop
```

**Lưu ý:** Flag `--drop` sẽ xóa collection cũ trước khi import. Bỏ flag này nếu muốn merge data.

---

### Phương pháp 2: Dùng mongosh

```javascript
// Connect to production
mongosh "PRODUCTION_MONGO_URL"

// Use database
use ship_management

// Drop existing collections (optional)
db.companies.drop()
db.users.drop()

// Read JSON files and insert
// (Paste nội dung từ file JSON vào đây)

// Insert companies
db.companies.insertMany([
  {
    "id": "0a6eaf96-0aaf-4793-89be-65d62cb7953c",
    "name": "Maritime Technology Development Co., Ltd.",
    "email": "amcsc.documents@gmail.com",
    "phone": "+84 123 456 789",
    "address": "123 Marine Street, District 1, Ho Chi Minh City, Vietnam",
    "logo_url": "",
    "tax_id": "0123456789",
    "created_at": "2025-10-29T09:13:29.436000",
    "updated_at": "2025-10-29T09:13:29.436000"
  }
])

// Insert users
db.users.insertMany([
  {
    "id": "7f192759-ec79-485b-ae66-1329ec78cc47",
    "username": "admin1",
    "password_hash": "$2b$12$wdq5F.4T2TqKpf85oS3FpejmrgKTPJBh6D90tyzzqVksz3UqhL8Xi",
    "email": "admin.simple@amcsc.vn",
    "full_name": "Admin User (Demo)",
    "role": "admin",
    "company": "0a6eaf96-0aaf-4793-89be-65d62cb7953c",
    "department": ["operations", "commercial", "technical", "safety"],
    "zalo": "0123456789",
    "created_at": "2025-10-29T09:13:29.436000",
    "updated_at": "2025-11-11T07:35:45.930000",
    "is_active": true,
    "ship": ""
  },
  {
    "id": "cc269020-8634-419a-bd44-eb431ba28119",
    "username": "system_admin",
    "email": "vntan1402@gmail.com",
    "full_name": "System Administrator",
    "role": "system_admin",
    "department": ["technical", "operations", "safety", "commercial", "crewing", "sso", "cso", "supply", "dpa"],
    "company": "",
    "ship": "",
    "zalo": "0989357282",
    "gmail": "admin@yourcompany.com",
    "is_active": true,
    "created_at": "2025-11-10T14:53:04.590000",
    "password_hash": "$2b$12$SaENraGS09E48JNt4C7bDuae7QTwPkgJ8752k7HlxquJgIIbK0RMu",
    "password": "$2b$12$SaENraGS09E48JNt4C7bDuae7QTwPkgJ8752k7HlxquJgIIbK0RMu"
  }
])

// Verify import
db.companies.countDocuments()  // Should return 1
db.users.countDocuments()       // Should return 2
db.users.find({role: "system_admin"}).pretty()
```

---

## ✅ Verify Sau Khi Import

### 1. Kiểm tra API Status
```bash
curl https://nautical-records.emergent.cloud/api/admin/status
```

Kết quả mong đợi:
```json
{
  "admin_exists": true,
  "total_admins": 2,
  "breakdown": {
    "system_admin": 1,
    "super_admin": 0,
    "admin": 1
  },
  "users": [
    {"username": "system_admin", "role": "system_admin"},
    {"username": "admin1", "role": "admin"}
  ]
}
```

### 2. Test Login

**User 1 - System Admin:**
- Username: `system_admin`
- Password: `YourSecure@Pass2024`
- Role: system_admin

**User 2 - Regular Admin:**
- Username: `admin1`
- Password: `123456`
- Role: admin

```bash
# Test login system_admin
curl -X POST "https://nautical-records.emergent.cloud/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"system_admin","password":"YourSecure@Pass2024","remember_me":false}'

# Test login admin1
curl -X POST "https://nautical-records.emergent.cloud/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"123456","remember_me":false}'
```

---

## 📊 Data Summary

### Companies (1 record)
| Field | Value |
|-------|-------|
| ID | 0a6eaf96-0aaf-4793-89be-65d62cb7953c |
| Name | Maritime Technology Development Co., Ltd. |
| Email | amcsc.documents@gmail.com |
| Tax ID | 0123456789 |

### Users (2 records)

**System Admin:**
| Field | Value |
|-------|-------|
| ID | cc269020-8634-419a-bd44-eb431ba28119 |
| Username | system_admin |
| Email | vntan1402@gmail.com |
| Role | system_admin |
| Password | YourSecure@Pass2024 |
| Status | Active ✅ |

**Admin User:**
| Field | Value |
|-------|-------|
| ID | 7f192759-ec79-485b-ae66-1329ec78cc47 |
| Username | admin1 |
| Email | admin.simple@amcsc.vn |
| Role | admin |
| Password | 123456 |
| Company | Maritime Technology Development Co., Ltd. |
| Status | Active ✅ |

---

## ⚠️ Important Notes

1. **Password Hashes:** Đã có sẵn bcrypt hash, không cần re-hash
2. **UUIDs:** Giữ nguyên IDs để maintain relationships
3. **Timestamps:** Đã convert sang ISO format string
4. **Company Relationship:** admin1 thuộc company, system_admin không thuộc company nào
5. **Permissions:** system_admin có full access, admin1 có limited access theo company

---

## 🔒 Security

- Passwords đã được hash bằng bcrypt
- Sau khi import, khuyến nghị users đổi password
- system_admin có thể quản lý toàn bộ hệ thống
- admin1 chỉ quản lý được data trong company của mình

---

## 📞 Contact

Nếu có vấn đề khi import, liên hệ:
- User: [Tên của bạn]
- Email: [Email của bạn]
- Domain: https://nautical-records.emergent.cloud/

---

## ✅ Post-Import Checklist

- [ ] Companies collection có 1 record
- [ ] Users collection có 2 records
- [ ] API /api/admin/status trả về admin_exists: true
- [ ] Login với system_admin thành công
- [ ] Login với admin1 thành công
- [ ] Web UI hoạt động bình thường

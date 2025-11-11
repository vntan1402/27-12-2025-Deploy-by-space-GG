# Fix Production User Company Mismatch

## 🚨 Vấn Đề

Production user `system_admin` có:
- `company`: `8d955d9d-d928-4389-a0f3-eec1757d43cd`

Nhưng company này KHÔNG tồn tại trong database → 500 error khi fetch company data.

---

## 💡 Giải Pháp

### **Option 1: Import Đúng Database** ⭐⭐⭐ (Khuyến nghị cao)

**Vấn đề gốc:** Production đang có user từ một lần tạo trước đó, nhưng không có companies.

**Giải pháp:**
1. Xóa database production hiện tại (clear all data)
2. Import đầy đủ từ local export:
   - `production_users_export.json`
   - `production_companies_export.json`

**Lợi ích:**
- ✅ Đảm bảo data consistency
- ✅ User và Company IDs match
- ✅ Có đầy đủ data để test

**Liên hệ Emergent Support:**
```
Subject: Request Full Database Import - Data Mismatch

Hi Emergent Team,

My production database has a user with invalid company reference.

Issue:
- User exists: system_admin (vntan1402@gmail.com)
- User.company: 8d955d9d-d928-4389-a0f3-eec1757d43cd
- But this company doesn't exist in database
- Causing 500 errors when fetching company data

Request:
1. CLEAR all existing data in production database
2. IMPORT from attached files:
   - production_users_export.json
   - production_companies_export.json

This will ensure user.company matches actual company in database.

Domain: https://nautical-records.emergent.cloud/
Job ID: [your job ID]

Files attached.
```

---

### **Option 2: Update User Company to NULL** (Temporary)

Nếu cần fix nhanh, set user.company = "" (empty) hoặc null.

**Yêu cầu Emergent Support:**
```
Subject: Quick Fix - Update User Company Field

Hi,

Can you help update user company field in production?

Database: ship_management
Collection: users
Query: {"username": "system_admin"}
Update: {"$set": {"company": ""}}

This will allow system_admin to login without company reference.

Domain: https://nautical-records.emergent.cloud/
```

**Sau khi update:**
- System admin có thể login
- Tạo company mới qua UI
- Link user với company mới

---

### **Option 3: Create Company Matching the ID** (Not Recommended)

Tạo company với exact ID `8d955d9d-d928-4389-a0f3-eec1757d43cd`.

**Vấn đề:**
- Phải hardcode UUID
- Không guarantee data integrity
- Không khuyến nghị

---

## 🎯 Khuyến Nghị

**Chọn Option 1** - Import full database:

**Lý do:**
1. ✅ Đảm bảo data consistency
2. ✅ User và Company đều có sẵn và match
3. ✅ Có test data để verify production
4. ✅ Password hash đúng
5. ✅ Tất cả relationships intact

**Steps:**
1. Contact Emergent Support (Discord: https://discord.gg/VzKfwCXC4A)
2. Request CLEAR + IMPORT
3. Provide files:
   - `/app/production_users_export.json`
   - `/app/production_companies_export.json`
   - `/app/IMPORT_INSTRUCTIONS_FOR_SUPPORT.md`
4. Wait 1-2 hours
5. Test login và company access

---

## ✅ Verification After Fix

Sau khi import, test:

```bash
# 1. Admin status
curl https://nautical-records.emergent.cloud/api/admin/status

# Expected: 
# - admin_exists: true
# - username: system_admin OR admin1

# 2. Login
curl -X POST https://nautical-records.emergent.cloud/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"123456"}'

# 3. Get companies (with token)
curl https://nautical-records.emergent.cloud/api/companies \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected:
# - Array with 1 company
# - Company ID: 0a6eaf96-0aaf-4793-89be-65d62cb7953c
```

---

## 📊 Data Comparison

| Field | Production (Current) | Local Export | Match |
|-------|---------------------|--------------|-------|
| User ID | cc269020-8634-419a-bd44-eb431ba28119 | cc269020-... | ✅ |
| Username | system_admin | system_admin | ✅ |
| User.company | **8d955d9d-d928-4389-a0f3-eec1757d43cd** | "" (empty) | ❌ |
| Company ID | N/A (doesn't exist) | 0a6eaf96-0aaf-4793-89be-65d62cb7953c | ❌ |

**Problem:** User.company references non-existent company!

---

## 🔧 Root Cause

**Scenario:**
1. Production was deployed once → auto-created system_admin
2. System admin was assigned to a company (8d955d9d-...)
3. Database was cleared or company was deleted
4. Now user exists but company doesn't
5. AuthContext tries to fetch company → 500 error

**Solution:**
- Import BOTH users AND companies together
- Ensure referential integrity

---

## 📞 Support Template

Use this when contacting Emergent Support:

```
Subject: Production Database Import - User/Company Mismatch

Hi Emergent Support,

Production Issue:
- Domain: https://nautical-records.emergent.cloud/
- Problem: User exists but references non-existent company
- Error: 500 when fetching company data
- Impact: Application unusable

Details:
- User: system_admin (ID: cc269020-8634-419a-bd44-eb431ba28119)
- User.company: 8d955d9d-d928-4389-a0f3-eec1757d43cd (doesn't exist)
- Frontend errors: "Failed to fetch company expiry"

Request:
1. CLEAR production database (ship_management)
2. IMPORT from attached files to ensure data consistency

Files attached:
- production_users_export.json (2 users)
- production_companies_export.json (1 company)
- IMPORT_INSTRUCTIONS_FOR_SUPPORT.md (guide)

After import:
- Users will have correct company references
- All IDs will match
- Application will work correctly

Job ID: [from chat 'i' button]

Thank you!
```

---

## 🎉 Expected Result After Fix

After successful import:

✅ **User:**
- username: admin1
- company: 0a6eaf96-0aaf-4793-89be-65d62cb7953c
- Can login with password: 123456

✅ **Company:**
- id: 0a6eaf96-0aaf-4793-89be-65d62cb7953c
- name: Maritime Technology Development Co., Ltd.
- Exists in database

✅ **No More Errors:**
- AuthContext fetches company successfully
- HomePage loads company data
- No 500 errors in console

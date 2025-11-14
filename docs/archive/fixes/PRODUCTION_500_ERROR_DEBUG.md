# Production 500 Error - Debug Guide

## 🔥 Vấn Đề
Production tại `https://nautical-records.emergent.cloud/` gặp lỗi 500 khi fetch data:
- `/api/companies` - Failed repeatedly
- `/api/verify-token` - Failed
- Settings page không load được

## 🎯 Nguyên Nhân Có Thể

### 1. **Database Trống (Khả năng cao nhất)** ⭐
Production database chưa có data vì:
- Admin chưa được tạo (do MongoDB permission issue)
- Companies collection trống
- Users collection trống hoặc thiếu data

**Triệu chứng:**
```
GET /api/companies → 500 error
Message: "No companies yet"
```

### 2. **MongoDB Permission Issues**
Backend không có quyền query MongoDB:
- Thiếu readWrite permission
- Connection string sai
- Authentication failed

### 3. **Backend Code Error**
Code bị lỗi khi query empty collection:
```python
# Có thể code không handle empty result
companies = await mongo_db.find_all('companies', {})
# Nếu companies = [] và code không check, có thể throw error
```

### 4. **Environment Variables Thiếu**
Thiếu các env variables quan trọng:
- `MONGO_URL`
- `JWT_SECRET`
- `INIT_ADMIN_*` variables

---

## 🔍 Các Bước Debug

### **Bước 1: Kiểm Tra Backend Logs** ⭐ (Quan trọng nhất)

**Làm sao:**
1. Trong Emergent Platform
2. Mở Deployment logs panel
3. Tìm dòng lỗi gần đây

**Tìm gì:**
```
ERROR: ...
Exception: ...
MongoDB error: ...
Permission denied: ...
```

### **Bước 2: Test API Endpoints Trực Tiếp**

**Companies endpoint:**
```bash
curl -v https://nautical-records.emergent.cloud/api/companies
```

**Expected (nếu OK):**
```json
[]  // Empty array nếu chưa có companies
```

**Actual (hiện tại):**
```json
{
  "detail": "Internal Server Error"
}
```

**Admin status:**
```bash
curl https://nautical-records.emergent.cloud/api/admin/status
```

### **Bước 3: Kiểm Tra Environment Variables**

Trong Deployments panel, verify:
```
✅ MONGO_URL - Có và đúng format
✅ JWT_SECRET - Có
✅ INIT_ADMIN_USERNAME - Có
✅ INIT_ADMIN_PASSWORD - Có
✅ INIT_ADMIN_EMAIL - Có
```

---

## 💡 Giải Pháp Theo Từng Trường Hợp

### **Case 1: Database Trống** ⭐⭐⭐

**Giải pháp A: Import Data từ Local**
1. Sử dụng files đã export:
   - `/app/production_users_export.json`
   - `/app/production_companies_export.json`
2. Gửi cho Emergent Support để import
3. Contact Discord: https://discord.gg/VzKfwCXC4A

**Giải pháp B: Deploy với Fixed Code**
1. Đảm bảo code đã fix (`mongo_db.create()` thay vì `insert_one()`)
2. Set đầy đủ env variables
3. Re-deploy
4. Admin sẽ tự động tạo

**Giải pháp C: Tạo Test Company Qua API** (Nếu admin đã tạo được)
```bash
# Login first
TOKEN=$(curl -X POST https://nautical-records.emergent.cloud/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"system_admin","password":"YourPassword"}' \
  | jq -r '.access_token')

# Create test company
curl -X POST https://nautical-records.emergent.cloud/api/companies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Company",
    "email": "test@company.com",
    "tax_id": "TEST001"
  }'
```

### **Case 2: Backend Code Error**

**Fix Backend Error Handling:**

Check file: `/app/backend/server.py`

Find companies endpoint:
```python
@api_router.get("/companies")
async def get_companies(...):
    try:
        companies = await mongo_db.find_all('companies', {})
        return companies if companies else []  # ✅ Ensure return empty array
    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        raise HTTPException(500, detail=str(e))  # Return detailed error
```

**Action:**
1. Xem code hiện tại có handle empty result không
2. Add proper error handling
3. Re-deploy

### **Case 3: MongoDB Permission**

**Đã fix trong code (dùng `mongo_db.create()`)** ✅

Nếu vẫn gặp permission error:
1. Contact Emergent Support
2. Yêu cầu grant `readWrite` permission cho MongoDB user
3. Provide Job ID và error logs

### **Case 4: Environment Variables**

**Fix:**
1. Vào Deployments panel
2. Add thiếu variables
3. Click "Re-Deploy"

---

## 🚨 Quick Fix Steps

### **Immediate Action (5 phút):**

1. **Check admin status:**
   ```bash
   curl https://nautical-records.emergent.cloud/api/admin/status
   ```
   
   - Nếu `admin_exists: false` → Database trống
   - Nếu `admin_exists: true` → Backend code issue

2. **Check backend logs** trong Emergent platform
   - Tìm exact error message
   - Screenshot và share với support

3. **Test simple endpoint:**
   ```bash
   curl https://nautical-records.emergent.cloud/api/health
   ```
   
   - Nếu work → Backend running, database issue
   - Nếu fail → Backend không chạy

### **Short Term Fix (30 phút):**

**Option A: Import Database** (Khuyến nghị)
1. Download export files
2. Contact Emergent Support
3. Request import vào production
4. Wait 1-2 hours

**Option B: Re-Deploy với env variables**
1. Set đầy đủ `INIT_ADMIN_*` variables
2. Deploy
3. Check logs cho admin creation
4. Verify `/api/admin/status`

### **Long Term Fix:**

1. ✅ Code đã fix (dùng wrapper methods)
2. ✅ Export data ready
3. ⏳ Waiting for production database import
4. ⏳ Verify all endpoints work after import

---

## 📞 Contact Support Template

**Subject:** 500 Error on Production - Empty Database

```
Hi Emergent Support,

My production app is experiencing 500 errors:
- Domain: https://nautical-records.emergent.cloud/
- Error: GET /api/companies returns 500
- Issue: Database appears to be empty (no admin, no companies)

I have:
- ✅ Fixed code (using mongo_db.create())
- ✅ Prepared data export files
- ✅ Set environment variables

Actions needed:
1. Import database from attached files:
   - production_users_export.json
   - production_companies_export.json

OR

2. Grant MongoDB permissions so admin can auto-create on startup

Job ID: [your job ID from chat 'i' button]

Files attached.

Thanks!
```

---

## ✅ Verification After Fix

Test these endpoints:

```bash
# 1. Admin status
curl https://nautical-records.emergent.cloud/api/admin/status

# 2. Companies list
curl https://nautical-records.emergent.cloud/api/companies

# 3. Login
curl -X POST https://nautical-records.emergent.cloud/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"system_admin","password":"YourPassword"}'

# 4. Health check
curl https://nautical-records.emergent.cloud/api/health
```

**Expected Results:**
- ✅ Admin status: `admin_exists: true`
- ✅ Companies: returns array (might be empty but not error)
- ✅ Login: returns token
- ✅ Health: returns OK

---

## 📊 Summary

**Most Likely Cause:** Production database is empty (no admin, no companies)

**Quick Fix:** Import database via Emergent Support

**Permanent Fix:** 
1. Code already fixed ✅
2. Auto-admin creation will work after deploy ✅
3. MongoDB permissions resolved via wrapper methods ✅

**Next Steps:**
1. Check deployment logs for exact error
2. Contact Emergent Support with export files
3. OR re-deploy with proper env variables

---

## 🎯 Root Cause Analysis

**Why Preview works but Production doesn't?**

| Environment | Database | Admin | Companies |
|-------------|----------|-------|-----------|
| **Preview (Local)** | ✅ Has data | ✅ system_admin exists | ✅ 1 company |
| **Production** | ❌ Empty | ❌ No admin | ❌ No companies |

**Reason:**
- Preview: You manually created admin and company
- Production: Fresh deploy, no data imported yet
- Solution: Import data OR re-deploy with auto-admin

---

**⚡ URGENT:** Contact Emergent Support NOW với export files!

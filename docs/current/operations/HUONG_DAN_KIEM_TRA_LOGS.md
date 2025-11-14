# 📝 HƯỚNG DẪN KIỂM TRA LOGS

## 📋 MỤC LỤC
1. [Logs trong Development](#logs-trong-development)
2. [Logs trong Production](#logs-trong-production)
3. [Các Log Messages Quan Trọng](#các-log-messages-quan-trọng)
4. [Troubleshooting với Logs](#troubleshooting-với-logs)
5. [Alternative Methods](#alternative-methods)

---

## 🖥️ LOGS TRONG DEVELOPMENT

### ✅ Có Full Access

**Location của logs:**
```bash
Backend Logs:
- /var/log/supervisor/backend.err.log  (Error & Info logs)
- /var/log/supervisor/backend.out.log  (Standard output)

Frontend Logs:
- /var/log/supervisor/frontend.err.log
- /var/log/supervisor/frontend.out.log
```

---

### 📖 COMMANDS ĐỂ XEM LOGS:

#### 1. Xem 50 dòng cuối cùng:
```bash
tail -n 50 /var/log/supervisor/backend.err.log
```

#### 2. Xem logs real-time (follow):
```bash
tail -f /var/log/supervisor/backend.err.log
```

#### 3. Search cho admin-related logs:
```bash
grep -i "admin" /var/log/supervisor/backend.err.log | tail -20
```

#### 4. Search cho startup logs:
```bash
grep -i "startup\|Admin.*created\|Admin.*exist" /var/log/supervisor/backend.err.log | tail -30
```

#### 5. Search với context (5 lines before & after):
```bash
grep -C 5 "ADMIN USER CREATED" /var/log/supervisor/backend.err.log
```

#### 6. Xem tất cả errors:
```bash
grep "ERROR" /var/log/supervisor/backend.err.log | tail -50
```

#### 7. Xem logs từ 1 giờ trước:
```bash
find /var/log/supervisor/ -name "*.log" -mmin -60 -exec tail -n 100 {} \;
```

---

### 🔍 LOG MESSAGES QUAN TRỌNG:

#### ✅ THÀNH CÔNG - Admin Được Tạo:

```
INFO:init_admin_startup:🔧 No admin users found. Creating initial admin from environment variables...
INFO:init_admin_startup:✅ Company created: Your Company Ltd
INFO:init_admin_startup:============================================================
INFO:init_admin_startup:✅ INITIAL ADMIN USER CREATED SUCCESSFULLY!
INFO:init_admin_startup:============================================================
INFO:init_admin_startup:Username:     system_admin
INFO:init_admin_startup:Email:        admin@yourcompany.com
INFO:init_admin_startup:Role:         SYSTEM_ADMIN
INFO:init_admin_startup:Company:      Your Company Ltd
INFO:init_admin_startup:============================================================
INFO:init_admin_startup:⚠️  IMPORTANT: Change the password after first login!
INFO:init_admin_startup:============================================================
```

**Ý nghĩa:**
- ✅ Admin user đã được tạo thành công
- ✅ Company đã được tạo
- ✅ Có thể login với credentials từ .env

---

#### ✅ SKIP - Admin Đã Tồn Tại:

```
INFO:     Waiting for application startup.
INFO:init_admin_startup:✅ Admin users already exist (1 system_admin, 2 super_admin)
INFO:     Application startup complete.
```

**Ý nghĩa:**
- ✅ Script chạy OK
- ✅ Detected admin đã có
- ✅ Skip create (correct behavior)
- ✅ App startup thành công

---

#### ❌ LỖI - Password Không Set:

```
INFO:init_admin_startup:🔧 No admin users found. Creating initial admin...
ERROR:init_admin_startup:❌ INIT_ADMIN_PASSWORD not set in environment variables!
ERROR:init_admin_startup:   Please set INIT_ADMIN_PASSWORD in .env file
```

**Action:**
1. Check file `/app/backend/.env`
2. Verify có dòng: `INIT_ADMIN_PASSWORD=...`
3. Restart backend: `sudo supervisorctl restart backend`

---

#### ❌ LỖI - MongoDB Connection:

```
ERROR:init_admin_startup:❌ Error initializing admin: Cannot use MongoClient after close
```

**Action:**
1. Script issue với MongoDB connection
2. Verify init_admin_startup.py không có `mongo_db.disconnect()`
3. Restart backend

---

#### ❌ LỖI - Duplicate Key:

```
ERROR:init_admin_startup:❌ Error initializing admin: E11000 duplicate key error collection: ship_management.companies index: tax_id_1
```

**Action:**
1. Company với tax_id đó đã tồn tại
2. Script sẽ skip và không crash
3. Check database manually nếu cần

---

### 📊 XEM LOGS CỤ THỂ:

#### Example 1: Check Admin Creation

```bash
# Command:
grep -A 10 "No admin users found" /var/log/supervisor/backend.err.log | tail -20

# Expected Output:
INFO:init_admin_startup:🔧 No admin users found. Creating initial admin...
INFO:init_admin_startup:✅ Company created: Your Company Ltd
INFO:init_admin_startup:============================================================
INFO:init_admin_startup:✅ INITIAL ADMIN USER CREATED SUCCESSFULLY!
...
```

---

#### Example 2: Check Login Attempts

```bash
# Command:
grep "Login attempt" /var/log/supervisor/backend.err.log | tail -10

# Output shows:
INFO:server:🔐 Login attempt for username: system_admin
INFO:server:✅ User found: system_admin
INFO:server:🔑 Password verification result: True
```

---

#### Example 3: Check Startup Sequence

```bash
# Command:
grep -E "startup|Admin.*exist|Admin.*created" /var/log/supervisor/backend.err.log | tail -15

# Shows full startup flow:
INFO:     Waiting for application startup.
INFO:init_admin_startup:✅ Admin users already exist (1 system_admin, 0 super_admin)
INFO:     Application startup complete.
```

---

## 🌐 LOGS TRONG PRODUCTION

### ⚠️ GIỚI HẠN:

**❌ KHÔNG CÓ:**
- Direct terminal access
- SSH access
- Log file access
- Real-time monitoring

**✅ CÓ:**
- Deployment logs (during deploy)
- Error reporting (nếu app crash)
- Platform monitoring dashboard (limited)

---

### 📱 CÁCH KIỂM TRA TRONG PRODUCTION:

#### Method 1: Platform Dashboard (Nếu có)

```
1. Login vào Emergent platform
2. Go to your deployed app
3. Click "Logs" or "Monitoring" tab
4. View deployment logs
5. Look for startup messages
```

**Tìm:**
- "Application starting"
- "Admin users already exist" hoặc "ADMIN USER CREATED"
- "Application startup complete"

---

#### Method 2: Deployment Logs

**Khi deploy, platform sẽ show logs:**

```
Deploying...
Building image...
Starting containers...
⏳ Waiting for application startup
✅ Application started successfully
🚀 Deployment complete

Check for these messages in the build logs:
- "Admin users already exist" → Good, admin exists
- "INITIAL ADMIN USER CREATED" → Good, admin just created
- No error messages → Good to go
```

---

#### Method 3: Test Login (BEST METHOD!)

**Cách TỐT NHẤT để verify admin trong production:**

```
1. Open production URL in browser
2. Try login với credentials từ .env
3. Nếu login thành công → Admin được tạo thành công! ✅
4. Nếu login thất bại → Check alternatives below
```

**Login Test:**
```
URL: https://your-app.emergentagent.com
Username: system_admin (hoặc từ .env)
Password: YourSecure@Pass2024 (hoặc từ .env)

✅ Success → Admin OK!
❌ Failed → Need troubleshooting
```

---

#### Method 4: API Health Check

**Nếu login UI không work, test API trực tiếp:**

```bash
curl -X POST https://your-app.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "system_admin",
    "password": "YourSecure@Pass2024"
  }'

# Expected:
✅ {"access_token":"eyJ...","token_type":"bearer"}

# If failed:
❌ {"detail":"Invalid credentials"} → Wrong password
❌ {"detail":"User not found"} → Admin not created
```

---

## 🔧 TROUBLESHOOTING VỚI LOGS:

### Problem 1: "Cannot login after deployment"

**Steps:**
```
1. Check deployment logs for:
   - "ADMIN USER CREATED" → Good
   - "Admin users already exist" → Good
   - No errors → Good

2. Verify credentials match .env:
   - Username correct?
   - Password correct? (case-sensitive!)

3. Test API directly (curl command above)

4. Check if app is actually running:
   - Production URL accessible?
   - Can you see login page?
```

---

### Problem 2: "Admin không được tạo"

**Check logs for:**

**Scenario A: Password not set**
```
ERROR: INIT_ADMIN_PASSWORD not set
→ Fix: Add INIT_ADMIN_PASSWORD to .env and redeploy
```

**Scenario B: MongoDB connection error**
```
ERROR: Cannot connect to MongoDB
→ Fix: Check MONGO_URL in production environment
```

**Scenario C: Script không chạy**
```
No logs from init_admin_startup at all
→ Fix: Verify startup event in server.py
→ Redeploy
```

---

### Problem 3: "Multiple admins created"

**Check logs:**
```
grep "ADMIN USER CREATED" /var/log/supervisor/backend.err.log | wc -l

If > 1:
→ Multiple creates happened
→ Delete duplicates via UI: System Settings → User Management
```

---

## 🎯 ALTERNATIVE VERIFICATION METHODS:

### Method 1: Database Query (Development Only)

```bash
cd /app/backend && export MONGO_URL='...' && python3 -c "
import asyncio
from mongodb_database import mongo_db

async def check():
    await mongo_db.connect()
    users = await mongo_db.find_all('users', {'role': 'system_admin'})
    print(f'System admins: {len(users)}')
    for u in users:
        print(f'  - {u.get(\"username\")} ({u.get(\"email\")})')
    await mongo_db.disconnect()

asyncio.run(check())
"
```

---

### Method 2: UI Verification (Production & Development)

```
1. Login successfully ✅
2. Go to: System Settings → User Management
3. Look for your admin user
4. Check role = SYSTEM_ADMIN
5. Verify can add all roles (dropdown test)
```

---

### Method 3: API Test (Production & Development)

```bash
# Test login
curl -X POST <URL>/api/auth/login \
  -d '{"username":"system_admin","password":"..."}'

# Test get users (need token)
curl -X GET <URL>/api/users \
  -H "Authorization: Bearer <token>"
```

---

## 📋 CHECKLIST: VERIFY ADMIN TRONG PRODUCTION

```
□ 1. Deploy completed successfully
□ 2. App is accessible at production URL
□ 3. Login page loads
□ 4. Can login with credentials from .env
   □ Username works
   □ Password works (case-sensitive!)
□ 5. Homepage loads after login
□ 6. System Settings accessible
□ 7. User Management accessible
□ 8. Can see admin user in list
□ 9. Can create new users (test + Add User)
□ 10. Can select all roles in dropdown
```

**If ALL ✅ → Admin setup SUCCESSFUL!**

---

## 💡 BEST PRACTICES:

### 1. Sau Mỗi Deploy:
```
✅ Test login ngay lập tức
✅ Verify admin exists
✅ Backup credentials an toàn
✅ Test creating a test user
```

### 2. Monitoring:
```
✅ Setup notification nếu app down
✅ Regular login tests
✅ Check error rates
✅ Monitor user creation
```

### 3. Logging Strategy:
```
✅ Development: Use tail -f for real-time
✅ Production: Test via login
✅ Keep credentials secure
✅ Document any issues
```

---

## 🆘 QUICK REFERENCE:

### Development Logs:
```bash
# Backend errors
tail -f /var/log/supervisor/backend.err.log

# Search admin
grep -i admin /var/log/supervisor/backend.err.log | tail -20

# Search startup
grep -i startup /var/log/supervisor/backend.err.log | tail -20
```

### Production Verification:
```bash
# Test login
curl -X POST https://your-app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"system_admin","password":"YourPass"}'

# Expected: {"access_token":"eyJ..."}
```

### Emergency:
```bash
# Development: Restart backend
sudo supervisorctl restart backend

# Production: Redeploy or contact support
```

---

## 📞 SUPPORT:

**Nếu không thể verify logs hoặc admin:**

1. **Check documentation:** All guides in /app/*.md files
2. **Contact support:**
   - Discord: https://discord.gg/VzKfwCXC4A
   - Email: support@emergent.sh
3. **Provide info:**
   - Screenshot of error
   - Deployment logs (if available)
   - Steps you tried
   - What you see vs what you expect

---

**TÓM TẮT:**
- Development: Full log access via terminal
- Production: Test via login (best method)
- Alternative: API tests, UI verification
- Emergency: Redeploy or support

---

**Last Updated:** 2025-11-10  
**Status:** ✅ Complete Guide

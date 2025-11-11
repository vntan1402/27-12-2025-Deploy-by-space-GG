# Environment Variables Guide - System Admin Setup

## 🎯 Tổng Quan

Sau khi cập nhật System Admin để không cần thuộc company, các environment variables đã được đơn giản hóa.

---

## ✅ Required Environment Variables

### **Cho System Admin Auto-Creation:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INIT_ADMIN_USERNAME` | ✅ Optional | `system_admin` | Username cho system admin |
| `INIT_ADMIN_PASSWORD` | ⚠️ **REQUIRED** | None | Password cho system admin |
| `INIT_ADMIN_EMAIL` | ✅ Optional | `admin@company.com` | Email cho system admin |
| `INIT_ADMIN_FULL_NAME` | ✅ Optional | `System Administrator` | Tên đầy đủ |

### **Không Còn Cần:**

| Variable | Status | Reason |
|----------|--------|--------|
| ~~`INIT_COMPANY_NAME`~~ | ❌ **KHÔNG CẦN** | System Admin không thuộc company nào |

---

## 📋 Environment Variables Configuration

### **Development (.env file):**

```bash
# Database
MONGO_URL=mongodb://localhost:27017/ship_management

# JWT Secret
JWT_SECRET=your-secret-key-change-in-production

# Admin Initialization (Auto-create admin on first startup)
INIT_ADMIN_USERNAME=system_admin
INIT_ADMIN_EMAIL=admin@yourcompany.com
INIT_ADMIN_PASSWORD=YourSecure@Pass2024
INIT_ADMIN_FULL_NAME=System Administrator

# Note: INIT_COMPANY_NAME is no longer required
# System Admin manages ALL companies without belonging to any specific one

# Admin API Security (optional)
ADMIN_CREATION_SECRET=secure-admin-creation-key-2024-change-me
```

### **Production (Emergent Deployments):**

**Minimum Required:**
```
INIT_ADMIN_PASSWORD=YourSecureProductionPassword123!
```

**Recommended:**
```
INIT_ADMIN_USERNAME=system_admin
INIT_ADMIN_PASSWORD=YourSecureProductionPassword123!
INIT_ADMIN_EMAIL=admin@nautical-records.com
INIT_ADMIN_FULL_NAME=System Administrator
```

---

## 🔧 Migration Guide

### **Nếu Bạn Đã Set INIT_COMPANY_NAME:**

**Option 1: Remove (Khuyến nghị)**
```bash
# ❌ Old
INIT_COMPANY_NAME=Your Company Ltd

# ✅ New - Just remove it
# INIT_COMPANY_NAME is not used anymore
```

**Option 2: Comment Out**
```bash
# INIT_COMPANY_NAME=Your Company Ltd  # Not needed - System Admin manages all companies
```

**Option 3: Leave as is**
- Variable sẽ được ignore
- Không ảnh hưởng gì
- Nhưng nên remove cho clean

---

## 🎯 How It Works Now

### **System Admin Creation Logic:**

```
1. Check if admin users exist
   ├─ Yes → Skip creation
   └─ No → Continue

2. Read environment variables
   ├─ INIT_ADMIN_USERNAME (default: system_admin)
   ├─ INIT_ADMIN_PASSWORD (REQUIRED)
   ├─ INIT_ADMIN_EMAIL (default: admin@company.com)
   └─ INIT_ADMIN_FULL_NAME (default: System Administrator)

3. Create System Admin
   ├─ username: from env
   ├─ password: hash from env
   ├─ email: from env
   ├─ role: system_admin
   └─ company: "" (empty - manages ALL companies)

4. No company creation
   └─ System Admin doesn't need a company
```

---

## 📊 Comparison: Old vs New

### **Old Setup (Before):**

```bash
# Required 5 variables
INIT_ADMIN_USERNAME=system_admin
INIT_ADMIN_PASSWORD=password
INIT_ADMIN_EMAIL=admin@company.com
INIT_ADMIN_FULL_NAME=Admin User
INIT_COMPANY_NAME=My Company Ltd  # ← Used to create company

# Result:
# - Created company "My Company Ltd"
# - Created system_admin assigned to that company
# - system_admin could only see that company
```

### **New Setup (Now):**

```bash
# Required 1 variable (others have defaults)
INIT_ADMIN_PASSWORD=password

# Optional (with good defaults)
INIT_ADMIN_USERNAME=system_admin
INIT_ADMIN_EMAIL=admin@company.com
INIT_ADMIN_FULL_NAME=Admin User
# INIT_COMPANY_NAME - NOT NEEDED

# Result:
# - NO company created
# - Created system_admin WITHOUT company
# - system_admin can see ALL companies
# - Companies can be created later via UI
```

---

## 🆕 Benefits of New Approach

### **1. Simpler Setup**
- ✅ Fewer required variables
- ✅ Clear purpose for each variable
- ✅ Better defaults

### **2. Flexible**
- ✅ System Admin manages all companies
- ✅ No initial company constraint
- ✅ Add companies later via UI

### **3. Production Ready**
- ✅ Minimal config needed
- ✅ One required variable (password)
- ✅ Secure by default

### **4. Clear Separation**
- ✅ System Admin = system-wide management
- ✅ Admin/Super Admin = company-specific
- ✅ No confusion

---

## 🔐 Security Best Practices

### **INIT_ADMIN_PASSWORD:**

**❌ Bad:**
```bash
INIT_ADMIN_PASSWORD=123456
INIT_ADMIN_PASSWORD=admin
INIT_ADMIN_PASSWORD=password
```

**✅ Good:**
```bash
INIT_ADMIN_PASSWORD=MySecure@Password2024!
INIT_ADMIN_PASSWORD=Nautical#Records$2024
INIT_ADMIN_PASSWORD=ShipMgmt!Secure#2024
```

**Requirements:**
- ✅ At least 8 characters
- ✅ Contains uppercase and lowercase
- ✅ Contains numbers
- ✅ Contains special characters
- ✅ Not a common password

---

## 📝 Deployment Checklist

### **Local Development:**
- [ ] Set `INIT_ADMIN_PASSWORD` in `.env`
- [ ] Remove or comment out `INIT_COMPANY_NAME`
- [ ] Start backend
- [ ] Verify system_admin created
- [ ] Login with system_admin
- [ ] Check no company assigned

### **Production Deployment:**
- [ ] Set `INIT_ADMIN_PASSWORD` in Deployments panel
- [ ] DO NOT set `INIT_COMPANY_NAME`
- [ ] Set optional variables (username, email, full name)
- [ ] Deploy
- [ ] Check deployment logs for admin creation
- [ ] Test login
- [ ] Verify system_admin has no company
- [ ] Create companies via UI

---

## 🆘 Troubleshooting

### **Q: I set INIT_COMPANY_NAME but it's not creating a company**
**A:** This is expected! System Admin no longer creates a company. Use the UI to create companies after login.

### **Q: Can I still use INIT_COMPANY_NAME?**
**A:** Yes, but it will be ignored. Better to remove it for clarity.

### **Q: How do I create the first company?**
**A:** 
1. Login as system_admin
2. Go to System Settings → Company Management
3. Click "Add Company"
4. Fill in details
5. Save

### **Q: What if I want system_admin to have a company?**
**A:** Not recommended, but you can:
1. Create a company via UI
2. Edit system_admin user
3. Assign company
4. But this defeats the purpose of system_admin role

### **Q: My production still shows old setup**
**A:** 
1. Check Deployments panel in Emergent
2. Remove `INIT_COMPANY_NAME` variable
3. Re-deploy
4. Or just leave it - will be ignored

---

## ✅ Verification

After setup, verify:

```bash
# 1. Check admin created
curl http://localhost:8001/api/admin/status

# Expected:
{
  "admin_exists": true,
  "total_admins": 1,
  "breakdown": {
    "system_admin": 1
  },
  "users": [{
    "username": "system_admin",
    "role": "system_admin",
    "company": ""  // ← Should be empty!
  }]
}

# 2. Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"system_admin","password":"YourPassword"}'

# 3. Check user details - company should be empty or null
```

---

## 📞 Need Help?

**If admin not creating:**
1. Check `INIT_ADMIN_PASSWORD` is set
2. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
3. Look for "Creating initial admin" message
4. Check for errors

**Contact Support:**
- Discord: https://discord.gg/VzKfwCXC4A
- Email: support@emergent.sh

---

## 🎉 Summary

**Old Way:**
- 5 required variables
- Created company automatically
- System admin tied to company

**New Way:**
- 1 required variable (INIT_ADMIN_PASSWORD)
- No company creation
- System admin manages ALL companies
- Simpler, more flexible, production-ready!

**Action Required:**
- ✅ Keep: INIT_ADMIN_PASSWORD (required)
- ✅ Optional: INIT_ADMIN_USERNAME, INIT_ADMIN_EMAIL, INIT_ADMIN_FULL_NAME
- ❌ Remove: INIT_COMPANY_NAME (not used)

# Admin Creation Scripts

Scripts to create admin users for the Ship Management System.

## Overview

The system provides 3 ways to create admin accounts:

1. **Auto-initialization** (Recommended for deployment)
2. **Quick Create Script** (Non-interactive)
3. **Interactive Create Script** (Full control)

---

## 1. Auto-initialization (Automatic)

### How it works:
- Runs automatically when the backend starts
- Checks if any admin exists
- If no admin found → creates one from `.env` variables
- **Zero manual intervention needed**

### Setup:

Edit `/app/backend/.env`:

```bash
# Admin Initialization (for auto-creation on first startup)
INIT_ADMIN_USERNAME=system_admin
INIT_ADMIN_EMAIL=admin@yourcompany.com
INIT_ADMIN_PASSWORD=YourSecure@Pass2024
INIT_ADMIN_FULL_NAME=System Administrator
```

### Usage:

```bash
# Just start the backend
# Admin will be created automatically if not exists

cd /app/backend
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Logs:

Check logs for:
```
✅ Admin user already exists: system_admin
# OR
✅ INITIAL SYSTEM ADMIN CREATED SUCCESSFULLY!
```

---

## 2. Quick Create Script (Non-interactive)

For quickly creating an admin without prompts.

### Usage:

1. **Edit values in the script:**

```bash
nano /app/backend/scripts/quick_create_admin.py

# Edit these values:
ADMIN_USERNAME = "production_admin"
ADMIN_EMAIL = "admin@production.com"
ADMIN_FULL_NAME = "Production Administrator"
ADMIN_PASSWORD = "Admin@2024"  # ⚠️ CHANGE THIS!
COMPANY_NAME = None  # Or "Your Company Name"
```

2. **Run:**

```bash
cd /app/backend
python3 scripts/quick_create_admin.py
```

3. **Output:**

```
==========================================================
⚡ QUICK ADMIN CREATOR
==========================================================
✅ Company created: Your Company
==========================================================
✅ ADMIN USER CREATED!
==========================================================
Username:     production_admin
Email:        admin@production.com
Password:     Admin@2024
Role:         SYSTEM_ADMIN
==========================================================
🚀 Ready to login!
⚠️  IMPORTANT: Change the password after first login!
==========================================================
```

---

## 3. Interactive Create Script

For full control with interactive prompts.

### Usage:

```bash
cd /app/backend
python3 scripts/create_first_admin.py
```

### Prompts:

```
🔐 CREATE FIRST ADMIN USER
==========================================================

📝 Enter Admin Information:
------------------------------------------------------------
Username (e.g., admin): my_admin
Email (e.g., admin@company.com): admin@mycompany.com
Full Name (e.g., System Administrator): John Doe
Password (will be hidden): ********
Confirm Password: ********

🏢 Company Setup:
------------------------------------------------------------
Create a new company? (yes/no): yes
Company Name: My Shipping Company
Company Email: info@mycompany.com
Company Phone (optional): +84123456789

👤 Creating Admin User...
------------------------------------------------------------
✅ Company 'My Shipping Company' created!

==========================================================
✅ ADMIN USER CREATED SUCCESSFULLY!
==========================================================
Username:     my_admin
Email:        admin@mycompany.com
Full Name:    John Doe
Role:         ADMIN
Company:      My Shipping Company
==========================================================
🚀 You can now login with these credentials!
⚠️  IMPORTANT: Change the password after first login!
==========================================================
```

---

## Role Types

### System Admin vs Company Admin

| Feature | System Admin | Company Admin |
|---------|--------------|---------------|
| **Company** | None (manages all) | Assigned to 1 company |
| **Access** | All companies | Own company only |
| **Created by** | Auto-init or scripts | System Admin creates |
| **Use case** | Platform administrator | Company manager |

### Auto-creation behavior:

```python
# If COMPANY_NAME is set → creates "admin" role
# If COMPANY_NAME is empty/None → creates "system_admin" role
```

---

## Environment Variables

```bash
# .env file

# Auto-initialization (used by startup event)
INIT_ADMIN_USERNAME=system_admin
INIT_ADMIN_EMAIL=admin@yourcompany.com
INIT_ADMIN_PASSWORD=YourSecure@Pass2024
INIT_ADMIN_FULL_NAME=System Administrator

# NOT needed for auto-init
# ADMIN_CREATION_SECRET=secure-admin-creation-key-2024-change-me
```

---

## Troubleshooting

### 1. "Username already exists"

**Solution:** Either:
- Use different username
- Delete existing user from MongoDB
- Skip creation (already have admin)

### 2. "INIT_ADMIN_PASSWORD not set"

**Solution:** Add to `.env`:
```bash
INIT_ADMIN_PASSWORD=YourSecurePassword123
```

### 3. Script import errors

**Solution:** Run from backend directory:
```bash
cd /app/backend
python3 scripts/quick_create_admin.py
```

### 4. MongoDB connection failed

**Solution:** Check MongoDB is running:
```bash
sudo systemctl status mongodb
# OR
mongosh --eval "db.runCommand({ ping: 1 })"
```

---

## Security Best Practices

1. ⚠️ **Change default password immediately after first login**
2. 🔐 Use strong passwords (min 12 chars, mixed case, numbers, symbols)
3. 🚫 Don't commit `.env` file with real passwords
4. 🔄 Rotate passwords regularly
5. 📝 Use different passwords for each environment (dev/staging/prod)

---

## Deployment Checklist

- [ ] Set INIT_ADMIN_PASSWORD in `.env`
- [ ] Set strong password (not default)
- [ ] Verify MongoDB is accessible
- [ ] Start backend (auto-init will run)
- [ ] Check logs for admin creation
- [ ] Test login with credentials
- [ ] Change password after first login
- [ ] Create additional users via UI

---

## Example: Fresh Deployment

```bash
# 1. Clone/deploy application
cd /app/backend

# 2. Configure environment
nano .env
# Add: INIT_ADMIN_PASSWORD=MySecurePass@2024

# 3. Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8001

# 4. Check logs
tail -f logs/backend.log | grep -i admin
# Should see: ✅ INITIAL SYSTEM ADMIN CREATED SUCCESSFULLY!

# 5. Login
# Username: system_admin
# Password: MySecurePass@2024

# 6. Change password via UI
```

---

## Notes

- Auto-init is **idempotent** (safe to run multiple times)
- Only creates admin if **none exists**
- Scripts can be used anytime to create additional admins
- All passwords are **bcrypt hashed** before storage
- Created admins have `is_active=True` by default

---

For more information, see:
- `/app/backend/app/utils/init_admin.py` - Auto-init logic
- `/app/backend/app/core/security.py` - Password hashing
- `/app/backend/app/main.py` - Startup event

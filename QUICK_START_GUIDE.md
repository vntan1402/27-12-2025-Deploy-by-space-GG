# ⚡ QUICK START - TẠO SYSTEM ADMIN TRONG 3 PHÚT

## 🎬 VIDEO SCRIPT STYLE GUIDE

### ⏱️ Thời gian: 3 phút
### 🎯 Mục tiêu: Tạo SYSTEM_ADMIN account trong production

---

## 📍 BƯỚC 1: MỞ FILE (30 giây)

```bash
cd /app/backend
nano quick_create_admin.py
```

**Hoặc dùng editor khác:**
```bash
vi quick_create_admin.py
# hoặc
code quick_create_admin.py
```

---

## 📍 BƯỚC 2: EDIT THÔNG TIN (1 phút)

**Tìm đến dòng này (gần cuối file):**
```python
# 🔧 CUSTOMIZE THESE VALUES:
ADMIN_USERNAME = "production_admin"
ADMIN_EMAIL = "admin@yourcompany.com"
ADMIN_FULL_NAME = "System Administrator"
ADMIN_PASSWORD = "Admin@2024"
COMPANY_NAME = "Your Company Ltd"
```

**Thay đổi thành thông tin của bạn:**
```python
ADMIN_USERNAME = "system_admin"           # ← Thay đổi
ADMIN_EMAIL = "admin@abcmaritime.com"     # ← Thay đổi
ADMIN_FULL_NAME = "Nguyễn Văn A"          # ← Thay đổi
ADMIN_PASSWORD = "MySecure@Pass2024"      # ← QUAN TRỌNG!
COMPANY_NAME = "ABC Maritime Co., Ltd"    # ← Thay đổi
```

**Lưu file:**
- Nano: `Ctrl+X`, `Y`, `Enter`
- Vi: `Esc`, `:wq`, `Enter`

---

## 📍 BƯỚC 3: CHẠY SCRIPT (30 giây)

```bash
python3 quick_create_admin.py
```

**Đợi output:**
```
✅ ADMIN USER CREATED!
Username:     system_admin
Password:     MySecure@Pass2024
Role:         SYSTEM_ADMIN
Company:      ABC Maritime Co., Ltd
🚀 Ready to login!
```

---

## 📍 BƯỚC 4: TEST LOGIN (1 phút)

1. **Mở browser** → Vào production URL
2. **Nhập:**
   - Username: `system_admin`
   - Password: `MySecure@Pass2024`
3. **Click** "Login"
4. **✅ Thành công!** → Vào được HomePage

---

## ✅ DONE! (3 phút)

**Bây giờ bạn có:**
- ✅ SYSTEM_ADMIN account
- ✅ Highest permissions
- ✅ Có thể tạo tất cả roles
- ✅ Quản lý toàn hệ thống

**Next:**
- 👥 Tạo users khác qua UI
- 🏢 Setup companies
- 🚢 Add ships
- 📄 Upload documents

---

## 🎥 VISUAL CHECKLIST

```
┌─────────────────────────────────────┐
│ □ Deploy app                        │
│ □ cd /app/backend                   │
│ □ nano quick_create_admin.py        │
│ □ Edit 5 giá trị                    │
│ □ Save file                         │
│ □ python3 quick_create_admin.py     │
│ □ See "✅ ADMIN USER CREATED!"      │
│ □ Open production URL               │
│ □ Login với credentials             │
│ □ ✅ Success!                       │
└─────────────────────────────────────┘
```

---

## 💬 ONE-LINER COMMANDS

**Toàn bộ process trong terminal:**
```bash
cd /app/backend && \
nano quick_create_admin.py && \
# [Edit file, save, exit] \
python3 quick_create_admin.py
```

---

## 🆘 HELP

**Nếu lỗi:**
```bash
# Check file exists
ls -la quick_create_admin.py

# Check Python works
python3 --version

# Check MongoDB connection
cat .env | grep MONGO_URL

# Check bcrypt installed
python3 -c "import bcrypt; print('OK')"
```

---

## 🎯 KEY POINTS

1. **Username** → Dùng để login
2. **Email** → Liên hệ
3. **Password** → MẬT KHẨU MẠNH! (8+ ký tự, hoa, thường, số, ký tự đặc biệt)
4. **Company Name** → Tên công ty của bạn
5. **Role** → Tự động là `system_admin` (cao nhất)

---

**That's it! Simple as 1-2-3!** 🎉

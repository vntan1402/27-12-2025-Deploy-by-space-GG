# 🎯 HƯỚNG DẪN TẠO SYSTEM_ADMIN - CHI TIẾT TỪNG BƯỚC

## 📋 MỤC LỤC
1. [Chuẩn Bị](#chuẩn-bị)
2. [Cách 1: Quick Create (Nhanh - Recommended)](#cách-1-quick-create)
3. [Cách 2: Interactive Create (Tương tác)](#cách-2-interactive-create)
4. [Xác Nhận Thành Công](#xác-nhận-thành-công)
5. [Test Login](#test-login)
6. [Troubleshooting](#troubleshooting)

---

## 📝 CHUẨN BỊ

### Bước 0.1: Xác nhận bạn đã deploy thành công
```
✅ App đã deploy
✅ Có production URL
✅ Có thể truy cập production environment
```

### Bước 0.2: Truy cập Backend Terminal

**Trong production environment:**
- Mở terminal/console
- Đảm bảo bạn có quyền chạy lệnh

### Bước 0.3: Kiểm tra files script tồn tại
```bash
ls -la /app/backend/quick_create_admin.py
ls -la /app/backend/create_first_admin.py
```

**Kết quả mong đợi:**
```
-rw-r--r-- 1 root root 3770 Nov 10 14:00 quick_create_admin.py
-rw-r--r-- 1 root root 4521 Nov 10 14:00 create_first_admin.py
```

✅ Nếu thấy các files → Tiếp tục
❌ Nếu không thấy → Files chưa được deploy, liên hệ support

---

## 🚀 CÁCH 1: QUICK CREATE (NHANH - RECOMMENDED)

### Bước 1.1: Mở file để edit thông tin

```bash
cd /app/backend
nano quick_create_admin.py
# Hoặc dùng editor khác: vi, vim, code, etc.
```

### Bước 1.2: Tìm đến phần CUSTOMIZE

**Scroll xuống dưới cùng file, tìm đoạn:**
```python
# ============================================
# 🔧 CUSTOMIZE THESE VALUES:
# ============================================
ADMIN_USERNAME = "production_admin"           # Change this
ADMIN_EMAIL = "admin@yourcompany.com"         # Change this
ADMIN_FULL_NAME = "System Administrator"      # Change this
ADMIN_PASSWORD = "Admin@2024"                 # Change this - IMPORTANT!
COMPANY_NAME = "Your Company Ltd"             # Change this or set to None
# ============================================
```

### Bước 1.3: Thay đổi các giá trị

**Ví dụ cụ thể:**
```python
# ============================================
# 🔧 CUSTOMIZE THESE VALUES:
# ============================================
ADMIN_USERNAME = "system_admin"               # ← Username để login
ADMIN_EMAIL = "admin@abcmaritime.com"         # ← Email của bạn
ADMIN_FULL_NAME = "Nguyễn Văn A"              # ← Tên đầy đủ
ADMIN_PASSWORD = "MySecure@Pass2024"          # ← Mật khẩu mạnh!
COMPANY_NAME = "ABC Maritime Co., Ltd"        # ← Tên công ty
# ============================================
```

**📌 Lưu ý về PASSWORD:**
```
✅ Nên:
   - Ít nhất 8 ký tự
   - Có chữ hoa: A-Z
   - Có chữ thường: a-z
   - Có số: 0-9
   - Có ký tự đặc biệt: @#$%
   - Ví dụ: "MySecure@Pass2024"

❌ Không nên:
   - "123456"
   - "password"
   - "admin"
   - Quá đơn giản
```

### Bước 1.4: Lưu file

**Nếu dùng nano:**
```
1. Nhấn: Ctrl + X
2. Nhấn: Y (Yes để save)
3. Nhấn: Enter (confirm filename)
```

**Nếu dùng vi/vim:**
```
1. Nhấn: Esc
2. Gõ: :wq
3. Nhấn: Enter
```

### Bước 1.5: Chạy script

```bash
cd /app/backend
python3 quick_create_admin.py
```

### Bước 1.6: Xem kết quả

**Output mong đợi:**
```
🎯 Creating admin with default settings...
   To customize, edit the values below:

============================================================
⚡ QUICK ADMIN CREATOR
============================================================
✅ Company created: ABC Maritime Co., Ltd
============================================================
✅ ADMIN USER CREATED!
============================================================
Username:     system_admin
Email:        admin@abcmaritime.com
Password:     MySecure@Pass2024
Role:         SYSTEM_ADMIN (Highest Level)
Company:      ABC Maritime Co., Ltd
============================================================
🚀 Ready to login!
============================================================

⚠️  IMPORTANT: Save these credentials securely!
```

✅ **THÀNH CÔNG!** → Chuyển đến [Test Login](#test-login)

---

## 🛠️ CÁCH 2: INTERACTIVE CREATE (TƯƠNG TÁC)

### Bước 2.1: Chạy script interactive

```bash
cd /app/backend
python3 create_first_admin.py
```

### Bước 2.2: Script sẽ hỏi thông tin

**Màn hình sẽ hiển thị:**
```
🎯 Creating admin with default settings...

⚠️  IMPORTANT: Run this script ONLY ONCE in production!
   This creates the first admin user with full permissions.

============================================================
🔐 CREATE FIRST ADMIN USER FOR PRODUCTION
============================================================

📝 Enter Admin Information:
------------------------------------------------------------
Username (e.g., admin): _
```

### Bước 2.3: Nhập thông tin từng bước

#### A. Nhập Username
```
Username (e.g., admin): system_admin
```
**Nhấn Enter**

#### B. Nhập Email
```
Email (e.g., admin@company.com): admin@abcmaritime.com
```
**Nhấn Enter**

#### C. Nhập Full Name
```
Full Name (e.g., System Administrator): Nguyễn Văn A
```
**Nhấn Enter**

#### D. Nhập Password (sẽ ẩn)
```
Password (will be hidden): 
```
**Gõ password (sẽ KHÔNG hiển thị trên màn hình)**
**Ví dụ: MySecure@Pass2024**
**Nhấn Enter**

#### E. Confirm Password
```
Confirm Password: 
```
**Gõ lại password giống y hệt**
**Nhấn Enter**

**⚠️ Nếu passwords không khớp:**
```
❌ Passwords do not match!
```
→ Script sẽ dừng, phải chạy lại từ đầu

**⚠️ Nếu password quá ngắn:**
```
❌ Password must be at least 6 characters!
```
→ Script sẽ dừng, phải chạy lại với password dài hơn

#### F. Tạo Company
```
🏢 Company Setup:
------------------------------------------------------------
Create a new company? (yes/no): yes
```
**Gõ: yes** hoặc **no**
**Nhấn Enter**

**Nếu chọn YES, sẽ hỏi tiếp:**

```
Company Name: ABC Maritime Co., Ltd
```
**Nhấn Enter**

```
Company Email: contact@abcmaritime.com
```
**Nhấn Enter**

```
Company Phone: +84 901 234 567
```
**Nhấn Enter**

### Bước 2.4: Script xử lý và tạo user

**Màn hình sẽ hiển thị:**
```
👤 Creating Admin User...
------------------------------------------------------------
✅ Company 'ABC Maritime Co., Ltd' created!

============================================================
✅ ADMIN USER CREATED SUCCESSFULLY!
============================================================
Username: system_admin
Email: admin@abcmaritime.com
Role: SYSTEM_ADMIN
Company: ABC Maritime Co., Ltd

🚀 You can now login with these credentials!
============================================================
```

✅ **THÀNH CÔNG!**

---

## ✅ XÁC NHẬN THÀNH CÔNG

### Kiểm tra trong Database

```bash
cd /app/backend
export $(cat .env | xargs)
python3 -c "
import asyncio
from mongodb_database import mongo_db

async def check():
    await mongo_db.connect()
    users = await mongo_db.find_all('users', {})
    print(f'Total users: {len(users)}')
    for user in users:
        print(f'  - {user.get(\"username\")}: {user.get(\"role\")} ({user.get(\"email\")})')
    await mongo_db.disconnect()

asyncio.run(check())
"
```

**Kết quả mong đợi:**
```
Total users: 1
  - system_admin: system_admin (admin@abcmaritime.com)
```

✅ **User đã được tạo trong database!**

---

## 🔐 TEST LOGIN

### Bước 3.1: Truy cập Production URL

**Mở browser và vào:**
```
https://your-production-url.emergentagent.com
```

### Bước 3.2: Nhập credentials

**Trang Login:**
```
Username: system_admin          (hoặc username bạn đã tạo)
Password: MySecure@Pass2024     (password bạn đã đặt)
```

### Bước 3.3: Click "Login" / "Đăng nhập"

### Bước 3.4: Kiểm tra đã vào HomePage

**Bạn sẽ thấy:**
```
✅ Chào mừng đến hệ thống quản lý tàu biển - ABC Maritime Co., Ltd
✅ Sidebar với các menu
✅ Company logo (nếu có)
```

### Bước 3.5: Verify Role

**Vào: System Settings → User Management**

**Bạn sẽ thấy:**
```
✅ List of users (có thể chỉ 1 user: bạn)
✅ Có nút "+ Add User"
✅ Có thể thêm user mới
```

**Click "+ Add User" và kiểm tra dropdown "Role":**
```
✅ Nếu thấy TẤT CẢ roles:
   - system_admin
   - super_admin
   - admin
   - manager
   - editor
   - viewer

→ Bạn là SYSTEM_ADMIN ✅ Thành công!
```

---

## 🚨 TROUBLESHOOTING

### Lỗi 1: "MONGO_URL environment variable not set"

**Nguyên nhân:** Backend .env không có MONGO_URL

**Giải pháp:**
```bash
# Kiểm tra .env file
cat /app/backend/.env | grep MONGO_URL

# Nếu không có, cần configure lại
```

### Lỗi 2: "Username already exists"

**Nguyên nhân:** Username đã tồn tại trong database

**Giải pháp A:** Dùng username khác
```python
ADMIN_USERNAME = "system_admin2"  # Thay đổi
```

**Giải pháp B:** Xóa user cũ (cẩn thận!)
```bash
cd /app/backend
export $(cat .env | xargs)
python3 -c "
import asyncio
from mongodb_database import mongo_db

async def delete():
    await mongo_db.connect()
    result = await mongo_db.delete('users', {'username': 'system_admin'})
    print('Deleted')
    await mongo_db.disconnect()

asyncio.run(delete())
"
```

### Lỗi 3: "Cannot import bcrypt"

**Nguyên nhân:** Chưa cài bcrypt

**Giải pháp:**
```bash
pip install bcrypt
# Sau đó chạy lại script
```

### Lỗi 4: Script chạy nhưng không hiển thị output

**Nguyên nhân:** Python buffering

**Giải pháp:**
```bash
python3 -u quick_create_admin.py
# Thêm flag -u để unbuffered
```

### Lỗi 5: "Cannot login" sau khi tạo user

**Check 1:** Username & password có đúng không?
```
→ Kiểm tra lại chính xác
→ Password có phân biệt hoa thường
```

**Check 2:** User có active không?
```bash
cd /app/backend
export $(cat .env | xargs)
python3 -c "
import asyncio
from mongodb_database import mongo_db

async def check():
    await mongo_db.connect()
    user = await mongo_db.find_one('users', {'username': 'system_admin'})
    print(f'is_active: {user.get(\"is_active\")}')
    await mongo_db.disconnect()

asyncio.run(check())
"
```

**Kết quả mong đợi:** `is_active: True`

**Check 3:** JWT_SECRET có configured không?
```bash
cat /app/backend/.env | grep JWT_SECRET
```

**Check 4:** Clear browser cache và thử lại
```
Ctrl + Shift + Delete → Clear cache → Thử login lại
```

### Lỗi 6: File script không tồn tại

**Nguyên nhân:** Files chưa được deploy

**Giải pháp:**
```
1. Check lại trong development environment
2. Redeploy app
3. Hoặc tạo file manually trong production
```

---

## 📋 CHECKLIST HOÀN CHỈNH

```
□ ✅ Đã deploy app thành công
□ ✅ Có production URL
□ ✅ Truy cập được backend terminal
□ ✅ File script tồn tại (/app/backend/quick_create_admin.py)
□ ✅ Edit script với thông tin của bạn
□ ✅ Chạy script: python3 quick_create_admin.py
□ ✅ Script output: "✅ ADMIN USER CREATED!"
□ ✅ Verify trong database: user tồn tại
□ ✅ Test login thành công
□ ✅ Verify role: SYSTEM_ADMIN
□ ✅ Test tạo user mới: có thể tạo tất cả roles
□ ✅ Lưu credentials an toàn
```

---

## 💡 TIPS

### 1. Lưu Credentials An Toàn
```
✅ Ghi vào Password Manager
✅ Lưu vào note an toàn
✅ Không share qua email/chat không mã hóa
```

### 2. Nếu Quên Password
```
Chạy lại script với username khác
Hoặc reset password qua database (cần IT support)
```

### 3. Backup Scripts
```bash
# Tạo backup scripts về local
scp user@production:/app/backend/*.py ./local-backup/
```

### 4. Test Ngay Sau Khi Tạo
```
Đừng đợi! Test login ngay để đảm bảo mọi thứ hoạt động
```

---

## 🎯 TÓM TẮT NHANH

### Các Lệnh Chính:
```bash
# 1. Di chuyển vào folder
cd /app/backend

# 2. Edit script
nano quick_create_admin.py
# → Thay đổi: username, email, password, company name
# → Save: Ctrl+X, Y, Enter

# 3. Chạy script
python3 quick_create_admin.py

# 4. Verify
python3 -c "import asyncio; from mongodb_database import mongo_db; asyncio.run(mongo_db.connect()); print('Connected')"
```

### Thời Gian:
```
⏱️  Toàn bộ quá trình: < 5 phút
   - Edit script: 2 phút
   - Run script: < 30 giây
   - Test login: 1 phút
```

---

## ✅ BẠN ĐÃ HOÀN THÀNH!

**Nếu mọi thứ thành công:**
```
🎉 Chúc mừng!
✅ SYSTEM_ADMIN account đã được tạo
✅ Login thành công
✅ Có thể tạo users khác qua UI

👉 Next step: Tạo các users khác cho tổ chức của bạn!
```

**Nếu gặp vấn đề:**
```
📖 Xem lại phần Troubleshooting
💬 Hoặc liên hệ support với:
   - Error message cụ thể
   - Steps bạn đã thực hiện
   - Screenshot nếu có
```

---

**Last Updated:** 2025-11-10
**Version:** 1.0.0
**Status:** ✅ Ready to Use

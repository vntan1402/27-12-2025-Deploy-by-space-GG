# 👥 HƯỚNG DẪN TẠO USERS TRONG PRODUCTION

## 🎯 Tổng Quan

Khi deploy với **Option A: Fresh Start**, production sẽ không có users nào.
Bạn cần tạo admin account đầu tiên, sau đó dùng admin account này để tạo các users khác qua UI.

---

## 📋 QUY TRÌNH SETUP USERS

### BƯỚC 1: Tạo Admin Account Đầu Tiên

#### Cách 1: Sử dụng Script (Recommended - Nhanh nhất)

```bash
# Trong production environment:
cd /app/backend
python3 create_first_admin.py
```

**Script sẽ hỏi:**
```
Username: admin
Email: admin@yourcompany.com  
Full Name: System Administrator
Password: ******** (ít nhất 6 ký tự)
Confirm Password: ********

Create company? yes/no
  → yes: Tạo luôn company mới
  → no: Bỏ qua (tạo company sau qua UI)

Company Name: Your Company Ltd
Company Email: contact@yourcompany.com
Company Phone: +84 xxx xxx xxx
```

**Kết quả:**
```
✅ Admin user created!
✅ Company created (nếu chọn yes)
🚀 Có thể login ngay!
```

---

#### Cách 2: Tạo Qua MongoDB Command

```python
# Trong production environment, tạo file: create_admin_manual.py

import asyncio
from mongodb_database import mongo_db
import bcrypt
from datetime import datetime
import uuid

async def create_admin_manual():
    await mongo_db.connect()
    
    # Thay đổi thông tin theo ý bạn
    admin = {
        "id": str(uuid.uuid4()),
        "username": "admin",                    # ← Thay đổi username
        "email": "admin@company.com",           # ← Thay đổi email
        "full_name": "System Administrator",    # ← Thay đổi tên
        "password": bcrypt.hashpw("Admin@123".encode(), bcrypt.gensalt()).decode(),  # ← Thay đổi password
        "role": "super_admin",
        "department": ["technical"],
        "company": None,                        # ← Thêm company ID sau
        "ship": None,
        "zalo": "",
        "gmail": "admin@company.com",
        "is_active": True,
        "created_at": datetime.now()
    }
    
    await mongo_db.insert('users', admin)
    print("✅ Admin created!")
    await mongo_db.disconnect()

asyncio.run(create_admin_manual())
```

Sau đó chạy:
```bash
python3 create_admin_manual.py
```

---

### BƯỚC 2: Login với Admin Account

1. Truy cập production URL
2. Đăng nhập với:
   - Username: `admin` (hoặc username bạn đã tạo)
   - Password: password bạn đã nhập

---

### BƯỚC 3: Tạo Company (Nếu Chưa Có)

**Qua UI:**
1. Login với admin account
2. Vào **System Settings** → **Company Management**
3. Click **"+ Add Company"**
4. Điền thông tin:
   ```
   Company Name: Your Company Ltd
   Email: contact@company.com
   Phone: +84 xxx xxx xxx
   Address: Company address
   Software Expiry: (tùy chọn)
   ```
5. Click **Save**

**Kết quả:** Company được tạo, admin account có thể được gán vào company này.

---

### BƯỚC 4: Update Admin Account với Company

**Qua UI:**
1. Vào **System Settings** → **User Management**
2. Find admin user vừa tạo
3. Click **Edit**
4. Chọn **Company** từ dropdown
5. Click **Save**

---

### BƯỚC 5: Tạo Các Users Khác

**Qua UI (Recommended - Dễ nhất):**

1. Login với admin account
2. Vào **System Settings** → **User Management**
3. Click **"+ Add User"**

**Điền thông tin user:**
```
Username: user1
Email: user1@company.com
Full Name: John Doe
Password: User@123
Role: 
  - VIEWER (Crew - chỉ xem)
  - EDITOR (Ship Officer - xem & chỉnh sửa)
  - MANAGER (Quản lý)
  - ADMIN (Quản trị công ty)
  - SUPER_ADMIN (Quản trị hệ thống)

Department: (có thể chọn nhiều)
  - Technical
  - Operations (Khai thác)
  - Logistics
  - Finance
  - Ship Crew (Thuyền viên tàu)
  - SSO (Ship Security Officer)
  - CSO (Company Security Officer)
  - Crewing
  - Safety
  - Commercial (Kinh Doanh)
  - DPA
  - Supply

Company: Chọn công ty
Ship: Chọn tàu (nếu là crew/ship officer)
Zalo: Zalo contact
Gmail: Gmail contact
```

4. Click **Save**
5. User mới có thể login ngay!

---

## 👥 CÁC LOẠI USER & PERMISSIONS

### 1. **SUPER_ADMIN** (Quản trị viên hệ thống)
```
Quyền cao nhất:
✅ Quản lý tất cả companies
✅ Quản lý tất cả users
✅ Quản lý system settings
✅ Xem & chỉnh sửa tất cả dữ liệu
✅ Configure Google Drive
✅ Manage software expiry
```

**Khi nào cần:**
- Admin chính của hệ thống
- IT Administrator

---

### 2. **ADMIN** (Quản trị viên công ty)
```
Quyền trong công ty:
✅ Quản lý users của công ty
✅ Quản lý ships của công ty
✅ Quản lý tất cả documents
✅ View company info
✅ Upload company logo
❌ Không quản lý companies khác
❌ Không quản lý system settings
```

**Khi nào cần:**
- Quản lý công ty
- Technical Superintendent

---

### 3. **MANAGER** (Người quản lý)
```
Quyền xem & phê duyệt:
✅ Xem tất cả documents
✅ Chỉnh sửa documents
✅ Xem ships & certificates
✅ View reports
❌ Không quản lý users
❌ Không xóa documents
```

**Khi nào cần:**
- Fleet Manager
- Operations Manager

---

### 4. **EDITOR** (Ship Officer - Sĩ quan tàu)
```
Quyền chỉnh sửa:
✅ Xem documents của tàu mình
✅ Upload & edit documents
✅ Update ship certificates
✅ Có thể là SSO (Ship Security Officer)
❌ Không xóa documents
❌ Không quản lý users
```

**Khi nào cần:**
- Chief Officer
- Chief Engineer
- Ship Officers

---

### 5. **VIEWER** (Crew - Thuyền viên)
```
Quyền chỉ xem:
✅ Xem documents của tàu mình
✅ Download documents
❌ Không upload
❌ Không chỉnh sửa
❌ Không xóa
```

**Khi nào cần:**
- Crew members
- Ship staff

---

## 🎯 SETUP MẪU CHO MỘT CÔNG TY

### Ví dụ: Setup cho công ty "ABC Maritime"

**1. Tạo Company:**
```
Name: ABC Maritime Co., Ltd
Email: info@abcmaritime.com
Phone: +84 901 234 567
```

**2. Tạo Admin của công ty:**
```
Username: abc_admin
Role: ADMIN
Company: ABC Maritime
Department: Technical, Operations
```

**3. Tạo Fleet Manager:**
```
Username: fleet_manager
Role: MANAGER
Company: ABC Maritime
Department: Operations
```

**4. Tạo Ship Officers (cho mỗi tàu):**
```
Tàu "MV Ocean Star":
  Username: ocean_star_co
  Role: EDITOR
  Ship: MV Ocean Star
  Department: Ship Crew, SSO

Tàu "MV Sea Explorer":
  Username: sea_explorer_co
  Role: EDITOR
  Ship: MV Sea Explorer
  Department: Ship Crew
```

**5. Tạo Crew Members:**
```
Username: crew_john
Role: VIEWER
Ship: MV Ocean Star
Department: Ship Crew
```

---

## 🔐 BẢO MẬT PASSWORDS

### Recommendations:

**Mật khẩu mạnh:**
```
✅ Ít nhất 8 ký tự
✅ Kết hợp chữ hoa, chữ thường
✅ Có số và ký tự đặc biệt
✅ Ví dụ: Admin@2024, Pass#123Word

❌ Tránh: 123456, password, admin
```

**Thay đổi mật khẩu:**
- Users có thể tự thay đổi mật khẩu trong profile settings
- Admin có thể reset password cho users

---

## 📊 CHECKLIST SAU KHI SETUP

```
□ ✅ Admin account đã tạo và login được
□ ✅ Company đã tạo
□ ✅ Admin đã gán vào company
□ ✅ Company logo đã upload (tùy chọn)
□ ✅ Software expiry đã set (nếu cần)
□ ✅ Các users cần thiết đã tạo:
    □ Admin cho công ty
    □ Managers
    □ Ship Officers
    □ Crew members
□ ✅ Test login với các user khác nhau
□ ✅ Verify permissions đúng cho từng role
□ ✅ Users có thể xem/edit theo quyền
```

---

## 🚨 TROUBLESHOOTING

### Vấn đề: "Cannot create admin - script fails"
```
Giải pháp:
1. Check MongoDB connection:
   - Verify MONGO_URL in .env
   - Test: python3 -c "from mongodb_database import mongo_db; import asyncio; asyncio.run(mongo_db.connect())"

2. Check bcrypt installed:
   pip install bcrypt
```

### Vấn đề: "Created admin but cannot login"
```
Giải pháp:
1. Verify username & password correct
2. Check user.is_active = True
3. Check JWT_SECRET configured in .env
4. Clear browser cache và thử lại
```

### Vấn đề: "User created but no permissions"
```
Giải pháp:
1. Check user.role is set correctly
2. Verify user.company matches a real company
3. For ship-related permissions, verify user.ship is set
```

---

## 💡 TIPS & BEST PRACTICES

1. **Tạo Admin đầu tiên:**
   - Dùng script `create_first_admin.py` - nhanh nhất
   - Password mạnh cho admin account
   - Note lại credentials an toàn

2. **Tổ chức Users:**
   - 1 SUPER_ADMIN cho hệ thống
   - 1-2 ADMIN cho mỗi công ty
   - Managers theo department
   - Officers cho mỗi tàu
   - Crew members theo tàu

3. **Security:**
   - Thay đổi password định kỳ
   - Không share admin credentials
   - Deactivate users khi không còn làm việc
   - Regular audit user list

4. **Documentation:**
   - Giữ danh sách users & roles
   - Document ai có quyền gì
   - Update khi có thay đổi

---

## 📞 SUPPORT

Nếu gặp vấn đề khi tạo users:
1. Check script output cho error messages
2. Verify database connection
3. Test với simple user creation first
4. Check logs trong production environment

---

**Tóm tắt:**
- 🔧 Dùng `create_first_admin.py` để tạo admin đầu tiên
- 🖥️ Sau đó dùng UI để tạo các users khác (dễ hơn)
- 👥 5 loại roles: VIEWER, EDITOR, MANAGER, ADMIN, SUPER_ADMIN
- 🏢 Gán users vào companies và ships tương ứng
- 🔐 Đảm bảo passwords mạnh và an toàn

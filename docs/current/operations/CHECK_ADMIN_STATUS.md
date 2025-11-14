# Hướng Dẫn Kiểm Tra System Admin Sau Khi Deploy

## 📋 Tổng Quan
Sau khi deploy, bạn cần kiểm tra xem System Admin đã được tạo tự động chưa để có thể đăng nhập vào hệ thống.

---

## ✅ Cách 1: Kiểm Tra Backend Logs (Nhanh Nhất)

### Bước 1: SSH vào server hoặc mở terminal
```bash
ssh user@your-server-ip
# Hoặc nếu đang ở local: mở terminal
```

### Bước 2: Kiểm tra logs
```bash
tail -n 100 /var/log/supervisor/backend.out.log | grep -i "admin"
```

### Kết quả mong đợi:
✅ **Nếu admin đã được tạo:**
```
INFO:init_admin_startup:✅ Admin users already exist (1 system_admin, 0 super_admin)
```

🆕 **Nếu admin vừa được tạo lần đầu:**
```
INFO:init_admin_startup:✅ INITIAL ADMIN USER CREATED SUCCESSFULLY!
INFO:init_admin_startup:Username:     system_admin
INFO:init_admin_startup:Email:        admin@yourcompany.com
INFO:init_admin_startup:Role:         SYSTEM_ADMIN
```

❌ **Nếu có lỗi:**
```
ERROR:init_admin_startup:❌ INIT_ADMIN_PASSWORD not set in environment variables!
ERROR:init_admin_startup:❌ Error initializing admin: ...
```

---

## 🌐 Cách 2: Kiểm Tra Qua Admin API Endpoint

### Bước 1: Gọi API status endpoint
```bash
curl -X GET "https://your-domain.com/api/admin/status"
```

Hoặc nếu local:
```bash
curl -X GET "http://localhost:8001/api/admin/status"
```

### Kết quả mong đợi:
✅ **Admin đã tồn tại:**
```json
{
  "admin_exists": true,
  "total_admins": 1,
  "admin_breakdown": {
    "system_admin": 1,
    "super_admin": 0
  },
  "users": [
    {
      "username": "system_admin",
      "email": "admin@yourcompany.com",
      "role": "system_admin",
      "company": "Your Company Ltd"
    }
  ]
}
```

❌ **Chưa có admin:**
```json
{
  "admin_exists": false,
  "total_admins": 0,
  "admin_breakdown": {
    "system_admin": 0,
    "super_admin": 0
  },
  "users": []
}
```

---

## 🔐 Cách 3: Thử Login Trực Tiếp

### Bước 1: Kiểm tra thông tin đăng nhập từ Environment Variables

Xem các biến môi trường đã set:
```bash
cat /app/backend/.env | grep INIT_ADMIN
```

Hoặc trong Emergent Platform → Deployments panel → Xem các env variables:
- `INIT_ADMIN_USERNAME`
- `INIT_ADMIN_PASSWORD`
- `INIT_ADMIN_EMAIL`
- `INIT_ADMIN_FULL_NAME`

### Bước 2: Test login qua API
```bash
curl -X POST "https://your-domain.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "system_admin",
    "password": "YourSecure@Pass2024",
    "remember_me": false
  }'
```

### Kết quả mong đợi:
✅ **Login thành công:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "username": "system_admin",
    "role": "system_admin",
    "email": "admin@yourcompany.com",
    ...
  }
}
```

❌ **Login thất bại:**
```json
{
  "detail": "Invalid credentials"
}
```

### Bước 3: Test login qua UI
1. Mở browser và truy cập: `https://your-domain.com`
2. Nhập username và password từ env variables
3. Click "Đăng nhập"
4. Nếu thành công → Được redirect đến homepage

---

## 🗄️ Cách 4: Kiểm Tra Database Trực Tiếp

### Bước 1: Kết nối MongoDB
```bash
mongosh "mongodb://localhost:27017/ship_management"
```

### Bước 2: Query user collection
```javascript
db.users.find({ "role": "system_admin" }).pretty()
```

### Kết quả mong đợi:
✅ **Admin tồn tại:**
```json
{
  "_id": ObjectId("..."),
  "id": "cc269020-8634-419a-bd44-eb431ba28119",
  "username": "system_admin",
  "email": "admin@yourcompany.com",
  "full_name": "System Administrator",
  "role": "system_admin",
  "password_hash": "$2b$12$...",
  "company": "0a6eaf96-0aaf-4793-89be-65d62cb7953c",
  "is_active": true,
  "created_at": ISODate("2025-11-10T14:53:04.590Z")
}
```

❌ **Không có admin:**
```
(empty result)
```

### Bước 3: Đếm số lượng admin
```javascript
db.users.countDocuments({ "role": "system_admin" })
// Kết quả mong đợi: 1
```

---

## 🔧 Xử Lý Khi Admin Chưa Được Tạo

### Nguyên nhân thường gặp:
1. ❌ Environment variables chưa được set đúng
2. ❌ Backend chưa restart sau khi thêm env variables
3. ❌ `INIT_ADMIN_PASSWORD` bị thiếu hoặc empty
4. ❌ MongoDB connection failed

### Giải pháp:

#### **A. Kiểm tra Environment Variables**
```bash
# Xem tất cả INIT_ADMIN variables
cat /app/backend/.env | grep INIT_ADMIN

# Đảm bảo có đủ các biến sau:
# INIT_ADMIN_USERNAME=system_admin
# INIT_ADMIN_EMAIL=admin@yourcompany.com
# INIT_ADMIN_PASSWORD=YourSecure@Pass2024
# INIT_ADMIN_FULL_NAME=System Administrator
# INIT_COMPANY_NAME=Your Company Ltd
```

#### **B. Restart Backend Service**
```bash
sudo supervisorctl restart backend

# Đợi 5-10 giây rồi kiểm tra logs
tail -f /var/log/supervisor/backend.out.log
```

#### **C. Tạo Admin Thủ Công Qua API** (Nếu các cách trên không được)

**Lưu ý:** Cần `ADMIN_CREATION_SECRET` từ env variables

```bash
# Lấy secret key
SECRET=$(cat /app/backend/.env | grep ADMIN_CREATION_SECRET | cut -d'=' -f2)

# Gọi API tạo admin
curl -X POST "https://your-domain.com/api/admin/create-from-env" \
  -H "X-Admin-Secret: $SECRET"
```

#### **D. Tạo Admin Thủ Công Qua Script Python**
```bash
cd /app/backend
python3 init_admin_startup.py
```

---

## 📊 Checklist Kiểm Tra Nhanh

| Bước | Mô tả | Lệnh | Trạng thái |
|------|-------|------|------------|
| 1 | Backend logs có message "Admin users already exist" | `tail -n 50 /var/log/supervisor/backend.out.log \| grep admin` | ☐ |
| 2 | API status trả về admin_exists: true | `curl http://localhost:8001/api/admin/status` | ☐ |
| 3 | Login qua API thành công | `curl -X POST http://localhost:8001/api/auth/login -d '{"username":"system_admin",...}'` | ☐ |
| 4 | Login qua UI thành công | Mở browser và test | ☐ |
| 5 | Database có record system_admin | `mongosh -> db.users.find({role:"system_admin"})` | ☐ |

---

## 🆘 Cần Hỗ Trợ?

Nếu sau khi kiểm tra vẫn gặp vấn đề:

1. **Thu thập thông tin:**
   ```bash
   # Backend logs
   tail -n 200 /var/log/supervisor/backend.out.log > backend_logs.txt
   
   # Environment variables (ẩn password)
   cat /app/backend/.env | grep INIT_ADMIN | sed 's/PASSWORD=.*/PASSWORD=***/' > env_vars.txt
   
   # Admin API status
   curl http://localhost:8001/api/admin/status > admin_status.json
   ```

2. **Gửi thông tin cho support team**

3. **Hoặc chạy lệnh troubleshoot:**
   ```bash
   cd /app/backend
   python3 -c "
   import asyncio
   from init_admin_startup import init_admin_if_needed
   asyncio.run(init_admin_if_needed())
   "
   ```

---

## 📝 Thông Tin Mặc Định (Nếu Sử Dụng Template)

| Field | Value |
|-------|-------|
| Username | `system_admin` |
| Password | `YourSecure@Pass2024` |
| Email | `admin@yourcompany.com` |
| Role | `system_admin` |
| Company | `Your Company Ltd` |

**⚠️ LƯU Ý QUAN TRỌNG:** Sau khi login lần đầu, BẮT BUỘC đổi password ngay!

---

## 🎯 Kết Luận

Sau khi deploy, admin sẽ được tạo tự động nếu:
- ✅ Environment variables đã set đầy đủ
- ✅ Backend khởi động thành công
- ✅ MongoDB connection hoạt động

Sử dụng các cách kiểm tra trên theo thứ tự từ **Cách 1 → Cách 4** để nhanh chóng xác định trạng thái admin.

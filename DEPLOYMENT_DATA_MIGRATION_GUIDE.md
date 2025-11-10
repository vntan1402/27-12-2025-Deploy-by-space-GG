# 🔄 HƯỚNG DẪN MIGRATE DATA KHI DEPLOY

## ⚠️ QUAN TRỌNG: Data KHÔNG tự động chuyển

Khi bạn deploy ứng dụng, production sẽ có MongoDB instance MỚI (trống).
Dữ liệu từ development KHÔNG tự động chuyển sang production.

---

## 📊 DỮ LIỆU HIỆN TẠI (Development)

### Đã Export Thành Công:
```
✅ Companies: 3 records
✅ Users: 5 records (bao gồm tất cả tài khoản đăng nhập)
✅ Ships: 4 records
✅ Audit Certificates: 3 records
✅ Drawings & Manuals: 4 records
✅ Test Reports: 6 records
✅ Approval Documents: 1 record
✅ System Settings: 1 record
```

### Vị trí Export:
```
📁 /app/backend/production_data_export/
   ├── companies.json
   ├── users.json (← QUAN TRỌNG: Chứa tất cả user accounts)
   ├── ships.json
   ├── audit_certificates.json
   ├── drawings_manuals.json
   ├── test_reports.json
   ├── approval_documents.json
   ├── system_settings.json
   └── export_summary.json
```

---

## 🚀 QUY TRÌNH MIGRATE DATA SAU KHI DEPLOY

### Bước 1: Download Files Export
```bash
# Zip toàn bộ folder export
cd /app/backend
tar -czf production_data_backup.tar.gz production_data_export/

# Download file này về máy local của bạn
# Sử dụng: Save to GitHub, Download trực tiếp, hoặc copy files
```

### Bước 2: Deploy Ứng Dụng
```
1. Click nút "Deploy" 
2. Đợi ~10 phút cho deploy hoàn tất
3. Nhận URL production
```

### Bước 3: Upload Data Export vào Production
```
Có 2 cách:

CÁCH 1: Sử dụng Code Editor (Recommended)
1. Truy cập production environment
2. Upload folder "production_data_export/" vào /app/backend/
3. Chạy script import

CÁCH 2: Manual Import qua MongoDB
1. Download các file JSON
2. Sử dụng MongoDB tools để import
```

### Bước 4: Chạy Import Script
```bash
# Trong production environment:
cd /app/backend
python3 import_production_data.py

# Script sẽ:
# 1. Đọc các file JSON từ production_data_export/
# 2. Convert datetime strings về datetime objects
# 3. Import vào production MongoDB
# 4. Confirm trước khi replace data (nếu đã có)
```

---

## 📋 USERS SẼ ĐƯỢC MIGRATE

### User Accounts (từ users.json):
```
1. admin1               - admin@amcsc.vn          (ADMIN)
2. admin                - admin@amcsc.vn          (SUPER_ADMIN)
3. Sadmin               - vntan1402@gmail.com     (SUPER_ADMIN)
4. crew1                - (VIEWER)
5. C/O                  - (EDITOR)
```

**Mật khẩu:** 
- ✅ Mật khẩu đã được hash (bcrypt) trong database
- ✅ Users có thể đăng nhập với mật khẩu CŨ sau khi import
- ⚠️ Nếu quên mật khẩu, cần reset trong production

---

## 🎯 LỰA CHỌN KHÁC: BẮT ĐẦU TỪ ĐẦU

Nếu đây là test data và bạn muốn bắt đầu sạch:

### Option A: Fresh Start (Production trống)
```
✅ Ưu điểm:
  - Sạch sẽ, không có test data
  - Tạo users mới từ đầu
  - Phù hợp nếu đang test

❌ Nhược điểm:
  - Mất tất cả data hiện tại
  - Phải tạo lại admin accounts
  - Phải setup lại companies
```

### Option B: Migrate Data (Recommended)
```
✅ Ưu điểm:
  - Giữ nguyên tất cả users
  - Giữ nguyên companies setup
  - Giữ nguyên test data để demo
  - Không cần tạo lại từ đầu

❌ Nhược điểm:
  - Phải thực hiện import process
  - Có thể có test data không cần thiết
```

---

## 🔐 QUAN TRỌNG: Admin Account

Để đảm bảo bạn luôn có quyền truy cập production:

### Trước khi Deploy:
1. ✅ Note lại username/password của admin accounts
2. ✅ Export data (ĐÃ HOÀN THÀNH)
3. ✅ Backup files export về local

### Sau khi Deploy:
```python
# Nếu cần tạo admin account mới trong production:
# Có thể chạy script sau trong production environment:

import asyncio
from mongodb_database import mongo_db
import bcrypt

async def create_admin():
    await mongo_db.connect()
    
    admin_user = {
        "id": "new-admin-uuid",
        "username": "production_admin",
        "email": "your-email@company.com",
        "password": bcrypt.hashpw("your-secure-password".encode(), bcrypt.gensalt()).decode(),
        "full_name": "Production Admin",
        "role": "super_admin",
        "department": ["technical"],
        "company": "YOUR_COMPANY_ID",
        "is_active": True,
        "created_at": datetime.now()
    }
    
    await mongo_db.insert("users", admin_user)
    await mongo_db.disconnect()

asyncio.run(create_admin())
```

---

## 📝 CHECKLIST SAU KHI MIGRATE

Sau khi import data vào production, verify:

```
□ Login với admin account để test
□ Check companies list
□ Check ships list  
□ Check users list
□ Test upload document
□ Test AI extraction (nếu có)
□ Test Google Drive sync (nếu có)
□ Verify company logo hiển thị
```

---

## 💡 TIPS & BEST PRACTICES

1. **Backup Thường Xuyên:**
   ```bash
   # Chạy định kỳ trong production:
   python3 export_production_data.py
   # Download backup về local
   ```

2. **Test Import Trước:**
   - Test import script trong development trước
   - Verify data integrity sau import

3. **Documentation:**
   - Note lại mọi thay đổi về data schema
   - Document migration steps

4. **Rollback Plan:**
   - Luôn có backup trước khi import
   - Biết cách restore nếu có vấn đề

---

## 🆘 TROUBLESHOOTING

### Vấn đề: "Import script báo lỗi"
```
Giải pháp:
1. Check file export_summary.json có đầy đủ không
2. Verify các file JSON không bị corrupt
3. Check MongoDB connection trong production
```

### Vấn đề: "Không login được sau import"
```
Giải pháp:
1. Verify users.json có data
2. Check password hashing format
3. Tạo admin account mới nếu cần (dùng script trên)
```

### Vấn đề: "Company logo không hiển thị"
```
Giải pháp:
1. Upload lại company logos vào /uploads/company_logos/
2. Update logo_url trong companies collection
3. Test endpoint /api/files/company_logos/{filename}
```

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề trong quá trình migrate:
1. Check logs trong production
2. Verify database connection
3. Test với collection nhỏ trước (vd: system_settings)
4. Liên hệ support nếu cần

---

**Tóm tắt:**
- ❌ Data KHÔNG tự động migrate
- ✅ Đã export thành công tất cả data
- ✅ Có scripts để import vào production  
- ✅ Tất cả user accounts sẽ được giữ nguyên (bao gồm passwords)
- 📁 Backup location: /app/backend/production_data_export/

**Recommended:** Migrate data để giữ nguyên users và setup hiện tại.

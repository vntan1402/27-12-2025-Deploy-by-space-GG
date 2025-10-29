# 🔒 Google Apps Script v3.0 - Phiên Bản Bảo Mật

## ✨ Tính Năng Bảo Mật Mới

### 1. ✅ Folder ID Động (Không Hardcode)
- **Trước đây**: `ROOT_FOLDER_ID` được hardcode trong script
- **Bây giờ**: Folder ID được truyền qua mỗi request từ backend
- **Lợi ích**: Nếu lộ Web App URL, dữ liệu vẫn an toàn vì không biết folder_id

### 2. ✅ Logging An Toàn
- **Mask sensitive data**: 
  - Folder ID: `1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB` → `1UeKVB***`
  - File content: `<1234 bytes>` thay vì log toàn bộ nội dung
- **Vẫn đủ thông tin để debug**: action, status, filename, size

### 3. 🔒 Validation Tăng Cường
- Kiểm tra `folder_id` bắt buộc trong mọi request
- Xác thực quyền truy cập folder trước khi thực hiện action
- Error messages rõ ràng nhưng không lộ thông tin nhạy cảm

---

## 📋 Hướng Dẫn Deploy Apps Script v3.0

### Bước 1: Mở Google Apps Script Editor

1. Truy cập: https://script.google.com
2. Tìm project hiện tại của bạn (hoặc tạo mới)

### Bước 2: Copy Code Mới

1. Mở file `/app/GOOGLE_APPS_SCRIPT_V3_SECURE.js`
2. Copy toàn bộ nội dung
3. Paste vào Apps Script Editor (thay thế code cũ hoàn toàn)
4. **Lưu ý**: Không cần thay đổi gì trong code, không có ROOT_FOLDER_ID để config

### Bước 3: Lưu Script

1. Click **Save** (hoặc Ctrl+S / Cmd+S)
2. Đặt tên project: "SystemGoogleDriveProxy_v3_Secure"

### Bước 4: Deploy Mới (QUAN TRỌNG)

**Option A: Deploy Mới Hoàn Toàn (Recommended)**

1. Click nút **Deploy** (góc trên bên phải)
2. Chọn **"New deployment"**
3. Click icon ⚙️ bên cạnh "Select type"
4. Chọn **"Web app"**
5. Điền thông tin:
   - **Description**: "v3.0 - Secure Dynamic Folder"
   - **Execute as**: **Me** (email của bạn)
   - **Who has access**: **Anyone**
6. Click **Deploy**
7. **Authorize** nếu được yêu cầu (review permissions → Allow)
8. **Copy NEW Web App URL** (URL này sẽ khác với URL cũ)
9. Click **Done**

**Option B: Cập Nhật Deployment Hiện Tại**

1. Click **Deploy** → **Manage deployments**
2. Click icon ✏️ (Edit) bên cạnh deployment hiện tại
3. Trong **Version**: Chọn **"New version"**
4. Click **Deploy**
5. Web App URL giữ nguyên nhưng code đã được cập nhật

---

## 🧪 Test Apps Script v3.0

### Cách 1: Dùng Test Script

```bash
cd /app
./test_apps_script_v3_secure.sh
```

Nhập Web App URL khi được hỏi.

### Cách 2: Test Thủ Công với curl

```bash
# Thay YOUR_WEB_APP_URL bằng URL thực của bạn
curl -X POST "YOUR_WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test_connection",
    "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
  }'
```

### Kết Quả Mong Đợi:

✅ **Thành công:**
```json
{
  "success": true,
  "message": "Connection successful",
  "data": {
    "status": "Connected",
    "folder_name": "Maritime Certificates V2",
    "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB",
    "timestamp": "2025-10-29T10:30:00.000Z"
  }
}
```

❌ **Lỗi khi thiếu folder_id:**
```json
{
  "success": false,
  "message": "Request failed: folder_id is required and must be a string",
  "error": "..."
}
```

---

## 🔍 Kiểm Tra Logs Trong Apps Script

Để debug khi có vấn đề:

1. Trong Apps Script Editor, click icon **Executions** (⏱️) bên trái
2. Thực hiện request (test connection, upload file, etc.)
3. Click vào execution để xem logs
4. Kiểm tra logs - sensitive data đã được mask:
   ```
   [2025-10-29 17:30:00] 📨 Incoming request | {"action":"test_connection"}
   [2025-10-29 17:30:01] 🔌 Connection test successful | {"folder_id":"1UeKVB***","folder_name":"Maritime Certificates V2"}
   [2025-10-29 17:30:01] ✅ SUCCESS: Connection successful | ...
   ```

---

## 🔐 So Sánh Bảo Mật

| Tính Năng | v2.0 (Cũ) | v3.0 (Mới) |
|-----------|-----------|-----------|
| Folder ID | ❌ Hardcoded trong script | ✅ Truyền động qua request |
| Nếu lộ URL | ⚠️ Có thể truy cập data | ✅ Không biết folder_id → an toàn |
| Logging | ⚠️ Log đầy đủ folder_id | ✅ Mask sensitive data |
| API Key | ❌ Không có | ➖ Không cần (folder_id là barrier) |
| Validation | ✅ Basic | ✅ Enhanced với permission check |

---

## 📱 Cấu Hình Trong Ứng Dụng

Sau khi deploy và test thành công:

1. Login vào ứng dụng
2. Vào **System Settings** → **Google Drive Configuration**
3. Chọn **Apps Script (Easiest)**
4. Điền:
   - **Web App URL**: URL mới từ deployment
   - **Folder ID**: `1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB`
   - **API Key**: Để trống (không cần)
5. Click **Test Connection**
6. Nếu thành công → Click **Save Configuration**

---

## ❓ Troubleshooting

### POST request trả về HTML thay vì JSON?

**Nguyên nhân**: Deployment chưa được cập nhật đúng cách

**Giải pháp**:
1. Tạo **NEW deployment** (không phải edit deployment cũ)
2. Đảm bảo chọn "Web app" làm deployment type
3. Đảm bảo "Who has access" = "Anyone"

### Error: "folder_id is required"?

**Nguyên nhân**: Request không có folder_id hoặc backend chưa được update

**Giải pháp**:
- Kiểm tra backend đã restart chưa: `sudo supervisorctl restart backend`
- Kiểm tra config trong database có folder_id chưa

### Error: "Invalid folder_id or no access permission"?

**Nguyên nhân**: 
- Folder ID sai
- Script không có quyền truy cập folder
- Account deploy script khác với account owner của folder

**Giải pháp**:
1. Kiểm tra Folder ID: https://drive.google.com/drive/folders/[FOLDER_ID]
2. Đảm bảo account deploy script có quyền truy cập folder (Owner hoặc Editor)
3. Share folder cho email account deploy script nếu cần

---

## 🎯 Next Steps

Sau khi v3.0 hoạt động thành công:

1. ✅ Test "Sync to Drive" (backup database)
2. ✅ Test "Sync from Drive" (restore database)
3. ✅ Kiểm tra auto-backup hàng ngày lúc 21:00 UTC
4. ✅ Monitor logs để đảm bảo không có thông tin nhạy cảm bị lộ

---

**Bạn đã sẵn sàng deploy chưa?** 🚀

# Hướng dẫn Setup Google Apps Script cho System Google Drive

## 📋 Tổng quan

Google Apps Script này hoạt động như một proxy giữa Ship Management System và Google Drive, cho phép:
- ✅ Backup tự động tất cả collections
- ✅ Tạo folder theo ngày (YYYY-MM-DD)
- ✅ Upload/Download files
- ✅ Restore database từ backup
- ✅ Không cần OAuth phức tạp

---

## 🚀 Bước 1: Tạo Project trong Google Apps Script

### 1.1. Truy cập Google Apps Script
1. Mở trình duyệt và truy cập: **https://script.google.com**
2. Đăng nhập bằng Google Account của bạn
3. Click nút **"New Project"** (Dự án mới)

### 1.2. Đặt tên Project
1. Click vào **"Untitled project"** ở góc trên bên trái
2. Đổi tên thành: **"Ship Management - System GDrive Proxy"**
3. Click **OK**

---

## 📁 Bước 2: Tạo Root Folder trên Google Drive

### 2.1. Tạo Folder
1. Mở Google Drive: **https://drive.google.com**
2. Click **New** > **Folder**
3. Đặt tên folder: **"Ship Management System Backups"**
4. Click **Create**

### 2.2. Lấy Folder ID
1. Mở folder vừa tạo
2. Nhìn vào URL trên thanh địa chỉ:
   ```
   https://drive.google.com/drive/folders/1abcDEFghiJKLmnopQRStuv2wxYZ
                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                          ĐÂY LÀ FOLDER ID
   ```
3. **Copy Folder ID** này (phần sau `/folders/`)
4. Ví dụ: `1abcDEFghiJKLmnopQRStuv2wxYZ`

---

## 💻 Bước 3: Paste Code vào Apps Script

### 3.1. Copy Code
1. Mở file `GOOGLE_APPS_SCRIPT_SYSTEM_GDRIVE.js` trong project của bạn
2. Copy toàn bộ code

### 3.2. Paste vào Apps Script Editor
1. Quay lại tab Google Apps Script
2. Xóa code mặc định trong file `Code.gs`
3. Paste code đã copy vào
4. Click **Save** (hoặc Ctrl+S)

### 3.3. Cập nhật ROOT_FOLDER_ID
1. Tìm dòng (dòng 32):
   ```javascript
   const ROOT_FOLDER_ID = "YOUR_ROOT_FOLDER_ID_HERE";
   ```
2. Thay `YOUR_ROOT_FOLDER_ID_HERE` bằng Folder ID đã copy ở Bước 2.2
3. Ví dụ:
   ```javascript
   const ROOT_FOLDER_ID = "1abcDEFghiJKLmnopQRStuv2wxYZ";
   ```
4. Click **Save** lại

---

## 🚀 Bước 4: Deploy Web App

### 4.1. Deploy
1. Click nút **Deploy** (góc trên bên phải)
2. Chọn **New deployment**

### 4.2. Cấu hình Deployment
1. **Description**: Nhập `Ship Management System GDrive Proxy v1.0`
2. Click biểu tượng **⚙️ (Settings)** bên cạnh "Select type"
3. Chọn **Web app**

### 4.3. Cài đặt Web App
Thiết lập các thông số sau:

**Execute as (Thực thi dưới tên):**
- Chọn: **Me** (your-email@gmail.com)

**Who has access (Ai có quyền truy cập):**
- Chọn: **Anyone** (Bất kỳ ai)

> ⚠️ **LƯU Ý QUAN TRỌNG**: 
> - Chọn "Anyone" để backend có thể gọi được
> - Apps Script sẽ chạy với quyền của tài khoản Google của bạn
> - Chỉ có backend của bạn mới biết URL này

### 4.4. Authorize
1. Click **Deploy**
2. Sẽ xuất hiện popup xin quyền truy cập
3. Click **Authorize access**
4. Chọn tài khoản Google của bạn
5. Click **Advanced** (Nâng cao)
6. Click **Go to Ship Management - System GDrive Proxy (unsafe)**
7. Click **Allow** (Cho phép)

### 4.5. Copy Web App URL
1. Sau khi deploy thành công, sẽ xuất hiện popup
2. **Copy** đường dẫn **Web app URL**
3. URL sẽ có dạng:
   ```
   https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec
   ```
4. Click **Done**

> 💡 **Tip**: Nếu bạn đóng popup mất, có thể lấy lại URL bằng cách:
> - Click **Deploy** > **Manage deployments**
> - Copy URL ở cột "Web app URL"

---

## 🧪 Bước 5: Test Apps Script

### 5.1. Test trong Browser (Đơn giản nhất)
1. Paste Web App URL vào trình duyệt
2. Bạn sẽ thấy trang web đẹp với:
   - ✅ Status: Apps Script is running
   - 📋 Configuration info
   - 🔧 Supported Actions
   - 📝 Example Request

### 5.2. Test bằng Apps Script Editor
1. Trong Apps Script Editor
2. Chọn function **`runTests`** từ dropdown (bên cạnh nút Run)
3. Click **Run** (▶️)
4. Xem kết quả trong **Execution log** (View > Logs)

### 5.3. Test bằng Postman hoặc curl
**Sử dụng curl:**
```bash
curl -X POST "YOUR_WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test_connection"
  }'
```

**Response thành công:**
```json
{
  "success": true,
  "message": "Connection successful",
  "folder_name": "Ship Management System Backups",
  "folder_id": "1abcDEFghiJKLmnopQRStuv2wxYZ",
  "folder_url": "https://drive.google.com/drive/folders/...",
  "access_time": "2025-01-29T14:30:00.000Z"
}
```

---

## ⚙️ Bước 6: Cấu hình trong Ship Management System

### 6.1. Đăng nhập vào System
1. Truy cập Ship Management System
2. Đăng nhập với tài khoản **Super Admin**

### 6.2. Mở System Settings
1. Click menu **Settings** (Cài đặt)
2. Scroll xuống phần **"Cấu hình Google Drive hệ thống"**
3. Click nút **"⚙️ Cấu hình Google Drive hệ thống"**

### 6.3. Nhập thông tin
1. Chọn tab **"Apps Script (Easiest)"**
2. Paste **Web App URL** vào ô "Google Apps Script Web App URL"
3. Paste **Folder ID** vào ô "Google Drive Folder ID"
4. Click **"Test Connection"** để kiểm tra
5. Nếu hiển thị ✅ "Apps Script proxy working!", click **"Save Configuration"**

---

## ✅ Bước 7: Kiểm tra hoạt động

### 7.1. Kiểm tra Status
- Sau khi save, bạn sẽ thấy:
  - ✅ **Trạng thái cấu hình**: Đã cấu hình
  - **Auth Method**: Apps Script
  - **Folder ID**: (folder ID của bạn)
  - **Collections trong DB**: (số collections)
  - **Backup folders trên Drive**: 0 (chưa có backup)

### 7.2. Test Backup thủ công
1. Click nút **"☁️↑ Backup lên Drive (Sync to Drive)"**
2. Đợi vài giây (tùy số lượng collections)
3. Sẽ thấy thông báo: "Backup thành công! X files đã được upload"
4. Kiểm tra Google Drive:
   - Mở folder "Ship Management System Backups"
   - Sẽ thấy folder mới theo ngày (VD: `2025-01-29`)
   - Mở folder đó, sẽ thấy các file JSON (users.json, ships.json, etc.)

### 7.3. Kiểm tra Auto-Backup
- Auto-backup sẽ tự động chạy lúc **21:00 UTC** mỗi ngày
- Kiểm tra backend logs để xem status:
  ```bash
  tail -f /var/log/supervisor/backend.*.log | grep "auto-backup"
  ```

---

## 🔧 Các Actions được hỗ trợ

### 1. test_connection
Test kết nối tới Google Drive
```json
{
  "action": "test_connection"
}
```

### 2. create_folder
Tạo folder backup theo ngày
```json
{
  "action": "create_folder",
  "parent_folder_id": "ROOT_FOLDER_ID",
  "folder_name": "2025-01-29"
}
```

### 3. upload_file
Upload file JSON backup
```json
{
  "action": "upload_file",
  "folder_id": "FOLDER_ID",
  "filename": "users.json",
  "content": "[{...}]",
  "mimeType": "application/json"
}
```

### 4. list_folders
List các backup folders
```json
{
  "action": "list_folders",
  "parent_folder_id": "ROOT_FOLDER_ID"
}
```

### 5. list_files
List files trong folder
```json
{
  "action": "list_files",
  "parent_folder_id": "ROOT_FOLDER_ID",
  "folder_name": "2025-01-29"
}
```

### 6. download_file
Download file để restore
```json
{
  "action": "download_file",
  "file_id": "FILE_ID"
}
```

### 7. delete_file
Xóa file
```json
{
  "action": "delete_file",
  "file_id": "FILE_ID"
}
```

---

## 🐛 Troubleshooting

### Lỗi: "ROOT_FOLDER_ID not configured"
- **Nguyên nhân**: Chưa update ROOT_FOLDER_ID trong code
- **Giải pháp**: Quay lại Bước 3.3, cập nhật ROOT_FOLDER_ID

### Lỗi: "Cannot access root folder"
- **Nguyên nhân**: Folder ID sai hoặc không có quyền truy cập
- **Giải pháp**: 
  - Kiểm tra lại Folder ID
  - Đảm bảo folder tồn tại trong Google Drive
  - Đảm bảo tài khoản Apps Script có quyền truy cập folder

### Lỗi: "Authorization required"
- **Nguyên nhân**: Chưa authorize Apps Script
- **Giải pháp**: Quay lại Bước 4.4, thực hiện authorize lại

### Backup không tự động chạy
- **Kiểm tra**: Backend logs có thông báo "✅ Scheduler started"
- **Kiểm tra**: Cấu hình Google Drive đã save chưa
- **Giải pháp**: Restart backend: `sudo supervisorctl restart backend`

---

## 📞 Hỗ trợ

Nếu gặp vấn đề, hãy kiểm tra:
1. ✅ ROOT_FOLDER_ID đã được cập nhật đúng
2. ✅ Apps Script đã được deploy với "Execute as: Me" và "Access: Anyone"
3. ✅ Đã authorize Apps Script với tài khoản Google
4. ✅ Test connection từ browser thành công
5. ✅ Web App URL đã được paste đúng vào System Settings

---

## 🎉 Hoàn thành!

Bây giờ bạn đã có:
- ✅ Google Apps Script proxy hoạt động
- ✅ Backup thủ công qua button
- ✅ Backup tự động lúc 21:00 hàng ngày
- ✅ Restore từ bất kỳ backup nào
- ✅ Backup tất cả collections động
- ✅ Folder riêng theo ngày

**Chúc mừng! Hệ thống backup của bạn đã sẵn sàng! 🚀**

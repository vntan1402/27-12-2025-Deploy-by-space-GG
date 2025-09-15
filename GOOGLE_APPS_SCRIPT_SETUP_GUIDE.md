# Google Apps Script Setup Guide - Ship Management System

## 🚀 Bước 1: Tạo Google Apps Script Project Mới

1. **Truy cập Google Apps Script**:
   - Vào https://script.google.com/
   - Đăng nhập bằng Google account có quyền truy cập Google Drive folder

2. **Tạo Project mới**:
   - Click "New Project"
   - Đổi tên project thành "Ship Management - Multi File Upload"

## 📝 Bước 2: Copy Code Mới

1. **Xóa code mặc định** trong file `Code.gs`

2. **Copy toàn bộ code** từ file `/app/GOOGLE_APPS_SCRIPT_FIXED_NEW.js` vào `Code.gs`

3. **Save project** (Ctrl+S)

## ⚙️ Bước 3: Deploy Web App

1. **Click Deploy** (góc trên bên phải)

2. **Chọn "New deployment"**

3. **Configuration**:
   - **Type**: Web app
   - **Description**: "Ship Management Multi-File Upload v2.0"
   - **Execute as**: Me (your email)
   - **Who has access**: Anyone (hoặc Anyone with Google account nếu cần bảo mật hơn)

4. **Click Deploy**

5. **Copy Web App URL** - URL này sẽ có dạng:
   ```
   https://script.google.com/macros/s/[SCRIPT_ID]/exec
   ```

## 🔧 Bước 4: Test Apps Script

### Test Basic Connection
```bash
curl -X POST "YOUR_NEW_WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{"action": "test_connection", "folder_id": "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG"}'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Connection successful",
  "folder_name": "Your Folder Name",
  "folder_id": "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG",
  "drive_access": true,
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### Test Folder Creation
```bash
curl -X POST "YOUR_NEW_WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{"action": "create_folder_structure", "parent_folder_id": "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG", "ship_name": "Test Ship Alpha"}'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Ship folder structure created: Test Ship Alpha", 
  "ship_folder_id": "NEW_SHIP_FOLDER_ID",
  "ship_folder_name": "Test Ship Alpha",
  "subfolder_ids": {
    "Certificates": "CERT_FOLDER_ID",
    "Test Reports": "TEST_FOLDER_ID", 
    "Survey Reports": "SURVEY_FOLDER_ID",
    "Drawings & Manuals": "DRAWING_FOLDER_ID",
    "Other Documents": "OTHER_FOLDER_ID"
  },
  "categories_created": 5,
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## 🔗 Bước 5: Cập nhật Backend Configuration

### Trong Ship Management System:

1. **Login** với admin/admin123

2. **Vào System Settings** → **Company Google Drive Configuration**

3. **Update configuration**:
   - **Authentication Method**: Apps Script Proxy
   - **Web App URL**: `YOUR_NEW_WEB_APP_URL` (từ bước 3)
   - **Folder ID**: `1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG`

4. **Test Connection** - Should show success

## ✅ Bước 6: Test Multi-File Upload

1. **Vào Add New Record** → **Certificate**

2. **Upload multiple files** using the multi-file upload section

3. **Check Google Drive**:
   - Should see new ship folder created
   - Should see 5 category subfolders
   - Files should be organized in correct categories

## 🐛 Troubleshooting

### If you get HTML response instead of JSON:
1. Make sure Web App is deployed correctly
2. Check "Execute as: Me" setting
3. Re-deploy with new version

### If folder creation fails:
1. Check Google Drive permissions
2. Verify folder ID is correct
3. Test with a simple folder first

### If file upload fails:
1. Check file size (max 150MB per file)
2. Verify base64 encoding is working
3. Check Apps Script logs in Google Apps Script editor

## 📊 Features Supported

✅ **Multi-file upload**
✅ **AI document classification** 
✅ **Auto folder structure creation**
✅ **5 category organization**
✅ **Duplicate file handling**
✅ **Error handling & logging**
✅ **JSON responses**
✅ **Legacy sync support**

## 🔄 Migration from Old Script

Sau khi deploy script mới:

1. **Test thoroughly** với một vài file
2. **Backup old script** (nếu cần)
3. **Update all configurations** với Web App URL mới
4. **Monitor logs** để đảm bảo hoạt động ổn định

---

**🎉 Congratulations!** Script mới sẽ hoạt động tốt với multi-file AI-powered document processing system!
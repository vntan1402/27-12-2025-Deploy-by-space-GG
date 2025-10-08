# BACKEND DIRECT UPLOAD SETUP GUIDE

## 🎯 Overview
Backend sẽ trực tiếp upload files lên Company Google Drive thay vì thông qua Apps Script, giải quyết vấn đề cross-account access.

## 📋 Setup Steps

### 1. Create Google Service Account
1. **Truy cập Google Cloud Console**: https://console.cloud.google.com
2. **Chọn Project** của System Account (nơi chạy Apps Script)
3. **Navigate**: IAM & Admin → Service Accounts
4. **Create Service Account**:
   - Name: `Maritime Backend Service`
   - Description: `Service account for backend file uploads to company drive`
   - Click **Create and Continue**
5. **Grant Roles**: (Optional - có thể skip)
6. **Done** → Click on created service account
7. **Keys tab** → **Add Key** → **Create New Key** → **JSON**
8. **Download** JSON key file

### 2. Share Company Google Drive
1. **Truy cập Company Google Drive** 
2. **Right-click** trên Company folder (ID: 1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG)
3. **Share** → **Add people and groups**
4. **Add service account email**:
   ```
   maritime-backend-service@[project-id].iam.gserviceaccount.com
   ```
5. **Permission**: **Editor**
6. **Send** notification (optional)

### 3. Configure Backend Environment
1. **Add Service Account JSON** to environment:
   ```bash
   # In .env file
   GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"maritime-backend-service@[project-id].iam.gserviceaccount.com",...}'
   ```

2. **Restart Backend**:
   ```bash
   sudo supervisorctl restart backend
   ```

### 4. Update Google Apps Script
1. **Replace Apps Script code** với nội dung từ `/app/DOCUMENT_AI_ONLY_APPS_SCRIPT.js`
2. **Deploy** → **New Deployment**
3. **Copy new URL** và update trong System Settings

### 5. Update Apps Script Manifest
1. **Create appsscript.json** với nội dung:
   ```json
   {
     "timeZone": "Asia/Ho_Chi_Minh",
     "dependencies": {},
     "exceptionLogging": "STACKDRIVER", 
     "runtimeVersion": "V8",
     "executionApi": {
       "access": "ANYONE"
     },
     "webapp": {
       "access": "ANYONE",
       "executeAs": "USER_DEPLOYING"
     },
     "oauthScopes": [
       "https://www.googleapis.com/auth/script.external_request",
       "https://www.googleapis.com/auth/documentai"
     ]
   }
   ```

## 🔍 Testing

### Test Service Account Connection
```python
# Test script
from backend.company_google_drive_manager import create_company_drive_manager

# Test connection
manager = create_company_drive_manager("your-company-uuid")
if manager:
    result = manager.test_connection()
    print("Connection test:", result)
```

### Test Passport Upload
1. **Login** as admin1/123456
2. **Navigate** to Add Crew → From Passport
3. **Upload** test passport file
4. **Check logs** for:
   ```
   📁 Backend uploading passport to Company Drive: BROTHER 36/Crew records
   📋 Backend uploading summary to Company Drive: SUMMARY/...
   ✅ File uploaded successfully
   ```

## 🚀 Expected Results

### Before (Apps Script Upload):
```
❌ Exception: Specified permissions are not sufficient to call DriveApp.getRootFolder
```

### After (Backend Direct Upload):
```json
{
  "success": true,
  "files": {
    "passport": {
      "file_id": "1ABC123...",
      "folder_path": "BROTHER 36/Crew records",
      "upload_method": "backend_direct_upload"
    },
    "summary": {
      "file_id": "1XYZ789...", 
      "folder_path": "SUMMARY",
      "upload_method": "backend_direct_upload"
    }
  }
}
```

## 📁 Final Folder Structure
```
Company Google Drive/
├── BROTHER 36/
│   └── Crew records/
│       └── passport_nguyen_van_a.pdf
├── MINH ANH 09/
│   └── Crew records/
│       └── passport_tran_van_b.pdf  
└── SUMMARY/
    ├── passport_nguyen_van_a_Summary.txt
    └── passport_tran_van_b_Summary.txt
```

## ⚠️ Important Notes
1. **Service Account Key** phải được bảo mật cẳn thận
2. **Company folder** phải được share với service account
3. **Apps Script** giờ chỉ xử lý Document AI, không upload file
4. **Backend logs** sẽ hiển thị "backend_direct_upload" thay vì "google_drive_maritime"

## 🔧 Troubleshooting
- **Permission denied**: Check service account có access vào company folder
- **File not found**: Verify company_folder_id trong database
- **Invalid credentials**: Check GOOGLE_SERVICE_ACCOUNT_JSON format
- **Import error**: Restart backend sau khi add environment variable
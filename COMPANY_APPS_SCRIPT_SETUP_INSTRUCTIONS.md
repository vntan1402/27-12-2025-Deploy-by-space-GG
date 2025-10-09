# Company Apps Script Setup Instructions

## 🚀 **Updated Apps Script for Passport Workflow**

### **Changes Made:**

1. **✅ Removed Apps Script Properties dependency** - Now uses `parent_folder_id` from backend Company Google Drive Configuration
2. **✅ Enhanced logging** - Detailed logs for debugging file upload process
3. **✅ Improved error handling** - Better error messages for folder and permission issues
4. **✅ Dynamic folder creation** - Supports both "Ship Name/Crew records" and "SUMMARY" folder paths

---

## 📋 **Setup Steps:**

### **Step 1: Replace Apps Script Code**
- Copy code from `/app/FINAL_COMPANY_APPS_SCRIPT_FOR_PASSPORT.js`
- Replace all code in your Company Apps Script project

### **Step 2: Configure OAuth Scopes (appsscript.json)**
```json
{
  "timeZone": "Asia/Ho_Chi_Minh",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "oauthScopes": [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file"
  ]
}
```

### **Step 3: Deploy as Web App**
1. Click **Deploy** → **New Deployment**
2. Type: **Web app**
3. Execute as: **Me**
4. Who has access: **Anyone** (for cross-account access)
5. Copy the **Web app URL**

### **Step 4: Update Backend Configuration**
Ensure your Company Google Drive Configuration in the backend has:
```json
{
  "company_id": "your_company_id",
  "company_apps_script_url": "https://script.google.com/your_web_app_url",
  "parent_folder_id": "your_company_google_drive_folder_id"
}
```

---

## 🔍 **What Backend Sends:**

For **passport file**:
```json
{
  "file_content": "base64_encoded_passport_content",
  "filename": "passport.pdf",
  "folder_path": "Ship Name/Crew records",
  "content_type": "application/pdf",
  "parent_folder_id": "company_folder_id_from_config"
}
```

For **summary file**:
```json
{
  "file_content": "base64_encoded_summary_content",
  "filename": "passport_Summary.txt",
  "folder_path": "SUMMARY",
  "content_type": "text/plain",
  "parent_folder_id": "company_folder_id_from_config"
}
```

---

## 📁 **Expected Folder Structure:**

```
Company Google Drive Folder
├── Ship Name 1/
│   └── Crew records/
│       └── passport.pdf
├── Ship Name 2/
│   └── Crew records/
│       └── another_passport.pdf
└── SUMMARY/
    ├── passport_Summary.txt
    └── another_passport_Summary.txt
```

---

## 🧪 **Testing:**

### **Test 1: Apps Script Direct Test**
```javascript
// Test in Apps Script editor
function testPassportUpload() {
  var testData = {
    filename: "test_passport.pdf",
    file_content: "base64_test_content", // Use real base64 for actual test
    folder_path: "Test Ship/Crew records",
    content_type: "application/pdf",
    parent_folder_id: "your_company_folder_id"
  };
  
  var result = handlePassportUpload(testData);
  Logger.log(result.getContentText());
}
```

### **Test 2: Backend API Test**
Use backend testing agent to test the full passport workflow.

---

## 🐛 **Debugging:**

1. **Check Apps Script Logs:**
   - Apps Script Editor → **Executions** tab
   - Look for detailed logs from `handlePassportUpload()`

2. **Common Issues:**
   - ❌ **Folder not accessible**: Check `parent_folder_id` and permissions
   - ❌ **Base64 decode error**: Check file content encoding
   - ❌ **Permission denied**: Ensure Apps Script has Drive access

3. **Backend Logs:**
   ```bash
   tail -f /var/log/supervisor/backend.*.log
   ```

---

## ✅ **Expected Success Response:**

```json
{
  "success": true,
  "message": "File uploaded successfully to Ship Name/Crew records",
  "file_id": "1ABC123...",
  "file_name": "passport.pdf",
  "file_url": "https://drive.google.com/file/d/...",
  "folder_path": "Ship Name/Crew records",
  "folder_id": "1DEF456...",
  "folder_name": "Crew records",
  "upload_timestamp": "2024-01-15T10:30:00.000Z",
  "file_size": 2048576,
  "content_type": "application/pdf",
  "service": "Company Apps Script - Passport Upload",
  "version": "v4.0-passport-optimized"
}
```

---

This updated Apps Script should resolve the file upload issue by properly receiving and using the Company Google Drive Folder ID from the backend configuration.
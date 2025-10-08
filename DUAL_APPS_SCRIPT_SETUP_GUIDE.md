# DUAL APPS SCRIPT SETUP GUIDE

## 🎯 Overview
Sử dụng 2 Apps Scripts riêng biệt:
- **System Apps Script**: Document AI processing (System Google Account)  
- **Company Apps Script**: File uploads (Company Google Account)

## 🏗️ Architecture
```
Frontend Upload → Backend → System Apps Script (Document AI)
                         ↓
                         Company Apps Script (File Upload)
                         ↓
                         Company Google Drive
```

## 📋 Setup Steps

### Step 1: Setup Company Apps Script (File Upload)
1. **Login** to Company Google Account
2. **Create** new Apps Script: https://script.google.com  
3. **Paste** code from `/app/COMPANY_FILE_UPLOAD_APPS_SCRIPT.js`
4. **Save** project as "Maritime File Upload Service"
5. **Deploy** as Web App:
   - Description: "File Upload v1.0"
   - Execute as: **Me** (Company Account)
   - Who has access: **Anyone**
6. **Copy** deployment URL
7. **Test** by visiting URL (should show service info)

### Step 2: Update Company Database Configuration
```sql
-- Add company_apps_script_url to existing configuration
UPDATE company_gdrive_config 
SET company_apps_script_url = 'https://script.google.com/macros/s/AKfyc...../exec'
WHERE company_id = 'your-company-uuid';
```

### Step 3: Update System Apps Script (Document AI Only)
1. **Login** to System Google Account
2. **Open** existing Document AI Apps Script
3. **Replace** code with `/app/DOCUMENT_AI_ONLY_APPS_SCRIPT.js`
4. **Deploy** → **New Deployment** (if needed)
5. **Update** URL in System Settings (if changed)

### Step 4: Test Dual Apps Script Setup
```bash
# Test Company Apps Script
curl -X GET "https://script.google.com/macros/s/[company-script-id]/exec"

# Expected response:
{
  "success": true,
  "message": "Company File Upload Service is WORKING!",
  "service": "Company File Upload Service v1.0",
  "account": "Company Google Account"
}

# Test System Apps Script  
curl -X GET "https://script.google.com/macros/s/[system-script-id]/exec"

# Expected response:
{
  "success": true,
  "message": "Document AI Processing Service is WORKING!",
  "service": "Document AI Processing Only v3.0"
}
```

### Step 5: Restart Backend
```bash
sudo supervisorctl restart backend
```

## 🔍 Verification Steps

### 1. Database Configuration Check
```python
# Check both URLs are configured
from mongodb_database import mongo_db

# System Apps Script URL (Document AI)
ai_config = mongo_db.find_one("ai_config", {"company_id": "your-uuid"})
system_url = ai_config["document_ai"]["apps_script_url"]
print(f"System Apps Script: {system_url}")

# Company Apps Script URL (File Upload)
gdrive_config = mongo_db.find_one("company_gdrive_config", {"company_id": "your-uuid"})
company_url = gdrive_config["company_apps_script_url"] 
print(f"Company Apps Script: {company_url}")
```

### 2. Test Passport Upload
1. **Login** as admin1/123456
2. **Navigate** to Add Crew → From Passport  
3. **Upload** test passport
4. **Check backend logs**:
   ```
   🔄 Processing passport with dual Apps Scripts: test.pdf
   📡 Step 1: Document AI analysis via System Apps Script...
   ✅ System Apps Script (Document AI) completed successfully  
   📁 Step 2: File uploads via Company Apps Script...
   📤 Uploading passport file: BROTHER 36/Crew records/test.pdf
   📋 Uploading summary file: SUMMARY/test_Summary.txt
   ✅ Dual Apps Script processing completed successfully
   ```

### 3. Verify Google Drive Files
**Company Google Drive should contain:**
```
Company Drive Root/
├── BROTHER 36/
│   └── Crew records/
│       └── test_passport.pdf        ← Real file
└── SUMMARY/  
    └── test_passport_Summary.txt    ← Real summary
```

## 🚀 Expected Results

### API Response Format:
```json
{
  "success": true,
  "analysis": {
    "full_name": "NGUYEN VAN TEST",
    "passport_number": "C1234567", 
    "date_of_birth": "15/02/1990",
    // ... other fields
  },
  "files": {
    "passport": {
      "filename": "test.pdf",
      "folder": "BROTHER 36/Crew records",
      "upload_result": {
        "success": true,
        "file_id": "1ABC123...",
        "upload_method": "company_apps_script"
      }
    },
    "summary": {
      "filename": "test_Summary.txt", 
      "folder": "SUMMARY",
      "upload_result": {
        "success": true,
        "file_id": "1XYZ789...",
        "upload_method": "company_apps_script"
      }
    }
  },
  "processing_method": "dual_apps_script",
  "workflow": "system_document_ai + company_file_upload"
}
```

## ⚠️ Troubleshooting

### Company Apps Script Issues:
- **403 Forbidden**: Check deploy settings (Execute as: Me, Access: Anyone)
- **File upload fails**: Verify Company account has Drive permissions
- **Folder creation fails**: Check Company Drive space and permissions

### System Apps Script Issues:  
- **Document AI fails**: Verify project_id, processor_id, location
- **Permission denied**: Check Document AI API is enabled

### Backend Issues:
- **URL not configured**: Check database has both Apps Script URLs
- **Import error**: Restart backend after adding dual_apps_script_manager.py
- **Timeout**: Increase timeout in aiohttp calls if needed

## 🔧 Configuration Summary

| Component | Account | Purpose | URL Location |
|-----------|---------|---------|-------------|
| **System Apps Script** | System Google | Document AI | ai_config.document_ai.apps_script_url |
| **Company Apps Script** | Company Google | File Upload | company_gdrive_config.company_apps_script_url |
| **Backend** | - | Orchestration | Calls both Apps Scripts |
| **Company Drive** | Company Google | File Storage | Receives files from Company Apps Script |

This setup provides clean separation of concerns and resolves cross-account access issues!
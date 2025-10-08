# COMPANY APPS SCRIPT UPLOAD SOLUTION

## 🎯 Concept
Sử dụng Company Apps Script hiện có (từ Company Google Drive Configuration) để upload files, thay vì tạo service account mới.

## 🏗️ Architecture
```
Frontend Upload
     ↓
Backend Processing
     ├── System Apps Script (Document AI)
     └── Company Apps Script (File Upload)
              ↓
         Company Google Drive
```

## ✅ Advantages
- ✅ Sử dụng infrastructure hiện có
- ✅ Company Apps Script đã có quyền access Company Drive  
- ✅ Không cần tạo service account
- ✅ Không cần share folder manually
- ✅ Đơn giản setup và maintain

## 📝 Implementation Plan

### 1. Company Apps Script (File Upload Only)
Tạo Apps Script trong Company Google account với chức năng upload file:

```javascript
function doPost(e) {
  return handleFileUpload(e);
}

function handleFileUpload(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    
    // Decode base64 file content
    var fileContent = Utilities.base64Decode(data.file_content);
    var blob = Utilities.newBlob(fileContent, data.content_type, data.filename);
    
    // Create folder structure
    var targetFolder = createFolderStructure(data.folder_path);
    
    // Upload file
    var file = targetFolder.createFile(blob);
    
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      file_id: file.getId(),
      filename: data.filename,
      folder_path: data.folder_path,
      upload_method: "company_apps_script"
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function createFolderStructure(folderPath) {
  var root = DriveApp.getRootFolder(); // Company's root
  var pathParts = folderPath.split('/');
  var currentFolder = root;
  
  for (var i = 0; i < pathParts.length; i++) {
    if (pathParts[i]) {
      var folders = currentFolder.getFoldersByName(pathParts[i]);
      if (folders.hasNext()) {
        currentFolder = folders.next();
      } else {
        currentFolder = currentFolder.createFolder(pathParts[i]);
      }
    }
  }
  
  return currentFolder;
}
```

### 2. Backend Dual Apps Script Calls

```python
# backend/dual_apps_script_manager.py
class DualAppsScriptManager:
    def __init__(self, company_id: str):
        self.company_id = company_id
        self.system_apps_script_url = get_system_apps_script_url()
        self.company_apps_script_url = get_company_apps_script_url(company_id)
    
    async def process_passport(self, file_content, filename, ship_name):
        # Step 1: Document AI via System Apps Script
        ai_result = await self.call_system_apps_script_for_ai(
            file_content, filename
        )
        
        # Step 2: File Upload via Company Apps Script
        upload_results = await self.upload_files_via_company_script(
            file_content, filename, ship_name, ai_result['summary']
        )
        
        return {
            'ai_analysis': ai_result,
            'file_uploads': upload_results
        }
    
    async def upload_files_via_company_script(self, file_content, filename, ship_name, summary):
        results = {}
        
        # Upload passport file
        results['passport'] = await self.call_company_apps_script({
            'file_content': base64.b64encode(file_content).decode(),
            'filename': filename,
            'folder_path': f"{ship_name}/Crew records",
            'content_type': 'application/octet-stream'
        })
        
        # Upload summary file
        summary_filename = f"{filename.rsplit('.', 1)[0]}_Summary.txt"
        results['summary'] = await self.call_company_apps_script({
            'file_content': base64.b64encode(summary.encode()).decode(),
            'filename': summary_filename,
            'folder_path': "SUMMARY",
            'content_type': 'text/plain'
        })
        
        return results
```

### 3. Database Schema Update
```python
# Add company_apps_script_url to existing company config
company_gdrive_config = {
    "company_id": "uuid",
    "folder_id": "existing_folder_id", 
    "company_apps_script_url": "https://script.google.com/macros/s/.../exec"  # NEW
}
```

## 🚀 Setup Steps

### Step 1: Create Company Apps Script
1. **Login** to Company Google Account
2. **Create** new Apps Script project: https://script.google.com
3. **Paste** Company file upload script
4. **Deploy** as Web App:
   - Execute as: **Me** 
   - Access: **Anyone**
5. **Copy** deployment URL

### Step 2: Update Company Configuration  
1. **Add Company Apps Script URL** to database:
   ```sql
   UPDATE company_gdrive_config 
   SET company_apps_script_url = 'https://script.google.com/macros/s/.../exec'
   WHERE company_id = 'company_uuid';
   ```

### Step 3: Update Backend
1. **Implement** DualAppsScriptManager
2. **Update** passport analysis endpoint
3. **Test** dual Apps Script calls

## 🔍 Testing Workflow

### Test 1: System Apps Script (Document AI)
```bash
curl -X POST $SYSTEM_APPS_SCRIPT_URL \
  -H "Content-Type: application/json" \
  -d '{"action": "analyze_passport_document_ai", "file_content": "...", ...}'
```

### Test 2: Company Apps Script (File Upload)  
```bash
curl -X POST $COMPANY_APPS_SCRIPT_URL \
  -H "Content-Type: application/json" \
  -d '{"file_content": "...", "filename": "test.pdf", "folder_path": "BROTHER 36/Crew records"}'
```

## 📊 Comparison with Other Solutions

| Solution | Complexity | Security | Maintenance |
|----------|------------|----------|-------------|
| **Company Apps Script** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Backend Service Account | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Folder Sharing | ⭐ | ⭐⭐ | ⭐⭐⭐ |

**Winner: Company Apps Script** ✅
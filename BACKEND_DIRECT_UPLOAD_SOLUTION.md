# BACKEND DIRECT UPLOAD SOLUTION

## Problem
- Apps Script (System Account) cannot access Company Google Drive
- Cross-account permission complexity

## Solution: Backend handles file upload directly

### Updated Workflow:
```
1. Frontend uploads passport → Backend
2. Backend calls Apps Script (System Account) → Document AI processing only  
3. Apps Script returns summary (no file upload)
4. Backend receives summary + uploads files to Company Drive directly
```

### Step 1: Backend Google Drive Integration
```python
# backend/google_drive_direct.py
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

class CompanyDriveManager:
    def __init__(self, service_account_file, company_folder_id):
        self.credentials = Credentials.from_service_account_file(
            service_account_file, 
            scopes=['https://www.googleapis.com/auth/drive']
        )
        self.service = build('drive', 'v3', credentials=self.credentials)
        self.company_folder_id = company_folder_id
    
    def upload_file(self, file_content, filename, folder_path):
        # Create folder structure if needed
        folder_id = self.create_folder_structure(folder_path)
        
        # Upload file
        media = MediaIoBaseUpload(
            io.BytesIO(file_content), 
            mimetype='application/octet-stream'
        )
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        file = self.service.files().create(
            body=file_metadata, 
            media_body=media
        ).execute()
        
        return file.get('id')
```

### Step 2: Update Apps Script (Document AI Only)
```javascript
// Apps Script now only handles Document AI processing
function handleAnalyzeDocument(data, documentType) {
  // Only Document AI processing
  // NO file upload functionality
  return {
    success: true,
    summary: documentSummary,
    // Remove file upload results
  };
}

// Remove handleRealFileUpload function entirely
```

### Step 3: Update Backend Workflow
```python
# server.py - Updated passport analysis
async def analyze_passport_for_crew():
    # 1. Call Apps Script for Document AI processing only
    ai_result = await call_apps_script_for_analysis(file_content, filename)
    
    # 2. Backend handles file uploads directly
    company_drive = CompanyDriveManager(service_account_file, company_folder_id)
    
    # 3. Upload passport file
    passport_file_id = company_drive.upload_file(
        file_content, filename, f"{ship_name}/Crew records"
    )
    
    # 4. Upload summary file  
    summary_file_id = company_drive.upload_file(
        summary_content, f"{filename}_Summary.txt", "SUMMARY"
    )
```

## Pros:
✅ Simpler Apps Script (only Document AI)
✅ Backend controls file upload
✅ Better error handling
✅ No cross-account Apps Script issues

## Cons:
❌ Backend needs Google Drive credentials
❌ More backend complexity
❌ Need service account setup
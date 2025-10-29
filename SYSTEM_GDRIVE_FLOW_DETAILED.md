# 🔄 System Google Drive Configuration - Flow Chi Tiết

## 📊 Overview Architecture

```
Frontend (React)
    ↓ HTTP Request
Backend (FastAPI)
    ↓ HTTP POST to Apps Script
Google Apps Script
    ↓ Google Drive API
Google Drive (Cloud Storage)
```

---

## 🎯 FLOW 1: TEST CONNECTION

### Bước 1: User Action (Frontend)

**Location**: `/app/frontend/src/components/SystemSettings/SystemGoogleDrive/SystemGoogleDriveModal.jsx`

**User clicks**: "Test Connection" button

**Trigger function**: `handleAppsScriptTest()`

```javascript
const handleAppsScriptTest = async () => {
  // 1. Validate inputs
  if (!config.web_app_url || !config.folder_id) {
    toast.error('Please fill in Web App URL and Folder ID');
    return;
  }

  // 2. Prepare payload
  const payload = {
    web_app_url: config.web_app_url,
    folder_id: config.folder_id
  };
  
  // 3. Add API key if provided (optional in v3.0)
  if (config.api_key) {
    payload.api_key = config.api_key;
  }
  
  // 4. Call backend API
  const response = await axios.post(
    `${REACT_APP_BACKEND_URL}/api/gdrive/configure-proxy`, 
    payload
  );
  
  // 5. Handle response
  if (response.data.success) {
    toast.success('Apps Script proxy working!');
  } else {
    toast.error('Apps Script proxy error');
  }
}
```

**Payload Example**:
```json
{
  "web_app_url": "https://script.google.com/macros/s/AKfycbz.../exec",
  "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
}
```

---

### Bước 2: Backend Receives Request

**Location**: `/app/backend/server.py` - Line 13650

**Endpoint**: `POST /api/gdrive/configure-proxy`

**Permission**: All authenticated users (updated from admin-only)

```python
@api_router.post("/gdrive/configure-proxy")
async def configure_google_drive_proxy(
    config_data: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    # 1. Extract data from request
    web_app_url = config_data.get("web_app_url")
    folder_id = config_data.get("folder_id")
    api_key = config_data.get("api_key")  # Optional
    
    # 2. Validate required fields
    if not web_app_url or not folder_id:
        raise HTTPException(
            status_code=400, 
            detail="web_app_url and folder_id are required"
        )
    
    # 3. Prepare test payload for Apps Script
    test_payload = {
        "action": "test_connection",
        "folder_id": folder_id
    }
    
    # 4. Add API key if provided
    if api_key:
        test_payload["api_key"] = api_key
    
    # 5. Send POST request to Apps Script
    response = requests.post(
        web_app_url, 
        json=test_payload, 
        timeout=30
    )
    
    # 6. Check HTTP status
    if response.status_code != 200:
        return {
            "success": False,
            "message": f"Apps Script test failed with status {response.status_code}",
            "error": f"HTTP {response.status_code}"
        }
    
    # 7. Parse JSON response
    result = response.json()
    
    # 8. If successful, save to database
    if result.get("success"):
        config_update = {
            "web_app_url": web_app_url,
            "folder_id": folder_id,
            "auth_method": "apps_script",
            "last_tested": datetime.now(timezone.utc).isoformat(),
            "test_result": "success"
        }
        
        await mongo_db.update(
            "gdrive_config",
            {"id": "system_gdrive"},
            config_update,
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Google Drive configuration successful!",
            "folder_name": result.get("data", {}).get("folder_name"),
            "folder_id": folder_id
        }
    else:
        return {
            "success": False,
            "message": f"Apps Script test failed: {result.get('message')}",
            "error": result.get("error")
        }
```

**Request to Apps Script**:
```json
{
  "action": "test_connection",
  "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
}
```

---

### Bước 3: Apps Script Processes Request

**Location**: `/app/GOOGLE_APPS_SCRIPT_V3_SECURE.js`

**Function**: `doPost(e)` → `testConnection()`

```javascript
// Main handler
function doPost(e) {
  try {
    // 1. Parse incoming JSON
    const payload = JSON.parse(e.postData.contents);
    const { action } = payload;
    
    // 2. Log request (with masked sensitive data)
    log(`📨 Incoming request`, { action: action });
    
    // 3. Route to appropriate function
    switch (action) {
      case 'test_connection':
        return successResponse(
          'Connection successful', 
          testConnection(payload)
        );
      
      // ... other actions
    }
  } catch (error) {
    return errorResponse('Request failed: ' + error.message, error);
  }
}

// Test connection function
function testConnection({ folder_id }) {
  // 1. Validate folder_id is provided
  const folder = validateFolderId(folder_id);
  
  // 2. Log success (with masked folder_id)
  log('🔌 Connection test successful', {
    folder_id: maskSensitiveData(folder_id),
    folder_name: folder.getName()
  });
  
  // 3. Return result
  return {
    status: 'Connected',
    folder_name: folder.getName(),
    folder_id: folder_id,
    timestamp: new Date().toISOString()
  };
}

// Validation function
function validateFolderId(folderId) {
  if (!folderId || typeof folderId !== 'string') {
    throw new Error('folder_id is required and must be a string');
  }
  
  // Try to access the folder
  try {
    const folder = DriveApp.getFolderById(folderId);
    return folder;  // ✅ Has access
  } catch (e) {
    throw new Error('Invalid folder_id or no access permission');
  }
}
```

**Apps Script Response**:
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

---

### Bước 4: Backend Returns to Frontend

Backend nhận response từ Apps Script và forward về Frontend:

```json
{
  "success": true,
  "message": "Google Drive configuration successful!",
  "folder_name": "Maritime Certificates V2",
  "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB",
  "test_result": "PASSED",
  "configuration_saved": true
}
```

---

### Bước 5: Frontend Displays Result

```javascript
// In handleAppsScriptTest()
if (response.data.success) {
  toast.success('Apps Script proxy working!');
  // Optionally display folder name
  console.log('Connected to folder:', response.data.folder_name);
} else {
  toast.error('Apps Script proxy error');
}
```

---

## 🎯 FLOW 2: SYNC TO DRIVE (BACKUP)

### Overview
```
Frontend → Backend → Apps Script → Google Drive
         ↓
    [Daily Folder Creation]
         ↓
    [Upload Each Collection as JSON]
         ↓
    [Update Last Sync Timestamp]
```

### Bước 1: User Clicks "Sync to Drive"

**Frontend**: `SystemGoogleDrive.jsx`

```javascript
const handleSyncToDrive = async () => {
  const response = await axios.post(
    `${REACT_APP_BACKEND_URL}/api/gdrive/sync-to-drive`
  );
  
  if (response.data.success) {
    toast.success(
      `Backup completed! ${response.data.files_uploaded} files uploaded`
    );
  }
}
```

---

### Bước 2: Backend Creates Daily Folder

**Backend**: `server.py` - Line 13364

```python
@api_router.post("/gdrive/sync-to-drive")
async def sync_to_drive(
    current_user: UserResponse = Depends(
        check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN])
    )
):
    # 1. Get configuration
    config = await mongo_db.find_one("gdrive_config", {"id": "system_gdrive"})
    web_app_url = config.get("web_app_url")
    
    # 2. Get current date for folder name
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Example: "2025-10-29"
    
    # 3. Create daily folder via Apps Script
    create_folder_payload = {
        "action": "create_folder",
        "parent_id": config.get("folder_id"),  # Root folder
        "folder_name": today
    }
    
    folder_response = requests.post(
        web_app_url, 
        json=create_folder_payload, 
        timeout=30
    )
    
    folder_result = folder_response.json()
    daily_folder_id = folder_result.get("data", {}).get("id")
    
    # Now we have the daily folder ID to upload files into
```

---

### Bước 3: Apps Script Creates Folder

```javascript
function createFolder({ folder_name, parent_id }) {
  // 1. Validate parent folder
  const parentFolder = validateFolderId(parent_id);
  
  // 2. Check if folder already exists
  const existingFolders = parentFolder.getFoldersByName(folder_name);
  if (existingFolders.hasNext()) {
    const folder = existingFolders.next();
    return folder;  // Return existing folder
  }
  
  // 3. Create new folder
  const folder = parentFolder.createFolder(folder_name);
  log('📁 Created new folder', { name: folder_name });
  
  return folder;
}
```

**Google Drive Structure**:
```
Maritime Certificates V2/
  └── 2025-10-29/          ← Daily folder created
      ├── users.json       ← Will be uploaded next
      ├── ships.json
      ├── companies.json
      └── certificates.json
```

---

### Bước 4: Backend Uploads Each Collection

```python
# Get ALL collections from database
all_collections = await mongo_db.list_collections()
# Example: ['users', 'ships', 'companies', 'certificates', ...]

files_uploaded = 0
upload_details = []

for collection_name in all_collections:
    # Skip system collections
    if collection_name.startswith('system.'):
        continue
    
    # 1. Get data from collection
    data = await mongo_db.find_all(collection_name, {})
    if not data:
        continue  # Skip empty collections
    
    # 2. Convert to JSON string
    json_data = json.dumps(data, default=str, indent=2)
    
    # 3. Upload to Google Drive via Apps Script
    payload = {
        "action": "upload_file",
        "folder_id": daily_folder_id,  # Upload into daily folder
        "filename": f"{collection_name}.json",
        "content": json_data,
        "mimeType": "application/json"
    }
    
    response = requests.post(web_app_url, json=payload, timeout=60)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            files_uploaded += 1
            upload_details.append({
                "collection": collection_name,
                "status": "uploaded",
                "records": len(data)
            })
```

---

### Bước 5: Apps Script Uploads File

```javascript
function uploadFile({ folder_id, filename, content, mimeType }) {
  // 1. Validate folder
  const folder = validateFolderId(folder_id);
  
  // 2. Create blob and upload
  const blob = Utilities.newBlob(content, mimeType, filename);
  const file = folder.createFile(blob);
  
  // 3. Log (with masked IDs and content size)
  log('⬆️ Uploaded file', { 
    name: filename, 
    size: content.length,
    mimeType: mimeType
  });
  
  return file;
}
```

---

### Bước 6: Update Last Sync Timestamp

```python
# After all files uploaded
await mongo_db.update(
    "gdrive_config",
    {"id": "system_gdrive"},
    {
        "last_sync": datetime.now(timezone.utc),
        "last_backup_folder": today,
        "last_backup_folder_id": daily_folder_id
    }
)

return {
    "success": True,
    "message": f"Backup completed. {files_uploaded} collections uploaded",
    "files_uploaded": files_uploaded,
    "backup_folder": today,
    "upload_details": upload_details
}
```

---

## 🎯 FLOW 3: SYNC FROM DRIVE (RESTORE)

### Overview
```
Frontend → Backend → Apps Script
         ↓
    [List files in backup folder]
         ↓
    [Download each JSON file]
         ↓
    [Restore to MongoDB collections]
```

### Bước 1: User Clicks "Sync from Drive"

```javascript
const handleSyncFromDrive = async () => {
  const response = await axios.post(
    `${REACT_APP_BACKEND_URL}/api/gdrive/sync-from-drive`,
    { folder_date: "2025-10-29" }  // Optional: specific date
  );
  
  if (response.data.success) {
    toast.success(
      `Restore completed! ${response.data.files_restored} collections restored`
    );
  }
}
```

---

### Bước 2: Backend Lists Files in Backup Folder

```python
@api_router.post("/gdrive/sync-from-drive")
async def sync_from_drive(
    folder_date: str = None,
    current_user: UserResponse = Depends(
        check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN])
    )
):
    # 1. Get configuration
    config = await mongo_db.find_one("gdrive_config", {"id": "system_gdrive"})
    
    # 2. Use specified folder or last backup folder
    if not folder_date:
        folder_date = config.get("last_backup_folder")
        # Example: "2025-10-29"
    
    # 3. List files in the backup folder
    list_payload = {
        "action": "list_files",
        "parent_folder_id": config.get("folder_id"),
        "folder_name": folder_date
    }
    
    list_response = requests.post(web_app_url, json=list_payload, timeout=30)
    list_result = list_response.json()
    
    files = list_result.get("data", [])
    # Example: [
    #   {"id": "1abc...", "name": "users.json"},
    #   {"id": "1def...", "name": "ships.json"},
    #   ...
    # ]
```

---

### Bước 3: Apps Script Lists Files

```javascript
function listFiles({ folder_id, parent_folder_id, folder_name }) {
  let folder;
  
  // Case 1: Direct folder_id
  if (folder_id) {
    folder = validateFolderId(folder_id);
  }
  // Case 2: Parent + subfolder name (for restore)
  else if (parent_folder_id && folder_name) {
    const parentFolder = validateFolderId(parent_folder_id);
    const subfolders = parentFolder.getFoldersByName(folder_name);
    
    if (!subfolders.hasNext()) {
      throw new Error(`Subfolder '${folder_name}' not found`);
    }
    
    folder = subfolders.next();
  }
  
  // Get all files in folder
  const files = folder.getFiles();
  const list = [];
  
  while (files.hasNext()) {
    const f = files.next();
    list.push({
      id: f.getId(),
      name: f.getName(),
      mimeType: f.getMimeType(),
      size: f.getSize()
    });
  }
  
  return list;
}
```

---

### Bước 4: Backend Downloads and Restores Each File

```python
files_restored = 0
restore_details = []

for file_info in files:
    filename = file_info.get("name")
    file_id = file_info.get("id")
    
    if not filename.endswith(".json"):
        continue
    
    collection_name = filename.replace(".json", "")
    
    # 1. Download file content via Apps Script
    download_payload = {
        "action": "download_file",
        "file_id": file_id
    }
    
    download_response = requests.post(
        web_app_url, 
        json=download_payload, 
        timeout=60
    )
    
    download_result = download_response.json()
    content = download_result.get("data", {}).get("content")
    
    # 2. Parse JSON content
    data = json.loads(content)
    
    # 3. Clear existing collection
    await mongo_db.delete_many(collection_name, {})
    
    # 4. Insert backup data
    if data:
        await mongo_db.insert_many(collection_name, data)
        files_restored += 1
        
        restore_details.append({
            "collection": collection_name,
            "status": "restored",
            "records": len(data)
        })

return {
    "success": True,
    "message": f"Restore completed. {files_restored} collections restored",
    "files_restored": files_restored,
    "restore_details": restore_details
}
```

---

### Bước 5: Apps Script Downloads File

```javascript
function downloadFile({ file_id }) {
  // 1. Validate file_id
  if (!file_id) {
    throw new Error('file_id is required');
  }
  
  try {
    // 2. Get file from Drive
    const file = DriveApp.getFileById(file_id);
    const content = file.getBlob().getDataAsString();
    
    // 3. Log (with masked ID and size)
    log('⬇️ Downloaded file', { 
      name: file.getName(), 
      size: content.length
    });
    
    // 4. Return file data
    return { 
      name: file.getName(), 
      content,  // Full JSON content
      mimeType: file.getMimeType() 
    };
  } catch (e) {
    throw new Error('Invalid file_id or no access permission');
  }
}
```

---

## 🎯 FLOW 4: AUTO BACKUP (Daily at 21:00 UTC)

### Backend Scheduler Setup

**Location**: `server.py` - Application Startup

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def auto_backup_task():
    """Automated daily backup to Google Drive"""
    try:
        logger.info("🔄 Starting automated backup to Google Drive...")
        
        # Get configuration
        config = await mongo_db.find_one("gdrive_config", {"id": "system_gdrive"})
        
        if not config or not config.get("web_app_url"):
            logger.warning("⚠️ Auto-backup skipped: Google Drive not configured")
            return
        
        # Call sync_to_drive logic
        # (same as manual sync, but triggered automatically)
        
        logger.info("✅ Automated backup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Auto-backup failed: {e}")

# Schedule daily backup at 21:00 UTC
scheduler.add_job(
    auto_backup_task,
    trigger='cron',
    hour=21,
    minute=0,
    timezone='UTC',
    id='daily_backup',
    replace_existing=True
)

scheduler.start()
logger.info("✅ Scheduler started - Auto-backup will run daily at 21:00 UTC")
```

---

## 📊 Data Flow Summary

### Test Connection Flow
```
User Input (URL + Folder ID)
    ↓ Frontend validation
Frontend POST /api/gdrive/configure-proxy
    ↓ JWT authentication
Backend validates & forwards
    ↓ POST to Apps Script
Apps Script validates folder access
    ↓ DriveApp.getFolderById()
Google Drive returns folder info
    ↓ JSON response
Apps Script formats response
    ↓ JSON response
Backend saves config & forwards
    ↓ JSON response
Frontend displays success message
```

### Backup Flow
```
User clicks "Sync to Drive"
    ↓
Backend gets all collections
    ↓ For each collection:
    ├─ Create daily folder (2025-10-29)
    ├─ Convert data to JSON
    ├─ Upload users.json
    ├─ Upload ships.json
    ├─ Upload companies.json
    └─ ... (all collections)
    ↓
Update last_sync timestamp
    ↓
Return summary to frontend
```

### Restore Flow
```
User clicks "Sync from Drive"
    ↓
Backend lists files in backup folder
    ↓ For each .json file:
    ├─ Download users.json
    ├─ Parse JSON content
    ├─ Clear existing collection
    ├─ Insert backup data
    └─ ... (all files)
    ↓
Return summary to frontend
```

---

## 🔒 Security Flow

### API Key (Optional in v3.0)
```
Frontend sends api_key (if configured)
    ↓
Backend forwards api_key to Apps Script
    ↓
Apps Script validates:
    ├─ if (payload.api_key !== EXPECTED_API_KEY)
    └─ throw Error('Invalid API key')
```

### Folder ID Validation
```
Every request includes folder_id
    ↓
Apps Script validates:
    ├─ DriveApp.getFolderById(folder_id)
    ├─ If folder not found → Error
    └─ If no access → Error
```

### Safe Logging
```
Before logging:
    folder_id: "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
    ↓ maskSensitiveData()
After logging:
    folder_id: "1UeKVB***"
```

---

## 🎯 Error Handling Flow

### Frontend Error
```javascript
try {
  await axios.post('/api/gdrive/configure-proxy', payload);
  toast.success('Connection successful!');
} catch (error) {
  if (error.response?.status === 403) {
    toast.error('Permission denied. Please login with admin account.');
  } else if (error.response?.status === 400) {
    toast.error('Invalid configuration. Please check your inputs.');
  } else {
    toast.error('Connection failed. Please try again.');
  }
}
```

### Backend Error
```python
try:
    response = requests.post(web_app_url, json=test_payload, timeout=30)
    return response.json()
except requests.exceptions.Timeout:
    return {
        "success": False,
        "message": "Apps Script request timed out",
        "error": "Request timeout after 30 seconds"
    }
except Exception as e:
    logger.error(f"Error: {e}")
    return {
        "success": False,
        "message": f"Configuration failed: {str(e)}"
    }
```

### Apps Script Error
```javascript
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    // ... process request
    return successResponse('Success', data);
  } catch (error) {
    return errorResponse('Request failed: ' + error.message, error);
  }
}
```

---

## ✅ Success Criteria

**Test Connection**:
- ✅ Apps Script URL accessible
- ✅ Folder ID valid and has access
- ✅ Response JSON with success=true
- ✅ Folder name displayed

**Backup**:
- ✅ Daily folder created (YYYY-MM-DD)
- ✅ All collections exported as JSON
- ✅ Files uploaded successfully
- ✅ Last sync timestamp updated

**Restore**:
- ✅ Backup folder found
- ✅ Files listed correctly
- ✅ JSON files downloaded
- ✅ Collections restored with correct data

---

**Flow documentation hoàn tất!** 🎉

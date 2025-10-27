# 🚨 GOOGLE APPS SCRIPT UPDATE REQUIRED

## Current Status
✅ **Backend & Frontend**: Hoàn tất implementation
❌ **Google Apps Script**: Cần cập nhật để hỗ trợ folder upload

## Why Apps Script Update is Needed

Tính năng "Folder Upload" cho Other Documents yêu cầu 2 actions mới trong Google Apps Script:
1. `create_subfolder` - Tạo subfolder trong "Other Documents"
2. `upload_to_folder` - Upload file vào folder cụ thể

**Hiện tại Apps Script của bạn chỉ hỗ trợ:**
- `upload_file_with_folder_creation` - Upload file vào category folder

## Required Apps Script Changes

### 1. Add `create_subfolder` Action

**Purpose**: Tạo subfolder bên trong "Other Documents" folder

**Request Format:**
```javascript
{
  "action": "create_subfolder",
  "parent_folder_id": "ROOT_FOLDER_ID",
  "ship_name": "BROTHER 36",
  "parent_category": "Class & Flag Cert",
  "category": "Other Documents",
  "subfolder_name": "Radio Report"  // Tên subfolder cần tạo
}
```

**Expected Response:**
```javascript
{
  "success": true,
  "folder_id": "1abc123xyz",  // Google Drive folder ID của subfolder mới
  "message": "Subfolder created successfully"
}
```

**Implementation Logic:**
1. Navigate to: ROOT → Ship Folder (e.g., "BROTHER 36") → "Class & Flag Cert" → "Other Documents"
2. Check if subfolder "Radio Report" already exists
   - If exists: Return existing folder_id
   - If not exists: Create new subfolder
3. Return folder_id

---

### 2. Add `upload_to_folder` Action

**Purpose**: Upload file trực tiếp vào folder ID cụ thể (không cần navigate folder path)

**Request Format:**
```javascript
{
  "action": "upload_to_folder",
  "folder_id": "1abc123xyz",  // Folder ID from create_subfolder response
  "filename": "report_001.pdf",
  "file_content": "base64_encoded_file_content",
  "content_type": "application/pdf"
}
```

**Expected Response:**
```javascript
{
  "success": true,
  "file_id": "1xyz789abc",  // Google Drive file ID
  "message": "File uploaded successfully"
}
```

**Implementation Logic:**
1. Decode base64 file_content
2. Create file blob
3. Upload directly to specified folder_id
4. Return file_id

---

## Sample Apps Script Code

### Handle `create_subfolder` Action

```javascript
function handleCreateSubfolder(data) {
  try {
    var parentFolderId = data.parent_folder_id;
    var shipName = data.ship_name;
    var parentCategory = data.parent_category;
    var category = data.category;
    var subfolderName = data.subfolder_name;
    
    // Navigate to category folder: ROOT → Ship → Parent Category → Category
    var rootFolder = DriveApp.getFolderById(parentFolderId);
    
    // Find or create ship folder
    var shipFolder = findOrCreateFolder(rootFolder, shipName);
    
    // Find or create parent category folder (e.g., "Class & Flag Cert")
    var parentCategoryFolder = findOrCreateFolder(shipFolder, parentCategory);
    
    // Find or create category folder (e.g., "Other Documents")
    var categoryFolder = findOrCreateFolder(parentCategoryFolder, category);
    
    // Find or create subfolder (e.g., "Radio Report")
    var subfolder = findOrCreateFolder(categoryFolder, subfolderName);
    
    return {
      success: true,
      folder_id: subfolder.getId(),
      message: "Subfolder created successfully"
    };
    
  } catch (error) {
    return {
      success: false,
      message: "Failed to create subfolder: " + error.toString()
    };
  }
}

function findOrCreateFolder(parentFolder, folderName) {
  var folders = parentFolder.getFoldersByName(folderName);
  if (folders.hasNext()) {
    return folders.next();
  } else {
    return parentFolder.createFolder(folderName);
  }
}
```

### Handle `upload_to_folder` Action

```javascript
function handleUploadToFolder(data) {
  try {
    var folderId = data.folder_id;
    var filename = data.filename;
    var fileContent = data.file_content;
    var contentType = data.content_type;
    
    // Decode base64 file content
    var decodedContent = Utilities.base64Decode(fileContent);
    var blob = Utilities.newBlob(decodedContent, contentType, filename);
    
    // Get folder and upload file
    var folder = DriveApp.getFolderById(folderId);
    var file = folder.createFile(blob);
    
    return {
      success: true,
      file_id: file.getId(),
      message: "File uploaded successfully"
    };
    
  } catch (error) {
    return {
      success: false,
      message: "Failed to upload file: " + error.toString()
    };
  }
}
```

### Update Main doPost Function

```javascript
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var action = data.action;
    
    // Existing actions
    if (action === "upload_file_with_folder_creation") {
      return ContentService.createTextOutput(
        JSON.stringify(handleUploadFileWithFolderCreation(data))
      ).setMimeType(ContentService.MimeType.JSON);
    }
    
    // NEW: Handle create_subfolder
    if (action === "create_subfolder") {
      return ContentService.createTextOutput(
        JSON.stringify(handleCreateSubfolder(data))
      ).setMimeType(ContentService.MimeType.JSON);
    }
    
    // NEW: Handle upload_to_folder
    if (action === "upload_to_folder") {
      return ContentService.createTextOutput(
        JSON.stringify(handleUploadToFolder(data))
      ).setMimeType(ContentService.MimeType.JSON);
    }
    
    return ContentService.createTextOutput(
      JSON.stringify({ success: false, message: "Unknown action: " + action })
    ).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({ success: false, message: error.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}
```

---

## Testing Apps Script Changes

### Test 1: Create Subfolder

**Request:**
```bash
curl -X POST "YOUR_APPS_SCRIPT_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create_subfolder",
    "parent_folder_id": "YOUR_ROOT_FOLDER_ID",
    "ship_name": "BROTHER 36",
    "parent_category": "Class & Flag Cert",
    "category": "Other Documents",
    "subfolder_name": "Test Subfolder"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "folder_id": "1abc123xyz",
  "message": "Subfolder created successfully"
}
```

### Test 2: Upload to Folder

**Request:**
```bash
curl -X POST "YOUR_APPS_SCRIPT_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "upload_to_folder",
    "folder_id": "1abc123xyz",
    "filename": "test.txt",
    "file_content": "SGVsbG8gV29ybGQ=",
    "content_type": "text/plain"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "file_id": "1xyz789abc",
  "message": "File uploaded successfully"
}
```

---

## What Happens After Apps Script Update

### 1. Folder Upload Workflow Will Work

**User Action:**
1. Select ship "BROTHER 36"
2. Click "Add Document" → "Upload Folder"
3. Select folder "Radio Report" with multiple files
4. Submit

**System Behavior:**
1. ✅ Backend calls Apps Script `create_subfolder`
2. ✅ Subfolder created: `BROTHER 36/Class & Flag Cert/Other Documents/Radio Report`
3. ✅ Backend calls Apps Script `upload_to_folder` for each file
4. ✅ All files uploaded to "Radio Report" subfolder
5. ✅ Database record created with folder_id and folder_link
6. ✅ User sees 📁 icon to open folder on Drive

### 2. Backward Compatibility

**Single File Upload** (existing functionality) will continue to work:
- Uses existing `upload_file_with_folder_creation` action
- No changes needed

---

## Deployment Steps

1. **Open your Company Apps Script**
   - Go to: https://script.google.com
   - Open your existing Apps Script project

2. **Add New Functions**
   - Copy `handleCreateSubfolder()` function
   - Copy `handleUploadToFolder()` function
   - Copy `findOrCreateFolder()` helper function

3. **Update doPost() Function**
   - Add the two new action handlers (`create_subfolder` and `upload_to_folder`)

4. **Deploy New Version**
   - Click "Deploy" → "New deployment"
   - Select "Web app"
   - Execute as: "Me"
   - Who has access: "Anyone"
   - Click "Deploy"

5. **Update Backend Configuration** (if Apps Script URL changed)
   - Login to Ship Management System
   - Go to Settings → Company Google Drive
   - Update Apps Script URL if needed

6. **Test**
   - Try uploading a folder in "Other Documents"
   - Verify subfolder is created on Google Drive
   - Verify all files are uploaded
   - Verify 📁 icon appears and opens folder

---

## Troubleshooting

### Issue: Subfolder not created

**Check:**
- Apps Script has `handleCreateSubfolder` function
- `doPost` correctly routes to `create_subfolder` action
- Apps Script has permissions to create folders
- Check Apps Script execution logs

**Debug:**
```javascript
// Add logging in handleCreateSubfolder
Logger.log("Creating subfolder: " + subfolderName);
Logger.log("In folder: " + categoryFolder.getName());
```

### Issue: File upload fails

**Check:**
- Apps Script has `handleUploadToFolder` function
- `doPost` correctly routes to `upload_to_folder` action
- folder_id is valid and accessible
- File content is properly base64 encoded

**Debug:**
```javascript
// Add logging in handleUploadToFolder
Logger.log("Uploading to folder ID: " + folderId);
Logger.log("Filename: " + filename);
Logger.log("Content type: " + contentType);
```

### Issue: Backend shows error

**Check backend logs:**
```bash
tail -f /var/log/supervisor/backend.err.log | grep "other-documents"
```

**Common errors:**
- "Company Apps Script URL not configured" → Update settings
- "Apps Script call failed" → Check Apps Script is deployed and accessible
- "Subfolder creation failed" → Check Apps Script response format

---

## Current System Status

✅ **Backend Ready**: All endpoints and logic implemented
✅ **Frontend Ready**: UI and upload flow implemented
✅ **Database Schema**: Updated with folder_id and folder_link fields
❌ **Apps Script**: Needs update (this document)

**Once Apps Script is updated, the folder upload feature will work completely!** 🎉

# Other Documents Folder Upload Feature

## Overview
This feature allows users to upload entire folders (e.g., "Radio Report") to the "Other Documents" section. The system creates a subfolder on Google Drive, uploads all files into it, and stores the folder link for easy access.

## Key Features

### 1. Folder Creation on Google Drive
- When uploading a folder, the system creates a subfolder under: `SHIP_NAME/Class & Flag Cert/Other Documents/[Folder Name]`
- Example: `BROTHER 36/Class & Flag Cert/Other Documents/Radio Report`

### 2. Multiple File Upload
- All files from the selected folder are uploaded to the created subfolder
- Supports PDF, JPG, JPEG, and other file types
- Progress tracking for each file during upload

### 3. Database Storage
- **folder_id**: Google Drive folder ID
- **folder_link**: Direct link to open folder in Google Drive (format: `https://drive.google.com/drive/folders/{folder_id}`)
- **file_ids**: Array of all uploaded file IDs
- **document_name**: Folder name (e.g., "Radio Report")

### 4. UI Enhancements
- **Folder Icon (📁)**: Displayed next to document name for folder uploads
  - Yellow color to distinguish from file uploads
  - Clicking opens the Google Drive folder in a new tab
- **File Icon (📄)**: Displayed for single file uploads
  - Blue color
  - Clicking opens the individual file in Google Drive

## Implementation Details

### Backend Changes

#### 1. Updated Pydantic Models (`server.py`)
```python
class OtherDocumentCreate(OtherDocumentBase):
    file_ids: Optional[List[str]] = None
    folder_id: Optional[str] = None  # NEW
    folder_link: Optional[str] = None  # NEW

class OtherDocumentResponse(BaseModel):
    # ... existing fields
    folder_id: Optional[str] = None  # NEW
    folder_link: Optional[str] = None  # NEW
```

#### 2. New DualAppsScriptManager Methods (`dual_apps_script_manager.py`)

**`upload_other_document_folder(files, folder_name, ship_name)`**
- Creates subfolder on Google Drive
- Uploads all files to the subfolder
- Returns folder_id, folder_link, and file_ids

**`_create_other_documents_subfolder(folder_name, ship_name)`**
- Calls Apps Script with action: `create_subfolder`
- Generates Google Drive folder link

**`_upload_file_to_folder(file_content, filename, content_type, folder_id)`**
- Uploads file directly to specified folder_id
- Calls Apps Script with action: `upload_to_folder`

#### 3. New API Endpoint (`server.py`)
```
POST /api/other-documents/upload-folder
- Parameters: files[], ship_id, folder_name, date, status, note
- Creates subfolder and uploads all files
- Returns folder_id, folder_link, file_ids
```

### Frontend Changes

#### 1. Updated Upload Logic (`App.js`)
- `handleFolderUpload()`: Rewritten to call new `/upload-folder` endpoint
- Sends all files in one request instead of individual uploads
- Displays progress for each file

#### 2. Table Display Enhancement
- Shows **folder icon (📁)** for folder uploads (when `folder_link` exists)
- Shows **file icon (📄)** for single file uploads (when `folder_link` doesn't exist)
- Clicking folder icon opens Google Drive folder
- Clicking file icon opens individual file

## Google Apps Script Requirements

The Company Apps Script must support these actions:

### 1. `create_subfolder`
```javascript
{
  "action": "create_subfolder",
  "parent_folder_id": "ROOT_FOLDER_ID",
  "ship_name": "BROTHER 36",
  "parent_category": "Class & Flag Cert",
  "category": "Other Documents",
  "subfolder_name": "Radio Report"
}
```
**Response:**
```javascript
{
  "success": true,
  "folder_id": "1xxxxxxxxxxxxx",
  "message": "Subfolder created successfully"
}
```

### 2. `upload_to_folder`
```javascript
{
  "action": "upload_to_folder",
  "folder_id": "1xxxxxxxxxxxxx",
  "filename": "report_001.pdf",
  "file_content": "base64_encoded_content",
  "content_type": "application/pdf"
}
```
**Response:**
```javascript
{
  "success": true,
  "file_id": "1yyyyyyyyyyyyyy",
  "message": "File uploaded successfully"
}
```

## User Workflow

### Uploading a Folder

1. **Select Ship**: Choose ship from dropdown
2. **Click "Add Document"**: Opens upload modal
3. **Select "Upload Folder"**: Click folder upload button
4. **Choose Folder**: Select folder from computer (e.g., "Radio Report")
5. **Auto-populate Name**: Document Name auto-fills with folder name
6. **Fill Optional Fields**: Date, Status, Note
7. **Submit**: Click submit to start upload

### Upload Process

1. System creates subfolder on Google Drive: `SHIP_NAME/Class & Flag Cert/Other Documents/Radio Report`
2. All files are uploaded to this subfolder
3. Progress shown for each file
4. Single record created in database with:
   - Document Name: "Radio Report"
   - folder_id: Google Drive folder ID
   - folder_link: Direct link to folder
   - file_ids: Array of all file IDs

### Viewing Folder on Drive

1. Navigate to "Other Documents" list
2. Find the folder record (e.g., "Radio Report")
3. Click the **yellow folder icon (📁)** next to the name
4. Google Drive folder opens in new tab with all files

## Database Schema

### `other_documents` Collection
```javascript
{
  "id": "uuid",
  "ship_id": "uuid",
  "document_name": "Radio Report",
  "date": "2025-01-01",
  "status": "Unknown",
  "note": "Optional note",
  "file_ids": ["1xxx", "1yyy", "1zzz"],  // Array of file IDs
  "folder_id": "1abc123",  // NEW: Google Drive folder ID
  "folder_link": "https://drive.google.com/drive/folders/1abc123",  // NEW: Direct link
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": null
}
```

## Benefits

1. **Organized Storage**: Files grouped in dedicated folders on Google Drive
2. **Easy Access**: One-click access to entire folder
3. **Better Organization**: Folder structure mirrors document structure
4. **Simplified Workflow**: Upload multiple files at once
5. **Clear Visual Indicators**: Folder icon vs. file icon distinction

## Example Use Case

**Scenario**: User needs to upload monthly Radio Reports with multiple PDF files

1. User selects ship "BROTHER 36"
2. Clicks "Add Document" → "Upload Folder"
3. Selects folder "Radio Report January 2025" with 10 PDF files
4. System:
   - Creates: `BROTHER 36/Class & Flag Cert/Other Documents/Radio Report January 2025`
   - Uploads all 10 files to this folder
   - Stores folder link in database
5. User sees "Radio Report January 2025" in list with 📁 icon
6. Clicking 📁 opens Google Drive folder with all 10 files

## Testing Checklist

- [ ] Folder upload creates subfolder on Google Drive
- [ ] All files uploaded to correct subfolder
- [ ] folder_id and folder_link stored in database
- [ ] Folder icon (📁) displayed for folder uploads
- [ ] File icon (📄) displayed for single file uploads
- [ ] Clicking folder icon opens Google Drive folder
- [ ] Clicking file icon opens individual file
- [ ] Progress tracking works for all files
- [ ] Error handling for failed file uploads
- [ ] Multiple folders can be uploaded to same ship

## Notes

- Folder uploads create ONE database record with multiple file_ids
- Single file uploads create ONE database record with one file_id
- folder_link is only populated for folder uploads
- If folder_link exists, show folder icon; otherwise show file icon (if files exist)

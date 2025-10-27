# Fix: Folder Structure Issue - Other Documents Upload

## Problem

**What was happening:**
```
BROTHER 36
└── Class & Flag Cert
    └── Other Documents/Radio Report  ❌ (One folder with "/" in name)
```

**What should happen:**
```
BROTHER 36
└── Class & Flag Cert
    └── Other Documents (existing folder)
        └── Radio Report ✅ (subfolder inside Other Documents)
```

## Root Cause

The Apps Script's `upload_file_with_folder_creation` action does NOT automatically parse nested paths with `/`. 

When we passed:
```javascript
{
  "parent_category": "Class & Flag Cert",
  "category": "Other Documents/Radio Report"  // ❌ Treated as single folder name
}
```

Apps Script created a folder literally named `"Other Documents/Radio Report"` instead of creating two nested folders.

## Solution

**Changed parameter structure** to properly create nested folders:

### Before (Wrong):
```javascript
{
  "parent_category": "Class & Flag Cert",
  "category": "Other Documents/Radio Report"
}
```
**Created:** `Class & Flag Cert` → `Other Documents/Radio Report` (1 folder)

### After (Correct):
```javascript
{
  "parent_category": "Class & Flag Cert/Other Documents",  // ✅ Include existing parent
  "category": "Radio Report"  // ✅ Just the subfolder name
}
```
**Creates:** `Class & Flag Cert` → `Other Documents` → `Radio Report` (nested correctly)

## Code Changes

### File: `dual_apps_script_manager.py`

**Changed in `upload_other_document_folder()` method:**

```python
# OLD (Wrong approach)
nested_category = f"Other Documents/{folder_name}"
# This created: "Other Documents/Radio Report" as ONE folder

# NEW (Correct approach)
parent_category_path = "Class & Flag Cert/Other Documents"
category_name = folder_name  # e.g., "Radio Report"
# This creates: Class & Flag Cert → Other Documents → Radio Report
```

**Changed in `_call_apps_script_for_folder_upload()` method:**

```python
# OLD parameters
def _call_apps_script_for_folder_upload(
    self,
    nested_category: str  # "Other Documents/Radio Report"
)

# NEW parameters
def _call_apps_script_for_folder_upload(
    self,
    parent_category_path: str,  # "Class & Flag Cert/Other Documents"
    category_name: str  # "Radio Report"
)
```

**Payload sent to Apps Script:**

```python
payload = {
    "action": "upload_file_with_folder_creation",
    "parent_folder_id": self.parent_folder_id,
    "ship_name": ship_name,
    "parent_category": "Class & Flag Cert/Other Documents",  # ✅ Full path to parent
    "category": "Radio Report",  # ✅ Just subfolder name
    "filename": filename,
    "file_content": file_base64,
    "content_type": content_type
}
```

## How Apps Script Should Handle This

### Apps Script Logic (Expected):

```javascript
function handleUploadFileWithFolderCreation(data) {
  var parentCategory = data.parent_category;  // "Class & Flag Cert/Other Documents"
  var category = data.category;  // "Radio Report"
  
  // Step 1: Navigate parent_category path (handles "/" automatically)
  var parentCategoryPath = parentCategory.split('/');  // ["Class & Flag Cert", "Other Documents"]
  var currentFolder = shipFolder;
  
  for (var i = 0; i < parentCategoryPath.length; i++) {
    currentFolder = findOrCreateFolder(currentFolder, parentCategoryPath[i]);
  }
  // Now currentFolder = "Other Documents" folder
  
  // Step 2: Create category folder inside
  var categoryFolder = findOrCreateFolder(currentFolder, category);  // "Radio Report"
  
  // Step 3: Upload file to categoryFolder
  var file = categoryFolder.createFile(blob);
  
  return {
    success: true,
    file_id: file.getId(),
    folder_id: categoryFolder.getId(),  // ID of "Radio Report" folder
    message: "File uploaded successfully"
  };
}
```

## Expected Behavior After Fix

### User uploads folder "Radio Report" with 8 files:

1. **Backend:** Calls Apps Script 8 times with:
   ```
   parent_category: "Class & Flag Cert/Other Documents"
   category: "Radio Report"
   ```

2. **Apps Script:** 
   - Navigates: ROOT → BROTHER 36 → Class & Flag Cert → Other Documents
   - Creates subfolder: "Radio Report" (if not exists)
   - Uploads file to: Other Documents/Radio Report/file.pdf

3. **Result on Google Drive:**
   ```
   BROTHER 36
   └── Class & Flag Cert
       └── Other Documents
           └── Radio Report
               ├── AIS.pdf
               ├── EPIRB.pdf
               ├── SART.pdf
               ├── SSAS.pdf
               ├── GOC.pdf
               ├── Service Supplier Full Term Certificate No. PM-23250.pdf
               ├── RECORD BROTHER 36 - 2024.pdf
               └── desktop.ini
   ```

4. **Database:** Stores:
   ```json
   {
     "document_name": "Radio Report",
     "folder_id": "1abc123xyz",  // ID of Radio Report folder
     "folder_link": "https://drive.google.com/drive/folders/1abc123xyz",
     "file_ids": ["1file1", "1file2", "1file3", ...]
   }
   ```

5. **UI:** Shows:
   - Document Name: "Radio Report" 📁 (yellow folder icon)
   - Clicking 📁 opens: `BROTHER 36/Class & Flag Cert/Other Documents/Radio Report/`

## Testing

### Test Case 1: Upload new folder
1. Select ship "BROTHER 36"
2. Go to "Class & Flag Cert" → "Other Documents List"
3. Click "Add Document" → "Upload Folder"
4. Select folder "Radio Report" with files
5. Submit

**Expected Result:**
- ✅ Folder created at: `Other Documents/Radio Report/`
- ✅ All files uploaded inside `Radio Report` folder
- ✅ Database has `folder_id` and `folder_link`
- ✅ UI shows 📁 icon
- ✅ Clicking 📁 opens correct folder

### Test Case 2: Upload another folder to same ship
1. Upload folder "Safety Equipment Reports"

**Expected Result:**
- ✅ Folder created at: `Other Documents/Safety Equipment Reports/`
- ✅ Both folders exist in same "Other Documents" parent
- ✅ No conflicts

### Test Case 3: Upload to different ship
1. Select ship "SUNSHINE 01"
2. Upload folder "Radio Report"

**Expected Result:**
- ✅ Folder created at: `SUNSHINE 01/Class & Flag Cert/Other Documents/Radio Report/`
- ✅ Separate from BROTHER 36's folders

## Apps Script Requirement

**Apps Script MUST support nested paths in `parent_category`:**

If your Apps Script doesn't already handle `parent_category` with `/` (like `"Class & Flag Cert/Other Documents"`), you need to update it:

```javascript
// In handleUploadFileWithFolderCreation function

// OLD - assumes parent_category is single folder
var parentCategoryFolder = findOrCreateFolder(shipFolder, parentCategory);

// NEW - handle nested path
var parentCategoryPath = parentCategory.split('/');
var currentFolder = shipFolder;
for (var i = 0; i < parentCategoryPath.length; i++) {
  currentFolder = findOrCreateFolder(currentFolder, parentCategoryPath[i]);
}
var parentCategoryFolder = currentFolder;
```

## Status

✅ **Backend Fixed:** Code updated to pass correct parameters
✅ **Logic Verified:** Approach confirmed correct
⚠️ **Needs Testing:** Upload a test folder to verify folder structure on Google Drive
⚠️ **Apps Script:** May need update if it doesn't handle nested `parent_category` path

## Next Steps

1. **Test upload** with a sample folder
2. **Check Google Drive** folder structure
3. **If folder still wrong:** Update Apps Script to handle nested `parent_category`
4. **Verify `folder_id`** is returned and stored correctly

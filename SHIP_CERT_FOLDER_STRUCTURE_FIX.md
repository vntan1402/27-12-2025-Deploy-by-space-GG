# Ship Certificate Folder Structure Fix

## 📋 OVERVIEW

Updated Ship Certificate upload flow to auto-create folder structure, matching Audit Certificate behavior.

**Problem:** Ship Certificate uploads were failing when folders didn't exist
**Solution:** Use `parent_category` + `category` structure with auto-folder creation

---

## ✅ CHANGES MADE

### 1. **Backend Service** (`certificate_multi_upload_service.py`)

**Before:**
```python
upload_result = await _upload_to_gdrive(
    gdrive_config_doc, file_content, file.filename, ship_name, "Certificates"
)
```

**After:**
```python
upload_result = await _upload_to_gdrive_with_parent(
    gdrive_config_doc, file_content, file.filename, ship_name,
    "Class & Flag Cert",  # parent_category
    "Certificates"         # category
)
```

**Changes:**
- Line 309-311: Main certificate upload
- Line 334-336: Summary file upload
- Line 709-744: Added new `_upload_to_gdrive_with_parent()` method
- Line 746-779: Kept old `_upload_to_gdrive()` for backward compatibility (marked as LEGACY)

---

### 2. **GDrive Helper** (`gdrive_helper.py`)

**Before:**
```python
async def upload_file_with_parent_category(..., category: str):
    # Auto-detected content_type from filename only
    if filename.lower().endswith('.pdf'):
        content_type = 'application/pdf'
    ...
```

**After:**
```python
async def upload_file_with_parent_category(..., category: str, content_type: str = None):
    # Support custom content_type OR auto-detect
    if not content_type:
        if filename.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif filename.lower().endswith('.txt'):
            content_type = 'text/plain'
        ...
```

**Changes:**
- Line 106: Added `content_type` parameter
- Line 133-147: Enhanced content type detection with override support
- Added support for `.txt` (text/plain) for summary files

---

## 🔄 FOLDER STRUCTURE BEHAVIOR

### **Before (OLD):**
```
{Ship Name}/
  └── Class & Flag Cert/          ← Must exist (hardcoded lookup)
       └── Certificates/           ← Must exist
            └── file.pdf
```
**Result:** ❌ Upload FAILED if folders don't exist

---

### **After (NEW):**
```
{Ship Name}/
  └── Class & Flag Cert/          ← Auto-created if missing
       └── Certificates/           ← Auto-created if missing
            └── file.pdf
```
**Result:** ✅ Upload SUCCESS - folders created automatically

---

## 📊 COMPARISON WITH AUDIT CERTIFICATE

| Feature | Ship Certificate (OLD) | Ship Certificate (NEW) | Audit Certificate |
|---------|------------------------|------------------------|-------------------|
| **Method** | `_upload_to_gdrive()` | `_upload_to_gdrive_with_parent()` | `GDriveService.upload_file()` |
| **Parameters** | ship_name, category | ship_name, parent_category, category | folder_path (parsed) |
| **Folder Structure** | {Ship}/Class & Flag Cert/Certificates/ | {Ship}/Class & Flag Cert/Certificates/ | {Ship}/ISM - ISPS - MLC/Audit Certificates/ |
| **Auto-create folders?** | ❌ NO | ✅ YES | ✅ YES |
| **Apps Script action** | `upload_file_with_folder_creation` (old logic) | `upload_file_with_folder_creation` (new logic) | `upload_file_with_folder_creation` (new logic) |
| **Uses `createNestedFolders()`?** | ❌ NO | ✅ YES | ✅ YES |

---

## 🧪 TESTING CHECKLIST

### **Test Case 1: New Ship (No Folders)**
1. Create new ship via "Add Ship" (folders created: 6 main categories only)
2. Upload Ship Certificate PDF
3. **Expected:** 
   - ✅ Folder "Class & Flag Cert" exists (created during ship creation)
   - ✅ Subfolder "Certificates" auto-created
   - ✅ File uploaded successfully
   - Path: `{Ship}/Class & Flag Cert/Certificates/cert.pdf`

### **Test Case 2: Existing Ship (Folders Exist)**
1. Select ship with existing folder structure
2. Upload Ship Certificate PDF
3. **Expected:**
   - ✅ Reuses existing "Class & Flag Cert" folder
   - ✅ Reuses existing "Certificates" subfolder
   - ✅ File uploaded successfully
   - No duplicate folders created

### **Test Case 3: Multi-file Upload**
1. Select ship
2. Upload 3 Ship Certificate PDFs simultaneously
3. **Expected:**
   - ✅ All 3 files uploaded to same folder
   - ✅ No race condition creating folders
   - ✅ Summary files (.txt) uploaded with correct MIME type

### **Test Case 4: Summary File Upload**
1. Upload certificate with AI analysis (generates summary)
2. **Expected:**
   - ✅ Main PDF uploaded: `cert.pdf`
   - ✅ Summary TXT uploaded: `cert_Summary.txt`
   - ✅ Both in same folder: `{Ship}/Class & Flag Cert/Certificates/`
   - ✅ Summary file has `text/plain` MIME type

---

## 🔍 APPS SCRIPT REQUIREMENTS

**The Apps Script must have `createNestedFolders()` function:**

```javascript
function createNestedFolders(parentFolder, folderNames) {
  var currentFolder = parentFolder;
  
  for (var i = 0; i < folderNames.length; i++) {
    var folderName = folderNames[i];
    
    // Check if folder already exists
    var folders = currentFolder.getFoldersByName(folderName);
    if (folders.hasNext()) {
      currentFolder = folders.next();  // Reuse existing
    } else {
      currentFolder = currentFolder.createFolder(folderName);  // Create new
    }
  }
  
  return currentFolder;
}
```

**Payload format from backend:**
```json
{
  "action": "upload_file_with_folder_creation",
  "parent_folder_id": "...",
  "ship_name": "MV OCEAN",
  "parent_category": "Class & Flag Cert",
  "category": "Certificates",
  "filename": "cert.pdf",
  "file_content": "base64...",
  "content_type": "application/pdf"
}
```

---

## 📝 BACKWARD COMPATIBILITY

**Old method `_upload_to_gdrive()` is kept for backward compatibility:**
- Marked as `LEGACY METHOD` in docstring
- Still functional if needed by other code
- Recommend migrating all usages to `_upload_to_gdrive_with_parent()`

---

## 🚀 DEPLOYMENT NOTES

### **Production Deployment:**
1. ✅ Deploy updated backend code
2. ✅ Verify Apps Script has `createNestedFolders()` function
3. ✅ Test with new ship (empty folder structure)
4. ✅ Test with existing ship (reuse folders)
5. ✅ Monitor logs for upload errors

### **Rollback Plan:**
If issues occur, revert these lines:
- `certificate_multi_upload_service.py`: Lines 309-311, 334-336
- Change back to `_upload_to_gdrive(..., "Certificates")`

---

## 📌 RELATED FILES

**Modified:**
- `/app/backend/app/services/certificate_multi_upload_service.py`
- `/app/backend/app/utils/gdrive_helper.py`

**Apps Script:**
- `/app/WORKING_APPS_SCRIPT.js` (reference implementation)

**Unchanged:**
- Audit Certificate flow (already using this pattern)
- Frontend components (no changes needed)

---

## ✅ SUMMARY

**Ship Certificate uploads now:**
1. ✅ Auto-create folder structure if missing
2. ✅ Reuse existing folders (no duplicates)
3. ✅ Match Audit Certificate behavior
4. ✅ Support custom MIME types (for summary files)
5. ✅ Work with new ship folder structure (6 main categories only)

**Path:** `{Ship Name}/Class & Flag Cert/Certificates/`

**Status:** ✅ READY FOR TESTING

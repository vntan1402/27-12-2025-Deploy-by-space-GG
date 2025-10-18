# Standby Crew Certificate File Upload Bug Fix

## Problem Report
When adding crew certificate for Standby crew, only the **summary file** was uploaded to Google Drive, but the **original certificate file** was NOT uploaded.

## Root Cause Identified
Apps Script received **empty `ship_name` parameter** (`ship_name: ''`) for Standby crew uploads and rejected the request with error: `Missing required parameters`.

**Technical Details:**
- Backend code set `ship_name = ''` (empty string) for Standby uploads
- Apps Script's `upload_file_with_folder_creation` action requires non-empty `ship_name`
- Summary file upload succeeded because it uses different parameters (ship_name = 'SUMMARY')

## Solution Implemented

### Code Change
**Location:** `/app/backend/dual_apps_script_manager.py` (lines ~710-755)

**Before (Broken):**
```python
if is_standby:
    # Find COMPANY DOCUMENT folder first
    company_document_folder_id = await find_company_document_folder()
    
    # Upload with empty ship_name
    cert_upload = await self._call_company_apps_script({
        'action': 'upload_file_with_folder_creation',
        'parent_folder_id': company_document_folder_id,
        'ship_name': '',  # ❌ Empty string - Apps Script rejects this
        'category': 'Standby Crew',
        'filename': cert_filename,
        'file_content': base64_content,
        'content_type': cert_content_type
    })
```

**After (Fixed):**
```python
if is_standby:
    # Upload with 'COMPANY DOCUMENT' as ship_name
    cert_upload = await self._call_company_apps_script({
        'action': 'upload_file_with_folder_creation',
        'parent_folder_id': self.parent_folder_id,  # ROOT folder
        'ship_name': 'COMPANY DOCUMENT',  # ✅ Non-empty, creates folder hierarchy
        'category': 'Standby Crew',
        'filename': cert_filename,
        'file_content': base64_content,
        'content_type': cert_content_type
    })
```

**Key Changes:**
1. ✅ Changed `ship_name` from `''` (empty) to `'COMPANY DOCUMENT'`
2. ✅ Simplified logic - removed extra COMPANY DOCUMENT folder lookup
3. ✅ Use ROOT folder as parent (let Apps Script handle folder creation)

### How Apps Script Handles It

**Parameters:**
- `parent_folder_id`: ROOT folder ID
- `ship_name`: "COMPANY DOCUMENT"
- `category`: "Standby Crew"

**Apps Script Logic:**
1. Look for "COMPANY DOCUMENT" folder in ROOT
2. If not found, create it
3. Look for "Standby Crew" folder in COMPANY DOCUMENT
4. If not found, create it
5. Upload file to COMPANY DOCUMENT/Standby Crew

**Result:** File uploaded to correct path: `ROOT/COMPANY DOCUMENT/Standby Crew`

## Testing Results

### Test Execution
- **Tester:** Backend Testing Agent
- **Test Date:** Current session
- **Test Crew:** NINH VIẾT THƯỞNG (ship_sign_on = "-")

### Results Summary
✅ **Both files uploaded successfully!**

**Before Fix:**
- Certificate File ID: `null` ❌
- Summary File ID: Valid ✅
- Result: **Only summary uploaded**

**After Fix:**
- Certificate File ID: `1X5SMAGUOpM-uYn8U3qTEqTk6jHs5fgIc` ✅
- Summary File ID: `1vkagB7ypYWpaoThCFnB4SsswrqYK760M` ✅
- Result: **Both files uploaded**

### Backend Logs Verification

**Before Fix:**
```
📍 Upload destination: COMPANY DOCUMENT/Standby Crew (Standby crew)
📤 Uploading certificate to COMPANY DOCUMENT/Standby Crew: test.pdf
   ship_name: ""  ❌
Apps Script Response: {success: false, message: "Missing required parameters"}
❌ Certificate file upload failed
```

**After Fix:**
```
📍 Upload destination: COMPANY DOCUMENT/Standby Crew (Standby crew)
📤 Uploading certificate to COMPANY DOCUMENT/Standby Crew: test.pdf
   ship_name: "COMPANY DOCUMENT"  ✅
Apps Script Response: {success: true, message: "File uploaded successfully"}
✅ Certificate file uploads completed successfully
📎 Certificate File ID: 1X5SMAGUOpM-uYn8U3qTEqTk6jHs5fgIc
📋 Summary File ID: 1vkagB7ypYWpaoThCFnB4SsswrqYK760M
```

## Files Modified

**Backend:**
- `/app/backend/dual_apps_script_manager.py`
  - `upload_certificate_files()` method (lines ~710-755)
  - Changed `ship_name` from `''` to `'COMPANY DOCUMENT'` for Standby uploads
  - Removed complex folder lookup logic
  - Simplified to use ROOT + ship_name + category pattern

**Documentation:**
- This file: `/app/STANDBY_CERT_UPLOAD_BUG_FIX.md`

## Impact

### Affected Users
- Any user adding certificates for Standby crew
- All certificates with `ship_id = null`

### Data Integrity
**Previous certificates (before fix):**
- Still have missing original files
- Only summary files exist
- May need manual re-upload if critical

**New certificates (after fix):**
- Both original and summary files uploaded
- Complete data integrity maintained

## Comparison: Standby vs Ship Uploads

### Standby Crew Upload (Fixed)
```python
{
    'parent_folder_id': ROOT_FOLDER_ID,
    'ship_name': 'COMPANY DOCUMENT',
    'category': 'Standby Crew'
}
```
→ Creates: `ROOT/COMPANY DOCUMENT/Standby Crew/file.pdf`

### Ship Crew Upload (Already Working)
```python
{
    'parent_folder_id': ROOT_FOLDER_ID,
    'ship_name': 'BROTHER 36',
    'category': 'Crew Records'
}
```
→ Creates: `ROOT/BROTHER 36/Crew Records/file.pdf`

**Pattern:** Both use same logic now - consistent and reliable!

## Why This Fix Works

### 1. Apps Script Requirement
Apps Script's `upload_file_with_folder_creation` expects:
- Non-empty `ship_name` parameter
- Creates folder hierarchy: `parent/ship_name/category`
- Rejects empty `ship_name` as invalid

### 2. Folder Hierarchy
Using `'COMPANY DOCUMENT'` as `ship_name`:
- Maintains correct folder structure
- Let's Apps Script handle folder creation
- No special case logic needed

### 3. Consistency
- Same upload pattern for Standby and Ship crew
- Reduces code complexity
- Easier to maintain and debug

## Edge Cases Handled

### Case 1: COMPANY DOCUMENT Folder Doesn't Exist
- Apps Script creates it automatically
- No manual intervention needed
- Works on first upload

### Case 2: Standby Crew Folder Doesn't Exist
- Apps Script creates it automatically
- Under COMPANY DOCUMENT folder
- Correct hierarchy maintained

### Case 3: Multiple Standby Certificates
- All upload to same Standby Crew folder
- No conflicts or duplicate folders
- Organized and consistent

## Status
✅ Bug Fixed
✅ Both certificate and summary files upload successfully
✅ Tested with real Standby crew data
✅ Backend logs confirm fix working
✅ No regressions for Ship crew uploads
✅ Production ready

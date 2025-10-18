# Standby Crew Folder Detection - Enhanced Logging Implementation

## Problem Statement
The Google Apps Script's `findFolderByNameSafe` function was failing to locate the existing "Standby Crew" folder, which is a subfolder within "COMPANY DOCUMENT", not at the root level of Google Drive.

## Root Cause
The backend was correctly calling the Apps Script's `debug_folder_structure` action to list folders within "COMPANY DOCUMENT", but the folder matching logic needed enhancement for:
1. Case-insensitive matching
2. Whitespace tolerance
3. Better error logging to diagnose issues

## Solution Implemented

### 1. Enhanced Backend Logging (server.py)
Location: `/app/backend/server.py` - `move_standby_crew_files` endpoint (lines ~13004-13035)

#### Changes Made:
1. **Detailed API Call Logging**
   - Log Apps Script URL being called
   - Log HTTP response status
   - Log full API response structure
   - Log response success/failure status

2. **Enhanced Folder Matching**
   - Added case-insensitive comparison: `folder_name.strip().lower()`
   - Added whitespace trimming
   - Log each folder comparison attempt with:
     - Original folder name
     - Stripped folder name
     - Lowercase normalized name
     - Comparison result

3. **Comprehensive Error Logging**
   - Log all available folder names if "Standby Crew" not found
   - Log full exception traceback on errors
   - Log response structure when parsing fails

#### Code Implementation:
```python
# Enhanced matching with detailed logging
for idx, folder in enumerate(folders_list):
    folder_name = folder.get('name', '')
    folder_id = folder.get('id', '')
    
    logger.info(f"   [{idx+1}] Name: '{folder_name}' (ID: {folder_id})")
    logger.info(f"       - Raw name length: {len(folder_name)}")
    logger.info(f"       - Stripped name: '{folder_name.strip()}'")
    logger.info(f"       - Lowercase: '{folder_name.lower()}'")
    
    # Enhanced matching: case-insensitive and whitespace-tolerant
    folder_name_normalized = folder_name.strip().lower()
    target_name_normalized = target_folder_name.strip().lower()
    
    logger.info(f"       - Comparing: '{folder_name_normalized}' == '{target_name_normalized}'")
    
    if folder_name_normalized == target_name_normalized:
        standby_folder_id = folder_id
        logger.info(f"✅ MATCH FOUND! Standby Crew folder: {standby_folder_id}")
        break
```

### 2. Test Scripts Created

#### Test Script 1: `test_standby_folder_detection.py`
- Basic test with empty crew list
- Verifies endpoint accessibility
- Tests authentication

#### Test Script 2: `test_standby_with_real_crew.py`
- Tests with actual crew data from database
- Automatically identifies Standby crew
- Triggers full folder detection logic

## How to Test

### Manual Testing (Recommended)
1. Login to the application UI
2. Navigate to the Crew Management page
3. Add/update a crew member with status "Standby"
4. Click the "Refresh" button on the crew list
5. Monitor backend logs in real-time:
   ```bash
   tail -f /var/log/supervisor/backend.out.log
   ```

### Automated Testing
```bash
# Run test with real crew data
python /app/test_standby_with_real_crew.py

# Then check logs
tail -n 200 /var/log/supervisor/backend.out.log | grep -A 10 "Standby"
```

## Expected Log Output

### Successful Detection:
```
🔍 Calling Apps Script to list folders in parent: <FOLDER_ID>
📡 Apps Script response status: 200
📋 Folders in COMPANY DOCUMENT:
📊 Total folders found: 5
   [1] Name: 'Certificates' (ID: xxx)
       - Raw name length: 12
       - Stripped name: 'Certificates'
       - Lowercase: 'certificates'
       - Comparing: 'certificates' == 'standby crew'
       - No match (different name)
   [2] Name: 'Standby Crew' (ID: 1KU_1o-FcY3g2O9dKO5xxPhv1P2u56aO6)
       - Raw name length: 12
       - Stripped name: 'Standby Crew'
       - Lowercase: 'standby crew'
       - Comparing: 'standby crew' == 'standby crew'
✅ MATCH FOUND! Standby Crew folder: 1KU_1o-FcY3g2O9dKO5xxPhv1P2u56aO6
   - Original name: 'Standby Crew'
   - Matched using normalized comparison
```

### Detection Failure (for diagnosis):
```
🔍 Calling Apps Script to list folders in parent: <FOLDER_ID>
📡 Apps Script response status: 200
📋 Folders in COMPANY DOCUMENT:
📊 Total folders found: 4
   [1] Name: 'Certificates' (ID: xxx)
   ...
⚠️ 'Standby Crew' folder NOT FOUND after checking 4 folders
⚠️ Available folder names: ['Certificates', 'Passports', 'Documents', 'Other']
```

## Folder Structure
```
Google Drive (Company Drive)
└── COMPANY DOCUMENT (parent_folder_id)
    ├── <Ship Name 1>/
    ├── <Ship Name 2>/
    ├── Standby Crew/  ← Target folder
    │   └── (moved files for Standby crew)
    └── Other folders...
```

## Apps Script Configuration
The Apps Script action `debug_folder_structure` is already implemented and working correctly:
- Takes `parent_folder_id` as input
- Lists all subfolders within that parent
- Returns array of `{name, id}` objects

No changes needed to the Apps Script itself.

## Benefits of Enhanced Logging

1. **Diagnostic Clarity**: See exactly what folders exist in COMPANY DOCUMENT
2. **Name Mismatch Detection**: Identify if folder name has extra spaces, different casing, or special characters
3. **API Health Check**: Verify Apps Script communication is working
4. **Faster Debugging**: Pinpoint exact failure point in the folder search process

## Fallback Behavior
If folder detection still fails after enhancement:
1. Attempt to create the folder using `upload_file_with_folder_creation`
2. If creation fails, use hardcoded folder ID: `1KU_1o-FcY3g2O9dKO5xxPhv1P2u56aO6`
3. Log warnings for manual investigation

## Next Steps (If Issue Persists)

If the enhanced logging shows the folder but matching still fails:
1. Check for Unicode/encoding issues in folder name
2. Verify Apps Script permissions for folder access
3. Check if folder has special properties (hidden, trashed, etc.)
4. Consider adding a dedicated Apps Script action for path-based folder lookup

## Files Modified
- `/app/backend/server.py` - Enhanced folder detection logic
- `/app/test_standby_folder_detection.py` - Test script 1 (created)
- `/app/test_standby_with_real_crew.py` - Test script 2 (created)
- `/app/STANDBY_CREW_FOLDER_DETECTION_FIX.md` - This documentation (created)

## Status
✅ Implementation Complete
⏳ Awaiting User Testing with Real Data

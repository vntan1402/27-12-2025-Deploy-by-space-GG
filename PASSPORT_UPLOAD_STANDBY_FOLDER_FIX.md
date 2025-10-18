# Passport Upload - Standby Folder Fix

## Summary
Fixed passport file upload destination for Standby crew in batch processing mode. Files now correctly upload to "COMPANY DOCUMENT > Standby Crew" instead of "- > Crew Records".

## Problem

**Issue:**
When uploading passport files for Standby crew in batch mode:
- Frontend correctly sent `ship_name = "-"`
- Backend received `ship_name = "-"` 
- But backend uploaded files to: `- > Crew Records` ❌
- Should upload to: `COMPANY DOCUMENT > Standby Crew` ✅

**Console Log:**
```
📋 Batch processing mode: STANDBY
📁 Target folder: COMPANY DOCUMENT > Standby Crew  ← Frontend
📤 Uploading passport file: -/Crew Records/...      ← Backend (Wrong!)
```

**Root Cause:**
Backend function `upload_passport_files` in `dual_apps_script_manager.py` did not handle the special case when `ship_name = "-"`. It treated "-" as a literal ship name and created folder structure: `- > Crew Records`.

## Solution

**File:** `backend/dual_apps_script_manager.py`
**Function:** `upload_passport_files` (lines ~869-885)

### Logic Added

**Before:**
```python
# Upload 1: Passport file to Ship/Crew Records
logger.info(f"📤 Uploading passport file: {ship_name}/Crew Records/{passport_filename}")
passport_upload = await self._call_company_apps_script({
    'action': 'upload_file_with_folder_creation',
    'parent_folder_id': self.parent_folder_id,
    'ship_name': ship_name,  # ❌ Always uses ship_name as-is
    'category': 'Crew Records',  # ❌ Always Crew Records
    ...
})
```

**After:**
```python
# Determine target folder based on ship_name
if ship_name == "-":
    target_ship = "COMPANY DOCUMENT"
    target_category = "Standby Crew"
    logger.info(f"📤 Uploading passport file (Standby): {target_ship}/{target_category}/{passport_filename}")
else:
    target_ship = ship_name
    target_category = "Crew Records"
    logger.info(f"📤 Uploading passport file (Normal): {target_ship}/{target_category}/{passport_filename}")

# Upload passport file
passport_upload = await self._call_company_apps_script({
    'action': 'upload_file_with_folder_creation',
    'parent_folder_id': self.parent_folder_id,
    'ship_name': target_ship,  # ✅ Dynamic based on mode
    'category': target_category,  # ✅ Dynamic based on mode
    ...
})
```

## Implementation Details

### Conditional Logic

**Check:**
```python
if ship_name == "-":
```

**Standby Mode:**
- `target_ship = "COMPANY DOCUMENT"`
- `target_category = "Standby Crew"`
- Folder path: `ROOT > COMPANY DOCUMENT > Standby Crew`

**Normal Mode:**
- `target_ship = ship_name` (e.g., "BROTHER 36")
- `target_category = "Crew Records"`
- Folder path: `ROOT > BROTHER 36 > Crew Records`

### Console Logs

**Updated logs for clarity:**

**Standby Mode:**
```
📤 Uploading passport file (Standby): COMPANY DOCUMENT/Standby Crew/passport.pdf
```

**Normal Mode:**
```
📤 Uploading passport file (Normal): BROTHER 36/Crew Records/passport.pdf
```

## Complete Flow

### Scenario: Batch Upload in Standby Mode

```
Step 1: Frontend
- User clicks [🟠 Standby Crew] button
- newCrewData.status = "Standby"
- Uploads 3 passport files

Step 2: Frontend Processing (processSinglePassportInBatch)
- Detects: isStandbyMode = true
- Creates crew: status="Standby", ship_sign_on="-"
- Sends to backend: ship_name="-"
- Log: "📋 Batch processing mode: STANDBY"
- Log: "📁 Target folder: COMPANY DOCUMENT > Standby Crew"

Step 3: Backend (upload_passport_files_after_creation)
- Receives: ship_name="-"
- Calls: dual_manager.upload_passport_files(..., ship_name="-")

Step 4: Backend (upload_passport_files)
- Checks: ship_name == "-" → True
- Sets: target_ship="COMPANY DOCUMENT", target_category="Standby Crew"
- Log: "📤 Uploading passport file (Standby): COMPANY DOCUMENT/Standby Crew/..."
- Uploads to: COMPANY DOCUMENT > Standby Crew

Step 5: Google Apps Script
- Receives: ship_name="COMPANY DOCUMENT", category="Standby Crew"
- Locates: COMPANY DOCUMENT folder
- Creates/finds: Standby Crew subfolder
- Uploads file to: COMPANY DOCUMENT/Standby Crew/passport.pdf

Result: ✅ Files in correct location
```

### Scenario: Batch Upload in Normal Mode

```
Step 1: Frontend
- Modal open with ship "BROTHER 36"
- newCrewData.status = "Sign on"
- Uploads 3 passport files

Step 2: Frontend Processing
- Detects: isStandbyMode = false
- Creates crew: status="Sign on", ship_sign_on="BROTHER 36"
- Sends to backend: ship_name="BROTHER 36"

Step 3: Backend (upload_passport_files)
- Checks: ship_name == "-" → False
- Sets: target_ship="BROTHER 36", target_category="Crew Records"
- Log: "📤 Uploading passport file (Normal): BROTHER 36/Crew Records/..."
- Uploads to: BROTHER 36 > Crew Records

Result: ✅ Files in ship folder
```

## Folder Structure

### Before Fix

**Standby Mode:**
```
ROOT
├── - (incorrect folder!)
│   └── Crew Records
│       ├── passport1.pdf
│       ├── passport2.pdf
│       └── passport3.pdf
└── COMPANY DOCUMENT
    └── Standby Crew (empty!)
```

### After Fix

**Standby Mode:**
```
ROOT
└── COMPANY DOCUMENT
    └── Standby Crew
        ├── passport1.pdf
        ├── passport2.pdf
        └── passport3.pdf
```

**Normal Mode (unchanged):**
```
ROOT
└── BROTHER 36
    └── Crew Records
        ├── passport1.pdf
        ├── passport2.pdf
        └── passport3.pdf
```

## Integration with Frontend

### Frontend Already Correct

Frontend was already sending correct `ship_name`:
- Standby mode: `ship_name = "-"`
- Normal mode: `ship_name = selectedShip?.name`

**Frontend code (already correct):**
```javascript
const targetShipName = isStandbyMode ? '-' : (selectedShip?.name || '-');
console.log(`📁 Target folder: ${isStandbyMode ? 'COMPANY DOCUMENT > Standby Crew' : `${targetShipName} > Crew Records`}`);

// Send to backend
ship_name: targetShipName
```

### Backend Now Handles Correctly

Backend now interprets `ship_name = "-"` as Standby indicator:
```python
if ship_name == "-":
    # Standby crew → COMPANY DOCUMENT/Standby Crew
else:
    # Normal crew → Ship Name/Crew Records
```

## Testing

### Test Case 1: Standby Mode Upload
1. Open Add Crew modal
2. Click [⚪ Standby Crew] → Active
3. Upload 3 passport files
4. Check console:
   - ✅ Frontend: "📋 Batch processing mode: STANDBY"
   - ✅ Backend: "📤 Uploading passport file (Standby): COMPANY DOCUMENT/Standby Crew/..."
5. Check Google Drive:
   - ✅ Files in: COMPANY DOCUMENT > Standby Crew
6. Check database:
   - ✅ Crew: status="Standby", ship_sign_on="-"
   - ✅ File IDs present

### Test Case 2: Normal Mode Upload
1. Open Add Crew modal (ship: BROTHER 36)
2. Upload 3 passport files
3. Check console:
   - ✅ Frontend: "📋 Batch processing mode: NORMAL"
   - ✅ Backend: "📤 Uploading passport file (Normal): BROTHER 36/Crew Records/..."
4. Check Google Drive:
   - ✅ Files in: BROTHER 36 > Crew Records
5. Check database:
   - ✅ Crew: status="Sign on", ship_sign_on="BROTHER 36"

### Test Case 3: Mode Switch
1. Start in Normal mode
2. Upload 2 passports → Ship folder
3. Switch to Standby mode
4. Upload 2 passports → Standby folder
5. Verify:
   - ✅ First 2 in ship folder
   - ✅ Last 2 in Standby folder

## Related Components

### Summary File Upload
- Also handled correctly
- Summary files upload to: `SUMMARY > Crew Records` (unchanged)
- Standby mode doesn't affect summary folder location

### Single File Upload
- Already working correctly (not affected)
- Uses review mode before adding

### File Movement
- Automatic movement on status change
- Works with this fix
- Can move between Ship and Standby folders

## Console Log Verification

### Expected Logs for Standby Upload

**Frontend:**
```
🔄 Batch processing 1/3: passport1.pdf
📋 Batch processing mode: STANDBY
   Status: Standby, Ship: -
📤 Uploading passport files to Drive for crew crew123...
📁 Target folder: COMPANY DOCUMENT > Standby Crew
```

**Backend:**
```
📤 Uploading passport files for crew: crew123
📤 Uploading passport files to Drive: passport1.pdf
📤 Uploading passport file (Standby): COMPANY DOCUMENT/Standby Crew/passport1.pdf
✅ Passport file uploads completed successfully
```

### Expected Logs for Normal Upload

**Frontend:**
```
🔄 Batch processing 1/3: passport1.pdf
📋 Batch processing mode: NORMAL
   Status: Sign on, Ship: BROTHER 36
📤 Uploading passport files to Drive for crew crew456...
📁 Target folder: BROTHER 36 > Crew Records
```

**Backend:**
```
📤 Uploading passport files for crew: crew456
📤 Uploading passport files to Drive: passport1.pdf
📤 Uploading passport file (Normal): BROTHER 36/Crew Records/passport1.pdf
✅ Passport file uploads completed successfully
```

## Notes

- This fix only affects passport file uploads (multi-file batch)
- Certificate uploads use different logic (not affected)
- Google Apps Script logic unchanged (already handles folders correctly)
- The special value "-" is now consistently interpreted as Standby mode indicator
- Frontend, backend, and Apps Script now all aligned on Standby logic

## Verification Steps

After deployment:
1. Clear any test folders: Delete "- > Crew Records" if exists
2. Test Standby upload
3. Verify files in: COMPANY DOCUMENT > Standby Crew
4. Check no "- > Crew Records" folder created
5. Test normal upload still works
6. Verify files in: Ship Name > Crew Records

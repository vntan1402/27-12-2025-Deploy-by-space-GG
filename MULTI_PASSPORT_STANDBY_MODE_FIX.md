# Multi Passport Upload - Standby Mode Fix

## Summary
Fixed multi-passport batch upload to correctly respect Standby mode settings, ensuring files are uploaded to the correct folder based on the current mode.

## Problem

**Issue:**
When uploading multiple passport files in Standby mode, the system was ignoring the Standby mode setting and:
- Creating crew members with `status: "Sign on"` instead of `status: "Standby"`
- Setting `ship_sign_on: selectedShip?.name` instead of `ship_sign_on: "-"`
- Uploading files to selected ship's folder instead of "Standby Crew" folder

**Root Cause:**
The `processSinglePassportInBatch` function had hardcoded values:
```javascript
status: 'Sign on',  // ❌ Always Sign on
ship_sign_on: selectedShip?.name || '-',  // ❌ Always uses selected ship
ship_name: analysis._ship_name || selectedShip?.name || '-'  // ❌ Always uses selected ship
```

## Solution

**File:** `frontend/src/App.js`
**Function:** `processSinglePassportInBatch` (lines ~5732-5900)

### Changes Made

#### 1. Check Standby Mode State

Added check for current form state before creating crew data:

```javascript
// Check if we're in Standby mode from the form state
const isStandbyMode = newCrewData.status === 'Standby';

console.log(`📋 Batch processing mode: ${isStandbyMode ? 'STANDBY' : 'NORMAL'}`);
console.log(`   Status: ${crewData.status}, Ship: ${crewData.ship_sign_on}`);
```

#### 2. Dynamic Crew Data Creation

Updated crew data to respect Standby mode:

**Before:**
```javascript
const crewData = {
  ...
  status: 'Sign on',  // ❌ Always Sign on
  ship_sign_on: selectedShip?.name || '-',  // ❌ Always ship
  ...
};
```

**After:**
```javascript
const crewData = {
  ...
  status: isStandbyMode ? 'Standby' : 'Sign on',  // ✅ Dynamic
  ship_sign_on: isStandbyMode ? '-' : (selectedShip?.name || '-'),  // ✅ Dynamic
  ...
};
```

#### 3. Dynamic File Upload Target

Updated file upload to use correct folder:

**Before:**
```javascript
ship_name: analysis._ship_name || selectedShip?.name || '-'  // ❌ Always ship
```

**After:**
```javascript
// Determine ship name based on mode
const targetShipName = isStandbyMode ? '-' : (selectedShip?.name || '-');
console.log(`📁 Target folder: ${isStandbyMode ? 'COMPANY DOCUMENT > Standby Crew' : `${targetShipName} > Crew Records`}`);

// Use in upload
ship_name: targetShipName  // ✅ Dynamic based on mode
```

#### 4. Correct Result Display

Updated batch result to show correct file path:

**Before:**
```javascript
filePath: uploadedPassportId ? `${selectedShip?.name}/Crew Records/${file.name}` : 'N/A',
ship: selectedShip?.name || '-',
```

**After:**
```javascript
filePath: uploadedPassportId 
  ? (isStandbyMode 
      ? `COMPANY DOCUMENT/Standby Crew/${file.name}` 
      : `${selectedShip?.name}/Crew Records/${file.name}`) 
  : 'N/A',
ship: targetShipName,  // Shows "-" for Standby, ship name for normal
```

## Behavior

### Normal Mode (Ship Selected)

**When uploading multiple passports:**
1. Creates crew with: `status: "Sign on"`, `ship_sign_on: "SHIP_NAME"`
2. Uploads files to: `SHIP_NAME/Crew Records/`
3. Result shows: `ship: "SHIP_NAME"`, `filePath: "SHIP_NAME/Crew Records/filename.pdf"`

### Standby Mode (Active)

**When uploading multiple passports:**
1. Creates crew with: `status: "Standby"`, `ship_sign_on: "-"`
2. Uploads files to: `COMPANY DOCUMENT/Standby Crew/`
3. Result shows: `ship: "-"`, `filePath: "COMPANY DOCUMENT/Standby Crew/filename.pdf"`

## Complete Flow

### Scenario: Multi-Upload in Standby Mode

```
User Actions:
1. Click "ADD NEW RECORD" → Crew Records
2. Modal opens (default: Normal mode)
3. Click [⚪ Standby Crew] button → Activates Standby Mode
4. Modal title changes to "for: Standby Crew" (orange)
5. Drag & drop 5 passport files

System Processing:
6. Detects isStandbyMode = true
7. For each passport file:
   a. Analyze passport
   b. Create crew with status="Standby", ship_sign_on="-"
   c. Upload original file → COMPANY DOCUMENT/Standby Crew/
   d. Upload summary file → COMPANY DOCUMENT/Standby Crew/
   e. Log: "📁 Target folder: COMPANY DOCUMENT > Standby Crew"
8. Show results modal with correct paths

Result Display:
✅ 5 crew members created
✅ Status: Standby
✅ Ship: -
✅ Files in: COMPANY DOCUMENT/Standby Crew/
```

### Scenario: Switch Mode During Process

```
User Actions:
1. Open modal (Normal mode for BROTHER 36)
2. Start uploading files
3. Mid-process: Click [🟠 Standby Crew] → Switch to Standby

System Behavior:
- Already-processed files: Ship folder (before switch)
- Next files: Standby folder (after switch)
- Each file uses mode at time of processing
```

## Console Logs

### Normal Mode Processing
```
🔄 Batch processing 1/3: passport1.pdf
📋 Batch processing mode: NORMAL
   Status: Sign on, Ship: BROTHER 36
📤 Uploading passport files to Drive for crew crew123...
📁 Target folder: BROTHER 36 > Crew Records
✅ Passport files uploaded successfully to Drive
```

### Standby Mode Processing
```
🔄 Batch processing 1/3: passport1.pdf
📋 Batch processing mode: STANDBY
   Status: Standby, Ship: -
📤 Uploading passport files to Drive for crew crew456...
📁 Target folder: COMPANY DOCUMENT > Standby Crew
✅ Passport files uploaded successfully to Drive
```

## Integration with Other Features

### Works With:

1. **Single File Upload**
   - Already had correct logic (not affected)
   - Uses review mode before adding

2. **Status Badge**
   - Shows "🟠 Chế độ Standby" when active
   - Consistent with batch processing mode

3. **Ship Sign On Field**
   - Disabled and locked to "-" in Standby mode
   - Crew data matches field state

4. **Automatic File Movement**
   - After batch upload, if status changes
   - Files can be moved between folders

5. **Processing Results Modal**
   - Shows correct file paths
   - Displays "-" for ship in Standby mode

## Testing Recommendations

### Test Case 1: Normal Multi-Upload
1. Open Add Crew modal (with ship selected)
2. Upload 3 passports
3. Verify:
   - ✅ Crew created with status="Sign on", ship="SHIP_NAME"
   - ✅ Files in ship's Crew Records folder
   - ✅ Results show correct ship name

### Test Case 2: Standby Multi-Upload
1. Open Add Crew modal
2. Click [⚪ Standby Crew] button
3. Upload 3 passports
4. Verify:
   - ✅ Crew created with status="Standby", ship="-"
   - ✅ Files in COMPANY DOCUMENT/Standby Crew folder
   - ✅ Results show ship: "-"

### Test Case 3: Mode Switch During Upload
1. Start in Normal mode
2. Upload 2 passports (should go to ship folder)
3. Switch to Standby mode
4. Upload 2 more passports (should go to Standby folder)
5. Verify:
   - ✅ First 2 in ship folder
   - ✅ Last 2 in Standby folder

### Test Case 4: Mixed Status Check
1. Upload 5 passports in Standby mode
2. Check database:
   - ✅ All 5 crew have status="Standby"
   - ✅ All 5 crew have ship_sign_on="-"
3. Check Google Drive:
   - ✅ All files in Standby Crew folder

### Test Case 5: Console Verification
1. Open browser console
2. Upload in Standby mode
3. Look for:
   - ✅ "📋 Batch processing mode: STANDBY"
   - ✅ "📁 Target folder: COMPANY DOCUMENT > Standby Crew"
   - ✅ No errors

## Related Files

- `frontend/src/App.js` - Main logic
- `backend/server.py` - Upload endpoint (unchanged)
- Google Apps Script - Folder creation logic (unchanged)

## Notes

- Single file upload was already working correctly (not affected by this fix)
- This fix only affects multi-file batch upload scenario
- The mode check uses `newCrewData.status` which is the current form state
- Mode is evaluated per-file, so switching mid-batch affects remaining files
- Backend logic for folder creation remains unchanged (already correct)

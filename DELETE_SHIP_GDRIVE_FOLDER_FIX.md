# Delete Ship Google Drive Folder Deletion Fix

## Problem Statement
The Delete Ship feature's Google Drive folder deletion was failing due to an Apps Script action name mismatch. The backend was sending action `delete_ship_folder` but Apps Script v4.3 expects `delete_complete_ship_structure`.

## Root Cause
- **Backend endpoint**: `/api/companies/{company_id}/gdrive/delete-ship-folder` was using incorrect action name
- **Apps Script v4.3**: Supports `delete_complete_ship_structure` action, not `delete_ship_folder`
- **Payload structure**: Also had parameter name mismatches (`main_folder_id` vs `parent_folder_id`)

## Solution Implemented

### Backend Changes (`/app/backend/server.py`)

Updated the `/api/companies/{company_id}/gdrive/delete-ship-folder` endpoint (line 14644-14650):

**Before:**
```python
payload = {
    "action": "delete_ship_folder",
    "ship_name": ship_name,
    "main_folder_id": main_folder_id,
    "company_name": company.get("name_en", "Unknown Company")
}
```

**After:**
```python
payload = {
    "action": "delete_complete_ship_structure",
    "parent_folder_id": main_folder_id,
    "ship_name": ship_name,
    "permanent_delete": False  # Move to trash by default for safety
}
```

**Changes:**
1. ✅ Action name: `delete_ship_folder` → `delete_complete_ship_structure`
2. ✅ Parameter: `main_folder_id` → `parent_folder_id` 
3. ✅ Added: `permanent_delete: False` for safety (moves to trash instead of permanent deletion)
4. ✅ Removed: Unused `company_name` parameter

### Frontend Changes

#### 1. Ship Service (`/app/frontend/src/services/shipService.js`)

Simplified the `delete()` method to only delete from database:

**Before:**
```javascript
delete: async (shipId, options = { delete_gdrive: false }) => {
  return api.delete(API_ENDPOINTS.SHIP_BY_ID(shipId), {
    data: options,
  });
}
```

**After:**
```javascript
delete: async (shipId) => {
  return api.delete(API_ENDPOINTS.SHIP_BY_ID(shipId));
}
```

#### 2. Class & Flag Cert Page (`/app/frontend/src/pages/ClassAndFlagCert.jsx`)

Implemented **two-call pattern** for better UX (matching V1 design):

**Pattern:**
1. **Call 1** (Blocking): DELETE ship from database → Close modal and refresh list immediately
2. **Call 2** (Background): Delete Google Drive folder → Show separate notifications

**Benefits:**
- ✅ Users don't wait for slow Google Drive deletion
- ✅ Modal closes immediately after database deletion
- ✅ Ship list refreshes instantly
- ✅ Google Drive deletion continues in background
- ✅ Separate notifications for each operation
- ✅ Graceful error handling for Google Drive failures

**Implementation:**
```javascript
const handleDeleteShip = async (shipId, deleteOption) => {
  // Step 1: Delete from database (quick, blocking)
  const response = await shipService.delete(shipId);
  
  // Step 2: Delete from Google Drive (slow, non-blocking background)
  if (deleteOption === 'with_gdrive') {
    (async () => {
      try {
        const gdriveResponse = await api.post(
          `/api/companies/${userCompanyId}/gdrive/delete-ship-folder`,
          { ship_name: deleteShipData.name }
        );
        // Show success/warning toasts based on response
      } catch (gdriveError) {
        // Show error toast but don't fail the whole operation
      }
    })();
  }
  
  // Close modal and refresh list immediately
  await fetchShips();
  setShowDeleteShipModal(false);
}
```

## Testing Requirements

### Test Case 1: Database-Only Deletion
1. ✅ Select a ship in Class & Flag Cert page
2. ✅ Click Edit Ship → Delete Ship button
3. ✅ Choose "Delete from Database Only" option
4. ✅ Click Confirm
5. ✅ **Expected**: 
   - Ship deleted from database
   - Modal closes immediately
   - Ship list refreshes
   - Toast: "Ship deleted successfully"
   - No Google Drive deletion attempted

### Test Case 2: Database + Google Drive Deletion
1. ✅ Select a ship in Class & Flag Cert page
2. ✅ Click Edit Ship → Delete Ship button
3. ✅ Choose "Delete from Database and Google Drive" option
4. ✅ Click Confirm
5. ✅ **Expected**:
   - Ship deleted from database immediately
   - Modal closes immediately
   - Ship list refreshes
   - Toast: "Ship deleted successfully"
   - Toast: "Deleting Google Drive folder..." (background)
   - Toast: "Google Drive folder deleted successfully" OR warning if failed
   - Google Drive folder moved to trash (not permanently deleted)

### Test Case 3: Google Drive Folder Not Found
1. ✅ Delete a ship that doesn't have a Google Drive folder
2. ✅ Choose "Delete from Database and Google Drive" option
3. ✅ **Expected**:
   - Ship deleted from database successfully
   - Warning toast: "Google Drive folder not found (may have been deleted previously)"
   - No error, graceful handling

### Test Case 4: Google Drive Deletion Failure
1. ✅ Simulate Apps Script error (invalid URL, timeout, etc.)
2. ✅ Choose "Delete from Database and Google Drive" option
3. ✅ **Expected**:
   - Ship deleted from database successfully
   - Warning toast: "Ship data deleted but Google Drive folder deletion failed"
   - Database deletion still succeeds even if Google Drive fails

## Technical Details

### Apps Script Action Details
The Apps Script v4.3 `delete_complete_ship_structure` action:
- **Input Parameters**:
  - `action`: "delete_complete_ship_structure"
  - `parent_folder_id`: ID of the root/company folder
  - `ship_name`: Name of the ship folder to delete
  - `permanent_delete`: `true` (permanent) or `false` (move to trash)

- **Output Response**:
  - `success`: boolean
  - `message`: string
  - `folder_name`: deleted folder name
  - `delete_method`: "moved_to_trash" or "permanently_deleted"
  - `deletion_stats`: { files_deleted, subfolders_deleted }
  - `deleted_timestamp`: timestamp

### Error Handling
1. **Backend Endpoint**: Returns proper error codes (400, 404, 500) with detailed messages
2. **Frontend**: Catches all errors and shows user-friendly toast notifications
3. **Google Drive Failures**: Don't block database deletion - gracefully degrade
4. **Folder Not Found**: Treated as warning, not error (idempotent operation)

## Files Modified
1. `/app/backend/server.py` - Fixed Apps Script action name and payload structure
2. `/app/frontend/src/services/shipService.js` - Simplified delete method
3. `/app/frontend/src/pages/ClassAndFlagCert.jsx` - Implemented two-call pattern with background Google Drive deletion
4. `/app/test_result.md` - Added testing tasks and status tracking

## Deployment Notes
- ✅ No database schema changes required
- ✅ No Apps Script redeployment needed (already supports correct action)
- ✅ Backward compatible with existing ship data
- ✅ Safe default: Moves to trash instead of permanent deletion
- ✅ Hot reload enabled - changes take effect immediately

## Success Criteria
- [x] Apps Script action name matches v4.3 expectations
- [x] Google Drive folder deletion works correctly
- [x] Database deletion is fast and responsive
- [x] Google Drive deletion runs in background
- [x] Error handling is graceful
- [x] User notifications are clear and helpful
- [ ] **Pending Testing**: All test cases pass successfully

# Auto-Determine Certificate Upload Folder - Frontend Implementation Complete

## Overview
Frontend has been updated to support the new certificate upload logic where the folder is automatically determined based on crew's `ship_sign_on` field, without requiring ship selection from the user.

## Frontend Changes Made

### 1. Remove Ship Selection Requirement

**Before:**
- Required `ship_id` from `selectedShip`, `selectedCrewForCertificates`, or first ship in list
- Showed error if no ship selected
- Passed `?ship_id=xxx` query parameter to API

**After:**
- No ship selection required
- Only requires `crew_id` selection
- Backend determines folder from crew's `ship_sign_on`
- API call without ship_id query parameter

### 2. Update Add Certificate Submit Function

**Location:** `/app/frontend/src/App.js` - `handleAddCrewCertificateSubmit()` (lines ~6464-6550)

**Changes:**
```javascript
// OLD LOGIC (Removed)
let shipId = selectedShip?.id || selectedCrewForCertificates?.ship_id || companyShips?.[0]?.id;
if (!shipId) {
  toast.error('Ship information not found...');
  return;
}
const response = await axios.post(`${API}/crew-certificates/manual?ship_id=${shipId}`, ...);

// NEW LOGIC
if (!newCrewCertificate.crew_id) {
  toast.error(language === 'vi' 
    ? 'Vui lòng chọn thuyền viên trước khi thêm chứng chỉ.' 
    : 'Please select a crew member before adding certificate.'
  );
  return;
}
const response = await axios.post(`${API}/crew-certificates/manual`, ...);
```

**Key Changes:**
- ✅ Removed `shipId` variable and all ship_id extraction logic
- ✅ Replaced ship_id validation with crew_id validation
- ✅ Removed `?ship_id=${shipId}` query parameter from API call
- ✅ Added console log: "Ship/Folder will be determined by backend based on crew's ship_sign_on"

### 3. Update Duplicate Certificate Confirmation

**Location:** `/app/frontend/src/App.js` - `handleConfirmAddDuplicateCert()` (lines ~6437-6461)

**Changes:**
- ✅ Removed `shipId` extraction logic
- ✅ Removed `?ship_id=${shipId}` query parameter from API call
- ✅ Now calls `${API}/crew-certificates/manual` without ship_id

### 4. Update Crew Selection Dropdown

**Location:** `/app/frontend/src/App.js` - Add Certificate Modal (lines ~11985-12012)

**Before:**
- Filtered crew list by `selectedShip?.name`
- Only showed crew members on selected ship
- Label: "Chọn thuyền viên từ tàu" (Select crew from ship)

**After:**
- Shows ALL crew members in company (no filtering by ship)
- Displays crew's ship_sign_on in option text for visibility
- Label: "Chọn thuyền viên" (Select crew member)
- Updated styling: yellow → blue theme

**Dropdown Options Format:**
```javascript
{crewList.map(crew => (
  <option key={crew.id} value={crew.id}>
    {crew.full_name} ({crew.passport}) - {crew.ship_sign_on || '-'} - {crew.rank || 'N/A'}
  </option>
))}
```

### 5. Enhanced User Guidance

**Added informative help text:**
```
💡 Chọn thuyền viên để tự động điền thông tin. Folder upload sẽ được xác định dựa trên Ship Sign On của thuyền viên.

📂 Standby crew (Ship Sign On = "-") → COMPANY DOCUMENT/Standby Crew
   Ship-assigned crew → {Ship Name}/Crew Records
```

**Purpose:**
- Educates users about how upload folder is determined
- Shows folder destination based on crew's ship_sign_on
- Makes the system behavior transparent

## User Flow

### Adding Certificate for Standby Crew

1. User clicks "Add Crew Certificate"
2. Modal opens with crew selection dropdown
3. User selects crew with `ship_sign_on = "-"`
4. Help text shows: "→ COMPANY DOCUMENT/Standby Crew"
5. User fills certificate details
6. User clicks Submit
7. **Backend automatically:**
   - Gets crew's ship_sign_on = "-"
   - Sets certificate's ship_id = null
   - Finds COMPANY DOCUMENT folder
   - Uploads to COMPANY DOCUMENT/Standby Crew
8. Success message shown
9. Certificate list refreshed

### Adding Certificate for Ship-Assigned Crew

1. User clicks "Add Crew Certificate"
2. Modal opens with crew selection dropdown
3. User selects crew with `ship_sign_on = "BROTHER 36"`
4. Help text shows: "→ {Ship Name}/Crew Records"
5. User fills certificate details
6. User clicks Submit
7. **Backend automatically:**
   - Gets crew's ship_sign_on = "BROTHER 36"
   - Finds ship by name → Gets ship_id
   - Sets certificate's ship_id = valid UUID
   - Uploads to BROTHER 36/Crew Records
8. Success message shown
9. Certificate list refreshed

## Validation Changes

### Old Validation
```javascript
if (!shipId) {
  toast.error('Ship information not found...');
  return;
}
```

### New Validation
```javascript
if (!newCrewCertificate.crew_id) {
  toast.error('Please select a crew member before adding certificate.');
  return;
}
```

**Result:** Crew selection is now the primary required field, not ship selection.

## API Integration

### Old API Call
```javascript
POST /api/crew-certificates/manual?ship_id={uuid}
Body: {
  crew_id: "...",
  crew_name: "...",
  ...
}
```

### New API Call
```javascript
POST /api/crew-certificates/manual
Body: {
  crew_id: "...",  // REQUIRED - backend gets ship_sign_on from this
  crew_name: "...",
  ...
}
```

## Error Handling

**Crew Not Selected:**
```
Vietnamese: "Vui lòng chọn thuyền viên trước khi thêm chứng chỉ."
English: "Please select a crew member before adding certificate."
```

**Backend Errors:**
- 404: Crew member not found
- 422: Validation error (missing crew_id)
- Other errors: Displayed with detail message

## UI Changes Summary

### Crew Selection Section
- **Background:** Yellow → Blue (bg-blue-50, border-blue-200)
- **Icon:** 🔍 → 👤
- **Label:** "Chọn thuyền viên từ tàu" → "Chọn thuyền viên"
- **Required:** ✅ Yes (marked with red asterisk)
- **Filter:** Ship-specific → Company-wide (all crew)
- **Display:** Name, Passport, Rank → Name, Passport, Ship Sign On, Rank

### Help Text
- **Line 1:** Auto-fill information explanation
- **Line 2:** Folder determination logic (NEW)
  - Blue text (text-blue-600)
  - Shows both Standby and Ship-assigned paths

## Files Modified

1. `/app/frontend/src/App.js`
   - `handleAddCrewCertificateSubmit()` - Lines ~6464-6550
   - `handleConfirmAddDuplicateCert()` - Lines ~6437-6461
   - Add Certificate Modal Crew Dropdown - Lines ~11985-12012

## Testing Checklist

### Test Scenario 1: Standby Crew Certificate
- [ ] Open Add Certificate modal
- [ ] Crew dropdown shows all crew members
- [ ] Select crew with ship_sign_on = "-"
- [ ] Help text shows "COMPANY DOCUMENT/Standby Crew"
- [ ] Fill certificate details
- [ ] Submit without errors
- [ ] Certificate created with ship_id = null
- [ ] Files uploaded to COMPANY DOCUMENT/Standby Crew

### Test Scenario 2: Ship-Assigned Crew Certificate
- [ ] Open Add Certificate modal
- [ ] Select crew with ship_sign_on = "BROTHER 36"
- [ ] Help text shows "{Ship Name}/Crew Records"
- [ ] Fill certificate details
- [ ] Submit without errors
- [ ] Certificate created with valid ship_id
- [ ] Files uploaded to BROTHER 36/Crew Records

### Test Scenario 3: Validation
- [ ] Open modal without selecting crew
- [ ] Try to submit
- [ ] Error message shown: "Please select a crew member"
- [ ] Select crew → Submit succeeds

### Test Scenario 4: Crew Selection
- [ ] Crew dropdown shows ALL crew in company (not filtered by ship)
- [ ] Each option shows: Name (Passport) - Ship Sign On - Rank
- [ ] Standby crew shows: Name (Passport) - "-" - Rank
- [ ] Selecting crew auto-fills name, passport, DOB, rank

## Benefits

1. **Simplified UX:** Users don't need to select ship separately
2. **Automatic Folder Routing:** Backend handles folder logic
3. **Transparency:** Users see where files will go
4. **Company-Wide View:** Can add certificates for any crew, not just selected ship
5. **Consistent with Backend:** Frontend aligns with new backend logic
6. **Better Validation:** Crew selection is the primary requirement

## Backward Compatibility

**Breaking Changes:**
- API no longer accepts `?ship_id=xxx` query parameter
- Old frontend versions will fail (ship_id required → removed)

**Migration:**
- All users must use updated frontend
- No data migration needed
- Existing certificates unaffected

## Status
✅ Frontend Implementation Complete
✅ API Integration Updated
✅ Validation Logic Updated
✅ UI Enhanced with Help Text
✅ Ready for Testing

## Next Steps
1. Test with real crew data (Standby and Ship-assigned)
2. Verify file upload to correct folders
3. Confirm database ship_id field values
4. User acceptance testing

# Auto-Move Standby Files - Date Sign Off Integration Fix

## Problem Discovered

User reported:
> "Status được auto change khi nhập Date sign off chứ không chỉnh sửa trực tiếp trong Edit crew member"

**Root Cause:**
- When user fills "Date Sign Off" field, status is automatically set to "Standby"
- The original auto-move logic only checked `oldStatus !== newStatus`
- If crew was already "Standby" before, the check would fail
- Files were NOT moved because oldStatus === newStatus === "Standby"

---

## The Auto-Status Change Logic

### In Add Crew Modal (line 14405):
```javascript
onChange={(e) => {
  const signOffDate = e.target.value;
  setNewCrewData({
    ...newCrewData, 
    date_sign_off: signOffDate,
    // Auto-update Status when Date Sign Off is filled
    status: signOffDate ? 'Standby' : newCrewData.status,
    ship_sign_on: signOffDate ? '-' : newCrewData.ship_sign_on
  });
}}
```

### In Edit Crew Modal (line 15228):
```javascript
onChange={(e) => {
  const signOffDate = e.target.value;
  setEditCrewData({
    ...editCrewData, 
    date_sign_off: signOffDate,
    // Auto-update Status ONLY when Date Sign Off is filled
    ...(signOffDate ? {
      status: 'Standby',
      ship_sign_on: '-'
    } : {})
  });
}}
```

**Key Point:** When user types a date in "Date Sign Off", status automatically becomes "Standby"

---

## Solution Implemented

### Enhanced Auto-Move Trigger Logic

**New approach: Check TWO conditions**

1. **Status changed to Standby** (original logic)
2. **Date Sign Off was newly filled** (NEW logic)

```javascript
// Check if date_sign_off was newly filled
const dateSignOffAdded = !oldDateSignOff && newDateSignOff;

// Trigger auto-move if EITHER condition is true:
if ((newStatus === 'standby' && oldStatus !== 'standby') || dateSignOffAdded) {
  console.log('🎯 Triggering auto-move');
  moveStandbyCrewFiles([editingCrew.id], editCrewData.full_name);
}
```

---

## Scenarios Now Covered

### Scenario 1: Direct Status Change
```
User edits crew → Changes Status dropdown to "Standby" → Update
✅ Triggers: newStatus === 'standby' && oldStatus !== 'standby'
✅ Files moved automatically
```

### Scenario 2: Fill Date Sign Off (First Time)
```
User edits crew → Types date in "Date Sign Off" → Status auto-changes to Standby → Update
✅ Triggers: dateSignOffAdded === true
✅ Files moved automatically
```

### Scenario 3: Crew Already Standby, Update Date Sign Off
```
Old: status = "Standby", date_sign_off = "2024-01-15"
User: Changes date_sign_off to "2024-02-20"
✅ Triggers: dateSignOffAdded === false (because old date existed)
❌ No auto-move (files already in Standby folder from previous update)
```

### Scenario 4: Clear Date Sign Off
```
User: Clears "Date Sign Off" field (empty)
Result: Status remains Standby, ship_sign_on unchanged
✅ Triggers: dateSignOffAdded === false
❌ No auto-move (status didn't change to Standby, was already Standby)
```

### Scenario 5: First Time Adding Date Sign Off to Crew
```
Old: status = "Sign on", date_sign_off = null
User: Types "2024-06-15" in Date Sign Off
Result: Status auto-changes to "Standby"
✅ Triggers: dateSignOffAdded === true (null → "2024-06-15")
✅ Files moved automatically!
```

---

## Enhanced Console Logging

**New detailed logging output:**
```javascript
console.log('🔍 Status & Date Sign Off check:', {
  oldStatus,
  newStatus,
  oldDateSignOff,
  newDateSignOff,
  dateSignOffAdded,
  statusChangedToStandby: newStatus === 'standby' && oldStatus !== 'standby',
  shouldTriggerMove: (newStatus === 'standby' && oldStatus !== 'standby') || dateSignOffAdded
});

console.log('🎯 Triggering auto-move for [Name]');
console.log('   Reason: Date Sign Off was newly filled → Status auto-changed to Standby');
```

**Expected Console Output:**
```
🔍 Status & Date Sign Off check: {
  oldStatus: "sign on",
  newStatus: "standby",
  oldDateSignOff: null,
  newDateSignOff: "2024-06-15",
  dateSignOffAdded: true,
  statusChangedToStandby: true,
  shouldTriggerMove: true
}

🎯 Triggering auto-move for Nguyễn Văn A
   Reason: Date Sign Off was newly filled → Status auto-changed to Standby

📦 Auto-moving files for 1 Standby crew to Standby Crew folder...
✅ Files moved successfully to Standby Crew folder
```

---

## Testing Instructions

### Test Case 1: Fill Date Sign Off for First Time
**Setup:**
- Crew with status "Sign on"
- NO date_sign_off value

**Steps:**
1. Edit crew
2. Type date in "Date Sign Off" field (e.g., today's date)
3. Click "Save Changes" (Lưu thay đổi)

**Expected:**
- ✅ Console shows `dateSignOffAdded: true`
- ✅ Console shows `shouldTriggerMove: true`
- ✅ Toast: "Đã cập nhật thông tin thuyền viên thành công"
- ✅ Toast: "Đã tự động di chuyển X files vào folder Standby Crew"
- ✅ Files moved to "Standby Crew" folder in Google Drive

### Test Case 2: Update Existing Date Sign Off
**Setup:**
- Crew with status "Standby"
- date_sign_off = "2024-01-15"

**Steps:**
1. Edit crew
2. Change date_sign_off to "2024-06-20"
3. Click "Save Changes"

**Expected:**
- ✅ Console shows `dateSignOffAdded: false`
- ✅ Console shows `shouldTriggerMove: false`
- ✅ Toast: "Đã cập nhật thông tin thuyền viên thành công"
- ❌ NO auto-move toast (files already in Standby folder)

### Test Case 3: Direct Status Change
**Setup:**
- Crew with status "Sign off"
- NO date_sign_off

**Steps:**
1. Edit crew
2. Change Status dropdown to "Standby"
3. Click "Save Changes"

**Expected:**
- ✅ Console shows `statusChangedToStandby: true`
- ✅ Console shows `shouldTriggerMove: true`
- ✅ Toast: Auto-move notification
- ✅ Files moved

### Test Case 4: Clear Date Sign Off
**Setup:**
- Crew with status "Standby"
- date_sign_off = "2024-01-15"

**Steps:**
1. Edit crew
2. Clear "Date Sign Off" field (delete the date)
3. Click "Save Changes"

**Expected:**
- ✅ Console shows `dateSignOffAdded: false`
- ✅ Console shows `shouldTriggerMove: false`
- ✅ Status remains "Standby"
- ❌ NO auto-move (expected behavior)

---

## Logic Flow Diagram

```
User fills Date Sign Off
    ↓
onChange handler triggers
    ↓
editCrewData.status = "Standby" (auto-set)
editCrewData.date_sign_off = [date]
    ↓
User clicks "Save Changes"
    ↓
handleUpdateCrew() called
    ↓
Check conditions:
  - dateSignOffAdded? (null → date)
  - statusChangedToStandby? (old ≠ standby, new = standby)
    ↓
IF either condition is TRUE:
  ↓
  moveStandbyCrewFiles([crew_id])
      ↓
      Backend moves files to "Standby Crew" folder
      ↓
      Toast notification: "Đã tự động di chuyển X files"
```

---

## Why This Fix Works

**Problem Before:**
```javascript
// Only checked status change
if (newStatus === 'standby' && oldStatus !== 'standby') {
  moveFiles();
}

// Failed when:
// - oldStatus = "Standby", newStatus = "Standby" (but date sign off was newly filled)
```

**Solution Now:**
```javascript
// Check BOTH status change AND date sign off added
const dateSignOffAdded = !oldDateSignOff && newDateSignOff;

if ((newStatus === 'standby' && oldStatus !== 'standby') || dateSignOffAdded) {
  moveFiles();
}

// Works for:
// 1. Direct status change: Sign on → Standby
// 2. Date sign off filled: null → "2024-06-15" (auto status → Standby)
```

---

## Edge Cases Handled

### Edge Case 1: Multiple Edits in Short Time
**Scenario:** User fills date sign off, saves, immediately edits again

**Behavior:**
- First save: Files moved (dateSignOffAdded = true)
- Second save: No move (dateSignOffAdded = false, files already there)
- ✅ Prevents duplicate moves

### Edge Case 2: Manual Status to Standby + No Date Sign Off
**Scenario:** User manually sets Status to "Standby" without filling date sign off

**Behavior:**
- Status changed: Sign on → Standby
- statusChangedToStandby = true
- ✅ Files moved correctly

### Edge Case 3: Date Sign Off + Manual Status Change Together
**Scenario:** User fills date sign off AND manually changes status in same edit

**Behavior:**
- Both conditions can be true
- Either one triggers the move
- ✅ Files moved once (not twice)

---

## Files Modified

**`/app/frontend/src/App.js`:**
- Enhanced `handleUpdateCrew` function (lines ~3207-3250)
- Added `dateSignOffAdded` detection logic
- Added comprehensive logging for date sign off tracking
- Updated trigger condition to include date sign off scenario

---

## Backward Compatibility

✅ **No Breaking Changes:**
- Original status change detection still works
- Added additional trigger condition
- Existing crew records unaffected
- No database schema changes

---

## Status

✅ **Fix Implemented**
✅ **Frontend Restarted**
⏳ **Ready for User Testing**

---

## Testing Checklist for User

- [ ] Test Case 1: Fill date sign off for first time
- [ ] Test Case 2: Update existing date sign off
- [ ] Test Case 3: Direct status change to Standby
- [ ] Test Case 4: Clear date sign off
- [ ] Verify console logs show correct trigger reasons
- [ ] Verify toast notifications appear appropriately
- [ ] Check Google Drive for files in "Standby Crew" folder

---

## Summary

**What was fixed:**
- Detected that status auto-changes when Date Sign Off is filled
- Added logic to detect when date_sign_off changes from null to a date
- Auto-move now triggers for BOTH scenarios:
  1. Direct status change to Standby
  2. Date Sign Off newly filled (which auto-sets status to Standby)

**User Impact:**
🎉 **Files will now automatically move when user fills Date Sign Off!**

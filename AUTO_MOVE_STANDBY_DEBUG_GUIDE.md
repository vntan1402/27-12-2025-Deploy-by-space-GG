# Auto-Move Standby Files - Debug Guide

## Issue Reported

User changed existing crew status to "Standby" but:
- ❌ Files were NOT automatically moved
- ❌ No toast notifications appeared

## Debug Changes Implemented

### 1. Enhanced Console Logging

**Added detailed logging in `handleUpdateCrew`:**
```javascript
console.log('🔍 Status check:', {
  oldStatus,
  newStatus,
  editingCrew_status: editingCrew.status,
  editCrewData_status: editCrewData.status,
  shouldTrigger: newStatus === 'standby' && oldStatus !== 'standby'
});
```

**Purpose:** See exactly what status values are being compared

---

### 2. Enhanced `moveStandbyCrewFiles` Logging

**Added comprehensive logging:**
```javascript
console.log(`📦 Auto-moving files for ${crewIds.length} Standby crew...`);
console.log('   Crew IDs:', crewIds);
console.log('   Crew Name:', crewName);
console.log('   API URL:', `${API}/crew/move-standby-files`);
console.log('📡 Move files API response:', response);
console.log('📦 Response data:', response.data);
```

**Purpose:** Track the entire API call flow

---

### 3. Better Error Messages

**Added info toast for no files:**
```javascript
if (response.data.moved_count === 0) {
  toast.info('Thuyền viên chưa có files để di chuyển');
}
```

**Added warning toast for API failures:**
```javascript
if (!response.data.success) {
  toast.warning('Không thể di chuyển files. Vui lòng kiểm tra logs.');
}
```

---

## Testing Instructions

### Step 1: Open Browser Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Clear console

### Step 2: Change Crew Status to Standby
1. Edit a crew member with status "Sign on" or "Sign off"
2. Change Status dropdown to "Standby"
3. Click "Update" (Cập nhật)

### Step 3: Check Console Output

**Expected console logs:**
```
🔍 Status check: {
  oldStatus: "sign on",
  newStatus: "standby",
  editingCrew_status: "Sign on",
  editCrewData_status: "Standby",
  shouldTrigger: true
}

🎯 Status changed to Standby for Nguyễn Văn A, auto-moving files...

📦 Auto-moving files for 1 Standby crew to Standby Crew folder...
   Crew IDs: ["crew-uuid-123"]
   Crew Name: Nguyễn Văn A
   API URL: http://localhost:8001/api/crew/move-standby-files

📡 Move files API response: {data: {...}, status: 200, ...}
📦 Response data: {success: true, moved_count: 2, message: "..."}

✅ Files moved successfully to Standby Crew folder
```

### Step 4: Check Toast Notifications

**Expected toasts:**
1. ✅ "Đã cập nhật thông tin thuyền viên thành công"
2. ✅ "Đã tự động di chuyển 2 files của Nguyễn Văn A vào folder Standby Crew"

OR (if no files):
1. ✅ "Đã cập nhật thông tin thuyền viên thành công"
2. ℹ️ "Nguyễn Văn A chưa có files để di chuyển"

---

## Common Issues & Solutions

### Issue 1: shouldTrigger = false

**Console shows:**
```
🔍 Status check: {
  oldStatus: "standby",
  newStatus: "standby",
  shouldTrigger: false
}
```

**Cause:** Crew status was already "Standby"

**Solution:** This is expected behavior. Files should have been moved previously.

---

### Issue 2: Status values don't match

**Console shows:**
```
🔍 Status check: {
  oldStatus: "sign on",
  newStatus: "sign on",
  shouldTrigger: false
}
```

**Cause:** Status didn't actually change in `editCrewData`

**Solution:** 
1. Check if status dropdown is bound correctly
2. Verify `editCrewData.status` is being updated on dropdown change

---

### Issue 3: API call fails

**Console shows:**
```
❌ Error auto-moving Standby crew files: AxiosError
   Error response: {status: 401, ...}
```

**Cause:** Authentication issue or backend error

**Solutions:**
1. Check if token is valid
2. Check backend logs: `tail -f /var/log/supervisor/backend.out.log`
3. Verify backend endpoint is accessible

---

### Issue 4: moved_count = 0

**Console shows:**
```
📦 Response data: {success: true, moved_count: 0, ...}
ℹ️ No files to move (crew may not have passport/certificate files yet)
```

**Cause:** Crew has no passport or certificates uploaded

**Solution:** 
1. Upload passport for the crew
2. Add certificates for the crew
3. Try changing status again

---

### Issue 5: Crew not found in backend

**Backend logs show:**
```
⚠️ Crew crew-uuid-123 not found
```

**Cause:** Crew ID mismatch or crew doesn't exist in database

**Solution:**
1. Check crew exists in database
2. Verify crew ID in API call
3. Check company_id matching

---

## Backend Debugging

### Check Backend Logs
```bash
# Follow logs in real-time
tail -f /var/log/supervisor/backend.out.log

# Search for move-related logs
tail -n 200 /var/log/supervisor/backend.out.log | grep -i "move.*file\|standby"

# Check for errors
tail -n 200 /var/log/supervisor/backend.err.log
```

### Expected Backend Logs

**Successful move:**
```
📦 Moving files for 1 Standby crew members to Standby Crew folder...
🔍 Calling Apps Script to list folders in parent: ...
✅ MATCH FOUND! Standby Crew folder: 1KU_1o-FcY3g2O9dKO5xxPhv1P2u56aO6
📦 Processing Standby crew: Nguyễn Văn A
📁 Moving 2 ORIGINAL files for Nguyễn Văn A...
✅ Moved passport file: file-id-123
✅ Moved certificate file: file-id-456
✅ Moved 2 files to Standby Crew folder
```

**No files to move:**
```
📦 Processing Standby crew: Nguyễn Văn A
ℹ️ No original files to move for Nguyễn Văn A
✅ Moved 0 files to Standby Crew folder
```

---

## Manual Testing Checklist

### Test Case 1: Crew with Files
- [ ] Crew has passport uploaded
- [ ] Crew has at least 1 certificate
- [ ] Change status from "Sign on" to "Standby"
- [ ] Verify console shows status change detected
- [ ] Verify API call is made
- [ ] Verify toast shows files moved
- [ ] Check Google Drive - files in "Standby Crew" folder

### Test Case 2: Crew without Files
- [ ] Crew has NO passport
- [ ] Crew has NO certificates
- [ ] Change status to "Standby"
- [ ] Verify console shows status change detected
- [ ] Verify API call is made
- [ ] Verify toast shows "no files to move"

### Test Case 3: Already Standby
- [ ] Crew already has status "Standby"
- [ ] Edit some other field (e.g., rank)
- [ ] Keep status as "Standby"
- [ ] Verify console shows shouldTrigger = false
- [ ] Verify NO auto-move triggered

---

## What to Check if Still Not Working

### 1. Check Status Field Binding
```javascript
// In editCrewData, verify status field exists
console.log('editCrewData:', editCrewData);
console.log('status value:', editCrewData.status);
```

### 2. Check Token
```javascript
// Verify token is available
console.log('Token:', token ? 'exists' : 'missing');
```

### 3. Check Backend Response
```javascript
// Look at full response structure
console.log('Full response:', response);
```

### 4. Check Network Tab
1. Open DevTools → Network tab
2. Filter: "move-standby-files"
3. Look for the API call
4. Check:
   - Request sent? (should see POST request)
   - Request payload? (should have crew_ids)
   - Response status? (should be 200)
   - Response data? (should have success: true)

---

## Files Modified

**`/app/frontend/src/App.js`:**
- Enhanced `handleUpdateCrew` with detailed status logging
- Enhanced `moveStandbyCrewFiles` with comprehensive API logging
- Added info toast for no files case
- Added warning toast for API failure case
- Added `.trim()` to status comparison for safety

---

## Status

✅ **Debug Logging Added**
✅ **Frontend Restarted**
⏳ **Awaiting User to Test with Enhanced Logs**

---

## Next Steps for User

1. **Test the feature again** with browser console open
2. **Copy console output** showing the logs
3. **Share the logs** so we can diagnose the exact issue
4. **Check toast notifications** that appear
5. **Check backend logs** if needed

The enhanced logging will reveal exactly where the process is failing!

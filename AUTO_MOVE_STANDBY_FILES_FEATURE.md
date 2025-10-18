# Tính năng Tự động Di chuyển Files vào Standby Crew Folder

## Tổng quan

Hệ thống giờ đây **TỰ ĐỘNG** di chuyển passport và crew certificate files vào folder "Standby Crew" khi:
1. User tạo mới crew member với status "Standby"
2. User thay đổi status của crew sang "Standby"

## Chi tiết Thay đổi

### 1. Helper Function: `moveStandbyCrewFiles`

**Vị trí:** `/app/frontend/src/App.js` (lines ~3042-3078)

**Chức năng:**
- Gọi backend API `/crew/move-standby-files` để di chuyển files
- Chạy async trong background (không block UI)
- Hiển thị toast notification thành công
- Không hiển thị error toast nếu fail (để không làm phiền user workflow)

**Tham số:**
- `crewIds`: Array of crew IDs cần di chuyển files
- `crewName`: (Optional) Tên crew để hiển thị trong notification

```javascript
const moveStandbyCrewFiles = async (crewIds, crewName = null) => {
  // Gọi API /crew/move-standby-files
  // Hiển thị toast success nếu có files được di chuyển
  // Log error nhưng không show error toast (background operation)
}
```

### 2. Auto-trigger khi Update Crew Status

**Vị trí:** `/app/frontend/src/App.js` - `handleUpdateCrew` function

**Logic:**
```javascript
// So sánh old status vs new status
const oldStatus = editingCrew.status ? editingCrew.status.toLowerCase() : '';
const newStatus = editCrewData.status ? editCrewData.status.toLowerCase() : '';

// Nếu status changed to "Standby" → Auto move files
if (newStatus === 'standby' && oldStatus !== 'standby') {
  moveStandbyCrewFiles([editingCrew.id], editCrewData.full_name);
}
```

**Khi nào trigger:**
- Old status: bất kỳ (Sign on, Sign off, etc.)
- New status: "Standby" (case-insensitive)
- Chỉ trigger khi có sự thay đổi (không trigger nếu đã là Standby)

### 3. Auto-trigger khi Add New Crew

**Vị trí:** `/app/frontend/src/App.js` - `handleAddCrewSubmit` function

**Logic:**
```javascript
// Check status của crew mới
const crewStatus = newCrewData.status ? newCrewData.status.toLowerCase() : '';

// Nếu status là "Standby" → Auto move files
if (crewStatus === 'standby') {
  moveStandbyCrewFiles([crewId], newCrewData.full_name);
}
```

**Khi nào trigger:**
- Crew mới được tạo thành công
- Status của crew là "Standby" (case-insensitive)
- Chạy sau khi passport files đã được upload (nếu có)

## User Experience Flow

### Scenario 1: Tạo Crew Mới với Status "Standby"

```
1. User mở "Add Crew" modal
2. User điền thông tin crew
3. User chọn Status = "Standby"
4. User upload passport (nếu có)
5. User click "Submit"
   ↓
6. ✅ Crew được tạo trong database
7. ✅ Passport files uploaded to Drive (nếu có)
8. ✅ Crew list refreshed
9. 🎯 AUTO: Files tự động di chuyển vào "Standby Crew" folder
10. ✅ Toast: "Đã tự động di chuyển X files của [Tên crew] vào folder Standby Crew"
11. ✅ Modal đóng
```

### Scenario 2: Thay đổi Status sang "Standby"

```
1. User click Edit trên crew member (status hiện tại: "Sign on")
2. User thay đổi Status từ "Sign on" → "Standby"
3. User click "Update"
   ↓
4. ✅ Crew updated trong database
5. ✅ Crew list refreshed
6. 🎯 AUTO: Files tự động di chuyển vào "Standby Crew" folder
7. ✅ Toast: "Đã cập nhật thông tin thuyền viên thành công"
8. ✅ Toast: "Đã tự động di chuyển X files của [Tên crew] vào folder Standby Crew"
9. ✅ Modal đóng
```

## Files được Di chuyển

Backend chỉ di chuyển **ORIGINAL files**:
- ✅ Passport original file (`passport_file_id`)
- ✅ Crew Certificate original files (`crew_cert_file_id`)
- ❌ KHÔNG di chuyển summary files (vẫn ở ship folder để dễ reference)

## Folder Structure

```
Google Drive (Company Drive)
└── COMPANY DOCUMENT
    ├── <Ship Name>/
    │   ├── Passport/
    │   │   └── summary files (không bị di chuyển)
    │   └── Certificates/
    │       └── summary files (không bị di chuyển)
    │
    └── Standby Crew/  ← Files của Standby crew được tự động di chuyển vào đây
        ├── [Crew Name]_passport.pdf
        └── [Crew Name]_[Cert Name].pdf
```

## Error Handling

### Silent Background Operation
- Function `moveStandbyCrewFiles` chạy async trong background
- Không dùng `await` → không block UI
- Nếu có error: log to console, KHÔNG hiển thị error toast
- Lý do: đây là background operation, không nên làm gián đoạn user workflow

### Success Notification
- Chỉ hiển thị toast success khi có files thực sự được di chuyển
- Nếu `moved_count = 0` (crew chưa có files): không hiển thị toast

### Graceful Degradation
- Nếu API call fail: crew vẫn được create/update thành công
- Files có thể được di chuyển sau bằng cách click nút "Refresh" (fallback)

## Backend API

**Endpoint:** `POST /api/crew/move-standby-files`

**Request Body:**
```json
{
  "crew_ids": ["crew-uuid-1", "crew-uuid-2"]
}
```

**Response:**
```json
{
  "success": true,
  "moved_count": 5,
  "message": "Moved 5 files successfully"
}
```

## Testing Instructions

### Test Case 1: Add New Crew with Standby Status
1. Login to application
2. Navigate to Crew Management
3. Click "Add Crew" (Thêm thuyền viên)
4. Fill in crew information
5. Upload passport file
6. **Set Status = "Standby"**
7. Click Submit
8. **Expected:** 
   - Crew created successfully
   - Toast: "Thuyền viên đã được thêm thành công!"
   - Toast: "Đã tự động di chuyển X files của [Tên] vào folder Standby Crew"
   - Check Google Drive: files should be in "Standby Crew" folder

### Test Case 2: Change Status to Standby
1. Login to application
2. Navigate to Crew Management
3. Click Edit on a crew member with status "Sign on"
4. **Change Status from "Sign on" to "Standby"**
5. Click Update
6. **Expected:**
   - Crew updated successfully
   - Toast: "Đã cập nhật thông tin thuyền viên thành công"
   - Toast: "Đã tự động di chuyển X files của [Tên] vào folder Standby Crew"
   - Check Google Drive: files moved to "Standby Crew" folder

### Test Case 3: Edit Standby Crew (No Re-move)
1. Login to application
2. Navigate to Crew Management
3. Click Edit on a crew member already with status "Standby"
4. Change some other field (e.g., rank, date_sign_off)
5. **Keep Status = "Standby"** (no change)
6. Click Update
7. **Expected:**
   - Crew updated successfully
   - Toast: "Đã cập nhật thông tin thuyền viên thành công"
   - **NO auto-move toast** (status didn't change)
   - Files remain in "Standby Crew" folder

### Test Case 4: New Crew without Files
1. Add new crew with Status = "Standby"
2. Do NOT upload passport
3. Click Submit
4. **Expected:**
   - Crew created successfully
   - Toast: "Thuyền viên đã được thêm thành công!"
   - **NO auto-move toast** (no files to move yet)

## Logs để Monitor

**Frontend Console:**
```javascript
🎯 Status changed to Standby for [Crew Name], auto-moving files...
📦 Auto-moving files for 1 Standby crew to Standby Crew folder...
✅ Files moved successfully to Standby Crew folder: {...}
ℹ️ No files to move (crew may not have passport/certificate files yet)
```

**Backend Logs:**
```
📦 Moving files for 1 Standby crew members to Standby Crew folder...
🔍 Calling Apps Script to list folders in parent: <FOLDER_ID>
✅ MATCH FOUND! Standby Crew folder: <FOLDER_ID>
📁 Moving 2 ORIGINAL files for [Crew Name] (no summaries)...
✅ File moved successfully!
```

## Benefits

1. ✅ **Automatic Process:** User không cần nhớ click "Refresh"
2. ✅ **Immediate:** Files được di chuyển ngay sau khi status change
3. ✅ **User-friendly:** Toast notifications rõ ràng
4. ✅ **Non-blocking:** Chạy background, không làm chậm UI
5. ✅ **Safe:** Crew create/update vẫn thành công dù file move fail
6. ✅ **Smart:** Chỉ trigger khi status THAY ĐỔI sang Standby

## Files Modified

- `/app/frontend/src/App.js`:
  - Added `moveStandbyCrewFiles` helper function
  - Modified `handleUpdateCrew` to auto-trigger file move on status change
  - Modified `handleAddCrewSubmit` to auto-trigger file move for new Standby crew

## Backward Compatibility

- ✅ Manual "Refresh" button vẫn hoạt động như cũ
- ✅ Không breaking changes
- ✅ Existing crews với status "Standby": files vẫn có thể di chuyển bằng "Refresh"

## Status

✅ **Implementation Complete**
✅ **Frontend Restarted**
⏳ **Awaiting User Testing**

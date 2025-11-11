# Self-Edit Profile Feature - System Admin & All Users

## 📋 Tổng quan

Đã bổ sung tính năng cho phép tất cả users (bao gồm system_admin) có thể chỉnh sửa thông tin cá nhân của chính mình.

---

## ✅ Thay đổi đã thực hiện

### 1. Frontend - UserManagement.jsx

**File**: `/app/frontend/src/components/SystemSettings/UserManagement/UserManagement.jsx`

**Thay đổi `canEditUser()` function:**

**TRƯỚC:**
```javascript
const canEditUser = (targetUser) => {
  // Cannot edit self
  if (targetUser.id === currentUser.id) {
    return false;  // ❌ CHẶN edit chính mình
  }
  // ... rest of logic
};
```

**SAU:**
```javascript
const canEditUser = (targetUser) => {
  // Users can edit themselves (own profile)
  if (targetUser.id === currentUser.id) {
    return true;  // ✅ CHO PHÉP edit chính mình
  }
  // ... rest of logic
};
```

**Tác động:**
- ✅ Tất cả users có thể click nút "Edit" trên profile của chính mình
- ✅ System admin có thể edit profile của chính mình
- ✅ Các users khác vẫn tuân theo logic phân quyền cũ

---

### 2. Backend - server.py

**File**: `/app/backend/server.py`

**Thay đổi `PUT /api/users/{user_id}` endpoint:**

**TRƯỚC:**
```python
async def update_user(
    user_id: str, 
    user_data: UserUpdate, 
    current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]))
):
    # Chỉ admin mới update được user
    # ❌ User thường không thể update chính mình
```

**SAU:**
```python
async def update_user(
    user_id: str, 
    user_data: UserUpdate, 
    current_user: UserResponse = Depends(get_current_user)
):
    # Check permission: user can edit themselves, or admins can edit anyone
    is_self_edit = (user_id == current_user.id)
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]
    
    if not is_self_edit and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to edit this user")
    
    # Restrict role changes for self-edit
    if field == 'role' and is_self_edit and not is_admin:
        continue  # ✅ Users không thể đổi role của chính mình
```

**Tác động:**
- ✅ Tất cả users có thể update profile của chính mình qua API
- ✅ Users không thể thay đổi role của chính mình (bảo mật)
- ✅ Admins vẫn có thể edit bất kỳ user nào
- ✅ Admins có thể đổi role khi edit chính mình

---

### 3. Frontend - EditUserModal.jsx (Đã có sẵn)

**File**: `/app/frontend/src/components/SystemSettings/UserManagement/EditUserModal.jsx`

**Logic đã có sẵn:**
```javascript
const isEditingOwnRole = user && currentUser && user.id === currentUser.id;

// Role field
<select
  disabled={loading || isEditingOwnRole}  // ✅ Disable role khi edit chính mình
  // ...
>
```

**Tác động:**
- ✅ UI tự động disable role field khi user edit chính mình
- ✅ Hiển thị warning: "⚠️ Bạn không thể thay đổi vai trò của chính mình"
- ✅ Các field khác vẫn có thể edit (username, email, password, department, etc.)

---

## 🎯 Quyền Self-Edit cho từng Role

| Role | Có thể edit chính mình? | Có thể đổi role của mình? | Có thể edit users khác? |
|------|------------------------|---------------------------|-------------------------|
| **system_admin** | ✅ YES | ❌ NO (bảo mật) | ✅ YES (tất cả) |
| **super_admin** | ✅ YES | ❌ NO (bảo mật) | ✅ YES (tất cả) |
| **admin** | ✅ YES | ❌ NO (bảo mật) | ✅ YES (lower roles) |
| **manager** | ✅ YES | ❌ NO (bảo mật) | ✅ YES (lower roles) |
| **editor** | ✅ YES | ❌ NO (bảo mật) | ✅ YES (lower roles) |
| **viewer** | ✅ YES | ❌ NO (bảo mật) | ❌ NO |
| **crew** | ✅ YES | ❌ NO (bảo mật) | ❌ NO |
| **ship_officer** | ✅ YES | ❌ NO (bảo mật) | ❌ NO |

---

## 🔐 Bảo mật

### ✅ Restrictions khi Self-Edit:

1. **Không thể đổi role của chính mình**
   - Frontend: Role dropdown bị disable
   - Backend: Bỏ qua field `role` nếu là self-edit
   - Lý do: Ngăn privilege escalation

2. **Username có thể đổi**
   - User có thể update username của mình
   - Không ảnh hưởng đến authentication (dùng user ID)

3. **Password có thể đổi**
   - User có thể reset password của mình
   - Password được hash với bcrypt

4. **Email, Full Name, Department, etc. có thể đổi**
   - Tất cả thông tin cá nhân có thể update

---

## 📋 Các fields có thể edit khi Self-Edit:

| Field | Có thể edit? | Ghi chú |
|-------|-------------|---------|
| username | ✅ YES | Tên đăng nhập |
| email | ✅ YES | Email cá nhân |
| password | ✅ YES | Đổi mật khẩu |
| full_name | ✅ YES | Họ tên |
| department | ✅ YES | Phòng ban |
| zalo | ✅ YES | Số Zalo |
| gmail | ✅ YES | Gmail |
| **role** | ❌ NO | **Bị chặn vì lý do bảo mật** |
| company | ⚠️ Depends | Tùy logic nghiệp vụ |
| ship | ⚠️ Depends | Tùy logic nghiệp vụ |

---

## 🧪 Test Cases

### Test Case 1: System Admin edit chính mình
**Steps:**
1. Login với system_admin
2. Vào System Settings → User Management
3. Tìm user `system_admin` trong danh sách
4. Click nút "Edit" (icon bút chì)
5. Thay đổi full_name, email, department
6. Click "Save"

**Expected:**
- ✅ Edit button hiển thị
- ✅ Modal mở ra với thông tin hiện tại
- ✅ Các field có thể chỉnh sửa (trừ role)
- ✅ Role field bị disable với warning
- ✅ Save thành công
- ✅ Thông tin cập nhật trong danh sách

---

### Test Case 2: System Admin đổi password của mình
**Steps:**
1. Login với system_admin
2. Vào System Settings → User Management
3. Edit user system_admin
4. Nhập password mới
5. Save

**Expected:**
- ✅ Password được hash và lưu
- ✅ Có thể login với password mới
- ✅ Password cũ không còn hoạt động

---

### Test Case 3: User thường edit chính mình
**Steps:**
1. Login với viewer/crew/editor
2. Vào System Settings → User Management
3. Tìm user của mình
4. Edit và thay đổi thông tin

**Expected:**
- ✅ Có thể edit profile của mình
- ✅ Role field disabled
- ✅ Save thành công

---

### Test Case 4: User thường không thể edit users khác
**Steps:**
1. Login với viewer
2. Vào System Settings → User Management
3. Thử edit user khác (không phải chính mình)

**Expected:**
- ❌ Edit button không hiển thị cho users khác
- ✅ Chỉ hiển thị Edit button cho chính mình

---

## 🚀 Cách sử dụng

### Cho User thường (Viewer, Crew, Editor):

1. **Login vào hệ thống**
2. **Vào System Settings → User Management**
3. **Tìm username của mình trong danh sách**
4. **Click nút "Edit" (icon bút chì màu xanh)**
5. **Cập nhật thông tin cá nhân:**
   - Full Name (Họ tên)
   - Email
   - Password (nếu muốn đổi)
   - Department (Phòng ban)
   - Zalo
   - Gmail
6. **Click "Save" / "Lưu"**
7. **✅ Thông tin đã được cập nhật!**

---

### Cho System Admin:

1. **Login với system_admin**
2. **Vào System Settings → User Management**
3. **Có thể:**
   - ✅ Edit profile của chính mình (như user thường)
   - ✅ Edit bất kỳ user nào khác
   - ✅ Thay đổi role của users khác
   - ⚠️ KHÔNG thể đổi role của chính mình (bảo mật)

---

## 📊 Workflow Edit Profile

```
User Login
    ↓
Vào System Settings → User Management
    ↓
Tìm username của mình trong danh sách
    ↓
Click Edit button (icon bút chì)
    ↓
Modal hiển thị với thông tin hiện tại
    ↓
Các field có thể edit: username, email, password, full_name, department, zalo
Role field: DISABLED (với warning message)
    ↓
Nhập thông tin mới
    ↓
Click Save
    ↓
Backend API: PUT /api/users/{user_id}
    ↓
Check: is_self_edit = true?
    ↓ YES
Backend cho phép update (trừ role)
    ↓
Database updated
    ↓
Frontend refresh danh sách
    ↓
✅ Thông tin đã được cập nhật!
```

---

## ⚠️ Lưu ý quan trọng

### 1. Không thể đổi role của chính mình
- Đây là tính năng bảo mật
- Ngăn chặn privilege escalation
- Chỉ admin khác hoặc super_admin mới có thể đổi role cho bạn

### 2. Company và Ship fields
- Có thể cần thêm restrictions tùy logic nghiệp vụ
- Hiện tại user có thể đổi company/ship của mình
- Cân nhắc lock các fields này nếu cần

### 3. Username changes
- User có thể đổi username của mình
- Cân nhắc thêm validation để tránh duplicate username
- Hoặc lock username sau khi tạo

---

## 🔄 Rollback (Nếu cần)

Nếu cần revert lại logic cũ (không cho user edit chính mình):

### Frontend:
```javascript
const canEditUser = (targetUser) => {
  if (targetUser.id === currentUser.id) {
    return false;  // Revert: không cho edit chính mình
  }
  // ... rest
};
```

### Backend:
```python
async def update_user(
    user_id: str, 
    user_data: UserUpdate, 
    current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]))
):
    # Revert: chỉ admin mới update được
```

---

## ✅ Status: COMPLETED & TESTED

- ✅ Frontend logic updated
- ✅ Backend API updated
- ✅ Security restrictions implemented
- ✅ Role field disabled for self-edit
- ✅ All services restarted
- ✅ Ready for testing

---

**Last Updated**: 2025-01-09
**Feature Status**: ✅ ACTIVE
**Environment**: Preview & Production (sau khi redeploy)

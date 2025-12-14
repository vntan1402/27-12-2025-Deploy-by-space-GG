# Permission System Analysis - Hệ Thống Phân Quyền

## 📋 **TỔNG QUAN**

Logic phân quyền hiện tại dựa trên **4 yếu tố chính**:
1. **User Role** (Vai trò)
2. **Department** (Phòng ban)
3. **Company** (Công ty)
4. **Action Type** (Loại hành động: Read/Create/Update/Delete)

---

## 👤 **1. USER ROLES (6 LEVELS)**

Định nghĩa trong `/app/backend/app/models/user.py` (dòng 6-12):

```python
class UserRole(str, Enum):
    VIEWER = "viewer"           # Level 1 - Chỉ xem
    EDITOR = "editor"           # Level 2 - Tạo/sửa documents
    MANAGER = "manager"         # Level 3 - Quản lý phòng ban
    ADMIN = "admin"             # Level 4 - Quản trị công ty
    SUPER_ADMIN = "super_admin" # Level 5 - Quản trị toàn hệ thống
    SYSTEM_ADMIN = "system_admin" # Level 6 - Quyền cao nhất
```

### **Phân cấp quyền:**

| Role | Quyền hạn | Ví dụ |
|------|-----------|-------|
| **VIEWER** | Chỉ xem dữ liệu | Nhân viên thực tập, nhân viên tạm thời |
| **EDITOR** | Xem + Tạo/Sửa documents | Nhân viên văn phòng, thủ thư |
| **MANAGER** | Editor + Quản lý phòng ban | Trưởng phòng, DPA Manager, Crewing Manager |
| **ADMIN** | Manager + Quản trị công ty | Giám đốc công ty, CEO |
| **SUPER_ADMIN** | Admin + Quản lý nhiều công ty | Owner, COO |
| **SYSTEM_ADMIN** | Full access hệ thống | System developer, Platform admin |

---

## 🏢 **2. DEPARTMENTS (11 PHÒNG BAN)**

Định nghĩa trong `/app/backend/app/models/user.py` (dòng 14-26):

```python
class Department(str, Enum):
    TECHNICAL = "technical"       # Kỹ thuật
    OPERATIONS = "operations"     # Vận hành
    LOGISTICS = "logistics"       # Hậu cần
    FINANCE = "finance"           # Tài chính
    SHIP_CREW = "ship_crew"       # Thủy thủ đoàn
    SSO = "sso"                   # Ship Security Officer
    CSO = "cso"                   # Company Security Officer
    CREWING = "crewing"           # Quản lý thuyền viên
    SAFETY = "safety"             # An toàn
    COMMERCIAL = "commercial"     # Thương mại
    DPA = "dpa"                   # Designated Person Ashore
    SUPPLY = "supply"             # Vật tư
```

**Lưu ý:**
- User có thể thuộc **nhiều phòng ban**: `department: List[str]`
- Department values được lưu **lowercase** trong database

---

## 🏢 **3. COMPANY-BASED FILTERING**

Mỗi user thuộc **1 company** (công ty):
```python
class UserBase(BaseModel):
    company: Optional[str] = None  # Company UUID
```

### **Quy tắc filtering:**

#### **A. Non-Admin Users (Viewer, Editor, Manager)**
- Chỉ thấy data của **công ty mình** (`current_user.company`)
- Không thấy data của công ty khác

**Example:**
```python
# File: company_cert_service.py line 37-38
filters["company"] = current_user.company  # Lọc theo company của user
```

#### **B. Admin & Super Admin**
- Có thể xem data của **tất cả công ty** (nếu không filter)
- Hoặc filter theo company cụ thể

**Example:**
```python
# File: ships.py line 29
# Admin có thể xem tất cả ships, hoặc filter theo company
```

---

## 🔒 **4. PERMISSION CHECK FUNCTIONS**

### **A. Role-Based Permission Checks**

#### **1. check_editor_permission()**
**Locations:** 
- `crew_certificates.py`
- `survey_reports.py`
- `test_reports.py`
- `approval_documents.py`
- `drawings_manuals.py`
- `other_documents.py`

**Logic:**
```python
def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, 
                                   UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user
```

**Allowed roles:**
- ✅ EDITOR
- ✅ MANAGER
- ✅ ADMIN
- ✅ SUPER_ADMIN
- ✅ SYSTEM_ADMIN

**Blocked roles:**
- ❌ VIEWER

---

#### **2. check_admin_permission()**
**Locations:**
- `system_settings.py`
- `gdrive.py`

**Logic:**
```python
def check_admin_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has admin permission"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user
```

**Allowed roles:**
- ✅ ADMIN
- ✅ SUPER_ADMIN
- ✅ SYSTEM_ADMIN

**Blocked roles:**
- ❌ VIEWER
- ❌ EDITOR
- ❌ MANAGER

---

### **B. Role + Department-Based Checks**

#### **3. check_dpa_manager_permission()**
**Location:** `company_certs.py` (dòng 14-32)

**Logic:**
```python
def check_dpa_manager_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user is Admin or Manager in DPA department"""
    
    # Admin level always has access
    if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        return current_user  # ✅ Granted
    
    # Manager with DPA department has access
    if current_user.role == UserRole.MANAGER:
        user_departments = current_user.department if isinstance(current_user.department, list) else [current_user.department]
        if "dpa" in [dept.lower() for dept in user_departments]:
            return current_user  # ✅ Granted
    
    # Others: Access denied
    raise HTTPException(status_code=403, detail=PERMISSION_DENIED)
```

**Allowed:**
- ✅ ADMIN (any department)
- ✅ SUPER_ADMIN (any department)
- ✅ SYSTEM_ADMIN (any department)
- ✅ MANAGER + DPA department

**Blocked:**
- ❌ MANAGER without DPA department
- ❌ EDITOR
- ❌ VIEWER

---

#### **4. check_crewing_manager_permission()** (Example)
**Location:** `crew_certificates.py` (context menu delete)

**Logic:**
```python
# In frontend: CertificateContextMenu.jsx
const canDelete = user.role === 'admin' || 
                  (user.role === 'manager' && user.department?.includes('crewing'));
```

**Allowed:**
- ✅ ADMIN (any department)
- ✅ MANAGER + Crewing department

**Blocked:**
- ❌ MANAGER without Crewing department
- ❌ EDITOR
- ❌ VIEWER

---

## 📊 **PERMISSION MATRIX**

### **Ship Certificates & Documents**

| Action | VIEWER | EDITOR | MANAGER | ADMIN | SUPER_ADMIN | SYSTEM_ADMIN |
|--------|--------|--------|---------|-------|-------------|--------------|
| **View** | ✅ (own company) | ✅ (own company) | ✅ (own company) | ✅ (all companies) | ✅ (all companies) | ✅ (all companies) |
| **Create** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Update** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Delete** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Uses:** `check_editor_permission()`

---

### **Company Certificates (SMS)**

| Action | VIEWER | EDITOR | MANAGER (non-DPA) | MANAGER (DPA) | ADMIN+ |
|--------|--------|--------|-------------------|---------------|--------|
| **View** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Create** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Update** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Delete** | ❌ | ❌ | ❌ | ✅ | ✅ |

**Uses:** `check_dpa_manager_permission()`

---

### **Crew Certificates**

| Action | VIEWER | EDITOR | MANAGER (non-Crewing) | MANAGER (Crewing) | ADMIN+ |
|--------|--------|--------|----------------------|-------------------|--------|
| **View** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Create** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Update** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Delete** | ❌ | ❌ | ❌ | ✅ | ✅ |

**Uses:** `check_editor_permission()` + Frontend department check

---

### **System Settings**

| Action | VIEWER | EDITOR | MANAGER | ADMIN+ |
|--------|--------|--------|---------|--------|
| **View** | ❌ | ❌ | ❌ | ✅ |
| **Update** | ❌ | ❌ | ❌ | ✅ |

**Uses:** `check_admin_permission()`

---

## 🔐 **AUTHENTICATION FLOW**

### **1. Login**
```
User inputs username + password
    ↓
Backend validates credentials
    ↓
Generate JWT token with user.id
    ↓
Return token + user info (role, department, company)
```

### **2. API Request**
```
Frontend sends request with JWT token in Authorization header
    ↓
Backend middleware: get_current_user()
    ↓
Verify JWT token
    ↓
Load user from database (with role, department, company)
    ↓
Pass to permission check function (if any)
    ↓
Execute API logic
    ↓
Filter data by company (if non-admin)
```

---

## 📝 **CODE EXAMPLES**

### **Example 1: Company-based filtering (Ships)**

```python
# File: services/ship_service.py
@staticmethod
async def get_all_ships(current_user: UserResponse):
    filters = {}
    
    # Non-admin users: Filter by company
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        filters["company"] = current_user.company
    
    # Admin users: See all companies (no filter)
    ships = await mongo_db.find_all("ships", filters)
    return ships
```

### **Example 2: Role + Department check (Company Certs)**

```python
# File: api/v1/company_certs.py
@router.post("", response_model=CompanyCertResponse)
async def create_company_cert(
    cert_data: CompanyCertCreate,
    current_user: UserResponse = Depends(check_dpa_manager_permission)  # ← CHECK HERE
):
    # Only Admin or DPA Manager can reach this point
    return await CompanyCertService.create_company_cert(cert_data, current_user)
```

### **Example 3: Frontend permission check**

```javascript
// File: frontend/src/components/CrewCertificate/CertificateContextMenu.jsx
const showDeleteOption = () => {
  // Check role and department
  if (user.role === 'admin') return true;
  if (user.role === 'manager' && user.department?.includes('crewing')) return true;
  return false;
};
```

---

## 🎯 **SUMMARY**

### **Phân quyền dựa trên 4 yếu tố:**

1. **ROLE** (6 levels: Viewer → System Admin)
   - Xác định **CẤP ĐỘ QUYỀN HẠN** tổng thể

2. **DEPARTMENT** (11 phòng ban)
   - Kết hợp với MANAGER role để tạo **quyền chuyên biệt**
   - Ví dụ: DPA Manager, Crewing Manager

3. **COMPANY** (Company UUID)
   - Tự động lọc data theo công ty
   - Non-admin chỉ thấy data của company mình

4. **ACTION TYPE** (CRUD)
   - Create/Update/Delete: Cần Editor+
   - View: Tất cả roles
   - System settings: Cần Admin+

### **Key Points:**
- ✅ Phân cấp rõ ràng: Viewer < Editor < Manager < Admin
- ✅ Company isolation: Tự động lọc theo company
- ✅ Department-specific permissions: Kết hợp Role + Department
- ✅ Centralized permission checks: Reusable functions
- ✅ JWT-based authentication: Stateless, scalable

---

## 📁 **FILES REFERENCE**

**Models:**
- `/app/backend/app/models/user.py` - User roles & departments

**Security:**
- `/app/backend/app/core/security.py` - JWT & authentication

**Permission Checks:**
- `/app/backend/app/api/v1/company_certs.py` - DPA Manager check
- `/app/backend/app/api/v1/crew_certificates.py` - Editor check
- `/app/backend/app/api/v1/system_settings.py` - Admin check

**Services:**
- `/app/backend/app/services/company_cert_service.py` - Company filtering
- `/app/backend/app/services/ship_service.py` - Company filtering

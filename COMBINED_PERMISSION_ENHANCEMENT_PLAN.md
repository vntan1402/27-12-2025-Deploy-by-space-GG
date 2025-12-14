# Combined Permission Enhancement Plan

## 🎯 **OBJECTIVES**

Implement 2 major enhancements simultaneously:

1. **Department-Based Permission System**
   - Manager quyền theo department
   - Category-department mapping
   - Editor/Viewer ship-based access
   - Editor/Viewer có thể view Company Certificates

2. **Error Message Standardization**
   - Tất cả 403 errors → Vietnamese
   - Centralized message management
   - User-friendly error messages

---

## 📊 **COMBINED TIMELINE**

| Phase | Tasks | Duration | Priority |
|-------|-------|----------|----------|
| **Phase 1** | Core Infrastructure | 2-3 hours | 🔴 Critical |
| **Phase 2** | Update Messages & Services | 3-4 hours | 🔴 Critical |
| **Phase 3** | Update All Documents | 2-3 hours | 🟡 High |
| **Phase 4** | Frontend (Optional) | 1-2 hours | 🟢 Medium |
| **Phase 5** | Testing & Verification | 2-3 hours | 🔴 Critical |
| **TOTAL** | | **10-15 hours** | |

---

## 🏗️ **PHASE 1: CORE INFRASTRUCTURE (2-3 hours)**

### **Task 1.1: Update messages.py** ⭐ PRIORITY 1

**File:** `/app/backend/app/core/messages.py`

**Add new constants:**
```python
"""
Common error messages for the application
"""

# Permission error messages (Vietnamese)
PERMISSION_DENIED = "Bạn không được cấp quyền để thực hiện việc này. Hãy liên hệ Admin."
ADMIN_ONLY = "Chỉ Admin mới có quyền thực hiện việc này. Hãy liên hệ Admin."
SYSTEM_ADMIN_ONLY = "Chỉ System Admin mới có quyền thực hiện việc này."
ACCESS_DENIED = "Truy cập bị từ chối. Bạn không có quyền xem nội dung này."

# ⭐ NEW: Specific permission messages
ACCESS_DENIED_SHIP = "Bạn không có quyền truy cập tàu này. Chỉ có thể xem tàu của công ty mình hoặc tàu đang sign on."
ACCESS_DENIED_COMPANY = "Bạn không có quyền truy cập dữ liệu của công ty này."
EDITOR_ONLY = "Chỉ Editor hoặc cao hơn mới có quyền thực hiện việc này."
MANAGER_ONLY = "Chỉ Manager hoặc cao hơn mới có quyền thực hiện việc này."
DEPARTMENT_PERMISSION_DENIED = "Department của bạn không có quyền quản lý loại tài liệu này. Hãy liên hệ Manager của department tương ứng."

# ⭐ NEW: Role-specific messages
DPA_MANAGER_ONLY = "Chỉ DPA Manager hoặc Admin mới có quyền thực hiện việc này."
CREWING_MANAGER_ONLY = "Chỉ Crewing Manager hoặc Admin mới có quyền thực hiện việc này."
TECHNICAL_MANAGER_ONLY = "Chỉ Technical Manager hoặc Admin mới có quyền thực hiện việc này."
SAFETY_MANAGER_ONLY = "Chỉ Safety Manager hoặc Admin mới có quyền thực hiện việc này."

# ⭐ NEW: Special cases
ADMIN_OWN_COMPANY_ONLY = "Admin chỉ có thể cập nhật thông tin công ty của mình."
SHIP_ACCESS_DENIED = "Bạn chỉ có thể xem tài liệu của tàu đang sign on."

# Authentication error messages
NOT_AUTHENTICATED = "Vui lòng đăng nhập để tiếp tục."
INVALID_CREDENTIALS = "Tên đăng nhập hoặc mật khẩu không chính xác."
TOKEN_EXPIRED = "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."

# Common error messages
NOT_FOUND = "Không tìm thấy dữ liệu."
INTERNAL_ERROR = "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau."
BAD_REQUEST = "Yêu cầu không hợp lệ."
```

**Changes:** Add 10 new constants

---

### **Task 1.2: Create Department Permission Module** ⭐ PRIORITY 1

**File:** `/app/backend/app/core/department_permissions.py` (NEW)

```python
"""
Department-based permission utilities
"""
from typing import List, Dict
from app.models.user import UserRole, Department

# Category to Department mapping
CATEGORY_DEPARTMENT_MAPPING: Dict[str, List[str]] = {
    "Class & Flag Cert": ["technical", "supply"],
    "Crew Records": ["crewing"],
    "ISM - ISPS - MLC": ["safety", "dpa", "cso"],
    "Safety Management System": ["dpa"],
    "Technical Infor": ["technical"],
    "Supplies": ["supply"]
}

# Document type to Category mapping
DOCUMENT_TYPE_CATEGORY_MAPPING: Dict[str, str] = {
    "ship_cert": "Class & Flag Cert",
    "survey_report": "Class & Flag Cert",
    "test_report": "Class & Flag Cert",
    "drawing_manual": "Class & Flag Cert",
    "other_document": "Class & Flag Cert",
    "crew_cert": "Crew Records",
    "crew_passport": "Crew Records",
    "audit_cert": "ISM - ISPS - MLC",
    "audit_report": "ISM - ISPS - MLC",
    "approval_doc": "ISM - ISPS - MLC",
    "other_audit_doc": "ISM - ISPS - MLC",
    "company_cert": "Safety Management System"
}

def get_managed_categories(departments: List[str]) -> List[str]:
    """
    Get categories that user's departments can manage
    
    Args:
        departments: List of user's departments (lowercase)
    
    Returns:
        List of category names user can manage
    """
    if not departments:
        return []
    
    # Normalize to lowercase
    normalized_depts = [dept.lower() if dept else "" for dept in departments]
    
    managed_categories = []
    for category, allowed_depts in CATEGORY_DEPARTMENT_MAPPING.items():
        if any(dept in allowed_depts for dept in normalized_depts):
            managed_categories.append(category)
    
    return managed_categories

def can_manage_category(user_departments: List[str], category: str) -> bool:
    """
    Check if user's departments can manage a specific category
    
    Args:
        user_departments: User's departments (lowercase)
        category: Category name
    
    Returns:
        True if user can manage this category
    """
    if not user_departments or not category:
        return False
    
    allowed_depts = CATEGORY_DEPARTMENT_MAPPING.get(category, [])
    normalized_depts = [dept.lower() if dept else "" for dept in user_departments]
    
    return any(dept in allowed_depts for dept in normalized_depts)

def get_category_for_document_type(doc_type: str) -> str:
    """
    Map document type to category
    
    Args:
        doc_type: ship_cert, crew_cert, audit_cert, etc.
    
    Returns:
        Category name or "Unknown"
    """
    return DOCUMENT_TYPE_CATEGORY_MAPPING.get(doc_type, "Unknown")

def get_department_for_category(category: str) -> List[str]:
    """
    Get list of departments that can manage a category
    
    Args:
        category: Category name
    
    Returns:
        List of department names
    """
    return CATEGORY_DEPARTMENT_MAPPING.get(category, [])
```

---

### **Task 1.3: Create Permission Check Module** ⭐ PRIORITY 1

**File:** `/app/backend/app/core/permission_checks.py` (NEW)

```python
"""
Enhanced permission check functions
"""
from typing import Optional, List
from fastapi import HTTPException
from app.models.user import UserResponse, UserRole
from app.core.department_permissions import can_manage_category, get_department_for_category
from app.core.messages import (
    ACCESS_DENIED,
    PERMISSION_DENIED,
    DEPARTMENT_PERMISSION_DENIED,
    SHIP_ACCESS_DENIED
)

def check_document_edit_permission(
    current_user: UserResponse,
    document_category: str,
    action: str = "edit"  # "create", "edit", "delete"
) -> bool:
    """
    Check if user has permission to edit document based on role and department
    
    Args:
        current_user: Current user
        document_category: Document category (e.g., "Class & Flag Cert")
        action: Action type (create/edit/delete)
    
    Returns:
        True if allowed, raises HTTPException if denied
    """
    # Super admins can do anything
    if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
        return True
    
    # Admin can manage company's documents
    if current_user.role == UserRole.ADMIN:
        return True
    
    # Manager: Check department
    if current_user.role == UserRole.MANAGER:
        user_departments = current_user.department if isinstance(current_user.department, list) else [current_user.department]
        
        if can_manage_category(user_departments, document_category):
            return True
        else:
            # Get allowed departments for better error message
            allowed_depts = get_department_for_category(document_category)
            dept_names = ", ".join(allowed_depts).upper()
            raise HTTPException(
                status_code=403,
                detail=f"{DEPARTMENT_PERMISSION_DENIED} (Cần department: {dept_names})"
            )
    
    # Editor/Viewer cannot edit
    if current_user.role in [UserRole.EDITOR, UserRole.VIEWER]:
        raise HTTPException(
            status_code=403,
            detail=PERMISSION_DENIED
        )
    
    return False

async def get_user_accessible_ships(current_user: UserResponse) -> Optional[List[str]]:
    """
    Get list of ship IDs that user can access
    
    For Editor/Viewer: Only ships they are signed on
    For Manager/Admin: All ships in their company
    For Super Admin: All ships
    
    Returns:
        List of ship IDs or None (for all access)
    """
    from app.repositories.crew_repository import CrewRepository
    from app.repositories.ship_repository import ShipRepository
    
    # Super admins see all
    if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
        return None  # All ships
    
    # Manager/Admin see company ships
    if current_user.role in [UserRole.MANAGER, UserRole.ADMIN]:
        ships = await ShipRepository.find_all(company=current_user.company)
        return [ship['id'] for ship in ships]
    
    # Editor/Viewer see only their assigned ship
    if current_user.role in [UserRole.EDITOR, UserRole.VIEWER]:
        # Find crew record for this user
        crew = await CrewRepository.find_one({"user_id": current_user.id})
        
        if not crew:
            return []  # No ship assigned
        
        # Get ship they are signed on
        ship_sign_on = crew.get('ship_sign_on')
        if ship_sign_on and ship_sign_on != '-':
            # Find ship by name
            ship = await ShipRepository.find_one({"name": ship_sign_on})
            if ship:
                return [ship['id']]
        
        return []  # No ship or not signed on
    
    return []

def can_view_company_documents(current_user: UserResponse) -> bool:
    """
    Check if user can view company-level documents (Company Certificates)
    
    Company documents are visible to ALL users in the company
    including Editor and Viewer roles
    
    Returns:
        True if user can view company documents
    """
    # All roles can view company documents
    return True

async def check_ship_access(current_user: UserResponse, ship_id: str) -> bool:
    """
    Check if user has access to a specific ship
    
    Args:
        current_user: Current user
        ship_id: Ship ID to check
    
    Returns:
        True if allowed, raises HTTPException if denied
    """
    accessible_ships = await get_user_accessible_ships(current_user)
    
    if accessible_ships is None:
        # No restrictions (Super Admin)
        return True
    
    if ship_id in accessible_ships:
        return True
    
    raise HTTPException(
        status_code=403,
        detail=SHIP_ACCESS_DENIED
    )
```

---

## 🔧 **PHASE 2: UPDATE SERVICES (3-4 hours)**

### **Strategy:**
- Fix error messages FIRST
- Then add department permission checks
- Update imports efficiently

---

### **Task 2.1: Ship Certificate Service** ⭐ HIGH PRIORITY

**File:** `/app/backend/app/services/certificate_multi_upload_service.py`

**Changes:**

1. **Add imports:**
```python
from app.core.messages import ACCESS_DENIED, PERMISSION_DENIED
from app.core.permission_checks import check_document_edit_permission
from app.core.department_permissions import get_category_for_document_type
```

2. **Update `_create_certificate_from_analysis()` (line ~309):**
```python
# Add permission check at the start
category = get_category_for_document_type("ship_cert")  # "Class & Flag Cert"
check_document_edit_permission(current_user, category, action="create")

# ... rest of logic
```

**Estimated time:** 10 minutes

---

### **Task 2.2: Crew Certificate Service** ⭐ HIGH PRIORITY

**File:** `/app/backend/app/services/crew_certificate_service.py`

**Changes:**

1. **Replace error messages (3 locations: 310, 545, 619):**
```python
# Add import
from app.core.messages import ACCESS_DENIED, PERMISSION_DENIED
from app.core.permission_checks import check_document_edit_permission

# Replace
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)
```

2. **Add permission check in create/update/delete:**
```python
# In create_crew_certificate (before logic)
category = "Crew Records"
check_document_edit_permission(current_user, category, action="create")

# In update_crew_certificate (before logic)
check_document_edit_permission(current_user, category, action="edit")

# In delete_crew_certificate (before logic)
check_document_edit_permission(current_user, category, action="delete")
```

**Estimated time:** 15 minutes

---

### **Task 2.3: Audit Certificate Service** ⭐ HIGH PRIORITY

**File:** `/app/backend/app/api/v1/audit_certificates.py`

**Changes:**

1. **Replace error messages (2 locations: 288, 613):**
```python
# Add import
from app.core.messages import ACCESS_DENIED, PERMISSION_DENIED
from app.core.permission_checks import check_document_edit_permission

# Replace
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)
```

2. **Add permission check in multi_upload (line ~238):**
```python
# After get current_user, before processing files
category = "ISM - ISPS - MLC"
check_document_edit_permission(current_user, category, action="create")
```

**Estimated time:** 15 minutes

---

### **Task 2.4: Company Certificate Service** ⭐ HIGH PRIORITY

**File:** `/app/backend/app/services/company_cert_service.py`

**Changes:**

1. **Update `get_company_certs()` - Allow Editor/Viewer:**
```python
async def get_company_certs(current_user: UserResponse):
    """Get company certificates - visible to ALL company members"""
    
    filters = {}
    
    # All roles can view company certs (including Editor/Viewer)
    # Filter by company
    if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
        filters["company"] = current_user.company
    
    certs = await CompanyCertRepository.find_all(**filters)
    return certs
```

2. **Add department permission check in create/update/delete:**
```python
from app.core.permission_checks import check_document_edit_permission

# In create_company_cert
category = "Safety Management System"
check_document_edit_permission(current_user, category, action="create")
```

**Estimated time:** 10 minutes

---

### **Task 2.5: Batch Update Other Services** 🔄

**Services to update (pattern similar to above):**

1. `crew_assignment_service.py` - Fix error messages (3 locations)
2. `crew_service.py` - Fix error messages (3 locations)
3. `audit_report_service.py` - Fix error messages + add ship check
4. `ship_service.py` - Fix error messages (3 locations)
5. `certificate_service.py` - Fix error messages + add ship filtering
6. `approval_document_service.py` - Fix error messages + permission check
7. `survey_report_service.py` - Add permission check
8. `test_report_service.py` - Add permission check
9. `drawing_manual_service.py` - Add permission check
10. `other_doc_service.py` - Add permission check

**Pattern for each:**
```python
# 1. Add imports
from app.core.messages import ACCESS_DENIED, PERMISSION_DENIED
from app.core.permission_checks import check_document_edit_permission

# 2. Replace error messages
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)

# 3. Add permission check
category = get_category_for_document_type("xxx")
check_document_edit_permission(current_user, category, action="create")
```

**Estimated time:** 1.5 hours

---

## 📋 **PHASE 3: UPDATE API FILES (1 hour)**

### **API Files to Update:**

| File | Changes | Priority |
|------|---------|----------|
| `crew_certificates.py` | Replace 2 error messages | High |
| `system_settings.py` | Replace 1 error message | Medium |
| `survey_reports.py` | Replace 1 error message | Medium |
| `test_reports.py` | Replace 1 error message | Medium |
| `other_documents.py` | Replace 1 error message | Medium |
| `ships.py` | Replace 1 error message | Medium |
| `supply_documents.py` | Replace 1 error message | Low |
| `other_audit_documents.py` | Replace 1 error message | Low |
| `drawings_manuals.py` | Replace 1 error message | Low |
| `gdrive.py` | Replace 1 error message | Low |
| `companies.py` | Replace 1 error message | Low |

**Pattern:**
```python
# Add import at top
from app.core.messages import PERMISSION_DENIED, ADMIN_ONLY

# Replace
- raise HTTPException(status_code=403, detail="Insufficient permissions")
+ raise HTTPException(status_code=403, detail=PERMISSION_DENIED)
```

**Batch execution:** Can use search-replace with `replace_all=True`

---

## 🧪 **PHASE 4: TESTING (2-3 hours)**

### **Test Matrix:**

| Test Scenario | User Role | Action | Expected Result |
|--------------|-----------|--------|-----------------|
| **1. Manager Technical** | Manager (Technical) | Create Ship Cert | ✅ Success |
| | | Create Crew Cert | ❌ 403 + Vietnamese error |
| | | View Company Cert | ✅ Success |
| **2. Manager Crewing** | Manager (Crewing) | Create Crew Cert | ✅ Success |
| | | Create Ship Cert | ❌ 403 + Vietnamese error |
| | | View Company Cert | ✅ Success |
| **3. Manager DPA** | Manager (DPA) | Create Audit Cert | ✅ Success |
| | | Create Company Cert | ✅ Success |
| | | Create Ship Cert | ❌ 403 + Vietnamese error |
| **4. Editor (Ship A)** | Editor (Ship A) | View Ship A docs | ✅ Success |
| | | View Ship B docs | ❌ 403 + Vietnamese error |
| | | View Company Cert | ✅ Success |
| | | Create any cert | ❌ 403 + Vietnamese error |
| **5. Admin Company A** | Admin (Company A) | View Company A data | ✅ Success |
| | | View Company B data | ❌ 403 + Vietnamese error |
| | | Create any cert | ✅ Success |

### **Testing Commands:**

```bash
# 1. Lint all modified files
cd /app/backend
python3 -m ruff check app/core/
python3 -m ruff check app/services/
python3 -m ruff check app/api/v1/

# 2. Test with curl (Manager Technical creates Ship Cert)
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
TOKEN="<manager_technical_token>"
curl -X POST "$API_URL/api/certificates/multi-upload?ship_id=..." \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@test.pdf"

# Expected: Success

# 3. Test with curl (Manager Technical creates Crew Cert)
curl -X POST "$API_URL/api/crew-certs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cert_name":"Test","crew_id":"..."}'

# Expected: 403 with Vietnamese message about department
```

---

## 📊 **IMPLEMENTATION CHECKLIST**

### **Phase 1: Core Infrastructure**
- [ ] Update `/app/backend/app/core/messages.py` (10 new constants)
- [ ] Create `/app/backend/app/core/department_permissions.py` (NEW)
- [ ] Create `/app/backend/app/core/permission_checks.py` (NEW)
- [ ] Test imports and basic functions

### **Phase 2: Services**
- [ ] Update `certificate_multi_upload_service.py` (Ship Cert)
- [ ] Update `crew_certificate_service.py` (Crew Cert)
- [ ] Update `audit_certificates.py` (Audit Cert)
- [ ] Update `company_cert_service.py` (Company Cert + Editor view access)
- [ ] Update remaining 10 services (batch)

### **Phase 3: API Files**
- [ ] Update 11 API files with error messages

### **Phase 4: Testing**
- [ ] Lint all files
- [ ] Manual testing with 5 test scenarios
- [ ] Verify all Vietnamese error messages
- [ ] Verify department permissions
- [ ] Verify ship-based filtering

---

## 🎯 **SUCCESS CRITERIA**

### **Permission System:**
1. ✅ Manager có quyền đúng theo department
2. ✅ Editor/Viewer chỉ thấy ship của mình
3. ✅ Editor/Viewer có thể view Company Certificates
4. ✅ Category-department mapping hoạt động đúng

### **Error Messages:**
1. ✅ Tất cả 403 errors hiển thị Vietnamese
2. ✅ Error messages rõ ràng và có hướng dẫn
3. ✅ Không còn hardcoded English messages
4. ✅ Consistent across all modules

### **Code Quality:**
1. ✅ Pass all linting checks
2. ✅ No breaking changes for existing users
3. ✅ Clear code comments
4. ✅ Follow existing patterns

---

## 🚀 **EXECUTION STRATEGY**

### **Day 1 (4-5 hours):**
- Morning: Phase 1 (Core Infrastructure) - 2-3 hours
- Afternoon: Phase 2 Part 1 (Main 4 services) - 2 hours

### **Day 2 (4-5 hours):**
- Morning: Phase 2 Part 2 (Remaining services) - 2 hours
- Afternoon: Phase 3 (API files) - 1 hour
- Testing: Initial testing - 1 hour

### **Day 3 (2-3 hours):**
- Phase 4: Comprehensive testing - 2-3 hours
- Bug fixes if needed
- Documentation update

---

## 📝 **FILES SUMMARY**

| Type | Action | Count |
|------|--------|-------|
| **New Files** | Create | 2 |
| **Core File** | Update | 1 |
| **Service Files** | Update | 14 |
| **API Files** | Update | 11 |
| **TOTAL** | | **28 files** |

---

## ⚠️ **RISKS & MITIGATION**

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing flows | High | Thorough testing before deploy |
| Performance (ship filtering) | Medium | Cache user-ship mapping |
| Complex permission logic | Medium | Clear documentation |
| Message translation quality | Low | Review with Vietnamese speaker |

---

**Bạn có sẵn sàng bắt đầu không?**
1. 🚀 Bắt đầu Phase 1 (Core Infrastructure)?
2. 📋 Review lại plan trước khi execute?
3. 🎯 Adjust priorities hoặc scope?

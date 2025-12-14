# Department-Based Permission Enhancement Plan

## 🎯 **OBJECTIVE**

Implement fine-grained permission control based on:
1. **Manager Role:** Department-specific CRUD permissions
2. **Category-Department Mapping:** Who manages what
3. **Editor/Viewer Restrictions:** Ship-based access only

---

## 📋 **NEW PERMISSION RULES**

### **Rule 1: Manager Department-Based Permissions**

| User | Department | Category | Permissions |
|------|-----------|----------|-------------|
| Manager (Technical) | Technical | Class & Flag Cert | ✅ Create/Update/Delete |
| Manager (Technical) | Technical | Crew Records | 👁️ View only |
| Manager (Crewing) | Crewing | Crew Records | ✅ Create/Update/Delete |
| Manager (Crewing) | Crewing | Class & Flag Cert | 👁️ View only |
| Manager (DPA) | DPA | ISM - ISPS - MLC | ✅ Create/Update/Delete |
| Manager (DPA) | DPA | Safety Management System | ✅ Create/Update/Delete |

**Logic:**
```
IF user.role == MANAGER:
    IF document.category IN user.managed_categories:
        GRANT Create/Update/Delete
    ELSE:
        GRANT View only
```

---

### **Rule 2: Category-Department Mapping**

| Category | Managed By Departments | Notes |
|----------|------------------------|-------|
| **Class & Flag Cert** | Technical, Supply | Ship certificates, surveys, tests, drawings |
| **Crew Records** | Crewing | Crew certs, passports |
| **ISM - ISPS - MLC** | Safety, DPA, CSO | Audit certs, reports, approval docs |
| **Safety Management System** | DPA | Company certs (SMS) |
| **Technical Infor** | Technical | Technical documents |
| **Supplies** | Supply | Supply documents |

**Constants file:**
```python
# File: /app/backend/app/core/department_permissions.py

CATEGORY_DEPARTMENT_MAPPING = {
    "Class & Flag Cert": ["technical", "supply"],
    "Crew Records": ["crewing"],
    "ISM - ISPS - MLC": ["safety", "dpa", "cso"],
    "Safety Management System": ["dpa"],
    "Technical Infor": ["technical"],
    "Supplies": ["supply"]
}
```

---

### **Rule 3: Editor/Viewer Ship-Based Access**

| User Role | Ship Assignment | Permissions |
|-----------|----------------|-------------|
| Editor (Sign on Ship A) | Ship A | ✅ View documents of Ship A |
| Editor (Sign on Ship A) | Ship B | ❌ Cannot view Ship B docs |
| Viewer (Sign on Ship B) | Ship B | ✅ View documents of Ship B |
| Viewer (No ship) | Any | ❌ No access |

**Logic:**
```
IF user.role IN [EDITOR, VIEWER]:
    user_ship = get_user_assigned_ship(user.id)
    IF user_ship:
        FILTER documents WHERE document.ship_id == user_ship.id
    ELSE:
        RETURN empty (no access)
```

---

## 🏗️ **IMPLEMENTATION PLAN**

### **Phase 1: Core Infrastructure (2-3 hours)**

#### **Task 1.1: Create Department Permission Module**
**File:** `/app/backend/app/core/department_permissions.py`

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

def get_managed_categories(departments: List[str]) -> List[str]:
    """
    Get categories that user's departments can manage
    
    Args:
        departments: List of user's departments (lowercase)
    
    Returns:
        List of category names user can manage
    """
    managed_categories = []
    for category, allowed_depts in CATEGORY_DEPARTMENT_MAPPING.items():
        if any(dept in allowed_depts for dept in departments):
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
    allowed_depts = CATEGORY_DEPARTMENT_MAPPING.get(category, [])
    return any(dept in allowed_depts for dept in user_departments)

def get_category_for_document_type(doc_type: str) -> str:
    """
    Map document type to category
    
    Args:
        doc_type: ship_cert, crew_cert, audit_cert, etc.
    
    Returns:
        Category name
    """
    mapping = {
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
    return mapping.get(doc_type, "Unknown")
```

---

#### **Task 1.2: Create Permission Check Functions**
**File:** `/app/backend/app/core/permission_checks.py`

```python
"""
Enhanced permission check functions
"""
from typing import Optional
from fastapi import HTTPException
from app.models.user import UserResponse, UserRole
from app.core.department_permissions import can_manage_category

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
        user_departments = [dept.lower() for dept in user_departments]
        
        if can_manage_category(user_departments, document_category):
            return True
        else:
            raise HTTPException(
                status_code=403,
                detail=f"Manager không có quyền {action} tài liệu thuộc category '{document_category}'. Chỉ department quản lý mới có quyền này."
            )
    
    # Editor/Viewer cannot edit
    if current_user.role in [UserRole.EDITOR, UserRole.VIEWER]:
        raise HTTPException(
            status_code=403,
            detail=f"Role {current_user.role} không có quyền {action} tài liệu"
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
```

---

### **Phase 2: Update Services (3-4 hours)**

#### **Task 2.1: Update Ship Certificate Service**
**File:** `/app/backend/app/services/certificate_multi_upload_service.py`

**Location:** `_create_certificate_from_analysis` method

**Add permission check:**
```python
from app.core.permission_checks import check_document_edit_permission
from app.core.department_permissions import get_category_for_document_type

# Before creating certificate
category = get_category_for_document_type("ship_cert")  # "Class & Flag Cert"
check_document_edit_permission(current_user, category, action="create")
```

---

#### **Task 2.2: Update Crew Certificate Service**
**File:** `/app/backend/app/services/crew_certificate_service.py`

**Methods to update:**
- `create_crew_certificate` - Add permission check
- `update_crew_certificate` - Add permission check
- `delete_crew_certificate` - Add permission check

**Add:**
```python
from app.core.permission_checks import check_document_edit_permission

# In create/update/delete methods
category = "Crew Records"
check_document_edit_permission(current_user, category, action="create")  # or "edit", "delete"
```

---

#### **Task 2.3: Update Audit Certificate Service**
**File:** `/app/backend/app/api/v1/audit_certificates.py`

**Methods to update:**
- `multi_upload_audit_certificates` - Add permission check
- `update_audit_certificate` - Add permission check
- `delete_audit_certificate` - Add permission check

**Add:**
```python
from app.core.permission_checks import check_document_edit_permission

category = "ISM - ISPS - MLC"
check_document_edit_permission(current_user, category, action="create")
```

---

#### **Task 2.4: Update Company Certificate Service**
**File:** `/app/backend/app/services/company_cert_service.py`

**Current:** Uses `check_dpa_manager_permission()`

**Update to:**
```python
from app.core.permission_checks import check_document_edit_permission

category = "Safety Management System"
check_document_edit_permission(current_user, category, action="create")
```

---

#### **Task 2.5: Add Ship-Based Filtering for Editor/Viewer**
**File:** `/app/backend/app/services/certificate_service.py`

**Update `get_certificates` method:**
```python
from app.core.permission_checks import get_user_accessible_ships

async def get_certificates(ship_id: Optional[str], current_user: UserResponse):
    """Get certificates with enhanced filtering"""
    
    # Get accessible ships for user
    accessible_ship_ids = await get_user_accessible_ships(current_user)
    
    if accessible_ship_ids is not None:  # Has restrictions
        if ship_id:
            # Verify requested ship is accessible
            if ship_id not in accessible_ship_ids:
                raise HTTPException(status_code=403, detail="Access denied to this ship")
        
        # Filter certificates by accessible ships
        all_certs = await CertificateRepository.find_all(ship_id=ship_id)
        certificates = [cert for cert in all_certs if cert.get('ship_id') in accessible_ship_ids]
    else:
        # No restrictions (Super Admin)
        certificates = await CertificateRepository.find_all(ship_id=ship_id)
    
    # ... rest of logic
```

---

### **Phase 3: Update All Document Services (2-3 hours)**

**Services to update:**

| # | Service | Doc Type | Category | Methods |
|---|---------|----------|----------|---------|
| 1 | `certificate_multi_upload_service.py` | Ship Cert | Class & Flag Cert | create |
| 2 | `survey_report_service.py` | Survey Report | Class & Flag Cert | create, update, delete |
| 3 | `test_report_service.py` | Test Report | Class & Flag Cert | create, update, delete |
| 4 | `drawing_manual_service.py` | Drawing/Manual | Class & Flag Cert | create, update, delete |
| 5 | `other_doc_service.py` | Other Document | Class & Flag Cert | create, update, delete |
| 6 | `crew_certificate_service.py` | Crew Cert | Crew Records | create, update, delete |
| 7 | `crew_service.py` (passport) | Crew Passport | Crew Records | create, update, delete |
| 8 | `audit_certificate_service.py` | Audit Cert | ISM - ISPS - MLC | create, update, delete |
| 9 | `audit_report_service.py` | Audit Report | ISM - ISPS - MLC | create, update, delete |
| 10 | `approval_document_service.py` | Approval Doc | ISM - ISPS - MLC | create, update, delete |
| 11 | `other_audit_document_service.py` | Other Audit Doc | ISM - ISPS - MLC | create, update, delete |
| 12 | `company_cert_service.py` | Company Cert | Safety Management System | create, update, delete |

**Pattern for each service:**
```python
from app.core.permission_checks import check_document_edit_permission
from app.core.department_permissions import get_category_for_document_type

# In create method
async def create_xxx(data, current_user):
    category = get_category_for_document_type("xxx")  # or direct string
    check_document_edit_permission(current_user, category, action="create")
    
    # ... rest of create logic

# In update method
async def update_xxx(id, data, current_user):
    category = get_category_for_document_type("xxx")
    check_document_edit_permission(current_user, category, action="edit")
    
    # ... rest of update logic

# In delete method
async def delete_xxx(id, current_user):
    category = get_category_for_document_type("xxx")
    check_document_edit_permission(current_user, category, action="delete")
    
    # ... rest of delete logic
```

---

### **Phase 4: Frontend Updates (Optional - 1-2 hours)**

#### **Task 4.1: Update Context Menus**
**Files:**
- `CertificateContextMenu.jsx`
- `AuditCertificateContextMenu.jsx`
- `CrewCertificateContextMenu.jsx`

**Add department checks:**
```javascript
const canEdit = () => {
  if (user.role === 'admin' || user.role === 'super_admin' || user.role === 'system_admin') {
    return true;
  }
  
  if (user.role === 'manager') {
    const category = getCategoryForDocument(document);
    const managedCategories = getManagedCategories(user.department);
    return managedCategories.includes(category);
  }
  
  return false;
};
```

#### **Task 4.2: Add Department Utility**
**File:** `/app/frontend/src/utils/departmentPermissions.js`

```javascript
export const CATEGORY_DEPARTMENT_MAPPING = {
  "Class & Flag Cert": ["technical", "supply"],
  "Crew Records": ["crewing"],
  "ISM - ISPS - MLC": ["safety", "dpa", "cso"],
  "Safety Management System": ["dpa"],
  "Technical Infor": ["technical"],
  "Supplies": ["supply"]
};

export const getManagedCategories = (userDepartments) => {
  const departments = Array.isArray(userDepartments) ? userDepartments : [userDepartments];
  const lowerDepts = departments.map(d => d.toLowerCase());
  
  const managed = [];
  for (const [category, allowedDepts] of Object.entries(CATEGORY_DEPARTMENT_MAPPING)) {
    if (lowerDepts.some(dept => allowedDepts.includes(dept))) {
      managed.push(category);
    }
  }
  return managed;
};

export const canManageCategory = (userDepartments, category) => {
  const managed = getManagedCategories(userDepartments);
  return managed.includes(category);
};
```

---

## 📊 **PERMISSION MATRIX (UPDATED)**

### **Scenario 1: Manager (Technical)**

| Action | Class & Flag Cert | Crew Records | ISM - ISPS - MLC |
|--------|-------------------|--------------|------------------|
| View | ✅ Yes | ✅ Yes | ✅ Yes |
| Create | ✅ Yes | ❌ No | ❌ No |
| Update | ✅ Yes | ❌ No | ❌ No |
| Delete | ✅ Yes | ❌ No | ❌ No |

### **Scenario 2: Manager (Crewing)**

| Action | Class & Flag Cert | Crew Records | ISM - ISPS - MLC |
|--------|-------------------|--------------|------------------|
| View | ✅ Yes | ✅ Yes | ✅ Yes |
| Create | ❌ No | ✅ Yes | ❌ No |
| Update | ❌ No | ✅ Yes | ❌ No |
| Delete | ❌ No | ✅ Yes | ❌ No |

### **Scenario 3: Manager (DPA)**

| Action | Class & Flag Cert | ISM - ISPS - MLC | SMS (Company Cert) |
|--------|-------------------|------------------|--------------------|
| View | ✅ Yes | ✅ Yes | ✅ Yes |
| Create | ❌ No | ✅ Yes | ✅ Yes |
| Update | ❌ No | ✅ Yes | ✅ Yes |
| Delete | ❌ No | ✅ Yes | ✅ Yes |

### **Scenario 4: Editor (Sign on Ship A)**

| Action | Ship A Docs | Ship B Docs | Company Docs |
|--------|-------------|-------------|--------------|
| View | ✅ Yes | ❌ No | ❌ No |
| Create | ❌ No | ❌ No | ❌ No |
| Update | ❌ No | ❌ No | ❌ No |
| Delete | ❌ No | ❌ No | ❌ No |

---

## 🧪 **TESTING PLAN**

### **Test Case 1: Manager Technical**
```
Login as: manager_technical (dept: technical)
Test:
  ✅ Can create Ship Certificate
  ✅ Can create Survey Report
  ❌ Cannot create Crew Certificate (403)
  ❌ Cannot create Audit Certificate (403)
  ✅ Can view all documents in company
```

### **Test Case 2: Manager Crewing**
```
Login as: manager_crewing (dept: crewing)
Test:
  ❌ Cannot create Ship Certificate (403)
  ✅ Can create Crew Certificate
  ✅ Can upload Crew Passport
  ❌ Cannot create Audit Certificate (403)
  ✅ Can view all documents in company
```

### **Test Case 3: Manager DPA**
```
Login as: manager_dpa (dept: dpa)
Test:
  ❌ Cannot create Ship Certificate (403)
  ❌ Cannot create Crew Certificate (403)
  ✅ Can create Audit Certificate
  ✅ Can create Company Certificate (SMS)
  ✅ Can view all documents in company
```

### **Test Case 4: Editor (Sign on Ship A)**
```
Login as: editor1 (sign_on: Ship A)
Test:
  ✅ Can view Ship A certificates
  ❌ Cannot view Ship B certificates
  ❌ Cannot create any certificates
  ❌ Cannot update any certificates
  ❌ Cannot delete any certificates
```

### **Test Case 5: Manager with Multiple Departments**
```
Login as: manager_multi (dept: [technical, safety])
Test:
  ✅ Can create Ship Certificate (technical)
  ✅ Can create Audit Certificate (safety)
  ❌ Cannot create Crew Certificate (403)
```

---

## 📝 **EXECUTION TIMELINE**

| Phase | Tasks | Estimated Time | Priority |
|-------|-------|----------------|----------|
| **Phase 1** | Core infrastructure | 2-3 hours | 🔴 High |
| **Phase 2** | Update main services | 3-4 hours | 🔴 High |
| **Phase 3** | Update all services | 2-3 hours | 🟡 Medium |
| **Phase 4** | Frontend updates | 1-2 hours | 🟢 Low |
| **Testing** | Manual + automated | 2-3 hours | 🔴 High |

**Total:** 10-15 hours

---

## ✅ **SUCCESS CRITERIA**

1. ✅ Manager có quyền theo department
2. ✅ Category-department mapping hoạt động đúng
3. ✅ Editor/Viewer chỉ thấy ship của mình
4. ✅ Tất cả permission checks consistent
5. ✅ Error messages rõ ràng (Vietnamese)
6. ✅ Pass all test cases
7. ✅ No breaking changes for existing users

---

## 🚨 **RISKS & MITIGATION**

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing functionality | High | Comprehensive testing before deploy |
| Performance impact (ship filtering) | Medium | Cache user-ship mapping |
| Complex multi-department logic | Medium | Clear documentation + examples |
| Frontend-backend sync | Low | Use same constants file |

---

## 📋 **DELIVERABLES**

1. ✅ `/app/backend/app/core/department_permissions.py` - New module
2. ✅ `/app/backend/app/core/permission_checks.py` - New module
3. ✅ Updated 12 service files with permission checks
4. ✅ Frontend utility file (optional)
5. ✅ Test cases documentation
6. ✅ Migration guide for existing users

---

**Bạn có muốn:**
1. 🚀 Bắt đầu implement Phase 1?
2. 📝 Review lại mapping Department-Category?
3. 🔧 Điều chỉnh plan?

# 🔐 Hệ Thống Phân Quyền - Demo & Examples

## 📋 Mục Lục
1. [Department Mapping](#department-mapping)
2. [Permission Checks by Role](#permission-checks-by-role)
3. [Code Examples](#code-examples)
4. [Error Messages](#error-messages)
5. [Real-world Scenarios](#real-world-scenarios)

---

## 1. Department Mapping

### Category ↔ Department Mapping

```python
# File: /app/backend/app/core/department_permissions.py

CATEGORY_DEPARTMENT_MAPPING = {
    "Class & Flag Cert": ["technical", "supply"],      # Ship certificates
    "Crew Records": ["crewing"],                        # Crew certificates/passports
    "ISM - ISPS - MLC": ["safety", "dpa", "cso"],      # Audit certificates
    "Safety Management System": ["dpa"],                # Company certificates
    "Technical Infor": ["technical"],                   # Technical documents
    "Supplies": ["supply"]                              # Supply documents
}
```

### Document Type → Category

```python
DOCUMENT_TYPE_CATEGORY_MAPPING = {
    "ship_cert": "Class & Flag Cert",
    "survey_report": "Class & Flag Cert",
    "test_report": "Class & Flag Cert",
    "crew_cert": "Crew Records",
    "crew_passport": "Crew Records",
    "audit_cert": "ISM - ISPS - MLC",
    "company_cert": "Safety Management System"
}
```

### Ví dụ queries:

```python
from app.core.department_permissions import get_managed_categories, can_manage_document_type

# Manager có departments: ["technical", "supply"]
categories = get_managed_categories(["technical", "supply"])
# → ["Class & Flag Cert", "Technical Infor", "Supplies"]

# Kiểm tra xem có thể manage ship_cert không?
can_manage = can_manage_document_type(["technical"], "ship_cert")
# → True (ship_cert thuộc "Class & Flag Cert", technical có quyền)

can_manage = can_manage_document_type(["technical"], "crew_cert")
# → False (crew_cert thuộc "Crew Records", technical KHÔNG có quyền)
```

---

## 2. Permission Checks by Role

### 🔴 System Admin / Super Admin
**Quyền hạn:** FULL ACCESS - Xem tất cả companies, tất cả documents

```python
# Không có restriction nào
✅ Xem tất cả ships, tất cả companies
✅ Tạo/sửa/xóa bất kỳ document nào
✅ Không bị giới hạn bởi department hoặc ship
```

### 🟠 Admin
**Quyền hạn:** Company-scoped FULL ACCESS

```python
# Chỉ xem data của COMPANY MÌNH
✅ Xem tất cả ships của company
✅ Tạo/sửa/xóa tất cả loại documents trong company
✅ KHÔNG bị giới hạn bởi department
❌ KHÔNG thể xem data của company khác
```

**Example:**
```python
# Admin của Company A
current_user.company = "company_a"
current_user.role = "admin"

# Cố gắng tạo certificate cho Company B
check_company_access(current_user, "company_b", "create")
# → HTTPException(403, "Bạn không có quyền truy cập dữ liệu của công ty này.")
```

### 🟡 Manager
**Quyền hạn:** Department-based + Company-scoped

```python
# Chỉ xem data của COMPANY MÌNH
# Chỉ tạo/sửa/xóa documents thuộc DEPARTMENT MÌNH

✅ Xem tất cả documents của company (không giới hạn department khi VIEW)
✅ Tạo/sửa/xóa documents thuộc department mình
❌ Tạo/sửa/xóa documents KHÔNG thuộc department mình
```

**Example 1: Technical Manager**
```python
user = {
    "role": "manager",
    "company": "company_a",
    "department": ["technical"]
}

# ✅ TẠO Ship Certificate (technical có quyền)
check_create_permission(user, "ship_cert", "company_a")
# → Success

# ❌ TẠO Crew Certificate (technical KHÔNG có quyền)
check_create_permission(user, "crew_cert", "company_a")
# → HTTPException(403, "Department của bạn không có quyền quản lý loại tài liệu này (Category: Crew Records)...")
```

**Example 2: DPA Manager**
```python
user = {
    "role": "manager",
    "company": "company_a",
    "department": ["dpa"]
}

# ✅ TẠO Company Certificate (dpa có quyền)
check_create_permission(user, "company_cert", "company_a")
# → Success

# ✅ TẠO Audit Certificate (dpa có quyền)
check_create_permission(user, "audit_cert", "company_a")
# → Success

# ❌ TẠO Ship Certificate (dpa KHÔNG có quyền)
check_create_permission(user, "ship_cert", "company_a")
# → HTTPException(403, "Department của bạn không có quyền...")
```

**Example 3: Multi-Department Manager**
```python
user = {
    "role": "manager",
    "company": "company_a",
    "department": ["technical", "crewing"]  # 2 departments
}

# ✅ Ship Cert (technical)
# ✅ Crew Cert (crewing)
# ❌ Company Cert (không có dpa)
```

### 🟢 Editor
**Quyền hạn:** Ship-scoped VIEW + Company Cert VIEW

```python
# Chỉ xem documents của SHIP ĐƯỢC ASSIGN
# Có thể VIEW Company Certificates

✅ Xem documents của ship được assign
✅ Xem Company Certificates (NEW!)
❌ Tạo/sửa/xóa bất kỳ document nào
❌ Xem documents của ships khác
```

**Example:**
```python
user = {
    "role": "editor",
    "company": "company_a",
    "assigned_ship_id": "ship_001"  # Được assign vào Ship A
}

# ✅ XEM Ship Certificates của Ship A
check_editor_viewer_ship_scope(user, "ship_001", "view")
# → Success

# ❌ XEM Ship Certificates của Ship B
check_editor_viewer_ship_scope(user, "ship_002", "view")
# → HTTPException(403, "Bạn chỉ có thể xem tài liệu của tàu đang sign on.")

# ✅ XEM Company Certificates
can_view_company_certificates(user)
# → True

# ❌ TẠO documents
check_create_permission(user, "ship_cert", "company_a")
# → HTTPException(403, "Chỉ Manager hoặc cao hơn mới có quyền thực hiện việc này.")
```

### 🔵 Viewer
**Quyền hạn:** Ship-scoped VIEW ONLY

```python
# Chỉ xem documents của SHIP ĐƯỢC ASSIGN
# KHÔNG thể xem Company Certificates

✅ Xem documents của ship được assign
❌ Xem Company Certificates (NEW!)
❌ Tạo/sửa/xóa bất kỳ document nào
❌ Xem documents của ships khác
```

**Example:**
```python
user = {
    "role": "viewer",
    "company": "company_a",
    "assigned_ship_id": "ship_001"
}

# ✅ XEM Ship Certificates của Ship A
check_editor_viewer_ship_scope(user, "ship_001", "view")
# → Success

# ❌ XEM Company Certificates
can_view_company_certificates(user)
# → False

# Nếu cố truy cập Company Certificates
if not can_view_company_certificates(user):
    raise HTTPException(403, "Truy cập bị từ chối. Bạn không có quyền xem nội dung này.")
```

---

## 3. Code Examples

### Example 1: Create Ship Certificate

**Scenario:** Manager Technical muốn upload ship certificate

```python
# File: certificate_multi_upload_service.py

async def process_multi_upload(ship_id, files, current_user, background_tasks):
    # Step 1: Get ship info
    ship = await db.ships.find_one({"id": ship_id})
    ship_company_id = ship.get("company")
    
    # Step 2: Permission checks
    from app.core.permission_checks import (
        check_company_access,
        check_create_permission,
        check_editor_viewer_ship_scope
    )
    
    # Check 1: Company access (Admin chỉ xem company mình)
    check_company_access(current_user, ship_company_id, "create ship certificates")
    # → System Admin: Pass
    # → Admin company A accessing company B: ❌ 403
    # → Admin company A accessing company A: ✅ Pass
    
    # Check 2: Create permission (role + department)
    check_create_permission(current_user, "ship_cert", ship_company_id)
    # → System Admin: ✅ Pass
    # → Admin: ✅ Pass (không bị giới hạn department)
    # → Manager Technical: ✅ Pass (ship_cert thuộc technical)
    # → Manager Crewing: ❌ 403 "Department của bạn không có quyền..."
    # → Editor: ❌ 403 "Chỉ Manager hoặc cao hơn..."
    
    # Check 3: Ship scope (chỉ cho Editor/Viewer)
    check_editor_viewer_ship_scope(current_user, ship_id, "create ship certificates")
    # → System Admin/Admin/Manager: ✅ Pass (không áp dụng cho họ)
    # → Editor assigned to ship_001, accessing ship_001: ✅ Pass
    # → Editor assigned to ship_001, accessing ship_002: ❌ 403
    
    # If all checks pass → Proceed with upload
    ...
```

### Example 2: Get Company Certificates

**Scenario:** Các roles khác nhau truy cập Company Certificates

```python
# File: company_cert_service.py

async def get_company_certs(company, current_user):
    from app.core.permission_checks import can_view_company_certificates, check_company_access
    
    # Check 1: Role-based access to Company Certificates
    if not can_view_company_certificates(current_user):
        # Viewer role blocked
        raise HTTPException(403, "Truy cập bị từ chối. Bạn không có quyền xem nội dung này.")
    
    # → System Admin: ✅ Pass
    # → Admin: ✅ Pass
    # → Manager: ✅ Pass
    # → Editor: ✅ Pass (NEW!)
    # → Viewer: ❌ 403 "Truy cập bị từ chối..."
    
    # Check 2: Company access
    filters = {"company": company or current_user.company}
    check_company_access(current_user, filters["company"], "view")
    # → Admin company A accessing company B: ❌ 403
    
    # If all checks pass → Return certificates
    certs = await mongo_db.find_all("company_certificates", filters)
    return certs
```

### Example 3: Get Ship Certificates with Filtering

**Scenario:** Editor/Viewer chỉ thấy ship của mình

```python
# File: certificate_service.py

async def get_certificates(ship_id, current_user):
    # Step 1: Company filtering (existing)
    if current_user.role not in [SYSTEM_ADMIN, SUPER_ADMIN]:
        company_ships = await ShipRepository.find_all(company=current_user.company)
        company_ship_ids = [ship['id'] for ship in company_ships]
        
        # Get all certificates for company ships
        certificates = [cert for cert in all_certificates 
                       if cert.get('ship_id') in company_ship_ids]
        
        # Step 2: NEW - Ship scope filtering for Editor/Viewer
        from app.core.permission_checks import filter_documents_by_ship_scope
        certificates = filter_documents_by_ship_scope(certificates, current_user)
        
        # What filter_documents_by_ship_scope does:
        # - If role is Editor/Viewer with assigned_ship_id = "ship_001"
        # - Filter: [cert for cert in certificates if cert['ship_id'] == "ship_001"]
        # - If role is Manager/Admin: No filtering (return all)
    
    return certificates
```

---

## 4. Error Messages

Tất cả error messages đều bằng tiếng Việt và rõ ràng:

### General Permission Errors

```python
# File: /app/backend/app/core/messages.py

PERMISSION_DENIED = "Bạn không được cấp quyền để thực hiện việc này. Hãy liên hệ Admin."
ACCESS_DENIED = "Truy cập bị từ chối. Bạn không có quyền xem nội dung này."
```

### Company Access Errors

```python
ACCESS_DENIED_COMPANY = "Bạn không có quyền truy cập dữ liệu của công ty này."
ADMIN_OWN_COMPANY_ONLY = "Admin chỉ có thể cập nhật thông tin công ty của mình."
```

### Ship Access Errors

```python
ACCESS_DENIED_SHIP = "Bạn không có quyền truy cập tàu này. Chỉ có thể xem tàu của công ty mình hoặc tàu đang sign on."
SHIP_ACCESS_DENIED = "Bạn chỉ có thể xem tài liệu của tàu đang sign on."
```

### Role-based Errors

```python
EDITOR_ONLY = "Chỉ Editor hoặc cao hơn mới có quyền thực hiện việc này."
MANAGER_ONLY = "Chỉ Manager hoặc cao hơn mới có quyền thực hiện việc này."
ADMIN_ONLY = "Chỉ Admin mới có quyền thực hiện việc này. Hãy liên hệ Admin."
SYSTEM_ADMIN_ONLY = "Chỉ System Admin mới có quyền thực hiện việc này."
```

### Department-based Errors

```python
DEPARTMENT_PERMISSION_DENIED = "Department của bạn không có quyền quản lý loại tài liệu này. Hãy liên hệ Manager của department tương ứng."

# Department-specific
DPA_MANAGER_ONLY = "Chỉ DPA Manager hoặc Admin mới có quyền thực hiện việc này."
CREWING_MANAGER_ONLY = "Chỉ Crewing Manager hoặc Admin mới có quyền thực hiện việc này."
TECHNICAL_MANAGER_ONLY = "Chỉ Technical Manager hoặc Admin mới có quyền thực hiện việc này."
SAFETY_MANAGER_ONLY = "Chỉ Safety Manager hoặc Admin mới có quyền thực hiện việc này."
```

---

## 5. Real-world Scenarios

### Scenario 1: Technical Manager Upload Ship Certificate

**User Info:**
```json
{
  "username": "technical_manager1",
  "role": "manager",
  "company": "hai_an_container",
  "department": ["technical"]
}
```

**Action:** Upload ship certificate to Ship "HAI AN 1"

**Permission Flow:**
```
1. check_company_access(user, "hai_an_container")
   → ✅ Pass (same company)

2. check_create_permission(user, "ship_cert", "hai_an_container")
   → check_minimum_role(user, MANAGER)  → ✅ Pass (is Manager)
   → check_manager_department_permission(user, "ship_cert")
       → can_manage_document_type(["technical"], "ship_cert")
       → ship_cert → "Class & Flag Cert" → ["technical", "supply"]
       → "technical" in ["technical", "supply"]
       → ✅ Pass

3. check_editor_viewer_ship_scope(user, "ship_001")
   → user.role = "manager" (not Editor/Viewer)
   → ✅ Pass (không áp dụng)

RESULT: ✅ SUCCESS - Certificate uploaded
```

### Scenario 2: Crewing Manager Try Upload Ship Certificate

**User Info:**
```json
{
  "username": "crewing_manager1",
  "role": "manager",
  "company": "hai_an_container",
  "department": ["crewing"]
}
```

**Action:** Upload ship certificate

**Permission Flow:**
```
1. check_company_access(user, "hai_an_container")
   → ✅ Pass

2. check_create_permission(user, "ship_cert", "hai_an_container")
   → check_minimum_role(user, MANAGER)  → ✅ Pass
   → check_manager_department_permission(user, "ship_cert")
       → can_manage_document_type(["crewing"], "ship_cert")
       → ship_cert → "Class & Flag Cert" → ["technical", "supply"]
       → "crewing" NOT in ["technical", "supply"]
       → ❌ FAIL

RESULT: ❌ 403 Error
Message: "Department của bạn không có quyền quản lý loại tài liệu này (Category: Class & Flag Cert). 
         Hãy liên hệ Manager của department tương ứng."
```

### Scenario 3: Editor View Company Certificates

**User Info:**
```json
{
  "username": "editor1",
  "role": "editor",
  "company": "hai_an_container",
  "assigned_ship_id": "ship_001"
}
```

**Action:** View company certificates

**Permission Flow:**
```
1. can_view_company_certificates(user)
   → user.role = "editor"
   → role != "viewer"
   → ✅ Pass (Editor CAN view Company Certs!)

2. check_company_access(user, "hai_an_container")
   → ✅ Pass

RESULT: ✅ SUCCESS - Company certificates shown
```

### Scenario 4: Viewer Try View Company Certificates

**User Info:**
```json
{
  "username": "viewer1",
  "role": "viewer",
  "company": "hai_an_container",
  "assigned_ship_id": "ship_001"
}
```

**Action:** View company certificates

**Permission Flow:**
```
1. can_view_company_certificates(user)
   → user.role = "viewer"
   → role == "viewer"
   → ❌ FAIL

RESULT: ❌ 403 Error
Message: "Truy cập bị từ chối. Bạn không có quyền xem nội dung này."
```

### Scenario 5: Editor View Ship Certificates

**User Info:**
```json
{
  "username": "editor1",
  "role": "editor",
  "company": "hai_an_container",
  "assigned_ship_id": "ship_001"  // Assigned to HAI AN 1
}
```

**Action:** View ship certificates

**Permission Flow:**
```
1. Company filtering
   → Get all ships of "hai_an_container"
   → ["ship_001", "ship_002", "ship_003"]
   → Get certificates for these ships
   → [cert1 (ship_001), cert2 (ship_002), cert3 (ship_003)]

2. filter_documents_by_ship_scope(certificates, user)
   → user.role = "editor"
   → user.assigned_ship_id = "ship_001"
   → Filter: [cert for cert in certificates if cert.ship_id == "ship_001"]
   → Result: [cert1]  // Only ship_001 certificates

RESULT: ✅ SUCCESS - Only certificates of HAI AN 1 shown
```

### Scenario 6: Admin Access Different Company

**User Info:**
```json
{
  "username": "admin1",
  "role": "admin",
  "company": "company_a"
}
```

**Action:** Try to view Company B's certificates

**Permission Flow:**
```
1. check_company_access(user, "company_b")
   → user.role = "admin" (not system_admin)
   → user.company = "company_a"
   → target_company = "company_b"
   → "company_a" != "company_b"
   → ❌ FAIL

RESULT: ❌ 403 Error
Message: "Bạn không có quyền truy cập dữ liệu của công ty này."
```

---

## 📊 Permission Matrix Summary

| Role | Company Scope | Department Scope | Ship Scope | Company Cert Access |
|------|---------------|------------------|------------|---------------------|
| **System Admin** | All | All | All | ✅ Full |
| **Super Admin** | All | All | All | ✅ Full |
| **Admin** | Own company only | All (không bị giới hạn) | All ships in company | ✅ Full |
| **Manager** | Own company only | Own departments only | All ships in company | ✅ Full |
| **Editor** | Own company only | N/A (View only) | Assigned ship only | ✅ View only |
| **Viewer** | Own company only | N/A (View only) | Assigned ship only | ❌ No access |

---

## 🔧 Utility Functions Reference

### Check Functions (raise HTTPException on fail)

```python
from app.core.permission_checks import *

# Company access
check_company_access(user, company_id, action="access")

# Ship access
check_ship_access(user, ship_company_id)
check_editor_viewer_ship_scope(user, ship_id, action="access")

# Manager department permission
check_manager_department_permission(user, document_type, action="create")

# Minimum role
check_minimum_role(user, UserRole.MANAGER, action="perform this action")

# Comprehensive checks (combines multiple checks)
check_create_permission(user, document_type, company_id)
check_edit_permission(user, document_type, company_id)
check_delete_permission(user, document_type, company_id)
```

### Query/Filter Functions (return boolean or filtered list)

```python
from app.core.permission_checks import *

# Check if user can view Company Certificates
can_view = can_view_company_certificates(user)  # → True/False

# Filter documents for Editor/Viewer by ship scope
filtered_docs = filter_documents_by_ship_scope(documents, user)
```

### Department Functions

```python
from app.core.department_permissions import *

# Get categories user can manage
categories = get_managed_categories(["technical", "supply"])
# → ["Class & Flag Cert", "Technical Infor", "Supplies"]

# Check if user can manage specific category
can_manage = can_manage_category(["technical"], "Class & Flag Cert")  # → True

# Check if user can manage specific document type
can_manage = can_manage_document_type(["crewing"], "crew_cert")  # → True

# Get category for document type
category = get_category_for_document_type("ship_cert")
# → "Class & Flag Cert"
```

---

## ✅ Implementation Checklist

### Services Updated
- ✅ `certificate_multi_upload_service.py` - Ship cert upload
- ✅ `certificate_service.py` - Ship cert CRUD
- ✅ `company_cert_service.py` - Company cert CRUD + Editor view access
- ✅ `crew_certificate_service.py` - Crew cert CRUD

### Core Modules
- ✅ `messages.py` - 10 new Vietnamese error messages
- ✅ `department_permissions.py` - Department mapping & utilities
- ✅ `permission_checks.py` - Centralized permission functions

### Testing Required
- ⏳ Backend testing agent verification
- ⏳ Role-based access testing
- ⏳ Department permission testing
- ⏳ Ship scope filtering testing

---

**Bạn có muốn tôi:**
1. Chạy backend testing agent để verify các scenarios trên?
2. Tiếp tục implement các services còn lại?
3. Có câu hỏi về bất kỳ phần nào trong demo?

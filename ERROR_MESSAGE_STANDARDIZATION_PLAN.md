# Error Message Standardization Plan

## 🎯 **OBJECTIVE**

Standardize all 403 permission error messages to use Vietnamese messages from `/app/backend/app/core/messages.py`

---

## 📊 **CURRENT STATE ANALYSIS**

### **✅ GOOD (Already using messages.py):**

| File | Count | Status |
|------|-------|--------|
| `company_certs.py` | 1 | ✅ Uses `PERMISSION_DENIED` |
| `crew_audit_logs.py` | 7 | ✅ Uses `PERMISSION_DENIED` & `SYSTEM_ADMIN_ONLY` |
| `approval_documents.py` | 1 | ✅ Uses `PERMISSION_DENIED` |
| `certificates.py` | 1 | ✅ Uses `PERMISSION_DENIED` |
| `companies.py` | 2 | ✅ Uses `PERMISSION_DENIED` & `SYSTEM_ADMIN_ONLY` |

**Total: 12 occurrences** ✅

---

### **❌ BAD (Using hardcoded English messages):**

#### **Type 1: "Access denied" (20 occurrences)**

| File | Line | Current Message |
|------|------|----------------|
| `crew_certificate_service.py` | 310, 545, 619 | "Access denied" |
| `crew_assignment_service.py` | 95, 333, 534 | "Access denied" |
| `crew_service.py` | 54, 138, 253 | "Access denied" |
| `audit_report_service.py` | 223 | "Access denied" |
| `ship_service.py` | 52, 111, 157 | "Access denied" |
| `certificate_service.py` | 50, 88 | "Access denied" |
| `approval_document_service.py` | 197 | "Access denied" |
| `crew_certificates.py` (API) | 168 | "Access denied" |
| `audit_certificates.py` (API) | 288, 613 | "Access denied" |

#### **Type 2: "Access denied to this ship" (3 occurrences)**

| File | Line | Current Message |
|------|------|----------------|
| `audit_report_service.py` | 410 | "Access denied to this ship" |
| `approval_document_service.py` | 387 | "Access denied to this ship" |
| `approval_document_analyze_service.py` | 125 | "Access denied to this ship" |

#### **Type 3: "Insufficient permissions" (11 occurrences)**

| File | Line | Current Message |
|------|------|----------------|
| `crew_certificates.py` | 22 | "Insufficient permissions" |
| `system_settings.py` | 14 | "Insufficient permissions" |
| `survey_reports.py` | 16 | "Insufficient permissions" |
| `test_reports.py` | 16 | "Insufficient permissions" |
| `other_documents.py` | 17 | "Insufficient permissions" |
| `ships.py` | 23 | "Insufficient permissions" |
| `supply_documents.py` | 19 | "Insufficient permissions" |
| `other_audit_documents.py` | 17 | "Insufficient permissions" |
| `drawings_manuals.py` | 16 | "Insufficient permissions" |

#### **Type 4: "Admin permission required" (1 occurrence)**

| File | Line | Current Message |
|------|------|----------------|
| `gdrive.py` | 20 | "Admin permission required" |

#### **Type 5: Special case (1 occurrence)**

| File | Line | Current Message |
|------|------|----------------|
| `companies.py` | 82 | "Admin can only update their own company" |

**Total to fix: 36 occurrences** ❌

---

## 📝 **UPDATED messages.py**

### **Current Content:**
```python
# Permission error messages (Vietnamese)
PERMISSION_DENIED = "Bạn không được cấp quyền để thực hiện việc này. Hãy liên hệ Admin."
ADMIN_ONLY = "Chỉ Admin mới có quyền thực hiện việc này. Hãy liên hệ Admin."
SYSTEM_ADMIN_ONLY = "Chỉ System Admin mới có quyền thực hiện việc này."
ACCESS_DENIED = "Truy cập bị từ chối. Bạn không có quyền xem nội dung này."
```

### **ADD New Messages:**
```python
# Specific permission messages
ACCESS_DENIED_SHIP = "Bạn không có quyền truy cập tàu này. Chỉ có thể xem tàu của công ty mình hoặc tàu đang sign on."
ACCESS_DENIED_COMPANY = "Bạn không có quyền truy cập dữ liệu của công ty này."
EDITOR_ONLY = "Chỉ Editor hoặc cao hơn mới có quyền thực hiện việc này."
MANAGER_ONLY = "Chỉ Manager hoặc cao hơn mới có quyền thực hiện việc này."
DEPARTMENT_PERMISSION_DENIED = "Department của bạn không có quyền quản lý loại tài liệu này."

# Role-specific messages
DPA_MANAGER_ONLY = "Chỉ DPA Manager hoặc Admin mới có quyền thực hiện việc này."
CREWING_MANAGER_ONLY = "Chỉ Crewing Manager hoặc Admin mới có quyền thực hiện việc này."

# Special cases
ADMIN_OWN_COMPANY_ONLY = "Admin chỉ có thể cập nhật thông tin công ty của mình."
```

---

## 🔧 **MAPPING TABLE**

| Current English Message | Replace With | Constant Name |
|------------------------|--------------|---------------|
| "Access denied" | "Truy cập bị từ chối..." | `ACCESS_DENIED` |
| "Access denied to this ship" | "Bạn không có quyền truy cập tàu này..." | `ACCESS_DENIED_SHIP` |
| "Insufficient permissions" | "Bạn không được cấp quyền..." | `PERMISSION_DENIED` |
| "Admin permission required" | "Chỉ Admin mới có quyền..." | `ADMIN_ONLY` |
| "Admin can only update their own company" | "Admin chỉ có thể cập nhật..." | `ADMIN_OWN_COMPANY_ONLY` |

---

## 🛠️ **IMPLEMENTATION PLAN**

### **Step 1: Update messages.py (5 minutes)**

**File:** `/app/backend/app/core/messages.py`

**Add:**
```python
# Specific permission messages
ACCESS_DENIED_SHIP = "Bạn không có quyền truy cập tàu này. Chỉ có thể xem tàu của công ty mình hoặc tàu đang sign on."
ACCESS_DENIED_COMPANY = "Bạn không có quyền truy cập dữ liệu của công ty này."
EDITOR_ONLY = "Chỉ Editor hoặc cao hơn mới có quyền thực hiện việc này."
MANAGER_ONLY = "Chỉ Manager hoặc cao hơn mới có quyền thực hiện việc này."
DEPARTMENT_PERMISSION_DENIED = "Department của bạn không có quyền quản lý loại tài liệu này."

# Role-specific messages
DPA_MANAGER_ONLY = "Chỉ DPA Manager hoặc Admin mới có quyền thực hiện việc này."
CREWING_MANAGER_ONLY = "Chỉ Crewing Manager hoặc Admin mới có quyền thực hiện việc này."

# Special cases
ADMIN_OWN_COMPANY_ONLY = "Admin chỉ có thể cập nhật thông tin công ty của mình."
```

---

### **Step 2: Fix Service Files (15 minutes)**

#### **2.1: crew_certificate_service.py (3 changes)**
```python
# Add import at top
from app.core.messages import ACCESS_DENIED

# Replace lines 310, 545, 619
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)
```

#### **2.2: crew_assignment_service.py (3 changes)**
```python
# Add import
from app.core.messages import ACCESS_DENIED

# Replace lines 95, 333, 534
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)
```

#### **2.3: crew_service.py (3 changes)**
```python
# Add import
from app.core.messages import ACCESS_DENIED

# Replace lines 54, 138, 253
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)
```

#### **2.4: audit_report_service.py (2 changes)**
```python
# Add import
from app.core.messages import ACCESS_DENIED, ACCESS_DENIED_SHIP

# Replace line 223
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)

# Replace line 410
- raise HTTPException(status_code=403, detail="Access denied to this ship")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED_SHIP)
```

#### **2.5: ship_service.py (3 changes)**
```python
# Add import
from app.core.messages import ACCESS_DENIED

# Replace lines 52, 111, 157
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)
```

#### **2.6: certificate_service.py (2 changes)**
```python
# Add import
from app.core.messages import ACCESS_DENIED

# Replace lines 50, 88
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)
```

#### **2.7: approval_document_service.py (2 changes)**
```python
# Add import
from app.core.messages import ACCESS_DENIED, ACCESS_DENIED_SHIP

# Replace line 197
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)

# Replace line 387
- raise HTTPException(status_code=403, detail="Access denied to this ship")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED_SHIP)
```

#### **2.8: approval_document_analyze_service.py (1 change)**
```python
# Add import
from app.core.messages import ACCESS_DENIED_SHIP

# Replace line 125
- raise HTTPException(status_code=403, detail="Access denied to this ship")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED_SHIP)
```

---

### **Step 3: Fix API Files (15 minutes)**

#### **3.1: crew_certificates.py (2 changes)**
```python
# Add import
from app.core.messages import PERMISSION_DENIED, ACCESS_DENIED

# Replace line 22
- raise HTTPException(status_code=403, detail="Insufficient permissions")
+ raise HTTPException(status_code=403, detail=PERMISSION_DENIED)

# Replace line 168
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)
```

#### **3.2: Multiple API files with "Insufficient permissions" (9 files)**

**Files:**
- `system_settings.py`
- `survey_reports.py`
- `test_reports.py`
- `other_documents.py`
- `ships.py`
- `supply_documents.py`
- `other_audit_documents.py`
- `drawings_manuals.py`

**Pattern for all:**
```python
# Add import
from app.core.messages import PERMISSION_DENIED

# Replace
- raise HTTPException(status_code=403, detail="Insufficient permissions")
+ raise HTTPException(status_code=403, detail=PERMISSION_DENIED)
```

#### **3.3: gdrive.py (1 change)**
```python
# Add import
from app.core.messages import ADMIN_ONLY

# Replace line 20
- raise HTTPException(status_code=403, detail="Admin permission required")
+ raise HTTPException(status_code=403, detail=ADMIN_ONLY)
```

#### **3.4: audit_certificates.py (2 changes)**
```python
# Add import
from app.core.messages import ACCESS_DENIED

# Replace lines 288, 613
- raise HTTPException(status_code=403, detail="Access denied")
+ raise HTTPException(status_code=403, detail=ACCESS_DENIED)
```

#### **3.5: companies.py (1 change)**
```python
# Add import
from app.core.messages import ADMIN_OWN_COMPANY_ONLY

# Replace line 82
- raise HTTPException(status_code=403, detail="Admin can only update their own company")
+ raise HTTPException(status_code=403, detail=ADMIN_OWN_COMPANY_ONLY)
```

---

## 📊 **SUMMARY**

### **Files to Modify:**

| Category | Count | Files |
|----------|-------|-------|
| **messages.py** | 1 | Add new constants |
| **Service Files** | 8 | crew_certificate, crew_assignment, crew, audit_report, ship, certificate, approval_document, approval_document_analyze |
| **API Files** | 13 | crew_certificates, system_settings, survey_reports, test_reports, other_documents, ships, supply_documents, other_audit_documents, drawings_manuals, gdrive, audit_certificates, companies |
| **TOTAL** | 22 | |

### **Changes Count:**

| Type | Count |
|------|-------|
| **Add imports** | 21 files |
| **Replace messages** | 36 locations |
| **Update messages.py** | 8 new constants |
| **TOTAL CHANGES** | 65+ |

---

## 🎯 **EXPECTED RESULTS**

### **Before:**
```python
raise HTTPException(status_code=403, detail="Access denied")
# User sees: "Access denied" (English, không rõ ràng)
```

### **After:**
```python
from app.core.messages import ACCESS_DENIED
raise HTTPException(status_code=403, detail=ACCESS_DENIED)
# User sees: "Truy cập bị từ chối. Bạn không có quyền xem nội dung này." (Vietnamese, rõ ràng)
```

---

## ✅ **BENEFITS**

1. **🇻🇳 Consistent Vietnamese:** Tất cả error messages đều Vietnamese
2. **📝 Centralized:** Dễ update messages ở 1 chỗ
3. **👤 User-friendly:** Messages rõ ràng, hướng dẫn user
4. **🔧 Maintainable:** Dễ maintain và mở rộng
5. **🌐 I18n Ready:** Sẵn sàng cho multi-language support

---

## 🧪 **TESTING CHECKLIST**

After implementation:

```
✅ Login as Editor → Try to create certificate → See Vietnamese error
✅ Login as Manager (non-DPA) → Try to create Company Cert → See Vietnamese error
✅ Login as Admin (Company A) → Try to access Ship B → See Vietnamese error
✅ All 403 errors show Vietnamese messages
✅ Error messages are clear and helpful
```

---

## ⏱️ **TIMELINE**

| Step | Task | Time |
|------|------|------|
| 1 | Update messages.py | 5 min |
| 2 | Fix 8 service files | 15 min |
| 3 | Fix 13 API files | 15 min |
| 4 | Test all endpoints | 10 min |
| 5 | Lint & verify | 5 min |
| **TOTAL** | | **50 minutes** |

---

## 🚀 **EXECUTION ORDER**

1. ✅ Update `/app/backend/app/core/messages.py`
2. ✅ Fix service files (8 files)
3. ✅ Fix API files (13 files)
4. ✅ Run linter
5. ✅ Test with different roles
6. ✅ Verify all messages Vietnamese

---

## 📝 **POST-IMPLEMENTATION**

**Guideline for future development:**

```python
# ❌ DON'T DO THIS
raise HTTPException(status_code=403, detail="Access denied")

# ✅ DO THIS
from app.core.messages import ACCESS_DENIED
raise HTTPException(status_code=403, detail=ACCESS_DENIED)
```

**Add to code review checklist:**
- [ ] All HTTPException 403 use constants from messages.py
- [ ] No hardcoded English error messages
- [ ] Error messages are user-friendly Vietnamese

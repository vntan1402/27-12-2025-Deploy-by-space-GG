# 🔍 CICA (CREW ACCOMMODATION) - CLARIFICATION & DECISION

## ❓ QUESTION
**Validation Rules: ❌ Non-ISM/ISPS/MLC → REJECT**  
**→ CICA có reject không?**

---

## 📊 PHÂN TÍCH HIỆN TRẠNG

### Backend V1 - Audit Certificate Module

#### Dictionary ISM_ISPS_MLC_CERTIFICATES (Lines 53-81):
```python
ISM_ISPS_MLC_CERTIFICATES = {
    "ism": [
        "SAFETY MANAGEMENT CERTIFICATE",
        "INTERIM SAFETY MANAGEMENT CERTIFICATE",
        "SMC",
        "DOCUMENT OF COMPLIANCE",
        "INTERIM DOCUMENT OF COMPLIANCE",
        "DOC",
    ],
    "isps": [
        "INTERNATIONAL SHIP SECURITY CERTIFICATE",
        "INTERIM INTERNATIONAL SHIP SECURITY CERTIFICATE",
        "ISSC",
        "SHIP SECURITY PLAN",
        "SSP",
    ],
    "mlc": [
        "MARITIME LABOUR CERTIFICATE",
        "INTERIM MARITIME LABOUR CERTIFICATE",
        "MLC",
        "DECLARATION OF MARITIME LABOUR COMPLIANCE",
        "DMLC",
        "DMLC PART I",
        "DMLC PART II",
    ]
}
```

**❌ KHÔNG có CICA trong dictionary**

#### Function check_ism_isps_mlc_category (Lines 2265-2291):
```python
def check_ism_isps_mlc_category(cert_name: str) -> dict:
    """
    Check if certificate belongs to ISM/ISPS/MLC categories
    Returns dict with 'is_valid' and 'category' or 'message'
    """
    if not cert_name:
        return {"is_valid": False, "message": "Certificate name is empty"}
    
    # Normalize cert name for comparison
    cert_name_upper = cert_name.upper().strip()
    
    # Check against all ISM/ISPS/MLC certificates
    for category, cert_list in ISM_ISPS_MLC_CERTIFICATES.items():
        for valid_cert in cert_list:
            if valid_cert in cert_name_upper or cert_name_upper in valid_cert:
                return {
                    "is_valid": True, 
                    "category": category.upper(),
                    "matched_cert": valid_cert
                }
    
    # Not found in any category
    return {
        "is_valid": False,
        "message": f"Certificate '{cert_name}' does not belong to ISM/ISPS/MLC categories"
    }
```

**❌ Function này CHỈ check ISM/ISPS/MLC, KHÔNG check CICA**

#### Multi-Upload Logic (Lines 27219-27243):
```python
# ===== CATEGORY VALIDATION (ISM/ISPS/MLC CHECK) =====
if cert_name:
    category_check = check_ism_isps_mlc_category(cert_name)
    
    if not category_check.get('is_valid'):
        logger.warning(f"⚠️ Category mismatch for {file.filename}: '{cert_name}' is not ISM/ISPS/MLC")
        
        summary["errors"] += 1
        results.append({
            "filename": file.filename,
            "status": "error",
            "message": f"Giấy chứng nhận '{cert_name}' không thuộc danh mục ISM/ISPS/MLC",
            "category_mismatch": True
        })
        continue  # Skip this file
```

**✅ Kết luận Backend V1 Audit Certificate:**
- **CICA SẼ BỊ REJECT** vì không có trong `ISM_ISPS_MLC_CERTIFICATES`

---

### Backend V1 - Audit Report Module (Khác với Audit Certificate!)

#### Audit Report AI Logic (audit_report_ai.py style code):
```python
# Lines 6952-6953, 6964-6965, 6976-6977, 6988-6989
if 'CICA' in filename_upper:
    audit_type = 'CICA'

if 'CREW ACCOMMODATION' in filename_upper:
    audit_type = 'CICA'
    logger.info("✅ Detected 'CREW ACCOMMODATION' in filename → type = CICA")
```

**✅ CICA được hỗ trợ trong Audit Report module**

---

## 🤔 VẤN ĐỀ PHÁT HIỆN

### Confusion giữa 2 modules:

1. **Audit Certificate** (`/audit-certificates` endpoint):
   - Certificates: ISM Safety Management Certificate, ISPS Security Certificate, MLC Labour Certificate
   - **KHÔNG hỗ trợ CICA**
   - Dictionary `ISM_ISPS_MLC_CERTIFICATES` chỉ có 3 categories

2. **Audit Report** (`/audit-reports` endpoint):
   - Reports: ISM Audit Report, ISPS Verification Report, MLC Inspection Report, **CICA Report**
   - **CÓ hỗ trợ CICA** (Crew Accommodation)
   - Có logic đặc biệt cho "CREW ACCOMMODATION"

---

## 🎯 DECISION & RECOMMENDATION

### Option 1: GIỮ NGUYÊN (CHỈ ISM/ISPS/MLC) ⭐ RECOMMENDED

**Lý do:**
- ✅ Đúng với logic Backend V1 hiện tại
- ✅ Audit Certificate != Audit Report (2 modules khác nhau)
- ✅ CICA (Crew Accommodation) thuộc Audit Report, không phải Audit Certificate
- ✅ Tránh confusion giữa Certificate và Report

**Implementation:**
```python
# Check category - ONLY ISM/ISPS/MLC for Audit Certificates
VALID_AUDIT_CERT_CATEGORIES = ["ISM", "ISPS", "MLC"]

def check_audit_certificate_category(cert_name: str) -> dict:
    """
    Check if certificate belongs to ISM/ISPS/MLC categories
    
    CICA (Crew Accommodation) is NOT included here because:
    - CICA belongs to Audit Report module (separate)
    - This is for Audit Certificates only
    """
    # Check logic...
```

**Validation message:**
```
❌ "Giấy chứng nhận '{cert_name}' không thuộc danh mục ISM/ISPS/MLC"
```

---

### Option 2: THÊM CICA VÀO AUDIT CERTIFICATE (Mở rộng)

**Lý do:**
- ⚠️ Một số user có thể có CICA certificates (không phải reports)
- ⚠️ CICA (Certificate of Inspection for Crew Accommodation) là loại certificate hợp lệ
- ⚠️ Tăng tính linh hoạt

**Implementation:**
```python
# Expand to include CICA
VALID_AUDIT_CERT_CATEGORIES = ["ISM", "ISPS", "MLC", "CICA"]

ISM_ISPS_MLC_CICA_CERTIFICATES = {
    "ism": [...],
    "isps": [...],
    "mlc": [...],
    "cica": [
        "CERTIFICATE OF INSPECTION",
        "CREW ACCOMMODATION CERTIFICATE",
        "STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
        "CICA",
    ]
}
```

**Validation message:**
```
❌ "Giấy chứng nhận '{cert_name}' không thuộc danh mục ISM/ISPS/MLC/CICA"
```

**Trade-offs:**
- ⚠️ Khác với Backend V1 (breaking change)
- ⚠️ Cần update UI (folder structure, filters)
- ⚠️ Cần update documentation

---

## 💡 FINAL RECOMMENDATION

### ⭐ **OPTION 1: GIỮ NGUYÊN (CHỈ ISM/ISPS/MLC)**

**Lý do chọn:**

1. **Consistency với Backend V1**
   - Backend V1 Audit Certificate đã hoạt động tốt
   - User đang quen với flow hiện tại
   - Không có bug reports về việc thiếu CICA

2. **Separation of Concerns**
   - Audit Certificate ≠ Audit Report
   - CICA Report đã có trong Audit Report module
   - Tránh duplicate functionality

3. **Folder Structure**
   - Path hiện tại: `{ShipName}/ISM - ISPS - MLC/Audit Certificates/`
   - Tên folder đã clear: "ISM - ISPS - MLC"
   - Nếu thêm CICA → phải đổi tên folder → breaking change lớn

4. **User Experience**
   - Filters hiện tại: ISM / ISPS / MLC
   - Table columns design cho 3 types
   - UI/UX đã optimize cho 3 categories

---

## 📋 IMPLEMENTATION PLAN (Option 1)

### Code Updates:

#### 1. Category Validation Function:
```python
# File: /app/backend/app/services/audit_certificate_analyze_service.py

# Certificate categories dictionary
AUDIT_CERTIFICATE_CATEGORIES = {
    "ism": [
        "SAFETY MANAGEMENT CERTIFICATE",
        "INTERIM SAFETY MANAGEMENT CERTIFICATE",
        "SMC",
        "DOCUMENT OF COMPLIANCE",
        "INTERIM DOCUMENT OF COMPLIANCE",
        "DOC",
    ],
    "isps": [
        "INTERNATIONAL SHIP SECURITY CERTIFICATE",
        "INTERIM INTERNATIONAL SHIP SECURITY CERTIFICATE",
        "ISSC",
        "SHIP SECURITY PLAN",
        "SSP",
    ],
    "mlc": [
        "MARITIME LABOUR CERTIFICATE",
        "INTERIM MARITIME LABOUR CERTIFICATE",
        "MLC",
        "DECLARATION OF MARITIME LABOUR COMPLIANCE",
        "DMLC",
        "DMLC PART I",
        "DMLC PART II",
    ]
}

@staticmethod
async def check_category_ism_isps_mlc(cert_name: str) -> Dict[str, Any]:
    """
    Check if certificate belongs to ISM/ISPS/MLC categories
    
    NOTE: CICA (Crew Accommodation) is NOT included here.
    CICA belongs to Audit Report module, not Audit Certificate.
    
    Args:
        cert_name: Certificate name to check
    
    Returns:
        dict: {
            "is_valid": bool,
            "category": "ISM" | "ISPS" | "MLC" | null,
            "message": str
        }
    """
    if not cert_name:
        return {
            "is_valid": False,
            "category": None,
            "message": "Certificate name is empty"
        }
    
    cert_name_upper = cert_name.upper().strip()
    
    # Check against all ISM/ISPS/MLC certificates
    for category, cert_list in AUDIT_CERTIFICATE_CATEGORIES.items():
        for valid_cert in cert_list:
            if valid_cert in cert_name_upper or cert_name_upper in valid_cert:
                return {
                    "is_valid": True,
                    "category": category.upper(),
                    "matched_cert": valid_cert,
                    "message": f"Valid {category.upper()} certificate"
                }
    
    # Not found in any category
    return {
        "is_valid": False,
        "category": None,
        "message": f"Certificate '{cert_name}' does not belong to ISM/ISPS/MLC categories"
    }
```

#### 2. Error Messages (Vietnamese + English):
```python
# Vietnamese
"Giấy chứng nhận '{cert_name}' không thuộc danh mục ISM/ISPS/MLC"
"Vui lòng upload ISM, ISPS, hoặc MLC certificates"

# English
"Certificate '{cert_name}' does not belong to ISM/ISPS/MLC categories"
"Please upload ISM, ISPS, or MLC certificates"
```

#### 3. Google Drive Path (KHÔNG thay đổi):
```python
# Path remains:
f"{ship_name}/ISM - ISPS - MLC/Audit Certificates/{filename}"

# NOT changed to:
# f"{ship_name}/ISM - ISPS - MLC - CICA/Audit Certificates/{filename}"
```

---

## 🔄 ALTERNATIVE: Nếu user yêu cầu CICA

### Nếu sau này cần thêm CICA:

**Migration Steps:**

1. **Update Dictionary:**
```python
AUDIT_CERTIFICATE_CATEGORIES = {
    "ism": [...],
    "isps": [...],
    "mlc": [...],
    "cica": [  # ⭐ NEW
        "CERTIFICATE OF INSPECTION",
        "CREW ACCOMMODATION CERTIFICATE",
        "STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
        "CICA",
    ]
}
```

2. **Update Validation Function:**
```python
# Change function name
check_category_ism_isps_mlc_cica()  # Add CICA
```

3. **Update Google Drive Path:**
```python
# Option A: Keep same folder (recommended)
f"{ship_name}/ISM - ISPS - MLC/Audit Certificates/{filename}"

# Option B: New folder name
f"{ship_name}/ISM - ISPS - MLC - CICA/Audit Certificates/{filename}"
```

4. **Update Frontend:**
- Filters: Add "CICA" option
- Table columns: Handle 4 categories
- Upload guidelines: Mention CICA

5. **Update Documentation:**
- API docs
- User guide
- Migration notes

**Effort Estimate:** 2-3 hours

---

## ✅ FINAL ANSWER

### CÂU TRẢ LỜI CHÍNH THỨC:

**Validation Rules: ❌ Non-ISM/ISPS/MLC → REJECT**

**→ CICA có reject không?**

# ✅ **CÓ, CICA SẼ BỊ REJECT**

**Lý do:**
1. ✅ Backend V1 hiện tại đang reject CICA trong Audit Certificate module
2. ✅ CICA thuộc Audit **Report** module (khác module)
3. ✅ Dictionary `ISM_ISPS_MLC_CERTIFICATES` không có CICA
4. ✅ Function `check_ism_isps_mlc_category()` chỉ accept 3 categories
5. ✅ Google Drive path folder tên "ISM - ISPS - MLC" (không có CICA)

**Implementation trong Backend V2:**
- Validation: CHỈ accept ISM, ISPS, MLC
- CICA certificate → Reject với error message
- Error message: "Giấy chứng nhận không thuộc danh mục ISM/ISPS/MLC"

**Nếu user cần upload CICA:**
- Hướng dẫn user upload vào **Audit Report** module thay vì Audit Certificate
- Hoặc (nếu cần) sau này mở rộng thêm CICA category (2-3 hours effort)

---

**Status**: ✅ Clarified  
**Decision**: CICA will be REJECTED in Audit Certificate module  
**Reason**: Consistency with Backend V1 + Separation of modules  
**Alternative**: Can add CICA later if business requirement changes

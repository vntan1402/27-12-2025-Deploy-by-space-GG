# AUDIT REPORT NO. & STATUS LOGIC - BACKEND V1 & V2

## 📋 TỔNG QUAN

Document này mô tả chi tiết logic xác định **Audit Report No.** và **Status** cho Audit Reports trong cả Backend V1 và V2.

---

## 🔢 AUDIT REPORT NO. (audit_report_no)

### 1. ĐỊNH NGHĨA

**Audit Report No.** là mã số/số tham chiếu duy nhất của báo cáo audit, do tổ chức audit cấp phát.

**Examples:**
- `A/25/1573`
- `AUD-2024-001`
- `REP-12345`
- `ISM-2024-001`
- `AR-001/2024`

### 2. EXTRACTION LOGIC (Backend V1 & V2)

**Source:** AI extraction from Document AI summary

**Priority Order:**
1. **Direct PDF extraction** (Gemini reads PDF directly)
   - More reliable for extracting reference numbers
   - Can read header/footer content
   
2. **Summary-based extraction** (fallback)
   - Extract from Document AI summary text
   - System AI (Gemini) parses summary

**Extraction Rules (from prompt):**

```
**audit_report_no**: 
- Extract the audit report number or reference number
- Examples: "A/25/1573", "AUD-2024-001", "REP-12345"
- Look for labels: "Report No.", "Reference No.", "Audit No.", "Document No."
- May be alphanumeric with slashes, dashes, or dots
- Usually appears near header, footer, or first page
```

### 3. WHERE TO FIND

**Common Locations:**
- Document header (top right or left)
- Document footer
- First page near title
- Near "Report No:" or "Reference:" labels
- In document metadata section

**Pattern Recognition:**
- Alphanumeric codes: `AUD-2024-001`, `AR-123`
- Slash separated: `A/25/1573`, `2024/ISM/001`
- Dot separated: `REP.2024.001`
- Hyphen separated: `ISM-2024-001`

### 4. POST-PROCESSING

**Backend V1 & V2:**
- No special post-processing for audit_report_no
- Extracted as-is from AI
- Empty string if not found

### 5. IMPLEMENTATION IN V2

**File:** `/app/backend/app/utils/audit_report_ai.py`

**Logic:**
```python
# In extraction prompt (lines 138-175)
prompt = f"""
...
**audit_report_no**: 
- Extract the audit report number or reference number
- Examples: "A/25/1573", "AUD-2024-001", "REP-12345"
...
"""

# AI extracts and returns in JSON
extracted_data = {
    "audit_report_no": "A/25/1573",  # Example
    ...
}

# No post-processing needed
return extracted_data
```

---

## ✅ STATUS FIELD

### 1. ĐỊNH NGHĨA

**Status** cho biết trạng thái hiện tại của audit report.

**Possible Values:**
- **Valid** - Audit report còn hiệu lực
- **Expired** - Audit report đã hết hạn
- **Pending** - Đang chờ xử lý
- **Other** - Trạng thái khác

### 2. LOGIC XÁC ĐỊNH STATUS

#### 2.1 Backend V1 Logic

**Location:** `/app/backend-v1/server.py` line 10066

**Logic:**
```python
# HARDCODED - Always set to "Valid"
analysis_result.update({
    'audit_report_name': extracted_fields.get('audit_report_name', ''),
    'audit_type': extracted_fields.get('audit_type', ''),
    # ... other fields ...
    'status': 'Valid',  # ← HARDCODED
    'confidence_score': 0.9,
})
```

**Conclusion:** Backend V1 **KHÔNG có logic tự động tính Status**. Luôn luôn là `"Valid"`.

#### 2.2 Backend V2 Logic

**Location:** `/app/backend/app/services/audit_report_analyze_service.py`

**Current Implementation:**
```python
# In _process_small_pdf() method
analysis_result = {
    "audit_report_name": "",
    # ... other fields ...
    "status": "Valid",  # ← HARDCODED (matching V1)
}
```

**Conclusion:** Backend V2 cũng **match 100% với V1** - Status luôn là `"Valid"`.

### 3. TẠI SAO KHÔNG TỰ ĐỘNG TÍNH STATUS?

**Lý do:**

1. **Audit Reports khác với Certificates:**
   - Certificates có `expiry_date` rõ ràng → có thể tính Valid/Expired
   - Audit Reports chỉ có `audit_date` (ngày audit) → KHÔNG có expiry date

2. **Audit Report không "expire":**
   - Audit reports là bản ghi lịch sử
   - Chúng không hết hạn như certificates
   - Status phụ thuộc vào context (e.g., có audit mới hơn không?)

3. **Manual Override Required:**
   - User có thể manually set status nếu cần
   - Có thể mark as "Expired" nếu có audit mới thay thế
   - Hoặc "Pending" nếu đang review

### 4. SO SÁNH VỚI CERTIFICATES

| Feature | Audit Report | Certificate |
|---------|--------------|-------------|
| **Has Expiry Date?** | ❌ No | ✅ Yes |
| **Auto-calculate Status?** | ❌ No | ✅ Yes |
| **Default Status** | "Valid" | Calculate from expiry_date |
| **Status Logic** | Hardcoded | `calculate_status(expiry_date)` |

**Certificate Status Logic (for reference):**
```python
def calculate_certificate_status(expiry_date, warning_days=60):
    """Calculate certificate status based on expiry date"""
    if not expiry_date:
        return "Unknown"
    
    today = datetime.now(timezone.utc).date()
    days_until_expiry = (expiry_date - today).days
    
    if days_until_expiry < 0:
        return "Expired"
    elif days_until_expiry <= warning_days:
        return "Expiring Soon"
    else:
        return "Valid"
```

**Audit Report does NOT use this logic** because there's no expiry_date.

---

## 🔄 COMPARISON: V1 vs V2

### audit_report_no

| Aspect | Backend V1 | Backend V2 | Status |
|--------|-----------|------------|--------|
| **Extraction Source** | AI (Direct PDF + Summary) | AI (Direct PDF + Summary) | ✅ MATCH |
| **Prompt** | Lines 7335-7337 | audit_report_ai.py | ✅ MATCH |
| **Post-processing** | None | None | ✅ MATCH |
| **Default Value** | Empty string | Empty string | ✅ MATCH |

### status

| Aspect | Backend V1 | Backend V2 | Status |
|--------|-----------|------------|--------|
| **Logic** | Hardcoded "Valid" | Hardcoded "Valid" | ✅ MATCH |
| **Location** | Line 10066 | audit_report_analyze_service.py | ✅ MATCH |
| **Auto-calculation?** | ❌ No | ❌ No | ✅ MATCH |
| **Can User Edit?** | ✅ Yes | ✅ Yes | ✅ MATCH |

**Conclusion:** ✅ **100% Feature Parity** achieved for both fields.

---

## 📝 EXTRACTION EXAMPLES

### Example 1: Simple Audit Report

**Input Document:**
```
ISM CODE AUDIT REPORT

Report No: A/25/1573
Date: 2024-01-15
Ship: MV ATLANTIC HERO
Audited by: DNV GL

Status: Satisfactory
```

**Extracted Fields:**
```json
{
  "audit_report_name": "ISM CODE AUDIT REPORT",
  "audit_report_no": "A/25/1573",
  "audit_date": "2024-01-15",
  "ship_name": "MV ATLANTIC HERO",
  "issued_by": "DNV GL",
  "status": "Valid"
}
```

### Example 2: Complex Reference Number

**Input Document:**
```
INTERNAL SAFETY MANAGEMENT AUDIT

Reference: ISM-INT-2024-001-REV-A
Conducted: March 15, 2024
Vessel: LUCKY STAR
Lead Auditor: John Smith
```

**Extracted Fields:**
```json
{
  "audit_report_name": "INTERNAL SAFETY MANAGEMENT AUDIT",
  "audit_report_no": "ISM-INT-2024-001-REV-A",
  "audit_date": "2024-03-15",
  "ship_name": "LUCKY STAR",
  "auditor_name": "John Smith",
  "status": "Valid"
}
```

### Example 3: Missing Audit Report No.

**Input Document:**
```
ISPS CODE COMPLIANCE AUDIT

Date of Audit: 2024-06-20
Vessel: MINH ANH 09
Conducted by: Vietnam Register

Findings: No major non-conformities
```

**Extracted Fields:**
```json
{
  "audit_report_name": "ISPS CODE COMPLIANCE AUDIT",
  "audit_report_no": "",  # ← Empty (not found in document)
  "audit_date": "2024-06-20",
  "ship_name": "MINH ANH 09",
  "issued_by": "Vietnam Register",
  "status": "Valid"
}
```

---

## 🛠️ IMPLEMENTATION STATUS

### Backend V2

**Files Verified:**

1. ✅ **`/app/backend/app/utils/audit_report_ai.py`**
   - Extraction prompt includes audit_report_no
   - Status not extracted (correct - should be hardcoded)

2. ✅ **`/app/backend/app/services/audit_report_analyze_service.py`**
   - Status hardcoded as "Valid" (line ~50)
   - Matches V1 behavior

3. ✅ **`/app/backend/app/models/audit_report.py`**
   - Model includes both fields
   - status default: "Valid"
   - audit_report_no: Optional[str]

**Implementation Complete:** ✅

---

## 💡 USER WORKFLOW

### Adding Audit Report

```
1. User uploads PDF
   ↓
2. AI analyzes document
   ↓
3. Extracts audit_report_no (if present)
   ↓
4. Sets status = "Valid" (default)
   ↓
5. User reviews form
   ↓
6. User can MANUALLY edit:
   - audit_report_no (if wrong/missing)
   - status (if want to change)
   ↓
7. Submit form
   ↓
8. Record saved with extracted/edited values
```

### Editing Status Later

```
1. User clicks "Edit" on audit report
   ↓
2. Modal opens with current values
   ↓
3. User can change status to:
   - "Valid" (default)
   - "Expired" (if superseded by new audit)
   - "Pending" (if under review)
   - Custom value
   ↓
4. Save changes
```

---

## 🎯 FUTURE ENHANCEMENTS (Optional)

### Possible Status Auto-calculation

If in the future we want to add auto-calculation:

**Option 1: Based on Next Audit Date**
```python
def calculate_audit_status(audit_date, audit_type):
    """Calculate if audit is still current"""
    # ISM/ISPS audits typically annual
    # MLC audits may have different intervals
    
    if audit_type == "ISM":
        validity_period = 365  # days
    elif audit_type == "ISPS":
        validity_period = 365
    elif audit_type == "MLC":
        validity_period = 365
    else:
        return "Valid"  # Unknown type, default to Valid
    
    today = datetime.now(timezone.utc).date()
    days_since_audit = (today - audit_date).days
    
    if days_since_audit > validity_period:
        return "Expired"  # Audit is more than 1 year old
    elif days_since_audit > validity_period - 60:
        return "Due Soon"  # Within 60 days of next audit
    else:
        return "Valid"
```

**Option 2: Based on Next Audit Record**
```python
def calculate_audit_status(current_audit, ship_id, audit_type):
    """Check if there's a newer audit for same ship/type"""
    newer_audits = get_audits_after_date(
        ship_id=ship_id,
        audit_type=audit_type,
        after_date=current_audit.audit_date
    )
    
    if newer_audits:
        return "Superseded"  # Newer audit exists
    else:
        return "Current"
```

**Note:** These are NOT implemented in V1 or V2. Status is always "Valid" by default.

---

## 📚 REFERENCE

**Backend V1:**
- Extraction prompt: lines 7335-7337 (audit_report_no)
- Status hardcoding: line 10066
- Prompt function: lines 7274-7410

**Backend V2:**
- Extraction logic: `/app/backend/app/utils/audit_report_ai.py`
- Analysis service: `/app/backend/app/services/audit_report_analyze_service.py`
- Model: `/app/backend/app/models/audit_report.py`

---

## ✅ CONCLUSION

### audit_report_no
- ✅ Extracted by AI from document
- ✅ No post-processing
- ✅ Can be empty if not found
- ✅ User can manually edit

### status
- ✅ Always defaults to "Valid"
- ✅ No auto-calculation logic
- ✅ User can manually change
- ✅ Same behavior in V1 and V2

**Both fields: 100% Feature Parity achieved** ✅

---

**Last Updated:** December 2024
**Version:** 2.0.0
**Status:** Production Ready ✅

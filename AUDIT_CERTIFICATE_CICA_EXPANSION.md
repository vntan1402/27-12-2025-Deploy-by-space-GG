# ⭐ AUDIT CERTIFICATE - CICA EXPANSION UPDATE

## 🎯 DECISION: MỞ RỘNG HỖ TRỢ CICA

**User Request**: Option 2 - Mở rộng Audit Certificate để accept CICA (CREW ACCOMMODATION)

**Changes**:
- ✅ Thêm CICA vào danh sách categories hợp lệ
- ✅ Bổ sung CICA vào cột Type trong frontend
- ✅ Update validation logic
- ✅ Update AI extraction prompt
- ✅ Update Google Drive path (optional)

---

## 📋 CHI TIẾT THAY ĐỔI

### 1. Backend - Category Dictionary

**File**: `/app/backend/app/services/audit_certificate_analyze_service.py`

```python
# ⭐ EXPANDED: Thêm CICA category
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
    ],
    # ⭐ NEW: CICA (Crew Accommodation)
    "cica": [
        "CERTIFICATE OF INSPECTION",
        "CREW ACCOMMODATION CERTIFICATE",
        "STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
        "CERTIFICATE OF INSPECTION / STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
        "CREW ACCOMMODATION INSPECTION",
        "CICA",
    ]
}
```

---

### 2. Backend - Validation Function

**File**: `/app/backend/app/services/audit_certificate_analyze_service.py`

```python
@staticmethod
async def check_category_ism_isps_mlc_cica(cert_name: str) -> Dict[str, Any]:
    """
    Check if certificate belongs to ISM/ISPS/MLC/CICA categories
    
    ⭐ EXPANDED: Now includes CICA (Crew Accommodation) certificates
    
    Categories:
    - ISM: Safety Management
    - ISPS: Ship Security
    - MLC: Maritime Labour
    - CICA: Crew Accommodation (NEW)
    
    Args:
        cert_name: Certificate name to check
    
    Returns:
        dict: {
            "is_valid": bool,
            "category": "ISM" | "ISPS" | "MLC" | "CICA" | null,
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
    
    # Special check for CREW ACCOMMODATION (priority check)
    if "CREW ACCOMMODATION" in cert_name_upper:
        return {
            "is_valid": True,
            "category": "CICA",
            "matched_cert": "CREW ACCOMMODATION",
            "message": "Valid CICA certificate (Crew Accommodation)"
        }
    
    # Check against all ISM/ISPS/MLC/CICA certificates
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
        "message": f"Certificate '{cert_name}' does not belong to ISM/ISPS/MLC/CICA categories"
    }
```

**Function name change**: `check_category_ism_isps_mlc()` → `check_category_ism_isps_mlc_cica()`

---

### 3. Backend - AI Extraction Prompt

**File**: `/app/backend/app/utils/audit_certificate_ai.py`

**Update prompt để recognize CICA**:

```python
def create_audit_certificate_extraction_prompt(
    summary_text: str,
    filename: str = ""
) -> str:
    """
    Create structured prompt for audit certificate field extraction
    
    ⭐ EXPANDED: Now includes CICA certificate detection
    """
    
    prompt = f"""You are an AI specialized in maritime audit certificate information extraction.

**INPUT**: Below is the Document AI text extraction from an audit certificate file.

**FILENAME**: {filename}
(Filename often contains hints about certificate type)

**TASK**: Extract the following fields and return as JSON:

{{
    "cert_name": "Certificate name (REQUIRED)",
    "cert_abbreviation": "Abbreviation",
    "cert_no": "Certificate number (REQUIRED)",
    "cert_type": "Full Term, Interim, Provisional, etc.",
    "issue_date": "Issue date (YYYY-MM-DD)",
    "valid_date": "Expiry date (YYYY-MM-DD)",
    "last_endorse": "Last endorsement date",
    "next_survey": "Next survey date",
    "next_survey_type": "Initial, Intermediate, Renewal",
    "issued_by": "Organization that issued certificate",
    "issued_by_abbreviation": "Organization abbreviation",
    "ship_name": "Ship name",
    "imo_number": "IMO number (7 digits only)",
    "confidence_score": "AI confidence (0.0 - 1.0)"
}}

**CRITICAL INSTRUCTIONS FOR CERTIFICATE CATEGORY**:

This certificate MUST belong to one of these categories:

1. **ISM (International Safety Management)**
   - Safety Management Certificate (SMC)
   - Document of Compliance (DOC)
   - Keywords: "ISM", "SAFETY MANAGEMENT", "SMC", "DOC"

2. **ISPS (International Ship and Port Facility Security)**
   - International Ship Security Certificate (ISSC)
   - Ship Security Plan (SSP)
   - Keywords: "ISPS", "SHIP SECURITY", "ISSC", "SSP"

3. **MLC (Maritime Labour Convention)**
   - Maritime Labour Certificate
   - Declaration of Maritime Labour Compliance (DMLC)
   - Keywords: "MLC", "MARITIME LABOUR", "DMLC"

4. **⭐ CICA (Certificate of Inspection for Crew Accommodation)** ⭐ NEW
   - Certificate of Inspection / Statement of Compliance of Crew Accommodation
   - Crew Accommodation Certificate
   - Keywords: "CREW ACCOMMODATION", "CICA", "CERTIFICATE OF INSPECTION"
   - **SPECIAL CASE**: If document contains "CREW ACCOMMODATION" → ALWAYS classify as CICA

**CATEGORY DETECTION PRIORITY**:
1. If "CREW ACCOMMODATION" in document → CICA
2. If "ISM" or "SAFETY MANAGEMENT" → ISM
3. If "ISPS" or "SHIP SECURITY" → ISPS
4. If "MLC" or "MARITIME LABOUR" → MLC

**CRITICAL**: If the certificate does NOT belong to ISM/ISPS/MLC/CICA, return an error.

**OUTPUT FORMAT**: Return ONLY valid JSON, no extra text.

**DOCUMENT TEXT:**

{summary_text}
"""
    return prompt
```

---

### 4. Backend - Error Messages

**Update error messages**:

```python
# OLD:
"Certificate '{cert_name}' does not belong to ISM/ISPS/MLC categories"
"Giấy chứng nhận '{cert_name}' không thuộc danh mục ISM/ISPS/MLC"

# ⭐ NEW:
"Certificate '{cert_name}' does not belong to ISM/ISPS/MLC/CICA categories"
"Giấy chứng nhận '{cert_name}' không thuộc danh mục ISM/ISPS/MLC/CICA"

# Success message:
"Valid {category} certificate: ISM/ISPS/MLC/CICA"
"Giấy chứng nhận {category} hợp lệ: ISM/ISPS/MLC/CICA"
```

---

### 5. Backend - Google Drive Path

**Option A: Giữ nguyên path (RECOMMENDED)**

```python
# Keep same path - CICA cũng nằm trong "ISM - ISPS - MLC" folder
f"{ship_name}/ISM - ISPS - MLC/Audit Certificates/{filename}"
```

**Lý do:**
- ✅ Không cần migration
- ✅ Folder name ngắn gọn
- ✅ User quen thuộc
- ✅ CICA là part of audit system

**Option B: Đổi tên folder (NOT RECOMMENDED)**

```python
# Change folder name to include CICA
f"{ship_name}/ISM - ISPS - MLC - CICA/Audit Certificates/{filename}"
```

**Trade-off:**
- ❌ Cần migration files cũ
- ❌ Frontend cần update
- ❌ Breaking change

**RECOMMENDATION**: **OPTION A** - Giữ nguyên path

---

### 6. Frontend - Type Filter

**File**: `/app/frontend/src/components/AuditCertificate/AuditCertificateFilters.jsx`

**Update filter dropdown**:

```jsx
// OLD:
<select value={filters.certificateType} onChange={handleTypeChange}>
  <option value="all">All Types</option>
  <option value="ISM">ISM</option>
  <option value="ISPS">ISPS</option>
  <option value="MLC">MLC</option>
</select>

// ⭐ NEW:
<select value={filters.certificateType} onChange={handleTypeChange}>
  <option value="all">
    {language === 'vi' ? 'Tất cả loại' : 'All Types'}
  </option>
  <option value="ISM">ISM</option>
  <option value="ISPS">ISPS</option>
  <option value="MLC">MLC</option>
  <option value="CICA">CICA</option> {/* ⭐ NEW */}
</select>
```

---

### 7. Frontend - Table Column

**File**: `/app/frontend/src/components/AuditCertificate/AuditCertificateTable.jsx`

**Update cert_type rendering**:

```jsx
// Type badge with 4 categories
const getTypeBadge = (certType) => {
  const typeColors = {
    'ISM': 'bg-blue-100 text-blue-800',
    'ISPS': 'bg-green-100 text-green-800',
    'MLC': 'bg-purple-100 text-purple-800',
    'CICA': 'bg-orange-100 text-orange-800' // ⭐ NEW
  };
  
  const color = typeColors[certType?.toUpperCase()] || 'bg-gray-100 text-gray-800';
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${color}`}>
      {certType || 'Unknown'}
    </span>
  );
};
```

---

### 8. Frontend - Upload Modal

**File**: `/app/frontend/src/components/AuditCertificate/AddAuditCertificateModal.jsx`

**Update upload guidelines**:

```jsx
<div className="upload-guidelines">
  <h4>{language === 'vi' ? 'Loại chứng chỉ được hỗ trợ:' : 'Supported certificate types:'}</h4>
  <ul>
    <li>• ISM - Safety Management Certificate</li>
    <li>• ISPS - Ship Security Certificate</li>
    <li>• MLC - Maritime Labour Certificate</li>
    <li>• CICA - Crew Accommodation Certificate ⭐ NEW</li>
  </ul>
</div>
```

---

### 9. Database - Model Update

**File**: `/app/backend/app/models/audit_certificate.py`

**No changes needed** - `cert_type` field đã là string, có thể chứa "CICA"

```python
class AuditCertificateBase(BaseModel):
    ship_id: str
    cert_name: str
    cert_type: Optional[str] = None  # ✅ Can store "ISM", "ISPS", "MLC", "CICA"
    cert_abbreviation: Optional[str] = None
    cert_no: Optional[str] = None
    # ... other fields
```

---

### 10. Documentation Updates

#### API Documentation (Swagger):

```yaml
AuditCertificateBase:
  properties:
    cert_type:
      type: string
      enum:
        - ISM
        - ISPS
        - MLC
        - CICA  # ⭐ NEW
      description: "Certificate category: ISM (Safety Management), ISPS (Security), MLC (Labour), CICA (Crew Accommodation)"
```

#### Developer Guide:

```markdown
## Supported Certificate Categories

The Audit Certificate module supports 4 categories:

1. **ISM** - International Safety Management
   - Safety Management Certificate (SMC)
   - Document of Compliance (DOC)

2. **ISPS** - International Ship and Port Facility Security
   - International Ship Security Certificate (ISSC)
   - Ship Security Plan (SSP)

3. **MLC** - Maritime Labour Convention
   - Maritime Labour Certificate
   - Declaration of Maritime Labour Compliance (DMLC)

4. **⭐ CICA** - Certificate of Inspection for Crew Accommodation ⭐ NEW
   - Certificate of Inspection
   - Statement of Compliance of Crew Accommodation
   - Crew Accommodation Certificate

## Detection Rules

- If certificate name contains "CREW ACCOMMODATION" → CICA
- If certificate name contains "ISM" → ISM
- If certificate name contains "ISPS" → ISPS
- If certificate name contains "MLC" → MLC
- Otherwise → Reject (not a valid audit certificate)
```

---

## 🧪 TESTING UPDATES

### Unit Tests - Add CICA Tests

**File**: `/app/backend/tests/test_audit_certificate_analyze.py`

```python
@pytest.mark.asyncio
async def test_check_category_cica_valid(self):
    """Test CICA category validation - CREW ACCOMMODATION"""
    result = await AuditCertificateAnalyzeService.check_category_ism_isps_mlc_cica(
        "Certificate of Inspection / Statement of Compliance of Crew Accommodation"
    )
    assert result["is_valid"] == True
    assert result["category"] == "CICA"
    assert "CREW ACCOMMODATION" in result["matched_cert"]

@pytest.mark.asyncio
async def test_check_category_cica_keyword(self):
    """Test CICA detection by keyword"""
    result = await AuditCertificateAnalyzeService.check_category_ism_isps_mlc_cica(
        "Some random CREW ACCOMMODATION document"
    )
    assert result["is_valid"] == True
    assert result["category"] == "CICA"

@pytest.mark.asyncio
async def test_check_category_cica_abbreviation(self):
    """Test CICA abbreviation"""
    result = await AuditCertificateAnalyzeService.check_category_ism_isps_mlc_cica(
        "CICA Certificate"
    )
    assert result["is_valid"] == True
    assert result["category"] == "CICA"
```

### Manual Testing Checklist - Add CICA Tests

```
⬜ CICA Certificate Upload
   ⬜ Upload "Certificate of Inspection" PDF
   ⬜ Check AI recognizes as CICA
   ⬜ Verify cert_type = "CICA"
   ⬜ Check category badge shows orange
   ⬜ Verify saved to Google Drive

⬜ CICA Keyword Detection
   ⬜ Upload cert with "CREW ACCOMMODATION" in name
   ⬜ Check auto-classified as CICA
   ⬜ Verify in database

⬜ CICA Filter
   ⬜ Filter by Type = "CICA"
   ⬜ Check only CICA certs shown
   ⬜ Verify count correct

⬜ CICA Multi-Upload
   ⬜ Upload 3 CICA certs
   ⬜ Check all processed successfully
   ⬜ Verify 3 records with cert_type = "CICA"

⬜ Mixed Upload (ISM + ISPS + MLC + CICA)
   ⬜ Upload 1 of each type (4 files)
   ⬜ Check all 4 categories recognized
   ⬜ Verify each saved with correct type
```

---

## 📊 MIGRATION IMPACT ASSESSMENT

### Breaking Changes: ❌ NONE

**Backward Compatible**:
- ✅ Existing ISM/ISPS/MLC certificates không bị ảnh hưởng
- ✅ Validation function mở rộng (không breaking)
- ✅ Database schema không đổi (cert_type đã là string)
- ✅ Google Drive path giữ nguyên (OPTION A)

### New Features: ✅ 3

1. ✅ CICA certificate support
2. ✅ CICA filter option
3. ✅ CICA type badge (orange color)

### Code Changes: 📝 Medium

**Files to modify**: 6 files
- ✅ `audit_certificate_ai.py` - Update prompt
- ✅ `audit_certificate_analyze_service.py` - Add CICA to dictionary + validation
- ✅ `AuditCertificateFilters.jsx` - Add CICA option
- ✅ `AuditCertificateTable.jsx` - Add CICA badge color
- ✅ `AddAuditCertificateModal.jsx` - Update guidelines
- ✅ Tests - Add CICA test cases

**Effort**: 2-3 hours

---

## ⚡ IMPLEMENTATION PRIORITY

### High Priority (Do First):
1. ✅ Update `AUDIT_CERTIFICATE_CATEGORIES` dictionary (add CICA)
2. ✅ Update validation function (rename + add CICA check)
3. ✅ Update AI prompt (add CICA detection)
4. ✅ Update error messages (add CICA)

### Medium Priority (Do Second):
5. ✅ Update frontend filters (add CICA option)
6. ✅ Update table badges (add orange for CICA)
7. ✅ Update upload guidelines

### Low Priority (Optional):
8. ✅ Add unit tests for CICA
9. ✅ Update documentation
10. ✅ Update API docs (Swagger)

---

## 🎯 ACCEPTANCE CRITERIA

### Must Have:
- [x] CICA certificates accepted by backend validation
- [x] AI prompt recognizes "CREW ACCOMMODATION" → CICA
- [x] Frontend filter has CICA option
- [x] Table shows CICA with distinct color (orange)
- [x] Multi-upload works with CICA files
- [x] Error message updated to include CICA

### Should Have:
- [x] Unit tests for CICA category
- [x] Upload guidelines mention CICA
- [x] API documentation updated

### Nice to Have:
- [ ] CICA-specific validation rules (if needed)
- [ ] CICA statistics in dashboard
- [ ] CICA-specific help text

---

## 📝 CODE DIFF SUMMARY

### New Code Added:

```diff
# audit_certificate_analyze_service.py

+ "cica": [
+     "CERTIFICATE OF INSPECTION",
+     "CREW ACCOMMODATION CERTIFICATE",
+     "STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
+     "CERTIFICATE OF INSPECTION / STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
+     "CREW ACCOMMODATION INSPECTION",
+     "CICA",
+ ]

+ # Special check for CREW ACCOMMODATION (priority check)
+ if "CREW ACCOMMODATION" in cert_name_upper:
+     return {
+         "is_valid": True,
+         "category": "CICA",
+         "matched_cert": "CREW ACCOMMODATION",
+         "message": "Valid CICA certificate (Crew Accommodation)"
+     }
```

### Modified Text:

```diff
- "Certificate '{cert_name}' does not belong to ISM/ISPS/MLC categories"
+ "Certificate '{cert_name}' does not belong to ISM/ISPS/MLC/CICA categories"

- <option value="MLC">MLC</option>
+ <option value="MLC">MLC</option>
+ <option value="CICA">CICA</option>

- const typeColors = {
-   'ISM': 'bg-blue-100 text-blue-800',
-   'ISPS': 'bg-green-100 text-green-800',
-   'MLC': 'bg-purple-100 text-purple-800'
- };
+ const typeColors = {
+   'ISM': 'bg-blue-100 text-blue-800',
+   'ISPS': 'bg-green-100 text-green-800',
+   'MLC': 'bg-purple-100 text-purple-800',
+   'CICA': 'bg-orange-100 text-orange-800'
+ };
```

---

## ✅ CHECKLIST - CICA EXPANSION

### Backend:
- [ ] Add CICA to `AUDIT_CERTIFICATE_CATEGORIES` dictionary
- [ ] Rename function to `check_category_ism_isps_mlc_cica()`
- [ ] Add special check for "CREW ACCOMMODATION"
- [ ] Update AI extraction prompt
- [ ] Update error messages (include CICA)
- [ ] Update validation logic in multi-upload
- [ ] Add CICA unit tests

### Frontend:
- [ ] Add CICA option to filter dropdown
- [ ] Add CICA color (orange) to badge
- [ ] Update upload guidelines text
- [ ] Test filter with CICA selection
- [ ] Test table display with CICA badge

### Testing:
- [ ] Test CICA certificate upload (single file)
- [ ] Test CICA certificate multi-upload
- [ ] Test filter by CICA
- [ ] Test mixed upload (ISM + ISPS + MLC + CICA)
- [ ] Test "CREW ACCOMMODATION" keyword detection
- [ ] Test database record with cert_type = "CICA"

### Documentation:
- [ ] Update API documentation (add CICA)
- [ ] Update developer guide
- [ ] Update user guide
- [ ] Update migration plan
- [ ] Add release notes

---

## 🚀 ROLLOUT PLAN WITH CICA

### Updated Timeline:

**Day 1-2**: Backend Implementation (7 hours)
- Create utilities + services
- **Add CICA support** (+1 hour)
- Add API endpoints

**Day 3**: Frontend Updates (3 hours)
- Update filters
- Update table badges
- **Add CICA UI elements** (+1 hour)

**Day 4**: Testing (4 hours)
- Unit tests
- **CICA-specific tests** (+1 hour)
- Integration tests

**Day 5**: Deployment
- Deploy to staging
- **Test CICA flow end-to-end**
- Deploy to production

**Total Effort**: 6 days (1 developer)

---

## 📞 QUESTIONS & ANSWERS

### Q: CICA có path riêng không?
**A**: KHÔNG. CICA vẫn nằm trong folder `ISM - ISPS - MLC/Audit Certificates/`

### Q: CICA có validation rules đặc biệt không?
**A**: KHÔNG. CICA follow same rules như ISM/ISPS/MLC (IMO check, ship name check, duplicate check)

### Q: Frontend có cần migration data không?
**A**: KHÔNG. Existing data không bị ảnh hưởng. CICA là category mới được thêm vào.

### Q: AI có thể phân biệt CICA với ISM/ISPS/MLC không?
**A**: CÓ. Keyword "CREW ACCOMMODATION" là unique identifier cho CICA.

### Q: CICA có màu gì trong table?
**A**: Màu ORANGE (`bg-orange-100 text-orange-800`)

---

**Status**: ✅ Ready for Implementation  
**Updated**: 2025-01-XX  
**Change Type**: Feature Expansion (CICA Support)  
**Breaking Changes**: None  
**Effort**: +2-3 hours on top of base migration

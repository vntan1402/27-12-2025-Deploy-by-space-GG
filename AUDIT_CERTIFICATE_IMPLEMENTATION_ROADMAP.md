# 🚀 AUDIT CERTIFICATE MIGRATION - IMPLEMENTATION ROADMAP

## 📊 INVESTIGATION SUMMARY

### Backend V1 Endpoints (Already Working):
```
✅ GET    /audit-certificates
✅ GET    /audit-certificates/upcoming-surveys
✅ GET    /audit-certificates/{cert_id}
✅ POST   /audit-certificates
✅ PUT    /audit-certificates/{cert_id}
✅ DELETE /audit-certificates/{cert_id}
✅ POST   /audit-certificates/bulk-delete
✅ POST   /audit-certificates/bulk-update
✅ POST   /audit-certificates/{cert_id}/upload-file
✅ GET    /audit-certificates/{cert_id}/file-link
✅ POST   /audit-certificates/analyze-file          ← NEED TO MIGRATE
✅ POST   /audit-certificates/create-with-file-override  ← NEED TO MIGRATE
✅ POST   /audit-certificates/multi-upload          ← NEED TO MIGRATE
✅ POST   /audit-certificates/{cert_id}/auto-rename-file
✅ POST   /audit-certificates/{cert_id}/calculate-next-survey
✅ POST   /ships/{ship_id}/audit-certificates/update-next-survey
```

### Backend V2 Status (Current):
```
✅ GET    /audit-certificates                       ← DONE
✅ GET    /audit-certificates/{cert_id}            ← DONE
✅ POST   /audit-certificates                      ← DONE
✅ PUT    /audit-certificates/{cert_id}            ← DONE
✅ DELETE /audit-certificates/{cert_id}            ← DONE (with BackgroundTasks)
✅ POST   /audit-certificates/bulk-delete          ← DONE (with BackgroundTasks)
✅ POST   /audit-certificates/check-duplicate      ← DONE
❌ POST   /audit-certificates/analyze              ← TODO (placeholder exists)
❌ POST   /audit-certificates/analyze-file         ← MISSING (frontend calls this!)
❌ POST   /audit-certificates/multi-upload         ← MISSING
❌ POST   /audit-certificates/create-with-file-override ← MISSING
```

### Key Findings:

1. **Frontend calls `/analyze-file`** but Backend V2 only has `/analyze` (mismatch!)
2. **Bulk delete** already implemented with BackgroundTasks ✅
3. **Background delete** pattern already in place (from certificates.py) ✅
4. Need to implement 3 endpoints: `analyze-file`, `multi-upload`, `create-with-file-override`

---

## 🎯 IMPLEMENTATION STEPS

### STEP 1: Create AI Utilities (2 hours)
**File**: `/app/backend/app/utils/audit_certificate_ai.py`

**Tasks**:
- [ ] Create `AUDIT_CERTIFICATE_CATEGORIES` dict (ISM/ISPS/MLC/CICA)
- [ ] Implement `extract_audit_certificate_fields_from_summary()`
- [ ] Implement `create_audit_certificate_extraction_prompt()` (with CICA)
- [ ] Implement `_post_process_extracted_data()`
- [ ] Implement `normalize_issued_by()` helper
- [ ] Implement `validate_certificate_type()` helper

**Reference**: 
- `/app/backend/app/utils/audit_report_ai.py` (pattern)
- `/app/backend-v1/server.py` lines 16143-16400 (analyze_document_with_ai)

---

### STEP 2: Create Analysis Service (3 hours)
**File**: `/app/backend/app/services/audit_certificate_analyze_service.py`

**Tasks**:
- [ ] Create `AuditCertificateAnalyzeService` class
- [ ] Implement `analyze_file()` - Main analysis method
- [ ] Implement `_process_small_file()` - Files ≤15 pages
- [ ] Implement `_process_large_file()` - Files >15 pages with splitting
- [ ] Implement `validate_ship_info()` - IMO & ship name validation
- [ ] Implement `check_extraction_quality()` - Quality assessment
- [ ] Implement `check_category_ism_isps_mlc_cica()` - Category validation (with CICA)

**Reference**:
- `/app/backend/app/services/audit_report_analyze_service.py` (main pattern)
- `/app/backend-v1/server.py` lines 27053-27305 (validation logic)

---

### STEP 3: Update API Endpoints (2 hours)
**File**: `/app/backend/app/api/v1/audit_certificates.py`

**Tasks**:
- [ ] **FIX**: Rename `/analyze` → `/analyze-file` (match frontend!)
- [ ] Implement `POST /analyze-file` endpoint (complete implementation)
- [ ] Add `POST /multi-upload` endpoint
- [ ] Add `POST /create-with-file-override` endpoint
- [ ] Import `AuditCertificateAnalyzeService`
- [ ] Handle FormData properly (file_content, filename, content_type, ship_id)

**Reference**:
- `/app/backend/app/api/v1/audit_reports.py` (analyze-file pattern)
- `/app/backend-v1/server.py` lines 26961-27462 (multi-upload logic)

---

### STEP 4: Update GDrive Service - Path Fix (30 min)
**File**: `/app/backend/app/services/gdrive_service.py`

**Tasks**:
- [ ] Find all occurrences of `ISM-ISPS-MLC`
- [ ] Replace with `ISM - ISPS - MLC` (add spaces)
- [ ] Test path creation

**Path Change**:
```python
# OLD:
f"{ship_name}/ISM-ISPS-MLC/Audit Certificates/{filename}"

# NEW:
f"{ship_name}/ISM - ISPS - MLC/Audit Certificates/{filename}"
```

---

### STEP 5: Update Audit Certificate Service (1 hour)
**File**: `/app/backend/app/services/audit_certificate_service.py`

**Tasks**:
- [ ] Enhance `check_duplicate()` method (return more details)
- [ ] Verify bulk_delete implementation (already has BackgroundTasks)
- [ ] Add any missing helper methods

**Reference**:
- Current implementation (already good)
- Backend V1 duplicate check logic

---

### STEP 6: Frontend - Add CICA Support (1 hour)
**Files**: 
- `/app/frontend/src/components/AuditCertificate/AuditCertificateFilters.jsx`
- `/app/frontend/src/components/AuditCertificate/AuditCertificateTable.jsx`
- `/app/frontend/src/components/AuditCertificate/AddAuditCertificateModal.jsx`

**Tasks**:
- [ ] **Filters**: Add CICA option to type dropdown
- [ ] **Table**: Add orange badge for CICA type
- [ ] **Modal**: Update upload guidelines (mention CICA)
- [ ] Verify `analyzeFile()` calls correct endpoint `/analyze-file`

**Frontend Service Check**:
```javascript
// auditCertificateService.js line 140
// ✅ Already calls '/api/audit-certificates/analyze-file' (correct!)
return api.post('/api/audit-certificates/analyze-file', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
  timeout: 90000,
});
```

---

### STEP 7: Testing (3 hours)

**Backend Tests**:
- [ ] Unit test: Category validation (ISM/ISPS/MLC/CICA)
- [ ] Unit test: CREW ACCOMMODATION → CICA detection
- [ ] Unit test: Extraction quality check
- [ ] Unit test: Ship validation (IMO/name)
- [ ] Integration test: analyze-file endpoint
- [ ] Integration test: multi-upload endpoint

**Manual Tests**:
- [ ] Upload single CICA PDF → Check analysis
- [ ] Upload 4 files (ISM+ISPS+MLC+CICA) → Check all processed
- [ ] Filter by CICA type → Check results
- [ ] Test IMO mismatch → Check rejection
- [ ] Test duplicate detection → Check modal

---

## 📝 DETAILED IMPLEMENTATION PLAN

### PHASE 1: Backend Core (Day 1-2)

#### Step 1.1: Create audit_certificate_ai.py
```bash
cd /app/backend/app/utils
# Create new file with AI extraction logic
# Port from audit_report_ai.py + Backend V1
```

**Key Functions**:
1. `extract_audit_certificate_fields_from_summary()` - Main extraction
2. `create_audit_certificate_extraction_prompt()` - AI prompt with CICA
3. `_post_process_extracted_data()` - Normalize & validate
4. Helper functions for cert_type, issued_by normalization

**CICA Detection Priority**:
```python
# Special check first
if "CREW ACCOMMODATION" in cert_name_upper:
    return {"category": "CICA", ...}

# Then check dictionary
for category, cert_list in AUDIT_CERTIFICATE_CATEGORIES.items():
    ...
```

#### Step 1.2: Create audit_certificate_analyze_service.py
```bash
cd /app/backend/app/services
# Create analysis service class
# Follow audit_report_analyze_service.py pattern
```

**Key Methods**:
1. `analyze_file()` - Main entry point (handles small & large files)
2. `validate_ship_info()` - IMO (hard reject) / Ship name (soft warning)
3. `check_extraction_quality()` - Critical fields check
4. `check_category_ism_isps_mlc_cica()` - Category validation

#### Step 1.3: Update audit_certificates.py API
```bash
cd /app/backend/app/api/v1
# Update existing file
# Add 3 new endpoints
```

**Endpoint 1: analyze-file**
```python
@router.post("/analyze-file")
async def analyze_audit_certificate_file(
    file_content: str = Form(...),
    filename: str = Form(...),
    content_type: str = Form(...),
    ship_id: str = Form(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Analyze single audit certificate file with AI"""
    # Call AuditCertificateAnalyzeService.analyze_file()
    # Return extracted_info + warnings
```

**Endpoint 2: multi-upload**
```python
@router.post("/multi-upload")
async def multi_upload_audit_certificates(
    ship_id: str = Query(...),
    files: List[UploadFile] = File(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Batch upload with auto-create"""
    # For each file:
    #   1. Analyze
    #   2. Quality check
    #   3. Category check (CICA included)
    #   4. Validate ship
    #   5. Check duplicate
    #   6. Upload to GDrive
    #   7. Create DB record
    # Return batch results
```

**Endpoint 3: create-with-file-override**
```python
@router.post("/create-with-file-override")
async def create_audit_certificate_with_file_override(
    ship_id: str = Query(...),
    file: UploadFile = File(...),
    cert_data: str = Form(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Create with file, bypass validation"""
    # Parse cert_data JSON
    # Upload to GDrive
    # Create DB record
```

---

### PHASE 2: Frontend Updates (Day 3)

#### Step 2.1: Update Filters
**File**: `AuditCertificateFilters.jsx`

```jsx
// Add CICA option
<option value="CICA">CICA - Crew Accommodation</option>
```

#### Step 2.2: Update Table Badges
**File**: `AuditCertificateTable.jsx`

```jsx
const typeColors = {
  'ISM': 'bg-blue-100 text-blue-800',
  'ISPS': 'bg-green-100 text-green-800',
  'MLC': 'bg-purple-100 text-purple-800',
  'CICA': 'bg-orange-100 text-orange-800'  // ⭐ NEW
};
```

#### Step 2.3: Update Upload Modal
**File**: `AddAuditCertificateModal.jsx`

```jsx
// Update guidelines
<ul>
  <li>• ISM - Safety Management Certificate</li>
  <li>• ISPS - Ship Security Certificate</li>
  <li>• MLC - Maritime Labour Certificate</li>
  <li>• CICA - Crew Accommodation Certificate ⭐ NEW</li>
</ul>
```

---

### PHASE 3: Testing (Day 4)

#### Unit Tests
**File**: `/app/backend/tests/test_audit_certificate_analyze.py`

```python
# Test CICA detection
def test_check_category_cica():
    result = check_category_ism_isps_mlc_cica("CREW ACCOMMODATION CERTIFICATE")
    assert result["category"] == "CICA"

# Test extraction quality
def test_check_extraction_quality_sufficient():
    extracted = {"cert_name": "ISM", "cert_no": "123", ...}
    result = check_extraction_quality(extracted)
    assert result["sufficient"] == True

# Test ship validation
def test_validate_ship_imo_mismatch():
    result = validate_ship_info("1234567", "Ship A", current_ship)
    assert result["error"] is not None  # Hard reject
```

#### Integration Tests
- Test analyze-file with real PDF
- Test multi-upload with 4 files
- Test CICA detection flow

#### Manual Tests
- Upload CICA certificate
- Filter by CICA type
- Test mixed upload (4 types)
- Test validation warnings

---

## 🔍 VERIFICATION CHECKLIST

### Before Each Step:
- [ ] ✅ Check Backend V1 implementation (reference)
- [ ] ✅ Check Frontend service calls (endpoint names)
- [ ] ✅ Check existing V2 patterns (certificates.py)
- [ ] ✅ Verify no breaking changes

### After Each Step:
- [ ] ✅ Run linter (Python/JavaScript)
- [ ] ✅ Test endpoint manually (curl/Postman)
- [ ] ✅ Check logs for errors
- [ ] ✅ Verify frontend still works

---

## 🚨 CRITICAL NOTES

### 1. Endpoint Name Mismatch - FIX REQUIRED!
**Issue**: Frontend calls `/analyze-file` but Backend V2 has `/analyze`

**Solution**: 
```python
# WRONG (current):
@router.post("/analyze")

# CORRECT (fix to):
@router.post("/analyze-file")
```

### 2. CICA Priority Detection
Always check "CREW ACCOMMODATION" keyword FIRST before dictionary lookup:

```python
# Priority check
if "CREW ACCOMMODATION" in cert_name_upper:
    return {"category": "CICA"}

# Then check dictionary
for category, cert_list in AUDIT_CERTIFICATE_CATEGORIES.items():
    ...
```

### 3. Google Drive Path
Spaces are important! Test path creation:
```python
# Correct:
"ISM - ISPS - MLC"  # with spaces

# Wrong:
"ISM-ISPS-MLC"  # no spaces
```

### 4. BackgroundTasks Already Implemented
No need to add BackgroundTasks for delete - already done! ✅

---

## 📊 PROGRESS TRACKING

### Day 1: Backend Utilities & Services
- [ ] audit_certificate_ai.py (2h)
- [ ] audit_certificate_analyze_service.py (3h)
- [ ] Test basic functions (1h)

### Day 2: API Endpoints
- [ ] Fix /analyze → /analyze-file
- [ ] Implement analyze-file endpoint (1h)
- [ ] Implement multi-upload endpoint (2h)
- [ ] Implement create-with-file-override (1h)
- [ ] Update gdrive_service path (30min)

### Day 3: Frontend & Integration
- [ ] Add CICA to filters (30min)
- [ ] Add CICA badge (30min)
- [ ] Update upload guidelines (30min)
- [ ] Integration testing (2h)

### Day 4: Testing & Deployment
- [ ] Unit tests (2h)
- [ ] Manual testing (2h)
- [ ] Bug fixes (variable)
- [ ] Deploy to staging

---

## ✅ READY TO START

**Next Action**: Begin with **STEP 1** - Create `audit_certificate_ai.py`

**Command**: Ready for implementation! 🚀

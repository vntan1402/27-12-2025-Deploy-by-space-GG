# 🚀 PLAN: UPGRADE SHIP CERTIFICATE AI PIPELINE

## 🎯 MỤC TIÊU

Áp dụng **Advanced AI Pipeline** từ Audit Certificate sang Ship Certificate để:
- ✅ Support scanned PDFs (OCR)
- ✅ Generate AI summaries
- ✅ Store summary files trên Google Drive
- ✅ Improve extraction quality với Document AI
- ✅ Consistent pipeline across modules

---

## 📊 CURRENT STATE vs TARGET STATE

### **Current State (Ship Certificate):**
```
PDF Upload
  ↓
PyPDF2.extract_text() [NO OCR]
  ↓
System AI (Gemini) extracts fields
  ↓
Upload PDF to GDrive
  ↓
Create certificate record
  ↓
❌ Scanned PDFs FAIL
❌ NO summary generation
❌ NO summary storage
```

### **Target State (như Audit Certificate):**
```
PDF Upload
  ↓
Google Document AI [WITH OCR]
  ↓
Extract full text (summary_text)
  ↓
System AI (Gemini) extracts fields
  ↓
Upload PDF to GDrive
  ↓
Upload Summary TXT to GDrive ⭐ NEW
  ↓
Create certificate record with summary_file_id ⭐ NEW
  ↓
✅ Scanned PDFs WORK
✅ Summary generation
✅ Summary storage
```

---

## 📋 DETAILED PLAN

---

### **PHASE 1: PREPARATION & ANALYSIS** ⏱️ 1-2 hours

#### Task 1.1: Code Review & Dependency Analysis
**Goal:** Hiểu rõ current implementation và identify reusable components

**Actions:**
- [ ] Review `CertificateMultiUploadService` (Ship Certificate service)
- [ ] Review `AuditCertificateAnalyzeService` (Audit Certificate service)
- [ ] Identify reusable utilities:
  - `document_ai_helper.py` ✅ (already generic)
  - `pdf_splitter.py` ✅ (already generic)
  - `audit_certificate_ai.py` ⚠️ (need to adapt prompt)
- [ ] Map data model differences

**Deliverables:**
- Comparison matrix của 2 services
- List of reusable vs custom components

---

#### Task 1.2: Database Schema Updates
**Goal:** Thêm summary fields vào Ship Certificate model

**Current Schema:**
```python
# /app/backend/app/models/certificate.py
class CertificateBase(BaseModel):
    ship_id: str
    cert_name: str
    cert_no: str
    ...
    file_id: str
    # ❌ MISSING: summary_file_id
    # ❌ MISSING: extracted_ship_name
```

**Target Schema:**
```python
class CertificateBase(BaseModel):
    ship_id: str
    cert_name: str
    cert_no: str
    ...
    file_id: str
    summary_file_id: Optional[str] = None  # ⭐ NEW
    extracted_ship_name: Optional[str] = None  # ⭐ NEW
```

**Actions:**
- [ ] Update `CertificateBase` model
- [ ] Update `CertificateResponse` model
- [ ] Update `CertificateCreate` model
- [ ] Add migration script (if needed for existing records)

**Files to modify:**
- `/app/backend/app/models/certificate.py`

**Deliverables:**
- Updated Pydantic models
- Migration plan for existing data

---

### **PHASE 2: BACKEND IMPLEMENTATION** ⏱️ 4-6 hours

---

#### Task 2.1: Create Ship Certificate AI Extraction Utility
**Goal:** Tạo prompt và extraction logic riêng cho Ship Certificates

**Actions:**
- [ ] Create new file: `/app/backend/app/utils/ship_certificate_ai.py`
- [ ] Define SHIP_CERTIFICATE_CATEGORIES
  ```python
  SHIP_CERTIFICATE_CATEGORIES = {
      "class": ["Class Certificate", "Classification Certificate"],
      "safety": ["Safety Certificate", "SOLAS", "Safety Equipment"],
      "load_line": ["Load Line Certificate", "LLC"],
      "tonnage": ["Tonnage Certificate"],
      "registry": ["Certificate of Registry"],
      # ... more categories
  }
  ```
- [ ] Create `extract_ship_certificate_fields_from_summary()` function
  - Based on `extract_audit_certificate_fields_from_summary()`
  - Customize prompt for Ship Certificate types
  - Same field extraction logic
- [ ] Create `create_ship_certificate_extraction_prompt()` function
  - Similar to audit prompt but for Ship Certificates
  - Include Ship Certificate specific validation

**Files to create:**
- `/app/backend/app/utils/ship_certificate_ai.py` (new)

**Reference:**
- `/app/backend/app/utils/audit_certificate_ai.py` (template)

**Deliverables:**
- Ship Certificate AI extraction utility
- Unit tests for extraction logic

---

#### Task 2.2: Create Ship Certificate Analysis Service
**Goal:** Service layer để handle Document AI + AI extraction

**Actions:**
- [ ] Create new file: `/app/backend/app/services/ship_certificate_analyze_service.py`
- [ ] Implement `analyze_file()` method:
  - Accept base64 file content
  - Validate file (size, type, magic bytes)
  - Check page count, split if needed
  - Call Document AI (via `document_ai_helper`)
  - Extract fields with System AI
  - Validate ship info (IMO/name)
  - Check duplicates
  - Return analysis result + summary_text
- [ ] Implement `_process_small_file()` (≤15 pages)
- [ ] Implement `_process_large_file()` (>15 pages, with splitting)
- [ ] Implement validation methods:
  - `validate_ship_info()`
  - `check_duplicate()`
  - `check_category()` (optional, less strict than Audit)

**Files to create:**
- `/app/backend/app/services/ship_certificate_analyze_service.py` (new)

**Reference:**
- `/app/backend/app/services/audit_certificate_analyze_service.py` (template)

**Deliverables:**
- Complete analysis service
- Unit tests for service methods

---

#### Task 2.3: Update Multi-Upload Service
**Goal:** Integrate Document AI pipeline vào existing multi-upload

**Current:**
```python
# /app/backend/app/services/certificate_multi_upload_service.py:391
text, is_scanned = PDFProcessor.extract_text_from_pdf(file_content)
```

**Target:**
```python
# Call new analysis service
from app.services.ship_certificate_analyze_service import ShipCertificateAnalyzeService

analysis_result = await ShipCertificateAnalyzeService.analyze_file(
    file_content=base64.b64encode(file_content).decode('utf-8'),
    filename=file.filename,
    content_type=file.content_type,
    ship_id=ship_id,
    current_user=current_user
)

summary_text = analysis_result.get("summary_text")  # ⭐ NEW
extracted_info = analysis_result.get("extracted_info")
```

**Actions:**
- [ ] Update `_analyze_document_with_ai()` method
  - Replace PyPDF2 extraction with Document AI
  - Use new `ShipCertificateAnalyzeService`
- [ ] Update `_process_single_file()` method
  - Add summary_text handling
  - Upload summary file to GDrive
  - Store summary_file_id in DB

**Files to modify:**
- `/app/backend/app/services/certificate_multi_upload_service.py`

**Key changes:**
```python
# OLD (line ~391)
if content_type == "application/pdf":
    text, is_scanned = PDFProcessor.extract_text_from_pdf(file_content)
    if not text or len(text.strip()) < 50:
        return {"category": "unknown", "confidence": 0.0}

# NEW
if content_type == "application/pdf":
    # Use Document AI pipeline
    analysis_result = await ShipCertificateAnalyzeService.analyze_file(
        file_content=base64.b64encode(file_content).decode('utf-8'),
        filename=filename,
        content_type=content_type,
        ship_id=ship_id,
        current_user=current_user
    )
    
    if not analysis_result.get("success"):
        return {
            "status": "error",
            "message": analysis_result.get("message", "Analysis failed")
        }
    
    summary_text = analysis_result.get("summary_text")  # ⭐
    extracted_info = analysis_result.get("extracted_info")
```

**Deliverables:**
- Updated multi-upload service
- Integration tests

---

#### Task 2.4: Implement Summary Upload Logic
**Goal:** Upload summary files lên Google Drive

**Actions:**
- [ ] Add summary upload trong `_process_single_file()`:
  ```python
  # After successful main file upload
  summary_file_id = None
  summary_text = analysis_result.get("summary_text")
  
  if summary_text and summary_text.strip():
      # Create summary filename
      base_name = file.filename.rsplit('.', 1)[0]
      summary_filename = f"{base_name}_Summary.txt"
      
      # Convert to bytes
      summary_bytes = summary_text.encode('utf-8')
      
      # Upload to GDrive
      summary_upload_result = await _upload_to_google_drive(
          file_content=summary_bytes,
          filename=summary_filename,
          content_type="text/plain",
          ship=ship,
          gdrive_config_doc=gdrive_config_doc,
          folder_name="certificates"  # Class & Flag/Certificates
      )
      
      if summary_upload_result.get("success"):
          summary_file_id = summary_upload_result.get("file_id")
  ```

- [ ] Update certificate creation to include `summary_file_id`:
  ```python
  cert_data = {
      "id": str(uuid.uuid4()),
      "ship_id": ship_id,
      ...
      "file_id": uploaded_file_id,
      "summary_file_id": summary_file_id,  # ⭐ NEW
      "extracted_ship_name": extracted_ship_name,  # ⭐ NEW
      ...
  }
  ```

**Files to modify:**
- `/app/backend/app/services/certificate_multi_upload_service.py`

**Deliverables:**
- Summary upload logic
- Integration tests

---

#### Task 2.5: Implement Summary Lifecycle Management
**Goal:** Auto delete/rename summary khi certificate thay đổi

**Actions:**
- [ ] Update DELETE endpoint (`/api/certificates/{cert_id}`):
  ```python
  # In certificate_service.py or certificates.py
  
  async def delete_certificate(cert_id: str):
      cert = await db.certificates.find_one({"id": cert_id})
      
      # Delete main file
      if cert.get("file_id"):
          await GDriveService.delete_file(cert["file_id"])
      
      # ⭐ NEW: Delete summary file
      if cert.get("summary_file_id"):
          await GDriveService.delete_file(cert["summary_file_id"])
      
      # Delete DB record
      await db.certificates.delete_one({"id": cert_id})
  ```

- [ ] Update AUTO-RENAME endpoint (`/api/certificates/{cert_id}/auto-rename-file`):
  ```python
  async def auto_rename_certificate_file(cert_id: str):
      cert = await db.certificates.find_one({"id": cert_id})
      
      # Rename main file
      new_filename = generate_new_filename(cert)
      await rename_file_on_gdrive(cert["file_id"], new_filename)
      
      # ⭐ NEW: Rename summary file
      if cert.get("summary_file_id"):
          summary_filename = f"{new_filename.rsplit('.', 1)[0]}_Summary.txt"
          await rename_file_on_gdrive(cert["summary_file_id"], summary_filename)
  ```

**Files to modify:**
- `/app/backend/app/services/certificate_service.py`
- `/app/backend/app/api/v1/certificates.py` (if delete/rename logic is here)

**Deliverables:**
- Summary lifecycle management
- Integration tests for delete/rename

---

### **PHASE 3: FRONTEND UPDATES** ⏱️ 2-3 hours

---

#### Task 3.1: Update Frontend Data Models
**Goal:** Add summary fields to TypeScript/JavaScript types

**Actions:**
- [ ] Update certificate type definitions (if using TypeScript)
- [ ] Add `summary_file_id` field
- [ ] Add `extracted_ship_name` field

**Files to check:**
- `/app/frontend/src/types/` (if exists)
- `/app/frontend/src/services/api.js` or similar

**Deliverables:**
- Updated type definitions

---

#### Task 3.2: Add Summary Preview UI (Optional but Recommended)
**Goal:** Display summary trong UI cho quick reference

**Options:**

**Option A: Tooltip Hover (Simple)**
```jsx
// In CertificateTable.jsx
<Tooltip content={certificate.summary_preview}>
  <span>📄 {certificate.cert_name}</span>
</Tooltip>
```

**Option B: Expandable Row (Better UX)**
```jsx
// Add expand button to table row
<button onClick={() => fetchSummary(cert.summary_file_id)}>
  View Summary
</button>

// Show summary in expanded section
{expanded && (
  <div className="summary-section">
    <pre>{summaryText}</pre>
  </div>
)}
```

**Option C: Summary Modal (Full-featured)**
```jsx
// Similar to NotesModal
<SummaryModal
  show={showSummary}
  certificate={selectedCert}
  onClose={() => setShowSummary(false)}
/>
```

**Recommendation:** Start with **Option A** (Tooltip), implement **Option B** later.

**Actions:**
- [ ] Decide on UI approach
- [ ] Implement summary preview component
- [ ] Add API call to fetch summary from GDrive (if needed)
- [ ] Update table component to show summary icon/button

**Files to modify:**
- `/app/frontend/src/components/CertificateTable.jsx` (or similar)
- Create `/app/frontend/src/components/ShipCertificates/SummaryModal.jsx` (if Option C)

**Deliverables:**
- Summary preview UI
- UX documentation

---

#### Task 3.3: Update Batch Results Modal
**Goal:** Show summary status trong multi-upload results

**Actions:**
- [ ] Update `BatchResultsModal.jsx` to show:
  - ✅ Certificate created
  - ✅ File uploaded
  - ✅ Summary generated ⭐ NEW
  ```jsx
  <div className="result-item">
    <CheckIcon /> Certificate created
    <CheckIcon /> File uploaded
    {result.summary_file_id ? (
      <CheckIcon /> Summary generated
    ) : (
      <InfoIcon /> No summary (manual entry)
    )}
  </div>
  ```

**Files to modify:**
- `/app/frontend/src/components/ShipCertificates/BatchResultsModal.jsx`

**Deliverables:**
- Updated batch results UI

---

### **PHASE 4: TESTING & VALIDATION** ⏱️ 3-4 hours

---

#### Task 4.1: Unit Tests

**Backend:**
- [ ] Test `ship_certificate_ai.py`:
  - Extraction logic
  - Prompt generation
  - Field validation
- [ ] Test `ship_certificate_analyze_service.py`:
  - Small file processing
  - Large file processing (splitting)
  - Error handling
- [ ] Test summary upload logic
- [ ] Test summary lifecycle (delete/rename)

**Frontend:**
- [ ] Test summary preview component
- [ ] Test batch results display

**Files to create:**
- `/app/backend/tests/test_ship_certificate_ai.py`
- `/app/backend/tests/test_ship_certificate_analyze_service.py`
- `/app/backend/tests/test_certificate_summary_lifecycle.py`

**Deliverables:**
- Unit test suite
- Test coverage report

---

#### Task 4.2: Integration Tests

**Test Scenarios:**

**Scenario 1: Normal PDF (with text layer)**
- [ ] Upload Class Certificate PDF
- [ ] Verify Document AI extracts text
- [ ] Verify System AI extracts fields
- [ ] Verify main file uploaded to GDrive
- [ ] Verify summary file uploaded to GDrive
- [ ] Verify DB record created with both file IDs

**Scenario 2: Scanned PDF (no text layer)**
- [ ] Upload scanned certificate
- [ ] Verify Document AI OCR works
- [ ] Verify System AI extracts fields from OCR text
- [ ] Verify both files uploaded
- [ ] Verify DB record created

**Scenario 3: Multi-file Upload (Mixed)**
- [ ] Upload 5 certificates (3 normal, 2 scanned)
- [ ] Verify all processed correctly
- [ ] Verify batch results accurate

**Scenario 4: Large PDF (>15 pages)**
- [ ] Upload 20-page certificate
- [ ] Verify PDF splitting works
- [ ] Verify chunk processing parallel
- [ ] Verify merged summary correct

**Scenario 5: Delete Certificate**
- [ ] Create certificate with summary
- [ ] Delete certificate
- [ ] Verify main file deleted from GDrive
- [ ] Verify summary file deleted from GDrive
- [ ] Verify DB record deleted

**Scenario 6: Rename Certificate**
- [ ] Create certificate with summary
- [ ] Auto-rename certificate
- [ ] Verify main file renamed on GDrive
- [ ] Verify summary file renamed on GDrive

**Deliverables:**
- Integration test suite
- Test report with screenshots

---

#### Task 4.3: Manual QA Testing

**Test Checklist:**
- [ ] Upload various certificate types:
  - Class Certificate
  - Load Line Certificate
  - Safety Certificate
  - SOLAS Certificate
  - Tonnage Certificate
- [ ] Test with different file qualities:
  - High quality scans
  - Low quality scans
  - Mixed text/image PDFs
- [ ] Test error scenarios:
  - Invalid file types
  - Corrupted PDFs
  - Very large files (>50MB)
  - Document AI timeout
- [ ] Test UI/UX:
  - Summary preview
  - Batch results
  - Error messages
- [ ] Test performance:
  - Processing time per file
  - Batch upload (10+ files)

**Deliverables:**
- QA test report
- Bug list (if any)

---

### **PHASE 5: DOCUMENTATION & DEPLOYMENT** ⏱️ 1-2 hours

---

#### Task 5.1: Update Documentation

**Documents to create/update:**
- [ ] `/app/SHIP_CERTIFICATE_AI_PIPELINE.md` (new)
  - Architecture overview
  - Component diagram
  - API documentation
  - Configuration guide
- [ ] `/app/ADD_SHIP_CERTIFICATE_FLOW.md` (update)
  - Update flow diagram
  - Add Document AI step
  - Add summary generation step
- [ ] `/app/COMPARISON_SHIP_VS_AUDIT_CERTIFICATES.md` (update)
  - Update comparison table (now both are equal)
- [ ] `README.md` or developer guide (update)
  - Mention new AI pipeline
  - Configuration requirements

**Deliverables:**
- Updated documentation

---

#### Task 5.2: Configuration & Environment Setup

**Requirements:**
- [ ] Verify Google Document AI enabled
- [ ] Verify Apps Script deployed
- [ ] Verify System AI configured
- [ ] Verify Emergent LLM key available
- [ ] Update environment variables (if needed)

**Configuration checklist:**
```bash
# In System Settings
✓ Document AI enabled
✓ Document AI project_id configured
✓ Document AI processor_id configured
✓ Apps Script URL configured
✓ System AI model: gemini-2.0-flash-exp
✓ EMERGENT_LLM_KEY available
```

**Deliverables:**
- Configuration verification checklist

---

#### Task 5.3: Deployment

**Deployment Steps:**
1. [ ] Create feature branch: `feature/ship-cert-advanced-ai-pipeline`
2. [ ] Commit all changes
3. [ ] Create pull request
4. [ ] Code review
5. [ ] Merge to main
6. [ ] Deploy to staging environment
7. [ ] Run integration tests on staging
8. [ ] Deploy to production
9. [ ] Monitor logs and metrics
10. [ ] Announce feature to users

**Rollback Plan:**
- Keep old code path as fallback
- Add feature flag: `USE_DOCUMENT_AI_FOR_SHIP_CERTS`
- Can disable if issues found

**Deliverables:**
- Deployed feature
- Deployment checklist

---

## 📊 EFFORT ESTIMATION

| Phase | Tasks | Estimated Time | Complexity |
|-------|-------|----------------|------------|
| **Phase 1: Preparation** | 2 tasks | 1-2 hours | 🟢 Low |
| **Phase 2: Backend** | 5 tasks | 4-6 hours | 🟡 Medium |
| **Phase 3: Frontend** | 3 tasks | 2-3 hours | 🟢 Low |
| **Phase 4: Testing** | 3 tasks | 3-4 hours | 🟡 Medium |
| **Phase 5: Documentation** | 3 tasks | 1-2 hours | 🟢 Low |
| **TOTAL** | 16 tasks | **11-17 hours** | **🟡 Medium** |

**Recommended Timeline:** 2-3 working days (with testing)

---

## 🎯 PRIORITIES & DEPENDENCIES

### **Must-Have (P0):**
1. ✅ Document AI integration (OCR support)
2. ✅ Summary generation
3. ✅ Summary storage on GDrive
4. ✅ Summary lifecycle (delete)
5. ✅ Database schema updates
6. ✅ Basic testing

### **Should-Have (P1):**
1. ✅ Summary lifecycle (rename)
2. ✅ Summary preview UI
3. ✅ Comprehensive integration tests
4. ✅ Documentation

### **Nice-to-Have (P2):**
1. ⚪ Advanced summary preview modal
2. ⚪ Summary search functionality
3. ⚪ Performance optimizations
4. ⚪ Analytics/metrics

---

## ⚠️ RISKS & MITIGATION

### Risk 1: Document AI Cost
**Risk:** Document AI có cost (~$0.002/page)  
**Impact:** HIGH - Cost increase cho multi-file uploads  
**Mitigation:**
- Monitor usage và cost
- Set quotas/limits nếu cần
- Inform user về pricing

### Risk 2: Processing Time
**Risk:** Document AI chậm hơn PyPDF2 (15s vs 2s)  
**Impact:** MEDIUM - User experience  
**Mitigation:**
- Implement progress indicators
- Background processing option
- Optimize với parallel processing

### Risk 3: Document AI Availability
**Risk:** Google API có thể down hoặc timeout  
**Impact:** HIGH - Upload failures  
**Mitigation:**
- Implement retry logic
- Add fallback to PyPDF2 (for normal PDFs)
- Clear error messages cho users

### Risk 4: Storage Increase
**Risk:** Summary files increase storage usage  
**Impact:** LOW - Text files nhỏ (~5-10KB)  
**Mitigation:**
- Monitor storage usage
- Implement cleanup cho old summaries

### Risk 5: Breaking Changes
**Risk:** Changes có thể break existing functionality  
**Impact:** HIGH - Production issues  
**Mitigation:**
- Comprehensive testing
- Feature flag for gradual rollout
- Rollback plan ready

---

## ✅ SUCCESS CRITERIA

### **Technical:**
- [ ] All scanned PDFs được process thành công
- [ ] Summary files được tạo và lưu trữ
- [ ] Summary lifecycle hoạt động (delete/rename)
- [ ] No regression trong existing functionality
- [ ] Test coverage ≥80%
- [ ] Performance acceptable (<30s per file)

### **User Experience:**
- [ ] Users có thể upload scanned certificates
- [ ] Users có thể xem summary preview
- [ ] Batch upload UI clear và informative
- [ ] Error messages helpful

### **Quality:**
- [ ] AI extraction accuracy ≥90%
- [ ] OCR text quality good (readable)
- [ ] No data loss
- [ ] Logs và monitoring đầy đủ

---

## 📝 POST-IMPLEMENTATION

### **Monitoring:**
- [ ] Track Document AI API usage
- [ ] Monitor processing times
- [ ] Track extraction accuracy
- [ ] Monitor error rates
- [ ] Track storage usage

### **Optimization Opportunities:**
- [ ] Cache Document AI results
- [ ] Optimize prompt for better extraction
- [ ] Implement summary search
- [ ] Add summary analytics

### **Future Enhancements:**
- [ ] Multi-language support
- [ ] Custom extraction rules per certificate type
- [ ] AI-powered certificate validation
- [ ] Automated certificate renewal alerts

---

## 🔗 REFERENCE DOCUMENTS

1. `/app/AUDIT_CERTIFICATE_SUMMARY_GENERATION.md` - Template reference
2. `/app/COMPARISON_SHIP_VS_AUDIT_CERTIFICATES.md` - Current state analysis
3. `/app/PDF_SCANNED_HANDLING_ANALYSIS.md` - OCR problem analysis
4. `/app/ADD_SHIP_CERTIFICATE_FLOW.md` - Current flow documentation

---

## 🎬 NEXT STEPS

### **Immediate Actions:**
1. **Review và approve plan** với stakeholders
2. **Create feature branch** từ main
3. **Start Phase 1** - Preparation & Analysis
4. **Daily progress updates** trong team

### **Communication:**
- Daily standup updates
- Weekly progress report
- Demo after Phase 3
- User announcement after deployment

---

**Plan created:** 2024-11-27  
**Estimated completion:** 2-3 working days  
**Priority:** HIGH (improves user experience significantly)  
**Status:** READY FOR REVIEW & APPROVAL

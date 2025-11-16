# 📋 Backend V1 → V2 Migration Checklist

## 🎯 Current Status Summary

### ✅ Already Migrated in Backend V2
1. ✅ GET /survey-reports
2. ✅ GET /survey-reports/{id}
3. ✅ POST /survey-reports (create)
4. ✅ PUT /survey-reports/{id} (update)
5. ✅ DELETE /survey-reports/{id} (single delete)
6. ✅ POST /survey-reports/bulk-delete
7. ✅ POST /survey-reports/check-duplicate
8. ✅ GET /certificates/upcoming-surveys
9. ✅ POST /ships/{ship_id}/calculate-special-survey-cycle
10. ✅ POST /certificates/{cert_id}/auto-rename-file

### ⚠️ Partially Migrated (Stub/Incomplete)
1. ⚠️ POST /survey-reports/analyze-file
   - **Status:** Stub exists, returns TODO message
   - **V1 Location:** server.py lines 8594-9270
   - **Complexity:** HIGH (676 lines of logic)
   - **Dependencies:**
     - PDFSplitter utility
     - TargetedOCR processor
     - DualAppsScriptManager
     - Document AI integration
     - System AI field extraction
     - Ship validation with fuzzy matching

### ❌ Not Yet Migrated (Critical Missing)
1. ❌ POST /survey-reports/{report_id}/upload-files
   - **Status:** Does not exist in V2
   - **V1 Location:** server.py lines 9334-9465
   - **Purpose:** Upload original PDF + summary text to GDrive
   - **Process:**
     - Decode base64 file content
     - Upload original to: `ShipName/Class & Flag Cert/Class Survey Report/`
     - Upload summary to: `SUMMARY/Class & Flag Document/`
     - Update DB with file IDs

2. ❌ GET /ships/{ship_id}/survey-status
   - **Status:** Does not exist in V2
   - **V1 Location:** server.py line 9468
   - **Purpose:** Get ship survey status records

3. ❌ POST /ships/{ship_id}/survey-status
   - **Status:** Does not exist in V2
   - **V1 Location:** server.py line 13970
   - **Purpose:** Create/update ship survey status

4. ❌ POST /ships/{ship_id}/update-next-survey
   - **Status:** Does not exist in V2
   - **V1 Location:** server.py line 19986
   - **Purpose:** Batch update next survey dates for ship certificates

---

## 🔧 Required Utilities/Helpers (Not in V2)

### 1. PDFSplitter
- **File:** backend-v1/pdf_splitter.py
- **Purpose:** Split large PDFs (>15 pages) into chunks for Document AI
- **Key Methods:**
  - `get_page_count(pdf_content)` - Count pages in PDF
  - `needs_splitting(pdf_content)` - Check if PDF needs splitting
  - `split_pdf(pdf_content, filename)` - Split into 12-page chunks
  - `create_enhanced_merged_summary()` - Merge chunk summaries

### 2. TargetedOCR
- **File:** backend-v1/targeted_ocr.py
- **Purpose:** Extract header/footer text from PDF (first page only)
- **Key Methods:**
  - `get_ocr_processor()` - Get OCR processor instance
  - `extract_from_pdf(pdf_content, page_num)` - Extract header/footer
- **Dependencies:** Tesseract OCR, pdf2image, Pillow

### 3. DualAppsScriptManager
- **File:** backend-v1/dual_apps_script_manager.py
- **Purpose:** Manage Document AI and GDrive operations
- **Key Methods:**
  - `analyze_survey_report_only()` - Document AI analysis
  - `upload_survey_report_file()` - Upload original PDF
  - `upload_survey_report_summary()` - Upload summary text

### 4. Survey Report AI Extraction
- **Function:** `extract_survey_report_fields_from_summary()`
- **Location:** backend-v1/server.py lines 7520-7640
- **Purpose:** Extract structured fields from Document AI summary
- **Uses:** System AI (Gemini/OpenAI)

### 5. Fuzzy String Matching
- **Function:** `calculate_similarity()`
- **Purpose:** Ship name validation (60% threshold)
- **Library:** python-Levenshtein or difflib

---

## 📊 Migration Priority

### 🔥 Priority 1: Critical for Survey Report Feature
1. **POST /survey-reports/analyze-file** (FULL implementation)
   - Reason: Core feature - AI analysis with OCR
   - Impact: Without this, users can't auto-populate survey report data
   - Estimate: 2-3 hours (complex logic)

2. **POST /survey-reports/{id}/upload-files**
   - Reason: Files won't be uploaded to GDrive
   - Impact: Survey reports exist in DB but no files accessible
   - Estimate: 1 hour

3. **PDFSplitter utility**
   - Reason: Large PDFs (>15 pages) will fail
   - Impact: Many survey reports are 20-40 pages
   - Estimate: 30 mins (copy from V1)

4. **TargetedOCR processor**
   - Reason: Report Form & Report No extraction accuracy
   - Impact: Critical fields might be missed
   - Estimate: 45 mins (copy + test Tesseract)

### 🟡 Priority 2: Important but Not Blocking
5. **DualAppsScriptManager integration**
   - Reason: Cleaner code structure
   - Impact: Can use direct Apps Script calls as workaround
   - Estimate: 1 hour

6. **Ship survey status endpoints**
   - Reason: Additional feature, not core
   - Impact: Survey status tracking won't work
   - Estimate: 1 hour

### 🟢 Priority 3: Nice to Have
7. **Batch update next survey**
   - Reason: Convenience feature
   - Impact: Users can still update individually
   - Estimate: 30 mins

---

## 🧪 Testing Requirements

### After Migration, Test:
1. ✅ Small PDF analysis (≤15 pages)
2. ✅ Large PDF analysis (>15 pages, test splitting)
3. ✅ OCR enhancement (test header/footer extraction)
4. ✅ Ship validation (correct ship vs wrong ship)
5. ✅ Bypass validation flow
6. ✅ File upload to GDrive (original + summary)
7. ✅ Duplicate check
8. ✅ Full end-to-end flow (upload → analyze → save → files uploaded)

---

## 📝 Implementation Notes

### analyze-file Endpoint Key Points:
1. Support FormData input (UploadFile + ship_id + bypass_validation)
2. Validate PDF file (magic bytes check)
3. Detect page count and decide split strategy
4. Run Document AI on chunks if needed
5. Perform Targeted OCR on first page
6. Merge summaries if split
7. Extract fields with System AI
8. Validate ship name/IMO with fuzzy matching
9. Return analysis data + base64 file content for later upload
10. Include metadata (_split_info, _ocr_info)

### upload-files Endpoint Key Points:
1. Accept base64 file content
2. Decode and upload to 2 locations:
   - Original: `ShipName/Class & Flag Cert/Class Survey Report/`
   - Summary: `SUMMARY/Class & Flag Document/`
3. Update survey_report record with file IDs
4. Handle errors gracefully (summary upload is non-critical)

---

## 🚀 Migration Plan

### Phase 1: Core Migration (4-5 hours)
1. Copy PDFSplitter utility → /app/backend/app/utils/pdf_splitter.py
2. Copy TargetedOCR → /app/backend/app/utils/targeted_ocr.py
3. Implement analyze-file endpoint logic
4. Implement upload-files endpoint
5. Add extract_survey_report_fields_from_summary() helper

### Phase 2: Testing & Refinement (2-3 hours)
1. Test with sample PDFs (small, large, scanned)
2. Verify OCR accuracy
3. Test ship validation flows
4. Test GDrive uploads
5. Fix any issues

### Phase 3: Additional Features (2 hours)
1. Ship survey status endpoints
2. Batch update next survey
3. Additional utilities if needed

**Total Estimate: 8-10 hours**

---

## ⚠️ Critical Dependencies to Check

Before migration, ensure backend V2 has:
- ✅ Google Document AI config in database
- ✅ Apps Script URL configured
- ✅ GDrive config working
- ✅ System AI config (Gemini/OpenAI)
- ❓ Tesseract OCR installed (for TargetedOCR)
- ❓ pdf2image library installed
- ❓ PyPDF2/pypdf library installed

---

## 📌 Decision Required

**Question for User:**
Should I proceed with migration starting from Priority 1 items?

**Recommended Approach:**
1. Start with analyze-file (most complex)
2. Then upload-files (completes the flow)
3. Test thoroughly
4. Add remaining features based on user needs

**Alternative:**
- Focus only on what user actively uses
- Skip features that are rarely used

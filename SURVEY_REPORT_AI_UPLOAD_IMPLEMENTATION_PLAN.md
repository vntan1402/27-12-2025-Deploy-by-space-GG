# Implementation Plan: Add Survey Report From File (AI Analysis)

## Mục tiêu
Xây dựng tính năng upload Survey Report file và tự động trích xuất thông tin bằng AI, tương tự như quy trình Add Crew Certificate.

---

## So sánh với Crew Certificate Workflow

| **Khía cạnh** | **Crew Certificate** | **Survey Report** |
|--------------|---------------------|-------------------|
| File size limit | 10MB | 20MB |
| Required selection | Crew member | Ship (already selected) |
| AI extraction fields | cert_name, cert_no, issued_by, issued_date, expiry_date, holder_name, rank | survey_report_name, survey_report_no, issued_by, issued_date, note, ship_name, ship_imo, surveyor_name |
| Name validation | holder_name vs crew_name | ship_name/ship_imo vs selected ship |
| Apps Script action | analyze_crew_certificate | analyze_maritime_document_ai |
| Apps Script document type | crew_certificate | Other Maritime Documents (general_maritime) |
| Original file folder | ShipName/Crew Records/CrewName_Passport/Certificates/CertName/ | ShipName/Class & Flag Cert/Class Survey Report/ |
| Summary file folder | (same as original) | SUMMARY/Class & Flag Document/ |
| MongoDB collection | crew_certificates | survey_reports |
| Batch processing | Yes (multiple files) | Yes (multiple files) |
| Single file mode | Review before submit | Review before submit |

---

## Chi tiết Implementation - Từng bước

### **BƯỚC 1: Frontend State Management**

#### 1.1. Thêm States mới vào App.js

**Location:** `/app/frontend/src/App.js` (sau Survey Report states hiện tại ~Line 1406)

**States cần thêm:**
```javascript
// Survey Report File Upload States
const [surveyReportFile, setSurveyReportFile] = useState(null);
const [isAnalyzingSurveyReport, setIsAnalyzingSurveyReport] = useState(false);
const [surveyReportError, setSurveyReportError] = useState('');
const [surveyReportFileInputRef] = useState(useRef(null));

// Batch processing states
const [isBatchProcessingSurveyReports, setIsBatchProcessingSurveyReports] = useState(false);
const [currentSurveyReportFileIndex, setCurrentSurveyReportFileIndex] = useState(0);
const [surveyReportBatchResults, setSurveyReportBatchResults] = useState([]);
const [surveyReportBatchProgress, setSurveyReportBatchProgress] = useState({ current: 0, total: 0 });

// Processing results modal
const [showSurveyReportProcessingResultsModal, setShowSurveyReportProcessingResultsModal] = useState(false);
const [surveyReportProcessingResults, setSurveyReportProcessingResults] = useState([]);
```

**Ước tính:** ~15 states mới

---

### **BƯỚC 2: Frontend Upload Handler Functions**

**Location:** `/app/frontend/src/App.js` (sau Survey Report functions hiện tại ~Line 4450)

#### 2.1. File Upload Handler
```javascript
const handleMultipleSurveyReportUpload = (files) => {
  // Validate files (format, size <= 20MB)
  // If single file: call handleSurveyReportFileUpload()
  // If multiple files: call startSurveyReportBatchProcessing()
}
```
**Lines:** ~50 lines
**Logic:**
- Validate file type (PDF, JPG, PNG)
- Validate file size (<= 20MB)
- Filter valid files
- Branch: single vs multiple files

#### 2.2. Single File Handler (Review Mode)
```javascript
const handleSurveyReportFileUpload = async (file) => {
  // Call analyze API
  // Populate newSurveyReport state with extracted data
  // Keep modal open for review
  // Handle validation warnings (ship name mismatch)
}
```
**Lines:** ~100 lines
**API Call:**
```javascript
POST ${API}/survey-reports/analyze-file
FormData:
- survey_report_file: File
- ship_id: string
```

#### 2.3. Batch Processing Orchestrator
```javascript
const startSurveyReportBatchProcessing = async (files) => {
  // Initialize batch states
  // Create promises with staggered delays (2s)
  // Process all files in parallel
  // Collect results
  // Show results modal
  // Refresh survey reports list
}
```
**Lines:** ~80 lines
**Features:**
- Parallel processing
- Staggered start (2s delay between files)
- Progress tracking
- Results collection

#### 2.4. Single File Processor (Batch Mode)
```javascript
const processSingleSurveyReportInBatch = async (file, current, total) => {
  // 1. Analyze file
  // 2. Check duplicate (optional)
  // 3. Create survey report record
  // 4. Upload files to Drive
  // 5. Update record with file IDs
  // Return result object
}
```
**Lines:** ~200 lines
**Steps:**
1. Call analyze API
2. Check duplicate (by ship_id + survey_report_no)
3. Create survey report via POST /api/survey-reports
4. Upload files via POST /api/survey-reports/{id}/upload-files
5. Return success/error result

#### 2.5. Helper Functions
```javascript
const handleSurveyReportFileAreaClick = () => { /* Trigger file input */ }
const handleSurveyReportFileDrop = (e) => { /* Handle drag & drop */ }
const handleResetSurveyReportFile = () => { /* Clear file */ }
```
**Lines:** ~30 lines total

**Total Frontend Functions:** ~460 lines of code

---

### **BƯỚC 3: Frontend UI Components**

**Location:** `/app/frontend/src/App.js` (trong Add Survey Report Modal ~Line 11255)

#### 3.1. Section: From Survey Report File (AI Analysis)
```jsx
{/* Section 1: From Survey Report File (AI Analysis) */}
<div className="mb-6">
  <h4 className="font-semibold">
    📄 {language === 'vi' ? 'Từ file báo cáo survey (AI phân tích)' : 'From Survey Report File (AI Analysis)'}
  </h4>
  <p className="text-sm text-gray-600">
    {language === 'vi' 
      ? 'Tải lên file báo cáo survey để tự động điền thông tin hoặc nhập thủ công bên dưới'
      : 'Upload survey report file to automatically fill information or enter manually below'}
  </p>
  
  {/* Drag & Drop Area */}
  {!surveyReportFile ? (
    <div className="border-2 border-dashed" onClick={handleSurveyReportFileAreaClick}>
      {/* Upload UI */}
    </div>
  ) : (
    <div className="bg-green-50">
      {/* File analyzed success UI */}
    </div>
  )}
  
  {/* Hidden file input */}
  <input ref={surveyReportFileInputRef} type="file" accept=".pdf,.jpg,.jpeg,.png" multiple />
  
  {/* Loading indicator */}
  {isAnalyzingSurveyReport && (
    <div className="animate-spin">Analyzing...</div>
  )}
  
  {/* Error display */}
  {surveyReportError && (
    <div className="bg-red-50">{surveyReportError}</div>
  )}
</div>
```
**Lines:** ~100 lines

#### 3.2. Batch Processing Progress Modal
```jsx
{isBatchProcessingSurveyReports && (
  <div className="fixed inset-0 z-[80]">
    <div className="bg-white rounded-xl">
      <h3>Processing {surveyReportBatchProgress.current}/{surveyReportBatchProgress.total} files...</h3>
      {/* Progress bar */}
      {/* Current file indicator */}
    </div>
  </div>
)}
```
**Lines:** ~80 lines

#### 3.3. Processing Results Modal
```jsx
{showSurveyReportProcessingResultsModal && (
  <div className="fixed inset-0 z-[80]">
    <div className="bg-white rounded-xl">
      <h3>Survey Report Processing Results</h3>
      {/* Results table */}
      <table>
        {surveyReportProcessingResults.map(result => (
          <tr>
            <td>{result.filename}</td>
            <td>{result.success ? '✅ Success' : '❌ Failed'}</td>
            <td>{result.surveyReportName}</td>
          </tr>
        ))}
      </table>
    </div>
  </div>
)}
```
**Lines:** ~150 lines

**Total Frontend UI:** ~330 lines of JSX

---

### **BƯỚC 4: Backend - Analyze Endpoint**

**Location:** `/app/backend/server.py` (sau Survey Report endpoints ~Line 5020)

#### 4.1. Main Endpoint
```python
@api_router.post("/survey-reports/analyze-file")
async def analyze_survey_report_file(
    survey_report_file: UploadFile = File(...),
    ship_id: str = Form(...),
    current_user: UserResponse = Depends(check_permission([...]))
):
    """
    Analyze survey report file using Google Document AI
    1. Extract text with Document AI
    2. Extract fields with System AI
    3. Validate ship name/IMO
    4. Return analysis data + file content (base64)
    """
```
**Lines:** ~300 lines

**Logic flow:**
1. Read file content
2. Get company & ship info
3. Get AI configuration (Document AI + System AI)
4. Call DualAppsScriptManager.analyze_maritime_document_only()
5. Extract fields from AI summary
6. Validate ship name/IMO
7. Return analysis + base64 encoded file

#### 4.2. Field Extraction Function
```python
async def extract_survey_report_fields_from_summary(
    summary_text: str,
    ai_provider: str,
    ai_model: str,
    use_emergent_key: bool
) -> Dict[str, Any]:
    """
    Use System AI to extract structured fields from Document AI summary
    Returns:
    {
        "survey_report_name": str,
        "survey_report_no": str,
        "issued_by": str,
        "issued_date": str (ISO format),
        "note": str,
        "ship_name": str,
        "ship_imo": str,
        "surveyor_name": str
    }
    """
```
**Lines:** ~150 lines

**AI Prompt structure:**
```
You are analyzing a maritime survey report. Extract the following fields:
- Survey Report Name: [Annual Survey, Special Survey, etc.]
- Survey Report No.: [Report number]
- Issued By: [Classification society name]
- Issued Date: [Date in ISO format]
- Ship Name: [Vessel name]
- Ship IMO: [IMO number]
- Surveyor Name: [Name of surveyor]
- Note: [Any important notes or findings]

Raw text:
{summary_text}

Return ONLY a JSON object with these fields.
```

#### 4.3. Ship Validation Function
```python
def validate_ship_match(
    extracted_ship_name: str,
    extracted_ship_imo: str,
    actual_ship_name: str,
    actual_ship_imo: str
) -> Dict[str, Any]:
    """
    Validate if extracted ship info matches selected ship
    Returns:
    {
        "ship_name_match": bool,
        "ship_imo_match": bool,
        "overall_match": bool
    }
    """
```
**Lines:** ~50 lines

**Matching logic:**
- Normalize ship names (uppercase, remove spaces)
- Check IMO exact match
- Return validation result

**Total Backend Analyze:** ~500 lines

---

### **BƯỚC 5: Backend - Upload Files Endpoint**

**Location:** `/app/backend/server.py` (sau analyze endpoint)

#### 5.1. Upload Endpoint
```python
@api_router.post("/survey-reports/{report_id}/upload-files")
async def upload_survey_report_files(
    report_id: str,
    file_content: str = Body(...),  # base64
    filename: str = Body(...),
    content_type: str = Body(...),
    summary_text: str = Body(...),
    current_user: UserResponse = Depends(check_permission([...]))
):
    """
    Upload survey report files to Google Drive after record creation
    1. Decode base64 file content
    2. Upload original file to: ShipName/Class & Flag Cert/Class Survey Report/
    3. Upload summary to: SUMMARY/Class & Flag Document/
    4. Update survey report record with file IDs
    """
```
**Lines:** ~200 lines

**Steps:**
1. Validate report exists
2. Get ship & company info
3. Decode base64 file content
4. Upload original via DualAppsScriptManager
5. Upload summary via DualAppsScriptManager
6. Update MongoDB record with file IDs
7. Return file IDs

**Total Backend Upload:** ~200 lines

---

### **BƯỚC 6: Dual Apps Script Manager Extension**

**Location:** `/app/backend/dual_apps_script_manager.py`

#### 6.1. Analyze Survey Report (No Upload)
```python
async def analyze_survey_report_only(
    self,
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: dict
) -> Dict[str, Any]:
    """
    Analyze survey report using Document AI without uploading
    Calls Apps Script action: analyze_maritime_document_ai
    Document type: Other Maritime Documents
    """
```
**Lines:** ~100 lines

**Apps Script call:**
```python
payload = {
    "action": "analyze_maritime_document_ai",
    "document": "Other Maritime Documents",
    "file_content": base64_file,
    "filename": filename,
    "content_type": content_type,
    "project_id": document_ai_config["project_id"],
    "processor_id": document_ai_config["processor_id"]
}
```

#### 6.2. Upload Survey Report File
```python
async def upload_survey_report_file(
    self,
    file_content: bytes,
    filename: str,
    content_type: str,
    ship_name: str,
    survey_report_name: str
) -> Dict[str, Any]:
    """
    Upload survey report to Google Drive
    Path: ShipName/Class & Flag Cert/Class Survey Report/
    Returns: {
        "survey_report_file_id": str,
        "file_path": str
    }
    """
```
**Lines:** ~80 lines

**Apps Script call:**
```python
payload = {
    "action": "upload_survey_report",
    "document": "Class Survey Report",
    "file_content": base64_file,
    "filename": filename,
    "content_type": content_type,
    "ship_name": ship_name,
    "survey_report_name": survey_report_name,
    "folder_path": f"{ship_name}/Class & Flag Cert/Class Survey Report"
}
```

#### 6.3. Upload Survey Report Summary
```python
async def upload_survey_report_summary(
    self,
    summary_text: str,
    filename: str,
    ship_name: str
) -> Dict[str, Any]:
    """
    Upload AI summary to SUMMARY folder
    Path: SUMMARY/Class & Flag Document/
    Returns: {
        "summary_file_id": str,
        "file_path": str
    }
    """
```
**Lines:** ~70 lines

**Total Dual Manager:** ~250 lines

---

### **BƯỚC 7: Apps Script Updates** (nếu cần)

**Location:** Google Apps Script project

#### 7.1. Check existing actions
- ✅ `analyze_maritime_document_ai` - Already exists
- ❓ `upload_survey_report` - Need to check/create
- ❓ Upload to SUMMARY folder - Need to check/create

**If new actions needed:**
```javascript
// Action: upload_survey_report
function uploadSurveyReport(params) {
  const {file_content, filename, ship_name, folder_path} = params;
  
  // Find or create folder: ShipName/Class & Flag Cert/Class Survey Report
  const folder = getOrCreateFolder(folder_path);
  
  // Upload file
  const file = folder.createFile(
    Utilities.newBlob(
      Utilities.base64Decode(file_content),
      params.content_type,
      filename
    )
  );
  
  return {
    success: true,
    survey_report_file_id: file.getId()
  };
}
```
**Lines:** ~50 lines per action

---

### **BƯỚC 8: Check Duplicate Endpoint** (Optional)

**Location:** `/app/backend/server.py`

```python
@api_router.post("/survey-reports/check-duplicate")
async def check_duplicate_survey_report(
    ship_id: str = Body(...),
    survey_report_no: str = Body(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Check if survey report already exists
    Returns: {
        "is_duplicate": bool,
        "existing_report": {...} (if duplicate)
    }
    """
    existing = await mongo_db.find_one("survey_reports", {
        "ship_id": ship_id,
        "survey_report_no": survey_report_no
    })
    
    return {
        "is_duplicate": existing is not None,
        "existing_report": existing
    }
```
**Lines:** ~40 lines

---

## Tổng kết Implementation

### **Frontend Changes**
| Component | Lines of Code | Complexity |
|-----------|--------------|------------|
| State Management | 15 states | Low |
| Upload Handlers | ~460 lines | Medium |
| UI Components | ~330 lines | Medium |
| **Total Frontend** | **~790 lines** | **Medium** |

### **Backend Changes**
| Component | Lines of Code | Complexity |
|-----------|--------------|------------|
| Analyze Endpoint | ~300 lines | High |
| Field Extraction | ~150 lines | High |
| Ship Validation | ~50 lines | Low |
| Upload Endpoint | ~200 lines | Medium |
| Check Duplicate | ~40 lines | Low |
| **Total Backend** | **~740 lines** | **High** |

### **Dual Apps Script Manager**
| Component | Lines of Code | Complexity |
|-----------|--------------|------------|
| Analyze Only | ~100 lines | Medium |
| Upload Report | ~80 lines | Medium |
| Upload Summary | ~70 lines | Medium |
| **Total Manager** | **~250 lines** | **Medium** |

### **Apps Script** (if needed)
| Component | Lines of Code | Complexity |
|-----------|--------------|------------|
| Upload Actions | ~100 lines | Low |

---

## **TỔNG CỘNG: ~1,880 lines of code**

---

## Độ phức tạp & Rủi ro

### **Phức tạp cao (High Complexity):**
1. **AI Field Extraction**: Prompt engineering cho survey report fields
2. **Ship Validation**: Logic matching ship name/IMO
3. **Error Handling**: Nhiều điểm có thể fail (AI, upload, validation)

### **Phức tạp trung bình (Medium Complexity):**
1. **Batch Processing**: Parallel với staggered delay
2. **File Upload Logic**: Hai folder khác nhau (original + summary)
3. **State Management**: Nhiều states tương tác

### **Rủi ro:**
1. **Apps Script Actions**: Có thể cần tạo mới hoặc modify
2. **Google Drive Permissions**: Folder structure có thể chưa tồn tại
3. **AI Accuracy**: Survey report format đa dạng, có thể extract sai
4. **File Size**: 20MB có thể gây timeout

---

## Thứ tự Implementation (Khuyến nghị)

### **Phase 1: Backend Foundation** (2-3 hours)
1. ✅ Create analyze endpoint
2. ✅ Create field extraction function
3. ✅ Create ship validation function
4. ✅ Test with sample survey report files

### **Phase 2: Dual Apps Script Manager** (1-2 hours)
1. ✅ Add analyze_survey_report_only()
2. ✅ Add upload_survey_report_file()
3. ✅ Add upload_survey_report_summary()
4. ✅ Test Apps Script integration

### **Phase 3: Frontend Single File** (2-3 hours)
1. ✅ Add states
2. ✅ Add UI section in modal
3. ✅ Add single file upload handler
4. ✅ Test review mode

### **Phase 4: Frontend Batch Processing** (2-3 hours)
1. ✅ Add batch processing functions
2. ✅ Add progress modal
3. ✅ Add results modal
4. ✅ Test multiple files

### **Phase 5: Backend Upload** (1-2 hours)
1. ✅ Create upload endpoint
2. ✅ Update record with file IDs
3. ✅ Test complete flow

### **Phase 6: Testing & Refinement** (2-3 hours)
1. ✅ Test với nhiều loại survey report
2. ✅ Test error cases
3. ✅ Test batch processing
4. ✅ Refine AI prompts

### **Total Estimated Time: 10-16 hours**

---

## Checklist Implementation

### **Pre-Implementation**
- [ ] Review existing Apps Script actions
- [ ] Check Google Drive folder structure
- [ ] Test Document AI với survey report samples
- [ ] Prepare test files (PDF, JPG, PNG)

### **Backend**
- [ ] Create analyze endpoint
- [ ] Implement field extraction
- [ ] Implement ship validation
- [ ] Create upload endpoint
- [ ] Add check duplicate endpoint
- [ ] Test all endpoints với Postman/curl

### **Dual Apps Script Manager**
- [ ] Add analyze_survey_report_only()
- [ ] Add upload_survey_report_file()
- [ ] Add upload_survey_report_summary()
- [ ] Test Apps Script calls

### **Frontend**
- [ ] Add state management
- [ ] Create upload handlers
- [ ] Build UI components
- [ ] Implement single file mode
- [ ] Implement batch mode
- [ ] Add progress tracking
- [ ] Add results modal
- [ ] Test user flows

### **Testing**
- [ ] Test single file upload & review
- [ ] Test multiple files batch processing
- [ ] Test AI extraction accuracy
- [ ] Test ship validation
- [ ] Test duplicate detection
- [ ] Test error handling
- [ ] Test Google Drive upload
- [ ] Test with different file formats
- [ ] Test with large files (20MB)

### **Documentation**
- [ ] Update API documentation
- [ ] Create user guide
- [ ] Document AI prompt templates
- [ ] Create troubleshooting guide

---

## Questions to Confirm Before Implementation

1. **Apps Script Actions:**
   - Có sẵn action `upload_survey_report` chưa?
   - Có cần tạo action upload to SUMMARY folder không?

2. **Google Drive Structure:**
   - Folder "Class Survey Report" đã tồn tại chưa?
   - Folder "SUMMARY/Class & Flag Document" đã tồn tại chưa?

3. **Validation:**
   - Có cần validate ship name/IMO strict không? (Hay cho phép bypass như crew certificate?)
   - Có cần check duplicate không?

4. **File Organization:**
   - Summary file naming convention: `{survey_report_name}_AI_Summary.txt`?
   - Original file giữ nguyên tên hay rename?

5. **Batch Processing:**
   - Có giới hạn số file upload 1 lần không? (VD: max 10 files)
   - Staggered delay 2s có phù hợp không?

6. **UI/UX:**
   - Single file mode có cần show ship validation warning như crew cert không?
   - Batch mode có auto-skip duplicate hay show error?

---

## Các file sẽ được modify

### **Backend**
1. `/app/backend/server.py` - Add endpoints (~740 lines)
2. `/app/backend/dual_apps_script_manager.py` - Add methods (~250 lines)

### **Frontend**
1. `/app/frontend/src/App.js` - Add states, functions, UI (~790 lines)

### **Apps Script** (nếu cần)
1. Google Apps Script project - Add upload actions (~100 lines)

### **Documentation**
1. `/app/SURVEY_REPORT_AI_UPLOAD_WORKFLOW.md` - New file
2. `/app/SURVEY_REPORT_LIST_IMPLEMENTATION_SUMMARY.md` - Update

---

**Sẵn sàng implement khi bạn confirm!** 🚀

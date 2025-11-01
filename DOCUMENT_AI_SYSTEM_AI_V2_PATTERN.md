# DOCUMENT AI & SYSTEM AI INTEGRATION - V2 Pattern Analysis

## Overview
This document analyzes the V2 implementation pattern for Document AI and System AI integration in the Class Survey Report feature. This pattern should be used consistently for Crew Records and other features.

---

## ARCHITECTURE - V2 DUAL APPS SCRIPT MANAGER

### Key Components

1. **System Apps Script** (Document AI Processing)
   - Purpose: AI analysis only (Google Document AI)
   - URL: Stored in `ai_config` collection (`system_ai.document_ai.apps_script_url`)
   - Function: OCR and text extraction from documents

2. **Company Apps Script** (File Upload)
   - Purpose: Upload files to Company Google Drive
   - URL: Stored in `company_gdrive_config` collection (`web_app_url` or `company_apps_script_url`)
   - Function: Create folders and upload files

3. **System AI** (Field Extraction)
   - Purpose: Extract structured data from Document AI summary
   - Provider: Gemini, OpenAI (via Emergent LLM Key)
   - Function: Convert unstructured summary to structured JSON fields

---

## WORKFLOW - CLASS SURVEY REPORT ANALYSIS (V2)

### Frontend Flow

```javascript
// 1. User uploads PDF file
const response = await surveyReportService.analyzeFile(
  selectedShip.id,
  file,
  false // bypass_validation
);

// 2. Process analysis result
if (data.success && data.analysis) {
  // Auto-fill form with extracted fields
  setFormData({
    survey_report_name: analysis.survey_report_name,
    report_form: analysis.report_form,
    survey_report_no: analysis.survey_report_no,
    issued_date: analysis.issued_date,
    issued_by: analysis.issued_by,
    status: analysis.status,
    note: analysis.note,
    surveyor_name: analysis.surveyor_name
  });
  
  // Store complete analysis (including _file_content, _summary_text)
  setAnalyzedData(analysis);
}

// 3. User reviews and submits
// Files are uploaded in background after record creation
```

### Backend Flow

```
POST /api/survey-reports/analyze
↓
1. File Validation
   - Check file type (PDF only)
   - Check file size
   - Validate PDF magic bytes
   ↓
2. Check if PDF needs splitting (> 15 pages)
   - Yes → Split into chunks (12 pages each)
   - No → Process as single file
   ↓
3. Document AI Analysis (via System Apps Script)
   ↓
4. Targeted OCR (Tesseract) for header/footer
   ↓
5. System AI Field Extraction (Gemini/GPT)
   ↓
6. Ship Validation
   - Compare extracted ship name/IMO with selected ship
   - Show warning if mismatch
   ↓
7. Return analysis + file content (base64)
   - DO NOT upload to Drive yet
   ↓
8. User submits → Create record in MongoDB
   ↓
9. Background upload to Google Drive
   - Original PDF
   - Summary text file
   ↓
10. Update record with file IDs
```

---

## STEP-BY-STEP IMPLEMENTATION

### Step 1: Document AI Analysis (System Apps Script)

**Location:** `dual_apps_script_manager.py` → `_call_system_apps_script_for_ai()`

```python
# Payload structure
payload = {
    "action": "analyze_maritime_document_ai",  # or "analyze_passport_document_ai"
    "file_content": base64_encoded_content,
    "filename": filename,
    "content_type": content_type,
    "project_id": document_ai_config["project_id"],
    "location": document_ai_config.get("location", "us"),
    "processor_id": document_ai_config["processor_id"]
}

# Call System Apps Script
response = await session.post(
    system_apps_script_url,
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=aiohttp.ClientTimeout(total=120)
)

# Response structure
{
    "success": true,
    "data": {
        "summary": "Full text extracted from document..."
    }
}
```

**Key Points:**
- ✅ System Apps Script handles ONLY Document AI processing
- ✅ Returns text summary (unstructured data)
- ✅ No file upload happens here
- ✅ Timeout: 120 seconds

---

### Step 2: Targeted OCR (Optional Enhancement)

**Location:** `server.py` → `analyze_survey_report_file()`

```python
from targeted_ocr import get_ocr_processor

ocr_processor = get_ocr_processor()

if ocr_processor.is_available():
    # Extract header/footer from first page
    ocr_result = ocr_processor.extract_from_pdf(file_content, page_num=0)
    
    if ocr_result.get('ocr_success'):
        header_text = ocr_result.get('header_text', '')
        footer_text = ocr_result.get('footer_text', '')
        
        # Append OCR section to Document AI summary
        ocr_section = f"""
        === HEADER TEXT (Top 15% of page) ===
        {header_text}
        
        === FOOTER TEXT (Bottom 15% of page) ===
        {footer_text}
        """
        
        enhanced_summary = document_ai_summary + ocr_section
```

**Purpose:**
- Extract critical info from headers/footers (Report Form, Report No)
- Enhance Document AI summary with OCR data
- Improves field extraction accuracy

---

### Step 3: System AI Field Extraction

**Location:** `server.py` → `extract_survey_report_fields_from_summary()`

```python
async def extract_survey_report_fields_from_summary(
    summary_text: str,
    ai_provider: str,
    ai_model: str,
    use_emergent_key: bool,
    filename: str = ""
) -> dict:
    """
    Extract structured fields from Document AI summary using System AI
    """
    
    # Create extraction prompt
    prompt = create_survey_report_extraction_prompt(summary_text, filename)
    
    # Use Emergent LLM Key for System AI
    if use_emergent_key and ai_provider in ["google", "emergent"]:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        emergent_key = get_emergent_llm_key()
        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"survey_extraction_{int(time.time())}",
            system_message="You are a maritime survey report analysis expert."
        ).with_model("gemini", ai_model)
        
        user_message = UserMessage(text=prompt)
        ai_response = await chat.send_message(user_message)
        
        # Parse JSON response
        clean_content = ai_response.strip().replace('```json', '').replace('```', '').strip()
        extracted_data = json.loads(clean_content)
        
        return extracted_data
```

**Key Points:**
- ✅ Uses Emergent LLM Key (unified key for OpenAI, Gemini, Claude)
- ✅ System message provides expert context
- ✅ Returns structured JSON with extracted fields
- ✅ Post-processing for date formats, title casing, etc.

**Extracted Fields (Survey Report):**
```json
{
  "survey_report_name": "Hull",
  "report_form": "CG (02-19)",
  "survey_report_no": "12345",
  "issued_by": "Lloyd's Register",
  "issued_date": "2024-01-15",
  "ship_name": "BROTHER 36",
  "ship_imo": "1234567",
  "surveyor_name": "John Smith",
  "note": "",
  "status": "Valid"
}
```

---

### Step 4: Ship Validation

**Location:** `server.py` → `analyze_survey_report_file()`

```python
# Extract ship info from AI analysis
extracted_ship_name = analysis_result.get('ship_name', '')
extracted_ship_imo = analysis_result.get('ship_imo', '')

# Compare with selected ship
if extracted_ship_name and ship_name:
    # Fuzzy matching with similarity threshold
    similarity = fuzz.ratio(extracted_ship_name.lower(), ship_name.lower())
    
    if similarity < 70:  # Mismatch detected
        return {
            "success": True,
            "validation_error": True,
            "extracted_ship_name": extracted_ship_name,
            "extracted_ship_imo": extracted_ship_imo,
            "expected_ship_name": ship_name,
            "expected_ship_imo": ship_imo,
            "analysis": analysis_result  # Still return data
        }
```

**Frontend Handling:**
```javascript
if (data.validation_error) {
  const confirmed = window.confirm(
    `⚠️ WARNING: Ship information mismatch!\n` +
    `PDF: ${extracted_ship_name}\n` +
    `Selected: ${expected_ship_name}\n` +
    `Continue anyway?`
  );
  
  if (confirmed) {
    // Retry with bypass_validation = true
    const retryResponse = await surveyReportService.analyzeFile(
      selectedShip.id,
      file,
      true // Bypass validation
    );
  }
}
```

---

### Step 5: Return Analysis with File Content

**Critical:** File content is stored in analysis result for later upload

```python
# Store file content FIRST (before any AI processing)
analysis_result['_file_content'] = base64.b64encode(file_content).decode('utf-8')
analysis_result['_filename'] = filename
analysis_result['_content_type'] = survey_report_file.content_type
analysis_result['_ship_name'] = ship_name
analysis_result['_summary_text'] = ''  # Will be filled after AI analysis

# After successful AI analysis
if document_ai_summary:
    analysis_result['_summary_text'] = document_ai_summary

# Return to frontend
return {
    "success": True,
    "analysis": analysis_result  # Contains both extracted fields AND file content
}
```

**Why this pattern?**
- ✅ Ensures files can be uploaded even if AI fails
- ✅ User can review and edit extracted data before submitting
- ✅ Separates analysis from file upload
- ✅ Allows manual entry fallback

---

### Step 6: Create Record (After User Review)

**Frontend:**
```javascript
// User submits form
const createData = {
  ship_id: selectedShip.id,
  survey_report_name: formData.survey_report_name,
  report_form: formData.report_form,
  survey_report_no: formData.survey_report_no,
  issued_date: formData.issued_date,
  issued_by: formData.issued_by,
  status: formData.status,
  note: formData.note,
  surveyor_name: formData.surveyor_name
  // DO NOT include file_ids here
};

const response = await surveyReportService.create(createData);
const recordId = response.data.id;
```

**Backend:**
```python
@api_router.post("/survey-reports")
async def create_survey_report(
    survey_data: SurveyReportCreate,
    current_user: UserResponse = Depends(...)
):
    # Create record in MongoDB
    record_id = str(uuid.uuid4())
    
    record = {
        "id": record_id,
        "company_id": company_uuid,
        "ship_id": survey_data.ship_id,
        **survey_data.dict(),
        "created_at": datetime.now(timezone.utc),
        "created_by": current_user.username
    }
    
    await mongo_db.insert("survey_reports", record)
    
    return SurveyReportResponse(**record)
```

---

### Step 7: Background File Upload

**Frontend:**
```javascript
// After record creation, upload files in background
if (analyzedData?._file_content) {
  // Don't await - let it run in background
  surveyReportService.uploadFileOnly(
    response.data.id,
    {
      file_content: analyzedData._file_content,
      filename: analyzedData._filename,
      content_type: analyzedData._content_type,
      summary_text: analyzedData._summary_text,
      ship_name: analyzedData._ship_name
    }
  ).then(() => {
    toast.success('Files uploaded to Drive');
  }).catch(() => {
    toast.warning('Record saved but file upload failed');
  });
}

// Close modal immediately
onClose();
```

**Backend:**
```python
@api_router.post("/survey-reports/{record_id}/upload-file-only")
async def upload_survey_report_files_after_creation(
    record_id: str,
    file_data: dict,
    current_user: UserResponse = Depends(...)
):
    # Decode file content
    file_content = base64.b64decode(file_data['file_content'])
    
    # Use dual manager to upload files
    from dual_apps_script_manager import create_dual_apps_script_manager
    dual_manager = create_dual_apps_script_manager(company_uuid)
    
    upload_result = await dual_manager.upload_survey_report_files(
        survey_file_content=file_content,
        survey_filename=file_data['filename'],
        survey_content_type=file_data['content_type'],
        ship_name=file_data['ship_name'],
        summary_text=file_data['summary_text']
    )
    
    # Update record with file IDs
    if upload_result.get('success'):
        uploads = upload_result.get('uploads', {})
        survey_file_id = uploads.get('survey', {}).get('file_id')
        summary_file_id = uploads.get('summary', {}).get('file_id')
        
        await mongo_db.update(
            "survey_reports",
            {"id": record_id},
            {
                "file_id": survey_file_id,
                "summary_file_id": summary_file_id,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": current_user.username
            }
        )
    
    return {"success": True, "file_id": survey_file_id, "summary_file_id": summary_file_id}
```

---

## COMPARISON: V1 vs V2

### V1 Pattern (OLD - Crew Passport)
```
Upload File
↓
Analyze with Document AI + Upload to Drive (TOGETHER)
↓
Return analysis with Drive file IDs
↓
User reviews
↓
Create crew record WITH file IDs
```

**Problems:**
- ❌ Files uploaded even if user cancels
- ❌ Drive storage wasted if user doesn't submit
- ❌ Cannot recover if upload fails

### V2 Pattern (NEW - Survey Report)
```
Upload File
↓
Analyze with Document AI (NO UPLOAD)
↓
Store file content in base64
↓
Return analysis + file content
↓
User reviews and edits
↓
Create record WITHOUT file IDs
↓
Background upload to Drive
↓
Update record with file IDs
```

**Benefits:**
- ✅ No wasted Drive storage
- ✅ User can cancel without consequence
- ✅ Manual entry fallback if AI fails
- ✅ Faster modal close (background upload)
- ✅ Better UX with progress indicators

---

## CONFIGURATION

### System AI Config (MongoDB - ai_config collection)
```json
{
  "id": "system_ai",
  "provider": "google",
  "model": "gemini-2.0-flash-exp",
  "use_emergent_key": true,
  "document_ai": {
    "enabled": true,
    "project_id": "your-project-id",
    "location": "us",
    "processor_id": "your-processor-id",
    "apps_script_url": "https://script.google.com/macros/s/.../exec"
  }
}
```

### Company Google Drive Config (MongoDB - company_gdrive_config collection)
```json
{
  "company_id": "company-uuid",
  "web_app_url": "https://script.google.com/macros/s/.../exec",
  "parent_folder_id": "drive-folder-id"
}
```

---

## ERROR HANDLING

### 1. Document AI Analysis Failed
```python
# Backend returns empty analysis
analysis_result = {
    "survey_report_name": "",
    "report_form": "",
    ...
    "_file_content": base64_file,  # Still include file content
    "_summary_text": ""
}

# Frontend shows manual entry form
toast.warning('AI analysis failed. Please enter manually.');
```

### 2. File Upload Failed (After Record Creation)
```python
# Record already saved in MongoDB
# Upload failure is non-critical

toast.warning('Record saved but file upload to Drive failed');
```

### 3. Ship Validation Mismatch
```python
# Show warning, allow user to decide
if (!window.confirm('Ship mismatch. Continue?')) {
  handleRemoveFile();
  return;
}

# Retry with bypass_validation = true
```

---

## BATCH PROCESSING (Multiple Files)

### Pattern
```javascript
// Process files in parallel with stagger
files.forEach((file, index) => {
  setTimeout(async () => {
    // 1. Analyze file
    const analysis = await analyzeFile(file);
    
    // 2. Auto-create record
    const record = await createRecord(analysis);
    
    // 3. Upload files in background
    await uploadFileOnly(record.id, analysis);
    
    // 4. Update progress
    updateProgress(index + 1, files.length);
  }, index * 1000); // 1-second stagger
});
```

---

## MIGRATION CHECKLIST FOR CREW ADD MODAL

### ✅ Use V2 Pattern
1. Call `/api/crew/analyze-passport` (analysis only, no upload)
2. Store file content in base64 in analysis result
3. Return analysis + file content to frontend
4. User reviews and edits form
5. Create crew record WITHOUT file IDs
6. Background upload via `/api/crew/{crew_id}/upload-passport-files`
7. Update crew record with file IDs

### ✅ Use Dual Apps Script Manager
```python
from dual_apps_script_manager import create_dual_apps_script_manager

dual_manager = create_dual_apps_script_manager(company_uuid)

# For analysis only
analysis_result = await dual_manager.analyze_passport_only(
    file_content=file_content,
    filename=filename,
    content_type=content_type,
    document_ai_config=document_ai_config
)

# For file upload (after crew creation)
upload_result = await dual_manager.upload_passport_files(
    passport_file_content=file_content,
    passport_filename=filename,
    passport_content_type=content_type,
    ship_name=ship_name,
    summary_text=summary_text
)
```

### ✅ Use System AI for Field Extraction
```python
# Extract passport fields from Document AI summary
extracted_fields = await extract_maritime_document_fields_from_summary(
    document_summary,
    document_type="passport",  # or "certificate", "survey_report"
    ai_provider="google",
    ai_model="gemini-2.0-flash-exp",
    use_emergent_key=True
)
```

---

## KEY TAKEAWAYS

1. **Separate Analysis from Upload**
   - Analysis happens immediately
   - Upload happens after record creation

2. **Store File Content in Analysis**
   - Base64 encode file content
   - Include in analysis response
   - Upload later in background

3. **Use Dual Apps Script Manager**
   - System Apps Script: Document AI only
   - Company Apps Script: File upload only

4. **Use System AI for Extraction**
   - Gemini/GPT via Emergent LLM Key
   - Convert summary to structured fields

5. **Better UX**
   - Fast modal close
   - Background upload with progress
   - Manual entry fallback

---

**Last Updated:** 2025-01-01
**V2 Reference:** 
- Frontend: `/app/frontend/src/components/ClassSurveyReport/AddSurveyReportModal.jsx`
- Backend: `/app/backend/server.py` lines 6478-7200
- Dual Manager: `/app/backend/dual_apps_script_manager.py`

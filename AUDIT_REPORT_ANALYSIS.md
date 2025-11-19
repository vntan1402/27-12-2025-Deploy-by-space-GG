# AUDIT REPORT MODULE - COMPLETE FLOW ANALYSIS (Backend V1)

## 📋 MỤC LỤC (TABLE OF CONTENTS)

1. [Tổng Quan Luồng (Flow Overview)](#1-tổng-quan-luồng-flow-overview)
2. [Frontend Flow](#2-frontend-flow)
3. [Backend Endpoints](#3-backend-endpoints)
4. [Document AI Integration](#4-document-ai-integration)
5. [PDF Splitting & Chunking](#5-pdf-splitting--chunking)
6. [File Upload to Google Drive](#6-file-upload-to-google-drive)
7. [Helper Functions & Utilities](#7-helper-functions--utilities)
8. [Key Configuration](#8-key-configuration)

---

## 1. TỔNG QUAN LUỒNG (FLOW OVERVIEW)

### Quy Trình Hoàn Chỉnh (Complete Workflow)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     AUDIT REPORT WORKFLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

User Upload File (PDF)
        │
        ├──▶ SINGLE FILE MODE
        │    │
        │    ▼
        │    Frontend: analyzeFile()
        │    │
        │    ▼
        │    POST /api/audit-reports/analyze-file
        │    │
        │    ├──▶ Check file size & page count
        │    │    │
        │    │    ├─▶ IF ≤15 pages:
        │    │    │   └─▶ Single file processing
        │    │    │       └─▶ analyze_audit_report_only()
        │    │    │           └─▶ Document AI extraction
        │    │    │               └─▶ System AI field extraction
        │    │    │
        │    │    └─▶ IF >15 pages:
        │    │        └─▶ PDF Splitting (max 12 pages/chunk)
        │    │            └─▶ Process each chunk
        │    │                └─▶ Merge results
        │    │
        │    ▼
        │    Return analysis result with:
        │    - Extracted fields
        │    - Base64 file content (_file_content)
        │    - Summary text (_summary_text)
        │    - Split info (_split_info)
        │    │
        │    ▼
        │    Frontend: Auto-fill form
        │    │
        │    ▼
        │    User review & submit
        │    │
        │    ▼
        │    POST /api/audit-reports (Create DB record)
        │    │
        │    ▼
        │    POST /api/audit-reports/{id}/upload-files
        │    │
        │    └─▶ Upload to Google Drive:
        │        ├─▶ Original file: ShipName/ISM-ISPS-MLC/Audit Report/{filename}
        │        └─▶ Summary file: ShipName/ISM-ISPS-MLC/Audit Report/{filename}_Summary.txt
        │
        │
        └──▶ BATCH FILE MODE (Multiple files)
             │
             ▼
             Frontend: onStartBatchProcessing()
             │
             └─▶ For each file:
                 └─▶ Same flow as SINGLE FILE MODE

```

---

## 2. FRONTEND FLOW

### 2.1 Component: `AddAuditReportModal.jsx`

**Location:** `/app/frontend/src/components/AuditReport/AddAuditReportModal.jsx`

#### Key Features:
- ✅ Drag & drop PDF upload
- ✅ AI analysis with OCR
- ✅ Ship name validation
- ✅ Auto-populate form fields
- ✅ Manual edit capability
- ✅ Duplicate check
- ✅ Background file upload
- ✅ Split PDF support (>15 pages)
- ✅ Batch processing support

#### File Upload Limits:
```javascript
// Max file size: 50MB per file
const oversizedFiles = fileArray.filter(f => f.size > 50 * 1024 * 1024);
```

#### Single File Flow:

```javascript
// 1. File Selection
handleFileSelect(files) → 
  ├─ Validate PDF format
  ├─ Check file size (max 50MB)
  └─ analyzeFile(file)

// 2. AI Analysis
analyzeFile(file) →
  ├─ auditReportService.analyzeFile(ship_id, file, bypass_validation)
  ├─ Handle validation error (ship mismatch)
  └─ processAnalysisSuccess(analysis)
      └─ Auto-fill form fields
          ├─ audit_report_name
          ├─ audit_type
          ├─ report_form
          ├─ audit_report_no
          ├─ audit_date
          ├─ issued_by
          ├─ auditor_name
          ├─ status
          └─ note

// 3. Form Submit
handleSubmit() →
  ├─ Validate required fields
  ├─ auditReportService.create(reportData)
  ├─ Close modal
  ├─ Refresh list (onReportAdded)
  └─ uploadFilesInBackground()
      └─ auditReportService.uploadFiles(
            reportId,
            fileContent (base64),
            filename,
            contentType,
            summaryText
         )
```

#### Batch File Flow:

```javascript
// When multiple files selected
onStartBatchProcessing(fileArray) →
  └─ Parent component handles batch processing
      └─ For each file:
          ├─ analyzeFile()
          ├─ createDocument()
          └─ uploadFilesToDrive()
```

#### Important State Variables:

```javascript
const [uploadedFile, setUploadedFile] = useState(null);        // Current file
const [analyzedData, setAnalyzedData] = useState(null);        // Complete analysis result
const [formData, setFormData] = useState({...});               // Form fields
const [showValidationModal, setShowValidationModal] = useState(false); // Ship validation
```

---

## 3. BACKEND ENDPOINTS

### 3.1 Analyze File Endpoint

**Route:** `POST /api/audit-reports/analyze-file`

**Location:** `/app/backend-v1/server.py` (lines 9746-10322)

**Function:** `analyze_audit_report_file()`

**Parameters:**
```python
- audit_report_file: UploadFile (PDF file)
- ship_id: str (Form data)
- bypass_validation: str = "false" (Form data)
```

**Returns:**
```python
{
    "success": True/False,
    "analysis": {
        # Extracted fields
        "audit_report_name": str,
        "audit_type": str,        # ISM, ISPS, MLC, CICA
        "report_form": str,
        "audit_report_no": str,
        "audit_date": str,        # YYYY-MM-DD
        "issued_by": str,
        "auditor_name": str,
        "ship_name": str,
        "ship_imo": str,
        "status": str,            # Valid/Expired
        "note": str,
        "confidence_score": float,
        
        # Internal data for upload
        "_file_content": str,     # Base64 encoded
        "_filename": str,
        "_content_type": str,
        "_summary_text": str,     # Full summary for upload
        "_split_info": {          # If PDF was split
            "was_split": bool,
            "total_pages": int,
            "chunks_count": int,
            "successful_chunks": int
        }
    },
    "validation_error": bool,     # If ship mismatch
    "extracted_ship_name": str,
    "expected_ship_name": str
}
```

**Processing Steps:**

```python
# 1. Validate file
if not filename.lower().endswith('.pdf'):
    raise HTTPException(400, "Only PDF files supported")

if not file_content.startswith(b'%PDF'):
    raise HTTPException(400, "Invalid PDF format")

# 2. Check page count & decide splitting
from pdf_splitter import PDFSplitter
splitter = PDFSplitter(max_pages_per_chunk=12)
total_pages = splitter.get_page_count(file_content)
needs_split = splitter.needs_splitting(file_content)  # True if >15 pages

# 3. Get ship & company info
company_uuid = await resolve_company_id(current_user)
ship = await mongo_db.find_one("ships", {"id": ship_id, "company": company_uuid})

# 4. Get AI configuration
ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
document_ai_config = ai_config_doc.get("document_ai", {})

# 5. Store file content FIRST (important!)
analysis_result['_file_content'] = base64.b64encode(file_content).decode('utf-8')
analysis_result['_filename'] = filename
analysis_result['_content_type'] = content_type
analysis_result['_summary_text'] = ''  # Will be filled

# 6a. Single file processing (≤15 pages)
if not needs_split:
    analysis_only_result = await dual_manager.analyze_audit_report_only(
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        document_ai_config=document_ai_config
    )
    
    # Extract Document AI summary
    ai_analysis = analysis_only_result.get('ai_analysis', {})
    summary_text = ai_analysis.get('data', {}).get('summary', '')
    analysis_result['_summary_text'] = summary_text
    
    # OCR Enhancement (header/footer extraction)
    from targeted_ocr import get_ocr_processor
    ocr_processor = get_ocr_processor()
    ocr_result = ocr_processor.extract_from_pdf(file_content, page_num=0)
    
    # Append OCR text to summary
    if ocr_result and ocr_result.get('ocr_success'):
        header_text = ocr_result.get('header_text', '').strip()
        footer_text = ocr_result.get('footer_text', '').strip()
        # Add OCR section to summary_text
        summary_text += ocr_section
        analysis_result['_summary_text'] = summary_text
    
    # Extract fields using System AI
    # Method 1: DIRECT PDF extraction (preferred)
    extracted_fields = await extract_audit_report_fields_from_pdf_directly(
        file_content,
        filename,
        ai_model,
        use_emergent_key
    )
    
    # Method 2: Summary-based extraction (fallback)
    if not extracted_fields:
        extracted_fields = await extract_audit_report_fields_from_summary(
            summary_text,
            ai_provider,
            ai_model,
            use_emergent_key,
            filename
        )
    
    # Update analysis_result with extracted fields
    analysis_result.update(extracted_fields)

# 6b. Multi-chunk processing (>15 pages)
else:
    chunks = splitter.split_pdf(file_content, filename)
    
    # Process each chunk
    chunk_results = []
    for i, chunk in enumerate(chunks):
        chunk_analysis = await dual_manager.analyze_audit_report_only(
            file_content=chunk['content'],
            filename=f"{filename}_chunk_{i+1}",
            content_type=content_type,
            document_ai_config=document_ai_config
        )
        if chunk_analysis.get('success'):
            chunk_results.append(chunk_analysis)
    
    # Merge results from chunks
    # Use field mapping with fallbacks
    first_chunk = chunk_results[0]['result']
    ai_analysis = first_chunk.get('ai_analysis', {})
    data = ai_analysis.get('data', {})
    
    audit_report_name = data.get('audit_report_name') or data.get('survey_report_name')
    audit_type = data.get('audit_type') or data.get('audit_type_extracted')
    # ... merge other fields
    
    analysis_result.update({
        'audit_report_name': audit_report_name,
        'audit_type': audit_type,
        # ... other fields
        '_split_info': {
            'was_split': True,
            'total_pages': total_pages,
            'chunks_count': len(chunks),
            'successful_chunks': len(chunk_results)
        }
    })

# 7. Build enhanced summary
summary_lines = [
    "="*60,
    "AUDIT REPORT ANALYSIS SUMMARY",
    "="*60,
    f"File: {filename}",
    f"Ship: {ship_name}",
    # ... all extracted fields
]
formatted_summary = '\n'.join(summary_lines)

# Combine formatted + raw Document AI text
combined_summary = formatted_summary + "\n\n" + raw_document_ai_text
analysis_result['_summary_text'] = combined_summary

# 8. Ship validation
extracted_ship_name = analysis_result.get('ship_name', '').strip()
extracted_ship_imo = analysis_result.get('ship_imo', '').strip()

validation_result = validate_ship_info_match(
    extracted_ship_name,
    extracted_ship_imo,
    ship_name,
    ship_imo
)

if not validation_result.get('overall_match') and not bypass_validation:
    # Return validation error
    return {
        "success": False,
        "validation_error": True,
        "extracted_ship_name": extracted_ship_name,
        "expected_ship_name": ship_name
    }

# 9. Return success
return {
    "success": True,
    "analysis": analysis_result
}
```

---

### 3.2 Upload Files Endpoint

**Route:** `POST /api/audit-reports/{report_id}/upload-files`

**Location:** `/app/backend-v1/server.py` (lines 10322-10472)

**Function:** `upload_audit_report_files()`

**Parameters:**
```python
- report_id: str (Path parameter)
- file_content: str (Body - base64 encoded)
- filename: str (Body)
- content_type: str (Body)
- summary_text: str (Body - optional)
```

**Returns:**
```python
{
    "success": True,
    "file_id": str,              # GDrive file ID (original)
    "summary_file_id": str,      # GDrive file ID (summary)
    "message": "Files uploaded successfully"
}
```

**Processing Steps:**

```python
# 1. Validate report exists
report = await mongo_db.find_one("audit_reports", {"id": report_id})

# 2. Get company & ship info
company_uuid = await resolve_company_id(current_user)
ship_id = report.get("ship_id")
ship = await mongo_db.find_one("ships", {"id": ship_id, "company": company_uuid})

# 3. Decode base64 file content
file_bytes = base64.b64decode(file_content)

# 4. Initialize Dual Manager
from dual_apps_script_manager import create_dual_apps_script_manager
dual_manager = create_dual_apps_script_manager(company_uuid)

# 5. Upload original file
# Path: ShipName/ISM-ISPS-MLC/Audit Report/
original_upload = await dual_manager.upload_audit_report_file(
    file_content=file_bytes,
    filename=filename,
    content_type=content_type,
    ship_name=ship_name,
    audit_report_name=audit_report_name
)

audit_report_file_id = original_upload.get('file_id')

# 6. Upload summary file (if provided)
if summary_text and summary_text.strip():
    base_name = filename.rsplit('.', 1)[0]
    summary_filename = f"{base_name}_Summary.txt"
    
    summary_upload = await dual_manager.upload_audit_report_summary(
        summary_text=summary_text,
        filename=summary_filename,
        ship_name=ship_name
    )
    
    audit_report_summary_file_id = summary_upload.get('summary_file_id')

# 7. Update database with file IDs
update_data = {
    'audit_report_file_id': audit_report_file_id,
    'audit_report_summary_file_id': audit_report_summary_file_id,
    'updated_at': datetime.now(timezone.utc).isoformat()
}
await mongo_db.update("audit_reports", {"id": report_id}, update_data)

# 8. Return success
return {
    "success": True,
    "file_id": audit_report_file_id,
    "summary_file_id": audit_report_summary_file_id,
    "message": "Files uploaded successfully"
}
```

---

### 3.3 Other Endpoints

```python
# Get all audit reports for a ship
GET /api/audit-reports?ship_id={ship_id}
→ get_audit_reports()

# Get single audit report
GET /api/audit-reports/{report_id}
→ get_audit_report()

# Create audit report (DB record only)
POST /api/audit-reports
→ create_audit_report()

# Update audit report
PUT /api/audit-reports/{report_id}
→ update_audit_report()

# Bulk delete
DELETE /api/audit-reports/bulk-delete
→ bulk_delete_audit_reports()
```

---

## 4. DOCUMENT AI INTEGRATION

### 4.1 Main Function: `analyze_audit_report_only()`

**Location:** `/app/backend-v1/dual_apps_script_manager.py` (lines 745-806)

**Purpose:** Analyze audit report using Document AI WITHOUT uploading

```python
async def analyze_audit_report_only(
    self,
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze audit report using Document AI
    Returns analysis results only (no file IDs)
    """
    # Load configuration
    await self._load_configuration()
    
    # Call System Apps Script for Document AI analysis
    ai_result = await self._call_system_apps_script_for_ai(
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        document_ai_config=document_ai_config,
        action="analyze_maritime_document_ai",
        document_type="audit_report"  # Important!
    )
    
    return {
        'success': True,
        'message': 'Audit report analysis completed',
        'ai_analysis': ai_result,
        'processing_method': 'analysis_only'
    }
```

### 4.2 Document AI Configuration

**Source:** MongoDB collection `ai_config` (document ID: `system_ai`)

```python
ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})

document_ai_config = {
    "enabled": True,
    "project_id": "your-gcp-project-id",
    "processor_id": "your-processor-id",
    "location": "us"  # or "eu"
}

# System AI config for field extraction
ai_provider = "google"  # or "emergent"
ai_model = "gemini-2.0-flash"
use_emergent_key = True
```

---

## 5. PDF SPLITTING & CHUNKING

### 5.1 PDFSplitter Utility

**Location:** `/app/backend-v1/pdf_splitter.py`

**Key Configuration:**

```python
MAX_PAGES_PER_CHUNK = 12  # Maximum pages per chunk
SPLIT_THRESHOLD = 15      # Split if more than 15 pages
```

**Usage:**

```python
from pdf_splitter import PDFSplitter

splitter = PDFSplitter(max_pages_per_chunk=12)

# Get page count
total_pages = splitter.get_page_count(file_content)

# Check if splitting needed
needs_split = splitter.needs_splitting(file_content)  # True if >15 pages

# Split PDF
chunks = splitter.split_pdf(file_content, filename)

# Returns list of chunks:
# [
#   {
#     'content': bytes,
#     'page_range': '1-12',
#     'chunk_index': 0
#   },
#   {
#     'content': bytes,
#     'page_range': '13-24',
#     'chunk_index': 1
#   }
# ]
```

### 5.2 Chunk Processing Flow

```python
# Process each chunk
chunk_results = []
for i, chunk in enumerate(chunks):
    logger.info(f"Processing chunk {i+1}/{len(chunks)} (pages {chunk['page_range']})")
    
    chunk_analysis = await dual_manager.analyze_audit_report_only(
        file_content=chunk['content'],
        filename=f"{filename}_chunk_{i+1}",
        content_type=content_type,
        document_ai_config=document_ai_config
    )
    
    if chunk_analysis.get('success'):
        chunk_results.append({
            'chunk_index': i,
            'page_range': chunk['page_range'],
            'result': chunk_analysis
        })
```

### 5.3 Result Merging

**Important:** Field mapping with fallbacks to handle different field names

```python
# Use first successful chunk as base
first_chunk = chunk_results[0]['result']
ai_analysis = first_chunk.get('ai_analysis', {})
data = ai_analysis.get('data', {})

# Field name mapping with fallbacks
audit_report_name = data.get('audit_report_name') or data.get('survey_report_name', '')
audit_type = data.get('audit_type') or data.get('audit_type_extracted', '')
report_form = data.get('report_form') or data.get('report_form_extracted', '')
audit_report_no = data.get('audit_report_no') or data.get('survey_report_no', '')
audit_date = data.get('audit_date') or data.get('issued_date', '')
auditor_name = data.get('auditor_name') or data.get('surveyor_name', '')

# Merge other fields...
analysis_result.update({
    'audit_report_name': audit_report_name,
    'audit_type': audit_type,
    'report_form': report_form,
    'audit_report_no': audit_report_no,
    'issued_by': data.get('issued_by', ''),
    'audit_date': audit_date,
    'ship_name': data.get('ship_name', ''),
    'ship_imo': data.get('ship_imo', ''),
    'auditor_name': auditor_name,
    'note': data.get('note', ''),
    'status': data.get('status', 'Valid'),
    'confidence_score': ai_analysis.get('confidence_score', 0.0),
    'processing_method': 'merged_from_chunks'
})
```

---

## 6. FILE UPLOAD TO GOOGLE DRIVE

### 6.1 Upload Original File

**Function:** `upload_audit_report_file()`

**Location:** `/app/backend-v1/dual_apps_script_manager.py` (lines 1859-1939)

**Target Path:** `ShipName/ISM-ISPS-MLC/Audit Report/`

```python
async def upload_audit_report_file(
    self,
    file_content: bytes,
    filename: str,
    content_type: str,
    ship_name: str,
    audit_report_name: str
) -> Dict[str, Any]:
    """
    Upload audit report file to Google Drive
    Path: ShipName/ISM-ISPS-MLC/Audit Report/
    """
    # Load configuration
    await self._load_configuration()
    
    # Validate configuration
    if not self.company_apps_script_url:
        raise ValueError("Company Apps Script URL not configured")
    
    if not self.parent_folder_id:
        raise ValueError("Company Google Drive Folder ID not configured")
    
    # Upload to nested path
    audit_report_upload = await self._call_company_apps_script({
        'action': 'upload_file_with_folder_creation',
        'parent_folder_id': self.parent_folder_id,  # ROOT folder
        'ship_name': ship_name,                     # Creates/finds ShipName folder
        'parent_category': 'ISM-ISPS-MLC',          # First level under ShipName
        'category': 'Audit Report',                 # Second level under ISM-ISPS-MLC
        'filename': filename,
        'file_content': base64.b64encode(file_content).decode('utf-8'),
        'content_type': content_type
    })
    
    if audit_report_upload.get('success'):
        file_id = audit_report_upload.get('file_id')
        return {
            'success': True,
            'message': 'Audit report file uploaded successfully',
            'file_id': file_id,
            'file_path': audit_report_upload.get('file_path')
        }
    else:
        return {
            'success': False,
            'message': 'Audit report file upload failed',
            'error': audit_report_upload.get('message')
        }
```

### 6.2 Upload Summary File

**Function:** `upload_audit_report_summary()`

**Location:** `/app/backend-v1/dual_apps_script_manager.py` (lines 1941-2010)

**Target Path:** `ShipName/ISM-ISPS-MLC/Audit Report/` (same as original)

```python
async def upload_audit_report_summary(
    self,
    summary_text: str,
    filename: str,
    ship_name: str
) -> Dict[str, Any]:
    """
    Upload audit report summary file to Google Drive
    Path: ShipName/ISM-ISPS-MLC/Audit Report/
    
    Filename format: {original_basename}_Summary.txt
    """
    # Load configuration
    await self._load_configuration()
    
    # Upload summary to same path as audit report
    summary_upload = await self._call_company_apps_script({
        'action': 'upload_file_with_folder_creation',
        'parent_folder_id': self.parent_folder_id,
        'ship_name': ship_name,
        'parent_category': 'ISM-ISPS-MLC',
        'category': 'Audit Report',
        'filename': filename,
        'file_content': base64.b64encode(summary_text.encode('utf-8')).decode('utf-8'),
        'content_type': 'text/plain'
    })
    
    if summary_upload.get('success'):
        file_id = summary_upload.get('file_id')
        return {
            'success': True,
            'message': 'Audit report summary uploaded successfully',
            'summary_file_id': file_id,
            'file_path': summary_upload.get('file_path')
        }
    else:
        return {
            'success': False,
            'message': 'Audit report summary upload failed',
            'error': summary_upload.get('message')
        }
```

### 6.3 Google Drive Path Structure

```
ROOT_FOLDER (parent_folder_id)
└── ShipName (e.g., "MV ATLANTIC HERO")
    └── ISM-ISPS-MLC (parent_category)
        └── Audit Report (category)
            ├── ISM_Annual_Audit_2024.pdf (original file)
            └── ISM_Annual_Audit_2024_Summary.txt (summary file)
```

**Important Notes:**
- ✅ Folder name is `ISM-ISPS-MLC` (with hyphens, no spaces)
- ✅ Folders are created automatically if they don't exist
- ✅ Uses company-specific Apps Script URL
- ✅ Uses company-specific parent folder ID

---

## 7. HELPER FUNCTIONS & UTILITIES

### 7.1 Field Extraction Functions

#### 7.1.1 Direct PDF Extraction (Priority 1)

**Function:** `extract_audit_report_fields_from_pdf_directly()`

**Location:** `/app/backend-v1/server.py` (lines 6738-6950)

**Purpose:** Extract fields DIRECTLY from PDF using Gemini 2.0 Flash

**Why use this?**
- ✅ More reliable for header/footer content
- ✅ Bypasses Document AI limitations
- ✅ Better extraction of `report_form` and `issued_by`

```python
async def extract_audit_report_fields_from_pdf_directly(
    file_content: bytes,
    filename: str,
    ai_model: str,
    use_emergent_key: bool
) -> dict:
    """
    Extract fields DIRECTLY from PDF (not from summary)
    Reads header/footer content that Document AI might miss
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    emergent_key = get_emergent_llm_key()
    
    # Create extraction prompt
    extraction_prompt = f"""You are an AI specialized in maritime audit report extraction.

**TASK**: Extract key information from this PDF audit report.

**IMPORTANT**: Read the ENTIRE document including headers and footers.

**EXTRACT THE FOLLOWING FIELDS** (return as JSON):

{{
    "audit_report_name": "Main title/name",
    "audit_type": "ISM CODE, ISPS, MLC, CICA, etc.",
    "report_form": "**CRITICAL** - Form code (CHECK FOOTER/HEADER FIRST) - e.g., '07-23', 'CG (02-19)'",
    "audit_report_no": "Report number",
    "issued_by": "**IMPORTANT** - Organization (CHECK LETTERHEAD/HEADER) - e.g., 'DNV GL', 'PMDS'",
    "audit_date": "Date (YYYY-MM-DD)",
    "auditor_name": "Auditor name(s)",
    "ship_name": "Ship name",
    "ship_imo": "IMO number (7 digits)",
    "note": "Notes"
}}

**CRITICAL FOR REPORT_FORM**:
- LOOK IN FOOTER/HEADER FIRST
- May appear as "(07-23)", "Form 7.10", "CG (02-19)"
- Often repeats on every page

**CRITICAL FOR ISSUED_BY**:
- LOOK IN LETTERHEAD/HEADER FIRST
- Check company logo, name at top
- Common: DNV GL, Lloyd's Register, PMDS, Bureau Veritas

**OUTPUT**: Return ONLY valid JSON, no extra text.
"""
    
    # Create chat with file upload
    chat = LlmChat(
        api_key=emergent_key,
        session_id=f"direct_pdf_extract_{int(time.time())}",
        system_message="You are a maritime document analysis expert."
    ).with_model("gemini", ai_model)
    
    # Encode PDF as base64
    pdf_base64 = base64.b64encode(file_content).decode('utf-8')
    
    # Send PDF with prompt
    user_message = UserMessage(
        text=extraction_prompt,
        files=[{
            "data": pdf_base64,
            "mime_type": "application/pdf",
            "name": filename
        }]
    )
    
    ai_response = await chat.send_message(user_message)
    
    # Parse JSON response
    clean_content = ai_response.replace('```json', '').replace('```', '').strip()
    extracted_data = json.loads(clean_content)
    
    # Post-processing: Extract report_form from filename (PRIORITY 1)
    # ... (pattern matching logic)
    
    return extracted_data
```

#### 7.1.2 Summary-Based Extraction (Fallback)

**Function:** `extract_audit_report_fields_from_summary()`

**Location:** `/app/backend-v1/server.py` (lines 7031-7273)

**Purpose:** Extract fields from Document AI summary text

```python
async def extract_audit_report_fields_from_summary(
    summary_text: str,
    ai_provider: str,
    ai_model: str,
    use_emergent_key: bool,
    filename: str = ""
) -> dict:
    """
    Extract audit report fields from Document AI summary
    Fallback method if direct PDF extraction fails
    """
    # Create extraction prompt
    prompt = create_audit_report_extraction_prompt(summary_text, filename)
    
    # Use System AI (Gemini) for extraction
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    emergent_key = get_emergent_llm_key()
    chat = LlmChat(
        api_key=emergent_key,
        session_id=f"audit_extraction_{int(time.time())}",
        system_message="You are a maritime audit report analysis expert."
    ).with_model("gemini", ai_model)
    
    user_message = UserMessage(text=prompt)
    ai_response = await chat.send_message(user_message)
    
    # Parse JSON response
    clean_content = ai_response.replace('```json', '').replace('```', '').strip()
    extracted_data = json.loads(clean_content)
    
    # Post-processing
    # 1. Parse audit_date (check if it's actually a report_form)
    # 2. Determine audit_type from multiple sources (filename > report_form > name)
    # 3. Extract report_form from filename patterns
    # 4. Normalize issued_by abbreviations
    
    return extracted_data
```

#### 7.1.3 Prompt Creation

**Function:** `create_audit_report_extraction_prompt()`

**Location:** `/app/backend-v1/server.py` (lines 7274-7450)

```python
def create_audit_report_extraction_prompt(summary_text: str, filename: str = "") -> str:
    """
    Create structured prompt for audit report field extraction
    """
    prompt = f"""You are an AI specialized in maritime audit report information extraction.

**INPUT**: Below is the Document AI text extraction from an audit report file.

**FILENAME**: {filename}
(Filename often contains hints about audit type and report form)

**TASK**: Extract the following fields and return as JSON:

{{
    "audit_report_name": "Main title or name",
    "audit_type": "ISM, ISPS, MLC, or CICA",
    "report_form": "Form code/number - CRITICAL",
    "audit_report_no": "Report number/reference",
    "issued_by": "Organization that issued/conducted audit",
    "audit_date": "Date of audit (YYYY-MM-DD)",
    "auditor_name": "Name(s) of auditor(s)",
    "ship_name": "Ship name",
    "ship_imo": "IMO number (7 digits only)",
    "note": "Important notes"
}}

**CRITICAL INSTRUCTIONS FOR REPORT_FORM**:
- Look in footer/header sections
- May appear as: "(07-23)", "CG (02-19)", "Form 7.10"
- Check "ADDITIONAL INFORMATION FROM HEADER/FOOTER" section
- Filename hint: {filename}

**CRITICAL INSTRUCTIONS FOR ISSUED_BY**:
- Look in letterhead/header sections
- Extract FULL organization name (not abbreviation)
- Common: DNV GL, Lloyd's Register, Bureau Veritas, PMDS
- DO NOT confuse with auditor name

**OUTPUT**: Return ONLY valid JSON.

---

**DOCUMENT TEXT:**

{summary_text}
"""
    return prompt
```

### 7.2 OCR Enhancement (Targeted OCR)

**Module:** `targeted_ocr.py`

**Purpose:** Extract header/footer text that Document AI might miss

```python
from targeted_ocr import get_ocr_processor

ocr_processor = get_ocr_processor()

if ocr_processor.is_available():
    # Extract from first page
    ocr_result = ocr_processor.extract_from_pdf(file_content, page_num=0)
    
    if ocr_result and ocr_result.get('ocr_success'):
        header_text = ocr_result.get('header_text', '').strip()
        footer_text = ocr_result.get('footer_text', '').strip()
        
        # Append to summary
        ocr_section = f"""
{'='*60}
ADDITIONAL INFORMATION FROM HEADER/FOOTER (OCR Extraction)
(Extracted for report form and reference numbers)
{'='*60}

=== HEADER TEXT (Top 15% of page) ===
{header_text}

=== FOOTER TEXT (Bottom 15% of page) ===
{footer_text}
{'='*60}
"""
        
        summary_text += ocr_section
```

### 7.3 Ship Validation

**Function:** `validate_ship_info_match()`

**Purpose:** Check if extracted ship name/IMO matches selected ship

```python
def validate_ship_info_match(
    extracted_ship_name: str,
    extracted_ship_imo: str,
    expected_ship_name: str,
    expected_ship_imo: str
) -> dict:
    """
    Validate ship information match
    Returns: {
        'overall_match': bool,
        'name_match': bool,
        'imo_match': bool,
        'confidence': str
    }
    """
    # Normalize for comparison
    extracted_name_clean = extracted_ship_name.upper().strip()
    expected_name_clean = expected_ship_name.upper().strip()
    
    # Check name similarity (fuzzy matching)
    name_match = (
        extracted_name_clean == expected_name_clean or
        extracted_name_clean in expected_name_clean or
        expected_name_clean in extracted_name_clean
    )
    
    # Check IMO (exact match required)
    imo_match = extracted_ship_imo == expected_ship_imo if extracted_ship_imo else False
    
    # Overall match: either name OR IMO matches
    overall_match = name_match or imo_match
    
    return {
        'overall_match': overall_match,
        'name_match': name_match,
        'imo_match': imo_match,
        'confidence': 'high' if (name_match and imo_match) else 'medium'
    }
```

---

## 8. KEY CONFIGURATION

### 8.1 Environment Variables

```python
# MongoDB Connection
MONGO_URL = os.environ.get('MONGO_URL')

# Emergent LLM Key (for AI operations)
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Google Cloud Project (for Document AI)
GCP_PROJECT_ID = "your-project-id"
GCP_PROCESSOR_ID = "your-processor-id"
GCP_LOCATION = "us"  # or "eu"
```

### 8.2 Database Collections

```python
# AI Configuration
collection: "ai_config"
document_id: "system_ai"
{
    "id": "system_ai",
    "provider": "google",
    "model": "gemini-2.0-flash",
    "use_emergent_key": True,
    "document_ai": {
        "enabled": True,
        "project_id": "your-gcp-project-id",
        "processor_id": "your-processor-id",
        "location": "us"
    }
}

# Company Configuration
collection: "companies"
{
    "id": "company-uuid",
    "name": "Company Name",
    "name_en": "Company Name EN",
    "name_vn": "Tên Công Ty",
    "google_drive_folder_id": "parent-folder-id",
    "apps_script_url": "https://script.google.com/..."
}

# Audit Reports
collection: "audit_reports"
{
    "id": "report-uuid",
    "ship_id": "ship-uuid",
    "audit_report_name": "ISM Annual Audit 2024",
    "audit_type": "ISM",
    "report_form": "07-23",
    "audit_report_no": "AR-2024-001",
    "audit_date": "2024-01-15",
    "issued_by": "DNV GL",
    "auditor_name": "John Smith",
    "status": "Valid",
    "note": "Annual audit completed",
    "audit_report_file_id": "gdrive-file-id",
    "audit_report_summary_file_id": "gdrive-summary-id",
    "created_at": "2024-01-20T10:00:00Z",
    "updated_at": "2024-01-20T10:00:00Z"
}
```

### 8.3 File Size Limits

```python
# Frontend limit
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB per file

# Backend processing
# No explicit limit, but Document AI has ~20MB limit per API call
# Large files (>15 pages) are automatically split into chunks
```

### 8.4 PDF Splitting Configuration

```python
# pdf_splitter.py
MAX_PAGES_PER_CHUNK = 12  # Pages per chunk
SPLIT_THRESHOLD = 15      # Split if more than this

# Processing logic
if total_pages <= 15:
    # Single file processing
    process_whole_file()
else:
    # Split into chunks of 12 pages each
    chunks = split_pdf(file_content, max_pages=12)
    for chunk in chunks:
        process_chunk(chunk)
    merge_results(chunks)
```

---

## 9. COMPARISON WITH APPROVAL DOCUMENT

### Similarities:
- ✅ Same overall workflow (analyze → create → upload)
- ✅ Same Document AI integration
- ✅ Same PDF splitting logic (max 12 pages/chunk)
- ✅ Same GDrive upload pattern
- ✅ Same ship validation
- ✅ Same background upload approach

### Differences:

| Aspect | Audit Report | Approval Document |
|--------|--------------|-------------------|
| **GDrive Path** | `ShipName/ISM-ISPS-MLC/Audit Report/` | `ShipName/ISM - ISPS - MLC/Approval Document/` |
| **Folder Name** | `ISM-ISPS-MLC` (hyphens) | `ISM - ISPS - MLC` (spaces) |
| **Additional Fields** | `auditor_name`, `report_form` | `approved_by`, `approved_date` |
| **OCR Enhancement** | ✅ Targeted OCR for header/footer | ✅ Targeted OCR for header/footer |
| **Direct PDF Extraction** | ✅ Priority method | ✅ Priority method |
| **Field Extraction** | Filename → report_form → name → AI | Filename → report_form → name → AI |

---

## 10. SUMMARY & KEY TAKEAWAYS

### ✅ Complete Flow Summary:

1. **File Upload** → Frontend validates PDF format and size (max 50MB)
2. **AI Analysis** → Backend calls `/analyze-file` endpoint
3. **Page Count Check** → If >15 pages, split into 12-page chunks
4. **Document AI** → Extract text from PDF (each chunk separately if split)
5. **OCR Enhancement** → Extract header/footer text for better accuracy
6. **Field Extraction** → Use System AI (Gemini) to extract structured fields
7. **Ship Validation** → Verify extracted ship name/IMO matches selected ship
8. **Auto-fill Form** → Frontend populates form fields
9. **User Review** → User can edit fields before submit
10. **Create DB Record** → Save audit report to database
11. **Background Upload** → Upload original file + summary to GDrive
12. **Update DB** → Store GDrive file IDs in database

### 🔑 Key Functions:

- `analyze_audit_report_file()` - Main analysis endpoint
- `upload_audit_report_files()` - Upload to GDrive
- `analyze_audit_report_only()` - Document AI analysis (no upload)
- `extract_audit_report_fields_from_pdf_directly()` - Direct PDF extraction
- `extract_audit_report_fields_from_summary()` - Summary-based extraction
- `upload_audit_report_file()` - Upload original file
- `upload_audit_report_summary()` - Upload summary file

### 📦 Key Dependencies:

- `PyPDF2` - PDF page counting and splitting
- `pdf_splitter.py` - PDF chunking utility
- `dual_apps_script_manager.py` - GDrive integration
- `targeted_ocr.py` - OCR enhancement
- `emergentintegrations` - Gemini AI integration
- Google Document AI - Text extraction

### 🎯 Critical Path:

```
User → Upload PDF → Analyze → Extract Fields → Validate Ship → 
Auto-fill Form → User Edit → Submit → Create DB → Upload GDrive → Done
```

### 🔄 Batch Processing:

- Frontend detects multiple files
- Calls `onStartBatchProcessing(fileArray)`
- Parent component processes each file sequentially
- Each file follows the same single-file flow

---

## END OF DOCUMENT

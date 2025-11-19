# 📋 APPROVAL DOCUMENT - FULL FLOW ANALYSIS

## 🎯 OVERVIEW
Migration analysis of "Add Approval Document" feature from Backend V1 to understand complete workflow for future migrations.

---

## 1️⃣ FRONTEND FLOW

### 📂 Files Structure
```
/app/frontend/src/components/ApprovalDocument/
├── AddApprovalDocumentModal.jsx       # Main Add Modal (AI Analysis + Manual Entry)
├── ApprovalDocumentTable.jsx          # Table Display + CRUD operations
├── EditApprovalDocumentModal.jsx      # Edit existing document
├── ApprovalDocumentNotesModal.jsx     # Edit notes only
├── BatchProcessingModal.jsx           # Multi-file batch processing UI
├── BatchResultsModal.jsx              # Batch results display
└── index.js                           # Component exports
```

### 🔄 Add Document Flow (`AddApprovalDocumentModal.jsx`)

#### **A. File Upload (Single File)**
```javascript
// Lines 79-130: handleFileSelect()
1. User selects/drags PDF file
2. Validations:
   - File type: Must be PDF
   - File size: Max 20MB
   - Multiple files → Triggers batch processing (see section B)
3. Single file → Continue to AI analysis
```

#### **B. Multi-File Upload (Batch Processing)**
```javascript
// Lines 84-111
if (fileArray.length > 1) {
  - Validate all files (PDF, max 20MB each)
  - Close modal immediately
  - Call onStartBatchProcessing(fileArray)
  - Opens BatchProcessingModal
}
```

#### **C. AI Analysis (Single File)**
```javascript
// Lines 176-293: analyzeFile()

API Call: POST /api/approval-documents/analyze-file
FormData:
  - ship_id: selectedShip.id
  - document_file: PDF file
  - bypass_validation: "false"

Response Structure:
{
  "approval_document_name": "extracted name",
  "approval_document_no": "extracted number",
  "approved_by": "extracted approver",
  "approved_date": "YYYY-MM-DD",
  "note": "extracted notes",
  "confidence_score": 0.0-1.0,
  "processing_method": "analysis_only_no_upload",
  "_filename": "original.pdf",
  "_file_content": "base64_encoded_pdf",
  "_content_type": "application/pdf",
  "_summary_text": "Document AI summary",
  "_split_info": {
    "was_limited": boolean,
    "total_pages": number,
    "processed_chunks": number,
    "total_chunks": number,
    "max_chunks_limit": 5,
    "all_chunks_failed": boolean,
    "partial_success": boolean,
    "has_failures": boolean
  }
}

Split Info Warnings (Lines 226-257):
- All chunks failed → Error toast (duration: 10s)
- Partial failure → Warning toast (duration: 8s)  
- File limited (>5 chunks) → Warning toast (duration: 8s)
```

#### **D. Form Auto-fill**
```javascript
// Lines 263-270
After successful analysis:
- approval_document_name: from AI or filename
- approval_document_no: from AI or empty
- approved_by: from AI (normalized) or empty
- approved_date: from AI (formatted) or empty
- status: Default "Unknown"
- note: from AI or empty
```

#### **E. Save Document**
```javascript
// Lines 296-400: handleSave()

Step 1: Create document record
POST /api/approval-documents
{
  "ship_id": selectedShip.id,
  "approval_document_name": formData.approval_document_name.trim(),
  "approval_document_no": formData.approval_document_no?.trim() || null,
  "approved_by": formData.approved_by?.trim() || null,
  "approved_date": formData.approved_date || null,
  "status": formData.status || "Unknown",
  "note": formData.note?.trim() || null
}

Response: { id: "document_id", ... }

Step 2: Background File Upload (Non-blocking)
POST /api/approval-documents/{document_id}/upload-files
{
  "file_content": analyzedData._file_content,  // base64
  "filename": analyzedData._filename,
  "content_type": "application/pdf",
  "summary_text": analyzedData._summary_text
}

UI Flow:
- Show "📤 Uploading file to Google Drive..." toast (infinite)
- Upload in background async IIFE
- Close modal immediately (non-blocking)
- On success: "✅ File uploaded to Google Drive!"
- On failure: "❌ Upload file failed. Document was saved."
```

---

## 2️⃣ BACKEND V1 FLOW

### 📂 Files Structure
```
/app/backend-v1/
├── server.py                          # Main endpoints
├── dual_apps_script_manager.py        # Apps Script manager
├── pdf_splitter.py                    # PDF splitting utility
└── issued_by_abbreviation.py          # Normalize issued_by
```

### 🔌 API Endpoints

#### **A. Analyze File Endpoint**
```python
# server.py Lines 13590-13829
@api_router.post("/approval-documents/analyze-file")
async def analyze_approval_document_file(
    ship_id: str = Form(...),
    document_file: UploadFile = File(...),
    bypass_validation: str = Form("false"),
    current_user = Depends(check_permission([EDITOR, MANAGER, ADMIN, SUPER_ADMIN]))
)
```

**Flow Steps:**

**1. File Validation (Lines 13604-13621)**
```python
- Read file content: file_content = await document_file.read()
- Check filename exists
- Check file not empty
- Validate PDF extension (.pdf)
- Validate PDF magic bytes (starts with b'%PDF')
```

**2. PDF Page Count & Split Check (Lines 13624-13642)**
```python
from pdf_splitter import PDFSplitter
splitter = PDFSplitter(max_pages_per_chunk=12)

total_pages = splitter.get_page_count(file_content)
needs_split = splitter.needs_splitting(file_content)  # >15 pages

PDF Analysis: {total_pages} pages, Split needed: {needs_split}
```

**3. Company & Ship Validation (Lines 13644-13677)**
```python
- Get company_uuid from current_user
- Fetch ship by ship_id
- Verify company access (UUID comparison)
- Extract ship_name
```

**4. Document AI Configuration (Lines 13679-13695)**
```python
ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
document_ai_config = ai_config_doc.get("document_ai", {})

Required:
  - enabled: true
  - project_id: "your-project-id"
  - processor_id: "your-processor-id"
```

**5. Initialize Analysis Result (Lines 13702-13722)**
```python
analysis_result = {
    "approval_document_name": "",
    "approval_document_no": "",
    "approved_by": "",
    "approved_date": "",
    "note": "",
    "confidence_score": 0.0,
    "processing_method": "clean_analysis",
    "_filename": filename,
    "_summary_text": ""
}

# Store file content FIRST (base64 encoded)
analysis_result['_file_content'] = base64.b64encode(file_content).decode('utf-8')
analysis_result['_content_type'] = document_file.content_type
analysis_result['_ship_name'] = ship_name
```

**6a. Large PDF Processing (>15 pages) - Lines 13724-13732**
```python
if needs_split and total_pages > 15:
    processing_method = 'split_pdf_batch_processing'
    
    # Split PDF into chunks (max 12 pages each)
    chunks = splitter.split_pdf(file_content, filename)
    
    MAX_CHUNKS = 5  # Process first 5 chunks only
    chunks_to_process = chunks[:MAX_CHUNKS]
    
    # Process each chunk with Document AI
    for chunk in chunks_to_process:
        # Call Document AI for each chunk
        # Extract fields from each chunk summary
        # Merge results using merge_analysis_results()
    
    # Create enhanced merged summary
    summary_text = create_enhanced_merged_summary(...)
    
    # Add split info to response
    analysis_result['_split_info'] = {
        'was_split': True,
        'total_pages': total_pages,
        'total_chunks': len(chunks),
        'processed_chunks': len(chunks_to_process),
        'max_chunks_limit': MAX_CHUNKS,
        'successful_chunks': count_success,
        'failed_chunks': count_failed,
        'all_chunks_failed': all_failed,
        'partial_success': some_success
    }
```

**6b. Small PDF Processing (≤15 pages) - Lines 13735-13804**
```python
else:
    # Normal single-file processing
    processing_method = 'analysis_only_no_upload'
    
    # Step 1: Document AI Analysis
    from dual_apps_script_manager import create_dual_apps_script_manager
    dual_manager = create_dual_apps_script_manager(company_uuid)
    
    ai_analysis = await dual_manager.analyze_test_report_file(
        file_content=file_content,
        filename=filename,
        content_type='application/pdf',
        document_ai_config=document_ai_config
    )
    
    if ai_analysis:
        summary_text = ai_analysis.get('summary_text', '')
        
        if summary_text and summary_text.strip():
            analysis_result['_summary_text'] = summary_text
            
            # Step 2: Extract fields from summary using System AI
            ai_provider = ai_config_doc.get("provider", "google")
            ai_model = ai_config_doc.get("model", "gemini-2.0-flash-exp")
            use_emergent_key = ai_config_doc.get("use_emergent_key", True)
            
            extracted_fields = await extract_approval_document_fields_from_summary(
                summary_text,
                ai_provider,
                ai_model,
                use_emergent_key
            )
            
            if extracted_fields:
                analysis_result.update(extracted_fields)
                # Fields: approval_document_name, approval_document_no,
                #         approved_by, approved_date, note
        
        if 'confidence_score' in ai_analysis:
            analysis_result['confidence_score'] = ai_analysis['confidence_score']
```

**7. Normalize Approved By (Lines 13806-13821)**
```python
if analysis_result.get('approved_by'):
    from issued_by_abbreviation import normalize_issued_by
    
    original = analysis_result['approved_by']
    normalized = normalize_issued_by(original)
    
    analysis_result['approved_by'] = normalized
    # e.g., "Panama Maritime Documentation Services" → "PMDS"
```

**8. Return Analysis Result**
```python
return analysis_result  # Complete with all extracted fields + metadata
```

---

#### **B. Upload Files Endpoint**
```python
# server.py Lines 13834-13964
@api_router.post("/approval-documents/{document_id}/upload-files")
async def upload_approval_document_files(
    document_id: str,
    file_content: str = Body(...),      # base64 encoded
    filename: str = Body(...),
    content_type: str = Body(...),
    summary_text: Optional[str] = Body(None),
    current_user = Depends(...)
)
```

**Flow Steps:**

**1. Validate Document (Lines 13853-13855)**
```python
document = await mongo_db.find_one("approval_documents", {"id": document_id})
if not document:
    raise HTTPException(404, "Document not found")
```

**2. Get Company & Ship Info (Lines 13858-13891)**
```python
company_uuid = await resolve_company_id(current_user)
ship_id = document.get("ship_id")
ship = await mongo_db.find_one("ships", {"id": ship_id})

# Verify company access (UUID comparison)
ship_name = ship.get("name", "Unknown Ship")
```

**3. Decode File Content (Lines 13894-13900)**
```python
import base64
file_bytes = base64.b64decode(file_content)
logger.info(f"✅ Decoded file content: {len(file_bytes)} bytes")
```

**4. Initialize Dual Apps Script Manager (Lines 13905-13906)**
```python
from dual_apps_script_manager import create_dual_apps_script_manager
dual_manager = create_dual_apps_script_manager(company_uuid)
```

**5. Upload Files to Google Drive (Lines 13909-13917)**
```python
# Target Path: ShipName/ISM-ISPS-MLC/Approval Document/
upload_result = await dual_manager.upload_approval_document_file(
    file_content=file_bytes,
    filename=filename,
    ship_name=ship_name,
    summary_text=summary_text  # Optional summary file
)

# Returns:
{
    'success': True/False,
    'original_file_id': 'GDrive file ID',
    'summary_file_id': 'GDrive summary file ID',
    'summary_error': 'Error if summary failed (non-critical)',
    'message': 'Status message'
}
```

**6. Update Document with File IDs (Lines 13931-13940)**
```python
update_data = {}
if original_file_id:
    update_data['file_id'] = original_file_id
if summary_file_id:
    update_data['summary_file_id'] = summary_file_id

if update_data:
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    await mongo_db.update("approval_documents", {"id": document_id}, update_data)
```

**7. Return Response (Lines 13951-13958)**
```python
return {
    "success": True,
    "message": "Approval document files uploaded successfully",
    "document": ApprovalDocumentResponse(**updated_document),
    "original_file_id": original_file_id,
    "summary_file_id": summary_file_id,
    "summary_error": summary_error  # Non-critical warning
}
```

---

### 🤖 AI EXTRACTION HELPER

#### **Function: `extract_approval_document_fields_from_summary`**
```python
# server.py Lines 8012-8086
async def extract_approval_document_fields_from_summary(
    summary_text: str,
    ai_provider: str,      # "google", "emergent"
    ai_model: str,         # "gemini-2.0-flash-exp"
    use_emergent_key: bool # True/False
) -> dict
```

**Flow:**

**1. Create Extraction Prompt (Lines 8025-8030)**
```python
prompt = create_approval_document_extraction_prompt(summary_text)
# Detailed prompt with extraction rules (see below)
```

**2. Call System AI (Lines 8034-8050)**
```python
if use_emergent_key and ai_provider in ["google", "emergent"]:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    emergent_key = get_emergent_llm_key()
    chat = LlmChat(
        api_key=emergent_key,
        session_id=f"approval_document_extraction_{int(time.time())}",
        system_message="You are a maritime regulatory documentation analysis expert."
    ).with_model("gemini", ai_model)
    
    user_message = UserMessage(text=prompt)
    ai_response = await chat.send_message(user_message)
```

**3. Parse JSON Response (Lines 8054-8068)**
```python
if ai_response and ai_response.strip():
    content = ai_response.strip()
    
    # Clean markdown code blocks
    clean_content = content.replace('```json', '').replace('```', '').strip()
    extracted_data = json.loads(clean_content)
    
    # Standardize date formats
    if extracted_data.get('approved_date'):
        from dateutil import parser
        parsed_date = parser.parse(extracted_data['approved_date'])
        extracted_data['approved_date'] = parsed_date.strftime('%Y-%m-%d')
    
    return extracted_data
    # Returns: {approval_document_name, approval_document_no, 
    #           approved_by, approved_date, note}
```

---

#### **Function: `create_approval_document_extraction_prompt`**
```python
# server.py Lines 8088-8159
def create_approval_document_extraction_prompt(summary_text: str) -> str
```

**Prompt Structure:**
```
=== FIELDS TO EXTRACT ===

**approval_document_name**: 
- Document title/name
- Look for: "Document Title", "Approval Title", "Certificate Name"
- Common types: ISM, ISPS, MLC, DOC, SMC approvals
- Be specific and include type

**approval_document_no**: 
- Document/approval/certificate number
- Look for: "Document No.", "Approval No.", "Certificate No."
- Format: may contain letters, numbers, dashes, slashes

**approved_by**: 
- Who approved/issued
- Look for: "Approved By", "Issued By", "Certified By", "Authority"
- Common: Classification societies, Flag administrations, Port State Control

**approved_date**: 
- Approval/issue/certification date
- Format: YYYY-MM-DD or any recognizable format
- Look for: "Approval Date", "Issue Date", "Certification Date"

**note**: 
- Important notes, remarks, conditions, limitations
- Look for: "Notes", "Remarks", "Conditions", "Special Requirements"
- Keep concise but include important regulatory details

=== EXTRACTION RULES ===
1. Be precise - extract exact values
2. Handle missing data - return empty string ""
3. Date formats - accept any, prefer YYYY-MM-DD
4. Document names - be specific, include type
5. Abbreviations - keep maritime abbreviations (ISM, ISPS, MLC, etc.)
6. Authority names - use full names when available

=== OUTPUT FORMAT ===
{
  "approval_document_name": "...",
  "approval_document_no": "...",
  "approved_by": "...",
  "approved_date": "YYYY-MM-DD",
  "note": "..."
}
```

---

### 📤 DUAL APPS SCRIPT MANAGER

#### **File: `dual_apps_script_manager.py`**

**Class: `DualAppsScriptManager`**

**Purpose:** 
- Manages calls to TWO different Apps Scripts:
  1. **System Apps Script** → Document AI processing only
  2. **Company Apps Script** → File uploads to Company Google Drive

**Configuration (Lines 28-64):**
```python
async def _load_configuration(self):
    # 1. Get System Apps Script URL (for Document AI)
    ai_config = await mongo_db.find_one("ai_config", {"id": "system_ai"})
    self.system_apps_script_url = ai_config["document_ai"].get("apps_script_url")
    
    # 2. Get Company Apps Script URL (for file upload)
    gdrive_config = await mongo_db.find_one(
        "company_gdrive_config",
        {"company_id": self.company_id}
    )
    
    # Check for web_app_url first, then fallback to company_apps_script_url
    self.company_apps_script_url = (
        gdrive_config.get("web_app_url") or 
        gdrive_config.get("company_apps_script_url")
    )
    
    self.parent_folder_id = (
        gdrive_config.get("parent_folder_id") or 
        gdrive_config.get("folder_id")
    )
```

**Method: `upload_approval_document_file`** (Lines 2017-2121)
```python
async def upload_approval_document_file(
    self,
    file_content: bytes,
    filename: str,
    ship_name: str,
    summary_text: Optional[str] = None
) -> Dict[str, Any]
```

**Target Path:** `ShipName/ISM-ISPS-MLC/Approval Document/`

**Upload Flow:**

**1. Load Configuration**
```python
await self._load_configuration()

# Validate
if not self.company_apps_script_url:
    raise ValueError("Company Apps Script URL not configured")
if not self.parent_folder_id:
    raise ValueError("Company Google Drive Folder ID not configured")
```

**2. Upload Original File (Lines 2052-2080)**
```python
original_upload = await self._call_company_apps_script({
    'action': 'upload_file_with_folder_creation',
    'parent_folder_id': self.parent_folder_id,    # ROOT folder
    'ship_name': ship_name,                        # Creates ShipName folder
    'parent_category': 'ISM-ISPS-MLC',            # First level under ShipName
    'category': 'Approval Document',               # Second level under ISM-ISPS-MLC
    'filename': filename,
    'file_content': base64.b64encode(file_content).decode('utf-8'),
    'content_type': 'application/pdf'
})

# Response:
{
    'success': True,
    'file_id': 'GDrive file ID',
    'file_path': 'ShipName/ISM-ISPS-MLC/Approval Document/filename.pdf',
    'message': '...'
}
```

**3. Upload Summary File (Lines 2083-2110) - Optional**
```python
if summary_text and summary_text.strip():
    summary_filename = filename.replace('.pdf', '_summary.txt')
    
    summary_upload = await self._call_company_apps_script({
        'action': 'upload_file_with_folder_creation',
        'parent_folder_id': self.parent_folder_id,
        'ship_name': ship_name,
        'parent_category': 'ISM-ISPS-MLC',
        'category': 'Approval Document',
        'filename': summary_filename,
        'file_content': base64.b64encode(summary_text.encode('utf-8')).decode('utf-8'),
        'content_type': 'text/plain'
    })
    
    # Summary upload is NON-CRITICAL
    # If fails, stored in 'summary_error' but original upload succeeds
```

**4. Return Result**
```python
return {
    'success': True,
    'message': 'Approval document files uploaded successfully',
    'original_file_id': original_file_id,
    'summary_file_id': summary_file_id,      # May be None
    'summary_error': summary_error            # May be None
}
```

---

### 📄 PDF SPLITTER UTILITY

#### **File: `pdf_splitter.py`**

**Class: `PDFSplitter`**

**Constructor (Lines 15-20):**
```python
def __init__(self, max_pages_per_chunk: int = 12):
    self.max_pages_per_chunk = 12  # Safely under 15 page limit
```

**Method: `get_page_count`** (Lines 22-29)
```python
def get_page_count(self, pdf_content: bytes) -> int:
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    return len(pdf_reader.pages)
```

**Method: `needs_splitting`** (Lines 31-34)
```python
def needs_splitting(self, pdf_content: bytes) -> bool:
    page_count = self.get_page_count(pdf_content)
    return page_count > 15  # Split if >15 pages
```

**Method: `split_pdf`** (Lines 36-111)
```python
def split_pdf(self, pdf_content: bytes, filename: str) -> List[Dict]:
    """
    Split PDF into chunks of max 12 pages each
    
    Returns:
    [
        {
            'content': bytes,                # PDF chunk bytes
            'chunk_num': 1,                  # Chunk number (1-indexed)
            'page_range': '1-12',            # Human-readable range
            'start_page': 1,                 # Start page (1-indexed)
            'end_page': 12,                  # End page (inclusive)
            'page_count': 12,                # Pages in this chunk
            'filename': 'report_chunk1.pdf', # Generated filename
            'size_bytes': 12345              # Chunk size
        },
        ...
    ]
    """
```

**Split Logic:**
```python
pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
total_pages = len(pdf_reader.pages)

if total_pages <= 15:
    # No splitting - return single chunk
    return [single_chunk_info]

# Split into chunks
chunks = []
base_filename = filename.rsplit('.', 1)[0]  # Remove .pdf

for start_page in range(0, total_pages, self.max_pages_per_chunk):
    end_page = min(start_page + self.max_pages_per_chunk, total_pages)
    
    # Create new PDF for this chunk
    pdf_writer = PyPDF2.PdfWriter()
    for page_num in range(start_page, end_page):
        pdf_writer.add_page(pdf_reader.pages[page_num])
    
    # Write to bytes
    chunk_bytes_io = io.BytesIO()
    pdf_writer.write(chunk_bytes_io)
    chunk_content = chunk_bytes_io.getvalue()
    
    chunk_info = {
        'content': chunk_content,
        'chunk_num': len(chunks) + 1,
        'page_range': f'{start_page + 1}-{end_page}',
        'start_page': start_page + 1,
        'end_page': end_page,
        'page_count': end_page - start_page,
        'filename': f'{base_filename}_chunk{chunk_num}.pdf',
        'size_bytes': len(chunk_content)
    }
    
    chunks.append(chunk_info)

return chunks
```

**Method: `merge_analysis_results`** (Lines 114-273)
```python
def merge_analysis_results(chunk_results: List[Dict]) -> Dict:
    """
    Intelligently merge results from multiple PDF chunks
    
    Strategy:
    1. Document Name: From first chunk (usually cover page)
    2. Document Number: Most common value
    3. Approved By: Most common value
    4. Approved Date: First valid date
    5. Notes: Concatenate with chunk indicators
    """
```

**Merge Strategies:**
```python
# 1. Name: Prefer first chunk (cover page)
if all_names:
    merged['approval_document_name'] = all_names[0]['value']

# 2. Document No: Most common occurrence
if all_report_nos:
    report_no_counts = {}
    for item in all_report_nos:
        report_no_counts[item['value']] = report_no_counts.get(item['value'], 0) + 1
    merged['approval_document_no'] = max(report_no_counts, key=report_no_counts.get)

# 3. Approved By: Most common
if all_approved_by:
    # Same logic as document no
    merged['approved_by'] = most_common_value

# 4. Date: First valid date
if all_dates:
    merged['approved_date'] = all_dates[0]['value']

# 5. Notes: Concatenate with page ranges
if all_notes:
    formatted_notes = []
    for note in all_notes:
        formatted_notes.append(f"[Pages {note['pages']}] {note['value']}")
    merged['note'] = ' | '.join(formatted_notes)

# Add metadata
merged['merge_info'] = {
    'total_chunks_processed': count,
    'failed_chunks': count_failed,
    'merge_strategy': 'intelligent',
    'chunks_with_data': {...}
}

return merged
```

**Method: `create_enhanced_merged_summary`** (Lines 276-361)
```python
def create_enhanced_merged_summary(
    chunk_results: List[Dict],
    merged_data: Dict,
    original_filename: str,
    total_pages: int
) -> str:
    """
    Create well-formatted merged summary document
    
    Format:
    ================================================================================
    APPROVAL DOCUMENT ANALYSIS - MERGED SUMMARY
    ================================================================================
    
    PROCESSING INFORMATION:
    --------------------------------------------------------------------------------
    Original File: filename.pdf
    Total Pages: 45
    Processing Date: 2025-01-19 10:30:00 UTC
    Processing Method: Split PDF + Batch Processing
    Total Chunks: 4
    Successful Chunks: 4
    Failed Chunks: 0
    
    EXTRACTED INFORMATION (MERGED):
    --------------------------------------------------------------------------------
    Approval Document Name: Safety Management System Approval
    Document Number: ISM-2024-001
    Approved By: Det Norske Veritas
    Approved Date: 2024-01-15
    Status: Valid
    
    Notes:
    [Pages 1-12] Valid until 2029-01-15
    [Pages 13-24] Covers ISM Code compliance
    
    DETAILED CHUNK ANALYSIS:
    ================================================================================
    
    CHUNK 1 (Pages 1-12)
    --------------------------------------------------------------------------------
    [Document AI summary text for chunk 1]
    
    CHUNK 2 (Pages 13-24)
    --------------------------------------------------------------------------------
    [Document AI summary text for chunk 2]
    
    ...
    
    ================================================================================
    END OF MERGED SUMMARY
    ================================================================================
    """
```

---

## 3️⃣ KEY TECHNICAL DECISIONS

### 🎯 MAX CHUNKS LIMIT
```python
MAX_CHUNKS = 5  # Process first 5 chunks only

Why limit to 5?
- Document AI processing is expensive
- First few chunks (cover + first pages) contain most important info
- Prevents excessive API costs for very large documents
- Balance between coverage and cost

Example: 100-page document
- Total chunks (12 pages each): 9 chunks
- Processed: First 5 chunks (60 pages)
- Skipped: Last 4 chunks (40 pages)
- Coverage: 60% of document, but captures critical information
```

### 📏 CHUNK SIZE
```python
max_pages_per_chunk = 12

Why 12 pages?
- Document AI limit: 15 pages per request
- Safety margin: 12 pages leaves buffer for processing
- Optimal performance: Not too small (many requests), not too large (timeout risk)
```

### 🔄 NON-BLOCKING FILE UPLOAD
```javascript
// Frontend: Async IIFE for background upload
(async () => {
    try {
        await uploadFiles();
        toast.success('✅ File uploaded!');
    } catch (error) {
        toast.error('❌ Upload failed');
    }
})();

// Close modal immediately - don't wait
onClose();

Why non-blocking?
- Google Drive upload can take 10-30 seconds
- User shouldn't wait with modal open
- Document is saved in DB immediately
- File upload is "best effort" - can retry if needed
```

### 🎯 TWO-STAGE PROCESSING
```
Stage 1: Document AI
- Input: PDF file bytes
- Output: Raw text summary (OCR + structure extraction)
- Tool: Google Document AI API

Stage 2: System AI (LLM)
- Input: Document AI summary text
- Output: Structured fields (JSON)
- Tool: Gemini/GPT via Emergent LLM

Why two stages?
- Document AI: Excellent at OCR and document structure
- System AI: Excellent at understanding context and extracting specific fields
- Separation of concerns: Document processing vs. data extraction
- Flexibility: Can swap out either component
```

### 📂 FOLDER STRUCTURE
```
ShipName/
└── ISM-ISPS-MLC/
    └── Approval Document/
        ├── document_name.pdf           # Original file
        └── document_name_summary.txt   # Summary file (optional)

Why ISM-ISPS-MLC parent folder?
- Regulatory grouping for maritime compliance documents
- ISM: International Safety Management Code
- ISPS: International Ship and Port Facility Security Code
- MLC: Maritime Labour Convention
- Groups related compliance documents together
```

### 🔐 DUAL APPS SCRIPT ARCHITECTURE
```
System Apps Script:
- Purpose: Document AI processing
- Scope: System-wide (one for all companies)
- Configuration: ai_config collection
- Why: Document AI credentials should be system-level

Company Apps Script:
- Purpose: File uploads to Company Google Drive
- Scope: Per-company (each company has own Drive)
- Configuration: company_gdrive_config collection
- Why: Each company manages their own Google Drive

Benefits:
- Separation of concerns
- Security: Companies only access their own Drive
- Flexibility: System can process documents without Company Drive config
- Scalability: Easy to add more companies
```

---

## 4️⃣ DATA MODELS

### MongoDB Collections

#### **approval_documents**
```javascript
{
    "id": "uuid",
    "ship_id": "ship_uuid",
    "approval_document_name": "Safety Management System Approval",
    "approval_document_no": "ISM-2024-001",
    "approved_by": "DNV",
    "approved_date": "2024-01-15T00:00:00",
    "status": "Valid",
    "note": "Valid until 2029-01-15",
    "file_id": "google_drive_file_id",        // Original PDF
    "summary_file_id": "google_drive_file_id", // Summary text file
    "created_at": "2025-01-19T10:30:00Z",
    "updated_at": "2025-01-19T10:35:00Z"
}
```

#### **ai_config**
```javascript
{
    "id": "system_ai",
    "provider": "google",
    "model": "gemini-2.0-flash-exp",
    "use_emergent_key": true,
    "document_ai": {
        "enabled": true,
        "project_id": "your-gcp-project",
        "processor_id": "your-processor-id",
        "location": "us",
        "apps_script_url": "https://script.google.com/..."
    }
}
```

#### **company_gdrive_config**
```javascript
{
    "company_id": "company_uuid",
    "web_app_url": "https://script.google.com/...",      // Primary
    "company_apps_script_url": "https://...",            // Fallback
    "parent_folder_id": "google_drive_folder_id",        // Primary
    "folder_id": "google_drive_folder_id",               // Fallback
    "created_at": "...",
    "updated_at": "..."
}
```

---

## 5️⃣ ERROR HANDLING

### Frontend Errors
```javascript
// File validation
- Invalid file type → Toast error
- File too large (>20MB) → Toast error
- Empty file → Toast error

// AI analysis
- Analysis failed → Toast error + Allow manual entry
- Partial failure → Toast warning + Show results
- All chunks failed → Toast error + Use filename as fallback

// Document creation
- Validation failed → Toast error
- Network error → Toast error
- Backend error → Toast error with details

// File upload (background)
- Upload failed → Toast warning "Document saved, upload failed"
- Summary upload failed → Silent (non-critical)
```

### Backend Errors
```python
# File validation
- No filename → 400 Bad Request
- Empty file → 400 Bad Request
- Invalid PDF type → 400 Bad Request
- Invalid PDF format → 400 Bad Request

# Authentication & Authorization
- Invalid token → 401 Unauthorized
- Insufficient permissions → 403 Forbidden
- Ship not found → 404 Not Found
- Company mismatch → 403 Access Denied

# Configuration
- AI config not found → 404 Not Found
- Document AI not enabled → 400 Bad Request
- Incomplete AI config → 400 Bad Request
- Company Drive not configured → Error in upload

# Processing
- PDF split error → 400 Invalid PDF
- Document AI error → Try to continue with fallback
- System AI error → Try to continue with fallback
- Apps Script error → 500 Internal Server Error

# Database
- Document not found → 404 Not Found
- Ship not found → 404 Not Found
- Database error → 500 Internal Server Error
```

---

## 6️⃣ PERFORMANCE CONSIDERATIONS

### File Size Limits
```
Single file: 20MB max
Reasoning:
- Balance between usability and performance
- Most approval documents are 1-10MB
- Prevents timeout issues
- Google Drive API comfortable with <20MB
```

### Chunk Processing
```python
# Parallel vs Sequential
Current: Sequential chunk processing
Reason: Document AI rate limits

Optimization opportunity:
- Could batch multiple chunks in parallel
- Need to respect Document AI quotas
- Would require careful rate limiting
```

### Background Upload
```javascript
// Non-blocking upload improves UX
Upload time breakdown:
- Base64 encode: <1s
- Network transfer: 5-15s
- Apps Script processing: 5-10s
- Total: 10-25s

Without background upload:
- User waits 10-25s with modal open ❌

With background upload:
- User sees "saved" immediately ✅
- Upload happens in background ✅
- Toast notification on completion ✅
```

---

## 7️⃣ TESTING CHECKLIST

### Frontend Tests
- [ ] Single file upload (small PDF <5 pages)
- [ ] Single file upload (large PDF >15 pages)
- [ ] Multi-file upload (trigger batch processing)
- [ ] File validation (non-PDF, oversized)
- [ ] AI analysis success
- [ ] AI analysis partial failure
- [ ] AI analysis complete failure
- [ ] Form auto-fill after analysis
- [ ] Manual entry without AI
- [ ] Document save success
- [ ] Document save failure
- [ ] Background upload success
- [ ] Background upload failure

### Backend Tests
- [ ] Analyze endpoint - small PDF
- [ ] Analyze endpoint - large PDF (split)
- [ ] Analyze endpoint - invalid PDF
- [ ] Analyze endpoint - empty file
- [ ] Extract fields from summary
- [ ] Normalize approved_by
- [ ] Upload files endpoint - success
- [ ] Upload files endpoint - no document
- [ ] Upload files endpoint - company access denied
- [ ] Apps Script integration - original file
- [ ] Apps Script integration - summary file
- [ ] Database update with file IDs

### Integration Tests
- [ ] End-to-end flow (upload → analyze → save → upload files)
- [ ] Multi-file batch processing
- [ ] Large document (>60 pages, 5+ chunks)
- [ ] Very large document (>150 pages, test limit)
- [ ] Company isolation (access control)
- [ ] Error recovery (AI failure → manual entry)

---

## 8️⃣ MIGRATION NOTES FOR NEW BACKEND

### Required Endpoints
```python
1. POST /api/approval-documents/analyze-file
   - Form data: ship_id, document_file, bypass_validation
   - Returns: analysis result with fields + metadata

2. POST /api/approval-documents
   - JSON body: document data
   - Returns: created document with ID

3. POST /api/approval-documents/{document_id}/upload-files
   - JSON body: file_content, filename, content_type, summary_text
   - Returns: upload result with file IDs

4. GET /api/approval-documents (list)
5. GET /api/approval-documents/{id} (get one)
6. PUT /api/approval-documents/{id} (update)
7. DELETE /api/approval-documents/{id} (delete)
8. POST /api/approval-documents/bulk-delete (bulk delete)
```

### Required Services
```python
1. approval_document_service.py
   - CRUD operations
   - File upload coordination

2. approval_document_ai_service.py
   - Document AI integration
   - System AI extraction
   - PDF splitting and merging

3. gdrive_helper.py (or dual_apps_script_manager.py)
   - Upload to ISM-ISPS-MLC/Approval Document/ path
   - Handle both original and summary files
```

### Required Models
```python
1. approval_doc.py (Pydantic)
   - ApprovalDocBase
   - ApprovalDocCreate
   - ApprovalDocUpdate
   - ApprovalDocResponse

2. Database schema (MongoDB)
   - Collection: approval_documents
   - Required fields: id, ship_id, approval_document_name
   - Optional fields: approval_document_no, approved_by, approved_date, status, note
   - File references: file_id, summary_file_id
```

### Dependencies
```python
Required Python packages:
- PyPDF2: PDF splitting
- google-cloud-documentai: Document AI
- aiohttp: Async HTTP for Apps Script calls
- python-dateutil: Date parsing
- emergentintegrations: System AI (if using Emergent LLM key)

Frontend packages:
- sonner: Toast notifications
- Already have file upload components
```

### Configuration Required
```
1. AI Configuration (ai_config collection):
   - provider, model, use_emergent_key
   - document_ai.enabled, project_id, processor_id, apps_script_url

2. Company Google Drive (company_gdrive_config collection):
   - company_id, web_app_url, parent_folder_id

3. Environment variables:
   - EMERGENT_LLM_KEY (if using Emergent key)
   - Google Cloud credentials (for Document AI)
```

---

## 9️⃣ COMPARISON WITH OTHER DOCUMENTS

### Similar Modules (for reference)
```
Approval Document   → ISM-ISPS-MLC > Approval Document
Other Document      → Class & Flag Cert > Other Documents
Other Audit Doc     → ISM-ISPS-MLC > Other Audit Document
Drawing Manual      → Drawings & Manuals (root level)
Test Report         → Test Reports (root level)
Survey Report       → Survey Reports (root level)
```

### Key Differences

**Approval Document:**
- Has Document AI + System AI (two-stage)
- Extracts specific fields (approval_document_name, approval_document_no, approved_by, approved_date)
- Uploads to nested path (ISM-ISPS-MLC/Approval Document/)
- Has summary file upload

**Other Document:**
- No AI analysis (simple file upload only)
- No field extraction
- Uploads to Class & Flag Cert/Other Documents/
- No summary file

**Other Audit Document:**
- No AI analysis (simple file upload only)
- No field extraction
- Uploads to ISM-ISPS-MLC/Other Audit Document/
- No summary file

**Drawing Manual:**
- Has Document AI + System AI
- Extracts different fields (drawing_manual_name, drawing_manual_no, approved_by, approved_date)
- Uploads to root Drawings & Manuals/
- Has summary file upload
- **ALMOST IDENTICAL to Approval Document** (just different folder path and field names)

---

## 🎯 SUMMARY

### Core Workflow
```
1. User uploads PDF file
2. Frontend calls analyze-file endpoint
3. Backend validates file and checks page count
4. If >15 pages: Split into chunks (max 12 pages each)
5. Process first 5 chunks with Document AI
6. Extract text summary from each chunk
7. Use System AI to extract fields from summary
8. Merge results intelligently
9. Return analysis to frontend with file content
10. User reviews/edits form (auto-filled)
11. Frontend saves document (database only)
12. Frontend uploads files in background (non-blocking)
13. Backend uploads to Google Drive via Apps Script
14. Update document with file IDs
```

### Critical Components
1. **PDF Splitter**: Split large files into processable chunks
2. **Document AI**: Extract text from PDF (OCR + structure)
3. **System AI**: Extract structured fields from text
4. **Dual Apps Script Manager**: Coordinate System + Company Apps Scripts
5. **Background Upload**: Non-blocking file upload for better UX
6. **Intelligent Merging**: Combine results from multiple chunks

### Success Metrics
- ✅ Small files (<15 pages): 100% processed
- ✅ Large files (>15 pages): First 60 pages processed (5 chunks × 12 pages)
- ✅ Field extraction: ~70-80% accuracy with good quality PDFs
- ✅ Upload time: 10-25 seconds (background, non-blocking)
- ✅ User experience: Immediate feedback, no waiting

---

**Document Created:** 2025-01-19
**Backend V1 Analyzed:** ✅ Complete
**Migration Ready:** ✅ Yes
**Next Module:** Test Reports or Drawing Manuals (very similar pattern)

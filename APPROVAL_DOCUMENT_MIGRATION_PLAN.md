# 📋 APPROVAL DOCUMENT MIGRATION PLAN

## 🎯 OBJECTIVES
Migrate "Add Approval Document" module from Backend V1 to new FastAPI backend with following requirements:
1. ✅ Keep all logic from Backend V1
2. ✅ Reuse existing utilities/helpers in new backend
3. ✅ Apply improvements from "Drawings & Manuals" implementation
4. ✅ Increase file size limit to 50MB (from 20MB)

---

## 📊 CURRENT STATUS ANALYSIS

### ✅ Already Implemented in New Backend
```
/app/backend/app/api/v1/approval_documents.py
├── GET /approval-documents (list)
├── GET /approval-documents/{doc_id} (get one)
├── POST /approval-documents (create)
├── PUT /approval-documents/{doc_id} (update)
├── DELETE /approval-documents/{doc_id} (delete)
├── POST /approval-documents/bulk-delete (bulk delete)
├── POST /approval-documents/check-duplicate (check duplicate)
└── POST /approval-documents/analyze (stub - NOT IMPLEMENTED)

/app/backend/app/models/approval_document.py
├── ApprovalDocumentCreate
├── ApprovalDocumentUpdate
├── ApprovalDocumentResponse
└── BulkDeleteApprovalDocumentRequest

/app/backend/app/services/approval_document_service.py
├── get_approval_documents()
├── get_approval_document_by_id()
├── create_approval_document()
├── update_approval_document()
├── delete_approval_document() - NEEDS BACKGROUND GDRIVE CLEANUP
├── bulk_delete_approval_documents() - NEEDS BACKGROUND GDRIVE CLEANUP
└── check_duplicate()
```

### ✅ Reusable Utilities Already in New Backend
```
/app/backend/app/utils/
├── pdf_splitter.py              ✅ EXISTS (identical to V1)
├── gdrive_helper.py              ✅ EXISTS
├── gdrive_folder_helper.py       ✅ EXISTS
└── issued_by_abbreviation.py    ❓ CHECK IF EXISTS

/app/backend/app/services/
└── gdrive_service.py             ✅ EXISTS
```

### 🎯 Reference Implementation: Drawings & Manuals
```
/app/backend/app/api/v1/drawings_manuals.py
├── POST /drawings-manuals/analyze-file        ✅ REFERENCE
└── POST /drawings-manuals/{doc_id}/upload-files ✅ REFERENCE

/app/backend/app/services/
├── drawing_manual_analyze_service.py          ✅ REFERENCE
└── drawing_manual_service.py                  ✅ REFERENCE (upload_files, delete with background)

/app/backend/app/utils/
└── drawing_manual_ai.py                       ✅ REFERENCE
```

### ❌ Missing in New Backend
```
1. POST /approval-documents/analyze-file endpoint (currently stub)
2. POST /approval-documents/{doc_id}/upload-files endpoint
3. approval_document_analyze_service.py
4. approval_document_ai.py (AI extraction helpers)
5. Background GDrive deletion in delete endpoints
6. issued_by_abbreviation.py (if not exists)
```

---

## 📋 MIGRATION PLAN - DETAILED PHASES

### **PHASE 1: Preparation & Verification** (30 mins)

#### 1.1 Check Existing Utilities
```bash
# Check if issued_by_abbreviation.py exists
ls -la /app/backend/app/utils/issued_by_abbreviation.py

# Check gdrive_helper.py capabilities
grep -n "upload_approval_document" /app/backend/app/utils/gdrive_helper.py
grep -n "ISM-ISPS-MLC" /app/backend/app/utils/gdrive_helper.py
```

**Action Items:**
- [ ] Verify `issued_by_abbreviation.py` exists or needs migration
- [ ] Check `gdrive_helper.py` supports approval document path
- [ ] Review `pdf_splitter.py` to confirm identical to V1
- [ ] Verify `DrawingManualAnalyzeService` as reference template

#### 1.2 Update Frontend File Size Limit
```javascript
// File: /app/frontend/src/components/ApprovalDocument/AddApprovalDocumentModal.jsx
// Line ~124: Update from 20MB to 50MB

OLD:
if (file.size > 20 * 1024 * 1024) {
  toast.error(language === 'vi' ? 'File quá lớn (tối đa 20MB)' : 'File too large (max 20MB)');
  return;
}

NEW:
if (file.size > 50 * 1024 * 1024) {
  toast.error(language === 'vi' ? 'File quá lớn (tối đa 50MB)' : 'File too large (max 50MB)');
  return;
}

// Line ~95: Update multi-file validation
OLD:
const oversizedFiles = fileArray.filter(f => f.size > 20 * 1024 * 1024);
if (oversizedFiles.length > 0) {
  toast.error(language === 'vi' ? 'Một số files quá lớn (tối đa 20MB/file)' : 'Some files are too large (max 20MB/file)');
  return;
}

NEW:
const oversizedFiles = fileArray.filter(f => f.size > 50 * 1024 * 1024);
if (oversizedFiles.length > 0) {
  toast.error(language === 'vi' ? 'Một số files quá lớn (tối đa 50MB/file)' : 'Some files are too large (max 50MB/file)');
  return;
}

// Line ~485: Update file size display
OLD:
PDF {language === 'vi' ? '(tối đa 20MB, nhiều file được hỗ trợ)' : '(max 20MB, multiple files supported)'}

NEW:
PDF {language === 'vi' ? '(tối đa 50MB, nhiều file được hỗ trợ)' : '(max 50MB, multiple files supported)'}
```

---

### **PHASE 2: Copy Missing Utilities** (45 mins)

#### 2.1 Copy `issued_by_abbreviation.py` (if not exists)
```bash
# Check if exists
if [ ! -f /app/backend/app/utils/issued_by_abbreviation.py ]; then
  # Copy from V1
  cp /app/backend-v1/issued_by_abbreviation.py /app/backend/app/utils/
fi
```

**File Content Reference:**
```python
# /app/backend/app/utils/issued_by_abbreviation.py
"""
Normalize issued_by and approved_by fields to standard abbreviations
e.g., "Panama Maritime Documentation Services" → "PMDS"
"""

def normalize_issued_by(issued_by: str) -> str:
    """
    Normalize issued_by to standard abbreviation
    """
    # Mapping dictionary with case-insensitive matching
    # ... (copy full logic from V1)
```

#### 2.2 Verify `gdrive_helper.py` Supports Approval Document Path
```python
# Check if this method exists in /app/backend/app/utils/gdrive_helper.py
async def upload_approval_document_file(
    file_content: bytes,
    filename: str,
    ship_name: str,
    summary_text: Optional[str] = None,
    company_id: str = None
) -> Dict[str, Any]:
    """
    Upload approval document to: ShipName/ISM-ISPS-MLC/Approval Document/
    """
```

**If NOT exists:**
- Add method to `gdrive_helper.py` following the pattern from `upload_drawing_manual_file`
- Target path: `{ship_name}/ISM-ISPS-MLC/Approval Document/`
- Parameters: `parent_category='ISM-ISPS-MLC'`, `category='Approval Document'`

---

### **PHASE 3: Create AI Extraction Utility** (1 hour)

#### 3.1 Create `approval_document_ai.py`
```python
# File: /app/backend/app/utils/approval_document_ai.py
"""
AI extraction utilities for Approval Documents
- Extract fields from Document AI summary using System AI
"""
import logging
import json
from typing import Dict, Optional

logger = logging.getLogger(__name__)

async def extract_approval_document_fields_from_summary(
    summary_text: str,
    ai_provider: str,
    ai_model: str,
    use_emergent_key: bool
) -> Dict:
    """
    Extract approval document fields from Document AI summary using System AI
    
    Fields to extract:
    - approval_document_name
    - approval_document_no
    - approved_by
    - approved_date
    - note
    
    Returns:
        dict: Extracted fields or empty dict on failure
    """
    try:
        logger.info("🤖 Extracting approval document fields from summary")
        
        # Create extraction prompt
        prompt = create_approval_document_extraction_prompt(summary_text)
        
        if not prompt:
            logger.error("Failed to create approval document extraction prompt")
            return {}
        
        # Use System AI for extraction
        if use_emergent_key and ai_provider in ["google", "emergent"]:
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                from app.core.config import settings
                
                # Get Emergent LLM key
                emergent_key = settings.EMERGENT_LLM_KEY
                if not emergent_key:
                    logger.error("Emergent LLM key not configured")
                    return {}
                
                chat = LlmChat(
                    api_key=emergent_key,
                    session_id=f"approval_document_extraction_{int(time.time())}",
                    system_message="You are a maritime regulatory documentation analysis expert."
                ).with_model("gemini", ai_model)
                
                logger.info(f"📤 Sending extraction prompt to {ai_model}...")
                
                user_message = UserMessage(text=prompt)
                ai_response = await chat.send_message(user_message)
                
                if ai_response and ai_response.strip():
                    content = ai_response.strip()
                    logger.info("🤖 Approval Document AI response received")
                    
                    # Parse JSON response
                    try:
                        clean_content = content.replace('```json', '').replace('```', '').strip()
                        extracted_data = json.loads(clean_content)
                        
                        # Standardize date formats
                        if extracted_data.get('approved_date'):
                            try:
                                from dateutil import parser
                                parsed_date = parser.parse(extracted_data['approved_date'])
                                extracted_data['approved_date'] = parsed_date.strftime('%Y-%m-%d')
                            except Exception as date_error:
                                logger.warning(f"Failed to parse approved_date: {date_error}")
                        
                        logger.info("✅ Successfully extracted approval document fields")
                        return extracted_data
                        
                    except json.JSONDecodeError as json_error:
                        logger.error(f"Failed to parse AI response as JSON: {json_error}")
                        return {}
                else:
                    logger.warning("AI response is empty")
                    return {}
                    
            except Exception as ai_error:
                logger.error(f"System AI extraction failed: {ai_error}")
                return {}
        else:
            logger.warning(f"Unsupported AI provider or configuration: {ai_provider}")
            return {}
            
    except Exception as e:
        logger.error(f"Error in extract_approval_document_fields_from_summary: {e}")
        return {}


def create_approval_document_extraction_prompt(summary_text: str) -> str:
    """
    Create extraction prompt for approval document fields
    
    Copy EXACT prompt from Backend V1 server.py lines 8088-8159
    """
    try:
        prompt = f"""
You are a maritime regulatory documentation analysis expert. Extract the following information from the approval document summary below.

=== FIELDS TO EXTRACT ===

**approval_document_name**: 
- Extract the name/title of the approval document
- Look for phrases like "Document Title", "Approval Title", "Subject", "Certificate Name"
- Common types: "Safety Management System Approval", "Security Plan Approval", "ISM Code Compliance", "ISPS Approval Certificate", "MLC Declaration of Maritime Labour Compliance"
- Be specific and include the type of approval (ISM, ISPS, MLC, DOC, SMC, etc.)

**approval_document_no**: 
- Extract the document number, approval number, or certificate number
- Look for "Document No.", "Approval No.", "Certificate No.", "Reference No.", "DOC No.", "SMC No."
- May contain letters, numbers, dashes, slashes (e.g., "ISM-2024-001", "DOC-123456", "SMC/2024/789")
- Include any prefix or suffix codes

**approved_by**: 
- Extract who approved or issued this document
- Look for "Approved By", "Issued By", "Certified By", "Authority", "Administration", "Flag State"
- Common approvers: Classification societies (DNV, LR, ABS, BV, etc.), Flag administrations, Port State Control, RO (Recognized Organization)
- May include full organization names or abbreviations

**approved_date**: 
- Extract the approval date, issue date, or certification date
- Look for "Approval Date", "Issue Date", "Date of Approval", "Certification Date", "Effective Date"
- Format: YYYY-MM-DD or any recognizable date format
- This is the date when the document was officially approved/issued

**note**: 
- Extract any important notes, remarks, conditions, or limitations
- Look for "Notes", "Remarks", "Conditions", "Limitations", "Special Requirements", "Validity Conditions"
- Include information about scope, limitations, or special conditions of approval
- Keep it concise but include important regulatory details

=== EXTRACTION RULES ===

1. **Be precise**: Extract exact values as they appear in the document
2. **Handle missing data**: If a field is not found, return an empty string ""
3. **Date formats**: Accept any date format, but prefer YYYY-MM-DD
4. **Document names**: Be specific and include the type (e.g., "DOC - Document of Compliance ISM Code" instead of just "DOC")
5. **Abbreviations**: Keep common maritime abbreviations (ISM, ISPS, MLC, DOC, SMC, etc.)
6. **Authority names**: Use full names when available (e.g., "Det Norske Veritas" instead of just "DNV")

=== DOCUMENT SUMMARY ===

{summary_text}

=== OUTPUT FORMAT ===

Respond ONLY with valid JSON in this EXACT format (no additional text or explanation):

{{
  "approval_document_name": "extracted document name or empty string",
  "approval_document_no": "extracted document number or empty string", 
  "approved_by": "extracted approver/issuer or empty string",
  "approved_date": "YYYY-MM-DD or empty string",
  "note": "extracted notes/remarks or empty string"
}}

IMPORTANT: Return ONLY the JSON object, nothing else.
"""
        return prompt
        
    except Exception as e:
        logger.error(f"Error creating approval document extraction prompt: {e}")
        return ""
```

**Action Items:**
- [ ] Create `/app/backend/app/utils/approval_document_ai.py`
- [ ] Copy exact prompt from Backend V1
- [ ] Add `import time` if needed
- [ ] Test prompt structure

---

### **PHASE 4: Create Analyze Service** (1.5 hours)

#### 4.1 Create `approval_document_analyze_service.py`
```python
# File: /app/backend/app/services/approval_document_analyze_service.py
"""
Approval Document Analysis Service
- Document AI processing
- System AI field extraction
- PDF splitting for large files
- Similar to DrawingManualAnalyzeService
"""
import base64
import logging
from typing import Dict, Optional
from fastapi import UploadFile, HTTPException

from app.models.user import UserResponse
from app.repositories.ship_repository import ShipRepository
from app.repositories.ai_config_repository import AIConfigRepository
from app.repositories.gdrive_config_repository import GDriveConfigRepository
from app.utils.pdf_splitter import PDFSplitter
from app.utils.approval_document_ai import (
    extract_approval_document_fields_from_summary,
    create_approval_document_extraction_prompt
)
from app.utils.issued_by_abbreviation import normalize_issued_by

logger = logging.getLogger(__name__)

class ApprovalDocumentAnalyzeService:
    """Service for analyzing approval document files with AI"""
    
    @staticmethod
    async def analyze_file(
        file: UploadFile,
        ship_id: str,
        bypass_validation: bool,
        current_user: UserResponse
    ) -> Dict:
        """
        Analyze approval document file using Document AI + System AI
        
        Process (identical to Backend V1):
        1. Validate PDF file (magic bytes, extension, size)
        2. Check page count and split if >15 pages
        3. Process with Document AI (parallel for chunks)
        4. Extract fields from summary with System AI
        5. Normalize approved_by
        6. Return analysis + base64 file content
        
        Args:
            file: PDF file upload
            ship_id: Ship ID
            bypass_validation: Skip validation (for testing)
            current_user: Current authenticated user
            
        Returns:
            dict: Analysis result with extracted fields + metadata
        """
        try:
            logger.info(f"✅ Starting approval document analysis for ship_id: {ship_id}")
            
            # Read file content
            file_content = await file.read()
            filename = file.filename
            
            # Validate file input
            if not filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            if not file_content or len(file_content) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Empty file provided. Please upload a valid PDF file."
                )
            
            # Validate file type
            if not filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only PDF files are supported for approval documents."
                )
            
            # Check PDF magic bytes
            if not file_content.startswith(b'%PDF'):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PDF file format. The file does not appear to be a valid PDF document."
                )
            
            # Check file size (50MB limit)
            max_size = 50 * 1024 * 1024  # 50MB
            if len(file_content) > max_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size is 50MB. Your file is {len(file_content) / (1024*1024):.1f}MB"
                )
            
            logger.info(f"📄 Processing approval document file: {filename} ({len(file_content)} bytes)")
            
            # Check if PDF needs splitting (>15 pages)
            splitter = PDFSplitter(max_pages_per_chunk=12)
            
            try:
                total_pages = splitter.get_page_count(file_content)
                needs_split = splitter.needs_splitting(file_content)
                logger.info(f"📊 PDF Analysis: {total_pages} pages, Split needed: {needs_split}")
            except ValueError as e:
                logger.error(f"❌ Invalid PDF file: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid or corrupted PDF file: {str(e)}. Please ensure the file is a valid PDF document."
                )
            except Exception as e:
                logger.warning(f"⚠️ Could not detect page count: {e}, assuming single file processing")
                total_pages = 0
                needs_split = False
            
            # Get company information
            company_id = current_user.company
            if not company_id:
                raise HTTPException(status_code=404, detail="Company not found")
            
            # Get ship information
            ship = await ShipRepository.get_by_id(ship_id)
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            # Verify company access
            if ship.company != company_id:
                logger.warning(f"Access denied: ship company '{ship.company}' != user company '{company_id}'")
                raise HTTPException(status_code=403, detail="Access denied to this ship")
            
            ship_name = ship.name
            
            # Get AI configuration for Document AI
            ai_config = await AIConfigRepository.get_system_ai_config()
            if not ai_config:
                raise HTTPException(
                    status_code=404,
                    detail="AI configuration not found. Please configure AI in System Settings."
                )
            
            document_ai_config = ai_config.get("document_ai", {})
            
            if not document_ai_config.get("enabled", False):
                raise HTTPException(
                    status_code=400,
                    detail="Google Document AI is not enabled in System Settings"
                )
            
            # Validate required Document AI configuration
            if not all([
                document_ai_config.get("project_id"),
                document_ai_config.get("processor_id")
            ]):
                raise HTTPException(
                    status_code=400,
                    detail="Incomplete Google Document AI configuration."
                )
            
            logger.info("🤖 Analyzing approval document with Google Document AI...")
            
            # Initialize empty analysis data
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
            
            # Store file content FIRST before any analysis
            analysis_result['_file_content'] = base64.b64encode(file_content).decode('utf-8')
            analysis_result['_filename'] = filename
            analysis_result['_content_type'] = file.content_type or 'application/pdf'
            analysis_result['_ship_name'] = ship_name
            analysis_result['_summary_text'] = ''
            
            # Process based on file size
            if needs_split and total_pages > 15:
                # Large PDF processing with splitting
                analysis_result = await ApprovalDocumentAnalyzeService._process_large_pdf(
                    file_content=file_content,
                    filename=filename,
                    ship_name=ship_name,
                    total_pages=total_pages,
                    splitter=splitter,
                    document_ai_config=document_ai_config,
                    ai_config=ai_config,
                    analysis_result=analysis_result,
                    company_id=company_id
                )
            else:
                # Small PDF: Normal single-file processing
                analysis_result = await ApprovalDocumentAnalyzeService._process_small_pdf(
                    file_content=file_content,
                    filename=filename,
                    document_ai_config=document_ai_config,
                    ai_config=ai_config,
                    analysis_result=analysis_result,
                    company_id=company_id
                )
            
            # Normalize approved_by to standard abbreviation
            if analysis_result.get('approved_by'):
                try:
                    original_approved_by = analysis_result['approved_by']
                    normalized_approved_by = normalize_issued_by(original_approved_by)
                    
                    if normalized_approved_by != original_approved_by:
                        analysis_result['approved_by'] = normalized_approved_by
                        logger.info(f"✅ Normalized Approved By: '{original_approved_by}' → '{normalized_approved_by}'")
                    else:
                        logger.info(f"ℹ️ Approved By kept as: '{original_approved_by}'")
                        
                except Exception as norm_error:
                    logger.error(f"❌ Error normalizing approved_by: {norm_error}")
            
            logger.info("✅ Approval document analysis completed successfully")
            return analysis_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error analyzing approval document file: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @staticmethod
    async def _process_small_pdf(
        file_content: bytes,
        filename: str,
        document_ai_config: Dict,
        ai_config: Dict,
        analysis_result: Dict,
        company_id: str
    ) -> Dict:
        """
        Process small PDF (≤15 pages) with Document AI + System AI
        
        Reference: Backend V1 server.py lines 13735-13804
        """
        logger.info("📄 Processing as single file (≤15 pages)")
        
        try:
            # Get Document AI service (reuse from drawing manuals)
            from app.services.document_ai_service import DocumentAIService
            
            # Analyze with Document AI
            ai_analysis = await DocumentAIService.analyze_document(
                file_content=file_content,
                filename=filename,
                content_type='application/pdf',
                document_ai_config=document_ai_config,
                company_id=company_id
            )
            
            if ai_analysis:
                summary_text = ai_analysis.get('summary_text', '')
                
                if summary_text and summary_text.strip():
                    analysis_result['_summary_text'] = summary_text
                    
                    # Extract fields from summary
                    logger.info("🧠 Extracting approval document fields from Document AI summary...")
                    
                    ai_provider = ai_config.get("provider", "google")
                    ai_model = ai_config.get("model", "gemini-2.0-flash-exp")
                    use_emergent_key = ai_config.get("use_emergent_key", True)
                    
                    try:
                        extracted_fields = await extract_approval_document_fields_from_summary(
                            summary_text,
                            ai_provider,
                            ai_model,
                            use_emergent_key
                        )
                        
                        if extracted_fields:
                            logger.info("✅ System AI approval document extraction completed successfully")
                            analysis_result.update(extracted_fields)
                            analysis_result["processing_method"] = "analysis_only_no_upload"
                            logger.info(f"   📋 Extracted Document Name: '{analysis_result.get('approval_document_name')}'")
                            logger.info(f"   🔢 Extracted Document No: '{analysis_result.get('approval_document_no')}'")
                        else:
                            logger.warning("⚠️ No fields extracted from summary, using fallback")
                            analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
                            analysis_result['note'] = "AI field extraction incomplete"
                    
                    except Exception as extraction_error:
                        logger.error(f"❌ Field extraction failed: {extraction_error}")
                        analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
                        analysis_result['note'] = f"AI extraction error: {str(extraction_error)[:100]}"
                
                else:
                    logger.warning("⚠️ Document AI returned empty summary")
                    analysis_result['_summary_text'] = ''
                    analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
                    analysis_result['note'] = "AI analysis returned empty result. Manual review required."
                
                if 'confidence_score' in ai_analysis:
                    analysis_result['confidence_score'] = ai_analysis['confidence_score']
                
                logger.info("✅ Approval document file analyzed successfully")
            else:
                logger.warning("⚠️ AI analysis returned no data, using fallback")
                analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
                analysis_result['note'] = "AI analysis unavailable. Manual review required."
                
        except Exception as ai_error:
            logger.error(f"❌ Document AI analysis failed: {ai_error}")
            logger.warning("⚠️ Continuing without AI analysis - file upload will still work")
            analysis_result['approval_document_name'] = analysis_result.get('approval_document_name') or filename
            analysis_result['note'] = f"AI analysis failed: {str(ai_error)}"
        
        return analysis_result
    
    
    @staticmethod
    async def _process_large_pdf(
        file_content: bytes,
        filename: str,
        ship_name: str,
        total_pages: int,
        splitter: PDFSplitter,
        document_ai_config: Dict,
        ai_config: Dict,
        analysis_result: Dict,
        company_id: str
    ) -> Dict:
        """
        Process large PDF (>15 pages) with splitting and batch processing
        
        Process:
        1. Split PDF into chunks (12 pages each)
        2. Process first 5 chunks only (MAX_CHUNKS = 5)
        3. Extract fields from each chunk
        4. Merge results intelligently
        5. Create enhanced merged summary
        
        Reference: Backend V1 server.py lines 12569-12722
        Reference: DrawingManualAnalyzeService (similar implementation)
        """
        logger.info("📦 Large PDF - using split processing")
        analysis_result['processing_method'] = 'split_pdf_batch_processing'
        
        try:
            # Split PDF into chunks
            chunks = splitter.split_pdf(file_content, filename)
            total_chunks = len(chunks)
            
            # Limit to first 5 chunks
            MAX_CHUNKS = 5
            chunks_to_process = chunks[:MAX_CHUNKS]
            
            if total_chunks > MAX_CHUNKS:
                skipped_chunks = total_chunks - MAX_CHUNKS
                logger.warning(f"⚠️ File has {total_chunks} chunks. Processing first {MAX_CHUNKS} chunks only, skipping {skipped_chunks} chunks")
                
                skipped_pages = sum(chunk.get('page_count', 0) for chunk in chunks[MAX_CHUNKS:])
                logger.info(f"📊 Processing {len(chunks_to_process)} chunks (~{sum(c.get('page_count', 0) for c in chunks_to_process)} pages), skipping ~{skipped_pages} pages")
            
            # Process chunks (reuse from drawing manuals)
            from app.services.document_ai_service import DocumentAIService
            
            chunk_results = []
            
            for chunk in chunks_to_process:
                try:
                    chunk_num = chunk['chunk_num']
                    chunk_content = chunk['content']
                    page_range = chunk['page_range']
                    
                    logger.info(f"🔄 Processing chunk {chunk_num}/{len(chunks_to_process)} (pages {page_range})...")
                    
                    # Analyze chunk with Document AI
                    ai_analysis = await DocumentAIService.analyze_document(
                        file_content=chunk_content,
                        filename=f"{filename}_chunk{chunk_num}",
                        content_type='application/pdf',
                        document_ai_config=document_ai_config,
                        company_id=company_id
                    )
                    
                    if ai_analysis and ai_analysis.get('summary_text'):
                        summary_text = ai_analysis['summary_text']
                        
                        # Extract fields from this chunk
                        ai_provider = ai_config.get("provider", "google")
                        ai_model = ai_config.get("model", "gemini-2.0-flash-exp")
                        use_emergent_key = ai_config.get("use_emergent_key", True)
                        
                        extracted_fields = await extract_approval_document_fields_from_summary(
                            summary_text,
                            ai_provider,
                            ai_model,
                            use_emergent_key
                        )
                        
                        chunk_results.append({
                            'success': True,
                            'chunk_num': chunk_num,
                            'page_range': page_range,
                            'summary_text': summary_text,
                            'extracted_fields': extracted_fields or {}
                        })
                        
                        logger.info(f"✅ Chunk {chunk_num} processed successfully")
                    else:
                        logger.warning(f"⚠️ Chunk {chunk_num} returned no summary")
                        chunk_results.append({
                            'success': False,
                            'chunk_num': chunk_num,
                            'page_range': page_range,
                            'error': 'No summary returned'
                        })
                    
                except Exception as chunk_error:
                    logger.error(f"❌ Error processing chunk {chunk_num}: {chunk_error}")
                    chunk_results.append({
                        'success': False,
                        'chunk_num': chunk_num,
                        'page_range': page_range,
                        'error': str(chunk_error)
                    })
            
            # Merge results from all chunks
            from app.utils.pdf_splitter import merge_analysis_results, create_enhanced_merged_summary
            
            merged_data = merge_analysis_results(chunk_results)
            
            if merged_data.get('success'):
                # Update analysis_result with merged data
                analysis_result.update({
                    'approval_document_name': merged_data.get('approval_document_name', ''),
                    'approval_document_no': merged_data.get('approval_document_no', ''),
                    'approved_by': merged_data.get('approved_by', ''),
                    'approved_date': merged_data.get('approved_date', ''),
                    'note': merged_data.get('note', ''),
                    'status': merged_data.get('status', 'Unknown')
                })
                
                # Create enhanced merged summary
                merged_summary = create_enhanced_merged_summary(
                    chunk_results,
                    merged_data,
                    filename,
                    total_pages
                )
                
                analysis_result['_summary_text'] = merged_summary
                
                # Add split info
                successful_chunks = [cr for cr in chunk_results if cr.get('success')]
                failed_chunks = len(chunk_results) - len(successful_chunks)
                all_chunks_failed = len(successful_chunks) == 0
                partial_success = len(successful_chunks) > 0 and failed_chunks > 0
                
                analysis_result['_split_info'] = {
                    'was_split': True,
                    'total_pages': total_pages,
                    'total_chunks': total_chunks,
                    'processed_chunks': len(chunks_to_process),
                    'successful_chunks': len(successful_chunks),
                    'failed_chunks': failed_chunks,
                    'all_chunks_failed': all_chunks_failed,
                    'partial_success': partial_success,
                    'has_failures': failed_chunks > 0,
                    'was_limited': total_chunks > MAX_CHUNKS,
                    'max_chunks_limit': MAX_CHUNKS,
                    'skipped_chunks': total_chunks - MAX_CHUNKS if total_chunks > MAX_CHUNKS else 0
                }
                
                logger.info("✅ Large PDF processing completed with merged results")
            else:
                logger.error("❌ Failed to merge chunk results")
                analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
                analysis_result['note'] = "Failed to merge chunk results. Manual review required."
            
        except Exception as split_error:
            logger.error(f"❌ Error in split PDF processing: {split_error}")
            analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
            analysis_result['note'] = f"Split processing error: {str(split_error)}"
        
        return analysis_result
```

**Action Items:**
- [ ] Create `/app/backend/app/services/approval_document_analyze_service.py`
- [ ] Reuse `DocumentAIService` from drawing manuals
- [ ] Implement both small and large PDF processing
- [ ] Add MAX_CHUNKS = 5 limit
- [ ] Test with sample PDFs

---

### **PHASE 5: Update API Endpoints** (1 hour)

#### 5.1 Add `analyze-file` Endpoint
```python
# File: /app/backend/app/api/v1/approval_documents.py
# Replace stub at lines 114-126

@router.post("/analyze-file")
async def analyze_approval_document_file(
    ship_id: str = Form(...),
    document_file: UploadFile = File(...),
    bypass_validation: str = Form("false"),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze approval document file using AI (Editor+ role required)
    
    Process:
    1. Validate PDF file (magic bytes, extension, max 50MB)
    2. Check if needs splitting (>15 pages)
    3. Process with Document AI (parallel chunks if large)
    4. Extract fields with System AI
    5. Normalize approved_by
    6. Return analysis + base64 file for upload
    
    Returns:
        dict: Analysis result with extracted fields + metadata
            {
                "approval_document_name": str,
                "approval_document_no": str,
                "approved_by": str (normalized),
                "approved_date": str (YYYY-MM-DD),
                "note": str,
                "confidence_score": float,
                "processing_method": str,
                "_filename": str,
                "_file_content": str (base64),
                "_content_type": str,
                "_summary_text": str,
                "_split_info": dict (if large file)
            }
    """
    try:
        from app.services.approval_document_analyze_service import ApprovalDocumentAnalyzeService
        
        bypass = bypass_validation.lower() == "true"
        
        result = await ApprovalDocumentAnalyzeService.analyze_file(
            file=document_file,
            ship_id=ship_id,
            bypass_validation=bypass,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing approval document: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 5.2 Add `upload-files` Endpoint
```python
# File: /app/backend/app/api/v1/approval_documents.py
# Add after analyze-file endpoint

@router.post("/{document_id}/upload-files")
async def upload_approval_document_files(
    document_id: str,
    file_content: str = Body(...),
    filename: str = Body(...),
    content_type: str = Body(...),
    summary_text: Optional[str] = Body(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload approval document files to Google Drive after record creation
    
    Path: {ship_name}/ISM-ISPS-MLC/Approval Document/
    - Original file and summary file in SAME folder
    
    Args:
        document_id: Document ID
        file_content: Base64 encoded file content
        filename: Original filename
        content_type: File MIME type
        summary_text: Optional summary text for summary file
        
    Returns:
        dict: Upload result
            {
                "success": true,
                "message": "...",
                "document": ApprovalDocumentResponse,
                "original_file_id": str,
                "summary_file_id": str,
                "summary_error": str (if summary upload failed)
            }
    """
    try:
        result = await ApprovalDocumentService.upload_files(
            document_id=document_id,
            file_content=file_content,
            filename=filename,
            content_type=content_type,
            summary_text=summary_text,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading approval document files: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Action Items:**
- [ ] Update `/app/backend/app/api/v1/approval_documents.py`
- [ ] Replace analyze stub with full implementation
- [ ] Add upload-files endpoint
- [ ] Add proper imports and error handling

---

### **PHASE 6: Add Upload Method to Service** (1 hour)

#### 6.1 Add `upload_files` to `ApprovalDocumentService`
```python
# File: /app/backend/app/services/approval_document_service.py
# Add this method

@staticmethod
async def upload_files(
    document_id: str,
    file_content: str,
    filename: str,
    content_type: str,
    summary_text: Optional[str],
    current_user: UserResponse
) -> Dict:
    """
    Upload approval document files to Google Drive
    
    Process:
    1. Validate document exists
    2. Verify company access
    3. Decode base64 file content
    4. Upload original file to: ShipName/ISM-ISPS-MLC/Approval Document/
    5. Upload summary file (if summary_text provided)
    6. Update document with file IDs
    
    Args:
        document_id: Document ID
        file_content: Base64 encoded file
        filename: Original filename
        content_type: MIME type
        summary_text: Optional summary text
        current_user: Current user
        
    Returns:
        dict: Upload result with file IDs
    """
    try:
        logger.info(f"📤 Starting file upload for approval document: {document_id}")
        
        # Validate document exists
        document = await ApprovalDocumentRepository.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get company and ship info
        company_id = current_user.company
        if not company_id:
            raise HTTPException(status_code=404, detail="Company not found")
        
        ship_id = document.ship_id
        if not ship_id:
            raise HTTPException(status_code=400, detail="Document has no ship_id")
        
        # Get ship
        ship = await ShipRepository.get_by_id(ship_id)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Verify company access
        if ship.company != company_id:
            logger.warning(f"Access denied: ship company '{ship.company}' != user company '{company_id}'")
            raise HTTPException(status_code=403, detail="Access denied to this ship")
        
        ship_name = ship.name
        
        # Decode base64 file content
        try:
            import base64
            file_bytes = base64.b64decode(file_content)
            logger.info(f"✅ Decoded file content: {len(file_bytes)} bytes")
        except Exception as e:
            logger.error(f"Failed to decode base64 file content: {e}")
            raise HTTPException(status_code=400, detail="Invalid file content encoding")
        
        logger.info(f"📄 Processing file: {filename} ({len(file_bytes)} bytes)")
        
        # Upload files to Google Drive
        from app.utils.gdrive_helper import upload_approval_document_file
        
        logger.info("📤 Uploading approval document files to Drive...")
        logger.info(f"📄 Target path: {ship_name}/ISM-ISPS-MLC/Approval Document/{filename}")
        
        upload_result = await upload_approval_document_file(
            file_content=file_bytes,
            filename=filename,
            ship_name=ship_name,
            summary_text=summary_text,
            company_id=company_id
        )
        
        if not upload_result.get('success'):
            logger.error(f"❌ File upload failed: {upload_result.get('message')}")
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {upload_result.get('message', 'Unknown error')}"
            )
        
        # Extract file IDs
        original_file_id = upload_result.get('original_file_id')
        summary_file_id = upload_result.get('summary_file_id')
        
        # Update document with file IDs
        update_data = {}
        if original_file_id:
            update_data['file_id'] = original_file_id
        if summary_file_id:
            update_data['summary_file_id'] = summary_file_id
        
        if update_data:
            from datetime import datetime, timezone
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            updated_doc = await ApprovalDocumentRepository.update(document_id, update_data)
            logger.info("✅ Document updated with file IDs")
        else:
            updated_doc = document
        
        # Handle summary upload failure (non-critical)
        summary_error = upload_result.get('summary_error')
        if summary_error:
            logger.warning(f"⚠️ Summary upload failed (non-critical): {summary_error}")
        
        logger.info("✅ Approval document files uploaded successfully")
        
        return {
            "success": True,
            "message": "Approval document files uploaded successfully",
            "document": updated_doc,
            "original_file_id": original_file_id,
            "summary_file_id": summary_file_id,
            "summary_error": summary_error
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading approval document files: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Action Items:**
- [ ] Update `/app/backend/app/services/approval_document_service.py`
- [ ] Add upload_files method
- [ ] Import required utilities
- [ ] Test with sample data

---

### **PHASE 7: Add Background GDrive Deletion** (45 mins)

#### 7.1 Update Delete Method with BackgroundTasks
```python
# File: /app/backend/app/services/approval_document_service.py
# Update existing delete_approval_document method

@staticmethod
async def delete_approval_document(
    doc_id: str,
    current_user: UserResponse,
    background_tasks: Optional[BackgroundTasks] = None
) -> Dict:
    """
    Delete approval document with optional background GDrive cleanup
    
    Process:
    1. Get document and verify access
    2. Delete from database immediately
    3. Schedule background GDrive file deletion (if file IDs exist)
    
    Args:
        doc_id: Document ID
        current_user: Current user
        background_tasks: FastAPI BackgroundTasks (for async deletion)
        
    Returns:
        dict: Deletion result
            {
                "success": true,
                "message": "...",
                "background_deletion": bool,
                "files_scheduled": int
            }
    """
    try:
        # Get document
        document = await ApprovalDocumentRepository.get_by_id(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Approval Document not found")
        
        # Verify company access
        company_id = current_user.company
        ship = await ShipRepository.get_by_id(document.ship_id)
        if ship and ship.company != company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete from database
        await ApprovalDocumentRepository.delete(doc_id)
        logger.info(f"✅ Approval Document deleted from DB: {doc_id}")
        
        # Schedule background GDrive deletion
        files_scheduled = 0
        background_deletion = False
        
        if background_tasks:
            file_ids_to_delete = []
            
            if document.file_id:
                file_ids_to_delete.append({
                    'file_id': document.file_id,
                    'description': f"{document.approval_document_name} (original)"
                })
                files_scheduled += 1
            
            if document.summary_file_id:
                file_ids_to_delete.append({
                    'file_id': document.summary_file_id,
                    'description': f"{document.approval_document_name} (summary)"
                })
                files_scheduled += 1
            
            if file_ids_to_delete:
                from app.services.gdrive_service import GDriveService
                
                for file_info in file_ids_to_delete:
                    background_tasks.add_task(
                        GDriveService.delete_file_with_retry,
                        file_id=file_info['file_id'],
                        description=file_info['description'],
                        document_type='approval_document',
                        company_id=company_id
                    )
                    logger.info(f"📋 Scheduled background deletion for: {file_info['description']}")
                
                background_deletion = True
        
        message = "Approval Document deleted successfully"
        if background_deletion:
            message += f". File deletion in progress ({files_scheduled} file(s))..."
        
        return {
            "success": True,
            "message": message,
            "background_deletion": background_deletion,
            "files_scheduled": files_scheduled
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting approval document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 7.2 Update Bulk Delete with Background Deletion
```python
# File: /app/backend/app/services/approval_document_service.py
# Update existing bulk_delete_approval_documents method

@staticmethod
async def bulk_delete_approval_documents(
    request: BulkDeleteApprovalDocumentRequest,
    current_user: UserResponse,
    background_tasks: Optional[BackgroundTasks] = None
) -> Dict:
    """
    Bulk delete approval documents with background GDrive cleanup
    
    Similar to single delete but processes multiple documents
    """
    try:
        doc_ids = request.doc_ids
        company_id = current_user.company
        
        deleted_count = 0
        files_scheduled = 0
        file_ids_to_delete = []
        
        for doc_id in doc_ids:
            try:
                document = await ApprovalDocumentRepository.get_by_id(doc_id)
                if not document:
                    continue
                
                # Verify access
                ship = await ShipRepository.get_by_id(document.ship_id)
                if ship and ship.company != company_id:
                    continue
                
                # Collect file IDs for background deletion
                if document.file_id:
                    file_ids_to_delete.append({
                        'file_id': document.file_id,
                        'description': f"{document.approval_document_name} (original)"
                    })
                
                if document.summary_file_id:
                    file_ids_to_delete.append({
                        'file_id': document.summary_file_id,
                        'description': f"{document.approval_document_name} (summary)"
                    })
                
                # Delete from database
                await ApprovalDocumentRepository.delete(doc_id)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error deleting document {doc_id}: {e}")
                continue
        
        # Schedule background deletions
        background_deletion = False
        if background_tasks and file_ids_to_delete:
            from app.services.gdrive_service import GDriveService
            
            for file_info in file_ids_to_delete:
                background_tasks.add_task(
                    GDriveService.delete_file_with_retry,
                    file_id=file_info['file_id'],
                    description=file_info['description'],
                    document_type='approval_document',
                    company_id=company_id
                )
                files_scheduled += 1
            
            background_deletion = True
            logger.info(f"📋 Scheduled {files_scheduled} file(s) for background deletion")
        
        message = f"Deleted {deleted_count} approval document(s)"
        if background_deletion:
            message += f". Background deletion of {files_scheduled} file(s) in progress..."
        
        return {
            "success": True,
            "message": message,
            "deleted_count": deleted_count,
            "background_deletion": background_deletion,
            "files_scheduled": files_scheduled
        }
        
    except Exception as e:
        logger.error(f"❌ Error bulk deleting approval documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 7.3 Update Delete Endpoints in API
```python
# File: /app/backend/app/api/v1/approval_documents.py
# Update delete endpoints to include BackgroundTasks

from fastapi import BackgroundTasks

@router.delete("/{doc_id}")
async def delete_approval_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    background: bool = Query(True),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Approval Document with optional background GDrive cleanup (Editor+ role required)"""
    try:
        return await ApprovalDocumentService.delete_approval_document(
            doc_id,
            current_user,
            background_tasks if background else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Approval Document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Approval Document")

@router.post("/bulk-delete")
async def bulk_delete_approval_documents(
    request: BulkDeleteApprovalDocumentRequest,
    background_tasks: BackgroundTasks,
    background: bool = Query(True),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Approval Documents with background GDrive cleanup (Editor+ role required)"""
    try:
        return await ApprovalDocumentService.bulk_delete_approval_documents(
            request,
            current_user,
            background_tasks if background else None
        )
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Approval Documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Approval Documents")
```

**Action Items:**
- [ ] Update delete methods with BackgroundTasks
- [ ] Add GDriveService.delete_file_with_retry calls
- [ ] Update API endpoints with background parameter
- [ ] Test deletion flow

---

### **PHASE 8: Update GDrive Helper (if needed)** (30 mins)

#### 8.1 Check and Add Approval Document Upload Method
```python
# File: /app/backend/app/utils/gdrive_helper.py
# Check if this method exists, if not add it

async def upload_approval_document_file(
    file_content: bytes,
    filename: str,
    ship_name: str,
    summary_text: Optional[str] = None,
    company_id: str = None
) -> Dict[str, Any]:
    """
    Upload approval document file (and optional summary) to Google Drive
    Path: ShipName/ISM-ISPS-MLC/Approval Document/
    
    Args:
        file_content: File content bytes
        filename: Original filename
        ship_name: Ship name for folder structure
        summary_text: Optional summary text
        company_id: Company ID for GDrive config
        
    Returns:
        dict: Upload results
            {
                'success': bool,
                'original_file_id': str,
                'summary_file_id': str,
                'summary_error': str,
                'message': str
            }
    """
    try:
        logger.info(f"📤 Uploading approval document file to Drive: {filename}")
        logger.info(f"   Ship: {ship_name}")
        logger.info(f"   Target Path: {ship_name}/ISM-ISPS-MLC/Approval Document/")
        
        # Get company GDrive configuration
        from app.repositories.gdrive_config_repository import GDriveConfigRepository
        gdrive_config = await GDriveConfigRepository.get_company_config(company_id)
        
        if not gdrive_config:
            raise ValueError("Company Google Drive not configured")
        
        # Upload original file
        upload_params = {
            'action': 'upload_file_with_folder_creation',
            'parent_folder_id': gdrive_config.parent_folder_id,
            'ship_name': ship_name,
            'parent_category': 'ISM-ISPS-MLC',        # First level under ShipName
            'category': 'Approval Document',          # Second level under ISM-ISPS-MLC
            'filename': filename,
            'file_content': base64.b64encode(file_content).decode('utf-8'),
            'content_type': 'application/pdf'
        }
        
        original_upload = await _call_apps_script(
            gdrive_config.web_app_url,
            upload_params
        )
        
        result = {
            'success': False,
            'original_file_id': None,
            'summary_file_id': None,
            'summary_error': None
        }
        
        if original_upload.get('success'):
            file_id = original_upload.get('file_id')
            result['original_file_id'] = file_id
            result['success'] = True
            logger.info(f"✅ Approval document file uploaded successfully")
            logger.info(f"   File ID: {file_id}")
        else:
            logger.error(f"❌ File upload failed: {original_upload.get('message')}")
            result['message'] = f"Original file upload failed: {original_upload.get('message')}"
            return result
        
        # Upload summary file if provided
        if summary_text and summary_text.strip():
            try:
                logger.info(f"📝 Uploading summary file...")
                summary_filename = filename.replace('.pdf', '_summary.txt')
                
                summary_params = {
                    'action': 'upload_file_with_folder_creation',
                    'parent_folder_id': gdrive_config.parent_folder_id,
                    'ship_name': ship_name,
                    'parent_category': 'ISM-ISPS-MLC',
                    'category': 'Approval Document',
                    'filename': summary_filename,
                    'file_content': base64.b64encode(summary_text.encode('utf-8')).decode('utf-8'),
                    'content_type': 'text/plain'
                }
                
                summary_upload = await _call_apps_script(
                    gdrive_config.web_app_url,
                    summary_params
                )
                
                if summary_upload.get('success'):
                    summary_file_id = summary_upload.get('file_id')
                    result['summary_file_id'] = summary_file_id
                    logger.info(f"✅ Summary file uploaded successfully")
                    logger.info(f"   Summary File ID: {summary_file_id}")
                else:
                    result['summary_error'] = f"Summary upload failed: {summary_upload.get('message')}"
                    logger.warning(f"⚠️ Summary file upload failed (non-critical): {summary_upload.get('message')}")
                    
            except Exception as summary_error:
                result['summary_error'] = str(summary_error)
                logger.warning(f"⚠️ Summary file upload error (non-critical): {summary_error}")
        
        result['message'] = 'Approval document files uploaded successfully'
        return result
            
    except Exception as e:
        logger.error(f"❌ Error uploading approval document files: {e}")
        return {
            'success': False,
            'message': f'File upload failed: {str(e)}',
            'error': str(e)
        }
```

**Action Items:**
- [ ] Check if `upload_approval_document_file` exists in gdrive_helper.py
- [ ] If not, add it following the pattern above
- [ ] Ensure `_call_apps_script` helper function exists
- [ ] Test upload flow

---

### **PHASE 9: Testing** (2 hours)

#### 9.1 Backend Testing
```bash
# Test analyze-file endpoint
curl -X POST "http://localhost:8001/api/approval-documents/analyze-file" \
  -H "Authorization: Bearer $TOKEN" \
  -F "ship_id=<ship_id>" \
  -F "document_file=@sample_approval.pdf" \
  -F "bypass_validation=false"

# Expected response:
{
  "approval_document_name": "...",
  "approval_document_no": "...",
  "approved_by": "...",
  "approved_date": "YYYY-MM-DD",
  "note": "...",
  "confidence_score": 0.8,
  "processing_method": "analysis_only_no_upload",
  "_filename": "sample_approval.pdf",
  "_file_content": "base64...",
  "_summary_text": "...",
  "_split_info": {...}  // if large file
}

# Test create + upload workflow
# 1. Create document
curl -X POST "http://localhost:8001/api/approval-documents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ship_id": "<ship_id>",
    "approval_document_name": "Test Approval",
    "approval_document_no": "TEST-001",
    "approved_by": "DNV",
    "approved_date": "2024-01-15",
    "status": "Valid"
  }'

# 2. Upload files
curl -X POST "http://localhost:8001/api/approval-documents/<doc_id>/upload-files" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_content": "<base64_content>",
    "filename": "test_approval.pdf",
    "content_type": "application/pdf",
    "summary_text": "Summary text..."
  }'

# Test delete with background cleanup
curl -X DELETE "http://localhost:8001/api/approval-documents/<doc_id>?background=true" \
  -H "Authorization: Bearer $TOKEN"
```

#### 9.2 Frontend Testing
```
1. Upload small PDF (<15 pages):
   - Should analyze quickly
   - Auto-fill form fields
   - Save successfully
   - Upload in background

2. Upload large PDF (>15 pages):
   - Should show split warning
   - Process first 5 chunks
   - Merge results
   - Display correctly

3. Upload very large PDF (>50MB):
   - Should reject with error
   - Show file size message

4. Multi-file upload:
   - Select multiple PDFs
   - Should trigger batch processing modal
   - Process all files

5. Delete document:
   - Should delete from DB immediately
   - Should show background deletion message
   - Check GDrive files removed
```

#### 9.3 Integration Testing
```
Test complete flow:
1. Login as Editor user
2. Select ship
3. Upload approval document PDF
4. Verify AI analysis
5. Check auto-filled fields
6. Save document
7. Verify file uploaded to GDrive
8. Check folder structure: ShipName/ISM-ISPS-MLC/Approval Document/
9. Verify both original and summary files
10. Delete document
11. Verify background deletion
12. Check GDrive files removed
```

**Action Items:**
- [ ] Test analyze endpoint with small PDF
- [ ] Test analyze endpoint with large PDF (>15 pages)
- [ ] Test analyze endpoint with very large PDF (>50MB)
- [ ] Test create + upload workflow
- [ ] Test delete with background cleanup
- [ ] Test bulk delete
- [ ] Test frontend integration
- [ ] Verify GDrive folder structure
- [ ] Check error handling

---

### **PHASE 10: Documentation & Cleanup** (30 mins)

#### 10.1 Update API Documentation
```python
# Ensure all endpoints have proper docstrings
# Add to API docs:
- POST /approval-documents/analyze-file
- POST /approval-documents/{doc_id}/upload-files
- DELETE /approval-documents/{doc_id}?background=true
- POST /approval-documents/bulk-delete?background=true
```

#### 10.2 Code Review Checklist
```
✅ All Backend V1 logic replicated
✅ Reused existing utilities (pdf_splitter, gdrive_helper)
✅ Applied Drawings & Manuals patterns
✅ File size limit increased to 50MB
✅ MAX_CHUNKS = 5 implemented
✅ Background GDrive deletion working
✅ Error handling comprehensive
✅ Logging informative
✅ Type hints correct
✅ No breaking changes to existing code
```

---

## 🎯 SUMMARY

### Total Time Estimate: **8-10 hours**
- Phase 1: Preparation (30 mins)
- Phase 2: Copy Utilities (45 mins)
- Phase 3: AI Extraction (1 hour)
- Phase 4: Analyze Service (1.5 hours)
- Phase 5: API Endpoints (1 hour)
- Phase 6: Upload Service (1 hour)
- Phase 7: Background Deletion (45 mins)
- Phase 8: GDrive Helper (30 mins)
- Phase 9: Testing (2 hours)
- Phase 10: Documentation (30 mins)

### Key Changes from Backend V1:
1. ✅ File size limit: 20MB → 50MB
2. ✅ Reused existing pdf_splitter.py
3. ✅ Reused existing gdrive_helper.py
4. ✅ Applied Drawings & Manuals patterns
5. ✅ Background GDrive deletion with retry
6. ✅ Improved error handling
7. ✅ Better logging

### Files to Create/Modify:
```
CREATE:
- /app/backend/app/utils/approval_document_ai.py
- /app/backend/app/services/approval_document_analyze_service.py

MODIFY:
- /app/backend/app/api/v1/approval_documents.py
- /app/backend/app/services/approval_document_service.py
- /app/backend/app/utils/gdrive_helper.py (if method missing)
- /app/frontend/src/components/ApprovalDocument/AddApprovalDocumentModal.jsx

VERIFY EXISTS:
- /app/backend/app/utils/issued_by_abbreviation.py
- /app/backend/app/utils/pdf_splitter.py
- /app/backend/app/services/gdrive_service.py
```

### Testing Priority:
1. **Critical:** Analyze-file endpoint (small & large PDFs)
2. **Critical:** Upload-files endpoint
3. **Critical:** Delete with background cleanup
4. **Important:** Frontend integration
5. **Important:** GDrive folder structure
6. **Nice to have:** Bulk operations

---

**Ready to start migration? 🚀**

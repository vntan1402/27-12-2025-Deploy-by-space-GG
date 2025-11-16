# PLAN MIGRATE TEST REPORT - CHI TIẾT

## Ngày bắt đầu: 2025
## Mục tiêu: Migrate 100% Test Report flow từ backend-v1 sang backend mới
## Phương pháp: Proper Refactor (Option B) cho utilities để reuse cho tất cả document types

---

## 📋 TỔNG QUAN

### Current Status:
- ✅ Survey Report: 100% migrated
- ⚠️ Test Report: 20% migrated (chỉ có CRUD basic)

### Missing Components:
1. ❌ analyze-file endpoint logic (~600 lines)
2. ❌ upload-files endpoint logic (~100 lines)
3. ❌ Valid Date Calculator (~150 lines)
4. ❌ AI extraction prompt (~200 lines)
5. ⚠️ Utilities cần refactor để generic (~200 lines refactor)

### Total Effort: 6-8 ngày làm việc

---

## 🎯 CHIẾN LƯỢC

### Phase 1: REFACTOR UTILITIES (2-3 ngày)
- Refactor 3 utilities để generic
- Test với Survey Report (đảm bảo không break)
- Chuẩn bị cho Test Report sử dụng

### Phase 2: MIGRATE TEST REPORT CORE LOGIC (3-4 ngày)
- Migrate analyze-file endpoint
- Migrate upload-files endpoint
- Migrate Valid Date Calculator
- Migrate AI extraction prompt

### Phase 3: TESTING & VALIDATION (1-2 ngày)
- Test với real-world PDF files
- Verify tất cả flows
- Bug fixes

---

## 📅 PHASE 1: REFACTOR UTILITIES (2-3 NGÀY)

### Objective: Refactor 3 utilities để generic, có thể sử dụng cho cả Survey Report và Test Report

---

### TASK 1.1: Refactor PDF Splitter (4-5 giờ)

#### A. Backup hiện tại
```bash
cp /app/backend/app/utils/pdf_splitter.py /app/backend/app/utils/pdf_splitter.py.backup
```

#### B. Refactor `merge_analysis_results()`

**File:** `/app/backend/app/utils/pdf_splitter.py`

**Changes:**

```python
# BEFORE (Survey Report specific):
def merge_analysis_results(chunk_results: List[Dict]) -> Dict:
    merged = {
        'survey_report_name': '',
        'survey_report_no': '',
        'issued_by': '',
        # ...
    }

# AFTER (Generic):
def merge_analysis_results(
    chunk_results: List[Dict],
    document_type: str = 'survey_report'  # ✅ NEW parameter
) -> Dict:
    """
    Merge analysis results from multiple chunks
    
    Args:
        chunk_results: List of chunk analysis results
        document_type: Type of document ('survey_report', 'test_report', etc.)
    
    Returns:
        Merged data dictionary
    """
    
    # ✅ Define field mappings per document type
    FIELD_MAPPINGS = {
        'survey_report': {
            'name': 'survey_report_name',
            'no': 'survey_report_no'
        },
        'test_report': {
            'name': 'test_report_name',
            'no': 'test_report_no'
        },
        'audit_report': {
            'name': 'audit_report_name',
            'no': 'audit_report_no'
        }
        # Future: drawings_manual, approval_document, etc.
    }
    
    if document_type not in FIELD_MAPPINGS:
        raise ValueError(f"Unsupported document_type: {document_type}")
    
    mapping = FIELD_MAPPINGS[document_type]
    name_field = mapping['name']
    no_field = mapping['no']
    
    # Initialize merged result with dynamic field names
    merged = {
        name_field: '',
        no_field: '',
        'issued_by': '',
        'issued_date': '',
        'ship_name': '',
        'ship_imo': '',
        'note': ''
    }
    
    # Merge logic using dynamic field names
    all_names = []
    report_nos = []
    
    for i, chunk in enumerate(chunk_results):
        chunk_num = i + 1
        if not chunk.get('success'):
            continue
        
        extracted = chunk.get('extracted_fields', {})
        
        # Merge name field
        if extracted.get(name_field):
            all_names.append({
                'value': extracted[name_field],
                'chunk': chunk_num
            })
        
        # Merge no field
        if extracted.get(no_field):
            report_nos.append(extracted[no_field])
        
        # Merge other common fields
        if extracted.get('issued_by') and not merged['issued_by']:
            merged['issued_by'] = extracted['issued_by']
        
        if extracted.get('issued_date') and not merged['issued_date']:
            merged['issued_date'] = extracted['issued_date']
        
        if extracted.get('ship_name') and not merged['ship_name']:
            merged['ship_name'] = extracted['ship_name']
        
        if extracted.get('ship_imo') and not merged['ship_imo']:
            merged['ship_imo'] = extracted['ship_imo']
    
    # Select most common name
    if all_names:
        merged[name_field] = all_names[0]['value']
        logger.info(f"  📝 {name_field}: '{merged[name_field]}' (from chunk {all_names[0]['chunk']})")
    
    # Select most common no
    if report_nos:
        from collections import Counter
        report_no_counts = Counter(report_nos)
        merged[no_field] = max(report_no_counts, key=report_no_counts.get)
        logger.info(f"  🔢 {no_field}: '{merged[no_field]}' (appears in {report_no_counts[merged[no_field]]} chunk(s))")
    
    return merged
```

#### C. Refactor `create_enhanced_merged_summary()`

**Changes:**

```python
# BEFORE:
def create_enhanced_merged_summary(
    chunk_results: List[Dict],
    merged_data: Dict,
    original_filename: str,
    total_pages: int
) -> str:
    # Hardcoded labels
    summary_lines.append(f"Survey Report Name: {merged_data.get('survey_report_name', 'N/A')}")
    summary_lines.append(f"Report Number: {merged_data.get('survey_report_no', 'N/A')}")

# AFTER:
def create_enhanced_merged_summary(
    chunk_results: List[Dict],
    merged_data: Dict,
    original_filename: str,
    total_pages: int,
    document_type: str = 'survey_report'  # ✅ NEW parameter
) -> str:
    """
    Create enhanced merged summary from chunk results
    
    Args:
        chunk_results: List of chunk results
        merged_data: Merged data dictionary
        original_filename: Original PDF filename
        total_pages: Total page count
        document_type: Type of document ('survey_report', 'test_report', etc.)
    
    Returns:
        Enhanced merged summary text
    """
    
    # ✅ Define label mappings per document type
    LABEL_MAPPINGS = {
        'survey_report': {
            'title': 'MERGED SURVEY REPORT ANALYSIS',
            'name_label': 'Survey Report Name',
            'name_field': 'survey_report_name',
            'no_label': 'Report Number',
            'no_field': 'survey_report_no'
        },
        'test_report': {
            'title': 'MERGED TEST REPORT ANALYSIS',
            'name_label': 'Test Report Name',
            'name_field': 'test_report_name',
            'no_label': 'Test Report Number',
            'no_field': 'test_report_no'
        },
        'audit_report': {
            'title': 'MERGED AUDIT REPORT ANALYSIS',
            'name_label': 'Audit Report Name',
            'name_field': 'audit_report_name',
            'no_label': 'Report Number',
            'no_field': 'audit_report_no'
        }
    }
    
    if document_type not in LABEL_MAPPINGS:
        raise ValueError(f"Unsupported document_type: {document_type}")
    
    mapping = LABEL_MAPPINGS[document_type]
    
    summary_parts = []
    
    # Header
    summary_parts.append("="*80)
    summary_parts.append(mapping['title'])
    summary_parts.append("="*80)
    summary_parts.append(f"Original File: {original_filename}")
    summary_parts.append(f"Total Pages: {total_pages}")
    summary_parts.append(f"Chunks Processed: {len(chunk_results)}")
    summary_parts.append("")
    
    # Key Fields (dynamic)
    summary_parts.append("--- KEY EXTRACTED FIELDS ---")
    summary_parts.append(f"{mapping['name_label']}: {merged_data.get(mapping['name_field'], 'N/A')}")
    summary_parts.append(f"{mapping['no_label']}: {merged_data.get(mapping['no_field'], 'N/A')}")
    summary_parts.append(f"Issued By: {merged_data.get('issued_by', 'N/A')}")
    summary_parts.append(f"Issued Date: {merged_data.get('issued_date', 'N/A')}")
    
    # Test Report specific field
    if document_type == 'test_report':
        summary_parts.append(f"Valid Date: {merged_data.get('valid_date', 'N/A')}")
    
    # Survey Report specific field
    if document_type == 'survey_report':
        summary_parts.append(f"Surveyor: {merged_data.get('surveyor_name', 'N/A')}")
    
    summary_parts.append("")
    
    # Individual Chunk Summaries
    summary_parts.append("="*80)
    summary_parts.append("DETAILED CONTENT FROM EACH CHUNK")
    summary_parts.append("="*80)
    
    for chunk_result in chunk_results:
        if chunk_result.get('success'):
            chunk_num = chunk_result.get('chunk_num', 0)
            page_range = chunk_result.get('page_range', '')
            summary_text = chunk_result.get('summary_text', '')
            
            summary_parts.append("")
            summary_parts.append(f"--- CHUNK {chunk_num} (Pages {page_range}) ---")
            summary_parts.append(summary_text)
            summary_parts.append("")
    
    # Footer
    summary_parts.append("="*80)
    summary_parts.append("END OF MERGED SUMMARY")
    summary_parts.append("="*80)
    
    return "\n".join(summary_parts)
```

#### D. Testing Task 1.1

**Test với Survey Report để đảm bảo backward compatibility:**

```python
# Test script: test_pdf_splitter_refactor.py

import asyncio
from app.utils.pdf_splitter import PDFSplitter, merge_analysis_results, create_enhanced_merged_summary

# Mock data
chunk_results_survey = [
    {
        'success': True,
        'chunk_num': 1,
        'page_range': '1-12',
        'summary_text': 'Chunk 1 summary...',
        'extracted_fields': {
            'survey_report_name': 'cargo gear',
            'survey_report_no': 'A/25/772',
            'issued_by': "Lloyd's Register",
            'issued_date': '2024-01-15'
        }
    },
    {
        'success': True,
        'chunk_num': 2,
        'page_range': '13-24',
        'summary_text': 'Chunk 2 summary...',
        'extracted_fields': {
            'survey_report_name': 'cargo gear',
            'survey_report_no': 'A/25/772'
        }
    }
]

# Test Survey Report (backward compatibility)
print("Testing Survey Report...")
merged_survey = merge_analysis_results(chunk_results_survey, document_type='survey_report')
print(f"✅ Merged survey_report_name: {merged_survey.get('survey_report_name')}")
print(f"✅ Merged survey_report_no: {merged_survey.get('survey_report_no')}")

summary_survey = create_enhanced_merged_summary(
    chunk_results_survey, 
    merged_survey, 
    'test_survey.pdf', 
    24,
    document_type='survey_report'
)
print(f"✅ Summary length: {len(summary_survey)} chars")

# Test Test Report (new)
chunk_results_test = [
    {
        'success': True,
        'chunk_num': 1,
        'page_range': '1-12',
        'summary_text': 'Test chunk 1...',
        'extracted_fields': {
            'test_report_name': 'EEBD',
            'test_report_no': 'TR-2024-001',
            'issued_by': 'VITECH',
            'issued_date': '2024-01-15'
        }
    }
]

print("\nTesting Test Report...")
merged_test = merge_analysis_results(chunk_results_test, document_type='test_report')
print(f"✅ Merged test_report_name: {merged_test.get('test_report_name')}")
print(f"✅ Merged test_report_no: {merged_test.get('test_report_no')}")

summary_test = create_enhanced_merged_summary(
    chunk_results_test,
    merged_test,
    'test_eebd.pdf',
    12,
    document_type='test_report'
)
print(f"✅ Summary length: {len(summary_test)} chars")

print("\n✅ All tests passed!")
```

**Checklist Task 1.1:**
- [ ] Backup original file
- [ ] Refactor `merge_analysis_results()` với parameter `document_type`
- [ ] Refactor `create_enhanced_merged_summary()` với parameter `document_type`
- [ ] Add FIELD_MAPPINGS và LABEL_MAPPINGS dictionaries
- [ ] Chạy test script
- [ ] Verify Survey Report vẫn hoạt động bình thường
- [ ] Verify Test Report có thể sử dụng functions mới

---

### TASK 1.2: Refactor Targeted OCR (3-4 giờ)

#### A. Backup hiện tại
```bash
cp /app/backend/app/utils/targeted_ocr.py /app/backend/app/utils/targeted_ocr.py.backup
```

#### B. Refactor `extract_from_pdf()`

**File:** `/app/backend/app/utils/targeted_ocr.py`

**Changes:**

```python
# BEFORE:
def extract_from_pdf(self, pdf_content: bytes, page_num: int = 0) -> Dict:
    # ...
    return {
        'report_form': report_form,
        'survey_report_no': survey_report_no,  # ⚠️ Hardcoded
        'header_text': header_text,
        'footer_text': footer_text,
        'ocr_success': True
    }

# AFTER:
def extract_from_pdf(
    self, 
    pdf_content: bytes, 
    page_num: int = 0,
    report_no_field: str = 'survey_report_no'  # ✅ NEW parameter
) -> Dict:
    """
    Extract report form and report number from PDF header/footer
    
    Args:
        pdf_content: PDF file bytes
        page_num: Page number to extract from (0-indexed)
        report_no_field: Field name for report number
            - 'survey_report_no' for Survey Reports
            - 'test_report_no' for Test Reports
            - 'audit_report_no' for Audit Reports
    
    Returns:
        Dict with:
        {
            'report_form': str or None,
            report_no_field: str or None,  # Dynamic field name
            'header_text': str,
            'footer_text': str,
            'ocr_success': bool
        }
    """
    
    result = {
        'report_form': None,
        report_no_field: None,  # ✅ Dynamic field name
        'header_text': '',
        'footer_text': '',
        'ocr_success': False,
        'ocr_error': None
    }
    
    try:
        # Convert PDF to image
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(
            pdf_content,
            first_page=page_num + 1,
            last_page=page_num + 1,
            dpi=300
        )
        
        if not images:
            result['ocr_error'] = 'Failed to convert PDF to image'
            return result
        
        page_image = images[0]
        
        # Extract header and footer
        header_text = self._extract_header(page_image)
        footer_text = self._extract_footer(page_image)
        
        result['header_text'] = header_text
        result['footer_text'] = footer_text
        
        # Combine for pattern matching
        combined_text = header_text + "\n" + footer_text
        
        # Extract report form
        report_form = self._extract_report_form(combined_text)
        if report_form:
            result['report_form'] = report_form
            logger.info(f"✅ Extracted report_form: '{report_form}'")
        
        # Extract report number (dynamic field name)
        report_no = self._extract_report_no(combined_text)
        if report_no:
            result[report_no_field] = report_no  # ✅ Dynamic assignment
            logger.info(f"✅ Extracted {report_no_field}: '{report_no}'")
        
        result['ocr_success'] = True
        
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        result['ocr_error'] = str(e)
    
    return result
```

#### C. Refactor `merge_document_ai_and_ocr()`

**Changes:**

```python
# BEFORE:
def merge_document_ai_and_ocr(
    self,
    doc_ai_result: Dict,
    ocr_result: Dict
) -> Dict:
    merged = {
        'report_form': None,
        'survey_report_no': None,  # ⚠️ Hardcoded
        # ...
    }

# AFTER:
def merge_document_ai_and_ocr(
    self,
    doc_ai_result: Dict,
    ocr_result: Dict,
    report_no_field: str = 'survey_report_no'  # ✅ NEW parameter
) -> Dict:
    """
    Merge Document AI and OCR results
    
    Args:
        doc_ai_result: Document AI extraction results
        ocr_result: OCR extraction results
        report_no_field: Field name for report number
    
    Returns:
        Merged results with source tracking
    """
    
    merged = {
        'report_form': None,
        report_no_field: None,  # ✅ Dynamic
        'report_form_source': 'none',
        'report_form_confidence': 'none',
        f'{report_no_field}_source': 'none',  # ✅ Dynamic
        f'{report_no_field}_confidence': 'none'  # ✅ Dynamic
    }
    
    # Extract values
    doc_form = (doc_ai_result.get('report_form') or '').strip()
    ocr_form = (ocr_result.get('report_form') or '').strip()
    
    doc_no = (doc_ai_result.get(report_no_field) or '').strip()  # ✅ Dynamic
    ocr_no = (ocr_result.get(report_no_field) or '').strip()  # ✅ Dynamic
    
    # Merge report_form (same logic)
    if doc_form and ocr_form:
        if doc_form.lower() == ocr_form.lower():
            merged['report_form'] = doc_form
            merged['report_form_source'] = 'both'
            merged['report_form_confidence'] = 'high'
        else:
            merged['report_form'] = doc_form
            merged['report_form_source'] = 'document_ai'
            merged['report_form_confidence'] = 'low'
    elif doc_form:
        merged['report_form'] = doc_form
        merged['report_form_source'] = 'document_ai'
        merged['report_form_confidence'] = 'medium'
    elif ocr_form:
        merged['report_form'] = ocr_form
        merged['report_form_source'] = 'ocr'
        merged['report_form_confidence'] = 'medium'
    
    # Merge report_no (dynamic field)
    if doc_no and ocr_no:
        if self._normalize_report_no(doc_no) == self._normalize_report_no(ocr_no):
            merged[report_no_field] = doc_no
            merged[f'{report_no_field}_source'] = 'both'
            merged[f'{report_no_field}_confidence'] = 'high'
        else:
            merged[report_no_field] = doc_no
            merged[f'{report_no_field}_source'] = 'document_ai'
            merged[f'{report_no_field}_confidence'] = 'low'
            logger.warning(f"⚠️ {report_no_field} mismatch: Document AI='{doc_no}' vs OCR='{ocr_no}'")
    elif doc_no:
        merged[report_no_field] = doc_no
        merged[f'{report_no_field}_source'] = 'document_ai'
        merged[f'{report_no_field}_confidence'] = 'medium'
    elif ocr_no:
        merged[report_no_field] = ocr_no
        merged[f'{report_no_field}_source'] = 'ocr'
        merged[f'{report_no_field}_confidence'] = 'medium'
    
    return merged
```

#### D. Testing Task 1.2

**Test script:**

```python
# test_targeted_ocr_refactor.py

from app.utils.targeted_ocr import get_ocr_processor

ocr_processor = get_ocr_processor()

# Test Survey Report
print("Testing Survey Report OCR...")
survey_result = ocr_processor.extract_from_pdf(
    survey_pdf_content,
    page_num=0,
    report_no_field='survey_report_no'  # ✅ Explicit
)
print(f"✅ survey_report_no: {survey_result.get('survey_report_no')}")
print(f"✅ report_form: {survey_result.get('report_form')}")

# Test Test Report
print("\nTesting Test Report OCR...")
test_result = ocr_processor.extract_from_pdf(
    test_pdf_content,
    page_num=0,
    report_no_field='test_report_no'  # ✅ New
)
print(f"✅ test_report_no: {test_result.get('test_report_no')}")
print(f"✅ report_form: {test_result.get('report_form')}")

# Test merge function
print("\nTesting merge...")
merged = ocr_processor.merge_document_ai_and_ocr(
    doc_ai_result={'test_report_no': 'TR-001'},
    ocr_result={'test_report_no': 'TR-001'},
    report_no_field='test_report_no'
)
print(f"✅ Merged: {merged}")

print("\n✅ All OCR tests passed!")
```

**Checklist Task 1.2:**
- [ ] Backup original file
- [ ] Refactor `extract_from_pdf()` với parameter `report_no_field`
- [ ] Refactor `merge_document_ai_and_ocr()` với parameter `report_no_field`
- [ ] Update return dictionary với dynamic field names
- [ ] Chạy test script
- [ ] Verify Survey Report vẫn hoạt động
- [ ] Verify Test Report có thể sử dụng

---

### TASK 1.3: Refactor Document AI Helper (2-3 giờ)

#### A. Backup hiện tại
```bash
cp /app/backend/app/utils/document_ai_helper.py /app/backend/app/utils/document_ai_helper.py.backup
```

#### B. Create Generic Function + Wrappers

**File:** `/app/backend/app/utils/document_ai_helper.py`

**Changes:**

```python
# BEFORE:
async def analyze_survey_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    # ...
    payload = {
        # ...
        "document_type": "survey_report"  # ⚠️ Hardcoded
    }

# AFTER: Add generic core function
async def analyze_document_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any],
    document_type: str  # ✅ NEW required parameter
) -> Dict[str, Any]:
    """
    Generic Document AI analysis for any document type
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type
        document_ai_config: Config with project_id, processor_id, location, apps_script_url
        document_type: Type of document
            - 'survey_report'
            - 'test_report'
            - 'audit_report'
            - 'drawings_manual'
            - 'approval_document'
            - etc.
    
    Returns:
        Dict with success status and summary text
    """
    try:
        # Extract config
        project_id = document_ai_config.get("project_id")
        processor_id = document_ai_config.get("processor_id")
        location = document_ai_config.get("location", "us")
        apps_script_url = document_ai_config.get("apps_script_url")
        
        if not project_id or not processor_id:
            return {
                "success": False,
                "message": "Missing Document AI configuration"
            }
        
        if not apps_script_url:
            return {
                "success": False,
                "message": "Missing Apps Script URL"
            }
        
        logger.info(f"🤖 Calling Google Document AI for {document_type}: {filename}")
        
        # Encode file to base64
        import base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Prepare request payload
        payload = {
            "action": "analyzeDocumentOnly",
            "fileName": filename,
            "fileContent": file_base64,
            "contentType": content_type,
            "documentAiConfig": {
                "projectId": project_id,
                "processorId": processor_id,
                "location": location
            },
            "document_type": document_type  # ✅ Dynamic
        }
        
        # Call Apps Script
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                apps_script_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Apps Script error: {error_text}")
                    return {
                        "success": False,
                        "message": f"Apps Script returned {response.status}"
                    }
                
                result = await response.json()
        
        # Check result
        if result.get('success'):
            summary_text = result.get('summary', '')
            logger.info(f"✅ Document AI success: {len(summary_text)} chars")
            
            return {
                "success": True,
                "summary_text": summary_text
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ Document AI failed: {error_msg}")
            return {
                "success": False,
                "message": error_msg
            }
    
    except Exception as e:
        logger.error(f"❌ Document AI exception: {e}")
        return {
            "success": False,
            "message": str(e)
        }


# ✅ Keep backward-compatible wrapper for Survey Report
async def analyze_survey_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze survey report using Document AI
    (Wrapper for backward compatibility)
    """
    return await analyze_document_with_document_ai(
        file_content,
        filename,
        content_type,
        document_ai_config,
        document_type='survey_report'
    )


# ✅ Add new wrapper for Test Report
async def analyze_test_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze test report using Document AI
    """
    return await analyze_document_with_document_ai(
        file_content,
        filename,
        content_type,
        document_ai_config,
        document_type='test_report'
    )


# ✅ Add wrapper for Audit Report
async def analyze_audit_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze audit report using Document AI
    """
    return await analyze_document_with_document_ai(
        file_content,
        filename,
        content_type,
        document_ai_config,
        document_type='audit_report'
    )
```

#### C. Testing Task 1.3

**Test script:**

```python
# test_document_ai_refactor.py

from app.utils.document_ai_helper import (
    analyze_document_with_document_ai,
    analyze_survey_report_with_document_ai,
    analyze_test_report_with_document_ai
)

# Mock config
doc_ai_config = {
    "project_id": "test-project",
    "processor_id": "test-processor",
    "location": "us",
    "apps_script_url": "https://script.google.com/..."
}

# Test generic function
print("Testing generic function...")
result = await analyze_document_with_document_ai(
    pdf_content,
    'test.pdf',
    'application/pdf',
    doc_ai_config,
    document_type='test_report'
)
print(f"✅ Result: {result.get('success')}")

# Test Survey Report wrapper (backward compatibility)
print("\nTesting Survey Report wrapper...")
survey_result = await analyze_survey_report_with_document_ai(
    pdf_content,
    'survey.pdf',
    'application/pdf',
    doc_ai_config
)
print(f"✅ Survey result: {survey_result.get('success')}")

# Test Test Report wrapper (new)
print("\nTesting Test Report wrapper...")
test_result = await analyze_test_report_with_document_ai(
    pdf_content,
    'test.pdf',
    'application/pdf',
    doc_ai_config
)
print(f"✅ Test result: {test_result.get('success')}")

print("\n✅ All Document AI tests passed!")
```

**Checklist Task 1.3:**
- [ ] Backup original file
- [ ] Create `analyze_document_with_document_ai()` generic function
- [ ] Keep `analyze_survey_report_with_document_ai()` as wrapper
- [ ] Add `analyze_test_report_with_document_ai()` wrapper
- [ ] Add `analyze_audit_report_with_document_ai()` wrapper
- [ ] Chạy test script
- [ ] Verify Survey Report vẫn hoạt động
- [ ] Verify Test Report có thể sử dụng

---

### TASK 1.4: Update Survey Report Service để dùng refactored utilities (1-2 giờ)

**File:** `/app/backend/app/services/survey_report_analyze_service.py`

**Changes:**

```python
# Cập nhật các function calls để truyền document_type parameter

# BEFORE:
merged_data = merge_analysis_results(chunk_results)

# AFTER:
merged_data = merge_analysis_results(chunk_results, document_type='survey_report')

# BEFORE:
merged_summary = create_enhanced_merged_summary(
    chunk_results, merged_data, filename, total_pages
)

# AFTER:
merged_summary = create_enhanced_merged_summary(
    chunk_results, merged_data, filename, total_pages, document_type='survey_report'
)

# BEFORE:
ocr_result = ocr_processor.extract_from_pdf(file_content, page_num=0)

# AFTER:
ocr_result = ocr_processor.extract_from_pdf(
    file_content, 
    page_num=0,
    report_no_field='survey_report_no'
)

# BEFORE:
merged_ocr = ocr_processor.merge_document_ai_and_ocr(doc_ai_result, ocr_result)

# AFTER:
merged_ocr = ocr_processor.merge_document_ai_and_ocr(
    doc_ai_result,
    ocr_result,
    report_no_field='survey_report_no'
)
```

**Checklist Task 1.4:**
- [ ] Update tất cả calls trong `survey_report_analyze_service.py`
- [ ] Thêm parameter `document_type='survey_report'`
- [ ] Thêm parameter `report_no_field='survey_report_no'`
- [ ] Test Survey Report flow end-to-end
- [ ] Verify không có regression

---

### TASK 1.5: Comprehensive Testing Phase 1 (2-3 giờ)

#### A. Unit Tests

Tạo file: `/app/backend/tests/test_utilities_refactor.py`

```python
import pytest
from app.utils.pdf_splitter import merge_analysis_results, create_enhanced_merged_summary
from app.utils.targeted_ocr import get_ocr_processor

class TestPDFSplitterRefactor:
    """Test refactored PDF splitter"""
    
    def test_merge_survey_report(self):
        """Test merge với Survey Report"""
        chunk_results = [
            {
                'success': True,
                'chunk_num': 1,
                'extracted_fields': {
                    'survey_report_name': 'cargo gear',
                    'survey_report_no': 'A/25/772'
                }
            }
        ]
        
        merged = merge_analysis_results(chunk_results, document_type='survey_report')
        
        assert merged['survey_report_name'] == 'cargo gear'
        assert merged['survey_report_no'] == 'A/25/772'
    
    def test_merge_test_report(self):
        """Test merge với Test Report"""
        chunk_results = [
            {
                'success': True,
                'chunk_num': 1,
                'extracted_fields': {
                    'test_report_name': 'EEBD',
                    'test_report_no': 'TR-2024-001'
                }
            }
        ]
        
        merged = merge_analysis_results(chunk_results, document_type='test_report')
        
        assert merged['test_report_name'] == 'EEBD'
        assert merged['test_report_no'] == 'TR-2024-001'
    
    def test_invalid_document_type(self):
        """Test với invalid document_type"""
        with pytest.raises(ValueError):
            merge_analysis_results([], document_type='invalid_type')

class TestTargetedOCRRefactor:
    """Test refactored Targeted OCR"""
    
    def test_extract_with_survey_field(self):
        """Test extract với survey_report_no field"""
        # Mock test
        pass
    
    def test_extract_with_test_field(self):
        """Test extract với test_report_no field"""
        # Mock test
        pass
```

Chạy tests:
```bash
cd /app/backend
pytest tests/test_utilities_refactor.py -v
```

#### B. Integration Tests

Test với real Survey Report flow:

```bash
# Manually test Survey Report upload
# 1. Upload a Survey Report PDF
# 2. Verify AI analysis works
# 3. Verify file upload works
# 4. Check logs for any errors
```

**Checklist Task 1.5:**
- [ ] Viết unit tests cho refactored utilities
- [ ] Chạy unit tests và fix bugs
- [ ] Test Survey Report flow end-to-end
- [ ] Verify không có regression
- [ ] Document any issues found

---

## 📅 PHASE 2: MIGRATE TEST REPORT CORE LOGIC (3-4 NGÀY)

### Objective: Migrate analyze-file, upload-files, Valid Date Calculator, AI extraction prompt

---

### TASK 2.1: Create Test Report AI Extraction Module (4-5 giờ)

#### A. Create file: `/app/backend/app/utils/test_report_ai.py`

Port from V1: `backend-v1/server.py` (line 8162-8341 và 7783-7858)

**File structure:**

```python
"""
Test Report AI Extraction Module
Handles System AI extraction for Test Reports
"""
import logging
import json
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def create_test_report_extraction_prompt(summary_text: str) -> str:
    """
    Create extraction prompt for test report fields
    
    Port from backend-v1/server.py line 8162-8341
    """
    try:
        prompt = f"""
You are a maritime test report data extraction expert. Extract the following information from the test report summary below.

=== FIELDS TO EXTRACT ===

**test_report_name**: 
- This report is about MAINTENANCE/TESTING of LIFESAVING and FIREFIGHTING EQUIPMENT on ships
- Extract the EQUIPMENT NAME that is being tested/maintained, NOT the test type
- Common equipment names to look for:
  * EEBD (Emergency Escape Breathing Device)
  * SCBA (Self-Contained Breathing Apparatus)
  * Portable Fire Extinguisher
  * Portable Foam Applicator
  * Life Raft / Liferaft
  * Lifeboat / Rescue Boat
  * CO2 System / Carbon Dioxide System
  * Fire Detection System / Fire Alarm System
  * Gas Detector / Gas Detection System
  * Immersion Suit / Survival Suit
  * Life Jacket / Lifejacket / Life Vest
  * Hydrostatic Release Unit (HRU)
  * EPIRB (Emergency Position Indicating Radio Beacon)
  * SART (Search and Rescue Transponder)
  * Fire Hose / Fire Fighting Hose
  * Fireman Outfit / Fireman's Outfit
  * Breathing Apparatus
  * Fixed Fire Extinguishing System
  * Sprinkler System
  * Emergency Fire Pump
  * Davit / Launching Appliance
  
- Return ONLY the equipment name (e.g., "EEBD", "Life Raft", "Portable Fire Extinguisher")
- Do NOT add "Test" or "Report" to the name

**report_form**: 
- Extract the SERVICE CHART or FORM used for this maintenance/inspection
- Look for patterns like:
  * "Service Chart [LETTER]" - e.g., "Service Chart A", "Service Chart K"
  * "Service Charts [LETTER]/[LETTER]" - e.g., "Service Charts H1/H2"
  * "SERVICE CHART [CODE]"
  * "Chart [CODE]"
  * "Form [NUMBER/LETTER]"
- Extract complete chart/form identifier exactly as written

**test_report_no**: 
- Extract the test report number or certificate number
- Look for "Test Report No.", "Certificate Number", "Report No."
- Common formats: "TR-2024-001", "CERT-123", "TEST/2024/456"

**issued_by**: 
- Extract who issued or conducted the test/maintenance
- **IMPORTANT: Extract ONLY the SHORT NAME, NOT the full legal company name**
- Rules:
  * ✅ "VITECH" (NOT "VITECH Technologies and Services JSC")
  * ✅ "Lloyd's Register" or "LR"
  * ✅ "DNV" (NOT "Det Norske Veritas")
  * ✅ "ABS" (NOT "American Bureau of Shipping")
- Remove legal suffixes: JSC, LLC, Inc., Co., Ltd., Corporation

**issued_date**: 
- Extract ACTUAL DATE when the inspection/maintenance was performed
- Look for "underwent inspection on [DATE]", "inspected on [DATE]", "serviced on [DATE]"
- **DO NOT extract date from:**
  * "Rev XX, issued by [COMPANY] on [DATE]" - form revision date
  * "Form issued on [DATE]" - form template date
- Focus on date when ACTUAL WORK was performed
- Format: YYYY-MM-DD

**valid_date**: 
- Extract the expiry date or next test due date
- Look for "Valid Until", "Expiry Date", "Next Test Due", "Expires"
- Format: YYYY-MM-DD

**ship_name**: 
- Extract the ship/vessel name
- Look for "Vessel Name", "Ship Name", "M/V", "MV"

**ship_imo**: 
- Extract the IMO number (7-digit number)
- Look for "IMO No.", "IMO Number"

**note**: 
- Extract any important notes, remarks, observations, or conditions
- Include test results, compliance status, special conditions

=== OUTPUT FORMAT ===
Return ONLY a JSON object with these exact field names:
{{
  "test_report_name": "",
  "report_form": "",
  "test_report_no": "",
  "issued_by": "",
  "issued_date": "",
  "valid_date": "",
  "ship_name": "",
  "ship_imo": "",
  "note": ""
}}

**IMPORTANT:**
- For test_report_name: Return ONLY the equipment name (e.g., "EEBD"), NOT "EEBD Test"
- Return ONLY the JSON object, no additional text
- Use empty string "" if information is not found
- Dates should be in YYYY-MM-DD format if possible

=== TEST REPORT SUMMARY ===
{summary_text}

=== YOUR JSON RESPONSE ===
"""
        return prompt
        
    except Exception as e:
        logger.error(f"Error creating test report extraction prompt: {e}")
        return ""


async def extract_test_report_fields_from_summary(
    summary_text: str,
    ai_provider: str,
    ai_model: str,
    use_emergent_key: bool
) -> dict:
    """
    Extract test report fields from Document AI summary using System AI
    
    Port from backend-v1/server.py line 7783-7858
    
    Args:
        summary_text: Document AI summary + OCR text
        ai_provider: AI provider ("google", "openai", etc.)
        ai_model: Model name ("gemini-2.0-flash-exp", etc.)
        use_emergent_key: Whether to use Emergent LLM key
    
    Returns:
        Extracted fields dictionary
    """
    try:
        logger.info("🤖 Extracting test report fields from summary")
        
        # Create extraction prompt
        prompt = create_test_report_extraction_prompt(summary_text)
        
        if not prompt:
            logger.error("Failed to create test report extraction prompt")
            return {}
        
        # Use System AI for extraction
        if use_emergent_key and ai_provider in ["google", "emergent"]:
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                from app.utils.emergent_key import get_emergent_llm_key
                
                emergent_key = get_emergent_llm_key()
                chat = LlmChat(
                    api_key=emergent_key,
                    session_id=f"test_report_extraction_{int(time.time())}",
                    system_message="You are a maritime test report analysis expert."
                ).with_model("gemini", ai_model)
                
                logger.info(f"📤 Sending extraction prompt to {ai_model}...")
                
                user_message = UserMessage(text=prompt)
                ai_response = await chat.send_message(user_message)
                
                if ai_response and ai_response.strip():
                    content = ai_response.strip()
                    logger.info("🤖 Test Report AI response received")
                    
                    # Parse JSON response
                    try:
                        clean_content = content.replace('```json', '').replace('```', '').strip()
                        extracted_data = json.loads(clean_content)
                        
                        # Standardize date formats
                        for date_field in ['issued_date', 'valid_date']:
                            if extracted_data.get(date_field):
                                try:
                                    from dateutil import parser
                                    parsed_date = parser.parse(extracted_data[date_field])
                                    extracted_data[date_field] = parsed_date.strftime('%Y-%m-%d')
                                except Exception as date_error:
                                    logger.warning(f"Failed to parse {date_field}: {date_error}")
                        
                        logger.info("✅ Successfully extracted test report fields")
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
        logger.error(f"Error in extract_test_report_fields_from_summary: {e}")
        return {}
```

**Checklist Task 2.1:**
- [ ] Create `/app/backend/app/utils/test_report_ai.py`
- [ ] Port `create_test_report_extraction_prompt()` từ V1
- [ ] Port `extract_test_report_fields_from_summary()` từ V1
- [ ] Test prompt generation
- [ ] Test extraction với mock data
- [ ] Verify JSON parsing logic

---

### TASK 2.2: Create Valid Date Calculator (3-4 giờ)

#### A. Create file: `/app/backend/app/utils/test_report_valid_date_calculator.py`

Port from V1: `backend-v1/test_report_valid_date_calculator.py`

**File structure:**

```python
"""
Test Report Valid Date Calculator
Calculates valid_date based on equipment type and issued_date
"""
import logging
from datetime import datetime
from typing import Optional, Dict
from dateutil import parser
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

# Default maintenance intervals (in months) for each equipment type
DEFAULT_INTERVALS = {
    # 12 months interval
    'eebd': 12,
    'emergency escape breathing device': 12,
    'scba': 12,
    'self-contained breathing apparatus': 12,
    'self contained breathing apparatus': 12,
    'portable fire extinguisher': 12,
    'fire extinguisher': 12,
    'life raft': 12,
    'liferaft': 12,
    'lifeboat': 12,
    'rescue boat': 12,
    'co2 system': 12,
    'carbon dioxide system': 12,
    'fire detection system': 12,
    'fire alarm system': 12,
    'gas detector': 12,
    'gas detection system': 12,
    'sart': 12,
    'search and rescue transponder': 12,
    'fire hose': 12,
    'fire fighting hose': 12,
    'fireman outfit': 12,
    "fireman's outfit": 12,
    'breathing apparatus': 12,
    'fixed fire extinguishing system': 12,
    'sprinkler system': 12,
    'emergency fire pump': 12,
    
    # 24 months interval
    'epirb': 24,
    'emergency position indicating radio beacon': 24,
    
    # 36 months interval (3 years)
    'immersion suit': 36,
    'survival suit': 36,
    'life jacket': 36,
    'lifejacket': 36,
    'life vest': 36,
    
    # 60 months interval (5 years)
    'davit': 60,
    'launching appliance': 60,
}


async def calculate_valid_date(
    test_report_name: str,
    issued_date: str,
    ship_id: str,
    mongo_db
) -> Optional[str]:
    """
    Calculate valid date based on equipment type and issued date
    
    Args:
        test_report_name: Equipment name (e.g., "EEBD", "Life Raft")
        issued_date: Issued date (ISO format or any parseable format)
        ship_id: Ship ID (to get ship-specific intervals)
        mongo_db: MongoDB instance
    
    Returns:
        Valid date in ISO format (YYYY-MM-DD) or None if calculation fails
    """
    try:
        logger.info(f"🧮 Calculating valid date for: {test_report_name}, issued: {issued_date}")
        
        # Parse issued date
        try:
            issued_date_obj = parser.parse(issued_date)
        except Exception as e:
            logger.error(f"Failed to parse issued_date '{issued_date}': {e}")
            return None
        
        # Normalize equipment name for lookup
        equipment_name_normalized = test_report_name.lower().strip()
        
        # Try to get ship-specific interval
        interval_months = None
        
        try:
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if ship:
                test_report_intervals = ship.get("test_report_intervals", {})
                
                # Try exact match first
                if equipment_name_normalized in test_report_intervals:
                    interval_months = test_report_intervals[equipment_name_normalized]
                    logger.info(f"✅ Found ship-specific interval: {interval_months} months")
                else:
                    # Try partial match
                    for key, value in test_report_intervals.items():
                        if key in equipment_name_normalized or equipment_name_normalized in key:
                            interval_months = value
                            logger.info(f"✅ Found ship-specific interval (partial match): {interval_months} months")
                            break
        except Exception as e:
            logger.warning(f"Could not fetch ship-specific intervals: {e}")
        
        # If no ship-specific interval, use default
        if interval_months is None:
            # Try exact match in default intervals
            if equipment_name_normalized in DEFAULT_INTERVALS:
                interval_months = DEFAULT_INTERVALS[equipment_name_normalized]
                logger.info(f"✅ Using default interval: {interval_months} months")
            else:
                # Try partial match in default intervals
                for key, value in DEFAULT_INTERVALS.items():
                    if key in equipment_name_normalized or equipment_name_normalized in key:
                        interval_months = value
                        logger.info(f"✅ Using default interval (partial match): {interval_months} months")
                        break
                
                # If still not found, use default 12 months
                if interval_months is None:
                    interval_months = 12
                    logger.warning(f"⚠️ No interval found for '{test_report_name}', using default 12 months")
        
        # Calculate valid date
        valid_date_obj = issued_date_obj + relativedelta(months=interval_months)
        
        # Return in ISO format
        valid_date_str = valid_date_obj.strftime('%Y-%m-%d')
        logger.info(f"✅ Calculated valid date: {valid_date_str} ({interval_months} months from {issued_date})")
        
        return valid_date_str
        
    except Exception as e:
        logger.error(f"❌ Error calculating valid date: {e}")
        return None


def get_default_interval(equipment_name: str) -> int:
    """
    Get default interval for equipment type (utility function)
    
    Args:
        equipment_name: Equipment name
    
    Returns:
        Interval in months (default 12 if not found)
    """
    equipment_name_normalized = equipment_name.lower().strip()
    
    # Try exact match
    if equipment_name_normalized in DEFAULT_INTERVALS:
        return DEFAULT_INTERVALS[equipment_name_normalized]
    
    # Try partial match
    for key, value in DEFAULT_INTERVALS.items():
        if key in equipment_name_normalized or equipment_name_normalized in key:
            return value
    
    # Default
    return 12
```

**Checklist Task 2.2:**
- [ ] Create `/app/backend/app/utils/test_report_valid_date_calculator.py`
- [ ] Port `calculate_valid_date()` từ V1
- [ ] Port `DEFAULT_INTERVALS` dictionary
- [ ] Add `get_default_interval()` utility function
- [ ] Test với các equipment types khác nhau
- [ ] Test ship-specific intervals
- [ ] Test default fallback

---

### TASK 2.3: Create Test Report Analyze Service (1 ngày)

#### A. Create file: `/app/backend/app/services/test_report_analyze_service.py`

**Tương tự như Survey Report Analyze Service, nhưng:**
1. Sử dụng `test_report` fields thay vì `survey_report`
2. Thêm Valid Date Calculator
3. Sử dụng test report AI extraction prompt

**File structure:**

```python
"""
Test Report Analyze Service
Handles AI analysis for Test Reports
"""
import logging
import base64
from typing import Dict, Any
from fastapi import HTTPException, UploadFile

from app.core.database import mongo_db
from app.models.user import UserResponse
from app.utils.pdf_splitter import PDFSplitter, merge_analysis_results, create_enhanced_merged_summary
from app.utils.targeted_ocr import get_ocr_processor
from app.utils.document_ai_helper import analyze_test_report_with_document_ai
from app.utils.test_report_ai import extract_test_report_fields_from_summary
from app.utils.test_report_valid_date_calculator import calculate_valid_date

logger = logging.getLogger(__name__)


class TestReportAnalyzeService:
    """Service for analyzing Test Report files"""
    
    @staticmethod
    async def analyze_file(
        file: UploadFile,
        ship_id: str,
        bypass_validation: bool,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        Analyze test report file using AI
        
        Process:
        1. Validate PDF
        2. Check page count for splitting
        3. Process with Document AI
        4. Perform Targeted OCR
        5. Extract fields with System AI
        6. Calculate Valid Date (UNIQUE TO TEST REPORT)
        7. Normalize issued_by
        8. Validate ship info
        9. Return analysis + file content
        """
        
        # Step 1: Read & validate file
        file_content = await file.read()
        filename = file.filename
        
        if not filename.lower().endswith('.pdf'):
            raise HTTPException(400, "Only PDF files supported")
        
        if not file_content.startswith(b'%PDF'):
            raise HTTPException(400, "Invalid PDF format")
        
        logger.info(f"📋 Analyzing Test Report: {filename} ({len(file_content)} bytes)")
        
        # Step 2: Check page count
        splitter = PDFSplitter(max_pages_per_chunk=12)
        
        try:
            total_pages = splitter.get_page_count(file_content)
            needs_split = splitter.needs_splitting(file_content)
            logger.info(f"📊 PDF: {total_pages} pages, Split needed: {needs_split}")
        except ValueError as e:
            raise HTTPException(400, f"Invalid PDF file: {str(e)}")
        
        # Step 3: Get ship & company info
        company_uuid = current_user.company
        
        ship = await mongo_db.find_one("ships", {"id": ship_id, "company": company_uuid})
        
        if not ship and not bypass_validation:
            raise HTTPException(404, "Ship not found")
        
        ship_name = ship.get("name", "Unknown Ship") if ship else "Unknown Ship"
        ship_imo = ship.get("imo", "") if ship else ""
        
        # Step 4: Get AI configuration
        ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
        if not ai_config_doc:
            raise HTTPException(404, "AI configuration not found")
        
        document_ai_config = ai_config_doc.get("document_ai", {})
        if not document_ai_config.get("enabled"):
            raise HTTPException(400, "Document AI not enabled")
        
        # Step 5: Initialize result & store file content
        analysis_result = {
            "test_report_name": "",
            "report_form": "",
            "test_report_no": "",
            "issued_by": "",
            "issued_date": "",
            "valid_date": "",
            "note": "",
            "ship_name": "",
            "ship_imo": "",
            "confidence_score": 0.0,
            "processing_method": "clean_analysis"
        }
        
        # CRITICAL: Store file content FIRST
        analysis_result['_file_content'] = base64.b64encode(file_content).decode('utf-8')
        analysis_result['_filename'] = filename
        analysis_result['_content_type'] = file.content_type
        analysis_result['_ship_name'] = ship_name
        analysis_result['_summary_text'] = ''
        
        # Step 6: Process based on PDF size
        if needs_split and total_pages > 15:
            # Large PDF: Split and process
            analysis_result = await TestReportAnalyzeService._process_large_pdf(
                file_content,
                filename,
                file.content_type,
                splitter,
                document_ai_config,
                ai_config_doc,
                analysis_result,
                total_pages
            )
        else:
            # Small PDF: Process normally
            analysis_result = await TestReportAnalyzeService._process_single_pdf(
                file_content,
                filename,
                file.content_type,
                document_ai_config,
                ai_config_doc,
                analysis_result,
                total_pages
            )
        
        # Step 7: Calculate Valid Date (UNIQUE TO TEST REPORT)
        logger.info("🧮 Calculating Valid Date...")
        
        test_report_name = analysis_result.get('test_report_name', '')
        issued_date = analysis_result.get('issued_date', '')
        
        if test_report_name and issued_date:
            calculated_valid_date = await calculate_valid_date(
                test_report_name=test_report_name,
                issued_date=issued_date,
                ship_id=ship_id,
                mongo_db=mongo_db
            )
            
            if calculated_valid_date:
                analysis_result['valid_date'] = calculated_valid_date
                logger.info(f"✅ Calculated Valid Date: {calculated_valid_date}")
        
        # Step 8: Normalize issued_by
        if analysis_result.get('issued_by'):
            from app.utils.issued_by_abbreviation import normalize_issued_by
            
            original = analysis_result['issued_by']
            normalized = normalize_issued_by(original)
            
            if normalized != original:
                analysis_result['issued_by'] = normalized
                logger.info(f"✅ Normalized Issued By: '{original}' → '{normalized}'")
        
        # Step 9: Validate ship info (if not bypassed)
        if not bypass_validation and ship:
            extracted_ship_name = analysis_result.get('ship_name', '').strip()
            extracted_ship_imo = analysis_result.get('ship_imo', '').strip()
            
            if extracted_ship_name or extracted_ship_imo:
                # Perform fuzzy matching (implement similar to Survey Report)
                # If mismatch, return validation_error
                pass
        
        # Step 10: Return analysis result
        logger.info("✅ Test report analysis completed successfully")
        return analysis_result
    
    
    @staticmethod
    async def _process_single_pdf(...):
        """Process small PDF (≤15 pages)"""
        # Similar to Survey Report logic
        # Use analyze_test_report_with_document_ai()
        # Use test_report OCR field names
        # Use extract_test_report_fields_from_summary()
        pass
    
    
    @staticmethod
    async def _process_large_pdf(...):
        """Process large PDF (>15 pages)"""
        # Similar to Survey Report logic
        # Split, process chunks, merge summaries
        # Use document_type='test_report' for merge functions
        pass
```

**Checklist Task 2.3:**
- [ ] Create `/app/backend/app/services/test_report_analyze_service.py`
- [ ] Implement `analyze_file()` method
- [ ] Implement `_process_single_pdf()` method
- [ ] Implement `_process_large_pdf()` method
- [ ] Integrate Valid Date Calculator
- [ ] Integrate Test Report AI extraction
- [ ] Add logging và error handling
- [ ] Test với mock data

---

### TASK 2.4: Update Test Report API Endpoint (1-2 giờ)

#### A. Update file: `/app/backend/app/api/v1/test_reports.py`

**Changes:**

```python
# BEFORE (skeleton):
@router.post("/analyze-file")
async def analyze_document_file(
    file: UploadFile = File(...),
    ship_id: Optional[str] = None,
    current_user: UserResponse = Depends(check_editor_permission)
):
    try:
        return await service.analyze_file(file, ship_id, current_user)
    except Exception as e:
        raise HTTPException(500, str(e))

# AFTER (full implementation):
@router.post("/analyze-file")
async def analyze_test_report_file(
    test_report_file: UploadFile = File(...),
    ship_id: str = Form(...),
    bypass_validation: str = Form("false"),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze test report file using AI
    
    Process:
    1. Validate PDF file
    2. Split if > 15 pages
    3. Process with Document AI + OCR
    4. Extract fields with System AI
    5. Calculate Valid Date
    6. Normalize issued_by
    7. Validate ship info
    8. Return analysis + file content (base64)
    """
    try:
        from app.services.test_report_analyze_service import TestReportAnalyzeService
        
        bypass_bool = bypass_validation.lower() == "true"
        
        result = await TestReportAnalyzeService.analyze_file(
            file=test_report_file,
            ship_id=ship_id,
            bypass_validation=bypass_bool,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing test report file: {e}")
        raise HTTPException(500, f"Failed to analyze test report: {str(e)}")
```

**Checklist Task 2.4:**
- [ ] Update `/app/backend/app/api/v1/test_reports.py`
- [ ] Change parameter names to match V1 (test_report_file, ship_id, bypass_validation)
- [ ] Import TestReportAnalyzeService
- [ ] Call analyze_file() method
- [ ] Add proper error handling
- [ ] Test endpoint với Postman/curl

---

### TASK 2.5: Migrate upload-files Endpoint (2-3 giờ)

#### A. Update Test Report Service

**File:** `/app/backend/app/services/test_report_service.py`

**Add method:**

```python
@staticmethod
async def upload_files(
    report_id: str,
    file_content: str,
    filename: str,
    content_type: str,
    summary_text: str,
    current_user: UserResponse
) -> Dict[str, Any]:
    """
    Upload test report files to Google Drive
    
    Port from backend-v1/server.py line 11646-11756
    """
    try:
        # Validate report exists
        report = await mongo_db.find_one("test_reports", {"id": report_id})
        if not report:
            raise HTTPException(404, "Test report not found")
        
        # Get ship info
        ship_id = report.get("ship_id")
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        
        ship_name = ship.get("name", "Unknown Ship")
        
        # Decode base64
        import base64
        try:
            file_bytes = base64.b64decode(file_content)
        except Exception as e:
            raise HTTPException(400, "Invalid file content encoding")
        
        # Get company UUID
        company_uuid = current_user.company
        
        # Upload files to Google Drive
        from app.services.gdrive_service import GoogleDriveService
        
        # Upload original file to: ShipName/Class & Flag Cert/Test Report/
        original_upload = await GoogleDriveService.upload_test_report_file(
            company_uuid=company_uuid,
            file_content=file_bytes,
            filename=filename,
            content_type=content_type,
            ship_name=ship_name
        )
        
        if not original_upload.get('success'):
            raise HTTPException(500, "Failed to upload original file")
        
        test_report_file_id = original_upload.get('test_report_file_id')
        
        # Upload summary file to: SUMMARY/Class & Flag Document/
        test_report_summary_file_id = None
        if summary_text and summary_text.strip():
            base_name = filename.rsplit('.', 1)[0]
            summary_filename = f"{base_name}_Summary.txt"
            
            summary_upload = await GoogleDriveService.upload_test_report_summary(
                company_uuid=company_uuid,
                summary_text=summary_text,
                filename=summary_filename,
                ship_name=ship_name
            )
            
            if summary_upload.get('success'):
                test_report_summary_file_id = summary_upload.get('summary_file_id')
        
        # Update record with file IDs
        from datetime import datetime, timezone
        update_data = {
            "test_report_file_id": test_report_file_id,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if test_report_summary_file_id:
            update_data["test_report_summary_file_id"] = test_report_summary_file_id
        
        await mongo_db.update("test_reports", {"id": report_id}, update_data)
        
        return {
            "success": True,
            "test_report_file_id": test_report_file_id,
            "test_report_summary_file_id": test_report_summary_file_id,
            "message": "Test report files uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading test report files: {e}")
        raise HTTPException(500, f"Failed to upload files: {str(e)}")
```

#### B. Add endpoint in API

**File:** `/app/backend/app/api/v1/test_reports.py`

**Add:**

```python
@router.post("/{report_id}/upload-files")
async def upload_test_report_files(
    report_id: str,
    file_content: str = Body(...),
    filename: str = Body(...),
    content_type: str = Body(...),
    summary_text: str = Body(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Upload test report files to Google Drive"""
    try:
        from app.services.test_report_service import TestReportService
        
        result = await TestReportService.upload_files(
            report_id=report_id,
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
        logger.error(f"Error uploading test report files: {e}")
        raise HTTPException(500, f"Failed to upload files: {str(e)}")
```

#### C. Check Google Drive Service

**File:** `/app/backend/app/services/gdrive_service.py`

**Ensure có methods:**

```python
@staticmethod
async def upload_test_report_file(
    company_uuid: str,
    file_content: bytes,
    filename: str,
    content_type: str,
    ship_name: str
) -> Dict[str, Any]:
    """Upload test report file to: ShipName/Class & Flag Cert/Test Report/"""
    # Similar to upload_survey_report_file
    # Different folder path
    pass

@staticmethod
async def upload_test_report_summary(
    company_uuid: str,
    summary_text: str,
    filename: str,
    ship_name: str
) -> Dict[str, Any]:
    """Upload summary to: SUMMARY/Class & Flag Document/"""
    # Similar to survey report summary upload
    pass
```

**Checklist Task 2.5:**
- [ ] Add `upload_files()` method in TestReportService
- [ ] Add endpoint `/api/test-reports/{report_id}/upload-files`
- [ ] Verify GoogleDriveService có test report methods
- [ ] Test upload flow end-to-end
- [ ] Verify files xuất hiện trên Google Drive

---

## 📅 PHASE 3: TESTING & VALIDATION (1-2 NGÀY)

### Objective: Test toàn bộ Test Report flow, fix bugs, verify với real-world PDFs

---

### TASK 3.1: End-to-End Testing (1 ngày)

#### A. Test với Small PDFs (≤15 pages)

**Test cases:**

1. **EEBD Test Report:**
   - Equipment: EEBD
   - Expected interval: 12 months
   - Verify valid_date calculation

2. **Life Raft Test Report:**
   - Equipment: Life Raft
   - Expected interval: 12 months
   - Verify valid_date calculation

3. **Immersion Suit Test Report:**
   - Equipment: Immersion Suit
   - Expected interval: 36 months
   - Verify valid_date calculation

4. **Davit Test Report:**
   - Equipment: Davit
   - Expected interval: 60 months
   - Verify valid_date calculation

**For each test case, verify:**
- [ ] AI analysis extracts correct equipment name
- [ ] Report Form extracted correctly
- [ ] Test Report No. extracted correctly
- [ ] Issued By extracted and normalized
- [ ] Issued Date extracted in ISO format
- [ ] Valid Date calculated correctly
- [ ] Ship validation works
- [ ] File upload to Google Drive succeeds
- [ ] Files appear in correct folder structure
- [ ] Record updated with file IDs
- [ ] Frontend displays correctly

#### B. Test với Large PDFs (>15 pages)

**Test cases:**

1. **20-page Test Report:**
   - Verify PDF splitting (2 chunks)
   - Verify merged summary
   - Verify OCR on first chunk
   - Verify field extraction from merged summary

2. **30-page Test Report:**
   - Verify PDF splitting (3 chunks)
   - Verify all chunks processed
   - Verify merged summary quality

**For each test case, verify:**
- [ ] PDF split correctly
- [ ] All chunks processed successfully
- [ ] Summaries merged correctly
- [ ] OCR performed on first chunk
- [ ] Fields extracted correctly from merged summary
- [ ] Valid date calculated correctly
- [ ] File upload succeeds

#### C. Test Edge Cases

1. **Missing fields:**
   - PDF without Report No.
   - PDF without Issued Date
   - PDF without equipment name

2. **Ship validation:**
   - Correct ship name/IMO → Pass
   - Wrong ship name → Show warning
   - Bypass validation → Allow

3. **Unknown equipment:**
   - Equipment not in DEFAULT_INTERVALS
   - Should fallback to 12 months

4. **Date parsing:**
   - Different date formats
   - Invalid dates

**Checklist Task 3.1:**
- [ ] Test với 4 equipment types khác nhau (12, 24, 36, 60 months)
- [ ] Test với small PDFs
- [ ] Test với large PDFs (>15 pages)
- [ ] Test edge cases
- [ ] Document all issues found
- [ ] Create bug list

---

### TASK 3.2: Bug Fixing (0.5-1 ngày)

**Expected bugs to fix:**

1. Date parsing issues
2. Equipment name normalization issues
3. PDF splitting edge cases
4. OCR failures (Tesseract not found)
5. Google Drive upload failures
6. Field extraction accuracy issues

**Process:**

For each bug:
- [ ] Reproduce bug
- [ ] Identify root cause
- [ ] Implement fix
- [ ] Test fix
- [ ] Verify không break other functionality
- [ ] Update documentation

---

### TASK 3.3: Frontend Verification (0.5 ngày)

**Verify frontend integration:**

1. **AddTestReportModal.jsx:**
   - [ ] Calls correct endpoint `/api/test-reports/analyze-file`
   - [ ] Sends correct FormData (test_report_file, ship_id, bypass_validation)
   - [ ] Handles response correctly
   - [ ] Auto-fills form fields correctly
   - [ ] Handles validation errors

2. **testReportService.js:**
   - [ ] analyzeFile() method có parameters đúng
   - [ ] uploadFiles() method gọi đúng endpoint
   - [ ] Error handling đúng

3. **TestReportList.jsx:**
   - [ ] Displays all fields correctly
   - [ ] File icons appear after upload
   - [ ] Status calculated correctly
   - [ ] Delete works (với file deletion)

**Checklist Task 3.3:**
- [ ] Verify frontend calls đúng endpoints
- [ ] Test full flow từ frontend
- [ ] Verify UI displays correctly
- [ ] Test error handling
- [ ] Document any frontend bugs

---

### TASK 3.4: Performance Testing (Optional - 0.5 ngày)

**Test performance với:**

1. **Large files:**
   - 50MB PDF
   - 100+ pages PDF

2. **Concurrent requests:**
   - Multiple users uploading simultaneously
   - Check database locks
   - Check Google Drive rate limits

3. **AI response time:**
   - Document AI latency
   - System AI extraction latency

**Checklist Task 3.4:**
- [ ] Test với large files
- [ ] Test concurrent uploads
- [ ] Measure response times
- [ ] Identify bottlenecks
- [ ] Optimize if needed

---

### TASK 3.5: Documentation & Cleanup (0.5 ngày)

**Documentation:**

1. **Create Migration Summary Document:**
   - What was migrated
   - What changed from V1
   - Known limitations
   - Testing results

2. **Update Code Comments:**
   - Add docstrings
   - Add inline comments for complex logic
   - Update README if needed

3. **Create Testing Guide:**
   - How to test Test Report flow
   - Test cases
   - Expected results

**Cleanup:**

1. **Remove backup files:**
   ```bash
   rm /app/backend/app/utils/*.backup
   ```

2. **Clean up logs:**
   - Remove excessive debug logs
   - Keep important info logs

3. **Code review:**
   - Remove commented code
   - Format code
   - Check imports

**Checklist Task 3.5:**
- [ ] Create migration summary document
- [ ] Update code comments
- [ ] Create testing guide
- [ ] Remove backup files
- [ ] Clean up logs
- [ ] Code review
- [ ] Update README

---

## 📊 TỔNG KẾT PLAN

### Timeline Summary:

| Phase | Tasks | Effort | Status |
|-------|-------|--------|--------|
| **Phase 1: Refactor Utilities** | 5 tasks | 2-3 ngày | ⏳ Pending |
| - Task 1.1: Refactor PDF Splitter | - | 4-5 giờ | ⏳ |
| - Task 1.2: Refactor Targeted OCR | - | 3-4 giờ | ⏳ |
| - Task 1.3: Refactor Document AI | - | 2-3 giờ | ⏳ |
| - Task 1.4: Update Survey Report | - | 1-2 giờ | ⏳ |
| - Task 1.5: Testing Phase 1 | - | 2-3 giờ | ⏳ |
| **Phase 2: Migrate Test Report** | 5 tasks | 3-4 ngày | ⏳ Pending |
| - Task 2.1: AI Extraction Module | - | 4-5 giờ | ⏳ |
| - Task 2.2: Valid Date Calculator | - | 3-4 giờ | ⏳ |
| - Task 2.3: Analyze Service | - | 1 ngày | ⏳ |
| - Task 2.4: Update API Endpoint | - | 1-2 giờ | ⏳ |
| - Task 2.5: Upload Files Endpoint | - | 2-3 giờ | ⏳ |
| **Phase 3: Testing & Validation** | 5 tasks | 1-2 ngày | ⏳ Pending |
| - Task 3.1: E2E Testing | - | 1 ngày | ⏳ |
| - Task 3.2: Bug Fixing | - | 0.5-1 ngày | ⏳ |
| - Task 3.3: Frontend Verification | - | 0.5 ngày | ⏳ |
| - Task 3.4: Performance Testing | - | 0.5 ngày | ⏳ |
| - Task 3.5: Documentation | - | 0.5 ngày | ⏳ |
| **TOTAL** | **15 tasks** | **6-8 ngày** | ⏳ |

---

### Files to Create/Update:

**New Files:**
1. ✅ `/app/backend/app/utils/test_report_ai.py`
2. ✅ `/app/backend/app/utils/test_report_valid_date_calculator.py`
3. ✅ `/app/backend/app/services/test_report_analyze_service.py`
4. ✅ `/app/backend/tests/test_utilities_refactor.py`
5. ✅ `/app/TEST_REPORT_MIGRATION_SUMMARY.md` (after completion)

**Updated Files:**
1. ⚠️ `/app/backend/app/utils/pdf_splitter.py` (refactor)
2. ⚠️ `/app/backend/app/utils/targeted_ocr.py` (refactor)
3. ⚠️ `/app/backend/app/utils/document_ai_helper.py` (refactor)
4. ⚠️ `/app/backend/app/services/survey_report_analyze_service.py` (update calls)
5. ⚠️ `/app/backend/app/api/v1/test_reports.py` (add logic)
6. ⚠️ `/app/backend/app/services/test_report_service.py` (add upload_files)
7. ⚠️ `/app/backend/app/services/gdrive_service.py` (verify test report methods)

---

### Dependencies Checklist:

**Python Packages:**
- [ ] `PyPDF2` - PDF splitting
- [ ] `pytesseract` - OCR
- [ ] `pdf2image` - PDF to image conversion
- [ ] `opencv-python` (cv2) - Image preprocessing
- [ ] `Pillow` (PIL) - Image manipulation
- [ ] `dateutil` - Date parsing
- [ ] `emergentintegrations` - LLM integration
- [ ] `aiohttp` - Async HTTP calls

**System Dependencies:**
- [ ] Tesseract OCR - `apt-get install tesseract-ocr`
- [ ] Poppler - `apt-get install poppler-utils`

**Verification:**
```bash
cd /app/backend
pip list | grep -E "(PyPDF2|pytesseract|pdf2image|opencv-python|Pillow|dateutil|emergent)"
which tesseract
which pdftotext
```

---

### Testing Checklist:

**Phase 1 Testing:**
- [ ] PDF Splitter với Survey Report
- [ ] PDF Splitter với Test Report
- [ ] Targeted OCR với Survey Report
- [ ] Targeted OCR với Test Report
- [ ] Document AI với Survey Report
- [ ] Document AI với Test Report
- [ ] Survey Report flow không bị break

**Phase 2 Testing:**
- [ ] AI extraction prompt accuracy
- [ ] Valid Date Calculator với các equipment types
- [ ] Analyze service với small PDFs
- [ ] Analyze service với large PDFs
- [ ] Upload files to Google Drive
- [ ] Record updates với file IDs

**Phase 3 Testing:**
- [ ] End-to-end flow từ frontend
- [ ] All equipment types (12, 24, 36, 60 months)
- [ ] Edge cases
- [ ] Performance với large files
- [ ] Frontend integration

---

## 🎯 SUCCESS CRITERIA

Migration được coi là thành công khi:

1. ✅ **Utilities Generic:**
   - PDF Splitter hoạt động cho cả Survey Report và Test Report
   - Targeted OCR hoạt động cho cả 2 document types
   - Document AI hoạt động cho cả 2 document types

2. ✅ **Test Report Core Logic:**
   - analyze-file endpoint hoạt động 100%
   - upload-files endpoint hoạt động 100%
   - Valid Date Calculator chính xác
   - AI extraction accuracy ≥ 85%

3. ✅ **No Regression:**
   - Survey Report vẫn hoạt động 100%
   - Không có bugs mới xuất hiện

4. ✅ **Testing:**
   - Tất cả test cases pass
   - No critical bugs
   - Performance acceptable

5. ✅ **Documentation:**
   - Migration summary complete
   - Testing guide complete
   - Code comments adequate

---

## 📞 SUPPORT & ESCALATION

**If stuck or blocked:**

1. **Technical issues:**
   - Check V1 code again for reference
   - Search for similar implementations
   - Use troubleshoot_agent

2. **AI/LLM issues:**
   - Check emergent integrations documentation
   - Verify API keys
   - Test with simpler prompts

3. **Google Drive issues:**
   - Check Apps Script logs
   - Verify permissions
   - Test with manual upload

4. **Critical blockers:**
   - Document the issue
   - Escalate to senior developer
   - Consider alternative approach

---

**Ngày tạo plan**: 2025
**Version**: 1.0
**Status**: ✅ READY TO START

---

## ✅ NEXT STEPS

1. **Review this plan** với team/user
2. **Get approval** để bắt đầu
3. **Start Phase 1** - Refactor utilities
4. **Update status** sau mỗi task hoàn thành
5. **Report progress** daily

**Ready to begin migration!** 🚀


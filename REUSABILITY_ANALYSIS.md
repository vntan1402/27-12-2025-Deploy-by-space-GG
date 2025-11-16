# PHÂN TÍCH KHẢ NĂNG REUSE UTILITIES CHO TEST REPORT

## Ngày phân tích: 2025
## Mục đích: Xác định utilities nào có thể reuse từ Survey Report sang Test Report

---

## 📊 TỔNG QUAN

Backend mới đã có 3 utilities quan trọng:
1. ✅ **PDF Splitter** - `/app/backend/app/utils/pdf_splitter.py`
2. ✅ **Targeted OCR** - `/app/backend/app/utils/targeted_ocr.py`
3. ✅ **Document AI Helper** - `/app/backend/app/utils/document_ai_helper.py`

**Câu hỏi:** Các utilities này có thể reuse cho Test Report không?

---

## 1. PDF SPLITTER - `/app/backend/app/utils/pdf_splitter.py`

### A. Core Functions (✅ GENERIC - Có thể reuse):

```python
class PDFSplitter:
    def __init__(self, max_pages_per_chunk: int = 12):
        """Generic - không phụ thuộc document type"""
    
    def get_page_count(self, pdf_content: bytes) -> int:
        """✅ Generic - đếm số trang"""
    
    def needs_splitting(self, pdf_content: bytes) -> bool:
        """✅ Generic - check cần split không"""
    
    def split_pdf(self, pdf_content: bytes, filename: str) -> List[Dict]:
        """✅ Generic - split PDF thành chunks"""
        # Returns:
        # [
        #   {
        #     'content': bytes,
        #     'chunk_num': 1,
        #     'page_range': '1-12',
        #     'start_page': 1,
        #     'end_page': 12,
        #     'page_count': 12,
        #     'filename': 'file_chunk1.pdf',
        #     'size_bytes': 12345
        #   },
        #   ...
        # ]
```

**✅ VERDICT:** **100% REUSABLE** cho Test Report

**Không cần sửa gì!** Core functions hoàn toàn generic.

---

### B. Helper Functions (⚠️ SPECIFIC - Cần adapt):

```python
def merge_analysis_results(chunk_results: List[Dict]) -> Dict:
    """
    ⚠️ Survey Report SPECIFIC
    Hardcoded fields: 'survey_report_name', 'survey_report_no'
    """
    merged = {
        'survey_report_name': '',  # ⚠️ Hardcoded
        'survey_report_no': '',    # ⚠️ Hardcoded
        'issued_by': '',
        'issued_date': '',
        'ship_name': '',
        'ship_imo': '',
        'surveyor_name': '',
        'status': 'Valid',
        'note': ''
    }
    
    # Logic to merge 'survey_report_name' from chunks
    if extracted.get('survey_report_name'):
        all_names.append({
            'value': extracted['survey_report_name'],
            'chunk': chunk_num
        })
    
    # Logic to merge 'survey_report_no' from chunks
    if extracted.get('survey_report_no'):
        report_nos.append(extracted['survey_report_no'])
```

**⚠️ VERDICT:** **CẦN REFACTOR** để support cả Survey Report và Test Report

**Solution:**
```python
def merge_analysis_results(
    chunk_results: List[Dict], 
    document_type: str = 'survey_report'  # ✅ Add parameter
) -> Dict:
    """
    Generic merge function supporting multiple document types
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
        }
    }
    
    name_field = FIELD_MAPPINGS[document_type]['name']
    no_field = FIELD_MAPPINGS[document_type]['no']
    
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
    for chunk in chunk_results:
        extracted = chunk.get('extracted_fields', {})
        
        if extracted.get(name_field):
            all_names.append({
                'value': extracted[name_field],
                'chunk': chunk_num
            })
        
        if extracted.get(no_field):
            report_nos.append(extracted[no_field])
    
    # ... rest of logic
```

---

```python
def create_enhanced_merged_summary(
    chunk_results: List[Dict],
    merged_data: Dict,
    original_filename: str,
    total_pages: int
) -> str:
    """
    ⚠️ Survey Report SPECIFIC
    Hardcoded fields in output
    """
    summary_lines.append(f"Survey Report Name: {merged_data.get('survey_report_name', 'N/A')}")
    summary_lines.append(f"Report Number: {merged_data.get('survey_report_no', 'N/A')}")
```

**⚠️ VERDICT:** **CẦN REFACTOR**

**Solution:**
```python
def create_enhanced_merged_summary(
    chunk_results: List[Dict],
    merged_data: Dict,
    original_filename: str,
    total_pages: int,
    document_type: str = 'survey_report'  # ✅ Add parameter
) -> str:
    """
    Generic summary creator supporting multiple document types
    """
    
    # ✅ Dynamic field handling
    FIELD_MAPPINGS = {
        'survey_report': {
            'name_label': 'Survey Report Name',
            'name_field': 'survey_report_name',
            'no_label': 'Report Number',
            'no_field': 'survey_report_no'
        },
        'test_report': {
            'name_label': 'Test Report Name',
            'name_field': 'test_report_name',
            'no_label': 'Test Report Number',
            'no_field': 'test_report_no'
        }
    }
    
    mapping = FIELD_MAPPINGS[document_type]
    
    summary_lines.append(f"{mapping['name_label']}: {merged_data.get(mapping['name_field'], 'N/A')}")
    summary_lines.append(f"{mapping['no_label']}: {merged_data.get(mapping['no_field'], 'N/A')}")
```

---

### C. Recommendation cho PDF Splitter:

**Option 1: REFACTOR để generic** (Recommended)
```python
# Thêm parameter document_type vào các helper functions
def merge_analysis_results(chunk_results, document_type='survey_report')
def create_enhanced_merged_summary(chunk_results, merged_data, filename, pages, document_type='survey_report')
```

**Option 2: TẠO MỚI cho Test Report**
```python
# Tạo riêng cho Test Report
def merge_test_report_analysis_results(chunk_results)
def create_test_report_merged_summary(chunk_results, merged_data, filename, pages)
```

**✅ KHUYẾN NGHỊ:** **Option 1 (REFACTOR)** - Maintainable hơn

---

## 2. TARGETED OCR - `/app/backend/app/utils/targeted_ocr.py`

### A. Core OCR Functions (✅ MOSTLY GENERIC):

```python
class TargetedOCRProcessor:
    def __init__(self, header_percent: float = 0.15, footer_percent: float = 0.15):
        """✅ Generic - không phụ thuộc document type"""
    
    def is_available(self) -> bool:
        """✅ Generic - check Tesseract có sẵn không"""
    
    def _extract_header(self, image: Image) -> str:
        """✅ Generic - extract header text"""
    
    def _extract_footer(self, image: Image) -> str:
        """✅ Generic - extract footer text"""
    
    def _preprocess_image(self, image: Image) -> Image:
        """✅ Generic - preprocess image cho OCR"""
```

**✅ VERDICT:** **100% REUSABLE**

---

### B. Pattern Extraction (⚠️ PARTIALLY SPECIFIC):

```python
def extract_from_pdf(self, pdf_content: bytes, page_num: int = 0) -> Dict:
    """
    Extract from PDF
    
    Returns:
        {
            'report_form': str or None,
            'survey_report_no': str or None,  # ⚠️ Hardcoded field name
            'header_text': str,
            'footer_text': str,
            'ocr_success': bool,
            'ocr_error': str or None
        }
    """
    
    # Extract fields using pattern matching
    report_form = self._extract_report_form(combined_text)
    survey_report_no = self._extract_report_no(combined_text)  # ⚠️ Naming
    
    return {
        'report_form': report_form,
        'survey_report_no': survey_report_no,  # ⚠️ Hardcoded
        'header_text': header_text,
        'footer_text': footer_text,
        'ocr_success': True
    }
```

**⚠️ ISSUE:** Field name `survey_report_no` hardcoded

**Solution:**
```python
def extract_from_pdf(
    self, 
    pdf_content: bytes, 
    page_num: int = 0,
    report_no_field: str = 'survey_report_no'  # ✅ Configurable
) -> Dict:
    """Generic extraction"""
    
    report_form = self._extract_report_form(combined_text)
    report_no = self._extract_report_no(combined_text)
    
    return {
        'report_form': report_form,
        report_no_field: report_no,  # ✅ Dynamic field name
        'header_text': header_text,
        'footer_text': footer_text,
        'ocr_success': True
    }
```

**Usage:**
```python
# Survey Report
ocr_result = ocr_processor.extract_from_pdf(
    file_content, 
    page_num=0,
    report_no_field='survey_report_no'
)

# Test Report
ocr_result = ocr_processor.extract_from_pdf(
    file_content, 
    page_num=0,
    report_no_field='test_report_no'
)
```

---

### C. Merge Functions (⚠️ SPECIFIC):

```python
def merge_document_ai_and_ocr(
    doc_ai_result: Dict,
    ocr_result: Dict
) -> Dict:
    """
    ⚠️ Survey Report SPECIFIC
    Hardcoded: 'survey_report_no'
    """
    merged = {
        'report_form': None,
        'survey_report_no': None,  # ⚠️ Hardcoded
        'report_form_source': 'none',
        'survey_report_no_source': 'none'  # ⚠️ Hardcoded
    }
    
    # Merge survey_report_no
    doc_no = (doc_ai_result.get('survey_report_no') or '').strip()
    ocr_no = (ocr_result.get('survey_report_no') or '').strip()
    
    if doc_no and ocr_no:
        if self._normalize_report_no(doc_no) == self._normalize_report_no(ocr_no):
            merged['survey_report_no'] = doc_no
            merged['survey_report_no_source'] = 'both'
```

**⚠️ VERDICT:** **CẦN REFACTOR**

**Solution:**
```python
def merge_document_ai_and_ocr(
    doc_ai_result: Dict,
    ocr_result: Dict,
    report_no_field: str = 'survey_report_no'  # ✅ Configurable
) -> Dict:
    """Generic merge function"""
    
    merged = {
        'report_form': None,
        report_no_field: None,  # ✅ Dynamic
        'report_form_source': 'none',
        f'{report_no_field}_source': 'none'  # ✅ Dynamic
    }
    
    # Merge report_no
    doc_no = (doc_ai_result.get(report_no_field) or '').strip()
    ocr_no = (ocr_result.get(report_no_field) or '').strip()
    
    if doc_no and ocr_no:
        if self._normalize_report_no(doc_no) == self._normalize_report_no(ocr_no):
            merged[report_no_field] = doc_no
            merged[f'{report_no_field}_source'] = 'both'
```

---

### D. Helper Function (✅ GENERIC):

```python
def get_ocr_processor() -> TargetedOCRProcessor:
    """✅ Generic singleton"""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = TargetedOCRProcessor()
    return _ocr_processor
```

**✅ VERDICT:** **100% REUSABLE**

---

### E. Recommendation cho Targeted OCR:

**REFACTOR để generic:**
```python
# Add configurable field names
class TargetedOCRProcessor:
    def extract_from_pdf(self, pdf_content, page_num=0, report_no_field='survey_report_no'):
        # ...
    
    def merge_document_ai_and_ocr(self, doc_ai, ocr, report_no_field='survey_report_no'):
        # ...
```

**✅ KHUYẾN NGHỊ:** **Minor refactor** - Thêm optional parameter `report_no_field`

---

## 3. DOCUMENT AI HELPER - `/app/backend/app/utils/document_ai_helper.py`

### A. Main Function (⚠️ SPECIFIC):

```python
async def analyze_survey_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    ⚠️ Function name is survey_report specific
    ⚠️ Hardcoded document_type in request
    """
    
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
        "document_type": "survey_report"  # ⚠️ Hardcoded
    }
    
    # Call Apps Script
    # ...
```

**⚠️ VERDICT:** **CẦN REFACTOR**

**Solution:**
```python
async def analyze_document_with_document_ai(  # ✅ Generic name
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any],
    document_type: str = 'survey_report'  # ✅ Configurable
) -> Dict[str, Any]:
    """
    Generic Document AI analysis for any document type
    """
    
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
    
    # Rest of logic...
```

**Hoặc tạo wrapper functions:**
```python
# Generic core function
async def analyze_document_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any],
    document_type: str
) -> Dict[str, Any]:
    # Core logic...

# Specific wrappers
async def analyze_survey_report_with_document_ai(
    file_content, filename, content_type, document_ai_config
):
    return await analyze_document_with_document_ai(
        file_content, filename, content_type, document_ai_config,
        document_type='survey_report'
    )

async def analyze_test_report_with_document_ai(
    file_content, filename, content_type, document_ai_config
):
    return await analyze_document_with_document_ai(
        file_content, filename, content_type, document_ai_config,
        document_type='test_report'
    )
```

**✅ KHUYẾN NGHỊ:** **Option 2 (Wrapper)** - Backward compatible

---

## 📊 TỔNG KẾT

### Utilities Reusability Matrix:

| Utility | Component | Status | Action Required | Effort |
|---------|-----------|--------|-----------------|--------|
| **PDF Splitter** | Core functions | ✅ 100% Generic | ✅ Reuse as-is | None |
| **PDF Splitter** | merge_analysis_results() | ⚠️ Specific | 🔧 Refactor | Low |
| **PDF Splitter** | create_enhanced_merged_summary() | ⚠️ Specific | 🔧 Refactor | Low |
| **Targeted OCR** | Core OCR | ✅ 100% Generic | ✅ Reuse as-is | None |
| **Targeted OCR** | extract_from_pdf() | ⚠️ Partially specific | 🔧 Add parameter | Very Low |
| **Targeted OCR** | merge_document_ai_and_ocr() | ⚠️ Specific | 🔧 Add parameter | Low |
| **Document AI** | analyze function | ⚠️ Specific | 🔧 Refactor or wrapper | Low |

### Summary:

✅ **70% có thể reuse TRỰC TIẾP** (core functions)
⚠️ **30% cần refactor NHẸ** (helper functions với hardcoded field names)

---

## 🎯 KHUYẾN NGHỊ

### Option A: QUICK FIX (Recommended cho Test Report)

**Không refactor utilities hiện tại**, tạo riêng cho Test Report:

```python
# test_report_analyze_service.py

# Reuse utilities as-is:
from app.utils.pdf_splitter import PDFSplitter  # ✅ Reuse
from app.utils.targeted_ocr import get_ocr_processor  # ✅ Reuse

# Create Test Report specific helpers:
def merge_test_report_analysis_results(chunk_results):
    """Test Report version of merge function"""
    merged = {
        'test_report_name': '',
        'test_report_no': '',
        # ... same logic, different field names
    }

def create_test_report_merged_summary(chunk_results, merged_data, filename, pages):
    """Test Report version of summary creator"""
    # ... same logic, different labels

async def analyze_test_report_with_document_ai(file_content, filename, content_type, config):
    """Test Report version of Document AI call"""
    # Call generic with document_type='test_report'
```

**Pros:**
- ✅ Quick implementation
- ✅ No risk of breaking Survey Report
- ✅ Can reuse 70% of logic

**Cons:**
- ❌ Code duplication
- ❌ Less maintainable long-term

**Estimated time:** 2-3 hours

---

### Option B: PROPER REFACTOR (Recommended long-term)

**Refactor utilities để fully generic:**

```python
# pdf_splitter.py - Add document_type parameter
def merge_analysis_results(chunk_results, document_type='survey_report'):
    # Dynamic field handling...

def create_enhanced_merged_summary(..., document_type='survey_report'):
    # Dynamic label handling...

# targeted_ocr.py - Add report_no_field parameter
def extract_from_pdf(self, ..., report_no_field='survey_report_no'):
    # Dynamic field names...

def merge_document_ai_and_ocr(self, ..., report_no_field='survey_report_no'):
    # Dynamic field names...

# document_ai_helper.py - Create generic + wrappers
async def analyze_document_with_document_ai(..., document_type):
    # Generic core...

async def analyze_survey_report_with_document_ai(...):
    return await analyze_document_with_document_ai(..., document_type='survey_report')

async def analyze_test_report_with_document_ai(...):
    return await analyze_document_with_document_ai(..., document_type='test_report')
```

**Pros:**
- ✅ Clean, maintainable code
- ✅ Future-proof for other document types
- ✅ Single source of truth

**Cons:**
- ❌ Need to update Survey Report service
- ❌ Need thorough testing

**Estimated time:** 4-6 hours (refactor + testing)

---

## ✅ KẾT LUẬN

### CÂU TRẢ LỜI:

**Q: 3 utilities (PDF Splitter, Targeted OCR, Document AI) có thể reuse cho Test Report không?**

**A: ✅ CÓ - Nhưng cần một số điều chỉnh nhỏ:**

1. **PDF Splitter:**
   - ✅ Core functions: 100% reuse
   - ⚠️ Helper functions: Cần refactor hoặc tạo mới

2. **Targeted OCR:**
   - ✅ Core OCR: 100% reuse
   - ⚠️ Field-specific logic: Cần thêm parameters hoặc tạo mới

3. **Document AI:**
   - ✅ Core logic: 95% reuse
   - ⚠️ Function name/payload: Cần wrapper hoặc refactor

### EFFORT ESTIMATE:

- **Option A (Quick):** 2-3 giờ (tạo riêng cho Test Report)
- **Option B (Proper):** 4-6 giờ (refactor để generic)

### KHUYẾN NGHỊ:

**Cho Test Report hiện tại:** Dùng **Option A** (quick fix)
- Reuse 70% code
- Tạo riêng 30% specific helpers
- Ship nhanh

**Cho tương lai:** Plan **Option B** (proper refactor)
- Refactor khi có thời gian
- Benefits cho tất cả document types
- Maintainable long-term

---

**Ngày hoàn thành**: 2025
**Verdict**: ✅ **70% CÓ THỂ REUSE TRỰC TIẾP**


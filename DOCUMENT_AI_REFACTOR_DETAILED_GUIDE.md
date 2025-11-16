# DOCUMENT AI HELPER - CHI TIẾT REFACTOR GUIDE

## Ngày: 2025
## Task: 1.3 - Refactor Document AI (2-3 giờ)
## Objective: Tạo generic function + wrappers để support tất cả document types

---

## 📋 MỤC LỤC

1. [Tổng quan](#1-tổng-quan)
2. [Current State Analysis](#2-current-state-analysis)
3. [Target State Design](#3-target-state-design)
4. [Step-by-Step Implementation](#4-step-by-step-implementation)
5. [Testing Strategy](#5-testing-strategy)
6. [Rollback Plan](#6-rollback-plan)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. TỔNG QUAN

### Vấn đề hiện tại:

```python
# File: /app/backend/app/utils/document_ai_helper.py

async def analyze_survey_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    # ...
    payload = {
        # ...
        "document_type": "survey_report"  # ⚠️ HARDCODED
    }
```

**Issues:**
1. ❌ Function name specific cho Survey Report
2. ❌ `document_type` hardcoded trong payload
3. ❌ Không thể reuse cho Test Report, Audit Report, etc.

### Giải pháp:

**Approach: Create Generic Core + Type-Specific Wrappers**

```
┌─────────────────────────────────────────────────────┐
│  analyze_document_with_document_ai()                │
│  (Generic Core Function)                            │
│  - Accepts document_type parameter                  │
│  - Handles all document types                       │
└─────────────────────────────────────────────────────┘
                        ▲
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        │               │               │
┌───────▼──────┐  ┌────▼─────┐  ┌─────▼──────┐
│ Survey       │  │ Test     │  │ Audit      │
│ Report       │  │ Report   │  │ Report     │
│ Wrapper      │  │ Wrapper  │  │ Wrapper    │
└──────────────┘  └──────────┘  └────────────┘
```

**Benefits:**
- ✅ Single source of truth (generic core)
- ✅ Backward compatible (keep old function as wrapper)
- ✅ Easy to add new document types
- ✅ Maintainable code

---

## 2. CURRENT STATE ANALYSIS

### Current File Structure:

```
/app/backend/app/utils/document_ai_helper.py
├── Imports (lines 1-11)
└── analyze_survey_report_with_document_ai() (lines 14-121)
    ├── Config extraction (lines 34-54)
    ├── File encoding (lines 56-57)
    ├── Payload building (lines 59-69)
    │   └── ⚠️ document_type: "survey_report" (line 68)
    ├── Apps Script call (lines 72-106)
    └── Error handling (lines 108-121)
```

### Current Function Signature:

```python
async def analyze_survey_report_with_document_ai(
    file_content: bytes,      # PDF file bytes
    filename: str,            # Original filename
    content_type: str,        # MIME type (application/pdf)
    document_ai_config: Dict  # Config dict with:
                              # - project_id
                              # - processor_id
                              # - location
                              # - apps_script_url
) -> Dict[str, Any]:          # Returns:
                              # {
                              #   "success": bool,
                              #   "data": {"summary": str},
                              #   "message": str (if error)
                              # }
```

### Current Apps Script Payload:

```python
payload = {
    "action": "analyze_maritime_document_ai",
    "file_content": "<base64_string>",
    "filename": "example.pdf",
    "content_type": "application/pdf",
    "project_id": "my-project",
    "processor_id": "abc123",
    "location": "us",
    "document_type": "survey_report"  # ⚠️ Hardcoded
}
```

### Where it's used:

**Survey Report Analyze Service:**
```python
# /app/backend/app/services/survey_report_analyze_service.py

from app.utils.document_ai_helper import analyze_survey_report_with_document_ai

# Called in _process_single_pdf() and _process_large_pdf()
result = await analyze_survey_report_with_document_ai(
    file_content=file_content,
    filename=filename,
    content_type=content_type,
    document_ai_config=document_ai_config
)
```

---

## 3. TARGET STATE DESIGN

### New File Structure:

```
/app/backend/app/utils/document_ai_helper.py
├── Imports (unchanged)
├── analyze_document_with_document_ai()        # ✅ NEW - Generic core
├── analyze_survey_report_with_document_ai()   # ✅ MODIFIED - Wrapper
├── analyze_test_report_with_document_ai()     # ✅ NEW - Wrapper
├── analyze_audit_report_with_document_ai()    # ✅ NEW - Wrapper
└── analyze_drawings_manual_with_document_ai() # ✅ NEW - Wrapper (future)
```

### Design Pattern: Strategy + Adapter

```python
# GENERIC CORE (Strategy)
async def analyze_document_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any],
    document_type: str  # ✅ NEW parameter
) -> Dict[str, Any]:
    """
    Generic Document AI analysis for any document type
    
    Supported document_types:
    - 'survey_report'
    - 'test_report'
    - 'audit_report'
    - 'drawings_manual'
    - 'approval_document'
    - etc.
    """
    # ... implementation


# TYPE-SPECIFIC WRAPPERS (Adapters)
async def analyze_survey_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Wrapper for Survey Report (backward compatible)"""
    return await analyze_document_with_document_ai(
        file_content,
        filename,
        content_type,
        document_ai_config,
        document_type='survey_report'
    )


async def analyze_test_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Wrapper for Test Report"""
    return await analyze_document_with_document_ai(
        file_content,
        filename,
        content_type,
        document_ai_config,
        document_type='test_report'
    )
```

---

## 4. STEP-BY-STEP IMPLEMENTATION

### STEP 1: Backup Current File (1 phút)

```bash
cp /app/backend/app/utils/document_ai_helper.py \
   /app/backend/app/utils/document_ai_helper.py.backup

# Verify backup
ls -lh /app/backend/app/utils/document_ai_helper.py*
```

---

### STEP 2: Create Generic Core Function (45-60 phút)

#### A. Add Generic Function BEFORE existing function

**File:** `/app/backend/app/utils/document_ai_helper.py`

**Insert at line 14 (before analyze_survey_report_with_document_ai):**

```python
async def analyze_document_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any],
    document_type: str
) -> Dict[str, Any]:
    """
    Generic Document AI analysis for any document type
    
    This is the core function that handles Document AI processing for all document types.
    Type-specific wrapper functions call this function with appropriate document_type.
    
    Args:
        file_content: PDF file bytes
        filename: Original filename (e.g., "report.pdf")
        content_type: MIME type (e.g., "application/pdf")
        document_ai_config: Configuration dictionary containing:
            - project_id: Google Cloud project ID
            - processor_id: Document AI processor ID
            - location: Processor location (default: "us")
            - apps_script_url: URL of deployed Apps Script web app
        document_type: Type of document being analyzed:
            - 'survey_report': Survey reports (class surveys, inspections)
            - 'test_report': Test reports (equipment maintenance, testing)
            - 'audit_report': Audit reports (ISM, ISPS, MLC audits)
            - 'drawings_manual': Technical drawings and manuals
            - 'approval_document': Approval documents
            - 'certificate': Certificates
            - 'other': Other maritime documents
    
    Returns:
        Dict containing:
        {
            "success": bool,              # True if analysis succeeded
            "data": {                     # Present if success=True
                "summary": str,           # Extracted text from PDF
                "confidence": float       # Optional confidence score
            },
            "message": str                # Error message if success=False
        }
    
    Example:
        >>> result = await analyze_document_with_document_ai(
        ...     file_content=pdf_bytes,
        ...     filename="survey_report.pdf",
        ...     content_type="application/pdf",
        ...     document_ai_config={
        ...         "project_id": "my-project",
        ...         "processor_id": "abc123",
        ...         "location": "us",
        ...         "apps_script_url": "https://script.google.com/..."
        ...     },
        ...     document_type='survey_report'
        ... )
        >>> if result['success']:
        ...     print(result['data']['summary'])
    
    Note:
        - Timeout is set to 120 seconds (2 minutes)
        - File is encoded to base64 before sending to Apps Script
        - Apps Script handles actual Google Document AI API call
        - This function is transport layer, not processing logic
    """
    try:
        # Validate document_type
        SUPPORTED_TYPES = [
            'survey_report',
            'test_report', 
            'audit_report',
            'drawings_manual',
            'approval_document',
            'certificate',
            'crew_certificate',
            'other_document',
            'other'
        ]
        
        if document_type not in SUPPORTED_TYPES:
            logger.warning(f"⚠️ Unsupported document_type: {document_type}, using 'other'")
            document_type = 'other'
        
        # Extract config
        project_id = document_ai_config.get("project_id")
        processor_id = document_ai_config.get("processor_id")
        location = document_ai_config.get("location", "us")
        
        if not project_id or not processor_id:
            logger.error("❌ Missing Document AI configuration (project_id or processor_id)")
            return {
                "success": False,
                "message": "Missing Document AI configuration (project_id or processor_id)"
            }
        
        logger.info(f"🤖 Calling Google Document AI for {document_type}: {filename}")
        logger.info(f"   Project: {project_id}, Processor: {processor_id}, Location: {location}")
        
        # Get Apps Script URL from config
        apps_script_url = document_ai_config.get("apps_script_url")
        
        if not apps_script_url:
            logger.error("❌ Apps Script URL not configured for Document AI")
            return {
                "success": False,
                "message": "Apps Script URL not configured for Document AI"
            }
        
        # Encode file to base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        logger.info(f"📦 Encoded file to base64: {len(file_base64)} chars")
        
        # Build request payload
        payload = {
            "action": "analyze_maritime_document_ai",
            "file_content": file_base64,
            "filename": filename,
            "content_type": content_type,
            "project_id": project_id,
            "processor_id": processor_id,
            "location": location,
            "document_type": document_type  # ✅ Dynamic value
        }
        
        logger.info(f"📤 Sending request to Apps Script: {apps_script_url}")
        
        # Call Apps Script with timeout
        async with aiohttp.ClientSession() as session:
            async with session.post(
                apps_script_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout
            ) as response:
                # Check HTTP status
                if response.status == 200:
                    result = await response.json()
                    
                    # Check Apps Script response
                    if result.get("success"):
                        summary = result.get("data", {}).get("summary", "")
                        confidence = result.get("data", {}).get("confidence", 0.0)
                        
                        logger.info(f"✅ Document AI analysis completed for {document_type}")
                        logger.info(f"   Summary length: {len(summary)} characters")
                        logger.info(f"   Confidence: {confidence}")
                        
                        return {
                            "success": True,
                            "data": {
                                "summary": summary,
                                "confidence": confidence
                            }
                        }
                    else:
                        error_msg = result.get("message", "Unknown error from Apps Script")
                        logger.error(f"❌ Document AI failed for {document_type}: {error_msg}")
                        return {
                            "success": False,
                            "message": error_msg
                        }
                else:
                    # HTTP error
                    error_text = await response.text()
                    logger.error(f"❌ Apps Script HTTP error: {response.status}")
                    logger.error(f"   Response: {error_text[:500]}")  # Log first 500 chars
                    return {
                        "success": False,
                        "message": f"Apps Script HTTP error: {response.status}"
                    }
    
    except asyncio.TimeoutError:
        logger.error(f"❌ Document AI request timed out for {document_type} after 120 seconds")
        return {
            "success": False,
            "message": "Document AI request timed out (>2 minutes). Try with a smaller file or check network connection."
        }
    
    except aiohttp.ClientError as e:
        logger.error(f"❌ Network error calling Document AI for {document_type}: {e}")
        return {
            "success": False,
            "message": f"Network error: {str(e)}"
        }
    
    except Exception as e:
        logger.error(f"❌ Unexpected error in Document AI for {document_type}: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": f"Document AI error: {str(e)}"
        }
```

**Key Changes in Generic Function:**
1. ✅ Added `document_type` parameter
2. ✅ Added validation for supported types
3. ✅ Dynamic `document_type` in payload
4. ✅ Enhanced logging with document_type
5. ✅ Better error messages
6. ✅ Comprehensive docstring

---

### STEP 3: Refactor Existing Function as Wrapper (15 phút)

#### A. Modify analyze_survey_report_with_document_ai()

**Replace existing function (lines 14-121) with:**

```python
async def analyze_survey_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze survey report using Google Document AI
    
    This is a wrapper function that calls the generic analyze_document_with_document_ai()
    with document_type='survey_report'. Kept for backward compatibility.
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type
        document_ai_config: Config with project_id, processor_id, location, apps_script_url
    
    Returns:
        Dict with success status and summary text
        
    Example:
        >>> result = await analyze_survey_report_with_document_ai(
        ...     file_content=pdf_bytes,
        ...     filename="cargo_gear_survey.pdf",
        ...     content_type="application/pdf",
        ...     document_ai_config=config
        ... )
    
    Note:
        This function is a wrapper for backward compatibility.
        New code should use analyze_document_with_document_ai() directly.
    """
    logger.info(f"🔄 Survey Report wrapper called for: {filename}")
    
    return await analyze_document_with_document_ai(
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        document_ai_config=document_ai_config,
        document_type='survey_report'
    )
```

**Key Changes:**
1. ✅ Simplified to 1 line delegation
2. ✅ Keeps same signature (backward compatible)
3. ✅ Added note about wrapper status
4. ✅ Logging for tracking usage

---

### STEP 4: Add New Wrappers (30 phút)

#### A. Add Test Report Wrapper

**Add after analyze_survey_report_with_document_ai():**

```python
async def analyze_test_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze test report using Google Document AI
    
    Test reports are maintenance/testing records for lifesaving and firefighting equipment.
    Common equipment: EEBD, SCBA, Life Rafts, Fire Extinguishers, etc.
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type
        document_ai_config: Config with project_id, processor_id, location, apps_script_url
    
    Returns:
        Dict with success status and summary text
        
    Example:
        >>> result = await analyze_test_report_with_document_ai(
        ...     file_content=pdf_bytes,
        ...     filename="eebd_test_2024.pdf",
        ...     content_type="application/pdf",
        ...     document_ai_config=config
        ... )
    """
    logger.info(f"🔄 Test Report wrapper called for: {filename}")
    
    return await analyze_document_with_document_ai(
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        document_ai_config=document_ai_config,
        document_type='test_report'
    )
```

#### B. Add Audit Report Wrapper

```python
async def analyze_audit_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze audit report using Google Document AI
    
    Audit reports include ISM, ISPS, and MLC audits.
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type
        document_ai_config: Config with project_id, processor_id, location, apps_script_url
    
    Returns:
        Dict with success status and summary text
        
    Example:
        >>> result = await analyze_audit_report_with_document_ai(
        ...     file_content=pdf_bytes,
        ...     filename="ism_audit_2024.pdf",
        ...     content_type="application/pdf",
        ...     document_ai_config=config
        ... )
    """
    logger.info(f"🔄 Audit Report wrapper called for: {filename}")
    
    return await analyze_document_with_document_ai(
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        document_ai_config=document_ai_config,
        document_type='audit_report'
    )
```

#### C. Add Drawings/Manual Wrapper

```python
async def analyze_drawings_manual_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze technical drawing or manual using Google Document AI
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type
        document_ai_config: Config with project_id, processor_id, location, apps_script_url
    
    Returns:
        Dict with success status and summary text
    """
    logger.info(f"🔄 Drawings/Manual wrapper called for: {filename}")
    
    return await analyze_document_with_document_ai(
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        document_ai_config=document_ai_config,
        document_type='drawings_manual'
    )
```

#### D. Add Generic Document Wrapper (fallback)

```python
async def analyze_other_document_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze other/generic document using Google Document AI
    
    Fallback wrapper for document types not covered by specific wrappers.
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type
        document_ai_config: Config with project_id, processor_id, location, apps_script_url
    
    Returns:
        Dict with success status and summary text
    """
    logger.info(f"🔄 Other Document wrapper called for: {filename}")
    
    return await analyze_document_with_document_ai(
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        document_ai_config=document_ai_config,
        document_type='other'
    )
```

---

### STEP 5: Update Module Exports (5 phút)

**Add at end of file (before the last line):**

```python
# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # Generic core function
    'analyze_document_with_document_ai',
    
    # Type-specific wrappers
    'analyze_survey_report_with_document_ai',
    'analyze_test_report_with_document_ai',
    'analyze_audit_report_with_document_ai',
    'analyze_drawings_manual_with_document_ai',
    'analyze_other_document_with_document_ai',
]
```

---

### STEP 6: Verify File Structure (2 phút)

**Final file structure should be:**

```python
"""
Document AI Helper - Generic implementation
Handles Google Document AI integration for all document types
"""
import logging
import aiohttp
import asyncio
import base64
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ============================================================================
# GENERIC CORE FUNCTION
# ============================================================================

async def analyze_document_with_document_ai(...):
    """Generic Document AI analysis for any document type"""
    pass


# ============================================================================
# TYPE-SPECIFIC WRAPPERS (for backward compatibility and convenience)
# ============================================================================

async def analyze_survey_report_with_document_ai(...):
    """Analyze survey report (wrapper)"""
    return await analyze_document_with_document_ai(..., document_type='survey_report')


async def analyze_test_report_with_document_ai(...):
    """Analyze test report (wrapper)"""
    return await analyze_document_with_document_ai(..., document_type='test_report')


async def analyze_audit_report_with_document_ai(...):
    """Analyze audit report (wrapper)"""
    return await analyze_document_with_document_ai(..., document_type='audit_report')


async def analyze_drawings_manual_with_document_ai(...):
    """Analyze drawings/manual (wrapper)"""
    return await analyze_document_with_document_ai(..., document_type='drawings_manual')


async def analyze_other_document_with_document_ai(...):
    """Analyze other document (wrapper)"""
    return await analyze_document_with_document_ai(..., document_type='other')


# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    'analyze_document_with_document_ai',
    'analyze_survey_report_with_document_ai',
    'analyze_test_report_with_document_ai',
    'analyze_audit_report_with_document_ai',
    'analyze_drawings_manual_with_document_ai',
    'analyze_other_document_with_document_ai',
]
```

---

## 5. TESTING STRATEGY

### STEP 1: Create Test Script (20 phút)

**Create file:** `/app/backend/tests/test_document_ai_refactor.py`

```python
"""
Test Document AI Helper Refactor
Verify generic function and wrappers work correctly
"""
import asyncio
import base64
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Import functions to test
from app.utils.document_ai_helper import (
    analyze_document_with_document_ai,
    analyze_survey_report_with_document_ai,
    analyze_test_report_with_document_ai,
    analyze_audit_report_with_document_ai
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_pdf_content():
    """Mock PDF file content"""
    # Simple PDF header
    return b'%PDF-1.4\n%Test PDF content\n%%EOF'


@pytest.fixture
def mock_document_ai_config():
    """Mock Document AI configuration"""
    return {
        "project_id": "test-project-123",
        "processor_id": "test-processor-456",
        "location": "us",
        "apps_script_url": "https://script.google.com/test"
    }


@pytest.fixture
def mock_successful_response():
    """Mock successful Document AI response"""
    return {
        "success": True,
        "data": {
            "summary": "This is a test survey report about cargo gear inspection...",
            "confidence": 0.95
        }
    }


# ============================================================================
# TESTS FOR GENERIC CORE FUNCTION
# ============================================================================

@pytest.mark.asyncio
async def test_generic_function_with_survey_report(
    mock_pdf_content,
    mock_document_ai_config,
    mock_successful_response
):
    """Test generic function with survey_report type"""
    
    with patch('aiohttp.ClientSession') as mock_session:
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_successful_response)
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        # Call generic function
        result = await analyze_document_with_document_ai(
            file_content=mock_pdf_content,
            filename="test_survey.pdf",
            content_type="application/pdf",
            document_ai_config=mock_document_ai_config,
            document_type='survey_report'
        )
        
        # Assertions
        assert result['success'] is True
        assert 'data' in result
        assert 'summary' in result['data']
        assert len(result['data']['summary']) > 0
        assert result['data']['confidence'] == 0.95


@pytest.mark.asyncio
async def test_generic_function_with_test_report(
    mock_pdf_content,
    mock_document_ai_config
):
    """Test generic function with test_report type"""
    
    mock_response_data = {
        "success": True,
        "data": {
            "summary": "This is a test report for EEBD maintenance...",
            "confidence": 0.92
        }
    }
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        # Call with test_report type
        result = await analyze_document_with_document_ai(
            file_content=mock_pdf_content,
            filename="test_eebd.pdf",
            content_type="application/pdf",
            document_ai_config=mock_document_ai_config,
            document_type='test_report'  # ✅ Different type
        )
        
        # Verify success
        assert result['success'] is True
        assert 'EEBD' in result['data']['summary']


@pytest.mark.asyncio
async def test_generic_function_invalid_document_type(
    mock_pdf_content,
    mock_document_ai_config,
    mock_successful_response
):
    """Test generic function with invalid document_type (should fallback to 'other')"""
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_successful_response)
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        # Call with invalid type
        result = await analyze_document_with_document_ai(
            file_content=mock_pdf_content,
            filename="test.pdf",
            content_type="application/pdf",
            document_ai_config=mock_document_ai_config,
            document_type='invalid_type'  # ⚠️ Invalid
        )
        
        # Should still succeed (fallback to 'other')
        assert result['success'] is True


@pytest.mark.asyncio
async def test_generic_function_missing_config(mock_pdf_content):
    """Test generic function with missing configuration"""
    
    # Missing project_id and processor_id
    incomplete_config = {
        "apps_script_url": "https://script.google.com/test"
    }
    
    result = await analyze_document_with_document_ai(
        file_content=mock_pdf_content,
        filename="test.pdf",
        content_type="application/pdf",
        document_ai_config=incomplete_config,
        document_type='survey_report'
    )
    
    # Should fail gracefully
    assert result['success'] is False
    assert 'Missing Document AI configuration' in result['message']


@pytest.mark.asyncio
async def test_generic_function_http_error(
    mock_pdf_content,
    mock_document_ai_config
):
    """Test generic function with HTTP error"""
    
    with patch('aiohttp.ClientSession') as mock_session:
        # Mock HTTP 500 error
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        result = await analyze_document_with_document_ai(
            file_content=mock_pdf_content,
            filename="test.pdf",
            content_type="application/pdf",
            document_ai_config=mock_document_ai_config,
            document_type='survey_report'
        )
        
        # Should fail
        assert result['success'] is False
        assert '500' in result['message']


@pytest.mark.asyncio
async def test_generic_function_timeout(
    mock_pdf_content,
    mock_document_ai_config
):
    """Test generic function with timeout"""
    
    with patch('aiohttp.ClientSession') as mock_session:
        # Mock timeout
        mock_session.return_value.__aenter__.return_value.post.side_effect = asyncio.TimeoutError()
        
        result = await analyze_document_with_document_ai(
            file_content=mock_pdf_content,
            filename="test.pdf",
            content_type="application/pdf",
            document_ai_config=mock_document_ai_config,
            document_type='survey_report'
        )
        
        # Should fail with timeout message
        assert result['success'] is False
        assert 'timed out' in result['message'].lower()


# ============================================================================
# TESTS FOR WRAPPERS (Backward Compatibility)
# ============================================================================

@pytest.mark.asyncio
async def test_survey_report_wrapper(
    mock_pdf_content,
    mock_document_ai_config,
    mock_successful_response
):
    """Test Survey Report wrapper calls generic function correctly"""
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_successful_response)
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        # Call wrapper (OLD API)
        result = await analyze_survey_report_with_document_ai(
            file_content=mock_pdf_content,
            filename="survey.pdf",
            content_type="application/pdf",
            document_ai_config=mock_document_ai_config
        )
        
        # Should work exactly like before
        assert result['success'] is True
        assert 'data' in result


@pytest.mark.asyncio
async def test_test_report_wrapper(
    mock_pdf_content,
    mock_document_ai_config
):
    """Test Test Report wrapper calls generic function correctly"""
    
    mock_response_data = {
        "success": True,
        "data": {
            "summary": "Test report summary...",
            "confidence": 0.9
        }
    }
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        # Call NEW wrapper
        result = await analyze_test_report_with_document_ai(
            file_content=mock_pdf_content,
            filename="test.pdf",
            content_type="application/pdf",
            document_ai_config=mock_document_ai_config
        )
        
        # Should work
        assert result['success'] is True


@pytest.mark.asyncio
async def test_audit_report_wrapper(
    mock_pdf_content,
    mock_document_ai_config
):
    """Test Audit Report wrapper"""
    
    mock_response_data = {
        "success": True,
        "data": {
            "summary": "Audit report summary...",
            "confidence": 0.88
        }
    }
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        # Call Audit Report wrapper
        result = await analyze_audit_report_with_document_ai(
            file_content=mock_pdf_content,
            filename="audit.pdf",
            content_type="application/pdf",
            document_ai_config=mock_document_ai_config
        )
        
        assert result['success'] is True


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_all_wrappers_use_same_core():
    """Verify all wrappers delegate to same generic core"""
    
    # This test verifies the design pattern is correct
    # All wrappers should call analyze_document_with_document_ai
    
    import inspect
    
    # Get source of Survey Report wrapper
    survey_source = inspect.getsource(analyze_survey_report_with_document_ai)
    
    # Should contain call to generic function
    assert 'analyze_document_with_document_ai' in survey_source
    assert "document_type='survey_report'" in survey_source
    
    # Same for Test Report wrapper
    test_source = inspect.getsource(analyze_test_report_with_document_ai)
    assert 'analyze_document_with_document_ai' in test_source
    assert "document_type='test_report'" in test_source


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
```

**Run tests:**

```bash
cd /app/backend
pytest tests/test_document_ai_refactor.py -v
```

---

### STEP 2: Manual Integration Test (15 phút)

**Create manual test script:** `/app/test_document_ai_manual.py`

```python
"""
Manual integration test for Document AI refactor
Test with real Survey Report service
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from app.utils.document_ai_helper import (
    analyze_survey_report_with_document_ai,
    analyze_test_report_with_document_ai
)


async def test_survey_report_backward_compatibility():
    """Test that Survey Report still works after refactor"""
    print("="*80)
    print("TEST 1: Survey Report Backward Compatibility")
    print("="*80)
    
    # Mock PDF content
    pdf_content = b'%PDF-1.4\n%Test PDF\n%%EOF'
    
    # Mock config (replace with real config for actual test)
    config = {
        "project_id": "test-project",
        "processor_id": "test-processor",
        "location": "us",
        "apps_script_url": "https://script.google.com/test"
    }
    
    try:
        result = await analyze_survey_report_with_document_ai(
            file_content=pdf_content,
            filename="test_survey.pdf",
            content_type="application/pdf",
            document_ai_config=config
        )
        
        print(f"✅ Function called successfully")
        print(f"   Success: {result.get('success')}")
        print(f"   Message: {result.get('message', 'N/A')}")
        
        if result.get('success'):
            summary = result.get('data', {}).get('summary', '')
            print(f"   Summary length: {len(summary)} chars")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_test_report_new_wrapper():
    """Test that Test Report wrapper works"""
    print("\n" + "="*80)
    print("TEST 2: Test Report New Wrapper")
    print("="*80)
    
    pdf_content = b'%PDF-1.4\n%Test PDF\n%%EOF'
    
    config = {
        "project_id": "test-project",
        "processor_id": "test-processor",
        "location": "us",
        "apps_script_url": "https://script.google.com/test"
    }
    
    try:
        result = await analyze_test_report_with_document_ai(
            file_content=pdf_content,
            filename="test_eebd.pdf",
            content_type="application/pdf",
            document_ai_config=config
        )
        
        print(f"✅ Function called successfully")
        print(f"   Success: {result.get('success')}")
        print(f"   Message: {result.get('message', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all manual tests"""
    await test_survey_report_backward_compatibility()
    await test_test_report_new_wrapper()
    
    print("\n" + "="*80)
    print("MANUAL TESTS COMPLETED")
    print("="*80)


if __name__ == '__main__':
    asyncio.run(main())
```

**Run manual test:**

```bash
cd /app
python test_document_ai_manual.py
```

---

### STEP 3: Test with Real Survey Report Flow (30 phút)

**Objective:** Verify Survey Report still works end-to-end

**Test Steps:**

1. **Start backend:**
   ```bash
   sudo supervisorctl restart backend
   tail -f /var/log/supervisor/backend.*.log
   ```

2. **Upload a real Survey Report PDF:**
   - Go to frontend
   - Select a ship
   - Upload a Survey Report PDF
   - Click "Analyze"

3. **Verify logs:**
   ```bash
   grep "Document AI" /var/log/supervisor/backend.*.log | tail -20
   ```

4. **Expected logs:**
   ```
   🔄 Survey Report wrapper called for: cargo_gear_survey.pdf
   🤖 Calling Google Document AI for survey_report: cargo_gear_survey.pdf
   📦 Encoded file to base64: XXXXX chars
   📤 Sending request to Apps Script: https://...
   ✅ Document AI analysis completed for survey_report
      Summary length: 2500 characters
   ```

5. **Verify form auto-fill:**
   - Check if fields are filled correctly
   - No errors in browser console

**Checklist:**
- [ ] Backend starts without errors
- [ ] Survey Report upload works
- [ ] Analysis completes successfully
- [ ] Form auto-fills correctly
- [ ] No regression bugs

---

## 6. ROLLBACK PLAN

### If Something Goes Wrong:

#### OPTION 1: Quick Rollback (1 phút)

```bash
# Restore backup
cp /app/backend/app/utils/document_ai_helper.py.backup \
   /app/backend/app/utils/document_ai_helper.py

# Restart backend
sudo supervisorctl restart backend

# Verify
tail -f /var/log/supervisor/backend.*.log
```

#### OPTION 2: Identify and Fix Issue (10-30 phút)

**Common Issues:**

1. **Import Error:**
   ```
   Error: cannot import name 'analyze_test_report_with_document_ai'
   ```
   **Fix:** Check function name spelling

2. **Syntax Error:**
   ```
   SyntaxError: invalid syntax at line XX
   ```
   **Fix:** Check parentheses, colons, indentation

3. **Survey Report Broken:**
   ```
   Error: missing positional argument 'document_type'
   ```
   **Fix:** Verify wrapper signature matches old function

4. **Test Fails:**
   ```
   AssertionError: Expected success=True, got success=False
   ```
   **Fix:** Check mock setup, verify payload structure

**Debug Steps:**

```bash
# 1. Check syntax
python -m py_compile /app/backend/app/utils/document_ai_helper.py

# 2. Interactive test
cd /app/backend
python -c "from app.utils.document_ai_helper import analyze_survey_report_with_document_ai; print('OK')"

# 3. Check imports in service
python -c "from app.services.survey_report_analyze_service import SurveyReportAnalyzeService; print('OK')"
```

---

## 7. TROUBLESHOOTING

### Issue 1: Function Not Found

**Symptoms:**
```
ImportError: cannot import name 'analyze_test_report_with_document_ai'
```

**Cause:** Function not defined or typo in name

**Fix:**
1. Check function definition exists
2. Check spelling matches import
3. Check __all__ export list

---

### Issue 2: Backward Compatibility Broken

**Symptoms:**
```
Survey Report upload fails after refactor
```

**Cause:** Wrapper doesn't match old signature

**Fix:**
1. Compare old vs new function signature
2. Ensure wrapper has same parameters
3. Verify return value structure unchanged

---

### Issue 3: Document Type Not Working

**Symptoms:**
```
Warning: Unsupported document_type: test_report, using 'other'
```

**Cause:** Typo in document_type or not in SUPPORTED_TYPES list

**Fix:**
1. Check SUPPORTED_TYPES list in generic function
2. Add missing type to list
3. Verify spelling matches

---

### Issue 4: Apps Script Errors

**Symptoms:**
```
Apps Script HTTP error: 400
```

**Cause:** Payload structure changed

**Fix:**
1. Compare old vs new payload
2. Verify "action" field is same
3. Check document_type field sent correctly

---

## 8. COMPLETION CHECKLIST

### Before Committing:

- [ ] Backup created
- [ ] Generic function implemented
- [ ] Survey Report wrapper works (backward compatible)
- [ ] Test Report wrapper added
- [ ] Audit Report wrapper added
- [ ] Other wrappers added (optional)
- [ ] __all__ export list updated
- [ ] Unit tests written
- [ ] Unit tests pass
- [ ] Manual integration test done
- [ ] Real Survey Report flow tested
- [ ] No regression bugs
- [ ] Logs show correct document_type
- [ ] Documentation updated

### After Committing:

- [ ] Survey Report Analyze Service still works
- [ ] No errors in production logs
- [ ] Ready to use for Test Report migration

---

## 9. NEXT STEPS

After completing this refactor:

1. ✅ **Update Survey Report Service** (Task 1.4)
   - Add `document_type='survey_report'` to calls (optional, wrapper handles it)
   - No changes required if using wrapper

2. ✅ **Create Test Report Analyze Service** (Task 2.3)
   - Use `analyze_test_report_with_document_ai()` wrapper
   - Or call generic function with `document_type='test_report'`

3. ✅ **Future Document Types**
   - Just add new wrapper function
   - Or call generic function with new type
   - No need to change core logic

---

## ✅ SUCCESS CRITERIA

Refactor is successful when:

1. ✅ Generic function works with all document types
2. ✅ Survey Report wrapper maintains backward compatibility
3. ✅ Test Report wrapper works correctly
4. ✅ All unit tests pass
5. ✅ Real Survey Report flow still works
6. ✅ No errors in logs
7. ✅ Code is clean and well-documented

---

**Estimated Time: 2-3 hours**

**Difficulty: Medium**

**Priority: High** (Blocking Test Report migration)

---

**Ready to start refactoring!** 🚀


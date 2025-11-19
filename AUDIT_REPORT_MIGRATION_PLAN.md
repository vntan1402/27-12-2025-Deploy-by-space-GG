# AUDIT REPORT MIGRATION PLAN - Backend V1 → Backend V2 (FastAPI)

## 📋 MỤC LỤC

1. [Tổng Quan Migration](#1-tổng-quan-migration)
2. [Kiểm Tra Hiện Trạng Backend Mới](#2-kiểm-tra-hiện-trạng-backend-mới)
3. [Các File Cần Tạo Mới](#3-các-file-cần-tạo-mới)
4. [Các File Cần Chỉnh Sửa](#4-các-file-cần-chỉnh-sửa)
5. [Chi Tiết Từng Phase](#5-chi-tiết-từng-phase)
6. [Testing Plan](#6-testing-plan)
7. [Checklist Hoàn Thành](#7-checklist-hoàn-thành)

---

## 1. TỔNG QUAN MIGRATION

### 🎯 Mục Tiêu

Migrate toàn bộ chức năng "Add Audit Report" từ backend-v1 sang backend mới (FastAPI), đảm bảo:
- ✅ Giữ nguyên 100% logic của backend V1
- ✅ Tái sử dụng tối đa utilities/helpers đã có
- ✅ Áp dụng improvements từ Approval Document & Survey Report
- ✅ Đúng folder path: `ShipName/ISM - ISPS - MLC/Audit Report/` (có spaces)

### 📊 So Sánh Backend V1 vs V2

| Aspect | Backend V1 | Backend V2 (Target) |
|--------|-----------|---------------------|
| **Framework** | FastAPI (monolithic) | FastAPI (modular structure) |
| **Service Layer** | Inside server.py | Separate service files |
| **AI Utilities** | Mixed in server.py | Separate AI helper files |
| **GDrive** | dual_apps_script_manager.py | gdrive_service.py + gdrive_helper.py |
| **PDF Splitting** | pdf_splitter.py | pdf_splitter.py (enhanced) |
| **Folder Path** | `ISM-ISPS-MLC` (hyphens) | `ISM - ISPS - MLC` (spaces) |

### 🔑 Key Differences vs Approval Document

Audit Report và Approval Document rất giống nhau, nhưng có các điểm khác:

| Feature | Audit Report | Approval Document |
|---------|--------------|-------------------|
| **Fields** | `auditor_name`, `report_form` | `approved_by`, `approved_date` |
| **GDrive Path** | `ISM - ISPS - MLC/Audit Report/` | `ISM - ISPS - MLC/Approval Document/` |
| **Document Type** | `audit_report` | `approval_document` |
| **AI Extraction** | Extract auditor info | Extract approval info |

---

## 2. KIỂM TRA HIỆN TRẠNG BACKEND MỚI

### ✅ Files Đã Có (Có Thể Tái Sử Dụng)

#### 2.1 API Endpoints
```
/app/backend/app/api/v1/audit_reports.py
```
**Status:** ✅ Đã có CRUD cơ bản
**Cần thêm:**
- `POST /analyze-file` endpoint (đã có placeholder line 115-127)
- `POST /{report_id}/upload-files` endpoint

#### 2.2 Service Layer
```
/app/backend/app/services/audit_report_service.py
```
**Status:** ✅ Đã có CRUD cơ bản
**Cần thêm:**
- Background file deletion
- Upload files method

#### 2.3 Models
```
/app/backend/app/models/audit_report.py
```
**Status:** ✅ Đã có đầy đủ models

#### 2.4 Utilities (Đã Có - Tái Sử Dụng)

✅ **PDF Processing:**
- `/app/backend/app/utils/pdf_splitter.py` - PDF splitting (max 12 pages/chunk)
- `/app/backend/app/utils/pdf_processor.py` - PDF utilities

✅ **Document AI:**
- `/app/backend/app/utils/document_ai_helper.py` - Document AI integration
- `/app/backend/app/utils/ai_helper.py` - System AI helper

✅ **GDrive:**
- `/app/backend/app/utils/gdrive_helper.py` - GDrive operations
- `/app/backend/app/services/gdrive_service.py` - GDrive service layer

✅ **Other Helpers:**
- `/app/backend/app/utils/issued_by_abbreviation.py` - Normalize issued_by
- `/app/backend/app/utils/targeted_ocr.py` - OCR for header/footer

✅ **Background Tasks:**
- `/app/backend/app/utils/background_tasks.py` - Async file deletion

### ❌ Files Chưa Có (Cần Tạo Mới)

#### 2.5 Analysis Service
```
/app/backend/app/services/audit_report_analyze_service.py
```
**Status:** ❌ Chưa có
**Pattern:** Copy từ `approval_document_analyze_service.py`

#### 2.6 AI Helper
```
/app/backend/app/utils/audit_report_ai.py
```
**Status:** ❌ Chưa có
**Pattern:** Copy từ `approval_document_ai.py`

---

## 3. CÁC FILE CẦN TẠO MỚI

### 3.1 Audit Report Analysis Service

**File:** `/app/backend/app/services/audit_report_analyze_service.py`

**Base:** Copy từ `approval_document_analyze_service.py`

**Modifications:**
```python
# Class name
class ApprovalDocumentAnalyzeService → class AuditReportAnalyzeService

# Document type
document_type="approval_document" → document_type="audit_report"

# Field extraction
from app.utils.approval_document_ai import extract_approval_document_fields_from_summary
→
from app.utils.audit_report_ai import extract_audit_report_fields_from_summary

# Analysis result fields
{
    "approval_document_name": ...,    → "audit_report_name": ...,
    "approved_by": ...,                → "issued_by": ...,
    "approved_date": ...,              → "audit_date": ...,
    # Add new fields:
    "audit_type": ...,
    "report_form": ...,
    "auditor_name": ...,
}
```

**Key Methods:**
```python
async def analyze_file(
    file: UploadFile,
    ship_id: str,
    bypass_validation: bool,
    current_user: UserResponse
) -> Dict[str, Any]

async def _process_document_ai_analysis(
    file_content: bytes,
    filename: str,
    document_ai_config: Dict[str, Any]
) -> str  # Returns summary text

async def _extract_fields_from_summary(
    summary_text: str,
    filename: str,
    ai_config: Dict[str, Any]
) -> Dict[str, Any]
```

---

### 3.2 Audit Report AI Helper

**File:** `/app/backend/app/utils/audit_report_ai.py`

**Base:** Copy từ `approval_document_ai.py`

**Modifications:**
```python
# Function name
async def extract_approval_document_fields_from_summary(...)
→
async def extract_audit_report_fields_from_summary(...)

# Extraction prompt
def create_audit_report_extraction_prompt(summary_text: str, filename: str = "") -> str:
    """
    Create prompt for Audit Report field extraction
    """
    return f"""You are an AI specialized in maritime audit report information extraction.

**TASK**: Extract key information from this audit report Document AI summary.

**FILENAME**: {filename}

**EXTRACT THE FOLLOWING FIELDS** (return as JSON):

{{
    "audit_report_name": "Main title or name of audit report",
    "audit_type": "Type of audit (ISM, ISPS, MLC, CICA)",
    "report_form": "**CRITICAL** - Form code/number (e.g., '07-23', 'CG (02-19)')",
    "audit_report_no": "Report number or reference",
    "issued_by": "**IMPORTANT** - Organization that issued/conducted audit",
    "audit_date": "Date of audit (YYYY-MM-DD format)",
    "auditor_name": "Name(s) of auditor(s)",
    "ship_name": "Name of ship being audited",
    "ship_imo": "IMO number (7 digits only)",
    "note": "Any important notes or observations"
}}

**CRITICAL INSTRUCTIONS FOR REPORT_FORM**:
- Look in footer/header sections first
- May appear as "(07-23)", "Form 7.10", "CG (02-19)", etc.
- Check "ADDITIONAL INFORMATION FROM HEADER/FOOTER" section
- Filename hint: {filename}

**CRITICAL INSTRUCTIONS FOR ISSUED_BY**:
- Look in letterhead/header sections first
- Extract FULL organization name (not just abbreviation)
- Common organizations: DNV GL, Lloyd's Register, Bureau Veritas, PMDS, Class NK, ABS
- DO NOT confuse with auditor name

**CRITICAL INSTRUCTIONS FOR AUDIT_TYPE**:
- Must be one of: ISM, ISPS, MLC, CICA
- Check report_form for hints (e.g., "ISM-AUD-01" → ISM)
- Check filename for hints
- Normalize variations (e.g., "ISM CODE" → "ISM")

**OUTPUT**: Return ONLY valid JSON, no extra text.

---

**DOCUMENT TEXT:**

{summary_text}
"""

# Field mapping & post-processing
# Same logic as Backend V1 extract_audit_report_fields_from_summary()
```

**Key Functions:**
```python
async def extract_audit_report_fields_from_summary(
    summary_text: str,
    filename: str,
    ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract audit report fields from Document AI summary using System AI
    
    Returns:
        dict with fields:
        - audit_report_name
        - audit_type (ISM/ISPS/MLC/CICA)
        - report_form
        - audit_report_no
        - issued_by (normalized)
        - audit_date (YYYY-MM-DD)
        - auditor_name
        - ship_name
        - ship_imo
        - note
    """
    # 1. Create extraction prompt
    # 2. Call System AI (Gemini)
    # 3. Parse JSON response
    # 4. Post-processing:
    #    - Parse audit_date (check if it's a report_form)
    #    - Determine audit_type from multiple sources
    #    - Extract report_form from filename patterns
    #    - Normalize issued_by
    # 5. Return extracted data

def create_audit_report_extraction_prompt(summary_text: str, filename: str) -> str:
    """Create structured prompt for audit report field extraction"""
    pass
```

---

## 4. CÁC FILE CẦN CHỈNH SỬA

### 4.1 API Router - `/app/backend/app/api/v1/audit_reports.py`

**Current Status:** Line 115-127 có placeholder

**Changes Needed:**

#### 4.1.1 Import Thêm
```python
from fastapi import BackgroundTasks, Form
from app.services.audit_report_analyze_service import AuditReportAnalyzeService
```

#### 4.1.2 Replace Analyze Endpoint (Lines 115-127)
```python
@router.post("/analyze-file")
async def analyze_audit_report_file(
    file: UploadFile = File(...),
    ship_id: str = Form(...),
    bypass_validation: str = Form("false"),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze audit report file using Document AI + System AI
    
    Returns analysis result with:
    - Extracted fields (audit_report_name, audit_type, report_form, etc.)
    - Base64 file content (_file_content)
    - Summary text (_summary_text)
    - Split info if applicable (_split_info)
    """
    try:
        # Convert bypass_validation string to boolean
        bypass_validation_bool = bypass_validation.lower() in ('true', '1', 'yes')
        
        # Call analysis service
        result = await AuditReportAnalyzeService.analyze_file(
            file=file,
            ship_id=ship_id,
            bypass_validation=bypass_validation_bool,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing audit report file: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to analyze audit report file: {str(e)}")
```

#### 4.1.3 Add Upload Files Endpoint
```python
@router.post("/{report_id}/upload-files")
async def upload_audit_report_files(
    report_id: str,
    file_content: str = Form(...),
    filename: str = Form(...),
    content_type: str = Form(...),
    summary_text: str = Form(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Upload audit report files to Google Drive
    
    1. Decode base64 file content
    2. Upload original file to: ShipName/ISM - ISPS - MLC/Audit Report/
    3. Upload summary if provided
    4. Update audit report record with file IDs
    """
    try:
        result = await AuditReportService.upload_files(
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
        logger.error(f"❌ Error uploading audit report files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload audit report files: {str(e)}")
```

#### 4.1.4 Update Delete Endpoints (Add BackgroundTasks)
```python
# Update line 75-87
@router.delete("/{report_id}")
async def delete_audit_report(
    report_id: str,
    background_tasks: BackgroundTasks,  # ADD THIS
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Audit Report (Editor+ role required)"""
    try:
        return await AuditReportService.delete_audit_report(
            report_id, 
            background_tasks,  # ADD THIS
            current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Audit Report: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Audit Report")

# Update line 89-99
@router.post("/bulk-delete")
async def bulk_delete_audit_reports(
    request: BulkDeleteAuditReportRequest,
    background_tasks: BackgroundTasks,  # ADD THIS
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Audit Reports (Editor+ role required)"""
    try:
        return await AuditReportService.bulk_delete_audit_reports(
            request, 
            background_tasks,  # ADD THIS
            current_user
        )
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Audit Reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Audit Reports")
```

#### 4.1.5 Fix Route Ordering

**CRITICAL:** Place static routes BEFORE dynamic routes to avoid 404 errors

```python
# Current order (WRONG):
@router.get("", ...)              # Line 19
@router.get("/{report_id}", ...)  # Line 32 - DYNAMIC ROUTE
@router.post("", ...)             # Line 46
@router.put("/{report_id}", ...)  # Line 60
@router.delete("/{report_id}")    # Line 75
@router.post("/bulk-delete")      # Line 89 - STATIC ROUTE (TOO LATE!)
@router.post("/check-duplicate")  # Line 101
@router.post("/analyze")          # Line 115

# Correct order (RIGHT):
@router.post("/analyze-file")        # STATIC - Place first
@router.post("/bulk-delete")         # STATIC - Place first
@router.post("/check-duplicate")     # STATIC - Place first
@router.get("", ...)                 # Collection route
@router.post("", ...)                # Collection route
@router.get("/{report_id}", ...)     # DYNAMIC - Place after static
@router.put("/{report_id}", ...)     # DYNAMIC
@router.delete("/{report_id}")       # DYNAMIC
@router.post("/{report_id}/upload-files")  # DYNAMIC
```

---

### 4.2 Service Layer - `/app/backend/app/services/audit_report_service.py`

**Changes Needed:**

#### 4.2.1 Import Thêm
```python
import base64
from fastapi import BackgroundTasks
from app.services.gdrive_service import GDriveService
from app.utils.background_tasks import schedule_file_deletion
```

#### 4.2.2 Add Upload Files Method
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
    Upload audit report files to Google Drive
    
    Path: ShipName/ISM - ISPS - MLC/Audit Report/
    
    Args:
        report_id: Audit report ID
        file_content: Base64 encoded file content
        filename: Original filename
        content_type: MIME type
        summary_text: Summary text to upload
        current_user: Current authenticated user
        
    Returns:
        dict: {
            "success": True,
            "file_id": str,
            "summary_file_id": str,
            "message": str
        }
    """
    try:
        logger.info(f"📤 Starting file upload for audit report: {report_id}")
        
        # 1. Validate report exists
        report = await mongo_db.find_one("audit_reports", {"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Audit report not found")
        
        # 2. Get company UUID
        company_uuid = current_user.company
        if not company_uuid:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # 3. Get ship info
        ship_id = report.get("ship_id")
        if not ship_id:
            raise HTTPException(status_code=400, detail="Audit report has no ship_id")
        
        ship = await mongo_db.find_one("ships", {"id": ship_id, "company": company_uuid})
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        ship_name = ship.get("name", "Unknown Ship")
        
        # 4. Decode base64 file content
        try:
            file_bytes = base64.b64decode(file_content)
            logger.info(f"✅ Decoded file content: {len(file_bytes)} bytes")
        except Exception as e:
            logger.error(f"Failed to decode base64 file content: {e}")
            raise HTTPException(status_code=400, detail="Invalid file content encoding")
        
        # 5. Upload original file
        # Path: ShipName/ISM - ISPS - MLC/Audit Report/
        logger.info(f"📄 Uploading original file: {ship_name}/ISM - ISPS - MLC/Audit Report/{filename}")
        
        original_file_id = await GDriveService.upload_file(
            file_content=file_bytes,
            filename=filename,
            content_type=content_type,
            ship_name=ship_name,
            parent_category="ISM - ISPS - MLC",  # NOTE: with spaces!
            category="Audit Report",
            company_uuid=company_uuid
        )
        
        logger.info(f"✅ Original file uploaded: {original_file_id}")
        
        # 6. Upload summary file (if provided)
        summary_file_id = None
        if summary_text and summary_text.strip():
            base_name = filename.rsplit('.', 1)[0]
            summary_filename = f"{base_name}_Summary.txt"
            
            logger.info(f"📋 Uploading summary file: {summary_filename}")
            
            summary_bytes = summary_text.encode('utf-8')
            
            summary_file_id = await GDriveService.upload_file(
                file_content=summary_bytes,
                filename=summary_filename,
                content_type="text/plain",
                ship_name=ship_name,
                parent_category="ISM - ISPS - MLC",
                category="Audit Report",
                company_uuid=company_uuid
            )
            
            logger.info(f"✅ Summary file uploaded: {summary_file_id}")
        
        # 7. Update database with file IDs
        from datetime import datetime, timezone
        update_data = {
            "audit_report_file_id": original_file_id,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if summary_file_id:
            update_data["audit_report_summary_file_id"] = summary_file_id
        
        await mongo_db.update("audit_reports", {"id": report_id}, update_data)
        
        logger.info(f"✅ Files uploaded successfully for audit report: {report_id}")
        
        return {
            "success": True,
            "file_id": original_file_id,
            "summary_file_id": summary_file_id,
            "message": "Files uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading audit report files: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to upload files: {str(e)}")
```

#### 4.2.3 Update Delete Methods (Add Background Deletion)

**Pattern:** Same as Approval Document

```python
@staticmethod
async def delete_audit_report(
    report_id: str, 
    background_tasks: BackgroundTasks,  # ADD THIS
    current_user: UserResponse
) -> Dict[str, str]:
    """Delete audit report by ID with background GDrive file deletion"""
    try:
        # Get company UUID
        company_uuid = current_user.company
        if not company_uuid:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Find audit report
        report = await mongo_db.find_one("audit_reports", {"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Audit report not found")
        
        # Check permission (only delete own company's reports)
        ship_id = report.get("ship_id")
        ship = await mongo_db.find_one("ships", {"id": ship_id, "company": company_uuid})
        if not ship:
            raise HTTPException(status_code=403, detail="Not authorized to delete this audit report")
        
        # Get file IDs for background deletion
        audit_report_file_id = report.get("audit_report_file_id")
        audit_report_summary_file_id = report.get("audit_report_summary_file_id")
        
        # Delete from database first
        deleted_count = await mongo_db.delete("audit_reports", {"id": report_id})
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Audit report not found")
        
        # Schedule background file deletion
        if audit_report_file_id:
            schedule_file_deletion(
                background_tasks,
                audit_report_file_id,
                company_uuid,
                "Audit Report (original)"
            )
        
        if audit_report_summary_file_id:
            schedule_file_deletion(
                background_tasks,
                audit_report_summary_file_id,
                company_uuid,
                "Audit Report (summary)"
            )
        
        logger.info(f"✅ Audit report {report_id} deleted successfully")
        return {"message": "Audit report deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting audit report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete audit report: {str(e)}")

@staticmethod
async def bulk_delete_audit_reports(
    request: BulkDeleteAuditReportRequest,
    background_tasks: BackgroundTasks,  # ADD THIS
    current_user: UserResponse
) -> Dict[str, Any]:
    """
    Bulk delete audit reports with background GDrive file deletion
    
    Pattern: Same as Approval Document
    Iterate through report_ids and call delete_audit_report for each
    """
    try:
        report_ids = request.report_ids
        
        if not report_ids or len(report_ids) == 0:
            raise HTTPException(status_code=400, detail="No report IDs provided")
        
        logger.info(f"📦 Bulk deleting {len(report_ids)} audit reports")
        
        deleted_count = 0
        failed_count = 0
        errors = []
        
        # Delete each report individually (for proper background deletion)
        for report_id in report_ids:
            try:
                await AuditReportService.delete_audit_report(
                    report_id=report_id,
                    background_tasks=background_tasks,
                    current_user=current_user
                )
                deleted_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to delete {report_id}: {str(e)}")
                logger.error(f"Failed to delete audit report {report_id}: {e}")
        
        logger.info(f"✅ Bulk delete completed: {deleted_count} deleted, {failed_count} failed")
        
        return {
            "message": f"Bulk delete completed: {deleted_count} deleted, {failed_count} failed",
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in bulk delete: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete audit reports: {str(e)}")
```

---

### 4.3 PDF Splitter - `/app/backend/app/utils/pdf_splitter.py`

**Current Status:** Already updated with dynamic field mapping

**Verify Field Mapping:** Check if `audit_report` fields are mapped correctly

```python
# In merge_analysis_results() function
FIELD_MAPPINGS = {
    'survey_report': {
        'name': ['survey_report_name', 'document_name'],
        'number': ['survey_report_no', 'document_no'],
        'inspector': ['surveyor_name', 'inspector_name'],
        # ... other mappings
    },
    'approval_document': {
        'name': ['approval_document_name', 'document_name'],
        'number': ['approval_document_no', 'document_no'],
        'approved_by': ['approved_by', 'issued_by'],
        'approved_date': ['approved_date', 'approval_date', 'issued_date'],
        # ... other mappings
    },
    'audit_report': {  # ADD THIS
        'name': ['audit_report_name', 'document_name'],
        'number': ['audit_report_no', 'document_no'],
        'type': ['audit_type'],
        'form': ['report_form'],
        'auditor': ['auditor_name', 'inspector_name'],
        'issued_by': ['issued_by'],
        'audit_date': ['audit_date', 'issued_date'],
        'ship_name': ['ship_name'],
        'ship_imo': ['ship_imo'],
        'note': ['note'],
        'status': ['status']
    }
}
```

**If not added yet:** Add the field mapping for `audit_report` document type

---

### 4.4 GDrive Helper - `/app/backend/app/utils/gdrive_helper.py`

**Current Status:** Already supports nested folders with `parent_category` + `category`

**Verify:** Path format uses spaces

```python
# Example usage for Audit Report:
parent_category = "ISM - ISPS - MLC"  # with spaces
category = "Audit Report"

# Creates: ShipName/ISM - ISPS - MLC/Audit Report/
```

**No changes needed if Approval Document already uses the same path format.**

---

## 5. CHI TIẾT TỪNG PHASE

### 📌 PHASE 1: Tạo AI Helper & Analysis Service

**Duration:** 30-45 minutes

**Tasks:**

1. **Create `audit_report_ai.py`**
   - Copy từ `approval_document_ai.py`
   - Rename functions
   - Update extraction prompt với audit report fields
   - Add post-processing logic:
     - Parse `audit_date` (check if it's `report_form`)
     - Determine `audit_type` from multiple sources
     - Extract `report_form` from filename patterns
     - Normalize `issued_by`

2. **Create `audit_report_analyze_service.py`**
   - Copy từ `approval_document_analyze_service.py`
   - Update class name, imports
   - Change document_type to `"audit_report"`
   - Update field mapping in analysis result
   - Add `audit_type`, `report_form`, `auditor_name` fields

3. **Test AI Helper Standalone**
   ```python
   # Test extraction with sample summary text
   python -c "
   import asyncio
   from app.utils.audit_report_ai import extract_audit_report_fields_from_summary
   
   result = asyncio.run(extract_audit_report_fields_from_summary(
       summary_text='ISM Annual Audit Report...',
       filename='ISM_Annual_Audit_2024.pdf',
       ai_config={...}
   ))
   print(result)
   "
   ```

**Expected Output:**
```json
{
  "audit_report_name": "ISM Annual Audit 2024",
  "audit_type": "ISM",
  "report_form": "07-23",
  "audit_report_no": "AR-2024-001",
  "issued_by": "DNV GL",
  "audit_date": "2024-01-15",
  "auditor_name": "John Smith",
  "ship_name": "MV ATLANTIC HERO",
  "ship_imo": "9876543"
}
```

---

### 📌 PHASE 2: Update API Router & Service

**Duration:** 30-45 minutes

**Tasks:**

1. **Update `audit_reports.py` router**
   - Add imports (BackgroundTasks, Form, AnalyzeService)
   - Fix route ordering (static before dynamic)
   - Replace `/analyze-file` endpoint (remove placeholder)
   - Add `/{report_id}/upload-files` endpoint
   - Update delete endpoints with BackgroundTasks

2. **Update `audit_report_service.py`**
   - Add `upload_files()` method
   - Update `delete_audit_report()` with background deletion
   - Update `bulk_delete_audit_reports()` with background deletion

3. **Verify PDF Splitter Field Mapping**
   - Check if `audit_report` mapping exists in `pdf_splitter.py`
   - Add if missing

4. **Test Service Methods**
   ```bash
   # Test in Python shell
   python -c "
   import asyncio
   from app.services.audit_report_service import AuditReportService
   
   # Test upload_files
   # Test delete with background tasks
   "
   ```

---

### 📌 PHASE 3: Integration Testing

**Duration:** 45-60 minutes

**Tasks:**

1. **Restart Backend**
   ```bash
   sudo supervisorctl restart backend
   tail -f /var/log/supervisor/backend.out.log
   ```

2. **Test Analyze Endpoint (Small File)**
   ```bash
   # Test with PDF ≤15 pages
   curl -X POST http://localhost:8001/api/audit-reports/analyze-file \
     -F "file=@small_audit_report.pdf" \
     -F "ship_id=ship-123" \
     -F "bypass_validation=false" \
     -H "Authorization: Bearer $TOKEN"
   ```

3. **Test Analyze Endpoint (Large File)**
   ```bash
   # Test with PDF >15 pages (should split into chunks)
   curl -X POST http://localhost:8001/api/audit-reports/analyze-file \
     -F "file=@large_audit_report.pdf" \
     -F "ship_id=ship-123" \
     -F "bypass_validation=false" \
     -H "Authorization: Bearer $TOKEN"
   ```

4. **Test Complete Flow**
   - Analyze file
   - Create audit report record
   - Upload files to GDrive
   - Verify file IDs in database
   - Check GDrive folder structure

5. **Test Ship Validation**
   - Upload file with wrong ship name
   - Should return validation error
   - Retry with bypass_validation=true
   - Should succeed

6. **Test Delete with Background Tasks**
   - Delete audit report
   - Verify DB record deleted immediately
   - Check logs for background file deletion
   - Verify files removed from GDrive

7. **Test Bulk Delete**
   - Create multiple audit reports
   - Bulk delete
   - Verify all deleted
   - Check background deletion logs

---

### 📌 PHASE 4: Frontend Integration (Optional)

**Duration:** 15-30 minutes

**Tasks:**

1. **Verify Frontend Service**
   - Check `/app/frontend/src/services/auditReportService.js`
   - Ensure it calls correct endpoints:
     - `POST /api/audit-reports/analyze-file`
     - `POST /api/audit-reports/{id}/upload-files`

2. **Update Frontend if Needed**
   - Change endpoint paths if different
   - Update request format (FormData)

3. **Test E2E Flow**
   - Upload single file
   - Upload batch files
   - Edit audit report
   - Delete audit report
   - Bulk delete

---

### 📌 PHASE 5: Final Verification

**Duration:** 15-30 minutes

**Tasks:**

1. **Verify GDrive Path**
   - Check folder structure: `ShipName/ISM - ISPS - MLC/Audit Report/`
   - Verify spaces in folder name (not hyphens)
   - Check both original and summary files uploaded

2. **Verify Field Extraction**
   - Check all fields extracted correctly:
     - `audit_report_name`
     - `audit_type` (ISM/ISPS/MLC/CICA)
     - `report_form` (from header/footer)
     - `audit_report_no`
     - `issued_by` (normalized abbreviation)
     - `audit_date` (YYYY-MM-DD format)
     - `auditor_name`
     - `ship_name` & `ship_imo`

3. **Verify PDF Splitting**
   - Upload 20-page PDF
   - Check logs for chunk processing
   - Verify merged results
   - Check `_split_info` in response

4. **Verify OCR Enhancement**
   - Check if header/footer text extracted
   - Verify OCR section in summary
   - Check report_form extracted from footer

5. **Compare with Backend V1**
   - Test same file in both backends
   - Compare extracted fields
   - Verify results match

---

## 6. TESTING PLAN

### 6.1 Unit Tests

**Test Files to Create:**

```
/app/backend/tests/test_audit_report_ai.py
/app/backend/tests/test_audit_report_analyze_service.py
/app/backend/tests/test_audit_report_service.py
```

**Test Cases:**

1. **AI Helper Tests**
   - Extract from valid summary
   - Extract from empty summary
   - Parse audit_date correctly
   - Determine audit_type from filename
   - Extract report_form from filename patterns
   - Normalize issued_by

2. **Analysis Service Tests**
   - Analyze small PDF (≤15 pages)
   - Analyze large PDF (>15 pages, with splitting)
   - Handle invalid PDF
   - Handle ship validation error
   - Handle OCR enhancement

3. **Service Layer Tests**
   - Upload files
   - Delete with background tasks
   - Bulk delete
   - Handle missing ship
   - Handle GDrive errors

### 6.2 Integration Tests

**Test Scenarios:**

| Scenario | Input | Expected Output |
|----------|-------|----------------|
| Small PDF | 10-page audit report | Single file processing, all fields extracted |
| Large PDF | 20-page audit report | Split into 2 chunks, merged results |
| Wrong Ship | PDF with different ship name | Validation error returned |
| Bypass Validation | Same PDF with bypass=true | Analysis succeeds |
| OCR Required | PDF with footer report_form | report_form extracted from OCR |
| Upload Files | After create | Files uploaded to correct GDrive path |
| Delete | Single audit report | DB deleted, GDrive files scheduled for deletion |
| Bulk Delete | 5 audit reports | All deleted, background tasks scheduled |

### 6.3 Backend Testing Agent

**Use:** `deep_testing_backend_v2`

**Task:**
```
Test the complete Audit Report module in backend V2:

1. Analyze endpoint with small PDF (≤15 pages)
2. Analyze endpoint with large PDF (>15 pages, should split)
3. Analyze with ship validation error
4. Analyze with bypass_validation=true
5. Create audit report record
6. Upload files to GDrive (verify path: ShipName/ISM - ISPS - MLC/Audit Report/)
7. Update audit report
8. Delete audit report (verify background file deletion)
9. Bulk delete multiple audit reports

Verify:
- All fields extracted correctly (audit_type, report_form, auditor_name, etc.)
- PDF splitting works for >15 pages
- GDrive path uses spaces (not hyphens)
- Background deletion scheduled
- Error handling works
```

### 6.4 Frontend Testing (Optional)

**Use:** `auto_frontend_testing_agent`

**Task:**
```
Test the Audit Report UI:

1. Open Add Audit Report modal
2. Upload single PDF file
3. Verify AI analysis runs
4. Verify form auto-fills
5. Submit form
6. Verify background upload
7. Upload batch files (3-5 files)
8. Verify batch processing
9. Edit audit report
10. Delete audit report
11. Bulk delete multiple audit reports

Verify:
- File upload works (max 50MB)
- AI analysis shows loading state
- Form fields populated correctly
- Validation errors shown
- Success messages displayed
- Files uploaded in background
- Batch processing sequential
```

---

## 7. CHECKLIST HOÀN THÀNH

### ✅ Phase 1: AI Helper & Analysis Service

- [ ] Create `audit_report_ai.py`
  - [ ] `extract_audit_report_fields_from_summary()`
  - [ ] `create_audit_report_extraction_prompt()`
  - [ ] Post-processing logic (audit_date, audit_type, report_form)
  - [ ] Normalize issued_by
- [ ] Create `audit_report_analyze_service.py`
  - [ ] `analyze_file()` method
  - [ ] `_process_document_ai_analysis()` method
  - [ ] `_extract_fields_from_summary()` method
  - [ ] Ship validation logic
  - [ ] PDF splitting support
- [ ] Test AI extraction standalone

### ✅ Phase 2: API & Service Updates

- [ ] Update `audit_reports.py` router
  - [ ] Fix route ordering (static before dynamic)
  - [ ] Replace `/analyze-file` endpoint
  - [ ] Add `/{report_id}/upload-files` endpoint
  - [ ] Update delete endpoints with BackgroundTasks
- [ ] Update `audit_report_service.py`
  - [ ] Add `upload_files()` method
  - [ ] Update `delete_audit_report()` with background deletion
  - [ ] Update `bulk_delete_audit_reports()` with background deletion
- [ ] Verify `pdf_splitter.py` field mapping
  - [ ] Add `audit_report` mapping if missing
- [ ] Test service methods

### ✅ Phase 3: Integration Testing

- [ ] Restart backend server
- [ ] Test analyze endpoint (small file)
- [ ] Test analyze endpoint (large file with splitting)
- [ ] Test complete flow (analyze → create → upload)
- [ ] Test ship validation
- [ ] Test delete with background tasks
- [ ] Test bulk delete
- [ ] Check GDrive path: `ShipName/ISM - ISPS - MLC/Audit Report/`

### ✅ Phase 4: Frontend Integration (Optional)

- [ ] Verify frontend service
- [ ] Update endpoints if needed
- [ ] Test E2E flow
  - [ ] Single file upload
  - [ ] Batch file upload
  - [ ] Edit audit report
  - [ ] Delete audit report
  - [ ] Bulk delete

### ✅ Phase 5: Final Verification

- [ ] Verify GDrive path (with spaces)
- [ ] Verify all fields extracted correctly
- [ ] Verify PDF splitting (>15 pages)
- [ ] Verify OCR enhancement
- [ ] Compare results with Backend V1
- [ ] Run backend testing agent
- [ ] Run frontend testing agent (optional)
- [ ] Document any issues or differences

---

## 8. NOTES & GOTCHAS

### 🔴 Critical Path Differences

| Aspect | Backend V1 | Backend V2 |
|--------|-----------|------------|
| **Folder Name** | `ISM-ISPS-MLC` (hyphens) | `ISM - ISPS - MLC` (spaces) |
| **Path** | `dual_apps_script_manager` | `gdrive_service` + `gdrive_helper` |
| **Background Deletion** | Not used | Use `BackgroundTasks` |
| **Route Ordering** | Not critical (less routes) | Critical (404 if wrong) |

### ⚠️ Common Mistakes to Avoid

1. **Wrong folder name format** - Must use spaces, not hyphens
2. **Route ordering** - Static routes must come before dynamic routes
3. **Forgot BackgroundTasks** - Delete won't schedule GDrive cleanup
4. **Field mapping** - Must add `audit_report` to pdf_splitter.py
5. **Document type** - Must be `"audit_report"` (not `"audit"`)
6. **Date parsing** - Check if `audit_date` is actually a `report_form`

### 💡 Tips

- Reuse as much code as possible from Approval Document
- Test with both small and large PDFs
- Always check logs for background deletion
- Verify GDrive path manually in Google Drive
- Compare results with Backend V1 for same file

---

## 9. ROLLBACK PLAN

If migration fails:

1. **Keep existing placeholder** in `audit_reports.py` line 115-127
2. **Don't delete V1 code** - Keep `backend-v1` intact
3. **Frontend fallback** - Point frontend to V1 endpoints temporarily
4. **Document issues** - Create detailed issue report
5. **Fix incrementally** - Don't try to fix everything at once

---

## 10. SUCCESS CRITERIA

Migration is considered successful when:

✅ All audit report CRUD operations work
✅ AI analysis works for both small and large PDFs
✅ PDF splitting works correctly (>15 pages)
✅ All fields extracted correctly (same as V1)
✅ Files uploaded to correct GDrive path (with spaces)
✅ Background file deletion works
✅ Ship validation works (with bypass option)
✅ OCR enhancement extracts header/footer
✅ Frontend integration works (if applicable)
✅ All tests pass (backend & frontend)
✅ No regressions in existing modules

---

## END OF MIGRATION PLAN

**Estimated Total Time:** 3-4 hours

**Priority:** High (completes ISM-ISPS-MLC document suite)

**Dependencies:** 
- Approval Document migration (✅ completed)
- Survey Report migration (✅ completed)
- PDF Splitter enhancements (✅ completed)

**Next Steps:**
1. Review this plan with team
2. Get approval to proceed
3. Start with Phase 1
4. Test incrementally after each phase
5. Document any issues or changes

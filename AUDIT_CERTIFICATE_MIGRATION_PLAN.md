# 📋 AUDIT CERTIFICATE MIGRATION PLAN - Backend V1 → V2

## 🎯 MỤC TIÊU

Migrate toàn bộ module "Add Audit Certificate" từ Backend V1 sang Backend V2 với:
- ✅ Đầy đủ tính năng AI analysis
- ✅ Multi-upload với batch processing
- ✅ Google Drive integration (GDriveService V2)
- ✅ Validation & duplicate detection
- ✅ **Sửa path: `ISM-ISPS-MLC` → `ISM - ISPS - MLC`**
- ✅ **⭐ MỚI: Mở rộng hỗ trợ CICA (CREW ACCOMMODATION) certificate**

---

## 📊 PHÂN TÍCH HIỆN TRẠNG

### Backend V1 (Cần port):
```
/app/backend-v1/server.py
├── POST /audit-certificates/multi-upload     (lines 26961-27462)
├── analyze_document_with_ai()                 (lines 16143-16400)
├── check_ai_extraction_quality()              (inline function)
├── check_audit_certificate_duplicates()       (lines 4376-4405)
└── check_ism_isps_mlc_category()             (function name)
```

### Backend V2 (Hiện có):
```
/app/backend/app/api/v1/audit_certificates.py
├── GET    /audit-certificates                 ✅
├── GET    /audit-certificates/{cert_id}       ✅
├── POST   /audit-certificates                 ✅
├── PUT    /audit-certificates/{cert_id}       ✅
├── DELETE /audit-certificates/{cert_id}       ✅
├── POST   /audit-certificates/bulk-delete     ✅
└── POST   /audit-certificates/check-duplicate ✅
```

### Audit Reports V2 (Reference pattern):
```
/app/backend/app/
├── api/v1/audit_reports.py
│   ├── POST /audit-reports/analyze-file       ✅ (Reference)
│   └── POST /audit-reports/{id}/upload-files  ✅ (Reference)
├── services/
│   ├── audit_report_service.py                ✅ (Reference)
│   └── audit_report_analyze_service.py        ✅ (Reference)
└── utils/
    └── audit_report_ai.py                     ✅ (Reference)
```

---

## 🗂️ CẤU TRÚC FILES MỚI

### Phase 1: Core Files (Tạo mới)

```
/app/backend/app/
├── services/
│   └── audit_certificate_analyze_service.py   ⭐ NEW
│       ├── AuditCertificateAnalyzeService
│       ├── analyze_file()
│       ├── process_small_file()
│       ├── process_large_file()
│       ├── validate_ship_info()
│       ├── check_extraction_quality()
│       └── check_category_ism_isps_mlc()
│
├── utils/
│   └── audit_certificate_ai.py                ⭐ NEW
│       ├── extract_audit_certificate_fields()
│       ├── create_audit_certificate_prompt()
│       └── post_process_extracted_data()
│
└── api/v1/
    └── audit_certificates.py                  ⭐ MODIFY
        ├── POST /analyze-file                 ⭐ NEW
        ├── POST /multi-upload                 ⭐ NEW
        └── POST /create-with-file-override    ⭐ NEW
```

### Phase 2: Service Updates

```
/app/backend/app/services/
├── audit_certificate_service.py              ⭐ UPDATE
│   ├── upload_files()                        ⭐ NEW
│   └── check_duplicate()                     ⭐ UPDATE
│
└── gdrive_service.py                         ⭐ UPDATE
    └── upload_file()                         ⭐ Fix path spacing
```

---

## 📝 CHI TIẾT IMPLEMENTATION

### PHASE 1: AI Analysis Infrastructure

#### File 1: `/app/backend/app/utils/audit_certificate_ai.py`

**Source**: Port from Backend V1 + Audit Report pattern

**Chức năng chính**:
```python
"""
Audit Certificate AI Extraction Utilities
Handles AI-powered field extraction from audit certificates (ISM/ISPS/MLC)
Based on Backend V1 analyze_document_with_ai and Audit Report AI pattern
"""

async def extract_audit_certificate_fields_from_summary(
    summary_text: str,
    filename: str,
    ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract audit certificate fields from Document AI summary using System AI
    
    Based on:
    - Backend V1: analyze_document_with_ai() lines 16143-16400
    - Audit Report: extract_audit_report_fields_from_summary()
    
    Fields to extract:
    - cert_name: Certificate name (REQUIRED)
    - cert_abbreviation: Abbreviation
    - cert_no: Certificate number (REQUIRED)
    - cert_type: Full Term, Interim, Provisional, etc.
    - issue_date: Issue date (YYYY-MM-DD)
    - valid_date: Expiry date (YYYY-MM-DD)
    - last_endorse: Last endorsement date
    - next_survey: Next survey date
    - next_survey_type: Initial, Intermediate, Renewal
    - issued_by: Organization that issued certificate
    - issued_by_abbreviation: Organization abbreviation
    - ship_name: Ship name
    - imo_number: IMO number (7 digits)
    - confidence_score: AI confidence
    
    Returns:
        dict: Extracted fields with post-processing applied
    """
    # 1. Get AI config
    # 2. Create extraction prompt
    # 3. Call System AI (Emergent LLM / Gemini)
    # 4. Parse JSON response
    # 5. Post-process extracted data
    # 6. Return result

def create_audit_certificate_extraction_prompt(
    summary_text: str,
    filename: str = ""
) -> str:
    """
    Create structured prompt for audit certificate field extraction
    
    Based on Backend V1 prompt pattern
    
    CRITICAL INSTRUCTIONS:
    - cert_name and cert_no are REQUIRED fields
    - cert_type must be one of: Full Term, Interim, Provisional, Short term, Conditional, Other
    - Dates in YYYY-MM-DD format
    - IMO number: 7 digits only
    - Issued by: Full organization name
    
    CATEGORY VALIDATION:
    - MUST be ISM, ISPS, or MLC certificate
    - Check cert_name for these keywords
    - Reject if not in these categories
    
    Returns:
        str: Formatted prompt for System AI
    """
    # Create detailed prompt with examples

def _post_process_extracted_data(
    extracted_data: Dict[str, Any],
    filename: str
) -> Dict[str, Any]:
    """
    Post-process extracted data
    
    Logic:
    1. Validate and normalize dates
    2. Validate cert_type (must be valid option)
    3. Normalize issued_by abbreviations
    4. Validate IMO number format
    5. Check category (ISM/ISPS/MLC)
    
    Returns:
        dict: Post-processed data
    """
    # Apply normalization rules
```

**Tham khảo**:
- `/app/backend-v1/server.py` lines 16143-16400 (analyze_document_with_ai)
- `/app/backend/app/utils/audit_report_ai.py` (pattern reference)

---

#### File 2: `/app/backend/app/services/audit_certificate_analyze_service.py`

**Source**: Pattern from `audit_report_analyze_service.py`

**Chức năng chính**:
```python
"""
Audit Certificate Analysis Service
Handles AI-powered analysis of audit certificate files (ISM/ISPS/MLC)
Based on Audit Report Analyze Service pattern
"""

class AuditCertificateAnalyzeService:
    """Service for analyzing audit certificate files with AI"""
    
    @staticmethod
    async def analyze_file(
        file_content: str,  # base64 encoded
        filename: str,
        content_type: str,
        ship_id: str,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        Analyze audit certificate file using Document AI + System AI
        
        Process (identical to Audit Report):
        1. Decode base64 file content
        2. Validate file (PDF/JPG/PNG, max 50MB, magic bytes)
        3. Check page count and split if >15 pages
        4. Process with Document AI (parallel for chunks)
        5. Extract fields from summary with System AI
        6. Normalize issued_by
        7. Validate ship name/IMO
        8. Check for duplicates
        9. Check category (ISM/ISPS/MLC)
        10. Return analysis + validation warnings
        
        Based on: audit_report_analyze_service.py
        
        Returns:
            dict: {
                "success": true,
                "extracted_info": {
                    "cert_name": str,
                    "cert_abbreviation": str,
                    "cert_no": str,
                    "cert_type": str,
                    "issue_date": str,
                    "valid_date": str,
                    "last_endorse": str,
                    "next_survey": str,
                    "next_survey_type": str,
                    "issued_by": str,
                    "issued_by_abbreviation": str,
                    "ship_name": str,
                    "imo_number": str,
                    "confidence_score": float
                },
                "validation_warning": {
                    "type": "imo_mismatch" | "ship_name_mismatch",
                    "message": str,
                    "override_note": str
                } | null,
                "duplicate_warning": {
                    "type": "duplicate",
                    "message": str,
                    "existing_certificate": {...}
                } | null,
                "category_warning": {
                    "type": "category_mismatch",
                    "message": str,
                    "cert_name": str
                } | null
            }
        """
        # Similar structure to audit_report_analyze_service.py
        
    @staticmethod
    async def _process_small_file(...):
        """Process file ≤15 pages"""
        # Call Document AI once
        # Extract fields with System AI
        # Return result
        
    @staticmethod
    async def _process_large_file(...):
        """Process file >15 pages with splitting"""
        # Split PDF into chunks
        # Process chunks in parallel
        # Merge summaries
        # Extract fields
        # Return result
        
    @staticmethod
    async def validate_ship_info(
        extracted_imo: str,
        extracted_ship_name: str,
        current_ship: dict
    ) -> Dict[str, Any]:
        """
        Validate extracted ship info against current ship
        
        Rules (from Backend V1):
        - IMO mismatch → HARD REJECT (return error)
        - Ship name mismatch → SOFT WARNING (return warning with note)
        
        Returns:
            dict: {
                "valid": bool,
                "warning": dict | null,
                "error": dict | null,
                "override_note": str | null
            }
        """
        # Implement validation logic from Backend V1 lines 27245-27305
        
    @staticmethod
    def check_extraction_quality(
        extracted_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if AI extraction is sufficient for automatic processing
        
        Based on Backend V1: check_ai_extraction_quality() lines 27053-27148
        
        Quality criteria:
        - Critical fields: cert_name, cert_no (MUST have both)
        - Confidence score >= 0.4
        - Overall extraction rate >= 0.3
        - Text quality >= 100 characters
        
        Returns:
            dict: {
                "sufficient": bool,
                "confidence_score": float,
                "critical_extraction_rate": float,
                "overall_extraction_rate": float,
                "text_quality_sufficient": bool,
                "missing_fields": list
            }
        """
        # Port logic from Backend V1
        
    @staticmethod
    async def check_category_ism_isps_mlc(
        cert_name: str
    ) -> Dict[str, Any]:
        """
        Check if certificate belongs to ISM/ISPS/MLC categories
        
        Based on Backend V1: check_ism_isps_mlc_category()
        
        Rules:
        - cert_name must contain: "ISM", "ISPS", or "MLC"
        - Case-insensitive search
        - If not found → Return error
        
        Returns:
            dict: {
                "is_valid": bool,
                "category": "ISM" | "ISPS" | "MLC" | null,
                "message": str
            }
        """
        # Check cert_name for ISM/ISPS/MLC keywords
```

**Tham khảo**:
- `/app/backend/app/services/audit_report_analyze_service.py` (main pattern)
- `/app/backend-v1/server.py` lines 27053-27305 (validation logic)

---

### PHASE 2: API Endpoints

#### File 3: `/app/backend/app/api/v1/audit_certificates.py` (UPDATE)

**Thêm 3 endpoints mới**:

```python
# ========== NEW ENDPOINT 1: Analyze File ==========

@router.post("/analyze-file")
async def analyze_audit_certificate_file(
    file_content: str = Form(...),
    filename: str = Form(...),
    content_type: str = Form(...),
    ship_id: str = Form(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze audit certificate file using AI (Editor+ role required)
    
    Process:
    1. Validate file input (base64, filename, content_type)
    2. Call AuditCertificateAnalyzeService.analyze_file()
    3. Return extracted_info + warnings
    
    Used by: Single file upload (analyze only, no DB create)
    
    Request Body:
        file_content: base64 encoded file
        filename: original filename
        content_type: MIME type
        ship_id: ship ID for validation
    
    Returns:
        {
            "success": true,
            "extracted_info": {...},
            "validation_warning": {...} | null,
            "duplicate_warning": {...} | null,
            "category_warning": {...} | null
        }
    """
    try:
        # Validate inputs
        if not filename or not file_content:
            raise HTTPException(status_code=400, detail="Missing filename or file content")
        
        # Call analyze service
        result = await AuditCertificateAnalyzeService.analyze_file(
            file_content=file_content,
            filename=filename,
            content_type=content_type,
            ship_id=ship_id,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing audit certificate file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== NEW ENDPOINT 2: Multi Upload ==========

@router.post("/multi-upload")
async def multi_upload_audit_certificates(
    ship_id: str = Query(...),
    files: List[UploadFile] = File(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload multiple audit certificate files with AI analysis and auto-create
    
    Based on Backend V1: multi_audit_cert_upload_for_ship() lines 26961-27462
    
    Process for each file:
    1. Read file content
    2. Validate file (size, type)
    3. Analyze with AI
    4. Check extraction quality
    5. Validate category (ISM/ISPS/MLC)
    6. Validate ship IMO/name
    7. Check for duplicates
    8. Upload to Google Drive: {ShipName}/ISM - ISPS - MLC/Audit Certificates/
    9. Create DB record
    10. Return result
    
    Request:
        ship_id: query param
        files: multipart/form-data array
    
    Returns:
        {
            "success": true,
            "message": "...",
            "results": [
                {
                    "filename": "...",
                    "status": "success" | "error" | "requires_manual_input" | "pending_duplicate_resolution",
                    "message": "...",
                    "extracted_info": {...},
                    "cert_id": "..." | null
                }
            ],
            "summary": {
                "total_files": 3,
                "successfully_created": 2,
                "errors": 1,
                "certificates_created": [...]
            }
        }
    """
    try:
        # Verify ship exists
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Verify company access
        company_id = current_user.company
        if ship.get("company") != company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        results = []
        summary = {
            "total_files": len(files),
            "successfully_created": 0,
            "errors": 0,
            "certificates_created": [],
            "error_files": []
        }
        
        # Get AI configuration
        ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
        if not ai_config_doc:
            raise HTTPException(status_code=500, detail="AI configuration not found")
        
        # Process each file
        for file in files:
            try:
                # Read file
                file_content = await file.read()
                
                # Validate size (50MB max)
                if len(file_content) > 50 * 1024 * 1024:
                    summary["errors"] += 1
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": "File size exceeds 50MB limit"
                    })
                    continue
                
                # Validate file type (PDF, JPG, PNG)
                supported_extensions = ['pdf', 'jpg', 'jpeg', 'png']
                file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
                if file_ext not in supported_extensions:
                    summary["errors"] += 1
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": "Unsupported file type. Supported: PDF, JPG, PNG"
                    })
                    continue
                
                # Convert to base64
                file_base64 = base64.b64encode(file_content).decode('utf-8')
                
                # Analyze with AI
                analysis_result = await AuditCertificateAnalyzeService.analyze_file(
                    file_content=file_base64,
                    filename=file.filename,
                    content_type=file.content_type,
                    ship_id=ship_id,
                    current_user=current_user
                )
                
                # Check if analysis successful
                if not analysis_result.get("success"):
                    summary["errors"] += 1
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": analysis_result.get("message", "Analysis failed")
                    })
                    continue
                
                extracted_info = analysis_result.get("extracted_info", {})
                
                # Check extraction quality
                quality_check = AuditCertificateAnalyzeService.check_extraction_quality(extracted_info)
                
                if not quality_check.get("sufficient"):
                    # Insufficient extraction → Request manual input
                    missing_fields = quality_check.get("missing_fields", [])
                    summary["errors"] += 1
                    results.append({
                        "filename": file.filename,
                        "status": "requires_manual_input",
                        "message": f"AI không thể trích xuất đủ thông tin. Thiếu: {', '.join(missing_fields)}",
                        "extracted_info": extracted_info,
                        "extraction_quality": quality_check
                    })
                    continue
                
                # Check category (ISM/ISPS/MLC)
                cert_name = extracted_info.get("cert_name", "")
                category_check = await AuditCertificateAnalyzeService.check_category_ism_isps_mlc(cert_name)
                
                if not category_check.get("is_valid"):
                    # Wrong category → Reject
                    summary["errors"] += 1
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": f"Giấy chứng nhận '{cert_name}' không thuộc danh mục ISM/ISPS/MLC",
                        "category_mismatch": True
                    })
                    continue
                
                # Check for validation warnings
                validation_warning = analysis_result.get("validation_warning")
                duplicate_warning = analysis_result.get("duplicate_warning")
                
                if validation_warning and validation_warning.get("type") == "imo_mismatch":
                    # IMO mismatch → Hard reject
                    summary["errors"] += 1
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": "Giấy chứng nhận của tàu khác, không thể lưu vào dữ liệu tàu hiện tại",
                        "validation_error": validation_warning
                    })
                    continue
                
                if duplicate_warning:
                    # Duplicate detected → Request user choice
                    results.append({
                        "filename": file.filename,
                        "status": "pending_duplicate_resolution",
                        "message": duplicate_warning.get("message"),
                        "duplicate_info": duplicate_warning
                    })
                    continue
                
                # All checks passed → Upload to GDrive and create DB record
                
                # Upload to Google Drive
                from app.services.gdrive_service import GDriveService
                
                # ⭐ NEW PATH WITH SPACES: "ISM - ISPS - MLC"
                upload_result = await GDriveService.upload_file(
                    file_content=file_content,
                    filename=file.filename,
                    content_type=file.content_type,
                    folder_path=f"{ship.get('name')}/ISM - ISPS - MLC/Audit Certificates",
                    company_id=company_id
                )
                
                if not upload_result.get("success"):
                    summary["errors"] += 1
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": upload_result.get("message", "Failed to upload to Google Drive")
                    })
                    continue
                
                # Create DB record
                validation_note = None
                if validation_warning and validation_warning.get("type") == "ship_name_mismatch":
                    validation_note = validation_warning.get("override_note", "Chỉ để tham khảo")
                
                cert_data = {
                    "id": str(uuid.uuid4()),
                    "ship_id": ship_id,
                    "ship_name": ship.get("name"),
                    "cert_name": extracted_info.get("cert_name"),
                    "cert_abbreviation": extracted_info.get("cert_abbreviation", ""),
                    "cert_no": extracted_info.get("cert_no"),
                    "cert_type": extracted_info.get("cert_type", "Full Term"),
                    "issue_date": extracted_info.get("issue_date"),
                    "valid_date": extracted_info.get("valid_date"),
                    "last_endorse": extracted_info.get("last_endorse"),
                    "next_survey": extracted_info.get("next_survey"),
                    "next_survey_type": extracted_info.get("next_survey_type"),
                    "issued_by": extracted_info.get("issued_by", ""),
                    "issued_by_abbreviation": extracted_info.get("issued_by_abbreviation", ""),
                    "notes": validation_note if validation_note else "",
                    "google_drive_file_id": upload_result.get("file_id"),
                    "file_name": file.filename,
                    "created_at": datetime.now(timezone.utc),
                    "company": company_id
                }
                
                # Create in database
                await mongo_db.create("audit_certificates", cert_data)
                
                summary["successfully_created"] += 1
                summary["certificates_created"].append({
                    "id": cert_data["id"],
                    "cert_name": cert_data["cert_name"],
                    "filename": file.filename
                })
                
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "message": "Certificate uploaded and created successfully",
                    "extracted_info": extracted_info,
                    "cert_id": cert_data["id"]
                })
                
                logger.info(f"✅ Created audit certificate from file: {file.filename}")
                
            except Exception as file_error:
                logger.error(f"❌ Error processing file {file.filename}: {file_error}")
                summary["errors"] += 1
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": str(file_error)
                })
        
        logger.info(f"🎉 Multi-upload complete: {summary['successfully_created']} success, {summary['errors']} errors")
        
        return {
            "success": True,
            "message": f"Processed {len(files)} files: {summary['successfully_created']} success, {summary['errors']} errors",
            "results": results,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-upload for audit certificates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== NEW ENDPOINT 3: Create with File Override ==========

@router.post("/create-with-file-override")
async def create_audit_certificate_with_file_override(
    ship_id: str = Query(...),
    file: UploadFile = File(...),
    cert_data: str = Form(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Create audit certificate with file, bypassing validation
    Used when user approves validation warning (IMO/ship name mismatch)
    
    Process:
    1. Parse cert_data JSON
    2. Upload file to Google Drive
    3. Create DB record (with validation note)
    
    Request:
        ship_id: query param
        file: uploaded file
        cert_data: JSON string with certificate data
    
    Returns:
        {
            "success": true,
            "message": "...",
            "cert_id": "..."
        }
    """
    try:
        # Verify ship
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Verify access
        company_id = current_user.company
        if ship.get("company") != company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Parse cert_data
        try:
            cert_payload = json.loads(cert_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid cert_data JSON")
        
        # Read file
        file_content = await file.read()
        
        # Upload to Google Drive
        from app.services.gdrive_service import GDriveService
        
        # ⭐ NEW PATH WITH SPACES: "ISM - ISPS - MLC"
        upload_result = await GDriveService.upload_file(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type,
            folder_path=f"{ship.get('name')}/ISM - ISPS - MLC/Audit Certificates",
            company_id=company_id
        )
        
        if not upload_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=upload_result.get("message", "Failed to upload file")
            )
        
        # Create DB record
        cert_record = {
            "id": str(uuid.uuid4()),
            "ship_id": ship_id,
            "ship_name": ship.get("name"),
            **cert_payload,
            "google_drive_file_id": upload_result.get("file_id"),
            "file_name": file.filename,
            "created_at": datetime.now(timezone.utc),
            "company": company_id
        }
        
        await mongo_db.create("audit_certificates", cert_record)
        
        logger.info(f"✅ Created audit certificate with file override: {cert_record['id']}")
        
        return {
            "success": True,
            "message": "Certificate created successfully with file override",
            "cert_id": cert_record["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating certificate with file override: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### PHASE 3: Google Drive Path Fix

#### File 4: `/app/backend/app/services/gdrive_service.py` (UPDATE)

**⭐ SỬA PATH: `ISM-ISPS-MLC` → `ISM - ISPS - MLC`**

```python
# Location: upload_file() method

# OLD PATH (No spaces):
# folder_path = f"{ship_name}/ISM-ISPS-MLC/Audit Certificates"

# ⭐ NEW PATH (With spaces):
# folder_path = f"{ship_name}/ISM - ISPS - MLC/Audit Certificates"

# Notes:
# - This change affects all audit certificate uploads
# - Google Drive handles spaces in folder names correctly
# - Apps Script will auto-create folders with correct names
# - Existing files in old path are NOT affected (migration not needed)
```

**Kiểm tra các nơi sử dụng path**:
```bash
# Tìm tất cả nơi sử dụng "ISM-ISPS-MLC" hoặc "ISM - ISPS - MLC"
grep -r "ISM-ISPS-MLC\|ISM - ISPS - MLC" /app/backend/app/ --include="*.py"
```

---

### PHASE 4: Service Layer Updates

#### File 5: `/app/backend/app/services/audit_certificate_service.py` (UPDATE)

**Thêm method mới**:

```python
@staticmethod
async def check_duplicate(
    ship_id: str,
    cert_name: str,
    cert_no: Optional[str],
    current_user: UserResponse
) -> dict:
    """
    Check if audit certificate is duplicate
    
    Enhanced from current implementation:
    - Match by cert_name + cert_no
    - Calculate similarity score
    - Return existing certificate details
    
    Based on Backend V1: check_audit_certificate_duplicates()
    
    Returns:
        {
            "is_duplicate": bool,
            "existing_id": str | null,
            "existing_certificate": dict | null,
            "similarity": float
        }
    """
    filters = {
        "ship_id": ship_id,
        "cert_name": cert_name
    }
    
    if cert_no:
        filters["cert_no"] = cert_no
    
    existing = await mongo_db.find_one(
        AuditCertificateService.collection_name,
        filters
    )
    
    if existing:
        # Calculate similarity (basic: 100% if both name and no match)
        similarity = 1.0 if cert_no and filters.get("cert_no") else 0.8
        
        return {
            "is_duplicate": True,
            "existing_id": existing.get("id"),
            "existing_certificate": {
                "cert_name": existing.get("cert_name"),
                "cert_no": existing.get("cert_no"),
                "cert_type": existing.get("cert_type"),
                "issue_date": existing.get("issue_date"),
                "valid_date": existing.get("valid_date"),
                "issued_by": existing.get("issued_by"),
                "created_at": existing.get("created_at")
            },
            "similarity": similarity
        }
    
    return {
        "is_duplicate": False,
        "existing_id": None,
        "existing_certificate": None,
        "similarity": 0.0
    }
```

---

## 🔄 MIGRATION STEPS

### Step 1: Tạo Utilities (Day 1 - 2 hours)
```bash
# Create: audit_certificate_ai.py
✅ extract_audit_certificate_fields_from_summary()
✅ create_audit_certificate_extraction_prompt()
✅ _post_process_extracted_data()

# Reference:
- /app/backend/app/utils/audit_report_ai.py
- /app/backend-v1/server.py lines 16143-16400
```

### Step 2: Tạo Analyze Service (Day 1-2 - 4 hours)
```bash
# Create: audit_certificate_analyze_service.py
✅ AuditCertificateAnalyzeService.analyze_file()
✅ _process_small_file()
✅ _process_large_file()
✅ validate_ship_info()
✅ check_extraction_quality()
✅ check_category_ism_isps_mlc()

# Reference:
- /app/backend/app/services/audit_report_analyze_service.py
- /app/backend-v1/server.py lines 27053-27305
```

### Step 3: Thêm API Endpoints (Day 2 - 3 hours)
```bash
# Update: audit_certificates.py
✅ POST /analyze-file
✅ POST /multi-upload
✅ POST /create-with-file-override

# Reference:
- /app/backend/app/api/v1/audit_reports.py (analyze-file pattern)
- /app/backend-v1/server.py lines 26961-27462 (multi-upload logic)
```

### Step 4: Update Services (Day 2 - 1 hour)
```bash
# Update: audit_certificate_service.py
✅ Enhanced check_duplicate() method

# Update: gdrive_service.py
✅ Fix path: "ISM - ISPS - MLC" (with spaces)
```

### Step 5: Testing (Day 3 - 4 hours)
```bash
✅ Unit tests
✅ Integration tests
✅ Manual testing với Postman
✅ Frontend testing
```

---

## 🧪 TESTING PLAN

### Unit Tests

**File**: `/app/backend/tests/test_audit_certificate_analyze.py`

```python
import pytest
from app.services.audit_certificate_analyze_service import AuditCertificateAnalyzeService

class TestAuditCertificateAnalyze:
    
    @pytest.mark.asyncio
    async def test_analyze_file_pdf_success(self):
        """Test successful PDF analysis"""
        # Mock file content (base64)
        # Mock AI response
        # Assert extracted fields
        
    @pytest.mark.asyncio
    async def test_analyze_file_invalid_type(self):
        """Test rejection of invalid file type"""
        # Assert HTTPException raised
        
    @pytest.mark.asyncio
    async def test_check_extraction_quality_sufficient(self):
        """Test quality check passes"""
        # Mock extracted_info with all required fields
        # Assert sufficient = True
        
    @pytest.mark.asyncio
    async def test_check_extraction_quality_insufficient(self):
        """Test quality check fails"""
        # Mock extracted_info missing critical fields
        # Assert sufficient = False
        
    @pytest.mark.asyncio
    async def test_validate_ship_imo_mismatch(self):
        """Test IMO mismatch validation"""
        # Assert returns error
        
    @pytest.mark.asyncio
    async def test_validate_ship_name_mismatch(self):
        """Test ship name mismatch validation"""
        # Assert returns warning (not error)
        
    @pytest.mark.asyncio
    async def test_check_category_valid(self):
        """Test ISM/ISPS/MLC category validation"""
        # Test with "ISM Code Certificate"
        # Assert is_valid = True
        
    @pytest.mark.asyncio
    async def test_check_category_invalid(self):
        """Test non-ISM/ISPS/MLC rejection"""
        # Test with "SOLAS Certificate"
        # Assert is_valid = False
```

### Integration Tests

**File**: `/app/backend/tests/test_audit_certificate_api.py`

```python
import pytest
from httpx import AsyncClient

class TestAuditCertificateAPI:
    
    @pytest.mark.asyncio
    async def test_analyze_file_endpoint(self, client: AsyncClient, auth_headers):
        """Test POST /api/audit-certificates/analyze-file"""
        # Prepare test file (base64)
        # Send request
        # Assert response structure
        
    @pytest.mark.asyncio
    async def test_multi_upload_endpoint(self, client: AsyncClient, auth_headers):
        """Test POST /api/audit-certificates/multi-upload"""
        # Prepare 3 test files
        # Send request
        # Assert summary: 3 total, 2 success, 1 error
        
    @pytest.mark.asyncio
    async def test_create_with_override_endpoint(self, client: AsyncClient, auth_headers):
        """Test POST /api/audit-certificates/create-with-file-override"""
        # Prepare file + cert_data
        # Send request
        # Assert certificate created
        # Assert file uploaded to GDrive
```

### Manual Testing Checklist

```
⬜ Single File Upload - PDF
   ⬜ Upload valid ISM certificate PDF
   ⬜ Check extracted fields auto-fill form
   ⬜ Verify dates format correctly
   ⬜ Save and check DB record

⬜ Single File Upload - Image
   ⬜ Upload JPG certificate
   ⬜ Check OCR extraction works
   ⬜ Verify confidence score

⬜ Multi File Upload - 3 files
   ⬜ Upload 3 PDFs simultaneously
   ⬜ Check staggered upload (2s delay)
   ⬜ Verify all progress bars update
   ⬜ Check 3 records created in DB
   ⬜ Verify Google Drive path: {Ship}/ISM - ISPS - MLC/Audit Certificates/

⬜ Validation - IMO Mismatch
   ⬜ Upload cert with wrong IMO
   ⬜ Check hard reject (status: error)
   ⬜ Verify error message

⬜ Validation - Ship Name Mismatch
   ⬜ Upload cert with different ship name
   ⬜ Check soft warning (status: warning)
   ⬜ Verify note added: "Chỉ để tham khảo"

⬜ Validation - Category Check
   ⬜ Upload non-ISM/ISPS/MLC certificate
   ⬜ Check rejection (status: error)
   ⬜ Verify category mismatch message

⬜ Validation - Duplicate Detection
   ⬜ Upload same certificate twice
   ⬜ Check duplicate modal appears
   ⬜ Verify existing certificate details shown

⬜ Quality Check - Insufficient Extraction
   ⬜ Upload poor quality/corrupted file
   ⬜ Check status: requires_manual_input
   ⬜ Verify missing fields listed

⬜ File Override Flow
   ⬜ Click "Continue" on validation warning
   ⬜ Form auto-fills with override note
   ⬜ Save successfully
   ⬜ Check DB record has validation note

⬜ Google Drive Path
   ⬜ Check folder created: "ISM - ISPS - MLC" (with spaces)
   ⬜ Verify file uploaded to correct path
   ⬜ Check file_id stored in DB

⬜ Error Handling
   ⬜ Test file > 50MB (reject)
   ⬜ Test unsupported file type (reject)
   ⬜ Test network error during upload
   ⬜ Test AI service unavailable
```

---

## 📊 ROLLOUT PLAN

### Phase 1: Development (Days 1-2)
- ✅ Create utility files
- ✅ Create analyze service
- ✅ Add API endpoints
- ✅ Update existing services

### Phase 2: Testing (Day 3)
- ✅ Unit tests
- ✅ Integration tests
- ✅ Manual testing with Postman

### Phase 3: Staging Deployment (Day 4)
- ✅ Deploy to staging environment
- ✅ Frontend team integration testing
- ✅ End-to-end testing

### Phase 4: Production Deployment (Day 5)
- ✅ Deploy to production
- ✅ Monitor logs
- ✅ User acceptance testing

### Phase 5: Cleanup (Day 6)
- ✅ Remove Backend V1 dependencies (if safe)
- ✅ Update documentation
- ✅ Performance optimization

---

## ⚠️ RISK MITIGATION

### Risk 1: Google Drive Path Change
**Issue**: Thay đổi path từ `ISM-ISPS-MLC` → `ISM - ISPS - MLC`

**Impact**: 
- Files cũ vẫn ở path cũ
- Files mới ở path mới
- Không có conflict (2 folders khác nhau)

**Solution**:
- ✅ Không cần migrate files cũ
- ✅ Frontend hiển thị cả 2 paths
- ✅ Document path change trong release notes

### Risk 2: AI Service Downtime
**Issue**: Google Document AI hoặc Emergent LLM không khả dụng

**Mitigation**:
- ✅ Graceful fallback: Show manual input form
- ✅ Retry logic với exponential backoff
- ✅ Clear error messages cho user

### Risk 3: Large File Processing
**Issue**: File >15 pages chậm, timeout

**Mitigation**:
- ✅ Implement PDF splitting (đã có trong audit_report)
- ✅ Parallel processing cho chunks
- ✅ Progress updates cho user

### Risk 4: Duplicate Detection False Positives
**Issue**: Có thể detect duplicate nhầm

**Mitigation**:
- ✅ Show duplicate modal (cho user quyết định)
- ✅ Display both certificates side-by-side
- ✅ Allow force override

---

## 📈 SUCCESS METRICS

### Performance Targets:
- ⏱️ Single file analysis: < 10 seconds
- ⏱️ Multi-upload (3 files): < 30 seconds
- ⏱️ API response time: < 2 seconds (excluding AI processing)
- 📊 AI extraction accuracy: > 90%
- 🎯 Duplicate detection accuracy: > 95%

### Quality Metrics:
- 🐛 Zero critical bugs in production
- ✅ 100% test coverage for core logic
- 📝 Full API documentation
- 👥 User satisfaction: Positive feedback

---

## 📚 DOCUMENTATION UPDATES

### API Documentation (Swagger/OpenAPI):
```yaml
/api/audit-certificates/analyze-file:
  post:
    summary: Analyze audit certificate file with AI
    tags: [Audit Certificates]
    security: [BearerAuth]
    requestBody:
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              file_content:
                type: string
                format: base64
              filename:
                type: string
              content_type:
                type: string
              ship_id:
                type: string
    responses:
      200:
        description: Analysis result
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                extracted_info:
                  type: object
                validation_warning:
                  type: object
                duplicate_warning:
                  type: object
                category_warning:
                  type: object
```

### Developer Guide:
```markdown
# Audit Certificate Upload - Developer Guide

## Overview
The Audit Certificate module handles upload and AI analysis of ISM/ISPS/MLC certificates.

## Architecture
- **Frontend**: AddAuditCertificateModal.jsx
- **Backend API**: /api/audit-certificates/*
- **Services**: AuditCertificateAnalyzeService
- **Storage**: MongoDB + Google Drive

## Upload Flow
1. User selects file(s)
2. Frontend uploads to backend
3. Backend analyzes with AI
4. Validates ship info, category, duplicates
5. Uploads to GDrive
6. Creates DB record

## Google Drive Path
Files are stored at:
```
{ShipName}/ISM - ISPS - MLC/Audit Certificates/{filename}
```

## Validation Rules
- **IMO Mismatch**: Hard reject
- **Ship Name Mismatch**: Soft warning (add note)
- **Category Check**: Only ISM/ISPS/MLC allowed
- **Duplicate Check**: Show modal for user choice

## Error Handling
- File size > 50MB: Reject
- Unsupported type: Reject
- Low AI confidence: Request manual input
- Network error: Show retry option
```

---

## 🎯 DELIVERABLES

### Code Files:
1. ✅ `/app/backend/app/utils/audit_certificate_ai.py` (NEW)
2. ✅ `/app/backend/app/services/audit_certificate_analyze_service.py` (NEW)
3. ✅ `/app/backend/app/api/v1/audit_certificates.py` (UPDATE)
4. ✅ `/app/backend/app/services/audit_certificate_service.py` (UPDATE)
5. ✅ `/app/backend/app/services/gdrive_service.py` (UPDATE - Path fix)

### Test Files:
1. ✅ `/app/backend/tests/test_audit_certificate_analyze.py` (NEW)
2. ✅ `/app/backend/tests/test_audit_certificate_api.py` (NEW)

### Documentation:
1. ✅ API Documentation (Swagger)
2. ✅ Developer Guide
3. ✅ Migration Notes
4. ✅ Release Notes

---

## 🚀 NEXT STEPS AFTER MIGRATION

1. **Monitor Production**:
   - Track API response times
   - Monitor AI accuracy
   - Watch error rates

2. **Gather Feedback**:
   - User feedback on UI/UX
   - Error messages clarity
   - Performance satisfaction

3. **Optimize**:
   - Reduce AI processing time
   - Improve duplicate detection
   - Enhance error recovery

4. **Iterate**:
   - Add more validation rules
   - Support more file types
   - Improve AI prompts

---

## 📞 SUPPORT

### Issues & Questions:
- Technical Issues: Check logs in `/var/log/supervisor/backend.*.log`
- AI Issues: Verify AI config in MongoDB `ai_config` collection
- GDrive Issues: Check company GDrive config

### Escalation:
- P0 (Critical): Production down → Rollback immediately
- P1 (High): Feature broken → Hotfix within 24h
- P2 (Medium): Minor bug → Fix in next release
- P3 (Low): Enhancement → Backlog

---

**Document Version**: 1.0  
**Created**: 2025-01-XX  
**Status**: ✅ Ready for Implementation  
**Estimated Effort**: 5-6 days (1 developer)

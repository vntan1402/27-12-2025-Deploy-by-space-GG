import logging
import base64
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks, Form
from pydantic import BaseModel

from app.models.audit_certificate import AuditCertificateCreate, AuditCertificateUpdate, AuditCertificateResponse, BulkDeleteAuditCertificateRequest
from app.models.user import UserResponse, UserRole
from app.services.audit_certificate_service import AuditCertificateService
from app.core.security import get_current_user
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[AuditCertificateResponse])
async def get_audit_certificates(
    ship_id: Optional[str] = Query(None),
    cert_type: Optional[str] = Query(None),  # Filter by ISM, ISPS, MLC
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Audit Certificates (ISM/ISPS/MLC), optionally filtered by ship_id and cert_type"""
    try:
        return await AuditCertificateService.get_audit_certificates(ship_id, cert_type, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching Audit Certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Audit Certificates")


@router.get("/upcoming-surveys")
async def get_upcoming_audit_surveys(
    days: int = Query(30, description="Number of days to look ahead (legacy parameter, not used with window logic)"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get upcoming audit surveys based on window logic
    
    This endpoint returns all audit certificates that are within their survey window:
    - (±6M): Intermediate surveys without Last Endorse (6 months before/after)
    - (±3M): Other surveys with bidirectional window (3 months before/after)
    - (-3M): Initial and Renewal surveys (3 months before only)
    
    The endpoint checks:
    1. All ships belonging to the user's company
    2. All audit certificates for those ships
    3. Certificates with next_survey_display field populated
    4. Current date falls within the survey window
    
    Returns certificates with status indicators:
    - is_overdue: Past window_close date
    - is_critical: ≤ 30 days to window_close
    - is_due_soon: More than 30 days but within window
    """
    try:
        return await AuditCertificateService.get_upcoming_audit_surveys(current_user, days)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting upcoming audit surveys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cert_id}", response_model=AuditCertificateResponse)
async def get_audit_certificate_by_id(
    cert_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific Audit Certificate by ID"""
    try:
        return await AuditCertificateService.get_audit_certificate_by_id(cert_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Audit Certificate {cert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Audit Certificate")

@router.post("", response_model=AuditCertificateResponse)
async def create_audit_certificate(
    cert_data: AuditCertificateCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Create new Audit Certificate (Editor+ role required)"""
    try:
        return await AuditCertificateService.create_audit_certificate(cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating Audit Certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Audit Certificate")

@router.put("/{cert_id}", response_model=AuditCertificateResponse)
async def update_audit_certificate(
    cert_id: str,
    cert_data: AuditCertificateUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Update Audit Certificate (Editor+ role required)"""
    try:
        return await AuditCertificateService.update_audit_certificate(cert_id, cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating Audit Certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Audit Certificate")

@router.delete("/{cert_id}")
async def delete_audit_certificate(
    cert_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Audit Certificate with background file deletion (Editor+ role required)"""
    try:
        return await AuditCertificateService.delete_audit_certificate(cert_id, current_user, background_tasks)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Audit Certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Audit Certificate")

@router.post("/bulk-delete")
async def bulk_delete_audit_certificates(
    request: BulkDeleteAuditCertificateRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Audit Certificates with background file deletion (Editor+ role required)"""
    try:
        return await AuditCertificateService.bulk_delete_audit_certificates(request, current_user, background_tasks)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Audit Certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Audit Certificates")

@router.post("/check-duplicate")
async def check_duplicate_audit_certificate(
    ship_id: str,
    cert_name: str,
    cert_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if Audit Certificate is duplicate"""
    try:
        return await AuditCertificateService.check_duplicate(ship_id, cert_name, cert_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

class AnalyzeFileRequest(BaseModel):
    file_content: str
    filename: str
    content_type: str
    ship_id: str

@router.post("/analyze-file")
async def analyze_audit_certificate_file(
    request_data: AnalyzeFileRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze audit certificate file using AI (Editor+ role required)
    
    Process:
    1. Receive JSON body with base64 file content
    2. Validate inputs
    3. Call AuditCertificateAnalyzeService.analyze_file()
    4. Return extracted_info + warnings
    
    Used by: Single file upload (analyze only, no DB create)
    
    Request Body (JSON):
        {
            "file_content": "base64_string",
            "filename": "filename.pdf",
            "content_type": "application/pdf",
            "ship_id": "ship_uuid"
        }
    
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
        logger.info(f"📥 Received analyze-file request (JSON body)")
        
        from app.services.audit_certificate_analyze_service import AuditCertificateAnalyzeService
        
        # Extract fields from request
        file_content = request_data.file_content
        filename = request_data.filename
        content_type = request_data.content_type
        ship_id = request_data.ship_id
        
        logger.info(f"ship_id={ship_id}, filename={filename}, content_type={content_type}")
        
        # Validate inputs
        if not file_content:
            logger.error("❌ No file_content provided")
            raise HTTPException(status_code=400, detail="No file_content provided")
        
        if not filename:
            logger.error("❌ No filename provided")
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not ship_id:
            logger.error("❌ No ship_id provided")
            raise HTTPException(status_code=400, detail="No ship_id provided")
        
        # Call analyze service (file_content is already base64)
        result = await AuditCertificateAnalyzeService.analyze_file(
            file_content=file_content,
            filename=filename,
            content_type=content_type or "application/pdf",
            ship_id=ship_id,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing audit certificate file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-upload")
async def multi_upload_audit_certificates(
    ship_id: str = Query(...),
    files: List[UploadFile] = File(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload multiple audit certificate files with AI analysis and auto-create
    
    Based on Backend V1: multi_audit_cert_upload_for_ship() lines 26970-27462
    
    Process for each file:
    1. Read file content
    2. Validate file (size, type)
    3. Analyze with AI
    4. Check extraction quality
    5. Validate category (ISM/ISPS/MLC/CICA)
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
            "results": [...],
            "summary": {...}
        }
    """
    try:
        from app.services.audit_certificate_analyze_service import AuditCertificateAnalyzeService
        from app.services.gdrive_service import GDriveService
        import uuid
        import json
        from datetime import datetime, timezone
        
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
                    summary["error_files"].append({
                        "filename": file.filename,
                        "error": "File size exceeds 50MB limit"
                    })
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
                    summary["error_files"].append({
                        "filename": file.filename,
                        "error": "Unsupported file type"
                    })
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
                    summary["error_files"].append({
                        "filename": file.filename,
                        "error": analysis_result.get("message", "Analysis failed")
                    })
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": analysis_result.get("message", "Analysis failed")
                    })
                    continue
                
                extracted_info = analysis_result.get("extracted_info", {})
                
                # ⭐ REMOVED: Quality check lần 2 (already checked in analyze_file service)
                # Trust the analyze service result - if it returned success, quality is sufficient
                
                # Check category (ISM/ISPS/MLC/CICA)
                category_warning = analysis_result.get("category_warning")
                if category_warning and not category_warning.get("is_valid"):
                    # Wrong category → Reject
                    summary["errors"] += 1
                    summary["error_files"].append({
                        "filename": file.filename,
                        "error": category_warning.get("message")
                    })
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": category_warning.get("message"),
                        "category_mismatch": True
                    })
                    continue
                
                # Check for validation warnings
                validation_warning = analysis_result.get("validation_warning")
                duplicate_warning = analysis_result.get("duplicate_warning")
                
                if validation_warning and validation_warning.get("is_blocking"):
                    # IMO mismatch → Hard reject
                    summary["errors"] += 1
                    summary["error_files"].append({
                        "filename": file.filename,
                        "error": validation_warning.get("message")
                    })
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": validation_warning.get("message"),
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
                    summary["error_files"].append({
                        "filename": file.filename,
                        "error": upload_result.get("message", "Failed to upload to Google Drive")
                    })
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": upload_result.get("message", "Failed to upload to Google Drive")
                    })
                    continue
                
                # Create DB record
                validation_note = None
                if validation_warning and not validation_warning.get("is_blocking"):
                    validation_note = validation_warning.get("override_note", "Chỉ để tham khảo")
                
                cert_data = {
                    "id": str(uuid.uuid4()),
                    "ship_id": ship_id,
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
                    "extracted_ship_name": extracted_info.get("ship_name", ""),  # Ship name extracted by AI
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
                summary["error_files"].append({
                    "filename": file.filename,
                    "error": str(file_error)
                })
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
        from app.services.gdrive_service import GDriveService
        import uuid
        import json
        from datetime import datetime, timezone
        
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
        # ⭐ NEW PATH WITH SPACES: "ISM - ISPS - MLC"
        logger.info(f"📤 Uploading file to GDrive: {file.filename}")
        upload_result = await GDriveService.upload_file(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type,
            folder_path=f"{ship.get('name')}/ISM - ISPS - MLC/Audit Certificates",
            company_id=company_id
        )
        
        logger.info(f"📥 Upload result: {upload_result}")
        
        if not upload_result.get("success"):
            logger.error(f"❌ GDrive upload failed: {upload_result}")
            raise HTTPException(
                status_code=500,
                detail=upload_result.get("message", "Failed to upload file")
            )
        
        file_id = upload_result.get("file_id")
        logger.info(f"✅ GDrive upload success! file_id={file_id}")
        
        # Create DB record
        cert_record = {
            "id": str(uuid.uuid4()),
            "ship_id": ship_id,
            "ship_name": ship.get("name"),
            **cert_payload,
            "google_drive_file_id": file_id,
            "file_name": file.filename,
            "created_at": datetime.now(timezone.utc),
            "company": company_id
        }
        
        logger.info(f"💾 Creating DB record with file_id={file_id}")
        
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

        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing audit certificate file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ships/{ship_id}/audit-certificates/update-next-survey")
async def update_ship_audit_certificates_next_survey(
    ship_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Calculate and update Next Survey for all audit certificates of a ship
    
    This endpoint implements the Next Survey calculation logic:
    - Interim certificates: Next Survey = Valid Date - 3M (Initial)
    - Short Term certificates: No Next Survey
    - Full Term with Last Endorse: Next Survey = Valid Date - 3M (Renewal)
    - Full Term without Last Endorse: Next Survey = Valid Date - 30 months, Window ±6M (Intermediate)
    - Special documents (DMLC I/II, SSP): No Next Survey
    """
    try:
        return await AuditCertificateService.update_ship_audit_certificates_next_survey(ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating audit certificates next survey for ship {ship_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@router.post("/{cert_id}/auto-rename-file")
async def auto_rename_audit_certificate_file(
    cert_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Auto-rename audit certificate file on Google Drive
    
    New filename pattern:
    {Shipname}_{CertType}_{CertAbbreviation}_{IssueDate_DDMMYYYY}.{ext}
    
    Example: VINASHIP_FullTerm_ISM-DOC_07052024.pdf
    
    Process:
    1. Get certificate from DB
    2. Validate has google_drive_file_id
    3. Get ship name (from extracted_ship_name or ship DB)
    4. Generate new filename with pattern
    5. Call Apps Script to rename file on Google Drive
    6. Update DB with new filename
    
    Requires:
    - Editor+ permission
    - Certificate must have google_drive_file_id
    - Company must have Apps Script URL configured
    
    Returns:
    {
      "success": true,
      "message": "File renamed successfully",
      "old_name": "original.pdf",
      "new_name": "VINASHIP_FullTerm_ISM-DOC_07052024.pdf",
      "file_id": "1ABC..."
    }
    """
    try:
        return await AuditCertificateService.auto_rename_file(cert_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error auto-renaming audit certificate file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


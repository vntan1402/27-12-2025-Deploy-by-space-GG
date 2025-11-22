import logging
import base64
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks, Form

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
    
    Request Body (Form Data):
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
        from app.services.audit_certificate_analyze_service import AuditCertificateAnalyzeService
        
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

        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing audit certificate file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

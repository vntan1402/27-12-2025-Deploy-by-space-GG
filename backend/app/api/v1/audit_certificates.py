import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks

from app.models.audit_certificate import AuditCertificateCreate, AuditCertificateUpdate, AuditCertificateResponse, BulkDeleteAuditCertificateRequest
from app.models.user import UserResponse, UserRole
from app.services.audit_certificate_service import AuditCertificateService
from app.core.security import get_current_user

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

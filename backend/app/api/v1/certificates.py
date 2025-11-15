import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query

from app.models.certificate import (
    CertificateCreate, 
    CertificateUpdate, 
    CertificateResponse,
    BulkDeleteRequest
)
from app.models.user import UserResponse, UserRole
from app.services.certificate_service import CertificateService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[CertificateResponse])
async def get_certificates(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get certificates, optionally filtered by ship_id
    """
    try:
        return await CertificateService.get_certificates(ship_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch certificates")

@router.get("/{cert_id}", response_model=CertificateResponse)
async def get_certificate_by_id(
    cert_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific certificate by ID
    """
    try:
        return await CertificateService.get_certificate_by_id(cert_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching certificate {cert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch certificate")

@router.post("", response_model=CertificateResponse)
async def create_certificate(
    cert_data: CertificateCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Create new certificate (Editor+ role required)
    """
    try:
        return await CertificateService.create_certificate(cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to create certificate")

@router.put("/{cert_id}", response_model=CertificateResponse)
async def update_certificate(
    cert_id: str,
    cert_data: CertificateUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Update certificate (Editor+ role required)
    """
    try:
        return await CertificateService.update_certificate(cert_id, cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to update certificate")

@router.delete("/{cert_id}")
async def delete_certificate(
    cert_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Delete certificate (Editor+ role required)
    """
    try:
        return await CertificateService.delete_certificate(cert_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete certificate")

@router.post("/bulk-delete")
async def bulk_delete_certificates(
    request: BulkDeleteRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Bulk delete certificates (Editor+ role required)
    """
    try:
        return await CertificateService.bulk_delete_certificates(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete certificates")

@router.post("/check-duplicate")
async def check_duplicate_certificate(
    ship_id: str,
    cert_name: str,
    cert_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Check if certificate is duplicate
    """
    try:
        return await CertificateService.check_duplicate(ship_id, cert_name, cert_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

@router.post("/analyze-file")
async def analyze_certificate_file(
    file: UploadFile = File(...),
    ship_id: Optional[str] = None,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze certificate file using AI (Editor+ role required)
    """
    try:
        return await CertificateService.analyze_certificate_file(file, ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing certificate file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze certificate: {str(e)}")

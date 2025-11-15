import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query

from app.models.crew_certificate import (
    CrewCertificateCreate,
    CrewCertificateUpdate,
    CrewCertificateResponse,
    BulkDeleteCrewCertificateRequest
)
from app.models.user import UserResponse, UserRole
from app.services.crew_certificate_service import CrewCertificateService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("/all", response_model=List[CrewCertificateResponse])
async def get_all_crew_certificates(
    crew_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get ALL crew certificates for the company (no ship filter)
    Includes both ship-assigned and Standby crew certificates
    """
    try:
        return await CrewCertificateService.get_all_crew_certificates(crew_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching all crew certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch all crew certificates")

@router.get("", response_model=List[CrewCertificateResponse])
async def get_crew_certificates(
    crew_id: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get crew certificates, optionally filtered by crew_id or company_id
    """
    try:
        return await CrewCertificateService.get_crew_certificates(crew_id, company_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching crew certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch crew certificates")

@router.get("/{cert_id}", response_model=CrewCertificateResponse)
async def get_crew_certificate_by_id(
    cert_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific crew certificate by ID
    """
    try:
        return await CrewCertificateService.get_crew_certificate_by_id(cert_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching crew certificate {cert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch crew certificate")

@router.post("", response_model=CrewCertificateResponse)
async def create_crew_certificate(
    cert_data: CrewCertificateCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Create new crew certificate (Editor+ role required)
    """
    try:
        return await CrewCertificateService.create_crew_certificate(cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating crew certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to create crew certificate")

@router.put("/{cert_id}", response_model=CrewCertificateResponse)
async def update_crew_certificate(
    cert_id: str,
    cert_data: CrewCertificateUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Update crew certificate (Editor+ role required)
    """
    try:
        return await CrewCertificateService.update_crew_certificate(cert_id, cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating crew certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to update crew certificate")

@router.delete("/bulk-delete")
async def bulk_delete_crew_certificates(
    request: BulkDeleteCrewCertificateRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Bulk delete crew certificates - MUST be before /{cert_id} route!
    (Editor+ role required)
    """
    try:
        return await CrewCertificateService.bulk_delete_crew_certificates(request, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error bulk deleting crew certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete crew certificates")

@router.delete("/{cert_id}")
async def delete_crew_certificate(
    cert_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Delete crew certificate (Editor+ role required)
    """
    try:
        return await CrewCertificateService.delete_crew_certificate(cert_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting crew certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete crew certificate")

@router.post("/bulk-delete")
async def bulk_delete_crew_certificates(
    request: BulkDeleteCrewCertificateRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Bulk delete crew certificates (Editor+ role required)
    """
    try:
        return await CrewCertificateService.bulk_delete_crew_certificates(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting crew certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete crew certificates")

@router.post("/check-duplicate")
async def check_duplicate_crew_certificate(
    crew_id: str,
    cert_name: str,
    cert_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Check if crew certificate is duplicate
    """
    try:
        return await CrewCertificateService.check_duplicate(crew_id, cert_name, cert_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

@router.post("/analyze-file")
async def analyze_crew_certificate_file(
    certificate_file: UploadFile = File(...),
    crew_id: str = Query(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze crew certificate file using AI (Editor+ role required)
    """
    try:
        return await CrewCertificateService.analyze_crew_certificate_file(certificate_file, crew_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing crew certificate file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze crew certificate: {str(e)}")


@router.post("/{cert_id}/upload-files")
async def upload_crew_certificate_files(
    cert_id: str,
    files: List[UploadFile] = File(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload multiple files for a crew certificate (Editor+ role required)
    """
    try:
        import os
        from pathlib import Path
        
        # Verify certificate exists
        cert = await CrewCertificateService.get_crew_certificate_by_id(cert_id, current_user)
        if not cert:
            raise HTTPException(status_code=404, detail="Crew certificate not found")
        
        # Create upload directory
        upload_dir = Path(f"/app/uploads/crew-certificates/{cert_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        for file in files:
            # Save file
            file_path = upload_dir / file.filename
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            uploaded_files.append({
                "filename": file.filename,
                "path": f"/uploads/crew-certificates/{cert_id}/{file.filename}",
                "size": len(content)
            })
        
        logger.info(f"✅ Uploaded {len(uploaded_files)} files for crew certificate {cert_id}")
        
        return {
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "files": uploaded_files
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading crew certificate files: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload files")

@router.get("/{cert_id}/file-link")
async def get_crew_certificate_file_link(
    cert_id: str,
    filename: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get file download link for crew certificate
    """
    try:
        import os
        from pathlib import Path
        
        # Verify certificate exists
        cert = await CrewCertificateService.get_crew_certificate_by_id(cert_id, current_user)
        if not cert:
            raise HTTPException(status_code=404, detail="Crew certificate not found")
        
        # Get file path
        if filename:
            file_path = f"/uploads/crew-certificates/{cert_id}/{filename}"
        else:
            # Return first file if no filename specified
            cert_dir = Path(f"/app/uploads/crew-certificates/{cert_id}")
            if cert_dir.exists():
                files = list(cert_dir.iterdir())
                if files:
                    file_path = f"/uploads/crew-certificates/{cert_id}/{files[0].name}"
                else:
                    raise HTTPException(status_code=404, detail="No files found for certificate")
            else:
                raise HTTPException(status_code=404, detail="No files found for certificate")
        
        # Check if file exists
        if not os.path.exists(f"/app{file_path}"):
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "file_url": file_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting crew certificate file link: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file link")

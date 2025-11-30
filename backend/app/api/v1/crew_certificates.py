import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form

from app.models.crew_certificate import (
    CrewCertificateCreate,
    CrewCertificateUpdate,
    CrewCertificateResponse,
    BulkDeleteCrewCertificateRequest,
    CrewCertificateCheckDuplicate
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

@router.post("/manual", response_model=CrewCertificateResponse)
async def create_crew_certificate_manual(
    cert_data: CrewCertificateCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Create crew certificate manually without file upload (Editor+ role required)
    Ship/Folder is determined automatically based on crew's ship_sign_on field
    """
    try:
        logger.info(f"📋 Creating crew certificate manually for crew: {cert_data.crew_name}")
        return await CrewCertificateService.create_crew_certificate(cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating crew certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to create crew certificate")

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

@router.post("/check-duplicate")
async def check_duplicate_crew_certificate(
    request: CrewCertificateCheckDuplicate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Check if crew certificate is duplicate (accepts JSON body)
    """
    try:
        return await CrewCertificateService.check_duplicate(request.crew_id, None, request.cert_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

@router.post("/analyze-file")
async def analyze_crew_certificate_file(
    cert_file: UploadFile = File(...),
    crew_id: str = Form(...),
    ship_id: Optional[str] = Form(None),
    bypass_validation: str = Form("false"),
    bypass_dob_validation: str = Form("false"),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze crew certificate file using AI (Editor+ role required)
    Matches frontend pattern from AddCrewCertificateModal
    """
    try:
        logger.info(f"📋 Analyze crew certificate request - crew_id: {crew_id}, ship_id: {ship_id}")
        return await CrewCertificateService.analyze_crew_certificate_file(cert_file, crew_id, current_user)
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
    Upload crew certificate files to Google Drive (Editor+ role required)
    """
    try:
        from app.services.crew_certificate_drive_service import CrewCertificateDriveService
        
        # Verify certificate exists
        cert = await CrewCertificateService.get_crew_certificate_by_id(cert_id, current_user)
        if not cert:
            raise HTTPException(status_code=404, detail="Crew certificate not found")
        
        # Get crew_id from certificate
        crew_id = cert.crew_id
        company_id = current_user.company
        
        uploaded_files = []
        cert_file_id = None
        
        for file in files:
            # Read file content
            content = await file.read()
            
            # Upload to Google Drive
            result = await CrewCertificateDriveService.upload_certificate_file(
                company_id=company_id,
                crew_id=crew_id,
                file_content=content,
                filename=file.filename,
                mime_type=file.content_type or 'application/octet-stream'
            )
            
            # Store first file as main certificate file
            if not cert_file_id:
                cert_file_id = result['file_id']
            
            uploaded_files.append({
                "filename": result['filename'],
                "file_id": result['file_id'],
                "folder_path": result['folder_path'],
                "size": len(content)
            })
        
        # Update certificate with file_id
        if cert_file_id:
            from app.services.crew_certificate_service import CrewCertificateService
            from app.models.crew_certificate import CrewCertificateUpdate
            
            update_data = CrewCertificateUpdate(crew_cert_file_id=cert_file_id)
            await CrewCertificateService.update_crew_certificate(cert_id, update_data, current_user)
        
        logger.info(f"✅ Uploaded {len(uploaded_files)} files to Google Drive for crew certificate {cert_id}")
        
        return {
            "message": f"Successfully uploaded {len(uploaded_files)} files to Google Drive",
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

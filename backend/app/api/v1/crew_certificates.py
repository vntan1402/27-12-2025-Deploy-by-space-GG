import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form, Body

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

@router.post("/check-duplicate")
async def check_crew_certificate_duplicate(
    check_data: dict = Body(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Check if a crew certificate is duplicate based on crew_id + cert_no
    Returns existing certificate info if duplicate found
    """
    try:
        crew_id = check_data.get('crew_id')
        cert_no = check_data.get('cert_no')
        
        if not crew_id or not cert_no:
            return {
                "is_duplicate": False,
                "message": "Missing crew_id or cert_no"
            }
        
        logger.info(f"🔍 Checking duplicate for crew_id: {crew_id}, cert_no: {cert_no}")
        
        result = await CrewCertificateService.check_duplicate(
            crew_id=crew_id,
            cert_no=cert_no,
            current_user=current_user
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check duplicate: {str(e)}")


@router.post("/manual", response_model=CrewCertificateResponse)
async def create_crew_certificate_manual(
    cert_data: CrewCertificateCreate,
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Create crew certificate manually without file upload (Editor+ role required)
    Ship/Folder is determined automatically based on crew's ship_sign_on field
    """
    try:
        # Auto-set company_id from current_user if not provided
        if not cert_data.company_id:
            cert_data.company_id = current_user.company
        
        logger.info(f"📋 Creating crew certificate manually for crew: {cert_data.crew_name}")
        return await CrewCertificateService.create_crew_certificate(cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating crew certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to create crew certificate")

@router.post("/{cert_id}/upload-files")
async def upload_crew_certificate_files(
    cert_id: str,
    file_data: dict = Body(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload crew certificate files to Google Drive AFTER successful certificate creation
    
    Request Body:
    {
        "file_content": "base64_encoded_file_content",
        "filename": "certificate.pdf",
        "content_type": "application/pdf",
        "summary_text": "OCR extracted text"
    }
    
    Returns:
    {
        "success": true,
        "message": "Files uploaded successfully",
        "cert_file_id": "gdrive-file-id-xxx",
        "summary_file_id": "gdrive-file-id-yyy"
    }
    """
    import base64
    from app.services.crew_certificate_drive_service import CrewCertificateDriveService
    from app.repositories.crew_certificate_repository import CrewCertificateRepository
    
    try:
        logger.info(f"📤 Upload crew certificate files request for cert: {cert_id}")
        
        # 1. Verify certificate exists
        cert = await CrewCertificateRepository.find_by_id(cert_id)
        if not cert:
            raise HTTPException(status_code=404, detail=f"Certificate {cert_id} not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            if cert.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # 2. Validate required fields
        required_fields = ['file_content', 'filename']
        missing_fields = [f for f in required_fields if f not in file_data]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # 3. Decode file content
        try:
            file_content = base64.b64decode(file_data['file_content'])
            logger.info(f"✅ Decoded file content: {len(file_content)} bytes")
        except Exception as e:
            logger.error(f"❌ Failed to decode base64: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid base64 file content: {str(e)}")
        
        # Validate file size (max 10MB)
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > 10:
            raise HTTPException(status_code=413, detail=f"File too large: {file_size_mb:.2f}MB (max 10MB)")
        
        # 4. Prepare upload data
        upload_data = {
            'file_content': file_content,
            'filename': file_data['filename'],
            'content_type': file_data.get('content_type', 'application/octet-stream'),
            'summary_text': file_data.get('summary_text', ''),
            'cert_id': cert_id,
            'crew_name': cert.get('crew_name', ''),
            'cert_name': cert.get('cert_name', ''),
            'cert_no': cert.get('cert_no', '')
        }
        
        # 5. Upload files to Google Drive via service
        drive_service = CrewCertificateDriveService()
        upload_result = await drive_service.upload_certificate_files(**upload_data)
        
        # 6. Update certificate with file IDs
        cert_file_id = upload_result.get('cert_file_id')
        summary_file_id = upload_result.get('summary_file_id')
        
        if cert_file_id or summary_file_id:
            update_data = {}
            if cert_file_id:
                update_data['crew_cert_file_id'] = cert_file_id
            if summary_file_id:
                update_data['crew_cert_summary_file_id'] = summary_file_id
            
            await CrewCertificateRepository.update(cert_id, update_data)
            logger.info(f"✅ Updated certificate {cert_id} with file IDs")
        
        return {
            "success": True,
            "message": "Files uploaded successfully to Google Drive",
            "cert_file_id": cert_file_id,
            "summary_file_id": summary_file_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading crew certificate files: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload crew certificate files: {str(e)}"
        )

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
    crew_id: str = Body(...),
    cert_no: str = Body(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Check if crew certificate is duplicate based on crew_id + cert_no (accepts JSON body)
    """
    try:
        return await CrewCertificateService.check_duplicate(crew_id, None, cert_no, current_user)
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

@router.post("/bulk-auto-rename")
async def bulk_auto_rename_certificates(
    request: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Bulk auto-rename crew certificate files using naming convention:
    {Rank}_{Full Name (Eng)}_{Certificate Name}.pdf
    """
    try:
        from app.services.crew_certificate_rename_service import CrewCertificateRenameService
        
        certificate_ids = request.get("certificate_ids", [])
        
        if not certificate_ids:
            raise HTTPException(status_code=400, detail="No certificate IDs provided")
        
        result = await CrewCertificateRenameService.bulk_auto_rename_certificate_files(
            certificate_ids=certificate_ids,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in bulk auto-rename endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        # Get certificate
        cert = await CrewCertificateService.get_crew_certificate_by_id(cert_id, current_user)
        if not cert:
            raise HTTPException(status_code=404, detail="Crew certificate not found")
        
        file_id = cert.get('crew_cert_file_id')
        if not file_id:
            raise HTTPException(status_code=404, detail="Certificate has no file")
        
        # Generate proper Google Drive download link
        # Use the export=download format with confirmation bypass
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"
        
        return {
            "file_url": download_url,
            "file_id": file_id,
            "cert_name": cert.get('cert_name', 'certificate')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting file link: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file link")

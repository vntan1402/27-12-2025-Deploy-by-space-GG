import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File, Form

from app.models.company_cert import CompanyCertCreate, CompanyCertUpdate, CompanyCertResponse, BulkDeleteCompanyCertRequest
from app.models.user import UserResponse, UserRole
from app.services.company_cert_service import CompanyCertService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_dpa_manager_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user is Admin or Manager in DPA department"""
    # Admin and Super Admin always have access
    if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        return current_user
    
    # Manager with DPA department has access
    if current_user.role == UserRole.MANAGER and current_user.department == "DPA":
        return current_user
    
    raise HTTPException(status_code=403, detail="Insufficient permissions. Admin or DPA Manager required.")

@router.get("", response_model=List[CompanyCertResponse])
async def get_company_certs(
    company: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Company Certificates, optionally filtered by company"""
    try:
        return await CompanyCertService.get_company_certs(company, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching Company Certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Company Certificates")

@router.get("/{cert_id}", response_model=CompanyCertResponse)
async def get_company_cert_by_id(
    cert_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific Company Certificate by ID"""
    try:
        return await CompanyCertService.get_company_cert_by_id(cert_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Company Certificate {cert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Company Certificate")

@router.post("", response_model=CompanyCertResponse)
async def create_company_cert(
    cert_data: CompanyCertCreate,
    current_user: UserResponse = Depends(check_dpa_manager_permission)
):
    """Create new Company Certificate (Admin or DPA Manager required)"""
    try:
        return await CompanyCertService.create_company_cert(cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating Company Certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Company Certificate")

@router.put("/{cert_id}", response_model=CompanyCertResponse)
async def update_company_cert(
    cert_id: str,
    cert_data: CompanyCertUpdate,
    current_user: UserResponse = Depends(check_dpa_manager_permission)
):
    """Update Company Certificate (Admin or DPA Manager required)"""
    try:
        return await CompanyCertService.update_company_cert(cert_id, cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating Company Certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Company Certificate")

@router.delete("/{cert_id}")
async def delete_company_cert(
    cert_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_dpa_manager_permission)
):
    """Delete Company Certificate (Admin or DPA Manager required)"""
    try:
        return await CompanyCertService.delete_company_cert(cert_id, current_user, background_tasks)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Company Certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Company Certificate")

@router.post("/bulk-delete")
async def bulk_delete_company_certs(
    request: BulkDeleteCompanyCertRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_dpa_manager_permission)
):
    """Bulk delete Company Certificates (Admin or DPA Manager required)"""
    try:
        return await CompanyCertService.bulk_delete_company_certs(request, current_user, background_tasks)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Company Certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Company Certificates")

@router.post("/analyze-file")
async def analyze_company_cert_file_endpoint(
    request: dict,
    current_user: UserResponse = Depends(check_dpa_manager_permission)
):
    """
    Analyze company certificate file with AI
    Extract: cert_name, cert_no, issue_date, valid_date, issued_by
    """
    try:
        import base64
        from app.services.company_cert_analyze_service import analyze_company_cert_file
        from app.services.ai_config_service import AIConfigService
        
        file_content_b64 = request.get("file_content")
        filename = request.get("filename")
        content_type = request.get("content_type", "application/pdf")
        
        if not file_content_b64 or not filename:
            raise HTTPException(status_code=400, detail="Missing file_content or filename")
        
        # Decode base64
        file_content = base64.b64decode(file_content_b64)
        
        # Get AI config
        ai_config_response = await AIConfigService.get_ai_config(current_user)
        ai_config_doc = {
            'provider': ai_config_response.provider,
            'model': ai_config_response.model,
            'use_emergent_key': ai_config_response.use_emergent_key,
            'custom_api_key': ai_config_response.custom_api_key,
            'temperature': ai_config_response.temperature,
            'max_tokens': ai_config_response.max_tokens,
            'document_ai': ai_config_response.document_ai or {}
        }
        
        # Extract Document AI config
        document_ai_config = ai_config_doc.get('document_ai', {})
        
        # Analyze file
        result = await analyze_company_cert_file(
            file_content=file_content,
            filename=filename,
            content_type=content_type,
            company_id=current_user.company,
            document_ai_config=document_ai_config,
            ai_config=ai_config_doc
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing company cert file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")

@router.post("/upload-with-file")
async def upload_company_cert_with_file(
    file: UploadFile = File(...),
    cert_data: str = Form(...),
    current_user: UserResponse = Depends(check_dpa_manager_permission)
):
    """
    Upload company certificate with file
    Create DB record + Upload file to Google Drive
    """
    try:
        import json
        from app.services.gdrive_service import GDriveService
        
        # Parse cert_data JSON
        cert_dict = json.loads(cert_data)
        cert_dict["company"] = current_user.company
        cert_dict["created_by"] = current_user.id
        
        # Create certificate in DB first
        cert_response = await CompanyCertService.create_company_cert(
            CompanyCertCreate(**cert_dict),
            current_user
        )
        
        cert_id = cert_response.id
        
        # Upload file to Google Drive
        folder_path = "COMPANY DOCUMENT/SMS/Company Certificates"
        file_content = await file.read()
        
        logger.info(f"📤 Uploading file to GDrive: {file.filename}")
        drive_result = await GDriveService.upload_file(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type or "application/pdf",
            folder_path=folder_path,
            company_id=current_user.company
        )
        
        if drive_result.get("success"):
            file_id = drive_result.get("file_id")
            logger.info(f"✅ GDrive upload success! file_id={file_id}")
            
            # Prepare update data
            update_data = {
                "file_id": file_id,
                "file_name": file.filename,
                "file_url": drive_result.get("file_url")
            }
            
            # Create summary file if summary_text provided
            summary_text = cert_dict.get("summary_text")
            if summary_text:
                try:
                    logger.info("📝 Creating summary file...")
                    # Create summary filename
                    base_name = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename
                    summary_filename = f"{base_name}_Summary.txt"
                    
                    # Upload summary file (same folder as main file)
                    summary_result = await GDriveService.upload_file(
                        file_content=summary_text.encode('utf-8'),
                        filename=summary_filename,
                        content_type="text/plain",
                        folder_path="COMPANY DOCUMENT / SMS / Company Certificates",
                        company_id=current_user.company
                    )
                    
                    if summary_result.get("success"):
                        summary_file_id = summary_result.get("file_id")
                        logger.info(f"✅ Summary file uploaded successfully: {summary_file_id}")
                        update_data["summary_file_id"] = summary_file_id
                        update_data["summary_file_url"] = summary_result.get("file_url")
                except Exception as e:
                    logger.warning(f"⚠️ Summary file upload failed: {e}")
            
            # Update certificate with file info
            await CompanyCertService.update_company_cert(
                cert_id,
                CompanyCertUpdate(**update_data),
                current_user
            )
            
            return {
                "success": True,
                "certificate": cert_response,
                "message": "Certificate uploaded successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to upload file to Google Drive")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading company cert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload: {str(e)}")

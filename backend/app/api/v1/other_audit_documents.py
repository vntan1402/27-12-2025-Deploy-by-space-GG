import logging
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form, BackgroundTasks

from app.models.other_audit_document import OtherAuditDocumentCreate, OtherAuditDocumentUpdate, OtherAuditDocumentResponse, BulkDeleteOtherAuditDocumentRequest
from app.models.user import UserResponse, UserRole
from app.services.other_audit_document_service import OtherAuditDocumentService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[OtherAuditDocumentResponse])
async def get_other_audit_documents(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Other Audit Documents, optionally filtered by ship_id"""
    try:
        return await OtherAuditDocumentService.get_other_audit_documents(ship_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching Other Audit Documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Other Audit Documents")

@router.get("/{doc_id}", response_model=OtherAuditDocumentResponse)
async def get_other_audit_document_by_id(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific Other Audit Document by ID"""
    try:
        return await OtherAuditDocumentService.get_other_audit_document_by_id(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Other Audit Document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Other Audit Document")

@router.post("", response_model=OtherAuditDocumentResponse)
async def create_other_audit_document(
    doc_data: OtherAuditDocumentCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Create new Other Audit Document (Editor+ role required)"""
    try:
        return await OtherAuditDocumentService.create_other_audit_document(doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating Other Audit Document: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Other Audit Document")

@router.put("/{doc_id}", response_model=OtherAuditDocumentResponse)
async def update_other_audit_document(
    doc_id: str,
    doc_data: OtherAuditDocumentUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Update Other Audit Document (Editor+ role required)"""
    try:
        return await OtherAuditDocumentService.update_other_audit_document(doc_id, doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating Other Audit Document: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Other Audit Document")

@router.delete("/{doc_id}")
async def delete_other_audit_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Other Audit Document with background GDrive cleanup (Editor+ role required)"""
    try:
        return await OtherAuditDocumentService.delete_other_audit_document(doc_id, current_user, background_tasks)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Other Audit Document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Other Audit Document")

@router.post("/bulk-delete")
async def bulk_delete_other_audit_documents(
    request: BulkDeleteOtherAuditDocumentRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Other Audit Documents with background GDrive cleanup (Editor+ role required)"""
    try:
        return await OtherAuditDocumentService.bulk_delete_other_audit_documents(request, current_user, background_tasks)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Other Audit Documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Other Audit Documents")

@router.post("/check-duplicate")
async def check_duplicate_other_audit_document(
    ship_id: str,
    document_name: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if Other Audit Document is duplicate"""
    try:
        return await OtherAuditDocumentService.check_duplicate(ship_id, document_name, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")



# ==================== UPLOAD ENDPOINTS ====================

@router.post("/upload")
async def upload_other_audit_document(
    file: UploadFile = File(...),
    ship_id: str = Form(...),
    document_name: str = Form(...),
    date: Optional[str] = Form(None),
    status: Optional[str] = Form("Valid"),
    note: Optional[str] = Form(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Upload single file for Other Audit Document (PDF, JPG)"""
    try:
        logger.info(f"📤 Uploading audit document file: {file.filename} for ship: {ship_id}")
        
        # Validate file type
        allowed_extensions = ['.pdf', '.jpg', '.jpeg']
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only PDF and JPG files are supported. Got: {file_extension}"
            )
        
        # Read file content
        file_content = await file.read()
        logger.info(f"✅ File read successfully: {len(file_content)} bytes")
        
        # Call service
        result = await OtherAuditDocumentService.upload_single_file(
            file_content=file_content,
            filename=file.filename,
            ship_id=ship_id,
            document_name=document_name,
            date=date,
            status=status or "Valid",
            note=note,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading audit document: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-file-only")
async def upload_file_only(
    file: UploadFile = File(...),
    ship_id: str = Form(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Upload file without creating a record (for background uploads)"""
    try:
        logger.info(f"📤 Uploading audit file (file-only): {file.filename} for ship: {ship_id}")
        
        # Read file content (accept ALL file types)
        file_content = await file.read()
        logger.info(f"✅ File read successfully: {len(file_content)} bytes")
        
        # Call service
        result = await OtherAuditDocumentService.upload_file_only(
            file_content=file_content,
            filename=file.filename,
            ship_id=ship_id,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading audit file: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-folder")
async def upload_folder(
    files: List[UploadFile] = File(...),
    ship_id: str = Form(...),
    folder_name: str = Form(...),
    date: Optional[str] = Form(None),
    status: Optional[str] = Form("Valid"),
    note: Optional[str] = Form(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload folder with multiple files to GDrive using streaming approach.
    Files are read and uploaded one-by-one to minimize memory usage.
    """
    try:
        logger.info(f"📁 Uploading audit folder: {folder_name} with {len(files)} files for ship: {ship_id}")
        logger.info(f"   🚀 Using streaming upload (read → upload → clear) to minimize RAM usage")
        
        # Call service with UploadFile list (streaming mode)
        result = await OtherAuditDocumentService.upload_folder_streaming(
            files=files,  # Pass UploadFile objects directly
            ship_id=ship_id,
            folder_name=folder_name,
            date=date,
            status=status or "Valid",
            note=note,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading audit folder: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{doc_id}/upload-file")
async def upload_file_for_document(
    doc_id: str,
    file: UploadFile = File(...),
    ship_id: str = Form(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Upload file for existing audit document (background upload case)"""
    try:
        logger.info(f"📤 Uploading audit file for document {doc_id}: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        logger.info(f"✅ File read successfully: {len(file_content)} bytes")
        
        # Call service
        result = await OtherAuditDocumentService.upload_file_for_document(
            document_id=doc_id,
            ship_id=ship_id,
            file_content=file_content,
            filename=file.filename,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading audit file for document: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

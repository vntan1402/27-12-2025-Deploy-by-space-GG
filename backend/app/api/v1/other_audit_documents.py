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

@router.post("/upload-folder")
async def upload_other_audit_document_folder(
    ship_id: str,
    folder_id: str,
    folder_link: str,
    files: List[UploadFile] = File(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Upload folder of files for Other Audit Document (Editor+ role required)"""
    # TODO: Implement folder upload logic
    return {
        "success": True,
        "message": "Folder upload not yet implemented",
        "file_count": len(files)
    }

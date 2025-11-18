import logging
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form, BackgroundTasks

from app.models.other_doc import OtherDocumentCreate, OtherDocumentUpdate, OtherDocumentResponse, BulkDeleteOtherDocumentRequest
from app.models.user import UserResponse, UserRole
from app.services.other_doc_service import OtherDocumentService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[OtherDocumentResponse])
async def get_other_documents(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Other Documents, optionally filtered by ship_id"""
    try:
        return await OtherDocumentService.get_other_documents(ship_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching Other Documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Other Documents")

@router.get("/{doc_id}", response_model=OtherDocumentResponse)
async def get_other_document_by_id(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific Other Document by ID"""
    try:
        return await OtherDocumentService.get_other_document_by_id(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Other Document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Other Document")

@router.post("", response_model=OtherDocumentResponse)
async def create_other_document(
    doc_data: OtherDocumentCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Create new Other Document (Editor+ role required)"""
    try:
        return await OtherDocumentService.create_other_document(doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating Other Document: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Other Document")

@router.put("/{doc_id}", response_model=OtherDocumentResponse)
async def update_other_document(
    doc_id: str,
    doc_data: OtherDocumentUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Update Other Document (Editor+ role required)"""
    try:
        return await OtherDocumentService.update_other_document(doc_id, doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating Other Document: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Other Document")

@router.delete("/{doc_id}")
async def delete_other_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Other Document with background GDrive file cleanup (Editor+ role required)"""
    try:
        return await OtherDocumentService.delete_other_document(doc_id, current_user, background_tasks)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Other Document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Other Document")

@router.post("/bulk-delete")
async def bulk_delete_other_documents(
    request: BulkDeleteOtherDocumentRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Other Documents with background GDrive cleanup (Editor+ role required)"""
    try:
        return await OtherDocumentService.bulk_delete_other_documents(request, current_user, background_tasks)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Other Documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Other Documents")

@router.post("/check-duplicate")
async def check_duplicate_other_document(
    ship_id: str,
    document_name: str,
    document_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if Other Document is duplicate"""
    try:
        return await OtherDocumentService.check_duplicate(ship_id, document_name, document_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

@router.post("/analyze-file")
async def analyze_other_document_file(
    file: UploadFile = File(...),
    ship_id: Optional[str] = None,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Analyze other document file using AI (Editor+ role required)"""
    # TODO: Implement AI analysis for other documents
    return {
        "success": True,
        "message": "Other document analysis not yet implemented",
        "analysis": None
    }

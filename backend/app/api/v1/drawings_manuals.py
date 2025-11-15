import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query

from app.models.document import DocumentCreate, DocumentUpdate, DocumentResponse, BulkDeleteDocumentRequest
from app.models.user import UserResponse, UserRole
from app.services.document_service import GenericDocumentService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service for this document type
service = GenericDocumentService("drawings_manuals", "Drawing/Manual")

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[DocumentResponse])
async def get_documents(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Drawing/Manuals, optionally filtered by ship_id"""
    try:
        return await service.get_documents(ship_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching Drawing/Manuals: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Drawing/Manuals")

@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document_by_id(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific Drawing/Manual by ID"""
    try:
        return await service.get_document_by_id(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Drawing/Manual {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Drawing/Manual")

@router.post("", response_model=DocumentResponse)
async def create_document(
    doc_data: DocumentCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Create new Drawing/Manual (Editor+ role required)"""
    try:
        return await service.create_document(doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating Drawing/Manual: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Drawing/Manual")

@router.put("/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: str,
    doc_data: DocumentUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Update Drawing/Manual (Editor+ role required)"""
    try:
        return await service.update_document(doc_id, doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating Drawing/Manual: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Drawing/Manual")

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Drawing/Manual (Editor+ role required)"""
    try:
        return await service.delete_document(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Drawing/Manual: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Drawing/Manual")

@router.post("/bulk-delete")
async def bulk_delete_documents(
    request: BulkDeleteDocumentRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Drawing/Manuals (Editor+ role required)"""
    try:
        return await service.bulk_delete_documents(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Drawing/Manuals: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Drawing/Manuals")

@router.post("/check-duplicate")
async def check_duplicate_document(
    ship_id: str,
    doc_name: str,
    doc_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if Drawing/Manual is duplicate"""
    try:
        return await service.check_duplicate(ship_id, doc_name, doc_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")


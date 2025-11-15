import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query

from app.models.approval_document import ApprovalDocumentCreate, ApprovalDocumentUpdate, ApprovalDocumentResponse, BulkDeleteApprovalDocumentRequest
from app.models.user import UserResponse, UserRole
from app.services.approval_document_service import ApprovalDocumentService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[ApprovalDocumentResponse])
async def get_approval_documents(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Approval Documents, optionally filtered by ship_id"""
    try:
        return await ApprovalDocumentService.get_approval_documents(ship_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching Approval Documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Approval Documents")

@router.get("/{doc_id}", response_model=ApprovalDocumentResponse)
async def get_approval_document_by_id(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific Approval Document by ID"""
    try:
        return await ApprovalDocumentService.get_approval_document_by_id(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Approval Document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Approval Document")

@router.post("", response_model=ApprovalDocumentResponse)
async def create_approval_document(
    doc_data: ApprovalDocumentCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Create new Approval Document (Editor+ role required)"""
    try:
        return await ApprovalDocumentService.create_approval_document(doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating Approval Document: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Approval Document")

@router.put("/{doc_id}", response_model=ApprovalDocumentResponse)
async def update_approval_document(
    doc_id: str,
    doc_data: ApprovalDocumentUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Update Approval Document (Editor+ role required)"""
    try:
        return await ApprovalDocumentService.update_approval_document(doc_id, doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating Approval Document: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Approval Document")

@router.delete("/{doc_id}")
async def delete_approval_document(
    doc_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Approval Document (Editor+ role required)"""
    try:
        return await ApprovalDocumentService.delete_approval_document(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Approval Document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Approval Document")

@router.post("/bulk-delete")
async def bulk_delete_approval_documents(
    request: BulkDeleteApprovalDocumentRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Approval Documents (Editor+ role required)"""
    try:
        return await ApprovalDocumentService.bulk_delete_approval_documents(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Approval Documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Approval Documents")

@router.post("/check-duplicate")
async def check_duplicate_approval_document(
    ship_id: str,
    approval_document_name: str,
    approval_document_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if Approval Document is duplicate"""
    try:
        return await ApprovalDocumentService.check_duplicate(ship_id, approval_document_name, approval_document_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

@router.post("/analyze")
async def analyze_approval_document_file(
    file: UploadFile = File(...),
    ship_id: Optional[str] = None,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Analyze approval document file using AI (Editor+ role required)"""
    # TODO: Implement AI analysis for approval documents
    return {
        "success": True,
        "message": "Approval document analysis not yet implemented",
        "analysis": None
    }

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, Query

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

@router.post("/analyze-file")
async def analyze_approval_document_file(
    ship_id: str = Form(...),
    document_file: UploadFile = File(...),
    bypass_validation: str = Form("false"),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze approval document file using AI (Editor+ role required)
    
    Process:
    1. Validate PDF file (magic bytes, extension, max 50MB)
    2. Check if needs splitting (>15 pages)
    3. Process with Document AI (parallel chunks if large)
    4. Extract fields with System AI
    5. Normalize approved_by
    6. Return analysis + base64 file for upload
    
    Returns:
        dict: Analysis result with extracted fields + metadata
            {
                "approval_document_name": str,
                "approval_document_no": str,
                "approved_by": str (normalized),
                "approved_date": str (YYYY-MM-DD),
                "note": str,
                "confidence_score": float,
                "processing_method": str,
                "_filename": str,
                "_file_content": str (base64),
                "_content_type": str,
                "_summary_text": str,
                "_split_info": dict (if large file)
            }
    """
    try:
        from app.services.approval_document_analyze_service import ApprovalDocumentAnalyzeService
        
        bypass = bypass_validation.lower() == "true"
        
        result = await ApprovalDocumentAnalyzeService.analyze_file(
            file=document_file,
            ship_id=ship_id,
            bypass_validation=bypass,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing approval document: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/upload-files")
async def upload_approval_document_files(
    document_id: str,
    file_content: str = Body(...),
    filename: str = Body(...),
    content_type: str = Body(...),
    summary_text: Optional[str] = Body(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload approval document files to Google Drive after record creation
    
    Path: {ship_name}/ISM-ISPS-MLC/Approval Document/
    - Original file and summary file in SAME folder
    
    Args:
        document_id: Document ID
        file_content: Base64 encoded file content
        filename: Original filename
        content_type: File MIME type
        summary_text: Optional summary text for summary file
        
    Returns:
        dict: Upload result
            {
                "success": true,
                "message": "...",
                "document": ApprovalDocumentResponse,
                "original_file_id": str,
                "summary_file_id": str,
                "summary_error": str (if summary upload failed)
            }
    """
    try:
        result = await ApprovalDocumentService.upload_files(
            document_id=document_id,
            file_content=file_content,
            filename=filename,
            content_type=content_type,
            summary_text=summary_text,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading approval document files: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


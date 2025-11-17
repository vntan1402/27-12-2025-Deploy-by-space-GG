import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form, Body, BackgroundTasks

from app.models.drawing_manual import DrawingManualCreate, DrawingManualUpdate, DrawingManualResponse, BulkDeleteDrawingManualRequest
from app.models.user import UserResponse, UserRole
from app.services.drawing_manual_service import DrawingManualService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[DrawingManualResponse])
async def get_drawings_manuals(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Drawings & Manuals, optionally filtered by ship_id"""
    try:
        return await DrawingManualService.get_drawings_manuals(ship_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching Drawings & Manuals: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Drawings & Manuals")

@router.get("/{doc_id}", response_model=DrawingManualResponse)
async def get_drawing_manual_by_id(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific Drawing/Manual by ID"""
    try:
        return await DrawingManualService.get_drawing_manual_by_id(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Drawing/Manual {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Drawing/Manual")

@router.post("", response_model=DrawingManualResponse)
async def create_drawing_manual(
    doc_data: DrawingManualCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Create new Drawing/Manual (Editor+ role required)"""
    try:
        return await DrawingManualService.create_drawing_manual(doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating Drawing/Manual: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Drawing/Manual")

@router.put("/{doc_id}", response_model=DrawingManualResponse)
async def update_drawing_manual(
    doc_id: str,
    doc_data: DrawingManualUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Update Drawing/Manual (Editor+ role required)"""
    try:
        return await DrawingManualService.update_drawing_manual(doc_id, doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating Drawing/Manual: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Drawing/Manual")

@router.delete("/{doc_id}")
async def delete_drawing_manual(
    doc_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Drawing/Manual (Editor+ role required)"""
    try:
        return await DrawingManualService.delete_drawing_manual(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Drawing/Manual: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Drawing/Manual")

@router.post("/bulk-delete")
async def bulk_delete_drawings_manuals(
    request: BulkDeleteDrawingManualRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Drawings & Manuals (Editor+ role required)"""
    try:
        return await DrawingManualService.bulk_delete_drawings_manuals(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Drawings & Manuals: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Drawings & Manuals")

@router.post("/check-duplicate")
async def check_duplicate_drawing_manual(
    ship_id: str,
    document_name: str,
    document_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if Drawing/Manual is duplicate"""
    try:
        return await DrawingManualService.check_duplicate(ship_id, document_name, document_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

@router.post("/analyze-file")
async def analyze_drawing_manual_file(
    ship_id: str = Form(...),
    document_file: UploadFile = File(...),
    bypass_validation: str = Form("false"),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze drawing/manual file using AI (Editor+ role required)
    
    Process:
    1. Validate PDF file
    2. Check if needs splitting (>15 pages)
    3. Process with Document AI (parallel chunks if large)
    4. Extract fields with System AI
    5. Normalize document_name & approved_by
    6. Return analysis + base64 file for upload
    """
    try:
        from app.services.drawing_manual_analyze_service import DrawingManualAnalyzeService
        
        bypass = bypass_validation.lower() == "true"
        
        result = await DrawingManualAnalyzeService.analyze_file(
            file=document_file,
            ship_id=ship_id,
            bypass_validation=bypass,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing drawing/manual: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/upload-files")
async def upload_drawing_manual_files(
    document_id: str,
    file_content: str = Body(...),
    filename: str = Body(...),
    content_type: str = Body(...),
    summary_text: Optional[str] = Body(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload drawing/manual files to Google Drive after record creation
    
    Path: {ship_name}/Class & Flag Cert/Drawings & Manuals/
    - Both original and summary files in SAME folder
    """
    try:
        result = await DrawingManualService.upload_files(
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
        logger.error(f"❌ Error uploading drawing/manual files: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


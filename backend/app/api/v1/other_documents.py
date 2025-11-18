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


# ==================== UPLOAD ENDPOINTS ====================

@router.post("/upload")
async def upload_other_document(
    file: UploadFile = File(...),
    ship_id: str = Form(...),
    document_name: str = Form(...),
    date: Optional[str] = Form(None),
    status: Optional[str] = Form("Valid"),
    note: Optional[str] = Form(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload a single file for other documents (PDF, JPG)
    NO AI processing - just file upload and metadata storage
    
    Creates 1 record with uploaded file
    """
    try:
        logger.info(f"📤 Uploading other document file: {file.filename} for ship: {ship_id}")
        
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
        result = await OtherDocumentService.upload_single_file(
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
        logger.error(f"❌ Error uploading other document: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-file-only")
async def upload_file_only(
    file: UploadFile = File(...),
    ship_id: str = Form(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload a file to Google Drive without creating a record
    Returns only the file_id for later use
    Accepts ALL file types (no filtering)
    
    Used for background uploads where record is already created
    """
    try:
        logger.info(f"📤 Uploading file (file-only): {file.filename} for ship: {ship_id}")
        
        # Read file content (accept ALL file types)
        file_content = await file.read()
        logger.info(f"✅ File read successfully: {len(file_content)} bytes")
        
        # Call service
        result = await OtherDocumentService.upload_file_only(
            file_content=file_content,
            filename=file.filename,
            ship_id=ship_id,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading file: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-folder")
async def upload_folder(
    files: List[UploadFile] = File(...),
    ship_id: str = Form(...),
    folder_name: str = Form(...),
    date: Optional[str] = Form(None),
    status: Optional[str] = Form("Unknown"),
    note: Optional[str] = Form(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload a folder with multiple files to Google Drive
    Creates a subfolder under "Other Documents" and uploads all files into it
    Also creates a single record with folder_id and folder_link
    """
    try:
        logger.info(f"📁 Uploading folder: {folder_name} with {len(files)} files for ship: {ship_id}")
        
        # Read all files into memory
        files_data = []
        for file in files:
            file_content = await file.read()
            # Extract only the filename, remove any folder path
            filename = os.path.basename(file.filename)
            files_data.append((file_content, filename))
            logger.info(f"   📄 Read file: {filename} ({len(file_content)} bytes)")
        
        # Call service
        result = await OtherDocumentService.upload_folder(
            files=files_data,
            ship_id=ship_id,
            folder_name=folder_name,
            date=date,
            status=status or "Unknown",
            note=note,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading folder: {e}")
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
    """
    Upload file for an existing document (background upload case)
    Updates the document's file_ids array
    """
    try:
        logger.info(f"📤 Uploading file for document {doc_id}: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        logger.info(f"✅ File read successfully: {len(file_content)} bytes")
        
        # Call service
        result = await OtherDocumentService.upload_file_for_document(
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
        logger.error(f"❌ Error uploading file for document: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

import logging
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form, BackgroundTasks

from app.models.other_doc import OtherDocumentCreate, OtherDocumentUpdate, OtherDocumentResponse, BulkDeleteOtherDocumentRequest
from app.models.user import UserResponse, UserRole
from app.services.other_doc_service import OtherDocumentService
from app.core.security import get_current_user
from app.core import messages


logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail=messages.PERMISSION_DENIED)
    return current_user

@router.get("", response_model=List[OtherDocumentResponse])
async def get_other_documents(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Other Documents, optionally filtered by ship_id"""
    try:
        return await OtherDocumentService.get_other_documents(ship_id, current_user)
    except HTTPException:
        raise
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
    status: Optional[str] = Form("Valid"),
    note: Optional[str] = Form(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload folder using PARALLEL approach with streaming.
    - Files upload in parallel with 1s staggered delay
    - Memory efficient: Read file only when needed
    - Much faster than sequential upload
    """
    try:
        logger.info(f"📁 Uploading folder: {folder_name} with {len(files)} files for ship: {ship_id}")
        logger.info("   🚀 Using parallel streaming upload (1s staggered delay)")
        
        # Call service with streaming mode
        result = await OtherDocumentService.upload_folder_streaming(
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
        logger.error(f"❌ Error uploading folder: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== BACKGROUND FOLDER UPLOAD ENDPOINTS ==========

@router.post("/background-upload-folder/create-task")
async def create_background_upload_task(
    ship_id: str = Form(...),
    folder_name: str = Form(...),
    total_files: int = Form(...),
    date: Optional[str] = Form(None),
    status: Optional[str] = Form("Valid"),
    note: Optional[str] = Form(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    V2: Create upload task (metadata only).
    Frontend uploads files one by one to /background-upload-folder/{task_id}/upload-file
    """
    from app.services.background_upload_service import BackgroundUploadService
    
    try:
        logger.info(f"📁 Creating background upload task: {folder_name} for {total_files} files")
        
        result = await BackgroundUploadService.create_upload_task(
            ship_id=ship_id,
            folder_name=folder_name,
            total_files=total_files,
            date=date,
            status=status or "Valid",
            note=note,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating background upload task: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/background-upload-folder/{task_id}/upload-file")
async def upload_file_to_task(
    task_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    V2: Upload a single file to an existing task.
    Call this for each file sequentially with 1s delay between calls.
    """
    from app.services.background_upload_service import BackgroundUploadService
    
    try:
        logger.info(f"📤 Uploading file to task {task_id}: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        filename = file.filename.split('/')[-1] if '/' in file.filename else file.filename
        
        result = await BackgroundUploadService.upload_single_file_to_task(
            task_id=task_id,
            file_content=file_content,
            filename=filename,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading file to task: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/background-upload-folder/{task_id}/add-file")
async def add_file_to_task(
    task_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    V3: Add a file to task's pending queue. Backend will process later.
    Frontend sends all files first, then calls /start-processing.
    """
    from app.services.background_upload_service import BackgroundUploadTaskService
    import base64
    
    try:
        # Get task and verify
        task = await BackgroundUploadTaskService.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        if task.get("status") not in ["pending", "receiving"]:
            raise HTTPException(status_code=400, detail=f"Task already {task.get('status')}")
        
        # Update status to receiving if first file
        if task.get("status") == "pending":
            await BackgroundUploadTaskService.update_task(task_id, {"status": "receiving"})
        
        # Read file content and store as base64 (for MongoDB storage)
        file_content = await file.read()
        filename = file.filename.split('/')[-1] if '/' in file.filename else file.filename
        
        # Determine content type
        if filename.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        elif filename.lower().endswith('.png'):
            content_type = 'image/png'
        else:
            content_type = file.content_type or 'application/octet-stream'
        
        # Store file data
        file_data = {
            "filename": filename,
            "content_base64": base64.b64encode(file_content).decode('utf-8'),
            "content_type": content_type,
            "size": len(file_content)
        }
        
        await BackgroundUploadTaskService.add_pending_file(task_id, file_data)
        
        # Get updated count
        task = await BackgroundUploadTaskService.get_task(task_id)
        received = task.get("received_files", 0)
        total = task.get("total_files", 0)
        
        logger.info(f"📥 Added file to task {task_id}: {filename} ({received}/{total})")
        
        return {
            "success": True,
            "filename": filename,
            "received_files": received,
            "total_files": total
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding file to task: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/background-upload-folder/{task_id}/start-processing")
async def start_task_processing(
    task_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    V3: Start background processing after all files are received.
    Backend will upload files to GDrive using asyncio.create_task().
    """
    from app.services.background_upload_service import BackgroundUploadTaskService, BackgroundUploadService
    
    try:
        # Get task and verify
        task = await BackgroundUploadTaskService.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        if task.get("status") not in ["pending", "receiving"]:
            raise HTTPException(status_code=400, detail=f"Task already {task.get('status')}")
        
        received = task.get("received_files", 0)
        total = task.get("total_files", 0)
        
        if received == 0:
            raise HTTPException(status_code=400, detail="No files received yet")
        
        logger.info(f"🚀 Starting background processing for task {task_id} ({received} files)")
        
        # Update status
        await BackgroundUploadTaskService.update_task(task_id, {
            "status": "processing",
            "total_files": received  # Update to actual received count
        })
        
        # Start background processing (like Auto Rename)
        import asyncio
        asyncio.create_task(
            BackgroundUploadService.process_pending_files_background(
                task_id=task_id,
                current_user=current_user
            )
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Background processing started for {received} files",
            "total_files": received
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting task processing: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/background-upload-folder")
async def background_upload_folder(
    files: List[UploadFile] = File(...),
    ship_id: str = Form(...),
    folder_name: str = Form(...),
    date: Optional[str] = Form(None),
    status: Optional[str] = Form("Valid"),
    note: Optional[str] = Form(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Start background folder upload.
    Returns task_id for polling status.
    """
    from app.services.background_upload_service import BackgroundUploadService
    
    try:
        logger.info(f"📁 Starting background upload: {folder_name} with {len(files)} files")
        
        result = await BackgroundUploadService.start_folder_upload(
            files=files,
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
        logger.error(f"❌ Error starting background upload: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/background-upload-folder/{task_id}")
async def get_background_upload_status(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get status of a background folder upload task.
    Poll this endpoint to track progress.
    """
    from app.services.background_upload_service import BackgroundUploadService
    
    try:
        return await BackgroundUploadService.get_task_status(task_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting background upload status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/background-upload-folder/{task_id}/cancel")
async def cancel_background_upload(
    task_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Cancel an in-progress background upload task.
    """
    from app.services.background_upload_service import BackgroundUploadTaskService
    
    try:
        logger.info(f"🚫 Cancel request for task {task_id} by user {current_user.id}")
        
        result = await BackgroundUploadTaskService.cancel_task(task_id, current_user.id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Cancel failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error cancelling background upload: {e}")
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

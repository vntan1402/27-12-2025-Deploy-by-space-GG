import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, BackgroundTasks

from app.models.approval_document import ApprovalDocumentCreate, ApprovalDocumentUpdate, ApprovalDocumentResponse, BulkDeleteApprovalDocumentRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class ApprovalDocumentService:
    """Service for Approval Document operations"""
    
    collection_name = "approval_documents"
    
    @staticmethod
    async def get_approval_documents(ship_id: Optional[str], current_user: UserResponse) -> List[ApprovalDocumentResponse]:
        """Get approval documents with optional ship filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        
        docs = await mongo_db.find_all(ApprovalDocumentService.collection_name, filters)
        
        # Handle backward compatibility
        result = []
        for doc in docs:
            if not doc.get("approval_document_name") and doc.get("doc_name"):
                doc["approval_document_name"] = doc.get("doc_name")
            
            if not doc.get("approval_document_no") and doc.get("doc_no"):
                doc["approval_document_no"] = doc.get("doc_no")
            
            if not doc.get("note") and doc.get("notes"):
                doc["note"] = doc.get("notes")
            
            if not doc.get("approval_document_name"):
                doc["approval_document_name"] = "Untitled Approval Document"
            
            if not doc.get("status"):
                doc["status"] = "Unknown"
            
            result.append(ApprovalDocumentResponse(**doc))
        
        return result
    
    @staticmethod
    async def get_approval_document_by_id(doc_id: str, current_user: UserResponse) -> ApprovalDocumentResponse:
        """Get approval document by ID"""
        doc = await mongo_db.find_one(ApprovalDocumentService.collection_name, {"id": doc_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Approval Document not found")
        
        # Backward compatibility
        if not doc.get("approval_document_name") and doc.get("doc_name"):
            doc["approval_document_name"] = doc.get("doc_name")
        
        if not doc.get("approval_document_no") and doc.get("doc_no"):
            doc["approval_document_no"] = doc.get("doc_no")
        
        if not doc.get("note") and doc.get("notes"):
            doc["note"] = doc.get("notes")
        
        if not doc.get("approval_document_name"):
            doc["approval_document_name"] = "Untitled Approval Document"
        
        if not doc.get("status"):
            doc["status"] = "Unknown"
        
        return ApprovalDocumentResponse(**doc)
    
    @staticmethod
    async def create_approval_document(doc_data: ApprovalDocumentCreate, current_user: UserResponse) -> ApprovalDocumentResponse:
        """Create new approval document"""
        doc_dict = doc_data.dict()
        doc_dict["id"] = str(uuid.uuid4())
        doc_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create(ApprovalDocumentService.collection_name, doc_dict)
        
        logger.info(f"✅ Approval Document created: {doc_dict['approval_document_name']}")
        
        return ApprovalDocumentResponse(**doc_dict)
    
    @staticmethod
    async def update_approval_document(doc_id: str, doc_data: ApprovalDocumentUpdate, current_user: UserResponse) -> ApprovalDocumentResponse:
        """Update approval document"""
        doc = await mongo_db.find_one(ApprovalDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Approval Document not found")
        
        update_data = doc_data.dict(exclude_unset=True)
        
        if update_data:
            await mongo_db.update(ApprovalDocumentService.collection_name, {"id": doc_id}, update_data)
        
        updated_doc = await mongo_db.find_one(ApprovalDocumentService.collection_name, {"id": doc_id})
        
        if not updated_doc.get("approval_document_name") and updated_doc.get("doc_name"):
            updated_doc["approval_document_name"] = updated_doc.get("doc_name")
        
        logger.info(f"✅ Approval Document updated: {doc_id}")
        
        return ApprovalDocumentResponse(**updated_doc)
    
    @staticmethod
    async def delete_approval_document(
        doc_id: str,
        current_user: UserResponse,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> dict:
        """
        Delete approval document with optional background GDrive cleanup
        
        Process:
        1. Get document and verify access
        2. Delete from database immediately
        3. Schedule background GDrive file deletion (if file IDs exist)
        
        Args:
            doc_id: Document ID
            current_user: Current user
            background_tasks: FastAPI BackgroundTasks (for async deletion)
            
        Returns:
            dict: Deletion result with background status
        """
        from app.utils.background_tasks import delete_file_background
        from app.services.gdrive_service import GDriveService
        
        # Get document
        doc = await mongo_db.find_one(ApprovalDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Approval Document not found")
        
        # Verify company access
        company_id = current_user.company
        ship_id = doc.get("ship_id")
        if ship_id:
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if ship and ship.get("company") != company_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Extract file info before deleting from DB
        file_id = doc.get("file_id")
        summary_file_id = doc.get("summary_file_id")
        document_name = doc.get("approval_document_name", "Unknown")
        
        # Delete from database immediately
        await mongo_db.delete(ApprovalDocumentService.collection_name, {"id": doc_id})
        logger.info(f"✅ Approval Document deleted from DB: {doc_id} ({document_name})")
        
        # Schedule background GDrive deletion
        files_scheduled = 0
        background_deletion = False
        
        if background_tasks and company_id:
            files_to_delete = []
            
            if file_id:
                files_to_delete.append(("original", file_id))
                logger.info(f"📋 Found original file to delete: {file_id}")
            
            if summary_file_id:
                files_to_delete.append(("summary", summary_file_id))
                logger.info(f"📋 Found summary file to delete: {summary_file_id}")
            
            if files_to_delete:
                for file_type, file_id_val in files_to_delete:
                    background_tasks.add_task(
                        delete_file_background,
                        file_id_val,
                        company_id,
                        "approval_document",
                        f"{document_name} ({file_type})",
                        GDriveService
                    )
                    logger.info(f"📋 Scheduled background deletion for {file_type} file: {file_id_val}")
                    files_scheduled += 1
                
                background_deletion = True
        
        message = "Approval Document deleted successfully"
        if background_deletion:
            message += f". File deletion in progress ({files_scheduled} file(s))..."
        
        return {
            "success": True,
            "message": message,
            "document_id": doc_id,
            "background_deletion": background_deletion,
            "files_scheduled": files_scheduled
        }
    
    @staticmethod
    async def bulk_delete_approval_documents(
        request: BulkDeleteApprovalDocumentRequest,
        current_user: UserResponse,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> dict:
        """
        Bulk delete approval documents with background GDrive cleanup
        
        Similar to single delete but processes multiple documents
        """
        from app.utils.background_tasks import delete_file_background
        from app.services.gdrive_service import GDriveService
        
        doc_ids = request.document_ids
        company_id = current_user.company
        
        deleted_count = 0
        files_scheduled = 0
        files_to_delete = []
        
        for doc_id in doc_ids:
            try:
                doc = await mongo_db.find_one(ApprovalDocumentService.collection_name, {"id": doc_id})
                if not doc:
                    continue
                
                # Verify access
                ship_id = doc.get("ship_id")
                if ship_id:
                    ship = await mongo_db.find_one("ships", {"id": ship_id})
                    if ship and ship.get("company") != company_id:
                        continue
                
                # Collect file IDs for background deletion
                document_name = doc.get("approval_document_name", "Unknown")
                
                if doc.get("file_id"):
                    files_to_delete.append({
                        'file_id': doc["file_id"],
                        'description': f"{document_name} (original)"
                    })
                
                if doc.get("summary_file_id"):
                    files_to_delete.append({
                        'file_id': doc["summary_file_id"],
                        'description': f"{document_name} (summary)"
                    })
                
                # Delete from database
                await mongo_db.delete(ApprovalDocumentService.collection_name, {"id": doc_id})
                deleted_count += 1
                logger.info(f"✅ Deleted approval document: {doc_id} ({document_name})")
                
            except Exception as e:
                logger.error(f"Error deleting document {doc_id}: {e}")
                continue
        
        # Schedule background deletions
        background_deletion = False
        if background_tasks and files_to_delete and company_id:
            for file_info in files_to_delete:
                background_tasks.add_task(
                    delete_file_background,
                    file_info['file_id'],
                    company_id,
                    "approval_document",
                    file_info['description'],
                    GDriveService
                )
                files_scheduled += 1
            
            background_deletion = True
            logger.info(f"📋 Scheduled {files_scheduled} file(s) for background deletion")
        
        message = f"Deleted {deleted_count} approval document(s)"
        if background_deletion:
            message += f". Background deletion of {files_scheduled} file(s) in progress..."
        
        logger.info(f"✅ Bulk deleted {deleted_count} approval documents")
        
        return {
            "success": True,
            "message": message,
            "deleted_count": deleted_count,
            "background_deletion": background_deletion,
            "files_scheduled": files_scheduled
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, approval_document_name: str, approval_document_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if approval document is duplicate"""
        filters = {
            "ship_id": ship_id,
            "approval_document_name": approval_document_name
        }
        
        if approval_document_no:
            filters["approval_document_no"] = approval_document_no
        
        existing = await mongo_db.find_one(ApprovalDocumentService.collection_name, filters)
        
        return {
            "is_duplicate": existing is not None,
            "existing_id": existing.get("id") if existing else None
        }

    
    @staticmethod
    async def upload_files(
        document_id: str,
        file_content: str,
        filename: str,
        content_type: str,
        summary_text: Optional[str],
        current_user: UserResponse
    ) -> dict:
        """
        Upload approval document files to Google Drive
        
        Process:
        1. Validate document exists
        2. Verify company access
        3. Decode base64 file content
        4. Upload original file to: ShipName/ISM-ISPS-MLC/Approval Document/
        5. Upload summary file (if summary_text provided)
        6. Update document with file IDs
        
        Args:
            document_id: Document ID
            file_content: Base64 encoded file
            filename: Original filename
            content_type: MIME type
            summary_text: Optional summary text
            current_user: Current user
            
        Returns:
            dict: Upload result with file IDs
        """
        try:
            logger.info(f"📤 Starting file upload for approval document: {document_id}")
            
            # Validate document exists
            document = await mongo_db.find_one(ApprovalDocumentService.collection_name, {"id": document_id})
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Get company and ship info
            company_id = current_user.company
            if not company_id:
                raise HTTPException(status_code=404, detail="Company not found")
            
            ship_id = document.get("ship_id")
            if not ship_id:
                raise HTTPException(status_code=400, detail="Document has no ship_id")
            
            # Get ship
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            # Verify company access
            ship_company = ship.get("company")
            if ship_company != company_id:
                logger.warning(f"Access denied: ship company '{ship_company}' != user company '{company_id}'")
                raise HTTPException(status_code=403, detail="Access denied to this ship")
            
            ship_name = ship.get("name", "Unknown Ship")
            
            # Decode base64 file content
            import base64
            try:
                file_bytes = base64.b64decode(file_content)
                logger.info(f"✅ Decoded file content: {len(file_bytes)} bytes")
            except Exception as e:
                logger.error(f"Failed to decode base64 file content: {e}")
                raise HTTPException(status_code=400, detail="Invalid file content encoding")
            
            logger.info(f"📄 Processing file: {filename} ({len(file_bytes)} bytes)")
            
            # Upload files to Google Drive
            from app.services.gdrive_service import GDriveService
            
            logger.info("📤 Uploading approval document files to Drive...")
            logger.info(f"📄 Target path: {ship_name}/ISM - ISPS - MLC/Approval Document/{filename}")
            
            # Upload original file to: ShipName/ISM - ISPS - MLC/Approval Document/
            upload_result = await GDriveService.upload_file(
                file_content=file_bytes,
                filename=filename,
                content_type=content_type,
                folder_path=f"{ship_name}/ISM - ISPS - MLC/Approval Document",
                company_id=company_id
            )
            
            if not upload_result.get('success'):
                logger.error(f"❌ File upload failed: {upload_result.get('message')}")
                raise HTTPException(
                    status_code=500,
                    detail=f"File upload failed: {upload_result.get('message', 'Unknown error')}"
                )
            
            original_file_id = upload_result.get('file_id')
            
            # Upload summary file if provided (to SAME folder)
            summary_file_id = None
            summary_error = None
            
            if summary_text and summary_text.strip():
                try:
                    # Create summary filename
                    base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                    summary_filename = f"{base_name}_Summary.txt"
                    
                    # Upload to SAME folder as original file
                    summary_folder_path = f"{ship_name}/ISM-ISPS-MLC/Approval Document"
                    
                    logger.info(f"📤 Uploading summary to: {summary_folder_path}/{summary_filename}")
                    
                    # Convert summary text to bytes
                    summary_bytes = summary_text.encode('utf-8')
                    
                    summary_upload = await GDriveService.upload_file(
                        file_content=summary_bytes,
                        filename=summary_filename,
                        content_type="text/plain",
                        folder_path=summary_folder_path,
                        company_id=company_id
                    )
                    
                    if summary_upload.get('success'):
                        summary_file_id = summary_upload.get('file_id')
                        logger.info(f"✅ Summary uploaded: {summary_file_id}")
                    else:
                        summary_error = summary_upload.get('message', 'Unknown error')
                        logger.warning(f"⚠️ Summary upload failed (non-critical): {summary_error}")
                        
                except Exception as summary_exc:
                    summary_error = str(summary_exc)
                    logger.warning(f"⚠️ Summary file upload error (non-critical): {summary_error}")
            
            # Update document with file IDs
            update_data = {}
            if original_file_id:
                update_data['file_id'] = original_file_id
            if summary_file_id:
                update_data['summary_file_id'] = summary_file_id
            
            if update_data:
                update_data['updated_at'] = datetime.now(timezone.utc)
                
                await mongo_db.update(
                    ApprovalDocumentService.collection_name,
                    {"id": document_id},
                    update_data
                )
                logger.info("✅ Document updated with file IDs")
            
            # Get updated document
            updated_doc = await mongo_db.find_one(ApprovalDocumentService.collection_name, {"id": document_id})
            
            # Handle backward compatibility
            if not updated_doc.get("approval_document_name") and updated_doc.get("doc_name"):
                updated_doc["approval_document_name"] = updated_doc.get("doc_name")
            
            if not updated_doc.get("approval_document_no") and updated_doc.get("doc_no"):
                updated_doc["approval_document_no"] = updated_doc.get("doc_no")
            
            if not updated_doc.get("status"):
                updated_doc["status"] = "Unknown"
            
            logger.info("✅ Approval document files uploaded successfully")
            
            return {
                "success": True,
                "message": "Approval document files uploaded successfully",
                "document": ApprovalDocumentResponse(**updated_doc),
                "original_file_id": original_file_id,
                "summary_file_id": summary_file_id,
                "summary_error": summary_error
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading approval document files: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))


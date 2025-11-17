import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.drawing_manual import DrawingManualCreate, DrawingManualUpdate, DrawingManualResponse, BulkDeleteDrawingManualRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class DrawingManualService:
    """Service for Drawing & Manual operations"""
    
    collection_name = "drawings_manuals"
    
    @staticmethod
    async def get_drawings_manuals(ship_id: Optional[str], current_user: UserResponse) -> List[DrawingManualResponse]:
        """Get drawings/manuals with optional ship filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        
        docs = await mongo_db.find_all(DrawingManualService.collection_name, filters)
        
        # Handle backward compatibility
        result = []
        for doc in docs:
            if not doc.get("document_name") and doc.get("doc_name"):
                doc["document_name"] = doc.get("doc_name")
            
            if not doc.get("document_no") and doc.get("doc_no"):
                doc["document_no"] = doc.get("doc_no")
            
            if not doc.get("approved_date") and doc.get("issue_date"):
                doc["approved_date"] = doc.get("issue_date")
            
            if not doc.get("note") and doc.get("notes"):
                doc["note"] = doc.get("notes")
            
            if not doc.get("document_name"):
                doc["document_name"] = "Untitled Document"
            
            if not doc.get("status"):
                doc["status"] = "Unknown"
            
            result.append(DrawingManualResponse(**doc))
        
        return result
    
    @staticmethod
    async def get_drawing_manual_by_id(doc_id: str, current_user: UserResponse) -> DrawingManualResponse:
        """Get drawing/manual by ID"""
        doc = await mongo_db.find_one(DrawingManualService.collection_name, {"id": doc_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Drawing/Manual not found")
        
        if not doc.get("document_name") and doc.get("doc_name"):
            doc["document_name"] = doc.get("doc_name")
        
        if not doc.get("document_no") and doc.get("doc_no"):
            doc["document_no"] = doc.get("doc_no")
        
        if not doc.get("approved_date") and doc.get("issue_date"):
            doc["approved_date"] = doc.get("issue_date")
        
        if not doc.get("note") and doc.get("notes"):
            doc["note"] = doc.get("notes")
        
        if not doc.get("document_name"):
            doc["document_name"] = "Untitled Document"
        
        if not doc.get("status"):
            doc["status"] = "Unknown"
        
        return DrawingManualResponse(**doc)
    
    @staticmethod
    async def create_drawing_manual(doc_data: DrawingManualCreate, current_user: UserResponse) -> DrawingManualResponse:
        """Create new drawing/manual"""
        doc_dict = doc_data.dict()
        doc_dict["id"] = str(uuid.uuid4())
        doc_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create(DrawingManualService.collection_name, doc_dict)
        
        logger.info(f"✅ Drawing/Manual created: {doc_dict['document_name']}")
        
        return DrawingManualResponse(**doc_dict)
    
    @staticmethod
    async def update_drawing_manual(doc_id: str, doc_data: DrawingManualUpdate, current_user: UserResponse) -> DrawingManualResponse:
        """Update drawing/manual"""
        doc = await mongo_db.find_one(DrawingManualService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Drawing/Manual not found")
        
        update_data = doc_data.dict(exclude_unset=True)
        
        if update_data:
            await mongo_db.update(DrawingManualService.collection_name, {"id": doc_id}, update_data)
        
        updated_doc = await mongo_db.find_one(DrawingManualService.collection_name, {"id": doc_id})
        
        if not updated_doc.get("document_name") and updated_doc.get("doc_name"):
            updated_doc["document_name"] = updated_doc.get("doc_name")
        
        logger.info(f"✅ Drawing/Manual updated: {doc_id}")
        
        return DrawingManualResponse(**updated_doc)
    
    @staticmethod
    async def delete_drawing_manual(
        doc_id: str, 
        current_user: UserResponse,
        background_tasks = None
    ) -> dict:
        """Delete drawing/manual and schedule Google Drive file deletion in background"""
        from fastapi import BackgroundTasks
        from app.utils.background_tasks import delete_file_background
        from app.services.gdrive_service import GDriveService
        from app.repositories.ship_repository import ShipRepository
        
        doc = await mongo_db.find_one(DrawingManualService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Drawing/Manual not found")
        
        # Extract file info before deleting from DB
        file_id = doc.get("file_id")
        summary_file_id = doc.get("summary_file_id")
        document_name = doc.get("document_name", "Unknown")
        
        # Delete from database immediately
        await mongo_db.delete(DrawingManualService.collection_name, {"id": doc_id})
        logger.info(f"✅ Drawing/Manual deleted from DB: {doc_id} ({document_name})")
        
        # Schedule Google Drive file deletions in background if files exist
        files_to_delete = []
        
        if file_id:
            files_to_delete.append(("original", file_id))
            logger.info(f"📋 Found original file to delete: {file_id}")
        
        if summary_file_id:
            files_to_delete.append(("summary", summary_file_id))
            logger.info(f"📋 Found summary file to delete: {summary_file_id}")
        
        if files_to_delete and background_tasks:
            # Get ship to find company_id
            ship_id = doc.get("ship_id")
            if ship_id:
                ship = await ShipRepository.find_by_id(ship_id)
                if ship:
                    company_id = ship.get("company")
                    if company_id:
                        for file_type, file_id_val in files_to_delete:
                            background_tasks.add_task(
                                delete_file_background,
                                file_id_val,
                                company_id,
                                "drawing_manual",
                                f"{document_name} ({file_type})",
                                GDriveService
                            )
                            logger.info(f"📋 Scheduled background deletion for {file_type} file: {file_id_val}")
                        
                        return {
                            "success": True,
                            "message": "Drawing/Manual deleted successfully. File deletion in progress...",
                            "document_id": doc_id,
                            "background_deletion": True,
                            "files_scheduled": len(files_to_delete)
                        }
        
        return {
            "success": True,
            "message": "Drawing/Manual deleted successfully",
            "document_id": doc_id,
            "background_deletion": False
        }
    
    @staticmethod
    async def bulk_delete_drawings_manuals(request: BulkDeleteDrawingManualRequest, current_user: UserResponse) -> dict:
        """Bulk delete drawings/manuals"""
        deleted_count = 0
        for doc_id in request.document_ids:
            try:
                await DrawingManualService.delete_drawing_manual(doc_id, current_user)
                deleted_count += 1
            except:
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} drawings/manuals")
        
        return {
            "message": f"Successfully deleted {deleted_count} drawings/manuals",
            "deleted_count": deleted_count
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
        Upload drawing/manual files to Google Drive
        
        Path: {ship_name}/Class & Flag Cert/Drawings & Manuals/
        - Original file and summary in SAME folder (unlike Test Report)
        
        Args:
            document_id: Drawing/Manual document ID
            file_content: Base64 encoded file content
            filename: Original filename
            content_type: File content type
            summary_text: Summary text (optional)
            current_user: Current user
        
        Returns:
            Upload result with file IDs
        """
        try:
            logger.info(f"📤 Starting file upload for drawing/manual: {document_id}")
            
            # Validate document exists
            document = await mongo_db.find_one(DrawingManualService.collection_name, {"id": document_id})
            if not document:
                raise HTTPException(status_code=404, detail="Drawing/Manual not found")
            
            # Get ship info
            ship_id = document.get("ship_id")
            if not ship_id:
                raise HTTPException(status_code=400, detail="Drawing/Manual has no ship_id")
            
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship")
            
            # Decode base64 file content
            import base64
            try:
                file_bytes = base64.b64decode(file_content)
                logger.info(f"✅ Decoded file content: {len(file_bytes)} bytes")
            except Exception as e:
                logger.error(f"Failed to decode base64 file content: {e}")
                raise HTTPException(status_code=400, detail="Invalid file content encoding")
            
            # Get company UUID
            company_uuid = current_user.company
            if not company_uuid:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Upload to Google Drive via GDriveService
            from app.services.gdrive_service import GDriveService
            
            # Upload original file to: ShipName/Class & Flag Cert/Drawings & Manuals/
            logger.info(f"📤 Uploading drawing/manual to: {ship_name}/Class & Flag Cert/Drawings & Manuals/{filename}")
            
            upload_result = await GDriveService.upload_file(
                file_content=file_bytes,
                filename=filename,
                content_type=content_type,
                folder_path=f"{ship_name}/Class & Flag Cert/Drawings & Manuals",
                company_id=company_uuid
            )
            
            if not upload_result.get('success'):
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload drawing/manual file: {upload_result.get('message', 'Unknown error')}"
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
                    summary_folder_path = f"{ship_name}/Class & Flag Cert/Drawings & Manuals"
                    
                    logger.info(f"📤 Uploading summary to: {summary_folder_path}/{summary_filename}")
                    
                    # Convert summary text to bytes
                    summary_bytes = summary_text.encode('utf-8')
                    
                    summary_upload = await GDriveService.upload_file(
                        file_content=summary_bytes,
                        filename=summary_filename,
                        content_type="text/plain",
                        folder_path=summary_folder_path,
                        company_id=company_uuid
                    )
                    
                    if summary_upload.get('success'):
                        summary_file_id = summary_upload.get('file_id')
                        logger.info(f"✅ Summary uploaded: {summary_file_id}")
                    else:
                        summary_error = summary_upload.get('message', 'Unknown error')
                        logger.warning(f"⚠️ Summary upload failed (non-critical): {summary_error}")
                        
                except Exception as summary_exc:
                    summary_error = str(summary_exc)
                    logger.warning(f"⚠️ Summary upload failed (non-critical): {summary_error}")
            
            # Update document record with file IDs
            update_data = {
                "updated_at": datetime.now(timezone.utc)
            }
            
            if original_file_id:
                update_data["file_id"] = original_file_id
            
            if summary_file_id:
                update_data["summary_file_id"] = summary_file_id
            
            await mongo_db.update(DrawingManualService.collection_name, {"id": document_id}, update_data)
            logger.info("✅ Drawing/Manual updated with file IDs")
            
            # Get updated document
            updated_document = await mongo_db.find_one(DrawingManualService.collection_name, {"id": document_id})
            
            logger.info("✅ Drawing/Manual files uploaded successfully")
            
            return {
                "success": True,
                "message": "Drawing/Manual files uploaded successfully",
                "document": DrawingManualResponse(**updated_document),
                "original_file_id": original_file_id,
                "summary_file_id": summary_file_id,
                "summary_error": summary_error
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading drawing/manual files: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def check_duplicate(ship_id: str, document_name: str, document_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if drawing/manual is duplicate"""
        filters = {
            "ship_id": ship_id,
            "document_name": document_name
        }
        
        if document_no:
            filters["document_no"] = document_no
        
        existing = await mongo_db.find_one(DrawingManualService.collection_name, filters)
        
        return {
            "is_duplicate": existing is not None,
            "existing_id": existing.get("id") if existing else None
        }

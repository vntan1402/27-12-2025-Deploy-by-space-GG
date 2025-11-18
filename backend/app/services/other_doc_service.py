import uuid
import logging
import base64
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from fastapi import HTTPException, BackgroundTasks

from app.models.other_doc import OtherDocumentCreate, OtherDocumentUpdate, OtherDocumentResponse, BulkDeleteOtherDocumentRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class OtherDocumentService:
    """Service for Other Document operations"""
    
    collection_name = "other_documents"
    
    @staticmethod
    async def get_other_documents(ship_id: Optional[str], current_user: UserResponse) -> List[OtherDocumentResponse]:
        """Get other documents with optional ship filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        
        docs = await mongo_db.find_all(OtherDocumentService.collection_name, filters)
        
        # Handle backward compatibility
        result = []
        for doc in docs:
            if not doc.get("document_name") and doc.get("doc_name"):
                doc["document_name"] = doc.get("doc_name")
            
            if not doc.get("date") and doc.get("issue_date"):
                doc["date"] = doc.get("issue_date")
            
            if not doc.get("note") and doc.get("notes"):
                doc["note"] = doc.get("notes")
            
            if not doc.get("document_name"):
                doc["document_name"] = "Untitled Document"
            
            if not doc.get("status"):
                doc["status"] = "Unknown"
            
            result.append(OtherDocumentResponse(**doc))
        
        return result
    
    @staticmethod
    async def get_other_document_by_id(doc_id: str, current_user: UserResponse) -> OtherDocumentResponse:
        """Get other document by ID"""
        doc = await mongo_db.find_one(OtherDocumentService.collection_name, {"id": doc_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Other Document not found")
        
        if not doc.get("document_name") and doc.get("doc_name"):
            doc["document_name"] = doc.get("doc_name")
        
        if not doc.get("date") and doc.get("issue_date"):
            doc["date"] = doc.get("issue_date")
        
        if not doc.get("note") and doc.get("notes"):
            doc["note"] = doc.get("notes")
        
        if not doc.get("document_name"):
            doc["document_name"] = "Untitled Document"
        
        if not doc.get("status"):
            doc["status"] = "Unknown"
        
        return OtherDocumentResponse(**doc)
    
    @staticmethod
    async def create_other_document(doc_data: OtherDocumentCreate, current_user: UserResponse) -> OtherDocumentResponse:
        """Create new other document"""
        doc_dict = doc_data.dict()
        doc_dict["id"] = str(uuid.uuid4())
        doc_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create(OtherDocumentService.collection_name, doc_dict)
        
        logger.info(f"✅ Other Document created: {doc_dict['document_name']}")
        
        return OtherDocumentResponse(**doc_dict)
    
    @staticmethod
    async def update_other_document(doc_id: str, doc_data: OtherDocumentUpdate, current_user: UserResponse) -> OtherDocumentResponse:
        """Update other document"""
        doc = await mongo_db.find_one(OtherDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Other Document not found")
        
        update_data = doc_data.dict(exclude_unset=True)
        
        if update_data:
            await mongo_db.update(OtherDocumentService.collection_name, {"id": doc_id}, update_data)
        
        updated_doc = await mongo_db.find_one(OtherDocumentService.collection_name, {"id": doc_id})
        
        if not updated_doc.get("document_name") and updated_doc.get("doc_name"):
            updated_doc["document_name"] = updated_doc.get("doc_name")
        
        logger.info(f"✅ Other Document updated: {doc_id}")
        
        return OtherDocumentResponse(**updated_doc)
    
    @staticmethod
    async def delete_other_document(doc_id: str, current_user: UserResponse) -> dict:
        """Delete other document"""
        doc = await mongo_db.find_one(OtherDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Other Document not found")
        
        await mongo_db.delete(OtherDocumentService.collection_name, {"id": doc_id})
        
        logger.info(f"✅ Other Document deleted: {doc_id}")
        
        return {"message": "Other Document deleted successfully"}
    
    @staticmethod
    async def bulk_delete_other_documents(request: BulkDeleteOtherDocumentRequest, current_user: UserResponse) -> dict:
        """Bulk delete other documents"""
        deleted_count = 0
        for doc_id in request.document_ids:
            try:
                await OtherDocumentService.delete_other_document(doc_id, current_user)
                deleted_count += 1
            except:
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} other documents")
        
        return {
            "message": f"Successfully deleted {deleted_count} other documents",
            "deleted_count": deleted_count
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, document_name: str, document_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if other document is duplicate"""
        filters = {
            "ship_id": ship_id,
            "document_name": document_name
        }
        
        if document_no:
            filters["document_no"] = document_no
        
        existing = await mongo_db.find_one(OtherDocumentService.collection_name, filters)
        
        return {
            "is_duplicate": existing is not None,
            "existing_id": existing.get("id") if existing else None
        }
    
    # ==================== UPLOAD METHODS ====================
    
    @staticmethod
    async def upload_single_file(
        file_content: bytes,
        filename: str,
        ship_id: str,
        document_name: str,
        date: Optional[str],
        status: str,
        note: Optional[str],
        current_user: UserResponse
    ) -> dict:
        """
        Upload single file + create record
        Path: ShipName > Class & Flag Cert > Other Documents > filename
        
        Returns:
            dict with document_id and file_id
        """
        try:
            logger.info(f"📤 Uploading single file: {filename} for ship: {ship_id}")
            
            # Get ship info
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship")
            
            # Get company UUID
            company_uuid = current_user.company
            if not company_uuid:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Validate file type
            allowed_extensions = ['.pdf', '.jpg', '.jpeg']
            file_extension = filename.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Only PDF and JPG files are supported."
                )
            
            # Upload to Google Drive
            from app.repositories.gdrive_config_repository import GDriveConfigRepository
            from app.utils.gdrive_helper import upload_file_to_ship_folder
            
            # Get GDrive config
            gdrive_config = await GDriveConfigRepository.get_by_company(company_uuid)
            if not gdrive_config:
                raise HTTPException(status_code=500, detail="Google Drive not configured for your company")
            
            # Upload file - Path: ShipName > Class & Flag Cert > Other Documents
            logger.info(f"📤 Uploading to: {ship_name}/Class & Flag Cert/Other Documents/{filename}")
            
            upload_result = await upload_file_to_ship_folder(
                gdrive_config=gdrive_config,
                file_content=file_content,
                filename=filename,
                ship_name=ship_name,
                category="Class & Flag Cert/Other Documents"
            )
            
            if not upload_result.get('success'):
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file: {upload_result.get('error', 'Unknown error')}"
                )
            
            file_id = upload_result.get('file_id')
            logger.info(f"✅ File uploaded with ID: {file_id}")
            
            # Create document record
            doc_dict = {
                "id": str(uuid.uuid4()),
                "ship_id": ship_id,
                "document_name": document_name,
                "date": date,
                "status": status or "Unknown",
                "note": note,
                "file_ids": [file_id],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await mongo_db.create(OtherDocumentService.collection_name, doc_dict)
            logger.info(f"✅ Other Document record created: {doc_dict['id']}")
            
            return {
                "success": True,
                "message": "File uploaded successfully",
                "document_id": doc_dict['id'],
                "file_id": file_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading single file: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def upload_file_only(
        file_content: bytes,
        filename: str,
        ship_id: str,
        current_user: UserResponse
    ) -> dict:
        """
        Upload file to GDrive WITHOUT creating a record
        Returns only file_id
        
        This is used for background uploads where record is already created
        """
        try:
            logger.info(f"📤 Uploading file-only: {filename} for ship: {ship_id}")
            
            # Get ship info
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship")
            
            # Get company UUID
            company_uuid = current_user.company
            if not company_uuid:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Upload to Google Drive (accept ALL file types)
            from app.repositories.gdrive_config_repository import GDriveConfigRepository
            from app.utils.gdrive_helper import upload_file_to_ship_folder
            
            # Get GDrive config
            gdrive_config = await GDriveConfigRepository.get_by_company(company_uuid)
            if not gdrive_config:
                raise HTTPException(status_code=500, detail="Google Drive not configured")
            
            # Upload file
            upload_result = await upload_file_to_ship_folder(
                gdrive_config=gdrive_config,
                file_content=file_content,
                filename=filename,
                ship_name=ship_name,
                category="Class & Flag Cert/Other Documents"
            )
            
            if not upload_result.get('success'):
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file: {upload_result.get('error', 'Unknown error')}"
                )
            
            file_id = upload_result.get('file_id')
            logger.info(f"✅ File uploaded (no record): {file_id}")
            
            return {
                "success": True,
                "message": "File uploaded successfully (no record created)",
                "file_id": file_id,
                "filename": filename
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading file-only: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def upload_folder(
        files: List[Tuple[bytes, str]],  # List of (file_content, filename) tuples
        ship_id: str,
        folder_name: str,
        date: Optional[str],
        status: str,
        note: Optional[str],
        current_user: UserResponse
    ) -> dict:
        """
        Upload folder with multiple files + create 1 record
        Path: ShipName > Class & Flag Cert > Other Documents > folder_name
        
        Returns:
            dict with document_id, folder_id, folder_link, file_ids
        """
        try:
            logger.info(f"📁 Uploading folder: {folder_name} with {len(files)} files for ship: {ship_id}")
            
            # Get ship info
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship")
            
            # Get company UUID
            company_uuid = current_user.company
            if not company_uuid:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Upload folder to Google Drive
            from app.repositories.gdrive_config_repository import GDriveConfigRepository
            from app.utils.gdrive_helper import upload_files_to_folder
            
            # Get GDrive config
            gdrive_config = await GDriveConfigRepository.get_by_company(company_uuid)
            if not gdrive_config:
                raise HTTPException(status_code=500, detail="Google Drive not configured")
            
            # Upload folder
            logger.info("📤 Creating subfolder and uploading files to Google Drive...")
            upload_result = await upload_files_to_folder(
                gdrive_config=gdrive_config,
                files=files,
                folder_name=folder_name,
                ship_name=ship_name,
                parent_category="Class & Flag Cert/Other Documents"
            )
            
            if not upload_result or not upload_result.get('success'):
                error_msg = upload_result.get('message', 'Unknown error') if upload_result else 'Upload failed'
                raise HTTPException(status_code=500, detail=f"Failed to upload folder: {error_msg}")
            
            folder_id = upload_result.get('folder_id')
            folder_link = upload_result.get('folder_link')
            file_ids = upload_result.get('file_ids', [])
            
            logger.info("✅ Folder uploaded to Google Drive")
            logger.info(f"   Folder ID: {folder_id}")
            logger.info(f"   Files uploaded: {len(file_ids)}/{len(files)}")
            
            # Create document record
            doc_dict = {
                "id": str(uuid.uuid4()),
                "ship_id": ship_id,
                "document_name": folder_name,
                "date": date,
                "status": status or "Unknown",
                "note": note,
                "file_ids": file_ids,
                "folder_id": folder_id,
                "folder_link": folder_link,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await mongo_db.create(OtherDocumentService.collection_name, doc_dict)
            logger.info(f"✅ Other Document folder record created: {doc_dict['id']}")
            
            return {
                "success": True,
                "message": f"Folder uploaded successfully: {len(file_ids)}/{len(files)} files",
                "document_id": doc_dict['id'],
                "folder_id": folder_id,
                "folder_link": folder_link,
                "file_ids": file_ids,
                "total_files": len(files),
                "successful_files": len(file_ids),
                "failed_files": upload_result.get('failed_files', [])
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading folder: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def upload_file_for_document(
        document_id: str,
        ship_id: str,
        file_content: bytes,
        filename: str,
        current_user: UserResponse
    ) -> dict:
        """
        Upload file for an existing document (background upload case)
        Updates the document's file_ids array
        
        Returns:
            dict with file_id and success status
        """
        try:
            logger.info(f"📤 Uploading file for existing document: {document_id}")
            
            # Validate document exists
            document = await mongo_db.find_one(OtherDocumentService.collection_name, {"id": document_id})
            if not document:
                raise HTTPException(status_code=404, detail="Other Document not found")
            
            # Get ship info
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship")
            
            # Get company UUID
            company_uuid = current_user.company
            if not company_uuid:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Upload to Google Drive
            from app.repositories.gdrive_config_repository import GDriveConfigRepository
            from app.utils.gdrive_helper import upload_file_to_ship_folder
            
            gdrive_config = await GDriveConfigRepository.get_by_company(company_uuid)
            if not gdrive_config:
                raise HTTPException(status_code=500, detail="Google Drive not configured")
            
            upload_result = await upload_file_to_ship_folder(
                gdrive_config=gdrive_config,
                file_content=file_content,
                filename=filename,
                ship_name=ship_name,
                category="Class & Flag Cert/Other Documents"
            )
            
            if not upload_result.get('success'):
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file: {upload_result.get('error', 'Unknown error')}"
                )
            
            file_id = upload_result.get('file_id')
            logger.info(f"✅ File uploaded: {file_id}")
            
            # Update document's file_ids
            current_file_ids = document.get("file_ids", [])
            current_file_ids.append(file_id)
            
            await mongo_db.update(
                OtherDocumentService.collection_name,
                {"id": document_id},
                {"file_ids": current_file_ids}
            )
            
            logger.info(f"✅ Updated document {document_id} with file_id: {file_id}")
            
            return {
                "success": True,
                "message": "File uploaded and document updated",
                "file_id": file_id,
                "filename": filename
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading file for document: {e}")
            raise HTTPException(status_code=500, detail=str(e))

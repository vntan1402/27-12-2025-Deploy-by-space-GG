import uuid
import logging
import asyncio
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from fastapi import HTTPException, BackgroundTasks

from app.models.other_audit_document import OtherAuditDocumentCreate, OtherAuditDocumentUpdate, OtherAuditDocumentResponse, BulkDeleteOtherAuditDocumentRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)


# Background task function for folder upload
async def upload_folder_background_task(
    document_id: str,
    files_info: List[Tuple[str, str]],  # List of (file_path, filename)
    folder_name: str,
    ship_name: str,
    parent_category: str,
    gdrive_config: dict,
    company_id: str
):
    """
    Background task to upload folder files after record is created.
    Updates the document with folder_id and file_ids when done.
    """
    try:
        logger.info(f"🔄 [Background] Starting folder upload for document: {document_id}")
        logger.info(f"   Folder: {folder_name}, Files: {len(files_info)}")
        
        # Import here to avoid circular imports
        from app.utils.gdrive_helper import upload_files_to_folder
        from app.repositories.gdrive_config_repository import GDriveConfigRepository
        
        # Get fresh GDrive config
        gdrive_config = await GDriveConfigRepository.get_by_company(company_id)
        if not gdrive_config:
            logger.error(f"❌ [Background] GDrive config not found for company: {company_id}")
            return
        
        # Prepare files data (read from temp storage if needed)
        # For now, we'll use the provided files_info
        # In production, files would be stored temporarily and read here
        
        # Upload folder
        upload_result = await upload_files_to_folder(
            gdrive_config=gdrive_config,
            files=files_info,
            folder_name=folder_name,
            ship_name=ship_name,
            parent_category=parent_category
        )
        
        if upload_result and upload_result.get('success'):
            folder_id = upload_result.get('folder_id')
            folder_link = upload_result.get('folder_link')
            file_ids = upload_result.get('file_ids', [])
            
            # Update document with upload results
            await mongo_db.update(
                "other_audit_documents",
                {"id": document_id},
                {
                    "folder_id": folder_id,
                    "folder_link": folder_link,
                    "file_ids": file_ids,
                    "upload_status": "completed",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.info(f"✅ [Background] Folder upload completed for document: {document_id}")
            logger.info(f"   Files uploaded: {len(file_ids)}/{len(files_info)}")
        else:
            error_msg = upload_result.get('message', 'Unknown error') if upload_result else 'Upload failed'
            logger.error(f"❌ [Background] Folder upload failed: {error_msg}")
            
            # Update document with error status
            await mongo_db.update(
                "other_audit_documents",
                {"id": document_id},
                {
                    "upload_status": "failed",
                    "upload_error": error_msg,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"❌ [Background] Error uploading folder: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Update document with error
        try:
            await mongo_db.update(
                "other_audit_documents",
                {"id": document_id},
                {
                    "upload_status": "failed",
                    "upload_error": str(e),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            )
        except:
            pass

class OtherAuditDocumentService:
    """Service for Other Audit Document operations"""
    
    collection_name = "other_audit_documents"
    
    @staticmethod
    def get_audit_log_service():
        """Get audit log service instance"""
        from app.services.crew_audit_log_service import CrewAuditLogService
        from app.repositories.crew_audit_log_repository import CrewAuditLogRepository
        return CrewAuditLogService(CrewAuditLogRepository(mongo_db.database))
    
    @staticmethod
    async def get_other_audit_documents(ship_id: Optional[str], current_user: UserResponse) -> List[OtherAuditDocumentResponse]:
        """Get other audit documents with optional ship filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        
        docs = await mongo_db.find_all(OtherAuditDocumentService.collection_name, filters)
        
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
                doc["status"] = "Valid"
            
            result.append(OtherAuditDocumentResponse(**doc))
        
        return result
    
    @staticmethod
    async def get_other_audit_document_by_id(doc_id: str, current_user: UserResponse) -> OtherAuditDocumentResponse:
        """Get other audit document by ID"""
        doc = await mongo_db.find_one(OtherAuditDocumentService.collection_name, {"id": doc_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Other Audit Document not found")
        
        # Backward compatibility
        if not doc.get("document_name") and doc.get("doc_name"):
            doc["document_name"] = doc.get("doc_name")
        
        if not doc.get("date") and doc.get("issue_date"):
            doc["date"] = doc.get("issue_date")
        
        if not doc.get("note") and doc.get("notes"):
            doc["note"] = doc.get("notes")
        
        if not doc.get("document_name"):
            doc["document_name"] = "Untitled Document"
        
        if not doc.get("status"):
            doc["status"] = "Valid"
        
        return OtherAuditDocumentResponse(**doc)
    
    @staticmethod
    async def create_other_audit_document(doc_data: OtherAuditDocumentCreate, current_user: UserResponse) -> OtherAuditDocumentResponse:
        """Create new other audit document"""
        doc_dict = doc_data.dict()
        doc_dict["id"] = str(uuid.uuid4())
        doc_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create(OtherAuditDocumentService.collection_name, doc_dict)
        
        # Log audit
        try:
            ship = await mongo_db.find_one("ships", {"id": doc_dict.get("ship_id")})
            ship_name = ship.get("name", "Unknown Ship") if ship else "Unknown Ship"
            
            audit_service = OtherAuditDocumentService.get_audit_log_service()
            user_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            await audit_service.log_document_create(
                ship_name=ship_name,
                doc_data=doc_dict,
                doc_type='other_audit_document',
                user=user_dict
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        logger.info(f"✅ Other Audit Document created: {doc_dict['document_name']}")
        
        return OtherAuditDocumentResponse(**doc_dict)
    
    @staticmethod
    async def update_other_audit_document(doc_id: str, doc_data: OtherAuditDocumentUpdate, current_user: UserResponse) -> OtherAuditDocumentResponse:
        """Update other audit document"""
        doc = await mongo_db.find_one(OtherAuditDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Other Audit Document not found")
        
        update_data = doc_data.dict(exclude_unset=True)
        
        if update_data:
            await mongo_db.update(OtherAuditDocumentService.collection_name, {"id": doc_id}, update_data)
        
        updated_doc = await mongo_db.find_one(OtherAuditDocumentService.collection_name, {"id": doc_id})
        
        if not updated_doc.get("document_name") and updated_doc.get("doc_name"):
            updated_doc["document_name"] = updated_doc.get("doc_name")
        
        logger.info(f"✅ Other Audit Document updated: {doc_id}")
        
        return OtherAuditDocumentResponse(**updated_doc)
    
    @staticmethod
    async def delete_other_audit_document(
        doc_id: str,
        current_user: UserResponse,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> dict:
        """Delete other audit document with background GDrive cleanup"""
        from app.utils.background_tasks import delete_file_background
        from app.services.gdrive_service import GDriveService
        from app.repositories.ship_repository import ShipRepository
        
        doc = await mongo_db.find_one(OtherAuditDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Other Audit Document not found")
        
        # Extract file info before deleting from DB
        file_ids = doc.get("file_ids", [])
        folder_id = doc.get("folder_id")
        document_name = doc.get("document_name", "Unknown")
        
        # Delete from database immediately
        await mongo_db.delete(OtherAuditDocumentService.collection_name, {"id": doc_id})
        logger.info(f"✅ Other Audit Document deleted from DB: {doc_id} ({document_name})")
        
        # Schedule Google Drive file deletions in background
        files_to_delete = []
        
        if file_ids:
            for idx, file_id in enumerate(file_ids):
                files_to_delete.append((f"file_{idx+1}", file_id))
            logger.info(f"📋 Found {len(file_ids)} audit files to delete")
        
        if folder_id:
            files_to_delete.append(("folder", folder_id))
            logger.info(f"📋 Found audit folder to delete: {folder_id}")
        
        if files_to_delete and background_tasks:
            ship_id = doc.get("ship_id")
            if ship_id:
                ship = await ShipRepository.find_by_id(ship_id)
                if ship:
                    company_id = ship.get("company")
                    if company_id:
                        for file_type, file_id in files_to_delete:
                            background_tasks.add_task(
                                delete_file_background,
                                file_id,
                                company_id,
                                "other_audit_document",
                                f"{document_name} ({file_type})",
                                GDriveService
                            )
                            logger.info(f"📋 Scheduled background deletion for audit {file_type}: {file_id}")
                        
                        return {
                            "success": True,
                            "message": "Other Audit Document deleted successfully. File deletion in progress...",
                            "document_id": doc_id,
                            "background_deletion": True,
                            "files_scheduled": len(files_to_delete)
                        }
        
        return {
            "success": True,
            "message": "Other Audit Document deleted successfully",
            "document_id": doc_id,
            "background_deletion": False
        }
    
    @staticmethod
    async def bulk_delete_other_audit_documents(
        request: BulkDeleteOtherAuditDocumentRequest,
        current_user: UserResponse,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> dict:
        """Bulk delete other audit documents with background GDrive cleanup"""
        deleted_count = 0
        files_scheduled = 0
        
        for doc_id in request.document_ids:
            try:
                result = await OtherAuditDocumentService.delete_other_audit_document(doc_id, current_user, background_tasks)
                deleted_count += 1
                
                if result.get('background_deletion'):
                    files_scheduled += result.get('files_scheduled', 0)
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to delete audit document {doc_id}: {e}")
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} audit documents, {files_scheduled} files scheduled for cleanup")
        
        return {
            "success": True,
            "message": f"Successfully deleted {deleted_count} audit documents. File cleanup in progress...",
            "deleted_count": deleted_count,
            "files_scheduled_for_deletion": files_scheduled,
            "background_deletion": files_scheduled > 0
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, document_name: str, current_user: UserResponse) -> dict:
        """Check if other audit document is duplicate"""
        filters = {
            "ship_id": ship_id,
            "document_name": document_name
        }
        
        existing = await mongo_db.find_one(OtherAuditDocumentService.collection_name, filters)
        
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
        Path: ShipName > ISM - ISPS - MLC > Other Audit Document > filename
        """
        try:
            logger.info(f"📤 Uploading single audit file: {filename} for ship: {ship_id}")
            
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
            from app.utils.gdrive_helper import upload_file_with_parent_category
            
            gdrive_config = await GDriveConfigRepository.get_by_company(company_uuid)
            if not gdrive_config:
                raise HTTPException(status_code=500, detail="Google Drive not configured")
            
            # Upload file - Path: ShipName > ISM - ISPS - MLC > Other Audit Document
            logger.info(f"📤 Uploading to: {ship_name}/ISM - ISPS - MLC/Other Audit Document/{filename}")
            
            upload_result = await upload_file_with_parent_category(
                gdrive_config=gdrive_config,
                file_content=file_content,
                filename=filename,
                ship_name=ship_name,
                parent_category="ISM - ISPS - MLC",
                category="Other Audit Document"
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
                "status": status or "Valid",
                "note": note,
                "file_ids": [file_id],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await mongo_db.create(OtherAuditDocumentService.collection_name, doc_dict)
            logger.info(f"✅ Other Audit Document record created: {doc_dict['id']}")
            
            return {
                "success": True,
                "message": "File uploaded successfully",
                "document_id": doc_dict['id'],
                "file_id": file_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading single audit file: {e}")
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
        """Upload file WITHOUT creating a record"""
        try:
            logger.info(f"📤 Uploading audit file-only: {filename} for ship: {ship_id}")
            
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship")
            company_uuid = current_user.company
            if not company_uuid:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            from app.repositories.gdrive_config_repository import GDriveConfigRepository
            from app.utils.gdrive_helper import upload_file_with_parent_category
            
            gdrive_config = await GDriveConfigRepository.get_by_company(company_uuid)
            if not gdrive_config:
                raise HTTPException(status_code=500, detail="Google Drive not configured")
            
            upload_result = await upload_file_with_parent_category(
                gdrive_config=gdrive_config,
                file_content=file_content,
                filename=filename,
                ship_name=ship_name,
                parent_category="ISM - ISPS - MLC",
                category="Other Audit Document"
            )
            
            if not upload_result.get('success'):
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file: {upload_result.get('error', 'Unknown error')}"
                )
            
            file_id = upload_result.get('file_id')
            logger.info(f"✅ Audit file uploaded (no record): {file_id}")
            
            return {
                "success": True,
                "message": "File uploaded successfully (no record created)",
                "file_id": file_id,
                "filename": filename
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading audit file-only: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def upload_folder(
        files: List[Tuple[bytes, str]],
        ship_id: str,
        folder_name: str,
        date: Optional[str],
        status: str,
        note: Optional[str],
        current_user: UserResponse
    ) -> dict:
        """Upload folder with multiple files + create 1 record"""
        try:
            logger.info(f"📁 Uploading audit folder: {folder_name} with {len(files)} files for ship: {ship_id}")
            
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship")
            company_uuid = current_user.company
            if not company_uuid:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            from app.repositories.gdrive_config_repository import GDriveConfigRepository
            from app.utils.gdrive_helper import upload_files_to_folder
            
            gdrive_config = await GDriveConfigRepository.get_by_company(company_uuid)
            if not gdrive_config:
                raise HTTPException(status_code=500, detail="Google Drive not configured")
            
            logger.info("📤 Creating subfolder and uploading files to Google Drive...")
            upload_result = await upload_files_to_folder(
                gdrive_config=gdrive_config,
                files=files,
                folder_name=folder_name,
                ship_name=ship_name,
                parent_category="ISM - ISPS - MLC/Other Audit Document"
            )
            
            if not upload_result or not upload_result.get('success'):
                error_msg = upload_result.get('message', 'Unknown error') if upload_result else 'Upload failed'
                raise HTTPException(status_code=500, detail=f"Failed to upload folder: {error_msg}")
            
            folder_id = upload_result.get('folder_id')
            folder_link = upload_result.get('folder_link')
            file_ids = upload_result.get('file_ids', [])
            
            logger.info("✅ Audit folder uploaded to Google Drive")
            logger.info(f"   Folder ID: {folder_id}")
            logger.info(f"   Files uploaded: {len(file_ids)}/{len(files)}")
            
            # Create document record
            doc_dict = {
                "id": str(uuid.uuid4()),
                "ship_id": ship_id,
                "document_name": folder_name,
                "date": date,
                "status": status or "Valid",
                "note": note,
                "file_ids": file_ids,
                "folder_id": folder_id,
                "folder_link": folder_link,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await mongo_db.create(OtherAuditDocumentService.collection_name, doc_dict)
            logger.info(f"✅ Other Audit Document folder record created: {doc_dict['id']}")
            
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
            logger.error(f"❌ Error uploading audit folder: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def upload_folder_streaming(
        files: List,  # List[UploadFile]
        ship_id: str,
        folder_name: str,
        date: Optional[str],
        status: str,
        note: Optional[str],
        current_user: UserResponse
    ) -> dict:
        """
        Upload folder with streaming approach (optimized for memory).
        Reads and uploads files ONE-BY-ONE to minimize RAM usage.
        """
        try:
            from fastapi import UploadFile
            
            total_files = len(files)
            logger.info(f"📁 Uploading audit folder (streaming): {folder_name} with {total_files} files")
            logger.info(f"   🚀 Memory optimization: Read → Upload → Clear (one file at a time)")
            
            # Get ship info
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship")
            company_uuid = current_user.company
            if not company_uuid:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Get GDrive config
            from app.repositories.gdrive_config_repository import GDriveConfigRepository
            gdrive_config = await GDriveConfigRepository.get_by_company(company_uuid)
            if not gdrive_config:
                raise HTTPException(status_code=500, detail="Google Drive not configured")
            
            # Upload files one by one
            from app.utils.gdrive_helper import upload_file_to_folder_streaming
            
            logger.info("📤 Starting streaming upload to Google Drive...")
            upload_result = await upload_file_to_folder_streaming(
                gdrive_config=gdrive_config,
                files=files,  # UploadFile objects
                folder_name=folder_name,
                ship_name=ship_name,
                parent_category="ISM - ISPS - MLC/Other Audit Document"
            )
            
            if not upload_result or not upload_result.get('success'):
                error_msg = upload_result.get('message', 'Unknown error') if upload_result else 'Upload failed'
                raise HTTPException(status_code=500, detail=f"Failed to upload folder: {error_msg}")
            
            folder_id = upload_result.get('folder_id')
            folder_link = upload_result.get('folder_link')
            file_ids = upload_result.get('file_ids', [])
            
            logger.info("✅ Streaming upload completed")
            logger.info(f"   Folder ID: {folder_id}")
            logger.info(f"   Files uploaded: {len(file_ids)}/{total_files}")
            
            # Create document record
            doc_dict = {
                "id": str(uuid.uuid4()),
                "ship_id": ship_id,
                "document_name": folder_name,
                "date": date,
                "status": status or "Valid",
                "note": note,
                "file_ids": file_ids,
                "folder_id": folder_id,
                "folder_link": folder_link,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await mongo_db.create(OtherAuditDocumentService.collection_name, doc_dict)
            logger.info(f"✅ Other Audit Document folder record created: {doc_dict['id']}")
            
            return {
                "success": True,
                "message": f"Folder uploaded successfully: {len(file_ids)}/{total_files} files",
                "document_id": doc_dict['id'],
                "folder_id": folder_id,
                "folder_link": folder_link,
                "file_ids": file_ids,
                "total_files": total_files,
                "successful_files": len(file_ids),
                "failed_files": upload_result.get('failed_files', [])
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading audit folder (streaming): {e}")
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
        """Upload file for existing document"""
        try:
            logger.info(f"📤 Uploading audit file for existing document: {document_id}")
            
            document = await mongo_db.find_one(OtherAuditDocumentService.collection_name, {"id": document_id})
            if not document:
                raise HTTPException(status_code=404, detail="Other Audit Document not found")
            
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship")
            company_uuid = current_user.company
            if not company_uuid:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            from app.repositories.gdrive_config_repository import GDriveConfigRepository
            from app.utils.gdrive_helper import upload_file_with_parent_category
            
            gdrive_config = await GDriveConfigRepository.get_by_company(company_uuid)
            if not gdrive_config:
                raise HTTPException(status_code=500, detail="Google Drive not configured")
            
            upload_result = await upload_file_with_parent_category(
                gdrive_config=gdrive_config,
                file_content=file_content,
                filename=filename,
                ship_name=ship_name,
                parent_category="ISM - ISPS - MLC",
                category="Other Audit Document"
            )
            
            if not upload_result.get('success'):
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file: {upload_result.get('error', 'Unknown error')}"
                )
            
            file_id = upload_result.get('file_id')
            logger.info(f"✅ Audit file uploaded: {file_id}")
            
            # Update document's file_ids
            current_file_ids = document.get("file_ids", [])
            current_file_ids.append(file_id)
            
            await mongo_db.update(
                OtherAuditDocumentService.collection_name,
                {"id": document_id},
                {"file_ids": current_file_ids}
            )
            
            logger.info(f"✅ Updated audit document {document_id} with file_id: {file_id}")
            
            return {
                "success": True,
                "message": "File uploaded and document updated",
                "file_id": file_id,
                "filename": filename
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading audit file for document: {e}")
            raise HTTPException(status_code=500, detail=str(e))

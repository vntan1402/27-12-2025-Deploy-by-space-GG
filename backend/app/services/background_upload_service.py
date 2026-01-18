"""
Background Upload Service
Handles background processing for folder uploads with progress tracking

NEW STRATEGY (v2):
- Frontend creates task first (with metadata only)
- Frontend uploads files one by one to a dedicated endpoint
- Backend tracks progress per file
- Works for any number of files without hitting request size limits
"""
import uuid
import logging
import asyncio
import base64
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException, UploadFile

from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)


class BackgroundUploadTaskService:
    """Service for managing background upload tasks"""
    
    COLLECTION = "background_upload_tasks"
    
    @staticmethod
    async def create_task(
        ship_id: str,
        folder_name: str,
        file_names: List[str],
        user_id: str,
        company_id: str,
        task_type: str = "folder_upload"
    ) -> str:
        """Create a new background upload task"""
        task_id = str(uuid.uuid4())
        
        task_doc = {
            "id": task_id,
            "user_id": user_id,
            "company_id": company_id,
            "ship_id": ship_id,
            "folder_name": folder_name,
            "task_type": task_type,
            "status": "pending",  # pending, processing, completed, failed
            "file_names": file_names,
            "total_files": len(file_names),
            "completed_files": 0,
            "failed_files": 0,
            "current_file": "",
            "results": [],  # List of {filename, success, file_id, error}
            "folder_id": None,
            "folder_link": None,
            "document_id": None,  # ID of created OtherDocument
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None
        }
        
        await mongo_db.database[BackgroundUploadTaskService.COLLECTION].insert_one(task_doc)
        logger.info(f"📝 Created background upload task {task_id} with {len(file_names)} files")
        
        return task_id
    
    @staticmethod
    async def create_task_v2(
        ship_id: str,
        folder_name: str,
        total_files: int,
        date: Optional[str],
        status: str,
        note: Optional[str],
        user_id: str,
        company_id: str,
        task_type: str = "folder_upload_v2"
    ) -> str:
        """Create a new background upload task (v2 - no file content)"""
        task_id = str(uuid.uuid4())
        
        task_doc = {
            "id": task_id,
            "user_id": user_id,
            "company_id": company_id,
            "ship_id": ship_id,
            "folder_name": folder_name,
            "task_type": task_type,
            "status": "pending",  # pending, processing, completed, failed
            "total_files": total_files,
            "completed_files": 0,
            "failed_files": 0,
            "current_file": "",
            "results": [],  # List of {filename, success, file_id, error}
            "folder_id": None,
            "folder_link": None,
            "document_id": None,
            # Extra metadata for creating document when complete
            "date": date,
            "doc_status": status,
            "note": note,
            "file_ids": [],  # Track all uploaded file IDs
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None
        }
        
        await mongo_db.database[BackgroundUploadTaskService.COLLECTION].insert_one(task_doc)
        logger.info(f"📝 Created background upload task v2: {task_id} for {total_files} files")
        
        return task_id
    
    @staticmethod
    async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status by ID"""
        task = await mongo_db.database[BackgroundUploadTaskService.COLLECTION].find_one({"id": task_id})
        return task
    
    @staticmethod
    async def update_task(task_id: str, updates: Dict[str, Any]):
        """Update task status"""
        updates["updated_at"] = datetime.utcnow()
        await mongo_db.database[BackgroundUploadTaskService.COLLECTION].update_one(
            {"id": task_id},
            {"$set": updates}
        )
    
    @staticmethod
    async def add_result(task_id: str, result: Dict[str, Any]):
        """Add an upload result to the task"""
        await mongo_db.database[BackgroundUploadTaskService.COLLECTION].update_one(
            {"id": task_id},
            {
                "$push": {"results": result},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    
    @staticmethod
    async def cleanup_old_tasks(hours: int = 24):
        """Remove tasks older than specified hours"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await mongo_db.database[BackgroundUploadTaskService.COLLECTION].delete_many(
            {"created_at": {"$lt": cutoff}}
        )
        if result.deleted_count > 0:
            logger.info(f"🧹 Cleaned up {result.deleted_count} old background upload tasks")


class BackgroundUploadService:
    """Service for background folder upload with progress tracking"""
    
    # ===== V2 API: Client-side sequential upload =====
    
    @staticmethod
    async def create_upload_task(
        ship_id: str,
        folder_name: str,
        total_files: int,
        date: Optional[str],
        status: str,
        note: Optional[str],
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        V2: Create upload task (metadata only, no files)
        Frontend will upload files one by one after task creation
        """
        if total_files <= 0:
            raise HTTPException(status_code=400, detail="total_files must be > 0")
        
        task_id = await BackgroundUploadTaskService.create_task_v2(
            ship_id=ship_id,
            folder_name=folder_name,
            total_files=total_files,
            date=date,
            status=status,
            note=note,
            user_id=current_user.id,
            company_id=current_user.company
        )
        
        # Set task status to processing immediately
        await BackgroundUploadTaskService.update_task(task_id, {"status": "processing"})
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Upload task created for {total_files} files",
            "total_files": total_files
        }
    
    @staticmethod
    async def upload_single_file_to_task(
        task_id: str,
        file_content: bytes,
        filename: str,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        V2: Upload a single file to an existing task
        Creates folder on first file, subsequent files go to same folder
        """
        from app.services.other_doc_service import OtherDocumentService
        
        # Get task
        task = await BackgroundUploadTaskService.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Verify user owns the task
        if task.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to upload to this task")
        
        # Check task status
        if task.get("status") not in ["pending", "processing"]:
            raise HTTPException(status_code=400, detail=f"Task already {task.get('status')}")
        
        ship_id = task.get("ship_id")
        folder_name = task.get("folder_name")
        
        # Update current file
        await BackgroundUploadTaskService.update_task(task_id, {
            "current_file": f"Uploading {filename}..."
        })
        
        try:
            # Get ship info
            ship = await mongo_db.database.ships.find_one({"id": ship_id})
            if not ship:
                raise Exception(f"Ship not found: {ship_id}")
            
            ship_name = ship.get("name", "Unknown")
            
            # Get GDrive config using repository
            from app.repositories.gdrive_config_repository import GDriveConfigRepository
            from uuid import UUID
            
            company_uuid = UUID(current_user.company) if current_user.company else None
            if not company_uuid:
                raise Exception("User has no company assigned")
            
            gdrive_config = await GDriveConfigRepository.get_by_company(company_uuid)
            if not gdrive_config:
                raise Exception("Google Drive not configured")
            
            script_url = gdrive_config.get("web_app_url") or gdrive_config.get("apps_script_url")
            parent_folder_id = gdrive_config.get("folder_id")
            
            if not script_url or not parent_folder_id:
                raise Exception("Google Drive configuration incomplete")
            
            # Determine content type
            if filename.lower().endswith('.pdf'):
                content_type = 'application/pdf'
            elif filename.lower().endswith(('.jpg', '.jpeg')):
                content_type = 'image/jpeg'
            elif filename.lower().endswith('.png'):
                content_type = 'image/png'
            else:
                content_type = 'application/octet-stream'
            
            # Prepare payload
            payload = {
                "action": "upload_file_with_folder_creation",
                "parent_folder_id": parent_folder_id,
                "ship_name": ship_name,
                "parent_category": "Class & Flag Cert/Other Documents",
                "category": folder_name,
                "filename": filename,
                "file_content": base64.b64encode(file_content).decode('utf-8'),
                "content_type": content_type
            }
            
            # Upload to Apps Script
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    script_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    result = await response.json()
            
            if result.get('success'):
                file_id = result.get('file_id')
                folder_id = result.get('folder_id')
                
                logger.info(f"✅ [{task_id}] Uploaded: {filename} -> file_id: {file_id}")
                
                # Add result and update counts
                await BackgroundUploadTaskService.add_result(task_id, {
                    'success': True,
                    'filename': filename,
                    'file_id': file_id,
                    'folder_id': folder_id
                })
                
                # Get current counts and update
                task = await BackgroundUploadTaskService.get_task(task_id)
                completed = task.get("completed_files", 0) + 1
                file_ids = task.get("file_ids", [])
                file_ids.append(file_id)
                
                updates = {
                    "completed_files": completed,
                    "file_ids": file_ids,
                    "current_file": ""
                }
                
                # Update folder_id if first file
                if not task.get("folder_id") and folder_id:
                    updates["folder_id"] = folder_id
                    updates["folder_link"] = f"https://drive.google.com/drive/folders/{folder_id}"
                
                # Check if all files completed
                total = task.get("total_files", 0)
                failed = task.get("failed_files", 0)
                
                if completed + failed >= total:
                    # All files processed - finalize task
                    updates["status"] = "completed" if failed == 0 else "completed_with_errors"
                    updates["completed_at"] = datetime.utcnow()
                    
                    # Create OtherDocument record
                    document_id = await BackgroundUploadService._create_document_for_task(task_id, task, updates)
                    if document_id:
                        updates["document_id"] = document_id
                
                await BackgroundUploadTaskService.update_task(task_id, updates)
                
                return {
                    "success": True,
                    "filename": filename,
                    "file_id": file_id,
                    "folder_id": folder_id,
                    "completed_files": completed,
                    "total_files": total
                }
            else:
                error_msg = result.get('message', 'Unknown error')
                logger.warning(f"⚠️ [{task_id}] Failed {filename}: {error_msg}")
                
                # Add failure result
                await BackgroundUploadTaskService.add_result(task_id, {
                    'success': False,
                    'filename': filename,
                    'error': error_msg
                })
                
                # Update failed count
                task = await BackgroundUploadTaskService.get_task(task_id)
                failed = task.get("failed_files", 0) + 1
                completed = task.get("completed_files", 0)
                total = task.get("total_files", 0)
                
                updates = {
                    "failed_files": failed,
                    "current_file": ""
                }
                
                # Check if all files processed
                if completed + failed >= total:
                    updates["status"] = "failed" if completed == 0 else "completed_with_errors"
                    updates["completed_at"] = datetime.utcnow()
                    
                    # Create document if any succeeded
                    if completed > 0:
                        document_id = await BackgroundUploadService._create_document_for_task(task_id, task, updates)
                        if document_id:
                            updates["document_id"] = document_id
                
                await BackgroundUploadTaskService.update_task(task_id, updates)
                
                return {
                    "success": False,
                    "filename": filename,
                    "error": error_msg,
                    "completed_files": completed,
                    "total_files": total
                }
                
        except Exception as e:
            logger.error(f"❌ [{task_id}] Error uploading {filename}: {e}")
            
            # Add failure result
            await BackgroundUploadTaskService.add_result(task_id, {
                'success': False,
                'filename': filename,
                'error': str(e)
            })
            
            # Update failed count
            task = await BackgroundUploadTaskService.get_task(task_id)
            failed = task.get("failed_files", 0) + 1
            completed = task.get("completed_files", 0)
            total = task.get("total_files", 0)
            
            updates = {
                "failed_files": failed,
                "current_file": ""
            }
            
            if completed + failed >= total:
                updates["status"] = "failed" if completed == 0 else "completed_with_errors"
                updates["completed_at"] = datetime.utcnow()
            
            await BackgroundUploadTaskService.update_task(task_id, updates)
            
            return {
                "success": False,
                "filename": filename,
                "error": str(e),
                "completed_files": completed,
                "total_files": total
            }
    
    @staticmethod
    async def _create_document_for_task(task_id: str, task: Dict, updates: Dict) -> Optional[str]:
        """Create OtherDocument record when task completes"""
        from app.models.other_doc import OtherDocumentCreate
        from app.services.other_doc_service import OtherDocumentService
        
        folder_id = updates.get("folder_id") or task.get("folder_id")
        file_ids = updates.get("file_ids") or task.get("file_ids", [])
        
        if not folder_id or not file_ids:
            logger.warning(f"[{task_id}] Cannot create document: no folder_id or file_ids")
            return None
        
        try:
            # Get user for creating document
            user_doc = await mongo_db.database.users.find_one({"id": task.get("user_id")})
            if not user_doc:
                logger.error(f"[{task_id}] User not found: {task.get('user_id')}")
                return None
            
            from app.models.user import UserResponse
            current_user = UserResponse(
                id=user_doc["id"],
                email=user_doc.get("email", ""),
                name=user_doc.get("name", ""),
                company=user_doc.get("company", ""),
                role=user_doc.get("role", "viewer"),
                language=user_doc.get("language", "en"),
                created_at=user_doc.get("created_at"),
                updated_at=user_doc.get("updated_at")
            )
            
            doc_data = OtherDocumentCreate(
                ship_id=task.get("ship_id"),
                folder_name=task.get("folder_name"),
                date=task.get("date"),
                status=task.get("doc_status", "Valid"),
                note=task.get("note")
            )
            
            # Create document record
            doc_result = await OtherDocumentService.create_other_document(doc_data, current_user)
            document_id = doc_result.id
            
            # Update with GDrive info
            await mongo_db.database.other_documents.update_one(
                {"id": document_id},
                {"$set": {
                    "google_drive_folder_id": folder_id,
                    "google_drive_folder_link": f"https://drive.google.com/drive/folders/{folder_id}",
                    "file_ids": file_ids,
                    "file_count": len(file_ids)
                }}
            )
            
            logger.info(f"✅ [{task_id}] Created OtherDocument: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"❌ [{task_id}] Failed to create OtherDocument: {e}")
            return None
    
    # ===== V1 API: Server-side background processing (for small uploads) =====
    
    @staticmethod
    async def start_folder_upload(
        files: List[UploadFile],
        ship_id: str,
        folder_name: str,
        date: Optional[str],
        status: str,
        note: Optional[str],
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        Start background folder upload process
        Returns task_id for polling status
        """
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Read all file contents first (before they get consumed)
        file_data = []
        file_names = []
        for f in files:
            content = await f.read()
            filename = f.filename.split('/')[-1] if '/' in f.filename else f.filename
            file_data.append({
                'content': content,
                'filename': filename,
                'content_type': f.content_type or 'application/octet-stream'
            })
            file_names.append(filename)
        
        # Create task
        task_id = await BackgroundUploadTaskService.create_task(
            ship_id=ship_id,
            folder_name=folder_name,
            file_names=file_names,
            user_id=current_user.id,
            company_id=current_user.company,
            task_type="folder_upload"
        )
        
        # Start background processing
        asyncio.create_task(
            BackgroundUploadService._process_folder_upload(
                task_id=task_id,
                file_data=file_data,
                ship_id=ship_id,
                folder_name=folder_name,
                date=date,
                status=status,
                note=note,
                current_user=current_user
            )
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Folder upload started for {len(files)} files",
            "total_files": len(files)
        }
    
    @staticmethod
    async def get_task_status(task_id: str) -> Dict[str, Any]:
        """Get status of a background upload task"""
        task = await BackgroundUploadTaskService.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "task_id": task["id"],
            "status": task["status"],
            "total_files": task["total_files"],
            "completed_files": task["completed_files"],
            "failed_files": task["failed_files"],
            "current_file": task.get("current_file", ""),
            "results": task.get("results", []),
            "folder_id": task.get("folder_id"),
            "folder_link": task.get("folder_link"),
            "document_id": task.get("document_id"),
            "created_at": task["created_at"].isoformat() if task.get("created_at") else None,
            "completed_at": task["completed_at"].isoformat() if task.get("completed_at") else None
        }
    
    @staticmethod
    async def _process_folder_upload(
        task_id: str,
        file_data: List[Dict],
        ship_id: str,
        folder_name: str,
        date: Optional[str],
        status: str,
        note: Optional[str],
        current_user: UserResponse
    ):
        """
        Background task to process folder upload
        Uploads first file to create folder, then remaining files in parallel
        """
        from app.services.other_doc_service import OtherDocumentService
        from app.db.mongodb import mongo_db
        
        logger.info(f"🚀 Starting background folder upload task {task_id} for {len(file_data)} files")
        
        # Update task status to processing
        await BackgroundUploadTaskService.update_task(task_id, {"status": "processing"})
        
        try:
            # Get ship info
            ship = await mongo_db.database.ships.find_one({"id": ship_id})
            if not ship:
                raise Exception(f"Ship not found: {ship_id}")
            
            ship_name = ship.get("name", "Unknown")
            
            # Get GDrive config using repository
            from app.repositories.gdrive_config_repository import GDriveConfigRepository
            from uuid import UUID
            
            company_uuid = UUID(current_user.company) if current_user.company else None
            if not company_uuid:
                raise Exception("User has no company assigned")
            
            gdrive_config = await GDriveConfigRepository.get_by_company(company_uuid)
            if not gdrive_config:
                raise Exception("Google Drive not configured")
            
            script_url = gdrive_config.get("web_app_url") or gdrive_config.get("apps_script_url")
            parent_folder_id = gdrive_config.get("folder_id")
            
            if not script_url or not parent_folder_id:
                raise Exception("Google Drive configuration incomplete")
            
            completed = 0
            failed = 0
            folder_id = None
            file_ids = []
            
            # Helper function to upload a single file
            async def upload_single_file(file_info: Dict, index: int, delay: float = 0) -> Dict:
                nonlocal folder_id
                
                try:
                    if delay > 0:
                        await asyncio.sleep(delay)
                    
                    filename = file_info['filename']
                    content = file_info['content']
                    
                    # Update current file
                    await BackgroundUploadTaskService.update_task(task_id, {
                        "current_file": f"Uploading {filename}..."
                    })
                    
                    # Determine content type
                    if filename.lower().endswith('.pdf'):
                        content_type = 'application/pdf'
                    elif filename.lower().endswith(('.jpg', '.jpeg')):
                        content_type = 'image/jpeg'
                    elif filename.lower().endswith('.png'):
                        content_type = 'image/png'
                    else:
                        content_type = file_info.get('content_type', 'application/octet-stream')
                    
                    # Prepare payload
                    payload = {
                        "action": "upload_file_with_folder_creation",
                        "parent_folder_id": parent_folder_id,
                        "ship_name": ship_name,
                        "parent_category": "Class & Flag Cert/Other Documents",
                        "category": folder_name,
                        "filename": filename,
                        "file_content": base64.b64encode(content).decode('utf-8'),
                        "content_type": content_type
                    }
                    
                    # Upload to Apps Script
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            script_url,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=300)
                        ) as response:
                            result = await response.json()
                    
                    if result.get('success'):
                        logger.info(f"✅ [{task_id}] Uploaded {index + 1}/{len(file_data)}: {filename}")
                        return {
                            'success': True,
                            'filename': filename,
                            'file_id': result.get('file_id'),
                            'folder_id': result.get('folder_id')
                        }
                    else:
                        logger.warning(f"⚠️ [{task_id}] Failed {filename}: {result.get('message')}")
                        return {
                            'success': False,
                            'filename': filename,
                            'error': result.get('message', 'Unknown error')
                        }
                        
                except Exception as e:
                    logger.error(f"❌ [{task_id}] Error uploading {file_info['filename']}: {e}")
                    return {
                        'success': False,
                        'filename': file_info['filename'],
                        'error': str(e)
                    }
            
            # STEP 1: Upload first file to create folder
            await BackgroundUploadTaskService.update_task(task_id, {
                "current_file": f"Creating folder and uploading {file_data[0]['filename']}..."
            })
            
            first_result = await upload_single_file(file_data[0], 0)
            
            # Add first result
            await BackgroundUploadTaskService.add_result(task_id, first_result)
            
            if first_result.get('success'):
                completed += 1
                folder_id = first_result.get('folder_id')
                file_ids.append(first_result.get('file_id'))
            else:
                failed += 1
            
            await BackgroundUploadTaskService.update_task(task_id, {
                "completed_files": completed,
                "failed_files": failed,
                "folder_id": folder_id,
                "folder_link": f"https://drive.google.com/drive/folders/{folder_id}" if folder_id else None
            })
            
            # STEP 2: Upload remaining files in parallel
            if len(file_data) > 1 and folder_id:
                logger.info(f"📁 [{task_id}] Folder created: {folder_id}, uploading remaining {len(file_data) - 1} files...")
                
                # Create tasks for remaining files with staggered delay
                remaining_tasks = []
                for idx, file_info in enumerate(file_data[1:], start=1):
                    delay = (idx - 1) * 1.0  # 1s staggered delay
                    remaining_tasks.append(upload_single_file(file_info, idx, delay))
                
                # Execute remaining uploads in parallel
                remaining_results = await asyncio.gather(*remaining_tasks)
                
                # Process results
                for result in remaining_results:
                    await BackgroundUploadTaskService.add_result(task_id, result)
                    
                    if result.get('success'):
                        completed += 1
                        file_ids.append(result.get('file_id'))
                    else:
                        failed += 1
                    
                    await BackgroundUploadTaskService.update_task(task_id, {
                        "completed_files": completed,
                        "failed_files": failed
                    })
            
            # STEP 3: Create OtherDocument record if any files uploaded successfully
            document_id = None
            if folder_id and file_ids:
                try:
                    from app.models.other_doc import OtherDocumentCreate
                    
                    doc_data = OtherDocumentCreate(
                        ship_id=ship_id,
                        folder_name=folder_name,
                        date=date,
                        status=status,
                        note=note
                    )
                    
                    # Create document record
                    doc_result = await OtherDocumentService.create_other_document(doc_data, current_user)
                    document_id = doc_result.id
                    
                    # Update with GDrive info
                    await mongo_db.database.other_documents.update_one(
                        {"id": document_id},
                        {"$set": {
                            "google_drive_folder_id": folder_id,
                            "google_drive_folder_link": f"https://drive.google.com/drive/folders/{folder_id}",
                            "file_ids": file_ids,
                            "file_count": len(file_ids)
                        }}
                    )
                    
                    logger.info(f"✅ [{task_id}] Created OtherDocument: {document_id}")
                    
                except Exception as e:
                    logger.error(f"❌ [{task_id}] Failed to create OtherDocument: {e}")
            
            # Mark task as completed
            final_status = "completed" if failed == 0 else ("failed" if completed == 0 else "completed_with_errors")
            
            await BackgroundUploadTaskService.update_task(task_id, {
                "status": final_status,
                "current_file": "",
                "document_id": document_id,
                "completed_at": datetime.utcnow()
            })
            
            logger.info(f"✅ [{task_id}] Folder upload completed: {completed} success, {failed} failed")
            
        except Exception as e:
            logger.error(f"❌ [{task_id}] Fatal error in folder upload: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            await BackgroundUploadTaskService.update_task(task_id, {
                "status": "failed",
                "current_file": "",
                "completed_at": datetime.utcnow()
            })
            await BackgroundUploadTaskService.add_result(task_id, {
                "success": False,
                "filename": "SYSTEM",
                "error": str(e)
            })

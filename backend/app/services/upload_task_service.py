"""
Upload Task Service
Manages background upload tasks for certificates and survey reports
"""
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4

from app.db.mongodb import mongo_db
from app.models.upload_task import (
    UploadTask, 
    FileTaskStatus, 
    TaskStatus, 
    ProcessingType,
    UploadTaskResponse
)
from app.models.user import UserResponse

logger = logging.getLogger(__name__)

# Constants
TEXT_LAYER_THRESHOLD = 400  # Minimum characters to use text layer path
COLLECTION_NAME = "upload_tasks"


class UploadTaskService:
    """Service for managing upload tasks"""
    
    @staticmethod
    async def create_task(
        task_type: str,
        ship_id: str,
        filenames: List[str],
        current_user: UserResponse
    ) -> str:
        """
        Create a new upload task
        
        Args:
            task_type: "certificate" or "survey_report"
            ship_id: Ship ID
            filenames: List of filenames to process
            current_user: Current user
            
        Returns:
            task_id: Unique task identifier
        """
        task_id = str(uuid4())
        
        # Create file status entries
        files = [
            FileTaskStatus(
                filename=filename,
                status=TaskStatus.PENDING,
                progress=0
            )
            for filename in filenames
        ]
        
        task = UploadTask(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            files=files,
            ship_id=ship_id,
            user_id=current_user.id,
            company_id=current_user.company,
            total_files=len(filenames),
            completed_files=0,
            failed_files=0
        )
        
        # Save to database
        await mongo_db.database[COLLECTION_NAME].insert_one(task.dict())
        
        logger.info(f"📋 Created upload task {task_id} with {len(filenames)} files")
        return task_id
    
    @staticmethod
    async def get_task(task_id: str) -> Optional[UploadTaskResponse]:
        """
        Get task status by ID
        
        Args:
            task_id: Task identifier
            
        Returns:
            UploadTaskResponse or None
        """
        task_doc = await mongo_db.database[COLLECTION_NAME].find_one(
            {"task_id": task_id},
            {"_id": 0}
        )
        
        if not task_doc:
            return None
        
        # Build response
        response = UploadTaskResponse(
            task_id=task_doc["task_id"],
            status=task_doc["status"],
            task_type=task_doc["task_type"],
            total_files=task_doc["total_files"],
            completed_files=task_doc["completed_files"],
            failed_files=task_doc["failed_files"],
            files=[FileTaskStatus(**f) for f in task_doc["files"]],
            created_at=task_doc["created_at"],
            updated_at=task_doc["updated_at"],
            completed_at=task_doc.get("completed_at")
        )
        
        # Add results/errors if completed
        if task_doc["status"] == TaskStatus.COMPLETED:
            results = []
            errors = []
            for f in task_doc["files"]:
                if f["status"] == TaskStatus.COMPLETED and f.get("result"):
                    results.append(f["result"])
                elif f["status"] == TaskStatus.FAILED:
                    errors.append({
                        "filename": f["filename"],
                        "error": f.get("error", "Unknown error")
                    })
            response.results = results
            response.errors = errors
        
        return response
    
    @staticmethod
    async def update_task_status(
        task_id: str,
        status: TaskStatus,
        completed_at: Optional[datetime] = None
    ):
        """
        Update overall task status
        """
        update_data = {
            "status": status.value if isinstance(status, TaskStatus) else status,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if completed_at:
            update_data["completed_at"] = completed_at
        
        await mongo_db.database[COLLECTION_NAME].update_one(
            {"task_id": task_id},
            {"$set": update_data}
        )
        
        logger.info(f"📋 Updated task {task_id} status to {status}")
    
    @staticmethod
    async def update_file_status(
        task_id: str,
        file_index: int,
        status: TaskStatus,
        progress: int = 0,
        processing_type: Optional[ProcessingType] = None,
        has_text_layer: Optional[bool] = None,
        text_char_count: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Update individual file status
        """
        update_data = {
            f"files.{file_index}.status": status.value if isinstance(status, TaskStatus) else status,
            f"files.{file_index}.progress": progress,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if processing_type:
            update_data[f"files.{file_index}.processing_type"] = (
                processing_type.value if isinstance(processing_type, ProcessingType) else processing_type
            )
        
        if has_text_layer is not None:
            update_data[f"files.{file_index}.has_text_layer"] = has_text_layer
        
        if text_char_count is not None:
            update_data[f"files.{file_index}.text_char_count"] = text_char_count
        
        if result:
            update_data[f"files.{file_index}.result"] = result
        
        if error:
            update_data[f"files.{file_index}.error"] = error
        
        if status == TaskStatus.PROCESSING:
            update_data[f"files.{file_index}.started_at"] = datetime.now(timezone.utc)
        
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            update_data[f"files.{file_index}.completed_at"] = datetime.now(timezone.utc)
        
        await mongo_db.database[COLLECTION_NAME].update_one(
            {"task_id": task_id},
            {"$set": update_data}
        )
    
    @staticmethod
    async def increment_completed(
        task_id: str,
        success: bool = True
    ):
        """
        Increment completed/failed file count and check if task is done
        """
        if success:
            inc_field = "completed_files"
        else:
            inc_field = "failed_files"
        
        # Increment counter
        result = await mongo_db.database[COLLECTION_NAME].find_one_and_update(
            {"task_id": task_id},
            {
                "$inc": {inc_field: 1},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            },
            return_document=True
        )
        
        if result:
            total = result["total_files"]
            completed = result["completed_files"]
            failed = result["failed_files"]
            
            # Check if all files are processed
            if completed + failed >= total:
                # Mark task as completed
                final_status = TaskStatus.COMPLETED if failed == 0 else TaskStatus.COMPLETED
                await UploadTaskService.update_task_status(
                    task_id,
                    final_status,
                    completed_at=datetime.now(timezone.utc)
                )
                logger.info(f"✅ Task {task_id} completed: {completed} success, {failed} failed")
    
    @staticmethod
    async def cleanup_old_tasks(days: int = 7):
        """
        Clean up old completed tasks
        """
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await mongo_db.database[COLLECTION_NAME].delete_many({
            "status": {"$in": [TaskStatus.COMPLETED, TaskStatus.FAILED]},
            "completed_at": {"$lt": cutoff}
        })
        
        if result.deleted_count > 0:
            logger.info(f"🧹 Cleaned up {result.deleted_count} old upload tasks")

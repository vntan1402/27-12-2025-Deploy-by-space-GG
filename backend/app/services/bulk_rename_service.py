"""
Bulk Auto Rename Service for Ship Certificates
Handles background processing of multiple certificate file renames
"""
import uuid
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException

from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)


class BulkRenameTaskService:
    """Service for managing bulk rename tasks"""
    
    COLLECTION = "bulk_rename_tasks"
    
    @staticmethod
    async def create_task(
        certificate_ids: List[str],
        user_id: str,
        company_id: str,
        task_type: str = "ship_certificate"
    ) -> str:
        """Create a new bulk rename task"""
        task_id = str(uuid.uuid4())
        
        task_doc = {
            "id": task_id,
            "user_id": user_id,
            "company_id": company_id,
            "task_type": task_type,
            "status": "pending",  # pending, processing, completed, failed
            "certificate_ids": certificate_ids,
            "total_files": len(certificate_ids),
            "completed_files": 0,
            "failed_files": 0,
            "current_file": "",
            "results": [],  # List of {cert_id, success, old_name, new_name, error}
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None
        }
        
        await mongo_db.database[BulkRenameTaskService.COLLECTION].insert_one(task_doc)
        logger.info(f"📝 Created bulk rename task {task_id} with {len(certificate_ids)} certificates")
        
        return task_id
    
    @staticmethod
    async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status by ID"""
        task = await mongo_db.database[BulkRenameTaskService.COLLECTION].find_one({"id": task_id})
        return task
    
    @staticmethod
    async def update_task(task_id: str, updates: Dict[str, Any]):
        """Update task status"""
        updates["updated_at"] = datetime.utcnow()
        await mongo_db.database[BulkRenameTaskService.COLLECTION].update_one(
            {"id": task_id},
            {"$set": updates}
        )
    
    @staticmethod
    async def add_result(task_id: str, result: Dict[str, Any]):
        """Add a rename result to the task"""
        await mongo_db.database[BulkRenameTaskService.COLLECTION].update_one(
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
        result = await mongo_db.database[BulkRenameTaskService.COLLECTION].delete_many(
            {"created_at": {"$lt": cutoff}}
        )
        if result.deleted_count > 0:
            logger.info(f"🧹 Cleaned up {result.deleted_count} old bulk rename tasks")


class BulkRenameService:
    """Service for bulk renaming certificate files in background"""
    
    @staticmethod
    async def start_bulk_rename(
        certificate_ids: List[str],
        current_user: UserResponse,
        task_type: str = "ship_certificate"
    ) -> Dict[str, Any]:
        """
        Start background bulk rename process
        Returns task_id for polling status
        """
        if not certificate_ids:
            raise HTTPException(status_code=400, detail="No certificate IDs provided")
        
        # Create task
        task_id = await BulkRenameTaskService.create_task(
            certificate_ids=certificate_ids,
            user_id=current_user.id,
            company_id=current_user.company,
            task_type=task_type
        )
        
        # Start background processing
        asyncio.create_task(
            BulkRenameService._process_bulk_rename(
                task_id=task_id,
                certificate_ids=certificate_ids,
                current_user=current_user,
                task_type=task_type
            )
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Bulk rename started for {len(certificate_ids)} certificates",
            "total_files": len(certificate_ids)
        }
    
    @staticmethod
    async def get_task_status(task_id: str) -> Dict[str, Any]:
        """Get status of a bulk rename task"""
        task = await BulkRenameTaskService.get_task(task_id)
        
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
            "created_at": task["created_at"].isoformat() if task.get("created_at") else None,
            "completed_at": task["completed_at"].isoformat() if task.get("completed_at") else None
        }
    
    @staticmethod
    async def _process_bulk_rename(
        task_id: str,
        certificate_ids: List[str],
        current_user: UserResponse,
        task_type: str
    ):
        """
        Background task to process bulk rename
        Processes files sequentially with 500ms delay
        """
        from app.services.certificate_service import CertificateService
        from app.services.audit_certificate_service import AuditCertificateService
        from app.services.company_cert_service import CompanyCertService
        
        logger.info(f"🚀 Starting background bulk rename task {task_id} for {len(certificate_ids)} certificates")
        
        # Update task status to processing
        await BulkRenameTaskService.update_task(task_id, {"status": "processing"})
        
        completed = 0
        failed = 0
        
        for i, cert_id in enumerate(certificate_ids):
            try:
                # Update current file being processed
                await BulkRenameTaskService.update_task(task_id, {
                    "current_file": f"Processing {i + 1}/{len(certificate_ids)}"
                })
                
                # Call appropriate rename service based on task type
                if task_type == "ship_certificate":
                    result = await CertificateService.auto_rename_certificate_file(cert_id, current_user)
                elif task_type == "audit_certificate":
                    result = await AuditCertificateService.auto_rename_file(cert_id, current_user)
                elif task_type == "company_certificate":
                    result = await CompanyCertService.auto_rename_file(cert_id, current_user)
                else:
                    result = await CertificateService.auto_rename_certificate_file(cert_id, current_user)
                
                # Add success result
                await BulkRenameTaskService.add_result(task_id, {
                    "cert_id": cert_id,
                    "success": True,
                    "old_name": result.get("old_name"),
                    "new_name": result.get("new_name"),
                    "summary_renamed": result.get("summary_renamed", False)
                })
                
                completed += 1
                await BulkRenameTaskService.update_task(task_id, {
                    "completed_files": completed
                })
                
                logger.info(f"✅ [{task_id}] Renamed {completed}/{len(certificate_ids)}: {result.get('new_name')}")
                
            except HTTPException as http_ex:
                failed += 1
                error_msg = http_ex.detail if hasattr(http_ex, 'detail') else str(http_ex)
                
                await BulkRenameTaskService.add_result(task_id, {
                    "cert_id": cert_id,
                    "success": False,
                    "error": error_msg
                })
                
                await BulkRenameTaskService.update_task(task_id, {
                    "failed_files": failed
                })
                
                logger.warning(f"⚠️ [{task_id}] Failed to rename cert {cert_id}: {error_msg}")
                
            except Exception as e:
                failed += 1
                
                await BulkRenameTaskService.add_result(task_id, {
                    "cert_id": cert_id,
                    "success": False,
                    "error": str(e)
                })
                
                await BulkRenameTaskService.update_task(task_id, {
                    "failed_files": failed
                })
                
                logger.error(f"❌ [{task_id}] Error renaming cert {cert_id}: {e}")
            
            # Delay between requests (500ms) to avoid rate limiting
            if i < len(certificate_ids) - 1:
                await asyncio.sleep(0.5)
        
        # Mark task as completed
        final_status = "completed" if failed == 0 else ("failed" if completed == 0 else "completed_with_errors")
        
        await BulkRenameTaskService.update_task(task_id, {
            "status": final_status,
            "current_file": "",
            "completed_at": datetime.utcnow()
        })
        
        logger.info(f"✅ [{task_id}] Bulk rename completed: {completed} success, {failed} failed")

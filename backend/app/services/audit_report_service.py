import uuid
import logging
import base64
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, BackgroundTasks

from app.models.audit_report import AuditReportCreate, AuditReportUpdate, AuditReportResponse, BulkDeleteAuditReportRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class AuditReportService:
    """Service for Audit Report operations (ISM/ISPS/MLC)"""
    
    collection_name = "audit_reports"
    
    @staticmethod
    async def get_audit_reports(ship_id: Optional[str], audit_type: Optional[str], current_user: UserResponse) -> List[AuditReportResponse]:
        """Get audit reports with optional ship and type filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        if audit_type:
            filters["audit_type"] = audit_type
        
        reports = await mongo_db.find_all(AuditReportService.collection_name, filters)
        
        # Handle backward compatibility
        result = []
        for report in reports:
            # Map old field names
            if not report.get("audit_report_name") and report.get("doc_name"):
                report["audit_report_name"] = report.get("doc_name")
            
            if not report.get("audit_report_no") and report.get("doc_no"):
                report["audit_report_no"] = report.get("doc_no")
            
            if not report.get("audit_date") and report.get("issue_date"):
                report["audit_date"] = report.get("issue_date")
            
            if not report.get("note") and report.get("notes"):
                report["note"] = report.get("notes")
            
            if not report.get("audit_report_name"):
                report["audit_report_name"] = "Untitled Audit Report"
            
            if not report.get("status"):
                report["status"] = "Valid"
            
            result.append(AuditReportResponse(**report))
        
        return result
    
    @staticmethod
    async def get_audit_report_by_id(report_id: str, current_user: UserResponse) -> AuditReportResponse:
        """Get audit report by ID"""
        report = await mongo_db.find_one(AuditReportService.collection_name, {"id": report_id})
        
        if not report:
            raise HTTPException(status_code=404, detail="Audit Report not found")
        
        # Backward compatibility
        if not report.get("audit_report_name") and report.get("doc_name"):
            report["audit_report_name"] = report.get("doc_name")
        
        if not report.get("audit_report_no") and report.get("doc_no"):
            report["audit_report_no"] = report.get("doc_no")
        
        if not report.get("audit_date") and report.get("issue_date"):
            report["audit_date"] = report.get("issue_date")
        
        if not report.get("note") and report.get("notes"):
            report["note"] = report.get("notes")
        
        if not report.get("audit_report_name"):
            report["audit_report_name"] = "Untitled Audit Report"
        
        if not report.get("status"):
            report["status"] = "Valid"
        
        return AuditReportResponse(**report)
    
    @staticmethod
    async def create_audit_report(report_data: AuditReportCreate, current_user: UserResponse) -> AuditReportResponse:
        """Create new audit report"""
        report_dict = report_data.dict()
        report_dict["id"] = str(uuid.uuid4())
        report_dict["created_at"] = datetime.now(timezone.utc)
        
        # Normalize issued_by to abbreviation
        if report_dict.get("issued_by"):
            from app.utils.issued_by_abbreviation import normalize_issued_by
            try:
                original_issued_by = report_dict["issued_by"]
                normalized_issued_by = normalize_issued_by(original_issued_by)
                report_dict["issued_by"] = normalized_issued_by
                if normalized_issued_by != original_issued_by:
                    logger.info(f"✅ Normalized Issued By: '{original_issued_by}' → '{normalized_issued_by}'")
            except Exception as e:
                logger.warning(f"⚠️ Could not normalize issued_by: {e}")
        
        await mongo_db.create(AuditReportService.collection_name, report_dict)
        
        logger.info(f"✅ Audit Report created: {report_dict['audit_report_name']} ({report_data.audit_type})")
        
        return AuditReportResponse(**report_dict)
    
    @staticmethod
    async def update_audit_report(report_id: str, report_data: AuditReportUpdate, current_user: UserResponse) -> AuditReportResponse:
        """Update audit report"""
        report = await mongo_db.find_one(AuditReportService.collection_name, {"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Audit Report not found")
        
        update_data = report_data.dict(exclude_unset=True)
        
        # Normalize issued_by to abbreviation if it's being updated
        if update_data.get("issued_by"):
            from app.utils.issued_by_abbreviation import normalize_issued_by
            try:
                original_issued_by = update_data["issued_by"]
                normalized_issued_by = normalize_issued_by(original_issued_by)
                update_data["issued_by"] = normalized_issued_by
                if normalized_issued_by != original_issued_by:
                    logger.info(f"✅ Normalized Issued By: '{original_issued_by}' → '{normalized_issued_by}'")
            except Exception as e:
                logger.warning(f"⚠️ Could not normalize issued_by: {e}")
        
        if update_data:
            await mongo_db.update(AuditReportService.collection_name, {"id": report_id}, update_data)
        
        updated_report = await mongo_db.find_one(AuditReportService.collection_name, {"id": report_id})
        
        if not updated_report.get("audit_report_name") and updated_report.get("doc_name"):
            updated_report["audit_report_name"] = updated_report.get("doc_name")
        
        logger.info(f"✅ Audit Report updated: {report_id}")
        
        return AuditReportResponse(**updated_report)
    
    @staticmethod
    async def delete_audit_report(
        report_id: str,
        background_tasks: BackgroundTasks,
        current_user: UserResponse
    ) -> dict:
        """
        Delete audit report with background GDrive cleanup
        
        Process:
        1. Get report and verify access
        2. Delete from database immediately
        3. Schedule background GDrive file deletion (if file IDs exist)
        
        Based on Approval Document pattern
        """
        from app.utils.background_tasks import delete_file_background
        from app.services.gdrive_service import GDriveService
        
        # Get report
        report = await mongo_db.find_one(AuditReportService.collection_name, {"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Audit Report not found")
        
        # Verify company access
        company_id = current_user.company
        ship_id = report.get("ship_id")
        if ship_id:
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if ship and ship.get("company") != company_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Extract file info before deleting from DB
        audit_report_file_id = report.get("audit_report_file_id")
        audit_report_summary_file_id = report.get("audit_report_summary_file_id")
        report_name = report.get("audit_report_name", "Unknown")
        
        # Delete from database immediately
        await mongo_db.delete(AuditReportService.collection_name, {"id": report_id})
        logger.info(f"✅ Audit Report deleted from DB: {report_id} ({report_name})")
        
        # Schedule background GDrive deletion
        files_scheduled = 0
        background_deletion = False
        
        if background_tasks and company_id:
            files_to_delete = []
            
            if audit_report_file_id:
                files_to_delete.append(("original", audit_report_file_id))
                logger.info(f"📋 Found original file to delete: {audit_report_file_id}")
            
            if audit_report_summary_file_id:
                files_to_delete.append(("summary", audit_report_summary_file_id))
                logger.info(f"📋 Found summary file to delete: {audit_report_summary_file_id}")
            
            if files_to_delete:
                for file_type, file_id_val in files_to_delete:
                    background_tasks.add_task(
                        delete_file_background,
                        file_id_val,
                        company_id,
                        "audit_report",
                        f"{report_name} ({file_type})",
                        GDriveService
                    )
                    logger.info(f"📋 Scheduled background deletion for {file_type} file: {file_id_val}")
                    files_scheduled += 1
                
                background_deletion = True
        
        message = "Audit Report deleted successfully"
        if background_deletion:
            message += f". File deletion in progress ({files_scheduled} file(s))..."
        
        return {
            "success": True,
            "message": message,
            "report_id": report_id,
            "background_deletion": background_deletion,
            "files_scheduled": files_scheduled
        }
    
    @staticmethod
    async def bulk_delete_audit_reports(
        request: BulkDeleteAuditReportRequest,
        background_tasks: BackgroundTasks,
        current_user: UserResponse
    ) -> dict:
        """
        Bulk delete audit reports with background GDrive cleanup
        Calls delete_audit_report for each report
        """
        deleted_count = 0
        files_scheduled = 0
        
        for report_id in request.document_ids:
            try:
                result = await AuditReportService.delete_audit_report(
                    report_id,
                    background_tasks,
                    current_user
                )
                deleted_count += 1
                files_scheduled += result.get("files_scheduled", 0)
            except Exception as e:
                logger.error(f"Failed to delete audit report {report_id}: {e}")
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} audit reports, scheduled {files_scheduled} file deletions")
        
        return {
            "success": True,
            "message": f"Successfully deleted {deleted_count} audit reports",
            "deleted_count": deleted_count,
            "files_scheduled": files_scheduled
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, audit_report_name: str, audit_report_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if audit report is duplicate"""
        filters = {
            "ship_id": ship_id,
            "audit_report_name": audit_report_name
        }
        
        if audit_report_no:
            filters["audit_report_no"] = audit_report_no
        
        existing = await mongo_db.find_one(AuditReportService.collection_name, filters)
        
        return {
            "is_duplicate": existing is not None,
            "existing_id": existing.get("id") if existing else None
        }

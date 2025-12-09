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
    def get_audit_log_service():
        """Get audit log service instance"""
        from app.services.crew_audit_log_service import CrewAuditLogService
        from app.repositories.crew_audit_log_repository import CrewAuditLogRepository
        return CrewAuditLogService(CrewAuditLogRepository(mongo_db.database))
    
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
    
    @staticmethod
    async def upload_files(
        report_id: str,
        file_content: str,
        filename: str,
        content_type: str,
        summary_text: Optional[str],
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        Upload audit report files to Google Drive
        
        Process:
        1. Validate report exists
        2. Verify company access
        3. Decode base64 file content
        4. Upload original file to: ShipName/ISM - ISPS - MLC/Audit Report/
        5. Upload summary file (if summary_text provided)
        6. Update report with file IDs
        
        Based on Backend V1 upload_audit_report_files()
        Location: /app/backend-v1/server.py lines 10322-10472
        
        Args:
            report_id: Audit report ID
            file_content: Base64 encoded file
            filename: Original filename
            content_type: MIME type
            summary_text: Optional summary text
            current_user: Current user
            
        Returns:
            dict: Upload result with file IDs
        """
        try:
            logger.info(f"📤 Starting file upload for audit report: {report_id}")
            
            # Validate report exists
            report = await mongo_db.find_one(AuditReportService.collection_name, {"id": report_id})
            if not report:
                raise HTTPException(status_code=404, detail="Audit report not found")
            
            # Get company and ship info
            company_id = current_user.company
            if not company_id:
                raise HTTPException(status_code=404, detail="Company not found")
            
            ship_id = report.get("ship_id")
            if not ship_id:
                raise HTTPException(status_code=400, detail="Audit report has no ship_id")
            
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
            try:
                file_bytes = base64.b64decode(file_content)
                logger.info(f"✅ Decoded file content: {len(file_bytes)} bytes")
            except Exception as e:
                logger.error(f"Failed to decode base64 file content: {e}")
                raise HTTPException(status_code=400, detail="Invalid file content encoding")
            
            logger.info(f"📄 Processing file: {filename} ({len(file_bytes)} bytes)")
            
            # Upload files to Google Drive
            from app.services.gdrive_service import GDriveService
            
            logger.info("📤 Uploading audit report files to Drive...")
            logger.info(f"📄 Target path: {ship_name}/ISM - ISPS - MLC/Audit Report/{filename}")
            
            # Upload original file to: ShipName/ISM - ISPS - MLC/Audit Report/
            # NOTE: Folder name uses SPACES, not hyphens
            upload_result = await GDriveService.upload_file(
                file_content=file_bytes,
                filename=filename,
                content_type=content_type,
                folder_path=f"{ship_name}/ISM - ISPS - MLC/Audit Report",
                company_id=company_id
            )
            
            if not upload_result.get('success'):
                logger.error(f"❌ File upload failed: {upload_result.get('message')}")
                raise HTTPException(
                    status_code=500,
                    detail=f"File upload failed: {upload_result.get('message', 'Unknown error')}"
                )
            
            audit_report_file_id = upload_result.get('file_id')
            logger.info(f"✅ Original file uploaded: {audit_report_file_id}")
            
            # Upload summary file if provided (to SAME folder)
            audit_report_summary_file_id = None
            summary_error = None
            
            if summary_text and summary_text.strip():
                try:
                    # Create summary filename
                    base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                    summary_filename = f"{base_name}_Summary.txt"
                    
                    logger.info(f"📋 Uploading summary file: {summary_filename} ({len(summary_text)} chars)")
                    
                    # Convert summary text to bytes
                    summary_bytes = summary_text.encode('utf-8')
                    
                    summary_result = await GDriveService.upload_file(
                        file_content=summary_bytes,
                        filename=summary_filename,
                        content_type="text/plain",
                        folder_path=f"{ship_name}/ISM - ISPS - MLC/Audit Report",
                        company_id=company_id
                    )
                    
                    if summary_result.get('success'):
                        audit_report_summary_file_id = summary_result.get('file_id')
                        if audit_report_summary_file_id:
                            logger.info(f"✅ Summary file uploaded successfully: {audit_report_summary_file_id}")
                        else:
                            logger.error(f"❌ CRITICAL: summary_result success=True but file_id is None!")
                            logger.error(f"   GDrive response: {summary_result}")
                            summary_error = "Summary upload returned success but no file_id"
                    else:
                        summary_error = f"Summary upload failed: {summary_result.get('message')}"
                        logger.warning(f"⚠️ {summary_error}")
                        logger.warning(f"   GDrive response: {summary_result}")
                        logger.warning(f"   Report will be created without summary file icon")
                        
                except Exception as summary_exc:
                    summary_error = f"Summary upload error: {str(summary_exc)}"
                    logger.error(f"❌ {summary_error}")
                    logger.error(f"   Report will be created without summary file icon")
            else:
                logger.warning(f"⚠️ No summary text provided for report {report_id}")
                logger.warning(f"   Summary file will not be uploaded - icon will not appear")
            
            # Update database with file IDs
            update_data = {
                "audit_report_file_id": audit_report_file_id,
                "updated_at": datetime.now(timezone.utc)
            }
            
            if audit_report_summary_file_id:
                update_data["audit_report_summary_file_id"] = audit_report_summary_file_id
                logger.info(f"✅ Both files will be saved: main={audit_report_file_id[:20]}..., summary={audit_report_summary_file_id[:20]}...")
            else:
                logger.warning(f"⚠️ ONLY main file will be saved: {audit_report_file_id[:20]}... (NO SUMMARY FILE ID)")
                logger.warning(f"   Reason: summary_file_id is None - summary upload may have failed")
            
            await mongo_db.update(AuditReportService.collection_name, {"id": report_id}, update_data)
            
            logger.info(f"✅ Database updated for audit report: {report_id}")
            
            result = {
                "success": True,
                "file_id": audit_report_file_id,
                "summary_file_id": audit_report_summary_file_id,
                "message": "Files uploaded successfully"
            }
            
            if summary_error:
                result["summary_warning"] = summary_error
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading audit report files: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to upload files: {str(e)}")

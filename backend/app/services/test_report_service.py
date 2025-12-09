import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, BackgroundTasks

from app.models.test_report import TestReportCreate, TestReportUpdate, TestReportResponse, BulkDeleteTestReportRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class TestReportService:
    """Service for Test Report operations"""
    
    collection_name = "test_reports"
    
    @staticmethod
    def get_audit_log_service():
        """Get audit log service instance"""
        from app.services.crew_audit_log_service import CrewAuditLogService
        from app.repositories.crew_audit_log_repository import CrewAuditLogRepository
        from app.db.mongodb import mongo_db
        return CrewAuditLogService(CrewAuditLogRepository(mongo_db.database))
    
    @staticmethod
    async def get_test_reports(ship_id: Optional[str], current_user: UserResponse) -> List[TestReportResponse]:
        """Get test reports with optional ship filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        
        reports = await mongo_db.find_all(TestReportService.collection_name, filters)
        
        # Handle backward compatibility with old data
        result = []
        for report in reports:
            # Map old field names if present
            if not report.get("test_report_name") and report.get("doc_name"):
                report["test_report_name"] = report.get("doc_name")
            
            if not report.get("test_report_no") and report.get("doc_no"):
                report["test_report_no"] = report.get("doc_no")
            
            # Map issue_date to issued_date for backward compatibility
            if not report.get("issued_date") and report.get("issue_date"):
                report["issued_date"] = report.get("issue_date")
            
            # Map notes to notes for backward compatibility
            if not report.get("notes") and report.get("note"):
                report["notes"] = report.get("note")
            
            # Map notes → note for frontend (frontend expects 'note' field)
            if report.get("notes") and not report.get("note"):
                report["note"] = report.get("notes")
            
            # Set defaults if still missing
            if not report.get("test_report_name"):
                report["test_report_name"] = "Untitled Test Report"
            
            if not report.get("status"):
                report["status"] = "Valid"
            
            result.append(TestReportResponse(**report))
        
        return result
    
    @staticmethod
    async def get_test_report_by_id(report_id: str, current_user: UserResponse) -> TestReportResponse:
        """Get test report by ID"""
        report = await mongo_db.find_one(TestReportService.collection_name, {"id": report_id})
        
        if not report:
            raise HTTPException(status_code=404, detail="Test Report not found")
        
        # Handle backward compatibility
        if not report.get("test_report_name") and report.get("doc_name"):
            report["test_report_name"] = report.get("doc_name")
        
        if not report.get("test_report_no") and report.get("doc_no"):
            report["test_report_no"] = report.get("doc_no")
        
        # Map issue_date to issued_date for backward compatibility
        if not report.get("issued_date") and report.get("issue_date"):
            report["issued_date"] = report.get("issue_date")
        
        # Map notes to notes for backward compatibility
        if not report.get("notes") and report.get("note"):
            report["notes"] = report.get("note")
        
        # Map notes → note for frontend (frontend expects 'note' field)
        if report.get("notes") and not report.get("note"):
            report["note"] = report.get("notes")
        
        if not report.get("test_report_name"):
            report["test_report_name"] = "Untitled Test Report"
        
        if not report.get("status"):
            report["status"] = "Valid"
        
        return TestReportResponse(**report)
    
    @staticmethod
    async def create_test_report(report_data: TestReportCreate, current_user: UserResponse) -> TestReportResponse:
        """Create new test report"""
        report_dict = report_data.dict()
        report_dict["id"] = str(uuid.uuid4())
        report_dict["created_at"] = datetime.now(timezone.utc)
        
        # Handle note/notes field - frontend sends 'note', backend stores 'notes'
        if "note" in report_dict and report_dict["note"] is not None:
            report_dict["notes"] = report_dict.pop("note")
            logger.debug("Mapped 'note' to 'notes' field")
        
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
        
        # Calculate valid_date if not provided but test_report_name and issued_date are available
        if (not report_dict.get("valid_date") and 
            report_dict.get("test_report_name") and 
            report_dict.get("issued_date") and 
            report_dict.get("ship_id")):
            
            try:
                from app.utils.test_report_valid_date_calculator import calculate_valid_date
                
                calculated_valid_date = await calculate_valid_date(
                    test_report_name=report_dict["test_report_name"],
                    issued_date=report_dict["issued_date"],
                    ship_id=report_dict["ship_id"],
                    mongo_db=mongo_db
                )
                
                if calculated_valid_date:
                    report_dict["valid_date"] = f"{calculated_valid_date}T00:00:00.000Z"
                    logger.info(f"✅ Auto-calculated Valid Date: {calculated_valid_date}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not auto-calculate valid_date: {e}")
        
        await mongo_db.create(TestReportService.collection_name, report_dict)
        
        # Log audit
        try:
            ship = await mongo_db.find_one("ships", {"id": report_dict.get("ship_id")})
            ship_name = ship.get("name", "Unknown Ship") if ship else "Unknown Ship"
            
            audit_service = TestReportService.get_audit_log_service()
            user_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            await audit_service.log_document_create(
                ship_name=ship_name,
                doc_data=report_dict,
                doc_type='test_report',
                user=user_dict
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        # Map notes → note for frontend response (frontend expects 'note' field)
        if report_dict.get("notes") and not report_dict.get("note"):
            report_dict["note"] = report_dict.get("notes")
        
        logger.info(f"✅ Test Report created: {report_dict['test_report_name']}")
        
        return TestReportResponse(**report_dict)
    
    @staticmethod
    async def update_test_report(report_id: str, report_data: TestReportUpdate, current_user: UserResponse) -> TestReportResponse:
        """Update test report"""
        report = await mongo_db.find_one(TestReportService.collection_name, {"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Test Report not found")
        
        update_data = report_data.dict(exclude_unset=True)
        
        # Handle note/notes field - frontend sends 'note', backend stores 'notes'
        if "note" in update_data:
            update_data["notes"] = update_data.pop("note")
            logger.debug("Mapped 'note' to 'notes' field")
        
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
            await mongo_db.update(TestReportService.collection_name, {"id": report_id}, update_data)
        
        updated_report = await mongo_db.find_one(TestReportService.collection_name, {"id": report_id})
        
        # Handle backward compatibility
        if not updated_report.get("test_report_name") and updated_report.get("doc_name"):
            updated_report["test_report_name"] = updated_report.get("doc_name")
        
        # Log audit
        try:
            ship = await mongo_db.find_one("ships", {"id": updated_report.get("ship_id")})
            ship_name = ship.get("name", "Unknown Ship") if ship else "Unknown Ship"
            
            audit_service = TestReportService.get_audit_log_service()
            user_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            await audit_service.log_document_update(
                ship_name=ship_name,
                old_doc=report,
                new_doc=updated_report,
                doc_type='test_report',
                user=user_dict
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        # Map notes → note for frontend (frontend expects 'note' field)
        if updated_report.get("notes") and not updated_report.get("note"):
            updated_report["note"] = updated_report.get("notes")
        
        logger.info(f"✅ Test Report updated: {report_id}")
        
        return TestReportResponse(**updated_report)
    
    @staticmethod
    async def delete_test_report(
        report_id: str, 
        current_user: UserResponse,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> dict:
        """Delete test report and schedule Google Drive file deletion in background"""
        from app.utils.background_tasks import delete_file_background
        from app.services.gdrive_service import GDriveService
        from app.repositories.ship_repository import ShipRepository
        
        report = await mongo_db.find_one(TestReportService.collection_name, {"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Test Report not found")
        
        # Extract file info before deleting from DB
        test_report_file_id = report.get("test_report_file_id")
        test_report_summary_file_id = report.get("test_report_summary_file_id")
        test_report_name = report.get("test_report_name", "Unknown")
        
        # Delete from database immediately
        await mongo_db.delete(TestReportService.collection_name, {"id": report_id})
        logger.info(f"✅ Test Report deleted from DB: {report_id} ({test_report_name})")
        
        # Log audit
        try:
            ship = await mongo_db.find_one("ships", {"id": report.get("ship_id")})
            ship_name = ship.get("name", "Unknown Ship") if ship else "Unknown Ship"
            
            audit_service = TestReportService.get_audit_log_service()
            user_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            await audit_service.log_document_delete(
                ship_name=ship_name,
                doc_data=report,
                doc_type='test_report',
                user=user_dict
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        # Schedule Google Drive file deletions in background if files exist
        files_to_delete = []
        
        if test_report_file_id:
            files_to_delete.append(("original", test_report_file_id))
            logger.info(f"📋 Found original file to delete: {test_report_file_id}")
        
        if test_report_summary_file_id:
            files_to_delete.append(("summary", test_report_summary_file_id))
            logger.info(f"📋 Found summary file to delete: {test_report_summary_file_id}")
        
        if files_to_delete and background_tasks:
            # Get ship to find company_id
            ship_id = report.get("ship_id")
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
                                "test_report",
                                f"{test_report_name} ({file_type})",
                                GDriveService
                            )
                            logger.info(f"📋 Scheduled background deletion for {file_type} file: {file_id}")
                        
                        return {
                            "success": True,
                            "message": "Test Report deleted successfully. File deletion in progress...",
                            "report_id": report_id,
                            "background_deletion": True,
                            "files_scheduled": len(files_to_delete)
                        }
        
        return {
            "success": True,
            "message": "Test Report deleted successfully",
            "report_id": report_id,
            "background_deletion": False
        }
    
    @staticmethod
    async def bulk_delete_test_reports(
        request: BulkDeleteTestReportRequest, 
        current_user: UserResponse,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> dict:
        """Bulk delete test reports and schedule Google Drive file cleanup"""
        deleted_count = 0
        files_scheduled = 0
        
        for report_id in request.report_ids:
            try:
                result = await TestReportService.delete_test_report(report_id, current_user, background_tasks)
                deleted_count += 1
                
                # Count scheduled files for deletion
                if result.get('background_deletion'):
                    files_scheduled += result.get('files_scheduled', 0)
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to delete test report {report_id}: {e}")
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} test reports, {files_scheduled} files scheduled for cleanup")
        
        return {
            "success": True,
            "message": f"Successfully deleted {deleted_count} test reports. File cleanup in progress...",
            "deleted_count": deleted_count,
            "files_scheduled_for_deletion": files_scheduled,
            "background_deletion": files_scheduled > 0
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, test_report_name: str, test_report_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if test report is duplicate"""
        filters = {
            "ship_id": ship_id,
            "test_report_name": test_report_name
        }
        
        if test_report_no:
            filters["test_report_no"] = test_report_no
        
        existing = await mongo_db.find_one(TestReportService.collection_name, filters)
        
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
    ) -> dict:
        """
        Upload test report files to Google Drive
        
        Port from backend-v1/server.py line 11646-11756
        
        Args:
            report_id: Test report ID
            file_content: Base64 encoded file content
            filename: Original filename
            content_type: File content type
            summary_text: Summary text (optional)
            current_user: Current user
        
        Returns:
            Upload result with file IDs
        """
        try:
            logger.info(f"📤 Starting file upload for test report: {report_id}")
            
            # Validate report exists
            report = await mongo_db.find_one(TestReportService.collection_name, {"id": report_id})
            if not report:
                raise HTTPException(status_code=404, detail="Test report not found")
            
            # Get ship info
            ship_id = report.get("ship_id")
            if not ship_id:
                raise HTTPException(status_code=400, detail="Test report has no ship_id")
            
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
            
            # Upload original file to: ShipName/Class & Flag Cert/Test Report/
            logger.info(f"📤 Uploading test report to: {ship_name}/Class & Flag Cert/Test Report/{filename}")
            
            upload_result = await GDriveService.upload_file(
                file_content=file_bytes,
                filename=filename,
                content_type=content_type,
                folder_path=f"{ship_name}/Class & Flag Cert/Test Report",
                company_id=company_uuid
            )
            
            if not upload_result.get('success'):
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload test report file: {upload_result.get('message', 'Unknown error')}"
                )
            
            test_report_file_id = upload_result.get('file_id')
            
            # Upload summary file if provided
            test_report_summary_file_id = None
            summary_error = None
            
            if summary_text and summary_text.strip():
                try:
                    # Create summary filename
                    base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                    summary_filename = f"{base_name}_Summary.txt"
                    
                    # Upload to SAME folder as original file (like Survey Report)
                    summary_folder_path = f"{ship_name}/Class & Flag Cert/Test Report"
                    
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
                        test_report_summary_file_id = summary_upload.get('file_id')
                        logger.info(f"✅ Summary uploaded: {test_report_summary_file_id}")
                    else:
                        summary_error = summary_upload.get('message', 'Unknown error')
                        logger.warning(f"⚠️ Summary upload failed (non-critical): {summary_error}")
                        
                except Exception as summary_exc:
                    summary_error = str(summary_exc)
                    logger.warning(f"⚠️ Summary upload failed (non-critical): {summary_error}")
            
            # Update test report record with file IDs
            update_data = {
                "updated_at": datetime.now(timezone.utc)
            }
            
            if test_report_file_id:
                update_data["test_report_file_id"] = test_report_file_id
            
            if test_report_summary_file_id:
                update_data["test_report_summary_file_id"] = test_report_summary_file_id
            
            await mongo_db.update(TestReportService.collection_name, {"id": report_id}, update_data)
            logger.info("✅ Test report updated with file IDs")
            
            # Get updated report
            updated_report = await mongo_db.find_one(TestReportService.collection_name, {"id": report_id})
            
            logger.info("✅ Test report files uploaded successfully")
            
            return {
                "success": True,
                "message": "Test report files uploaded successfully",
                "test_report_file_id": test_report_file_id,
                "test_report_summary_file_id": test_report_summary_file_id,
                "summary_error": summary_error
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading test report files: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload test report files: {str(e)}"
            )

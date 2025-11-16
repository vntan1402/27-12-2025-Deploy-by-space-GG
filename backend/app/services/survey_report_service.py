import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.survey_report import SurveyReportCreate, SurveyReportUpdate, SurveyReportResponse, BulkDeleteSurveyReportRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class SurveyReportService:
    """Service for Survey Report operations"""
    
    collection_name = "survey_reports"
    
    @staticmethod
    async def get_survey_reports(ship_id: Optional[str], current_user: UserResponse) -> List[SurveyReportResponse]:
        """Get survey reports with optional ship filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        
        reports = await mongo_db.find_all(SurveyReportService.collection_name, filters)
        
        # Handle backward compatibility
        result = []
        for report in reports:
            # Map old field names if present
            if not report.get("survey_report_name") and report.get("doc_name"):
                report["survey_report_name"] = report.get("doc_name")
            
            if not report.get("survey_report_no") and report.get("doc_no"):
                report["survey_report_no"] = report.get("doc_no")
            
            if not report.get("issued_date") and report.get("issue_date"):
                report["issued_date"] = report.get("issue_date")
            
            if not report.get("issued_by") and report.get("issued_by"):
                report["issued_by"] = report.get("issued_by")
            
            if not report.get("note") and report.get("notes"):
                report["note"] = report.get("notes")
            
            # Set defaults
            if not report.get("survey_report_name"):
                report["survey_report_name"] = "Untitled Survey Report"
            
            if not report.get("status"):
                report["status"] = "Valid"
            
            result.append(SurveyReportResponse(**report))
        
        return result
    
    @staticmethod
    async def get_survey_report_by_id(report_id: str, current_user: UserResponse) -> SurveyReportResponse:
        """Get survey report by ID"""
        report = await mongo_db.find_one(SurveyReportService.collection_name, {"id": report_id})
        
        if not report:
            raise HTTPException(status_code=404, detail="Survey Report not found")
        
        # Backward compatibility
        if not report.get("survey_report_name") and report.get("doc_name"):
            report["survey_report_name"] = report.get("doc_name")
        
        if not report.get("survey_report_no") and report.get("doc_no"):
            report["survey_report_no"] = report.get("doc_no")
        
        if not report.get("issued_date") and report.get("issue_date"):
            report["issued_date"] = report.get("issue_date")
        
        if not report.get("note") and report.get("notes"):
            report["note"] = report.get("notes")
        
        if not report.get("survey_report_name"):
            report["survey_report_name"] = "Untitled Survey Report"
        
        if not report.get("status"):
            report["status"] = "Valid"
        
        return SurveyReportResponse(**report)
    
    @staticmethod
    async def create_survey_report(report_data: SurveyReportCreate, current_user: UserResponse) -> SurveyReportResponse:
        """Create new survey report"""
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
        
        await mongo_db.create(SurveyReportService.collection_name, report_dict)
        
        logger.info(f"✅ Survey Report created: {report_dict['survey_report_name']}")
        
        return SurveyReportResponse(**report_dict)
    
    @staticmethod
    async def update_survey_report(report_id: str, report_data: SurveyReportUpdate, current_user: UserResponse) -> SurveyReportResponse:
        """Update survey report"""
        report = await mongo_db.find_one(SurveyReportService.collection_name, {"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Survey Report not found")
        
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
            await mongo_db.update(SurveyReportService.collection_name, {"id": report_id}, update_data)
        
        updated_report = await mongo_db.find_one(SurveyReportService.collection_name, {"id": report_id})
        
        if not updated_report.get("survey_report_name") and updated_report.get("doc_name"):
            updated_report["survey_report_name"] = updated_report.get("doc_name")
        
        logger.info(f"✅ Survey Report updated: {report_id}")
        
        return SurveyReportResponse(**updated_report)
    
    @staticmethod
    async def delete_survey_report(report_id: str, current_user: UserResponse) -> dict:
        """Delete survey report"""
        report = await mongo_db.find_one(SurveyReportService.collection_name, {"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Survey Report not found")
        
        await mongo_db.delete(SurveyReportService.collection_name, {"id": report_id})
        
        logger.info(f"✅ Survey Report deleted: {report_id}")
        
        return {"message": "Survey Report deleted successfully"}
    
    @staticmethod
    async def bulk_delete_survey_reports(request: BulkDeleteSurveyReportRequest, current_user: UserResponse) -> dict:
        """Bulk delete survey reports"""
        deleted_count = 0
        errors = []
        
        for report_id in request.report_ids:
            try:
                await SurveyReportService.delete_survey_report(report_id, current_user)
                deleted_count += 1
            except Exception as e:
                errors.append(f"Failed to delete {report_id}: {str(e)}")
                logger.error(f"Error deleting survey report {report_id}: {e}")
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count}/{len(request.report_ids)} survey reports")
        
        return {
            "success": True,
            "message": f"Successfully deleted {deleted_count} survey report(s)",
            "deleted_count": deleted_count,
            "errors": errors if errors else None
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, survey_report_name: str, survey_report_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if survey report is duplicate"""
        filters = {
            "ship_id": ship_id,
            "survey_report_name": survey_report_name
        }
        
        if survey_report_no:
            filters["survey_report_no"] = survey_report_no
        
        existing = await mongo_db.find_one(SurveyReportService.collection_name, filters)
        
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
        summary_text: str,
        current_user: UserResponse
    ) -> dict:
        """
        Upload survey report files to Google Drive
        
        Process:
        1. Validate report exists
        2. Decode base64 file content
        3. Upload original to ship folder
        4. Upload summary to SUMMARY folder
        5. Update record with file IDs
        """
        import base64
        from app.services.gdrive_service import GDriveService
        from app.repositories.ship_repository import ShipRepository
        
        logger.info(f"📤 Starting file upload for survey report: {report_id}")
        
        # Validate report exists
        report = await mongo_db.find_one(SurveyReportService.collection_name, {"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Survey report not found")
        
        # Get ship info
        ship_id = report.get("ship_id")
        if not ship_id:
            raise HTTPException(status_code=400, detail="Survey report has no ship_id")
        
        ship = await ShipRepository.find_by_id(ship_id)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        ship_name = ship.get("name", "Unknown Ship")
        # survey_report_name is for future use if needed
        # survey_report_name = report.get("survey_report_name", "Survey Report")
        
        # Decode base64 file content
        try:
            file_bytes = base64.b64decode(file_content)
            logger.info(f"✅ Decoded file content: {len(file_bytes)} bytes")
        except Exception as e:
            logger.error(f"Failed to decode base64 file content: {e}")
            raise HTTPException(status_code=400, detail="Invalid file content encoding")
        
        upload_results = {}
        
        # Upload 1: Original file to ShipName/Class & Flag Cert/Class Survey Report/
        logger.info(f"📄 Uploading original file to: {ship_name}/Class & Flag Cert/Class Survey Report/{filename}")
        
        try:
            # Build folder path
            folder_path = f"{ship_name}/Class & Flag Cert/Class Survey Report"
            
            original_upload = await GDriveService.upload_file(
                file_content=file_bytes,
                filename=filename,
                content_type=content_type,
                folder_path=folder_path,
                company_id=current_user.company
            )
            
            if not original_upload.get('success'):
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload survey report file: {original_upload.get('message')}"
                )
            
            survey_report_file_id = original_upload.get('file_id')
            upload_results['original'] = original_upload
            logger.info(f"✅ Original file uploaded: {survey_report_file_id}")
            
        except HTTPException:
            raise
        except Exception as upload_error:
            logger.error(f"❌ Error uploading original file: {upload_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload survey report file: {str(upload_error)}"
            )
        
        # Upload 2: Summary file to SAME folder as original (Class Survey Report folder)
        survey_report_summary_file_id = None
        if summary_text and summary_text.strip():
            base_name = filename.rsplit('.', 1)[0]
            summary_filename = f"{base_name}_Summary.txt"
            
            logger.info(f"📋 Uploading summary file to: {ship_name}/Class & Flag Cert/Class Survey Report/{summary_filename}")
            
            try:
                # Convert summary text to bytes
                summary_bytes = summary_text.encode('utf-8')
                
                # Upload to SAME folder as original file
                summary_folder_path = f"{ship_name}/Class & Flag Cert/Class Survey Report"
                
                summary_upload = await GDriveService.upload_file(
                    file_content=summary_bytes,
                    filename=summary_filename,
                    content_type="text/plain",
                    folder_path=summary_folder_path,
                    company_id=current_user.company
                )
                
                if summary_upload.get('success'):
                    survey_report_summary_file_id = summary_upload.get('file_id')
                    upload_results['summary'] = summary_upload
                    logger.info(f"✅ Summary file uploaded: {survey_report_summary_file_id}")
                else:
                    logger.warning(f"⚠️ Summary file upload failed (non-critical): {summary_upload.get('message')}")
                    
            except Exception as summary_error:
                logger.warning(f"⚠️ Summary upload failed (non-critical): {summary_error}")
        
        # Update survey report record with file IDs
        update_data = {
            "survey_report_file_id": survey_report_file_id,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if survey_report_summary_file_id:
            update_data["survey_report_summary_file_id"] = survey_report_summary_file_id
        
        await mongo_db.update(
            SurveyReportService.collection_name,
            {"id": report_id},
            update_data
        )
        logger.info("✅ Survey report record updated with file IDs")
        
        return {
            "success": True,
            "survey_report_file_id": survey_report_file_id,
            "survey_report_summary_file_id": survey_report_summary_file_id,
            "message": "Survey report files uploaded successfully",
            "upload_results": upload_results
        }


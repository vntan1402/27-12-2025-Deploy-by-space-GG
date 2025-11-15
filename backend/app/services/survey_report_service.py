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
        for report_id in request.document_ids:
            try:
                await SurveyReportService.delete_survey_report(report_id, current_user)
                deleted_count += 1
            except:
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} survey reports")
        
        return {
            "message": f"Successfully deleted {deleted_count} survey reports",
            "deleted_count": deleted_count
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

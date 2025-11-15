import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.test_report import TestReportCreate, TestReportUpdate, TestReportResponse, BulkDeleteTestReportRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class TestReportService:
    """Service for Test Report operations"""
    
    collection_name = "test_reports"
    
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
        
        if not report.get("test_report_name"):
            report["test_report_name"] = "Untitled Test Report"
        
        return TestReportResponse(**report)
    
    @staticmethod
    async def create_test_report(report_data: TestReportCreate, current_user: UserResponse) -> TestReportResponse:
        """Create new test report"""
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
        
        await mongo_db.create(TestReportService.collection_name, report_dict)
        
        logger.info(f"✅ Test Report created: {report_dict['test_report_name']}")
        
        return TestReportResponse(**report_dict)
    
    @staticmethod
    async def update_test_report(report_id: str, report_data: TestReportUpdate, current_user: UserResponse) -> TestReportResponse:
        """Update test report"""
        report = await mongo_db.find_one(TestReportService.collection_name, {"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Test Report not found")
        
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
            await mongo_db.update(TestReportService.collection_name, {"id": report_id}, update_data)
        
        updated_report = await mongo_db.find_one(TestReportService.collection_name, {"id": report_id})
        
        # Handle backward compatibility
        if not updated_report.get("test_report_name") and updated_report.get("doc_name"):
            updated_report["test_report_name"] = updated_report.get("doc_name")
        
        logger.info(f"✅ Test Report updated: {report_id}")
        
        return TestReportResponse(**updated_report)
    
    @staticmethod
    async def delete_test_report(report_id: str, current_user: UserResponse) -> dict:
        """Delete test report"""
        report = await mongo_db.find_one(TestReportService.collection_name, {"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Test Report not found")
        
        await mongo_db.delete(TestReportService.collection_name, {"id": report_id})
        
        logger.info(f"✅ Test Report deleted: {report_id}")
        
        return {"message": "Test Report deleted successfully"}
    
    @staticmethod
    async def bulk_delete_test_reports(request: BulkDeleteTestReportRequest, current_user: UserResponse) -> dict:
        """Bulk delete test reports"""
        deleted_count = 0
        for report_id in request.document_ids:
            try:
                await TestReportService.delete_test_report(report_id, current_user)
                deleted_count += 1
            except:
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} test reports")
        
        return {
            "message": f"Successfully deleted {deleted_count} test reports",
            "deleted_count": deleted_count
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

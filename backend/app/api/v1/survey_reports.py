import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query

from app.models.survey_report import SurveyReportCreate, SurveyReportUpdate, SurveyReportResponse, BulkDeleteSurveyReportRequest
from app.models.user import UserResponse, UserRole
from app.services.survey_report_service import SurveyReportService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[SurveyReportResponse])
async def get_survey_reports(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Survey Reports, optionally filtered by ship_id"""
    try:
        return await SurveyReportService.get_survey_reports(ship_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching Survey Reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Survey Reports")

@router.get("/{doc_id}", response_model=SurveyReportResponse)
async def get_survey_report_by_id(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific Survey Report by ID"""
    try:
        return await SurveyReportService.get_survey_report_by_id(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Survey Report {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Survey Report")

@router.post("", response_model=SurveyReportResponse)
async def create_survey_report(
    report_data: SurveyReportCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Create new Survey Report (Editor+ role required)"""
    try:
        return await SurveyReportService.create_survey_report(report_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating Survey Report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Survey Report")

@router.put("/{doc_id}", response_model=SurveyReportResponse)
async def update_survey_report(
    doc_id: str,
    report_data: SurveyReportUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Update Survey Report (Editor+ role required)"""
    try:
        return await SurveyReportService.update_survey_report(doc_id, report_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating Survey Report: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Survey Report")

@router.delete("/{doc_id}")
async def delete_survey_report(
    doc_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Survey Report (Editor+ role required)"""
    try:
        return await SurveyReportService.delete_survey_report(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Survey Report: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Survey Report")

@router.post("/bulk-delete")
async def bulk_delete_survey_reports(
    request: BulkDeleteSurveyReportRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Survey Reports (Editor+ role required)"""
    try:
        return await SurveyReportService.bulk_delete_survey_reports(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Survey Reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Survey Reports")

@router.post("/check-duplicate")
async def check_duplicate_survey_report(
    ship_id: str,
    survey_report_name: str,
    survey_report_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if Survey Report is duplicate"""
    try:
        return await SurveyReportService.check_duplicate(ship_id, survey_report_name, survey_report_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

@router.post("/analyze-file")
async def analyze_survey_report_file(
    file: UploadFile = File(...),
    ship_id: Optional[str] = None,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Analyze survey report file using AI (Editor+ role required)"""
    # TODO: Implement AI analysis for survey reports
    return {
        "success": True,
        "message": "Survey report analysis not yet implemented",
        "analysis": None
    }

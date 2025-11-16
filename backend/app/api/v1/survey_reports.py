import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form, Body

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
    survey_report_file: UploadFile = File(...),
    ship_id: str = Form(...),
    bypass_validation: str = Form("false"),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze survey report file using Google Document AI
    
    Process:
    1. Validate PDF file
    2. Split if >15 pages
    3. Process with Document AI


@router.post("/{report_id}/upload-files")
async def upload_survey_report_files(
    report_id: str,
    file_content: str = Body(...),
    filename: str = Body(...),
    content_type: str = Body(...),
    summary_text: str = Body(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload survey report files to Google Drive after record creation
    
    Process:
    1. Decode base64 file content
    2. Upload original to: ShipName/Class & Flag Cert/Class Survey Report/
    3. Upload summary to: SUMMARY/Class & Flag Document/
    4. Update record with file IDs
    
    Args:
        report_id: Survey report ID
        file_content: Base64 encoded file content
        filename: Original filename
        content_type: File MIME type
        summary_text: Enhanced summary text (with OCR)
        current_user: Current authenticated user
    """
    from app.services.survey_report_service import SurveyReportService
    
    try:
        result = await SurveyReportService.upload_files(
            report_id=report_id,
            file_content=file_content,
            filename=filename,
            content_type=content_type,
            summary_text=summary_text,
            current_user=current_user
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading survey report files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload survey report files: {str(e)}"
        )
    """
    from app.services.survey_report_analyze_service import SurveyReportAnalyzeService
    
    try:
        bypass_bool = bypass_validation.lower() == "true"
        
        result = await SurveyReportAnalyzeService.analyze_file(
            file=survey_report_file,
            ship_id=ship_id,
            bypass_validation=bypass_bool,
            current_user=current_user
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing survey report file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze survey report: {str(e)}"
        )

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Body, Form

from app.models.test_report import TestReportCreate, TestReportUpdate, TestReportResponse, BulkDeleteTestReportRequest
from app.models.user import UserResponse, UserRole
from app.services.test_report_service import TestReportService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[TestReportResponse])
async def get_test_reports(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Test Reports, optionally filtered by ship_id"""
    try:
        return await TestReportService.get_test_reports(ship_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching Test Reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Test Reports")

@router.get("/{doc_id}", response_model=TestReportResponse)
async def get_test_report_by_id(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific Test Report by ID"""
    try:
        return await TestReportService.get_test_report_by_id(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Test Report {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Test Report")

@router.post("", response_model=TestReportResponse)
async def create_test_report(
    report_data: TestReportCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Create new Test Report (Editor+ role required)"""
    try:
        return await TestReportService.create_test_report(report_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating Test Report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Test Report")

@router.put("/{doc_id}", response_model=TestReportResponse)
async def update_test_report(
    doc_id: str,
    report_data: TestReportUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Update Test Report (Editor+ role required)"""
    try:
        return await TestReportService.update_test_report(doc_id, report_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating Test Report: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Test Report")

@router.delete("/{doc_id}")
async def delete_test_report(
    doc_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Test Report (Editor+ role required)"""
    try:
        return await TestReportService.delete_test_report(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Test Report: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Test Report")

@router.post("/bulk-delete")
async def bulk_delete_test_reports(
    request: BulkDeleteTestReportRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Test Reports (Editor+ role required)"""
    try:
        return await TestReportService.bulk_delete_test_reports(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Test Reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Test Reports")

@router.post("/check-duplicate")
async def check_duplicate_test_report(
    ship_id: str,
    test_report_name: str,
    test_report_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if Test Report is duplicate"""
    try:
        return await TestReportService.check_duplicate(ship_id, test_report_name, test_report_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

@router.post("/{report_id}/upload-files")
async def upload_test_report_files(
    report_id: str,
    file_content: str = Body(...),
    filename: str = Body(...),
    content_type: str = Body(...),
    summary_text: Optional[str] = Body(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload test report files to Google Drive after record creation (Editor+ role required)
    
    Process:
    1. Decode base64 file content
    2. Upload original file to: ShipName/Class & Flag Cert/Test Report/
    3. Upload summary to: SUMMARY/Class & Flag Document/
    4. Update test report record with file IDs
    
    Args:
        report_id: Test report ID
        file_content: Base64 encoded file content
        filename: Original filename
        content_type: File content type
        summary_text: Summary text (optional)
        current_user: Current authenticated user
    
    Returns:
        Upload result with file IDs
    """
    try:
        result = await TestReportService.upload_files(
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
        logger.error(f"❌ Error uploading test report files: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to upload test report files: {str(e)}")

@router.post("/analyze-file")
async def analyze_test_report_file(
    test_report_file: UploadFile = File(...),
    ship_id: str = Form(...),
    bypass_validation: str = Form("false"),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze Test Report file using AI (Editor+ role required)
    
    Process:
    1. Validate PDF file
    2. Split if > 15 pages
    3. Process with Document AI + OCR
    4. Extract fields with System AI
    5. Calculate Valid Date based on equipment type
    6. Normalize issued_by
    7. Validate ship info
    8. Return analysis + file content (base64) for later upload
    
    Args:
        test_report_file: PDF file to analyze
        ship_id: Ship ID to validate against
        bypass_validation: Skip ship name/IMO validation if True
        current_user: Current authenticated user
    
    Returns:
        Analysis result with extracted fields + file content
    """
    try:
        from app.services.test_report_analyze_service import TestReportAnalyzeService
        
        bypass_bool = bypass_validation.lower() == "true"
        
        result = await TestReportAnalyzeService.analyze_file(
            file=test_report_file,
            ship_id=ship_id,
            bypass_validation=bypass_bool,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing test report file: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze test report: {str(e)}")


import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query

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
async def check_duplicate_document(
    ship_id: str,
    doc_name: str,
    doc_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if Test Report is duplicate"""
    try:
        return await service.check_duplicate(ship_id, doc_name, doc_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

@router.post("/analyze-file")
async def analyze_document_file(
    file: UploadFile = File(...),
    ship_id: Optional[str] = None,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Analyze Test Report file using AI (Editor+ role required)"""
    try:
        return await service.analyze_file(file, ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing Test Report file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze Test Report: {str(e)}")


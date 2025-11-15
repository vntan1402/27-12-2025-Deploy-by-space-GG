import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query

from app.models.audit_report import AuditReportCreate, AuditReportUpdate, AuditReportResponse, BulkDeleteAuditReportRequest
from app.models.user import UserResponse, UserRole
from app.services.audit_report_service import AuditReportService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[AuditReportResponse])
async def get_audit_reports(
    ship_id: Optional[str] = Query(None),
    audit_type: Optional[str] = Query(None),  # Filter by ISM, ISPS, or MLC
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Audit Reports (ISM/ISPS/MLC), optionally filtered by ship_id and audit_type"""
    try:
        return await AuditReportService.get_audit_reports(ship_id, audit_type, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching Audit Reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Audit Reports")

@router.get("/{report_id}", response_model=AuditReportResponse)
async def get_audit_report_by_id(
    report_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific Audit Report by ID"""
    try:
        return await AuditReportService.get_audit_report_by_id(report_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching Audit Report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Audit Report")

@router.post("", response_model=AuditReportResponse)
async def create_audit_report(
    report_data: AuditReportCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Create new Audit Report (Editor+ role required)"""
    try:
        return await AuditReportService.create_audit_report(report_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating Audit Report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Audit Report")

@router.put("/{report_id}", response_model=AuditReportResponse)
async def update_audit_report(
    report_id: str,
    report_data: AuditReportUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Update Audit Report (Editor+ role required)"""
    try:
        return await AuditReportService.update_audit_report(report_id, report_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating Audit Report: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Audit Report")

@router.delete("/{report_id}")
async def delete_audit_report(
    report_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Audit Report (Editor+ role required)"""
    try:
        return await AuditReportService.delete_audit_report(report_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Audit Report: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Audit Report")

@router.post("/bulk-delete")
async def bulk_delete_audit_reports(
    request: BulkDeleteAuditReportRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Audit Reports (Editor+ role required)"""
    try:
        return await AuditReportService.bulk_delete_audit_reports(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting Audit Reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete Audit Reports")

@router.post("/check-duplicate")
async def check_duplicate_audit_report(
    ship_id: str,
    audit_report_name: str,
    audit_report_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if Audit Report is duplicate"""
    try:
        return await AuditReportService.check_duplicate(ship_id, audit_report_name, audit_report_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

@router.post("/analyze")
async def analyze_audit_report_file(
    file: UploadFile = File(...),
    ship_id: Optional[str] = None,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Analyze audit report file using AI (Editor+ role required)"""
    # TODO: Implement AI analysis for audit reports
    return {
        "success": True,
        "message": "Audit report analysis not yet implemented",
        "analysis": None
    }

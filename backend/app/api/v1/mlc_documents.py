"""MLC Documents - Wrapper for Audit Reports with audit_type=MLC"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.audit_report import AuditReportResponse, BulkDeleteAuditReportRequest
from app.models.user import UserResponse
from app.services.audit_report_service import AuditReportService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# MLC Documents are Audit Reports with audit_type="MLC"

@router.get("", response_model=List[AuditReportResponse])
async def get_mlc_documents(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get MLC Documents (Audit Reports with type=MLC)"""
    try:
        return await AuditReportService.get_audit_reports(ship_id, "MLC", current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching MLC Documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch MLC Documents")

@router.get("/{doc_id}", response_model=AuditReportResponse)
async def get_mlc_document_by_id(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get MLC Document by ID"""
    try:
        return await AuditReportService.get_audit_report_by_id(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching MLC Document: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch MLC Document")

@router.post("/bulk-delete")
async def bulk_delete_mlc_documents(
    request: BulkDeleteAuditReportRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Bulk delete MLC Documents"""
    try:
        return await AuditReportService.bulk_delete_audit_reports(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting MLC Documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete MLC Documents")

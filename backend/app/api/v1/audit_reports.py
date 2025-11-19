import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from pydantic import BaseModel

from app.models.audit_report import AuditReportCreate, AuditReportUpdate, AuditReportResponse, BulkDeleteAuditReportRequest
from app.models.user import UserResponse, UserRole
from app.services.audit_report_service import AuditReportService
from app.services.audit_report_analyze_service import AuditReportAnalyzeService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user


# ========== STATIC ROUTES (must come before dynamic routes) ==========

@router.post("/bulk-delete")
async def bulk_delete_audit_reports(
    request: BulkDeleteAuditReportRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete Audit Reports with background GDrive cleanup (Editor+ role required)"""
    try:
        return await AuditReportService.bulk_delete_audit_reports(
            request,
            background_tasks,
            current_user
        )
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

@router.post("/analyze-file")
async def analyze_audit_report_file(
    ship_id: str = Form(...),
    audit_report_file: UploadFile = File(...),
    bypass_validation: str = Form("false"),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze audit report file using AI (Editor+ role required)
    
    Process:
    1. Validate PDF file (magic bytes, extension, max 50MB)
    2. Check if needs splitting (>15 pages)
    3. Process with Document AI (parallel chunks if large)
    4. Extract fields with System AI
    5. Normalize issued_by
    6. Validate ship name/IMO (optional)
    7. Return analysis + base64 file for upload
    
    Returns:
        dict: Analysis result with extracted fields + metadata
            {
                "audit_report_name": str,
                "audit_type": str (ISM/ISPS/MLC/CICA),
                "report_form": str,
                "audit_report_no": str,
                "issued_by": str (normalized),
                "audit_date": str (YYYY-MM-DD),
                "auditor_name": str,
                "ship_name": str,
                "ship_imo": str,
                "note": str,
                "confidence_score": float,
                "_file_content": str (base64),
                "_filename": str,
                "_content_type": str,
                "_summary_text": str,
                "_split_info": dict (if split)
            }
    """
    try:
        # Convert bypass_validation string to boolean
        bypass_validation_bool = bypass_validation.lower() in ('true', '1', 'yes')
        
        # Call analysis service
        result = await AuditReportAnalyzeService.analyze_file(
            file=audit_report_file,
            ship_id=ship_id,
            bypass_validation=bypass_validation_bool,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing audit report file: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to analyze audit report file: {str(e)}")


# ========== COLLECTION ROUTES ==========

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


# ========== DYNAMIC ROUTES (must come after static routes) ==========

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
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete Audit Report with background GDrive cleanup (Editor+ role required)"""
    try:
        return await AuditReportService.delete_audit_report(
            report_id,
            background_tasks,
            current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting Audit Report: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Audit Report")

class UploadFilesRequest(BaseModel):
    """Request model for upload files endpoint"""
    file_content: str
    filename: str
    content_type: str
    summary_text: Optional[str] = None

@router.post("/{report_id}/upload-files")
async def upload_audit_report_files(
    report_id: str,
    request: UploadFilesRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Upload audit report files to Google Drive
    
    Path: ShipName/ISM - ISPS - MLC/Audit Report/
    
    1. Decode base64 file content
    2. Upload original file
    3. Upload summary file (if provided)
    4. Update audit report record with file IDs
    
    Args:
        report_id: Audit report ID
        file_content: Base64 encoded file content
        filename: Original filename
        content_type: MIME type
        summary_text: Summary text to upload (optional)
    
    Returns:
        dict: {
            "success": True,
            "file_id": str,
            "summary_file_id": str,
            "message": str
        }
    """
    try:
        result = await AuditReportService.upload_files(
            report_id=report_id,
            file_content=request.file_content,
            filename=request.filename,
            content_type=request.content_type,
            summary_text=request.summary_text,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading audit report files: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to upload audit report files: {str(e)}")

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks

from app.models.certificate import (
    CertificateCreate, 
    CertificateUpdate, 
    CertificateResponse,
    BulkDeleteRequest
)
from app.models.user import UserResponse, UserRole
from app.services.certificate_service import CertificateService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[CertificateResponse])
async def get_certificates(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get certificates, optionally filtered by ship_id
    """
    try:
        return await CertificateService.get_certificates(ship_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch certificates")

@router.get("/{cert_id}", response_model=CertificateResponse)
async def get_certificate_by_id(
    cert_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific certificate by ID
    """
    try:
        return await CertificateService.get_certificate_by_id(cert_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching certificate {cert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch certificate")

@router.post("", response_model=CertificateResponse)
async def create_certificate(
    cert_data: CertificateCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Create new certificate (Editor+ role required)
    """
    try:
        return await CertificateService.create_certificate(cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to create certificate")

@router.put("/{cert_id}", response_model=CertificateResponse)
async def update_certificate(
    cert_id: str,
    cert_data: CertificateUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Update certificate (Editor+ role required)
    """
    try:
        return await CertificateService.update_certificate(cert_id, cert_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to update certificate")

@router.delete("/{cert_id}")
async def delete_certificate(
    cert_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Delete certificate with background Google Drive file deletion (Editor+ role required)
    """
    try:
        return await CertificateService.delete_certificate(cert_id, current_user, background_tasks)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete certificate")

@router.post("/bulk-delete")
async def bulk_delete_certificates(
    request: BulkDeleteRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Bulk delete certificates with background file deletion (Editor+ role required)
    """
    try:
        return await CertificateService.bulk_delete_certificates(request, current_user, background_tasks)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete certificates")

@router.post("/check-duplicate")
async def check_duplicate_certificate(
    ship_id: str,
    cert_name: str,
    cert_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Check if certificate is duplicate
    """
    try:
        return await CertificateService.check_duplicate(ship_id, cert_name, cert_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")

@router.post("/analyze-file")
async def analyze_certificate_file(
    file: UploadFile = File(...),
    ship_id: Optional[str] = None,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze certificate file using AI (Editor+ role required)
    """
    try:
        return await CertificateService.analyze_certificate_file(file, ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing certificate file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze certificate: {str(e)}")


@router.post("/{cert_id}/upload-files")
async def upload_certificate_files(
    cert_id: str,
    files: List[UploadFile] = File(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload multiple files for a certificate (Editor+ role required)
    """
    try:
        import os
        from pathlib import Path
        
        # Verify certificate exists
        cert = await CertificateService.get_certificate_by_id(cert_id, current_user)
        if not cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Create upload directory
        upload_dir = Path(f"/app/uploads/certificates/{cert_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        for file in files:
            # Save file
            file_path = upload_dir / file.filename
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            uploaded_files.append({
                "filename": file.filename,
                "path": f"/uploads/certificates/{cert_id}/{file.filename}",
                "size": len(content)
            })
        
        logger.info(f"✅ Uploaded {len(uploaded_files)} files for certificate {cert_id}")
        
        return {
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "files": uploaded_files
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading certificate files: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload files")

@router.get("/{cert_id}/file-link")
async def get_certificate_file_link(
    cert_id: str,
    filename: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get file download link for certificate
    """
    try:
        import os
        from pathlib import Path
        
        # Verify certificate exists
        cert = await CertificateService.get_certificate_by_id(cert_id, current_user)
        if not cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Get file path
        if filename:
            file_path = f"/uploads/certificates/{cert_id}/{filename}"
        else:
            # Return first file if no filename specified
            cert_dir = Path(f"/app/uploads/certificates/{cert_id}")
            if cert_dir.exists():
                files = list(cert_dir.iterdir())
                if files:
                    file_path = f"/uploads/certificates/{cert_id}/{files[0].name}"
                else:
                    raise HTTPException(status_code=404, detail="No files found for certificate")
            else:
                raise HTTPException(status_code=404, detail="No files found for certificate")
        
        # Check if file exists
        if not os.path.exists(f"/app{file_path}"):
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "file_url": file_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting certificate file link: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file link")



@router.get("/upcoming-surveys")
async def get_upcoming_surveys(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get upcoming surveys with annotation-based window logic
    Simplified version migrated from backend-v1
    """
    from datetime import datetime, timedelta
    from app.db.mongodb import mongo_db
    import re
    
    try:
        user_company = current_user.company
        logger.info(f"🔍 Checking upcoming surveys for company: {user_company}")
        
        # Get company record
        company_record = await mongo_db.database.companies.find_one({"id": user_company})
        company_name = None
        if company_record:
            company_name = company_record.get('name_en') or company_record.get('name_vn')
        
        # Get all ships by company ID or name
        ships_query = {"$or": [{"company": user_company}]}
        if company_name:
            ships_query["$or"].append({"company": company_name})
        
        ships = await mongo_db.database.ships.find(ships_query).to_list(length=1000)
        ship_ids = [ship.get('id') for ship in ships if ship.get('id')]
        
        logger.info(f"🚢 Found {len(ships)} ships for company")
        
        if not ship_ids:
            return {
                "upcoming_surveys": [],
                "total_count": 0,
                "company": user_company,
                "check_date": datetime.now().date().isoformat()
            }
        
        # Get all certificates from these ships
        all_certificates = await mongo_db.database.certificates.find(
            {"ship_id": {"$in": ship_ids}}
        ).to_list(length=10000)
        
        logger.info(f"📄 Found {len(all_certificates)} total certificates to check")
        
        current_date = datetime.now().date()
        upcoming_surveys = []
        
        for cert in all_certificates:
            try:
                # Get Next Survey Display field
                next_survey_display = cert.get('next_survey_display') or cert.get('next_survey')
                
                if not next_survey_display:
                    continue
                
                # Parse date (dd/mm/yyyy format or ISO)
                next_survey_str = str(next_survey_display)
                date_match = re.search(r'(\d{2}/\d{2}/\d{4})', next_survey_str)
                
                if not date_match:
                    # Try ISO format
                    date_match_alt = re.search(r'(\d{4}-\d{2}-\d{2})', next_survey_str)
                    if date_match_alt:
                        date_str = date_match_alt.group(1)
                        next_survey_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        continue
                else:
                    date_str = date_match.group(1)
                    next_survey_date = datetime.strptime(date_str, '%d/%m/%Y').date()
                
                # Determine window (default ±3 months)
                window_months = 3
                if '(-3M)' in next_survey_str or '(-3M' in next_survey_str:
                    # Special Survey: only before
                    window_open = next_survey_date - timedelta(days=90)
                    window_close = next_survey_date
                else:
                    # Annual/Intermediate: ±3M
                    window_open = next_survey_date - timedelta(days=90)
                    window_close = next_survey_date + timedelta(days=90)
                
                # Check if current date is WITHIN window (backend-v1 logic)
                if not (window_open <= current_date <= window_close):
                    continue  # Not within window yet
                
                # Calculate status
                days_until_window_close = (window_close - current_date).days
                days_until_survey = (next_survey_date - current_date).days
                
                # Status logic (unified with backend-v1)
                is_overdue = current_date > window_close
                is_critical = 0 <= days_until_window_close <= 30
                
                # Due Soon: within window but > 30 days to close
                window_close_minus_30_date = window_close - timedelta(days=30)
                is_due_soon = window_open < current_date < window_close_minus_30_date
                
                # Determine primary status
                if is_overdue:
                    status = "overdue"
                elif is_critical:
                    status = "critical"
                elif is_due_soon:
                    status = "due_soon"
                else:
                    status = "within_window"
                
                # Get ship info
                ship = next((s for s in ships if s.get('id') == cert.get('ship_id')), None)
                
                # Get cert abbreviation
                cert_abbreviation = cert.get('cert_abbreviation') or cert.get('abbreviation', '')
                cert_name_display = f"{cert.get('cert_name', '')} ({cert_abbreviation})" if cert_abbreviation else cert.get('cert_name', '')
                
                upcoming_surveys.append({
                    "certificate_id": cert.get("id"),
                    "ship_id": cert.get("ship_id"),
                    "ship_name": ship.get("name") if ship else "Unknown",
                    "cert_name": cert.get("cert_name"),
                    "cert_abbreviation": cert_abbreviation,
                    "cert_name_display": cert_name_display,
                    "cert_type": cert.get("cert_type"),
                    "cert_no": cert.get("cert_no"),
                    "next_survey": next_survey_str,
                    "next_survey_date": next_survey_date.isoformat(),
                    "next_survey_type": cert.get("next_survey_type"),
                    "last_endorse": cert.get("last_endorse"),
                    "status": cert.get("status"),  # Certificate status (Active/Expired/etc)
                    "days_until_survey": days_until_survey,
                    "days_until_window_close": days_until_window_close,
                    "is_overdue": is_overdue,
                    "is_due_soon": is_due_soon,
                    "is_critical": is_critical,
                    "is_within_window": True,
                    "window_open": window_open.isoformat(),
                    "window_close": window_close.isoformat(),
                    "window_type": "±3M" if '(±3M)' in next_survey_str else "-3M"
                })
                
            except Exception as e:
                logger.warning(f"Error processing certificate {cert.get('id')}: {e}")
                continue
        
        # Sort by days_until_window_close (most urgent first)
        upcoming_surveys.sort(key=lambda x: x["days_until_window_close"])
        
        logger.info(f"✅ Found {len(upcoming_surveys)} upcoming surveys")
        
        return {
            "upcoming_surveys": upcoming_surveys,
            "total_count": len(upcoming_surveys),
            "company": user_company,
            "company_name": company_name,
            "check_date": current_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking upcoming surveys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check upcoming surveys: {str(e)}")


@router.post("/multi-upload")
async def multi_certificate_upload(
    ship_id: str = Query(..., description="Ship ID for certificate upload"),
    files: List[UploadFile] = File(..., description="Certificate files to upload"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload multiple certificate files with AI analysis and Google Drive integration
    
    This endpoint processes multiple certificate files in a single request:
    1. AI analysis for information extraction
    2. Quality check and classification
    3. IMO/ship name validation
    4. Duplicate detection
    5. Google Drive upload
    6. Certificate record creation
    
    Returns detailed results for each file including success/error status
    """
    from app.services.certificate_multi_upload_service import CertificateMultiUploadService
    
    try:
        logger.info(f"📤 Multi-upload started: {len(files)} files for ship {ship_id}")
        
        # Delegate to service
        result = await CertificateMultiUploadService.process_multi_upload(
            ship_id=ship_id,
            files=files,
            current_user=current_user,
            background_tasks=background_tasks
        )
        
        logger.info(f"✅ Multi-upload completed: {result.get('summary', {})}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Multi-upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


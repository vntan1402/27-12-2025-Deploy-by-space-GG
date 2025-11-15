import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.models.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.models.user import UserResponse, UserRole
from app.services.company_service import CompanyService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_admin_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has admin permission"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[CompanyResponse])
async def get_companies(current_user: UserResponse = Depends(get_current_user)):
    """
    Get all companies
    """
    try:
        return await CompanyService.get_all_companies(current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching companies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch companies")

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company_by_id(
    company_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific company by ID
    """
    try:
        return await CompanyService.get_company_by_id(company_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch company")

@router.post("", response_model=CompanyResponse)
async def create_company(
    company_data: CompanyCreate,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Create new company (Admin only)
    """
    try:
        return await CompanyService.create_company(company_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating company: {e}")
        raise HTTPException(status_code=500, detail="Failed to create company")

@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Update company (Admin only)
    """
    try:
        return await CompanyService.update_company(company_id, company_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating company: {e}")
        raise HTTPException(status_code=500, detail="Failed to update company")

@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Delete company (Admin only)
    """
    try:
        return await CompanyService.delete_company(company_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting company: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete company")

@router.post("/{company_id}/upload-logo")
async def upload_company_logo(
    company_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Upload company logo (Admin only)
    """
    try:
        return await CompanyService.upload_logo(company_id, file, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading company logo: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload company logo: {str(e)}")

@router.post("/{company_id}/gdrive/delete-ship-folder")
async def delete_ship_folder_from_gdrive(
    company_id: str,
    folder_data: dict,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Delete ship folder from Google Drive (Admin only)
    """
    try:
        from app.services.gdrive_service import GDriveService
        from app.repositories.gdrive_config_repository import GDriveConfigRepository
        import aiohttp
        
        # Validate request data
        ship_name = folder_data.get("ship_name")
        
        if not ship_name:
            raise HTTPException(status_code=400, detail="Missing ship_name")
        
        # Get company
        company = await CompanyService.get_company_by_id(company_id, current_user)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get company Google Drive configuration
        gdrive_config = await GDriveConfigRepository.get_by_company(company_id)
        if not gdrive_config:
            raise HTTPException(status_code=404, detail="Company Google Drive not configured")
        
        # Get Apps Script configuration
        apps_script_url = gdrive_config.get("web_app_url") or gdrive_config.get("apps_script_url")
        main_folder_id = gdrive_config.get("folder_id") or gdrive_config.get("main_folder_id")
        
        if not apps_script_url:
            raise HTTPException(status_code=400, detail="Apps Script URL not configured")
        
        if not main_folder_id:
            raise HTTPException(status_code=400, detail="Main folder ID not configured")
        
        # Call Apps Script to delete ship folder
        payload = {
            "action": "delete_complete_ship_structure",
            "parent_folder_id": main_folder_id,
            "ship_name": ship_name,
            "permanent_delete": False  # Move to trash by default for safety
        }
        
        logger.info(f"🗑️ Deleting ship folder '{ship_name}' from Google Drive for company {company_id}")
        
        # Make request to Apps Script
        async with aiohttp.ClientSession() as session:
            async with session.post(
                apps_script_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)  # Longer timeout for folder deletion
            ) as response:
                if response.status != 200:
                    logger.error(f"Apps Script request failed: {response.status}")
                    raise HTTPException(status_code=500, detail="Failed to delete ship folder")
                
                result = await response.json()
                
                if not result.get("success"):
                    logger.error(f"Apps Script returned error: {result.get('message', 'Unknown error')}")
                    # Don't fail if folder not found (may already be deleted)
                    if result.get("error_type") == "folder_not_found":
                        logger.info(f"Ship folder '{ship_name}' not found on Google Drive (may already be deleted)")
                        return {
                            "success": True,
                            "message": "Ship folder not found on Google Drive (may already be deleted)",
                            "ship_name": ship_name,
                            "warning": "Ship folder was not found on Google Drive"
                        }
                    else:
                        raise HTTPException(status_code=500, detail=f"Delete folder failed: {result.get('message', 'Unknown error')}")
                
                logger.info(f"✅ Ship folder '{ship_name}' deleted successfully from Google Drive")
                
                return {
                    "success": True,
                    "message": "Ship folder deleted successfully from Google Drive",
                    "ship_name": ship_name,
                    "folder_name": result.get("folder_name"),
                    "files_deleted": result.get("files_deleted", 0),
                    "subfolders_deleted": result.get("subfolders_deleted", 0),
                    "deleted_timestamp": result.get("deleted_timestamp")
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting ship folder from Google Drive: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete ship folder: {str(e)}")

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.models.user import UserResponse, UserRole
from app.models.gdrive_config import (
    GDriveProxyConfigRequest,
    GDriveSyncRequest,
    GDriveTestRequest
)
from app.services.gdrive_service import GDriveService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_admin_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has admin or higher permission"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin permission required")
    return current_user

@router.get("/status")
async def get_gdrive_status(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get Google Drive synchronization status
    """
    try:
        return await GDriveService.get_status(current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting GDrive status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Google Drive status")

@router.get("/config")
async def get_gdrive_config(
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Get Google Drive configuration (Admin+ role required)
    """
    try:
        return await GDriveService.get_config(current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting GDrive config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Google Drive configuration")

@router.post("/configure-proxy")
async def configure_gdrive_proxy(
    config: GDriveProxyConfigRequest,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Configure Google Drive with Apps Script proxy (Admin+ role required)
    """
    try:
        return await GDriveService.configure_proxy(config, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error configuring GDrive proxy: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure Google Drive")

@router.post("/configure")
async def configure_gdrive_service_account(
    service_account_json: str,
    folder_id: str,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Configure Google Drive with Service Account (Admin+ role required)
    """
    try:
        return await GDriveService.configure_service_account(
            service_account_json,
            folder_id,
            current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error configuring GDrive service account: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure Google Drive")

@router.post("/test")
async def test_gdrive_connection(
    test_request: Optional[GDriveTestRequest] = None,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Test Google Drive connection (Admin+ role required)
    """
    try:
        service_account_json = test_request.service_account_json if test_request else None
        folder_id = test_request.folder_id if test_request else None
        
        return await GDriveService.test_connection(
            current_user,
            service_account_json,
            folder_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error testing GDrive connection: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.post("/sync-to-drive")
async def sync_to_gdrive(
    sync_request: Optional[GDriveSyncRequest] = None,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Sync local data to Google Drive - Backup (Admin+ role required)
    """
    try:
        return await GDriveService.sync_to_drive(current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error syncing to GDrive: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync to Google Drive")

@router.post("/sync-from-drive")
async def sync_from_gdrive(
    sync_request: Optional[GDriveSyncRequest] = None,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Sync data from Google Drive to local - Restore (Admin+ role required)
    """
    try:
        return await GDriveService.sync_from_drive(current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error syncing from GDrive: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync from Google Drive")

# OAuth endpoints placeholder (for future implementation)
@router.post("/oauth/authorize")
async def oauth_authorize(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    folder_id: str,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Start OAuth authorization flow (Admin+ role required)
    TODO: Implement OAuth flow
    """
    return {
        "success": False,
        "message": "OAuth flow not yet implemented. Please use Apps Script or Service Account method."
    }

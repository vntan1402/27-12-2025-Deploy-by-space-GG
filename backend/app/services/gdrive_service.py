import logging
import os
import json
import io
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import requests

from app.models.user import UserResponse
from app.models.gdrive_config import (
    GDriveConfigCreate, 
    GDriveConfigUpdate, 
    GDriveConfigResponse,
    GDriveProxyConfigRequest
)
from app.repositories.gdrive_config_repository import GDriveConfigRepository

logger = logging.getLogger(__name__)

class GDriveService:
    """Service for Google Drive operations"""
    
    @staticmethod
    async def get_config(current_user: UserResponse) -> GDriveConfigResponse:
        """Get Google Drive configuration for current user's company"""
        try:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            config = await GDriveConfigRepository.get_by_company(current_user.company)
            
            if not config:
                # Create default config
                logger.info(f"No GDrive config found for company {current_user.company}, creating default")
                default_config = GDriveConfigCreate(
                    auth_method="apps_script"
                )
                config = await GDriveConfigRepository.create(
                    default_config,
                    current_user.company,
                    current_user.id
                )
            
            # Don't expose sensitive data
            response_config = config.copy()
            if response_config.get("service_account_json"):
                response_config["service_account_json"] = "***HIDDEN***"
            if response_config.get("client_secret"):
                response_config["client_secret"] = "***HIDDEN***"
            
            return GDriveConfigResponse(**response_config)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting GDrive config: {e}")
            raise HTTPException(status_code=500, detail="Failed to get Google Drive configuration")
    
    @staticmethod
    async def configure_proxy(
        proxy_config: GDriveProxyConfigRequest,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """Configure Google Drive with Apps Script proxy"""
        try:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Test connection to Apps Script
            test_payload = {
                "action": "test_connection",
                "parent_folder_id": proxy_config.folder_id
            }
            
            try:
                response = requests.post(
                    proxy_config.web_app_url,
                    json=test_payload,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                if not result.get("success"):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Apps Script test failed: {result.get('message', 'Unknown error')}"
                    )
            except requests.exceptions.RequestException as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to connect to Apps Script: {str(e)}"
                )
            
            # Update configuration
            update_data = GDriveConfigUpdate(
                auth_method="apps_script",
                web_app_url=proxy_config.web_app_url,
                folder_id=proxy_config.folder_id
            )
            
            existing_config = await GDriveConfigRepository.get_by_company(current_user.company)
            
            if existing_config:
                updated_config = await GDriveConfigRepository.update(
                    current_user.company,
                    update_data,
                    current_user.id
                )
            else:
                create_data = GDriveConfigCreate(
                    auth_method="apps_script",
                    web_app_url=proxy_config.web_app_url,
                    folder_id=proxy_config.folder_id
                )
                updated_config = await GDriveConfigRepository.create(
                    create_data,
                    current_user.company,
                    current_user.id
                )
            
            return {
                "success": True,
                "message": "Google Drive configured successfully with Apps Script",
                "config": GDriveConfigResponse(**updated_config)
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error configuring GDrive proxy: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to configure Google Drive: {str(e)}")
    
    @staticmethod
    async def configure_service_account(
        service_account_json: str,
        folder_id: str,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """Configure Google Drive with Service Account"""
        try:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Validate service account JSON
            try:
                credentials_dict = json.loads(service_account_json)
                if 'private_key' in credentials_dict:
                    credentials_dict['private_key'] = credentials_dict['private_key'].replace('\\n', '\n')
                
                scopes = ['https://www.googleapis.com/auth/drive']
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict, scopes=scopes
                )
                
                # Test connection
                service = build('drive', 'v3', credentials=credentials)
                service.files().list(q=f"parents in '{folder_id}'", pageSize=1).execute()
                
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid service account credentials: {str(e)}"
                )
            
            # Update configuration
            update_data = GDriveConfigUpdate(
                auth_method="service_account",
                service_account_json=service_account_json,
                folder_id=folder_id
            )
            
            existing_config = await GDriveConfigRepository.get_by_company(current_user.company)
            
            if existing_config:
                updated_config = await GDriveConfigRepository.update(
                    current_user.company,
                    update_data,
                    current_user.id
                )
            else:
                create_data = GDriveConfigCreate(
                    auth_method="service_account",
                    service_account_json=service_account_json,
                    folder_id=folder_id
                )
                updated_config = await GDriveConfigRepository.create(
                    create_data,
                    current_user.company,
                    current_user.id
                )
            
            return {
                "success": True,
                "message": "Google Drive configured successfully with Service Account",
                "config": GDriveConfigResponse(**updated_config)
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error configuring service account: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to configure Google Drive: {str(e)}")
    
    @staticmethod
    async def test_connection(
        current_user: UserResponse,
        service_account_json: Optional[str] = None,
        folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Test Google Drive connection"""
        try:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Use provided credentials or get from config
            if not service_account_json or not folder_id:
                config = await GDriveConfigRepository.get_by_company(current_user.company)
                if not config:
                    raise HTTPException(status_code=404, detail="Google Drive not configured")
                
                service_account_json = service_account_json or config.get("service_account_json")
                folder_id = folder_id or config.get("folder_id")
                auth_method = config.get("auth_method")
            else:
                auth_method = "service_account"
            
            if not folder_id:
                raise HTTPException(status_code=400, detail="Folder ID is required")
            
            # Test based on auth method
            if auth_method == "apps_script":
                config = await GDriveConfigRepository.get_by_company(current_user.company)
                web_app_url = config.get("web_app_url")
                if not web_app_url:
                    raise HTTPException(status_code=400, detail="Apps Script URL not configured")
                
                test_payload = {"action": "test_connection", "parent_folder_id": folder_id}
                response = requests.post(web_app_url, json=test_payload, timeout=30)
                response.raise_for_status()
                result = response.json()
                
                if result.get("success"):
                    return {
                        "success": True,
                        "message": "Google Drive connection successful (Apps Script)",
                        "method": "apps_script"
                    }
                else:
                    raise HTTPException(status_code=400, detail=result.get("message", "Connection test failed"))
            
            elif auth_method == "service_account" and service_account_json:
                credentials_dict = json.loads(service_account_json)
                if 'private_key' in credentials_dict:
                    credentials_dict['private_key'] = credentials_dict['private_key'].replace('\\n', '\n')
                
                scopes = ['https://www.googleapis.com/auth/drive']
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict, scopes=scopes
                )
                
                service = build('drive', 'v3', credentials=credentials)
                files = service.files().list(q=f"parents in '{folder_id}'", pageSize=5).execute()
                
                return {
                    "success": True,
                    "message": "Google Drive connection successful (Service Account)",
                    "method": "service_account",
                    "file_count": len(files.get("files", []))
                }
            
            else:
                raise HTTPException(status_code=400, detail="Invalid auth method or missing credentials")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error testing GDrive connection: {e}")
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}"
            }
    
    @staticmethod
    async def get_status(current_user: UserResponse) -> Dict[str, Any]:
        """Get Google Drive synchronization status"""
        try:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            config = await GDriveConfigRepository.get_by_company(current_user.company)
            
            if not config:
                return {
                    "configured": False,
                    "is_configured": False,
                    "last_sync": None,
                    "auth_method": None
                }
            
            return {
                "configured": config.get("is_configured", False),
                "is_configured": config.get("is_configured", False),
                "last_sync": config.get("last_sync"),
                "auth_method": config.get("auth_method"),
                "folder_id": config.get("folder_id")
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting GDrive status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get Google Drive status")
    
    @staticmethod
    async def sync_to_drive(current_user: UserResponse) -> Dict[str, Any]:
        """Sync local data to Google Drive (Backup)"""
        try:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            config = await GDriveConfigRepository.get_by_company(current_user.company)
            
            if not config or not config.get("is_configured"):
                raise HTTPException(status_code=400, detail="Google Drive not configured")
            
            # TODO: Implement actual sync logic based on auth method
            # For now, return placeholder
            
            await GDriveConfigRepository.update_last_sync(current_user.company)
            
            return {
                "success": True,
                "message": "Sync to Google Drive initiated",
                "files_synced": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error syncing to GDrive: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to sync to Google Drive: {str(e)}")
    
    @staticmethod
    async def sync_from_drive(current_user: UserResponse) -> Dict[str, Any]:
        """Sync data from Google Drive to local (Restore)"""
        try:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            config = await GDriveConfigRepository.get_by_company(current_user.company)
            
            if not config or not config.get("is_configured"):
                raise HTTPException(status_code=400, detail="Google Drive not configured")
            
            # TODO: Implement actual sync logic based on auth method
            # For now, return placeholder
            
            await GDriveConfigRepository.update_last_sync(current_user.company)
            
            return {
                "success": True,
                "message": "Sync from Google Drive initiated",
                "files_restored": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error syncing from GDrive: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to sync from Google Drive: {str(e)}")
    
    @staticmethod
    async def get_file_view_url(file_id: str, current_user: UserResponse) -> Dict[str, Any]:
        """Get Google Drive file view URL for opening in new window"""
        try:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Get company-specific Google Drive configuration
            config = await GDriveConfigRepository.get_by_company(current_user.company)
            
            if not config:
                # Fallback to standard Google Drive view URL
                view_url = f"https://drive.google.com/file/d/{file_id}/view"
                return {"success": True, "view_url": view_url}
            
            # Determine auth method and script URL
            auth_method = config.get("auth_method", "apps_script")
            script_url = config.get("web_app_url") or config.get("apps_script_url")
            
            if auth_method == "apps_script" and script_url:
                try:
                    # Get file view URL from Apps Script
                    payload = {
                        "action": "get_file_view_url",
                        "file_id": file_id
                    }
                    
                    logger.info(f"Requesting file view URL from Apps Script for file: {file_id}")
                    response = requests.post(script_url, json=payload, timeout=30)
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    if result.get("success") and result.get("view_url"):
                        return {"success": True, "view_url": result.get("view_url")}
                    else:
                        # Fallback to standard Google Drive view URL
                        view_url = f"https://drive.google.com/file/d/{file_id}/view"
                        return {"success": True, "view_url": view_url}
                        
                except Exception as e:
                    logger.error(f"Apps Script file view URL failed: {e}")
                    # Fallback to standard Google Drive view URL
                    view_url = f"https://drive.google.com/file/d/{file_id}/view"
                    return {"success": True, "view_url": view_url}
            else:
                # Fallback to standard Google Drive view URL
                view_url = f"https://drive.google.com/file/d/{file_id}/view"
                return {"success": True, "view_url": view_url}
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting Google Drive file view URL: {e}")
            # Final fallback
            view_url = f"https://drive.google.com/file/d/{file_id}/view"
            return {"success": True, "view_url": view_url}
    
    @staticmethod
    async def get_file_download_url(file_id: str, current_user: UserResponse) -> Dict[str, Any]:
        """Get Google Drive file download URL"""
        try:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Get company-specific Google Drive configuration
            config = await GDriveConfigRepository.get_by_company(current_user.company)
            
            if not config:
                # Fallback to standard Google Drive download URL
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                return {"success": True, "download_url": download_url}
            
            # Determine auth method and script URL
            auth_method = config.get("auth_method", "apps_script")
            script_url = config.get("web_app_url") or config.get("apps_script_url")
            
            if auth_method == "apps_script" and script_url:
                try:
                    # Get file download URL from Apps Script
                    payload = {
                        "action": "get_file_download_url",
                        "file_id": file_id
                    }
                    
                    logger.info(f"Requesting file download URL from Apps Script for file: {file_id}")
                    response = requests.post(script_url, json=payload, timeout=30)
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    if result.get("success") and result.get("download_url"):
                        return {"success": True, "download_url": result.get("download_url")}
                    else:
                        # Fallback to standard Google Drive download URL
                        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                        return {"success": True, "download_url": download_url}
                        
                except Exception as e:
                    logger.error(f"Apps Script file download URL failed: {e}")
                    # Fallback to standard Google Drive download URL
                    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    return {"success": True, "download_url": download_url}
            else:
                # Fallback to standard Google Drive download URL
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                return {"success": True, "download_url": download_url}
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting Google Drive file download URL: {e}")
            # Final fallback
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            return {"success": True, "download_url": download_url}
    
    @staticmethod
    async def delete_file(file_id: str, company_id: str, permanent_delete: bool = False) -> Dict[str, Any]:
        """
        Delete file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            company_id: Company ID for config lookup
            permanent_delete: If True, permanently delete. If False, move to trash.
            
        Returns:
            dict with success status and message
        """
        try:
            if not file_id:
                return {"success": False, "message": "No file ID provided"}
            
            if not company_id:
                return {"success": False, "message": "No company ID provided"}
            
            logger.info(f"🗑️ Attempting to delete file {file_id} from Google Drive")
            logger.info(f"🔍 DEBUG - Delete file: company_id = {company_id}, file_id = {file_id}")
            
            # Get company Google Drive configuration
            config = await GDriveConfigRepository.get_by_company(company_id)
            logger.info(f"🔍 DEBUG - GDrive config found: {config is not None}")
            
            if not config:
                logger.warning("⚠️ No Google Drive configuration found for company")
                return {"success": False, "message": "No Google Drive configuration found"}
            
            # Determine auth method and script URL
            auth_method = config.get("auth_method", "apps_script")
            script_url = config.get("web_app_url") or config.get("apps_script_url")
            
            if auth_method == "apps_script" and script_url:
                try:
                    # Call Apps Script to delete file
                    payload = {
                        "action": "delete_file",
                        "file_id": file_id,
                        "permanent_delete": permanent_delete
                    }
                    
                    response = requests.post(script_url, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            logger.info(f"✅ File {file_id} deleted from Google Drive successfully")
                            return {"success": True, "message": "File deleted successfully"}
                        else:
                            logger.warning(f"⚠️ Google Drive file deletion warning: {result.get('message')}")
                            return {"success": False, "message": result.get("message", "Unknown error")}
                    else:
                        logger.warning(f"⚠️ Failed to delete file from Google Drive: HTTP {response.status_code}")
                        return {"success": False, "message": f"HTTP {response.status_code}"}
                        
                except Exception as e:
                    logger.warning(f"⚠️ Google Drive deletion failed: {str(e)}")
                    return {"success": False, "message": str(e)}
            else:
                logger.warning("⚠️ No Apps Script URL configured for Google Drive deletion")
                return {"success": False, "message": "No Apps Script URL configured"}
                
        except Exception as e:
            logger.error(f"Error deleting Google Drive file: {e}")
            return {"success": False, "message": str(e)}

"""
Google Drive Helper - Utilities for Google Drive operations
Adapted from V1's dual_apps_script_manager.py
"""

import logging
import httpx
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

class GoogleDriveHelper:
    """Helper class for Google Drive API operations via Apps Script"""
    
    def __init__(self, company_id: str):
        """
        Initialize with company-specific configuration
        
        Args:
            company_id: Company UUID to fetch Google Drive config
        """
        self.company_id = company_id
        self.apps_script_url = None
        self.folder_id = None
    
    async def load_config(self):
        """Load Google Drive configuration from database"""
        from app.db.mongodb import mongo_db
        
        # Get company's Google Drive configuration from company_gdrive_config collection
        # This matches how Audit Certificate module accesses the config
        gdrive_config = await mongo_db.find_one("company_gdrive_config", {"company_id": self.company_id})
        
        if not gdrive_config:
            raise ValueError(f"Google Drive configuration not found for company {self.company_id}")
        
        # Use web_app_url (actual field name in DB) not apps_script_url
        self.apps_script_url = gdrive_config.get('web_app_url')
        self.folder_id = gdrive_config.get('folder_id')
        
        if not self.apps_script_url:
            raise ValueError("Google Apps Script URL not configured for company")
        
        if not self.folder_id:
            raise ValueError("Google Drive folder ID not configured for company")
        
        logger.info(f"✅ Google Drive config loaded for company {self.company_id}")
        logger.info(f"   📁 Folder ID: {self.folder_id}")
        logger.info(f"   🔗 Apps Script URL: {self.apps_script_url[:50]}...")
    
    async def call_apps_script(self, payload: Dict, timeout: float = 90.0) -> Dict:
        """
        Call Google Apps Script with given payload
        
        Args:
            payload: Action and data to send to Apps Script
            timeout: Request timeout in seconds
            
        Returns:
            Response from Apps Script
        """
        if not self.apps_script_url:
            await self.load_config()
        
        try:
            logger.info(f"📞 Calling Apps Script: {payload.get('action')}")
            
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.post(
                    self.apps_script_url,
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result.get('success'):
                    logger.info(f"✅ Apps Script response: SUCCESS")
                    logger.info(f"   📦 Response data: {result}")
                else:
                    logger.warning(f"⚠️ Apps Script response: {result.get('message', 'Unknown error')}")
                
                return result
                
        except httpx.TimeoutException:
            logger.error("❌ Apps Script call timed out")
            return {
                "success": False,
                "message": "Google Apps Script timeout",
                "error": "TIMEOUT"
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Apps Script HTTP error: {e.response.status_code}")
            return {
                "success": False,
                "message": f"HTTP {e.response.status_code}: {e.response.text}",
                "error": "HTTP_ERROR"
            }
        except Exception as e:
            logger.error(f"❌ Apps Script call failed: {e}")
            return {
                "success": False,
                "message": str(e),
                "error": str(type(e).__name__)
            }
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        folder_path: str,
        mime_type: str = 'application/octet-stream'
    ) -> Optional[str]:
        """
        Upload a file to Google Drive
        
        Args:
            file_content: File content as bytes
            filename: Name of the file
            folder_path: Path within company folder (e.g., "BROTHER 36/Passport")
            mime_type: MIME type of the file
            
        Returns:
            File ID if successful, None otherwise
        """
        import base64
        
        logger.info(f"📤 Uploading file: {filename}")
        logger.info(f"   📁 Folder path: {folder_path}")
        logger.info(f"   📊 Size: {len(file_content)} bytes")
        logger.info(f"   🎭 MIME type: {mime_type}")
        
        # Parse folder_path to match Apps Script expected format
        # Expected: "ShipName/ParentCategory/Category" e.g. "BROTHER 36/Crew Records/Crew List"
        path_parts = folder_path.split('/')
        if len(path_parts) >= 3:
            ship_name = path_parts[0]
            parent_category = path_parts[1]
            category = path_parts[2]
        elif len(path_parts) == 2:
            # For COMPANY DOCUMENT/Standby Crew
            ship_name = path_parts[0]
            parent_category = path_parts[1]
            category = ""
        else:
            raise ValueError(f"Invalid folder_path format: {folder_path}")
        
        payload = {
            "action": "upload_file_with_folder_creation",
            "parent_folder_id": self.folder_id,
            "ship_name": ship_name,
            "parent_category": parent_category,
            "category": category,
            "filename": filename,
            "file_content": base64.b64encode(file_content).decode('utf-8'),
            "content_type": mime_type
        }
        
        result = await self.call_apps_script(payload, timeout=120.0)
        
        if result.get('success'):
            file_id = result.get('file_id')
            logger.info(f"✅ File uploaded successfully: {filename}")
            logger.info(f"   🆔 File ID: {file_id}")
            return file_id
        else:
            logger.error(f"❌ File upload failed: {result.get('message')}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"🗑️ Deleting file: {file_id}")
        
        payload = {
            "action": "delete_file",
            "file_id": file_id
        }
        
        result = await self.call_apps_script(payload)
        success = result.get('success', False)
        
        if success:
            logger.info(f"✅ File deleted successfully")
        else:
            logger.error(f"❌ File deletion failed: {result.get('message')}")
        
        return success
    
    async def rename_file(self, file_id: str, new_name: str) -> bool:
        """
        Rename a file in Google Drive
        
        Args:
            file_id: Google Drive file ID
            new_name: New filename
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"✏️ Renaming file: {file_id}")
        logger.info(f"   📝 New name: {new_name}")
        
        payload = {
            "action": "rename_file",
            "file_id": file_id,
            "new_name": new_name
        }
        
        result = await self.call_apps_script(payload)
        success = result.get('success', False)
        
        if success:
            logger.info(f"✅ File renamed successfully")
        else:
            logger.error(f"❌ File rename failed: {result.get('message')}")
        
        return success

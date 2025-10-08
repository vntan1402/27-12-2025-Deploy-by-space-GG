"""
Company Google Drive Manager
Handles direct file upload to Company Google Drive using Service Account
"""
import io
import os
import json
import logging
from typing import Optional, Dict, Any
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class CompanyDriveManager:
    """
    Manages direct file uploads to Company Google Drive
    Uses Service Account for authentication
    """
    
    def __init__(self, service_account_info: Dict[str, Any], company_folder_id: str):
        """
        Initialize Company Drive Manager
        
        Args:
            service_account_info: Service account credentials as dict
            company_folder_id: ID of the company's root folder in Google Drive
        """
        try:
            self.credentials = Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            self.service = build('drive', 'v3', credentials=self.credentials)
            self.company_folder_id = company_folder_id
            logger.info("✅ Company Google Drive Manager initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Company Drive Manager: {e}")
            raise
    
    def find_or_create_folder(self, parent_folder_id: str, folder_name: str) -> str:
        """
        Find existing folder or create new one
        
        Args:
            parent_folder_id: ID of parent folder
            folder_name: Name of folder to find/create
            
        Returns:
            str: Folder ID
        """
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and parents in '{parent_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                logger.info(f"📁 Found existing folder '{folder_name}': {folder_id}")
                return folder_id
            
            # Create new folder if not found
            folder_metadata = {
                'name': folder_name,
                'parents': [parent_folder_id],
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id, name'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"✅ Created new folder '{folder_name}': {folder_id}")
            return folder_id
            
        except HttpError as e:
            logger.error(f"❌ Error finding/creating folder '{folder_name}': {e}")
            raise
    
    def create_folder_structure(self, folder_path: str) -> str:
        """
        Create nested folder structure
        
        Args:
            folder_path: Path like "BROTHER 36/Crew records" or "SUMMARY"
            
        Returns:
            str: Final folder ID
        """
        try:
            current_folder_id = self.company_folder_id
            path_parts = folder_path.split('/')
            
            logger.info(f"📁 Creating folder structure: {folder_path}")
            
            for part in path_parts:
                if part.strip():  # Skip empty parts
                    current_folder_id = self.find_or_create_folder(current_folder_id, part.strip())
            
            logger.info(f"✅ Folder structure ready: {folder_path} -> {current_folder_id}")
            return current_folder_id
            
        except Exception as e:
            logger.error(f"❌ Error creating folder structure '{folder_path}': {e}")
            raise
    
    def upload_file(self, file_content: bytes, filename: str, folder_path: str, 
                   content_type: str = 'application/octet-stream') -> Dict[str, Any]:
        """
        Upload file to Company Google Drive
        
        Args:
            file_content: File content as bytes
            filename: Name of the file
            folder_path: Folder path like "BROTHER 36/Crew records" or "SUMMARY"
            content_type: MIME type of the file
            
        Returns:
            dict: Upload result with file ID and details
        """
        try:
            logger.info(f"📤 Starting file upload: {filename} -> {folder_path}")
            
            # Create folder structure
            folder_id = self.create_folder_structure(folder_path)
            
            # Prepare file content
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=content_type,
                resumable=True
            )
            
            # File metadata
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            # Upload file
            file_result = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, mimeType, createdTime, webViewLink'
            ).execute()
            
            file_id = file_result.get('id')
            file_size = file_result.get('size', 0)
            web_link = file_result.get('webViewLink')
            
            logger.info(f"✅ File uploaded successfully: {filename}")
            logger.info(f"   File ID: {file_id}")
            logger.info(f"   Size: {file_size} bytes")
            logger.info(f"   Folder: {folder_path}")
            
            return {
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'folder_path': folder_path,
                'folder_id': folder_id,
                'file_size': int(file_size) if file_size else 0,
                'web_link': web_link,
                'upload_method': 'backend_direct_upload',
                'upload_timestamp': file_result.get('createdTime')
            }
            
        except HttpError as e:
            logger.error(f"❌ Google Drive API error uploading {filename}: {e}")
            return {
                'success': False,
                'error': f"Google Drive API error: {e}",
                'filename': filename,
                'folder_path': folder_path
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error uploading {filename}: {e}")
            return {
                'success': False,
                'error': f"Upload error: {e}",
                'filename': filename,
                'folder_path': folder_path
            }
    
    def get_folder_info(self, folder_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a folder
        
        Args:
            folder_path: Folder path like "BROTHER 36/Crew records"
            
        Returns:
            dict: Folder information or None if not found
        """
        try:
            folder_id = self.create_folder_structure(folder_path)
            
            folder_info = self.service.files().get(
                fileId=folder_id,
                fields='id, name, parents, createdTime, modifiedTime, webViewLink'
            ).execute()
            
            return {
                'id': folder_info.get('id'),
                'name': folder_info.get('name'),
                'path': folder_path,
                'created': folder_info.get('createdTime'),
                'modified': folder_info.get('modifiedTime'),
                'web_link': folder_info.get('webViewLink')
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting folder info for '{folder_path}': {e}")
            return None
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Company Google Drive
        
        Returns:
            dict: Test result
        """
        try:
            logger.info("🔍 Testing Company Google Drive connection...")
            
            # Try to get company folder info
            folder_info = self.service.files().get(
                fileId=self.company_folder_id,
                fields='id, name, owners, createdTime'
            ).execute()
            
            logger.info("✅ Company Google Drive connection successful")
            
            return {
                'success': True,
                'company_folder_id': self.company_folder_id,
                'folder_name': folder_info.get('name'),
                'owners': folder_info.get('owners', []),
                'created': folder_info.get('createdTime'),
                'connection_method': 'service_account'
            }
            
        except HttpError as e:
            logger.error(f"❌ Company Google Drive connection failed: {e}")
            return {
                'success': False,
                'error': f"Connection failed: {e}",
                'company_folder_id': self.company_folder_id
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error testing connection: {e}")
            return {
                'success': False,
                'error': f"Unexpected error: {e}",
                'company_folder_id': self.company_folder_id
            }


def create_company_drive_manager(company_id: str) -> Optional[CompanyDriveManager]:
    """
    Factory function to create CompanyDriveManager instance
    
    Args:
        company_id: Company UUID
        
    Returns:
        CompanyDriveManager instance or None if setup incomplete
    """
    try:
        from mongodb_database import mongo_db
        
        # Get company Google Drive configuration
        company_config = mongo_db.find_one(
            "company_gdrive_config",
            {"company_id": company_id}
        )
        
        if not company_config:
            logger.warning(f"❌ No Google Drive config found for company: {company_id}")
            return None
        
        # Get service account info from environment or config
        service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not service_account_json:
            logger.warning("❌ GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")
            return None
        
        service_account_info = json.loads(service_account_json)
        company_folder_id = company_config.get('folder_id')
        
        if not company_folder_id:
            logger.warning(f"❌ No folder_id in Google Drive config for company: {company_id}")
            return None
        
        return CompanyDriveManager(service_account_info, company_folder_id)
        
    except Exception as e:
        logger.error(f"❌ Error creating CompanyDriveManager: {e}")
        return None
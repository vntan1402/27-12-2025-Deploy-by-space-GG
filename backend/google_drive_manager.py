import os
import json
import io
from typing import Dict, Any, Optional, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from datetime import datetime, timezone
import hashlib
import logging

logger = logging.getLogger(__name__)

class GoogleDriveManager:
    def __init__(self):
        self.service = None
        self.credentials = None
        self.folder_id = None
        self.is_configured = False
        self.local_data_path = "/app/backend/data"
        
        # Create local data directory
        os.makedirs(self.local_data_path, exist_ok=True)
        
        # Load configuration if exists
        self.load_configuration()

    def configure(self, service_account_json: str, folder_id: str) -> bool:
        """Configure Google Drive integration with service account credentials"""
        try:
            # Parse service account JSON
            credentials_dict = json.loads(service_account_json)
            
            # Create credentials from service account info
            scopes = ['https://www.googleapis.com/auth/drive']
            self.credentials = service_account.Credentials.from_service_account_info(
                credentials_dict, scopes=scopes
            )
            
            # Build Drive service
            self.service = build('drive', 'v3', credentials=self.credentials)
            self.folder_id = folder_id
            
            # Test connection by listing files
            self.service.files().list(q=f"parents in '{folder_id}'", pageSize=1).execute()
            
            # Save configuration
            config = {
                'service_account_json': service_account_json,
                'folder_id': folder_id,
                'configured_at': datetime.now(timezone.utc).isoformat()
            }
            
            config_path = os.path.join(self.local_data_path, 'gdrive_config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            self.is_configured = True
            logger.info("Google Drive configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure Google Drive: {e}")
            return False

    def load_configuration(self):
        """Load existing Google Drive configuration"""
        try:
            config_path = os.path.join(self.local_data_path, 'gdrive_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Reconfigure with saved settings
                if self.configure(config['service_account_json'], config['folder_id']):
                    logger.info("Google Drive configuration loaded from saved settings")
        except Exception as e:
            logger.error(f"Failed to load Google Drive configuration: {e}")

    def upload_file(self, local_path: str, drive_filename: str) -> Optional[str]:
        """Upload a file to Google Drive"""
        if not self.is_configured:
            logger.error("Google Drive not configured")
            return None
        
        try:
            file_metadata = {
                'name': drive_filename,
                'parents': [self.folder_id]
            }
            
            media = MediaIoBaseUpload(
                io.BytesIO(open(local_path, 'rb').read()),
                mimetype='application/octet-stream',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            logger.info(f"Uploaded {drive_filename} to Google Drive")
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Failed to upload file to Google Drive: {e}")
            return None

    def download_file(self, file_id: str, local_path: str) -> bool:
        """Download a file from Google Drive"""
        if not self.is_configured:
            logger.error("Google Drive not configured")
            return False
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            with open(local_path, 'wb') as f:
                f.write(fh.getbuffer())
            
            logger.info(f"Downloaded file from Google Drive to {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from Google Drive: {e}")
            return False

    def list_files(self) -> List[Dict[str, Any]]:
        """List files in the configured Google Drive folder"""
        if not self.is_configured:
            return []
        
        try:
            results = self.service.files().list(
                q=f"parents in '{self.folder_id}'",
                fields="files(id, name, modifiedTime, size)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            logger.error(f"Failed to list files from Google Drive: {e}")
            return []

    def sync_to_drive(self) -> bool:
        """Upload all local database files to Google Drive"""
        if not self.is_configured:
            logger.error("Google Drive not configured")
            return False
        
        try:
            # Files to sync
            files_to_sync = [
                'users.json',
                'ships.json', 
                'certificates.json',
                'company_settings.json'
            ]
            
            for filename in files_to_sync:
                local_path = os.path.join(self.local_data_path, filename)
                if os.path.exists(local_path):
                    # Check if file exists on Drive
                    drive_files = self.list_files()
                    existing_file = next((f for f in drive_files if f['name'] == filename), None)
                    
                    if existing_file:
                        # Update existing file
                        self._update_file(existing_file['id'], local_path)
                    else:
                        # Upload new file
                        self.upload_file(local_path, filename)
            
            logger.info("Sync to Google Drive completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync to Google Drive: {e}")
            return False

    def sync_from_drive(self) -> bool:
        """Download all database files from Google Drive to local"""
        if not self.is_configured:
            logger.error("Google Drive not configured")
            return False
        
        try:
            drive_files = self.list_files()
            
            for file_info in drive_files:
                if file_info['name'].endswith('.json'):
                    local_path = os.path.join(self.local_data_path, file_info['name'])
                    self.download_file(file_info['id'], local_path)
            
            logger.info("Sync from Google Drive completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync from Google Drive: {e}")
            return False

    def _update_file(self, file_id: str, local_path: str) -> bool:
        """Update an existing file on Google Drive"""
        try:
            media = MediaIoBaseUpload(
                io.BytesIO(open(local_path, 'rb').read()),
                mimetype='application/octet-stream',
                resumable=True
            )
            
            self.service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update file on Google Drive: {e}")
            return False

    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status"""
        if not self.is_configured:
            return {
                'configured': False,
                'last_sync': None,
                'local_files': 0,
                'drive_files': 0
            }
        
        # Count local files
        local_files = len([f for f in os.listdir(self.local_data_path) 
                          if f.endswith('.json')])
        
        # Count drive files
        drive_files = len(self.list_files())
        
        # Get last sync time from config
        last_sync = None
        try:
            config_path = os.path.join(self.local_data_path, 'gdrive_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    last_sync = config.get('last_sync')
        except:
            pass
        
        return {
            'configured': self.is_configured,
            'last_sync': last_sync,
            'local_files': local_files,
            'drive_files': drive_files,
            'folder_id': self.folder_id
        }

# Global instance
gdrive_manager = GoogleDriveManager()
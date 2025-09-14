import os
import json
import io
from typing import Dict, Any, Optional, List
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
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
        self.auth_method = None  # 'service_account' or 'oauth'
        self.local_data_path = "/app/backend/data"
        
        # OAuth specific
        self.client_config = None
        self.oauth_credentials = None
        
        # Create local data directory
        os.makedirs(self.local_data_path, exist_ok=True)
        
        # Load configuration if exists
        self.load_configuration()

    def configure_oauth(self, client_config: Dict[str, Any], oauth_credentials: Dict[str, Any], folder_id: str) -> bool:
        """Configure Google Drive integration with OAuth 2.0 credentials"""
        try:
            # Store client config for future token refresh
            self.client_config = client_config
            
            # Create credentials from OAuth token data
            self.oauth_credentials = Credentials(
                token=oauth_credentials.get('token'),
                refresh_token=oauth_credentials.get('refresh_token'),
                token_uri=oauth_credentials.get('token_uri'),
                client_id=oauth_credentials.get('client_id'),
                client_secret=oauth_credentials.get('client_secret'),
                scopes=oauth_credentials.get('scopes', ['https://www.googleapis.com/auth/drive.file'])
            )
            
            # Build Drive service
            self.service = build('drive', 'v3', credentials=self.oauth_credentials)
            self.folder_id = folder_id
            self.auth_method = 'oauth'
            
            # Test connection by listing files
            self.service.files().list(q=f"parents in '{folder_id}'", pageSize=1).execute()
            
            # Save configuration
            config = {
                'auth_method': 'oauth',
                'client_config': client_config,
                'oauth_credentials': {
                    'token': oauth_credentials.get('token'),
                    'refresh_token': oauth_credentials.get('refresh_token'),
                    'token_uri': oauth_credentials.get('token_uri'),
                    'client_id': oauth_credentials.get('client_id'),
                    'client_secret': oauth_credentials.get('client_secret'),
                    'scopes': oauth_credentials.get('scopes')
                },
                'folder_id': folder_id,
                'configured_at': datetime.now(timezone.utc).isoformat()
            }
            
            config_path = os.path.join(self.local_data_path, 'gdrive_config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.is_configured = True
            logger.info("Google Drive configured successfully with OAuth 2.0")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure Google Drive with OAuth: {e}")
            return False

    def get_oauth_authorization_url(self, client_config: Dict[str, Any]) -> tuple[str, str]:
        """Generate OAuth 2.0 authorization URL"""
        try:
            scopes = ['https://www.googleapis.com/auth/drive.file']
            
            # Create flow instance
            flow = Flow.from_client_config(
                client_config, 
                scopes=scopes
            )
            
            # Set redirect URI (this should match your registered redirect URI)
            flow.redirect_uri = client_config.get('redirect_uri', 'http://localhost:8000/oauth2callback')
            
            # Generate authorization URL
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # Store flow for later use
            self._temp_flow = flow
            
            return authorization_url, state
            
        except Exception as e:
            logger.error(f"Failed to generate OAuth authorization URL: {e}")
            return None, None

    def handle_oauth_callback(self, authorization_response: str) -> Dict[str, Any]:
        """Handle OAuth 2.0 callback and exchange code for tokens"""
        try:
            if not hasattr(self, '_temp_flow'):
                raise ValueError("No OAuth flow found. Call get_oauth_authorization_url first.")
            
            # Fetch token using authorization response
            self._temp_flow.fetch_token(authorization_response=authorization_response)
            
            # Get credentials
            credentials = self._temp_flow.credentials
            
            # Convert credentials to dict
            oauth_credentials = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            # Clean up temp flow
            delattr(self, '_temp_flow')
            
            return oauth_credentials
            
        except Exception as e:
            logger.error(f"Failed to handle OAuth callback: {e}")
            return None

    def configure(self, service_account_json: str = None, folder_id: str = None, client_config: Dict[str, Any] = None, oauth_credentials: Dict[str, Any] = None) -> bool:
        """Configure Google Drive integration with Service Account or OAuth credentials"""
        
        # OAuth configuration
        if client_config and oauth_credentials and folder_id:
            return self.configure_oauth(client_config, oauth_credentials, folder_id)
        
        # Service Account configuration (legacy)
        if service_account_json and folder_id:
            return self.configure_service_account(service_account_json, folder_id)
        
        raise ValueError("Invalid configuration parameters. Provide either OAuth or Service Account credentials.")

    def configure_service_account(self, service_account_json: str, folder_id: str) -> bool:
        """Configure Google Drive integration with service account credentials (legacy)"""
        try:
            # Parse service account JSON
            credentials_dict = json.loads(service_account_json)
            
            # Fix escaped newlines in private key
            if 'private_key' in credentials_dict:
                credentials_dict['private_key'] = credentials_dict['private_key'].replace('\\n', '\n')
            
            # Create credentials from service account info
            scopes = ['https://www.googleapis.com/auth/drive']
            self.credentials = service_account.Credentials.from_service_account_info(
                credentials_dict, scopes=scopes
            )
            
            # Build Drive service
            self.service = build('drive', 'v3', credentials=self.credentials)
            self.folder_id = folder_id
            self.auth_method = 'service_account'
            
            # Test connection by listing files
            self.service.files().list(q=f"parents in '{folder_id}'", pageSize=1).execute()
            
            # Save configuration
            config = {
                'auth_method': 'service_account',
                'service_account_json': service_account_json,
                'folder_id': folder_id,
                'configured_at': datetime.now(timezone.utc).isoformat()
            }
            
            config_path = os.path.join(self.local_data_path, 'gdrive_config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.is_configured = True
            logger.info("Google Drive configured successfully with Service Account")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure Google Drive with Service Account: {e}")
            return False
            
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
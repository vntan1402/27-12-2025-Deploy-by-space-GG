#!/usr/bin/env python3
"""
Google Drive API Direct Test
Test Google Drive API directly to verify the service account permissions issue
"""

import requests
import json
import sys
import os
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleDriveAPITester:
    def __init__(self, base_url="https://certmaster-ship.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.gdrive_service = None
        self.folder_id = None
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate(self):
        """Authenticate with the backend"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.log("✅ Authentication successful")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {e}")
            return False
    
    def get_gdrive_config(self):
        """Get Google Drive configuration from backend"""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(
                f"{self.api_url}/gdrive/config",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                config = response.json()
                self.folder_id = config.get('folder_id')
                self.log(f"✅ Got Google Drive config")
                self.log(f"Folder ID: {self.folder_id}")
                self.log(f"Service Account: {config.get('service_account_email')}")
                return config
            else:
                self.log(f"❌ Failed to get config: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Config retrieval error: {e}")
            return None
    
    def test_folder_access(self):
        """Test access to the Google Drive folder"""
        if not self.folder_id:
            self.log("❌ No folder ID available")
            return False
            
        try:
            # We need to get the service account JSON to test directly
            # Since it's not exposed via API, we'll use the GoogleDriveManager
            sys.path.append('/app/backend')
            from google_drive_manager import GoogleDriveManager
            
            gdrive_manager = GoogleDriveManager()
            
            if not gdrive_manager.is_configured:
                self.log("❌ Google Drive Manager not configured")
                return False
            
            # Test listing files in the folder
            self.log("Testing folder access...")
            files = gdrive_manager.list_files()
            self.log(f"✅ Successfully accessed folder")
            self.log(f"Files in folder: {len(files)}")
            
            # Test folder permissions by trying to get folder metadata
            try:
                folder_info = gdrive_manager.service.files().get(
                    fileId=self.folder_id,
                    fields="id,name,permissions,capabilities"
                ).execute()
                
                self.log(f"Folder name: {folder_info.get('name')}")
                self.log(f"Folder capabilities: {folder_info.get('capabilities', {})}")
                
                # Check if we can write to the folder
                capabilities = folder_info.get('capabilities', {})
                can_add_children = capabilities.get('canAddChildren', False)
                can_edit = capabilities.get('canEdit', False)
                
                self.log(f"Can add children: {can_add_children}")
                self.log(f"Can edit: {can_edit}")
                
                return True
                
            except HttpError as e:
                self.log(f"❌ Error accessing folder metadata: {e}")
                return False
                
        except Exception as e:
            self.log(f"❌ Folder access test error: {e}")
            return False
    
    def test_service_account_quota(self):
        """Test service account storage quota issue"""
        try:
            sys.path.append('/app/backend')
            from google_drive_manager import GoogleDriveManager
            
            gdrive_manager = GoogleDriveManager()
            
            if not gdrive_manager.is_configured:
                self.log("❌ Google Drive Manager not configured")
                return False
            
            # Try to get information about the service account
            try:
                about_info = gdrive_manager.service.about().get(
                    fields="user,storageQuota"
                ).execute()
                
                user_info = about_info.get('user', {})
                storage_quota = about_info.get('storageQuota', {})
                
                self.log(f"Service Account Email: {user_info.get('emailAddress')}")
                self.log(f"Display Name: {user_info.get('displayName')}")
                self.log(f"Storage Quota: {storage_quota}")
                
                # Check if this is the quota issue
                if not storage_quota or storage_quota.get('limit') == '0':
                    self.log("❌ CRITICAL ISSUE: Service Account has no storage quota!")
                    self.log("This is why files cannot be uploaded to Google Drive.")
                    return False
                else:
                    self.log("✅ Service Account has storage quota")
                    return True
                    
            except HttpError as e:
                if "storageQuotaExceeded" in str(e):
                    self.log("❌ CRITICAL ISSUE: Storage quota exceeded!")
                    self.log("Service Accounts do not have personal storage quota.")
                    return False
                else:
                    self.log(f"❌ Error getting service account info: {e}")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Service account quota test error: {e}")
            return False
    
    def test_shared_drive_detection(self):
        """Test if the folder is in a shared drive"""
        try:
            sys.path.append('/app/backend')
            from google_drive_manager import GoogleDriveManager
            
            gdrive_manager = GoogleDriveManager()
            
            if not gdrive_manager.is_configured:
                self.log("❌ Google Drive Manager not configured")
                return False
            
            # Check if the folder is in a shared drive
            try:
                folder_info = gdrive_manager.service.files().get(
                    fileId=self.folder_id,
                    fields="id,name,parents,driveId,teamDriveId"
                ).execute()
                
                drive_id = folder_info.get('driveId')
                team_drive_id = folder_info.get('teamDriveId')
                parents = folder_info.get('parents', [])
                
                self.log(f"Folder parents: {parents}")
                self.log(f"Drive ID: {drive_id}")
                self.log(f"Team Drive ID: {team_drive_id}")
                
                if drive_id or team_drive_id:
                    self.log("✅ Folder is in a Shared Drive")
                    return True
                else:
                    self.log("❌ Folder is NOT in a Shared Drive")
                    self.log("This is likely the root cause - service accounts need Shared Drives!")
                    return False
                    
            except HttpError as e:
                self.log(f"❌ Error checking shared drive status: {e}")
                return False
                
        except Exception as e:
            self.log(f"❌ Shared drive detection error: {e}")
            return False
    
    def test_upload_with_shared_drive(self):
        """Test upload using shared drive parameters"""
        try:
            sys.path.append('/app/backend')
            from google_drive_manager import GoogleDriveManager
            import io
            from googleapiclient.http import MediaIoBaseUpload
            
            gdrive_manager = GoogleDriveManager()
            
            if not gdrive_manager.is_configured:
                self.log("❌ Google Drive Manager not configured")
                return False
            
            # Create a test file
            test_content = json.dumps({
                "test": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "purpose": "Shared Drive Upload Test"
            }, indent=2)
            
            # Try upload with supportsAllDrives=True
            try:
                file_metadata = {
                    'name': 'test_shared_drive_upload.json',
                    'parents': [self.folder_id]
                }
                
                media = MediaIoBaseUpload(
                    io.BytesIO(test_content.encode()),
                    mimetype='application/json',
                    resumable=True
                )
                
                # Upload with shared drive support
                file = gdrive_manager.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name',
                    supportsAllDrives=True  # This is key for shared drives
                ).execute()
                
                self.log(f"✅ Successfully uploaded test file with Shared Drive support!")
                self.log(f"File ID: {file.get('id')}")
                self.log(f"File Name: {file.get('name')}")
                
                # Clean up - delete the test file
                gdrive_manager.service.files().delete(
                    fileId=file.get('id'),
                    supportsAllDrives=True
                ).execute()
                
                self.log("✅ Test file cleaned up")
                return True
                
            except HttpError as e:
                if "storageQuotaExceeded" in str(e):
                    self.log("❌ Still getting storage quota error even with Shared Drive support")
                    self.log("The folder may not be properly configured as a Shared Drive")
                else:
                    self.log(f"❌ Upload failed with Shared Drive support: {e}")
                return False
                
        except Exception as e:
            self.log(f"❌ Shared drive upload test error: {e}")
            return False
    
    def run_comprehensive_api_test(self):
        """Run comprehensive Google Drive API test"""
        self.log("🔍 GOOGLE DRIVE API COMPREHENSIVE TEST")
        self.log("=" * 60)
        
        # Step 1: Authentication
        self.log("=== STEP 1: AUTHENTICATION ===")
        if not self.authenticate():
            self.log("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Get Google Drive Configuration
        self.log("=== STEP 2: GET GOOGLE DRIVE CONFIGURATION ===")
        config = self.get_gdrive_config()
        if not config:
            self.log("❌ Cannot proceed without Google Drive configuration")
            return False
        
        # Step 3: Test Folder Access
        self.log("=== STEP 3: TEST FOLDER ACCESS ===")
        folder_access = self.test_folder_access()
        
        # Step 4: Test Service Account Quota
        self.log("=== STEP 4: TEST SERVICE ACCOUNT QUOTA ===")
        quota_ok = self.test_service_account_quota()
        
        # Step 5: Test Shared Drive Detection
        self.log("=== STEP 5: TEST SHARED DRIVE DETECTION ===")
        is_shared_drive = self.test_shared_drive_detection()
        
        # Step 6: Test Upload with Shared Drive Support
        self.log("=== STEP 6: TEST UPLOAD WITH SHARED DRIVE SUPPORT ===")
        shared_drive_upload = self.test_upload_with_shared_drive()
        
        # Summary
        self.log("=" * 60)
        self.log("📊 GOOGLE DRIVE API TEST RESULTS")
        self.log("=" * 60)
        
        results = [
            ("Authentication", True),
            ("Google Drive Configuration", config is not None),
            ("Folder Access", folder_access),
            ("Service Account Quota", quota_ok),
            ("Shared Drive Detection", is_shared_drive),
            ("Shared Drive Upload", shared_drive_upload)
        ]
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name:30} {status}")
        
        # Root Cause Analysis
        self.log("\n" + "=" * 60)
        self.log("🔍 ROOT CAUSE ANALYSIS")
        self.log("=" * 60)
        
        if not quota_ok:
            self.log("❌ CRITICAL ISSUE IDENTIFIED:")
            self.log("Service Accounts do not have personal storage quota in Google Drive.")
            self.log("This is why the uploads are failing with 'storageQuotaExceeded' error.")
            self.log("")
            self.log("SOLUTIONS:")
            self.log("1. Use a Shared Drive (Google Workspace) instead of personal Drive")
            self.log("2. Use OAuth delegation with a real user account")
            self.log("3. Configure the folder to be in a Shared Drive")
            
        if not is_shared_drive:
            self.log("❌ FOLDER CONFIGURATION ISSUE:")
            self.log("The target folder is not in a Shared Drive.")
            self.log("Service accounts can only upload to Shared Drives, not personal drives.")
            
        if shared_drive_upload:
            self.log("✅ SHARED DRIVE UPLOAD WORKS:")
            self.log("Upload with supportsAllDrives=True parameter works!")
            self.log("The GoogleDriveManager needs to be updated to use this parameter.")
        
        return all(result for _, result in results)

def main():
    """Main execution"""
    tester = GoogleDriveAPITester()
    success = tester.run_comprehensive_api_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
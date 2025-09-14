#!/usr/bin/env python3
"""
Google Drive Upload Debug Test
Comprehensive testing of Google Drive sync functionality to debug actual upload issues
"""

import requests
import json
import os
import time
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleDriveDebugTester:
    def __init__(self, base_url="https://shipdesk.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.gdrive_config = None
        self.gdrive_service = None
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_api_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        self.log(f"Testing {name}...")
        self.log(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    self.log(f"Error: {error_detail}")
                except:
                    self.log(f"Error: {response.text}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}")
            return False, {}

    def test_authentication(self):
        """Test authentication with admin credentials"""
        self.log("=== STEP 1: AUTHENTICATION ===")
        
        success, response = self.run_api_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_info = response.get('user', {})
            self.log(f"✅ Authentication successful")
            self.log(f"User: {user_info.get('full_name')} ({user_info.get('role')})")
            return True
        else:
            self.log("❌ Authentication failed")
            return False

    def test_gdrive_configuration(self):
        """Test Google Drive configuration retrieval"""
        self.log("=== STEP 2: GOOGLE DRIVE CONFIGURATION ===")
        
        # Get current configuration
        success, config = self.run_api_test(
            "Get Google Drive Config",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            self.gdrive_config = config
            self.log(f"Configuration Status: {config.get('configured')}")
            self.log(f"Folder ID: {config.get('folder_id')}")
            self.log(f"Service Account: {config.get('service_account_email')}")
            self.log(f"Last Sync: {config.get('last_sync')}")
            return config.get('configured', False)
        
        return False

    def test_gdrive_status(self):
        """Test Google Drive status"""
        self.log("=== STEP 3: GOOGLE DRIVE STATUS ===")
        
        success, status = self.run_api_test(
            "Get Google Drive Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            self.log(f"Configured: {status.get('configured')}")
            self.log(f"Local Files: {status.get('local_files')}")
            self.log(f"Drive Files: {status.get('drive_files')}")
            self.log(f"Last Sync: {status.get('last_sync')}")
            return True
        
        return False

    def test_data_export(self):
        """Test data export to JSON files"""
        self.log("=== STEP 4: DATA EXPORT VERIFICATION ===")
        
        # Check if data directory exists and has files
        data_path = "/app/backend/data"
        if not os.path.exists(data_path):
            self.log(f"❌ Data directory does not exist: {data_path}")
            return False
        
        json_files = [f for f in os.listdir(data_path) if f.endswith('.json')]
        self.log(f"Found {len(json_files)} JSON files in {data_path}")
        
        total_records = 0
        for json_file in json_files:
            file_path = os.path.join(data_path, json_file)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    record_count = len(data) if isinstance(data, list) else 1
                    total_records += record_count
                    self.log(f"  {json_file}: {record_count} records")
            except Exception as e:
                self.log(f"  ❌ Error reading {json_file}: {e}")
        
        self.log(f"Total records across all files: {total_records}")
        return len(json_files) > 0

    def initialize_gdrive_service(self):
        """Initialize Google Drive service directly"""
        self.log("=== STEP 5: DIRECT GOOGLE DRIVE SERVICE INITIALIZATION ===")
        
        if not self.gdrive_config or not self.gdrive_config.get('configured'):
            self.log("❌ Google Drive not configured")
            return False
        
        try:
            # Get service account JSON from backend
            # We need to make a request to get the actual service account JSON
            # Since it's not exposed in the config endpoint for security
            
            # For now, let's try to get it from the database directly
            # This is a debug approach - in production, credentials should be handled securely
            
            self.log("⚠️ Cannot initialize direct Google Drive service without service account JSON")
            self.log("Service account JSON is not exposed via API for security reasons")
            return False
            
        except Exception as e:
            self.log(f"❌ Failed to initialize Google Drive service: {e}")
            return False

    def test_sync_to_drive_api(self):
        """Test sync to drive via API"""
        self.log("=== STEP 6: SYNC TO DRIVE API TEST ===")
        
        success, response = self.run_api_test(
            "Sync To Drive",
            "POST",
            "gdrive/sync-to-drive",
            200
        )
        
        if success:
            self.log(f"✅ Sync API call successful")
            self.log(f"Response: {response}")
            return True
        else:
            self.log(f"❌ Sync API call failed")
            return False

    def test_drive_files_count_after_sync(self):
        """Test drive files count after sync"""
        self.log("=== STEP 7: VERIFY FILES ON GOOGLE DRIVE AFTER SYNC ===")
        
        # Wait a moment for sync to complete
        time.sleep(2)
        
        success, status = self.run_api_test(
            "Get Google Drive Status After Sync",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            drive_files = status.get('drive_files', 0)
            local_files = status.get('local_files', 0)
            
            self.log(f"Local Files: {local_files}")
            self.log(f"Drive Files: {drive_files}")
            
            if drive_files > 0:
                self.log(f"✅ Files found on Google Drive: {drive_files}")
                return True
            else:
                self.log(f"❌ No files found on Google Drive despite sync")
                return False
        
        return False

    def test_individual_file_upload_simulation(self):
        """Simulate individual file upload process"""
        self.log("=== STEP 8: INDIVIDUAL FILE UPLOAD SIMULATION ===")
        
        # Create a test JSON file
        test_data = {
            "test_upload": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "purpose": "Google Drive upload test"
        }
        
        test_file_path = "/tmp/test_upload.json"
        try:
            with open(test_file_path, 'w') as f:
                json.dump(test_data, f, indent=2)
            
            self.log(f"✅ Created test file: {test_file_path}")
            
            # Check file size
            file_size = os.path.getsize(test_file_path)
            self.log(f"Test file size: {file_size} bytes")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to create test file: {e}")
            return False

    def check_backend_logs(self):
        """Check backend logs for Google Drive related errors"""
        self.log("=== STEP 9: BACKEND LOGS ANALYSIS ===")
        
        try:
            # Check supervisor logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"Checking {log_file}...")
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        # Get last 20 lines
                        recent_lines = lines[-20:] if len(lines) > 20 else lines
                        
                        gdrive_related = [line for line in recent_lines 
                                        if any(keyword in line.lower() for keyword in 
                                              ['google', 'drive', 'sync', 'upload', 'pem', 'credential'])]
                        
                        if gdrive_related:
                            self.log(f"Google Drive related log entries:")
                            for line in gdrive_related:
                                self.log(f"  {line.strip()}")
                        else:
                            self.log(f"No recent Google Drive related entries in {log_file}")
                else:
                    self.log(f"Log file not found: {log_file}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {e}")
            return False

    def test_google_drive_manager_directly(self):
        """Test Google Drive Manager directly"""
        self.log("=== STEP 10: DIRECT GOOGLE DRIVE MANAGER TEST ===")
        
        try:
            # Import the Google Drive Manager
            import sys
            sys.path.append('/app/backend')
            from google_drive_manager import GoogleDriveManager
            
            gdrive_manager = GoogleDriveManager()
            
            # Check if it's configured
            self.log(f"Google Drive Manager configured: {gdrive_manager.is_configured}")
            self.log(f"Folder ID: {gdrive_manager.folder_id}")
            
            if gdrive_manager.is_configured:
                # Try to list files
                files = gdrive_manager.list_files()
                self.log(f"Files found via direct manager: {len(files)}")
                
                for file_info in files[:5]:  # Show first 5 files
                    self.log(f"  File: {file_info.get('name')} (ID: {file_info.get('id')})")
                
                # Try sync
                self.log("Attempting direct sync...")
                sync_result = gdrive_manager.sync_to_drive()
                self.log(f"Direct sync result: {sync_result}")
                
                return sync_result
            else:
                self.log("❌ Google Drive Manager not configured")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Google Drive Manager directly: {e}")
            return False

    def run_comprehensive_debug(self):
        """Run comprehensive Google Drive debug test"""
        self.log("🔍 GOOGLE DRIVE UPLOAD DEBUG TEST")
        self.log("=" * 60)
        
        test_results = []
        
        # Step 1: Authentication
        test_results.append(("Authentication", self.test_authentication()))
        if not test_results[-1][1]:
            self.log("❌ Cannot proceed without authentication")
            return self.print_results(test_results)
        
        # Step 2: Google Drive Configuration
        test_results.append(("Google Drive Configuration", self.test_gdrive_configuration()))
        
        # Step 3: Google Drive Status
        test_results.append(("Google Drive Status", self.test_gdrive_status()))
        
        # Step 4: Data Export Verification
        test_results.append(("Data Export Verification", self.test_data_export()))
        
        # Step 5: Direct Google Drive Service (may not work due to security)
        test_results.append(("Direct Google Drive Service", self.initialize_gdrive_service()))
        
        # Step 6: Sync to Drive API
        test_results.append(("Sync To Drive API", self.test_sync_to_drive_api()))
        
        # Step 7: Verify Files After Sync
        test_results.append(("Verify Files After Sync", self.test_drive_files_count_after_sync()))
        
        # Step 8: Individual File Upload Simulation
        test_results.append(("Individual File Upload Simulation", self.test_individual_file_upload_simulation()))
        
        # Step 9: Backend Logs Analysis
        test_results.append(("Backend Logs Analysis", self.check_backend_logs()))
        
        # Step 10: Direct Google Drive Manager Test
        test_results.append(("Direct Google Drive Manager Test", self.test_google_drive_manager_directly()))
        
        return self.print_results(test_results)

    def print_results(self, test_results):
        """Print comprehensive test results"""
        self.log("=" * 60)
        self.log("📊 GOOGLE DRIVE DEBUG TEST RESULTS")
        self.log("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name:35} {status}")
            if result:
                passed_tests += 1
        
        self.log(f"\nAPI Tests: {self.tests_passed}/{self.tests_run}")
        self.log(f"Feature Tests: {passed_tests}/{total_tests}")
        
        # Summary and recommendations
        self.log("\n" + "=" * 60)
        self.log("🔍 DEBUG ANALYSIS & RECOMMENDATIONS")
        self.log("=" * 60)
        
        if passed_tests < total_tests:
            self.log("❌ ISSUES IDENTIFIED:")
            
            for test_name, result in test_results:
                if not result:
                    if "Authentication" in test_name:
                        self.log("  - Authentication failed - check admin credentials")
                    elif "Configuration" in test_name:
                        self.log("  - Google Drive not configured - check service account setup")
                    elif "Status" in test_name:
                        self.log("  - Google Drive status API issues")
                    elif "Data Export" in test_name:
                        self.log("  - Data export to JSON files failed")
                    elif "Sync" in test_name:
                        self.log("  - Sync to Google Drive failed - check credentials and permissions")
                    elif "Files After Sync" in test_name:
                        self.log("  - Files not appearing on Google Drive - sync not working properly")
                    elif "Direct Google Drive" in test_name:
                        self.log("  - Direct Google Drive access issues - check service account permissions")
        else:
            self.log("✅ All tests passed - Google Drive integration appears to be working")
        
        return passed_tests == total_tests

def main():
    """Main execution"""
    tester = GoogleDriveDebugTester()
    success = tester.run_comprehensive_debug()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
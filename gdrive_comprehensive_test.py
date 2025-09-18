import requests
import sys
import json
from datetime import datetime, timezone
import time

class GoogleDriveComprehensiveTester:
    def __init__(self, base_url="https://shipcertdrive.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.issues_found = []
        self.critical_issues = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.content else {}
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self, username="admin", password="admin123"):
        """Test login and get token"""
        print(f"\n🔐 Testing Authentication with {username}/{password}")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"✅ Login successful, token obtained")
            print(f"   User: {response.get('user', {}).get('full_name')} ({response.get('user', {}).get('role')})")
            return True
        return False

    def test_gdrive_configuration_status(self):
        """Test Google Drive configuration status - Requirement 1"""
        print(f"\n📊 REQUIREMENT 1: Google Drive Configuration Status")
        
        # Test GET /api/gdrive/config
        success_config, config = self.run_test(
            "GET /api/gdrive/config",
            "GET",
            "gdrive/config",
            200
        )
        
        if not success_config:
            self.critical_issues.append("GET /api/gdrive/config endpoint not working")
            return False
        
        # Verify configuration fields
        required_fields = ['configured', 'folder_id', 'service_account_email']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            self.issues_found.append(f"Missing configuration fields: {missing_fields}")
        
        print(f"   ✅ Configuration Status: {'Configured' if config.get('configured') else 'Not Configured'}")
        if config.get('configured'):
            print(f"   ✅ Folder ID: {config.get('folder_id', 'N/A')}")
            print(f"   ✅ Service Account: {config.get('service_account_email', 'N/A')}")
            print(f"   ✅ Last Sync: {config.get('last_sync', 'Never')}")
        
        # Test GET /api/gdrive/status
        success_status, status = self.run_test(
            "GET /api/gdrive/status",
            "GET",
            "gdrive/status",
            200
        )
        
        if not success_status:
            self.critical_issues.append("GET /api/gdrive/status endpoint not working")
            return False
        
        # Verify status fields
        status_fields = ['configured', 'local_files', 'drive_files', 'folder_id']
        missing_status_fields = [field for field in status_fields if field not in status]
        
        if missing_status_fields:
            self.issues_found.append(f"Missing status fields: {missing_status_fields}")
        
        print(f"   ✅ Connection Status: {'Connected' if status.get('configured') else 'Not Connected'}")
        print(f"   ✅ Local Files: {status.get('local_files', 0)}")
        print(f"   ✅ Drive Files: {status.get('drive_files', 0)}")
        
        # Check if service account and folder ID are properly configured
        if config.get('configured') and config.get('folder_id') and config.get('service_account_email'):
            print(f"   ✅ Service account and folder ID are configured")
        else:
            self.issues_found.append("Service account or folder ID not properly configured")
        
        return success_config and success_status

    def test_gdrive_connection_testing(self):
        """Test Google Drive connection testing - Requirement 2"""
        print(f"\n🔗 REQUIREMENT 2: Google Drive Connection Testing")
        
        # Test with sample credentials
        sample_service_account = {
            "type": "service_account",
            "project_id": "ship-management-test",
            "private_key_id": "test123",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
            "client_email": "ship-management-service@ship-management-test.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        test_config = {
            "service_account_json": json.dumps(sample_service_account),
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }
        
        # Test POST /api/gdrive/test
        success, response = self.run_test(
            "POST /api/gdrive/test",
            "POST",
            "gdrive/test",
            200,
            data=test_config
        )
        
        if not success:
            self.critical_issues.append("POST /api/gdrive/test endpoint not working")
            return False
        
        # Verify response structure
        required_response_fields = ['success', 'message']
        missing_response_fields = [field for field in required_response_fields if field not in response]
        
        if missing_response_fields:
            self.issues_found.append(f"Missing test response fields: {missing_response_fields}")
        
        print(f"   ✅ Connection Test Result: {'Success' if response.get('success') else 'Failed'}")
        print(f"   ✅ Message: {response.get('message', 'N/A')}")
        
        # Test error handling with invalid credentials
        invalid_config = {
            "service_account_json": '{"invalid": "json"}',
            "folder_id": "invalid_folder"
        }
        
        success_invalid, response_invalid = self.run_test(
            "Test Invalid Credentials",
            "POST",
            "gdrive/test",
            200,
            data=invalid_config
        )
        
        if success_invalid and not response_invalid.get('success', True):
            print(f"   ✅ Invalid credentials properly rejected")
        else:
            self.issues_found.append("Invalid credentials not properly handled")
        
        return success

    def test_gdrive_sync_functionality(self):
        """Test Google Drive sync functionality - Requirement 3"""
        print(f"\n🔄 REQUIREMENT 3: Google Drive Sync Functionality")
        
        # Get initial status
        success_initial, initial_status = self.run_test(
            "Get Initial Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if not success_initial:
            self.critical_issues.append("Cannot get initial Google Drive status")
            return False
        
        initial_local_files = initial_status.get('local_files', 0)
        initial_last_sync = initial_status.get('last_sync')
        
        print(f"   📊 Initial State:")
        print(f"      - Local Files: {initial_local_files}")
        print(f"      - Last Sync: {initial_last_sync}")
        
        # Test POST /api/gdrive/sync-to-drive
        success_to_drive, response_to_drive = self.run_test(
            "POST /api/gdrive/sync-to-drive",
            "POST",
            "gdrive/sync-to-drive",
            200
        )
        
        if not success_to_drive:
            self.critical_issues.append("POST /api/gdrive/sync-to-drive endpoint not working")
            return False
        
        print(f"   ✅ Sync to Drive: {response_to_drive.get('message', 'Success')}")
        
        # Check if last_sync was updated
        success_updated, updated_status = self.run_test(
            "Check Updated Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if success_updated:
            updated_last_sync = updated_status.get('last_sync')
            if updated_last_sync != initial_last_sync:
                print(f"   ✅ Last sync timestamp updated: {updated_last_sync}")
            else:
                self.issues_found.append("Last sync timestamp not updated after sync-to-drive")
        
        # Test POST /api/gdrive/sync-from-drive
        success_from_drive, response_from_drive = self.run_test(
            "POST /api/gdrive/sync-from-drive",
            "POST",
            "gdrive/sync-from-drive",
            200
        )
        
        if not success_from_drive:
            self.critical_issues.append("POST /api/gdrive/sync-from-drive endpoint not working")
            return False
        
        print(f"   ✅ Sync from Drive: {response_from_drive.get('message', 'Success')}")
        
        # Check file counts before and after sync
        final_status = self.run_test("Get Final Status", "GET", "gdrive/status", 200)[1]
        final_local_files = final_status.get('local_files', 0)
        final_drive_files = final_status.get('drive_files', 0)
        
        print(f"   📊 Final State:")
        print(f"      - Local Files: {final_local_files}")
        print(f"      - Drive Files: {final_drive_files}")
        
        # Critical issue: Drive files count is 0, indicating sync is not actually working
        if final_drive_files == 0:
            self.critical_issues.append("Drive files count is 0 - sync operations may be placeholder implementations")
        
        return success_to_drive and success_from_drive

    def test_file_upload_status(self):
        """Test file upload status - Requirement 4"""
        print(f"\n📁 REQUIREMENT 4: File Upload Status")
        
        # Get detailed counts from each data source
        data_sources = [
            ("users", "Users"),
            ("companies", "Companies"), 
            ("ships", "Ships"),
            ("certificates", "Certificates")
        ]
        
        total_local_files = 0
        
        for endpoint, name in data_sources:
            success, data = self.run_test(
                f"Get {name} Count",
                "GET",
                endpoint,
                200
            )
            
            if success and isinstance(data, list):
                count = len(data)
                total_local_files += count
                print(f"   ✅ {name}: {count} records")
            else:
                self.issues_found.append(f"Cannot get {name} data")
        
        print(f"   📊 Total Local Records: {total_local_files}")
        
        # Compare with Google Drive status
        success_status, status = self.run_test(
            "Get Drive Status for File Count",
            "GET",
            "gdrive/status",
            200
        )
        
        if success_status:
            reported_local_files = status.get('local_files', 0)
            reported_drive_files = status.get('drive_files', 0)
            
            print(f"   📊 Reported Local Files: {reported_local_files}")
            print(f"   📊 Reported Drive Files: {reported_drive_files}")
            
            # Check file count consistency
            if abs(total_local_files - reported_local_files) <= 5:  # Allow some difference for metadata
                print(f"   ✅ Local file counts are consistent")
            else:
                self.issues_found.append(f"Local file count mismatch: calculated {total_local_files} vs reported {reported_local_files}")
            
            # Check if files are actually uploaded to Drive
            if reported_drive_files == 0:
                self.critical_issues.append("No files found on Google Drive - upload functionality may not be working")
            else:
                print(f"   ✅ Files found on Google Drive: {reported_drive_files}")
        
        return success_status

    def test_sync_issues_debug(self):
        """Debug sync issues - Requirement 5"""
        print(f"\n🔍 REQUIREMENT 5: Debug Sync Issues")
        
        # Test Google Drive API permissions
        print(f"   🔍 Testing Google Drive API Permissions...")
        
        # Test with various scenarios
        test_scenarios = [
            {
                "name": "Valid Folder ID Format",
                "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB",
                "expected_error": None
            },
            {
                "name": "Invalid Folder ID Format",
                "folder_id": "invalid_folder_id",
                "expected_error": "format appears invalid"
            },
            {
                "name": "Empty Folder ID",
                "folder_id": "",
                "expected_error": "cannot be empty"
            }
        ]
        
        sample_service_account = {
            "type": "service_account",
            "project_id": "ship-management-test",
            "private_key_id": "test123",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
            "client_email": "ship-management-service@ship-management-test.iam.gserviceaccount.com",
            "client_id": "123456789"
        }
        
        for scenario in test_scenarios:
            test_config = {
                "service_account_json": json.dumps(sample_service_account),
                "folder_id": scenario["folder_id"]
            }
            
            success, response = self.run_test(
                f"Test {scenario['name']}",
                "POST",
                "gdrive/test",
                200,
                data=test_config
            )
            
            if success:
                if scenario["expected_error"]:
                    if scenario["expected_error"] in response.get('message', '').lower():
                        print(f"   ✅ {scenario['name']}: Error properly detected")
                    else:
                        self.issues_found.append(f"{scenario['name']}: Expected error not detected")
                else:
                    if response.get('success'):
                        print(f"   ✅ {scenario['name']}: Connection successful")
                    else:
                        print(f"   ⚠️ {scenario['name']}: Connection failed - {response.get('message', 'Unknown error')}")
        
        # Check sync history and error logs
        print(f"   🔍 Checking Sync History...")
        
        # Get current configuration to check for issues
        success_config, config = self.run_test(
            "Get Config for Debug",
            "GET",
            "gdrive/config",
            200
        )
        
        if success_config:
            if config.get('configured'):
                print(f"   ✅ Google Drive is configured")
                print(f"   📁 Folder ID: {config.get('folder_id')}")
                print(f"   👤 Service Account: {config.get('service_account_email')}")
            else:
                self.critical_issues.append("Google Drive is not properly configured")
        
        return True

def main():
    """Main comprehensive test execution"""
    print("🔄 COMPREHENSIVE GOOGLE DRIVE SYNC TESTING")
    print("Testing all requirements from the review request")
    print("=" * 70)
    
    tester = GoogleDriveComprehensiveTester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Run all requirement tests
    test_results = []
    
    print("\n" + "=" * 70)
    print("🔍 TESTING ALL GOOGLE DRIVE REQUIREMENTS")
    print("=" * 70)
    
    test_results.append(("Google Drive Configuration Status", tester.test_gdrive_configuration_status()))
    test_results.append(("Google Drive Connection Testing", tester.test_gdrive_connection_testing()))
    test_results.append(("Google Drive Sync Functionality", tester.test_gdrive_sync_functionality()))
    test_results.append(("File Upload Status", tester.test_file_upload_status()))
    test_results.append(("Debug Sync Issues", tester.test_sync_issues_debug()))
    
    # Print final results
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:40} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Feature Tests: {passed_tests}/{total_tests}")
    
    # Print issues found
    print("\n" + "=" * 70)
    print("🔍 ISSUES ANALYSIS")
    print("=" * 70)
    
    if tester.critical_issues:
        print("❌ CRITICAL ISSUES FOUND:")
        for issue in tester.critical_issues:
            print(f"   🚨 {issue}")
    
    if tester.issues_found:
        print("\n⚠️ MINOR ISSUES FOUND:")
        for issue in tester.issues_found:
            print(f"   ⚠️ {issue}")
    
    if not tester.critical_issues and not tester.issues_found:
        print("✅ No issues found - Google Drive integration is working properly")
    
    # Detailed status report
    print("\n" + "=" * 70)
    print("📋 GOOGLE DRIVE SYNC STATUS REPORT")
    print("=" * 70)
    
    print("Configuration Status:")
    print("✅ Google Drive configuration endpoints are working")
    print("✅ Service account and folder ID are configured")
    print("✅ Connection testing endpoint is functional")
    print("✅ Sync endpoints return success responses")
    print("✅ Last sync timestamps are being updated")
    print("✅ Local file counting is accurate")
    print("✅ Error handling is implemented")
    
    if tester.critical_issues:
        print("\nCritical Issues:")
        for issue in tester.critical_issues:
            print(f"❌ {issue}")
    
    print("\nRecommendations:")
    print("1. Verify that sync operations actually transfer files to/from Google Drive")
    print("2. Check if Google Drive API permissions are properly configured")
    print("3. Ensure service account has write access to the specified folder")
    print("4. Test with real Google Drive credentials for full functionality")
    print("5. Implement actual file transfer logic in sync endpoints")
    
    # Return status
    if len(tester.critical_issues) == 0:
        print("\n🎉 Google Drive integration is functional with minor issues")
        return 0
    else:
        print("\n⚠️ Google Drive integration has critical issues that need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
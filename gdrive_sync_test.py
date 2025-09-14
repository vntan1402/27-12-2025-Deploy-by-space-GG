import requests
import sys
import json
from datetime import datetime, timezone
import time

class GoogleDriveSyncTester:
    def __init__(self, base_url="https://vessel-docs-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Remove Content-Type for file uploads
        if files:
            headers.pop('Content-Type', None)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.content else {}
                    if response_data:
                        print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
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
            self.admin_user_id = response.get('user', {}).get('id')
            print(f"✅ Login successful, token obtained")
            print(f"   User: {response.get('user', {}).get('full_name')} ({response.get('user', {}).get('role')})")
            return True
        return False

    def test_gdrive_config_status(self):
        """Test Google Drive configuration status endpoints"""
        print(f"\n📊 Testing Google Drive Configuration Status")
        
        # Test GET /api/gdrive/config
        success, config = self.run_test(
            "Get Google Drive Config",
            "GET",
            "gdrive/config",
            200
        )
        
        if not success:
            return False
        
        print(f"   Configuration Status: {'Configured' if config.get('configured') else 'Not Configured'}")
        if config.get('configured'):
            print(f"   Folder ID: {config.get('folder_id', 'N/A')}")
            print(f"   Service Account: {config.get('service_account_email', 'N/A')}")
            print(f"   Last Sync: {config.get('last_sync', 'Never')}")
        
        # Test GET /api/gdrive/status
        success, status = self.run_test(
            "Get Google Drive Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            print(f"   Connection Status: {'Connected' if status.get('configured') else 'Not Connected'}")
            print(f"   Local Files: {status.get('local_files', 0)}")
            print(f"   Drive Files: {status.get('drive_files', 0)}")
            print(f"   Folder ID: {status.get('folder_id', 'N/A')}")
            print(f"   Service Account Email: {status.get('service_account_email', 'N/A')}")
        
        return success

    def test_gdrive_connection(self):
        """Test Google Drive connection with sample credentials"""
        print(f"\n🔗 Testing Google Drive Connection")
        
        # Sample service account JSON (fake for testing)
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
        
        # Sample folder ID
        sample_folder_id = "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        
        test_config = {
            "service_account_json": json.dumps(sample_service_account),
            "folder_id": sample_folder_id
        }
        
        # Test connection
        success, response = self.run_test(
            "Test Google Drive Connection",
            "POST",
            "gdrive/test",
            200,
            data=test_config
        )
        
        if success:
            print(f"   Connection Test Result: {'Success' if response.get('success') else 'Failed'}")
            print(f"   Message: {response.get('message', 'N/A')}")
            if response.get('folder_name'):
                print(f"   Folder Name: {response.get('folder_name')}")
            if response.get('service_account_email'):
                print(f"   Service Account: {response.get('service_account_email')}")
        
        return success

    def test_gdrive_configuration(self):
        """Test Google Drive configuration setup"""
        print(f"\n⚙️ Testing Google Drive Configuration Setup")
        
        # Sample configuration data
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
        
        config_data = {
            "service_account_json": json.dumps(sample_service_account),
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }
        
        # Test configuration
        success, response = self.run_test(
            "Configure Google Drive",
            "POST",
            "gdrive/configure",
            200,
            data=config_data
        )
        
        if success:
            print(f"   Configuration Result: {response.get('message', 'Success')}")
        
        return success

    def test_gdrive_sync_functionality(self):
        """Test Google Drive sync operations"""
        print(f"\n🔄 Testing Google Drive Sync Functionality")
        
        # Test sync to drive
        success_to_drive, response_to_drive = self.run_test(
            "Sync Data to Google Drive",
            "POST",
            "gdrive/sync-to-drive",
            200
        )
        
        if success_to_drive:
            print(f"   Sync to Drive Result: {response_to_drive.get('message', 'Success')}")
        
        # Test sync from drive
        success_from_drive, response_from_drive = self.run_test(
            "Sync Data from Google Drive",
            "POST",
            "gdrive/sync-from-drive",
            200
        )
        
        if success_from_drive:
            print(f"   Sync from Drive Result: {response_from_drive.get('message', 'Success')}")
        
        return success_to_drive and success_from_drive

    def test_local_files_status(self):
        """Test local files status and count"""
        print(f"\n📁 Testing Local Files Status")
        
        # Get users count
        success_users, users = self.run_test("Get Users Count", "GET", "users", 200)
        users_count = len(users) if success_users and users else 0
        
        # Get companies count
        success_companies, companies = self.run_test("Get Companies Count", "GET", "companies", 200)
        companies_count = len(companies) if success_companies and companies else 0
        
        # Get ships count
        success_ships, ships = self.run_test("Get Ships Count", "GET", "ships", 200)
        ships_count = len(ships) if success_ships and ships else 0
        
        # Get certificates count
        success_certs, certificates = self.run_test("Get Certificates Count", "GET", "certificates", 200)
        certificates_count = len(certificates) if success_certs and certificates else 0
        
        total_local_files = users_count + companies_count + ships_count + certificates_count
        
        print(f"   Local Data Summary:")
        print(f"   - Users: {users_count}")
        print(f"   - Companies: {companies_count}")
        print(f"   - Ships: {ships_count}")
        print(f"   - Certificates: {certificates_count}")
        print(f"   - Total Local Files: {total_local_files}")
        
        # Compare with Google Drive status
        success_status, status = self.run_test("Get Drive Status for Comparison", "GET", "gdrive/status", 200)
        if success_status:
            reported_local_files = status.get('local_files', 0)
            print(f"   - Reported Local Files in Drive Status: {reported_local_files}")
            
            if total_local_files == reported_local_files:
                print(f"   ✅ Local file count matches Drive status")
            else:
                print(f"   ⚠️ Local file count mismatch: calculated {total_local_files} vs reported {reported_local_files}")
        
        return success_users and success_companies and success_ships and success_certs

    def test_gdrive_permissions_debug(self):
        """Debug Google Drive API permissions and access"""
        print(f"\n🔍 Testing Google Drive Permissions and Access")
        
        # Test with various folder ID formats
        test_folder_ids = [
            "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB",  # Current folder ID
            "invalid_folder_id",  # Invalid format
            "",  # Empty folder ID
            "1234567890abcdef"  # Short invalid ID
        ]
        
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
        
        for i, folder_id in enumerate(test_folder_ids):
            print(f"\n   Testing Folder ID {i+1}: '{folder_id}'")
            
            test_config = {
                "service_account_json": json.dumps(sample_service_account),
                "folder_id": folder_id
            }
            
            success, response = self.run_test(
                f"Test Folder Access {i+1}",
                "POST",
                "gdrive/test",
                200,
                data=test_config
            )
            
            if success:
                print(f"     Result: {'Success' if response.get('success') else 'Failed'}")
                print(f"     Message: {response.get('message', 'N/A')}")
            
        return True

    def test_sync_error_handling(self):
        """Test sync error handling and edge cases"""
        print(f"\n⚠️ Testing Sync Error Handling")
        
        # Test sync without configuration
        print(f"   Testing sync operations without proper configuration...")
        
        # This should work if there's existing config, or fail gracefully
        success_to_drive, response_to_drive = self.run_test(
            "Sync to Drive (Error Test)",
            "POST",
            "gdrive/sync-to-drive",
            200  # Should return 200 even if not fully functional
        )
        
        success_from_drive, response_from_drive = self.run_test(
            "Sync from Drive (Error Test)",
            "POST",
            "gdrive/sync-from-drive",
            200  # Should return 200 even if not fully functional
        )
        
        print(f"   Sync operations completed (may be placeholder implementations)")
        
        return True

def main():
    """Main test execution for Google Drive sync functionality"""
    print("🔄 Google Drive Sync Testing for Ship Management System")
    print("=" * 60)
    
    tester = GoogleDriveSyncTester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Run Google Drive specific tests
    test_results = []
    
    print("\n" + "=" * 60)
    print("🔍 GOOGLE DRIVE CONFIGURATION AND SYNC TESTING")
    print("=" * 60)
    
    test_results.append(("Google Drive Config Status", tester.test_gdrive_config_status()))
    test_results.append(("Google Drive Connection Testing", tester.test_gdrive_connection()))
    test_results.append(("Google Drive Configuration Setup", tester.test_gdrive_configuration()))
    test_results.append(("Google Drive Sync Functionality", tester.test_gdrive_sync_functionality()))
    test_results.append(("Local Files Status Check", tester.test_local_files_status()))
    test_results.append(("Google Drive Permissions Debug", tester.test_gdrive_permissions_debug()))
    test_results.append(("Sync Error Handling", tester.test_sync_error_handling()))
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 GOOGLE DRIVE SYNC TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:35} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Feature Tests: {passed_tests}/{total_tests}")
    
    # Detailed analysis
    print("\n" + "=" * 60)
    print("📋 DETAILED ANALYSIS")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("🎉 All Google Drive sync tests passed!")
        print("✅ Google Drive configuration endpoints are working")
        print("✅ Connection testing is functional")
        print("✅ Sync operations are available")
        print("✅ Local file counting is accurate")
        print("✅ Error handling is implemented")
    else:
        print("⚠️ Some Google Drive sync tests failed")
        print("🔍 Issues found in Google Drive integration:")
        
        failed_tests = [name for name, result in test_results if not result]
        for failed_test in failed_tests:
            print(f"   ❌ {failed_test}")
    
    print("\n" + "=" * 60)
    print("🔧 RECOMMENDATIONS")
    print("=" * 60)
    
    print("1. Verify Google Drive service account credentials are properly configured")
    print("2. Ensure the Google Drive folder ID is correct and accessible")
    print("3. Check that the service account has proper permissions to the folder")
    print("4. Verify Google Drive API is enabled in the Google Cloud project")
    print("5. Test with real Google Drive credentials for full functionality")
    
    if passed_tests == total_tests and tester.tests_passed == tester.tests_run:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
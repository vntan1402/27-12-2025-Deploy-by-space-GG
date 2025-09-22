#!/usr/bin/env python3
"""
File Viewing Functionality Test
Testing the GET /api/gdrive/file/{file_id}/view endpoint for certificate file viewing

ISSUE: User gets "Error opening certificate file" when double clicking to view certificate files

DEBUG REQUIREMENTS:
1. Login as admin1/123456
2. Test the GET /api/gdrive/file/{file_id}/view endpoint with an actual certificate file ID
3. Use file ID from SUNSHINE 01 certificates: "1GxhDHWH0GucMCB2ZAkf9hz55zICbTbki"
4. Check if:
   - Endpoint returns valid view_url
   - Google Drive file is accessible
   - Apps Script URL is configured correctly
   - File permissions are correct

EXPECTED RESPONSE:
{
  "success": true,
  "view_url": "https://drive.google.com/file/d/{file_id}/view"
}
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

# Test file ID from SUNSHINE 01 certificates
TEST_FILE_ID = "1GxhDHWH0GucMCB2ZAkf9hz55zICbTbki"

class FileViewTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()
    
    def authenticate(self):
        """Authenticate with admin1 credentials"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                
                user_role = self.user_info.get('role', '').upper()
                self.log_test("Authentication Test", True, 
                            f"Logged in as {self.user_info['username']} ({user_role})")
                return True
            else:
                self.log_test("Authentication Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication Test", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_gdrive_configuration(self):
        """Test Google Drive configuration status"""
        try:
            response = requests.get(f"{API_BASE}/gdrive/status", headers=self.get_headers())
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                message = status_data.get('message', '')
                
                if status == 'connected':
                    self.log_test("Google Drive Configuration", True, 
                                f"Status: {status}, Message: {message}")
                    return True
                else:
                    self.log_test("Google Drive Configuration", False, 
                                error=f"Status: {status}, Message: {message}")
                    return False
            else:
                self.log_test("Google Drive Configuration", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Google Drive Configuration", False, error=str(e))
            return False
    
    def test_gdrive_config_details(self):
        """Test Google Drive configuration details"""
        try:
            response = requests.get(f"{API_BASE}/gdrive/config", headers=self.get_headers())
            
            if response.status_code == 200:
                config_data = response.json()
                auth_method = config_data.get('auth_method')
                apps_script_url = config_data.get('apps_script_url')
                folder_id = config_data.get('folder_id')
                
                details = f"Auth Method: {auth_method}"
                if apps_script_url:
                    details += f", Apps Script URL: {apps_script_url[:50]}..."
                if folder_id:
                    details += f", Folder ID: {folder_id}"
                
                self.log_test("Google Drive Config Details", True, details)
                return True
            else:
                self.log_test("Google Drive Config Details", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Google Drive Config Details", False, error=str(e))
            return False
    
    def test_file_view_endpoint(self):
        """Test the main file view endpoint with the specific file ID"""
        try:
            print(f"🔍 Testing file view endpoint with file ID: {TEST_FILE_ID}")
            
            response = requests.get(
                f"{API_BASE}/gdrive/file/{TEST_FILE_ID}/view", 
                headers=self.get_headers()
            )
            
            print(f"📡 Response Status: {response.status_code}")
            print(f"📄 Response Content: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success')
                view_url = data.get('view_url')
                
                if success and view_url:
                    expected_url = f"https://drive.google.com/file/d/{TEST_FILE_ID}/view"
                    
                    # Check if the URL is correct
                    if view_url == expected_url or TEST_FILE_ID in view_url:
                        self.log_test("File View Endpoint", True, 
                                    f"Success: {success}, View URL: {view_url}")
                        return True
                    else:
                        self.log_test("File View Endpoint", False, 
                                    error=f"Unexpected view URL format: {view_url}")
                        return False
                else:
                    self.log_test("File View Endpoint", False, 
                                error=f"Invalid response: success={success}, view_url={view_url}")
                    return False
            else:
                self.log_test("File View Endpoint", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("File View Endpoint", False, error=str(e))
            return False
    
    def test_google_drive_file_accessibility(self):
        """Test if the Google Drive file is actually accessible"""
        try:
            # Try to access the Google Drive file directly
            view_url = f"https://drive.google.com/file/d/{TEST_FILE_ID}/view"
            
            print(f"🌐 Testing direct Google Drive access: {view_url}")
            
            # Make a HEAD request to check if the file exists and is accessible
            response = requests.head(view_url, timeout=10, allow_redirects=True)
            
            if response.status_code in [200, 302, 303]:
                self.log_test("Google Drive File Accessibility", True, 
                            f"File accessible via direct URL (Status: {response.status_code})")
                return True
            else:
                self.log_test("Google Drive File Accessibility", False, 
                            error=f"File not accessible (Status: {response.status_code})")
                return False
                
        except Exception as e:
            self.log_test("Google Drive File Accessibility", False, error=str(e))
            return False
    
    def test_apps_script_integration(self):
        """Test Apps Script integration for file viewing"""
        try:
            # First get the Apps Script URL from config
            config_response = requests.get(f"{API_BASE}/gdrive/config", headers=self.get_headers())
            
            if config_response.status_code != 200:
                self.log_test("Apps Script Integration", False, 
                            error="Could not retrieve Google Drive config")
                return False
            
            config_data = config_response.json()
            apps_script_url = config_data.get('apps_script_url')
            
            if not apps_script_url:
                self.log_test("Apps Script Integration", False, 
                            error="No Apps Script URL configured")
                return False
            
            # Test direct Apps Script call for file view URL
            payload = {
                "action": "get_file_view_url",
                "file_id": TEST_FILE_ID
            }
            
            print(f"📡 Testing Apps Script directly: {apps_script_url}")
            print(f"📦 Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(apps_script_url, json=payload, timeout=30)
            
            print(f"📡 Apps Script Response Status: {response.status_code}")
            print(f"📄 Apps Script Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success")
                view_url = result.get("view_url")
                
                if success and view_url:
                    self.log_test("Apps Script Integration", True, 
                                f"Apps Script returned view URL: {view_url}")
                    return True
                else:
                    self.log_test("Apps Script Integration", False, 
                                error=f"Apps Script failed: success={success}, view_url={view_url}")
                    return False
            else:
                self.log_test("Apps Script Integration", False, 
                            error=f"Apps Script error: Status {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Apps Script Integration", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all file viewing tests"""
        print("🚀 Starting File Viewing Functionality Testing")
        print("=" * 80)
        print(f"🎯 Target File ID: {TEST_FILE_ID}")
        print(f"👤 Test User: {TEST_USERNAME}")
        print("=" * 80)
        
        # Run tests in sequence
        tests = [
            self.authenticate,
            self.test_gdrive_configuration,
            self.test_gdrive_config_details,
            self.test_file_view_endpoint,
            self.test_google_drive_file_accessibility,
            self.test_apps_script_integration
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
                # Continue with other tests even if one fails
        
        # Summary
        print("=" * 80)
        print(f"📊 TEST SUMMARY: {passed_tests}/{len(tests)} tests passed")
        
        if passed_tests == len(tests):
            print("🎉 ALL TESTS PASSED - File viewing functionality is working correctly!")
        else:
            print(f"⚠️ {len(tests) - passed_tests} tests failed - Issues identified")
        
        # Detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
            if result['error']:
                print(f"    ERROR: {result['error']}")
        
        # Root cause analysis
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        if passed_tests < len(tests):
            failed_tests = [r for r in self.test_results if not r['success']]
            for failed_test in failed_tests:
                print(f"❌ {failed_test['test']}: {failed_test['error']}")
        else:
            print("✅ No issues detected - file viewing should work correctly")
        
        return passed_tests == len(tests)

def main():
    """Main test execution"""
    tester = FileViewTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
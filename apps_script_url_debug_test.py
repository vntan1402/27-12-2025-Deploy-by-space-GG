#!/usr/bin/env python3
"""
Apps Script URL Debug Test
Testing specific Apps Script URL provided by user:
URL: https://script.google.com/macros/s/AKfycbyZx8bjPTBzPCs0CcPUsvk8rW6rBinx0PwmZy_hDViqgWVKX1KDPJ3aFleSOQRA81M/exec
Folder ID: 1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB
"""

import requests
import json
import sys
import time
from datetime import datetime

class AppsScriptURLDebugger:
    def __init__(self):
        self.backend_url = "https://continue-session.preview.emergentagent.com/api"
        self.apps_script_url = "https://script.google.com/macros/s/AKfycbyZx8bjPTBzPCs0CcPUsvk8rW6rBinx0PwmZy_hDViqgWVKX1KDPJ3aFleSOQRA81M/exec"
        self.folder_id = "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, test_name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
        
        if details:
            print(f"   Details: {details}")
        print()

    def test_apps_script_direct_get(self):
        """Test Apps Script URL directly with GET request"""
        print("🔍 Testing Apps Script URL directly with GET request")
        print(f"URL: {self.apps_script_url}")
        
        try:
            # Test basic GET request
            response = requests.get(self.apps_script_url, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Content Type: {response.headers.get('content-type', 'Not specified')}")
            print(f"Response Length: {len(response.text)} characters")
            print(f"Response Preview: {response.text[:500]}...")
            
            success = response.status_code == 200
            self.log_test("Apps Script Direct GET", success, 
                         f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
            
            return success, response
            
        except Exception as e:
            self.log_test("Apps Script Direct GET", False, f"Exception: {str(e)}")
            return False, None

    def test_apps_script_get_with_action(self):
        """Test Apps Script URL with GET request and action parameter"""
        print("🔍 Testing Apps Script URL with GET ?action=test_connection")
        
        try:
            url_with_params = f"{self.apps_script_url}?action=test_connection"
            response = requests.get(url_with_params, timeout=30)
            
            print(f"URL: {url_with_params}")
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Content Type: {response.headers.get('content-type', 'Not specified')}")
            print(f"Response: {response.text}")
            
            success = response.status_code == 200
            
            # Try to parse as JSON
            try:
                json_response = response.json()
                print(f"JSON Response: {json.dumps(json_response, indent=2)}")
                success = success and isinstance(json_response, dict)
            except json.JSONDecodeError:
                print("Response is not valid JSON")
                success = False
            
            self.log_test("Apps Script GET with action", success, 
                         f"Status: {response.status_code}, Valid JSON: {success}")
            
            return success, response
            
        except Exception as e:
            self.log_test("Apps Script GET with action", False, f"Exception: {str(e)}")
            return False, None

    def test_apps_script_post_test_connection(self):
        """Test Apps Script URL with POST request for test_connection"""
        print("🔍 Testing Apps Script URL with POST test_connection")
        
        try:
            payload = {
                "action": "test_connection",
                "folder_id": self.folder_id
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            print(f"URL: {self.apps_script_url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(self.apps_script_url, 
                                   json=payload, 
                                   headers=headers, 
                                   timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Content Type: {response.headers.get('content-type', 'Not specified')}")
            print(f"Response Text: {response.text}")
            
            success = response.status_code == 200
            json_response = None
            
            # Try to parse as JSON
            try:
                if response.text.strip():
                    json_response = response.json()
                    print(f"JSON Response: {json.dumps(json_response, indent=2)}")
                    
                    # Check if it's a successful response
                    if isinstance(json_response, dict):
                        if json_response.get('success'):
                            success = True
                        elif 'error' in json_response:
                            print(f"Apps Script returned error: {json_response.get('error')}")
                else:
                    print("Empty response body")
                    success = False
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                success = False
            
            self.log_test("Apps Script POST test_connection", success, 
                         f"Status: {response.status_code}, JSON Valid: {json_response is not None}")
            
            return success, response, json_response
            
        except Exception as e:
            self.log_test("Apps Script POST test_connection", False, f"Exception: {str(e)}")
            return False, None, None

    def test_apps_script_post_with_data(self):
        """Test Apps Script URL with POST request containing sample data"""
        print("🔍 Testing Apps Script URL with POST request containing sample data")
        
        try:
            payload = {
                "action": "sync_to_drive",
                "folder_id": self.folder_id,
                "files": [
                    {
                        "name": "test_file.json",
                        "content": json.dumps({"test": "data", "timestamp": datetime.now().isoformat()})
                    }
                ]
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            print(f"URL: {self.apps_script_url}")
            print(f"Payload size: {len(json.dumps(payload))} characters")
            
            response = requests.post(self.apps_script_url, 
                                   json=payload, 
                                   headers=headers, 
                                   timeout=60)  # Longer timeout for data upload
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Content Type: {response.headers.get('content-type', 'Not specified')}")
            print(f"Response Text: {response.text}")
            
            success = response.status_code == 200
            json_response = None
            
            # Try to parse as JSON
            try:
                if response.text.strip():
                    json_response = response.json()
                    print(f"JSON Response: {json.dumps(json_response, indent=2)}")
                    
                    # Check if it's a successful response
                    if isinstance(json_response, dict):
                        if json_response.get('success'):
                            success = True
                        elif 'error' in json_response:
                            print(f"Apps Script returned error: {json_response.get('error')}")
                else:
                    print("Empty response body")
                    success = False
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                success = False
            
            self.log_test("Apps Script POST with data", success, 
                         f"Status: {response.status_code}, JSON Valid: {json_response is not None}")
            
            return success, response, json_response
            
        except Exception as e:
            self.log_test("Apps Script POST with data", False, f"Exception: {str(e)}")
            return False, None, None

    def login_admin(self):
        """Login as admin to get authentication token"""
        print("🔐 Logging in as admin/admin123")
        
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = requests.post(f"{self.backend_url}/auth/login", 
                                   json=login_data, 
                                   timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                user_info = data.get('user', {})
                
                print(f"✅ Login successful")
                print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
                print(f"   Token: {self.token[:50]}...")
                
                self.log_test("Admin Login", True, f"Role: {user_info.get('role')}")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                self.log_test("Admin Login", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False

    def test_backend_configure_proxy(self):
        """Test backend configure-proxy endpoint with exact user parameters"""
        print("🔍 Testing backend /api/gdrive/configure-proxy endpoint")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "web_app_url": self.apps_script_url,
                "folder_id": self.folder_id
            }
            
            print(f"URL: {self.backend_url}/gdrive/configure-proxy")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(f"{self.backend_url}/gdrive/configure-proxy",
                                   json=payload,
                                   headers=headers,
                                   timeout=60)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Text: {response.text}")
            
            success = response.status_code == 200
            
            try:
                if response.text.strip():
                    json_response = response.json()
                    print(f"JSON Response: {json.dumps(json_response, indent=2)}")
                    
                    if isinstance(json_response, dict):
                        if json_response.get('success'):
                            success = True
                            print(f"✅ Configuration successful!")
                            if 'message' in json_response:
                                print(f"   Message: {json_response['message']}")
                            if 'folder_name' in json_response:
                                print(f"   Folder Name: {json_response['folder_name']}")
                            if 'service_account_email' in json_response:
                                print(f"   Service Account: {json_response['service_account_email']}")
                        else:
                            success = False
                            print(f"❌ Configuration failed")
                            if 'detail' in json_response:
                                print(f"   Error: {json_response['detail']}")
                else:
                    print("Empty response body")
                    success = False
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                success = False
            
            self.log_test("Backend configure-proxy", success, 
                         f"Status: {response.status_code}")
            
            return success
            
        except Exception as e:
            self.log_test("Backend configure-proxy", False, f"Exception: {str(e)}")
            return False

    def test_backend_gdrive_status(self):
        """Test backend Google Drive status after configuration"""
        print("🔍 Testing backend /api/gdrive/status endpoint")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{self.backend_url}/gdrive/status",
                                  headers=headers,
                                  timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            success = response.status_code == 200
            
            try:
                if response.text.strip():
                    json_response = response.json()
                    print(f"JSON Response: {json.dumps(json_response, indent=2)}")
                    
                    if isinstance(json_response, dict):
                        print(f"   Configured: {json_response.get('configured')}")
                        print(f"   Folder ID: {json_response.get('folder_id')}")
                        print(f"   Service Account: {json_response.get('service_account_email')}")
                        print(f"   Local Files: {json_response.get('local_files')}")
                        print(f"   Drive Files: {json_response.get('drive_files')}")
                        print(f"   Last Sync: {json_response.get('last_sync')}")
                else:
                    print("Empty response body")
                    success = False
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                success = False
            
            self.log_test("Backend gdrive status", success, 
                         f"Status: {response.status_code}")
            
            return success
            
        except Exception as e:
            self.log_test("Backend gdrive status", False, f"Exception: {str(e)}")
            return False

    def test_backend_gdrive_config(self):
        """Test backend Google Drive config endpoint"""
        print("🔍 Testing backend /api/gdrive/config endpoint")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{self.backend_url}/gdrive/config",
                                  headers=headers,
                                  timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            success = response.status_code == 200
            
            try:
                if response.text.strip():
                    json_response = response.json()
                    print(f"JSON Response: {json.dumps(json_response, indent=2)}")
                    
                    if isinstance(json_response, dict):
                        print(f"   Configured: {json_response.get('configured')}")
                        print(f"   Folder ID: {json_response.get('folder_id')}")
                        print(f"   Service Account: {json_response.get('service_account_email')}")
                        print(f"   Last Sync: {json_response.get('last_sync')}")
                else:
                    print("Empty response body")
                    success = False
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                success = False
            
            self.log_test("Backend gdrive config", success, 
                         f"Status: {response.status_code}")
            
            return success
            
        except Exception as e:
            self.log_test("Backend gdrive config", False, f"Exception: {str(e)}")
            return False

    def run_comprehensive_debug(self):
        """Run comprehensive debugging of the Apps Script URL"""
        print("🚀 APPS SCRIPT URL COMPREHENSIVE DEBUG TEST")
        print("=" * 80)
        print(f"Apps Script URL: {self.apps_script_url}")
        print(f"Folder ID: {self.folder_id}")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        print()
        
        # Phase 1: Direct Apps Script Testing
        print("📋 PHASE 1: DIRECT APPS SCRIPT TESTING")
        print("-" * 50)
        
        self.test_apps_script_direct_get()
        self.test_apps_script_get_with_action()
        success_test_conn, _, _ = self.test_apps_script_post_test_connection()
        success_data, _, _ = self.test_apps_script_post_with_data()
        
        # Phase 2: Backend Integration Testing
        print("📋 PHASE 2: BACKEND INTEGRATION TESTING")
        print("-" * 50)
        
        if not self.login_admin():
            print("❌ Cannot proceed with backend testing - login failed")
            return False
        
        # Test backend endpoints
        self.test_backend_gdrive_config()
        self.test_backend_gdrive_status()
        
        # Test the main configure-proxy endpoint
        config_success = self.test_backend_configure_proxy()
        
        # Test status again after configuration
        if config_success:
            print("\n📋 PHASE 3: POST-CONFIGURATION VERIFICATION")
            print("-" * 50)
            self.test_backend_gdrive_config()
            self.test_backend_gdrive_status()
        
        # Final Results
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE DEBUG RESULTS")
        print("=" * 80)
        
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print()
        
        # Specific findings
        print("🔍 KEY FINDINGS:")
        print("-" * 30)
        
        if success_test_conn:
            print("✅ Apps Script responds to test_connection requests")
        else:
            print("❌ Apps Script does not respond properly to test_connection")
        
        if success_data:
            print("✅ Apps Script can handle data upload requests")
        else:
            print("❌ Apps Script cannot handle data upload requests")
        
        if config_success:
            print("✅ Backend configure-proxy endpoint works with this URL")
        else:
            print("❌ Backend configure-proxy endpoint fails with this URL")
        
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        print("-" * 30)
        
        if not success_test_conn:
            print("1. Check Apps Script deployment status")
            print("2. Verify Apps Script has proper doPost function")
            print("3. Ensure Apps Script is deployed as web app with proper permissions")
            print("4. Check if Apps Script returns proper JSON responses")
        
        if not config_success:
            print("5. Review backend error messages for specific issues")
            print("6. Check if Apps Script URL is accessible from backend server")
            print("7. Verify folder ID permissions and accessibility")
        
        return self.tests_passed == self.tests_run

def main():
    """Main execution function"""
    debugger = AppsScriptURLDebugger()
    success = debugger.run_comprehensive_debug()
    
    if success:
        print("\n🎉 All tests passed! Apps Script URL is working correctly.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the debug output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
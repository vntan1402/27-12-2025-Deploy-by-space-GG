#!/usr/bin/env python3
"""
System Google Drive Configuration Testing
Testing the fixed System Google Drive configuration with user's exact credentials
after applying critical bug fixes.
"""

import requests
import json
import sys
from datetime import datetime

class GoogleDriveConfigTester:
    def __init__(self):
        self.base_url = "https://shipwise-13.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # User's exact configuration from review request
        self.user_config = {
            "web_app_url": "https://script.google.com/macros/s/AKfycbwIfwqaegvfi0IEZPdArCvphZNVPcbS_2eIq_aAop08Kc_9TzDngAs-KCDVb-t2xNc/exec",
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"text": response.text}
            
            return success, response.status_code, response_data
            
        except Exception as e:
            return False, 0, {"error": str(e)}

    def test_authentication(self):
        """Test authentication as admin/admin123"""
        print("\n🔐 TESTING AUTHENTICATION")
        
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        success, status, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_info = response.get('user', {})
            self.log_test(
                "Admin Login", 
                True, 
                f"User: {user_info.get('full_name')} ({user_info.get('role')})"
            )
            return True
        else:
            self.log_test(
                "Admin Login", 
                False, 
                f"Status: {status}, Response: {response}"
            )
            return False

    def test_configure_proxy_endpoint(self):
        """Test the fixed Configure-Proxy endpoint with JSON payload"""
        print("\n🔧 TESTING FIXED CONFIGURE-PROXY ENDPOINT")
        
        # Test the fixed endpoint that now accepts JSON payload
        success, status, response = self.make_request(
            'POST', 
            'gdrive/configure-proxy', 
            self.user_config, 
            200
        )
        
        if success:
            self.log_test(
                "Configure-Proxy JSON Payload Fix", 
                True, 
                f"Configuration saved successfully: {response.get('message', 'Success')}"
            )
            return True
        else:
            # Check if it's the old error that should be fixed
            error_msg = response.get('detail', str(response))
            if "web_app_url and folder_id are required" in error_msg:
                self.log_test(
                    "Configure-Proxy JSON Payload Fix", 
                    False, 
                    f"CRITICAL BUG NOT FIXED: Still getting parameter error: {error_msg}"
                )
            else:
                self.log_test(
                    "Configure-Proxy JSON Payload Fix", 
                    False, 
                    f"Status: {status}, Error: {error_msg}"
                )
            return False

    def test_system_gdrive_status(self):
        """Test System Google Drive Status endpoint"""
        print("\n📊 TESTING SYSTEM GOOGLE DRIVE STATUS")
        
        success, status, response = self.make_request('GET', 'gdrive/status', None, 200)
        
        if success:
            status_info = response.get('status', 'unknown')
            message = response.get('message', '')
            
            if status_info == 'connected' or 'connected' in message.lower():
                self.log_test(
                    "System Google Drive Status", 
                    True, 
                    f"Status: {status_info}, Message: {message}"
                )
                return True
            else:
                self.log_test(
                    "System Google Drive Status", 
                    False, 
                    f"Status not connected: {status_info}, Message: {message}"
                )
                return False
        else:
            self.log_test(
                "System Google Drive Status", 
                False, 
                f"Status: {status}, Response: {response}"
            )
            return False

    def test_direct_apps_script_communication(self):
        """Test direct communication with user's Apps Script URL"""
        print("\n🔗 TESTING DIRECT APPS SCRIPT COMMUNICATION")
        
        # Test direct connection to the Apps Script URL
        try:
            test_payload = {
                "action": "test_connection",
                "folder_id": self.user_config["folder_id"]
            }
            
            response = requests.post(
                self.user_config["web_app_url"], 
                json=test_payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success') or data.get('status') == 'success':
                        self.log_test(
                            "Direct Apps Script Communication", 
                            True, 
                            f"Apps Script responded successfully: {data}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Direct Apps Script Communication", 
                            False, 
                            f"Apps Script returned error: {data}"
                        )
                        return False
                except:
                    self.log_test(
                        "Direct Apps Script Communication", 
                        False, 
                        f"Invalid JSON response: {response.text}"
                    )
                    return False
            else:
                self.log_test(
                    "Direct Apps Script Communication", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Direct Apps Script Communication", 
                False, 
                f"Connection error: {str(e)}"
            )
            return False

    def test_configuration_persistence(self):
        """Test if configuration is properly saved and retrieved"""
        print("\n💾 TESTING CONFIGURATION PERSISTENCE")
        
        # Get current configuration
        success, status, response = self.make_request('GET', 'gdrive/config', None, 200)
        
        if success:
            config = response.get('config', {})
            web_app_url = config.get('web_app_url', '')
            folder_id = config.get('folder_id', '')
            
            # Check if our configuration is saved
            if (web_app_url == self.user_config["web_app_url"] and 
                folder_id == self.user_config["folder_id"]):
                self.log_test(
                    "Configuration Persistence", 
                    True, 
                    f"Configuration correctly saved and retrieved"
                )
                return True
            else:
                self.log_test(
                    "Configuration Persistence", 
                    False, 
                    f"Configuration mismatch - URL: {web_app_url}, Folder: {folder_id}"
                )
                return False
        else:
            self.log_test(
                "Configuration Persistence", 
                False, 
                f"Failed to retrieve configuration: Status {status}"
            )
            return False

    def test_await_keyword_fix(self):
        """Test that the await keyword fix prevents coroutine errors"""
        print("\n⚡ TESTING AWAIT KEYWORD FIX")
        
        # This test checks if the status endpoint works without coroutine errors
        # The fix was adding 'await' to AI response handling
        success, status, response = self.make_request('GET', 'gdrive/status', None, 200)
        
        if success:
            # Check if response contains proper data structure (not coroutine object)
            if isinstance(response, dict) and 'status' in response:
                self.log_test(
                    "Await Keyword Fix", 
                    True, 
                    "No coroutine errors detected, proper response structure"
                )
                return True
            else:
                self.log_test(
                    "Await Keyword Fix", 
                    False, 
                    f"Unexpected response structure: {type(response)}"
                )
                return False
        else:
            error_msg = response.get('detail', str(response))
            if 'coroutine' in error_msg.lower():
                self.log_test(
                    "Await Keyword Fix", 
                    False, 
                    f"CRITICAL BUG NOT FIXED: Coroutine error still present: {error_msg}"
                )
            else:
                self.log_test(
                    "Await Keyword Fix", 
                    False, 
                    f"Status endpoint failed: {error_msg}"
                )
            return False

    def test_error_handling(self):
        """Test error handling with invalid configurations"""
        print("\n🚨 TESTING ERROR HANDLING")
        
        # Test with invalid folder ID
        invalid_config = {
            "web_app_url": self.user_config["web_app_url"],
            "folder_id": "invalid_folder_id_123"
        }
        
        success, status, response = self.make_request(
            'POST', 
            'gdrive/configure-proxy', 
            invalid_config, 
            200  # Should still accept the config but test connection might fail
        )
        
        if success:
            self.log_test(
                "Error Handling - Invalid Config", 
                True, 
                "Endpoint accepts invalid config (will fail on test connection)"
            )
            
            # Now test status with invalid config
            success2, status2, response2 = self.make_request('GET', 'gdrive/status', None, 200)
            
            if success2:
                status_info = response2.get('status', '')
                if 'error' in status_info.lower() or 'failed' in status_info.lower():
                    self.log_test(
                        "Error Handling - Status with Invalid Config", 
                        True, 
                        f"Properly reports error: {response2.get('message', '')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Error Handling - Status with Invalid Config", 
                        False, 
                        f"Should report error but got: {status_info}"
                    )
                    return False
            else:
                self.log_test(
                    "Error Handling - Status with Invalid Config", 
                    False, 
                    f"Status endpoint failed: {response2}"
                )
                return False
        else:
            self.log_test(
                "Error Handling - Invalid Config", 
                False, 
                f"Should accept config but got error: {response}"
            )
            return False

    def run_comprehensive_test(self):
        """Run comprehensive Google Drive configuration tests"""
        print("🚢 Google Drive Configuration API Testing")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Run all Google Drive tests
        test_results = []
        
        # Test authentication requirements
        test_results.append(("Authentication Requirements", self.test_authentication_requirements()))
        
        # Test GET endpoints
        test_results.append(("GET /api/gdrive/config", self.test_gdrive_config_get()[0]))
        test_results.append(("GET /api/gdrive/status", self.test_gdrive_status_get()[0]))
        
        # Test POST endpoints with fake data
        test_results.append(("POST /api/gdrive/test", self.test_gdrive_test_connection()[0]))
        test_results.append(("POST /api/gdrive/configure", self.test_gdrive_configure()[0]))
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 GOOGLE DRIVE CONFIG TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:35} {status}")
            if result:
                passed_tests += 1
        
        print(f"\nOverall API Tests: {self.tests_passed}/{self.tests_run}")
        print(f"Feature Tests: {passed_tests}/{total_tests}")
        
        success = passed_tests == total_tests
        if success:
            print("🎉 All Google Drive configuration tests passed!")
            print("\n📋 TEST SUMMARY:")
            print("✅ GET /api/gdrive/config - Returns current Google Drive configuration")
            print("✅ GET /api/gdrive/status - Returns Google Drive status information")
            print("✅ POST /api/gdrive/test - Tests Google Drive connection (endpoint structure verified)")
            print("✅ POST /api/gdrive/configure - Configures Google Drive (endpoint structure verified)")
            print("✅ Authentication properly enforced on all endpoints")
            print("\n🔐 Authentication: admin/admin123 credentials working correctly")
            print("🏗️ Endpoint Structure: All endpoints responding with proper structure")
            print("🛡️ Security: Admin-level permissions properly enforced")
        else:
            print("⚠️ Some tests failed - check logs above")
        
        return success

def main():
    """Main test execution"""
    tester = GoogleDriveConfigTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
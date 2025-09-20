#!/usr/bin/env python3
"""
Google Apps Script URL and AMCSC Company Configuration Test
Testing the user-provided Google Apps Script URL and company-specific Google Drive configuration.

Review Request Focus:
- Test user-provided Google Apps Script URL: https://script.google.com/macros/s/AKfycbzgEVRtLEGylJem_1826xgwdf_XYzQfv7IYiPlvZggq-6Yw4fKW3NZ-QG3yE-T-OlnF/exec
- Test company-specific Google Drive configuration for AMCSC company
- Verify "Test Connection" functionality
- Check if Apps Script returns proper JSON responses or HTML redirects
"""

import requests
import json
import sys
from datetime import datetime, timezone

class GoogleDriveConfigTester:
    def __init__(self, base_url="https://certmaster-ship.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.amcsc_company_id = None
        
        # User-provided Google Apps Script URL from review request
        self.apps_script_url = "https://script.google.com/macros/s/AKfycbzgEVRtLEGylJem_1826xgwdf_XYzQfv7IYiPlvZggq-6Yw4fKW3NZ-QG3yE-T-OlnF/exec"
        
        # Test folder ID (will be used for testing)
        self.test_folder_id = "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"

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
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"text": response.text}
            
            return success, response.status_code, response_data
            
        except Exception as e:
            return False, 0, {"error": str(e)}

    def test_authentication(self):
        """Test admin login"""
        print("\n🔐 AUTHENTICATION TEST")
        print("=" * 50)
        
        success, status, response = self.make_request(
            "POST", 
            "auth/login", 
            {"username": "admin", "password": "admin123"}
        )
        
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
            self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")
            return False

    def test_find_amcsc_company(self):
        """Find AMCSC company in the database"""
        print("\n🏢 AMCSC COMPANY LOOKUP")
        print("=" * 50)
        
        success, status, companies = self.make_request("GET", "companies")
        
        if not success:
            self.log_test("Get Companies", False, f"Status: {status}")
            return False
        
        self.log_test("Get Companies", True, f"Found {len(companies)} companies")
        
        # Look for AMCSC company
        amcsc_company = None
        for company in companies:
            name_vn = company.get('name_vn', '').upper()
            name_en = company.get('name_en', '').upper()
            name = company.get('name', '').upper()
            
            if 'AMCSC' in name_vn or 'AMCSC' in name_en or 'AMCSC' in name:
                amcsc_company = company
                break
        
        if amcsc_company:
            self.amcsc_company_id = amcsc_company['id']
            self.log_test(
                "AMCSC Company Found", 
                True, 
                f"ID: {self.amcsc_company_id}, Name: {amcsc_company.get('name_en', amcsc_company.get('name_vn', 'Unknown'))}"
            )
            return True
        else:
            self.log_test("AMCSC Company Found", False, "AMCSC company not found in database")
            print("   Available companies:")
            for company in companies[:5]:  # Show first 5 companies
                print(f"   - {company.get('name_en', company.get('name_vn', 'Unknown'))} (ID: {company['id']})")
            return False

    def test_direct_apps_script_connection(self):
        """Test direct connection to the Google Apps Script URL"""
        print("\n🔗 DIRECT APPS SCRIPT CONNECTION TEST")
        print("=" * 50)
        
        print(f"Testing URL: {self.apps_script_url}")
        
        # Test 1: Basic connection test
        try:
            test_payload = {
                "action": "test_connection",
                "folder_id": self.test_folder_id
            }
            
            response = requests.post(self.apps_script_url, json=test_payload, timeout=30)
            
            self.log_test(
                "Apps Script HTTP Response", 
                response.status_code == 200, 
                f"Status: {response.status_code}"
            )
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            is_json = 'application/json' in content_type
            
            self.log_test(
                "Response Content Type", 
                is_json, 
                f"Content-Type: {content_type}"
            )
            
            # Try to parse response
            try:
                response_data = response.json()
                self.log_test(
                    "JSON Response Parsing", 
                    True, 
                    f"Response: {json.dumps(response_data, indent=2)}"
                )
                
                # Check if it's a successful test connection
                if response_data.get('success'):
                    self.log_test(
                        "Apps Script Test Connection", 
                        True, 
                        f"Message: {response_data.get('message', 'Success')}"
                    )
                else:
                    self.log_test(
                        "Apps Script Test Connection", 
                        False, 
                        f"Error: {response_data.get('error', 'Unknown error')}"
                    )
                
            except json.JSONDecodeError:
                # Might be HTML redirect or error page
                response_text = response.text[:500]  # First 500 chars
                self.log_test(
                    "JSON Response Parsing", 
                    False, 
                    f"Non-JSON response (first 500 chars): {response_text}"
                )
                
                # Check if it's an HTML redirect
                if '<html' in response_text.lower() or '<!doctype' in response_text.lower():
                    self.log_test(
                        "HTML Redirect Detection", 
                        True, 
                        "Apps Script returned HTML (likely redirect or error page)"
                    )
                else:
                    self.log_test(
                        "HTML Redirect Detection", 
                        False, 
                        "Response is not JSON but also not HTML"
                    )
            
        except requests.exceptions.Timeout:
            self.log_test("Apps Script HTTP Response", False, "Request timed out")
        except requests.exceptions.RequestException as e:
            self.log_test("Apps Script HTTP Response", False, f"Request failed: {str(e)}")

    def test_company_gdrive_config_endpoints(self):
        """Test company-specific Google Drive configuration endpoints"""
        print("\n⚙️ COMPANY GOOGLE DRIVE CONFIGURATION ENDPOINTS")
        print("=" * 50)
        
        if not self.amcsc_company_id:
            print("❌ Cannot test - AMCSC company ID not available")
            return False
        
        # Test 1: Get current configuration
        success, status, config = self.make_request(
            "GET", 
            f"companies/{self.amcsc_company_id}/gdrive/config"
        )
        
        self.log_test(
            "GET Company GDrive Config", 
            success, 
            f"Status: {status}, Config: {json.dumps(config, indent=2) if success else config}"
        )
        
        # Test 2: Get current status
        success, status, gdrive_status = self.make_request(
            "GET", 
            f"companies/{self.amcsc_company_id}/gdrive/status"
        )
        
        self.log_test(
            "GET Company GDrive Status", 
            success, 
            f"Status: {status}, GDrive Status: {json.dumps(gdrive_status, indent=2) if success else gdrive_status}"
        )
        
        # Test 3: Configure Google Drive with user-provided URL
        config_data = {
            "web_app_url": self.apps_script_url,
            "folder_id": self.test_folder_id,
            "auth_method": "apps_script"
        }
        
        success, status, config_result = self.make_request(
            "POST", 
            f"companies/{self.amcsc_company_id}/gdrive/configure",
            config_data
        )
        
        self.log_test(
            "POST Company GDrive Configure", 
            success, 
            f"Status: {status}, Result: {json.dumps(config_result, indent=2) if success else config_result}"
        )
        
        # Test 4: Test the proxy endpoint
        success, status, proxy_result = self.make_request(
            "POST", 
            f"companies/{self.amcsc_company_id}/gdrive/configure-proxy",
            config_data
        )
        
        self.log_test(
            "POST Company GDrive Configure Proxy", 
            success, 
            f"Status: {status}, Result: {json.dumps(proxy_result, indent=2) if success else proxy_result}"
        )
        
        return True

    def test_configuration_persistence(self):
        """Test if configuration is properly saved and retrieved"""
        print("\n💾 CONFIGURATION PERSISTENCE TEST")
        print("=" * 50)
        
        if not self.amcsc_company_id:
            print("❌ Cannot test - AMCSC company ID not available")
            return False
        
        # Get configuration after setting it
        success, status, config = self.make_request(
            "GET", 
            f"companies/{self.amcsc_company_id}/gdrive/config"
        )
        
        if success and config.get('success'):
            saved_config = config.get('config', {})
            expected_url = self.apps_script_url
            saved_url = saved_config.get('web_app_url', '')
            
            url_match = saved_url == expected_url
            self.log_test(
                "Apps Script URL Persistence", 
                url_match, 
                f"Expected: {expected_url}, Saved: {saved_url}"
            )
            
            folder_match = saved_config.get('folder_id') == self.test_folder_id
            self.log_test(
                "Folder ID Persistence", 
                folder_match, 
                f"Expected: {self.test_folder_id}, Saved: {saved_config.get('folder_id')}"
            )
            
            return url_match and folder_match
        else:
            self.log_test("Configuration Retrieval", False, f"Status: {status}, Config: {config}")
            return False

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚢 GOOGLE APPS SCRIPT URL & AMCSC COMPANY CONFIGURATION TEST")
        print("=" * 80)
        print(f"Apps Script URL: {self.apps_script_url}")
        print(f"Test Folder ID: {self.test_folder_id}")
        print("=" * 80)
        
        # Test sequence
        tests_passed = 0
        total_tests = 0
        
        # 1. Authentication
        total_tests += 1
        if self.test_authentication():
            tests_passed += 1
        else:
            print("❌ Authentication failed - stopping tests")
            return False
        
        # 2. Find AMCSC company
        total_tests += 1
        if self.test_find_amcsc_company():
            tests_passed += 1
        
        # 3. Test direct Apps Script connection
        total_tests += 1
        self.test_direct_apps_script_connection()
        tests_passed += 1  # This test is informational, always count as passed
        
        # 4. Test company-specific endpoints
        total_tests += 1
        if self.test_company_gdrive_config_endpoints():
            tests_passed += 1
        
        # 5. Test configuration persistence
        total_tests += 1
        if self.test_configuration_persistence():
            tests_passed += 1
        
        # Final results
        print("\n" + "=" * 80)
        print("📊 FINAL TEST RESULTS")
        print("=" * 80)
        print(f"Individual API Tests: {self.tests_passed}/{self.tests_run}")
        print(f"Test Categories: {tests_passed}/{total_tests}")
        
        if self.tests_passed == self.tests_run and tests_passed == total_tests:
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print("⚠️ SOME TESTS FAILED - Check details above")
            return False

def main():
    """Main test execution"""
    tester = GoogleDriveConfigTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
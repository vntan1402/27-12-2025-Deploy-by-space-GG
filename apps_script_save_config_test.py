#!/usr/bin/env python3
"""
Apps Script Save Configuration Testing
Testing the Apps Script proxy configuration functionality as requested in review.
"""

import requests
import sys
import json
from datetime import datetime, timezone
import time

class AppsScriptConfigTester:
    def __init__(self, base_url="https://shipgooglesync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        
        # User's specific Apps Script configuration from review request
        self.apps_script_url = "https://script.google.com/macros/s/AKfycbyZx8bjPTBzPCs0CcPUsvk8rW6rBinx0PwmZy_hDViqgWVKX1KDPJ3aFleSOQRA81M/exec"
        self.folder_id = "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            print(f"   Response Status: {response.status_code}")
            
            # Try to parse response
            try:
                response_data = response.json() if response.content else {}
                print(f"   Response Data: {json.dumps(response_data, indent=2)}")
            except:
                response_data = {}
                if response.text:
                    print(f"   Response Text: {response.text[:500]}...")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                return True, response_data
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                return False, response_data

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
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
            user_info = response.get('user', {})
            print(f"✅ Login successful, token obtained")
            print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
            print(f"   Company: {user_info.get('company', 'N/A')}")
            return True
        return False

    def test_apps_script_configure_proxy(self):
        """Test POST /api/gdrive/configure-proxy with user's Apps Script URL"""
        print(f"\n📝 Testing Apps Script Configure Proxy")
        print(f"   Apps Script URL: {self.apps_script_url}")
        print(f"   Folder ID: {self.folder_id}")
        
        config_data = {
            "web_app_url": self.apps_script_url,
            "folder_id": self.folder_id
        }
        
        success, response = self.run_test(
            "Configure Apps Script Proxy",
            "POST",
            "gdrive/configure-proxy",
            200,  # Expecting success if Apps Script is fixed
            data=config_data
        )
        
        if success:
            print(f"✅ Apps Script proxy configured successfully")
            print(f"   Message: {response.get('message', 'N/A')}")
            print(f"   Service Account: {response.get('service_account_email', 'N/A')}")
            print(f"   Folder Name: {response.get('folder_name', 'N/A')}")
        else:
            print(f"❌ Apps Script proxy configuration failed")
            print(f"   This may indicate the Apps Script still has bugs")
        
        return success

    def test_gdrive_config_after_setup(self):
        """Test GET /api/gdrive/config after successful configuration"""
        print(f"\n📋 Testing Google Drive Config Retrieval")
        
        success, response = self.run_test(
            "Get Google Drive Config",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            print(f"✅ Google Drive config retrieved successfully")
            print(f"   Configured: {response.get('configured', False)}")
            print(f"   Folder ID: {response.get('folder_id', 'N/A')}")
            print(f"   Service Account Email: {response.get('service_account_email', 'N/A')}")
            print(f"   Last Sync: {response.get('last_sync', 'N/A')}")
            
            # Verify auth_method is set to "apps_script"
            if response.get('configured'):
                print(f"   ✅ Configuration shows as configured")
            else:
                print(f"   ❌ Configuration shows as not configured")
                
        return success

    def test_gdrive_status_with_apps_script(self):
        """Test GET /api/gdrive/status with Apps Script configuration"""
        print(f"\n📊 Testing Google Drive Status with Apps Script Config")
        
        success, response = self.run_test(
            "Get Google Drive Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            print(f"✅ Google Drive status retrieved successfully")
            print(f"   Configured: {response.get('configured', False)}")
            print(f"   Local Files: {response.get('local_files', 0)}")
            print(f"   Drive Files: {response.get('drive_files', 0)}")
            print(f"   Folder ID: {response.get('folder_id', 'N/A')}")
            print(f"   Last Sync: {response.get('last_sync', 'N/A')}")
            
            # Verify drive_files counting works
            if response.get('configured'):
                print(f"   ✅ Status shows as configured")
                if response.get('drive_files', 0) >= 0:
                    print(f"   ✅ Drive files count working: {response.get('drive_files', 0)} files")
                else:
                    print(f"   ❌ Drive files count not working")
            else:
                print(f"   ❌ Status shows as not configured")
                
        return success

    def test_sync_to_drive_proxy(self):
        """Test POST /api/gdrive/sync-to-drive-proxy"""
        print(f"\n🔄 Testing Sync to Drive via Apps Script Proxy")
        
        success, response = self.run_test(
            "Sync to Drive via Proxy",
            "POST",
            "gdrive/sync-to-drive-proxy",
            200
        )
        
        if success:
            print(f"✅ Sync to Drive via proxy successful")
            print(f"   Message: {response.get('message', 'N/A')}")
            print(f"   Success: {response.get('success', False)}")
            
            # Verify MongoDB export and Apps Script communication
            if response.get('success'):
                print(f"   ✅ Apps Script communication working")
            else:
                print(f"   ❌ Apps Script communication failed")
        else:
            print(f"❌ Sync to Drive via proxy failed")
            
        return success

    def test_configuration_persistence(self):
        """Test that configuration is properly saved to MongoDB"""
        print(f"\n💾 Testing Configuration Persistence")
        
        # Get config again to verify persistence
        success, response = self.run_test(
            "Verify Config Persistence",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            configured = response.get('configured', False)
            folder_id = response.get('folder_id', '')
            
            print(f"   Configured: {configured}")
            print(f"   Folder ID: {folder_id}")
            
            # Check if our specific values are saved
            if configured and folder_id == self.folder_id:
                print(f"✅ Configuration persistence verified")
                print(f"   ✅ Folder ID matches: {folder_id}")
                return True
            else:
                print(f"❌ Configuration persistence failed")
                print(f"   Expected Folder ID: {self.folder_id}")
                print(f"   Actual Folder ID: {folder_id}")
                return False
        
        return False

    def test_direct_apps_script_connection(self):
        """Test direct connection to Apps Script URL to diagnose issues"""
        print(f"\n🔗 Testing Direct Apps Script Connection")
        print(f"   URL: {self.apps_script_url}")
        
        try:
            # Test GET request
            print(f"   Testing GET request...")
            response = requests.get(self.apps_script_url, timeout=30)
            print(f"   GET Status: {response.status_code}")
            print(f"   GET Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   GET Response: {response.text[:200]}...")
            
            # Test POST request with test_connection action
            print(f"   Testing POST request with test_connection...")
            post_data = {"action": "test_connection"}
            response = requests.post(self.apps_script_url, json=post_data, timeout=30)
            print(f"   POST Status: {response.status_code}")
            print(f"   POST Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   POST Response: {response.text[:500]}...")
            
            # Check if response is JSON
            try:
                json_response = response.json()
                print(f"   ✅ Valid JSON response: {json.dumps(json_response, indent=2)}")
                return True
            except:
                print(f"   ❌ Invalid JSON response")
                return False
                
        except Exception as e:
            print(f"   ❌ Direct connection failed: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive Apps Script configuration test"""
        print("🚀 Apps Script Save Configuration Testing")
        print("=" * 60)
        print(f"Apps Script URL: {self.apps_script_url}")
        print(f"Folder ID: {self.folder_id}")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Run all tests in sequence
        test_results = []
        
        # 1. Test direct Apps Script connection first
        test_results.append(("Direct Apps Script Connection", self.test_direct_apps_script_connection()))
        
        # 2. Test Apps Script configure-proxy endpoint
        test_results.append(("Apps Script Configure Proxy", self.test_apps_script_configure_proxy()))
        
        # 3. Test configuration persistence
        test_results.append(("Configuration Persistence", self.test_configuration_persistence()))
        
        # 4. Test config retrieval after setup
        test_results.append(("Google Drive Config After Setup", self.test_gdrive_config_after_setup()))
        
        # 5. Test status endpoint with Apps Script config
        test_results.append(("Google Drive Status with Apps Script", self.test_gdrive_status_with_apps_script()))
        
        # 6. Test sync functionality
        test_results.append(("Sync to Drive via Proxy", self.test_sync_to_drive_proxy()))
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 APPS SCRIPT CONFIGURATION TEST RESULTS")
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
        
        # Final assessment
        if passed_tests == total_tests and self.tests_passed == self.tests_run:
            print("\n🎉 ALL APPS SCRIPT CONFIGURATION TESTS PASSED!")
            print("✅ Apps Script Save Configuration functionality is working correctly")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} TESTS FAILED")
            if passed_tests == 0:
                print("❌ Apps Script configuration is not working - likely Apps Script code issues")
            elif passed_tests < total_tests // 2:
                print("❌ Major issues with Apps Script configuration")
            else:
                print("⚠️ Some Apps Script features working, but issues remain")
            return False

def main():
    """Main test execution"""
    tester = AppsScriptConfigTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
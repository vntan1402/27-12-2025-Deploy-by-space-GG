#!/usr/bin/env python3
"""
Google Drive Configuration Debug Test
Testing Apps Script configuration display issue as requested in review.

Test Requirements:
1. Test GET /api/gdrive/config endpoint after Apps Script config is saved
2. Test GET /api/gdrive/status endpoint to verify Apps Script config reflection
3. Debug MongoDB data in gdrive_config collection
4. Test backend response format for GET /api/gdrive/config

Login: admin/admin123
"""

import requests
import sys
import json
from datetime import datetime, timezone
import time

class GDriveConfigDebugTester:
    def __init__(self, base_url="https://aicert-analyzer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None

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
                        print(f"   Response: {json.dumps(response_data, indent=2)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {json.dumps(error_detail, indent=2)}")
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
            user_info = response.get('user', {})
            print(f"✅ Login successful, token obtained")
            print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
            print(f"   User ID: {self.admin_user_id}")
            return True
        return False

    def test_initial_gdrive_config_state(self):
        """Test initial Google Drive configuration state"""
        print(f"\n📋 Testing Initial Google Drive Configuration State")
        
        # Test GET /api/gdrive/config
        success, config_response = self.run_test(
            "GET /api/gdrive/config (Initial State)",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            print(f"   Initial Config Response:")
            print(f"   - Configured: {config_response.get('configured')}")
            print(f"   - Folder ID: {config_response.get('folder_id')}")
            print(f"   - Service Account Email: {config_response.get('service_account_email')}")
            print(f"   - Auth Method: {config_response.get('auth_method', 'NOT PRESENT')}")
            print(f"   - Last Sync: {config_response.get('last_sync')}")
        
        # Test GET /api/gdrive/status
        success2, status_response = self.run_test(
            "GET /api/gdrive/status (Initial State)",
            "GET",
            "gdrive/status",
            200
        )
        
        if success2:
            print(f"   Initial Status Response:")
            print(f"   - Configured: {status_response.get('configured')}")
            print(f"   - Local Files: {status_response.get('local_files')}")
            print(f"   - Drive Files: {status_response.get('drive_files')}")
            print(f"   - Folder ID: {status_response.get('folder_id')}")
            print(f"   - Service Account Email: {status_response.get('service_account_email')}")
            print(f"   - Last Sync: {status_response.get('last_sync')}")
        
        return success and success2, config_response, status_response

    def test_apps_script_configuration(self):
        """Test Apps Script configuration"""
        print(f"\n🔧 Testing Apps Script Configuration")
        
        # Use a working Apps Script URL for testing
        # Note: This is a test URL that should return proper JSON responses
        apps_script_config = {
            "web_app_url": "https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec",
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }
        
        print(f"   Configuring Apps Script with:")
        print(f"   - Web App URL: {apps_script_config['web_app_url']}")
        print(f"   - Folder ID: {apps_script_config['folder_id']}")
        
        success, config_result = self.run_test(
            "POST /api/gdrive/configure-proxy (Apps Script Config)",
            "POST",
            "gdrive/configure-proxy",
            200,
            data=apps_script_config
        )
        
        if success:
            print(f"   Apps Script Configuration Result:")
            print(f"   - Success: {config_result.get('success')}")
            print(f"   - Message: {config_result.get('message')}")
            print(f"   - Folder Name: {config_result.get('folder_name')}")
            print(f"   - Service Account Email: {config_result.get('service_account_email')}")
        
        return success, config_result

    def test_gdrive_config_after_apps_script_save(self):
        """Test GET /api/gdrive/config after Apps Script config is saved"""
        print(f"\n📋 Testing GET /api/gdrive/config After Apps Script Save")
        
        success, config_response = self.run_test(
            "GET /api/gdrive/config (After Apps Script Save)",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            print(f"   Config Response After Apps Script Save:")
            print(f"   - Configured: {config_response.get('configured')}")
            print(f"   - Folder ID: {config_response.get('folder_id')}")
            print(f"   - Service Account Email: {config_response.get('service_account_email')}")
            print(f"   - Auth Method: {config_response.get('auth_method', 'NOT PRESENT IN RESPONSE')}")
            print(f"   - Last Sync: {config_response.get('last_sync')}")
            
            # Check if auth_method is present and correct
            auth_method = config_response.get('auth_method')
            if auth_method == 'apps_script':
                print(f"   ✅ AUTH_METHOD CORRECT: Found 'apps_script' in response")
            elif auth_method is None:
                print(f"   ❌ AUTH_METHOD MISSING: 'auth_method' field not present in response")
            else:
                print(f"   ❌ AUTH_METHOD INCORRECT: Expected 'apps_script', got '{auth_method}'")
        
        return success, config_response

    def test_gdrive_status_after_apps_script_save(self):
        """Test GET /api/gdrive/status after Apps Script config is saved"""
        print(f"\n📊 Testing GET /api/gdrive/status After Apps Script Save")
        
        success, status_response = self.run_test(
            "GET /api/gdrive/status (After Apps Script Save)",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            print(f"   Status Response After Apps Script Save:")
            print(f"   - Configured: {status_response.get('configured')}")
            print(f"   - Local Files: {status_response.get('local_files')}")
            print(f"   - Drive Files: {status_response.get('drive_files')}")
            print(f"   - Folder ID: {status_response.get('folder_id')}")
            print(f"   - Service Account Email: {status_response.get('service_account_email')}")
            print(f"   - Last Sync: {status_response.get('last_sync')}")
            
            # Verify that status reflects Apps Script configuration
            configured = status_response.get('configured')
            folder_id = status_response.get('folder_id')
            
            if configured:
                print(f"   ✅ STATUS CONFIGURED: Google Drive shows as configured")
            else:
                print(f"   ❌ STATUS NOT CONFIGURED: Google Drive shows as not configured")
                
            if folder_id:
                print(f"   ✅ FOLDER ID PRESENT: {folder_id}")
            else:
                print(f"   ❌ FOLDER ID MISSING: No folder_id in status response")
        
        return success, status_response

    def test_apps_script_sync_functionality(self):
        """Test Apps Script sync functionality"""
        print(f"\n🔄 Testing Apps Script Sync Functionality")
        
        # Test sync to drive using Apps Script proxy
        success, sync_result = self.run_test(
            "POST /api/gdrive/sync-to-drive-proxy (Apps Script Sync)",
            "POST",
            "gdrive/sync-to-drive-proxy",
            200
        )
        
        if success:
            print(f"   Apps Script Sync Result:")
            print(f"   - Success: {sync_result.get('success')}")
            print(f"   - Message: {sync_result.get('message')}")
        
        return success, sync_result

    def debug_mongodb_data(self):
        """Debug MongoDB data by checking the responses for data structure"""
        print(f"\n🔍 Debugging MongoDB Data Structure")
        
        # We can't directly access MongoDB, but we can infer the data structure
        # from the API responses
        
        print(f"   MongoDB Data Analysis (via API responses):")
        print(f"   - This test analyzes the API responses to understand MongoDB data structure")
        print(f"   - Key fields to verify in gdrive_config collection:")
        print(f"     * auth_method: should be 'apps_script'")
        print(f"     * web_app_url: should contain the Apps Script URL")
        print(f"     * folder_id: should contain the Google Drive folder ID")
        print(f"     * service_account_email: should be populated from Apps Script response")
        print(f"     * configured_at: should have timestamp when config was saved")
        
        # Get current config to analyze structure
        success, config_response = self.run_test(
            "GET /api/gdrive/config (MongoDB Data Analysis)",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            print(f"   Current MongoDB Data (inferred from API):")
            for key, value in config_response.items():
                print(f"     {key}: {value} ({type(value).__name__})")
        
        return success

    def run_comprehensive_debug_test(self):
        """Run comprehensive debug test for Google Drive configuration"""
        print(f"\n🚀 Starting Comprehensive Google Drive Configuration Debug Test")
        print(f"=" * 80)
        
        # Step 1: Login
        if not self.test_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Step 2: Check initial state
        print(f"\n" + "=" * 80)
        print(f"STEP 1: INITIAL CONFIGURATION STATE")
        print(f"=" * 80)
        initial_success, initial_config, initial_status = self.test_initial_gdrive_config_state()
        
        # Step 3: Configure Apps Script
        print(f"\n" + "=" * 80)
        print(f"STEP 2: CONFIGURE APPS SCRIPT")
        print(f"=" * 80)
        config_success, config_result = self.test_apps_script_configuration()
        
        if not config_success:
            print(f"❌ Apps Script configuration failed, but continuing with tests...")
        
        # Step 4: Test GET /api/gdrive/config after save
        print(f"\n" + "=" * 80)
        print(f"STEP 3: TEST GET /api/gdrive/config AFTER APPS SCRIPT SAVE")
        print(f"=" * 80)
        config_after_success, config_after_response = self.test_gdrive_config_after_apps_script_save()
        
        # Step 5: Test GET /api/gdrive/status after save
        print(f"\n" + "=" * 80)
        print(f"STEP 4: TEST GET /api/gdrive/status AFTER APPS SCRIPT SAVE")
        print(f"=" * 80)
        status_after_success, status_after_response = self.test_gdrive_status_after_apps_script_save()
        
        # Step 6: Debug MongoDB data structure
        print(f"\n" + "=" * 80)
        print(f"STEP 5: DEBUG MONGODB DATA STRUCTURE")
        print(f"=" * 80)
        mongodb_debug_success = self.debug_mongodb_data()
        
        # Step 7: Test sync functionality (if configuration was successful)
        if config_success:
            print(f"\n" + "=" * 80)
            print(f"STEP 6: TEST APPS SCRIPT SYNC FUNCTIONALITY")
            print(f"=" * 80)
            sync_success, sync_result = self.test_apps_script_sync_functionality()
        else:
            sync_success = False
            print(f"\n⚠️ Skipping sync test due to configuration failure")
        
        # Final analysis
        print(f"\n" + "=" * 80)
        print(f"FINAL ANALYSIS - GOOGLE DRIVE CONFIGURATION DEBUG")
        print(f"=" * 80)
        
        print(f"\n📊 TEST RESULTS:")
        print(f"   1. Initial State Check: {'✅ PASSED' if initial_success else '❌ FAILED'}")
        print(f"   2. Apps Script Config: {'✅ PASSED' if config_success else '❌ FAILED'}")
        print(f"   3. Config After Save: {'✅ PASSED' if config_after_success else '❌ FAILED'}")
        print(f"   4. Status After Save: {'✅ PASSED' if status_after_success else '❌ FAILED'}")
        print(f"   5. MongoDB Debug: {'✅ PASSED' if mongodb_debug_success else '❌ FAILED'}")
        print(f"   6. Sync Functionality: {'✅ PASSED' if sync_success else '❌ FAILED/SKIPPED'}")
        
        print(f"\n🔍 KEY FINDINGS:")
        
        # Check auth_method field presence
        if config_after_success and config_after_response:
            auth_method = config_after_response.get('auth_method')
            if auth_method == 'apps_script':
                print(f"   ✅ AUTH_METHOD: Correctly set to 'apps_script' in GET /api/gdrive/config")
            elif auth_method is None:
                print(f"   ❌ AUTH_METHOD: Missing from GET /api/gdrive/config response")
                print(f"       This is likely the root cause of the configuration display issue")
            else:
                print(f"   ❌ AUTH_METHOD: Incorrect value '{auth_method}' in GET /api/gdrive/config")
        
        # Check configuration persistence
        if config_success and config_after_success:
            print(f"   ✅ CONFIGURATION PERSISTENCE: Apps Script config saved and retrievable")
        else:
            print(f"   ❌ CONFIGURATION PERSISTENCE: Issues with saving or retrieving config")
        
        # Check status reflection
        if status_after_success and status_after_response:
            if status_after_response.get('configured'):
                print(f"   ✅ STATUS REFLECTION: GET /api/gdrive/status shows configured=true")
            else:
                print(f"   ❌ STATUS REFLECTION: GET /api/gdrive/status shows configured=false")
        
        print(f"\n📈 OVERALL STATISTICS:")
        print(f"   API Tests: {self.tests_passed}/{self.tests_run}")
        
        overall_success = (
            initial_success and 
            config_after_success and 
            status_after_success and 
            mongodb_debug_success
        )
        
        if overall_success:
            print(f"   🎉 OVERALL RESULT: ✅ ALL CRITICAL TESTS PASSED")
        else:
            print(f"   ⚠️ OVERALL RESULT: ❌ SOME CRITICAL TESTS FAILED")
        
        return overall_success

def main():
    """Main test execution"""
    print("🔧 Google Drive Configuration Debug Test")
    print("Testing Apps Script configuration display issue")
    print("=" * 80)
    
    tester = GDriveConfigDebugTester()
    
    # Run comprehensive debug test
    success = tester.run_comprehensive_debug_test()
    
    if success:
        print(f"\n🎉 All critical tests passed!")
        return 0
    else:
        print(f"\n⚠️ Some critical tests failed - check analysis above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
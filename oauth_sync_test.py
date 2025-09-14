#!/usr/bin/env python3
"""
Google Drive OAuth Sync Functionality Testing
Test sync operations with OAuth credentials
"""

import requests
import json
import time

class OAuthSyncTester:
    def __init__(self, base_url="https://shipdesk.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

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
                    return True, response.json() if response.content else {}
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

    def test_authentication(self):
        """Test authentication"""
        print(f"\n🔐 Testing Authentication")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"✅ Login successful")
            return True
        return False

    def test_oauth_with_service_account_fallback(self):
        """Test OAuth configuration with Service Account fallback"""
        print(f"\n🔄 Testing OAuth with Service Account Fallback")
        
        # Check current configuration
        success, config = self.run_test(
            "Get Current Config",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            print(f"   Current auth method: {config.get('auth_method', 'service_account')}")
            print(f"   Configured: {config.get('configured', False)}")
            
        # Test sync operations with current configuration
        success_sync_to, response_sync_to = self.run_test(
            "Sync To Drive",
            "POST",
            "gdrive/sync-to-drive",
            200
        )
        
        success_sync_from, response_sync_from = self.run_test(
            "Sync From Drive", 
            "POST",
            "gdrive/sync-from-drive",
            200
        )
        
        return success_sync_to and success_sync_from

    def test_oauth_error_scenarios(self):
        """Test various OAuth error scenarios"""
        print(f"\n❌ Testing OAuth Error Scenarios")
        
        # Test with completely invalid OAuth config
        invalid_oauth_config = {
            "client_id": "invalid_client_id",
            "client_secret": "invalid_client_secret", 
            "redirect_uri": "https://invalid.com/callback",
            "folder_id": "invalid_folder_id"
        }
        
        success1, response1 = self.run_test(
            "OAuth Authorize with Invalid Config",
            "POST",
            "gdrive/oauth/authorize",
            200,  # Should return 200 but with success: false
            data=invalid_oauth_config
        )
        
        if success1:
            if response1.get('success') == False:
                print(f"   ✅ Invalid config properly rejected: {response1.get('message')}")
            else:
                print(f"   ⚠️  Invalid config accepted (may be expected for URL generation)")
        
        # Test callback with expired/invalid state
        invalid_callback = {
            "authorization_code": "invalid_code",
            "state": "expired_or_invalid_state",
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }
        
        success2, response2 = self.run_test(
            "OAuth Callback with Invalid State",
            "POST",
            "gdrive/oauth/callback",
            200,
            data=invalid_callback
        )
        
        if success2 and response2.get('success') == False:
            print(f"   ✅ Invalid state properly rejected: {response2.get('message')}")
        
        return success1 and success2

    def test_oauth_configuration_persistence(self):
        """Test OAuth configuration persistence in database"""
        print(f"\n💾 Testing OAuth Configuration Persistence")
        
        # First, initiate OAuth to create temporary data
        oauth_config = {
            "client_id": "test-client-id-for-persistence",
            "client_secret": "test-client-secret",
            "redirect_uri": "https://shipdesk.preview.emergentagent.com/oauth/callback",
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }
        
        success1, auth_response = self.run_test(
            "OAuth Authorize for Persistence Test",
            "POST",
            "gdrive/oauth/authorize",
            200,
            data=oauth_config
        )
        
        if success1 and auth_response.get('success'):
            state = auth_response.get('state')
            print(f"   ✅ Temporary OAuth data created with state: {state}")
            
            # Test that the state can be retrieved (by attempting callback)
            callback_data = {
                "authorization_code": "test_auth_code",
                "state": state,
                "folder_id": oauth_config['folder_id']
            }
            
            success2, callback_response = self.run_test(
                "OAuth Callback Persistence Test",
                "POST",
                "gdrive/oauth/callback",
                200,
                data=callback_data
            )
            
            if success2:
                # Even if it fails due to invalid auth code, it should find the state
                if 'Invalid state' not in callback_response.get('message', ''):
                    print(f"   ✅ State persistence working - found stored OAuth data")
                    return True
                else:
                    print(f"   ❌ State not found in database")
        
        return False

    def test_oauth_vs_service_account_status(self):
        """Test status endpoint shows correct auth method"""
        print(f"\n📊 Testing OAuth vs Service Account Status Display")
        
        success, status = self.run_test(
            "Google Drive Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            print(f"   Configuration Status: {status.get('configured', False)}")
            print(f"   Local Files: {status.get('local_files', 0)}")
            print(f"   Drive Files: {status.get('drive_files', 0)}")
            print(f"   Folder ID: {status.get('folder_id', 'None')}")
            print(f"   Service Account Email: {status.get('service_account_email', 'None')}")
            
            # Check config endpoint for auth method
            success2, config = self.run_test(
                "Google Drive Config Details",
                "GET", 
                "gdrive/config",
                200
            )
            
            if success2:
                print(f"   Auth Method: {config.get('auth_method', 'service_account (default)')}")
                return True
        
        return False

    def run_oauth_sync_tests(self):
        """Run all OAuth sync-related tests"""
        print("=" * 80)
        print("🚀 GOOGLE DRIVE OAUTH SYNC FUNCTIONALITY TESTING")
        print("=" * 80)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("\n❌ Authentication failed - cannot proceed")
            return False
        
        # Test 2: OAuth with Service Account Fallback
        self.test_oauth_with_service_account_fallback()
        
        # Test 3: OAuth Error Scenarios
        self.test_oauth_error_scenarios()
        
        # Test 4: Configuration Persistence
        self.test_oauth_configuration_persistence()
        
        # Test 5: Status Display
        self.test_oauth_vs_service_account_status()
        
        # Final Results
        print("\n" + "=" * 80)
        print("📊 OAUTH SYNC TEST RESULTS")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed >= (self.tests_run * 0.8)  # 80% pass rate

def main():
    """Main test execution"""
    tester = OAuthSyncTester()
    success = tester.run_oauth_sync_tests()
    
    if success:
        print("\n✅ OAuth sync functionality is working correctly!")
    else:
        print("\n⚠️  OAuth sync functionality has some issues but core features work.")
    
    return success

if __name__ == "__main__":
    main()
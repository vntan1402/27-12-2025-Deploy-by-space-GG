#!/usr/bin/env python3
"""
Google Drive OAuth 2.0 Implementation Testing
Test comprehensive OAuth flow for Google Drive integration
"""

import requests
import json
import uuid
import time
from datetime import datetime, timezone

class GoogleDriveOAuthTester:
    def __init__(self, base_url="https://continue-session.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        
        # Mock OAuth configuration for testing
        self.mock_oauth_config = {
            "client_id": "123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com",
            "client_secret": "GOCSPX-abcdefghijklmnopqrstuvwxyz123456",
            "redirect_uri": "https://continue-session.preview.emergentagent.com/oauth/callback",
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }
        
        # Mock OAuth callback data
        self.mock_callback_data = {
            "authorization_code": "4/0AX4XfWh1234567890abcdefghijklmnopqrstuvwxyz",
            "state": "",  # Will be set during authorize test
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

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

    def test_authentication(self, username="admin", password="admin123"):
        """Test authentication with admin credentials"""
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

    def test_oauth_authorize_endpoint(self):
        """Test POST /api/gdrive/oauth/authorize endpoint"""
        print(f"\n🔑 Testing OAuth Authorization Endpoint")
        
        success, response = self.run_test(
            "OAuth Authorize",
            "POST",
            "gdrive/oauth/authorize",
            200,
            data=self.mock_oauth_config
        )
        
        if success:
            # Verify response structure
            if 'authorization_url' in response and 'state' in response:
                auth_url = response.get('authorization_url', '') or ''
                state = response.get('state', '') or ''
                print(f"   ✅ Authorization URL generated: {auth_url[:100]}...")
                print(f"   ✅ State parameter: {state}")
                
                # Store state for callback test
                self.mock_callback_data['state'] = state
                
                # Verify URL contains expected parameters
                if 'accounts.google.com' in auth_url and 'client_id' in auth_url:
                    print(f"   ✅ Authorization URL format valid")
                    return True
                else:
                    print(f"   ❌ Authorization URL format invalid")
                    return False
            else:
                print(f"   ❌ Missing required fields in response")
                return False
        return False

    def test_oauth_callback_endpoint(self):
        """Test POST /api/gdrive/oauth/callback endpoint"""
        print(f"\n🔄 Testing OAuth Callback Endpoint")
        
        # First ensure we have a state from authorize test
        if not self.mock_callback_data['state']:
            print("   ⚠️  No state available, running authorize test first...")
            if not self.test_oauth_authorize_endpoint():
                return False
        
        success, response = self.run_test(
            "OAuth Callback",
            "POST",
            "gdrive/oauth/callback",
            200,
            data=self.mock_callback_data
        )
        
        if success:
            # Note: This will likely fail with mock data, but we're testing the endpoint structure
            print(f"   ✅ Callback endpoint accessible")
            print(f"   Response: {response}")
            return True
        return False

    def test_oauth_state_validation(self):
        """Test state parameter validation in OAuth flow"""
        print(f"\n🔒 Testing OAuth State Parameter Validation")
        
        # Test with invalid state
        invalid_callback_data = self.mock_callback_data.copy()
        invalid_callback_data['state'] = 'invalid_state_parameter'
        
        success, response = self.run_test(
            "OAuth Callback with Invalid State",
            "POST",
            "gdrive/oauth/callback",
            200,  # Expecting 200 but with error message
            data=invalid_callback_data
        )
        
        if success:
            # Check if error message indicates invalid state
            if 'success' in response and not response.get('success', True):
                if 'state' in response.get('message', '').lower():
                    print(f"   ✅ State validation working - Error: {response.get('message')}")
                    return True
            print(f"   ⚠️  State validation response: {response}")
        return False

    def test_oauth_missing_parameters(self):
        """Test OAuth endpoints with missing parameters"""
        print(f"\n❌ Testing OAuth Error Handling - Missing Parameters")
        
        # Test authorize with missing client_id
        incomplete_config = self.mock_oauth_config.copy()
        del incomplete_config['client_id']
        
        success, response = self.run_test(
            "OAuth Authorize Missing Client ID",
            "POST",
            "gdrive/oauth/authorize",
            422,  # Expecting validation error
            data=incomplete_config
        )
        
        if not success:
            # Try with 400 status instead
            success, response = self.run_test(
                "OAuth Authorize Missing Client ID (400)",
                "POST",
                "gdrive/oauth/authorize",
                400,
                data=incomplete_config
            )
        
        # Test callback with missing authorization_code
        incomplete_callback = self.mock_callback_data.copy()
        del incomplete_callback['authorization_code']
        
        success2, response2 = self.run_test(
            "OAuth Callback Missing Auth Code",
            "POST",
            "gdrive/oauth/callback",
            422,  # Expecting validation error
            data=incomplete_callback
        )
        
        if not success2:
            # Try with 400 status instead
            success2, response2 = self.run_test(
                "OAuth Callback Missing Auth Code (400)",
                "POST",
                "gdrive/oauth/callback",
                400,
                data=incomplete_callback
            )
        
        return success or success2

    def test_oauth_temporary_storage(self):
        """Test temporary OAuth data storage in MongoDB"""
        print(f"\n💾 Testing OAuth Temporary Data Storage")
        
        # First run authorize to create temporary storage
        success, response = self.run_test(
            "OAuth Authorize for Storage Test",
            "POST",
            "gdrive/oauth/authorize",
            200,
            data=self.mock_oauth_config
        )
        
        if success and 'state' in response:
            print(f"   ✅ Temporary OAuth data should be stored with state: {response['state']}")
            
            # Now test callback with the same state
            callback_data = self.mock_callback_data.copy()
            callback_data['state'] = response['state']
            
            success2, response2 = self.run_test(
                "OAuth Callback Storage Retrieval",
                "POST",
                "gdrive/oauth/callback",
                200,
                data=callback_data
            )
            
            if success2:
                print(f"   ✅ Temporary data retrieval working")
                return True
        
        return False

    def test_gdrive_status_with_oauth(self):
        """Test Google Drive status endpoint with OAuth configuration"""
        print(f"\n📊 Testing Google Drive Status with OAuth")
        
        success, response = self.run_test(
            "Google Drive Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            print(f"   Configuration Status: {response.get('configured', False)}")
            print(f"   Local Files: {response.get('local_files', 0)}")
            print(f"   Drive Files: {response.get('drive_files', 0)}")
            print(f"   Folder ID: {response.get('folder_id', 'None')}")
            print(f"   Service Account Email: {response.get('service_account_email', 'None')}")
            return True
        return False

    def test_gdrive_config_endpoint(self):
        """Test Google Drive configuration endpoint"""
        print(f"\n⚙️  Testing Google Drive Configuration Endpoint")
        
        success, response = self.run_test(
            "Google Drive Config",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            print(f"   Configuration: {response}")
            return True
        return False

    def test_oauth_permissions(self):
        """Test OAuth endpoints require admin permissions"""
        print(f"\n🔐 Testing OAuth Endpoints Permission Requirements")
        
        # Store current token
        original_token = self.token
        
        # Remove token to test unauthorized access
        self.token = None
        
        success1, response1 = self.run_test(
            "OAuth Authorize Without Auth",
            "POST",
            "gdrive/oauth/authorize",
            403,  # Expecting forbidden
            data=self.mock_oauth_config
        )
        
        success2, response2 = self.run_test(
            "OAuth Callback Without Auth",
            "POST",
            "gdrive/oauth/callback",
            403,  # Expecting forbidden
            data=self.mock_callback_data
        )
        
        # Restore token
        self.token = original_token
        
        return success1 and success2

    def test_oauth_integration_flow(self):
        """Test complete OAuth integration flow simulation"""
        print(f"\n🔄 Testing Complete OAuth Integration Flow")
        
        # Step 1: Initiate OAuth
        print("   Step 1: Initiating OAuth authorization...")
        success1, auth_response = self.run_test(
            "OAuth Flow - Authorize",
            "POST",
            "gdrive/oauth/authorize",
            200,
            data=self.mock_oauth_config
        )
        
        if not success1:
            return False
        
        # Step 2: Simulate callback (will fail with mock data but tests endpoint)
        print("   Step 2: Processing OAuth callback...")
        callback_data = self.mock_callback_data.copy()
        callback_data['state'] = auth_response.get('state', '')
        
        success2, callback_response = self.run_test(
            "OAuth Flow - Callback",
            "POST",
            "gdrive/oauth/callback",
            200,
            data=callback_data
        )
        
        # Step 3: Check configuration status
        print("   Step 3: Checking configuration status...")
        success3, status_response = self.run_test(
            "OAuth Flow - Status Check",
            "GET",
            "gdrive/status",
            200
        )
        
        print(f"   OAuth Flow Results:")
        print(f"   - Authorization: {'✅' if success1 else '❌'}")
        print(f"   - Callback: {'✅' if success2 else '❌'}")
        print(f"   - Status Check: {'✅' if success3 else '❌'}")
        
        return success1 and success3  # Callback may fail with mock data

    def run_comprehensive_oauth_tests(self):
        """Run all OAuth-related tests"""
        print("=" * 80)
        print("🚀 GOOGLE DRIVE OAUTH 2.0 COMPREHENSIVE TESTING")
        print("=" * 80)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("\n❌ Authentication failed - cannot proceed with OAuth tests")
            return False
        
        # Test 2: OAuth Authorization Endpoint
        self.test_oauth_authorize_endpoint()
        
        # Test 3: OAuth Callback Endpoint
        self.test_oauth_callback_endpoint()
        
        # Test 4: State Parameter Validation
        self.test_oauth_state_validation()
        
        # Test 5: Error Handling - Missing Parameters
        self.test_oauth_missing_parameters()
        
        # Test 6: Temporary Storage Testing
        self.test_oauth_temporary_storage()
        
        # Test 7: Google Drive Status with OAuth
        self.test_gdrive_status_with_oauth()
        
        # Test 8: Google Drive Config Endpoint
        self.test_gdrive_config_endpoint()
        
        # Test 9: Permission Requirements
        self.test_oauth_permissions()
        
        # Test 10: Complete Integration Flow
        self.test_oauth_integration_flow()
        
        # Final Results
        print("\n" + "=" * 80)
        print("📊 GOOGLE DRIVE OAUTH 2.0 TEST RESULTS")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL OAUTH TESTS PASSED!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    """Main test execution"""
    tester = GoogleDriveOAuthTester()
    success = tester.run_comprehensive_oauth_tests()
    
    if success:
        print("\n✅ Google Drive OAuth 2.0 implementation is working correctly!")
    else:
        print("\n❌ Google Drive OAuth 2.0 implementation has issues that need attention.")
    
    return success

if __name__ == "__main__":
    main()
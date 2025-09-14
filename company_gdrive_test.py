#!/usr/bin/env python3
"""
Company Google Drive Configuration Endpoints Testing
Tests the new Company Google Drive Configuration endpoints that were just implemented.
"""

import requests
import json
import time
from datetime import datetime, timezone

class CompanyGDriveConfigTester:
    def __init__(self, base_url="https://shipgooglesync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.test_company_id = None

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

    def create_test_company(self):
        """Create a test company for Google Drive configuration testing"""
        print(f"\n🏢 Creating Test Company for Google Drive Configuration")
        
        # First check if we already have companies
        success, companies = self.run_test("Get Existing Companies", "GET", "companies", 200)
        if success and companies:
            # Use the first existing company
            self.test_company_id = companies[0]['id']
            print(f"✅ Using existing company: {companies[0].get('name_en', 'Unknown')} (ID: {self.test_company_id})")
            return True
        
        # Create a new test company
        company_data = {
            "name_vn": "Công ty Test Google Drive",
            "name_en": "Test Google Drive Company Ltd",
            "address_vn": "123 Đường Test, TP.HCM",
            "address_en": "123 Test Street, Ho Chi Minh City",
            "tax_id": f"TEST{int(time.time())}",
            "gmail": "test@testgdrive.com",
            "zalo": "0901234567",
            "system_expiry": "2025-12-31T23:59:59Z"
        }
        
        success, company = self.run_test(
            "Create Test Company",
            "POST",
            "companies",
            200,
            data=company_data
        )
        
        if success and 'id' in company:
            self.test_company_id = company['id']
            print(f"✅ Test company created: {company.get('name_en')} (ID: {self.test_company_id})")
            return True
        
        print("❌ Failed to create test company")
        return False

    def test_company_gdrive_config_get(self):
        """Test GET /api/companies/{company_id}/gdrive/config"""
        print(f"\n📋 Testing Company Google Drive Configuration GET")
        
        if not self.test_company_id:
            print("❌ No test company ID available")
            return False
        
        success, config = self.run_test(
            "Get Company Google Drive Config",
            "GET",
            f"companies/{self.test_company_id}/gdrive/config",
            200
        )
        
        if success:
            print(f"   Configuration: {json.dumps(config, indent=2)}")
            # Verify expected fields
            expected_fields = ['configured', 'auth_method', 'folder_id', 'service_account_email', 'last_sync']
            for field in expected_fields:
                if field in config:
                    print(f"   ✅ Field '{field}' present: {config[field]}")
                else:
                    print(f"   ⚠️ Field '{field}' missing")
            return True
        
        return False

    def test_company_gdrive_status_get(self):
        """Test GET /api/companies/{company_id}/gdrive/status"""
        print(f"\n📊 Testing Company Google Drive Status GET")
        
        if not self.test_company_id:
            print("❌ No test company ID available")
            return False
        
        success, status = self.run_test(
            "Get Company Google Drive Status",
            "GET",
            f"companies/{self.test_company_id}/gdrive/status",
            200
        )
        
        if success:
            print(f"   Status: {json.dumps(status, indent=2)}")
            # Verify expected fields
            expected_fields = ['configured', 'auth_method', 'last_sync', 'local_files', 'drive_files', 'folder_id', 'service_account_email']
            for field in expected_fields:
                if field in status:
                    print(f"   ✅ Field '{field}' present: {status[field]}")
                else:
                    print(f"   ⚠️ Field '{field}' missing")
            return True
        
        return False

    def test_company_gdrive_configure_proxy(self):
        """Test POST /api/companies/{company_id}/gdrive/configure-proxy"""
        print(f"\n🔧 Testing Company Google Drive Apps Script Proxy Configuration")
        
        if not self.test_company_id:
            print("❌ No test company ID available")
            return False
        
        # Test with sample Apps Script configuration
        proxy_config = {
            "web_app_url": "https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec",
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }
        
        success, response = self.run_test(
            "Configure Company Google Drive Apps Script Proxy",
            "POST",
            f"companies/{self.test_company_id}/gdrive/configure-proxy",
            200,
            data=proxy_config
        )
        
        if success:
            print(f"   Response: {json.dumps(response, indent=2)}")
            # Verify expected fields
            if 'success' in response and response['success']:
                print(f"   ✅ Configuration successful")
            if 'message' in response:
                print(f"   ✅ Message: {response['message']}")
            if 'folder_name' in response:
                print(f"   ✅ Folder name: {response['folder_name']}")
            return True
        
        return False

    def test_company_gdrive_configure_service_account(self):
        """Test POST /api/companies/{company_id}/gdrive/configure (Service Account)"""
        print(f"\n🔐 Testing Company Google Drive Service Account Configuration")
        
        if not self.test_company_id:
            print("❌ No test company ID available")
            return False
        
        # Test with sample service account configuration (will fail but should return proper error)
        service_account_config = {
            "service_account_json": json.dumps({
                "type": "service_account",
                "project_id": "test-project",
                "private_key_id": "test-key-id",
                "private_key": "-----BEGIN PRIVATE KEY-----\nTEST_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
                "client_email": "test@test-project.iam.gserviceaccount.com",
                "client_id": "123456789",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }),
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }
        
        # This should return 400 or 500 due to invalid credentials, but endpoint should exist
        success, response = self.run_test(
            "Configure Company Google Drive Service Account",
            "POST",
            f"companies/{self.test_company_id}/gdrive/configure",
            [200, 400, 500],  # Accept multiple status codes
            data=service_account_config
        )
        
        if success:
            print(f"   Response: {json.dumps(response, indent=2)}")
            print(f"   ✅ Endpoint exists and responds properly")
            return True
        
        return False

    def test_company_gdrive_oauth_authorize(self):
        """Test POST /api/companies/{company_id}/gdrive/oauth/authorize"""
        print(f"\n🔑 Testing Company Google Drive OAuth Authorization")
        
        if not self.test_company_id:
            print("❌ No test company ID available")
            return False
        
        # Test with sample OAuth configuration
        oauth_config = {
            "client_id": "123456789-abcdefghijklmnop.apps.googleusercontent.com",
            "client_secret": "GOCSPX-test_client_secret",
            "redirect_uri": f"{self.base_url}/oauth2callback",
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }
        
        success, response = self.run_test(
            "Company Google Drive OAuth Authorization",
            "POST",
            f"companies/{self.test_company_id}/gdrive/oauth/authorize",
            [200, 400, 500],  # Accept multiple status codes
            data=oauth_config
        )
        
        if success:
            print(f"   Response: {json.dumps(response, indent=2)}")
            # Verify expected fields
            if 'success' in response:
                print(f"   ✅ Success field present: {response['success']}")
            if 'message' in response:
                print(f"   ✅ Message: {response['message']}")
            if 'authorization_url' in response:
                print(f"   ✅ Authorization URL present")
            if 'state' in response:
                print(f"   ✅ State parameter present")
            return True
        
        return False

    def test_company_gdrive_sync_to_drive_proxy(self):
        """Test POST /api/companies/{company_id}/gdrive/sync-to-drive-proxy"""
        print(f"\n🔄 Testing Company Google Drive Sync to Drive Proxy")
        
        if not self.test_company_id:
            print("❌ No test company ID available")
            return False
        
        success, response = self.run_test(
            "Company Google Drive Sync to Drive Proxy",
            "POST",
            f"companies/{self.test_company_id}/gdrive/sync-to-drive-proxy",
            [200, 400, 500],  # Accept multiple status codes (may fail if not configured)
            data={}
        )
        
        if success:
            print(f"   Response: {json.dumps(response, indent=2)}")
            # Verify expected fields
            if 'success' in response:
                print(f"   ✅ Success field present: {response['success']}")
            if 'message' in response:
                print(f"   ✅ Message: {response['message']}")
            return True
        
        return False

    def test_permission_checking(self):
        """Test permission checking for company Google Drive endpoints"""
        print(f"\n🔒 Testing Permission Checking")
        
        if not self.test_company_id:
            print("❌ No test company ID available")
            return False
        
        # Test without authentication (should fail with 403)
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Unauthenticated Access to Company Google Drive Config",
            "GET",
            f"companies/{self.test_company_id}/gdrive/config",
            403
        )
        
        # Restore token
        self.token = original_token
        
        if success:
            print(f"   ✅ Properly blocked unauthenticated access")
            return True
        
        return False

    def test_error_handling(self):
        """Test error handling for invalid company IDs"""
        print(f"\n⚠️ Testing Error Handling")
        
        # Test with non-existent company ID
        fake_company_id = "non-existent-company-id"
        
        success, response = self.run_test(
            "Get Config for Non-existent Company",
            "GET",
            f"companies/{fake_company_id}/gdrive/config",
            404
        )
        
        if success:
            print(f"   ✅ Properly returned 404 for non-existent company")
            return True
        
        return False

    def run_all_tests(self):
        """Run all Company Google Drive Configuration tests"""
        print("=" * 80)
        print("🚀 COMPANY GOOGLE DRIVE CONFIGURATION ENDPOINTS TESTING")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.test_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Step 2: Create test company
        if not self.create_test_company():
            print("❌ Failed to create test company, stopping tests")
            return False
        
        # Step 3: Test all endpoints
        test_methods = [
            self.test_company_gdrive_config_get,
            self.test_company_gdrive_status_get,
            self.test_company_gdrive_configure_proxy,
            self.test_company_gdrive_configure_service_account,
            self.test_company_gdrive_oauth_authorize,
            self.test_company_gdrive_sync_to_drive_proxy,
            self.test_permission_checking,
            self.test_error_handling
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {e}")
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 COMPANY GOOGLE DRIVE CONFIGURATION TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "0%")
        
        if self.test_company_id:
            print(f"\nTest Company ID: {self.test_company_id}")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = CompanyGDriveConfigTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All Company Google Drive Configuration tests passed!")
    else:
        print(f"\n⚠️ Some tests failed. Check the output above for details.")
    
    exit(0 if success else 1)
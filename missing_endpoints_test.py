#!/usr/bin/env python3
"""
Missing Endpoints Testing for Ship Management System
Tests the newly added endpoints to fix reported issues as per review request.
"""

import requests
import sys
import json
from datetime import datetime, timezone
import time

class MissingEndpointsTester:
    def __init__(self, base_url="https://shipdesk.preview.emergentagent.com"):
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
                        print(f"   Response preview: {str(response_data)[:200]}...")
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

    def test_authentication(self, username="admin", password="admin123"):
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

    def test_company_management_fix(self):
        """Test Company Management Fix Verification"""
        print(f"\n🏢 Testing Company Management Fix Verification")
        
        # Test GET /api/companies - ensure it returns companies properly
        success, companies = self.run_test(
            "GET /api/companies",
            "GET",
            "companies",
            200
        )
        
        if not success:
            print("❌ Company Management Fix FAILED - GET /api/companies not working")
            return False
        
        if not companies:
            print("⚠️ Company Management Fix - No companies found in database")
            return False
        
        print(f"✅ Company Management Fix - Found {len(companies)} companies")
        for i, company in enumerate(companies[:3]):  # Show first 3 companies
            print(f"   Company {i+1}: {company.get('name_en', 'N/A')} / {company.get('name_vn', 'N/A')}")
            print(f"              Tax ID: {company.get('tax_id', 'N/A')}")
            print(f"              Gmail: {company.get('gmail', 'N/A')}")
        
        return True

    def test_missing_endpoints(self):
        """Test Missing Endpoints Now Added"""
        print(f"\n🔧 Testing Missing Endpoints Now Added")
        
        endpoints_to_test = [
            ("GET /api/ships", "ships", "ships"),
            ("GET /api/certificates", "certificates", "certificates"),
            ("GET /api/ai-config", "ai-config", "AI configuration"),
            ("GET /api/usage-stats", "usage-stats", "usage statistics"),
            ("GET /api/settings", "settings", "system settings")
        ]
        
        all_passed = True
        
        for endpoint_name, endpoint_path, description in endpoints_to_test:
            success, data = self.run_test(
                endpoint_name,
                "GET",
                endpoint_path,
                200
            )
            
            if not success:
                print(f"❌ {endpoint_name} FAILED - {description} endpoint not working")
                all_passed = False
            else:
                print(f"✅ {endpoint_name} WORKING - {description} returned successfully")
                
                # Show specific data for each endpoint
                if endpoint_path == "ships" and isinstance(data, list):
                    print(f"   Found {len(data)} ships")
                    if data:
                        print(f"   Sample ship: {data[0].get('name', 'N/A')} (IMO: {data[0].get('imo', 'N/A')})")
                
                elif endpoint_path == "certificates" and isinstance(data, list):
                    print(f"   Found {len(data)} certificates")
                    if data:
                        print(f"   Sample certificate: {data[0].get('type', 'N/A')} for ship {data[0].get('ship_id', 'N/A')}")
                
                elif endpoint_path == "ai-config":
                    print(f"   AI Provider: {data.get('provider', 'N/A')}")
                    print(f"   AI Model: {data.get('model', 'N/A')}")
                
                elif endpoint_path == "usage-stats":
                    print(f"   Total Requests: {data.get('total_requests', 0)}")
                    print(f"   Date Range: {data.get('date_range', 'N/A')}")
                
                elif endpoint_path == "settings":
                    print(f"   System Name: {data.get('system_name', 'N/A')}")
                    print(f"   Version: {data.get('version', 'N/A')}")
        
        return all_passed

    def test_google_drive_configuration_fix(self):
        """Test Google Drive Configuration Fix"""
        print(f"\n☁️ Testing Google Drive Configuration Fix")
        
        # Test GET /api/gdrive/config - verify configuration is returned
        success, config = self.run_test(
            "GET /api/gdrive/config",
            "GET",
            "gdrive/config",
            200
        )
        
        if not success:
            print("❌ Google Drive Configuration Fix FAILED - GET /api/gdrive/config not working")
            return False
        
        print(f"✅ GET /api/gdrive/config WORKING")
        print(f"   Configured: {config.get('configured', False)}")
        print(f"   Folder ID: {config.get('folder_id', 'N/A')}")
        print(f"   Service Account Email: {config.get('service_account_email', 'N/A')}")
        
        # Test GET /api/gdrive/status - verify status is working
        success, status = self.run_test(
            "GET /api/gdrive/status",
            "GET",
            "gdrive/status",
            200
        )
        
        if not success:
            print("❌ Google Drive Configuration Fix FAILED - GET /api/gdrive/status not working")
            return False
        
        print(f"✅ GET /api/gdrive/status WORKING")
        print(f"   Configured: {status.get('configured', False)}")
        print(f"   Local Files: {status.get('local_files', 0)}")
        print(f"   Drive Files: {status.get('drive_files', 0)}")
        print(f"   Last Sync: {status.get('last_sync', 'Never')}")
        
        return True

    def run_comprehensive_test(self):
        """Run all tests for the review request"""
        print("🚢 Missing Endpoints Testing for Ship Management System")
        print("=" * 60)
        print("Testing newly added endpoints to fix reported issues:")
        print("1. Company Management Fix Verification")
        print("2. Missing Endpoints Now Added")
        print("3. Google Drive Configuration Fix")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_authentication():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Run all test categories
        test_results = []
        
        test_results.append(("Company Management Fix", self.test_company_management_fix()))
        test_results.append(("Missing Endpoints", self.test_missing_endpoints()))
        test_results.append(("Google Drive Configuration Fix", self.test_google_drive_configuration_fix()))
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 MISSING ENDPOINTS TEST RESULTS SUMMARY")
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
        
        success = passed_tests == total_tests and self.tests_passed == self.tests_run
        
        if success:
            print("🎉 All missing endpoints tests passed!")
            print("✅ Company Management and Google Drive configuration issues resolved")
            print("✅ All critical endpoints are now working and returning proper data from MongoDB")
        else:
            print("⚠️ Some tests failed - check logs above for details")
        
        return success

def main():
    """Main test execution"""
    tester = MissingEndpointsTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
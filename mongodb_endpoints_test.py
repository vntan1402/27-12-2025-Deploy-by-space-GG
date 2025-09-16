#!/usr/bin/env python3
"""
MongoDB Endpoints Testing for Ship Management System
Testing the newly added MongoDB endpoints for reported issues:
1. Company Management Issues
2. Google Drive Configuration Issues  
3. Data Verification
"""

import requests
import sys
import json
from datetime import datetime, timezone
import time

class MongoDBEndpointsTester:
    def __init__(self, base_url="https://aicert-analyzer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_data = None

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

    def test_authentication(self):
        """Test authentication with admin/admin123 credentials"""
        print(f"\n🔐 Testing Authentication with admin/admin123")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_data = response.get('user', {})
            print(f"✅ Login successful, token obtained")
            print(f"   User: {self.admin_user_data.get('full_name')} ({self.admin_user_data.get('role')})")
            print(f"   Company: {self.admin_user_data.get('company', 'None')}")
            return True
        return False

    def test_company_management_endpoints(self):
        """Test Company Management MongoDB endpoints"""
        print(f"\n🏢 Testing Company Management MongoDB Endpoints")
        
        # Test GET /api/companies - verify companies are returned from MongoDB
        success, companies = self.run_test(
            "GET /api/companies",
            "GET",
            "companies",
            200
        )
        
        if not success:
            print("❌ CRITICAL: GET /api/companies failed")
            return False
        
        print(f"   ✅ Found {len(companies)} companies in MongoDB")
        
        # Verify company data structure and content
        if companies:
            company = companies[0]
            required_fields = ['id', 'name_vn', 'name_en', 'created_at']
            missing_fields = [field for field in required_fields if field not in company]
            
            if missing_fields:
                print(f"   ❌ Missing required fields in company data: {missing_fields}")
                return False
            else:
                print(f"   ✅ Company data structure verified")
                print(f"   Sample company: {company.get('name_en', 'N/A')} / {company.get('name_vn', 'N/A')}")
        else:
            print(f"   ⚠️ WARNING: No companies found in MongoDB - this may explain why Company Management shows no content")
            return False
        
        # Test individual company retrieval
        if companies:
            company_id = companies[0]['id']
            success, company_detail = self.run_test(
                f"GET /api/companies/{company_id}",
                "GET",
                f"companies/{company_id}",
                200
            )
            
            if success:
                print(f"   ✅ Individual company retrieval working")
                print(f"   Company details: {company_detail.get('name_en')} (ID: {company_id})")
            else:
                print(f"   ❌ Individual company retrieval failed")
                return False
        
        return True

    def test_google_drive_configuration_endpoints(self):
        """Test Google Drive Configuration MongoDB endpoints"""
        print(f"\n☁️ Testing Google Drive Configuration MongoDB Endpoints")
        
        # Test GET /api/gdrive/config - verify configuration is returned
        success, gdrive_config = self.run_test(
            "GET /api/gdrive/config",
            "GET",
            "gdrive/config",
            200
        )
        
        if not success:
            print("❌ CRITICAL: GET /api/gdrive/config failed")
            return False
        
        print(f"   ✅ Google Drive config endpoint working")
        print(f"   Configuration status: {'Configured' if gdrive_config.get('configured') else 'Not configured'}")
        
        if gdrive_config.get('configured'):
            print(f"   Folder ID: {gdrive_config.get('folder_id', 'N/A')}")
            print(f"   Service Account: {gdrive_config.get('service_account_email', 'N/A')}")
            print(f"   Last Sync: {gdrive_config.get('last_sync', 'Never')}")
        else:
            print(f"   ⚠️ WARNING: Google Drive not configured - this may explain missing configuration")
        
        # Test GET /api/gdrive/status - verify status information
        success, gdrive_status = self.run_test(
            "GET /api/gdrive/status",
            "GET",
            "gdrive/status",
            200
        )
        
        if not success:
            print("❌ CRITICAL: GET /api/gdrive/status failed")
            return False
        
        print(f"   ✅ Google Drive status endpoint working")
        print(f"   Status configured: {gdrive_status.get('configured', False)}")
        print(f"   Local files count: {gdrive_status.get('local_files', 0)}")
        print(f"   Drive files count: {gdrive_status.get('drive_files', 0)}")
        
        # Verify required fields in status response
        required_status_fields = ['configured', 'local_files', 'drive_files']
        missing_fields = [field for field in required_status_fields if field not in gdrive_status]
        
        if missing_fields:
            print(f"   ❌ Missing required fields in status response: {missing_fields}")
            return False
        else:
            print(f"   ✅ Google Drive status data structure verified")
        
        return True

    def test_mongodb_data_verification(self):
        """Test MongoDB data verification"""
        print(f"\n🗄️ Testing MongoDB Data Verification")
        
        # Verify that companies exist in MongoDB database
        success, companies = self.run_test(
            "Verify Companies in MongoDB",
            "GET",
            "companies",
            200
        )
        
        if success:
            companies_count = len(companies)
            print(f"   ✅ Companies in MongoDB: {companies_count}")
            
            if companies_count == 0:
                print(f"   ❌ CRITICAL ISSUE: No companies found in MongoDB")
                print(f"   This explains why Company Management shows no content")
                return False
            
            # Check company data quality
            valid_companies = 0
            for company in companies:
                if company.get('name_en') and company.get('name_vn') and company.get('id'):
                    valid_companies += 1
            
            print(f"   ✅ Valid companies with complete data: {valid_companies}/{companies_count}")
            
            if valid_companies < companies_count:
                print(f"   ⚠️ WARNING: Some companies have incomplete data")
        else:
            print(f"   ❌ CRITICAL: Cannot verify companies in MongoDB")
            return False
        
        # Test user data to verify admin user has proper company assignment
        success, users = self.run_test(
            "Verify Users in MongoDB",
            "GET",
            "users",
            200
        )
        
        if success:
            users_count = len(users)
            print(f"   ✅ Users in MongoDB: {users_count}")
            
            # Find admin user and check company assignment
            admin_user = None
            for user in users:
                if user.get('username') == 'admin':
                    admin_user = user
                    break
            
            if admin_user:
                admin_company = admin_user.get('company')
                print(f"   ✅ Admin user found with company: {admin_company}")
                
                # Check if admin's company exists in companies list
                if admin_company:
                    matching_companies = [c for c in companies if 
                                        c.get('name_en') == admin_company or 
                                        c.get('name_vn') == admin_company]
                    
                    if matching_companies:
                        print(f"   ✅ Admin's company '{admin_company}' found in companies list")
                    else:
                        print(f"   ❌ CRITICAL: Admin's company '{admin_company}' NOT found in companies list")
                        print(f"   This may cause Company Management visibility issues")
                        return False
                else:
                    print(f"   ⚠️ WARNING: Admin user has no company assigned")
            else:
                print(f"   ❌ Admin user not found in users list")
                return False
        else:
            print(f"   ❌ CRITICAL: Cannot verify users in MongoDB")
            return False
        
        return True

    def test_endpoint_permissions(self):
        """Test endpoint permissions for admin user"""
        print(f"\n🔒 Testing Endpoint Permissions for Admin User")
        
        # Test that admin user can access company endpoints
        success, companies = self.run_test(
            "Admin Access to Companies",
            "GET",
            "companies",
            200
        )
        
        if success:
            print(f"   ✅ Admin user can access companies endpoint")
        else:
            print(f"   ❌ CRITICAL: Admin user cannot access companies endpoint")
            return False
        
        # Test that admin user can access Google Drive endpoints
        success, gdrive_config = self.run_test(
            "Admin Access to Google Drive Config",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            print(f"   ✅ Admin user can access Google Drive config endpoint")
        else:
            print(f"   ❌ CRITICAL: Admin user cannot access Google Drive config endpoint")
            return False
        
        success, gdrive_status = self.run_test(
            "Admin Access to Google Drive Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            print(f"   ✅ Admin user can access Google Drive status endpoint")
        else:
            print(f"   ❌ CRITICAL: Admin user cannot access Google Drive status endpoint")
            return False
        
        return True

    def run_comprehensive_test(self):
        """Run comprehensive MongoDB endpoints test"""
        print("🗄️ MongoDB Endpoints Testing for Ship Management System")
        print("=" * 60)
        print("Testing newly added MongoDB endpoints for reported issues:")
        print("1. Company Management Issues")
        print("2. Google Drive Configuration Issues")
        print("3. Data Verification")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_authentication():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Run all tests
        test_results = []
        
        test_results.append(("Company Management Endpoints", self.test_company_management_endpoints()))
        test_results.append(("Google Drive Configuration Endpoints", self.test_google_drive_configuration_endpoints()))
        test_results.append(("MongoDB Data Verification", self.test_mongodb_data_verification()))
        test_results.append(("Endpoint Permissions", self.test_endpoint_permissions()))
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 MONGODB ENDPOINTS TEST RESULTS")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:40} {status}")
            if result:
                passed_tests += 1
        
        print(f"\nOverall API Tests: {self.tests_passed}/{self.tests_run}")
        print(f"Feature Tests: {passed_tests}/{total_tests}")
        
        # Summary of findings
        print("\n" + "=" * 60)
        print("🔍 SUMMARY OF FINDINGS")
        print("=" * 60)
        
        if passed_tests == total_tests and self.tests_passed == self.tests_run:
            print("🎉 All MongoDB endpoints are working correctly!")
            print("✅ Company Management endpoints functional")
            print("✅ Google Drive Configuration endpoints functional")
            print("✅ Data verification successful")
            print("✅ Admin permissions working correctly")
        else:
            print("⚠️ Issues found with MongoDB endpoints:")
            
            for test_name, result in test_results:
                if not result:
                    if "Company Management" in test_name:
                        print("❌ Company Management issues detected - may explain no content display")
                    elif "Google Drive" in test_name:
                        print("❌ Google Drive Configuration issues detected - may explain missing config")
                    elif "Data Verification" in test_name:
                        print("❌ Data integrity issues detected - may cause display problems")
                    elif "Permissions" in test_name:
                        print("❌ Permission issues detected - may block access to features")
        
        return passed_tests == total_tests and self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = MongoDBEndpointsTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
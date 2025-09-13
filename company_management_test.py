import requests
import sys
import json
from datetime import datetime, timezone
import time

class CompanyManagementTester:
    def __init__(self, base_url="https://ship-management.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_company_id = None

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
        """Test Super Admin authentication"""
        print(f"\n🔐 Testing Super Admin Authentication")
        success, response = self.run_test(
            "Super Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_role = response.get('user', {}).get('role')
            print(f"✅ Login successful - Role: {user_role}")
            if user_role != 'super_admin':
                print(f"❌ Expected super_admin role, got {user_role}")
                return False
            return True
        return False

    def test_get_initial_companies(self):
        """Test GET /api/companies - Check initial state"""
        print(f"\n📋 Testing Initial Companies List")
        success, companies = self.run_test(
            "Get Initial Companies",
            "GET",
            "companies",
            200
        )
        if success:
            print(f"   Initial companies count: {len(companies)}")
            return True
        return False

    def test_create_company(self):
        """Test POST /api/companies with comprehensive test data"""
        print(f"\n🏢 Testing Company Creation")
        
        company_data = {
            "name_vn": "Công ty TNHH Test",
            "name_en": "Test Company Ltd",
            "address_vn": "123 Đường Test, Quận 1, TP.HCM",
            "address_en": "123 Test Street, District 1, HCMC",
            "tax_id": "0123456789",
            "gmail": "test@company.com",
            "zalo": "0901234567",
            "system_expiry": "2025-12-31T23:59:59Z"
        }
        
        success, company = self.run_test(
            "Create Company",
            "POST",
            "companies",
            200,
            data=company_data
        )
        
        if success:
            self.created_company_id = company.get('id')
            print(f"   Created company ID: {self.created_company_id}")
            print(f"   Company name (VN): {company.get('name_vn')}")
            print(f"   Company name (EN): {company.get('name_en')}")
            print(f"   Tax ID: {company.get('tax_id')}")
            print(f"   Gmail: {company.get('gmail')}")
            print(f"   Zalo: {company.get('zalo')}")
            
            # Verify all fields are correctly saved
            expected_fields = ['name_vn', 'name_en', 'address_vn', 'address_en', 'tax_id', 'gmail', 'zalo']
            for field in expected_fields:
                if company.get(field) != company_data[field]:
                    print(f"❌ Field mismatch - {field}: expected {company_data[field]}, got {company.get(field)}")
                    return False
            
            return True
        return False

    def test_get_company_by_id(self):
        """Test GET /api/companies/{company_id} - Retrieve created company"""
        if not self.created_company_id:
            print("❌ No company ID available for retrieval test")
            return False
            
        print(f"\n🔍 Testing Company Retrieval by ID")
        success, company = self.run_test(
            "Get Company by ID",
            "GET",
            f"companies/{self.created_company_id}",
            200
        )
        
        if success:
            print(f"   Retrieved company: {company.get('name_en')}")
            print(f"   Tax ID: {company.get('tax_id')}")
            print(f"   System expiry: {company.get('system_expiry')}")
            return True
        return False

    def test_update_company(self):
        """Test PUT /api/companies/{company_id} - Update company with modified data"""
        if not self.created_company_id:
            print("❌ No company ID available for update test")
            return False
            
        print(f"\n✏️ Testing Company Update")
        
        updated_data = {
            "name_vn": "Công ty TNHH Test Updated",
            "name_en": "Test Company Ltd Updated",
            "address_vn": "456 Đường Test Updated, Quận 2, TP.HCM",
            "address_en": "456 Test Street Updated, District 2, HCMC",
            "tax_id": "0123456789",
            "gmail": "updated@company.com",
            "zalo": "0901234568",
            "system_expiry": "2026-12-31T23:59:59Z"
        }
        
        success, company = self.run_test(
            "Update Company",
            "PUT",
            f"companies/{self.created_company_id}",
            200,
            data=updated_data
        )
        
        if success:
            print(f"   Updated company name (EN): {company.get('name_en')}")
            print(f"   Updated Gmail: {company.get('gmail')}")
            print(f"   Updated Zalo: {company.get('zalo')}")
            print(f"   Updated system expiry: {company.get('system_expiry')}")
            
            # Verify updates were applied
            if company.get('name_en') != updated_data['name_en']:
                print(f"❌ Update failed - name_en not updated")
                return False
            if company.get('gmail') != updated_data['gmail']:
                print(f"❌ Update failed - gmail not updated")
                return False
                
            return True
        return False

    def test_delete_company(self):
        """Test DELETE /api/companies/{company_id} - Test company deletion"""
        if not self.created_company_id:
            print("❌ No company ID available for deletion test")
            return False
            
        print(f"\n🗑️ Testing Company Deletion")
        success, response = self.run_test(
            "Delete Company",
            "DELETE",
            f"companies/{self.created_company_id}",
            200
        )
        
        if success:
            print(f"   Company deleted successfully")
            print(f"   Response: {response.get('message', 'No message')}")
            return True
        return False

    def test_verify_company_deleted(self):
        """Test GET /api/companies - Verify company is deleted"""
        print(f"\n✅ Testing Company Deletion Verification")
        success, companies = self.run_test(
            "Verify Company Deleted",
            "GET",
            "companies",
            200
        )
        
        if success:
            # Check if the deleted company is no longer in the list
            for company in companies:
                if company.get('id') == self.created_company_id:
                    print(f"❌ Deleted company still found in list")
                    return False
            print(f"   ✅ Company successfully removed from list")
            print(f"   Current companies count: {len(companies)}")
            return True
        return False

    def test_edge_cases(self):
        """Test edge cases for Company Management"""
        print(f"\n⚠️ Testing Edge Cases")
        
        # Test 1: Create company with minimal required fields only
        print(f"\n   Testing minimal company creation...")
        minimal_data = {
            "name_vn": "Minimal Company VN",
            "name_en": "Minimal Company EN",
            "address_vn": "Minimal Address VN",
            "address_en": "Minimal Address EN",
            "tax_id": "1234567890"
        }
        
        success, minimal_company = self.run_test(
            "Create Minimal Company",
            "POST",
            "companies",
            200,
            data=minimal_data
        )
        
        minimal_company_id = None
        if success:
            minimal_company_id = minimal_company.get('id')
            print(f"   ✅ Minimal company created: {minimal_company_id}")
        
        # Test 2: Update non-existent company (should return 404)
        print(f"\n   Testing update non-existent company...")
        fake_id = "non-existent-company-id"
        success, response = self.run_test(
            "Update Non-existent Company",
            "PUT",
            f"companies/{fake_id}",
            404,
            data=minimal_data
        )
        
        if success:
            print(f"   ✅ Correctly returned 404 for non-existent company")
        
        # Test 3: Delete non-existent company (should return 404)
        print(f"\n   Testing delete non-existent company...")
        success, response = self.run_test(
            "Delete Non-existent Company",
            "DELETE",
            f"companies/{fake_id}",
            404
        )
        
        if success:
            print(f"   ✅ Correctly returned 404 for non-existent company deletion")
        
        # Clean up minimal company if created
        if minimal_company_id:
            print(f"\n   Cleaning up minimal company...")
            self.run_test(
                "Cleanup Minimal Company",
                "DELETE",
                f"companies/{minimal_company_id}",
                200
            )
        
        return True

def main():
    """Main test execution for Company Management"""
    print("🏢 Company Management API Testing")
    print("=" * 60)
    
    tester = CompanyManagementTester()
    
    # Test authentication first
    if not tester.test_authentication():
        print("❌ Super Admin authentication failed, stopping tests")
        return 1
    
    # Run Company Management tests in sequence
    test_results = []
    
    test_results.append(("Initial Companies Check", tester.test_get_initial_companies()))
    test_results.append(("Company Creation", tester.test_create_company()))
    test_results.append(("Company Retrieval", tester.test_get_company_by_id()))
    test_results.append(("Company Update", tester.test_update_company()))
    test_results.append(("Company Deletion", tester.test_delete_company()))
    test_results.append(("Deletion Verification", tester.test_verify_company_deleted()))
    test_results.append(("Edge Cases", tester.test_edge_cases()))
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 COMPANY MANAGEMENT TEST RESULTS")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:30} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Feature Tests: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests and tester.tests_passed == tester.tests_run:
        print("🎉 All Company Management tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
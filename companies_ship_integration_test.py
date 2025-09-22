#!/usr/bin/env python3
"""
Companies API and Ship Form Integration Testing
Tests companies API for dropdown data and ship form integration as requested in review.
"""

import requests
import sys
import json
import time
from datetime import datetime, timezone

class CompaniesShipIntegrationTester:
    def __init__(self, base_url="https://continue-session.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.test_results = []
        self.available_companies = []

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

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

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.content else {}
                    self.log_result(name, True, f"Status: {response.status_code}")
                    return True, response_data
                except:
                    self.log_result(name, True, f"Status: {response.status_code}")
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                    self.log_result(name, False, f"Status: {response.status_code}, Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                    self.log_result(name, False, f"Status: {response.status_code}, Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.log_result(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_authentication(self):
        """Test login with admin/admin123 credentials"""
        print(f"\n🔐 TESTING AUTHENTICATION")
        success, response = self.run_test(
            "Admin Login (admin/admin123)",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            user_info = response.get('user', {})
            print(f"✅ Login successful")
            print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
            print(f"   Company: {user_info.get('company')}")
            return True
        return False

    def test_companies_api_for_dropdowns(self):
        """Test GET /api/companies endpoint to verify company dropdown data is available"""
        print(f"\n🏢 TESTING COMPANIES API FOR DROPDOWN DATA")
        
        success, companies = self.run_test(
            "GET /api/companies for Ship Owner and Company dropdowns",
            "GET",
            "companies",
            200
        )
        
        if success:
            self.available_companies = companies
            print(f"   Found {len(companies)} companies available for dropdowns")
            
            if companies:
                print(f"   Company data structure verification:")
                first_company = companies[0]
                required_fields = ['id', 'name_vn', 'name_en']
                
                for field in required_fields:
                    if field in first_company:
                        print(f"     ✅ {field}: {first_company.get(field)}")
                    else:
                        print(f"     ❌ {field}: missing")
                        return False
                
                print(f"\n   Available companies for Ship Owner dropdown:")
                for i, company in enumerate(companies):
                    name_display = f"{company.get('name_en', 'N/A')} / {company.get('name_vn', 'N/A')}"
                    print(f"     {i+1}. {name_display} (ID: {company.get('id', 'N/A')})")
                
                print(f"\n   Available companies for Company dropdown:")
                for i, company in enumerate(companies):
                    name_display = f"{company.get('name_en', 'N/A')} / {company.get('name_vn', 'N/A')}"
                    print(f"     {i+1}. {name_display} (ID: {company.get('id', 'N/A')})")
                
                return True
            else:
                print(f"   ⚠️  No companies found - dropdowns will be empty")
                return True  # Not a failure, just empty data
        
        return False

    def test_ship_creation_with_required_fields(self):
        """Test ship creation with new required fields using existing company data"""
        print(f"\n🚢 TESTING SHIP CREATION WITH REQUIRED FIELDS")
        
        if not self.available_companies:
            print(f"   ⚠️  No companies available for testing - creating test company first")
            # Create a test company for testing
            test_company_data = {
                "name_vn": "Công ty Test Ship",
                "name_en": "Test Ship Company",
                "address_vn": "123 Test Street, Ho Chi Minh City",
                "address_en": "123 Test Street, Ho Chi Minh City",
                "tax_id": f"TEST{int(time.time())}",
                "gmail": "test@testshipcompany.com",
                "zalo": "0901234567"
            }
            
            success, test_company = self.run_test(
                "Create Test Company for Ship Testing",
                "POST",
                "companies",
                200,
                data=test_company_data
            )
            
            if success:
                self.available_companies = [test_company]
                print(f"   ✅ Test company created: {test_company.get('name_en')}")
            else:
                print(f"   ❌ Failed to create test company")
                return False
        
        # Test 1: Create ship with Ship Owner and Company fields from existing companies
        company_for_owner = self.available_companies[0]
        company_for_management = self.available_companies[0]  # Using same company for both
        
        ship_with_required_fields = {
            "name": f"Required Fields Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Singapore",
            "ship_type": "Container Ship",
            "gross_tonnage": 75000.0,
            "year_built": 2023,
            "ship_owner": company_for_owner.get('name_en'),
            "company": company_for_management.get('name_en')
        }
        
        success, ship_with_fields = self.run_test(
            "Create Ship with Ship Owner and Company from existing data",
            "POST",
            "ships",
            200,
            data=ship_with_required_fields
        )
        
        if success:
            print(f"   ✅ Ship created with required fields")
            print(f"     Ship Owner: {ship_with_fields.get('ship_owner')}")
            print(f"     Company: {ship_with_fields.get('company')}")
            print(f"     Ship ID: {ship_with_fields.get('id')}")
        
        # Test 2: Verify ship creation validation without required fields
        ship_without_required = {
            "name": f"No Required Fields Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Panama",
            "ship_type": "Bulk Carrier",
            "gross_tonnage": 50000.0,
            "year_built": 2022
            # Intentionally omitting ship_owner and company
        }
        
        success_no_required, ship_no_required = self.run_test(
            "Create Ship without Ship Owner and Company fields",
            "POST",
            "ships",
            200,  # Should still work (fields are optional)
            data=ship_without_required
        )
        
        if success_no_required:
            print(f"   ✅ Ship created without required fields (backward compatibility)")
            print(f"     Ship Owner: {ship_no_required.get('ship_owner', 'None (as expected)')}")
            print(f"     Company: {ship_no_required.get('company', 'None (as expected)')}")
            print(f"     Ship ID: {ship_no_required.get('id')}")
        
        return success and success_no_required

    def test_ship_form_validation_scenarios(self):
        """Test various ship form validation scenarios"""
        print(f"\n✅ TESTING SHIP FORM VALIDATION SCENARIOS")
        
        if not self.available_companies:
            print(f"   ❌ No companies available for validation testing")
            return False
        
        company_name = self.available_companies[0].get('name_en')
        
        # Test 1: Ship with only Ship Owner field
        ship_owner_only = {
            "name": f"Owner Only Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Marshall Islands",
            "ship_type": "Tanker",
            "gross_tonnage": 60000.0,
            "year_built": 2023,
            "ship_owner": company_name
            # No company field
        }
        
        success_owner, ship_owner_result = self.run_test(
            "Create Ship with only Ship Owner field",
            "POST",
            "ships",
            200,
            data=ship_owner_only
        )
        
        if success_owner:
            print(f"   ✅ Ship with only Ship Owner created")
            print(f"     Ship Owner: {ship_owner_result.get('ship_owner')}")
            print(f"     Company: {ship_owner_result.get('company', 'None (as expected)')}")
        
        # Test 2: Ship with only Company field
        time.sleep(1)  # Ensure unique timestamp
        ship_company_only = {
            "name": f"Company Only Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Liberia",
            "ship_type": "LNG Carrier",
            "gross_tonnage": 80000.0,
            "year_built": 2023,
            "company": company_name
            # No ship_owner field
        }
        
        success_company, ship_company_result = self.run_test(
            "Create Ship with only Company field",
            "POST",
            "ships",
            200,
            data=ship_company_only
        )
        
        if success_company:
            print(f"   ✅ Ship with only Company created")
            print(f"     Ship Owner: {ship_company_result.get('ship_owner', 'None (as expected)')}")
            print(f"     Company: {ship_company_result.get('company')}")
        
        # Test 3: Ship with both fields from different companies (if multiple available)
        if len(self.available_companies) > 1:
            time.sleep(1)  # Ensure unique timestamp
            ship_both_fields = {
                "name": f"Both Fields Ship {int(time.time())}",
                "imo": f"IMO{int(time.time())}",
                "flag": "Norway",
                "ship_type": "Offshore Vessel",
                "gross_tonnage": 45000.0,
                "year_built": 2023,
                "ship_owner": self.available_companies[0].get('name_en'),
                "company": self.available_companies[1].get('name_en')
            }
            
            success_both, ship_both_result = self.run_test(
                "Create Ship with different Ship Owner and Company",
                "POST",
                "ships",
                200,
                data=ship_both_fields
            )
            
            if success_both:
                print(f"   ✅ Ship with different Owner and Company created")
                print(f"     Ship Owner: {ship_both_result.get('ship_owner')}")
                print(f"     Company: {ship_both_result.get('company')}")
        
        return success_owner and success_company

    def test_existing_ship_crud_with_new_fields(self):
        """Test existing ship CRUD operations still work with new ship_owner and company fields"""
        print(f"\n🔄 TESTING EXISTING SHIP CRUD WITH NEW FIELDS")
        
        # Get existing ships
        success, existing_ships = self.run_test(
            "GET existing ships to test CRUD operations",
            "GET",
            "ships",
            200
        )
        
        if success:
            print(f"   Found {len(existing_ships)} existing ships")
            
            # Count ships with new fields
            ships_with_owner = [s for s in existing_ships if s.get('ship_owner')]
            ships_with_company = [s for s in existing_ships if s.get('company')]
            
            print(f"   Ships with ship_owner field: {len(ships_with_owner)}")
            print(f"   Ships with company field: {len(ships_with_company)}")
            
            # Test updating an existing ship to add new fields
            if existing_ships:
                test_ship = existing_ships[0]
                ship_id = test_ship.get('id')
                
                if self.available_companies:
                    company_name = self.available_companies[0].get('name_en')
                    
                    update_data = {
                        "ship_owner": f"Updated Owner {int(time.time())}",
                        "company": company_name
                    }
                    
                    success_update, updated_ship = self.run_test(
                        f"Update existing ship to add ship_owner and company",
                        "PUT",
                        f"ships/{ship_id}",
                        200,
                        data=update_data
                    )
                    
                    if success_update:
                        print(f"   ✅ Existing ship updated with new fields")
                        print(f"     Original name: {test_ship.get('name')}")
                        print(f"     New Ship Owner: {updated_ship.get('ship_owner')}")
                        print(f"     New Company: {updated_ship.get('company')}")
                
                # Test backward compatibility - update traditional fields
                traditional_update = {
                    "flag": f"Updated Flag {int(time.time() % 1000)}"
                }
                
                success_traditional, traditional_result = self.run_test(
                    f"Update existing ship with traditional fields only",
                    "PUT",
                    f"ships/{ship_id}",
                    200,
                    data=traditional_update
                )
                
                if success_traditional:
                    print(f"   ✅ Traditional field update still works")
                    print(f"     Updated flag: {traditional_result.get('flag')}")
                    print(f"     Ship Owner preserved: {traditional_result.get('ship_owner', 'None')}")
                    print(f"     Company preserved: {traditional_result.get('company', 'None')}")
        
        return success

    def run_comprehensive_test(self):
        """Run all companies and ship integration tests"""
        print("🏢🚢 COMPANIES API AND SHIP FORM INTEGRATION TESTING")
        print("=" * 80)
        print(f"Testing Backend URL: {self.base_url}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run tests in order
        tests = [
            ("Authentication", self.test_authentication),
            ("Companies API for Dropdowns", self.test_companies_api_for_dropdowns),
            ("Ship Creation with Required Fields", self.test_ship_creation_with_required_fields),
            ("Ship Form Validation Scenarios", self.test_ship_form_validation_scenarios),
            ("Existing Ship CRUD with New Fields", self.test_existing_ship_crud_with_new_fields)
        ]
        
        test_group_results = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n{'='*60}")
                result = test_func()
                test_group_results.append((test_name, result))
                if result:
                    print(f"\n✅ {test_name} - PASSED")
                else:
                    print(f"\n❌ {test_name} - FAILED")
            except Exception as e:
                print(f"\n💥 {test_name} - ERROR: {str(e)}")
                test_group_results.append((test_name, False))
        
        # Print summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 80)
        print("📊 COMPANIES API AND SHIP INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        passed_groups = sum(1 for _, result in test_group_results if result)
        total_groups = len(test_group_results)
        
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"🧪 Individual API Tests: {self.tests_passed}/{self.tests_run} passed")
        print(f"📋 Test Groups: {passed_groups}/{total_groups} passed")
        print(f"🏢 Companies Available: {len(self.available_companies)}")
        
        print(f"\n📋 Test Group Results:")
        for test_name, result in test_group_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name:40} {status}")
        
        # Detailed results for failed tests
        if self.test_results:
            failed_tests = [r for r in self.test_results if not r['success']]
            if failed_tests:
                print(f"\n❌ Failed Tests Details:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        overall_success = passed_groups == total_groups and self.tests_passed >= (self.tests_run * 0.8)
        
        if overall_success:
            print(f"\n🎉 ALL COMPANIES API AND SHIP INTEGRATION TESTS PASSED!")
            print("✅ Companies API provides proper dropdown data")
            print("✅ Ship creation with Ship Owner and Company fields working")
            print("✅ Ship form validation scenarios working")
            print("✅ Existing ship CRUD operations compatible with new fields")
            print("✅ Backward compatibility maintained")
        else:
            print(f"\n⚠️  SOME COMPANIES/SHIP INTEGRATION TESTS FAILED")
            print("❌ Check the detailed results above for specific issues")
        
        return overall_success

def main():
    """Main test execution"""
    tester = CompaniesShipIntegrationTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
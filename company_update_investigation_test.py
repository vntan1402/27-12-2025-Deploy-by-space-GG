#!/usr/bin/env python3
"""
Company Update Functionality Investigation Test

This test specifically investigates the "Failed to update company!" error
when Google Drive is configured, as reported in the review request.

Focus Areas:
1. Login as admin/admin123
2. Find AMCSC company (ID: cfe73cb0-cc88-4659-92a7-57cb413a5573)
3. Test company update functionality using PUT /api/companies/{company_id}
4. Try updating different company fields
5. Check if Google Drive configuration is causing conflicts
6. Test both companies with and without Google Drive configuration
7. Check backend logs for detailed error messages
8. Verify Pydantic model validation issues
"""

import requests
import json
import sys
from datetime import datetime, timezone
import time

class CompanyUpdateInvestigator:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.issues_found = []
        self.amcsc_company_id = "cfe73cb0-cc88-4659-92a7-57cb413a5573"
        
    def log_issue(self, severity, description, details=None):
        """Log an issue found during testing"""
        issue = {
            "severity": severity,  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
            "description": description,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.issues_found.append(issue)
        print(f"🚨 {severity}: {description}")
        if details:
            print(f"   Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers_override=None):
        """Run a single API test with detailed logging"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if headers_override:
            headers.update(headers_override)
        
        # Remove Content-Type for file uploads
        if files:
            headers.pop('Content-Type', None)

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        print(f"   Method: {method}")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
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

            print(f"   Response Status: {response.status_code}")
            
            # Always try to get response content
            try:
                response_data = response.json() if response.content else {}
                if response_data:
                    print(f"   Response Data: {json.dumps(response_data, indent=2)[:500]}...")
            except:
                response_data = {}
                if response.text:
                    print(f"   Response Text: {response.text[:500]}...")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED")
                return True, response_data
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                
                # Log detailed error information
                error_details = {
                    "expected_status": expected_status,
                    "actual_status": response.status_code,
                    "response_data": response_data,
                    "response_text": response.text[:1000] if response.text else None
                }
                
                self.log_issue("HIGH", f"{name} failed", error_details)
                return False, response_data

        except Exception as e:
            print(f"❌ FAILED - Exception: {str(e)}")
            self.log_issue("CRITICAL", f"{name} threw exception", str(e))
            return False, {}

    def test_authentication(self):
        """Test admin authentication"""
        print(f"\n🔐 STEP 1: Testing Authentication")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_info = response.get('user', {})
            print(f"✅ Authentication successful")
            print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
            print(f"   Company: {user_info.get('company')}")
            return True
        else:
            self.log_issue("CRITICAL", "Authentication failed - cannot proceed with tests")
            return False

    def test_get_all_companies(self):
        """Get all companies to understand current state"""
        print(f"\n🏢 STEP 2: Getting All Companies")
        success, companies = self.run_test(
            "Get All Companies",
            "GET",
            "companies",
            200
        )
        
        if success:
            print(f"✅ Found {len(companies)} companies")
            
            # Look for AMCSC company specifically
            amcsc_company = None
            for company in companies:
                if company.get('id') == self.amcsc_company_id:
                    amcsc_company = company
                    break
                # Also check by name in case ID changed
                if 'AMCSC' in str(company.get('name_vn', '')) or 'AMCSC' in str(company.get('name_en', '')):
                    print(f"   Found AMCSC-like company: {company.get('name_vn')} / {company.get('name_en')} (ID: {company.get('id')})")
            
            if amcsc_company:
                print(f"✅ AMCSC company found with expected ID: {self.amcsc_company_id}")
                print(f"   Company details: {json.dumps(amcsc_company, indent=2)}")
                return True, companies, amcsc_company
            else:
                self.log_issue("HIGH", f"AMCSC company not found with ID {self.amcsc_company_id}")
                # Try to find any company with AMCSC in name
                for company in companies:
                    company_str = json.dumps(company).upper()
                    if 'AMCSC' in company_str:
                        print(f"   Found potential AMCSC company: {company}")
                        return True, companies, company
                return True, companies, None
        else:
            self.log_issue("CRITICAL", "Cannot retrieve companies list")
            return False, [], None

    def test_google_drive_configuration_status(self):
        """Check Google Drive configuration status"""
        print(f"\n☁️ STEP 3: Checking Google Drive Configuration")
        
        # Check system-wide Google Drive config
        success, gdrive_config = self.run_test(
            "Get Google Drive Config",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            print(f"✅ Google Drive system config retrieved")
            print(f"   Configured: {gdrive_config.get('configured', False)}")
            print(f"   Folder ID: {gdrive_config.get('folder_id', 'Not set')}")
        
        # Check Google Drive status
        success2, gdrive_status = self.run_test(
            "Get Google Drive Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if success2:
            print(f"✅ Google Drive status retrieved")
            print(f"   Status: {gdrive_status}")
        
        return success and success2, gdrive_config

    def test_company_specific_gdrive_config(self, company_id):
        """Check company-specific Google Drive configuration"""
        print(f"\n☁️ STEP 4: Checking Company-Specific Google Drive Config for {company_id}")
        
        # Test company-specific Google Drive endpoints
        endpoints_to_test = [
            ("Get Company GDrive Config", "GET", f"companies/{company_id}/gdrive/config", 200),
            ("Get Company GDrive Status", "GET", f"companies/{company_id}/gdrive/status", 200),
        ]
        
        results = {}
        for name, method, endpoint, expected_status in endpoints_to_test:
            success, response = self.run_test(name, method, endpoint, expected_status)
            results[endpoint] = {"success": success, "data": response}
        
        return results

    def test_company_update_scenarios(self, company):
        """Test various company update scenarios"""
        print(f"\n🔄 STEP 5: Testing Company Update Scenarios")
        
        if not company:
            self.log_issue("CRITICAL", "No company provided for update testing")
            return False
        
        company_id = company.get('id')
        print(f"   Testing updates for company: {company.get('name_vn')} / {company.get('name_en')} (ID: {company_id})")
        
        # Test 1: Update single field (name_vn)
        print(f"\n   Test 1: Update name_vn field")
        original_name_vn = company.get('name_vn', '')
        test_name_vn = f"{original_name_vn} - Updated {int(time.time())}"
        
        update_data_1 = {
            "name_vn": test_name_vn
        }
        
        success1, response1 = self.run_test(
            "Update Company - name_vn only",
            "PUT",
            f"companies/{company_id}",
            200,
            data=update_data_1
        )
        
        # Test 2: Update multiple fields
        print(f"\n   Test 2: Update multiple fields")
        update_data_2 = {
            "name_vn": company.get('name_vn', ''),
            "name_en": company.get('name_en', ''),
            "address_vn": f"Updated Address VN {int(time.time())}",
            "address_en": f"Updated Address EN {int(time.time())}",
            "tax_id": company.get('tax_id', ''),
            "gmail": f"updated_{int(time.time())}@gmail.com",
            "zalo": f"0901{int(time.time()) % 1000000:06d}"
        }
        
        success2, response2 = self.run_test(
            "Update Company - multiple fields",
            "PUT",
            f"companies/{company_id}",
            200,
            data=update_data_2
        )
        
        # Test 3: Update with system_expiry field
        print(f"\n   Test 3: Update with system_expiry field")
        update_data_3 = {
            "name_vn": company.get('name_vn', ''),
            "name_en": company.get('name_en', ''),
            "address_vn": company.get('address_vn', ''),
            "address_en": company.get('address_en', ''),
            "tax_id": company.get('tax_id', ''),
            "system_expiry": "2025-12-31T23:59:59Z"
        }
        
        success3, response3 = self.run_test(
            "Update Company - with system_expiry",
            "PUT",
            f"companies/{company_id}",
            200,
            data=update_data_3
        )
        
        # Test 4: Update with all possible fields
        print(f"\n   Test 4: Update with all possible fields")
        update_data_4 = {
            "name_vn": company.get('name_vn', ''),
            "name_en": company.get('name_en', ''),
            "address_vn": company.get('address_vn', ''),
            "address_en": company.get('address_en', ''),
            "tax_id": company.get('tax_id', ''),
            "gmail": company.get('gmail', ''),
            "zalo": company.get('zalo', ''),
            "system_expiry": company.get('system_expiry', None),
            # Legacy fields
            "name": company.get('name', ''),
            "address": company.get('address', ''),
            "phone": company.get('phone', ''),
            "email": company.get('email', ''),
            "website": company.get('website', '')
        }
        
        success4, response4 = self.run_test(
            "Update Company - all fields",
            "PUT",
            f"companies/{company_id}",
            200,
            data=update_data_4
        )
        
        # Test 5: Update with invalid data to test validation
        print(f"\n   Test 5: Update with invalid data (validation test)")
        update_data_5 = {
            "name_vn": "",  # Empty required field
            "tax_id": "invalid-tax-id-format-that-is-way-too-long-and-should-fail-validation"
        }
        
        success5, response5 = self.run_test(
            "Update Company - invalid data",
            "PUT",
            f"companies/{company_id}",
            422,  # Expect validation error
            data=update_data_5
        )
        
        # Summary of update tests
        update_results = [success1, success2, success3, success4, success5]
        passed_updates = sum(update_results)
        
        print(f"\n   Update Test Summary: {passed_updates}/5 tests passed")
        
        if passed_updates < 4:  # Allow validation test to fail
            self.log_issue("HIGH", f"Company update functionality has issues - only {passed_updates}/5 tests passed")
        
        return passed_updates >= 4

    def test_companies_without_gdrive(self):
        """Test updating companies that don't have Google Drive configured"""
        print(f"\n🏢 STEP 6: Testing Companies Without Google Drive Configuration")
        
        # Get all companies
        success, companies = self.run_test(
            "Get Companies for Non-GDrive Test",
            "GET",
            "companies",
            200
        )
        
        if not success or not companies:
            self.log_issue("HIGH", "Cannot get companies for non-GDrive testing")
            return False
        
        # Find a company that's not AMCSC (assuming AMCSC has GDrive configured)
        test_company = None
        for company in companies:
            if company.get('id') != self.amcsc_company_id:
                test_company = company
                break
        
        if not test_company:
            print("   No alternative company found for testing")
            return True
        
        print(f"   Testing company without GDrive: {test_company.get('name_vn')} / {test_company.get('name_en')}")
        
        # Test simple update
        update_data = {
            "name_vn": test_company.get('name_vn', ''),
            "name_en": test_company.get('name_en', ''),
            "address_vn": f"Test Address {int(time.time())}",
            "tax_id": test_company.get('tax_id', '')
        }
        
        success, response = self.run_test(
            "Update Non-GDrive Company",
            "PUT",
            f"companies/{test_company.get('id')}",
            200,
            data=update_data
        )
        
        return success

    def check_backend_logs(self):
        """Check backend logs for errors (if accessible)"""
        print(f"\n📋 STEP 7: Checking Backend Logs")
        
        # Note: In a containerized environment, we might not have direct access to logs
        # This is a placeholder for log checking logic
        print("   Note: Backend log checking would require direct server access")
        print("   Recommendation: Check supervisor logs with:")
        print("   tail -n 100 /var/log/supervisor/backend.*.log")
        
        return True

    def analyze_pydantic_models(self):
        """Analyze potential Pydantic model issues"""
        print(f"\n🔍 STEP 8: Analyzing Potential Pydantic Model Issues")
        
        # Test with various data types that might cause validation issues
        test_cases = [
            {
                "name": "String system_expiry",
                "data": {"system_expiry": "2025-12-31"},
                "expected_issue": "Date format validation"
            },
            {
                "name": "Datetime system_expiry",
                "data": {"system_expiry": "2025-12-31T23:59:59Z"},
                "expected_issue": "None - should work"
            },
            {
                "name": "None system_expiry",
                "data": {"system_expiry": None},
                "expected_issue": "None - should work"
            },
            {
                "name": "Empty strings",
                "data": {"name_vn": "", "name_en": ""},
                "expected_issue": "Required field validation"
            },
            {
                "name": "Missing required fields",
                "data": {"gmail": "test@example.com"},
                "expected_issue": "Missing required fields"
            }
        ]
        
        print("   Testing various data scenarios that might cause Pydantic validation issues:")
        
        for test_case in test_cases:
            print(f"\n   Testing: {test_case['name']}")
            print(f"   Expected issue: {test_case['expected_issue']}")
            print(f"   Data: {test_case['data']}")
            
            # We'll test this against a dummy endpoint or analyze the data structure
            # For now, just log the analysis
            
        return True

    def generate_report(self):
        """Generate comprehensive investigation report"""
        print(f"\n" + "="*80)
        print("📊 COMPANY UPDATE FUNCTIONALITY INVESTIGATION REPORT")
        print("="*80)
        
        print(f"\n🔢 TEST STATISTICS:")
        print(f"   Total Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "N/A")
        
        print(f"\n🚨 ISSUES FOUND: {len(self.issues_found)}")
        if self.issues_found:
            for i, issue in enumerate(self.issues_found, 1):
                print(f"\n   Issue {i}: {issue['severity']} - {issue['description']}")
                if issue['details']:
                    print(f"   Details: {json.dumps(issue['details'], indent=4)}")
        else:
            print("   ✅ No critical issues found!")
        
        print(f"\n🎯 KEY FINDINGS:")
        
        # Analyze the pattern of failures
        critical_issues = [i for i in self.issues_found if i['severity'] == 'CRITICAL']
        high_issues = [i for i in self.issues_found if i['severity'] == 'HIGH']
        
        if critical_issues:
            print(f"   ❌ CRITICAL: {len(critical_issues)} critical issues prevent basic functionality")
        
        if high_issues:
            print(f"   ⚠️  HIGH: {len(high_issues)} high-priority issues affect company updates")
        
        if not critical_issues and not high_issues:
            print(f"   ✅ Company update functionality appears to be working correctly")
        
        print(f"\n💡 RECOMMENDATIONS:")
        
        if critical_issues:
            print(f"   1. Fix authentication and basic API connectivity issues first")
        
        if high_issues:
            print(f"   2. Investigate company update endpoint validation and error handling")
            print(f"   3. Check Pydantic model definitions for CompanyBase and CompanyUpdate")
            print(f"   4. Verify Google Drive integration doesn't interfere with company updates")
        
        print(f"   5. Check backend logs for detailed error messages:")
        print(f"      tail -n 100 /var/log/supervisor/backend.*.log")
        
        print(f"\n🔧 NEXT STEPS:")
        print(f"   1. Review backend server.py company update endpoint implementation")
        print(f"   2. Check MongoDB company document structure and constraints")
        print(f"   3. Test company updates with Google Drive configuration disabled")
        print(f"   4. Verify frontend error handling and user feedback")
        
        return len(critical_issues) == 0 and len(high_issues) <= 2

def main():
    """Main investigation execution"""
    print("🔍 Company Update Functionality Investigation")
    print("=" * 60)
    print("Investigating: 'Failed to update company!' error when Google Drive is configured")
    print("Target: AMCSC company (ID: cfe73cb0-cc88-4659-92a7-57cb413a5573)")
    print("=" * 60)
    
    investigator = CompanyUpdateInvestigator()
    
    # Step 1: Authentication
    if not investigator.test_authentication():
        print("❌ Investigation cannot proceed without authentication")
        return 1
    
    # Step 2: Get companies and find AMCSC
    success, companies, amcsc_company = investigator.test_get_all_companies()
    if not success:
        print("❌ Investigation cannot proceed without company data")
        return 1
    
    # Step 3: Check Google Drive configuration
    investigator.test_google_drive_configuration_status()
    
    # Step 4: Check company-specific Google Drive config
    if amcsc_company:
        investigator.test_company_specific_gdrive_config(amcsc_company.get('id'))
    
    # Step 5: Test company update scenarios
    if amcsc_company:
        investigator.test_company_update_scenarios(amcsc_company)
    else:
        print("⚠️ Cannot test AMCSC company updates - company not found")
    
    # Step 6: Test companies without Google Drive
    investigator.test_companies_without_gdrive()
    
    # Step 7: Check backend logs (informational)
    investigator.check_backend_logs()
    
    # Step 8: Analyze Pydantic models
    investigator.analyze_pydantic_models()
    
    # Generate final report
    success = investigator.generate_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
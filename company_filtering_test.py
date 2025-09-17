import requests
import sys
import json
from datetime import datetime, timezone
import time

class CompanyFilteringTester:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.current_user = None

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

    def test_login(self, username, password):
        """Test login and get token"""
        print(f"\n🔐 Testing Authentication with {username}/{password}")
        success, response = self.run_test(
            f"Login as {username}",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.current_user = response.get('user', {})
            print(f"✅ Login successful, token obtained")
            print(f"   User: {self.current_user.get('full_name')} ({self.current_user.get('role')})")
            print(f"   Company: {self.current_user.get('company')}")
            print(f"   Department: {self.current_user.get('department')}")
            return True
        return False

    def analyze_user_data(self, username):
        """Analyze current user data"""
        print(f"\n📊 ANALYZING USER DATA FOR {username.upper()}")
        print("=" * 60)
        print(f"User ID: {self.current_user.get('id')}")
        print(f"Username: {self.current_user.get('username')}")
        print(f"Full Name: {self.current_user.get('full_name')}")
        print(f"Email: {self.current_user.get('email')}")
        print(f"Role: {self.current_user.get('role')}")
        print(f"Department: {self.current_user.get('department')}")
        print(f"Company: '{self.current_user.get('company')}'")
        print(f"Ship: {self.current_user.get('ship')}")
        print(f"Active: {self.current_user.get('is_active')}")
        print("=" * 60)

    def get_all_companies_data(self):
        """Get all companies data for analysis"""
        print(f"\n🏢 GETTING ALL COMPANIES DATA")
        print("=" * 60)
        
        success, companies = self.run_test(
            "Get Companies",
            "GET",
            "companies",
            200
        )
        
        if success:
            print(f"✅ Retrieved {len(companies)} companies")
            print("\nCOMPANIES DATABASE ANALYSIS:")
            print("-" * 40)
            for i, company in enumerate(companies, 1):
                print(f"{i}. Company ID: {company.get('id')}")
                print(f"   Name VN: '{company.get('name_vn')}'")
                print(f"   Name EN: '{company.get('name_en')}'")
                print(f"   Tax ID: {company.get('tax_id')}")
                print(f"   Gmail: {company.get('gmail')}")
                print(f"   Zalo: {company.get('zalo')}")
                print(f"   Created By: {company.get('created_by')}")
                print(f"   Logo URL: {company.get('logo_url')}")
                print("-" * 40)
            
            return companies
        else:
            print("❌ Failed to retrieve companies")
            return []

    def analyze_company_matching(self, companies):
        """Analyze company matching logic"""
        print(f"\n🔍 COMPANY MATCHING ANALYSIS")
        print("=" * 60)
        
        user_company = self.current_user.get('company')
        user_role = self.current_user.get('role')
        
        print(f"Current User Company: '{user_company}'")
        print(f"Current User Role: '{user_role}'")
        print()
        
        matching_companies = []
        
        print("MATCHING LOGIC ANALYSIS:")
        print("-" * 30)
        
        for company in companies:
            name_vn = company.get('name_vn', '')
            name_en = company.get('name_en', '')
            
            vn_match = name_vn == user_company
            en_match = name_en == user_company
            
            print(f"Company: {name_vn} / {name_en}")
            print(f"  VN Match ('{name_vn}' == '{user_company}'): {vn_match}")
            print(f"  EN Match ('{name_en}' == '{user_company}'): {en_match}")
            print(f"  Overall Match: {vn_match or en_match}")
            
            if vn_match or en_match:
                matching_companies.append(company)
            print()
        
        print(f"EXPECTED COMPANIES FOR {user_role}: {len(matching_companies)}")
        if matching_companies:
            for company in matching_companies:
                print(f"  - {company.get('name_vn')} / {company.get('name_en')}")
        else:
            print("  - NO MATCHING COMPANIES FOUND!")
            print("  - This explains why admin1 sees 0 companies")
        
        return matching_companies

    def test_company_filtering_scenario(self, username, password, expected_behavior):
        """Test complete company filtering scenario"""
        print(f"\n{'='*80}")
        print(f"TESTING COMPANY FILTERING FOR {username.upper()}")
        print(f"Expected Behavior: {expected_behavior}")
        print(f"{'='*80}")
        
        # Step 1: Login
        if not self.test_login(username, password):
            print(f"❌ Login failed for {username}")
            return False
        
        # Step 2: Analyze user data
        self.analyze_user_data(username)
        
        # Step 3: Get companies and analyze
        companies = self.get_all_companies_data()
        if not companies:
            return False
        
        # Step 4: Analyze matching logic
        expected_companies = self.analyze_company_matching(companies)
        
        # Step 5: Verify results
        print(f"\n📋 VERIFICATION RESULTS")
        print("=" * 40)
        print(f"User: {username}")
        print(f"Role: {self.current_user.get('role')}")
        print(f"Company: '{self.current_user.get('company')}'")
        print(f"Companies Retrieved: {len(companies)}")
        print(f"Expected Companies: {len(expected_companies)}")
        
        if self.current_user.get('role') == 'admin':
            if len(expected_companies) == 0:
                print("🔍 ROOT CAUSE IDENTIFIED:")
                print("   Admin user's company field does not match any company's name_vn or name_en")
                print("   This is why admin1 sees 0 companies instead of their company's data")
                print("\n💡 DEBUGGING RECOMMENDATIONS:")
                print("   1. Check exact string matching (case sensitivity, spaces, special characters)")
                print("   2. Verify admin1's company field value")
                print("   3. Verify company database name_vn and name_en values")
                print("   4. Consider if company names were updated after user creation")
        
        return True

def main():
    """Main test execution for company filtering analysis"""
    print("🏢 COMPANY FILTERING DETAILED ANALYSIS")
    print("=" * 80)
    
    tester = CompanyFilteringTester()
    
    # Test Scenario 1: admin1 (Admin role, XYZ Company)
    print("\n" + "🔍 SCENARIO 1: ADMIN USER COMPANY FILTERING")
    success1 = tester.test_company_filtering_scenario(
        "admin1", 
        "123456", 
        "Should see only companies where name_vn='XYZ Company' OR name_en='XYZ Company'"
    )
    
    # Reset for next test
    tester.token = None
    tester.current_user = None
    
    # Test Scenario 2: superadmin1 (Super Admin role)
    print("\n" + "🔍 SCENARIO 2: SUPER ADMIN USER COMPANY FILTERING")
    success2 = tester.test_company_filtering_scenario(
        "superadmin1", 
        "123456", 
        "Should see all companies (5 companies total)"
    )
    
    # Final Summary
    print("\n" + "=" * 80)
    print("📊 COMPANY FILTERING ANALYSIS SUMMARY")
    print("=" * 80)
    
    print(f"Admin1 Test: {'✅ COMPLETED' if success1 else '❌ FAILED'}")
    print(f"SuperAdmin1 Test: {'✅ COMPLETED' if success2 else '❌ FAILED'}")
    print(f"Total API Tests: {tester.tests_passed}/{tester.tests_run}")
    
    if success1 and success2:
        print("\n🎉 Company filtering analysis completed successfully!")
        print("📋 Check the detailed analysis above for root cause identification")
        return 0
    else:
        print("\n⚠️ Some tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
import requests
import sys
import json
from datetime import datetime, timezone
import time

class AdminCompanyDebugTester:
    def __init__(self, base_url="https://shipgooglesync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin1_token = None
        self.superadmin1_token = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

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

    def login_user(self, username, password, user_type="user"):
        """Login and get token for specific user"""
        print(f"\n🔐 Testing Authentication with {username}/{password}")
        success, response = self.run_test(
            f"{user_type} Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            token = response['access_token']
            user_data = response.get('user', {})
            print(f"✅ Login successful for {username}")
            print(f"   User: {user_data.get('full_name')} ({user_data.get('role')})")
            print(f"   Company: {user_data.get('company')}")
            print(f"   Department: {user_data.get('department')}")
            return token, user_data
        return None, None

    def debug_admin1_company_visibility(self):
        """Debug admin1 company visibility issue"""
        print(f"\n🔍 DEBUGGING ADMIN1 COMPANY VISIBILITY ISSUE")
        print("=" * 60)
        
        # Step 1: Login as admin1 and get user data
        print(f"\n📋 STEP 1: Check admin1 User Data")
        self.admin1_token, admin1_data = self.login_user("admin1", "123456", "admin1")
        if not self.admin1_token:
            print("❌ Failed to login as admin1")
            return False
        
        print(f"\n📊 ADMIN1 USER DATA ANALYSIS:")
        print(f"   ID: {admin1_data.get('id')}")
        print(f"   Username: {admin1_data.get('username')}")
        print(f"   Full Name: {admin1_data.get('full_name')}")
        print(f"   Role: {admin1_data.get('role')}")
        print(f"   Company: '{admin1_data.get('company')}'")
        print(f"   Department: {admin1_data.get('department')}")
        print(f"   Email: {admin1_data.get('email')}")
        
        admin1_company = admin1_data.get('company')
        print(f"\n🎯 ADMIN1 COMPANY FIELD VALUE: '{admin1_company}'")
        print(f"   Type: {type(admin1_company)}")
        print(f"   Length: {len(admin1_company) if admin1_company else 'None'}")
        print(f"   Stripped: '{admin1_company.strip() if admin1_company else 'None'}'")
        
        # Step 2: Login as superadmin1 and get all companies
        print(f"\n📋 STEP 2: Check Company Database (as superadmin1)")
        self.superadmin1_token, superadmin1_data = self.login_user("superadmin1", "123456", "superadmin1")
        if not self.superadmin1_token:
            print("❌ Failed to login as superadmin1")
            return False
        
        # Get all companies as superadmin1
        success, all_companies = self.run_test(
            "Get All Companies (superadmin1)",
            "GET",
            "companies",
            200,
            token=self.superadmin1_token
        )
        
        if not success:
            print("❌ Failed to get companies as superadmin1")
            return False
        
        print(f"\n📊 COMPANY DATABASE ANALYSIS:")
        print(f"   Total Companies Found: {len(all_companies)}")
        
        for i, company in enumerate(all_companies, 1):
            print(f"\n   Company {i}:")
            print(f"     ID: {company.get('id')}")
            print(f"     Name VN: '{company.get('name_vn')}'")
            print(f"     Name EN: '{company.get('name_en')}'")
            print(f"     Tax ID: {company.get('tax_id')}")
            print(f"     Gmail: {company.get('gmail')}")
            print(f"     Zalo: {company.get('zalo')}")
            print(f"     Created By: {company.get('created_by')}")
            
            # Check if this company matches admin1's company
            name_vn_match = company.get('name_vn') == admin1_company
            name_en_match = company.get('name_en') == admin1_company
            
            print(f"     MATCH ANALYSIS:")
            print(f"       name_vn == admin1.company: {name_vn_match}")
            print(f"       name_en == admin1.company: {name_en_match}")
            
            if name_vn_match or name_en_match:
                print(f"     🎯 POTENTIAL MATCH FOUND!")
        
        # Step 3: Test company filtering as admin1
        print(f"\n📋 STEP 3: Test Company Filtering Logic (as admin1)")
        success, admin1_companies = self.run_test(
            "Get Companies (admin1)",
            "GET",
            "companies",
            200,
            token=self.admin1_token
        )
        
        if not success:
            print("❌ Failed to get companies as admin1")
            return False
        
        print(f"\n📊 ADMIN1 COMPANY FILTERING RESULTS:")
        print(f"   Companies Visible to admin1: {len(admin1_companies)}")
        
        if len(admin1_companies) == 0:
            print("   🚨 ISSUE CONFIRMED: admin1 sees 0 companies!")
        else:
            for i, company in enumerate(admin1_companies, 1):
                print(f"\n   Visible Company {i}:")
                print(f"     ID: {company.get('id')}")
                print(f"     Name VN: '{company.get('name_vn')}'")
                print(f"     Name EN: '{company.get('name_en')}'")
        
        # Step 4: String Matching Analysis
        print(f"\n📋 STEP 4: String Matching Analysis")
        print(f"\n🔍 DETAILED STRING COMPARISON:")
        print(f"   admin1.company: '{admin1_company}'")
        
        matching_companies = []
        for company in all_companies:
            name_vn = company.get('name_vn', '')
            name_en = company.get('name_en', '')
            
            print(f"\n   Comparing with Company ID {company.get('id')}:")
            print(f"     name_vn: '{name_vn}'")
            print(f"     name_en: '{name_en}'")
            
            # Exact match
            vn_exact = name_vn == admin1_company
            en_exact = name_en == admin1_company
            
            # Case insensitive match
            vn_case_insensitive = name_vn.lower() == admin1_company.lower() if admin1_company else False
            en_case_insensitive = name_en.lower() == admin1_company.lower() if admin1_company else False
            
            # Stripped match
            vn_stripped = name_vn.strip() == admin1_company.strip() if admin1_company else False
            en_stripped = name_en.strip() == admin1_company.strip() if admin1_company else False
            
            print(f"     Exact Match (VN): {vn_exact}")
            print(f"     Exact Match (EN): {en_exact}")
            print(f"     Case Insensitive (VN): {vn_case_insensitive}")
            print(f"     Case Insensitive (EN): {en_case_insensitive}")
            print(f"     Stripped Match (VN): {vn_stripped}")
            print(f"     Stripped Match (EN): {en_stripped}")
            
            if vn_exact or en_exact:
                matching_companies.append(company)
                print(f"     ✅ EXACT MATCH FOUND!")
            elif vn_case_insensitive or en_case_insensitive:
                print(f"     ⚠️ CASE SENSITIVITY ISSUE!")
            elif vn_stripped or en_stripped:
                print(f"     ⚠️ WHITESPACE ISSUE!")
        
        # Step 5: Root Cause Analysis
        print(f"\n📋 STEP 5: Root Cause Analysis")
        print(f"\n🔍 DIAGNOSIS:")
        
        if not admin1_company:
            print("   🚨 ISSUE: admin1.company field is None or empty!")
            print("   🔧 SOLUTION: admin1 needs to be assigned to a company")
        elif len(matching_companies) == 0:
            print("   🚨 ISSUE: No companies in database match admin1.company field!")
            print(f"   🔧 SOLUTION: Either create a company with name '{admin1_company}' or update admin1.company field")
        elif len(admin1_companies) == 0 and len(matching_companies) > 0:
            print("   🚨 ISSUE: Companies exist that should match, but filtering logic is not working!")
            print("   🔧 SOLUTION: Check backend filtering logic in /api/companies endpoint")
        else:
            print("   ✅ No issues found - admin1 should be able to see their company")
        
        # Step 6: Provide Exact Fix
        print(f"\n📋 STEP 6: Exact Solution Required")
        
        if len(matching_companies) > 0:
            print(f"\n✅ MATCHING COMPANIES FOUND:")
            for company in matching_companies:
                print(f"   Company: {company.get('name_vn')} / {company.get('name_en')}")
                print(f"   ID: {company.get('id')}")
        
        if len(admin1_companies) == 0:
            print(f"\n🔧 RECOMMENDED ACTIONS:")
            if not admin1_company:
                print("   1. Update admin1 user to assign them to an existing company")
                print("   2. Use one of these existing company names:")
                for company in all_companies[:3]:
                    print(f"      - '{company.get('name_en')}' or '{company.get('name_vn')}'")
            elif len(matching_companies) == 0:
                print(f"   1. Create a new company with name '{admin1_company}'")
                print(f"   2. OR update admin1.company to match an existing company:")
                for company in all_companies[:3]:
                    print(f"      - '{company.get('name_en')}' or '{company.get('name_vn')}'")
            else:
                print("   1. Check backend filtering logic - companies exist but not being returned")
                print("   2. Verify /api/companies endpoint filtering for Admin role")
        
        return True

def main():
    """Main debug execution"""
    print("🔍 ADMIN COMPANY VISIBILITY DEBUG TEST")
    print("=" * 60)
    
    tester = AdminCompanyDebugTester()
    
    # Run the comprehensive debug analysis
    success = tester.debug_admin1_company_visibility()
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 DEBUG TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"API Tests Run: {tester.tests_run}")
    print(f"API Tests Passed: {tester.tests_passed}")
    
    if success:
        print("✅ Debug analysis completed successfully")
        print("📋 Check the detailed analysis above for root cause and solution")
        return 0
    else:
        print("❌ Debug analysis failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
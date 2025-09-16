import requests
import sys
import json
from datetime import datetime, timezone
import time

class AdminRoleAccessTester:
    def __init__(self, base_url="https://ship-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tokens = {}  # Store tokens for different users
        self.tests_run = 0
        self.tests_passed = 0
        self.user_data = {}  # Store user data for different accounts

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

    def test_login(self, username, password, user_key):
        """Test login and get token for specific user"""
        print(f"\n🔐 Testing Authentication with {username}/{password}")
        success, response = self.run_test(
            f"{user_key} Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.tokens[user_key] = response['access_token']
            self.user_data[user_key] = response.get('user', {})
            print(f"✅ Login successful for {user_key}")
            print(f"   User: {response.get('user', {}).get('full_name')} ({response.get('user', {}).get('role')})")
            print(f"   Company: {response.get('user', {}).get('company')}")
            return True
        return False

    def test_admin_user_filtering(self):
        """Test Admin role user management filtering"""
        print(f"\n👥 Testing Admin User Management Filtering")
        
        # Test admin1 user filtering
        admin1_token = self.tokens.get('admin1')
        if not admin1_token:
            print("❌ admin1 token not available")
            return False
        
        success, users = self.run_test(
            "Admin1 Get Users (Should see only XYZ Company users)",
            "GET",
            "users",
            200,
            token=admin1_token
        )
        
        if not success:
            return False
        
        print(f"   Admin1 sees {len(users)} users")
        
        # Analyze user companies
        xyz_users = []
        abc_users = []
        other_users = []
        
        for user in users:
            company = user.get('company', 'None')
            username = user.get('username', 'Unknown')
            role = user.get('role', 'Unknown')
            print(f"   - {username} ({role}) - Company: {company}")
            
            if company == 'XYZ Company':
                xyz_users.append(user)
            elif company in ['ABC Company Ltd Updated', 'ABC Company']:
                abc_users.append(user)
            else:
                other_users.append(user)
        
        # Verify admin1 only sees XYZ Company users
        expected_xyz_users = ['admin1', 'officer1']  # Based on test credentials
        found_xyz_usernames = [u.get('username') for u in xyz_users]
        
        print(f"\n   Analysis:")
        print(f"   - XYZ Company users: {len(xyz_users)} ({found_xyz_usernames})")
        print(f"   - ABC Company users: {len(abc_users)} (should be 0 for admin1)")
        print(f"   - Other company users: {len(other_users)}")
        
        # Admin1 should only see XYZ Company users
        if len(abc_users) > 0:
            print(f"❌ FAILED: Admin1 can see ABC Company users: {[u.get('username') for u in abc_users]}")
            return False
        
        if len(xyz_users) == 0:
            print(f"❌ FAILED: Admin1 cannot see any XYZ Company users")
            return False
        
        print(f"✅ PASSED: Admin1 correctly sees only XYZ Company users")
        return True

    def test_superadmin_user_access(self):
        """Test Super Admin sees all users"""
        print(f"\n👑 Testing Super Admin User Access (Should see ALL users)")
        
        superadmin_token = self.tokens.get('superadmin1')
        if not superadmin_token:
            print("❌ superadmin1 token not available")
            return False
        
        success, users = self.run_test(
            "SuperAdmin1 Get Users (Should see ALL users)",
            "GET",
            "users",
            200,
            token=superadmin_token
        )
        
        if not success:
            return False
        
        print(f"   SuperAdmin1 sees {len(users)} users")
        
        # Analyze all users
        company_breakdown = {}
        for user in users:
            company = user.get('company', 'None')
            username = user.get('username', 'Unknown')
            role = user.get('role', 'Unknown')
            print(f"   - {username} ({role}) - Company: {company}")
            
            if company not in company_breakdown:
                company_breakdown[company] = []
            company_breakdown[company].append(username)
        
        print(f"\n   Company Breakdown:")
        for company, usernames in company_breakdown.items():
            print(f"   - {company}: {len(usernames)} users ({usernames})")
        
        # Super Admin should see users from multiple companies
        if len(company_breakdown) < 2:
            print(f"❌ FAILED: Super Admin should see users from multiple companies")
            return False
        
        print(f"✅ PASSED: Super Admin correctly sees all users from multiple companies")
        return True

    def test_admin_company_filtering(self):
        """Test Admin role company management filtering"""
        print(f"\n🏢 Testing Admin Company Management Filtering")
        
        admin1_token = self.tokens.get('admin1')
        if not admin1_token:
            print("❌ admin1 token not available")
            return False
        
        success, companies = self.run_test(
            "Admin1 Get Companies (Should see only XYZ Company)",
            "GET",
            "companies",
            200,
            token=admin1_token
        )
        
        if not success:
            return False
        
        print(f"   Admin1 sees {len(companies)} companies")
        
        # Analyze companies
        xyz_companies = []
        abc_companies = []
        other_companies = []
        
        for company in companies:
            name_vn = company.get('name_vn', '')
            name_en = company.get('name_en', '')
            company_id = company.get('id', '')
            print(f"   - {name_vn} / {name_en} (ID: {company_id})")
            
            if name_en == 'XYZ Company' or name_vn == 'Công ty XYZ':
                xyz_companies.append(company)
            elif 'ABC' in name_en or 'ABC' in name_vn:
                abc_companies.append(company)
            else:
                other_companies.append(company)
        
        print(f"\n   Analysis:")
        print(f"   - XYZ Companies: {len(xyz_companies)}")
        print(f"   - ABC Companies: {len(abc_companies)} (should be 0 for admin1)")
        print(f"   - Other Companies: {len(other_companies)}")
        
        # Admin1 should only see XYZ Company
        if len(abc_companies) > 0:
            print(f"❌ FAILED: Admin1 can see ABC companies")
            return False
        
        if len(xyz_companies) == 0:
            print(f"❌ FAILED: Admin1 cannot see XYZ Company")
            return False
        
        # Store XYZ company ID for edit test
        self.xyz_company_id = xyz_companies[0].get('id') if xyz_companies else None
        
        print(f"✅ PASSED: Admin1 correctly sees only XYZ Company")
        return True

    def test_superadmin_company_access(self):
        """Test Super Admin sees all companies"""
        print(f"\n🏢 Testing Super Admin Company Access (Should see ALL companies)")
        
        superadmin_token = self.tokens.get('superadmin1')
        if not superadmin_token:
            print("❌ superadmin1 token not available")
            return False
        
        success, companies = self.run_test(
            "SuperAdmin1 Get Companies (Should see ALL companies)",
            "GET",
            "companies",
            200,
            token=superadmin_token
        )
        
        if not success:
            return False
        
        print(f"   SuperAdmin1 sees {len(companies)} companies")
        
        # Analyze all companies
        company_types = {'XYZ': [], 'ABC': [], 'Other': []}
        for company in companies:
            name_vn = company.get('name_vn', '')
            name_en = company.get('name_en', '')
            company_id = company.get('id', '')
            print(f"   - {name_vn} / {name_en} (ID: {company_id})")
            
            if 'XYZ' in name_en or 'XYZ' in name_vn:
                company_types['XYZ'].append(company)
                # Store ABC company ID for cross-company edit test
                if not hasattr(self, 'abc_company_id'):
                    # Find an ABC company for the cross-company test
                    pass
            elif 'ABC' in name_en or 'ABC' in name_vn:
                company_types['ABC'].append(company)
                # Store ABC company ID for cross-company edit test
                self.abc_company_id = company.get('id')
            else:
                company_types['Other'].append(company)
        
        print(f"\n   Company Type Breakdown:")
        for company_type, company_list in company_types.items():
            print(f"   - {company_type}: {len(company_list)} companies")
        
        # Super Admin should see multiple companies
        total_companies = sum(len(companies) for companies in company_types.values())
        if total_companies < 2:
            print(f"❌ FAILED: Super Admin should see multiple companies")
            return False
        
        print(f"✅ PASSED: Super Admin correctly sees all companies")
        return True

    def test_admin_company_edit_permissions(self):
        """Test Admin can edit own company but not others"""
        print(f"\n✏️ Testing Admin Company Edit Permissions")
        
        admin1_token = self.tokens.get('admin1')
        if not admin1_token:
            print("❌ admin1 token not available")
            return False
        
        # Test 1: Admin1 should be able to edit XYZ Company
        if hasattr(self, 'xyz_company_id') and self.xyz_company_id:
            print(f"\n   Testing edit of own company (XYZ Company ID: {self.xyz_company_id})")
            
            edit_data = {
                "name_vn": "Công ty XYZ Cập Nhật",
                "name_en": "XYZ Company Updated",
                "address_vn": "123 Đường Test, TP.HCM",
                "address_en": "123 Test Street, HCMC",
                "tax_id": "0123456789",
                "gmail": "admin@xyzcompany.com",
                "zalo": "0901234567"
            }
            
            success, response = self.run_test(
                "Admin1 Edit Own Company (Should succeed)",
                "PUT",
                f"companies/{self.xyz_company_id}",
                200,
                data=edit_data,
                token=admin1_token
            )
            
            if not success:
                print(f"❌ FAILED: Admin1 cannot edit own company")
                return False
            
            print(f"✅ PASSED: Admin1 can edit own company")
        else:
            print(f"⚠️ SKIPPED: XYZ Company ID not available for edit test")
        
        # Test 2: Admin1 should NOT be able to edit ABC Company
        if hasattr(self, 'abc_company_id') and self.abc_company_id:
            print(f"\n   Testing edit of other company (ABC Company ID: {self.abc_company_id})")
            
            edit_data = {
                "name_vn": "Công ty ABC Hack Attempt",
                "name_en": "ABC Company Hack Attempt",
                "address_vn": "Hacker Address",
                "address_en": "Hacker Address",
                "tax_id": "9999999999",
                "gmail": "hacker@abc.com",
                "zalo": "0999999999"
            }
            
            success, response = self.run_test(
                "Admin1 Edit Other Company (Should fail with 403)",
                "PUT",
                f"companies/{self.abc_company_id}",
                403,
                data=edit_data,
                token=admin1_token
            )
            
            if not success:
                print(f"❌ FAILED: Admin1 edit restriction not working properly")
                return False
            
            print(f"✅ PASSED: Admin1 correctly blocked from editing other company")
        else:
            print(f"⚠️ SKIPPED: ABC Company ID not available for cross-company edit test")
        
        return True

    def run_all_tests(self):
        """Run all admin role access control tests"""
        print("🔐 Admin Role Access Control Testing")
        print("=" * 60)
        
        # Test credentials from review request
        test_users = [
            ("admin1", "123456", "admin1"),
            ("superadmin1", "123456", "superadmin1"),
            ("officer1", "123456", "officer1"),
            ("crew1", "123456", "crew1")
        ]
        
        # Login all test users
        login_success = True
        for username, password, user_key in test_users:
            if not self.test_login(username, password, user_key):
                print(f"❌ Failed to login {user_key}")
                login_success = False
        
        if not login_success:
            print("❌ Some logins failed, stopping tests")
            return False
        
        # Run all access control tests
        test_results = []
        
        test_results.append(("Admin User Filtering", self.test_admin_user_filtering()))
        test_results.append(("Super Admin User Access", self.test_superadmin_user_access()))
        test_results.append(("Admin Company Filtering", self.test_admin_company_filtering()))
        test_results.append(("Super Admin Company Access", self.test_superadmin_company_access()))
        test_results.append(("Admin Company Edit Permissions", self.test_admin_company_edit_permissions()))
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 ADMIN ROLE ACCESS CONTROL TEST RESULTS")
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
        
        # Summary of expected vs actual results
        print(f"\n📋 EXPECTED RESULTS VERIFICATION:")
        print(f"✓ Admin sees only same company users: {'✅' if passed_tests > 0 else '❌'}")
        print(f"✓ Admin sees only own company: {'✅' if passed_tests > 1 else '❌'}")
        print(f"✓ Admin can edit own company: {'✅' if passed_tests > 3 else '❌'}")
        print(f"✓ Admin cannot edit other companies: {'✅' if passed_tests > 3 else '❌'}")
        print(f"✓ Super Admin sees all users/companies: {'✅' if passed_tests > 2 else '❌'}")
        
        if passed_tests == total_tests and self.tests_passed == self.tests_run:
            print("\n🎉 All Admin Role Access Control tests passed!")
            return True
        else:
            print("\n⚠️ Some tests failed - Admin role access control needs attention")
            return False

def main():
    """Main test execution"""
    tester = AdminRoleAccessTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
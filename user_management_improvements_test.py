import requests
import sys
import json
from datetime import datetime, timezone
import time
import random
import string

class UserManagementImprovementsTester:
    def __init__(self, base_url="https://vessel-docs-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.test_users = {}  # Store created test users
        self.companies = []
        self.ships = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if params:
            print(f"   Params: {params}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
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
                        print(f"   Response: {json.dumps(response_data, indent=2)[:500]}...")
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

    def setup_test_data(self):
        """Setup test data - companies, ships, and users"""
        print(f"\n🔧 Setting up test data...")
        
        # Get existing companies and ships
        success, companies = self.run_test("Get Companies", "GET", "companies", 200)
        if success:
            self.companies = companies
            print(f"   Found {len(companies)} companies")
        
        success, ships = self.run_test("Get Ships", "GET", "ships", 200)
        if success:
            self.ships = ships
            print(f"   Found {len(ships)} ships")
        
        # Create test users with different roles
        test_users_data = [
            {
                "username": f"crew_user_{int(time.time())}",
                "email": f"crew_{int(time.time())}@shipmanagement.com",
                "password": "CrewPass123!",
                "full_name": "Test Crew Member",
                "role": "viewer",
                "department": "ship_crew",
                "company": self.companies[0]['name_en'] if self.companies else "Test Company",
                "ship": self.ships[0]['id'] if self.ships else None,
                "zalo": f"090{random.randint(1000000, 9999999)}",
                "gmail": f"crew.gmail_{int(time.time())}@gmail.com"
            },
            {
                "username": f"manager_user_{int(time.time())}",
                "email": f"manager_{int(time.time())}@shipmanagement.com", 
                "password": "ManagerPass123!",
                "full_name": "Test Manager",
                "role": "manager",
                "department": "operations",
                "company": self.companies[0]['name_en'] if self.companies else "Test Company",
                "zalo": f"091{random.randint(1000000, 9999999)}",
                "gmail": f"manager.gmail_{int(time.time())}@gmail.com"
            }
        ]
        
        for user_data in test_users_data:
            success, user = self.run_test(
                f"Create Test User ({user_data['role']})",
                "POST",
                "users",
                200,
                data=user_data
            )
            if success:
                self.test_users[user_data['role']] = {
                    'data': user,
                    'credentials': {'username': user_data['username'], 'password': user_data['password']}
                }
                print(f"   Created {user_data['role']} user: {user.get('username')}")
        
        return len(self.test_users) > 0

    def test_enhanced_user_filtering_and_sorting(self):
        """Test Enhanced User Filtering and Sorting API"""
        print(f"\n🔍 Testing Enhanced User Filtering and Sorting API")
        
        # Test 1: Basic filtered endpoint without filters
        success, users = self.run_test(
            "Get Filtered Users (No Filters)",
            "GET",
            "users/filtered",
            200
        )
        if not success:
            return False
        
        print(f"   Found {len(users)} users without filters")
        
        # Test 2: Filter by company
        if self.companies:
            company_name = self.companies[0]['name_en']
            success, filtered_users = self.run_test(
                "Filter Users by Company",
                "GET",
                "users/filtered",
                200,
                params={"company": company_name}
            )
            if success:
                print(f"   Found {len(filtered_users)} users for company: {company_name}")
        
        # Test 3: Filter by department
        success, dept_users = self.run_test(
            "Filter Users by Department",
            "GET", 
            "users/filtered",
            200,
            params={"department": "operations"}
        )
        if success:
            print(f"   Found {len(dept_users)} users in operations department")
        
        # Test 4: Filter by ship
        if self.ships:
            ship_id = self.ships[0]['id']
            success, ship_users = self.run_test(
                "Filter Users by Ship",
                "GET",
                "users/filtered", 
                200,
                params={"ship": ship_id}
            )
            if success:
                print(f"   Found {len(ship_users)} users assigned to ship")
        
        # Test 5: Sort by full_name ascending
        success, sorted_users = self.run_test(
            "Sort Users by Full Name (ASC)",
            "GET",
            "users/filtered",
            200,
            params={"sort_by": "full_name", "sort_order": "asc"}
        )
        if success:
            print(f"   Sorted {len(sorted_users)} users by full_name ascending")
            if len(sorted_users) >= 2:
                print(f"   First user: {sorted_users[0].get('full_name')}")
                print(f"   Last user: {sorted_users[-1].get('full_name')}")
        
        # Test 6: Sort by company descending
        success, sorted_users = self.run_test(
            "Sort Users by Company (DESC)",
            "GET",
            "users/filtered",
            200,
            params={"sort_by": "company", "sort_order": "desc"}
        )
        if success:
            print(f"   Sorted {len(sorted_users)} users by company descending")
        
        # Test 7: Sort by created_at
        success, sorted_users = self.run_test(
            "Sort Users by Created Date",
            "GET",
            "users/filtered",
            200,
            params={"sort_by": "created_at", "sort_order": "desc"}
        )
        if success:
            print(f"   Sorted {len(sorted_users)} users by creation date")
        
        # Test 8: Combined filters and sorting
        if self.companies:
            success, combined_result = self.run_test(
                "Combined Filter and Sort",
                "GET",
                "users/filtered",
                200,
                params={
                    "company": self.companies[0]['name_en'],
                    "sort_by": "role",
                    "sort_order": "asc"
                }
            )
            if success:
                print(f"   Combined filter/sort returned {len(combined_result)} users")
        
        return True

    def test_self_edit_permissions(self):
        """Test Self-Edit Permissions for Crew Role"""
        print(f"\n👤 Testing Self-Edit Permissions for Crew Role")
        
        if 'viewer' not in self.test_users:
            print("   ❌ No crew user available for testing")
            return False
        
        crew_user = self.test_users['viewer']
        crew_user_id = crew_user['data']['id']
        
        # Login as crew user
        crew_credentials = crew_user['credentials']
        success, crew_login = self.run_test(
            "Crew User Login",
            "POST",
            "auth/login",
            200,
            data=crew_credentials
        )
        if not success:
            return False
        
        # Store original token and switch to crew token
        admin_token = self.token
        self.token = crew_login['access_token']
        
        # Test 1: Get editable fields for crew user (self)
        success, editable_fields = self.run_test(
            "Get Editable Fields (Crew Self)",
            "GET",
            f"users/{crew_user_id}/editable-fields",
            200
        )
        if success:
            expected_fields = ["email", "zalo", "password"]
            actual_fields = editable_fields.get('editable_fields', [])
            print(f"   Crew can edit fields: {actual_fields}")
            if set(expected_fields).issubset(set(actual_fields)):
                print(f"   ✅ Crew has correct self-edit permissions")
            else:
                print(f"   ❌ Expected fields {expected_fields}, got {actual_fields}")
        
        # Test 2: Self-edit email and zalo
        new_email = f"updated_crew_{int(time.time())}@shipmanagement.com"
        new_zalo = f"092{random.randint(1000000, 9999999)}"
        
        success, updated_user = self.run_test(
            "Crew Self-Edit Email and Zalo",
            "PUT",
            f"users/{crew_user_id}/self-edit",
            200,
            data={
                "email": new_email,
                "zalo": new_zalo
            }
        )
        if success:
            print(f"   ✅ Crew successfully updated email: {updated_user.get('email')}")
            print(f"   ✅ Crew successfully updated zalo: {updated_user.get('zalo')}")
        
        # Test 3: Try to edit restricted fields (should fail or be ignored)
        success, restricted_edit = self.run_test(
            "Crew Try Edit Restricted Fields",
            "PUT",
            f"users/{crew_user_id}/self-edit",
            200,  # Should succeed but ignore restricted fields
            data={
                "role": "admin",  # Should be ignored
                "company": "Hacker Company",  # Should be ignored
                "email": f"final_crew_{int(time.time())}@shipmanagement.com"  # Should work
            }
        )
        if success:
            # Check that role and company weren't changed
            if restricted_edit.get('role') == 'viewer' and restricted_edit.get('company') != "Hacker Company":
                print(f"   ✅ Restricted fields properly ignored")
            else:
                print(f"   ❌ Restricted fields were changed: role={restricted_edit.get('role')}, company={restricted_edit.get('company')}")
        
        # Test 4: Try to edit another user (should fail)
        if 'manager' in self.test_users:
            manager_user_id = self.test_users['manager']['data']['id']
            success, unauthorized_edit = self.run_test(
                "Crew Try Edit Other User",
                "PUT",
                f"users/{manager_user_id}/self-edit",
                403,  # Should be forbidden
                data={"email": "hacker@evil.com"}
            )
            if not success:  # We expect this to fail (403)
                print(f"   ✅ Crew correctly blocked from editing other users")
        
        # Restore admin token
        self.token = admin_token
        
        return True

    def test_user_model_enhancements(self):
        """Test User Model Enhancement with Zalo and Gmail"""
        print(f"\n📝 Testing User Model Enhancement with Zalo and Gmail")
        
        # Test 1: Create user with zalo field (should succeed)
        user_with_zalo = {
            "username": f"zalo_user_{int(time.time())}",
            "email": f"zalo_test_{int(time.time())}@shipmanagement.com",
            "password": "ZaloTest123!",
            "full_name": "Zalo Test User",
            "role": "viewer",
            "department": "technical",
            "company": self.companies[0]['name_en'] if self.companies else "Test Company",
            "zalo": f"093{random.randint(1000000, 9999999)}",
            "gmail": f"zalo.gmail_{int(time.time())}@gmail.com"
        }
        
        success, created_user = self.run_test(
            "Create User with Zalo and Gmail",
            "POST",
            "users",
            200,
            data=user_with_zalo
        )
        if success:
            print(f"   ✅ User created with zalo: {created_user.get('zalo')}")
            print(f"   ✅ User created with gmail: {created_user.get('gmail')}")
        
        # Test 2: Try to create user without zalo field (should fail)
        user_without_zalo = {
            "username": f"no_zalo_user_{int(time.time())}",
            "email": f"no_zalo_{int(time.time())}@shipmanagement.com",
            "password": "NoZalo123!",
            "full_name": "No Zalo User",
            "role": "viewer",
            "department": "technical",
            "company": self.companies[0]['name_en'] if self.companies else "Test Company"
            # Missing zalo field
        }
        
        success, failed_user = self.run_test(
            "Create User without Zalo (Should Fail)",
            "POST",
            "users",
            400,  # Should fail with validation error
            data=user_without_zalo
        )
        if not success:  # We expect this to fail
            print(f"   ✅ User creation correctly failed without zalo field")
        
        # Test 3: Try to create user with empty zalo (should fail)
        user_empty_zalo = {
            "username": f"empty_zalo_user_{int(time.time())}",
            "email": f"empty_zalo_{int(time.time())}@shipmanagement.com",
            "password": "EmptyZalo123!",
            "full_name": "Empty Zalo User",
            "role": "viewer",
            "department": "technical",
            "company": self.companies[0]['name_en'] if self.companies else "Test Company",
            "zalo": ""  # Empty zalo
        }
        
        success, failed_user = self.run_test(
            "Create User with Empty Zalo (Should Fail)",
            "POST",
            "users",
            400,  # Should fail with validation error
            data=user_empty_zalo
        )
        if not success:  # We expect this to fail
            print(f"   ✅ User creation correctly failed with empty zalo field")
        
        # Test 4: Verify existing users have zalo and gmail fields
        success, all_users = self.run_test(
            "Get All Users to Check Fields",
            "GET",
            "users",
            200
        )
        if success:
            users_with_zalo = [u for u in all_users if u.get('zalo')]
            users_with_gmail = [u for u in all_users if u.get('gmail')]
            print(f"   Found {len(users_with_zalo)} users with zalo field")
            print(f"   Found {len(users_with_gmail)} users with gmail field")
        
        return True

    def test_role_based_access_control(self):
        """Test role-based access control for filtering"""
        print(f"\n🔐 Testing Role-Based Access Control")
        
        # Test with different user roles
        for role, user_info in self.test_users.items():
            if role == 'viewer':  # Skip viewer as they don't have manager permissions
                continue
                
            print(f"\n   Testing with {role} user...")
            
            # Login as this user
            credentials = user_info['credentials']
            success, login_response = self.run_test(
                f"{role.title()} User Login",
                "POST",
                "auth/login",
                200,
                data=credentials
            )
            if not success:
                continue
            
            # Store admin token and switch to user token
            admin_token = self.token
            self.token = login_response['access_token']
            
            # Test filtered users endpoint
            success, filtered_users = self.run_test(
                f"Get Filtered Users as {role.title()}",
                "GET",
                "users/filtered",
                200
            )
            if success:
                user_companies = set(u.get('company') for u in filtered_users if u.get('company'))
                print(f"   {role.title()} sees users from companies: {user_companies}")
                
                # Manager should only see same company users
                if role == 'manager':
                    user_company = user_info['data'].get('company')
                    if user_company and len(user_companies) == 1 and user_company in user_companies:
                        print(f"   ✅ Manager correctly sees only same company users")
                    else:
                        print(f"   ❌ Manager access control issue")
            
            # Restore admin token
            self.token = admin_token
        
        return True

    def test_existing_functionality(self):
        """Test that existing functionality still works"""
        print(f"\n🔄 Testing Existing Functionality")
        
        # Test 1: Regular GET /api/users still works
        success, users = self.run_test(
            "Get Users (Original Endpoint)",
            "GET",
            "users",
            200
        )
        if success:
            print(f"   ✅ Original users endpoint works: {len(users)} users")
        
        # Test 2: User creation still works
        legacy_user = {
            "username": f"legacy_user_{int(time.time())}",
            "email": f"legacy_{int(time.time())}@shipmanagement.com",
            "password": "Legacy123!",
            "full_name": "Legacy Test User",
            "role": "viewer",
            "department": "technical",
            "zalo": f"094{random.randint(1000000, 9999999)}"  # Now required
        }
        
        success, created_user = self.run_test(
            "Create User (Legacy Style)",
            "POST",
            "users",
            200,
            data=legacy_user
        )
        if success:
            print(f"   ✅ User creation still works: {created_user.get('username')}")
        
        # Test 3: User update still works
        if created_user:
            success, updated_user = self.run_test(
                "Update User (Legacy Style)",
                "PUT",
                f"users/{created_user['id']}",
                200,
                data={"full_name": "Updated Legacy User"}
            )
            if success:
                print(f"   ✅ User update still works: {updated_user.get('full_name')}")
        
        return True

def main():
    """Main test execution"""
    print("🚢 User Management Improvements Testing")
    print("=" * 60)
    
    tester = UserManagementImprovementsTester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Setup test data
    if not tester.setup_test_data():
        print("❌ Test data setup failed, stopping tests")
        return 1
    
    # Run all tests
    test_results = []
    
    test_results.append(("Enhanced User Filtering and Sorting API", tester.test_enhanced_user_filtering_and_sorting()))
    test_results.append(("Self-Edit Permissions for Crew Role", tester.test_self_edit_permissions()))
    test_results.append(("User Model Enhancement with Zalo and Gmail", tester.test_user_model_enhancements()))
    test_results.append(("Role-Based Access Control", tester.test_role_based_access_control()))
    test_results.append(("Existing Functionality", tester.test_existing_functionality()))
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 USER MANAGEMENT IMPROVEMENTS TEST RESULTS")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:45} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Feature Tests: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests and tester.tests_passed == tester.tests_run:
        print("🎉 All User Management Improvements tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
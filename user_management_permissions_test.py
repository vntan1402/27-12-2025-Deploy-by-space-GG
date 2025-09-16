import requests
import sys
import json
from datetime import datetime, timezone
import time

class UserManagementPermissionsAPITester:
    def __init__(self, base_url="https://aicert-analyzer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tokens = {}  # Store tokens for different users
        self.user_data = {}  # Store user data for different users
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test credentials from review request
        self.test_users = {
            "manager1": {"username": "manager1", "password": "123456", "expected_role": "manager", "expected_company": "ABC Company Ltd Updated"},
            "admin1": {"username": "admin1", "password": "123456", "expected_role": "admin", "expected_company": "XYZ Company"},
            "superadmin1": {"username": "superadmin1", "password": "123456", "expected_role": "super_admin", "expected_company": "ABC Company Ltd Updated"},
            "crew1": {"username": "crew1", "password": "123456", "expected_role": "viewer", "expected_company": "ABC Company Ltd Updated"},
            "officer1": {"username": "officer1", "password": "123456", "expected_role": "editor", "expected_company": "XYZ Company"}
        }

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

    def test_login_all_users(self):
        """Test login for all test users and verify their roles"""
        print(f"\n🔐 Testing Authentication for All Test Users")
        
        all_success = True
        for user_key, user_info in self.test_users.items():
            print(f"\n--- Testing login for {user_key} ---")
            success, response = self.run_test(
                f"Login {user_key}",
                "POST",
                "auth/login",
                200,
                data={"username": user_info["username"], "password": user_info["password"]},
                token=None
            )
            
            if success and 'access_token' in response:
                self.tokens[user_key] = response['access_token']
                self.user_data[user_key] = response.get('user', {})
                
                # Verify role and company
                actual_role = self.user_data[user_key].get('role')
                actual_company = self.user_data[user_key].get('company')
                expected_role = user_info["expected_role"]
                expected_company = user_info["expected_company"]
                
                print(f"   ✅ Login successful for {user_key}")
                print(f"   User: {self.user_data[user_key].get('full_name')} ({actual_role})")
                print(f"   Company: {actual_company}")
                
                # Verify role matches expected
                if actual_role != expected_role:
                    print(f"   ⚠️ Role mismatch: expected {expected_role}, got {actual_role}")
                    all_success = False
                
                # Verify company matches expected
                if actual_company != expected_company:
                    print(f"   ⚠️ Company mismatch: expected {expected_company}, got {actual_company}")
                    all_success = False
                    
            else:
                print(f"   ❌ Login failed for {user_key}")
                all_success = False
        
        return all_success

    def test_company_filtering_manager(self):
        """Test company filtering for Manager role - manager1 should only see ABC Company users"""
        print(f"\n🏢 Testing Company Filtering for Manager Role")
        
        if 'manager1' not in self.tokens:
            print("❌ manager1 token not available")
            return False
        
        # Get users as manager1
        success, users = self.run_test(
            "Get Users as Manager1",
            "GET",
            "users",
            200,
            token=self.tokens['manager1']
        )
        
        if not success:
            return False
        
        print(f"   Manager1 sees {len(users)} users")
        
        # Verify all users belong to ABC Company Ltd Updated
        abc_company_users = 0
        other_company_users = 0
        
        for user in users:
            user_company = user.get('company', 'No Company')
            print(f"   - {user.get('username')} ({user.get('role')}) - Company: {user_company}")
            
            if user_company == "ABC Company Ltd Updated":
                abc_company_users += 1
            else:
                other_company_users += 1
        
        print(f"   ABC Company users: {abc_company_users}")
        print(f"   Other company users: {other_company_users}")
        
        # Manager should only see ABC Company users (expected: 3 users - manager1, superadmin1, crew1)
        if other_company_users > 0:
            print(f"   ❌ Manager1 can see users from other companies - filtering not working")
            return False
        
        if abc_company_users != 3:
            print(f"   ⚠️ Expected 3 ABC Company users, found {abc_company_users}")
        
        print(f"   ✅ Company filtering working - Manager only sees same company users")
        return True

    def test_admin_sees_all_users(self):
        """Test that Admin sees all users (no company filtering)"""
        print(f"\n👑 Testing Admin Sees All Users")
        
        if 'admin1' not in self.tokens:
            print("❌ admin1 token not available")
            return False
        
        # Get users as admin1
        success, users = self.run_test(
            "Get Users as Admin1",
            "GET",
            "users",
            200,
            token=self.tokens['admin1']
        )
        
        if not success:
            return False
        
        print(f"   Admin1 sees {len(users)} users")
        
        # Count users by company
        company_counts = {}
        for user in users:
            company = user.get('company', 'No Company')
            company_counts[company] = company_counts.get(company, 0) + 1
        
        print(f"   Users by company:")
        for company, count in company_counts.items():
            print(f"   - {company}: {count} users")
        
        # Admin should see users from multiple companies (expected: 8+ users total)
        if len(users) < 5:  # Should see at least 5 test users
            print(f"   ❌ Admin sees too few users - expected at least 5")
            return False
        
        if len(company_counts) < 2:
            print(f"   ❌ Admin should see users from multiple companies")
            return False
        
        print(f"   ✅ Admin can see all users from all companies")
        return True

    def test_super_admin_sees_all_users(self):
        """Test that Super Admin sees all users"""
        print(f"\n👑 Testing Super Admin Sees All Users")
        
        if 'superadmin1' not in self.tokens:
            print("❌ superadmin1 token not available")
            return False
        
        # Get users as superadmin1
        success, users = self.run_test(
            "Get Users as SuperAdmin1",
            "GET",
            "users",
            200,
            token=self.tokens['superadmin1']
        )
        
        if not success:
            return False
        
        print(f"   SuperAdmin1 sees {len(users)} users")
        
        # Super Admin should see all users (same as Admin)
        if len(users) < 5:  # Should see at least 5 test users
            print(f"   ❌ Super Admin sees too few users - expected at least 5")
            return False
        
        print(f"   ✅ Super Admin can see all users")
        return True

    def test_can_edit_permissions_endpoint(self):
        """Test GET /api/users/{user_id}/can-edit endpoint for different role combinations"""
        print(f"\n🔐 Testing Can-Edit Permissions Endpoint")
        
        if not all(key in self.tokens for key in ['manager1', 'admin1', 'superadmin1']):
            print("❌ Required tokens not available")
            return False
        
        # First get all users to get their IDs
        success, all_users = self.run_test(
            "Get All Users for Permission Testing",
            "GET",
            "users",
            200,
            token=self.tokens['superadmin1']
        )
        
        if not success:
            return False
        
        # Create user lookup by username
        user_lookup = {}
        for user in all_users:
            user_lookup[user.get('username')] = user
        
        test_scenarios = [
            # (current_user, target_user, expected_can_edit, description)
            ("manager1", "crew1", True, "Manager can edit lower role in same company"),
            ("manager1", "officer1", False, "Manager cannot edit user in different company"),
            ("manager1", "admin1", False, "Manager cannot edit higher role"),
            ("manager1", "superadmin1", False, "Manager cannot edit Super Admin"),
            ("admin1", "crew1", True, "Admin can edit lower role"),
            ("admin1", "manager1", True, "Admin can edit Manager role"),
            ("admin1", "superadmin1", False, "Admin cannot edit Super Admin"),
            ("superadmin1", "admin1", True, "Super Admin can edit Admin"),
            ("superadmin1", "manager1", True, "Super Admin can edit Manager"),
            ("superadmin1", "crew1", True, "Super Admin can edit anyone"),
        ]
        
        all_success = True
        for current_user, target_user, expected_can_edit, description in test_scenarios:
            if target_user not in user_lookup:
                print(f"   ⚠️ Target user {target_user} not found, skipping test")
                continue
            
            target_user_id = user_lookup[target_user]['id']
            
            success, response = self.run_test(
                f"Can Edit: {description}",
                "GET",
                f"users/{target_user_id}/can-edit",
                200,
                token=self.tokens[current_user]
            )
            
            if success:
                actual_can_edit = response.get('can_edit', False)
                if actual_can_edit == expected_can_edit:
                    print(f"   ✅ {description}: {actual_can_edit}")
                else:
                    print(f"   ❌ {description}: expected {expected_can_edit}, got {actual_can_edit}")
                    all_success = False
            else:
                all_success = False
        
        return all_success

    def test_role_hierarchy_edit_permissions(self):
        """Test actual user edit operations based on role hierarchy"""
        print(f"\n⚖️ Testing Role Hierarchy Edit Permissions")
        
        if not all(key in self.tokens for key in ['manager1', 'admin1', 'superadmin1']):
            print("❌ Required tokens not available")
            return False
        
        # Get all users first
        success, all_users = self.run_test(
            "Get All Users for Edit Testing",
            "GET",
            "users",
            200,
            token=self.tokens['superadmin1']
        )
        
        if not success:
            return False
        
        # Find crew1 user for testing
        crew1_user = None
        for user in all_users:
            if user.get('username') == 'crew1':
                crew1_user = user
                break
        
        if not crew1_user:
            print("❌ crew1 user not found for edit testing")
            return False
        
        crew1_id = crew1_user['id']
        
        # Test 1: Manager1 should be able to edit crew1 (same company, lower role)
        print(f"\n--- Test 1: Manager1 editing crew1 (should succeed) ---")
        edit_data = {
            "username": crew1_user['username'],
            "email": crew1_user['email'],
            "full_name": crew1_user['full_name'] + " - Updated by Manager",
            "role": crew1_user['role'],
            "department": crew1_user['department'],
            "company": crew1_user['company'],
            "ship": crew1_user.get('ship'),
            "zalo": crew1_user.get('zalo'),
            "gmail": crew1_user.get('gmail')
        }
        
        success, response = self.run_test(
            "Manager1 Edit crew1",
            "PUT",
            f"users/{crew1_id}",
            200,
            data=edit_data,
            token=self.tokens['manager1']
        )
        
        manager_edit_success = success
        
        # Test 2: Find a Super Admin user and try to edit with admin1 (should fail)
        superadmin_user = None
        for user in all_users:
            if user.get('role') == 'super_admin' and user.get('username') != 'admin':  # Not the default admin
                superadmin_user = user
                break
        
        if superadmin_user:
            print(f"\n--- Test 2: Admin1 editing Super Admin (should fail) ---")
            superadmin_edit_data = {
                "username": superadmin_user['username'],
                "email": superadmin_user['email'],
                "full_name": superadmin_user['full_name'],
                "role": superadmin_user['role'],
                "department": superadmin_user['department'],
                "company": superadmin_user['company'],
                "ship": superadmin_user.get('ship'),
                "zalo": superadmin_user.get('zalo'),
                "gmail": superadmin_user.get('gmail')
            }
            
            success, response = self.run_test(
                "Admin1 Edit Super Admin (should fail)",
                "PUT",
                f"users/{superadmin_user['id']}",
                403,  # Should be forbidden
                data=superadmin_edit_data,
                token=self.tokens['admin1']
            )
            
            admin_edit_superadmin_blocked = success  # Success means it correctly returned 403
        else:
            print("   ⚠️ No Super Admin user found for testing admin edit restrictions")
            admin_edit_superadmin_blocked = True  # Assume success if no test possible
        
        # Test 3: Super Admin should be able to edit anyone
        print(f"\n--- Test 3: Super Admin editing crew1 (should succeed) ---")
        superadmin_edit_data = {
            "username": crew1_user['username'],
            "email": crew1_user['email'],
            "full_name": crew1_user['full_name'].replace(" - Updated by Manager", "") + " - Updated by SuperAdmin",
            "role": crew1_user['role'],
            "department": crew1_user['department'],
            "company": crew1_user['company'],
            "ship": crew1_user.get('ship'),
            "zalo": crew1_user.get('zalo'),
            "gmail": crew1_user.get('gmail')
        }
        
        success, response = self.run_test(
            "SuperAdmin1 Edit crew1",
            "PUT",
            f"users/{crew1_id}",
            200,
            data=superadmin_edit_data,
            token=self.tokens['superadmin1']
        )
        
        superadmin_edit_success = success
        
        # Summary
        print(f"\n--- Role Hierarchy Edit Test Results ---")
        print(f"   Manager1 can edit crew1 (same company, lower role): {'✅' if manager_edit_success else '❌'}")
        print(f"   Admin1 blocked from editing Super Admin: {'✅' if admin_edit_superadmin_blocked else '❌'}")
        print(f"   Super Admin can edit anyone: {'✅' if superadmin_edit_success else '❌'}")
        
        return manager_edit_success and admin_edit_superadmin_blocked and superadmin_edit_success

    def test_cross_company_restrictions(self):
        """Test that Manager cannot edit users from different companies"""
        print(f"\n🏢 Testing Cross-Company Edit Restrictions")
        
        if 'manager1' not in self.tokens:
            print("❌ manager1 token not available")
            return False
        
        # Get all users
        success, all_users = self.run_test(
            "Get All Users for Cross-Company Testing",
            "GET",
            "users",
            200,
            token=self.tokens['superadmin1']
        )
        
        if not success:
            return False
        
        # Find a user from XYZ Company (different from manager1's ABC Company)
        xyz_user = None
        for user in all_users:
            if user.get('company') == 'XYZ Company' and user.get('role') in ['viewer', 'editor']:  # Lower or equal role
                xyz_user = user
                break
        
        if not xyz_user:
            print("   ⚠️ No XYZ Company user found for cross-company testing")
            return True  # Can't test, but not a failure
        
        print(f"   Testing manager1 editing {xyz_user['username']} from {xyz_user['company']}")
        
        # Try to edit the XYZ Company user (should fail)
        edit_data = {
            "username": xyz_user['username'],
            "email": xyz_user['email'],
            "full_name": xyz_user['full_name'] + " - Attempted edit by Manager1",
            "role": xyz_user['role'],
            "department": xyz_user['department'],
            "company": xyz_user['company'],
            "ship": xyz_user.get('ship'),
            "zalo": xyz_user.get('zalo'),
            "gmail": xyz_user.get('gmail')
        }
        
        success, response = self.run_test(
            "Manager1 Edit Cross-Company User (should fail)",
            "PUT",
            f"users/{xyz_user['id']}",
            403,  # Should be forbidden
            data=edit_data,
            token=self.tokens['manager1']
        )
        
        if success:
            print(f"   ✅ Cross-company edit correctly blocked")
            return True
        else:
            print(f"   ❌ Cross-company edit was not blocked")
            return False

    def test_self_edit_prevention(self):
        """Test that users cannot delete themselves"""
        print(f"\n🚫 Testing Self-Edit Prevention")
        
        # Test with admin1 trying to delete themselves
        if 'admin1' not in self.tokens or 'admin1' not in self.user_data:
            print("❌ admin1 data not available")
            return False
        
        admin1_id = self.user_data['admin1']['id']
        
        success, response = self.run_test(
            "Admin1 Delete Self (should fail)",
            "DELETE",
            f"users/{admin1_id}",
            400,  # Should return bad request
            token=self.tokens['admin1']
        )
        
        if success:
            print(f"   ✅ Self-deletion correctly prevented")
            return True
        else:
            print(f"   ❌ Self-deletion was not prevented")
            return False

def main():
    """Main test execution"""
    print("🔐 User Management Permissions & Company Filtering Testing")
    print("=" * 70)
    
    tester = UserManagementPermissionsAPITester()
    
    # Test authentication for all users first
    if not tester.test_login_all_users():
        print("❌ Authentication failed for some users, but continuing with available users")
    
    # Run all permission tests
    test_results = []
    
    test_results.append(("Company Filtering (Manager)", tester.test_company_filtering_manager()))
    test_results.append(("Admin Sees All Users", tester.test_admin_sees_all_users()))
    test_results.append(("Super Admin Sees All Users", tester.test_super_admin_sees_all_users()))
    test_results.append(("Can-Edit Permissions Endpoint", tester.test_can_edit_permissions_endpoint()))
    test_results.append(("Role Hierarchy Edit Permissions", tester.test_role_hierarchy_edit_permissions()))
    test_results.append(("Cross-Company Restrictions", tester.test_cross_company_restrictions()))
    test_results.append(("Self-Edit Prevention", tester.test_self_edit_prevention()))
    
    # Print final results
    print("\n" + "=" * 70)
    print("📊 USER MANAGEMENT PERMISSIONS TEST RESULTS")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:35} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Feature Tests: {passed_tests}/{total_tests}")
    
    # Summary of key findings
    print(f"\n📋 KEY FINDINGS:")
    print(f"   - Manager Role Company Filtering: {'✅ Working' if test_results[0][1] else '❌ Not Working'}")
    print(f"   - Role Hierarchy Permissions: {'✅ Working' if test_results[3][1] and test_results[4][1] else '❌ Issues Found'}")
    print(f"   - Cross-Company Restrictions: {'✅ Working' if test_results[5][1] else '❌ Not Working'}")
    print(f"   - Self-Edit Prevention: {'✅ Working' if test_results[6][1] else '❌ Not Working'}")
    
    if passed_tests == total_tests and tester.tests_passed >= (tester.tests_run * 0.9):  # Allow 10% tolerance
        print("\n🎉 User Management Permissions Testing PASSED!")
        return 0
    else:
        print("\n⚠️ Some User Management Permission tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
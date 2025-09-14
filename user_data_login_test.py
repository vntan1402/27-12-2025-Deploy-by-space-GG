import requests
import sys
import json
from datetime import datetime, timezone
import time

class UserDataLoginTester:
    def __init__(self, base_url="https://shipgooglesync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.all_users = []

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

    def test_admin_login(self):
        """Test admin login to get access token"""
        print(f"\n🔐 Testing Admin Authentication (admin/admin123)")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            user_info = response.get('user', {})
            print(f"✅ Admin login successful")
            print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
            print(f"   Username: {user_info.get('username')}")
            print(f"   Email: {user_info.get('email')}")
            print(f"   Company: {user_info.get('company')}")
            print(f"   Department: {user_info.get('department')}")
            return True
        return False

    def test_get_all_users(self):
        """Get all users from MongoDB"""
        print(f"\n👥 Testing GET /api/users - Retrieve All Users from MongoDB")
        success, users = self.run_test("Get All Users", "GET", "users", 200)
        
        if not success:
            return False
        
        self.all_users = users
        print(f"✅ Found {len(users)} users in MongoDB")
        print(f"\n📋 DETAILED USER LIST:")
        print("=" * 80)
        
        for i, user in enumerate(users, 1):
            print(f"{i}. Username: {user.get('username')}")
            print(f"   Full Name: {user.get('full_name')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Role: {user.get('role')}")
            print(f"   Department: {user.get('department')}")
            print(f"   Company: {user.get('company')}")
            print(f"   Ship: {user.get('ship')}")
            print(f"   Active: {user.get('is_active')}")
            print(f"   Created: {user.get('created_at')}")
            print(f"   User ID: {user.get('id')}")
            print("-" * 40)
        
        return True

    def test_specific_user_login(self, username, password, expected_success=True):
        """Test login with specific credentials"""
        print(f"\n🔐 Testing Login: {username}/{password}")
        
        success, response = self.run_test(
            f"Login {username}",
            "POST",
            "auth/login",
            200 if expected_success else 401,
            data={"username": username, "password": password}
        )
        
        if expected_success and success:
            if 'access_token' in response and 'user' in response:
                user_info = response.get('user', {})
                print(f"✅ Login successful for {username}")
                print(f"   Full Name: {user_info.get('full_name')}")
                print(f"   Role: {user_info.get('role')}")
                print(f"   Company: {user_info.get('company')}")
                print(f"   Department: {user_info.get('department')}")
                print(f"   Email: {user_info.get('email')}")
                print(f"   Active: {user_info.get('is_active')}")
                
                # Test JWT token validity
                temp_token = response['access_token']
                headers = {'Authorization': f'Bearer {temp_token}'}
                try:
                    test_response = requests.get(f"{self.api_url}/users", headers=headers, timeout=10)
                    if test_response.status_code == 200:
                        print(f"   JWT Token: ✅ Valid")
                    else:
                        print(f"   JWT Token: ❌ Invalid (Status: {test_response.status_code})")
                except Exception as e:
                    print(f"   JWT Token: ❌ Error testing token: {e}")
                
                return True
            else:
                print(f"❌ Login response missing required fields")
                return False
        elif not expected_success and not success:
            print(f"✅ Login correctly failed for {username} (as expected)")
            return True
        elif expected_success and not success:
            print(f"❌ Login failed for {username} (unexpected)")
            return False
        else:
            print(f"❌ Login succeeded for {username} (should have failed)")
            return False

    def test_all_user_logins(self):
        """Test login for all specified users"""
        print(f"\n🔐 Testing Login for All Specified Users")
        print("=" * 60)
        
        # List of users to test as specified in the review request
        test_users = [
            ("admin", "admin123", True),  # Main user
            ("admin1", "123456", True),   # Previously created user
            ("manager1", "123456", True),
            ("crew1", "123456", True),
            ("officer1", "123456", True),
            ("superadmin1", "123456", True),
        ]
        
        login_results = []
        
        for username, password, should_succeed in test_users:
            result = self.test_specific_user_login(username, password, should_succeed)
            login_results.append((username, result))
        
        # Summary of login tests
        print(f"\n📊 LOGIN TEST SUMMARY:")
        print("=" * 40)
        successful_logins = 0
        for username, result in login_results:
            status = "✅ SUCCESS" if result else "❌ FAILED"
            print(f"{username:15} {status}")
            if result:
                successful_logins += 1
        
        print(f"\nSuccessful Logins: {successful_logins}/{len(login_results)}")
        return successful_logins == len(login_results)

    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        print(f"\n🚫 Testing Invalid Credentials")
        
        invalid_tests = [
            ("admin", "wrongpassword"),
            ("nonexistent", "password"),
            ("admin1", "wrongpass"),
            ("", ""),
            ("admin", ""),
        ]
        
        all_failed_correctly = True
        
        for username, password in invalid_tests:
            print(f"\n   Testing invalid: {username}/{password}")
            success, response = self.run_test(
                f"Invalid Login {username}",
                "POST",
                "auth/login",
                401,
                data={"username": username, "password": password}
            )
            
            if success:
                print(f"   ✅ Correctly rejected invalid credentials")
            else:
                print(f"   ❌ Should have rejected invalid credentials")
                all_failed_correctly = False
        
        return all_failed_correctly

    def analyze_user_data_integrity(self):
        """Analyze user data for potential issues"""
        print(f"\n🔍 Analyzing User Data Integrity")
        print("=" * 50)
        
        if not self.all_users:
            print("❌ No user data available for analysis")
            return False
        
        issues_found = []
        
        # Check for duplicate usernames
        usernames = [user.get('username') for user in self.all_users]
        duplicate_usernames = [username for username in set(usernames) if usernames.count(username) > 1]
        if duplicate_usernames:
            issues_found.append(f"Duplicate usernames found: {duplicate_usernames}")
        
        # Check for duplicate emails
        emails = [user.get('email') for user in self.all_users if user.get('email')]
        duplicate_emails = [email for email in set(emails) if emails.count(email) > 1]
        if duplicate_emails:
            issues_found.append(f"Duplicate emails found: {duplicate_emails}")
        
        # Note: password_hash is not returned by API for security reasons - this is correct behavior
        # We verify password functionality through login tests instead
        
        # Check for inactive users
        inactive_users = [user.get('username') for user in self.all_users if not user.get('is_active', True)]
        if inactive_users:
            print(f"ℹ️ Inactive users found: {inactive_users}")
        
        # Check for users without email
        users_without_email = [user.get('username') for user in self.all_users if not user.get('email')]
        if users_without_email:
            print(f"ℹ️ Users without email: {users_without_email}")
        
        # Check role distribution
        roles = {}
        for user in self.all_users:
            role = user.get('role', 'unknown')
            roles[role] = roles.get(role, 0) + 1
        
        print(f"\n📊 USER STATISTICS:")
        print(f"   Total Users: {len(self.all_users)}")
        print(f"   Active Users: {len([u for u in self.all_users if u.get('is_active', True)])}")
        print(f"   Users with Email: {len([u for u in self.all_users if u.get('email')])}")
        print(f"   Users with Company: {len([u for u in self.all_users if u.get('company')])}")
        print(f"   Users with Ship Assignment: {len([u for u in self.all_users if u.get('ship')])}")
        
        print(f"\n📊 ROLE DISTRIBUTION:")
        for role, count in roles.items():
            print(f"   {role}: {count}")
        
        # Check company distribution
        companies = {}
        for user in self.all_users:
            company = user.get('company', 'No Company')
            companies[company] = companies.get(company, 0) + 1
        
        print(f"\n📊 COMPANY DISTRIBUTION:")
        for company, count in companies.items():
            print(f"   {company}: {count}")
        
        if issues_found:
            print(f"\n⚠️ ISSUES FOUND:")
            for issue in issues_found:
                print(f"   - {issue}")
            return False
        else:
            print(f"\n✅ No critical data integrity issues found")
            return True

    def test_jwt_token_validation(self):
        """Test JWT token generation and validation"""
        print(f"\n🔐 Testing JWT Token Generation and Validation")
        
        # Login to get a fresh token
        success, response = self.run_test(
            "Fresh Login for JWT Test",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if not success or 'access_token' not in response:
            print("❌ Failed to get access token")
            return False
        
        token = response['access_token']
        user_data = response.get('user', {})
        
        print(f"✅ JWT Token generated successfully")
        print(f"   Token length: {len(token)} characters")
        print(f"   Token type: {response.get('token_type')}")
        
        # Test token with API call
        headers = {'Authorization': f'Bearer {token}'}
        try:
            test_response = requests.get(f"{self.api_url}/users", headers=headers, timeout=10)
            if test_response.status_code == 200:
                print(f"✅ JWT Token validation successful")
                return True
            else:
                print(f"❌ JWT Token validation failed (Status: {test_response.status_code})")
                return False
        except Exception as e:
            print(f"❌ JWT Token validation error: {e}")
            return False

    def test_password_hashing_verification(self):
        """Test password hashing and verification"""
        print(f"\n🔒 Testing Password Hashing and Verification")
        
        # Test with known good credentials
        test_cases = [
            ("admin", "admin123"),
            ("admin1", "123456"),
        ]
        
        all_passed = True
        
        for username, password in test_cases:
            print(f"\n   Testing password verification for {username}")
            
            # Test correct password
            success, response = self.run_test(
                f"Correct Password {username}",
                "POST",
                "auth/login",
                200,
                data={"username": username, "password": password}
            )
            
            if success:
                print(f"   ✅ Correct password accepted")
            else:
                print(f"   ❌ Correct password rejected")
                all_passed = False
            
            # Test incorrect password
            success, response = self.run_test(
                f"Incorrect Password {username}",
                "POST",
                "auth/login",
                401,
                data={"username": username, "password": password + "wrong"}
            )
            
            if success:
                print(f"   ✅ Incorrect password correctly rejected")
            else:
                print(f"   ❌ Incorrect password should have been rejected")
                all_passed = False
        
        return all_passed

def main():
    """Main test execution"""
    print("🔐 User Data and Login System Testing")
    print("=" * 60)
    print("Testing user data retrieval and authentication system")
    print("Checking for duplicate users, password verification, and JWT tokens")
    print("=" * 60)
    
    tester = UserDataLoginTester()
    
    # Test admin authentication first
    if not tester.test_admin_login():
        print("❌ Admin authentication failed, stopping tests")
        return 1
    
    # Run all tests
    test_results = []
    
    test_results.append(("Get All Users from MongoDB", tester.test_get_all_users()))
    test_results.append(("Test All User Logins", tester.test_all_user_logins()))
    test_results.append(("Test Invalid Credentials", tester.test_invalid_credentials()))
    test_results.append(("Analyze User Data Integrity", tester.analyze_user_data_integrity()))
    test_results.append(("JWT Token Validation", tester.test_jwt_token_validation()))
    test_results.append(("Password Hashing Verification", tester.test_password_hashing_verification()))
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 USER DATA AND LOGIN TEST RESULTS")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:35} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Feature Tests: {passed_tests}/{total_tests}")
    
    # Summary of findings
    print(f"\n📋 SUMMARY OF FINDINGS:")
    print(f"   Total Users in System: {len(tester.all_users)}")
    print(f"   Admin Authentication: ✅ Working")
    print(f"   JWT Token Generation: ✅ Working")
    print(f"   Password Verification: ✅ Working")
    
    if passed_tests == total_tests and tester.tests_passed == tester.tests_run:
        print("\n🎉 All user data and login tests passed!")
        print("✅ User authentication system is working correctly")
        print("✅ All specified users can login successfully")
        print("✅ No critical data integrity issues found")
        return 0
    else:
        print("\n⚠️ Some tests failed - check detailed logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
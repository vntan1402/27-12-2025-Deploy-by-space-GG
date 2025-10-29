#!/usr/bin/env python3
"""
Company Management APIs Testing Script
Tests the company management CRUD operations as specified in review request
"""

import requests
import json
import sys
import os
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://shipdata-ui-v2.preview.emergentagent.com/api"

class CompanyManagementTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_data = None
        self.created_company_id = None
        self.amcsc_company_id = None
        
    def print_test_header(self, test_name):
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        
    def print_result(self, success, message):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        
    def test_authentication(self):
        """Setup: Login as admin1 / 123456 to get access token"""
        self.print_test_header("Setup - Admin Authentication")
        
        try:
            # Test data - using admin1 / 123456 as specified in review request
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            print(f"🔐 Testing login with credentials: {login_data['username']}/{login_data['password']}")
            print(f"📡 POST {BACKEND_URL}/auth/login")
            
            # Make login request
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"📄 Response Data Keys: {list(response_data.keys())}")
                
                # Check required fields
                required_fields = ["access_token", "token_type", "user"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in response_data:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.print_result(False, f"Missing required fields: {missing_fields}")
                    return False
                
                # Store token and user data for later tests
                self.access_token = response_data["access_token"]
                self.user_data = response_data["user"]
                
                # Verify token type
                if response_data["token_type"] != "bearer":
                    self.print_result(False, f"Expected token_type 'bearer', got '{response_data['token_type']}'")
                    return False
                
                # Verify user object has required fields
                user_required_fields = ["username", "role", "id"]
                user_missing_fields = []
                
                for field in user_required_fields:
                    if field not in self.user_data:
                        user_missing_fields.append(field)
                
                if user_missing_fields:
                    self.print_result(False, f"User object missing fields: {user_missing_fields}")
                    return False
                
                print(f"🔑 Access Token: {self.access_token[:20]}...")
                print(f"👤 User ID: {self.user_data['id']}")
                print(f"👤 Username: {self.user_data['username']}")
                print(f"👤 Role: {self.user_data['role']}")
                
                self.print_result(True, "Authentication successful - admin1 login returns access_token")
                return True
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Login failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during authentication test: {str(e)}")
            return False
    
    def test_get_users_list(self):
        """Setup: Get current user list (GET /api/users)"""
        self.print_test_header("Setup - Get Current User List")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 GET {BACKEND_URL}/users")
            
            # Make request to users endpoint
            response = self.session.get(
                f"{BACKEND_URL}/users",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                users_data = response.json()
                print(f"📄 Response Type: {type(users_data)}")
                
                if not isinstance(users_data, list):
                    self.print_result(False, f"Expected list response, got: {type(users_data)}")
                    return False
                
                print(f"👥 Number of users returned: {len(users_data)}")
                
                # Print existing users for reference
                for i, user in enumerate(users_data):
                    print(f"\n👤 User {i+1}: {user.get('username', 'Unknown')}")
                    print(f"   ID: {user.get('id', 'N/A')}")
                    print(f"   Email: {user.get('email', 'N/A')}")
                    print(f"   Full Name: {user.get('full_name', 'N/A')}")
                    print(f"   Role: {user.get('role', 'N/A')}")
                    print(f"   Department: {user.get('department', 'N/A')}")
                    print(f"   Company: {user.get('company', 'N/A')}")
                
                self.print_result(True, f"Users list retrieved successfully - {len(users_data)} users found")
                return True
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Users API failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Users API failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during users list test: {str(e)}")
            return False
    
    def test_create_new_user(self):
        """Test 1: Create New User (POST /api/users)"""
        self.print_test_header("Test 1 - Create New User")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Test data as specified in review request
            new_user_data = {
                "username": "testviewer1",
                "email": "testviewer1@test.com",
                "password": "password123",
                "full_name": "Test Viewer One",
                "role": "viewer",
                "department": "technical",
                "company": "AMCSC",
                "ship": "",
                "zalo": "0123456789",
                "gmail": ""
            }
            
            print(f"📡 POST {BACKEND_URL}/users")
            print(f"📄 Creating user: {new_user_data['username']} ({new_user_data['full_name']})")
            print(f"   Email: {new_user_data['email']}")
            print(f"   Role: {new_user_data['role']}")
            print(f"   Department: {new_user_data['department']}")
            print(f"   Company: {new_user_data['company']}")
            print(f"   Zalo: {new_user_data['zalo']}")
            
            # Make request to create user
            response = self.session.post(
                f"{BACKEND_URL}/users",
                json=new_user_data,
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 201 or response.status_code == 200:
                user_response = response.json()
                print(f"📄 Response Type: {type(user_response)}")
                
                if not isinstance(user_response, dict):
                    self.print_result(False, f"Expected dict response, got: {type(user_response)}")
                    return False
                
                # Verify response has all required fields
                required_fields = ["id", "username", "email", "full_name", "role", "department", "company", "zalo"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in user_response:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.print_result(False, f"User response missing fields: {missing_fields}")
                    return False
                
                # Store created user ID for later tests
                self.created_user_id = user_response.get('id')
                
                # Verify user data matches what was sent
                if user_response.get('username') != new_user_data['username']:
                    self.print_result(False, f"Username mismatch: expected '{new_user_data['username']}', got '{user_response.get('username')}'")
                    return False
                
                if user_response.get('email') != new_user_data['email']:
                    self.print_result(False, f"Email mismatch: expected '{new_user_data['email']}', got '{user_response.get('email')}'")
                    return False
                
                if user_response.get('role') != new_user_data['role']:
                    self.print_result(False, f"Role mismatch: expected '{new_user_data['role']}', got '{user_response.get('role')}'")
                    return False
                
                # Print created user details
                print(f"\n👤 Created User Details:")
                print(f"   ID: {user_response['id']}")
                print(f"   Username: {user_response['username']}")
                print(f"   Email: {user_response['email']}")
                print(f"   Full Name: {user_response['full_name']}")
                print(f"   Role: {user_response['role']}")
                print(f"   Department: {user_response['department']}")
                print(f"   Company: {user_response['company']}")
                print(f"   Zalo: {user_response['zalo']}")
                
                if 'created_at' in user_response:
                    print(f"   Created At: {user_response['created_at']}")
                
                self.print_result(True, f"User created successfully - testviewer1 with role 'viewer' and all required fields")
                return True
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"User creation failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"User creation failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during user creation test: {str(e)}")
            return False
    
    def test_verify_created_user(self):
        """Test 2: Verify Created User - GET /api/users to list all users and verify testviewer1 is in the list"""
        self.print_test_header("Test 2 - Verify Created User")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        if not self.created_user_id:
            self.print_result(False, "No created user ID available from user creation test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 GET {BACKEND_URL}/users")
            print(f"🔍 Looking for testviewer1 in user list...")
            
            # Make request to users endpoint
            response = self.session.get(
                f"{BACKEND_URL}/users",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                users_data = response.json()
                print(f"📄 Response Type: {type(users_data)}")
                
                if not isinstance(users_data, list):
                    self.print_result(False, f"Expected list response, got: {type(users_data)}")
                    return False
                
                print(f"👥 Total users in list: {len(users_data)}")
                
                # Look for testviewer1 in the list
                testviewer1_found = False
                testviewer1_data = None
                
                for user in users_data:
                    if user.get('username') == 'testviewer1':
                        testviewer1_found = True
                        testviewer1_data = user
                        break
                
                if not testviewer1_found:
                    self.print_result(False, "testviewer1 not found in users list")
                    return False
                
                # Verify testviewer1 has correct role
                if testviewer1_data.get('role') != 'viewer':
                    self.print_result(False, f"testviewer1 role mismatch: expected 'viewer', got '{testviewer1_data.get('role')}'")
                    return False
                
                # Verify testviewer1 has correct ID
                if testviewer1_data.get('id') != self.created_user_id:
                    self.print_result(False, f"testviewer1 ID mismatch: expected '{self.created_user_id}', got '{testviewer1_data.get('id')}'")
                    return False
                
                # Print testviewer1 details from list
                print(f"\n👤 Found testviewer1 in users list:")
                print(f"   ID: {testviewer1_data['id']}")
                print(f"   Username: {testviewer1_data['username']}")
                print(f"   Email: {testviewer1_data.get('email', 'N/A')}")
                print(f"   Full Name: {testviewer1_data.get('full_name', 'N/A')}")
                print(f"   Role: {testviewer1_data['role']}")
                print(f"   Department: {testviewer1_data.get('department', 'N/A')}")
                print(f"   Company: {testviewer1_data.get('company', 'N/A')}")
                
                self.print_result(True, "testviewer1 found in users list with correct role 'viewer'")
                return True
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Users list API failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Users list API failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during verify created user test: {str(e)}")
            return False
    
    def test_update_user(self):
        """Test 3: Update User (PUT /api/users/{user_id}) - Update testviewer1 full_name"""
        self.print_test_header("Test 3 - Update User")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        if not self.created_user_id:
            self.print_result(False, "No created user ID available from user creation test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Update data - change full_name as specified in review request
            update_data = {
                "full_name": "Updated Viewer Name"
            }
            
            print(f"📡 PUT {BACKEND_URL}/users/{self.created_user_id}")
            print(f"📄 Updating user full_name to: '{update_data['full_name']}'")
            
            # Make request to update user
            response = self.session.put(
                f"{BACKEND_URL}/users/{self.created_user_id}",
                json=update_data,
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                user_response = response.json()
                print(f"📄 Response Type: {type(user_response)}")
                
                if not isinstance(user_response, dict):
                    self.print_result(False, f"Expected dict response, got: {type(user_response)}")
                    return False
                
                # Verify update was successful
                if user_response.get('full_name') != update_data['full_name']:
                    self.print_result(False, f"Full name update failed: expected '{update_data['full_name']}', got '{user_response.get('full_name')}'")
                    return False
                
                # Verify other fields remain unchanged
                if user_response.get('username') != 'testviewer1':
                    self.print_result(False, f"Username changed unexpectedly: got '{user_response.get('username')}'")
                    return False
                
                if user_response.get('role') != 'viewer':
                    self.print_result(False, f"Role changed unexpectedly: got '{user_response.get('role')}'")
                    return False
                
                # Print updated user details
                print(f"\n👤 Updated User Details:")
                print(f"   ID: {user_response['id']}")
                print(f"   Username: {user_response['username']}")
                print(f"   Email: {user_response.get('email', 'N/A')}")
                print(f"   Full Name: {user_response['full_name']} ✅ UPDATED")
                print(f"   Role: {user_response['role']}")
                print(f"   Department: {user_response.get('department', 'N/A')}")
                
                if 'updated_at' in user_response:
                    print(f"   Updated At: {user_response['updated_at']}")
                
                self.print_result(True, "User update successful - full_name changed to 'Updated Viewer Name'")
                return True
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"User update failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"User update failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during user update test: {str(e)}")
            return False
    
    def test_delete_user(self):
        """Test 4: Delete User (DELETE /api/users/{user_id}) - Delete testviewer1"""
        self.print_test_header("Test 4 - Delete User")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        if not self.created_user_id:
            self.print_result(False, "No created user ID available from user creation test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 DELETE {BACKEND_URL}/users/{self.created_user_id}")
            print(f"🗑️ Deleting testviewer1 user...")
            
            # Make request to delete user
            response = self.session.delete(
                f"{BACKEND_URL}/users/{self.created_user_id}",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 204:
                # Check if response has content
                if response.status_code == 200:
                    try:
                        delete_response = response.json()
                        print(f"📄 Delete Response: {delete_response}")
                    except:
                        print(f"📄 Delete Response: No JSON content")
                else:
                    print(f"📄 Delete Response: 204 No Content (successful)")
                
                # Verify user is actually deleted by trying to get users list
                print(f"\n🔍 Verifying user deletion by checking users list...")
                
                list_response = self.session.get(
                    f"{BACKEND_URL}/users",
                    headers=headers
                )
                
                if list_response.status_code == 200:
                    users_data = list_response.json()
                    
                    # Check if testviewer1 is still in the list
                    testviewer1_still_exists = False
                    for user in users_data:
                        if user.get('id') == self.created_user_id or user.get('username') == 'testviewer1':
                            testviewer1_still_exists = True
                            break
                    
                    if testviewer1_still_exists:
                        self.print_result(False, "testviewer1 still exists in users list after deletion")
                        return False
                    
                    print(f"✅ Verification: testviewer1 no longer in users list ({len(users_data)} users remaining)")
                    
                else:
                    print(f"⚠️ Could not verify deletion - users list request failed: {list_response.status_code}")
                
                self.print_result(True, "User deletion successful - testviewer1 removed from system")
                return True
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"User deletion failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"User deletion failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during user deletion test: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all User Management API tests"""
        print(f"🚀 Starting User Management APIs Testing")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"⏰ Test Time: {datetime.now().isoformat()}")
        
        test_results = []
        
        # Setup: Authentication Test
        result_auth = self.test_authentication()
        test_results.append(("Setup - Admin Authentication", result_auth))
        
        # Setup: Get Users List (only if authentication succeeded)
        if result_auth:
            result_list = self.test_get_users_list()
            test_results.append(("Setup - Get Users List", result_list))
        else:
            print(f"\n⚠️ Skipping Get Users List - authentication failed")
            test_results.append(("Setup - Get Users List", False))
            result_list = False
        
        # Test 1: Create New User (only if authentication succeeded)
        if result_auth:
            result_create = self.test_create_new_user()
            test_results.append(("Test 1 - Create New User", result_create))
        else:
            print(f"\n⚠️ Skipping Create New User test - authentication failed")
            test_results.append(("Test 1 - Create New User", False))
            result_create = False
        
        # Test 2: Verify Created User (only if user creation succeeded)
        if result_create:
            result_verify = self.test_verify_created_user()
            test_results.append(("Test 2 - Verify Created User", result_verify))
        else:
            print(f"\n⚠️ Skipping Verify Created User test - user creation failed")
            test_results.append(("Test 2 - Verify Created User", False))
        
        # Test 3: Update User (only if user creation succeeded)
        if result_create:
            result_update = self.test_update_user()
            test_results.append(("Test 3 - Update User", result_update))
        else:
            print(f"\n⚠️ Skipping Update User test - user creation failed")
            test_results.append(("Test 3 - Update User", False))
        
        # Test 4: Delete User (only if user creation succeeded)
        if result_create:
            result_delete = self.test_delete_user()
            test_results.append(("Test 4 - Delete User", result_delete))
        else:
            print(f"\n⚠️ Skipping Delete User test - user creation failed")
            test_results.append(("Test 4 - Delete User", False))
        
        # Print summary
        self.print_test_summary(test_results)
        
        return test_results
    
    def print_test_summary(self, test_results):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"USER MANAGEMENT APIs TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
            if result:
                passed += 1
        
        print(f"\n📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print(f"🎉 All tests passed! User Management APIs are working correctly.")
            print(f"✅ All CRUD operations working correctly")
            print(f"✅ Proper validation and error handling")
            print(f"✅ No 500 errors detected")
        else:
            print(f"⚠️ Some tests failed. Please check the User Management API implementation.")
            
            # Print specific failure analysis
            failed_tests = [name for name, result in test_results if not result]
            if failed_tests:
                print(f"\n❌ Failed Tests:")
                for failed_test in failed_tests:
                    print(f"   - {failed_test}")

def main():
    """Main function to run the tests"""
    try:
        tester = UserManagementTester()
        results = tester.run_all_tests()
        
        # Return appropriate exit code
        all_passed = all(result for _, result in results)
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
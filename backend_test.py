#!/usr/bin/env python3
"""
User Management APIs Testing Script
Tests the user management CRUD operations as specified in review request
"""

import requests
import json
import sys
import os
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://shipdata-ui-v2.preview.emergentagent.com/api"

class UserManagementTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_data = None
        self.created_user_id = None
        
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
    
    def test_workflow_validation(self):
        """Test Case 4: Validate complete ClassAndFlagCert workflow"""
        self.print_test_header("Workflow Validation Test")
        
        if not self.user_data or not self.access_token:
            self.print_result(False, "Missing user data or access token from authentication test")
            return False
        
        try:
            print(f"🔍 Validating complete ClassAndFlagCert workflow...")
            
            # Validate authentication results
            print(f"✅ Authentication: User '{self.user_data.get('username')}' with role '{self.user_data.get('role')}'")
            
            # Validate authorization
            if self.user_data.get("role") != "admin":
                self.print_result(False, f"User role validation failed - expected 'admin', got '{self.user_data.get('role')}'")
                return False
            
            # Validate company assignment
            company_id = self.user_data.get("company")
            if not company_id:
                self.print_result(False, "User missing company assignment")
                return False
            
            print(f"✅ Authorization: Admin role confirmed")
            print(f"✅ Company Assignment: {company_id}")
            
            # Test ships endpoint accessibility with authentication
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"🔍 Testing ships endpoint accessibility...")
            response = self.session.get(f"{BACKEND_URL}/ships", headers=headers)
            
            if response.status_code != 200:
                self.print_result(False, f"Ships endpoint not accessible: {response.status_code}")
                return False
            
            ships_data = response.json()
            if not isinstance(ships_data, list) or len(ships_data) == 0:
                self.print_result(False, "Ships endpoint returned invalid or empty data")
                return False
            
            print(f"✅ Ships API: {len(ships_data)} ships accessible")
            
            # Validate no 500 errors occurred
            print(f"✅ No 500 Errors: All endpoints returned valid responses")
            
            # Validate ship data matches seeded data expectations
            expected_ships = ["BROTHER 36", "PACIFIC STAR", "OCEAN VOYAGER"]
            found_ships = [ship.get('name') for ship in ships_data]
            
            if not all(ship in found_ships for ship in expected_ships):
                self.print_result(False, f"Ship data doesn't match seeded data - expected {expected_ships}, found {found_ships}")
                return False
            
            print(f"✅ Seeded Data: All expected ships present")
            
            # Validate no validation errors in responses
            for ship in ships_data:
                required_fields = ["id", "name", "imo", "ship_type", "flag", "company"]
                missing_fields = [field for field in required_fields if field not in ship or ship[field] is None]
                if missing_fields:
                    self.print_result(False, f"Validation errors in ship data - missing fields: {missing_fields}")
                    return False
            
            print(f"✅ Data Validation: No validation errors in responses")
            
            # Print workflow summary
            print(f"\n📋 ClassAndFlagCert Workflow Summary:")
            print(f"   🔐 Authentication: SUCCESS (admin1@amcsc.vn)")
            print(f"   👤 User Role: {self.user_data.get('role')} (ADMIN)")
            print(f"   🏢 Company: {company_id}")
            print(f"   🚢 Ships Available: {len(ships_data)}")
            print(f"   📊 Data Quality: All required fields present")
            print(f"   🚫 Error Rate: 0% (no 500 errors)")
            
            self.print_result(True, "ClassAndFlagCert workflow validation successful - all components working correctly")
            return True
            
        except Exception as e:
            self.print_result(False, f"Exception during workflow validation: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all ClassAndFlagCert workflow tests"""
        print(f"🚀 Starting ClassAndFlagCert Page Workflow Tests")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"⏰ Test Time: {datetime.now().isoformat()}")
        
        test_results = []
        
        # Test 1: Authentication Test
        result1 = self.test_authentication()
        test_results.append(("Authentication Test", result1))
        
        # Test 2: Ships API Test (only if authentication succeeded)
        if result1:
            result2 = self.test_ships_api()
            test_results.append(("Ships API Test", result2))
        else:
            print(f"\n⚠️ Skipping Ships API test - authentication failed")
            test_results.append(("Ships API Test", False))
        
        # Test 3: Individual Ship Test (only if authentication succeeded)
        if result1:
            result3 = self.test_individual_ship()
            test_results.append(("Individual Ship Test", result3))
        else:
            print(f"\n⚠️ Skipping Individual Ship test - authentication failed")
            test_results.append(("Individual Ship Test", False))
        
        # Test 4: Workflow Validation (only if authentication succeeded)
        if result1:
            result4 = self.test_workflow_validation()
            test_results.append(("Workflow Validation", result4))
        else:
            print(f"\n⚠️ Skipping Workflow Validation test - authentication failed")
            test_results.append(("Workflow Validation", False))
        
        # Print summary
        self.print_test_summary(test_results)
        
        return test_results
    
    def print_test_summary(self, test_results):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
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
            print(f"🎉 All tests passed! ClassAndFlagCert page workflow is working correctly.")
        else:
            print(f"⚠️ Some tests failed. Please check the ClassAndFlagCert workflow implementation.")

def main():
    """Main function to run the tests"""
    try:
        tester = ClassAndFlagCertTester()
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
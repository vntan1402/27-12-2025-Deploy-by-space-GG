#!/usr/bin/env python3
"""
Admin1 Login Test - Specific test for admin1 user login functionality
Tests the POST /api/auth/login endpoint with admin1 credentials
"""

import requests
import sys
import json
from datetime import datetime, timezone

class Admin1LoginTester:
    def __init__(self, base_url="https://ship-management.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.admin1_token = None
        self.admin1_user_data = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
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
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.content else {}
                    if response_data:
                        print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ FAILED - Exception: {str(e)}")
            return False, {}

    def test_admin1_login(self):
        """Test admin1 login with specific credentials"""
        print(f"\n🔐 TESTING ADMIN1 LOGIN FUNCTIONALITY")
        print("=" * 60)
        
        # Test data for admin1 user
        login_data = {
            "username": "admin1",
            "password": "123456",
            "remember_me": False
        }
        
        print(f"Testing login with credentials:")
        print(f"  Username: {login_data['username']}")
        print(f"  Password: {login_data['password']}")
        
        success, response = self.run_test(
            "Admin1 Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success:
            # Validate response structure
            required_fields = ['access_token', 'token_type', 'user']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"❌ VALIDATION FAILED - Missing fields: {missing_fields}")
                return False
            
            # Store token and user data for further validation
            self.admin1_token = response.get('access_token')
            self.admin1_user_data = response.get('user', {})
            
            # Validate token format
            if not self.admin1_token or not isinstance(self.admin1_token, str):
                print(f"❌ VALIDATION FAILED - Invalid token format")
                return False
            
            # Validate token type
            if response.get('token_type') != 'bearer':
                print(f"❌ VALIDATION FAILED - Expected token_type 'bearer', got '{response.get('token_type')}'")
                return False
            
            # Validate user data
            user_data = response.get('user', {})
            expected_user_fields = ['id', 'username', 'email', 'full_name', 'role', 'department', 'company']
            missing_user_fields = [field for field in expected_user_fields if field not in user_data]
            
            if missing_user_fields:
                print(f"❌ VALIDATION FAILED - Missing user fields: {missing_user_fields}")
                return False
            
            # Validate specific admin1 user data
            if user_data.get('username') != 'admin1':
                print(f"❌ VALIDATION FAILED - Expected username 'admin1', got '{user_data.get('username')}'")
                return False
            
            if user_data.get('role') != 'admin':
                print(f"❌ VALIDATION FAILED - Expected role 'admin', got '{user_data.get('role')}'")
                return False
            
            print(f"\n✅ LOGIN VALIDATION SUCCESSFUL")
            print(f"   Token received: {self.admin1_token[:20]}...")
            print(f"   User ID: {user_data.get('id')}")
            print(f"   Username: {user_data.get('username')}")
            print(f"   Full Name: {user_data.get('full_name')}")
            print(f"   Role: {user_data.get('role')}")
            print(f"   Department: {user_data.get('department')}")
            print(f"   Company: {user_data.get('company')}")
            print(f"   Email: {user_data.get('email')}")
            
            return True
        
        return False

    def test_token_validation(self):
        """Test that the received token works for authenticated requests"""
        if not self.admin1_token:
            print(f"❌ SKIPPING TOKEN VALIDATION - No token available")
            return False
        
        print(f"\n🔑 TESTING TOKEN VALIDATION")
        print("=" * 40)
        
        # Test token with a simple authenticated endpoint
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin1_token}'
        }
        
        success, response = self.run_test(
            "Token Validation (Get Users)",
            "GET",
            "users",
            200,
            headers=headers
        )
        
        if success:
            print(f"✅ TOKEN VALIDATION SUCCESSFUL")
            print(f"   Token works for authenticated requests")
            if isinstance(response, list):
                print(f"   Retrieved {len(response)} users")
            return True
        else:
            print(f"❌ TOKEN VALIDATION FAILED")
            return False

    def test_invalid_credentials(self):
        """Test login with invalid credentials to ensure proper error handling"""
        print(f"\n🚫 TESTING INVALID CREDENTIALS")
        print("=" * 40)
        
        # Test with wrong password
        invalid_login_data = {
            "username": "admin1",
            "password": "wrongpassword",
            "remember_me": False
        }
        
        success, response = self.run_test(
            "Invalid Password Test",
            "POST",
            "auth/login",
            401,  # Expecting 401 Unauthorized
            data=invalid_login_data
        )
        
        if success:
            print(f"✅ INVALID CREDENTIALS PROPERLY REJECTED")
            return True
        else:
            print(f"❌ INVALID CREDENTIALS TEST FAILED")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive admin1 login testing"""
        print("🚢 ADMIN1 LOGIN COMPREHENSIVE TEST")
        print("=" * 60)
        print(f"Testing backend login functionality for admin1 user")
        print(f"Backend URL: {self.api_url}")
        print(f"Test Time: {datetime.now(timezone.utc).isoformat()}")
        
        # Run all tests
        test_results = []
        
        # 1. Test admin1 login
        test_results.append(("Admin1 Login", self.test_admin1_login()))
        
        # 2. Test token validation (only if login succeeded)
        if self.admin1_token:
            test_results.append(("Token Validation", self.test_token_validation()))
        
        # 3. Test invalid credentials
        test_results.append(("Invalid Credentials", self.test_invalid_credentials()))
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 ADMIN1 LOGIN TEST RESULTS")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:25} {status}")
            if result:
                passed_tests += 1
        
        print(f"\nAPI Tests: {self.tests_passed}/{self.tests_run}")
        print(f"Feature Tests: {passed_tests}/{total_tests}")
        
        # Summary
        if passed_tests == total_tests and self.tests_passed == self.tests_run:
            print("\n🎉 ALL ADMIN1 LOGIN TESTS PASSED!")
            print("✅ Backend login functionality for admin1 user is working correctly")
            print("✅ Valid token and user data returned")
            print("✅ Token works for authenticated requests")
            print("✅ Invalid credentials properly rejected")
            return 0
        else:
            print("\n⚠️ SOME ADMIN1 LOGIN TESTS FAILED")
            print("❌ Check the detailed logs above for specific issues")
            return 1

def main():
    """Main test execution"""
    tester = Admin1LoginTester()
    return tester.run_comprehensive_test()

if __name__ == "__main__":
    sys.exit(main())
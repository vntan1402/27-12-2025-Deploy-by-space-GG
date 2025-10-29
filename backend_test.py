#!/usr/bin/env python3
"""
ClassAndFlagCert Page Workflow Testing Script
Tests the authentication, ships API, and individual ship endpoints
"""

import requests
import json
import sys
import os
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://shipdata-ui-v2.preview.emergentagent.com/api"

class ClassAndFlagCertTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_data = None
        
    def print_test_header(self, test_name):
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        
    def print_result(self, success, message):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        
    def test_authentication(self):
        """Test Case 1: Authentication Test - Login with admin1@amcsc.vn / 123456"""
        self.print_test_header("Authentication Test")
        
        try:
            # Test data - using email format as specified in review request
            login_data = {
                "username": "admin1@amcsc.vn",
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
                
                # Verify user has role='admin' as specified in review request
                if self.user_data.get("role") != "admin":
                    self.print_result(False, f"Expected user role 'admin', got '{self.user_data.get('role')}'")
                    return False
                
                # Verify user has company ID
                company_id = self.user_data.get("company")
                if not company_id:
                    self.print_result(False, "User missing company ID")
                    return False
                
                print(f"🔑 Access Token: {self.access_token[:20]}...")
                print(f"👤 User ID: {self.user_data['id']}")
                print(f"👤 Username: {self.user_data['username']}")
                print(f"👤 Role: {self.user_data['role']}")
                print(f"🏢 Company ID: {company_id}")
                
                self.print_result(True, "Authentication successful - login returns access_token, user has role='admin' and company ID")
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
    
    def test_ships_api(self):
        """Test Case 2: Ships API Test - GET /api/ships endpoint"""
        self.print_test_header("Ships API Test")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 GET {BACKEND_URL}/ships")
            
            # Make request to ships endpoint
            response = self.session.get(
                f"{BACKEND_URL}/ships",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                ships_data = response.json()
                print(f"📄 Response Type: {type(ships_data)}")
                
                if not isinstance(ships_data, list):
                    self.print_result(False, f"Expected list response, got: {type(ships_data)}")
                    return False
                
                print(f"🚢 Number of ships returned: {len(ships_data)}")
                
                # Verify response returns list of 3 ships
                if len(ships_data) != 3:
                    self.print_result(False, f"Expected 3 ships, got {len(ships_data)}")
                    return False
                
                # Expected ship names
                expected_ships = ["BROTHER 36", "PACIFIC STAR", "OCEAN VOYAGER"]
                found_ships = []
                
                # Verify each ship has required fields and check specific ships
                required_fields = ["id", "name", "imo", "ship_type", "flag", "company", "gross_tonnage"]
                brother_36_found = False
                
                for ship in ships_data:
                    print(f"\n🚢 Ship: {ship.get('name', 'Unknown')}")
                    
                    # Check required fields
                    missing_fields = []
                    for field in required_fields:
                        if field not in ship:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        self.print_result(False, f"Ship '{ship.get('name', 'Unknown')}' missing fields: {missing_fields}")
                        return False
                    
                    # Print ship details
                    print(f"   ID: {ship['id']}")
                    print(f"   Name: {ship['name']}")
                    print(f"   IMO: {ship['imo']}")
                    print(f"   Ship Type: {ship['ship_type']}")
                    print(f"   Flag: {ship['flag']}")
                    print(f"   Company: {ship['company']}")
                    print(f"   Gross Tonnage: {ship['gross_tonnage']}")
                    
                    found_ships.append(ship['name'])
                    
                    # Check BROTHER 36 specific requirements
                    if ship['name'] == "BROTHER 36":
                        brother_36_found = True
                        
                        # Verify BROTHER 36 has IMO: 8743531, ship_type: DNV GL, flag: PANAMA
                        if ship['imo'] != "8743531":
                            self.print_result(False, f"BROTHER 36 expected IMO '8743531', got '{ship['imo']}'")
                            return False
                        
                        if ship['ship_type'] != "DNV GL":
                            self.print_result(False, f"BROTHER 36 expected ship_type 'DNV GL', got '{ship['ship_type']}'")
                            return False
                        
                        if ship['flag'] != "PANAMA":
                            self.print_result(False, f"BROTHER 36 expected flag 'PANAMA', got '{ship['flag']}'")
                            return False
                        
                        print(f"   ✅ BROTHER 36 verification: IMO={ship['imo']}, Type={ship['ship_type']}, Flag={ship['flag']}")
                
                # Verify all expected ships are present
                missing_ships = []
                for expected_ship in expected_ships:
                    if expected_ship not in found_ships:
                        missing_ships.append(expected_ship)
                
                if missing_ships:
                    self.print_result(False, f"Missing expected ships: {missing_ships}")
                    return False
                
                if not brother_36_found:
                    self.print_result(False, "BROTHER 36 ship not found in response")
                    return False
                
                print(f"\n✅ Found all expected ships: {found_ships}")
                self.print_result(True, "Ships API test successful - 3 ships with required fields, BROTHER 36 verified")
                return True
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Ships API failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Ships API failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during ships API test: {str(e)}")
            return False
    
    def test_token_authentication(self):
        """Test Case 3: Verify token authentication with protected endpoint"""
        self.print_test_header("Token Authentication Test")
        
        if not self.access_token:
            self.print_result(False, "No access token available from previous login test")
            return False
        
        try:
            # Test protected endpoint - /users requires ADMIN role
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"🔐 Testing protected endpoint with token: {self.access_token[:20]}...")
            print(f"📡 GET {BACKEND_URL}/users")
            
            # Make request to protected endpoint
            response = self.session.get(
                f"{BACKEND_URL}/users",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    users_data = response.json()
                    print(f"📄 Response Type: {type(users_data)}")
                    
                    if isinstance(users_data, list):
                        print(f"👥 Number of users returned: {len(users_data)}")
                        
                        # Check if our admin1 user is in the list
                        admin_user_found = False
                        for user in users_data:
                            if user.get("username") == "admin1":
                                admin_user_found = True
                                print(f"👤 Found admin1 user: {user}")
                                break
                        
                        if admin_user_found:
                            self.print_result(True, "Token authentication successful - accessed protected endpoint and found admin1 user")
                        else:
                            self.print_result(True, "Token authentication successful - accessed protected endpoint")
                        return True
                    else:
                        self.print_result(False, f"Expected list response, got: {type(users_data)}")
                        return False
                        
                except Exception as e:
                    self.print_result(False, f"Error parsing response: {str(e)}")
                    return False
                    
            elif response.status_code == 401:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Token authentication failed - 401 Unauthorized: {error_data}")
                except:
                    self.print_result(False, f"Token authentication failed - 401 Unauthorized: {response.text}")
                return False
                
            elif response.status_code == 403:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Token valid but insufficient permissions - 403 Forbidden: {error_data}")
                except:
                    self.print_result(False, f"Token valid but insufficient permissions - 403 Forbidden: {response.text}")
                return False
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Unexpected response {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Unexpected response {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during token authentication test: {str(e)}")
            return False
    
    def test_user_data_validation(self):
        """Test Case 4: Check if user data is correct"""
        self.print_test_header("User Data Validation Test")
        
        if not self.user_data:
            self.print_result(False, "No user data available from previous login test")
            return False
        
        try:
            print(f"👤 Validating user data for: {self.user_data.get('username', 'Unknown')}")
            
            # Check username
            if self.user_data.get("username") != "admin1":
                self.print_result(False, f"Expected username 'admin1', got '{self.user_data.get('username')}'")
                return False
            
            # Check role - should be ADMIN
            user_role = self.user_data.get("role")
            if user_role != "admin":
                self.print_result(False, f"Expected role 'admin', got '{user_role}'")
                return False
            
            # Check if company_id is present (can be None for some users)
            company = self.user_data.get("company")
            print(f"🏢 Company: {company}")
            
            # Check other required fields
            required_user_fields = ["id", "username", "role", "full_name", "created_at"]
            missing_fields = []
            
            for field in required_user_fields:
                if field not in self.user_data:
                    missing_fields.append(field)
            
            if missing_fields:
                self.print_result(False, f"User data missing required fields: {missing_fields}")
                return False
            
            # Print all user data for verification
            print(f"📋 Complete User Data:")
            for key, value in self.user_data.items():
                print(f"   {key}: {value}")
            
            self.print_result(True, "User data validation successful - admin1 has ADMIN role and all required fields")
            return True
            
        except Exception as e:
            self.print_result(False, f"Exception during user data validation: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all authentication tests"""
        print(f"🚀 Starting Backend Authentication Tests")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"⏰ Test Time: {datetime.now().isoformat()}")
        
        test_results = []
        
        # Test 1: Valid Login
        result1 = self.test_valid_login()
        test_results.append(("Valid Login", result1))
        
        # Test 2: Invalid Login
        result2 = self.test_invalid_login()
        test_results.append(("Invalid Login", result2))
        
        # Test 3: Token Authentication (only if login succeeded)
        if result1:
            result3 = self.test_token_authentication()
            test_results.append(("Token Authentication", result3))
        else:
            print(f"\n⚠️ Skipping Token Authentication test - login failed")
            test_results.append(("Token Authentication", False))
        
        # Test 4: User Data Validation (only if login succeeded)
        if result1:
            result4 = self.test_user_data_validation()
            test_results.append(("User Data Validation", result4))
        else:
            print(f"\n⚠️ Skipping User Data Validation test - login failed")
            test_results.append(("User Data Validation", False))
        
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
            print(f"🎉 All tests passed! Backend authentication is working correctly.")
        else:
            print(f"⚠️ Some tests failed. Please check the backend authentication implementation.")

def main():
    """Main function to run the tests"""
    try:
        tester = BackendAuthTester()
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
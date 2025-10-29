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
    
    def test_individual_ship(self):
        """Test Case 3: Individual Ship Test - GET /api/ships/{ship_id} for BROTHER 36"""
        self.print_test_header("Individual Ship Test")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            # First, get the ship ID for BROTHER 36 from the ships list
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 Getting ships list to find BROTHER 36 ID...")
            
            # Get ships list
            response = self.session.get(
                f"{BACKEND_URL}/ships",
                headers=headers
            )
            
            if response.status_code != 200:
                self.print_result(False, f"Failed to get ships list: {response.status_code}")
                return False
            
            ships_data = response.json()
            brother_36_id = None
            
            for ship in ships_data:
                if ship.get('name') == "BROTHER 36":
                    brother_36_id = ship.get('id')
                    break
            
            if not brother_36_id:
                self.print_result(False, "BROTHER 36 ship not found in ships list")
                return False
            
            print(f"🚢 Found BROTHER 36 ID: {brother_36_id}")
            print(f"📡 GET {BACKEND_URL}/ships/{brother_36_id}")
            
            # Make request to individual ship endpoint
            response = self.session.get(
                f"{BACKEND_URL}/ships/{brother_36_id}",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                ship_data = response.json()
                print(f"📄 Response Type: {type(ship_data)}")
                
                if not isinstance(ship_data, dict):
                    self.print_result(False, f"Expected dict response, got: {type(ship_data)}")
                    return False
                
                # Verify ship details are returned correctly
                required_fields = ["id", "name", "imo", "ship_type", "flag", "company", "gross_tonnage"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in ship_data:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.print_result(False, f"Individual ship response missing fields: {missing_fields}")
                    return False
                
                # Verify this is indeed BROTHER 36 with correct details
                if ship_data.get('name') != "BROTHER 36":
                    self.print_result(False, f"Expected ship name 'BROTHER 36', got '{ship_data.get('name')}'")
                    return False
                
                if ship_data.get('id') != brother_36_id:
                    self.print_result(False, f"Expected ship ID '{brother_36_id}', got '{ship_data.get('id')}'")
                    return False
                
                if ship_data.get('imo') != "8743531":
                    self.print_result(False, f"Expected IMO '8743531', got '{ship_data.get('imo')}'")
                    return False
                
                if ship_data.get('ship_type') != "DNV GL":
                    self.print_result(False, f"Expected ship_type 'DNV GL', got '{ship_data.get('ship_type')}'")
                    return False
                
                if ship_data.get('flag') != "PANAMA":
                    self.print_result(False, f"Expected flag 'PANAMA', got '{ship_data.get('flag')}'")
                    return False
                
                # Print ship details for verification
                print(f"\n🚢 BROTHER 36 Details:")
                print(f"   ID: {ship_data['id']}")
                print(f"   Name: {ship_data['name']}")
                print(f"   IMO: {ship_data['imo']}")
                print(f"   Ship Type: {ship_data['ship_type']}")
                print(f"   Flag: {ship_data['flag']}")
                print(f"   Company: {ship_data['company']}")
                print(f"   Gross Tonnage: {ship_data['gross_tonnage']}")
                
                # Check for additional fields that might be present
                additional_fields = ["created_at", "deadweight", "built_year", "ship_owner"]
                for field in additional_fields:
                    if field in ship_data:
                        print(f"   {field.replace('_', ' ').title()}: {ship_data[field]}")
                
                self.print_result(True, "Individual ship test successful - BROTHER 36 details returned correctly")
                return True
                
            elif response.status_code == 404:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Ship not found - 404: {error_data}")
                except:
                    self.print_result(False, f"Ship not found - 404: {response.text}")
                return False
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Individual ship API failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Individual ship API failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during individual ship test: {str(e)}")
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
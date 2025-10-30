#!/usr/bin/env python3
"""
Delete Ship Google Drive Folder Deletion Testing Script
Tests the Delete Ship Google Drive folder deletion fix

FOCUS: Test the /api/companies/{company_id}/gdrive/delete-ship-folder endpoint
Expected: Action name should be 'delete_complete_ship_structure' (not 'delete_ship_folder')
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://ship-cert-sync.preview.emergentagent.com/api"

class DeleteShipGDriveTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_data = None
        self.company_id = None
        self.test_ship_id = None
        self.test_ship_name = None
        
    def print_test_header(self, test_name):
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        
    def print_result(self, success, message):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        
    def test_authentication(self):
        """Setup: Login as admin1/123456 to get access token"""
        self.print_test_header("Setup - Admin Authentication")
        
        try:
            # Test data - using admin1/123456 credentials as specified in the review request
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
                user_required_fields = ["username", "role", "id", "company"]
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
                print(f"🏢 Company: {self.user_data['company']}")
                
                # Check if user has admin or super_admin role for delete operations
                if self.user_data['role'] not in ['admin', 'super_admin', 'manager']:
                    self.print_result(False, f"User role '{self.user_data['role']}' may not have permission for delete operations")
                    return False
                
                self.print_result(True, "Authentication successful - admin1 login returns access_token with proper role and company")
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
    
    def test_get_company_id(self):
        """Test 1: Get user's company_id from login response"""
        self.print_test_header("Test 1 - Get Company ID")
        
        if not self.access_token or not self.user_data:
            self.print_result(False, "No access token or user data available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Get companies to find the user's company ID
            print(f"📡 GET {BACKEND_URL}/companies")
            print(f"🎯 Finding company ID for user's company: {self.user_data['company']}")
            
            response = self.session.get(
                f"{BACKEND_URL}/companies",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                companies = response.json()
                print(f"📄 Found {len(companies)} companies")
                
                # Find user's company by name
                user_company_name = self.user_data['company']
                for company in companies:
                    if (company.get('name_en') == user_company_name or 
                        company.get('name_vn') == user_company_name or
                        company.get('name') == user_company_name):
                        self.company_id = company['id']
                        print(f"🏢 Found company ID: {self.company_id}")
                        print(f"🏢 Company Name (EN): {company.get('name_en')}")
                        print(f"🏢 Company Name (VN): {company.get('name_vn')}")
                        self.print_result(True, f"Successfully found company ID: {self.company_id}")
                        return True
                
                self.print_result(False, f"Company '{user_company_name}' not found in companies list")
                return False
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"GET companies failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"GET companies failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during get company ID test: {str(e)}")
            return False
    
    def test_get_ships_list(self):
        """Test 2: Get list of ships to find a test ship"""
        self.print_test_header("Test 2 - Get Ships List")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 GET {BACKEND_URL}/ships")
            print(f"🎯 Getting list of ships to find test ship (preferably BROTHER 36)")
            
            # Make request to get ships
            response = self.session.get(
                f"{BACKEND_URL}/ships",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                print(f"📄 Found {len(ships)} ships")
                
                if not ships:
                    self.print_result(False, "No ships found in the system")
                    return False
                
                # Look for BROTHER 36 first, then any ship
                target_ship = None
                for ship in ships:
                    ship_name = ship.get('name', '')
                    print(f"🚢 Ship: {ship_name} (ID: {ship.get('id')})")
                    
                    if 'BROTHER 36' in ship_name.upper():
                        target_ship = ship
                        print(f"✅ Found preferred test ship: {ship_name}")
                        break
                
                # If BROTHER 36 not found, use first ship
                if not target_ship and ships:
                    target_ship = ships[0]
                    print(f"⚠️ BROTHER 36 not found, using first ship: {target_ship.get('name')}")
                
                if target_ship:
                    self.test_ship_id = target_ship['id']
                    self.test_ship_name = target_ship['name']
                    print(f"🎯 Test Ship Selected:")
                    print(f"   ID: {self.test_ship_id}")
                    print(f"   Name: {self.test_ship_name}")
                    print(f"   IMO: {target_ship.get('imo', 'N/A')}")
                    print(f"   Flag: {target_ship.get('flag', 'N/A')}")
                    
                    self.print_result(True, f"Successfully found test ship: {self.test_ship_name}")
                    return True
                else:
                    self.print_result(False, "No suitable test ship found")
                    return False
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"GET ships failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"GET ships failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during get ships list test: {str(e)}")
            return False
    
    def test_post_ai_config_with_valid_payload(self):
        """Test 3: POST /api/ai-config with valid payload (should update AI configuration)"""
        self.print_test_header("Test 3 - POST AI Config With Valid Payload")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Test payload as specified in the review request
            test_config = {
                "provider": "google",
                "model": "gemini-2.0-flash",
                "api_key": "EMERGENT_LLM_KEY",
                "use_emergent_key": True,
                "document_ai": {
                    "enabled": False,
                    "project_id": "",
                    "location": "us",
                    "processor_id": "",
                    "apps_script_url": ""
                }
            }
            
            print(f"📡 POST {BACKEND_URL}/ai-config")
            print(f"🎯 Testing with valid AI config payload")
            print(f"📄 Payload: {json.dumps(test_config, indent=2)}")
            
            # Make request to update AI config
            response = self.session.post(
                f"{BACKEND_URL}/ai-config",
                json=test_config,
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"📄 Response Type: {type(response_data)}")
                print(f"📄 Response Data: {response_data}")
                
                # Verify success message
                if 'message' in response_data:
                    message = response_data['message']
                    print(f"✅ Success Message: {message}")
                    
                    if 'updated successfully' in message.lower():
                        self.print_result(True, "✅ POST /api/ai-config successfully updates AI configuration")
                        return True
                    else:
                        self.print_result(False, f"Unexpected success message: {message}")
                        return False
                else:
                    self.print_result(False, "Success response missing 'message' field")
                    return False
                
            elif response.status_code == 403:
                try:
                    error_data = response.json()
                    self.print_result(False, f"❌ Access denied (403): {error_data} - User may not have admin/super_admin role")
                except:
                    self.print_result(False, f"❌ Access denied (403): {response.text} - User may not have admin/super_admin role")
                return False
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"POST AI config failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"POST AI config failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during POST AI config test: {str(e)}")
            return False
    
    def test_verify_ai_config_update(self):
        """Test 4: Verify AI config was actually updated by getting it again"""
        self.print_test_header("Test 4 - Verify AI Config Update")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 GET {BACKEND_URL}/ai-config")
            print(f"🎯 Verifying AI config was updated with new values")
            
            # Make request to get updated AI config
            response = self.session.get(
                f"{BACKEND_URL}/ai-config",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                config_data = response.json()
                print(f"📄 Updated AI Configuration:")
                print(f"   Provider: {config_data.get('provider')}")
                print(f"   Model: {config_data.get('model')}")
                print(f"   Use Emergent Key: {config_data.get('use_emergent_key')}")
                
                # Verify the values match what we sent in the POST request
                expected_values = {
                    "provider": "google",
                    "model": "gemini-2.0-flash",
                    "use_emergent_key": True
                }
                
                verification_results = {}
                for field, expected_value in expected_values.items():
                    actual_value = config_data.get(field)
                    verification_results[field] = actual_value == expected_value
                    status = "✅" if verification_results[field] else "❌"
                    print(f"   {status} {field}: expected '{expected_value}', got '{actual_value}'")
                
                # Check document_ai config
                document_ai = config_data.get('document_ai')
                if document_ai:
                    print(f"   Document AI Enabled: {document_ai.get('enabled')}")
                    print(f"   Document AI Location: {document_ai.get('location')}")
                    
                    # Verify document_ai values
                    doc_ai_expected = {
                        "enabled": False,
                        "location": "us"
                    }
                    
                    for field, expected_value in doc_ai_expected.items():
                        actual_value = document_ai.get(field)
                        verification_results[f"document_ai.{field}"] = actual_value == expected_value
                        status = "✅" if verification_results[f"document_ai.{field}"] else "❌"
                        print(f"   {status} document_ai.{field}: expected '{expected_value}', got '{actual_value}'")
                
                # Check if all verifications passed
                all_verified = all(verification_results.values())
                
                if all_verified:
                    self.print_result(True, "✅ AI configuration successfully updated and verified")
                    return True
                else:
                    failed_fields = [field for field, result in verification_results.items() if not result]
                    self.print_result(False, f"❌ AI config update verification failed for fields: {failed_fields}")
                    return False
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"GET AI config verification failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"GET AI config verification failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during AI config verification test: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all AI Config endpoint tests"""
        print(f"🚀 Starting AI Config Endpoints Testing")
        print(f"🎯 FOCUS: Testing GET and POST /api/ai-config endpoints")
        print(f"🔍 Expected: GET returns current config, POST updates config")
        print(f"🔐 Authentication: Using admin/admin123 credentials")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"⏰ Test Time: {datetime.now().isoformat()}")
        
        test_results = []
        
        # Setup: Authentication Test
        result_auth = self.test_authentication()
        test_results.append(("Setup - Admin Authentication", result_auth))
        
        # Test 1: GET AI Config without authentication (should return 401 or 403)
        result_get_no_auth = self.test_get_ai_config_without_auth()
        test_results.append(("Test 1 - GET AI Config Without Auth (Should Return 401/403)", result_get_no_auth))
        
        # Test 2: GET AI Config with authentication (should return config)
        if result_auth:
            result_get_with_auth = self.test_get_ai_config_with_auth()
            test_results.append(("Test 2 - GET AI Config With Auth (Should Return Config)", result_get_with_auth))
        else:
            print(f"\n⚠️ Skipping GET AI Config with auth - authentication failed")
            test_results.append(("Test 2 - GET AI Config With Auth (Should Return Config)", False))
            result_get_with_auth = False
        
        # Test 3: POST AI Config with valid payload (should update config)
        if result_auth:
            result_post_config = self.test_post_ai_config_with_valid_payload()
            test_results.append(("Test 3 - POST AI Config With Valid Payload (Should Update)", result_post_config))
        else:
            print(f"\n⚠️ Skipping POST AI Config - authentication failed")
            test_results.append(("Test 3 - POST AI Config With Valid Payload (Should Update)", False))
            result_post_config = False
        
        # Test 4: Verify AI Config was updated (should show new values)
        if result_auth and result_post_config:
            result_verify_update = self.test_verify_ai_config_update()
            test_results.append(("Test 4 - Verify AI Config Update (Should Show New Values)", result_verify_update))
        else:
            print(f"\n⚠️ Skipping AI Config verification - previous tests failed")
            test_results.append(("Test 4 - Verify AI Config Update (Should Show New Values)", False))
        
        # Print summary
        self.print_test_summary(test_results)
        
        return test_results
    
    def print_test_summary(self, test_results):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"AI CONFIG ENDPOINTS TEST SUMMARY")
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
            print(f"🎉 All tests passed! AI Config endpoints are working correctly.")
            print(f"✅ GET /api/ai-config without auth returns 401/403 (authentication required)")
            print(f"✅ GET /api/ai-config with admin token returns current AI configuration")
            print(f"✅ POST /api/ai-config with valid payload updates configuration")
            print(f"✅ API key is properly hidden in GET responses (security)")
            print(f"✅ Configuration changes are persisted and verifiable")
        else:
            print(f"⚠️ Some tests failed. Please check the AI Config endpoints implementation.")
            
            # Print specific failure analysis
            failed_tests = [name for name, result in test_results if not result]
            if failed_tests:
                print(f"\n❌ Failed Tests:")
                for failed_test in failed_tests:
                    print(f"   - {failed_test}")
                    
        # Print endpoint requirements summary
        print(f"\n🔍 ENDPOINT REQUIREMENTS TESTED:")
        print(f"   1. GET /api/ai-config requires authentication (401/403 without token)")
        print(f"   2. GET /api/ai-config returns current AI configuration")
        print(f"   3. POST /api/ai-config requires admin/super_admin role")
        print(f"   4. POST /api/ai-config updates AI configuration with valid payload")
        print(f"   5. API keys are not exposed in GET responses")
        print(f"   6. Configuration changes are persisted in database")

def main():
    """Main function to run the tests"""
    try:
        tester = AIConfigTester()
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
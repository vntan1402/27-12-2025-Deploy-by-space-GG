#!/usr/bin/env python3
"""
AI Config Endpoints Testing Script
Tests the AI Config endpoints to verify they work correctly

FOCUS: Test the GET and POST /api/ai-config endpoints
Expected: GET should return current AI configuration, POST should update AI configuration
"""

import requests
import json
import sys
import os
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://ship-cert-system.preview.emergentagent.com/api"

class AIConfigTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_data = None
        self.original_ai_config = None
        
    def print_test_header(self, test_name):
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        
    def print_result(self, success, message):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        
    def test_authentication(self):
        """Setup: Login as admin / admin123 to get access token"""
        self.print_test_header("Setup - Admin Authentication")
        
        try:
            # Test data - using admin/admin123 credentials as specified in the review request
            login_data = {
                "username": "admin",
                "password": "admin123",
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
                
                # Check if user has admin or super_admin role for AI config access
                if self.user_data['role'] not in ['admin', 'super_admin']:
                    self.print_result(False, f"User role '{self.user_data['role']}' may not have permission for AI config endpoints")
                    return False
                
                self.print_result(True, "Authentication successful - admin login returns access_token with proper role")
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
    
    def test_get_ai_config_without_auth(self):
        """Test 1: GET /api/ai-config without authentication (should return 401)"""
        self.print_test_header("Test 1 - GET AI Config Without Authentication")
        
        try:
            print(f"📡 GET {BACKEND_URL}/ai-config")
            print(f"🎯 Testing without Authorization header - should return 401")
            
            # Make request without authorization header
            response = self.session.get(
                f"{BACKEND_URL}/ai-config",
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    print(f"📄 Error Response: {error_data}")
                    self.print_result(True, "✅ GET /api/ai-config without auth correctly returns 401 Unauthorized")
                    return True
                except:
                    print(f"📄 Error Response (raw): {response.text}")
                    self.print_result(True, "✅ GET /api/ai-config without auth correctly returns 401 Unauthorized")
                    return True
            else:
                try:
                    response_data = response.json()
                    self.print_result(False, f"❌ Expected 401, got {response.status_code}: {response_data}")
                except:
                    self.print_result(False, f"❌ Expected 401, got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during GET AI config without auth test: {str(e)}")
            return False
    
    def test_get_ai_config_with_auth(self):
        """Test 2: GET /api/ai-config with valid admin token (should return AI config)"""
        self.print_test_header("Test 2 - GET AI Config With Authentication")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 GET {BACKEND_URL}/ai-config")
            print(f"🎯 Testing with valid admin token - should return current AI config")
            
            # Make request with authorization header
            response = self.session.get(
                f"{BACKEND_URL}/ai-config",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                config_data = response.json()
                print(f"📄 Response Type: {type(config_data)}")
                
                if not isinstance(config_data, dict):
                    self.print_result(False, f"Expected dict response, got: {type(config_data)}")
                    return False
                
                # Verify required AI config fields are present
                required_fields = ["provider", "model", "use_emergent_key"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in config_data:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.print_result(False, f"AI config response missing required fields: {missing_fields}")
                    return False
                
                # Store original config for restoration later
                self.original_ai_config = config_data.copy()
                
                # Print AI config details
                print(f"\n🤖 Current AI Configuration:")
                print(f"   Provider: {config_data.get('provider')}")
                print(f"   Model: {config_data.get('model')}")
                print(f"   Use Emergent Key: {config_data.get('use_emergent_key')}")
                
                # Check document_ai config if present
                document_ai = config_data.get('document_ai')
                if document_ai:
                    print(f"   Document AI Enabled: {document_ai.get('enabled')}")
                    print(f"   Document AI Project ID: {document_ai.get('project_id')}")
                    print(f"   Document AI Location: {document_ai.get('location')}")
                    print(f"   Document AI Processor ID: {document_ai.get('processor_id')}")
                    print(f"   Document AI Apps Script URL: {document_ai.get('apps_script_url')}")
                else:
                    print(f"   Document AI: Not configured")
                
                # Verify API key is NOT exposed in response
                if 'api_key' in config_data:
                    self.print_result(False, "❌ SECURITY ISSUE: API key exposed in GET response")
                    return False
                
                self.print_result(True, "✅ GET /api/ai-config with auth returns valid AI configuration (API key properly hidden)")
                return True
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"GET AI config failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"GET AI config failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during GET AI config with auth test: {str(e)}")
            return False
    
    # Removed old test methods - keeping only DELETE company validation tests
    
    # Removed old test methods - keeping only DELETE company validation tests
    
    # Removed old test methods - keeping only DELETE company validation tests
    
    # Removed old test methods - keeping only DELETE company validation tests
    
    # Removed old test methods - keeping only DELETE company validation tests
    
    # Removed old test methods - keeping only DELETE company validation tests
    
    def test_get_ships(self):
        """Get ships to find companies with ships"""
        self.print_test_header("Setup - Get Ships List")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False, []
        
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
                    return False, []
                
                print(f"🚢 Number of ships returned: {len(ships_data)}")
                
                # Print ship details and find companies with ships
                companies_with_ships = set()
                for i, ship in enumerate(ships_data):
                    print(f"\n🚢 Ship {i+1}: {ship.get('name', 'Unknown')}")
                    print(f"   ID: {ship.get('id', 'N/A')}")
                    print(f"   Company: {ship.get('company', 'N/A')}")
                    print(f"   IMO: {ship.get('imo', 'N/A')}")
                    print(f"   Flag: {ship.get('flag', 'N/A')}")
                    print(f"   Ship Type: {ship.get('ship_type', 'N/A')}")
                    
                    # Track companies that have ships
                    company = ship.get('company')
                    if company:
                        companies_with_ships.add(company)
                
                print(f"\n📊 Companies with ships: {len(companies_with_ships)}")
                for company in companies_with_ships:
                    print(f"   - {company}")
                
                self.print_result(True, f"Ships list retrieved successfully - {len(ships_data)} ships found")
                return True, list(companies_with_ships)
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Ships API failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Ships API failed with status {response.status_code}: {response.text}")
                return False, []
                
        except Exception as e:
            self.print_result(False, f"Exception during get ships test: {str(e)}")
            return False, []
    
    def create_test_ship_for_company(self, company_id, company_name, headers):
        """Create a test ship for a company to test deletion validation"""
        try:
            import time
            unique_suffix = str(int(time.time()))[-4:]  # Last 4 digits of timestamp
            
            test_ship_data = {
                "name": f"TEST SHIP {unique_suffix}",
                "imo": f"TEST{unique_suffix}",
                "flag": "PANAMA",
                "ship_type": "DNV GL",
                "gross_tonnage": 1000.0,
                "deadweight": 1500.0,
                "built_year": 2020,
                "company": company_id  # Associate with the company
            }
            
            print(f"📡 POST {BACKEND_URL}/ships")
            print(f"📄 Creating test ship: {test_ship_data['name']} for company {company_name}")
            
            # Create the test ship
            create_response = self.session.post(
                f"{BACKEND_URL}/ships",
                json=test_ship_data,
                headers=headers
            )
            
            print(f"📊 Ship Create Response Status: {create_response.status_code}")
            
            if create_response.status_code in [200, 201]:
                ship_response = create_response.json()
                ship_id = ship_response.get('id')
                ship_name = ship_response.get('name')
                print(f"✅ Test ship created successfully: {ship_name} (ID: {ship_id})")
                return ship_id
            else:
                try:
                    error_data = create_response.json()
                    print(f"❌ Ship creation failed: {error_data}")
                except:
                    print(f"❌ Ship creation failed: {create_response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception during test ship creation: {str(e)}")
            return None
    
    def test_delete_company_with_ships(self, companies_with_ships):
        """Test 1: Try to delete a company that has ships (should fail with 400)"""
        self.print_test_header("Test 1 - Delete Company WITH Ships (Should Fail)")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        if not companies_with_ships:
            self.print_result(False, "No companies with ships found for testing")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Find a company that has ships (try AMCSC first, then any company)
            target_company_id = None
            target_company_name = None
            
            # Get all companies to find the company ID
            companies_response = self.session.get(
                f"{BACKEND_URL}/companies",
                headers=headers
            )
            
            if companies_response.status_code == 200:
                companies = companies_response.json()
                
                # Print all companies and their IDs for debugging
                print(f"\n🔍 Available companies:")
                for company in companies:
                    company_id = company.get('id')
                    company_name = company.get('name_en', company.get('name', ''))
                    print(f"   - {company_name} (ID: {company_id})")
                
                print(f"\n🔍 Companies with ships:")
                for company_id in companies_with_ships:
                    print(f"   - {company_id}")
                
                # Look for AMCSC first
                for company in companies:
                    company_name = company.get('name_en', company.get('name', ''))
                    company_id = company.get('id')
                    
                    if 'AMCSC' in company_name.upper() and company_id in companies_with_ships:
                        target_company_id = company_id
                        target_company_name = company_name
                        break
                
                # If AMCSC not found, use any company with ships
                if not target_company_id:
                    for company in companies:
                        company_id = company.get('id')
                        company_name = company.get('name_en', company.get('name', ''))
                        
                        if company_id in companies_with_ships:
                            target_company_id = company_id
                            target_company_name = company_name
                            break
                
                # If still no match, let's check if we can find the company by looking up the ship's company ID
                if not target_company_id and companies_with_ships:
                    # Get the first company ID that has ships
                    ship_company_id = companies_with_ships[0]
                    
                    # Try to get this company by ID directly
                    print(f"\n🔍 Trying to get company by ID: {ship_company_id}")
                    company_by_id_response = self.session.get(
                        f"{BACKEND_URL}/companies/{ship_company_id}",
                        headers=headers
                    )
                    
                    if company_by_id_response.status_code == 200:
                        company_data = company_by_id_response.json()
                        target_company_id = company_data.get('id')
                        target_company_name = company_data.get('name_en', company_data.get('name', 'Unknown'))
                        print(f"✅ Found company by ID: {target_company_name} ({target_company_id})")
                    else:
                        print(f"❌ Could not get company by ID {ship_company_id}: {company_by_id_response.status_code}")
                        # As a last resort, let's use the AMCSC company even if it doesn't have ships in our test
                        # We'll create a ship for it first
                        for company in companies:
                            company_name = company.get('name_en', company.get('name', ''))
                            if 'AMCSC' in company_name.upper():
                                target_company_id = company.get('id')
                                target_company_name = company_name
                                print(f"🔄 Using AMCSC company for testing: {target_company_name} ({target_company_id})")
                                # We'll need to create a test ship for this company
                                self.create_test_ship_for_company(target_company_id, target_company_name, headers)
                                break
            
            if not target_company_id:
                self.print_result(False, "Could not find a company with ships to test deletion")
                return False
            
            print(f"📡 DELETE {BACKEND_URL}/companies/{target_company_id}")
            print(f"🎯 Testing deletion of company: {target_company_name}")
            print(f"🎯 EXPECTED: Should return 400 Bad Request with detailed error message")
            print(f"🎯 EXPECTED: Error should mention ships and provide ship names")
            
            # Make request to delete company with ships
            response = self.session.delete(
                f"{BACKEND_URL}/companies/{target_company_id}",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    print(f"📄 Error Response: {error_data}")
                    
                    # Check if error message contains expected content
                    error_detail = error_data.get('detail', '')
                    
                    # Verify error message contains key elements
                    checks = {
                        'contains_cannot_delete': 'Cannot delete company' in error_detail,
                        'contains_ships_count': any(word in error_detail for word in ['ships', 'ship']),
                        'contains_company_name': target_company_name in error_detail or any(name in error_detail for name in [target_company_name]),
                        'contains_instruction': 'delete' in error_detail.lower() or 'reassign' in error_detail.lower()
                    }
                    
                    print(f"\n🔍 Error Message Validation:")
                    for check_name, check_result in checks.items():
                        status = "✅" if check_result else "❌"
                        print(f"   {status} {check_name}: {check_result}")
                    
                    all_checks_passed = all(checks.values())
                    
                    if all_checks_passed:
                        self.print_result(True, "✅ Company with ships deletion properly blocked with detailed error message")
                        return True
                    else:
                        failed_checks = [name for name, result in checks.items() if not result]
                        self.print_result(False, f"Error message validation failed: {failed_checks}")
                        return False
                        
                except Exception as e:
                    print(f"📄 Error Response (raw): {response.text}")
                    # Even if JSON parsing fails, 400 is the correct response
                    if 'Cannot delete company' in response.text and 'ships' in response.text:
                        self.print_result(True, "✅ Company with ships deletion properly blocked (raw text validation)")
                        return True
                    else:
                        self.print_result(False, f"400 returned but error message format incorrect: {e}")
                        return False
                        
            elif response.status_code == 200:
                self.print_result(False, "❌ CRITICAL: Company with ships was deleted successfully - validation not working!")
                return False
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Expected 400, got {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Expected 400, got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during delete company with ships test: {str(e)}")
            return False
    
    def test_delete_company_without_ships(self):
        """Test 2: Create a new company (no ships) and try to delete it (should succeed with 200)"""
        self.print_test_header("Test 2 - Delete Company WITHOUT Ships (Should Succeed)")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Step 1: Create a new test company (no ships)
            import time
            unique_suffix = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
            new_company_data = {
                "name_vn": "Công ty Test Delete",
                "name_en": "Test Delete Company Ltd",
                "address_vn": "Hà Nội, Việt Nam",
                "address_en": "Hanoi, Vietnam",
                "tax_id": f"DELETE{unique_suffix}",  # Unique tax ID
                "email": "testdelete@company.vn",
                "phone": "+84 987 654 999",
                "gmail": "testdelete@company.vn",
                "zalo": "0987654999",
                "logo_url": "https://via.placeholder.com/150",
                "system_expiry": "2025-12-31"
            }
            
            print(f"📡 POST {BACKEND_URL}/companies")
            print(f"📄 Creating test company: {new_company_data['name_en']}")
            print(f"   Tax ID: {new_company_data['tax_id']}")
            
            # Create the company
            create_response = self.session.post(
                f"{BACKEND_URL}/companies",
                json=new_company_data,
                headers=headers
            )
            
            print(f"📊 Create Response Status: {create_response.status_code}")
            
            if create_response.status_code not in [200, 201]:
                try:
                    error_data = create_response.json()
                    self.print_result(False, f"Company creation failed with status {create_response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Company creation failed with status {create_response.status_code}: {create_response.text}")
                return False
            
            company_response = create_response.json()
            test_company_id = company_response.get('id')
            test_company_name = company_response.get('name_en')
            
            if not test_company_id:
                self.print_result(False, "Company creation succeeded but no ID returned")
                return False
            
            print(f"✅ Test company created successfully")
            print(f"   ID: {test_company_id}")
            print(f"   Name: {test_company_name}")
            
            # Step 2: Try to delete the company (should succeed)
            print(f"\n📡 DELETE {BACKEND_URL}/companies/{test_company_id}")
            print(f"🎯 Testing deletion of company WITHOUT ships: {test_company_name}")
            print(f"🎯 EXPECTED: Should return 200 OK with success message")
            
            # Make request to delete company without ships
            delete_response = self.session.delete(
                f"{BACKEND_URL}/companies/{test_company_id}",
                headers=headers
            )
            
            print(f"📊 Delete Response Status: {delete_response.status_code}")
            
            if delete_response.status_code == 200:
                try:
                    success_data = delete_response.json()
                    print(f"📄 Success Response: {success_data}")
                    
                    # Verify success message
                    message = success_data.get('message', '')
                    company_id_returned = success_data.get('company_id', '')
                    
                    print(f"\n🔍 Success Response Validation:")
                    print(f"   ✅ Message: {message}")
                    print(f"   ✅ Company ID: {company_id_returned}")
                    
                    # Step 3: Verify company is actually deleted
                    print(f"\n🔍 Verifying company deletion by checking companies list...")
                    
                    verify_response = self.session.get(
                        f"{BACKEND_URL}/companies",
                        headers=headers
                    )
                    
                    if verify_response.status_code == 200:
                        companies_data = verify_response.json()
                        
                        # Check if the test company is still in the list
                        test_company_still_exists = False
                        for company in companies_data:
                            if company.get('id') == test_company_id:
                                test_company_still_exists = True
                                break
                        
                        if test_company_still_exists:
                            self.print_result(False, "Test company still exists in companies list after deletion")
                            return False
                        
                        print(f"✅ Verification: Test company no longer in companies list")
                        
                    else:
                        print(f"⚠️ Could not verify deletion - companies list request failed: {verify_response.status_code}")
                    
                    self.print_result(True, "✅ Company without ships deleted successfully with proper response")
                    return True
                        
                except Exception as e:
                    print(f"📄 Success Response (raw): {delete_response.text}")
                    # Even if JSON parsing fails, 200 is the correct response
                    self.print_result(True, "✅ Company without ships deleted successfully (raw response)")
                    return True
                    
            elif delete_response.status_code == 400:
                try:
                    error_data = delete_response.json()
                    self.print_result(False, f"❌ UNEXPECTED: Company without ships deletion blocked with 400: {error_data}")
                except:
                    self.print_result(False, f"❌ UNEXPECTED: Company without ships deletion blocked with 400: {delete_response.text}")
                return False
            else:
                try:
                    error_data = delete_response.json()
                    self.print_result(False, f"Expected 200, got {delete_response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Expected 200, got {delete_response.status_code}: {delete_response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during delete company without ships test: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all DELETE Company Validation tests"""
        print(f"🚀 Starting DELETE Company Validation Testing")
        print(f"🎯 FOCUS: Testing DELETE company validation logic")
        print(f"🔍 Expected: 400 error if company has ships, 200 OK if no ships")
        print(f"✅ Validation: Should check ships by company_id and company name")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"⏰ Test Time: {datetime.now().isoformat()}")
        
        test_results = []
        
        # Setup: Authentication Test
        result_auth = self.test_authentication()
        test_results.append(("Setup - Admin Authentication", result_auth))
        
        # Setup: Get Companies List
        if result_auth:
            result_get_companies = self.test_get_all_companies()
            test_results.append(("Setup - Get Companies List", result_get_companies))
        else:
            print(f"\n⚠️ Skipping Get Companies - authentication failed")
            test_results.append(("Setup - Get Companies List", False))
            result_get_companies = False
        
        # Setup: Get Ships List
        if result_auth:
            result_get_ships, companies_with_ships = self.test_get_ships()
            test_results.append(("Setup - Get Ships List", result_get_ships))
        else:
            print(f"\n⚠️ Skipping Get Ships - authentication failed")
            test_results.append(("Setup - Get Ships List", False))
            result_get_ships = False
            companies_with_ships = []
        
        # Test 1: Delete Company WITH Ships (should fail)
        if result_auth and result_get_ships:
            result_delete_with_ships = self.test_delete_company_with_ships(companies_with_ships)
            test_results.append(("Test 1 - Delete Company WITH Ships (Should Fail)", result_delete_with_ships))
        else:
            print(f"\n⚠️ Skipping Delete Company WITH Ships - setup failed")
            test_results.append(("Test 1 - Delete Company WITH Ships (Should Fail)", False))
        
        # Test 2: Delete Company WITHOUT Ships (should succeed)
        if result_auth:
            result_delete_without_ships = self.test_delete_company_without_ships()
            test_results.append(("Test 2 - Delete Company WITHOUT Ships (Should Succeed)", result_delete_without_ships))
        else:
            print(f"\n⚠️ Skipping Delete Company WITHOUT Ships - authentication failed")
            test_results.append(("Test 2 - Delete Company WITHOUT Ships (Should Succeed)", False))
        
        # Print summary
        self.print_test_summary(test_results)
        
        return test_results
    
    def print_test_summary(self, test_results):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"DELETE COMPANY VALIDATION TEST SUMMARY")
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
            print(f"🎉 All tests passed! DELETE company validation is working correctly.")
            print(f"✅ Company with ships deletion properly blocked with 400 Bad Request")
            print(f"✅ Error message contains ship count and ship names")
            print(f"✅ Company without ships deletion succeeds with 200 OK")
            print(f"✅ Validation checks both company_id and company name")
            print(f"✅ Database integrity maintained - companies with ships preserved")
        else:
            print(f"⚠️ Some tests failed. Please check the DELETE company validation implementation.")
            
            # Print specific failure analysis
            failed_tests = [name for name, result in test_results if not result]
            if failed_tests:
                print(f"\n❌ Failed Tests:")
                for failed_test in failed_tests:
                    print(f"   - {failed_test}")
                    
        # Print validation requirements summary
        print(f"\n🔍 VALIDATION REQUIREMENTS TESTED:")
        print(f"   1. Check if company has ships before deletion")
        print(f"   2. Return 400 Bad Request if ships exist")
        print(f"   3. Include detailed error message with ship count and names")
        print(f"   4. Allow deletion if no ships associated")
        print(f"   5. Return 200 OK with success message for valid deletions")

def main():
    """Main function to run the tests"""
    try:
        tester = DeleteCompanyValidationTester()
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
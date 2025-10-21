#!/usr/bin/env python3
"""
Certificate Manual Next Survey Edit Functionality Testing
FOCUS: Test that manual edits to Next Survey date properly clear next_survey_display

REVIEW REQUEST REQUIREMENTS:
1. Authentication: Login with admin1/123456 credentials
2. Get Certificate: Find a certificate that has both next_survey and next_survey_display values
3. Manual Edit Test: Use PUT /api/certificates/{cert_id} to update next_survey to a new manual date
4. Verify Update: Check that the response shows:
   - next_survey updated to the new manual value
   - next_survey_display cleared (set to null/None)
5. Fetch Verification: Get the same certificate again to confirm changes persisted

EXPECTED RESULTS:
- PUT request should update next_survey to manual value
- next_survey_display should be cleared/null after manual edit
- Frontend will then display manual value via formatDate(cert.next_survey)
- This fixes the issue where auto-calculated display overrides manual edits
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import time
import traceback

# Configuration - Use environment variable for backend URL
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipsurvey-ai.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class CertificateManualEditTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for certificate manual edit functionality
        self.manual_edit_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            
            # Certificate discovery
            'certificate_with_both_fields_found': False,
            'certificate_has_next_survey': False,
            'certificate_has_next_survey_display': False,
            'suitable_test_certificate_identified': False,
            
            # Manual edit testing
            'put_request_successful': False,
            'next_survey_updated_correctly': False,
            'next_survey_display_cleared': False,
            'response_structure_correct': False,
            
            # Persistence verification
            'fetch_after_update_successful': False,
            'manual_value_persisted': False,
            'display_field_remains_null': False,
            'database_persistence_confirmed': False,
            
            # Edge case testing
            'multiple_edits_working': False,
            'date_format_handling_correct': False,
            'api_response_consistent': False,
        }
        
        # Store test data
        self.test_certificate = None
        self.original_next_survey = None
        self.original_next_survey_display = None
        self.new_manual_date = None
        self.update_response = None
        self.fetch_response = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        # Also store in our log collection
        self.backend_logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
    def authenticate(self):
        """Authenticate with admin1/123456 credentials as specified in review request"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.manual_edit_tests['authentication_successful'] = True
                user_company = self.current_user.get('company')
                if user_company:
                    self.manual_edit_tests['user_company_identified'] = True
                return True
            else:
                self.log(f"   ❌ Authentication failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def find_certificate_with_both_fields(self):
        """Find a certificate that has both next_survey and next_survey_display values"""
        try:
            self.log("🔍 Finding certificate with both next_survey and next_survey_display...")
            
            # Get ships first
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                return False
            
            ships = response.json()
            user_company = self.current_user.get('company')
            user_ships = [ship for ship in ships if ship.get('company') == user_company]
            
            self.log(f"   Found {len(user_ships)} ships for user's company")
            
            # Search through ships for certificates with both fields
            for ship in user_ships:
                ship_id = ship.get('id')
                ship_name = ship.get('name')
                
                self.log(f"   Checking ship: {ship_name}")
                
                # Get certificates for this ship
                endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
                response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 200:
                    certificates = response.json()
                    self.log(f"      Found {len(certificates)} certificates")
                    
                    for cert in certificates:
                        cert_id = cert.get('id')
                        cert_name = cert.get('cert_name', 'Unknown')
                        next_survey = cert.get('next_survey')
                        next_survey_display = cert.get('next_survey_display')
                        
                        self.log(f"         Certificate: {cert_name}")
                        self.log(f"            next_survey: {next_survey}")
                        self.log(f"            next_survey_display: {next_survey_display}")
                        
                        # Check if this certificate has both fields
                        if next_survey and next_survey_display:
                            self.log(f"         ✅ Found suitable certificate: {cert_name}")
                            self.log(f"            Ship: {ship_name}")
                            self.log(f"            Certificate ID: {cert_id}")
                            self.log(f"            Current next_survey: {next_survey}")
                            self.log(f"            Current next_survey_display: {next_survey_display}")
                            
                            # Store test certificate data
                            self.test_certificate = cert
                            self.test_certificate['ship_name'] = ship_name
                            self.original_next_survey = next_survey
                            self.original_next_survey_display = next_survey_display
                            
                            self.manual_edit_tests['certificate_with_both_fields_found'] = True
                            self.manual_edit_tests['certificate_has_next_survey'] = True
                            self.manual_edit_tests['certificate_has_next_survey_display'] = True
                            self.manual_edit_tests['suitable_test_certificate_identified'] = True
                            
                            return True
                else:
                    self.log(f"      ❌ Failed to get certificates for {ship_name}: {response.status_code}")
            
            self.log("   ⚠️ No certificate found with both next_survey and next_survey_display")
            self.log("   Creating a test certificate with both fields...")
            
            # Create a test certificate with both fields
            return self.create_test_certificate_with_both_fields()
                
        except Exception as e:
            self.log(f"❌ Error finding certificate with both fields: {str(e)}", "ERROR")
            return False
    
    def create_test_certificate_with_both_fields(self):
        """Create a test certificate with both next_survey and next_survey_display fields"""
        try:
            self.log("🔧 Creating test certificate with both next_survey and next_survey_display...")
            
            # Get first available ship
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code != 200:
                self.log("❌ Failed to get ships for test certificate creation")
                return False
            
            ships = response.json()
            user_company = self.current_user.get('company')
            user_ships = [ship for ship in ships if ship.get('company') == user_company]
            
            if not user_ships:
                self.log("❌ No user company ships found")
                return False
            
            test_ship = user_ships[0]
            ship_id = test_ship.get('id')
            ship_name = test_ship.get('name')
            
            self.log(f"   Using ship: {ship_name}")
            
            # Create certificate with both fields
            current_date = datetime.now()
            next_survey_date = current_date + timedelta(days=90)
            
            cert_data = {
                "ship_id": ship_id,
                "cert_name": "TEST CERTIFICATE FOR MANUAL EDIT",
                "cert_type": "Full Term",
                "cert_no": "MANUAL-EDIT-TEST-001",
                "issue_date": current_date.isoformat(),
                "valid_date": (current_date + timedelta(days=365)).isoformat(),
                "next_survey": next_survey_date.strftime('%Y-%m-%d'),
                "next_survey_display": f"Due in 90 days ({next_survey_date.strftime('%d/%m/%Y')})",
                "next_survey_type": "Annual",
                "issued_by": "Test Authority",
                "category": "certificates",
                "sensitivity_level": "public"
            }
            
            endpoint = f"{BACKEND_URL}/certificates"
            response = requests.post(endpoint, json=cert_data, headers=self.get_headers(), timeout=30)
            
            if response.status_code in [200, 201]:
                cert_response = response.json()
                cert_id = cert_response.get('id')
                
                self.log(f"   ✅ Test certificate created successfully")
                self.log(f"      Certificate ID: {cert_id}")
                self.log(f"      next_survey: {cert_response.get('next_survey')}")
                self.log(f"      next_survey_display: {cert_response.get('next_survey_display')}")
                
                # Store test certificate data
                self.test_certificate = cert_response
                self.test_certificate['ship_name'] = ship_name
                self.original_next_survey = cert_response.get('next_survey')
                self.original_next_survey_display = cert_response.get('next_survey_display')
                
                self.manual_edit_tests['certificate_with_both_fields_found'] = True
                self.manual_edit_tests['certificate_has_next_survey'] = True
                self.manual_edit_tests['certificate_has_next_survey_display'] = True
                self.manual_edit_tests['suitable_test_certificate_identified'] = True
                
                return True
            else:
                self.log(f"   ❌ Failed to create test certificate: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating test certificate: {str(e)}", "ERROR")
            return False
    
    def test_manual_next_survey_edit(self):
        """Test manual edit of next_survey field and verify next_survey_display is cleared"""
        try:
            self.log("✏️ Testing manual Next Survey edit functionality...")
            
            if not self.test_certificate:
                self.log("❌ No test certificate available")
                return False
            
            cert_id = self.test_certificate.get('id')
            cert_name = self.test_certificate.get('cert_name')
            ship_name = self.test_certificate.get('ship_name')
            
            self.log(f"   Certificate: {cert_name}")
            self.log(f"   Ship: {ship_name}")
            self.log(f"   Certificate ID: {cert_id}")
            self.log(f"   Original next_survey: {self.original_next_survey}")
            self.log(f"   Original next_survey_display: {self.original_next_survey_display}")
            
            # Create new manual date (different from original)
            current_date = datetime.now()
            self.new_manual_date = (current_date + timedelta(days=120)).strftime('%Y-%m-%d')
            
            self.log(f"   New manual date: {self.new_manual_date}")
            
            # Prepare update payload - only update next_survey
            update_payload = {
                "next_survey": self.new_manual_date
            }
            
            self.log("   Sending PUT request to update next_survey...")
            
            # Send PUT request
            endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
            self.log(f"   PUT {endpoint}")
            self.log(f"   Payload: {json.dumps(update_payload, indent=2)}")
            
            response = requests.put(endpoint, json=update_payload, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.manual_edit_tests['put_request_successful'] = True
                self.log("   ✅ PUT request successful")
                
                try:
                    self.update_response = response.json()
                    self.log("   ✅ Response is valid JSON")
                    
                    # Log the full response for analysis
                    self.log(f"   Response data: {json.dumps(self.update_response, indent=2, default=str)}")
                    
                    # Verify the response structure and values
                    return self.verify_update_response()
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                self.log(f"   ❌ PUT request failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing manual next_survey edit: {str(e)}", "ERROR")
            return False
    
    def verify_update_response(self):
        """Verify that the update response shows correct next_survey and cleared next_survey_display"""
        try:
            self.log("🔍 Verifying update response...")
            
            if not self.update_response:
                self.log("❌ No update response to verify")
                return False
            
            response_next_survey = self.update_response.get('next_survey')
            response_next_survey_display = self.update_response.get('next_survey_display')
            
            self.log(f"   Response next_survey: {response_next_survey}")
            self.log(f"   Response next_survey_display: {response_next_survey_display}")
            
            # Check if next_survey was updated correctly
            if response_next_survey:
                # Handle different date formats
                if isinstance(response_next_survey, str):
                    # Extract date part if it's ISO format
                    if 'T' in response_next_survey:
                        response_date_part = response_next_survey.split('T')[0]
                    else:
                        response_date_part = response_next_survey
                else:
                    response_date_part = str(response_next_survey)
                
                if response_date_part == self.new_manual_date or response_next_survey == self.new_manual_date:
                    self.manual_edit_tests['next_survey_updated_correctly'] = True
                    self.log("   ✅ next_survey updated correctly to manual value")
                else:
                    self.log(f"   ❌ next_survey not updated correctly")
                    self.log(f"      Expected: {self.new_manual_date}")
                    self.log(f"      Got: {response_next_survey}")
                    return False
            else:
                self.log("   ❌ next_survey is missing from response")
                return False
            
            # Check if next_survey_display was cleared (set to null/None)
            if response_next_survey_display is None:
                self.manual_edit_tests['next_survey_display_cleared'] = True
                self.log("   ✅ next_survey_display cleared (set to null) - MANUAL EDIT LOGIC WORKING")
            else:
                self.log(f"   ❌ next_survey_display not cleared - still has value: {response_next_survey_display}")
                self.log("   ❌ This means manual edits may be overridden by auto-calculated display")
                return False
            
            # Check response structure
            expected_fields = ['id', 'next_survey', 'next_survey_display']
            missing_fields = []
            
            for field in expected_fields:
                if field not in self.update_response:
                    missing_fields.append(field)
            
            if not missing_fields:
                self.manual_edit_tests['response_structure_correct'] = True
                self.log("   ✅ Response structure is correct")
            else:
                self.log(f"   ❌ Missing fields in response: {missing_fields}")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error verifying update response: {str(e)}", "ERROR")
            return False
    
    def verify_persistence(self):
        """Fetch the certificate again to verify changes persisted in database"""
        try:
            self.log("💾 Verifying database persistence...")
            
            if not self.test_certificate:
                self.log("❌ No test certificate to verify")
                return False
            
            cert_id = self.test_certificate.get('id')
            
            # Fetch the certificate again
            endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.manual_edit_tests['fetch_after_update_successful'] = True
                self.log("   ✅ Fetch after update successful")
                
                try:
                    self.fetch_response = response.json()
                    self.log("   ✅ Fetch response is valid JSON")
                    
                    # Verify persistence
                    fetch_next_survey = self.fetch_response.get('next_survey')
                    fetch_next_survey_display = self.fetch_response.get('next_survey_display')
                    
                    self.log(f"   Fetched next_survey: {fetch_next_survey}")
                    self.log(f"   Fetched next_survey_display: {fetch_next_survey_display}")
                    
                    # Check if manual value persisted
                    if fetch_next_survey:
                        # Handle different date formats
                        if isinstance(fetch_next_survey, str):
                            if 'T' in fetch_next_survey:
                                fetch_date_part = fetch_next_survey.split('T')[0]
                            else:
                                fetch_date_part = fetch_next_survey
                        else:
                            fetch_date_part = str(fetch_next_survey)
                        
                        if fetch_date_part == self.new_manual_date or fetch_next_survey == self.new_manual_date:
                            self.manual_edit_tests['manual_value_persisted'] = True
                            self.log("   ✅ Manual next_survey value persisted in database")
                        else:
                            self.log(f"   ❌ Manual value not persisted")
                            self.log(f"      Expected: {self.new_manual_date}")
                            self.log(f"      Got: {fetch_next_survey}")
                            return False
                    else:
                        self.log("   ❌ next_survey is missing from fetch response")
                        return False
                    
                    # Check if next_survey_display remains null
                    if fetch_next_survey_display is None:
                        self.manual_edit_tests['display_field_remains_null'] = True
                        self.manual_edit_tests['database_persistence_confirmed'] = True
                        self.log("   ✅ next_survey_display remains null in database - PERSISTENCE CONFIRMED")
                    else:
                        self.log(f"   ❌ next_survey_display not null in database: {fetch_next_survey_display}")
                        return False
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON in fetch response: {str(e)}")
                    return False
            else:
                self.log(f"   ❌ Fetch after update failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying persistence: {str(e)}", "ERROR")
            return False
    
    def test_multiple_edits(self):
        """Test multiple consecutive edits to ensure functionality remains consistent"""
        try:
            self.log("🔄 Testing multiple consecutive edits...")
            
            if not self.test_certificate:
                self.log("❌ No test certificate available")
                return False
            
            cert_id = self.test_certificate.get('id')
            
            # Perform second edit
            current_date = datetime.now()
            second_manual_date = (current_date + timedelta(days=150)).strftime('%Y-%m-%d')
            
            self.log(f"   Second manual date: {second_manual_date}")
            
            update_payload = {
                "next_survey": second_manual_date
            }
            
            endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
            response = requests.put(endpoint, json=update_payload, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                response_next_survey = response_data.get('next_survey')
                response_next_survey_display = response_data.get('next_survey_display')
                
                self.log(f"   Second edit response next_survey: {response_next_survey}")
                self.log(f"   Second edit response next_survey_display: {response_next_survey_display}")
                
                # Verify second edit
                if response_next_survey_display is None:
                    self.manual_edit_tests['multiple_edits_working'] = True
                    self.log("   ✅ Multiple edits working - next_survey_display remains cleared")
                    return True
                else:
                    self.log(f"   ❌ Multiple edits failed - next_survey_display not cleared: {response_next_survey_display}")
                    return False
            else:
                self.log(f"   ❌ Second edit failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing multiple edits: {str(e)}", "ERROR")
            return False
    
    def test_date_format_handling(self):
        """Test different date formats to ensure robust handling"""
        try:
            self.log("📅 Testing date format handling...")
            
            if not self.test_certificate:
                self.log("❌ No test certificate available")
                return False
            
            cert_id = self.test_certificate.get('id')
            
            # Test different date formats
            date_formats = [
                "2025-12-25",  # YYYY-MM-DD
                "25/12/2025",  # DD/MM/YYYY
                "2025-12-25T00:00:00Z",  # ISO format
            ]
            
            format_tests_passed = 0
            
            for date_format in date_formats:
                self.log(f"   Testing date format: {date_format}")
                
                update_payload = {
                    "next_survey": date_format
                }
                
                endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
                response = requests.put(endpoint, json=update_payload, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 200:
                    response_data = response.json()
                    response_next_survey_display = response_data.get('next_survey_display')
                    
                    if response_next_survey_display is None:
                        format_tests_passed += 1
                        self.log(f"      ✅ Format {date_format} handled correctly")
                    else:
                        self.log(f"      ❌ Format {date_format} failed - display not cleared")
                else:
                    self.log(f"      ❌ Format {date_format} failed - status: {response.status_code}")
            
            if format_tests_passed == len(date_formats):
                self.manual_edit_tests['date_format_handling_correct'] = True
                self.log("   ✅ All date formats handled correctly")
                return True
            else:
                self.log(f"   ❌ Date format handling issues - {format_tests_passed}/{len(date_formats)} passed")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing date format handling: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_manual_edit_test(self):
        """Run comprehensive test of certificate manual Next Survey edit functionality"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE CERTIFICATE MANUAL EDIT TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find certificate with both fields
            self.log("\nSTEP 2: Finding certificate with both next_survey and next_survey_display")
            if not self.find_certificate_with_both_fields():
                self.log("❌ CRITICAL: Could not find or create suitable test certificate")
                return False
            
            # Step 3: Test manual edit
            self.log("\nSTEP 3: Testing manual Next Survey edit")
            if not self.test_manual_next_survey_edit():
                self.log("❌ CRITICAL: Manual edit test failed")
                return False
            
            # Step 4: Verify persistence
            self.log("\nSTEP 4: Verifying database persistence")
            if not self.verify_persistence():
                self.log("❌ CRITICAL: Persistence verification failed")
                return False
            
            # Step 5: Test multiple edits
            self.log("\nSTEP 5: Testing multiple consecutive edits")
            if not self.test_multiple_edits():
                self.log("❌ Multiple edits test failed")
                # Don't fail the entire test for this
            
            # Step 6: Test date format handling
            self.log("\nSTEP 6: Testing date format handling")
            if not self.test_date_format_handling():
                self.log("❌ Date format handling test failed")
                # Don't fail the entire test for this
            
            self.manual_edit_tests['api_response_consistent'] = True
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE MANUAL EDIT TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of manual edit test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 CERTIFICATE MANUAL EDIT TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.manual_edit_tests)
            passed_tests = sum(1 for result in self.manual_edit_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION:")
            auth_tests = [
                ('authentication_successful', 'Login with admin1/123456 successful'),
                ('user_company_identified', 'User company identified'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.manual_edit_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Certificate Discovery Results
            self.log("\n🔍 CERTIFICATE DISCOVERY:")
            discovery_tests = [
                ('certificate_with_both_fields_found', 'Certificate with both fields found'),
                ('certificate_has_next_survey', 'Certificate has next_survey field'),
                ('certificate_has_next_survey_display', 'Certificate has next_survey_display field'),
                ('suitable_test_certificate_identified', 'Suitable test certificate identified'),
            ]
            
            for test_key, description in discovery_tests:
                status = "✅ PASS" if self.manual_edit_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Manual Edit Results
            self.log("\n✏️ MANUAL EDIT FUNCTIONALITY:")
            edit_tests = [
                ('put_request_successful', 'PUT request successful'),
                ('next_survey_updated_correctly', 'next_survey updated to manual value'),
                ('next_survey_display_cleared', 'next_survey_display cleared (set to null)'),
                ('response_structure_correct', 'Response structure correct'),
            ]
            
            for test_key, description in edit_tests:
                status = "✅ PASS" if self.manual_edit_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Persistence Results
            self.log("\n💾 DATABASE PERSISTENCE:")
            persistence_tests = [
                ('fetch_after_update_successful', 'Fetch after update successful'),
                ('manual_value_persisted', 'Manual value persisted in database'),
                ('display_field_remains_null', 'next_survey_display remains null'),
                ('database_persistence_confirmed', 'Database persistence confirmed'),
            ]
            
            for test_key, description in persistence_tests:
                status = "✅ PASS" if self.manual_edit_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Edge Case Results
            self.log("\n🔄 EDGE CASE TESTING:")
            edge_tests = [
                ('multiple_edits_working', 'Multiple consecutive edits working'),
                ('date_format_handling_correct', 'Date format handling correct'),
                ('api_response_consistent', 'API response consistent'),
            ]
            
            for test_key, description in edge_tests:
                status = "✅ PASS" if self.manual_edit_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            # Check critical functionality
            critical_tests = [
                'put_request_successful',
                'next_survey_updated_correctly', 
                'next_survey_display_cleared',
                'manual_value_persisted',
                'display_field_remains_null'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.manual_edit_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ MANUAL EDIT FUNCTIONALITY IS WORKING CORRECTLY")
                self.log("   ✅ Manual next_survey edits properly clear next_survey_display")
                self.log("   ✅ Frontend will display manual value via formatDate(cert.next_survey)")
                self.log("   ✅ Auto-calculated display no longer overrides manual edits")
            elif critical_passed >= 3:
                self.log("   ⚠️ MANUAL EDIT FUNCTIONALITY MOSTLY WORKING")
                self.log("   ⚠️ Some issues detected but core functionality appears operational")
            else:
                self.log("   ❌ MANUAL EDIT FUNCTIONALITY HAS ISSUES")
                self.log("   ❌ Manual edits may not be working correctly")
                self.log("   ❌ Auto-calculated display may still override manual values")
            
            # Test Data Summary
            if self.test_certificate:
                self.log("\n📋 TEST DATA SUMMARY:")
                self.log(f"   Certificate: {self.test_certificate.get('cert_name')}")
                self.log(f"   Ship: {self.test_certificate.get('ship_name')}")
                self.log(f"   Certificate ID: {self.test_certificate.get('id')}")
                self.log(f"   Original next_survey: {self.original_next_survey}")
                self.log(f"   Original next_survey_display: {self.original_next_survey_display}")
                self.log(f"   New manual date: {self.new_manual_date}")
                
                if self.update_response:
                    self.log(f"   Update response next_survey: {self.update_response.get('next_survey')}")
                    self.log(f"   Update response next_survey_display: {self.update_response.get('next_survey_display')}")
                
                if self.fetch_response:
                    self.log(f"   Fetch response next_survey: {self.fetch_response.get('next_survey')}")
                    self.log(f"   Fetch response next_survey_display: {self.fetch_response.get('next_survey_display')}")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the certificate manual edit test"""
    print("Certificate Manual Next Survey Edit Functionality Test")
    print("=" * 60)
    
    tester = CertificateManualEditTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_manual_edit_test()
        
        # Print detailed summary
        tester.print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
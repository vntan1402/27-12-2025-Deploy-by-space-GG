#!/usr/bin/env python3
"""
Ship Management System - Certificate Edit Bug Reproduction Test
FOCUS: Test the certificate edit functionality to reproduce the Next Survey update bug

REVIEW REQUEST REQUIREMENTS:
1. Login with admin1/123456
2. Find a certificate in Certificate List and note its current Next Survey value
3. Edit the certificate and change the Next Survey field to a different date
4. Save the changes and verify the response shows success
5. Check if the Certificate List updates to show the new Next Survey value
6. Verify the database actually contains the updated Next Survey value

BACKEND TESTING FOCUS:
1. PUT /api/certificates/{cert_id} - Test this endpoint directly with Next Survey update
2. Database Verification - Check if the update actually persists in MongoDB
3. Response Verification - Ensure the PUT response contains the updated data
4. GET /api/ships/{ship_id}/certificates - Verify this returns updated data

KEY AREAS TO CHECK:
1. Backend Update Logic: Does the PUT request actually update next_survey field in database?
2. Date Format Handling: Are date formats processed correctly during update?
3. Response Data: Does the PUT response contain the updated next_survey value?
4. Database Persistence: Is the change actually saved to MongoDB?
5. Fetch Logic: Does the GET request return the updated data?

EXPECTED BEHAVIOR:
- PUT request should update next_survey field in database
- Certificate list should refresh with new Next Survey value
- Database should contain the updated next_survey value
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
import tempfile
from urllib.parse import urlparse

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://crewcert-manager.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class CertificateEditBugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for certificate edit bug reproduction
        self.bug_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            
            # Certificate discovery
            'certificates_found': False,
            'test_certificate_selected': False,
            'original_next_survey_noted': False,
            
            # PUT endpoint testing
            'put_endpoint_accessible': False,
            'put_request_successful': False,
            'put_response_contains_updated_data': False,
            'put_response_format_correct': False,
            
            # Database persistence verification
            'database_update_persisted': False,
            'get_request_returns_updated_data': False,
            'certificate_list_shows_new_value': False,
            
            # Date format handling
            'date_format_processed_correctly': False,
            'next_survey_field_updated_in_db': False,
            
            # Bug reproduction verification
            'bug_reproduced': False,
            'update_logic_working': False,
            'fetch_logic_working': False,
        }
        
        # Store test data
        self.user_company = None
        self.test_ship = None
        self.test_certificate = None
        self.original_next_survey = None
        self.new_next_survey = None
        self.updated_certificate = None
        
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
                
                self.bug_tests['authentication_successful'] = True
                self.user_company = self.current_user.get('company')
                if self.user_company:
                    self.bug_tests['user_company_identified'] = True
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
    
    def find_test_certificate(self):
        """Find a certificate to test with - preferably one with a next_survey date"""
        try:
            self.log("🔍 Finding a test certificate with next_survey date...")
            
            # Get ships for the user's company
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                return False
            
            ships = response.json()
            user_company_ships = [ship for ship in ships if ship.get('company') == self.user_company]
            
            if not user_company_ships:
                self.log("❌ No ships found for user's company")
                return False
            
            self.log(f"   Found {len(user_company_ships)} ships for company {self.user_company}")
            
            # Look for certificates with next_survey dates
            for ship in user_company_ships:
                ship_id = ship.get('id')
                ship_name = ship.get('name')
                
                self.log(f"   Checking certificates for ship: {ship_name}")
                
                # Get certificates for this ship
                cert_endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
                cert_response = requests.get(cert_endpoint, headers=self.get_headers(), timeout=30)
                
                if cert_response.status_code == 200:
                    certificates = cert_response.json()
                    self.log(f"      Found {len(certificates)} certificates")
                    
                    # Look for a certificate with next_survey date
                    for cert in certificates:
                        next_survey = cert.get('next_survey')
                        cert_name = cert.get('cert_name', 'Unknown')
                        cert_id = cert.get('id')
                        
                        if next_survey and cert_id:
                            self.log(f"      ✅ Found suitable test certificate:")
                            self.log(f"         Certificate ID: {cert_id}")
                            self.log(f"         Certificate Name: {cert_name}")
                            self.log(f"         Current Next Survey: {next_survey}")
                            self.log(f"         Ship: {ship_name}")
                            
                            self.test_ship = ship
                            self.test_certificate = cert
                            self.original_next_survey = next_survey
                            self.bug_tests['certificates_found'] = True
                            self.bug_tests['test_certificate_selected'] = True
                            self.bug_tests['original_next_survey_noted'] = True
                            return True
                    
                    self.log(f"      No certificates with next_survey found on {ship_name}")
                else:
                    self.log(f"      ❌ Failed to get certificates for {ship_name}: {cert_response.status_code}")
            
            self.log("❌ No suitable test certificate found with next_survey date")
            return False
            
        except Exception as e:
            self.log(f"❌ Error finding test certificate: {str(e)}", "ERROR")
            return False
    
    def test_put_certificate_endpoint(self):
        """Test the PUT /api/certificates/{cert_id} endpoint with Next Survey update"""
        try:
            self.log("🔄 Testing PUT /api/certificates/{cert_id} endpoint...")
            
            if not self.test_certificate:
                self.log("❌ No test certificate available")
                return False
            
            cert_id = self.test_certificate.get('id')
            self.log(f"   Certificate ID: {cert_id}")
            self.log(f"   Original Next Survey: {self.original_next_survey}")
            
            # Calculate a new next_survey date (30 days from now)
            from datetime import datetime, timedelta
            new_date = datetime.now() + timedelta(days=30)
            self.new_next_survey = new_date.strftime('%Y-%m-%d')
            
            self.log(f"   New Next Survey: {self.new_next_survey}")
            
            # Prepare update data - only update next_survey field
            update_data = {
                "next_survey": self.new_next_survey
            }
            
            endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
            self.log(f"   PUT {endpoint}")
            self.log(f"   Update data: {json.dumps(update_data, indent=2)}")
            
            response = requests.put(endpoint, json=update_data, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                self.bug_tests['put_endpoint_accessible'] = True
                self.bug_tests['put_request_successful'] = True
                self.log("✅ PUT request successful")
                
                try:
                    response_data = response.json()
                    self.updated_certificate = response_data
                    self.log("✅ Response is valid JSON")
                    
                    # Check if response contains the updated next_survey value
                    response_next_survey = response_data.get('next_survey')
                    self.log(f"   Response next_survey: {response_next_survey}")
                    
                    if response_next_survey:
                        # Parse and compare dates (handle different formats)
                        try:
                            if isinstance(response_next_survey, str):
                                if 'T' in response_next_survey:
                                    response_date = datetime.fromisoformat(response_next_survey.replace('Z', '+00:00')).date()
                                else:
                                    response_date = datetime.strptime(response_next_survey, '%Y-%m-%d').date()
                            else:
                                response_date = response_next_survey
                            
                            expected_date = datetime.strptime(self.new_next_survey, '%Y-%m-%d').date()
                            
                            if response_date == expected_date:
                                self.bug_tests['put_response_contains_updated_data'] = True
                                self.bug_tests['date_format_processed_correctly'] = True
                                self.log("✅ PUT response contains updated next_survey value")
                            else:
                                self.log(f"❌ PUT response next_survey mismatch: got {response_date}, expected {expected_date}")
                        except Exception as e:
                            self.log(f"⚠️ Could not parse response date: {str(e)}")
                    else:
                        self.log("❌ PUT response does not contain next_survey field")
                    
                    # Check response format
                    expected_fields = ['id', 'cert_name', 'next_survey']
                    missing_fields = [field for field in expected_fields if field not in response_data]
                    
                    if not missing_fields:
                        self.bug_tests['put_response_format_correct'] = True
                        self.log("✅ PUT response format is correct")
                    else:
                        self.log(f"❌ PUT response missing fields: {missing_fields}")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                self.log(f"❌ PUT request failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing PUT endpoint: {str(e)}", "ERROR")
            return False
    
    def verify_database_persistence(self):
        """Verify that the update actually persisted in the database"""
        try:
            self.log("💾 Verifying database persistence...")
            
            if not self.test_certificate or not self.test_ship:
                self.log("❌ No test data available for verification")
                return False
            
            cert_id = self.test_certificate.get('id')
            ship_id = self.test_ship.get('id')
            
            # Method 1: Get the specific certificate by ID (if endpoint exists)
            self.log("   Method 1: Direct certificate fetch")
            cert_endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
            cert_response = requests.get(cert_endpoint, headers=self.get_headers(), timeout=30)
            
            if cert_response.status_code == 200:
                cert_data = cert_response.json()
                db_next_survey = cert_data.get('next_survey')
                self.log(f"   Database next_survey (direct): {db_next_survey}")
                
                if db_next_survey:
                    try:
                        if isinstance(db_next_survey, str):
                            if 'T' in db_next_survey:
                                db_date = datetime.fromisoformat(db_next_survey.replace('Z', '+00:00')).date()
                            else:
                                db_date = datetime.strptime(db_next_survey, '%Y-%m-%d').date()
                        else:
                            db_date = db_next_survey
                        
                        expected_date = datetime.strptime(self.new_next_survey, '%Y-%m-%d').date()
                        
                        if db_date == expected_date:
                            self.bug_tests['database_update_persisted'] = True
                            self.bug_tests['next_survey_field_updated_in_db'] = True
                            self.log("✅ Database update persisted (direct fetch)")
                        else:
                            self.log(f"❌ Database value mismatch: got {db_date}, expected {expected_date}")
                    except Exception as e:
                        self.log(f"⚠️ Could not parse database date: {str(e)}")
            else:
                self.log(f"   Direct certificate fetch failed: {cert_response.status_code}")
            
            # Method 2: Get certificates through ship endpoint
            self.log("   Method 2: Ship certificates fetch")
            ship_cert_endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
            ship_cert_response = requests.get(ship_cert_endpoint, headers=self.get_headers(), timeout=30)
            
            if ship_cert_response.status_code == 200:
                certificates = ship_cert_response.json()
                
                # Find our test certificate
                test_cert_in_list = None
                for cert in certificates:
                    if cert.get('id') == cert_id:
                        test_cert_in_list = cert
                        break
                
                if test_cert_in_list:
                    list_next_survey = test_cert_in_list.get('next_survey')
                    self.log(f"   Certificate list next_survey: {list_next_survey}")
                    
                    if list_next_survey:
                        try:
                            if isinstance(list_next_survey, str):
                                if 'T' in list_next_survey:
                                    list_date = datetime.fromisoformat(list_next_survey.replace('Z', '+00:00')).date()
                                else:
                                    list_date = datetime.strptime(list_next_survey, '%Y-%m-%d').date()
                            else:
                                list_date = list_next_survey
                            
                            expected_date = datetime.strptime(self.new_next_survey, '%Y-%m-%d').date()
                            
                            if list_date == expected_date:
                                self.bug_tests['get_request_returns_updated_data'] = True
                                self.bug_tests['certificate_list_shows_new_value'] = True
                                self.log("✅ Certificate list shows updated value")
                            else:
                                self.log(f"❌ Certificate list value mismatch: got {list_date}, expected {expected_date}")
                        except Exception as e:
                            self.log(f"⚠️ Could not parse certificate list date: {str(e)}")
                    else:
                        self.log("❌ Certificate list does not contain next_survey field")
                else:
                    self.log("❌ Test certificate not found in certificate list")
            else:
                self.log(f"   Ship certificates fetch failed: {ship_cert_response.status_code}")
            
            # Overall assessment
            if (self.bug_tests.get('database_update_persisted', False) and 
                self.bug_tests.get('get_request_returns_updated_data', False)):
                self.bug_tests['update_logic_working'] = True
                self.bug_tests['fetch_logic_working'] = True
                self.log("✅ Database persistence verified - update and fetch logic working")
                return True
            elif self.bug_tests.get('database_update_persisted', False):
                self.log("⚠️ Database update persisted but fetch logic may have issues")
                return True
            else:
                self.log("❌ Database persistence verification failed")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying database persistence: {str(e)}", "ERROR")
            return False
    
    def test_bug_reproduction(self):
        """Test if the bug can be reproduced - check if update actually fails"""
        try:
            self.log("🐛 Testing bug reproduction...")
            
            # Compare original vs current values
            if not self.original_next_survey or not self.new_next_survey:
                self.log("❌ Missing original or new next_survey values")
                return False
            
            self.log(f"   Original Next Survey: {self.original_next_survey}")
            self.log(f"   Expected New Next Survey: {self.new_next_survey}")
            
            # Check if the update actually worked
            update_successful = (
                self.bug_tests.get('put_request_successful', False) and
                self.bug_tests.get('put_response_contains_updated_data', False) and
                self.bug_tests.get('database_update_persisted', False) and
                self.bug_tests.get('certificate_list_shows_new_value', False)
            )
            
            if update_successful:
                self.log("✅ Certificate update working correctly - bug NOT reproduced")
                self.log("   - PUT request successful")
                self.log("   - PUT response contains updated data")
                self.log("   - Database update persisted")
                self.log("   - Certificate list shows new value")
                self.bug_tests['bug_reproduced'] = False
            else:
                self.log("❌ Certificate update failed - bug REPRODUCED")
                self.bug_tests['bug_reproduced'] = True
                
                # Identify specific failure points
                if not self.bug_tests.get('put_request_successful', False):
                    self.log("   - PUT request failed")
                if not self.bug_tests.get('put_response_contains_updated_data', False):
                    self.log("   - PUT response does not contain updated data")
                if not self.bug_tests.get('database_update_persisted', False):
                    self.log("   - Database update did not persist")
                if not self.bug_tests.get('certificate_list_shows_new_value', False):
                    self.log("   - Certificate list does not show new value")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing bug reproduction: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_certificate_edit_test(self):
        """Run comprehensive test of certificate edit functionality"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE CERTIFICATE EDIT BUG REPRODUCTION TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find test certificate
            self.log("\nSTEP 2: Finding test certificate")
            if not self.find_test_certificate():
                self.log("❌ CRITICAL: No suitable test certificate found")
                return False
            
            # Step 3: Test PUT endpoint
            self.log("\nSTEP 3: Testing PUT /api/certificates/{cert_id} endpoint")
            if not self.test_put_certificate_endpoint():
                self.log("❌ CRITICAL: PUT endpoint test failed")
                return False
            
            # Step 4: Verify database persistence
            self.log("\nSTEP 4: Verifying database persistence")
            if not self.verify_database_persistence():
                self.log("❌ CRITICAL: Database persistence verification failed")
                return False
            
            # Step 5: Test bug reproduction
            self.log("\nSTEP 5: Testing bug reproduction")
            if not self.test_bug_reproduction():
                self.log("❌ Bug reproduction test failed")
                return False
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE CERTIFICATE EDIT TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of certificate edit test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 CERTIFICATE EDIT BUG REPRODUCTION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.bug_tests)
            passed_tests = sum(1 for result in self.bug_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION:")
            auth_tests = [
                ('authentication_successful', 'Login with admin1/123456'),
                ('user_company_identified', 'User company identified'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.bug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Certificate Discovery Results
            self.log("\n🔍 CERTIFICATE DISCOVERY:")
            discovery_tests = [
                ('certificates_found', 'Certificates found'),
                ('test_certificate_selected', 'Test certificate selected'),
                ('original_next_survey_noted', 'Original Next Survey value noted'),
            ]
            
            for test_key, description in discovery_tests:
                status = "✅ PASS" if self.bug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # PUT Endpoint Results
            self.log("\n🔄 PUT ENDPOINT TESTING:")
            put_tests = [
                ('put_endpoint_accessible', 'PUT /api/certificates/{cert_id} accessible'),
                ('put_request_successful', 'PUT request successful'),
                ('put_response_contains_updated_data', 'PUT response contains updated data'),
                ('put_response_format_correct', 'PUT response format correct'),
            ]
            
            for test_key, description in put_tests:
                status = "✅ PASS" if self.bug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Database Persistence Results
            self.log("\n💾 DATABASE PERSISTENCE:")
            db_tests = [
                ('database_update_persisted', 'Database update persisted'),
                ('next_survey_field_updated_in_db', 'Next Survey field updated in database'),
                ('get_request_returns_updated_data', 'GET request returns updated data'),
                ('certificate_list_shows_new_value', 'Certificate list shows new value'),
            ]
            
            for test_key, description in db_tests:
                status = "✅ PASS" if self.bug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Date Format Handling Results
            self.log("\n📅 DATE FORMAT HANDLING:")
            date_tests = [
                ('date_format_processed_correctly', 'Date format processed correctly'),
                ('update_logic_working', 'Update logic working'),
                ('fetch_logic_working', 'Fetch logic working'),
            ]
            
            for test_key, description in date_tests:
                status = "✅ PASS" if self.bug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Bug Reproduction Results
            self.log("\n🐛 BUG REPRODUCTION:")
            bug_reproduced = self.bug_tests.get('bug_reproduced', False)
            if bug_reproduced:
                self.log("   ❌ BUG REPRODUCED - Certificate edit functionality is not working correctly")
                self.log("   ❌ Next Survey update is failing")
            else:
                self.log("   ✅ BUG NOT REPRODUCED - Certificate edit functionality is working correctly")
                self.log("   ✅ Next Survey update is working as expected")
            
            # Test Data Summary
            if self.test_certificate and self.test_ship:
                self.log("\n📋 TEST DATA SUMMARY:")
                self.log(f"   Ship: {self.test_ship.get('name')}")
                self.log(f"   Certificate: {self.test_certificate.get('cert_name')}")
                self.log(f"   Certificate ID: {self.test_certificate.get('id')}")
                self.log(f"   Original Next Survey: {self.original_next_survey}")
                self.log(f"   New Next Survey: {self.new_next_survey}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_passed = sum(1 for test_key, _ in put_tests + db_tests if self.bug_tests.get(test_key, False))
            if critical_passed >= 6:  # Most critical tests passed
                self.log("   ✅ CERTIFICATE EDIT FUNCTIONALITY APPEARS TO BE WORKING")
                self.log("   ✅ PUT endpoint successfully updates Next Survey field")
                self.log("   ✅ Database persistence is working correctly")
                self.log("   ✅ Certificate list reflects updated values")
            else:
                self.log("   ❌ CERTIFICATE EDIT FUNCTIONALITY HAS ISSUES")
                self.log("   ❌ Next Survey update bug confirmed")
                self.log("   ❌ Further investigation needed")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the certificate edit bug reproduction test"""
    try:
        print("🚀 Starting Certificate Edit Bug Reproduction Test")
        print("=" * 80)
        
        tester = CertificateEditBugTester()
        
        # Run the comprehensive test
        success = tester.run_comprehensive_certificate_edit_test()
        
        # Print detailed summary
        tester.print_test_summary()
        
        if success:
            print("\n✅ Certificate edit test completed successfully")
            return 0
        else:
            print("\n❌ Certificate edit test failed")
            return 1
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
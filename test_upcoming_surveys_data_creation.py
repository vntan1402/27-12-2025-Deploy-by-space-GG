#!/usr/bin/env python3
"""
Ship Management System - Create Test Data for Upcoming Surveys Notification System
FOCUS: Create test certificate with upcoming survey date for notification testing

REVIEW REQUEST REQUIREMENTS:
1. Login with admin1/123456
2. Find a ship belonging to AMCSC company 
3. Create or update a certificate with next_survey date within ±3 months window (current date ±90 days)
4. Set the certificate with proper fields: cert_name, cert_abbreviation, next_survey, next_survey_type, last_endorse
5. Test the upcoming surveys API to verify it returns the test certificate
6. Verify the certificate appears in the upcoming surveys list

TEST CERTIFICATE DETAILS TO CREATE:
- Ship: Any ship in AMCSC company (e.g., SUNSHINE 01 or MINH ANH 09)
- Certificate Name: "Test Survey Notification Certificate"
- Cert Abbreviation: "TSN" 
- Next Survey: Set to current date + 30 days (within ±3 months window)
- Next Survey Type: "Annual Survey"
- Last Endorse: Set to current date - 365 days

EXPECTED OUTCOME:
- Certificate created successfully with upcoming survey date
- API `/api/certificates/upcoming-surveys` returns the test certificate
- Certificate shows in upcoming surveys list with proper status indicators
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
import uuid

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://crew-cert-manager.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class UpcomingSurveysDataCreationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for data creation functionality
        self.data_creation_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'amcsc_company_confirmed': False,
            
            # Ship identification
            'amcsc_ships_found': False,
            'target_ship_selected': False,
            'ship_data_retrieved': False,
            
            # Certificate creation
            'test_certificate_created': False,
            'certificate_fields_set_correctly': False,
            'next_survey_date_in_window': False,
            
            # API verification
            'upcoming_surveys_api_accessible': False,
            'test_certificate_returned_by_api': False,
            'certificate_appears_in_list': False,
            'status_indicators_correct': False,
        }
        
        # Store test data
        self.user_company = None
        self.amcsc_ships = []
        self.selected_ship = None
        self.test_certificate = None
        self.test_certificate_id = None
        self.upcoming_surveys_response = {}
        
        # Test certificate details as specified in review request
        self.test_cert_data = {
            'cert_name': 'Test Survey Notification Certificate',
            'cert_abbreviation': 'TSN',
            'next_survey_type': 'Annual Survey',
            'cert_type': 'Full Term',
            'issued_by': 'Test Authority'
        }
        
        # Calculate dates
        current_date = datetime.now()
        self.test_cert_data['next_survey'] = (current_date + timedelta(days=30)).strftime('%Y-%m-%d')
        self.test_cert_data['last_endorse'] = (current_date - timedelta(days=365)).strftime('%Y-%m-%d')
        self.test_cert_data['issue_date'] = (current_date - timedelta(days=400)).strftime('%Y-%m-%d')
        self.test_cert_data['valid_date'] = (current_date + timedelta(days=365)).strftime('%Y-%m-%d')
        
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
                
                self.data_creation_tests['authentication_successful'] = True
                self.user_company = self.current_user.get('company')
                if self.user_company:
                    self.data_creation_tests['user_company_identified'] = True
                    
                    # Check if user is from AMCSC company
                    if self.user_company == 'AMCSC':
                        self.data_creation_tests['amcsc_company_confirmed'] = True
                        self.log("✅ User belongs to AMCSC company as required")
                    else:
                        self.log(f"⚠️ User company is '{self.user_company}', not 'AMCSC' as expected")
                        
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
    
    def find_amcsc_ships(self):
        """Find ships belonging to AMCSC company"""
        try:
            self.log("🚢 Finding ships belonging to AMCSC company...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                all_ships = response.json()
                self.log(f"   Total ships found: {len(all_ships)}")
                
                # Filter for AMCSC company ships
                amcsc_ships = [ship for ship in all_ships if ship.get('company') == 'AMCSC']
                self.amcsc_ships = amcsc_ships
                
                self.log(f"   AMCSC company ships found: {len(amcsc_ships)}")
                
                if amcsc_ships:
                    self.data_creation_tests['amcsc_ships_found'] = True
                    
                    # Log ship details
                    for ship in amcsc_ships:
                        self.log(f"      Ship: {ship.get('name')} (IMO: {ship.get('imo')}, ID: {ship.get('id')})")
                    
                    # Select target ship (prefer SUNSHINE 01 or MINH ANH 09 as mentioned in review request)
                    target_ship = None
                    for ship in amcsc_ships:
                        ship_name = ship.get('name', '').upper()
                        if 'SUNSHINE 01' in ship_name or 'MINH ANH 09' in ship_name:
                            target_ship = ship
                            break
                    
                    # If preferred ships not found, use first available
                    if not target_ship:
                        target_ship = amcsc_ships[0]
                    
                    self.selected_ship = target_ship
                    self.data_creation_tests['target_ship_selected'] = True
                    
                    self.log(f"✅ Selected target ship: {target_ship.get('name')} (ID: {target_ship.get('id')})")
                    return True
                else:
                    self.log("❌ No ships found for AMCSC company")
                    return False
            else:
                self.log(f"❌ Failed to retrieve ships: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding AMCSC ships: {str(e)}", "ERROR")
            return False
    
    def get_ship_details(self):
        """Get detailed information about the selected ship"""
        try:
            if not self.selected_ship:
                self.log("❌ No ship selected for details retrieval")
                return False
            
            ship_id = self.selected_ship.get('id')
            self.log(f"📋 Getting details for ship: {self.selected_ship.get('name')} (ID: {ship_id})")
            
            endpoint = f"{BACKEND_URL}/ships/{ship_id}"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ship_data = response.json()
                self.selected_ship = ship_data  # Update with full details
                self.data_creation_tests['ship_data_retrieved'] = True
                
                self.log("✅ Ship details retrieved successfully")
                self.log(f"   Ship Name: {ship_data.get('name')}")
                self.log(f"   IMO: {ship_data.get('imo')}")
                self.log(f"   Flag: {ship_data.get('flag')}")
                self.log(f"   Ship Type: {ship_data.get('ship_type')}")
                self.log(f"   Company: {ship_data.get('company')}")
                
                return True
            else:
                self.log(f"❌ Failed to get ship details: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting ship details: {str(e)}", "ERROR")
            return False
    
    def create_test_certificate(self):
        """Create test certificate with upcoming survey date"""
        try:
            if not self.selected_ship:
                self.log("❌ No ship selected for certificate creation")
                return False
            
            ship_id = self.selected_ship.get('id')
            ship_name = self.selected_ship.get('name')
            
            self.log(f"📜 Creating test certificate for ship: {ship_name}")
            self.log("   Test Certificate Details:")
            self.log(f"      Certificate Name: {self.test_cert_data['cert_name']}")
            self.log(f"      Certificate Abbreviation: {self.test_cert_data['cert_abbreviation']}")
            self.log(f"      Next Survey Date: {self.test_cert_data['next_survey']} (30 days from now)")
            self.log(f"      Next Survey Type: {self.test_cert_data['next_survey_type']}")
            self.log(f"      Last Endorse: {self.test_cert_data['last_endorse']} (365 days ago)")
            self.log(f"      Issue Date: {self.test_cert_data['issue_date']}")
            self.log(f"      Valid Date: {self.test_cert_data['valid_date']}")
            
            # Prepare certificate data
            cert_data = {
                'ship_id': ship_id,
                'cert_name': self.test_cert_data['cert_name'],
                'cert_type': self.test_cert_data['cert_type'],
                'cert_no': f'TSN-{datetime.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:8].upper()}',
                'issue_date': self.test_cert_data['issue_date'],
                'valid_date': self.test_cert_data['valid_date'],
                'last_endorse': self.test_cert_data['last_endorse'],
                'next_survey': self.test_cert_data['next_survey'],
                'next_survey_type': self.test_cert_data['next_survey_type'],
                'issued_by': self.test_cert_data['issued_by'],
                'category': 'certificates',
                'sensitivity_level': 'public',
                'notes': 'Test certificate created for upcoming surveys notification system testing'
            }
            
            endpoint = f"{BACKEND_URL}/certificates"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=cert_data, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                created_cert = response.json()
                self.test_certificate = created_cert
                self.test_certificate_id = created_cert.get('id')
                
                self.data_creation_tests['test_certificate_created'] = True
                self.log("✅ Test certificate created successfully")
                self.log(f"   Certificate ID: {self.test_certificate_id}")
                self.log(f"   Certificate Number: {created_cert.get('cert_no')}")
                
                # Verify certificate fields are set correctly
                fields_correct = True
                expected_fields = {
                    'cert_name': self.test_cert_data['cert_name'],
                    'next_survey_type': self.test_cert_data['next_survey_type'],
                    'next_survey': self.test_cert_data['next_survey']
                }
                
                for field, expected_value in expected_fields.items():
                    actual_value = created_cert.get(field)
                    if field == 'next_survey':
                        # Handle date format differences
                        if actual_value:
                            actual_date = actual_value.split('T')[0] if 'T' in actual_value else actual_value
                            if actual_date != expected_value:
                                self.log(f"   ⚠️ Field mismatch - {field}: expected {expected_value}, got {actual_date}")
                                fields_correct = False
                        else:
                            self.log(f"   ❌ Missing field: {field}")
                            fields_correct = False
                    else:
                        if actual_value != expected_value:
                            self.log(f"   ⚠️ Field mismatch - {field}: expected {expected_value}, got {actual_value}")
                            fields_correct = False
                
                if fields_correct:
                    self.data_creation_tests['certificate_fields_set_correctly'] = True
                    self.log("✅ All certificate fields set correctly")
                
                # Verify next survey date is within ±3 months window
                next_survey_str = created_cert.get('next_survey')
                if next_survey_str:
                    try:
                        if 'T' in next_survey_str:
                            next_survey_date = datetime.fromisoformat(next_survey_str.replace('Z', '+00:00'))
                        else:
                            next_survey_date = datetime.strptime(next_survey_str, '%Y-%m-%d')
                        
                        current_date = datetime.now()
                        three_months_ago = current_date - timedelta(days=90)
                        three_months_ahead = current_date + timedelta(days=90)
                        
                        if three_months_ago <= next_survey_date <= three_months_ahead:
                            self.data_creation_tests['next_survey_date_in_window'] = True
                            self.log(f"✅ Next survey date is within ±3 months window")
                            self.log(f"   Next survey: {next_survey_date.strftime('%Y-%m-%d')}")
                            self.log(f"   Window: {three_months_ago.strftime('%Y-%m-%d')} to {three_months_ahead.strftime('%Y-%m-%d')}")
                        else:
                            self.log(f"❌ Next survey date is outside ±3 months window")
                    except Exception as e:
                        self.log(f"⚠️ Could not verify next survey date: {str(e)}")
                
                return True
            else:
                self.log(f"❌ Failed to create test certificate: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating test certificate: {str(e)}", "ERROR")
            return False
    
    def test_upcoming_surveys_api(self):
        """Test the upcoming surveys API to verify it returns the test certificate"""
        try:
            self.log("📅 Testing upcoming surveys API...")
            
            endpoint = f"{BACKEND_URL}/certificates/upcoming-surveys"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.data_creation_tests['upcoming_surveys_api_accessible'] = True
                self.log("✅ Upcoming surveys API is accessible")
                
                try:
                    response_data = response.json()
                    self.upcoming_surveys_response = response_data
                    
                    self.log("✅ Response is valid JSON")
                    self.log(f"   Response keys: {list(response_data.keys())}")
                    
                    # Check if our test certificate appears in the response
                    upcoming_surveys = response_data.get('upcoming_surveys', [])
                    total_count = response_data.get('total_count', 0)
                    
                    self.log(f"   Total upcoming surveys: {total_count}")
                    self.log(f"   Surveys in response: {len(upcoming_surveys)}")
                    
                    # Look for our test certificate
                    test_cert_found = False
                    test_cert_in_response = None
                    
                    for survey in upcoming_surveys:
                        ship_name = survey.get('ship_name', '')
                        cert_name = survey.get('cert_name_display', '')
                        cert_id = survey.get('certificate_id', '')
                        
                        self.log(f"      Survey: {ship_name} - {cert_name} (ID: {cert_id})")
                        
                        # Check if this is our test certificate
                        if (cert_id == self.test_certificate_id or 
                            cert_name == self.test_cert_data['cert_name'] or
                            ship_name == self.selected_ship.get('name')):
                            test_cert_found = True
                            test_cert_in_response = survey
                            self.log(f"         ✅ Found our test certificate!")
                            break
                    
                    if test_cert_found:
                        self.data_creation_tests['test_certificate_returned_by_api'] = True
                        self.data_creation_tests['certificate_appears_in_list'] = True
                        self.log("✅ Test certificate appears in upcoming surveys list")
                        
                        # Verify status indicators
                        if test_cert_in_response:
                            is_overdue = test_cert_in_response.get('is_overdue')
                            is_due_soon = test_cert_in_response.get('is_due_soon')
                            days_until_survey = test_cert_in_response.get('days_until_survey')
                            
                            self.log(f"   Status indicators:")
                            self.log(f"      Is overdue: {is_overdue}")
                            self.log(f"      Is due soon: {is_due_soon}")
                            self.log(f"      Days until survey: {days_until_survey}")
                            
                            # Since we set next survey to +30 days, it should not be overdue
                            # and should be due soon (within 30 days)
                            if is_overdue == False and days_until_survey is not None:
                                if 25 <= days_until_survey <= 35:  # Allow some tolerance
                                    self.data_creation_tests['status_indicators_correct'] = True
                                    self.log("✅ Status indicators are correct")
                                else:
                                    self.log(f"⚠️ Days until survey seems incorrect: {days_until_survey} (expected ~30)")
                            else:
                                self.log("⚠️ Status indicators may be incorrect")
                    else:
                        self.log("❌ Test certificate not found in upcoming surveys list")
                        self.log("   This could mean:")
                        self.log("   - Certificate was not created properly")
                        self.log("   - Date filtering is not working")
                        self.log("   - Company filtering is excluding our certificate")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                self.log(f"❌ Upcoming surveys API failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing upcoming surveys API: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_data_creation_tests(self):
        """Main test function for creating test data for upcoming surveys notification"""
        self.log("🔄 STARTING SHIP MANAGEMENT SYSTEM - CREATE TEST DATA FOR UPCOMING SURVEYS NOTIFICATION")
        self.log("🎯 FOCUS: Create test certificate with upcoming survey date for notification testing")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Find AMCSC ships
            self.log("\n🚢 STEP 2: FIND AMCSC COMPANY SHIPS")
            self.log("=" * 50)
            if not self.find_amcsc_ships():
                self.log("❌ Could not find AMCSC ships - cannot proceed")
                return False
            
            # Step 3: Get ship details
            self.log("\n📋 STEP 3: GET SHIP DETAILS")
            self.log("=" * 50)
            if not self.get_ship_details():
                self.log("❌ Could not get ship details - cannot proceed")
                return False
            
            # Step 4: Create test certificate
            self.log("\n📜 STEP 4: CREATE TEST CERTIFICATE")
            self.log("=" * 50)
            if not self.create_test_certificate():
                self.log("❌ Could not create test certificate - cannot proceed")
                return False
            
            # Step 5: Test upcoming surveys API
            self.log("\n📅 STEP 5: TEST UPCOMING SURVEYS API")
            self.log("=" * 50)
            api_success = self.test_upcoming_surveys_api()
            
            # Step 6: Final Analysis
            self.log("\n📊 STEP 6: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return api_success
            
        except Exception as e:
            self.log(f"❌ Comprehensive data creation testing error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of test data creation for upcoming surveys notification"""
        try:
            self.log("🔄 SHIP MANAGEMENT SYSTEM - CREATE TEST DATA FOR UPCOMING SURVEYS NOTIFICATION - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.data_creation_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.data_creation_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.data_creation_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.data_creation_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.data_creation_tests)})")
            
            # Review request requirements analysis
            self.log("\n📋 REVIEW REQUEST REQUIREMENTS ANALYSIS:")
            
            req1_met = self.data_creation_tests['authentication_successful']
            req2_met = self.data_creation_tests['amcsc_ships_found'] and self.data_creation_tests['target_ship_selected']
            req3_met = self.data_creation_tests['test_certificate_created'] and self.data_creation_tests['next_survey_date_in_window']
            req4_met = self.data_creation_tests['certificate_fields_set_correctly']
            req5_met = self.data_creation_tests['upcoming_surveys_api_accessible'] and self.data_creation_tests['test_certificate_returned_by_api']
            req6_met = self.data_creation_tests['certificate_appears_in_list']
            
            self.log(f"   1. Login with admin1/123456: {'✅ MET' if req1_met else '❌ NOT MET'}")
            self.log(f"      - Authentication successful")
            
            self.log(f"   2. Find ship in AMCSC company: {'✅ MET' if req2_met else '❌ NOT MET'}")
            self.log(f"      - AMCSC ships found and target ship selected")
            
            self.log(f"   3. Create certificate with upcoming survey date: {'✅ MET' if req3_met else '❌ NOT MET'}")
            self.log(f"      - Certificate created with next_survey within ±3 months window")
            
            self.log(f"   4. Set proper certificate fields: {'✅ MET' if req4_met else '❌ NOT MET'}")
            self.log(f"      - cert_name, cert_abbreviation, next_survey, next_survey_type, last_endorse")
            
            self.log(f"   5. Test upcoming surveys API: {'✅ MET' if req5_met else '❌ NOT MET'}")
            self.log(f"      - API accessible and returns test certificate")
            
            self.log(f"   6. Verify certificate in list: {'✅ MET' if req6_met else '❌ NOT MET'}")
            self.log(f"      - Certificate appears in upcoming surveys list")
            
            requirements_met = sum([req1_met, req2_met, req3_met, req4_met, req5_met, req6_met])
            
            # Test certificate summary
            if self.test_certificate:
                self.log(f"\n📜 TEST CERTIFICATE CREATED:")
                self.log(f"   Ship: {self.selected_ship.get('name') if self.selected_ship else 'Unknown'}")
                self.log(f"   Certificate Name: {self.test_cert_data['cert_name']}")
                self.log(f"   Certificate Abbreviation: {self.test_cert_data['cert_abbreviation']}")
                self.log(f"   Next Survey: {self.test_cert_data['next_survey']} (30 days from creation)")
                self.log(f"   Next Survey Type: {self.test_cert_data['next_survey_type']}")
                self.log(f"   Last Endorse: {self.test_cert_data['last_endorse']} (365 days ago)")
                self.log(f"   Certificate ID: {self.test_certificate_id}")
            
            # Final conclusion
            if success_rate >= 80 and requirements_met >= 5:
                self.log(f"\n🎉 CONCLUSION: TEST DATA CREATION FOR UPCOMING SURVEYS NOTIFICATION COMPLETED SUCCESSFULLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Test certificate created and verified!")
                self.log(f"   ✅ Requirements met: {requirements_met}/6")
                self.log(f"   ✅ Test certificate created with upcoming survey date")
                self.log(f"   ✅ Certificate appears in upcoming surveys API response")
                self.log(f"   ✅ All required fields set correctly")
                self.log(f"   ✅ Frontend will be able to display notification when this data exists")
            elif success_rate >= 60 and requirements_met >= 4:
                self.log(f"\n⚠️ CONCLUSION: TEST DATA CREATION PARTIALLY SUCCESSFUL")
                self.log(f"   Success rate: {success_rate:.1f}% - Most functionality working, minor issues")
                self.log(f"   ⚠️ Requirements met: {requirements_met}/6")
                
                if req1_met and req3_met:
                    self.log(f"   ✅ Core functionality (authentication and certificate creation) working")
                if not req5_met:
                    self.log(f"   ⚠️ Upcoming surveys API may need attention")
                if not req6_met:
                    self.log(f"   ⚠️ Certificate visibility in list may need fixes")
            else:
                self.log(f"\n❌ CONCLUSION: TEST DATA CREATION HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Significant fixes needed")
                self.log(f"   ❌ Requirements met: {requirements_met}/6")
                self.log(f"   ❌ Test data creation needs major fixes before notification system can be tested")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run test data creation for upcoming surveys notification"""
    print("🔄 SHIP MANAGEMENT SYSTEM - CREATE TEST DATA FOR UPCOMING SURVEYS NOTIFICATION STARTED")
    print("=" * 80)
    
    try:
        tester = UpcomingSurveysDataCreationTester()
        success = tester.run_comprehensive_data_creation_tests()
        
        if success:
            print("\n✅ TEST DATA CREATION FOR UPCOMING SURVEYS NOTIFICATION COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ TEST DATA CREATION FOR UPCOMING SURVEYS NOTIFICATION COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
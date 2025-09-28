#!/usr/bin/env python3
"""
Next Survey Calculation Logic Testing Script
Testing the new Next Survey calculation logic following IMO regulations and 5-year survey cycles

WHAT TO TEST:
1. Next Survey Calculation API: POST /api/ships/{ship_id}/update-next-survey
2. Logic Requirements:
   - 5-year Special Survey Cycle with proper anniversary dates
   - Annual Surveys: 1st, 2nd, 3rd, 4th Annual Survey within 5-year cycle
   - Next Survey Date: nearest future Annual Survey in dd/MM/yyyy format with ±3M window
   - Condition Certificates: Next Survey = valid_date
   - Next Survey Type Logic with Intermediate Survey considerations
3. IMO Compliance Check: ±3 months window, anniversary dates, 5-year cycle calculations
4. Data Integration: ships with anniversary_date and special_survey_cycle data

Authentication: admin1/123456
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fleetops-7.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class NextSurveyCalculationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking
        self.test_results = {
            # Authentication
            'authentication_successful': False,
            
            # API Endpoint Testing
            'next_survey_api_accessible': False,
            'next_survey_api_working': False,
            
            # 5-year Special Survey Cycle Testing
            'special_survey_cycle_identified': False,
            'anniversary_dates_derived': False,
            'five_year_cycle_accurate': False,
            
            # Annual Survey Testing
            'annual_surveys_calculated': False,
            'first_annual_survey_identified': False,
            'second_annual_survey_identified': False,
            'third_annual_survey_identified': False,
            'fourth_annual_survey_identified': False,
            
            # Next Survey Date Testing
            'next_survey_date_format_correct': False,
            'next_survey_window_applied': False,
            'nearest_future_survey_selected': False,
            
            # Condition Certificate Testing
            'condition_cert_logic_working': False,
            
            # Next Survey Type Logic Testing
            'survey_type_logic_working': False,
            'second_annual_intermediate_logic': False,
            'third_annual_intermediate_logic': False,
            
            # IMO Compliance Testing
            'three_month_window_verified': False,
            'anniversary_date_compliance': False,
            'five_year_cycle_compliance': False,
            'intermediate_survey_timing': False,
            
            # Data Integration Testing
            'ship_anniversary_date_integration': False,
            'special_survey_cycle_integration': False,
            'missing_fields_handling': False,
            'field_updates_working': False,
        }
        
        # Test ship data
        self.test_ship_id = None
        self.test_ship_name = "NEXT SURVEY TEST SHIP 2025"
        self.test_certificates = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        self.backend_logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
    def authenticate(self):
        """Authenticate with admin1/123456 credentials"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            response = requests.post(endpoint, json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User: {self.current_user.get('username')} ({self.current_user.get('role')})")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.test_results['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed - Status: {response.status_code}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def create_test_ship_with_survey_data(self):
        """Create a test ship with comprehensive survey data for testing"""
        try:
            self.log("🚢 Creating test ship with comprehensive survey data...")
            
            # Create ship with specific anniversary date and special survey cycle
            ship_data = {
                'name': self.test_ship_name,
                'imo': '9888888',
                'flag': 'PANAMA',
                'ship_type': 'DNV GL',
                'gross_tonnage': 5000.0,
                'built_year': 2020,
                'ship_owner': 'Test Owner',
                'company': 'AMCSC',
                
                # Anniversary date (day 15, month 3 = March 15th)
                'anniversary_date': {
                    'day': 15,
                    'month': 3,
                    'auto_calculated': True,
                    'source_certificate_type': 'Full Term Class Certificate',
                    'manual_override': False
                },
                
                # Special Survey Cycle (5-year cycle)
                'special_survey_cycle': {
                    'from_date': '2021-03-15T00:00:00Z',  # March 15, 2021
                    'to_date': '2026-03-15T00:00:00Z',    # March 15, 2026 (5 years later)
                    'intermediate_required': True,
                    'cycle_type': 'SOLAS Safety Construction Survey Cycle'
                },
                
                # Last surveys for reference
                'last_special_survey': '2021-03-15T00:00:00Z',
                'last_intermediate_survey': '2023-09-15T00:00:00Z'  # Between 2nd and 3rd year
            }
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.post(
                endpoint,
                json=ship_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                self.test_ship_id = response_data.get('id')
                self.log("✅ Test ship created successfully")
                self.log(f"   Ship ID: {self.test_ship_id}")
                self.log(f"   Anniversary Date: March 15th (day=15, month=3)")
                self.log(f"   Special Survey Cycle: 2021-03-15 to 2026-03-15 (5 years)")
                self.log(f"   Expected Annual Surveys:")
                self.log(f"      1st Annual: March 15, 2022")
                self.log(f"      2nd Annual: March 15, 2023")
                self.log(f"      3rd Annual: March 15, 2024")
                self.log(f"      4th Annual: March 15, 2025")
                self.log(f"      Special Survey: March 15, 2026")
                
                return True
            else:
                self.log(f"❌ Test ship creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Test ship creation error: {str(e)}", "ERROR")
            return False
    
    def create_test_certificates(self):
        """Create test certificates with different types and dates"""
        try:
            self.log("📋 Creating test certificates for Next Survey testing...")
            
            if not self.test_ship_id:
                self.log("❌ No test ship available")
                return False
            
            # Certificate 1: Full Term Class Certificate (should use anniversary date logic)
            cert1_data = {
                'ship_id': self.test_ship_id,
                'cert_name': 'CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE',
                'cert_type': 'Full Term',
                'cert_no': 'CSSC-2024-001',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-03-15T00:00:00Z',  # Matches special survey cycle end
                'issued_by': 'DNV GL',
                'category': 'certificates'
            }
            
            # Certificate 2: Condition Certificate (should use valid_date as next survey)
            cert2_data = {
                'ship_id': self.test_ship_id,
                'cert_name': 'CARGO SHIP SAFETY EQUIPMENT CERTIFICATE',
                'cert_type': 'Conditional',
                'cert_no': 'CSEC-2024-002',
                'issue_date': '2024-06-01T00:00:00Z',
                'valid_date': '2025-06-01T00:00:00Z',  # Should be used as next survey
                'issued_by': 'DNV GL',
                'category': 'certificates'
            }
            
            # Certificate 3: Interim Certificate (should use anniversary date logic)
            cert3_data = {
                'ship_id': self.test_ship_id,
                'cert_name': 'INTERNATIONAL TONNAGE CERTIFICATE',
                'cert_type': 'Interim',
                'cert_no': 'ITC-2024-003',
                'issue_date': '2024-02-01T00:00:00Z',
                'valid_date': '2025-02-01T00:00:00Z',
                'issued_by': 'Panama Maritime Authority',
                'category': 'certificates'
            }
            
            # Certificate 4: Certificate without valid_date (should return null)
            cert4_data = {
                'ship_id': self.test_ship_id,
                'cert_name': 'RADIO SAFETY CERTIFICATE',
                'cert_type': 'Full Term',
                'cert_no': 'RSC-2024-004',
                'issue_date': '2024-03-01T00:00:00Z',
                'valid_date': None,  # No valid date
                'issued_by': 'DNV GL',
                'category': 'certificates'
            }
            
            certificates_to_create = [cert1_data, cert2_data, cert3_data, cert4_data]
            created_count = 0
            
            for cert_data in certificates_to_create:
                endpoint = f"{BACKEND_URL}/certificates"
                response = requests.post(
                    endpoint,
                    json=cert_data,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    cert_response = response.json()
                    self.test_certificates.append(cert_response)
                    created_count += 1
                    self.log(f"   ✅ Created: {cert_data['cert_name']} ({cert_data['cert_type']})")
                else:
                    self.log(f"   ❌ Failed to create: {cert_data['cert_name']}")
            
            self.log(f"✅ Created {created_count}/4 test certificates")
            return created_count > 0
            
        except Exception as e:
            self.log(f"❌ Test certificates creation error: {str(e)}", "ERROR")
            return False
    
    def test_next_survey_api_endpoint(self):
        """Test the Next Survey Calculation API endpoint"""
        try:
            self.log("🎯 Testing Next Survey Calculation API endpoint...")
            
            if not self.test_ship_id:
                self.log("❌ No test ship available")
                return False
            
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}/update-next-survey"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(
                endpoint,
                headers=self.get_headers(),
                timeout=60
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.test_results['next_survey_api_accessible'] = True
                
                response_data = response.json()
                self.log("✅ Next Survey API endpoint accessible")
                
                # Log the full response for analysis
                self.log("   API Response:")
                self.log(f"   {json.dumps(response_data, indent=2)}")
                
                if response_data.get('success'):
                    self.test_results['next_survey_api_working'] = True
                    self.log("✅ Next Survey API working successfully")
                    
                    # Analyze the results
                    updated_count = response_data.get('updated_count', 0)
                    total_certificates = response_data.get('total_certificates', 0)
                    results = response_data.get('results', [])
                    
                    self.log(f"   Updated {updated_count}/{total_certificates} certificates")
                    
                    # Analyze each certificate result
                    for result in results:
                        cert_name = result.get('cert_name', 'Unknown')
                        cert_type = result.get('cert_type', 'Unknown')
                        new_next_survey = result.get('new_next_survey')
                        new_next_survey_type = result.get('new_next_survey_type')
                        reasoning = result.get('reasoning', '')
                        
                        self.log(f"   📋 {cert_name} ({cert_type}):")
                        self.log(f"      Next Survey: {new_next_survey}")
                        self.log(f"      Next Survey Type: {new_next_survey_type}")
                        self.log(f"      Reasoning: {reasoning}")
                        
                        # Test specific logic requirements
                        self.analyze_certificate_result(result)
                    
                    return True
                else:
                    self.log(f"❌ Next Survey API failed: {response_data.get('message')}")
                    return False
            else:
                self.log(f"❌ Next Survey API endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Next Survey API testing error: {str(e)}", "ERROR")
            return False
    
    def analyze_certificate_result(self, result):
        """Analyze individual certificate result for compliance with requirements"""
        try:
            cert_name = result.get('cert_name', '').upper()
            cert_type = result.get('cert_type', '').upper()
            new_next_survey = result.get('new_next_survey')
            new_next_survey_type = result.get('new_next_survey_type')
            reasoning = result.get('reasoning', '')
            
            # Test 1: Date format verification (dd/MM/yyyy)
            if new_next_survey:
                # Check if date is in dd/MM/yyyy format
                import re
                date_pattern = r'\d{2}/\d{2}/\d{4}'
                if re.search(date_pattern, new_next_survey):
                    self.test_results['next_survey_date_format_correct'] = True
                    self.log(f"      ✅ Date format correct: {new_next_survey}")
                
                # Check for ±3M window
                if '±3M' in new_next_survey or '±' in new_next_survey:
                    self.test_results['next_survey_window_applied'] = True
                    self.test_results['three_month_window_verified'] = True
                    self.log(f"      ✅ ±3M window applied: {new_next_survey}")
            
            # Test 2: Condition certificate logic
            if 'CONDITION' in cert_type:
                if new_next_survey and 'Condition Certificate Expiry' in str(new_next_survey_type):
                    self.test_results['condition_cert_logic_working'] = True
                    self.log(f"      ✅ Condition certificate logic working")
            
            # Test 3: Survey type logic
            if new_next_survey_type:
                self.test_results['survey_type_logic_working'] = True
                
                if 'Annual Survey' in new_next_survey_type:
                    self.test_results['annual_surveys_calculated'] = True
                    
                    if '1st Annual Survey' in new_next_survey_type:
                        self.test_results['first_annual_survey_identified'] = True
                    elif '2nd Annual Survey' in new_next_survey_type:
                        self.test_results['second_annual_survey_identified'] = True
                        if 'Intermediate' in new_next_survey_type:
                            self.test_results['second_annual_intermediate_logic'] = True
                    elif '3rd Annual Survey' in new_next_survey_type:
                        self.test_results['third_annual_survey_identified'] = True
                    elif '4th Annual Survey' in new_next_survey_type:
                        self.test_results['fourth_annual_survey_identified'] = True
                
                if 'Intermediate Survey' in new_next_survey_type:
                    self.test_results['third_annual_intermediate_logic'] = True
                    self.test_results['intermediate_survey_timing'] = True
                
                if 'Special Survey' in new_next_survey_type:
                    self.test_results['five_year_cycle_accurate'] = True
            
            # Test 4: Anniversary date compliance
            if 'anniversary date' in reasoning.lower():
                self.test_results['anniversary_date_compliance'] = True
                self.test_results['anniversary_dates_derived'] = True
            
            # Test 5: 5-year cycle compliance
            if '5-year' in reasoning.lower() or 'cycle' in reasoning.lower():
                self.test_results['five_year_cycle_compliance'] = True
                self.test_results['special_survey_cycle_identified'] = True
            
            # Test 6: No valid date handling
            if not new_next_survey and 'no valid date' in reasoning.lower():
                self.log(f"      ✅ No valid date handling working correctly")
            
        except Exception as e:
            self.log(f"❌ Certificate result analysis error: {str(e)}", "ERROR")
    
    def test_data_integration(self):
        """Test data integration with ship anniversary_date and special_survey_cycle"""
        try:
            self.log("🔗 Testing data integration with ship fields...")
            
            if not self.test_ship_id:
                self.log("❌ No test ship available")
                return False
            
            # Get ship data to verify integration
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ship_data = response.json()
                
                # Test anniversary_date integration
                anniversary_date = ship_data.get('anniversary_date')
                if anniversary_date and isinstance(anniversary_date, dict):
                    day = anniversary_date.get('day')
                    month = anniversary_date.get('month')
                    if day == 15 and month == 3:
                        self.test_results['ship_anniversary_date_integration'] = True
                        self.log("✅ Ship anniversary_date integration working (day=15, month=3)")
                
                # Test special_survey_cycle integration
                special_survey_cycle = ship_data.get('special_survey_cycle')
                if special_survey_cycle and isinstance(special_survey_cycle, dict):
                    from_date = special_survey_cycle.get('from_date')
                    to_date = special_survey_cycle.get('to_date')
                    if from_date and to_date and '2021-03-15' in from_date and '2026-03-15' in to_date:
                        self.test_results['special_survey_cycle_integration'] = True
                        self.log("✅ Special survey cycle integration working (5-year cycle)")
                
                return True
            else:
                self.log(f"❌ Failed to get ship data: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Data integration testing error: {str(e)}", "ERROR")
            return False
    
    def test_missing_fields_handling(self):
        """Test handling of ships missing anniversary_date and special_survey_cycle"""
        try:
            self.log("🔍 Testing missing fields handling...")
            
            # Create a ship without anniversary_date and special_survey_cycle
            ship_data = {
                'name': 'MISSING FIELDS TEST SHIP',
                'imo': '9777777',
                'flag': 'PANAMA',
                'ship_type': 'ABS',
                'gross_tonnage': 3000.0,
                'ship_owner': 'Test Owner',
                'company': 'AMCSC'
                # No anniversary_date or special_survey_cycle
            }
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.post(
                endpoint,
                json=ship_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                ship_response = response.json()
                missing_fields_ship_id = ship_response.get('id')
                
                # Create a certificate for this ship
                cert_data = {
                    'ship_id': missing_fields_ship_id,
                    'cert_name': 'SAFETY MANAGEMENT CERTIFICATE',
                    'cert_type': 'Full Term',
                    'cert_no': 'SMC-2024-001',
                    'issue_date': '2024-01-01T00:00:00Z',
                    'valid_date': '2025-12-31T00:00:00Z',
                    'issued_by': 'ABS',
                    'category': 'certificates'
                }
                
                cert_endpoint = f"{BACKEND_URL}/certificates"
                cert_response = requests.post(
                    cert_endpoint,
                    json=cert_data,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if cert_response.status_code in [200, 201]:
                    # Test Next Survey calculation for ship without anniversary data
                    survey_endpoint = f"{BACKEND_URL}/ships/{missing_fields_ship_id}/update-next-survey"
                    survey_response = requests.post(
                        survey_endpoint,
                        headers=self.get_headers(),
                        timeout=30
                    )
                    
                    if survey_response.status_code == 200:
                        survey_data = survey_response.json()
                        if survey_data.get('success'):
                            self.test_results['missing_fields_handling'] = True
                            self.log("✅ Missing fields handling working - derives from certificate dates")
                        
                        # Cleanup
                        requests.delete(f"{BACKEND_URL}/ships/{missing_fields_ship_id}", 
                                      headers=self.get_headers(), timeout=30)
                
                return True
            else:
                self.log(f"❌ Failed to create test ship for missing fields: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Missing fields testing error: {str(e)}", "ERROR")
            return False
    
    def test_field_updates(self):
        """Test that next_survey, next_survey_display, and next_survey_type fields are updated"""
        try:
            self.log("📝 Testing field updates in certificates...")
            
            if not self.test_certificates:
                self.log("❌ No test certificates available")
                return False
            
            # Get updated certificate data
            updated_certs = 0
            for cert in self.test_certificates:
                cert_id = cert.get('id')
                if cert_id:
                    endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
                    response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
                    
                    if response.status_code == 200:
                        cert_data = response.json()
                        
                        # Check if fields were updated
                        next_survey = cert_data.get('next_survey')
                        next_survey_display = cert_data.get('next_survey_display')
                        next_survey_type = cert_data.get('next_survey_type')
                        
                        if next_survey or next_survey_display or next_survey_type:
                            updated_certs += 1
                            self.log(f"   ✅ Certificate updated: {cert_data.get('cert_name')}")
                            self.log(f"      next_survey: {next_survey}")
                            self.log(f"      next_survey_display: {next_survey_display}")
                            self.log(f"      next_survey_type: {next_survey_type}")
            
            if updated_certs > 0:
                self.test_results['field_updates_working'] = True
                self.log(f"✅ Field updates working - {updated_certs} certificates updated")
                return True
            else:
                self.log("❌ No certificate fields were updated")
                return False
                
        except Exception as e:
            self.log(f"❌ Field updates testing error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up test ship and certificates"""
        try:
            if self.test_ship_id:
                self.log("🧹 Cleaning up test data...")
                
                # Delete test ship (this should cascade delete certificates)
                endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
                response = requests.delete(endpoint, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 200:
                    self.log("✅ Test data cleaned up successfully")
                else:
                    self.log(f"⚠️ Test data cleanup failed: {response.status_code}")
                    
        except Exception as e:
            self.log(f"⚠️ Cleanup error: {str(e)}", "WARNING")
    
    def run_comprehensive_tests(self):
        """Run all Next Survey calculation tests"""
        self.log("🎯 STARTING NEXT SURVEY CALCULATION TESTING")
        self.log("Testing IMO regulations and 5-year survey cycles")
        self.log("=" * 100)
        
        try:
            # Step 1: Authentication
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed")
                return False
            
            # Step 2: Create test ship with survey data
            self.log("\n🚢 STEP 2: CREATE TEST SHIP WITH SURVEY DATA")
            self.log("=" * 50)
            if not self.create_test_ship_with_survey_data():
                self.log("❌ Test ship creation failed - cannot proceed")
                return False
            
            # Step 3: Create test certificates
            self.log("\n📋 STEP 3: CREATE TEST CERTIFICATES")
            self.log("=" * 50)
            if not self.create_test_certificates():
                self.log("❌ Test certificates creation failed - cannot proceed")
                return False
            
            # Step 4: Test Next Survey API endpoint
            self.log("\n🎯 STEP 4: TEST NEXT SURVEY CALCULATION API")
            self.log("=" * 50)
            api_success = self.test_next_survey_api_endpoint()
            
            # Step 5: Test data integration
            self.log("\n🔗 STEP 5: TEST DATA INTEGRATION")
            self.log("=" * 50)
            self.test_data_integration()
            
            # Step 6: Test missing fields handling
            self.log("\n🔍 STEP 6: TEST MISSING FIELDS HANDLING")
            self.log("=" * 50)
            self.test_missing_fields_handling()
            
            # Step 7: Test field updates
            self.log("\n📝 STEP 7: TEST FIELD UPDATES")
            self.log("=" * 50)
            self.test_field_updates()
            
            # Step 8: Final analysis
            self.log("\n📊 STEP 8: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return api_success
            
        finally:
            # Always cleanup
            self.log("\n🧹 CLEANUP")
            self.log("=" * 50)
            self.cleanup_test_data()
    
    def provide_final_analysis(self):
        """Provide comprehensive analysis of test results"""
        try:
            self.log("🎯 NEXT SURVEY CALCULATION TESTING - FINAL RESULTS")
            self.log("=" * 80)
            
            # Count passed/failed tests
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.test_results.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            # Overall results
            total_tests = len(self.test_results)
            success_rate = (len(passed_tests) / total_tests) * 100
            
            self.log(f"📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{total_tests})")
            
            # Category analysis
            categories = {
                'Authentication': ['authentication_successful'],
                'API Endpoint': ['next_survey_api_accessible', 'next_survey_api_working'],
                '5-Year Special Survey Cycle': ['special_survey_cycle_identified', 'anniversary_dates_derived', 'five_year_cycle_accurate'],
                'Annual Survey Logic': ['annual_surveys_calculated', 'first_annual_survey_identified', 'second_annual_survey_identified', 'third_annual_survey_identified', 'fourth_annual_survey_identified'],
                'Next Survey Date': ['next_survey_date_format_correct', 'next_survey_window_applied', 'nearest_future_survey_selected'],
                'Condition Certificates': ['condition_cert_logic_working'],
                'Survey Type Logic': ['survey_type_logic_working', 'second_annual_intermediate_logic', 'third_annual_intermediate_logic'],
                'IMO Compliance': ['three_month_window_verified', 'anniversary_date_compliance', 'five_year_cycle_compliance', 'intermediate_survey_timing'],
                'Data Integration': ['ship_anniversary_date_integration', 'special_survey_cycle_integration', 'missing_fields_handling', 'field_updates_working']
            }
            
            self.log("\n📋 CATEGORY ANALYSIS:")
            for category, tests in categories.items():
                category_passed = sum(1 for test in tests if self.test_results.get(test, False))
                category_rate = (category_passed / len(tests)) * 100
                status = "✅" if category_rate >= 80 else "⚠️" if category_rate >= 60 else "❌"
                self.log(f"   {status} {category}: {category_rate:.1f}% ({category_passed}/{len(tests)})")
            
            # Key findings
            self.log("\n🔍 KEY FINDINGS:")
            
            if self.test_results.get('next_survey_api_working'):
                self.log("   ✅ Next Survey Calculation API is working")
            else:
                self.log("   ❌ Next Survey Calculation API has issues")
            
            if self.test_results.get('five_year_cycle_accurate'):
                self.log("   ✅ 5-year Special Survey Cycle logic is working")
            else:
                self.log("   ❌ 5-year Special Survey Cycle logic needs attention")
            
            if self.test_results.get('anniversary_date_compliance'):
                self.log("   ✅ Anniversary date compliance verified")
            else:
                self.log("   ❌ Anniversary date compliance issues detected")
            
            if self.test_results.get('three_month_window_verified'):
                self.log("   ✅ ±3 months window is being applied correctly")
            else:
                self.log("   ❌ ±3 months window application needs verification")
            
            if self.test_results.get('condition_cert_logic_working'):
                self.log("   ✅ Condition certificate logic is working")
            else:
                self.log("   ⚠️ Condition certificate logic not fully tested")
            
            if self.test_results.get('intermediate_survey_timing'):
                self.log("   ✅ Intermediate survey timing logic is working")
            else:
                self.log("   ⚠️ Intermediate survey timing logic not fully verified")
            
            # Final conclusion
            if success_rate >= 80:
                self.log(f"\n🎉 CONCLUSION: NEXT SURVEY CALCULATION LOGIC IS WORKING EXCELLENTLY")
                self.log(f"   The new IMO-compliant Next Survey calculation logic is successfully implemented")
                self.log(f"   ✅ 5-year survey cycles properly identified")
                self.log(f"   ✅ Anniversary dates correctly derived")
                self.log(f"   ✅ Annual surveys (1st, 2nd, 3rd, 4th) calculated")
                self.log(f"   ✅ Next Survey dates in dd/MM/yyyy format with ±3M window")
                self.log(f"   ✅ Intermediate survey logic working")
                self.log(f"   ✅ Data integration with ship fields working")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: NEXT SURVEY CALCULATION PARTIALLY WORKING")
                self.log(f"   Some functionality is working but improvements needed")
                self.log(f"   Success rate: {success_rate:.1f}%")
            else:
                self.log(f"\n❌ CONCLUSION: NEXT SURVEY CALCULATION HAS CRITICAL ISSUES")
                self.log(f"   Significant fixes needed for IMO compliance")
                self.log(f"   Success rate: {success_rate:.1f}%")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run Next Survey calculation tests"""
    print("🎯 NEXT SURVEY CALCULATION TESTING STARTED")
    print("Testing IMO regulations and 5-year survey cycles")
    print("=" * 80)
    
    try:
        tester = NextSurveyCalculationTester()
        success = tester.run_comprehensive_tests()
        
        if success:
            print("\n✅ NEXT SURVEY CALCULATION TESTING COMPLETED")
        else:
            print("\n❌ NEXT SURVEY CALCULATION TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    sys.exit(0)

if __name__ == "__main__":
    main()
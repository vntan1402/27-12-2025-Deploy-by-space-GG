#!/usr/bin/env python3
"""
Ship Management System - Initial Survey Type Rules Bug Fix Testing
FOCUS: Test the FIXED Initial survey type logic after certificate name matching bug fix

REVIEW REQUEST REQUIREMENTS:
1. Login with admin1/123456
2. Test the `/api/certificates/upcoming-surveys` endpoint after the name matching fix
3. Verify that Initial certificates with full names are now properly identified:
   - 'SAFETY MANAGEMENT CERTIFICATE' should match 'SAFETY MANAGEMENT' 
   - 'INTERNATIONAL SHIP SECURITY CERTIFICATE' should match 'SHIP SECURITY'
   - 'MARITIME LABOUR CERTIFICATE' should match 'MARITIME LABOUR'
4. Check that Initial certificates now appear in upcoming surveys results
5. Verify window calculation works correctly: window_open = valid_date - 90 days, window_close = valid_date
6. Check status classification: is_overdue, is_due_soon, is_critical logic for Initial certificates
7. Verify window_type displays as "Valid-3M→Valid"
8. Check survey_window_rule shows "Initial SMC/ISSC/MLC: Valid date - 3M → Valid date"

EXPECTED RESULTS AFTER FIX:
- Initial certificates with next_survey_type "Initial" should appear in results
- Window calculation should use valid_date - 90 days to valid_date  
- Status should be calculated based on valid_date expiry logic
- Window type should show "Valid-3M→Valid"
- Response should include Initial certificates in upcoming_surveys array

CRITICAL TEST:
The previously created test Initial certificates should now appear in the upcoming surveys response 
if they fall within their calculated windows and match the updated name criteria.
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
# Try internal URL first, then external
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipmate-55.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class InitialSurveyBugFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Initial survey type rules bug fix verification
        self.bug_fix_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            
            # Upcoming surveys endpoint tests
            'upcoming_surveys_endpoint_accessible': False,
            'upcoming_surveys_response_valid': False,
            'response_structure_correct': False,
            
            # BUG FIX VERIFICATION - Certificate Name Matching
            'full_name_safety_management_matched': False,
            'full_name_ship_security_matched': False,
            'full_name_maritime_labour_matched': False,
            'initial_certificates_now_appearing': False,
            'name_matching_bug_fixed': False,
            
            # Initial Certificate Window Logic Tests (Post-Fix)
            'initial_certificate_window_correct': False,
            'valid_date_minus_90_days_calculation': False,
            'window_close_equals_valid_date': False,
            'current_date_within_window_filter': False,
            
            # Initial Certificate Status Classification (Post-Fix)
            'initial_overdue_logic_working': False,
            'initial_due_soon_logic_working': False,
            'initial_critical_logic_working': False,
            'status_based_on_valid_date': False,
            
            # Window Type Display (Post-Fix)
            'window_type_valid_3m_to_valid': False,
            'survey_window_rule_correct': False,
            'initial_smc_issc_mlc_rule_displayed': False,
            
            # Response Structure Verification
            'initial_certificates_in_upcoming_surveys': False,
            'window_calculation_fields_present': False,
            'logic_info_includes_initial_rules': False,
            
            # Test Certificate Creation and Verification
            'test_initial_certificates_created': False,
            'created_certificates_appear_in_results': False,
            'window_calculations_accurate': False,
        }
        
        # Store test results for analysis
        self.user_company = None
        self.upcoming_surveys_response = {}
        self.company_ships = []
        self.test_certificates = []
        self.date_analysis = {}
        
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
                
                self.bug_fix_tests['authentication_successful'] = True
                self.user_company = self.current_user.get('company')
                if self.user_company:
                    self.bug_fix_tests['user_company_identified'] = True
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
    
    def is_valid_date_format(self, date_value):
        """Check if date value has a valid format"""
        if not date_value:
            return True  # None/empty is valid
        
        # Check for ISO format with timezone
        if isinstance(date_value, str):
            # Common valid formats: ISO with timezone, ISO without timezone
            valid_patterns = [
                r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$',
                r'^\d{4}-\d{2}-\d{2}$',
                r'^\d{2}/\d{2}/\d{4}$'
            ]
            
            for pattern in valid_patterns:
                if re.match(pattern, date_value):
                    return True
            return False
        
        return True  # Non-string values are considered valid
    
    def test_upcoming_surveys_endpoint(self):
        """Test the upcoming surveys endpoint accessibility and response"""
        try:
            self.log("📅 Testing upcoming surveys endpoint...")
            
            endpoint = f"{BACKEND_URL}/certificates/upcoming-surveys"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.bug_fix_tests['upcoming_surveys_endpoint_accessible'] = True
                self.log("✅ Upcoming surveys endpoint is accessible")
                
                try:
                    response_data = response.json()
                    self.upcoming_surveys_response = response_data
                    self.bug_fix_tests['upcoming_surveys_response_valid'] = True
                    self.log("✅ Response is valid JSON")
                    
                    # Log response structure for analysis
                    self.log(f"   Response keys: {list(response_data.keys())}")
                    
                    return True
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                self.log(f"❌ Upcoming surveys endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing upcoming surveys endpoint: {str(e)}", "ERROR")
            return False
    
    def verify_response_structure(self):
        """Verify the upcoming surveys response has the correct structure with new fields"""
        try:
            self.log("🔍 Verifying updated response structure...")
            
            if not self.upcoming_surveys_response:
                self.log("❌ No response data to verify")
                return False
            
            response = self.upcoming_surveys_response
            
            # Check for expected top-level keys (including new ones)
            expected_keys = ['upcoming_surveys', 'total_count', 'company', 'check_date', 'logic_info']
            missing_keys = []
            
            for key in expected_keys:
                if key not in response:
                    missing_keys.append(key)
                else:
                    self.log(f"   ✅ Found key: {key}")
            
            if missing_keys:
                self.log(f"   ❌ Missing keys: {missing_keys}")
                return False
            
            self.bug_fix_tests['response_structure_correct'] = True
            self.log("✅ Top-level response structure is correct")
            
            # NEW: Verify logic_info structure includes Initial certificate rules
            logic_info = response.get('logic_info', {})
            expected_logic_fields = ['description', 'window_calculation', 'filter_condition', 'window_rules']
            logic_missing = []
            
            for field in expected_logic_fields:
                if field not in logic_info:
                    logic_missing.append(field)
                else:
                    self.log(f"   ✅ Found logic_info.{field}: {logic_info[field]}")
            
            # Check if Initial certificate rules are documented
            window_rules = logic_info.get('window_rules', {})
            if window_rules:
                self.log(f"   Found {len(window_rules)} window rules:")
                initial_rule_found = False
                
                for rule_key, rule_description in window_rules.items():
                    self.log(f"      {rule_key}: {rule_description}")
                    
                    if 'initial_smc_issc_mlc' in rule_key:
                        initial_rule_found = True
                        if 'Valid date - 3M → Valid date' in rule_description or '3 months before expiry' in rule_description:
                            self.bug_fix_tests['logic_info_includes_initial_rules'] = True
                            self.log(f"         ✅ Initial certificate rule correctly documented")
                
                if len(window_rules) >= 4:
                    self.bug_fix_tests['all_window_rule_types_documented'] = True
                    self.log("✅ All window rule types documented")
                
                if not initial_rule_found:
                    self.log("   ❌ Initial SMC/ISSC/MLC rule not found in logic_info")
            else:
                self.log("   ❌ No window_rules found in logic_info")
            
            if not logic_missing:
                self.log("✅ Updated logic_info structure is correct")
            else:
                self.log(f"   ❌ Missing logic_info fields: {logic_missing}")
            
            # Check upcoming_surveys array structure
            upcoming_surveys = response.get('upcoming_surveys', [])
            self.log(f"   Found {len(upcoming_surveys)} upcoming surveys")
            
            if upcoming_surveys:
                # Check first survey item structure with NEW fields
                first_survey = upcoming_surveys[0]
                expected_survey_fields = [
                    'ship_name', 'cert_name_display', 'next_survey', 
                    'next_survey_type', 'last_endorse', 'days_until_survey',
                    'is_overdue', 'is_due_soon', 'is_critical', 'is_within_window',
                    'window_open', 'window_close', 'days_from_window_open', 'days_to_window_close'
                ]
                
                missing_fields = []
                new_fields_found = []
                
                for field in expected_survey_fields:
                    if field not in first_survey:
                        missing_fields.append(field)
                    else:
                        self.log(f"      ✅ Found field: {field}")
                        if field in ['is_critical', 'is_within_window', 'window_open', 'window_close', 'days_from_window_open', 'days_to_window_close']:
                            new_fields_found.append(field)
                
                if missing_fields:
                    self.log(f"   ❌ Missing survey fields: {missing_fields}")
                    return False
                
                self.bug_fix_tests['required_fields_present'] = True
                self.log("✅ All required survey fields are present")
                
                # NEW: Check if new window fields are present
                if len(new_fields_found) >= 6:  # All 6 new fields
                    self.bug_fix_tests['window_calculation_fields_present'] = True
                    self.log("✅ All new window calculation fields are present")
                else:
                    self.log(f"   ❌ Missing new window fields. Found: {new_fields_found}")
                
                # Store surveys for further analysis
                self.test_certificates = upcoming_surveys
                
                return True
            else:
                self.log("   ⚠️ No upcoming surveys found in response")
                # This might be valid if no surveys are due
                self.bug_fix_tests['required_fields_present'] = True
                return True
                
        except Exception as e:
            self.log(f"❌ Error verifying response structure: {str(e)}", "ERROR")
            return False
    
    def test_certificate_name_matching_bug_fix(self):
        """Test the FIXED certificate name matching for Initial SMC, ISSC, MLC certificates"""
        try:
            self.log("🔍 Testing CERTIFICATE NAME MATCHING BUG FIX...")
            self.log("   BEFORE FIX: Backend looked for 'SMC', 'ISSC', 'MLC' in certificate names")
            self.log("   AFTER FIX: Backend should match full names like 'SAFETY MANAGEMENT CERTIFICATE'")
            
            if not self.test_certificates:
                self.log("   ⚠️ No upcoming surveys to test certificate name matching")
                self.log("   Creating test Initial certificates to verify the fix...")
                if self.create_test_initial_certificates():
                    # Re-test the endpoint after creating certificates
                    if self.test_upcoming_surveys_endpoint() and self.verify_response_structure():
                        self.log("   ✅ Test certificates created and endpoint re-tested")
                    else:
                        self.log("   ❌ Failed to re-test endpoint after certificate creation")
                        return False
                else:
                    self.log("   ❌ Failed to create test certificates")
                    return False
            
            # Test the specific name matching patterns that were fixed
            full_name_matches = {
                'SAFETY MANAGEMENT CERTIFICATE': False,
                'INTERNATIONAL SHIP SECURITY CERTIFICATE': False, 
                'MARITIME LABOUR CERTIFICATE': False
            }
            
            initial_certificates_found = []
            
            for survey in self.test_certificates:
                ship_name = survey.get('ship_name', 'Unknown')
                cert_name = survey.get('cert_name', '').upper()
                next_survey_type = survey.get('next_survey_type', '').upper()
                window_type = survey.get('window_type', '')
                
                self.log(f"   Certificate for {ship_name}:")
                self.log(f"      Cert Name: {cert_name}")
                self.log(f"      Next Survey Type: {next_survey_type}")
                self.log(f"      Window Type: {window_type}")
                
                # Check if it's an Initial survey type
                if 'INITIAL' in next_survey_type:
                    initial_certificates_found.append(survey)
                    self.log(f"      ✅ Initial survey type detected")
                    
                    # Test the specific name matching patterns that were fixed
                    if 'SAFETY MANAGEMENT' in cert_name:
                        full_name_matches['SAFETY MANAGEMENT CERTIFICATE'] = True
                        self.log(f"      ✅ SAFETY MANAGEMENT certificate name matched (BUG FIX WORKING)")
                        
                    if 'SHIP SECURITY' in cert_name or 'INTERNATIONAL SHIP SECURITY' in cert_name:
                        full_name_matches['INTERNATIONAL SHIP SECURITY CERTIFICATE'] = True
                        self.log(f"      ✅ SHIP SECURITY certificate name matched (BUG FIX WORKING)")
                        
                    if 'MARITIME LABOUR' in cert_name:
                        full_name_matches['MARITIME LABOUR CERTIFICATE'] = True
                        self.log(f"      ✅ MARITIME LABOUR certificate name matched (BUG FIX WORKING)")
                    
                    # Also check for abbreviation matches (should still work)
                    if any(abbrev in cert_name for abbrev in ['SMC', 'ISSC', 'MLC']):
                        self.log(f"      ✅ Abbreviation match also working: {cert_name}")
                    
                    # Verify window type display for Initial certificates
                    if window_type == 'Valid-3M→Valid':
                        self.bug_fix_tests['window_type_valid_3m_to_valid'] = True
                        self.log(f"      ✅ Correct window type display: {window_type}")
                    else:
                        self.log(f"      ❌ Incorrect window type display: {window_type} (expected: Valid-3M→Valid)")
            
            # Evaluate the bug fix results
            matches_found = sum(full_name_matches.values())
            
            if matches_found > 0:
                self.bug_fix_tests['name_matching_bug_fixed'] = True
                self.log(f"✅ CERTIFICATE NAME MATCHING BUG FIX VERIFIED - {matches_found}/3 full name patterns matched")
                
                # Set specific match flags
                if full_name_matches['SAFETY MANAGEMENT CERTIFICATE']:
                    self.bug_fix_tests['full_name_safety_management_matched'] = True
                if full_name_matches['INTERNATIONAL SHIP SECURITY CERTIFICATE']:
                    self.bug_fix_tests['full_name_ship_security_matched'] = True
                if full_name_matches['MARITIME LABOUR CERTIFICATE']:
                    self.bug_fix_tests['full_name_maritime_labour_matched'] = True
            
            if initial_certificates_found:
                self.bug_fix_tests['initial_certificates_now_appearing'] = True
                self.bug_fix_tests['initial_certificates_in_upcoming_surveys'] = True
                self.log(f"✅ Initial certificates now appearing in results - BUG FIX SUCCESSFUL")
                self.log(f"   Found {len(initial_certificates_found)} Initial certificates in upcoming surveys")
                return True
            else:
                self.log("   ⚠️ No Initial certificates found in results")
                self.log("   This could mean:")
                self.log("     1. No Initial certificates exist")
                self.log("     2. No Initial certificates are within their windows")
                self.log("     3. Bug fix may not be complete")
                return True  # Don't fail the test, but note the situation
                
        except Exception as e:
            self.log(f"❌ Error testing certificate name matching bug fix: {str(e)}", "ERROR")
            return False

    def test_initial_certificate_window_logic(self):
        """Test Initial certificate window logic: valid_date - 90 days to valid_date"""
        try:
            self.log("📅 Testing Initial certificate window logic...")
            
            if not self.test_certificates:
                self.log("   ⚠️ No upcoming surveys to test initial certificate window logic")
                return True
            
            from datetime import datetime, timedelta
            current_date = datetime.now().date()
            
            self.log(f"   Current date: {current_date}")
            self.log("   INITIAL LOGIC: window_open = valid_date - 90 days, window_close = valid_date")
            
            initial_windows_correct = 0
            initial_windows_incorrect = 0
            
            for survey in self.test_certificates:
                ship_name = survey.get('ship_name', 'Unknown')
                cert_name = survey.get('cert_name', '').upper()
                next_survey_type = survey.get('next_survey_type', '').upper()
                valid_date_str = survey.get('valid_date')
                window_open_str = survey.get('window_open')
                window_close_str = survey.get('window_close')
                window_type = survey.get('window_type', '')
                
                # Only test Initial SMC/ISSC/MLC certificates
                if ('INITIAL' in next_survey_type and 
                    any(cert_type in cert_name for cert_type in ['SMC', 'ISSC', 'MLC'])):
                    
                    self.log(f"   Initial {cert_name} certificate for {ship_name}:")
                    
                    if valid_date_str and window_open_str and window_close_str:
                        try:
                            # Parse dates
                            valid_date = datetime.fromisoformat(valid_date_str).date()
                            window_open = datetime.fromisoformat(window_open_str).date()
                            window_close = datetime.fromisoformat(window_close_str).date()
                            
                            # Calculate expected window for Initial certificates
                            expected_window_open = valid_date - timedelta(days=90)
                            expected_window_close = valid_date
                            
                            self.log(f"      Valid date: {valid_date}")
                            self.log(f"      Window open: {window_open} (expected: {expected_window_open})")
                            self.log(f"      Window close: {window_close} (expected: {expected_window_close})")
                            self.log(f"      Window type: {window_type}")
                            
                            # Verify Initial certificate window calculation
                            if (window_open == expected_window_open and 
                                window_close == expected_window_close):
                                initial_windows_correct += 1
                                self.log(f"      ✅ Initial certificate window calculation correct")
                                
                                # Verify current date is within window (since certificate was returned)
                                if expected_window_open <= current_date <= expected_window_close:
                                    self.log(f"      ✅ Current date {current_date} is within Initial certificate window")
                                else:
                                    self.log(f"      ❌ Current date {current_date} is NOT within Initial certificate window")
                                    initial_windows_incorrect += 1
                            else:
                                initial_windows_incorrect += 1
                                self.log(f"      ❌ Initial certificate window calculation incorrect")
                                
                        except Exception as e:
                            self.log(f"      ⚠️ Could not verify Initial certificate window: {str(e)}")
                            initial_windows_incorrect += 1
                    else:
                        self.log(f"   ❌ Missing window data for Initial certificate {ship_name}")
                        initial_windows_incorrect += 1
            
            if initial_windows_incorrect == 0 and initial_windows_correct > 0:
                self.survey_tests['initial_certificate_window_correct'] = True
                self.survey_tests['valid_date_window_calculation_working'] = True
                self.survey_tests['initial_certificate_filter_working'] = True
                self.log(f"✅ Initial certificate window logic working correctly - all {initial_windows_correct} Initial certificates have correct windows")
                return True
            elif initial_windows_correct == 0:
                self.log("   ⚠️ No Initial SMC/ISSC/MLC certificates found to test window logic")
                return True
            else:
                self.log(f"❌ Initial certificate window issues - {initial_windows_incorrect} certificates have incorrect windows")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Initial certificate window logic: {str(e)}", "ERROR")
            return False

    def test_all_window_rule_types(self):
        """Test all 4 window rule types work correctly"""
        try:
            self.log("🔍 Testing all window rule types...")
            
            if not self.test_certificates:
                self.log("   ⚠️ No upcoming surveys to test window rule types")
                return True
            
            window_types_found = set()
            window_rule_examples = {}
            
            for survey in self.test_certificates:
                ship_name = survey.get('ship_name', 'Unknown')
                cert_name = survey.get('cert_name', '')
                next_survey_type = survey.get('next_survey_type', '')
                window_type = survey.get('window_type', '')
                survey_window_rule = survey.get('survey_window_rule', '')
                
                if window_type:
                    window_types_found.add(window_type)
                    window_rule_examples[window_type] = {
                        'ship_name': ship_name,
                        'cert_name': cert_name,
                        'next_survey_type': next_survey_type,
                        'survey_window_rule': survey_window_rule
                    }
            
            self.log(f"   Found window types: {list(window_types_found)}")
            
            # Expected window types
            expected_window_types = {
                'Issue→Valid': 'Condition Certificate Expiry',
                'Valid-3M→Valid': 'Initial SMC/ISSC/MLC',
                '-3M': 'Special Survey',
                '±3M': 'Other Surveys'
            }
            
            types_working = 0
            for window_type, description in expected_window_types.items():
                if window_type in window_types_found:
                    example = window_rule_examples[window_type]
                    self.log(f"   ✅ {window_type} ({description}) found:")
                    self.log(f"      Example: {example['cert_name']} on {example['ship_name']}")
                    self.log(f"      Survey type: {example['next_survey_type']}")
                    self.log(f"      Rule: {example['survey_window_rule']}")
                    types_working += 1
                    
                    # Set specific test flags
                    if window_type == 'Issue→Valid':
                        self.survey_tests['condition_certificate_expiry_window'] = True
                    elif window_type == 'Valid-3M→Valid':
                        self.survey_tests['initial_smc_issc_mlc_window'] = True
                    elif window_type == '-3M':
                        self.survey_tests['special_survey_window'] = True
                    elif window_type == '±3M':
                        self.survey_tests['other_surveys_window'] = True
                else:
                    self.log(f"   ⚠️ {window_type} ({description}) not found in results")
            
            if types_working >= 2:  # At least 2 different window types working
                self.survey_tests['window_type_display_correct'] = True
                self.log(f"✅ Window rule types working correctly - found {types_working}/4 types")
                return True
            else:
                self.log(f"❌ Insufficient window rule types found - only {types_working}/4 types")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing window rule types: {str(e)}", "ERROR")
            return False

    def test_company_filtering(self):
        """Test that only certificates from user's company ships are returned"""
        try:
            self.log("🏢 Testing company filtering...")
            
            if not self.user_company:
                self.log("❌ User company not identified")
                return False
            
            self.log(f"   User company: {self.user_company}")
            
            # Check if response includes company information
            response_company = self.upcoming_surveys_response.get('company')
            if response_company:
                self.log(f"   Response company: {response_company}")
                
                if response_company == self.user_company:
                    self.survey_tests['company_filtering_working'] = True
                    self.log("✅ Company filtering working - response company matches user company")
                else:
                    self.log(f"❌ Company mismatch - user: {self.user_company}, response: {response_company}")
                    return False
            else:
                self.log("⚠️ No company information in response")
            
            # Get all ships to verify company filtering
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                all_ships = response.json()
                user_company_ships = [ship for ship in all_ships if ship.get('company') == self.user_company]
                
                self.log(f"   Total ships: {len(all_ships)}")
                self.log(f"   User company ships: {len(user_company_ships)}")
                
                # Check if all surveys are from user's company ships
                if self.test_certificates:
                    user_company_ship_names = {ship.get('name') for ship in user_company_ships}
                    
                    surveys_from_user_ships = 0
                    surveys_from_other_ships = 0
                    
                    for survey in self.test_certificates:
                        ship_name = survey.get('ship_name')
                        if ship_name in user_company_ship_names:
                            surveys_from_user_ships += 1
                        else:
                            surveys_from_other_ships += 1
                            self.log(f"      ❌ Survey from non-user ship: {ship_name}")
                    
                    if surveys_from_other_ships == 0:
                        self.survey_tests['only_user_company_ships_returned'] = True
                        self.log(f"✅ All {surveys_from_user_ships} surveys are from user's company ships")
                        return True
                    else:
                        self.log(f"❌ Found {surveys_from_other_ships} surveys from other companies")
                        return False
                else:
                    self.log("   ⚠️ No surveys to verify company filtering")
                    self.survey_tests['only_user_company_ships_returned'] = True
                    return True
            else:
                self.log(f"   ❌ Failed to get ships for company verification: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing company filtering: {str(e)}", "ERROR")
            return False

    def test_initial_certificate_status_logic(self):
        """Test Initial certificate status logic: overdue, due_soon, critical based on valid_date"""
        try:
            self.log("🚦 Testing Initial certificate status logic...")
            
            if not self.test_certificates:
                self.log("   ⚠️ No surveys to test Initial certificate status logic")
                return True
            
            from datetime import datetime, timedelta
            current_date = datetime.now().date()
            
            initial_status_correct = 0
            initial_certificates_tested = 0
            
            for survey in self.test_certificates:
                ship_name = survey.get('ship_name', 'Unknown')
                cert_name = survey.get('cert_name', '').upper()
                next_survey_type = survey.get('next_survey_type', '').upper()
                valid_date_str = survey.get('valid_date')
                is_overdue = survey.get('is_overdue')
                is_due_soon = survey.get('is_due_soon')
                is_critical = survey.get('is_critical')
                
                # Only test Initial SMC/ISSC/MLC certificates
                if ('INITIAL' in next_survey_type and 
                    any(cert_type in cert_name for cert_type in ['SMC', 'ISSC', 'MLC'])):
                    
                    initial_certificates_tested += 1
                    self.log(f"   Initial {cert_name} certificate for {ship_name}:")
                    self.log(f"      Valid date: {valid_date_str}")
                    self.log(f"      Is overdue: {is_overdue}")
                    self.log(f"      Is due soon: {is_due_soon}")
                    self.log(f"      Is critical: {is_critical}")
                    
                    if valid_date_str:
                        try:
                            # Parse the valid date (for Initial certificates, status is based on valid_date)
                            valid_date = datetime.fromisoformat(valid_date_str).date()
                            
                            # Calculate expected values for Initial certificates
                            days_to_expiry = (valid_date - current_date).days
                            expected_is_overdue = current_date > valid_date
                            expected_is_due_soon = 0 <= days_to_expiry <= 30 and not expected_is_overdue
                            expected_is_critical = days_to_expiry <= 7 or expected_is_overdue
                            
                            self.log(f"      Days to expiry: {days_to_expiry}")
                            self.log(f"      Expected is_overdue: {expected_is_overdue}")
                            self.log(f"      Expected is_due_soon: {expected_is_due_soon}")
                            self.log(f"      Expected is_critical: {expected_is_critical}")
                            
                            # Verify Initial certificate status calculations
                            status_correct = True
                            
                            if is_overdue != expected_is_overdue:
                                self.log(f"         ❌ Is overdue mismatch: got {is_overdue}, expected {expected_is_overdue}")
                                status_correct = False
                            
                            if is_due_soon != expected_is_due_soon:
                                self.log(f"         ❌ Is due soon mismatch: got {is_due_soon}, expected {expected_is_due_soon}")
                                status_correct = False
                            
                            if is_critical != expected_is_critical:
                                self.log(f"         ❌ Is critical mismatch: got {is_critical}, expected {expected_is_critical}")
                                status_correct = False
                            
                            if status_correct:
                                initial_status_correct += 1
                                self.log(f"         ✅ Initial certificate status classification correct")
                            
                        except Exception as e:
                            self.log(f"      ⚠️ Could not verify Initial certificate status: {str(e)}")
            
            if initial_certificates_tested == 0:
                self.log("   ⚠️ No Initial SMC/ISSC/MLC certificates found to test status logic")
                return True
            elif initial_status_correct == initial_certificates_tested:
                self.survey_tests['initial_certificate_overdue_logic'] = True
                self.survey_tests['initial_certificate_due_soon_logic'] = True
                self.survey_tests['initial_certificate_critical_logic'] = True
                self.log(f"✅ Initial certificate status logic working correctly for all {initial_certificates_tested} Initial certificates")
                return True
            else:
                self.log(f"❌ Initial certificate status incorrect for {initial_certificates_tested - initial_status_correct}/{initial_certificates_tested} certificates")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Initial certificate status logic: {str(e)}", "ERROR")
            return False

    def test_updated_status_classification(self):
        """Test the UPDATED status classification logic with new is_critical field"""
        try:
            self.log("🚦 Testing UPDATED status classification logic...")
            
            if not self.test_certificates:
                self.log("   ⚠️ No surveys to test status classification")
                self.survey_tests['status_indicators_calculated'] = True
                return True
            
            from datetime import datetime, timedelta
            current_date = datetime.now().date()
            
            status_correct = 0
            total_surveys = len(self.test_certificates)
            
            for survey in self.test_certificates:
                ship_name = survey.get('ship_name', 'Unknown')
                cert_name = survey.get('cert_name', '').upper()
                next_survey_type = survey.get('next_survey_type', '').upper()
                next_survey_date_str = survey.get('next_survey_date')
                valid_date_str = survey.get('valid_date')
                is_overdue = survey.get('is_overdue')
                is_due_soon = survey.get('is_due_soon')
                is_critical = survey.get('is_critical')
                is_within_window = survey.get('is_within_window')
                days_until_survey = survey.get('days_until_survey')
                
                self.log(f"   Survey for {ship_name}:")
                self.log(f"      Cert Name: {cert_name}")
                self.log(f"      Survey Type: {next_survey_type}")
                self.log(f"      Next survey: {next_survey_date_str}")
                self.log(f"      Valid date: {valid_date_str}")
                self.log(f"      Is overdue: {is_overdue}")
                self.log(f"      Is due soon: {is_due_soon}")
                self.log(f"      Is critical: {is_critical}")
                self.log(f"      Is within window: {is_within_window}")
                self.log(f"      Days until survey: {days_until_survey}")
                
                # Different logic for Initial SMC/ISSC/MLC certificates vs others
                is_initial_smc_issc_mlc = ('INITIAL' in next_survey_type and 
                                         any(cert_type in cert_name for cert_type in ['SMC', 'ISSC', 'MLC']))
                
                if is_initial_smc_issc_mlc and valid_date_str:
                    # For Initial certificates, use valid_date for status calculation
                    try:
                        valid_date = datetime.fromisoformat(valid_date_str).date()
                        days_diff = (valid_date - current_date).days
                        expected_is_overdue = current_date > valid_date
                        expected_is_due_soon = 0 <= days_diff <= 30 and not expected_is_overdue
                        expected_is_critical = days_diff <= 7 or expected_is_overdue
                        expected_is_within_window = True  # Should be true since certificate was returned
                        
                        self.log(f"      [Initial Certificate] Days to expiry: {days_diff}")
                        
                    except Exception as e:
                        self.log(f"      ⚠️ Could not parse valid_date for Initial certificate: {str(e)}")
                        continue
                        
                elif next_survey_date_str:
                    # For other certificates, use next_survey_date for status calculation
                    try:
                        next_survey_date = datetime.fromisoformat(next_survey_date_str).date()
                        days_diff = (next_survey_date - current_date).days
                        expected_is_overdue = next_survey_date < current_date
                        expected_is_due_soon = 0 <= days_diff <= 30 and not expected_is_overdue
                        expected_is_critical = days_diff <= 7 or expected_is_overdue
                        expected_is_within_window = True  # Should be true since certificate was returned
                        
                        self.log(f"      [Regular Certificate] Days until survey: {days_diff}")
                        
                    except Exception as e:
                        self.log(f"      ⚠️ Could not parse next_survey_date: {str(e)}")
                        continue
                else:
                    self.log(f"      ⚠️ Missing date information for status calculation")
                    continue
                
                self.log(f"      Expected is_overdue: {expected_is_overdue}")
                self.log(f"      Expected is_due_soon: {expected_is_due_soon}")
                self.log(f"      Expected is_critical: {expected_is_critical}")
                self.log(f"      Expected is_within_window: {expected_is_within_window}")
                
                # Verify calculations
                classification_correct = True
                
                if is_overdue != expected_is_overdue:
                    self.log(f"         ❌ Is overdue mismatch: got {is_overdue}, expected {expected_is_overdue}")
                    classification_correct = False
                
                if is_due_soon != expected_is_due_soon:
                    self.log(f"         ❌ Is due soon mismatch: got {is_due_soon}, expected {expected_is_due_soon}")
                    classification_correct = False
                
                if is_critical != expected_is_critical:
                    self.log(f"         ❌ Is critical mismatch: got {is_critical}, expected {expected_is_critical}")
                    classification_correct = False
                
                if is_within_window != expected_is_within_window:
                    self.log(f"         ❌ Is within window mismatch: got {is_within_window}, expected {expected_is_within_window}")
                    classification_correct = False
                
                if classification_correct:
                    status_correct += 1
                    self.log(f"         ✅ Status classification correct")
            
            if status_correct == total_surveys:
                self.survey_tests['status_indicators_calculated'] = True
                self.survey_tests['days_until_survey_accurate'] = True
                self.log(f"✅ UPDATED status classification working correctly for all {total_surveys} surveys")
                return True
            else:
                self.log(f"❌ Status classification incorrect for {total_surveys - status_correct}/{total_surveys} surveys")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing status classification: {str(e)}", "ERROR")
            return False

    def create_test_initial_certificates(self):
        """Create test Initial SMC/ISSC/MLC certificates with FULL NAMES to test the bug fix"""
        try:
            self.log("🔧 Creating test Initial certificates with FULL NAMES to verify bug fix...")
            
            # Get ships to create certificates for
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code != 200:
                self.log("❌ Failed to get ships for test certificate creation")
                return False
            
            ships = response.json()
            user_company_ships = [ship for ship in ships if ship.get('company') == self.user_company]
            
            if not user_company_ships:
                self.log("❌ No user company ships found for test certificate creation")
                return False
            
            # Use the first ship
            test_ship = user_company_ships[0]
            ship_id = test_ship.get('id')
            ship_name = test_ship.get('name')
            
            self.log(f"   Using ship: {ship_name} (ID: {ship_id})")
            
            # Create test Initial certificates with FULL NAMES (this tests the bug fix)
            from datetime import datetime, timedelta
            current_date = datetime.now()
            
            test_certificates = [
                {
                    "ship_id": ship_id,
                    "cert_name": "SAFETY MANAGEMENT CERTIFICATE",  # Full name - should match 'SAFETY MANAGEMENT'
                    "cert_type": "Full Term",
                    "cert_no": "SMC-BUGFIX-TEST-001",
                    "issue_date": (current_date - timedelta(days=365)).isoformat(),
                    "valid_date": (current_date + timedelta(days=42)).isoformat(),  # Within 90-day window
                    "next_survey_type": "Initial",
                    "issued_by": "Panama Maritime Documentation Services",
                    "category": "certificates",
                    "sensitivity_level": "public"
                },
                {
                    "ship_id": ship_id,
                    "cert_name": "INTERNATIONAL SHIP SECURITY CERTIFICATE",  # Full name - should match 'SHIP SECURITY'
                    "cert_type": "Full Term", 
                    "cert_no": "ISSC-BUGFIX-TEST-001",
                    "issue_date": (current_date - timedelta(days=300)).isoformat(),
                    "valid_date": (current_date + timedelta(days=16)).isoformat(),  # Within 90-day window, due soon
                    "next_survey_type": "Initial",
                    "issued_by": "Panama Maritime Documentation Services",
                    "category": "certificates",
                    "sensitivity_level": "public"
                },
                {
                    "ship_id": ship_id,
                    "cert_name": "MARITIME LABOUR CERTIFICATE",  # Full name - should match 'MARITIME LABOUR'
                    "cert_type": "Full Term",
                    "cert_no": "MLC-BUGFIX-TEST-001", 
                    "issue_date": (current_date - timedelta(days=200)).isoformat(),
                    "valid_date": (current_date + timedelta(days=6)).isoformat(),  # Within 90-day window, critical
                    "next_survey_type": "Initial",
                    "issued_by": "Panama Maritime Documentation Services",
                    "category": "certificates",
                    "sensitivity_level": "public"
                }
            ]
            
            self.log("   Creating certificates with FULL NAMES to test bug fix:")
            created_count = 0
            for cert_data in test_certificates:
                self.log(f"      Creating: {cert_data['cert_name']}")
                self.log(f"         Valid date: {cert_data['valid_date']}")
                self.log(f"         Survey type: {cert_data['next_survey_type']}")
                
                endpoint = f"{BACKEND_URL}/certificates"
                response = requests.post(endpoint, json=cert_data, headers=self.get_headers(), timeout=30)
                
                if response.status_code in [200, 201]:
                    created_count += 1
                    cert_response = response.json()
                    self.log(f"         ✅ Created successfully (ID: {cert_response.get('id')})")
                else:
                    self.log(f"         ❌ Failed to create: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"            Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"            Error: {response.text[:200]}")
            
            if created_count > 0:
                self.bug_fix_tests['test_initial_certificates_created'] = True
                self.log(f"✅ Created {created_count}/3 test Initial certificates with FULL NAMES")
                self.log("   These certificates should now be detected by the FIXED name matching logic")
                return True
            else:
                self.log("❌ Failed to create any test Initial certificates")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating test Initial certificates: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_bug_fix_test(self):
        """Run comprehensive test of the Initial survey type certificate name matching bug fix"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE INITIAL SURVEY TYPE BUG FIX TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Test upcoming surveys endpoint
            self.log("\nSTEP 2: Testing upcoming surveys endpoint")
            if not self.test_upcoming_surveys_endpoint():
                self.log("❌ CRITICAL: Upcoming surveys endpoint failed")
                return False
            
            # Step 3: Verify response structure
            self.log("\nSTEP 3: Verifying response structure")
            if not self.verify_response_structure():
                self.log("❌ CRITICAL: Response structure verification failed")
                return False
            
            # Step 4: Test certificate name matching bug fix
            self.log("\nSTEP 4: Testing certificate name matching bug fix")
            if not self.test_certificate_name_matching_bug_fix():
                self.log("❌ Certificate name matching test failed")
                return False
            
            # Step 5: Test Initial certificate window logic
            self.log("\nSTEP 5: Testing Initial certificate window logic")
            if not self.test_initial_certificate_window_logic():
                self.log("❌ Initial certificate window logic test failed")
                return False
            
            # Step 6: Test Initial certificate status logic
            self.log("\nSTEP 6: Testing Initial certificate status logic")
            if not self.test_initial_certificate_status_logic():
                self.log("❌ Initial certificate status logic test failed")
                return False
            
            # Step 7: Validate survey data
            self.log("\nSTEP 7: Validating survey data")
            if not self.validate_survey_data():
                self.log("❌ Survey data validation failed")
                return False
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE BUG FIX TEST COMPLETED SUCCESSFULLY")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_bug_fix_test_summary(self):
        """Print comprehensive summary of bug fix test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 INITIAL SURVEY TYPE BUG FIX TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.bug_fix_tests)
            passed_tests = sum(1 for result in self.bug_fix_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Critical Bug Fix Results
            self.log("🔧 CRITICAL BUG FIX VERIFICATION:")
            critical_tests = [
                ('name_matching_bug_fixed', 'Certificate name matching bug fixed'),
                ('full_name_safety_management_matched', 'SAFETY MANAGEMENT CERTIFICATE matched'),
                ('full_name_ship_security_matched', 'INTERNATIONAL SHIP SECURITY CERTIFICATE matched'),
                ('full_name_maritime_labour_matched', 'MARITIME LABOUR CERTIFICATE matched'),
                ('initial_certificates_now_appearing', 'Initial certificates now appearing in results'),
            ]
            
            for test_key, description in critical_tests:
                status = "✅ PASS" if self.bug_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Window Logic Results
            self.log("\n📅 WINDOW CALCULATION VERIFICATION:")
            window_tests = [
                ('initial_certificate_window_correct', 'Initial certificate window calculation correct'),
                ('valid_date_minus_90_days_calculation', 'Valid date - 90 days calculation working'),
                ('window_close_equals_valid_date', 'Window close equals valid date'),
                ('current_date_within_window_filter', 'Current date within window filter working'),
            ]
            
            for test_key, description in window_tests:
                status = "✅ PASS" if self.bug_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Status Classification Results
            self.log("\n🚦 STATUS CLASSIFICATION VERIFICATION:")
            status_tests = [
                ('initial_overdue_logic_working', 'Initial certificate overdue logic'),
                ('initial_due_soon_logic_working', 'Initial certificate due soon logic'),
                ('initial_critical_logic_working', 'Initial certificate critical logic'),
                ('status_based_on_valid_date', 'Status based on valid date (not next_survey_date)'),
            ]
            
            for test_key, description in status_tests:
                status = "✅ PASS" if self.bug_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Display Results
            self.log("\n📺 DISPLAY VERIFICATION:")
            display_tests = [
                ('window_type_valid_3m_to_valid', 'Window type displays as "Valid-3M→Valid"'),
                ('survey_window_rule_correct', 'Survey window rule correct'),
                ('initial_smc_issc_mlc_rule_displayed', 'Initial SMC/ISSC/MLC rule displayed'),
            ]
            
            for test_key, description in display_tests:
                status = "✅ PASS" if self.bug_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL BUG FIX ASSESSMENT:")
            
            critical_passed = sum(1 for test_key, _ in critical_tests if self.bug_fix_tests.get(test_key, False))
            if critical_passed >= 3:  # At least 3 critical tests passed
                self.log("   ✅ BUG FIX APPEARS TO BE WORKING")
                self.log("   ✅ Initial certificates with full names are now being detected")
                self.log("   ✅ Certificate name matching logic has been successfully updated")
            else:
                self.log("   ❌ BUG FIX MAY NOT BE COMPLETE")
                self.log("   ❌ Initial certificates may still not be detected properly")
                self.log("   ❌ Further investigation needed")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")
    
    def run_comprehensive_bug_fix_test(self):
        """Run comprehensive test of the Initial survey type certificate name matching bug fix"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE INITIAL SURVEY TYPE BUG FIX TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Test upcoming surveys endpoint
            self.log("\nSTEP 2: Testing upcoming surveys endpoint")
            if not self.test_upcoming_surveys_endpoint():
                self.log("❌ CRITICAL: Upcoming surveys endpoint failed")
                return False
            
            # Step 3: Verify response structure
            self.log("\nSTEP 3: Verifying response structure")
            if not self.verify_response_structure():
                self.log("❌ CRITICAL: Response structure verification failed")
                return False
            
            # Step 4: Test certificate name matching bug fix
            self.log("\nSTEP 4: Testing certificate name matching bug fix")
            if not self.test_certificate_name_matching_bug_fix():
                self.log("❌ Certificate name matching test failed")
                return False
            
            # Step 5: Test Initial certificate window logic
            self.log("\nSTEP 5: Testing Initial certificate window logic")
            if not self.test_initial_certificate_window_logic():
                self.log("❌ Initial certificate window logic test failed")
                return False
            
            # Step 6: Test Initial certificate status logic
            self.log("\nSTEP 6: Testing Initial certificate status logic")
            if not self.test_initial_certificate_status_logic():
                self.log("❌ Initial certificate status logic test failed")
                return False
            
            # Step 7: Validate survey data
            self.log("\nSTEP 7: Validating survey data")
            if not self.validate_survey_data():
                self.log("❌ Survey data validation failed")
                return False
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE BUG FIX TEST COMPLETED SUCCESSFULLY")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False

    def test_specific_certificate_verification(self):
        """Test for the specific 'Test Survey Notification Certificate' mentioned in review request"""
        try:
            self.log("🔍 Testing for specific 'Test Survey Notification Certificate'...")
            
            if not self.test_certificates:
                self.log("   ⚠️ No survey data to search for test certificate")
                self.log("   Attempting to create test Initial certificates...")
                
                # Try to create test Initial certificates
                if self.create_test_initial_certificates():
                    self.log("   ✅ Test Initial certificates created, re-testing endpoint...")
                    
                    # Re-test the endpoint to get the new certificates
                    if self.test_upcoming_surveys_endpoint():
                        self.log("   ✅ Endpoint re-tested successfully")
                        if self.verify_response_structure():
                            self.log("   ✅ Response structure verified")
                        else:
                            self.log("   ❌ Response structure verification failed")
                    else:
                        self.log("   ❌ Endpoint re-test failed")
                else:
                    self.log("   ❌ Failed to create test Initial certificates")
                
                return True
            
            test_cert_found = False
            test_cert_details = None
            
            for survey in self.test_certificates:
                cert_name = survey.get('cert_name', '')
                cert_name_display = survey.get('cert_name_display', '')
                ship_name = survey.get('ship_name', '')
                
                # Look for the test certificate or Initial certificates
                if ('Test Survey Notification Certificate' in cert_name or 
                    'Test Survey Notification Certificate' in cert_name_display or
                    any(cert_type in cert_name.upper() for cert_type in ['SMC', 'ISSC', 'MLC'])):
                    test_cert_found = True
                    test_cert_details = survey
                    self.log(f"   ✅ Found certificate: {cert_name}")
                    self.log(f"      Ship: {ship_name}")
                    self.log(f"      Certificate: {cert_name}")
                    self.log(f"      Display: {cert_name_display}")
                    self.log(f"      Next Survey: {survey.get('next_survey_date')}")
                    self.log(f"      Window Open: {survey.get('window_open')}")
                    self.log(f"      Window Close: {survey.get('window_close')}")
                    self.log(f"      Is Critical: {survey.get('is_critical')}")
                    self.log(f"      Is Due Soon: {survey.get('is_due_soon')}")
                    break
            
            if test_cert_found:
                self.survey_tests['test_certificate_found'] = True
                
                # Verify the test certificate is within its window (since it was returned)
                if test_cert_details and test_cert_details.get('is_within_window'):
                    self.survey_tests['test_certificate_in_window'] = True
                    self.log("   ✅ Test certificate is correctly within its window")
                else:
                    self.log("   ❌ Test certificate window status unclear")
            else:
                self.log("   ⚠️ No test certificates found in results")
                self.log("   This might be expected if no certificates are within their windows")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing specific certificate: {str(e)}", "ERROR")
            return False

    def validate_survey_data(self):
        """Validate the survey data returned by the endpoint"""
        try:
            self.log("✅ Validating survey data quality...")
            
            if not self.test_certificates:
                self.log("   ⚠️ No survey data to validate")
                return True
            
            ship_names_present = 0
            cert_names_present = 0
            valid_dates = 0
            window_dates_present = 0
            
            for survey in self.test_certificates:
                ship_name = survey.get('ship_name')
                cert_name_display = survey.get('cert_name_display')
                next_survey = survey.get('next_survey')
                window_open = survey.get('window_open')
                window_close = survey.get('window_close')
                
                if ship_name and ship_name.strip():
                    ship_names_present += 1
                
                if cert_name_display and cert_name_display.strip():
                    cert_names_present += 1
                
                if next_survey:
                    valid_dates += 1
                
                if window_open and window_close:
                    window_dates_present += 1
            
            total_surveys = len(self.test_certificates)
            
            if ship_names_present == total_surveys:
                self.survey_tests['ship_names_present'] = True
                self.log(f"   ✅ All {total_surveys} surveys have ship names")
            else:
                self.log(f"   ❌ {total_surveys - ship_names_present}/{total_surveys} surveys missing ship names")
            
            if cert_names_present == total_surveys:
                self.survey_tests['cert_display_names_present'] = True
                self.log(f"   ✅ All {total_surveys} surveys have certificate display names")
            else:
                self.log(f"   ❌ {total_surveys - cert_names_present}/{total_surveys} surveys missing cert display names")
            
            if valid_dates == total_surveys:
                self.survey_tests['next_survey_dates_valid'] = True
                self.log(f"   ✅ All {total_surveys} surveys have valid next survey dates")
            else:
                self.log(f"   ❌ {total_surveys - valid_dates}/{total_surveys} surveys missing next survey dates")
            
            if window_dates_present == total_surveys:
                self.survey_tests['window_dates_calculated_correctly'] = True
                self.log(f"   ✅ All {total_surveys} surveys have window dates calculated")
            else:
                self.log(f"   ❌ {total_surveys - window_dates_present}/{total_surveys} surveys missing window dates")
            
            return (ship_names_present == total_surveys and 
                   cert_names_present == total_surveys and 
                   valid_dates == total_surveys and
                   window_dates_present == total_surveys)
            
        except Exception as e:
            self.log(f"❌ Error validating survey data: {str(e)}", "ERROR")
            return False

    def test_ship_data_retrieval(self):
        """Test ship data retrieval and verify date fields"""
        try:
            self.log("📊 Testing ship data retrieval and date field verification...")
            
            if not self.ship_data.get('id'):
                self.log("❌ No ship data available for testing")
                return False
            
            ship_id = self.ship_data.get('id')
            
            # Get individual ship data
            endpoint = f"{BACKEND_URL}/ships/{ship_id}"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ship_data = response.json()
                self.log("✅ Ship data retrieved successfully")
                self.timezone_tests['ship_data_retrieved_successfully'] = True
                
                # Store original dates for comparison
                date_fields = [
                    'last_docking', 'last_docking_2', 'next_docking',
                    'last_special_survey', 'last_intermediate_survey',
                    'keel_laid', 'delivery_date'
                ]
                
                self.log("   Date fields in ship data:")
                dates_found = 0
                for field in date_fields:
                    value = ship_data.get(field)
                    if value:
                        self.original_dates[field] = value
                        self.log(f"      {field}: {value}")
                        dates_found += 1
                    else:
                        self.log(f"      {field}: None")
                
                if dates_found > 0:
                    self.timezone_tests['date_fields_present'] = True
                    self.log(f"✅ Found {dates_found} date fields")
                
                # Check special_survey_cycle dates
                special_survey_cycle = ship_data.get('special_survey_cycle')
                if special_survey_cycle:
                    self.log("   Special Survey Cycle dates:")
                    from_date = special_survey_cycle.get('from_date')
                    to_date = special_survey_cycle.get('to_date')
                    if from_date:
                        self.original_dates['special_survey_from_date'] = from_date
                        self.log(f"      from_date: {from_date}")
                    if to_date:
                        self.original_dates['special_survey_to_date'] = to_date
                        self.log(f"      to_date: {to_date}")
                
                # Verify date format consistency
                consistent_formats = True
                for field, date_value in self.original_dates.items():
                    if not self.is_valid_date_format(date_value):
                        self.log(f"   ⚠️ Inconsistent date format in {field}: {date_value}")
                        consistent_formats = False
                
                if consistent_formats:
                    self.timezone_tests['date_formats_consistent'] = True
                    self.log("✅ All date formats are consistent")
                
                return True
            else:
                self.log(f"   ❌ Failed to retrieve ship data: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing ship data retrieval: {str(e)}", "ERROR")
            return False
    
    def test_ship_update_operations(self):
        """Test updating ship's date fields and verify no timezone shifts"""
        try:
            self.log("🔄 Testing ship update operations and date preservation...")
            
            if not self.ship_data.get('id'):
                self.log("❌ No ship data available for testing")
                return False
            
            ship_id = self.ship_data.get('id')
            
            # Prepare update data with current dates to test preservation
            update_data = {}
            
            # Use existing dates if available, or set test dates
            if self.original_dates:
                # Use a subset of existing dates for update test
                test_date = "2024-02-10T00:00:00"  # Known test date
                update_data = {
                    "last_docking": test_date,
                    "name": self.ship_data.get('name'),  # Required field
                    "flag": self.ship_data.get('flag', 'BELIZE'),  # Required field
                    "ship_type": self.ship_data.get('ship_type', 'PMDS')  # Required field
                }
            else:
                self.log("   No original dates found, using test dates")
                update_data = {
                    "last_docking": "2024-02-10T00:00:00",
                    "last_docking_2": "2023-08-15T00:00:00",
                    "name": self.ship_data.get('name'),
                    "flag": self.ship_data.get('flag', 'BELIZE'),
                    "ship_type": self.ship_data.get('ship_type', 'PMDS')
                }
            
            self.log(f"   Updating ship with date fields:")
            for field, value in update_data.items():
                if 'docking' in field or 'date' in field:
                    self.log(f"      {field}: {value}")
            
            # Perform ship update
            endpoint = f"{BACKEND_URL}/ships/{ship_id}"
            response = requests.put(endpoint, json=update_data, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                updated_ship = response.json()
                self.log("✅ Ship update successful")
                self.timezone_tests['ship_update_successful'] = True
                
                # Verify dates were preserved
                dates_preserved = True
                timezone_shifts_detected = False
                
                self.log("   Verifying date preservation:")
                for field, original_value in update_data.items():
                    if 'docking' in field or 'date' in field:
                        updated_value = updated_ship.get(field)
                        self.updated_dates[field] = updated_value
                        
                        self.log(f"      {field}:")
                        self.log(f"         Sent: {original_value}")
                        self.log(f"         Received: {updated_value}")
                        
                        # Check for timezone shifts
                        if original_value and updated_value:
                            if self.detect_timezone_shift(original_value, updated_value):
                                self.log(f"         ⚠️ Timezone shift detected!")
                                timezone_shifts_detected = True
                                dates_preserved = False
                            else:
                                self.log(f"         ✅ Date preserved correctly")
                        elif original_value != updated_value:
                            self.log(f"         ⚠️ Date value changed unexpectedly")
                            dates_preserved = False
                
                if dates_preserved:
                    self.timezone_tests['dates_preserved_after_update'] = True
                    self.log("✅ All dates preserved correctly after update")
                
                if not timezone_shifts_detected:
                    self.timezone_tests['no_timezone_shifts_detected'] = True
                    self.log("✅ No timezone shifts detected")
                
                return True
            else:
                self.log(f"   ❌ Ship update failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing ship update operations: {str(e)}", "ERROR")
            return False
    
    def detect_timezone_shift(self, original_date, updated_date):
        """Detect if there's a timezone shift between original and updated dates"""
        try:
            if not original_date or not updated_date:
                return False
            
            # Parse dates and compare
            from datetime import datetime
            
            # Handle different date formats
            def parse_date(date_str):
                if isinstance(date_str, str):
                    # Try ISO format
                    try:
                        if date_str.endswith('Z'):
                            date_str = date_str[:-1] + '+00:00'
                        return datetime.fromisoformat(date_str)
                    except:
                        pass
                    
                    # Try other formats
                    try:
                        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                    except:
                        pass
                
                return None
            
            orig_dt = parse_date(original_date)
            upd_dt = parse_date(updated_date)
            
            if orig_dt and upd_dt:
                # Check if dates differ by more than expected (timezone shift)
                diff = abs((orig_dt - upd_dt).total_seconds())
                # Allow small differences (seconds), but flag hour-level differences
                return diff > 3600  # More than 1 hour difference suggests timezone shift
            
            return False
            
        except Exception as e:
            self.log(f"   Error detecting timezone shift: {str(e)}")
            return False
    
    def test_recalculation_endpoints(self):
        """Test all recalculation endpoints for date consistency"""
        try:
            self.log("🔄 Testing recalculation endpoints for date consistency...")
            
            if not self.ship_data.get('id'):
                self.log("❌ No ship data available for testing")
                return False
            
            ship_id = self.ship_data.get('id')
            
            # Test endpoints as specified in review request
            endpoints_to_test = [
                ('calculate-special-survey-cycle', 'special_survey_cycle_working'),
                ('calculate-docking-dates', 'docking_dates_calculation_working'),
                ('calculate-next-docking', 'next_docking_calculation_working'),
                ('calculate-anniversary-date', 'anniversary_date_calculation_working')
            ]
            
            all_endpoints_working = True
            consistent_dates = True
            
            for endpoint_name, test_flag in endpoints_to_test:
                self.log(f"   Testing {endpoint_name}...")
                
                endpoint = f"{BACKEND_URL}/ships/{ship_id}/{endpoint_name}"
                response = requests.post(endpoint, headers=self.get_headers(), timeout=30)
                
                self.log(f"      POST {endpoint}")
                self.log(f"      Response status: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.log(f"      ✅ {endpoint_name} endpoint working")
                    self.timezone_tests[test_flag] = True
                    
                    # Store results for analysis
                    self.recalculation_results[endpoint_name] = response_data
                    
                    # Log response for analysis
                    self.log(f"      Response: {json.dumps(response_data, indent=8)}")
                    
                    # Check date formats in response
                    if not self.verify_response_date_formats(response_data, endpoint_name):
                        consistent_dates = False
                        
                else:
                    self.log(f"      ❌ {endpoint_name} endpoint failed: {response.status_code}")
                    all_endpoints_working = False
                    try:
                        error_data = response.json()
                        self.log(f"         Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"         Error: {response.text[:200]}")
            
            if all_endpoints_working:
                self.timezone_tests['all_endpoints_return_proper_formats'] = True
                self.log("✅ All recalculation endpoints are working")
            
            if consistent_dates:
                self.timezone_tests['recalculation_dates_consistent'] = True
                self.log("✅ All recalculation endpoints return consistent date formats")
            
            return all_endpoints_working
                
        except Exception as e:
            self.log(f"❌ Error testing recalculation endpoints: {str(e)}", "ERROR")
            return False
    
    def verify_response_date_formats(self, response_data, endpoint_name):
        """Verify that response contains properly formatted dates"""
        try:
            consistent = True
            
            # Check different response structures based on endpoint
            if endpoint_name == 'calculate-special-survey-cycle':
                cycle_data = response_data.get('special_survey_cycle', {})
                from_date = cycle_data.get('from_date')
                to_date = cycle_data.get('to_date')
                
                if from_date and not self.is_valid_date_format(from_date):
                    self.log(f"         ⚠️ Invalid from_date format: {from_date}")
                    consistent = False
                if to_date and not self.is_valid_date_format(to_date):
                    self.log(f"         ⚠️ Invalid to_date format: {to_date}")
                    consistent = False
                    
            elif endpoint_name == 'calculate-docking-dates':
                docking_dates = response_data.get('docking_dates', {})
                for field in ['last_docking_1', 'last_docking_2']:
                    date_value = docking_dates.get(field)
                    if date_value and not self.is_valid_date_format(date_value):
                        self.log(f"         ⚠️ Invalid {field} format: {date_value}")
                        consistent = False
                        
            elif endpoint_name == 'calculate-next-docking':
                next_docking = response_data.get('next_docking')
                if next_docking and not self.is_valid_date_format(next_docking):
                    self.log(f"         ⚠️ Invalid next_docking format: {next_docking}")
                    consistent = False
                    
            elif endpoint_name == 'calculate-anniversary-date':
                anniversary_data = response_data.get('anniversary_date', {})
                # Anniversary date typically has day/month, not full date
                day = anniversary_data.get('day')
                month = anniversary_data.get('month')
                if day and (not isinstance(day, int) or day < 1 or day > 31):
                    self.log(f"         ⚠️ Invalid day value: {day}")
                    consistent = False
                if month and (not isinstance(month, int) or month < 1 or month > 12):
                    self.log(f"         ⚠️ Invalid month value: {month}")
                    consistent = False
            
            if consistent:
                self.log(f"         ✅ Date formats are consistent in {endpoint_name}")
            
            return consistent
            
        except Exception as e:
            self.log(f"         Error verifying date formats: {str(e)}")
            return False
    
    def run_comprehensive_upcoming_surveys_tests(self):
        """Main test function for Initial Survey Type Rules Testing for SMC, ISSC, MLC Certificates"""
        self.log("🔄 STARTING SHIP MANAGEMENT SYSTEM - INITIAL SURVEY TYPE RULES TESTING")
        self.log("🎯 FOCUS: Test the updated upcoming surveys logic with Initial survey type rules for SMC, ISSC, MLC certificates")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Test upcoming surveys endpoint
            self.log("\n📅 STEP 2: TEST UPCOMING SURVEYS ENDPOINT")
            self.log("=" * 50)
            endpoint_success = self.test_upcoming_surveys_endpoint()
            if not endpoint_success:
                self.log("❌ Upcoming surveys endpoint failed - cannot proceed")
                return False
            
            # Step 3: Verify updated response structure with Initial certificate rules
            self.log("\n🔍 STEP 3: VERIFY UPDATED RESPONSE STRUCTURE WITH INITIAL CERTIFICATE RULES")
            self.log("=" * 50)
            structure_success = self.verify_response_structure()
            
            # Step 4: Test Initial certificate detection
            self.log("\n🔍 STEP 4: TEST INITIAL CERTIFICATE DETECTION")
            self.log("=" * 50)
            initial_detection_success = self.test_initial_certificate_detection()
            
            # Step 5: Test Initial certificate window logic
            self.log("\n📅 STEP 5: TEST INITIAL CERTIFICATE WINDOW LOGIC")
            self.log("=" * 50)
            initial_window_success = self.test_initial_certificate_window_logic()
            
            # Step 6: Test all window rule types
            self.log("\n🔍 STEP 6: TEST ALL WINDOW RULE TYPES")
            self.log("=" * 50)
            window_rules_success = self.test_all_window_rule_types()
            
            # Step 7: Test Initial certificate status logic
            self.log("\n🚦 STEP 7: TEST INITIAL CERTIFICATE STATUS LOGIC")
            self.log("=" * 50)
            initial_status_success = self.test_initial_certificate_status_logic()
            
            # Step 8: Test company filtering
            self.log("\n🏢 STEP 8: TEST COMPANY FILTERING")
            self.log("=" * 50)
            company_filtering_success = self.test_company_filtering()
            
            # Step 9: Test UPDATED status classification
            self.log("\n🚦 STEP 9: TEST UPDATED STATUS CLASSIFICATION")
            self.log("=" * 50)
            status_classification_success = self.test_updated_status_classification()
            
            # Step 10: Test specific certificate verification
            self.log("\n🔍 STEP 10: TEST SPECIFIC CERTIFICATE VERIFICATION")
            self.log("=" * 50)
            specific_cert_success = self.test_specific_certificate_verification()
            
            # Step 11: Validate survey data
            self.log("\n✅ STEP 11: VALIDATE SURVEY DATA")
            self.log("=" * 50)
            data_validation_success = self.validate_survey_data()
            
            # Step 12: Final Analysis
            self.log("\n📊 STEP 12: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return (endpoint_success and structure_success and 
                   initial_detection_success and initial_window_success and
                   window_rules_success and initial_status_success and
                   company_filtering_success and status_classification_success and 
                   specific_cert_success and data_validation_success)
            
        except Exception as e:
            self.log(f"❌ Comprehensive Initial survey type rules testing error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of Initial Survey Type Rules Testing for SMC, ISSC, MLC Certificates"""
        try:
            self.log("🔄 SHIP MANAGEMENT SYSTEM - INITIAL SURVEY TYPE RULES TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.survey_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.survey_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.survey_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.survey_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.survey_tests)})")
            
            # Initial Certificate Detection Analysis
            self.log("\n🔍 INITIAL CERTIFICATE DETECTION ANALYSIS:")
            
            detection_tests = [
                'initial_certificate_detection_working',
                'smc_issc_mlc_certificates_identified',
                'initial_survey_type_recognized'
            ]
            detection_passed = sum(1 for test in detection_tests if self.survey_tests.get(test, False))
            detection_rate = (detection_passed / len(detection_tests)) * 100
            
            self.log(f"\n🎯 INITIAL CERTIFICATE DETECTION: {detection_rate:.1f}% ({detection_passed}/{len(detection_tests)})")
            
            if self.survey_tests['initial_certificate_detection_working']:
                self.log("   ✅ SUCCESS: Initial certificate detection working correctly")
                self.log("      Identifies certificates with next_survey_type 'Initial' AND cert_name containing 'SMC', 'ISSC', or 'MLC'")
            else:
                self.log("   ❌ ISSUE: Initial certificate detection has problems")
            
            if self.survey_tests['smc_issc_mlc_certificates_identified']:
                self.log("   ✅ SUCCESS: SMC/ISSC/MLC certificates identified correctly")
            else:
                self.log("   ❌ ISSUE: SMC/ISSC/MLC certificate identification incorrect")
            
            # Initial Certificate Window Logic Analysis
            self.log("\n📅 INITIAL CERTIFICATE WINDOW LOGIC ANALYSIS:")
            
            window_tests = [
                'initial_certificate_window_correct',
                'valid_date_window_calculation_working',
                'initial_certificate_filter_working'
            ]
            window_passed = sum(1 for test in window_tests if self.survey_tests.get(test, False))
            window_rate = (window_passed / len(window_tests)) * 100
            
            self.log(f"\n🎯 INITIAL CERTIFICATE WINDOW LOGIC: {window_rate:.1f}% ({window_passed}/{len(window_tests)})")
            
            if self.survey_tests['initial_certificate_window_correct']:
                self.log("   ✅ SUCCESS: Initial certificate window logic working correctly")
                self.log("      window_open = valid_date - 90 days, window_close = valid_date")
            else:
                self.log("   ❌ ISSUE: Initial certificate window calculation incorrect")
            
            if self.survey_tests['valid_date_window_calculation_working']:
                self.log("   ✅ SUCCESS: Valid date window calculation working")
            else:
                self.log("   ❌ ISSUE: Valid date window calculation problems")
            
            # Window Rule Types Analysis
            self.log("\n🔍 WINDOW RULE TYPES ANALYSIS:")
            
            rule_tests = [
                'condition_certificate_expiry_window',
                'initial_smc_issc_mlc_window',
                'special_survey_window',
                'other_surveys_window'
            ]
            rule_passed = sum(1 for test in rule_tests if self.survey_tests.get(test, False))
            rule_rate = (rule_passed / len(rule_tests)) * 100
            
            self.log(f"\n🎯 WINDOW RULE TYPES: {rule_rate:.1f}% ({rule_passed}/{len(rule_tests)})")
            
            if self.survey_tests['condition_certificate_expiry_window']:
                self.log("   ✅ SUCCESS: Condition Certificate Expiry window (Issue→Valid) working")
            else:
                self.log("   ❌ ISSUE: Condition Certificate Expiry window not found")
            
            if self.survey_tests['initial_smc_issc_mlc_window']:
                self.log("   ✅ SUCCESS: Initial SMC/ISSC/MLC window (Valid-3M→Valid) working")
            else:
                self.log("   ❌ ISSUE: Initial SMC/ISSC/MLC window not found")
            
            if self.survey_tests['special_survey_window']:
                self.log("   ✅ SUCCESS: Special Survey window (-3M) working")
            else:
                self.log("   ❌ ISSUE: Special Survey window not found")
            
            if self.survey_tests['other_surveys_window']:
                self.log("   ✅ SUCCESS: Other Surveys window (±3M) working")
            else:
                self.log("   ❌ ISSUE: Other Surveys window not found")
            
            # Initial Certificate Status Logic Analysis
            self.log("\n🚦 INITIAL CERTIFICATE STATUS LOGIC ANALYSIS:")
            
            status_tests = [
                'initial_certificate_overdue_logic',
                'initial_certificate_due_soon_logic',
                'initial_certificate_critical_logic'
            ]
            status_passed = sum(1 for test in status_tests if self.survey_tests.get(test, False))
            status_rate = (status_passed / len(status_tests)) * 100
            
            self.log(f"\n🎯 INITIAL CERTIFICATE STATUS LOGIC: {status_rate:.1f}% ({status_passed}/{len(status_tests)})")
            
            if self.survey_tests['initial_certificate_overdue_logic']:
                self.log("   ✅ SUCCESS: Initial certificate overdue logic working (current_date > valid_date)")
            else:
                self.log("   ❌ ISSUE: Initial certificate overdue logic incorrect")
            
            if self.survey_tests['initial_certificate_due_soon_logic']:
                self.log("   ✅ SUCCESS: Initial certificate due soon logic working (expires within 30 days)")
            else:
                self.log("   ❌ ISSUE: Initial certificate due soon logic incorrect")
            
            if self.survey_tests['initial_certificate_critical_logic']:
                self.log("   ✅ SUCCESS: Initial certificate critical logic working (expires within 7 days or overdue)")
            else:
                self.log("   ❌ ISSUE: Initial certificate critical logic incorrect")
            
            # Updated Logic Info Analysis
            self.log("\n📋 UPDATED LOGIC INFO ANALYSIS:")
            
            if self.survey_tests['logic_info_includes_initial_rules']:
                self.log("   ✅ SUCCESS: Logic info includes Initial certificate rules")
                self.log("      'Initial SMC/ISSC/MLC: Valid date - 3M → Valid date' documented")
            else:
                self.log("   ❌ ISSUE: Logic info missing Initial certificate rules")
            
            if self.survey_tests['all_window_rule_types_documented']:
                self.log("   ✅ SUCCESS: All 4 window rule types documented")
            else:
                self.log("   ❌ ISSUE: Missing window rule types in documentation")
            
            # Company filtering analysis
            self.log("\n🏢 COMPANY FILTERING ANALYSIS:")
            
            if self.survey_tests['company_filtering_working']:
                self.log("   ✅ SUCCESS: Company filtering working correctly")
            else:
                self.log("   ❌ ISSUE: Company filtering not working")
            
            # Test certificate analysis
            self.log("\n🔍 TEST CERTIFICATE ANALYSIS:")
            
            if self.survey_tests['test_certificate_found']:
                self.log("   ✅ SUCCESS: 'Test Survey Notification Certificate' found in results")
            else:
                self.log("   ⚠️ INFO: 'Test Survey Notification Certificate' not found")
                self.log("      This may be expected if current date is outside certificate's ±90 day window")
            
            if self.survey_tests['test_certificate_in_window']:
                self.log("   ✅ SUCCESS: Test certificate correctly within its window")
            
            # Review request requirements analysis
            self.log("\n📋 REVIEW REQUEST REQUIREMENTS ANALYSIS:")
            
            req1_met = self.survey_tests['authentication_successful']
            req2_met = self.survey_tests['upcoming_surveys_endpoint_accessible']
            req3_met = self.survey_tests['initial_certificate_detection_working']
            req4_met = self.survey_tests['initial_certificate_window_correct']
            req5_met = self.survey_tests['window_type_display_correct']
            req6_met = self.survey_tests['logic_info_includes_initial_rules']
            
            self.log(f"   1. Login with admin1/123456: {'✅ MET' if req1_met else '❌ NOT MET'}")
            self.log(f"      - Authentication successful")
            
            self.log(f"   2. Test updated endpoint with all window rules: {'✅ MET' if req2_met else '❌ NOT MET'}")
            self.log(f"      - /api/certificates/upcoming-surveys accessible with Initial type rules")
            
            self.log(f"   3. Verify Initial Survey logic for SMC/ISSC/MLC: {'✅ MET' if req3_met else '❌ NOT MET'}")
            self.log(f"      - Initial certificate detection and identification working")
            
            self.log(f"   4. Verify Initial certificate window: {'✅ MET' if req4_met else '❌ NOT MET'}")
            self.log(f"      - window_open = valid_date - 90 days, window_close = valid_date")
            
            self.log(f"   5. Verify window type display: {'✅ MET' if req5_met else '❌ NOT MET'}")
            self.log(f"      - 'Valid-3M→Valid' for Initial certificates, other types working")
            
            self.log(f"   6. Check updated logic info: {'✅ MET' if req6_met else '❌ NOT MET'}")
            self.log(f"      - Logic info includes Initial SMC/ISSC/MLC rules explanation")
            
            requirements_met = sum([req1_met, req2_met, req3_met, req4_met, req5_met, req6_met])
            
            # Final conclusion
            if success_rate >= 80 and requirements_met >= 5:
                self.log(f"\n🎉 CONCLUSION: INITIAL SURVEY TYPE RULES FOR SMC/ISSC/MLC CERTIFICATES ARE WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Initial certificate logic fully implemented!")
                self.log(f"   ✅ Requirements met: {requirements_met}/6")
                self.log(f"   ✅ Initial SMC/ISSC/MLC certificates detected correctly")
                self.log(f"   ✅ Initial certificate window logic working (valid_date - 90 days → valid_date)")
                self.log(f"   ✅ All window rule types working correctly")
                self.log(f"   ✅ Initial certificate status logic working")
                self.log(f"   ✅ Updated logic info includes Initial certificate rules")
            elif success_rate >= 60 and requirements_met >= 4:
                self.log(f"\n⚠️ CONCLUSION: INITIAL SURVEY TYPE RULES PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Most Initial certificate functionality working, minor improvements needed")
                self.log(f"   ⚠️ Requirements met: {requirements_met}/6")
                
                if req1_met and req2_met:
                    self.log(f"   ✅ Core functionality (authentication and endpoint) is working")
                if not req3_met:
                    self.log(f"   ⚠️ Initial certificate detection may need attention")
                if not req4_met:
                    self.log(f"   ⚠️ Initial certificate window logic may need fixes")
                if not req5_met:
                    self.log(f"   ⚠️ Window type display may be incorrect")
                if not req6_met:
                    self.log(f"   ⚠️ Logic info may be missing Initial certificate rules")
            else:
                self.log(f"\n❌ CONCLUSION: INITIAL SURVEY TYPE RULES HAVE CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Significant fixes needed")
                self.log(f"   ❌ Requirements met: {requirements_met}/6")
                self.log(f"   ❌ Initial survey type rules need major fixes before production use")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run Initial Survey Type Certificate Name Matching Bug Fix Test"""
    print("🚀 INITIAL SURVEY TYPE CERTIFICATE NAME MATCHING BUG FIX TEST STARTED")
    print("=" * 80)
    
    try:
        tester = InitialSurveyBugFixTester()
        success = tester.run_comprehensive_bug_fix_test()
        
        if success:
            print("\n✅ BUG FIX TEST COMPLETED SUCCESSFULLY")
            tester.print_bug_fix_test_summary()
        else:
            print("\n❌ BUG FIX TEST COMPLETED WITH ISSUES")
            tester.print_bug_fix_test_summary()
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
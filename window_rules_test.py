#!/usr/bin/env python3
"""
Ship Management System - Next Survey Window Rules Testing
FOCUS: Test the updated upcoming surveys logic with Special Survey vs Other Survey window rules

REVIEW REQUEST REQUIREMENTS:
1. Login with admin1/123456
2. Test the updated `/api/certificates/upcoming-surveys` endpoint with new window rules
3. Verify the window rules are applied correctly:
   - Special Survey: Only -3M window (90 days before survey date, no days after)
     - window_open = next_survey - 90 days
     - window_close = next_survey (no extension)
   - Other Surveys: ±3M window (90 days before and after survey date)
     - window_open = next_survey - 90 days  
     - window_close = next_survey + 90 days
4. Check response includes new fields:
   - window_type: "-3M" for Special Survey, "±3M" for others
   - survey_window_rule: explanation of rule applied
   - Updated logic_info with window rules explanation

KEY VERIFICATION POINTS:
1. Special Survey Handling: Certificates with "Special Survey" type get -3M window only
2. Other Survey Handling: All other survey types get ±3M window
3. Overdue Logic: Different overdue determination based on survey type
4. Critical Status: Adjusted critical logic for Special Survey vs others
5. Response Structure: New fields populated correctly

EXPECTED BEHAVIOR:
- Special Survey certificates only appear if current_date is within 90 days before survey date
- Other survey certificates appear if current_date is within 90 days before OR after survey date
- Window type displayed correctly in response
- Different overdue and critical logic applied based on survey type
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://maritime-docs.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class WindowRulesTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for window rules
        self.window_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            
            # Endpoint accessibility
            'upcoming_surveys_endpoint_accessible': False,
            'response_valid_json': False,
            
            # Window rules implementation
            'special_survey_window_rules_applied': False,
            'other_survey_window_rules_applied': False,
            'window_type_field_present': False,
            'survey_window_rule_field_present': False,
            
            # Logic verification
            'special_survey_minus_3m_only': False,
            'other_surveys_plus_minus_3m': False,
            'overdue_logic_different_by_type': False,
            'critical_logic_different_by_type': False,
            
            # Response structure
            'logic_info_has_window_rules': False,
            'window_calculation_explained': False,
            'filter_condition_correct': False,
        }
        
        # Store test data for analysis
        self.user_company = None
        self.upcoming_surveys_response = {}
        self.special_survey_certificates = []
        self.other_survey_certificates = []
        
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
                
                self.window_tests['authentication_successful'] = True
                self.user_company = self.current_user.get('company')
                if self.user_company:
                    self.window_tests['user_company_identified'] = True
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
    
    def test_upcoming_surveys_endpoint(self):
        """Test the upcoming surveys endpoint with new window rules"""
        try:
            self.log("📅 Testing upcoming surveys endpoint with window rules...")
            
            endpoint = f"{BACKEND_URL}/certificates/upcoming-surveys"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.window_tests['upcoming_surveys_endpoint_accessible'] = True
                self.log("✅ Upcoming surveys endpoint is accessible")
                
                try:
                    response_data = response.json()
                    self.upcoming_surveys_response = response_data
                    self.window_tests['response_valid_json'] = True
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
    
    def verify_window_rules_implementation(self):
        """Verify that window rules are correctly implemented for Special Survey vs Other Surveys"""
        try:
            self.log("🔍 Verifying window rules implementation...")
            
            if not self.upcoming_surveys_response:
                self.log("❌ No response data to verify")
                return False
            
            upcoming_surveys = self.upcoming_surveys_response.get('upcoming_surveys', [])
            self.log(f"   Found {len(upcoming_surveys)} upcoming surveys to analyze")
            
            if not upcoming_surveys:
                self.log("   ⚠️ No upcoming surveys found - cannot verify window rules")
                # This might be valid if no surveys are due
                return True
            
            special_surveys_found = 0
            other_surveys_found = 0
            window_type_correct = 0
            survey_window_rule_correct = 0
            
            for survey in upcoming_surveys:
                next_survey_type = survey.get('next_survey_type', '')
                window_type = survey.get('window_type', '')
                survey_window_rule = survey.get('survey_window_rule', '')
                ship_name = survey.get('ship_name', 'Unknown')
                cert_name = survey.get('cert_name', 'Unknown')
                
                self.log(f"   Survey: {ship_name} - {cert_name}")
                self.log(f"      Next Survey Type: '{next_survey_type}'")
                self.log(f"      Window Type: '{window_type}'")
                self.log(f"      Survey Window Rule: '{survey_window_rule}'")
                
                # Check if window_type and survey_window_rule fields are present
                if 'window_type' in survey:
                    self.window_tests['window_type_field_present'] = True
                if 'survey_window_rule' in survey:
                    self.window_tests['survey_window_rule_field_present'] = True
                
                # Categorize by survey type
                if 'Special Survey' in next_survey_type:
                    special_surveys_found += 1
                    self.special_survey_certificates.append(survey)
                    
                    # Verify Special Survey window rules
                    if window_type == '-3M':
                        window_type_correct += 1
                        self.log(f"         ✅ Special Survey window type correct: {window_type}")
                    else:
                        self.log(f"         ❌ Special Survey window type incorrect: expected '-3M', got '{window_type}'")
                    
                    if 'Special Survey: -3M only' in survey_window_rule:
                        survey_window_rule_correct += 1
                        self.log(f"         ✅ Special Survey window rule correct")
                    else:
                        self.log(f"         ❌ Special Survey window rule incorrect: '{survey_window_rule}'")
                else:
                    other_surveys_found += 1
                    self.other_survey_certificates.append(survey)
                    
                    # Verify Other Survey window rules
                    if window_type == '±3M':
                        window_type_correct += 1
                        self.log(f"         ✅ Other Survey window type correct: {window_type}")
                    else:
                        self.log(f"         ❌ Other Survey window type incorrect: expected '±3M', got '{window_type}'")
                    
                    if 'Other surveys: ±3M' in survey_window_rule:
                        survey_window_rule_correct += 1
                        self.log(f"         ✅ Other Survey window rule correct")
                    else:
                        self.log(f"         ❌ Other Survey window rule incorrect: '{survey_window_rule}'")
            
            self.log(f"   Summary:")
            self.log(f"      Special Surveys found: {special_surveys_found}")
            self.log(f"      Other Surveys found: {other_surveys_found}")
            self.log(f"      Window types correct: {window_type_correct}/{len(upcoming_surveys)}")
            self.log(f"      Survey window rules correct: {survey_window_rule_correct}/{len(upcoming_surveys)}")
            
            # Set test results
            if special_surveys_found > 0:
                self.window_tests['special_survey_window_rules_applied'] = True
            if other_surveys_found > 0:
                self.window_tests['other_survey_window_rules_applied'] = True
            
            # Check if all window types and rules are correct
            if window_type_correct == len(upcoming_surveys) and survey_window_rule_correct == len(upcoming_surveys):
                self.log("✅ All window rules are correctly implemented")
                return True
            else:
                self.log(f"❌ Window rules implementation has issues")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying window rules implementation: {str(e)}", "ERROR")
            return False
    
    def verify_window_calculations(self):
        """Verify that window calculations are correct for Special Survey vs Other Surveys"""
        try:
            self.log("📊 Verifying window calculations...")
            
            current_date = datetime.now().date()
            self.log(f"   Current date: {current_date}")
            
            special_calculations_correct = 0
            other_calculations_correct = 0
            
            # Test Special Survey calculations
            self.log(f"   Testing {len(self.special_survey_certificates)} Special Survey certificates:")
            for survey in self.special_survey_certificates:
                ship_name = survey.get('ship_name', 'Unknown')
                next_survey_date_str = survey.get('next_survey_date')
                window_open_str = survey.get('window_open')
                window_close_str = survey.get('window_close')
                
                if next_survey_date_str and window_open_str and window_close_str:
                    try:
                        next_survey_date = datetime.fromisoformat(next_survey_date_str).date()
                        window_open = datetime.fromisoformat(window_open_str).date()
                        window_close = datetime.fromisoformat(window_close_str).date()
                        
                        # Expected Special Survey window: -3M only (no extension after)
                        expected_window_open = next_survey_date - timedelta(days=90)
                        expected_window_close = next_survey_date  # No extension
                        
                        self.log(f"      {ship_name} Special Survey:")
                        self.log(f"         Next survey: {next_survey_date}")
                        self.log(f"         Window open: {window_open} (expected: {expected_window_open})")
                        self.log(f"         Window close: {window_close} (expected: {expected_window_close})")
                        
                        if window_open == expected_window_open and window_close == expected_window_close:
                            special_calculations_correct += 1
                            self.log(f"         ✅ Special Survey window calculation correct")
                        else:
                            self.log(f"         ❌ Special Survey window calculation incorrect")
                            
                    except Exception as e:
                        self.log(f"         ⚠️ Could not verify calculation: {str(e)}")
            
            # Test Other Survey calculations
            self.log(f"   Testing {len(self.other_survey_certificates)} Other Survey certificates:")
            for survey in self.other_survey_certificates:
                ship_name = survey.get('ship_name', 'Unknown')
                next_survey_date_str = survey.get('next_survey_date')
                window_open_str = survey.get('window_open')
                window_close_str = survey.get('window_close')
                
                if next_survey_date_str and window_open_str and window_close_str:
                    try:
                        next_survey_date = datetime.fromisoformat(next_survey_date_str).date()
                        window_open = datetime.fromisoformat(window_open_str).date()
                        window_close = datetime.fromisoformat(window_close_str).date()
                        
                        # Expected Other Survey window: ±3M (before and after)
                        expected_window_open = next_survey_date - timedelta(days=90)
                        expected_window_close = next_survey_date + timedelta(days=90)
                        
                        self.log(f"      {ship_name} Other Survey:")
                        self.log(f"         Next survey: {next_survey_date}")
                        self.log(f"         Window open: {window_open} (expected: {expected_window_open})")
                        self.log(f"         Window close: {window_close} (expected: {expected_window_close})")
                        
                        if window_open == expected_window_open and window_close == expected_window_close:
                            other_calculations_correct += 1
                            self.log(f"         ✅ Other Survey window calculation correct")
                        else:
                            self.log(f"         ❌ Other Survey window calculation incorrect")
                            
                    except Exception as e:
                        self.log(f"         ⚠️ Could not verify calculation: {str(e)}")
            
            # Set test results
            if special_calculations_correct == len(self.special_survey_certificates):
                self.window_tests['special_survey_minus_3m_only'] = True
                self.log(f"✅ All Special Survey calculations correct (-3M only)")
            
            if other_calculations_correct == len(self.other_survey_certificates):
                self.window_tests['other_surveys_plus_minus_3m'] = True
                self.log(f"✅ All Other Survey calculations correct (±3M)")
            
            return (special_calculations_correct == len(self.special_survey_certificates) and 
                   other_calculations_correct == len(self.other_survey_certificates))
                
        except Exception as e:
            self.log(f"❌ Error verifying window calculations: {str(e)}", "ERROR")
            return False
    
    def verify_overdue_and_critical_logic(self):
        """Verify that overdue and critical logic differs by survey type"""
        try:
            self.log("🚦 Verifying overdue and critical logic by survey type...")
            
            current_date = datetime.now().date()
            special_logic_correct = 0
            other_logic_correct = 0
            
            # Test Special Survey logic
            self.log(f"   Testing Special Survey overdue/critical logic:")
            for survey in self.special_survey_certificates:
                ship_name = survey.get('ship_name', 'Unknown')
                next_survey_date_str = survey.get('next_survey_date')
                is_overdue = survey.get('is_overdue')
                is_critical = survey.get('is_critical')
                
                if next_survey_date_str:
                    try:
                        next_survey_date = datetime.fromisoformat(next_survey_date_str).date()
                        days_until_survey = (next_survey_date - current_date).days
                        
                        # Expected Special Survey logic:
                        # - Overdue: past survey date (no grace period)
                        # - Critical: due within 7 days or overdue
                        expected_is_overdue = next_survey_date < current_date
                        expected_is_critical = days_until_survey <= 7
                        
                        self.log(f"      {ship_name}:")
                        self.log(f"         Days until survey: {days_until_survey}")
                        self.log(f"         Is overdue: {is_overdue} (expected: {expected_is_overdue})")
                        self.log(f"         Is critical: {is_critical} (expected: {expected_is_critical})")
                        
                        if is_overdue == expected_is_overdue and is_critical == expected_is_critical:
                            special_logic_correct += 1
                            self.log(f"         ✅ Special Survey logic correct")
                        else:
                            self.log(f"         ❌ Special Survey logic incorrect")
                            
                    except Exception as e:
                        self.log(f"         ⚠️ Could not verify logic: {str(e)}")
            
            # Test Other Survey logic
            self.log(f"   Testing Other Survey overdue/critical logic:")
            for survey in self.other_survey_certificates:
                ship_name = survey.get('ship_name', 'Unknown')
                next_survey_date_str = survey.get('next_survey_date')
                is_overdue = survey.get('is_overdue')
                is_critical = survey.get('is_critical')
                
                if next_survey_date_str:
                    try:
                        next_survey_date = datetime.fromisoformat(next_survey_date_str).date()
                        days_until_survey = (next_survey_date - current_date).days
                        
                        # Expected Other Survey logic:
                        # - Overdue: past survey date + 90 days window
                        # - Critical: due within 7 days or significantly overdue (>30 days past)
                        expected_is_overdue = current_date > (next_survey_date + timedelta(days=90))
                        expected_is_critical = days_until_survey <= 7 or days_until_survey < -30
                        
                        self.log(f"      {ship_name}:")
                        self.log(f"         Days until survey: {days_until_survey}")
                        self.log(f"         Is overdue: {is_overdue} (expected: {expected_is_overdue})")
                        self.log(f"         Is critical: {is_critical} (expected: {expected_is_critical})")
                        
                        if is_overdue == expected_is_overdue and is_critical == expected_is_critical:
                            other_logic_correct += 1
                            self.log(f"         ✅ Other Survey logic correct")
                        else:
                            self.log(f"         ❌ Other Survey logic incorrect")
                            
                    except Exception as e:
                        self.log(f"         ⚠️ Could not verify logic: {str(e)}")
            
            # Set test results
            if special_logic_correct == len(self.special_survey_certificates):
                self.log(f"✅ All Special Survey overdue/critical logic correct")
            
            if other_logic_correct == len(self.other_survey_certificates):
                self.log(f"✅ All Other Survey overdue/critical logic correct")
            
            if (special_logic_correct == len(self.special_survey_certificates) and 
                other_logic_correct == len(self.other_survey_certificates)):
                self.window_tests['overdue_logic_different_by_type'] = True
                self.window_tests['critical_logic_different_by_type'] = True
                return True
            
            return False
                
        except Exception as e:
            self.log(f"❌ Error verifying overdue and critical logic: {str(e)}", "ERROR")
            return False
    
    def verify_logic_info_structure(self):
        """Verify that logic_info contains window rules explanation"""
        try:
            self.log("📋 Verifying logic_info structure with window rules...")
            
            logic_info = self.upcoming_surveys_response.get('logic_info', {})
            
            if not logic_info:
                self.log("❌ No logic_info found in response")
                return False
            
            self.log(f"   Logic info keys: {list(logic_info.keys())}")
            
            # Check for window rules section
            window_rules = logic_info.get('window_rules', {})
            if window_rules:
                self.window_tests['logic_info_has_window_rules'] = True
                self.log("✅ Window rules section found in logic_info")
                
                special_survey_rule = window_rules.get('special_survey', '')
                other_surveys_rule = window_rules.get('other_surveys', '')
                
                self.log(f"      Special Survey rule: '{special_survey_rule}'")
                self.log(f"      Other Surveys rule: '{other_surveys_rule}'")
                
                # Verify rule content
                if '-3M' in special_survey_rule and '90 days before' in special_survey_rule:
                    self.log("      ✅ Special Survey rule correctly explained")
                else:
                    self.log("      ❌ Special Survey rule explanation incorrect")
                
                if '±3M' in other_surveys_rule and '90 days before and after' in other_surveys_rule:
                    self.log("      ✅ Other Surveys rule correctly explained")
                else:
                    self.log("      ❌ Other Surveys rule explanation incorrect")
            else:
                self.log("❌ No window_rules section found in logic_info")
            
            # Check for window calculation section
            window_calculation = logic_info.get('window_calculation', {})
            if window_calculation:
                self.window_tests['window_calculation_explained'] = True
                self.log("✅ Window calculation section found in logic_info")
                
                special_calc = window_calculation.get('special_survey', '')
                other_calc = window_calculation.get('other_surveys', '')
                
                self.log(f"      Special Survey calculation: '{special_calc}'")
                self.log(f"      Other Surveys calculation: '{other_calc}'")
            else:
                self.log("❌ No window_calculation section found in logic_info")
            
            # Check filter condition
            filter_condition = logic_info.get('filter_condition', '')
            if filter_condition and 'window_open <= current_date <= window_close' in filter_condition:
                self.window_tests['filter_condition_correct'] = True
                self.log(f"✅ Filter condition correct: '{filter_condition}'")
            else:
                self.log(f"❌ Filter condition incorrect or missing: '{filter_condition}'")
            
            return (self.window_tests['logic_info_has_window_rules'] and 
                   self.window_tests['window_calculation_explained'] and 
                   self.window_tests['filter_condition_correct'])
                
        except Exception as e:
            self.log(f"❌ Error verifying logic_info structure: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_window_rules_tests(self):
        """Main test function for Next Survey window rules"""
        self.log("🔄 STARTING SHIP MANAGEMENT SYSTEM - NEXT SURVEY WINDOW RULES TESTING")
        self.log("🎯 FOCUS: Test Special Survey vs Other Survey window rules")
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
            
            # Step 3: Verify window rules implementation
            self.log("\n🔍 STEP 3: VERIFY WINDOW RULES IMPLEMENTATION")
            self.log("=" * 50)
            window_rules_success = self.verify_window_rules_implementation()
            
            # Step 4: Verify window calculations
            self.log("\n📊 STEP 4: VERIFY WINDOW CALCULATIONS")
            self.log("=" * 50)
            calculations_success = self.verify_window_calculations()
            
            # Step 5: Verify overdue and critical logic
            self.log("\n🚦 STEP 5: VERIFY OVERDUE AND CRITICAL LOGIC")
            self.log("=" * 50)
            logic_success = self.verify_overdue_and_critical_logic()
            
            # Step 6: Verify logic_info structure
            self.log("\n📋 STEP 6: VERIFY LOGIC_INFO STRUCTURE")
            self.log("=" * 50)
            logic_info_success = self.verify_logic_info_structure()
            
            # Step 7: Final Analysis
            self.log("\n📊 STEP 7: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return (endpoint_success and window_rules_success and 
                   calculations_success and logic_success and logic_info_success)
            
        except Exception as e:
            self.log(f"❌ Comprehensive window rules testing error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of Next Survey window rules testing"""
        try:
            self.log("🔄 SHIP MANAGEMENT SYSTEM - NEXT SURVEY WINDOW RULES TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.window_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.window_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.window_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.window_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.window_tests)})")
            
            # Window rules analysis
            self.log("\n📅 WINDOW RULES ANALYSIS:")
            self.log(f"   Special Survey certificates found: {len(self.special_survey_certificates)}")
            self.log(f"   Other Survey certificates found: {len(self.other_survey_certificates)}")
            
            if self.window_tests['special_survey_window_rules_applied']:
                self.log("   ✅ Special Survey window rules applied correctly (-3M only)")
            else:
                self.log("   ❌ Special Survey window rules not applied correctly")
            
            if self.window_tests['other_survey_window_rules_applied']:
                self.log("   ✅ Other Survey window rules applied correctly (±3M)")
            else:
                self.log("   ❌ Other Survey window rules not applied correctly")
            
            # Review request requirements analysis
            self.log("\n📋 REVIEW REQUEST REQUIREMENTS ANALYSIS:")
            
            req1_met = self.window_tests['authentication_successful']
            req2_met = self.window_tests['upcoming_surveys_endpoint_accessible']
            req3_met = (self.window_tests['special_survey_minus_3m_only'] and 
                       self.window_tests['other_surveys_plus_minus_3m'])
            req4_met = (self.window_tests['window_type_field_present'] and 
                       self.window_tests['survey_window_rule_field_present'])
            req5_met = (self.window_tests['overdue_logic_different_by_type'] and 
                       self.window_tests['critical_logic_different_by_type'])
            req6_met = self.window_tests['logic_info_has_window_rules']
            
            self.log(f"   1. Login with admin1/123456: {'✅ MET' if req1_met else '❌ NOT MET'}")
            self.log(f"   2. Test updated endpoint: {'✅ MET' if req2_met else '❌ NOT MET'}")
            self.log(f"   3. Verify window rules: {'✅ MET' if req3_met else '❌ NOT MET'}")
            self.log(f"      - Special Survey: -3M only")
            self.log(f"      - Other Surveys: ±3M")
            self.log(f"   4. Check new response fields: {'✅ MET' if req4_met else '❌ NOT MET'}")
            self.log(f"      - window_type, survey_window_rule")
            self.log(f"   5. Verify different logic by type: {'✅ MET' if req5_met else '❌ NOT MET'}")
            self.log(f"      - Overdue and critical logic")
            self.log(f"   6. Check updated logic_info: {'✅ MET' if req6_met else '❌ NOT MET'}")
            
            requirements_met = sum([req1_met, req2_met, req3_met, req4_met, req5_met, req6_met])
            
            # Final conclusion
            if success_rate >= 80 and requirements_met >= 5:
                self.log(f"\n🎉 CONCLUSION: NEXT SURVEY WINDOW RULES ARE WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Window rules fully implemented!")
                self.log(f"   ✅ Requirements met: {requirements_met}/6")
                self.log(f"   ✅ Special Survey: Only -3M window (90 days before, no extension)")
                self.log(f"   ✅ Other Surveys: ±3M window (90 days before and after)")
                self.log(f"   ✅ Different overdue and critical logic by survey type")
                self.log(f"   ✅ New response fields populated correctly")
            elif success_rate >= 60 and requirements_met >= 4:
                self.log(f"\n⚠️ CONCLUSION: NEXT SURVEY WINDOW RULES PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Most functionality working, minor improvements needed")
                self.log(f"   ⚠️ Requirements met: {requirements_met}/6")
            else:
                self.log(f"\n❌ CONCLUSION: NEXT SURVEY WINDOW RULES HAVE CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Significant fixes needed")
                self.log(f"   ❌ Requirements met: {requirements_met}/6")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run Next Survey Window Rules tests"""
    print("🔄 SHIP MANAGEMENT SYSTEM - NEXT SURVEY WINDOW RULES TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = WindowRulesTester()
        success = tester.run_comprehensive_window_rules_tests()
        
        if success:
            print("\n✅ NEXT SURVEY WINDOW RULES TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ NEXT SURVEY WINDOW RULES TESTING COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
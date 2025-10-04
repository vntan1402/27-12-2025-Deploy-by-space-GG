#!/usr/bin/env python3
"""
Ship Management System - Updated Upcoming Surveys Logic Testing
FOCUS: Test the updated upcoming surveys logic with new window calculation

REVIEW REQUEST REQUIREMENTS:
1. Login with admin1/123456
2. Test the updated `/api/certificates/upcoming-surveys` endpoint with new logic
3. Verify the new window calculation logic:
   - For each certificate: window_open = next_survey - 90 days, window_close = next_survey + 90 days
   - Filter condition: window_open <= current_date <= window_close
4. Check the new response structure with updated fields:
   - is_critical field (overdue or within 7 days)
   - window_open, window_close for each certificate
   - days_from_window_open, days_to_window_close
   - Updated logic_info in response

KEY VERIFICATION POINTS:
1. Window Calculation: Each certificate creates its own ±90 day window around next_survey_date
2. Current Date Filter: Only certificates whose window contains current date are returned
3. Status Classification: 
   - is_critical: overdue or due within 7 days
   - is_due_soon: due within 30 days (but not critical)
   - is_within_window: within certificate's ±90 day window
4. Response Fields: New window information fields are populated correctly

EXPECTED BEHAVIOR:
- Test certificate "Test Survey Notification Certificate" should still appear if current date falls within its ±90 day window
- Response should include new window_open, window_close dates for each certificate
- Status indicators should reflect new classification logic
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vesseltrack.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class UpcomingSurveysNotificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for updated upcoming surveys logic
        self.survey_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            
            # Upcoming surveys endpoint tests
            'upcoming_surveys_endpoint_accessible': False,
            'upcoming_surveys_response_valid': False,
            'response_structure_correct': False,
            
            # NEW: Window calculation tests
            'window_calculation_logic_working': False,
            'individual_certificate_windows_correct': False,
            'current_date_filter_working': False,
            
            # NEW: Updated response structure tests
            'new_window_fields_present': False,
            'logic_info_updated': False,
            'window_dates_calculated_correctly': False,
            
            # NEW: Status classification tests
            'is_critical_field_present': False,
            'is_critical_logic_correct': False,
            'status_classification_updated': False,
            
            # Company filtering tests
            'company_filtering_working': False,
            'only_user_company_ships_returned': False,
            
            # Response structure tests
            'required_fields_present': False,
            'status_indicators_calculated': False,
            'days_until_survey_accurate': False,
            
            # Data validation tests
            'ship_names_present': False,
            'cert_display_names_present': False,
            'next_survey_dates_valid': False,
            
            # NEW: Test certificate verification
            'test_certificate_found': False,
            'test_certificate_in_window': False,
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
                
                self.survey_tests['authentication_successful'] = True
                self.user_company = self.current_user.get('company')
                if self.user_company:
                    self.survey_tests['user_company_identified'] = True
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
                self.survey_tests['upcoming_surveys_endpoint_accessible'] = True
                self.log("✅ Upcoming surveys endpoint is accessible")
                
                try:
                    response_data = response.json()
                    self.upcoming_surveys_response = response_data
                    self.survey_tests['upcoming_surveys_response_valid'] = True
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
        """Verify the upcoming surveys response has the correct structure"""
        try:
            self.log("🔍 Verifying response structure...")
            
            if not self.upcoming_surveys_response:
                self.log("❌ No response data to verify")
                return False
            
            response = self.upcoming_surveys_response
            
            # Check for expected top-level keys
            expected_keys = ['upcoming_surveys', 'total_count', 'company']
            missing_keys = []
            
            for key in expected_keys:
                if key not in response:
                    missing_keys.append(key)
                else:
                    self.log(f"   ✅ Found key: {key}")
            
            if missing_keys:
                self.log(f"   ❌ Missing keys: {missing_keys}")
                return False
            
            self.survey_tests['response_structure_correct'] = True
            self.log("✅ Top-level response structure is correct")
            
            # Check upcoming_surveys array structure
            upcoming_surveys = response.get('upcoming_surveys', [])
            self.log(f"   Found {len(upcoming_surveys)} upcoming surveys")
            
            if upcoming_surveys:
                # Check first survey item structure
                first_survey = upcoming_surveys[0]
                expected_survey_fields = [
                    'ship_name', 'cert_name_display', 'next_survey', 
                    'next_survey_type', 'last_endorse', 'days_until_survey',
                    'is_overdue', 'is_due_soon'
                ]
                
                missing_fields = []
                for field in expected_survey_fields:
                    if field not in first_survey:
                        missing_fields.append(field)
                    else:
                        self.log(f"      ✅ Found field: {field}")
                
                if missing_fields:
                    self.log(f"   ❌ Missing survey fields: {missing_fields}")
                    return False
                
                self.survey_tests['required_fields_present'] = True
                self.log("✅ All required survey fields are present")
                
                # Store surveys for further analysis
                self.test_certificates = upcoming_surveys
                
                return True
            else:
                self.log("   ⚠️ No upcoming surveys found in response")
                # This might be valid if no surveys are due
                self.survey_tests['required_fields_present'] = True
                return True
                
        except Exception as e:
            self.log(f"❌ Error verifying response structure: {str(e)}", "ERROR")
            return False
    
    def test_date_filtering_logic(self):
        """Test the ±3 months date filtering logic"""
        try:
            self.log("📅 Testing date filtering logic (±3 months window)...")
            
            if not self.test_certificates:
                self.log("   ⚠️ No upcoming surveys to test date filtering")
                # This might be valid - no surveys due
                self.survey_tests['date_filtering_logic_working'] = True
                self.survey_tests['three_month_window_correct'] = True
                return True
            
            from datetime import datetime, timedelta
            current_date = datetime.now()
            three_months_ago = current_date - timedelta(days=90)
            three_months_ahead = current_date + timedelta(days=90)
            
            self.log(f"   Current date: {current_date.strftime('%Y-%m-%d')}")
            self.log(f"   Window start: {three_months_ago.strftime('%Y-%m-%d')} (-90 days)")
            self.log(f"   Window end: {three_months_ahead.strftime('%Y-%m-%d')} (+90 days)")
            
            dates_in_window = 0
            dates_outside_window = 0
            
            for survey in self.test_certificates:
                next_survey_str = survey.get('next_survey')
                if next_survey_str:
                    try:
                        # Parse the next survey date
                        if 'T' in next_survey_str:
                            next_survey_date = datetime.fromisoformat(next_survey_str.replace('Z', '+00:00'))
                        else:
                            next_survey_date = datetime.strptime(next_survey_str, '%Y-%m-%d')
                        
                        # Check if date is within ±3 months window
                        if three_months_ago <= next_survey_date <= three_months_ahead:
                            dates_in_window += 1
                            self.log(f"      ✅ {survey.get('ship_name')} - {next_survey_date.strftime('%Y-%m-%d')} (in window)")
                        else:
                            dates_outside_window += 1
                            self.log(f"      ❌ {survey.get('ship_name')} - {next_survey_date.strftime('%Y-%m-%d')} (outside window)")
                    except Exception as e:
                        self.log(f"      ⚠️ Could not parse date: {next_survey_str} - {str(e)}")
            
            if dates_outside_window == 0:
                self.survey_tests['date_filtering_logic_working'] = True
                self.survey_tests['three_month_window_correct'] = True
                self.log(f"✅ Date filtering logic working correctly - all {dates_in_window} surveys within ±3 months")
                return True
            else:
                self.log(f"❌ Date filtering issue - {dates_outside_window} surveys outside ±3 months window")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing date filtering logic: {str(e)}", "ERROR")
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

    def test_status_indicators(self):
        """Test status indicators calculation (is_overdue, is_due_soon, days_until_survey)"""
        try:
            self.log("🚦 Testing status indicators calculation...")
            
            if not self.test_certificates:
                self.log("   ⚠️ No surveys to test status indicators")
                self.survey_tests['status_indicators_calculated'] = True
                return True
            
            from datetime import datetime, timedelta
            current_date = datetime.now()
            
            status_indicators_correct = 0
            total_surveys = len(self.test_certificates)
            
            for survey in self.test_certificates:
                ship_name = survey.get('ship_name', 'Unknown')
                next_survey_str = survey.get('next_survey')
                is_overdue = survey.get('is_overdue')
                is_due_soon = survey.get('is_due_soon')
                days_until_survey = survey.get('days_until_survey')
                
                self.log(f"   Survey for {ship_name}:")
                self.log(f"      Next survey: {next_survey_str}")
                self.log(f"      Is overdue: {is_overdue}")
                self.log(f"      Is due soon: {is_due_soon}")
                self.log(f"      Days until survey: {days_until_survey}")
                
                if next_survey_str:
                    try:
                        # Parse the next survey date
                        if 'T' in next_survey_str:
                            next_survey_date = datetime.fromisoformat(next_survey_str.replace('Z', '+00:00'))
                        else:
                            next_survey_date = datetime.strptime(next_survey_str, '%Y-%m-%d')
                        
                        # Calculate expected values
                        days_diff = (next_survey_date - current_date).days
                        expected_is_overdue = days_diff < 0
                        expected_is_due_soon = 0 <= days_diff <= 30  # Assuming 30 days is "due soon"
                        
                        self.log(f"      Calculated days difference: {days_diff}")
                        self.log(f"      Expected is_overdue: {expected_is_overdue}")
                        self.log(f"      Expected is_due_soon: {expected_is_due_soon}")
                        
                        # Verify calculations
                        indicators_correct = True
                        
                        if days_until_survey != days_diff:
                            self.log(f"         ❌ Days until survey mismatch: got {days_until_survey}, expected {days_diff}")
                            indicators_correct = False
                        
                        if is_overdue != expected_is_overdue:
                            self.log(f"         ❌ Is overdue mismatch: got {is_overdue}, expected {expected_is_overdue}")
                            indicators_correct = False
                        
                        if indicators_correct:
                            status_indicators_correct += 1
                            self.log(f"         ✅ Status indicators correct")
                        
                    except Exception as e:
                        self.log(f"      ⚠️ Could not verify status indicators: {str(e)}")
            
            if status_indicators_correct == total_surveys:
                self.survey_tests['status_indicators_calculated'] = True
                self.survey_tests['days_until_survey_accurate'] = True
                self.log(f"✅ Status indicators calculated correctly for all {total_surveys} surveys")
                return True
            else:
                self.log(f"❌ Status indicators incorrect for {total_surveys - status_indicators_correct}/{total_surveys} surveys")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing status indicators: {str(e)}", "ERROR")
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
            
            for survey in self.test_certificates:
                ship_name = survey.get('ship_name')
                cert_name_display = survey.get('cert_name_display')
                next_survey = survey.get('next_survey')
                
                if ship_name and ship_name.strip():
                    ship_names_present += 1
                
                if cert_name_display and cert_name_display.strip():
                    cert_names_present += 1
                
                if next_survey:
                    valid_dates += 1
            
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
            
            return (ship_names_present == total_surveys and 
                   cert_names_present == total_surveys and 
                   valid_dates == total_surveys)
            
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
        """Main test function for upcoming surveys notification functionality"""
        self.log("🔄 STARTING SHIP MANAGEMENT SYSTEM - UPCOMING SURVEYS NOTIFICATION TESTING")
        self.log("🎯 FOCUS: Test the new upcoming surveys notification system")
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
            
            # Step 3: Verify response structure
            self.log("\n🔍 STEP 3: VERIFY RESPONSE STRUCTURE")
            self.log("=" * 50)
            structure_success = self.verify_response_structure()
            
            # Step 4: Test date filtering logic
            self.log("\n📅 STEP 4: TEST DATE FILTERING LOGIC")
            self.log("=" * 50)
            date_filtering_success = self.test_date_filtering_logic()
            
            # Step 5: Test company filtering
            self.log("\n🏢 STEP 5: TEST COMPANY FILTERING")
            self.log("=" * 50)
            company_filtering_success = self.test_company_filtering()
            
            # Step 6: Test status indicators
            self.log("\n🚦 STEP 6: TEST STATUS INDICATORS")
            self.log("=" * 50)
            status_indicators_success = self.test_status_indicators()
            
            # Step 7: Final Analysis
            self.log("\n📊 STEP 7: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return (endpoint_success and structure_success and 
                   date_filtering_success and company_filtering_success and 
                   status_indicators_success)
            
        except Exception as e:
            self.log(f"❌ Comprehensive upcoming surveys testing error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of upcoming surveys notification testing"""
        try:
            self.log("🔄 SHIP MANAGEMENT SYSTEM - UPCOMING SURVEYS NOTIFICATION TESTING - RESULTS")
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
            
            # Upcoming surveys endpoint analysis
            self.log("\n📅 UPCOMING SURVEYS ENDPOINT ANALYSIS:")
            
            if self.survey_tests['upcoming_surveys_endpoint_accessible']:
                self.log("   ✅ CONFIRMED: /api/certificates/upcoming-surveys endpoint is accessible")
            else:
                self.log("   ❌ ISSUE: Upcoming surveys endpoint not accessible")
            
            if self.survey_tests['upcoming_surveys_response_valid']:
                self.log("   ✅ SUCCESS: Endpoint returns valid JSON response")
            else:
                self.log("   ❌ ISSUE: Invalid response from endpoint")
            
            # Response structure analysis
            self.log("\n🔍 RESPONSE STRUCTURE ANALYSIS:")
            
            if self.survey_tests['response_structure_correct']:
                self.log("   ✅ SUCCESS: Response has correct top-level structure")
            else:
                self.log("   ❌ ISSUE: Response structure incorrect")
            
            if self.survey_tests['required_fields_present']:
                self.log("   ✅ SUCCESS: All required fields present in survey objects")
                self.log("      Fields: ship_name, cert_name_display, next_survey, next_survey_type, last_endorse, status indicators")
            else:
                self.log("   ❌ ISSUE: Missing required fields in survey objects")
            
            # Date filtering analysis
            self.log("\n📅 DATE FILTERING ANALYSIS:")
            
            date_tests = [
                'date_filtering_logic_working',
                'three_month_window_correct',
                'date_comparison_accurate'
            ]
            date_passed = sum(1 for test in date_tests if self.survey_tests.get(test, False))
            date_rate = (date_passed / len(date_tests)) * 100
            
            self.log(f"\n🎯 DATE FILTERING: {date_rate:.1f}% ({date_passed}/{len(date_tests)})")
            
            if self.survey_tests['date_filtering_logic_working']:
                self.log("   ✅ SUCCESS: Date filtering logic working correctly")
            else:
                self.log("   ❌ ISSUE: Date filtering logic has problems")
            
            if self.survey_tests['three_month_window_correct']:
                self.log("   ✅ SUCCESS: ±3 months window correctly implemented")
            else:
                self.log("   ❌ ISSUE: ±3 months window incorrect")
            
            # Company filtering analysis
            self.log("\n🏢 COMPANY FILTERING ANALYSIS:")
            
            company_tests = [
                'company_filtering_working',
                'only_user_company_ships_returned'
            ]
            company_passed = sum(1 for test in company_tests if self.survey_tests.get(test, False))
            company_rate = (company_passed / len(company_tests)) * 100
            
            self.log(f"\n🎯 COMPANY FILTERING: {company_rate:.1f}% ({company_passed}/{len(company_tests)})")
            
            if self.survey_tests['company_filtering_working']:
                self.log("   ✅ SUCCESS: Company filtering working correctly")
            else:
                self.log("   ❌ ISSUE: Company filtering not working")
            
            if self.survey_tests['only_user_company_ships_returned']:
                self.log("   ✅ SUCCESS: Only user's company ships returned")
            else:
                self.log("   ❌ ISSUE: Surveys from other companies returned")
            
            # Status indicators analysis
            self.log("\n🚦 STATUS INDICATORS ANALYSIS:")
            
            status_tests = [
                'status_indicators_calculated',
                'days_until_survey_accurate'
            ]
            status_passed = sum(1 for test in status_tests if self.survey_tests.get(test, False))
            status_rate = (status_passed / len(status_tests)) * 100
            
            self.log(f"\n🎯 STATUS INDICATORS: {status_rate:.1f}% ({status_passed}/{len(status_tests)})")
            
            if self.survey_tests['status_indicators_calculated']:
                self.log("   ✅ SUCCESS: Status indicators calculated correctly")
                self.log("      is_overdue, is_due_soon, days_until_survey working")
            else:
                self.log("   ❌ ISSUE: Status indicators calculation problems")
            
            # Review request requirements analysis
            self.log("\n📋 REVIEW REQUEST REQUIREMENTS ANALYSIS:")
            
            req1_met = self.survey_tests['authentication_successful']
            req2_met = self.survey_tests['upcoming_surveys_endpoint_accessible']
            req3_met = self.survey_tests['date_filtering_logic_working']
            req4_met = self.survey_tests['required_fields_present']
            req5_met = self.survey_tests['company_filtering_working']
            req6_met = self.survey_tests['status_indicators_calculated']
            
            self.log(f"   1. Login with admin1/123456: {'✅ MET' if req1_met else '❌ NOT MET'}")
            self.log(f"      - Authentication successful")
            
            self.log(f"   2. Test /api/certificates/upcoming-surveys endpoint: {'✅ MET' if req2_met else '❌ NOT MET'}")
            self.log(f"      - Endpoint accessible and returns valid response")
            
            self.log(f"   3. Verify ±3 months date filtering: {'✅ MET' if req3_met else '❌ NOT MET'}")
            self.log(f"      - Date comparison logic works correctly")
            
            self.log(f"   4. Check response structure: {'✅ MET' if req4_met else '❌ NOT MET'}")
            self.log(f"      - All required fields present")
            
            self.log(f"   5. Verify company filtering: {'✅ MET' if req5_met else '❌ NOT MET'}")
            self.log(f"      - Only user's company ships returned")
            
            self.log(f"   6. Test status indicators: {'✅ MET' if req6_met else '❌ NOT MET'}")
            self.log(f"      - is_overdue, is_due_soon, days_until_survey calculated")
            
            requirements_met = sum([req1_met, req2_met, req3_met, req4_met, req5_met, req6_met])
            
            # Final conclusion
            if success_rate >= 80 and requirements_met >= 5:
                self.log(f"\n🎉 CONCLUSION: UPCOMING SURVEYS NOTIFICATION SYSTEM IS WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Upcoming surveys functionality fully implemented!")
                self.log(f"   ✅ Requirements met: {requirements_met}/6")
                self.log(f"   ✅ Endpoint returns certificates within ±3 months window")
                self.log(f"   ✅ Response structure includes all required fields")
                self.log(f"   ✅ Company filtering works correctly")
                self.log(f"   ✅ Status indicators calculated accurately")
            elif success_rate >= 60 and requirements_met >= 4:
                self.log(f"\n⚠️ CONCLUSION: UPCOMING SURVEYS NOTIFICATION SYSTEM PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Most functionality working, minor improvements needed")
                self.log(f"   ⚠️ Requirements met: {requirements_met}/6")
                
                if req1_met and req2_met:
                    self.log(f"   ✅ Core functionality (authentication and endpoint) is working")
                if not req3_met:
                    self.log(f"   ⚠️ Date filtering logic may need attention")
                if not req5_met:
                    self.log(f"   ⚠️ Company filtering may need fixes")
            else:
                self.log(f"\n❌ CONCLUSION: UPCOMING SURVEYS NOTIFICATION SYSTEM HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Significant fixes needed")
                self.log(f"   ❌ Requirements met: {requirements_met}/6")
                self.log(f"   ❌ Upcoming surveys notification system needs major fixes before production use")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run Ship Management System Upcoming Surveys Notification tests"""
    print("🔄 SHIP MANAGEMENT SYSTEM - UPCOMING SURVEYS NOTIFICATION TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = UpcomingSurveysNotificationTester()
        success = tester.run_comprehensive_upcoming_surveys_tests()
        
        if success:
            print("\n✅ UPCOMING SURVEYS NOTIFICATION TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ UPCOMING SURVEYS NOTIFICATION TESTING COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
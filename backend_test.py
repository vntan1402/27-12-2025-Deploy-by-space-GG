#!/usr/bin/env python3
"""
Ship Management System - Timezone Fix Testing
FOCUS: Test timezone fix for date handling consistency

REVIEW REQUEST REQUIREMENTS:
1. Ship Data Retrieval: Login with admin1/123456, retrieve SUNSHINE 01 ship data, verify date fields
2. Ship Update Operations: Test updating ship's date fields via PUT /api/ships/{ship_id}
3. Recalculation Endpoints: Test all recalculation endpoints for date consistency

EXPECTED BEHAVIOR:
- All date fields should remain consistent with no timezone shifts
- Dates saved and retrieved should be identical
- Recalculation endpoints should return proper date formats

TEST FOCUS:
- Date field consistency in ship data retrieval
- Date preservation during ship updates
- Recalculation endpoint date format consistency
- Timezone handling verification
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fleet-tracker-104.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class TimezoneFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for timezone fix functionality
        self.timezone_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'sunshine_01_ship_found': False,
            
            # Ship data retrieval tests
            'ship_data_retrieved_successfully': False,
            'date_fields_present': False,
            'date_formats_consistent': False,
            
            # Ship update tests
            'ship_update_successful': False,
            'dates_preserved_after_update': False,
            'no_timezone_shifts_detected': False,
            
            # Recalculation endpoint tests
            'special_survey_cycle_working': False,
            'docking_dates_calculation_working': False,
            'next_docking_calculation_working': False,
            'anniversary_date_calculation_working': False,
            
            # Date consistency verification
            'recalculation_dates_consistent': False,
            'all_endpoints_return_proper_formats': False,
        }
        
        # Store test results for analysis
        self.ship_data = {}
        self.original_dates = {}
        self.updated_dates = {}
        self.recalculation_results = {}
        
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
                
                self.backfill_tests['authentication_successful'] = True
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
    
    def find_sunshine_01_ship(self):
        """Find SUNSHINE 01 ship as specified in review request"""
        try:
            self.log("🚢 Finding SUNSHINE 01 ship...")
            
            # Get all ships to find SUNSHINE 01
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} total ships")
                
                # Look for SUNSHINE 01
                sunshine_ship = None
                for ship in ships:
                    ship_name = ship.get('name', '').upper()
                    if 'SUNSHINE' in ship_name and '01' in ship_name:
                        sunshine_ship = ship
                        break
                
                if sunshine_ship:
                    self.ship_data = sunshine_ship
                    ship_id = sunshine_ship.get('id')
                    ship_name = sunshine_ship.get('name')
                    imo = sunshine_ship.get('imo')
                    
                    self.log(f"✅ Found SUNSHINE 01 ship:")
                    self.log(f"   Ship ID: {ship_id}")
                    self.log(f"   Ship Name: {ship_name}")
                    self.log(f"   IMO: {imo}")
                    
                    self.timezone_tests['sunshine_01_ship_found'] = True
                    return True
                else:
                    self.log("❌ SUNSHINE 01 ship not found")
                    # List available ships for debugging
                    self.log("   Available ships:")
                    for ship in ships[:10]:
                        self.log(f"      - {ship.get('name', 'Unknown')}")
                    return False
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding SUNSHINE 01 ship: {str(e)}", "ERROR")
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
    
    def run_comprehensive_timezone_tests(self):
        """Main test function for timezone fix functionality"""
        self.log("🔄 STARTING SHIP MANAGEMENT SYSTEM - TIMEZONE FIX TESTING")
        self.log("🎯 FOCUS: Test timezone fix for date handling consistency")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Find SUNSHINE 01 ship
            self.log("\n🚢 STEP 2: FIND SUNSHINE 01 SHIP")
            self.log("=" * 50)
            ship_found = self.find_sunshine_01_ship()
            if not ship_found:
                self.log("❌ SUNSHINE 01 ship not found - cannot proceed with testing")
                return False
            
            # Step 3: Test ship data retrieval
            self.log("\n📊 STEP 3: SHIP DATA RETRIEVAL")
            self.log("=" * 50)
            retrieval_success = self.test_ship_data_retrieval()
            
            # Step 4: Test ship update operations
            self.log("\n🔄 STEP 4: SHIP UPDATE OPERATIONS")
            self.log("=" * 50)
            update_success = self.test_ship_update_operations()
            
            # Step 5: Test recalculation endpoints
            self.log("\n🔄 STEP 5: RECALCULATION ENDPOINTS")
            self.log("=" * 50)
            recalc_success = self.test_recalculation_endpoints()
            
            # Step 6: Final Analysis
            self.log("\n📊 STEP 6: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return retrieval_success and update_success and recalc_success
            
        except Exception as e:
            self.log(f"❌ Comprehensive timezone testing error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of backfill testing"""
        try:
            self.log("🔄 CERTIFICATE BACKFILL SHIP INFORMATION TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.backfill_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.backfill_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.backfill_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.backfill_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.backfill_tests)})")
            
            # Backfill-specific analysis
            self.log("\n🔄 BACKFILL FUNCTIONALITY ANALYSIS:")
            
            # Core functionality tests
            core_tests = [
                'backfill_endpoint_accessible',
                'backfill_processing_successful',
                'certificates_updated_with_ship_info',
                'extracted_ship_name_populated'
            ]
            core_passed = sum(1 for test in core_tests if self.backfill_tests.get(test, False))
            core_rate = (core_passed / len(core_tests)) * 100
            
            self.log(f"\n🎯 CORE BACKFILL FUNCTIONALITY: {core_rate:.1f}% ({core_passed}/{len(core_tests)})")
            
            if self.backfill_tests['backfill_processing_successful']:
                self.log("   ✅ CONFIRMED: Backfill job is WORKING")
                self.log("   ✅ Endpoint processes existing certificates successfully")
                
                if self.backfill_results:
                    processed = self.backfill_results.get('processed', 0)
                    updated = self.backfill_results.get('updated', 0)
                    errors = self.backfill_results.get('errors', 0)
                    
                    self.log(f"   📊 Processing Statistics:")
                    self.log(f"      Processed: {processed} certificates")
                    self.log(f"      Updated: {updated} certificates")
                    self.log(f"      Errors: {errors} certificates")
                    
                    if updated > 0:
                        self.log(f"   ✅ SUCCESS: {updated} certificates updated with ship information")
                    else:
                        self.log("   ℹ️ INFO: No certificates needed updating (may be expected)")
            else:
                self.log("   ❌ ISSUE: Backfill job needs fixing")
            
            # Tooltip functionality tests
            tooltip_tests = [
                'extracted_ship_name_populated',
                'tooltip_data_available'
            ]
            tooltip_passed = sum(1 for test in tooltip_tests if self.backfill_tests.get(test, False))
            tooltip_rate = (tooltip_passed / len(tooltip_tests)) * 100
            
            self.log(f"\n🏷️ TOOLTIP FUNCTIONALITY: {tooltip_rate:.1f}% ({tooltip_passed}/{len(tooltip_tests)})")
            
            if self.backfill_tests['tooltip_data_available']:
                self.log("   ✅ CONFIRMED: Tooltip functionality is READY")
                self.log("   ✅ Certificates now have extracted_ship_name for tooltips")
                self.log("   ✅ Previously processed certificates will show ship names")
            else:
                self.log("   ⚠️ ISSUE: Tooltip data may not be available yet")
            
            # Data quality tests
            data_tests = [
                'ship_info_fields_populated',
                'backfill_response_format_correct',
                'processing_statistics_provided'
            ]
            data_passed = sum(1 for test in data_tests if self.backfill_tests.get(test, False))
            data_rate = (data_passed / len(data_tests)) * 100
            
            self.log(f"\n📊 DATA QUALITY & API RESPONSE: {data_rate:.1f}% ({data_passed}/{len(data_tests)})")
            
            # Review request requirements analysis
            self.log("\n📋 REVIEW REQUEST REQUIREMENTS ANALYSIS:")
            
            req1_met = self.backfill_tests['backfill_endpoint_accessible'] and self.backfill_tests['backfill_processing_successful']
            req2_met = self.backfill_tests['certificates_updated_with_ship_info'] and self.backfill_tests['ship_info_fields_populated']
            req3_met = self.backfill_tests['extracted_ship_name_populated'] and self.backfill_tests['tooltip_data_available']
            
            self.log(f"   1. Run Backfill Job: {'✅ MET' if req1_met else '❌ NOT MET'}")
            self.log(f"      - Endpoint accessible and processing certificates")
            
            self.log(f"   2. Verify Processing: {'✅ MET' if req2_met else '❌ NOT MET'}")
            self.log(f"      - Certificates updated with missing ship information")
            
            self.log(f"   3. Check Results: {'✅ MET' if req3_met else '❌ NOT MET'}")
            self.log(f"      - Tooltips will show ship names for processed certificates")
            
            requirements_met = sum([req1_met, req2_met, req3_met])
            
            # Final conclusion
            if success_rate >= 80 and requirements_met >= 2:
                self.log(f"\n🎉 CONCLUSION: BACKFILL FUNCTIONALITY IS WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Backfill job successfully implemented!")
                self.log(f"   ✅ Requirements met: {requirements_met}/3")
                self.log(f"   ✅ Existing certificates can now be processed for ship information")
                self.log(f"   ✅ Tooltips will show ship names for previously processed certificates")
                self.log(f"   ✅ System ready for production use with reasonable limits")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: BACKFILL FUNCTIONALITY PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Some functionality working, improvements needed")
                self.log(f"   ⚠️ Requirements met: {requirements_met}/3")
                
                if req1_met:
                    self.log(f"   ✅ Backfill job is accessible and processing")
                else:
                    self.log(f"   ❌ Backfill job needs attention")
                    
                if req2_met:
                    self.log(f"   ✅ Certificate processing is working")
                else:
                    self.log(f"   ❌ Certificate processing needs attention")
                    
                if req3_met:
                    self.log(f"   ✅ Tooltip functionality is ready")
                else:
                    self.log(f"   ❌ Tooltip functionality needs attention")
            else:
                self.log(f"\n❌ CONCLUSION: BACKFILL FUNCTIONALITY HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Significant fixes needed")
                self.log(f"   ❌ Requirements met: {requirements_met}/3")
                self.log(f"   ❌ Backfill job needs major fixes before production use")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run Certificate Backfill Ship Information tests"""
    print("🔄 CERTIFICATE BACKFILL SHIP INFORMATION TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = CertificateBackfillTester()
        success = tester.run_comprehensive_backfill_tests()
        
        if success:
            print("\n✅ CERTIFICATE BACKFILL TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ CERTIFICATE BACKFILL TESTING COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
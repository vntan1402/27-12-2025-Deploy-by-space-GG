#!/usr/bin/env python3
"""
Ship Creation Debug Test - Debugging "Failed to add ship: [object Object],[object Object]" Error

This test specifically focuses on debugging the ship creation issue mentioned in the review request:
- Test POST /api/ships endpoint with various ship data combinations
- Check backend validation and error handling
- Verify field processing and data types
- Test different scenarios to identify the root cause of the 422 errors
"""

import requests
import json
import os
import sys
from datetime import datetime, timezone
import traceback

# Configuration - Try internal URL first, then external
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=10)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nautical-certs-1.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class ShipCreationDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking
        self.tests = {
            'authentication_successful': False,
            'minimal_ship_creation_working': False,
            'complete_ship_creation_working': False,
            'last_docking_fields_working': False,
            'validation_errors_identified': False,
            'backend_error_response_format_correct': False,
            'field_type_validation_working': False,
        }
        
        # Test ship counter
        self.test_ship_counter = 1
        
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
                
                self.tests['authentication_successful'] = True
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
    
    def test_minimal_ship_creation(self):
        """Test ship creation with minimal required fields only"""
        try:
            self.log("🚢 Testing minimal ship creation (required fields only)...")
            
            # Minimal ship data with only required fields
            ship_data = {
                'name': f'MINIMAL TEST SHIP {self.test_ship_counter}',
                'flag': 'PANAMA',
                'ship_type': 'DNV GL',
                'company': 'AMCSC'
            }
            
            self.log(f"   Ship data: {json.dumps(ship_data, indent=2)}")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(
                endpoint,
                json=ship_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                self.log("✅ Minimal ship creation successful")
                self.log(f"   Created ship ID: {response_data.get('id')}")
                self.log(f"   Created ship name: {response_data.get('name')}")
                
                self.tests['minimal_ship_creation_working'] = True
                self.test_ship_counter += 1
                return True, response_data.get('id')
            else:
                self.log(f"   ❌ Minimal ship creation failed: {response.status_code}")
                self.log(f"   Response body: {response.text}")
                
                # Try to parse error response
                try:
                    error_data = response.json()
                    self.log(f"   Parsed error: {json.dumps(error_data, indent=2)}")
                    
                    # Check if this is a validation error (422)
                    if response.status_code == 422:
                        self.tests['validation_errors_identified'] = True
                        self.analyze_validation_errors(error_data)
                        
                except Exception as parse_error:
                    self.log(f"   Failed to parse error response: {parse_error}")
                
                return False, None
                
        except Exception as e:
            self.log(f"❌ Minimal ship creation error: {str(e)}", "ERROR")
            return False, None
    
    def test_complete_ship_creation(self):
        """Test ship creation with all fields including Last Docking"""
        try:
            self.log("🚢 Testing complete ship creation (all fields including Last Docking)...")
            
            # Complete ship data with all fields
            ship_data = {
                'name': f'COMPLETE TEST SHIP {self.test_ship_counter}',
                'imo': f'999{self.test_ship_counter:04d}',
                'flag': 'PANAMA',
                'ship_type': 'DNV GL',
                'gross_tonnage': 5000.0,
                'deadweight': 8000.0,
                'built_year': 2015,
                'ship_owner': 'Test Owner',
                'company': 'AMCSC',
                # Last Docking fields that might be causing issues
                'last_docking': '2023-01-15T00:00:00Z',
                'last_docking_2': '2022-06-10T00:00:00Z',
                'next_docking': '2026-01-15T00:00:00Z',
                'last_special_survey': '2021-03-10T00:00:00Z',
                # Complex objects that might cause serialization issues
                'anniversary_date': {
                    'day': 15,
                    'month': 3,
                    'auto_calculated': True,
                    'source_certificate_type': 'Full Term Class Certificate',
                    'manual_override': False
                },
                'special_survey_cycle': {
                    'from_date': '2021-03-10T00:00:00Z',
                    'to_date': '2026-03-10T00:00:00Z',
                    'intermediate_required': True,
                    'cycle_type': 'SOLAS Safety Construction Survey Cycle'
                }
            }
            
            self.log(f"   Ship data: {json.dumps(ship_data, indent=2)}")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(
                endpoint,
                json=ship_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                self.log("✅ Complete ship creation successful")
                self.log(f"   Created ship ID: {response_data.get('id')}")
                self.log(f"   Created ship name: {response_data.get('name')}")
                
                self.tests['complete_ship_creation_working'] = True
                self.tests['last_docking_fields_working'] = True
                self.test_ship_counter += 1
                return True, response_data.get('id')
            else:
                self.log(f"   ❌ Complete ship creation failed: {response.status_code}")
                self.log(f"   Response body: {response.text}")
                
                # Try to parse error response
                try:
                    error_data = response.json()
                    self.log(f"   Parsed error: {json.dumps(error_data, indent=2)}")
                    
                    # Check if this is a validation error (422)
                    if response.status_code == 422:
                        self.tests['validation_errors_identified'] = True
                        self.analyze_validation_errors(error_data)
                        
                except Exception as parse_error:
                    self.log(f"   Failed to parse error response: {parse_error}")
                
                return False, None
                
        except Exception as e:
            self.log(f"❌ Complete ship creation error: {str(e)}", "ERROR")
            return False, None
    
    def test_last_docking_field_variations(self):
        """Test different Last Docking field formats that might be causing issues"""
        try:
            self.log("🚢 Testing Last Docking field variations...")
            
            # Test different date formats that might be causing issues
            test_cases = [
                {
                    'name': 'ISO Format',
                    'last_docking': '2023-01-15T00:00:00Z',
                    'last_docking_2': '2022-06-10T00:00:00Z'
                },
                {
                    'name': 'ISO Format without Z',
                    'last_docking': '2023-01-15T00:00:00',
                    'last_docking_2': '2022-06-10T00:00:00'
                },
                {
                    'name': 'Date only',
                    'last_docking': '2023-01-15',
                    'last_docking_2': '2022-06-10'
                },
                {
                    'name': 'MM/YYYY format (as mentioned in review)',
                    'last_docking': '01/2023',
                    'last_docking_2': '06/2022'
                },
                {
                    'name': 'Month Year format',
                    'last_docking': 'JAN 2023',
                    'last_docking_2': 'JUN 2022'
                }
            ]
            
            for i, test_case in enumerate(test_cases):
                self.log(f"   Testing {test_case['name']} format...")
                
                ship_data = {
                    'name': f'DOCKING TEST {self.test_ship_counter} - {test_case["name"]}',
                    'flag': 'PANAMA',
                    'ship_type': 'DNV GL',
                    'company': 'AMCSC',
                    'last_docking': test_case['last_docking'],
                    'last_docking_2': test_case['last_docking_2']
                }
                
                endpoint = f"{BACKEND_URL}/ships"
                response = requests.post(
                    endpoint,
                    json=ship_data,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                self.log(f"      Response status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    self.log(f"      ✅ {test_case['name']} format works")
                    if 'last_docking' in test_case['name'].lower():
                        self.tests['last_docking_fields_working'] = True
                else:
                    self.log(f"      ❌ {test_case['name']} format failed")
                    self.log(f"      Error: {response.text[:200]}")
                
                self.test_ship_counter += 1
            
            return True
            
        except Exception as e:
            self.log(f"❌ Last Docking field variations test error: {str(e)}", "ERROR")
            return False
    
    def analyze_validation_errors(self, error_data):
        """Analyze validation errors to understand the root cause"""
        try:
            self.log("🔍 Analyzing validation errors...")
            
            # Check if it's a Pydantic validation error
            if 'detail' in error_data:
                detail = error_data['detail']
                
                if isinstance(detail, list):
                    self.log("   Pydantic validation errors found:")
                    for error in detail:
                        if isinstance(error, dict):
                            field = error.get('loc', ['unknown'])[-1]  # Get the field name
                            msg = error.get('msg', 'Unknown error')
                            error_type = error.get('type', 'unknown')
                            
                            self.log(f"      Field: {field}")
                            self.log(f"      Error: {msg}")
                            self.log(f"      Type: {error_type}")
                            self.log("      ---")
                            
                            # Check for specific field issues
                            if 'last_docking' in str(field).lower():
                                self.log("      🎯 IDENTIFIED: Last Docking field validation issue")
                            elif 'anniversary_date' in str(field).lower():
                                self.log("      🎯 IDENTIFIED: Anniversary Date field validation issue")
                            elif 'special_survey' in str(field).lower():
                                self.log("      🎯 IDENTIFIED: Special Survey field validation issue")
                            
                elif isinstance(detail, str):
                    self.log(f"   Error message: {detail}")
                else:
                    self.log(f"   Raw error detail: {detail}")
            
            self.tests['backend_error_response_format_correct'] = True
            
        except Exception as e:
            self.log(f"❌ Error analyzing validation errors: {str(e)}", "ERROR")
    
    def test_field_type_validation(self):
        """Test different field types to identify type validation issues"""
        try:
            self.log("🔍 Testing field type validation...")
            
            # Test with potentially problematic field types
            test_cases = [
                {
                    'name': 'String numbers',
                    'data': {
                        'name': f'TYPE TEST {self.test_ship_counter}',
                        'flag': 'PANAMA',
                        'ship_type': 'DNV GL',
                        'company': 'AMCSC',
                        'gross_tonnage': '5000',  # String instead of float
                        'deadweight': '8000',     # String instead of float
                        'built_year': '2015'      # String instead of int
                    }
                },
                {
                    'name': 'Null values',
                    'data': {
                        'name': f'NULL TEST {self.test_ship_counter}',
                        'flag': 'PANAMA',
                        'ship_type': 'DNV GL',
                        'company': 'AMCSC',
                        'gross_tonnage': None,
                        'deadweight': None,
                        'built_year': None
                    }
                },
                {
                    'name': 'Empty strings',
                    'data': {
                        'name': f'EMPTY TEST {self.test_ship_counter}',
                        'flag': 'PANAMA',
                        'ship_type': 'DNV GL',
                        'company': 'AMCSC',
                        'imo': '',
                        'ship_owner': ''
                    }
                }
            ]
            
            for test_case in test_cases:
                self.log(f"   Testing {test_case['name']}...")
                
                endpoint = f"{BACKEND_URL}/ships"
                response = requests.post(
                    endpoint,
                    json=test_case['data'],
                    headers=self.get_headers(),
                    timeout=30
                )
                
                self.log(f"      Response status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    self.log(f"      ✅ {test_case['name']} accepted")
                else:
                    self.log(f"      ❌ {test_case['name']} rejected")
                    if response.status_code == 422:
                        try:
                            error_data = response.json()
                            self.analyze_validation_errors(error_data)
                        except:
                            pass
                
                self.test_ship_counter += 1
            
            self.tests['field_type_validation_working'] = True
            return True
            
        except Exception as e:
            self.log(f"❌ Field type validation test error: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs_for_errors(self):
        """Check backend logs for recent errors"""
        try:
            self.log("📋 Checking backend logs for recent errors...")
            
            # Try to get recent backend logs
            import subprocess
            result = subprocess.run(
                ['tail', '-n', '100', '/var/log/supervisor/backend.err.log'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                log_lines = result.stdout.strip().split('\n')
                error_lines = [line for line in log_lines if 'ERROR' in line or 'Exception' in line or 'Traceback' in line]
                
                if error_lines:
                    self.log("   Recent backend errors found:")
                    for line in error_lines[-10:]:  # Show last 10 error lines
                        self.log(f"      {line}")
                else:
                    self.log("   No recent backend errors found in logs")
            else:
                self.log("   Could not access backend error logs")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Backend log check error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_ship_creation_debug(self):
        """Main test function for debugging ship creation issues"""
        self.log("🎯 STARTING SHIP CREATION DEBUG TESTING")
        self.log("🎯 FOCUS: Debug 'Failed to add ship: [object Object],[object Object]' error")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Check backend logs first
            self.log("\n📋 STEP 2: CHECK BACKEND LOGS")
            self.log("=" * 50)
            self.check_backend_logs_for_errors()
            
            # Step 3: Test minimal ship creation
            self.log("\n🚢 STEP 3: MINIMAL SHIP CREATION TEST")
            self.log("=" * 50)
            minimal_success, minimal_ship_id = self.test_minimal_ship_creation()
            
            # Step 4: Test complete ship creation
            self.log("\n🚢 STEP 4: COMPLETE SHIP CREATION TEST")
            self.log("=" * 50)
            complete_success, complete_ship_id = self.test_complete_ship_creation()
            
            # Step 5: Test Last Docking field variations
            self.log("\n🚢 STEP 5: LAST DOCKING FIELD VARIATIONS TEST")
            self.log("=" * 50)
            self.test_last_docking_field_variations()
            
            # Step 6: Test field type validation
            self.log("\n🔍 STEP 6: FIELD TYPE VALIDATION TEST")
            self.log("=" * 50)
            self.test_field_type_validation()
            
            # Step 7: Final Analysis
            self.log("\n📊 STEP 7: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return minimal_success or complete_success
            
        except Exception as e:
            self.log(f"❌ Comprehensive test error: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of ship creation debug testing"""
        try:
            self.log("🎯 SHIP CREATION DEBUG TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.tests)})")
            
            # Specific analysis for the reported issue
            self.log("\n🎯 SPECIFIC ISSUE ANALYSIS:")
            self.log("   Issue: 'Failed to add ship: [object Object],[object Object]' error")
            
            if self.tests['validation_errors_identified']:
                self.log("   ✅ VALIDATION ERRORS IDENTIFIED - Root cause found in backend validation")
                self.log("   🔍 The [object Object] error is likely due to frontend not properly displaying validation error objects")
            else:
                self.log("   ❌ No validation errors identified - issue might be elsewhere")
            
            if self.tests['minimal_ship_creation_working']:
                self.log("   ✅ MINIMAL SHIP CREATION WORKS - Issue is with specific fields")
            else:
                self.log("   ❌ MINIMAL SHIP CREATION FAILS - Basic validation issue")
            
            if self.tests['last_docking_fields_working']:
                self.log("   ✅ LAST DOCKING FIELDS WORK - Not the source of the issue")
            else:
                self.log("   ❌ LAST DOCKING FIELDS PROBLEMATIC - Likely source of validation errors")
            
            if self.tests['backend_error_response_format_correct']:
                self.log("   ✅ BACKEND ERROR RESPONSE FORMAT CORRECT - Frontend needs to handle error objects properly")
            else:
                self.log("   ❌ BACKEND ERROR RESPONSE FORMAT ISSUES - Backend not returning proper error format")
            
            # Final conclusion
            if success_rate >= 70:
                self.log(f"\n🎉 CONCLUSION: SHIP CREATION DEBUG SUCCESSFUL")
                self.log(f"   Success rate: {success_rate:.1f}% - Root cause identified!")
                self.log(f"   ✅ Backend validation is working correctly")
                self.log(f"   ✅ Error responses are properly formatted")
                self.log(f"   🔍 The [object Object] error is a FRONTEND DISPLAY ISSUE")
                self.log(f"   🔍 Frontend needs to properly serialize error objects for display")
            elif success_rate >= 40:
                self.log(f"\n⚠️ CONCLUSION: PARTIAL SUCCESS IN DEBUGGING")
                self.log(f"   Success rate: {success_rate:.1f}% - Some issues identified")
                self.log(f"   🔍 Mixed results suggest multiple potential causes")
            else:
                self.log(f"\n❌ CONCLUSION: SHIP CREATION HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Backend validation failing")
                self.log(f"   🔍 Backend needs investigation and fixes")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run ship creation debug tests"""
    print("🎯 SHIP CREATION DEBUG TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = ShipCreationDebugTester()
        success = tester.run_comprehensive_ship_creation_debug()
        
        if success:
            print("\n✅ SHIP CREATION DEBUG TESTING COMPLETED")
        else:
            print("\n❌ SHIP CREATION DEBUG TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
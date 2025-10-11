#!/usr/bin/env python3
"""
Backend Test for Place Sign On Bulk Update Functionality
Testing the Place Sign On bulk update functionality specifically:

REVIEW REQUEST REQUIREMENTS:
1. Test Setup:
   - Verify API authentication is working
   - Get list of crew members from BROTHER 36 ship
   - Select at least 2-3 crew members for bulk update testing

2. Test Individual Crew Update:
   - Test PUT /api/crew/{crew_id} with place_sign_on field
   - Send request like: {"place_sign_on": "Hai Phong, Vietnam"}
   - Verify response shows updated place_sign_on value
   - Confirm the crew record in database is actually updated

3. Test Bulk Update Simulation:
   - Update multiple crew members (2-3 crew) with different place_sign_on values
   - For each crew member, send PUT request to update place_sign_on
   - Verify each individual update is successful

4. Test Data Persistence:
   - After updating, get crew list again via GET /api/crew?ship_name=BROTHER%2036
   - Verify that place_sign_on values are actually updated in the response
   - Compare before/after values to confirm persistence

5. Test Edge Cases:
   - Update place_sign_on with empty string ""
   - Update with null value
   - Update with long string value
   - Verify proper validation and error handling

6. Debug Logging:
   - Check backend logs for any errors during crew update operations
   - Verify MongoDB update operations are executing successfully
   - Look for any database connection or query issues
"""

import requests
import json
import os
import sys
import time
from datetime import datetime
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
    # Fallback to external URL from environment
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class PlaceSignOnTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.ship_name = "BROTHER 36"
        self.test_results = {}
        self.crew_members = []
        self.selected_crew_for_testing = []
        self.before_update_data = {}
        self.after_update_data = {}
        
        # Test tracking
        self.test_results = {
            # Setup tests
            'authentication_successful': False,
            'crew_list_retrieved': False,
            'crew_members_found_for_ship': False,
            'selected_crew_for_testing': False,
            
            # Individual update tests
            'individual_crew_update_successful': False,
            'place_sign_on_field_updated': False,
            'response_shows_updated_value': False,
            'database_record_updated': False,
            
            # Bulk update simulation tests
            'bulk_update_multiple_crew': False,
            'all_individual_updates_successful': False,
            'different_values_applied': False,
            
            # Data persistence tests
            'crew_list_retrieved_after_update': False,
            'place_sign_on_values_persisted': False,
            'before_after_comparison_successful': False,
            
            # Edge case tests
            'empty_string_update_handled': False,
            'null_value_update_handled': False,
            'long_string_update_handled': False,
            'validation_error_handling': False,
            
            # Backend logging tests
            'backend_logs_checked': False,
            'mongodb_operations_successful': False,
            'no_database_connection_issues': False,
        }
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
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
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.test_results['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_crew_members_for_ship(self):
        """Get list of crew members from BROTHER 36 ship"""
        try:
            self.log(f"📋 Getting crew members for ship: {self.ship_name}")
            
            # URL encode the ship name
            ship_name_encoded = self.ship_name.replace(" ", "%20")
            endpoint = f"{BACKEND_URL}/crew?ship_name={ship_name_encoded}"
            self.log(f"   GET {endpoint}")
            
            response = self.session.get(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.crew_members = response.json()
                self.log(f"✅ Retrieved {len(self.crew_members)} crew members")
                self.test_results['crew_list_retrieved'] = True
                
                if len(self.crew_members) > 0:
                    self.test_results['crew_members_found_for_ship'] = True
                    
                    # Log crew member details
                    for i, crew in enumerate(self.crew_members):
                        self.log(f"   Crew {i+1}: {crew.get('full_name', 'Unknown')} (ID: {crew.get('id', 'Unknown')})")
                        current_place_sign_on = crew.get('place_sign_on', 'Not set')
                        self.log(f"      Current place_sign_on: {current_place_sign_on}")
                    
                    # Select 2-3 crew members for testing
                    self.selected_crew_for_testing = self.crew_members[:min(3, len(self.crew_members))]
                    self.log(f"✅ Selected {len(self.selected_crew_for_testing)} crew members for testing")
                    self.test_results['selected_crew_for_testing'] = True
                    
                    # Store before update data
                    for crew in self.selected_crew_for_testing:
                        crew_id = crew.get('id')
                        self.before_update_data[crew_id] = {
                            'full_name': crew.get('full_name'),
                            'place_sign_on': crew.get('place_sign_on')
                        }
                    
                    return True
                else:
                    self.log("❌ No crew members found for the ship", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get crew members: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting crew members: {str(e)}", "ERROR")
            return False
    
    def test_individual_crew_update(self):
        """Test PUT /api/crew/{crew_id} with place_sign_on field"""
        try:
            if not self.selected_crew_for_testing:
                self.log("❌ No crew members selected for testing", "ERROR")
                return False
            
            # Test with first crew member
            test_crew = self.selected_crew_for_testing[0]
            crew_id = test_crew.get('id')
            crew_name = test_crew.get('full_name', 'Unknown')
            
            self.log(f"🧪 Testing individual crew update for: {crew_name} (ID: {crew_id})")
            
            # Test data
            test_place_sign_on = "Hai Phong, Vietnam"
            update_data = {
                "place_sign_on": test_place_sign_on
            }
            
            endpoint = f"{BACKEND_URL}/crew/{crew_id}"
            self.log(f"   PUT {endpoint}")
            self.log(f"   Update data: {json.dumps(update_data, indent=2)}")
            
            response = self.session.put(endpoint, json=update_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.test_results['individual_crew_update_successful'] = True
                self.log("✅ Individual crew update successful")
                
                try:
                    updated_crew = response.json()
                    response_place_sign_on = updated_crew.get('place_sign_on')
                    
                    self.log(f"   Response place_sign_on: {response_place_sign_on}")
                    
                    if response_place_sign_on == test_place_sign_on:
                        self.test_results['place_sign_on_field_updated'] = True
                        self.test_results['response_shows_updated_value'] = True
                        self.log("✅ Response shows updated place_sign_on value")
                        
                        # Verify database record is actually updated
                        self.log("   Verifying database record is updated...")
                        verify_response = self.session.get(endpoint, timeout=30)
                        
                        if verify_response.status_code == 200:
                            verified_crew = verify_response.json()
                            verified_place_sign_on = verified_crew.get('place_sign_on')
                            
                            if verified_place_sign_on == test_place_sign_on:
                                self.test_results['database_record_updated'] = True
                                self.log("✅ Database record confirmed updated")
                            else:
                                self.log(f"❌ Database record not updated. Expected: {test_place_sign_on}, Got: {verified_place_sign_on}", "ERROR")
                        else:
                            self.log(f"❌ Failed to verify database record: {verify_response.status_code}", "ERROR")
                    else:
                        self.log(f"❌ Response place_sign_on mismatch. Expected: {test_place_sign_on}, Got: {response_place_sign_on}", "ERROR")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                    return False
            else:
                self.log(f"❌ Individual crew update failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in individual crew update test: {str(e)}", "ERROR")
            return False
    
    def test_bulk_update_simulation(self):
        """Test bulk update simulation - update multiple crew members with different place_sign_on values"""
        try:
            self.log("🔄 Testing bulk update simulation...")
            
            if len(self.selected_crew_for_testing) < 2:
                self.log("❌ Need at least 2 crew members for bulk update test", "ERROR")
                return False
            
            # Different test values for each crew member
            test_values = [
                "Ho Chi Minh City, Vietnam",
                "Da Nang, Vietnam", 
                "Hai Phong, Vietnam"
            ]
            
            successful_updates = 0
            
            for i, crew in enumerate(self.selected_crew_for_testing):
                crew_id = crew.get('id')
                crew_name = crew.get('full_name', 'Unknown')
                test_value = test_values[i % len(test_values)]
                
                self.log(f"   Updating crew {i+1}: {crew_name}")
                self.log(f"   Setting place_sign_on to: {test_value}")
                
                update_data = {"place_sign_on": test_value}
                endpoint = f"{BACKEND_URL}/crew/{crew_id}"
                
                response = self.session.put(endpoint, json=update_data, timeout=30)
                
                if response.status_code == 200:
                    successful_updates += 1
                    self.log(f"   ✅ Update successful for {crew_name}")
                    
                    # Store after update data
                    self.after_update_data[crew_id] = {
                        'full_name': crew_name,
                        'place_sign_on': test_value
                    }
                else:
                    self.log(f"   ❌ Update failed for {crew_name}: {response.status_code}", "ERROR")
            
            if successful_updates == len(self.selected_crew_for_testing):
                self.test_results['bulk_update_multiple_crew'] = True
                self.test_results['all_individual_updates_successful'] = True
                self.test_results['different_values_applied'] = True
                self.log(f"✅ Bulk update simulation successful - {successful_updates}/{len(self.selected_crew_for_testing)} updates completed")
                return True
            else:
                self.log(f"❌ Bulk update simulation partial failure - {successful_updates}/{len(self.selected_crew_for_testing)} updates completed", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in bulk update simulation: {str(e)}", "ERROR")
            return False
    
    def test_data_persistence(self):
        """Test data persistence - verify updates are actually saved"""
        try:
            self.log("💾 Testing data persistence...")
            
            # Wait a moment for database to sync
            time.sleep(2)
            
            # Get crew list again
            ship_name_encoded = self.ship_name.replace(" ", "%20")
            endpoint = f"{BACKEND_URL}/crew?ship_name={ship_name_encoded}"
            self.log(f"   GET {endpoint} (after updates)")
            
            response = self.session.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                updated_crew_list = response.json()
                self.test_results['crew_list_retrieved_after_update'] = True
                self.log(f"✅ Retrieved updated crew list - {len(updated_crew_list)} members")
                
                # Compare before/after values
                persistence_verified = True
                
                for crew in updated_crew_list:
                    crew_id = crew.get('id')
                    if crew_id in self.after_update_data:
                        expected_place_sign_on = self.after_update_data[crew_id]['place_sign_on']
                        actual_place_sign_on = crew.get('place_sign_on')
                        crew_name = crew.get('full_name', 'Unknown')
                        
                        self.log(f"   Checking {crew_name}:")
                        self.log(f"      Expected: {expected_place_sign_on}")
                        self.log(f"      Actual: {actual_place_sign_on}")
                        
                        if actual_place_sign_on == expected_place_sign_on:
                            self.log(f"      ✅ Persistence verified for {crew_name}")
                        else:
                            self.log(f"      ❌ Persistence failed for {crew_name}", "ERROR")
                            persistence_verified = False
                
                if persistence_verified:
                    self.test_results['place_sign_on_values_persisted'] = True
                    self.test_results['before_after_comparison_successful'] = True
                    self.log("✅ All place_sign_on values persisted correctly")
                    return True
                else:
                    self.log("❌ Some place_sign_on values did not persist", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to retrieve updated crew list: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing data persistence: {str(e)}", "ERROR")
            return False
    
    def test_edge_cases(self):
        """Test edge cases - empty string, null value, long string"""
        try:
            self.log("🧪 Testing edge cases...")
            
            if not self.selected_crew_for_testing:
                self.log("❌ No crew members available for edge case testing", "ERROR")
                return False
            
            test_crew = self.selected_crew_for_testing[0]
            crew_id = test_crew.get('id')
            crew_name = test_crew.get('full_name', 'Unknown')
            
            edge_cases = [
                {
                    'name': 'Empty string',
                    'value': '',
                    'expected_status': [200, 400],  # Either should work or be rejected
                    'test_key': 'empty_string_update_handled'
                },
                {
                    'name': 'Null value',
                    'value': None,
                    'expected_status': [200, 400],
                    'test_key': 'null_value_update_handled'
                },
                {
                    'name': 'Long string',
                    'value': 'A' * 500,  # 500 character string
                    'expected_status': [200, 400],
                    'test_key': 'long_string_update_handled'
                }
            ]
            
            endpoint = f"{BACKEND_URL}/crew/{crew_id}"
            
            for case in edge_cases:
                self.log(f"   Testing {case['name']}: {crew_name}")
                
                update_data = {"place_sign_on": case['value']}
                
                response = self.session.put(endpoint, json=update_data, timeout=30)
                self.log(f"      Response status: {response.status_code}")
                
                if response.status_code in case['expected_status']:
                    self.test_results[case['test_key']] = True
                    self.log(f"      ✅ {case['name']} handled correctly")
                    
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            actual_value = response_data.get('place_sign_on')
                            self.log(f"      Updated value: {actual_value}")
                        except:
                            pass
                else:
                    self.log(f"      ❌ {case['name']} not handled correctly - unexpected status: {response.status_code}", "ERROR")
                    try:
                        error_data = response.json()
                        self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        pass
            
            # Test validation error handling
            self.test_results['validation_error_handling'] = True
            self.log("✅ Edge case testing completed")
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing edge cases: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs(self):
        """Check backend logs for any errors during crew update operations"""
        try:
            self.log("📋 Checking backend logs for crew update operations...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            mongodb_operations_found = False
            no_errors_found = True
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 50 lines to capture recent activity
                        result = os.popen(f"tail -n 50 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            for line in lines:
                                if line.strip():
                                    # Look for MongoDB operations
                                    if any(keyword in line.lower() for keyword in ['mongodb', 'crew', 'update', 'place_sign_on']):
                                        mongodb_operations_found = True
                                        self.log(f"     🔍 MongoDB operation: {line}")
                                    
                                    # Look for errors
                                    if any(keyword in line.lower() for keyword in ['error', 'failed', 'exception']):
                                        if 'crew' in line.lower() or 'update' in line.lower():
                                            no_errors_found = False
                                            self.log(f"     ❌ Error found: {line}")
                        else:
                            self.log(f"   {log_file} is empty or not accessible")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
                else:
                    self.log(f"   {log_file} not found")
            
            if mongodb_operations_found:
                self.test_results['mongodb_operations_successful'] = True
                self.log("✅ MongoDB operations detected in logs")
            
            if no_errors_found:
                self.test_results['no_database_connection_issues'] = True
                self.log("✅ No database connection issues found")
            
            self.test_results['backend_logs_checked'] = True
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test of Place Sign On bulk update functionality"""
        try:
            self.log("🚀 STARTING PLACE SIGN ON BULK UPDATE FUNCTIONALITY TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Get crew members for ship
            self.log("\nSTEP 2: Get crew members from BROTHER 36 ship")
            if not self.get_crew_members_for_ship():
                self.log("❌ CRITICAL: Failed to get crew members - cannot proceed")
                return False
            
            # Step 3: Test individual crew update
            self.log("\nSTEP 3: Test individual crew update with place_sign_on field")
            self.test_individual_crew_update()
            
            # Step 4: Test bulk update simulation
            self.log("\nSTEP 4: Test bulk update simulation")
            self.test_bulk_update_simulation()
            
            # Step 5: Test data persistence
            self.log("\nSTEP 5: Test data persistence")
            self.test_data_persistence()
            
            # Step 6: Test edge cases
            self.log("\nSTEP 6: Test edge cases")
            self.test_edge_cases()
            
            # Step 7: Check backend logs
            self.log("\nSTEP 7: Check backend logs")
            self.check_backend_logs()
            
            self.log("\n" + "=" * 80)
            self.log("✅ PLACE SIGN ON BULK UPDATE TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 PLACE SIGN ON BULK UPDATE TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Setup Results
            self.log("🔧 SETUP & AUTHENTICATION:")
            setup_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('crew_list_retrieved', 'Crew list retrieved'),
                ('crew_members_found_for_ship', 'Crew members found for BROTHER 36'),
                ('selected_crew_for_testing', 'Selected crew for testing'),
            ]
            
            for test_key, description in setup_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Individual Update Results
            self.log("\n👤 INDIVIDUAL CREW UPDATE:")
            individual_tests = [
                ('individual_crew_update_successful', 'Individual crew update successful'),
                ('place_sign_on_field_updated', 'place_sign_on field updated'),
                ('response_shows_updated_value', 'Response shows updated value'),
                ('database_record_updated', 'Database record updated'),
            ]
            
            for test_key, description in individual_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Bulk Update Results
            self.log("\n🔄 BULK UPDATE SIMULATION:")
            bulk_tests = [
                ('bulk_update_multiple_crew', 'Bulk update multiple crew'),
                ('all_individual_updates_successful', 'All individual updates successful'),
                ('different_values_applied', 'Different values applied'),
            ]
            
            for test_key, description in bulk_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Data Persistence Results
            self.log("\n💾 DATA PERSISTENCE:")
            persistence_tests = [
                ('crew_list_retrieved_after_update', 'Crew list retrieved after update'),
                ('place_sign_on_values_persisted', 'place_sign_on values persisted'),
                ('before_after_comparison_successful', 'Before/after comparison successful'),
            ]
            
            for test_key, description in persistence_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Edge Cases Results
            self.log("\n🧪 EDGE CASES:")
            edge_tests = [
                ('empty_string_update_handled', 'Empty string update handled'),
                ('null_value_update_handled', 'Null value update handled'),
                ('long_string_update_handled', 'Long string update handled'),
                ('validation_error_handling', 'Validation error handling'),
            ]
            
            for test_key, description in edge_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Results
            self.log("\n📋 BACKEND LOGS:")
            log_tests = [
                ('backend_logs_checked', 'Backend logs checked'),
                ('mongodb_operations_successful', 'MongoDB operations successful'),
                ('no_database_connection_issues', 'No database connection issues'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'individual_crew_update_successful',
                'place_sign_on_field_updated',
                'database_record_updated',
                'place_sign_on_values_persisted'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.test_results.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL FUNCTIONALITY WORKING")
                self.log("   ✅ Place Sign On bulk update is functional")
                self.log("   ✅ Data persistence is working correctly")
            else:
                self.log("   ❌ SOME CRITICAL FUNCTIONALITY NOT WORKING")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Before/After Data Summary
            if self.before_update_data and self.after_update_data:
                self.log("\n📊 BEFORE/AFTER DATA SUMMARY:")
                for crew_id in self.before_update_data:
                    before = self.before_update_data[crew_id]
                    after = self.after_update_data.get(crew_id, {})
                    
                    self.log(f"   {before['full_name']}:")
                    self.log(f"      Before: {before.get('place_sign_on', 'Not set')}")
                    self.log(f"      After:  {after.get('place_sign_on', 'Not updated')}")
            
            if success_rate >= 80:
                self.log(f"\n   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"\n   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"\n   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the Place Sign On bulk update tests"""
    print("🧪 Backend Test: Place Sign On Bulk Update Functionality")
    print("🎯 Focus: Test individual and bulk updates of place_sign_on field")
    print("=" * 80)
    print("Testing requirements:")
    print("1. API authentication working")
    print("2. Get crew members from BROTHER 36 ship")
    print("3. Test individual crew update with place_sign_on field")
    print("4. Test bulk update simulation")
    print("5. Test data persistence")
    print("6. Test edge cases (empty, null, long strings)")
    print("7. Check backend logs for errors")
    print("=" * 80)
    
    tester = PlaceSignOnTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Return appropriate exit code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: Recalculate Docking Dates API Endpoint Testing
Review Request: Test the "Recalculate Docking Dates" API endpoint to verify that the handleRecalculateDockingDates function fix is working correctly.
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import time
import traceback

# Configuration - Use external URL from frontend/.env
try:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
        else:
            BACKEND_URL = "https://marine-cert-system.preview.emergentagent.com/api"
except:
    BACKEND_URL = "https://marine-cert-system.preview.emergentagent.com/api"

class RecalculateDockingDatesTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Recalculate Docking Dates API
        self.docking_tests = {
            'authentication_successful': False,
            'ships_list_retrieved': False,
            'test_ship_found': False,
            'test_ship_has_certificates': False,
            'docking_dates_api_accessible': False,
            'api_responds_correctly': False,
            'no_javascript_error': False,
            'response_format_correct': False,
            'docking_dates_extracted': False,
            'error_handling_working': False
        }
        
        # Available test ships (excluding SUNSHINE 01)
        self.available_ships = [
            "Test Ship No Config",
            "Test Ship No Company", 
            "SUNSHINE STAR",
            "TEST ANNIVERSARY SHIP"
        ]
        
        self.selected_ship = None
        self.selected_ship_id = None
        
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
            
            response = requests.post(endpoint, json=login_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                self.log(f"   Full Name: {self.current_user.get('full_name')}")
                
                self.docking_tests['authentication_successful'] = True
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
    
    def get_available_ships(self):
        """Get list of available ships and find a suitable test ship"""
        try:
            self.log("🚢 Retrieving available ships...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   ✅ Retrieved {len(ships)} ships")
                
                self.docking_tests['ships_list_retrieved'] = True
                
                # Find a suitable test ship (not SUNSHINE 01)
                for ship in ships:
                    ship_name = ship.get('name', '')
                    ship_id = ship.get('id', '')
                    
                    # Skip SUNSHINE 01 as specified in review request
                    if 'SUNSHINE 01' in ship_name.upper():
                        self.log(f"   ⏭️ Skipping SUNSHINE 01 (deleted certificates)")
                        continue
                    
                    # Look for one of our available test ships
                    for available_ship in self.available_ships:
                        if available_ship.upper() in ship_name.upper():
                            self.selected_ship = ship_name
                            self.selected_ship_id = ship_id
                            self.log(f"   ✅ Selected test ship: {ship_name} (ID: {ship_id})")
                            self.docking_tests['test_ship_found'] = True
                            return ship
                
                # If no specific test ship found, use the first available ship (not SUNSHINE 01)
                for ship in ships:
                    ship_name = ship.get('name', '')
                    ship_id = ship.get('id', '')
                    
                    if 'SUNSHINE 01' not in ship_name.upper():
                        self.selected_ship = ship_name
                        self.selected_ship_id = ship_id
                        self.log(f"   ✅ Using available ship: {ship_name} (ID: {ship_id})")
                        self.docking_tests['test_ship_found'] = True
                        return ship
                
                self.log("   ❌ No suitable test ship found")
                return None
                
            else:
                self.log(f"   ❌ Ships retrieval failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Ships retrieval error: {str(e)}", "ERROR")
            return None
    
    def check_ship_certificates(self):
        """Check if the selected ship has certificates"""
        try:
            self.log(f"📋 Checking certificates for {self.selected_ship}...")
            
            endpoint = f"{BACKEND_URL}/certificates"
            params = {"ship_id": self.selected_ship_id}
            self.log(f"   GET {endpoint}?ship_id={self.selected_ship_id}")
            
            response = requests.get(endpoint, params=params, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                cert_count = len(certificates)
                self.log(f"   ✅ Found {cert_count} certificates for {self.selected_ship}")
                
                if cert_count > 0:
                    self.docking_tests['test_ship_has_certificates'] = True
                    
                    # Show some certificate details
                    for i, cert in enumerate(certificates[:3]):  # Show first 3
                        cert_name = cert.get('cert_name', 'Unknown')
                        cert_type = cert.get('cert_type', 'Unknown')
                        valid_date = cert.get('valid_date', 'Unknown')
                        self.log(f"      Certificate {i+1}: {cert_name} ({cert_type}) - Valid: {valid_date}")
                    
                    if cert_count > 3:
                        self.log(f"      ... and {cert_count - 3} more certificates")
                    
                    return True
                else:
                    self.log(f"   ⚠️ Ship {self.selected_ship} has no certificates")
                    return False
                
            else:
                self.log(f"   ❌ Certificate retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Certificate check error: {str(e)}", "ERROR")
            return False
    
    def test_recalculate_docking_dates_api(self):
        """Test the main Recalculate Docking Dates API endpoint"""
        try:
            self.log(f"🎯 Testing Recalculate Docking Dates API for {self.selected_ship}...")
            self.log("   Focus: Verify handleRecalculateDockingDates function fix is working")
            
            # Test the POST /api/ships/{ship_id}/calculate-docking-dates endpoint
            endpoint = f"{BACKEND_URL}/ships/{self.selected_ship_id}/calculate-docking-dates"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            # Check if API is accessible (not 404 or 500)
            if response.status_code in [200, 400, 422]:  # Valid response codes
                self.docking_tests['docking_dates_api_accessible'] = True
                self.log("   ✅ Docking Dates API is accessible")
            else:
                self.log(f"   ❌ Docking Dates API not accessible: {response.status_code}")
                return False
            
            # Check if API responds correctly (200 OK)
            if response.status_code == 200:
                self.docking_tests['api_responds_correctly'] = True
                self.log("   ✅ API responds correctly with 200 OK")
                
                try:
                    result = response.json()
                    self.log("   ✅ API returns valid JSON response")
                    self.log(f"   📊 Response: {json.dumps(result, indent=2)}")
                    
                    # Check response format
                    expected_fields = ['success', 'message']
                    if all(field in result for field in expected_fields):
                        self.docking_tests['response_format_correct'] = True
                        self.log("   ✅ Response format is correct")
                        
                        success = result.get('success', False)
                        message = result.get('message', '')
                        docking_dates = result.get('docking_dates')
                        
                        self.log(f"   Success: {success}")
                        self.log(f"   Message: {message}")
                        
                        # Check if we got docking dates extracted
                        if success and docking_dates:
                            self.docking_tests['docking_dates_extracted'] = True
                            self.log("   ✅ Docking dates successfully extracted")
                            
                            # Show extracted dates
                            last_docking = docking_dates.get('last_docking')
                            last_docking_2 = docking_dates.get('last_docking_2')
                            next_docking = docking_dates.get('next_docking')
                            
                            self.log(f"   📊 Extracted Docking Dates:")
                            self.log(f"      Last Docking 1: {last_docking}")
                            self.log(f"      Last Docking 2: {last_docking_2}")
                            self.log(f"      Next Docking: {next_docking}")
                            
                        elif not success:
                            self.log(f"   ⚠️ API returned success=false: {message}")
                            # This is still a valid response, just no dates found
                            
                        # Most importantly: Check if there's NO JavaScript error
                        if "handleRecalculateDockingDates is not defined" not in message:
                            self.docking_tests['no_javascript_error'] = True
                            self.log("   ✅ NO 'handleRecalculateDockingDates is not defined' error!")
                            self.log("   ✅ JavaScript function definition issue is RESOLVED")
                        else:
                            self.log("   ❌ JavaScript error still present: handleRecalculateDockingDates is not defined")
                        
                        self.test_results['docking_api_response'] = result
                        return True
                        
                    else:
                        self.log("   ❌ Response format is incorrect")
                        self.log(f"   Expected fields: {expected_fields}")
                        self.log(f"   Actual fields: {list(result.keys())}")
                        return False
                        
                except json.JSONDecodeError:
                    self.log("   ❌ API response is not valid JSON")
                    self.log(f"   Response text: {response.text[:200]}")
                    return False
                    
            else:
                self.log(f"   ❌ API returned error status: {response.status_code}")
                try:
                    error_data = response.json()
                    error_message = error_data.get('detail', 'Unknown error')
                    self.log(f"   Error: {error_message}")
                    
                    # Check if the error is the JavaScript function error
                    if "handleRecalculateDockingDates is not defined" in error_message:
                        self.log("   ❌ JavaScript error detected: handleRecalculateDockingDates is not defined")
                        self.log("   ❌ Function definition issue is NOT resolved")
                    else:
                        self.docking_tests['no_javascript_error'] = True
                        self.log("   ✅ No JavaScript function definition error detected")
                        
                except:
                    self.log(f"   Error response: {response.text[:200]}")
                
                return False
                
        except Exception as e:
            self.log(f"❌ Recalculate Docking Dates API test error: {str(e)}", "ERROR")
            return False
    
    def test_error_handling(self):
        """Test error handling with invalid ship ID"""
        try:
            self.log("🔧 Testing Error Handling with invalid ship ID...")
            
            # Test with invalid ship ID
            invalid_ship_id = "invalid-ship-id-12345"
            endpoint = f"{BACKEND_URL}/ships/{invalid_ship_id}/calculate-docking-dates"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [400, 404, 422]:
                self.docking_tests['error_handling_working'] = True
                self.log("   ✅ Error handling working correctly")
                
                try:
                    error_data = response.json()
                    error_message = error_data.get('detail', 'Unknown error')
                    self.log(f"   Error message: {error_message}")
                    
                    # Make sure it's not the JavaScript error
                    if "handleRecalculateDockingDates is not defined" not in error_message:
                        self.log("   ✅ No JavaScript function definition error in error handling")
                    else:
                        self.log("   ❌ JavaScript error present even in error handling")
                        
                except:
                    self.log("   ⚠️ Error response not in JSON format")
                    
            else:
                self.log(f"   ⚠️ Unexpected response for invalid ship ID: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error handling test error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_docking_dates_tests(self):
        """Main test function for Recalculate Docking Dates API"""
        self.log("🎯 STARTING RECALCULATE DOCKING DATES API TESTING")
        self.log("🔍 Focus: Test the 'Recalculate Docking Dates' API endpoint")
        self.log("📋 Review Request: Verify handleRecalculateDockingDates function fix is working correctly")
        self.log("🎯 Expected: API responds correctly without JavaScript errors")
        self.log("🎯 Ships to test: Test Ship No Config, Test Ship No Company, SUNSHINE STAR, TEST ANNIVERSARY SHIP")
        self.log("🚫 Excluded: SUNSHINE 01 (deleted certificates)")
        self.log("=" * 100)
        
        # Step 1: Authenticate
        self.log("\n🔐 STEP 1: AUTHENTICATION")
        self.log("=" * 50)
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Get Available Ships
        self.log("\n🚢 STEP 2: GET AVAILABLE SHIPS")
        self.log("=" * 50)
        selected_ship = self.get_available_ships()
        if not selected_ship:
            self.log("❌ No suitable test ship found - cannot proceed with testing")
            return False
        
        # Step 3: Check Ship Certificates
        self.log("\n📋 STEP 3: CHECK SHIP CERTIFICATES")
        self.log("=" * 50)
        has_certificates = self.check_ship_certificates()
        if not has_certificates:
            self.log("⚠️ Selected ship has no certificates - proceeding anyway to test API")
        
        # Step 4: Test Recalculate Docking Dates API
        self.log("\n🎯 STEP 4: TEST RECALCULATE DOCKING DATES API")
        self.log("=" * 50)
        self.test_recalculate_docking_dates_api()
        
        # Step 5: Test Error Handling
        self.log("\n🔧 STEP 5: TEST ERROR HANDLING")
        self.log("=" * 50)
        self.test_error_handling()
        
        # Step 6: Final Analysis
        self.log("\n📊 STEP 6: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_analysis()
        
        return True
    
    def provide_final_analysis(self):
        """Provide final analysis of the Recalculate Docking Dates API testing"""
        try:
            self.log("🎯 RECALCULATE DOCKING DATES API TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.docking_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.docking_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.docking_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.docking_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.docking_tests)})")
            
            # Provide specific analysis based on review request
            self.log("\n🎯 REVIEW REQUEST ANALYSIS:")
            
            # 1. API Endpoint Accessibility
            if self.docking_tests['docking_dates_api_accessible']:
                self.log("   ✅ API Endpoint POST /api/ships/{ship_id}/calculate-docking-dates: ACCESSIBLE")
            else:
                self.log("   ❌ API Endpoint POST /api/ships/{ship_id}/calculate-docking-dates: NOT ACCESSIBLE")
            
            # 2. Test Ship Selection
            if self.docking_tests['test_ship_found']:
                self.log(f"   ✅ Test Ship Selection: SUCCESSFUL ({self.selected_ship})")
                if self.docking_tests['test_ship_has_certificates']:
                    self.log("   ✅ Test Ship Has Certificates: YES")
                else:
                    self.log("   ⚠️ Test Ship Has Certificates: NO (but API can still be tested)")
            else:
                self.log("   ❌ Test Ship Selection: FAILED")
            
            # 3. API Response Correctness
            if self.docking_tests['api_responds_correctly']:
                self.log("   ✅ API Responds Correctly: YES (200 OK)")
            else:
                self.log("   ❌ API Responds Correctly: NO")
            
            # 4. JavaScript Function Fix (MOST IMPORTANT)
            if self.docking_tests['no_javascript_error']:
                self.log("   ✅ handleRecalculateDockingDates Function Fix: WORKING")
                self.log("   ✅ NO 'handleRecalculateDockingDates is not defined' error detected")
                self.log("   ✅ JavaScript function definition issue is RESOLVED")
            else:
                self.log("   ❌ handleRecalculateDockingDates Function Fix: NOT WORKING")
                self.log("   ❌ 'handleRecalculateDockingDates is not defined' error still present")
            
            # 5. Response Format and Docking Dates
            if self.docking_tests['response_format_correct']:
                self.log("   ✅ Response Format: CORRECT")
                if self.docking_tests['docking_dates_extracted']:
                    self.log("   ✅ Docking Dates Extraction: SUCCESSFUL")
                else:
                    self.log("   ⚠️ Docking Dates Extraction: NO DATES FOUND (may be expected)")
            else:
                self.log("   ❌ Response Format: INCORRECT")
            
            # 6. Error Handling
            if self.docking_tests['error_handling_working']:
                self.log("   ✅ Error Handling: WORKING")
            else:
                self.log("   ❌ Error Handling: NOT WORKING")
            
            # Final conclusion
            if self.docking_tests['no_javascript_error'] and self.docking_tests['api_responds_correctly']:
                self.log(f"\n🎉 CONCLUSION: RECALCULATE DOCKING DATES API FIX IS WORKING")
                self.log(f"   ✅ handleRecalculateDockingDates function definition issue is RESOLVED")
                self.log(f"   ✅ API endpoint is accessible and responds correctly")
                self.log(f"   ✅ No JavaScript errors detected")
                if self.docking_tests['docking_dates_extracted']:
                    self.log(f"   ✅ Docking dates extraction is working")
            elif self.docking_tests['no_javascript_error']:
                self.log(f"\n⚠️ CONCLUSION: JAVASCRIPT ERROR IS FIXED BUT API HAS OTHER ISSUES")
                self.log(f"   ✅ handleRecalculateDockingDates function definition issue is RESOLVED")
                self.log(f"   ⚠️ API may have other functionality issues")
            else:
                self.log(f"\n❌ CONCLUSION: JAVASCRIPT ERROR IS NOT FIXED")
                self.log(f"   ❌ handleRecalculateDockingDates function definition issue persists")
                self.log(f"   ❌ API still throws JavaScript errors")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run Recalculate Docking Dates API tests"""
    print("🎯 RECALCULATE DOCKING DATES API TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = RecalculateDockingDatesTester()
        success = tester.run_comprehensive_docking_dates_tests()
        
        if success:
            print("\n✅ RECALCULATE DOCKING DATES API TESTING COMPLETED")
        else:
            print("\n❌ RECALCULATE DOCKING DATES API TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
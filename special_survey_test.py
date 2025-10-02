#!/usr/bin/env python3
"""
Special Survey From Date Calculation Bug Fix Test
FOCUS: Test the special_survey_from_date calculation bug fix for SUNSHINE 01
Review Request: Test if special_survey_from_date is being calculated correctly (5 years prior, same day/month)
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import traceback

# Configuration - Use environment variable for backend URL
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fleet-tracker-104.preview.emergentagent.com') + '/api'

class SpecialSurveyTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.sunshine_01_id = "e21c71a2-9543-4f92-990c-72f54292fde8"
        
        # Test tracking
        self.test_results = {
            'authentication_successful': False,
            'sunshine_01_exists': False,
            'special_survey_endpoint_accessible': False,
            'special_survey_calculation_working': False,
            'from_date_calculation_correct': False,
            'same_day_month_logic_verified': False,
            'expected_dates_match': False
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
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.test_results['authentication_successful'] = True
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
    
    def check_sunshine_01_exists(self):
        """Check if SUNSHINE 01 ship exists with the expected ID"""
        try:
            self.log("🚢 Checking if SUNSHINE 01 ship exists...")
            self.log(f"   Expected ID: {self.sunshine_01_id}")
            
            endpoint = f"{BACKEND_URL}/ships/{self.sunshine_01_id}"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ship_data = response.json()
                ship_name = ship_data.get('name', 'Unknown')
                ship_imo = ship_data.get('imo', 'Unknown')
                
                self.log("✅ SUNSHINE 01 ship found")
                self.log(f"   Ship Name: {ship_name}")
                self.log(f"   Ship IMO: {ship_imo}")
                self.log(f"   Ship ID: {ship_data.get('id')}")
                
                if ship_name == "SUNSHINE 01":
                    self.test_results['sunshine_01_exists'] = True
                    return True
                else:
                    self.log(f"   ⚠️ Ship found but name mismatch: expected 'SUNSHINE 01', got '{ship_name}'")
                    return False
            else:
                self.log(f"   ❌ SUNSHINE 01 ship not found: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ship existence check error: {str(e)}", "ERROR")
            return False
    
    def test_special_survey_calculation(self):
        """Test the special survey cycle calculation endpoint"""
        try:
            self.log("📊 Testing Special Survey Cycle Calculation...")
            self.log("   Focus: special_survey_from_date calculation (5 years prior, same day/month)")
            
            endpoint = f"{BACKEND_URL}/ships/{self.sunshine_01_id}/calculate-special-survey-cycle"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                self.log("✅ Special Survey calculation endpoint accessible")
                self.test_results['special_survey_endpoint_accessible'] = True
                
                # Log the full response
                self.log("   API Response:")
                self.log(f"   {json.dumps(response_data, indent=2)}")
                
                # Check if calculation was successful
                success = response_data.get('success', False)
                message = response_data.get('message', '')
                special_survey_cycle = response_data.get('special_survey_cycle', {})
                
                if success:
                    self.log("✅ Special Survey calculation successful")
                    self.log(f"   Message: {message}")
                    self.test_results['special_survey_calculation_working'] = True
                    
                    # Extract dates for verification
                    from_date = special_survey_cycle.get('from_date')
                    to_date = special_survey_cycle.get('to_date')
                    cycle_type = special_survey_cycle.get('cycle_type')
                    display = special_survey_cycle.get('display')
                    
                    self.log(f"   From Date: {from_date}")
                    self.log(f"   To Date: {to_date}")
                    self.log(f"   Cycle Type: {cycle_type}")
                    self.log(f"   Display: {display}")
                    
                    # Verify the calculation logic
                    return self.verify_date_calculation(from_date, to_date)
                else:
                    self.log(f"   ❌ Special Survey calculation failed: {message}")
                    return False
            else:
                self.log(f"   ❌ Special Survey calculation endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Special Survey calculation test error: {str(e)}", "ERROR")
            return False
    
    def verify_date_calculation(self, from_date, to_date):
        """Verify that the from_date is calculated correctly (5 years prior, same day/month)"""
        try:
            self.log("🔍 Verifying Date Calculation Logic...")
            self.log("   Expected: from_date should be 5 years prior to to_date with same day/month")
            
            if not from_date or not to_date:
                self.log("   ❌ Missing date values for verification")
                return False
            
            # Parse the dates
            from_date_str = str(from_date)
            to_date_str = str(to_date)
            
            self.log(f"   From Date String: {from_date_str}")
            self.log(f"   To Date String: {to_date_str}")
            
            # Expected values based on review request
            expected_to_date = "10/03/2026"
            expected_from_date = "10/03/2021"
            
            self.log(f"   Expected To Date: {expected_to_date}")
            self.log(f"   Expected From Date: {expected_from_date}")
            
            # Check if to_date matches expected
            if expected_to_date in to_date_str:
                self.log("   ✅ To Date matches expected value")
                to_date_correct = True
            else:
                self.log(f"   ⚠️ To Date doesn't match expected: got '{to_date_str}', expected to contain '{expected_to_date}'")
                to_date_correct = False
            
            # Check if from_date matches expected
            if expected_from_date in from_date_str:
                self.log("   ✅ From Date matches expected value")
                self.test_results['from_date_calculation_correct'] = True
                from_date_correct = True
            else:
                self.log(f"   ❌ From Date doesn't match expected: got '{from_date_str}', expected to contain '{expected_from_date}'")
                from_date_correct = False
            
            # Verify same day/month logic
            if self.verify_same_day_month_logic(from_date_str, to_date_str):
                self.log("   ✅ Same day/month logic verified")
                self.test_results['same_day_month_logic_verified'] = True
                same_day_month_correct = True
            else:
                self.log("   ❌ Same day/month logic failed")
                same_day_month_correct = False
            
            # Overall verification
            if from_date_correct and to_date_correct and same_day_month_correct:
                self.log("   ✅ Date calculation verification PASSED")
                self.test_results['expected_dates_match'] = True
                return True
            else:
                self.log("   ❌ Date calculation verification FAILED")
                return False
                
        except Exception as e:
            self.log(f"❌ Date calculation verification error: {str(e)}", "ERROR")
            return False
    
    def verify_same_day_month_logic(self, from_date_str, to_date_str):
        """Verify that from_date and to_date have the same day and month"""
        try:
            # Extract day and month from both dates
            # Look for DD/MM/YYYY pattern
            import re
            
            # Pattern to match DD/MM/YYYY
            date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
            
            from_match = re.search(date_pattern, from_date_str)
            to_match = re.search(date_pattern, to_date_str)
            
            if from_match and to_match:
                from_day, from_month, from_year = from_match.groups()
                to_day, to_month, to_year = to_match.groups()
                
                self.log(f"   From Date: Day={from_day}, Month={from_month}, Year={from_year}")
                self.log(f"   To Date: Day={to_day}, Month={to_month}, Year={to_year}")
                
                # Check if day and month are the same
                if from_day == to_day and from_month == to_month:
                    self.log(f"   ✅ Same day/month confirmed: {from_day}/{from_month}")
                    
                    # Check if year difference is 5
                    year_diff = int(to_year) - int(from_year)
                    if year_diff == 5:
                        self.log(f"   ✅ 5-year difference confirmed: {from_year} to {to_year}")
                        return True
                    else:
                        self.log(f"   ❌ Year difference is {year_diff}, expected 5")
                        return False
                else:
                    self.log(f"   ❌ Day/month mismatch: from={from_day}/{from_month}, to={to_day}/{to_month}")
                    return False
            else:
                self.log("   ⚠️ Could not parse DD/MM/YYYY format from dates")
                # Try alternative parsing if needed
                return False
                
        except Exception as e:
            self.log(f"❌ Same day/month verification error: {str(e)}", "ERROR")
            return False
    
    def test_ai_certificate_analysis(self):
        """Test AI certificate analysis endpoint for special survey date extraction"""
        try:
            self.log("🤖 Testing AI Certificate Analysis for Special Survey Dates...")
            self.log("   This would test the AI extraction of special survey dates from CSSC certificate")
            
            # For now, we'll focus on the calculation endpoint
            # The AI analysis would require the actual certificate file
            self.log("   ⚠️ AI certificate analysis requires actual certificate file - skipping for now")
            self.log("   ✅ Focusing on calculation endpoint which uses existing certificate data")
            
            return True
            
        except Exception as e:
            self.log(f"❌ AI certificate analysis test error: {str(e)}", "ERROR")
            return False
    
    def run_special_survey_tests(self):
        """Main test function for Special Survey From Date calculation"""
        self.log("📊 STARTING SPECIAL SURVEY FROM DATE CALCULATION BUG FIX TEST")
        self.log("🎯 Focus: Test special_survey_from_date calculation for SUNSHINE 01")
        self.log("📋 Expected: if to_date is '10/03/2026', from_date should be '10/03/2021'")
        self.log("🔍 Key Test: 5 years prior, same day/month logic")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Check if SUNSHINE 01 exists
            self.log("\n🚢 STEP 2: SUNSHINE 01 SHIP VERIFICATION")
            self.log("=" * 50)
            if not self.check_sunshine_01_exists():
                self.log("❌ SUNSHINE 01 ship not found - cannot proceed with testing")
                return False
            
            # Step 3: Test Special Survey Calculation
            self.log("\n📊 STEP 3: SPECIAL SURVEY CYCLE CALCULATION TEST")
            self.log("=" * 50)
            if not self.test_special_survey_calculation():
                self.log("❌ Special Survey calculation test failed")
                return False
            
            # Step 4: Test AI Certificate Analysis (optional)
            self.log("\n🤖 STEP 4: AI CERTIFICATE ANALYSIS TEST")
            self.log("=" * 50)
            self.test_ai_certificate_analysis()
            
            # Step 5: Final Analysis
            self.log("\n📊 STEP 5: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Test execution error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of the Special Survey testing"""
        try:
            self.log("📊 SPECIAL SURVEY FROM DATE CALCULATION BUG FIX TEST - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.test_results.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.test_results)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.test_results)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.test_results)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.test_results)})")
            
            # Provide specific analysis based on review request
            self.log("\n🎯 REVIEW REQUEST ANALYSIS:")
            
            # 1. Ship Existence
            if self.test_results['sunshine_01_exists']:
                self.log("   ✅ SUNSHINE 01 ship exists with correct ID")
            else:
                self.log("   ❌ SUNSHINE 01 ship not found or ID mismatch")
            
            # 2. Special Survey Calculation
            if self.test_results['special_survey_calculation_working']:
                self.log("   ✅ Special Survey calculation endpoint working")
            else:
                self.log("   ❌ Special Survey calculation endpoint failed")
            
            # 3. From Date Calculation
            if self.test_results['from_date_calculation_correct']:
                self.log("   ✅ From Date calculation correct (10/03/2021)")
            else:
                self.log("   ❌ From Date calculation incorrect")
            
            # 4. Same Day/Month Logic
            if self.test_results['same_day_month_logic_verified']:
                self.log("   ✅ Same day/month logic verified (5 years prior)")
            else:
                self.log("   ❌ Same day/month logic failed")
            
            # 5. Expected Dates Match
            if self.test_results['expected_dates_match']:
                self.log("   ✅ Expected dates match (to_date: 10/03/2026, from_date: 10/03/2021)")
            else:
                self.log("   ❌ Expected dates don't match")
            
            # Final conclusion
            bug_fix_working = (
                self.test_results['from_date_calculation_correct'] and
                self.test_results['same_day_month_logic_verified'] and
                self.test_results['expected_dates_match']
            )
            
            if bug_fix_working:
                self.log(f"\n🎉 CONCLUSION: SPECIAL SURVEY FROM DATE CALCULATION BUG FIX IS WORKING")
                self.log(f"   ✅ Bug fix successfully implemented and verified")
                self.log(f"   ✅ special_survey_from_date correctly calculated as 5 years prior")
                self.log(f"   ✅ Same day/month logic working (10/03/2021 from 10/03/2026)")
                self.log(f"   ✅ Expected behavior confirmed: to_date '10/03/2026' → from_date '10/03/2021'")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: SPECIAL SURVEY CALCULATION PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Some functionality working, bug may still exist")
            else:
                self.log(f"\n❌ CONCLUSION: SPECIAL SURVEY FROM DATE CALCULATION BUG STILL PRESENT")
                self.log(f"   Success rate: {success_rate:.1f}% - Bug fix not working correctly")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run Special Survey From Date calculation tests"""
    print("📊 SPECIAL SURVEY FROM DATE CALCULATION BUG FIX TEST STARTED")
    print("=" * 80)
    
    try:
        tester = SpecialSurveyTester()
        success = tester.run_special_survey_tests()
        
        if success:
            print("\n✅ SPECIAL SURVEY FROM DATE CALCULATION TEST COMPLETED")
        else:
            print("\n❌ SPECIAL SURVEY FROM DATE CALCULATION TEST FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
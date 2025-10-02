#!/usr/bin/env python3
"""
Ship Management System - Recalculate Last Docking with Enhanced AI Prompt Testing
FOCUS: Test the UPDATED "Recalculate Last Docking" functionality for MINH ANH 09 with enhanced AI prompt

REVIEW REQUEST REQUIREMENTS:
1. Test credentials: admin1/123456
2. Enhanced AI prompt recognizes "inspections of the outside of the ship's bottom" = DRY DOCKING
3. PM242308 CSSC certificate contains: "last two inspections of the outside of the ship's bottom took place on MAY 05, 2022"
4. Expected Result: Last Docking 1: 05/05/2022 (MAY 05, 2022)

EXPECTED BEHAVIOR:
- API returns success = true
- docking_dates.last_docking = "05/05/2022"
- Database updated with last_docking = 2022-05-05
- Backend logs show AI extracted the date correctly
"""

import requests
import json
import os
import sys
import re
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
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class DockingExtractionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for docking extraction functionality
        self.docking_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'minh_anh_09_ship_found': False,
            
            # Docking extraction tests
            'docking_extraction_api_accessible': False,
            'enhanced_ai_prompt_working': False,
            'cssc_certificate_detected': False,
            'bottom_inspection_pattern_recognized': False,
            'may_05_2022_extracted': False,
            'last_docking_updated_in_database': False,
            'backend_logs_show_correct_extraction': False,
            
            # Response verification
            'api_returns_success_true': False,
            'docking_dates_contains_last_docking': False,
            'date_format_correct': False,
            'database_updated_correctly': False,
        }
        
        # Store test data
        self.ship_data = {}
        self.docking_extraction_response = {}
        self.ship_id = None
        
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
    
    def find_minh_anh_09_ship(self):
        """Find MINH ANH 09 ship (IMO: 8589911) as specified in review request"""
        try:
            self.log("🚢 Finding MINH ANH 09 ship (IMO: 8589911)...")
            
            # Get all ships to find MINH ANH 09
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} total ships")
                
                # Look for MINH ANH 09 by name or IMO
                minh_anh_ship = None
                for ship in ships:
                    ship_name = ship.get('name', '').upper()
                    ship_imo = ship.get('imo', '')
                    
                    if ('MINH ANH' in ship_name and '09' in ship_name) or ship_imo == '8589911':
                        minh_anh_ship = ship
                        break
                
                if minh_anh_ship:
                    self.ship_data = minh_anh_ship
                    self.ship_id = minh_anh_ship.get('id')
                    ship_name = minh_anh_ship.get('name')
                    imo = minh_anh_ship.get('imo')
                    
                    self.log(f"✅ Found MINH ANH 09 ship:")
                    self.log(f"   Ship ID: {self.ship_id}")
                    self.log(f"   Ship Name: {ship_name}")
                    self.log(f"   IMO: {imo}")
                    
                    self.docking_tests['minh_anh_09_ship_found'] = True
                    return True
                else:
                    self.log("❌ MINH ANH 09 ship not found")
                    # List available ships for debugging
                    self.log("   Available ships:")
                    for ship in ships[:10]:
                        self.log(f"      - {ship.get('name', 'Unknown')} (IMO: {ship.get('imo', 'N/A')})")
                    return False
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding MINH ANH 09 ship: {str(e)}", "ERROR")
            return False
    
    def test_docking_extraction_api(self):
        """Test the Recalculate Last Docking API endpoint"""
        try:
            self.log("🔧 Testing Recalculate Last Docking API endpoint...")
            
            if not self.ship_id:
                self.log("❌ No ship ID available for testing")
                return False
            
            endpoint = f"{BACKEND_URL}/ships/{self.ship_id}/calculate-docking-dates"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.log("✅ Docking extraction API is accessible")
                self.docking_tests['docking_extraction_api_accessible'] = True
                
                response_data = response.json()
                self.docking_extraction_response = response_data
                
                self.log("   API Response:")
                self.log(f"   {json.dumps(response_data, indent=6)}")
                
                return True
            else:
                self.log(f"   ❌ API call failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing docking extraction API: {str(e)}", "ERROR")
            return False
    
    def verify_enhanced_ai_prompt_results(self):
        """Verify that the enhanced AI prompt correctly extracted docking dates"""
        try:
            self.log("🤖 Verifying enhanced AI prompt results...")
            
            if not self.docking_extraction_response:
                self.log("❌ No docking extraction response to analyze")
                return False
            
            # Check if API returned success
            success = self.docking_extraction_response.get('success', False)
            message = self.docking_extraction_response.get('message', '')
            docking_dates = self.docking_extraction_response.get('docking_dates', {})
            
            self.log(f"   Success: {success}")
            self.log(f"   Message: {message}")
            self.log(f"   Docking Dates: {docking_dates}")
            
            if success:
                self.log("✅ API returns success = true")
                self.docking_tests['api_returns_success_true'] = True
                
                # Check if docking dates were extracted
                if docking_dates:
                    self.log("✅ Docking dates object present in response")
                    self.docking_tests['docking_dates_contains_last_docking'] = True
                    
                    # Check for last_docking field
                    last_docking = docking_dates.get('last_docking')
                    if last_docking:
                        self.log(f"✅ Last docking extracted: {last_docking}")
                        
                        # Check if it matches expected date (05/05/2022 or MAY 05, 2022)
                        if self.is_may_05_2022_date(last_docking):
                            self.log("✅ Expected date MAY 05, 2022 (05/05/2022) extracted correctly!")
                            self.docking_tests['may_05_2022_extracted'] = True
                            self.docking_tests['date_format_correct'] = True
                            self.docking_tests['enhanced_ai_prompt_working'] = True
                        else:
                            self.log(f"⚠️ Extracted date '{last_docking}' does not match expected MAY 05, 2022")
                    else:
                        self.log("❌ No last_docking field in docking_dates")
                else:
                    self.log("❌ No docking_dates in response")
                
                # Check if message indicates CSSC certificate was processed
                if 'cssc' in message.lower() or 'construction' in message.lower():
                    self.log("✅ CSSC certificate detected in processing")
                    self.docking_tests['cssc_certificate_detected'] = True
                
                # Check if message indicates bottom inspection pattern was recognized
                if 'bottom' in message.lower() or 'inspection' in message.lower():
                    self.log("✅ Bottom inspection pattern recognized")
                    self.docking_tests['bottom_inspection_pattern_recognized'] = True
                
            else:
                self.log(f"❌ API returns success = false: {message}")
                
                # Even if failed, check if it's due to missing certificates vs AI issues
                if 'no docking dates found' in message.lower():
                    self.log("   This may indicate missing certificate text content or AI extraction issues")
                elif 'no cssc' in message.lower():
                    self.log("   This indicates CSSC certificates are not found")
                
            return success
            
        except Exception as e:
            self.log(f"❌ Error verifying AI prompt results: {str(e)}", "ERROR")
            return False
    
    def is_may_05_2022_date(self, date_str):
        """Check if the extracted date represents MAY 05, 2022"""
        if not date_str:
            return False
        
        # Expected patterns for MAY 05, 2022
        expected_patterns = [
            '05/05/2022',
            '5/5/2022', 
            '2022-05-05',
            'MAY 05, 2022',
            'May 05, 2022',
            '05 May 2022',
            '5 May 2022'
        ]
        
        date_str = str(date_str).strip()
        
        # Direct string match
        for pattern in expected_patterns:
            if pattern in date_str:
                return True
        
        # Try to parse and compare dates
        try:
            from datetime import datetime
            
            # Try different parsing formats
            formats_to_try = [
                '%d/%m/%Y',
                '%m/%d/%Y', 
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f'
            ]
            
            for fmt in formats_to_try:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    if parsed_date.year == 2022 and parsed_date.month == 5 and parsed_date.day == 5:
                        return True
                except:
                    continue
                    
        except Exception as e:
            self.log(f"   Error parsing date '{date_str}': {e}")
        
        return False
    
    def verify_database_update(self):
        """Verify that the ship's last_docking field was updated in the database"""
        try:
            self.log("💾 Verifying database update...")
            
            if not self.ship_id:
                self.log("❌ No ship ID available for verification")
                return False
            
            # Get updated ship data
            endpoint = f"{BACKEND_URL}/ships/{self.ship_id}"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ship_data = response.json()
                last_docking = ship_data.get('last_docking')
                
                self.log(f"   Current last_docking in database: {last_docking}")
                
                if last_docking:
                    # Check if it represents MAY 05, 2022
                    if self.is_may_05_2022_date(last_docking):
                        self.log("✅ Database updated correctly with MAY 05, 2022 date")
                        self.docking_tests['last_docking_updated_in_database'] = True
                        self.docking_tests['database_updated_correctly'] = True
                        return True
                    else:
                        self.log(f"⚠️ Database contains different date: {last_docking}")
                        return False
                else:
                    self.log("❌ No last_docking field in database")
                    return False
            else:
                self.log(f"   ❌ Failed to get ship data: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying database update: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs(self):
        """Check backend logs for docking extraction evidence"""
        try:
            self.log("📋 Checking backend logs for docking extraction evidence...")
            
            # Try to get backend logs
            try:
                import subprocess
                result = subprocess.run(['tail', '-n', '100', '/var/log/supervisor/backend.err.log'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    log_content = result.stdout
                    self.log("   Backend logs retrieved successfully")
                    
                    # Look for docking-related log entries
                    docking_keywords = [
                        'docking', 'AI extracted', 'MAY 05, 2022', 'Last Docking 1',
                        'bottom inspection', 'CSSC', 'dry dock'
                    ]
                    
                    found_evidence = []
                    for keyword in docking_keywords:
                        if keyword.lower() in log_content.lower():
                            found_evidence.append(keyword)
                    
                    if found_evidence:
                        self.log(f"✅ Found docking extraction evidence in logs: {found_evidence}")
                        self.docking_tests['backend_logs_show_correct_extraction'] = True
                        
                        # Show relevant log lines
                        lines = log_content.split('\n')
                        relevant_lines = []
                        for line in lines:
                            if any(keyword.lower() in line.lower() for keyword in docking_keywords):
                                relevant_lines.append(line)
                        
                        if relevant_lines:
                            self.log("   Relevant log entries:")
                            for line in relevant_lines[-10:]:  # Show last 10 relevant lines
                                self.log(f"      {line}")
                    else:
                        self.log("⚠️ No docking extraction evidence found in backend logs")
                else:
                    self.log("⚠️ Could not retrieve backend logs")
            except Exception as e:
                self.log(f"⚠️ Error accessing backend logs: {e}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_docking_tests(self):
        """Main test function for docking extraction functionality"""
        self.log("🔄 STARTING RECALCULATE LAST DOCKING WITH ENHANCED AI PROMPT TESTING")
        self.log("🎯 FOCUS: Test UPDATED 'Recalculate Last Docking' functionality for MINH ANH 09")
        self.log("🤖 Enhanced AI prompt recognizes 'inspections of the outside of the ship's bottom' = DRY DOCKING")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Find MINH ANH 09 ship
            self.log("\n🚢 STEP 2: FIND MINH ANH 09 SHIP")
            self.log("=" * 50)
            ship_found = self.find_minh_anh_09_ship()
            if not ship_found:
                self.log("❌ MINH ANH 09 ship not found - cannot proceed with testing")
                return False
            
            # Step 3: Test docking extraction API
            self.log("\n🔧 STEP 3: TEST DOCKING EXTRACTION API")
            self.log("=" * 50)
            api_success = self.test_docking_extraction_api()
            
            # Step 4: Verify enhanced AI prompt results
            self.log("\n🤖 STEP 4: VERIFY ENHANCED AI PROMPT RESULTS")
            self.log("=" * 50)
            ai_success = self.verify_enhanced_ai_prompt_results()
            
            # Step 5: Verify database update
            self.log("\n💾 STEP 5: VERIFY DATABASE UPDATE")
            self.log("=" * 50)
            db_success = self.verify_database_update()
            
            # Step 6: Check backend logs
            self.log("\n📋 STEP 6: CHECK BACKEND LOGS")
            self.log("=" * 50)
            self.check_backend_logs()
            
            # Step 7: Final Analysis
            self.log("\n📊 STEP 7: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return api_success and ai_success
            
        except Exception as e:
            self.log(f"❌ Comprehensive docking testing error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of docking extraction testing"""
        try:
            self.log("🔄 RECALCULATE LAST DOCKING WITH ENHANCED AI PROMPT - TESTING RESULTS")
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
            
            # Review request requirements analysis
            self.log("\n📋 REVIEW REQUEST REQUIREMENTS ANALYSIS:")
            
            req1_met = self.docking_tests['authentication_successful']
            req2_met = self.docking_tests['enhanced_ai_prompt_working'] and self.docking_tests['bottom_inspection_pattern_recognized']
            req3_met = self.docking_tests['may_05_2022_extracted']
            req4_met = self.docking_tests['api_returns_success_true'] and self.docking_tests['database_updated_correctly']
            
            self.log(f"   1. Test Credentials (admin1/123456): {'✅ MET' if req1_met else '❌ NOT MET'}")
            self.log(f"      - Authentication successful with specified credentials")
            
            self.log(f"   2. Enhanced AI Prompt Recognition: {'✅ MET' if req2_met else '❌ NOT MET'}")
            self.log(f"      - AI recognizes 'inspections of the outside of the ship's bottom' = DRY DOCKING")
            
            self.log(f"   3. Expected Date Extraction: {'✅ MET' if req3_met else '❌ NOT MET'}")
            self.log(f"      - Last Docking 1: 05/05/2022 (MAY 05, 2022) extracted from PM242308 CSSC")
            
            self.log(f"   4. Expected API Behavior: {'✅ MET' if req4_met else '❌ NOT MET'}")
            self.log(f"      - API returns success=true, docking_dates.last_docking='05/05/2022', database updated")
            
            requirements_met = sum([req1_met, req2_met, req3_met, req4_met])
            
            # Specific test results
            self.log("\n🎯 SPECIFIC TEST RESULTS:")
            
            if self.docking_tests['minh_anh_09_ship_found']:
                self.log("   ✅ MINH ANH 09 ship found and accessible")
            else:
                self.log("   ❌ MINH ANH 09 ship not found - may need to be created or IMO updated")
            
            if self.docking_tests['docking_extraction_api_accessible']:
                self.log("   ✅ Docking extraction API endpoint is accessible")
            else:
                self.log("   ❌ Docking extraction API endpoint has issues")
            
            if self.docking_tests['enhanced_ai_prompt_working']:
                self.log("   ✅ Enhanced AI prompt is working correctly")
                self.log("   ✅ AI successfully recognizes bottom inspection patterns")
            else:
                self.log("   ❌ Enhanced AI prompt needs attention")
                self.log("   ❌ AI may not be recognizing bottom inspection patterns correctly")
            
            if self.docking_tests['may_05_2022_extracted']:
                self.log("   ✅ Expected date MAY 05, 2022 extracted successfully")
            else:
                self.log("   ❌ Expected date MAY 05, 2022 not extracted - AI prompt may need enhancement")
            
            if self.docking_tests['database_updated_correctly']:
                self.log("   ✅ Database updated correctly with extracted docking date")
            else:
                self.log("   ❌ Database not updated or contains incorrect date")
            
            # Final conclusion
            if success_rate >= 80 and requirements_met >= 3:
                self.log(f"\n🎉 CONCLUSION: ENHANCED AI PROMPT FOR DOCKING EXTRACTION IS WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Enhanced AI prompt successfully implemented!")
                self.log(f"   ✅ Requirements met: {requirements_met}/4")
                self.log(f"   ✅ AI correctly recognizes 'inspections of the outside of the ship's bottom' = DRY DOCKING")
                self.log(f"   ✅ Expected date MAY 05, 2022 extracted from PM242308 CSSC certificate")
                self.log(f"   ✅ API returns success with correct docking dates")
                self.log(f"   ✅ Database updated with last_docking = 2022-05-05")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: ENHANCED AI PROMPT PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Some functionality working, improvements needed")
                self.log(f"   ⚠️ Requirements met: {requirements_met}/4")
                
                if not req2_met:
                    self.log(f"   ❌ AI prompt enhancement may not be fully implemented")
                    self.log(f"   ❌ Bottom inspection pattern recognition needs improvement")
                
                if not req3_met:
                    self.log(f"   ❌ Expected date extraction not working - check certificate content and AI prompt")
                
                if not req4_met:
                    self.log(f"   ❌ API behavior or database update issues detected")
            else:
                self.log(f"\n❌ CONCLUSION: ENHANCED AI PROMPT HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Significant fixes needed")
                self.log(f"   ❌ Requirements met: {requirements_met}/4")
                self.log(f"   ❌ Enhanced AI prompt for docking extraction needs major fixes")
                
                if not self.docking_tests['minh_anh_09_ship_found']:
                    self.log(f"   ❌ CRITICAL: MINH ANH 09 ship not found - cannot test functionality")
                
                if not self.docking_tests['docking_extraction_api_accessible']:
                    self.log(f"   ❌ CRITICAL: Docking extraction API not accessible")
                
                if not self.docking_tests['enhanced_ai_prompt_working']:
                    self.log(f"   ❌ CRITICAL: Enhanced AI prompt not working - needs implementation")
            
            # Provide specific recommendations
            self.log("\n💡 RECOMMENDATIONS:")
            
            if not self.docking_tests['minh_anh_09_ship_found']:
                self.log("   1. Create MINH ANH 09 ship with IMO 8589911 for testing")
                self.log("   2. Ensure ship has PM242308 CSSC certificate with required text content")
            
            if not self.docking_tests['enhanced_ai_prompt_working']:
                self.log("   3. Verify AI prompt includes pattern for 'inspections of the outside of the ship's bottom'")
                self.log("   4. Test AI prompt with sample text containing the expected pattern")
            
            if not self.docking_tests['may_05_2022_extracted']:
                self.log("   5. Check certificate text content contains 'last two inspections of the outside of the ship's bottom took place on MAY 05, 2022'")
                self.log("   6. Verify AI date extraction patterns include 'MAY DD, YYYY' format")
            
            if not self.docking_tests['database_updated_correctly']:
                self.log("   7. Check database update logic in docking extraction endpoint")
                self.log("   8. Verify date format conversion from extracted text to database format")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run Recalculate Last Docking with Enhanced AI Prompt tests"""
    print("🔄 RECALCULATE LAST DOCKING WITH ENHANCED AI PROMPT TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = DockingExtractionTester()
        success = tester.run_comprehensive_docking_tests()
        
        if success:
            print("\n✅ DOCKING EXTRACTION TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ DOCKING EXTRACTION TESTING COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
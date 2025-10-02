#!/usr/bin/env python3
"""
MINH ANH 09 - Recalculate Last Docking Debug Test
FOCUS: Debug why MINH ANH 09 ship cannot extract last docking date from CSSC certificate

REVIEW REQUEST REQUIREMENTS:
1. Login with admin1/123456
2. Find MINH ANH 09 ship
3. Check CSSC certificate PM242308 has text_content
4. Trigger Recalculate Last Docking
5. Analyze response and backend logs
6. Identify root cause of extraction failure

EXPECTED ISSUES TO INVESTIGATE:
- Issue 1: No text_content in CSSC certificate
- Issue 2: AI cannot parse certificate format
- Issue 3: Wrong date format parsing
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

class MinhAnh09DockingDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.minh_anh_ship = None
        self.cssc_certificates = []
        self.debug_results = {}
        
        # Test tracking
        self.debug_tests = {
            'authentication_successful': False,
            'minh_anh_09_ship_found': False,
            'cssc_certificates_found': False,
            'pm242308_certificate_found': False,
            'text_content_available': False,
            'recalculate_docking_triggered': False,
            'backend_logs_analyzed': False,
            'root_cause_identified': False
        }
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
    def authenticate(self):
        """Step 1: Login and Get Token"""
        try:
            self.log("🔐 STEP 1: LOGIN AND GET TOKEN")
            self.log("=" * 50)
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            self.log(f"POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=60)
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                self.log(f"   Token: {self.auth_token[:20]}...")
                
                self.debug_tests['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed - Status: {response.status_code}")
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
        """Step 2: Get MINH ANH 09 Ship ID"""
        try:
            self.log("\n🚢 STEP 2: GET MINH ANH 09 SHIP ID")
            self.log("=" * 50)
            
            # Get all ships to find MINH ANH 09
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"Found {len(ships)} total ships")
                
                # Look for MINH ANH 09
                minh_anh_ship = None
                for ship in ships:
                    ship_name = ship.get('name', '').upper()
                    if 'MINH ANH' in ship_name and '09' in ship_name:
                        minh_anh_ship = ship
                        break
                
                if minh_anh_ship:
                    self.minh_anh_ship = minh_anh_ship
                    ship_id = minh_anh_ship.get('id')
                    ship_name = minh_anh_ship.get('name')
                    imo = minh_anh_ship.get('imo')
                    flag = minh_anh_ship.get('flag')
                    ship_type = minh_anh_ship.get('ship_type')
                    
                    self.log(f"✅ Found MINH ANH 09 ship:")
                    self.log(f"   Ship ID: {ship_id}")
                    self.log(f"   Ship Name: {ship_name}")
                    self.log(f"   IMO: {imo}")
                    self.log(f"   Flag: {flag}")
                    self.log(f"   Class Society: {ship_type}")
                    
                    self.debug_tests['minh_anh_09_ship_found'] = True
                    return True
                else:
                    self.log("❌ MINH ANH 09 ship not found")
                    # List available ships for debugging
                    self.log("   Available ships:")
                    for ship in ships[:10]:
                        self.log(f"      - {ship.get('name', 'Unknown')}")
                    return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding MINH ANH 09 ship: {str(e)}", "ERROR")
            return False
    
    def check_cssc_certificate_text_content(self):
        """Step 3: Check CSSC Certificate has text_content"""
        try:
            self.log("\n📋 STEP 3: CHECK CSSC CERTIFICATE HAS TEXT_CONTENT")
            self.log("=" * 50)
            
            if not self.minh_anh_ship:
                self.log("❌ No MINH ANH 09 ship data available")
                return False
            
            ship_id = self.minh_anh_ship.get('id')
            
            # Get certificates for MINH ANH 09
            endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
            self.log(f"GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"Found {len(certificates)} total certificates for MINH ANH 09")
                
                # Look for CSSC certificates
                cssc_certs = []
                pm242308_cert = None
                
                for cert in certificates:
                    cert_name = cert.get('cert_name', '').upper()
                    cert_no = cert.get('cert_no', '').upper()
                    
                    # Check if it's a CSSC certificate
                    if any(keyword in cert_name for keyword in ['CARGO SHIP SAFETY CONSTRUCTION', 'CSSC', 'SAFETY CONSTRUCTION']):
                        cssc_certs.append(cert)
                        self.log(f"   Found CSSC certificate:")
                        self.log(f"      Name: {cert.get('cert_name')}")
                        self.log(f"      Number: {cert.get('cert_no')}")
                        self.log(f"      ID: {cert.get('id')}")
                        
                        # Check if this is PM242308
                        if cert_no == 'PM242308':
                            pm242308_cert = cert
                            self.log(f"      ⭐ This is PM242308 certificate!")
                
                self.cssc_certificates = cssc_certs
                
                if cssc_certs:
                    self.debug_tests['cssc_certificates_found'] = True
                    self.log(f"✅ Found {len(cssc_certs)} CSSC certificate(s)")
                    
                    if pm242308_cert:
                        self.debug_tests['pm242308_certificate_found'] = True
                        self.log("✅ PM242308 certificate found!")
                        
                        # Check text_content field
                        text_content = pm242308_cert.get('text_content')
                        has_text_content = bool(text_content and len(str(text_content).strip()) > 0)
                        
                        self.log(f"   text_content field analysis:")
                        self.log(f"      Has text_content: {has_text_content}")
                        
                        if has_text_content:
                            self.debug_tests['text_content_available'] = True
                            text_length = len(str(text_content))
                            self.log(f"      Text length: {text_length} characters")
                            self.log(f"      First 500 characters:")
                            self.log(f"      '{str(text_content)[:500]}...'")
                            
                            # Look for docking-related keywords in text
                            text_lower = str(text_content).lower()
                            docking_keywords = ['dry dock', 'docking', 'bottom inspection', 'hull inspection', 'construction survey']
                            found_keywords = [kw for kw in docking_keywords if kw in text_lower]
                            
                            if found_keywords:
                                self.log(f"      ✅ Found docking-related keywords: {found_keywords}")
                            else:
                                self.log(f"      ⚠️ No obvious docking-related keywords found")
                        else:
                            self.log(f"      ❌ ISSUE IDENTIFIED: PM242308 certificate has NO text_content!")
                            self.log(f"      ❌ This is likely the root cause - AI cannot analyze empty text")
                            self.debug_results['root_cause'] = "PM242308 certificate missing text_content field"
                    else:
                        self.log("⚠️ PM242308 certificate not found, checking other CSSC certificates")
                        
                        # Check text_content for other CSSC certificates
                        for cert in cssc_certs:
                            cert_no = cert.get('cert_no', 'Unknown')
                            text_content = cert.get('text_content')
                            has_text_content = bool(text_content and len(str(text_content).strip()) > 0)
                            
                            self.log(f"   Certificate {cert_no}:")
                            self.log(f"      Has text_content: {has_text_content}")
                            
                            if has_text_content:
                                self.debug_tests['text_content_available'] = True
                                text_length = len(str(text_content))
                                self.log(f"      Text length: {text_length} characters")
                else:
                    self.log("❌ No CSSC certificates found for MINH ANH 09")
                    self.log("   Available certificate types:")
                    cert_types = set()
                    for cert in certificates:
                        cert_name = cert.get('cert_name', 'Unknown')
                        cert_types.add(cert_name)
                    
                    for cert_type in sorted(cert_types):
                        self.log(f"      - {cert_type}")
                
                return len(cssc_certs) > 0
            else:
                self.log(f"❌ Failed to get certificates: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking CSSC certificate: {str(e)}", "ERROR")
            return False
    
    def trigger_recalculate_last_docking(self):
        """Step 4: Trigger Recalculate Last Docking"""
        try:
            self.log("\n🔄 STEP 4: TRIGGER RECALCULATE LAST DOCKING")
            self.log("=" * 50)
            
            if not self.minh_anh_ship:
                self.log("❌ No MINH ANH 09 ship data available")
                return False
            
            ship_id = self.minh_anh_ship.get('id')
            
            endpoint = f"{BACKEND_URL}/ships/{ship_id}/calculate-docking-dates"
            self.log(f"POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=60)
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                self.debug_tests['recalculate_docking_triggered'] = True
                
                self.log("✅ Recalculate Last Docking API call successful")
                self.log("📊 API Response Analysis:")
                self.log(f"   Full response: {json.dumps(response_data, indent=4)}")
                
                # Analyze response fields
                success = response_data.get('success', False)
                message = response_data.get('message', '')
                docking_dates = response_data.get('docking_dates')
                
                self.log(f"   success: {success}")
                self.log(f"   message: '{message}'")
                self.log(f"   docking_dates: {docking_dates}")
                
                # Store results for analysis
                self.debug_results['api_response'] = response_data
                
                if success:
                    self.log("✅ SUCCESS: Docking dates were calculated successfully")
                    if docking_dates:
                        last_docking_1 = docking_dates.get('last_docking_1')
                        last_docking_2 = docking_dates.get('last_docking_2')
                        self.log(f"   Last Docking 1: {last_docking_1}")
                        self.log(f"   Last Docking 2: {last_docking_2}")
                else:
                    self.log("❌ FAILURE: Docking dates calculation failed")
                    self.log(f"   Failure message: '{message}'")
                    
                    # Common failure messages to analyze
                    if "no docking dates found" in message.lower():
                        self.log("   🔍 ANALYSIS: No docking dates found in certificates")
                        if not self.debug_tests['text_content_available']:
                            self.log("   🎯 ROOT CAUSE: Missing text_content in CSSC certificates")
                            self.debug_results['root_cause'] = "Missing text_content prevents AI analysis"
                        else:
                            self.log("   🎯 POSSIBLE CAUSE: AI cannot parse certificate format or date patterns")
                            self.debug_results['root_cause'] = "AI parsing issue - certificate format not recognized"
                    elif "no cssc" in message.lower():
                        self.log("   🔍 ANALYSIS: No CSSC certificates found")
                        self.debug_results['root_cause'] = "CSSC certificates not detected by system"
                
                return True
            else:
                self.log(f"❌ Recalculate Last Docking API call failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error triggering recalculate last docking: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs(self):
        """Step 5: Check Backend Logs"""
        try:
            self.log("\n📋 STEP 5: CHECK BACKEND LOGS")
            self.log("=" * 50)
            
            # Check supervisor backend logs
            log_commands = [
                "tail -n 100 /var/log/supervisor/backend.*.log | grep -A5 -B5 'docking'",
                "tail -n 100 /var/log/supervisor/backend.*.log | grep -A5 -B5 'CSSC'",
                "tail -n 100 /var/log/supervisor/backend.*.log | grep -A5 -B5 'AI extracted'",
                "tail -n 100 /var/log/supervisor/backend.*.log | grep -A5 -B5 'No docking dates found'"
            ]
            
            import subprocess
            
            for cmd in log_commands:
                try:
                    self.log(f"Running: {cmd}")
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    
                    if result.stdout:
                        self.log("   Log output:")
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                self.log(f"      {line}")
                    else:
                        self.log("   No matching log entries found")
                        
                except subprocess.TimeoutExpired:
                    self.log("   Log command timed out")
                except Exception as e:
                    self.log(f"   Log command error: {str(e)}")
            
            self.debug_tests['backend_logs_analyzed'] = True
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Step 6: Analyze Response and Provide Final Analysis"""
        try:
            self.log("\n📊 STEP 6: FINAL ANALYSIS AND ROOT CAUSE IDENTIFICATION")
            self.log("=" * 50)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.debug_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ DEBUG TESTS PASSED ({len(passed_tests)}/{len(self.debug_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ DEBUG TESTS FAILED ({len(failed_tests)}/{len(self.debug_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Root cause analysis
            self.log("\n🔍 ROOT CAUSE ANALYSIS:")
            
            if not self.debug_tests['minh_anh_09_ship_found']:
                self.log("❌ CRITICAL ISSUE: MINH ANH 09 ship not found in database")
                self.log("   RECOMMENDATION: Verify ship name spelling or create ship record")
                self.debug_results['root_cause'] = "MINH ANH 09 ship not found in database"
                
            elif not self.debug_tests['cssc_certificates_found']:
                self.log("❌ CRITICAL ISSUE: No CSSC certificates found for MINH ANH 09")
                self.log("   RECOMMENDATION: Upload CSSC certificates for this ship")
                self.debug_results['root_cause'] = "No CSSC certificates available for analysis"
                
            elif not self.debug_tests['text_content_available']:
                self.log("❌ ROOT CAUSE IDENTIFIED: CSSC certificates have no text_content")
                self.log("   ISSUE: AI cannot analyze certificates without extracted text")
                self.log("   SOLUTION: Ensure PDF text is extracted during certificate upload")
                self.log("   TECHNICAL FIX: Check OCR processor and text extraction pipeline")
                self.debug_results['root_cause'] = "Missing text_content in CSSC certificates"
                
            elif self.debug_tests['recalculate_docking_triggered']:
                api_response = self.debug_results.get('api_response', {})
                if not api_response.get('success', False):
                    message = api_response.get('message', '')
                    self.log("❌ ROOT CAUSE: AI cannot parse certificate format")
                    self.log(f"   API MESSAGE: '{message}'")
                    self.log("   ISSUE: Certificate text exists but AI cannot find docking dates")
                    self.log("   SOLUTION: Improve AI prompt or date extraction patterns")
                    self.debug_results['root_cause'] = "AI parsing failure - cannot extract docking dates from text"
                else:
                    self.log("✅ SUCCESS: Docking dates extracted successfully")
                    self.debug_results['root_cause'] = "No issue - system working correctly"
            
            # Expected issues analysis
            self.log("\n📋 EXPECTED ISSUES ANALYSIS:")
            
            # Issue 1: No text_content in CSSC
            if not self.debug_tests['text_content_available']:
                self.log("✅ ISSUE 1 CONFIRMED: No text_content in CSSC certificate")
                self.log("   → Need to ensure PDF text is extracted during upload")
            else:
                self.log("❌ ISSUE 1 NOT CONFIRMED: CSSC certificate has text_content")
            
            # Issue 2: AI Cannot Parse Certificate Format
            if self.debug_tests['text_content_available'] and self.debug_tests['recalculate_docking_triggered']:
                api_response = self.debug_results.get('api_response', {})
                if not api_response.get('success', False):
                    self.log("✅ ISSUE 2 CONFIRMED: AI cannot parse certificate format")
                    self.log("   → Need to check what's in the certificate and improve AI prompt")
                else:
                    self.log("❌ ISSUE 2 NOT CONFIRMED: AI successfully parsed certificate")
            else:
                self.log("⚠️ ISSUE 2 CANNOT BE TESTED: Prerequisites not met")
            
            # Issue 3: Wrong Date Format
            if self.debug_tests['recalculate_docking_triggered']:
                api_response = self.debug_results.get('api_response', {})
                docking_dates = api_response.get('docking_dates')
                if docking_dates:
                    # Check if dates are in correct format
                    last_docking_1 = docking_dates.get('last_docking_1')
                    if last_docking_1:
                        # Check if it matches dd/MM/yyyy format
                        import re
                        if re.match(r'\d{2}/\d{2}/\d{4}', str(last_docking_1)):
                            self.log("❌ ISSUE 3 NOT CONFIRMED: Date format is correct (dd/MM/yyyy)")
                        else:
                            self.log("✅ ISSUE 3 CONFIRMED: Wrong date format")
                            self.log(f"   → Check parse_date_string() function")
                    else:
                        self.log("⚠️ ISSUE 3 CANNOT BE TESTED: No dates extracted")
                else:
                    self.log("⚠️ ISSUE 3 CANNOT BE TESTED: No docking dates returned")
            else:
                self.log("⚠️ ISSUE 3 CANNOT BE TESTED: API call failed")
            
            # Critical information summary
            self.log("\n📋 CRITICAL INFORMATION SUMMARY:")
            
            if self.debug_tests['pm242308_certificate_found']:
                self.log("1. ✅ PM242308 certificate found")
                if self.debug_tests['text_content_available']:
                    self.log("2. ✅ PM242308 certificate has text_content")
                    # Show sample text if available
                    for cert in self.cssc_certificates:
                        if cert.get('cert_no', '').upper() == 'PM242308':
                            text_content = cert.get('text_content', '')
                            if text_content:
                                self.log(f"3. Sample text content (first 500 chars):")
                                self.log(f"   '{str(text_content)[:500]}...'")
                            break
                else:
                    self.log("2. ❌ PM242308 certificate has NO text_content")
            else:
                self.log("1. ❌ PM242308 certificate NOT found")
            
            if self.debug_tests['recalculate_docking_triggered']:
                api_response = self.debug_results.get('api_response', {})
                self.log(f"4. API response: {json.dumps(api_response, indent=4)}")
            else:
                self.log("4. ❌ API call failed - no response to analyze")
            
            # Final recommendation
            root_cause = self.debug_results.get('root_cause', 'Unknown')
            self.log(f"\n🎯 FINAL DIAGNOSIS:")
            self.log(f"   ROOT CAUSE: {root_cause}")
            
            if "text_content" in root_cause.lower():
                self.log("   PRIORITY: HIGH - Fix certificate text extraction")
                self.log("   ACTION: Ensure OCR processor extracts text during PDF upload")
                self.log("   TECHNICAL: Check create_certificate_from_analysis_with_notes function")
            elif "parsing" in root_cause.lower():
                self.log("   PRIORITY: MEDIUM - Improve AI parsing logic")
                self.log("   ACTION: Enhance docking date extraction patterns")
                self.log("   TECHNICAL: Check extract_docking_dates_from_certificates function")
            elif "not found" in root_cause.lower():
                self.log("   PRIORITY: HIGH - Data availability issue")
                self.log("   ACTION: Verify ship and certificate data in database")
            else:
                self.log("   STATUS: System working correctly or unknown issue")
            
            self.debug_tests['root_cause_identified'] = True
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False
    
    def run_debug_test(self):
        """Main debug function for MINH ANH 09 docking issue"""
        self.log("🔄 MINH ANH 09 - RECALCULATE LAST DOCKING DEBUG TEST")
        self.log("🎯 FOCUS: Debug why MINH ANH 09 cannot extract last docking date from CSSC certificate")
        self.log("=" * 100)
        
        try:
            # Step 1: Login and Get Token
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with debugging")
                return False
            
            # Step 2: Get MINH ANH 09 Ship ID
            if not self.find_minh_anh_09_ship():
                self.log("❌ MINH ANH 09 ship not found - cannot proceed with debugging")
                return False
            
            # Step 3: Check CSSC Certificate has text_content
            if not self.check_cssc_certificate_text_content():
                self.log("❌ CSSC certificate check failed - proceeding with analysis")
            
            # Step 4: Trigger Recalculate Last Docking
            if not self.trigger_recalculate_last_docking():
                self.log("❌ Recalculate Last Docking failed - proceeding with analysis")
            
            # Step 5: Check Backend Logs
            self.check_backend_logs()
            
            # Step 6: Analyze Response
            self.provide_final_analysis()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Debug test error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run MINH ANH 09 docking debug test"""
    print("🔄 MINH ANH 09 - RECALCULATE LAST DOCKING DEBUG TEST STARTED")
    print("=" * 80)
    
    try:
        debugger = MinhAnh09DockingDebugger()
        success = debugger.run_debug_test()
        
        if success:
            print("\n✅ MINH ANH 09 DOCKING DEBUG TEST COMPLETED")
        else:
            print("\n❌ MINH ANH 09 DOCKING DEBUG TEST COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
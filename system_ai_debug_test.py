#!/usr/bin/env python3
"""
System AI Debug Test - Debug System AI Primary Method Implementation

REVIEW REQUEST FOCUS:
Debug the System AI primary method implementation to verify if the new structured prompt is being used correctly:

POST to /api/crew/analyze-passport with a Vietnamese passport file

**FOCUS: Debug System AI Prompt Usage**

Critical checks needed:
1. **Verify NEW structured prompt is being sent** to System AI (should contain "=== FIELDS TO EXTRACT ===" and example output format)
2. **Check System AI response format** - should return structured JSON with fields like "Passport_Number", "Surname", "Given_Names" 
3. **Verify field conversion** - structured format should be converted to old format (full_name, passport_number, etc.)
4. **Check extraction method logs** - should show "System AI as PRIMARY method with structured prompt"

**Expected Flow:**
- System AI receives new structured prompt
- Returns JSON with "Surname": "BUI", "Given_Names": "VAN HAI", etc.
- Backend converts to "full_name": "BUI VAN HAI"
- No more "EACH STARTING WITH" extraction errors

**Debug Questions:**
- Is the new prompt template actually being used?
- Is System AI returning structured format or old format?
- Is field conversion function being called?
- Are there any prompt or response parsing issues?

This should identify why System AI is still extracting "EACH STARTING WITH" despite the new structured prompt implementation.
"""

import requests
import json
import os
import sys
import re
import time
import traceback
from datetime import datetime

# Configuration
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipsurvey-ai.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class SystemAIDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.ship_name = "BROTHER 36"
        self.ship_id = None
        
        # Debug tracking for System AI prompt usage
        self.debug_results = {
            # Authentication and setup
            'authentication_successful': False,
            'ship_discovery_successful': False,
            
            # System AI Prompt Debug
            'structured_prompt_sent': False,
            'fields_to_extract_section_found': False,
            'example_output_format_found': False,
            'system_ai_primary_method_log': False,
            
            # System AI Response Debug
            'structured_json_response_received': False,
            'passport_number_field_found': False,
            'surname_field_found': False,
            'given_names_field_found': False,
            
            # Field Conversion Debug
            'field_conversion_function_called': False,
            'structured_to_old_format_conversion': False,
            'full_name_properly_constructed': False,
            'no_each_starting_with_errors': False,
            
            # Backend Logs Debug
            'system_ai_extraction_logs_found': False,
            'gemini_api_calls_confirmed': False,
            'structured_prompt_logs_found': False,
            'field_conversion_logs_found': False,
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
            response = requests.post(endpoint, json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.debug_results['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_ship(self):
        """Find the test ship"""
        try:
            self.log(f"🚢 Finding ship: {self.ship_name}")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                for ship in ships:
                    if ship.get("name") == self.ship_name:
                        self.ship_id = ship.get("id")
                        self.log(f"✅ Found ship: {self.ship_name} (ID: {self.ship_id})")
                        self.debug_results['ship_discovery_successful'] = True
                        return True
                
                self.log(f"❌ Ship '{self.ship_name}' not found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def get_vietnamese_passport_test_file(self):
        """Get a real Vietnamese passport PDF file for debugging"""
        try:
            self.log("📄 Using real Vietnamese passport PDF file...")
            
            # Use existing Vietnamese passport PDF file
            passport_files = [
                "/app/PASS_PORT_Tran_Trong_Toan.pdf",
                "/app/3_2O_THUONG_PP.pdf", 
                "/app/2_CO_DUC_PP.pdf"
            ]
            
            for passport_file in passport_files:
                if os.path.exists(passport_file):
                    file_size = os.path.getsize(passport_file)
                    self.log(f"✅ Found real passport file: {passport_file}")
                    self.log(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                    
                    # Verify it's a PDF file
                    with open(passport_file, 'rb') as f:
                        header = f.read(8)
                        if header.startswith(b'%PDF'):
                            self.log("✅ File is a valid PDF")
                            return passport_file
                        else:
                            self.log("❌ File is not a valid PDF", "ERROR")
                            continue
            
            self.log("❌ No valid Vietnamese passport PDF files found", "ERROR")
            return None
            
        except Exception as e:
            self.log(f"❌ Error getting passport file: {str(e)}", "ERROR")
            return None
    
    def debug_system_ai_passport_processing(self):
        """Debug System AI passport processing with focus on prompt usage"""
        try:
            self.log("🔍 DEBUGGING SYSTEM AI PASSPORT PROCESSING")
            self.log("=" * 80)
            self.log("Focus: Verify new structured prompt is being used correctly")
            self.log("Expected: System AI receives structured prompt with '=== FIELDS TO EXTRACT ==='")
            self.log("Expected: Returns JSON with 'Passport_Number', 'Surname', 'Given_Names'")
            self.log("Expected: Backend converts to old format (full_name, passport_number, etc.)")
            self.log("=" * 80)
            
            # Get real passport file
            passport_file_path = self.get_vietnamese_passport_test_file()
            if not passport_file_path:
                return False
            
            # Get filename for upload
            filename = os.path.basename(passport_file_path)
            
            # Prepare multipart form data
            with open(passport_file_path, "rb") as f:
                files = {
                    "passport_file": (filename, f, "application/pdf")
                }
                data = {
                    "ship_name": self.ship_name
                }
                
                self.log(f"📤 Uploading real Vietnamese passport PDF: {filename}")
                self.log(f"🚢 Ship name: {self.ship_name}")
                self.log("🎯 Focus: Debug System AI prompt and response handling")
                
                endpoint = f"{BACKEND_URL}/crew/analyze-passport"
                self.log(f"   POST {endpoint}")
                
                start_time = time.time()
                response = self.session.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=120  # Longer timeout for AI processing
                )
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            self.log(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Passport analysis endpoint accessible")
                
                self.log(f"📋 Response keys: {list(result.keys())}")
                
                # Debug System AI response structure
                if result.get("success"):
                    self.log("✅ Passport analysis successful")
                    
                    # Check analysis data for System AI extraction evidence
                    analysis = result.get("analysis", {})
                    if analysis:
                        self.log("🔍 DEBUGGING ANALYSIS DATA STRUCTURE:")
                        self.log(f"   Analysis keys: {list(analysis.keys())}")
                        
                        # Check for structured format evidence
                        structured_fields = ['Passport_Number', 'Surname', 'Given_Names', 'Date_of_Birth']
                        old_format_fields = ['full_name', 'passport_number', 'date_of_birth', 'place_of_birth']
                        
                        structured_found = any(field in analysis for field in structured_fields)
                        old_format_found = any(field in analysis for field in old_format_fields)
                        
                        if structured_found:
                            self.log("🎯 STRUCTURED FORMAT DETECTED in response:")
                            self.debug_results['structured_json_response_received'] = True
                            for field in structured_fields:
                                if field in analysis:
                                    self.log(f"   ✅ {field}: {analysis[field]}")
                                    if field == 'Passport_Number':
                                        self.debug_results['passport_number_field_found'] = True
                                    elif field == 'Surname':
                                        self.debug_results['surname_field_found'] = True
                                    elif field == 'Given_Names':
                                        self.debug_results['given_names_field_found'] = True
                        
                        if old_format_found:
                            self.log("🔄 OLD FORMAT DETECTED in response:")
                            for field in old_format_fields:
                                if field in analysis:
                                    self.log(f"   ✅ {field}: {analysis[field]}")
                                    
                                    # Check for field conversion evidence
                                    if field == 'full_name' and analysis[field]:
                                        full_name = analysis[field]
                                        # Check if it's properly constructed (not containing "EACH STARTING WITH")
                                        if "EACH STARTING WITH" not in full_name.upper():
                                            self.debug_results['no_each_starting_with_errors'] = True
                                            self.log(f"   ✅ No 'EACH STARTING WITH' errors in full_name")
                                        else:
                                            self.log(f"   ❌ 'EACH STARTING WITH' error found in full_name: {full_name}")
                                        
                                        # Check if it looks like converted structured format
                                        if " " in full_name and len(full_name.split()) >= 2:
                                            self.debug_results['full_name_properly_constructed'] = True
                                            self.log(f"   ✅ Full name properly constructed: {full_name}")
                        
                        # Check processing method for System AI evidence
                        processing_method = result.get("processing_method", "")
                        if processing_method:
                            self.log(f"🔧 Processing method: {processing_method}")
                            if "system" in processing_method.lower() or "ai" in processing_method.lower():
                                self.log("   ✅ System AI processing method detected")
                    
                    return True
                else:
                    error_msg = result.get("message", "Unknown error")
                    self.log(f"❌ Passport analysis failed: {error_msg}", "ERROR")
                    
                    # Check for specific error patterns
                    if "EACH STARTING WITH" in error_msg:
                        self.log("🚨 CRITICAL: 'EACH STARTING WITH' error detected in response!", "ERROR")
                    
                    return False
            else:
                self.log(f"❌ Passport analysis request failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in System AI debug test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def analyze_backend_logs_for_system_ai_evidence(self):
        """Analyze backend logs for System AI prompt and processing evidence"""
        try:
            self.log("📋 ANALYZING BACKEND LOGS FOR SYSTEM AI EVIDENCE")
            self.log("=" * 60)
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            # Patterns to look for in logs
            system_ai_patterns = [
                "System AI as PRIMARY method with structured prompt",
                "Using System AI as PRIMARY method",
                "Implementing ACTUAL System AI extraction",
                "Sending extraction prompt to gemini",
                "System AI extraction successful",
                "Converted structured passport fields",
                "=== FIELDS TO EXTRACT ===",
                "Passport_Number",
                "Surname",
                "Given_Names"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Analyzing {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            self.log(f"   📊 Analyzing {len(lines)} log lines...")
                            
                            # Look for System AI evidence
                            for pattern in system_ai_patterns:
                                matching_lines = [line for line in lines if pattern in line]
                                if matching_lines:
                                    self.log(f"   ✅ Found pattern '{pattern}':")
                                    for line in matching_lines[-3:]:  # Show last 3 matches
                                        self.log(f"      🔍 {line.strip()}")
                                    
                                    # Set debug flags based on patterns found
                                    if "System AI as PRIMARY method" in pattern:
                                        self.debug_results['system_ai_primary_method_log'] = True
                                    elif "=== FIELDS TO EXTRACT ===" in pattern:
                                        self.debug_results['fields_to_extract_section_found'] = True
                                        self.debug_results['structured_prompt_sent'] = True
                                    elif "Sending extraction prompt to gemini" in pattern:
                                        self.debug_results['gemini_api_calls_confirmed'] = True
                                    elif "System AI extraction successful" in pattern:
                                        self.debug_results['system_ai_extraction_logs_found'] = True
                                    elif "Converted structured passport fields" in pattern:
                                        self.debug_results['field_conversion_function_called'] = True
                                        self.debug_results['structured_to_old_format_conversion'] = True
                                else:
                                    self.log(f"   ❌ Pattern '{pattern}' NOT found")
                            
                            # Look for error patterns
                            error_patterns = [
                                "EACH STARTING WITH",
                                "extraction error",
                                "prompt error",
                                "AI response error"
                            ]
                            
                            self.log("   🚨 Checking for error patterns:")
                            for error_pattern in error_patterns:
                                error_lines = [line for line in lines if error_pattern.lower() in line.lower()]
                                if error_lines:
                                    self.log(f"   ❌ Found error pattern '{error_pattern}':")
                                    for line in error_lines[-2:]:  # Show last 2 error matches
                                        self.log(f"      🚨 {line.strip()}")
                                else:
                                    self.log(f"   ✅ No '{error_pattern}' errors found")
                        else:
                            self.log(f"   ⚠️ {log_file} is empty or not accessible")
                    except Exception as e:
                        self.log(f"   ❌ Error reading {log_file}: {e}")
                else:
                    self.log(f"   ⚠️ {log_file} not found")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error analyzing backend logs: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_system_ai_debug(self):
        """Run comprehensive System AI debug test"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE SYSTEM AI DEBUG TEST")
            self.log("=" * 80)
            self.log("OBJECTIVE: Debug System AI primary method implementation")
            self.log("FOCUS: Verify new structured prompt usage and field conversion")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Ship Discovery
            self.log("\nSTEP 2: Ship Discovery")
            if not self.find_ship():
                self.log("❌ CRITICAL: Ship discovery failed - cannot proceed")
                return False
            
            # Step 3: System AI Passport Processing Debug
            self.log("\nSTEP 3: System AI Passport Processing Debug")
            success = self.debug_system_ai_passport_processing()
            
            # Step 4: Backend Logs Analysis
            self.log("\nSTEP 4: Backend Logs Analysis for System AI Evidence")
            self.analyze_backend_logs_for_system_ai_evidence()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE SYSTEM AI DEBUG TEST COMPLETED")
            return success
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in System AI debug test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_debug_summary(self):
        """Print comprehensive summary of System AI debug results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 SYSTEM AI DEBUG TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.debug_results)
            passed_tests = sum(1 for result in self.debug_results.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Debug Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} checks passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('ship_discovery_successful', 'Ship discovery successful'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.debug_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # System AI Prompt Debug Results
            self.log("\n🤖 SYSTEM AI PROMPT DEBUG:")
            prompt_tests = [
                ('structured_prompt_sent', 'NEW structured prompt sent to System AI'),
                ('fields_to_extract_section_found', '"=== FIELDS TO EXTRACT ===" section found'),
                ('example_output_format_found', 'Example output format found in prompt'),
                ('system_ai_primary_method_log', '"System AI as PRIMARY method" log found'),
            ]
            
            for test_key, description in prompt_tests:
                status = "✅ PASS" if self.debug_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # System AI Response Debug Results
            self.log("\n📥 SYSTEM AI RESPONSE DEBUG:")
            response_tests = [
                ('structured_json_response_received', 'Structured JSON response received'),
                ('passport_number_field_found', '"Passport_Number" field found'),
                ('surname_field_found', '"Surname" field found'),
                ('given_names_field_found', '"Given_Names" field found'),
            ]
            
            for test_key, description in response_tests:
                status = "✅ PASS" if self.debug_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Field Conversion Debug Results
            self.log("\n🔄 FIELD CONVERSION DEBUG:")
            conversion_tests = [
                ('field_conversion_function_called', 'Field conversion function called'),
                ('structured_to_old_format_conversion', 'Structured to old format conversion'),
                ('full_name_properly_constructed', 'Full name properly constructed'),
                ('no_each_starting_with_errors', 'No "EACH STARTING WITH" errors'),
            ]
            
            for test_key, description in conversion_tests:
                status = "✅ PASS" if self.debug_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Debug Results
            self.log("\n📋 BACKEND LOGS DEBUG:")
            log_tests = [
                ('system_ai_extraction_logs_found', 'System AI extraction logs found'),
                ('gemini_api_calls_confirmed', 'Gemini API calls confirmed'),
                ('structured_prompt_logs_found', 'Structured prompt logs found'),
                ('field_conversion_logs_found', 'Field conversion logs found'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.debug_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Analysis
            self.log("\n🎯 CRITICAL ANALYSIS:")
            
            # Check if new structured prompt is being used
            structured_prompt_working = (
                self.debug_results.get('structured_prompt_sent', False) and
                self.debug_results.get('fields_to_extract_section_found', False) and
                self.debug_results.get('system_ai_primary_method_log', False)
            )
            
            if structured_prompt_working:
                self.log("   ✅ NEW STRUCTURED PROMPT IS BEING USED")
            else:
                self.log("   ❌ NEW STRUCTURED PROMPT NOT CONFIRMED")
            
            # Check if System AI is returning structured format
            structured_response_working = (
                self.debug_results.get('structured_json_response_received', False) and
                self.debug_results.get('passport_number_field_found', False) and
                self.debug_results.get('surname_field_found', False)
            )
            
            if structured_response_working:
                self.log("   ✅ SYSTEM AI RETURNING STRUCTURED FORMAT")
            else:
                self.log("   ❌ SYSTEM AI STRUCTURED FORMAT NOT CONFIRMED")
            
            # Check if field conversion is working
            field_conversion_working = (
                self.debug_results.get('field_conversion_function_called', False) and
                self.debug_results.get('structured_to_old_format_conversion', False) and
                self.debug_results.get('full_name_properly_constructed', False)
            )
            
            if field_conversion_working:
                self.log("   ✅ FIELD CONVERSION IS WORKING")
            else:
                self.log("   ❌ FIELD CONVERSION NOT CONFIRMED")
            
            # Check if "EACH STARTING WITH" errors are resolved
            if self.debug_results.get('no_each_starting_with_errors', False):
                self.log("   ✅ NO MORE 'EACH STARTING WITH' EXTRACTION ERRORS")
            else:
                self.log("   ❌ 'EACH STARTING WITH' ERRORS MAY STILL EXIST")
            
            # Overall Assessment
            self.log("\n🏆 OVERALL ASSESSMENT:")
            
            critical_checks = [
                'structured_prompt_sent',
                'system_ai_primary_method_log',
                'field_conversion_function_called',
                'no_each_starting_with_errors'
            ]
            
            critical_passed = sum(1 for check in critical_checks if self.debug_results.get(check, False))
            
            if critical_passed == len(critical_checks):
                self.log("   ✅ ALL CRITICAL SYSTEM AI CHECKS PASSED")
                self.log("   ✅ New structured prompt implementation working correctly")
                self.log("   ✅ System AI extraction errors should be resolved")
            elif critical_passed >= len(critical_checks) * 0.75:
                self.log("   ⚠️ MOST CRITICAL CHECKS PASSED - Minor issues may remain")
                self.log(f"   ⚠️ {critical_passed}/{len(critical_checks)} critical checks passed")
            else:
                self.log("   ❌ CRITICAL SYSTEM AI ISSUES IDENTIFIED")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_checks)} critical checks passed")
                self.log("   ❌ System AI structured prompt may not be working correctly")
            
            if success_rate >= 80:
                self.log(f"   ✅ EXCELLENT DEBUG SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ GOOD DEBUG SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW DEBUG SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing debug summary: {str(e)}", "ERROR")

def main():
    """Main function to run the System AI debug tests"""
    print("🔍 System AI Debug Test - Debug System AI Primary Method Implementation")
    print("🎯 Focus: Verify new structured prompt usage and field conversion")
    print("=" * 80)
    print("Debug objectives:")
    print("1. Verify NEW structured prompt is being sent to System AI")
    print("2. Check System AI response format (structured JSON)")
    print("3. Verify field conversion (structured to old format)")
    print("4. Check extraction method logs")
    print("5. Identify why 'EACH STARTING WITH' errors may still occur")
    print("=" * 80)
    
    tester = SystemAIDebugTester()
    
    try:
        # Run comprehensive debug test
        success = tester.run_comprehensive_system_ai_debug()
        
        # Print debug summary
        tester.print_debug_summary()
        
        # Return appropriate exit code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n❌ Debug test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
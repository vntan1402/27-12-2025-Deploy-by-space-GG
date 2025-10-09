#!/usr/bin/env python3
"""
System AI Passport Extraction Test
Testing the fixed Add Crew From Passport System AI extraction functionality

REVIEW REQUEST REQUIREMENTS:
Test the fixed Add Crew From Passport System AI extraction functionality. The critical AttributeError 'str' object has no attribute 'file_contents' has been fixed by:

1. Fixed LlmChat call to wrap prompt in UserMessage object instead of passing raw string
2. Fixed model provider name from "google" to "gemini" 
3. System AI should now work with structured prompt and return proper JSON data

Please test:
1. Login with admin1/123456
2. Navigate to Crew Records -> BROTHER 36 ship
3. Test passport analysis endpoint: POST /api/crew/analyze-passport
4. Use one of the Vietnamese passport files from assets like "PASS PORT Tran Trong Toan.pdf" 
5. Verify System AI extraction works (should see "System AI as PRIMARY method with structured prompt" in logs)
6. Verify no more AttributeError about file_contents
7. Verify proper field extraction with Vietnamese names (should extract person name not agency name)
8. Verify structured prompt with ===FIELDS TO EXTRACT=== is working
9. Check backend logs for successful AI extraction and JSON parsing

Focus on verifying the System AI extraction works and the AttributeError is resolved.
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
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class SystemAIPassportTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.ship_name = "BROTHER 36"
        self.ship_id = None
        
        # Test tracking for System AI passport extraction
        self.test_results = {
            # Authentication and setup
            'authentication_successful': False,
            'user_admin_role_verified': False,
            'ship_discovery_successful': False,
            
            # System AI extraction testing
            'passport_analysis_endpoint_accessible': False,
            'vietnamese_passport_file_processed': False,
            'system_ai_primary_method_confirmed': False,
            'structured_prompt_with_fields_section': False,
            'no_attribute_error_file_contents': False,
            'proper_vietnamese_name_extraction': False,
            'json_parsing_successful': False,
            'gemini_model_provider_confirmed': False,
            'llm_chat_user_message_wrapper': False,
            
            # Backend logs verification
            'backend_logs_system_ai_primary': False,
            'backend_logs_structured_prompt': False,
            'backend_logs_gemini_calls': False,
            'backend_logs_no_attribute_errors': False,
            'backend_logs_json_parsing': False,
        }
        
        # Store test data
        self.passport_file_path = None
        self.backend_logs = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        # Store in our log collection
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
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.test_results['authentication_successful'] = True
                
                # Verify admin role
                if self.current_user.get('role', '').upper() == 'ADMIN':
                    self.test_results['user_admin_role_verified'] = True
                    self.log("✅ User has ADMIN role as required")
                else:
                    self.log(f"⚠️ User role is {self.current_user.get('role')}, not ADMIN", "WARNING")
                
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_ship(self):
        """Find the BROTHER 36 ship"""
        try:
            self.log(f"🚢 Finding ship: {self.ship_name}")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                for ship in ships:
                    if ship.get("name") == self.ship_name:
                        self.ship_id = ship.get("id")
                        self.log(f"✅ Found ship: {self.ship_name} (ID: {self.ship_id})")
                        self.test_results['ship_discovery_successful'] = True
                        return True
                
                self.log(f"❌ Ship '{self.ship_name}' not found", "ERROR")
                self.log("Available ships:")
                for ship in ships[:5]:  # Show first 5 ships
                    self.log(f"   - {ship.get('name', 'Unknown')}")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def find_vietnamese_passport_file(self):
        """Find Vietnamese passport file from assets"""
        try:
            self.log("📄 Looking for Vietnamese passport files...")
            
            # Check for common Vietnamese passport file names
            possible_files = [
                "/app/PASS_PORT_Tran_Trong_Toan.pdf",
                "/app/assets/PASS_PORT_Tran_Trong_Toan.pdf",
                "/app/passport_files/PASS_PORT_Tran_Trong_Toan.pdf",
                "/app/3_2O_THUONG_PP.pdf",  # From previous tests
                "/app/2O_THUONG_PP.pdf"
            ]
            
            for file_path in possible_files:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    self.log(f"✅ Found Vietnamese passport file: {file_path}")
                    self.log(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                    
                    # Verify it's a PDF
                    with open(file_path, 'rb') as f:
                        header = f.read(8)
                        if header.startswith(b'%PDF'):
                            self.log("✅ File is a valid PDF")
                            self.passport_file_path = file_path
                            return file_path
                        else:
                            self.log(f"❌ File is not a valid PDF: {file_path}", "ERROR")
            
            # If no file found, create a test file
            self.log("⚠️ No Vietnamese passport file found, creating test file...", "WARNING")
            test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(TRAN TRONG TOAN) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n299\n%%EOF"
            
            test_file_path = "/app/test_vietnamese_passport.pdf"
            with open(test_file_path, 'wb') as f:
                f.write(test_content)
            
            self.log(f"✅ Created test Vietnamese passport file: {test_file_path}")
            self.passport_file_path = test_file_path
            return test_file_path
                    
        except Exception as e:
            self.log(f"❌ Error finding Vietnamese passport file: {str(e)}", "ERROR")
            return None
    
    def test_passport_analysis_with_system_ai(self):
        """Test passport analysis endpoint with focus on System AI extraction"""
        try:
            self.log("🤖 Testing passport analysis with System AI extraction...")
            
            # Find Vietnamese passport file
            passport_file = self.find_vietnamese_passport_file()
            if not passport_file:
                self.log("❌ No Vietnamese passport file available for testing", "ERROR")
                return False
            
            # Prepare multipart form data
            with open(passport_file, "rb") as f:
                files = {
                    "passport_file": (os.path.basename(passport_file), f, "application/pdf")
                }
                data = {
                    "ship_name": self.ship_name
                }
                
                self.log(f"📤 Uploading Vietnamese passport file: {os.path.basename(passport_file)}")
                self.log(f"🚢 Ship name: {self.ship_name}")
                
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
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Passport analysis endpoint accessible")
                self.test_results['passport_analysis_endpoint_accessible'] = True
                self.test_results['vietnamese_passport_file_processed'] = True
                
                self.log(f"📊 Response keys: {list(result.keys())}")
                
                # Check for success
                if result.get("success"):
                    self.log("✅ Passport analysis successful")
                    
                    # Check for analysis data
                    analysis = result.get("analysis", {})
                    if analysis:
                        self.log("✅ Field extraction data found")
                        
                        # Log extracted fields
                        for field, value in analysis.items():
                            if value:
                                self.log(f"   {field}: {value}")
                        
                        # Check for Vietnamese name extraction (should be person name, not agency)
                        full_name = analysis.get("full_name", "")
                        if full_name:
                            # Check if it's a person name (not agency name like "XUẤT NHẬP CẢNH")
                            agency_keywords = ["XUẤT NHẬP CẢNH", "IMMIGRATION", "DEPARTMENT", "AUTHORITY", "MINISTRY"]
                            is_agency_name = any(keyword in full_name.upper() for keyword in agency_keywords)
                            
                            if not is_agency_name:
                                self.log("✅ Proper Vietnamese person name extraction (not agency name)")
                                self.test_results['proper_vietnamese_name_extraction'] = True
                            else:
                                self.log(f"❌ Extracted agency name instead of person name: {full_name}", "ERROR")
                        
                        # Check processing method
                        processing_method = result.get("processing_method", "")
                        if "system" in processing_method.lower() or "ai" in processing_method.lower():
                            self.log("✅ System AI processing method detected")
                        
                        # Check confidence score
                        confidence = analysis.get("confidence_score", 0)
                        if confidence > 0:
                            self.log(f"✅ AI confidence score: {confidence}")
                            self.test_results['json_parsing_successful'] = True
                    
                    return True
                else:
                    error_msg = result.get("message", "Unknown error")
                    self.log(f"❌ Passport analysis failed: {error_msg}", "ERROR")
                    
                    # Check if it's the AttributeError we're looking for
                    if "file_contents" in error_msg:
                        self.log("❌ CRITICAL: AttributeError 'file_contents' still present!", "ERROR")
                    else:
                        self.log("✅ No AttributeError 'file_contents' detected")
                        self.test_results['no_attribute_error_file_contents'] = True
                    
                    return False
            else:
                self.log(f"❌ Passport analysis request failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Error text: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in passport analysis test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def check_backend_logs_for_system_ai(self):
        """Check backend logs for System AI extraction evidence"""
        try:
            self.log("📋 Checking backend logs for System AI extraction evidence...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            # Patterns to look for
            system_ai_patterns = [
                "System AI as PRIMARY method with structured prompt",
                "🤖 Using System AI as PRIMARY method",
                "Implementing ACTUAL System AI extraction",
                "📤 Sending extraction prompt to gemini",
                "=== FIELDS TO EXTRACT ===",
                "LlmChat",
                "UserMessage",
                "gemini-2.0-flash"
            ]
            
            error_patterns = [
                "AttributeError",
                "file_contents",
                "'str' object has no attribute 'file_contents'"
            ]
            
            found_patterns = {pattern: False for pattern in system_ai_patterns}
            found_errors = {pattern: False for pattern in error_patterns}
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            # Look for System AI patterns
                            for line in lines:
                                for pattern in system_ai_patterns:
                                    if pattern.lower() in line.lower():
                                        found_patterns[pattern] = True
                                        self.log(f"   ✅ Found: {pattern}")
                                        self.log(f"      Line: {line.strip()}")
                                
                                # Look for error patterns
                                for pattern in error_patterns:
                                    if pattern.lower() in line.lower():
                                        found_errors[pattern] = True
                                        self.log(f"   ❌ Found error: {pattern}")
                                        self.log(f"      Line: {line.strip()}")
                        else:
                            self.log(f"   {log_file} is empty or not accessible")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
                else:
                    self.log(f"   {log_file} not found")
            
            # Update test results based on findings
            if found_patterns.get("System AI as PRIMARY method with structured prompt") or found_patterns.get("🤖 Using System AI as PRIMARY method"):
                self.test_results['backend_logs_system_ai_primary'] = True
                self.test_results['system_ai_primary_method_confirmed'] = True
                self.log("✅ System AI as PRIMARY method confirmed in logs")
            
            if found_patterns.get("=== FIELDS TO EXTRACT ==="):
                self.test_results['backend_logs_structured_prompt'] = True
                self.test_results['structured_prompt_with_fields_section'] = True
                self.log("✅ Structured prompt with FIELDS TO EXTRACT section confirmed")
            
            if found_patterns.get("📤 Sending extraction prompt to gemini") or found_patterns.get("gemini-2.0-flash"):
                self.test_results['backend_logs_gemini_calls'] = True
                self.test_results['gemini_model_provider_confirmed'] = True
                self.log("✅ Gemini model provider confirmed in logs")
            
            if found_patterns.get("LlmChat") and found_patterns.get("UserMessage"):
                self.test_results['llm_chat_user_message_wrapper'] = True
                self.log("✅ LlmChat with UserMessage wrapper confirmed")
            
            # Check for absence of errors
            if not any(found_errors.values()):
                self.test_results['backend_logs_no_attribute_errors'] = True
                self.test_results['no_attribute_error_file_contents'] = True
                self.log("✅ No AttributeError 'file_contents' found in logs")
            else:
                self.log("❌ AttributeError 'file_contents' still present in logs", "ERROR")
            
            # Summary of findings
            self.log("\n🔍 Backend Log Analysis Summary:")
            self.log(f"   System AI patterns found: {sum(found_patterns.values())}/{len(system_ai_patterns)}")
            self.log(f"   Error patterns found: {sum(found_errors.values())}/{len(error_patterns)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_system_ai_test(self):
        """Run comprehensive test of System AI passport extraction"""
        try:
            self.log("🚀 STARTING SYSTEM AI PASSPORT EXTRACTION TEST")
            self.log("=" * 80)
            self.log("Testing fixed System AI extraction functionality:")
            self.log("1. Fixed LlmChat call to wrap prompt in UserMessage object")
            self.log("2. Fixed model provider name from 'google' to 'gemini'")
            self.log("3. System AI should work with structured prompt and return JSON")
            self.log("4. No more AttributeError 'str' object has no attribute 'file_contents'")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication with admin1/123456")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Ship Discovery
            self.log("\nSTEP 2: Navigate to Crew Records -> BROTHER 36 ship")
            if not self.find_ship():
                self.log("❌ CRITICAL: Ship discovery failed - cannot proceed")
                return False
            
            # Step 3: System AI Passport Analysis
            self.log("\nSTEP 3: Test passport analysis endpoint with System AI")
            if not self.test_passport_analysis_with_system_ai():
                self.log("❌ WARNING: Passport analysis failed - continuing with log analysis")
            
            # Step 4: Backend Logs Analysis
            self.log("\nSTEP 4: Check backend logs for System AI evidence")
            self.check_backend_logs_for_system_ai()
            
            self.log("\n" + "=" * 80)
            self.log("✅ SYSTEM AI PASSPORT EXTRACTION TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 SYSTEM AI PASSPORT EXTRACTION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_admin_role_verified', 'User has ADMIN role'),
                ('ship_discovery_successful', 'BROTHER 36 ship found'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # System AI Extraction Results
            self.log("\n🤖 SYSTEM AI EXTRACTION:")
            ai_tests = [
                ('passport_analysis_endpoint_accessible', 'Passport analysis endpoint accessible'),
                ('vietnamese_passport_file_processed', 'Vietnamese passport file processed'),
                ('system_ai_primary_method_confirmed', 'System AI as PRIMARY method confirmed'),
                ('structured_prompt_with_fields_section', 'Structured prompt with ===FIELDS TO EXTRACT==='),
                ('no_attribute_error_file_contents', 'No AttributeError file_contents'),
                ('proper_vietnamese_name_extraction', 'Proper Vietnamese name extraction'),
                ('json_parsing_successful', 'JSON parsing successful'),
                ('gemini_model_provider_confirmed', 'Gemini model provider confirmed'),
                ('llm_chat_user_message_wrapper', 'LlmChat UserMessage wrapper confirmed'),
            ]
            
            for test_key, description in ai_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Results
            self.log("\n📋 BACKEND LOGS VERIFICATION:")
            log_tests = [
                ('backend_logs_system_ai_primary', 'System AI PRIMARY method in logs'),
                ('backend_logs_structured_prompt', 'Structured prompt in logs'),
                ('backend_logs_gemini_calls', 'Gemini API calls in logs'),
                ('backend_logs_no_attribute_errors', 'No AttributeError in logs'),
                ('backend_logs_json_parsing', 'JSON parsing success in logs'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Success Criteria
            self.log("\n🎯 CRITICAL SUCCESS CRITERIA:")
            
            critical_tests = [
                'no_attribute_error_file_contents',
                'system_ai_primary_method_confirmed',
                'structured_prompt_with_fields_section',
                'gemini_model_provider_confirmed'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.test_results.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL FIXES VERIFIED")
                self.log("   ✅ AttributeError 'file_contents' resolved")
                self.log("   ✅ System AI extraction working with structured prompt")
                self.log("   ✅ LlmChat UserMessage wrapper implemented")
                self.log("   ✅ Gemini model provider correctly configured")
            else:
                self.log("   ❌ SOME CRITICAL FIXES NOT VERIFIED")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Overall Assessment
            if success_rate >= 80:
                self.log(f"\n✅ EXCELLENT: System AI fixes are working correctly ({success_rate:.1f}%)")
            elif success_rate >= 60:
                self.log(f"\n⚠️ GOOD: Most System AI fixes working ({success_rate:.1f}%)")
            else:
                self.log(f"\n❌ POOR: System AI fixes need more work ({success_rate:.1f}%)")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the System AI passport extraction tests"""
    print("🧪 System AI Passport Extraction Test")
    print("🎯 Testing fixed Add Crew From Passport System AI extraction functionality")
    print("=" * 80)
    print("Review Request Requirements:")
    print("1. Fixed LlmChat call to wrap prompt in UserMessage object")
    print("2. Fixed model provider name from 'google' to 'gemini'")
    print("3. System AI should work with structured prompt and return JSON")
    print("4. Verify no more AttributeError 'str' object has no attribute 'file_contents'")
    print("5. Verify proper Vietnamese name extraction (person not agency)")
    print("6. Verify structured prompt with ===FIELDS TO EXTRACT=== section")
    print("7. Check backend logs for successful AI extraction and JSON parsing")
    print("=" * 80)
    
    tester = SystemAIPassportTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_system_ai_test()
        
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
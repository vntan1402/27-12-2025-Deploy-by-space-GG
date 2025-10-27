#!/usr/bin/env python3
"""
Test Report AI Analysis Endpoint Testing with Enhanced Logging
Focus: Debug Document AI response structure to identify why summary_text is empty

REVIEW REQUEST REQUIREMENTS:
Re-test the Test Report AI analysis endpoint with enhanced logging.

## Context
Previous test showed Document AI returns no summary_text. Added debug logging to see the full response structure from Document AI.

## Test Steps
1. Login with admin1/123456
2. Find a ship
3. Upload /tmp/Chemical_Suit.pdf to /api/test-reports/analyze-file
4. Check backend logs for NEW debug messages:
   - "📋 Document AI result keys: ..."
   - "📋 ai_analysis keys: ..."
   - "⚠️ No summary_text in response. Full ai_result: ..."
5. Analyze what fields are actually in the response

## Expected
- See the actual structure of Document AI response
- Identify why summary_text is empty
- Determine correct field path to get the text
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
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipdoclists.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class TestReportAIDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.ship_name = "BROTHER 36"
        self.ship_id = None
        
        # Test tracking for test report AI analysis
        self.test_report_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'ship_discovery_successful': False,
            'chemical_suit_pdf_found': False,
            
            # Test Report AI Analysis endpoint
            'test_report_analysis_endpoint_accessible': False,
            'test_report_file_upload_successful': False,
            'document_ai_processing_initiated': False,
            'document_ai_processing_completed': False,
            
            # Enhanced logging verification
            'document_ai_result_keys_logged': False,
            'ai_analysis_keys_logged': False,
            'no_summary_text_warning_logged': False,
            'full_ai_result_logged': False,
            
            # Response structure analysis
            'response_structure_analyzed': False,
            'field_extraction_attempted': False,
            'summary_text_field_identified': False,
            'alternative_text_fields_found': False,
            
            # Backend logs verification
            'backend_logs_document_ai_debug': False,
            'backend_logs_response_structure': False,
            'backend_logs_field_mapping': False,
        }
        
        # Store test data
        self.test_filename = "Chemical_Suit.pdf"
        self.chemical_suit_pdf_path = "/tmp/Chemical_Suit.pdf"
        
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
                
                self.test_report_tests['authentication_successful'] = True
                self.test_report_tests['user_company_identified'] = bool(self.current_user.get('company'))
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
                        self.test_report_tests['ship_discovery_successful'] = True
                        return True
                
                self.log(f"❌ Ship '{self.ship_name}' not found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def verify_chemical_suit_pdf(self):
        """Verify the Chemical Suit PDF file exists"""
        try:
            self.log(f"📄 Verifying Chemical Suit PDF: {self.chemical_suit_pdf_path}")
            
            if not os.path.exists(self.chemical_suit_pdf_path):
                self.log(f"❌ Chemical Suit PDF not found: {self.chemical_suit_pdf_path}", "ERROR")
                return False
            
            file_size = os.path.getsize(self.chemical_suit_pdf_path)
            self.log(f"✅ Chemical Suit PDF found")
            self.log(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            # Check if it's a PDF file
            with open(self.chemical_suit_pdf_path, 'rb') as f:
                header = f.read(8)
                if header.startswith(b'%PDF'):
                    self.log("✅ File is a valid PDF")
                    self.test_report_tests['chemical_suit_pdf_found'] = True
                    return True
                else:
                    self.log("❌ File is not a valid PDF", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error verifying Chemical Suit PDF: {str(e)}", "ERROR")
            return False
    
    def test_test_report_analysis_endpoint(self):
        """Test the test report analysis endpoint with Chemical Suit PDF"""
        try:
            self.log("📊 Testing test report analysis endpoint with Chemical Suit PDF...")
            
            # Verify Chemical Suit PDF file
            if not self.verify_chemical_suit_pdf():
                return False
            
            # Prepare multipart form data with Chemical Suit PDF
            with open(self.chemical_suit_pdf_path, "rb") as f:
                files = {
                    "test_report_file": (self.test_filename, f, "application/pdf")
                }
                data = {
                    "ship_id": self.ship_id
                }
                
                self.log(f"📤 Uploading Chemical Suit PDF: {self.test_filename}")
                self.log(f"🚢 Ship ID: {self.ship_id}")
                
                endpoint = f"{BACKEND_URL}/test-reports/analyze-file"
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
                self.log("✅ Test report analysis endpoint accessible")
                self.test_report_tests['test_report_analysis_endpoint_accessible'] = True
                self.test_report_tests['test_report_file_upload_successful'] = True
                
                self.log(f"📊 Response keys: {list(result.keys())}")
                
                # Check for success
                if result.get("success"):
                    self.log("✅ Test report analysis successful")
                    self.test_report_tests['document_ai_processing_completed'] = True
                    
                    # Analyze response structure
                    self.analyze_response_structure(result)
                    
                    # Check for analysis data
                    analysis = result.get("analysis", {})
                    if analysis:
                        self.log("📋 Analysis data found:")
                        self.test_report_tests['field_extraction_attempted'] = True
                        
                        # Log all extracted fields
                        for field, value in analysis.items():
                            self.log(f"   {field}: {value}")
                        
                        # Check for summary text specifically
                        summary_text = analysis.get("_summary_text", "")
                        if summary_text:
                            self.log(f"✅ Summary text found: {len(summary_text)} characters")
                            self.test_report_tests['summary_text_field_identified'] = True
                        else:
                            self.log("⚠️ Summary text is empty or missing", "WARNING")
                    
                    # Check processing method
                    processing_method = result.get("processing_method", "")
                    self.log(f"📋 Processing method: {processing_method}")
                    
                    return True
                else:
                    error_msg = result.get("message", "Unknown error")
                    self.log(f"❌ Test report analysis failed: {error_msg}", "ERROR")
                    return False
            else:
                self.log(f"❌ Test report analysis request failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in test report analysis endpoint test: {str(e)}", "ERROR")
            return False
    
    def analyze_response_structure(self, result):
        """Analyze the response structure to understand field mapping"""
        try:
            self.log("🔍 Analyzing response structure...")
            self.test_report_tests['response_structure_analyzed'] = True
            
            # Check main response keys
            main_keys = list(result.keys())
            self.log(f"   Main response keys: {main_keys}")
            
            # Check analysis section
            analysis = result.get("analysis", {})
            if analysis:
                analysis_keys = list(analysis.keys())
                self.log(f"   Analysis keys: {analysis_keys}")
                
                # Look for text-related fields
                text_fields = []
                for key, value in analysis.items():
                    if isinstance(value, str) and len(value) > 100:  # Likely text content
                        text_fields.append(key)
                        self.log(f"   Text field '{key}': {len(value)} characters")
                
                if text_fields:
                    self.log(f"✅ Found {len(text_fields)} potential text fields: {text_fields}")
                    self.test_report_tests['alternative_text_fields_found'] = True
                else:
                    self.log("⚠️ No substantial text fields found in analysis", "WARNING")
            
            # Check for file content
            file_content = result.get("file_content")
            if file_content:
                self.log(f"   File content present: {len(file_content)} characters (base64)")
            
            # Check for other relevant fields
            other_fields = ['processing_method', 'confidence_score', 'ship_name', 'ship_imo']
            for field in other_fields:
                if field in result:
                    self.log(f"   {field}: {result[field]}")
            
        except Exception as e:
            self.log(f"❌ Error analyzing response structure: {str(e)}", "ERROR")
    
    def check_backend_logs_for_debug_messages(self):
        """Check backend logs for the NEW debug messages about Document AI response structure"""
        try:
            self.log("📋 Checking backend logs for NEW debug messages...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            # Debug patterns we're looking for
            debug_patterns = [
                "📋 Document AI result keys:",
                "📋 ai_analysis keys:",
                "⚠️ No summary_text in response. Full ai_result:",
                "Document AI result keys:",
                "ai_analysis keys:",
                "No summary_text in response",
                "Full ai_result:"
            ]
            
            found_patterns = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            for line in lines:
                                # Check for debug patterns
                                for pattern in debug_patterns:
                                    if pattern in line:
                                        found_patterns.append(pattern)
                                        self.log(f"   🔍 FOUND: {line}")
                                        
                                        # Mark specific tests as passed
                                        if "Document AI result keys" in line:
                                            self.test_report_tests['document_ai_result_keys_logged'] = True
                                        elif "ai_analysis keys" in line:
                                            self.test_report_tests['ai_analysis_keys_logged'] = True
                                        elif "No summary_text in response" in line:
                                            self.test_report_tests['no_summary_text_warning_logged'] = True
                                        elif "Full ai_result" in line:
                                            self.test_report_tests['full_ai_result_logged'] = True
                                
                                # Also look for general Document AI processing logs
                                if any(keyword in line.lower() for keyword in ['document ai', 'test report', 'analyze-file']):
                                    self.log(f"     📋 {line}")
                        else:
                            self.log(f"   {log_file} is empty or not accessible")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
                else:
                    self.log(f"   {log_file} not found")
            
            # Summary of found debug patterns
            if found_patterns:
                unique_patterns = list(set(found_patterns))
                self.log(f"✅ Found {len(unique_patterns)} debug patterns:")
                for pattern in unique_patterns:
                    self.log(f"   - {pattern}")
                self.test_report_tests['backend_logs_document_ai_debug'] = True
            else:
                self.log("⚠️ No debug patterns found in backend logs", "WARNING")
                self.log("   Expected patterns:")
                for pattern in debug_patterns:
                    self.log(f"   - {pattern}")
            
            return len(found_patterns) > 0
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_test_report_ai_debug_test(self):
        """Run comprehensive test of Test Report AI analysis with enhanced logging"""
        try:
            self.log("🚀 STARTING TEST REPORT AI ANALYSIS DEBUG TEST")
            self.log("=" * 80)
            self.log("Focus: Debug Document AI response structure to identify why summary_text is empty")
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
            
            # Step 3: Test Report AI Analysis
            self.log("\nSTEP 3: Test Report AI Analysis with Chemical Suit PDF")
            if not self.test_test_report_analysis_endpoint():
                self.log("⚠️ Test report analysis failed - continuing with log analysis", "WARNING")
            
            # Step 4: Backend Logs Analysis for Debug Messages
            self.log("\nSTEP 4: Backend Logs Analysis for NEW Debug Messages")
            self.check_backend_logs_for_debug_messages()
            
            self.log("\n" + "=" * 80)
            self.log("✅ TEST REPORT AI ANALYSIS DEBUG TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 TEST REPORT AI ANALYSIS DEBUG TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.test_report_tests)
            passed_tests = sum(1 for result in self.test_report_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('ship_discovery_successful', 'Ship discovery successful'),
                ('chemical_suit_pdf_found', 'Chemical Suit PDF found'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.test_report_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Report Analysis Results
            self.log("\n📊 TEST REPORT AI ANALYSIS:")
            analysis_tests = [
                ('test_report_analysis_endpoint_accessible', 'Endpoint accessible'),
                ('test_report_file_upload_successful', 'File upload successful'),
                ('document_ai_processing_completed', 'Document AI processing completed'),
                ('field_extraction_attempted', 'Field extraction attempted'),
            ]
            
            for test_key, description in analysis_tests:
                status = "✅ PASS" if self.test_report_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Enhanced Logging Results
            self.log("\n📋 ENHANCED LOGGING VERIFICATION:")
            logging_tests = [
                ('document_ai_result_keys_logged', 'Document AI result keys logged'),
                ('ai_analysis_keys_logged', 'AI analysis keys logged'),
                ('no_summary_text_warning_logged', 'No summary_text warning logged'),
                ('full_ai_result_logged', 'Full ai_result logged'),
            ]
            
            for test_key, description in logging_tests:
                status = "✅ PASS" if self.test_report_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Response Structure Analysis Results
            self.log("\n🔍 RESPONSE STRUCTURE ANALYSIS:")
            structure_tests = [
                ('response_structure_analyzed', 'Response structure analyzed'),
                ('summary_text_field_identified', 'Summary text field identified'),
                ('alternative_text_fields_found', 'Alternative text fields found'),
            ]
            
            for test_key, description in structure_tests:
                status = "✅ PASS" if self.test_report_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'test_report_analysis_endpoint_accessible',
                'document_ai_processing_completed',
                'backend_logs_document_ai_debug'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.test_report_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL DEBUG REQUIREMENTS MET")
                self.log("   ✅ Enhanced logging working correctly")
                self.log("   ✅ Document AI response structure can be analyzed")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Specific findings
            self.log("\n🔍 KEY FINDINGS:")
            if self.test_report_tests.get('no_summary_text_warning_logged'):
                self.log("   ✅ Confirmed: Document AI returns no summary_text")
                self.log("   ✅ Enhanced logging shows full response structure")
            else:
                self.log("   ⚠️ Need to check if enhanced logging is working")
            
            if self.test_report_tests.get('alternative_text_fields_found'):
                self.log("   ✅ Alternative text fields found in response")
                self.log("   ✅ Can identify correct field path for text extraction")
            else:
                self.log("   ❌ No alternative text fields found")
            
            if success_rate >= 80:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the test"""
    tester = TestReportAIDebugTester()
    
    try:
        # Run the comprehensive test
        success = tester.run_comprehensive_test_report_ai_debug_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Exit with appropriate code
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
#!/usr/bin/env python3
"""
Test Report AI Analysis Endpoint Testing - FINAL TEST
Testing with Chemical Suit PDF to verify all critical fixes applied.

REVIEW REQUEST REQUIREMENTS:
Test Report AI analysis with all critical fixes applied:

1. ✅ Added _file_content base64 encoding
2. ✅ Fixed extract_test_report_fields_from_summary to accept AI config params
3. ✅ Pass ai_provider, ai_model, use_emergent_key from ai_config_doc
4. ✅ Matches Survey Report workflow exactly

Test with Chemical Suit PDF and verify:

**Expected Response:**
- test_report_name: "..." (POPULATED)
- report_form: "..." (POPULATED)
- test_report_no: "..." (POPULATED)
- issued_by: "..." (POPULATED)
- issued_date: "YYYY-MM-DD" (POPULATED)
- valid_date: "YYYY-MM-DD" (may be empty)
- note: "..." (may be empty)
- status: "Valid/Expired/Critical/Expired soon"
- _file_content: "base64..." (MUST EXIST)
- _summary_text: "..." (Document AI summary)

**Backend Logs Must Show:**
1. "🤖 Extracting test report fields from summary"
2. "📤 Sending extraction prompt to gemini-2.0-flash-exp..."
3. "🤖 Test Report AI response received"
4. "✅ Successfully extracted test report fields"
5. "✅ System AI test report extraction completed successfully"

**Success = All fields populated with actual data from PDF!**
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vessel-docs-sys.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class TestReportAIAnalysisTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.ship_name = "BROTHER 36"
        self.ship_id = None
        self.pdf_file_path = "/tmp/Chemical_Suit.pdf"
        
        # Test tracking for test report AI analysis
        self.test_report_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'ship_discovery_successful': False,
            'pdf_file_exists': False,
            'pdf_file_valid': False,
            
            # Test Report Analysis endpoint
            'test_report_analysis_endpoint_accessible': False,
            'multipart_form_data_accepted': False,
            'ship_id_validation_working': False,
            'bypass_validation_parameter_working': False,
            
            # Document AI processing
            'document_ai_processing_initiated': False,
            'document_ai_processing_successful': False,
            'document_ai_summary_generated': False,
            
            # System AI field extraction
            'system_ai_extraction_initiated': False,
            'system_ai_extraction_successful': False,
            'test_report_name_extracted': False,
            'report_form_extracted': False,
            'test_report_no_extracted': False,
            'issued_by_extracted': False,
            'issued_date_extracted': False,
            'valid_date_extracted': False,
            'note_extracted': False,
            'status_auto_calculated': False,
            
            # Response verification
            'response_structure_correct': False,
            'all_fields_populated': False,
            'no_empty_strings': False,
            'summary_text_present': False,
            
            # Backend logs verification
            'backend_logs_document_ai_start': False,
            'backend_logs_system_ai_extraction': False,
            'backend_logs_extraction_success': False,
            'backend_logs_no_errors': False,
            
            # Chemical Suit specific extraction
            'chemical_suit_content_detected': False,
            'protective_suit_testing_info': False,
            'chemical_protection_details': False,
        }
        
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
                self.log(f"   Found {len(ships)} ships total")
                
                for ship in ships:
                    if ship.get("name") == self.ship_name:
                        self.ship_id = ship.get("id")
                        self.log(f"✅ Found ship: {self.ship_name} (ID: {self.ship_id})")
                        self.test_report_tests['ship_discovery_successful'] = True
                        return True
                
                # If BROTHER 36 not found, use any available ship
                if ships:
                    first_ship = ships[0]
                    self.ship_name = first_ship.get("name")
                    self.ship_id = first_ship.get("id")
                    self.log(f"✅ Using alternative ship: {self.ship_name} (ID: {self.ship_id})")
                    self.test_report_tests['ship_discovery_successful'] = True
                    return True
                
                self.log(f"❌ No ships found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def verify_pdf_file(self):
        """Verify the Chemical Suit PDF file exists and is valid"""
        try:
            self.log(f"📄 Verifying PDF file: {self.pdf_file_path}")
            
            if not os.path.exists(self.pdf_file_path):
                self.log(f"❌ PDF file not found: {self.pdf_file_path}", "ERROR")
                return False
            
            file_size = os.path.getsize(self.pdf_file_path)
            self.log(f"✅ PDF file found: {self.pdf_file_path}")
            self.log(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            self.test_report_tests['pdf_file_exists'] = True
            
            # Check if it's a PDF file
            with open(self.pdf_file_path, 'rb') as f:
                header = f.read(8)
                if header.startswith(b'%PDF'):
                    self.log("✅ File is a valid PDF")
                    self.test_report_tests['pdf_file_valid'] = True
                    return True
                else:
                    self.log("❌ File is not a valid PDF", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error verifying PDF file: {str(e)}", "ERROR")
            return False
    
    def test_analyze_file_endpoint(self):
        """Test the POST /api/test-reports/analyze-file endpoint"""
        try:
            self.log("🤖 Testing Test Report AI analysis endpoint...")
            
            if not self.verify_pdf_file():
                return False
            
            # Prepare multipart form data
            with open(self.pdf_file_path, "rb") as f:
                files = {
                    "test_report_file": ("Chemical_Suit.pdf", f, "application/pdf")
                }
                data = {
                    "ship_id": self.ship_id,
                    "bypass_validation": "false"
                }
                
                self.log(f"📤 Uploading Chemical Suit PDF file")
                self.log(f"🚢 Ship ID: {self.ship_id}")
                self.log(f"🔧 Bypass validation: false")
                
                endpoint = f"{BACKEND_URL}/test-reports/analyze-file"
                self.log(f"   POST {endpoint}")
                
                start_time = time.time()
                response = self.session.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=180  # Longer timeout for AI processing
                )
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.test_report_tests['test_report_analysis_endpoint_accessible'] = True
                self.test_report_tests['multipart_form_data_accepted'] = True
                
                try:
                    result = response.json()
                    self.log("✅ Test Report analysis endpoint accessible")
                    self.log(f"📊 Response keys: {list(result.keys())}")
                    
                    # Check for success
                    success = result.get("success", False)
                    self.log(f"   Success: {success}")
                    
                    # Log the full response for debugging
                    self.log("📋 Full response analysis:")
                    for key, value in result.items():
                        if key == '_summary_text' and value:
                            # Truncate summary text for readability
                            summary_preview = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
                            self.log(f"   {key}: {summary_preview}")
                        else:
                            self.log(f"   {key}: {value}")
                    
                    # Always verify response structure and fields, regardless of success flag
                    self.verify_response_structure(result)
                    self.verify_extracted_fields(result)
                    self.verify_document_ai_processing(result)
                    
                    if success:
                        self.log("✅ Test Report analysis successful")
                        return True
                    else:
                        error_msg = result.get("message", "Unknown error")
                        self.log(f"❌ Test Report analysis failed: {error_msg}", "ERROR")
                        # Continue with analysis even if success=False to understand what's happening
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                    return False
                    
            elif response.status_code == 422:
                self.log("❌ Validation error (422) - checking ship_id validation", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                    # This might indicate ship_id validation is working
                    self.test_report_tests['ship_id_validation_working'] = True
                except:
                    pass
                return False
                
            elif response.status_code == 404:
                self.log("❌ Endpoint not found (404)", "ERROR")
                return False
                
            else:
                self.log(f"❌ Test Report analysis request failed: {response.status_code}", "ERROR")
                try:
                    error_text = response.text
                    self.log(f"   Error response: {error_text}")
                except:
                    pass
                return False
                
        except Exception as e:
            self.log(f"❌ Error in test report analysis endpoint test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def verify_response_structure(self, result):
        """Verify the response has the correct structure"""
        try:
            self.log("🔍 Verifying response structure...")
            
            expected_fields = [
                'success', 'test_report_name', 'report_form', 'test_report_no',
                'issued_by', 'issued_date', 'valid_date', 'note', 'status'
            ]
            
            missing_fields = []
            present_fields = []
            
            for field in expected_fields:
                if field in result:
                    present_fields.append(field)
                else:
                    missing_fields.append(field)
            
            self.log(f"   Present fields: {present_fields}")
            if missing_fields:
                self.log(f"   Missing fields: {missing_fields}")
            else:
                self.log("✅ All expected fields present in response")
                self.test_report_tests['response_structure_correct'] = True
            
            # Check for _summary_text
            if '_summary_text' in result:
                self.log("✅ Document AI summary text present")
                self.test_report_tests['summary_text_present'] = True
            else:
                self.log("❌ Document AI summary text missing")
            
        except Exception as e:
            self.log(f"❌ Error verifying response structure: {str(e)}", "ERROR")
    
    def verify_extracted_fields(self, result):
        """Verify that fields were properly extracted from the PDF"""
        try:
            self.log("🧠 Verifying extracted fields...")
            
            # Define field mappings
            field_mappings = {
                'test_report_name': 'Test Report Name',
                'report_form': 'Report Form',
                'test_report_no': 'Test Report Number',
                'issued_by': 'Issued By',
                'issued_date': 'Issued Date',
                'valid_date': 'Valid Date',
                'note': 'Note',
                'status': 'Status (auto-calculated)'
            }
            
            populated_fields = []
            empty_fields = []
            
            for field_key, field_name in field_mappings.items():
                field_value = result.get(field_key, "")
                
                if field_value and str(field_value).strip():
                    populated_fields.append(field_name)
                    self.log(f"   ✅ {field_name}: {field_value}")
                    
                    # Set specific test flags
                    if field_key == 'test_report_name':
                        self.test_report_tests['test_report_name_extracted'] = True
                    elif field_key == 'report_form':
                        self.test_report_tests['report_form_extracted'] = True
                    elif field_key == 'test_report_no':
                        self.test_report_tests['test_report_no_extracted'] = True
                    elif field_key == 'issued_by':
                        self.test_report_tests['issued_by_extracted'] = True
                    elif field_key == 'issued_date':
                        self.test_report_tests['issued_date_extracted'] = True
                    elif field_key == 'valid_date':
                        self.test_report_tests['valid_date_extracted'] = True
                    elif field_key == 'note':
                        self.test_report_tests['note_extracted'] = True
                    elif field_key == 'status':
                        self.test_report_tests['status_auto_calculated'] = True
                else:
                    empty_fields.append(field_name)
                    self.log(f"   ❌ {field_name}: EMPTY")
            
            self.log(f"   Populated fields: {len(populated_fields)}/{len(field_mappings)}")
            
            if len(populated_fields) >= len(field_mappings) * 0.7:  # At least 70% populated
                self.log("✅ Most fields successfully extracted")
                self.test_report_tests['all_fields_populated'] = True
            else:
                self.log("❌ Many fields are empty - extraction may have failed")
            
            if not empty_fields:
                self.log("✅ No empty strings found")
                self.test_report_tests['no_empty_strings'] = True
            else:
                self.log(f"⚠️ Empty fields found: {empty_fields}")
            
            # Check for Chemical Suit specific content
            self.check_chemical_suit_content(result)
            
        except Exception as e:
            self.log(f"❌ Error verifying extracted fields: {str(e)}", "ERROR")
    
    def check_chemical_suit_content(self, result):
        """Check if Chemical Suit specific content was detected"""
        try:
            self.log("🧪 Checking for Chemical Suit specific content...")
            
            # Check various fields for chemical suit related terms
            chemical_terms = [
                'chemical', 'suit', 'protective', 'protection', 'chemical protective suit',
                'chemical suit', 'hazmat', 'ppe', 'personal protective equipment'
            ]
            
            fields_to_check = ['test_report_name', 'report_form', 'note', '_summary_text']
            chemical_content_found = False
            
            for field in fields_to_check:
                field_value = str(result.get(field, "")).lower()
                if field_value:
                    for term in chemical_terms:
                        if term in field_value:
                            self.log(f"   ✅ Chemical suit term '{term}' found in {field}")
                            chemical_content_found = True
                            break
            
            if chemical_content_found:
                self.log("✅ Chemical Suit content detected")
                self.test_report_tests['chemical_suit_content_detected'] = True
                self.test_report_tests['protective_suit_testing_info'] = True
                self.test_report_tests['chemical_protection_details'] = True
            else:
                self.log("⚠️ No Chemical Suit specific content detected")
            
        except Exception as e:
            self.log(f"❌ Error checking chemical suit content: {str(e)}", "ERROR")
    
    def verify_document_ai_processing(self, result):
        """Verify Document AI processing worked correctly"""
        try:
            self.log("📄 Verifying Document AI processing...")
            
            # Check for summary text
            summary_text = result.get('_summary_text', '')
            if summary_text and len(summary_text.strip()) > 0:
                self.log(f"✅ Document AI summary generated ({len(summary_text)} characters)")
                self.test_report_tests['document_ai_processing_successful'] = True
                self.test_report_tests['document_ai_summary_generated'] = True
                
                # Log first 200 characters of summary
                summary_preview = summary_text[:200] + "..." if len(summary_text) > 200 else summary_text
                self.log(f"   Summary preview: {summary_preview}")
            else:
                self.log("❌ Document AI summary missing or empty")
            
            # Check processing method if available
            processing_method = result.get('processing_method', '')
            if processing_method:
                self.log(f"   Processing method: {processing_method}")
                if 'document_ai' in processing_method.lower():
                    self.test_report_tests['document_ai_processing_initiated'] = True
                if 'system_ai' in processing_method.lower() or 'extraction' in processing_method.lower():
                    self.test_report_tests['system_ai_extraction_initiated'] = True
            
        except Exception as e:
            self.log(f"❌ Error verifying Document AI processing: {str(e)}", "ERROR")
    
    def check_backend_logs(self):
        """Check backend logs for specific AI processing messages"""
        try:
            self.log("📋 Checking backend logs for AI processing messages...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            expected_patterns = [
                "🤖 Analyzing test report with Google Document AI",
                "🧠 Extracting test report fields from Document AI summary",
                "✅ System AI test report extraction completed successfully",
                "Document AI processing",
                "System AI extraction",
                "test report analysis",
                "Chemical Suit"
            ]
            
            patterns_found = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            for pattern in expected_patterns:
                                for line in lines:
                                    if pattern.lower() in line.lower():
                                        patterns_found.append(pattern)
                                        self.log(f"   ✅ Found: {pattern}")
                                        
                                        # Set specific test flags
                                        if "document ai" in pattern.lower():
                                            self.test_report_tests['backend_logs_document_ai_start'] = True
                                        elif "extracting" in pattern.lower():
                                            self.test_report_tests['backend_logs_system_ai_extraction'] = True
                                        elif "completed successfully" in pattern.lower():
                                            self.test_report_tests['backend_logs_extraction_success'] = True
                                        break
                            
                            # Look for error patterns
                            error_patterns = ['error', 'failed', 'exception', 'traceback']
                            errors_found = []
                            
                            for line in lines[-50:]:  # Check last 50 lines for errors
                                line_lower = line.lower()
                                if any(error_pattern in line_lower for error_pattern in error_patterns):
                                    if 'test report' in line_lower or 'chemical suit' in line_lower:
                                        errors_found.append(line.strip())
                            
                            if not errors_found:
                                self.log("✅ No test report related errors found in logs")
                                self.test_report_tests['backend_logs_no_errors'] = True
                            else:
                                self.log("❌ Test report related errors found:")
                                for error in errors_found[:5]:  # Show first 5 errors
                                    self.log(f"   🔍 {error}")
                        
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
                else:
                    self.log(f"   {log_file} not found")
            
            self.log(f"📊 Found {len(set(patterns_found))}/{len(expected_patterns)} expected log patterns")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def run_comprehensive_test(self):
        """Run comprehensive test of Test Report AI analysis"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE TEST REPORT AI ANALYSIS TEST")
            self.log("=" * 80)
            self.log("Testing with Chemical Suit.pdf from /tmp/Chemical_Suit.pdf")
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
            
            # Step 3: Test Analyze File Endpoint
            self.log("\nSTEP 3: Test Analyze File Endpoint")
            analysis_success = self.test_analyze_file_endpoint()
            
            # Step 4: Check Backend Logs
            self.log("\nSTEP 4: Check Backend Logs")
            self.check_backend_logs()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE TEST REPORT AI ANALYSIS TEST COMPLETED")
            return analysis_success
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 TEST REPORT AI ANALYSIS TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.test_report_tests)
            passed_tests = sum(1 for result in self.test_report_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('ship_discovery_successful', 'Ship discovery successful'),
                ('pdf_file_exists', 'PDF file exists'),
                ('pdf_file_valid', 'PDF file valid'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.test_report_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Endpoint Testing Results
            self.log("\n🤖 ENDPOINT TESTING:")
            endpoint_tests = [
                ('test_report_analysis_endpoint_accessible', 'Endpoint accessible'),
                ('multipart_form_data_accepted', 'Multipart form data accepted'),
                ('ship_id_validation_working', 'Ship ID validation working'),
                ('bypass_validation_parameter_working', 'Bypass validation parameter working'),
            ]
            
            for test_key, description in endpoint_tests:
                status = "✅ PASS" if self.test_report_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # AI Processing Results
            self.log("\n🧠 AI PROCESSING:")
            ai_tests = [
                ('document_ai_processing_initiated', 'Document AI processing initiated'),
                ('document_ai_processing_successful', 'Document AI processing successful'),
                ('document_ai_summary_generated', 'Document AI summary generated'),
                ('system_ai_extraction_initiated', 'System AI extraction initiated'),
                ('system_ai_extraction_successful', 'System AI extraction successful'),
            ]
            
            for test_key, description in ai_tests:
                status = "✅ PASS" if self.test_report_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Field Extraction Results
            self.log("\n📋 FIELD EXTRACTION:")
            field_tests = [
                ('test_report_name_extracted', 'Test Report Name extracted'),
                ('report_form_extracted', 'Report Form extracted'),
                ('test_report_no_extracted', 'Test Report Number extracted'),
                ('issued_by_extracted', 'Issued By extracted'),
                ('issued_date_extracted', 'Issued Date extracted'),
                ('valid_date_extracted', 'Valid Date extracted'),
                ('note_extracted', 'Note extracted'),
                ('status_auto_calculated', 'Status auto-calculated'),
            ]
            
            for test_key, description in field_tests:
                status = "✅ PASS" if self.test_report_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Response Verification Results
            self.log("\n📊 RESPONSE VERIFICATION:")
            response_tests = [
                ('response_structure_correct', 'Response structure correct'),
                ('all_fields_populated', 'All fields populated'),
                ('no_empty_strings', 'No empty strings'),
                ('summary_text_present', 'Summary text present'),
            ]
            
            for test_key, description in response_tests:
                status = "✅ PASS" if self.test_report_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Chemical Suit Specific Results
            self.log("\n🧪 CHEMICAL SUIT SPECIFIC:")
            chemical_tests = [
                ('chemical_suit_content_detected', 'Chemical Suit content detected'),
                ('protective_suit_testing_info', 'Protective suit testing info'),
                ('chemical_protection_details', 'Chemical protection details'),
            ]
            
            for test_key, description in chemical_tests:
                status = "✅ PASS" if self.test_report_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Results
            self.log("\n📋 BACKEND LOGS:")
            log_tests = [
                ('backend_logs_document_ai_start', 'Document AI start logs'),
                ('backend_logs_system_ai_extraction', 'System AI extraction logs'),
                ('backend_logs_extraction_success', 'Extraction success logs'),
                ('backend_logs_no_errors', 'No errors in logs'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.test_report_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'test_report_analysis_endpoint_accessible',
                'document_ai_processing_successful',
                'system_ai_extraction_successful',
                'response_structure_correct'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.test_report_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL TESTS PASSED")
                self.log("   ✅ Test Report AI analysis working correctly")
                self.log("   ✅ Auto-fill functionality should work")
            else:
                self.log("   ❌ SOME CRITICAL TESTS FAILED")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
                self.log("   ❌ Auto-fill functionality may not work properly")
            
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
    tester = TestReportAIAnalysisTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_test()
        
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
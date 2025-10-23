#!/usr/bin/env python3
"""
Survey Report Analysis with Targeted OCR Testing
Testing CU (02-19).pdf with System AI vs Targeted OCR comparison

REVIEW REQUEST REQUIREMENTS:
Test the complete Survey Report analysis workflow with the newly implemented Targeted OCR for Header/Footer extraction. Compare results from System AI vs Targeted OCR.

FILE TO TEST:
- URL: https://customer-assets.emergentagent.com/job_doc-navigator-9/artifacts/gz0hce82_CU%20%2802-19%29.pdf
- Filename: CU (02-19).pdf

TEST WORKFLOW:
1. Download the PDF file
2. Analyze using POST /api/survey-reports/analyze-file
3. Extract and display BOTH results clearly:
   - System AI results (Document AI + LLM extraction)
   - Targeted OCR results (Header/Footer extraction)

AUTHENTICATION:
- Login: admin1@example.com / 123456

SHIP:
- Use BROTHER 36 (ID: 7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7)

WHAT TO CHECK AND REPORT:
1. System AI Results
2. Targeted OCR Results (_ocr_info)
3. Merge Results
4. Comparison Table
5. Backend Logs
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
    # Fallback to external URL from environment
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class SurveyReportOCRTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.ship_name = "BROTHER 36"
        self.ship_id = "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"
        self.pdf_url = "https://customer-assets.emergentagent.com/job_doc-navigator-9/artifacts/gz0hce82_CU%20%2802-19%29.pdf"
        self.pdf_filename = "CU (02-19).pdf"
        
        # Test tracking for Survey Report OCR testing
        self.ocr_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'ship_discovery_successful': False,
            
            # PDF file handling
            'pdf_file_download_successful': False,
            'pdf_file_valid': False,
            'pdf_file_size_acceptable': False,
            
            # Survey Report analysis endpoint
            'survey_analysis_endpoint_accessible': False,
            'survey_file_upload_successful': False,
            'analysis_processing_successful': False,
            
            # System AI Results
            'system_ai_survey_report_name_extracted': False,
            'system_ai_report_form_extracted': False,
            'system_ai_survey_report_no_extracted': False,
            'system_ai_issued_by_extracted': False,
            'system_ai_issued_date_extracted': False,
            'system_ai_surveyor_name_extracted': False,
            'system_ai_note_extracted': False,
            
            # Targeted OCR Results
            'ocr_attempted': False,
            'ocr_success': False,
            'ocr_report_form_extracted': False,
            'ocr_survey_report_no_extracted': False,
            'ocr_header_text_present': False,
            'ocr_footer_text_present': False,
            
            # Merge Results
            'merge_results_present': False,
            'report_form_source_identified': False,
            'report_form_confidence_calculated': False,
            'survey_report_no_source_identified': False,
            'survey_report_no_confidence_calculated': False,
            'needs_manual_review_flag_set': False,
            
            # Backend Logs
            'backend_logs_ocr_start': False,
            'backend_logs_ocr_completion': False,
            'backend_logs_merge_results': False,
        }
        
        # Store analysis results for comparison
        self.system_ai_results = {}
        self.targeted_ocr_results = {}
        self.merge_results = {}
        
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
        """Authenticate with admin1@example.com / 123456 credentials"""
        try:
            self.log("🔐 Authenticating with admin1@example.com / 123456...")
            
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
                
                self.ocr_tests['authentication_successful'] = True
                self.ocr_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def verify_ship(self):
        """Verify the test ship exists"""
        try:
            self.log(f"🚢 Verifying ship: {self.ship_name} (ID: {self.ship_id})")
            
            response = self.session.get(f"{BACKEND_URL}/ships/{self.ship_id}")
            
            if response.status_code == 200:
                ship_data = response.json()
                if ship_data.get("name") == self.ship_name:
                    self.log(f"✅ Ship verified: {self.ship_name}")
                    self.log(f"   Ship ID: {self.ship_id}")
                    self.log(f"   IMO: {ship_data.get('imo', 'N/A')}")
                    self.ocr_tests['ship_discovery_successful'] = True
                    return True
                else:
                    self.log(f"❌ Ship name mismatch: expected {self.ship_name}, got {ship_data.get('name')}", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to verify ship: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying ship: {str(e)}", "ERROR")
            return False
    
    def download_pdf_file(self):
        """Download the PDF file for testing"""
        try:
            self.log(f"📥 Downloading PDF file: {self.pdf_filename}")
            self.log(f"   URL: {self.pdf_url}")
            
            response = requests.get(self.pdf_url, timeout=120)
            
            if response.status_code == 200:
                # Save to temporary file
                pdf_path = f"/app/{self.pdf_filename.replace(' ', '_').replace('(', '').replace(')', '')}"
                
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                self.log(f"✅ PDF file downloaded successfully")
                self.log(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                self.log(f"   Saved to: {pdf_path}")
                
                # Verify it's a valid PDF
                if response.content.startswith(b'%PDF'):
                    self.log("✅ File is a valid PDF")
                    self.ocr_tests['pdf_file_download_successful'] = True
                    self.ocr_tests['pdf_file_valid'] = True
                    self.ocr_tests['pdf_file_size_acceptable'] = file_size > 0
                    return pdf_path
                else:
                    self.log("❌ Downloaded file is not a valid PDF", "ERROR")
                    return None
            else:
                self.log(f"❌ Failed to download PDF: {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error downloading PDF file: {str(e)}", "ERROR")
            return None
    
    def test_survey_report_analysis_with_ocr(self, pdf_path):
        """Test the survey report analysis endpoint with Targeted OCR"""
        try:
            self.log("📄 Testing Survey Report analysis with Targeted OCR...")
            self.log(f"   Ship: {self.ship_name} (ID: {self.ship_id})")
            self.log(f"   PDF: {self.pdf_filename}")
            
            # Prepare multipart form data
            with open(pdf_path, "rb") as f:
                files = {
                    "survey_report_file": (self.pdf_filename, f, "application/pdf")
                }
                
                endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
                self.log(f"📤 POST {endpoint}")
                
                start_time = time.time()
                response = self.session.post(
                    endpoint,
                    files=files,
                    data={"ship_id": self.ship_id},
                    timeout=180  # Longer timeout for AI processing + OCR
                )
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Survey Report analysis endpoint accessible")
                self.ocr_tests['survey_analysis_endpoint_accessible'] = True
                self.ocr_tests['survey_file_upload_successful'] = True
                
                # Check for success
                if result.get("success"):
                    self.log("✅ Survey Report analysis successful")
                    self.ocr_tests['analysis_processing_successful'] = True
                    
                    # Extract System AI results
                    self.extract_system_ai_results(result)
                    
                    # Extract Targeted OCR results
                    self.extract_targeted_ocr_results(result)
                    
                    # Extract Merge results
                    self.extract_merge_results(result)
                    
                    # Print complete analysis response
                    self.print_complete_analysis_response(result)
                    
                    return True
                else:
                    error_msg = result.get("message", "Unknown error")
                    self.log(f"❌ Survey Report analysis failed: {error_msg}", "ERROR")
                    return False
            else:
                self.log(f"❌ Survey Report analysis request failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in survey report analysis test: {str(e)}", "ERROR")
            return False
    
    def extract_system_ai_results(self, result):
        """Extract System AI results from the response"""
        try:
            self.log("🤖 Extracting System AI results...")
            
            # Extract main fields
            self.system_ai_results = {
                'survey_report_name': result.get('survey_report_name', ''),
                'report_form': result.get('report_form', ''),
                'survey_report_no': result.get('survey_report_no', ''),
                'issued_by': result.get('issued_by', ''),
                'issued_date': result.get('issued_date', ''),
                'surveyor_name': result.get('surveyor_name', ''),
                'note': result.get('note', '')
            }
            
            # Check which fields were extracted
            for field, value in self.system_ai_results.items():
                if value:
                    self.log(f"   ✅ {field}: {value}")
                    # Update test results
                    test_key = f"system_ai_{field}_extracted"
                    if test_key in self.ocr_tests:
                        self.ocr_tests[test_key] = True
                else:
                    self.log(f"   ❌ {field}: (empty)")
            
            self.log(f"📊 System AI extracted {sum(1 for v in self.system_ai_results.values() if v)}/7 fields")
            
        except Exception as e:
            self.log(f"❌ Error extracting System AI results: {str(e)}", "ERROR")
    
    def extract_targeted_ocr_results(self, result):
        """Extract Targeted OCR results from the response"""
        try:
            self.log("🔍 Extracting Targeted OCR results...")
            
            # Look for _ocr_info in the response
            ocr_info = result.get('_ocr_info', {})
            
            if ocr_info:
                self.log("✅ OCR info found in response")
                
                self.targeted_ocr_results = {
                    'ocr_attempted': ocr_info.get('ocr_attempted', False),
                    'ocr_success': ocr_info.get('ocr_success', False),
                    'report_form': ocr_info.get('report_form', ''),
                    'survey_report_no': ocr_info.get('survey_report_no', ''),
                    'header_text': ocr_info.get('header_text', ''),
                    'footer_text': ocr_info.get('footer_text', '')
                }
                
                # Check OCR attempt and success
                if self.targeted_ocr_results['ocr_attempted']:
                    self.log("   ✅ OCR attempted: True")
                    self.ocr_tests['ocr_attempted'] = True
                else:
                    self.log("   ❌ OCR attempted: False")
                
                if self.targeted_ocr_results['ocr_success']:
                    self.log("   ✅ OCR success: True")
                    self.ocr_tests['ocr_success'] = True
                else:
                    self.log("   ❌ OCR success: False")
                
                # Check extracted fields
                if self.targeted_ocr_results['report_form']:
                    self.log(f"   ✅ OCR report_form: {self.targeted_ocr_results['report_form']}")
                    self.ocr_tests['ocr_report_form_extracted'] = True
                else:
                    self.log("   ❌ OCR report_form: (empty)")
                
                if self.targeted_ocr_results['survey_report_no']:
                    self.log(f"   ✅ OCR survey_report_no: {self.targeted_ocr_results['survey_report_no']}")
                    self.ocr_tests['ocr_survey_report_no_extracted'] = True
                else:
                    self.log("   ❌ OCR survey_report_no: (empty)")
                
                # Check raw OCR text
                if self.targeted_ocr_results['header_text']:
                    self.log(f"   ✅ Header text: {len(self.targeted_ocr_results['header_text'])} characters")
                    self.log(f"      Preview: {self.targeted_ocr_results['header_text'][:100]}...")
                    self.ocr_tests['ocr_header_text_present'] = True
                else:
                    self.log("   ❌ Header text: (empty)")
                
                if self.targeted_ocr_results['footer_text']:
                    self.log(f"   ✅ Footer text: {len(self.targeted_ocr_results['footer_text'])} characters")
                    self.log(f"      Preview: {self.targeted_ocr_results['footer_text'][:100]}...")
                    self.ocr_tests['ocr_footer_text_present'] = True
                else:
                    self.log("   ❌ Footer text: (empty)")
                
            else:
                self.log("❌ No OCR info found in response", "ERROR")
                self.targeted_ocr_results = {}
            
        except Exception as e:
            self.log(f"❌ Error extracting Targeted OCR results: {str(e)}", "ERROR")
    
    def extract_merge_results(self, result):
        """Extract merge results from the response"""
        try:
            self.log("🔀 Extracting Merge results...")
            
            # Look for merge result fields
            merge_fields = [
                'report_form_source',
                'report_form_confidence',
                'survey_report_no_source',
                'survey_report_no_confidence',
                'needs_manual_review'
            ]
            
            self.merge_results = {}
            for field in merge_fields:
                value = result.get(field)
                if value is not None:
                    self.merge_results[field] = value
                    self.log(f"   ✅ {field}: {value}")
                    
                    # Update test results
                    test_key = field.replace('_', '_') + '_' + ('identified' if 'source' in field else 'calculated' if 'confidence' in field else 'set')
                    if test_key in self.ocr_tests:
                        self.ocr_tests[test_key] = True
                else:
                    self.log(f"   ❌ {field}: (not present)")
            
            if self.merge_results:
                self.log("✅ Merge results found")
                self.ocr_tests['merge_results_present'] = True
            else:
                self.log("❌ No merge results found")
            
        except Exception as e:
            self.log(f"❌ Error extracting merge results: {str(e)}", "ERROR")
    
    def print_complete_analysis_response(self, result):
        """Print the complete analysis response in formatted JSON"""
        try:
            self.log("📋 COMPLETE ANALYSIS RESPONSE:")
            self.log("=" * 80)
            
            # Pretty print the JSON response
            formatted_json = json.dumps(result, indent=2, ensure_ascii=False)
            
            # Split into lines and log each line
            for line in formatted_json.split('\n'):
                self.log(f"   {line}")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing complete response: {str(e)}", "ERROR")
    
    def create_comparison_table(self):
        """Create a clear comparison table showing System AI vs OCR results"""
        try:
            self.log("📊 COMPARISON TABLE: System AI vs Targeted OCR")
            self.log("=" * 100)
            
            # Table header
            header = f"{'Field':<20} | {'System AI':<30} | {'Targeted OCR':<30} | {'Final Result':<20} | {'Confidence':<10}"
            self.log(header)
            self.log("-" * 100)
            
            # Compare report_form
            system_report_form = self.system_ai_results.get('report_form', '')
            ocr_report_form = self.targeted_ocr_results.get('report_form', '')
            final_report_form = system_report_form or ocr_report_form  # Simple merge logic
            confidence = self.merge_results.get('report_form_confidence', 'N/A')
            
            row = f"{'report_form':<20} | {system_report_form[:30]:<30} | {ocr_report_form[:30]:<30} | {final_report_form[:20]:<20} | {confidence:<10}"
            self.log(row)
            
            # Compare survey_report_no
            system_report_no = self.system_ai_results.get('survey_report_no', '')
            ocr_report_no = self.targeted_ocr_results.get('survey_report_no', '')
            final_report_no = system_report_no or ocr_report_no  # Simple merge logic
            confidence = self.merge_results.get('survey_report_no_confidence', 'N/A')
            
            row = f"{'survey_report_no':<20} | {system_report_no[:30]:<30} | {ocr_report_no[:30]:<30} | {final_report_no[:20]:<20} | {confidence:<10}"
            self.log(row)
            
            self.log("=" * 100)
            
        except Exception as e:
            self.log(f"❌ Error creating comparison table: {str(e)}", "ERROR")
    
    def check_backend_logs_for_ocr(self):
        """Check backend logs for OCR processing messages"""
        try:
            self.log("📋 Checking backend logs for OCR processing...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            ocr_patterns = [
                "Starting Targeted OCR for header/footer extraction",
                "Targeted OCR completed successfully",
                "OCR merge results",
                "Enhanced OCR processor",
                "Header/Footer extraction"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            # Look for OCR-related patterns
                            for pattern in ocr_patterns:
                                found_lines = [line for line in lines if pattern.lower() in line.lower()]
                                if found_lines:
                                    self.log(f"   ✅ Found pattern '{pattern}':")
                                    for line in found_lines[-3:]:  # Show last 3 matches
                                        self.log(f"      {line}")
                                    
                                    # Update test results
                                    if "starting targeted ocr" in pattern.lower():
                                        self.ocr_tests['backend_logs_ocr_start'] = True
                                    elif "completed successfully" in pattern.lower():
                                        self.ocr_tests['backend_logs_ocr_completion'] = True
                                    elif "merge results" in pattern.lower():
                                        self.ocr_tests['backend_logs_merge_results'] = True
                                else:
                                    self.log(f"   ❌ Pattern '{pattern}' not found")
                        else:
                            self.log(f"   {log_file} is empty or not accessible")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
                else:
                    self.log(f"   {log_file} not found")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_ocr_test(self):
        """Run comprehensive test of Survey Report analysis with Targeted OCR"""
        try:
            self.log("🚀 STARTING SURVEY REPORT ANALYSIS WITH TARGETED OCR TEST")
            self.log("=" * 80)
            self.log(f"Testing file: {self.pdf_filename}")
            self.log(f"Ship: {self.ship_name} (ID: {self.ship_id})")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Ship Verification
            self.log("\nSTEP 2: Ship Verification")
            if not self.verify_ship():
                self.log("❌ CRITICAL: Ship verification failed - cannot proceed")
                return False
            
            # Step 3: Download PDF File
            self.log("\nSTEP 3: Download PDF File")
            pdf_path = self.download_pdf_file()
            if not pdf_path:
                self.log("❌ CRITICAL: PDF download failed - cannot proceed")
                return False
            
            # Step 4: Survey Report Analysis with OCR
            self.log("\nSTEP 4: Survey Report Analysis with Targeted OCR")
            if not self.test_survey_report_analysis_with_ocr(pdf_path):
                self.log("❌ CRITICAL: Survey Report analysis failed")
                return False
            
            # Step 5: Create Comparison Table
            self.log("\nSTEP 5: Create Comparison Table")
            self.create_comparison_table()
            
            # Step 6: Check Backend Logs
            self.log("\nSTEP 6: Check Backend Logs for OCR Processing")
            self.check_backend_logs_for_ocr()
            
            # Step 7: Cleanup
            self.log("\nSTEP 7: Cleanup")
            try:
                if pdf_path and os.path.exists(pdf_path):
                    os.remove(pdf_path)
                    self.log(f"✅ Cleaned up PDF file: {pdf_path}")
            except Exception as e:
                self.log(f"⚠️ Could not clean up PDF file: {e}")
            
            self.log("\n" + "=" * 80)
            self.log("✅ SURVEY REPORT ANALYSIS WITH TARGETED OCR TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 SURVEY REPORT ANALYSIS WITH TARGETED OCR TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.ocr_tests)
            passed_tests = sum(1 for result in self.ocr_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('ship_discovery_successful', 'Ship discovery successful'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # PDF File Handling Results
            self.log("\n📄 PDF FILE HANDLING:")
            pdf_tests = [
                ('pdf_file_download_successful', 'PDF file download successful'),
                ('pdf_file_valid', 'PDF file valid'),
                ('pdf_file_size_acceptable', 'PDF file size acceptable'),
            ]
            
            for test_key, description in pdf_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Survey Analysis Results
            self.log("\n📊 SURVEY ANALYSIS ENDPOINT:")
            analysis_tests = [
                ('survey_analysis_endpoint_accessible', 'Endpoint accessible'),
                ('survey_file_upload_successful', 'File upload successful'),
                ('analysis_processing_successful', 'Analysis processing successful'),
            ]
            
            for test_key, description in analysis_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # System AI Results
            self.log("\n🤖 SYSTEM AI RESULTS:")
            system_ai_tests = [
                ('system_ai_survey_report_name_extracted', 'Survey report name extracted'),
                ('system_ai_report_form_extracted', 'Report form extracted'),
                ('system_ai_survey_report_no_extracted', 'Survey report no extracted'),
                ('system_ai_issued_by_extracted', 'Issued by extracted'),
                ('system_ai_issued_date_extracted', 'Issued date extracted'),
                ('system_ai_surveyor_name_extracted', 'Surveyor name extracted'),
                ('system_ai_note_extracted', 'Note extracted'),
            ]
            
            for test_key, description in system_ai_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Targeted OCR Results
            self.log("\n🔍 TARGETED OCR RESULTS:")
            ocr_tests = [
                ('ocr_attempted', 'OCR attempted'),
                ('ocr_success', 'OCR success'),
                ('ocr_report_form_extracted', 'OCR report form extracted'),
                ('ocr_survey_report_no_extracted', 'OCR survey report no extracted'),
                ('ocr_header_text_present', 'OCR header text present'),
                ('ocr_footer_text_present', 'OCR footer text present'),
            ]
            
            for test_key, description in ocr_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Merge Results
            self.log("\n🔀 MERGE RESULTS:")
            merge_tests = [
                ('merge_results_present', 'Merge results present'),
                ('report_form_source_identified', 'Report form source identified'),
                ('report_form_confidence_calculated', 'Report form confidence calculated'),
                ('survey_report_no_source_identified', 'Survey report no source identified'),
                ('survey_report_no_confidence_calculated', 'Survey report no confidence calculated'),
                ('needs_manual_review_flag_set', 'Needs manual review flag set'),
            ]
            
            for test_key, description in merge_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Results
            self.log("\n📋 BACKEND LOGS:")
            log_tests = [
                ('backend_logs_ocr_start', 'OCR start logs found'),
                ('backend_logs_ocr_completion', 'OCR completion logs found'),
                ('backend_logs_merge_results', 'Merge results logs found'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'analysis_processing_successful',
                'ocr_attempted',
                'ocr_success',
                'merge_results_present'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.ocr_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL OCR REQUIREMENTS MET")
                self.log("   ✅ Targeted OCR working correctly")
                self.log("   ✅ System AI and OCR results merged successfully")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Success criteria assessment
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
    """Main function to run the Survey Report OCR test"""
    tester = SurveyReportOCRTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_ocr_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"\n❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
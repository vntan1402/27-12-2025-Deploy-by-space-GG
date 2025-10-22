#!/usr/bin/env python3
"""
Invalid PDF File Handling Test for Survey Report AI Analysis Endpoint

REVIEW REQUEST REQUIREMENTS:
Test the Invalid PDF File Handling fix in the Survey Report AI Analysis endpoint.

The /api/survey-reports/analyze-file endpoint has been enhanced with comprehensive validation 
for invalid/corrupted PDF files. Previously, the endpoint would return 200 OK even for 
corrupted PDFs, allowing them to proceed to Document AI processing which would fail.

TEST CASES:
1. Valid PDF File (should work normally)
2. Empty File (should return 400)
3. Non-PDF File Renamed to .pdf (should return 400)
4. Corrupted PDF File (should return 400)
5. File with Non-PDF Extension (should return 400)

Authentication: admin1/123456
Ship: BROTHER 36 (ID: 7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7)
"""

import requests
import json
import os
import sys
import tempfile
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
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class InvalidPDFHandlingTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.ship_id = "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"  # BROTHER 36
        self.ship_name = "BROTHER 36"
        
        # Test tracking
        self.test_results = {
            # Authentication and setup
            'authentication_successful': False,
            'ship_verification_successful': False,
            'endpoint_accessible': False,
            
            # Test Case 1: Valid PDF File
            'valid_pdf_works_normally': False,
            'valid_pdf_returns_200': False,
            'valid_pdf_analysis_successful': False,
            
            # Test Case 2: Empty File
            'empty_file_returns_400': False,
            'empty_file_correct_error_message': False,
            
            # Test Case 3: Non-PDF File Renamed to .pdf
            'non_pdf_renamed_returns_400': False,
            'non_pdf_renamed_correct_error_message': False,
            
            # Test Case 4: Corrupted PDF File
            'corrupted_pdf_returns_400': False,
            'corrupted_pdf_correct_error_message': False,
            
            # Test Case 5: File with Non-PDF Extension
            'non_pdf_extension_returns_400': False,
            'non_pdf_extension_correct_error_message': False,
            
            # Validation order verification
            'validation_before_document_ai': False,
            'early_error_detection': False,
            'proper_error_responses': False,
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
                self.log(f"   User: {self.current_user.get('username')}")
                self.log(f"   Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.test_results['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def verify_ship(self):
        """Verify the test ship exists and is accessible"""
        try:
            self.log(f"🚢 Verifying ship: {self.ship_name} (ID: {self.ship_id})")
            
            # Get ships list to verify our test ship exists
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                for ship in ships:
                    if ship.get("id") == self.ship_id and ship.get("name") == self.ship_name:
                        self.log(f"✅ Ship verified: {ship.get('name')} (IMO: {ship.get('imo', 'N/A')})")
                        self.test_results['ship_verification_successful'] = True
                        return True
                
                self.log(f"❌ Ship not found: {self.ship_name}", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying ship: {str(e)}", "ERROR")
            return False
    
    def create_test_files(self):
        """Create test files for different scenarios"""
        try:
            self.log("📁 Creating test files...")
            
            # Create temporary directory for test files
            self.temp_dir = tempfile.mkdtemp()
            self.log(f"   Temp directory: {self.temp_dir}")
            
            # Test Case 1: Valid PDF File (create a minimal valid PDF)
            self.valid_pdf_path = os.path.join(self.temp_dir, "valid_test.pdf")
            valid_pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
            
            with open(self.valid_pdf_path, 'wb') as f:
                f.write(valid_pdf_content)
            self.log(f"   ✅ Created valid PDF: {self.valid_pdf_path}")
            
            # Test Case 2: Empty File
            self.empty_file_path = os.path.join(self.temp_dir, "empty_test.pdf")
            with open(self.empty_file_path, 'wb') as f:
                pass  # Create empty file
            self.log(f"   ✅ Created empty file: {self.empty_file_path}")
            
            # Test Case 3: Non-PDF File Renamed to .pdf
            self.non_pdf_renamed_path = os.path.join(self.temp_dir, "text_file.pdf")
            with open(self.non_pdf_renamed_path, 'w') as f:
                f.write("This is a text file, not a PDF file. It should be rejected.")
            self.log(f"   ✅ Created non-PDF renamed file: {self.non_pdf_renamed_path}")
            
            # Test Case 4: Corrupted PDF File (starts with %PDF but has corrupted content)
            self.corrupted_pdf_path = os.path.join(self.temp_dir, "corrupted_test.pdf")
            corrupted_content = b"%PDF-1.4\nThis is corrupted PDF content that will fail PyPDF2 validation\n"
            with open(self.corrupted_pdf_path, 'wb') as f:
                f.write(corrupted_content)
            self.log(f"   ✅ Created corrupted PDF: {self.corrupted_pdf_path}")
            
            # Test Case 5: File with Non-PDF Extension
            self.non_pdf_extension_path = os.path.join(self.temp_dir, "document.txt")
            with open(self.non_pdf_extension_path, 'w') as f:
                f.write("This is a text document with .txt extension.")
            self.log(f"   ✅ Created non-PDF extension file: {self.non_pdf_extension_path}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating test files: {str(e)}", "ERROR")
            return False
    
    def test_case_1_valid_pdf(self):
        """Test Case 1: Valid PDF File (should work normally)"""
        try:
            self.log("📄 TEST CASE 1: Valid PDF File (should work normally)")
            
            with open(self.valid_pdf_path, "rb") as f:
                files = {
                    "survey_report_file": ("valid_test.pdf", f, "application/pdf")
                }
                data = {
                    "ship_id": self.ship_id
                }
                
                endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
                self.log(f"   POST {endpoint}")
                
                start_time = time.time()
                response = self.session.post(endpoint, files=files, data=data, timeout=120)
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.log(f"   ⏱️ Processing time: {processing_time:.1f} seconds")
                self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.log("   ✅ Valid PDF returns 200 OK as expected")
                self.test_results['valid_pdf_returns_200'] = True
                
                try:
                    result = response.json()
                    if result.get("success"):
                        self.log("   ✅ Valid PDF analysis successful")
                        self.test_results['valid_pdf_analysis_successful'] = True
                        self.test_results['valid_pdf_works_normally'] = True
                    else:
                        self.log("   ⚠️ Valid PDF analysis returned success=false")
                        
                except Exception as e:
                    self.log(f"   ⚠️ Could not parse response JSON: {e}")
                
                return True
            else:
                self.log(f"   ❌ Valid PDF failed with status: {response.status_code}")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Error in Test Case 1: {str(e)}", "ERROR")
            return False
    
    def test_case_2_empty_file(self):
        """Test Case 2: Empty File (should return 400)"""
        try:
            self.log("📄 TEST CASE 2: Empty File (should return 400)")
            
            with open(self.empty_file_path, "rb") as f:
                files = {
                    "survey_report_file": ("empty_test.pdf", f, "application/pdf")
                }
                data = {
                    "ship_id": self.ship_id
                }
                
                endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
                response = self.session.post(endpoint, files=files, data=data, timeout=60)
                
                self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 400:
                self.log("   ✅ Empty file returns 400 Bad Request as expected")
                self.test_results['empty_file_returns_400'] = True
                
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", "")
                    self.log(f"   Error message: {error_message}")
                    
                    expected_message = "Empty file provided. Please upload a valid PDF file."
                    if expected_message in error_message:
                        self.log("   ✅ Correct error message for empty file")
                        self.test_results['empty_file_correct_error_message'] = True
                    else:
                        self.log(f"   ❌ Unexpected error message. Expected: '{expected_message}'")
                        
                except Exception as e:
                    self.log(f"   ⚠️ Could not parse error response: {e}")
                
                return True
            else:
                self.log(f"   ❌ Empty file returned status {response.status_code}, expected 400")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Error in Test Case 2: {str(e)}", "ERROR")
            return False
    
    def test_case_3_non_pdf_renamed(self):
        """Test Case 3: Non-PDF File Renamed to .pdf (should return 400)"""
        try:
            self.log("📄 TEST CASE 3: Non-PDF File Renamed to .pdf (should return 400)")
            
            with open(self.non_pdf_renamed_path, "rb") as f:
                files = {
                    "survey_report_file": ("text_file.pdf", f, "application/pdf")
                }
                data = {
                    "ship_id": self.ship_id
                }
                
                endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
                response = self.session.post(endpoint, files=files, data=data, timeout=60)
                
                self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 400:
                self.log("   ✅ Non-PDF renamed file returns 400 Bad Request as expected")
                self.test_results['non_pdf_renamed_returns_400'] = True
                
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", "")
                    self.log(f"   Error message: {error_message}")
                    
                    expected_message = "Invalid PDF file format. The file does not appear to be a valid PDF document."
                    if expected_message in error_message:
                        self.log("   ✅ Correct error message for non-PDF renamed file")
                        self.test_results['non_pdf_renamed_correct_error_message'] = True
                    else:
                        self.log(f"   ❌ Unexpected error message. Expected: '{expected_message}'")
                        
                except Exception as e:
                    self.log(f"   ⚠️ Could not parse error response: {e}")
                
                return True
            else:
                self.log(f"   ❌ Non-PDF renamed file returned status {response.status_code}, expected 400")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Error in Test Case 3: {str(e)}", "ERROR")
            return False
    
    def test_case_4_corrupted_pdf(self):
        """Test Case 4: Corrupted PDF File (should return 400)"""
        try:
            self.log("📄 TEST CASE 4: Corrupted PDF File (should return 400)")
            
            with open(self.corrupted_pdf_path, "rb") as f:
                files = {
                    "survey_file": ("corrupted_test.pdf", f, "application/pdf")
                }
                data = {
                    "ship_id": self.ship_id
                }
                
                endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
                response = self.session.post(endpoint, files=files, data=data, timeout=60)
                
                self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 400:
                self.log("   ✅ Corrupted PDF returns 400 Bad Request as expected")
                self.test_results['corrupted_pdf_returns_400'] = True
                
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", "")
                    self.log(f"   Error message: {error_message}")
                    
                    expected_message_start = "Invalid or corrupted PDF file:"
                    if error_message.startswith(expected_message_start):
                        self.log("   ✅ Correct error message for corrupted PDF")
                        self.test_results['corrupted_pdf_correct_error_message'] = True
                    else:
                        self.log(f"   ❌ Unexpected error message. Expected to start with: '{expected_message_start}'")
                        
                except Exception as e:
                    self.log(f"   ⚠️ Could not parse error response: {e}")
                
                return True
            else:
                self.log(f"   ❌ Corrupted PDF returned status {response.status_code}, expected 400")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Error in Test Case 4: {str(e)}", "ERROR")
            return False
    
    def test_case_5_non_pdf_extension(self):
        """Test Case 5: File with Non-PDF Extension (should return 400)"""
        try:
            self.log("📄 TEST CASE 5: File with Non-PDF Extension (should return 400)")
            
            with open(self.non_pdf_extension_path, "rb") as f:
                files = {
                    "survey_file": ("document.txt", f, "text/plain")
                }
                data = {
                    "ship_id": self.ship_id
                }
                
                endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
                response = self.session.post(endpoint, files=files, data=data, timeout=60)
                
                self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 400:
                self.log("   ✅ Non-PDF extension file returns 400 Bad Request as expected")
                self.test_results['non_pdf_extension_returns_400'] = True
                
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", "")
                    self.log(f"   Error message: {error_message}")
                    
                    expected_message = "Invalid file type. Only PDF files are supported for survey reports."
                    if expected_message in error_message:
                        self.log("   ✅ Correct error message for non-PDF extension")
                        self.test_results['non_pdf_extension_correct_error_message'] = True
                    else:
                        self.log(f"   ❌ Unexpected error message. Expected: '{expected_message}'")
                        
                except Exception as e:
                    self.log(f"   ⚠️ Could not parse error response: {e}")
                
                return True
            else:
                self.log(f"   ❌ Non-PDF extension file returned status {response.status_code}, expected 400")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Error in Test Case 5: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs(self):
        """Check backend logs for validation patterns"""
        try:
            self.log("📋 Checking backend logs for validation patterns...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            validation_patterns = [
                "Empty file provided",
                "Invalid PDF file format",
                "Invalid or corrupted PDF file",
                "Only PDF files are supported",
                "PDF magic bytes validation",
                "PyPDF2",
                "ValueError"
            ]
            
            found_patterns = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            for pattern in validation_patterns:
                                if pattern.lower() in result.lower():
                                    found_patterns.append(pattern)
                                    self.log(f"   ✅ Found validation pattern: {pattern}")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            if found_patterns:
                self.test_results['validation_before_document_ai'] = True
                self.test_results['early_error_detection'] = True
                self.log("   ✅ Validation patterns found in backend logs")
            else:
                self.log("   ⚠️ No validation patterns found in backend logs")
            
            return len(found_patterns) > 0
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def verify_endpoint_accessibility(self):
        """Verify the survey reports analyze-file endpoint is accessible"""
        try:
            self.log("🔍 Verifying endpoint accessibility...")
            
            # Test with OPTIONS request to check if endpoint exists
            endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
            response = self.session.options(endpoint, timeout=30)
            
            if response.status_code in [200, 405]:  # 405 is also acceptable (Method Not Allowed)
                self.log("   ✅ Survey reports analyze-file endpoint is accessible")
                self.test_results['endpoint_accessible'] = True
                return True
            else:
                self.log(f"   ❌ Endpoint not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying endpoint accessibility: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_files(self):
        """Clean up temporary test files"""
        try:
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                self.log("🧹 Cleaned up temporary test files")
        except Exception as e:
            self.log(f"⚠️ Error cleaning up test files: {e}")
    
    def run_comprehensive_test(self):
        """Run comprehensive test of invalid PDF file handling"""
        try:
            self.log("🚀 STARTING INVALID PDF FILE HANDLING TEST")
            self.log("=" * 80)
            self.log("Testing enhanced validation for Survey Report AI Analysis endpoint")
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
            
            # Step 3: Endpoint Accessibility
            self.log("\nSTEP 3: Endpoint Accessibility")
            if not self.verify_endpoint_accessibility():
                self.log("❌ CRITICAL: Endpoint not accessible - cannot proceed")
                return False
            
            # Step 4: Create Test Files
            self.log("\nSTEP 4: Creating Test Files")
            if not self.create_test_files():
                self.log("❌ CRITICAL: Failed to create test files - cannot proceed")
                return False
            
            # Step 5: Run Test Cases
            self.log("\nSTEP 5: Running Test Cases")
            
            # Test Case 1: Valid PDF File
            self.test_case_1_valid_pdf()
            
            # Test Case 2: Empty File
            self.test_case_2_empty_file()
            
            # Test Case 3: Non-PDF File Renamed to .pdf
            self.test_case_3_non_pdf_renamed()
            
            # Test Case 4: Corrupted PDF File
            self.test_case_4_corrupted_pdf()
            
            # Test Case 5: File with Non-PDF Extension
            self.test_case_5_non_pdf_extension()
            
            # Step 6: Backend Logs Analysis
            self.log("\nSTEP 6: Backend Logs Analysis")
            self.check_backend_logs()
            
            # Step 7: Cleanup
            self.log("\nSTEP 7: Cleanup")
            self.cleanup_test_files()
            
            self.log("\n" + "=" * 80)
            self.log("✅ INVALID PDF FILE HANDLING TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 INVALID PDF FILE HANDLING TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            setup_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('ship_verification_successful', 'Ship verification successful'),
                ('endpoint_accessible', 'Endpoint accessible'),
            ]
            
            for test_key, description in setup_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Case Results
            self.log("\n📄 TEST CASE RESULTS:")
            
            # Test Case 1: Valid PDF
            self.log("   TEST CASE 1: Valid PDF File")
            valid_pdf_tests = [
                ('valid_pdf_returns_200', 'Returns 200 OK'),
                ('valid_pdf_analysis_successful', 'Analysis successful'),
                ('valid_pdf_works_normally', 'Works normally'),
            ]
            
            for test_key, description in valid_pdf_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"      {status} - {description}")
            
            # Test Case 2: Empty File
            self.log("   TEST CASE 2: Empty File")
            empty_file_tests = [
                ('empty_file_returns_400', 'Returns 400 Bad Request'),
                ('empty_file_correct_error_message', 'Correct error message'),
            ]
            
            for test_key, description in empty_file_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"      {status} - {description}")
            
            # Test Case 3: Non-PDF Renamed
            self.log("   TEST CASE 3: Non-PDF File Renamed to .pdf")
            non_pdf_renamed_tests = [
                ('non_pdf_renamed_returns_400', 'Returns 400 Bad Request'),
                ('non_pdf_renamed_correct_error_message', 'Correct error message'),
            ]
            
            for test_key, description in non_pdf_renamed_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"      {status} - {description}")
            
            # Test Case 4: Corrupted PDF
            self.log("   TEST CASE 4: Corrupted PDF File")
            corrupted_pdf_tests = [
                ('corrupted_pdf_returns_400', 'Returns 400 Bad Request'),
                ('corrupted_pdf_correct_error_message', 'Correct error message'),
            ]
            
            for test_key, description in corrupted_pdf_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"      {status} - {description}")
            
            # Test Case 5: Non-PDF Extension
            self.log("   TEST CASE 5: File with Non-PDF Extension")
            non_pdf_extension_tests = [
                ('non_pdf_extension_returns_400', 'Returns 400 Bad Request'),
                ('non_pdf_extension_correct_error_message', 'Correct error message'),
            ]
            
            for test_key, description in non_pdf_extension_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"      {status} - {description}")
            
            # Validation Results
            self.log("\n🔍 VALIDATION VERIFICATION:")
            validation_tests = [
                ('validation_before_document_ai', 'Validation before Document AI'),
                ('early_error_detection', 'Early error detection'),
            ]
            
            for test_key, description in validation_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Success Criteria
            self.log("\n🎯 CRITICAL SUCCESS CRITERIA:")
            
            critical_tests = [
                'valid_pdf_works_normally',
                'empty_file_returns_400',
                'non_pdf_renamed_returns_400',
                'corrupted_pdf_returns_400',
                'non_pdf_extension_returns_400'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.test_results.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL TESTS PASSED")
                self.log("   ✅ Invalid PDF file handling working correctly")
                self.log("   ✅ Valid PDFs continue to work normally")
                self.log("   ✅ Invalid PDFs return 400 Bad Request (not 200 OK)")
                self.log("   ✅ Clear error messages provided")
            else:
                self.log("   ❌ SOME CRITICAL TESTS FAILED")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Overall Assessment
            if success_rate >= 90:
                self.log(f"\n   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
                self.log("   ✅ Invalid PDF file handling fix is working correctly")
            elif success_rate >= 70:
                self.log(f"\n   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
                self.log("   ⚠️ Most functionality working, some issues need attention")
            else:
                self.log(f"\n   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
                self.log("   ❌ Significant issues with invalid PDF file handling")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the invalid PDF file handling test"""
    tester = InvalidPDFHandlingTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n⚠️ Test interrupted by user", "WARNING")
        tester.cleanup_test_files()
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        tester.cleanup_test_files()
        sys.exit(1)

if __name__ == "__main__":
    main()
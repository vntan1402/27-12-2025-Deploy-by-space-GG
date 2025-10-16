#!/usr/bin/env python3
"""
Backend Test for FIXED Add Crew From Passport Workflow
Testing with REAL Vietnamese passport file: 3. 2O THUONG - PP.pdf

REVIEW REQUEST REQUIREMENTS:
Test the COMPLETE "Add Crew From Passport" workflow with the FIXED extraction system:

Use the real Vietnamese passport file: `3. 2O THUONG - PP.pdf`  
URL: https://customer-assets.emergentagent.com/job_crewdocs-ai/artifacts/06s7wz8r_3.%202O%20THUONG%20-%20PP.pdf

POST to /api/crew/analyze-passport with this real passport file

The FIXED system now has:
1. **System AI extraction** (with improved prompts)
2. **Manual fallback extraction** (from AI response) 
3. **Direct regex extraction** (from Document AI summary) - NEW SOLUTION

Expected results with the fixed extraction:
- **Full Name**: "HỒ SỸ CHƯƠNG" (NOT agency names)
- **Place of Birth**: "Nghệ An" (NOT "is Nghệ An")  
- **Passport Number**: "C9780204"
- **Date of Birth**: "01/01/1969" (DD/MM/YYYY format)
- **All other fields**: Properly extracted

Verify:
- Document AI processing works with real file
- Field extraction now returns correct Vietnamese passport data
- File upload to Google Drive succeeds (using fixed Apps Script method)
- No more "XUẤT NHẬP CẢNH" or "is [place]" errors
- Complete end-to-end workflow functions properly

This should demonstrate the complete fix for Vietnamese passport extraction accuracy.
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
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://smartcrew.preview.emergentagent.com') + '/api'
print(f"Using backend URL: {BACKEND_URL}")

# Test credentials
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

# Expected results for the FIXED extraction system
EXPECTED_RESULTS = {
    "full_name": "HỒ SỸ CHƯƠNG",  # NOT agency names like "XUẤT NHẬP CẢNH"
    "place_of_birth": "Nghệ An",  # NOT "is Nghệ An"
    "passport_number": "C9780204",
    "date_of_birth": "01/01/1969",  # DD/MM/YYYY format
    "nationality": "Vietnamese",
    "sex": "M"
}

class PassportExtractionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        print(f"\n{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if expected and actual:
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
    
    def authenticate(self):
        """Authenticate with the backend"""
        try:
            print(f"\n🔐 AUTHENTICATION TEST")
            print(f"Attempting login with {TEST_USERNAME}/{TEST_PASSWORD}")
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_info = data.get('user', {})
                
                # Set authorization header for future requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                
                self.log_test(
                    "Authentication", 
                    True, 
                    f"Successfully authenticated as {self.user_info.get('username')} with role {self.user_info.get('role')}"
                )
                return True
            else:
                self.log_test(
                    "Authentication", 
                    False, 
                    f"Login failed with status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def verify_passport_file(self):
        """Verify the real passport file exists and is valid"""
        try:
            print(f"\n📄 PASSPORT FILE VERIFICATION")
            
            passport_file = "/app/3_2O_THUONG_PP.pdf"
            
            if not os.path.exists(passport_file):
                self.log_test(
                    "Passport File Exists", 
                    False, 
                    f"Passport file not found at {passport_file}"
                )
                return False
            
            file_size = os.path.getsize(passport_file)
            self.log_test(
                "Passport File Exists", 
                True, 
                f"File found: {passport_file} ({file_size:,} bytes)"
            )
            
            # Verify it's a PDF file
            with open(passport_file, 'rb') as f:
                header = f.read(4)
                is_pdf = header == b'%PDF'
                
            self.log_test(
                "Passport File Format", 
                is_pdf, 
                f"PDF header check: {header}" if is_pdf else f"Invalid PDF header: {header}"
            )
            
            return is_pdf
            
        except Exception as e:
            self.log_test("Passport File Verification", False, f"File verification error: {str(e)}")
            return False
    
    def test_passport_analysis_endpoint(self):
        """Test the passport analysis endpoint with real file"""
        try:
            print(f"\n🔍 PASSPORT ANALYSIS ENDPOINT TEST")
            
            passport_file = "/app/3_2O_THUONG_PP.pdf"
            
            # Prepare multipart form data
            with open(passport_file, 'rb') as f:
                files = {
                    'passport_file': ('3_2O_THUONG_PP.pdf', f, 'application/pdf')
                }
                data = {
                    'ship_name': 'BROTHER 36'  # Test ship name
                }
                
                print(f"Sending POST request to {BACKEND_URL}/crew/analyze-passport")
                print(f"File: {passport_file} ({os.path.getsize(passport_file):,} bytes)")
                
                start_time = time.time()
                response = self.session.post(
                    f"{BACKEND_URL}/crew/analyze-passport",
                    files=files,
                    data=data,
                    timeout=120  # 2 minute timeout for processing
                )
                processing_time = time.time() - start_time
                
                print(f"Response received in {processing_time:.1f} seconds")
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    self.log_test(
                        "Passport Analysis Endpoint", 
                        True, 
                        f"Endpoint accessible, processing time: {processing_time:.1f}s"
                    )
                    
                    # Check if the response indicates success
                    success = result.get('success', False)
                    self.log_test(
                        "Passport Analysis Success", 
                        success, 
                        f"API returned success: {success}, message: {result.get('message', 'N/A')}"
                    )
                    
                    return result
                    
                else:
                    self.log_test(
                        "Passport Analysis Endpoint", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return None
                    
        except Exception as e:
            self.log_test("Passport Analysis Endpoint", False, f"Request error: {str(e)}")
            return None
    
    def verify_fixed_extraction(self, analysis_result):
        """Verify the FIXED extraction system results"""
        try:
            print(f"\n🎯 FIXED EXTRACTION VERIFICATION")
            
            if not analysis_result:
                self.log_test("Fixed Extraction Verification", False, "No analysis result to verify")
                return False
            
            # Check if analysis was successful
            if not analysis_result.get('success', False):
                error_msg = analysis_result.get('error', analysis_result.get('message', 'Unknown error'))
                self.log_test("Analysis Success", False, f"Analysis failed: {error_msg}")
                return False
            
            # Get extracted data
            extracted_data = analysis_result.get('analysis', {})
            if not extracted_data:
                self.log_test("Extracted Data Present", False, "No extracted data in response")
                return False
            
            self.log_test("Extracted Data Present", True, f"Found extracted data with {len(extracted_data)} fields")
            
            # Verify each expected field
            all_correct = True
            
            for field, expected_value in EXPECTED_RESULTS.items():
                actual_value = extracted_data.get(field, "")
                
                # Special handling for different field types
                if field in ["date_of_birth", "issue_date", "expiry_date"]:
                    # For dates, check if format is DD/MM/YYYY
                    date_pattern = r'^\d{2}/\d{2}/\d{4}$'
                    is_correct_format = bool(re.match(date_pattern, str(actual_value)))
                    
                    if field == "date_of_birth":
                        is_correct = actual_value == expected_value
                    else:
                        is_correct = is_correct_format  # For other dates, just check format
                    
                    self.log_test(
                        f"Field: {field}",
                        is_correct,
                        f"Date format check" if field != "date_of_birth" else f"Exact match check",
                        expected_value if field == "date_of_birth" else "DD/MM/YYYY format",
                        actual_value
                    )
                    
                elif field == "full_name":
                    # Check that it's NOT an agency name
                    is_not_agency = "XUẤT NHẬP CẢNH" not in str(actual_value)
                    is_expected_name = actual_value == expected_value
                    is_correct = is_not_agency and (is_expected_name or len(str(actual_value)) > 5)
                    
                    self.log_test(
                        f"Field: {field}",
                        is_correct,
                        f"Not agency name: {is_not_agency}, Valid name: {len(str(actual_value)) > 5}",
                        expected_value,
                        actual_value
                    )
                    
                elif field == "place_of_birth":
                    # Check that it doesn't have "is" prefix
                    has_no_is_prefix = not str(actual_value).startswith("is ")
                    is_expected_place = actual_value == expected_value
                    is_correct = has_no_is_prefix and (is_expected_place or len(str(actual_value)) > 2)
                    
                    self.log_test(
                        f"Field: {field}",
                        is_correct,
                        f"No 'is' prefix: {has_no_is_prefix}, Valid place: {len(str(actual_value)) > 2}",
                        expected_value,
                        actual_value
                    )
                    
                else:
                    # Exact match for other fields
                    is_correct = actual_value == expected_value
                    self.log_test(
                        f"Field: {field}",
                        is_correct,
                        "Exact match check",
                        expected_value,
                        actual_value
                    )
                
                if not is_correct:
                    all_correct = False
            
            # Overall extraction quality
            self.log_test(
                "Overall Fixed Extraction Quality",
                all_correct,
                f"All critical fields extracted correctly: {all_correct}"
            )
            
            return all_correct
            
        except Exception as e:
            self.log_test("Fixed Extraction Verification", False, f"Verification error: {str(e)}")
            return False
    
    def verify_file_upload_success(self, analysis_result):
        """Verify that files were uploaded to Google Drive successfully"""
        try:
            print(f"\n📤 FILE UPLOAD VERIFICATION")
            
            if not analysis_result:
                self.log_test("File Upload Verification", False, "No analysis result to check")
                return False
            
            # Check for file upload success indicators
            files_data = analysis_result.get('files', {})
            
            if not files_data:
                self.log_test("File Upload Data Present", False, "No files data in response")
                return False
            
            self.log_test("File Upload Data Present", True, f"Files data found: {len(files_data)} entries")
            
            # Check for passport file upload
            passport_file = files_data.get('passport_file')
            if passport_file:
                passport_file_id = passport_file.get('file_id', '')
                passport_success = bool(passport_file_id)
                self.log_test(
                    "Passport File Upload",
                    passport_success,
                    f"File ID: {passport_file_id}" if passport_success else "No file ID returned"
                )
            else:
                self.log_test("Passport File Upload", False, "No passport file data in response")
                passport_success = False
            
            # Check for summary file upload
            summary_file = files_data.get('summary_file')
            if summary_file:
                summary_file_id = summary_file.get('file_id', '')
                summary_success = bool(summary_file_id)
                self.log_test(
                    "Summary File Upload",
                    summary_success,
                    f"File ID: {summary_file_id}" if summary_success else "No file ID returned"
                )
            else:
                self.log_test("Summary File Upload", False, "No summary file data in response")
                summary_success = False
            
            # Overall upload success
            overall_success = passport_success and summary_success
            self.log_test(
                "Overall File Upload Success",
                overall_success,
                f"Passport: {passport_success}, Summary: {summary_success}"
            )
            
            return overall_success
            
        except Exception as e:
            self.log_test("File Upload Verification", False, f"Upload verification error: {str(e)}")
            return False
    
    def verify_document_ai_processing(self, analysis_result):
        """Verify Document AI processing worked correctly"""
        try:
            print(f"\n🤖 DOCUMENT AI PROCESSING VERIFICATION")
            
            if not analysis_result:
                self.log_test("Document AI Processing", False, "No analysis result to check")
                return False
            
            # Check for processing method
            processing_method = analysis_result.get('processing_method', '')
            has_processing_method = bool(processing_method)
            
            self.log_test(
                "Processing Method Present",
                has_processing_method,
                f"Method: {processing_method}" if has_processing_method else "No processing method found"
            )
            
            # Check for confidence score
            confidence_score = analysis_result.get('analysis', {}).get('confidence_score', 0)
            has_confidence = confidence_score > 0
            
            self.log_test(
                "Confidence Score Present",
                has_confidence,
                f"Confidence: {confidence_score}" if has_confidence else "No confidence score"
            )
            
            # Check for summary or text content (indicates Document AI worked)
            summary = analysis_result.get('summary', '')
            has_summary = len(summary) > 100  # Should have substantial content
            
            self.log_test(
                "Document AI Summary Generated",
                has_summary,
                f"Summary length: {len(summary)} characters" if summary else "No summary generated"
            )
            
            # Overall Document AI success
            overall_success = has_processing_method and has_confidence and has_summary
            self.log_test(
                "Overall Document AI Processing",
                overall_success,
                f"Method: {has_processing_method}, Confidence: {has_confidence}, Summary: {has_summary}"
            )
            
            return overall_success
            
        except Exception as e:
            self.log_test("Document AI Processing Verification", False, f"Processing verification error: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("=" * 80)
        print("🧪 COMPREHENSIVE FIXED PASSPORT EXTRACTION TEST")
        print("=" * 80)
        print(f"Testing with real Vietnamese passport: 3. 2O THUONG - PP.pdf")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Expected Results: {EXPECTED_RESULTS}")
        
        # Step 1: Authentication
        if not self.authenticate():
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with tests")
            return False
        
        # Step 2: Verify passport file
        if not self.verify_passport_file():
            print("\n❌ CRITICAL: Passport file verification failed - cannot proceed")
            return False
        
        # Step 3: Test passport analysis endpoint
        analysis_result = self.test_passport_analysis_endpoint()
        if not analysis_result:
            print("\n❌ CRITICAL: Passport analysis endpoint failed - cannot proceed")
            return False
        
        # Step 4: Verify fixed extraction
        extraction_success = self.verify_fixed_extraction(analysis_result)
        
        # Step 5: Verify Document AI processing
        document_ai_success = self.verify_document_ai_processing(analysis_result)
        
        # Step 6: Verify file upload success
        upload_success = self.verify_file_upload_success(analysis_result)
        
        # Generate final report
        self.generate_final_report(extraction_success, document_ai_success, upload_success)
        
        return extraction_success and document_ai_success and upload_success
    
    def generate_final_report(self, extraction_success, document_ai_success, upload_success):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 FINAL TEST REPORT")
        print("=" * 80)
        
        # Count test results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n🎯 CRITICAL COMPONENTS:")
        print(f"   Fixed Extraction System: {'✅ WORKING' if extraction_success else '❌ FAILED'}")
        print(f"   Document AI Processing: {'✅ WORKING' if document_ai_success else '❌ FAILED'}")
        print(f"   File Upload to Google Drive: {'✅ WORKING' if upload_success else '❌ FAILED'}")
        
        # Overall assessment
        overall_success = extraction_success and document_ai_success and upload_success
        print(f"\n🏆 OVERALL ASSESSMENT: {'✅ COMPLETE SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
        
        if overall_success:
            print("\n✅ FIXED EXTRACTION SYSTEM VERIFICATION COMPLETE")
            print("   - Vietnamese passport data extracted correctly")
            print("   - No more agency name errors (XUẤT NHẬP CẢNH)")
            print("   - No more 'is [place]' errors")
            print("   - Proper DD/MM/YYYY date format")
            print("   - Complete end-to-end workflow functional")
        else:
            print("\n❌ ISSUES IDENTIFIED:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = PassportExtractionTester()
    
    try:
        success = tester.run_comprehensive_test()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
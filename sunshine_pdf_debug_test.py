#!/usr/bin/env python3
"""
FOCUSED DEBUG TEST for SUNSHINE_01_ImagePDF.pdf Fallback Issue

This test specifically investigates why SUNSHINE_01_ImagePDF.pdf is falling back to 
filename-based classification instead of proper AI analysis.

INVESTIGATION FOCUS:
1. Login as admin1/123456
2. Test POST /api/certificates/multi-upload with SUNSHINE_01_ImagePDF_New.pdf (997KB)
3. Monitor Smart Processing workflow:
   - File Type Analysis: Should detect as "image_based" PDF
   - Method Selection: Should use OCR processing (not direct text extraction)
   - OCR Processing: Should extract text from scanned images
   - AI Analysis: Should analyze extracted text and return proper certificate data
4. Check backend logs for OCR failures or fallback triggers
5. Verify dependencies (poppler-utils, tesseract-ocr) are working

EXPECTED RESULTS:
- pdf_type: "image_based" 
- processing_method: "enhanced_ocr" or "multi_engine_ocr"
- AI should extract real certificate name like "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE"
- Should NOT fallback to "Maritime Certificate - filename" pattern
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

# Test file from review request
TEST_PDF_FILE = "/app/SUNSHINE_01_ImagePDF_New.pdf"
SHIP_ID = "e21c71a2-9543-4f92-990c-72f54292fde8"  # SUNSHINE 01 ship ID

class SunshinePDFDebugTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results with detailed information"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()
    
    def authenticate(self):
        """Authenticate with admin1/123456 credentials"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                
                user_role = self.user_info.get('role', '').upper()
                self.log_test("Authentication Test", True, 
                            f"Logged in as {self.user_info['username']} ({user_role})")
                return True
            else:
                self.log_test("Authentication Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication Test", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_pdf_file_verification(self):
        """Verify the specific SUNSHINE_01_ImagePDF_New.pdf file exists and has correct size"""
        try:
            if os.path.exists(TEST_PDF_FILE):
                file_size = os.path.getsize(TEST_PDF_FILE)
                expected_size_kb = 997  # From review request
                actual_size_kb = file_size // 1024
                
                size_match = abs(actual_size_kb - expected_size_kb) <= 50  # Allow 50KB tolerance
                
                details = f"File: {TEST_PDF_FILE}, Size: {actual_size_kb}KB (expected ~{expected_size_kb}KB)"
                self.log_test("PDF File Verification", size_match, details)
                return size_match
            else:
                self.log_test("PDF File Verification", False, 
                            error=f"File not found: {TEST_PDF_FILE}")
                return False
                
        except Exception as e:
            self.log_test("PDF File Verification", False, error=str(e))
            return False
    
    def test_ship_existence(self):
        """Verify SUNSHINE 01 ship exists with correct ID"""
        try:
            response = requests.get(f"{API_BASE}/ships/{SHIP_ID}", headers=self.get_headers())
            
            if response.status_code == 200:
                ship_data = response.json()
                ship_name = ship_data.get('name', '')
                
                if 'SUNSHINE' in ship_name.upper():
                    self.log_test("Ship Existence Test", True, 
                                f"Found ship: {ship_name} (ID: {SHIP_ID})")
                    return True
                else:
                    self.log_test("Ship Existence Test", False, 
                                error=f"Ship name mismatch: {ship_name}")
                    return False
            else:
                self.log_test("Ship Existence Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Ship Existence Test", False, error=str(e))
            return False
    
    def test_ocr_dependencies(self):
        """Test if OCR dependencies (poppler-utils, tesseract-ocr) are installed"""
        try:
            # Test poppler-utils
            poppler_result = os.system("which pdftoppm > /dev/null 2>&1")
            poppler_installed = poppler_result == 0
            
            # Test tesseract-ocr
            tesseract_result = os.system("which tesseract > /dev/null 2>&1")
            tesseract_installed = tesseract_result == 0
            
            dependencies_ok = poppler_installed and tesseract_installed
            
            details = f"Poppler-utils: {'✓' if poppler_installed else '✗'}, Tesseract: {'✓' if tesseract_installed else '✗'}"
            
            self.log_test("OCR Dependencies Test", dependencies_ok, details)
            return dependencies_ok
            
        except Exception as e:
            self.log_test("OCR Dependencies Test", False, error=str(e))
            return False
    
    def test_multi_upload_workflow(self):
        """Test the complete multi-upload workflow that's failing"""
        try:
            # Read the test PDF file
            with open(TEST_PDF_FILE, 'rb') as f:
                pdf_content = f.read()
            
            # Prepare the multipart form data for multi-upload
            files = {
                'files': ('SUNSHINE_01_ImagePDF_New.pdf', pdf_content, 'application/pdf')
            }
            
            data = {
                'ship_id': SHIP_ID
            }
            
            print(f"📤 Testing multi-upload with: {TEST_PDF_FILE} ({len(pdf_content):,} bytes)")
            print(f"🚢 Ship ID: {SHIP_ID}")
            
            # Make the API request to multi-upload endpoint
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                files=files,
                data=data,
                headers=self.get_headers()
            )
            processing_time = time.time() - start_time
            
            print(f"⏱️ Processing time: {processing_time:.2f} seconds")
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"📋 Response data: {json.dumps(response_data, indent=2)}")
                
                # Analyze the response for fallback patterns
                return self.analyze_multi_upload_response(response_data, processing_time)
                
            else:
                error_text = response.text
                self.log_test("Multi-Upload Workflow", False,
                            error=f"Status: {response.status_code}, Response: {error_text}")
                return False
                
        except Exception as e:
            self.log_test("Multi-Upload Workflow", False, error=str(e))
            return False
    
    def analyze_multi_upload_response(self, response_data, processing_time):
        """Analyze the multi-upload response for fallback patterns"""
        success_count = 0
        total_tests = 6
        
        # 1. Check if processing was successful
        success = response_data.get('success', False)
        if success:
            self.log_test("Multi-Upload Success", True, "Upload processing completed")
            success_count += 1
        else:
            self.log_test("Multi-Upload Success", False, 
                        error=f"Upload failed: {response_data.get('message', 'Unknown error')}")
        
        # 2. Check for processed files
        processed_files = response_data.get('processed_files', [])
        if len(processed_files) > 0:
            self.log_test("File Processing", True, f"Processed {len(processed_files)} files")
            success_count += 1
            
            # Analyze the first processed file
            first_file = processed_files[0]
            return self.analyze_processed_file(first_file, success_count, total_tests)
        else:
            self.log_test("File Processing", False, error="No files were processed")
            return False
    
    def analyze_processed_file(self, file_data, success_count, total_tests):
        """Analyze individual processed file for fallback patterns"""
        
        # 3. Check PDF type detection
        pdf_type = file_data.get('pdf_type')
        if pdf_type == 'image_based':
            self.log_test("PDF Type Detection", True, f"Correctly detected as: {pdf_type}")
            success_count += 1
        else:
            self.log_test("PDF Type Detection", False, 
                        error=f"Expected 'image_based', got: {pdf_type}")
        
        # 4. Check processing method
        processing_method = file_data.get('processing_method')
        expected_methods = ['enhanced_ocr', 'multi_engine_ocr', 'ocr_processing']
        if processing_method in expected_methods:
            self.log_test("Processing Method Selection", True, 
                        f"Using OCR method: {processing_method}")
            success_count += 1
        else:
            self.log_test("Processing Method Selection", False, 
                        error=f"Expected OCR method, got: {processing_method}")
        
        # 5. Check for filename-based fallback (the main issue)
        cert_name = file_data.get('cert_name', '')
        is_filename_fallback = (
            'Maritime Certificate' in cert_name or 
            'filename' in cert_name.lower() or
            'SUNSHINE_01_ImagePDF' in cert_name
        )
        
        if not is_filename_fallback and cert_name:
            self.log_test("AI Analysis (No Filename Fallback)", True, 
                        f"Real certificate name extracted: {cert_name}")
            success_count += 1
        else:
            self.log_test("AI Analysis (No Filename Fallback)", False, 
                        error=f"Filename-based fallback detected: {cert_name}")
        
        # 6. Check for real certificate data extraction
        real_data_fields = ['cert_no', 'issue_date', 'valid_date', 'issued_by']
        extracted_real_data = []
        
        for field in real_data_fields:
            value = file_data.get(field)
            if value and value != 'Unknown' and not str(value).startswith('CERT_'):
                extracted_real_data.append(f"{field}: {value}")
        
        if len(extracted_real_data) >= 2:
            self.log_test("Real Certificate Data Extraction", True, 
                        f"Extracted {len(extracted_real_data)} real fields: {', '.join(extracted_real_data[:2])}")
            success_count += 1
        else:
            self.log_test("Real Certificate Data Extraction", False, 
                        error=f"Insufficient real data extracted: {extracted_real_data}")
        
        # Overall assessment
        workflow_success = success_count >= 5  # At least 5 out of 6 tests should pass
        
        if workflow_success:
            self.log_test("SUNSHINE PDF Smart Processing", True,
                        f"Smart processing successful: {success_count}/{total_tests} tests passed")
        else:
            self.log_test("SUNSHINE PDF Smart Processing", False,
                        error=f"Smart processing failed: Only {success_count}/{total_tests} tests passed")
        
        # Print detailed analysis
        print("\n🔍 DETAILED ANALYSIS:")
        print(f"Certificate Name: {cert_name}")
        print(f"PDF Type: {pdf_type}")
        print(f"Processing Method: {processing_method}")
        print(f"Filename Fallback: {'YES' if is_filename_fallback else 'NO'}")
        print(f"Real Data Fields: {len(extracted_real_data)}")
        
        return workflow_success
    
    def check_backend_logs(self):
        """Check backend logs for OCR failures or fallback triggers"""
        try:
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.err.log",
                "/var/log/supervisor/backend.out.log"
            ]
            
            found_logs = False
            for log_file in log_files:
                if os.path.exists(log_file):
                    found_logs = True
                    print(f"\n📋 Checking {log_file}:")
                    # Get last 50 lines of logs
                    os.system(f"tail -n 50 {log_file} | grep -i -E '(ocr|tesseract|poppler|fallback|sunshine)' || echo 'No relevant log entries found'")
            
            if found_logs:
                self.log_test("Backend Log Analysis", True, "Backend logs checked for OCR/fallback issues")
            else:
                self.log_test("Backend Log Analysis", False, error="Backend log files not found")
            
            return found_logs
            
        except Exception as e:
            self.log_test("Backend Log Analysis", False, error=str(e))
            return False
    
    def run_debug_investigation(self):
        """Run the complete debug investigation"""
        print("🔍 SUNSHINE_01_ImagePDF.pdf FALLBACK DEBUG INVESTIGATION")
        print("=" * 80)
        print("FOCUS: Why is the PDF falling back to filename-based classification?")
        print("EXPECTED: Should use OCR processing and extract real certificate data")
        print("=" * 80)
        
        # Run tests in sequence
        tests = [
            self.authenticate,
            self.test_pdf_file_verification,
            self.test_ship_existence,
            self.test_ocr_dependencies,
            self.test_multi_upload_workflow,
            self.check_backend_logs
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
            else:
                print(f"❌ Investigation step failed: {test.__name__}")
                # Continue with other tests even if one fails
        
        # Summary
        print("=" * 80)
        print(f"📊 INVESTIGATION SUMMARY: {passed_tests}/{len(tests)} steps completed")
        
        if passed_tests >= 4:  # At least 4 steps should complete successfully
            print("🎯 INVESTIGATION COMPLETED - Check results above for root cause")
        else:
            print(f"⚠️ INVESTIGATION INCOMPLETE - {len(tests) - passed_tests} steps failed")
        
        # Detailed results
        print("\n📋 DETAILED INVESTIGATION RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
            if result['error']:
                print(f"    ERROR: {result['error']}")
        
        return passed_tests >= 4

def main():
    """Main debug investigation execution"""
    print("🚀 Starting SUNSHINE_01_ImagePDF.pdf Fallback Debug Investigation")
    
    tester = SunshinePDFDebugTester()
    success = tester.run_debug_investigation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
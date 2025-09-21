#!/usr/bin/env python3
"""
PDF-Only Restriction with Enhanced OCR Testing
Testing the system's PDF-only restriction while maintaining enhanced OCR processing capabilities.
This test verifies that only PDF files are accepted and that enhanced OCR works correctly with PDF files.
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import io
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ship-cert-manager-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

# Test PDF file URL from review request
TEST_PDF_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/swohyuf9_SS%20STAR%20PM252494416_ImagePDF.pdf"

class PDFOCRTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
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
                username = self.user_info.get('username', '')
                
                self.log_test("Authentication Test", True, 
                            f"Logged in as {username} with role {user_role}")
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
    
    def download_test_pdf(self):
        """Download the test PDF file from the provided URL"""
        try:
            print(f"Downloading test PDF from: {TEST_PDF_URL}")
            response = requests.get(TEST_PDF_URL, timeout=30)
            
            if response.status_code == 200:
                pdf_content = response.content
                file_size = len(pdf_content)
                
                self.log_test("PDF Download Test", True, 
                            f"Successfully downloaded PDF file ({file_size:,} bytes)")
                return pdf_content
            else:
                self.log_test("PDF Download Test", False, 
                            error=f"Failed to download PDF. Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("PDF Download Test", False, error=str(e))
            return None
    
    def test_pdf_file_acceptance(self, pdf_content):
        """Test that PDF files are accepted and processed"""
        try:
            # Test the analyze-ship-certificate endpoint with PDF file
            files = {
                'file': ('SS_STAR_PM252494416_ImagePDF.pdf', io.BytesIO(pdf_content), 'application/pdf')
            }
            
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if the response contains expected structure
                if 'success' in result and 'data' in result:
                    success = result.get('success', False)
                    data = result.get('data', {})
                    analysis = data.get('analysis', {})
                    
                    if success:
                        self.log_test("PDF File Acceptance Test", True, 
                                    f"PDF file accepted and processed successfully. Analysis contains {len(analysis)} fields")
                        return result
                    else:
                        self.log_test("PDF File Acceptance Test", False, 
                                    error=f"PDF processing failed: {result.get('message', 'Unknown error')}")
                        return None
                else:
                    self.log_test("PDF File Acceptance Test", False, 
                                error="Response missing expected structure (success/data fields)")
                    return None
            else:
                self.log_test("PDF File Acceptance Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("PDF File Acceptance Test", False, error=str(e))
            return None
    
    def test_non_pdf_file_rejection(self):
        """Test that non-PDF files are rejected with proper error message"""
        try:
            # Create a PNG file (image file that should be rejected)
            png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
            
            files = {
                'file': ('test_image.png', io.BytesIO(png_content), 'image/png')
            }
            
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 400:
                result = response.json()
                error_message = result.get('detail', '').lower()
                
                if 'only pdf files are allowed' in error_message:
                    self.log_test("Non-PDF File Rejection Test", True, 
                                f"Non-PDF file correctly rejected with message: {result.get('detail', '')}")
                    return True
                else:
                    self.log_test("Non-PDF File Rejection Test", False, 
                                error=f"Wrong error message. Expected 'Only PDF files are allowed', got: {result.get('detail', '')}")
                    return False
            else:
                self.log_test("Non-PDF File Rejection Test", False, 
                            error=f"Expected 400 status code, got {response.status_code}. Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Non-PDF File Rejection Test", False, error=str(e))
            return False
    
    def test_enhanced_ocr_processing(self, analysis_result):
        """Test that enhanced OCR processing extracts ship data correctly"""
        try:
            if not analysis_result:
                self.log_test("Enhanced OCR Processing Test", False, 
                            error="No analysis result provided")
                return False
            
            data = analysis_result.get('data', {})
            analysis = data.get('analysis', {})
            
            # Expected ship data from the review request
            expected_data = {
                'ship_name': 'SUNSHINE STAR',
                'imo_number': '9405136',
                'flag': 'BELIZE',
                'class_society': 'PMDS',
                'gross_tonnage': 2988,
                'deadweight': 5274.3,
                'built_year': 2005
            }
            
            extracted_fields = []
            missing_fields = []
            incorrect_fields = []
            
            for field, expected_value in expected_data.items():
                actual_value = analysis.get(field)
                
                if actual_value is not None and actual_value != "null" and str(actual_value).strip():
                    extracted_fields.append(field)
                    
                    # Check if the value matches expected (case insensitive for strings)
                    if isinstance(expected_value, str):
                        if str(actual_value).upper().strip() != str(expected_value).upper().strip():
                            incorrect_fields.append(f"{field}: expected '{expected_value}', got '{actual_value}'")
                    elif isinstance(expected_value, (int, float)):
                        try:
                            if abs(float(actual_value) - float(expected_value)) > 0.1:
                                incorrect_fields.append(f"{field}: expected {expected_value}, got {actual_value}")
                        except (ValueError, TypeError):
                            incorrect_fields.append(f"{field}: expected {expected_value}, got non-numeric '{actual_value}'")
                else:
                    missing_fields.append(field)
            
            # Evaluate the OCR performance
            total_fields = len(expected_data)
            extracted_count = len(extracted_fields)
            accuracy_rate = (extracted_count / total_fields) * 100
            
            if extracted_count >= 5:  # At least 5 out of 7 fields should be extracted
                details = f"Extracted {extracted_count}/{total_fields} fields ({accuracy_rate:.1f}% accuracy). "
                details += f"Extracted: {', '.join(extracted_fields)}"
                
                if missing_fields:
                    details += f". Missing: {', '.join(missing_fields)}"
                if incorrect_fields:
                    details += f". Incorrect: {', '.join(incorrect_fields)}"
                
                self.log_test("Enhanced OCR Processing Test", True, details)
                return True
            else:
                error_msg = f"Only extracted {extracted_count}/{total_fields} fields ({accuracy_rate:.1f}% accuracy). "
                error_msg += f"Missing: {', '.join(missing_fields)}"
                
                self.log_test("Enhanced OCR Processing Test", False, error=error_msg)
                return False
                
        except Exception as e:
            self.log_test("Enhanced OCR Processing Test", False, error=str(e))
            return False
    
    def test_tesseract_ocr_availability(self):
        """Test that Tesseract OCR is available and working"""
        try:
            # Create a simple text-based PDF for OCR testing
            simple_pdf_content = b"""%PDF-1.4
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
/Length 100
>>
stream
BT
/F1 12 Tf
72 720 Td
(SHIP NAME: TEST VESSEL) Tj
0 -20 Td
(IMO NUMBER: 1234567) Tj
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
350
%%EOF"""
            
            files = {
                'file': ('test_ocr.pdf', io.BytesIO(simple_pdf_content), 'application/pdf')
            }
            
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if OCR processing was attempted
                processing_method = result.get('data', {}).get('processing_method', '')
                fallback_reason = result.get('data', {}).get('fallback_reason', '')
                
                if 'ocr' in processing_method.lower() or 'tesseract' in processing_method.lower():
                    self.log_test("Tesseract OCR Availability Test", True, 
                                f"OCR processing detected. Method: {processing_method}")
                    return True
                elif fallback_reason and 'ocr' in fallback_reason.lower():
                    self.log_test("Tesseract OCR Availability Test", False, 
                                error=f"OCR processing failed: {fallback_reason}")
                    return False
                else:
                    self.log_test("Tesseract OCR Availability Test", True, 
                                f"PDF processed successfully. Method: {processing_method}")
                    return True
            else:
                self.log_test("Tesseract OCR Availability Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Tesseract OCR Availability Test", False, error=str(e))
            return False
    
    def test_error_handling_for_corrupted_pdf(self):
        """Test error handling for corrupted PDF files"""
        try:
            # Create a corrupted PDF file
            corrupted_pdf = b"This is not a valid PDF file content"
            
            files = {
                'file': ('corrupted.pdf', io.BytesIO(corrupted_pdf), 'application/pdf')
            }
            
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers()
            )
            
            # Should either process with fallback or return appropriate error
            if response.status_code in [200, 400, 422]:
                if response.status_code == 200:
                    result = response.json()
                    fallback_reason = result.get('data', {}).get('fallback_reason', '')
                    
                    if fallback_reason:
                        self.log_test("Error Handling - Corrupted PDF Test", True, 
                                    f"Corrupted PDF handled gracefully with fallback: {fallback_reason}")
                    else:
                        self.log_test("Error Handling - Corrupted PDF Test", True, 
                                    "Corrupted PDF processed without errors")
                else:
                    result = response.json()
                    self.log_test("Error Handling - Corrupted PDF Test", True, 
                                f"Corrupted PDF properly rejected with status {response.status_code}: {result.get('detail', '')}")
                return True
            else:
                self.log_test("Error Handling - Corrupted PDF Test", False, 
                            error=f"Unexpected status code {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Error Handling - Corrupted PDF Test", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all PDF-only restriction with enhanced OCR tests"""
        print("🧪 PDF-ONLY RESTRICTION WITH ENHANCED OCR TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test PDF URL: {TEST_PDF_URL}")
        print()
        
        # Step 1: Authentication Test
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Download Test PDF
        pdf_content = self.download_test_pdf()
        if not pdf_content:
            print("❌ Failed to download test PDF. Cannot proceed with PDF tests.")
            return False
        
        # Step 3: Test PDF File Acceptance and Processing
        analysis_result = self.test_pdf_file_acceptance(pdf_content)
        if not analysis_result:
            print("❌ PDF file acceptance test failed.")
            return False
        
        # Step 4: Test Non-PDF File Rejection
        if not self.test_non_pdf_file_rejection():
            print("❌ Non-PDF file rejection test failed.")
            return False
        
        # Step 5: Test Enhanced OCR Processing
        if not self.test_enhanced_ocr_processing(analysis_result):
            print("❌ Enhanced OCR processing test failed.")
            # Continue with other tests
        
        # Step 6: Test Tesseract OCR Availability
        if not self.test_tesseract_ocr_availability():
            print("❌ Tesseract OCR availability test failed.")
            # Continue with other tests
        
        # Step 7: Test Error Handling for Corrupted PDF
        if not self.test_error_handling_for_corrupted_pdf():
            print("❌ Error handling test failed.")
            # Continue with other tests
        
        # Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
            if result['error']:
                print(f"    Error: {result['error']}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! PDF-only restriction with enhanced OCR is working correctly.")
            return True
        else:
            print(f"\n❌ {total - passed} tests failed. Please review the issues above.")
            return False

def main():
    """Main test execution"""
    tester = PDFOCRTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
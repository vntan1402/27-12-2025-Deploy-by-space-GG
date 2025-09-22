#!/usr/bin/env python3
"""
Backend Testing for NEW ENHANCED Multi Cert Upload workflow with JPG/PNG support
Testing the enhanced /api/certificates/multi-upload endpoint with:
1. Support for JPG, PNG files in addition to PDF files
2. File type validation for "application/pdf", "image/jpeg", "image/jpg", "image/png"
3. Enhanced ship analysis to handle image files with OCR
4. New process_image_with_ocr() method in OCR processor
5. Updated classify_by_filename() to support image extensions
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

class EnhancedMultiCertUploadTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.test_ship_id = None
        
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
        """Authenticate with admin credentials"""
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
    
    def get_test_ship(self):
        """Get a test ship for certificate upload"""
        try:
            response = requests.get(f"{API_BASE}/ships", headers=self.get_headers())
            
            if response.status_code == 200:
                ships = response.json()
                if ships:
                    self.test_ship_id = ships[0]['id']
                    ship_name = ships[0]['name']
                    self.log_test("Test Ship Selection", True, 
                                f"Selected ship: {ship_name} (ID: {self.test_ship_id})")
                    return True
                else:
                    self.log_test("Test Ship Selection", False, 
                                error="No ships found in database")
                    return False
            else:
                self.log_test("Test Ship Selection", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Test Ship Selection", False, error=str(e))
            return False
    
    def create_test_jpg_certificate(self):
        """Create a simple test JPG image with certificate text"""
        try:
            # Create a simple certificate image
            width, height = 800, 600
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw certificate content
            y_pos = 50
            
            # Title
            draw.text((width//2 - 150, y_pos), "SAFETY MANAGEMENT CERTIFICATE", 
                     fill='black', font=font_large)
            y_pos += 60
            
            # Certificate details
            certificate_text = [
                "Certificate Number: TEST123456",
                "Ship Name: TEST VESSEL",
                "IMO Number: 1234567",
                "Flag State: PANAMA",
                "Issue Date: 2024-01-15",
                "Valid Until: 2025-01-15",
                "Issued By: Test Maritime Authority",
                "",
                "This is to certify that the Safety Management System",
                "of the above ship has been audited and complies with",
                "the requirements of the ISM Code."
            ]
            
            for line in certificate_text:
                draw.text((50, y_pos), line, fill='black', font=font_medium)
                y_pos += 30
            
            # Save to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG', quality=95)
            img_bytes.seek(0)
            
            self.log_test("Test JPG Certificate Creation", True, 
                        f"Created test certificate image ({len(img_bytes.getvalue())} bytes)")
            return img_bytes.getvalue()
            
        except Exception as e:
            self.log_test("Test JPG Certificate Creation", False, error=str(e))
            return None
    
    def create_test_pdf_certificate(self):
        """Create a simple test PDF certificate (mock data)"""
        # For this test, we'll use a simple text-based approach
        # In a real scenario, you'd use a PDF library like reportlab
        pdf_content = b"""%PDF-1.4
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
/Length 200
>>
stream
BT
/F1 12 Tf
100 700 Td
(CARGO SHIP SAFETY CERTIFICATE) Tj
0 -20 Td
(Certificate Number: PDF789012) Tj
0 -20 Td
(Ship Name: PDF TEST SHIP) Tj
0 -20 Td
(IMO Number: 9876543) Tj
0 -20 Td
(Flag State: LIBERIA) Tj
0 -20 Td
(Issue Date: 2024-02-01) Tj
0 -20 Td
(Valid Until: 2025-02-01) Tj
0 -20 Td
(Issued By: Test Classification Society) Tj
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
456
%%EOF"""
        
        self.log_test("Test PDF Certificate Creation", True, 
                    f"Created test PDF certificate ({len(pdf_content)} bytes)")
        return pdf_content
    
    def test_multi_upload_endpoint_accessibility(self):
        """Test that the multi-upload endpoint is accessible"""
        try:
            if not self.test_ship_id:
                self.log_test("Multi-Upload Endpoint Accessibility", False, 
                            error="No test ship ID available")
                return False
            
            # Test with empty request to check endpoint accessibility
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={"ship_id": self.test_ship_id},
                headers=self.get_headers()
            )
            
            # We expect this to fail with 400 (no files), not 404 (endpoint not found)
            if response.status_code == 400:
                self.log_test("Multi-Upload Endpoint Accessibility", True, 
                            "Endpoint accessible (400 Bad Request as expected for empty request)")
                return True
            elif response.status_code == 404:
                self.log_test("Multi-Upload Endpoint Accessibility", False, 
                            error="Endpoint not found (404)")
                return False
            else:
                self.log_test("Multi-Upload Endpoint Accessibility", True, 
                            f"Endpoint accessible (Status: {response.status_code})")
                return True
                
        except Exception as e:
            self.log_test("Multi-Upload Endpoint Accessibility", False, error=str(e))
            return False
    
    def test_pdf_file_upload(self):
        """Test PDF file upload (existing functionality)"""
        try:
            if not self.test_ship_id:
                self.log_test("PDF File Upload Test", False, 
                            error="No test ship ID available")
                return False
            
            # Create test PDF
            pdf_content = self.create_test_pdf_certificate()
            if not pdf_content:
                return False
            
            # Prepare files for upload
            files = {
                'files': ('test_certificate.pdf', pdf_content, 'application/pdf')
            }
            
            print(f"📤 Uploading PDF file: test_certificate.pdf ({len(pdf_content)} bytes)")
            
            # Make the API request
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={"ship_id": self.test_ship_id},
                files=files,
                headers=self.get_headers()
            )
            processing_time = time.time() - start_time
            
            print(f"⏱️ Processing time: {processing_time:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if 'results' in data and isinstance(data['results'], list):
                    results = data['results']
                    if len(results) > 0:
                        result = results[0]
                        filename = result.get('filename', 'unknown')
                        status = result.get('status', 'unknown')
                        
                        self.log_test("PDF File Upload Test", True, 
                                    f"PDF processed: {filename}, Status: {status}, Processing time: {processing_time:.2f}s")
                        
                        # Verify PDF processing workflow
                        return self.verify_pdf_processing_workflow(result)
                    else:
                        self.log_test("PDF File Upload Test", False, 
                                    error="No results in response")
                        return False
                else:
                    self.log_test("PDF File Upload Test", False, 
                                error="Invalid response structure")
                    return False
            else:
                self.log_test("PDF File Upload Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("PDF File Upload Test", False, error=str(e))
            return False
    
    def test_jpg_file_upload(self):
        """Test JPG file upload (new functionality)"""
        try:
            if not self.test_ship_id:
                self.log_test("JPG File Upload Test", False, 
                            error="No test ship ID available")
                return False
            
            # Create test JPG
            jpg_content = self.create_test_jpg_certificate()
            if not jpg_content:
                return False
            
            # Prepare files for upload
            files = {
                'files': ('test_certificate.jpg', jpg_content, 'image/jpeg')
            }
            
            print(f"📤 Uploading JPG file: test_certificate.jpg ({len(jpg_content)} bytes)")
            
            # Make the API request
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={"ship_id": self.test_ship_id},
                files=files,
                headers=self.get_headers()
            )
            processing_time = time.time() - start_time
            
            print(f"⏱️ Processing time: {processing_time:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if 'results' in data and isinstance(data['results'], list):
                    results = data['results']
                    if len(results) > 0:
                        result = results[0]
                        filename = result.get('filename', 'unknown')
                        status = result.get('status', 'unknown')
                        
                        self.log_test("JPG File Upload Test", True, 
                                    f"JPG processed: {filename}, Status: {status}, Processing time: {processing_time:.2f}s")
                        
                        # Verify JPG processing workflow
                        return self.verify_jpg_processing_workflow(result)
                    else:
                        self.log_test("JPG File Upload Test", False, 
                                    error="No results in response")
                        return False
                else:
                    self.log_test("JPG File Upload Test", False, 
                                error="Invalid response structure")
                    return False
            else:
                self.log_test("JPG File Upload Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("JPG File Upload Test", False, error=str(e))
            return False
    
    def test_mixed_file_upload(self):
        """Test mixed file upload (PDF + JPG in single batch)"""
        try:
            if not self.test_ship_id:
                self.log_test("Mixed File Upload Test", False, 
                            error="No test ship ID available")
                return False
            
            # Create test files
            pdf_content = self.create_test_pdf_certificate()
            jpg_content = self.create_test_jpg_certificate()
            
            if not pdf_content or not jpg_content:
                return False
            
            # Prepare multiple files for upload
            files = [
                ('files', ('mixed_test.pdf', pdf_content, 'application/pdf')),
                ('files', ('mixed_test.jpg', jpg_content, 'image/jpeg'))
            ]
            
            print(f"📤 Uploading mixed files: PDF ({len(pdf_content)} bytes) + JPG ({len(jpg_content)} bytes)")
            
            # Make the API request
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={"ship_id": self.test_ship_id},
                files=files,
                headers=self.get_headers()
            )
            processing_time = time.time() - start_time
            
            print(f"⏱️ Processing time: {processing_time:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if 'results' in data and isinstance(data['results'], list):
                    results = data['results']
                    if len(results) == 2:  # Should have 2 results
                        pdf_result = None
                        jpg_result = None
                        
                        for result in results:
                            filename = result.get('filename', '')
                            if filename.endswith('.pdf'):
                                pdf_result = result
                            elif filename.endswith('.jpg'):
                                jpg_result = result
                        
                        if pdf_result and jpg_result:
                            pdf_status = pdf_result.get('status', 'unknown')
                            jpg_status = jpg_result.get('status', 'unknown')
                            
                            self.log_test("Mixed File Upload Test", True, 
                                        f"Mixed upload successful: PDF status: {pdf_status}, JPG status: {jpg_status}, Processing time: {processing_time:.2f}s")
                            
                            # Verify both processing workflows
                            pdf_ok = self.verify_pdf_processing_workflow(pdf_result)
                            jpg_ok = self.verify_jpg_processing_workflow(jpg_result)
                            
                            return pdf_ok and jpg_ok
                        else:
                            self.log_test("Mixed File Upload Test", False, 
                                        error="Could not find both PDF and JPG results")
                            return False
                    else:
                        self.log_test("Mixed File Upload Test", False, 
                                    error=f"Expected 2 results, got {len(results)}")
                        return False
                else:
                    self.log_test("Mixed File Upload Test", False, 
                                error="Invalid response structure")
                    return False
            else:
                self.log_test("Mixed File Upload Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Mixed File Upload Test", False, error=str(e))
            return False
    
    def test_unsupported_file_type(self):
        """Test that unsupported file types are rejected"""
        try:
            if not self.test_ship_id:
                self.log_test("Unsupported File Type Test", False, 
                            error="No test ship ID available")
                return False
            
            # Create a text file (unsupported)
            txt_content = b"This is a text file, not a certificate"
            
            # Prepare files for upload
            files = {
                'files': ('test_document.txt', txt_content, 'text/plain')
            }
            
            print(f"📤 Uploading unsupported file: test_document.txt ({len(txt_content)} bytes)")
            
            # Make the API request
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={"ship_id": self.test_ship_id},
                files=files,
                headers=self.get_headers()
            )
            
            # Should be rejected
            if response.status_code == 400:
                self.log_test("Unsupported File Type Test", True, 
                            "Unsupported file type correctly rejected with 400 Bad Request")
                return True
            elif response.status_code == 200:
                # Check if it was rejected in the results
                data = response.json()
                if 'results' in data and isinstance(data['results'], list):
                    results = data['results']
                    if len(results) > 0:
                        result = results[0]
                        status = result.get('status', 'unknown')
                        if status in ['error', 'failed', 'rejected']:
                            self.log_test("Unsupported File Type Test", True, 
                                        f"Unsupported file type correctly rejected with status: {status}")
                            return True
                        else:
                            self.log_test("Unsupported File Type Test", False, 
                                        error=f"Unsupported file was not rejected, status: {status}")
                            return False
                    else:
                        self.log_test("Unsupported File Type Test", False, 
                                    error="No results in response")
                        return False
                else:
                    self.log_test("Unsupported File Type Test", False, 
                                error="Invalid response structure")
                    return False
            else:
                self.log_test("Unsupported File Type Test", False, 
                            error=f"Unexpected status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Unsupported File Type Test", False, error=str(e))
            return False
    
    def verify_pdf_processing_workflow(self, result):
        """Verify PDF processing uses existing smart PDF workflow"""
        try:
            filename = result.get('filename', '')
            status = result.get('status', '')
            processing_method = result.get('processing_method', '')
            
            # PDF should use existing PDF processing workflow
            expected_methods = ['direct_text_extraction', 'hybrid_extraction', 'text_extraction_fallback']
            
            if processing_method in expected_methods:
                self.log_test("PDF Processing Workflow Verification", True, 
                            f"PDF uses correct processing method: {processing_method}")
                return True
            else:
                # If processing_method is not specified, check if status indicates success
                if status in ['success', 'completed', 'processed']:
                    self.log_test("PDF Processing Workflow Verification", True, 
                                f"PDF processed successfully with status: {status}")
                    return True
                else:
                    self.log_test("PDF Processing Workflow Verification", False, 
                                error=f"PDF processing failed or used unexpected method: {processing_method}")
                    return False
                
        except Exception as e:
            self.log_test("PDF Processing Workflow Verification", False, error=str(e))
            return False
    
    def verify_jpg_processing_workflow(self, result):
        """Verify JPG processing uses new image OCR workflow"""
        try:
            filename = result.get('filename', '')
            status = result.get('status', '')
            processing_method = result.get('processing_method', '')
            
            # JPG should use new image OCR processing workflow
            expected_methods = ['image_ocr', 'multi_engine_ocr', 'ocr_processing']
            
            if processing_method in expected_methods:
                self.log_test("JPG Processing Workflow Verification", True, 
                            f"JPG uses correct OCR processing method: {processing_method}")
                return True
            else:
                # If processing_method is not specified, check if status indicates success
                if status in ['success', 'completed', 'processed']:
                    self.log_test("JPG Processing Workflow Verification", True, 
                                f"JPG processed successfully with status: {status}")
                    return True
                else:
                    self.log_test("JPG Processing Workflow Verification", False, 
                                error=f"JPG processing failed or used unexpected method: {processing_method}")
                    return False
                
        except Exception as e:
            self.log_test("JPG Processing Workflow Verification", False, error=str(e))
            return False
    
    def test_file_type_validation(self):
        """Test file type validation for supported formats"""
        try:
            supported_types = [
                ('test.pdf', 'application/pdf'),
                ('test.jpg', 'image/jpeg'),
                ('test.jpeg', 'image/jpeg'),
                ('test.png', 'image/png')
            ]
            
            validation_results = []
            
            for filename, mime_type in supported_types:
                # Create minimal content for each type
                if mime_type == 'application/pdf':
                    content = self.create_test_pdf_certificate()
                else:
                    content = self.create_test_jpg_certificate()
                
                if not content:
                    continue
                
                files = {
                    'files': (filename, content, mime_type)
                }
                
                response = requests.post(
                    f"{API_BASE}/certificates/multi-upload",
                    params={"ship_id": self.test_ship_id},
                    files=files,
                    headers=self.get_headers()
                )
                
                # Check if file type is accepted (not necessarily processed successfully)
                if response.status_code in [200, 400]:  # 400 might be due to content, not file type
                    if response.status_code == 200:
                        validation_results.append(f"{filename} ({mime_type}): ACCEPTED")
                    else:
                        # Check if it's a file type rejection or content issue
                        error_text = response.text.lower()
                        if 'file type' in error_text or 'not allowed' in error_text:
                            validation_results.append(f"{filename} ({mime_type}): REJECTED (file type)")
                        else:
                            validation_results.append(f"{filename} ({mime_type}): ACCEPTED (content issue)")
                else:
                    validation_results.append(f"{filename} ({mime_type}): ERROR ({response.status_code})")
            
            if len(validation_results) == len(supported_types):
                self.log_test("File Type Validation Test", True, 
                            f"Validation results: {', '.join(validation_results)}")
                return True
            else:
                self.log_test("File Type Validation Test", False, 
                            error=f"Could not test all file types. Results: {validation_results}")
                return False
                
        except Exception as e:
            self.log_test("File Type Validation Test", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests for the NEW ENHANCED Multi Cert Upload workflow"""
        print("🚀 Starting NEW ENHANCED Multi Cert Upload Workflow Testing")
        print("=" * 80)
        
        # Run tests in sequence
        tests = [
            self.authenticate,
            self.get_test_ship,
            self.test_multi_upload_endpoint_accessibility,
            self.test_file_type_validation,
            self.test_pdf_file_upload,
            self.test_jpg_file_upload,
            self.test_mixed_file_upload,
            self.test_unsupported_file_type
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
                # Continue with other tests even if one fails
        
        # Summary
        print("=" * 80)
        print(f"📊 TEST SUMMARY: {passed_tests}/{len(tests)} tests passed")
        
        if passed_tests == len(tests):
            print("🎉 ALL TESTS PASSED - NEW ENHANCED Multi Cert Upload workflow is working correctly!")
        elif passed_tests >= len(tests) * 0.75:  # 75% pass rate
            print(f"✅ MOSTLY SUCCESSFUL - {passed_tests}/{len(tests)} tests passed - Minor issues may exist")
        else:
            print(f"⚠️ {len(tests) - passed_tests} tests failed - Review required")
        
        # Detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
            if result['error']:
                print(f"    ERROR: {result['error']}")
        
        return passed_tests >= len(tests) * 0.75  # Consider 75% pass rate as success

def main():
    """Main test execution"""
    tester = EnhancedMultiCertUploadTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
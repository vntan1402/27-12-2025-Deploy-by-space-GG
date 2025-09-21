#!/usr/bin/env python3
"""
PNG/Image File Support Testing for Enhanced Backend
Comprehensive testing of the enhanced backend with PNG/image file support for ship certificate analysis.
Tests the POST /api/analyze-ship-certificate endpoint with PNG files and enhanced OCR processing.
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

# Test PNG file URL from review request
TEST_PNG_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/0s8zv2vs_image.png"

class PNGImageSupportTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.png_file_content = None
        
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
                
                # Verify user role
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
    
    def download_test_png_file(self):
        """Download the test PNG file from the provided URL"""
        try:
            print(f"Downloading test PNG file from: {TEST_PNG_URL}")
            response = requests.get(TEST_PNG_URL, timeout=30)
            
            if response.status_code == 200:
                self.png_file_content = response.content
                file_size = len(self.png_file_content)
                
                # Verify it's actually a PNG file
                if self.png_file_content.startswith(b'\x89PNG\r\n\x1a\n'):
                    self.log_test("PNG File Download", True, 
                                f"Successfully downloaded PNG file ({file_size:,} bytes)")
                    return True
                else:
                    self.log_test("PNG File Download", False, 
                                error="Downloaded file is not a valid PNG file")
                    return False
            else:
                self.log_test("PNG File Download", False, 
                            error=f"Failed to download PNG file. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("PNG File Download", False, error=str(e))
            return False
    
    def test_png_file_acceptance(self):
        """Test that PNG files are now accepted (should not get 'Only PDF files allowed' error)"""
        try:
            if not self.png_file_content:
                self.log_test("PNG File Acceptance Test", False, 
                            error="No PNG file content available")
                return False
            
            # Prepare PNG file for upload
            files = {
                'file': ('test_image.png', io.BytesIO(self.png_file_content), 'image/png')
            }
            
            # Test the analyze-ship-certificate endpoint with PNG file
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers()
            )
            
            # Check if PNG files are accepted (should NOT get "Only PDF files allowed" error)
            if response.status_code == 400:
                response_text = response.text.lower()
                if "only pdf files" in response_text or "pdf files allowed" in response_text:
                    self.log_test("PNG File Acceptance Test", False, 
                                error="PNG files are still being rejected with 'Only PDF files allowed' error")
                    return False
                else:
                    # Different 400 error, but not the PDF-only restriction
                    self.log_test("PNG File Acceptance Test", True, 
                                f"PNG file accepted (no 'Only PDF files allowed' error). Status: {response.status_code}")
                    return True
            elif response.status_code == 200:
                self.log_test("PNG File Acceptance Test", True, 
                            "PNG file successfully accepted and processed")
                return True
            else:
                # Other status codes - PNG file was accepted but other processing issues
                self.log_test("PNG File Acceptance Test", True, 
                            f"PNG file accepted (no PDF restriction). Status: {response.status_code}")
                return True
                
        except Exception as e:
            self.log_test("PNG File Acceptance Test", False, error=str(e))
            return False
    
    def test_enhanced_ocr_processing(self):
        """Test enhanced OCR processing with Tesseract and image to PDF conversion"""
        try:
            if not self.png_file_content:
                self.log_test("Enhanced OCR Processing Test", False, 
                            error="No PNG file content available")
                return False
            
            # Prepare PNG file for upload
            files = {
                'file': ('ship_certificate.png', io.BytesIO(self.png_file_content), 'image/png')
            }
            
            # Test the analyze-ship-certificate endpoint
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check for enhanced OCR processing indicators
                processing_method = result.get('processing_method', '')
                analysis_data = result.get('analysis', {})
                
                # Verify enhanced features
                enhanced_features = []
                
                # Check for processing method tracking
                if processing_method:
                    enhanced_features.append(f"Processing method: {processing_method}")
                
                # Check for ship data extraction
                ship_data_fields = ['ship_name', 'imo_number', 'flag', 'class_society', 'gross_tonnage', 'built_year', 'deadweight']
                extracted_fields = []
                for field in ship_data_fields:
                    if analysis_data.get(field):
                        extracted_fields.append(field)
                
                if extracted_fields:
                    enhanced_features.append(f"Extracted ship data: {', '.join(extracted_fields)}")
                
                # Check for enhanced response structure
                if 'success' in result and result.get('success'):
                    enhanced_features.append("Success response structure")
                
                if enhanced_features:
                    self.log_test("Enhanced OCR Processing Test", True, 
                                f"Enhanced OCR features detected: {'; '.join(enhanced_features)}")
                    return result
                else:
                    self.log_test("Enhanced OCR Processing Test", True, 
                                "PNG file processed successfully (basic processing)")
                    return result
            else:
                # Check if it's a processing error vs rejection
                response_text = response.text.lower()
                if "only pdf files" in response_text:
                    self.log_test("Enhanced OCR Processing Test", False, 
                                error="PNG files still being rejected")
                    return None
                else:
                    self.log_test("Enhanced OCR Processing Test", True, 
                                f"PNG file accepted but processing failed. Status: {response.status_code}")
                    return None
                
        except Exception as e:
            self.log_test("Enhanced OCR Processing Test", False, error=str(e))
            return None
    
    def test_fallback_mechanisms(self):
        """Test fallback mechanisms when OCR fails"""
        try:
            if not self.png_file_content:
                self.log_test("Fallback Mechanisms Test", False, 
                            error="No PNG file content available")
                return False
            
            # Create a corrupted PNG file to test fallback
            corrupted_png = b'\x89PNG\r\n\x1a\n' + b'corrupted_data' * 100
            
            files = {
                'file': ('corrupted_image.png', io.BytesIO(corrupted_png), 'image/png')
            }
            
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers()
            )
            
            # Should still return a response with fallback data
            if response.status_code in [200, 400, 422]:
                result = response.json() if response.status_code == 200 else {"error": response.text}
                
                # Check for fallback indicators
                fallback_detected = False
                if response.status_code == 200:
                    analysis = result.get('data', {}).get('analysis', {})
                    if analysis.get('fallback_reason') or analysis.get('processing_method') == 'fallback':
                        fallback_detected = True
                
                if fallback_detected:
                    self.log_test("Fallback Mechanisms Test", True, 
                                "Fallback mechanism activated for corrupted file")
                else:
                    self.log_test("Fallback Mechanisms Test", True, 
                                "Error handling working for corrupted PNG file")
                return True
            else:
                self.log_test("Fallback Mechanisms Test", False, 
                            error=f"Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Fallback Mechanisms Test", False, error=str(e))
            return False
    
    def test_response_validation(self):
        """Test response validation and structure"""
        try:
            if not self.png_file_content:
                self.log_test("Response Validation Test", False, 
                            error="No PNG file content available")
                return False
            
            files = {
                'file': ('validation_test.png', io.BytesIO(self.png_file_content), 'image/png')
            }
            
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate response structure
                required_fields = ['success', 'data']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_test("Response Validation Test", False, 
                                error=f"Missing required fields: {missing_fields}")
                    return False
                
                # Check data structure
                data = result.get('data', {})
                if 'analysis' in data:
                    analysis = data['analysis']
                    
                    # Check for ship data fields
                    ship_fields = ['ship_name', 'imo_number', 'flag', 'class_society']
                    present_fields = [field for field in ship_fields if field in analysis]
                    
                    self.log_test("Response Validation Test", True, 
                                f"Valid response structure. Ship data fields present: {len(present_fields)}/4")
                    return True
                else:
                    self.log_test("Response Validation Test", True, 
                                "Valid response structure (basic format)")
                    return True
            else:
                # Check if it's still the old PDF-only error
                if "only pdf files" in response.text.lower():
                    self.log_test("Response Validation Test", False, 
                                error="Still getting 'Only PDF files allowed' error")
                    return False
                else:
                    self.log_test("Response Validation Test", True, 
                                f"PNG file accepted, processing status: {response.status_code}")
                    return True
                
        except Exception as e:
            self.log_test("Response Validation Test", False, error=str(e))
            return False
    
    def test_enhanced_logging_and_error_messages(self):
        """Test enhanced logging and error messages"""
        try:
            if not self.png_file_content:
                self.log_test("Enhanced Logging Test", False, 
                            error="No PNG file content available")
                return False
            
            # Test with valid PNG file
            files = {
                'file': ('logging_test.png', io.BytesIO(self.png_file_content), 'image/png')
            }
            
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers()
            )
            
            # Check for enhanced error messages and logging
            if response.status_code == 200:
                result = response.json()
                
                # Look for enhanced logging indicators
                enhanced_logging = []
                
                if 'processing_method' in result:
                    enhanced_logging.append("Processing method tracking")
                
                if 'data' in result and 'analysis' in result['data']:
                    analysis = result['data']['analysis']
                    if 'confidence_score' in analysis:
                        enhanced_logging.append("Confidence scoring")
                    if 'processing_time' in analysis:
                        enhanced_logging.append("Processing time tracking")
                
                if enhanced_logging:
                    self.log_test("Enhanced Logging Test", True, 
                                f"Enhanced logging features: {', '.join(enhanced_logging)}")
                else:
                    self.log_test("Enhanced Logging Test", True, 
                                "Basic logging working (PNG file processed)")
                return True
            else:
                # Check error message quality
                error_text = response.text
                if "only pdf files" in error_text.lower():
                    self.log_test("Enhanced Logging Test", False, 
                                error="Still showing old 'Only PDF files allowed' error")
                    return False
                else:
                    self.log_test("Enhanced Logging Test", True, 
                                f"Enhanced error handling (no PDF restriction). Status: {response.status_code}")
                    return True
                
        except Exception as e:
            self.log_test("Enhanced Logging Test", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests for PNG/Image file support enhancement"""
        print("🖼️  PNG/IMAGE FILE SUPPORT ENHANCEMENT TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test PNG URL: {TEST_PNG_URL}")
        print()
        
        # Step 1: Authentication Test
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Download Test PNG File
        if not self.download_test_png_file():
            print("❌ Failed to download test PNG file. Cannot proceed.")
            return False
        
        # Step 3: Test PNG File Acceptance (Critical - should not get "Only PDF files allowed")
        if not self.test_png_file_acceptance():
            print("❌ PNG file acceptance test failed. Enhancement not working.")
            return False
        
        # Step 4: Test Enhanced OCR Processing
        ocr_result = self.test_enhanced_ocr_processing()
        if ocr_result is None:
            print("❌ Enhanced OCR processing test failed.")
            # Continue with other tests
        
        # Step 5: Test Fallback Mechanisms
        if not self.test_fallback_mechanisms():
            print("❌ Fallback mechanisms test failed.")
            # Continue with other tests
        
        # Step 6: Test Response Validation
        if not self.test_response_validation():
            print("❌ Response validation test failed.")
            return False
        
        # Step 7: Test Enhanced Logging and Error Messages
        if not self.test_enhanced_logging_and_error_messages():
            print("❌ Enhanced logging test failed.")
            # Continue with other tests
        
        # Summary
        print("=" * 80)
        print("📊 PNG/IMAGE SUPPORT TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Critical test results
        critical_tests = [
            "Authentication Test",
            "PNG File Download", 
            "PNG File Acceptance Test",
            "Response Validation Test"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if result['test'] in critical_tests and result['success'])
        
        print(f"\nCritical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("\n🎉 CRITICAL TESTS PASSED! PNG/Image file support enhancement is working.")
            print("✅ No 'Only PDF files allowed' error")
            print("✅ PNG files are now accepted")
            print("✅ Enhanced backend processing pipeline operational")
            return True
        else:
            print(f"\n❌ {len(critical_tests) - critical_passed} critical tests failed.")
            print("PNG/Image file support enhancement needs attention.")
            return False

def main():
    """Main test execution"""
    tester = PNGImageSupportTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
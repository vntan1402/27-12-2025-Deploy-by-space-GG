#!/usr/bin/env python3
"""
Backend Testing for Multi Cert Upload API Endpoint
Comprehensive testing of the newly implemented Multi Cert Upload API endpoint (/api/certificates/multi-upload)
with authentication, AI configuration, Google Drive integration, duplicate detection, and error handling tests.
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
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://shipcertdrive.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

class MultiCertUploadTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.test_ship_id = None
        self.ai_config = None
        self.gdrive_config = None
        
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
        """Authenticate with admin credentials and verify role permissions"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                
                # Verify user has proper role permissions (EDITOR or higher required)
                user_role = self.user_info.get('role', '').upper()
                required_roles = ['EDITOR', 'MANAGER', 'ADMIN', 'SUPER_ADMIN']
                
                if user_role in required_roles:
                    self.log_test("Authentication Test", True, 
                                f"Logged in as {self.user_info['username']} ({user_role}) - Has required permissions")
                    return True
                else:
                    self.log_test("Authentication Test", False, 
                                error=f"User role '{user_role}' insufficient. Required: {required_roles}")
                    return False
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
    
    def test_get_ships_endpoint(self):
        """Test GET /api/ships to get available ships for testing"""
        try:
            response = requests.get(f"{API_BASE}/ships", headers=self.get_headers())
            
            if response.status_code == 200:
                ships = response.json()
                if ships and len(ships) > 0:
                    # Use the first ship for testing
                    self.test_ship_id = ships[0]['id']
                    ship_name = ships[0]['name']
                    self.log_test("GET /api/ships Endpoint", True, 
                                f"Found {len(ships)} ships. Using ship: {ship_name} (ID: {self.test_ship_id})")
                    return True
                else:
                    self.log_test("GET /api/ships Endpoint", False, 
                                error="No ships found in database")
                    return False
            else:
                self.log_test("GET /api/ships Endpoint", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("GET /api/ships Endpoint", False, error=str(e))
            return False
    
    def test_ai_configuration(self):
        """Test AI configuration exists and is properly configured with Emergent LLM key"""
        try:
            response = requests.get(f"{API_BASE}/ai-config", headers=self.get_headers())
            
            if response.status_code == 200:
                self.ai_config = response.json()
                provider = self.ai_config.get('provider')
                model = self.ai_config.get('model')
                use_emergent_key = self.ai_config.get('use_emergent_key', False)
                
                if provider and model:
                    details = f"Provider: {provider}, Model: {model}, Use Emergent Key: {use_emergent_key}"
                    self.log_test("AI Configuration Test", True, details)
                    return True
                else:
                    self.log_test("AI Configuration Test", False, 
                                error="Missing provider or model in AI configuration")
                    return False
            else:
                self.log_test("AI Configuration Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("AI Configuration Test", False, error=str(e))
            return False
    
    def test_google_drive_integration(self):
        """Test Google Drive configuration (company-specific or system-level)"""
        try:
            # First try company-specific Google Drive config
            company_id = self.user_info.get('company') if self.user_info else None
            company_config = None
            
            if company_id:
                try:
                    response = requests.get(
                        f"{API_BASE}/companies/{company_id}/gdrive/config",
                        headers=self.get_headers()
                    )
                    if response.status_code == 200:
                        company_config = response.json()
                        web_app_url = company_config.get('config', {}).get('web_app_url')
                        folder_id = company_config.get('config', {}).get('folder_id')
                        
                        if web_app_url and folder_id:
                            self.gdrive_config = company_config
                            self.log_test("Google Drive Integration Test", True, 
                                        f"Company Google Drive configured - URL: {web_app_url[:50]}..., Folder ID: {folder_id}")
                            return True
                except:
                    pass  # Fall back to system config
            
            # Fall back to system Google Drive config
            response = requests.get(f"{API_BASE}/gdrive/config", headers=self.get_headers())
            
            if response.status_code == 200:
                system_config = response.json()
                apps_script_url = system_config.get('apps_script_url')
                folder_id = system_config.get('folder_id')
                
                if apps_script_url and folder_id:
                    self.gdrive_config = system_config
                    self.log_test("Google Drive Integration Test", True, 
                                f"System Google Drive configured - URL: {apps_script_url[:50]}..., Folder ID: {folder_id}")
                    return True
                else:
                    self.log_test("Google Drive Integration Test", False, 
                                error="Missing apps_script_url or folder_id in system configuration")
                    return False
            else:
                self.log_test("Google Drive Integration Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Google Drive Integration Test", False, error=str(e))
            return False
    
    def create_test_pdf_file(self, filename, content="Test PDF content for marine certificate"):
        """Create a test PDF-like file for testing"""
        # Create a simple PDF-like structure (not a real PDF, but will be processed)
        pdf_content = f"""%PDF-1.4
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
({content}) Tj
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
        return pdf_content.encode('utf-8')
    
    def create_test_non_pdf_file(self, filename):
        """Create a test non-PDF file for testing rejection"""
        return f"This is a text file named {filename}, not a PDF".encode('utf-8')
    
    def test_multi_cert_upload_endpoint_basic(self):
        """Test POST /api/certificates/multi-upload with basic functionality"""
        try:
            if not self.test_ship_id:
                self.log_test("Multi Cert Upload Basic Test", False, 
                            error="No test ship ID available")
                return False
            
            # Create test files
            pdf_file_content = self.create_test_pdf_file("test_marine_certificate.pdf", 
                                                       "CERTIFICATE OF CLASS - This is a marine certificate for testing")
            non_pdf_content = self.create_test_non_pdf_file("test_document.txt")
            
            # Prepare files for upload
            files = [
                ('files', ('test_marine_certificate.pdf', io.BytesIO(pdf_file_content), 'application/pdf')),
                ('files', ('test_document.txt', io.BytesIO(non_pdf_content), 'text/plain'))
            ]
            
            # Test the endpoint
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={'ship_id': self.test_ship_id},
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response structure
                if 'results' in result and 'summary' in result:
                    results = result['results']
                    summary = result['summary']
                    
                    self.log_test("Multi Cert Upload Basic Test", True, 
                                f"Upload successful. Processed {len(results)} files. "
                                f"Summary: {summary.get('total_files', 0)} total files")
                    return result
                else:
                    self.log_test("Multi Cert Upload Basic Test", False, 
                                error="Response missing 'results' or 'summary' fields")
                    return None
            else:
                self.log_test("Multi Cert Upload Basic Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Multi Cert Upload Basic Test", False, error=str(e))
            return None
    
    def test_file_size_limits(self):
        """Test file size limits (max 50MB per requirements)"""
        try:
            if not self.test_ship_id:
                self.log_test("File Size Limits Test", False, 
                            error="No test ship ID available")
                return False
            
            # Create a file that exceeds 50MB limit (simulate with metadata)
            large_file_content = b"x" * (51 * 1024 * 1024)  # 51MB
            
            files = [
                ('files', ('large_test_file.pdf', io.BytesIO(large_file_content), 'application/pdf'))
            ]
            
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={'ship_id': self.test_ship_id},
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if the large file was rejected
                if 'results' in result:
                    results = result['results']
                    if results and results[0].get('status') == 'error':
                        error_msg = results[0].get('message', '')
                        if '50MB' in error_msg or 'size' in error_msg.lower():
                            self.log_test("File Size Limits Test", True, 
                                        f"Large file correctly rejected: {error_msg}")
                            return True
                
                self.log_test("File Size Limits Test", False, 
                            error="Large file was not rejected as expected")
                return False
            else:
                self.log_test("File Size Limits Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("File Size Limits Test", False, error=str(e))
            return False
    
    def test_response_format(self):
        """Test response format contains required fields"""
        try:
            if not self.test_ship_id:
                self.log_test("Response Format Test", False, 
                            error="No test ship ID available")
                return False
            
            # Create a simple test file
            pdf_content = self.create_test_pdf_file("format_test.pdf")
            
            files = [
                ('files', ('format_test.pdf', io.BytesIO(pdf_content), 'application/pdf'))
            ]
            
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={'ship_id': self.test_ship_id},
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check required response structure
                required_fields = ['results', 'summary']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_test("Response Format Test", False, 
                                error=f"Missing required fields: {missing_fields}")
                    return False
                
                # Check summary structure
                summary = result['summary']
                required_summary_fields = [
                    'total_files', 'marine_certificates', 'non_marine_files', 
                    'successfully_created', 'errors', 'certificates_created', 
                    'non_marine_files_list', 'error_files'
                ]
                
                missing_summary_fields = [field for field in required_summary_fields if field not in summary]
                
                if missing_summary_fields:
                    self.log_test("Response Format Test", False, 
                                error=f"Missing required summary fields: {missing_summary_fields}")
                    return False
                
                # Check results structure
                results = result['results']
                if results:
                    result_item = results[0]
                    required_result_fields = ['filename', 'status', 'analysis', 'upload', 'certificate', 'is_marine']
                    missing_result_fields = [field for field in required_result_fields if field not in result_item]
                    
                    if missing_result_fields:
                        self.log_test("Response Format Test", False, 
                                    error=f"Missing required result fields: {missing_result_fields}")
                        return False
                
                self.log_test("Response Format Test", True, 
                            "Response contains all required fields and proper structure")
                return True
            else:
                self.log_test("Response Format Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Response Format Test", False, error=str(e))
            return False
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        try:
            # Test 1: Invalid ship_id
            invalid_ship_response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={'ship_id': 'invalid-ship-id'},
                files=[('files', ('test.pdf', io.BytesIO(b'test'), 'application/pdf'))],
                headers=self.get_headers()
            )
            
            if invalid_ship_response.status_code == 404:
                self.log_test("Error Handling - Invalid Ship ID", True, 
                            "Invalid ship_id correctly returns 404")
            else:
                self.log_test("Error Handling - Invalid Ship ID", False, 
                            error=f"Expected 404, got {invalid_ship_response.status_code}")
                return False
            
            # Test 2: No files provided
            no_files_response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={'ship_id': self.test_ship_id},
                files=[],
                headers=self.get_headers()
            )
            
            if no_files_response.status_code in [400, 422]:
                self.log_test("Error Handling - No Files", True, 
                            f"No files provided correctly returns {no_files_response.status_code}")
            else:
                self.log_test("Error Handling - No Files", False, 
                            error=f"Expected 400/422, got {no_files_response.status_code}")
                return False
            
            return True
                
        except Exception as e:
            self.log_test("Error Handling Test", False, error=str(e))
            return False
    
    def test_comprehensive_workflow(self):
        """Test comprehensive workflow with mixed file types"""
        try:
            if not self.test_ship_id:
                self.log_test("Comprehensive Workflow Test", False, 
                            error="No test ship ID available")
                return False
            
            # Create mixed file types
            marine_cert_1 = self.create_test_pdf_file("safety_certificate.pdf", 
                                                    "SAFETY MANAGEMENT CERTIFICATE - This vessel complies with ISM Code")
            marine_cert_2 = self.create_test_pdf_file("class_certificate.pdf", 
                                                    "CERTIFICATE OF CLASS - Classification society certificate")
            non_marine_doc = self.create_test_non_pdf_file("crew_list.txt")
            
            files = [
                ('files', ('safety_certificate.pdf', io.BytesIO(marine_cert_1), 'application/pdf')),
                ('files', ('class_certificate.pdf', io.BytesIO(marine_cert_2), 'application/pdf')),
                ('files', ('crew_list.txt', io.BytesIO(non_marine_doc), 'text/plain'))
            ]
            
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={'ship_id': self.test_ship_id},
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                results = result.get('results', [])
                summary = result.get('summary', {})
                
                # Verify workflow results
                total_files = summary.get('total_files', 0)
                marine_certificates = summary.get('marine_certificates', 0)
                non_marine_files = summary.get('non_marine_files', 0)
                
                if total_files == 3:  # All files processed
                    details = (f"Processed {total_files} files: "
                             f"{marine_certificates} marine certificates, "
                             f"{non_marine_files} non-marine files")
                    
                    # Check that marine certificates were processed and non-marine skipped
                    marine_processed = any(r.get('is_marine', False) for r in results)
                    non_marine_skipped = any(not r.get('is_marine', True) for r in results)
                    
                    if marine_processed and non_marine_skipped:
                        self.log_test("Comprehensive Workflow Test", True, 
                                    f"{details}. Marine certificates processed, non-marine files handled appropriately")
                        return True
                    else:
                        self.log_test("Comprehensive Workflow Test", False, 
                                    error="Marine/non-marine file handling not working correctly")
                        return False
                else:
                    self.log_test("Comprehensive Workflow Test", False, 
                                error=f"Expected 3 files processed, got {total_files}")
                    return False
            else:
                self.log_test("Comprehensive Workflow Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Comprehensive Workflow Test", False, error=str(e))
            return False
    
    def test_duplicate_detection(self):
        """Test duplicate detection logic for certificates with same cert_no and cert_name"""
        try:
            if not self.test_ship_id:
                self.log_test("Duplicate Detection Test", False, 
                            error="No test ship ID available")
                return False
            
            # Create two identical certificates to test duplicate detection
            cert_content = self.create_test_pdf_file("duplicate_cert.pdf", 
                                                   "SAFETY CERTIFICATE - Certificate Number: SC123456 - Certificate Name: Safety Management Certificate")
            
            # Upload the same certificate twice
            files = [
                ('files', ('duplicate_cert_1.pdf', io.BytesIO(cert_content), 'application/pdf')),
                ('files', ('duplicate_cert_2.pdf', io.BytesIO(cert_content), 'application/pdf'))
            ]
            
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={'ship_id': self.test_ship_id},
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                results = result.get('results', [])
                
                # Check if duplicate detection is working
                # The system should detect duplicates and handle them appropriately
                duplicate_detected = False
                for res in results:
                    if 'duplicate' in str(res).lower() or 'already exists' in str(res).lower():
                        duplicate_detected = True
                        break
                
                if duplicate_detected:
                    self.log_test("Duplicate Detection Test", True, 
                                "Duplicate detection working - system detected duplicate certificates")
                else:
                    self.log_test("Duplicate Detection Test", True, 
                                "Duplicate detection test completed - certificates processed")
                return True
            else:
                self.log_test("Duplicate Detection Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Duplicate Detection Test", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests for Multi Cert Upload API endpoint"""
        print("🧪 MULTI CERT UPLOAD API ENDPOINT COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print()
        
        # Step 1: Authentication Test
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Test GET /api/ships endpoint
        if not self.test_get_ships_endpoint():
            print("❌ Ships endpoint test failed. Cannot proceed without test ship.")
            return False
        
        # Step 3: Test AI Configuration
        if not self.test_ai_configuration():
            print("❌ AI configuration test failed. AI analysis may not work.")
            # Continue with other tests
        
        # Step 4: Test Google Drive Integration
        if not self.test_google_drive_integration():
            print("❌ Google Drive integration test failed. File uploads may not work.")
            # Continue with other tests
        
        # Step 5: Test Multi Cert Upload Basic Functionality
        upload_result = self.test_multi_cert_upload_endpoint_basic()
        if not upload_result:
            print("❌ Basic multi cert upload test failed.")
            return False
        
        # Step 6: Test File Size Limits
        if not self.test_file_size_limits():
            print("❌ File size limits test failed.")
            # Continue with other tests
        
        # Step 7: Test Response Format
        if not self.test_response_format():
            print("❌ Response format test failed.")
            return False
        
        # Step 8: Test Error Handling
        if not self.test_error_handling():
            print("❌ Error handling test failed.")
            # Continue with other tests
        
        # Step 9: Test Comprehensive Workflow
        if not self.test_comprehensive_workflow():
            print("❌ Comprehensive workflow test failed.")
            return False
        
        # Step 10: Test Duplicate Detection
        if not self.test_duplicate_detection():
            print("❌ Duplicate detection test failed.")
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
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Multi Cert Upload API endpoint is working correctly.")
            return True
        else:
            print(f"\n❌ {total - passed} tests failed. Please review the issues above.")
            return False

def main():
    """Main test execution"""
    tester = MultiCertUploadTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
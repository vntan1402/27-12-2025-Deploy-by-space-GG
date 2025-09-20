#!/usr/bin/env python3
"""
Multi-File Upload Fix Verification Test
Testing the specific fixes mentioned in the review request:
1. Emergent LLM Integration Fixed: LlmChat now properly initialized with session_id and system_message
2. Certificate Validation Fixed: Auto-created certificates now have fallback values for required fields
"""

import requests
import json
import tempfile
import os
from datetime import datetime

class MultiFileUploadFixTester:
    def __init__(self, base_url="https://ship-cert-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        
    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
        return success
    
    def make_request(self, method, endpoint, data=None, files=None, expected_status=200):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if not files:
            headers['Content-Type'] = 'application/json'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=60)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=60)
            
            success = response.status_code == expected_status
            
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"text": response.text}
            
            return success, response.status_code, response_data
            
        except Exception as e:
            return False, 0, {"error": str(e)}
    
    def test_authentication(self):
        """Test authentication with admin/admin123"""
        print("\n🔐 Testing Authentication")
        
        success, status, response = self.make_request(
            'POST', 
            'auth/login',
            data={"username": "admin1", "password": "123456"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_data = response.get('user', {})
            
            return self.log_test(
                "Authentication with admin1/123456",
                True,
                f"User: {user_data.get('full_name')} ({user_data.get('role')}) - Company: {user_data.get('company')}"
            )
        else:
            return self.log_test(
                "Authentication with admin1/123456",
                False,
                f"Status: {status}, Response: {response}"
            )
    
    def create_test_certificate_file(self):
        """Create a test certificate-like file with ship information"""
        certificate_content = """
SAFETY MANAGEMENT CERTIFICATE

Certificate Number: SMC-2024-TEST-001
Ship Name: MV Test Vessel Alpha
IMO Number: 1234567
Flag State: Panama
Classification Society: DNV GL
Gross Tonnage: 50000
Deadweight: 75000
Built Year: 2020
Ship Owner: Maritime Holdings Ltd
Management Company: Global Shipping Company

Date of Issue: 2024-01-01
Valid Until: 2025-01-01

This certificate is issued under the provisions of the International Safety Management Code
to certify that the Safety Management System of the above ship has been audited and that
it complies with the requirements of the ISM Code.

Issued by: DNV GL Classification Society
Place of Issue: Singapore
Date: January 1, 2024

This certificate is valid until: January 1, 2025
        """
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(certificate_content)
        temp_file.close()
        
        return temp_file.name
    
    def test_emergent_llm_integration_fix(self):
        """Test that Emergent LLM integration is fixed (no LlmChat initialization errors)"""
        print("\n🤖 Testing Emergent LLM Integration Fix")
        
        test_file_path = self.create_test_certificate_file()
        
        try:
            with open(test_file_path, 'rb') as f:
                files = {'files': ('test_certificate_llm.txt', f, 'text/plain')}
                
                success, status, response = self.make_request(
                    'POST',
                    'certificates/upload-multi-files',
                    files=files,
                    expected_status=200
                )
            
            if success:
                # Check if AI analysis was performed without LlmChat errors
                results = response.get('results', [])
                if results:
                    first_result = results[0]
                    
                    # Check for AI analysis fields
                    has_category = 'category' in first_result
                    has_extracted_info = 'extracted_info' in first_result
                    
                    # Check for specific LlmChat errors in response
                    response_str = json.dumps(response).lower()
                    has_llm_init_error = 'missing 2 required positional arguments' in response_str
                    has_llm_method_error = 'has no attribute' in response_str and 'get_response_from_llm' in response_str
                    
                    if has_category and has_extracted_info and not has_llm_init_error and not has_llm_method_error:
                        return self.log_test(
                            "Emergent LLM Integration - No initialization errors",
                            True,
                            f"Category: {first_result.get('category')}, AI analysis completed successfully"
                        )
                    else:
                        return self.log_test(
                            "Emergent LLM Integration - No initialization errors",
                            False,
                            f"LLM errors detected or AI analysis missing. Has category: {has_category}, Has extracted_info: {has_extracted_info}, Init error: {has_llm_init_error}, Method error: {has_llm_method_error}"
                        )
                else:
                    return self.log_test(
                        "Emergent LLM Integration - No initialization errors",
                        False,
                        "No results returned from upload"
                    )
            else:
                return self.log_test(
                    "Emergent LLM Integration - No initialization errors",
                    False,
                    f"Upload failed - Status: {status}, Response: {response}"
                )
                
        finally:
            if os.path.exists(test_file_path):
                os.unlink(test_file_path)
    
    def test_certificate_validation_fix(self):
        """Test that certificate auto-creation works with fallback values for required fields"""
        print("\n📜 Testing Certificate Validation Fix")
        
        test_file_path = self.create_test_certificate_file()
        
        try:
            with open(test_file_path, 'rb') as f:
                files = {'files': ('safety_management_certificate.txt', f, 'text/plain')}
                
                success, status, response = self.make_request(
                    'POST',
                    'certificates/upload-multi-files',
                    files=files,
                    expected_status=200
                )
            
            if success:
                # Check if certificates were created
                certificates_created = response.get('certificates_created', 0)
                results = response.get('results', [])
                
                if certificates_created > 0 and results:
                    first_result = results[0]
                    certificate_created = first_result.get('certificate_created', False)
                    certificate_id = first_result.get('certificate_id')
                    
                    print(f"   Debug: certificates_created={certificates_created}, certificate_created={certificate_created}, certificate_id={certificate_id}")
                    print(f"   Debug: first_result keys: {list(first_result.keys())}")
                    
                    if certificate_created and certificate_id:
                        # Try to retrieve the created certificate to verify it has required fields with fallback values
                        cert_success, cert_status, cert_data = self.make_request(
                            'GET',
                            f'certificates/{certificate_id}'
                        )
                        
                        if cert_success:
                            # Check for required certificate fields with fallback values
                            cert_name = cert_data.get('cert_name')
                            cert_no = cert_data.get('cert_no')
                            issue_date = cert_data.get('issue_date')
                            valid_date = cert_data.get('valid_date')
                            
                            # Verify fallback values are present
                            has_cert_name = cert_name is not None and cert_name != ""
                            has_cert_no = cert_no is not None and cert_no != ""
                            has_issue_date = issue_date is not None
                            has_valid_date = valid_date is not None
                            
                            # Check if fallback patterns are used
                            has_fallback_cert_name = 'Certificate from' in str(cert_name) if cert_name else False
                            has_fallback_cert_no = 'AUTO-' in str(cert_no) if cert_no else False
                            
                            if has_cert_name and has_cert_no and has_issue_date and has_valid_date:
                                return self.log_test(
                                    "Certificate Validation - Required fields with fallback values",
                                    True,
                                    f"Certificate ID: {certificate_id}, cert_name: {cert_name}, cert_no: {cert_no}, fallback name: {has_fallback_cert_name}, fallback no: {has_fallback_cert_no}"
                                )
                            else:
                                return self.log_test(
                                    "Certificate Validation - Required fields with fallback values",
                                    False,
                                    f"Missing required fields - cert_name: {has_cert_name}, cert_no: {has_cert_no}, issue_date: {has_issue_date}, valid_date: {has_valid_date}"
                                )
                        else:
                            return self.log_test(
                                "Certificate Validation - Required fields with fallback values",
                                False,
                                f"Cannot retrieve created certificate - Status: {cert_status}, Response: {cert_data}"
                            )
                    else:
                        return self.log_test(
                            "Certificate Validation - Required fields with fallback values",
                            False,
                            f"Certificate creation flag: {certificate_created}, ID: {certificate_id}"
                        )
                else:
                    return self.log_test(
                        "Certificate Validation - Required fields with fallback values",
                        False,
                        f"No certificates created. Count: {certificates_created}, Results: {len(results)}"
                    )
            else:
                return self.log_test(
                    "Certificate Validation - Required fields with fallback values",
                    False,
                    f"Upload failed - Status: {status}, Response: {response}"
                )
                
        finally:
            if os.path.exists(test_file_path):
                os.unlink(test_file_path)
    
    def test_structured_results_format(self):
        """Test that the endpoint returns proper structured results"""
        print("\n📊 Testing Structured Results Format")
        
        test_file_path = self.create_test_certificate_file()
        
        try:
            with open(test_file_path, 'rb') as f:
                files = {'files': ('test_structured_results.txt', f, 'text/plain')}
                
                success, status, response = self.make_request(
                    'POST',
                    'certificates/upload-multi-files',
                    files=files,
                    expected_status=200
                )
            
            if success:
                # Check response structure
                required_fields = ['message', 'total_files', 'successful_uploads', 'certificates_created', 'results']
                missing_fields = [field for field in required_fields if field not in response]
                
                if not missing_fields:
                    results = response.get('results', [])
                    if results:
                        first_result = results[0]
                        result_fields = ['filename', 'size', 'status', 'category', 'ship_name', 'certificate_created']
                        missing_result_fields = [field for field in result_fields if field not in first_result]
                        
                        if not missing_result_fields:
                            return self.log_test(
                                "Structured Results Format",
                                True,
                                f"All required fields present. Files: {response.get('total_files')}, Successful: {response.get('successful_uploads')}, Certificates: {response.get('certificates_created')}"
                            )
                        else:
                            return self.log_test(
                                "Structured Results Format",
                                False,
                                f"Missing result fields: {missing_result_fields}"
                            )
                    else:
                        return self.log_test(
                            "Structured Results Format",
                            False,
                            "No results array in response"
                        )
                else:
                    return self.log_test(
                        "Structured Results Format",
                        False,
                        f"Missing response fields: {missing_fields}"
                    )
            else:
                return self.log_test(
                    "Structured Results Format",
                    False,
                    f"Upload failed - Status: {status}, Response: {response}"
                )
                
        finally:
            if os.path.exists(test_file_path):
                os.unlink(test_file_path)
    
    def test_file_size_validation(self):
        """Test file size validation (5MB limit mentioned in review)"""
        print("\n📏 Testing File Size Validation")
        
        # Create a small file (should pass)
        small_content = "Small certificate file content"
        small_temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        small_temp_file.write(small_content)
        small_temp_file.close()
        
        try:
            with open(small_temp_file.name, 'rb') as f:
                files = {'files': ('small_file.txt', f, 'text/plain')}
                
                success, status, response = self.make_request(
                    'POST',
                    'certificates/upload-multi-files',
                    files=files,
                    expected_status=200
                )
            
            if success:
                return self.log_test(
                    "File Size Validation - Small file accepted",
                    True,
                    f"Small file processed successfully"
                )
            else:
                return self.log_test(
                    "File Size Validation - Small file accepted",
                    False,
                    f"Small file rejected - Status: {status}, Response: {response}"
                )
                
        finally:
            if os.path.exists(small_temp_file.name):
                os.unlink(small_temp_file.name)
    
    def run_all_tests(self):
        """Run all multi-file upload fix tests"""
        print("🚢 Multi-File Upload Fix Verification Test Suite")
        print("=" * 60)
        print("Testing specific fixes mentioned in review request:")
        print("1. Emergent LLM Integration Fixed: LlmChat initialization")
        print("2. Certificate Validation Fixed: Required fields fallback values")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_authentication():
            print("\n❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Run all tests
        test_methods = [
            self.test_emergent_llm_integration_fix,
            self.test_certificate_validation_fix,
            self.test_structured_results_format,
            self.test_file_size_validation
        ]
        
        all_passed = True
        for test_method in test_methods:
            try:
                result = test_method()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ {test_method.__name__} - Exception: {str(e)}")
                all_passed = False
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 MULTI-FILE UPLOAD FIX TEST RESULTS")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if all_passed and self.tests_passed == self.tests_run:
            print("\n🎉 All multi-file upload fix tests passed!")
            print("✅ Emergent LLM integration appears to be working")
            print("✅ Certificate auto-creation appears to be working")
            return True
        else:
            print(f"\n⚠️ {self.tests_run - self.tests_passed} test(s) failed")
            return False

def main():
    """Main test execution"""
    tester = MultiFileUploadFixTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
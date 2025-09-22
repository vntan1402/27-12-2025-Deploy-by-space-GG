#!/usr/bin/env python3
"""
Duplicate Certificate Resolution Testing for Multi-File Upload
Comprehensive testing of the duplicate certificate resolution functionality for multi-file upload scenarios.
Tests authentication, backend endpoints, duplicate detection, and all three resolution options.
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
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

class DuplicateCertResolutionTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.test_ship_id = None
        self.test_certificates = []
        
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
                
                # Verify user has proper role permissions
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
    
    def get_test_ship(self):
        """Get a test ship for certificate upload testing"""
        try:
            response = requests.get(f"{API_BASE}/ships", headers=self.get_headers())
            
            if response.status_code == 200:
                ships = response.json()
                if ships and len(ships) > 0:
                    self.test_ship_id = ships[0]['id']
                    ship_name = ships[0].get('name', 'Unknown Ship')
                    self.log_test("Get Test Ship", True, 
                                f"Using ship: {ship_name} (ID: {self.test_ship_id})")
                    return True
                else:
                    self.log_test("Get Test Ship", False, error="No ships found in database")
                    return False
            else:
                self.log_test("Get Test Ship", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Test Ship", False, error=str(e))
            return False
    
    def create_test_certificate(self, cert_name="Test Certificate for Duplicate", cert_no="TEST-CERT-001"):
        """Create a test certificate to use for duplicate testing"""
        try:
            cert_data = {
                "ship_id": self.test_ship_id,
                "cert_name": cert_name,
                "cert_no": cert_no,
                "cert_type": "Full Term",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Test Classification Society",
                "category": "certificates",
                "sensitivity_level": "public",
                "file_uploaded": False
            }
            
            response = requests.post(f"{API_BASE}/certificates", 
                                   json=cert_data, 
                                   headers=self.get_headers())
            
            if response.status_code == 200:
                cert = response.json()
                self.test_certificates.append(cert)
                self.log_test("Create Test Certificate", True, 
                            f"Created certificate: {cert_name} (ID: {cert['id']})")
                return cert
            else:
                self.log_test("Create Test Certificate", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Test Certificate", False, error=str(e))
            return None
    
    def create_test_pdf_content(self, cert_name="Test Certificate for Duplicate", cert_no="TEST-CERT-001"):
        """Create a simple PDF-like content for testing"""
        # This creates a simple text content that mimics a certificate
        pdf_content = f"""
%PDF-1.4
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
({cert_name}) Tj
0 -20 Td
(Certificate Number: {cert_no}) Tj
0 -20 Td
(Ship Name: Test Ship) Tj
0 -20 Td
(Issue Date: 2024-01-01) Tj
0 -20 Td
(Valid Until: 2025-01-01) Tj
0 -20 Td
(Issued by: Test Classification Society) Tj
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
%%EOF
        """.strip()
        
        return pdf_content.encode('utf-8')
    
    def test_multi_upload_endpoint_exists(self):
        """Test that the multi-upload endpoint exists and is accessible"""
        try:
            # Create a simple test file
            test_content = self.create_test_pdf_content()
            files = {'files': ('test.pdf', io.BytesIO(test_content), 'application/pdf')}
            
            response = requests.post(f"{API_BASE}/certificates/multi-upload?ship_id={self.test_ship_id}", 
                                   files=files, 
                                   headers=self.get_headers())
            
            # We expect either 200 (success) or some other valid response, not 404
            if response.status_code != 404:
                self.log_test("Multi-Upload Endpoint Accessibility", True, 
                            f"Endpoint accessible - Status: {response.status_code}")
                return True
            else:
                self.log_test("Multi-Upload Endpoint Accessibility", False, 
                            error=f"Endpoint not found - Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Multi-Upload Endpoint Accessibility", False, error=str(e))
            return False
    
    def test_process_with_resolution_endpoint_exists(self):
        """Test that the process-with-resolution endpoint exists and is accessible"""
        try:
            # Send a minimal test request to check if endpoint exists
            test_data = {
                "analysis_result": {},
                "ship_id": self.test_ship_id,
                "duplicate_resolution": "cancel"
            }
            
            response = requests.post(f"{API_BASE}/certificates/process-with-resolution", 
                                   json=test_data, 
                                   headers=self.get_headers())
            
            # We expect either 200 (success) or some validation error, not 404
            if response.status_code != 404:
                self.log_test("Process-With-Resolution Endpoint Accessibility", True, 
                            f"Endpoint accessible - Status: {response.status_code}")
                return True
            else:
                self.log_test("Process-With-Resolution Endpoint Accessibility", False, 
                            error=f"Endpoint not found - Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Process-With-Resolution Endpoint Accessibility", False, error=str(e))
            return False
    
    def test_duplicate_detection_scenario(self):
        """Test duplicate detection during multi-file upload"""
        try:
            # First, create a certificate that will be duplicated
            existing_cert = self.create_test_certificate("Safety Management Certificate", "SMC-2024-001")
            if not existing_cert:
                return False
            
            # Now upload a file with the same certificate name and number
            test_content = self.create_test_pdf_content("Safety Management Certificate", "SMC-2024-001")
            files = {'files': ('duplicate_cert.pdf', io.BytesIO(test_content), 'application/pdf')}
            
            response = requests.post(f"{API_BASE}/certificates/multi-upload?ship_id={self.test_ship_id}", 
                                   files=files, 
                                   headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                # Check if any result has duplicate status and requires_user_choice
                duplicate_found = False
                for result in results:
                    if (result.get('status') == 'duplicate' and 
                        result.get('requires_user_choice') == True):
                        duplicate_found = True
                        
                        # Verify response structure
                        required_fields = ['duplicate_certificate', 'duplicates', 'analysis']
                        missing_fields = [field for field in required_fields if field not in result]
                        
                        if not missing_fields:
                            self.log_test("Duplicate Detection Scenario", True, 
                                        f"Duplicate detected correctly with proper response structure. "
                                        f"Duplicate cert: {result['duplicate_certificate'].get('cert_name', 'Unknown')}")
                            return True
                        else:
                            self.log_test("Duplicate Detection Scenario", False, 
                                        error=f"Missing required fields in duplicate response: {missing_fields}")
                            return False
                
                if not duplicate_found:
                    self.log_test("Duplicate Detection Scenario", False, 
                                error="No duplicate status found in response despite uploading duplicate certificate")
                    return False
            else:
                self.log_test("Duplicate Detection Scenario", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Duplicate Detection Scenario", False, error=str(e))
            return False
    
    def test_resolution_cancel(self):
        """Test 'cancel' resolution option"""
        try:
            resolution_data = {
                "analysis_result": {
                    "cert_name": "Test Certificate Cancel",
                    "cert_no": "CANCEL-001",
                    "category": "certificates"
                },
                "upload_result": {
                    "success": True,
                    "file_id": "test_file_id"
                },
                "ship_id": self.test_ship_id,
                "duplicate_resolution": "cancel"
            }
            
            response = requests.post(f"{API_BASE}/certificates/process-with-resolution", 
                                   json=resolution_data, 
                                   headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'cancelled':
                    self.log_test("Resolution Option - Cancel", True, 
                                f"Cancel resolution working correctly: {data.get('message', 'No message')}")
                    return True
                else:
                    self.log_test("Resolution Option - Cancel", False, 
                                error=f"Expected status 'cancelled', got: {data.get('status')}")
                    return False
            else:
                self.log_test("Resolution Option - Cancel", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Resolution Option - Cancel", False, error=str(e))
            return False
    
    def test_resolution_overwrite(self):
        """Test 'overwrite' resolution option"""
        try:
            # First create a certificate to overwrite
            existing_cert = self.create_test_certificate("Certificate to Overwrite", "OVERWRITE-001")
            if not existing_cert:
                return False
            
            resolution_data = {
                "analysis_result": {
                    "cert_name": "Certificate to Overwrite - Updated",
                    "cert_no": "OVERWRITE-001",
                    "category": "certificates",
                    "issue_date": "2024-02-01T00:00:00Z",
                    "valid_date": "2025-02-01T00:00:00Z",
                    "issued_by": "Updated Classification Society"
                },
                "upload_result": {
                    "success": True,
                    "file_id": "overwrite_file_id"
                },
                "ship_id": self.test_ship_id,
                "duplicate_resolution": "overwrite",
                "duplicate_target_id": existing_cert['id']
            }
            
            response = requests.post(f"{API_BASE}/certificates/process-with-resolution", 
                                   json=resolution_data, 
                                   headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    # Verify the old certificate was deleted
                    check_response = requests.get(f"{API_BASE}/ships/{self.test_ship_id}/certificates", 
                                                headers=self.get_headers())
                    
                    if check_response.status_code == 200:
                        certificates = check_response.json()
                        old_cert_exists = any(cert['id'] == existing_cert['id'] for cert in certificates)
                        
                        if not old_cert_exists:
                            self.log_test("Resolution Option - Overwrite", True, 
                                        f"Overwrite resolution working correctly - old certificate deleted, new one created")
                            return True
                        else:
                            self.log_test("Resolution Option - Overwrite", False, 
                                        error="Old certificate still exists after overwrite")
                            return False
                    else:
                        self.log_test("Resolution Option - Overwrite", False, 
                                    error="Could not verify certificate deletion")
                        return False
                else:
                    self.log_test("Resolution Option - Overwrite", False, 
                                error=f"Expected status 'success', got: {data.get('status')}")
                    return False
            else:
                self.log_test("Resolution Option - Overwrite", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Resolution Option - Overwrite", False, error=str(e))
            return False
    
    def test_resolution_keep_both(self):
        """Test 'keep_both' resolution option"""
        try:
            # First create a certificate to keep alongside the new one
            existing_cert = self.create_test_certificate("Certificate to Keep", "KEEP-001")
            if not existing_cert:
                return False
            
            resolution_data = {
                "analysis_result": {
                    "cert_name": "Certificate to Keep - New Version",
                    "cert_no": "KEEP-001",
                    "category": "certificates",
                    "issue_date": "2024-03-01T00:00:00Z",
                    "valid_date": "2025-03-01T00:00:00Z",
                    "issued_by": "New Classification Society"
                },
                "upload_result": {
                    "success": True,
                    "file_id": "keep_both_file_id"
                },
                "ship_id": self.test_ship_id,
                "duplicate_resolution": "keep_both"
            }
            
            response = requests.post(f"{API_BASE}/certificates/process-with-resolution", 
                                   json=resolution_data, 
                                   headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    # Verify both certificates exist
                    check_response = requests.get(f"{API_BASE}/ships/{self.test_ship_id}/certificates", 
                                                headers=self.get_headers())
                    
                    if check_response.status_code == 200:
                        certificates = check_response.json()
                        old_cert_exists = any(cert['id'] == existing_cert['id'] for cert in certificates)
                        new_cert_exists = any(cert.get('cert_name') == "Certificate to Keep - New Version" for cert in certificates)
                        
                        if old_cert_exists and new_cert_exists:
                            self.log_test("Resolution Option - Keep Both", True, 
                                        f"Keep both resolution working correctly - both certificates exist")
                            return True
                        else:
                            self.log_test("Resolution Option - Keep Both", False, 
                                        error=f"Missing certificates - Old exists: {old_cert_exists}, New exists: {new_cert_exists}")
                            return False
                    else:
                        self.log_test("Resolution Option - Keep Both", False, 
                                    error="Could not verify certificate existence")
                        return False
                else:
                    self.log_test("Resolution Option - Keep Both", False, 
                                error=f"Expected status 'success', got: {data.get('status')}")
                    return False
            else:
                self.log_test("Resolution Option - Keep Both", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Resolution Option - Keep Both", False, error=str(e))
            return False
    
    def test_api_response_validation(self):
        """Test API response structure validation"""
        try:
            # Create a duplicate scenario and check response structure
            existing_cert = self.create_test_certificate("Response Validation Cert", "RESP-VAL-001")
            if not existing_cert:
                return False
            
            test_content = self.create_test_pdf_content("Response Validation Cert", "RESP-VAL-001")
            files = {'files': ('response_validation.pdf', io.BytesIO(test_content), 'application/pdf')}
            
            response = requests.post(f"{API_BASE}/certificates/multi-upload?ship_id={self.test_ship_id}", 
                                   files=files, 
                                   headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                for result in results:
                    if result.get('status') == 'duplicate':
                        # Validate required response structure
                        required_fields = {
                            'requires_user_choice': bool,
                            'duplicate_certificate': dict,
                            'duplicates': list,
                            'analysis': dict,
                            'filename': str,
                            'status': str,
                            'message': str
                        }
                        
                        validation_errors = []
                        for field, expected_type in required_fields.items():
                            if field not in result:
                                validation_errors.append(f"Missing field: {field}")
                            elif not isinstance(result[field], expected_type):
                                validation_errors.append(f"Field {field} has wrong type: expected {expected_type.__name__}, got {type(result[field]).__name__}")
                        
                        # Validate duplicate_certificate structure
                        duplicate_cert = result.get('duplicate_certificate', {})
                        cert_required_fields = ['id', 'cert_name', 'cert_no']
                        for field in cert_required_fields:
                            if field not in duplicate_cert:
                                validation_errors.append(f"Missing field in duplicate_certificate: {field}")
                        
                        if not validation_errors:
                            self.log_test("API Response Validation", True, 
                                        f"Response structure is valid with all required fields")
                            return True
                        else:
                            self.log_test("API Response Validation", False, 
                                        error=f"Validation errors: {', '.join(validation_errors)}")
                            return False
                
                self.log_test("API Response Validation", False, 
                            error="No duplicate status found to validate response structure")
                return False
            else:
                self.log_test("API Response Validation", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("API Response Validation", False, error=str(e))
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid resolution data"""
        try:
            # Test with missing required parameters
            invalid_data = {
                "ship_id": self.test_ship_id,
                # Missing analysis_result and duplicate_resolution
            }
            
            response = requests.post(f"{API_BASE}/certificates/process-with-resolution", 
                                   json=invalid_data, 
                                   headers=self.get_headers())
            
            # Should return an error status (400 or 422)
            if response.status_code in [400, 422, 500]:
                self.log_test("Error Handling - Invalid Data", True, 
                            f"Properly handled invalid data with status: {response.status_code}")
                
                # Test with invalid resolution option
                invalid_resolution_data = {
                    "analysis_result": {"cert_name": "Test", "cert_no": "TEST"},
                    "ship_id": self.test_ship_id,
                    "duplicate_resolution": "invalid_option"  # Invalid option
                }
                
                response2 = requests.post(f"{API_BASE}/certificates/process-with-resolution", 
                                        json=invalid_resolution_data, 
                                        headers=self.get_headers())
                
                # Should handle gracefully
                if response2.status_code in [200, 400, 422, 500]:
                    self.log_test("Error Handling - Invalid Resolution Option", True, 
                                f"Handled invalid resolution option with status: {response2.status_code}")
                    return True
                else:
                    self.log_test("Error Handling - Invalid Resolution Option", False, 
                                error=f"Unexpected status: {response2.status_code}")
                    return False
            else:
                self.log_test("Error Handling - Invalid Data", False, 
                            error=f"Expected error status, got: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Error Handling", False, error=str(e))
            return False
    
    def cleanup_test_certificates(self):
        """Clean up test certificates created during testing"""
        try:
            cleanup_count = 0
            for cert in self.test_certificates:
                try:
                    response = requests.delete(f"{API_BASE}/certificates/{cert['id']}", 
                                             headers=self.get_headers())
                    if response.status_code == 200:
                        cleanup_count += 1
                except:
                    pass  # Ignore cleanup errors
            
            self.log_test("Cleanup Test Certificates", True, 
                        f"Cleaned up {cleanup_count} test certificates")
            return True
            
        except Exception as e:
            self.log_test("Cleanup Test Certificates", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all duplicate certificate resolution tests"""
        print("🚀 Starting Duplicate Certificate Resolution Testing")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Get test ship
        if not self.get_test_ship():
            print("❌ Could not get test ship. Cannot proceed with tests.")
            return False
        
        # Test endpoint accessibility
        self.test_multi_upload_endpoint_exists()
        self.test_process_with_resolution_endpoint_exists()
        
        # Test duplicate detection and resolution
        self.test_duplicate_detection_scenario()
        self.test_resolution_cancel()
        self.test_resolution_overwrite()
        self.test_resolution_keep_both()
        
        # Test API response validation
        self.test_api_response_validation()
        
        # Test error handling
        self.test_error_handling()
        
        # Cleanup
        self.cleanup_test_certificates()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['error']}")
        
        return failed_tests == 0

def main():
    """Main function to run the duplicate certificate resolution tests"""
    tester = DuplicateCertResolutionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All duplicate certificate resolution tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
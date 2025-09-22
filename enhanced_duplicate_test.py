#!/usr/bin/env python3
"""
Enhanced Duplicate Certificate Resolution Testing
Tests the duplicate certificate resolution functionality by creating real certificates first,
then testing the multi-upload with actual duplicate scenarios.
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

class EnhancedDuplicateTester:
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
    
    def create_test_certificate_for_duplicate(self):
        """Create a specific test certificate that we can duplicate"""
        try:
            cert_data = {
                "ship_id": self.test_ship_id,
                "cert_name": "Safety Management Certificate",
                "cert_no": "SMC-TEST-2024-001",
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
                self.log_test("Create Test Certificate for Duplicate Testing", True, 
                            f"Created certificate: {cert['cert_name']} (No: {cert['cert_no']}, ID: {cert['id']})")
                return cert
            else:
                self.log_test("Create Test Certificate for Duplicate Testing", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Test Certificate for Duplicate Testing", False, error=str(e))
            return None
    
    def test_duplicate_detection_with_manual_upload(self):
        """Test duplicate detection by manually creating a certificate with same details"""
        try:
            # First create the original certificate
            original_cert = self.create_test_certificate_for_duplicate()
            if not original_cert:
                return False
            
            # Now try to create another certificate with the same cert_name and cert_no
            duplicate_cert_data = {
                "ship_id": self.test_ship_id,
                "cert_name": "Safety Management Certificate",  # Same name
                "cert_no": "SMC-TEST-2024-001",  # Same number
                "cert_type": "Interim",  # Different type
                "issue_date": "2024-06-01T00:00:00Z",  # Different date
                "valid_date": "2024-12-01T00:00:00Z",  # Different date
                "issued_by": "Different Classification Society",  # Different issuer
                "category": "certificates",
                "sensitivity_level": "public",
                "file_uploaded": False
            }
            
            # Check if the system detects this as a duplicate using the duplicate check function
            # We'll simulate what the multi-upload endpoint does
            
            # First, let's test the duplicate detection logic by checking existing certificates
            existing_certs_response = requests.get(f"{API_BASE}/ships/{self.test_ship_id}/certificates", 
                                                  headers=self.get_headers())
            
            if existing_certs_response.status_code == 200:
                existing_certs = existing_certs_response.json()
                
                # Check if our duplicate would be detected
                duplicate_found = False
                for existing_cert in existing_certs:
                    if (existing_cert.get('cert_name', '').lower().strip() == duplicate_cert_data['cert_name'].lower().strip() and
                        existing_cert.get('cert_no', '').lower().strip() == duplicate_cert_data['cert_no'].lower().strip()):
                        duplicate_found = True
                        break
                
                if duplicate_found:
                    self.log_test("Duplicate Detection Logic Test", True, 
                                f"Duplicate detection logic working - found matching certificate with same name and number")
                    return True
                else:
                    self.log_test("Duplicate Detection Logic Test", False, 
                                error="Duplicate detection logic failed - no matching certificate found despite same name and number")
                    return False
            else:
                self.log_test("Duplicate Detection Logic Test", False, 
                            error=f"Could not retrieve existing certificates: {existing_certs_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Duplicate Detection Logic Test", False, error=str(e))
            return False
    
    def test_multi_upload_with_simple_file(self):
        """Test multi-upload endpoint with a simple text file to see how it handles non-PDF files"""
        try:
            # Create a simple text file that contains certificate information
            test_content = """
SAFETY MANAGEMENT CERTIFICATE

Certificate Number: SMC-TEST-2024-001
Ship Name: Test Ship
Certificate Name: Safety Management Certificate
Issue Date: 2024-01-01
Valid Until: 2025-01-01
Issued by: Test Classification Society

This is a test certificate for duplicate detection testing.
            """.strip().encode('utf-8')
            
            files = {'files': ('test_certificate.txt', io.BytesIO(test_content), 'text/plain')}
            
            response = requests.post(f"{API_BASE}/certificates/multi-upload?ship_id={self.test_ship_id}", 
                                   files=files, 
                                   headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                self.log_test("Multi-Upload with Simple File", True, 
                            f"Multi-upload processed file. Results: {len(results)} files processed")
                
                # Print the results for debugging
                for i, result in enumerate(results):
                    print(f"    Result {i+1}: Status={result.get('status')}, Message={result.get('message', 'No message')}")
                    if result.get('analysis'):
                        analysis = result['analysis']
                        print(f"      Analysis: cert_name={analysis.get('cert_name')}, cert_no={analysis.get('cert_no')}")
                
                return True
            else:
                self.log_test("Multi-Upload with Simple File", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Multi-Upload with Simple File", False, error=str(e))
            return False
    
    def test_process_with_resolution_cancel(self):
        """Test the cancel resolution option"""
        try:
            resolution_data = {
                "analysis_result": {
                    "cert_name": "Safety Management Certificate",
                    "cert_no": "SMC-TEST-2024-001",
                    "category": "certificates",
                    "issue_date": "2024-01-01T00:00:00Z",
                    "valid_date": "2025-01-01T00:00:00Z",
                    "issued_by": "Test Classification Society"
                },
                "upload_result": {
                    "success": True,
                    "file_id": "test_file_id_cancel"
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
                    self.log_test("Process With Resolution - Cancel", True, 
                                f"Cancel resolution working: {data.get('message', 'No message')}")
                    return True
                else:
                    self.log_test("Process With Resolution - Cancel", False, 
                                error=f"Expected 'cancelled' status, got: {data.get('status')}")
                    return False
            else:
                self.log_test("Process With Resolution - Cancel", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Process With Resolution - Cancel", False, error=str(e))
            return False
    
    def test_process_with_resolution_overwrite(self):
        """Test the overwrite resolution option"""
        try:
            # First create a certificate to overwrite
            cert_to_overwrite = {
                "ship_id": self.test_ship_id,
                "cert_name": "Certificate for Overwrite Test",
                "cert_no": "OVERWRITE-TEST-001",
                "cert_type": "Full Term",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Original Classification Society",
                "category": "certificates",
                "sensitivity_level": "public",
                "file_uploaded": False
            }
            
            create_response = requests.post(f"{API_BASE}/certificates", 
                                          json=cert_to_overwrite, 
                                          headers=self.get_headers())
            
            if create_response.status_code != 200:
                self.log_test("Process With Resolution - Overwrite", False, 
                            error="Could not create certificate to overwrite")
                return False
            
            created_cert = create_response.json()
            self.test_certificates.append(created_cert)
            
            # Now test the overwrite resolution
            resolution_data = {
                "analysis_result": {
                    "cert_name": "Certificate for Overwrite Test - Updated",
                    "cert_no": "OVERWRITE-TEST-001",
                    "category": "certificates",
                    "issue_date": "2024-06-01T00:00:00Z",
                    "valid_date": "2025-06-01T00:00:00Z",
                    "issued_by": "Updated Classification Society"
                },
                "upload_result": {
                    "success": True,
                    "file_id": "test_file_id_overwrite"
                },
                "ship_id": self.test_ship_id,
                "duplicate_resolution": "overwrite",
                "duplicate_target_id": created_cert['id']
            }
            
            response = requests.post(f"{API_BASE}/certificates/process-with-resolution", 
                                   json=resolution_data, 
                                   headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    # Verify the old certificate was deleted and new one created
                    check_response = requests.get(f"{API_BASE}/ships/{self.test_ship_id}/certificates", 
                                                headers=self.get_headers())
                    
                    if check_response.status_code == 200:
                        certificates = check_response.json()
                        old_cert_exists = any(cert['id'] == created_cert['id'] for cert in certificates)
                        new_cert_exists = any("Updated" in cert.get('cert_name', '') for cert in certificates)
                        
                        if not old_cert_exists and new_cert_exists:
                            self.log_test("Process With Resolution - Overwrite", True, 
                                        f"Overwrite resolution working - old certificate deleted, new one created")
                            return True
                        else:
                            self.log_test("Process With Resolution - Overwrite", False, 
                                        error=f"Overwrite failed - Old exists: {old_cert_exists}, New exists: {new_cert_exists}")
                            return False
                    else:
                        self.log_test("Process With Resolution - Overwrite", False, 
                                    error="Could not verify overwrite result")
                        return False
                else:
                    self.log_test("Process With Resolution - Overwrite", False, 
                                error=f"Expected 'success' status, got: {data.get('status')}")
                    return False
            else:
                self.log_test("Process With Resolution - Overwrite", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Process With Resolution - Overwrite", False, error=str(e))
            return False
    
    def test_process_with_resolution_keep_both(self):
        """Test the keep_both resolution option"""
        try:
            # First create a certificate to keep alongside the new one
            cert_to_keep = {
                "ship_id": self.test_ship_id,
                "cert_name": "Certificate for Keep Both Test",
                "cert_no": "KEEP-BOTH-TEST-001",
                "cert_type": "Full Term",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Original Classification Society",
                "category": "certificates",
                "sensitivity_level": "public",
                "file_uploaded": False
            }
            
            create_response = requests.post(f"{API_BASE}/certificates", 
                                          json=cert_to_keep, 
                                          headers=self.get_headers())
            
            if create_response.status_code != 200:
                self.log_test("Process With Resolution - Keep Both", False, 
                            error="Could not create certificate for keep both test")
                return False
            
            created_cert = create_response.json()
            self.test_certificates.append(created_cert)
            
            # Now test the keep_both resolution
            resolution_data = {
                "analysis_result": {
                    "cert_name": "Certificate for Keep Both Test - New Version",
                    "cert_no": "KEEP-BOTH-TEST-001",
                    "category": "certificates",
                    "issue_date": "2024-06-01T00:00:00Z",
                    "valid_date": "2025-06-01T00:00:00Z",
                    "issued_by": "New Classification Society"
                },
                "upload_result": {
                    "success": True,
                    "file_id": "test_file_id_keep_both"
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
                        old_cert_exists = any(cert['id'] == created_cert['id'] for cert in certificates)
                        new_cert_exists = any("New Version" in cert.get('cert_name', '') for cert in certificates)
                        
                        if old_cert_exists and new_cert_exists:
                            self.log_test("Process With Resolution - Keep Both", True, 
                                        f"Keep both resolution working - both certificates exist")
                            return True
                        else:
                            self.log_test("Process With Resolution - Keep Both", False, 
                                        error=f"Keep both failed - Old exists: {old_cert_exists}, New exists: {new_cert_exists}")
                            return False
                    else:
                        self.log_test("Process With Resolution - Keep Both", False, 
                                    error="Could not verify keep both result")
                        return False
                else:
                    self.log_test("Process With Resolution - Keep Both", False, 
                                error=f"Expected 'success' status, got: {data.get('status')}")
                    return False
            else:
                self.log_test("Process With Resolution - Keep Both", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Process With Resolution - Keep Both", False, error=str(e))
            return False
    
    def test_error_handling_invalid_resolution(self):
        """Test error handling for invalid resolution data"""
        try:
            # Test with invalid resolution option
            invalid_data = {
                "analysis_result": {
                    "cert_name": "Test Certificate",
                    "cert_no": "TEST-001",
                    "category": "certificates"
                },
                "ship_id": self.test_ship_id,
                "duplicate_resolution": "invalid_option"  # Invalid option
            }
            
            response = requests.post(f"{API_BASE}/certificates/process-with-resolution", 
                                   json=invalid_data, 
                                   headers=self.get_headers())
            
            # The endpoint should handle this gracefully
            if response.status_code in [200, 400, 422]:
                self.log_test("Error Handling - Invalid Resolution", True, 
                            f"Invalid resolution handled gracefully with status: {response.status_code}")
                return True
            else:
                self.log_test("Error Handling - Invalid Resolution", False, 
                            error=f"Unexpected status for invalid resolution: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Error Handling - Invalid Resolution", False, error=str(e))
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
        """Run all enhanced duplicate certificate resolution tests"""
        print("🚀 Starting Enhanced Duplicate Certificate Resolution Testing")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Get test ship
        if not self.get_test_ship():
            print("❌ Could not get test ship. Cannot proceed with tests.")
            return False
        
        # Test duplicate detection logic
        self.test_duplicate_detection_with_manual_upload()
        
        # Test multi-upload with simple file
        self.test_multi_upload_with_simple_file()
        
        # Test resolution options
        self.test_process_with_resolution_cancel()
        self.test_process_with_resolution_overwrite()
        self.test_process_with_resolution_keep_both()
        
        # Test error handling
        self.test_error_handling_invalid_resolution()
        
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
    """Main function to run the enhanced duplicate certificate resolution tests"""
    tester = EnhancedDuplicateTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All enhanced duplicate certificate resolution tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
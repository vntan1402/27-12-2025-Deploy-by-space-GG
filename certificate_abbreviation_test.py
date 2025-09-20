#!/usr/bin/env python3
"""
Certificate Abbreviation Mapping System Testing
Comprehensive testing of the newly implemented Certificate Abbreviation Mapping System
including CRUD operations, validation, database integration, and end-to-end workflows.
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ship-cert-manager-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

class CertificateAbbreviationTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.test_ship_id = None
        self.test_cert_id = None
        self.test_mapping_id = None
        
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
                
                self.log_test("Authentication Test", True, 
                            f"Logged in as {self.user_info['username']} ({self.user_info.get('role', 'Unknown')})")
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
    
    def setup_test_data(self):
        """Setup test ship and certificate for testing"""
        try:
            # Get existing ships
            response = requests.get(f"{API_BASE}/ships", headers=self.get_headers())
            if response.status_code == 200:
                ships = response.json()
                if ships:
                    self.test_ship_id = ships[0]['id']
                    self.log_test("Test Data Setup - Ship", True, 
                                f"Using existing ship: {ships[0]['name']} (ID: {self.test_ship_id})")
                else:
                    # Create a test ship
                    ship_data = {
                        "name": "Test Ship for Abbreviation Testing",
                        "imo": "1234567",
                        "flag": "Panama",
                        "ship_type": "General Cargo",
                        "company": self.user_info.get('company', 'test-company')
                    }
                    response = requests.post(f"{API_BASE}/ships", json=ship_data, headers=self.get_headers())
                    if response.status_code == 200:
                        ship = response.json()
                        self.test_ship_id = ship['id']
                        self.log_test("Test Data Setup - Ship", True, 
                                    f"Created test ship: {ship['name']} (ID: {self.test_ship_id})")
                    else:
                        self.log_test("Test Data Setup - Ship", False, 
                                    error=f"Failed to create test ship: {response.text}")
                        return False
            else:
                self.log_test("Test Data Setup - Ship", False, 
                            error=f"Failed to get ships: {response.text}")
                return False
            
            # Create a test certificate
            cert_data = {
                "ship_id": self.test_ship_id,
                "cert_name": "Safety Management Certificate",
                "cert_type": "Full Term",
                "cert_no": "SMC-TEST-001",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Panama Maritime Documentation Services"
            }
            response = requests.post(f"{API_BASE}/certificates", json=cert_data, headers=self.get_headers())
            if response.status_code == 200:
                cert = response.json()
                self.test_cert_id = cert['id']
                self.log_test("Test Data Setup - Certificate", True, 
                            f"Created test certificate: {cert['cert_name']} (ID: {self.test_cert_id})")
                return True
            else:
                self.log_test("Test Data Setup - Certificate", False, 
                            error=f"Failed to create test certificate: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Test Data Setup", False, error=str(e))
            return False
    
    def test_get_certificate_abbreviation_mappings(self):
        """Test GET /api/certificate-abbreviation-mappings endpoint"""
        try:
            response = requests.get(f"{API_BASE}/certificate-abbreviation-mappings", headers=self.get_headers())
            
            if response.status_code == 200:
                mappings = response.json()
                self.log_test("GET Certificate Abbreviation Mappings", True, 
                            f"Retrieved {len(mappings)} mappings")
                return True
            else:
                self.log_test("GET Certificate Abbreviation Mappings", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("GET Certificate Abbreviation Mappings", False, error=str(e))
            return False
    
    def test_create_certificate_abbreviation_mapping(self):
        """Test POST /api/certificate-abbreviation-mappings endpoint"""
        try:
            mapping_data = {
                "cert_name": "Safety Management Certificate",
                "abbreviation": "SMC"
            }
            
            response = requests.post(f"{API_BASE}/certificate-abbreviation-mappings", 
                                   json=mapping_data, headers=self.get_headers())
            
            if response.status_code == 200:
                mapping = response.json()
                self.test_mapping_id = mapping['id']
                self.log_test("POST Certificate Abbreviation Mapping", True, 
                            f"Created mapping: {mapping['cert_name']} -> {mapping['abbreviation']} (ID: {self.test_mapping_id})")
                return True
            else:
                self.log_test("POST Certificate Abbreviation Mapping", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("POST Certificate Abbreviation Mapping", False, error=str(e))
            return False
    
    def test_update_certificate_abbreviation_mapping(self):
        """Test PUT /api/certificate-abbreviation-mappings/{id} endpoint"""
        try:
            if not self.test_mapping_id:
                self.log_test("PUT Certificate Abbreviation Mapping", False, 
                            error="No test mapping ID available")
                return False
            
            update_data = {
                "abbreviation": "SMCERT"
            }
            
            response = requests.put(f"{API_BASE}/certificate-abbreviation-mappings/{self.test_mapping_id}", 
                                  json=update_data, headers=self.get_headers())
            
            if response.status_code == 200:
                mapping = response.json()
                self.log_test("PUT Certificate Abbreviation Mapping", True, 
                            f"Updated mapping abbreviation to: {mapping['abbreviation']}")
                return True
            else:
                self.log_test("PUT Certificate Abbreviation Mapping", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("PUT Certificate Abbreviation Mapping", False, error=str(e))
            return False
    
    def test_certificate_integration_with_abbreviations(self):
        """Test that certificates now include abbreviations in their responses"""
        try:
            # Get certificates to see if they include abbreviations
            response = requests.get(f"{API_BASE}/certificates", headers=self.get_headers())
            
            if response.status_code == 200:
                certificates = response.json()
                if certificates:
                    cert = certificates[0]
                    if 'cert_abbreviation' in cert:
                        self.log_test("Certificate Integration - Abbreviations", True, 
                                    f"Certificate includes abbreviation: {cert.get('cert_abbreviation', 'None')}")
                        return True
                    else:
                        self.log_test("Certificate Integration - Abbreviations", False, 
                                    error="Certificate response missing 'cert_abbreviation' field")
                        return False
                else:
                    self.log_test("Certificate Integration - Abbreviations", False, 
                                error="No certificates found to test")
                    return False
            else:
                self.log_test("Certificate Integration - Abbreviations", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Certificate Integration - Abbreviations", False, error=str(e))
            return False
    
    def test_certificate_update_with_manual_abbreviation(self):
        """Test PUT /api/certificates/{id} with manual cert_abbreviation to verify mapping creation"""
        try:
            if not self.test_cert_id:
                self.log_test("Certificate Update with Manual Abbreviation", False, 
                            error="No test certificate ID available")
                return False
            
            # Update certificate with manual abbreviation
            update_data = {
                "cert_abbreviation": "MANUAL_SMC"
            }
            
            response = requests.put(f"{API_BASE}/certificates/{self.test_cert_id}", 
                                  json=update_data, headers=self.get_headers())
            
            if response.status_code == 200:
                cert = response.json()
                if cert.get('cert_abbreviation') == 'MANUAL_SMC':
                    self.log_test("Certificate Update with Manual Abbreviation", True, 
                                f"Certificate updated with manual abbreviation: {cert['cert_abbreviation']}")
                    
                    # Verify that a mapping was created
                    time.sleep(1)  # Give time for mapping to be saved
                    mappings_response = requests.get(f"{API_BASE}/certificate-abbreviation-mappings", 
                                                   headers=self.get_headers())
                    if mappings_response.status_code == 200:
                        mappings = mappings_response.json()
                        manual_mapping = next((m for m in mappings if m['abbreviation'] == 'MANUAL_SMC'), None)
                        if manual_mapping:
                            self.log_test("Certificate Update - Mapping Creation", True, 
                                        f"Manual abbreviation mapping created: {manual_mapping['cert_name']} -> {manual_mapping['abbreviation']}")
                        else:
                            self.log_test("Certificate Update - Mapping Creation", False, 
                                        error="Manual abbreviation mapping not found in database")
                    
                    return True
                else:
                    self.log_test("Certificate Update with Manual Abbreviation", False, 
                                error=f"Expected 'MANUAL_SMC', got '{cert.get('cert_abbreviation')}'")
                    return False
            else:
                self.log_test("Certificate Update with Manual Abbreviation", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Certificate Update with Manual Abbreviation", False, error=str(e))
            return False
    
    def test_abbreviation_length_validation(self):
        """Test abbreviation length validation (max 10 characters)"""
        try:
            # Test with abbreviation longer than 10 characters
            mapping_data = {
                "cert_name": "Test Certificate for Length Validation",
                "abbreviation": "THIS_IS_TOO_LONG_ABBREVIATION"  # 30 characters
            }
            
            response = requests.post(f"{API_BASE}/certificate-abbreviation-mappings", 
                                   json=mapping_data, headers=self.get_headers())
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', '')
                if '10 characters' in error_detail:
                    self.log_test("Abbreviation Length Validation", True, 
                                f"Long abbreviation correctly rejected: {error_detail}")
                    return True
                else:
                    self.log_test("Abbreviation Length Validation", False, 
                                error=f"Wrong error message: {error_detail}")
                    return False
            else:
                self.log_test("Abbreviation Length Validation", False, 
                            error=f"Expected 400 status, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Abbreviation Length Validation", False, error=str(e))
            return False
    
    def test_duplicate_certificate_name_handling(self):
        """Test duplicate certificate name handling in mappings"""
        try:
            # Create first mapping
            mapping_data_1 = {
                "cert_name": "Duplicate Test Certificate",
                "abbreviation": "DTC1"
            }
            
            response_1 = requests.post(f"{API_BASE}/certificate-abbreviation-mappings", 
                                     json=mapping_data_1, headers=self.get_headers())
            
            if response_1.status_code == 200:
                mapping_1 = response_1.json()
                
                # Try to create second mapping with same certificate name
                mapping_data_2 = {
                    "cert_name": "Duplicate Test Certificate",
                    "abbreviation": "DTC2"
                }
                
                response_2 = requests.post(f"{API_BASE}/certificate-abbreviation-mappings", 
                                         json=mapping_data_2, headers=self.get_headers())
                
                if response_2.status_code == 200:
                    mapping_2 = response_2.json()
                    # Should update existing mapping, not create new one
                    if mapping_1['id'] == mapping_2['id'] and mapping_2['abbreviation'] == 'DTC2':
                        self.log_test("Duplicate Certificate Name Handling", True, 
                                    "Duplicate certificate name correctly updates existing mapping")
                        return True
                    else:
                        self.log_test("Duplicate Certificate Name Handling", False, 
                                    error="Duplicate handling not working as expected")
                        return False
                else:
                    self.log_test("Duplicate Certificate Name Handling", False, 
                                error=f"Second mapping failed: {response_2.status_code}, {response_2.text}")
                    return False
            else:
                self.log_test("Duplicate Certificate Name Handling", False, 
                            error=f"First mapping failed: {response_1.status_code}, {response_1.text}")
                return False
                
        except Exception as e:
            self.log_test("Duplicate Certificate Name Handling", False, error=str(e))
            return False
    
    def test_user_defined_abbreviation_priority(self):
        """Test that user-defined abbreviations are prioritized over auto-generated ones"""
        try:
            # Create a certificate with a name that would auto-generate an abbreviation
            cert_data = {
                "ship_id": self.test_ship_id,
                "cert_name": "International Safety Management Certificate",
                "cert_type": "Full Term",
                "cert_no": "ISMC-TEST-001",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Classification Society"
            }
            
            response = requests.post(f"{API_BASE}/certificates", json=cert_data, headers=self.get_headers())
            if response.status_code == 200:
                cert = response.json()
                auto_abbreviation = cert.get('cert_abbreviation', '')
                
                # Now create a user-defined mapping for the same certificate name
                mapping_data = {
                    "cert_name": "International Safety Management Certificate",
                    "abbreviation": "USER_ISM"
                }
                
                mapping_response = requests.post(f"{API_BASE}/certificate-abbreviation-mappings", 
                                               json=mapping_data, headers=self.get_headers())
                
                if mapping_response.status_code == 200:
                    # Get all certificates to find our test certificate and see if it uses the user-defined abbreviation
                    cert_response = requests.get(f"{API_BASE}/certificates", 
                                               headers=self.get_headers())
                    
                    if cert_response.status_code == 200:
                        all_certs = cert_response.json()
                        updated_cert = next((c for c in all_certs if c['id'] == cert['id']), None)
                        
                        if updated_cert:
                            new_abbreviation = updated_cert.get('cert_abbreviation', '')
                            
                            if new_abbreviation == 'USER_ISM':
                                self.log_test("User-Defined Abbreviation Priority", True, 
                                            f"User-defined abbreviation prioritized: {new_abbreviation} (was: {auto_abbreviation})")
                                return True
                            else:
                                self.log_test("User-Defined Abbreviation Priority", False, 
                                            error=f"Expected 'USER_ISM', got '{new_abbreviation}'")
                                return False
                        else:
                            self.log_test("User-Defined Abbreviation Priority", False, 
                                        error="Test certificate not found in certificates list")
                            return False
                    else:
                        self.log_test("User-Defined Abbreviation Priority", False, 
                                    error=f"Failed to retrieve certificates: {cert_response.text}")
                        return False
                else:
                    self.log_test("User-Defined Abbreviation Priority", False, 
                                error=f"Failed to create mapping: {mapping_response.text}")
                    return False
            else:
                self.log_test("User-Defined Abbreviation Priority", False, 
                            error=f"Failed to create test certificate: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User-Defined Abbreviation Priority", False, error=str(e))
            return False
    
    def test_delete_certificate_abbreviation_mapping(self):
        """Test DELETE /api/certificate-abbreviation-mappings/{id} endpoint"""
        try:
            if not self.test_mapping_id:
                self.log_test("DELETE Certificate Abbreviation Mapping", False, 
                            error="No test mapping ID available")
                return False
            
            response = requests.delete(f"{API_BASE}/certificate-abbreviation-mappings/{self.test_mapping_id}", 
                                     headers=self.get_headers())
            
            if response.status_code == 200:
                # Verify mapping is deleted
                get_response = requests.get(f"{API_BASE}/certificate-abbreviation-mappings", 
                                          headers=self.get_headers())
                if get_response.status_code == 200:
                    mappings = get_response.json()
                    deleted_mapping = next((m for m in mappings if m['id'] == self.test_mapping_id), None)
                    if not deleted_mapping:
                        self.log_test("DELETE Certificate Abbreviation Mapping", True, 
                                    "Mapping successfully deleted")
                        return True
                    else:
                        self.log_test("DELETE Certificate Abbreviation Mapping", False, 
                                    error="Mapping still exists after deletion")
                        return False
                else:
                    self.log_test("DELETE Certificate Abbreviation Mapping", False, 
                                error=f"Failed to verify deletion: {get_response.text}")
                    return False
            else:
                self.log_test("DELETE Certificate Abbreviation Mapping", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("DELETE Certificate Abbreviation Mapping", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests for Certificate Abbreviation Mapping System"""
        print("🧪 CERTIFICATE ABBREVIATION MAPPING SYSTEM COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print()
        
        # Step 1: Authentication Test
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed. Cannot proceed with tests.")
            return False
        
        # Step 3: Test GET certificate abbreviation mappings
        self.test_get_certificate_abbreviation_mappings()
        
        # Step 4: Test POST certificate abbreviation mapping
        self.test_create_certificate_abbreviation_mapping()
        
        # Step 5: Test PUT certificate abbreviation mapping
        self.test_update_certificate_abbreviation_mapping()
        
        # Step 6: Test certificate integration with abbreviations
        self.test_certificate_integration_with_abbreviations()
        
        # Step 7: Test certificate update with manual abbreviation
        self.test_certificate_update_with_manual_abbreviation()
        
        # Step 8: Test abbreviation length validation
        self.test_abbreviation_length_validation()
        
        # Step 9: Test duplicate certificate name handling
        self.test_duplicate_certificate_name_handling()
        
        # Step 10: Test user-defined abbreviation priority
        self.test_user_defined_abbreviation_priority()
        
        # Step 11: Test DELETE certificate abbreviation mapping
        self.test_delete_certificate_abbreviation_mapping()
        
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
            print("\n🎉 ALL TESTS PASSED! Certificate Abbreviation Mapping System is working correctly.")
            return True
        else:
            print(f"\n❌ {total - passed} tests failed. Please review the issues above.")
            return False

def main():
    """Main test execution"""
    tester = CertificateAbbreviationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
End-to-End Workflow Test for Certificate Abbreviation Mapping System
Test the complete workflow: creating mappings, using them in certificate operations,
and verifying that user-defined abbreviations take priority over auto-generated ones.
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://certmaster-ship.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

class EndToEndWorkflowTester:
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
                self.log_test("Authentication", True, 
                            f"Logged in as {self.user_info['username']} ({self.user_info.get('role', 'Unknown')})")
                return True
            else:
                self.log_test("Authentication", False, error=f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def setup_test_ship(self):
        """Setup test ship"""
        try:
            # Get existing ships
            response = requests.get(f"{API_BASE}/ships", headers=self.get_headers())
            if response.status_code == 200:
                ships = response.json()
                if ships:
                    self.test_ship_id = ships[0]['id']
                    self.log_test("Test Ship Setup", True, 
                                f"Using existing ship: {ships[0]['name']} (ID: {self.test_ship_id})")
                    return True
                else:
                    self.log_test("Test Ship Setup", False, error="No ships found")
                    return False
            else:
                self.log_test("Test Ship Setup", False, error=f"Failed to get ships: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Test Ship Setup", False, error=str(e))
            return False
    
    def test_complete_workflow(self):
        """Test complete end-to-end workflow"""
        try:
            workflow_steps = []
            
            # Step 1: Create a certificate without any mapping (should get auto-generated abbreviation)
            cert_data_1 = {
                "ship_id": self.test_ship_id,
                "cert_name": "International Load Line Certificate",
                "cert_type": "Full Term",
                "cert_no": "ILLC-001",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Maritime Authority"
            }
            
            cert_response_1 = requests.post(f"{API_BASE}/certificates", 
                                          json=cert_data_1, headers=self.get_headers())
            
            if cert_response_1.status_code == 200:
                cert_1 = cert_response_1.json()
                auto_abbreviation = cert_1.get('cert_abbreviation', '')
                workflow_steps.append(f"Step 1: Created certificate with auto-generated abbreviation: '{auto_abbreviation}'")
                
                # Step 2: Create a user-defined mapping for the same certificate name
                mapping_data = {
                    "cert_name": "International Load Line Certificate",
                    "abbreviation": "ILLC_USER"
                }
                
                mapping_response = requests.post(f"{API_BASE}/certificate-abbreviation-mappings", 
                                               json=mapping_data, headers=self.get_headers())
                
                if mapping_response.status_code == 200:
                    mapping = mapping_response.json()
                    workflow_steps.append(f"Step 2: Created user-defined mapping: '{mapping['cert_name']}' -> '{mapping['abbreviation']}'")
                    
                    # Step 3: Create another certificate with the same name (should use user-defined abbreviation)
                    cert_data_2 = {
                        "ship_id": self.test_ship_id,
                        "cert_name": "International Load Line Certificate",
                        "cert_type": "Interim",
                        "cert_no": "ILLC-002",
                        "issue_date": "2024-01-01T00:00:00Z",
                        "valid_date": "2025-01-01T00:00:00Z",
                        "issued_by": "Maritime Authority"
                    }
                    
                    cert_response_2 = requests.post(f"{API_BASE}/certificates", 
                                                  json=cert_data_2, headers=self.get_headers())
                    
                    if cert_response_2.status_code == 200:
                        cert_2 = cert_response_2.json()
                        user_abbreviation = cert_2.get('cert_abbreviation', '')
                        workflow_steps.append(f"Step 3: Created second certificate with user-defined abbreviation: '{user_abbreviation}'")
                        
                        # Step 4: Update first certificate manually to trigger mapping save
                        update_data = {
                            "cert_abbreviation": "MAN_ILLC"
                        }
                        
                        update_response = requests.put(f"{API_BASE}/certificates/{cert_1['id']}", 
                                                     json=update_data, headers=self.get_headers())
                        
                        if update_response.status_code == 200:
                            updated_cert = update_response.json()
                            manual_abbreviation = updated_cert.get('cert_abbreviation', '')
                            workflow_steps.append(f"Step 4: Updated first certificate with manual abbreviation: '{manual_abbreviation}'")
                            
                            # Step 5: Verify that the manual abbreviation created a new mapping
                            time.sleep(1)  # Give time for mapping to be saved
                            
                            mappings_response = requests.get(f"{API_BASE}/certificate-abbreviation-mappings", 
                                                           headers=self.get_headers())
                            
                            if mappings_response.status_code == 200:
                                mappings = mappings_response.json()
                                manual_mapping = next((m for m in mappings if m['abbreviation'] == 'MAN_ILLC'), None)
                                
                                if manual_mapping:
                                    workflow_steps.append(f"Step 5: Manual abbreviation mapping created: '{manual_mapping['cert_name']}' -> '{manual_mapping['abbreviation']}'")
                                    
                                    # Step 6: Create a third certificate to see which mapping is used (should be the most recent one)
                                    cert_data_3 = {
                                        "ship_id": self.test_ship_id,
                                        "cert_name": "International Load Line Certificate",
                                        "cert_type": "Short Term",
                                        "cert_no": "ILLC-003",
                                        "issue_date": "2024-01-01T00:00:00Z",
                                        "valid_date": "2025-01-01T00:00:00Z",
                                        "issued_by": "Maritime Authority"
                                    }
                                    
                                    cert_response_3 = requests.post(f"{API_BASE}/certificates", 
                                                                  json=cert_data_3, headers=self.get_headers())
                                    
                                    if cert_response_3.status_code == 200:
                                        cert_3 = cert_response_3.json()
                                        final_abbreviation = cert_3.get('cert_abbreviation', '')
                                        workflow_steps.append(f"Step 6: Created third certificate with abbreviation: '{final_abbreviation}'")
                                        
                                        # Step 7: Verify usage count increment
                                        final_mappings_response = requests.get(f"{API_BASE}/certificate-abbreviation-mappings", 
                                                                              headers=self.get_headers())
                                        
                                        if final_mappings_response.status_code == 200:
                                            final_mappings = final_mappings_response.json()
                                            used_mapping = next((m for m in final_mappings if m['abbreviation'] == final_abbreviation), None)
                                            
                                            if used_mapping:
                                                usage_count = used_mapping.get('usage_count', 0)
                                                workflow_steps.append(f"Step 7: Mapping usage count: {usage_count}")
                                                
                                                # Clean up test data
                                                requests.delete(f"{API_BASE}/certificates/{cert_1['id']}", headers=self.get_headers())
                                                requests.delete(f"{API_BASE}/certificates/{cert_2['id']}", headers=self.get_headers())
                                                requests.delete(f"{API_BASE}/certificates/{cert_3['id']}", headers=self.get_headers())
                                                
                                                for mapping in final_mappings:
                                                    if 'INTERNATIONAL LOAD LINE CERTIFICATE' in mapping.get('cert_name', ''):
                                                        requests.delete(f"{API_BASE}/certificate-abbreviation-mappings/{mapping['id']}", 
                                                                      headers=self.get_headers())
                                                
                                                # Verify workflow success
                                                success_criteria = [
                                                    auto_abbreviation != '',  # Auto-generation worked
                                                    user_abbreviation == 'ILLC_USER',  # User-defined mapping used
                                                    manual_abbreviation == 'MAN_ILLC',  # Manual update worked
                                                    manual_mapping is not None,  # Manual mapping created
                                                    final_abbreviation == 'MAN_ILLC',  # Latest mapping used
                                                    usage_count > 0  # Usage count incremented
                                                ]
                                                
                                                if all(success_criteria):
                                                    workflow_details = "\n    " + "\n    ".join(workflow_steps)
                                                    self.log_test("Complete End-to-End Workflow", True, 
                                                                f"All workflow steps completed successfully:{workflow_details}")
                                                    return True
                                                else:
                                                    self.log_test("Complete End-to-End Workflow", False, 
                                                                error=f"Some success criteria failed: {success_criteria}")
                                                    return False
                                            else:
                                                self.log_test("Complete End-to-End Workflow", False, 
                                                            error="Used mapping not found")
                                                return False
                                        else:
                                            self.log_test("Complete End-to-End Workflow", False, 
                                                        error="Failed to get final mappings")
                                            return False
                                    else:
                                        self.log_test("Complete End-to-End Workflow", False, 
                                                    error="Failed to create third certificate")
                                        return False
                                else:
                                    self.log_test("Complete End-to-End Workflow", False, 
                                                error="Manual abbreviation mapping not created")
                                    return False
                            else:
                                self.log_test("Complete End-to-End Workflow", False, 
                                            error="Failed to get mappings after manual update")
                                return False
                        else:
                            self.log_test("Complete End-to-End Workflow", False, 
                                        error="Failed to update certificate with manual abbreviation")
                            return False
                    else:
                        self.log_test("Complete End-to-End Workflow", False, 
                                    error="Failed to create second certificate")
                        return False
                else:
                    self.log_test("Complete End-to-End Workflow", False, 
                                error="Failed to create user-defined mapping")
                    return False
            else:
                self.log_test("Complete End-to-End Workflow", False, 
                            error="Failed to create first certificate")
                return False
                
        except Exception as e:
            self.log_test("Complete End-to-End Workflow", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all end-to-end workflow tests"""
        print("🧪 END-TO-END WORKFLOW TESTING FOR CERTIFICATE ABBREVIATION MAPPING SYSTEM")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Setup test ship
        if not self.setup_test_ship():
            print("❌ Test ship setup failed. Cannot proceed with tests.")
            return False
        
        # Step 3: Test complete workflow
        self.test_complete_workflow()
        
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
            print("\n🎉 ALL END-TO-END WORKFLOW TESTS PASSED!")
            return True
        else:
            print(f"\n❌ {total - passed} tests failed. Please review the issues above.")
            return False

def main():
    """Main test execution"""
    tester = EndToEndWorkflowTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
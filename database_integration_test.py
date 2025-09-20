#!/usr/bin/env python3
"""
Database Integration Test for Certificate Abbreviation Mapping System
Test MongoDB storage and usage count increment functionality.
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

class DatabaseIntegrationTester:
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
    
    def test_database_persistence(self):
        """Test that mappings are properly stored in MongoDB"""
        try:
            # Create a test mapping
            mapping_data = {
                "cert_name": "Database Test Certificate",
                "abbreviation": "DBTEST"
            }
            
            create_response = requests.post(f"{API_BASE}/certificate-abbreviation-mappings", 
                                          json=mapping_data, headers=self.get_headers())
            
            if create_response.status_code == 200:
                created_mapping = create_response.json()
                mapping_id = created_mapping['id']
                
                # Verify the mapping persists by retrieving it
                get_response = requests.get(f"{API_BASE}/certificate-abbreviation-mappings", 
                                          headers=self.get_headers())
                
                if get_response.status_code == 200:
                    mappings = get_response.json()
                    found_mapping = next((m for m in mappings if m['id'] == mapping_id), None)
                    
                    if found_mapping:
                        # Check all required fields are present
                        required_fields = ['id', 'cert_name', 'abbreviation', 'created_by', 'created_at', 'usage_count']
                        missing_fields = [field for field in required_fields if field not in found_mapping]
                        
                        if not missing_fields:
                            self.log_test("Database Persistence", True, 
                                        f"Mapping persisted with all required fields: {found_mapping['cert_name']} -> {found_mapping['abbreviation']}")
                            
                            # Clean up
                            requests.delete(f"{API_BASE}/certificate-abbreviation-mappings/{mapping_id}", 
                                          headers=self.get_headers())
                            return True
                        else:
                            self.log_test("Database Persistence", False, 
                                        error=f"Missing required fields: {missing_fields}")
                            return False
                    else:
                        self.log_test("Database Persistence", False, 
                                    error="Created mapping not found in database")
                        return False
                else:
                    self.log_test("Database Persistence", False, 
                                error=f"Failed to retrieve mappings: {get_response.text}")
                    return False
            else:
                self.log_test("Database Persistence", False, 
                            error=f"Failed to create mapping: {create_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Database Persistence", False, error=str(e))
            return False
    
    def test_usage_count_increment(self):
        """Test usage count increment when mappings are retrieved"""
        try:
            # Create a test mapping
            mapping_data = {
                "cert_name": "Usage Count Test Certificate",
                "abbreviation": "UCTC"
            }
            
            create_response = requests.post(f"{API_BASE}/certificate-abbreviation-mappings", 
                                          json=mapping_data, headers=self.get_headers())
            
            if create_response.status_code == 200:
                created_mapping = create_response.json()
                mapping_id = created_mapping['id']
                initial_usage_count = created_mapping.get('usage_count', 0)
                
                # Create a certificate that will use this mapping
                ship_response = requests.get(f"{API_BASE}/ships", headers=self.get_headers())
                if ship_response.status_code == 200:
                    ships = ship_response.json()
                    if ships:
                        test_ship_id = ships[0]['id']
                        
                        cert_data = {
                            "ship_id": test_ship_id,
                            "cert_name": "Usage Count Test Certificate",
                            "cert_type": "Full Term",
                            "cert_no": "UCTC-001",
                            "issue_date": "2024-01-01T00:00:00Z",
                            "valid_date": "2025-01-01T00:00:00Z",
                            "issued_by": "Test Authority"
                        }
                        
                        cert_response = requests.post(f"{API_BASE}/certificates", 
                                                    json=cert_data, headers=self.get_headers())
                        
                        if cert_response.status_code == 200:
                            cert = cert_response.json()
                            
                            # The certificate creation should trigger abbreviation lookup and increment usage count
                            time.sleep(1)  # Give time for async operations
                            
                            # Check if usage count was incremented
                            get_response = requests.get(f"{API_BASE}/certificate-abbreviation-mappings", 
                                                      headers=self.get_headers())
                            
                            if get_response.status_code == 200:
                                mappings = get_response.json()
                                updated_mapping = next((m for m in mappings if m['id'] == mapping_id), None)
                                
                                if updated_mapping:
                                    new_usage_count = updated_mapping.get('usage_count', 0)
                                    
                                    if new_usage_count > initial_usage_count:
                                        self.log_test("Usage Count Increment", True, 
                                                    f"Usage count incremented from {initial_usage_count} to {new_usage_count}")
                                        
                                        # Clean up
                                        requests.delete(f"{API_BASE}/certificates/{cert['id']}", 
                                                      headers=self.get_headers())
                                        requests.delete(f"{API_BASE}/certificate-abbreviation-mappings/{mapping_id}", 
                                                      headers=self.get_headers())
                                        return True
                                    else:
                                        self.log_test("Usage Count Increment", False, 
                                                    error=f"Usage count not incremented: {initial_usage_count} -> {new_usage_count}")
                                        return False
                                else:
                                    self.log_test("Usage Count Increment", False, 
                                                error="Mapping not found after certificate creation")
                                    return False
                            else:
                                self.log_test("Usage Count Increment", False, 
                                            error=f"Failed to retrieve mappings: {get_response.text}")
                                return False
                        else:
                            self.log_test("Usage Count Increment", False, 
                                        error=f"Failed to create test certificate: {cert_response.text}")
                            return False
                    else:
                        self.log_test("Usage Count Increment", False, 
                                    error="No ships available for testing")
                        return False
                else:
                    self.log_test("Usage Count Increment", False, 
                                error=f"Failed to get ships: {ship_response.text}")
                    return False
            else:
                self.log_test("Usage Count Increment", False, 
                            error=f"Failed to create mapping: {create_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Usage Count Increment", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all database integration tests"""
        print("🧪 DATABASE INTEGRATION TESTING FOR CERTIFICATE ABBREVIATION MAPPING SYSTEM")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Test database persistence
        self.test_database_persistence()
        
        # Step 3: Test usage count increment
        self.test_usage_count_increment()
        
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
            print("\n🎉 ALL DATABASE INTEGRATION TESTS PASSED!")
            return True
        else:
            print(f"\n❌ {total - passed} tests failed. Please review the issues above.")
            return False

def main():
    """Main test execution"""
    tester = DatabaseIntegrationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
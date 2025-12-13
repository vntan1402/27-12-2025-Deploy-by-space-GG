#!/usr/bin/env python3
"""
🧪 SHIP CERTIFICATE AUDIT LOGGING - COMPREHENSIVE TEST SUITE

This test suite verifies that ship certificate operations (CREATE, UPDATE, DELETE)
properly generate audit logs as required by the P0 bug fix.

Test Coverage:
1. CREATE Certificate Audit Logging (IOPP, ISPP, Load Line, etc.)
2. UPDATE Certificate Audit Logging with field changes
3. DELETE Certificate Audit Logging with data preservation
4. Integration with Audit Logs API and filtering
5. Role-based access verification
6. Metadata structure validation
7. Different certificate types testing
"""

import requests
import json
import time
from datetime import datetime, timedelta
import unittest

class ShipCertificateAuditLogsTest(unittest.TestCase):
    """Test suite for ship certificate audit logging"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.BACKEND_URL = "https://safety-sys-manager.preview.emergentagent.com/api"
        cls.USERNAME = "admin1"
        cls.PASSWORD = "123456"
        
        # Login and get token
        cls.token = cls._login()
        cls.headers = {"Authorization": f"Bearer {cls.token}"}
        
        # Get test ship ID
        cls.ship_id = cls._get_test_ship_id()
        if not cls.ship_id:
            raise Exception("No test ship available")
        
        print(f"🚢 Using test ship ID: {cls.ship_id}")
    
    @classmethod
    def _login(cls):
        """Login and return access token"""
        response = requests.post(f"{cls.BACKEND_URL}/auth/login", 
                               json={"username": cls.USERNAME, "password": cls.PASSWORD})
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.status_code}")
        return response.json()["access_token"]
    
    @classmethod
    def _get_test_ship_id(cls):
        """Get a test ship ID"""
        response = requests.get(f"{cls.BACKEND_URL}/ships?limit=1", headers=cls.headers)
        if response.status_code == 200:
            ships = response.json()
            if ships and len(ships) > 0:
                return ships[0].get('id')
        return None
    
    def _create_certificate(self, cert_name, cert_no, cert_type="Full Term", 
                          issue_date="2024-01-15", valid_date="2027-01-15", 
                          issued_by="DNV"):
        """Helper to create a certificate"""
        cert_data = {
            "ship_id": self.ship_id,
            "cert_name": cert_name,
            "cert_no": cert_no,
            "cert_type": cert_type,
            "issue_date": issue_date,
            "valid_date": valid_date,
            "issued_by": issued_by,
            "status": "Valid"
        }
        
        response = requests.post(f"{self.BACKEND_URL}/certificates", 
                               headers=self.headers, json=cert_data)
        return response
    
    def _update_certificate(self, cert_id, updates):
        """Helper to update a certificate"""
        response = requests.put(f"{self.BACKEND_URL}/certificates/{cert_id}", 
                              headers=self.headers, json=updates)
        return response
    
    def _delete_certificate(self, cert_id):
        """Helper to delete a certificate"""
        response = requests.delete(f"{self.BACKEND_URL}/certificates/{cert_id}", 
                                 headers=self.headers)
        return response
    
    def _get_audit_logs(self, entity_type=None, action=None, limit=10):
        """Helper to get audit logs"""
        params = {"limit": limit}
        if entity_type:
            params["entity_type"] = entity_type
        if action:
            params["action"] = action
        
        response = requests.get(f"{self.BACKEND_URL}/audit-logs", 
                              headers=self.headers, params=params)
        return response
    
    def _verify_audit_log_structure(self, log, expected_action, expected_entity_type="ship_certificate"):
        """Verify audit log structure"""
        required_fields = [
            'id', 'entity_type', 'entity_id', 'entity_name', 'action',
            'performed_by', 'performed_by_id', 'performed_by_name', 
            'performed_at', 'changes', 'company_id', 'ship_name', 'metadata'
        ]
        
        # Check required fields
        for field in required_fields:
            self.assertIn(field, log, f"Missing required field: {field}")
        
        # Check entity type and action
        self.assertEqual(log['entity_type'], expected_entity_type)
        self.assertEqual(log['action'], expected_action)
        
        # Check metadata for ship certificates
        if expected_entity_type == "ship_certificate":
            metadata = log.get('metadata', {})
            self.assertIn('certificate_id', metadata)
            self.assertIn('certificate_name', metadata)
        
        return True
    
    def test_01_create_iopp_certificate_audit_logging(self):
        """Test CREATE audit logging for IOPP certificate"""
        print("\n🧪 Test 1: CREATE IOPP Certificate Audit Logging")
        
        # Get initial count
        initial_response = self._get_audit_logs(entity_type="ship_certificate")
        self.assertEqual(initial_response.status_code, 200)
        initial_count = initial_response.json().get('total', 0)
        
        # Create IOPP certificate
        response = self._create_certificate("IOPP CERTIFICATE", "IOPP_TEST_001")
        self.assertEqual(response.status_code, 200)
        
        cert_data = response.json()
        cert_id = cert_data.get('id')
        self.assertIsNotNone(cert_id)
        
        # Wait for audit log
        time.sleep(1)
        
        # Verify CREATE audit log
        logs_response = self._get_audit_logs(entity_type="ship_certificate", 
                                           action="CREATE_SHIP_CERTIFICATE")
        self.assertEqual(logs_response.status_code, 200)
        
        logs = logs_response.json().get('logs', [])
        self.assertGreater(len(logs), 0, "No CREATE audit logs found")
        
        latest_log = logs[0]
        self._verify_audit_log_structure(latest_log, "CREATE_SHIP_CERTIFICATE")
        
        # Verify specific fields
        self.assertEqual(latest_log['metadata']['certificate_name'], "IOPP CERTIFICATE")
        self.assertEqual(latest_log['metadata']['certificate_number'], "IOPP_TEST_001")
        self.assertIsNotNone(latest_log['ship_name'])
        self.assertIsNotNone(latest_log['company_id'])
        
        # Verify changes structure
        changes = latest_log['changes']
        self.assertIsInstance(changes, list)
        self.assertGreater(len(changes), 0)
        
        # Clean up
        self._delete_certificate(cert_id)
        print("   ✅ IOPP CREATE audit logging verified")
    
    def test_02_create_ispp_certificate_audit_logging(self):
        """Test CREATE audit logging for ISPP certificate"""
        print("\n🧪 Test 2: CREATE ISPP Certificate Audit Logging")
        
        # Create ISPP certificate
        response = self._create_certificate("ISPP CERTIFICATE", "ISPP_TEST_001")
        self.assertEqual(response.status_code, 200)
        
        cert_id = response.json().get('id')
        time.sleep(1)
        
        # Verify audit log
        logs_response = self._get_audit_logs(entity_type="ship_certificate", 
                                           action="CREATE_SHIP_CERTIFICATE")
        self.assertEqual(logs_response.status_code, 200)
        
        logs = logs_response.json().get('logs', [])
        latest_log = logs[0]
        
        self.assertEqual(latest_log['metadata']['certificate_name'], "ISPP CERTIFICATE")
        self.assertEqual(latest_log['metadata']['certificate_number'], "ISPP_TEST_001")
        
        # Clean up
        self._delete_certificate(cert_id)
        print("   ✅ ISPP CREATE audit logging verified")
    
    def test_03_create_load_line_certificate_audit_logging(self):
        """Test CREATE audit logging for Load Line certificate"""
        print("\n🧪 Test 3: CREATE Load Line Certificate Audit Logging")
        
        # Create Load Line certificate
        response = self._create_certificate("LOAD LINE CERTIFICATE", "LL_TEST_001")
        self.assertEqual(response.status_code, 200)
        
        cert_id = response.json().get('id')
        time.sleep(1)
        
        # Verify audit log
        logs_response = self._get_audit_logs(entity_type="ship_certificate", 
                                           action="CREATE_SHIP_CERTIFICATE")
        self.assertEqual(logs_response.status_code, 200)
        
        logs = logs_response.json().get('logs', [])
        latest_log = logs[0]
        
        self.assertEqual(latest_log['metadata']['certificate_name'], "LOAD LINE CERTIFICATE")
        
        # Clean up
        self._delete_certificate(cert_id)
        print("   ✅ Load Line CREATE audit logging verified")
    
    def test_04_update_certificate_audit_logging(self):
        """Test UPDATE audit logging with field changes"""
        print("\n🧪 Test 4: UPDATE Certificate Audit Logging")
        
        # Create certificate
        response = self._create_certificate("IOPP RENEWAL", "IOPP_UPD_001")
        self.assertEqual(response.status_code, 200)
        cert_id = response.json().get('id')
        
        time.sleep(1)
        
        # Update certificate
        updates = {
            "cert_no": "IOPP_UPD_001_MODIFIED",
            "issue_date": "2024-03-15",
            "valid_date": "2027-03-15",
            "issued_by": "Lloyd's Register",
            "last_endorse": "2024-06-15"
        }
        
        update_response = self._update_certificate(cert_id, updates)
        self.assertEqual(update_response.status_code, 200)
        
        time.sleep(1)
        
        # Verify UPDATE audit log
        logs_response = self._get_audit_logs(entity_type="ship_certificate", 
                                           action="UPDATE_SHIP_CERTIFICATE")
        self.assertEqual(logs_response.status_code, 200)
        
        logs = logs_response.json().get('logs', [])
        self.assertGreater(len(logs), 0)
        
        latest_log = logs[0]
        self._verify_audit_log_structure(latest_log, "UPDATE_SHIP_CERTIFICATE")
        
        # Verify changes captured
        changes = latest_log['changes']
        change_fields = [change['field'] for change in changes]
        
        expected_changes = ['cert_no', 'issue_date', 'valid_date', 'issued_by', 'last_endorse']
        for expected_field in expected_changes:
            self.assertIn(expected_field, change_fields, 
                         f"Expected change field {expected_field} not found")
        
        # Verify specific change values
        cert_no_change = next((c for c in changes if c['field'] == 'cert_no'), None)
        self.assertIsNotNone(cert_no_change)
        self.assertEqual(cert_no_change['old_value'], "IOPP_UPD_001")
        self.assertEqual(cert_no_change['new_value'], "IOPP_UPD_001_MODIFIED")
        
        # Clean up
        self._delete_certificate(cert_id)
        print("   ✅ UPDATE audit logging verified")
    
    def test_05_delete_certificate_audit_logging(self):
        """Test DELETE audit logging with data preservation"""
        print("\n🧪 Test 5: DELETE Certificate Audit Logging")
        
        # Create certificate
        response = self._create_certificate("ISSC CERTIFICATE", "ISSC_DEL_001")
        self.assertEqual(response.status_code, 200)
        cert_id = response.json().get('id')
        
        time.sleep(1)
        
        # Delete certificate
        delete_response = self._delete_certificate(cert_id)
        self.assertEqual(delete_response.status_code, 200)
        
        time.sleep(1)
        
        # Verify DELETE audit log
        logs_response = self._get_audit_logs(entity_type="ship_certificate", 
                                           action="DELETE_SHIP_CERTIFICATE")
        self.assertEqual(logs_response.status_code, 200)
        
        logs = logs_response.json().get('logs', [])
        self.assertGreater(len(logs), 0)
        
        latest_log = logs[0]
        self._verify_audit_log_structure(latest_log, "DELETE_SHIP_CERTIFICATE")
        
        # Verify certificate data preserved in audit log
        metadata = latest_log['metadata']
        self.assertEqual(metadata['certificate_name'], "ISSC CERTIFICATE")
        self.assertEqual(metadata['certificate_number'], "ISSC_DEL_001")
        
        # Verify certificate is actually deleted (should return 404)
        get_response = requests.get(f"{self.BACKEND_URL}/certificates/{cert_id}", 
                                  headers=self.headers)
        self.assertEqual(get_response.status_code, 404)
        
        print("   ✅ DELETE audit logging verified")
    
    def test_06_audit_logs_api_integration(self):
        """Test integration with Audit Logs API"""
        print("\n🧪 Test 6: Audit Logs API Integration")
        
        # Test entity_type filter
        response = self._get_audit_logs(entity_type="ship_certificate", limit=5)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('logs', data)
        self.assertIn('total', data)
        
        # Verify all logs have correct entity_type
        logs = data.get('logs', [])
        for log in logs:
            self.assertEqual(log['entity_type'], 'ship_certificate')
        
        print(f"   ✅ Entity type filter working: {data.get('total', 0)} ship_certificate logs")
        
        # Test action filtering
        actions = ['CREATE_SHIP_CERTIFICATE', 'UPDATE_SHIP_CERTIFICATE', 'DELETE_SHIP_CERTIFICATE']
        for action in actions:
            action_response = self._get_audit_logs(entity_type="ship_certificate", 
                                                 action=action, limit=1)
            self.assertEqual(action_response.status_code, 200)
            action_data = action_response.json()
            
            if action_data.get('logs'):
                log = action_data['logs'][0]
                self.assertEqual(log['action'], action)
        
        print("   ✅ Action filtering working for all certificate actions")
    
    def test_07_role_based_access_verification(self):
        """Test role-based access to audit logs"""
        print("\n🧪 Test 7: Role-based Access Verification")
        
        # Admin should be able to access all audit logs
        response = self._get_audit_logs(limit=10)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertGreater(data.get('total', 0), 0)
        
        print(f"   ✅ Admin can access all audit logs: {data.get('total', 0)} total logs")
        
        # Verify logs contain proper user information
        logs = data.get('logs', [])
        if logs:
            log = logs[0]
            self.assertIsNotNone(log.get('performed_by'))
            self.assertIsNotNone(log.get('performed_by_id'))
            self.assertIsNotNone(log.get('performed_by_name'))
        
        print("   ✅ User information properly recorded in audit logs")
    
    def test_08_metadata_structure_validation(self):
        """Test metadata structure in audit logs"""
        print("\n🧪 Test 8: Metadata Structure Validation")
        
        # Create a certificate to generate fresh audit log
        response = self._create_certificate("METADATA_TEST_CERT", "META_001")
        self.assertEqual(response.status_code, 200)
        cert_id = response.json().get('id')
        
        time.sleep(1)
        
        # Get the audit log
        logs_response = self._get_audit_logs(entity_type="ship_certificate", 
                                           action="CREATE_SHIP_CERTIFICATE", limit=1)
        self.assertEqual(logs_response.status_code, 200)
        
        logs = logs_response.json().get('logs', [])
        self.assertGreater(len(logs), 0)
        
        log = logs[0]
        metadata = log.get('metadata', {})
        
        # Verify required metadata fields
        required_metadata = ['certificate_id', 'certificate_name', 'certificate_number']
        for field in required_metadata:
            self.assertIn(field, metadata, f"Missing metadata field: {field}")
        
        # Verify metadata values
        self.assertEqual(metadata['certificate_name'], "METADATA_TEST_CERT")
        self.assertEqual(metadata['certificate_number'], "META_001")
        self.assertEqual(metadata['certificate_id'], cert_id)
        
        # Clean up
        self._delete_certificate(cert_id)
        print("   ✅ Metadata structure validation passed")

def run_tests():
    """Run all tests"""
    print("🧪 SHIP CERTIFICATE AUDIT LOGGING - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(ShipCertificateAuditLogsTest)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=None)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ ALL SHIP CERTIFICATE AUDIT LOGGING TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
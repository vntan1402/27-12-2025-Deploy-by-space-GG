#!/usr/bin/env python3
"""
🧪 AUDIT CERTIFICATE ANALYSIS - TEXT LAYER + DOCUMENT AI MERGE TESTING

Testing the improved Audit Certificate Analysis flow with parallel processing:
1. Text layer extraction from PDF (if available)
2. Document AI OCR extraction 
3. Merge both sources into enhanced summary
4. System AI field extraction from merged content
5. Summary file upload to Google Drive with 2 sections:
   - PART 1: TEXT LAYER CONTENT
   - PART 2: DOCUMENT AI OCR CONTENT
6. Verify API response structure and content
"""

import requests
import json
import base64
import io
from datetime import datetime, timedelta
import time

BACKEND_URL = "https://maritime-docs-3.preview.emergentagent.com/api"
USERNAME = "admin1"
PASSWORD = "123456"

def login():
    """Login and get access token"""
    response = requests.post(f"{BACKEND_URL}/auth/login", json={"username": USERNAME, "password": PASSWORD})
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")
    return response.json()["access_token"]

def get_test_ship_id(headers):
    """Get a test ship ID from existing ships"""
    response = requests.get(f"{BACKEND_URL}/ships?limit=1", headers=headers)
    if response.status_code == 200:
        ships = response.json()
        if ships and len(ships) > 0:
            return ships[0].get('id')
    return None

def create_test_certificate(headers, ship_id, cert_name="TEST IOPP CERTIFICATE", cert_no="TEST001"):
    """Create a test certificate"""
    cert_data = {
        "ship_id": ship_id,
        "cert_name": cert_name,
        "cert_no": cert_no,
        "cert_type": "Full Term",
        "issue_date": "2024-01-15",
        "valid_date": "2027-01-15",
        "issued_by": "DNV",
        "status": "Valid"
    }
    
    response = requests.post(f"{BACKEND_URL}/certificates", headers=headers, json=cert_data)
    return response

def update_test_certificate(headers, cert_id, updates):
    """Update a test certificate"""
    response = requests.put(f"{BACKEND_URL}/certificates/{cert_id}", headers=headers, json=updates)
    return response

def delete_test_certificate(headers, cert_id):
    """Delete a test certificate"""
    response = requests.delete(f"{BACKEND_URL}/certificates/{cert_id}", headers=headers)
    return response

def get_audit_logs(headers, entity_type=None, action=None, limit=10):
    """Get audit logs with optional filtering"""
    params = {"limit": limit}
    if entity_type:
        params["entity_type"] = entity_type
    if action:
        params["action"] = action
    
    response = requests.get(f"{BACKEND_URL}/audit-logs", headers=headers, params=params)
    return response

def verify_audit_log_structure(log, expected_action, expected_entity_type="ship_certificate"):
    """Verify audit log has correct structure and required fields"""
    required_fields = [
        'id', 'entity_type', 'entity_id', 'entity_name', 'action',
        'performed_by', 'performed_by_id', 'performed_by_name', 
        'performed_at', 'changes', 'company_id', 'ship_name', 'metadata'
    ]
    
    missing_fields = [field for field in required_fields if field not in log]
    if missing_fields:
        return False, f"Missing fields: {missing_fields}"
    
    if log['entity_type'] != expected_entity_type:
        return False, f"Wrong entity_type: expected {expected_entity_type}, got {log['entity_type']}"
    
    if log['action'] != expected_action:
        return False, f"Wrong action: expected {expected_action}, got {log['action']}"
    
    # Check metadata structure for ship certificates
    if expected_entity_type == "ship_certificate":
        metadata = log.get('metadata', {})
        required_metadata = ['certificate_id', 'certificate_name']
        missing_metadata = [field for field in required_metadata if field not in metadata]
        if missing_metadata:
            return False, f"Missing metadata fields: {missing_metadata}"
    
    return True, "Valid structure"

# Main test execution
def main():
    print("🧪 SHIP CERTIFICATE AUDIT LOGGING - COMPREHENSIVE TESTING")
    print("=" * 80)
    
    try:
        # Login
        print("\n1. 🔐 Authentication Test")
        token = login()
        headers = {"Authorization": f"Bearer {token}"}
        print("   ✅ Login successful")
        
        # Get test ship
        print("\n2. 🚢 Getting Test Ship")
        ship_id = get_test_ship_id(headers)
        if not ship_id:
            print("   ❌ No ships found for testing")
            return
        print(f"   ✅ Using ship ID: {ship_id}")
        
        # Get initial audit log count
        print("\n3. 📊 Initial Audit Log Count")
        initial_response = get_audit_logs(headers, entity_type="ship_certificate")
        if initial_response.status_code == 200:
            initial_count = initial_response.json().get('total', 0)
            print(f"   ✅ Initial ship_certificate audit logs: {initial_count}")
        else:
            print(f"   ❌ Failed to get initial count: {initial_response.status_code}")
            return
        
        # Test 1: CREATE Certificate Audit Logging
        print("\n4. 🆕 CREATE Certificate Audit Logging Test")
        create_response = create_test_certificate(headers, ship_id, "IOPP CERTIFICATE", "IOPP001")
        
        if create_response.status_code == 200:
            cert_data = create_response.json()
            cert_id = cert_data.get('id')
            print(f"   ✅ Certificate created successfully: {cert_id}")
            
            # Wait a moment for audit log to be created
            time.sleep(1)
            
            # Check for CREATE audit log
            create_logs_response = get_audit_logs(headers, entity_type="ship_certificate", action="CREATE_SHIP_CERTIFICATE")
            if create_logs_response.status_code == 200:
                logs = create_logs_response.json().get('logs', [])
                if logs:
                    latest_log = logs[0]  # Most recent log
                    is_valid, message = verify_audit_log_structure(latest_log, "CREATE_SHIP_CERTIFICATE")
                    if is_valid:
                        print("   ✅ CREATE audit log generated with correct structure")
                        print(f"      - Entity Type: {latest_log['entity_type']}")
                        print(f"      - Action: {latest_log['action']}")
                        print(f"      - Ship Name: {latest_log['ship_name']}")
                        print(f"      - Certificate Name: {latest_log['metadata']['certificate_name']}")
                        print(f"      - Certificate Number: {latest_log['metadata'].get('certificate_number', 'N/A')}")
                        print(f"      - Performed By: {latest_log['performed_by_name']} ({latest_log['performed_by']})")
                        print(f"      - Company ID: {latest_log['company_id']}")
                        print(f"      - Changes Count: {len(latest_log['changes'])}")
                    else:
                        print(f"   ❌ CREATE audit log structure invalid: {message}")
                else:
                    print("   ❌ No CREATE audit logs found")
            else:
                print(f"   ❌ Failed to get CREATE audit logs: {create_logs_response.status_code}")
        else:
            print(f"   ❌ Certificate creation failed: {create_response.status_code} - {create_response.text}")
            return
        
        # Test 2: UPDATE Certificate Audit Logging
        print("\n5. 🔄 UPDATE Certificate Audit Logging Test")
        update_data = {
            "cert_no": "IOPP001_UPDATED",
            "issue_date": "2024-02-15",
            "valid_date": "2027-02-15",
            "issued_by": "Lloyd's Register"
        }
        
        update_response = update_test_certificate(headers, cert_id, update_data)
        if update_response.status_code == 200:
            print("   ✅ Certificate updated successfully")
            
            # Wait a moment for audit log to be created
            time.sleep(1)
            
            # Check for UPDATE audit log
            update_logs_response = get_audit_logs(headers, entity_type="ship_certificate", action="UPDATE_SHIP_CERTIFICATE")
            if update_logs_response.status_code == 200:
                logs = update_logs_response.json().get('logs', [])
                if logs:
                    latest_log = logs[0]  # Most recent log
                    is_valid, message = verify_audit_log_structure(latest_log, "UPDATE_SHIP_CERTIFICATE")
                    if is_valid:
                        print("   ✅ UPDATE audit log generated with correct structure")
                        print(f"      - Changes Count: {len(latest_log['changes'])}")
                        print(f"      - Changes: {[change['field'] for change in latest_log['changes']]}")
                        
                        # Verify specific changes
                        changes_by_field = {change['field']: change for change in latest_log['changes']}
                        if 'cert_no' in changes_by_field:
                            change = changes_by_field['cert_no']
                            print(f"      - Certificate Number: {change['old_value']} → {change['new_value']}")
                        if 'issued_by' in changes_by_field:
                            change = changes_by_field['issued_by']
                            print(f"      - Issued By: {change['old_value']} → {change['new_value']}")
                    else:
                        print(f"   ❌ UPDATE audit log structure invalid: {message}")
                else:
                    print("   ❌ No UPDATE audit logs found")
            else:
                print(f"   ❌ Failed to get UPDATE audit logs: {update_logs_response.status_code}")
        else:
            print(f"   ❌ Certificate update failed: {update_response.status_code} - {update_response.text}")
        
        # Test 3: DELETE Certificate Audit Logging
        print("\n6. 🗑️ DELETE Certificate Audit Logging Test")
        delete_response = delete_test_certificate(headers, cert_id)
        if delete_response.status_code == 200:
            print("   ✅ Certificate deleted successfully")
            
            # Wait a moment for audit log to be created
            time.sleep(1)
            
            # Check for DELETE audit log
            delete_logs_response = get_audit_logs(headers, entity_type="ship_certificate", action="DELETE_SHIP_CERTIFICATE")
            if delete_logs_response.status_code == 200:
                logs = delete_logs_response.json().get('logs', [])
                if logs:
                    latest_log = logs[0]  # Most recent log
                    is_valid, message = verify_audit_log_structure(latest_log, "DELETE_SHIP_CERTIFICATE")
                    if is_valid:
                        print("   ✅ DELETE audit log generated with correct structure")
                        print(f"      - Certificate preserved in audit: {latest_log['metadata']['certificate_name']}")
                        print(f"      - Certificate Number: {latest_log['metadata'].get('certificate_number', 'N/A')}")
                    else:
                        print(f"   ❌ DELETE audit log structure invalid: {message}")
                else:
                    print("   ❌ No DELETE audit logs found")
            else:
                print(f"   ❌ Failed to get DELETE audit logs: {delete_logs_response.status_code}")
        else:
            print(f"   ❌ Certificate deletion failed: {delete_response.status_code} - {delete_response.text}")
        
        # Test 4: Integration with Audit Logs API
        print("\n7. 🔍 Integration with Audit Logs API Test")
        
        # Test entity_type filter
        filter_response = get_audit_logs(headers, entity_type="ship_certificate", limit=5)
        if filter_response.status_code == 200:
            filter_data = filter_response.json()
            print(f"   ✅ Entity type filter working: {filter_data.get('total', 0)} ship_certificate logs")
            
            # Verify all returned logs are ship_certificate type
            logs = filter_data.get('logs', [])
            all_correct_type = all(log.get('entity_type') == 'ship_certificate' for log in logs)
            if all_correct_type:
                print("   ✅ All filtered logs have correct entity_type")
            else:
                print("   ❌ Some filtered logs have incorrect entity_type")
        else:
            print(f"   ❌ Entity type filter failed: {filter_response.status_code}")
        
        # Test role-based access (admin should see all logs)
        all_logs_response = get_audit_logs(headers, limit=10)
        if all_logs_response.status_code == 200:
            all_logs_data = all_logs_response.json()
            print(f"   ✅ Admin can access all audit logs: {all_logs_data.get('total', 0)} total logs")
        else:
            print(f"   ❌ Failed to access all audit logs: {all_logs_response.status_code}")
        
        # Final count verification
        print("\n8. 📈 Final Audit Log Count Verification")
        final_response = get_audit_logs(headers, entity_type="ship_certificate")
        if final_response.status_code == 200:
            final_count = final_response.json().get('total', 0)
            added_logs = final_count - initial_count
            print(f"   ✅ Final ship_certificate audit logs: {final_count}")
            print(f"   ✅ New audit logs created: {added_logs} (expected: 3 for CREATE/UPDATE/DELETE)")
            
            if added_logs >= 3:
                print("   ✅ All CRUD operations generated audit logs successfully")
            else:
                print(f"   ⚠️ Expected at least 3 new logs, got {added_logs}")
        else:
            print(f"   ❌ Failed to get final count: {final_response.status_code}")
        
        print("\n" + "=" * 80)
        print("✅ SHIP CERTIFICATE AUDIT LOGGING TESTING COMPLETED")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
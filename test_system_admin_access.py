#!/usr/bin/env python3
"""
🧪 SYSTEM ADMIN ACCESS TEST

Test system_admin role access to ship certificate audit logs
"""

import requests
import json

BACKEND_URL = "https://marinetec-safety.preview.emergentagent.com/api"
SYSTEM_ADMIN_USERNAME = "system_admin"
SYSTEM_ADMIN_PASSWORD = "YourSecure@Pass2024"

def login_system_admin():
    """Login as system_admin"""
    response = requests.post(f"{BACKEND_URL}/auth/login", 
                           json={"username": SYSTEM_ADMIN_USERNAME, "password": SYSTEM_ADMIN_PASSWORD})
    if response.status_code != 200:
        raise Exception(f"System admin login failed: {response.status_code} - {response.text}")
    return response.json()["access_token"]

def test_system_admin_audit_access():
    """Test system admin access to audit logs"""
    print("🧪 SYSTEM ADMIN AUDIT LOG ACCESS TEST")
    print("=" * 60)
    
    try:
        # Login as system_admin
        print("\n1. 🔐 System Admin Authentication")
        token = login_system_admin()
        headers = {"Authorization": f"Bearer {token}"}
        print("   ✅ System admin login successful")
        
        # Test access to all audit logs
        print("\n2. 📊 System Admin Audit Log Access")
        response = requests.get(f"{BACKEND_URL}/audit-logs?limit=10", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            total_logs = data.get('total', 0)
            returned_logs = len(data.get('logs', []))
            print(f"   ✅ System admin can access all audit logs")
            print(f"   📊 Total logs: {total_logs}")
            print(f"   📊 Returned logs: {returned_logs}")
        else:
            print(f"   ❌ System admin audit log access failed: {response.status_code}")
            return False
        
        # Test ship_certificate specific logs
        print("\n3. 🚢 Ship Certificate Audit Logs Access")
        response = requests.get(f"{BACKEND_URL}/audit-logs?entity_type=ship_certificate&limit=5", 
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            cert_logs = data.get('total', 0)
            print(f"   ✅ System admin can access ship certificate logs")
            print(f"   📊 Ship certificate logs: {cert_logs}")
            
            # Show sample log structure
            logs = data.get('logs', [])
            if logs:
                sample_log = logs[0]
                print(f"   📋 Sample log action: {sample_log.get('action')}")
                print(f"   📋 Sample log entity: {sample_log.get('entity_name')}")
                print(f"   📋 Sample log performed by: {sample_log.get('performed_by_name')}")
        else:
            print(f"   ❌ Ship certificate logs access failed: {response.status_code}")
            return False
        
        # Test filtering by action
        print("\n4. 🔍 Action Filtering Test")
        actions = ['CREATE_SHIP_CERTIFICATE', 'UPDATE_SHIP_CERTIFICATE', 'DELETE_SHIP_CERTIFICATE']
        
        for action in actions:
            response = requests.get(f"{BACKEND_URL}/audit-logs?entity_type=ship_certificate&action={action}&limit=1", 
                                  headers=headers)
            if response.status_code == 200:
                count = response.json().get('total', 0)
                print(f"   ✅ {action}: {count} logs")
            else:
                print(f"   ❌ {action}: Failed to access")
        
        print("\n" + "=" * 60)
        print("✅ SYSTEM ADMIN AUDIT LOG ACCESS TEST COMPLETED")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_system_admin_audit_access()
    exit(0 if success else 1)
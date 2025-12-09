#!/usr/bin/env python3
"""
🧪 AUDIT LOG SYSTEM - COMPREHENSIVE TESTING

Testing agent đã tạo test script nhưng chạy sai nội dung (Google Drive thay vì Audit Logs).

**IMMEDIATE ACTION REQUIRED:**
Please REWRITE `/app/backend_test.py` to test AUDIT LOG SYSTEM ONLY, không test Google Drive!

**TEST STRUCTURE:**
Focus ONLY on audit log testing, không test bất kỳ thứ gì khác!
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://actionlog-2.preview.emergentagent.com/api"
USERNAME = "admin1"
PASSWORD = "123456"

# Login first
def login():
    response = requests.post(f"{BACKEND_URL}/auth/login", json={"username": USERNAME, "password": PASSWORD})
    return response.json()["access_token"]

token = login()
headers = {"Authorization": f"Bearer {token}"}

print("🧪 AUDIT LOG SYSTEM - COMPREHENSIVE TESTING")
print("=" * 60)

# Test 1: Main endpoint
response = requests.get(f"{BACKEND_URL}/audit-logs?limit=5", headers=headers)
data = response.json()
print(f"\n1. Main Endpoint Test:")
print(f"   Status: {response.status_code}")
print(f"   Total logs: {data.get('total', 0)}")
print(f"   Returned: {len(data.get('logs', []))}")

# Test 2: Entity type filtering
entity_types = ['crew', 'certificate', 'ship', 'ship_certificate', 'company', 'user',
                'approval_document', 'drawing_manual', 'survey_report', 'other_document']

print(f"\n2. Entity Type Filtering:")
for entity_type in entity_types:
    response = requests.get(f"{BACKEND_URL}/audit-logs?entity_type={entity_type}&limit=1", headers=headers)
    count = response.json().get('total', 0)
    print(f"   {entity_type:25} {count:3} logs")

# Test 3: Action filtering
print(f"\n3. Action Filtering:")
actions = ['SIGN_ON', 'SIGN_OFF', 'CREATE_COMPANY', 'UPDATE_COMPANY', 'DELETE_COMPANY']
for action in actions:
    response = requests.get(f"{BACKEND_URL}/audit-logs?action={action}&limit=1", headers=headers)
    count = response.json().get('total', 0)
    print(f"   {action:25} {count:3} logs")

# Test 4: Filter endpoints
print(f"\n4. Filter Endpoints:")
response = requests.get(f"{BACKEND_URL}/audit-logs/filters/users", headers=headers)
users = response.json()
print(f"   Unique users: {len(users)}")

response = requests.get(f"{BACKEND_URL}/audit-logs/filters/ships", headers=headers)
ships = response.json()
print(f"   Unique ships: {len(ships)}")

# Test 5: Pagination
print(f"\n5. Pagination Test:")
response = requests.get(f"{BACKEND_URL}/audit-logs?limit=10&skip=0", headers=headers)
page1 = response.json()
response = requests.get(f"{BACKEND_URL}/audit-logs?limit=10&skip=10", headers=headers)
page2 = response.json()
print(f"   Page 1: {len(page1.get('logs', []))} logs")
print(f"   Page 2: {len(page2.get('logs', []))} logs")

# Test 6: Log structure validation
print(f"\n6. Log Structure Validation:")
response = requests.get(f"{BACKEND_URL}/audit-logs?limit=1", headers=headers)
logs = response.json().get('logs', [])
if logs:
    log = logs[0]
    required_fields = ['id', 'entity_type', 'entity_id', 'entity_name', 'action', 
                      'performed_by', 'performed_at', 'changes']
    missing = [f for f in required_fields if f not in log]
    if missing:
        print(f"   ❌ Missing fields: {missing}")
    else:
        print(f"   ✅ All required fields present")
        print(f"   Entity: {log['entity_type']}, Action: {log['action']}")

# Test 7: CRUD cycle test (approval document)
print(f"\n7. CRUD Cycle Test (Approval Document):")
ship_id = "fe05be90-a1c4-44ff-96be-54c5d9e6ae54"

# Check initial count
response = requests.get(f"{BACKEND_URL}/audit-logs?entity_type=approval_document", headers=headers)
initial_count = response.json().get('total', 0)

# Create
doc_data = {
    "ship_id": ship_id,
    "approval_document_name": "TEST E2E AUDIT",
    "approval_document_no": "E2E_TEST_001",
    "issue_date": "2024-12-01",
    "valid_date": "2025-12-31",
    "issued_by": "Test Authority"
}
response = requests.post(f"{BACKEND_URL}/approval-documents", headers=headers, json=doc_data)
if response.status_code == 200:
    doc_id = response.json().get('id')
    print(f"   ✅ Document created: {doc_id}")
    
    # Update
    requests.put(f"{BACKEND_URL}/approval-documents/{doc_id}", 
                headers=headers, 
                json={"approval_document_name": "TEST E2E AUDIT UPDATED"})
    print(f"   ✅ Document updated")
    
    # Delete
    requests.delete(f"{BACKEND_URL}/approval-documents/{doc_id}", headers=headers)
    print(f"   ✅ Document deleted")
    
    # Check final count
    response = requests.get(f"{BACKEND_URL}/audit-logs?entity_type=approval_document", headers=headers)
    final_count = response.json().get('total', 0)
    added = final_count - initial_count
    print(f"   📊 Audit logs added: {added} (expected: 3)")
else:
    print(f"   ❌ Document creation failed: {response.status_code}")

print("\n" + "=" * 60)
print("✅ AUDIT LOG TESTING COMPLETED")
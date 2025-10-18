#!/usr/bin/env python3
"""
Detailed Certificate Abbreviation Testing
Focus on understanding the exact behavior of cert_abbreviation saving
"""

import requests
import json
import os

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://crew-cert-portal.preview.emergentagent.com') + '/api'

def authenticate():
    """Authenticate and get token"""
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def get_headers(token):
    """Get authentication headers"""
    return {"Authorization": f"Bearer {token}"}

def test_certificate_abbreviation_detailed():
    """Detailed test of certificate abbreviation functionality"""
    print("🔍 DETAILED CERTIFICATE ABBREVIATION TESTING")
    print("=" * 60)
    
    # Authenticate
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = get_headers(token)
    cert_id = "3ce38d28-84d1-4982-87d6-eb32068e981b"  # PM242309 certificate
    
    # Test 1: Get current certificate data
    print("\n📋 Test 1: Get current certificate data")
    response = requests.get(f"{BACKEND_URL}/certificates/{cert_id}", headers=headers)
    if response.status_code == 200:
        cert_data = response.json()
        print(f"   Current abbreviation: {cert_data.get('cert_abbreviation')}")
        print(f"   Certificate name: {cert_data.get('cert_name')}")
    else:
        print(f"   ❌ Failed to get certificate: {response.status_code}")
        return
    
    # Test 2: Update with short abbreviation (should work)
    print("\n🔄 Test 2: Update with short abbreviation 'CLASS'")
    update_data = {"cert_abbreviation": "CLASS"}
    response = requests.put(f"{BACKEND_URL}/certificates/{cert_id}", json=update_data, headers=headers)
    if response.status_code == 200:
        updated_cert = response.json()
        print(f"   ✅ Update successful")
        print(f"   New abbreviation: {updated_cert.get('cert_abbreviation')}")
    else:
        print(f"   ❌ Update failed: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # Test 3: Update with long abbreviation (should be limited)
    print("\n🔄 Test 3: Update with long abbreviation 'CLASSIFICATION'")
    update_data = {"cert_abbreviation": "CLASSIFICATION"}
    response = requests.put(f"{BACKEND_URL}/certificates/{cert_id}", json=update_data, headers=headers)
    if response.status_code == 200:
        updated_cert = response.json()
        print(f"   ✅ Update successful")
        print(f"   New abbreviation: {updated_cert.get('cert_abbreviation')}")
        print(f"   Note: Backend may have validation rules for abbreviation length")
    else:
        print(f"   ❌ Update failed: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # Test 4: Verify database record
    print("\n🔍 Test 4: Verify current database record")
    response = requests.get(f"{BACKEND_URL}/certificates/{cert_id}", headers=headers)
    if response.status_code == 200:
        cert_data = response.json()
        print(f"   Final abbreviation: {cert_data.get('cert_abbreviation')}")
        print(f"   Certificate ID: {cert_data.get('id')}")
        print(f"   Certificate name: {cert_data.get('cert_name')}")
        print(f"   Certificate number: {cert_data.get('cert_no')}")
    
    # Test 5: Update back to original 'CL'
    print("\n🔄 Test 5: Update back to original 'CL'")
    update_data = {"cert_abbreviation": "CL"}
    response = requests.put(f"{BACKEND_URL}/certificates/{cert_id}", json=update_data, headers=headers)
    if response.status_code == 200:
        updated_cert = response.json()
        print(f"   ✅ Update successful")
        print(f"   Final abbreviation: {updated_cert.get('cert_abbreviation')}")
    else:
        print(f"   ❌ Update failed: {response.status_code}")
    
    # Test 6: Check abbreviation mappings
    print("\n🗂️ Test 6: Check abbreviation mappings")
    response = requests.get(f"{BACKEND_URL}/certificate-abbreviation-mappings", headers=headers)
    if response.status_code == 200:
        mappings = response.json()
        print(f"   Found {len(mappings)} abbreviation mappings")
        
        # Look for relevant mappings
        for mapping in mappings:
            if 'CLASSIFICATION' in mapping.get('cert_name', '').upper():
                print(f"   Mapping: {mapping.get('cert_name')} → {mapping.get('abbreviation')}")
                print(f"   Usage count: {mapping.get('usage_count', 0)}")
    else:
        print(f"   ❌ Failed to get mappings: {response.status_code}")
    
    print("\n✅ DETAILED TESTING COMPLETED")

if __name__ == "__main__":
    test_certificate_abbreviation_detailed()
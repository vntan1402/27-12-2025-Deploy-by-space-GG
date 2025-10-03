#!/usr/bin/env python3
"""
Check Certificate Abbreviations - Verify which certificates have missing abbreviations
"""

import requests
import json
import os

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vesseldocs.preview.emergentagent.com') + '/api'

def authenticate():
    """Authenticate with admin1/123456"""
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

def check_specific_certificates():
    """Check the specific certificates that showed different behavior"""
    print("🔍 Checking Specific Certificate Abbreviations")
    print("=" * 60)
    
    # Authenticate
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Certificates to check based on auto-rename results
    certificates_to_check = [
        {
            'id': '3d773205-9f70-4085-b2d5-60858bbdae35',
            'name': 'INTERNATIONAL LOAD LINE CERTIFICATE',
            'ship': 'SUNSHINE STAR',
            'expected_abbrev': 'LL',
            'auto_rename_used': 'INTERNATIONAL_LOAD_LINE_CERTIFICATE'  # Full name used
        },
        {
            'id': '41440429-2673-4c2d-afd2-f5c5c922f650',
            'name': 'INTERNATIONAL LOAD LINE CERTIFICATE',
            'ship': 'MINH ANH 09',
            'expected_abbrev': 'LL',
            'auto_rename_used': 'LL'  # Abbreviation used
        },
        {
            'id': '9dcf4755-dc55-4dab-bd2f-a4a7ae237663',
            'name': 'CLASSIFICATION CERTIFICATE',
            'ship': 'SUNSHINE 01',
            'expected_abbrev': 'CL',
            'auto_rename_used': 'CLASSIFICATION_CERTIFICATE'  # Full name used
        },
        {
            'id': '077344cb-e926-4520-a837-9dcf23c7f346',
            'name': 'CLASSIFICATION CERTIFICATE',
            'ship': 'SUNSHINE STAR',
            'expected_abbrev': 'CL',
            'auto_rename_used': 'CLASSIFICATION_CERTIFICATE'  # Full name used
        }
    ]
    
    certificates_needing_fix = []
    
    for cert in certificates_to_check:
        print(f"\n📋 Certificate: {cert['name']} ({cert['ship']})")
        print(f"   ID: {cert['id']}")
        print(f"   Auto-rename used: {cert['auto_rename_used']}")
        
        # Get certificate details
        endpoint = f"{BACKEND_URL}/certificates/{cert['id']}"
        response = requests.get(endpoint, headers=get_headers(token), timeout=30)
        
        if response.status_code == 200:
            cert_data = response.json()
            cert_abbreviation = cert_data.get('cert_abbreviation')
            
            print(f"   Current cert_abbreviation: {cert_abbreviation}")
            
            if not cert_abbreviation or cert_abbreviation.strip() == '':
                print(f"   ❌ MISSING ABBREVIATION - needs to be updated to '{cert['expected_abbrev']}'")
                certificates_needing_fix.append({
                    'id': cert['id'],
                    'name': cert['name'],
                    'ship': cert['ship'],
                    'current_abbreviation': cert_abbreviation,
                    'needed_abbreviation': cert['expected_abbrev']
                })
            elif cert_abbreviation != cert['expected_abbrev']:
                print(f"   ⚠️ WRONG ABBREVIATION - has '{cert_abbreviation}', should be '{cert['expected_abbrev']}'")
                certificates_needing_fix.append({
                    'id': cert['id'],
                    'name': cert['name'],
                    'ship': cert['ship'],
                    'current_abbreviation': cert_abbreviation,
                    'needed_abbreviation': cert['expected_abbrev']
                })
            else:
                print(f"   ✅ CORRECT ABBREVIATION - has '{cert_abbreviation}'")
        else:
            print(f"   ❌ Failed to get certificate details: {response.status_code}")
    
    # Summary
    print(f"\n📊 CERTIFICATE ABBREVIATION ANALYSIS:")
    print(f"   Total certificates checked: {len(certificates_to_check)}")
    print(f"   Certificates needing fix: {len(certificates_needing_fix)}")
    
    if certificates_needing_fix:
        print(f"\n🔧 CERTIFICATES THAT NEED ABBREVIATION UPDATES:")
        for cert in certificates_needing_fix:
            print(f"   - {cert['ship']}: {cert['name']}")
            print(f"     ID: {cert['id']}")
            print(f"     Current: {cert['current_abbreviation']} → Needed: {cert['needed_abbreviation']}")
        
        # Offer to fix them
        print(f"\n🔧 FIXING CERTIFICATES WITH MISSING/WRONG ABBREVIATIONS...")
        fixed_count = 0
        
        for cert in certificates_needing_fix:
            print(f"\n   Updating: {cert['ship']} - {cert['name']}")
            
            update_data = {
                "cert_abbreviation": cert['needed_abbreviation']
            }
            
            endpoint = f"{BACKEND_URL}/certificates/{cert['id']}"
            response = requests.put(endpoint, json=update_data, headers=get_headers(token), timeout=30)
            
            if response.status_code == 200:
                updated_cert = response.json()
                new_abbreviation = updated_cert.get('cert_abbreviation')
                print(f"      ✅ Updated successfully: {cert['current_abbreviation']} → {new_abbreviation}")
                fixed_count += 1
            else:
                print(f"      ❌ Update failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"         Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"         Error: {response.text[:200]}")
        
        print(f"\n📊 UPDATE SUMMARY:")
        print(f"   Certificates fixed: {fixed_count}/{len(certificates_needing_fix)}")
        
        if fixed_count > 0:
            print(f"\n🔄 TESTING AUTO-RENAME AFTER FIX...")
            # Test auto-rename again for fixed certificates
            for cert in certificates_needing_fix[:2]:  # Test first 2 fixed certificates
                print(f"\n   Testing: {cert['ship']} - {cert['name']}")
                
                endpoint = f"{BACKEND_URL}/certificates/{cert['id']}/auto-rename-file"
                response = requests.post(endpoint, headers=get_headers(token), timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    naming_convention = result.get('naming_convention', {})
                    cert_identifier = naming_convention.get('cert_identifier', '')
                    
                    print(f"      ✅ Auto-rename successful")
                    print(f"      📁 cert_identifier: {cert_identifier}")
                    
                    if cert_identifier == cert['needed_abbreviation']:
                        print(f"      ✅ SUCCESS: Now using abbreviation '{cert['needed_abbreviation']}'!")
                    else:
                        print(f"      ⚠️ Still using: {cert_identifier}")
                else:
                    print(f"      ❌ Auto-rename failed: {response.status_code}")
    else:
        print(f"   ✅ All certificates have correct abbreviations!")

if __name__ == "__main__":
    check_specific_certificates()
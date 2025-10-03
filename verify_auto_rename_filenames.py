#!/usr/bin/env python3
"""
Verify Auto-Rename Filenames - Check if LL and CL abbreviations are being used
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

def test_auto_rename_with_filename_check():
    """Test auto-rename and check actual filenames generated"""
    print("🔄 Testing Auto-Rename Functionality with Filename Verification")
    print("=" * 70)
    
    # Authenticate
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Test certificates (LL and CL certificates found earlier)
    test_certificates = [
        {
            'id': '3d773205-9f70-4085-b2d5-60858bbdae35',
            'name': 'INTERNATIONAL LOAD LINE CERTIFICATE',
            'ship': 'SUNSHINE STAR',
            'expected_abbrev': 'LL'
        },
        {
            'id': '41440429-2673-4c2d-afd2-f5c5c922f650',
            'name': 'INTERNATIONAL LOAD LINE CERTIFICATE',
            'ship': 'MINH ANH 09',
            'expected_abbrev': 'LL'
        },
        {
            'id': '9dcf4755-dc55-4dab-bd2f-a4a7ae237663',
            'name': 'CLASSIFICATION CERTIFICATE',
            'ship': 'SUNSHINE 01',
            'expected_abbrev': 'CL'
        },
        {
            'id': '077344cb-e926-4520-a837-9dcf23c7f346',
            'name': 'CLASSIFICATION CERTIFICATE',
            'ship': 'SUNSHINE STAR',
            'expected_abbrev': 'CL'
        }
    ]
    
    abbreviation_usage_count = 0
    full_name_usage_count = 0
    
    for cert in test_certificates:
        print(f"\n🔍 Testing: {cert['name']} ({cert['ship']})")
        print(f"   Expected abbreviation: {cert['expected_abbrev']}")
        
        # Test auto-rename
        endpoint = f"{BACKEND_URL}/certificates/{cert['id']}/auto-rename-file"
        response = requests.post(endpoint, headers=get_headers(token), timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Auto-rename successful")
            
            # Check the response for filename information
            print(f"   📄 Response: {json.dumps(result, indent=6)}")
            
            # Look for filename in various possible fields
            filename = None
            if 'new_filename' in result:
                filename = result['new_filename']
            elif 'filename' in result:
                filename = result['filename']
            elif 'generated_filename' in result:
                filename = result['generated_filename']
            
            if filename:
                print(f"   📁 Generated filename: {filename}")
                
                # Check if abbreviation is used
                if f"_{cert['expected_abbrev']}_" in filename:
                    print(f"   ✅ ABBREVIATION USED: Found '{cert['expected_abbrev']}' in filename")
                    abbreviation_usage_count += 1
                elif cert['name'].replace(' ', '_').upper() in filename.upper():
                    print(f"   ❌ FULL NAME USED: Found full certificate name in filename")
                    full_name_usage_count += 1
                else:
                    print(f"   ⚠️ UNCLEAR: Cannot determine if abbreviation or full name is used")
            else:
                print(f"   ⚠️ No filename found in response")
                
        else:
            print(f"   ❌ Auto-rename failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"      Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"      Error: {response.text[:200]}")
    
    # Summary
    print(f"\n📊 FILENAME GENERATION SUMMARY:")
    print(f"   Certificates using abbreviations: {abbreviation_usage_count}")
    print(f"   Certificates using full names: {full_name_usage_count}")
    print(f"   Total certificates tested: {len(test_certificates)}")
    
    if abbreviation_usage_count > 0:
        print(f"   ✅ SUCCESS: Auto-rename is using abbreviations!")
    elif full_name_usage_count > 0:
        print(f"   ❌ ISSUE: Auto-rename is using full certificate names instead of abbreviations")
    else:
        print(f"   ⚠️ UNCLEAR: Could not determine filename generation pattern")

if __name__ == "__main__":
    test_auto_rename_with_filename_check()
#!/usr/bin/env python3
"""
Check the newly created certificate for extracted_ship_name field
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://seacraft-portfolio.preview.emergentagent.com') + '/api'

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

def main():
    print("🔍 Checking newly created certificate...")
    
    # Authenticate
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Get SUNSHINE 01 certificates
    response = requests.get(f"{BACKEND_URL}/ships", headers=get_headers(token), timeout=30)
    if response.status_code != 200:
        print("❌ Failed to get ships")
        return
    
    ships = response.json()
    sunshine_ship = None
    
    for ship in ships:
        if 'SUNSHINE 01' in ship.get('name', '').upper():
            sunshine_ship = ship
            break
    
    if not sunshine_ship:
        print("❌ SUNSHINE 01 ship not found")
        return
    
    ship_id = sunshine_ship.get('id')
    print(f"✅ Found SUNSHINE 01 ship: {ship_id}")
    
    # Get certificates
    response = requests.get(f"{BACKEND_URL}/ships/{ship_id}/certificates", headers=get_headers(token), timeout=30)
    if response.status_code != 200:
        print("❌ Failed to get certificates")
        return
    
    certificates = response.json()
    print(f"Found {len(certificates)} certificates")
    
    # Look for the newly created certificate
    test_cert = None
    for cert in certificates:
        if cert.get('cert_no') == 'TEST-CSSC-2025-001':
            test_cert = cert
            break
    
    if not test_cert:
        print("❌ Test certificate not found")
        return
    
    print("✅ Found test certificate")
    print(f"Certificate ID: {test_cert.get('id')}")
    print(f"Certificate Name: {test_cert.get('cert_name')}")
    print(f"Certificate No: {test_cert.get('cert_no')}")
    
    # Check extracted_ship_name field
    extracted_ship_name = test_cert.get('extracted_ship_name')
    print(f"\n🔍 EXTRACTED_SHIP_NAME FIELD CHECK:")
    print(f"   extracted_ship_name: {extracted_ship_name}")
    
    if extracted_ship_name:
        print("🎉 SUCCESS: extracted_ship_name field is populated!")
        print(f"   Value: {extracted_ship_name}")
        print("   The tooltip should now show the extracted ship name")
    else:
        print("❌ ISSUE: extracted_ship_name field is still missing")
        print("   This confirms the backend is not saving the field properly")
    
    # Check if text_content is present
    text_content = test_cert.get('text_content')
    print(f"\n📋 TEXT_CONTENT FIELD CHECK:")
    if text_content:
        print(f"   ✅ text_content present: {len(text_content)} characters")
        print(f"   First 200 chars: {text_content[:200]}...")
        
        # Check if ship name is in text content
        if 'SUNSHINE 01' in text_content:
            print("   ✅ Ship name 'SUNSHINE 01' found in text content")
        else:
            print("   ❌ Ship name 'SUNSHINE 01' not found in text content")
    else:
        print("   ❌ text_content field is missing")
    
    # Show full certificate data for debugging
    print(f"\n📋 FULL CERTIFICATE DATA:")
    print(json.dumps(test_cert, indent=2, default=str))

if __name__ == "__main__":
    main()
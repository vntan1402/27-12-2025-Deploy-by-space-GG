#!/usr/bin/env python3
"""
Check the latest certificate for extracted_ship_name field
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nautical-certs-1.preview.emergentagent.com') + '/api'

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
    print("🔍 Checking latest certificate...")
    
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
    
    # Find the latest certificate (by created_at)
    latest_cert = None
    latest_time = None
    
    for cert in certificates:
        created_at = cert.get('created_at')
        if created_at:
            if latest_time is None or created_at > latest_time:
                latest_time = created_at
                latest_cert = cert
    
    if not latest_cert:
        print("❌ No certificates found")
        return
    
    print("✅ Found latest certificate")
    print(f"Certificate ID: {latest_cert.get('id')}")
    print(f"Certificate Name: {latest_cert.get('cert_name')}")
    print(f"Certificate No: {latest_cert.get('cert_no')}")
    print(f"Created At: {latest_cert.get('created_at')}")
    
    # Check extracted_ship_name field
    extracted_ship_name = latest_cert.get('extracted_ship_name')
    print(f"\n🔍 EXTRACTED_SHIP_NAME FIELD CHECK:")
    print(f"   extracted_ship_name: {extracted_ship_name}")
    
    if extracted_ship_name:
        print("🎉 SUCCESS: extracted_ship_name field is populated!")
        print(f"   Value: {extracted_ship_name}")
        print("   The tooltip should now show the extracted ship name")
    else:
        print("❌ ISSUE: extracted_ship_name field is still missing")
    
    # Check if text_content is present
    text_content = latest_cert.get('text_content')
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
    
    # Show relevant certificate fields
    print(f"\n📋 RELEVANT CERTIFICATE FIELDS:")
    relevant_fields = ['id', 'cert_name', 'cert_no', 'ship_name', 'extracted_ship_name', 'text_content', 'created_at']
    for field in relevant_fields:
        value = latest_cert.get(field)
        if field == 'text_content' and value:
            print(f"   {field}: {len(value)} characters")
        else:
            print(f"   {field}: {value}")

if __name__ == "__main__":
    main()
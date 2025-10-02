#!/usr/bin/env python3
"""
Test AI Docking Extraction with PM242308 Certificate
This test specifically checks if the AI can extract "MAY 05, 2022" from the PM242308 CSSC certificate
"""

import requests
import json
import os
import sys
from datetime import datetime

# Configuration
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

def authenticate():
    """Authenticate and get token"""
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Authentication failed: {response.status_code}")
        return None

def get_headers(token):
    """Get authentication headers"""
    return {"Authorization": f"Bearer {token}"}

def test_pm242308_certificate():
    """Test the specific PM242308 certificate that should contain the MAY 05, 2022 date"""
    
    print("🔍 Testing PM242308 Certificate AI Extraction")
    print("=" * 60)
    
    # Authenticate
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful")
    
    # Get MINH ANH 09 ship ID
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=get_headers(token), timeout=30)
    if ships_response.status_code != 200:
        print("❌ Failed to get ships")
        return False
    
    ships = ships_response.json()
    minh_anh_ship = None
    for ship in ships:
        if 'MINH ANH' in ship.get('name', '').upper() and '09' in ship.get('name', ''):
            minh_anh_ship = ship
            break
    
    if not minh_anh_ship:
        print("❌ MINH ANH 09 ship not found")
        return False
    
    ship_id = minh_anh_ship['id']
    print(f"✅ Found MINH ANH 09: {ship_id}")
    
    # Get certificates for this ship
    certs_response = requests.get(f"{BACKEND_URL}/certificates?ship_id={ship_id}", headers=get_headers(token), timeout=30)
    if certs_response.status_code != 200:
        print("❌ Failed to get certificates")
        return False
    
    certificates = certs_response.json()
    pm242308_cert = None
    
    for cert in certificates:
        if cert.get('cert_no') == 'PM242308':
            pm242308_cert = cert
            break
    
    if not pm242308_cert:
        print("❌ PM242308 certificate not found")
        return False
    
    print(f"✅ Found PM242308 certificate: {pm242308_cert['id']}")
    
    # Check if certificate has text content
    text_content = pm242308_cert.get('text_content')
    if not text_content:
        print("❌ PM242308 certificate has no text content")
        return False
    
    print(f"✅ Certificate has text content ({len(text_content)} characters)")
    
    # Look for the specific phrase in the text content
    target_phrase = "last two inspections of the outside of the ship's bottom took place on"
    may_05_2022_phrase = "MAY 05, 2022"
    
    if target_phrase.lower() in text_content.lower():
        print(f"✅ Found target phrase: '{target_phrase}'")
        
        # Find the exact line containing this phrase
        lines = text_content.split('\n')
        for i, line in enumerate(lines):
            if target_phrase.lower() in line.lower():
                print(f"   Line {i+1}: {line.strip()}")
                
                if may_05_2022_phrase in line:
                    print(f"✅ Found expected date '{may_05_2022_phrase}' in the same line!")
                else:
                    print(f"⚠️ Expected date '{may_05_2022_phrase}' not found in this line")
    else:
        print(f"❌ Target phrase '{target_phrase}' not found in certificate text")
        
        # Search for variations
        variations = [
            "inspections of the outside of the ship's bottom",
            "inspection of the outside of the ship's bottom", 
            "outside of the ship's bottom",
            "bottom took place on",
            "MAY 05, 2022"
        ]
        
        print("\n🔍 Searching for phrase variations:")
        for variation in variations:
            if variation.lower() in text_content.lower():
                print(f"   ✅ Found: '{variation}'")
                # Show context
                lines = text_content.split('\n')
                for i, line in enumerate(lines):
                    if variation.lower() in line.lower():
                        print(f"      Line {i+1}: {line.strip()}")
            else:
                print(f"   ❌ Not found: '{variation}'")
    
    # Now test the actual API endpoint
    print(f"\n🔧 Testing calculate-docking-dates API endpoint...")
    
    docking_response = requests.post(f"{BACKEND_URL}/ships/{ship_id}/calculate-docking-dates", 
                                   headers=get_headers(token), timeout=60)
    
    print(f"   Response status: {docking_response.status_code}")
    
    if docking_response.status_code == 200:
        response_data = docking_response.json()
        print(f"   Response: {json.dumps(response_data, indent=4)}")
        
        success = response_data.get('success', False)
        docking_dates = response_data.get('docking_dates', {})
        
        if success and docking_dates:
            last_docking = docking_dates.get('last_docking')
            if last_docking == '05/05/2022':
                print("✅ SUCCESS: API correctly extracted MAY 05, 2022 as 05/05/2022!")
                return True
            else:
                print(f"⚠️ API extracted different date: {last_docking} (expected: 05/05/2022)")
        else:
            print(f"❌ API failed to extract docking dates: {response_data.get('message', 'Unknown error')}")
    else:
        print(f"❌ API call failed: {docking_response.status_code}")
        try:
            error_data = docking_response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Error: {docking_response.text}")
    
    return False

def main():
    """Main test function"""
    print("🧪 PM242308 CERTIFICATE AI EXTRACTION TEST")
    print("=" * 80)
    
    success = test_pm242308_certificate()
    
    if success:
        print("\n✅ TEST PASSED: AI successfully extracted MAY 05, 2022 from PM242308")
    else:
        print("\n❌ TEST FAILED: AI did not extract the expected date")
    
    return success

if __name__ == "__main__":
    main()
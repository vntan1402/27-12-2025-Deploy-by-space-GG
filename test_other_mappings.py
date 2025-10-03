#!/usr/bin/env python3
"""
Test other certificate mappings (LL, CL, ITC) across different ships
"""

import requests
import json

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
    else:
        raise Exception("Internal URL not working")
except:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break

def authenticate():
    """Authenticate with admin1/123456"""
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def get_headers(token):
    """Get authentication headers"""
    return {"Authorization": f"Bearer {token}"}

def test_other_mappings():
    """Test LL, CL, ITC mappings across all ships"""
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = get_headers(token)
    
    # Get all ships
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers, timeout=30)
    if ships_response.status_code != 200:
        print("❌ Failed to get ships")
        return
    
    ships = ships_response.json()
    print(f"🚢 Found {len(ships)} ships")
    
    # Expected mappings to look for
    target_mappings = {
        'INTERNATIONAL LOAD LINE CERTIFICATE': 'LL',
        'CLASSIFICATION CERTIFICATE': 'CL', 
        'INTERNATIONAL TONNAGE CERTIFICATE': 'ITC',
        'CERTIFICADO INTERNACIONAL DE ARQUEO': 'ITC'
    }
    
    mapping_usage_found = {}
    
    for ship in ships:
        ship_name = ship.get('name')
        ship_id = ship.get('id')
        
        print(f"\n🔍 Checking ship: {ship_name}")
        
        # Get certificates for this ship
        certs_response = requests.get(f"{BACKEND_URL}/ships/{ship_id}/certificates", headers=headers, timeout=30)
        if certs_response.status_code != 200:
            continue
            
        certificates = certs_response.json()
        print(f"   Found {len(certificates)} certificates")
        
        for cert in certificates:
            cert_name = cert.get('cert_name', '').upper()
            cert_abbreviation = cert.get('cert_abbreviation', '')
            
            # Check if this certificate matches any target mapping
            for target_name, expected_abbrev in target_mappings.items():
                if target_name.upper() in cert_name or any(word in cert_name for word in target_name.upper().split()):
                    print(f"      📋 Certificate: {cert_name}")
                    print(f"         Current Abbreviation: {cert_abbreviation}")
                    print(f"         Expected Mapping: {expected_abbrev}")
                    
                    if cert_abbreviation == expected_abbrev:
                        print(f"         ✅ Mapping used correctly: {expected_abbrev}")
                        mapping_usage_found[target_name] = True
                    else:
                        print(f"         ⚠️ Mapping not used or incorrect: {cert_abbreviation} vs {expected_abbrev}")
                    break
    
    print(f"\n📊 MAPPING USAGE SUMMARY:")
    for target_name, expected_abbrev in target_mappings.items():
        if target_name in mapping_usage_found:
            print(f"   ✅ {target_name} → {expected_abbrev} (USED)")
        else:
            print(f"   ❌ {target_name} → {expected_abbrev} (NOT FOUND)")
    
    print(f"\n🎯 TOTAL MAPPINGS VERIFIED: {len(mapping_usage_found)}/{len(target_mappings)}")

if __name__ == "__main__":
    test_other_mappings()
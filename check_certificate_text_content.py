#!/usr/bin/env python3
"""
Check Certificate Text Content
Check if existing certificates have text_content field for analysis
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://certflow-2.preview.emergentagent.com') + '/api'

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
    print("🔍 Checking Certificate Text Content...")
    
    # Authenticate
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Get ships
    response = requests.get(f"{BACKEND_URL}/ships", headers=get_headers(token), timeout=30)
    if response.status_code != 200:
        print("❌ Failed to get ships")
        return
    
    ships = response.json()
    print(f"Found {len(ships)} ships")
    
    # Check certificates for each ship
    for ship in ships:
        ship_name = ship.get('name', 'Unknown')
        ship_id = ship.get('id')
        
        print(f"\n🚢 Ship: {ship_name}")
        
        # Get certificates
        response = requests.get(f"{BACKEND_URL}/ships/{ship_id}/certificates", headers=get_headers(token), timeout=30)
        if response.status_code != 200:
            print(f"   ❌ Failed to get certificates")
            continue
        
        certificates = response.json()
        print(f"   Found {len(certificates)} certificates")
        
        # Check text content
        certificates_with_text = 0
        certificates_with_extracted_name = 0
        
        for cert in certificates:
            cert_name = cert.get('cert_name', 'Unknown')[:50]
            has_text_content = bool(cert.get('text_content'))
            has_extracted_name = bool(cert.get('extracted_ship_name'))
            
            if has_text_content:
                certificates_with_text += 1
                text_content = cert.get('text_content', '')
                print(f"   ✅ {cert_name}... - HAS TEXT CONTENT ({len(text_content)} chars)")
                
                # Check if text contains ship name
                if 'SUNSHINE' in text_content.upper():
                    print(f"      🎯 Contains 'SUNSHINE' in text content")
                    
            if has_extracted_name:
                certificates_with_extracted_name += 1
                extracted_name = cert.get('extracted_ship_name')
                print(f"   ✅ {cert_name}... - HAS EXTRACTED_SHIP_NAME: {extracted_name}")
        
        print(f"   📊 Summary: {certificates_with_text}/{len(certificates)} have text_content")
        print(f"   📊 Summary: {certificates_with_extracted_name}/{len(certificates)} have extracted_ship_name")

if __name__ == "__main__":
    main()
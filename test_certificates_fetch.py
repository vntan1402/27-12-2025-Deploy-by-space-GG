#!/usr/bin/env python3
"""
Test fetching certificates to debug the display issue
"""
import requests
import json

backend_url = 'http://localhost:8001'

# Login
login_data = {
    "username": "admin1",
    "password": "123456"
}

session = requests.Session()

print("🔐 Logging in...")
login_response = session.post(f"{backend_url}/api/auth/login", json=login_data)

if login_response.status_code == 200:
    login_result = login_response.json()
    token = login_result.get('access_token')
    session.headers.update({'Authorization': f'Bearer {token}'})
    print("✅ Login successful")
    
    # Get all certificates
    print("\n📋 Testing certificates fetch...")
    certs_response = session.get(f"{backend_url}/api/certificates")
    print(f"Certificates response status: {certs_response.status_code}")
    
    if certs_response.status_code == 200:
        certificates = certs_response.json()
        print(f"✅ Successfully fetched {len(certificates)} certificates")
        
        # Check a few certificates for next_survey field
        if certificates:
            print(f"\n📋 Sample certificate data:")
            for i, cert in enumerate(certificates[:3]):
                print(f"   Certificate {i+1}: {cert.get('cert_name', 'Unknown')}")
                print(f"      Ship ID: {cert.get('ship_id')}")
                print(f"      Next Survey: {cert.get('next_survey')}")
                print(f"      Next Survey Display: {cert.get('next_survey_display')}")
                print(f"      Next Survey Type: {cert.get('next_survey_type')}")
                print()
    else:
        try:
            error_data = certs_response.json()
            print(f"❌ Certificates fetch failed: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"❌ Certificates fetch failed: {certs_response.status_code} - {certs_response.text}")
    
    # Also test ship-specific certificates
    print("\n🚢 Testing ship-specific certificates...")
    ships_response = session.get(f"{backend_url}/api/ships")
    
    if ships_response.status_code == 200:
        ships = ships_response.json()
        if ships:
            test_ship = ships[0]
            ship_id = test_ship['id']
            ship_name = test_ship.get('name', 'Unknown')
            
            print(f"Testing certificates for ship: {ship_name}")
            ship_certs_response = session.get(f"{backend_url}/api/ships/{ship_id}/certificates")
            print(f"Ship certificates response status: {ship_certs_response.status_code}")
            
            if ship_certs_response.status_code == 200:
                ship_certificates = ship_certs_response.json()
                print(f"✅ Successfully fetched {len(ship_certificates)} certificates for ship")
                
                if ship_certificates:
                    print(f"\n📋 Sample ship certificate data:")
                    for cert in ship_certificates[:2]:
                        print(f"   - {cert.get('cert_name', 'Unknown')}")
                        print(f"     Next Survey: {cert.get('next_survey')}")
                        print(f"     Next Survey Display: {cert.get('next_survey_display')}")
                        print(f"     Next Survey Type: {cert.get('next_survey_type')}")
            else:
                try:
                    error_data = ship_certs_response.json()
                    print(f"❌ Ship certificates fetch failed: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"❌ Ship certificates fetch failed: {ship_certs_response.status_code} - {ship_certs_response.text}")
else:
    print(f"❌ Login failed: {login_response.text}")
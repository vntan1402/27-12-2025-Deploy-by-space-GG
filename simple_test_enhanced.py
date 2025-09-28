#!/usr/bin/env python3
"""
Simple test for enhanced survey logic
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
print(f"Login status: {login_response.status_code}")

if login_response.status_code == 200:
    login_result = login_response.json()
    token = login_result.get('access_token')
    session.headers.update({'Authorization': f'Bearer {token}'})
    print("✅ Login successful")
    
    # Test getting certificates first
    print("\n📋 Getting certificates...")
    certs_response = session.get(f"{backend_url}/api/certificates")
    print(f"Certificates status: {certs_response.status_code}")
    
    if certs_response.status_code == 200:
        certificates = certs_response.json()
        print(f"Found {len(certificates)} certificates")
        
        if certificates:
            # Test enhanced survey type on first certificate
            test_cert_id = certificates[0]['id']
            test_cert_name = certificates[0].get('cert_name', 'Unknown')
            print(f"\n🔍 Testing enhanced survey type on: {test_cert_name}")
            
            enhanced_response = session.post(f"{backend_url}/api/certificates/{test_cert_id}/determine-survey-type-enhanced")
            print(f"Enhanced survey type status: {enhanced_response.status_code}")
            
            if enhanced_response.status_code == 200:
                result = enhanced_response.json()
                print("✅ Enhanced survey type successful")
                print(json.dumps(result, indent=2))
            else:
                print(f"❌ Enhanced survey type failed: {enhanced_response.text}")
        else:
            print("❌ No certificates found")
    else:
        print(f"❌ Failed to get certificates: {certs_response.text}")
else:
    print(f"❌ Login failed: {login_response.text}")
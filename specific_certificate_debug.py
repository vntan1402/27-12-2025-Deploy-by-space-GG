#!/usr/bin/env python3
"""
Specific Certificate Debug - Check individual certificate abbreviation data
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
    """Check specific certificates that had issues"""
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = get_headers(token)
    
    # Certificate IDs from the test results
    problem_certificates = [
        "3d773205-9f70-4085-b2d5-60858bbdae35",  # LL cert that used full name
        "077344cb-e926-4520-a837-9dcf23c7f346",  # CL cert that used full name
        "41440429-2673-4c2d-afd2-f5c5c922f650",  # LL cert that correctly used 'LL'
    ]
    
    for cert_id in problem_certificates:
        print(f"\n🔍 Checking certificate: {cert_id}")
        
        # Get certificate details
        response = requests.get(f"{BACKEND_URL}/certificates/{cert_id}", headers=headers, timeout=30)
        
        if response.status_code == 200:
            cert = response.json()
            print(f"   Certificate Name: '{cert.get('cert_name', 'N/A')}'")
            print(f"   Certificate Abbreviation: '{cert.get('cert_abbreviation', 'N/A')}'")
            print(f"   Certificate Type: '{cert.get('cert_type', 'N/A')}'")
            print(f"   Ship ID: '{cert.get('ship_id', 'N/A')}'")
            print(f"   Google Drive File ID: '{cert.get('google_drive_file_id', 'N/A')}'")
            
            # Check if abbreviation is empty or None
            cert_abbreviation = cert.get('cert_abbreviation')
            if not cert_abbreviation or cert_abbreviation.strip() == '':
                print(f"   ❌ ISSUE: cert_abbreviation is empty or None")
            else:
                print(f"   ✅ cert_abbreviation is present: '{cert_abbreviation}'")
        else:
            print(f"   ❌ Failed to get certificate: {response.status_code}")

if __name__ == "__main__":
    check_specific_certificates()
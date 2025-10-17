#!/usr/bin/env python3
"""
Debug DOB Validation Test
Focused test to debug the DOB validation issue
"""

import requests
import json
import tempfile
from datetime import datetime

# Configuration
BACKEND_URL = 'https://shipmatrix.preview.emergentagent.com/api'

def authenticate():
    """Authenticate and return session"""
    session = requests.Session()
    
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        return session, data.get("user", {})
    return None, None

def create_test_certificate_with_dob(holder_name, dob):
    """Create test certificate with specific DOB"""
    certificate_content = f"""
CERTIFICATE OF COMPETENCY

This is to certify that {holder_name}
has been found competent to perform duties as specified.

Certificate Number: COC-TEST-{int(datetime.now().timestamp())}
Issued By: Test Maritime Authority
Issue Date: {datetime.now().strftime('%d/%m/%Y')}
Expiry Date: {datetime.now().strftime('%d/%m/%Y')}

Date of Birth: {dob}

This certificate is valid for all vessels.

Signed: Test Authority
Date: {datetime.now().strftime('%d/%m/%Y')}
"""
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write(certificate_content)
    temp_file.close()
    return temp_file.name

def test_dob_extraction_and_validation():
    """Test DOB extraction and validation step by step"""
    print("🔍 DEBUG: DOB Validation Test")
    print("=" * 50)
    
    # Authenticate
    session, user = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    print(f"✅ Authenticated as: {user.get('username')}")
    
    # Get crew with DOB
    crew_response = session.get(f"{BACKEND_URL}/crew")
    if crew_response.status_code != 200:
        print("❌ Failed to get crew list")
        return
    
    crew_list = crew_response.json()
    crew_with_dob = None
    
    for crew in crew_list:
        if crew.get("date_of_birth"):
            crew_with_dob = crew
            break
    
    if not crew_with_dob:
        print("❌ No crew with DOB found")
        return
    
    print(f"✅ Found crew with DOB: {crew_with_dob.get('full_name')}")
    print(f"   Crew DOB: {crew_with_dob.get('date_of_birth')}")
    
    # Get ships
    ships_response = session.get(f"{BACKEND_URL}/ships")
    if ships_response.status_code != 200:
        print("❌ Failed to get ships")
        return
    
    ships = ships_response.json()
    test_ship = None
    for ship in ships:
        if ship.get("name") in ["BROTHER 36", "MINH ANH 09"]:
            test_ship = ship
            break
    
    if not test_ship:
        print("❌ No test ship found")
        return
    
    print(f"✅ Found test ship: {test_ship.get('name')}")
    
    # Test 1: Certificate with MATCHING DOB
    print("\n🧪 TEST 1: Certificate with MATCHING DOB")
    crew_dob = crew_with_dob.get('date_of_birth', '')
    if 'T' in crew_dob:
        crew_dob_date = crew_dob.split('T')[0]  # Extract date part
        # Convert YYYY-MM-DD to DD/MM/YYYY for certificate
        parts = crew_dob_date.split('-')
        cert_dob_match = f"{parts[2]}/{parts[1]}/{parts[0]}"
    else:
        cert_dob_match = "19/02/1979"  # Fallback
    
    print(f"   Using DOB in certificate: {cert_dob_match}")
    
    cert_file = create_test_certificate_with_dob(
        crew_with_dob.get('full_name'), 
        cert_dob_match
    )
    
    try:
        with open(cert_file, "rb") as f:
            files = {"cert_file": ("test_cert.txt", f, "text/plain")}
            data = {
                "ship_id": test_ship.get("id"),
                "crew_id": crew_with_dob.get("id")
            }
            
            response = session.post(
                f"{BACKEND_URL}/crew-certificates/analyze-file",
                files=files,
                data=data,
                timeout=120
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ SUCCESS - Certificate analysis completed")
                print(f"   AI extracted DOB: {result.get('date_of_birth', 'NOT FOUND')}")
            else:
                print(f"   ❌ FAILED - {response.text}")
    
    finally:
        import os
        try:
            os.unlink(cert_file)
        except:
            pass
    
    # Test 2: Certificate with MISMATCHED DOB
    print("\n🧪 TEST 2: Certificate with MISMATCHED DOB")
    cert_dob_mismatch = "01/01/1990"  # Different DOB
    print(f"   Using DOB in certificate: {cert_dob_mismatch}")
    
    cert_file = create_test_certificate_with_dob(
        crew_with_dob.get('full_name'), 
        cert_dob_mismatch
    )
    
    try:
        with open(cert_file, "rb") as f:
            files = {"cert_file": ("test_cert.txt", f, "text/plain")}
            data = {
                "ship_id": test_ship.get("id"),
                "crew_id": crew_with_dob.get("id")
            }
            
            response = session.post(
                f"{BACKEND_URL}/crew-certificates/analyze-file",
                files=files,
                data=data,
                timeout=120
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 400:
                result = response.json()
                print("   ✅ SUCCESS - DOB mismatch detected correctly")
                print(f"   Error: {result.get('detail', {}).get('error', 'Unknown')}")
                print(f"   AI DOB: {result.get('detail', {}).get('ai_extracted_dob', 'Unknown')}")
                print(f"   Crew DOB: {result.get('detail', {}).get('crew_dob', 'Unknown')}")
            elif response.status_code == 200:
                result = response.json()
                print("   ❌ FAILED - Expected 400 but got 200")
                print(f"   AI extracted DOB: {result.get('date_of_birth', 'NOT FOUND')}")
                print("   This suggests DOB validation is not working")
            else:
                print(f"   ❌ UNEXPECTED - {response.text}")
    
    finally:
        import os
        try:
            os.unlink(cert_file)
        except:
            pass
    
    # Test 3: Certificate with BYPASS parameter
    print("\n🧪 TEST 3: Certificate with BYPASS parameter")
    cert_file = create_test_certificate_with_dob(
        crew_with_dob.get('full_name'), 
        cert_dob_mismatch
    )
    
    try:
        with open(cert_file, "rb") as f:
            files = {"cert_file": ("test_cert.txt", f, "text/plain")}
            data = {
                "ship_id": test_ship.get("id"),
                "crew_id": crew_with_dob.get("id"),
                "bypass_dob_validation": "true"
            }
            
            response = session.post(
                f"{BACKEND_URL}/crew-certificates/analyze-file",
                files=files,
                data=data,
                timeout=120
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ SUCCESS - Bypass parameter working")
                print(f"   AI extracted DOB: {result.get('date_of_birth', 'NOT FOUND')}")
            else:
                print(f"   ❌ FAILED - {response.text}")
    
    finally:
        import os
        try:
            os.unlink(cert_file)
        except:
            pass

if __name__ == "__main__":
    test_dob_extraction_and_validation()
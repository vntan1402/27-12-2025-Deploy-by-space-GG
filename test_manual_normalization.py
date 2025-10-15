#!/usr/bin/env python3
"""
Test normalization via manual endpoint to see if it works there
"""

import requests
import json
import os
import sys
from datetime import datetime

# Configuration - Use environment variable for backend URL
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
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

def authenticate():
    """Authenticate and return session"""
    session = requests.Session()
    
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        session.headers.update({
            "Authorization": f"Bearer {auth_token}"
        })
        print("✅ Authentication successful")
        return session
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def test_manual_normalization():
    """Test normalization via manual endpoint"""
    
    print("🔍 Testing normalization via manual endpoint...")
    
    session = authenticate()
    if not session:
        return False
    
    # Get ship ID
    ships_response = session.get(f"{BACKEND_URL}/ships")
    if ships_response.status_code != 200:
        print("❌ Failed to get ships")
        return False
    
    ships = ships_response.json()
    brother_36_ship = None
    for ship in ships:
        if ship.get("name") == "BROTHER 36":
            brother_36_ship = ship
            break
    
    if not brother_36_ship:
        print("❌ BROTHER 36 ship not found")
        return False
    
    ship_id = brother_36_ship.get("id")
    print(f"✅ Found BROTHER 36 ship: {ship_id}")
    
    # Test cases with unnormalized issued_by
    test_cases = [
        {
            "name": "Panama Test",
            "issued_by": "RERL Maritime Authority of the Republic of Panama",
            "expected": "Panama Maritime Authority"
        },
        {
            "name": "Vietnam Test", 
            "issued_by": "Socialist Republic of Vietnam Maritime Administration",
            "expected": "Vietnam Maritime Administration"
        },
        {
            "name": "Marshall Islands Test",
            "issued_by": "The Government of Marshall Islands",
            "expected": "Marshall Islands Maritime Administrator"
        }
    ]
    
    created_certificates = []
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📋 Test Case {i+1}: {test_case['name']}")
        print(f"   Input issued_by: '{test_case['issued_by']}'")
        print(f"   Expected: '{test_case['expected']}'")
        
        # Create certificate with unnormalized issued_by
        cert_data = {
            "crew_name": f"Test Crew {i+1}",
            "passport": f"TEST{i+1:03d}",
            "cert_name": f"Test Certificate {i+1}",
            "cert_no": f"TEST-{i+1:03d}",
            "issued_by": test_case["issued_by"],
            "issued_date": "2024-01-01T00:00:00Z",
            "cert_expiry": "2025-01-01T00:00:00Z",
            "status": "Valid",
            "note": f"Normalization test {i+1}"
        }
        
        # Create certificate
        endpoint = f"{BACKEND_URL}/crew-certificates/manual"
        params = {"ship_id": ship_id}
        
        response = session.post(endpoint, json=cert_data, params=params, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            cert_id = result.get("id")
            created_certificates.append(cert_id)
            
            print(f"   ✅ Certificate created: {cert_id}")
            
            # Get the certificate back to check normalization
            get_response = session.get(f"{BACKEND_URL}/crew-certificates/{ship_id}")
            
            if get_response.status_code == 200:
                certificates = get_response.json()
                
                # Find our certificate
                found_cert = None
                for cert in certificates:
                    if cert.get("id") == cert_id:
                        found_cert = cert
                        break
                
                if found_cert:
                    stored_issued_by = found_cert.get("issued_by", "")
                    print(f"   Stored issued_by: '{stored_issued_by}'")
                    
                    if stored_issued_by == test_case["expected"]:
                        print("   ✅ NORMALIZATION WORKING!")
                    elif stored_issued_by == test_case["issued_by"]:
                        print("   ❌ NO NORMALIZATION - value unchanged")
                    else:
                        print(f"   ⚠️ UNEXPECTED RESULT: '{stored_issued_by}'")
                else:
                    print("   ❌ Certificate not found in response")
            else:
                print(f"   ❌ Failed to retrieve certificates: {get_response.status_code}")
        else:
            print(f"   ❌ Failed to create certificate: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error text: {response.text}")
    
    # Clean up
    print(f"\n🧹 Cleaning up {len(created_certificates)} test certificates...")
    for cert_id in created_certificates:
        try:
            delete_response = session.delete(f"{BACKEND_URL}/crew-certificates/{cert_id}")
            if delete_response.status_code == 200:
                print(f"   ✅ Deleted: {cert_id}")
            else:
                print(f"   ⚠️ Failed to delete: {cert_id}")
        except Exception as e:
            print(f"   ⚠️ Error deleting {cert_id}: {e}")
    
    return True

if __name__ == "__main__":
    test_manual_normalization()
#!/usr/bin/env python3
"""
Simple test script to debug the upcoming surveys endpoint issue
"""

import requests
import json
from datetime import datetime

# Backend URL
BACKEND_URL = "https://cert-tracker-8.preview.emergentagent.com/api"

def test_upcoming_surveys():
    """Test the upcoming surveys endpoint with detailed logging"""
    
    # Step 1: Login
    print("🔐 Step 1: Authenticating...")
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    session = requests.Session()
    response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return
    
    auth_data = response.json()
    access_token = auth_data["access_token"]
    user_data = auth_data["user"]
    
    print(f"✅ Login successful")
    print(f"👤 User: {user_data['username']}")
    print(f"🏢 Company: {user_data['company']}")
    
    # Step 2: Get upcoming surveys
    print(f"\n📡 Step 2: Getting upcoming surveys...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = session.get(f"{BACKEND_URL}/certificates/upcoming-surveys", headers=headers)
    
    print(f"📊 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📄 Response structure: {json.dumps(data, indent=2, default=str)}")
        
        upcoming_surveys = data.get("upcoming_surveys", [])
        print(f"\n📋 Found {len(upcoming_surveys)} upcoming surveys")
        
        # Look for the specific certificate
        target_cert_id = "51d1c55a-81d4-4e68-9dd2-9fef7d8bf895"
        print(f"\n🔍 Looking for certificate: {target_cert_id}")
        
        found = False
        for survey in upcoming_surveys:
            cert_id = survey.get('certificate_id', '')
            if cert_id == target_cert_id:
                print(f"✅ FOUND TARGET CERTIFICATE!")
                print(f"   📋 Details: {json.dumps(survey, indent=4, default=str)}")
                found = True
                break
            else:
                print(f"   📋 Other cert: {cert_id} - {survey.get('cert_name', '')}")
        
        if not found:
            print(f"❌ Target certificate {target_cert_id} NOT FOUND")
            
        # Step 3: Check all certificates for this company
        print(f"\n📡 Step 3: Getting all ships and certificates...")
        
        # Get ships
        ships_response = session.get(f"{BACKEND_URL}/ships", headers=headers)
        if ships_response.status_code == 200:
            ships = ships_response.json()
            print(f"🚢 Found {len(ships)} ships")
            
            for ship in ships:
                ship_id = ship.get('id')
                ship_name = ship.get('name')
                print(f"   🚢 Ship: {ship_name} (ID: {ship_id})")
                
                # Get certificates for this ship
                certs_response = session.get(f"{BACKEND_URL}/ships/{ship_id}/certificates", headers=headers)
                if certs_response.status_code == 200:
                    certificates = certs_response.json()
                    print(f"      📋 Found {len(certificates)} certificates")
                    
                    for cert in certificates:
                        cert_id = cert.get('id')
                        cert_name = cert.get('cert_name', '')
                        next_survey = cert.get('next_survey', '')
                        next_survey_type = cert.get('next_survey_type', '')
                        
                        print(f"         📄 Cert: {cert_id}")
                        print(f"            Name: {cert_name}")
                        print(f"            Next Survey: {next_survey}")
                        print(f"            Survey Type: {next_survey_type}")
                        
                        if cert_id == target_cert_id:
                            print(f"         ✅ FOUND TARGET CERTIFICATE IN SHIP {ship_name}!")
                            print(f"            Full details: {json.dumps(cert, indent=12, default=str)}")
                else:
                    print(f"      ❌ Failed to get certificates: {certs_response.status_code}")
        else:
            print(f"❌ Failed to get ships: {ships_response.status_code}")
            
    else:
        print(f"❌ Failed to get upcoming surveys: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_upcoming_surveys()
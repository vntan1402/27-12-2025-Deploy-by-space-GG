#!/usr/bin/env python3
"""
Test Crew Certificate Upload Flow
"""

import requests
import json
import base64

# Backend URL
BACKEND_URL = "http://0.0.0.0:8001/api"

# Test credentials
USERNAME = "admin1"
PASSWORD = "123456"

def test_cert_upload():
    print("=" * 80)
    print("TESTING CREW CERTIFICATE UPLOAD FLOW")
    print("=" * 80)
    
    # Step 1: Login
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BACKEND_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Step 2: Get ships
    print("\n2. Getting ships...")
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers)
    ships = ships_response.json()
    
    if not ships:
        print("❌ No ships found")
        return
    
    ship = ships[0]
    ship_id = ship["id"]
    ship_name = ship["name"]
    print(f"✅ Using ship: {ship_name} ({ship_id})")
    
    # Step 3: Get crew members
    print("\n3. Getting crew members...")
    crew_response = requests.get(
        f"{BACKEND_URL}/crew?ship_name={ship_name}",
        headers=headers
    )
    crew_list = crew_response.json()
    
    if not crew_list:
        print("❌ No crew members found")
        return
    
    crew = crew_list[0]
    crew_id = crew["id"]
    crew_name = crew["full_name"]
    print(f"✅ Using crew: {crew_name} ({crew_id})")
    
    # Step 4: Check if analyze endpoint returns _file_content
    print("\n4. Testing analyze endpoint...")
    
    # Create dummy PDF file
    dummy_pdf = b"%PDF-1.4\nDummy certificate content"
    
    files = {
        'cert_file': ('test_cert.pdf', dummy_pdf, 'application/pdf')
    }
    data = {
        'ship_id': ship_id,
        'crew_id': crew_id
    }
    
    analyze_response = requests.post(
        f"{BACKEND_URL}/crew-certificates/analyze-file",
        files=files,
        data=data,
        headers=headers
    )
    
    print(f"   Status: {analyze_response.status_code}")
    
    if analyze_response.status_code == 200:
        analyze_data = analyze_response.json()
        print(f"   Success: {analyze_data.get('success')}")
        
        analysis = analyze_data.get('analysis', {})
        print(f"\n   Analysis keys: {list(analysis.keys())}")
        
        # Check for underscore-prefixed fields
        has_file_content = '_file_content' in analysis
        has_filename = '_filename' in analysis
        has_content_type = '_content_type' in analysis
        has_summary = '_summary_text' in analysis
        
        print(f"\n   ✅ Has _file_content: {has_file_content}")
        print(f"   ✅ Has _filename: {has_filename}")
        print(f"   ✅ Has _content_type: {has_content_type}")
        print(f"   ✅ Has _summary_text: {has_summary}")
        
        if has_file_content:
            print(f"\n   📦 File content length: {len(analysis['_file_content'])} chars")
        else:
            print("\n   ❌ PROBLEM: _file_content is missing!")
            print(f"   Response: {json.dumps(analyze_data, indent=2)[:500]}")
    else:
        print(f"   ❌ Analyze failed: {analyze_response.text}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_cert_upload()

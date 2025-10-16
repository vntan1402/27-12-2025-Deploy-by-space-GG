#!/usr/bin/env python3
"""
Test certificate AI extraction with the actual COC file
"""

import requests
import json
import os

BACKEND_URL = 'https://crew-doc-manager.preview.emergentagent.com/api'

def test_certificate_extraction():
    print("🧪 Testing Certificate AI Extraction")
    print("=" * 60)
    
    # Login
    print("1️⃣ Logging in...")
    login_response = requests.post(f'{BACKEND_URL}/auth/login', 
                                  json={'username': 'admin1', 'password': '123456'})
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json()['access_token']
    user = login_response.json()['user']
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"✅ Logged in as {user.get('username')} ({user.get('role')})")
    print()
    
    # Get ships
    print("2️⃣ Getting ships...")
    ships_response = requests.get(f'{BACKEND_URL}/ships', headers=headers)
    if ships_response.status_code != 200:
        print(f"❌ Failed to get ships: {ships_response.status_code}")
        return False
    
    ships = ships_response.json()
    brother_36 = next((s for s in ships if s['name'] == 'BROTHER 36'), None)
    
    if not brother_36:
        print("❌ BROTHER 36 ship not found")
        return False
    
    print(f"✅ Found ship: {brother_36['name']} (ID: {brother_36['id']})")
    print()
    
    # Get crew member HO SY CHUONG
    print("3️⃣ Getting crew member HO SY CHUONG...")
    crew_response = requests.get(f'{BACKEND_URL}/crew?ship_name=BROTHER 36', headers=headers)
    if crew_response.status_code != 200:
        print(f"❌ Failed to get crew: {crew_response.status_code}")
        return False
    
    crew_list = crew_response.json()
    ho_sy_chuong = next((c for c in crew_list if 'CHUONG' in c.get('full_name', '').upper()), None)
    
    if not ho_sy_chuong:
        print("❌ HO SY CHUONG not found in crew list")
        return False
    
    print(f"✅ Found crew: {ho_sy_chuong['full_name']} (Passport: {ho_sy_chuong['passport']})")
    print()
    
    # Upload certificate file for analysis
    print("4️⃣ Uploading COC certificate for AI analysis...")
    file_path = '/app/test_coc_certificate.pdf'
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'rb') as f:
        files = {'cert_file': ('1. CAPT CHUONG - PNM COC.pdf', f, 'application/pdf')}
        data = {
            'ship_id': brother_36['id'],
            'crew_id': ho_sy_chuong['id']
        }
        
        print(f"📤 Sending request to /crew-certificates/analyze-file...")
        print(f"   Ship ID: {brother_36['id']}")
        print(f"   Crew ID: {ho_sy_chuong['id']}")
        print()
        
        response = requests.post(
            f'{BACKEND_URL}/crew-certificates/analyze-file',
            files=files,
            data=data,
            headers=headers,
            timeout=120
        )
    
    print(f"📊 Response Status: {response.status_code}")
    print()
    
    if response.status_code != 200:
        print(f"❌ Analysis failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Parse response
    result = response.json()
    
    print("=" * 60)
    print("📋 AI EXTRACTION RESULTS")
    print("=" * 60)
    
    if result.get('success'):
        print("✅ Analysis successful!")
        print()
        
        # Show crew info
        print("👤 Crew Information:")
        print(f"   Crew Name: {result.get('crew_name', 'N/A')}")
        print(f"   Passport: {result.get('passport', 'N/A')}")
        print()
        
        # Show certificate analysis
        analysis = result.get('analysis', {})
        print("📜 Certificate Details (AI Extracted):")
        print(f"   Cert Name: {analysis.get('cert_name', 'N/A')}")
        print(f"   Cert No: {analysis.get('cert_no', 'N/A')}")
        print(f"   Issued By: {analysis.get('issued_by', 'N/A')}")
        print(f"   Issued Date: {analysis.get('issued_date', 'N/A')}")
        print(f"   Expiry Date: {analysis.get('expiry_date', 'N/A')}")
        print(f"   Note: {analysis.get('note', 'N/A')}")
        print(f"   Confidence: {analysis.get('confidence_score', 0.0)}")
        print(f"   Processing: {analysis.get('processing_method', 'N/A')}")
        print()
        
        # Compare with expected values
        print("=" * 60)
        print("🔍 COMPARISON WITH EXPECTED VALUES")
        print("=" * 60)
        
        expected = {
            'cert_name': 'Certificate of Competency (COC) - Endorsement',
            'cert_no': 'CT-585639/24-HCV',
            'issued_by': 'Panama Maritime Authority',
            'issued_date': '15/01/2025',
            'expiry_date': '27/02/2028',
            'note': 'Original COC from Vietnam, MASTER-II/2, MANAGEMENT level'
        }
        
        for field, expected_val in expected.items():
            actual_val = analysis.get(field, 'N/A')
            match = '✅' if str(actual_val).strip() == str(expected_val).strip() else '❌'
            print(f"{match} {field}:")
            print(f"   Expected: {expected_val}")
            print(f"   Actual:   {actual_val}")
            print()
        
    else:
        print("❌ Analysis failed")
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_certificate_extraction()

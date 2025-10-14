#!/usr/bin/env python3
"""
Detailed Extraction Test - Analyze the actual extraction results
"""

import requests
import json
import os

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipmate-certs.preview.emergentagent.com') + '/api'
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

def authenticate():
    """Authenticate and get token"""
    session = requests.Session()
    response = session.post(f"{BACKEND_URL}/auth/login", json={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        session.headers.update({'Authorization': f'Bearer {token}'})
        return session
    return None

def test_passport_extraction():
    """Test passport extraction and analyze results"""
    session = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    passport_file = "/app/3_2O_THUONG_PP.pdf"
    
    with open(passport_file, 'rb') as f:
        files = {
            'passport_file': ('3_2O_THUONG_PP.pdf', f, 'application/pdf')
        }
        data = {
            'ship_name': 'BROTHER 36'
        }
        
        print(f"🔍 Testing passport extraction with {passport_file}")
        response = session.post(
            f"{BACKEND_URL}/crew/analyze-passport",
            files=files,
            data=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Response received successfully")
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
            
            # Analyze extracted data
            analysis = result.get('analysis', {})
            print(f"\n📊 EXTRACTED DATA ANALYSIS:")
            print(f"Total fields: {len(analysis)}")
            
            for field, value in analysis.items():
                print(f"   {field}: '{value}'")
            
            # Check specific issues
            print(f"\n🎯 SPECIFIC ISSUE ANALYSIS:")
            
            # Full name check
            full_name = analysis.get('full_name', '')
            print(f"Full Name: '{full_name}'")
            print(f"   - Contains agency name (XUẤT NHẬP CẢNH): {'XUẤT NHẬP CẢNH' in full_name}")
            print(f"   - Is Vietnamese name: {len(full_name) > 5 and not 'XUẤT NHẬP CẢNH' in full_name}")
            
            # Place of birth check
            place_of_birth = analysis.get('place_of_birth', '')
            print(f"Place of Birth: '{place_of_birth}'")
            print(f"   - Has 'is' prefix: {place_of_birth.startswith('is ')}")
            print(f"   - Clean place name: {place_of_birth.replace('is ', '') if place_of_birth.startswith('is ') else place_of_birth}")
            
            # Date format check
            date_of_birth = analysis.get('date_of_birth', '')
            date_pattern = r'^\d{2}/\d{2}/\d{4}$'
            print(f"Date of Birth: '{date_of_birth}'")
            print(f"   - DD/MM/YYYY format: {bool(re.match(date_pattern, str(date_of_birth)))}")
            
            # Processing method
            processing_method = result.get('processing_method', '')
            print(f"\nProcessing Method: {processing_method}")
            
            # Summary check
            summary = result.get('summary', '')
            print(f"Summary Length: {len(summary)} characters")
            if len(summary) > 0:
                print(f"Summary Preview: {summary[:200]}...")
            
            # Files check
            files_data = result.get('files', {})
            print(f"\nFiles Data: {len(files_data)} entries")
            for file_type, file_info in files_data.items():
                print(f"   {file_type}: {file_info}")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")

if __name__ == "__main__":
    import re
    test_passport_extraction()
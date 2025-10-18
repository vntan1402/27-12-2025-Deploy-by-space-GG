#!/usr/bin/env python3
"""
Enhanced Passport Testing with Real Image File
"""

import requests
import json
import os
import sys
from datetime import datetime
import traceback

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://crewcert-manager.preview.emergentagent.com') + '/api'
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

def test_with_real_passport():
    """Test with a real passport file if available"""
    
    # Check if we have a real passport file in the system
    passport_files = [
        '/app/Ho_chieu_pho_thong.jpg',
        '/app/PASS PORT Tran Trong Toan.pdf',
        '/app/passport_sample.jpg',
        '/app/passport_sample.pdf'
    ]
    
    passport_file = None
    for file_path in passport_files:
        if os.path.exists(file_path):
            passport_file = file_path
            break
    
    if not passport_file:
        print("❌ No real passport file found for testing")
        return False
    
    print(f"✅ Found passport file: {passport_file}")
    
    # Authenticate
    session = requests.Session()
    login_data = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
    
    try:
        response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
        
        token = response.json().get('access_token')
        print("✅ Authentication successful")
        
        # Get ships
        response = session.get(f"{BACKEND_URL}/ships", headers={'Authorization': f'Bearer {token}'})
        if response.status_code != 200:
            print(f"❌ Failed to get ships: {response.status_code}")
            return False
        
        ships = response.json()
        if not ships:
            print("❌ No ships found")
            return False
        
        selected_ship = ships[0]
        print(f"✅ Selected ship: {selected_ship.get('name')}")
        
        # Test passport analysis
        with open(passport_file, 'rb') as f:
            files = {'passport_file': (os.path.basename(passport_file), f, 'image/jpeg' if passport_file.endswith('.jpg') else 'application/pdf')}
            data = {'ship_name': selected_ship.get('name')}
            headers = {'Authorization': f'Bearer {token}'}
            
            print("🔄 Testing passport analysis...")
            response = requests.post(
                f"{BACKEND_URL}/crew/analyze-passport", 
                files=files, 
                data=data, 
                headers=headers,
                timeout=120
            )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API Response received")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message', 'No message')}")
            
            if result.get('success'):
                # Check analysis data
                analysis = result.get('analysis', {})
                if analysis:
                    print("📋 Extracted Fields:")
                    for key, value in analysis.items():
                        if value and str(value).strip():
                            print(f"   {key}: {value}")
                
                # Check file uploads
                files_data = result.get('files', {})
                if files_data:
                    print("📁 File Upload Results:")
                    for file_type, file_info in files_data.items():
                        print(f"   {file_type}: {file_info.get('file_id', 'No ID')} -> {file_info.get('folder_path', 'No path')}")
                else:
                    print("⚠️  No file upload data in response")
                
                return True
            else:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 ENHANCED PASSPORT TESTING WITH REAL FILES")
    print("=" * 60)
    success = test_with_real_passport()
    print("=" * 60)
    if success:
        print("✅ Test completed successfully")
    else:
        print("❌ Test failed")
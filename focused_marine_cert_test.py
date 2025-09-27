#!/usr/bin/env python3
"""
Focused Marine Certificate Classification Test
Testing the specific issues identified in the review request
"""

import requests
import json
import os
import tempfile
import time
from datetime import datetime

BACKEND_URL = 'http://localhost:8001/api'

def authenticate():
    """Authenticate and get token"""
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def get_test_ship():
    """Get an existing test ship or create one"""
    token = authenticate()
    if not token:
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to get existing ships
    response = requests.get(f"{BACKEND_URL}/ships", headers=headers, timeout=30)
    if response.status_code == 200:
        ships = response.json()
        if ships:
            return ships[0]['id'], token
    
    # Create a new ship
    ship_data = {
        'name': 'FOCUSED TEST SHIP',
        'imo': '9999997',
        'flag': 'PANAMA',
        'ship_type': 'PMDS',
        'gross_tonnage': 5000.0,
        'built_year': 2015,
        'ship_owner': 'Test Owner',
        'company': 'AMCSC'
    }
    
    response = requests.post(f"{BACKEND_URL}/ships", json=ship_data, headers=headers, timeout=30)
    if response.status_code in [200, 201]:
        ship_id = response.json().get('id')
        return ship_id, token
    
    return None, token

def create_simple_marine_certificate():
    """Create a simple marine certificate content"""
    content = """CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE

Certificate No: CSSC-2024-TEST-001
IMO Number: 9999997
Ship Name: FOCUSED TEST SHIP
Flag State: PANAMA
Classification Society: PMDS
Issue Date: 15/01/2024
Valid Until: 15/01/2029
Issued by: Panama Maritime Authority

This certificate is issued under the provisions of SOLAS 1974
and certifies that the ship has been surveyed and complies
with the applicable requirements of the Convention.

The ship is authorized to carry cargo in accordance with
the provisions of the International Load Line Convention 1966.

Survey Status:
- Annual Survey: 15/01/2024
- Intermediate Survey: Due 15/07/2024
- Special Survey: Due 15/01/2029

Inspections of the outside of the ship's bottom:
- Last inspection: 15/01/2024
- Next inspection due: 15/01/2026

This certificate is valid until 15/01/2029 subject to
annual and intermediate surveys being carried out.

Issued at: Panama City
Date: 15/01/2024
Authority: Panama Maritime Authority
"""
    return content.encode('utf-8')

def test_analyze_certificate():
    """Test the analyze-ship-certificate endpoint"""
    print("🔍 Testing analyze-ship-certificate endpoint...")
    
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test certificate content
    cert_content = create_simple_marine_certificate()
    
    # Test with text file first (should work)
    files = {
        'file': ('marine_certificate.txt', cert_content, 'text/plain')
    }
    
    response = requests.post(
        f"{BACKEND_URL}/analyze-ship-certificate",
        files=files,
        headers=headers,
        timeout=60
    )
    
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Analyze endpoint working")
        print(f"   Analysis result: {json.dumps(data, indent=2)}")
        
        # Check if it's classified as marine certificate
        analysis = data.get('analysis', {})
        category = analysis.get('category', '')
        
        if category:
            print(f"   Category: {category}")
            if category.lower() == 'certificates':
                print("✅ Correctly classified as marine certificate")
                return True
            else:
                print(f"❌ Incorrectly classified as: {category}")
        else:
            print("❌ No category classification found")
        
        return False
    else:
        print(f"❌ Analyze endpoint failed: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error}")
        except:
            print(f"   Error: {response.text[:500]}")
        return False

def test_multi_upload():
    """Test the multi-upload endpoint"""
    print("📤 Testing multi-upload endpoint...")
    
    ship_id, token = get_test_ship()
    if not ship_id or not token:
        print("❌ Could not get test ship or authenticate")
        return False
    
    print(f"   Using ship ID: {ship_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test certificate content
    cert_content = create_simple_marine_certificate()
    
    # Test multi-upload
    files = {
        'files': ('marine_certificate_multi.txt', cert_content, 'text/plain')
    }
    
    params = {'ship_id': ship_id}
    
    response = requests.post(
        f"{BACKEND_URL}/certificates/multi-upload",
        files=files,
        params=params,
        headers=headers,
        timeout=120
    )
    
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Multi-upload endpoint accessible")
        print(f"   Result: {json.dumps(data, indent=2)}")
        
        # Check for errors
        results = data.get('results', [])
        for result in results:
            status = result.get('status', '')
            message = result.get('message', '')
            filename = result.get('filename', '')
            
            print(f"   File: {filename}")
            print(f"   Status: {status}")
            print(f"   Message: {message}")
            
            if 'not a marine certificate' in message.lower():
                print("❌ 'Not a marine certificate' error still present")
                return False
            elif 'unknown error' in message.lower():
                print("❌ 'Unknown error' still present")
                return False
            elif status.lower() == 'success':
                print("✅ Upload successful")
                return True
            else:
                print(f"⚠️ Status: {status}")
        
        return len(results) > 0
    else:
        print(f"❌ Multi-upload failed: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error}")
        except:
            print(f"   Error: {response.text[:500]}")
        return False

def test_ai_config():
    """Test AI configuration"""
    print("🤖 Testing AI configuration...")
    
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BACKEND_URL}/ai-config", headers=headers, timeout=30)
    
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ AI config accessible")
        print(f"   Config: {json.dumps(data, indent=2)}")
        
        provider = data.get('provider', '')
        model = data.get('model', '')
        use_emergent_key = data.get('use_emergent_key', False)
        
        if provider and model:
            print(f"✅ AI configured: {provider} {model}")
            if use_emergent_key:
                print("✅ Using Emergent key")
            return True
        else:
            print("❌ AI not properly configured")
            return False
    else:
        print(f"❌ AI config failed: {response.status_code}")
        return False

def main():
    print("🎯 FOCUSED MARINE CERTIFICATE CLASSIFICATION TEST")
    print("=" * 60)
    
    # Test 1: AI Configuration
    ai_working = test_ai_config()
    print()
    
    # Test 2: Analyze Certificate
    analyze_working = test_analyze_certificate()
    print()
    
    # Test 3: Multi-upload
    multi_upload_working = test_multi_upload()
    print()
    
    # Summary
    print("📊 SUMMARY:")
    print(f"   AI Configuration: {'✅' if ai_working else '❌'}")
    print(f"   Certificate Analysis: {'✅' if analyze_working else '❌'}")
    print(f"   Multi-upload: {'✅' if multi_upload_working else '❌'}")
    
    if ai_working and analyze_working and multi_upload_working:
        print("\n🎉 ALL TESTS PASSED - Marine certificate classification is working!")
    else:
        print("\n❌ SOME TESTS FAILED - Issues remain with marine certificate classification")
        
        if not ai_working:
            print("   - AI configuration needs attention")
        if not analyze_working:
            print("   - Certificate analysis/classification needs fixing")
        if not multi_upload_working:
            print("   - Multi-upload endpoint has issues")

if __name__ == "__main__":
    main()
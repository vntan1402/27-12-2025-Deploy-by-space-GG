#!/usr/bin/env python3
"""
Test script to verify the AI extraction confidence fix
"""
import requests
import json
import sys
import os

API_URL = "https://shipmate-55.preview.emergentagent.com"

def login():
    """Login and get auth token"""
    login_data = {
        "username": "admin1", 
        "password": "123456"
    }
    
    response = requests.post(f"{API_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def get_ships(token):
    """Get list of ships"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/api/ships", headers=headers)
    
    if response.status_code == 200:
        ships = response.json()
        print(f"✅ Found {len(ships)} ships")
        return ships
    else:
        print(f"❌ Failed to get ships: {response.status_code}")
        return []

def test_multi_cert_upload(token, ship_id):
    """Test multi certificate upload with the PDF file"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Download the PDF file from the uploaded artifact
    pdf_url = "https://customer-assets.emergentagent.com/job_shipmate-55/artifacts/21a6dco6_BROTHER%2036%20-%20IEEC-%20PM242758.pdf"
    pdf_response = requests.get(pdf_url)
    
    if pdf_response.status_code != 200:
        print(f"❌ Failed to download PDF: {pdf_response.status_code}")
        return False
    
    print(f"✅ Downloaded PDF: {len(pdf_response.content)} bytes")
    
    # Prepare form data
    files = {
        'files': ('BROTHER 36 - IEEC- PM242758.pdf', pdf_response.content, 'application/pdf')
    }
    
    data = {
        'category': 'Class & Flag Cert',
        'subcategory': 'Certificates'
    }
    
    print(f"\n🧪 Testing multi certificate upload with AI extraction fix...")
    
    # Make multi upload request
    url = f"{API_URL}/api/certificates/multi-upload?ship_id={ship_id}"
    response = requests.post(url, headers=headers, files=files, data=data, timeout=120)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Multi certificate upload completed")
        print(f"Results: {json.dumps(result, indent=2)}")
        
        # Check if AI extraction was successful
        if "results" in result and len(result["results"]) > 0:
            first_result = result["results"][0]
            
            if first_result.get("status") == "success":
                print("🎉 SUCCESS: AI extraction worked correctly!")
                print(f"   Certificate created with ID: {first_result.get('certificate_id')}")
                return True
            elif first_result.get("status") == "ai_extraction_failed":
                print("❌ STILL FAILING: AI extraction still requires manual input")
                print(f"   Reason: {first_result.get('reason', 'Unknown')}")
                return False
            else:
                print(f"⚠️ Unexpected status: {first_result.get('status')}")
                return False
        else:
            print("❌ No results in response")
            return False
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    print("🧪 Testing AI Extraction Confidence Fix")
    print("=" * 50)
    
    # Login
    token = login()
    if not token:
        sys.exit(1)
    
    # Get ships
    ships = get_ships(token)
    if not ships:
        print("❌ No ships found for testing")
        sys.exit(1)
    
    # Use first ship for testing
    test_ship = ships[0]
    ship_id = test_ship.get('id')
    ship_name = test_ship.get('name')
    
    print(f"\n📋 Testing with ship: {ship_name} (ID: {ship_id})")
    
    # Test multi certificate upload
    success = test_multi_cert_upload(token, ship_id)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ SUCCESS: AI extraction confidence fix is working!")
        print("   - The certificate was processed automatically")
        print("   - No manual input required")
    else:
        print("❌ ISSUE: AI extraction still failing")
        print("   - Certificate still requires manual input")
        print("   - Additional investigation needed")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test Google Drive folder deletion with non-existent ship
"""

import requests
import json

# Backend URL from frontend .env
BACKEND_URL = "https://ship-cert-sync.preview.emergentagent.com/api"

def test_nonexistent_ship():
    """Test deletion with non-existent ship name"""
    
    # Login first
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    session = requests.Session()
    response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    auth_data = response.json()
    access_token = auth_data["access_token"]
    company_id = auth_data["user"]["company"]
    
    print(f"✅ Login successful")
    print(f"🏢 Company ID: {company_id}")
    
    # Test with non-existent ship
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "ship_name": "NONEXISTENT_SHIP_TEST_12345"
    }
    
    print(f"\n🔍 Testing with non-existent ship: {payload['ship_name']}")
    
    response = session.post(
        f"{BACKEND_URL}/companies/{company_id}/gdrive/delete-ship-folder",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"📊 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        response_data = response.json()
        print(f"📄 Response: {json.dumps(response_data, indent=2)}")
        
        if response_data.get("success"):
            if "not found" in response_data.get("message", "").lower():
                print(f"✅ Non-existent ship handled gracefully with success=true and 'not found' message")
            else:
                print(f"✅ Non-existent ship handled with success=true")
        else:
            print(f"⚠️ Non-existent ship returned success=false")
    else:
        try:
            error_data = response.json()
            print(f"📄 Error Response: {json.dumps(error_data, indent=2)}")
        except:
            print(f"📄 Error Response (raw): {response.text}")

if __name__ == "__main__":
    test_nonexistent_ship()
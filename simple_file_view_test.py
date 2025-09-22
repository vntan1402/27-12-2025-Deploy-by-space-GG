#!/usr/bin/env python3
"""
Simple File View Test - Test the fixed endpoint
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "https://continue-session.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"
TEST_FILE_ID = "1GxhDHWH0GucMCB2ZAkf9hz55zICbTbki"

def test_file_view():
    print("🚀 Testing File View Fix")
    print("=" * 50)
    
    # Wait for backend to be ready
    print("⏳ Waiting for backend to be ready...")
    for i in range(10):
        try:
            response = requests.get(f"{API_BASE}/", timeout=5)
            if response.status_code != 502:
                print(f"✅ Backend is ready (status: {response.status_code})")
                break
        except:
            pass
        print(f"   Attempt {i+1}/10...")
        time.sleep(3)
    else:
        print("❌ Backend not ready after 30 seconds")
        return False
    
    # Authenticate
    print("\n🔐 Authenticating...")
    try:
        auth_response = requests.post(f"{API_BASE}/auth/login", json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }, timeout=10)
        
        if auth_response.status_code == 200:
            token = auth_response.json()["access_token"]
            print(f"✅ Authenticated successfully")
        else:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Test file view endpoint
    print(f"\n📁 Testing file view endpoint with file ID: {TEST_FILE_ID}")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        view_response = requests.get(
            f"{API_BASE}/gdrive/file/{TEST_FILE_ID}/view", 
            headers=headers,
            timeout=30
        )
        
        print(f"📡 Response Status: {view_response.status_code}")
        print(f"📄 Response Content: {view_response.text}")
        
        if view_response.status_code == 200:
            data = view_response.json()
            if data.get('success') and data.get('view_url'):
                print(f"✅ SUCCESS: File view URL retrieved: {data['view_url']}")
                return True
            else:
                print(f"❌ FAILED: Invalid response structure")
                return False
        else:
            print(f"❌ FAILED: HTTP {view_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ File view test error: {e}")
        return False

if __name__ == "__main__":
    success = test_file_view()
    if success:
        print("\n🎉 FILE VIEW FIX SUCCESSFUL!")
    else:
        print("\n💥 FILE VIEW FIX FAILED!")
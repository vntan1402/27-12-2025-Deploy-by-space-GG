#!/usr/bin/env python3
"""
Test script to trigger the Standby Crew folder detection logic
and view the enhanced logging output.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')

# Get backend URL
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')

def test_standby_folder_detection():
    """Test the Standby Crew folder detection with enhanced logging"""
    
    print("=" * 80)
    print("Testing Standby Crew Folder Detection")
    print("=" * 80)
    
    # First, login to get a token
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={
            "email": "admin@example.com",
            "password": "admin123"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    token = login_response.json().get("access_token")
    print(f"✅ Login successful, token: {token[:20]}...")
    
    # Call the move-standby-files endpoint with empty crew_ids to trigger folder detection
    print("\n2. Calling move-standby-files endpoint (empty crew list)...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    move_response = requests.post(
        f"{BACKEND_URL}/api/crew/move-standby-files",
        headers=headers,
        json={"crew_ids": []}
    )
    
    print(f"\n3. Response Status: {move_response.status_code}")
    print(f"Response Body:")
    print(json.dumps(move_response.json(), indent=2))
    
    print("\n" + "=" * 80)
    print("✅ Test completed!")
    print("📋 Check backend logs for detailed folder detection output:")
    print("    tail -n 100 /var/log/supervisor/backend.out.log")
    print("=" * 80)

if __name__ == "__main__":
    test_standby_folder_detection()

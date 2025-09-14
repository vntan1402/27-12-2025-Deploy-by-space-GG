#!/usr/bin/env python3
"""
Debug OAuth Implementation - Check actual responses
"""

import requests
import json

def test_oauth_debug():
    base_url = "https://shipgooglesync.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login first
    login_response = requests.post(f"{api_url}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = login_response.json()['access_token']
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test OAuth authorize endpoint
    oauth_config = {
        "client_id": "123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com",
        "client_secret": "GOCSPX-abcdefghijklmnopqrstuvwxyz123456",
        "redirect_uri": "https://shipgooglesync.preview.emergentagent.com/oauth/callback",
        "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
    }
    
    print("🔍 Testing OAuth Authorize Endpoint...")
    auth_response = requests.post(f"{api_url}/gdrive/oauth/authorize", json=oauth_config, headers=headers)
    
    print(f"Status Code: {auth_response.status_code}")
    print(f"Response: {json.dumps(auth_response.json(), indent=2)}")
    
    if auth_response.status_code == 200:
        response_data = auth_response.json()
        
        # Check if we have the expected fields
        print(f"\nResponse Analysis:")
        print(f"- Success: {response_data.get('success', 'Not present')}")
        print(f"- Message: {response_data.get('message', 'Not present')}")
        print(f"- Authorization URL: {response_data.get('authorization_url', 'Not present')}")
        print(f"- State: {response_data.get('state', 'Not present')}")
        
        # Test callback with the state (if available)
        state = response_data.get('state')
        if state:
            print(f"\n🔍 Testing OAuth Callback with state: {state}")
            callback_data = {
                "authorization_code": "4/0AX4XfWh1234567890abcdefghijklmnopqrstuvwxyz",
                "state": state,
                "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
            }
            
            callback_response = requests.post(f"{api_url}/gdrive/oauth/callback", json=callback_data, headers=headers)
            print(f"Callback Status Code: {callback_response.status_code}")
            print(f"Callback Response: {json.dumps(callback_response.json(), indent=2)}")

if __name__ == "__main__":
    test_oauth_debug()
#!/usr/bin/env python3
"""
Debug script to check if place_sign_on field is being saved to database
"""

import requests
import json
import os

# Configuration
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL from environment
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

def authenticate():
    """Authenticate and get token"""
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def main():
    print("🔍 Debugging place_sign_on field issue...")
    
    # Authenticate
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get crew members
    response = requests.get(f"{BACKEND_URL}/crew?ship_name=BROTHER%2036", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get crew members: {response.status_code}")
        return
    
    crew_members = response.json()
    if not crew_members:
        print("❌ No crew members found")
        return
    
    # Test with first crew member
    test_crew = crew_members[0]
    crew_id = test_crew.get('id')
    crew_name = test_crew.get('full_name', 'Unknown')
    
    print(f"🧪 Testing with crew: {crew_name} (ID: {crew_id})")
    
    # Check current state
    print(f"📋 Current crew data:")
    for key, value in test_crew.items():
        print(f"   {key}: {value}")
    
    # Update place_sign_on
    test_value = "DEBUG TEST - Hai Phong, Vietnam"
    update_data = {"place_sign_on": test_value}
    
    print(f"\n🔄 Updating place_sign_on to: {test_value}")
    response = requests.put(f"{BACKEND_URL}/crew/{crew_id}", json=update_data, headers=headers)
    
    print(f"📤 Update response status: {response.status_code}")
    if response.status_code == 200:
        response_data = response.json()
        print(f"📋 Update response data:")
        for key, value in response_data.items():
            print(f"   {key}: {value}")
        
        # Check if place_sign_on is in response
        if 'place_sign_on' in response_data:
            print(f"✅ place_sign_on in response: {response_data['place_sign_on']}")
        else:
            print("❌ place_sign_on NOT in response")
    else:
        print(f"❌ Update failed: {response.text}")
        return
    
    # Get crew member again to check persistence
    print(f"\n🔍 Checking persistence...")
    response = requests.get(f"{BACKEND_URL}/crew/{crew_id}", headers=headers)
    
    if response.status_code == 200:
        retrieved_data = response.json()
        print(f"📋 Retrieved crew data:")
        for key, value in retrieved_data.items():
            print(f"   {key}: {value}")
        
        # Check if place_sign_on is in retrieved data
        if 'place_sign_on' in retrieved_data:
            print(f"✅ place_sign_on persisted: {retrieved_data['place_sign_on']}")
        else:
            print("❌ place_sign_on NOT persisted in response")
    else:
        print(f"❌ Failed to retrieve crew: {response.status_code}")
    
    # Get crew list to check if it appears there
    print(f"\n🔍 Checking crew list...")
    response = requests.get(f"{BACKEND_URL}/crew?ship_name=BROTHER%2036", headers=headers)
    
    if response.status_code == 200:
        crew_list = response.json()
        for crew in crew_list:
            if crew.get('id') == crew_id:
                print(f"📋 Crew in list:")
                for key, value in crew.items():
                    print(f"   {key}: {value}")
                
                if 'place_sign_on' in crew:
                    print(f"✅ place_sign_on in crew list: {crew['place_sign_on']}")
                else:
                    print("❌ place_sign_on NOT in crew list")
                break
        else:
            print("❌ Crew not found in list")
    else:
        print(f"❌ Failed to get crew list: {response.status_code}")

if __name__ == "__main__":
    main()
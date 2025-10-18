#!/usr/bin/env python3
"""
Test Standby Crew Folder Detection with Real Crew Data
"""

import requests
import json
import os
import time

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL")
    else:
        raise Exception("Internal URL not working")
except:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                external_url = line.split('=', 1)[1].strip()
                BACKEND_URL = external_url + '/api'
                print(f"Using external backend URL: {BACKEND_URL}")
                break

def authenticate():
    """Authenticate and return session"""
    session = requests.Session()
    
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ Authentication successful")
        return session
    else:
        print("❌ Authentication failed")
        return None

def get_standby_crew(session):
    """Get crew members with Standby status"""
    response = session.get(f"{BACKEND_URL}/crew")
    if response.status_code == 200:
        crew_list = response.json()
        standby_crew = [crew for crew in crew_list if crew.get('status') == 'Standby']
        print(f"Found {len(standby_crew)} standby crew members")
        return standby_crew
    return []

def test_move_standby_files(session, crew_ids):
    """Test move standby files with real crew IDs"""
    print(f"\n🔄 Testing move-standby-files with {len(crew_ids)} crew members...")
    
    # Monitor backend logs in real-time
    print("📋 Monitoring backend logs...")
    
    # Make the API call
    test_data = {"crew_ids": crew_ids}
    
    print(f"📤 POST /api/crew/move-standby-files")
    print(f"📋 Crew IDs: {crew_ids}")
    
    start_time = time.time()
    response = session.post(f"{BACKEND_URL}/crew/move-standby-files", json=test_data, timeout=120)
    end_time = time.time()
    
    print(f"⏱️ Processing time: {end_time - start_time:.1f} seconds")
    print(f"📡 Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"📊 Response: {json.dumps(result, indent=2)}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def main():
    print("🚀 Testing Standby Crew Folder Detection with Real Crew Data")
    print("=" * 60)
    
    # Authenticate
    session = authenticate()
    if not session:
        return
    
    # Get standby crew
    standby_crew = get_standby_crew(session)
    
    if standby_crew:
        # Test with first standby crew member
        crew_ids = [standby_crew[0]['id']]
        crew_name = standby_crew[0]['full_name']
        print(f"Testing with crew: {crew_name}")
        
        success = test_move_standby_files(session, crew_ids)
        
        if success:
            print("\n✅ Test completed - Check backend logs for 2-step process details")
        else:
            print("\n❌ Test failed")
    else:
        print("No standby crew found - testing with empty crew_ids")
        test_move_standby_files(session, [])
    
    print("\n📋 Check backend logs with:")
    print("tail -f /var/log/supervisor/backend.out.log | grep -E 'Step 1|Step 2|COMPANY DOCUMENT|Standby Crew'")

if __name__ == "__main__":
    main()
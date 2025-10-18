#!/usr/bin/env python3
"""
Test the Standby Crew folder detection by triggering it with actual crew data.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')

BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')

def main():
    print("=" * 80)
    print("Testing Standby Crew Folder Detection - With Real Crew")
    print("=" * 80)
    
    # Login
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={
            "username": "admin",
            "password": "admin123",
            "remember_me": False
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed")
        return
    
    token = login_response.json().get("access_token")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("✅ Login successful")
    
    # Get crew list
    print("\n2. Fetching crew list...")
    crew_response = requests.get(
        f"{BACKEND_URL}/api/crew",
        headers=headers
    )
    
    if crew_response.status_code != 200:
        print(f"❌ Failed to fetch crew")
        return
    
    crew_list = crew_response.json()
    print(f"✅ Found {len(crew_list)} crew members")
    
    # Filter for Standby crew
    standby_crew = [c for c in crew_list if (c.get("status") or "").lower() == "standby"]
    print(f"📊 Standby crew count: {len(standby_crew)}")
    
    if not standby_crew:
        print("\n⚠️ No Standby crew found. Creating a test scenario...")
        print("   Using first crew member if available...")
        if crew_list:
            test_crew_ids = [crew_list[0]["id"]]
            print(f"   Using crew: {crew_list[0].get('full_name', 'Unknown')}")
        else:
            print("❌ No crew members found in database")
            return
    else:
        # Use first few standby crew
        test_crew_ids = [c["id"] for c in standby_crew[:2]]
        print(f"   Using crew: {', '.join([c.get('full_name', c['id']) for c in standby_crew[:2]])}")
    
    # Trigger folder detection
    print(f"\n3. Triggering move-standby-files with {len(test_crew_ids)} crew IDs...")
    print(f"   This will trigger the Standby Crew folder detection logic...")
    
    move_response = requests.post(
        f"{BACKEND_URL}/api/crew/move-standby-files",
        headers=headers,
        json={"crew_ids": test_crew_ids}
    )
    
    print(f"\n4. Response Status: {move_response.status_code}")
    print(f"Response Body:")
    print(json.dumps(move_response.json(), indent=2))
    
    print("\n" + "=" * 80)
    print("✅ Test completed!")
    print("\n📋 NOW CHECK THE BACKEND LOGS FOR DETAILED OUTPUT:")
    print("    tail -n 150 /var/log/supervisor/backend.out.log | grep -A 5 -B 5 'Standby'")
    print("\n    OR view full logs:")
    print("    tail -n 200 /var/log/supervisor/backend.out.log")
    print("=" * 80)

if __name__ == "__main__":
    main()

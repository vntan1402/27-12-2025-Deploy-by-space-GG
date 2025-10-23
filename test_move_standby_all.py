#!/usr/bin/env python3
import requests

BACKEND_URL = 'https://shipdata-hub.preview.emergentagent.com/api'

print("=" * 70)
print("🧪 TEST: Move All Standby Crew Files")
print("=" * 70)

# Authenticate
print("\n📝 Authentication...")
login_response = requests.post(
    f"{BACKEND_URL}/auth/login",
    json={"username": "admin1", "password": "123456", "remember_me": False}
)
token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print("✅ Authenticated")

# Get all crew
print("\n📝 Finding all Standby crew...")
crew_response = requests.get(f"{BACKEND_URL}/crew", headers=headers)
all_crew = crew_response.json()

standby_crew = []
for c in all_crew:
    if c.get("status", "").lower() == "standby":
        standby_crew.append(c)
        print(f"   ✅ {c.get('full_name')} - Passport: {c.get('passport_file_id')}")

print(f"\n📊 Found {len(standby_crew)} Standby crew members")

if len(standby_crew) == 0:
    print("❌ No Standby crew found")
    exit(1)

# Call move API
print("\n📝 Calling move-standby-files API...")
crew_ids = [c.get("id") for c in standby_crew]

try:
    move_response = requests.post(
        f"{BACKEND_URL}/crew/move-standby-files",
        json={"crew_ids": crew_ids},
        headers=headers,
        timeout=120
    )
    
    print(f"\n📊 Response Status: {move_response.status_code}")
    
    if move_response.status_code == 200:
        result = move_response.json()
        print("✅ SUCCESS")
        print(f"\n📋 Result:")
        print(f"   Moved Count: {result.get('moved_count')}")
        print(f"   Message: {result.get('message')}")
        
        if result.get('errors'):
            print(f"\n⚠️ Errors:")
            for error in result.get('errors', []):
                print(f"   - {error}")
    else:
        print(f"❌ FAILED: {move_response.text}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)

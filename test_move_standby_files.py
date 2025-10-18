#!/usr/bin/env python3
"""
Test moving Standby crew files
"""
import requests
import json

# Configuration
BACKEND_URL = 'https://fleet-cert-system.preview.emergentagent.com/api'
STANDBY_FOLDER_ID = '1KU_1o-FcY3g2O9dKO5xxPhv1P2u56aO6'  # Real folder ID from user

print("=" * 70)
print("🧪 TEST: Move Standby Crew Files")
print("=" * 70)

# Step 1: Authenticate
print("\n📝 Step 1: Authentication...")
login_response = requests.post(
    f"{BACKEND_URL}/auth/login",
    json={"username": "admin1", "password": "123456", "remember_me": False}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit(1)

token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print("✅ Authenticated successfully")

# Step 2: Find TRAN VAN DUC
print("\n📝 Step 2: Finding TRAN VAN DUC...")
crew_response = requests.get(
    f"{BACKEND_URL}/crew?ship_name=BROTHER 36",
    headers=headers
)

crew = None
for c in crew_response.json():
    name = c.get("full_name", "").upper()
    if "TRAN VAN DUC" in name or "TRẦN VĂN ĐỨC" in name:
        crew = c
        break

if not crew:
    print("❌ Crew TRAN VAN DUC not found")
    exit(1)

print(f"✅ Found crew: {crew.get('full_name')}")
print(f"   Crew ID: {crew.get('id')}")
print(f"   Status: {crew.get('status')}")
print(f"   Passport File ID: {crew.get('passport_file_id')}")
print(f"   Date Sign Off: {crew.get('date_sign_off')}")

# Step 3: Get crew certificates
print("\n📝 Step 3: Getting crew certificates...")
certs_response = requests.get(
    f"{BACKEND_URL}/crew-certificates?crew_id={crew.get('id')}",
    headers=headers
)

certs_data = certs_response.json()
if isinstance(certs_data, list):
    certs = certs_data
else:
    certs = certs_data.get('certificates', [])
    
print(f"   Found {len(certs)} certificates")
for cert in certs:
    if isinstance(cert, dict):
        print(f"   - {cert.get('cert_name')}: file_id={cert.get('crew_cert_file_id')}")

# Step 4: Test move files with CORRECT folder ID
print("\n📝 Step 4: Testing move files with correct folder ID...")
print(f"   Target Folder ID: {STANDBY_FOLDER_ID}")

try:
    move_response = requests.post(
        f"{BACKEND_URL}/crew/move-standby-files",
        json={
            "crew_ids": [crew.get("id")]
        },
        headers=headers,
        timeout=120
    )
    
    print(f"\n📊 Response Status: {move_response.status_code}")
    print("=" * 70)
    
    if move_response.status_code == 200:
        result = move_response.json()
        print("✅ SUCCESS")
        print(f"\n📋 Result:")
        print(f"   Success: {result.get('success')}")
        print(f"   Moved Count: {result.get('moved_count')}")
        print(f"   Message: {result.get('message')}")
        
        if result.get('errors'):
            print(f"\n⚠️ Errors:")
            for error in result['errors']:
                print(f"   - {error}")
    else:
        print(f"❌ FAILED")
        print(f"Response: {move_response.text}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)

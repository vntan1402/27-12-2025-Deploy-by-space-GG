#!/usr/bin/env python3
"""
Test the new Next Survey API endpoint
"""
import requests
import json

backend_url = 'http://localhost:8001'

# Login
login_data = {
    "username": "admin1",
    "password": "123456"
}

session = requests.Session()

print("🔐 Logging in...")
login_response = session.post(f"{backend_url}/api/auth/login", json=login_data)

if login_response.status_code == 200:
    login_result = login_response.json()
    token = login_result.get('access_token')
    session.headers.update({'Authorization': f'Bearer {token}'})
    print("✅ Login successful")
    
    # Get ships to test with
    print("\n🚢 Getting ships...")
    ships_response = session.get(f"{backend_url}/api/ships")
    
    if ships_response.status_code == 200:
        ships = ships_response.json()
        print(f"Found {len(ships)} ships")
        
        if ships:
            # Test with first ship
            test_ship = ships[0]
            ship_id = test_ship['id']
            ship_name = test_ship.get('name', 'Unknown')
            
            print(f"\n🎯 Testing Next Survey update for ship: {ship_name}")
            
            # Call the new API endpoint
            update_response = session.post(f"{backend_url}/api/ships/{ship_id}/update-next-survey")
            print(f"Response status: {update_response.status_code}")
            
            if update_response.status_code == 200:
                result = update_response.json()
                print("✅ Next Survey update successful!")
                print(f"Updated certificates: {result.get('updated_count', 0)}")
                print(f"Total certificates: {result.get('total_certificates', 0)}")
                
                # Show some results
                results = result.get('results', [])
                if results:
                    print(f"\n📋 Sample updates:")
                    for update_result in results[:3]:  # Show first 3
                        print(f"   - {update_result['cert_name']}")
                        print(f"     Type: {update_result['cert_type']}")
                        print(f"     Next Survey: {update_result['old_next_survey']} → {update_result['new_next_survey']}")
                        print(f"     Next Survey Type: {update_result['old_next_survey_type']} → {update_result['new_next_survey_type']}")
                        print(f"     Reasoning: {update_result['reasoning']}")
                        print()
                else:
                    print("   No certificates were updated")
            else:
                try:
                    error_data = update_response.json()
                    print(f"❌ Update failed: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"❌ Update failed: {update_response.status_code} - {update_response.text}")
        else:
            print("❌ No ships found")
    else:
        print(f"❌ Failed to get ships: {ships_response.status_code}")
else:
    print(f"❌ Login failed: {login_response.text}")
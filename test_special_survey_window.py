#!/usr/bin/env python3
"""
Test Special Survey window logic (-3M vs ±3M)
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
            # Test with first ship (SUNSHINE 01)
            test_ship = ships[0]
            ship_id = test_ship['id']
            ship_name = test_ship.get('name', 'Unknown')
            
            print(f"\n🎯 Testing Special Survey window logic for ship: {ship_name}")
            
            # Update Next Survey to trigger recalculation
            update_response = session.post(f"{backend_url}/api/ships/{ship_id}/update-next-survey")
            
            if update_response.status_code == 200:
                result = update_response.json()
                print("✅ Next Survey update successful!")
                print(f"Updated certificates: {result.get('updated_count', 0)}")
                
                # Show results with window information
                results = result.get('results', [])
                if results:
                    print(f"\n📋 Survey window analysis:")
                    for update_result in results:
                        cert_name = update_result['cert_name']
                        survey_type = update_result['new_next_survey_type']
                        next_survey = update_result['new_next_survey']
                        
                        print(f"   - {cert_name}")
                        print(f"     Next Survey: {next_survey}")
                        print(f"     Survey Type: {survey_type}")
                        
                        # Check window format
                        if survey_type == 'Special Survey':
                            if '(-3M)' in next_survey:
                                print(f"     ✅ Correct: Special Survey shows -3M window")
                            elif '(±3M)' in next_survey:
                                print(f"     ❌ Incorrect: Special Survey should show -3M, not ±3M")
                            else:
                                print(f"     ❓ Unknown window format: {next_survey}")
                        else:
                            if '(±3M)' in next_survey:
                                print(f"     ✅ Correct: Non-Special Survey shows ±3M window")
                            elif '(-3M)' in next_survey:
                                print(f"     ❓ Unusual: Non-Special Survey shows -3M window")
                            else:
                                print(f"     ❓ Unknown window format: {next_survey}")
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
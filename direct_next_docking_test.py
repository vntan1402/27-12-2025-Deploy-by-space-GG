#!/usr/bin/env python3
"""
Direct Next Docking Endpoint Test
Test the specific endpoint with the exact scenario from the review request
"""

import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Get backend URL from frontend/.env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=')[1].strip() + '/api'
            break

def authenticate():
    """Authenticate and get token"""
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_specific_scenario():
    """Test the specific scenario from review request"""
    print("🔄 TESTING SPECIFIC NEXT DOCKING SCENARIO FROM REVIEW REQUEST")
    print("=" * 70)
    
    # Authenticate
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get ships to find one with Last Docking date
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers, timeout=30)
    if ships_response.status_code != 200:
        print("❌ Failed to get ships")
        return
    
    ships = ships_response.json()
    print(f"📊 Found {len(ships)} ships")
    
    # Find a ship with Last Docking date
    test_ship = None
    for ship in ships:
        if ship.get('last_docking'):
            test_ship = ship
            break
    
    if not test_ship:
        print("❌ No ship with Last Docking date found")
        return
    
    ship_id = test_ship['id']
    ship_name = test_ship['name']
    current_last_docking = test_ship['last_docking']
    
    print(f"🚢 Testing with ship: {ship_name}")
    print(f"   Ship ID: {ship_id}")
    print(f"   Current Last Docking: {current_last_docking}")
    
    # Update ship with the specific test date from review request: 05/05/2022
    test_last_docking = "2022-05-05T00:00:00"
    
    update_data = {
        "name": ship_name,
        "flag": test_ship.get('flag', 'PANAMA'),
        "ship_type": test_ship.get('ship_type', 'PMDS'),
        "last_docking": test_last_docking
    }
    
    print(f"\n🔄 Step 1: Update ship with test Last Docking date")
    print(f"   Setting Last Docking to: {test_last_docking}")
    
    update_response = requests.put(f"{BACKEND_URL}/ships/{ship_id}", json=update_data, headers=headers, timeout=30)
    
    if update_response.status_code == 200:
        updated_ship = update_response.json()
        print("✅ Ship updated successfully")
        print(f"   Updated Last Docking: {updated_ship.get('last_docking')}")
        print(f"   Updated Next Docking: {updated_ship.get('next_docking')}")
        
        # Calculate expected result
        last_docking_dt = datetime.fromisoformat(test_last_docking.replace('T00:00:00', ''))
        expected_next_docking = last_docking_dt + relativedelta(months=36)
        
        print(f"\n📊 Expected Calculation Analysis:")
        print(f"   Last Docking: {last_docking_dt.strftime('%d/%m/%Y')}")
        print(f"   Expected Next Docking (relativedelta): {expected_next_docking.strftime('%d/%m/%Y')}")
        print(f"   Expected: 05/05/2022 + 36 months = 05/05/2025 ✅")
        
        # Check if automatic calculation matches expected
        if updated_ship.get('next_docking'):
            actual_next = datetime.fromisoformat(updated_ship['next_docking'].replace('Z', '+00:00'))
            print(f"   Actual Next Docking: {actual_next.strftime('%d/%m/%Y')}")
            
            if (actual_next.day == expected_next_docking.day and 
                actual_next.month == expected_next_docking.month and
                actual_next.year == expected_next_docking.year):
                print("   ✅ AUTOMATIC CALCULATION CORRECT - Fix is working!")
            else:
                print("   ❌ AUTOMATIC CALCULATION INCORRECT")
        else:
            print("   ⚠️ No automatic Next Docking calculation")
    else:
        print(f"❌ Ship update failed: {update_response.status_code}")
        return
    
    # Test the specific endpoint
    print(f"\n🔄 Step 2: Test calculate-next-docking endpoint")
    
    endpoint_response = requests.post(f"{BACKEND_URL}/ships/{ship_id}/calculate-next-docking", headers=headers, timeout=30)
    
    if endpoint_response.status_code == 200:
        endpoint_data = endpoint_response.json()
        print("✅ Endpoint accessible")
        print(f"   Response: {json.dumps(endpoint_data, indent=4)}")
        
        # Analyze the response
        if endpoint_data.get('success'):
            next_docking_info = endpoint_data.get('next_docking', {})
            
            if isinstance(next_docking_info, dict):
                next_docking_date = next_docking_info.get('date')
                calculation_method = next_docking_info.get('calculation_method')
                
                print(f"\n📊 Endpoint Calculation Analysis:")
                print(f"   Calculation Method: {calculation_method}")
                print(f"   Next Docking Date: {next_docking_date}")
                
                if next_docking_date:
                    # Parse the date (format might be DD/MM/YYYY)
                    try:
                        if '/' in next_docking_date:
                            day, month, year = next_docking_date.split('/')
                            endpoint_date = datetime(int(year), int(month), int(day))
                        else:
                            endpoint_date = datetime.fromisoformat(next_docking_date)
                        
                        print(f"   Parsed Date: {endpoint_date.strftime('%d/%m/%Y')}")
                        
                        # Compare with expected
                        if (endpoint_date.day == expected_next_docking.day and 
                            endpoint_date.month == expected_next_docking.month and
                            endpoint_date.year == expected_next_docking.year):
                            print("   ✅ ENDPOINT CALCULATION CORRECT - Fix is working!")
                        else:
                            print("   ❌ ENDPOINT CALCULATION INCORRECT")
                            print(f"      Expected: {expected_next_docking.strftime('%d/%m/%Y')}")
                            print(f"      Got: {endpoint_date.strftime('%d/%m/%Y')}")
                    except Exception as e:
                        print(f"   ❌ Error parsing endpoint date: {e}")
            else:
                print(f"   Next Docking: {next_docking_info}")
        else:
            print(f"   ❌ Endpoint calculation failed: {endpoint_data.get('message')}")
    else:
        print(f"❌ Endpoint failed: {endpoint_response.status_code}")
        try:
            error_data = endpoint_response.json()
            print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"   Error: {endpoint_response.text[:200]}")
    
    print(f"\n🎯 REVIEW REQUEST VERIFICATION:")
    print(f"   Expected Behavior: 05/05/2022 + 36 months = 05/05/2025")
    print(f"   Before Fix: Would give 04/05/2025 (1-day shift ❌)")
    print(f"   After Fix: Should give 05/05/2025 (correct ✅)")

if __name__ == "__main__":
    test_specific_scenario()
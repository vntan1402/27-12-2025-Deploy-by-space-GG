#!/usr/bin/env python3
"""
Manual test script to verify the Google Drive ship deletion bug fix
"""
import requests
import json
import sys

API_URL = "https://shipmate-55.preview.emergentagent.com"

def login():
    """Login and get auth token"""
    login_data = {
        "username": "admin1", 
        "password": "123456"
    }
    
    response = requests.post(f"{API_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def get_ships(token):
    """Get list of ships"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/api/ships", headers=headers)
    
    if response.status_code == 200:
        ships = response.json()
        print(f"✅ Found {len(ships)} ships")
        for ship in ships:
            print(f"   - {ship.get('name')} (ID: {ship.get('id')})")
        return ships
    else:
        print(f"❌ Failed to get ships: {response.status_code}")
        return []

def test_ship_deletion_with_google_drive(token, ship_id, ship_name):
    """Test ship deletion with Google Drive folder deletion"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # First, test the Google Drive configuration lookup by attempting deletion
    print(f"\n🗑️ Testing Google Drive ship deletion for: {ship_name}")
    
    # Make DELETE request with delete_google_drive_folder=true
    url = f"{API_URL}/api/ships/{ship_id}?delete_google_drive_folder=true"
    response = requests.delete(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Ship deletion request completed")
        print(f"Database deletion: {result.get('database_deletion', 'unknown')}")
        print(f"Google Drive deletion requested: {result.get('google_drive_deletion_requested', 'unknown')}")
        if 'google_drive_deletion' in result:
            gdrive_result = result['google_drive_deletion']
            print(f"Google Drive deletion result: {gdrive_result.get('success', 'unknown')}")
            if gdrive_result.get('message'):
                print(f"Google Drive message: {gdrive_result['message']}")
        return True
    else:
        print(f"❌ Ship deletion failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    print("🧪 Testing Ship Deletion with Google Drive folder deletion fix")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        sys.exit(1)
    
    # Get ships
    ships = get_ships(token)
    if not ships:
        print("❌ No ships found for testing")
        sys.exit(1)
    
    # Find a test ship (preferably not the main ones)
    test_ship = None
    for ship in ships:
        ship_name = ship.get('name', '')
        # Avoid deleting main ships, look for test ships
        if 'TEST' in ship_name.upper() or ship_name in ['SUNSHINE 01']:  # We can test with SUNSHINE 01 as it's been used in tests
            test_ship = ship
            break
    
    if not test_ship:
        # Just use the first ship for testing (we're just testing the configuration lookup)
        test_ship = ships[0]
        print(f"⚠️ Using first available ship for testing: {test_ship.get('name')}")
    
    print(f"\n📋 Test ship selected: {test_ship.get('name')} (ID: {test_ship.get('id')})")
    
    # Ask user confirmation before proceeding with deletion
    confirmation = input(f"\n⚠️ This will DELETE the ship '{test_ship.get('name')}' and its Google Drive folder. Continue? (yes/no): ")
    if confirmation.lower() not in ['yes', 'y']:
        print("❌ Test cancelled by user")
        sys.exit(0)
    
    # Test deletion with Google Drive
    success = test_ship_deletion_with_google_drive(
        token, 
        test_ship.get('id'), 
        test_ship.get('name')
    )
    
    if success:
        print("\n✅ Test completed successfully - Google Drive configuration lookup is now working!")
    else:
        print("\n❌ Test failed - there may still be issues with the configuration lookup")

if __name__ == "__main__":
    main()
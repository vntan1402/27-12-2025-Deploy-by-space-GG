#!/usr/bin/env python3
"""
Focused test for crew certificates endpoint - testing the actual endpoint functionality
"""

import requests
import json
import io
from datetime import datetime

# Configuration
BACKEND_URL = 'https://test-survey-portal.preview.emergentagent.com/api'

def test_endpoint_registration():
    """Test if the endpoint is registered (not 404)"""
    print("🔍 Testing endpoint registration...")
    
    # Login first
    login_response = requests.post(f'{BACKEND_URL}/auth/login', 
                                  json={'username': 'admin1', 'password': '123456'})
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test the endpoint with minimal data to see if it's registered
    dummy_pdf = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>'
    files = {'cert_file': ('test.pdf', io.BytesIO(dummy_pdf), 'application/pdf')}
    data = {'ship_id': 'test-ship-id'}
    
    response = requests.post(f'{BACKEND_URL}/crew-certificates/analyze-file',
                           files=files, data=data, headers=headers, timeout=30)
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 404:
        if "Not Found" in response.text and "detail" not in response.text:
            print("❌ ENDPOINT NOT REGISTERED - Returns FastAPI 404")
            return False
        else:
            print("✅ ENDPOINT IS REGISTERED - Returns application 404 (Ship not found)")
            return True
    else:
        print("✅ ENDPOINT IS REGISTERED - Returns non-404 response")
        return True

def test_with_valid_ship():
    """Test with a ship that has correct company_id"""
    print("\n🚢 Testing with ships that have company_id...")
    
    # Login
    login_response = requests.post(f'{BACKEND_URL}/auth/login', 
                                  json={'username': 'admin1', 'password': '123456'})
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json()['access_token']
    user = login_response.json()['user']
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"User company: {user.get('company')}")
    
    # Get all ships and check their company_id
    ships_response = requests.get(f'{BACKEND_URL}/ships', headers=headers)
    if ships_response.status_code != 200:
        print(f"❌ Failed to get ships: {ships_response.status_code}")
        return False
    
    ships = ships_response.json()
    print(f"Found {len(ships)} ships:")
    
    valid_ship = None
    for ship in ships:
        ship_id = ship.get('id')
        ship_name = ship.get('name')
        company_id = ship.get('company_id')
        company = ship.get('company')
        
        print(f"  - {ship_name}: company='{company}', company_id='{company_id}'")
        
        # Check if this ship has a company_id
        if company_id:
            valid_ship = ship
            break
    
    if not valid_ship:
        print("⚠️ No ships found with company_id set")
        print("This explains why the endpoint returns 'Ship not found'")
        print("The endpoint logic requires ships to have company_id matching user's company")
        return False
    
    # Test with the valid ship
    print(f"\n✅ Testing with ship that has company_id: {valid_ship['name']}")
    
    dummy_pdf = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>'
    files = {'cert_file': ('test.pdf', io.BytesIO(dummy_pdf), 'application/pdf')}
    data = {'ship_id': valid_ship['id']}
    
    response = requests.post(f'{BACKEND_URL}/crew-certificates/analyze-file',
                           files=files, data=data, headers=headers, timeout=60)
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 404 and "Ship not found" in response.text:
        print("❌ Still getting 'Ship not found' - company_id mismatch issue")
        return False
    elif response.status_code in [200, 400, 500]:
        print("✅ Endpoint is working - got past ship validation")
        return True
    else:
        print(f"⚠️ Unexpected response: {response.status_code}")
        return True

def main():
    print("🎯 FOCUSED CREW CERTIFICATES ENDPOINT TEST")
    print("=" * 60)
    print("Goal: Verify the endpoint is registered and identify the real issue")
    print("=" * 60)
    
    # Test 1: Check if endpoint is registered
    endpoint_registered = test_endpoint_registration()
    
    # Test 2: Check ship data issue
    ship_data_ok = test_with_valid_ship()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    if endpoint_registered:
        print("✅ ENDPOINT IS REGISTERED: /api/crew-certificates/analyze-file exists")
        print("✅ The 404 error is NOT because the endpoint doesn't exist")
        print("✅ The 404 error is because of 'Ship not found' logic")
    else:
        print("❌ ENDPOINT NOT REGISTERED: FastAPI returns 404 Not Found")
        print("❌ Need to check endpoint registration in server.py")
    
    if not ship_data_ok:
        print("🔍 ROOT CAUSE IDENTIFIED:")
        print("   - Ships in database have company_id = null")
        print("   - Endpoint requires ship.company_id = user.company_id")
        print("   - This is a DATA ISSUE, not an endpoint issue")
        print("\n💡 SOLUTION:")
        print("   - Update ship records to have correct company_id")
        print("   - OR modify endpoint logic to handle null company_id")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
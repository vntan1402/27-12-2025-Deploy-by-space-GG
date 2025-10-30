#!/usr/bin/env python3
"""
Debug script to check company ID mismatch issue
"""

import requests
import json

# Backend URL
BACKEND_URL = "https://cert-tracker-8.preview.emergentagent.com/api"

def debug_company_mismatch():
    """Debug the company ID mismatch"""
    
    # Login
    session = requests.Session()
    login_response = session.post(f"{BACKEND_URL}/auth/login", json={
        "username": "admin1",
        "password": "123456"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    auth_data = login_response.json()
    access_token = auth_data["access_token"]
    user_data = auth_data["user"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"👤 User Data:")
    print(f"   Username: {user_data['username']}")
    print(f"   Company: {user_data['company']}")
    print(f"   Role: {user_data['role']}")
    
    user_company = user_data['company']
    
    # Get all companies
    companies_response = session.get(f"{BACKEND_URL}/companies", headers=headers)
    if companies_response.status_code == 200:
        companies = companies_response.json()
        print(f"\n🏢 All Companies:")
        for company in companies:
            print(f"   ID: {company.get('id')}")
            print(f"   Name EN: {company.get('name_en')}")
            print(f"   Name VN: {company.get('name_vn')}")
            print(f"   Match User Company: {company.get('id') == user_company}")
            print()
    
    # Get all ships
    ships_response = session.get(f"{BACKEND_URL}/ships", headers=headers)
    if ships_response.status_code == 200:
        ships = ships_response.json()
        print(f"🚢 All Ships:")
        for ship in ships:
            print(f"   ID: {ship.get('id')}")
            print(f"   Name: {ship.get('name')}")
            print(f"   Company: {ship.get('company')}")
            print(f"   Match User Company: {ship.get('company') == user_company}")
            print()
    
    # Check what the upcoming surveys endpoint is actually looking for
    print(f"🔍 Upcoming Surveys Logic:")
    print(f"   User Company ID: {user_company}")
    print(f"   Looking for ships with company field = '{user_company}'")
    
    # Check if any ships match
    matching_ships = []
    if ships_response.status_code == 200:
        ships = ships_response.json()
        for ship in ships:
            if ship.get('company') == user_company:
                matching_ships.append(ship)
        
        print(f"   Found {len(matching_ships)} matching ships")
        
        if matching_ships:
            print(f"   Matching ships:")
            for ship in matching_ships:
                print(f"     - {ship.get('name')} (ID: {ship.get('id')})")
        else:
            print(f"   ❌ NO MATCHING SHIPS FOUND!")
            print(f"   This explains why upcoming surveys returns empty list")
            
            print(f"\n🔧 Ship company values vs user company:")
            for ship in ships:
                ship_company = ship.get('company')
                print(f"     Ship '{ship.get('name')}': company='{ship_company}'")
                print(f"       Type: {type(ship_company)}")
                print(f"       Length: {len(ship_company) if ship_company else 'None'}")
                print(f"       User company: '{user_company}'")
                print(f"       Type: {type(user_company)}")
                print(f"       Length: {len(user_company) if user_company else 'None'}")
                print(f"       Equal: {ship_company == user_company}")
                print(f"       Equal (stripped): {ship_company.strip() == user_company.strip() if ship_company and user_company else False}")
                print()

if __name__ == "__main__":
    debug_company_mismatch()
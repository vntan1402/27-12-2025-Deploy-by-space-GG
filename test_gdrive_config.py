#!/usr/bin/env python3
"""
Test Google Drive configuration for AMCSC company
"""

import requests
import json
import os

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vesseldocs.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

def authenticate():
    """Authenticate with admin1/123456"""
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token"), data.get("user", {})
    return None, None

def get_headers(token):
    """Get authentication headers"""
    return {"Authorization": f"Bearer {token}"}

def main():
    print("🔍 Testing Google Drive Configuration")
    print("=" * 50)
    
    # Authenticate
    token, user = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    print(f"✅ Authenticated as: {user.get('username')} ({user.get('company')})")
    
    # Get companies
    response = requests.get(f"{BACKEND_URL}/companies", headers=get_headers(token), timeout=30)
    if response.status_code == 200:
        companies = response.json()
        print(f"\n📋 Found {len(companies)} companies:")
        for company in companies:
            company_id = company.get('id')
            company_name = company.get('name_en', company.get('name', 'Unknown'))
            print(f"  - {company_name} (ID: {company_id})")
            
            # Check Google Drive config for each company
            gdrive_response = requests.get(f"{BACKEND_URL}/companies/{company_id}/gdrive/status", 
                                         headers=get_headers(token), timeout=30)
            if gdrive_response.status_code == 200:
                gdrive_data = gdrive_response.json()
                print(f"    Google Drive Status: {gdrive_data.get('status', 'Unknown')}")
                if gdrive_data.get('message'):
                    print(f"    Message: {gdrive_data.get('message')}")
            else:
                print(f"    Google Drive Status: Not configured (HTTP {gdrive_response.status_code})")
    else:
        print(f"❌ Failed to get companies: {response.status_code}")

if __name__ == "__main__":
    main()
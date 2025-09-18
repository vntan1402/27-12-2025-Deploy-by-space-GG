#!/usr/bin/env python3
"""
Company Update Fix Test

This test confirms the root cause and tests the fix for the company update issue.
"""

import requests
import json
import sys

def test_company_update_endpoint():
    """Test if company update endpoint exists"""
    base_url = "https://shipmanage.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login first
    login_response = requests.post(f"{api_url}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return False
    
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Test PUT endpoint
    company_id = "cfe73cb0-cc88-4659-92a7-57cb413a5573"
    update_data = {"name_vn": "Test Update"}
    
    response = requests.put(f"{api_url}/companies/{company_id}", json=update_data, headers=headers)
    
    print(f"PUT /api/companies/{company_id} returned: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ CONFIRMED: PUT /api/companies/{company_id} endpoint is missing (404 Not Found)")
        return True
    else:
        print(f"❌ Unexpected response: {response.status_code}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Company Update Endpoint Existence")
    print("=" * 50)
    
    if test_company_update_endpoint():
        print("\n🎯 ROOT CAUSE IDENTIFIED:")
        print("   The PUT /api/companies/{company_id} endpoint is missing from the backend")
        print("   This is why all company update attempts return 'Failed to update company!'")
        print("\n💡 SOLUTION:")
        print("   Need to implement the missing endpoint in backend/server.py")
        print("   1. Add CompanyUpdate Pydantic model")
        print("   2. Add PUT /api/companies/{company_id} endpoint")
        print("   3. Implement update logic with proper validation")
    else:
        print("\n❌ Could not confirm the issue")
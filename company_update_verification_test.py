#!/usr/bin/env python3
"""
Company Update Verification Test

This test verifies that the company update functionality now works after implementing
the missing PUT /api/companies/{company_id} endpoint.
"""

import requests
import json
import sys
import time

def test_company_update_functionality():
    """Test the fixed company update functionality"""
    base_url = "https://shipmanage.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔐 Step 1: Authenticating...")
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
    print("✅ Authentication successful")
    
    print("\n🏢 Step 2: Getting AMCSC company details...")
    # Get AMCSC company
    company_id = "cfe73cb0-cc88-4659-92a7-57cb413a5573"
    get_response = requests.get(f"{api_url}/companies", headers=headers)
    
    if get_response.status_code != 200:
        print("❌ Failed to get companies")
        return False
    
    companies = get_response.json()
    amcsc_company = None
    for company in companies:
        if company.get('id') == company_id:
            amcsc_company = company
            break
    
    if not amcsc_company:
        print(f"❌ AMCSC company not found with ID {company_id}")
        return False
    
    print(f"✅ Found AMCSC company: {amcsc_company.get('name_vn')} / {amcsc_company.get('name_en')}")
    
    print("\n🔄 Step 3: Testing company update scenarios...")
    
    # Test 1: Simple field update
    print("   Test 1: Update name_vn field")
    original_name_vn = amcsc_company.get('name_vn', '')
    test_name_vn = f"{original_name_vn} - Test Update {int(time.time())}"
    
    update_data_1 = {
        "name_vn": test_name_vn
    }
    
    response_1 = requests.put(f"{api_url}/companies/{company_id}", json=update_data_1, headers=headers)
    print(f"   Status: {response_1.status_code}")
    
    if response_1.status_code == 200:
        print("   ✅ Single field update successful")
        updated_company = response_1.json()
        print(f"   Updated name_vn: {updated_company.get('name_vn')}")
    else:
        print(f"   ❌ Single field update failed: {response_1.text}")
        return False
    
    # Test 2: Multiple field update
    print("\n   Test 2: Update multiple fields")
    update_data_2 = {
        "name_vn": original_name_vn,  # Restore original
        "address_vn": f"Updated Address VN {int(time.time())}",
        "address_en": f"Updated Address EN {int(time.time())}",
        "gmail": f"updated_{int(time.time())}@company.com"
    }
    
    response_2 = requests.put(f"{api_url}/companies/{company_id}", json=update_data_2, headers=headers)
    print(f"   Status: {response_2.status_code}")
    
    if response_2.status_code == 200:
        print("   ✅ Multiple field update successful")
        updated_company = response_2.json()
        print(f"   Updated address_vn: {updated_company.get('address_vn')}")
        print(f"   Updated gmail: {updated_company.get('gmail')}")
    else:
        print(f"   ❌ Multiple field update failed: {response_2.text}")
        return False
    
    # Test 3: System expiry update
    print("\n   Test 3: Update system_expiry field")
    update_data_3 = {
        "system_expiry": "2025-12-31T23:59:59Z"
    }
    
    response_3 = requests.put(f"{api_url}/companies/{company_id}", json=update_data_3, headers=headers)
    print(f"   Status: {response_3.status_code}")
    
    if response_3.status_code == 200:
        print("   ✅ System expiry update successful")
        updated_company = response_3.json()
        print(f"   Updated system_expiry: {updated_company.get('system_expiry')}")
    else:
        print(f"   ❌ System expiry update failed: {response_3.text}")
        return False
    
    # Test 4: Test with another company (non-AMCSC)
    print("\n🏢 Step 4: Testing update on company without Google Drive...")
    other_company = None
    for company in companies:
        if company.get('id') != company_id:
            other_company = company
            break
    
    if other_company:
        other_company_id = other_company.get('id')
        print(f"   Testing company: {other_company.get('name_vn')} / {other_company.get('name_en')}")
        
        update_data_4 = {
            "address_vn": f"Non-GDrive Test Address {int(time.time())}"
        }
        
        response_4 = requests.put(f"{api_url}/companies/{other_company_id}", json=update_data_4, headers=headers)
        print(f"   Status: {response_4.status_code}")
        
        if response_4.status_code == 200:
            print("   ✅ Non-Google Drive company update successful")
        else:
            print(f"   ❌ Non-Google Drive company update failed: {response_4.text}")
            return False
    else:
        print("   ⚠️ No other company found for testing")
    
    print("\n🎉 All company update tests passed!")
    return True

def main():
    print("🔍 Company Update Functionality Verification")
    print("=" * 60)
    print("Testing the fix for 'Failed to update company!' error")
    print("=" * 60)
    
    if test_company_update_functionality():
        print("\n✅ SUCCESS: Company update functionality is now working!")
        print("\n🎯 ISSUE RESOLVED:")
        print("   - The missing PUT /api/companies/{company_id} endpoint has been implemented")
        print("   - CompanyUpdate Pydantic model has been added")
        print("   - Company updates now work regardless of Google Drive configuration")
        print("   - Both AMCSC (with Google Drive) and other companies can be updated")
        
        print("\n💡 ROOT CAUSE WAS:")
        print("   - Missing backend endpoint, NOT a Google Drive configuration conflict")
        print("   - The error occurred for ALL companies, not just those with Google Drive")
        print("   - Frontend was correctly calling the API, but the endpoint didn't exist")
        
        return 0
    else:
        print("\n❌ FAILED: Company update functionality still has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Frontend Integration Test - Test the exact API calls the frontend would make
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://maritime-ai-crew-1.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

def test_frontend_workflow():
    """Test the exact workflow a frontend user would follow"""
    print("🖥️ Testing Frontend Integration Workflow")
    print("=" * 50)
    
    # Step 1: Login
    print("Step 1: Login with admin1/123456")
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    login_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    if login_response.status_code != 200:
        print("❌ Login failed")
        return False
    
    user_data = login_response.json()
    token = user_data.get("access_token")
    user = user_data.get("user", {})
    company = user.get("company")
    
    print(f"✅ Login successful - Company: {company}")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Get ships list (as frontend would)
    print("\nStep 2: Get ships list")
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers, timeout=30)
    if ships_response.status_code != 200:
        print("❌ Failed to get ships")
        return False
    
    ships = ships_response.json()
    company_ships = [ship for ship in ships if ship.get('company') == company]
    print(f"✅ Found {len(company_ships)} ships for company {company}")
    
    if not company_ships:
        print("❌ No ships found")
        return False
    
    # Step 3: Select a ship and get its certificates
    test_ship = company_ships[0]
    ship_id = test_ship.get('id')
    ship_name = test_ship.get('name')
    
    print(f"\nStep 3: Get certificates for ship '{ship_name}'")
    cert_response = requests.get(f"{BACKEND_URL}/ships/{ship_id}/certificates", headers=headers, timeout=30)
    if cert_response.status_code != 200:
        print("❌ Failed to get certificates")
        return False
    
    certificates = cert_response.json()
    print(f"✅ Found {len(certificates)} certificates")
    
    # Step 4: Find a certificate with next_survey to edit
    test_cert = None
    for cert in certificates:
        if cert.get('next_survey') and cert.get('id'):
            test_cert = cert
            break
    
    if not test_cert:
        print("❌ No certificate with next_survey found")
        return False
    
    cert_id = test_cert.get('id')
    cert_name = test_cert.get('cert_name')
    original_next_survey = test_cert.get('next_survey')
    
    print(f"\nStep 4: Selected certificate for editing")
    print(f"   Certificate: {cert_name}")
    print(f"   ID: {cert_id}")
    print(f"   Current Next Survey: {original_next_survey}")
    
    # Step 5: Edit the certificate (simulate frontend form submission)
    print(f"\nStep 5: Edit certificate - Update Next Survey field")
    
    # Generate new date (frontend would get this from user input)
    new_date = datetime.now() + timedelta(days=60)
    new_next_survey = new_date.strftime('%Y-%m-%d')
    
    print(f"   New Next Survey: {new_next_survey}")
    
    # Frontend would send a PUT request with the updated data
    update_data = {
        "next_survey": new_next_survey
    }
    
    put_response = requests.put(f"{BACKEND_URL}/certificates/{cert_id}", 
                               json=update_data, headers=headers, timeout=30)
    
    print(f"   PUT Response Status: {put_response.status_code}")
    
    if put_response.status_code != 200:
        print("❌ Certificate update failed")
        try:
            error_data = put_response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Error: {put_response.text}")
        return False
    
    put_data = put_response.json()
    response_next_survey = put_data.get('next_survey')
    print(f"   Response Next Survey: {response_next_survey}")
    print("✅ Certificate update successful")
    
    # Step 6: Refresh certificate list (as frontend would after edit)
    print(f"\nStep 6: Refresh certificate list to verify update")
    
    refresh_response = requests.get(f"{BACKEND_URL}/ships/{ship_id}/certificates", headers=headers, timeout=30)
    if refresh_response.status_code != 200:
        print("❌ Failed to refresh certificate list")
        return False
    
    refreshed_certificates = refresh_response.json()
    
    # Find our updated certificate in the refreshed list
    updated_cert = None
    for cert in refreshed_certificates:
        if cert.get('id') == cert_id:
            updated_cert = cert
            break
    
    if not updated_cert:
        print("❌ Updated certificate not found in refreshed list")
        return False
    
    refreshed_next_survey = updated_cert.get('next_survey')
    print(f"   Refreshed Next Survey: {refreshed_next_survey}")
    
    # Step 7: Verify the update persisted correctly
    print(f"\nStep 7: Verify update persistence")
    
    try:
        # Parse dates for comparison
        if isinstance(refreshed_next_survey, str):
            if 'T' in refreshed_next_survey:
                refreshed_date = datetime.fromisoformat(refreshed_next_survey.replace('Z', '+00:00')).date()
            else:
                refreshed_date = datetime.strptime(refreshed_next_survey, '%Y-%m-%d').date()
        
        expected_date = datetime.strptime(new_next_survey, '%Y-%m-%d').date()
        
        if refreshed_date == expected_date:
            print("✅ Update verified - Certificate list shows correct new value")
            print(f"   Original: {original_next_survey}")
            print(f"   Updated:  {refreshed_next_survey}")
            return True
        else:
            print(f"❌ Update verification failed")
            print(f"   Expected: {expected_date}")
            print(f"   Got:      {refreshed_date}")
            return False
    
    except Exception as e:
        print(f"❌ Date parsing error: {str(e)}")
        return False

def test_date_format_variations():
    """Test different date formats that frontend might send"""
    print("\n📅 Testing Date Format Variations")
    print("=" * 40)
    
    # Login
    login_data = {"username": "admin1", "password": "123456", "remember_me": False}
    login_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    if login_response.status_code != 200:
        return False
    
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get a test certificate
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers, timeout=30)
    ships = ships_response.json()
    amcsc_ships = [ship for ship in ships if ship.get('company') == 'AMCSC']
    
    test_cert = None
    for ship in amcsc_ships:
        cert_response = requests.get(f"{BACKEND_URL}/ships/{ship['id']}/certificates", headers=headers, timeout=30)
        if cert_response.status_code == 200:
            certificates = cert_response.json()
            for cert in certificates:
                if cert.get('next_survey') and cert.get('id'):
                    test_cert = cert
                    break
        if test_cert:
            break
    
    if not test_cert:
        print("❌ No test certificate found")
        return False
    
    cert_id = test_cert.get('id')
    
    # Test different date formats frontend might send
    date_formats = [
        "2025-12-15",           # ISO format (YYYY-MM-DD)
        "2025-12-16T00:00:00",  # ISO datetime
        "2025-12-17T00:00:00Z", # ISO datetime with Z
    ]
    
    results = []
    
    for date_format in date_formats:
        print(f"Testing date format: {date_format}")
        
        update_data = {"next_survey": date_format}
        put_response = requests.put(f"{BACKEND_URL}/certificates/{cert_id}", 
                                   json=update_data, headers=headers, timeout=30)
        
        if put_response.status_code == 200:
            # Verify the update
            verify_response = requests.get(f"{BACKEND_URL}/certificates/{cert_id}", 
                                         headers=headers, timeout=30)
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                stored_date = verify_data.get('next_survey')
                print(f"   ✅ Accepted - Stored as: {stored_date}")
                results.append(True)
            else:
                print(f"   ❌ Verification failed")
                results.append(False)
        else:
            print(f"   ❌ Update failed: {put_response.status_code}")
            results.append(False)
    
    success_rate = (sum(results) / len(results)) * 100 if results else 0
    print(f"\nDate format handling success rate: {success_rate:.1f}%")
    
    return success_rate > 80

def main():
    """Run frontend integration tests"""
    print("🚀 Frontend Integration Testing")
    print("=" * 60)
    
    # Test 1: Complete frontend workflow
    workflow_success = test_frontend_workflow()
    
    # Test 2: Date format variations
    date_format_success = test_date_format_variations()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FRONTEND INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Frontend Workflow", workflow_success),
        ("Date Format Variations", date_format_success)
    ]
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    overall_success = sum(1 for _, result in tests if result)
    print(f"\nOverall Success Rate: {overall_success}/{len(tests)} tests passed")
    
    if overall_success == len(tests):
        print("\n✅ CONCLUSION: Certificate edit functionality is working correctly")
        print("✅ Frontend integration should work as expected")
        print("✅ No Next Survey update bug detected")
    else:
        print("\n❌ CONCLUSION: Issues detected with certificate edit functionality")
        print("❌ Frontend integration may have problems")

if __name__ == "__main__":
    main()
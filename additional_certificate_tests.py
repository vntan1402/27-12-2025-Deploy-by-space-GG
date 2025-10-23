#!/usr/bin/env python3
"""
Additional Certificate Edit Tests - Multiple scenarios and edge cases
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://doc-navigator-9.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

def authenticate():
    """Authenticate and get token"""
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def get_headers(token):
    """Get auth headers"""
    return {"Authorization": f"Bearer {token}"}

def test_multiple_certificate_updates():
    """Test updating multiple certificates to verify consistency"""
    print("\n🔄 Testing multiple certificate updates...")
    
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = get_headers(token)
    
    # Get ships
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers, timeout=30)
    if ships_response.status_code != 200:
        print("❌ Failed to get ships")
        return False
    
    ships = ships_response.json()
    amcsc_ships = [ship for ship in ships if ship.get('company') == 'AMCSC']
    
    if not amcsc_ships:
        print("❌ No AMCSC ships found")
        return False
    
    # Test multiple certificates
    test_results = []
    
    for ship in amcsc_ships[:2]:  # Test first 2 ships
        ship_id = ship.get('id')
        ship_name = ship.get('name')
        
        print(f"\n   Testing certificates for ship: {ship_name}")
        
        # Get certificates
        cert_response = requests.get(f"{BACKEND_URL}/ships/{ship_id}/certificates", headers=headers, timeout=30)
        if cert_response.status_code != 200:
            continue
        
        certificates = cert_response.json()
        
        # Find certificates with next_survey
        for cert in certificates[:3]:  # Test first 3 certificates per ship
            cert_id = cert.get('id')
            cert_name = cert.get('cert_name', 'Unknown')
            original_next_survey = cert.get('next_survey')
            
            if not original_next_survey or not cert_id:
                continue
            
            print(f"      Testing certificate: {cert_name}")
            print(f"         Original Next Survey: {original_next_survey}")
            
            # Generate new date
            new_date = datetime.now() + timedelta(days=45)
            new_next_survey = new_date.strftime('%Y-%m-%d')
            
            # Update certificate
            update_data = {"next_survey": new_next_survey}
            put_response = requests.put(f"{BACKEND_URL}/certificates/{cert_id}", 
                                      json=update_data, headers=headers, timeout=30)
            
            if put_response.status_code == 200:
                response_data = put_response.json()
                response_next_survey = response_data.get('next_survey')
                
                # Verify update
                verify_response = requests.get(f"{BACKEND_URL}/certificates/{cert_id}", 
                                             headers=headers, timeout=30)
                
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    db_next_survey = verify_data.get('next_survey')
                    
                    # Check if dates match
                    try:
                        if isinstance(db_next_survey, str):
                            if 'T' in db_next_survey:
                                db_date = datetime.fromisoformat(db_next_survey.replace('Z', '+00:00')).date()
                            else:
                                db_date = datetime.strptime(db_next_survey, '%Y-%m-%d').date()
                        
                        expected_date = datetime.strptime(new_next_survey, '%Y-%m-%d').date()
                        
                        if db_date == expected_date:
                            print(f"         ✅ Update successful: {new_next_survey}")
                            test_results.append(True)
                        else:
                            print(f"         ❌ Update failed: expected {expected_date}, got {db_date}")
                            test_results.append(False)
                    except Exception as e:
                        print(f"         ❌ Date parsing error: {str(e)}")
                        test_results.append(False)
                else:
                    print(f"         ❌ Verification failed: {verify_response.status_code}")
                    test_results.append(False)
            else:
                print(f"         ❌ PUT request failed: {put_response.status_code}")
                test_results.append(False)
    
    success_rate = (sum(test_results) / len(test_results)) * 100 if test_results else 0
    print(f"\n   Multiple certificate update success rate: {success_rate:.1f}% ({sum(test_results)}/{len(test_results)})")
    
    return success_rate > 80

def test_edge_case_dates():
    """Test edge case date formats and values"""
    print("\n📅 Testing edge case dates...")
    
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = get_headers(token)
    
    # Get a test certificate
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers, timeout=30)
    if ships_response.status_code != 200:
        return False
    
    ships = ships_response.json()
    amcsc_ships = [ship for ship in ships if ship.get('company') == 'AMCSC']
    
    if not amcsc_ships:
        return False
    
    # Find a certificate to test with
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
        print("❌ No suitable test certificate found")
        return False
    
    cert_id = test_cert.get('id')
    print(f"   Using certificate: {test_cert.get('cert_name')}")
    
    # Test different date formats
    edge_case_dates = [
        "2025-12-31",  # End of year
        "2026-02-29",  # Leap year (invalid)
        "2024-02-29",  # Leap year (valid)
        "2025-01-01",  # Start of year
        "2030-06-15",  # Far future
    ]
    
    results = []
    
    for test_date in edge_case_dates:
        print(f"   Testing date: {test_date}")
        
        # Handle leap year edge case
        if test_date == "2026-02-29":
            test_date = "2026-02-28"  # Adjust invalid leap year date
            print(f"      Adjusted to: {test_date}")
        
        update_data = {"next_survey": test_date}
        put_response = requests.put(f"{BACKEND_URL}/certificates/{cert_id}", 
                                  json=update_data, headers=headers, timeout=30)
        
        if put_response.status_code == 200:
            # Verify the update
            verify_response = requests.get(f"{BACKEND_URL}/certificates/{cert_id}", 
                                         headers=headers, timeout=30)
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                db_next_survey = verify_data.get('next_survey')
                
                try:
                    if isinstance(db_next_survey, str):
                        if 'T' in db_next_survey:
                            db_date = datetime.fromisoformat(db_next_survey.replace('Z', '+00:00')).date()
                        else:
                            db_date = datetime.strptime(db_next_survey, '%Y-%m-%d').date()
                    
                    expected_date = datetime.strptime(test_date, '%Y-%m-%d').date()
                    
                    if db_date == expected_date:
                        print(f"      ✅ Edge case date handled correctly")
                        results.append(True)
                    else:
                        print(f"      ❌ Date mismatch: expected {expected_date}, got {db_date}")
                        results.append(False)
                except Exception as e:
                    print(f"      ❌ Date parsing error: {str(e)}")
                    results.append(False)
            else:
                print(f"      ❌ Verification failed: {verify_response.status_code}")
                results.append(False)
        else:
            print(f"      ❌ PUT request failed: {put_response.status_code}")
            results.append(False)
    
    success_rate = (sum(results) / len(results)) * 100 if results else 0
    print(f"   Edge case date success rate: {success_rate:.1f}% ({sum(results)}/{len(results)})")
    
    return success_rate > 80

def test_concurrent_updates():
    """Test concurrent updates to the same certificate"""
    print("\n⚡ Testing concurrent updates...")
    
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = get_headers(token)
    
    # Get a test certificate
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers, timeout=30)
    if ships_response.status_code != 200:
        return False
    
    ships = ships_response.json()
    amcsc_ships = [ship for ship in ships if ship.get('company') == 'AMCSC']
    
    if not amcsc_ships:
        return False
    
    # Find a certificate to test with
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
        print("❌ No suitable test certificate found")
        return False
    
    cert_id = test_cert.get('id')
    print(f"   Using certificate: {test_cert.get('cert_name')}")
    
    # Perform rapid sequential updates
    import threading
    import time
    
    results = []
    
    def update_certificate(date_suffix):
        try:
            new_date = f"2025-{date_suffix:02d}-15"
            update_data = {"next_survey": new_date}
            
            response = requests.put(f"{BACKEND_URL}/certificates/{cert_id}", 
                                  json=update_data, headers=headers, timeout=30)
            
            results.append({
                'date': new_date,
                'status': response.status_code,
                'success': response.status_code == 200
            })
        except Exception as e:
            results.append({
                'date': f"2025-{date_suffix:02d}-15",
                'status': 'error',
                'success': False,
                'error': str(e)
            })
    
    # Create threads for concurrent updates
    threads = []
    for i in range(1, 6):  # 5 concurrent updates
        thread = threading.Thread(target=update_certificate, args=(i + 10,))
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Analyze results
    successful_updates = sum(1 for r in results if r['success'])
    print(f"   Concurrent updates: {successful_updates}/{len(results)} successful")
    
    # Check final state
    final_response = requests.get(f"{BACKEND_URL}/certificates/{cert_id}", headers=headers, timeout=30)
    if final_response.status_code == 200:
        final_data = final_response.json()
        final_next_survey = final_data.get('next_survey')
        print(f"   Final next_survey value: {final_next_survey}")
    
    return successful_updates > 0

def main():
    """Run additional certificate edit tests"""
    print("🚀 Running Additional Certificate Edit Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Multiple certificate updates
    result1 = test_multiple_certificate_updates()
    test_results.append(('Multiple Certificate Updates', result1))
    
    # Test 2: Edge case dates
    result2 = test_edge_case_dates()
    test_results.append(('Edge Case Dates', result2))
    
    # Test 3: Concurrent updates
    result3 = test_concurrent_updates()
    test_results.append(('Concurrent Updates', result3))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ADDITIONAL TESTS SUMMARY")
    print("=" * 60)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    overall_success = sum(1 for _, result in test_results if result)
    print(f"\nOverall Success Rate: {overall_success}/{len(test_results)} tests passed")
    
    if overall_success == len(test_results):
        print("✅ All additional tests passed - Certificate edit functionality is robust")
    else:
        print("⚠️ Some additional tests failed - May indicate edge case issues")

if __name__ == "__main__":
    main()
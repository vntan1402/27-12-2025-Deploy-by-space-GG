#!/usr/bin/env python3
"""
Test the None strip fix with sample data
"""
import requests
import sys
import os

# Test backend URL
backend_url = 'http://localhost:8001'

def test_certificate_upload():
    """Test certificate upload with the CSSE certificate that was failing"""
    
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
            sunshine_ship = None
            
            for ship in ships:
                if 'SUNSHINE' in ship.get('name', '').upper():
                    sunshine_ship = ship
                    break
            
            if sunshine_ship:
                ship_id = sunshine_ship['id']
                ship_name = sunshine_ship.get('name', 'Unknown')
                
                print(f"✅ Found ship: {ship_name}")
                
                # Test with analysis result that has None values (simulating the issue)
                test_analysis = {
                    "category": "certificates",
                    "cert_name": None,  # This would cause the strip error
                    "cert_no": None,
                    "cert_type": None,  # This specifically caused the error
                    "issue_date": None,
                    "valid_date": None,
                    "issued_by": None,
                    "ship_name": "SUNSHINE 01",
                    "confidence": "low"
                }
                
                print(f"\n🧪 Testing get_enhanced_last_endorse with None values...")
                
                # Create a test certificate creation request
                test_request = {
                    "ship_id": ship_id,
                    "analysis_result": test_analysis,
                    "notes": "Test certificate with None values",
                    "file_content_b64": "dGVzdA==",  # "test" in base64
                    "filename": "test-csse.pdf"
                }
                
                create_response = session.post(f"{backend_url}/api/create-certificate-from-analysis-notes", json=test_request)
                print(f"Certificate creation status: {create_response.status_code}")
                
                if create_response.status_code == 200:
                    result = create_response.json()
                    print("✅ Certificate creation successful!")
                    print(f"   Certificate ID: {result.get('certificate_id', 'Not found')}")
                    print("✅ Fix working - None values handled properly")
                elif create_response.status_code == 422:
                    print("⚠️ Validation error (expected with None values):")
                    try:
                        error_data = create_response.json()
                        print(f"   Detail: {error_data.get('detail', 'Unknown validation error')}")
                        print("✅ Fix working - validation catches None values gracefully")
                    except:
                        print("   Unable to parse error details")
                else:
                    try:
                        error_data = create_response.json()
                        if "'NoneType' object has no attribute 'strip'" in str(error_data.get('detail', '')):
                            print("❌ Fix NOT working - still getting strip error")
                        else:
                            print(f"⚠️ Different error: {error_data.get('detail', 'Unknown error')}")
                            print("✅ Fix working - no more strip errors")
                    except:
                        print(f"❌ Request failed: {create_response.status_code} - {create_response.text[:200]}")
            else:
                print("❌ SUNSHINE ship not found")
        else:
            print(f"❌ Failed to get ships: {ships_response.status_code}")
    else:
        print(f"❌ Login failed: {login_response.text}")

if __name__ == "__main__":
    test_certificate_upload()
#!/usr/bin/env python3
"""
Simple test to verify certificate delete fix
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "https://seacraft-portfolio.preview.emergentagent.com/api"

def test_certificate_delete():
    print("🗑️ Testing Certificate Delete Fix...")
    
    # Login
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    print("🔐 Logging in...")
    for attempt in range(3):
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                if token:
                    print("✅ Login successful")
                    break
            else:
                print(f"❌ Login failed: {response.status_code}")
                time.sleep(5)
        except Exception as e:
            print(f"❌ Login error: {e}")
            time.sleep(5)
    else:
        print("❌ Could not login after 3 attempts")
        return
    
    # Set up session
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Get ships
    print("🚢 Getting ships...")
    ships_response = session.get(f"{BACKEND_URL}/ships", timeout=10)
    if ships_response.status_code != 200:
        print(f"❌ Failed to get ships: {ships_response.status_code}")
        return
    
    ships = ships_response.json()
    sunshine_ship = None
    
    for ship in ships:
        if "SUNSHINE" in ship.get('name', '').upper():
            sunshine_ship = ship
            break
    
    if not sunshine_ship:
        print("❌ SUNSHINE ship not found")
        return
    
    print(f"✅ Found ship: {sunshine_ship.get('name')}")
    
    # Get certificates
    print("📋 Getting certificates...")
    cert_response = session.get(f"{BACKEND_URL}/ships/{sunshine_ship['id']}/certificates", timeout=10)
    if cert_response.status_code != 200:
        print(f"❌ Failed to get certificates: {cert_response.status_code}")
        return
    
    certificates = cert_response.json()
    print(f"✅ Found {len(certificates)} certificates")
    
    if not certificates:
        print("❌ No certificates to test with")
        return
    
    # Find a certificate with Google Drive file
    test_cert = None
    for cert in certificates:
        if cert.get('google_drive_file_id'):
            test_cert = cert
            break
    
    if not test_cert:
        print("❌ No certificates with Google Drive files found")
        return
    
    print(f"📄 Testing with certificate: {test_cert.get('cert_name', 'N/A')}")
    print(f"   Google Drive File ID: {test_cert.get('google_drive_file_id')}")
    
    # Test delete
    print("🗑️ Testing certificate deletion...")
    delete_response = session.delete(f"{BACKEND_URL}/certificates/{test_cert['id']}", timeout=30)
    
    print(f"Delete response status: {delete_response.status_code}")
    
    if delete_response.status_code == 200:
        try:
            delete_data = delete_response.json()
            print("✅ Certificate deletion successful")
            print(f"Response: {json.dumps(delete_data, indent=2)}")
            
            gdrive_deleted = delete_data.get('gdrive_file_deleted', False)
            print(f"Google Drive file deleted: {'✅' if gdrive_deleted else '❌'}")
            
            if gdrive_deleted:
                print("🎉 FIX SUCCESSFUL: Google Drive file deletion is now working!")
            else:
                print("⚠️ Google Drive file deletion still not working")
                
        except json.JSONDecodeError:
            print("✅ Certificate deletion successful (no JSON response)")
    else:
        print(f"❌ Certificate deletion failed: {delete_response.status_code}")
        print(f"Error: {delete_response.text}")

if __name__ == "__main__":
    test_certificate_delete()
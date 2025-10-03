#!/usr/bin/env python3
"""
Auto Rename Debug - Debug the actual Auto Rename File process step by step
"""

import requests
import json
import os

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vesseldocs.preview.emergentagent.com') + '/api'

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
        return data.get("access_token")
    return None

def get_headers(token):
    """Get authentication headers"""
    return {"Authorization": f"Bearer {token}"}

def debug_auto_rename_process():
    """Debug the auto rename process step by step"""
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = get_headers(token)
    
    # Test with a specific LL certificate that should use abbreviation
    cert_id = "41440429-2673-4c2d-afd2-f5c5c922f650"  # This one worked correctly
    
    print(f"🔍 Debugging Auto Rename process for certificate: {cert_id}")
    
    # Step 1: Get certificate details directly
    print(f"\n📋 STEP 1: Get certificate details")
    cert_response = requests.get(f"{BACKEND_URL}/certificates/{cert_id}", headers=headers, timeout=30)
    
    if cert_response.status_code == 200:
        cert = cert_response.json()
        print(f"   ✅ Certificate retrieved successfully")
        print(f"   Certificate Name: '{cert.get('cert_name', 'N/A')}'")
        print(f"   Certificate Abbreviation: '{cert.get('cert_abbreviation', 'N/A')}'")
        print(f"   Certificate Type: '{cert.get('cert_type', 'N/A')}'")
        print(f"   Ship ID: '{cert.get('ship_id', 'N/A')}'")
        print(f"   Google Drive File ID: '{cert.get('google_drive_file_id', 'N/A')}'")
    else:
        print(f"   ❌ Failed to get certificate: {cert_response.status_code}")
        return
    
    # Step 2: Get ship details
    ship_id = cert.get('ship_id')
    print(f"\n🚢 STEP 2: Get ship details for ID: {ship_id}")
    ship_response = requests.get(f"{BACKEND_URL}/ships/{ship_id}", headers=headers, timeout=30)
    
    if ship_response.status_code == 200:
        ship = ship_response.json()
        print(f"   ✅ Ship retrieved successfully")
        print(f"   Ship Name: '{ship.get('name', 'N/A')}'")
        print(f"   Ship IMO: '{ship.get('imo', 'N/A')}'")
    else:
        print(f"   ❌ Failed to get ship: {ship_response.status_code}")
        return
    
    # Step 3: Simulate the filename generation logic
    print(f"\n🔧 STEP 3: Simulate filename generation logic")
    
    ship_name = ship.get("name", "Unknown Ship").replace(" ", "_")
    cert_type = cert.get("cert_type", "Unknown Type").replace(" ", "_")
    cert_abbreviation = cert.get("cert_abbreviation", "")
    cert_name = cert.get("cert_name", "Unknown Certificate").replace(" ", "_")
    issue_date = cert.get("issue_date")
    
    print(f"   ship_name: '{ship_name}'")
    print(f"   cert_type: '{cert_type}'")
    print(f"   cert_abbreviation: '{cert_abbreviation}'")
    print(f"   cert_name: '{cert_name}'")
    print(f"   issue_date: '{issue_date}'")
    
    # Use abbreviation if available, otherwise use cert name
    cert_identifier = cert_abbreviation if cert_abbreviation else cert_name
    cert_identifier = cert_identifier.replace(" ", "_")
    
    print(f"   cert_identifier (final): '{cert_identifier}'")
    print(f"   Logic: {'Using abbreviation' if cert_abbreviation else 'Using full name'}")
    
    # Format issue date
    date_str = ""
    if issue_date:
        try:
            from datetime import datetime
            if isinstance(issue_date, str):
                if 'T' in issue_date:
                    parsed_date = datetime.fromisoformat(issue_date.replace('Z', '+00:00'))
                else:
                    parsed_date = datetime.strptime(issue_date, '%Y-%m-%d')
                date_str = parsed_date.strftime('%Y%m%d')
            else:
                date_str = "NoDate"
        except:
            date_str = "NoDate"
    else:
        date_str = "NoDate"
    
    print(f"   date_str: '{date_str}'")
    
    # Build new filename
    file_extension = ".pdf"
    new_filename = f"{ship_name}_{cert_type}_{cert_identifier}_{date_str}{file_extension}"
    
    print(f"   Expected filename: '{new_filename}'")
    
    # Step 4: Actually call the auto rename endpoint
    print(f"\n🔄 STEP 4: Call Auto Rename endpoint")
    rename_response = requests.post(f"{BACKEND_URL}/certificates/{cert_id}/auto-rename-file", headers=headers, timeout=30)
    
    if rename_response.status_code == 200:
        rename_data = rename_response.json()
        print(f"   ✅ Auto rename successful")
        print(f"   Actual new filename: '{rename_data.get('new_name', 'N/A')}'")
        print(f"   Naming convention used:")
        naming_conv = rename_data.get('naming_convention', {})
        print(f"      ship_name: '{naming_conv.get('ship_name', 'N/A')}'")
        print(f"      cert_type: '{naming_conv.get('cert_type', 'N/A')}'")
        print(f"      cert_identifier: '{naming_conv.get('cert_identifier', 'N/A')}'")
        print(f"      issue_date: '{naming_conv.get('issue_date', 'N/A')}'")
        
        # Compare expected vs actual
        expected_cert_identifier = cert_abbreviation if cert_abbreviation else cert_name.replace(" ", "_")
        actual_cert_identifier = naming_conv.get('cert_identifier', '')
        
        print(f"\n🔍 COMPARISON:")
        print(f"   Expected cert_identifier: '{expected_cert_identifier}'")
        print(f"   Actual cert_identifier: '{actual_cert_identifier}'")
        
        if expected_cert_identifier == actual_cert_identifier:
            print(f"   ✅ MATCH: Logic working correctly")
        else:
            print(f"   ❌ MISMATCH: Logic not working as expected")
            
    else:
        print(f"   ❌ Auto rename failed: {rename_response.status_code}")
        try:
            error_data = rename_response.json()
            print(f"      Error: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"      Error: {rename_response.text[:200]}")

if __name__ == "__main__":
    debug_auto_rename_process()
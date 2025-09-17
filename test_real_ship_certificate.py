#!/usr/bin/env python3
"""
Test certificate upload with real ship name
"""

import requests
import sys
import json
import io
from datetime import datetime

def test_with_real_ship():
    """Test certificate upload with existing ship name"""
    
    # Login
    login_response = requests.post('https://shipwise-13.preview.emergentagent.com/api/auth/login', 
                                  json={'username': 'admin', 'password': 'admin123'})
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get existing ships
    ships_response = requests.get('https://shipwise-13.preview.emergentagent.com/api/ships', headers=headers)
    ships = ships_response.json()
    
    if not ships:
        print("No ships found")
        return
    
    # Use the first ship
    ship = ships[0]
    ship_name = ship['name']
    ship_id = ship['id']
    
    print(f"Using ship: {ship_name} (ID: {ship_id})")
    
    # Create certificate content with the real ship name
    certificate_content = f"""
INTERNATIONAL AIR POLLUTION PREVENTION CERTIFICATE

Ship Name: {ship_name}
IMO Number: IMO1234567
Flag State: Panama
Classification Society: DNV GL

Certificate Number: IAPP-2024-001
Issue Date: 01 January 2024
Valid Until: 01 January 2027

This is to certify that this ship has been surveyed in accordance with 
regulation 5 of Annex VI to the International Convention for the Prevention 
of Pollution from Ships, 1973, as modified by the Protocol of 1978 relating 
thereto, and that the survey showed that the structure, equipment, systems, 
fittings, arrangements and material of the ship and the condition thereof 
are in all respects satisfactory.

Issued by: Panama Maritime Authority
On behalf of the Government of Panama

Authorized Officer: Captain John Smith
Date: 01 January 2024
Place: Panama City

This certificate is valid until 01 January 2027 subject to surveys 
in accordance with the Convention.
"""
    
    # Upload the certificate
    files = {
        'files': (f'{ship_name}_certificate.pdf', io.BytesIO(certificate_content.encode('utf-8')), 'application/pdf')
    }
    
    print(f"Uploading certificate for {ship_name}...")
    
    upload_response = requests.post(
        'https://shipwise-13.preview.emergentagent.com/api/certificates/upload-multi-files',
        files=files,
        headers={'Authorization': f'Bearer {token}'},
        timeout=120
    )
    
    if upload_response.status_code == 200:
        result = upload_response.json()
        print("Upload successful!")
        
        for file_result in result.get('results', []):
            print(f"\n--- Results for {file_result.get('filename')} ---")
            print(f"Status: {file_result.get('status')}")
            
            if file_result.get('status') == 'success':
                analysis = file_result.get('analysis', {})
                print(f"AI Analysis:")
                print(f"  Category: {analysis.get('category')}")
                print(f"  Ship Name: {analysis.get('ship_name')}")
                print(f"  Cert Name: {analysis.get('cert_name')}")
                
                upload = file_result.get('upload', {})
                print(f"Google Drive Upload:")
                print(f"  Success: {upload.get('success')}")
                if upload.get('success'):
                    print(f"  File ID: {upload.get('file_id')}")
                    print(f"  Folder Path: {upload.get('folder_path')}")
                else:
                    print(f"  Error: {upload.get('error')}")
                
                certificate = file_result.get('certificate', {})
                print(f"Certificate Record:")
                if certificate and isinstance(certificate, dict):
                    if certificate.get('success', False) or certificate.get('id'):
                        print(f"  Success: True")
                        print(f"  Certificate ID: {certificate.get('id')}")
                    else:
                        print(f"  Success: False")
                        print(f"  Error: {certificate.get('error', 'Unknown error')}")
                else:
                    print(f"  Success: False")
                    print(f"  Certificate data: {certificate}")
            else:
                print(f"Upload failed: {file_result.get('message')}")
    else:
        print(f"Upload failed with status {upload_response.status_code}")
        print(upload_response.text)

if __name__ == "__main__":
    test_with_real_ship()
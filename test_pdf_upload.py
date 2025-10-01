#!/usr/bin/env python3
"""
Test PDF Upload for Ship Name Extraction
Create a simple PDF and test the AI analysis
"""

import requests
import json
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nautical-certs-1.preview.emergentagent.com') + '/api'

def create_test_pdf():
    """Create a simple PDF with ship certificate content"""
    # Create temporary PDF file
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_file.close()
    
    # Create PDF content
    c = canvas.Canvas(temp_file.name, pagesize=letter)
    width, height = letter
    
    # Add certificate content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE")
    
    c.setFont("Helvetica", 12)
    y = height - 150
    
    lines = [
        "This is to certify that the ship SUNSHINE 01 has been surveyed",
        "in accordance with the provisions of the International Convention",
        "for the Safety of Life at Sea, 1974, as amended.",
        "",
        "Ship Name: SUNSHINE 01",
        "IMO Number: 9415313",
        "Port of Registry: BELIZE",
        "Flag State: BELIZE",
        "Classification Society: PANAMA MARITIME DOCUMENTATION SERVICES (PMDS)",
        "",
        "Certificate Number: TEST-CSSC-2025-001",
        "Issue Date: 15/01/2024",
        "Valid Until: 10/03/2026",
        "Last Endorsed: 15/06/2024",
        "",
        "This certificate is issued under the authority of the Government of BELIZE.",
        "The ship SUNSHINE 01 complies with the relevant requirements of the Convention."
    ]
    
    for line in lines:
        c.drawString(100, y, line)
        y -= 20
    
    c.save()
    return temp_file.name

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

def main():
    print("🔍 Testing PDF Upload for Ship Name Extraction...")
    
    # Authenticate
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Find SUNSHINE 01 ship
    response = requests.get(f"{BACKEND_URL}/ships", headers=get_headers(token), timeout=30)
    if response.status_code != 200:
        print("❌ Failed to get ships")
        return
    
    ships = response.json()
    sunshine_ship = None
    
    for ship in ships:
        if 'SUNSHINE 01' in ship.get('name', '').upper():
            sunshine_ship = ship
            break
    
    if not sunshine_ship:
        print("❌ SUNSHINE 01 ship not found")
        return
    
    ship_id = sunshine_ship.get('id')
    print(f"✅ Found SUNSHINE 01 ship: {ship_id}")
    
    # Create test PDF
    print("📄 Creating test PDF with ship name content...")
    pdf_path = create_test_pdf()
    
    try:
        # Upload the PDF
        print("📤 Uploading test PDF certificate...")
        
        endpoint = f"{BACKEND_URL}/certificates/multi-upload?ship_id={ship_id}"
        
        with open(pdf_path, 'rb') as file:
            files = {'files': ('test_certificate.pdf', file, 'application/pdf')}
            data = {
                'category': 'certificates',
                'sensitivity_level': 'public'
            }
            
            response = requests.post(
                endpoint,
                files=files,
                data=data,
                headers=get_headers(token),
                timeout=120  # AI analysis can take time
            )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ Certificate upload successful")
            
            # Log the full response for analysis
            print("📋 AI Analysis Response:")
            print(json.dumps(response_data, indent=2))
            
            # Check if AI extracted ship name
            results = response_data.get('results', [])
            if results:
                first_result = results[0]
                
                if first_result.get('status') == 'success':
                    print("✅ Certificate created successfully")
                    
                    # Check for extracted ship name
                    extracted_ship_name = first_result.get('extracted_ship_name')
                    analysis_result = first_result.get('analysis_result', {})
                    ship_name_from_analysis = analysis_result.get('ship_name')
                    
                    print(f"🔍 Ship Name Extraction Results:")
                    print(f"   ship_name in analysis_result: {ship_name_from_analysis}")
                    print(f"   extracted_ship_name in certificate: {extracted_ship_name}")
                    
                    if extracted_ship_name:
                        print("🎉 SUCCESS: extracted_ship_name field is populated!")
                        print(f"   Value: {extracted_ship_name}")
                        print("   This should fix the tooltip issue for new certificates")
                    else:
                        print("❌ ISSUE: extracted_ship_name field is still missing")
                        
                        if ship_name_from_analysis:
                            print("   AI extracted ship name but field was not saved to certificate")
                            print("   This indicates a backend issue in certificate creation")
                        else:
                            print("   AI did not extract ship name from PDF content")
                            print("   This indicates an AI analysis issue")
                else:
                    print(f"❌ Certificate creation failed: {first_result.get('message')}")
                    
        else:
            print(f"❌ Certificate upload failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error: {response.text[:500]}")
                
    finally:
        # Clean up temporary file
        try:
            os.unlink(pdf_path)
        except:
            pass

if __name__ == "__main__":
    main()
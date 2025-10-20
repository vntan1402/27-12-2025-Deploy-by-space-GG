#!/usr/bin/env python3
"""
Test DOB validation with PDF file
"""

import requests
import json
import tempfile
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Configuration
BACKEND_URL = 'https://nautical-crew-hub.preview.emergentagent.com/api'

def authenticate():
    """Authenticate and return session"""
    session = requests.Session()
    
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        return session, data.get("user", {})
    return None, None

def create_pdf_certificate(holder_name, dob):
    """Create a PDF certificate with specific DOB"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_file.close()
    
    # Create PDF
    c = canvas.Canvas(temp_file.name, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "CERTIFICATE OF COMPETENCY")
    
    # Content
    c.setFont("Helvetica", 12)
    y = height - 150
    
    lines = [
        f"This is to certify that {holder_name}",
        "has been found competent to perform duties as specified.",
        "",
        f"Certificate Number: COC-TEST-{int(datetime.now().timestamp())}",
        "Issued By: Test Maritime Authority",
        f"Issue Date: {datetime.now().strftime('%d/%m/%Y')}",
        f"Expiry Date: {datetime.now().strftime('%d/%m/%Y')}",
        "",
        f"Date of Birth: {dob}",
        "",
        "This certificate is valid for all vessels.",
        "",
        "Signed: Test Authority",
        f"Date: {datetime.now().strftime('%d/%m/%Y')}"
    ]
    
    for line in lines:
        c.drawString(100, y, line)
        y -= 20
    
    c.save()
    return temp_file.name

def test_dob_with_pdf():
    """Test DOB validation with PDF files"""
    print("🔍 DEBUG: DOB Validation Test with PDF")
    print("=" * 50)
    
    # Authenticate
    session, user = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    print(f"✅ Authenticated as: {user.get('username')}")
    
    # Get crew with DOB
    crew_response = session.get(f"{BACKEND_URL}/crew")
    if crew_response.status_code != 200:
        print("❌ Failed to get crew list")
        return
    
    crew_list = crew_response.json()
    crew_with_dob = None
    
    for crew in crew_list:
        if crew.get("date_of_birth"):
            crew_with_dob = crew
            break
    
    if not crew_with_dob:
        print("❌ No crew with DOB found")
        return
    
    print(f"✅ Found crew with DOB: {crew_with_dob.get('full_name')}")
    print(f"   Crew DOB: {crew_with_dob.get('date_of_birth')}")
    
    # Get ships
    ships_response = session.get(f"{BACKEND_URL}/ships")
    if ships_response.status_code != 200:
        print("❌ Failed to get ships")
        return
    
    ships = ships_response.json()
    test_ship = None
    for ship in ships:
        if ship.get("name") in ["BROTHER 36", "MINH ANH 09"]:
            test_ship = ship
            break
    
    if not test_ship:
        print("❌ No test ship found")
        return
    
    print(f"✅ Found test ship: {test_ship.get('name')}")
    
    # Test with MISMATCHED DOB in PDF
    print("\n🧪 TEST: PDF Certificate with MISMATCHED DOB")
    cert_dob_mismatch = "01/01/1990"  # Different DOB
    print(f"   Using DOB in certificate: {cert_dob_mismatch}")
    
    try:
        pdf_file = create_pdf_certificate(
            crew_with_dob.get('full_name'), 
            cert_dob_mismatch
        )
        
        with open(pdf_file, "rb") as f:
            files = {"cert_file": ("test_cert.pdf", f, "application/pdf")}
            data = {
                "ship_id": test_ship.get("id"),
                "crew_id": crew_with_dob.get("id")
            }
            
            response = session.post(
                f"{BACKEND_URL}/crew-certificates/analyze-file",
                files=files,
                data=data,
                timeout=120
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 400:
                result = response.json()
                print("   ✅ SUCCESS - DOB mismatch detected correctly")
                print(f"   Error: {result.get('detail', {}).get('error', 'Unknown')}")
                print(f"   AI DOB: {result.get('detail', {}).get('ai_extracted_dob', 'Unknown')}")
                print(f"   Crew DOB: {result.get('detail', {}).get('crew_dob', 'Unknown')}")
            elif response.status_code == 200:
                result = response.json()
                print("   ❌ FAILED - Expected 400 but got 200")
                print(f"   AI extracted DOB: {result.get('date_of_birth', 'NOT FOUND')}")
                print("   This suggests DOB validation is not working or AI didn't extract from PDF")
            else:
                print(f"   ❌ UNEXPECTED - {response.text}")
    
    finally:
        import os
        try:
            os.unlink(pdf_file)
        except:
            pass

if __name__ == "__main__":
    test_dob_with_pdf()
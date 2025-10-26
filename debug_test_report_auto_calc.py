#!/usr/bin/env python3
"""
Debug Test Report Auto-Calculation - Check what's happening with the auto-calc feature
"""

import requests
import json
import tempfile
import os

# Use external backend URL
BACKEND_URL = "https://shipsystem.preview.emergentagent.com/api"

def create_simple_test_pdf():
    """Create a simple PDF without valid_date to trigger auto-calculation"""
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 150
>>
stream
BT
/F1 12 Tf
72 720 Td
(Chemical Suit Test Report) Tj
0 -20 Td
(Test Report No: CS-2024-DEBUG) Tj
0 -20 Td
(Issued Date: 15/01/2024) Tj
0 -20 Td
(Issued By: VITECH) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
406
%%EOF"""
    return pdf_content

def main():
    # Authenticate
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"Authentication failed: {response.status_code}")
        return
    
    auth_token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create test PDF
    pdf_content = create_simple_test_pdf()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(pdf_content)
        temp_file_path = temp_file.name
    
    try:
        # Upload test report
        with open(temp_file_path, "rb") as f:
            files = {
                "test_report_file": ("Debug_Chemical_Suit.pdf", f, "application/pdf")
            }
            data = {
                "ship_id": "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7",
                "bypass_validation": "false"
            }
            
            print("Uploading debug test report...")
            response = requests.post(
                f"{BACKEND_URL}/test-reports/analyze-file",
                files=files,
                data=data,
                headers=headers,
                timeout=120
            )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\nResponse fields:")
            for key, value in result.items():
                if not key.startswith('_'):  # Skip internal fields
                    print(f"  {key}: {value}")
            
            # Check if auto-calculation was triggered
            valid_date = result.get("valid_date")
            issued_date = result.get("issued_date")
            test_report_name = result.get("test_report_name")
            
            print(f"\nAuto-calculation analysis:")
            print(f"  AI extracted valid_date: {bool(valid_date)}")
            print(f"  AI extracted issued_date: {bool(issued_date)}")
            print(f"  AI extracted test_report_name: {bool(test_report_name)}")
            print(f"  Should trigger auto-calc: {not valid_date and bool(issued_date) and bool(test_report_name)}")
            
        else:
            print(f"Request failed: {response.text}")
            
    finally:
        # Clean up
        os.unlink(temp_file_path)

if __name__ == "__main__":
    main()
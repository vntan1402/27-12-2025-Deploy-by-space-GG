#!/usr/bin/env python3
"""
Test Auto-Calculation with proper issued_date format
"""

import requests
import json
import tempfile
import os
from datetime import datetime

# Use external backend URL
BACKEND_URL = "https://shipdoclists.preview.emergentagent.com/api"

def create_test_pdf_with_proper_date():
    """Create a PDF with proper date format that AI should extract"""
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
/Parent 2 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
72 720 Td
(CHEMICAL SUIT TEST REPORT) Tj
0 -20 Td
(Test Report Number: CS-2024-001) Tj
0 -20 Td
(Issue Date: January 15, 2024) Tj
0 -20 Td
(Issued Date: 15/01/2024) Tj
0 -20 Td
(Issued By: VITECH Marine Services) Tj
0 -20 Td
(Equipment: Chemical Protective Suit) Tj
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
456
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
    
    # Create test PDF with proper date format
    pdf_content = create_test_pdf_with_proper_date()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(pdf_content)
        temp_file_path = temp_file.name
    
    try:
        # Upload test report
        with open(temp_file_path, "rb") as f:
            files = {
                "test_report_file": ("Chemical_Suit_With_Date.pdf", f, "application/pdf")
            }
            data = {
                "ship_id": "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7",
                "bypass_validation": "false"
            }
            
            print("Uploading test report with proper date format...")
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
            print("\nExtracted fields:")
            print(f"  test_report_name: '{result.get('test_report_name', '')}'")
            print(f"  issued_date: '{result.get('issued_date', '')}'")
            print(f"  valid_date: '{result.get('valid_date', '')}'")
            print(f"  status: '{result.get('status', '')}'")
            print(f"  confidence_score: {result.get('confidence_score', 0)}")
            
            # Check if auto-calculation should have been triggered
            valid_date = result.get("valid_date")
            issued_date = result.get("issued_date")
            test_report_name = result.get("test_report_name")
            
            print(f"\nAuto-calculation analysis:")
            print(f"  AI extracted valid_date: {bool(valid_date)} ('{valid_date}')")
            print(f"  AI extracted issued_date: {bool(issued_date)} ('{issued_date}')")
            print(f"  AI extracted test_report_name: {bool(test_report_name)} ('{test_report_name}')")
            
            should_trigger = not valid_date and bool(issued_date) and bool(test_report_name)
            print(f"  Should trigger auto-calc: {should_trigger}")
            
            if should_trigger:
                print("  ✅ Auto-calculation should have been triggered!")
                if valid_date:
                    print(f"  ✅ Valid date was calculated: {valid_date}")
                else:
                    print("  ❌ Valid date was NOT calculated - check backend logs")
            else:
                if valid_date:
                    print("  ✅ AI extracted valid_date, auto-calc correctly skipped")
                else:
                    print("  ❌ Missing required fields for auto-calculation")
            
        else:
            print(f"Request failed: {response.text}")
            
    finally:
        # Clean up
        os.unlink(temp_file_path)

if __name__ == "__main__":
    main()
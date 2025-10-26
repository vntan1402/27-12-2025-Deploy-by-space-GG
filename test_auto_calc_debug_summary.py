#!/usr/bin/env python3
"""
Debug Auto-Calculation - Check what AI sees in summary text
"""

import requests
import json
import tempfile
import os

# Use external backend URL
BACKEND_URL = "https://shipsystem.preview.emergentagent.com/api"

def create_minimal_test_pdf():
    """Create a minimal PDF to see what AI extracts"""
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
/Length 120
>>
stream
BT
/F1 12 Tf
72 720 Td
(Life Raft Test Report) Tj
0 -20 Td
(Issued: 10/02/2024) Tj
0 -20 Td
(Equipment: Life Raft) Tj
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
376
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
    
    # Create minimal test PDF
    pdf_content = create_minimal_test_pdf()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(pdf_content)
        temp_file_path = temp_file.name
    
    try:
        # Upload test report
        with open(temp_file_path, "rb") as f:
            files = {
                "test_report_file": ("Life_Raft_Minimal.pdf", f, "application/pdf")
            }
            data = {
                "ship_id": "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7",
                "bypass_validation": "false"
            }
            
            print("Uploading minimal Life Raft test report...")
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
            
            # Print all fields including internal ones
            print("\nFull response:")
            for key, value in result.items():
                if key == '_summary_text':
                    print(f"  {key}: '{value[:200]}...' (truncated)")
                else:
                    print(f"  {key}: {value}")
            
            # Check auto-calculation conditions
            valid_date = result.get("valid_date")
            issued_date = result.get("issued_date")
            test_report_name = result.get("test_report_name")
            
            print(f"\nAuto-calculation conditions:")
            print(f"  valid_date extracted: {bool(valid_date)} ('{valid_date}')")
            print(f"  issued_date extracted: {bool(issued_date)} ('{issued_date}')")
            print(f"  test_report_name extracted: {bool(test_report_name)} ('{test_report_name}')")
            
            should_auto_calc = not valid_date and bool(issued_date) and bool(test_report_name)
            print(f"  Should auto-calculate: {should_auto_calc}")
            
            if should_auto_calc:
                print("  🎯 This should trigger auto-calculation!")
                print("  Expected: Life Raft → 12 months from issued_date")
                if issued_date:
                    from datetime import datetime, timedelta
                    try:
                        issued_dt = datetime.strptime(issued_date, "%Y-%m-%d")
                        expected_valid = issued_dt + timedelta(days=365)  # 12 months
                        print(f"  Expected valid_date: {expected_valid.strftime('%Y-%m-%d')}")
                    except:
                        print("  Could not calculate expected date")
            
        else:
            print(f"Request failed: {response.text}")
            
    finally:
        # Clean up
        os.unlink(temp_file_path)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Simple PDF test to check the actual response structure
"""

import requests
import json
import io

# Configuration
API_BASE = "http://127.0.0.1:8001/api"
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

def authenticate():
    """Authenticate and get token"""
    response = requests.post(f"{API_BASE}/auth/login", json={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    else:
        print(f"Authentication failed: {response.status_code} - {response.text}")
        return None

def test_pdf_endpoint():
    """Test the PDF endpoint with a simple PDF"""
    token = authenticate()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a simple PDF content
    simple_pdf = b"""%PDF-1.4
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
/Length 100
>>
stream
BT
/F1 12 Tf
72 720 Td
(SHIP NAME: SUNSHINE STAR) Tj
0 -20 Td
(IMO NUMBER: 9405136) Tj
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
350
%%EOF"""
    
    files = {
        'file': ('test.pdf', io.BytesIO(simple_pdf), 'application/pdf')
    }
    
    print("Testing PDF endpoint...")
    response = requests.post(
        f"{API_BASE}/analyze-ship-certificate",
        files=files,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Content: {response.text}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"JSON Response: {json.dumps(data, indent=2)}")
        except:
            print("Response is not valid JSON")

def test_non_pdf_rejection():
    """Test non-PDF file rejection"""
    token = authenticate()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a PNG file
    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    
    files = {
        'file': ('test.png', io.BytesIO(png_content), 'image/png')
    }
    
    print("\nTesting non-PDF rejection...")
    response = requests.post(
        f"{API_BASE}/analyze-ship-certificate",
        files=files,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")

if __name__ == "__main__":
    test_pdf_endpoint()
    test_non_pdf_rejection()
#!/usr/bin/env python3
"""
AI Analysis Test for BROTHER 36 PDF
Test the AI analysis endpoint directly to see if it can extract ship name
"""

import requests
import os

def test_ai_analysis():
    base_url = "https://certmaster-ship.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login first
    login_response = requests.post(f"{api_url}/auth/login", json={
        "username": "admin1",
        "password": "123456"
    })
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test AI analysis endpoint
    pdf_path = "/app/BROTHER_36_EIAPP_PM242757.pdf"
    
    if not os.path.exists(pdf_path):
        print("❌ PDF file not found")
        return
    
    print("🔍 Testing AI analysis endpoint...")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': ('BROTHER_36_EIAPP_PM242757.pdf', f, 'application/pdf')}
        
        response = requests.post(
            f"{api_url}/analyze-ship-certificate",
            files=files,
            headers=headers,
            timeout=60
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI Analysis successful!")
            print(f"Ship Name: {result.get('ship_name', 'Not extracted')}")
            print(f"Certificate Name: {result.get('cert_name', 'Not extracted')}")
            print(f"Category: {result.get('category', 'Not extracted')}")
            print(f"Certificate No: {result.get('cert_no', 'Not extracted')}")
            
            if result.get('ship_name') == 'BROTHER 36':
                print("✅ Ship name correctly extracted!")
            else:
                print(f"⚠️  Ship name issue: Expected 'BROTHER 36', got '{result.get('ship_name')}'")
        else:
            print(f"❌ AI Analysis failed: {response.text}")

if __name__ == "__main__":
    test_ai_analysis()
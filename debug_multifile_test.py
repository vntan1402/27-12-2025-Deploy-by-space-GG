#!/usr/bin/env python3
"""
Debug Multi-File Upload Test
Quick test to debug the multi-file upload issue
"""

import requests
import tempfile
import os

def test_multifile_debug():
    base_url = "https://aicert-analyzer.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login as admin
    login_response = requests.post(f"{api_url}/auth/login", json={
        "username": "admin", 
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Download test PDF
    pdf_url = "https://customer-assets.emergentagent.com/job_vessel-docs-1/artifacts/nzwrda4b_BROTHER%2036%20-%20IAPP%20-%20PM242838.pdf"
    pdf_response = requests.get(pdf_url)
    
    if pdf_response.status_code != 200:
        print("❌ PDF download failed")
        return
    
    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.write(pdf_response.content)
    temp_file.close()
    
    # Create a company first
    company_data = {
        "name_vn": "Debug Company",
        "name_en": "Debug Company",
        "address_vn": "Debug Address",
        "address_en": "Debug Address", 
        "tax_id": "DEBUG123",
        "gmail": "debug@company.com",
        "zalo": "0123456789"
    }
    
    company_response = requests.post(f"{api_url}/companies", json=company_data, headers=headers)
    if company_response.status_code != 200:
        print(f"❌ Company creation failed: {company_response.status_code}")
        print(company_response.text)
        return
    
    company_name = company_response.json()['name_en']
    
    # Create a user with company
    user_data = {
        "username": "debug_user",
        "password": "debug123",
        "email": "debug@test.com",
        "full_name": "Debug User",
        "role": "editor",
        "department": "technical",
        "company": company_name,
        "zalo": "0987654321"
    }
    
    user_response = requests.post(f"{api_url}/users", json=user_data, headers=headers)
    if user_response.status_code != 200:
        print(f"❌ User creation failed: {user_response.status_code}")
        print(user_response.text)
        return
    
    # Login as the new user
    user_login_response = requests.post(f"{api_url}/auth/login", json={
        "username": "debug_user",
        "password": "debug123"
    })
    
    if user_login_response.status_code != 200:
        print("❌ User login failed")
        return
    
    user_token = user_login_response.json()['access_token']
    user_headers = {'Authorization': f'Bearer {user_token}'}
    
    # Test multi-file upload
    with open(temp_file.name, 'rb') as f:
        files = {'files': ('BROTHER_36_IAPP_PM242838.pdf', f, 'application/pdf')}
        
        upload_response = requests.post(
            f"{api_url}/certificates/upload-multi-files",
            files=files,
            headers=user_headers,
            timeout=300
        )
    
    print(f"Upload response status: {upload_response.status_code}")
    print(f"Upload response: {upload_response.text}")
    
    # Clean up
    os.unlink(temp_file.name)

if __name__ == "__main__":
    test_multifile_debug()
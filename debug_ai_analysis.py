#!/usr/bin/env python3

import requests
import sys
import json
import tempfile
import os

def test_ai_analysis_directly():
    """Test the AI analysis function directly"""
    
    # Login first
    response = requests.post('https://ship-manager-1.preview.emergentagent.com/api/auth/login', 
                            json={'username': 'admin1', 'password': '123456'})
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Download the PDF
    pdf_url = "https://customer-assets.emergentagent.com/job_vessel-docs-1/artifacts/nzwrda4b_BROTHER%2036%20-%20IAPP%20-%20PM242838.pdf"
    pdf_response = requests.get(pdf_url, timeout=30)
    pdf_content = pdf_response.content
    filename = "BROTHER 36 - IAPP - PM242838.pdf"
    
    print(f"Downloaded PDF: {len(pdf_content)} bytes")
    
    # Test single PDF analysis (this works)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(pdf_content)
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/pdf')}
            response = requests.post(
                'https://ship-manager-1.preview.emergentagent.com/api/analyze-ship-certificate',
                files=files, 
                headers=headers,
                timeout=60
            )
        
        print(f"Single PDF Analysis Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Single PDF Result: {json.dumps(result, indent=2)}")
        else:
            print(f"Single PDF Error: {response.text}")
            
    finally:
        try:
            os.unlink(temp_file_path)
        except:
            pass
    
    # Test multi-file upload with detailed error capture
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(pdf_content)
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            files = {'files': (filename, f, 'application/pdf')}
            response = requests.post(
                'https://ship-manager-1.preview.emergentagent.com/api/certificates/upload-multi-files',
                files=files, 
                headers=headers,
                timeout=60
            )
        
        print(f"\nMulti-File Upload Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Multi-File Result: {json.dumps(result, indent=2)}")
        else:
            print(f"Multi-File Error: {response.text}")
            
    finally:
        try:
            os.unlink(temp_file_path)
        except:
            pass

if __name__ == "__main__":
    test_ai_analysis_directly()
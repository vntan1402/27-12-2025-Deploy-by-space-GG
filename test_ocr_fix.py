#!/usr/bin/env python3
"""
Test OCR processor with Poppler fix
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

# SUNSHINE ship ID
SUNSHINE_SHIP_ID = "e21c71a2-9543-4f92-990c-72f54292fde8"

def test_ocr_fix():
    """Test if OCR processing works after Poppler installation"""
    try:
        # Authenticate
        response = requests.post(f"{API_BASE}/auth/login", json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ Authentication successful")
        
        # Download the SUNSHINE PDF
        pdf_url = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/s6nh3s3p_SUNSHINE_01_ImagePDF.pdf"
        pdf_response = requests.get(pdf_url)
        
        if pdf_response.status_code != 200:
            print(f"❌ PDF download failed: {pdf_response.status_code}")
            return False
        
        pdf_content = pdf_response.content
        print(f"✅ PDF downloaded: {len(pdf_content):,} bytes")
        
        # Test multi-cert upload with detailed logging
        files = {
            'files': ('SUNSHINE_01_CSSC_PM25385.pdf', pdf_content, 'application/pdf')
        }
        
        print("🔍 Testing multi-cert upload with OCR processing...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE}/certificates/multi-upload?ship_id={SUNSHINE_SHIP_ID}",
            files=files,
            headers=headers
        )
        
        processing_time = time.time() - start_time
        print(f"⏱️ Processing time: {processing_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if results:
                result = results[0]
                analysis = result.get('analysis', {})
                
                print(f"\n🎯 ANALYSIS RESULTS:")
                print(f"  Status: {result.get('status')}")
                print(f"  Category: {analysis.get('category')}")
                print(f"  Certificate Name: '{analysis.get('cert_name')}'")
                print(f"  Certificate Number: '{analysis.get('cert_no')}'")
                print(f"  Confidence: {analysis.get('confidence')}")
                print(f"  Extraction Error: {analysis.get('extraction_error')}")
                
                # Check if we're still getting filename-based classification
                cert_name = analysis.get('cert_name', '')
                if cert_name.startswith("Maritime Certificate -"):
                    print(f"❌ STILL USING FILENAME-BASED CLASSIFICATION")
                    print(f"    This means OCR processing is still failing")
                    return False
                else:
                    print(f"✅ OCR PROCESSING APPEARS TO BE WORKING")
                    print(f"    Certificate name is not filename-based")
                    return True
            else:
                print(f"❌ No results in response")
                return False
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    print("🔧 TESTING OCR FIX AFTER POPPLER INSTALLATION")
    print("=" * 60)
    
    success = test_ocr_fix()
    
    if success:
        print("\n🎉 OCR FIX SUCCESSFUL - Certificate names should now be extracted correctly")
    else:
        print("\n❌ OCR FIX FAILED - Still using filename-based classification")
    
    sys.exit(0 if success else 1)
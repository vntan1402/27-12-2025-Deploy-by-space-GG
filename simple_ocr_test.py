#!/usr/bin/env python3
"""
Simple OCR Test - Test if OCR processing is working after installing Poppler and Tesseract
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import io
import urllib.request

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ship-cert-manager-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

# PDF file from review request
PDF_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/s6nh3s3p_SUNSHINE_01_ImagePDF.pdf"

def test_ocr_fix():
    """Test if OCR processing is working after installing dependencies"""
    print("🔍 SIMPLE OCR TEST - Testing if Poppler and Tesseract fix worked")
    print("=" * 70)
    
    try:
        # Step 1: Login
        print("🔐 Step 1: Authentication...")
        login_response = requests.post(f"{API_BASE}/auth/login", json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }, timeout=30)
        
        if login_response.status_code != 200:
            print(f"❌ Authentication failed: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Authentication successful")
        
        # Step 2: Download PDF
        print("📥 Step 2: Downloading PDF...")
        with urllib.request.urlopen(PDF_URL) as response:
            pdf_content = response.read()
        
        file_size = len(pdf_content)
        print(f"✅ Downloaded PDF: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        
        # Step 3: Test certificate analysis
        print("🔍 Step 3: Testing certificate analysis...")
        files = {
            'file': ('SUNSHINE_01_ImagePDF.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        
        analysis_response = requests.post(
            f"{API_BASE}/analyze-ship-certificate",
            files=files,
            headers=headers,
            timeout=120  # Give it 2 minutes for OCR processing
        )
        
        if analysis_response.status_code == 200:
            result = analysis_response.json()
            analysis_data = result.get('data', {}).get('analysis', {})
            
            cert_name = analysis_data.get('cert_name', '')
            cert_number = analysis_data.get('cert_no', '')
            issued_by = analysis_data.get('issued_by', '')
            ship_name = analysis_data.get('ship_name', '')
            
            print(f"📋 Analysis Results:")
            print(f"   Ship Name: '{ship_name}'")
            print(f"   Certificate Name: '{cert_name}'")
            print(f"   Certificate Number: '{cert_number}'")
            print(f"   Issued By: '{issued_by}'")
            
            # Check if it's still using filename-based fallback
            if ('SUNSHINE_01_ImagePDF' in str(cert_name) or 
                'CERT_SUNSHINE_01_IMAGEPDF' in str(cert_number) or
                'Filename-based' in str(issued_by)):
                print("❌ STILL USING FILENAME-BASED FALLBACK")
                print("   OCR processing is still not working correctly")
                return False
            elif ('tonnage' in str(cert_name).lower() or 
                  'PM242' in str(cert_number) or
                  'belize' in str(issued_by).lower() or
                  'panama' in str(issued_by).lower()):
                print("✅ SUCCESS: Real PDF extraction working!")
                print("   OCR processing is now functional")
                return True
            else:
                print("⚠️ UNCLEAR: Analysis completed but results are unclear")
                print(f"   Full analysis data: {analysis_data}")
                return False
        else:
            print(f"❌ Analysis failed: {analysis_response.status_code}")
            print(f"   Response: {analysis_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_ocr_fix()
    print("\n" + "=" * 70)
    if success:
        print("🎉 OCR FIX SUCCESSFUL - Real PDF extraction is working!")
    else:
        print("❌ OCR FIX FAILED - Still using filename-based fallback")
    print("=" * 70)
    sys.exit(0 if success else 1)
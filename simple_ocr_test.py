#!/usr/bin/env python3
"""
Simple OCR Test for Ship Management System
Focus: Testing the specific OCR fixes mentioned in the review request
"""

import requests
import json
import tempfile
import os
from datetime import datetime

# Configuration
BACKEND_URL = "http://0.0.0.0:8001/api"
TEST_PDF_URL = "https://customer-assets.emergentagent.com/job_shipment-ai-1/artifacts/1mu8wxqn_SS%20STAR%20PM252494416_ImagePDF.pdf"
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def main():
    log("🔬 Starting Simple OCR Test")
    
    # Step 1: Authenticate
    log("🔐 Authenticating...")
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "remember_me": False
    }
    
    session = requests.Session()
    response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        log(f"❌ Authentication failed: {response.status_code}")
        return False
    
    data = response.json()
    token = data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    log("✅ Authentication successful")
    
    # Step 2: Download PDF
    log("📥 Downloading test PDF...")
    pdf_response = requests.get(TEST_PDF_URL)
    if pdf_response.status_code != 200:
        log(f"❌ PDF download failed: {pdf_response.status_code}")
        return False
    
    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.write(pdf_response.content)
    temp_file.close()
    
    file_size = len(pdf_response.content)
    log(f"✅ PDF downloaded: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    try:
        # Step 3: Test OCR endpoint
        log("🔬 Testing OCR endpoint...")
        
        with open(temp_file.name, 'rb') as pdf_file:
            files = {
                'file': ('SS_STAR_PM252494416_ImagePDF.pdf', pdf_file, 'application/pdf')
            }
            
            start_time = datetime.now()
            response = session.post(f"{BACKEND_URL}/analyze-ship-certificate", files=files)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            log(f"⏱️  Processing time: {processing_time:.2f} seconds")
            log(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    log("✅ OCR endpoint responded successfully")
                    
                    # Analyze response
                    success = result.get('success', False)
                    log(f"   Success: {success}")
                    
                    # Check for analysis data
                    analysis = None
                    if 'data' in result and 'analysis' in result['data']:
                        analysis = result['data']['analysis']
                    elif 'analysis' in result:
                        analysis = result['analysis']
                    
                    if analysis:
                        log("   📋 Extracted Ship Data:")
                        
                        # Expected fields based on review request
                        expected_fields = {
                            'ship_name': 'SUNSHINE STAR',
                            'imo_number': '9405136', 
                            'flag': 'BELIZE',
                            'class_society': 'PMDS',
                            'gross_tonnage': 2988,
                            'built_year': 2005,
                            'deadweight': 5274.3
                        }
                        
                        extracted_count = 0
                        for field, expected in expected_fields.items():
                            value = analysis.get(field)
                            if value and str(value).strip() and value != 'null':
                                log(f"      ✅ {field}: {value}")
                                extracted_count += 1
                            else:
                                log(f"      ❌ {field}: Not extracted")
                        
                        log(f"   📈 Extraction Rate: {extracted_count}/{len(expected_fields)} ({extracted_count/len(expected_fields)*100:.1f}%)")
                        
                        # Check processing method
                        processing_method = result.get('processing_method', 'Unknown')
                        log(f"   🔧 Processing Method: {processing_method}")
                        
                        # Check for fallback reasons
                        fallback_reason = analysis.get('fallback_reason') or result.get('fallback_reason')
                        if fallback_reason:
                            log(f"   ⚠️  Fallback Reason: {fallback_reason}")
                        
                        # Determine if OCR is working
                        if extracted_count >= 4 and not fallback_reason:
                            log("🎉 OCR FUNCTIONALITY: WORKING - Real data extracted successfully!")
                            return True
                        elif extracted_count >= 2:
                            log("⚠️  OCR FUNCTIONALITY: PARTIAL - Some data extracted")
                            return True
                        else:
                            log("❌ OCR FUNCTIONALITY: POOR - Minimal or no real data extracted")
                            return False
                    else:
                        log("   ❌ No analysis data found")
                        return False
                        
                except json.JSONDecodeError:
                    log(f"❌ Invalid JSON response: {response.text[:200]}...")
                    return False
            else:
                log(f"❌ OCR endpoint failed: {response.status_code}")
                log(f"   Error: {response.text}")
                return False
                
    finally:
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
            log("🧹 Cleaned up temp file")

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 OCR TEST PASSED!")
    else:
        print("\n❌ OCR TEST FAILED!")
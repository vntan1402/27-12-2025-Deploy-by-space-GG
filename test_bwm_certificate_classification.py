#!/usr/bin/env python3
"""
Test BWM SOC certificate classification to debug why it's not classified as marine certificate
"""
import requests
import sys
import os
import base64

# Test backend URL
backend_url = 'http://localhost:8001'

def test_certificate_classification():
    """Test the BWM SOC certificate classification"""
    
    # Login
    login_data = {
        "username": "admin1",
        "password": "123456"
    }
    
    session = requests.Session()
    
    print("🔐 Logging in...")
    login_response = session.post(f"{backend_url}/api/auth/login", json=login_data)
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        token = login_result.get('access_token')
        session.headers.update({'Authorization': f'Bearer {token}'})
        print("✅ Login successful")
        
        # Download the PDF file
        pdf_url = "https://customer-assets.emergentagent.com/job_122ebe49-2c94-4bb7-ae0f-b005c9c2f055/artifacts/nbes1g4w_SUNSHINE%2001%20-%20BWM%20SOC%20-%20PM242911.pdf"
        
        print(f"\n📥 Downloading PDF from: {pdf_url}")
        pdf_response = requests.get(pdf_url)
        
        if pdf_response.status_code == 200:
            pdf_content = pdf_response.content
            print(f"✅ Downloaded PDF: {len(pdf_content)} bytes")
            
            # Test single certificate analysis endpoint
            print(f"\n🔍 Testing single certificate analysis...")
            
            files = {
                'file': ('BWM_SOC_PM242911.pdf', pdf_content, 'application/pdf')
            }
            
            analyze_response = session.post(f"{backend_url}/api/analyze-ship-certificate", files=files)
            print(f"Analysis response status: {analyze_response.status_code}")
            
            if analyze_response.status_code == 200:
                result = analyze_response.json()
                print("✅ Certificate analysis successful!")
                print(f"   Category: {result.get('category', 'Not found')}")
                print(f"   Cert Name: {result.get('cert_name', 'Not found')}")
                print(f"   Cert No: {result.get('cert_no', 'Not found')}")
                print(f"   Cert Type: {result.get('cert_type', 'Not found')}")
                print(f"   Issue Date: {result.get('issue_date', 'Not found')}")
                print(f"   Valid Date: {result.get('valid_date', 'Not found')}")
                print(f"   Issued By: {result.get('issued_by', 'Not found')}")
                print(f"   Confidence: {result.get('confidence', 'Not found')}")
                
                # Check classification
                category = result.get('category')
                if category == 'certificates':
                    print("✅ CORRECTLY classified as Marine Certificate!")
                else:
                    print(f"❌ INCORRECTLY classified as '{category}' instead of 'certificates'")
                    
                    # Show the full result for debugging
                    print(f"\n🔍 Full AI analysis result:")
                    import json
                    print(json.dumps(result, indent=2, default=str))
            else:
                try:
                    error_data = analyze_response.json()
                    print(f"❌ Analysis failed: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"❌ Analysis failed: {analyze_response.status_code} - {analyze_response.text[:500]}")
            
            # Test multi-certificate upload to see the classification
            print(f"\n📤 Testing multi-certificate upload classification...")
            
            files = {
                'files': ('BWM_SOC_PM242911.pdf', pdf_content, 'application/pdf')
            }
            data = {
                'ship_id': 'test-ship-id'  # We just want to see the classification step
            }
            
            multi_upload_response = session.post(f"{backend_url}/api/multi-cert-upload", files=files, data=data)
            print(f"Multi-upload response status: {multi_upload_response.status_code}")
            
            if multi_upload_response.status_code == 200:
                multi_result = multi_upload_response.json()
                print("✅ Multi-upload test successful!")
                
                if multi_result.get('results'):
                    first_result = multi_result['results'][0]
                    print(f"   Status: {first_result.get('status', 'Not found')}")
                    print(f"   Message: {first_result.get('message', 'Not found')}")
                    print(f"   Is Marine: {first_result.get('is_marine', 'Not found')}")
                    
                    if first_result.get('analysis'):
                        analysis = first_result['analysis']
                        print(f"   Analysis Category: {analysis.get('category', 'Not found')}")
                        
                        if analysis.get('category') == 'certificates':
                            print("✅ Multi-upload CORRECTLY classified as Marine Certificate!")
                        else:
                            print(f"❌ Multi-upload INCORRECTLY classified as '{analysis.get('category')}' instead of 'certificates'")
            else:
                try:
                    error_data = multi_upload_response.json()
                    print(f"❌ Multi-upload failed: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"❌ Multi-upload failed: {multi_upload_response.status_code} - {multi_upload_response.text[:500]}")
                    
        else:
            print(f"❌ Failed to download PDF: {pdf_response.status_code}")
    else:
        print(f"❌ Login failed: {login_response.text}")

if __name__ == "__main__":
    test_certificate_classification()
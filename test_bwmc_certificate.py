#!/usr/bin/env python3
"""
Test script to debug the BWMC certificate AI extraction issue
"""
import requests
import json
import sys

API_URL = "https://shipmate-55.preview.emergentagent.com"

def login():
    """Login and get auth token"""
    login_data = {
        "username": "admin1", 
        "password": "123456"
    }
    
    response = requests.post(f"{API_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_bwmc_certificate_upload(token, ship_id):
    """Test BWMC certificate upload with the problematic PDF file"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Download the PDF file from the uploaded artifact
    pdf_url = "https://customer-assets.emergentagent.com/job_shipmate-55/artifacts/miu8x0al_BROTHER%2036-BWMC-021204%20%281%29.pdf"
    pdf_response = requests.get(pdf_url)
    
    if pdf_response.status_code != 200:
        print(f"❌ Failed to download PDF: {pdf_response.status_code}")
        return False
    
    print(f"✅ Downloaded PDF: {len(pdf_response.content)} bytes")
    
    # Prepare form data
    files = {
        'files': ('BROTHER 36-BWMC-021204 (1).pdf', pdf_response.content, 'application/pdf')
    }
    
    data = {
        'category': 'Class & Flag Cert',
        'subcategory': 'Certificates'
    }
    
    print(f"\n🧪 Testing BWMC certificate AI extraction...")
    print(f"   File: BROTHER 36-BWMC-021204 (1).pdf")
    print(f"   Size: {len(pdf_response.content)} bytes")
    
    # Make multi upload request with extended timeout
    url = f"{API_URL}/api/certificates/multi-upload?ship_id={ship_id}"
    response = requests.post(url, headers=headers, files=files, data=data, timeout=180)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Multi certificate upload completed")
        
        # Check if AI extraction was successful
        if "results" in result and len(result["results"]) > 0:
            first_result = result["results"][0]
            
            print(f"\n📊 AI Extraction Analysis:")
            print(f"   Status: {first_result.get('status', 'unknown')}")
            
            if first_result.get("status") == "success":
                analysis = first_result.get("analysis", {})
                print("🎉 SUCCESS: AI extraction worked correctly!")
                print(f"   Certificate Name: {analysis.get('cert_name', 'N/A')}")
                print(f"   Certificate No: {analysis.get('cert_no', 'N/A')}")
                print(f"   Ship Name: {analysis.get('ship_name', 'N/A')}")
                print(f"   Processing Method: {analysis.get('processing_method', 'N/A')}")
                print(f"   OCR Confidence: {analysis.get('ocr_confidence', 'N/A')}")
                print(f"   PDF Type: {analysis.get('pdf_type', 'N/A')}")
                print(f"   Text Length: {analysis.get('text_length', 'N/A')} chars")
                return True
                
            elif first_result.get("status") == "ai_extraction_failed":
                print("❌ AI extraction failed - analyzing reasons:")
                print(f"   Reason: {first_result.get('reason', 'Unknown')}")
                
                # Get detailed analysis if available
                analysis = first_result.get("analysis", {})
                if analysis:
                    print(f"\n📋 Extracted Analysis Details:")
                    print(f"   Category: {analysis.get('category', 'N/A')}")
                    print(f"   Confidence: {analysis.get('confidence', 'N/A')}")
                    print(f"   Processing Method: {analysis.get('processing_method', 'N/A')}")
                    print(f"   OCR Confidence: {analysis.get('ocr_confidence', 'N/A')}")
                    print(f"   PDF Type: {analysis.get('pdf_type', 'N/A')}")
                    print(f"   Text Length: {analysis.get('text_length', 'N/A')} chars")
                    
                    # Show extracted fields to understand what worked and what didn't
                    critical_fields = ['ship_name', 'cert_name', 'cert_no']
                    all_fields = ['ship_name', 'imo_number', 'cert_name', 'cert_no', 
                                 'issue_date', 'valid_date', 'issued_by']
                    
                    print(f"\n🔍 Field Extraction Analysis:")
                    for field in all_fields:
                        value = analysis.get(field, 'N/A')
                        status = "✅" if value and str(value).lower() not in ['unknown', 'null', 'none', '', 'n/a'] else "❌"
                        critical = "🔴" if field in critical_fields else "🔵"
                        print(f"   {critical} {status} {field}: {value}")
                
                return False
            else:
                print(f"⚠️ Unexpected status: {first_result.get('status')}")
                print(f"Full result: {json.dumps(first_result, indent=2)}")
                return False
        else:
            print("❌ No results in response")
            print(f"Full response: {json.dumps(result, indent=2)}")
            return False
    else:
        print(f"❌ Upload failed: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"Error details: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"Response text: {response.text}")
        return False

def main():
    print("🧪 Testing BWMC Certificate AI Extraction Issue")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        sys.exit(1)
    
    # Use known ship ID (BROTHER 36)
    ship_id = "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"  # BROTHER 36
    
    print(f"\n📋 Testing with ship: BROTHER 36")
    print(f"   Ship ID: {ship_id}")
    
    # Test BWMC certificate upload
    success = test_bwmc_certificate_upload(token, ship_id)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ SUCCESS: BWMC certificate AI extraction is working!")
    else:
        print("❌ ISSUE: BWMC certificate still requires manual input")
        print("\nPossible causes:")
        print("1. Image-based PDF requiring OCR processing")
        print("2. Complex document layout confusing AI")
        print("3. Confidence scoring still too strict")
        print("4. Missing specialized certificate type handling")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script to verify the BWMC certificate OCR fix
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

def test_bwmc_certificate_after_ocr_fix(token, ship_id):
    """Test BWMC certificate upload after installing PyCryptodome and Poppler"""
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
    
    print(f"\n🧪 Testing BWMC certificate AI extraction after OCR dependencies fix...")
    print(f"   Dependencies installed: PyCryptodome + Poppler")
    
    # Make multi upload request
    url = f"{API_URL}/api/certificates/multi-upload?ship_id={ship_id}"
    
    try:
        response = requests.post(url, headers=headers, files=files, data=data, timeout=90)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Multi certificate upload completed")
            
            # Check if AI extraction was successful
            if "results" in result and len(result["results"]) > 0:
                first_result = result["results"][0]
                
                print(f"\n📊 AI Extraction Results:")
                print(f"   Status: {first_result.get('status', 'unknown')}")
                
                if first_result.get("status") == "success":
                    analysis = first_result.get("analysis", {})
                    print("🎉 SUCCESS: AI extraction now working correctly!")
                    print(f"   Certificate Name: {analysis.get('cert_name', 'N/A')}")
                    print(f"   Certificate No: {analysis.get('cert_no', 'N/A')}")
                    print(f"   Ship Name: {analysis.get('ship_name', 'N/A')}")
                    print(f"   Issue Date: {analysis.get('issue_date', 'N/A')}")
                    print(f"   Valid Date: {analysis.get('valid_date', 'N/A')}")
                    print(f"   Processing Method: {analysis.get('processing_method', 'N/A')}")
                    print(f"   OCR Confidence: {analysis.get('ocr_confidence', 'N/A')}")
                    print(f"   PDF Type: {analysis.get('pdf_type', 'N/A')}")
                    print(f"   Text Length: {analysis.get('text_length', 'N/A')} chars")
                    
                    # Show upload success
                    upload_info = first_result.get("upload", {})
                    if upload_info.get("success"):
                        print(f"   🔗 Google Drive: {upload_info.get('file_url', 'N/A')}")
                        print(f"   📁 Folder: {upload_info.get('folder_path', 'N/A')}")
                    
                    certificate_info = first_result.get("certificate", {})
                    if certificate_info.get("success"):
                        print(f"   🆔 Certificate ID: {certificate_info.get('id', 'N/A')}")
                    
                    return True
                    
                elif first_result.get("status") == "ai_extraction_failed":
                    print("❌ AI extraction still failed:")
                    print(f"   Reason: {first_result.get('reason', 'Unknown')}")
                    
                    # Get analysis details to see what improved
                    analysis = first_result.get("analysis", {})
                    if analysis:
                        print(f"\n📋 Failure Analysis:")
                        print(f"   Processing Method: {analysis.get('processing_method', 'N/A')}")
                        print(f"   OCR Confidence: {analysis.get('ocr_confidence', 'N/A')}")
                        print(f"   PDF Type: {analysis.get('pdf_type', 'N/A')}")
                        print(f"   Text Length: {analysis.get('text_length', 'N/A')} chars")
                        print(f"   Confidence: {analysis.get('confidence', 'N/A')}")
                    
                    return False
                else:
                    print(f"⚠️ Unexpected status: {first_result.get('status')}")
                    return False
            else:
                print("❌ No results in response")
                return False
        else:
            print(f"❌ Upload failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Response text: {response.text}")
            return False
            
    except requests.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def main():
    print("🧪 Testing BWMC Certificate After OCR Dependencies Fix")
    print("=" * 60)
    print("Dependencies installed:")
    print("  - PyCryptodome: For encrypted PDF handling")
    print("  - Poppler: For PDF to image conversion")
    
    # Login
    token = login()
    if not token:
        sys.exit(1)
    
    # Use known ship ID (BROTHER 36)
    ship_id = "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"  # BROTHER 36
    
    print(f"\n📋 Testing with ship: BROTHER 36")
    print(f"   Ship ID: {ship_id}")
    
    # Test BWMC certificate upload
    success = test_bwmc_certificate_after_ocr_fix(token, ship_id)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ SUCCESS: BWMC certificate OCR dependencies fix worked!")
        print("   - PDF encryption handled with PyCryptodome")
        print("   - OCR processing enabled with Poppler")
        print("   - Certificate processed automatically")
    else:
        print("❌ ISSUE: OCR dependencies fix may need additional work")
        print("   - Check backend logs for detailed error analysis")

if __name__ == "__main__":
    main()
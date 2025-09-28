#!/usr/bin/env python3
"""
PDF Marine Certificate Classification Test
Testing with actual PDF files to check OCR and classification
"""

import requests
import json
import os
import tempfile
import time
from datetime import datetime
from io import BytesIO

BACKEND_URL = 'http://localhost:8001/api'

def authenticate():
    """Authenticate and get token"""
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def create_simple_pdf_with_reportlab():
    """Create a simple PDF using reportlab if available"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add marine certificate content
        p.drawString(100, 750, "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE")
        p.drawString(100, 720, "Certificate No: CSSC-2024-001")
        p.drawString(100, 690, "IMO Number: 9999998")
        p.drawString(100, 660, "Ship Name: MARINE TEST VESSEL")
        p.drawString(100, 630, "Flag State: PANAMA")
        p.drawString(100, 600, "Classification Society: PMDS")
        p.drawString(100, 570, "Issue Date: 15/01/2024")
        p.drawString(100, 540, "Valid Until: 15/01/2029")
        p.drawString(100, 510, "Issued by: Panama Maritime Authority")
        p.drawString(100, 480, "This certificate is issued under the provisions of SOLAS 1974")
        p.drawString(100, 450, "and certifies that the ship has been surveyed and complies")
        p.drawString(100, 420, "with the applicable requirements of the Convention.")
        p.drawString(100, 390, "")
        p.drawString(100, 360, "Survey Status:")
        p.drawString(120, 340, "- Annual Survey: 15/01/2024")
        p.drawString(120, 320, "- Intermediate Survey: Due 15/07/2024")
        p.drawString(120, 300, "- Special Survey: Due 15/01/2029")
        p.drawString(100, 270, "")
        p.drawString(100, 250, "Inspections of the outside of the ship's bottom:")
        p.drawString(120, 230, "- Last inspection: 15/01/2024")
        p.drawString(120, 210, "- Next inspection due: 15/01/2026")
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        print("⚠️ reportlab not available, creating minimal PDF")
        return create_minimal_pdf()

def create_minimal_pdf():
    """Create a minimal PDF with basic structure"""
    # This creates a very basic PDF structure
    pdf_content = b"""%PDF-1.4
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
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj

4 0 obj
<<
/Length 800
>>
stream
BT
/F1 12 Tf
100 700 Td
(CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE) Tj
0 -20 Td
(Certificate No: CSSC-2024-001) Tj
0 -20 Td
(IMO Number: 9999998) Tj
0 -20 Td
(Ship Name: MARINE TEST VESSEL) Tj
0 -20 Td
(Flag State: PANAMA) Tj
0 -20 Td
(Classification Society: PMDS) Tj
0 -20 Td
(Issue Date: 15/01/2024) Tj
0 -20 Td
(Valid Until: 15/01/2029) Tj
0 -20 Td
(Issued by: Panama Maritime Authority) Tj
0 -20 Td
() Tj
0 -20 Td
(This certificate is issued under the provisions of SOLAS 1974) Tj
0 -20 Td
(and certifies that the ship has been surveyed and complies) Tj
0 -20 Td
(with the applicable requirements of the Convention.) Tj
0 -20 Td
() Tj
0 -20 Td
(Survey Status:) Tj
0 -20 Td
(- Annual Survey: 15/01/2024) Tj
0 -20 Td
(- Intermediate Survey: Due 15/07/2024) Tj
0 -20 Td
(- Special Survey: Due 15/01/2029) Tj
0 -20 Td
() Tj
0 -20 Td
(Inspections of the outside of the ship's bottom:) Tj
0 -20 Td
(- Last inspection: 15/01/2024) Tj
0 -20 Td
(- Next inspection due: 15/01/2026) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000356 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
1206
%%EOF"""
    return pdf_content

def test_analyze_certificate_pdf():
    """Test the analyze-ship-certificate endpoint with PDF"""
    print("🔍 Testing analyze-ship-certificate endpoint with PDF...")
    
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test PDF
    pdf_content = create_simple_pdf_with_reportlab()
    
    files = {
        'file': ('marine_certificate.pdf', pdf_content, 'application/pdf')
    }
    
    print(f"   Testing with PDF ({len(pdf_content)} bytes)")
    
    response = requests.post(
        f"{BACKEND_URL}/analyze-ship-certificate",
        files=files,
        headers=headers,
        timeout=120  # Longer timeout for OCR processing
    )
    
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Analyze endpoint working with PDF")
        
        # Check the analysis result
        analysis = data.get('analysis', {})
        success = data.get('success', False)
        message = data.get('message', '')
        
        print(f"   Success: {success}")
        print(f"   Message: {message}")
        
        # Check key fields
        cert_name = analysis.get('cert_name')
        category = analysis.get('category')
        processing_method = analysis.get('processing_method')
        pdf_type = analysis.get('pdf_type')
        
        print(f"   Certificate Name: {cert_name}")
        print(f"   Category: {category}")
        print(f"   Processing Method: {processing_method}")
        print(f"   PDF Type: {pdf_type}")
        
        # Check if classified correctly
        if category and category.lower() == 'certificates':
            print("✅ Correctly classified as marine certificate (category: certificates)")
            return True
        elif category:
            print(f"❌ Incorrectly classified as: {category}")
        else:
            print("❌ No category classification found")
            
        # Show more details for debugging
        print(f"   Full analysis: {json.dumps(analysis, indent=2)}")
        
        return False
    else:
        print(f"❌ Analyze endpoint failed: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error}")
        except:
            print(f"   Error: {response.text[:500]}")
        return False

def test_multi_upload_pdf():
    """Test multi-upload with PDF"""
    print("📤 Testing multi-upload endpoint with PDF...")
    
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get existing ship
    response = requests.get(f"{BACKEND_URL}/ships", headers=headers, timeout=30)
    if response.status_code != 200:
        print("❌ Could not get ships")
        return False
    
    ships = response.json()
    if not ships:
        print("❌ No ships available")
        return False
    
    ship_id = ships[0]['id']
    print(f"   Using ship: {ships[0]['name']} (ID: {ship_id})")
    
    # Create test PDF
    pdf_content = create_simple_pdf_with_reportlab()
    
    files = {
        'files': ('marine_certificate_multi.pdf', pdf_content, 'application/pdf')
    }
    
    params = {'ship_id': ship_id}
    
    print(f"   Testing with PDF ({len(pdf_content)} bytes)")
    
    response = requests.post(
        f"{BACKEND_URL}/certificates/multi-upload",
        files=files,
        params=params,
        headers=headers,
        timeout=120
    )
    
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Multi-upload endpoint accessible")
        
        # Check results
        results = data.get('results', [])
        summary = data.get('summary', {})
        
        print(f"   Summary: {json.dumps(summary, indent=2)}")
        
        for result in results:
            filename = result.get('filename', '')
            status = result.get('status', '')
            message = result.get('message', '')
            
            print(f"   File: {filename}")
            print(f"   Status: {status}")
            print(f"   Message: {message}")
            
            if 'not a marine certificate' in message.lower():
                print("❌ 'Not a marine certificate' error found")
                return False
            elif 'unknown error' in message.lower():
                print("❌ 'Unknown error' found")
                return False
            elif status.lower() == 'success':
                print("✅ Upload successful - marine certificate recognized")
                return True
            elif status.lower() == 'error':
                print(f"❌ Upload error: {message}")
                return False
        
        return len(results) > 0
    else:
        print(f"❌ Multi-upload failed: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error}")
        except:
            print(f"   Error: {response.text[:500]}")
        return False

def check_ocr_functionality():
    """Check if OCR is working by testing PDF processing"""
    print("🔧 Testing OCR functionality...")
    
    try:
        # Test if we can import required libraries
        import pdf2image
        print("✅ pdf2image available")
        
        import pytesseract
        print("✅ pytesseract available")
        
        # Test tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
        
        # Test poppler tools
        import subprocess
        result = subprocess.run(['pdfinfo', '--help'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ poppler-utils (pdfinfo) working")
        else:
            print("❌ poppler-utils not working")
            
        return True
        
    except Exception as e:
        print(f"❌ OCR functionality test failed: {e}")
        return False

def main():
    print("🎯 PDF MARINE CERTIFICATE CLASSIFICATION TEST")
    print("=" * 60)
    
    # Test 1: OCR Functionality
    ocr_working = check_ocr_functionality()
    print()
    
    # Test 2: Analyze Certificate with PDF
    analyze_working = test_analyze_certificate_pdf()
    print()
    
    # Test 3: Multi-upload with PDF
    multi_upload_working = test_multi_upload_pdf()
    print()
    
    # Summary
    print("📊 SUMMARY:")
    print(f"   OCR Functionality: {'✅' if ocr_working else '❌'}")
    print(f"   PDF Certificate Analysis: {'✅' if analyze_working else '❌'}")
    print(f"   PDF Multi-upload: {'✅' if multi_upload_working else '❌'}")
    
    if ocr_working and analyze_working and multi_upload_working:
        print("\n🎉 ALL TESTS PASSED - Marine certificate classification with OCR is working!")
    else:
        print("\n❌ SOME TESTS FAILED - Issues remain with marine certificate classification")
        
        if not ocr_working:
            print("   - OCR functionality needs attention")
        if not analyze_working:
            print("   - PDF certificate analysis/classification needs fixing")
        if not multi_upload_working:
            print("   - PDF multi-upload has issues")

if __name__ == "__main__":
    main()
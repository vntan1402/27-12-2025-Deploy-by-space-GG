#!/usr/bin/env python3
"""
Debug OCR functionality to understand why it's failing
"""

import sys
import os
sys.path.append('/app/backend')

from targeted_ocr import get_ocr_processor
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf():
    """Create a test PDF with header/footer content"""
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    
    # HEADER CONTENT (Top 15% of page)
    header_y_start = height * 0.85
    c.drawString(100, header_y_start, "MARITIME SURVEY REPORT HEADER")
    c.drawString(100, header_y_start - 20, "Classification Society: DNV GL")
    c.drawString(100, header_y_start - 40, "Document ID: MSR-2024-OCR-TEST")
    c.drawString(100, header_y_start - 60, "Report Form: Form SDS")
    
    # MAIN CONTENT (Middle section)
    main_y_start = height * 0.7
    c.drawString(100, main_y_start, "SURVEY REPORT")
    c.drawString(100, main_y_start - 30, "Ship Name: BROTHER 36")
    c.drawString(100, main_y_start - 50, "IMO Number: 8743531")
    c.drawString(100, main_y_start - 70, "Survey Type: Annual Survey")
    c.drawString(100, main_y_start - 90, "Report Number: SR-2024-OCR-001")
    
    # FOOTER CONTENT (Bottom 15% of page)
    footer_y_start = height * 0.15
    c.drawString(100, footer_y_start, "SURVEY REPORT FOOTER SECTION")
    c.drawString(100, footer_y_start - 20, "Survey completed at Port of Singapore")
    c.drawString(100, footer_y_start - 40, "Report No: SR-2024-OCR-001")
    c.drawString(100, footer_y_start - 60, "Page 1 of 1 - End of Document")
    
    c.save()
    pdf_content = pdf_buffer.getvalue()
    pdf_buffer.close()
    return pdf_content

def test_ocr():
    """Test OCR functionality"""
    print("🔍 Testing OCR functionality...")
    
    # Create test PDF
    print("📄 Creating test PDF...")
    pdf_content = create_test_pdf()
    print(f"✅ Test PDF created: {len(pdf_content)} bytes")
    
    # Get OCR processor
    print("🔧 Getting OCR processor...")
    try:
        ocr_processor = get_ocr_processor()
        print(f"✅ OCR processor created")
        print(f"📊 OCR available: {ocr_processor.is_available()}")
    except Exception as e:
        print(f"❌ Failed to get OCR processor: {e}")
        return
    
    # Test OCR extraction
    print("🔍 Testing OCR extraction...")
    try:
        result = ocr_processor.extract_from_pdf(pdf_content, page_num=0)
        print(f"📊 OCR Result:")
        print(f"   ocr_success: {result.get('ocr_success')}")
        print(f"   ocr_error: {result.get('ocr_error')}")
        print(f"   header_text: '{result.get('header_text', '')}'")
        print(f"   footer_text: '{result.get('footer_text', '')}'")
        print(f"   report_form: '{result.get('report_form', '')}'")
        print(f"   survey_report_no: '{result.get('survey_report_no', '')}'")
        
        if result.get('ocr_success'):
            print("✅ OCR extraction successful!")
        else:
            print(f"❌ OCR extraction failed: {result.get('ocr_error')}")
            
    except Exception as e:
        print(f"❌ Exception during OCR extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr()
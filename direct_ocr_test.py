#!/usr/bin/env python3
"""
Direct OCR Test - Test OCR processing directly without API calls

This test directly tests the OCR processor to verify that the 
SUNSHINE_01_ImagePDF.pdf can be processed correctly with the new dependencies.
"""

import sys
import os
import time
from pathlib import Path

# Add backend directory to path
sys.path.append('/app/backend')

def test_direct_ocr_processing():
    """Test OCR processing directly"""
    print("🔍 DIRECT OCR PROCESSING TEST")
    print("=" * 60)
    
    try:
        # Import the OCR processor
        from ocr_processor import EnhancedOCRProcessor
        
        print("✅ OCR processor imported successfully")
        
        # Initialize the processor
        ocr_processor = EnhancedOCRProcessor()
        print("✅ OCR processor initialized")
        
        # Test file
        pdf_file = "/app/SUNSHINE_01_ImagePDF_New.pdf"
        if not os.path.exists(pdf_file):
            print(f"❌ Test PDF file not found: {pdf_file}")
            return False
        
        print(f"📄 Testing with: {pdf_file}")
        
        # Read the PDF file
        with open(pdf_file, 'rb') as f:
            pdf_content = f.read()
        
        print(f"📊 PDF size: {len(pdf_content):,} bytes")
        
        # Process with OCR
        print("🔄 Starting OCR processing...")
        start_time = time.time()
        
        result = ocr_processor.process_pdf(pdf_content, "SUNSHINE_01_ImagePDF_New.pdf")
        
        processing_time = time.time() - start_time
        print(f"⏱️ Processing completed in {processing_time:.2f} seconds")
        
        # Analyze results
        if result:
            print("✅ OCR processing successful!")
            print(f"📋 Extracted text length: {len(result.get('text', ''))}")
            print(f"🎯 Confidence score: {result.get('confidence', 'N/A')}")
            print(f"📝 Processing method: {result.get('processing_method', 'N/A')}")
            
            # Show first 200 characters of extracted text
            extracted_text = result.get('text', '')
            if extracted_text:
                print(f"📄 Text preview: {extracted_text[:200]}...")
                
                # Check for certificate-related keywords
                keywords = ['certificate', 'cargo', 'ship', 'safety', 'construction', 'issued', 'valid']
                found_keywords = [kw for kw in keywords if kw.lower() in extracted_text.lower()]
                
                if found_keywords:
                    print(f"🔍 Found certificate keywords: {', '.join(found_keywords)}")
                    print("✅ OCR successfully extracted certificate content!")
                    return True
                else:
                    print("⚠️ No certificate keywords found in extracted text")
                    return False
            else:
                print("❌ No text extracted from PDF")
                return False
        else:
            print("❌ OCR processing failed - no result returned")
            return False
            
    except Exception as e:
        print(f"❌ Direct OCR test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run direct OCR test"""
    success = test_direct_ocr_processing()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 DIRECT OCR TEST PASSED!")
        print("The OCR processor can successfully extract text from SUNSHINE_01_ImagePDF.pdf")
        print("The fallback issue should be resolved in the API.")
    else:
        print("❌ DIRECT OCR TEST FAILED!")
        print("There may still be issues with OCR processing.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
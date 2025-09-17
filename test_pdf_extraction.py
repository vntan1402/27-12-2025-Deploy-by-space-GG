#!/usr/bin/env python3
"""
Test script to verify the enhanced PDF extraction functionality
"""

import sys
import os
sys.path.append('/app/backend')

from server import extract_text_from_pdf, classify_by_filename, analyze_with_google
import asyncio
from datetime import datetime

def test_pdf_extraction_with_empty_content():
    """Test PDF extraction with empty/invalid content"""
    print("Testing PDF extraction with empty content...")
    
    # Test with empty bytes
    result = extract_text_from_pdf(b"")
    print(f"Empty content result: '{result}'")
    
    # Test with invalid PDF content
    result = extract_text_from_pdf(b"This is not a PDF file")
    print(f"Invalid PDF result: '{result}'")
    
def test_classify_by_filename():
    """Test the enhanced classify_by_filename function"""
    print("\nTesting classify_by_filename...")
    
    # Test with certificate filename
    result = classify_by_filename("PM252494430.pdf")
    print(f"Certificate classification result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # Test with non-certificate filename
    result = classify_by_filename("manual.pdf")
    print(f"\nManual classification result:")
    for key, value in result.items():
        print(f"  {key}: {value}")

async def test_google_analysis_with_failed_extraction():
    """Test Google analysis when PDF extraction fails"""
    print("\nTesting Google analysis with failed PDF extraction...")
    
    # Mock parameters
    file_content = b"Invalid PDF content"
    filename = "test_certificate.pdf"
    content_type = "application/pdf"
    api_key = "test_key"
    model = "gemini-2.0-flash-exp"
    analysis_prompt = "Test prompt"
    
    try:
        result = await analyze_with_google(file_content, filename, content_type, api_key, model, analysis_prompt)
        print(f"Google analysis result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Expected error in Google analysis: {e}")

if __name__ == "__main__":
    print("=== Testing Enhanced PDF Extraction ===")
    
    test_pdf_extraction_with_empty_content()
    test_classify_by_filename()
    
    # Run async test
    asyncio.run(test_google_analysis_with_failed_extraction())
    
    print("\n=== Test completed ===")
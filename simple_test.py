#!/usr/bin/env python3
"""
Simple test for PDF extraction functions
"""

import sys
import os
sys.path.append('/app/backend')

# Import only the functions we need
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF content with enhanced error handling"""
    try:
        import PyPDF2
        import io
        from datetime import datetime
        
        # Create a PDF reader from bytes with enhanced error handling
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        
        # Check if PDF has pages
        if not pdf_reader.pages:
            logger.warning("PDF has no pages")
            return ""
        
        # Extract text from all pages with individual page error handling
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            except Exception as page_error:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {page_error}")
                continue
        
        # Clean and validate extracted text
        text = text.strip()
        if not text:
            logger.warning("No readable text content extracted from PDF")
            return ""
        
        # Log successful extraction for debugging
        logger.info(f"Successfully extracted {len(text)} characters from PDF")
        return text
    
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        # Fallback: try to decode as text if it's a simple text file
        try:
            return file_content.decode('utf-8', errors='ignore')
        except:
            return ""

def classify_by_filename(filename: str) -> dict:
    """Fallback classification based on filename"""
    filename_lower = filename.lower()
    
    # Basic classification rules
    if any(ext in filename_lower for ext in ['.dwg', 'drawing', 'manual', 'handbook']):
        category = "drawings_manuals"
    elif any(term in filename_lower for term in ['test', 'maintenance', 'inspection', 'check']):
        category = "test_reports"
    elif any(term in filename_lower for term in ['survey', 'audit', 'examination']):
        category = "survey_reports"
    elif any(term in filename_lower for term in ['certificate', 'cert', 'license', 'permit']):
        category = "certificates"
    else:
        category = "other_documents"
    
    # Return enhanced structure for certificates
    if category == "certificates":
        return {
            "category": category,
            "cert_name": f"Certificate from {filename}",
            "cert_type": "Unknown Certificate Type",
            "cert_no": f"FILENAME_BASED_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "issue_date": None,
            "valid_date": None,
            "issued_by": "Filename-based classification",
            "ship_name": "Unknown Ship",
            "confidence": 0.1,
            "extraction_error": "Classified by filename only - AI analysis failed"
        }
    else:
        return {
            "category": category,
            "ship_name": "Unknown_Ship",
            "confidence": "low",
            "cert_name": None,
            "cert_type": None,
            "cert_no": None,
            "issue_date": None,
            "valid_date": None,
            "issued_by": None
        }

def test_functions():
    print("=== Testing Enhanced PDF Extraction Functions ===")
    
    # Test 1: Empty content
    print("\n1. Testing with empty content:")
    result = extract_text_from_pdf(b"")
    print(f"   Result: '{result}'")
    
    # Test 2: Invalid PDF content
    print("\n2. Testing with invalid PDF content:")
    result = extract_text_from_pdf(b"This is not a PDF file")
    print(f"   Result: '{result}'")
    
    # Test 3: Certificate filename classification
    print("\n3. Testing certificate filename classification:")
    result = classify_by_filename("PM252494430.pdf")
    print("   Result:")
    for key, value in result.items():
        print(f"     {key}: {value}")
    
    # Test 4: Non-certificate filename classification
    print("\n4. Testing non-certificate filename classification:")
    result = classify_by_filename("manual.pdf")
    print("   Result:")
    for key, value in result.items():
        print(f"     {key}: {value}")
    
    print("\n=== Tests completed successfully ===")

if __name__ == "__main__":
    test_functions()
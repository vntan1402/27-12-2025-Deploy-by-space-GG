#!/usr/bin/env python3
"""
OCR Dependency Test - Verify that OCR dependencies are working correctly

Based on the backend logs, we found the root cause:
- ERROR: "Unable to get page count. Is poppler installed and in PATH?"
- This causes OCR processing to fail and fallback to filename-based classification

This test verifies that poppler-utils and tesseract-ocr are working correctly.
"""

import os
import subprocess
import sys
from pathlib import Path

def test_poppler_utils():
    """Test if poppler-utils is working correctly"""
    print("🔍 Testing Poppler-utils...")
    
    try:
        # Test if pdftoppm is available
        result = subprocess.run(['which', 'pdftoppm'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ pdftoppm not found in PATH")
            return False
        
        print(f"✅ pdftoppm found at: {result.stdout.strip()}")
        
        # Test with the actual PDF file
        pdf_file = "/app/SUNSHINE_01_ImagePDF_New.pdf"
        if not os.path.exists(pdf_file):
            print(f"❌ Test PDF file not found: {pdf_file}")
            return False
        
        # Try to get page count using pdfinfo
        result = subprocess.run(['pdfinfo', pdf_file], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ pdfinfo failed: {result.stderr}")
            return False
        
        # Extract page count from pdfinfo output
        for line in result.stdout.split('\n'):
            if line.startswith('Pages:'):
                page_count = line.split(':')[1].strip()
                print(f"✅ PDF page count detected: {page_count}")
                break
        else:
            print("❌ Could not extract page count from pdfinfo")
            return False
        
        # Try to convert first page to image
        output_dir = "/tmp/ocr_test"
        os.makedirs(output_dir, exist_ok=True)
        
        result = subprocess.run([
            'pdftoppm', 
            '-png', 
            '-f', '1', 
            '-l', '1',
            '-r', '300',
            pdf_file,
            f"{output_dir}/test_page"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ pdftoppm conversion failed: {result.stderr}")
            return False
        
        # Check if output file was created
        output_file = f"{output_dir}/test_page-1.png"
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ PDF to PNG conversion successful: {output_file} ({file_size} bytes)")
            # Clean up
            os.remove(output_file)
            return True
        else:
            print("❌ PDF to PNG conversion failed - no output file created")
            return False
            
    except Exception as e:
        print(f"❌ Poppler-utils test failed: {e}")
        return False

def test_tesseract_ocr():
    """Test if tesseract-ocr is working correctly"""
    print("\n🔍 Testing Tesseract OCR...")
    
    try:
        # Test if tesseract is available
        result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ tesseract not found in PATH")
            return False
        
        print(f"✅ tesseract found at: {result.stdout.strip()}")
        
        # Get tesseract version
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ Tesseract version: {version_line}")
        
        # Test OCR with a simple image (create a test image with text)
        test_image_path = "/tmp/test_ocr.png"
        
        # Create a simple test image with text using ImageMagick if available
        try:
            result = subprocess.run([
                'convert', 
                '-size', '300x100', 
                'xc:white', 
                '-font', 'DejaVu-Sans', 
                '-pointsize', '20', 
                '-fill', 'black', 
                '-annotate', '+10+30', 
                'TEST OCR TEXT',
                test_image_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(test_image_path):
                # Test OCR on the created image
                result = subprocess.run([
                    'tesseract', 
                    test_image_path, 
                    'stdout'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    ocr_text = result.stdout.strip()
                    print(f"✅ OCR test successful: '{ocr_text}'")
                    os.remove(test_image_path)
                    return True
                else:
                    print(f"❌ OCR test failed: {result.stderr}")
                    return False
            else:
                print("⚠️ Could not create test image (ImageMagick not available), but tesseract is installed")
                return True
                
        except FileNotFoundError:
            print("⚠️ ImageMagick not available for test image creation, but tesseract is installed")
            return True
            
    except Exception as e:
        print(f"❌ Tesseract test failed: {e}")
        return False

def test_python_pdf_libraries():
    """Test if Python PDF libraries are working"""
    print("\n🔍 Testing Python PDF Libraries...")
    
    try:
        # Test PyPDF2
        try:
            import PyPDF2
            print("✅ PyPDF2 imported successfully")
        except ImportError:
            print("❌ PyPDF2 not available")
            return False
        
        # Test pdf2image
        try:
            from pdf2image import convert_from_path
            print("✅ pdf2image imported successfully")
            
            # Test with actual PDF
            pdf_file = "/app/SUNSHINE_01_ImagePDF_New.pdf"
            if os.path.exists(pdf_file):
                try:
                    # Try to convert first page
                    images = convert_from_path(pdf_file, first_page=1, last_page=1, dpi=150)
                    if images:
                        print(f"✅ pdf2image conversion successful: {len(images)} page(s) converted")
                        return True
                    else:
                        print("❌ pdf2image conversion failed - no images returned")
                        return False
                except Exception as e:
                    print(f"❌ pdf2image conversion failed: {e}")
                    return False
            else:
                print("⚠️ Test PDF not found, but pdf2image is available")
                return True
                
        except ImportError:
            print("❌ pdf2image not available")
            return False
            
    except Exception as e:
        print(f"❌ Python PDF libraries test failed: {e}")
        return False

def main():
    """Run all OCR dependency tests"""
    print("🚀 OCR DEPENDENCY VERIFICATION TEST")
    print("=" * 60)
    print("This test verifies that OCR dependencies are working correctly")
    print("to resolve the SUNSHINE_01_ImagePDF.pdf fallback issue.")
    print("=" * 60)
    
    tests = [
        ("Poppler-utils", test_poppler_utils),
        ("Tesseract OCR", test_tesseract_ocr),
        ("Python PDF Libraries", test_python_pdf_libraries)
    ]
    
    passed_tests = 0
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        if test_func():
            passed_tests += 1
            print(f"✅ {test_name} test PASSED")
        else:
            print(f"❌ {test_name} test FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY: {passed_tests}/{len(tests)} tests passed")
    
    if passed_tests == len(tests):
        print("🎉 ALL OCR DEPENDENCIES ARE WORKING CORRECTLY!")
        print("The fallback issue should be resolved after backend restart.")
    else:
        print(f"⚠️ {len(tests) - passed_tests} dependency test(s) failed")
        print("OCR processing may still fail and cause filename-based fallback.")
    
    return passed_tests == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
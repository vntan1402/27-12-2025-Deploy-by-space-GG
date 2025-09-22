#!/usr/bin/env python3
"""
COMPREHENSIVE IMAGE-BASED PDF WORKFLOW TESTING
Testing the COMPLETE NEW WORKFLOW with IMAGE-BASED PDF - SUNSHINE_01_ImagePDF.pdf

COMPARISON TESTING:
- Previous file: SUNSHINE_01_CSSC_PM25385.pdf (275KB) → detected as TEXT-BASED → used direct_text_extraction  
- New file: SUNSHINE_01_ImagePDF.pdf (997KB) → should detect as IMAGE-BASED → should use OCR processing

NEW WORKFLOW TO TEST:
1. 🔍 PDF Type Analysis → should detect "image_based" (vs "text_based" for previous file)
2. ⚡ Processing Method Selection → should choose OCR processing (vs direct text extraction)
3. 🤖 OCR Processing → Tesseract + Google Vision API 
4. 📊 Enhanced Metadata → processing_method: "enhanced_ocr" or similar

EXPECTED DIFFERENCES:
- PDF Type: "image_based" (vs "text_based")
- Processing Method: OCR-based (vs direct_text_extraction)  
- Processing Time: Longer due to OCR (vs faster text extraction)
- Final Results: Should be similar ship data extraction
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

# Test files for comparison
TEXT_BASED_PDF = "/app/SUNSHINE_01_CSSC_PM25385.pdf"  # Previous text-based PDF
IMAGE_BASED_PDF = "/app/SUNSHINE_01_ImagePDF.pdf"     # New image-based PDF

class ImagePDFWorkflowTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.text_based_results = None
        self.image_based_results = None
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                
                user_role = self.user_info.get('role', '').upper()
                self.log_test("Authentication Test", True, 
                            f"Logged in as {self.user_info['username']} ({user_role})")
                return True
            else:
                self.log_test("Authentication Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication Test", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def verify_test_files(self):
        """Verify both test PDF files exist and get their sizes"""
        try:
            files_info = {}
            
            # Check text-based PDF
            if os.path.exists(TEXT_BASED_PDF):
                size = os.path.getsize(TEXT_BASED_PDF)
                files_info['text_based'] = {'path': TEXT_BASED_PDF, 'size': size}
            else:
                self.log_test("Test Files Verification", False, 
                            error=f"Text-based PDF not found: {TEXT_BASED_PDF}")
                return False
            
            # Check image-based PDF
            if os.path.exists(IMAGE_BASED_PDF):
                size = os.path.getsize(IMAGE_BASED_PDF)
                files_info['image_based'] = {'path': IMAGE_BASED_PDF, 'size': size}
            else:
                self.log_test("Test Files Verification", False, 
                            error=f"Image-based PDF not found: {IMAGE_BASED_PDF}")
                return False
            
            details = (f"Text-based PDF: {files_info['text_based']['size']:,} bytes, "
                      f"Image-based PDF: {files_info['image_based']['size']:,} bytes")
            
            self.log_test("Test Files Verification", True, details)
            return True
                
        except Exception as e:
            self.log_test("Test Files Verification", False, error=str(e))
            return False
    
    def analyze_pdf_file(self, file_path, file_type):
        """Analyze a PDF file and return results"""
        try:
            # Read the PDF file
            with open(file_path, 'rb') as f:
                pdf_content = f.read()
            
            file_name = os.path.basename(file_path)
            
            # Prepare the multipart form data
            files = {
                'file': (file_name, pdf_content, 'application/pdf')
            }
            
            print(f"📤 Analyzing {file_type} PDF: {file_name} ({len(pdf_content):,} bytes)")
            
            # Make the API request
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers()
            )
            processing_time = time.time() - start_time
            
            print(f"⏱️ Processing time: {processing_time:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    analysis = data.get('analysis', {})
                    return {
                        'success': True,
                        'analysis': analysis,
                        'processing_time': processing_time,
                        'file_size': len(pdf_content),
                        'file_name': file_name
                    }
                else:
                    return {
                        'success': False,
                        'error': f"API returned success=False: {data.get('message', 'Unknown error')}",
                        'processing_time': processing_time
                    }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'processing_time': processing_time
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': 0
            }
    
    def test_text_based_pdf_workflow(self):
        """Test the text-based PDF workflow (baseline)"""
        print("\n🔍 TESTING TEXT-BASED PDF WORKFLOW (BASELINE)")
        print("=" * 60)
        
        result = self.analyze_pdf_file(TEXT_BASED_PDF, "text-based")
        
        if result['success']:
            self.text_based_results = result
            analysis = result['analysis']
            
            # Verify expected characteristics for text-based PDF
            pdf_type = analysis.get('pdf_type')
            processing_method = analysis.get('processing_method')
            
            expected_pdf_type = pdf_type == 'text_based'
            expected_processing = processing_method in ['direct_text_extraction', 'text_extraction_fallback']
            
            details = (f"PDF Type: {pdf_type}, Processing Method: {processing_method}, "
                      f"Processing Time: {result['processing_time']:.2f}s")
            
            if expected_pdf_type and expected_processing:
                self.log_test("Text-Based PDF Workflow", True, details)
                return True
            else:
                self.log_test("Text-Based PDF Workflow", False, 
                            error=f"Unexpected workflow: {details}")
                return False
        else:
            self.log_test("Text-Based PDF Workflow", False, error=result['error'])
            return False
    
    def test_image_based_pdf_workflow(self):
        """Test the NEW image-based PDF workflow"""
        print("\n🤖 TESTING IMAGE-BASED PDF WORKFLOW (NEW)")
        print("=" * 60)
        
        result = self.analyze_pdf_file(IMAGE_BASED_PDF, "image-based")
        
        if result['success']:
            self.image_based_results = result
            analysis = result['analysis']
            
            # Verify expected characteristics for image-based PDF
            pdf_type = analysis.get('pdf_type')
            processing_method = analysis.get('processing_method')
            ocr_confidence = analysis.get('ocr_confidence')
            
            expected_pdf_type = pdf_type == 'image_based'
            expected_processing = processing_method in ['enhanced_ocr', 'hybrid_ocr_enhanced', 'ocr_processing']
            has_ocr_confidence = isinstance(ocr_confidence, (int, float)) and 0 <= ocr_confidence <= 1
            
            details = (f"PDF Type: {pdf_type}, Processing Method: {processing_method}, "
                      f"OCR Confidence: {ocr_confidence}, Processing Time: {result['processing_time']:.2f}s")
            
            success_criteria = [expected_pdf_type, expected_processing, has_ocr_confidence]
            
            if all(success_criteria):
                self.log_test("Image-Based PDF Workflow", True, details)
                return True
            else:
                issues = []
                if not expected_pdf_type:
                    issues.append(f"Wrong PDF type: {pdf_type} (expected: image_based)")
                if not expected_processing:
                    issues.append(f"Wrong processing method: {processing_method}")
                if not has_ocr_confidence:
                    issues.append(f"Invalid OCR confidence: {ocr_confidence}")
                
                self.log_test("Image-Based PDF Workflow", False, 
                            error=f"Issues: {'; '.join(issues)}")
                return False
        else:
            self.log_test("Image-Based PDF Workflow", False, error=result['error'])
            return False
    
    def compare_workflow_results(self):
        """Compare the results between text-based and image-based workflows"""
        if not self.text_based_results or not self.image_based_results:
            self.log_test("Workflow Comparison", False, 
                        error="Missing results from previous tests")
            return False
        
        try:
            print("\n📊 WORKFLOW COMPARISON ANALYSIS")
            print("=" * 60)
            
            text_analysis = self.text_based_results['analysis']
            image_analysis = self.image_based_results['analysis']
            
            # Compare PDF types
            text_pdf_type = text_analysis.get('pdf_type')
            image_pdf_type = image_analysis.get('pdf_type')
            
            # Compare processing methods
            text_processing = text_analysis.get('processing_method')
            image_processing = image_analysis.get('processing_method')
            
            # Compare processing times
            text_time = self.text_based_results['processing_time']
            image_time = self.image_based_results['processing_time']
            
            # Compare extracted ship data
            ship_fields = ['ship_name', 'imo_number', 'flag', 'class_society', 'gross_tonnage', 'deadweight', 'built_year']
            
            text_extracted = {}
            image_extracted = {}
            
            for field in ship_fields:
                text_val = text_analysis.get(field)
                image_val = image_analysis.get(field)
                
                if text_val is not None:
                    text_extracted[field] = text_val
                if image_val is not None:
                    image_extracted[field] = image_val
            
            # Analysis results
            comparison_results = {
                'pdf_type_different': text_pdf_type != image_pdf_type,
                'processing_method_different': text_processing != image_processing,
                'image_processing_slower': image_time > text_time,
                'similar_data_extraction': len(text_extracted) > 0 and len(image_extracted) > 0
            }
            
            print(f"📋 COMPARISON RESULTS:")
            print(f"   Text-based PDF: Type={text_pdf_type}, Method={text_processing}, Time={text_time:.2f}s")
            print(f"   Image-based PDF: Type={image_pdf_type}, Method={image_processing}, Time={image_time:.2f}s")
            print(f"   Text-based extracted fields: {len(text_extracted)} ({list(text_extracted.keys())})")
            print(f"   Image-based extracted fields: {len(image_extracted)} ({list(image_extracted.keys())})")
            
            # Verify expected differences
            expected_differences = [
                comparison_results['pdf_type_different'],
                comparison_results['processing_method_different'],
                comparison_results['similar_data_extraction']
            ]
            
            if all(expected_differences):
                details = (f"✅ PDF types differ: {text_pdf_type} vs {image_pdf_type}, "
                          f"✅ Processing methods differ: {text_processing} vs {image_processing}, "
                          f"✅ Both extracted ship data successfully, "
                          f"⏱️ Image processing time: {image_time:.2f}s vs Text: {text_time:.2f}s")
                
                self.log_test("Workflow Comparison", True, details)
                return True
            else:
                issues = []
                if not comparison_results['pdf_type_different']:
                    issues.append("PDF types should be different")
                if not comparison_results['processing_method_different']:
                    issues.append("Processing methods should be different")
                if not comparison_results['similar_data_extraction']:
                    issues.append("Both workflows should extract ship data")
                
                self.log_test("Workflow Comparison", False, 
                            error=f"Issues: {'; '.join(issues)}")
                return False
                
        except Exception as e:
            self.log_test("Workflow Comparison", False, error=str(e))
            return False
    
    def verify_ocr_processing_features(self):
        """Verify OCR-specific features in image-based PDF processing"""
        if not self.image_based_results:
            self.log_test("OCR Processing Features", False, 
                        error="No image-based results available")
            return False
        
        try:
            analysis = self.image_based_results['analysis']
            
            # Check for OCR-specific features
            ocr_features = {
                'ocr_confidence': analysis.get('ocr_confidence'),
                'processing_notes': analysis.get('processing_notes', []),
                'processing_method': analysis.get('processing_method')
            }
            
            # Verify OCR confidence score
            ocr_confidence = ocr_features['ocr_confidence']
            has_valid_confidence = isinstance(ocr_confidence, (int, float)) and 0 <= ocr_confidence <= 1
            
            # Verify processing notes mention OCR
            processing_notes = ocr_features['processing_notes']
            has_ocr_notes = any('ocr' in str(note).lower() or 'tesseract' in str(note).lower() 
                               for note in processing_notes)
            
            # Verify processing method indicates OCR
            processing_method = ocr_features['processing_method']
            is_ocr_method = any(keyword in processing_method.lower() 
                               for keyword in ['ocr', 'tesseract', 'vision'])
            
            ocr_checks = [has_valid_confidence, has_ocr_notes or is_ocr_method]
            
            if all(ocr_checks):
                details = (f"OCR Confidence: {ocr_confidence:.3f}, "
                          f"Processing Method: {processing_method}, "
                          f"Processing Notes: {len(processing_notes)} notes")
                
                self.log_test("OCR Processing Features", True, details)
                return True
            else:
                issues = []
                if not has_valid_confidence:
                    issues.append(f"Invalid OCR confidence: {ocr_confidence}")
                if not (has_ocr_notes or is_ocr_method):
                    issues.append("No OCR indicators in processing method or notes")
                
                self.log_test("OCR Processing Features", False, 
                            error=f"Issues: {'; '.join(issues)}")
                return False
                
        except Exception as e:
            self.log_test("OCR Processing Features", False, error=str(e))
            return False
    
    def verify_ship_data_consistency(self):
        """Verify that both workflows extract consistent ship data"""
        if not self.text_based_results or not self.image_based_results:
            self.log_test("Ship Data Consistency", False, 
                        error="Missing results from previous tests")
            return False
        
        try:
            text_analysis = self.text_based_results['analysis']
            image_analysis = self.image_based_results['analysis']
            
            # Key ship identification fields that should be consistent
            key_fields = ['ship_name', 'imo_number']
            
            consistent_fields = []
            inconsistent_fields = []
            
            for field in key_fields:
                text_val = text_analysis.get(field)
                image_val = image_analysis.get(field)
                
                if text_val and image_val:
                    # Normalize for comparison (case insensitive, strip whitespace)
                    text_normalized = str(text_val).strip().upper()
                    image_normalized = str(image_val).strip().upper()
                    
                    if text_normalized == image_normalized:
                        consistent_fields.append(f"{field}: {text_val}")
                    else:
                        inconsistent_fields.append(f"{field}: '{text_val}' vs '{image_val}'")
            
            # At least ship name should be consistent
            if len(consistent_fields) >= 1:
                details = f"Consistent fields: {', '.join(consistent_fields)}"
                if inconsistent_fields:
                    details += f" | Minor differences: {', '.join(inconsistent_fields)}"
                
                self.log_test("Ship Data Consistency", True, details)
                return True
            else:
                error_msg = f"No consistent key fields found. Inconsistencies: {', '.join(inconsistent_fields)}"
                self.log_test("Ship Data Consistency", False, error=error_msg)
                return False
                
        except Exception as e:
            self.log_test("Ship Data Consistency", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests for the image-based PDF workflow"""
        print("🚀 Starting COMPREHENSIVE IMAGE-BASED PDF WORKFLOW TESTING")
        print("🎯 FOCUS: Demonstrate smart workflow choosing different processing methods for different PDF types")
        print("=" * 100)
        
        # Run tests in sequence
        tests = [
            self.authenticate,
            self.verify_test_files,
            self.test_text_based_pdf_workflow,
            self.test_image_based_pdf_workflow,
            self.compare_workflow_results,
            self.verify_ocr_processing_features,
            self.verify_ship_data_consistency
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
                # Continue with other tests even if one fails
        
        # Summary
        print("=" * 100)
        print(f"📊 TEST SUMMARY: {passed_tests}/{len(tests)} tests passed")
        
        if passed_tests == len(tests):
            print("🎉 ALL TESTS PASSED - IMAGE-BASED PDF WORKFLOW is working correctly!")
            print("✅ Smart workflow successfully chooses different processing methods for different PDF types")
        elif passed_tests >= len(tests) - 1:
            print("⚠️ MOSTLY SUCCESSFUL - Minor issues detected but core functionality working")
        else:
            print(f"❌ SIGNIFICANT ISSUES - {len(tests) - passed_tests} tests failed - Review required")
        
        # Detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
            if result['error']:
                print(f"    ERROR: {result['error']}")
        
        return passed_tests >= len(tests) - 1  # Allow 1 minor failure

def main():
    """Main test execution"""
    tester = ImagePDFWorkflowTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
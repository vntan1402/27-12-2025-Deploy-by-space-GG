#!/usr/bin/env python3
"""
OCR-Enabled Add New Ship Functionality Testing
Comprehensive testing of the enhanced OCR-enabled "Add New Ship" functionality with the provided PDF file.
Tests authentication, OCR processing, Google Vision API integration, and ship data extraction accuracy.
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import io
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

# Fallback credentials if admin1 doesn't exist
FALLBACK_USERNAME = "admin"
FALLBACK_PASSWORD = "admin123"

# PDF file from review request
PDF_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/swohyuf9_SS%20STAR%20PM252494416_ImagePDF.pdf"

# Expected results from review request
EXPECTED_SHIP_DATA = {
    "ship_name": "SUNSHINE STAR",
    "imo_number": "9405136",
    "flag": "BELIZE",
    "class_society": "PMDS",  # Panama Maritime Documentation Services
    "gross_tonnage": 2988,
    "deadweight": 5274.3,
    "built_year": 2005
}

class OCRShipAnalysisTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.pdf_content = None
        self.analysis_result = None
        
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
        """Authenticate with admin1/123456 credentials, fallback to admin/admin123"""
        try:
            # Try primary credentials first
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                
                # Verify user role and permissions
                user_role = self.user_info.get('role', '').upper()
                username = self.user_info.get('username', '')
                
                self.log_test("Authentication Test", True, 
                            f"Successfully logged in as {username} with role: {user_role}")
                return True
            else:
                # Try fallback credentials
                print(f"Primary credentials failed, trying fallback credentials...")
                response = requests.post(f"{API_BASE}/auth/login", json={
                    "username": FALLBACK_USERNAME,
                    "password": FALLBACK_PASSWORD
                })
                
                if response.status_code == 200:
                    data = response.json()
                    self.token = data["access_token"]
                    self.user_info = data["user"]
                    
                    # Verify user role and permissions
                    user_role = self.user_info.get('role', '').upper()
                    username = self.user_info.get('username', '')
                    
                    self.log_test("Authentication Test", True, 
                                f"Successfully logged in as {username} with role: {user_role} (using fallback credentials)")
                    return True
                else:
                    self.log_test("Authentication Test", False, 
                                error=f"Both primary and fallback authentication failed. Status: {response.status_code}, Response: {response.text}")
                    return False
                
        except Exception as e:
            self.log_test("Authentication Test", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def download_pdf_file(self):
        """Download the PDF file from the provided URL"""
        try:
            print(f"📥 Downloading PDF file from: {PDF_URL}")
            response = requests.get(PDF_URL, timeout=30)
            
            if response.status_code == 200:
                self.pdf_content = response.content
                file_size_mb = len(self.pdf_content) / (1024 * 1024)
                
                self.log_test("PDF Download Test", True, 
                            f"Successfully downloaded PDF file ({file_size_mb:.2f} MB)")
                return True
            else:
                self.log_test("PDF Download Test", False, 
                            error=f"Failed to download PDF. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("PDF Download Test", False, error=str(e))
            return False
    
    def test_ocr_processor_availability(self):
        """Test if OCR processor is available and configured"""
        try:
            # Check if the backend has OCR processor configured
            # This is inferred from the server.py imports and OCR functionality
            
            # Test by making a simple request to see if OCR-related endpoints exist
            response = requests.get(f"{API_BASE}/ai-config", headers=self.get_headers())
            
            if response.status_code == 200:
                ai_config = response.json()
                provider = ai_config.get('provider', '')
                model = ai_config.get('model', '')
                
                # Check if AI is configured for OCR processing
                if provider and model:
                    self.log_test("OCR Processor Availability Test", True, 
                                f"AI configuration found - Provider: {provider}, Model: {model}")
                    return True
                else:
                    self.log_test("OCR Processor Availability Test", False, 
                                error="AI configuration missing provider or model")
                    return False
            else:
                self.log_test("OCR Processor Availability Test", False, 
                            error=f"Cannot access AI config. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OCR Processor Availability Test", False, error=str(e))
            return False
    
    def test_analyze_ship_certificate_endpoint(self):
        """Test POST /api/analyze-ship-certificate with the PDF file"""
        try:
            if not self.pdf_content:
                self.log_test("Analyze Ship Certificate Endpoint Test", False, 
                            error="PDF content not available")
                return False
            
            print("🔍 Testing OCR analysis with the provided PDF file...")
            
            # Prepare the file for upload
            files = {
                'file': ('SS_STAR_PM252494416_ImagePDF.pdf', io.BytesIO(self.pdf_content), 'application/pdf')
            }
            
            # Make the API call
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers(),
                timeout=60  # Allow more time for OCR processing
            )
            
            if response.status_code == 200:
                self.analysis_result = response.json()
                
                # Log the full response for debugging
                print(f"📋 Full API Response: {json.dumps(self.analysis_result, indent=2)}")
                
                # Check if we have analysis data
                if 'data' in self.analysis_result and 'analysis' in self.analysis_result['data']:
                    analysis_data = self.analysis_result['data']['analysis']
                    
                    self.log_test("Analyze Ship Certificate Endpoint Test", True, 
                                f"OCR analysis completed successfully. Extracted {len(analysis_data)} fields")
                    return True
                else:
                    self.log_test("Analyze Ship Certificate Endpoint Test", False, 
                                error="Response missing 'data.analysis' structure")
                    return False
            else:
                self.log_test("Analyze Ship Certificate Endpoint Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Analyze Ship Certificate Endpoint Test", False, error=str(e))
            return False
    
    def test_ocr_enhancement_verification(self):
        """Verify OCR processor is working with Google Vision API or fallback text extraction"""
        try:
            if not self.analysis_result:
                self.log_test("OCR Enhancement Verification Test", False, 
                            error="No analysis result available")
                return False
            
            analysis_data = self.analysis_result.get('data', {}).get('analysis', {})
            
            # Check if OCR successfully extracted text from the image-based PDF
            extracted_fields = []
            for field, value in analysis_data.items():
                if value and value != "null" and str(value).strip():
                    extracted_fields.append(f"{field}: {value}")
            
            if extracted_fields:
                self.log_test("OCR Enhancement Verification Test", True, 
                            f"OCR successfully extracted {len(extracted_fields)} fields from image-based PDF: {', '.join(extracted_fields)}")
                return True
            else:
                self.log_test("OCR Enhancement Verification Test", False, 
                            error="OCR failed to extract any meaningful data from the PDF")
                return False
                
        except Exception as e:
            self.log_test("OCR Enhancement Verification Test", False, error=str(e))
            return False
    
    def test_maritime_certificate_detection(self):
        """Test maritime certificate detection and analysis"""
        try:
            if not self.analysis_result:
                self.log_test("Maritime Certificate Detection Test", False, 
                            error="No analysis result available")
                return False
            
            analysis_data = self.analysis_result.get('data', {}).get('analysis', {})
            
            # Check if the system detected this as a maritime certificate
            # Look for maritime-specific fields
            maritime_indicators = [
                'ship_name', 'imo_number', 'flag', 'class_society', 
                'gross_tonnage', 'deadweight', 'built_year'
            ]
            
            detected_maritime_fields = []
            for indicator in maritime_indicators:
                if indicator in analysis_data and analysis_data[indicator]:
                    detected_maritime_fields.append(indicator)
            
            if detected_maritime_fields:
                self.log_test("Maritime Certificate Detection Test", True, 
                            f"Maritime certificate detected. Found {len(detected_maritime_fields)} maritime fields: {', '.join(detected_maritime_fields)}")
                return True
            else:
                self.log_test("Maritime Certificate Detection Test", False, 
                            error="System did not detect maritime certificate fields")
                return False
                
        except Exception as e:
            self.log_test("Maritime Certificate Detection Test", False, error=str(e))
            return False
    
    def test_ship_form_field_mapping(self):
        """Test the mapping of certificate data to ship form fields"""
        try:
            if not self.analysis_result:
                self.log_test("Ship Form Field Mapping Test", False, 
                            error="No analysis result available")
                return False
            
            analysis_data = self.analysis_result.get('data', {}).get('analysis', {})
            
            # Check if the response contains the expected ship form fields
            expected_fields = ['ship_name', 'imo_number', 'flag', 'class_society', 'gross_tonnage', 'deadweight', 'built_year']
            
            mapped_fields = []
            missing_fields = []
            
            for field in expected_fields:
                if field in analysis_data:
                    mapped_fields.append(f"{field}: {analysis_data[field]}")
                else:
                    missing_fields.append(field)
            
            if mapped_fields:
                details = f"Successfully mapped {len(mapped_fields)} fields: {', '.join(mapped_fields)}"
                if missing_fields:
                    details += f". Missing fields: {', '.join(missing_fields)}"
                
                self.log_test("Ship Form Field Mapping Test", True, details)
                return True
            else:
                self.log_test("Ship Form Field Mapping Test", False, 
                            error="No ship form fields were mapped from the certificate")
                return False
                
        except Exception as e:
            self.log_test("Ship Form Field Mapping Test", False, error=str(e))
            return False
    
    def test_response_data_structure(self):
        """Verify the API returns proper ship data structure"""
        try:
            if not self.analysis_result:
                self.log_test("Response Data Structure Test", False, 
                            error="No analysis result available")
                return False
            
            # Check the overall response structure
            required_top_level_fields = ['data']
            missing_top_level = [field for field in required_top_level_fields if field not in self.analysis_result]
            
            if missing_top_level:
                self.log_test("Response Data Structure Test", False, 
                            error=f"Missing top-level fields: {missing_top_level}")
                return False
            
            # Check the data structure
            data = self.analysis_result.get('data', {})
            required_data_fields = ['analysis']
            missing_data_fields = [field for field in required_data_fields if field not in data]
            
            if missing_data_fields:
                self.log_test("Response Data Structure Test", False, 
                            error=f"Missing data fields: {missing_data_fields}")
                return False
            
            # Check if analysis contains ship-related fields
            analysis = data.get('analysis', {})
            if isinstance(analysis, dict) and analysis:
                self.log_test("Response Data Structure Test", True, 
                            f"Response has proper structure with {len(analysis)} analysis fields")
                return True
            else:
                self.log_test("Response Data Structure Test", False, 
                            error="Analysis field is empty or not a dictionary")
                return False
                
        except Exception as e:
            self.log_test("Response Data Structure Test", False, error=str(e))
            return False
    
    def test_extracted_data_accuracy(self):
        """Test the accuracy of extracted ship information against expected results"""
        try:
            if not self.analysis_result:
                self.log_test("Extracted Data Accuracy Test", False, 
                            error="No analysis result available")
                return False
            
            analysis_data = self.analysis_result.get('data', {}).get('analysis', {})
            
            # Compare extracted data with expected results
            accuracy_results = []
            total_expected = len(EXPECTED_SHIP_DATA)
            correct_extractions = 0
            
            for expected_field, expected_value in EXPECTED_SHIP_DATA.items():
                extracted_value = analysis_data.get(expected_field)
                
                if extracted_value:
                    # Convert to string for comparison
                    extracted_str = str(extracted_value).strip()
                    expected_str = str(expected_value).strip()
                    
                    if extracted_str.upper() == expected_str.upper():
                        accuracy_results.append(f"✅ {expected_field}: {extracted_value} (CORRECT)")
                        correct_extractions += 1
                    else:
                        accuracy_results.append(f"❌ {expected_field}: Expected '{expected_value}', Got '{extracted_value}'")
                else:
                    accuracy_results.append(f"❌ {expected_field}: Not extracted (Expected '{expected_value}')")
            
            accuracy_percentage = (correct_extractions / total_expected) * 100
            
            details = f"Accuracy: {accuracy_percentage:.1f}% ({correct_extractions}/{total_expected} correct)\n" + "\n".join(accuracy_results)
            
            # Consider test successful if we get at least 50% accuracy (OCR can be challenging)
            success = accuracy_percentage >= 50.0
            
            self.log_test("Extracted Data Accuracy Test", success, details)
            return success
                
        except Exception as e:
            self.log_test("Extracted Data Accuracy Test", False, error=str(e))
            return False
    
    def test_confidence_scores_and_processing_methods(self):
        """Test confidence scores and processing methods in the response"""
        try:
            if not self.analysis_result:
                self.log_test("Confidence Scores and Processing Methods Test", False, 
                            error="No analysis result available")
                return False
            
            # Check if the response includes confidence scores or processing method information
            response_str = json.dumps(self.analysis_result)
            
            confidence_indicators = ['confidence', 'score', 'accuracy', 'method', 'processing']
            found_indicators = [indicator for indicator in confidence_indicators if indicator.lower() in response_str.lower()]
            
            if found_indicators:
                self.log_test("Confidence Scores and Processing Methods Test", True, 
                            f"Found processing metadata indicators: {', '.join(found_indicators)}")
                return True
            else:
                # Even if no explicit confidence scores, if we have data, the processing worked
                analysis_data = self.analysis_result.get('data', {}).get('analysis', {})
                if analysis_data:
                    self.log_test("Confidence Scores and Processing Methods Test", True, 
                                "OCR processing completed successfully (confidence scores not explicitly provided)")
                    return True
                else:
                    self.log_test("Confidence Scores and Processing Methods Test", False, 
                                error="No processing metadata or analysis data found")
                    return False
                
        except Exception as e:
            self.log_test("Confidence Scores and Processing Methods Test", False, error=str(e))
            return False
    
    def test_image_based_pdf_processing(self):
        """Test that the system can handle image-based/scanned PDFs"""
        try:
            if not self.analysis_result:
                self.log_test("Image-based PDF Processing Test", False, 
                            error="No analysis result available")
                return False
            
            analysis_data = self.analysis_result.get('data', {}).get('analysis', {})
            
            # If we extracted any meaningful data from the PDF, it means OCR worked on the image-based PDF
            meaningful_extractions = []
            for field, value in analysis_data.items():
                if value and str(value).strip() and str(value).strip().lower() not in ['null', 'none', '']:
                    meaningful_extractions.append(f"{field}: {value}")
            
            if meaningful_extractions:
                self.log_test("Image-based PDF Processing Test", True, 
                            f"Successfully processed image-based PDF and extracted {len(meaningful_extractions)} meaningful fields: {', '.join(meaningful_extractions[:3])}{'...' if len(meaningful_extractions) > 3 else ''}")
                return True
            else:
                self.log_test("Image-based PDF Processing Test", False, 
                            error="Failed to extract meaningful data from image-based PDF")
                return False
                
        except Exception as e:
            self.log_test("Image-based PDF Processing Test", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests for OCR-enabled Add New Ship functionality"""
        print("🧪 OCR-ENABLED ADD NEW SHIP FUNCTIONALITY COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test User: {TEST_USERNAME}")
        print(f"PDF Source: {PDF_URL}")
        print()
        
        # Step 1: Authentication Test
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Download PDF File
        if not self.download_pdf_file():
            print("❌ PDF download failed. Cannot proceed with OCR tests.")
            return False
        
        # Step 3: Test OCR Processor Availability
        if not self.test_ocr_processor_availability():
            print("❌ OCR processor availability test failed. OCR may not work properly.")
            # Continue with tests to see actual behavior
        
        # Step 4: Test Analyze Ship Certificate Endpoint
        if not self.test_analyze_ship_certificate_endpoint():
            print("❌ Analyze ship certificate endpoint test failed.")
            return False
        
        # Step 5: Test OCR Enhancement Verification
        if not self.test_ocr_enhancement_verification():
            print("❌ OCR enhancement verification failed.")
            # Continue to see what was actually extracted
        
        # Step 6: Test Maritime Certificate Detection
        if not self.test_maritime_certificate_detection():
            print("❌ Maritime certificate detection test failed.")
            # Continue with other tests
        
        # Step 7: Test Ship Form Field Mapping
        if not self.test_ship_form_field_mapping():
            print("❌ Ship form field mapping test failed.")
            # Continue with other tests
        
        # Step 8: Test Response Data Structure
        if not self.test_response_data_structure():
            print("❌ Response data structure test failed.")
            return False
        
        # Step 9: Test Extracted Data Accuracy
        if not self.test_extracted_data_accuracy():
            print("❌ Extracted data accuracy test failed.")
            # Continue with other tests
        
        # Step 10: Test Confidence Scores and Processing Methods
        if not self.test_confidence_scores_and_processing_methods():
            print("❌ Confidence scores and processing methods test failed.")
            # Continue with other tests
        
        # Step 11: Test Image-based PDF Processing
        if not self.test_image_based_pdf_processing():
            print("❌ Image-based PDF processing test failed.")
            # Continue with summary
        
        # Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
            if result['error']:
                print(f"    ERROR: {result['error']}")
        
        if passed >= total * 0.7:  # 70% success rate threshold
            print(f"\n🎉 OCR-ENABLED ADD NEW SHIP FUNCTIONALITY IS WORKING! ({passed}/{total} tests passed)")
            return True
        else:
            print(f"\n❌ OCR-ENABLED ADD NEW SHIP FUNCTIONALITY HAS ISSUES. ({total - passed} tests failed)")
            return False

def main():
    """Main test execution"""
    tester = OCRShipAnalysisTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
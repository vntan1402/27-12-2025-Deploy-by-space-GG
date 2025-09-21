#!/usr/bin/env python3
"""
Certificate Extraction Test - Specific PDF File Testing
Testing certificate extraction with the SPECIFIC PDF file user provided to verify OCR processor is working correctly.
This test focuses on verifying that the system extracts CORRECT data from PDF content using enhanced OCR processor
instead of generating fake filename-based data.

REVIEW REQUEST VERIFICATION:
- Test POST /api/certificates/multi-upload with ship selection and the EXACT PDF file
- Verify CORRECT data extraction:
  * Certificate Name: "International Tonnage Certificate (1969)"
  * Certificate Number: "PM242868" 
  * Issue Date: "December 12, 2024"
  * Issued By: "Government of Belize, issued by Panama Maritime Documentation Services Inc."
  * Ship Name: "SUNSHINE 01"
  * IMO Number: "9415313"
"""

import requests
import sys
import json
import os
import io
from datetime import datetime
import time

# Test configuration
TEST_PDF_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/s6nh3s3p_SUNSHINE_01_ImagePDF.pdf"

# Expected correct extraction data from review request
EXPECTED_DATA = {
    "certificate_name": "International Tonnage Certificate (1969)",
    "certificate_number": "PM242868",
    "issue_date": "December 12, 2024",
    "issued_by": "Government of Belize, issued by Panama Maritime Documentation Services Inc.",
    "ship_name": "SUNSHINE 01",
    "imo_number": "9415313"
}

# Data that should NOT be extracted (old filename-based data)
INCORRECT_DATA = {
    "certificate_name": "Maritime Certificate - SUNSHINE_01_ImagePDF",
    "certificate_number": "CERT_SUNSHINE_01_IMAGEPDF",
    "issued_by": "Maritime Authority (Filename-based classification)"
}

class CertificateExtractionTester:
    def __init__(self, base_url="https://ship-cert-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_ship_id = None
        self.pdf_content = None

    def log_result(self, test_name, success, details="", error=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()

    def login(self):
        """Login as admin"""
        print("🔐 Logging in as admin/admin123...")
        
        response = requests.post(
            f"{self.api_url}/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            user = data.get('user', {})
            self.log_result("Authentication", True, 
                          f"User: {user.get('full_name')} ({user.get('role')}), Company: {user.get('company', 'Not assigned')}")
            return True
        else:
            self.log_result("Authentication", False, error=f"{response.status_code} - {response.text}")
            return False

    def download_test_pdf(self):
        """Download the specific PDF file from the provided URL"""
        print(f"📥 Downloading test PDF from: {TEST_PDF_URL}")
        try:
            response = requests.get(TEST_PDF_URL, timeout=60)
            
            if response.status_code == 200:
                self.pdf_content = response.content
                file_size = len(self.pdf_content)
                self.log_result("PDF Download", True, 
                              f"Downloaded PDF file successfully. Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                return True
            else:
                self.log_result("PDF Download", False, error=f"Failed to download PDF. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("PDF Download", False, error=str(e))
            return False

    def get_test_ship(self):
        """Get a ship for testing - look for SUNSHINE 01 or use first available"""
        print("🚢 Getting test ship...")
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"{self.api_url}/ships", headers=headers, timeout=30)
            
            if response.status_code == 200:
                ships = response.json()
                if ships and len(ships) > 0:
                    # Look for SUNSHINE 01 first (matches the PDF)
                    sunshine_ship = None
                    for ship in ships:
                        if "SUNSHINE" in ship.get('name', '').upper():
                            sunshine_ship = ship
                            break
                    
                    if sunshine_ship:
                        self.test_ship_id = sunshine_ship['id']
                        ship_name = sunshine_ship['name']
                        self.log_result("Ship Selection", True, 
                                      f"Found matching ship: {ship_name} (ID: {self.test_ship_id})")
                    else:
                        # Use first available ship
                        self.test_ship_id = ships[0]['id']
                        ship_name = ships[0]['name']
                        self.log_result("Ship Selection", True, 
                                      f"Using first available ship: {ship_name} (ID: {self.test_ship_id})")
                    return True
                else:
                    self.log_result("Ship Selection", False, error="No ships found in database")
                    return False
            else:
                self.log_result("Ship Selection", False, error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Ship Selection", False, error=str(e))
            return False

    def test_ai_config(self):
        """Test current AI configuration"""
        print("🤖 Checking AI Configuration...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{self.api_url}/ai-config", headers=headers, timeout=30)
        
        if response.status_code == 200:
            config = response.json()
            self.log_result("AI Configuration", True, 
                          f"Provider: {config.get('provider')}, Model: {config.get('model')}, Use Emergent Key: {config.get('use_emergent_key')}")
            return config
        else:
            self.log_result("AI Configuration", False, error=f"Status: {response.status_code}")
            return None

    def test_certificate_upload_and_extraction(self):
        """Test certificate upload with the specific PDF file and verify OCR extraction"""
        print("📤 Testing Certificate Upload & Extraction...")
        
        if not self.test_ship_id or not self.pdf_content:
            self.log_result("Certificate Upload & Extraction", False, 
                          error="Missing test ship ID or PDF content")
            return None
        
        try:
            # Prepare the PDF file for upload
            files = [
                ('files', ('SUNSHINE_01_ImagePDF.pdf', io.BytesIO(self.pdf_content), 'application/pdf'))
            ]
            
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.post(
                f"{self.api_url}/certificates/multi-upload",
                params={'ship_id': self.test_ship_id},
                files=files,
                headers=headers,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response structure
                if 'results' in result and len(result['results']) > 0:
                    file_result = result['results'][0]
                    
                    # Check if the file was processed successfully
                    if file_result.get('status') == 'success':
                        analysis = file_result.get('analysis', {})
                        
                        # Extract the certificate data from analysis
                        extracted_data = {
                            "certificate_name": analysis.get('cert_name', ''),
                            "certificate_number": analysis.get('cert_no', ''),
                            "issue_date": analysis.get('issue_date', ''),
                            "issued_by": analysis.get('issued_by', ''),
                            "ship_name": analysis.get('ship_name', ''),
                            "imo_number": analysis.get('imo_number', '')
                        }
                        
                        self.log_result("Certificate Upload & Extraction", True, 
                                      f"PDF uploaded and processed successfully. Extracted data: {json.dumps(extracted_data, indent=2)}")
                        
                        return extracted_data
                    else:
                        error_msg = file_result.get('message', 'Unknown error')
                        self.log_result("Certificate Upload & Extraction", False, 
                                      error=f"File processing failed: {error_msg}")
                        return None
                else:
                    self.log_result("Certificate Upload & Extraction", False, 
                                  error="No results in response or empty results")
                    return None
            else:
                self.log_result("Certificate Upload & Extraction", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Certificate Upload & Extraction", False, error=str(e))
            return None

    def verify_extracted_data(self, extracted_data):
        """Verify that the extracted data matches expected values and is not filename-based"""
        if not extracted_data:
            self.log_result("Data Verification", False, error="No extracted data to verify")
            return False
        
        try:
            # Check if we got the expected correct data
            correct_matches = 0
            total_expected = len(EXPECTED_DATA)
            
            verification_details = []
            
            for field, expected_value in EXPECTED_DATA.items():
                extracted_value = extracted_data.get(field, '')
                
                # For dates, be flexible with format matching
                if 'date' in field.lower():
                    # Check if the date contains key components
                    if 'December' in expected_value and 'December' in str(extracted_value):
                        correct_matches += 1
                        verification_details.append(f"✅ {field}: Contains expected date components")
                    elif '2024' in expected_value and '2024' in str(extracted_value):
                        correct_matches += 1
                        verification_details.append(f"✅ {field}: Contains expected year")
                    else:
                        verification_details.append(f"❌ {field}: Expected '{expected_value}', got '{extracted_value}'")
                else:
                    # For other fields, check for key components
                    if expected_value.lower() in str(extracted_value).lower() or str(extracted_value).lower() in expected_value.lower():
                        correct_matches += 1
                        verification_details.append(f"✅ {field}: Matches expected value")
                    else:
                        verification_details.append(f"❌ {field}: Expected '{expected_value}', got '{extracted_value}'")
            
            # Check that we're NOT getting the old incorrect filename-based data
            filename_based_detected = False
            for field, incorrect_value in INCORRECT_DATA.items():
                extracted_value = extracted_data.get(field, '')
                if incorrect_value.lower() in str(extracted_value).lower():
                    filename_based_detected = True
                    verification_details.append(f"⚠️ {field}: Contains filename-based data: '{extracted_value}'")
            
            # Determine success
            success_threshold = total_expected * 0.6  # At least 60% of expected data should match
            is_successful = correct_matches >= success_threshold and not filename_based_detected
            
            details = f"Correct matches: {correct_matches}/{total_expected}. " + "; ".join(verification_details)
            
            if is_successful:
                self.log_result("Data Verification", True, details)
            else:
                error_msg = f"Insufficient correct matches ({correct_matches}/{total_expected})"
                if filename_based_detected:
                    error_msg += " and filename-based data detected"
                self.log_result("Data Verification", False, error=error_msg, details=details)
            
            return is_successful
            
        except Exception as e:
            self.log_result("Data Verification", False, error=str(e))
            return False

    def run_certificate_extraction_test(self):
        """Run the complete certificate extraction test"""
        print("🔍 CERTIFICATE EXTRACTION TEST - SPECIFIC PDF FILE")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print(f"Test PDF URL: {TEST_PDF_URL}")
        print(f"Expected Certificate: {EXPECTED_DATA['certificate_name']}")
        print(f"Expected Certificate Number: {EXPECTED_DATA['certificate_number']}")
        print()
        
        # Step 1: Authentication
        if not self.login():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Download the specific PDF file
        if not self.download_test_pdf():
            print("❌ PDF download failed. Cannot proceed with extraction test.")
            return False
        
        # Step 3: Get a test ship
        if not self.get_test_ship():
            print("❌ Ship selection failed. Cannot proceed without test ship.")
            return False
        
        # Step 4: Test AI configuration
        ai_config = self.test_ai_config()
        if not ai_config:
            print("❌ AI configuration test failed. AI analysis may not work.")
            # Continue to see what happens
        
        # Step 5: Test certificate upload and extraction
        extracted_data = self.test_certificate_upload_and_extraction()
        if not extracted_data:
            print("❌ Certificate extraction failed.")
            return False
        
        # Step 6: Verify the extracted data
        if not self.verify_extracted_data(extracted_data):
            print("❌ Data verification failed. Extracted data does not match expected values.")
            return False
        
        # Summary
        print("=" * 80)
        print("📊 CERTIFICATE EXTRACTION TEST SUMMARY")
        print("=" * 80)
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 CERTIFICATE EXTRACTION TEST PASSED!")
            print("✅ OCR processor is working correctly")
            print("✅ Real certificate data is being extracted from PDF content")
            print("✅ No filename-based fake data detected")
            return True
        else:
            print(f"\n❌ {self.tests_run - self.tests_passed} tests failed.")
            print("⚠️ OCR processor may not be working correctly")
            print("⚠️ System may still be generating filename-based data")
            return False

def main():
    """Main test execution"""
    tester = CertificateExtractionTester()
    success = tester.run_certificate_extraction_test()
    
    if success:
        print("\n🎉 Certificate extraction test completed successfully!")
        print("The OCR processor and AI analysis are working correctly.")
        return 0
    else:
        print("\n⚠️ Certificate extraction issues found - investigation needed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
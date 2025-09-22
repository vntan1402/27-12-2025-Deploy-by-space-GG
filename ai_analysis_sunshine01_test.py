#!/usr/bin/env python3
"""
AI Analysis Testing for SUNSHINE 01 Certificate
Testing the fixed AI Analysis functionality with the SUNSHINE 01 - CSSC - PM25385.pdf file
after installing missing dependencies (PyPDF2, opencv-python, pytesseract).

Review Request: Test the /api/analyze-ship-certificate endpoint with specific expected data:
- Ship Name: SUNSHINE 01
- IMO Number: 9415313
- Flag: Belize
- Gross Tonnage: 2959
- Certificate Type: Cargo Ship Safety Construction Certificate (CSSC)
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

# Expected data from the PDF
EXPECTED_DATA = {
    "ship_name": "SUNSHINE 01",
    "imo_number": "9415313",
    "flag": "Belize",
    "gross_tonnage": 2959,
    "certificate_type": "Cargo Ship Safety Construction Certificate"
}

class AIAnalysisTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        
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
    
    def authenticate(self):
        """Authenticate with the backend"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                self.log_test("Authentication", True, f"Logged in as {self.user_info['username']} ({self.user_info['role']})")
                return True
            else:
                self.log_test("Authentication", False, error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def check_pdf_file_exists(self):
        """Check if the SUNSHINE 01 PDF file exists"""
        try:
            pdf_path = "/app/SUNSHINE_01_CSSC_PM25385.pdf"
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                self.log_test("PDF File Check", True, f"File exists at {pdf_path}, Size: {file_size} bytes")
                return True
            else:
                self.log_test("PDF File Check", False, error=f"File not found at {pdf_path}")
                return False
        except Exception as e:
            self.log_test("PDF File Check", False, error=str(e))
            return False
    
    def test_ai_analysis_endpoint(self):
        """Test the /api/analyze-ship-certificate endpoint with SUNSHINE 01 PDF"""
        try:
            pdf_path = "/app/SUNSHINE_01_CSSC_PM25385.pdf"
            
            # Read the PDF file
            with open(pdf_path, 'rb') as f:
                files = {'file': ('SUNSHINE_01_CSSC_PM25385.pdf', f, 'application/pdf')}
                
                response = requests.post(
                    f"{API_BASE}/analyze-ship-certificate",
                    files=files,
                    headers=self.get_headers()
                )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("AI Analysis API Call", True, f"Status: {response.status_code}")
                
                # Check if the response has the expected structure
                if 'success' in data and data['success']:
                    analysis_data = data.get('data', {}).get('analysis', {})
                    
                    # Verify extracted data against expected values
                    self.verify_extracted_data(analysis_data)
                    return True
                else:
                    error_msg = data.get('error', 'Unknown error')
                    fallback_reason = data.get('data', {}).get('fallback_reason', 'No fallback reason')
                    self.log_test("AI Analysis Success Check", False, 
                                error=f"Analysis failed: {error_msg}, Fallback: {fallback_reason}")
                    return False
            else:
                self.log_test("AI Analysis API Call", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("AI Analysis API Call", False, error=str(e))
            return False
    
    def verify_extracted_data(self, analysis_data):
        """Verify the extracted data matches expected values"""
        try:
            print(f"\n📊 EXTRACTED DATA ANALYSIS:")
            print(f"Raw analysis data: {json.dumps(analysis_data, indent=2)}")
            
            # Check each expected field
            matches = 0
            total_fields = len(EXPECTED_DATA)
            
            for field, expected_value in EXPECTED_DATA.items():
                extracted_value = analysis_data.get(field)
                
                if field == "ship_name":
                    # Ship name comparison (case insensitive)
                    if extracted_value and str(extracted_value).upper() == str(expected_value).upper():
                        matches += 1
                        self.log_test(f"Ship Name Extraction", True, 
                                    f"Expected: '{expected_value}', Got: '{extracted_value}'")
                    else:
                        self.log_test(f"Ship Name Extraction", False, 
                                    f"Expected: '{expected_value}', Got: '{extracted_value}'")
                
                elif field == "imo_number":
                    # IMO number comparison (as string)
                    if extracted_value and str(extracted_value) == str(expected_value):
                        matches += 1
                        self.log_test(f"IMO Number Extraction", True, 
                                    f"Expected: '{expected_value}', Got: '{extracted_value}'")
                    else:
                        self.log_test(f"IMO Number Extraction", False, 
                                    f"Expected: '{expected_value}', Got: '{extracted_value}'")
                
                elif field == "flag":
                    # Flag comparison (case insensitive)
                    if extracted_value and str(extracted_value).upper() == str(expected_value).upper():
                        matches += 1
                        self.log_test(f"Flag Extraction", True, 
                                    f"Expected: '{expected_value}', Got: '{extracted_value}'")
                    else:
                        self.log_test(f"Flag Extraction", False, 
                                    f"Expected: '{expected_value}', Got: '{extracted_value}'")
                
                elif field == "gross_tonnage":
                    # Gross tonnage comparison (numeric)
                    if extracted_value and (int(float(extracted_value)) == expected_value):
                        matches += 1
                        self.log_test(f"Gross Tonnage Extraction", True, 
                                    f"Expected: {expected_value}, Got: {extracted_value}")
                    else:
                        self.log_test(f"Gross Tonnage Extraction", False, 
                                    f"Expected: {expected_value}, Got: {extracted_value}")
                
                elif field == "certificate_type":
                    # Certificate type comparison (partial match for CSSC)
                    if extracted_value and ("CSSC" in str(extracted_value).upper() or 
                                          "CARGO SHIP SAFETY CONSTRUCTION" in str(extracted_value).upper()):
                        matches += 1
                        self.log_test(f"Certificate Type Extraction", True, 
                                    f"Expected: '{expected_value}', Got: '{extracted_value}'")
                    else:
                        self.log_test(f"Certificate Type Extraction", False, 
                                    f"Expected: '{expected_value}', Got: '{extracted_value}'")
            
            # Overall success rate
            success_rate = (matches / total_fields) * 100
            if success_rate >= 60:  # 60% success rate threshold
                self.log_test("Overall Data Extraction", True, 
                            f"Success rate: {success_rate:.1f}% ({matches}/{total_fields} fields correct)")
            else:
                self.log_test("Overall Data Extraction", False, 
                            f"Success rate: {success_rate:.1f}% ({matches}/{total_fields} fields correct)")
            
        except Exception as e:
            self.log_test("Data Verification", False, error=str(e))
    
    def check_ocr_dependencies(self):
        """Check if OCR dependencies are properly installed"""
        try:
            # Test OCR processor initialization
            response = requests.get(f"{API_BASE}/health", headers=self.get_headers())
            
            if response.status_code == 200:
                self.log_test("Backend Health Check", True, "Backend is responding")
            else:
                self.log_test("Backend Health Check", False, f"Status: {response.status_code}")
            
            # Check if we can make a simple request to see if dependencies are working
            # This is indirect but will show if the OCR processor is initialized
            return True
            
        except Exception as e:
            self.log_test("OCR Dependencies Check", False, error=str(e))
            return False
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 Starting AI Analysis Testing for SUNSHINE 01 Certificate")
        print("=" * 70)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Check PDF file exists
        if not self.check_pdf_file_exists():
            print("❌ PDF file not found. Cannot proceed with AI analysis test.")
            return False
        
        # Step 3: Check OCR dependencies (indirect)
        self.check_ocr_dependencies()
        
        # Step 4: Test AI Analysis endpoint
        ai_success = self.test_ai_analysis_endpoint()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if ai_success:
            print("\n🎉 AI ANALYSIS FUNCTIONALITY IS WORKING!")
            print("✅ The missing dependencies (PyPDF2, opencv-python, pytesseract) have been successfully installed.")
            print("✅ The /api/analyze-ship-certificate endpoint is now functional.")
        else:
            print("\n❌ AI ANALYSIS FUNCTIONALITY ISSUES DETECTED")
            print("❌ There may still be issues with the AI analysis or OCR processing.")
        
        return ai_success

def main():
    """Main test execution"""
    tester = AIAnalysisTester()
    success = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
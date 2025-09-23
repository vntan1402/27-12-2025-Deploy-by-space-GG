#!/usr/bin/env python3
"""
Load Line Certificate Classification Test - Direct Function Testing

Testing the analyze_document_with_ai function directly to see why Load Line Certificate
is not being classified as "certificates" category.

This test will:
1. Call the multi-cert upload endpoint directly with the Load Line Certificate
2. Check the classification result
3. Debug the AI analysis response
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

# Test file from review request
TEST_PDF_FILE = "/app/SUNSHINE_01_ILL_PM25826.pdf"
SHIP_ID = "e21c71a2-9543-4f92-990c-72f54292fde8"  # SUNSHINE 01 ship ID

class LoadLineCertificateClassificationTester:
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
        print()
    
    def authenticate(self):
        """Authenticate with admin1 credentials"""
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
    
    def test_multi_cert_upload_classification(self):
        """Test multi-cert upload to see the exact classification behavior"""
        try:
            # Read the Load Line Certificate PDF file
            with open(TEST_PDF_FILE, 'rb') as f:
                pdf_content = f.read()
            
            print(f"📤 Testing Multi-Cert Upload Classification with Load Line Certificate")
            print(f"File: {TEST_PDF_FILE} ({len(pdf_content):,} bytes)")
            print(f"Ship ID: {SHIP_ID}")
            print()
            
            # Prepare the multipart form data for multi-cert upload
            files = {
                'files': ('SUNSHINE_01_ILL_PM25826.pdf', pdf_content, 'application/pdf')
            }
            
            # Make the API request to multi-cert upload
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload?ship_id={SHIP_ID}",
                files=files,
                headers=self.get_headers()
            )
            processing_time = time.time() - start_time
            
            print(f"⏱️ Processing time: {processing_time:.2f} seconds")
            print()
            
            if response.status_code == 200:
                result = response.json()
                
                print("🔍 COMPLETE MULTI-CERT UPLOAD RESPONSE:")
                print(json.dumps(result, indent=2, default=str))
                print()
                
                # Analyze the results
                return self.analyze_classification_results(result)
                
            else:
                self.log_test("Multi-Cert Upload Classification", False,
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Multi-Cert Upload Classification", False, error=str(e))
            return False
    
    def analyze_classification_results(self, result):
        """Analyze the classification results from multi-cert upload"""
        success_count = 0
        total_tests = 5
        
        print("🔍 CLASSIFICATION RESULTS ANALYSIS:")
        print("=" * 60)
        
        # 1. Check overall summary
        summary = result.get('summary', {})
        total_files = summary.get('total_files', 0)
        marine_certificates = summary.get('marine_certificates', 0)
        non_marine_files = summary.get('non_marine_files', 0)
        
        print(f"📊 Summary:")
        print(f"   Total files: {total_files}")
        print(f"   Marine certificates: {marine_certificates}")
        print(f"   Non-marine files: {non_marine_files}")
        print()
        
        if marine_certificates > 0:
            self.log_test("Load Line Certificate Marine Classification", True,
                        f"Certificate correctly classified as marine certificate")
            success_count += 1
        else:
            self.log_test("Load Line Certificate Marine Classification", False,
                        error=f"Certificate incorrectly classified as non-marine! Marine: {marine_certificates}, Non-marine: {non_marine_files}")
        
        # 2. Check individual file results
        results = result.get('results', [])
        load_line_result = None
        
        for file_result in results:
            if 'SUNSHINE_01_ILL_PM25826.pdf' in file_result.get('filename', ''):
                load_line_result = file_result
                break
        
        if load_line_result:
            print(f"🔍 LOAD LINE CERTIFICATE INDIVIDUAL RESULT:")
            print(json.dumps(load_line_result, indent=2, default=str))
            print()
            
            # Check status
            status = load_line_result.get('status')
            is_marine = load_line_result.get('is_marine', False)
            
            if status == 'success' and is_marine:
                self.log_test("Load Line Certificate Processing Status", True,
                            f"Status: {status}, Is Marine: {is_marine}")
                success_count += 1
            elif status == 'skipped':
                self.log_test("Load Line Certificate Processing Status", False,
                            error=f"Certificate was SKIPPED! Status: {status}, Is Marine: {is_marine}")
            else:
                self.log_test("Load Line Certificate Processing Status", False,
                            error=f"Unexpected status: {status}, Is Marine: {is_marine}")
            
            # 3. Check AI analysis results
            analysis = load_line_result.get('analysis', {})
            if analysis:
                print(f"🔍 AI ANALYSIS DETAILS:")
                print(json.dumps(analysis, indent=2, default=str))
                print()
                
                # Check category classification
                category = analysis.get('category')
                if category == 'certificates':
                    self.log_test("AI Category Classification", True,
                                f"Correctly classified as: {category}")
                    success_count += 1
                else:
                    self.log_test("AI Category Classification", False,
                                error=f"INCORRECT CLASSIFICATION - Expected: 'certificates', Got: '{category}'")
                
                # Check certificate name detection
                cert_name = analysis.get('cert_name')
                if cert_name and 'load line' in cert_name.lower():
                    self.log_test("Certificate Name Detection", True,
                                f"Load Line Certificate detected: {cert_name}")
                    success_count += 1
                else:
                    self.log_test("Certificate Name Detection", False,
                                error=f"Load Line Certificate name not detected: {cert_name}")
                
                # Check certificate number detection
                cert_no = analysis.get('cert_no')
                if cert_no and 'PM25826' in str(cert_no):
                    self.log_test("Certificate Number Detection", True,
                                f"Certificate number detected: {cert_no}")
                    success_count += 1
                else:
                    self.log_test("Certificate Number Detection", False,
                                error=f"Expected certificate number PM25826 not detected: {cert_no}")
            else:
                self.log_test("AI Analysis Presence", False,
                            error="No AI analysis data found in result")
        else:
            self.log_test("Load Line Certificate Result Found", False,
                        error="Load Line Certificate result not found in response")
        
        # 4. Check for skip reasons if applicable
        non_marine_files_list = summary.get('non_marine_files_list', [])
        if non_marine_files_list:
            print(f"❌ NON-MARINE FILES DETECTED:")
            for non_marine in non_marine_files_list:
                if 'SUNSHINE_01_ILL_PM25826.pdf' in non_marine.get('filename', ''):
                    print(f"   Filename: {non_marine.get('filename')}")
                    print(f"   Category: {non_marine.get('category')}")
                    print(f"   Reason: {non_marine.get('reason')}")
                    print()
        
        print(f"📊 CLASSIFICATION ANALYSIS RESULTS: {success_count}/{total_tests} tests passed")
        
        return success_count >= 3  # At least 3 out of 5 tests should pass
    
    def run_all_tests(self):
        """Run all Load Line Certificate classification tests"""
        print("🔍 LOAD LINE CERTIFICATE CLASSIFICATION TEST")
        print("=" * 80)
        print(f"Testing Load Line Certificate: {TEST_PDF_FILE}")
        print(f"Expected: Marine Certificate (category = 'certificates')")
        print(f"Ship: SUNSHINE 01 (ID: {SHIP_ID})")
        print("=" * 80)
        print()
        
        # Run tests in sequence
        tests = [
            self.authenticate,
            self.test_multi_cert_upload_classification
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
                # Continue with other tests to get full picture
        
        print("=" * 80)
        print(f"📊 FINAL RESULTS: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests < total_tests:
            print("❌ LOAD LINE CERTIFICATE CLASSIFICATION ISSUE CONFIRMED")
            print("   The Load Line Certificate is being incorrectly classified!")
            print("   This explains why it's being skipped during multi-cert upload.")
        else:
            print("✅ LOAD LINE CERTIFICATE CLASSIFICATION WORKING CORRECTLY")
        
        print("=" * 80)
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    tester = LoadLineCertificateClassificationTester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("1. Check AI prompt for Load Line Certificate recognition")
        print("2. Review marine certificate classification rules")
        print("3. Verify certificate keywords detection in AI analysis")
        print("4. Check if 'Load Line Certificate' is included in marine certificate examples")
        print("5. Review AI model's understanding of maritime certificate types")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
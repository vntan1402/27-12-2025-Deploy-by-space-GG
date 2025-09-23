#!/usr/bin/env python3
"""
Load Line Certificate Classification Debug Test

Testing the specific issue where Load Line Certificate (SUNSHINE_01_ILL_PM25826.pdf) 
is being classified as non-marine certificate and skipped during multi-cert upload.

PROBLEM: Load Line Certificate is definitely a Marine Certificate but AI classification 
is marking it as non-marine.

INVESTIGATION:
1. Login as admin1/123456
2. Test AI analysis directly on SUNSHINE_01_ILL_PM25826.pdf (232KB)  
3. Check what category the AI analysis returns:
   - Expected: category = "certificates" (marine certificate)
   - Current: category = something else (causing skip)
4. Examine AI analysis response for:
   - Certificate classification
   - Document content analysis
   - Marine certificate keywords detection
5. Check backend logs for classification decision process
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

# Test credentials from review request
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

# Test file from review request
TEST_PDF_FILE = "/app/SUNSHINE_01_ILL_PM25826.pdf"
SHIP_ID = "e21c71a2-9543-4f92-990c-72f54292fde8"  # SUNSHINE 01 ship ID

class LoadLineCertificateDebugTester:
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
    
    def test_pdf_file_exists(self):
        """Test that the Load Line Certificate PDF file exists"""
        try:
            if os.path.exists(TEST_PDF_FILE):
                file_size = os.path.getsize(TEST_PDF_FILE)
                self.log_test("Load Line Certificate PDF File Test", True, 
                            f"File found: {TEST_PDF_FILE} ({file_size:,} bytes - Expected: ~232KB)")
                return True
            else:
                self.log_test("Load Line Certificate PDF File Test", False, 
                            error=f"File not found: {TEST_PDF_FILE}")
                return False
                
        except Exception as e:
            self.log_test("Load Line Certificate PDF File Test", False, error=str(e))
            return False
    
    def test_ship_exists(self):
        """Test that SUNSHINE 01 ship exists in database"""
        try:
            response = requests.get(f"{API_BASE}/ships/{SHIP_ID}", headers=self.get_headers())
            
            if response.status_code == 200:
                ship_data = response.json()
                ship_name = ship_data.get('name', 'Unknown')
                self.log_test("SUNSHINE 01 Ship Verification", True, 
                            f"Ship found: {ship_name} (ID: {SHIP_ID})")
                return True
            else:
                self.log_test("SUNSHINE 01 Ship Verification", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SUNSHINE 01 Ship Verification", False, error=str(e))
            return False
    
    def test_ai_configuration(self):
        """Test AI configuration for certificate analysis"""
        try:
            response = requests.get(f"{API_BASE}/ai-config", headers=self.get_headers())
            
            if response.status_code == 200:
                ai_config = response.json()
                provider = ai_config.get('provider')
                model = ai_config.get('model')
                use_emergent_key = ai_config.get('use_emergent_key', False)
                
                if provider and model:
                    details = f"Provider: {provider}, Model: {model}, Use Emergent Key: {use_emergent_key}"
                    self.log_test("AI Configuration Test", True, details)
                    return True
                else:
                    self.log_test("AI Configuration Test", False, 
                                error="Missing provider or model in AI configuration")
                    return False
            else:
                self.log_test("AI Configuration Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("AI Configuration Test", False, error=str(e))
            return False
    
    def test_direct_ai_analysis(self):
        """Test direct AI analysis on Load Line Certificate"""
        try:
            # Read the Load Line Certificate PDF file
            with open(TEST_PDF_FILE, 'rb') as f:
                pdf_content = f.read()
            
            # Prepare the multipart form data
            files = {
                'file': ('SUNSHINE_01_ILL_PM25826.pdf', pdf_content, 'application/pdf')
            }
            
            print(f"📤 Analyzing Load Line Certificate: {TEST_PDF_FILE} ({len(pdf_content):,} bytes)")
            
            # Make the API request to analyze certificate
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
                
                # Log the complete response for debugging
                print("🔍 COMPLETE AI ANALYSIS RESPONSE:")
                print(json.dumps(data, indent=2, default=str))
                print()
                
                # Verify basic response structure
                if not data.get('success'):
                    self.log_test("Direct AI Analysis - Basic Response", False,
                                error=f"Response success field is False: {data.get('message', 'No message')}")
                    return False
                
                analysis = data.get('analysis', {})
                if not analysis:
                    self.log_test("Direct AI Analysis - Basic Response", False,
                                error="No analysis data in response")
                    return False
                
                self.log_test("Direct AI Analysis - Basic Response", True,
                            f"Success: {data.get('success')}, Message: {data.get('message', 'N/A')}")
                
                # Analyze the classification results
                return self.analyze_certificate_classification(analysis, data)
                
            else:
                self.log_test("Direct AI Analysis - API Call", False,
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Direct AI Analysis - API Call", False, error=str(e))
            return False
    
    def analyze_certificate_classification(self, analysis, full_response):
        """Analyze the certificate classification results"""
        success_count = 0
        total_tests = 6
        
        print("🔍 CERTIFICATE CLASSIFICATION ANALYSIS:")
        print("=" * 60)
        
        # 1. Check category classification
        category = analysis.get('category')
        print(f"📋 Category: {category}")
        
        if category == "certificates":
            self.log_test("Certificate Category Classification", True,
                        f"Correctly classified as marine certificate: {category}")
            success_count += 1
        else:
            self.log_test("Certificate Category Classification", False,
                        error=f"INCORRECT CLASSIFICATION - Expected: 'certificates', Got: '{category}' - This causes the certificate to be skipped!")
        
        # 2. Check certificate name detection
        cert_name = analysis.get('cert_name')
        print(f"📜 Certificate Name: {cert_name}")
        
        if cert_name and "load line" in cert_name.lower():
            self.log_test("Load Line Certificate Name Detection", True,
                        f"Load Line Certificate detected: {cert_name}")
            success_count += 1
        else:
            self.log_test("Load Line Certificate Name Detection", False,
                        error=f"Load Line Certificate not properly detected: {cert_name}")
        
        # 3. Check ship name detection
        ship_name = analysis.get('ship_name')
        print(f"🚢 Ship Name: {ship_name}")
        
        if ship_name and "sunshine" in ship_name.lower():
            self.log_test("Ship Name Detection", True,
                        f"SUNSHINE ship detected: {ship_name}")
            success_count += 1
        else:
            self.log_test("Ship Name Detection", False,
                        error=f"SUNSHINE ship not properly detected: {ship_name}")
        
        # 4. Check certificate number detection
        cert_no = analysis.get('cert_no')
        print(f"🔢 Certificate Number: {cert_no}")
        
        if cert_no and "PM25826" in str(cert_no):
            self.log_test("Certificate Number Detection", True,
                        f"Certificate number detected: {cert_no}")
            success_count += 1
        else:
            self.log_test("Certificate Number Detection", False,
                        error=f"Expected certificate number PM25826 not detected: {cert_no}")
        
        # 5. Check issued by detection
        issued_by = analysis.get('issued_by')
        print(f"🏢 Issued By: {issued_by}")
        
        if issued_by:
            self.log_test("Issuing Authority Detection", True,
                        f"Issuing authority detected: {issued_by}")
            success_count += 1
        else:
            self.log_test("Issuing Authority Detection", False,
                        error="No issuing authority detected")
        
        # 6. Check marine certificate keywords
        marine_keywords = ['load line', 'international', 'certificate', 'tonnage', 'freeboard']
        detected_keywords = []
        
        # Check in certificate name
        if cert_name:
            for keyword in marine_keywords:
                if keyword.lower() in cert_name.lower():
                    detected_keywords.append(keyword)
        
        # Check in other fields
        for field_name, field_value in analysis.items():
            if field_value and isinstance(field_value, str):
                for keyword in marine_keywords:
                    if keyword.lower() in field_value.lower() and keyword not in detected_keywords:
                        detected_keywords.append(keyword)
        
        if detected_keywords:
            self.log_test("Marine Certificate Keywords Detection", True,
                        f"Marine keywords detected: {', '.join(detected_keywords)}")
            success_count += 1
        else:
            self.log_test("Marine Certificate Keywords Detection", False,
                        error="No marine certificate keywords detected")
        
        print()
        print("🔍 CLASSIFICATION DECISION ANALYSIS:")
        print("=" * 60)
        
        # Analyze why it might be classified incorrectly
        if category != "certificates":
            print(f"❌ CRITICAL ISSUE: Certificate classified as '{category}' instead of 'certificates'")
            print("   This causes the certificate to be skipped during multi-cert upload!")
            print()
            print("🔍 POSSIBLE CAUSES:")
            print("   1. AI model not recognizing 'Load Line Certificate' as marine certificate")
            print("   2. Classification logic in backend not handling this certificate type")
            print("   3. Marine certificate keywords not being detected properly")
            print("   4. Document content analysis failing to identify maritime context")
            print()
            
            # Check if there's any fallback reason
            fallback_reason = full_response.get('fallback_reason')
            if fallback_reason:
                print(f"   Fallback reason: {fallback_reason}")
            
            # Check processing method
            processing_method = analysis.get('processing_method')
            if processing_method:
                print(f"   Processing method: {processing_method}")
        
        print(f"📊 CLASSIFICATION TEST RESULTS: {success_count}/{total_tests} tests passed")
        
        return success_count >= 4  # At least 4 out of 6 tests should pass
    
    def test_multi_cert_upload_simulation(self):
        """Simulate multi-cert upload to see the skip behavior"""
        try:
            # Read the Load Line Certificate PDF file
            with open(TEST_PDF_FILE, 'rb') as f:
                pdf_content = f.read()
            
            # Prepare the multipart form data for multi-cert upload
            files = {
                'files': ('SUNSHINE_01_ILL_PM25826.pdf', pdf_content, 'application/pdf')
            }
            
            data = {
                'ship_id': SHIP_ID
            }
            
            print(f"📤 Testing Multi-Cert Upload with Load Line Certificate")
            
            # Make the API request to multi-cert upload
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                files=files,
                data=data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print("🔍 MULTI-CERT UPLOAD RESPONSE:")
                print(json.dumps(result, indent=2, default=str))
                print()
                
                # Check if certificate was skipped
                skipped_files = result.get('skipped_files', [])
                processed_files = result.get('processed_files', [])
                
                if any('SUNSHINE_01_ILL_PM25826.pdf' in str(file) for file in skipped_files):
                    self.log_test("Multi-Cert Upload - Skip Detection", False,
                                error="Load Line Certificate was SKIPPED as non-marine certificate!")
                    
                    # Analyze skip reason
                    for skipped in skipped_files:
                        if 'SUNSHINE_01_ILL_PM25826.pdf' in str(skipped):
                            skip_reason = skipped.get('reason', 'No reason provided')
                            print(f"❌ SKIP REASON: {skip_reason}")
                    
                    return False
                elif any('SUNSHINE_01_ILL_PM25826.pdf' in str(file) for file in processed_files):
                    self.log_test("Multi-Cert Upload - Processing Success", True,
                                "Load Line Certificate was correctly processed as marine certificate")
                    return True
                else:
                    self.log_test("Multi-Cert Upload - File Not Found", False,
                                error="Load Line Certificate not found in processed or skipped files")
                    return False
                
            else:
                self.log_test("Multi-Cert Upload - API Call", False,
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Multi-Cert Upload - API Call", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all Load Line Certificate classification debug tests"""
        print("🔍 LOAD LINE CERTIFICATE CLASSIFICATION DEBUG TEST")
        print("=" * 80)
        print(f"Testing Load Line Certificate: {TEST_PDF_FILE}")
        print(f"Expected: Marine Certificate (category = 'certificates')")
        print(f"Ship: SUNSHINE 01 (ID: {SHIP_ID})")
        print("=" * 80)
        print()
        
        # Run tests in sequence
        tests = [
            self.authenticate,
            self.test_pdf_file_exists,
            self.test_ship_exists,
            self.test_ai_configuration,
            self.test_direct_ai_analysis,
            self.test_multi_cert_upload_simulation
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
    tester = LoadLineCertificateDebugTester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("1. Check AI model training for Load Line Certificate recognition")
        print("2. Review marine certificate classification rules in backend")
        print("3. Verify marine certificate keywords detection logic")
        print("4. Check document content analysis for maritime context")
        print("5. Review certificate category mapping logic")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
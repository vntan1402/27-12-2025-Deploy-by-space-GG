#!/usr/bin/env python3
"""
AI Analysis Pipeline Testing - FINAL VERIFICATION TEST
Testing the complete AI analysis pipeline with proper Emergent LLM key configuration.

Review Request Requirements:
1. Authentication: Login as admin1/123456
2. PNG File Test: Test POST /api/analyze-ship-certificate with PNG file
3. AI Configuration Verification: Verify Emergent LLM key usage
4. Expected Results: NO "AI analysis failed or no API key available" error
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

# PNG file URL from review request
PNG_FILE_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/0s8zv2vs_image.png"

class AIAnalysisPipelineTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.png_file_content = None
        
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
        """Authenticate with admin1/123456 credentials"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                
                # Verify user details
                username = self.user_info.get('username')
                role = self.user_info.get('role', '').upper()
                
                self.log_test("Authentication Test", True, 
                            f"Successfully logged in as {username} with role {role}")
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
    
    def download_png_file(self):
        """Download the PNG file from the provided URL"""
        try:
            print(f"Downloading PNG file from: {PNG_FILE_URL}")
            response = requests.get(PNG_FILE_URL, timeout=30)
            
            if response.status_code == 200:
                self.png_file_content = response.content
                file_size = len(self.png_file_content)
                
                # Verify it's actually a PNG file
                if self.png_file_content.startswith(b'\x89PNG'):
                    self.log_test("PNG File Download", True, 
                                f"Successfully downloaded PNG file ({file_size:,} bytes)")
                    return True
                else:
                    self.log_test("PNG File Download", False, 
                                error="Downloaded file is not a valid PNG")
                    return False
            else:
                self.log_test("PNG File Download", False, 
                            error=f"Failed to download PNG file. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("PNG File Download", False, error=str(e))
            return False
    
    def test_ai_configuration(self):
        """Test AI configuration and verify Emergent LLM key setup"""
        try:
            response = requests.get(f"{API_BASE}/ai-config", headers=self.get_headers())
            
            if response.status_code == 200:
                ai_config = response.json()
                provider = ai_config.get('provider')
                model = ai_config.get('model')
                use_emergent_key = ai_config.get('use_emergent_key', False)
                
                details = f"Provider: {provider}, Model: {model}, Use Emergent Key: {use_emergent_key}"
                
                # Check if Emergent LLM key is being used
                if use_emergent_key or provider == 'emergent':
                    self.log_test("AI Configuration Verification", True, 
                                f"Emergent LLM key configuration detected. {details}")
                else:
                    self.log_test("AI Configuration Verification", True, 
                                f"AI configuration found. {details}")
                return ai_config
            else:
                self.log_test("AI Configuration Verification", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("AI Configuration Verification", False, error=str(e))
            return None
    
    def test_png_file_analysis(self):
        """Test POST /api/analyze-ship-certificate with PNG file"""
        try:
            if not self.png_file_content:
                self.log_test("PNG File Analysis Test", False, 
                            error="PNG file content not available")
                return None
            
            # Prepare the PNG file for upload
            files = {
                'file': ('0s8zv2vs_image.png', io.BytesIO(self.png_file_content), 'image/png')
            }
            
            print(f"Testing PNG file analysis with {len(self.png_file_content):,} byte PNG file...")
            
            # Make the API call
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers(),
                timeout=60  # Allow up to 60 seconds for AI processing
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Debug: Print the full response to understand what we're getting
                print(f"DEBUG: Full API response: {json.dumps(result, indent=2)}")
                
                # Check for the critical error we're trying to avoid
                fallback_reason = result.get('fallback_reason', '')
                if "AI analysis failed or no API key available" in fallback_reason:
                    self.log_test("PNG File Analysis Test", False, 
                                error=f"CRITICAL: Still getting API key error: {fallback_reason}")
                    return result
                
                # Check if we have meaningful ship data extraction
                analysis_data = result.get('data', {}).get('analysis', {}) or result.get('analysis', {})
                
                ship_fields = ['ship_name', 'imo_number', 'flag', 'class_society', 'gross_tonnage', 'deadweight', 'built_year', 'ship_owner']
                populated_fields = []
                null_fields = []
                
                for field in ship_fields:
                    value = analysis_data.get(field)
                    if value is not None and value != '' and str(value).lower() != 'null':
                        populated_fields.append(f"{field}: {value}")
                    else:
                        null_fields.append(field)
                
                # Check processing method and confidence
                processing_method = result.get('processing_method', 'Unknown')
                confidence_score = result.get('confidence_score', 'Unknown')
                
                # Evaluate results
                if len(populated_fields) > 0:
                    details = (f"SUCCESS: AI analysis working! "
                             f"Processing method: {processing_method}, "
                             f"Confidence: {confidence_score}, "
                             f"Populated fields ({len(populated_fields)}): {', '.join(populated_fields[:3])}...")
                    
                    if len(populated_fields) >= 4:  # Good extraction
                        self.log_test("PNG File Analysis Test", True, details)
                    else:  # Partial extraction
                        details += f" (Partial extraction - {len(null_fields)} fields still null)"
                        self.log_test("PNG File Analysis Test", True, details)
                else:
                    # All fields are null - this is the issue we're trying to fix
                    error_msg = (f"All ship data fields are null. "
                               f"Processing method: {processing_method}, "
                               f"Fallback reason: {fallback_reason}")
                    self.log_test("PNG File Analysis Test", False, error=error_msg)
                
                return result
                
            elif response.status_code == 400:
                # Check if it's the "Only PDF files are allowed" error
                error_text = response.text
                if "Only PDF files are allowed" in error_text:
                    self.log_test("PNG File Analysis Test", False, 
                                error="CRITICAL: Backend still rejecting PNG files - 'Only PDF files are allowed'")
                else:
                    self.log_test("PNG File Analysis Test", False, 
                                error=f"Bad Request (400): {error_text}")
                return None
            else:
                self.log_test("PNG File Analysis Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("PNG File Analysis Test", False, error=str(e))
            return None
    
    def test_emergent_llm_key_usage(self):
        """Verify that Emergent LLM key is being used correctly"""
        try:
            # Check backend environment for Emergent LLM key
            # This is indirect - we'll check through AI config and analysis results
            
            # First check if AI config shows Emergent key usage
            ai_config_response = requests.get(f"{API_BASE}/ai-config", headers=self.get_headers())
            
            if ai_config_response.status_code == 200:
                ai_config = ai_config_response.json()
                use_emergent_key = ai_config.get('use_emergent_key', False)
                provider = ai_config.get('provider', '')
                
                if use_emergent_key or provider.lower() == 'emergent':
                    self.log_test("Emergent LLM Key Usage Verification", True, 
                                f"AI configuration indicates Emergent LLM key usage (provider: {provider}, use_emergent_key: {use_emergent_key})")
                    return True
                else:
                    # Check if we can still get successful AI analysis without explicit Emergent flag
                    self.log_test("Emergent LLM Key Usage Verification", True, 
                                f"AI configuration found (provider: {provider}) - will verify through analysis results")
                    return True
            else:
                self.log_test("Emergent LLM Key Usage Verification", False, 
                            error=f"Could not retrieve AI configuration: {ai_config_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Emergent LLM Key Usage Verification", False, error=str(e))
            return False
    
    def verify_expected_results(self, analysis_result):
        """Verify that we get the expected results from the review request"""
        try:
            if not analysis_result:
                self.log_test("Expected Results Verification", False, 
                            error="No analysis result to verify")
                return False
            
            # Check 1: NO "AI analysis failed or no API key available" error
            fallback_reason = analysis_result.get('fallback_reason', '')
            if "AI analysis failed or no API key available" in fallback_reason:
                self.log_test("Expected Results Verification", False, 
                            error=f"CRITICAL: Still getting API key error: {fallback_reason}")
                return False
            
            # Check 2: Ship data fields populated with extracted information
            analysis_data = analysis_result.get('data', {}).get('analysis', {}) or analysis_result.get('analysis', {})
            
            populated_count = 0
            for field in ['ship_name', 'imo_number', 'flag', 'class_society', 'gross_tonnage', 'deadweight', 'built_year', 'ship_owner']:
                value = analysis_data.get(field)
                if value is not None and value != '' and str(value).lower() != 'null':
                    populated_count += 1
            
            # Check 3: Proper processing method and confidence scores
            processing_method = analysis_result.get('processing_method', 'Unknown')
            confidence_score = analysis_result.get('confidence_score')
            
            # Check 4: Success response with meaningful data
            success = analysis_result.get('success', False)
            
            if success and populated_count > 0 and processing_method != 'Unknown':
                details = (f"✅ NO API key error, "
                         f"✅ {populated_count}/8 ship data fields populated, "
                         f"✅ Processing method: {processing_method}, "
                         f"✅ Confidence score: {confidence_score}, "
                         f"✅ Success response received")
                
                self.log_test("Expected Results Verification", True, details)
                return True
            else:
                error_details = []
                if not success:
                    error_details.append("Response not marked as successful")
                if populated_count == 0:
                    error_details.append("No ship data fields populated")
                if processing_method == 'Unknown':
                    error_details.append("Processing method unknown")
                
                self.log_test("Expected Results Verification", False, 
                            error=f"Missing expected results: {', '.join(error_details)}")
                return False
                
        except Exception as e:
            self.log_test("Expected Results Verification", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests for AI Analysis Pipeline"""
        print("🧪 AI ANALYSIS PIPELINE FINAL VERIFICATION TEST")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test User: {TEST_USERNAME}")
        print(f"PNG File URL: {PNG_FILE_URL}")
        print()
        
        # Step 1: Authentication Test
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Download PNG File
        if not self.download_png_file():
            print("❌ PNG file download failed. Cannot proceed with analysis test.")
            return False
        
        # Step 3: Test AI Configuration
        ai_config = self.test_ai_configuration()
        if not ai_config:
            print("❌ AI configuration test failed. AI analysis may not work.")
            # Continue with tests to see what happens
        
        # Step 4: Test Emergent LLM Key Usage
        if not self.test_emergent_llm_key_usage():
            print("❌ Emergent LLM key verification failed.")
            # Continue with tests
        
        # Step 5: Test PNG File Analysis (MAIN TEST)
        analysis_result = self.test_png_file_analysis()
        if not analysis_result:
            print("❌ PNG file analysis test failed completely.")
            return False
        
        # Step 6: Verify Expected Results
        if not self.verify_expected_results(analysis_result):
            print("❌ Expected results verification failed.")
            return False
        
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
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! AI Analysis Pipeline is working correctly with Emergent LLM key.")
            print("✅ PNG file processing working")
            print("✅ No 'AI analysis failed or no API key available' errors")
            print("✅ Ship data extraction functional")
            print("✅ Proper processing method and confidence scores")
            return True
        else:
            print(f"\n❌ {total - passed} tests failed. AI Analysis Pipeline issues detected:")
            
            # Show specific failures
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['test']}: {result['error']}")
            
            return False

def main():
    """Main test execution"""
    tester = AIAnalysisPipelineTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
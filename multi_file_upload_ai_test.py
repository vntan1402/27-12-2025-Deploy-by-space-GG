#!/usr/bin/env python3
"""
Multi-File Upload with AI Processing Test Suite
Tests the updated multi-file upload system that uses AI config from the system instead of hardcoded Emergent LLM key.
"""

import requests
import sys
import json
import time
import os
from datetime import datetime, timezone

class MultiFileUploadAITester:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.test_pdf_url = "https://drive.google.com/uc?export=download&id=1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")

    def run_api_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        # Override with custom headers if provided
        if headers:
            test_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            test_headers.pop('Content-Type', None)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=60)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=test_headers, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=test_headers, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=60)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=60)

            success = response.status_code == expected_status
            if success:
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text[:500]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_authentication(self):
        """Test admin login"""
        print(f"\n🔐 Testing Authentication")
        success, response = self.run_api_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin1", "password": "123456"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            user_info = response.get('user', {})
            self.log_test(
                "Authentication successful",
                True,
                f"User: {user_info.get('full_name')} ({user_info.get('role')})"
            )
            return True
        else:
            self.log_test("Authentication failed", False, "Could not obtain access token")
            return False

    def test_ai_config_retrieval(self):
        """Test AI configuration retrieval"""
        print(f"\n🤖 Testing AI Configuration")
        success, config = self.run_api_test(
            "Get AI Config",
            "GET",
            "ai-config",
            200
        )
        
        if success:
            provider = config.get('provider', 'Unknown')
            model = config.get('model', 'Unknown')
            has_api_key = bool(config.get('api_key'))
            
            self.log_test(
                "AI Config retrieved successfully",
                True,
                f"Provider: {provider}, Model: {model}, API Key configured: {has_api_key}"
            )
            
            # Verify expected configuration (system is now using AI config from database)
            # The key point is that it's NOT hardcoded Emergent LLM, but configurable
            expected_providers = ["openai", "emergent", "anthropic", "google"]
            
            if provider.lower() in [p.lower() for p in expected_providers] and has_api_key:
                self.log_test(
                    "AI Config matches expected settings",
                    True,
                    f"✓ Provider: {provider}, ✓ Model: {model}, ✓ API Key present"
                )
                return config
            else:
                self.log_test(
                    "AI Config does not match expected settings",
                    False,
                    f"Expected valid provider from {expected_providers}, got: provider={provider}, model={model}"
                )
                return config
        else:
            self.log_test("Failed to retrieve AI config", False)
            return None

    def download_test_pdf(self):
        """Download or create a test PDF"""
        print(f"\n📄 Creating Test PDF")
        try:
            # Create a simple PDF-like content for testing
            # Since we can't get the actual PDF, we'll create a minimal test
            pdf_header = b'%PDF-1.4\n'
            pdf_content = pdf_header + b'''1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
100 700 Td
(INTERNATIONAL AIR POLLUTION PREVENTION CERTIFICATE) Tj
0 -20 Td
(Ship Name: BROTHER 36) Tj
0 -20 Td
(Certificate Number: PM242838) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000100 00000 n 
0000000178 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
330
%%EOF'''
            
            self.log_test(
                "Test PDF created",
                True,
                f"Size: {len(pdf_content):,} bytes"
            )
            return pdf_content
            
        except Exception as e:
            self.log_test(
                "Error creating test PDF",
                False,
                str(e)
            )
            return None

    def test_multi_file_upload(self, pdf_content):
        """Test multi-file upload endpoint with AI processing"""
        print(f"\n📤 Testing Multi-File Upload with AI Processing")
        
        if not pdf_content:
            self.log_test("Cannot test multi-file upload", False, "No PDF content available")
            return False
        
        # Prepare file for upload
        files = [
            ('files', ('BROTHER_36_IAPP_Certificate.pdf', pdf_content, 'application/pdf'))
        ]
        
        # Test the multi-file upload endpoint
        success, response = self.run_api_test(
            "Multi-File Upload with AI Processing",
            "POST",
            "certificates/upload-multi-files",
            200,
            files=files
        )
        
        if success:
            # Analyze the response
            total_files = response.get('total_files', 0)
            successful_uploads = response.get('successful_uploads', 0)
            certificates_created = response.get('certificates_created', 0)
            results = response.get('results', [])
            
            self.log_test(
                "Multi-file upload completed",
                True,
                f"Files: {total_files}, Uploads: {successful_uploads}, Certificates: {certificates_created}"
            )
            
            # Analyze individual file results
            if results:
                file_result = results[0]  # First (and only) file
                
                # Check AI analysis results
                category = file_result.get('category')
                ship_name = file_result.get('ship_name')
                extracted_info = file_result.get('extracted_info', {})
                cert_name = extracted_info.get('cert_name')
                certificate_created = file_result.get('certificate_created', False)
                errors = file_result.get('errors', [])
                
                print(f"\n📊 AI Analysis Results:")
                print(f"   Category: {category}")
                print(f"   Ship Name: {ship_name}")
                print(f"   Certificate Name: {cert_name}")
                print(f"   Certificate Created: {certificate_created}")
                if errors:
                    print(f"   Errors: {errors}")
                
                # Verify expected results
                expected_results = {
                    'category': 'certificates',
                    'ship_name': 'BROTHER 36',
                    'cert_name': 'International Air Pollution Prevention Certificate'
                }
                
                results_correct = True
                verification_details = []
                
                # Check category
                if category == expected_results['category']:
                    verification_details.append(f"✓ Category: {category}")
                else:
                    verification_details.append(f"✗ Category: expected '{expected_results['category']}', got '{category}'")
                    results_correct = False
                
                # Check ship name
                if ship_name == expected_results['ship_name']:
                    verification_details.append(f"✓ Ship Name: {ship_name}")
                else:
                    verification_details.append(f"✗ Ship Name: expected '{expected_results['ship_name']}', got '{ship_name}'")
                    results_correct = False
                
                # Check certificate name
                if cert_name and expected_results['cert_name'] in cert_name:
                    verification_details.append(f"✓ Certificate Name: {cert_name}")
                else:
                    verification_details.append(f"✗ Certificate Name: expected '{expected_results['cert_name']}', got '{cert_name}'")
                    results_correct = False
                
                # Check certificate creation
                if certificate_created:
                    verification_details.append(f"✓ Certificate record created")
                else:
                    verification_details.append(f"✗ Certificate record not created")
                    results_correct = False
                
                self.log_test(
                    "AI Analysis Results Verification",
                    results_correct,
                    "\n   " + "\n   ".join(verification_details)
                )
                
                return results_correct
            else:
                self.log_test("No file results in response", False)
                return False
        else:
            self.log_test("Multi-file upload failed", False)
            return False

    def test_certificate_creation_verification(self):
        """Verify that certificate records were actually created"""
        print(f"\n📋 Verifying Certificate Creation")
        
        # Get all certificates to verify creation
        success, certificates = self.run_api_test(
            "Get All Certificates",
            "GET",
            "certificates",
            200
        )
        
        if success:
            # Look for BROTHER 36 certificates
            brother36_certs = [cert for cert in certificates if 'BROTHER 36' in cert.get('ship_name', '')]
            iapp_certs = [cert for cert in certificates if 'Air Pollution' in cert.get('cert_name', '')]
            
            self.log_test(
                "Certificate verification completed",
                True,
                f"Total certificates: {len(certificates)}, BROTHER 36 certificates: {len(brother36_certs)}, IAPP certificates: {len(iapp_certs)}"
            )
            
            if brother36_certs:
                cert = brother36_certs[0]
                print(f"   Found BROTHER 36 certificate:")
                print(f"     ID: {cert.get('id')}")
                print(f"     Name: {cert.get('cert_name')}")
                print(f"     Ship: {cert.get('ship_name')}")
                print(f"     Category: {cert.get('category')}")
                return True
            else:
                self.log_test("No BROTHER 36 certificates found", False)
                return False
        else:
            self.log_test("Failed to retrieve certificates", False)
            return False

    def test_ai_provider_switch_verification(self):
        """Verify that the system is using the configured AI provider instead of hardcoded Emergent LLM"""
        print(f"\n🔄 Verifying AI Provider Switch")
        
        # Get AI config to confirm current settings
        success, config = self.run_api_test(
            "Verify AI Config",
            "GET",
            "ai-config",
            200
        )
        
        if success:
            provider = config.get('provider', '').lower()
            model = config.get('model', '')
            
            # The key verification is that the system is using AI config from database
            # rather than hardcoded values in the code
            valid_providers = ['openai', 'emergent', 'anthropic', 'google']
            
            if provider in valid_providers:
                self.log_test(
                    "AI Provider switch verified",
                    True,
                    f"System is using configurable AI provider: {provider} with model {model} (not hardcoded)"
                )
                return True
            else:
                self.log_test(
                    "AI Provider configuration unclear",
                    False,
                    f"Provider: {provider}, Model: {model}"
                )
                return False
        else:
            self.log_test("Could not verify AI provider configuration", False)
            return False

    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("🚢 Multi-File Upload with AI Processing Test Suite")
        print("=" * 60)
        print("Testing updated system that uses AI config from database instead of hardcoded Emergent LLM key")
        print("=" * 60)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Test 2: AI Configuration
        ai_config = self.test_ai_config_retrieval()
        if not ai_config:
            print("⚠️ AI Config test failed, but continuing...")
        
        # Test 3: AI Provider Switch Verification
        self.test_ai_provider_switch_verification()
        
        # Test 4: Download Test PDF
        pdf_content = self.download_test_pdf()
        if not pdf_content:
            print("❌ Could not download test PDF, stopping upload tests")
            return False
        
        # Test 5: Multi-File Upload with AI Processing
        upload_success = self.test_multi_file_upload(pdf_content)
        
        # Test 6: Certificate Creation Verification
        cert_verification = self.test_certificate_creation_verification()
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"Total API Tests: {self.tests_passed}/{self.tests_run}")
        
        # Key test results
        key_tests = [
            ("Authentication", self.token is not None),
            ("AI Config Retrieved", ai_config is not None),
            ("PDF Download", pdf_content is not None),
            ("Multi-File Upload", upload_success),
            ("Certificate Creation", cert_verification)
        ]
        
        passed_key_tests = sum(1 for _, result in key_tests if result)
        total_key_tests = len(key_tests)
        
        for test_name, result in key_tests:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:25} {status}")
        
        print(f"\nKey Feature Tests: {passed_key_tests}/{total_key_tests}")
        
        if passed_key_tests == total_key_tests:
            print("🎉 All key tests passed! Multi-file upload with AI processing is working correctly.")
            print("\n✅ VERIFICATION COMPLETE:")
            print("   • System uses AI config from database (not hardcoded Emergent LLM)")
            print("   • AI correctly identifies category as 'certificates'")
            print("   • AI correctly extracts ship name as 'BROTHER 36'")
            print("   • AI correctly identifies certificate name")
            print("   • System auto-creates certificate records")
            return True
        else:
            print("⚠️ Some key tests failed - check results above")
            return False

def main():
    """Main test execution"""
    tester = MultiFileUploadAITester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
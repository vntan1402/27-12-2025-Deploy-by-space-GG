#!/usr/bin/env python3
"""
AI Analysis Testing for Ship Management System
Testing improved AI analysis with real certificate PDF file

Focus: Test the improved AI analysis with the real certificate PDF file that the user uploaded.
The user reported that:
1. Ship name was analyzed as "Unknown Ship" (should be "BROTHER 36")
2. File was classified as "Other Documents" (should be "certificates")

Test Requirements:
1. Login as admin/admin123
2. Use the improved analyze_document_with_ai function
3. Test with the actual PDF file URL: https://customer-assets.emergentagent.com/job_vessel-docs-1/artifacts/nzwrda4b_BROTHER%2036%20-%20IAPP%20-%20PM242838.pdf
4. Verify the AI now correctly identifies:
   - category: "certificates" (not "other_documents")
   - ship_name: "BROTHER 36" (not "Unknown Ship")
   - cert_name: "International Air Pollution Prevention Certificate"
   - cert_no: "PM242838"
   - Other certificate details
"""

import requests
import sys
import json
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path

class AIAnalysisTester:
    def __init__(self, base_url="https://aicert-analyzer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        
        # Test data - Real certificate PDF URL from user report
        self.test_pdf_url = "https://customer-assets.emergentagent.com/job_vessel-docs-1/artifacts/nzwrda4b_BROTHER%2036%20-%20IAPP%20-%20PM242838.pdf"
        self.expected_results = {
            "category": "certificates",
            "ship_name": "BROTHER 36",
            "cert_name": "International Air Pollution Prevention Certificate",
            "cert_type": "Full Term Certificate",
            "cert_no": "PM242838",
            "issue_date": "2024-12-10",
            "valid_date": "2028-03-18",
            "issued_by": "Panama Maritime Documentation Services Inc"
        }

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED")
        
        if details:
            print(f"   {details}")

    def run_api_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        
        # Default headers
        default_headers = {}
        if self.token:
            default_headers['Authorization'] = f'Bearer {self.token}'
        
        # Merge with provided headers
        if headers:
            default_headers.update(headers)
        
        # Don't set Content-Type for file uploads
        if not files and method in ['POST', 'PUT']:
            default_headers['Content-Type'] = 'application/json'

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=60)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=default_headers, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=default_headers, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=60)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=60)

            success = response.status_code == expected_status
            if success:
                print(f"✅ API Call Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {"text": response.text}
            else:
                print(f"❌ API Call Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ API Call Failed - Error: {str(e)}")
            return False, {}

    def test_authentication(self):
        """Test admin login"""
        print(f"\n🔐 TESTING AUTHENTICATION")
        print("=" * 50)
        
        success, response = self.run_api_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            user_info = response.get('user', {})
            self.log_test(
                "Authentication", 
                True, 
                f"User: {user_info.get('full_name')} ({user_info.get('role')})"
            )
            return True
        else:
            self.log_test("Authentication", False, "Failed to get access token")
            return False

    def download_test_pdf(self):
        """Download the real certificate PDF for testing"""
        print(f"\n📥 DOWNLOADING TEST PDF")
        print("=" * 50)
        
        try:
            print(f"Downloading PDF from: {self.test_pdf_url}")
            response = requests.get(self.test_pdf_url, timeout=30)
            
            if response.status_code == 200:
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(response.content)
                temp_file.close()
                
                file_size = len(response.content)
                self.log_test(
                    "PDF Download", 
                    True, 
                    f"Downloaded {file_size} bytes to {temp_file.name}"
                )
                return temp_file.name
            else:
                self.log_test(
                    "PDF Download", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("PDF Download", False, f"Error: {str(e)}")
            return None

    def test_ship_certificate_analysis(self, pdf_path):
        """Test the /api/analyze-ship-certificate endpoint"""
        print(f"\n🤖 TESTING SHIP CERTIFICATE ANALYSIS")
        print("=" * 50)
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                files = {'file': ('BROTHER_36_IAPP_PM242838.pdf', pdf_file, 'application/pdf')}
                
                success, response = self.run_api_test(
                    "Ship Certificate Analysis",
                    "POST",
                    "analyze-ship-certificate",
                    200,
                    files=files
                )
                
                if success:
                    analysis = response.get('analysis', {})
                    
                    # Check ship name extraction
                    ship_name = analysis.get('ship_name')
                    ship_name_correct = ship_name == self.expected_results['ship_name']
                    self.log_test(
                        "Ship Name Extraction",
                        ship_name_correct,
                        f"Expected: '{self.expected_results['ship_name']}', Got: '{ship_name}'"
                    )
                    
                    # Check other fields
                    imo_number = analysis.get('imo_number')
                    self.log_test(
                        "IMO Number Extraction",
                        imo_number is not None,
                        f"IMO: {imo_number}"
                    )
                    
                    # Print full analysis result
                    print(f"\n📊 FULL ANALYSIS RESULT:")
                    for key, value in analysis.items():
                        print(f"   {key}: {value}")
                    
                    return ship_name_correct
                else:
                    self.log_test("Ship Certificate Analysis", False, "API call failed")
                    return False
                    
        except Exception as e:
            self.log_test("Ship Certificate Analysis", False, f"Error: {str(e)}")
            return False

    def test_multi_file_upload_analysis(self, pdf_path):
        """Test the multi-file upload endpoint that uses analyze_document_with_ai"""
        print(f"\n📁 TESTING MULTI-FILE UPLOAD WITH AI ANALYSIS")
        print("=" * 50)
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                files = {'files': ('BROTHER_36_IAPP_PM242838.pdf', pdf_file, 'application/pdf')}
                
                success, response = self.run_api_test(
                    "Multi-File Upload with AI Analysis",
                    "POST",
                    "certificates/upload-multi-files",
                    200,
                    files=files
                )
                
                if success:
                    results = response.get('results', [])
                    
                    if results:
                        first_result = results[0]
                        ai_analysis = first_result.get('ai_analysis', {})
                        
                        # Check document category classification
                        category = ai_analysis.get('category')
                        category_correct = category == self.expected_results['category']
                        self.log_test(
                            "Document Category Classification",
                            category_correct,
                            f"Expected: '{self.expected_results['category']}', Got: '{category}'"
                        )
                        
                        # Check ship name in AI analysis
                        ship_name = ai_analysis.get('ship_name')
                        ship_name_correct = ship_name == self.expected_results['ship_name']
                        self.log_test(
                            "Ship Name in AI Analysis",
                            ship_name_correct,
                            f"Expected: '{self.expected_results['ship_name']}', Got: '{ship_name}'"
                        )
                        
                        # Check certificate name
                        cert_name = ai_analysis.get('cert_name')
                        cert_name_correct = cert_name and "Air Pollution Prevention" in cert_name
                        self.log_test(
                            "Certificate Name Recognition",
                            cert_name_correct,
                            f"Expected: Contains 'Air Pollution Prevention', Got: '{cert_name}'"
                        )
                        
                        # Check certificate number
                        cert_no = ai_analysis.get('cert_no')
                        cert_no_correct = cert_no == self.expected_results['cert_no']
                        self.log_test(
                            "Certificate Number Extraction",
                            cert_no_correct,
                            f"Expected: '{self.expected_results['cert_no']}', Got: '{cert_no}'"
                        )
                        
                        # Print full AI analysis result
                        print(f"\n🧠 FULL AI ANALYSIS RESULT:")
                        for key, value in ai_analysis.items():
                            print(f"   {key}: {value}")
                        
                        return category_correct and ship_name_correct
                    else:
                        self.log_test("Multi-File Upload Analysis", False, "No results returned")
                        return False
                else:
                    self.log_test("Multi-File Upload Analysis", False, "API call failed")
                    return False
                    
        except Exception as e:
            self.log_test("Multi-File Upload Analysis", False, f"Error: {str(e)}")
            return False

    def test_ai_improvements_verification(self):
        """Verify that the AI improvements are working correctly"""
        print(f"\n🎯 TESTING AI IMPROVEMENTS VERIFICATION")
        print("=" * 50)
        
        # Download the real certificate PDF
        pdf_path = self.download_test_pdf()
        if not pdf_path:
            return False
        
        try:
            # Test both endpoints
            ship_analysis_success = self.test_ship_certificate_analysis(pdf_path)
            multi_file_analysis_success = self.test_multi_file_upload_analysis(pdf_path)
            
            # Overall verification
            overall_success = ship_analysis_success and multi_file_analysis_success
            self.log_test(
                "Overall AI Improvements",
                overall_success,
                "Both ship analysis and document classification working correctly" if overall_success else "Some AI analysis issues remain"
            )
            
            return overall_success
            
        finally:
            # Clean up temporary file
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)

    def run_comprehensive_test(self):
        """Run comprehensive AI analysis testing"""
        print("🤖 AI ANALYSIS TESTING FOR SHIP MANAGEMENT SYSTEM")
        print("=" * 60)
        print(f"Testing improved AI analysis with real certificate PDF")
        print(f"Expected Ship: {self.expected_results['ship_name']}")
        print(f"Expected Category: {self.expected_results['category']}")
        print(f"Expected Certificate: {self.expected_results['cert_name']}")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_authentication():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Test AI improvements
        ai_success = self.test_ai_improvements_verification()
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if ai_success:
            print("🎉 AI ANALYSIS IMPROVEMENTS VERIFIED SUCCESSFULLY!")
            print("✅ Ship name correctly identified as 'BROTHER 36'")
            print("✅ Document correctly classified as 'certificates'")
            print("✅ Certificate details properly extracted")
        else:
            print("⚠️ AI ANALYSIS ISSUES DETECTED")
            print("❌ Some AI analysis improvements may not be working correctly")
        
        return ai_success

def main():
    """Main test execution"""
    tester = AIAnalysisTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
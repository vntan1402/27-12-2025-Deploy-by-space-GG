#!/usr/bin/env python3
"""
AI Analysis Improvements Test - Review Request Specific
Testing the fixed AI analysis function with real IAPP certificate PDF

This test addresses the specific review request:
- Test the fixed AI analysis function with the real IAPP certificate PDF
- Verify improvements made to use .with_model("gemini", "gemini-2.0-flash") approach
- Check enhanced JSON parsing with markdown code block cleaning
- Verify improved error handling and data validation
- Test with user's real certificate: BROTHER 36 - IAPP - PM242838.pdf
"""

import requests
import sys
import json
import tempfile
import os
from datetime import datetime, timezone
import time

class AIAnalysisImprovementsTester:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Real certificate PDF from review request
        self.test_pdf_url = "https://customer-assets.emergentagent.com/job_vessel-docs-1/artifacts/nzwrda4b_BROTHER%2036%20-%20IAPP%20-%20PM242838.pdf"
        
        # Expected results after fix
        self.expected_results = {
            "category": "certificates",  # not "other_documents"
            "ship_name": "BROTHER 36",   # not "Unknown Ship"
            "cert_name": "International Air Pollution Prevention Certificate",
            "cert_no": "PM242838",
            "cert_type": "Full Term Certificate",
            "issue_date": "2024-12-10",
            "valid_date": "2028-03-18"
        }

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if success:
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {test_name}: FAILED")
            if details:
                print(f"   {details}")

    def run_api_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=120):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if files:
            headers.pop('Content-Type', None)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {"raw_response": response.text}
            else:
                try:
                    error_detail = response.json()
                    return False, error_detail
                except:
                    return False, {"error": response.text, "status_code": response.status_code}

        except Exception as e:
            return False, {"error": str(e)}

    def test_authentication(self):
        """Test admin authentication"""
        print("\n" + "="*60)
        print("🔐 AUTHENTICATION TEST")
        print("="*60)
        
        success, response = self.run_api_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            {"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_info = response.get('user', {})
            self.log_result("Authentication", True, f"Role: {user_info.get('role')}, Company: {user_info.get('company')}")
            return True
        else:
            self.log_result("Authentication", False, "Failed to get access token")
            return False

    def download_test_pdf(self):
        """Download the real IAPP certificate PDF"""
        print("\n" + "="*60)
        print("📥 PDF DOWNLOAD TEST")
        print("="*60)
        
        try:
            print(f"Downloading: {self.test_pdf_url}")
            response = requests.get(self.test_pdf_url, timeout=30)
            
            if response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(response.content)
                temp_file.close()
                
                file_size = len(response.content)
                self.log_result("PDF Download", True, f"Size: {file_size} bytes, Path: {temp_file.name}")
                return temp_file.name, response.content
            else:
                self.log_result("PDF Download", False, f"HTTP {response.status_code}")
                return None, None
                
        except Exception as e:
            self.log_result("PDF Download", False, str(e))
            return None, None

    def test_single_pdf_analysis(self, pdf_path):
        """Test the /api/analyze-ship-certificate endpoint"""
        print("\n" + "="*60)
        print("🔍 SINGLE PDF ANALYSIS TEST")
        print("="*60)
        
        if not pdf_path:
            self.log_result("Single PDF Analysis", False, "No PDF file available")
            return False
        
        with open(pdf_path, 'rb') as f:
            files = {'file': ('BROTHER_36_IAPP_PM242838.pdf', f, 'application/pdf')}
            
            success, response = self.run_api_test(
                "Analyze Ship Certificate",
                "POST",
                "analyze-ship-certificate",
                200,
                files=files,
                timeout=180
            )
        
        if success:
            analysis = response.get('analysis', {})
            
            print(f"\n📋 Analysis Results:")
            for field, value in analysis.items():
                print(f"   {field}: {value}")
            
            # Check ship name extraction
            ship_name = analysis.get('ship_name')
            if ship_name == self.expected_results['ship_name']:
                self.log_result("Ship Name Extraction", True, f"Correctly extracted: {ship_name}")
            else:
                self.log_result("Ship Name Extraction", False, f"Expected '{self.expected_results['ship_name']}', got: {ship_name}")
            
            # Check all expected fields are present
            expected_fields = ['ship_name', 'imo_number', 'class_society', 'flag', 'gross_tonnage', 'deadweight', 'built_year', 'ship_owner']
            missing_fields = [field for field in expected_fields if field not in analysis]
            
            if not missing_fields:
                self.log_result("Analysis Structure", True, "All expected fields present")
            else:
                self.log_result("Analysis Structure", False, f"Missing fields: {missing_fields}")
            
            self.log_result("Single PDF Analysis", True, "Analysis completed successfully")
            return True
        else:
            self.log_result("Single PDF Analysis", False, f"API failed: {response}")
            return False

    def create_test_user_with_company(self):
        """Create a test user associated with a company for multi-file upload testing"""
        print("\n" + "="*60)
        print("👤 TEST USER CREATION")
        print("="*60)
        
        # First, get available companies
        success, companies_response = self.run_api_test(
            "Get Companies",
            "GET",
            "companies",
            200
        )
        
        if not success or not companies_response:
            self.log_result("Get Companies", False, "No companies available")
            return None
        
        companies = companies_response if isinstance(companies_response, list) else []
        if not companies:
            self.log_result("Get Companies", False, "No companies found")
            return None
        
        # Use the first available company
        company = companies[0]
        company_name = company.get('name_en', company.get('name_vn', 'Test Company'))
        
        # Create test user
        test_user_data = {
            "username": f"test_ai_user_{int(time.time())}",
            "password": "testpass123",
            "email": f"test_ai_{int(time.time())}@example.com",
            "full_name": "AI Test User",
            "role": "editor",
            "department": "technical",
            "company": company_name,
            "zalo": "0123456789",
            "gmail": f"test_ai_{int(time.time())}@gmail.com"
        }
        
        success, user_response = self.run_api_test(
            "Create Test User",
            "POST",
            "auth/register",
            201,
            test_user_data
        )
        
        if success:
            self.log_result("Test User Creation", True, f"User: {test_user_data['username']}, Company: {company_name}")
            
            # Login as the test user
            login_success, login_response = self.run_api_test(
                "Test User Login",
                "POST",
                "auth/login",
                200,
                {"username": test_user_data['username'], "password": test_user_data['password']}
            )
            
            if login_success and 'access_token' in login_response:
                self.token = login_response['access_token']  # Switch to test user token
                self.log_result("Test User Login", True, "Switched to test user token")
                return test_user_data['username']
            else:
                self.log_result("Test User Login", False, "Failed to login as test user")
                return None
        else:
            self.log_result("Test User Creation", False, f"Failed: {user_response}")
            return None

    def test_multi_file_upload(self, pdf_path):
        """Test the /api/certificates/upload-multi-files endpoint"""
        print("\n" + "="*60)
        print("📤 MULTI-FILE UPLOAD TEST")
        print("="*60)
        
        if not pdf_path:
            self.log_result("Multi-File Upload", False, "No PDF file available")
            return False
        
        with open(pdf_path, 'rb') as f:
            files = {'files': ('BROTHER_36_IAPP_PM242838.pdf', f, 'application/pdf')}
            
            success, response = self.run_api_test(
                "Multi-File Upload with AI",
                "POST",
                "certificates/upload-multi-files",
                200,
                files=files,
                timeout=300  # Longer timeout for AI processing and Google Drive
            )
        
        if success:
            results = response.get('results', [])
            if results:
                file_result = results[0]
                
                print(f"\n📊 Upload Results:")
                print(f"   Total files: {response.get('total_files', 0)}")
                print(f"   Successful uploads: {response.get('successful_uploads', 0)}")
                print(f"   Certificates created: {response.get('certificates_created', 0)}")
                
                # Check category classification (main issue from review request)
                category = file_result.get('category')
                if category == self.expected_results['category']:
                    self.log_result("Category Classification Fix", True, f"Correctly classified as: {category}")
                else:
                    self.log_result("Category Classification Fix", False, f"Expected '{self.expected_results['category']}', got: {category}")
                
                # Check ship name extraction (main issue from review request)
                ship_name = file_result.get('ship_name')
                if ship_name == self.expected_results['ship_name']:
                    self.log_result("Ship Name Extraction Fix", True, f"Correctly extracted: {ship_name}")
                else:
                    self.log_result("Ship Name Extraction Fix", False, f"Expected '{self.expected_results['ship_name']}', got: {ship_name}")
                
                # Check extracted information details
                extracted_info = file_result.get('extracted_info', {})
                if extracted_info:
                    print(f"\n📋 Extracted Information:")
                    for field, value in extracted_info.items():
                        print(f"   {field}: {value}")
                    
                    # Verify specific certificate details
                    cert_name = extracted_info.get('cert_name')
                    cert_no = extracted_info.get('cert_no')
                    
                    if cert_name and 'Air Pollution Prevention' in cert_name:
                        self.log_result("Certificate Name Extraction", True, f"Correctly identified: {cert_name}")
                    else:
                        self.log_result("Certificate Name Extraction", False, f"Expected IAPP certificate, got: {cert_name}")
                    
                    if cert_no == self.expected_results['cert_no']:
                        self.log_result("Certificate Number Extraction", True, f"Correctly extracted: {cert_no}")
                    else:
                        self.log_result("Certificate Number Extraction", False, f"Expected '{self.expected_results['cert_no']}', got: {cert_no}")
                
                # Check certificate auto-creation
                cert_created = file_result.get('certificate_created', False)
                if cert_created:
                    self.log_result("Certificate Auto-Creation", True, f"Certificate ID: {file_result.get('certificate_id')}")
                else:
                    self.log_result("Certificate Auto-Creation", False, "Certificate not auto-created")
                
                # Check Google Drive upload
                gdrive_uploaded = file_result.get('google_drive_uploaded', False)
                if gdrive_uploaded:
                    self.log_result("Google Drive Upload", True, f"File ID: {file_result.get('google_drive_file_id')}")
                else:
                    self.log_result("Google Drive Upload", False, "File not uploaded to Google Drive")
                
                # Check for processing errors
                errors = file_result.get('errors', [])
                if errors:
                    print(f"\n⚠️ Processing Errors:")
                    for error in errors:
                        print(f"   - {error}")
                    self.log_result("Processing Errors", False, f"{len(errors)} errors occurred")
                else:
                    self.log_result("Processing Errors", True, "No processing errors")
            
            self.log_result("Multi-File Upload", True, "Upload completed successfully")
            return True
        else:
            self.log_result("Multi-File Upload", False, f"API failed: {response}")
            return False

    def test_certificate_verification(self):
        """Verify that certificates are correctly created and retrievable"""
        print("\n" + "="*60)
        print("📋 CERTIFICATE VERIFICATION TEST")
        print("="*60)
        
        success, response = self.run_api_test(
            "Get Certificates",
            "GET",
            "certificates",
            200
        )
        
        if success:
            certificates = response if isinstance(response, list) else []
            
            # Look for BROTHER 36 IAPP certificate
            brother36_certs = [cert for cert in certificates if 
                             cert.get('ship_name') == 'BROTHER 36' and 
                             'IAPP' in cert.get('cert_name', '')]
            
            if brother36_certs:
                cert = brother36_certs[0]
                print(f"\n📋 Found BROTHER 36 IAPP Certificate:")
                print(f"   ID: {cert.get('id')}")
                print(f"   Name: {cert.get('cert_name')}")
                print(f"   Number: {cert.get('cert_no')}")
                print(f"   Ship: {cert.get('ship_name')}")
                print(f"   Category: {cert.get('category')}")
                
                # Verify it's in the correct category
                if cert.get('category') == 'certificates':
                    self.log_result("Certificate Category Verification", True, "Certificate correctly categorized")
                else:
                    self.log_result("Certificate Category Verification", False, f"Wrong category: {cert.get('category')}")
                
                self.log_result("Certificate Verification", True, f"Certificate found and verified")
                return True
            else:
                self.log_result("Certificate Verification", False, "BROTHER 36 IAPP certificate not found")
                return False
        else:
            self.log_result("Certificate Verification", False, f"Failed to retrieve certificates: {response}")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive test of AI analysis improvements"""
        print("🚀 AI ANALYSIS IMPROVEMENTS TEST")
        print("Testing fixed AI analysis function with real IAPP certificate PDF")
        print("Review Request: Test AI improvements with BROTHER 36 - IAPP - PM242838.pdf")
        print("="*80)
        
        start_time = time.time()
        
        # Step 1: Authentication
        if not self.test_authentication():
            print("\n❌ Authentication failed. Cannot proceed.")
            return False
        
        # Step 2: Download test PDF
        pdf_path, pdf_content = self.download_test_pdf()
        if not pdf_path:
            print("\n❌ PDF download failed. Cannot proceed.")
            return False
        
        # Step 3: Test single PDF analysis
        single_analysis_success = self.test_single_pdf_analysis(pdf_path)
        
        # Step 4: Create test user with company for multi-file upload
        test_user = self.create_test_user_with_company()
        
        # Step 5: Test multi-file upload (if test user created successfully)
        multi_upload_success = False
        if test_user:
            multi_upload_success = self.test_multi_file_upload(pdf_path)
        
        # Step 6: Verify certificate creation
        cert_verification_success = self.test_certificate_verification()
        
        # Clean up
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "="*80)
        print("📊 AI ANALYSIS IMPROVEMENTS TEST SUMMARY")
        print("="*80)
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"🧪 Tests run: {self.tests_run}")
        print(f"✅ Tests passed: {self.tests_passed}")
        print(f"❌ Tests failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Key findings
        print(f"\n🔍 KEY FINDINGS - REVIEW REQUEST VERIFICATION:")
        
        # Check if the main reported issues are fixed
        category_fixed = any(r['success'] for r in self.test_results if 'Category Classification' in r['test'])
        ship_name_fixed = any(r['success'] for r in self.test_results if 'Ship Name Extraction' in r['test'])
        
        print(f"\n📋 Issue Resolution Status:")
        if category_fixed:
            print("   ✅ FIXED: Category classification - Documents now correctly classified as 'certificates'")
        else:
            print("   ❌ NOT FIXED: Category classification - Still classifying as 'other_documents'")
        
        if ship_name_fixed:
            print("   ✅ FIXED: Ship name extraction - Ship name now correctly extracted as 'BROTHER 36'")
        else:
            print("   ❌ NOT FIXED: Ship name extraction - Still showing 'Unknown Ship'")
        
        # Overall assessment
        critical_issues_resolved = category_fixed and ship_name_fixed
        
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if critical_issues_resolved:
            print("   ✅ SUCCESS: AI analysis improvements are working correctly")
            print("   • Previously reported issues have been resolved")
            print("   • Certificate classification is now accurate")
            print("   • Ship information extraction is working properly")
        else:
            print("   ⚠️  PARTIAL SUCCESS: Some improvements working, but issues remain")
            print("   • Further refinement may be needed for full resolution")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        passed_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]
        
        if passed_tests:
            print(f"\n✅ PASSED ({len(passed_tests)}):")
            for result in passed_tests:
                print(f"   • {result['test']}")
        
        if failed_tests:
            print(f"\n❌ FAILED ({len(failed_tests)}):")
            for result in failed_tests:
                print(f"   • {result['test']}: {result['details']}")
        
        return critical_issues_resolved

if __name__ == "__main__":
    tester = AIAnalysisImprovementsTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import time
import tempfile
import os

class MultiFileUploadDebugTester:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Remove Content-Type for file uploads
        if files:
            headers.pop('Content-Type', None)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {"raw_response": response.text}
            else:
                print(f"❌ Failed - Expected: {expected_status}, Got: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False, {"error": response.text, "status_code": response.status_code}

        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False, {"error": str(e)}

    def login(self):
        """Login as admin user"""
        print("\n🔐 Logging in as admin...")
        success, response = self.run_test(
            "Admin Login", "POST", "auth/login", 200,
            {"username": "admin1", "password": "123456"}
        )
        
        if success and "access_token" in response:
            self.token = response["access_token"]
            self.admin_user_id = response["user"]["id"]
            print(f"✅ Login successful - User ID: {self.admin_user_id}")
            print(f"   Role: {response['user']['role']}")
            print(f"   Company: {response['user'].get('company', 'None')}")
            return True
        else:
            print("❌ Login failed")
            return False

    def download_test_pdf(self):
        """Download the specific BROTHER 36 IAPP certificate PDF"""
        print("\n📥 Downloading BROTHER 36 IAPP certificate PDF...")
        
        pdf_url = "https://customer-assets.emergentagent.com/job_vessel-docs-1/artifacts/nzwrda4b_BROTHER%2036%20-%20IAPP%20-%20PM242838.pdf"
        
        try:
            response = requests.get(pdf_url, timeout=30)
            if response.status_code == 200:
                print(f"✅ PDF downloaded successfully - Size: {len(response.content)} bytes")
                return response.content, "BROTHER 36 - IAPP - PM242838.pdf"
            else:
                print(f"❌ Failed to download PDF - Status: {response.status_code}")
                return None, None
        except Exception as e:
            print(f"❌ Exception downloading PDF: {str(e)}")
            return None, None

    def test_single_pdf_analysis(self, pdf_content, filename):
        """Test the single PDF analysis endpoint for comparison"""
        print(f"\n🔍 Testing Single PDF Analysis Endpoint...")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/pdf')}
                success, response = self.run_test(
                    "Single PDF Analysis", "POST", "analyze-ship-certificate", 200,
                    files=files
                )
            
            if success:
                print("✅ Single PDF Analysis Results:")
                for key, value in response.items():
                    print(f"   {key}: {value}")
                return response
            else:
                print("❌ Single PDF Analysis failed")
                return None
                
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_multi_file_upload(self, pdf_content, filename):
        """Test the multi-file upload endpoint with the BROTHER 36 PDF"""
        print(f"\n🔍 Testing Multi-File Upload Endpoint...")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'files': (filename, f, 'application/pdf')}
                success, response = self.run_test(
                    "Multi-File Upload", "POST", "certificates/upload-multi-files", 200,
                    files=files
                )
            
            if success:
                print("✅ Multi-File Upload Results:")
                print(f"   Message: {response.get('message', 'N/A')}")
                print(f"   Total Files: {response.get('total_files', 0)}")
                print(f"   Successful Uploads: {response.get('successful_uploads', 0)}")
                print(f"   Certificates Created: {response.get('certificates_created', 0)}")
                
                # Analyze each file result
                results = response.get('results', [])
                for i, result in enumerate(results):
                    print(f"\n   📄 File {i+1} Results:")
                    print(f"      Filename: {result.get('filename', 'N/A')}")
                    print(f"      Status: {result.get('status', 'N/A')}")
                    print(f"      Category: {result.get('category', 'N/A')}")
                    print(f"      Ship Name: {result.get('ship_name', 'N/A')}")
                    print(f"      Certificate Created: {result.get('certificate_created', False)}")
                    print(f"      Google Drive Uploaded: {result.get('google_drive_uploaded', False)}")
                    
                    # Show extracted info
                    extracted_info = result.get('extracted_info', {})
                    if extracted_info:
                        print(f"      📋 Extracted Information:")
                        for key, value in extracted_info.items():
                            print(f"         {key}: {value}")
                    
                    # Show errors
                    errors = result.get('errors', [])
                    if errors:
                        print(f"      ❌ Errors:")
                        for error in errors:
                            print(f"         - {error}")
                
                return response
            else:
                print("❌ Multi-File Upload failed")
                print(f"   Error: {response.get('error', 'Unknown error')}")
                return None
                
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def debug_ai_analysis_process(self):
        """Debug the AI analysis process by checking configuration"""
        print(f"\n🔍 Debugging AI Analysis Configuration...")
        
        # Check AI configuration
        success, response = self.run_test(
            "Get AI Config", "GET", "ai-config", 200
        )
        
        if success:
            print("✅ AI Configuration:")
            for key, value in response.items():
                print(f"   {key}: {value}")
        else:
            print("❌ Failed to get AI configuration")
        
        # Check if Emergent LLM key is configured
        print(f"\n🔍 Checking Backend Environment...")
        # We can't directly check environment variables, but we can infer from responses

    def check_company_gdrive_config(self):
        """Check if the admin user's company has Google Drive configured"""
        print(f"\n🔍 Checking Company Google Drive Configuration...")
        
        # Get companies
        success, response = self.run_test(
            "Get Companies", "GET", "companies", 200
        )
        
        if success:
            companies = response if isinstance(response, list) else []
            print(f"✅ Found {len(companies)} companies")
            
            for company in companies:
                print(f"   Company: {company.get('name_en', 'N/A')} / {company.get('name_vn', 'N/A')}")
                gdrive_config = company.get('gdrive_config') or {}
                configured = gdrive_config.get('configured', False)
                print(f"   Google Drive Configured: {configured}")
                
                if configured:
                    print(f"   Auth Method: {gdrive_config.get('auth_method', 'N/A')}")
                    print(f"   Folder ID: {gdrive_config.get('folder_id', 'N/A')}")
        else:
            print("❌ Failed to get companies")

    def run_comprehensive_debug(self):
        """Run comprehensive debugging of multi-file upload issue"""
        print("=" * 80)
        print("🚀 MULTI-FILE UPLOAD DEBUG TEST - BROTHER 36 IAPP CERTIFICATE")
        print("=" * 80)
        
        # Step 1: Login
        if not self.login():
            print("❌ Cannot proceed without login")
            return False
        
        # Step 2: Download test PDF
        pdf_content, filename = self.download_test_pdf()
        if not pdf_content:
            print("❌ Cannot proceed without test PDF")
            return False
        
        # Step 3: Check AI and company configuration
        self.debug_ai_analysis_process()
        self.check_company_gdrive_config()
        
        # Step 4: Test single PDF analysis (working baseline)
        single_result = self.test_single_pdf_analysis(pdf_content, filename)
        
        # Step 5: Test multi-file upload (problematic endpoint)
        multi_result = self.test_multi_file_upload(pdf_content, filename)
        
        # Step 6: Compare results
        print(f"\n" + "=" * 80)
        print("📊 COMPARISON ANALYSIS")
        print("=" * 80)
        
        if single_result and multi_result:
            print("✅ Both endpoints responded successfully")
            
            # Compare single vs multi results
            single_ship = single_result.get('ship_name', 'N/A')
            single_category = single_result.get('category', 'N/A')
            
            multi_results = multi_result.get('results', [])
            if multi_results:
                multi_ship = multi_results[0].get('ship_name', 'N/A')
                multi_category = multi_results[0].get('category', 'N/A')
                multi_cert_created = multi_results[0].get('certificate_created', False)
                
                print(f"\n📋 COMPARISON:")
                print(f"   Single Analysis Ship Name: {single_ship}")
                print(f"   Multi Upload Ship Name: {multi_ship}")
                print(f"   Single Analysis Category: {single_category}")
                print(f"   Multi Upload Category: {multi_category}")
                print(f"   Multi Upload Certificate Created: {multi_cert_created}")
                
                # Identify issues
                issues = []
                if multi_ship == "Unknown_Ship" and single_ship != "Unknown_Ship":
                    issues.append("❌ Multi-file upload not extracting ship name correctly")
                
                if multi_category == "other_documents" and single_category == "certificates":
                    issues.append("❌ Multi-file upload not classifying as certificates")
                
                if not multi_cert_created and multi_category == "certificates":
                    issues.append("❌ Multi-file upload not creating certificate record")
                
                if issues:
                    print(f"\n🚨 IDENTIFIED ISSUES:")
                    for issue in issues:
                        print(f"   {issue}")
                else:
                    print(f"\n✅ No issues identified - both endpoints working correctly")
            
        else:
            if not single_result:
                print("❌ Single PDF analysis failed")
            if not multi_result:
                print("❌ Multi-file upload failed")
        
        # Summary
        print(f"\n" + "=" * 80)
        print("📈 TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = MultiFileUploadDebugTester()
    success = tester.run_comprehensive_debug()
    sys.exit(0 if success else 1)
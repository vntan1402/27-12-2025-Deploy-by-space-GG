#!/usr/bin/env python3
"""
Multi-File Upload with Enhanced Date Parsing Test
Focus: Debug "Invalid time value" error in AI analysis date parsing
"""

import requests
import json
import time
import os
import sys
from datetime import datetime, timezone

class DateParsingTester:
    def __init__(self, base_url="https://aicert-analyzer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_info = None

    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=60):
        """Run a single API test with enhanced error reporting"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Don't set Content-Type for file uploads - let requests handle it
        if not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        self.log(f"Testing {name}...")
        self.log(f"   URL: {url}")
        
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
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}", "PASS")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}", "FAIL")
                try:
                    error_detail = response.json()
                    self.log(f"   Error: {json.dumps(error_detail, indent=2)}", "ERROR")
                except:
                    self.log(f"   Error: {response.text}", "ERROR")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}", "FAIL")
            return False, {}

    def test_login(self, username="admin", password="admin123"):
        """Test login and get token"""
        self.log(f"🔐 Testing Authentication with {username}/{password}")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_info = response.get('user', {})
            self.log(f"✅ Login successful")
            self.log(f"   User: {self.user_info.get('full_name')} ({self.user_info.get('role')})")
            self.log(f"   Company: {self.user_info.get('company')}")
            return True
        return False

    def test_alternative_login(self):
        """Test alternative login credentials"""
        self.log("🔐 Trying alternative login credentials...")
        
        # Try admin1/123456
        if self.test_login("admin1", "123456"):
            return True
        
        # Try admin/admin123 again
        if self.test_login("admin", "admin123"):
            return True
            
        return False

    def check_backend_logs(self):
        """Check backend logs for date parsing errors"""
        self.log("📋 Checking backend logs for date parsing issues...")
        try:
            # Check supervisor backend logs
            result = os.popen("tail -n 100 /var/log/supervisor/backend.*.log 2>/dev/null").read()
            if result:
                self.log("Backend logs (last 100 lines):")
                lines = result.split('\n')
                # Look for relevant log entries
                for line in lines[-50:]:  # Show last 50 lines
                    if line.strip() and any(keyword in line.lower() for keyword in 
                                          ['date', 'time', 'parse', 'invalid', 'error', 'ai analysis']):
                        self.log(f"   {line}")
            else:
                self.log("No backend logs found or accessible")
        except Exception as e:
            self.log(f"Error reading backend logs: {e}", "ERROR")

    def test_multi_file_upload_with_brother36(self):
        """Test multi-file upload with BROTHER 36 certificate PDF"""
        self.log("🚢 Testing Multi-File Upload with BROTHER 36 Certificate")
        
        # Check if PDF file exists
        pdf_path = "/app/brother36_certificate.pdf"
        if not os.path.exists(pdf_path):
            self.log(f"❌ BROTHER 36 certificate PDF not found at {pdf_path}", "ERROR")
            return False
        
        file_size = os.path.getsize(pdf_path)
        self.log(f"📄 Found BROTHER 36 certificate PDF ({file_size} bytes)")
        
        try:
            # Prepare file for upload
            with open(pdf_path, 'rb') as f:
                files = {
                    'files': ('brother36_certificate.pdf', f, 'application/pdf')
                }
                
                self.log("🔄 Uploading BROTHER 36 certificate for AI analysis...")
                self.log("   This will test the enhanced date parsing functionality")
                
                # Check backend logs before upload
                self.log("📋 Backend logs before upload:")
                self.check_backend_logs()
                
                success, response = self.run_test(
                    "Multi-File Upload with AI Processing",
                    "POST",
                    "certificates/upload-multi-files",
                    200,
                    files=files,
                    timeout=120  # Longer timeout for AI processing
                )
                
                # Check backend logs after upload
                self.log("📋 Backend logs after upload:")
                self.check_backend_logs()
                
                if success:
                    self.log("✅ Multi-file upload completed successfully")
                    self.log(f"   Response: {json.dumps(response, indent=2)}")
                    
                    # Analyze the response for date parsing issues
                    self.analyze_upload_response(response)
                    return True
                else:
                    self.log("❌ Multi-file upload failed", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error during multi-file upload: {str(e)}", "ERROR")
            # Check logs after error
            self.check_backend_logs()
            return False

    def analyze_upload_response(self, response):
        """Analyze upload response for date parsing issues"""
        self.log("🔍 Analyzing upload response for date parsing issues...")
        
        results = response.get('results', [])
        for i, result in enumerate(results):
            filename = result.get('filename', f'file_{i}')
            self.log(f"📄 File: {filename}")
            self.log(f"   Status: {result.get('status')}")
            self.log(f"   Category: {result.get('category')}")
            self.log(f"   Ship Name: {result.get('ship_name')}")
            self.log(f"   Certificate Created: {result.get('certificate_created')}")
            
            # Check for errors
            errors = result.get('errors', [])
            if errors:
                self.log(f"   ❌ Errors found:")
                for error in errors:
                    self.log(f"      - {error}")
                    if "Invalid time value" in error:
                        self.log("   🎯 FOUND 'Invalid time value' error!", "CRITICAL")
            
            # Check extracted info for date values
            extracted_info = result.get('extracted_info', {})
            if extracted_info:
                self.log(f"   📊 Extracted Information:")
                date_fields = ['issue_date', 'valid_date', 'last_endorse', 'next_survey']
                for field in date_fields:
                    if field in extracted_info:
                        value = extracted_info[field]
                        self.log(f"      {field}: '{value}' (type: {type(value).__name__})")

    def test_single_pdf_analysis(self):
        """Test single PDF analysis endpoint for comparison"""
        self.log("🔍 Testing Single PDF Analysis for comparison...")
        
        pdf_path = "/app/brother36_certificate.pdf"
        if not os.path.exists(pdf_path):
            self.log(f"❌ PDF not found at {pdf_path}", "ERROR")
            return False
        
        try:
            with open(pdf_path, 'rb') as f:
                files = {
                    'file': ('brother36_certificate.pdf', f, 'application/pdf')
                }
                
                success, response = self.run_test(
                    "Single PDF Analysis",
                    "POST",
                    "analyze-ship-certificate",
                    200,
                    files=files,
                    timeout=60
                )
                
                if success:
                    self.log("✅ Single PDF analysis completed")
                    self.log(f"   Response: {json.dumps(response, indent=2)}")
                    
                    # Check for date values in response
                    date_fields = ['issue_date', 'valid_date', 'last_endorse', 'next_survey']
                    for field in date_fields:
                        if field in response:
                            value = response[field]
                            self.log(f"   {field}: '{value}' (type: {type(value).__name__})")
                    
                    return True
                else:
                    self.log("❌ Single PDF analysis failed", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error during single PDF analysis: {str(e)}", "ERROR")
            return False

    def test_companies_endpoint(self):
        """Test companies endpoint to ensure user has access"""
        self.log("🏢 Testing Companies endpoint access...")
        
        success, response = self.run_test(
            "Get Companies",
            "GET",
            "companies",
            200
        )
        
        if success:
            companies = response if isinstance(response, list) else []
            self.log(f"✅ Found {len(companies)} companies")
            for company in companies:
                self.log(f"   - {company.get('name_en', 'N/A')} / {company.get('name_vn', 'N/A')}")
            return True
        else:
            self.log("❌ Failed to access companies endpoint", "ERROR")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive multi-file upload test"""
        self.log("🚢 Starting Multi-File Upload with Enhanced Date Parsing Test")
        self.log("=" * 80)
        
        # Test authentication
        if not self.test_alternative_login():
            self.log("❌ Authentication failed with all credentials", "CRITICAL")
            return False
        
        # Test companies access
        companies_success = self.test_companies_endpoint()
        if not companies_success:
            self.log("❌ Companies access failed", "ERROR")
        
        # Test single PDF analysis first
        self.log("\n" + "=" * 50)
        self.log("PHASE 1: Single PDF Analysis Test")
        self.log("=" * 50)
        single_analysis_success = self.test_single_pdf_analysis()
        
        # Test multi-file upload
        self.log("\n" + "=" * 50)
        self.log("PHASE 2: Multi-File Upload Test")
        self.log("=" * 50)
        multi_upload_success = self.test_multi_file_upload_with_brother36()
        
        # Final summary
        self.log("\n" + "=" * 80)
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("=" * 80)
        self.log(f"Authentication: {'✅ PASSED' if self.token else '❌ FAILED'}")
        self.log(f"Companies Access: {'✅ PASSED' if companies_success else '❌ FAILED'}")
        self.log(f"Single PDF Analysis: {'✅ PASSED' if single_analysis_success else '❌ FAILED'}")
        self.log(f"Multi-File Upload: {'✅ PASSED' if multi_upload_success else '❌ FAILED'}")
        self.log(f"Overall API Tests: {self.tests_passed}/{self.tests_run}")
        
        if self.user_info:
            self.log(f"User: {self.user_info.get('full_name')} ({self.user_info.get('role')})")
            self.log(f"Company: {self.user_info.get('company')}")
        
        # Check final backend logs
        self.log("\n📋 Final Backend Logs Check:")
        self.check_backend_logs()
        
        return multi_upload_success

def main():
    """Main test execution"""
    tester = DateParsingTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Focused Date Parsing Test for Multi-File Upload
Tests the specific "Invalid time value" error in AI analysis date parsing
"""

import requests
import json
import time
import os
import sys
from datetime import datetime, timezone

class FocusedDateParsingTester:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
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

    def test_login(self, username="admin1", password="123456"):
        """Test login and get token"""
        self.log(f"🔐 Testing Authentication with {username}/{password}")
        success, response = self.run_test(
            "Login",
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

    def check_backend_logs(self):
        """Check backend logs for date parsing errors"""
        self.log("📋 Checking backend logs for date parsing issues...")
        try:
            # Check supervisor backend logs
            result = os.popen("tail -n 200 /var/log/supervisor/backend.*.log 2>/dev/null | grep -i -E '(date|time|parse|invalid|ai analysis|issue_date|valid_date)'").read()
            if result:
                self.log("Relevant backend log entries:")
                for line in result.split('\n'):
                    if line.strip():
                        self.log(f"   {line}")
            else:
                self.log("No relevant date parsing log entries found")
        except Exception as e:
            self.log(f"Error reading backend logs: {e}", "ERROR")

    def test_multi_file_upload_with_test_certificate(self):
        """Test multi-file upload with test certificate containing date information"""
        self.log("🚢 Testing Multi-File Upload with Test Certificate (Contains Date Info)")
        
        # Check if test certificate file exists
        cert_path = "/app/test_certificate.txt"
        if not os.path.exists(cert_path):
            self.log(f"❌ Test certificate not found at {cert_path}", "ERROR")
            return False
        
        file_size = os.path.getsize(cert_path)
        self.log(f"📄 Found test certificate ({file_size} bytes)")
        
        try:
            # Prepare file for upload
            with open(cert_path, 'rb') as f:
                files = {
                    'files': ('brother36_test_certificate.txt', f, 'text/plain')
                }
                
                self.log("🔄 Uploading test certificate for AI analysis...")
                self.log("   This certificate contains specific date formats to test parsing")
                
                # Check backend logs before upload
                self.log("📋 Backend logs before upload:")
                self.check_backend_logs()
                
                success, response = self.run_test(
                    "Multi-File Upload with Test Certificate",
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
                        self.log("   This is the error we're debugging!", "CRITICAL")
            else:
                self.log("   ✅ No errors found in processing")
            
            # Check extracted info for date values
            extracted_info = result.get('extracted_info', {})
            if extracted_info:
                self.log(f"   📊 Extracted Information:")
                date_fields = ['issue_date', 'valid_date', 'last_endorse', 'next_survey']
                for field in date_fields:
                    if field in extracted_info:
                        value = extracted_info[field]
                        self.log(f"      {field}: '{value}' (type: {type(value).__name__})")
                        
                        # If we have a date value, let's analyze its format
                        if value and value != 'None' and value is not None:
                            self.log(f"      🔍 Analyzing date format for {field}: '{value}'")
                            self.test_date_parsing(field, value)
            else:
                self.log("   ⚠️ No extracted information found")

    def test_date_parsing(self, field_name, date_value):
        """Test date parsing with the specific value returned by AI"""
        self.log(f"🧪 Testing date parsing for {field_name}: '{date_value}'")
        
        # Try to parse the date using the same logic as the backend
        try:
            from datetime import datetime
            
            # Clean the date string
            date_str = str(date_value).strip()
            
            # Try ISO format first
            if 'T' in date_str:
                parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                self.log(f"   ✅ Successfully parsed as ISO format: {parsed_date}")
                return True
            else:
                # Try various date formats
                date_formats = [
                    '%Y-%m-%d',           # 2024-12-10
                    '%d/%m/%Y',           # 10/12/2024
                    '%m/%d/%Y',           # 12/10/2024
                    '%d-%m-%Y',           # 10-12-2024
                    '%Y/%m/%d',           # 2024/12/10
                    '%B %d, %Y',          # December 10, 2024
                    '%d %B %Y',           # 10 December 2024
                    '%b %d, %Y',          # Dec 10, 2024
                ]
                
                for date_format in date_formats:
                    try:
                        parsed_date = datetime.strptime(date_str, date_format)
                        self.log(f"   ✅ Successfully parsed with format '{date_format}': {parsed_date}")
                        return True
                    except ValueError:
                        continue
                        
            # If all formats fail
            self.log(f"   ❌ Unable to parse date string: '{date_str}'", "ERROR")
            self.log(f"   🎯 This could be the source of 'Invalid time value' error!", "CRITICAL")
            return False
            
        except Exception as e:
            self.log(f"   ❌ Error parsing date string '{date_value}': {e}", "ERROR")
            return False

    def test_various_date_formats(self):
        """Test various date formats that might cause issues"""
        self.log("🧪 Testing Various Date Formats That Might Cause Issues")
        
        problematic_dates = [
            "2024-12-10T00:00:00Z",
            "2024-12-10",
            "10/12/2024",
            "12/10/2024", 
            "December 10, 2024",
            "10 December 2024",
            "Dec 10, 2024",
            "2024/12/10",
            "10-12-2024",
            "null",
            "None",
            "",
            "N/A",
            "Invalid Date",
            "2024-13-45",  # Invalid date
            "2024-02-30",  # Invalid date
        ]
        
        for date_str in problematic_dates:
            self.test_date_parsing("test_field", date_str)

    def run_comprehensive_test(self):
        """Run comprehensive date parsing test"""
        self.log("🚢 Starting Focused Date Parsing Test for Multi-File Upload")
        self.log("=" * 80)
        
        # Test authentication
        if not self.test_login():
            self.log("❌ Authentication failed", "CRITICAL")
            return False
        
        # Test various date formats first
        self.log("\n" + "=" * 50)
        self.log("PHASE 1: Date Format Testing")
        self.log("=" * 50)
        self.test_various_date_formats()
        
        # Test multi-file upload with test certificate
        self.log("\n" + "=" * 50)
        self.log("PHASE 2: Multi-File Upload with Test Certificate")
        self.log("=" * 50)
        multi_upload_success = self.test_multi_file_upload_with_test_certificate()
        
        # Final summary
        self.log("\n" + "=" * 80)
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("=" * 80)
        self.log(f"Authentication: {'✅ PASSED' if self.token else '❌ FAILED'}")
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
    tester = FocusedDateParsingTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
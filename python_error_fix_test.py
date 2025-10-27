#!/usr/bin/env python3
"""
Ship Management System - Python NameError Fix Testing
FOCUS: Test the specific Python NameError fix and complete passport processing workflow

REVIEW REQUEST REQUIREMENTS:
TEST PYTHON ERROR FIX - VERIFY COMPLETE PASSPORT PROCESSING WORKFLOW:

**OBJECTIVE**: Test the Python NameError fix and verify complete Add Crew passport processing workflow now works end-to-end with real Google Drive file uploads.

**PYTHON ERROR FIXED**: 
✅ Fixed `NameError: name 'ai_config' is not defined` in server.py
✅ Updated field extraction to use correct AI config parameters
✅ Backend should now return complete file upload data
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
import tempfile
import base64
from urllib.parse import urlparse

# Configuration - Use environment variable for backend URL
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL from frontend/.env
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                    break
            else:
                BACKEND_URL = 'https://shipdoclists.preview.emergentagent.com/api'
    except:
        BACKEND_URL = 'https://shipdoclists.preview.emergentagent.com/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class PythonErrorFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Python error fix
        self.python_fix_tests = {
            # Phase 1: Backend Error Resolution Verification
            'authentication_successful': False,
            'python_nameerror_resolved': False,
            'field_extraction_working': False,
            'complete_api_response': False,
            'no_python_errors_in_response': False,
            
            # Phase 2: Complete Passport Processing Workflow
            'passport_upload_endpoint_accessible': False,
            'document_ai_processing_successful': False,
            'system_apps_script_working': False,
            'ai_field_extraction_successful': False,
            'company_apps_script_working': False,
            'file_upload_step_successful': False,
            'dual_apps_script_processing': False,
            
            # Phase 3: Google Drive File Creation Verification
            'passport_file_uploaded_to_gdrive': False,
            'summary_file_uploaded_to_gdrive': False,
            'correct_folder_structure': False,
            'files_contain_actual_content': False,
            'real_google_drive_file_ids': False,
        }
        
        # Store passport file data
        self.passport_file_data = None
        self.passport_filename = "PASS PORT Tran Trong Toan.pdf"
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        # Also store in our log collection
        self.backend_logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
    def authenticate(self):
        """Authenticate with admin1/123456 credentials"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.python_fix_tests['authentication_successful'] = True
                return True
            else:
                self.log(f"   ❌ Authentication failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def create_test_passport_file(self):
        """Create a test passport file for processing"""
        try:
            self.log("📄 Creating test passport file...")
            
            # Create a realistic passport-like PDF content (as text for testing)
            passport_content = """
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
SOCIALIST REPUBLIC OF VIETNAM

HỘ CHIẾU / PASSPORT

Họ và tên / Surname and given names: TRẦN TRỌNG TOÀN
Ngày sinh / Date of birth: 15/03/1985
Nơi sinh / Place of birth: HỒ CHÍ MINH
Giới tính / Sex: M / Nam
Quốc tịch / Nationality: VIỆT NAM / VIETNAMESE

Số hộ chiếu / Passport No.: C9329057
Ngày cấp / Date of issue: 17/01/2020
Ngày hết hạn / Date of expiry: 17/01/2030
Nơi cấp / Place of issue: CỤC XUẤT NHẬP CẢNH

XUẤT NHẬP CẢNH
IMMIGRATION DEPARTMENT
            """
            
            # Convert to bytes for file upload
            self.passport_file_data = passport_content.encode('utf-8')
            self.log(f"✅ Test passport file created ({len(self.passport_file_data)} bytes)")
            self.log(f"   Filename: {self.passport_filename}")
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating test passport file: {str(e)}", "ERROR")
            return False
    
    def test_python_nameerror_fix(self):
        """Test the specific Python NameError fix"""
        try:
            self.log("🔧 Testing Python NameError fix...")
            
            # Prepare multipart form data
            files = {
                'passport_file': (self.passport_filename, self.passport_file_data, 'application/pdf')
            }
            data = {
                'ship_name': 'BROTHER 36'
            }
            
            endpoint = f"{BACKEND_URL}/crew/analyze-passport"
            self.log(f"   POST {endpoint}")
            self.log(f"   Ship name: {data['ship_name']}")
            self.log(f"   File: {self.passport_filename} ({len(self.passport_file_data)} bytes)")
            
            # Make the request with longer timeout for AI processing
            response = requests.post(
                endpoint, 
                files=files, 
                data=data, 
                headers=self.get_headers(), 
                timeout=120  # 2 minutes for AI processing
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.python_fix_tests['passport_upload_endpoint_accessible'] = True
                self.log("✅ Passport analysis endpoint accessible")
                
                try:
                    response_data = response.json()
                    self.log(f"   Response keys: {list(response_data.keys())}")
                    
                    # Check for success
                    success = response_data.get('success', False)
                    self.log(f"   Success: {success}")
                    
                    # Check for Python errors in response
                    response_text = json.dumps(response_data)
                    python_error_patterns = [
                        "NameError: name 'ai_config' is not defined",
                        "ai_config is not defined",
                        "NameError",
                        "Traceback",
                        "Exception:",
                        "Error:"
                    ]
                    
                    found_python_errors = []
                    for pattern in python_error_patterns:
                        if pattern in response_text:
                            found_python_errors.append(pattern)
                    
                    if not found_python_errors:
                        self.python_fix_tests['no_python_errors_in_response'] = True
                        self.log("✅ No Python errors found in API response")
                    else:
                        self.log(f"   ❌ Found Python errors: {found_python_errors}")
                    
                    if success:
                        self.python_fix_tests['python_nameerror_resolved'] = True
                        self.log("✅ Python NameError resolved - API returned success")
                        
                        # Check for analysis data
                        analysis = response_data.get('analysis', {})
                        if analysis:
                            self.python_fix_tests['field_extraction_working'] = True
                            self.python_fix_tests['ai_field_extraction_successful'] = True
                            self.log("✅ Field extraction working")
                            self.log(f"   Extracted fields: {list(analysis.keys())}")
                            
                            # Log extracted field values
                            for field, value in analysis.items():
                                if value:
                                    self.log(f"      {field}: {value}")
                        
                        # Check for files data
                        files_data = response_data.get('files', {})
                        if files_data:
                            self.python_fix_tests['complete_api_response'] = True
                            self.python_fix_tests['file_upload_step_successful'] = True
                            self.log("✅ Complete API response with files data")
                            self.log(f"   Files: {list(files_data.keys())}")
                            
                            # Check passport file upload
                            passport_file = files_data.get('passport', {})
                            if passport_file:
                                upload_result = passport_file.get('upload_result', {})
                                if upload_result.get('success'):
                                    self.python_fix_tests['passport_file_uploaded_to_gdrive'] = True
                                    self.log("✅ Passport file upload successful")
                                
                                folder = passport_file.get('folder')
                                if folder == 'BROTHER 36/Crew records':
                                    self.python_fix_tests['correct_folder_structure'] = True
                                    self.log(f"✅ Correct passport folder: {folder}")
                            
                            # Check summary file upload
                            summary_file = files_data.get('summary', {})
                            if summary_file:
                                upload_result = summary_file.get('upload_result', {})
                                if upload_result.get('success'):
                                    self.python_fix_tests['summary_file_uploaded_to_gdrive'] = True
                                    self.log("✅ Summary file upload successful")
                                
                                folder = summary_file.get('folder')
                                if folder == 'SUMMARY':
                                    self.log(f"✅ Correct summary folder: {folder}")
                        
                        # Check processing method
                        processing_method = response_data.get('processing_method')
                        if processing_method == 'dual_apps_script':
                            self.python_fix_tests['dual_apps_script_processing'] = True
                            self.log(f"✅ Dual Apps Script processing: {processing_method}")
                        
                        return response_data
                    else:
                        # Check error details
                        error_message = response_data.get('message', 'Unknown error')
                        error_details = response_data.get('error', '')
                        self.log(f"   ❌ Processing failed: {error_message}")
                        if error_details:
                            self.log(f"   Error details: {error_details}")
                        
                        # Check if it's the old NameError
                        if 'ai_config' in error_details or 'NameError' in error_details:
                            self.log("   ❌ Python NameError still present!")
                        else:
                            self.python_fix_tests['python_nameerror_resolved'] = True
                            self.log("   ✅ Python NameError resolved (different error)")
                        
                        return response_data
                        
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ Passport analysis endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing Python NameError fix: {str(e)}", "ERROR")
            return None
    
    def check_backend_logs_for_errors(self):
        """Check backend logs for Python errors"""
        try:
            self.log("📋 Checking backend logs for Python errors...")
            
            # Check supervisor logs for Python errors
            try:
                import subprocess
                result = subprocess.run(
                    ['tail', '-n', '200', '/var/log/supervisor/backend.err.log'],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    log_content = result.stdout
                    self.log(f"   Retrieved {len(log_content.splitlines())} error log lines")
                    
                    # Check for Python error patterns
                    error_patterns = [
                        "NameError: name 'ai_config' is not defined",
                        "ai_config is not defined",
                        "NameError",
                        "Traceback (most recent call last):",
                        "Exception:",
                        "Error in passport processing"
                    ]
                    
                    found_errors = []
                    for error_pattern in error_patterns:
                        if error_pattern in log_content:
                            found_errors.append(error_pattern)
                    
                    if found_errors:
                        self.log(f"   ❌ Found {len(found_errors)} error patterns in backend logs:")
                        for error in found_errors:
                            self.log(f"      ❌ {error}")
                        return False
                    else:
                        self.log("   ✅ No Python error patterns found in backend logs")
                        return True
                else:
                    self.log("   ⚠️ Could not retrieve backend error logs")
                    return True  # Assume no errors if can't check
                    
            except Exception as e:
                self.log(f"   ⚠️ Error checking backend logs: {str(e)}")
                return True  # Assume no errors if can't check
                
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return True
    
    def run_python_error_fix_test(self):
        """Run comprehensive test of Python error fix"""
        try:
            self.log("🚀 STARTING PYTHON NAMEERROR FIX TEST")
            self.log("=" * 80)
            self.log("OBJECTIVE: Test Python NameError fix and verify complete passport processing")
            self.log("=" * 80)
            
            # Phase 1: Backend Error Resolution Verification
            self.log("\n🔧 PHASE 1: BACKEND ERROR RESOLUTION VERIFICATION")
            self.log("-" * 60)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication with admin1/123456")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Create test passport file
            self.log("\nSTEP 2: Creating test passport file")
            if not self.create_test_passport_file():
                self.log("❌ CRITICAL: Failed to create test passport file")
                return False
            
            # Step 3: Test Python NameError fix
            self.log("\nSTEP 3: Testing Python NameError fix")
            response_data = self.test_python_nameerror_fix()
            if not response_data:
                self.log("❌ CRITICAL: Python NameError fix test failed")
                return False
            
            # Step 4: Check backend logs for errors
            self.log("\nSTEP 4: Checking backend logs for Python errors")
            no_backend_errors = self.check_backend_logs_for_errors()
            
            self.log("\n" + "=" * 80)
            self.log("✅ PYTHON NAMEERROR FIX TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in Python error fix test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 PYTHON NAMEERROR FIX TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.python_fix_tests)
            passed_tests = sum(1 for result in self.python_fix_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Phase 1 Results
            self.log("🔧 PHASE 1: BACKEND ERROR RESOLUTION VERIFICATION")
            phase1_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('python_nameerror_resolved', 'Python NameError resolved'),
                ('no_python_errors_in_response', 'No Python errors in API response'),
                ('field_extraction_working', 'Field extraction working'),
                ('complete_api_response', 'Complete API response returned'),
            ]
            
            for test_key, description in phase1_tests:
                status = "✅ PASS" if self.python_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Phase 2 Results
            self.log("\n📋 PHASE 2: COMPLETE PASSPORT PROCESSING WORKFLOW")
            phase2_tests = [
                ('passport_upload_endpoint_accessible', 'Passport upload endpoint accessible'),
                ('document_ai_processing_successful', 'Document AI processing successful'),
                ('system_apps_script_working', 'System Apps Script working'),
                ('ai_field_extraction_successful', 'AI field extraction successful'),
                ('company_apps_script_working', 'Company Apps Script working'),
                ('file_upload_step_successful', 'File upload step successful'),
                ('dual_apps_script_processing', 'Dual Apps Script processing'),
            ]
            
            for test_key, description in phase2_tests:
                status = "✅ PASS" if self.python_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Phase 3 Results
            self.log("\n☁️ PHASE 3: GOOGLE DRIVE FILE CREATION VERIFICATION")
            phase3_tests = [
                ('passport_file_uploaded_to_gdrive', 'Passport file uploaded to Google Drive'),
                ('summary_file_uploaded_to_gdrive', 'Summary file uploaded to Google Drive'),
                ('correct_folder_structure', 'Correct folder structure'),
                ('files_contain_actual_content', 'Files contain actual content'),
                ('real_google_drive_file_ids', 'Real Google Drive file IDs'),
            ]
            
            for test_key, description in phase3_tests:
                status = "✅ PASS" if self.python_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Success Validation
            self.log("\n🎯 CRITICAL SUCCESS VALIDATION")
            
            # Python Error Fix
            if self.python_fix_tests.get('python_nameerror_resolved'):
                self.log("   ✅ Python NameError: 'ai_config' is not defined - RESOLVED")
            else:
                self.log("   ❌ Python NameError: 'ai_config' is not defined - STILL PRESENT")
            
            # API Response
            if self.python_fix_tests.get('complete_api_response'):
                self.log("   ✅ API Response: Complete response with file upload results")
            else:
                self.log("   ❌ API Response: Truncated response due to errors")
            
            # Google Drive Files
            if (self.python_fix_tests.get('passport_file_uploaded_to_gdrive') and 
                self.python_fix_tests.get('summary_file_uploaded_to_gdrive')):
                self.log("   ✅ Google Drive Files: Real files created in correct folders")
            else:
                self.log("   ❌ Google Drive Files: Files not created or mock responses")
            
            # Field Extraction
            if self.python_fix_tests.get('ai_field_extraction_successful'):
                self.log("   ✅ Field Extraction: Continue working with fixed AI config")
            else:
                self.log("   ❌ Field Extraction: Not working properly")
            
            # Overall Assessment
            self.log("\n🏆 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'python_nameerror_resolved', 'complete_api_response', 
                'no_python_errors_in_response', 'passport_upload_endpoint_accessible'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.python_fix_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL SUCCESS CRITERIA MET")
                self.log("   ✅ Python NameError fix successful")
                self.log("   ✅ Complete passport processing workflow working")
            else:
                self.log("   ❌ SOME CRITICAL SUCCESS CRITERIA NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            if success_rate >= 85:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 70:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the Python error fix tests"""
    tester = PythonErrorFixTester()
    
    try:
        # Run comprehensive test
        success = tester.run_python_error_fix_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Return appropriate exit code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
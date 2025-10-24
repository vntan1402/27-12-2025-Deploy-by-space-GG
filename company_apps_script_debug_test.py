#!/usr/bin/env python3
"""
Company Apps Script File Upload Debug Testing
FOCUS: Debug why files are not appearing in Google Drive despite Company Apps Script URL being configured

REVIEW REQUEST REQUIREMENTS:
DEBUG COMPANY APPS SCRIPT FILE UPLOAD - INVESTIGATE MISSING FILES IN GOOGLE DRIVE:

**OBJECTIVE**: Debug why files are not appearing in Google Drive despite Company Apps Script URL being configured. 
User confirms no files in BROTHER 36/Crew records folder and no SUMMARY folder created.

**ISSUE IDENTIFIED**:
- Company Apps Script URL configured: https://script.google.com/macros/s/AKfycbzzpvHsThfQPjlz7kgr6Uontm-b0y-4AyishYmxPDIB72yxbBK29Zbv9oGiV3BHte2u/exec
- Backend reports success, but Google Drive shows no files
- BROTHER 36/Crew Records folder empty
- No SUMMARY folder created in Company Drive root

**COMPREHENSIVE DEBUGGING REQUIREMENTS**:

### **Phase 1: Company Apps Script URL Testing**
1. **Direct URL Test**: Test Company Apps Script URL directly to verify it's working
2. **Response Verification**: Check if Apps Script returns valid response
3. **Service Availability**: Verify the Apps Script service is deployed and accessible

### **Phase 2: Company Apps Script Code Verification**
4. **Code Analysis**: The Company Apps Script may not have the correct upload code
5. **File Upload Function**: Verify it has real file upload functionality (not just mock responses)
6. **Google Drive Integration**: Check if it actually creates files in Google Drive

### **Phase 3: Backend Integration Debug**
7. **Passport Analysis Test**: Run passport analysis with detailed logging
8. **Company Apps Script Calls**: Monitor actual requests sent to Company Apps Script
9. **Response Analysis**: Analyze Company Apps Script responses vs expected behavior
10. **Error Detection**: Look for hidden errors in file upload process

### **Phase 4: Real File Upload Verification**
11. **Manual Upload Test**: Test Company Apps Script with manual file upload request
12. **Folder Creation**: Verify Apps Script can create folders in Google Drive
13. **Permission Check**: Verify Apps Script has proper Google Drive permissions
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
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://marine-doc-system.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class CompanyAppsScriptDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Company Apps Script URL from review request
        self.company_apps_script_url = "https://script.google.com/macros/s/AKfycbzzpvHsThfQPjlz7kgr6Uontm-b0y-4AyishYmxPDIB72yxbBK29Zbv9oGiV3BHte2u/exec"
        
        # Test tracking for Company Apps Script debugging
        self.debug_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            
            # Phase 1: Company Apps Script URL Testing
            'company_apps_script_url_accessible': False,
            'company_apps_script_returns_valid_response': False,
            'company_apps_script_service_deployed': False,
            
            # Phase 2: Company Apps Script Code Verification
            'company_apps_script_has_upload_code': False,
            'company_apps_script_real_upload_functionality': False,
            'company_apps_script_google_drive_integration': False,
            
            # Phase 3: Backend Integration Debug
            'passport_analysis_endpoint_working': False,
            'company_apps_script_calls_monitored': False,
            'company_apps_script_response_analysis': False,
            'hidden_errors_detected': False,
            
            # Phase 4: Real File Upload Verification
            'manual_upload_test_successful': False,
            'folder_creation_verified': False,
            'google_drive_permissions_verified': False,
            
            # Critical Issues Detection
            'company_apps_script_mock_responses_only': False,
            'company_apps_script_missing_permissions': False,
            'backend_integration_issues': False,
            'folder_path_mismatch': False,
        }
        
        # Store test data
        self.user_company = None
        
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
                
                self.debug_tests['authentication_successful'] = True
                self.user_company = self.current_user.get('company')
                if self.user_company:
                    self.debug_tests['user_company_identified'] = True
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
    
    def test_company_apps_script_direct_access(self):
        """Phase 1: Test Company Apps Script URL directly"""
        try:
            self.log("🌐 PHASE 1: Testing Company Apps Script URL directly...")
            self.log(f"   URL: {self.company_apps_script_url}")
            
            # Test 1: Basic GET request to check if service is accessible
            self.log("   Test 1: Basic GET request to check accessibility...")
            try:
                response = requests.get(self.company_apps_script_url, timeout=30)
                self.log(f"   Response status: {response.status_code}")
                self.log(f"   Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    self.debug_tests['company_apps_script_url_accessible'] = True
                    self.log("   ✅ Company Apps Script URL is accessible")
                    
                    # Check response content
                    response_text = response.text[:500]  # First 500 chars
                    self.log(f"   Response content (first 500 chars): {response_text}")
                    
                    if response_text and len(response_text) > 0:
                        self.debug_tests['company_apps_script_returns_valid_response'] = True
                        self.log("   ✅ Company Apps Script returns valid response")
                        
                        # Check if it looks like a deployed service
                        if "script" in response_text.lower() or "function" in response_text.lower() or "maritime" in response_text.lower():
                            self.debug_tests['company_apps_script_service_deployed'] = True
                            self.log("   ✅ Company Apps Script appears to be properly deployed")
                        else:
                            self.log("   ⚠️ Response doesn't look like a deployed Apps Script service")
                    else:
                        self.log("   ❌ Empty response from Company Apps Script")
                else:
                    self.log(f"   ❌ Company Apps Script URL not accessible - Status: {response.status_code}")
                    self.log(f"   Response: {response.text[:200]}")
                    
            except requests.exceptions.Timeout:
                self.log("   ❌ Company Apps Script URL request timed out")
            except requests.exceptions.RequestException as e:
                self.log(f"   ❌ Company Apps Script URL request failed: {str(e)}")
            
            # Test 2: POST request with test payload to check functionality
            self.log("   Test 2: POST request with test payload...")
            try:
                test_payload = {
                    "action": "test_connection",
                    "timestamp": datetime.now().isoformat()
                }
                
                response = requests.post(
                    self.company_apps_script_url, 
                    json=test_payload, 
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                self.log(f"   POST Response status: {response.status_code}")
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        self.log(f"   POST Response data: {response_data}")
                        
                        if response_data.get('success') or 'error' in response_data:
                            self.log("   ✅ Company Apps Script responds to POST requests")
                        else:
                            self.log("   ⚠️ Unexpected POST response format")
                    except json.JSONDecodeError:
                        self.log(f"   POST Response text: {response.text[:200]}")
                else:
                    self.log(f"   ❌ POST request failed - Status: {response.status_code}")
                    
            except Exception as e:
                self.log(f"   ❌ POST request error: {str(e)}")
                
        except Exception as e:
            self.log(f"❌ Error in Phase 1 testing: {str(e)}", "ERROR")
    
    def test_company_apps_script_file_upload_functionality(self):
        """Phase 2: Test Company Apps Script file upload functionality"""
        try:
            self.log("📁 PHASE 2: Testing Company Apps Script file upload functionality...")
            
            # Test 3: Manual file upload test with base64 encoded file
            self.log("   Test 3: Manual file upload test...")
            
            # Create a test file content
            test_file_content = "This is a test file for Company Apps Script debugging.\nTimestamp: " + datetime.now().isoformat()
            test_file_base64 = base64.b64encode(test_file_content.encode()).decode()
            
            # Test payload similar to what backend would send
            upload_payload = {
                "action": "upload_file",
                "file_content": test_file_base64,
                "filename": "debug_test_file.txt",
                "folder_path": "BROTHER 36/Crew records",
                "category": "passport",
                "timestamp": datetime.now().isoformat()
            }
            
            self.log(f"   Sending upload payload: {json.dumps({k: v if k != 'file_content' else f'{v[:50]}...' for k, v in upload_payload.items()}, indent=2)}")
            
            try:
                response = requests.post(
                    self.company_apps_script_url,
                    json=upload_payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=60  # Longer timeout for file upload
                )
                
                self.log(f"   Upload response status: {response.status_code}")
                self.log(f"   Upload response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        self.log(f"   Upload response data: {json.dumps(response_data, indent=2)}")
                        
                        # Check for success indicators
                        if response_data.get('success') == True:
                            self.debug_tests['company_apps_script_real_upload_functionality'] = True
                            self.log("   ✅ Company Apps Script has real file upload functionality")
                            
                            # Check for Google Drive file ID
                            if response_data.get('file_id') and 'mock' not in str(response_data.get('file_id')).lower():
                                self.debug_tests['company_apps_script_google_drive_integration'] = True
                                self.log(f"   ✅ Real Google Drive file ID returned: {response_data.get('file_id')}")
                            else:
                                self.debug_tests['company_apps_script_mock_responses_only'] = True
                                self.log(f"   ❌ Mock or invalid file ID returned: {response_data.get('file_id')}")
                                
                        elif 'permission' in str(response_data).lower() or 'auth' in str(response_data).lower():
                            self.debug_tests['company_apps_script_missing_permissions'] = True
                            self.log("   ❌ Company Apps Script has permission issues")
                            self.log(f"   Permission error details: {response_data}")
                            
                        else:
                            self.log(f"   ❌ Upload failed - Response: {response_data}")
                            
                    except json.JSONDecodeError:
                        self.log(f"   Upload response text: {response.text}")
                        if 'success' in response.text.lower():
                            self.log("   ⚠️ Upload may have succeeded but response is not JSON")
                        
                else:
                    self.log(f"   ❌ Upload request failed - Status: {response.status_code}")
                    self.log(f"   Error response: {response.text[:300]}")
                    
            except requests.exceptions.Timeout:
                self.log("   ❌ Upload request timed out - Apps Script may be processing but slow")
            except Exception as e:
                self.log(f"   ❌ Upload request error: {str(e)}")
            
            # Test 4: Test SUMMARY folder creation
            self.log("   Test 4: Testing SUMMARY folder creation...")
            
            summary_payload = {
                "action": "upload_file",
                "file_content": base64.b64encode("Test summary content".encode()).decode(),
                "filename": "debug_test_summary.txt",
                "folder_path": "SUMMARY",
                "category": "summary",
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                response = requests.post(
                    self.company_apps_script_url,
                    json=summary_payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=60
                )
                
                self.log(f"   SUMMARY upload response status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        self.log(f"   SUMMARY response: {json.dumps(response_data, indent=2)}")
                        
                        if response_data.get('success') == True:
                            self.debug_tests['folder_creation_verified'] = True
                            self.log("   ✅ SUMMARY folder creation working")
                        else:
                            self.log("   ❌ SUMMARY folder creation failed")
                            
                    except json.JSONDecodeError:
                        self.log(f"   SUMMARY response text: {response.text}")
                        
            except Exception as e:
                self.log(f"   ❌ SUMMARY upload error: {str(e)}")
                
        except Exception as e:
            self.log(f"❌ Error in Phase 2 testing: {str(e)}", "ERROR")
    
    def test_backend_passport_analysis_integration(self):
        """Phase 3: Test backend passport analysis with Company Apps Script integration"""
        try:
            self.log("🔍 PHASE 3: Testing backend passport analysis integration...")
            
            # Test 5: Run passport analysis and monitor Company Apps Script calls
            self.log("   Test 5: Running passport analysis with detailed monitoring...")
            
            # Create a test passport file
            test_passport_content = """
            PASSPORT
            CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
            SOCIALIST REPUBLIC OF VIETNAM
            
            Họ và tên / Surname and given names: NGUYEN VAN TEST
            Số hộ chiếu / Passport No.: C1234567
            Ngày sinh / Date of birth: 15/05/1990
            Nơi sinh / Place of birth: HO CHI MINH
            Giới tính / Sex: M
            Quốc tịch / Nationality: VIETNAMESE
            Ngày cấp / Date of issue: 01/01/2020
            Ngày hết hạn / Date of expiry: 01/01/2030
            """
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(test_passport_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload passport for analysis
                endpoint = f"{BACKEND_URL}/crew/analyze-passport"
                self.log(f"   POST {endpoint}")
                
                with open(temp_file_path, 'rb') as file:
                    files = {
                        'passport_file': ('test_passport.txt', file, 'text/plain')
                    }
                    data = {
                        'ship_name': 'BROTHER 36'
                    }
                    
                    self.log("   Uploading passport file for analysis...")
                    response = requests.post(
                        endpoint, 
                        files=files, 
                        data=data, 
                        headers=self.get_headers(), 
                        timeout=120  # Long timeout for AI processing
                    )
                
                self.log(f"   Analysis response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.debug_tests['passport_analysis_endpoint_working'] = True
                    self.log("   ✅ Passport analysis endpoint working")
                    
                    try:
                        response_data = response.json()
                        self.log(f"   Analysis response: {json.dumps(response_data, indent=2)}")
                        
                        # Check if Company Apps Script was called
                        if response_data.get('success') == True:
                            self.debug_tests['company_apps_script_calls_monitored'] = True
                            self.log("   ✅ Backend reports successful processing")
                            
                            # Check for file upload indicators
                            if 'files' in response_data or 'file_id' in response_data:
                                self.log("   ✅ File upload indicators present in response")
                            else:
                                self.log("   ⚠️ No file upload indicators in response")
                                
                            # Check for analysis data
                            if 'analysis' in response_data or 'extracted_data' in response_data:
                                self.log("   ✅ Analysis data present in response")
                            else:
                                self.log("   ⚠️ No analysis data in response")
                                
                        elif response_data.get('success') == False:
                            self.debug_tests['backend_integration_issues'] = True
                            error_msg = response_data.get('error', 'Unknown error')
                            self.log(f"   ❌ Backend reports failure: {error_msg}")
                            
                            # Check for specific Company Apps Script errors
                            if 'company apps script' in error_msg.lower():
                                self.log("   ❌ Company Apps Script specific error detected")
                            if 'not configured' in error_msg.lower():
                                self.log("   ❌ Configuration issue detected")
                            if 'permission' in error_msg.lower():
                                self.debug_tests['company_apps_script_missing_permissions'] = True
                                self.log("   ❌ Permission issue detected")
                                
                        else:
                            self.log("   ⚠️ Unexpected response format")
                            
                    except json.JSONDecodeError:
                        self.log(f"   Analysis response text: {response.text[:500]}")
                        
                else:
                    self.log(f"   ❌ Passport analysis failed - Status: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data}")
                    except:
                        self.log(f"   Error text: {response.text[:300]}")
                        
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Error in Phase 3 testing: {str(e)}", "ERROR")
    
    def test_backend_logs_analysis(self):
        """Phase 4: Analyze backend logs for hidden errors"""
        try:
            self.log("📋 PHASE 4: Analyzing backend logs for hidden errors...")
            
            # Test 6: Check backend logs for Company Apps Script related errors
            self.log("   Test 6: Checking backend logs...")
            
            # Try to get backend logs (if available via API)
            try:
                # This might not be available, but worth trying
                logs_endpoint = f"{BACKEND_URL}/logs"
                response = requests.get(logs_endpoint, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 200:
                    logs_data = response.json()
                    self.log(f"   ✅ Backend logs retrieved: {len(logs_data)} entries")
                    
                    # Search for Company Apps Script related errors
                    company_script_errors = []
                    for log_entry in logs_data[-50:]:  # Last 50 entries
                        log_message = str(log_entry.get('message', '')).lower()
                        if 'company apps script' in log_message or 'file upload' in log_message:
                            company_script_errors.append(log_entry)
                    
                    if company_script_errors:
                        self.debug_tests['hidden_errors_detected'] = True
                        self.log(f"   ❌ Found {len(company_script_errors)} Company Apps Script related log entries:")
                        for error in company_script_errors[-5:]:  # Show last 5
                            self.log(f"      {error.get('timestamp', 'N/A')}: {error.get('message', 'N/A')}")
                    else:
                        self.log("   ✅ No Company Apps Script errors found in recent logs")
                        
                else:
                    self.log(f"   ⚠️ Backend logs not accessible - Status: {response.status_code}")
                    
            except Exception as e:
                self.log(f"   ⚠️ Could not retrieve backend logs: {str(e)}")
            
            # Test 7: Check supervisor logs for backend errors
            self.log("   Test 7: Checking supervisor backend logs...")
            try:
                import subprocess
                result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.err.log'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and result.stdout:
                    self.log("   ✅ Supervisor backend error logs retrieved")
                    log_lines = result.stdout.split('\n')
                    
                    # Search for Company Apps Script related errors
                    relevant_lines = []
                    for line in log_lines:
                        if ('company apps script' in line.lower() or 
                            'file upload' in line.lower() or 
                            'google drive' in line.lower() or
                            'error' in line.lower()):
                            relevant_lines.append(line)
                    
                    if relevant_lines:
                        self.debug_tests['hidden_errors_detected'] = True
                        self.log(f"   ❌ Found {len(relevant_lines)} relevant error log lines:")
                        for line in relevant_lines[-5:]:  # Show last 5
                            self.log(f"      {line.strip()}")
                    else:
                        self.log("   ✅ No relevant errors found in supervisor logs")
                        
                else:
                    self.log("   ⚠️ Could not read supervisor backend logs")
                    
            except Exception as e:
                self.log(f"   ⚠️ Error reading supervisor logs: {str(e)}")
                
        except Exception as e:
            self.log(f"❌ Error in Phase 4 testing: {str(e)}", "ERROR")
    
    def run_comprehensive_company_apps_script_debug(self):
        """Run comprehensive Company Apps Script debugging"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE COMPANY APPS SCRIPT DEBUG TESTING")
            self.log("=" * 80)
            self.log(f"Target Company Apps Script URL: {self.company_apps_script_url}")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Phase 1 - Direct Company Apps Script URL Testing
            self.log("\nSTEP 2: PHASE 1 - Company Apps Script URL Testing")
            self.test_company_apps_script_direct_access()
            
            # Step 3: Phase 2 - Company Apps Script File Upload Functionality
            self.log("\nSTEP 3: PHASE 2 - Company Apps Script File Upload Functionality")
            self.test_company_apps_script_file_upload_functionality()
            
            # Step 4: Phase 3 - Backend Integration Debug
            self.log("\nSTEP 4: PHASE 3 - Backend Integration Debug")
            self.test_backend_passport_analysis_integration()
            
            # Step 5: Phase 4 - Backend Logs Analysis
            self.log("\nSTEP 5: PHASE 4 - Backend Logs Analysis")
            self.test_backend_logs_analysis()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE COMPANY APPS SCRIPT DEBUG COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive debug: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_debug_summary(self):
        """Print comprehensive summary of debug results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 COMPANY APPS SCRIPT DEBUG SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.debug_tests)
            passed_tests = sum(1 for result in self.debug_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Debug Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Phase 1 Results
            self.log("\n🌐 PHASE 1 - COMPANY APPS SCRIPT URL TESTING:")
            phase1_tests = [
                ('company_apps_script_url_accessible', 'Company Apps Script URL accessible'),
                ('company_apps_script_returns_valid_response', 'Returns valid response'),
                ('company_apps_script_service_deployed', 'Service properly deployed'),
            ]
            
            for test_key, description in phase1_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Phase 2 Results
            self.log("\n📁 PHASE 2 - FILE UPLOAD FUNCTIONALITY:")
            phase2_tests = [
                ('company_apps_script_real_upload_functionality', 'Real file upload functionality'),
                ('company_apps_script_google_drive_integration', 'Google Drive integration working'),
                ('folder_creation_verified', 'Folder creation verified'),
            ]
            
            for test_key, description in phase2_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Phase 3 Results
            self.log("\n🔍 PHASE 3 - BACKEND INTEGRATION:")
            phase3_tests = [
                ('passport_analysis_endpoint_working', 'Passport analysis endpoint working'),
                ('company_apps_script_calls_monitored', 'Company Apps Script calls monitored'),
            ]
            
            for test_key, description in phase3_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Issues Detection
            self.log("\n🚨 CRITICAL ISSUES DETECTED:")
            critical_issues = [
                ('company_apps_script_mock_responses_only', 'Company Apps Script returns mock responses only'),
                ('company_apps_script_missing_permissions', 'Company Apps Script missing Google Drive permissions'),
                ('backend_integration_issues', 'Backend integration issues'),
                ('hidden_errors_detected', 'Hidden errors detected in logs'),
            ]
            
            issues_found = False
            for test_key, description in critical_issues:
                if self.debug_tests.get(test_key, False):
                    issues_found = True
                    self.log(f"   ❌ ISSUE - {description}")
            
            if not issues_found:
                self.log("   ✅ No critical issues detected")
            
            # Root Cause Analysis
            self.log("\n🔍 ROOT CAUSE ANALYSIS:")
            
            if not self.debug_tests.get('company_apps_script_url_accessible', False):
                self.log("   ❌ CRITICAL: Company Apps Script URL is not accessible")
                self.log("      → Check if URL is correct and service is deployed")
                
            elif self.debug_tests.get('company_apps_script_mock_responses_only', False):
                self.log("   ❌ CRITICAL: Company Apps Script returns mock responses only")
                self.log("      → Apps Script code needs real Google Drive upload implementation")
                
            elif self.debug_tests.get('company_apps_script_missing_permissions', False):
                self.log("   ❌ CRITICAL: Company Apps Script missing Google Drive permissions")
                self.log("      → Update Apps Script OAuth scopes to include full Google Drive access")
                
            elif self.debug_tests.get('backend_integration_issues', False):
                self.log("   ❌ CRITICAL: Backend integration issues")
                self.log("      → Check backend configuration and Company Apps Script URL setup")
                
            elif success_rate < 50:
                self.log("   ❌ CRITICAL: Multiple issues detected")
                self.log("      → Comprehensive review of Company Apps Script and backend integration needed")
                
            else:
                self.log("   ✅ No obvious root cause identified - may be a visibility issue")
                self.log("      → Files may be uploaded but not visible in expected Google Drive location")
            
            # Recommendations
            self.log("\n💡 RECOMMENDATIONS:")
            
            if not self.debug_tests.get('company_apps_script_url_accessible', False):
                self.log("   1. Verify Company Apps Script URL is correct and deployed")
                self.log("   2. Check Apps Script project permissions and sharing settings")
                
            if self.debug_tests.get('company_apps_script_mock_responses_only', False):
                self.log("   1. Update Company Apps Script code to implement real Google Drive upload")
                self.log("   2. Remove mock responses and add actual DriveApp.createFile() calls")
                
            if self.debug_tests.get('company_apps_script_missing_permissions', False):
                self.log("   1. Update Apps Script OAuth scopes to include https://www.googleapis.com/auth/drive")
                self.log("   2. Re-authorize the Apps Script with full Google Drive permissions")
                
            if self.debug_tests.get('backend_integration_issues', False):
                self.log("   1. Check backend Company Apps Script URL configuration")
                self.log("   2. Verify request payload format matches Apps Script expectations")
                
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing debug summary: {str(e)}", "ERROR")

def main():
    """Main function to run the Company Apps Script debug tests"""
    tester = CompanyAppsScriptDebugTester()
    
    try:
        # Run comprehensive debug
        success = tester.run_comprehensive_company_apps_script_debug()
        
        # Print summary
        tester.print_debug_summary()
        
        # Return appropriate exit code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n❌ Debug interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
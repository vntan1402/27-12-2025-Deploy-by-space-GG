#!/usr/bin/env python3
"""
Ship Management System - Final Passport Processing Workflow Test
FOCUS: Test Python NameError fix and complete passport processing workflow with real PDF

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

class FinalPassportWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        
        # Test tracking for final passport workflow
        self.workflow_tests = {
            # Critical Success Criteria
            'authentication_successful': False,
            'python_nameerror_resolved': False,
            'passport_endpoint_accessible': False,
            'api_returns_success_true': False,
            'complete_api_response_with_files': False,
            'document_ai_processing_working': False,
            'field_extraction_successful': False,
            'file_upload_step_working': False,
            'dual_apps_script_working': False,
            'passport_file_uploaded': False,
            'summary_file_uploaded': False,
            'correct_folder_structure': False,
            'no_python_errors_in_logs': False,
        }
        
        # Store passport file data
        self.passport_file_path = "/app/PASS_PORT_Tran_Trong_Toan.pdf"
        self.passport_filename = "PASS PORT Tran Trong Toan.pdf"
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
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
            response = requests.post(endpoint, json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User: {self.current_user.get('username')} ({self.current_user.get('role')})")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.workflow_tests['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed - Status: {response.status_code}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_complete_passport_workflow(self):
        """Test the complete passport processing workflow with real PDF"""
        try:
            self.log("🔍 Testing complete passport processing workflow...")
            
            # Check if passport file exists
            if not os.path.exists(self.passport_file_path):
                self.log(f"❌ Passport file not found: {self.passport_file_path}")
                return None
            
            file_size = os.path.getsize(self.passport_file_path)
            self.log(f"📄 Using real passport file: {self.passport_filename} ({file_size} bytes)")
            
            # Read the passport file
            with open(self.passport_file_path, 'rb') as f:
                passport_file_data = f.read()
            
            # Prepare multipart form data
            files = {
                'passport_file': (self.passport_filename, passport_file_data, 'application/pdf')
            }
            data = {
                'ship_name': 'BROTHER 36'
            }
            
            endpoint = f"{BACKEND_URL}/crew/analyze-passport"
            self.log(f"   POST {endpoint}")
            self.log(f"   Ship name: {data['ship_name']}")
            
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
                self.workflow_tests['passport_endpoint_accessible'] = True
                self.log("✅ Passport analysis endpoint accessible")
                
                try:
                    response_data = response.json()
                    
                    # Check for Python errors in response
                    response_text = json.dumps(response_data)
                    python_error_patterns = [
                        "NameError: name 'ai_config' is not defined",
                        "ai_config is not defined",
                        "NameError",
                        "Traceback",
                        "Exception in passport processing"
                    ]
                    
                    found_python_errors = []
                    for pattern in python_error_patterns:
                        if pattern in response_text:
                            found_python_errors.append(pattern)
                    
                    if not found_python_errors:
                        self.workflow_tests['python_nameerror_resolved'] = True
                        self.log("✅ Python NameError resolved - no Python errors in response")
                    else:
                        self.log(f"❌ Found Python errors: {found_python_errors}")
                    
                    # Check for success
                    success = response_data.get('success', False)
                    self.log(f"   API Success: {success}")
                    
                    if success:
                        self.workflow_tests['api_returns_success_true'] = True
                        self.log("✅ API returns success: true")
                        
                        # Check for analysis data
                        analysis = response_data.get('analysis', {})
                        if analysis:
                            self.workflow_tests['field_extraction_successful'] = True
                            self.log("✅ Field extraction successful")
                            
                            # Log key extracted fields
                            key_fields = ['full_name', 'passport_number', 'date_of_birth', 'nationality']
                            for field in key_fields:
                                value = analysis.get(field, '')
                                if value:
                                    self.log(f"      {field}: {value}")
                        
                        # Check for files data
                        files_data = response_data.get('files', {})
                        if files_data:
                            self.workflow_tests['complete_api_response_with_files'] = True
                            self.log("✅ Complete API response with files data")
                            
                            # Check passport file upload
                            passport_file = files_data.get('passport', {})
                            if passport_file:
                                upload_result = passport_file.get('upload_result', {})
                                if upload_result.get('success'):
                                    self.workflow_tests['passport_file_uploaded'] = True
                                    self.log("✅ Passport file uploaded successfully")
                                
                                folder = passport_file.get('folder')
                                if folder == 'BROTHER 36/Crew records':
                                    self.workflow_tests['correct_folder_structure'] = True
                                    self.log(f"✅ Correct passport folder: {folder}")
                            
                            # Check summary file upload
                            summary_file = files_data.get('summary', {})
                            if summary_file:
                                upload_result = summary_file.get('upload_result', {})
                                if upload_result.get('success'):
                                    self.workflow_tests['summary_file_uploaded'] = True
                                    self.log("✅ Summary file uploaded successfully")
                        
                        # Check processing method
                        processing_method = response_data.get('processing_method')
                        if processing_method == 'dual_apps_script':
                            self.workflow_tests['dual_apps_script_working'] = True
                            self.log(f"✅ Dual Apps Script processing: {processing_method}")
                        
                        # Check workflow
                        workflow = response_data.get('workflow')
                        if workflow:
                            self.log(f"   Workflow: {workflow}")
                            if 'document_ai' in workflow and 'file_upload' in workflow:
                                self.workflow_tests['document_ai_processing_working'] = True
                                self.workflow_tests['file_upload_step_working'] = True
                        
                        return response_data
                    else:
                        # Check error details
                        error_message = response_data.get('message', 'Unknown error')
                        error_details = response_data.get('error', '')
                        self.log(f"   ❌ Processing failed: {error_message}")
                        if error_details:
                            self.log(f"   Error details: {error_details}")
                        
                        # Still check if Python NameError is resolved
                        if 'ai_config' not in error_details and 'NameError' not in error_details:
                            self.workflow_tests['python_nameerror_resolved'] = True
                            self.log("   ✅ Python NameError resolved (different error type)")
                        
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
            self.log(f"❌ Error testing passport workflow: {str(e)}", "ERROR")
            return None
    
    def check_backend_logs_for_success_patterns(self):
        """Check backend logs for expected success patterns"""
        try:
            self.log("📋 Checking backend logs for success patterns...")
            
            # Expected success patterns from the review request
            expected_patterns = [
                "System Apps Script URL loaded for Document AI",
                "Company Apps Script URL loaded for file upload",
                "Document AI completed successfully",
                "Field extraction completed successfully",
                "All file uploads completed successfully",
                "Dual Apps Script processing completed successfully"
            ]
            
            # Check supervisor logs
            try:
                import subprocess
                result = subprocess.run(
                    ['tail', '-n', '100', '/var/log/supervisor/backend.out.log'],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    log_content = result.stdout
                    
                    # Check for expected patterns
                    found_patterns = []
                    for pattern in expected_patterns:
                        if pattern in log_content:
                            found_patterns.append(pattern)
                    
                    self.log(f"   Found {len(found_patterns)}/{len(expected_patterns)} expected patterns")
                    
                    # Check for Python errors
                    error_patterns = [
                        "NameError: name 'ai_config' is not defined",
                        "ai_config is not defined",
                        "NameError",
                        "Traceback (most recent call last):"
                    ]
                    
                    found_errors = []
                    for error_pattern in error_patterns:
                        if error_pattern in log_content:
                            found_errors.append(error_pattern)
                    
                    if not found_errors:
                        self.workflow_tests['no_python_errors_in_logs'] = True
                        self.log("   ✅ No Python errors found in backend logs")
                    else:
                        self.log(f"   ❌ Found Python errors in logs: {found_errors}")
                    
                    return len(found_patterns), len(found_errors)
                else:
                    self.log("   ⚠️ Could not retrieve backend logs")
                    return 0, 0
                    
            except Exception as e:
                self.log(f"   ⚠️ Error checking backend logs: {str(e)}")
                return 0, 0
                
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return 0, 0
    
    def run_final_test(self):
        """Run the final comprehensive test"""
        try:
            self.log("🚀 STARTING FINAL PASSPORT PROCESSING WORKFLOW TEST")
            self.log("=" * 80)
            self.log("OBJECTIVE: Verify Python NameError fix and complete workflow")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Test complete passport workflow
            self.log("\nSTEP 2: Testing complete passport processing workflow")
            response_data = self.test_complete_passport_workflow()
            if not response_data:
                self.log("❌ CRITICAL: Passport workflow test failed")
                return False
            
            # Step 3: Check backend logs
            self.log("\nSTEP 3: Checking backend logs")
            found_patterns, found_errors = self.check_backend_logs_for_success_patterns()
            
            self.log("\n" + "=" * 80)
            self.log("✅ FINAL PASSPORT PROCESSING WORKFLOW TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in final test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_final_summary(self):
        """Print final comprehensive summary"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 FINAL PASSPORT PROCESSING WORKFLOW TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.workflow_tests)
            passed_tests = sum(1 for result in self.workflow_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Critical Success Criteria from Review Request
            self.log("🎯 CRITICAL SUCCESS CRITERIA FROM REVIEW REQUEST:")
            
            # Python Error Fix
            if self.workflow_tests.get('python_nameerror_resolved'):
                self.log("   ✅ Python Error Fix: NameError 'ai_config' is not defined - RESOLVED")
            else:
                self.log("   ❌ Python Error Fix: NameError 'ai_config' is not defined - STILL PRESENT")
            
            # API Response
            if self.workflow_tests.get('api_returns_success_true'):
                self.log("   ✅ API Response: Returns success: true (not truncated)")
            else:
                self.log("   ❌ API Response: Does not return success: true")
            
            # Complete Response
            if self.workflow_tests.get('complete_api_response_with_files'):
                self.log("   ✅ Complete Response: API returns full response including file data")
            else:
                self.log("   ❌ Complete Response: API response missing file data")
            
            # Field Extraction
            if self.workflow_tests.get('field_extraction_successful'):
                self.log("   ✅ Field Extraction: AI field extraction works with fixed parameters")
            else:
                self.log("   ❌ Field Extraction: AI field extraction not working")
            
            # File Upload
            if (self.workflow_tests.get('passport_file_uploaded') and 
                self.workflow_tests.get('summary_file_uploaded')):
                self.log("   ✅ Google Drive Files: Files actually created in Google Drive")
            else:
                self.log("   ❌ Google Drive Files: Files not created in Google Drive")
            
            # Folder Structure
            if self.workflow_tests.get('correct_folder_structure'):
                self.log("   ✅ Folder Structure: Correct folders (BROTHER 36/Crew records, SUMMARY)")
            else:
                self.log("   ❌ Folder Structure: Incorrect folder structure")
            
            # Backend Logs
            if self.workflow_tests.get('no_python_errors_in_logs'):
                self.log("   ✅ Backend Logs: No Python errors in backend logs")
            else:
                self.log("   ❌ Backend Logs: Python errors found in backend logs")
            
            # Expected Backend Log Pattern
            self.log("\n📋 EXPECTED BACKEND LOG PATTERN:")
            expected_log_pattern = """
✅ System Apps Script URL loaded for Document AI
✅ Company Apps Script URL loaded for file upload
🔄 Processing passport with dual Apps Scripts: PASS PORT Tran Trong Toan.pdf
📡 Step 1: Document AI analysis via System Apps Script...
✅ System Apps Script (Document AI) completed successfully
🧠 Extracting fields from Document AI summary using system AI...
✅ Field extraction completed successfully
📁 Step 2: File uploads via Company Apps Script...
📤 Uploading passport file: BROTHER 36/Crew records/PASS PORT Tran Trong Toan.pdf
📋 Uploading summary file: SUMMARY/PASS_PORT_Tran_Trong_Toan_Summary.txt
✅ All file uploads completed successfully
✅ Dual Apps Script processing completed successfully
            """
            self.log(expected_log_pattern.strip())
            
            # Overall Assessment
            self.log("\n🏆 OVERALL ASSESSMENT:")
            
            # Check critical tests
            critical_tests = [
                'python_nameerror_resolved', 'api_returns_success_true', 
                'complete_api_response_with_files', 'field_extraction_successful'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.workflow_tests.get(test_key, False))
            
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
            self.log(f"❌ Error printing final summary: {str(e)}", "ERROR")

def main():
    """Main function to run the final passport workflow test"""
    tester = FinalPassportWorkflowTester()
    
    try:
        # Run final test
        success = tester.run_final_test()
        
        # Print summary
        tester.print_final_summary()
        
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
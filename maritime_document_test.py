#!/usr/bin/env python3
"""
Maritime Document Analysis System Testing
FOCUS: Debug the maritime document analysis system

ISSUE DESCRIPTION:
- Backend API `/api/crew/analyze-maritime-document` returns 200 OK
- Apps Script receives requests and executes successfully 
- File uploads work (Maritime Document AI v2.0 service responds)
- BUT: Document AI analysis returns empty results (all passport fields are "")

TESTING FOCUS:
1. Backend to Apps Script communication
2. Apps Script to Document AI API calls
3. Document AI response parsing
4. Summary generation process
5. AI field extraction from summary

Apps Script URL: https://script.google.com/macros/s/AKfycbzRFYZFZgyrj7EQrQFYVReBx390nKmbPykT2jtSaGz4kMQWrcwoTSoOq5GR0Ds4Ajc/exec
Test file: /app/Ho_chieu_pho_thong.jpg
"""

import requests
import json
import os
import sys
import base64
import time
from datetime import datetime
import traceback
from pathlib import Path

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipmatrix.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

# Apps Script URL from review request
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzRFYZFZgyrj7EQrQFYVReBx390nKmbPykT2jtSaGz4kMQWrcwoTSoOq5GR0Ds4Ajc/exec"

class MaritimeDocumentTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for maritime document analysis
        self.maritime_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'test_file_exists': False,
            
            # Backend API testing
            'analyze_maritime_document_endpoint_accessible': False,
            'backend_returns_200_ok': False,
            'backend_processes_file_upload': False,
            'backend_validates_document_type': False,
            'backend_validates_ship_name': False,
            
            # AI Configuration testing
            'ai_config_exists': False,
            'document_ai_enabled': False,
            'document_ai_config_complete': False,
            'apps_script_url_configured': False,
            
            # Apps Script communication
            'backend_calls_apps_script': False,
            'apps_script_receives_request': False,
            'apps_script_responds_successfully': False,
            'apps_script_returns_summary': False,
            
            # Document AI processing
            'document_ai_processes_file': False,
            'document_ai_returns_text': False,
            'document_ai_summary_generated': False,
            'document_ai_summary_not_empty': False,
            
            # AI field extraction
            'ai_field_extraction_called': False,
            'ai_field_extraction_successful': False,
            'passport_fields_extracted': False,
            'passport_fields_not_empty': False,
            
            # Response validation
            'response_contains_analysis': False,
            'response_contains_passport_data': False,
            'response_success_true': False,
            
            # File operations
            'google_drive_upload_attempted': False,
            'summary_file_created': False,
        }
        
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
                
                self.maritime_tests['authentication_successful'] = True
                if self.current_user.get('company'):
                    self.maritime_tests['user_company_identified'] = True
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
    
    def check_test_file(self):
        """Check if the Vietnamese passport test file exists"""
        try:
            self.log("📄 Checking test file: /app/Ho_chieu_pho_thong.jpg")
            
            test_file_path = Path("/app/Ho_chieu_pho_thong.jpg")
            
            if test_file_path.exists():
                file_size = test_file_path.stat().st_size
                self.log(f"✅ Test file exists: {file_size} bytes")
                self.maritime_tests['test_file_exists'] = True
                return True
            else:
                self.log("❌ Test file not found")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking test file: {str(e)}", "ERROR")
            return False
    
    def check_ai_configuration(self):
        """Check AI configuration for Document AI"""
        try:
            self.log("🤖 Checking AI configuration...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.maritime_tests['ai_config_exists'] = True
                
                try:
                    ai_config = response.json()
                    self.log("✅ AI configuration found")
                    
                    # Check Document AI configuration
                    document_ai = ai_config.get("document_ai", {})
                    
                    if document_ai.get("enabled", False):
                        self.maritime_tests['document_ai_enabled'] = True
                        self.log("✅ Document AI is enabled")
                        
                        # Check required fields
                        project_id = document_ai.get("project_id")
                        processor_id = document_ai.get("processor_id")
                        location = document_ai.get("location", "us")
                        apps_script_url = document_ai.get("apps_script_url")
                        
                        self.log(f"   Project ID: {project_id}")
                        self.log(f"   Processor ID: {processor_id}")
                        self.log(f"   Location: {location}")
                        self.log(f"   Apps Script URL: {apps_script_url}")
                        
                        if project_id and processor_id:
                            self.maritime_tests['document_ai_config_complete'] = True
                            self.log("✅ Document AI configuration is complete")
                        else:
                            self.log("❌ Document AI configuration incomplete - missing project_id or processor_id")
                        
                        if apps_script_url:
                            self.maritime_tests['apps_script_url_configured'] = True
                            self.log("✅ Apps Script URL is configured")
                        else:
                            self.log("❌ Apps Script URL not configured")
                    else:
                        self.log("❌ Document AI is not enabled")
                    
                    return ai_config
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ AI configuration check failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error checking AI configuration: {str(e)}", "ERROR")
            return None
    
    def test_direct_apps_script_call(self):
        """Test direct call to Apps Script URL to verify it's working"""
        try:
            self.log("🔗 Testing direct Apps Script call...")
            self.log(f"   URL: {APPS_SCRIPT_URL}")
            
            # Simple test payload
            test_payload = {
                "action": "test_connection",
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                APPS_SCRIPT_URL,
                json=test_payload,
                timeout=60,
                headers={'Content-Type': 'application/json'}
            )
            
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    self.log(f"   Response data: {json.dumps(response_data, indent=2)}")
                    self.log("✅ Apps Script is accessible and responding")
                    return True
                except:
                    self.log(f"   Response text: {response.text[:500]}")
                    self.log("✅ Apps Script is accessible (non-JSON response)")
                    return True
            else:
                self.log(f"   ❌ Apps Script call failed: {response.status_code}")
                self.log(f"   Response: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing direct Apps Script call: {str(e)}", "ERROR")
            return False
    
    def test_maritime_document_analysis(self):
        """Test the main maritime document analysis endpoint"""
        try:
            self.log("🛂 Testing maritime document analysis endpoint...")
            
            # Read the test file
            test_file_path = Path("/app/Ho_chieu_pho_thong.jpg")
            
            if not test_file_path.exists():
                self.log("❌ Test file not found")
                return None
            
            with open(test_file_path, 'rb') as f:
                file_content = f.read()
            
            self.log(f"📄 Loaded test file: {len(file_content)} bytes")
            
            # Prepare the request
            endpoint = f"{BACKEND_URL}/crew/analyze-maritime-document"
            self.log(f"   POST {endpoint}")
            
            # Prepare form data
            files = {
                'document_file': ('Ho_chieu_pho_thong.jpg', file_content, 'image/jpeg')
            }
            
            data = {
                'document_type': 'passport',
                'ship_name': 'TEST_SHIP'
            }
            
            self.log(f"   Document type: {data['document_type']}")
            self.log(f"   Ship name: {data['ship_name']}")
            
            # Make the request
            self.log("🚀 Making request to maritime document analysis endpoint...")
            
            response = requests.post(
                endpoint,
                files=files,
                data=data,
                headers=self.get_headers(),
                timeout=120  # Longer timeout for document processing
            )
            
            self.log(f"   Response status: {response.status_code}")
            self.maritime_tests['analyze_maritime_document_endpoint_accessible'] = True
            
            if response.status_code == 200:
                self.maritime_tests['backend_returns_200_ok'] = True
                self.maritime_tests['backend_processes_file_upload'] = True
                self.log("✅ Backend endpoint accessible and returns 200 OK")
                
                try:
                    response_data = response.json()
                    self.log("✅ Response is valid JSON")
                    
                    # Log the full response for debugging
                    self.log("📋 Full response data:")
                    self.log(json.dumps(response_data, indent=2, default=str))
                    
                    # Check response structure
                    if response_data.get("success"):
                        self.maritime_tests['response_success_true'] = True
                        self.log("✅ Response indicates success")
                    else:
                        self.log("❌ Response indicates failure")
                    
                    # Check analysis data
                    analysis = response_data.get("analysis", {})
                    if analysis:
                        self.maritime_tests['response_contains_analysis'] = True
                        self.log("✅ Response contains analysis data")
                        
                        # Check passport-specific fields
                        passport_fields = [
                            'full_name', 'sex', 'date_of_birth', 'place_of_birth',
                            'passport_number', 'nationality', 'issue_date', 'expiry_date'
                        ]
                        
                        self.log("🔍 Checking passport fields:")
                        non_empty_fields = 0
                        for field in passport_fields:
                            value = analysis.get(field, "")
                            self.log(f"   {field}: '{value}'")
                            if value and value.strip():
                                non_empty_fields += 1
                        
                        if non_empty_fields > 0:
                            self.maritime_tests['passport_fields_not_empty'] = True
                            self.log(f"✅ Found {non_empty_fields}/{len(passport_fields)} non-empty passport fields")
                        else:
                            self.log("❌ ALL passport fields are empty - this is the main issue!")
                        
                        # Check processing method
                        processing_method = analysis.get("processing_method", "")
                        confidence_score = analysis.get("confidence_score", 0.0)
                        
                        self.log(f"   Processing method: {processing_method}")
                        self.log(f"   Confidence score: {confidence_score}")
                        
                        if processing_method == "maritime_summary_to_ai_extraction":
                            self.maritime_tests['ai_field_extraction_successful'] = True
                            self.log("✅ AI field extraction was attempted")
                        elif processing_method == "summary_only":
                            self.log("⚠️ Only summary generated, AI extraction failed")
                        else:
                            self.log(f"⚠️ Unknown processing method: {processing_method}")
                    else:
                        self.log("❌ Response does not contain analysis data")
                    
                    # Check files information
                    files_info = response_data.get("files", {})
                    if files_info:
                        self.maritime_tests['google_drive_upload_attempted'] = True
                        self.log("✅ Google Drive upload was attempted")
                        
                        document_info = files_info.get("document", {})
                        summary_info = files_info.get("summary", {})
                        
                        if document_info:
                            self.log(f"   Document folder: {document_info.get('folder')}")
                            self.log(f"   Document filename: {document_info.get('filename')}")
                        
                        if summary_info:
                            self.maritime_tests['summary_file_created'] = True
                            self.log(f"   Summary folder: {summary_info.get('folder')}")
                            self.log(f"   Summary filename: {summary_info.get('filename')}")
                    
                    return response_data
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    self.log(f"   Response text: {response.text[:1000]}")
                    return None
            else:
                self.log(f"   ❌ Backend endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error text: {response.text[:500]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing maritime document analysis: {str(e)}", "ERROR")
            traceback.print_exc()
            return None
    
    def test_backend_logs_analysis(self):
        """Check backend logs for more detailed debugging information"""
        try:
            self.log("📋 Checking backend logs for debugging information...")
            
            # Try to get backend logs (this might not work in all environments)
            try:
                import subprocess
                result = subprocess.run(
                    ['tail', '-n', '50', '/var/log/supervisor/backend.err.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout:
                    self.log("📋 Recent backend error logs:")
                    for line in result.stdout.split('\n')[-20:]:  # Last 20 lines
                        if line.strip():
                            self.log(f"   {line}")
                else:
                    self.log("   No recent error logs found")
                    
            except Exception as log_error:
                self.log(f"   Could not access backend logs: {log_error}")
            
            # Try stdout logs too
            try:
                result = subprocess.run(
                    ['tail', '-n', '50', '/var/log/supervisor/backend.out.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout:
                    self.log("📋 Recent backend output logs:")
                    for line in result.stdout.split('\n')[-20:]:  # Last 20 lines
                        if line.strip() and ('maritime' in line.lower() or 'passport' in line.lower() or 'document' in line.lower()):
                            self.log(f"   {line}")
                            
            except Exception as log_error:
                self.log(f"   Could not access backend output logs: {log_error}")
                
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def run_comprehensive_maritime_document_test(self):
        """Run comprehensive test of maritime document analysis system"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE MARITIME DOCUMENT ANALYSIS TEST")
            self.log("=" * 80)
            self.log("DEBUGGING: Apps Script running but Document AI returns empty results")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Check test file
            self.log("\nSTEP 2: Check test file")
            if not self.check_test_file():
                self.log("❌ CRITICAL: Test file not found - cannot proceed")
                return False
            
            # Step 3: Check AI configuration
            self.log("\nSTEP 3: Check AI configuration")
            ai_config = self.check_ai_configuration()
            if not ai_config:
                self.log("❌ CRITICAL: AI configuration not found - cannot proceed")
                return False
            
            # Step 4: Test direct Apps Script call
            self.log("\nSTEP 4: Test direct Apps Script call")
            self.test_direct_apps_script_call()
            
            # Step 5: Test maritime document analysis endpoint
            self.log("\nSTEP 5: Test maritime document analysis endpoint")
            analysis_result = self.test_maritime_document_analysis()
            
            # Step 6: Check backend logs for debugging
            self.log("\nSTEP 6: Check backend logs for debugging")
            self.test_backend_logs_analysis()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE MARITIME DOCUMENT ANALYSIS TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 MARITIME DOCUMENT ANALYSIS TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.maritime_tests)
            passed_tests = sum(1 for result in self.maritime_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('test_file_exists', 'Test file exists'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.maritime_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend API Results
            self.log("\n🔧 BACKEND API:")
            backend_tests = [
                ('analyze_maritime_document_endpoint_accessible', 'Endpoint accessible'),
                ('backend_returns_200_ok', 'Returns 200 OK'),
                ('backend_processes_file_upload', 'Processes file upload'),
                ('backend_validates_document_type', 'Validates document type'),
                ('backend_validates_ship_name', 'Validates ship name'),
            ]
            
            for test_key, description in backend_tests:
                status = "✅ PASS" if self.maritime_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # AI Configuration Results
            self.log("\n🤖 AI CONFIGURATION:")
            ai_config_tests = [
                ('ai_config_exists', 'AI config exists'),
                ('document_ai_enabled', 'Document AI enabled'),
                ('document_ai_config_complete', 'Document AI config complete'),
                ('apps_script_url_configured', 'Apps Script URL configured'),
            ]
            
            for test_key, description in ai_config_tests:
                status = "✅ PASS" if self.maritime_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Apps Script Communication Results
            self.log("\n🔗 APPS SCRIPT COMMUNICATION:")
            apps_script_tests = [
                ('backend_calls_apps_script', 'Backend calls Apps Script'),
                ('apps_script_receives_request', 'Apps Script receives request'),
                ('apps_script_responds_successfully', 'Apps Script responds successfully'),
                ('apps_script_returns_summary', 'Apps Script returns summary'),
            ]
            
            for test_key, description in apps_script_tests:
                status = "✅ PASS" if self.maritime_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Document AI Processing Results
            self.log("\n📄 DOCUMENT AI PROCESSING:")
            doc_ai_tests = [
                ('document_ai_processes_file', 'Document AI processes file'),
                ('document_ai_returns_text', 'Document AI returns text'),
                ('document_ai_summary_generated', 'Document AI summary generated'),
                ('document_ai_summary_not_empty', 'Document AI summary not empty'),
            ]
            
            for test_key, description in doc_ai_tests:
                status = "✅ PASS" if self.maritime_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # AI Field Extraction Results
            self.log("\n🧠 AI FIELD EXTRACTION:")
            ai_extraction_tests = [
                ('ai_field_extraction_called', 'AI field extraction called'),
                ('ai_field_extraction_successful', 'AI field extraction successful'),
                ('passport_fields_extracted', 'Passport fields extracted'),
                ('passport_fields_not_empty', 'Passport fields not empty'),
            ]
            
            for test_key, description in ai_extraction_tests:
                status = "✅ PASS" if self.maritime_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Response Validation Results
            self.log("\n📋 RESPONSE VALIDATION:")
            response_tests = [
                ('response_contains_analysis', 'Response contains analysis'),
                ('response_contains_passport_data', 'Response contains passport data'),
                ('response_success_true', 'Response success is true'),
            ]
            
            for test_key, description in response_tests:
                status = "✅ PASS" if self.maritime_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # File Operations Results
            self.log("\n📁 FILE OPERATIONS:")
            file_tests = [
                ('google_drive_upload_attempted', 'Google Drive upload attempted'),
                ('summary_file_created', 'Summary file created'),
            ]
            
            for test_key, description in file_tests:
                status = "✅ PASS" if self.maritime_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Root Cause Analysis
            self.log("\n🔍 ROOT CAUSE ANALYSIS:")
            
            if not self.maritime_tests.get('passport_fields_not_empty', False):
                self.log("   ❌ MAIN ISSUE: All passport fields are empty")
                
                if self.maritime_tests.get('backend_returns_200_ok', False):
                    self.log("   ✅ Backend API is working (returns 200 OK)")
                    
                    if self.maritime_tests.get('document_ai_config_complete', False):
                        self.log("   ✅ Document AI configuration is complete")
                        
                        if self.maritime_tests.get('apps_script_url_configured', False):
                            self.log("   ✅ Apps Script URL is configured")
                            self.log("   🔍 LIKELY ISSUE: Problem in Apps Script → Document AI → Summary → AI extraction chain")
                            self.log("   🔍 NEXT STEPS: Check Apps Script logs, Document AI API calls, summary generation")
                        else:
                            self.log("   ❌ ISSUE: Apps Script URL not configured")
                    else:
                        self.log("   ❌ ISSUE: Document AI configuration incomplete")
                else:
                    self.log("   ❌ ISSUE: Backend API not working properly")
            else:
                self.log("   ✅ Passport fields are being extracted successfully")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the maritime document analysis tests"""
    tester = MaritimeDocumentTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_maritime_document_test()
        
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
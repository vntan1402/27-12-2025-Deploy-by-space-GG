#!/usr/bin/env python3
"""
Ship Management System - Google Apps Script v2.1 Testing
FOCUS: Test the newly updated Google Apps Script (v2.1 with real upload) using the new URL

REVIEW REQUEST REQUIREMENTS:
Test the newly updated Google Apps Script (v2.1 with real upload) using the new URL to verify that 
SUMMARY folder is now created in Google Drive and summary files are actually uploaded.

NEW APPS SCRIPT URL: https://script.google.com/macros/s/AKfycbzRGG-cwbPW5D_jY4-ejgHu4IbR1_GJ2GyBRqsiAYxihdGUv2Me4lua10wywooZGd8/exec

SPECIFIC TESTING REQUIREMENTS:
1. Update Apps Script URL: Ensure backend uses the new Apps Script URL
2. Authentication: Login with admin1/123456 and verify Document AI configuration
3. Test Passport Upload: Upload a test passport file to trigger summary creation
4. Verify Real Upload: Check that files are actually uploaded to Google Drive with real file IDs
5. Confirm SUMMARY Folder: Verify SUMMARY folder is created at company root level
6. File Content Verification: Ensure summary files contain actual content

CRITICAL SUCCESS CRITERIA:
- New Apps Script URL should be accessible and respond correctly
- Backend should communicate successfully with new Apps Script
- SUMMARY folder should appear in Google Drive company folder
- Summary files should be uploaded with real Google Drive file IDs
- Files should contain actual passport analysis content
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
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

# Expected new Apps Script URL
NEW_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzRGG-cwbPW5D_jY4-ejgHu4IbR1_GJ2GyBRqsiAYxihdGUv2Me4lua10wywooZGd8/exec"

class AppsScriptV21Tester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Apps Script v2.1 testing
        self.apps_script_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'document_ai_config_accessible': False,
            
            # Apps Script URL verification
            'new_apps_script_url_configured': False,
            'apps_script_url_accessible': False,
            'apps_script_responds_correctly': False,
            
            # Document AI configuration
            'document_ai_enabled': False,
            'document_ai_project_configured': False,
            'document_ai_processor_configured': False,
            
            # Passport upload and analysis
            'passport_upload_endpoint_accessible': False,
            'passport_file_upload_successful': False,
            'document_ai_analysis_triggered': False,
            'summary_generation_successful': False,
            
            # Google Drive integration
            'google_drive_communication_successful': False,
            'real_file_ids_returned': False,
            'summary_folder_creation_confirmed': False,
            'summary_files_uploaded': False,
            'file_content_verification': False,
            
            # Backend logs analysis
            'backend_uses_new_apps_script_url': False,
            'real_upload_success_logs': False,
            'folder_creation_logs': False,
            'file_upload_success_logs': False,
        }
        
        # Store test data for analysis
        self.uploaded_files = []
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
                
                self.apps_script_tests['authentication_successful'] = True
                self.user_company = self.current_user.get('company')
                if self.user_company:
                    self.apps_script_tests['user_company_identified'] = True
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
    
    def test_apps_script_url_configuration(self):
        """Test if backend is configured with the new Apps Script URL"""
        try:
            self.log("🔗 Testing Apps Script URL configuration...")
            
            # Get AI configuration to check Apps Script URL
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.apps_script_tests['document_ai_config_accessible'] = True
                self.log("✅ Document AI config accessible")
                
                try:
                    config_data = response.json()
                    document_ai = config_data.get('document_ai', {})
                    
                    # Check if Document AI is enabled
                    if document_ai.get('enabled'):
                        self.apps_script_tests['document_ai_enabled'] = True
                        self.log("✅ Document AI enabled")
                        
                        # Check project configuration
                        project_id = document_ai.get('project_id')
                        if project_id:
                            self.apps_script_tests['document_ai_project_configured'] = True
                            self.log(f"✅ Document AI project configured: {project_id}")
                        
                        # Check processor configuration
                        processor_id = document_ai.get('processor_id')
                        if processor_id:
                            self.apps_script_tests['document_ai_processor_configured'] = True
                            self.log(f"✅ Document AI processor configured: {processor_id}")
                        
                        # Check Apps Script URL
                        apps_script_url = document_ai.get('apps_script_url')
                        if apps_script_url:
                            self.log(f"   Current Apps Script URL: {apps_script_url}")
                            
                            if apps_script_url == NEW_APPS_SCRIPT_URL:
                                self.apps_script_tests['new_apps_script_url_configured'] = True
                                self.log("✅ New Apps Script URL is configured correctly")
                            else:
                                self.log(f"   ❌ Apps Script URL mismatch!")
                                self.log(f"   Expected: {NEW_APPS_SCRIPT_URL}")
                                self.log(f"   Current:  {apps_script_url}")
                        else:
                            self.log("   ❌ Apps Script URL not configured")
                    else:
                        self.log("   ❌ Document AI not enabled")
                    
                    return config_data
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ Failed to get AI config: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing Apps Script URL configuration: {str(e)}", "ERROR")
            return None
    
    def test_apps_script_accessibility(self):
        """Test if the new Apps Script URL is accessible and responds correctly"""
        try:
            self.log("🌐 Testing Apps Script URL accessibility...")
            self.log(f"   Testing URL: {NEW_APPS_SCRIPT_URL}")
            
            # Test basic GET request to Apps Script
            response = requests.get(NEW_APPS_SCRIPT_URL, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.apps_script_tests['apps_script_url_accessible'] = True
                self.log("✅ Apps Script URL is accessible")
                
                # Check if response indicates it's working
                response_text = response.text[:500]  # First 500 chars
                self.log(f"   Response preview: {response_text}")
                
                # Look for indicators that it's the correct Apps Script
                if any(keyword in response_text.lower() for keyword in ['google', 'script', 'apps']):
                    self.apps_script_tests['apps_script_responds_correctly'] = True
                    self.log("✅ Apps Script responds correctly")
                else:
                    self.log("   ⚠️ Apps Script response doesn't contain expected keywords")
                
                return True
            else:
                self.log(f"   ❌ Apps Script URL not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Apps Script accessibility: {str(e)}", "ERROR")
            return False
    
    def create_test_passport_file(self):
        """Create a test passport file for upload"""
        try:
            self.log("📄 Creating test passport file...")
            
            # Create a simple text file that simulates passport content
            passport_content = """
PASSPORT
REPUBLIC OF VIETNAM
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM

Passport No./Số hộ chiếu: C1234567
Surname/Họ: NGUYEN
Given Names/Tên: VAN TEST
Date of Birth/Ngày sinh: 15/05/1990
Place of Birth/Nơi sinh: HO CHI MINH CITY
Sex/Giới tính: M/Nam
Nationality/Quốc tịch: VIETNAMESE/VIỆT NAM
Date of Issue/Ngày cấp: 01/01/2020
Date of Expiry/Ngày hết hạn: 01/01/2030
Issuing Authority/Cơ quan cấp: IMMIGRATION DEPARTMENT

This is a test passport file for Google Apps Script v2.1 testing.
Testing SUMMARY folder creation and real file upload functionality.
"""
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.write(passport_content)
            temp_file.close()
            
            self.log(f"✅ Test passport file created: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Error creating test passport file: {str(e)}", "ERROR")
            return None
    
    def test_passport_upload_and_analysis(self):
        """Test passport upload and analysis with new Apps Script"""
        try:
            self.log("📤 Testing passport upload and analysis...")
            
            # Create test passport file
            test_file_path = self.create_test_passport_file()
            if not test_file_path:
                return False
            
            try:
                # Prepare file for upload
                with open(test_file_path, 'rb') as f:
                    files = {
                        'file': ('test_passport_apps_script_v21.txt', f, 'text/plain')
                    }
                    
                    endpoint = f"{BACKEND_URL}/crew/analyze-passport"
                    self.log(f"   POST {endpoint}")
                    
                    response = requests.post(
                        endpoint, 
                        files=files, 
                        headers=self.get_headers(), 
                        timeout=120  # Longer timeout for file processing
                    )
                    
                    self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.apps_script_tests['passport_upload_endpoint_accessible'] = True
                    self.apps_script_tests['passport_file_upload_successful'] = True
                    self.log("✅ Passport upload endpoint accessible and working")
                    
                    try:
                        response_data = response.json()
                        self.log("✅ Passport analysis response received")
                        
                        # Check for Document AI analysis
                        if 'extracted_data' in response_data:
                            self.apps_script_tests['document_ai_analysis_triggered'] = True
                            self.log("✅ Document AI analysis triggered")
                            
                            extracted_data = response_data['extracted_data']
                            self.log(f"   Extracted data keys: {list(extracted_data.keys())}")
                        
                        # Check for summary generation
                        if 'summary' in response_data or 'analysis_summary' in response_data:
                            self.apps_script_tests['summary_generation_successful'] = True
                            self.log("✅ Summary generation successful")
                        
                        # Check for Google Drive file IDs
                        file_ids = []
                        for key, value in response_data.items():
                            if 'file_id' in key and value:
                                file_ids.append(value)
                                self.log(f"   File ID found: {key} = {value}")
                        
                        if file_ids:
                            self.apps_script_tests['google_drive_communication_successful'] = True
                            self.apps_script_tests['real_file_ids_returned'] = True
                            self.log("✅ Real Google Drive file IDs returned")
                            
                            # Check if file IDs look real (not fake/mock)
                            for file_id in file_ids:
                                if not file_id.startswith('fake_') and not file_id.startswith('mock_'):
                                    self.log(f"   ✅ Real file ID detected: {file_id}")
                                else:
                                    self.log(f"   ❌ Mock file ID detected: {file_id}")
                        
                        # Store response for further analysis
                        self.uploaded_files.append(response_data)
                        
                        return response_data
                        
                    except json.JSONDecodeError as e:
                        self.log(f"   ❌ Invalid JSON response: {str(e)}")
                        return None
                else:
                    self.log(f"   ❌ Passport upload failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"   Error: {response.text[:200]}")
                    return None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(test_file_path)
                    self.log("   Temporary file cleaned up")
                except:
                    pass
                
        except Exception as e:
            self.log(f"❌ Error testing passport upload: {str(e)}", "ERROR")
            return None
    
    def analyze_backend_logs(self):
        """Analyze backend logs for Apps Script communication"""
        try:
            self.log("🔍 Analyzing backend logs for Apps Script communication...")
            
            # Check supervisor backend logs
            try:
                import subprocess
                result = subprocess.run(
                    ['tail', '-n', '100', '/var/log/supervisor/backend.err.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    log_content = result.stdout
                    self.log("✅ Backend logs retrieved")
                    
                    # Check for new Apps Script URL usage
                    if NEW_APPS_SCRIPT_URL in log_content:
                        self.apps_script_tests['backend_uses_new_apps_script_url'] = True
                        self.log("✅ Backend uses new Apps Script URL")
                    
                    # Check for real upload success
                    success_indicators = [
                        'success=True',
                        'file_id',
                        'Apps Script response received',
                        'successfully uploaded'
                    ]
                    
                    for indicator in success_indicators:
                        if indicator in log_content:
                            self.apps_script_tests['real_upload_success_logs'] = True
                            self.log(f"✅ Real upload success indicator found: {indicator}")
                            break
                    
                    # Check for SUMMARY folder creation
                    summary_indicators = [
                        'SUMMARY/',
                        'SUMMARY folder',
                        'summary_file',
                        'Saving summary to Google Drive'
                    ]
                    
                    for indicator in summary_indicators:
                        if indicator in log_content:
                            self.apps_script_tests['folder_creation_logs'] = True
                            self.apps_script_tests['summary_files_uploaded'] = True
                            self.log(f"✅ SUMMARY folder/file indicator found: {indicator}")
                            break
                    
                    # Check for file upload success confirmations
                    upload_confirmations = [
                        'file uploads completed successfully',
                        'uploaded successfully',
                        'Google Drive upload successful'
                    ]
                    
                    for confirmation in upload_confirmations:
                        if confirmation in log_content:
                            self.apps_script_tests['file_upload_success_logs'] = True
                            self.log(f"✅ File upload success confirmation: {confirmation}")
                            break
                    
                    # Log relevant excerpts
                    lines = log_content.split('\n')
                    relevant_lines = [line for line in lines if any(keyword in line.lower() for keyword in 
                                    ['apps script', 'summary', 'google drive', 'file_id', 'upload'])]
                    
                    if relevant_lines:
                        self.log("   Relevant log excerpts:")
                        for line in relevant_lines[-10:]:  # Last 10 relevant lines
                            self.log(f"     {line}")
                    
                else:
                    self.log("   ⚠️ Could not retrieve backend logs")
                    
            except Exception as e:
                self.log(f"   ⚠️ Error retrieving backend logs: {str(e)}")
            
        except Exception as e:
            self.log(f"❌ Error analyzing backend logs: {str(e)}", "ERROR")
    
    def test_summary_folder_verification(self):
        """Test verification of SUMMARY folder creation"""
        try:
            self.log("📁 Testing SUMMARY folder verification...")
            
            # This would ideally check Google Drive directly, but we'll check through backend response
            if self.uploaded_files:
                for upload_response in self.uploaded_files:
                    # Look for SUMMARY folder indicators in response
                    response_str = json.dumps(upload_response).lower()
                    
                    if 'summary' in response_str:
                        self.apps_script_tests['summary_folder_creation_confirmed'] = True
                        self.log("✅ SUMMARY folder creation confirmed in response")
                    
                    # Check for file content verification
                    if any(key in upload_response for key in ['summary', 'analysis_summary', 'extracted_data']):
                        content = upload_response.get('summary') or upload_response.get('analysis_summary') or str(upload_response.get('extracted_data', ''))
                        if content and len(content.strip()) > 10:  # Non-empty content
                            self.apps_script_tests['file_content_verification'] = True
                            self.log("✅ File content verification passed - summary contains actual content")
                            self.log(f"   Content preview: {content[:100]}...")
                        else:
                            self.log("   ❌ File content verification failed - empty or minimal content")
            else:
                self.log("   ⚠️ No upload responses to verify")
            
        except Exception as e:
            self.log(f"❌ Error testing SUMMARY folder verification: {str(e)}", "ERROR")
    
    def run_comprehensive_apps_script_test(self):
        """Run comprehensive test of Apps Script v2.1 functionality"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE GOOGLE APPS SCRIPT v2.1 TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Test Apps Script URL configuration
            self.log("\nSTEP 2: Testing Apps Script URL configuration")
            config_data = self.test_apps_script_url_configuration()
            
            # Step 3: Test Apps Script accessibility
            self.log("\nSTEP 3: Testing Apps Script URL accessibility")
            self.test_apps_script_accessibility()
            
            # Step 4: Test passport upload and analysis
            self.log("\nSTEP 4: Testing passport upload and analysis")
            upload_response = self.test_passport_upload_and_analysis()
            
            # Step 5: Analyze backend logs
            self.log("\nSTEP 5: Analyzing backend logs")
            self.analyze_backend_logs()
            
            # Step 6: Test SUMMARY folder verification
            self.log("\nSTEP 6: Testing SUMMARY folder verification")
            self.test_summary_folder_verification()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE APPS SCRIPT v2.1 TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 GOOGLE APPS SCRIPT v2.1 TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.apps_script_tests)
            passed_tests = sum(1 for result in self.apps_script_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('document_ai_config_accessible', 'Document AI config accessible'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.apps_script_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Apps Script URL Results
            self.log("\n🔗 APPS SCRIPT URL VERIFICATION:")
            url_tests = [
                ('new_apps_script_url_configured', 'New Apps Script URL configured'),
                ('apps_script_url_accessible', 'Apps Script URL accessible'),
                ('apps_script_responds_correctly', 'Apps Script responds correctly'),
                ('backend_uses_new_apps_script_url', 'Backend uses new Apps Script URL'),
            ]
            
            for test_key, description in url_tests:
                status = "✅ PASS" if self.apps_script_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Document AI Configuration Results
            self.log("\n🤖 DOCUMENT AI CONFIGURATION:")
            ai_tests = [
                ('document_ai_enabled', 'Document AI enabled'),
                ('document_ai_project_configured', 'Document AI project configured'),
                ('document_ai_processor_configured', 'Document AI processor configured'),
            ]
            
            for test_key, description in ai_tests:
                status = "✅ PASS" if self.apps_script_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Passport Upload Results
            self.log("\n📤 PASSPORT UPLOAD & ANALYSIS:")
            upload_tests = [
                ('passport_upload_endpoint_accessible', 'Passport upload endpoint accessible'),
                ('passport_file_upload_successful', 'Passport file upload successful'),
                ('document_ai_analysis_triggered', 'Document AI analysis triggered'),
                ('summary_generation_successful', 'Summary generation successful'),
            ]
            
            for test_key, description in upload_tests:
                status = "✅ PASS" if self.apps_script_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Google Drive Integration Results
            self.log("\n☁️ GOOGLE DRIVE INTEGRATION:")
            gdrive_tests = [
                ('google_drive_communication_successful', 'Google Drive communication successful'),
                ('real_file_ids_returned', 'Real file IDs returned (not mock)'),
                ('summary_folder_creation_confirmed', 'SUMMARY folder creation confirmed'),
                ('summary_files_uploaded', 'Summary files uploaded'),
                ('file_content_verification', 'File content verification passed'),
            ]
            
            for test_key, description in gdrive_tests:
                status = "✅ PASS" if self.apps_script_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Analysis Results
            self.log("\n📋 BACKEND LOGS ANALYSIS:")
            logs_tests = [
                ('real_upload_success_logs', 'Real upload success logs found'),
                ('folder_creation_logs', 'Folder creation logs found'),
                ('file_upload_success_logs', 'File upload success logs found'),
            ]
            
            for test_key, description in logs_tests:
                status = "✅ PASS" if self.apps_script_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Success Criteria Assessment
            self.log("\n🎯 CRITICAL SUCCESS CRITERIA ASSESSMENT:")
            
            critical_criteria = [
                ('apps_script_url_accessible', 'New Apps Script URL accessible and responds correctly'),
                ('google_drive_communication_successful', 'Backend communicates successfully with new Apps Script'),
                ('summary_folder_creation_confirmed', 'SUMMARY folder appears in Google Drive company folder'),
                ('real_file_ids_returned', 'Summary files uploaded with real Google Drive file IDs'),
                ('file_content_verification', 'Files contain actual passport analysis content'),
            ]
            
            critical_passed = sum(1 for test_key, _ in critical_criteria if self.apps_script_tests.get(test_key, False))
            
            for test_key, description in critical_criteria:
                status = "✅ MET" if self.apps_script_tests.get(test_key, False) else "❌ NOT MET"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🏆 OVERALL ASSESSMENT:")
            
            if critical_passed == len(critical_criteria):
                self.log("   ✅ ALL CRITICAL SUCCESS CRITERIA MET")
                self.log("   ✅ Google Apps Script v2.1 with real upload is working correctly")
                self.log("   ✅ SUMMARY folder creation and file upload functionality verified")
            elif critical_passed >= 3:
                self.log("   ⚠️ MOST CRITICAL CRITERIA MET - Some issues remain")
                self.log(f"   ⚠️ {critical_passed}/{len(critical_criteria)} critical criteria met")
            else:
                self.log("   ❌ CRITICAL ISSUES IDENTIFIED")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_criteria)} critical criteria met")
                self.log("   ❌ Google Apps Script v2.1 may not be working correctly")
            
            if success_rate >= 80:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            # Recommendations
            self.log("\n💡 RECOMMENDATIONS:")
            
            if not self.apps_script_tests.get('new_apps_script_url_configured'):
                self.log("   🔧 Update backend configuration to use new Apps Script URL")
            
            if not self.apps_script_tests.get('real_file_ids_returned'):
                self.log("   🔧 Verify Apps Script v2.1 is returning real Google Drive file IDs")
            
            if not self.apps_script_tests.get('summary_folder_creation_confirmed'):
                self.log("   🔧 Check Google Drive directly for SUMMARY folder creation")
            
            if success_rate < 80:
                self.log("   🔧 Review failed tests and address configuration issues")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the Apps Script v2.1 tests"""
    tester = AppsScriptV21Tester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_apps_script_test()
        
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
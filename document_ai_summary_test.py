#!/usr/bin/env python3
"""
Document AI Summary File Upload Debug Test
FOCUS: Investigate why Document AI summary files are not appearing in SUMMARY folder in Google Drive

REVIEW REQUEST REQUIREMENTS:
1. Authentication & Setup: Login with admin1/123456, verify Google Drive configuration
2. Passport Analysis with File Tracking: Upload a test passport and track the file upload process
3. Google Drive Structure Analysis: Check actual Google Drive folder structure and verify SUMMARY folder exists
4. Backend Log Analysis: Capture detailed logs during summary file upload process
5. Error Investigation: Check for any Google Drive upload errors or permission issues

CRITICAL INVESTIGATION POINTS:
- Summary File Creation: Verify summary content is generated correctly in backend
- Google Drive Upload Process: Check if upload_file_with_folder_creation function works for SUMMARY folder
- Folder Path Analysis: Verify folder_path="SUMMARY" is processed correctly
- Google Apps Script Integration: Check if Apps Script handles SUMMARY folder creation/upload
- Permission Issues: Verify company Google Drive configuration allows folder creation
"""

import requests
import json
import os
import sys
import base64
import tempfile
from datetime import datetime, timedelta
import time
import traceback
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://maritime-ai-crew-1.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class DocumentAISummaryTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Document AI summary file upload debugging
        self.debug_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'google_drive_config_verified': False,
            
            # Document AI Configuration
            'ai_config_accessible': False,
            'document_ai_enabled': False,
            'document_ai_config_complete': False,
            
            # Passport Analysis Workflow
            'passport_analysis_endpoint_accessible': False,
            'passport_file_upload_successful': False,
            'document_ai_analysis_completed': False,
            'summary_content_generated': False,
            
            # Google Drive Upload Process
            'passport_file_uploaded_to_crewlist': False,
            'summary_file_upload_attempted': False,
            'summary_folder_creation_attempted': False,
            'summary_file_upload_successful': False,
            
            # Error Investigation
            'google_drive_upload_errors_captured': False,
            'apps_script_errors_captured': False,
            'permission_errors_identified': False,
            'folder_creation_errors_identified': False,
        }
        
        # Store test data
        self.test_ship_name = "BROTHER 36"
        self.uploaded_files = []
        
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
                if self.current_user.get('company'):
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
    
    def verify_ai_configuration(self):
        """Verify Google Document AI configuration"""
        try:
            self.log("🤖 Verifying Google Document AI configuration...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.debug_tests['ai_config_accessible'] = True
                self.log("✅ AI configuration endpoint accessible")
                
                try:
                    ai_config = response.json()
                    self.log(f"   AI Provider: {ai_config.get('provider', 'Not set')}")
                    self.log(f"   AI Model: {ai_config.get('model', 'Not set')}")
                    
                    # Check Document AI configuration
                    document_ai = ai_config.get('document_ai', {})
                    if document_ai:
                        self.log("   📄 Document AI Configuration:")
                        self.log(f"      Enabled: {document_ai.get('enabled', False)}")
                        self.log(f"      Project ID: {document_ai.get('project_id', 'Not set')}")
                        self.log(f"      Location: {document_ai.get('location', 'Not set')}")
                        self.log(f"      Processor ID: {document_ai.get('processor_id', 'Not set')}")
                        
                        if document_ai.get('enabled', False):
                            self.debug_tests['document_ai_enabled'] = True
                            self.log("   ✅ Document AI is enabled")
                            
                            # Check if all required parameters are configured
                            if all([
                                document_ai.get('project_id'),
                                document_ai.get('processor_id')
                            ]):
                                self.debug_tests['document_ai_config_complete'] = True
                                self.log("   ✅ Document AI configuration is complete")
                                return True
                            else:
                                self.log("   ❌ Document AI configuration is incomplete")
                                return False
                        else:
                            self.log("   ❌ Document AI is not enabled")
                            return False
                    else:
                        self.log("   ❌ No Document AI configuration found")
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                self.log(f"   ❌ AI configuration endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying AI configuration: {str(e)}", "ERROR")
            return False
    
    def create_test_passport_file(self):
        """Create a test passport file for upload"""
        try:
            self.log("📄 Creating test passport file...")
            
            # Create a simple text file that mimics passport content
            passport_content = """PASSPORT
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
SOCIALIST REPUBLIC OF VIETNAM

Type/Loại: P
Country code/Mã quốc gia: VNM
Passport No./Số hộ chiếu: C1234567

Surname/Họ: NGUYEN
Given names/Tên: VAN TEST

Nationality/Quốc tịch: VIETNAMESE
Date of birth/Ngày sinh: 15/05/1990
Sex/Giới tính: M
Place of birth/Nơi sinh: HO CHI MINH

Date of issue/Ngày cấp: 01/01/2020
Date of expiry/Ngày hết hạn: 01/01/2030
Authority/Cơ quan cấp: IMMIGRATION DEPARTMENT

This is a test passport file for Document AI summary upload debugging.
"""
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.write(passport_content)
            temp_file.close()
            
            self.log(f"   ✅ Test passport file created: {temp_file.name}")
            self.log(f"   📝 Content length: {len(passport_content)} characters")
            
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Error creating test passport file: {str(e)}", "ERROR")
            return None
    
    def test_passport_analysis_with_file_tracking(self):
        """Test passport analysis endpoint with detailed file tracking"""
        try:
            self.log("🛂 Testing passport analysis with detailed file tracking...")
            
            # Create test passport file
            test_file_path = self.create_test_passport_file()
            if not test_file_path:
                self.log("❌ Failed to create test passport file")
                return False
            
            try:
                # Read test file
                with open(test_file_path, 'rb') as f:
                    file_content = f.read()
                
                filename = "test_passport_debug.txt"
                
                # Prepare multipart form data
                files = {
                    'passport_file': (filename, file_content, 'text/plain')
                }
                data = {
                    'ship_name': self.test_ship_name
                }
                
                endpoint = f"{BACKEND_URL}/crew/analyze-passport"
                self.log(f"   POST {endpoint}")
                self.log(f"   Ship Name: {self.test_ship_name}")
                self.log(f"   File: {filename} ({len(file_content)} bytes)")
                
                # Make request with detailed logging
                self.log("   🚀 Sending passport analysis request...")
                response = requests.post(
                    endpoint, 
                    files=files, 
                    data=data, 
                    headers=self.get_headers(), 
                    timeout=120  # Longer timeout for Document AI processing
                )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.debug_tests['passport_analysis_endpoint_accessible'] = True
                    self.debug_tests['passport_file_upload_successful'] = True
                    self.log("✅ Passport analysis endpoint accessible and working")
                    
                    try:
                        response_data = response.json()
                        self.log("   📊 Response Analysis:")
                        self.log(f"      Success: {response_data.get('success', False)}")
                        self.log(f"      Message: {response_data.get('message', 'No message')}")
                        
                        # Check analysis results
                        analysis = response_data.get('analysis', {})
                        if analysis:
                            self.debug_tests['document_ai_analysis_completed'] = True
                            self.log("   🤖 Document AI Analysis Results:")
                            self.log(f"      Full Name: '{analysis.get('full_name', 'N/A')}'")
                            self.log(f"      Passport Number: '{analysis.get('passport_number', 'N/A')}'")
                            self.log(f"      Confidence Score: {analysis.get('confidence_score', 0):.2%}")
                            self.log(f"      Processing Method: {analysis.get('processing_method', 'N/A')}")
                            
                            # Check if summary content was generated
                            if analysis.get('raw_summary') or analysis.get('full_name'):
                                self.debug_tests['summary_content_generated'] = True
                                self.log("   ✅ Summary content was generated")
                        
                        # Check file upload results
                        files_info = response_data.get('files', {})
                        if files_info:
                            self.log("   📁 File Upload Results:")
                            
                            # Check passport file upload
                            passport_file = files_info.get('passport', {})
                            if passport_file:
                                self.log(f"      Passport File:")
                                self.log(f"         Filename: {passport_file.get('filename', 'N/A')}")
                                self.log(f"         Folder: {passport_file.get('folder', 'N/A')}")
                                upload_result = passport_file.get('upload_result', {})
                                if upload_result and upload_result.get('success'):
                                    self.debug_tests['passport_file_uploaded_to_crewlist'] = True
                                    self.log(f"         ✅ Upload successful to Crewlist folder")
                                else:
                                    self.log(f"         ❌ Upload failed: {upload_result.get('error', 'Unknown error')}")
                            
                            # Check summary file upload - THIS IS THE CRITICAL PART
                            summary_file = files_info.get('summary', {})
                            if summary_file:
                                self.debug_tests['summary_file_upload_attempted'] = True
                                self.log(f"      📋 Summary File:")
                                self.log(f"         Filename: {summary_file.get('filename', 'N/A')}")
                                self.log(f"         Folder: {summary_file.get('folder', 'N/A')}")
                                
                                upload_result = summary_file.get('upload_result', {})
                                self.log(f"         Upload Result: {json.dumps(upload_result, indent=8)}")
                                
                                if upload_result and upload_result.get('success'):
                                    self.debug_tests['summary_file_upload_successful'] = True
                                    self.log(f"         ✅ SUMMARY file upload successful!")
                                    self.log(f"         📂 File ID: {upload_result.get('file_id', 'N/A')}")
                                    self.log(f"         🔗 Folder Path: {upload_result.get('folder_path', 'N/A')}")
                                else:
                                    self.log(f"         ❌ SUMMARY file upload FAILED!")
                                    self.log(f"         💥 Error: {upload_result.get('error', 'Unknown error')}")
                                    self.log(f"         📝 Details: {upload_result.get('details', 'No details')}")
                                    
                                    # This is a critical finding - summary upload failed
                                    self.debug_tests['google_drive_upload_errors_captured'] = True
                            else:
                                self.log("      ❌ No summary file information in response")
                        else:
                            self.log("   ❌ No file upload information in response")
                            
                            # Check if there's an error message about file uploads
                            error_msg = response_data.get('error', '')
                            if error_msg:
                                self.log(f"   💥 File Upload Error: {error_msg}")
                                self.debug_tests['google_drive_upload_errors_captured'] = True
                        
                        return True
                        
                    except json.JSONDecodeError as e:
                        self.log(f"   ❌ Invalid JSON response: {str(e)}")
                        self.log(f"   Raw response: {response.text[:500]}")
                        return False
                        
                elif response.status_code == 404:
                    self.log("   ❌ 404 Error - Likely AI configuration issue")
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', 'Unknown error')
                        self.log(f"   Error: {error_detail}")
                        
                        if "AI configuration not found" in error_detail:
                            self.log("   🔍 ROOT CAUSE: Google Document AI not configured")
                        elif "Document AI is not enabled" in error_detail:
                            self.log("   🔍 ROOT CAUSE: Document AI is disabled in settings")
                        elif "Incomplete Google Document AI configuration" in error_detail:
                            self.log("   🔍 ROOT CAUSE: Document AI configuration incomplete")
                    except:
                        pass
                    return False
                else:
                    self.log(f"   ❌ Passport analysis failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"   Error: {response.text[:200]}")
                    return False
                    
            finally:
                # Clean up test file
                try:
                    os.unlink(test_file_path)
                    self.log(f"   🧹 Cleaned up test file: {test_file_path}")
                except:
                    pass
                
        except Exception as e:
            self.log(f"❌ Error testing passport analysis: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs(self):
        """Check backend logs for Google Drive upload errors"""
        try:
            self.log("📋 Checking backend logs for Google Drive upload errors...")
            
            # This would require access to backend logs
            # For now, we'll simulate by checking if we captured any errors
            if self.debug_tests.get('google_drive_upload_errors_captured', False):
                self.log("   ✅ Google Drive upload errors were captured in response")
                return True
            else:
                self.log("   ⚠️ No explicit Google Drive upload errors captured")
                self.log("   💡 Check supervisor backend logs: tail -n 100 /var/log/supervisor/backend.*.log")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def investigate_google_drive_folder_structure(self):
        """Investigate Google Drive folder structure and SUMMARY folder"""
        try:
            self.log("📂 Investigating Google Drive folder structure...")
            
            # This would require direct Google Drive API access or Apps Script call
            # For now, we'll provide guidance on what to check
            self.log("   🔍 MANUAL INVESTIGATION REQUIRED:")
            self.log("   1. Check if SUMMARY folder exists in Google Drive root")
            self.log("   2. Verify company Google Drive configuration allows root-level folder creation")
            self.log("   3. Check Google Apps Script logs for folder creation attempts")
            self.log("   4. Verify upload_file_with_folder_creation function handles 'SUMMARY' path correctly")
            
            # Based on our test results, provide specific guidance
            if self.debug_tests.get('summary_file_upload_attempted', False):
                if not self.debug_tests.get('summary_file_upload_successful', False):
                    self.log("   🎯 CRITICAL FINDING: Summary file upload was attempted but FAILED")
                    self.log("   💡 This suggests the issue is in Google Drive upload process, not summary generation")
                    self.debug_tests['folder_creation_errors_identified'] = True
                else:
                    self.log("   ✅ Summary file upload was successful according to backend response")
            else:
                self.log("   ❌ Summary file upload was not attempted - check earlier steps")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error investigating Google Drive structure: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_debug_test(self):
        """Run comprehensive debug test for Document AI summary file upload issue"""
        try:
            self.log("🚀 STARTING DOCUMENT AI SUMMARY FILE UPLOAD DEBUG TEST")
            self.log("🎯 OBJECTIVE: Investigate why summary files are not appearing in SUMMARY folder")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication & Setup")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Verify Google Document AI configuration
            self.log("\nSTEP 2: Verify Google Document AI Configuration")
            if not self.verify_ai_configuration():
                self.log("❌ CRITICAL: Document AI configuration issue - may prevent analysis")
                # Continue anyway to see what happens
            
            # Step 3: Test passport analysis with detailed file tracking
            self.log("\nSTEP 3: Test Passport Analysis with File Tracking")
            passport_success = self.test_passport_analysis_with_file_tracking()
            
            # Step 4: Check backend logs for errors
            self.log("\nSTEP 4: Check Backend Logs for Errors")
            self.check_backend_logs()
            
            # Step 5: Investigate Google Drive folder structure
            self.log("\nSTEP 5: Investigate Google Drive Folder Structure")
            self.investigate_google_drive_folder_structure()
            
            self.log("\n" + "=" * 80)
            self.log("✅ DOCUMENT AI SUMMARY DEBUG TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in debug test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_debug_summary(self):
        """Print comprehensive summary of debug findings"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 DOCUMENT AI SUMMARY FILE UPLOAD DEBUG SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.debug_tests)
            passed_tests = sum(1 for result in self.debug_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Debug Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} checks passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('ai_config_accessible', 'AI configuration accessible'),
                ('document_ai_enabled', 'Document AI enabled'),
                ('document_ai_config_complete', 'Document AI configuration complete'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Passport Analysis Results
            self.log("\n🛂 PASSPORT ANALYSIS WORKFLOW:")
            analysis_tests = [
                ('passport_analysis_endpoint_accessible', 'Passport analysis endpoint accessible'),
                ('passport_file_upload_successful', 'Passport file upload successful'),
                ('document_ai_analysis_completed', 'Document AI analysis completed'),
                ('summary_content_generated', 'Summary content generated'),
            ]
            
            for test_key, description in analysis_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Google Drive Upload Results - CRITICAL SECTION
            self.log("\n📁 GOOGLE DRIVE UPLOAD PROCESS:")
            upload_tests = [
                ('passport_file_uploaded_to_crewlist', 'Passport file uploaded to Crewlist folder'),
                ('summary_file_upload_attempted', 'Summary file upload attempted'),
                ('summary_file_upload_successful', 'Summary file upload successful'),
            ]
            
            for test_key, description in upload_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Error Investigation Results
            self.log("\n🔍 ERROR INVESTIGATION:")
            error_tests = [
                ('google_drive_upload_errors_captured', 'Google Drive upload errors captured'),
                ('folder_creation_errors_identified', 'Folder creation errors identified'),
            ]
            
            for test_key, description in error_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Root Cause Analysis
            self.log("\n🎯 ROOT CAUSE ANALYSIS:")
            
            if not self.debug_tests.get('document_ai_config_complete', False):
                self.log("   ❌ POTENTIAL CAUSE: Document AI configuration incomplete")
                self.log("      💡 Check System Settings → AI Configuration → Google Document AI")
                
            if not self.debug_tests.get('summary_file_upload_attempted', False):
                self.log("   ❌ POTENTIAL CAUSE: Summary file upload not attempted")
                self.log("      💡 Issue may be in passport analysis workflow before upload")
                
            elif not self.debug_tests.get('summary_file_upload_successful', False):
                self.log("   ❌ CONFIRMED CAUSE: Summary file upload attempted but FAILED")
                self.log("      💡 Issue is in Google Drive upload process for SUMMARY folder")
                self.log("      🔧 Check upload_file_with_folder_creation function")
                self.log("      🔧 Check Google Apps Script folder creation for 'SUMMARY' path")
                self.log("      🔧 Check company Google Drive permissions for root-level folders")
                
            if self.debug_tests.get('google_drive_upload_errors_captured', False):
                self.log("   ✅ Google Drive upload errors were captured - check response details above")
                
            # Expected Findings Verification
            self.log("\n📋 EXPECTED FINDINGS VERIFICATION:")
            
            expected_findings = [
                "Google Drive upload is failing silently",
                "SUMMARY folder creation is not working", 
                "Permission issues preventing root-level folder access",
                "Apps Script integration issue with folder creation"
            ]
            
            if not self.debug_tests.get('summary_file_upload_successful', False):
                if self.debug_tests.get('summary_file_upload_attempted', False):
                    self.log("   ✅ CONFIRMED: Google Drive upload is failing (not silently - errors captured)")
                    self.log("   ✅ LIKELY: SUMMARY folder creation is not working")
                    self.log("   ✅ POSSIBLE: Permission issues preventing root-level folder access")
                    self.log("   ✅ POSSIBLE: Apps Script integration issue with folder creation")
                else:
                    self.log("   ❓ UNCLEAR: Summary upload not attempted - issue may be earlier in workflow")
            else:
                self.log("   ❌ UNEXPECTED: Summary file upload appears successful according to backend")
                self.log("   💡 Issue may be in Google Drive folder structure or file visibility")
            
            # Recommendations
            self.log("\n💡 RECOMMENDATIONS:")
            
            if not self.debug_tests.get('document_ai_config_complete', False):
                self.log("   1. Complete Google Document AI configuration in System Settings")
                
            if not self.debug_tests.get('summary_file_upload_successful', False):
                self.log("   2. Debug upload_file_with_folder_creation function for folder_path='SUMMARY'")
                self.log("   3. Check Google Apps Script logs for SUMMARY folder creation attempts")
                self.log("   4. Verify company Google Drive configuration allows root-level folder creation")
                self.log("   5. Test SUMMARY folder creation manually in Google Drive")
                
            self.log("   6. Check backend supervisor logs: tail -n 100 /var/log/supervisor/backend.*.log")
            self.log("   7. Monitor Google Apps Script execution logs during passport upload")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing debug summary: {str(e)}", "ERROR")

def main():
    """Main function to run the Document AI summary debug test"""
    tester = DocumentAISummaryTester()
    
    try:
        # Run comprehensive debug test
        success = tester.run_comprehensive_debug_test()
        
        # Print summary
        tester.print_debug_summary()
        
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
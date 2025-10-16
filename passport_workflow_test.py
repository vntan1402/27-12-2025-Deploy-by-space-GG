#!/usr/bin/env python3
"""
Ship Management System - Add Crew From Passport Workflow Testing
FOCUS: Test the updated "Add Crew From Passport" workflow with new simplified folder structure

REVIEW REQUEST REQUIREMENTS:
Test the updated "Add Crew From Passport" workflow with the new simplified folder structure:

POST to /api/crew/analyze-passport with a passport file

The updated workflow should now create:
1. Passport file: `[Ship Name]/Crew Records/[filename].jpg` (no Crew List subfolder)
2. Summary file: `SUMMARY/[filename]_Summary.txt` (no Documents subfolder)

Key changes tested:
- Passport upload uses only `category: "Crew Records"` (no parent_category)  
- Summary upload uses `ship_name: "SUMMARY"` with no category (direct upload)
- Apps Script now handles cases where category is optional

Verify that:
- Backend logs show correct folder paths: "Ship Name/Crew Records" and "SUMMARY"
- No nested subcategories are created
- File uploads complete successfully
- Folder structure matches user requirements exactly
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
from urllib.parse import urlparse
import base64

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://crew-doc-manager.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class PassportWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for passport workflow testing
        self.passport_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'ship_available_for_testing': False,
            
            # Passport upload endpoint
            'passport_upload_endpoint_accessible': False,
            'passport_file_upload_successful': False,
            'multipart_form_data_accepted': False,
            
            # Folder structure verification
            'passport_folder_path_correct': False,
            'summary_folder_path_correct': False,
            'no_nested_subcategories_created': False,
            'crew_records_category_only': False,
            'summary_direct_upload': False,
            
            # Backend processing
            'document_ai_processing_successful': False,
            'field_extraction_working': False,
            'date_standardization_working': False,
            'dual_apps_script_processing': False,
            
            # File upload verification
            'passport_file_uploaded_to_drive': False,
            'summary_file_uploaded_to_drive': False,
            'file_upload_completion_successful': False,
            'google_drive_file_ids_returned': False,
            
            # Backend logs verification
            'backend_logs_show_correct_paths': False,
            'no_crew_list_subfolder_in_logs': False,
            'no_documents_subfolder_in_logs': False,
            'simplified_folder_structure_confirmed': False,
        }
        
        # Store test data
        self.test_ship_name = None
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
                
                self.passport_tests['authentication_successful'] = True
                if self.current_user.get('company'):
                    self.passport_tests['user_company_identified'] = True
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
    
    def get_test_ship(self):
        """Get a ship for testing"""
        try:
            self.log("🚢 Getting test ship for passport upload...")
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ships = response.json()
                if ships:
                    # Use first available ship
                    test_ship = ships[0]
                    self.test_ship_name = test_ship.get('name')
                    self.log(f"✅ Using test ship: {self.test_ship_name}")
                    self.passport_tests['ship_available_for_testing'] = True
                    return self.test_ship_name
                else:
                    self.log("❌ No ships available for testing")
                    return None
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error getting test ship: {str(e)}", "ERROR")
            return None
    
    def create_test_passport_file(self):
        """Create a test passport file for upload"""
        try:
            # Create a simple test PDF content (minimal PDF structure)
            pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(TEST PASSPORT) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
            
            return pdf_content
            
        except Exception as e:
            self.log(f"❌ Error creating test passport file: {str(e)}", "ERROR")
            return None
    
    def test_passport_upload_endpoint(self):
        """Test POST /api/crew/analyze-passport endpoint"""
        try:
            self.log("📄 Testing POST /api/crew/analyze-passport endpoint...")
            
            if not self.test_ship_name:
                self.log("❌ No test ship available")
                return False
            
            # Create test passport file
            passport_content = self.create_test_passport_file()
            if not passport_content:
                self.log("❌ Failed to create test passport file")
                return False
            
            # Prepare multipart form data
            files = {
                'passport_file': ('test_passport_simplified_structure.pdf', passport_content, 'application/pdf')
            }
            
            data = {
                'ship_name': self.test_ship_name
            }
            
            endpoint = f"{BACKEND_URL}/crew/analyze-passport"
            self.log(f"   POST {endpoint}")
            self.log(f"   Ship name: {self.test_ship_name}")
            self.log(f"   File: test_passport_simplified_structure.pdf")
            
            # Make the request
            response = requests.post(
                endpoint, 
                files=files, 
                data=data, 
                headers=self.get_headers(), 
                timeout=120  # Longer timeout for file processing
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.passport_tests['passport_upload_endpoint_accessible'] = True
                self.passport_tests['multipart_form_data_accepted'] = True
                self.log("✅ Passport upload endpoint accessible")
                
                try:
                    response_data = response.json()
                    self.log(f"   Response keys: {list(response_data.keys())}")
                    
                    # Check if upload was successful
                    if response_data.get('success'):
                        self.passport_tests['passport_file_upload_successful'] = True
                        self.log("✅ Passport file upload successful")
                        
                        # Check for extracted data
                        if 'analysis' in response_data:
                            self.passport_tests['field_extraction_working'] = True
                            self.log("✅ Field extraction working")
                            
                            analysis = response_data['analysis']
                            self.log(f"   Extracted fields: {list(analysis.keys()) if isinstance(analysis, dict) else 'N/A'}")
                        
                        # Check for files data
                        if 'files' in response_data:
                            files_data = response_data['files']
                            if files_data:
                                self.passport_tests['file_upload_completion_successful'] = True
                                self.log("✅ File upload completion successful")
                                
                                # Check for Google Drive file IDs
                                if any('file_id' in str(files_data).lower() for file_data in files_data if file_data):
                                    self.passport_tests['google_drive_file_ids_returned'] = True
                                    self.log("✅ Google Drive file IDs returned")
                        
                        # Check processing method
                        processing_method = response_data.get('processing_method', '')
                        if 'dual' in processing_method.lower():
                            self.passport_tests['dual_apps_script_processing'] = True
                            self.log("✅ Dual Apps Script processing confirmed")
                        
                        return response_data
                    else:
                        self.log(f"❌ Upload failed: {response_data.get('message', 'Unknown error')}")
                        if 'error' in response_data:
                            self.log(f"   Error details: {response_data['error']}")
                        return None
                        
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return None
            else:
                self.log(f"   ❌ Passport upload endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing passport upload endpoint: {str(e)}", "ERROR")
            traceback.print_exc()
            return None
    
    def check_backend_logs_for_folder_structure(self):
        """Check backend logs for correct folder structure"""
        try:
            self.log("📋 Checking backend logs for folder structure...")
            
            # Get recent backend logs
            try:
                with open('/var/log/supervisor/backend.out.log', 'r') as f:
                    recent_logs = f.readlines()[-100:]  # Get last 100 lines
            except:
                try:
                    with open('/var/log/supervisor/backend.err.log', 'r') as f:
                        recent_logs = f.readlines()[-100:]
                except:
                    self.log("⚠️ Could not access backend logs")
                    return False
            
            log_content = ''.join(recent_logs)
            self.log(f"   Analyzing {len(recent_logs)} recent log lines...")
            
            # Check for correct folder paths
            expected_passport_path = f"{self.test_ship_name}/Crew Records"
            expected_summary_path = "SUMMARY"
            
            # Look for passport folder path
            if expected_passport_path in log_content:
                self.passport_tests['passport_folder_path_correct'] = True
                self.log(f"✅ Correct passport folder path found: {expected_passport_path}")
            else:
                self.log(f"❌ Expected passport folder path not found: {expected_passport_path}")
            
            # Look for summary folder path
            if expected_summary_path in log_content and "SUMMARY/" in log_content:
                self.passport_tests['summary_folder_path_correct'] = True
                self.log(f"✅ Correct summary folder path found: {expected_summary_path}")
            else:
                self.log(f"❌ Expected summary folder path not found: {expected_summary_path}")
            
            # Check that old nested structure is NOT present
            old_crew_list_path = f"{self.test_ship_name}/Crew Records/Crew List"
            old_documents_path = "SUMMARY/Documents"
            
            if old_crew_list_path not in log_content:
                self.passport_tests['no_crew_list_subfolder_in_logs'] = True
                self.log("✅ No 'Crew List' subfolder found in logs (correct)")
            else:
                self.log("❌ Old 'Crew List' subfolder structure found in logs")
            
            if old_documents_path not in log_content:
                self.passport_tests['no_documents_subfolder_in_logs'] = True
                self.log("✅ No 'Documents' subfolder found in logs (correct)")
            else:
                self.log("❌ Old 'Documents' subfolder structure found in logs")
            
            # Check for category usage
            if 'category: "Crew Records"' in log_content or '"category":"Crew Records"' in log_content:
                self.passport_tests['crew_records_category_only'] = True
                self.log("✅ 'Crew Records' category usage confirmed")
            
            # Check for direct SUMMARY upload (no category)
            if 'ship_name: "SUMMARY"' in log_content or '"ship_name":"SUMMARY"' in log_content:
                self.passport_tests['summary_direct_upload'] = True
                self.log("✅ Direct SUMMARY upload confirmed")
            
            # Overall folder structure verification
            if (self.passport_tests['passport_folder_path_correct'] and 
                self.passport_tests['summary_folder_path_correct'] and
                self.passport_tests['no_crew_list_subfolder_in_logs'] and
                self.passport_tests['no_documents_subfolder_in_logs']):
                self.passport_tests['simplified_folder_structure_confirmed'] = True
                self.passport_tests['backend_logs_show_correct_paths'] = True
                self.passport_tests['no_nested_subcategories_created'] = True
                self.log("✅ Simplified folder structure confirmed in backend logs")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def verify_document_ai_processing(self, response_data):
        """Verify Document AI processing is working"""
        try:
            self.log("🤖 Verifying Document AI processing...")
            
            if not response_data:
                return False
            
            # Check for AI processing indicators
            processing_method = response_data.get('processing_method', '')
            if 'document_ai' in processing_method.lower() or 'ai' in processing_method.lower():
                self.passport_tests['document_ai_processing_successful'] = True
                self.log("✅ Document AI processing confirmed")
            
            # Check for analysis data
            analysis = response_data.get('analysis', {})
            if analysis and isinstance(analysis, dict):
                # Check for typical passport fields
                passport_fields = ['full_name', 'passport_number', 'date_of_birth', 'nationality']
                found_fields = [field for field in passport_fields if field in analysis]
                
                if found_fields:
                    self.passport_tests['field_extraction_working'] = True
                    self.log(f"✅ Field extraction working - found: {found_fields}")
                
                # Check for date standardization
                date_fields = ['date_of_birth', 'issue_date', 'expiry_date']
                for field in date_fields:
                    if field in analysis:
                        date_value = analysis[field]
                        # Check if date is in DD/MM/YYYY format (standardized)
                        if isinstance(date_value, str) and re.match(r'\d{2}/\d{2}/\d{4}', date_value):
                            self.passport_tests['date_standardization_working'] = True
                            self.log(f"✅ Date standardization working - {field}: {date_value}")
                            break
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error verifying Document AI processing: {str(e)}", "ERROR")
            return False
    
    def verify_file_uploads(self, response_data):
        """Verify file uploads to Google Drive"""
        try:
            self.log("📁 Verifying file uploads to Google Drive...")
            
            if not response_data:
                return False
            
            files_data = response_data.get('files', [])
            if not files_data:
                self.log("❌ No files data in response")
                return False
            
            passport_file_uploaded = False
            summary_file_uploaded = False
            
            for file_info in files_data:
                if not file_info:
                    continue
                    
                file_name = file_info.get('filename', '')
                file_path = file_info.get('folder_path', '')
                file_id = file_info.get('file_id', '')
                
                self.log(f"   File: {file_name}")
                self.log(f"   Path: {file_path}")
                self.log(f"   ID: {file_id}")
                
                # Check passport file
                if 'passport' in file_name.lower() and file_id:
                    passport_file_uploaded = True
                    # Verify correct folder structure
                    expected_path = f"{self.test_ship_name}/Crew Records"
                    if expected_path in file_path:
                        self.log(f"   ✅ Passport file uploaded to correct path: {file_path}")
                    else:
                        self.log(f"   ❌ Passport file path incorrect. Expected: {expected_path}, Got: {file_path}")
                
                # Check summary file
                if 'summary' in file_name.lower() and file_id:
                    summary_file_uploaded = True
                    # Verify correct folder structure
                    if file_path == "SUMMARY" or file_path.startswith("SUMMARY/"):
                        self.log(f"   ✅ Summary file uploaded to correct path: {file_path}")
                    else:
                        self.log(f"   ❌ Summary file path incorrect. Expected: SUMMARY, Got: {file_path}")
            
            if passport_file_uploaded:
                self.passport_tests['passport_file_uploaded_to_drive'] = True
                self.log("✅ Passport file uploaded to Google Drive")
            
            if summary_file_uploaded:
                self.passport_tests['summary_file_uploaded_to_drive'] = True
                self.log("✅ Summary file uploaded to Google Drive")
            
            return passport_file_uploaded and summary_file_uploaded
            
        except Exception as e:
            self.log(f"❌ Error verifying file uploads: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_passport_workflow_test(self):
        """Run comprehensive test of passport workflow with simplified folder structure"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE PASSPORT WORKFLOW TEST")
            self.log("🎯 FOCUS: Testing simplified folder structure changes")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Get test ship
            self.log("\nSTEP 2: Getting test ship")
            if not self.get_test_ship():
                self.log("❌ CRITICAL: No test ship available - cannot proceed")
                return False
            
            # Step 3: Test passport upload endpoint
            self.log("\nSTEP 3: Testing passport upload endpoint")
            response_data = self.test_passport_upload_endpoint()
            
            # Step 4: Verify Document AI processing
            self.log("\nSTEP 4: Verifying Document AI processing")
            self.verify_document_ai_processing(response_data)
            
            # Step 5: Verify file uploads
            self.log("\nSTEP 5: Verifying file uploads to Google Drive")
            self.verify_file_uploads(response_data)
            
            # Step 6: Check backend logs for folder structure
            self.log("\nSTEP 6: Checking backend logs for folder structure")
            self.check_backend_logs_for_folder_structure()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE PASSPORT WORKFLOW TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 PASSPORT WORKFLOW TEST SUMMARY")
            self.log("🎯 SIMPLIFIED FOLDER STRUCTURE VERIFICATION")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.passport_tests)
            passed_tests = sum(1 for result in self.passport_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('ship_available_for_testing', 'Test ship available'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Passport Upload Results
            self.log("\n📄 PASSPORT UPLOAD ENDPOINT:")
            upload_tests = [
                ('passport_upload_endpoint_accessible', 'Endpoint accessible'),
                ('multipart_form_data_accepted', 'Multipart form data accepted'),
                ('passport_file_upload_successful', 'File upload successful'),
            ]
            
            for test_key, description in upload_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Folder Structure Results (CRITICAL)
            self.log("\n📁 FOLDER STRUCTURE VERIFICATION (CRITICAL):")
            folder_tests = [
                ('passport_folder_path_correct', 'Passport folder: [Ship Name]/Crew Records'),
                ('summary_folder_path_correct', 'Summary folder: SUMMARY'),
                ('no_crew_list_subfolder_in_logs', 'No Crew List subfolder (removed)'),
                ('no_documents_subfolder_in_logs', 'No Documents subfolder (removed)'),
                ('crew_records_category_only', 'Uses category: "Crew Records" only'),
                ('summary_direct_upload', 'Summary uses ship_name: "SUMMARY"'),
                ('no_nested_subcategories_created', 'No nested subcategories'),
                ('simplified_folder_structure_confirmed', 'Simplified structure confirmed'),
            ]
            
            for test_key, description in folder_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Processing Results
            self.log("\n🤖 DOCUMENT PROCESSING:")
            processing_tests = [
                ('document_ai_processing_successful', 'Document AI processing'),
                ('field_extraction_working', 'Field extraction'),
                ('date_standardization_working', 'Date standardization'),
                ('dual_apps_script_processing', 'Dual Apps Script processing'),
            ]
            
            for test_key, description in processing_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # File Upload Results
            self.log("\n📤 GOOGLE DRIVE FILE UPLOADS:")
            file_tests = [
                ('passport_file_uploaded_to_drive', 'Passport file uploaded'),
                ('summary_file_uploaded_to_drive', 'Summary file uploaded'),
                ('file_upload_completion_successful', 'Upload completion successful'),
                ('google_drive_file_ids_returned', 'Google Drive file IDs returned'),
            ]
            
            for test_key, description in file_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Results
            self.log("\n📋 BACKEND LOGS VERIFICATION:")
            log_tests = [
                ('backend_logs_show_correct_paths', 'Backend logs show correct paths'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Assessment
            self.log("\n🎯 CRITICAL FOLDER STRUCTURE ASSESSMENT:")
            
            critical_folder_tests = [
                'passport_folder_path_correct', 'summary_folder_path_correct',
                'no_crew_list_subfolder_in_logs', 'no_documents_subfolder_in_logs',
                'simplified_folder_structure_confirmed'
            ]
            
            critical_passed = sum(1 for test_key in critical_folder_tests if self.passport_tests.get(test_key, False))
            
            if critical_passed == len(critical_folder_tests):
                self.log("   ✅ SIMPLIFIED FOLDER STRUCTURE WORKING CORRECTLY")
                self.log("   ✅ Passport files: [Ship Name]/Crew Records (no Crew List subfolder)")
                self.log("   ✅ Summary files: SUMMARY (no Documents subfolder)")
                self.log("   ✅ No nested subcategories created")
            else:
                self.log("   ❌ FOLDER STRUCTURE ISSUES DETECTED")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_folder_tests)} critical tests passed")
            
            # Overall Assessment
            self.log("\n🏆 OVERALL ASSESSMENT:")
            
            if success_rate >= 90:
                self.log(f"   ✅ EXCELLENT: {success_rate:.1f}% - Simplified folder structure working perfectly")
            elif success_rate >= 75:
                self.log(f"   ✅ GOOD: {success_rate:.1f}% - Most functionality working, minor issues")
            elif success_rate >= 50:
                self.log(f"   ⚠️ PARTIAL: {success_rate:.1f}% - Some functionality working, needs attention")
            else:
                self.log(f"   ❌ POOR: {success_rate:.1f}% - Major issues with folder structure implementation")
            
            # Specific Review Request Verification
            self.log("\n📋 REVIEW REQUEST REQUIREMENTS VERIFICATION:")
            
            requirements_met = []
            requirements_failed = []
            
            # Requirement 1: Passport file path
            if self.passport_tests.get('passport_folder_path_correct'):
                requirements_met.append("✅ Passport file: [Ship Name]/Crew Records/[filename].jpg")
            else:
                requirements_failed.append("❌ Passport file: [Ship Name]/Crew Records/[filename].jpg")
            
            # Requirement 2: Summary file path
            if self.passport_tests.get('summary_folder_path_correct'):
                requirements_met.append("✅ Summary file: SUMMARY/[filename]_Summary.txt")
            else:
                requirements_failed.append("❌ Summary file: SUMMARY/[filename]_Summary.txt")
            
            # Requirement 3: Category usage
            if self.passport_tests.get('crew_records_category_only'):
                requirements_met.append("✅ Passport upload uses only category: 'Crew Records'")
            else:
                requirements_failed.append("❌ Passport upload uses only category: 'Crew Records'")
            
            # Requirement 4: Summary direct upload
            if self.passport_tests.get('summary_direct_upload'):
                requirements_met.append("✅ Summary upload uses ship_name: 'SUMMARY' with no category")
            else:
                requirements_failed.append("❌ Summary upload uses ship_name: 'SUMMARY' with no category")
            
            # Requirement 5: No nested subcategories
            if self.passport_tests.get('no_nested_subcategories_created'):
                requirements_met.append("✅ No nested subcategories are created")
            else:
                requirements_failed.append("❌ No nested subcategories are created")
            
            # Requirement 6: Backend logs show correct paths
            if self.passport_tests.get('backend_logs_show_correct_paths'):
                requirements_met.append("✅ Backend logs show correct folder paths")
            else:
                requirements_failed.append("❌ Backend logs show correct folder paths")
            
            for req in requirements_met:
                self.log(f"   {req}")
            
            for req in requirements_failed:
                self.log(f"   {req}")
            
            if len(requirements_failed) == 0:
                self.log("\n🎉 ALL REVIEW REQUEST REQUIREMENTS MET SUCCESSFULLY!")
            else:
                self.log(f"\n⚠️ {len(requirements_failed)} REVIEW REQUEST REQUIREMENTS NOT MET")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the passport workflow tests"""
    tester = PassportWorkflowTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_passport_workflow_test()
        
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
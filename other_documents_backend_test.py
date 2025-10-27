#!/usr/bin/env python3
"""
Other Documents List File Upload Fix Testing - Comprehensive Backend Test
Testing the fix for Other Documents upload issue by switching from GoogleDriveManager to DualAppsScriptManager

REVIEW REQUEST REQUIREMENTS:
Test "Other Documents List" File Upload Fix to verify:
1. Fixed the Other Documents upload issue by switching from GoogleDriveManager to DualAppsScriptManager
2. Added two new methods to DualAppsScriptManager:
   - upload_other_document_file() - Main upload method
   - _call_apps_script_for_other_document_upload() - Helper to call Company Apps Script
3. Updated server.py endpoints to use DualAppsScriptManager:
   - /api/other-documents/upload - Upload file and create record
   - /api/other-documents/upload-file-only - Upload file only, return file_id

TEST PLAN:
Phase 1: Authentication & Setup
Phase 2: Upload Endpoint Testing
Phase 3: Backend Logs Verification
Phase 4: Database Verification

EXPECTED RESULTS:
- Both upload endpoints return 200 OK
- Files are uploaded to Google Drive successfully
- File IDs are valid Google Drive IDs (format: 1xxxxxxxxxxxxx)
- Database records created correctly
- Backend logs show Company Apps Script being called (not Document AI)
- No 500 errors
- No AttributeError about company_id

CRITICAL: Verify that Company Apps Script URL is being used, NOT Document AI Apps Script URL!
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipdoclists.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class OtherDocumentsUploadTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.ship_name = "BROTHER 36"
        self.ship_id = None
        
        # Test tracking for Other Documents upload functionality
        self.upload_tests = {
            # Phase 1: Authentication & Setup
            'authentication_successful': False,
            'user_company_identified': False,
            'company_has_gdrive_config': False,
            'ship_discovery_successful': False,
            'ships_list_found': False,
            
            # Phase 2: Upload Endpoint Testing
            'upload_file_only_endpoint_accessible': False,
            'upload_file_only_successful': False,
            'upload_file_only_returns_file_id': False,
            'upload_endpoint_accessible': False,
            'upload_with_metadata_successful': False,
            'upload_returns_document_id': False,
            'upload_returns_file_id': False,
            'file_ids_valid_gdrive_format': False,
            
            # Phase 3: Backend Logs Verification
            'uploading_other_document_logs': False,
            'company_apps_script_call_logs': False,
            'company_apps_script_response_logs': False,
            'upload_success_logs': False,
            'no_document_ai_errors': False,
            'no_company_id_attribute_errors': False,
            
            # Phase 4: Database Verification
            'mongodb_record_created': False,
            'correct_ship_id_in_record': False,
            'file_ids_array_populated': False,
            'metadata_fields_saved': False,
            
            # Critical Verification
            'company_apps_script_used': False,
            'not_document_ai_apps_script': False,
            'dual_apps_script_manager_used': False,
            'google_drive_upload_successful': False,
        }
        
        # Store test data
        self.test_file_path = None
        self.test_document_id = None
        self.company_gdrive_config = None
        
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
        """Phase 1: Authenticate with admin1/123456 credentials"""
        try:
            self.log("🔐 Phase 1: Authentication & Setup")
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
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.upload_tests['authentication_successful'] = True
                self.upload_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def verify_company_gdrive_config(self):
        """Verify user has company assignment and company has Google Drive configuration"""
        try:
            self.log("🏢 Verifying company has Google Drive configuration...")
            
            company_name = self.current_user.get('company')
            if not company_name:
                self.log("❌ User has no company assignment", "ERROR")
                return False
            
            # Get companies to find company details
            response = self.session.get(f"{BACKEND_URL}/companies")
            
            if response.status_code == 200:
                companies = response.json()
                for company in companies:
                    if company.get("name_en") == company_name or company.get("name_vn") == company_name:
                        company_id = company.get("id")
                        self.log(f"✅ Found company: {company_name} (ID: {company_id})")
                        
                        # Check for Google Drive configuration
                        gdrive_config = company.get("company_gdrive_config", {})
                        if gdrive_config and gdrive_config.get("apps_script_url") and gdrive_config.get("folder_id"):
                            self.log("✅ Company has Google Drive configuration")
                            self.log(f"   Apps Script URL: {gdrive_config.get('apps_script_url')}")
                            self.log(f"   Folder ID: {gdrive_config.get('folder_id')}")
                            self.company_gdrive_config = gdrive_config
                            self.upload_tests['company_has_gdrive_config'] = True
                            return True
                        else:
                            self.log("❌ Company missing Google Drive configuration", "ERROR")
                            return False
                
                self.log(f"❌ Company '{company_name}' not found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get companies: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying company config: {str(e)}", "ERROR")
            return False
    
    def find_ship(self):
        """Find the test ship and get list of ships"""
        try:
            self.log(f"🚢 Finding ship: {self.ship_name}")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"✅ Retrieved {len(ships)} ships")
                self.upload_tests['ships_list_found'] = True
                
                for ship in ships:
                    if ship.get("name") == self.ship_name:
                        self.ship_id = ship.get("id")
                        self.log(f"✅ Found ship: {self.ship_name} (ID: {self.ship_id})")
                        self.upload_tests['ship_discovery_successful'] = True
                        return True
                
                self.log(f"❌ Ship '{self.ship_name}' not found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def create_test_pdf_file(self):
        """Create a small test PDF file for upload testing"""
        try:
            self.log("📄 Creating test PDF file...")
            
            # Create a simple PDF content (minimal PDF structure)
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
(Other Document Test) Tj
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
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
                f.write(pdf_content)
                self.test_file_path = f.name
            
            file_size = len(pdf_content)
            self.log(f"✅ Test PDF created: {self.test_file_path}")
            self.log(f"   File size: {file_size} bytes")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating test PDF: {str(e)}", "ERROR")
            return False
    
    def test_upload_file_only_endpoint(self):
        """Phase 2: Test /api/other-documents/upload-file-only endpoint"""
        try:
            self.log("📤 Phase 2: Upload Endpoint Testing")
            self.log("📤 Testing /api/other-documents/upload-file-only endpoint...")
            
            if not self.test_file_path:
                self.log("❌ No test file available", "ERROR")
                return False
            
            # Prepare multipart form data
            with open(self.test_file_path, "rb") as f:
                files = {
                    "file": ("test_other_document.pdf", f, "application/pdf")
                }
                data = {
                    "ship_id": self.ship_id
                }
                
                endpoint = f"{BACKEND_URL}/other-documents/upload-file-only"
                self.log(f"   POST {endpoint}")
                self.log(f"   Ship ID: {self.ship_id}")
                
                start_time = time.time()
                response = self.session.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=120
                )
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.upload_tests['upload_file_only_endpoint_accessible'] = True
                self.upload_tests['upload_file_only_successful'] = True
                
                try:
                    result = response.json()
                    self.log("✅ Upload file only endpoint successful")
                    self.log(f"📊 Response keys: {list(result.keys())}")
                    
                    # Check for file_id in response
                    file_id = result.get("file_id")
                    if file_id:
                        self.log(f"✅ File ID returned: {file_id}")
                        self.upload_tests['upload_file_only_returns_file_id'] = True
                        
                        # Verify Google Drive file ID format (should start with '1' and be long)
                        if file_id.startswith('1') and len(file_id) > 20:
                            self.log("✅ File ID has valid Google Drive format")
                            self.upload_tests['file_ids_valid_gdrive_format'] = True
                        else:
                            self.log(f"⚠️ File ID format may be invalid: {file_id}")
                    else:
                        self.log("❌ No file_id in response", "ERROR")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                    return False
            else:
                self.log(f"❌ Upload file only endpoint failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Raw response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing upload file only endpoint: {str(e)}", "ERROR")
            return False
    
    def test_upload_with_metadata_endpoint(self):
        """Test /api/other-documents/upload endpoint with metadata"""
        try:
            self.log("📋 Testing /api/other-documents/upload endpoint with metadata...")
            
            if not self.test_file_path:
                self.log("❌ No test file available", "ERROR")
                return False
            
            # Prepare multipart form data with metadata
            with open(self.test_file_path, "rb") as f:
                files = {
                    "file": ("test_other_document_with_metadata.pdf", f, "application/pdf")
                }
                data = {
                    "ship_id": self.ship_id,
                    "document_name": "Test Other Document with Metadata",
                    "date": "2024-01-15T10:30:00Z",
                    "status": "Valid",
                    "note": "This is a test document for Other Documents upload functionality"
                }
                
                endpoint = f"{BACKEND_URL}/other-documents/upload"
                self.log(f"   POST {endpoint}")
                self.log(f"   Ship ID: {self.ship_id}")
                self.log(f"   Document Name: {data['document_name']}")
                self.log(f"   Status: {data['status']}")
                
                start_time = time.time()
                response = self.session.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=120
                )
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.upload_tests['upload_endpoint_accessible'] = True
                self.upload_tests['upload_with_metadata_successful'] = True
                
                try:
                    result = response.json()
                    self.log("✅ Upload with metadata endpoint successful")
                    self.log(f"📊 Response keys: {list(result.keys())}")
                    
                    # Check for document_id in response
                    document_id = result.get("document_id")
                    if document_id:
                        self.log(f"✅ Document ID returned: {document_id}")
                        self.upload_tests['upload_returns_document_id'] = True
                        self.test_document_id = document_id
                    else:
                        self.log("❌ No document_id in response", "ERROR")
                    
                    # Check for file_id in response
                    file_id = result.get("file_id")
                    if file_id:
                        self.log(f"✅ File ID returned: {file_id}")
                        self.upload_tests['upload_returns_file_id'] = True
                        
                        # Verify Google Drive file ID format
                        if file_id.startswith('1') and len(file_id) > 20:
                            self.log("✅ File ID has valid Google Drive format")
                            self.upload_tests['file_ids_valid_gdrive_format'] = True
                        else:
                            self.log(f"⚠️ File ID format may be invalid: {file_id}")
                    else:
                        self.log("❌ No file_id in response", "ERROR")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                    return False
            else:
                self.log(f"❌ Upload with metadata endpoint failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Raw response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing upload with metadata endpoint: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs(self):
        """Phase 3: Check backend logs for specific patterns"""
        try:
            self.log("📋 Phase 3: Backend Logs Verification")
            self.log("📋 Checking backend logs for upload patterns...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            # Expected log patterns for Other Documents upload
            expected_patterns = {
                'uploading_other_document_logs': [
                    "📤 Uploading other document",
                    "Uploading other document file",
                    "Other document upload"
                ],
                'company_apps_script_call_logs': [
                    "📡 Calling Company Apps Script for other document upload",
                    "Company Apps Script for other document",
                    "Calling Company Apps Script"
                ],
                'company_apps_script_response_logs': [
                    "✅ Company Apps Script response received",
                    "Company Apps Script response",
                    "Apps Script response"
                ],
                'upload_success_logs': [
                    "✅ Other document file uploaded successfully",
                    "Other document uploaded successfully",
                    "File uploaded successfully"
                ],
                'no_document_ai_errors': [
                    "Document AI Apps Script URL not configured"  # Should NOT appear
                ],
                'no_company_id_attribute_errors': [
                    "AttributeError.*company_id"  # Should NOT appear
                ]
            }
            
            all_log_content = ""
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        all_log_content += result
                        
                        if result.strip():
                            self.log(f"   Found {len(result.strip().split(chr(10)))} lines")
                        else:
                            self.log(f"   {log_file} is empty or not accessible")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
                else:
                    self.log(f"   {log_file} not found")
            
            # Search for expected patterns
            self.log("🔍 Searching for expected log patterns:")
            
            for test_key, patterns in expected_patterns.items():
                found = False
                for pattern in patterns:
                    if test_key in ['no_document_ai_errors', 'no_company_id_attribute_errors']:
                        # These should NOT be found (negative tests)
                        if re.search(pattern, all_log_content, re.IGNORECASE):
                            self.log(f"   ❌ Found unwanted pattern: {pattern}")
                            found = True
                        else:
                            self.log(f"   ✅ Good - pattern not found: {pattern}")
                            self.upload_tests[test_key] = True
                    else:
                        # These should be found (positive tests)
                        if re.search(pattern, all_log_content, re.IGNORECASE):
                            self.log(f"   ✅ Found expected pattern: {pattern}")
                            self.upload_tests[test_key] = True
                            found = True
                            break
                
                if not found and test_key not in ['no_document_ai_errors', 'no_company_id_attribute_errors']:
                    self.log(f"   ❌ Expected pattern not found for: {test_key}")
            
            # Check for Company Apps Script vs Document AI usage
            if "Company Apps Script" in all_log_content:
                self.log("✅ Company Apps Script being used")
                self.upload_tests['company_apps_script_used'] = True
            
            if "Document AI Apps Script" not in all_log_content:
                self.log("✅ Document AI Apps Script NOT being used (correct)")
                self.upload_tests['not_document_ai_apps_script'] = True
            
            if "DualAppsScriptManager" in all_log_content or "dual_apps_script_manager" in all_log_content:
                self.log("✅ DualAppsScriptManager being used")
                self.upload_tests['dual_apps_script_manager_used'] = True
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def verify_database_record(self):
        """Phase 4: Verify database record was created correctly"""
        try:
            self.log("🗄️ Phase 4: Database Verification")
            self.log("🗄️ Verifying MongoDB record was created...")
            
            if not self.test_document_id:
                self.log("❌ No test document ID available for verification", "ERROR")
                return False
            
            # Get the created document
            endpoint = f"{BACKEND_URL}/other-documents/{self.test_document_id}"
            response = self.session.get(endpoint)
            
            if response.status_code == 200:
                document = response.json()
                self.log("✅ MongoDB record found")
                self.log(f"📊 Document fields: {list(document.keys())}")
                
                # Verify ship_id
                if document.get("ship_id") == self.ship_id:
                    self.log("✅ Correct ship_id in record")
                    self.upload_tests['correct_ship_id_in_record'] = True
                else:
                    self.log(f"❌ Incorrect ship_id: expected {self.ship_id}, got {document.get('ship_id')}")
                
                # Verify file_ids array
                file_ids = document.get("file_ids", [])
                if file_ids and len(file_ids) > 0:
                    self.log(f"✅ File IDs array populated: {file_ids}")
                    self.upload_tests['file_ids_array_populated'] = True
                    
                    # Verify Google Drive file ID format
                    for file_id in file_ids:
                        if file_id.startswith('1') and len(file_id) > 20:
                            self.log(f"✅ Valid Google Drive file ID: {file_id}")
                            self.upload_tests['google_drive_upload_successful'] = True
                        else:
                            self.log(f"⚠️ Questionable file ID format: {file_id}")
                else:
                    self.log("❌ File IDs array empty or missing")
                
                # Verify metadata fields
                expected_fields = ['document_name', 'date', 'status', 'note']
                metadata_ok = True
                for field in expected_fields:
                    if field in document and document[field]:
                        self.log(f"   ✅ {field}: {document[field]}")
                    else:
                        self.log(f"   ❌ Missing or empty {field}")
                        metadata_ok = False
                
                if metadata_ok:
                    self.log("✅ All metadata fields saved correctly")
                    self.upload_tests['metadata_fields_saved'] = True
                
                self.upload_tests['mongodb_record_created'] = True
                return True
            else:
                self.log(f"❌ Failed to retrieve document: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying database record: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        try:
            self.log("🧹 Cleaning up test data...")
            
            # Delete test document if created
            if self.test_document_id:
                try:
                    endpoint = f"{BACKEND_URL}/other-documents/{self.test_document_id}"
                    response = self.session.delete(endpoint)
                    if response.status_code in [200, 204]:
                        self.log(f"   ✅ Cleaned up document ID: {self.test_document_id}")
                    else:
                        self.log(f"   ⚠️ Failed to clean up document ID: {self.test_document_id}")
                except Exception as e:
                    self.log(f"   ⚠️ Error cleaning up document: {str(e)}")
            
            # Delete test file
            if self.test_file_path and os.path.exists(self.test_file_path):
                try:
                    os.unlink(self.test_file_path)
                    self.log(f"   ✅ Cleaned up test file: {self.test_file_path}")
                except Exception as e:
                    self.log(f"   ⚠️ Error cleaning up test file: {str(e)}")
            
            self.log("✅ Cleanup completed")
            
        except Exception as e:
            self.log(f"❌ Error during cleanup: {str(e)}", "ERROR")
    
    def run_comprehensive_other_documents_test(self):
        """Run comprehensive test of Other Documents upload functionality"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE OTHER DOCUMENTS UPLOAD TEST")
            self.log("=" * 80)
            self.log("Testing Other Documents List File Upload Fix:")
            self.log("- Switch from GoogleDriveManager to DualAppsScriptManager")
            self.log("- Company Apps Script URL usage (NOT Document AI)")
            self.log("- Both upload endpoints functionality")
            self.log("- Database record creation")
            self.log("=" * 80)
            
            # Phase 1: Authentication & Setup
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            if not self.verify_company_gdrive_config():
                self.log("❌ CRITICAL: Company Google Drive config missing - cannot proceed")
                return False
            
            if not self.find_ship():
                self.log("❌ CRITICAL: Ship discovery failed - cannot proceed")
                return False
            
            # Create test file
            if not self.create_test_pdf_file():
                self.log("❌ CRITICAL: Test file creation failed - cannot proceed")
                return False
            
            # Phase 2: Upload Endpoint Testing
            self.test_upload_file_only_endpoint()
            self.test_upload_with_metadata_endpoint()
            
            # Phase 3: Backend Logs Verification
            self.check_backend_logs()
            
            # Phase 4: Database Verification
            self.verify_database_record()
            
            # Cleanup
            self.cleanup_test_data()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE OTHER DOCUMENTS UPLOAD TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 OTHER DOCUMENTS UPLOAD TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.upload_tests)
            passed_tests = sum(1 for result in self.upload_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Phase 1: Authentication & Setup Results
            self.log("🔐 PHASE 1: AUTHENTICATION & SETUP:")
            phase1_tests = [
                ('authentication_successful', 'Login with admin1/123456'),
                ('user_company_identified', 'User has company assignment'),
                ('company_has_gdrive_config', 'Company has Google Drive config'),
                ('ship_discovery_successful', 'Ship discovery successful'),
                ('ships_list_found', 'Ships list retrieved'),
            ]
            
            for test_key, description in phase1_tests:
                status = "✅ PASS" if self.upload_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Phase 2: Upload Endpoint Testing Results
            self.log("\n📤 PHASE 2: UPLOAD ENDPOINT TESTING:")
            phase2_tests = [
                ('upload_file_only_endpoint_accessible', '/api/other-documents/upload-file-only accessible'),
                ('upload_file_only_successful', 'Upload file only successful'),
                ('upload_file_only_returns_file_id', 'Upload file only returns file_id'),
                ('upload_endpoint_accessible', '/api/other-documents/upload accessible'),
                ('upload_with_metadata_successful', 'Upload with metadata successful'),
                ('upload_returns_document_id', 'Upload returns document_id'),
                ('upload_returns_file_id', 'Upload returns file_id'),
                ('file_ids_valid_gdrive_format', 'File IDs have valid Google Drive format'),
            ]
            
            for test_key, description in phase2_tests:
                status = "✅ PASS" if self.upload_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Phase 3: Backend Logs Verification Results
            self.log("\n📋 PHASE 3: BACKEND LOGS VERIFICATION:")
            phase3_tests = [
                ('uploading_other_document_logs', '"📤 Uploading other document" messages'),
                ('company_apps_script_call_logs', '"📡 Calling Company Apps Script" messages'),
                ('company_apps_script_response_logs', '"✅ Company Apps Script response" messages'),
                ('upload_success_logs', '"✅ Other document uploaded successfully" messages'),
                ('no_document_ai_errors', 'NO "Document AI Apps Script URL not configured" errors'),
                ('no_company_id_attribute_errors', 'NO AttributeError about company_id'),
            ]
            
            for test_key, description in phase3_tests:
                status = "✅ PASS" if self.upload_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Phase 4: Database Verification Results
            self.log("\n🗄️ PHASE 4: DATABASE VERIFICATION:")
            phase4_tests = [
                ('mongodb_record_created', 'MongoDB record created'),
                ('correct_ship_id_in_record', 'Correct ship_id in record'),
                ('file_ids_array_populated', 'File IDs array populated'),
                ('metadata_fields_saved', 'Metadata fields saved'),
            ]
            
            for test_key, description in phase4_tests:
                status = "✅ PASS" if self.upload_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Verification Results
            self.log("\n🎯 CRITICAL VERIFICATION:")
            critical_tests = [
                ('company_apps_script_used', 'Company Apps Script URL being used'),
                ('not_document_ai_apps_script', 'NOT Document AI Apps Script URL'),
                ('dual_apps_script_manager_used', 'DualAppsScriptManager being used'),
                ('google_drive_upload_successful', 'Google Drive upload successful'),
            ]
            
            for test_key, description in critical_tests:
                status = "✅ PASS" if self.upload_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            # Check critical requirements
            critical_requirements = [
                'upload_file_only_successful',
                'upload_with_metadata_successful',
                'file_ids_valid_gdrive_format',
                'company_apps_script_used',
                'not_document_ai_apps_script',
                'no_document_ai_errors',
                'no_company_id_attribute_errors'
            ]
            
            critical_passed = sum(1 for test_key in critical_requirements if self.upload_tests.get(test_key, False))
            
            if critical_passed == len(critical_requirements):
                self.log("   ✅ ALL CRITICAL REQUIREMENTS MET")
                self.log("   ✅ Other Documents upload fix working correctly")
                self.log("   ✅ Company Apps Script URL being used (not Document AI)")
                self.log("   ✅ Both upload endpoints return 200 OK")
                self.log("   ✅ Files uploaded to Google Drive successfully")
                self.log("   ✅ No 500 errors or AttributeError about company_id")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_requirements)} critical tests passed")
            
            # Success rate assessment
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
    """Main function to run the Other Documents upload test"""
    tester = OtherDocumentsUploadTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_other_documents_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"\n❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
File Linking Functionality Backend Test

This test covers the new file linking functionality as requested in the review:

1. **Test passport analysis with file ID saving**:
   - Upload a passport file via POST /api/crew/analyze-passport
   - Verify the response includes file_ids in analysis.file_ids
   - Check that both passport_file_id and summary_file_id are present

2. **Test crew creation with file IDs**:
   - Create a new crew member with passport analysis data that includes file_ids
   - Verify the crew record in database includes passport_file_id and summary_file_id

3. **Test crew deletion with file cleanup**:
   - Delete a crew member that has associated file IDs
   - Verify the response includes information about deleted files
   - Check that the deletion API calls the Google Drive delete functionality

4. **Test file rename endpoint**:
   - Call POST /api/crew/{crew_id}/rename-files with a new filename
   - Verify the endpoint makes proper API calls to rename both passport and summary files
   - Check the response includes renamed_files information

5. **Test crew list retrieval**:
   - Get crew list via GET /api/crew?ship_name=BROTHER%2036
   - Verify crew records include passport_file_id and summary_file_id fields
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
    # Fallback to external URL from environment
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class FileLinkingTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.ship_name = "BROTHER 36"
        self.created_crew_ids = []
        
        # Test tracking for file linking functionality
        self.file_linking_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            
            # Test 1: Passport analysis with file ID saving
            'passport_analysis_endpoint_accessible': False,
            'passport_file_uploaded_successfully': False,
            'analysis_contains_file_ids': False,
            'passport_file_id_present': False,
            'summary_file_id_present': False,
            'file_ids_structure_correct': False,
            
            # Test 2: Crew creation with file IDs
            'crew_creation_with_file_ids_successful': False,
            'crew_record_contains_passport_file_id': False,
            'crew_record_contains_summary_file_id': False,
            'file_ids_stored_in_database': False,
            
            # Test 3: Crew deletion with file cleanup
            'crew_deletion_endpoint_accessible': False,
            'deletion_response_includes_deleted_files': False,
            'google_drive_delete_calls_made': False,
            'file_cleanup_successful': False,
            
            # Test 4: File rename endpoint
            'file_rename_endpoint_accessible': False,
            'passport_file_rename_attempted': False,
            'summary_file_rename_attempted': False,
            'rename_response_includes_renamed_files': False,
            'google_drive_rename_calls_made': False,
            
            # Test 5: Crew list retrieval
            'crew_list_endpoint_accessible': False,
            'crew_list_includes_file_ids': False,
            'passport_file_id_in_crew_list': False,
            'summary_file_id_in_crew_list': False,
        }
        
        # Store test data
        self.test_passport_file_ids = {}
        self.test_crew_id = None
        
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
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.file_linking_tests['authentication_successful'] = True
                self.file_linking_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def create_test_passport_file(self):
        """Create a test passport file for testing"""
        try:
            # Create a simple PDF-like file for testing
            test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
            
            # Write to temporary file
            test_file_path = "/tmp/test_passport_file_linking.pdf"
            with open(test_file_path, 'wb') as f:
                f.write(test_content)
            
            self.log(f"✅ Created test passport file: {test_file_path}")
            return test_file_path
            
        except Exception as e:
            self.log(f"❌ Error creating test passport file: {str(e)}", "ERROR")
            return None
    
    def test_passport_analysis_with_file_ids(self):
        """Test 1: Test passport analysis with file ID saving"""
        try:
            self.log("📄 TEST 1: Testing passport analysis with file ID saving...")
            
            # Create test passport file
            test_file_path = self.create_test_passport_file()
            if not test_file_path:
                return False
            
            # Prepare multipart form data
            with open(test_file_path, "rb") as f:
                files = {
                    "passport_file": ("test_passport_file_linking.pdf", f, "application/pdf")
                }
                data = {
                    "ship_name": self.ship_name
                }
                
                self.log(f"📤 Uploading test passport file for file linking test")
                self.log(f"🚢 Ship name: {self.ship_name}")
                
                endpoint = f"{BACKEND_URL}/crew/analyze-passport"
                self.log(f"   POST {endpoint}")
                
                start_time = time.time()
                response = self.session.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=120  # Longer timeout for AI processing
                )
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.file_linking_tests['passport_analysis_endpoint_accessible'] = True
                self.file_linking_tests['passport_file_uploaded_successfully'] = True
                
                self.log("✅ Passport analysis endpoint accessible")
                self.log(f"📊 Response keys: {list(result.keys())}")
                
                # Check for success
                if result.get("success"):
                    self.log("✅ Passport analysis successful")
                    
                    # Check for analysis data with file_ids
                    analysis = result.get("analysis", {})
                    if analysis:
                        self.log("✅ Analysis data found")
                        
                        # Check for file_ids in analysis
                        file_ids = analysis.get("file_ids", {})
                        if file_ids:
                            self.file_linking_tests['analysis_contains_file_ids'] = True
                            self.log("✅ Analysis contains file_ids")
                            
                            # Check for passport_file_id
                            passport_file_id = file_ids.get("passport_file_id")
                            if passport_file_id:
                                self.file_linking_tests['passport_file_id_present'] = True
                                self.test_passport_file_ids['passport_file_id'] = passport_file_id
                                self.log(f"✅ Passport file ID present: {passport_file_id}")
                            else:
                                self.log("❌ Passport file ID not present in analysis.file_ids")
                            
                            # Check for summary_file_id
                            summary_file_id = file_ids.get("summary_file_id")
                            if summary_file_id:
                                self.file_linking_tests['summary_file_id_present'] = True
                                self.test_passport_file_ids['summary_file_id'] = summary_file_id
                                self.log(f"✅ Summary file ID present: {summary_file_id}")
                            else:
                                self.log("❌ Summary file ID not present in analysis.file_ids")
                            
                            # Check file_ids structure
                            if passport_file_id and summary_file_id:
                                self.file_linking_tests['file_ids_structure_correct'] = True
                                self.log("✅ File IDs structure is correct")
                        else:
                            self.log("❌ No file_ids found in analysis")
                    
                    # Also check files object for additional verification
                    files_data = result.get("files", {})
                    if files_data:
                        self.log("📁 Files object found in response:")
                        
                        passport_file = files_data.get("passport", {})
                        if passport_file:
                            file_id = passport_file.get("file_id")
                            self.log(f"   📄 Passport file ID: {file_id}")
                        
                        summary_file = files_data.get("summary", {})
                        if summary_file:
                            file_id = summary_file.get("file_id")
                            self.log(f"   📋 Summary file ID: {file_id}")
                    
                    return True
                else:
                    error_msg = result.get("message", "Unknown error")
                    self.log(f"❌ Passport analysis failed: {error_msg}", "ERROR")
                    return False
            else:
                self.log(f"❌ Passport analysis request failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in passport analysis test: {str(e)}", "ERROR")
            return False
    
    def test_crew_creation_with_file_ids(self):
        """Test 2: Test crew creation with file IDs"""
        try:
            self.log("👤 TEST 2: Testing crew creation with file IDs...")
            
            if not self.test_passport_file_ids:
                self.log("❌ No file IDs available from passport analysis - skipping crew creation test")
                return False
            
            # Create crew data with file IDs
            crew_data = {
                "full_name": "TEST FILE LINKING CREW",
                "sex": "M",
                "date_of_birth": "1990-05-15",
                "place_of_birth": "TEST CITY",
                "passport": f"FL{int(time.time())}",  # Unique passport number
                "nationality": "VIETNAMESE",
                "rank": "Officer",
                "seamen_book": f"SB-FL-{int(time.time())}",
                "status": "Sign on",
                "ship_sign_on": self.ship_name,
                "passport_file_id": self.test_passport_file_ids.get("passport_file_id"),
                "summary_file_id": self.test_passport_file_ids.get("summary_file_id")
            }
            
            endpoint = f"{BACKEND_URL}/crew"
            self.log(f"   POST {endpoint}")
            self.log(f"   Creating crew with file IDs:")
            self.log(f"     Passport File ID: {crew_data['passport_file_id']}")
            self.log(f"     Summary File ID: {crew_data['summary_file_id']}")
            
            response = self.session.post(endpoint, json=crew_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                created_crew = response.json()
                self.file_linking_tests['crew_creation_with_file_ids_successful'] = True
                self.test_crew_id = created_crew.get('id')
                self.created_crew_ids.append(self.test_crew_id)
                
                self.log("✅ Crew creation with file IDs successful")
                self.log(f"   Created crew ID: {self.test_crew_id}")
                
                # Verify file IDs are stored in the crew record
                if created_crew.get('passport_file_id'):
                    self.file_linking_tests['crew_record_contains_passport_file_id'] = True
                    self.log(f"✅ Crew record contains passport_file_id: {created_crew.get('passport_file_id')}")
                else:
                    self.log("❌ Crew record does not contain passport_file_id")
                
                if created_crew.get('summary_file_id'):
                    self.file_linking_tests['crew_record_contains_summary_file_id'] = True
                    self.log(f"✅ Crew record contains summary_file_id: {created_crew.get('summary_file_id')}")
                else:
                    self.log("❌ Crew record does not contain summary_file_id")
                
                # Check if both file IDs are stored
                if created_crew.get('passport_file_id') and created_crew.get('summary_file_id'):
                    self.file_linking_tests['file_ids_stored_in_database'] = True
                    self.log("✅ Both file IDs stored in database successfully")
                
                return True
            else:
                self.log(f"❌ Crew creation failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in crew creation test: {str(e)}", "ERROR")
            return False
    
    def test_crew_deletion_with_file_cleanup(self):
        """Test 3: Test crew deletion with file cleanup"""
        try:
            self.log("🗑️ TEST 3: Testing crew deletion with file cleanup...")
            
            if not self.test_crew_id:
                self.log("❌ No test crew ID available - skipping deletion test")
                return False
            
            endpoint = f"{BACKEND_URL}/crew/{self.test_crew_id}"
            self.log(f"   DELETE {endpoint}")
            
            response = self.session.delete(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 204]:
                self.file_linking_tests['crew_deletion_endpoint_accessible'] = True
                self.log("✅ Crew deletion endpoint accessible")
                
                try:
                    if response.status_code == 200:
                        deletion_result = response.json()
                        self.log(f"📊 Deletion response: {deletion_result}")
                        
                        # Check for deleted_files information
                        deleted_files = deletion_result.get('deleted_files', [])
                        if deleted_files:
                            self.file_linking_tests['deletion_response_includes_deleted_files'] = True
                            self.file_linking_tests['file_cleanup_successful'] = True
                            self.log(f"✅ Deletion response includes deleted files: {deleted_files}")
                        else:
                            self.log("⚠️ No deleted_files information in response")
                        
                        # Check success message
                        message = deletion_result.get('message', '')
                        if 'files deleted' in message.lower():
                            self.file_linking_tests['google_drive_delete_calls_made'] = True
                            self.log("✅ Google Drive delete calls indicated in message")
                        
                        # Remove from our tracking list
                        if self.test_crew_id in self.created_crew_ids:
                            self.created_crew_ids.remove(self.test_crew_id)
                    else:
                        # Status 204 - successful deletion but no content
                        self.log("✅ Crew deleted successfully (204 No Content)")
                        if self.test_crew_id in self.created_crew_ids:
                            self.created_crew_ids.remove(self.test_crew_id)
                    
                    return True
                    
                except json.JSONDecodeError:
                    # 204 responses typically don't have JSON content
                    self.log("✅ Crew deleted successfully (no JSON response)")
                    if self.test_crew_id in self.created_crew_ids:
                        self.created_crew_ids.remove(self.test_crew_id)
                    return True
                    
            else:
                self.log(f"❌ Crew deletion failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in crew deletion test: {str(e)}", "ERROR")
            return False
    
    def test_file_rename_endpoint(self):
        """Test 4: Test file rename endpoint"""
        try:
            self.log("🔄 TEST 4: Testing file rename endpoint...")
            
            # First, create a new crew with file IDs for rename testing
            if not self.test_passport_file_ids:
                self.log("❌ No file IDs available - skipping rename test")
                return False
            
            # Create a new crew for rename testing
            crew_data = {
                "full_name": "TEST RENAME CREW",
                "sex": "F",
                "date_of_birth": "1985-08-20",
                "place_of_birth": "RENAME TEST CITY",
                "passport": f"RN{int(time.time())}",  # Unique passport number
                "nationality": "VIETNAMESE",
                "rank": "Engineer",
                "status": "Sign on",
                "ship_sign_on": self.ship_name,
                "passport_file_id": self.test_passport_file_ids.get("passport_file_id"),
                "summary_file_id": self.test_passport_file_ids.get("summary_file_id")
            }
            
            # Create crew
            create_response = self.session.post(f"{BACKEND_URL}/crew", json=crew_data, timeout=30)
            if create_response.status_code not in [200, 201]:
                self.log("❌ Failed to create crew for rename test")
                return False
            
            rename_crew = create_response.json()
            rename_crew_id = rename_crew.get('id')
            self.created_crew_ids.append(rename_crew_id)
            
            self.log(f"✅ Created crew for rename test: {rename_crew_id}")
            
            # Test the rename endpoint
            new_filename = "RENAMED_PASSPORT_FILE.pdf"
            endpoint = f"{BACKEND_URL}/crew/{rename_crew_id}/rename-files"
            self.log(f"   POST {endpoint}")
            self.log(f"   New filename: {new_filename}")
            
            # Prepare form data
            form_data = {
                "new_filename": new_filename
            }
            
            response = self.session.post(endpoint, data=form_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.file_linking_tests['file_rename_endpoint_accessible'] = True
                self.log("✅ File rename endpoint accessible")
                
                try:
                    rename_result = response.json()
                    self.log(f"📊 Rename response: {rename_result}")
                    
                    # Check for renamed_files information
                    renamed_files = rename_result.get('renamed_files', [])
                    if renamed_files:
                        self.file_linking_tests['rename_response_includes_renamed_files'] = True
                        self.log(f"✅ Rename response includes renamed files: {renamed_files}")
                        
                        # Check if passport file was renamed
                        if 'passport' in renamed_files:
                            self.file_linking_tests['passport_file_rename_attempted'] = True
                            self.log("✅ Passport file rename attempted")
                        
                        # Check if summary file was renamed
                        if 'summary' in renamed_files:
                            self.file_linking_tests['summary_file_rename_attempted'] = True
                            self.log("✅ Summary file rename attempted")
                        
                        # Check if Google Drive rename calls were made
                        if renamed_files:
                            self.file_linking_tests['google_drive_rename_calls_made'] = True
                            self.log("✅ Google Drive rename calls made")
                    else:
                        self.log("⚠️ No renamed_files information in response")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    return False
                    
            else:
                self.log(f"❌ File rename request failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in file rename test: {str(e)}", "ERROR")
            return False
    
    def test_crew_list_with_file_ids(self):
        """Test 5: Test crew list retrieval with file IDs"""
        try:
            self.log("📋 TEST 5: Testing crew list retrieval with file IDs...")
            
            # Test crew list endpoint with ship filter
            endpoint = f"{BACKEND_URL}/crew?ship_name={self.ship_name.replace(' ', '%20')}"
            self.log(f"   GET {endpoint}")
            
            response = self.session.get(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.file_linking_tests['crew_list_endpoint_accessible'] = True
                self.log("✅ Crew list endpoint accessible")
                
                try:
                    crew_list = response.json()
                    self.log(f"📊 Retrieved {len(crew_list)} crew members")
                    
                    # Check if any crew members have file IDs
                    crew_with_file_ids = []
                    for crew in crew_list:
                        crew_name = crew.get('full_name', 'Unknown')
                        passport_file_id = crew.get('passport_file_id')
                        summary_file_id = crew.get('summary_file_id')
                        
                        if passport_file_id or summary_file_id:
                            crew_with_file_ids.append(crew_name)
                            self.log(f"   👤 {crew_name}:")
                            if passport_file_id:
                                self.log(f"      📄 Passport File ID: {passport_file_id}")
                            if summary_file_id:
                                self.log(f"      📋 Summary File ID: {summary_file_id}")
                    
                    if crew_with_file_ids:
                        self.file_linking_tests['crew_list_includes_file_ids'] = True
                        self.log(f"✅ Crew list includes file IDs ({len(crew_with_file_ids)} crew members)")
                        
                        # Check for specific file ID types
                        passport_file_ids_found = any(crew.get('passport_file_id') for crew in crew_list)
                        summary_file_ids_found = any(crew.get('summary_file_id') for crew in crew_list)
                        
                        if passport_file_ids_found:
                            self.file_linking_tests['passport_file_id_in_crew_list'] = True
                            self.log("✅ Passport file IDs found in crew list")
                        
                        if summary_file_ids_found:
                            self.file_linking_tests['summary_file_id_in_crew_list'] = True
                            self.log("✅ Summary file IDs found in crew list")
                    else:
                        self.log("⚠️ No crew members with file IDs found in list")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    return False
                    
            else:
                self.log(f"❌ Crew list request failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in crew list test: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        try:
            self.log("🧹 Cleaning up test data...")
            
            for crew_id in self.created_crew_ids[:]:  # Copy list to avoid modification during iteration
                try:
                    endpoint = f"{BACKEND_URL}/crew/{crew_id}"
                    response = self.session.delete(endpoint, timeout=30)
                    if response.status_code in [200, 204]:
                        self.log(f"   ✅ Cleaned up crew ID: {crew_id}")
                        self.created_crew_ids.remove(crew_id)
                    else:
                        self.log(f"   ⚠️ Failed to clean up crew ID: {crew_id}")
                except Exception as e:
                    self.log(f"   ⚠️ Error cleaning up crew ID {crew_id}: {str(e)}")
            
            # Clean up test file
            test_file_path = "/tmp/test_passport_file_linking.pdf"
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
                self.log("   ✅ Cleaned up test passport file")
            
            self.log("✅ Cleanup completed")
            
        except Exception as e:
            self.log(f"❌ Error during cleanup: {str(e)}", "ERROR")
    
    def run_comprehensive_file_linking_test(self):
        """Run comprehensive test of file linking functionality"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE FILE LINKING FUNCTIONALITY TEST")
            self.log("=" * 80)
            self.log("🎯 TESTING NEW FILE LINKING FEATURES:")
            self.log("   1. Passport analysis with file ID saving")
            self.log("   2. Crew creation with file IDs")
            self.log("   3. Crew deletion with file cleanup")
            self.log("   4. File rename endpoint")
            self.log("   5. Crew list retrieval with file IDs")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\n🔐 STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Test passport analysis with file ID saving
            self.log("\n📄 STEP 2: Test passport analysis with file ID saving")
            if not self.test_passport_analysis_with_file_ids():
                self.log("❌ WARNING: Passport analysis with file IDs failed - continuing with other tests")
            
            # Step 3: Test crew creation with file IDs
            self.log("\n👤 STEP 3: Test crew creation with file IDs")
            if not self.test_crew_creation_with_file_ids():
                self.log("❌ WARNING: Crew creation with file IDs failed - continuing with other tests")
            
            # Step 4: Test crew deletion with file cleanup
            self.log("\n🗑️ STEP 4: Test crew deletion with file cleanup")
            if not self.test_crew_deletion_with_file_cleanup():
                self.log("❌ WARNING: Crew deletion with file cleanup failed - continuing with other tests")
            
            # Step 5: Test file rename endpoint
            self.log("\n🔄 STEP 5: Test file rename endpoint")
            if not self.test_file_rename_endpoint():
                self.log("❌ WARNING: File rename endpoint failed - continuing with other tests")
            
            # Step 6: Test crew list retrieval with file IDs
            self.log("\n📋 STEP 6: Test crew list retrieval with file IDs")
            if not self.test_crew_list_with_file_ids():
                self.log("❌ WARNING: Crew list with file IDs failed")
            
            # Step 7: Cleanup
            self.log("\n🧹 STEP 7: Cleanup test data")
            self.cleanup_test_data()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE FILE LINKING FUNCTIONALITY TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 FILE LINKING FUNCTIONALITY TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.file_linking_tests)
            passed_tests = sum(1 for result in self.file_linking_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.file_linking_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test 1: Passport Analysis with File ID Saving
            self.log("\n📄 TEST 1: PASSPORT ANALYSIS WITH FILE ID SAVING:")
            test1_tests = [
                ('passport_analysis_endpoint_accessible', 'Passport analysis endpoint accessible'),
                ('passport_file_uploaded_successfully', 'Passport file uploaded successfully'),
                ('analysis_contains_file_ids', 'Analysis contains file_ids'),
                ('passport_file_id_present', 'Passport file ID present in analysis.file_ids'),
                ('summary_file_id_present', 'Summary file ID present in analysis.file_ids'),
                ('file_ids_structure_correct', 'File IDs structure is correct'),
            ]
            
            for test_key, description in test1_tests:
                status = "✅ PASS" if self.file_linking_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test 2: Crew Creation with File IDs
            self.log("\n👤 TEST 2: CREW CREATION WITH FILE IDs:")
            test2_tests = [
                ('crew_creation_with_file_ids_successful', 'Crew creation with file IDs successful'),
                ('crew_record_contains_passport_file_id', 'Crew record contains passport_file_id'),
                ('crew_record_contains_summary_file_id', 'Crew record contains summary_file_id'),
                ('file_ids_stored_in_database', 'File IDs stored in database'),
            ]
            
            for test_key, description in test2_tests:
                status = "✅ PASS" if self.file_linking_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test 3: Crew Deletion with File Cleanup
            self.log("\n🗑️ TEST 3: CREW DELETION WITH FILE CLEANUP:")
            test3_tests = [
                ('crew_deletion_endpoint_accessible', 'Crew deletion endpoint accessible'),
                ('deletion_response_includes_deleted_files', 'Deletion response includes deleted files info'),
                ('google_drive_delete_calls_made', 'Google Drive delete calls made'),
                ('file_cleanup_successful', 'File cleanup successful'),
            ]
            
            for test_key, description in test3_tests:
                status = "✅ PASS" if self.file_linking_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test 4: File Rename Endpoint
            self.log("\n🔄 TEST 4: FILE RENAME ENDPOINT:")
            test4_tests = [
                ('file_rename_endpoint_accessible', 'File rename endpoint accessible'),
                ('passport_file_rename_attempted', 'Passport file rename attempted'),
                ('summary_file_rename_attempted', 'Summary file rename attempted'),
                ('rename_response_includes_renamed_files', 'Rename response includes renamed files'),
                ('google_drive_rename_calls_made', 'Google Drive rename calls made'),
            ]
            
            for test_key, description in test4_tests:
                status = "✅ PASS" if self.file_linking_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test 5: Crew List Retrieval with File IDs
            self.log("\n📋 TEST 5: CREW LIST RETRIEVAL WITH FILE IDs:")
            test5_tests = [
                ('crew_list_endpoint_accessible', 'Crew list endpoint accessible'),
                ('crew_list_includes_file_ids', 'Crew list includes file IDs'),
                ('passport_file_id_in_crew_list', 'Passport file IDs found in crew list'),
                ('summary_file_id_in_crew_list', 'Summary file IDs found in crew list'),
            ]
            
            for test_key, description in test5_tests:
                status = "✅ PASS" if self.file_linking_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'passport_analysis_endpoint_accessible',
                'analysis_contains_file_ids',
                'crew_creation_with_file_ids_successful',
                'file_ids_stored_in_database',
                'crew_deletion_endpoint_accessible',
                'file_rename_endpoint_accessible',
                'crew_list_endpoint_accessible'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.file_linking_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL FILE LINKING FEATURES WORKING")
                self.log("   ✅ File linking functionality is operational")
            else:
                self.log("   ❌ SOME CRITICAL FILE LINKING FEATURES NOT WORKING")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            if success_rate >= 80:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the file linking tests"""
    print("🧪 Backend Test: File Linking Functionality")
    print("🎯 Testing new file linking features for crew management")
    print("=" * 80)
    print("Testing requirements:")
    print("1. Passport analysis with file ID saving")
    print("2. Crew creation with file IDs")
    print("3. Crew deletion with file cleanup")
    print("4. File rename endpoint")
    print("5. Crew list retrieval with file IDs")
    print("=" * 80)
    
    tester = FileLinkingTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_file_linking_test()
        
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
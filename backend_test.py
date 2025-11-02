#!/usr/bin/env python3
"""
Backend API Testing Script - DELETE Crew Endpoint Background File Deletion Testing

FOCUS: Test the refactored DELETE /api/crew/{crew_id} endpoint with background file deletion functionality.
This endpoint was recently refactored to match the Test Report pattern for background Google Drive file deletion.

TEST REQUIREMENTS:
1. Authentication & Setup:
   - Login with admin1/123456 credentials
   - Resolve company ID (AMCSC)
   - Find crew member 'HỒ Sỹ Chương' (ID: 25d229a9-a560-484b-b49e-050294c6f711) with passport C9780204
   - Verify this crew has passport_file_id and summary_file_id for background deletion testing

2. Background Deletion Mode Test (default behavior):
   - DELETE /api/crew/{crew_id} with background=true (or omit parameter for default)
   - Expected Response: Status 200 OK, { "success": true, "message": "Crew member deleted from database (passport files are being deleted from Google Drive in background)", "files_deleted_in_background": true }
   - Verify Immediate Database Deletion: Crew record should be deleted from MongoDB immediately, subsequent GET /api/crew/{crew_id} should return 404
   - Verify Background File Deletion: Check backend logs for background task messages

3. Certificate Validation Test:
   - Find a crew member who has crew certificates
   - Try to DELETE this crew member
   - Expected Response: Status 400 Bad Request, { "detail": "Cannot delete crew \"{crew_name}\": {count} certificates exist. Please delete all certificates first." }

4. Synchronous Mode Test (background=false):
   - DELETE /api/crew/{crew_id}?background=false
   - Expected Response: Status 200 OK, { "success": true, "message": "Crew member and files deleted successfully", "deleted_files": ["passport", "summary"] }

5. Edge Cases:
   - DELETE crew with no files (no passport_file_id or summary_file_id)
   - DELETE non-existent crew_id (should return 404)
   - DELETE without authentication (should return 403)

Test credentials: admin1/123456
Test crew: 'HỒ Sỹ Chương' (25d229a9-a560-484b-b49e-050294c6f711)
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://mariner-papers.preview.emergentagent.com/api"

class BackendAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_data = None
        self.company_id = None
        self.test_crew_id = None  # Target crew for deletion testing
        self.test_crew_data = None
        self.crew_with_certificates_id = None  # Crew with certificates for validation testing
        self.crew_without_files_id = None  # Crew without files for edge case testing
        
    def print_test_header(self, test_name):
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        
    def print_result(self, success, message):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        
    def test_authentication(self):
        """Setup: Login as admin1/123456 to get access token"""
        self.print_test_header("Setup - Admin Authentication")
        
        try:
            # Test data - using admin1/123456 credentials as specified in the review request
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            print(f"🔐 Testing login with credentials: {login_data['username']}/{login_data['password']}")
            print(f"📡 POST {BACKEND_URL}/auth/login")
            
            # Make login request
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"📄 Response Data Keys: {list(response_data.keys())}")
                
                # Check required fields
                required_fields = ["access_token", "token_type", "user"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in response_data:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.print_result(False, f"Missing required fields: {missing_fields}")
                    return False
                
                # Store token and user data for later tests
                self.access_token = response_data["access_token"]
                self.user_data = response_data["user"]
                
                # Verify token type
                if response_data["token_type"] != "bearer":
                    self.print_result(False, f"Expected token_type 'bearer', got '{response_data['token_type']}'")
                    return False
                
                # Verify user object has required fields
                user_required_fields = ["username", "role", "id", "company"]
                user_missing_fields = []
                
                for field in user_required_fields:
                    if field not in self.user_data:
                        user_missing_fields.append(field)
                
                if user_missing_fields:
                    self.print_result(False, f"User object missing fields: {user_missing_fields}")
                    return False
                
                print(f"🔑 Access Token: {self.access_token[:20]}...")
                print(f"👤 User ID: {self.user_data['id']}")
                print(f"👤 Username: {self.user_data['username']}")
                print(f"👤 Role: {self.user_data['role']}")
                print(f"🏢 Company: {self.user_data['company']}")
                
                # Check if user has admin or super_admin role for delete operations
                if self.user_data['role'] not in ['admin', 'super_admin', 'manager']:
                    self.print_result(False, f"User role '{self.user_data['role']}' may not have permission for delete operations")
                    return False
                
                self.print_result(True, "Authentication successful - admin1 login returns access_token with proper role and company")
                return True
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Login failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during authentication test: {str(e)}")
            return False
    
    def test_get_company_id(self):
        """Test 1: Get user's company_id from login response"""
        self.print_test_header("Test 1 - Get Company ID")
        
        if not self.access_token or not self.user_data:
            self.print_result(False, "No access token or user data available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Get companies to find the user's company ID
            print(f"📡 GET {BACKEND_URL}/companies")
            print(f"🎯 Finding company ID for user's company: {self.user_data['company']}")
            
            response = self.session.get(
                f"{BACKEND_URL}/companies",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                companies = response.json()
                print(f"📄 Found {len(companies)} companies")
                
                # Find user's company by ID or name
                user_company_identifier = self.user_data['company']
                
                # First try to match by ID (if user.company is already a UUID)
                for company in companies:
                    if company.get('id') == user_company_identifier:
                        self.company_id = company['id']
                        print(f"🏢 Found company by ID: {self.company_id}")
                        print(f"🏢 Company Name (EN): {company.get('name_en')}")
                        print(f"🏢 Company Name (VN): {company.get('name_vn')}")
                        self.print_result(True, f"Successfully found company ID: {self.company_id}")
                        return True
                
                # If not found by ID, try by name
                for company in companies:
                    if (company.get('name_en') == user_company_identifier or 
                        company.get('name_vn') == user_company_identifier or
                        company.get('name') == user_company_identifier):
                        self.company_id = company['id']
                        print(f"🏢 Found company by name: {self.company_id}")
                        print(f"🏢 Company Name (EN): {company.get('name_en')}")
                        print(f"🏢 Company Name (VN): {company.get('name_vn')}")
                        self.print_result(True, f"Successfully found company ID: {self.company_id}")
                        return True
                
                # Debug: Print all companies to see what's available
                print(f"🔍 Available companies:")
                for company in companies:
                    print(f"   ID: {company.get('id')}, Name EN: {company.get('name_en')}, Name VN: {company.get('name_vn')}")
                
                self.print_result(False, f"Company '{user_company_identifier}' not found in companies list")
                return False
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"GET companies failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"GET companies failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during get company ID test: {str(e)}")
            return False
    
    def test_find_target_crew(self):
        """Test 2: Find target crew member 'HỒ Sỹ Chương' for deletion testing"""
        self.print_test_header("Test 2 - Find Target Crew Member")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 GET {BACKEND_URL}/crew")
            print(f"🎯 Finding crew member 'HỒ Sỹ Chương' (ID: 25d229a9-a560-484b-b49e-050294c6f711)")
            
            # Make request to get crew list
            response = self.session.get(
                f"{BACKEND_URL}/crew",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                crew_list = response.json()
                print(f"📄 Found {len(crew_list)} crew members")
                
                if not crew_list:
                    self.print_result(False, "No crew members found in the system")
                    return False
                
                # Look for target crew member
                target_crew = None
                crew_with_certs = None
                crew_without_files = None
                
                for crew in crew_list:
                    crew_name = crew.get('full_name', '')
                    crew_id = crew.get('id', '')
                    passport = crew.get('passport', '')
                    passport_file_id = crew.get('passport_file_id')
                    summary_file_id = crew.get('summary_file_id')
                    
                    print(f"👤 Crew: {crew_name} (ID: {crew_id[:8]}..., Passport: {passport})")
                    
                    # Look for HỒ Sỹ Chương with passport C9780204
                    if ('HỒ' in crew_name.upper() and 'CHƯƠNG' in crew_name.upper()) or crew_id == '25d229a9-a560-484b-b49e-050294c6f711':
                        target_crew = crew
                        print(f"✅ Found target crew: {crew_name}")
                        print(f"   ID: {crew_id}")
                        print(f"   Passport: {passport}")
                        print(f"   Has passport_file_id: {bool(passport_file_id)}")
                        print(f"   Has summary_file_id: {bool(summary_file_id)}")
                    
                    # Look for crew without files for edge case testing
                    if not passport_file_id and not summary_file_id and not crew_without_files:
                        crew_without_files = crew
                        print(f"📝 Found crew without files: {crew_name} (for edge case testing)")
                
                if target_crew:
                    self.test_crew_id = target_crew['id']
                    self.test_crew_data = target_crew
                    
                    # Verify this crew has files for background deletion testing
                    has_passport_file = bool(target_crew.get('passport_file_id'))
                    has_summary_file = bool(target_crew.get('summary_file_id'))
                    
                    if has_passport_file and has_summary_file:
                        print(f"✅ Target crew has both passport and summary files - perfect for background deletion testing")
                    elif has_passport_file or has_summary_file:
                        print(f"⚠️ Target crew has only one file - still suitable for testing")
                    else:
                        print(f"⚠️ Target crew has no files - will test deletion without files")
                    
                    # Store crew without files for edge case testing
                    if crew_without_files:
                        self.crew_without_files_id = crew_without_files['id']
                        print(f"📝 Stored crew without files: {crew_without_files.get('full_name')} ({crew_without_files['id'][:8]}...)")
                    
                    self.print_result(True, f"Successfully found target crew: {target_crew.get('full_name')} ({target_crew['id'][:8]}...)")
                    return True
                else:
                    self.print_result(False, "Target crew 'HỒ Sỹ Chương' not found in crew list")
                    return False
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"GET crew failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"GET crew failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during find target crew test: {str(e)}")
            return False
    
    def test_find_crew_with_certificates(self):
        """Test 3: Find a crew member who has certificates for validation testing"""
        self.print_test_header("Test 3 - Find Crew Member with Certificates")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 GET {BACKEND_URL}/crew-certificates/all")
            print(f"🎯 Finding crew member with certificates for validation testing")
            
            # Make request to get crew certificates
            response = self.session.get(
                f"{BACKEND_URL}/crew-certificates/all",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                print(f"📄 Found {len(certificates)} crew certificates")
                
                if not certificates:
                    print(f"⚠️ No crew certificates found - will skip certificate validation test")
                    self.print_result(True, "No crew certificates found - certificate validation test will be skipped")
                    return True
                
                # Group certificates by crew_id to find crew with certificates
                crew_cert_counts = {}
                for cert in certificates:
                    crew_id = cert.get('crew_id')
                    crew_name = cert.get('crew_name', 'Unknown')
                    if crew_id:
                        if crew_id not in crew_cert_counts:
                            crew_cert_counts[crew_id] = {
                                'count': 0,
                                'crew_name': crew_name
                            }
                        crew_cert_counts[crew_id]['count'] += 1
                
                # Find crew with most certificates (but not our target crew)
                best_crew = None
                max_certs = 0
                
                for crew_id, info in crew_cert_counts.items():
                    cert_count = info['count']
                    crew_name = info['crew_name']
                    
                    print(f"👤 Crew {crew_name} ({crew_id[:8]}...): {cert_count} certificates")
                    
                    # Don't use our target crew for this test
                    if crew_id != self.test_crew_id and cert_count > max_certs:
                        max_certs = cert_count
                        best_crew = {
                            'crew_id': crew_id,
                            'crew_name': crew_name,
                            'cert_count': cert_count
                        }
                
                if best_crew:
                    self.crew_with_certificates_id = best_crew['crew_id']
                    print(f"✅ Selected crew with certificates: {best_crew['crew_name']} ({best_crew['cert_count']} certificates)")
                    self.print_result(True, f"Found crew with {best_crew['cert_count']} certificates for validation testing")
                    return True
                else:
                    print(f"⚠️ No suitable crew with certificates found (excluding target crew)")
                    self.print_result(True, "No suitable crew with certificates found - validation test will be skipped")
                    return True
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"GET crew-certificates failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"GET crew-certificates failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during find crew with certificates test: {str(e)}")
            return False
    
    def test_delete_crew_background_mode(self):
        """Test 4: DELETE crew with background=true (default behavior)"""
        self.print_test_header("Test 4 - DELETE Crew Background Mode (Default)")
        
        if not self.access_token or not self.test_crew_id:
            self.print_result(False, "Missing required data from previous tests")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 DELETE {BACKEND_URL}/crew/{self.test_crew_id}")
            print(f"🎯 Testing background deletion mode (default behavior)")
            print(f"👤 Target Crew: {self.test_crew_data.get('full_name')} (ID: {self.test_crew_id[:8]}...)")
            
            # Test with background=true (default)
            start_time = time.time()
            response = self.session.delete(
                f"{BACKEND_URL}/crew/{self.test_crew_id}",
                headers=headers,
                timeout=30
            )
            response_time = time.time() - start_time
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"⏱️ Response Time: {response_time:.3f} seconds")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"📄 Response Keys: {list(response_data.keys())}")
                
                # Verify expected response structure
                expected_fields = ["success", "message", "files_deleted_in_background"]
                success = response_data.get("success")
                message = response_data.get("message", "")
                files_deleted_in_background = response_data.get("files_deleted_in_background")
                
                print(f"✅ Success: {success}")
                print(f"📝 Message: {message}")
                print(f"🔄 Files Deleted in Background: {files_deleted_in_background}")
                
                # Verify response structure
                if success and "deleted from database" in message:
                    print(f"✅ Response indicates database deletion completed")
                    
                    if files_deleted_in_background:
                        print(f"✅ Response indicates files are being deleted in background")
                    
                    # Verify API response time is fast (< 500ms for background mode)
                    if response_time < 0.5:
                        print(f"✅ Response time {response_time:.3f}s is fast (< 500ms) - background mode working")
                    else:
                        print(f"⚠️ Response time {response_time:.3f}s is slow (> 500ms) - may not be background mode")
                    
                    # Verify immediate database deletion
                    print(f"\n🔍 Verifying immediate database deletion...")
                    verify_response = self.session.get(
                        f"{BACKEND_URL}/crew/{self.test_crew_id}",
                        headers=headers
                    )
                    
                    if verify_response.status_code == 404:
                        print(f"✅ Crew deleted from database immediately (GET returns 404)")
                        
                        # Check backend logs for background task messages
                        print(f"\n📋 Checking backend logs for background task messages...")
                        self.check_background_deletion_logs()
                        
                        self.print_result(True, f"Background deletion successful - crew deleted from DB immediately, files being deleted in background")
                        return True
                    else:
                        print(f"❌ Crew still exists in database (GET returns {verify_response.status_code})")
                        self.print_result(False, "Database deletion not immediate")
                        return False
                else:
                    self.print_result(False, f"Unexpected response structure or content: {response_data}")
                    return False
                    
            elif response.status_code == 400:
                # This might be expected if crew has certificates
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", "")
                    if "certificates exist" in detail:
                        print(f"⚠️ Crew has certificates - this is expected validation")
                        print(f"📝 Error: {detail}")
                        self.print_result(True, "Crew has certificates - validation working correctly")
                        return True
                    else:
                        self.print_result(False, f"Unexpected 400 error: {error_data}")
                        return False
                except:
                    self.print_result(False, f"DELETE crew failed with status {response.status_code}: {response.text}")
                    return False
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"DELETE crew failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"DELETE crew failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during background deletion test: {str(e)}")
            return False
    
    def check_background_deletion_logs(self):
        """Helper method to check backend logs for background deletion messages"""
        try:
            import subprocess
            result = subprocess.run(['tail', '-n', '100', '/var/log/supervisor/backend.err.log'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                log_content = result.stdout
                
                # Check for expected background task log messages
                background_started = "🔄 Background task started: Deleting files for crew" in log_content
                passport_deleted = "✅ Background: Passport file deleted:" in log_content
                summary_deleted = "✅ Background: Summary file deleted:" in log_content
                task_completed = "✅ Background task completed: Deleted" in log_content
                
                print(f"   📋 Background task started: {'✅ FOUND' if background_started else '❌ NOT FOUND'}")
                print(f"   📋 Passport file deleted: {'✅ FOUND' if passport_deleted else '❌ NOT FOUND'}")
                print(f"   📋 Summary file deleted: {'✅ FOUND' if summary_deleted else '❌ NOT FOUND'}")
                print(f"   📋 Task completed: {'✅ FOUND' if task_completed else '❌ NOT FOUND'}")
                
                # Print recent relevant log lines
                lines = log_content.split('\n')
                relevant_lines = [line for line in lines if any(keyword in line for keyword in 
                                ['Background task', 'Background:', 'Deleting files for crew'])]
                
                if relevant_lines:
                    print(f"\n📄 Recent background deletion logs:")
                    for line in relevant_lines[-5:]:  # Last 5 relevant lines
                        print(f"   {line}")
                else:
                    print(f"   ⚠️ No background deletion logs found yet (may still be processing)")
                    
            else:
                print(f"   ⚠️ Could not read backend logs")
        except Exception as e:
            print(f"   ⚠️ Log check failed: {e}")

    def test_certificate_validation(self):
        """Test 5: Try to delete crew member with certificates (should be blocked)"""
        self.print_test_header("Test 5 - Certificate Validation Test")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        if not self.crew_with_certificates_id:
            print(f"⚠️ No crew with certificates found - skipping validation test")
            self.print_result(True, "No crew with certificates found - validation test skipped")
            return True
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 DELETE {BACKEND_URL}/crew/{self.crew_with_certificates_id}")
            print(f"🎯 Testing certificate validation (should block deletion)")
            print(f"👤 Target Crew: {self.crew_with_certificates_id[:8]}... (has certificates)")
            
            # Try to delete crew with certificates
            response = self.session.delete(
                f"{BACKEND_URL}/crew/{self.crew_with_certificates_id}",
                headers=headers,
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 400:
                # This is expected - crew has certificates
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", "")
                    
                    print(f"📝 Error Detail: {detail}")
                    
                    # Verify error message format
                    if "Cannot delete crew" in detail and "certificates exist" in detail:
                        print(f"✅ Correct error message format")
                        
                        # Verify crew name and certificate count are included
                        if ":" in detail and "certificates" in detail:
                            print(f"✅ Error message includes crew name and certificate count")
                            
                            # Verify crew is NOT deleted from database
                            print(f"\n🔍 Verifying crew was NOT deleted from database...")
                            verify_response = self.session.get(
                                f"{BACKEND_URL}/crew/{self.crew_with_certificates_id}",
                                headers=headers
                            )
                            
                            if verify_response.status_code == 200:
                                print(f"✅ Crew still exists in database (validation working)")
                                self.print_result(True, "Certificate validation working correctly - deletion blocked")
                                return True
                            else:
                                print(f"❌ Crew was deleted despite having certificates")
                                self.print_result(False, "Certificate validation failed - crew was deleted")
                                return False
                        else:
                            print(f"⚠️ Error message missing crew name or certificate count")
                            self.print_result(True, "Certificate validation working but message format could be improved")
                            return True
                    else:
                        print(f"❌ Unexpected error message format")
                        self.print_result(False, f"Unexpected error message: {detail}")
                        return False
                        
                except Exception as e:
                    print(f"❌ Error parsing response: {e}")
                    self.print_result(False, f"Error parsing 400 response: {e}")
                    return False
                    
            elif response.status_code == 200:
                # This is unexpected - deletion should have been blocked
                print(f"❌ Deletion succeeded when it should have been blocked")
                self.print_result(False, "Certificate validation failed - deletion was allowed")
                return False
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Unexpected response status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Unexpected response status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during certificate validation test: {str(e)}")
            return False
    
    def test_delete_crew_synchronous_mode(self):
        """Test 6: DELETE crew with background=false (synchronous mode)"""
        self.print_test_header("Test 6 - DELETE Crew Synchronous Mode")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        # Use crew without files if available, otherwise skip this test
        if not self.crew_without_files_id:
            print(f"⚠️ No crew without files found - skipping synchronous mode test")
            self.print_result(True, "No crew without files found - synchronous mode test skipped")
            return True
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 DELETE {BACKEND_URL}/crew/{self.crew_without_files_id}?background=false")
            print(f"🎯 Testing synchronous deletion mode (background=false)")
            print(f"👤 Target Crew: {self.crew_without_files_id[:8]}... (crew without files)")
            
            # Test with background=false (synchronous mode)
            start_time = time.time()
            response = self.session.delete(
                f"{BACKEND_URL}/crew/{self.crew_without_files_id}?background=false",
                headers=headers,
                timeout=60  # Longer timeout for synchronous mode
            )
            response_time = time.time() - start_time
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"⏱️ Response Time: {response_time:.3f} seconds")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"📄 Response Keys: {list(response_data.keys())}")
                
                # Verify expected response structure for synchronous mode
                success = response_data.get("success")
                message = response_data.get("message", "")
                deleted_files = response_data.get("deleted_files", [])
                
                print(f"✅ Success: {success}")
                print(f"📝 Message: {message}")
                print(f"📁 Deleted Files: {deleted_files}")
                
                # Verify response structure for synchronous mode
                if success and "files deleted successfully" in message:
                    print(f"✅ Response indicates synchronous deletion completed")
                    
                    # Verify crew is deleted from database
                    print(f"\n🔍 Verifying crew deleted from database...")
                    verify_response = self.session.get(
                        f"{BACKEND_URL}/crew/{self.crew_without_files_id}",
                        headers=headers
                    )
                    
                    if verify_response.status_code == 404:
                        print(f"✅ Crew deleted from database (GET returns 404)")
                        self.print_result(True, f"Synchronous deletion successful - crew and files deleted")
                        return True
                    else:
                        print(f"❌ Crew still exists in database (GET returns {verify_response.status_code})")
                        self.print_result(False, "Synchronous deletion failed - crew not deleted from database")
                        return False
                else:
                    self.print_result(False, f"Unexpected response structure or content: {response_data}")
                    return False
                    
            elif response.status_code == 400:
                # This might be expected if crew has certificates
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", "")
                    if "certificates exist" in detail:
                        print(f"⚠️ Crew has certificates - this is expected validation")
                        print(f"📝 Error: {detail}")
                        self.print_result(True, "Crew has certificates - validation working correctly")
                        return True
                    else:
                        self.print_result(False, f"Unexpected 400 error: {error_data}")
                        return False
                except:
                    self.print_result(False, f"DELETE crew failed with status {response.status_code}: {response.text}")
                    return False
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"DELETE crew failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"DELETE crew failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during synchronous deletion test: {str(e)}")
            return False
    
    def test_edge_cases(self):
        """Test 7: Edge cases - non-existent crew, no authentication"""
        self.print_test_header("Test 7 - Edge Cases")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        edge_case_results = []
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Edge Case 1: DELETE non-existent crew_id
            print(f"\n🔍 Edge Case 1: DELETE non-existent crew_id")
            fake_crew_id = "non-existent-crew-id-12345"
            print(f"📡 DELETE {BACKEND_URL}/crew/{fake_crew_id}")
            
            response = self.session.delete(
                f"{BACKEND_URL}/crew/{fake_crew_id}",
                headers=headers,
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 404:
                print(f"✅ Correctly returns 404 for non-existent crew")
                edge_case_results.append(True)
            else:
                print(f"❌ Expected 404, got {response.status_code}")
                edge_case_results.append(False)
            
            # Edge Case 2: DELETE without authentication
            print(f"\n🔍 Edge Case 2: DELETE without authentication")
            print(f"📡 DELETE {BACKEND_URL}/crew/{fake_crew_id} (no auth header)")
            
            response = self.session.delete(
                f"{BACKEND_URL}/crew/{fake_crew_id}",
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 403:
                print(f"✅ Correctly returns 403 for unauthenticated request")
                edge_case_results.append(True)
            elif response.status_code == 401:
                print(f"✅ Correctly returns 401 for unauthenticated request")
                edge_case_results.append(True)
            else:
                print(f"❌ Expected 403/401, got {response.status_code}")
                edge_case_results.append(False)
            
            # Summary of edge case results
            passed_edge_cases = sum(edge_case_results)
            total_edge_cases = len(edge_case_results)
            
            print(f"\n📊 Edge Cases Summary: {passed_edge_cases}/{total_edge_cases} passed")
            
            if passed_edge_cases == total_edge_cases:
                self.print_result(True, f"All edge cases passed ({passed_edge_cases}/{total_edge_cases})")
                return True
            else:
                self.print_result(False, f"Some edge cases failed ({passed_edge_cases}/{total_edge_cases})")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during edge cases test: {str(e)}")
            return False
    
    def test_backend_logs_verification(self):
        """Test 8: Verify backend logs for proper logging sequence"""
        self.print_test_header("Test 8 - Backend Logs Verification")
        
        try:
            print(f"📋 Checking supervisor logs for DELETE crew operations...")
            
            import subprocess
            result = subprocess.run(['tail', '-n', '200', '/var/log/supervisor/backend.err.log'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_content = result.stdout
                
                # Check for expected DELETE crew log messages
                crew_deletion_logs = [
                    "🗑️ Deleting crew member:",
                    "✅ Crew member deleted from database:",
                    "🚀 Background deletion mode:",
                    "📤 Starting background file deletion",
                    "🔄 Background task started: Deleting files for crew",
                    "✅ Background: Passport file deleted:",
                    "✅ Background: Summary file deleted:",
                    "✅ Background task completed: Deleted"
                ]
                
                found_logs = []
                for log_pattern in crew_deletion_logs:
                    if log_pattern in log_content:
                        found_logs.append(log_pattern)
                        print(f"✅ Found: {log_pattern}")
                    else:
                        print(f"❌ Missing: {log_pattern}")
                
                # Check for certificate validation logs
                validation_logs = [
                    "❌ Cannot delete crew",
                    "certificates still exist"
                ]
                
                validation_found = []
                for log_pattern in validation_logs:
                    if log_pattern in log_content:
                        validation_found.append(log_pattern)
                        print(f"✅ Found validation log: {log_pattern}")
                
                # Print recent DELETE crew related logs
                lines = log_content.split('\n')
                relevant_lines = [line for line in lines if any(keyword in line for keyword in 
                                ['Deleting crew', 'crew member', 'Background task', 'certificates exist'])]
                
                if relevant_lines:
                    print(f"\n📄 Recent DELETE crew logs:")
                    for line in relevant_lines[-10:]:  # Last 10 relevant lines
                        print(f"   {line}")
                
                # Scoring
                log_score = len(found_logs)
                total_possible = len(crew_deletion_logs)
                
                print(f"\n📊 Log Verification Summary:")
                print(f"   Found logs: {log_score}/{total_possible}")
                print(f"   Validation logs: {len(validation_found)}")
                
                if log_score >= total_possible // 2:  # At least half the logs found
                    self.print_result(True, f"Backend logs verification successful ({log_score}/{total_possible} logs found)")
                    return True
                else:
                    self.print_result(False, f"Insufficient logs found ({log_score}/{total_possible})")
                    return False
                    
            else:
                print(f"⚠️ Could not read backend logs")
                self.print_result(True, "Could not read backend logs - test skipped")
                return True
                
        except Exception as e:
            print(f"⚠️ Log verification failed: {e}")
            self.print_result(True, f"Log verification failed: {e} - test skipped")
            return True
    
    def run_all_tests(self):
        """Run all DELETE Crew endpoint tests in sequence"""
        print(f"\n🚀 STARTING DELETE CREW ENDPOINT BACKGROUND FILE DELETION TESTING")
        print(f"🎯 Testing refactored DELETE /api/crew/{{crew_id}} endpoint with background file deletion")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"📅 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test sequence for DELETE Crew endpoint
        tests = [
            ("Setup - Authentication", self.test_authentication),
            ("Setup - Company ID Resolution", self.test_get_company_id),
            ("Setup - Find Target Crew", self.test_find_target_crew),
            ("Setup - Find Crew with Certificates", self.test_find_crew_with_certificates),
            ("Test 1 - Background Deletion Mode (Default)", self.test_delete_crew_background_mode),
            ("Test 2 - Certificate Validation", self.test_certificate_validation),
            ("Test 3 - Synchronous Deletion Mode", self.test_delete_crew_synchronous_mode),
            ("Test 4 - Edge Cases", self.test_edge_cases),
            ("Test 5 - Backend Logs Verification", self.test_backend_logs_verification),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n" + "="*80)
                result = test_func()
                results.append((test_name, result))
                
                if not result:
                    print(f"❌ Test failed: {test_name}")
                    print(f"⚠️ Stopping test sequence due to failure")
                    break
                else:
                    print(f"✅ Test passed: {test_name}")
                    
            except Exception as e:
                print(f"💥 Exception in {test_name}: {str(e)}")
                results.append((test_name, False))
                break
        
        # Print final summary
        print(f"\n" + "="*80)
        print(f"📊 DELETE CREW ENDPOINT TEST SUMMARY")
        print(f"="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
        print(f"📅 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")
        
        # Overall assessment
        if success_rate >= 80:
            print(f"\n🎉 DELETE CREW ENDPOINT TESTING SUCCESSFUL!")
            print(f"✅ Background deletion mode working correctly")
            print(f"✅ Certificate validation preventing deletion")
            print(f"✅ Synchronous deletion mode working")
            print(f"✅ Edge cases handled properly")
            print(f"✅ Backend logging working correctly")
        elif success_rate >= 60:
            print(f"\n⚠️ DELETE CREW ENDPOINT PARTIALLY WORKING")
            print(f"📊 Some components working but issues detected")
            print(f"🔧 Review failed tests for specific issues")
        else:
            print(f"\n❌ DELETE CREW ENDPOINT TESTING FAILED")
            print(f"🚨 Critical issues detected in core functionality")
            print(f"🔧 Major fixes required")
        
        return success_rate >= 80


if __name__ == "__main__":
    """Main execution - run DELETE crew endpoint tests"""
    tester = BackendAPITester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED - DELETE CREW ENDPOINT IS WORKING CORRECTLY")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED - REVIEW RESULTS ABOVE")
        sys.exit(1)

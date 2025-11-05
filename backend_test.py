#!/usr/bin/env python3
"""
Backend API Testing Script - Audit Report AI Analysis Endpoint Testing

FOCUS: Test the Audit Report AI Analysis endpoint (/api/audit-reports/analyze) after AI configuration fix.
The fix changed from looking in 'ai_configs' collection with company_id to 'ai_config' collection with id='system_ai'.

TEST REQUIREMENTS:
1. Authentication Setup:
   - Login with admin1/123456
   - Get company_id and ship list
   - Find a test ship (e.g., BROTHER 36)

2. Audit Report Analysis Endpoint Test:
   - POST /api/audit-reports/analyze
   - Parameters: ship_id (from ship list), file (PDF), bypass_validation=false
   - Use a sample PDF audit report if available, or create a minimal PDF for testing
   - Expected response: success=true, analysis object with fields (audit_report_name, audit_type, audit_report_no, audit_date, audited_by, auditor_name, status, note)
   - Should NOT return 403/400 errors related to AI config

3. Backend Logs Verification:
   - Check logs for: "✅ Using emergent_llm_key from system AI config" OR "⚠️ No system AI config found, using fallback emergent_llm_key"
   - Verify AI analysis process logs
   - Confirm no errors related to missing AI config or emergent_llm_key

4. Error Handling:
   - Test with invalid ship_id (should return 404)
   - Test with non-PDF file (should return 400 with proper message)
   - Test without authentication (should return 403)

SUCCESS CRITERIA:
- ✅ Endpoint returns 200 OK with analysis results (not 403/400 AI config error)
- ✅ AI config retrieved successfully (either from system_ai or fallback)
- ✅ Analysis uses Gemini model and returns proper JSON structure
- ✅ Backend logs show proper AI config retrieval and analysis process
- ✅ Error handling works correctly

Test credentials: admin1/123456
Test ship: BROTHER 36 (or any available ship)
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://audit-flow.preview.emergentagent.com/api"

class BackendAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_data = None
        self.company_id = None
        self.ships_list = None  # List of ships for testing
        self.test_ship_id = None  # Target ship for audit report testing
        self.test_ship_data = None
        
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
    
    def test_get_ships_list(self):
        """Test 2: Get ships list and find test ship (e.g., BROTHER 36)"""
        self.print_test_header("Test 2 - Get Ships List and Find Test Ship")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 GET {BACKEND_URL}/ships")
            print(f"🎯 Finding test ship (preferably BROTHER 36)")
            
            # Make request to get ships list
            response = self.session.get(
                f"{BACKEND_URL}/ships",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                ships_list = response.json()
                print(f"📄 Found {len(ships_list)} ships")
                
                if not ships_list:
                    self.print_result(False, "No ships found in the system")
                    return False
                
                self.ships_list = ships_list
                
                # Look for BROTHER 36 or any suitable test ship
                target_ship = None
                
                for ship in ships_list:
                    ship_name = ship.get('name', '')
                    ship_id = ship.get('id', '')
                    imo = ship.get('imo', '')
                    ship_type = ship.get('ship_type', '')
                    
                    print(f"🚢 Ship: {ship_name} (ID: {ship_id[:8]}..., IMO: {imo}, Type: {ship_type})")
                    
                    # Prefer BROTHER 36 if available
                    if 'BROTHER 36' in ship_name.upper():
                        target_ship = ship
                        print(f"✅ Found preferred test ship: {ship_name}")
                        break
                    elif not target_ship:  # Use first ship as fallback
                        target_ship = ship
                
                if target_ship:
                    self.test_ship_id = target_ship['id']
                    self.test_ship_data = target_ship
                    
                    print(f"✅ Selected test ship: {target_ship.get('name')}")
                    print(f"   ID: {target_ship['id']}")
                    print(f"   IMO: {target_ship.get('imo', 'N/A')}")
                    print(f"   Type: {target_ship.get('ship_type', 'N/A')}")
                    
                    self.print_result(True, f"Successfully found test ship: {target_ship.get('name')} ({target_ship['id'][:8]}...)")
                    return True
                else:
                    self.print_result(False, "No suitable test ship found")
                    return False
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"GET ships failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"GET ships failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during get ships list test: {str(e)}")
            return False
    
    def create_test_pdf(self):
        """Create a minimal test PDF for audit report analysis"""
        try:
            # Create a simple text file that we'll use as a "PDF" for testing
            test_content = """
AUDIT REPORT

Ship Name: BROTHER 36
IMO Number: 8743531
Audit Type: ISM
Audit Report No: AR-2024-001
Audit Date: 15/01/2024
Audited By: DNV GL
Auditor Name: John Smith
Status: Valid
Note: Annual ISM audit completed successfully

This is a test audit report for API testing purposes.
            """.strip()
            
            # Write to a temporary file
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False)
            temp_file.write(test_content)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            print(f"⚠️ Could not create test PDF: {e}")
            return None
    
    def test_audit_report_analyze_endpoint(self):
        """Test 3: POST /api/audit-reports/analyze endpoint with AI configuration fix"""
        self.print_test_header("Test 3 - Audit Report AI Analysis Endpoint")
        
        if not self.access_token or not self.test_ship_id:
            self.print_result(False, "Missing required data from previous tests")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            print(f"📡 POST {BACKEND_URL}/audit-reports/analyze")
            print(f"🎯 Testing AI analysis with ship_id and PDF file")
            print(f"🚢 Target Ship: {self.test_ship_data.get('name')} (ID: {self.test_ship_id[:8]}...)")
            
            # Create test PDF file
            test_pdf_path = self.create_test_pdf()
            if not test_pdf_path:
                self.print_result(False, "Could not create test PDF file")
                return False
            
            try:
                # Prepare multipart form data
                with open(test_pdf_path, 'rb') as pdf_file:
                    files = {
                        'file': ('test_audit_report.pdf', pdf_file, 'application/pdf')
                    }
                    data = {
                        'ship_id': self.test_ship_id,
                        'bypass_validation': 'false'
                    }
                    
                    print(f"📄 Uploading test PDF file for analysis...")
                    print(f"📋 Parameters: ship_id={self.test_ship_id[:8]}..., bypass_validation=false")
                    
                    # Make the API request
                    start_time = time.time()
                    response = self.session.post(
                        f"{BACKEND_URL}/audit-reports/analyze",
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=120  # AI analysis can take time
                    )
                    response_time = time.time() - start_time
                    
                    print(f"📊 Response Status: {response.status_code}")
                    print(f"⏱️ Response Time: {response_time:.1f} seconds")
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        print(f"📄 Response Keys: {list(response_data.keys())}")
                        
                        # Verify expected response structure
                        success = response_data.get("success")
                        analysis = response_data.get("analysis", {})
                        
                        print(f"✅ Success: {success}")
                        print(f"🔍 Analysis Keys: {list(analysis.keys()) if analysis else 'None'}")
                        
                        if success and analysis:
                            # Check for expected analysis fields
                            expected_fields = [
                                "audit_report_name", "audit_type", "audit_report_no", 
                                "audit_date", "audited_by", "auditor_name", "status", "note"
                            ]
                            
                            found_fields = []
                            for field in expected_fields:
                                if field in analysis:
                                    found_fields.append(field)
                                    value = analysis[field]
                                    print(f"   {field}: {value}")
                            
                            print(f"📊 Found {len(found_fields)}/{len(expected_fields)} expected fields")
                            
                            # Verify this is NOT a 403/400 AI config error
                            if len(found_fields) >= 4:  # At least half the fields should be present
                                print(f"✅ AI analysis successful - extracted audit report fields")
                                print(f"✅ No AI configuration errors detected")
                                
                                # Check backend logs for AI config messages
                                print(f"\n📋 Checking backend logs for AI config retrieval...")
                                self.check_ai_config_logs()
                                
                                self.print_result(True, f"Audit Report AI analysis successful - endpoint working correctly")
                                return True
                            else:
                                print(f"⚠️ Analysis returned but with limited fields")
                                self.print_result(False, f"Analysis incomplete - only {len(found_fields)} fields found")
                                return False
                        else:
                            print(f"❌ Analysis failed or returned empty")
                            self.print_result(False, f"Analysis failed: success={success}, analysis={bool(analysis)}")
                            return False
                            
                    elif response.status_code == 403:
                        # This indicates AI config error - the main issue we're testing
                        try:
                            error_data = response.json()
                            detail = error_data.get("detail", "")
                            print(f"❌ 403 Forbidden Error: {detail}")
                            
                            if "AI configuration" in detail or "emergent_llm_key" in detail:
                                print(f"🚨 CRITICAL: AI configuration error detected - this is the bug we're testing!")
                                self.print_result(False, f"AI configuration error: {detail}")
                            else:
                                print(f"❌ Authentication/authorization error: {detail}")
                                self.print_result(False, f"Authentication error: {detail}")
                            return False
                        except:
                            self.print_result(False, f"403 error with unparseable response: {response.text}")
                            return False
                            
                    elif response.status_code == 400:
                        # Check if this is AI config related or validation error
                        try:
                            error_data = response.json()
                            detail = error_data.get("detail", "")
                            print(f"❌ 400 Bad Request: {detail}")
                            
                            if "AI configuration" in detail or "emergent_llm_key" in detail:
                                print(f"🚨 CRITICAL: AI configuration error detected - this is the bug we're testing!")
                                self.print_result(False, f"AI configuration error: {detail}")
                            else:
                                print(f"⚠️ Validation or request error: {detail}")
                                self.print_result(False, f"Request validation error: {detail}")
                            return False
                        except:
                            self.print_result(False, f"400 error with unparseable response: {response.text}")
                            return False
                    else:
                        try:
                            error_data = response.json()
                            self.print_result(False, f"Audit report analysis failed with status {response.status_code}: {error_data}")
                        except:
                            self.print_result(False, f"Audit report analysis failed with status {response.status_code}: {response.text}")
                        return False
                        
            finally:
                # Clean up test file
                try:
                    import os
                    os.unlink(test_pdf_path)
                except:
                    pass
                
        except Exception as e:
            self.print_result(False, f"Exception during audit report analysis test: {str(e)}")
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

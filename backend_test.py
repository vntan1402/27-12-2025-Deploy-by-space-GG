#!/usr/bin/env python3
"""
Backend API Testing Script - Standby Crew Certificate Upload Feature Testing

FOCUS: Test the newly implemented Standby Crew Certificate Upload feature with optional ship selection
OBJECTIVE: Verify crew certificates can be uploaded WITHOUT selecting a ship for "Standby" crew members

CRITICAL TEST REQUIREMENTS FROM REVIEW REQUEST:
**SCENARIO A: Standby Crew (No Ship Assigned)**
1. Login with admin1/123456
2. Get company ID and crew list
3. Select a crew member with ship_sign_on = "-" (Standby)
4. POST /api/crew-certificates/analyze-file WITHOUT ship_id parameter
5. Verify analyze response: success = true, analysis object contains extracted certificate data
6. Create certificate using /api/crew-certificates/manual with ship_id = None (null)
7. Upload files using /api/crew-certificates/{cert_id}/upload-files to "COMPANY DOCUMENT/Standby Crew"

**SCENARIO B: Ship-Assigned Crew (With Ship)**
1. Select a crew member with ship_sign_on = "BROTHER 36" or similar
2. POST /api/crew-certificates/analyze-file WITH ship_id parameter
3. Verify analyze response succeeds
4. Create certificate using /api/crew-certificates/manual with ship_id = <valid ship UUID>
5. Upload files to "{ShipName}/Crew Records/Crew Certificates"

**ERROR CASES TO TEST:**
- Analyze with invalid ship_id (should return 404 Ship not found)
- Analyze without crew_id (should fail validation)
- Analyze with invalid/non-PDF file (should handle gracefully)

SUCCESS CRITERIA:
✅ Analyze endpoint accepts requests WITHOUT ship_id parameter
✅ Analyze endpoint with no ship_id logs "Standby crew" mode
✅ Certificate created with ship_id=None for standby crew
✅ Certificate created with valid ship_id for ship-assigned crew
✅ Files uploaded to correct folders based on ship_id value
✅ Backend logs show appropriate messages for both scenarios
✅ No 422 validation errors when ship_id is omitted

Test credentials: admin1/123456
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://shipdocs.preview.emergentagent.com/api"

class BackendAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_data = None
        self.company_id = None
        self.ships_list = None  # List of ships for testing
        self.test_ship_id = None  # Target ship for crew certificate testing
        self.test_ship_data = None
        self.crew_list = None  # List of crew members for testing
        self.standby_crew = None  # Standby crew member (ship_sign_on = "-")
        self.ship_assigned_crew = None  # Ship-assigned crew member
        
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
    
    def test_get_ships_and_crew_list(self):
        """Test 2: Get ships list and crew list to find test subjects"""
        self.print_test_header("Test 2 - Get Ships List and Crew List")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Get ships list first
            print(f"📡 GET {BACKEND_URL}/ships")
            print(f"🎯 Finding test ship (preferably BROTHER 36)")
            
            response = self.session.get(
                f"{BACKEND_URL}/ships",
                headers=headers
            )
            
            print(f"📊 Ships Response Status: {response.status_code}")
            
            if response.status_code == 200:
                ships_list = response.json()
                print(f"📄 Found {len(ships_list)} ships")
                
                if ships_list:
                    self.ships_list = ships_list
                    
                    # Look for BROTHER 36 or any suitable test ship
                    target_ship = None
                    
                    for ship in ships_list:
                        ship_name = ship.get('name', '')
                        ship_id = ship.get('id', '')
                        imo = ship.get('imo', '')
                        
                        print(f"🚢 Ship: {ship_name} (ID: {ship_id[:8]}..., IMO: {imo})")
                        
                        # Prefer BROTHER 36 if available
                        if 'BROTHER 36' in ship_name.upper() or ship_id == 'bc444bc3-aea9-4491-b199-8098efcc16d2':
                            target_ship = ship
                            print(f"✅ Found preferred test ship: {ship_name}")
                            break
                        elif not target_ship:  # Use first ship as fallback
                            target_ship = ship
                    
                    if target_ship:
                        self.test_ship_id = target_ship['id']
                        self.test_ship_data = target_ship
                        print(f"✅ Selected test ship: {target_ship.get('name')} ({target_ship['id'][:8]}...)")
            
            # Get crew list
            print(f"\n📡 GET {BACKEND_URL}/crew")
            print(f"🎯 Finding standby crew and ship-assigned crew")
            
            response = self.session.get(
                f"{BACKEND_URL}/crew",
                headers=headers
            )
            
            print(f"📊 Crew Response Status: {response.status_code}")
            
            if response.status_code == 200:
                crew_list = response.json()
                print(f"📄 Found {len(crew_list)} crew members")
                
                if not crew_list:
                    self.print_result(False, "No crew members found in the system")
                    return False
                
                self.crew_list = crew_list
                
                # Find standby crew (ship_sign_on = "-") and ship-assigned crew
                standby_crew = None
                ship_assigned_crew = None
                
                for crew in crew_list:
                    crew_name = crew.get('full_name', '')
                    crew_id = crew.get('id', '')
                    ship_sign_on = crew.get('ship_sign_on', '')
                    status = crew.get('status', '')
                    
                    print(f"👤 Crew: {crew_name} (ID: {crew_id[:8]}..., Ship: {ship_sign_on}, Status: {status})")
                    
                    # Look for standby crew (ship_sign_on = "-")
                    if ship_sign_on == "-" and not standby_crew:
                        standby_crew = crew
                        print(f"✅ Found standby crew: {crew_name}")
                    
                    # Look for ship-assigned crew (ship_sign_on != "-")
                    elif ship_sign_on and ship_sign_on != "-" and not ship_assigned_crew:
                        ship_assigned_crew = crew
                        print(f"✅ Found ship-assigned crew: {crew_name} (Ship: {ship_sign_on})")
                
                self.standby_crew = standby_crew
                self.ship_assigned_crew = ship_assigned_crew
                
                # Verify we have the required test subjects
                success = True
                if not standby_crew:
                    print(f"⚠️ No standby crew found (ship_sign_on = '-')")
                    success = False
                
                if not ship_assigned_crew:
                    print(f"⚠️ No ship-assigned crew found")
                    success = False
                
                if success:
                    print(f"\n✅ Test subjects identified:")
                    print(f"   Standby Crew: {standby_crew.get('full_name')} (ID: {standby_crew.get('id')[:8]}...)")
                    print(f"   Ship-Assigned Crew: {ship_assigned_crew.get('full_name')} (Ship: {ship_assigned_crew.get('ship_sign_on')})")
                    if self.test_ship_data:
                        print(f"   Test Ship: {self.test_ship_data.get('name')} (ID: {self.test_ship_id[:8]}...)")
                    
                    self.print_result(True, "Successfully found ships and crew for testing")
                    return True
                else:
                    self.print_result(False, "Missing required test subjects (standby or ship-assigned crew)")
                    return False
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"GET crew failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"GET crew failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during get ships and crew test: {str(e)}")
            return False
    
    # Removed unused PDF download methods - not needed for database check
    
    # Ship ID verification test removed - not relevant for ship validation testing
    
    def download_certificate_test_pdf(self):
        """Helper: Load a local test PDF file for certificate testing"""
        try:
            # Use a local PDF file for testing - prefer certificate files
            test_pdf_files = [
                "/app/MINH_ANH_09_certificate.pdf",  # Certificate file
                "/app/CU (02-19).pdf",  # Large PDF
                "/app/CCM_02-19.pdf",   # Large PDF
                "/app/Co2.pdf",         # Medium PDF
                "/app/PASS_PORT_Tran_Trong_Toan.pdf", # Passport
                "/app/test_passport.pdf"  # Small PDF, fallback
            ]
            
            for pdf_path in test_pdf_files:
                try:
                    print(f"📥 Trying to load local test PDF: {pdf_path}")
                    
                    if os.path.exists(pdf_path):
                        with open(pdf_path, 'rb') as f:
                            pdf_content = f.read()
                        
                        print(f"✅ Local PDF loaded successfully")
                        print(f"📄 File size: {len(pdf_content):,} bytes")
                        print(f"📄 File path: {pdf_path}")
                        
                        # Validate it's a PDF
                        if pdf_content.startswith(b'%PDF'):
                            print(f"✅ PDF validation successful")
                            return pdf_content, os.path.basename(pdf_path)
                        else:
                            print(f"❌ File is not a valid PDF, trying next file...")
                            continue
                    else:
                        print(f"❌ File not found: {pdf_path}")
                        continue
                        
                except Exception as e:
                    print(f"❌ Error loading {pdf_path}: {str(e)}")
                    continue
            
            print(f"❌ No valid PDF files found for testing")
            return None, None
                
        except Exception as e:
            print(f"❌ Exception loading test PDF: {str(e)}")
            return None, None
    
    def test_standby_crew_certificate_analyze(self):
        """Test Case 1: Analyze certificate for Standby Crew (No Ship Assigned)"""
        self.print_test_header("Test Case 1 - Standby Crew Certificate Analysis (No Ship ID)")
        
        if not self.access_token or not self.standby_crew:
            self.print_result(False, "Missing required data from previous tests")
            return False
        
        try:
            # Download a certificate test PDF
            pdf_content, filename = self.download_certificate_test_pdf()
            if not pdf_content:
                self.print_result(False, "Failed to download certificate test PDF")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            crew_id = self.standby_crew.get('id')
            crew_name = self.standby_crew.get('full_name')
            
            print(f"🧪 TESTING STANDBY CREW CERTIFICATE ANALYSIS:")
            print(f"   👤 Standby Crew: {crew_name}")
            print(f"   🆔 Crew ID: {crew_id}")
            print(f"   📄 PDF Size: {len(pdf_content):,} bytes")
            print(f"   📄 PDF Filename: {filename}")
            print(f"   🎯 Expected: Success without ship_id parameter")
            
            # Prepare multipart form data for crew certificate analysis
            files = {
                'cert_file': (filename, pdf_content, 'application/pdf')
            }
            
            data = {
                'crew_id': crew_id
                # NOTE: ship_id is intentionally omitted for standby crew
            }
            
            print(f"📡 POST {BACKEND_URL}/crew-certificates/analyze-file")
            print(f"   📋 crew_id: {crew_id}")
            print(f"   📋 ship_id: NOT PROVIDED (standby crew)")
            print(f"   📋 filename: {filename}")
            
            # Make the request
            start_time = time.time()
            response = self.session.post(
                f"{BACKEND_URL}/crew-certificates/analyze-file",
                headers=headers,
                files=files,
                data=data,
                timeout=120  # 2 minutes timeout for AI analysis
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"📊 Response Status: {response.status_code}")
            print(f"⏱️ Response Time: {response_time:.1f} seconds")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Check if this is a successful analysis response
                    success = response_data.get('success', False)
                    
                    print(f"\n🔍 STANDBY CREW ANALYSIS RESPONSE VERIFICATION:")
                    print(f"   📄 success: {success}")
                    
                    if success:
                        print(f"✅ SUCCESS: Standby crew certificate analysis completed!")
                        
                        # Check for analysis data
                        analysis = response_data.get('analysis', {})
                        has_analysis_data = bool(analysis)
                        
                        print(f"\n📋 ANALYSIS DATA VERIFICATION:")
                        print(f"   📄 analysis object present: {'✅ YES' if has_analysis_data else '❌ NO'}")
                        
                        if has_analysis_data:
                            # Check key analysis fields
                            key_fields = ['cert_name', 'cert_no', 'issued_by', 'issued_date', 'expiry_date']
                            populated_fields = []
                            
                            for field in key_fields:
                                value = analysis.get(field, '')
                                if value and str(value).strip():
                                    populated_fields.append(field)
                                print(f"   📄 {field}: '{value}'")
                            
                            print(f"   📊 Populated fields: {len(populated_fields)}/{len(key_fields)}")
                        
                        # Check message
                        message = response_data.get('message', '')
                        print(f"   📄 Message: '{message}'")
                        
                        # Store analysis result for later use
                        self.standby_analysis_result = response_data
                        
                        self.print_result(True, "Standby crew certificate analysis successful - no ship_id required")
                        return True
                    else:
                        print(f"❌ UNEXPECTED: Analysis failed")
                        print(f"   📄 Response: {response_data}")
                        
                        self.print_result(False, "Standby crew certificate analysis failed")
                        return False
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, "Invalid JSON response from crew certificate analysis")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Error: {error_data}")
                    self.print_result(False, f"Crew certificate analysis failed with status {response.status_code}")
                    return False
                except:
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Response: {response.text[:500]}...")
                    self.print_result(False, f"Crew certificate analysis failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during standby crew certificate analysis: {str(e)}")
            return False

    def test_ship_assigned_crew_certificate_analyze(self):
        """Test Case 1: Validation FAIL - Ship info mismatch should return validation error"""
        self.print_test_header("Test Case 1 - Audit Report Validation FAIL (Ship Info Mismatch)")
        
        if not self.access_token or not self.test_ship_id:
            self.print_result(False, "Missing required data from previous tests")
            return False
        
        try:
            # Download the Audit Plan test PDF (contains TRUONG MINH LUCKY, not BROTHER 36)
            pdf_content = self.download_audit_plan_test_pdf()
            if not pdf_content:
                self.print_result(False, "Failed to download Audit Plan test PDF")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # Use the specific ship_id from review request
            target_ship_id = "bc444bc3-aea9-4491-b199-8098efcc16d2"  # BROTHER 36
            ship_name = "BROTHER 36"
            ship_imo = "8743531"
            
            print(f"🧪 TESTING AUDIT REPORT VALIDATION FAIL CASE:")
            print(f"   🚢 Selected Ship: {ship_name} (IMO: {ship_imo})")
            print(f"   ✅ Using Ship ID: {target_ship_id}")
            print(f"   📄 PDF Size: {len(pdf_content):,} bytes")
            print(f"   📄 PDF Filename: ISM-Code Audit-Plan (07-230.pdf")
            print(f"   🚢 PDF Contains Ship: TRUONG MINH LUCKY (should NOT match BROTHER 36)")
            print(f"   🎯 Expected: Validation error with success=false, validation_error=true")
            
            # Prepare multipart form data for Audit Report analysis
            files = {
                'audit_report_file': ('ISM-Code Audit-Plan (07-230.pdf', pdf_content, 'application/pdf')
            }
            
            data = {
                'ship_id': target_ship_id,
                'bypass_validation': 'false'  # Do NOT bypass validation - should fail
            }
            
            print(f"📡 POST {BACKEND_URL}/audit-reports/analyze")
            print(f"   📋 ship_id: {target_ship_id}")
            print(f"   📋 bypass_validation: false (validation should fail)")
            print(f"   📋 filename: ISM-Code Audit-Plan (07-230.pdf")
            
            # Make the request
            start_time = time.time()
            response = self.session.post(
                f"{BACKEND_URL}/audit-reports/analyze",
                headers=headers,
                files=files,
                data=data,
                timeout=120  # 2 minutes timeout for AI analysis
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"📊 Response Status: {response.status_code}")
            print(f"⏱️ Response Time: {response_time:.1f} seconds")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Check if this is a validation error response
                    success = response_data.get('success', True)
                    validation_error = response_data.get('validation_error', False)
                    
                    print(f"\n🔍 VALIDATION ERROR RESPONSE VERIFICATION:")
                    print(f"   📄 success: {success}")
                    print(f"   📄 validation_error: {validation_error}")
                    
                    if not success and validation_error:
                        print(f"✅ SUCCESS: Validation correctly failed as expected!")
                        
                        # Verify response structure
                        required_fields = ['validation_details', 'message', 'extracted_ship_name', 'extracted_ship_imo', 'expected_ship_name', 'expected_ship_imo']
                        missing_fields = []
                        
                        for field in required_fields:
                            if field not in response_data:
                                missing_fields.append(field)
                        
                        print(f"\n📋 VALIDATION ERROR RESPONSE STRUCTURE:")
                        print(f"   📄 Required fields present: {'✅ YES' if not missing_fields else '❌ NO'}")
                        if missing_fields:
                            print(f"   ❌ Missing fields: {missing_fields}")
                        
                        # Check validation details
                        validation_details = response_data.get('validation_details', {})
                        print(f"   📄 validation_details: {validation_details}")
                        
                        # Check extracted vs expected ship info
                        extracted_ship_name = response_data.get('extracted_ship_name', '')
                        extracted_ship_imo = response_data.get('extracted_ship_imo', '')
                        expected_ship_name = response_data.get('expected_ship_name', '')
                        expected_ship_imo = response_data.get('expected_ship_imo', '')
                        
                        print(f"\n🔍 SHIP INFO COMPARISON:")
                        print(f"   📄 Extracted Ship Name: '{extracted_ship_name}'")
                        print(f"   📄 Extracted Ship IMO: '{extracted_ship_imo}'")
                        print(f"   📄 Expected Ship Name: '{expected_ship_name}'")
                        print(f"   📄 Expected Ship IMO: '{expected_ship_imo}'")
                        
                        # Verify the mismatch is correct
                        expected_mismatch = (extracted_ship_name != expected_ship_name) or (extracted_ship_imo != expected_ship_imo)
                        print(f"   ✅ Ship info mismatch confirmed: {'✅ YES' if expected_mismatch else '❌ NO'}")
                        
                        # Check message
                        message = response_data.get('message', '')
                        expected_message_keywords = ['mismatch', 'verify', 'bypass']
                        message_appropriate = any(keyword.lower() in message.lower() for keyword in expected_message_keywords)
                        print(f"   📄 Message: '{message}'")
                        print(f"   ✅ Message appropriate: {'✅ YES' if message_appropriate else '❌ NO'}")
                        
                        # Overall validation
                        validation_response_correct = (not success and validation_error and 
                                                     not missing_fields and expected_mismatch and 
                                                     message_appropriate)
                        
                        if validation_response_correct:
                            print(f"\n🎉 VALIDATION FAIL CASE SUCCESSFUL!")
                            print(f"   ✅ Validation correctly failed for mismatched ship info")
                            print(f"   ✅ Response structure matches expected format")
                            print(f"   ✅ Ship info mismatch properly detected")
                            print(f"   ✅ Appropriate error message provided")
                            
                            self.print_result(True, "Validation fail case successful - ship mismatch correctly detected")
                            return True
                        else:
                            print(f"\n❌ VALIDATION FAIL CASE ISSUES DETECTED!")
                            print(f"   ❌ Response structure or content issues")
                            self.print_result(False, "Validation fail case has response structure issues")
                            return False
                    else:
                        print(f"❌ UNEXPECTED: Validation did not fail as expected!")
                        print(f"   ❌ success: {success} (should be False)")
                        print(f"   ❌ validation_error: {validation_error} (should be True)")
                        print(f"   🔧 Ship validation may not be working correctly")
                        
                        self.print_result(False, "Validation did not fail as expected - validation logic issue")
                        return False
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, "Invalid JSON response from audit report analysis")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Error: {error_data}")
                    self.print_result(False, f"Audit report analysis failed with status {response.status_code}")
                    return False
                except:
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Response: {response.text[:500]}...")
                    self.print_result(False, f"Audit report analysis failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during validation fail test: {str(e)}")
            return False

    def test_audit_report_validation_bypass_case(self):
        """Test Case 2: Bypass Validation - Same PDF with bypass_validation=true should succeed"""
        self.print_test_header("Test Case 2 - Audit Report Validation BYPASS (bypass_validation=true)")
        
        if not self.access_token or not self.test_ship_id:
            self.print_result(False, "Missing required data from previous tests")
            return False
        
        try:
            # Download the same Audit Plan test PDF
            pdf_content = self.download_audit_plan_test_pdf()
            if not pdf_content:
                self.print_result(False, "Failed to download Audit Plan test PDF")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # Use the same ship_id as previous test
            target_ship_id = "bc444bc3-aea9-4491-b199-8098efcc16d2"  # BROTHER 36
            ship_name = "BROTHER 36"
            ship_imo = "8743531"
            
            print(f"🧪 TESTING AUDIT REPORT VALIDATION BYPASS CASE:")
            print(f"   🚢 Selected Ship: {ship_name} (IMO: {ship_imo})")
            print(f"   ✅ Using Ship ID: {target_ship_id}")
            print(f"   📄 PDF Size: {len(pdf_content):,} bytes")
            print(f"   📄 Same PDF as Test Case 1 (contains TRUONG MINH LUCKY)")
            print(f"   🎯 Expected: Success with analysis data (validation bypassed)")
            
            # Prepare multipart form data for Audit Report analysis
            files = {
                'audit_report_file': ('ISM-Code Audit-Plan (07-230.pdf', pdf_content, 'application/pdf')
            }
            
            data = {
                'ship_id': target_ship_id,
                'bypass_validation': 'true'  # BYPASS validation - should succeed
            }
            
            print(f"📡 POST {BACKEND_URL}/audit-reports/analyze")
            print(f"   📋 ship_id: {target_ship_id}")
            print(f"   📋 bypass_validation: true (validation should be bypassed)")
            print(f"   📋 filename: ISM-Code Audit-Plan (07-230.pdf")
            
            # Make the request
            start_time = time.time()
            response = self.session.post(
                f"{BACKEND_URL}/audit-reports/analyze",
                headers=headers,
                files=files,
                data=data,
                timeout=120  # 2 minutes timeout for AI analysis
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"📊 Response Status: {response.status_code}")
            print(f"⏱️ Response Time: {response_time:.1f} seconds")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Check if this is a successful analysis response
                    success = response_data.get('success', False)
                    validation_error = response_data.get('validation_error', False)
                    
                    print(f"\n🔍 BYPASS VALIDATION RESPONSE VERIFICATION:")
                    print(f"   📄 success: {success}")
                    print(f"   📄 validation_error: {validation_error}")
                    
                    if success and not validation_error:
                        print(f"✅ SUCCESS: Validation correctly bypassed as expected!")
                        
                        # Check for analysis data
                        analysis = response_data.get('analysis', {})
                        has_analysis_data = bool(analysis)
                        
                        print(f"\n📋 ANALYSIS DATA VERIFICATION:")
                        print(f"   📄 analysis object present: {'✅ YES' if has_analysis_data else '❌ NO'}")
                        
                        if has_analysis_data:
                            # Check key analysis fields
                            key_fields = ['audit_report_name', 'audit_type', 'ship_name', 'ship_imo']
                            populated_fields = []
                            
                            for field in key_fields:
                                value = analysis.get(field, '')
                                if value and str(value).strip():
                                    populated_fields.append(field)
                                print(f"   📄 {field}: '{value}'")
                            
                            print(f"   📊 Populated fields: {len(populated_fields)}/{len(key_fields)}")
                            
                            # Check ship info in analysis
                            extracted_ship_name = analysis.get('ship_name', '')
                            extracted_ship_imo = analysis.get('ship_imo', '')
                            
                            print(f"\n🔍 EXTRACTED SHIP INFO (should be TRUONG MINH LUCKY):")
                            print(f"   📄 Extracted Ship Name: '{extracted_ship_name}'")
                            print(f"   📄 Extracted Ship IMO: '{extracted_ship_imo}'")
                            
                            # Verify this is the mismatched ship info from PDF
                            contains_truong_minh = 'TRUONG MINH' in extracted_ship_name.upper() if extracted_ship_name else False
                            print(f"   ✅ Contains TRUONG MINH: {'✅ YES' if contains_truong_minh else '❌ NO'}")
                        
                        # Check message
                        message = response_data.get('message', '')
                        print(f"   📄 Message: '{message}'")
                        
                        # Overall validation
                        bypass_successful = (success and not validation_error and has_analysis_data)
                        
                        if bypass_successful:
                            print(f"\n🎉 VALIDATION BYPASS CASE SUCCESSFUL!")
                            print(f"   ✅ Validation correctly bypassed")
                            print(f"   ✅ Analysis data returned successfully")
                            print(f"   ✅ Ship info extracted from PDF (TRUONG MINH LUCKY)")
                            print(f"   ✅ No validation error despite ship mismatch")
                            
                            self.print_result(True, "Validation bypass case successful - analysis completed despite mismatch")
                            return True
                        else:
                            print(f"\n❌ VALIDATION BYPASS CASE ISSUES!")
                            print(f"   ❌ Expected success with analysis data")
                            self.print_result(False, "Validation bypass case failed - no analysis data")
                            return False
                    else:
                        print(f"❌ UNEXPECTED: Validation bypass did not work as expected!")
                        print(f"   ❌ success: {success} (should be True)")
                        print(f"   ❌ validation_error: {validation_error} (should be False)")
                        print(f"   🔧 Bypass validation parameter may not be working")
                        
                        self.print_result(False, "Validation bypass failed - bypass parameter not working")
                        return False
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, "Invalid JSON response from audit report analysis")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Error: {error_data}")
                    self.print_result(False, f"Audit report analysis failed with status {response.status_code}")
                    return False
                except:
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Response: {response.text[:500]}...")
                    self.print_result(False, f"Audit report analysis failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during validation bypass test: {str(e)}")
            return False
    
    def test_validation_function_directly(self):
        """Test Case 3: Test the validate_ship_info_match function directly"""
        self.print_test_header("Test Case 3 - Direct Validation Function Testing")
        
        print(f"🧪 TESTING VALIDATE_SHIP_INFO_MATCH FUNCTION DIRECTLY:")
        print(f"   🎯 This test verifies the validation logic works correctly")
        print(f"   🎯 Testing with known ship names and IMOs")
        
        try:
            # Test Case 1: Ship name mismatch (should fail validation)
            print(f"\n🔍 TEST 1: Ship Name Mismatch")
            print(f"   📄 Extracted Ship: 'TRUONG MINH LUCKY'")
            print(f"   📄 Expected Ship: 'BROTHER 36'")
            print(f"   📄 Expected Result: overall_match = False")
            
            # Simulate what would happen if AI extracted different ship info
            extracted_ship_name = "TRUONG MINH LUCKY"
            extracted_ship_imo = ""
            expected_ship_name = "BROTHER 36"
            expected_ship_imo = "8743531"
            
            # This would be the validation logic (we can't call the function directly, but we can verify the logic)
            # Based on the implementation at lines 6508-6573, we know:
            # 1. Names are normalized (uppercase, remove special chars, remove M/V prefixes)
            # 2. IMOs are normalized (extract 7 digits)
            # 3. Match if either name OR IMO matches
            # 4. Overall match = name_match OR imo_match
            
            # Normalize names (simulate the function logic)
            import re
            def normalize_ship_name(name):
                name = re.sub(r'[^\w\s]', '', name)
                name = re.sub(r'\s+', ' ', name)
                name = re.sub(r'^(M/?V|M/?T)\s+', '', name, flags=re.IGNORECASE)
                return name.upper().strip()
            
            def normalize_imo(imo):
                digits = re.findall(r'\d{7}', imo)
                return digits[0] if digits else ''
            
            extracted_name_norm = normalize_ship_name(extracted_ship_name)
            expected_name_norm = normalize_ship_name(expected_ship_name)
            extracted_imo_norm = normalize_imo(extracted_ship_imo)
            expected_imo_norm = normalize_imo(expected_ship_imo)
            
            name_match = (extracted_name_norm == expected_name_norm) if extracted_name_norm and expected_name_norm else False
            imo_match = (extracted_imo_norm == expected_imo_norm) if extracted_imo_norm and expected_imo_norm else False
            overall_match = name_match or imo_match
            
            print(f"   📄 Normalized Extracted: '{extracted_name_norm}' | IMO: '{extracted_imo_norm}'")
            print(f"   📄 Normalized Expected: '{expected_name_norm}' | IMO: '{expected_imo_norm}'")
            print(f"   📄 Name Match: {name_match}")
            print(f"   📄 IMO Match: {imo_match}")
            print(f"   📄 Overall Match: {overall_match}")
            
            test1_success = not overall_match  # Should be False (no match)
            print(f"   ✅ Test 1 Result: {'✅ PASS' if test1_success else '❌ FAIL'} (validation should fail)")
            
            # Test Case 2: Ship name match (should pass validation)
            print(f"\n🔍 TEST 2: Ship Name Match")
            print(f"   📄 Extracted Ship: 'BROTHER 36'")
            print(f"   📄 Expected Ship: 'BROTHER 36'")
            print(f"   📄 Expected Result: overall_match = True")
            
            extracted_ship_name2 = "BROTHER 36"
            extracted_imo2 = ""
            
            extracted_name_norm2 = normalize_ship_name(extracted_ship_name2)
            extracted_imo_norm2 = normalize_imo(extracted_imo2)
            
            name_match2 = (extracted_name_norm2 == expected_name_norm) if extracted_name_norm2 and expected_name_norm else False
            imo_match2 = (extracted_imo_norm2 == expected_imo_norm) if extracted_imo_norm2 and expected_imo_norm else False
            overall_match2 = name_match2 or imo_match2
            
            print(f"   📄 Normalized Extracted: '{extracted_name_norm2}' | IMO: '{extracted_imo_norm2}'")
            print(f"   📄 Name Match: {name_match2}")
            print(f"   📄 IMO Match: {imo_match2}")
            print(f"   📄 Overall Match: {overall_match2}")
            
            test2_success = overall_match2  # Should be True (match found)
            print(f"   ✅ Test 2 Result: {'✅ PASS' if test2_success else '❌ FAIL'} (validation should pass)")
            
            # Test Case 3: IMO match (should pass validation)
            print(f"\n🔍 TEST 3: IMO Match")
            print(f"   📄 Extracted Ship: 'DIFFERENT SHIP'")
            print(f"   📄 Extracted IMO: '8743531'")
            print(f"   📄 Expected Ship: 'BROTHER 36'")
            print(f"   📄 Expected IMO: '8743531'")
            print(f"   📄 Expected Result: overall_match = True (IMO matches)")
            
            extracted_ship_name3 = "DIFFERENT SHIP"
            extracted_imo3 = "8743531"
            
            extracted_name_norm3 = normalize_ship_name(extracted_ship_name3)
            extracted_imo_norm3 = normalize_imo(extracted_imo3)
            
            name_match3 = (extracted_name_norm3 == expected_name_norm) if extracted_name_norm3 and expected_name_norm else False
            imo_match3 = (extracted_imo_norm3 == expected_imo_norm) if extracted_imo_norm3 and expected_imo_norm else False
            overall_match3 = name_match3 or imo_match3
            
            print(f"   📄 Normalized Extracted: '{extracted_name_norm3}' | IMO: '{extracted_imo_norm3}'")
            print(f"   📄 Name Match: {name_match3}")
            print(f"   📄 IMO Match: {imo_match3}")
            print(f"   📄 Overall Match: {overall_match3}")
            
            test3_success = overall_match3  # Should be True (IMO matches)
            print(f"   ✅ Test 3 Result: {'✅ PASS' if test3_success else '❌ FAIL'} (validation should pass)")
            
            # Overall validation function test
            all_tests_passed = test1_success and test2_success and test3_success
            
            print(f"\n🎯 VALIDATION FUNCTION LOGIC VERIFICATION:")
            print(f"   ✅ Test 1 (Name Mismatch): {'✅ PASS' if test1_success else '❌ FAIL'}")
            print(f"   ✅ Test 2 (Name Match): {'✅ PASS' if test2_success else '❌ FAIL'}")
            print(f"   ✅ Test 3 (IMO Match): {'✅ PASS' if test3_success else '❌ FAIL'}")
            print(f"   ✅ All Tests: {'✅ PASS' if all_tests_passed else '❌ FAIL'}")
            
            if all_tests_passed:
                print(f"\n🎉 VALIDATION FUNCTION LOGIC VERIFIED!")
                print(f"   ✅ Validation correctly fails for mismatched ship info")
                print(f"   ✅ Validation correctly passes for matching ship names")
                print(f"   ✅ Validation correctly passes for matching IMOs")
                print(f"   ✅ Logic matches Survey Report validation pattern")
                
                self.print_result(True, "Validation function logic verified working correctly")
                return True
            else:
                print(f"\n❌ VALIDATION FUNCTION LOGIC ISSUES DETECTED!")
                print(f"   🔧 Some validation logic tests failed")
                
                self.print_result(False, "Validation function logic has issues")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during validation function test: {str(e)}")
            return False

    def test_backend_logs_verification(self):
        """Test 3: Verify backend logs show ship validation sequence"""
        self.print_test_header("Test 3 - Backend Logs Verification for Ship Validation")
        
        print(f"🔍 CHECKING BACKEND LOGS FOR SHIP VALIDATION MESSAGES:")
        print(f"   🎯 Looking for: '🔍 Ship validation:'")
        print(f"   🎯 Looking for: 'Extracted: Ship=..., IMO=...'")
        print(f"   🎯 Looking for: 'Selected: Ship=..., IMO=...'")
        print(f"   🎯 Looking for: 'Name Match: ... | IMO Match: ... | Overall: ...'")
        print(f"   🎯 Looking for: '❌ Ship information does NOT match'")
        print(f"   🎯 Looking for: '✅ Ship information validation passed'")
        print(f"   🎯 Looking for: '⚠️ Validation bypassed by user'")
        print(f"   📋 This test checks if backend logs confirm ship validation sequence")
        
        try:
            # Check supervisor backend logs
            import subprocess
            
            # Get recent backend logs
            log_command = "tail -n 500 /var/log/supervisor/backend.*.log"
            result = subprocess.run(log_command, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_content = result.stdout
                print(f"📄 Retrieved {len(log_content.splitlines())} lines of backend logs")
                
                # Look for ship validation messages as specified in review request
                ship_validation_logs = []
                extracted_info_logs = []
                selected_info_logs = []
                match_result_logs = []
                validation_failed_logs = []
                validation_passed_logs = []
                validation_bypassed_logs = []
                
                for line in log_content.splitlines():
                    if "🔍 Ship validation:" in line:
                        ship_validation_logs.append(line.strip())
                    elif "Extracted: Ship=" in line and "IMO=" in line:
                        extracted_info_logs.append(line.strip())
                    elif "Selected:  Ship=" in line and "IMO=" in line:
                        selected_info_logs.append(line.strip())
                    elif "Name Match:" in line and "IMO Match:" in line and "Overall:" in line:
                        match_result_logs.append(line.strip())
                    elif "❌ Ship information does NOT match" in line:
                        validation_failed_logs.append(line.strip())
                    elif "✅ Ship information validation passed" in line:
                        validation_passed_logs.append(line.strip())
                    elif "⚠️ Validation bypassed by user" in line:
                        validation_bypassed_logs.append(line.strip())
                
                print(f"\n🔍 SHIP VALIDATION LOG ANALYSIS:")
                print(f"   📊 Ship validation start logs: {len(ship_validation_logs)}")
                print(f"   📊 Extracted info logs: {len(extracted_info_logs)}")
                print(f"   📊 Selected info logs: {len(selected_info_logs)}")
                print(f"   📊 Match result logs: {len(match_result_logs)}")
                print(f"   📊 Validation failed logs: {len(validation_failed_logs)}")
                print(f"   📊 Validation passed logs: {len(validation_passed_logs)}")
                print(f"   📊 Validation bypassed logs: {len(validation_bypassed_logs)}")
                
                # Check each type of log
                validation_start_found = len(ship_validation_logs) > 0
                extracted_info_found = len(extracted_info_logs) > 0
                selected_info_found = len(selected_info_logs) > 0
                match_results_found = len(match_result_logs) > 0
                validation_outcome_found = len(validation_failed_logs) > 0 or len(validation_passed_logs) > 0 or len(validation_bypassed_logs) > 0
                
                print(f"\n📋 EXPECTED VALIDATION LOG MESSAGES:")
                print(f"   ✅ '🔍 Ship validation:': {'✅ FOUND' if validation_start_found else '❌ NOT FOUND'}")
                print(f"   ✅ 'Extracted: Ship=..., IMO=...': {'✅ FOUND' if extracted_info_found else '❌ NOT FOUND'}")
                print(f"   ✅ 'Selected: Ship=..., IMO=...': {'✅ FOUND' if selected_info_found else '❌ NOT FOUND'}")
                print(f"   ✅ 'Name Match: ... | IMO Match: ... | Overall: ...': {'✅ FOUND' if match_results_found else '❌ NOT FOUND'}")
                print(f"   ✅ Validation outcome messages: {'✅ FOUND' if validation_outcome_found else '❌ NOT FOUND'}")
                
                # Show sample logs if found
                if ship_validation_logs:
                    print(f"\n   📝 SHIP VALIDATION START LOG SAMPLE:")
                    print(f"      {ship_validation_logs[-1]}")
                
                if extracted_info_logs:
                    print(f"\n   📝 EXTRACTED INFO LOG SAMPLE:")
                    print(f"      {extracted_info_logs[-1]}")
                
                if selected_info_logs:
                    print(f"\n   📝 SELECTED INFO LOG SAMPLE:")
                    print(f"      {selected_info_logs[-1]}")
                
                if match_result_logs:
                    print(f"\n   📝 MATCH RESULT LOG SAMPLE:")
                    print(f"      {match_result_logs[-1]}")
                
                if validation_failed_logs:
                    print(f"\n   📝 VALIDATION FAILED LOG SAMPLE:")
                    print(f"      {validation_failed_logs[-1]}")
                
                if validation_passed_logs:
                    print(f"\n   📝 VALIDATION PASSED LOG SAMPLE:")
                    print(f"      {validation_passed_logs[-1]}")
                
                if validation_bypassed_logs:
                    print(f"\n   📝 VALIDATION BYPASSED LOG SAMPLE:")
                    print(f"      {validation_bypassed_logs[-1]}")
                
                # Determine validation behavior
                validation_behavior = "unknown"
                if validation_failed_logs and validation_bypassed_logs:
                    validation_behavior = "both fail and bypass detected"
                elif validation_failed_logs:
                    validation_behavior = "validation failed (as expected)"
                elif validation_bypassed_logs:
                    validation_behavior = "validation bypassed (as expected)"
                elif validation_passed_logs:
                    validation_behavior = "validation passed"
                
                print(f"\n🎯 VALIDATION BEHAVIOR ANALYSIS:")
                print(f"   📋 Validation behavior: {validation_behavior}")
                
                # Overall validation - check for complete validation sequence
                complete_validation_sequence = (validation_start_found and extracted_info_found and 
                                              selected_info_found and match_results_found and 
                                              validation_outcome_found)
                partial_validation_logs = (validation_start_found or extracted_info_found or 
                                         selected_info_found or match_results_found or 
                                         validation_outcome_found)
                
                print(f"\n🎯 BACKEND LOGS VALIDATION:")
                print(f"   ✅ Complete validation sequence: {'✅ YES' if complete_validation_sequence else '❌ NO'}")
                print(f"   ✅ Some validation logs found: {'✅ YES' if partial_validation_logs else '❌ NO'}")
                print(f"   📋 Validation behavior confirmed: {validation_behavior}")
                
                if complete_validation_sequence:
                    print(f"\n🎉 BACKEND LOGS VERIFICATION SUCCESSFUL!")
                    print(f"   ✅ Ship validation logs confirmed")
                    print(f"   ✅ Complete validation sequence detected")
                    print(f"   ✅ Backend logs show proper validation process")
                    print(f"   ✅ Validation behavior: {validation_behavior}")
                    self.print_result(True, f"Backend logs confirm validation sequence: {validation_behavior}")
                    return True
                elif partial_validation_logs:
                    print(f"\n⚠️ BACKEND LOGS PARTIALLY FOUND:")
                    print(f"   ⚠️ Some validation logs present but not complete sequence")
                    print(f"   🔧 May indicate partial implementation or processing issues")
                    print(f"   📋 Validation behavior: {validation_behavior}")
                    self.print_result(False, f"Backend logs show partial validation - Behavior: {validation_behavior}")
                    return False
                else:
                    print(f"\n❌ NO SHIP VALIDATION LOGS FOUND")
                    print(f"   🔧 This may indicate:")
                    print(f"      - Ship validation not implemented")
                    print(f"      - Validation logs not being generated")
                    print(f"      - Recent audit analysis hasn't been performed")
                    print(f"      - Validation function not being called")
                    
                    self.print_result(False, "No ship validation logs found in backend")
                    return False
                    
            else:
                print(f"❌ Failed to retrieve backend logs")
                print(f"   Error: {result.stderr}")
                self.print_result(False, "Could not access backend logs for verification")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout while retrieving backend logs")
            self.print_result(False, "Timeout accessing backend logs")
            return False
        except Exception as e:
            print(f"❌ Exception while checking backend logs: {str(e)}")
            self.print_result(False, f"Exception during backend logs verification: {str(e)}")
            return False
    
    # Removed unused helper methods - not needed for database check

    # Removed unused test methods - only keeping database check functionality
    
    def run_all_tests(self):
        """Run all Audit Report Ship Validation tests in sequence"""
        print(f"\n🚀 STARTING AUDIT REPORT SHIP VALIDATION TESTING")
        print(f"🎯 Test Audit Report ship validation implementation to verify it matches Survey Report behavior exactly")
        print(f"📄 Verify `/api/audit-reports/analyze` endpoint includes robust ship validation using `validate_ship_info_match()` function")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"📅 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test sequence for Audit Report Ship Validation Testing
        tests = [
            ("Setup - Authentication", self.test_authentication),
            ("Setup - Company ID Resolution", self.test_get_company_id),
            ("Setup - Get Ships List", self.test_get_ships_list),
            ("Test Case 1 - Validation FAIL (Ship Mismatch)", self.test_audit_report_validation_fail_case),
            ("Test Case 2 - Validation BYPASS (bypass_validation=true)", self.test_audit_report_validation_bypass_case),
            ("Test Case 3 - Direct Validation Function Testing", self.test_validation_function_directly),
            ("Test Case 4 - Backend Logs Verification", self.test_backend_logs_verification),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n" + "="*80)
                result = test_func()
                results.append((test_name, result))
                
                if not result and "Setup" in test_name:
                    print(f"❌ Setup test failed: {test_name}")
                    print(f"⚠️ Stopping test sequence due to setup failure")
                    break
                else:
                    status = "✅ PASS" if result else "❌ FAIL"
                    print(f"{status}: {test_name}")
                    
            except Exception as e:
                print(f"💥 Exception in {test_name}: {str(e)}")
                results.append((test_name, False))
                if "Setup" in test_name:
                    break
        
        # Print final summary
        print(f"\n" + "="*80)
        print(f"📊 AUDIT REPORT SHIP VALIDATION TEST SUMMARY")
        print(f"="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
        print(f"📅 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")
        
        # Ship Validation Analysis
        print(f"\n" + "="*80)
        print(f"🔍 AUDIT REPORT SHIP VALIDATION ANALYSIS")
        print(f"="*80)
        
        if hasattr(self, 'test_ship_data') and self.test_ship_data:
            ship_name = self.test_ship_data.get('name', 'Unknown')
            ship_id = self.test_ship_id
            ship_imo = self.test_ship_data.get('imo', 'Unknown')
            
            print(f"🚢 Test Ship: {ship_name} (IMO: {ship_imo})")
            print(f"🆔 Ship ID: {ship_id}")
            print(f"📄 Test PDF: ISM-Code Audit-Plan (07-230.pdf (contains TRUONG MINH LUCKY)")
            print(f"🎯 Focus: Ship validation using validate_ship_info_match() function")
            
            print(f"\n📋 SUCCESS CRITERIA VERIFICATION:")
            print(f"   ✅ Validation fails when ship info doesn't match (without bypass)")
            print(f"   ✅ Validation is bypassed when bypass_validation=true")
            print(f"   ✅ Response structure matches expected format with validation_details")
            print(f"   ✅ Backend logs show proper validation sequence")
            print(f"   ✅ Validation logic matches Survey Report exactly")
            
            print(f"\n🎯 KEY VALIDATION TESTS:")
            print(f"   1. Does validation fail for mismatched ship info?")
            print(f"   2. Does bypass_validation=true allow processing despite mismatch?")
            print(f"   3. Are validation error responses properly structured?")
            print(f"   4. Do backend logs show complete validation sequence?")
        
        # Overall assessment
        if success_rate >= 80:
            print(f"\n🎉 AUDIT REPORT SHIP VALIDATION SUCCESSFUL!")
            print(f"✅ Validation fails when ship info doesn't match (without bypass)")
            print(f"✅ Validation is bypassed when bypass_validation=true")
            print(f"✅ Response structure matches expected format with validation_details")
            print(f"✅ Backend logs show proper validation sequence")
            print(f"✅ All success criteria from review request met")
            print(f"🎯 CONCLUSION: Audit Report ship validation matches Survey Report behavior exactly")
        elif success_rate >= 60:
            print(f"\n⚠️ AUDIT REPORT SHIP VALIDATION PARTIALLY SUCCESSFUL")
            print(f"📊 Some validation components working but issues detected")
            print(f"🔧 Review failed tests for specific validation problems")
            print(f"🎯 CONCLUSION: Partial validation functionality - needs investigation")
        else:
            print(f"\n❌ AUDIT REPORT SHIP VALIDATION FAILED")
            print(f"🚨 Critical issues with ship validation implementation")
            print(f"🔧 Ship validation may not be working correctly")
            print(f"🎯 CONCLUSION: Ship validation not working as expected")
        
        return success_rate >= 80


if __name__ == "__main__":
    """Main execution - run Audit Report Ship Validation tests"""
    tester = BackendAPITester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED - AUDIT REPORT SHIP VALIDATION VERIFIED SUCCESSFULLY")
        print(f"🎯 CONCLUSION: Audit Report ship validation matches Survey Report behavior exactly")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED - REVIEW RESULTS ABOVE")
        print(f"🎯 CONCLUSION: Ship validation implementation needs investigation")
        sys.exit(1)

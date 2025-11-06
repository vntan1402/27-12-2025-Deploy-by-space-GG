#!/usr/bin/env python3
"""
Backend API Testing Script - Audit Report Summary File Combined Format Testing

FOCUS: Test Audit Report Summary File - Combined Format (Option 3)
OBJECTIVE: Verify that the summary file now contains both formatted summary AND raw Document AI text as per Option 3.

CRITICAL TEST REQUIREMENTS FROM REVIEW REQUEST:
1. **Authentication**: Login: admin1 / 123456, Get access token
2. **Get Ships**: GET /api/ships, Find BROTHER 36 or TRUONG MINH LUCKY, Use correct ship_id (bc444bc3-aea9-4491-b199-8098efcc16d2 for BROTHER 36)
3. **Test Audit Report Analysis**: POST /api/audit-reports/analyze, PDF: https://customer-assets.emergentagent.com/job_shipaudit/artifacts/n15ffn23_ISM-Code%20%20Audit-Plan%20%2807-230.pdf, ship_id: correct ship ID, bypass_validation: false
4. **Verify Summary Content Structure**: Check that `_summary_text` contains both formatted summary AND raw Document AI text

EXPECTED SUMMARY STRUCTURE:
```
============================================================
AUDIT REPORT ANALYSIS SUMMARY (DOCUMENT AI + SYSTEM AI)
============================================================

File: ...
Ship: ...
Analysis Date: ...

--- Extracted Information ---
Audit Report Name: ...
Audit Type: ...
[... other fields ...]

============================================================

============================================================
RAW DOCUMENT AI TEXT (Original OCR/Text Extraction)
============================================================

[Raw text content from Document AI]
```

SUCCESS CRITERIA:
- _summary_text contains BOTH formatted fields AND raw Document AI text
- Clear separation between two sections
- Raw text section should contain original OCR/text extraction
- Backend logs should show "Combined summary created: Formatted (XXX chars) + Raw (XXX chars)"

Test credentials: admin1/123456
Test ship: BROTHER 36 (ID: bc444bc3-aea9-4491-b199-8098efcc16d2)
PDF URL: https://customer-assets.emergentagent.com/job_shipaudit/artifacts/n15ffn23_ISM-Code%20%20Audit-Plan%20%2807-230.pdf
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://shipaudit.preview.emergentagent.com/api"

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
                    
                    # Prefer BROTHER 36 if available (specific ID from review request)
                    if 'BROTHER 36' in ship_name.upper() or ship_id == 'bc444bc3-aea9-4491-b199-8098efcc16d2':
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
    
    # Removed unused PDF download methods - not needed for database check
    
    def test_ship_id_verification(self):
        """Test 3: Verify Ship ID Discrepancy - Compare frontend ship_id with database ship_id"""
        self.print_test_header("Test 3 - Ship ID Verification and Discrepancy Analysis")
        
        if not self.access_token or not self.test_ship_id:
            self.print_result(False, "Missing required data from previous tests")
            return False
        
        try:
            # The problematic ship_id from frontend (from review request)
            frontend_ship_id = "9000377f-ac3f-48d8-ba83-a80fb1a8f490"
            database_ship_id = self.test_ship_id
            ship_name = self.test_ship_data.get('name', 'Unknown')
            
            print(f"🔍 SHIP ID DISCREPANCY ANALYSIS:")
            print(f"   🚢 Ship Name: {ship_name}")
            print(f"   🌐 Frontend Ship ID: {frontend_ship_id}")
            print(f"   🗄️ Database Ship ID: {database_ship_id}")
            
            # Compare the ship IDs
            if frontend_ship_id == database_ship_id:
                print(f"   ✅ Ship IDs MATCH - No discrepancy found")
                self.print_result(True, f"Ship IDs match - no discrepancy for {ship_name}")
                return True
            else:
                print(f"   🚨 SHIP ID MISMATCH DETECTED!")
                print(f"   ❌ Frontend is using: {frontend_ship_id}")
                print(f"   ✅ Database contains: {database_ship_id}")
                print(f"   🔧 This explains the 'Ship not found' error!")
                
                # Check if the frontend ship_id exists in any ship
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                print(f"\n🔍 CHECKING IF FRONTEND SHIP_ID EXISTS IN DATABASE:")
                
                # Search through all ships to see if frontend_ship_id exists
                frontend_ship_found = False
                if self.ships_list:
                    for ship in self.ships_list:
                        if ship.get('id') == frontend_ship_id:
                            frontend_ship_found = True
                            print(f"   ✅ Frontend ship_id FOUND in database!")
                            print(f"   🚢 Ship Name: {ship.get('name', 'Unknown')}")
                            print(f"   🏢 Company: {ship.get('company', 'Unknown')}")
                            print(f"   📋 IMO: {ship.get('imo', 'Unknown')}")
                            print(f"   🎯 ISSUE: Frontend is using wrong ship - should be {ship_name} ({database_ship_id})")
                            break
                
                if not frontend_ship_found:
                    print(f"   ❌ Frontend ship_id NOT FOUND in any ship in database")
                    print(f"   🎯 ISSUE: Frontend is using completely invalid/outdated ship_id")
                    print(f"   🔧 Possible causes:")
                    print(f"      - Local storage contains old ship_id")
                    print(f"      - State management issue in frontend")
                    print(f"      - Ship was deleted but frontend still references it")
                    print(f"      - Wrong company context")
                
                print(f"\n🎯 ROOT CAUSE ANALYSIS:")
                print(f"   🚨 Frontend is sending wrong ship_id: {frontend_ship_id}")
                print(f"   ✅ Correct ship_id for {ship_name}: {database_ship_id}")
                print(f"   🔧 Frontend needs to use correct ship_id to avoid 'Ship not found' errors")
                
                self.print_result(False, f"Ship ID mismatch detected - Frontend: {frontend_ship_id[:8]}..., Database: {database_ship_id[:8]}...")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during ship ID verification test: {str(e)}")
            return False
    
    def download_test_pdf(self):
        """Helper: Download the test PDF from customer assets"""
        try:
            pdf_url = "https://customer-assets.emergentagent.com/job_shipaudit/artifacts/n15ffn23_ISM-Code%20%20Audit-Plan%20%2807-230.pdf"
            
            print(f"📥 Downloading test PDF from: {pdf_url}")
            
            response = requests.get(pdf_url, timeout=30)
            
            if response.status_code == 200:
                pdf_content = response.content
                print(f"✅ PDF downloaded successfully")
                print(f"📄 File size: {len(pdf_content):,} bytes")
                print(f"📋 Content-Type: {response.headers.get('content-type', 'Unknown')}")
                
                # Validate it's a PDF
                if pdf_content.startswith(b'%PDF'):
                    print(f"✅ PDF validation successful")
                    return pdf_content
                else:
                    print(f"❌ Downloaded file is not a valid PDF")
                    return None
            else:
                print(f"❌ Failed to download PDF: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Exception downloading PDF: {str(e)}")
            return None
    
    def test_audit_report_analyze_combined_summary_format(self):
        """Test 4: Test POST /api/audit-reports/analyze and verify Combined Summary Format (Option 3)"""
        self.print_test_header("Test 4 - Audit Report Analysis with Combined Summary Format Verification")
        
        if not self.access_token or not self.test_ship_id:
            self.print_result(False, "Missing required data from previous tests")
            return False
        
        try:
            # Download the test PDF
            pdf_content = self.download_test_pdf()
            if not pdf_content:
                self.print_result(False, "Failed to download test PDF")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # Test with CORRECT ship_id (from database)
            correct_ship_id = self.test_ship_id
            ship_name = self.test_ship_data.get('name', 'Unknown')
            
            print(f"🧪 TESTING AUDIT REPORT ANALYSIS WITH COMBINED SUMMARY FORMAT:")
            print(f"   🚢 Ship Name: {ship_name}")
            print(f"   ✅ Using Ship ID: {correct_ship_id}")
            print(f"   📄 PDF Size: {len(pdf_content):,} bytes")
            print(f"   🎯 Focus: Verify _summary_text contains BOTH formatted summary AND raw Document AI text")
            
            # Prepare multipart form data
            files = {
                'audit_report_file': ('ISM-Code-Audit-Plan.pdf', pdf_content, 'application/pdf')
            }
            
            data = {
                'ship_id': correct_ship_id,
                'bypass_validation': 'false'
            }
            
            print(f"📡 POST {BACKEND_URL}/audit-reports/analyze")
            print(f"   📋 ship_id: {correct_ship_id}")
            print(f"   📋 bypass_validation: false")
            
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
                    print(f"✅ SUCCESS: Audit report analysis completed successfully!")
                    
                    # Check response structure
                    print(f"\n📋 RESPONSE ANALYSIS:")
                    if 'success' in response_data:
                        print(f"   ✅ success: {response_data.get('success')}")
                    
                    if 'message' in response_data:
                        print(f"   📝 message: {response_data.get('message')}")
                    
                    # CRITICAL: Check for _summary_text field
                    analysis = response_data.get('analysis', {})
                    summary_text = analysis.get('_summary_text', '')
                    
                    print(f"\n🔍 COMBINED SUMMARY FORMAT VERIFICATION:")
                    print(f"   📄 _summary_text present: {'✅ YES' if summary_text else '❌ NO'}")
                    
                    if summary_text:
                        summary_length = len(summary_text)
                        print(f"   📏 _summary_text length: {summary_length:,} characters")
                        
                        # Check for required sections in the combined format
                        has_formatted_section = "AUDIT REPORT ANALYSIS SUMMARY (DOCUMENT AI + SYSTEM AI)" in summary_text
                        has_separator = "RAW DOCUMENT AI TEXT (Original OCR/Text Extraction)" in summary_text
                        has_extracted_info = "--- Extracted Information ---" in summary_text
                        
                        print(f"   ✅ Part 1 - Formatted Summary Header: {'✅ FOUND' if has_formatted_section else '❌ MISSING'}")
                        print(f"   ✅ Part 2 - Separator Line: {'✅ FOUND' if has_separator else '❌ MISSING'}")
                        print(f"   ✅ Part 3 - Extracted Info Section: {'✅ FOUND' if has_extracted_info else '❌ MISSING'}")
                        
                        # Check for raw Document AI text section
                        separator_index = summary_text.find("RAW DOCUMENT AI TEXT (Original OCR/Text Extraction)")
                        if separator_index > 0:
                            raw_text_section = summary_text[separator_index + 100:]  # Text after separator
                            raw_text_length = len(raw_text_section.strip())
                            print(f"   📄 Raw Document AI text length: {raw_text_length:,} characters")
                            print(f"   ✅ Raw text section: {'✅ NOT EMPTY' if raw_text_length > 50 else '❌ EMPTY OR TOO SHORT'}")
                            
                            # Show sample of raw text (first 200 chars)
                            if raw_text_length > 0:
                                sample_raw_text = raw_text_section.strip()[:200]
                                print(f"   📝 Raw text sample: {sample_raw_text}...")
                        else:
                            print(f"   ❌ Raw Document AI text section: NOT FOUND")
                        
                        # Show sample of formatted section (first 500 chars)
                        formatted_section = summary_text[:500] if summary_text else ""
                        print(f"\n📝 FORMATTED SECTION SAMPLE (first 500 chars):")
                        print(f"   {formatted_section}...")
                        
                        # Validate structure completeness
                        structure_valid = has_formatted_section and has_separator and has_extracted_info
                        raw_text_valid = separator_index > 0 and len(summary_text[separator_index + 100:].strip()) > 50
                        
                        print(f"\n🎯 COMBINED FORMAT VALIDATION:")
                        print(f"   ✅ Structure Valid: {'✅ YES' if structure_valid else '❌ NO'}")
                        print(f"   ✅ Raw Text Valid: {'✅ YES' if raw_text_valid else '❌ NO'}")
                        print(f"   ✅ Total Length > 1000 chars: {'✅ YES' if summary_length > 1000 else '❌ NO'}")
                        
                        if structure_valid and raw_text_valid and summary_length > 1000:
                            print(f"\n🎉 COMBINED SUMMARY FORMAT VERIFICATION SUCCESSFUL!")
                            print(f"   ✅ _summary_text contains BOTH formatted summary AND raw Document AI text")
                            print(f"   ✅ Clear separation between sections")
                            print(f"   ✅ Raw text section is populated with OCR content")
                            print(f"   ✅ Format matches Option 3 requirements exactly")
                            
                            self.print_result(True, f"Combined summary format (Option 3) verified successfully - contains both formatted and raw text")
                            return True
                        else:
                            print(f"\n❌ COMBINED SUMMARY FORMAT VALIDATION FAILED!")
                            print(f"   ❌ Structure issues detected in _summary_text")
                            print(f"   🔧 May be missing formatted section, separator, or raw text")
                            
                            self.print_result(False, f"Combined summary format validation failed - missing required sections")
                            return False
                    else:
                        print(f"   ❌ _summary_text field is missing or empty")
                        print(f"   🔧 Combined summary format cannot be verified without _summary_text")
                        
                        self.print_result(False, f"_summary_text field missing - cannot verify combined format")
                        return False
                    
                    # Also check other analysis fields for completeness
                    print(f"\n📊 EXTRACTED FIELDS VERIFICATION:")
                    key_fields = ['audit_report_name', 'audit_type', 'audit_report_no', 'audit_date', 'auditor_name', 'issued_by']
                    for field in key_fields:
                        value = analysis.get(field, 'Not extracted')
                        print(f"      {field}: {value}")
                    
                    if 'ship_name' in response_data:
                        print(f"   🚢 ship_name: {response_data.get('ship_name')}")
                    
                    if 'ship_imo' in response_data:
                        print(f"   🔢 ship_imo: {response_data.get('ship_imo')}")
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, "Invalid JSON response from audit report analysis")
                    return False
                    
            elif response.status_code == 404:
                try:
                    error_data = response.json()
                    error_message = error_data.get('detail', 'Unknown error')
                    
                    if 'Ship not found' in error_message:
                        print(f"🚨 CRITICAL: Getting 'Ship not found' error!")
                        print(f"   ❌ Error: {error_message}")
                        print(f"   🔧 Ship ID {correct_ship_id} not found in backend")
                        self.print_result(False, f"Ship not found error - cannot test combined summary format")
                        return False
                    else:
                        print(f"❌ 404 Error (not ship-related): {error_message}")
                        self.print_result(False, f"404 error: {error_message}")
                        return False
                        
                except json.JSONDecodeError:
                    print(f"❌ 404 error with non-JSON response: {response.text}")
                    self.print_result(False, "404 error with invalid response format")
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
            self.print_result(False, f"Exception during combined summary format test: {str(e)}")
            return False
    
    def test_backend_logs_verification(self):
        """Test 5: Verify backend logs show combined summary creation messages"""
        self.print_test_header("Test 5 - Backend Logs Verification for Combined Summary Creation")
        
        print(f"🔍 CHECKING BACKEND LOGS FOR COMBINED SUMMARY MESSAGES:")
        print(f"   🎯 Looking for: 'Combined summary created: Formatted (XXX chars) + Raw (XXX chars)'")
        print(f"   📋 This test checks if backend logs confirm the combined summary creation process")
        
        try:
            # Check supervisor backend logs
            import subprocess
            
            # Get recent backend logs
            log_command = "tail -n 100 /var/log/supervisor/backend.*.log"
            result = subprocess.run(log_command, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_content = result.stdout
                print(f"📄 Retrieved {len(log_content.splitlines())} lines of backend logs")
                
                # Look for combined summary creation messages
                combined_summary_logs = []
                audit_analysis_logs = []
                
                for line in log_content.splitlines():
                    if "Combined summary created" in line:
                        combined_summary_logs.append(line.strip())
                    elif "audit report analysis" in line.lower() or "audit report" in line.lower():
                        audit_analysis_logs.append(line.strip())
                
                print(f"\n🔍 COMBINED SUMMARY LOG ANALYSIS:")
                print(f"   📊 Combined summary creation logs found: {len(combined_summary_logs)}")
                print(f"   📊 Audit analysis related logs found: {len(audit_analysis_logs)}")
                
                if combined_summary_logs:
                    print(f"   ✅ FOUND COMBINED SUMMARY CREATION LOGS:")
                    for i, log_line in enumerate(combined_summary_logs[-3:], 1):  # Show last 3
                        print(f"      {i}. {log_line}")
                    
                    # Check if logs show both formatted and raw text lengths
                    latest_log = combined_summary_logs[-1] if combined_summary_logs else ""
                    has_formatted_chars = "Formatted (" in latest_log and "chars)" in latest_log
                    has_raw_chars = "Raw (" in latest_log and "chars)" in latest_log
                    
                    print(f"\n   📋 LOG CONTENT VERIFICATION:")
                    print(f"      ✅ Shows formatted text length: {'✅ YES' if has_formatted_chars else '❌ NO'}")
                    print(f"      ✅ Shows raw text length: {'✅ YES' if has_raw_chars else '❌ NO'}")
                    
                    if has_formatted_chars and has_raw_chars:
                        print(f"\n   🎉 BACKEND LOGS CONFIRM COMBINED SUMMARY CREATION!")
                        print(f"      ✅ Backend is correctly creating combined summaries with both sections")
                        print(f"      ✅ Logs show character counts for both formatted and raw text")
                        self.print_result(True, "Backend logs confirm combined summary creation with formatted + raw text")
                        return True
                    else:
                        print(f"\n   ⚠️ BACKEND LOGS INCOMPLETE:")
                        print(f"      ❌ Logs don't show both formatted and raw text lengths")
                        print(f"      🔧 May indicate partial implementation of combined format")
                        self.print_result(False, "Backend logs don't show complete combined summary creation")
                        return False
                else:
                    print(f"   ❌ NO COMBINED SUMMARY CREATION LOGS FOUND")
                    print(f"   🔧 This may indicate:")
                    print(f"      - Combined summary feature not implemented")
                    print(f"      - Logs not being generated")
                    print(f"      - Recent audit analysis hasn't been performed")
                    
                    if audit_analysis_logs:
                        print(f"\n   📋 RELATED AUDIT ANALYSIS LOGS FOUND:")
                        for i, log_line in enumerate(audit_analysis_logs[-3:], 1):  # Show last 3
                            print(f"      {i}. {log_line}")
                    
                    self.print_result(False, "No combined summary creation logs found in backend")
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
        """Run all Combined Summary Format tests in sequence"""
        print(f"\n🚀 STARTING AUDIT REPORT COMBINED SUMMARY FORMAT TESTING")
        print(f"🎯 Test Audit Report Summary File - Combined Format (Option 3)")
        print(f"📄 Verify _summary_text contains both formatted summary AND raw Document AI text")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"📅 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test sequence for Combined Summary Format Testing
        tests = [
            ("Setup - Authentication", self.test_authentication),
            ("Setup - Company ID Resolution", self.test_get_company_id),
            ("Setup - Get Ships List", self.test_get_ships_list),
            ("Test 1 - Ship ID Verification", self.test_ship_id_verification),
            ("Test 2 - Audit Analysis Combined Summary Format", self.test_audit_report_analyze_combined_summary_format),
            ("Test 3 - Backend Logs Verification", self.test_backend_logs_verification),
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
        print(f"📊 SHIP ID DEBUG TEST SUMMARY")
        print(f"="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
        print(f"📅 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")
        
        # Ship ID Analysis Summary
        print(f"\n" + "="*80)
        print(f"🔍 SHIP ID ANALYSIS SUMMARY")
        print(f"="*80)
        
        if hasattr(self, 'test_ship_data') and self.test_ship_data:
            ship_name = self.test_ship_data.get('name', 'Unknown')
            correct_ship_id = self.test_ship_id
            wrong_ship_id = "9000377f-ac3f-48d8-ba83-a80fb1a8f490"
            
            print(f"🚢 Ship Name: {ship_name}")
            print(f"✅ CORRECT Ship ID: {correct_ship_id}")
            print(f"❌ WRONG Ship ID (from frontend): {wrong_ship_id}")
            
            if correct_ship_id != wrong_ship_id:
                print(f"\n🎯 ROOT CAUSE IDENTIFIED:")
                print(f"   🚨 Frontend is using WRONG ship_id: {wrong_ship_id}")
                print(f"   ✅ Database contains CORRECT ship_id: {correct_ship_id}")
                print(f"   🔧 Frontend needs to use correct ship_id to avoid 'Ship not found' errors")
                print(f"\n💡 RECOMMENDED FIXES:")
                print(f"   1. Clear frontend local storage/state for ship selection")
                print(f"   2. Ensure ship selection component uses current database ship_id")
                print(f"   3. Add ship_id validation in frontend before API calls")
                print(f"   4. Check if ship selection state management is working correctly")
            else:
                print(f"\n✅ No ship_id discrepancy found - IDs match")
        
        # Overall assessment
        if success_rate >= 80:
            print(f"\n🎉 SHIP ID DEBUG TESTING SUCCESSFUL!")
            print(f"✅ Ship ID discrepancy identified and verified")
            print(f"✅ Correct ship_id works with audit report analysis")
            print(f"✅ Wrong ship_id correctly returns 'Ship not found' error")
            print(f"✅ Root cause identified - frontend using wrong ship_id")
        elif success_rate >= 60:
            print(f"\n⚠️ SHIP ID DEBUG PARTIALLY SUCCESSFUL")
            print(f"📊 Some components working but issues detected")
            print(f"🔧 Review failed tests for specific issues")
        else:
            print(f"\n❌ SHIP ID DEBUG TESTING FAILED")
            print(f"🚨 Critical issues detected - unable to identify root cause")
            print(f"🔧 Major investigation required")
        
        return success_rate >= 80


if __name__ == "__main__":
    """Main execution - run Ship ID Debug tests"""
    tester = BackendAPITester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED - SHIP ID ISSUE SUCCESSFULLY DEBUGGED")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED - REVIEW RESULTS ABOVE")
        sys.exit(1)

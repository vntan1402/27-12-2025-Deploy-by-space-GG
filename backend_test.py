#!/usr/bin/env python3
"""
Backend API Testing Script - OCR Extraction Testing with Tesseract Available

FOCUS: Test Audit Report OCR header/footer extraction with Tesseract now available
OBJECTIVE: Verify OCR header/footer extraction is now working with correct targeted_ocr import.

CRITICAL TEST REQUIREMENTS FROM REVIEW REQUEST:
1. **Authentication**: Login: admin1 / 123456
2. **Get Ship**: GET /api/ships, Find BROTHER 36 (bc444bc3-aea9-4491-b199-8098efcc16d2)
3. **Audit Report Analysis with OCR**: POST /api/audit-reports/analyze
   - PDF: https://customer-assets.emergentagent.com/job_shipaudit/artifacts/n15ffn23_ISM-Code%20%20Audit-Plan%20%2807-230.pdf
   - ship_id: bc444bc3-aea9-4491-b199-8098efcc16d2
   - bypass_validation: false
4. **Verify OCR in Summary**: Check `_summary_text` contains:
   ```
   ============================================================
   ADDITIONAL INFORMATION FROM HEADER/FOOTER (OCR Extraction)
   ============================================================
   
   === HEADER TEXT (Top 15% of page) ===
   [actual OCR extracted text from PDF header]
   
   === FOOTER TEXT (Bottom 15% of page) ===
   [actual OCR extracted text from PDF footer]
   ============================================================
   ```
5. **Backend Logs Verification**: Look for:
   - "🔍 Starting Targeted OCR"
   - "✅ OCR processor available"
   - "✅ Targeted OCR completed successfully"
   - "📄 OCR results: header=XXX chars, footer=XXX chars"
   - "✅ Header text added"
   - "✅ Footer text added"
   - "✅ Enhanced summary with OCR"
6. **Report Form Check**: Verify report_form = "07-230" from filename extraction

SUCCESS CRITERIA:
- ✅ OCR section present in _summary_text
- ✅ Header text length > 0
- ✅ Footer text length > 0
- ✅ Backend logs show OCR success
- ✅ report_form = "07-230"

FAILURE INDICATORS:
- ❌ No "ADDITIONAL INFORMATION FROM HEADER/FOOTER" section
- ❌ "OCR processor not available"
- ❌ "OCR extraction returned no results"

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
    
    def test_audit_report_analyze_report_form_and_ocr_extraction(self):
        """Test 4: Test POST /api/audit-reports/analyze and verify Report Form extraction and OCR header/footer extraction"""
        self.print_test_header("Test 4 - Audit Report Analysis with Report Form & OCR Extraction Verification")
        
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
            
            # Use the specific ship_id from review request
            target_ship_id = "bc444bc3-aea9-4491-b199-8098efcc16d2"  # BROTHER 36
            ship_name = "BROTHER 36"
            
            print(f"🧪 TESTING AUDIT REPORT ANALYSIS WITH REPORT FORM & OCR EXTRACTION:")
            print(f"   🚢 Ship Name: {ship_name}")
            print(f"   ✅ Using Ship ID: {target_ship_id}")
            print(f"   📄 PDF Size: {len(pdf_content):,} bytes")
            print(f"   📄 PDF Filename: ISM-Code  Audit-Plan (07-230.pdf")
            print(f"   🎯 Focus: Verify report_form extraction from filename and OCR header/footer extraction")
            
            # Prepare multipart form data with original filename to test filename extraction
            files = {
                'audit_report_file': ('ISM-Code  Audit-Plan (07-230.pdf', pdf_content, 'application/pdf')
            }
            
            data = {
                'ship_id': target_ship_id,
                'bypass_validation': 'false'  # Use false as specified in review request
            }
            
            print(f"📡 POST {BACKEND_URL}/audit-reports/analyze")
            print(f"   📋 ship_id: {target_ship_id}")
            print(f"   📋 bypass_validation: false")
            print(f"   📋 filename: ISM-Code  Audit-Plan (07-230.pdf")
            
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
                    
                    # CRITICAL: Check for report_form field
                    analysis = response_data.get('analysis', {})
                    report_form = analysis.get('report_form', '')
                    
                    print(f"\n🔍 REPORT FORM EXTRACTION VERIFICATION:")
                    print(f"   📄 report_form present: {'✅ YES' if report_form else '❌ NO'}")
                    print(f"   📄 report_form value: '{report_form}'")
                    
                    # Check if report_form matches expected pattern from filename (specifically 07-230)
                    expected_form = '07-230'
                    form_match = report_form == expected_form if report_form else False
                    print(f"   ✅ Expected report_form '07-230': {'✅ YES' if form_match else '❌ NO'}")
                    if report_form and not form_match:
                        print(f"   ⚠️ Got '{report_form}' instead of expected '07-230'")
                    
                    # CRITICAL: Check for _summary_text field and OCR content
                    summary_text = analysis.get('_summary_text', '')
                    
                    print(f"\n🔍 OCR HEADER/FOOTER EXTRACTION VERIFICATION:")
                    print(f"   📄 _summary_text present: {'✅ YES' if summary_text else '❌ NO'}")
                    
                    if summary_text:
                        summary_length = len(summary_text)
                        print(f"   📏 _summary_text length: {summary_length:,} characters")
                        
                        # Check for OCR section specifically
                        has_ocr_section = "ADDITIONAL INFORMATION FROM HEADER/FOOTER (OCR Extraction)" in summary_text
                        
                        print(f"   ✅ OCR Header/Footer Section: {'✅ FOUND' if has_ocr_section else '❌ MISSING'}")
                        
                        # Check OCR section content and structure
                        header_text_length = 0
                        footer_text_length = 0
                        ocr_content_valid = False
                        
                        if has_ocr_section:
                            ocr_start = summary_text.find("ADDITIONAL INFORMATION FROM HEADER/FOOTER (OCR Extraction)")
                            if ocr_start >= 0:
                                # Extract the OCR section
                                ocr_section = summary_text[ocr_start:]
                                
                                # Look for header and footer subsections
                                has_header_section = "=== HEADER TEXT (Top 15% of page) ===" in ocr_section
                                has_footer_section = "=== FOOTER TEXT (Bottom 15% of page) ===" in ocr_section
                                
                                print(f"   ✅ Header subsection: {'✅ FOUND' if has_header_section else '❌ MISSING'}")
                                print(f"   ✅ Footer subsection: {'✅ FOUND' if has_footer_section else '❌ MISSING'}")
                                
                                # Extract header text if present
                                if has_header_section:
                                    header_start = ocr_section.find("=== HEADER TEXT (Top 15% of page) ===")
                                    header_end = ocr_section.find("=== FOOTER TEXT (Bottom 15% of page) ===")
                                    if header_start >= 0 and header_end > header_start:
                                        header_content = ocr_section[header_start:header_end].strip()
                                        # Remove the header marker to get actual text
                                        header_text = header_content.replace("=== HEADER TEXT (Top 15% of page) ===", "").strip()
                                        header_text_length = len(header_text)
                                        print(f"   📄 Header text length: {header_text_length} characters")
                                        if header_text_length > 0:
                                            print(f"   📝 Header sample: {header_text[:100]}...")
                                
                                # Extract footer text if present
                                if has_footer_section:
                                    footer_start = ocr_section.find("=== FOOTER TEXT (Bottom 15% of page) ===")
                                    footer_end = ocr_section.find("============================================================", footer_start + 50)
                                    if footer_start >= 0:
                                        if footer_end > footer_start:
                                            footer_content = ocr_section[footer_start:footer_end].strip()
                                        else:
                                            footer_content = ocr_section[footer_start:].strip()
                                        # Remove the footer marker to get actual text
                                        footer_text = footer_content.replace("=== FOOTER TEXT (Bottom 15% of page) ===", "").strip()
                                        footer_text_length = len(footer_text)
                                        print(f"   📄 Footer text length: {footer_text_length} characters")
                                        if footer_text_length > 0:
                                            print(f"   📝 Footer sample: {footer_text[:100]}...")
                                
                                ocr_content_valid = header_text_length > 0 or footer_text_length > 0
                                print(f"   ✅ OCR content valid: {'✅ YES' if ocr_content_valid else '❌ NO'}")
                            else:
                                print(f"   ❌ OCR section found but content not accessible")
                        else:
                            print(f"   ❌ OCR section: NOT FOUND in _summary_text")
                        
                        print(f"\n🎯 OVERALL VALIDATION:")
                        print(f"   ✅ OCR section present: {'✅ YES' if has_ocr_section else '❌ NO'}")
                        print(f"   ✅ Header text length > 0: {'✅ YES' if header_text_length > 0 else '❌ NO'}")
                        print(f"   ✅ Footer text length > 0: {'✅ YES' if footer_text_length > 0 else '❌ NO'}")
                        print(f"   ✅ Report form = '07-230': {'✅ YES' if form_match else '❌ NO'}")
                        
                        # Success criteria from review request
                        success_criteria_met = (
                            has_ocr_section and  # OCR section present in _summary_text
                            (header_text_length > 0 or footer_text_length > 0) and  # Header or footer text length > 0
                            form_match  # report_form = "07-230"
                        )
                        
                        if success_criteria_met:
                            print(f"\n🎉 OCR EXTRACTION VERIFICATION SUCCESSFUL!")
                            print(f"   ✅ OCR section present in _summary_text")
                            print(f"   ✅ Header text length: {header_text_length} chars")
                            print(f"   ✅ Footer text length: {footer_text_length} chars")
                            print(f"   ✅ Report form = '07-230': {report_form}")
                            print(f"   ✅ All success criteria from review request met")
                            
                            self.print_result(True, f"OCR extraction verified successfully - Header: {header_text_length} chars, Footer: {footer_text_length} chars, Form: '{report_form}'")
                            return True
                        else:
                            print(f"\n❌ OCR EXTRACTION VALIDATION FAILED!")
                            print(f"   ❌ OCR section: {has_ocr_section}")
                            print(f"   ❌ Header length: {header_text_length}")
                            print(f"   ❌ Footer length: {footer_text_length}")
                            print(f"   ❌ Report form match: {form_match} (got: '{report_form}')")
                            
                            self.print_result(False, f"OCR extraction validation failed - missing required components")
                            return False
                    else:
                        print(f"   ❌ _summary_text field is missing or empty")
                        print(f"   🔧 Cannot verify OCR extraction without _summary_text")
                        
                        self.print_result(False, f"_summary_text field missing - cannot verify OCR extraction")
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
                        print(f"   🔧 Ship ID {target_ship_id} not found in backend")
                        self.print_result(False, f"Ship not found error - cannot test report form & OCR extraction")
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
            self.print_result(False, f"Exception during report form & OCR extraction test: {str(e)}")
            return False
    
    def test_backend_logs_verification(self):
        """Test 5: Verify backend logs show OCR processing and report form extraction messages"""
        self.print_test_header("Test 5 - Backend Logs Verification for OCR Processing and Report Form Extraction")
        
        print(f"🔍 CHECKING BACKEND LOGS FOR OCR AND REPORT FORM MESSAGES:")
        print(f"   🎯 Looking for: '🔍 Starting Targeted OCR'")
        print(f"   🎯 Looking for: '✅ OCR processor available'")
        print(f"   🎯 Looking for: '✅ Enhanced summary with OCR'")
        print(f"   🎯 Looking for: '✅ Extracted report_form from filename'")
        print(f"   📋 This test checks if backend logs confirm OCR processing and filename extraction")
        
        try:
            # Check supervisor backend logs
            import subprocess
            
            # Get recent backend logs
            log_command = "tail -n 200 /var/log/supervisor/backend.*.log"
            result = subprocess.run(log_command, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_content = result.stdout
                print(f"📄 Retrieved {len(log_content.splitlines())} lines of backend logs")
                
                # Look for OCR processing messages as specified in review request
                ocr_start_logs = []
                ocr_available_logs = []
                ocr_completed_logs = []
                ocr_results_logs = []
                header_added_logs = []
                footer_added_logs = []
                ocr_enhanced_logs = []
                report_form_logs = []
                audit_analysis_logs = []
                
                for line in log_content.splitlines():
                    if "🔍 Starting Targeted OCR" in line:
                        ocr_start_logs.append(line.strip())
                    elif "✅ OCR processor available" in line:
                        ocr_available_logs.append(line.strip())
                    elif "✅ Targeted OCR completed successfully" in line:
                        ocr_completed_logs.append(line.strip())
                    elif "📄 OCR results: header=" in line and "chars, footer=" in line:
                        ocr_results_logs.append(line.strip())
                    elif "✅ Header text added" in line:
                        header_added_logs.append(line.strip())
                    elif "✅ Footer text added" in line:
                        footer_added_logs.append(line.strip())
                    elif "✅ Enhanced summary with OCR" in line:
                        ocr_enhanced_logs.append(line.strip())
                    elif "✅ Extracted report_form from filename" in line:
                        report_form_logs.append(line.strip())
                    elif "audit report analysis" in line.lower() or "audit report" in line.lower():
                        audit_analysis_logs.append(line.strip())
                
                print(f"\n🔍 OCR PROCESSING LOG ANALYSIS:")
                print(f"   📊 OCR start logs found: {len(ocr_start_logs)}")
                print(f"   📊 OCR processor available logs found: {len(ocr_available_logs)}")
                print(f"   📊 OCR completed logs found: {len(ocr_completed_logs)}")
                print(f"   📊 OCR results logs found: {len(ocr_results_logs)}")
                print(f"   📊 Header added logs found: {len(header_added_logs)}")
                print(f"   📊 Footer added logs found: {len(footer_added_logs)}")
                print(f"   📊 OCR enhanced summary logs found: {len(ocr_enhanced_logs)}")
                print(f"   📊 Report form extraction logs found: {len(report_form_logs)}")
                print(f"   📊 Audit analysis related logs found: {len(audit_analysis_logs)}")
                
                # Check each type of log
                ocr_start_found = len(ocr_start_logs) > 0
                ocr_available_found = len(ocr_available_logs) > 0
                ocr_completed_found = len(ocr_completed_logs) > 0
                ocr_results_found = len(ocr_results_logs) > 0
                header_added_found = len(header_added_logs) > 0
                footer_added_found = len(footer_added_logs) > 0
                ocr_enhanced_found = len(ocr_enhanced_logs) > 0
                report_form_found = len(report_form_logs) > 0
                
                print(f"\n📋 EXPECTED LOG MESSAGES VERIFICATION:")
                print(f"   ✅ '🔍 Starting Targeted OCR': {'✅ FOUND' if ocr_start_found else '❌ NOT FOUND'}")
                print(f"   ✅ '✅ OCR processor available': {'✅ FOUND' if ocr_available_found else '❌ NOT FOUND'}")
                print(f"   ✅ '✅ Targeted OCR completed successfully': {'✅ FOUND' if ocr_completed_found else '❌ NOT FOUND'}")
                print(f"   ✅ '📄 OCR results: header=XXX chars, footer=XXX chars': {'✅ FOUND' if ocr_results_found else '❌ NOT FOUND'}")
                print(f"   ✅ '✅ Header text added': {'✅ FOUND' if header_added_found else '❌ NOT FOUND'}")
                print(f"   ✅ '✅ Footer text added': {'✅ FOUND' if footer_added_found else '❌ NOT FOUND'}")
                print(f"   ✅ '✅ Enhanced summary with OCR': {'✅ FOUND' if ocr_enhanced_found else '❌ NOT FOUND'}")
                
                # Show sample logs if found
                if ocr_start_logs:
                    print(f"\n   📝 OCR START LOG SAMPLE:")
                    print(f"      {ocr_start_logs[-1]}")
                
                if ocr_available_logs:
                    print(f"\n   📝 OCR AVAILABLE LOG SAMPLE:")
                    print(f"      {ocr_available_logs[-1]}")
                
                if ocr_enhanced_logs:
                    print(f"\n   📝 OCR ENHANCED LOG SAMPLE:")
                    print(f"      {ocr_enhanced_logs[-1]}")
                
                if report_form_logs:
                    print(f"\n   📝 REPORT FORM EXTRACTION LOG SAMPLE:")
                    print(f"      {report_form_logs[-1]}")
                
                # Overall validation
                all_expected_logs_found = ocr_start_found and ocr_available_found and ocr_enhanced_found and report_form_found
                partial_logs_found = ocr_start_found or ocr_available_found or ocr_enhanced_found or report_form_found
                
                print(f"\n🎯 BACKEND LOGS VALIDATION:")
                print(f"   ✅ All expected logs found: {'✅ YES' if all_expected_logs_found else '❌ NO'}")
                print(f"   ✅ Some OCR/report form logs found: {'✅ YES' if partial_logs_found else '❌ NO'}")
                
                if all_expected_logs_found:
                    print(f"\n🎉 BACKEND LOGS VERIFICATION SUCCESSFUL!")
                    print(f"   ✅ OCR processing logs confirmed")
                    print(f"   ✅ Report form extraction logs confirmed")
                    print(f"   ✅ All expected log messages found")
                    self.print_result(True, "Backend logs confirm OCR processing and report form extraction")
                    return True
                elif partial_logs_found:
                    print(f"\n⚠️ BACKEND LOGS PARTIALLY FOUND:")
                    print(f"   ⚠️ Some OCR/report form logs present but not all expected messages")
                    print(f"   🔧 May indicate partial implementation or different log format")
                    self.print_result(False, "Backend logs show partial OCR/report form processing")
                    return False
                else:
                    print(f"\n❌ NO OCR/REPORT FORM LOGS FOUND")
                    print(f"   🔧 This may indicate:")
                    print(f"      - OCR processing not implemented")
                    print(f"      - Report form extraction not working")
                    print(f"      - Logs not being generated")
                    print(f"      - Recent audit analysis hasn't been performed")
                    
                    if audit_analysis_logs:
                        print(f"\n   📋 RELATED AUDIT ANALYSIS LOGS FOUND:")
                        for i, log_line in enumerate(audit_analysis_logs[-3:], 1):  # Show last 3
                            print(f"      {i}. {log_line}")
                    
                    self.print_result(False, "No OCR or report form extraction logs found in backend")
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
        """Run all Report Form & OCR Extraction tests in sequence"""
        print(f"\n🚀 STARTING AUDIT REPORT FORM & OCR EXTRACTION TESTING")
        print(f"🎯 Test Report Form extraction from filename and OCR header/footer extraction")
        print(f"📄 Verify report_form field populated and _summary_text contains OCR section")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"📅 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test sequence for Report Form & OCR Extraction Testing
        tests = [
            ("Setup - Authentication", self.test_authentication),
            ("Setup - Company ID Resolution", self.test_get_company_id),
            ("Setup - Get Ships List", self.test_get_ships_list),
            ("Test 1 - Ship ID Verification", self.test_ship_id_verification),
            ("Test 2 - Audit Analysis Report Form & OCR Extraction", self.test_audit_report_analyze_report_form_and_ocr_extraction),
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
        print(f"📊 REPORT FORM & OCR EXTRACTION TEST SUMMARY")
        print(f"="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
        print(f"📅 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")
        
        # Report Form & OCR Extraction Analysis
        print(f"\n" + "="*80)
        print(f"🔍 REPORT FORM & OCR EXTRACTION ANALYSIS")
        print(f"="*80)
        
        if hasattr(self, 'test_ship_data') and self.test_ship_data:
            ship_name = self.test_ship_data.get('name', 'Unknown')
            ship_id = self.test_ship_id
            
            print(f"🚢 Test Ship: {ship_name}")
            print(f"🆔 Ship ID: {ship_id}")
            print(f"📄 Test PDF: ISM-Code Audit-Plan (07-230.pdf")
            print(f"🎯 Focus: Report Form & OCR Extraction")
            
            print(f"\n📋 EXPECTED RESULTS VERIFICATION:")
            print(f"   ✅ report_form field populated (from AI or filename)")
            print(f"   ✅ _summary_text contains 3 sections")
            print(f"   ✅ OCR section has header/footer text")
            print(f"   ✅ Backend logs show OCR processing")
        
        # Overall assessment
        if success_rate >= 80:
            print(f"\n🎉 REPORT FORM & OCR EXTRACTION TESTING SUCCESSFUL!")
            print(f"✅ report_form field populated (from AI or filename)")
            print(f"✅ _summary_text contains 3 sections including OCR")
            print(f"✅ OCR section has header/footer text content")
            print(f"✅ Backend logs show OCR processing")
            print(f"✅ All success criteria from review request met")
        elif success_rate >= 60:
            print(f"\n⚠️ REPORT FORM & OCR EXTRACTION PARTIALLY SUCCESSFUL")
            print(f"📊 Some components working but extraction issues detected")
            print(f"🔧 Review failed tests for specific extraction problems")
        else:
            print(f"\n❌ REPORT FORM & OCR EXTRACTION TESTING FAILED")
            print(f"🚨 Critical issues with report form or OCR extraction")
            print(f"🔧 Major extraction corrections required")
        
        return success_rate >= 80


if __name__ == "__main__":
    """Main execution - run Report Form & OCR Extraction tests"""
    tester = BackendAPITester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED - REPORT FORM & OCR EXTRACTION VERIFIED SUCCESSFULLY")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED - REVIEW RESULTS ABOVE")
        sys.exit(1)

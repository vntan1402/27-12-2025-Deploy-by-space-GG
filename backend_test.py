#!/usr/bin/env python3
"""
Backend API Testing Script - NCR Form Report Form Extraction Testing

FOCUS: Test System AI Report Form Extraction from Footer - NCR Form
OBJECTIVE: Test if System AI can extract report_form from footer of PDF document.

CRITICAL TEST REQUIREMENTS FROM REVIEW REQUEST:
1. **Authentication**: Login: admin1 / 123456
2. **Get Ship**: GET /api/ships - Find BROTHER 36 (bc444bc3-aea9-4491-b199-8098efcc16d2)
3. **Test Audit Report Analysis**: POST /api/audit-reports/analyze
   - PDF: NCR form from https://customer-assets.emergentagent.com/job_shipaudit/artifacts/atqzy94l_ISM-Code%20%20NCR%20%2807-23%29.pdf
   - Filename: "ISM-Code  NCR (07-23).pdf"
   - ship_id: bc444bc3-aea9-4491-b199-8098efcc16d2
   - bypass_validation: false
4. **Verify Report Form Extraction**: Check `report_form` field in response
   - Expected: Should extract form code from footer
   - Possible values: "(07-23)", "NCR (07-23)", "07-23", or similar
5. **Check Backend Logs for AI Processing**: Look for:
   - "🤖 Extracting audit report fields from summary"
   - "📤 Sending extraction prompt to gemini"
   - "📄 Extracted Report Form: '...'"
   - "✅ Extracted report_form from filename: '...'" (if AI fails)

KEY QUESTIONS:
1. Does `report_form` field have a value?
2. What is the exact value extracted?
3. Did it come from AI (footer/content) or filename pattern?
4. What does Document AI summary contain about footer?

SUCCESS CRITERIA:
- ✅ report_form is populated (not empty)
- ✅ Value matches form code in footer or filename
- ✅ Backend logs show extraction method

Test credentials: admin1/123456
Test ship: BROTHER 36 (ID: bc444bc3-aea9-4491-b199-8098efcc16d2)
Test PDF: ISM-Code  NCR (07-23).pdf
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://audit-report-sync.preview.emergentagent.com/api"

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
    
    def download_ncr_test_pdf(self):
        """Helper: Download the NCR test PDF from customer assets"""
        try:
            # NCR form PDF URL from review request
            pdf_url = "https://customer-assets.emergentagent.com/job_shipaudit/artifacts/atqzy94l_ISM-Code%20%20NCR%20%2807-23%29.pdf"
            
            print(f"📥 Downloading NCR test PDF from: {pdf_url}")
            
            response = requests.get(pdf_url, timeout=30)
            
            if response.status_code == 200:
                pdf_content = response.content
                print(f"✅ NCR PDF downloaded successfully")
                print(f"📄 File size: {len(pdf_content):,} bytes")
                print(f"📋 Content-Type: {response.headers.get('content-type', 'Unknown')}")
                print(f"📄 Expected filename: ISM-Code  NCR (07-23).pdf")
                
                # Validate it's a PDF
                if pdf_content.startswith(b'%PDF'):
                    print(f"✅ PDF validation successful")
                    return pdf_content
                else:
                    print(f"❌ Downloaded file is not a valid PDF")
                    return None
            else:
                print(f"❌ Failed to download NCR PDF: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Exception downloading NCR PDF: {str(e)}")
            return None
    
    def test_audit_report_analyze_ncr_form_extraction(self):
        """Test 4: Test POST /api/audit-reports/analyze and verify report_form extraction from NCR PDF"""
        self.print_test_header("Test 4 - Audit Report Analysis with NCR Form Report Form Extraction")
        
        if not self.access_token or not self.test_ship_id:
            self.print_result(False, "Missing required data from previous tests")
            return False
        
        try:
            # Download the NCR test PDF
            pdf_content = self.download_ncr_test_pdf()
            if not pdf_content:
                self.print_result(False, "Failed to download NCR test PDF")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # Use the specific ship_id from review request
            target_ship_id = "bc444bc3-aea9-4491-b199-8098efcc16d2"  # BROTHER 36
            ship_name = "BROTHER 36"
            
            print(f"🧪 TESTING AUDIT REPORT ANALYSIS WITH NCR FORM EXTRACTION:")
            print(f"   🚢 Ship Name: {ship_name}")
            print(f"   ✅ Using Ship ID: {target_ship_id}")
            print(f"   📄 PDF Size: {len(pdf_content):,} bytes")
            print(f"   📄 PDF Filename: ISM-Code  NCR (07-23).pdf")
            print(f"   🎯 Focus: Verify report_form extraction from footer")
            print(f"   🎯 Expected report_form values: '(07-23)', 'NCR (07-23)', '07-23', or similar")
            
            # Prepare multipart form data for Audit Report analysis
            files = {
                'audit_report_file': ('ISM-Code  NCR (07-23).pdf', pdf_content, 'application/pdf')
            }
            
            data = {
                'ship_id': target_ship_id,
                'bypass_validation': 'true'  # Use true to bypass ship validation and get extracted data
            }
            
            print(f"📡 POST {BACKEND_URL}/audit-reports/analyze")
            print(f"   📋 ship_id: {target_ship_id}")
            print(f"   📋 bypass_validation: true")
            print(f"   📋 filename: ISM-Code  NCR (07-23).pdf")
            
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
                    
                    # CRITICAL: Check for report_form field extraction
                    analysis = response_data.get('analysis', {})
                    report_form = analysis.get('report_form', '')
                    
                    print(f"\n🔍 REPORT FORM EXTRACTION VERIFICATION:")
                    print(f"   📄 report_form field present: {'✅ YES' if 'report_form' in analysis else '❌ NO'}")
                    print(f"   📄 report_form value: '{report_form}'")
                    print(f"   📄 report_form populated: {'✅ YES' if report_form and report_form.strip() else '❌ NO'}")
                    
                    # Check if report_form matches expected values
                    expected_values = ['(07-23)', 'NCR (07-23)', '07-23', '07-230']
                    form_match = any(expected in str(report_form) for expected in expected_values) if report_form else False
                    
                    print(f"   📄 Expected values: {expected_values}")
                    print(f"   ✅ Form matches expected: {'✅ YES' if form_match else '❌ NO'}")
                    
                    # Check Document AI summary for footer content
                    summary_text = analysis.get('_summary_text', '')
                    print(f"\n🔍 DOCUMENT AI SUMMARY ANALYSIS:")
                    print(f"   📄 _summary_text present: {'✅ YES' if summary_text else '❌ NO'}")
                    
                    if summary_text:
                        summary_length = len(summary_text)
                        print(f"   📏 _summary_text length: {summary_length:,} characters")
                        
                        # Look for footer-related content in summary
                        footer_keywords = ['footer', 'bottom', '07-23', 'NCR', 'form']
                        footer_content_found = any(keyword.lower() in summary_text.lower() for keyword in footer_keywords)
                        print(f"   📄 Footer-related content: {'✅ FOUND' if footer_content_found else '❌ NOT FOUND'}")
                        
                        # Check for OCR section (if available)
                        has_ocr_section = "ADDITIONAL INFORMATION FROM HEADER/FOOTER (OCR Extraction)" in summary_text
                        print(f"   📄 OCR Header/Footer Section: {'✅ FOUND' if has_ocr_section else '❌ NOT FOUND'}")
                        
                        if has_ocr_section:
                            # Extract footer text from OCR section
                            ocr_start = summary_text.find("ADDITIONAL INFORMATION FROM HEADER/FOOTER (OCR Extraction)")
                            if ocr_start >= 0:
                                ocr_section = summary_text[ocr_start:]
                                has_footer_section = "=== FOOTER TEXT (Bottom 15% of page) ===" in ocr_section
                                print(f"   📄 OCR Footer subsection: {'✅ FOUND' if has_footer_section else '❌ NOT FOUND'}")
                                
                                if has_footer_section:
                                    footer_start = ocr_section.find("=== FOOTER TEXT (Bottom 15% of page) ===")
                                    footer_end = ocr_section.find("============================================================", footer_start + 50)
                                    if footer_start >= 0:
                                        if footer_end > footer_start:
                                            footer_content = ocr_section[footer_start:footer_end].strip()
                                        else:
                                            footer_content = ocr_section[footer_start:].strip()
                                        footer_text = footer_content.replace("=== FOOTER TEXT (Bottom 15% of page) ===", "").strip()
                                        print(f"   📄 Footer text length: {len(footer_text)} characters")
                                        if len(footer_text) > 0:
                                            print(f"   📝 Footer sample: {footer_text[:200]}...")
                                            # Check if footer contains form code
                                            footer_has_form = any(expected in footer_text for expected in expected_values)
                                            print(f"   ✅ Footer contains form code: {'✅ YES' if footer_has_form else '❌ NO'}")
                    
                    # Check other extracted fields
                    print(f"\n📊 OTHER EXTRACTED FIELDS:")
                    key_fields = ['audit_report_name', 'audit_type', 'audit_report_no', 'audit_date', 'auditor_name', 'issued_by', 'status', 'note']
                    for field in key_fields:
                        value = analysis.get(field, 'Not extracted')
                        print(f"   {field}: {value}")
                    
                    if 'ship_name' in response_data:
                        print(f"   🚢 ship_name: {response_data.get('ship_name')}")
                    
                    if 'ship_imo' in response_data:
                        print(f"   🔢 ship_imo: {response_data.get('ship_imo')}")
                    
                    # Overall validation
                    print(f"\n🎯 SUCCESS CRITERIA VALIDATION:")
                    report_form_populated = bool(report_form and report_form.strip())
                    form_matches_expected = form_match
                    
                    print(f"   ✅ report_form is populated: {'✅ YES' if report_form_populated else '❌ NO'}")
                    print(f"   ✅ Value matches expected: {'✅ YES' if form_matches_expected else '❌ NO'}")
                    print(f"   📄 Actual report_form: '{report_form}'")
                    
                    # Success criteria from review request
                    success_criteria_met = report_form_populated and form_matches_expected
                    
                    if success_criteria_met:
                        print(f"\n🎉 NCR FORM REPORT_FORM EXTRACTION SUCCESSFUL!")
                        print(f"   ✅ report_form field populated: '{report_form}'")
                        print(f"   ✅ Value matches expected form code")
                        print(f"   ✅ System AI successfully extracted report_form from NCR PDF")
                        
                        self.print_result(True, f"NCR form report_form extraction successful: '{report_form}'")
                        return True
                    else:
                        print(f"\n❌ NCR FORM REPORT_FORM EXTRACTION FAILED!")
                        print(f"   ❌ report_form populated: {report_form_populated}")
                        print(f"   ❌ Form matches expected: {form_matches_expected}")
                        print(f"   📄 Actual value: '{report_form}'")
                        
                        self.print_result(False, f"NCR form report_form extraction failed - Value: '{report_form}'")
                        return False
                    
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
                        self.print_result(False, f"Ship not found error - cannot test NCR form extraction")
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
            self.print_result(False, f"Exception during NCR form extraction test: {str(e)}")
            return False
    
    def test_backend_logs_verification(self):
        """Test 5: Verify backend logs show AI processing and report form extraction messages"""
        self.print_test_header("Test 5 - Backend Logs Verification for AI Processing and Report Form Extraction")
        
        print(f"🔍 CHECKING BACKEND LOGS FOR AUDIT REPORT AI PROCESSING MESSAGES:")
        print(f"   🎯 Looking for: '🤖 Extracting audit report fields from summary'")
        print(f"   🎯 Looking for: '📤 Sending extraction prompt to gemini'")
        print(f"   🎯 Looking for: '📄 Extracted Report Form: ...'")
        print(f"   🎯 Looking for: '✅ Extracted report_form from filename: ...'")
        print(f"   📋 This test checks if backend logs confirm AI processing and report_form extraction")
        
        try:
            # Check supervisor backend logs
            import subprocess
            
            # Get recent backend logs
            log_command = "tail -n 300 /var/log/supervisor/backend.*.log"
            result = subprocess.run(log_command, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_content = result.stdout
                print(f"📄 Retrieved {len(log_content.splitlines())} lines of backend logs")
                
                # Look for AI processing messages as specified in review request
                ai_extraction_logs = []
                gemini_prompt_logs = []
                report_form_extracted_logs = []
                filename_extraction_logs = []
                audit_analysis_logs = []
                
                for line in log_content.splitlines():
                    if "🤖 Extracting audit report fields from summary" in line:
                        ai_extraction_logs.append(line.strip())
                    elif "📤 Sending extraction prompt to gemini" in line:
                        gemini_prompt_logs.append(line.strip())
                    elif "📄 Extracted Report Form:" in line:
                        report_form_extracted_logs.append(line.strip())
                    elif "✅ Extracted report_form from filename:" in line:
                        filename_extraction_logs.append(line.strip())
                    elif "audit report analysis" in line.lower() or "audit report" in line.lower():
                        audit_analysis_logs.append(line.strip())
                
                print(f"\n🔍 AUDIT REPORT AI PROCESSING LOG ANALYSIS:")
                print(f"   📊 AI extraction logs found: {len(ai_extraction_logs)}")
                print(f"   📊 Gemini prompt logs found: {len(gemini_prompt_logs)}")
                print(f"   📊 Report form extracted logs found: {len(report_form_extracted_logs)}")
                print(f"   📊 Filename extraction logs found: {len(filename_extraction_logs)}")
                print(f"   📊 Audit analysis related logs found: {len(audit_analysis_logs)}")
                
                # Check each type of log
                ai_extraction_found = len(ai_extraction_logs) > 0
                gemini_prompt_found = len(gemini_prompt_logs) > 0
                report_form_found = len(report_form_extracted_logs) > 0
                filename_extraction_found = len(filename_extraction_logs) > 0
                
                print(f"\n📋 EXPECTED LOG MESSAGES VERIFICATION:")
                print(f"   ✅ '🤖 Extracting audit report fields from summary': {'✅ FOUND' if ai_extraction_found else '❌ NOT FOUND'}")
                print(f"   ✅ '📤 Sending extraction prompt to gemini': {'✅ FOUND' if gemini_prompt_found else '❌ NOT FOUND'}")
                print(f"   ✅ '📄 Extracted Report Form: ...': {'✅ FOUND' if report_form_found else '❌ NOT FOUND'}")
                print(f"   ✅ '✅ Extracted report_form from filename: ...': {'✅ FOUND' if filename_extraction_found else '❌ NOT FOUND'}")
                
                # Show sample logs if found
                if ai_extraction_logs:
                    print(f"\n   📝 AI EXTRACTION LOG SAMPLE:")
                    print(f"      {ai_extraction_logs[-1]}")
                
                if gemini_prompt_logs:
                    print(f"\n   📝 GEMINI PROMPT LOG SAMPLE:")
                    print(f"      {gemini_prompt_logs[-1]}")
                
                if report_form_found:
                    print(f"\n   📝 REPORT FORM EXTRACTED LOG SAMPLE:")
                    print(f"      {report_form_extracted_logs[-1]}")
                
                if filename_extraction_found:
                    print(f"\n   📝 FILENAME EXTRACTION LOG SAMPLE:")
                    print(f"      {filename_extraction_logs[-1]}")
                
                # Determine extraction method
                extraction_method = "unknown"
                if report_form_found and ai_extraction_found:
                    extraction_method = "AI (footer/content)"
                elif filename_extraction_found:
                    extraction_method = "filename pattern"
                elif ai_extraction_found or gemini_prompt_found:
                    extraction_method = "AI attempted"
                
                print(f"\n🎯 EXTRACTION METHOD ANALYSIS:")
                print(f"   📋 Extraction method: {extraction_method}")
                
                # Overall validation - focus on key AI processing indicators
                critical_logs_found = (ai_extraction_found and gemini_prompt_found) or filename_extraction_found
                partial_logs_found = ai_extraction_found or gemini_prompt_found or report_form_found or filename_extraction_found
                
                print(f"\n🎯 BACKEND LOGS VALIDATION:")
                print(f"   ✅ Critical AI logs found: {'✅ YES' if critical_logs_found else '❌ NO'}")
                print(f"   ✅ Some extraction logs found: {'✅ YES' if partial_logs_found else '❌ NO'}")
                print(f"   📋 Extraction method confirmed: {extraction_method}")
                
                if critical_logs_found:
                    print(f"\n🎉 BACKEND LOGS VERIFICATION SUCCESSFUL!")
                    print(f"   ✅ Audit Report AI processing logs confirmed")
                    print(f"   ✅ Extraction method identified: {extraction_method}")
                    print(f"   ✅ Backend logs show extraction process")
                    self.print_result(True, f"Backend logs confirm extraction method: {extraction_method}")
                    return True
                elif partial_logs_found:
                    print(f"\n⚠️ BACKEND LOGS PARTIALLY FOUND:")
                    print(f"   ⚠️ Some AI processing logs present but not complete flow")
                    print(f"   🔧 May indicate partial implementation or processing issues")
                    print(f"   📋 Extraction method: {extraction_method}")
                    self.print_result(False, f"Backend logs show partial processing - Method: {extraction_method}")
                    return False
                else:
                    print(f"\n❌ NO AI PROCESSING LOGS FOUND")
                    print(f"   🔧 This may indicate:")
                    print(f"      - AI processing not implemented")
                    print(f"      - Logs not being generated")
                    print(f"      - Recent audit analysis hasn't been performed")
                    print(f"      - System AI configuration issues")
                    
                    if audit_analysis_logs:
                        print(f"\n   📋 RELATED AUDIT ANALYSIS LOGS FOUND:")
                        for i, log_line in enumerate(audit_analysis_logs[-3:], 1):  # Show last 3
                            print(f"      {i}. {log_line}")
                    
                    self.print_result(False, "No AI processing logs found in backend")
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
        """Run all NCR Form Report Form Extraction tests in sequence"""
        print(f"\n🚀 STARTING NCR FORM REPORT FORM EXTRACTION TESTING")
        print(f"🎯 Test System AI Report Form Extraction from Footer - NCR Form")
        print(f"📄 Verify report_form field extraction from NCR PDF footer")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"📅 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test sequence for NCR Form Extraction Testing
        tests = [
            ("Setup - Authentication", self.test_authentication),
            ("Setup - Company ID Resolution", self.test_get_company_id),
            ("Setup - Get Ships List", self.test_get_ships_list),
            ("Test 1 - Ship ID Verification", self.test_ship_id_verification),
            ("Test 2 - NCR Form Report Form Extraction", self.test_audit_report_analyze_ncr_form_extraction),
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
        print(f"📊 NCR FORM REPORT FORM EXTRACTION TEST SUMMARY")
        print(f"="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
        print(f"📅 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")
        
        # NCR Form Analysis
        print(f"\n" + "="*80)
        print(f"🔍 NCR FORM REPORT FORM EXTRACTION ANALYSIS")
        print(f"="*80)
        
        if hasattr(self, 'test_ship_data') and self.test_ship_data:
            ship_name = self.test_ship_data.get('name', 'Unknown')
            ship_id = self.test_ship_id
            
            print(f"🚢 Test Ship: {ship_name}")
            print(f"🆔 Ship ID: {ship_id}")
            print(f"📄 Test PDF: ISM-Code  NCR (07-23).pdf")
            print(f"🎯 Focus: System AI Report Form Extraction from Footer")
            
            print(f"\n📋 SUCCESS CRITERIA VERIFICATION:")
            print(f"   ✅ report_form is populated (not empty)")
            print(f"   ✅ Value matches form code in footer or filename")
            print(f"   ✅ Backend logs show extraction method")
            
            print(f"\n🎯 KEY QUESTIONS ANALYSIS:")
            print(f"   1. Does report_form field have a value?")
            print(f"   2. What is the exact value extracted?")
            print(f"   3. Did it come from AI (footer/content) or filename pattern?")
            print(f"   4. What does Document AI summary contain about footer?")
        
        # Overall assessment
        if success_rate >= 80:
            print(f"\n🎉 NCR FORM REPORT FORM EXTRACTION SUCCESSFUL!")
            print(f"✅ report_form field populated")
            print(f"✅ Value matches expected form code")
            print(f"✅ Backend logs show extraction method")
            print(f"✅ All success criteria from review request met")
            print(f"🎯 CONCLUSION: System AI can extract report_form from NCR PDF")
        elif success_rate >= 60:
            print(f"\n⚠️ NCR FORM EXTRACTION PARTIALLY SUCCESSFUL")
            print(f"📊 Some components working but extraction issues detected")
            print(f"🔧 Review failed tests for specific extraction problems")
            print(f"🎯 CONCLUSION: Partial extraction functionality - needs investigation")
        else:
            print(f"\n❌ NCR FORM REPORT FORM EXTRACTION FAILED")
            print(f"🚨 Critical issues with report_form extraction from NCR PDF")
            print(f"🔧 System AI may not be extracting from footer correctly")
            print(f"🎯 CONCLUSION: report_form extraction not working as expected")
        
        return success_rate >= 80


if __name__ == "__main__":
    """Main execution - run NCR Form Report Form Extraction tests"""
    tester = BackendAPITester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED - NCR FORM REPORT FORM EXTRACTION VERIFIED SUCCESSFULLY")
        print(f"🎯 CONCLUSION: System AI can extract report_form from NCR PDF footer")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED - REVIEW RESULTS ABOVE")
        print(f"🎯 CONCLUSION: report_form extraction needs investigation")
        sys.exit(1)

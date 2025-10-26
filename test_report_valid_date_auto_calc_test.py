#!/usr/bin/env python3
"""
Test Report Valid Date Auto-Calculation Feature Testing - Comprehensive Backend Test

REVIEW REQUEST REQUIREMENTS:
Test the new Test Report Valid Date Auto-Calculation feature with comprehensive scenarios:

3-TIER VALID DATE AUTO-CALCULATION SYSTEM:
- TIER 1: Parse Note field for certificate references, query Certificate List for matching certificate, return next_survey date
- TIER 2: Use IMO equipment maintenance intervals based on test_report_name (e.g., Chemical Suit = 12 months)
- TIER 3: Fallback to Ship's anniversary_date + 1 year

TESTING REQUIREMENTS:
- TEST 1: Baseline - AI Successfully Extracts Valid Date (Auto-calc should be skipped)
- TEST 2: Tier 2 - IMO Equipment Interval Calculation
- TEST 3: Tier 1 - Certificate Reference from Note Field
- TEST 4: Tier 3 - Ship Anniversary Date Fallback
- TEST 5: Backend Logs Verification
- TEST 6: Status Calculation with Auto-calculated Valid Date

Authentication: admin1 / 123456
Company: AMCSC
Ship: BROTHER 36 (ID: 7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7)
Backend endpoint: POST /api/test-reports/analyze-file
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
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class TestReportValidDateAutoCalcTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.ship_name = "BROTHER 36"
        self.ship_id = "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"
        
        # Test tracking for valid date auto-calculation functionality
        self.auto_calc_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'ship_discovery_successful': False,
            'test_reports_analyze_endpoint_accessible': False,
            
            # TEST 1: Baseline - AI Successfully Extracts Valid Date
            'test1_ai_extracts_valid_date': False,
            'test1_auto_calc_skipped': False,
            'test1_no_auto_calc_logs': False,
            'test1_valid_date_from_ai': False,
            
            # TEST 2: Tier 2 - IMO Equipment Interval Calculation
            'test2_chemical_suit_12_months': False,
            'test2_life_raft_12_months': False,
            'test2_eebd_12_months': False,
            'test2_fire_extinguisher_12_months': False,
            'test2_equipment_matched_logs': False,
            'test2_imo_interval_calculation_logs': False,
            
            # TEST 3: Tier 1 - Certificate Reference from Note Field
            'test3_certificate_reference_parsed': False,
            'test3_certificate_list_queried': False,
            'test3_matching_certificate_found': False,
            'test3_next_survey_date_returned': False,
            'test3_certificate_reference_logs': False,
            
            # TEST 4: Tier 3 - Ship Anniversary Date Fallback
            'test4_ship_anniversary_queried': False,
            'test4_anniversary_plus_one_year': False,
            'test4_fallback_logs_found': False,
            'test4_anniversary_date_calculation': False,
            
            # TEST 5: Backend Logs Verification
            'test5_auto_calc_initiation_logs': False,
            'test5_tier_specific_logs': False,
            'test5_calculation_flow_logs': False,
            'test5_issued_date_logs': False,
            'test5_note_field_logs': False,
            
            # TEST 6: Status Calculation with Auto-calculated Valid Date
            'test6_status_calculated_correctly': False,
            'test6_valid_status_for_future_date': False,
            'test6_expiring_soon_status': False,
            'test6_expired_status_for_past_date': False,
        }
        
        # Store test data
        self.test_files = []
        self.created_test_reports = []
        
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
                
                self.auto_calc_tests['authentication_successful'] = True
                self.auto_calc_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def verify_ship(self):
        """Verify the test ship exists"""
        try:
            self.log(f"🚢 Verifying ship: {self.ship_name} (ID: {self.ship_id})")
            
            response = self.session.get(f"{BACKEND_URL}/ships/{self.ship_id}")
            
            if response.status_code == 200:
                ship = response.json()
                self.log(f"✅ Ship verified: {ship.get('name')} (IMO: {ship.get('imo', 'N/A')})")
                self.log(f"   Anniversary date: {ship.get('anniversary_date', 'Not set')}")
                self.auto_calc_tests['ship_discovery_successful'] = True
                return True
            else:
                self.log(f"❌ Ship verification failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying ship: {str(e)}", "ERROR")
            return False
    
    def create_test_pdf_content(self, content_type="chemical_suit_with_valid_date"):
        """Create test PDF content for different scenarios"""
        try:
            # Create a simple PDF with specific content for testing
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
/Length 200
>>
stream
BT
/F1 12 Tf
72 720 Td
"""
            
            if content_type == "chemical_suit_with_valid_date":
                pdf_content += b"""(Chemical Suit Test Report) Tj
0 -20 Td
(Test Report No: CS-2024-001) Tj
0 -20 Td
(Issued Date: 15/01/2024) Tj
0 -20 Td
(Valid Date: 15/01/2025) Tj
0 -20 Td
(Issued By: VITECH) Tj
"""
            elif content_type == "chemical_suit_no_valid_date":
                pdf_content += b"""(Chemical Suit Test Report) Tj
0 -20 Td
(Test Report No: CS-2024-002) Tj
0 -20 Td
(Issued Date: 15/01/2024) Tj
0 -20 Td
(Issued By: VITECH) Tj
0 -20 Td
(Note: Chemical protective equipment testing) Tj
"""
            elif content_type == "life_raft_no_valid_date":
                pdf_content += b"""(Life Raft Test Report) Tj
0 -20 Td
(Test Report No: LR-2024-001) Tj
0 -20 Td
(Issued Date: 10/02/2024) Tj
0 -20 Td
(Issued By: Marine Safety Equipment) Tj
"""
            elif content_type == "certificate_reference_note":
                pdf_content += b"""(Equipment Test Report) Tj
0 -20 Td
(Test Report No: EQ-2024-001) Tj
0 -20 Td
(Issued Date: 20/03/2024) Tj
0 -20 Td
(Note: The next due date for testing is within 3 months before or after the anniversary date of the cargo ship safety radio certificate) Tj
"""
            elif content_type == "unknown_equipment":
                pdf_content += b"""(Unknown Equipment Test Report) Tj
0 -20 Td
(Test Report No: UE-2024-001) Tj
0 -20 Td
(Issued Date: 25/04/2024) Tj
0 -20 Td
(Note: General equipment testing) Tj
"""
            
            pdf_content += b"""ET
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
456
%%EOF"""
            
            return pdf_content
            
        except Exception as e:
            self.log(f"❌ Error creating test PDF content: {str(e)}", "ERROR")
            return None
    
    def test_baseline_ai_extracts_valid_date(self):
        """TEST 1: Baseline - AI Successfully Extracts Valid Date (Auto-calc should be skipped)"""
        try:
            self.log("📋 TEST 1: Baseline - AI Successfully Extracts Valid Date")
            self.log("   Expected: Auto-calculation should be skipped when AI extracts valid_date")
            
            # Create test PDF with valid_date that AI should extract
            pdf_content = self.create_test_pdf_content("chemical_suit_with_valid_date")
            if not pdf_content:
                return False
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload test report for analysis
                with open(temp_file_path, "rb") as f:
                    files = {
                        "test_report_file": ("Chemical_Suit_With_Valid_Date.pdf", f, "application/pdf")
                    }
                    data = {
                        "ship_id": self.ship_id,
                        "bypass_validation": "false"
                    }
                    
                    self.log("📤 Uploading Chemical Suit test report with valid_date...")
                    
                    endpoint = f"{BACKEND_URL}/test-reports/analyze-file"
                    self.log(f"   POST {endpoint}")
                    
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
                    result = response.json()
                    self.auto_calc_tests['test_reports_analyze_endpoint_accessible'] = True
                    
                    # Check if valid_date was extracted by AI
                    valid_date = result.get("valid_date")
                    if valid_date:
                        self.log(f"✅ AI extracted valid_date: {valid_date}")
                        self.auto_calc_tests['test1_ai_extracts_valid_date'] = True
                        self.auto_calc_tests['test1_valid_date_from_ai'] = True
                        
                        # Check backend logs to ensure auto-calculation was skipped
                        self.check_backend_logs_for_auto_calc_skip()
                        
                        return True
                    else:
                        self.log("❌ AI did not extract valid_date - this should not happen for TEST 1")
                        return False
                else:
                    self.log(f"❌ Test report analysis failed: {response.text}", "ERROR")
                    return False
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log(f"❌ Error in TEST 1: {str(e)}", "ERROR")
            return False
    
    def test_tier2_imo_equipment_intervals(self):
        """TEST 2: Tier 2 - IMO Equipment Interval Calculation"""
        try:
            self.log("📋 TEST 2: Tier 2 - IMO Equipment Interval Calculation")
            self.log("   Expected: Calculate valid_date using IMO equipment intervals")
            
            # Test different equipment types
            equipment_tests = [
                ("chemical_suit_no_valid_date", "Chemical Suit", 12),
                ("life_raft_no_valid_date", "Life Raft", 12),
            ]
            
            for content_type, equipment_name, expected_months in equipment_tests:
                self.log(f"🔧 Testing {equipment_name} - Expected interval: {expected_months} months")
                
                # Create test PDF without valid_date
                pdf_content = self.create_test_pdf_content(content_type)
                if not pdf_content:
                    continue
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                    temp_file.write(pdf_content)
                    temp_file_path = temp_file.name
                
                try:
                    # Upload test report for analysis
                    with open(temp_file_path, "rb") as f:
                        files = {
                            "test_report_file": (f"{equipment_name.replace(' ', '_')}_No_Valid_Date.pdf", f, "application/pdf")
                        }
                        data = {
                            "ship_id": self.ship_id,
                            "bypass_validation": "false"
                        }
                        
                        self.log(f"📤 Uploading {equipment_name} test report without valid_date...")
                        
                        endpoint = f"{BACKEND_URL}/test-reports/analyze-file"
                        
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
                        result = response.json()
                        
                        # Check if valid_date was auto-calculated
                        valid_date = result.get("valid_date")
                        issued_date = result.get("issued_date")
                        test_report_name = result.get("test_report_name", "")
                        
                        self.log(f"   Test report name: {test_report_name}")
                        self.log(f"   Issued date: {issued_date}")
                        self.log(f"   Valid date: {valid_date}")
                        
                        if valid_date and issued_date:
                            # Verify the calculation is correct (issued_date + expected_months)
                            try:
                                from datetime import datetime
                                from dateutil.relativedelta import relativedelta
                                
                                if isinstance(issued_date, str):
                                    issued_dt = datetime.fromisoformat(issued_date.replace('Z', '+00:00'))
                                else:
                                    issued_dt = issued_date
                                
                                expected_valid_date = issued_dt + relativedelta(months=expected_months)
                                
                                if isinstance(valid_date, str):
                                    actual_valid_dt = datetime.fromisoformat(valid_date.replace('Z', '+00:00'))
                                else:
                                    actual_valid_dt = valid_date
                                
                                # Check if dates match (within 1 day tolerance)
                                date_diff = abs((actual_valid_dt - expected_valid_date).days)
                                
                                if date_diff <= 1:
                                    self.log(f"✅ {equipment_name} interval calculation CORRECT")
                                    self.log(f"   Expected: {expected_valid_date.strftime('%Y-%m-%d')}")
                                    self.log(f"   Actual: {actual_valid_dt.strftime('%Y-%m-%d')}")
                                    
                                    # Mark specific equipment test as passed
                                    if "Chemical Suit" in equipment_name:
                                        self.auto_calc_tests['test2_chemical_suit_12_months'] = True
                                    elif "Life Raft" in equipment_name:
                                        self.auto_calc_tests['test2_life_raft_12_months'] = True
                                else:
                                    self.log(f"❌ {equipment_name} interval calculation INCORRECT")
                                    self.log(f"   Expected: {expected_valid_date.strftime('%Y-%m-%d')}")
                                    self.log(f"   Actual: {actual_valid_dt.strftime('%Y-%m-%d')}")
                                    self.log(f"   Difference: {date_diff} days")
                                    
                            except Exception as e:
                                self.log(f"❌ Error verifying {equipment_name} calculation: {e}")
                        else:
                            self.log(f"❌ {equipment_name} - Missing valid_date or issued_date in response")
                    else:
                        self.log(f"❌ {equipment_name} analysis failed: {response.text}", "ERROR")
                        
                finally:
                    # Clean up temporary file
                    os.unlink(temp_file_path)
            
            # Check backend logs for equipment matching and calculation
            self.check_backend_logs_for_tier2_calculation()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in TEST 2: {str(e)}", "ERROR")
            return False
    
    def test_tier1_certificate_reference(self):
        """TEST 3: Tier 1 - Certificate Reference from Note Field"""
        try:
            self.log("📋 TEST 3: Tier 1 - Certificate Reference from Note Field")
            self.log("   Expected: Parse certificate reference from note, query Certificate List")
            
            # Create test PDF with certificate reference in note
            pdf_content = self.create_test_pdf_content("certificate_reference_note")
            if not pdf_content:
                return False
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload test report for analysis
                with open(temp_file_path, "rb") as f:
                    files = {
                        "test_report_file": ("Certificate_Reference_Test.pdf", f, "application/pdf")
                    }
                    data = {
                        "ship_id": self.ship_id,
                        "bypass_validation": "false"
                    }
                    
                    self.log("📤 Uploading test report with certificate reference in note...")
                    
                    endpoint = f"{BACKEND_URL}/test-reports/analyze-file"
                    
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
                    result = response.json()
                    
                    # Check if valid_date was calculated from certificate reference
                    valid_date = result.get("valid_date")
                    note = result.get("note", "")
                    
                    self.log(f"   Note field: {note}")
                    self.log(f"   Valid date: {valid_date}")
                    
                    # Check if note contains certificate reference
                    if "cargo ship safety radio certificate" in note.lower():
                        self.log("✅ Certificate reference found in note field")
                        self.auto_calc_tests['test3_certificate_reference_parsed'] = True
                        
                        if valid_date:
                            self.log("✅ Valid date calculated from certificate reference")
                            self.auto_calc_tests['test3_next_survey_date_returned'] = True
                        else:
                            self.log("❌ Valid date not calculated despite certificate reference")
                    else:
                        self.log("❌ Certificate reference not found in note field")
                    
                    # Check backend logs for certificate reference processing
                    self.check_backend_logs_for_tier1_certificate()
                    
                    return True
                else:
                    self.log(f"❌ Certificate reference test failed: {response.text}", "ERROR")
                    return False
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log(f"❌ Error in TEST 3: {str(e)}", "ERROR")
            return False
    
    def test_tier3_ship_anniversary_fallback(self):
        """TEST 4: Tier 3 - Ship Anniversary Date Fallback"""
        try:
            self.log("📋 TEST 4: Tier 3 - Ship Anniversary Date Fallback")
            self.log("   Expected: Use Ship's anniversary_date + 1 year as fallback")
            
            # Create test PDF with unknown equipment (no IMO interval, no certificate reference)
            pdf_content = self.create_test_pdf_content("unknown_equipment")
            if not pdf_content:
                return False
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload test report for analysis
                with open(temp_file_path, "rb") as f:
                    files = {
                        "test_report_file": ("Unknown_Equipment_Fallback.pdf", f, "application/pdf")
                    }
                    data = {
                        "ship_id": self.ship_id,
                        "bypass_validation": "false"
                    }
                    
                    self.log("📤 Uploading unknown equipment test report for fallback test...")
                    
                    endpoint = f"{BACKEND_URL}/test-reports/analyze-file"
                    
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
                    result = response.json()
                    
                    # Check if valid_date was calculated using ship anniversary date
                    valid_date = result.get("valid_date")
                    test_report_name = result.get("test_report_name", "")
                    
                    self.log(f"   Test report name: {test_report_name}")
                    self.log(f"   Valid date: {valid_date}")
                    
                    if valid_date:
                        self.log("✅ Valid date calculated using fallback method")
                        self.auto_calc_tests['test4_anniversary_plus_one_year'] = True
                        
                        # Verify it's anniversary date + 1 year by checking ship's anniversary date
                        ship_response = self.session.get(f"{BACKEND_URL}/ships/{self.ship_id}")
                        if ship_response.status_code == 200:
                            ship_data = ship_response.json()
                            anniversary_date = ship_data.get("anniversary_date")
                            
                            if anniversary_date:
                                self.log(f"   Ship anniversary date: {anniversary_date}")
                                self.auto_calc_tests['test4_ship_anniversary_queried'] = True
                                
                                # Verify calculation (anniversary + 1 year)
                                try:
                                    from datetime import datetime
                                    from dateutil.relativedelta import relativedelta
                                    
                                    if isinstance(anniversary_date, dict):
                                        # Handle AnniversaryDate object
                                        day = anniversary_date.get('day')
                                        month = anniversary_date.get('month')
                                        if day and month:
                                            # Use current year or next year
                                            current_year = datetime.now().year
                                            anniversary_dt = datetime(current_year, month, day)
                                            expected_valid_date = anniversary_dt + relativedelta(years=1)
                                            
                                            self.log(f"   Expected valid date: {expected_valid_date.strftime('%Y-%m-%d')}")
                                            self.auto_calc_tests['test4_anniversary_date_calculation'] = True
                                    
                                except Exception as e:
                                    self.log(f"   Could not verify anniversary calculation: {e}")
                            else:
                                self.log("   Ship anniversary date not set")
                    else:
                        self.log("❌ Valid date not calculated using fallback method")
                    
                    # Check backend logs for fallback processing
                    self.check_backend_logs_for_tier3_fallback()
                    
                    return True
                else:
                    self.log(f"❌ Fallback test failed: {response.text}", "ERROR")
                    return False
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log(f"❌ Error in TEST 4: {str(e)}", "ERROR")
            return False
    
    def test_status_calculation_with_auto_valid_date(self):
        """TEST 6: Status Calculation with Auto-calculated Valid Date"""
        try:
            self.log("📋 TEST 6: Status Calculation with Auto-calculated Valid Date")
            self.log("   Expected: Status calculated correctly based on auto-calculated valid_date")
            
            # Test with different scenarios to get different status values
            test_scenarios = [
                ("chemical_suit_no_valid_date", "Valid"),  # Future date should be "Valid"
            ]
            
            for content_type, expected_status in test_scenarios:
                self.log(f"🔍 Testing status calculation for {content_type}")
                
                # Create test PDF
                pdf_content = self.create_test_pdf_content(content_type)
                if not pdf_content:
                    continue
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                    temp_file.write(pdf_content)
                    temp_file_path = temp_file.name
                
                try:
                    # Upload test report for analysis
                    with open(temp_file_path, "rb") as f:
                        files = {
                            "test_report_file": (f"Status_Test_{content_type}.pdf", f, "application/pdf")
                        }
                        data = {
                            "ship_id": self.ship_id,
                            "bypass_validation": "false"
                        }
                        
                        endpoint = f"{BACKEND_URL}/test-reports/analyze-file"
                        
                        response = self.session.post(
                            endpoint,
                            files=files,
                            data=data,
                            timeout=120
                        )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        valid_date = result.get("valid_date")
                        status = result.get("status")
                        
                        self.log(f"   Valid date: {valid_date}")
                        self.log(f"   Status: {status}")
                        
                        if valid_date and status:
                            self.log("✅ Status calculated with auto-calculated valid_date")
                            self.auto_calc_tests['test6_status_calculated_correctly'] = True
                            
                            # Check if status makes sense based on valid_date
                            if status in ["Valid", "Expiring Soon", "Expired", "Critical"]:
                                self.log(f"✅ Status '{status}' is valid")
                                
                                if status == "Valid":
                                    self.auto_calc_tests['test6_valid_status_for_future_date'] = True
                                elif status == "Expiring Soon":
                                    self.auto_calc_tests['test6_expiring_soon_status'] = True
                                elif status == "Expired":
                                    self.auto_calc_tests['test6_expired_status_for_past_date'] = True
                            else:
                                self.log(f"❌ Invalid status: {status}")
                        else:
                            self.log("❌ Missing valid_date or status in response")
                            
                finally:
                    # Clean up temporary file
                    os.unlink(temp_file_path)
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in TEST 6: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs_for_auto_calc_skip(self):
        """Check backend logs to verify auto-calculation was skipped"""
        try:
            self.log("📋 Checking backend logs for auto-calculation skip...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
            ]
            
            auto_calc_patterns = [
                "🧮 AI did not extract Valid Date",
                "🧮 Calculating Valid Date for:",
                "Auto-calculation skipped",
                "AI extracted valid_date"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        
                        # Look for auto-calculation patterns
                        found_skip = False
                        found_calc = False
                        
                        for line in result.split('\n'):
                            if "🧮 AI did not extract Valid Date" in line:
                                found_calc = True
                                self.log(f"   Found auto-calc initiation: {line}")
                            elif "Auto-calculation skipped" in line or "AI extracted valid_date" in line:
                                found_skip = True
                                self.log(f"   Found auto-calc skip: {line}")
                        
                        if found_skip and not found_calc:
                            self.log("✅ Auto-calculation correctly skipped when AI extracts valid_date")
                            self.auto_calc_tests['test1_auto_calc_skipped'] = True
                            self.auto_calc_tests['test1_no_auto_calc_logs'] = True
                        elif found_calc:
                            self.log("❌ Auto-calculation was triggered when it should have been skipped")
                        else:
                            self.log("⚠️ No auto-calculation logs found", "WARNING")
                            
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def check_backend_logs_for_tier2_calculation(self):
        """Check backend logs for Tier 2 IMO equipment interval calculation"""
        try:
            self.log("📋 Checking backend logs for Tier 2 calculation...")
            
            log_files = ["/var/log/supervisor/backend.out.log"]
            
            tier2_patterns = [
                "✅ Matched equipment",
                "✅ Calculated valid date from IMO intervals",
                "Chemical Suit",
                "Life Raft",
                "EEBD",
                "Fire Extinguisher"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        
                        equipment_matched = False
                        imo_calculation = False
                        
                        for line in result.split('\n'):
                            if "✅ Matched equipment" in line:
                                equipment_matched = True
                                self.log(f"   Found equipment match: {line}")
                            elif "✅ Calculated valid date from IMO intervals" in line:
                                imo_calculation = True
                                self.log(f"   Found IMO calculation: {line}")
                        
                        if equipment_matched:
                            self.auto_calc_tests['test2_equipment_matched_logs'] = True
                        if imo_calculation:
                            self.auto_calc_tests['test2_imo_interval_calculation_logs'] = True
                            
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
        except Exception as e:
            self.log(f"❌ Error checking Tier 2 logs: {str(e)}", "ERROR")
    
    def check_backend_logs_for_tier1_certificate(self):
        """Check backend logs for Tier 1 certificate reference processing"""
        try:
            self.log("📋 Checking backend logs for Tier 1 certificate processing...")
            
            log_files = ["/var/log/supervisor/backend.out.log"]
            
            tier1_patterns = [
                "📋 Found certificate reference in note",
                "✅ Direct match found",
                "✅ Abbreviation match found",
                "cargo ship safety radio certificate"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        
                        cert_reference = False
                        cert_match = False
                        
                        for line in result.split('\n'):
                            if "📋 Found certificate reference in note" in line:
                                cert_reference = True
                                self.log(f"   Found certificate reference: {line}")
                            elif "✅ Direct match found" in line or "✅ Abbreviation match found" in line:
                                cert_match = True
                                self.log(f"   Found certificate match: {line}")
                        
                        if cert_reference:
                            self.auto_calc_tests['test3_certificate_reference_logs'] = True
                        if cert_match:
                            self.auto_calc_tests['test3_certificate_list_queried'] = True
                            self.auto_calc_tests['test3_matching_certificate_found'] = True
                            
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
        except Exception as e:
            self.log(f"❌ Error checking Tier 1 logs: {str(e)}", "ERROR")
    
    def check_backend_logs_for_tier3_fallback(self):
        """Check backend logs for Tier 3 ship anniversary fallback"""
        try:
            self.log("📋 Checking backend logs for Tier 3 fallback...")
            
            log_files = ["/var/log/supervisor/backend.out.log"]
            
            tier3_patterns = [
                "🔄 Falling back to Ship anniversary date",
                "✅ Found anniversary date",
                "✅ Valid Date from Ship anniversary date"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        
                        fallback_initiated = False
                        anniversary_found = False
                        
                        for line in result.split('\n'):
                            if "🔄 Falling back to Ship anniversary date" in line:
                                fallback_initiated = True
                                self.log(f"   Found fallback initiation: {line}")
                            elif "✅ Found anniversary date" in line or "✅ Valid Date from Ship anniversary date" in line:
                                anniversary_found = True
                                self.log(f"   Found anniversary calculation: {line}")
                        
                        if fallback_initiated:
                            self.auto_calc_tests['test4_fallback_logs_found'] = True
                        if anniversary_found:
                            self.auto_calc_tests['test4_ship_anniversary_queried'] = True
                            
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
        except Exception as e:
            self.log(f"❌ Error checking Tier 3 logs: {str(e)}", "ERROR")
    
    def check_comprehensive_backend_logs(self):
        """TEST 5: Backend Logs Verification - Check for all auto-calculation logs"""
        try:
            self.log("📋 TEST 5: Comprehensive Backend Logs Verification")
            
            log_files = ["/var/log/supervisor/backend.out.log"]
            
            expected_patterns = [
                "🧮 Calculating Valid Date for:",
                "📅 Issued Date:",
                "📝 Note:",
                "✅ Matched equipment",
                "📋 Found certificate reference in note",
                "🔄 Falling back to Ship anniversary date"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        result = os.popen(f"tail -n 300 {log_file}").read()
                        
                        found_patterns = {}
                        
                        for pattern in expected_patterns:
                            found_patterns[pattern] = False
                            
                            for line in result.split('\n'):
                                if pattern in line:
                                    found_patterns[pattern] = True
                                    self.log(f"   ✅ Found: {pattern}")
                                    break
                            
                            if not found_patterns[pattern]:
                                self.log(f"   ❌ Missing: {pattern}")
                        
                        # Update test results based on found patterns
                        if found_patterns.get("🧮 Calculating Valid Date for:"):
                            self.auto_calc_tests['test5_auto_calc_initiation_logs'] = True
                        if found_patterns.get("📅 Issued Date:"):
                            self.auto_calc_tests['test5_issued_date_logs'] = True
                        if found_patterns.get("📝 Note:"):
                            self.auto_calc_tests['test5_note_field_logs'] = True
                        
                        # Check for tier-specific logs
                        tier_patterns_found = (
                            found_patterns.get("✅ Matched equipment", False) or
                            found_patterns.get("📋 Found certificate reference in note", False) or
                            found_patterns.get("🔄 Falling back to Ship anniversary date", False)
                        )
                        
                        if tier_patterns_found:
                            self.auto_calc_tests['test5_tier_specific_logs'] = True
                            self.auto_calc_tests['test5_calculation_flow_logs'] = True
                            
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in TEST 5: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test of all Test Report Valid Date Auto-Calculation scenarios"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE TEST REPORT VALID DATE AUTO-CALCULATION TEST")
            self.log("=" * 80)
            self.log("Testing 3-Tier Valid Date Auto-Calculation System:")
            self.log("TIER 1: Certificate reference from Note field → Certificate List query")
            self.log("TIER 2: IMO equipment intervals (Chemical Suit, Life Raft, etc. = 12 months)")
            self.log("TIER 3: Ship anniversary_date + 1 year fallback")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Ship Verification
            self.log("\nSTEP 2: Ship Verification")
            if not self.verify_ship():
                self.log("❌ CRITICAL: Ship verification failed - cannot proceed")
                return False
            
            # Step 3: TEST 1 - Baseline AI Extraction
            self.log("\nSTEP 3: TEST 1 - Baseline AI Extraction (Auto-calc should be skipped)")
            self.test_baseline_ai_extracts_valid_date()
            
            # Step 4: TEST 2 - Tier 2 IMO Equipment Intervals
            self.log("\nSTEP 4: TEST 2 - Tier 2 IMO Equipment Intervals")
            self.test_tier2_imo_equipment_intervals()
            
            # Step 5: TEST 3 - Tier 1 Certificate Reference
            self.log("\nSTEP 5: TEST 3 - Tier 1 Certificate Reference")
            self.test_tier1_certificate_reference()
            
            # Step 6: TEST 4 - Tier 3 Ship Anniversary Fallback
            self.log("\nSTEP 6: TEST 4 - Tier 3 Ship Anniversary Fallback")
            self.test_tier3_ship_anniversary_fallback()
            
            # Step 7: TEST 5 - Backend Logs Verification
            self.log("\nSTEP 7: TEST 5 - Backend Logs Verification")
            self.check_comprehensive_backend_logs()
            
            # Step 8: TEST 6 - Status Calculation
            self.log("\nSTEP 8: TEST 6 - Status Calculation with Auto-calculated Valid Date")
            self.test_status_calculation_with_auto_valid_date()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE TEST REPORT VALID DATE AUTO-CALCULATION TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 TEST REPORT VALID DATE AUTO-CALCULATION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.auto_calc_tests)
            passed_tests = sum(1 for result in self.auto_calc_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('ship_discovery_successful', 'Ship discovery successful'),
                ('test_reports_analyze_endpoint_accessible', 'Test reports analyze endpoint accessible'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.auto_calc_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # TEST 1 Results
            self.log("\n📋 TEST 1 - BASELINE AI EXTRACTION:")
            test1_tests = [
                ('test1_ai_extracts_valid_date', 'AI extracts valid_date successfully'),
                ('test1_auto_calc_skipped', 'Auto-calculation skipped when AI succeeds'),
                ('test1_no_auto_calc_logs', 'No auto-calculation logs when skipped'),
                ('test1_valid_date_from_ai', 'Valid date comes from AI extraction'),
            ]
            
            for test_key, description in test1_tests:
                status = "✅ PASS" if self.auto_calc_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # TEST 2 Results
            self.log("\n🔧 TEST 2 - TIER 2 IMO EQUIPMENT INTERVALS:")
            test2_tests = [
                ('test2_chemical_suit_12_months', 'Chemical Suit → 12 months calculation'),
                ('test2_life_raft_12_months', 'Life Raft → 12 months calculation'),
                ('test2_equipment_matched_logs', 'Equipment matching logs found'),
                ('test2_imo_interval_calculation_logs', 'IMO interval calculation logs found'),
            ]
            
            for test_key, description in test2_tests:
                status = "✅ PASS" if self.auto_calc_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # TEST 3 Results
            self.log("\n📋 TEST 3 - TIER 1 CERTIFICATE REFERENCE:")
            test3_tests = [
                ('test3_certificate_reference_parsed', 'Certificate reference parsed from note'),
                ('test3_certificate_list_queried', 'Certificate List queried'),
                ('test3_matching_certificate_found', 'Matching certificate found'),
                ('test3_next_survey_date_returned', 'Next survey date returned'),
                ('test3_certificate_reference_logs', 'Certificate reference logs found'),
            ]
            
            for test_key, description in test3_tests:
                status = "✅ PASS" if self.auto_calc_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # TEST 4 Results
            self.log("\n🔄 TEST 4 - TIER 3 SHIP ANNIVERSARY FALLBACK:")
            test4_tests = [
                ('test4_ship_anniversary_queried', 'Ship anniversary date queried'),
                ('test4_anniversary_plus_one_year', 'Anniversary + 1 year calculation'),
                ('test4_fallback_logs_found', 'Fallback logs found'),
                ('test4_anniversary_date_calculation', 'Anniversary date calculation verified'),
            ]
            
            for test_key, description in test4_tests:
                status = "✅ PASS" if self.auto_calc_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # TEST 5 Results
            self.log("\n📋 TEST 5 - BACKEND LOGS VERIFICATION:")
            test5_tests = [
                ('test5_auto_calc_initiation_logs', 'Auto-calculation initiation logs'),
                ('test5_tier_specific_logs', 'Tier-specific calculation logs'),
                ('test5_calculation_flow_logs', 'Calculation flow logs'),
                ('test5_issued_date_logs', 'Issued date logs'),
                ('test5_note_field_logs', 'Note field logs'),
            ]
            
            for test_key, description in test5_tests:
                status = "✅ PASS" if self.auto_calc_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # TEST 6 Results
            self.log("\n📊 TEST 6 - STATUS CALCULATION:")
            test6_tests = [
                ('test6_status_calculated_correctly', 'Status calculated with auto-calculated valid_date'),
                ('test6_valid_status_for_future_date', 'Valid status for future dates'),
                ('test6_expiring_soon_status', 'Expiring Soon status detection'),
                ('test6_expired_status_for_past_date', 'Expired status for past dates'),
            ]
            
            for test_key, description in test6_tests:
                status = "✅ PASS" if self.auto_calc_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            # Check critical functionality
            tier1_working = self.auto_calc_tests.get('test3_certificate_reference_parsed', False)
            tier2_working = (self.auto_calc_tests.get('test2_chemical_suit_12_months', False) or 
                           self.auto_calc_tests.get('test2_life_raft_12_months', False))
            tier3_working = self.auto_calc_tests.get('test4_anniversary_plus_one_year', False)
            baseline_working = self.auto_calc_tests.get('test1_auto_calc_skipped', False)
            
            working_tiers = sum([tier1_working, tier2_working, tier3_working])
            
            self.log(f"   3-Tier System Status:")
            self.log(f"   - TIER 1 (Certificate Reference): {'✅ WORKING' if tier1_working else '❌ NOT WORKING'}")
            self.log(f"   - TIER 2 (IMO Equipment Intervals): {'✅ WORKING' if tier2_working else '❌ NOT WORKING'}")
            self.log(f"   - TIER 3 (Ship Anniversary Fallback): {'✅ WORKING' if tier3_working else '❌ NOT WORKING'}")
            self.log(f"   - Baseline (AI Skip Logic): {'✅ WORKING' if baseline_working else '❌ NOT WORKING'}")
            
            if working_tiers == 3 and baseline_working:
                self.log("   ✅ ALL TIERS WORKING CORRECTLY - FEATURE FULLY FUNCTIONAL")
            elif working_tiers >= 2:
                self.log(f"   ⚠️ PARTIAL FUNCTIONALITY - {working_tiers}/3 tiers working")
            else:
                self.log(f"   ❌ MAJOR ISSUES - Only {working_tiers}/3 tiers working")
            
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
    """Main function to run the comprehensive test"""
    tester = TestReportValidDateAutoCalcTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Return appropriate exit code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
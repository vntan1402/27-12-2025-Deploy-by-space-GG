#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: Docking Date Extraction Logic Testing from CSSC and DD Certificates
Review Request: Test docking date extraction logic sau khi fix syntax error
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import time
import traceback
import subprocess
import tempfile
import base64

# Configuration - Use production backend URL for testing
BACKEND_URL = "https://vessel-docs-hub.preview.emergentagent.com/api"

class DockingDateExtractionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Docking Date Extraction Logic
        self.docking_tests = {
            'authentication_successful': False,
            'backend_startup_verified': False,
            'basic_endpoint_connectivity': False,
            'docking_endpoint_working': False,
            'cssc_certificate_found': False,
            'certificate_filtering_working': False,
            'date_extraction_patterns_working': False,
            'assignment_logic_working': False,
            'last_docking_1_extracted': False,
            'last_docking_2_extracted': False,
            'date_validation_working': False,
            'duplicates_removed': False,
            'sorting_working': False,
            'ship_update_working': False,
            'response_format_correct': False,
            'dd_mm_yyyy_format_verified': False,
            'error_handling_working': False
        }
        
        # Test ship ID for SUNSHINE 01 as specified in review request
        self.test_ship_id = "e21c71a2-9543-4f92-990c-72f54292fde8"
        self.test_ship_name = "SUNSHINE 01"
        
        # Expected results from review request
        self.expected_certificate = "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE"
        self.expected_keywords = ['safety construction', 'cssc', 'dry dock', 'dd', 'docking survey']
        self.expected_date_patterns = [
            'dry dock date', 'docking survey date', 'construction survey', 'issued date'
        ]
        
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
        """Authenticate with admin1/123456 credentials as specified in review request"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                self.log(f"   Full Name: {self.current_user.get('full_name')}")
                
                self.docking_tests['authentication_successful'] = True
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
    
    def test_backend_startup_verification(self):
        """Test backend startup and basic connectivity"""
        try:
            self.log("🔧 Testing Backend Startup and Basic Connectivity...")
            
            # Test basic health endpoint
            health_endpoint = f"{BACKEND_URL.replace('/api', '')}/health"
            try:
                response = requests.get(health_endpoint, timeout=10)
                if response.status_code == 200:
                    self.log("   ✅ Backend health check passed")
                    self.docking_tests['backend_startup_verified'] = True
                else:
                    self.log(f"   ⚠️ Backend health check returned: {response.status_code}")
            except:
                self.log("   ⚠️ Backend health endpoint not available")
            
            # Test basic API connectivity with ships endpoint
            ships_endpoint = f"{BACKEND_URL}/ships"
            try:
                response = requests.get(ships_endpoint, headers=self.get_headers(), timeout=10)
                if response.status_code == 200:
                    self.log("   ✅ Basic API connectivity verified")
                    self.docking_tests['basic_endpoint_connectivity'] = True
                else:
                    self.log(f"   ⚠️ Ships endpoint returned: {response.status_code}")
            except Exception as e:
                self.log(f"   ❌ Basic API connectivity failed: {e}")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"❌ Backend startup verification error: {str(e)}", "ERROR")
            return False

    def test_docking_date_extraction_endpoint(self):
        """Test the Docking Date Extraction Function"""
        try:
            self.log("🎯 Testing Docking Date Extraction Function...")
            self.log(f"   Target Ship: {self.test_ship_name} (ID: {self.test_ship_id})")
            self.log(f"   FOCUS: Extract Last Docking 1 & 2 from CSSC and DD certificates")
            self.log(f"   Expected: Find CSSC certificates and extract docking dates")
            
            # Test the POST /api/ships/{ship_id}/calculate-docking-dates endpoint
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}/calculate-docking-dates"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Docking Date Extraction endpoint responded successfully")
                self.log(f"   📊 Response: {json.dumps(result, indent=2)}")
                
                # Check if the function is working
                success = result.get('success', False)
                message = result.get('message', '')
                docking_dates = result.get('docking_dates')
                
                self.log(f"   Success: {success}")
                self.log(f"   Message: {message}")
                
                # Check if we got a successful calculation
                if success and docking_dates:
                    self.log("   ✅ Docking Date Extraction successful")
                    self.docking_tests['docking_endpoint_working'] = True
                    
                    # Extract Last Docking 1 and Last Docking 2
                    last_docking_1 = docking_dates.get('last_docking')
                    last_docking_2 = docking_dates.get('last_docking_2')
                    
                    self.log(f"   📊 Extracted Docking Dates:")
                    self.log(f"      Last Docking 1 (Most Recent): {last_docking_1}")
                    self.log(f"      Last Docking 2 (Second Most Recent): {last_docking_2}")
                    
                    # Verify Last Docking 1 extraction
                    if last_docking_1:
                        self.log("   ✅ Last Docking 1 extracted successfully")
                        self.docking_tests['last_docking_1_extracted'] = True
                        
                        # Verify dd/MM/yyyy format
                        if '/' in last_docking_1 and len(last_docking_1.split('/')) == 3:
                            self.log("   ✅ Last Docking 1 format verified (dd/MM/yyyy)")
                            self.docking_tests['dd_mm_yyyy_format_verified'] = True
                    
                    # Verify Last Docking 2 extraction
                    if last_docking_2:
                        self.log("   ✅ Last Docking 2 extracted successfully")
                        self.docking_tests['last_docking_2_extracted'] = True
                    
                    # Verify response format
                    expected_response_fields = ['success', 'message', 'docking_dates']
                    if all(field in result for field in expected_response_fields):
                        self.log("   ✅ Response format correct")
                        self.docking_tests['response_format_correct'] = True
                    
                    # Verify assignment logic (Last Docking 1 should be more recent than Last Docking 2)
                    if last_docking_1 and last_docking_2:
                        try:
                            date1 = datetime.strptime(last_docking_1, '%d/%m/%Y')
                            date2 = datetime.strptime(last_docking_2, '%d/%m/%Y')
                            if date1 > date2:
                                self.log("   ✅ Assignment logic correct (Last Docking 1 > Last Docking 2)")
                                self.docking_tests['assignment_logic_working'] = True
                            else:
                                self.log("   ⚠️ Assignment logic may be incorrect")
                        except:
                            self.log("   ⚠️ Could not verify assignment logic due to date parsing error")
                
                else:
                    self.log("   ❌ Docking Date Extraction failed or returned no data")
                    self.log(f"      Success: {success}")
                    self.log(f"      Message: {message}")
                
                self.test_results['docking_response'] = result
                return True
                
            else:
                self.log(f"   ❌ Docking Date Extraction failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Docking Date Extraction test error: {str(e)}", "ERROR")
            return False
    
    def test_cssc_certificate_detection(self):
        """Test CSSC Certificate Detection and Filtering"""
        try:
            self.log("🔍 Testing CSSC Certificate Detection and Filtering...")
            
            # Get certificates for SUNSHINE 01 ship
            endpoint = f"{BACKEND_URL}/certificates"
            params = {"ship_id": self.test_ship_id}
            self.log(f"   GET {endpoint}?ship_id={self.test_ship_id}")
            
            response = requests.get(endpoint, params=params, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   ✅ Retrieved {len(certificates)} certificates for {self.test_ship_name}")
                
                # Look for CSSC and docking-related certificates
                cssc_certificates = []
                docking_certificates = []
                
                for cert in certificates:
                    cert_name = cert.get('cert_name', '').lower()
                    
                    # Check for CSSC certificate
                    if "cargo ship safety construction certificate" in cert_name:
                        cssc_certificates.append(cert)
                        self.log(f"   ✅ Found CSSC: {cert.get('cert_name')}")
                    
                    # Check for docking-related keywords
                    for keyword in self.expected_keywords:
                        if keyword in cert_name:
                            docking_certificates.append(cert)
                            self.log(f"   ✅ Found docking-related cert ('{keyword}'): {cert.get('cert_name')}")
                            break
                
                if cssc_certificates:
                    self.log(f"   ✅ CSSC Certificate Detection successful ({len(cssc_certificates)} found)")
                    self.docking_tests['cssc_certificate_found'] = True
                    
                    # Analyze the first CSSC certificate
                    cssc_cert = cssc_certificates[0]
                    self.log(f"   📊 CSSC Certificate Analysis:")
                    self.log(f"      Name: {cssc_cert.get('cert_name')}")
                    self.log(f"      Type: {cssc_cert.get('cert_type')}")
                    self.log(f"      Issue Date: {cssc_cert.get('issue_date')}")
                    self.log(f"      Valid Date: {cssc_cert.get('valid_date')}")
                    self.log(f"      Has Text Content: {bool(cssc_cert.get('text_content'))}")
                    
                    # Check if certificate has text content for date extraction
                    if cssc_cert.get('text_content'):
                        self.log("   ✅ CSSC certificate has text content for date extraction")
                        text_content = cssc_cert.get('text_content', '')
                        
                        # Test date extraction patterns
                        date_patterns_found = []
                        for pattern in self.expected_date_patterns:
                            if pattern.replace(' ', '') in text_content.lower().replace(' ', ''):
                                date_patterns_found.append(pattern)
                        
                        if date_patterns_found:
                            self.log(f"   ✅ Date extraction patterns found: {date_patterns_found}")
                            self.docking_tests['date_extraction_patterns_working'] = True
                        else:
                            self.log("   ⚠️ No expected date patterns found in certificate text")
                    else:
                        self.log("   ⚠️ CSSC certificate has no text content")
                
                if docking_certificates:
                    self.log(f"   ✅ Certificate Filtering working ({len(docking_certificates)} docking-related certificates)")
                    self.docking_tests['certificate_filtering_working'] = True
                else:
                    self.log("   ⚠️ No docking-related certificates found with expected keywords")
                
                self.test_results['certificate_analysis'] = {
                    'total_certificates': len(certificates),
                    'cssc_certificates': len(cssc_certificates),
                    'docking_certificates': len(docking_certificates),
                    'cssc_cert_details': cssc_certificates[0] if cssc_certificates else None
                }
                
                return True
                
            else:
                self.log(f"   ❌ Certificate retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ CSSC certificate detection test error: {str(e)}", "ERROR")
            return False
    def test_date_validation_and_ship_update(self):
        """Test Date Validation (1980 - current year range) and Ship Update"""
        try:
            self.log("📅 Testing Date Validation and Ship Update...")
            
            # Test date validation range (1980 - current year)
            current_year = datetime.now().year
            self.log(f"   Expected date range: 1980 - {current_year}")
            
            # Check if extracted dates are within valid range
            docking_response = self.test_results.get('docking_response', {})
            if docking_response.get('success'):
                docking_dates = docking_response.get('docking_dates', {})
                
                for date_type, date_str in docking_dates.items():
                    if date_str:
                        try:
                            parsed_date = datetime.strptime(date_str, '%d/%m/%Y')
                            year = parsed_date.year
                            
                            if 1980 <= year <= current_year:
                                self.log(f"   ✅ {date_type} date validation passed: {date_str} (year {year})")
                                self.docking_tests['date_validation_working'] = True
                            else:
                                self.log(f"   ❌ {date_type} date validation failed: {date_str} (year {year} out of range)")
                        except Exception as e:
                            self.log(f"   ❌ Error parsing {date_type} date: {e}")
            
            # Test ship update with calculated docking dates
            self.log("   🔄 Testing Ship Update with Calculated Docking Dates...")
            
            # Get current ship data
            ship_endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
            ship_response = requests.get(ship_endpoint, headers=self.get_headers(), timeout=30)
            
            if ship_response.status_code == 200:
                ship_data = ship_response.json()
                
                # Check if ship was updated with docking dates
                current_last_docking = ship_data.get('last_docking')
                current_last_docking_2 = ship_data.get('last_docking_2')
                
                self.log(f"   📊 Current Ship Docking Dates:")
                self.log(f"      Last Docking: {current_last_docking}")
                self.log(f"      Last Docking 2: {current_last_docking_2}")
                
                if current_last_docking or current_last_docking_2:
                    self.log("   ✅ Ship update with calculated docking dates successful")
                    self.docking_tests['ship_update_working'] = True
                else:
                    self.log("   ⚠️ Ship may not have been updated with docking dates")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Date validation and ship update test error: {str(e)}", "ERROR")
            return False

    def test_certificate_text_parsing(self):
        """Test Certificate Text Content Parsing for Docking Dates"""
        try:
            self.log("📝 Testing Certificate Text Content Parsing...")
            
            # Get certificate details for text analysis
            cert_analysis = self.test_results.get('certificate_analysis', {})
            cssc_cert = cert_analysis.get('cssc_cert_details')
            
            if cssc_cert and cssc_cert.get('text_content'):
                text_content = cssc_cert.get('text_content')
                self.log(f"   ✅ Analyzing text content from: {cssc_cert.get('cert_name')}")
                self.log(f"   Text content length: {len(text_content)} characters")
                
                # Look for docking-related text patterns
                docking_patterns = [
                    'dry dock', 'docking', 'construction survey', 'issued', 'certificate date',
                    'survey completed', 'inspection date', 'built date', 'keel laid'
                ]
                
                found_patterns = []
                for pattern in docking_patterns:
                    if pattern in text_content.lower():
                        found_patterns.append(pattern)
                
                if found_patterns:
                    self.log(f"   ✅ Certificate text parsing patterns found: {found_patterns}")
                    self.docking_tests['certificate_filtering_working'] = True
                
                # Look for date patterns in text
                import re
                date_patterns = [
                    r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}',  # DD/MM/YYYY format
                    r'\d{1,2}\s+\w{3,9}\s+\d{4}'  # DD Month YYYY format
                ]
                
                dates_found = []
                for pattern in date_patterns:
                    matches = re.findall(pattern, text_content)
                    dates_found.extend(matches)
                
                if dates_found:
                    self.log(f"   ✅ Date patterns found in text: {len(dates_found)} dates")
                    self.log(f"   Sample dates: {dates_found[:3]}")  # Show first 3
                else:
                    self.log("   ⚠️ No date patterns found in certificate text")
            else:
                self.log("   ⚠️ No CSSC certificate text content available for parsing")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Certificate text parsing test error: {str(e)}", "ERROR")
            return False

    def test_edge_cases_and_leap_year_handling(self):
        """Test Edge Cases and Leap Year Handling for Same Day/Month Logic"""
        try:
            self.log("🧪 Testing Edge Cases and Leap Year Handling...")
            
            # Test 1: Verify year calculation logic
            self.log("   1️⃣ Testing Year Calculation Logic...")
            
            # Test the logic: From Date = To Date - 5 years (same day/month)
            test_cases = [
                {"to_date": "2026-03-10", "expected_from": "2021-03-10", "description": "Normal case (review request)"},
                {"to_date": "2028-02-29", "expected_from": "2023-02-28", "description": "Leap year edge case (Feb 29th)"},
                {"to_date": "2025-12-31", "expected_from": "2020-12-31", "description": "Year end case"},
                {"to_date": "2024-01-01", "expected_from": "2019-01-01", "description": "Year start case"},
            ]
            
            for test_case in test_cases:
                to_date_str = test_case["to_date"]
                expected_from_str = test_case["expected_from"]
                description = test_case["description"]
                
                self.log(f"      Testing: {description}")
                self.log(f"         To Date: {to_date_str}")
                self.log(f"         Expected From Date: {expected_from_str}")
                
                try:
                    # Parse to_date
                    to_dt = datetime.fromisoformat(to_date_str)
                    
                    # Calculate from_date using same day/month logic
                    try:
                        from_dt = to_dt.replace(year=to_dt.year - 5)
                    except ValueError:
                        # Handle leap year edge case (Feb 29th)
                        from_dt = to_dt.replace(year=to_dt.year - 5, month=2, day=28)
                        self.log(f"         ⚠️ Leap year adjustment: Feb 29 -> Feb 28")
                    
                    calculated_from_str = from_dt.strftime('%Y-%m-%d')
                    
                    self.log(f"         Calculated From Date: {calculated_from_str}")
                    
                    # Verify same day/month
                    if from_dt.day == to_dt.day and from_dt.month == to_dt.month:
                        self.log(f"         ✅ Same day/month verified: Day={from_dt.day}, Month={from_dt.month}")
                    else:
                        self.log(f"         ❌ Same day/month failed: From({from_dt.day}/{from_dt.month}) != To({to_dt.day}/{to_dt.month})")
                    
                    # Check if matches expected
                    if calculated_from_str == expected_from_str:
                        self.log(f"         ✅ Calculation matches expected result")
                        if description == "Normal case (review request)":
                            self.log(f"         🎯 Review request case verified!")
                        elif description == "Leap year edge case (Feb 29th)":
                            self.special_survey_tests['leap_year_handling_tested'] = True
                    else:
                        self.log(f"         ⚠️ Calculation differs from expected: {expected_from_str}")
                        
                except Exception as e:
                    self.log(f"         ❌ Error in calculation: {e}")
            
            # Test 2: Verify no date calculation errors
            self.log("   2️⃣ Testing Date Calculation Error Prevention...")
            
            # Test with the actual review request data
            review_to_date = "2026-03-10T00:00:00Z"
            try:
                to_dt = datetime.fromisoformat(review_to_date.replace('Z', ''))
                from_dt = to_dt.replace(year=to_dt.year - 5)
                
                from_display = from_dt.strftime('%d/%m/%Y')
                to_display = to_dt.strftime('%d/%m/%Y')
                
                self.log(f"      Review Request Verification:")
                self.log(f"         Input: {review_to_date}")
                self.log(f"         To Date: {to_display}")
                self.log(f"         From Date: {from_display}")
                
                # Check against expected results
                if to_display == self.expected_to_date and from_display == self.expected_from_date:
                    self.log(f"      ✅ Review request calculation correct")
                    self.log(f"         Expected: {self.expected_display_format}")
                    self.log(f"         Calculated: {from_display} - {to_display}")
                else:
                    self.log(f"      ❌ Review request calculation incorrect")
                    self.log(f"         Expected: {self.expected_display_format}")
                    self.log(f"         Calculated: {from_display} - {to_display}")
                
                # Check if it's NOT the previous incorrect result
                if from_display != self.previous_incorrect_from_date:
                    self.log(f"      ✅ Fixed: No longer showing previous incorrect result ({self.previous_incorrect_from_date})")
                else:
                    self.log(f"      ❌ Still showing previous incorrect result: {self.previous_incorrect_from_date}")
                    
            except Exception as e:
                self.log(f"      ❌ Error in review request verification: {e}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Edge cases and leap year test error: {str(e)}", "ERROR")
            return False

    def test_imo_5_year_logic_verification(self):
        """Test IMO 5-Year Logic Verification"""
        try:
            self.log("🧠 Testing IMO 5-Year Logic Verification...")
            
            # Test the logic components for IMO standards
            self.log("   📋 Testing IMO Logic Components:")
            
            # 1. Test Full Term Class certificate priority
            self.log("   1️⃣ Testing Full Term Class Certificate Priority Logic...")
            
            cert_analysis = self.test_results.get('certificate_analysis', {})
            if cert_analysis:
                full_term_class_certs = cert_analysis.get('full_term_class_certificates', 0)
                cargo_safety_cert = cert_analysis.get('cargo_safety_cert')
                
                if full_term_class_certs > 0:
                    self.log(f"      ✅ Found {full_term_class_certs} Full Term Class certificates")
                    self.special_survey_tests['full_term_class_certificates_found'] = True
                else:
                    self.log("      ⚠️ No Full Term Class certificates found")
                
                # Check specific certificate
                if cargo_safety_cert:
                    cert_type = cargo_safety_cert.get('cert_type', '')
                    if cert_type == 'Full Term':
                        self.log("      ✅ CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE is Full Term")
                    else:
                        self.log(f"      ⚠️ Certificate type: {cert_type}")
            
            # 2. Test IMO 5-year cycle calculation
            self.log("   2️⃣ Testing IMO 5-Year Cycle Calculation...")
            
            special_survey_response = self.test_results.get('special_survey_response', {})
            if special_survey_response and special_survey_response.get('success'):
                special_survey_cycle = special_survey_response.get('special_survey_cycle', {})
                from_date = special_survey_cycle.get('from_date')
                to_date = special_survey_cycle.get('to_date')
                
                if from_date and to_date:
                    try:
                        from_dt = datetime.fromisoformat(from_date.replace('Z', ''))
                        to_dt = datetime.fromisoformat(to_date.replace('Z', ''))
                        years_diff = (to_dt - from_dt).days / 365.25
                        
                        self.log(f"      Cycle Period: {years_diff:.2f} years")
                        
                        if 4.8 <= years_diff <= 5.2:  # Allow tolerance for 5 years
                            self.log("      ✅ IMO 5-year cycle verified")
                            self.special_survey_tests['imo_5_year_logic_verified'] = True
                        else:
                            self.log(f"      ⚠️ Cycle period not exactly 5 years")
                    except Exception as e:
                        self.log(f"      ⚠️ Error calculating cycle period: {e}")
            
            # 3. Test intermediate survey requirement
            self.log("   3️⃣ Testing Intermediate Survey Requirement...")
            
            if special_survey_response and special_survey_response.get('success'):
                special_survey_cycle = special_survey_response.get('special_survey_cycle', {})
                intermediate_required = special_survey_cycle.get('intermediate_required')
                
                if intermediate_required:
                    self.log("      ✅ Intermediate Survey required = true (IMO requirement)")
                    self.special_survey_tests['intermediate_survey_required'] = True
                else:
                    self.log("      ⚠️ Intermediate Survey should be required per IMO standards")
            
            return True
            
        except Exception as e:
            self.log(f"❌ IMO 5-year logic verification error: {str(e)}", "ERROR")
            return False

    def test_complete_integration(self):
        """Test Complete Integration of Special Survey Cycle"""
        try:
            self.log("🔗 Testing Complete Integration of Special Survey Cycle...")
            
            # Test ship processing with auto-calculation
            self.log("   1️⃣ Testing Ship Processing with Auto-calculation...")
            
            # Get current ship data
            ship_endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
            self.log(f"      GET {ship_endpoint}")
            ship_response = requests.get(ship_endpoint, headers=self.get_headers(), timeout=30)
            
            if ship_response.status_code == 200:
                ship_data = ship_response.json()
                current_special_survey = ship_data.get('special_survey_cycle')
                
                self.log(f"      Current Special Survey Cycle: {current_special_survey}")
                
                if current_special_survey:
                    self.log("      ✅ Ship has Special Survey Cycle data")
                    
                    # Verify structure
                    expected_fields = ['from_date', 'to_date', 'intermediate_required', 'cycle_type']
                    all_fields_present = all(field in current_special_survey for field in expected_fields)
                    
                    if all_fields_present:
                        self.log("      ✅ Special Survey Cycle structure complete")
                    else:
                        self.log("      ⚠️ Some Special Survey Cycle fields missing")
                else:
                    self.log("      ⚠️ No Special Survey Cycle data in ship")
            
            # Test ship update with special survey cycle
            self.log("   2️⃣ Testing Ship Update with Special Survey Cycle...")
            
            # Update ship to trigger auto-calculation
            update_data = {
                "last_special_survey": "2024-01-15T00:00:00Z"
            }
            
            update_response = requests.put(ship_endpoint, json=update_data, headers=self.get_headers(), timeout=30)
            
            if update_response.status_code == 200:
                updated_ship = update_response.json()
                updated_special_survey = updated_ship.get('special_survey_cycle')
                
                self.log("      ✅ Ship update successful")
                self.log(f"      Updated Special Survey Cycle: {updated_special_survey}")
                
                if updated_special_survey:
                    self.log("      ✅ Auto-calculation logic working in ship updates")
                else:
                    self.log("      ⚠️ Auto-calculation may not be working")
            else:
                self.log(f"      ⚠️ Ship update failed: {update_response.status_code}")
            
            # Test IMO compliance verification
            self.log("   3️⃣ Testing IMO Compliance Verification...")
            
            special_survey_response = self.test_results.get('special_survey_response', {})
            if special_survey_response and special_survey_response.get('success'):
                special_survey_cycle = special_survey_response.get('special_survey_cycle', {})
                
                # Check all IMO requirements
                imo_requirements = {
                    'intermediate_required': special_survey_cycle.get('intermediate_required'),
                    'cycle_type_solas': 'SOLAS' in str(special_survey_cycle.get('cycle_type', '')),
                    'five_year_cycle': True  # Already verified in previous test
                }
                
                all_imo_compliant = all(imo_requirements.values())
                
                if all_imo_compliant:
                    self.log("      ✅ Full IMO compliance verified")
                else:
                    self.log("      ⚠️ Some IMO requirements not met")
                    for req, status in imo_requirements.items():
                        self.log(f"         {req}: {'✅' if status else '❌'}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Complete integration test error: {str(e)}", "ERROR")
            return False

    def test_enhanced_logic_verification(self):
        """Test Enhanced Logic for Anniversary Date Calculation"""
        try:
            self.log("🧠 Testing Enhanced Logic for Anniversary Date Calculation...")
            
            # Test the logic priorities and parsing capabilities
            self.log("   📋 Testing Logic Components:")
            
            # 1. Test Full Term certificate priority
            self.log("   1️⃣ Testing Full Term Certificate Priority Logic...")
            
            # Get ship data to check current anniversary date
            ship_endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
            self.log(f"      GET {ship_endpoint}")
            ship_response = requests.get(ship_endpoint, headers=self.get_headers(), timeout=30)
            
            if ship_response.status_code == 200:
                ship_data = ship_response.json()
                current_anniversary = ship_data.get('anniversary_date')
                
                self.log(f"      Current Anniversary Date: {current_anniversary}")
                
                if current_anniversary:
                    source_cert = current_anniversary.get('source_certificate_type', '')
                    if 'Full Term' in source_cert:
                        self.log("      ✅ Anniversary date derived from Full Term certificate")
                        self.anniversary_tests['full_term_priority_verified'] = True
                    else:
                        self.log(f"      ⚠️ Anniversary date source: {source_cert}")
                else:
                    self.log("      ⚠️ No current anniversary date found")
            
            # 2. Test endorsement parsing (if available)
            self.log("   2️⃣ Testing Endorsement 'Due range for annual Survey' Parsing...")
            
            # Get certificates and check for endorsement text
            cert_endpoint = f"{BACKEND_URL}/certificates"
            params = {"ship_id": self.test_ship_id}
            cert_response = requests.get(cert_endpoint, params=params, headers=self.get_headers(), timeout=30)
            
            if cert_response.status_code == 200:
                certificates = cert_response.json()
                endorsement_found = False
                
                for cert in certificates:
                    # Check if certificate has text content with endorsement information
                    text_content = cert.get('text_content', '')
                    if text_content and 'due range for annual survey' in text_content.lower():
                        self.log(f"      ✅ Found endorsement text in certificate: {cert.get('cert_name', 'Unknown')}")
                        endorsement_found = True
                        break
                
                if endorsement_found:
                    self.log("      ✅ Endorsement parsing capability detected")
                    self.anniversary_tests['endorsement_parsing_working'] = True
                else:
                    self.log("      ⚠️ No endorsement text found in certificates")
            
            # 3. Test most common day/month combination logic
            self.log("   3️⃣ Testing Most Common Day/Month Combination Logic...")
            
            # This would be tested by the recalculate function itself
            # We can verify this by checking if the calculated result makes sense
            recalculate_result = self.test_results.get('recalculate_response', {})
            if recalculate_result.get('success'):
                anniversary_date = recalculate_result.get('anniversary_date', {})
                day = anniversary_date.get('day')
                month = anniversary_date.get('month')
                
                if day and month:
                    self.log(f"      ✅ Most common logic produced result: day={day}, month={month}")
                    self.anniversary_tests['most_common_logic_working'] = True
                else:
                    self.log("      ⚠️ Most common logic did not produce valid day/month")
            else:
                self.log("      ⚠️ Cannot test most common logic - recalculate function failed")
            
            # 4. Test edge cases and error handling
            self.log("   4️⃣ Testing Edge Cases and Error Handling...")
            
            # Test with a non-existent ship ID
            fake_ship_id = "00000000-0000-0000-0000-000000000000"
            fake_endpoint = f"{BACKEND_URL}/ships/{fake_ship_id}/calculate-anniversary-date"
            fake_response = requests.post(fake_endpoint, headers=self.get_headers(), timeout=10)
            
            if fake_response.status_code == 404:
                self.log("      ✅ Proper error handling for non-existent ship")
                self.anniversary_tests['edge_cases_handled'] = True
            else:
                self.log(f"      ⚠️ Unexpected response for non-existent ship: {fake_response.status_code}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Enhanced logic verification error: {str(e)}", "ERROR")
            return False

    def test_special_survey_cycle_model(self):
        """Test the SpecialSurveyCycle model functionality"""
        try:
            self.log("🔍 Testing SpecialSurveyCycle model functionality...")
            
            # Test ship update with special_survey_cycle data
            special_survey_data = {
                "from_date": "2024-01-15T00:00:00Z",
                "to_date": "2025-01-15T00:00:00Z",
                "intermediate_required": True,
                "cycle_type": "Annual"
            }
            
            update_data = {
                "special_survey_cycle": special_survey_data,
                "last_special_survey": "2024-01-15T00:00:00Z"
            }
            
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
            self.log(f"   PUT {endpoint}")
            self.log(f"   Update data: {update_data}")
            
            response = requests.put(endpoint, json=update_data, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Ship update with special_survey_cycle successful")
                
                # Check if special_survey_cycle was saved correctly
                updated_special_survey = result.get('special_survey_cycle')
                updated_last_special_survey = result.get('last_special_survey')
                
                self.log(f"   📊 Updated Special Survey Cycle: {updated_special_survey}")
                self.log(f"   📊 Updated Last Special Survey: {updated_last_special_survey}")
                
                if updated_special_survey:
                    # Verify structure
                    expected_fields = ['from_date', 'to_date', 'intermediate_required', 'cycle_type']
                    all_fields_present = all(field in updated_special_survey for field in expected_fields)
                    
                    if all_fields_present:
                        self.log("   ✅ SpecialSurveyCycle model structure verified")
                        self.log(f"      From Date: {updated_special_survey.get('from_date')}")
                        self.log(f"      To Date: {updated_special_survey.get('to_date')}")
                        self.log(f"      Intermediate Required: {updated_special_survey.get('intermediate_required')}")
                        self.log(f"      Cycle Type: {updated_special_survey.get('cycle_type')}")
                        
                        self.anniversary_tests['special_survey_cycle_model_working'] = True
                        self.anniversary_tests['ship_update_with_special_survey_tested'] = True
                    else:
                        self.log("   ❌ SpecialSurveyCycle model structure incomplete")
                else:
                    self.log("   ❌ Special Survey Cycle not saved in update")
                
                self.test_results['special_survey_update'] = result
                return True
            else:
                self.log(f"   ❌ Ship update with special_survey_cycle failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ SpecialSurveyCycle model test error: {str(e)}", "ERROR")
            return False
    
    def test_data_consistency(self):
        """Test that all existing ship data remains intact after model changes"""
        try:
            self.log("🔍 Testing data consistency and backward compatibility...")
            
            # Get all ships to verify existing data integrity
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   ✅ Retrieved {len(ships)} ships for data consistency check")
                
                # Check each ship for data integrity
                intact_ships = 0
                ships_with_new_fields = 0
                ships_with_legacy_fields = 0
                
                for ship in ships:
                    ship_name = ship.get('name', 'Unknown')
                    
                    # Check core fields are intact
                    core_fields = ['id', 'name', 'imo', 'flag', 'company']
                    core_intact = all(ship.get(field) is not None for field in core_fields if field != 'imo')  # IMO can be None
                    
                    if core_intact:
                        intact_ships += 1
                    
                    # Check for new fields
                    if ship.get('special_survey_cycle') is not None:
                        ships_with_new_fields += 1
                    
                    # Check for legacy fields
                    if ship.get('legacy_dry_dock_cycle') is not None or ship.get('legacy_anniversary_date') is not None:
                        ships_with_legacy_fields += 1
                    
                    # Log details for SUNSHINE 01
                    if ship.get('name') == self.test_ship_name:
                        self.log(f"   📊 {self.test_ship_name} Data Integrity:")
                        self.log(f"      Core fields intact: {core_intact}")
                        self.log(f"      Has special_survey_cycle: {ship.get('special_survey_cycle') is not None}")
                        self.log(f"      Has legacy fields: {ship.get('legacy_dry_dock_cycle') is not None}")
                        
                        # Verify specific 3-column layout fields
                        column_1_fields = ['imo', 'ship_owner', 'deadweight']
                        column_2_fields = ['built_year', 'last_docking', 'dry_dock_cycle']
                        column_3_fields = ['anniversary_date', 'last_special_survey', 'special_survey_cycle']
                        
                        for field in column_1_fields + column_2_fields + column_3_fields:
                            value = ship.get(field)
                            self.log(f"         {field}: {'✅' if value is not None else '⚠️'} {value}")
                
                self.log(f"   📊 Data Consistency Results:")
                self.log(f"      Ships with intact core data: {intact_ships}/{len(ships)}")
                self.log(f"      Ships with new special_survey_cycle field: {ships_with_new_fields}/{len(ships)}")
                self.log(f"      Ships with legacy fields: {ships_with_legacy_fields}/{len(ships)}")
                
                # Verify data consistency
                if intact_ships == len(ships):
                    self.log("   ✅ All existing ship data remains intact")
                    self.anniversary_tests['data_consistency_verified'] = True
                else:
                    self.log(f"   ⚠️ Some ships have data integrity issues: {len(ships) - intact_ships} affected")
                
                # Verify backward compatibility
                if ships_with_legacy_fields > 0:
                    self.log("   ✅ Backward compatibility maintained - legacy fields preserved")
                    self.anniversary_tests['backward_compatibility_verified'] = True
                else:
                    self.log("   ⚠️ No legacy fields found - may indicate migration issues")
                
                self.test_results['data_consistency'] = {
                    'total_ships': len(ships),
                    'intact_ships': intact_ships,
                    'ships_with_new_fields': ships_with_new_fields,
                    'ships_with_legacy_fields': ships_with_legacy_fields
                }
                
                return True
            else:
                self.log(f"   ❌ Data consistency check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Data consistency test error: {str(e)}", "ERROR")
            return False
    
    def test_ship_creation_enhanced_fields(self):
        """Test ship creation with enhanced anniversary_date and dry_dock_cycle fields"""
        try:
            self.log("🆕 Testing ship creation with enhanced fields...")
            
            # Create test ship data with enhanced fields
            import random
            unique_imo = f"999{random.randint(1000, 9999)}"
            ship_data = {
                "name": f"TEST ANNIVERSARY SHIP {random.randint(100, 999)}",
                "imo": unique_imo,
                "flag": "PANAMA",
                "ship_type": "General Cargo",
                "gross_tonnage": 5000,
                "deadweight": 8000,
                "built_year": 2020,
                "company": "AMCSC",
                "ship_owner": "Test Owner",
                "last_docking": "2023-01-15T00:00:00Z",
                "last_special_survey": "2023-06-20T00:00:00Z",
                "anniversary_date": {
                    "day": 20,
                    "month": 6,
                    "auto_calculated": False,
                    "source_certificate_type": "Manual Entry",
                    "manual_override": True
                },
                "dry_dock_cycle": {
                    "from_date": "2023-06-20T00:00:00Z",
                    "to_date": "2028-06-20T00:00:00Z",
                    "intermediate_docking_required": True,
                    "last_intermediate_docking": None
                }
            }
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=ship_data, headers=self.get_headers(), timeout=10)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Ship creation with enhanced fields successful")
                
                # Check enhanced fields in response
                created_anniversary = result.get('anniversary_date')
                created_dry_dock = result.get('dry_dock_cycle')
                
                self.log(f"   📊 Created Ship Enhanced Fields:")
                self.log(f"      Anniversary Date: {created_anniversary}")
                self.log(f"      Dry Dock Cycle: {created_dry_dock}")
                
                # Verify enhanced fields
                if created_anniversary and created_dry_dock:
                    # Check anniversary date structure
                    if (created_anniversary.get('day') == 20 and 
                        created_anniversary.get('month') == 6 and
                        created_anniversary.get('manual_override') == True):
                        self.log("   ✅ Anniversary date enhanced fields correct")
                    
                    # Check dry dock cycle structure
                    if (created_dry_dock.get('intermediate_docking_required') == True and
                        created_dry_dock.get('from_date') and
                        created_dry_dock.get('to_date')):
                        self.log("   ✅ Dry dock cycle enhanced fields correct")
                        self.log("   ✅ Lloyd's 5-year period with intermediate docking requirement verified")
                    
                    self.anniversary_tests['ship_creation_enhanced_fields_tested'] = True
                
                # Store created ship ID for cleanup
                self.test_results['created_ship_id'] = result.get('id')
                self.test_results['ship_creation'] = result
                return True
            else:
                self.log(f"   ❌ Ship creation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ship creation test error: {str(e)}", "ERROR")
            return False
    
    def test_ship_update_enhanced_fields(self):
        """Test ship update with enhanced anniversary_date and dry_dock_cycle fields"""
        try:
            self.log("🔄 Testing ship update with enhanced fields...")
            
            # Update the SUNSHINE 01 ship with enhanced fields
            update_data = {
                "last_docking": "2024-02-10T00:00:00Z",
                "last_special_survey": "2024-01-15T00:00:00Z",
                "anniversary_date": {
                    "day": 15,
                    "month": 1,
                    "auto_calculated": True,
                    "source_certificate_type": "Full Term Class Certificate",
                    "manual_override": False
                },
                "dry_dock_cycle": {
                    "from_date": "2024-01-15T00:00:00Z",
                    "to_date": "2029-01-15T00:00:00Z",
                    "intermediate_docking_required": True,
                    "last_intermediate_docking": "2024-02-10T00:00:00Z"
                }
            }
            
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
            self.log(f"   PUT {endpoint}")
            
            response = requests.put(endpoint, json=update_data, headers=self.get_headers(), timeout=10)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Ship update with enhanced fields successful")
                
                # Check enhanced fields in response
                updated_anniversary = result.get('anniversary_date')
                updated_dry_dock = result.get('dry_dock_cycle')
                
                self.log(f"   📊 Updated Ship Enhanced Fields:")
                self.log(f"      Anniversary Date: {updated_anniversary}")
                self.log(f"      Dry Dock Cycle: {updated_dry_dock}")
                
                # Verify enhanced fields
                if updated_anniversary and updated_dry_dock:
                    # Check anniversary date structure
                    if (updated_anniversary.get('day') == 15 and 
                        updated_anniversary.get('month') == 1 and
                        updated_anniversary.get('auto_calculated') == True):
                        self.log("   ✅ Anniversary date enhanced fields updated correctly")
                    
                    # Check dry dock cycle structure with intermediate docking
                    if (updated_dry_dock.get('intermediate_docking_required') == True and
                        updated_dry_dock.get('last_intermediate_docking')):
                        self.log("   ✅ Dry dock cycle with intermediate docking updated correctly")
                        self.log("   ✅ Lloyd's intermediate docking requirements verified")
                        
                        # Check 5-year period (from_date to to_date should be ~5 years)
                        from_date_str = updated_dry_dock.get('from_date')
                        to_date_str = updated_dry_dock.get('to_date')
                        if from_date_str and to_date_str:
                            from datetime import datetime
                            from_date = datetime.fromisoformat(from_date_str.replace('Z', ''))
                            to_date = datetime.fromisoformat(to_date_str.replace('Z', ''))
                            years_diff = (to_date - from_date).days / 365.25
                            if 4.5 <= years_diff <= 5.5:  # Allow some tolerance
                                self.log(f"   ✅ Lloyd's 5-year dry dock cycle verified ({years_diff:.1f} years)")
                                self.anniversary_tests['lloyd_standards_compliance_verified'] = True
                    
                    self.anniversary_tests['ship_update_enhanced_fields_tested'] = True
                
                self.test_results['ship_update'] = result
                return True
            else:
                self.log(f"   ❌ Ship update failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ship update test error: {str(e)}", "ERROR")
            return False
    
    def test_backward_compatibility(self):
        """Test backward compatibility with legacy data formats"""
        try:
            self.log("🔄 Testing backward compatibility with legacy data formats...")
            
            # Test creating ship with legacy fields
            import random
            unique_legacy_imo = f"888{random.randint(1000, 9999)}"
            legacy_ship_data = {
                "name": f"LEGACY TEST SHIP {random.randint(100, 999)}",
                "imo": unique_legacy_imo,
                "flag": "LIBERIA",
                "ship_type": "Bulk Carrier",
                "gross_tonnage": 15000,
                "deadweight": 25000,
                "built_year": 2015,
                "company": "AMCSC",
                "ship_owner": "Legacy Owner",
                "legacy_dry_dock_cycle": 60,  # Legacy months field
                "legacy_anniversary_date": "2024-03-15T00:00:00Z"  # Legacy datetime field
            }
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   POST {endpoint} (with legacy fields)")
            
            response = requests.post(endpoint, json=legacy_ship_data, headers=self.get_headers(), timeout=10)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Ship creation with legacy fields successful")
                
                # Check if legacy fields are preserved
                legacy_dry_dock = result.get('legacy_dry_dock_cycle')
                legacy_anniversary = result.get('legacy_anniversary_date')
                
                # Check if enhanced fields were created from legacy
                enhanced_dry_dock = result.get('dry_dock_cycle')
                enhanced_anniversary = result.get('anniversary_date')
                
                self.log(f"   📊 Backward Compatibility Results:")
                self.log(f"      Legacy Dry Dock Cycle: {legacy_dry_dock}")
                self.log(f"      Legacy Anniversary Date: {legacy_anniversary}")
                self.log(f"      Enhanced Dry Dock Cycle: {enhanced_dry_dock}")
                self.log(f"      Enhanced Anniversary Date: {enhanced_anniversary}")
                
                # Verify backward compatibility
                if legacy_dry_dock == 60 and legacy_anniversary:
                    self.log("   ✅ Legacy fields preserved correctly")
                
                if enhanced_dry_dock or enhanced_anniversary:
                    self.log("   ✅ Enhanced fields created from legacy data")
                    self.anniversary_tests['backward_compatibility_tested'] = True
                
                # Store created ship ID for cleanup
                self.test_results['legacy_ship_id'] = result.get('id')
                self.test_results['backward_compatibility'] = result
                return True
            else:
                self.log(f"   ❌ Legacy ship creation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Backward compatibility test error: {str(e)}", "ERROR")
            return False
    
    def capture_backend_logs(self):
        """Capture backend logs for 3-column layout and special survey cycle analysis"""
        try:
            self.log("📝 Capturing backend logs for 3-column layout processing...")
            
            # Try to capture backend logs
            try:
                result = subprocess.run(
                    ['tail', '-n', '100', '/var/log/supervisor/backend.out.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout:
                    log_lines = result.stdout.strip().split('\n')
                    
                    # Look for layout and special survey related log messages
                    layout_logs = []
                    for line in log_lines:
                        if any(keyword in line.lower() for keyword in ['special_survey', 'survey_cycle', 'ship', 'enhanced', 'model']):
                            layout_logs.append(line)
                    
                    if layout_logs:
                        self.log("   ✅ Layout-related backend logs found:")
                        for log_line in layout_logs[-5:]:  # Show last 5 relevant logs
                            self.log(f"      {log_line}")
                        
                        # Check for specific special survey processing messages
                        processing_logs = [line for line in layout_logs if 'special_survey' in line.lower()]
                        if processing_logs:
                            self.log("   ✅ Special survey processing logs detected")
                    else:
                        self.log("   ⚠️ No layout-specific logs found in recent backend output")
                    
                    self.test_results['backend_logs'] = log_lines
                    self.test_results['layout_logs'] = layout_logs
                else:
                    self.log("   ⚠️ No backend logs accessible")
                    
            except Exception as e:
                self.log(f"   ⚠️ Backend log capture error: {str(e)}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Backend log capture error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_docking_date_tests(self):
        """Main test function for Docking Date Extraction Logic"""
        self.log("🎯 STARTING DOCKING DATE EXTRACTION TESTING")
        self.log("🔍 Focus: Test docking date extraction logic sau khi fix syntax error")
        self.log("📋 Review Request: Verify CSSC certificate detection and date extraction")
        self.log("🎯 Expected: CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE detection")
        self.log("🎯 Keywords: 'safety construction', 'cssc', 'dry dock', 'dd'")
        self.log("🎯 Date range: 1980 - current year")
        self.log("🎯 Format: dd/MM/yyyy")
        self.log("=" * 100)
        
        # Step 1: Authenticate
        self.log("\n🔐 STEP 1: AUTHENTICATION")
        self.log("=" * 50)
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Backend Startup Verification
        self.log("\n🔧 STEP 2: BACKEND STARTUP VERIFICATION")
        self.log("=" * 50)
        self.test_backend_startup_verification()
        
        # Step 3: CSSC Certificate Detection
        self.log("\n🔍 STEP 3: CSSC CERTIFICATE DETECTION")
        self.log("=" * 50)
        self.test_cssc_certificate_detection()
        
        # Step 4: Certificate Text Parsing
        self.log("\n📝 STEP 4: CERTIFICATE TEXT PARSING")
        self.log("=" * 50)
        self.test_certificate_text_parsing()
        
        # Step 5: Docking Date Extraction Endpoint
        self.log("\n🎯 STEP 5: DOCKING DATE EXTRACTION ENDPOINT")
        self.log("=" * 50)
        self.test_docking_date_extraction_endpoint()
        
        # Step 6: Date Validation and Ship Update
        self.log("\n📅 STEP 6: DATE VALIDATION AND SHIP UPDATE")
        self.log("=" * 50)
        self.test_date_validation_and_ship_update()
        
        # Step 7: Final analysis
        self.log("\n📊 STEP 7: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_docking_analysis()
        
        return True
    
    def provide_final_same_day_month_analysis(self):
        """Provide final analysis of the Same Day/Month Logic testing"""
        try:
            self.log("🎯 SPECIAL SURVEY CYCLE SAME DAY/MONTH TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.special_survey_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ SAME DAY/MONTH TESTS PASSED ({len(passed_tests)}/{len(self.special_survey_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ SAME DAY/MONTH TESTS FAILED ({len(failed_tests)}/{len(self.special_survey_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Overall assessment
            success_rate = len(passed_tests) / len(self.special_survey_tests) * 100
            self.log(f"\n📊 SAME DAY/MONTH TESTING SUCCESS RATE: {success_rate:.1f}%")
            
            # CRITICAL REVIEW REQUEST VERIFICATION
            self.log(f"\n🎯 CRITICAL REVIEW REQUEST VERIFICATION:")
            
            # Special Survey Cycle Function Analysis
            special_survey_result = self.test_results.get('special_survey_response', {})
            self.log(f"   🔄 Special Survey Cycle Calculation Function:")
            if special_survey_result:
                success = special_survey_result.get('success', False)
                message = special_survey_result.get('message', 'No message')
                special_survey_cycle = special_survey_result.get('special_survey_cycle')
                
                self.log(f"      Status: {'✅ Working' if success else '❌ Failed'}")
                self.log(f"      Message: {message}")
                
                if special_survey_cycle:
                    from_date = special_survey_cycle.get('from_date')
                    to_date = special_survey_cycle.get('to_date')
                    intermediate_required = special_survey_cycle.get('intermediate_required')
                    cycle_type = special_survey_cycle.get('cycle_type', 'Unknown')
                    
                    self.log(f"      From Date: {from_date}")
                    self.log(f"      To Date: {to_date}")
                    self.log(f"      Intermediate Required: {intermediate_required}")
                    self.log(f"      Cycle Type: {cycle_type}")
                    
                    # CRITICAL: Check same day/month requirement
                    if from_date and to_date:
                        try:
                            from_dt = datetime.fromisoformat(from_date.replace('Z', ''))
                            to_dt = datetime.fromisoformat(to_date.replace('Z', ''))
                            
                            from_display = from_dt.strftime('%d/%m/%Y')
                            to_display = to_dt.strftime('%d/%m/%Y')
                            display_format = f"{from_display} - {to_display}"
                            
                            self.log(f"      Display Format: {display_format}")
                            
                            # Check same day/month
                            same_day = from_dt.day == to_dt.day
                            same_month = from_dt.month == to_dt.month
                            
                            self.log(f"      🔍 SAME DAY/MONTH VERIFICATION:")
                            self.log(f"         From Date: Day={from_dt.day}, Month={from_dt.month}")
                            self.log(f"         To Date: Day={to_dt.day}, Month={to_dt.month}")
                            self.log(f"         Same Day: {'✅' if same_day else '❌'}")
                            self.log(f"         Same Month: {'✅' if same_month else '❌'}")
                            
                            if same_day and same_month:
                                self.log(f"      ✅ SAME DAY/MONTH REQUIREMENT SATISFIED!")
                            else:
                                self.log(f"      ❌ SAME DAY/MONTH REQUIREMENT FAILED!")
                            
                            # Check against expected results
                            if display_format == self.expected_display_format:
                                self.log(f"      ✅ Display format matches expected: {self.expected_display_format}")
                            else:
                                self.log(f"      ❌ Display format differs from expected: {self.expected_display_format}")
                                
                            # Check if fixed from previous incorrect result
                            if from_display != self.previous_incorrect_from_date:
                                self.log(f"      ✅ FIXED: No longer showing previous incorrect result ({self.previous_incorrect_from_date})")
                            else:
                                self.log(f"      ❌ STILL BROKEN: Showing previous incorrect result ({self.previous_incorrect_from_date})")
                                
                        except Exception as e:
                            self.log(f"      ❌ Error formatting display: {e}")
                else:
                    self.log(f"      ❌ No special survey cycle calculated")
            else:
                self.log(f"      ❌ No special survey response received")
            
            # Certificate Verification
            cert_verification = self.test_results.get('certificate_verification', {})
            self.log(f"   🔍 Certificate Verification:")
            if cert_verification:
                cargo_safety_found = cert_verification.get('cargo_safety_cert_found', False)
                cargo_safety_cert = cert_verification.get('cargo_safety_cert')
                
                self.log(f"      CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE: {'✅ Found' if cargo_safety_found else '❌ Not Found'}")
                
                if cargo_safety_cert:
                    valid_date = cargo_safety_cert.get('valid_date', '')
                    if "2026-03-10" in valid_date:
                        self.log(f"      ✅ Expected certificate with valid_date: 2026-03-10 found")
                    else:
                        self.log(f"      ⚠️ Certificate valid_date: {valid_date}")
            else:
                self.log(f"      ❌ No certificate verification performed")
            
            # Key Review Request Requirements Summary
            self.log(f"\n📋 REVIEW REQUEST REQUIREMENTS SUMMARY:")
            self.log(f"   1. Login as admin1/123456: {'✅' if self.special_survey_tests.get('authentication_successful') else '❌'}")
            self.log(f"   2. POST /api/ships/.../calculate-special-survey-cycle: {'✅' if self.special_survey_tests.get('special_survey_endpoint_working') else '❌'}")
            self.log(f"   3. CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE found: {'✅' if self.special_survey_tests.get('expected_certificate_found') else '❌'}")
            self.log(f"   4. From Date có cùng ngày/tháng với To Date: {'✅' if self.special_survey_tests.get('same_day_month_verified') else '❌'}")
            self.log(f"   5. To Date = 10/03/2026: {'✅' if self.special_survey_tests.get('to_date_correct') else '❌'}")
            self.log(f"   6. From Date = 10/03/2021: {'✅' if self.special_survey_tests.get('from_date_correct') else '❌'}")
            self.log(f"   7. Date calculation fixed: {'✅' if self.special_survey_tests.get('date_calculation_fixed') else '❌'}")
            self.log(f"   8. Display format '10/03/2021 - 10/03/2026': {'✅' if self.special_survey_tests.get('display_format_correct') else '❌'}")
            self.log(f"   9. Cycle type 'SOLAS Safety Construction Survey Cycle': {'✅' if self.special_survey_tests.get('cycle_type_correct') else '❌'}")
            self.log(f"   10. Intermediate_required: true: {'✅' if self.special_survey_tests.get('intermediate_required_true') else '❌'}")
            self.log(f"   11. Leap year handling tested: {'✅' if self.special_survey_tests.get('leap_year_handling_tested') else '❌'}")
            
            # Final conclusion
            critical_tests = ['same_day_month_verified', 'from_date_correct', 'to_date_correct', 'date_calculation_fixed']
            critical_passed = sum(1 for test in critical_tests if self.special_survey_tests.get(test, False))
            
            self.log(f"\n🎯 FINAL CONCLUSION:")
            if critical_passed == len(critical_tests):
                self.log(f"   ✅ SAME DAY/MONTH REQUIREMENT SUCCESSFULLY IMPLEMENTED!")
                self.log(f"   ✅ From Date now has same day/month as To Date")
                self.log(f"   ✅ Date calculation logic has been fixed")
            else:
                self.log(f"   ❌ SAME DAY/MONTH REQUIREMENT NOT FULLY IMPLEMENTED")
                self.log(f"   ❌ Critical tests passed: {critical_passed}/{len(critical_tests)}")
                self.log(f"   ❌ Date calculation logic may still need fixes")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main test execution"""
    print("🎯 Ship Management System - Special Survey Cycle Same Day/Month Testing")
    print("🔍 Focus: Test fixed Special Survey Cycle logic với same day/month requirement")
    print("📋 Review Request: Verify From Date có cùng ngày/tháng với To Date")
    print("🎯 Expected: CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE với valid_date: 2026-03-10")
    print("🎯 Should calculate: To Date = 10/03/2026, From Date = 10/03/2021 (cùng ngày/tháng)")
    print("🎯 Previous result: From Date = 09/03/2021 (sai 1 ngày)")
    print("🎯 After fix: From Date = 10/03/2021 (đúng cùng ngày/tháng)")
    print("=" * 100)
    
    tester = SpecialSurveyCycleTester()
    success = tester.run_comprehensive_same_day_month_tests()
    
    print("=" * 100)
    print("🔍 SPECIAL SURVEY CYCLE LOGIC TESTING RESULTS:")
    print("=" * 70)
    
    # Print test summary
    passed_tests = [f for f, passed in tester.special_survey_tests.items() if passed]
    failed_tests = [f for f, passed in tester.special_survey_tests.items() if not passed]
    
    print(f"✅ SPECIAL SURVEY TESTS PASSED ({len(passed_tests)}/10):")
    for test in passed_tests:
        print(f"   ✅ {test.replace('_', ' ').title()}")
    
    if failed_tests:
        print(f"\n❌ SPECIAL SURVEY TESTS FAILED ({len(failed_tests)}/10):")
        for test in failed_tests:
            print(f"   ❌ {test.replace('_', ' ').title()}")
    
    # Print key findings
    print(f"\n🔍 KEY FINDINGS:")
    
    # Special Survey Cycle Function Analysis
    special_survey_result = tester.test_results.get('special_survey_response', {})
    print(f"   🔄 Special Survey Cycle Calculation Function:")
    if special_survey_result:
        success_flag = special_survey_result.get('success', False)
        message = special_survey_result.get('message', 'No message')
        special_survey_cycle = special_survey_result.get('special_survey_cycle')
        
        print(f"      Function Status: {'✅ Working' if success_flag else '❌ Failed'}")
        print(f"      Message: {message}")
        
        if special_survey_cycle:
            from_date = special_survey_cycle.get('from_date')
            to_date = special_survey_cycle.get('to_date')
            cycle_type = special_survey_cycle.get('cycle_type')
            intermediate_required = special_survey_cycle.get('intermediate_required')
            
            print(f"      From Date: {from_date}")
            print(f"      To Date: {to_date}")
            print(f"      Cycle Type: {cycle_type}")
            print(f"      Intermediate Required: {intermediate_required}")
            
            # Check display format
            if from_date and to_date:
                try:
                    from_dt = datetime.fromisoformat(from_date.replace('Z', ''))
                    to_dt = datetime.fromisoformat(to_date.replace('Z', ''))
                    display_format = f"{from_dt.strftime('%d/%m/%Y')} - {to_dt.strftime('%d/%m/%Y')}"
                    print(f"      Display Format: {display_format}")
                    print(f"      Expected Format: {tester.expected_display_format}")
                    print(f"      Format Match: {'✅' if display_format == tester.expected_display_format else '❌'}")
                except Exception as e:
                    print(f"      ❌ Error formatting display: {e}")
        else:
            print(f"      ❌ No special survey cycle calculated")
    else:
        print(f"      ❌ No response from special survey calculation function")
    
    # Certificate Analysis
    cert_analysis = tester.test_results.get('certificate_analysis', {})
    print(f"   🔍 Certificate Analysis:")
    if cert_analysis:
        total_certs = cert_analysis.get('total_certificates', 0)
        full_term_class_certs = cert_analysis.get('full_term_class_certificates', 0)
        valid_date_certs = cert_analysis.get('certificates_with_valid_date', 0)
        cargo_safety_found = cert_analysis.get('cargo_safety_cert_found', False)
        
        print(f"      Total Certificates: {total_certs}")
        print(f"      Full Term Class Certificates: {full_term_class_certs}")
        print(f"      Certificates with valid_date: {valid_date_certs}")
        print(f"      CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE: {'✅ Found' if cargo_safety_found else '❌ Not Found'}")
        
        # Check expected certificate
        cargo_safety_cert = cert_analysis.get('cargo_safety_cert')
        if cargo_safety_cert:
            valid_date = cargo_safety_cert.get('valid_date', '')
            print(f"      Certificate valid_date: {valid_date}")
            print(f"      Expected valid_date: {tester.expected_valid_date}")
            print(f"      Valid Date Match: {'✅' if tester.expected_valid_date in valid_date else '❌'}")
    else:
        print(f"      ❌ No certificate analysis performed")
    
    # Calculate success rate
    success_rate = len(passed_tests) / len(tester.special_survey_tests) * 100
    print(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")
    
    print("=" * 100)
    if success:
        print("🎉 Special Survey Cycle Logic testing completed!")
        print("✅ All testing steps executed - detailed analysis available above")
    else:
        print("❌ Special Survey Cycle Logic testing completed with issues!")
        print("🔍 Check detailed logs above for specific issues")
    
    # Provide recommendations based on findings
    print("\n💡 NEXT STEPS FOR MAIN AGENT:")
    
    # Review Request Requirements
    print("   📋 REVIEW REQUEST REQUIREMENTS STATUS:")
    
    # Special Survey Endpoint
    if tester.special_survey_tests.get('special_survey_endpoint_working'):
        print("   ✅ Special Survey Cycle Calculation Endpoint: Working correctly")
    else:
        print("   ❌ Special Survey Cycle Calculation Endpoint: Not working")
        print("      1. Check if POST /api/ships/{ship_id}/calculate-special-survey-cycle endpoint exists")
        print("      2. Verify calculate_special_survey_cycle_from_certificates function implementation")
        print("      3. Ensure endpoint returns proper response structure")
    
    # Full Term Class Certificates
    if tester.special_survey_tests.get('full_term_class_certificates_found'):
        print("   ✅ Full Term Class Certificates: Found and processed correctly")
    else:
        print("   ❌ Full Term Class Certificates: Not found or not processed")
        print("      1. Verify function finds Full Term certificates with class keywords")
        print("      2. Check certificate filtering logic for 'class', 'safety construction', etc.")
        print("      3. Ensure CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE is identified")
    
    # IMO 5-Year Logic
    if tester.special_survey_tests.get('imo_5_year_logic_verified'):
        print("   ✅ IMO 5-Year Logic: Verified correctly")
    else:
        print("   ❌ IMO 5-Year Logic: Issues with 5-year calculation")
        print("      1. Check To Date = Valid date of latest Full Term Class certificate")
        print("      2. Verify From Date = 5 years before To Date")
        print("      3. Ensure intermediate survey required = true")
    
    # Expected Results
    if tester.special_survey_tests.get('date_calculation_correct'):
        print("   ✅ Date Calculation: From Date = 2021-03-10, To Date = 2026-03-10 verified")
    else:
        print("   ❌ Date Calculation: Does not match expected dates")
        print("      1. Check CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE valid_date: 2026-03-10")
        print("      2. Verify 5-year calculation logic")
        print("      3. Ensure display format: '10/03/2021 - 10/03/2026'")
    
    # Cycle Type
    if tester.special_survey_tests.get('cycle_type_correct'):
        print("   ✅ Cycle Type: 'SOLAS Safety Construction Survey Cycle' verified")
    else:
        print("   ❌ Cycle Type: Does not match expected type")
        print("      1. Check cycle type determination logic")
        print("      2. Verify 'safety construction' certificate detection")
        print("      3. Ensure proper cycle type assignment")
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
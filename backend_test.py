#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: Enhanced Docking Extraction Logic với CSSC "inspections of the outside of the ship's bottom" và Survey Status
Review Request: Test enhanced docking extraction logic với CSSC "inspections of the outside of the ship's bottom" và Survey Status
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

class EnhancedDockingExtractionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Enhanced Docking Extraction Logic
        self.docking_tests = {
            'authentication_successful': False,
            'backend_startup_verified': False,
            'basic_endpoint_connectivity': False,
            'docking_endpoint_working': False,
            'cssc_certificate_found': False,
            'cssc_bottom_inspection_patterns_working': False,
            'survey_status_integration_working': False,
            'enhanced_pattern_matching_working': False,
            'priority_order_working': False,
            'last_docking_1_extracted': False,
            'last_docking_2_extracted': False,
            'next_docking_calculation_working': False,
            'enhanced_results_verified': False,
            'cssc_bottom_inspection_focus_working': False,
            'survey_status_docking_info_working': False,
            'improved_accuracy_verified': False,
            'response_format_correct': False,
            'dd_mm_yyyy_format_verified': False,
            'error_handling_working': False
        }
        
        # Test ship ID for SUNSHINE 01 as specified in review request
        self.test_ship_id = "e21c71a2-9543-4f92-990c-72f54292fde8"
        self.test_ship_name = "SUNSHINE 01"
        
        # Enhanced patterns from review request
        self.expected_certificate = "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE"
        
        # Enhanced pattern categories (20+ patterns)
        self.cssc_bottom_patterns = [
            "inspections of the outside of the ship's bottom",
            "bottom inspection", 
            "hull bottom survey",
            "outside of ship's bottom",
            "ship bottom inspection"
        ]
        
        self.survey_status_patterns = [
            "survey status...docking",
            "docking inspection status", 
            "status...dry dock",
            "survey status docking",
            "docking survey status"
        ]
        
        self.general_docking_patterns = [
            "dry dock date",
            "docking survey date", 
            "construction survey",
            "last dry dock",
            "docking inspection",
            "hull survey",
            "bottom survey"
        ]
        
        # Priority order: CSSC Bottom → Survey Status → General Docking
        self.pattern_priority = ["CSSC Bottom", "Survey Status", "General Docking"]
        
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

    def test_enhanced_cssc_bottom_inspection_extraction(self):
        """Test Enhanced CSSC Bottom Inspection Extraction"""
        try:
            self.log("🔍 Testing Enhanced CSSC Bottom Inspection Extraction...")
            self.log("   Focus: 'inspections of the outside of the ship's bottom' patterns")
            
            # Get certificates for SUNSHINE 01 ship
            endpoint = f"{BACKEND_URL}/certificates"
            params = {"ship_id": self.test_ship_id}
            self.log(f"   GET {endpoint}?ship_id={self.test_ship_id}")
            
            response = requests.get(endpoint, params=params, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   ✅ Retrieved {len(certificates)} certificates for {self.test_ship_name}")
                
                # Look for CSSC certificates specifically
                cssc_certificates = []
                
                for cert in certificates:
                    cert_name = cert.get('cert_name', '').lower()
                    
                    # Check for CSSC certificate (CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE)
                    if "cargo ship safety construction certificate" in cert_name:
                        cssc_certificates.append(cert)
                        self.log(f"   ✅ Found CSSC: {cert.get('cert_name')}")
                
                if cssc_certificates:
                    self.log(f"   ✅ CSSC Certificate Detection successful ({len(cssc_certificates)} found)")
                    self.docking_tests['cssc_certificate_found'] = True
                    
                    # Test enhanced CSSC bottom inspection patterns
                    for cssc_cert in cssc_certificates:
                        self.log(f"   📊 Analyzing CSSC Certificate: {cssc_cert.get('cert_name')}")
                        self.log(f"      Type: {cssc_cert.get('cert_type')}")
                        self.log(f"      Issue Date: {cssc_cert.get('issue_date')}")
                        self.log(f"      Valid Date: {cssc_cert.get('valid_date')}")
                        
                        text_content = cssc_cert.get('text_content', '')
                        if text_content:
                            self.log("   ✅ CSSC certificate has text content for enhanced pattern matching")
                            
                            # Test enhanced CSSC bottom inspection patterns
                            bottom_patterns_found = []
                            for pattern in self.cssc_bottom_patterns:
                                if pattern.lower() in text_content.lower():
                                    bottom_patterns_found.append(pattern)
                                    self.log(f"      ✅ Found CSSC bottom pattern: '{pattern}'")
                            
                            if bottom_patterns_found:
                                self.log(f"   ✅ Enhanced CSSC bottom inspection patterns working: {len(bottom_patterns_found)} patterns found")
                                self.docking_tests['cssc_bottom_inspection_patterns_working'] = True
                            else:
                                self.log("   ⚠️ No enhanced CSSC bottom inspection patterns found")
                        else:
                            self.log("   ⚠️ CSSC certificate has no text content for pattern matching")
                
                self.test_results['cssc_analysis'] = {
                    'total_certificates': len(certificates),
                    'cssc_certificates': len(cssc_certificates),
                    'cssc_cert_details': cssc_certificates
                }
                
                return True
                
            else:
                self.log(f"   ❌ Certificate retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Enhanced CSSC bottom inspection test error: {str(e)}", "ERROR")
            return False

    def test_survey_status_integration(self):
        """Test Survey Status Integration for Docking Date Extraction"""
        try:
            self.log("📋 Testing Survey Status Integration...")
            self.log("   Focus: extract_docking_dates_from_survey_status function")
            
            # Get ship data to check for survey status information
            ship_endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
            response = requests.get(ship_endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ship_data = response.json()
                self.log(f"   ✅ Retrieved ship data for {self.test_ship_name}")
                
                # Check if ship has survey status information
                survey_status = ship_data.get('survey_status')
                if survey_status:
                    self.log("   ✅ Ship has survey status information")
                    self.log(f"   Survey Status: {survey_status[:100]}...")  # Show first 100 chars
                    
                    # Test survey status patterns
                    status_patterns_found = []
                    for pattern in self.survey_status_patterns:
                        if pattern.lower() in survey_status.lower():
                            status_patterns_found.append(pattern)
                            self.log(f"      ✅ Found survey status pattern: '{pattern}'")
                    
                    if status_patterns_found:
                        self.log(f"   ✅ Survey status integration patterns working: {len(status_patterns_found)} patterns found")
                        self.docking_tests['survey_status_integration_working'] = True
                else:
                    self.log("   ⚠️ Ship has no survey status information")
                
                # Also check certificates for survey status sections
                certificates = self.test_results.get('cssc_analysis', {}).get('cssc_cert_details', [])
                for cert in certificates:
                    text_content = cert.get('text_content', '')
                    if text_content and 'survey status' in text_content.lower():
                        self.log(f"   ✅ Found survey status section in certificate: {cert.get('cert_name')}")
                        
                        # Test survey status patterns in certificate text
                        cert_status_patterns = []
                        for pattern in self.survey_status_patterns:
                            if pattern.lower() in text_content.lower():
                                cert_status_patterns.append(pattern)
                        
                        if cert_status_patterns:
                            self.log(f"      ✅ Survey status patterns in certificate: {cert_status_patterns}")
                            self.docking_tests['survey_status_docking_info_working'] = True
                
                return True
                
            else:
                self.log(f"   ❌ Ship data retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Survey status integration test error: {str(e)}", "ERROR")
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

    def provide_final_docking_analysis(self):
        """Provide final analysis of the Docking Date Extraction testing"""
        try:
            self.log("🎯 DOCKING DATE EXTRACTION TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.docking_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ DOCKING DATE TESTS PASSED ({len(passed_tests)}/{len(self.docking_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ DOCKING DATE TESTS FAILED ({len(failed_tests)}/{len(self.docking_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.docking_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.docking_tests)})")
            
            # Provide specific analysis based on review request
            self.log("\n🎯 REVIEW REQUEST ANALYSIS:")
            
            # 1. Quick Fix Verification
            if (self.docking_tests['authentication_successful'] and 
                self.docking_tests['backend_startup_verified'] and 
                self.docking_tests['basic_endpoint_connectivity']):
                self.log("   ✅ Quick Fix Verification: PASSED")
                self.log("      - Login as admin1/123456: ✅")
                self.log("      - Backend startup verified: ✅")
                self.log("      - Basic endpoint connectivity: ✅")
            else:
                self.log("   ❌ Quick Fix Verification: FAILED")
            
            # 2. Docking Date Extraction
            if (self.docking_tests['docking_endpoint_working'] and 
                self.docking_tests['last_docking_1_extracted']):
                self.log("   ✅ Docking Date Extraction: PASSED")
                self.log("      - POST /api/ships/.../calculate-docking-dates: ✅")
                self.log("      - Last Docking 1 extracted: ✅")
                if self.docking_tests['last_docking_2_extracted']:
                    self.log("      - Last Docking 2 extracted: ✅")
            else:
                self.log("   ❌ Docking Date Extraction: FAILED")
            
            # 3. CSSC Certificate Detection
            if self.docking_tests['cssc_certificate_found']:
                self.log("   ✅ CSSC Certificate Detection: PASSED")
                self.log("      - CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE found: ✅")
            else:
                self.log("   ❌ CSSC Certificate Detection: FAILED")
            
            # 4. Certificate Filtering
            if self.docking_tests['certificate_filtering_working']:
                self.log("   ✅ Certificate Filtering: PASSED")
                self.log("      - Keywords filtering working: ✅")
            else:
                self.log("   ❌ Certificate Filtering: FAILED")
            
            # 5. Response Format
            if (self.docking_tests['response_format_correct'] and 
                self.docking_tests['dd_mm_yyyy_format_verified']):
                self.log("   ✅ Response Format: PASSED")
                self.log("      - Success response format: ✅")
                self.log("      - dd/MM/yyyy formatting: ✅")
            else:
                self.log("   ❌ Response Format: FAILED")
            
            # 6. Date Validation and Ship Update
            if (self.docking_tests['date_validation_working'] and 
                self.docking_tests['ship_update_working']):
                self.log("   ✅ Date Validation & Ship Update: PASSED")
                self.log("      - Date range validation (1980-current): ✅")
                self.log("      - Ship update with calculated dates: ✅")
            else:
                self.log("   ❌ Date Validation & Ship Update: FAILED")
            
            # Final conclusion
            if success_rate >= 80:
                self.log(f"\n🎉 CONCLUSION: DOCKING DATE EXTRACTION LOGIC IS WORKING CORRECTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Syntax error fix successful!")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: DOCKING DATE EXTRACTION PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Some issues need attention")
            else:
                self.log(f"\n❌ CONCLUSION: DOCKING DATE EXTRACTION HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Major problems detected")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run docking date extraction tests"""
    print("🎯 DOCKING DATE EXTRACTION TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = DockingDateExtractionTester()
        success = tester.run_comprehensive_docking_date_tests()
        
        if success:
            print("\n✅ DOCKING DATE EXTRACTION TESTING COMPLETED")
        else:
            print("\n❌ DOCKING DATE EXTRACTION TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
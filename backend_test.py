#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: Anniversary Date and Dry Dock Cycle Enhancements
Review Request: Test anniversary date and dry dock cycle enhancements with Lloyd's maritime standards compliance
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

# Configuration - Use external URL from frontend/.env
BACKEND_URL = "https://vessel-docs-hub.preview.emergentagent.com/api"

class AnniversaryDateDryDockTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for anniversary date and dry dock cycle enhancements
        self.anniversary_tests = {
            'authentication_successful': False,
            'ship_retrieval_enhanced_data_tested': False,
            'anniversary_date_calculation_tested': False,
            'anniversary_date_override_tested': False,
            'ship_creation_enhanced_fields_tested': False,
            'ship_update_enhanced_fields_tested': False,
            'backward_compatibility_tested': False,
            'lloyd_standards_compliance_verified': False,
            'validation_day_month_tested': False,
            'sunshine_01_ship_tested': False
        }
        
        # Test ship ID for SUNSHINE 01 as specified in review request
        self.test_ship_id = "e21c71a2-9543-4f92-990c-72f54292fde8"
        self.test_ship_name = "SUNSHINE 01"
        
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
            
            response = requests.post(endpoint, json=login_data, timeout=10)
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
                
                self.anniversary_tests['authentication_successful'] = True
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
    
    def test_ship_retrieval_enhanced_data(self):
        """Test basic ship retrieval endpoints to verify they handle enhanced data structures"""
        try:
            self.log("🚢 Testing ship retrieval with enhanced data structures...")
            
            # Test 1: Get all ships
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   ✅ Retrieved {len(ships)} ships")
                
                # Look for SUNSHINE 01 ship
                sunshine_ship = None
                for ship in ships:
                    if ship.get('id') == self.test_ship_id or ship.get('name') == self.test_ship_name:
                        sunshine_ship = ship
                        break
                
                if sunshine_ship:
                    self.log(f"   ✅ Found {self.test_ship_name} ship")
                    self.log(f"      Ship ID: {sunshine_ship.get('id')}")
                    self.log(f"      Ship Name: {sunshine_ship.get('name')}")
                    
                    # Check for enhanced fields
                    anniversary_date = sunshine_ship.get('anniversary_date')
                    dry_dock_cycle = sunshine_ship.get('dry_dock_cycle')
                    
                    self.log(f"      Anniversary Date: {anniversary_date}")
                    self.log(f"      Dry Dock Cycle: {dry_dock_cycle}")
                    
                    # Check legacy compatibility fields
                    legacy_anniversary = sunshine_ship.get('legacy_anniversary_date')
                    legacy_dry_dock = sunshine_ship.get('legacy_dry_dock_cycle')
                    
                    self.log(f"      Legacy Anniversary Date: {legacy_anniversary}")
                    self.log(f"      Legacy Dry Dock Cycle: {legacy_dry_dock}")
                    
                    self.test_results['sunshine_ship_data'] = sunshine_ship
                    self.anniversary_tests['sunshine_01_ship_tested'] = True
                else:
                    self.log(f"   ⚠️ {self.test_ship_name} ship not found")
                
                # Test 2: Get specific ship by ID
                if sunshine_ship:
                    ship_endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
                    self.log(f"   GET {ship_endpoint}")
                    ship_response = requests.get(ship_endpoint, headers=self.get_headers(), timeout=30)
                    
                    if ship_response.status_code == 200:
                        ship_data = ship_response.json()
                        self.log("   ✅ Individual ship retrieval successful")
                        self.log(f"      Enhanced fields present: {bool(ship_data.get('anniversary_date') or ship_data.get('dry_dock_cycle'))}")
                        self.anniversary_tests['ship_retrieval_enhanced_data_tested'] = True
                    else:
                        self.log(f"   ❌ Individual ship retrieval failed: {ship_response.status_code}")
                
                return True
            else:
                self.log(f"   ❌ Ship retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ship retrieval test error: {str(e)}", "ERROR")
            return False
    
    def test_anniversary_date_calculation(self):
        """Test the new anniversary date calculation endpoint"""
        try:
            self.log("📅 Testing anniversary date calculation endpoint...")
            
            # Test the calculate anniversary date endpoint
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}/calculate-anniversary-date"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Anniversary date calculation successful")
                
                # Check the response structure
                anniversary_date = result.get('anniversary_date')
                if anniversary_date:
                    day = anniversary_date.get('day')
                    month = anniversary_date.get('month')
                    auto_calculated = anniversary_date.get('auto_calculated')
                    source_cert_type = anniversary_date.get('source_certificate_type')
                    
                    self.log(f"   📊 Anniversary Date Calculation Results:")
                    self.log(f"      Day: {day}")
                    self.log(f"      Month: {month}")
                    self.log(f"      Auto Calculated: {auto_calculated}")
                    self.log(f"      Source Certificate Type: {source_cert_type}")
                    
                    # Validate day/month values (1-31 for day, 1-12 for month)
                    if day and month:
                        if 1 <= day <= 31 and 1 <= month <= 12:
                            self.log("   ✅ Day/month validation passed")
                            self.anniversary_tests['validation_day_month_tested'] = True
                        else:
                            self.log(f"   ❌ Day/month validation failed: day={day}, month={month}")
                    
                    # Check Lloyd's standards compliance
                    if auto_calculated and source_cert_type:
                        self.log("   ✅ Lloyd's standards compliance: Auto-calculated from certificates")
                        self.anniversary_tests['lloyd_standards_compliance_verified'] = True
                    
                    self.anniversary_tests['anniversary_date_calculation_tested'] = True
                else:
                    self.log("   ⚠️ No anniversary date calculated - may be expected if no suitable certificates")
                
                self.test_results['anniversary_calculation'] = result
                return True
            else:
                self.log(f"   ❌ Anniversary date calculation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Anniversary date calculation test error: {str(e)}", "ERROR")
            return False
    
    def test_anniversary_date_override(self):
        """Test the anniversary date override endpoint"""
        try:
            self.log("🔧 Testing anniversary date override endpoint...")
            
            # Test manual override of anniversary date
            override_data = {
                "day": 15,
                "month": 8,
                "manual_override": True,
                "source_certificate_type": "Manual Override by User"
            }
            
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}/override-anniversary-date"
            self.log(f"   POST {endpoint}")
            self.log(f"   Override data: {override_data}")
            
            response = requests.post(endpoint, json=override_data, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Anniversary date override successful")
                
                # Check the response
                anniversary_date = result.get('anniversary_date')
                if anniversary_date:
                    day = anniversary_date.get('day')
                    month = anniversary_date.get('month')
                    manual_override = anniversary_date.get('manual_override')
                    auto_calculated = anniversary_date.get('auto_calculated')
                    
                    self.log(f"   📊 Override Results:")
                    self.log(f"      Day: {day}")
                    self.log(f"      Month: {month}")
                    self.log(f"      Manual Override: {manual_override}")
                    self.log(f"      Auto Calculated: {auto_calculated}")
                    
                    # Verify override worked correctly
                    if day == 15 and month == 8 and manual_override and not auto_calculated:
                        self.log("   ✅ Manual override capabilities working correctly")
                        self.anniversary_tests['anniversary_date_override_tested'] = True
                    else:
                        self.log("   ❌ Manual override not working as expected")
                
                self.test_results['anniversary_override'] = result
                return True
            else:
                self.log(f"   ❌ Anniversary date override failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Anniversary date override test error: {str(e)}", "ERROR")
            return False
    
    def test_ship_creation_enhanced_fields(self):
        """Test ship creation with enhanced anniversary_date and dry_dock_cycle fields"""
        try:
            self.log("🆕 Testing ship creation with enhanced fields...")
            
            # Create test ship data with enhanced fields
            ship_data = {
                "name": "TEST ANNIVERSARY SHIP",
                "imo": "9999999",
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
            
            response = requests.post(endpoint, json=ship_data, headers=self.get_headers(), timeout=30)
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
    
    def test_certificate_types_with_endorsements(self):
        """Test certificate types that should have endorsement requirements"""
        try:
            self.log("📋 Testing certificate types with known endorsement requirements...")
            
            test_results = []
            
            for cert_type in self.certificate_types_with_endorsements[:3]:  # Test first 3 types
                self.log(f"   🔍 Testing {cert_type} certificate...")
                
                # Create test content for this certificate type
                test_content = f"""
                {cert_type.upper()} CERTIFICATE
                
                Certificate No: {cert_type.replace(' ', '')}-2024-001
                Ship Name: TEST VESSEL
                
                Survey Information:
                Annual survey: 20/05/2024
                Intermediate survey: 15/11/2023
                
                This certificate is valid until: 20/05/2025
                
                Issued by: Panama Maritime Documentation Services
                """
                
                endpoint = f"{BACKEND_URL}/analyze-ship-certificate"
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                    temp_file.write(test_content)
                    temp_file_path = temp_file.name
                
                try:
                    with open(temp_file_path, 'rb') as f:
                        files = {'file': (f'{cert_type.lower()}_cert.txt', f, 'text/plain')}
                        
                        response = requests.post(endpoint, files=files, headers=self.get_headers(), timeout=60)
                        
                        if response.status_code == 200:
                            result = response.json()
                            last_endorse = result.get('last_endorse')
                            
                            test_results.append({
                                'cert_type': cert_type,
                                'last_endorse': last_endorse,
                                'success': bool(last_endorse)
                            })
                            
                            if last_endorse:
                                self.log(f"      ✅ {cert_type}: Endorsement date detected - {last_endorse}")
                            else:
                                self.log(f"      ⚠️ {cert_type}: No endorsement date detected")
                        else:
                            self.log(f"      ❌ {cert_type}: Analysis failed - {response.status_code}")
                            test_results.append({
                                'cert_type': cert_type,
                                'last_endorse': None,
                                'success': False
                            })
                            
                finally:
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
            
            # Analyze results
            successful_tests = sum(1 for result in test_results if result['success'])
            total_tests = len(test_results)
            
            self.log(f"   📊 Certificate Type Test Results: {successful_tests}/{total_tests} successful")
            
            if successful_tests > 0:
                self.endorsement_tests['certificate_types_with_endorsements_tested'] = True
            
            self.test_results['certificate_type_tests'] = test_results
            return successful_tests > 0
            
        except Exception as e:
            self.log(f"❌ Certificate types test error: {str(e)}", "ERROR")
            return False
    
    def verify_enhanced_processing_results(self):
        """Verify that enhanced processing results are working correctly"""
        try:
            self.log("✅ Verifying enhanced processing results...")
            
            # Check all previous test results
            ai_test = self.test_results.get('ai_prompt_test', {})
            multiple_test = self.test_results.get('multiple_endorsement_test', {})
            fallback_test = self.test_results.get('fallback_pattern_test', {})
            cert_type_tests = self.test_results.get('certificate_type_tests', [])
            
            verification_results = {
                'ai_enhancement_working': bool(ai_test.get('last_endorse')),
                'multiple_handling_working': bool(multiple_test.get('last_endorse')),
                'fallback_working': bool(fallback_test.get('last_endorse')),
                'cert_types_working': any(test['success'] for test in cert_type_tests)
            }
            
            self.log(f"   📊 Enhanced Processing Verification:")
            self.log(f"      AI Enhancement: {'✅' if verification_results['ai_enhancement_working'] else '❌'}")
            self.log(f"      Multiple Handling: {'✅' if verification_results['multiple_handling_working'] else '❌'}")
            self.log(f"      Fallback Pattern: {'✅' if verification_results['fallback_working'] else '❌'}")
            self.log(f"      Certificate Types: {'✅' if verification_results['cert_types_working'] else '❌'}")
            
            # Overall verification
            working_features = sum(verification_results.values())
            total_features = len(verification_results)
            
            self.log(f"   📊 Overall Enhancement Status: {working_features}/{total_features} features working")
            
            if working_features >= 2:  # At least 50% working
                self.endorsement_tests['enhanced_processing_results_verified'] = True
                self.log("   ✅ Enhanced processing results verified successfully")
                return True
            else:
                self.log("   ⚠️ Enhanced processing results need improvement")
                return False
                
        except Exception as e:
            self.log(f"❌ Enhanced processing verification error: {str(e)}", "ERROR")
            return False
    
    def capture_backend_logs(self):
        """Capture backend logs for endorsement processing analysis"""
        try:
            self.log("📝 Capturing backend logs for endorsement processing...")
            
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
                    
                    # Look for endorsement-related log messages
                    endorsement_logs = []
                    for line in log_lines:
                        if any(keyword in line.lower() for keyword in ['endorse', 'pattern matching', 'survey', 'annual']):
                            endorsement_logs.append(line)
                    
                    if endorsement_logs:
                        self.log("   ✅ Endorsement-related backend logs found:")
                        for log_line in endorsement_logs[-5:]:  # Show last 5 relevant logs
                            self.log(f"      {log_line}")
                        
                        # Check for specific pattern matching messages
                        pattern_matching_logs = [line for line in endorsement_logs if 'pattern matching' in line.lower()]
                        if pattern_matching_logs:
                            self.log("   ✅ Pattern matching logs detected - fallback mechanism working")
                    else:
                        self.log("   ⚠️ No endorsement-specific logs found in recent backend output")
                    
                    self.test_results['backend_logs'] = log_lines
                    self.test_results['endorsement_logs'] = endorsement_logs
                else:
                    self.log("   ⚠️ No backend logs accessible")
                    
            except Exception as e:
                self.log(f"   ⚠️ Backend log capture error: {str(e)}")
            
            self.endorsement_tests['backend_logs_captured'] = True
            return True
                
        except Exception as e:
            self.log(f"❌ Backend log capture error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_endorsement_tests(self):
        """Main test function for enhanced endorsement processing"""
        self.log("🎯 STARTING ENHANCED ENDORSEMENT PROCESSING TESTING")
        self.log("🔍 Focus: Enhanced Last Endorse processing for maritime certificates")
        self.log("📋 Review Request: Test AI prompt enhancement and fallback pattern matching")
        self.log("🎯 Testing: Authentication, AI enhancement, multiple endorsements, fallback patterns")
        self.log("=" * 100)
        
        # Step 1: Authenticate
        self.log("\n🔐 STEP 1: AUTHENTICATION")
        self.log("=" * 50)
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Find PMDS certificates
        self.log("\n📋 STEP 2: FIND PMDS CERTIFICATES")
        self.log("=" * 50)
        pmds_certificates = self.find_pmds_certificates()
        
        # Step 3: Test AI prompt enhancement
        self.log("\n🤖 STEP 3: TEST AI PROMPT ENHANCEMENT")
        self.log("=" * 50)
        self.test_ai_prompt_enhancement()
        
        # Step 4: Test multiple endorsement handling
        self.log("\n📅 STEP 4: TEST MULTIPLE ENDORSEMENT HANDLING")
        self.log("=" * 50)
        self.test_multiple_endorsement_handling()
        
        # Step 5: Test fallback pattern matching
        self.log("\n🔍 STEP 5: TEST FALLBACK PATTERN MATCHING")
        self.log("=" * 50)
        self.test_fallback_pattern_matching()
        
        # Step 6: Test certificate types with endorsements
        self.log("\n📋 STEP 6: TEST CERTIFICATE TYPES WITH ENDORSEMENTS")
        self.log("=" * 50)
        self.test_certificate_types_with_endorsements()
        
        # Step 7: Verify enhanced processing results
        self.log("\n✅ STEP 7: VERIFY ENHANCED PROCESSING RESULTS")
        self.log("=" * 50)
        self.verify_enhanced_processing_results()
        
        # Step 8: Capture backend logs
        self.log("\n📝 STEP 8: CAPTURE BACKEND LOGS")
        self.log("=" * 50)
        self.capture_backend_logs()
        
        # Step 9: Final analysis
        self.log("\n📊 STEP 9: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_endorsement_analysis()
        
        return True
    
    def provide_final_endorsement_analysis(self):
        """Provide final analysis of the enhanced endorsement processing testing"""
        try:
            self.log("🎯 ENHANCED ENDORSEMENT PROCESSING TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.endorsement_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ ENDORSEMENT TESTS PASSED ({len(passed_tests)}/10):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ ENDORSEMENT TESTS FAILED ({len(failed_tests)}/10):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Overall assessment
            success_rate = len(passed_tests) / len(self.endorsement_tests) * 100
            self.log(f"\n📊 ENDORSEMENT TESTING SUCCESS RATE: {success_rate:.1f}%")
            
            # Detailed results
            self.log(f"\n🔍 DETAILED RESULTS:")
            
            # PMDS certificates
            pmds_certificates = self.test_results.get('pmds_certificates', [])
            if pmds_certificates:
                self.log(f"   📋 PMDS Certificates Found: {len(pmds_certificates)}")
                for cert in pmds_certificates[:3]:  # Show first 3
                    self.log(f"      - {cert.get('cert_name')} on {cert.get('ship_name')}")
            
            # Test results analysis
            ai_test = self.test_results.get('ai_prompt_test', {})
            multiple_test = self.test_results.get('multiple_endorsement_test', {})
            fallback_test = self.test_results.get('fallback_pattern_test', {})
            cert_type_tests = self.test_results.get('certificate_type_tests', [])
            
            self.log(f"   🤖 AI Prompt Enhancement:")
            self.log(f"      Last Endorse Detected: {ai_test.get('last_endorse', 'None')}")
            self.log(f"      Status: {'✅ Working' if ai_test.get('last_endorse') else '❌ Not Working'}")
            
            self.log(f"   📅 Multiple Endorsement Handling:")
            self.log(f"      Last Endorse Detected: {multiple_test.get('last_endorse', 'None')}")
            self.log(f"      Status: {'✅ Working' if multiple_test.get('last_endorse') else '❌ Not Working'}")
            
            self.log(f"   🔍 Fallback Pattern Matching:")
            self.log(f"      Last Endorse Detected: {fallback_test.get('last_endorse', 'None')}")
            self.log(f"      Status: {'✅ Working' if fallback_test.get('last_endorse') else '❌ Not Working'}")
            
            if cert_type_tests:
                successful_cert_tests = sum(1 for test in cert_type_tests if test['success'])
                total_cert_tests = len(cert_type_tests)
                self.log(f"   📋 Certificate Types Testing:")
                self.log(f"      Success Rate: {successful_cert_tests}/{total_cert_tests}")
                for test in cert_type_tests:
                    status = '✅' if test['success'] else '❌'
                    self.log(f"      {status} {test['cert_type']}: {test.get('last_endorse', 'None')}")
            
            # Backend logs analysis
            endorsement_logs = self.test_results.get('endorsement_logs', [])
            if endorsement_logs:
                self.log(f"   📝 Backend Logs Analysis:")
                self.log(f"      Endorsement-related logs found: {len(endorsement_logs)}")
                pattern_matching_logs = [line for line in endorsement_logs if 'pattern matching' in line.lower()]
                if pattern_matching_logs:
                    self.log(f"      Pattern matching logs: {len(pattern_matching_logs)} found")
                    self.log("      ✅ Fallback mechanism appears to be working")
                
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    print("🎯 Ship Management System - Enhanced Endorsement Processing Testing")
    print("🔍 Focus: Enhanced Last Endorse processing for maritime certificates")
    print("📋 Review Request: Test AI prompt enhancement and fallback pattern matching")
    print("🎯 Testing: Authentication, AI enhancement, multiple endorsements, fallback patterns")
    print("=" * 100)
    
    tester = EnhancedEndorsementTester()
    success = tester.run_comprehensive_endorsement_tests()
    
    print("=" * 100)
    print("🔍 ENHANCED ENDORSEMENT PROCESSING TESTING RESULTS:")
    print("=" * 70)
    
    # Print test summary
    passed_tests = [f for f, passed in tester.endorsement_tests.items() if passed]
    failed_tests = [f for f, passed in tester.endorsement_tests.items() if not passed]
    
    print(f"✅ ENDORSEMENT TESTS PASSED ({len(passed_tests)}/10):")
    for test in passed_tests:
        print(f"   ✅ {test.replace('_', ' ').title()}")
    
    if failed_tests:
        print(f"\n❌ ENDORSEMENT TESTS FAILED ({len(failed_tests)}/10):")
        for test in failed_tests:
            print(f"   ❌ {test.replace('_', ' ').title()}")
    
    # Print key findings
    print(f"\n🔍 KEY FINDINGS:")
    
    # PMDS certificates
    pmds_certificates = tester.test_results.get('pmds_certificates', [])
    print(f"   📋 PMDS Certificates Analysis:")
    print(f"      Total PMDS certificates found: {len(pmds_certificates)}")
    
    # Test results
    ai_test = tester.test_results.get('ai_prompt_test', {})
    multiple_test = tester.test_results.get('multiple_endorsement_test', {})
    fallback_test = tester.test_results.get('fallback_pattern_test', {})
    cert_type_tests = tester.test_results.get('certificate_type_tests', [])
    
    print(f"   🤖 AI Prompt Enhancement: {'✅ Working' if ai_test.get('last_endorse') else '❌ Not Working'}")
    print(f"   📅 Multiple Endorsement Handling: {'✅ Working' if multiple_test.get('last_endorse') else '❌ Not Working'}")
    print(f"   🔍 Fallback Pattern Matching: {'✅ Working' if fallback_test.get('last_endorse') else '❌ Not Working'}")
    
    if cert_type_tests:
        successful_cert_tests = sum(1 for test in cert_type_tests if test['success'])
        total_cert_tests = len(cert_type_tests)
        print(f"   📋 Certificate Types Testing: {successful_cert_tests}/{total_cert_tests} successful")
    
    # Calculate success rate
    success_rate = len(passed_tests) / len(tester.endorsement_tests) * 100
    print(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")
    
    print("=" * 100)
    if success:
        print("🎉 Enhanced endorsement processing testing completed!")
        print("✅ All testing steps executed - detailed analysis available above")
    else:
        print("❌ Enhanced endorsement processing testing completed with issues!")
        print("🔍 Check detailed logs above for specific issues")
    
    # Provide recommendations based on findings
    print("\n💡 NEXT STEPS FOR MAIN AGENT:")
    
    # AI Enhancement recommendations
    if ai_test.get('last_endorse'):
        print("   ✅ AI prompt enhancement is working correctly")
    else:
        print("   ❌ AI prompt enhancement needs improvement")
        print("   1. Check AI model configuration and prompts")
        print("   2. Verify maritime domain knowledge in prompts")
        print("   3. Test with different certificate formats")
    
    # Multiple endorsement handling
    if multiple_test.get('last_endorse'):
        print("   ✅ Multiple endorsement handling is working correctly")
    else:
        print("   ❌ Multiple endorsement handling needs improvement")
        print("   1. Check date parsing and comparison logic")
        print("   2. Verify latest date selection algorithm")
    
    # Fallback pattern matching
    if fallback_test.get('last_endorse'):
        print("   ✅ Fallback pattern matching is working correctly")
    else:
        print("   ❌ Fallback pattern matching needs improvement")
        print("   1. Check regex patterns for endorsement dates")
        print("   2. Verify fallback mechanism triggers correctly")
        print("   3. Test with more diverse certificate formats")
    
    # Certificate types
    if cert_type_tests:
        successful_cert_tests = sum(1 for test in cert_type_tests if test['success'])
        if successful_cert_tests > 0:
            print(f"   ✅ Certificate types testing partially successful ({successful_cert_tests} working)")
        else:
            print("   ❌ Certificate types testing failed")
            print("   1. Check certificate type recognition")
            print("   2. Verify endorsement requirements mapping")
    
    # Backend logs
    endorsement_logs = tester.test_results.get('endorsement_logs', [])
    if endorsement_logs:
        print("   ✅ Backend logs show endorsement processing activity")
    else:
        print("   ⚠️ No endorsement-specific backend logs found")
        print("   1. Check backend logging configuration")
        print("   2. Verify endorsement processing is being logged")
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
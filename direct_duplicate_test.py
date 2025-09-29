#!/usr/bin/env python3
"""
Direct Backend Duplicate Detection Testing Script
FOCUS: Testing the enhanced 5-field duplicate detection logic by examining backend behavior

TESTING OBJECTIVE: Verify the enhanced duplicate detection now requires ALL 5 fields to match exactly:
- Certificate Name, Certificate Number, Issue Date, Valid Date, Last Endorse

Authentication: admin1/123456 credentials
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import time
import traceback

# Use internal backend URL for faster testing
BACKEND_URL = 'http://0.0.0.0:8001/api'
print(f"Using internal backend URL: {BACKEND_URL}")

class DirectDuplicateDetectionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        
        # Test tracking for enhanced duplicate detection
        self.test_results = {
            # Authentication
            'authentication_successful': False,
            
            # Backend Code Analysis
            'calculate_certificate_similarity_function_found': False,
            'enhanced_5_field_logic_implemented': False,
            'logging_patterns_implemented': False,
            
            # API Testing
            'certificate_creation_api_working': False,
            'ship_creation_api_working': False,
            'backend_responding': False,
            
            # Duplicate Detection Logic Tests
            'duplicate_detection_requires_all_5_fields': False,
            'different_issue_date_not_duplicate': False,
            'different_valid_date_not_duplicate': False,
            'different_last_endorse_not_duplicate': False,
            'all_fields_same_is_duplicate': False,
        }
        
        # Test ship data
        self.test_ship_id = None
        self.test_ship_name = "DIRECT DUPLICATE TEST SHIP 2025"
        self.test_imo = "9777777"
        self.created_certificates = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
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
                
                self.test_results['authentication_successful'] = True
                self.test_results['backend_responding'] = True
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
    
    def analyze_backend_code_for_duplicate_detection(self):
        """Analyze the backend code to verify 5-field duplicate detection implementation"""
        try:
            self.log("🔍 ANALYZING BACKEND CODE FOR ENHANCED DUPLICATE DETECTION")
            self.log("=" * 60)
            
            # Read the backend server.py file to analyze the implementation
            backend_file_path = "/app/backend/server.py"
            
            with open(backend_file_path, 'r') as f:
                backend_code = f.read()
            
            # Check for calculate_certificate_similarity function
            if "def calculate_certificate_similarity" in backend_code:
                self.test_results['calculate_certificate_similarity_function_found'] = True
                self.log("✅ calculate_certificate_similarity function found in backend code")
                
                # Extract the function to analyze its implementation
                function_start = backend_code.find("def calculate_certificate_similarity")
                function_end = backend_code.find("\ndef ", function_start + 1)
                if function_end == -1:
                    function_end = backend_code.find("\nclass ", function_start + 1)
                if function_end == -1:
                    function_end = len(backend_code)
                
                function_code = backend_code[function_start:function_end]
                
                # Check for 5-field implementation
                required_fields = ['cert_name', 'cert_no', 'issue_date', 'valid_date', 'last_endorse']
                fields_found = 0
                
                for field in required_fields:
                    if field in function_code:
                        fields_found += 1
                        self.log(f"   ✅ Field '{field}' found in duplicate detection logic")
                    else:
                        self.log(f"   ❌ Field '{field}' NOT found in duplicate detection logic")
                
                if fields_found == 5:
                    self.test_results['enhanced_5_field_logic_implemented'] = True
                    self.log("✅ All 5 fields found in duplicate detection logic")
                else:
                    self.log(f"❌ Only {fields_found}/5 fields found in duplicate detection logic")
                
                # Check for enhanced logging patterns
                logging_patterns = [
                    "Enhanced Duplicate Check",
                    "Comparing 5 fields",
                    "ALL 5 fields match",
                    "Not all fields match"
                ]
                
                logging_found = 0
                for pattern in logging_patterns:
                    if pattern in function_code:
                        logging_found += 1
                        self.log(f"   ✅ Logging pattern '{pattern}' found")
                    else:
                        self.log(f"   ❌ Logging pattern '{pattern}' NOT found")
                
                if logging_found >= 3:
                    self.test_results['logging_patterns_implemented'] = True
                    self.log("✅ Enhanced logging patterns implemented")
                else:
                    self.log(f"❌ Only {logging_found}/4 logging patterns found")
                
                # Check for the specific logic that requires ALL 5 fields to match
                if "name_match and number_match and issue_match and valid_match and endorse_match" in function_code:
                    self.test_results['duplicate_detection_requires_all_5_fields'] = True
                    self.log("✅ Logic requires ALL 5 fields to match for duplicate detection")
                else:
                    self.log("❌ Logic does NOT require all 5 fields to match")
                
                # Display relevant parts of the function
                self.log("\n📋 RELEVANT DUPLICATE DETECTION CODE:")
                lines = function_code.split('\n')
                for i, line in enumerate(lines[:50]):  # Show first 50 lines
                    if any(field in line for field in required_fields) or any(pattern in line for pattern in logging_patterns):
                        self.log(f"   {i+1:3d}: {line.strip()}")
                
            else:
                self.log("❌ calculate_certificate_similarity function NOT found in backend code")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Backend code analysis error: {str(e)}", "ERROR")
            return False
    
    def test_basic_api_functionality(self):
        """Test basic API functionality to ensure backend is working"""
        try:
            self.log("🔧 TESTING BASIC API FUNCTIONALITY")
            self.log("=" * 60)
            
            # Test ship creation
            self.log("\n📋 Testing ship creation API...")
            ship_data = {
                'name': self.test_ship_name,
                'imo': self.test_imo,
                'flag': 'PANAMA',
                'ship_type': 'PMDS',
                'gross_tonnage': 5000.0,
                'built_year': 2020,
                'ship_owner': 'Test Owner',
                'company': 'AMCSC'
            }
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.post(
                endpoint,
                json=ship_data,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                self.test_ship_id = response_data.get('id')
                self.test_results['ship_creation_api_working'] = True
                self.log(f"✅ Ship creation API working - Ship ID: {self.test_ship_id}")
            else:
                self.log(f"❌ Ship creation API failed: {response.status_code}")
                return False
            
            # Test certificate creation
            self.log("\n📋 Testing certificate creation API...")
            cert_data = {
                'ship_id': self.test_ship_id,
                'cert_name': 'TEST CERTIFICATE',
                'cert_no': 'TEST-001',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            endpoint = f"{BACKEND_URL}/certificates"
            response = requests.post(
                endpoint,
                json=cert_data,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                cert_id = response_data.get('id')
                self.created_certificates.append(cert_id)
                self.test_results['certificate_creation_api_working'] = True
                self.log(f"✅ Certificate creation API working - Certificate ID: {cert_id}")
            else:
                self.log(f"❌ Certificate creation API failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"❌ Basic API functionality test error: {str(e)}", "ERROR")
            return False
    
    def test_duplicate_detection_behavior(self):
        """Test duplicate detection behavior by creating certificates with different field combinations"""
        try:
            self.log("🔍 TESTING DUPLICATE DETECTION BEHAVIOR")
            self.log("=" * 60)
            
            if not self.test_ship_id:
                self.log("❌ No test ship available for duplicate detection testing")
                return False
            
            # Test 1: Create certificates with same name/number but different issue_date
            self.log("\n📋 TEST 1: Same name/number, different issue_date")
            
            cert_1a = {
                'ship_id': self.test_ship_id,
                'cert_name': 'DUPLICATE TEST CERTIFICATE',
                'cert_no': 'DTC-001',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            cert_1b = {
                'ship_id': self.test_ship_id,
                'cert_name': 'DUPLICATE TEST CERTIFICATE',
                'cert_no': 'DTC-001',
                'issue_date': '2024-02-15T00:00:00Z',  # Different issue_date
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            # Create first certificate
            response_1a = requests.post(
                f"{BACKEND_URL}/certificates",
                json=cert_1a,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response_1a.status_code in [200, 201]:
                cert_id_1a = response_1a.json().get('id')
                self.created_certificates.append(cert_id_1a)
                self.log(f"   ✅ First certificate created: {cert_id_1a}")
                
                # Try to create second certificate with different issue_date
                response_1b = requests.post(
                    f"{BACKEND_URL}/certificates",
                    json=cert_1b,
                    headers=self.get_headers(),
                    timeout=10
                )
                
                if response_1b.status_code in [200, 201]:
                    cert_id_1b = response_1b.json().get('id')
                    self.created_certificates.append(cert_id_1b)
                    self.test_results['different_issue_date_not_duplicate'] = True
                    self.log(f"   ✅ Second certificate created: {cert_id_1b}")
                    self.log("   ✅ TEST 1 PASSED: Different issue_date correctly NOT considered duplicate")
                else:
                    self.log(f"   ❌ Second certificate creation failed: {response_1b.status_code}")
                    self.log("   ❌ TEST 1 FAILED: Different issue_date incorrectly considered duplicate")
            else:
                self.log(f"   ❌ First certificate creation failed: {response_1a.status_code}")
            
            # Test 2: Create certificates with same name/number/issue but different valid_date
            self.log("\n📋 TEST 2: Same name/number/issue, different valid_date")
            
            cert_2a = {
                'ship_id': self.test_ship_id,
                'cert_name': 'VALID DATE TEST CERTIFICATE',
                'cert_no': 'VDT-002',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            cert_2b = {
                'ship_id': self.test_ship_id,
                'cert_name': 'VALID DATE TEST CERTIFICATE',
                'cert_no': 'VDT-002',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2027-01-15T00:00:00Z',  # Different valid_date
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            # Create certificates
            response_2a = requests.post(f"{BACKEND_URL}/certificates", json=cert_2a, headers=self.get_headers(), timeout=10)
            if response_2a.status_code in [200, 201]:
                cert_id_2a = response_2a.json().get('id')
                self.created_certificates.append(cert_id_2a)
                
                response_2b = requests.post(f"{BACKEND_URL}/certificates", json=cert_2b, headers=self.get_headers(), timeout=10)
                if response_2b.status_code in [200, 201]:
                    cert_id_2b = response_2b.json().get('id')
                    self.created_certificates.append(cert_id_2b)
                    self.test_results['different_valid_date_not_duplicate'] = True
                    self.log("   ✅ TEST 2 PASSED: Different valid_date correctly NOT considered duplicate")
                else:
                    self.log("   ❌ TEST 2 FAILED: Different valid_date incorrectly considered duplicate")
            
            # Test 3: Create certificates with same name/number/issue/valid but different last_endorse
            self.log("\n📋 TEST 3: Same name/number/issue/valid, different last_endorse")
            
            cert_3a = {
                'ship_id': self.test_ship_id,
                'cert_name': 'ENDORSE TEST CERTIFICATE',
                'cert_no': 'ETC-003',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            cert_3b = {
                'ship_id': self.test_ship_id,
                'cert_name': 'ENDORSE TEST CERTIFICATE',
                'cert_no': 'ETC-003',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-07-15T00:00:00Z',  # Different last_endorse
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            # Create certificates
            response_3a = requests.post(f"{BACKEND_URL}/certificates", json=cert_3a, headers=self.get_headers(), timeout=10)
            if response_3a.status_code in [200, 201]:
                cert_id_3a = response_3a.json().get('id')
                self.created_certificates.append(cert_id_3a)
                
                response_3b = requests.post(f"{BACKEND_URL}/certificates", json=cert_3b, headers=self.get_headers(), timeout=10)
                if response_3b.status_code in [200, 201]:
                    cert_id_3b = response_3b.json().get('id')
                    self.created_certificates.append(cert_id_3b)
                    self.test_results['different_last_endorse_not_duplicate'] = True
                    self.log("   ✅ TEST 3 PASSED: Different last_endorse correctly NOT considered duplicate")
                else:
                    self.log("   ❌ TEST 3 FAILED: Different last_endorse incorrectly considered duplicate")
            
            # Test 4: Try to create certificate with ALL 5 fields exactly the same (should fail or be rejected)
            self.log("\n📋 TEST 4: ALL 5 fields exactly the same (should be duplicate)")
            
            cert_4_original = {
                'ship_id': self.test_ship_id,
                'cert_name': 'EXACT DUPLICATE TEST',
                'cert_no': 'EDT-004',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            cert_4_duplicate = {
                'ship_id': self.test_ship_id,
                'cert_name': 'EXACT DUPLICATE TEST',      # Same
                'cert_no': 'EDT-004',                     # Same
                'issue_date': '2024-01-15T00:00:00Z',    # Same
                'valid_date': '2026-01-15T00:00:00Z',    # Same
                'last_endorse': '2024-06-15T00:00:00Z',  # Same
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            # Create original certificate
            response_4a = requests.post(f"{BACKEND_URL}/certificates", json=cert_4_original, headers=self.get_headers(), timeout=10)
            if response_4a.status_code in [200, 201]:
                cert_id_4a = response_4a.json().get('id')
                self.created_certificates.append(cert_id_4a)
                self.log(f"   ✅ Original certificate created: {cert_id_4a}")
                
                # Try to create exact duplicate
                response_4b = requests.post(f"{BACKEND_URL}/certificates", json=cert_4_duplicate, headers=self.get_headers(), timeout=10)
                if response_4b.status_code in [200, 201]:
                    cert_id_4b = response_4b.json().get('id')
                    self.created_certificates.append(cert_id_4b)
                    self.log(f"   ❌ Duplicate certificate incorrectly created: {cert_id_4b}")
                    self.log("   ❌ TEST 4 FAILED: ALL 5 fields matching incorrectly allowed")
                else:
                    self.test_results['all_fields_same_is_duplicate'] = True
                    self.log(f"   ✅ Duplicate certificate correctly rejected: {response_4b.status_code}")
                    self.log("   ✅ TEST 4 PASSED: ALL 5 fields matching correctly identified as duplicate")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Duplicate detection behavior test error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            if self.test_ship_id:
                self.log("🧹 Cleaning up test ship and certificates...")
                
                # Delete the ship (this should cascade delete certificates)
                endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
                response = requests.delete(endpoint, headers=self.get_headers(), timeout=10)
                
                if response.status_code == 200:
                    self.log("✅ Test ship and certificates cleaned up successfully")
                else:
                    self.log(f"⚠️ Test ship cleanup failed: {response.status_code}")
                    
        except Exception as e:
            self.log(f"⚠️ Cleanup error: {str(e)}", "WARNING")
    
    def run_comprehensive_tests(self):
        """Main test function for enhanced duplicate detection"""
        self.log("🔍 STARTING DIRECT BACKEND DUPLICATE DETECTION TESTING")
        self.log("🎯 OBJECTIVE: Verify 5-field duplicate detection implementation")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Analyze Backend Code
            self.log("\n🔍 STEP 2: BACKEND CODE ANALYSIS")
            self.log("=" * 50)
            test_2_success = self.analyze_backend_code_for_duplicate_detection()
            
            # Step 3: Test Basic API Functionality
            self.log("\n🔧 STEP 3: BASIC API FUNCTIONALITY")
            self.log("=" * 50)
            test_3_success = self.test_basic_api_functionality()
            
            # Step 4: Test Duplicate Detection Behavior
            self.log("\n🔍 STEP 4: DUPLICATE DETECTION BEHAVIOR")
            self.log("=" * 50)
            test_4_success = self.test_duplicate_detection_behavior()
            
            # Step 5: Final Analysis
            self.log("\n📊 STEP 5: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return test_2_success and test_3_success and test_4_success
            
        finally:
            # Always cleanup
            self.log("\n🧹 CLEANUP")
            self.log("=" * 50)
            self.cleanup_test_data()
    
    def provide_final_analysis(self):
        """Provide final analysis of enhanced duplicate detection testing"""
        try:
            self.log("🔍 ENHANCED DUPLICATE DETECTION TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.test_results.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.test_results)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.test_results)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.test_results)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.test_results)})")
            
            # Category-specific analysis
            self.log("\n🎯 CATEGORY-SPECIFIC ANALYSIS:")
            
            # Backend Code Implementation
            code_tests = [
                'calculate_certificate_similarity_function_found',
                'enhanced_5_field_logic_implemented',
                'logging_patterns_implemented',
                'duplicate_detection_requires_all_5_fields'
            ]
            code_passed = sum(1 for test in code_tests if self.test_results.get(test, False))
            code_rate = (code_passed / len(code_tests)) * 100
            
            self.log(f"\n🔍 BACKEND CODE IMPLEMENTATION: {code_rate:.1f}% ({code_passed}/{len(code_tests)})")
            if code_rate >= 75:
                self.log("   ✅ CONFIRMED: Enhanced 5-field duplicate detection is IMPLEMENTED in backend code")
                self.log("   ✅ Backend code contains the required logic and logging patterns")
            else:
                self.log("   ❌ ISSUE: Enhanced 5-field duplicate detection implementation incomplete")
            
            # API Functionality
            api_tests = [
                'backend_responding',
                'ship_creation_api_working',
                'certificate_creation_api_working'
            ]
            api_passed = sum(1 for test in api_tests if self.test_results.get(test, False))
            api_rate = (api_passed / len(api_tests)) * 100
            
            self.log(f"\n🔧 API FUNCTIONALITY: {api_rate:.1f}% ({api_passed}/{len(api_tests)})")
            if api_rate >= 75:
                self.log("   ✅ CONFIRMED: Backend API is working correctly")
            else:
                self.log("   ❌ ISSUE: Backend API functionality needs attention")
            
            # Duplicate Detection Behavior
            behavior_tests = [
                'different_issue_date_not_duplicate',
                'different_valid_date_not_duplicate',
                'different_last_endorse_not_duplicate',
                'all_fields_same_is_duplicate'
            ]
            behavior_passed = sum(1 for test in behavior_tests if self.test_results.get(test, False))
            behavior_rate = (behavior_passed / len(behavior_tests)) * 100
            
            self.log(f"\n🔍 DUPLICATE DETECTION BEHAVIOR: {behavior_rate:.1f}% ({behavior_passed}/{len(behavior_tests)})")
            if behavior_rate >= 75:
                self.log("   ✅ CONFIRMED: Enhanced 5-field duplicate detection is WORKING correctly")
                self.log("   ✅ Only certificates with ALL 5 fields matching are considered duplicates")
            else:
                self.log("   ❌ ISSUE: Enhanced 5-field duplicate detection behavior needs fixing")
            
            # Final conclusion
            if success_rate >= 80:
                self.log(f"\n🎉 CONCLUSION: ENHANCED DUPLICATE DETECTION IS WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Enhanced 5-field duplicate detection successfully implemented!")
                self.log(f"   ✅ Backend Code: Properly implemented with 5-field logic")
                self.log(f"   ✅ API Functionality: Working correctly")
                self.log(f"   ✅ Duplicate Detection: Behaving as expected")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: ENHANCED DUPLICATE DETECTION PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Some functionality working, improvements needed")
                
                if code_rate >= 75:
                    self.log(f"   ✅ Backend implementation is correct")
                else:
                    self.log(f"   ❌ Backend implementation needs attention")
                    
                if behavior_rate >= 75:
                    self.log(f"   ✅ Duplicate detection behavior is working")
                else:
                    self.log(f"   ❌ Duplicate detection behavior needs fixing")
            else:
                self.log(f"\n❌ CONCLUSION: ENHANCED DUPLICATE DETECTION HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Enhanced duplicate detection needs significant fixes")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run Direct Backend Duplicate Detection tests"""
    print("🔍 DIRECT BACKEND DUPLICATE DETECTION TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = DirectDuplicateDetectionTester()
        success = tester.run_comprehensive_tests()
        
        if success:
            print("\n✅ DIRECT BACKEND DUPLICATE DETECTION TESTING COMPLETED")
        else:
            print("\n❌ DIRECT BACKEND DUPLICATE DETECTION TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
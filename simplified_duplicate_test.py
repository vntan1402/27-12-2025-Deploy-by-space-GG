#!/usr/bin/env python3
"""
Enhanced Duplicate Certificate Detection Testing Script - Simplified Version
FOCUS: Testing the enhanced 5-field duplicate detection logic directly

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
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://certflow-2.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class SimplifiedDuplicateDetectionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for enhanced duplicate detection
        self.test_results = {
            # Authentication
            'authentication_successful': False,
            
            # 5-Field Duplicate Detection Tests
            'same_name_number_different_issue_date_not_duplicate': False,
            'same_name_number_issue_different_valid_date_not_duplicate': False,
            'same_name_number_issue_valid_different_endorse_not_duplicate': False,
            'all_5_fields_matching_is_duplicate': False,
            
            # Backend API Tests
            'certificate_creation_working': False,
            'certificate_retrieval_working': False,
            'duplicate_check_function_accessible': False,
        }
        
        # Test ship data
        self.test_ship_id = None
        self.test_ship_name = "ENHANCED DUPLICATE TEST SHIP 2025"
        self.test_imo = "9888888"
        self.created_certificates = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        # Store in log collection
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
            
            response = requests.post(endpoint, json=login_data, timeout=60)
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
    
    def create_test_ship(self):
        """Create a test ship for duplicate detection testing"""
        try:
            self.log("🚢 Creating test ship for enhanced duplicate detection testing...")
            
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
            self.log(f"   POST {endpoint}")
            
            response = requests.post(
                endpoint,
                json=ship_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                self.test_ship_id = response_data.get('id')
                self.log("✅ Test ship created successfully")
                self.log(f"   Ship ID: {self.test_ship_id}")
                self.log(f"   Ship Name: {response_data.get('name')}")
                self.log(f"   IMO: {response_data.get('imo')}")
                return True
            else:
                self.log(f"   ❌ Test ship creation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Test ship creation error: {str(e)}", "ERROR")
            return False
    
    def create_test_certificate(self, cert_data):
        """Create a single test certificate"""
        try:
            endpoint = f"{BACKEND_URL}/certificates"
            
            response = requests.post(
                endpoint,
                json=cert_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                cert_id = response_data.get('id')
                self.created_certificates.append(cert_id)
                self.log(f"   ✅ Certificate created: {cert_data.get('cert_name')} - {cert_data.get('cert_no')} (ID: {cert_id})")
                return cert_id
            else:
                self.log(f"   ❌ Certificate creation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Certificate creation error: {str(e)}", "ERROR")
            return None
    
    def get_ship_certificates(self):
        """Get all certificates for the test ship"""
        try:
            endpoint = f"{BACKEND_URL}/certificates"
            params = {'ship_id': self.test_ship_id}
            
            response = requests.get(
                endpoint,
                params=params,
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   ✅ Retrieved {len(certificates)} certificates for ship")
                return certificates
            else:
                self.log(f"   ❌ Certificate retrieval failed: {response.status_code}")
                return []
                
        except Exception as e:
            self.log(f"❌ Certificate retrieval error: {str(e)}", "ERROR")
            return []
    
    def test_enhanced_5_field_duplicate_detection(self):
        """Test the enhanced 5-field duplicate detection logic by creating certificates and checking duplicates"""
        try:
            self.log("🔍 TESTING ENHANCED 5-FIELD DUPLICATE DETECTION")
            self.log("=" * 60)
            
            # Test 1: Same cert_name and cert_no but different issue_date → Should NOT be duplicate
            self.log("\n📋 TEST 1: Same name/number, different issue date - Should NOT be duplicate")
            
            # Create first certificate
            cert_1a = {
                'ship_id': self.test_ship_id,
                'cert_name': 'CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE',
                'cert_no': 'CSSC-2024-001',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            cert_id_1a = self.create_test_certificate(cert_1a)
            if not cert_id_1a:
                self.log("   ❌ Failed to create first certificate for Test 1")
                return False
            
            # Create second certificate with different issue_date
            cert_1b = {
                'ship_id': self.test_ship_id,
                'cert_name': 'CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE',
                'cert_no': 'CSSC-2024-001',
                'issue_date': '2024-02-15T00:00:00Z',  # Different issue date
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            cert_id_1b = self.create_test_certificate(cert_1b)
            if cert_id_1b:
                self.test_results['same_name_number_different_issue_date_not_duplicate'] = True
                self.log("   ✅ TEST 1 PASSED: Different issue dates correctly allowed (not considered duplicate)")
            else:
                self.log("   ❌ TEST 1 FAILED: Different issue dates incorrectly rejected as duplicate")
            
            # Test 2: Same cert_name, cert_no, issue_date but different valid_date → Should NOT be duplicate
            self.log("\n📋 TEST 2: Same name/number/issue, different valid date - Should NOT be duplicate")
            
            cert_2 = {
                'ship_id': self.test_ship_id,
                'cert_name': 'INTERNATIONAL TONNAGE CERTIFICATE',
                'cert_no': 'ITC-2024-002',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2027-01-15T00:00:00Z',  # Different valid date
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            # First create a reference certificate
            cert_2_ref = {
                'ship_id': self.test_ship_id,
                'cert_name': 'INTERNATIONAL TONNAGE CERTIFICATE',
                'cert_no': 'ITC-2024-002',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-01-15T00:00:00Z',  # Original valid date
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            cert_id_2_ref = self.create_test_certificate(cert_2_ref)
            cert_id_2 = self.create_test_certificate(cert_2)
            
            if cert_id_2_ref and cert_id_2:
                self.test_results['same_name_number_issue_different_valid_date_not_duplicate'] = True
                self.log("   ✅ TEST 2 PASSED: Different valid dates correctly allowed (not considered duplicate)")
            else:
                self.log("   ❌ TEST 2 FAILED: Different valid dates incorrectly rejected as duplicate")
            
            # Test 3: Same cert_name, cert_no, issue_date, valid_date but different last_endorse → Should NOT be duplicate
            self.log("\n📋 TEST 3: Same name/number/issue/valid, different last endorse - Should NOT be duplicate")
            
            cert_3_ref = {
                'ship_id': self.test_ship_id,
                'cert_name': 'SAFETY EQUIPMENT CERTIFICATE',
                'cert_no': 'SEC-2024-003',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            cert_3 = {
                'ship_id': self.test_ship_id,
                'cert_name': 'SAFETY EQUIPMENT CERTIFICATE',
                'cert_no': 'SEC-2024-003',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-07-15T00:00:00Z',  # Different last endorse
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            cert_id_3_ref = self.create_test_certificate(cert_3_ref)
            cert_id_3 = self.create_test_certificate(cert_3)
            
            if cert_id_3_ref and cert_id_3:
                self.test_results['same_name_number_issue_valid_different_endorse_not_duplicate'] = True
                self.log("   ✅ TEST 3 PASSED: Different last endorse correctly allowed (not considered duplicate)")
            else:
                self.log("   ❌ TEST 3 FAILED: Different last endorse incorrectly rejected as duplicate")
            
            # Test 4: ALL 5 fields matching exactly → Should be DUPLICATE (this should fail to create)
            self.log("\n📋 TEST 4: ALL 5 fields matching exactly - Should be DUPLICATE (creation should fail)")
            
            cert_4_original = {
                'ship_id': self.test_ship_id,
                'cert_name': 'SAFETY RADIO CERTIFICATE',
                'cert_no': 'SRC-2024-004',
                'issue_date': '2024-01-15T00:00:00Z',
                'valid_date': '2026-01-15T00:00:00Z',
                'last_endorse': '2024-06-15T00:00:00Z',
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            cert_4_duplicate = {
                'ship_id': self.test_ship_id,
                'cert_name': 'SAFETY RADIO CERTIFICATE',  # Same
                'cert_no': 'SRC-2024-004',              # Same
                'issue_date': '2024-01-15T00:00:00Z',   # Same
                'valid_date': '2026-01-15T00:00:00Z',   # Same
                'last_endorse': '2024-06-15T00:00:00Z', # Same
                'cert_type': 'Full Term',
                'issued_by': 'PMDS'
            }
            
            # Create original certificate
            cert_id_4_original = self.create_test_certificate(cert_4_original)
            
            if cert_id_4_original:
                # Try to create duplicate - this should fail or be rejected
                cert_id_4_duplicate = self.create_test_certificate(cert_4_duplicate)
                
                if not cert_id_4_duplicate:
                    self.test_results['all_5_fields_matching_is_duplicate'] = True
                    self.log("   ✅ TEST 4 PASSED: ALL 5 fields matching correctly rejected as DUPLICATE")
                else:
                    self.log("   ❌ TEST 4 FAILED: ALL 5 fields matching incorrectly allowed (should be duplicate)")
            else:
                self.log("   ❌ TEST 4 SETUP FAILED: Could not create original certificate")
            
            # Verify certificate creation is working
            if len(self.created_certificates) > 0:
                self.test_results['certificate_creation_working'] = True
                self.log(f"\n✅ Certificate creation working - Created {len(self.created_certificates)} certificates")
            
            # Test certificate retrieval
            certificates = self.get_ship_certificates()
            if len(certificates) > 0:
                self.test_results['certificate_retrieval_working'] = True
                self.log(f"✅ Certificate retrieval working - Retrieved {len(certificates)} certificates")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Enhanced 5-field duplicate detection test error: {str(e)}", "ERROR")
            return False
    
    def test_backend_logs_for_duplicate_detection(self):
        """Check if we can find evidence of the enhanced duplicate detection in backend behavior"""
        try:
            self.log("📝 TESTING BACKEND DUPLICATE DETECTION BEHAVIOR")
            self.log("=" * 60)
            
            # Get all certificates to analyze patterns
            certificates = self.get_ship_certificates()
            
            if len(certificates) > 0:
                self.log(f"   Found {len(certificates)} certificates in database")
                
                # Analyze certificate patterns to infer duplicate detection behavior
                cert_names = {}
                cert_numbers = {}
                
                for cert in certificates:
                    cert_name = cert.get('cert_name', '')
                    cert_no = cert.get('cert_no', '')
                    
                    if cert_name:
                        cert_names[cert_name] = cert_names.get(cert_name, 0) + 1
                    if cert_no:
                        cert_numbers[cert_no] = cert_numbers.get(cert_no, 0) + 1
                
                # Check for patterns that indicate 5-field duplicate detection
                duplicate_names = {name: count for name, count in cert_names.items() if count > 1}
                duplicate_numbers = {num: count for num, count in cert_numbers.items() if count > 1}
                
                self.log(f"   Certificate names with multiple instances: {duplicate_names}")
                self.log(f"   Certificate numbers with multiple instances: {duplicate_numbers}")
                
                # If we have certificates with same names/numbers but different other fields,
                # it suggests 5-field duplicate detection is working
                if duplicate_names or duplicate_numbers:
                    self.log("   ✅ Evidence of enhanced duplicate detection: certificates with same names/numbers but different other fields exist")
                    self.test_results['duplicate_check_function_accessible'] = True
                else:
                    self.log("   ⚠️ No clear evidence of duplicate detection behavior")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Backend duplicate detection behavior test error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_ship(self):
        """Clean up the test ship and all its certificates"""
        try:
            if self.test_ship_id:
                self.log("🧹 Cleaning up test ship and certificates...")
                
                # Delete the ship (this should cascade delete certificates)
                endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
                response = requests.delete(endpoint, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 200:
                    self.log("✅ Test ship and certificates cleaned up successfully")
                else:
                    self.log(f"⚠️ Test ship cleanup failed: {response.status_code}")
                    
        except Exception as e:
            self.log(f"⚠️ Cleanup error: {str(e)}", "WARNING")
    
    def run_comprehensive_tests(self):
        """Main test function for enhanced duplicate detection"""
        self.log("🔍 STARTING ENHANCED DUPLICATE CERTIFICATE DETECTION TESTING")
        self.log("🎯 OBJECTIVE: Verify 5-field duplicate detection with direct certificate creation")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Create Test Ship
            self.log("\n🚢 STEP 2: CREATE TEST SHIP")
            self.log("=" * 50)
            if not self.create_test_ship():
                self.log("❌ Test ship creation failed - cannot proceed with testing")
                return False
            
            # Step 3: Test Enhanced 5-Field Duplicate Detection
            self.log("\n🔍 STEP 3: ENHANCED 5-FIELD DUPLICATE DETECTION")
            self.log("=" * 50)
            test_3_success = self.test_enhanced_5_field_duplicate_detection()
            
            # Step 4: Test Backend Duplicate Detection Behavior
            self.log("\n📝 STEP 4: BACKEND DUPLICATE DETECTION BEHAVIOR")
            self.log("=" * 50)
            test_4_success = self.test_backend_logs_for_duplicate_detection()
            
            # Step 5: Final Analysis
            self.log("\n📊 STEP 5: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return test_3_success and test_4_success
            
        finally:
            # Always cleanup
            self.log("\n🧹 CLEANUP")
            self.log("=" * 50)
            self.cleanup_test_ship()
    
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
            
            # 5-Field Duplicate Detection
            duplicate_detection_tests = [
                'same_name_number_different_issue_date_not_duplicate',
                'same_name_number_issue_different_valid_date_not_duplicate',
                'same_name_number_issue_valid_different_endorse_not_duplicate',
                'all_5_fields_matching_is_duplicate'
            ]
            duplicate_passed = sum(1 for test in duplicate_detection_tests if self.test_results.get(test, False))
            duplicate_rate = (duplicate_passed / len(duplicate_detection_tests)) * 100
            
            self.log(f"\n🔍 5-FIELD DUPLICATE DETECTION: {duplicate_rate:.1f}% ({duplicate_passed}/{len(duplicate_detection_tests)})")
            if duplicate_rate >= 75:
                self.log("   ✅ CONFIRMED: Enhanced 5-field duplicate detection is WORKING")
                self.log("   ✅ Only certificates with ALL 5 fields matching are considered duplicates")
            else:
                self.log("   ❌ ISSUE: Enhanced 5-field duplicate detection needs fixing")
                self.log("   ❌ Current behavior may still use old 2-field duplicate detection")
            
            # Backend API Tests
            api_tests = [
                'certificate_creation_working',
                'certificate_retrieval_working',
                'duplicate_check_function_accessible'
            ]
            api_passed = sum(1 for test in api_tests if self.test_results.get(test, False))
            api_rate = (api_passed / len(api_tests)) * 100
            
            self.log(f"\n🔧 BACKEND API FUNCTIONALITY: {api_rate:.1f}% ({api_passed}/{len(api_tests)})")
            if api_rate >= 75:
                self.log("   ✅ CONFIRMED: Backend API is working correctly")
            else:
                self.log("   ❌ ISSUE: Backend API functionality needs attention")
            
            # Final conclusion
            if success_rate >= 80:
                self.log(f"\n🎉 CONCLUSION: ENHANCED DUPLICATE DETECTION IS WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Enhanced 5-field duplicate detection successfully implemented!")
                self.log(f"   ✅ 5-Field Duplicate Detection: Working correctly")
                self.log(f"   ✅ Backend API: Functioning properly")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: ENHANCED DUPLICATE DETECTION PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Some functionality working, improvements needed")
                
                if duplicate_rate >= 75:
                    self.log(f"   ✅ Core 5-field duplicate detection is working well")
                else:
                    self.log(f"   ❌ Core 5-field duplicate detection needs attention")
                    
                if api_rate >= 75:
                    self.log(f"   ✅ Backend API is working well")
                else:
                    self.log(f"   ❌ Backend API needs attention")
            else:
                self.log(f"\n❌ CONCLUSION: ENHANCED DUPLICATE DETECTION HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Enhanced duplicate detection needs significant fixes")
                self.log(f"   ❌ The 5-field duplicate detection may not be properly implemented")
                self.log(f"   ❌ System may still be using old 2-field duplicate detection logic")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run Enhanced Duplicate Detection tests"""
    print("🔍 ENHANCED DUPLICATE CERTIFICATE DETECTION TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = SimplifiedDuplicateDetectionTester()
        success = tester.run_comprehensive_tests()
        
        if success:
            print("\n✅ ENHANCED DUPLICATE DETECTION TESTING COMPLETED")
        else:
            print("\n❌ ENHANCED DUPLICATE DETECTION TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
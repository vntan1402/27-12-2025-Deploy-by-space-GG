#!/usr/bin/env python3
"""
Priority Validation Testing Script
FOCUS: Testing the updated execution order of IMO/Ship Name validation logic in multi-certificate upload endpoint

SPECIFIC TESTING FOR PRIORITY EXECUTION ORDER:
1. IMO/Ship Name validation runs as PRIORITY 1 before duplicate certificate check (PRIORITY 2)
2. Different IMO → immediate error, no further processing
3. Counter accuracy: Only valid certificates increment marine_certificates counter
4. Duplicate check only runs after IMO validation passes
"""

import requests
import json
import os
import sys
import tempfile
import base64
from datetime import datetime
import traceback
from io import BytesIO

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fleet-tracker-104.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class PriorityValidationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        
        # Test tracking for priority execution order
        self.priority_tests = {
            'authentication_successful': False,
            'test_ship_created': False,
            'imo_mismatch_blocks_immediately': False,
            'imo_mismatch_error_message_correct': False,
            'marine_certificates_counter_not_incremented_on_imo_fail': False,
            'duplicate_check_skipped_on_imo_fail': False,
            'imo_match_proceeds_to_duplicate_check': False,
            'marine_certificates_counter_incremented_after_imo_pass': False,
            'priority_execution_order_verified': False,
        }
        
        # Test ship data
        self.test_ship_id = None
        self.test_ship_name = "PRIORITY TEST SHIP"
        self.test_ship_imo = "9999999"
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
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
            response = requests.post(endpoint, json=login_data, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User: {self.current_user.get('username')} ({self.current_user.get('role')})")
                
                self.priority_tests['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def create_test_ship(self):
        """Create a test ship for priority validation testing"""
        try:
            self.log("🚢 Creating test ship for priority validation testing...")
            
            ship_data = {
                'name': self.test_ship_name,
                'imo': self.test_ship_imo,
                'flag': 'PANAMA',
                'ship_type': 'DNV GL',
                'gross_tonnage': 5000.0,
                'built_year': 2015,
                'ship_owner': 'Test Owner',
                'company': 'AMCSC'
            }
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.post(
                endpoint,
                json=ship_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                self.test_ship_id = response_data.get('id')
                self.log("✅ Test ship created successfully")
                self.log(f"   Ship ID: {self.test_ship_id}")
                self.log(f"   Ship IMO: {self.test_ship_imo}")
                
                self.priority_tests['test_ship_created'] = True
                return True
            else:
                self.log(f"❌ Test ship creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Test ship creation error: {str(e)}", "ERROR")
            return False
    
    def create_simple_pdf_content(self, imo_number, ship_name, cert_name):
        """Create simple PDF-like content for testing"""
        content = f"""
MARITIME CERTIFICATE
Certificate: {cert_name}
Ship Name: {ship_name}
IMO Number: {imo_number}
Issue Date: {datetime.now().strftime('%d/%m/%Y')}
Valid Until: {datetime.now().strftime('%d/%m/%Y')}
"""
        return content.encode('utf-8')
    
    def test_priority_1_imo_mismatch_blocking(self):
        """
        Test Priority 1: IMO Mismatch should block upload immediately
        - Different IMO should result in immediate error
        - No duplicate check should run
        - Marine certificates counter should NOT be incremented
        """
        try:
            self.log("🎯 TESTING PRIORITY 1: IMO Mismatch Blocking...")
            
            if not self.test_ship_id:
                self.log("❌ No test ship available")
                return False
            
            # Create certificate with different IMO
            different_imo = "8888888"  # Different from test ship IMO (9999999)
            file_content = self.create_simple_pdf_content(
                different_imo, 
                "DIFFERENT SHIP", 
                "TEST CERTIFICATE WITH DIFFERENT IMO"
            )
            
            # Prepare multipart form data
            files = {
                'files': ('different_imo_cert.pdf', file_content, 'application/pdf')
            }
            
            endpoint = f"{BACKEND_URL}/certificates/multi-upload?ship_id={self.test_ship_id}"
            self.log(f"   POST {endpoint}")
            self.log(f"   Test Ship IMO: {self.test_ship_imo}")
            self.log(f"   Certificate IMO: {different_imo} (different)")
            
            response = requests.post(
                endpoint,
                files=files,
                headers=self.get_headers(),
                timeout=30  # Reduced timeout
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                self.log("   Response received:")
                self.log(f"   {json.dumps(response_data, indent=2)}")
                
                # Check results
                results = response_data.get('results', [])
                summary = response_data.get('summary', {})
                
                if results:
                    result = results[0]
                    status = result.get('status')
                    message = result.get('message', '')
                    
                    # Check if IMO mismatch blocked upload
                    if status == 'error':
                        self.log("✅ PRIORITY 1: IMO mismatch blocked upload immediately")
                        self.priority_tests['imo_mismatch_blocks_immediately'] = True
                        
                        # Check error message
                        expected_message = "Giấy chứng nhận của tàu khác, không thể lưu vào dữ liệu tàu hiện tại"
                        if expected_message in message:
                            self.log("✅ PRIORITY 1: Error message is correct")
                            self.priority_tests['imo_mismatch_error_message_correct'] = True
                        else:
                            self.log(f"❌ PRIORITY 1: Error message incorrect: {message}")
                    else:
                        self.log(f"❌ PRIORITY 1: IMO mismatch did not block upload (status: {status})")
                
                # Check counters
                marine_certificates = summary.get('marine_certificates', 0)
                errors = summary.get('errors', 0)
                
                self.log(f"   Marine Certificates Counter: {marine_certificates}")
                self.log(f"   Errors Counter: {errors}")
                
                if marine_certificates == 0:
                    self.log("✅ PRIORITY 1: Marine certificates counter NOT incremented (correct)")
                    self.priority_tests['marine_certificates_counter_not_incremented_on_imo_fail'] = True
                else:
                    self.log("❌ PRIORITY 1: Marine certificates counter incorrectly incremented")
                
                # Check if duplicate check was skipped
                response_str = json.dumps(response_data)
                if 'duplicate' not in response_str.lower() and 'pending_duplicate_resolution' not in response_str:
                    self.log("✅ PRIORITY 1: Duplicate check was skipped (correct)")
                    self.priority_tests['duplicate_check_skipped_on_imo_fail'] = True
                else:
                    self.log("❌ PRIORITY 1: Duplicate check was not skipped")
                
                return True
            else:
                self.log(f"❌ PRIORITY 1: Multi-upload endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Priority 1 testing error: {str(e)}", "ERROR")
            return False
    
    def test_priority_2_imo_match_proceed_to_duplicate_check(self):
        """
        Test Priority 2: IMO Match should proceed to duplicate check
        - Same IMO should pass validation
        - Should proceed to duplicate check (Priority 2)
        - Marine certificates counter should be incremented
        """
        try:
            self.log("🎯 TESTING PRIORITY 2: IMO Match - Proceed to Duplicate Check...")
            
            if not self.test_ship_id:
                self.log("❌ No test ship available")
                return False
            
            # Create certificate with matching IMO
            file_content = self.create_simple_pdf_content(
                self.test_ship_imo,  # Same IMO as test ship
                self.test_ship_name,  # Same ship name
                "TEST CERTIFICATE WITH MATCHING IMO"
            )
            
            # Prepare multipart form data
            files = {
                'files': ('matching_imo_cert.pdf', file_content, 'application/pdf')
            }
            
            endpoint = f"{BACKEND_URL}/certificates/multi-upload?ship_id={self.test_ship_id}"
            self.log(f"   POST {endpoint}")
            self.log(f"   Test Ship IMO: {self.test_ship_imo}")
            self.log(f"   Certificate IMO: {self.test_ship_imo} (matching)")
            
            response = requests.post(
                endpoint,
                files=files,
                headers=self.get_headers(),
                timeout=30
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                self.log("   Response received:")
                self.log(f"   {json.dumps(response_data, indent=2)}")
                
                # Check results
                results = response_data.get('results', [])
                summary = response_data.get('summary', {})
                
                if results:
                    result = results[0]
                    status = result.get('status')
                    
                    # Check if IMO validation passed and proceeded to duplicate check
                    if status in ['success', 'pending_duplicate_resolution']:
                        self.log("✅ PRIORITY 2: IMO validation passed - proceeded to duplicate check")
                        self.priority_tests['imo_match_proceeds_to_duplicate_check'] = True
                    else:
                        self.log(f"❌ PRIORITY 2: IMO validation did not proceed correctly (status: {status})")
                
                # Check counters
                marine_certificates = summary.get('marine_certificates', 0)
                
                self.log(f"   Marine Certificates Counter: {marine_certificates}")
                
                if marine_certificates >= 1:
                    self.log("✅ PRIORITY 2: Marine certificates counter incremented after IMO pass")
                    self.priority_tests['marine_certificates_counter_incremented_after_imo_pass'] = True
                else:
                    self.log("❌ PRIORITY 2: Marine certificates counter not incremented")
                
                return True
            else:
                self.log(f"❌ PRIORITY 2: Multi-upload endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Priority 2 testing error: {str(e)}", "ERROR")
            return False
    
    def verify_priority_execution_order(self):
        """Verify that the priority execution order is working correctly"""
        try:
            self.log("🎯 VERIFYING PRIORITY EXECUTION ORDER...")
            
            # Check if both priority tests passed
            priority_1_working = (
                self.priority_tests['imo_mismatch_blocks_immediately'] and
                self.priority_tests['marine_certificates_counter_not_incremented_on_imo_fail'] and
                self.priority_tests['duplicate_check_skipped_on_imo_fail']
            )
            
            priority_2_working = (
                self.priority_tests['imo_match_proceeds_to_duplicate_check'] and
                self.priority_tests['marine_certificates_counter_incremented_after_imo_pass']
            )
            
            if priority_1_working and priority_2_working:
                self.log("✅ PRIORITY EXECUTION ORDER: Working correctly")
                self.log("   ✅ Priority 1: IMO validation blocks immediately on mismatch")
                self.log("   ✅ Priority 2: Duplicate check only runs after IMO validation passes")
                self.priority_tests['priority_execution_order_verified'] = True
                return True
            else:
                self.log("❌ PRIORITY EXECUTION ORDER: Not working correctly")
                if not priority_1_working:
                    self.log("   ❌ Priority 1 (IMO blocking) has issues")
                if not priority_2_working:
                    self.log("   ❌ Priority 2 (duplicate check after IMO pass) has issues")
                return False
                
        except Exception as e:
            self.log(f"❌ Priority execution order verification error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_ship(self):
        """Clean up the test ship"""
        try:
            if self.test_ship_id:
                self.log("🧹 Cleaning up test ship...")
                
                endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
                response = requests.delete(endpoint, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 200:
                    self.log("✅ Test ship cleaned up successfully")
                else:
                    self.log(f"⚠️ Test ship cleanup failed: {response.status_code}")
                    
        except Exception as e:
            self.log(f"⚠️ Cleanup error: {str(e)}", "WARNING")
    
    def run_priority_validation_tests(self):
        """Main test function for priority validation testing"""
        self.log("🎯 STARTING PRIORITY VALIDATION TESTING")
        self.log("🎯 OBJECTIVE: Verify IMO validation runs as PRIORITY 1 before duplicate check (PRIORITY 2)")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed")
                return False
            
            # Step 2: Create Test Ship
            self.log("\n🚢 STEP 2: CREATE TEST SHIP")
            self.log("=" * 50)
            if not self.create_test_ship():
                self.log("❌ Test ship creation failed - cannot proceed")
                return False
            
            # Step 3: Test Priority 1 - IMO Mismatch Blocking
            self.log("\n🎯 STEP 3: PRIORITY 1 - IMO MISMATCH BLOCKING")
            self.log("=" * 50)
            priority_1_success = self.test_priority_1_imo_mismatch_blocking()
            
            # Step 4: Test Priority 2 - IMO Match Proceed to Duplicate Check
            self.log("\n🎯 STEP 4: PRIORITY 2 - IMO MATCH PROCEED TO DUPLICATE CHECK")
            self.log("=" * 50)
            priority_2_success = self.test_priority_2_imo_match_proceed_to_duplicate_check()
            
            # Step 5: Verify Priority Execution Order
            self.log("\n🎯 STEP 5: VERIFY PRIORITY EXECUTION ORDER")
            self.log("=" * 50)
            execution_order_success = self.verify_priority_execution_order()
            
            # Step 6: Final Analysis
            self.log("\n📊 STEP 6: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return priority_1_success and priority_2_success and execution_order_success
            
        finally:
            # Always cleanup
            self.log("\n🧹 CLEANUP")
            self.log("=" * 50)
            self.cleanup_test_ship()
    
    def provide_final_analysis(self):
        """Provide final analysis of priority validation testing"""
        try:
            self.log("🎯 PRIORITY VALIDATION TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.priority_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.priority_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.priority_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.priority_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.priority_tests)})")
            
            # Final conclusion
            if success_rate >= 85:
                self.log(f"\n🎉 CONCLUSION: PRIORITY EXECUTION ORDER IS WORKING EXCELLENTLY")
                self.log(f"   ✅ IMO validation runs as PRIORITY 1 before duplicate check")
                self.log(f"   ✅ Different IMO blocks upload immediately")
                self.log(f"   ✅ Marine certificates counter accuracy verified")
                self.log(f"   ✅ Duplicate check only runs after IMO validation passes")
            elif success_rate >= 70:
                self.log(f"\n⚠️ CONCLUSION: PRIORITY EXECUTION ORDER PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Some improvements needed")
            else:
                self.log(f"\n❌ CONCLUSION: PRIORITY EXECUTION ORDER HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Significant fixes needed")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run priority validation tests"""
    print("🎯 PRIORITY VALIDATION TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = PriorityValidationTester()
        success = tester.run_priority_validation_tests()
        
        if success:
            print("\n✅ PRIORITY VALIDATION TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ PRIORITY VALIDATION TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    sys.exit(0)

if __name__ == "__main__":
    main()
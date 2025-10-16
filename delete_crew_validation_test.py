#!/usr/bin/env python3
"""
DELETE Crew Validation Logic Testing

REVIEW REQUEST REQUIREMENTS:
Test the new DELETE crew validation logic:

**Test Cases:**

1. **Test DELETE crew with certificates (should BLOCK)**
   - Find a crew member who has certificates
   - Try to DELETE /api/crew/{crew_id}
   - Verify response:
     * Status: 400 Bad Request
     * Response body contains:
       - error: "CREW_HAS_CERTIFICATES"
       - message with crew name and instruction to delete certificates first
       - crew_name
       - certificate_count
   - Verify crew is NOT deleted from database

2. **Test DELETE crew without certificates (should ALLOW)**
   - Find or create a crew member with NO certificates
   - Try to DELETE /api/crew/{crew_id}
   - Verify response:
     * Status: 200 OK
     * Success message
   - Verify crew IS deleted from database

**Database Collections:**
- crew_members
- crew_certificates

**Important:**
- Use existing company_id: cd1951d0-223e-4a09-865b-593047ed8c2d
- Check certificates by crew_id in crew_certificates collection
- Validate error message format matches Vietnamese requirement
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
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class DeleteCrewValidationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.company_id = "cd1951d0-223e-4a09-865b-593047ed8c2d"
        
        # Test tracking
        self.test_results = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_verified': False,
            
            # Test Case 1: DELETE crew with certificates (should BLOCK)
            'crew_with_certificates_found': False,
            'delete_crew_with_certs_blocked': False,
            'error_status_400_returned': False,
            'error_code_crew_has_certificates': False,
            'vietnamese_error_message_present': False,
            'crew_name_in_response': False,
            'certificate_count_in_response': False,
            'crew_not_deleted_from_database': False,
            
            # Test Case 2: DELETE crew without certificates (should ALLOW)
            'crew_without_certificates_found': False,
            'delete_crew_without_certs_allowed': False,
            'success_status_200_returned': False,
            'success_message_present': False,
            'crew_deleted_from_database': False,
            
            # Additional validation
            'validation_logic_working_correctly': False,
            'database_integrity_maintained': False,
        }
        
        # Store test data
        self.crew_with_certs = None
        self.crew_without_certs = None
        self.created_test_crew_id = None
        
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
                
                self.test_results['authentication_successful'] = True
                
                # Verify company ID matches expected
                user_company = self.current_user.get('company')
                if user_company == 'AMCSC':  # This should resolve to our target company_id
                    self.test_results['user_company_verified'] = True
                    self.log(f"✅ User company verified: {user_company}")
                
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_crew_with_certificates(self):
        """Find a crew member who has certificates"""
        try:
            self.log("🔍 Finding crew member with certificates...")
            
            # Get all crew members
            response = self.session.get(f"{BACKEND_URL}/crew")
            
            if response.status_code == 200:
                crew_list = response.json()
                self.log(f"   Found {len(crew_list)} total crew members")
                
                # Check each crew member for certificates
                for crew in crew_list:
                    crew_id = crew.get("id")
                    crew_name = crew.get("full_name")
                    
                    # Check if this crew has certificates
                    cert_response = self.session.get(f"{BACKEND_URL}/crew-certificates/7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7?crew_id={crew_id}")
                    
                    if cert_response.status_code == 200:
                        certificates = cert_response.json()
                        if certificates and len(certificates) > 0:
                            self.crew_with_certs = {
                                'id': crew_id,
                                'name': crew_name,
                                'certificate_count': len(certificates)
                            }
                            self.log(f"✅ Found crew with certificates: {crew_name}")
                            self.log(f"   Crew ID: {crew_id}")
                            self.log(f"   Certificate count: {len(certificates)}")
                            self.test_results['crew_with_certificates_found'] = True
                            return True
                
                self.log("❌ No crew members with certificates found", "WARNING")
                return False
            else:
                self.log(f"❌ Failed to get crew list: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding crew with certificates: {str(e)}", "ERROR")
            return False
    
    def find_crew_without_certificates(self):
        """Find or create a crew member without certificates"""
        try:
            self.log("🔍 Finding crew member without certificates...")
            
            # Get all crew members
            response = self.session.get(f"{BACKEND_URL}/crew")
            
            if response.status_code == 200:
                crew_list = response.json()
                
                # Check each crew member for certificates
                for crew in crew_list:
                    crew_id = crew.get("id")
                    crew_name = crew.get("full_name")
                    
                    # Check if this crew has certificates
                    cert_response = self.session.get(f"{BACKEND_URL}/crew-certificates/7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7?crew_id={crew_id}")
                    
                    if cert_response.status_code == 200:
                        certificates = cert_response.json()
                        if not certificates or len(certificates) == 0:
                            self.crew_without_certs = {
                                'id': crew_id,
                                'name': crew_name
                            }
                            self.log(f"✅ Found crew without certificates: {crew_name}")
                            self.log(f"   Crew ID: {crew_id}")
                            self.test_results['crew_without_certificates_found'] = True
                            return True
                
                # If no crew without certificates found, create one
                self.log("   No existing crew without certificates found, creating test crew...")
                return self.create_test_crew_without_certificates()
            else:
                self.log(f"❌ Failed to get crew list: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding crew without certificates: {str(e)}", "ERROR")
            return False
    
    def create_test_crew_without_certificates(self):
        """Create a test crew member without certificates"""
        try:
            self.log("👤 Creating test crew member without certificates...")
            
            test_crew_data = {
                "full_name": "TEST DELETE CREW VALIDATION",
                "sex": "M",
                "date_of_birth": "1990-01-01T00:00:00Z",
                "place_of_birth": "TEST CITY",
                "passport": f"TESTDEL{int(time.time())}",  # Unique passport number
                "nationality": "VIETNAMESE",
                "rank": "Test Officer",
                "status": "Standby",
                "ship_sign_on": "-"
            }
            
            endpoint = f"{BACKEND_URL}/crew"
            response = self.session.post(endpoint, json=test_crew_data, timeout=30)
            
            if response.status_code in [200, 201]:
                crew_data = response.json()
                crew_id = crew_data.get('id')
                crew_name = crew_data.get('full_name')
                
                self.crew_without_certs = {
                    'id': crew_id,
                    'name': crew_name
                }
                self.created_test_crew_id = crew_id
                
                self.log(f"✅ Created test crew: {crew_name}")
                self.log(f"   Crew ID: {crew_id}")
                self.test_results['crew_without_certificates_found'] = True
                return True
            else:
                self.log(f"❌ Failed to create test crew: {response.status_code}", "ERROR")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating test crew: {str(e)}", "ERROR")
            return False
    
    def test_delete_crew_with_certificates(self):
        """Test Case 1: DELETE crew with certificates (should BLOCK)"""
        try:
            self.log("🚫 TEST CASE 1: DELETE crew with certificates (should BLOCK)")
            
            if not self.crew_with_certs:
                self.log("❌ No crew with certificates available for testing", "ERROR")
                return False
            
            crew_id = self.crew_with_certs['id']
            crew_name = self.crew_with_certs['name']
            expected_cert_count = self.crew_with_certs['certificate_count']
            
            self.log(f"   Testing DELETE on crew: {crew_name} (ID: {crew_id})")
            self.log(f"   Expected certificate count: {expected_cert_count}")
            
            # Verify crew exists before deletion attempt
            pre_delete_response = self.session.get(f"{BACKEND_URL}/crew/{crew_id}")
            if pre_delete_response.status_code != 200:
                self.log("❌ Crew not found before deletion test", "ERROR")
                return False
            
            # Attempt to delete crew with certificates
            endpoint = f"{BACKEND_URL}/crew/{crew_id}"
            self.log(f"   DELETE {endpoint}")
            
            response = self.session.delete(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            # Should return 400 Bad Request
            if response.status_code == 400:
                self.log("✅ DELETE blocked with 400 status as expected")
                self.test_results['delete_crew_with_certs_blocked'] = True
                self.test_results['error_status_400_returned'] = True
                
                try:
                    error_data = response.json()
                    self.log(f"   Response body: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                    
                    # Check for required error structure
                    detail = error_data.get("detail", {})
                    if isinstance(detail, dict):
                        # Check error code
                        error_code = detail.get("error")
                        if error_code == "CREW_HAS_CERTIFICATES":
                            self.log("✅ Error code 'CREW_HAS_CERTIFICATES' present")
                            self.test_results['error_code_crew_has_certificates'] = True
                        
                        # Check Vietnamese error message
                        message = detail.get("message", "")
                        if "Thuyền viên" in message and "chứng chỉ" in message:
                            self.log("✅ Vietnamese error message present")
                            self.test_results['vietnamese_error_message_present'] = True
                        
                        # Check crew name in response
                        response_crew_name = detail.get("crew_name")
                        if response_crew_name == crew_name:
                            self.log("✅ Crew name correctly included in response")
                            self.test_results['crew_name_in_response'] = True
                        
                        # Check certificate count in response
                        response_cert_count = detail.get("certificate_count")
                        if response_cert_count == expected_cert_count:
                            self.log("✅ Certificate count correctly included in response")
                            self.test_results['certificate_count_in_response'] = True
                    
                except json.JSONDecodeError:
                    self.log("❌ Could not parse error response as JSON", "ERROR")
                
                # Verify crew still exists in database (not deleted)
                post_delete_response = self.session.get(f"{BACKEND_URL}/crew/{crew_id}")
                if post_delete_response.status_code == 200:
                    self.log("✅ Crew still exists in database (not deleted)")
                    self.test_results['crew_not_deleted_from_database'] = True
                else:
                    self.log("❌ Crew was deleted from database (should not happen)", "ERROR")
                
                return True
            else:
                self.log(f"❌ Expected 400 status, got {response.status_code}", "ERROR")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing delete crew with certificates: {str(e)}", "ERROR")
            return False
    
    def test_delete_crew_without_certificates(self):
        """Test Case 2: DELETE crew without certificates (should ALLOW)"""
        try:
            self.log("✅ TEST CASE 2: DELETE crew without certificates (should ALLOW)")
            
            if not self.crew_without_certs:
                self.log("❌ No crew without certificates available for testing", "ERROR")
                return False
            
            crew_id = self.crew_without_certs['id']
            crew_name = self.crew_without_certs['name']
            
            self.log(f"   Testing DELETE on crew: {crew_name} (ID: {crew_id})")
            
            # Verify crew exists before deletion attempt
            pre_delete_response = self.session.get(f"{BACKEND_URL}/crew/{crew_id}")
            if pre_delete_response.status_code != 200:
                self.log("❌ Crew not found before deletion test", "ERROR")
                return False
            
            # Verify crew has no certificates
            cert_response = self.session.get(f"{BACKEND_URL}/crew-certificates?crew_id={crew_id}")
            if cert_response.status_code == 200:
                certificates = cert_response.json()
                if certificates and len(certificates) > 0:
                    self.log(f"❌ Crew has {len(certificates)} certificates, cannot use for test", "ERROR")
                    return False
                else:
                    self.log("✅ Confirmed crew has no certificates")
            
            # Attempt to delete crew without certificates
            endpoint = f"{BACKEND_URL}/crew/{crew_id}"
            self.log(f"   DELETE {endpoint}")
            
            response = self.session.delete(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            # Should return 200 OK
            if response.status_code == 200:
                self.log("✅ DELETE allowed with 200 status as expected")
                self.test_results['delete_crew_without_certs_allowed'] = True
                self.test_results['success_status_200_returned'] = True
                
                try:
                    success_data = response.json()
                    self.log(f"   Response body: {json.dumps(success_data, indent=2, ensure_ascii=False)}")
                    
                    # Check for success message
                    success = success_data.get("success")
                    message = success_data.get("message", "")
                    
                    if success and "deleted successfully" in message:
                        self.log("✅ Success message present")
                        self.test_results['success_message_present'] = True
                    
                except json.JSONDecodeError:
                    self.log("❌ Could not parse success response as JSON", "ERROR")
                
                # Verify crew is deleted from database
                post_delete_response = self.session.get(f"{BACKEND_URL}/crew/{crew_id}")
                if post_delete_response.status_code == 404:
                    self.log("✅ Crew successfully deleted from database")
                    self.test_results['crew_deleted_from_database'] = True
                    
                    # Clear the created test crew ID since it's deleted
                    if self.created_test_crew_id == crew_id:
                        self.created_test_crew_id = None
                else:
                    self.log("❌ Crew still exists in database (should be deleted)", "ERROR")
                
                return True
            else:
                self.log(f"❌ Expected 200 status, got {response.status_code}", "ERROR")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing delete crew without certificates: {str(e)}", "ERROR")
            return False
    
    def validate_overall_logic(self):
        """Validate that the overall validation logic is working correctly"""
        try:
            self.log("🔍 Validating overall DELETE crew validation logic...")
            
            # Check if both test cases passed
            test1_passed = (
                self.test_results['delete_crew_with_certs_blocked'] and
                self.test_results['error_status_400_returned'] and
                self.test_results['crew_not_deleted_from_database']
            )
            
            test2_passed = (
                self.test_results['delete_crew_without_certs_allowed'] and
                self.test_results['success_status_200_returned'] and
                self.test_results['crew_deleted_from_database']
            )
            
            if test1_passed and test2_passed:
                self.log("✅ Validation logic working correctly")
                self.test_results['validation_logic_working_correctly'] = True
                
                # Check database integrity
                if (self.test_results['crew_not_deleted_from_database'] and 
                    self.test_results['crew_deleted_from_database']):
                    self.log("✅ Database integrity maintained")
                    self.test_results['database_integrity_maintained'] = True
                
                return True
            else:
                self.log("❌ Validation logic has issues", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error validating overall logic: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up any created test data"""
        try:
            if self.created_test_crew_id:
                self.log("🧹 Cleaning up created test crew...")
                
                # Try to delete the test crew (it might already be deleted by the test)
                endpoint = f"{BACKEND_URL}/crew/{self.created_test_crew_id}"
                response = self.session.delete(endpoint, timeout=30)
                
                if response.status_code in [200, 404]:
                    self.log("✅ Test crew cleanup completed")
                else:
                    self.log(f"⚠️ Test crew cleanup failed: {response.status_code}")
                
                self.created_test_crew_id = None
                
        except Exception as e:
            self.log(f"⚠️ Error during cleanup: {str(e)}", "WARNING")
    
    def run_comprehensive_test(self):
        """Run comprehensive DELETE crew validation test"""
        try:
            self.log("🚀 STARTING DELETE CREW VALIDATION LOGIC TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find crew with certificates
            self.log("\nSTEP 2: Finding crew with certificates")
            if not self.find_crew_with_certificates():
                self.log("⚠️ WARNING: No crew with certificates found - Test Case 1 will be skipped")
            
            # Step 3: Find crew without certificates
            self.log("\nSTEP 3: Finding crew without certificates")
            if not self.find_crew_without_certificates():
                self.log("❌ CRITICAL: Cannot find or create crew without certificates")
                return False
            
            # Step 4: Test Case 1 - DELETE crew with certificates (should BLOCK)
            if self.crew_with_certs:
                self.log("\nSTEP 4: Test Case 1 - DELETE crew with certificates")
                self.test_delete_crew_with_certificates()
            else:
                self.log("\nSTEP 4: SKIPPED - No crew with certificates available")
            
            # Step 5: Test Case 2 - DELETE crew without certificates (should ALLOW)
            self.log("\nSTEP 5: Test Case 2 - DELETE crew without certificates")
            self.test_delete_crew_without_certificates()
            
            # Step 6: Validate overall logic
            self.log("\nSTEP 6: Validate overall logic")
            self.validate_overall_logic()
            
            # Step 7: Cleanup
            self.log("\nSTEP 7: Cleanup")
            self.cleanup_test_data()
            
            self.log("\n" + "=" * 80)
            self.log("✅ DELETE CREW VALIDATION TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 DELETE CREW VALIDATION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_verified', 'User company verified'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Case 1 Results
            self.log("\n🚫 TEST CASE 1: DELETE crew with certificates (should BLOCK):")
            test1_tests = [
                ('crew_with_certificates_found', 'Crew with certificates found'),
                ('delete_crew_with_certs_blocked', 'DELETE request blocked'),
                ('error_status_400_returned', '400 Bad Request status returned'),
                ('error_code_crew_has_certificates', 'Error code CREW_HAS_CERTIFICATES'),
                ('vietnamese_error_message_present', 'Vietnamese error message present'),
                ('crew_name_in_response', 'Crew name in response'),
                ('certificate_count_in_response', 'Certificate count in response'),
                ('crew_not_deleted_from_database', 'Crew NOT deleted from database'),
            ]
            
            for test_key, description in test1_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Case 2 Results
            self.log("\n✅ TEST CASE 2: DELETE crew without certificates (should ALLOW):")
            test2_tests = [
                ('crew_without_certificates_found', 'Crew without certificates found'),
                ('delete_crew_without_certs_allowed', 'DELETE request allowed'),
                ('success_status_200_returned', '200 OK status returned'),
                ('success_message_present', 'Success message present'),
                ('crew_deleted_from_database', 'Crew deleted from database'),
            ]
            
            for test_key, description in test2_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Validation Results
            self.log("\n🔍 OVERALL VALIDATION:")
            validation_tests = [
                ('validation_logic_working_correctly', 'Validation logic working correctly'),
                ('database_integrity_maintained', 'Database integrity maintained'),
            ]
            
            for test_key, description in validation_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'delete_crew_with_certs_blocked',
                'error_status_400_returned',
                'crew_not_deleted_from_database',
                'delete_crew_without_certs_allowed',
                'success_status_200_returned',
                'crew_deleted_from_database'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.test_results.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL VALIDATION REQUIREMENTS MET")
                self.log("   ✅ DELETE crew validation logic working correctly")
                self.log("   ✅ Crew with certificates properly blocked from deletion")
                self.log("   ✅ Crew without certificates properly allowed for deletion")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Specific validation details
            if self.crew_with_certs:
                self.log(f"\n📋 TEST DETAILS:")
                self.log(f"   Crew with certificates: {self.crew_with_certs['name']} ({self.crew_with_certs['certificate_count']} certs)")
            
            if self.crew_without_certs:
                self.log(f"   Crew without certificates: {self.crew_without_certs['name']}")
            
            if success_rate >= 90:
                self.log(f"\n   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 75:
                self.log(f"\n   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"\n   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the DELETE crew validation test"""
    tester = DeleteCrewValidationTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Return appropriate exit code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        tester.cleanup_test_data()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        traceback.print_exc()
        tester.cleanup_test_data()
        sys.exit(1)

if __name__ == "__main__":
    main()
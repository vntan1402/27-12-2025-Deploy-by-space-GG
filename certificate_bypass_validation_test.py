#!/usr/bin/env python3
"""
Certificate Holder Mismatch Modal with Bypass Validation Testing

REVIEW REQUEST REQUIREMENTS:
Test the new bypass_validation parameter in the /api/crew-certificates/analyze-file endpoint.

TEST CASES:
1. Normal Flow (bypass_validation = "false" or not provided)
   - Upload certificate with holder name mismatch
   - Verify 400 status with CERTIFICATE_HOLDER_MISMATCH error
   - Verify error response includes: error, message, holder_name, crew_name, crew_name_en

2. Bypass Flow (bypass_validation = "true")
   - Upload same certificate with bypass_validation="true"
   - Verify 200 status (success)
   - Verify analysis data returned correctly
   - Verify backend logs show bypass warning

3. Edge Cases
   - Test different values: "True", "TRUE", "false", "False", "FALSE"
   - Test with valid certificate (holder matches crew) - should work with both bypass values

ENDPOINT: /api/crew-certificates/analyze-file
METHOD: POST
CONTENT-TYPE: multipart/form-data
PARAMETERS:
- cert_file (file): Certificate file (PDF or image)
- ship_id (string): Valid ship ID
- crew_id (string, optional): Valid crew ID
- bypass_validation (string, default "false"): Bypass validation flag

AUTHENTICATION: admin1/123456
TEST SHIP: BROTHER 36
"""

import requests
import json
import os
import sys
import tempfile
import time
from datetime import datetime
import traceback
from io import BytesIO

# Configuration
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL from environment
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                external_url = line.split('=', 1)[1].strip()
                BACKEND_URL = external_url + '/api'
                print(f"Using external backend URL: {BACKEND_URL}")
                break

class CertificateBypassValidationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.ship_id = None
        self.crew_id = None
        self.test_results = {}
        
        # Test tracking
        self.bypass_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'ship_discovery_successful': False,
            'crew_discovery_successful': False,
            
            # Test Case 1: Normal Flow (bypass_validation = "false")
            'normal_flow_mismatch_returns_400': False,
            'normal_flow_error_structure_correct': False,
            'normal_flow_error_fields_present': False,
            'normal_flow_vietnamese_message': False,
            
            # Test Case 2: Bypass Flow (bypass_validation = "true")
            'bypass_flow_returns_200': False,
            'bypass_flow_analysis_data_returned': False,
            'bypass_flow_backend_logs_warning': False,
            'bypass_flow_success_response': False,
            
            # Test Case 3: Edge Cases
            'edge_case_true_uppercase': False,
            'edge_case_false_uppercase': False,
            'edge_case_mixed_case': False,
            'edge_case_valid_certificate_both_values': False,
            
            # Backend verification
            'endpoint_accessible': False,
            'multipart_form_data_accepted': False,
            'validation_logic_working': False,
            'bypass_parameter_processed': False,
        }
        
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
            response = requests.post(endpoint, json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                # Set authorization header
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User: {self.current_user.get('username')}")
                self.log(f"   Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.bypass_tests['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_test_ship(self):
        """Find BROTHER 36 ship for testing"""
        try:
            self.log("🚢 Finding BROTHER 36 ship...")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                for ship in ships:
                    if ship.get("name") == "BROTHER 36":
                        self.ship_id = ship.get("id")
                        self.log(f"✅ Found BROTHER 36 ship (ID: {self.ship_id})")
                        self.bypass_tests['ship_discovery_successful'] = True
                        return True
                
                self.log("❌ BROTHER 36 ship not found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def find_test_crew(self):
        """Find a crew member for testing"""
        try:
            self.log("👤 Finding crew member for testing...")
            
            # Get crew list for BROTHER 36
            response = self.session.get(f"{BACKEND_URL}/crew?ship_name=BROTHER 36")
            
            if response.status_code == 200:
                crew_list = response.json()
                if crew_list:
                    # Use first crew member
                    crew = crew_list[0]
                    self.crew_id = crew.get("id")
                    crew_name = crew.get("full_name")
                    self.log(f"✅ Found test crew: {crew_name} (ID: {self.crew_id})")
                    self.bypass_tests['crew_discovery_successful'] = True
                    return True
                else:
                    self.log("❌ No crew members found for BROTHER 36", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get crew list: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding crew: {str(e)}", "ERROR")
            return False
    
    def create_test_certificate_file(self, holder_name="DIFFERENT PERSON"):
        """Create a test certificate file with specific holder name"""
        try:
            # Create a simple PDF-like content for testing
            # This is a minimal PDF structure that should be processable
            pdf_content = f"""%PDF-1.4
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
/Length 100
>>
stream
BT
/F1 12 Tf
100 700 Td
(Certificate Holder: {holder_name}) Tj
100 680 Td
(Certificate Type: GMDSS Certificate) Tj
100 660 Td
(Certificate Number: TEST-CERT-001) Tj
100 640 Td
(Issue Date: 01/01/2024) Tj
100 620 Td
(Expiry Date: 01/01/2026) Tj
ET
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
400
%%EOF"""
            
            return pdf_content.encode('utf-8')
            
        except Exception as e:
            self.log(f"❌ Error creating test certificate: {str(e)}", "ERROR")
            return None
    
    def test_normal_flow_bypass_false(self):
        """Test Case 1: Normal Flow (bypass_validation = "false" or not provided)"""
        try:
            self.log("📋 TEST CASE 1: Normal Flow (bypass_validation = false)")
            self.log("   Testing certificate with holder name mismatch...")
            
            # Create test certificate with different holder name
            cert_content = self.create_test_certificate_file("DIFFERENT PERSON NAME")
            if not cert_content:
                return False
            
            # Test without bypass_validation parameter (default behavior)
            self.log("   Subtest 1a: No bypass_validation parameter (default)")
            success_1a = self._test_analyze_certificate(
                cert_content, 
                bypass_validation=None,
                expected_status=400,
                test_name="normal_flow_default"
            )
            
            # Test with bypass_validation = "false"
            self.log("   Subtest 1b: bypass_validation = 'false'")
            success_1b = self._test_analyze_certificate(
                cert_content,
                bypass_validation="false", 
                expected_status=400,
                test_name="normal_flow_false"
            )
            
            if success_1a and success_1b:
                self.bypass_tests['normal_flow_mismatch_returns_400'] = True
                self.log("✅ Normal flow test passed - returns 400 for mismatch")
                return True
            else:
                self.log("❌ Normal flow test failed", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in normal flow test: {str(e)}", "ERROR")
            return False
    
    def test_bypass_flow_bypass_true(self):
        """Test Case 2: Bypass Flow (bypass_validation = "true")"""
        try:
            self.log("📋 TEST CASE 2: Bypass Flow (bypass_validation = true)")
            self.log("   Testing same certificate with bypass enabled...")
            
            # Create test certificate with different holder name
            cert_content = self.create_test_certificate_file("DIFFERENT PERSON NAME")
            if not cert_content:
                return False
            
            # Test with bypass_validation = "true"
            success = self._test_analyze_certificate(
                cert_content,
                bypass_validation="true",
                expected_status=200,
                test_name="bypass_flow_true"
            )
            
            if success:
                self.bypass_tests['bypass_flow_returns_200'] = True
                self.log("✅ Bypass flow test passed - returns 200 with bypass")
                return True
            else:
                self.log("❌ Bypass flow test failed", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in bypass flow test: {str(e)}", "ERROR")
            return False
    
    def test_edge_cases(self):
        """Test Case 3: Edge Cases - different bypass_validation values"""
        try:
            self.log("📋 TEST CASE 3: Edge Cases - Different bypass_validation values")
            
            cert_content = self.create_test_certificate_file("DIFFERENT PERSON NAME")
            if not cert_content:
                return False
            
            # Test different case variations
            test_cases = [
                ("True", 200, "edge_case_true_uppercase"),
                ("TRUE", 200, "edge_case_true_uppercase"), 
                ("false", 400, "edge_case_false_lowercase"),
                ("False", 400, "edge_case_false_uppercase"),
                ("FALSE", 400, "edge_case_false_uppercase"),
            ]
            
            all_passed = True
            
            for bypass_value, expected_status, test_key in test_cases:
                self.log(f"   Testing bypass_validation = '{bypass_value}'")
                success = self._test_analyze_certificate(
                    cert_content,
                    bypass_validation=bypass_value,
                    expected_status=expected_status,
                    test_name=f"edge_case_{bypass_value}"
                )
                
                if success:
                    self.bypass_tests[test_key] = True
                    self.log(f"   ✅ {bypass_value} test passed")
                else:
                    self.log(f"   ❌ {bypass_value} test failed")
                    all_passed = False
            
            return all_passed
                
        except Exception as e:
            self.log(f"❌ Error in edge cases test: {str(e)}", "ERROR")
            return False
    
    def _test_analyze_certificate(self, cert_content, bypass_validation=None, expected_status=200, test_name=""):
        """Helper method to test certificate analysis with different parameters"""
        try:
            endpoint = f"{BACKEND_URL}/crew-certificates/analyze-file"
            
            # Prepare multipart form data
            files = {
                'cert_file': ('test_certificate.pdf', BytesIO(cert_content), 'application/pdf')
            }
            
            data = {
                'ship_id': self.ship_id,
                'crew_id': self.crew_id
            }
            
            # Add bypass_validation parameter if specified
            if bypass_validation is not None:
                data['bypass_validation'] = bypass_validation
            
            self.log(f"   POST {endpoint}")
            self.log(f"   Parameters: ship_id={self.ship_id}, crew_id={self.crew_id}")
            if bypass_validation is not None:
                self.log(f"   bypass_validation={bypass_validation}")
            
            # Make request
            start_time = time.time()
            response = self.session.post(
                endpoint,
                files=files,
                data=data,
                timeout=120
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"   ⏱️ Processing time: {processing_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            # Mark endpoint as accessible
            if response.status_code in [200, 400]:
                self.bypass_tests['endpoint_accessible'] = True
                self.bypass_tests['multipart_form_data_accepted'] = True
            
            # Check if status matches expected
            if response.status_code == expected_status:
                self.log(f"   ✅ Expected status {expected_status} received")
                
                # Parse response
                try:
                    response_data = response.json()
                    
                    if expected_status == 400:
                        # Validate error response structure
                        self._validate_error_response(response_data, test_name)
                    elif expected_status == 200:
                        # Validate success response structure
                        self._validate_success_response(response_data, test_name)
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log(f"   ❌ Invalid JSON response", "ERROR")
                    return False
            else:
                self.log(f"   ❌ Expected status {expected_status}, got {response.status_code}", "ERROR")
                
                # Log response for debugging
                try:
                    error_data = response.json()
                    self.log(f"   Response: {json.dumps(error_data, indent=2)}")
                except:
                    self.log(f"   Response text: {response.text}")
                
                return False
                
        except Exception as e:
            self.log(f"   ❌ Error in certificate analysis: {str(e)}", "ERROR")
            return False
    
    def _validate_error_response(self, response_data, test_name):
        """Validate error response structure for 400 status"""
        try:
            self.log("   Validating error response structure...")
            
            # Check for required fields in error response
            detail = response_data.get('detail', {})
            
            if isinstance(detail, dict):
                error = detail.get('error')
                message = detail.get('message')
                holder_name = detail.get('holder_name')
                crew_name = detail.get('crew_name')
                crew_name_en = detail.get('crew_name_en')
                
                self.log(f"   Error: {error}")
                self.log(f"   Message: {message}")
                self.log(f"   Holder name: {holder_name}")
                self.log(f"   Crew name: {crew_name}")
                self.log(f"   Crew name EN: {crew_name_en}")
                
                # Validate required fields
                if error == "CERTIFICATE_HOLDER_MISMATCH":
                    self.bypass_tests['normal_flow_error_structure_correct'] = True
                    self.log("   ✅ Error type correct: CERTIFICATE_HOLDER_MISMATCH")
                
                if message and "chứng chỉ" in message.lower():
                    self.bypass_tests['normal_flow_vietnamese_message'] = True
                    self.log("   ✅ Vietnamese error message present")
                
                if holder_name and crew_name:
                    self.bypass_tests['normal_flow_error_fields_present'] = True
                    self.log("   ✅ Required fields present in error response")
                
                self.bypass_tests['validation_logic_working'] = True
                
            else:
                self.log(f"   ❌ Unexpected error response format: {detail}")
                
        except Exception as e:
            self.log(f"   ❌ Error validating error response: {str(e)}", "ERROR")
    
    def _validate_success_response(self, response_data, test_name):
        """Validate success response structure for 200 status"""
        try:
            self.log("   Validating success response structure...")
            
            success = response_data.get('success', False)
            analysis = response_data.get('analysis', {})
            
            self.log(f"   Success: {success}")
            self.log(f"   Analysis data keys: {list(analysis.keys()) if analysis else 'None'}")
            
            if success:
                self.bypass_tests['bypass_flow_success_response'] = True
                self.log("   ✅ Success flag present")
            
            if analysis:
                self.bypass_tests['bypass_flow_analysis_data_returned'] = True
                self.log("   ✅ Analysis data returned")
                
                # Log some analysis fields
                for key, value in analysis.items():
                    if value:
                        self.log(f"     {key}: {value}")
            
            self.bypass_tests['bypass_parameter_processed'] = True
            
        except Exception as e:
            self.log(f"   ❌ Error validating success response: {str(e)}", "ERROR")
    
    def check_backend_logs_for_bypass_warning(self):
        """Check backend logs for bypass validation warning"""
        try:
            self.log("📋 Checking backend logs for bypass validation warning...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            bypass_warning_found = False
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # Get recent logs
                        result = os.popen(f"tail -n 50 {log_file}").read()
                        
                        # Look for bypass validation warning
                        if "VALIDATION BYPASSED" in result:
                            self.log("✅ Found bypass validation warning in logs")
                            self.bypass_tests['bypass_flow_backend_logs_warning'] = True
                            bypass_warning_found = True
                            
                            # Extract the warning line
                            lines = result.split('\n')
                            for line in lines:
                                if "VALIDATION BYPASSED" in line:
                                    self.log(f"   Log: {line.strip()}")
                                    break
                        
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            if not bypass_warning_found:
                self.log("⚠️ Bypass validation warning not found in recent logs")
            
            return bypass_warning_found
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test of bypass validation feature"""
        try:
            self.log("🚀 STARTING CERTIFICATE HOLDER MISMATCH BYPASS VALIDATION TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find test ship
            self.log("\nSTEP 2: Finding test ship (BROTHER 36)")
            if not self.find_test_ship():
                self.log("❌ CRITICAL: Ship discovery failed - cannot proceed")
                return False
            
            # Step 3: Find test crew
            self.log("\nSTEP 3: Finding test crew member")
            if not self.find_test_crew():
                self.log("❌ CRITICAL: Crew discovery failed - cannot proceed")
                return False
            
            # Step 4: Test normal flow (bypass_validation = false)
            self.log("\nSTEP 4: Testing normal flow (bypass_validation = false)")
            self.test_normal_flow_bypass_false()
            
            # Step 5: Test bypass flow (bypass_validation = true)
            self.log("\nSTEP 5: Testing bypass flow (bypass_validation = true)")
            self.test_bypass_flow_bypass_true()
            
            # Step 6: Test edge cases
            self.log("\nSTEP 6: Testing edge cases (different bypass_validation values)")
            self.test_edge_cases()
            
            # Step 7: Check backend logs
            self.log("\nSTEP 7: Checking backend logs for bypass warnings")
            self.check_backend_logs_for_bypass_warning()
            
            self.log("\n" + "=" * 80)
            self.log("✅ CERTIFICATE HOLDER MISMATCH BYPASS VALIDATION TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 CERTIFICATE HOLDER MISMATCH BYPASS VALIDATION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.bypass_tests)
            passed_tests = sum(1 for result in self.bypass_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('ship_discovery_successful', 'Ship discovery successful'),
                ('crew_discovery_successful', 'Crew discovery successful'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.bypass_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Case 1: Normal Flow Results
            self.log("\n📋 TEST CASE 1 - NORMAL FLOW (bypass_validation = false):")
            normal_tests = [
                ('normal_flow_mismatch_returns_400', 'Returns 400 for holder name mismatch'),
                ('normal_flow_error_structure_correct', 'Error structure correct (CERTIFICATE_HOLDER_MISMATCH)'),
                ('normal_flow_error_fields_present', 'Required error fields present'),
                ('normal_flow_vietnamese_message', 'Vietnamese error message present'),
            ]
            
            for test_key, description in normal_tests:
                status = "✅ PASS" if self.bypass_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Case 2: Bypass Flow Results
            self.log("\n📋 TEST CASE 2 - BYPASS FLOW (bypass_validation = true):")
            bypass_tests = [
                ('bypass_flow_returns_200', 'Returns 200 when bypass enabled'),
                ('bypass_flow_analysis_data_returned', 'Analysis data returned correctly'),
                ('bypass_flow_backend_logs_warning', 'Backend logs show bypass warning'),
                ('bypass_flow_success_response', 'Success response structure correct'),
            ]
            
            for test_key, description in bypass_tests:
                status = "✅ PASS" if self.bypass_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Case 3: Edge Cases Results
            self.log("\n📋 TEST CASE 3 - EDGE CASES:")
            edge_tests = [
                ('edge_case_true_uppercase', 'Uppercase TRUE/True values work'),
                ('edge_case_false_uppercase', 'Uppercase FALSE/False values work'),
                ('edge_case_mixed_case', 'Mixed case values handled correctly'),
            ]
            
            for test_key, description in edge_tests:
                status = "✅ PASS" if self.bypass_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Verification Results
            self.log("\n🔧 BACKEND VERIFICATION:")
            backend_tests = [
                ('endpoint_accessible', 'Endpoint accessible'),
                ('multipart_form_data_accepted', 'Multipart form data accepted'),
                ('validation_logic_working', 'Validation logic working'),
                ('bypass_parameter_processed', 'Bypass parameter processed correctly'),
            ]
            
            for test_key, description in backend_tests:
                status = "✅ PASS" if self.bypass_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'normal_flow_mismatch_returns_400',
                'bypass_flow_returns_200',
                'validation_logic_working',
                'bypass_parameter_processed'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.bypass_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL REQUIREMENTS MET")
                self.log("   ✅ Normal flow blocks mismatched certificates (400 error)")
                self.log("   ✅ Bypass flow allows mismatched certificates (200 success)")
                self.log("   ✅ Backend validation logic working correctly")
                self.log("   ✅ bypass_validation parameter processed correctly")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Success rate assessment
            if success_rate >= 90:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 75:
                self.log(f"   ✅ GOOD SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ MODERATE SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    tester = CertificateBypassValidationTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Comprehensive Standby Crew Certificate Upload Fix Verification Test

This test verifies the fix for the Standby Crew Certificate File Upload issue:
- Bug: ship_name was empty ('') causing Apps Script to fail
- Fix: ship_name changed to 'COMPANY DOCUMENT' for Standby crew uploads
- Expected: Both certificate file and summary file should upload successfully
"""

import requests
import json
import os
import sys
import tempfile
from datetime import datetime
import time
import traceback

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                external_url = line.split('=', 1)[1].strip()
                BACKEND_URL = external_url + '/api'
                print(f"Using external backend URL: {BACKEND_URL}")
                break

class ComprehensiveStandbyCertTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        
        # Test results tracking
        self.test_results = {
            'authentication_successful': False,
            'standby_crew_found': False,
            'ship_crew_found': False,
            'standby_cert_created_with_null_ship_id': False,
            'ship_cert_created_with_valid_ship_id': False,
            'standby_cert_file_uploaded': False,
            'standby_summary_file_uploaded': False,
            'ship_cert_file_uploaded': False,
            'ship_summary_file_uploaded': False,
            'standby_both_files_uploaded': False,
            'ship_both_files_uploaded': False,
            'backend_logs_show_company_document': False,
            'backend_logs_show_standby_crew_folder': False,
            'no_apps_script_errors': False,
            'fix_working_correctly': False
        }
        
        # Store test data
        self.standby_crew = None
        self.ship_crew = None
        self.standby_cert_id = None
        self.ship_cert_id = None
        
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
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User: {self.current_user.get('username')} ({self.current_user.get('role')})")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.test_results['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_test_crew_members(self):
        """Find Standby crew and Ship crew for testing"""
        try:
            self.log("🔍 Finding test crew members...")
            
            response = self.session.get(f"{BACKEND_URL}/crew")
            
            if response.status_code == 200:
                crew_list = response.json()
                self.log(f"   Found {len(crew_list)} total crew members")
                
                # Find Standby crew (ship_sign_on = "-")
                for crew in crew_list:
                    ship_sign_on = crew.get("ship_sign_on", "")
                    if ship_sign_on == "-":
                        self.standby_crew = crew
                        self.log(f"✅ Found Standby crew: {crew.get('full_name')} (ID: {crew.get('id')})")
                        self.test_results['standby_crew_found'] = True
                        break
                
                # Find Ship crew (ship_sign_on != "-")
                for crew in crew_list:
                    ship_sign_on = crew.get("ship_sign_on", "")
                    if ship_sign_on and ship_sign_on != "-":
                        self.ship_crew = crew
                        self.log(f"✅ Found Ship crew: {crew.get('full_name')} (Ship: {ship_sign_on})")
                        self.test_results['ship_crew_found'] = True
                        break
                
                return self.standby_crew is not None and self.ship_crew is not None
            else:
                self.log(f"❌ Failed to get crew list: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding crew members: {str(e)}", "ERROR")
            return False
    
    def create_test_certificates(self):
        """Create test certificates for both Standby and Ship crew"""
        try:
            self.log("📋 Creating test certificates...")
            
            # Create Standby crew certificate
            if self.standby_crew:
                standby_cert_data = {
                    "crew_id": self.standby_crew.get("id"),
                    "crew_name": self.standby_crew.get("full_name"),
                    "passport": self.standby_crew.get("passport", "STANDBY123"),
                    "cert_name": "STCW Basic Safety Training",
                    "cert_no": "BST-STANDBY-TEST-001",
                    "issued_by": "Panama Maritime Authority",
                    "issued_date": "2023-01-15T00:00:00Z",
                    "cert_expiry": "2028-01-15T00:00:00Z",
                    "status": "Valid",
                    "note": "Test certificate for Standby crew upload fix verification"
                }
                
                response = self.session.post(f"{BACKEND_URL}/crew-certificates/manual", json=standby_cert_data, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    self.standby_cert_id = result.get("id")
                    ship_id = result.get("ship_id")
                    
                    self.log(f"✅ Standby certificate created (ID: {self.standby_cert_id})")
                    self.log(f"   Ship ID: {ship_id}")
                    
                    if ship_id is None:
                        self.log("✅ Ship ID is null for Standby crew (correct)")
                        self.test_results['standby_cert_created_with_null_ship_id'] = True
                    else:
                        self.log(f"❌ Ship ID should be null for Standby crew, got: {ship_id}", "ERROR")
                else:
                    self.log(f"❌ Standby certificate creation failed: {response.text}", "ERROR")
                    return False
            
            # Create Ship crew certificate
            if self.ship_crew:
                ship_cert_data = {
                    "crew_id": self.ship_crew.get("id"),
                    "crew_name": self.ship_crew.get("full_name"),
                    "passport": self.ship_crew.get("passport", "SHIP123"),
                    "cert_name": "STCW Basic Safety Training",
                    "cert_no": "BST-SHIP-TEST-001",
                    "issued_by": "Panama Maritime Authority",
                    "issued_date": "2023-01-15T00:00:00Z",
                    "cert_expiry": "2028-01-15T00:00:00Z",
                    "status": "Valid",
                    "note": "Test certificate for Ship crew comparison"
                }
                
                response = self.session.post(f"{BACKEND_URL}/crew-certificates/manual", json=ship_cert_data, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    self.ship_cert_id = result.get("id")
                    ship_id = result.get("ship_id")
                    
                    self.log(f"✅ Ship certificate created (ID: {self.ship_cert_id})")
                    self.log(f"   Ship ID: {ship_id}")
                    
                    if ship_id:
                        self.log("✅ Ship ID is valid UUID for Ship crew (correct)")
                        self.test_results['ship_cert_created_with_valid_ship_id'] = True
                    else:
                        self.log("❌ Ship ID should be valid UUID for Ship crew", "ERROR")
                else:
                    self.log(f"❌ Ship certificate creation failed: {response.text}", "ERROR")
                    return False
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating certificates: {str(e)}", "ERROR")
            return False
    
    def create_test_pdf_file(self, filename):
        """Create a test PDF file for upload"""
        try:
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
/Length 50
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Certificate File) Tj
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
305
%%EOF"""
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(pdf_content)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Error creating test PDF file: {str(e)}", "ERROR")
            return None
    
    def test_certificate_file_uploads(self):
        """Test certificate file uploads for both Standby and Ship crew"""
        try:
            self.log("📤 Testing certificate file uploads...")
            
            # Test Standby crew certificate upload
            if self.standby_cert_id:
                self.log("📤 Testing Standby crew certificate upload...")
                
                test_file_path = self.create_test_pdf_file("standby_test_cert.pdf")
                if not test_file_path:
                    return False
                
                try:
                    with open(test_file_path, "rb") as f:
                        files = {
                            "cert_file": ("standby_test_certificate.pdf", f, "application/pdf")
                        }
                        data = {
                            "cert_id": self.standby_cert_id
                        }
                        
                        start_time = time.time()
                        response = self.session.post(
                            f"{BACKEND_URL}/crew-certificates/{self.standby_cert_id}/upload-files",
                            files=files,
                            data=data,
                            timeout=120
                        )
                        end_time = time.time()
                        
                        self.log(f"⏱️ Standby upload processing time: {end_time - start_time:.1f} seconds")
                        self.log(f"   Response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            success = result.get("success", False)
                            cert_file_id = result.get("crew_cert_file_id")
                            summary_file_id = result.get("crew_cert_summary_file_id")
                            
                            self.log(f"   Success: {success}")
                            self.log(f"   Certificate File ID: {cert_file_id}")
                            self.log(f"   Summary File ID: {summary_file_id}")
                            
                            if cert_file_id:
                                self.log("✅ Standby certificate file uploaded successfully")
                                self.test_results['standby_cert_file_uploaded'] = True
                            
                            if summary_file_id:
                                self.log("✅ Standby summary file uploaded successfully")
                                self.test_results['standby_summary_file_uploaded'] = True
                            
                            if cert_file_id and summary_file_id:
                                self.log("✅ STANDBY: Both files uploaded successfully - FIX WORKING!")
                                self.test_results['standby_both_files_uploaded'] = True
                            else:
                                self.log("❌ STANDBY: Not all files uploaded - fix may not be working", "ERROR")
                        else:
                            self.log(f"❌ Standby upload failed: {response.text}", "ERROR")
                            
                finally:
                    os.unlink(test_file_path)
            
            # Test Ship crew certificate upload (for comparison)
            if self.ship_cert_id:
                self.log("📤 Testing Ship crew certificate upload (for comparison)...")
                
                test_file_path = self.create_test_pdf_file("ship_test_cert.pdf")
                if not test_file_path:
                    return False
                
                try:
                    with open(test_file_path, "rb") as f:
                        files = {
                            "cert_file": ("ship_test_certificate.pdf", f, "application/pdf")
                        }
                        data = {
                            "cert_id": self.ship_cert_id
                        }
                        
                        start_time = time.time()
                        response = self.session.post(
                            f"{BACKEND_URL}/crew-certificates/{self.ship_cert_id}/upload-files",
                            files=files,
                            data=data,
                            timeout=120
                        )
                        end_time = time.time()
                        
                        self.log(f"⏱️ Ship upload processing time: {end_time - start_time:.1f} seconds")
                        self.log(f"   Response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            success = result.get("success", False)
                            cert_file_id = result.get("crew_cert_file_id")
                            summary_file_id = result.get("crew_cert_summary_file_id")
                            
                            self.log(f"   Success: {success}")
                            self.log(f"   Certificate File ID: {cert_file_id}")
                            self.log(f"   Summary File ID: {summary_file_id}")
                            
                            if cert_file_id:
                                self.test_results['ship_cert_file_uploaded'] = True
                            
                            if summary_file_id:
                                self.test_results['ship_summary_file_uploaded'] = True
                            
                            if cert_file_id and summary_file_id:
                                self.log("✅ SHIP: Both files uploaded successfully")
                                self.test_results['ship_both_files_uploaded'] = True
                        else:
                            self.log(f"❌ Ship upload failed: {response.text}", "ERROR")
                            
                finally:
                    os.unlink(test_file_path)
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing certificate uploads: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs_for_fix(self):
        """Check backend logs for evidence of the fix"""
        try:
            self.log("📋 Checking backend logs for fix evidence...")
            
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            company_document_found = False
            standby_crew_folder_found = False
            no_errors_found = True
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # Get last 300 lines to capture recent activity
                        result = os.popen(f"tail -n 300 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            for line in lines:
                                # Look for evidence of the fix
                                if "Upload destination:" in line and "COMPANY DOCUMENT" in line:
                                    self.log(f"   ✅ Found COMPANY DOCUMENT upload destination: {line.strip()}")
                                    company_document_found = True
                                    self.test_results['backend_logs_show_company_document'] = True
                                
                                if "Standby Crew" in line:
                                    self.log(f"   ✅ Found Standby Crew folder reference: {line.strip()}")
                                    standby_crew_folder_found = True
                                    self.test_results['backend_logs_show_standby_crew_folder'] = True
                                
                                # Look for the specific fix
                                if 'ship_name: "COMPANY DOCUMENT"' in line:
                                    self.log(f"   ✅ Found FIXED ship_name parameter: {line.strip()}")
                                
                                if 'ship_name: ""' in line or "ship_name: ''" in line:
                                    self.log(f"   ❌ Found EMPTY ship_name (bug not fixed): {line.strip()}")
                                    no_errors_found = False
                                
                                # Look for Apps Script success
                                if "Apps Script response" in line and "success=True" in line:
                                    self.log(f"   ✅ Apps Script success: {line.strip()}")
                                
                                if "ERROR" in line and "Apps Script" in line:
                                    self.log(f"   ❌ Apps Script error: {line.strip()}")
                                    no_errors_found = False
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            if no_errors_found:
                self.test_results['no_apps_script_errors'] = True
            
            return company_document_found and standby_crew_folder_found
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test of the Standby crew certificate upload fix"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE STANDBY CREW CERTIFICATE UPLOAD FIX TEST")
            self.log("=" * 80)
            self.log("Testing fix: ship_name changed from '' (empty) to 'COMPANY DOCUMENT'")
            self.log("Expected: BOTH certificate file and summary file should upload for Standby crew")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find test crew members
            self.log("\nSTEP 2: Find Test Crew Members")
            if not self.find_test_crew_members():
                self.log("❌ CRITICAL: Could not find required test crew members")
                return False
            
            # Step 3: Create test certificates
            self.log("\nSTEP 3: Create Test Certificates")
            if not self.create_test_certificates():
                self.log("❌ CRITICAL: Certificate creation failed")
                return False
            
            # Step 4: Test file uploads
            self.log("\nSTEP 4: Test Certificate File Uploads")
            self.test_certificate_file_uploads()
            
            # Step 5: Check backend logs
            self.log("\nSTEP 5: Check Backend Logs for Fix Evidence")
            self.check_backend_logs_for_fix()
            
            # Determine if fix is working
            standby_working = self.test_results['standby_both_files_uploaded']
            ship_working = self.test_results['ship_both_files_uploaded']
            logs_confirm = (self.test_results['backend_logs_show_company_document'] and 
                          self.test_results['backend_logs_show_standby_crew_folder'])
            
            if standby_working and logs_confirm:
                self.log("✅ FIX IS WORKING CORRECTLY!")
                self.test_results['fix_working_correctly'] = True
            else:
                self.log("❌ FIX MAY NOT BE WORKING CORRECTLY")
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE STANDBY CREW CERTIFICATE UPLOAD FIX TEST COMPLETED")
            return standby_working
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 COMPREHENSIVE STANDBY CREW CERTIFICATE UPLOAD FIX TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Test Results by Category
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('standby_crew_found', 'Standby crew found'),
                ('ship_crew_found', 'Ship crew found'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            self.log("\n📋 CERTIFICATE CREATION:")
            cert_tests = [
                ('standby_cert_created_with_null_ship_id', 'Standby certificate created with ship_id = null'),
                ('ship_cert_created_with_valid_ship_id', 'Ship certificate created with valid ship_id'),
            ]
            
            for test_key, description in cert_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            self.log("\n📤 FILE UPLOAD RESULTS:")
            upload_tests = [
                ('standby_cert_file_uploaded', 'Standby certificate file uploaded'),
                ('standby_summary_file_uploaded', 'Standby summary file uploaded'),
                ('standby_both_files_uploaded', 'STANDBY: Both files uploaded (CRITICAL)'),
                ('ship_cert_file_uploaded', 'Ship certificate file uploaded'),
                ('ship_summary_file_uploaded', 'Ship summary file uploaded'),
                ('ship_both_files_uploaded', 'SHIP: Both files uploaded (comparison)'),
            ]
            
            for test_key, description in upload_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            self.log("\n📋 BACKEND LOGS & FIX VERIFICATION:")
            log_tests = [
                ('backend_logs_show_company_document', 'Backend logs show COMPANY DOCUMENT'),
                ('backend_logs_show_standby_crew_folder', 'Backend logs show Standby Crew folder'),
                ('no_apps_script_errors', 'No Apps Script errors'),
                ('fix_working_correctly', 'FIX WORKING CORRECTLY (OVERALL)'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Assessment
            self.log("\n🎯 CRITICAL ASSESSMENT:")
            
            critical_tests = [
                'standby_cert_file_uploaded',
                'standby_summary_file_uploaded',
                'standby_both_files_uploaded'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.test_results.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL TESTS PASSED")
                self.log("   ✅ Standby crew certificate uploads working correctly")
                self.log("   ✅ ship_name: 'COMPANY DOCUMENT' fix successful")
                self.log("   ✅ Both certificate and summary files uploaded")
            else:
                self.log("   ❌ CRITICAL TESTS FAILED")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
                self.log("   ❌ Fix may not be working correctly")
            
            # Expected vs Actual Results
            self.log("\n📋 EXPECTED VS ACTUAL RESULTS:")
            self.log("   Expected (FIXED):")
            self.log("     - Certificate file uploaded: crew_cert_file_id not null ✓")
            self.log("     - Summary file uploaded: crew_cert_summary_file_id not null ✓")
            self.log("     - Both file IDs stored in database ✓")
            self.log("     - No Apps Script errors ✓")
            self.log("     - Files in folder: ROOT/COMPANY DOCUMENT/Standby Crew ✓")
            
            standby_cert = self.test_results.get('standby_cert_file_uploaded', False)
            standby_summary = self.test_results.get('standby_summary_file_uploaded', False)
            
            self.log("   Actual Results:")
            self.log(f"     - Certificate file uploaded: {'✅ YES' if standby_cert else '❌ NO'}")
            self.log(f"     - Summary file uploaded: {'✅ YES' if standby_summary else '❌ NO'}")
            self.log(f"     - Both files uploaded: {'✅ YES' if standby_cert and standby_summary else '❌ NO'}")
            self.log(f"     - Fix working correctly: {'✅ YES' if self.test_results.get('fix_working_correctly') else '❌ NO'}")
            
            if success_rate >= 90:
                self.log(f"\n   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}% - Fix is working perfectly!")
            elif success_rate >= 75:
                self.log(f"\n   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}% - Fix is mostly working")
            else:
                self.log(f"\n   ❌ LOW SUCCESS RATE: {success_rate:.1f}% - Fix needs attention")
            
            self.log("=" * 80)
            
            return success_rate >= 75
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")
            return False

def main():
    """Main test execution"""
    tester = ComprehensiveStandbyCertTester()
    
    try:
        # Run the comprehensive test
        success = tester.run_comprehensive_test()
        
        # Print detailed summary
        summary_success = tester.print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success and summary_success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
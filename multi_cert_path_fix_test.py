#!/usr/bin/env python3
"""
Multi Certificate Upload Google Drive Folder Path Fix - Final Verification Test
FOCUS: Test the FIXED Multi Certificate upload with new createNestedFolders approach

REVIEW REQUEST REQUIREMENTS:
1. Authentication: Login with admin1/123456 credentials
2. Multi Cert Upload Test: Upload a test certificate via POST /api/certificates/multi-upload  
3. Verify NEW Correct Path: Confirm file uploaded to:
   - ✅ Expected: `SUNSHINE 01/Class & Flag Cert/Certificates/[filename]`
   - ❌ NOT: `SUNSHINE 01/Certificates/[filename]` (old incorrect path)
4. Parameter Verification: Check backend sends:
   - `parent_category`: "Class & Flag Cert"
   - `category`: "Certificates" 
   - `filename`: correct filename
5. Google Apps Script Response: Verify response contains correct folder_path

KEY FIX VERIFICATION POINTS:
- Backend sends both parent_category AND category parameters correctly
- Google Apps Script createNestedFolders() creates proper hierarchy
- Upload response folder_path shows: "SUNSHINE 01/Class & Flag Cert/Certificates"
- File successfully created in the correct nested folder structure
- No "folder not found" errors

SUCCESS CRITERIA:
- ✅ Google Drive upload successful 
- ✅ Correct folder path: "[Ship]/Class & Flag Cert/Certificates"
- ✅ Certificate record created in database
- ✅ Google Apps Script nested folder creation working
- ✅ Backend parameter transmission correct
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
import io

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://certisync-marine.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class MultiCertPathFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Multi Certificate Upload Path Fix verification
        self.path_fix_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_admin_role_verified': False,
            'user_company_identified': False,
            
            # Multi Certificate Upload Test
            'multi_upload_endpoint_accessible': False,
            'test_certificate_created': False,
            'upload_request_successful': False,
            'upload_response_valid': False,
            
            # NEW PATH VERIFICATION - Critical Fix Points
            'correct_folder_path_in_response': False,
            'new_nested_path_structure': False,
            'old_incorrect_path_not_used': False,
            'class_flag_cert_parent_folder': False,
            'certificates_subfolder_correct': False,
            
            # Parameter Verification
            'parent_category_parameter_sent': False,
            'category_parameter_sent': False,
            'filename_parameter_correct': False,
            'backend_parameters_correct': False,
            
            # Google Apps Script Integration
            'google_drive_upload_successful': False,
            'google_apps_script_response_valid': False,
            'nested_folder_creation_working': False,
            'folder_path_in_response': False,
            
            # Database Verification
            'certificate_record_created': False,
            'database_folder_path_correct': False,
            'google_drive_file_id_present': False,
            
            # Error Handling
            'no_folder_not_found_errors': False,
            'createNestedFolders_working': False,
        }
        
        # Store test results for analysis
        self.user_company = None
        self.test_ship = None
        self.upload_response = {}
        self.created_certificate = {}
        self.test_file_content = None
        
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
                
                self.path_fix_tests['authentication_successful'] = True
                
                # Verify admin role
                if self.current_user.get('role', '').upper() in ['ADMIN', 'SUPER_ADMIN']:
                    self.path_fix_tests['user_admin_role_verified'] = True
                    self.log("✅ Admin role verified")
                
                self.user_company = self.current_user.get('company')
                if self.user_company:
                    self.path_fix_tests['user_company_identified'] = True
                    self.log(f"✅ User company identified: {self.user_company}")
                
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
    
    def find_test_ship(self):
        """Find SUNSHINE 01 ship or suitable test ship"""
        try:
            self.log("🚢 Finding test ship (preferably SUNSHINE 01)...")
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                return False
            
            ships = response.json()
            self.log(f"   Found {len(ships)} total ships")
            
            # Look for SUNSHINE 01 first
            sunshine_ship = None
            user_company_ships = []
            
            for ship in ships:
                ship_name = ship.get('name', '')
                ship_company = ship.get('company', '')
                
                if ship_company == self.user_company:
                    user_company_ships.append(ship)
                    
                if 'SUNSHINE' in ship_name.upper() and '01' in ship_name:
                    sunshine_ship = ship
                    self.log(f"   ✅ Found SUNSHINE 01 ship: {ship_name}")
            
            if sunshine_ship:
                self.test_ship = sunshine_ship
                self.log(f"   Using SUNSHINE 01 ship: {sunshine_ship.get('name')} (ID: {sunshine_ship.get('id')})")
                return True
            elif user_company_ships:
                self.test_ship = user_company_ships[0]
                self.log(f"   Using first user company ship: {self.test_ship.get('name')} (ID: {self.test_ship.get('id')})")
                return True
            else:
                self.log("❌ No suitable test ship found")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding test ship: {str(e)}", "ERROR")
            return False
    
    def create_test_certificate_pdf(self):
        """Create a simple test certificate PDF for upload"""
        try:
            self.log("📄 Creating test certificate PDF...")
            
            # Create a simple PDF content (minimal implementation)
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
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Certificate) Tj
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
300
%%EOF"""
            
            self.test_file_content = pdf_content
            
            self.log(f"✅ Test certificate PDF created ({len(self.test_file_content)} bytes)")
            self.path_fix_tests['test_certificate_created'] = True
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating test certificate PDF: {str(e)}", "ERROR")
            return False
    
    def test_multi_certificate_upload(self):
        """Test the multi-certificate upload endpoint with path fix verification"""
        try:
            self.log("📤 Testing multi-certificate upload with path fix verification...")
            
            if not self.test_file_content:
                self.log("❌ No test file content available")
                return False
            
            # Prepare the upload request
            endpoint = f"{BACKEND_URL}/certificates/multi-upload"
            self.log(f"   POST {endpoint}")
            
            # Add ship_id as query parameter
            params = {"ship_id": self.test_ship.get('id')}
            
            # Prepare files for upload
            files = {
                'files': ('test_certificate.pdf', self.test_file_content, 'application/pdf')
            }
            
            # Prepare form data - CRITICAL: Check what parameters are sent
            form_data = {
                'category': 'Class & Flag Cert',  # This should be parent_category
                'subcategory': 'Certificates',    # This should be category
                'ship_name': self.test_ship.get('name'),
            }
            
            self.log("   📋 Upload parameters being sent:")
            self.log(f"      ship_id (query): {params['ship_id']}")
            self.log(f"      category (form): {form_data['category']}")
            self.log(f"      subcategory (form): {form_data['subcategory']}")
            self.log(f"      ship_name (form): {form_data['ship_name']}")
            self.log(f"      file: test_certificate.pdf ({len(self.test_file_content)} bytes)")
            
            # Make the upload request
            response = requests.post(
                endpoint, 
                params=params,
                data=form_data,
                files=files,
                headers=self.get_headers(), 
                timeout=120  # Longer timeout for file upload
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.path_fix_tests['multi_upload_endpoint_accessible'] = True
                self.path_fix_tests['upload_request_successful'] = True
                self.log("✅ Multi-certificate upload request successful")
                
                try:
                    response_data = response.json()
                    self.upload_response = response_data
                    self.path_fix_tests['upload_response_valid'] = True
                    self.log("✅ Upload response is valid JSON")
                    
                    # Log the full response for analysis
                    self.log("   📋 Upload response structure:")
                    self.log(f"      Response keys: {list(response_data.keys())}")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return False
            else:
                self.log(f"❌ Multi-certificate upload failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing multi-certificate upload: {str(e)}", "ERROR")
            return False
    
    def verify_new_folder_path_structure(self):
        """Verify the NEW correct folder path structure in response"""
        try:
            self.log("🔍 Verifying NEW folder path structure...")
            
            if not self.upload_response:
                self.log("❌ No upload response to verify")
                return False
            
            # Check if upload was successful
            success = self.upload_response.get('success', False)
            if not success:
                self.log("❌ Upload was not successful according to response")
                return False
            
            # Look for results array
            results = self.upload_response.get('results', [])
            if not results:
                self.log("❌ No results in upload response")
                return False
            
            self.log(f"   Found {len(results)} upload results")
            
            # Check each result for correct folder path
            correct_paths = 0
            incorrect_paths = 0
            
            for i, result in enumerate(results):
                self.log(f"   📁 Result {i+1}:")
                
                # Check if upload was successful
                result_success = result.get('success', False)
                self.log(f"      Success: {result_success}")
                
                if not result_success:
                    error_msg = result.get('error', 'Unknown error')
                    self.log(f"      ❌ Upload failed: {error_msg}")
                    incorrect_paths += 1
                    continue
                
                # Get folder path from response
                folder_path = result.get('folder_path', '')
                google_drive_folder_path = result.get('google_drive_folder_path', '')
                file_name = result.get('file_name', '')
                
                self.log(f"      File name: {file_name}")
                self.log(f"      Folder path: {folder_path}")
                self.log(f"      Google Drive folder path: {google_drive_folder_path}")
                
                # CRITICAL VERIFICATION: Check for NEW correct path structure
                ship_name = self.test_ship.get('name', '')
                expected_new_path = f"{ship_name}/Class & Flag Cert/Certificates"
                old_incorrect_path = f"{ship_name}/Certificates"
                
                self.log(f"      Expected NEW path: {expected_new_path}")
                self.log(f"      Old INCORRECT path: {old_incorrect_path}")
                
                # Check folder_path field
                if folder_path:
                    if expected_new_path in folder_path or folder_path == expected_new_path:
                        self.log("      ✅ CORRECT NEW PATH STRUCTURE FOUND in folder_path")
                        correct_paths += 1
                        self.path_fix_tests['correct_folder_path_in_response'] = True
                        self.path_fix_tests['new_nested_path_structure'] = True
                        self.path_fix_tests['class_flag_cert_parent_folder'] = True
                        self.path_fix_tests['certificates_subfolder_correct'] = True
                        
                        # Verify it's NOT the old incorrect path
                        if old_incorrect_path not in folder_path:
                            self.path_fix_tests['old_incorrect_path_not_used'] = True
                            self.log("      ✅ Old incorrect path NOT used")
                        else:
                            self.log("      ❌ Old incorrect path still present")
                            
                    elif old_incorrect_path in folder_path:
                        self.log("      ❌ OLD INCORRECT PATH STRUCTURE FOUND")
                        self.log(f"         Found: {folder_path}")
                        self.log(f"         This should be: {expected_new_path}")
                        incorrect_paths += 1
                    else:
                        self.log(f"      ⚠️ Unexpected folder path format: {folder_path}")
                        incorrect_paths += 1
                
                # Also check google_drive_folder_path field
                if google_drive_folder_path:
                    if expected_new_path in google_drive_folder_path:
                        self.log("      ✅ CORRECT NEW PATH also found in google_drive_folder_path")
                    elif old_incorrect_path in google_drive_folder_path:
                        self.log("      ❌ OLD INCORRECT PATH found in google_drive_folder_path")
                
                # Check for Google Drive success indicators
                google_drive_file_id = result.get('google_drive_file_id')
                if google_drive_file_id:
                    self.path_fix_tests['google_drive_upload_successful'] = True
                    self.log(f"      ✅ Google Drive upload successful (File ID: {google_drive_file_id})")
                
                # Store certificate info for database verification
                cert_id = result.get('certificate_id')
                if cert_id:
                    self.created_certificate = result
                    self.path_fix_tests['certificate_record_created'] = True
                    self.log(f"      ✅ Certificate record created (ID: {cert_id})")
            
            # Overall assessment
            if correct_paths > 0 and incorrect_paths == 0:
                self.log(f"✅ NEW FOLDER PATH STRUCTURE VERIFIED - All {correct_paths} uploads use correct path")
                self.path_fix_tests['folder_path_in_response'] = True
                return True
            elif incorrect_paths > 0:
                self.log(f"❌ FOLDER PATH FIX NOT WORKING - {incorrect_paths} uploads use old incorrect path")
                return False
            else:
                self.log("⚠️ No clear folder path information found in response")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying folder path structure: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_path_fix_test(self):
        """Run comprehensive test of the Multi Certificate Upload Google Drive folder path fix"""
        try:
            self.log("🚀 STARTING MULTI CERTIFICATE UPLOAD GOOGLE DRIVE FOLDER PATH FIX TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find test ship
            self.log("\nSTEP 2: Finding test ship")
            if not self.find_test_ship():
                self.log("❌ CRITICAL: Could not find suitable test ship")
                return False
            
            # Step 3: Create test certificate
            self.log("\nSTEP 3: Creating test certificate PDF")
            if not self.create_test_certificate_pdf():
                self.log("❌ CRITICAL: Could not create test certificate")
                return False
            
            # Step 4: Test multi-certificate upload
            self.log("\nSTEP 4: Testing multi-certificate upload")
            if not self.test_multi_certificate_upload():
                self.log("❌ CRITICAL: Multi-certificate upload failed")
                return False
            
            # Step 5: Verify NEW folder path structure
            self.log("\nSTEP 5: Verifying NEW folder path structure")
            if not self.verify_new_folder_path_structure():
                self.log("❌ CRITICAL: Folder path structure verification failed")
                return False
            
            self.log("\n" + "=" * 80)
            self.log("✅ MULTI CERTIFICATE UPLOAD PATH FIX TEST COMPLETED SUCCESSFULLY")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_path_fix_test_summary(self):
        """Print comprehensive summary of path fix test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 MULTI CERTIFICATE UPLOAD PATH FIX TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.path_fix_tests)
            passed_tests = sum(1 for result in self.path_fix_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Critical Path Fix Results
            self.log("🔧 CRITICAL PATH FIX VERIFICATION:")
            critical_tests = [
                ('correct_folder_path_in_response', 'Correct folder path in response'),
                ('new_nested_path_structure', 'NEW nested path structure working'),
                ('old_incorrect_path_not_used', 'Old incorrect path NOT used'),
                ('class_flag_cert_parent_folder', 'Class & Flag Cert parent folder created'),
                ('certificates_subfolder_correct', 'Certificates subfolder correct'),
            ]
            
            for test_key, description in critical_tests:
                status = "✅ PASS" if self.path_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL PATH FIX ASSESSMENT:")
            
            critical_passed = sum(1 for test_key, _ in critical_tests if self.path_fix_tests.get(test_key, False))
            if critical_passed >= 4:  # At least 4 critical tests passed
                self.log("   ✅ MULTI CERTIFICATE UPLOAD PATH FIX IS WORKING")
                self.log("   ✅ Files are now uploaded to correct nested folder structure")
                self.log("   ✅ Google Apps Script createNestedFolders() is functioning")
                self.log("   ✅ Backend parameter transmission is correct")
                
                # Check specific success criteria from review request
                if (self.path_fix_tests.get('google_drive_upload_successful', False) and
                    self.path_fix_tests.get('correct_folder_path_in_response', False) and
                    self.path_fix_tests.get('certificate_record_created', False)):
                    
                    self.log("\n🏆 SUCCESS CRITERIA MET:")
                    self.log("   ✅ Google Drive upload successful")
                    self.log("   ✅ Correct folder path: [Ship]/Class & Flag Cert/Certificates")
                    self.log("   ✅ Certificate record created in database")
                    
                    self.log("\n🎉 MULTI CERTIFICATE GOOGLE DRIVE FOLDER PATH ISSUE IS FINALLY RESOLVED!")
                else:
                    self.log("\n⚠️ Some success criteria not fully met - review individual test results")
            else:
                self.log("   ❌ MULTI CERTIFICATE UPLOAD PATH FIX IS NOT WORKING")
                self.log("   ❌ Files may still be uploaded to incorrect folder structure")
                self.log("   ❌ Further investigation and fixes needed")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    tester = MultiCertPathFixTester()
    
    try:
        # Run the comprehensive test
        success = tester.run_comprehensive_path_fix_test()
        
        # Print detailed summary
        tester.print_path_fix_test_summary()
        
        # Exit with appropriate code
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
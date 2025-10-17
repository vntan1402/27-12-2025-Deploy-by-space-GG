#!/usr/bin/env python3
"""
Ship Management System - Multi Certificate Upload Google Drive Folder Path Fix Testing
FOCUS: Test the FIXED Multi Certificate upload folder path to verify files are uploaded to correct "Class & Flag Cert/Certificates" path

REVIEW REQUEST REQUIREMENTS:
1. Authentication: Login with admin1/123456 credentials
2. Multi Cert Upload Test: Upload a test certificate file via POST /api/certificates/multi-upload
3. Verify Correct Path: Check that the file is uploaded to correct Google Drive path:
   - Expected path: `SUNSHINE 01/Class & Flag Cert/Certificates/[filename]`
   - NOT: `SUNSHINE 01/Certificates/[filename]` (old incorrect path)
4. Parameter Analysis: Verify backend now sends:
   - `parent_category`: "Class & Flag Cert" 
   - `category`: "Certificates"
   - `filename`: correct filename
5. Google Apps Script Response: Check upload response shows correct folder_path

EXPECTED RESULTS AFTER FIX:
- File uploaded to Google Drive successfully ✅
- Folder path in response: "SUNSHINE 01/Class & Flag Cert/Certificates" ✅  
- Certificate created in database ✅
- No "folder not found" errors ✅
"""

import requests
import json
import os
import sys
import tempfile
from datetime import datetime
import time
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
    # Fallback to external URL from frontend/.env
    BACKEND_URL = 'https://shipmatrix.preview.emergentagent.com/api'
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                    break
    except:
        pass
    print(f"Using external backend URL: {BACKEND_URL}")

class FolderPathFixTester:
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
            'user_company_identified': False,
            'test_ship_found': False,
            
            # Multi Certificate Upload Tests
            'multi_upload_endpoint_accessible': False,
            'test_file_created': False,
            'upload_request_successful': False,
            'upload_response_valid': False,
            
            # CRITICAL PATH FIX VERIFICATION
            'correct_folder_path_in_response': False,
            'parent_category_sent_correctly': False,
            'category_sent_correctly': False,
            'filename_sent_correctly': False,
            'google_drive_upload_successful': False,
            'certificate_created_in_database': False,
            
            # Path Structure Verification
            'path_contains_class_flag_cert': False,
            'path_contains_certificates_subfolder': False,
            'path_structure_correct': False,
            'old_incorrect_path_not_used': False,
            
            # Response Analysis
            'folder_path_field_present': False,
            'google_drive_file_id_present': False,
            'no_folder_not_found_errors': False,
            'upload_metadata_correct': False,
        }
        
        # Store test data
        self.test_ship = None
        self.upload_response = {}
        self.test_file_content = None
        self.test_filename = None
        
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
                user_company = self.current_user.get('company')
                if user_company:
                    self.path_fix_tests['user_company_identified'] = True
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
        """Find SUNSHINE 01 ship for testing as specified in review request"""
        try:
            self.log("🚢 Finding SUNSHINE 01 ship for testing...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships")
                
                # Look for SUNSHINE 01 specifically
                sunshine_ship = None
                for ship in ships:
                    ship_name = ship.get('name', '').upper()
                    if 'SUNSHINE' in ship_name and '01' in ship_name:
                        sunshine_ship = ship
                        break
                
                if sunshine_ship:
                    self.test_ship = sunshine_ship
                    self.path_fix_tests['test_ship_found'] = True
                    self.log("✅ SUNSHINE 01 ship found")
                    self.log(f"   Ship ID: {sunshine_ship.get('id')}")
                    self.log(f"   Ship Name: {sunshine_ship.get('name')}")
                    self.log(f"   Company: {sunshine_ship.get('company')}")
                    return True
                else:
                    # Use first available ship if SUNSHINE 01 not found
                    if ships:
                        self.test_ship = ships[0]
                        self.path_fix_tests['test_ship_found'] = True
                        self.log(f"⚠️ SUNSHINE 01 not found, using: {ships[0].get('name')}")
                        self.log(f"   Ship ID: {ships[0].get('id')}")
                        return True
                    else:
                        self.log("❌ No ships found")
                        return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding test ship: {str(e)}", "ERROR")
            return False
    
    def create_test_certificate_file(self):
        """Create a realistic test certificate PDF file for upload"""
        try:
            self.log("📄 Creating test certificate file...")
            
            # Create a realistic certificate filename
            self.test_filename = f"Safety_Management_Certificate_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Create realistic PDF-like content that will be recognized as a marine certificate
            pdf_header = b"%PDF-1.4\n"
            ship_name = self.test_ship.get('name', 'SUNSHINE 01')
            imo_number = self.test_ship.get('imo', '9415313')
            
            certificate_content = f"""
SAFETY MANAGEMENT CERTIFICATE

This is to certify that the Safety Management System of the ship named below has been audited and that the ship complies with the requirements of the International Safety Management Code.

Ship Name: {ship_name}
IMO Number: {imo_number}
Port of Registry: BELIZE
Flag: BELIZE
Gross Tonnage: 5000
Ship Type: CARGO SHIP

Certificate Number: SMC-{datetime.now().strftime('%Y%m%d')}-001
Issue Date: {datetime.now().strftime('%d/%m/%Y')}
Valid Until: {(datetime.now().replace(year=datetime.now().year + 1)).strftime('%d/%m/%Y')}

This certificate is issued under the provisions of the International Safety Management Code (ISM Code) as adopted by the International Maritime Organization by resolution A.741(18).

The Safety Management System of the above ship has been audited and found to comply with the requirements of the ISM Code.

Issued by: Panama Maritime Documentation Services
Place of Issue: PANAMA
Date of Issue: {datetime.now().strftime('%d/%m/%Y')}

This certificate is valid until: {(datetime.now().replace(year=datetime.now().year + 1)).strftime('%d/%m/%Y')}

ENDORSEMENT FOR ANNUAL VERIFICATION
This is to certify that at an annual verification required by paragraph 13.1 of the ISM Code, the ship was found to comply with the relevant provisions of the ISM Code.

Annual verification: {datetime.now().strftime('%d/%m/%Y')}
Place: PANAMA
Signature: [Authorized Officer]

This is a test certificate for Multi Certificate Upload Path Fix verification.
Expected upload path: {ship_name}/Class & Flag Cert/Certificates/{self.test_filename}
""".encode('utf-8')
            
            # Combine to create PDF-like content
            self.test_file_content = pdf_header + certificate_content + b"\n%%EOF"
            
            self.path_fix_tests['test_file_created'] = True
            self.log("✅ Test certificate file created")
            self.log(f"   Filename: {self.test_filename}")
            self.log(f"   Size: {len(self.test_file_content)} bytes")
            self.log(f"   Content type: application/pdf")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating test certificate file: {str(e)}", "ERROR")
            return False
    
    def test_multi_certificate_upload(self):
        """Test the multi-certificate upload endpoint with path fix verification"""
        try:
            self.log("📤 Testing Multi Certificate Upload with Path Fix...")
            
            if not self.test_ship or not self.test_file_content or not self.test_filename:
                self.log("❌ Missing test prerequisites")
                return False
            
            ship_id = self.test_ship.get('id')
            ship_name = self.test_ship.get('name')
            
            self.log(f"   Ship: {ship_name} (ID: {ship_id})")
            self.log(f"   File: {self.test_filename}")
            self.log("   Expected path: {ship_name}/Class & Flag Cert/Certificates/{filename}")
            
            # Prepare multipart form data
            files = {
                'files': (self.test_filename, self.test_file_content, 'application/pdf')
            }
            
            # Test the multi-upload endpoint
            endpoint = f"{BACKEND_URL}/certificates/multi-upload"
            params = {'ship_id': ship_id}
            
            self.log(f"   POST {endpoint}?ship_id={ship_id}")
            self.log("   CRITICAL TEST: Verifying backend sends correct parameters to Google Apps Script:")
            self.log("      Expected parent_category: 'Class & Flag Cert'")
            self.log("      Expected category: 'Certificates'")
            self.log("      Expected filename: correct filename")
            
            response = requests.post(
                endpoint, 
                files=files, 
                params=params,
                headers=self.get_headers(), 
                timeout=120  # Longer timeout for file upload
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.path_fix_tests['multi_upload_endpoint_accessible'] = True
                self.path_fix_tests['upload_request_successful'] = True
                self.log("✅ Multi-upload request successful")
                
                try:
                    response_data = response.json()
                    self.upload_response = response_data
                    self.path_fix_tests['upload_response_valid'] = True
                    self.log("✅ Upload response is valid JSON")
                    
                    # Log response structure for analysis
                    self.log(f"   Response keys: {list(response_data.keys())}")
                    
                    # Log detailed response for debugging
                    self.log("   Detailed response:")
                    self.log(f"      {json.dumps(response_data, indent=2)}")
                    
                    return True
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return False
            else:
                self.log(f"❌ Multi-upload request failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing multi-certificate upload: {str(e)}", "ERROR")
            return False
    
    def verify_folder_path_fix(self):
        """Verify the critical folder path fix - files should go to 'Class & Flag Cert/Certificates' not just 'Certificates'"""
        try:
            self.log("🔍 VERIFYING CRITICAL FOLDER PATH FIX...")
            
            if not self.upload_response:
                self.log("❌ No upload response to verify")
                return False
            
            ship_name = self.test_ship.get('name', 'UNKNOWN')
            expected_path = f"{ship_name}/Class & Flag Cert/Certificates"
            old_incorrect_path = f"{ship_name}/Certificates"
            
            self.log(f"   Expected correct path: {expected_path}")
            self.log(f"   Old incorrect path: {old_incorrect_path}")
            
            # Check if response contains upload results
            upload_results = self.upload_response.get('results', [])
            if not upload_results:
                self.log("❌ No upload results in response")
                return False
            
            self.log(f"   Found {len(upload_results)} upload results")
            
            path_fix_verified = False
            google_drive_success = False
            certificate_created = False
            
            for i, result in enumerate(upload_results):
                self.log(f"   Result {i+1}:")
                self.log(f"      Filename: {result.get('filename', 'Unknown')}")
                self.log(f"      Status: {result.get('status', 'Unknown')}")
                
                # Check Google Drive upload details
                google_drive_info = result.get('google_drive', {})
                if google_drive_info:
                    self.log(f"      Google Drive Info:")
                    
                    # CRITICAL: Check folder_path in response
                    folder_path = google_drive_info.get('folder_path', '')
                    file_id = google_drive_info.get('file_id', '')
                    file_url = google_drive_info.get('file_url', '')
                    
                    self.log(f"         Folder Path: '{folder_path}'")
                    self.log(f"         File ID: {file_id}")
                    self.log(f"         File URL: {file_url[:100]}..." if file_url else "         File URL: None")
                    
                    if folder_path:
                        self.path_fix_tests['folder_path_field_present'] = True
                        
                        # CRITICAL TEST: Verify correct folder path structure
                        if 'Class & Flag Cert/Certificates' in folder_path:
                            self.path_fix_tests['correct_folder_path_in_response'] = True
                            self.path_fix_tests['path_contains_class_flag_cert'] = True
                            self.path_fix_tests['path_contains_certificates_subfolder'] = True
                            self.path_fix_tests['path_structure_correct'] = True
                            path_fix_verified = True
                            self.log("         ✅ CORRECT FOLDER PATH STRUCTURE FOUND!")
                            self.log("         ✅ Contains 'Class & Flag Cert' parent category")
                            self.log("         ✅ Contains 'Certificates' subcategory")
                        else:
                            self.log("         ❌ INCORRECT FOLDER PATH - Missing 'Class & Flag Cert/Certificates'")
                            
                            # Check if it's using the old incorrect path
                            if folder_path.endswith('/Certificates') and 'Class & Flag Cert' not in folder_path:
                                self.log("         ❌ USING OLD INCORRECT PATH STRUCTURE")
                                self.log(f"         ❌ Found: {folder_path}")
                                self.log(f"         ❌ Expected: {expected_path}")
                            else:
                                self.path_fix_tests['old_incorrect_path_not_used'] = True
                    
                    if file_id:
                        self.path_fix_tests['google_drive_file_id_present'] = True
                        google_drive_success = True
                        self.log("         ✅ Google Drive file ID present - upload successful")
                    
                    # Check for upload success
                    if result.get('status') == 'success':
                        self.path_fix_tests['google_drive_upload_successful'] = True
                        self.log("         ✅ Upload status: success")
                
                # Check certificate creation
                certificate_info = result.get('certificate', {})
                if certificate_info:
                    cert_id = certificate_info.get('id')
                    if cert_id:
                        self.path_fix_tests['certificate_created_in_database'] = True
                        certificate_created = True
                        self.log(f"         ✅ Certificate created in database (ID: {cert_id})")
            
            # Verify no folder not found errors
            error_messages = []
            for result in upload_results:
                if result.get('status') != 'success':
                    error_msg = result.get('error', '')
                    if error_msg:
                        error_messages.append(error_msg)
                        if 'folder not found' in error_msg.lower():
                            self.log(f"         ❌ FOLDER NOT FOUND ERROR: {error_msg}")
                        else:
                            self.log(f"         ⚠️ Other error: {error_msg}")
            
            if not error_messages or not any('folder not found' in msg.lower() for msg in error_messages):
                self.path_fix_tests['no_folder_not_found_errors'] = True
                self.log("      ✅ No 'folder not found' errors detected")
            
            # Overall assessment
            if path_fix_verified and google_drive_success and certificate_created:
                self.log("✅ FOLDER PATH FIX VERIFICATION SUCCESSFUL")
                self.log("   ✅ Files uploaded to correct 'Class & Flag Cert/Certificates' path")
                self.log("   ✅ Google Drive upload successful")
                self.log("   ✅ Certificate created in database")
                return True
            else:
                self.log("❌ FOLDER PATH FIX VERIFICATION FAILED")
                if not path_fix_verified:
                    self.log("   ❌ Incorrect folder path structure")
                if not google_drive_success:
                    self.log("   ❌ Google Drive upload issues")
                if not certificate_created:
                    self.log("   ❌ Certificate not created in database")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying folder path fix: {str(e)}", "ERROR")
            return False
    
    def verify_backend_parameters(self):
        """Verify that backend sends correct parameters to Google Apps Script"""
        try:
            self.log("🔧 Verifying backend parameter transmission...")
            
            # This is inferred from the successful upload and correct folder path
            # We can't directly inspect the Google Apps Script call, but we can verify the results
            
            if not self.upload_response:
                self.log("❌ No upload response to analyze parameters")
                return False
            
            # Check if the upload was successful with correct parameters
            upload_results = self.upload_response.get('results', [])
            
            for result in upload_results:
                filename = result.get('filename', '')
                google_drive_info = result.get('google_drive', {})
                folder_path = google_drive_info.get('folder_path', '')
                
                self.log(f"   Analyzing result for: {filename}")
                
                # Verify filename parameter
                if filename == self.test_filename:
                    self.path_fix_tests['filename_sent_correctly'] = True
                    self.log("      ✅ Filename parameter sent correctly")
                else:
                    self.log(f"      ❌ Filename mismatch: expected {self.test_filename}, got {filename}")
                
                # Verify parent_category and category parameters (inferred from folder path)
                if 'Class & Flag Cert/Certificates' in folder_path:
                    self.path_fix_tests['parent_category_sent_correctly'] = True
                    self.path_fix_tests['category_sent_correctly'] = True
                    self.log("      ✅ parent_category: 'Class & Flag Cert' sent correctly")
                    self.log("      ✅ category: 'Certificates' sent correctly")
                    self.log("      ✅ Google Apps Script constructed correct path")
                else:
                    self.log("      ❌ Incorrect parameters sent to Google Apps Script")
                    self.log(f"      ❌ Resulting path: {folder_path}")
                    self.log("      ❌ Expected path should contain: Class & Flag Cert/Certificates")
            
            # Overall parameter verification
            if (self.path_fix_tests.get('filename_sent_correctly', False) and
                self.path_fix_tests.get('parent_category_sent_correctly', False) and
                self.path_fix_tests.get('category_sent_correctly', False)):
                self.log("✅ Backend parameter transmission verified")
                return True
            else:
                self.log("❌ Backend parameter transmission issues detected")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying backend parameters: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_path_fix_test(self):
        """Run comprehensive test of the Multi Certificate Upload folder path fix"""
        try:
            self.log("🚀 STARTING MULTI CERTIFICATE UPLOAD FOLDER PATH FIX TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find test ship
            self.log("\nSTEP 2: Finding test ship")
            if not self.find_test_ship():
                self.log("❌ CRITICAL: Test ship not found - cannot proceed")
                return False
            
            # Step 3: Create test certificate file
            self.log("\nSTEP 3: Creating test certificate file")
            if not self.create_test_certificate_file():
                self.log("❌ CRITICAL: Test file creation failed - cannot proceed")
                return False
            
            # Step 4: Test multi-certificate upload
            self.log("\nSTEP 4: Testing multi-certificate upload")
            if not self.test_multi_certificate_upload():
                self.log("❌ CRITICAL: Multi-certificate upload failed")
                return False
            
            # Step 5: Verify folder path fix
            self.log("\nSTEP 5: Verifying folder path fix")
            if not self.verify_folder_path_fix():
                self.log("❌ CRITICAL: Folder path fix verification failed")
                return False
            
            # Step 6: Verify backend parameters
            self.log("\nSTEP 6: Verifying backend parameters")
            if not self.verify_backend_parameters():
                self.log("❌ Backend parameter verification failed")
                return False
            
            self.log("\n" + "=" * 80)
            self.log("✅ MULTI CERTIFICATE UPLOAD FOLDER PATH FIX TEST COMPLETED SUCCESSFULLY")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_path_fix_test_summary(self):
        """Print comprehensive summary of folder path fix test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 MULTI CERTIFICATE UPLOAD FOLDER PATH FIX TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.path_fix_tests)
            passed_tests = sum(1 for result in self.path_fix_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Critical Path Fix Results
            self.log("🔧 CRITICAL FOLDER PATH FIX VERIFICATION:")
            critical_tests = [
                ('correct_folder_path_in_response', 'Correct folder path in response'),
                ('path_contains_class_flag_cert', 'Path contains "Class & Flag Cert"'),
                ('path_contains_certificates_subfolder', 'Path contains "Certificates" subfolder'),
                ('path_structure_correct', 'Complete path structure correct'),
                ('old_incorrect_path_not_used', 'Old incorrect path not used'),
            ]
            
            for test_key, description in critical_tests:
                status = "✅ PASS" if self.path_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Parameter Verification
            self.log("\n🔧 BACKEND PARAMETER VERIFICATION:")
            parameter_tests = [
                ('parent_category_sent_correctly', 'parent_category: "Class & Flag Cert" sent correctly'),
                ('category_sent_correctly', 'category: "Certificates" sent correctly'),
                ('filename_sent_correctly', 'filename sent correctly'),
            ]
            
            for test_key, description in parameter_tests:
                status = "✅ PASS" if self.path_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Upload Success Verification
            self.log("\n📤 UPLOAD SUCCESS VERIFICATION:")
            upload_tests = [
                ('google_drive_upload_successful', 'Google Drive upload successful'),
                ('certificate_created_in_database', 'Certificate created in database'),
                ('google_drive_file_id_present', 'Google Drive file ID present'),
                ('no_folder_not_found_errors', 'No "folder not found" errors'),
            ]
            
            for test_key, description in upload_tests:
                status = "✅ PASS" if self.path_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Technical Verification
            self.log("\n🔍 TECHNICAL VERIFICATION:")
            technical_tests = [
                ('multi_upload_endpoint_accessible', 'Multi-upload endpoint accessible'),
                ('upload_response_valid', 'Upload response valid JSON'),
                ('folder_path_field_present', 'folder_path field present in response'),
                ('upload_metadata_correct', 'Upload metadata correct'),
            ]
            
            for test_key, description in technical_tests:
                status = "✅ PASS" if self.path_fix_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL FOLDER PATH FIX ASSESSMENT:")
            
            critical_passed = sum(1 for test_key, _ in critical_tests if self.path_fix_tests.get(test_key, False))
            parameter_passed = sum(1 for test_key, _ in parameter_tests if self.path_fix_tests.get(test_key, False))
            upload_passed = sum(1 for test_key, _ in upload_tests if self.path_fix_tests.get(test_key, False))
            
            if critical_passed >= 4 and parameter_passed >= 2 and upload_passed >= 3:
                self.log("   ✅ FOLDER PATH FIX IS WORKING CORRECTLY")
                self.log("   ✅ Files are now uploaded to correct 'Class & Flag Cert/Certificates' path")
                self.log("   ✅ Backend sends correct parameters to Google Apps Script")
                self.log("   ✅ Google Apps Script constructs correct folder path")
                self.log("   ✅ Upload process completes successfully")
            else:
                self.log("   ❌ FOLDER PATH FIX MAY NOT BE COMPLETE")
                if critical_passed < 4:
                    self.log("   ❌ Critical path structure issues detected")
                if parameter_passed < 2:
                    self.log("   ❌ Backend parameter transmission issues")
                if upload_passed < 3:
                    self.log("   ❌ Upload process issues detected")
                self.log("   ❌ Further investigation needed")
            
            # Expected vs Actual Results
            if self.test_ship and self.upload_response:
                ship_name = self.test_ship.get('name', 'UNKNOWN')
                expected_path = f"{ship_name}/Class & Flag Cert/Certificates"
                
                self.log(f"\n📋 EXPECTED VS ACTUAL RESULTS:")
                self.log(f"   Expected path: {expected_path}")
                
                upload_results = self.upload_response.get('results', [])
                for result in upload_results:
                    google_drive_info = result.get('google_drive', {})
                    actual_path = google_drive_info.get('folder_path', 'NOT FOUND')
                    filename = result.get('filename', 'Unknown')
                    
                    self.log(f"   Actual path for {filename}: {actual_path}")
                    
                    if expected_path in actual_path:
                        self.log(f"      ✅ CORRECT - Path contains expected structure")
                    else:
                        self.log(f"      ❌ INCORRECT - Path does not match expected structure")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    tester = FolderPathFixTester()
    
    try:
        # Run comprehensive test
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
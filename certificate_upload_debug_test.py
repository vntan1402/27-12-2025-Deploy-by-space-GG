#!/usr/bin/env python3
"""
Certificate Multi-File Upload Workflow Debug Test
=================================================

This test specifically debugs the certificate upload workflow issues reported:
1. AI classification incorrectly categorizing certificates as "other_documents"
2. Google Drive upload failures
3. Database record creation failures

Focus: POST /api/certificates/upload-multi-files endpoint
"""

import requests
import sys
import json
import io
import os
from datetime import datetime, timezone
import time

class CertificateUploadDebugTester:
    def __init__(self, base_url="https://certmaster-ship.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.test_ship_id = None

    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=60):
        """Run a single API test with detailed logging"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Remove Content-Type for file uploads
        if files:
            headers.pop('Content-Type', None)

        self.tests_run += 1
        self.log(f"Testing {name}...")
        self.log(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}", "PASS")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}", "FAIL")
                try:
                    error_detail = response.json()
                    self.log(f"Error details: {json.dumps(error_detail, indent=2)}", "ERROR")
                except:
                    self.log(f"Error text: {response.text}", "ERROR")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}", "ERROR")
            return False, {}

    def test_authentication(self):
        """Test admin authentication"""
        self.log("=== AUTHENTICATION TEST ===")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            user_info = response.get('user', {})
            self.log(f"✅ Authentication successful")
            self.log(f"User: {user_info.get('full_name')} ({user_info.get('role')})")
            return True
        else:
            self.log("❌ Authentication failed", "ERROR")
            return False

    def test_ai_configuration(self):
        """Test AI configuration status"""
        self.log("=== AI CONFIGURATION TEST ===")
        
        success, ai_config = self.run_test(
            "Get AI Configuration",
            "GET",
            "ai-config",
            200
        )
        
        if success:
            self.log(f"AI Provider: {ai_config.get('provider', 'Not set')}")
            self.log(f"AI Model: {ai_config.get('model', 'Not set')}")
            self.log(f"Use Emergent Key: {ai_config.get('use_emergent_key', 'Not set')}")
            return True
        else:
            self.log("❌ AI configuration not accessible", "ERROR")
            return False

    def test_google_drive_configuration(self):
        """Test Google Drive configuration status"""
        self.log("=== GOOGLE DRIVE CONFIGURATION TEST ===")
        
        # Test system Google Drive config
        success, gdrive_config = self.run_test(
            "Get System Google Drive Config",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            self.log(f"Google Drive configured: {gdrive_config.get('configured', False)}")
            self.log(f"Auth method: {gdrive_config.get('auth_method', 'Not set')}")
            if gdrive_config.get('folder_id'):
                self.log(f"Folder ID: {gdrive_config.get('folder_id')}")
            if gdrive_config.get('apps_script_url'):
                self.log(f"Apps Script URL: {gdrive_config.get('apps_script_url')}")
        
        # Test Google Drive status
        success, gdrive_status = self.run_test(
            "Get System Google Drive Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            self.log(f"Google Drive status: {gdrive_status.get('status', 'Unknown')}")
            self.log(f"Status message: {gdrive_status.get('message', 'No message')}")
            return True
        else:
            self.log("❌ Google Drive configuration not accessible", "ERROR")
            return False

    def setup_test_ship(self):
        """Create a test ship for certificate upload"""
        self.log("=== SETTING UP TEST SHIP ===")
        
        # First check if we have existing ships
        success, ships = self.run_test("Get Existing Ships", "GET", "ships", 200)
        
        if success and ships:
            # Use the first existing ship
            self.test_ship_id = ships[0]['id']
            ship_name = ships[0]['name']
            self.log(f"Using existing ship: {ship_name} (ID: {self.test_ship_id})")
            return True
        
        # Create a new test ship
        ship_data = {
            "name": f"Test Certificate Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Panama",
            "ship_type": "DNV GL",
            "gross_tonnage": 50000.0,
            "deadweight": 75000.0,
            "built_year": 2020,
            "company": "Test Maritime Company"
        }
        
        success, ship = self.run_test(
            "Create Test Ship",
            "POST",
            "ships",
            200,
            data=ship_data
        )
        
        if success:
            self.test_ship_id = ship.get('id')
            self.log(f"✅ Created test ship: {ship.get('name')} (ID: {self.test_ship_id})")
            return True
        else:
            self.log("❌ Failed to create test ship", "ERROR")
            return False

    def create_test_certificate_pdf(self):
        """Create a mock PDF content that should be classified as a certificate"""
        # Create a text content that mimics a maritime certificate
        certificate_content = """
INTERNATIONAL AIR POLLUTION PREVENTION CERTIFICATE

Ship Name: TEST VESSEL ALPHA
IMO Number: IMO1234567
Flag State: Panama
Classification Society: DNV GL

Certificate Number: IAPP-2024-001
Issue Date: 01 January 2024
Valid Until: 01 January 2027

This is to certify that this ship has been surveyed in accordance with 
regulation 5 of Annex VI to the International Convention for the Prevention 
of Pollution from Ships, 1973, as modified by the Protocol of 1978 relating 
thereto, and that the survey showed that the structure, equipment, systems, 
fittings, arrangements and material of the ship and the condition thereof 
are in all respects satisfactory.

Issued by: Panama Maritime Authority
On behalf of the Government of Panama

Authorized Officer: Captain John Smith
Date: 01 January 2024
Place: Panama City

This certificate is valid until 01 January 2027 subject to surveys 
in accordance with the Convention.
"""
        return certificate_content.encode('utf-8')

    def test_certificate_upload_workflow(self):
        """Test the complete certificate upload workflow"""
        self.log("=== CERTIFICATE UPLOAD WORKFLOW TEST ===")
        
        if not self.test_ship_id:
            self.log("❌ No test ship available for certificate upload", "ERROR")
            return False
        
        # Create test certificate file
        pdf_content = self.create_test_certificate_pdf()
        
        # Prepare file for upload
        files = {
            'files': ('test_certificate.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        
        self.log(f"Uploading test certificate (size: {len(pdf_content)} bytes)")
        self.log("File content preview:")
        self.log(pdf_content.decode('utf-8')[:200] + "...")
        
        # Test the multi-file upload endpoint
        success, response = self.run_test(
            "Certificate Multi-File Upload",
            "POST",
            "certificates/upload-multi-files",
            200,
            files=files,
            timeout=120  # Longer timeout for AI processing
        )
        
        if success:
            self.log("✅ Upload request completed successfully")
            
            # Analyze the response
            results = response.get('results', [])
            if results:
                for i, result in enumerate(results):
                    self.log(f"--- File {i+1} Results ---")
                    self.log(f"Filename: {result.get('filename', 'Unknown')}")
                    self.log(f"Status: {result.get('status', 'Unknown')}")
                    
                    if result.get('status') == 'success':
                        # Check AI analysis results
                        analysis = result.get('analysis', {})
                        self.log(f"AI Analysis Results:")
                        self.log(f"  Category: {analysis.get('category', 'Not classified')}")
                        self.log(f"  Ship Name: {analysis.get('ship_name', 'Not detected')}")
                        self.log(f"  Cert Name: {analysis.get('cert_name', 'Not detected')}")
                        self.log(f"  Cert Number: {analysis.get('cert_no', 'Not detected')}")
                        self.log(f"  Issue Date: {analysis.get('issue_date', 'Not detected')}")
                        self.log(f"  Valid Date: {analysis.get('valid_date', 'Not detected')}")
                        self.log(f"  Issued By: {analysis.get('issued_by', 'Not detected')}")
                        
                        # Check Google Drive upload results
                        upload = result.get('upload', {})
                        self.log(f"Google Drive Upload:")
                        self.log(f"  Success: {upload.get('success', False)}")
                        if upload.get('success'):
                            self.log(f"  File ID: {upload.get('file_id', 'Not provided')}")
                            self.log(f"  Folder Path: {upload.get('folder_path', 'Not provided')}")
                        else:
                            self.log(f"  Error: {upload.get('error', 'Unknown error')}")
                        
                        # Check certificate record creation
                        certificate = result.get('certificate', {})
                        self.log(f"Certificate Record Creation:")
                        if certificate and isinstance(certificate, dict) and certificate.get('success', False):
                            self.log(f"  Success: True")
                            self.log(f"  Certificate ID: {certificate.get('id', 'Not provided')}")
                        else:
                            self.log(f"  Success: False")
                            if isinstance(certificate, dict):
                                self.log(f"  Error: {certificate.get('error', 'Unknown error')}")
                            else:
                                self.log(f"  Error: Certificate data is {type(certificate)}: {certificate}")
                        
                        # Analyze the issues
                        self.analyze_upload_issues(analysis, upload, certificate)
                        
                    else:
                        self.log(f"Upload failed: {result.get('message', 'Unknown error')}")
            
            return True
        else:
            self.log("❌ Certificate upload failed", "ERROR")
            return False

    def analyze_upload_issues(self, analysis, upload, certificate):
        """Analyze and report specific issues found in the upload workflow"""
        self.log("=== ISSUE ANALYSIS ===")
        
        issues_found = []
        
        # Issue 1: AI Classification
        category = analysis.get('category', '')
        if category != 'certificates':
            issues_found.append(f"❌ AI CLASSIFICATION ISSUE: Category is '{category}', should be 'certificates'")
            self.log("AI Classification Problem Detected:")
            self.log("  - The AI is not correctly identifying maritime certificates")
            self.log("  - This prevents proper database record creation")
            self.log("  - Check AI prompt and classification logic")
        else:
            self.log("✅ AI Classification: Correctly identified as 'certificates'")
        
        # Issue 2: Ship Name Detection
        ship_name = analysis.get('ship_name', '')
        if not ship_name or ship_name in ['Unknown_Ship', 'Unknown Ship', '']:
            issues_found.append(f"❌ SHIP NAME DETECTION ISSUE: Ship name is '{ship_name}'")
            self.log("Ship Name Detection Problem:")
            self.log("  - AI cannot extract ship name from certificate")
            self.log("  - This affects Google Drive folder organization")
            self.log("  - Check if certificate content contains ship name")
        else:
            self.log(f"✅ Ship Name Detection: Found '{ship_name}'")
        
        # Issue 3: Google Drive Upload
        if not upload.get('success', False):
            issues_found.append(f"❌ GOOGLE DRIVE UPLOAD ISSUE: {upload.get('error', 'Unknown error')}")
            self.log("Google Drive Upload Problem:")
            self.log(f"  - Error: {upload.get('error', 'Unknown error')}")
            self.log("  - Check Google Drive configuration")
            self.log("  - Verify Apps Script URL and folder permissions")
        else:
            self.log("✅ Google Drive Upload: Successful")
        
        # Issue 4: Certificate Record Creation
        if not certificate or not (isinstance(certificate, dict) and certificate.get('success', False)):
            error_msg = "Unknown error"
            if isinstance(certificate, dict):
                error_msg = certificate.get('error', 'Unknown error')
            elif certificate is not None:
                error_msg = f"Invalid certificate data type: {type(certificate)}"
            
            issues_found.append(f"❌ DATABASE RECORD CREATION ISSUE: {error_msg}")
            self.log("Database Record Creation Problem:")
            self.log(f"  - Error: {error_msg}")
            self.log("  - This is likely due to AI classification issues")
            self.log("  - Records are only created when category='certificates'")
        else:
            self.log("✅ Database Record Creation: Successful")
        
        # Summary
        if issues_found:
            self.log("=== ISSUES SUMMARY ===")
            for issue in issues_found:
                self.log(issue)
        else:
            self.log("✅ No issues found - certificate upload workflow working correctly")

    def test_existing_certificates(self):
        """Test retrieval of existing certificates"""
        self.log("=== EXISTING CERTIFICATES TEST ===")
        
        # Test general certificates endpoint
        success, certificates = self.run_test(
            "Get All Certificates",
            "GET",
            "certificates",
            200
        )
        
        if success:
            self.log(f"Found {len(certificates)} total certificates in system")
            
            # Show sample certificates
            for i, cert in enumerate(certificates[:3]):  # Show first 3
                self.log(f"Certificate {i+1}:")
                self.log(f"  Name: {cert.get('cert_name', 'Unknown')}")
                self.log(f"  Ship ID: {cert.get('ship_id', 'Unknown')}")
                self.log(f"  Category: {cert.get('category', 'Unknown')}")
                self.log(f"  Status: {cert.get('status', 'Unknown')}")
            
            return True
        else:
            self.log("❌ Failed to retrieve certificates", "ERROR")
            return False

    def run_comprehensive_debug(self):
        """Run comprehensive debug test for certificate upload workflow"""
        self.log("🔍 CERTIFICATE UPLOAD WORKFLOW DEBUG TEST")
        self.log("=" * 60)
        
        test_results = []
        
        # Step 1: Authentication
        if not self.test_authentication():
            self.log("❌ Cannot proceed without authentication", "ERROR")
            return False
        test_results.append(("Authentication", True))
        
        # Step 2: Check AI Configuration
        ai_config_ok = self.test_ai_configuration()
        test_results.append(("AI Configuration", ai_config_ok))
        
        # Step 3: Check Google Drive Configuration
        gdrive_config_ok = self.test_google_drive_configuration()
        test_results.append(("Google Drive Configuration", gdrive_config_ok))
        
        # Step 4: Setup test ship
        ship_setup_ok = self.setup_test_ship()
        test_results.append(("Test Ship Setup", ship_setup_ok))
        
        # Step 5: Test existing certificates
        existing_certs_ok = self.test_existing_certificates()
        test_results.append(("Existing Certificates", existing_certs_ok))
        
        # Step 6: Test certificate upload workflow (main test)
        if ship_setup_ok:
            upload_workflow_ok = self.test_certificate_upload_workflow()
            test_results.append(("Certificate Upload Workflow", upload_workflow_ok))
        else:
            self.log("⚠️ Skipping certificate upload test due to ship setup failure", "WARN")
            test_results.append(("Certificate Upload Workflow", False))
        
        # Final Results
        self.log("=" * 60)
        self.log("📊 DEBUG TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name:30} {status}")
            if result:
                passed_tests += 1
        
        self.log(f"\nOverall API Tests: {self.tests_passed}/{self.tests_run}")
        self.log(f"Feature Tests: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests and self.tests_passed == self.tests_run:
            self.log("🎉 All tests passed!")
            return True
        else:
            self.log("⚠️ Some tests failed - check logs above")
            return False

def main():
    """Main test execution"""
    tester = CertificateUploadDebugTester()
    success = tester.run_comprehensive_debug()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
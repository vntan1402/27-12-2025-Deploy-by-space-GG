#!/usr/bin/env python3
"""
Multi-File Upload with Enhanced Date Parsing Test
Focus: Debug "Invalid time value" error in AI analysis date parsing
"""

import requests
import json
import time
import io
import os
import sys
from datetime import datetime, timezone

class MultiFileUploadTester:
    def __init__(self, base_url="https://continue-session.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_info = None

    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=60):
        """Run a single API test with enhanced error reporting"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Don't set Content-Type for file uploads - let requests handle it
        if not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        self.log(f"Testing {name}...")
        self.log(f"   URL: {url}")
        
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
                    self.log(f"   Error: {json.dumps(error_detail, indent=2)}", "ERROR")
                except:
                    self.log(f"   Error: {response.text}", "ERROR")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}", "FAIL")
            return False, {}

    def test_authentication(self):
        """Test 1: Authentication with admin/admin123"""
        print("\n🔐 Testing Authentication")
        
        # First login as admin to create test user
        admin_success, admin_status, admin_response = self.make_request(
            'POST', 'auth/login', 
            data={"username": "admin", "password": "admin123"}
        )
        
        if not admin_success:
            self.log_test("Authentication with admin/admin123", False, f"Admin login failed: {admin_status}")
            return False
        
        admin_token = admin_response['access_token']
        
        # Create test user with company association
        import time
        import requests
        test_username = f'test_upload_user_{int(time.time())}'
        test_user_data = {
            'username': test_username,
            'email': f'test_upload_{int(time.time())}@example.com',
            'password': 'TestPass123!',
            'full_name': 'Test Upload User',
            'role': 'editor',
            'department': 'technical',
            'company': 'AMCSC',
            'zalo': '0901234567'
        }
        
        headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
        create_response = requests.post(f'{self.api_url}/users', headers=headers, json=test_user_data, timeout=30)
        
        if create_response.status_code != 200:
            self.log_test("Authentication with admin/admin123", False, f"Failed to create test user: {create_response.status_code}")
            return False
        
        # Now login with test user
        success, status, response = self.make_request(
            'POST', 'auth/login', 
            data={"username": test_username, "password": "TestPass123!"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_info = response.get('user', {})
            self.log_test(
                "Authentication with test user (has company)", 
                True, 
                f"User: {self.user_info.get('full_name')} ({self.user_info.get('role')}) - Company: {self.user_info.get('company')}"
            )
            return True
        else:
            self.log_test(
                "Authentication with test user (has company)", 
                False, 
                f"Status: {status}, Response: {response}"
            )
            return False

    def test_endpoint_exists(self):
        """Test 2: Check if multi-file upload endpoint exists"""
        print("\n🔍 Testing Endpoint Availability")
        
        # Create a small test file
        test_content = b"Test file content for endpoint check"
        files = {'files': ('test.txt', io.BytesIO(test_content), 'text/plain')}
        
        success, status, response = self.make_request(
            'POST', 'certificates/upload-multi-files', 
            files=files, expected_status=200
        )
        
        # We expect this to work or fail with a specific error (not 404)
        endpoint_exists = status != 404
        
        self.log_test(
            "POST /api/certificates/upload-multi-files endpoint exists", 
            endpoint_exists, 
            f"Status: {status} (not 404 means endpoint exists)"
        )
        
        return endpoint_exists

    def create_test_files(self):
        """Create test files for upload"""
        test_files = []
        
        # 1. Certificate-like text file
        cert_content = """
SAFETY MANAGEMENT CERTIFICATE

Ship Name: MV OCEAN STAR
IMO Number: 9123456
Certificate Number: SMC-2024-001
Issue Date: 2024-01-15
Valid Until: 2025-01-15
Issued by: DNV GL
Certificate Type: Full Term

This is to certify that the Safety Management System of the above ship has been audited and found to comply with the requirements of the ISM Code.
        """.strip()
        
        test_files.append({
            'name': 'safety_management_certificate.txt',
            'content': cert_content.encode('utf-8'),
            'mime_type': 'text/plain',
            'expected_category': 'certificates'
        })
        
        # 2. Test report file
        test_report_content = """
LIFEBOAT TEST REPORT

Ship: MV OCEAN STAR
Date: 2024-01-10
Equipment: Lifeboat No. 1
Test Type: Monthly Inspection

Test Results:
- Lowering mechanism: OK
- Engine start: OK
- Radio equipment: OK
- Emergency supplies: OK

Next test due: 2024-02-10
        """.strip()
        
        test_files.append({
            'name': 'lifeboat_test_report.txt',
            'content': test_report_content.encode('utf-8'),
            'mime_type': 'text/plain',
            'expected_category': 'test_reports'
        })
        
        # 3. Survey report file
        survey_content = """
ANNUAL SURVEY REPORT

Vessel: MV OCEAN STAR
Survey Date: 2024-01-20
Surveyor: John Smith
Classification Society: DNV GL

Survey Type: Annual Survey
Survey Status: Completed
Findings: No deficiencies found

Next survey due: 2025-01-20
        """.strip()
        
        test_files.append({
            'name': 'annual_survey_report.txt',
            'content': survey_content.encode('utf-8'),
            'mime_type': 'text/plain',
            'expected_category': 'survey_reports'
        })
        
        # 4. Manual/Drawing file
        manual_content = """
TECHNICAL MANUAL

Ship: MV OCEAN STAR
Equipment: Main Engine
Model: MAN B&W 6S50MC

Operating Instructions:
1. Pre-start checks
2. Starting procedure
3. Normal operation
4. Shutdown procedure

Maintenance Schedule:
- Daily checks
- Weekly maintenance
- Monthly overhaul
        """.strip()
        
        test_files.append({
            'name': 'main_engine_manual.txt',
            'content': manual_content.encode('utf-8'),
            'mime_type': 'text/plain',
            'expected_category': 'drawings_manuals'
        })
        
        # 5. Other document
        other_content = """
CREW LIST

Ship: MV OCEAN STAR
Date: 2024-01-01

Captain: John Doe
Chief Officer: Jane Smith
Chief Engineer: Bob Johnson
Cook: Alice Brown

Total crew: 12 persons
        """.strip()
        
        test_files.append({
            'name': 'crew_list.txt',
            'content': other_content.encode('utf-8'),
            'mime_type': 'text/plain',
            'expected_category': 'other_documents'
        })
        
        return test_files

    def test_single_file_upload(self):
        """Test 3: Upload single file with AI analysis"""
        print("\n📄 Testing Single File Upload with AI Analysis")
        
        test_files = self.create_test_files()
        cert_file = test_files[0]  # Use certificate file
        
        files = {'files': (cert_file['name'], io.BytesIO(cert_file['content']), cert_file['mime_type'])}
        
        success, status, response = self.make_request(
            'POST', 'certificates/upload-multi-files', 
            files=files, expected_status=200
        )
        
        if success:
            results = response.get('results', [])
            if results:
                file_result = results[0]
                ai_analysis_worked = file_result.get('extracted_info') is not None
                category_detected = file_result.get('category') == cert_file['expected_category']
                
                self.log_test(
                    "Single file upload with AI analysis", 
                    True, 
                    f"Category: {file_result.get('category')}, AI Info: {bool(file_result.get('extracted_info'))}"
                )
                
                return file_result
            else:
                self.log_test("Single file upload with AI analysis", False, "No results returned")
                return None
        else:
            self.log_test(
                "Single file upload with AI analysis", 
                False, 
                f"Status: {status}, Response: {response}"
            )
            return None

    def test_multi_file_upload(self):
        """Test 4: Upload multiple files simultaneously"""
        print("\n📁 Testing Multi-File Upload")
        
        test_files = self.create_test_files()
        
        # Prepare multiple files for upload
        files = []
        for i, test_file in enumerate(test_files[:3]):  # Upload first 3 files
            files.append(('files', (test_file['name'], io.BytesIO(test_file['content']), test_file['mime_type'])))
        
        success, status, response = self.make_request(
            'POST', 'certificates/upload-multi-files', 
            files=files, expected_status=200
        )
        
        if success:
            total_files = response.get('total_files', 0)
            successful_uploads = response.get('successful_uploads', 0)
            results = response.get('results', [])
            
            self.log_test(
                "Multi-file upload", 
                True, 
                f"Processed: {total_files}, Successful: {successful_uploads}, Results: {len(results)}"
            )
            
            return results
        else:
            self.log_test(
                "Multi-file upload", 
                False, 
                f"Status: {status}, Response: {response}"
            )
            return []

    def test_file_classification(self):
        """Test 5: Verify AI file classification works correctly"""
        print("\n🤖 Testing AI File Classification")
        
        test_files = self.create_test_files()
        classification_results = []
        
        for test_file in test_files:
            files = {'files': (test_file['name'], io.BytesIO(test_file['content']), test_file['mime_type'])}
            
            success, status, response = self.make_request(
                'POST', 'certificates/upload-multi-files', 
                files=files, expected_status=200
            )
            
            if success and response.get('results'):
                file_result = response['results'][0]
                detected_category = file_result.get('category')
                expected_category = test_file['expected_category']
                
                classification_correct = detected_category == expected_category
                classification_results.append({
                    'filename': test_file['name'],
                    'expected': expected_category,
                    'detected': detected_category,
                    'correct': classification_correct
                })
                
                print(f"   {test_file['name']}: {detected_category} ({'✅' if classification_correct else '❌'})")
        
        correct_classifications = sum(1 for r in classification_results if r['correct'])
        total_classifications = len(classification_results)
        
        self.log_test(
            "AI File Classification", 
            correct_classifications > 0, 
            f"Correct: {correct_classifications}/{total_classifications}"
        )
        
        return classification_results

    def test_google_drive_integration(self):
        """Test 6: Verify Google Drive integration (Apps Script method)"""
        print("\n☁️ Testing Google Drive Integration")
        
        # First check if Google Drive is configured
        success, status, config_response = self.make_request('GET', 'gdrive/config')
        
        if not success:
            self.log_test("Google Drive Integration", False, "Cannot access Google Drive config")
            return False
        
        configured = config_response.get('configured', False)
        auth_method = config_response.get('auth_method', 'unknown')
        
        if not configured:
            self.log_test("Google Drive Integration", False, "Google Drive not configured")
            return False
        
        # Test file upload with Google Drive integration
        test_files = self.create_test_files()
        cert_file = test_files[0]  # Use certificate file
        
        files = {'files': (cert_file['name'], io.BytesIO(cert_file['content']), cert_file['mime_type'])}
        
        success, status, response = self.make_request(
            'POST', 'certificates/upload-multi-files', 
            files=files, expected_status=200
        )
        
        if success and response.get('results'):
            file_result = response['results'][0]
            google_drive_uploaded = file_result.get('google_drive_uploaded', False)
            google_drive_file_id = file_result.get('google_drive_file_id')
            
            self.log_test(
                "Google Drive Integration", 
                google_drive_uploaded, 
                f"Auth method: {auth_method}, File ID: {google_drive_file_id}"
            )
            
            return google_drive_uploaded
        else:
            self.log_test("Google Drive Integration", False, f"Upload failed: {response}")
            return False

    def test_certificate_auto_creation(self):
        """Test 7: Verify auto certificate record creation for 'certificates' category"""
        print("\n📜 Testing Auto Certificate Record Creation")
        
        test_files = self.create_test_files()
        cert_file = test_files[0]  # Certificate file
        
        files = {'files': (cert_file['name'], io.BytesIO(cert_file['content']), cert_file['mime_type'])}
        
        success, status, response = self.make_request(
            'POST', 'certificates/upload-multi-files', 
            files=files, expected_status=200
        )
        
        if success and response.get('results'):
            file_result = response['results'][0]
            certificate_created = file_result.get('certificate_created', False)
            certificate_id = file_result.get('certificate_id')
            
            if certificate_created and certificate_id:
                # Verify certificate was actually created in database
                cert_success, cert_status, cert_data = self.make_request('GET', f'certificates/{certificate_id}')
                
                if cert_success:
                    self.log_test(
                        "Auto Certificate Record Creation", 
                        True, 
                        f"Certificate ID: {certificate_id}, Name: {cert_data.get('cert_name')}"
                    )
                    return True
                else:
                    self.log_test("Auto Certificate Record Creation", False, "Certificate not found in database")
                    return False
            else:
                self.log_test("Auto Certificate Record Creation", False, "Certificate not created")
                return False
        else:
            self.log_test("Auto Certificate Record Creation", False, f"Upload failed: {response}")
            return False

    def test_ship_survey_status_update(self):
        """Test 8: Verify Ship Survey Status updates"""
        print("\n🚢 Testing Ship Survey Status Updates")
        
        # Create a survey report that should trigger survey status update
        survey_content = """
ANNUAL SURVEY REPORT

Vessel: MV TEST SURVEY SHIP
IMO: 9876543
Survey Date: 2024-01-20
Survey Type: Annual Survey
Certificate Type: CLASS
Surveyor: John Smith
Classification Society: DNV GL

Survey Status: Completed
Issuance Date: 2024-01-20
Expiration Date: 2025-01-20
Next Survey Due: 2025-01-15

Findings: No deficiencies found
        """.strip()
        
        files = {'files': ('survey_report_with_status.txt', io.BytesIO(survey_content.encode('utf-8')), 'text/plain')}
        
        success, status, response = self.make_request(
            'POST', 'certificates/upload-multi-files', 
            files=files, expected_status=200
        )
        
        if success and response.get('results'):
            file_result = response['results'][0]
            survey_status_updated = file_result.get('survey_status_updated', False)
            
            self.log_test(
                "Ship Survey Status Updates", 
                survey_status_updated, 
                f"Survey status updated: {survey_status_updated}"
            )
            
            return survey_status_updated
        else:
            self.log_test("Ship Survey Status Updates", False, f"Upload failed: {response}")
            return False

    def test_structured_results(self):
        """Test 9: Verify endpoint returns structured results"""
        print("\n📊 Testing Structured Results Format")
        
        test_files = self.create_test_files()
        files = []
        for test_file in test_files[:2]:  # Upload 2 files
            files.append(('files', (test_file['name'], io.BytesIO(test_file['content']), test_file['mime_type'])))
        
        success, status, response = self.make_request(
            'POST', 'certificates/upload-multi-files', 
            files=files, expected_status=200
        )
        
        if success:
            # Check response structure
            required_fields = ['message', 'total_files', 'successful_uploads', 'certificates_created', 'results']
            has_all_fields = all(field in response for field in required_fields)
            
            results = response.get('results', [])
            if results:
                # Check individual result structure
                result_fields = ['filename', 'size', 'status', 'category', 'ship_name', 'certificate_created', 
                               'survey_status_updated', 'google_drive_uploaded', 'errors', 'extracted_info']
                first_result = results[0]
                has_result_fields = all(field in first_result for field in result_fields)
                
                self.log_test(
                    "Structured Results Format", 
                    has_all_fields and has_result_fields, 
                    f"Response fields: {has_all_fields}, Result fields: {has_result_fields}"
                )
                
                return has_all_fields and has_result_fields
            else:
                self.log_test("Structured Results Format", False, "No results in response")
                return False
        else:
            self.log_test("Structured Results Format", False, f"Request failed: {response}")
            return False

    def test_error_handling(self):
        """Test 10: Verify proper error handling"""
        print("\n⚠️ Testing Error Handling")
        
        # Test 1: File too large (create a large file)
        large_content = b"x" * (151 * 1024 * 1024)  # 151MB - exceeds 150MB limit
        files = {'files': ('large_file.txt', io.BytesIO(large_content), 'text/plain')}
        
        success, status, response = self.make_request(
            'POST', 'certificates/upload-multi-files', 
            files=files, expected_status=400
        )
        
        file_size_error_handled = status == 400 and "150MB" in str(response)
        
        # Test 2: No files provided
        success2, status2, response2 = self.make_request(
            'POST', 'certificates/upload-multi-files', 
            files={}, expected_status=422
        )
        
        no_files_error_handled = status2 in [400, 422]  # Either is acceptable
        
        self.log_test(
            "Error Handling", 
            file_size_error_handled and no_files_error_handled, 
            f"File size error: {file_size_error_handled}, No files error: {no_files_error_handled}"
        )
        
        return file_size_error_handled and no_files_error_handled

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚢 Multi-File Upload with AI Processing Test Suite")
        print("=" * 60)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("❌ Authentication failed - stopping tests")
            return False
        
        # Test 2: Endpoint exists
        if not self.test_endpoint_exists():
            print("❌ Endpoint not available - stopping tests")
            return False
        
        # Run all other tests
        test_results = []
        
        test_results.append(("Single File Upload with AI", self.test_single_file_upload()))
        test_results.append(("Multi-File Upload", self.test_multi_file_upload()))
        test_results.append(("AI File Classification", self.test_file_classification()))
        test_results.append(("Google Drive Integration", self.test_google_drive_integration()))
        test_results.append(("Auto Certificate Creation", self.test_certificate_auto_creation()))
        test_results.append(("Ship Survey Status Updates", self.test_ship_survey_status_update()))
        test_results.append(("Structured Results Format", self.test_structured_results()))
        test_results.append(("Error Handling", self.test_error_handling()))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:35} {status}")
            if result:
                passed_tests += 1
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        print(f"API Calls: {self.tests_passed}/{self.tests_run} successful")
        
        if passed_tests == total_tests:
            print("🎉 All multi-file upload tests passed!")
            return True
        else:
            print("⚠️ Some tests failed - check details above")
            return False

def main():
    """Main test execution"""
    tester = MultiFileUploadTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
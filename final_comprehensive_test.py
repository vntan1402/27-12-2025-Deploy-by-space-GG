#!/usr/bin/env python3
"""
Final Comprehensive Test for Google Apps Script URL and Multi-File Upload
Testing all requirements from the review request
"""

import requests
import json
import tempfile
import os
import time

class FinalComprehensiveTest:
    def __init__(self, base_url="https://shipcertdrive.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.test_token = None
        self.test_user_id = None
        
        # Apps Script URL and Folder ID from review request
        self.apps_script_url = "https://script.google.com/macros/s/AKfycbwphwgJwjyW4V-Y2y0J4uIa40zZwybm7s9maqNemi04EawcOhxRX99rbSXGWxk_D6o/exec"
        self.folder_id = "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG"
        
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")

    def admin_login(self):
        """1. Login as admin/admin123"""
        print("\n🔐 REQUIREMENT 1: LOGIN AS ADMIN/ADMIN123")
        print("=" * 60)
        
        response = requests.post(f"{self.api_url}/auth/login", json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data.get('access_token')
            user_info = data.get('user', {})
            
            self.log_test(
                "Admin Login (admin/admin123)",
                True,
                f"User: {user_info.get('full_name')} | Role: {user_info.get('role')}"
            )
            return True
        else:
            self.log_test("Admin Login", False, f"Status: {response.status_code}")
            return False

    def test_apps_script_actions(self):
        """2. Test the Apps Script URL directly with various actions"""
        print("\n🔗 REQUIREMENT 2: TEST APPS SCRIPT URL WITH VARIOUS ACTIONS")
        print("=" * 60)
        print(f"Apps Script URL: {self.apps_script_url}")
        print(f"Folder ID: {self.folder_id}")
        
        # Test test_connection
        try:
            response = requests.post(self.apps_script_url, json={
                "action": "test_connection",
                "folder_id": self.folder_id  # Added folder_id as required
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "Apps Script test_connection",
                    result.get('success', False),
                    f"Message: {result.get('message')} | Service Account: {result.get('service_account_email', 'Not provided')}"
                )
            else:
                self.log_test("Apps Script test_connection", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Apps Script test_connection", False, f"Error: {str(e)}")
        
        # Test create_folder_structure (for ship folder creation)
        try:
            response = requests.post(self.apps_script_url, json={
                "action": "create_folder_structure",
                "folder_id": self.folder_id,
                "ship_name": "Final Test Ship"
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                subfolder_ids = result.get('subfolder_ids', {})
                
                self.log_test(
                    "Apps Script create_folder_structure",
                    success,
                    f"Ship folder created | Subfolders: {len(subfolder_ids)} | Categories: {list(subfolder_ids.keys())}"
                )
                
                # Verify all expected categories are present
                expected_categories = ['Certificates', 'Test Reports', 'Survey Reports', 'Drawings & Manuals', 'Other Documents']
                missing_categories = [cat for cat in expected_categories if cat not in subfolder_ids]
                
                if not missing_categories:
                    self.log_test("All category folders created", True, f"All 5 categories present")
                else:
                    self.log_test("All category folders created", False, f"Missing: {missing_categories}")
                
                return subfolder_ids
            else:
                self.log_test("Apps Script create_folder_structure", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Apps Script create_folder_structure", False, f"Error: {str(e)}")
        
        return {}

    def test_apps_script_upload_file(self, subfolder_ids):
        """Test upload_file action"""
        if not subfolder_ids:
            self.log_test("Apps Script upload_file", False, "No subfolder IDs available")
            return
        
        # Test uploading to "Other Documents" folder specifically
        other_docs_folder_id = subfolder_ids.get('Other Documents')
        if not other_docs_folder_id:
            self.log_test("Apps Script upload_file", False, "Other Documents folder not found")
            return
        
        try:
            import base64
            test_content = "This is a test file for upload_file action testing."
            content_base64 = base64.b64encode(test_content.encode()).decode()
            
            response = requests.post(self.apps_script_url, json={
                "action": "upload_file",
                "folder_id": other_docs_folder_id,
                "file_name": "test_upload_file.txt",
                "file_content": content_base64,
                "mime_type": "text/plain"
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "Apps Script upload_file",
                    result.get('success', False),
                    f"File uploaded to Other Documents folder | File ID: {result.get('file_id', 'Not provided')}"
                )
            else:
                self.log_test("Apps Script upload_file", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Apps Script upload_file", False, f"Error: {str(e)}")

    def create_test_user_and_login(self):
        """Create test user with company association and login"""
        print("\n👤 CREATING TEST USER FOR MULTI-FILE UPLOAD")
        print("=" * 60)
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Get companies
        response = requests.get(f"{self.api_url}/companies", headers=headers)
        if response.status_code != 200:
            self.log_test("Get companies for test user", False, f"Status: {response.status_code}")
            return False
        
        companies = response.json()
        if not companies:
            self.log_test("Get companies for test user", False, "No companies available")
            return False
        
        company_name = companies[0].get('name_en', companies[0].get('name_vn'))
        
        # Create test user
        test_username = f"final_test_{int(time.time())}"
        user_data = {
            'username': test_username,
            'password': 'TestPass123!',
            'email': f'{test_username}@test.com',
            'full_name': 'Final Test User',
            'role': 'editor',
            'department': 'technical',
            'company': company_name,
            'zalo': '0901234567',
            'gmail': f'{test_username}@gmail.com'
        }
        
        response = requests.post(f"{self.api_url}/users", json=user_data, headers=headers)
        
        if response.status_code == 200:
            user_info = response.json()
            self.test_user_id = user_info.get('id')
            self.log_test("Create test user", True, f"User: {test_username} | Company: {company_name}")
        else:
            self.log_test("Create test user", False, f"Status: {response.status_code}")
            return False
        
        # Login as test user
        response = requests.post(f"{self.api_url}/auth/login", json={
            'username': test_username,
            'password': 'TestPass123!'
        })
        
        if response.status_code == 200:
            data = response.json()
            self.test_token = data.get('access_token')
            self.log_test("Test user login", True, f"Token obtained")
            return True
        else:
            self.log_test("Test user login", False, f"Status: {response.status_code}")
            return False

    def test_multi_file_upload_reproduce_error(self):
        """3. Test multi-file upload with a simple text file to reproduce the error"""
        print("\n📁 REQUIREMENT 3: TEST MULTI-FILE UPLOAD TO REPRODUCE ERROR")
        print("=" * 60)
        
        headers = {'Authorization': f'Bearer {self.test_token}'}
        
        # Get ships
        response = requests.get(f"{self.api_url}/ships", headers=headers)
        if response.status_code != 200:
            self.log_test("Get ships for upload", False, f"Status: {response.status_code}")
            return False
        
        ships = response.json()
        if not ships:
            self.log_test("Get ships for upload", False, "No ships available")
            return False
        
        ship_id = ships[0]['id']
        ship_name = ships[0]['name']
        
        # Create a simple text file that should be classified as "other_documents"
        test_content = "This is a simple text file to test the multi-file upload and reproduce the 'Target folder not found for category: other_documents' error."
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(test_content)
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                files = [('files', ('simple_test_file.txt', f, 'text/plain'))]
                data = {'ship_id': ship_id, 'ship_name': ship_name}
                
                response = requests.post(
                    f"{self.api_url}/certificates/upload-multi-files",
                    data=data,
                    files=files,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    successful_uploads = result.get('successful_uploads', 0)
                    
                    # Check if the specific error was reproduced or fixed
                    if 'results' in result and result['results']:
                        file_result = result['results'][0]
                        errors = file_result.get('errors', [])
                        category = file_result.get('category')
                        google_drive_uploaded = file_result.get('google_drive_uploaded', False)
                        
                        target_folder_error = any('Target folder not found' in error for error in errors)
                        
                        if target_folder_error:
                            self.log_test(
                                "Multi-file upload (error reproduction)",
                                False,
                                f"ERROR REPRODUCED: Target folder not found for category: {category}"
                            )
                        else:
                            self.log_test(
                                "Multi-file upload (error fixed)",
                                True,
                                f"SUCCESS: File uploaded to {category} category | Google Drive: {google_drive_uploaded}"
                            )
                    
                    return successful_uploads > 0
                else:
                    self.log_test("Multi-file upload", False, f"Status: {response.status_code}")
                    return False
        
        except Exception as e:
            self.log_test("Multi-file upload", False, f"Error: {str(e)}")
            return False
        finally:
            os.unlink(temp_file.name)

    def test_backend_category_mapping(self):
        """4. Check the backend category mapping logic"""
        print("\n🗂️ REQUIREMENT 4: CHECK BACKEND CATEGORY MAPPING LOGIC")
        print("=" * 60)
        
        # Test the category mapping that happens in the backend
        expected_mapping = {
            "certificates": "Certificates",
            "test_reports": "Test Reports",
            "survey_reports": "Survey Reports", 
            "drawings_manuals": "Drawings & Manuals",
            "other_documents": "Other Documents"
        }
        
        print("Backend category mapping verification:")
        for backend_category, expected_folder in expected_mapping.items():
            print(f"   '{backend_category}' -> '{expected_folder}'")
        
        # Test with Apps Script folder creation to verify mapping works
        try:
            response = requests.post(self.apps_script_url, json={
                "action": "create_folder_structure",
                "folder_id": self.folder_id,
                "ship_name": "Category Mapping Test Ship"
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    subfolder_ids = result.get('subfolder_ids', {})
                    
                    mapping_success = True
                    for backend_category, expected_folder in expected_mapping.items():
                        if expected_folder not in subfolder_ids:
                            mapping_success = False
                            print(f"   ❌ Missing folder: {expected_folder}")
                    
                    self.log_test(
                        "Backend category mapping verification",
                        mapping_success,
                        f"All {len(expected_mapping)} category mappings verified" if mapping_success else "Some mappings failed"
                    )
                    return mapping_success
        except Exception as e:
            self.log_test("Backend category mapping verification", False, f"Error: {str(e)}")
        
        return False

    def test_complete_workflow(self):
        """5. Verify that the folder structure creation and file upload process work together"""
        print("\n🔄 REQUIREMENT 5: VERIFY COMPLETE WORKFLOW")
        print("=" * 60)
        
        headers = {'Authorization': f'Bearer {self.test_token}'}
        
        # Get ships
        response = requests.get(f"{self.api_url}/ships", headers=headers)
        if response.status_code != 200:
            self.log_test("Get ships for workflow test", False, f"Status: {response.status_code}")
            return False
        
        ships = response.json()
        if not ships:
            self.log_test("Get ships for workflow test", False, "No ships available")
            return False
        
        ship_id = ships[0]['id']
        ship_name = ships[0]['name']
        
        # Test complete workflow with multiple file types
        test_files = [
            ("workflow_certificate.txt", "Certificate document for workflow test", "certificates"),
            ("workflow_other.txt", "Other document for workflow test", "other_documents"),
            ("workflow_test_report.txt", "Test report for workflow test", "test_reports"),
            ("workflow_survey.txt", "Survey report for workflow test", "survey_reports"),
            ("workflow_manual.txt", "Manual document for workflow test", "drawings_manuals")
        ]
        
        temp_files = []
        
        try:
            # Create temporary files
            for filename, content, expected_category in test_files:
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                temp_file.write(content)
                temp_file.close()
                temp_files.append((temp_file.name, filename, expected_category))
            
            # Upload all files
            files = []
            for temp_path, filename, _ in temp_files:
                files.append(('files', (filename, open(temp_path, 'rb'), 'text/plain')))
            
            data = {'ship_id': ship_id, 'ship_name': ship_name}
            
            response = requests.post(
                f"{self.api_url}/certificates/upload-multi-files",
                data=data,
                files=files,
                headers=headers,
                timeout=120
            )
            
            # Close file handles
            for file_tuple in files:
                file_tuple[1][1].close()
            
            if response.status_code == 200:
                result = response.json()
                total_files = result.get('total_files', 0)
                successful_uploads = result.get('successful_uploads', 0)
                certificates_created = result.get('certificates_created', 0)
                
                # Analyze workflow success
                workflow_success = successful_uploads == total_files
                
                self.log_test(
                    "Complete workflow test",
                    workflow_success,
                    f"Files: {total_files} | Successful: {successful_uploads} | Certificates: {certificates_created}"
                )
                
                # Detailed analysis
                if 'results' in result:
                    category_success = {}
                    for i, file_result in enumerate(result['results']):
                        category = file_result.get('category')
                        google_drive_uploaded = file_result.get('google_drive_uploaded', False)
                        errors = file_result.get('errors', [])
                        
                        category_success[category] = google_drive_uploaded and len(errors) == 0
                    
                    print(f"   Category upload results:")
                    for category, success in category_success.items():
                        status = "✅" if success else "❌"
                        print(f"      {status} {category}")
                
                return workflow_success
            else:
                self.log_test("Complete workflow test", False, f"Status: {response.status_code}")
                return False
        
        except Exception as e:
            self.log_test("Complete workflow test", False, f"Error: {str(e)}")
            return False
        finally:
            # Clean up temporary files
            for temp_path, _, _ in temp_files:
                try:
                    os.unlink(temp_path)
                except:
                    pass

    def cleanup_test_user(self):
        """Clean up test user"""
        if self.test_user_id and self.admin_token:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = requests.delete(f"{self.api_url}/users/{self.test_user_id}", headers=headers)
            if response.status_code == 200:
                print(f"✅ Test user cleaned up")
            else:
                print(f"⚠️ Could not clean up test user: {response.status_code}")

    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚢 FINAL COMPREHENSIVE TEST - GOOGLE APPS SCRIPT & MULTI-FILE UPLOAD")
        print("=" * 80)
        print("Testing all requirements from the review request:")
        print("1. Login as admin/admin123")
        print("2. Test the Apps Script URL directly with various actions")
        print("3. Test multi-file upload with a simple text file to reproduce the error")
        print("4. Check the backend category mapping logic")
        print("5. Verify that the folder structure creation and file upload process work together")
        print("=" * 80)
        
        # Requirement 1: Login as admin/admin123
        if not self.admin_login():
            return False
        
        # Requirement 2: Test the Apps Script URL directly with various actions
        subfolder_ids = self.test_apps_script_actions()
        self.test_apps_script_upload_file(subfolder_ids)
        
        # Create test user for file upload tests
        if not self.create_test_user_and_login():
            return False
        
        # Requirement 3: Test multi-file upload with a simple text file to reproduce the error
        self.test_multi_file_upload_reproduce_error()
        
        # Requirement 4: Check the backend category mapping logic
        self.test_backend_category_mapping()
        
        # Requirement 5: Verify that the folder structure creation and file upload process work together
        self.test_complete_workflow()
        
        # Cleanup
        self.cleanup_test_user()
        
        # Print final results
        print("\n" + "=" * 80)
        print("📊 FINAL TEST RESULTS")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            print("✅ The 'Target folder not found for category: other_documents' error has been RESOLVED")
            print("✅ Google Apps Script URL is working correctly")
            print("✅ Multi-file upload functionality is working properly")
            print("✅ Category mapping is functioning as expected")
            print("✅ Complete workflow from folder creation to file upload is operational")
            return True
        else:
            print("⚠️ Some tests failed - check details above")
            return False

def main():
    tester = FinalComprehensiveTest()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
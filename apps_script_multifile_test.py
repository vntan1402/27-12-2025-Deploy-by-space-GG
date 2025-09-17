#!/usr/bin/env python3
"""
Google Apps Script URL and Multi-File Upload Testing
Testing the new Google Apps Script URL and debugging the "Target folder not found for category: other_documents" error.
"""

import requests
import json
import time
import tempfile
import os
from datetime import datetime, timezone

class AppsScriptMultiFileUploadTester:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        
        # Apps Script URL from review request
        self.apps_script_url = "https://script.google.com/macros/s/AKfycbwphwgJwjyW4V-Y2y0J4uIa40zZwybm7s9maqNemi04EawcOhxRX99rbSXGWxk_D6o/exec"
        self.folder_id = "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG"

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

    def make_request(self, method, endpoint, data=None, files=None, timeout=30):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if files is None and data is not None:
            headers['Content-Type'] = 'application/json'

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
            
            return response
        except Exception as e:
            print(f"   Request error: {str(e)}")
            return None

    def test_login(self):
        """Test login as admin/admin123"""
        print("\n🔐 TESTING AUTHENTICATION")
        print("=" * 50)
        
        response = self.make_request('POST', 'auth/login', {
            'username': 'admin',
            'password': 'admin123'
        })
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get('access_token')
                self.admin_user_id = data.get('user', {}).get('id')
                user_info = data.get('user', {})
                
                self.log_test(
                    "Admin Login (admin/admin123)",
                    True,
                    f"User: {user_info.get('full_name')} | Role: {user_info.get('role')} | Company: {user_info.get('company')}"
                )
                return True
            except Exception as e:
                self.log_test("Admin Login", False, f"JSON parse error: {str(e)}")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("Admin Login", False, f"Status: {status}")
            return False

    def test_apps_script_direct(self):
        """Test the Apps Script URL directly with various actions"""
        print("\n🔗 TESTING APPS SCRIPT URL DIRECTLY")
        print("=" * 50)
        print(f"Apps Script URL: {self.apps_script_url}")
        print(f"Folder ID: {self.folder_id}")
        
        # Test 1: test_connection
        print("\n1. Testing test_connection action...")
        try:
            response = requests.post(self.apps_script_url, 
                json={"action": "test_connection"},
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.log_test(
                        "Apps Script test_connection",
                        result.get('success', False),
                        f"Message: {result.get('message', 'No message')} | Service Account: {result.get('service_account_email', 'Not provided')}"
                    )
                except json.JSONDecodeError:
                    self.log_test("Apps Script test_connection", False, f"Invalid JSON response: {response.text[:200]}")
            else:
                self.log_test("Apps Script test_connection", False, f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            self.log_test("Apps Script test_connection", False, f"Request failed: {str(e)}")
        
        # Test 2: create_folder_structure
        print("\n2. Testing create_folder_structure action...")
        try:
            response = requests.post(self.apps_script_url,
                json={
                    "action": "create_folder_structure",
                    "folder_id": self.folder_id,
                    "ship_name": "Test Ship for Folder Creation"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.log_test(
                        "Apps Script create_folder_structure",
                        result.get('success', False),
                        f"Message: {result.get('message', 'No message')} | Subfolder IDs: {result.get('subfolder_ids', {})}"
                    )
                    return result.get('subfolder_ids', {})
                except json.JSONDecodeError:
                    self.log_test("Apps Script create_folder_structure", False, f"Invalid JSON response: {response.text[:200]}")
            else:
                self.log_test("Apps Script create_folder_structure", False, f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            self.log_test("Apps Script create_folder_structure", False, f"Request failed: {str(e)}")
        
        return {}

    def test_apps_script_upload_file(self, subfolder_ids):
        """Test upload_file action with Apps Script"""
        print("\n3. Testing upload_file action...")
        
        # Create a simple test file
        test_content = f"Test document content created at {datetime.now()}\nThis is a test file for category mapping."
        
        try:
            response = requests.post(self.apps_script_url,
                json={
                    "action": "upload_file",
                    "folder_id": self.folder_id,
                    "file_name": "test_other_document.txt",
                    "file_content": test_content,
                    "category": "Other Documents",  # Note: This should map to "other_documents" in backend
                    "subfolder_ids": subfolder_ids
                },
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.log_test(
                        "Apps Script upload_file",
                        result.get('success', False),
                        f"Message: {result.get('message', 'No message')} | File ID: {result.get('file_id', 'Not provided')}"
                    )
                    return result.get('success', False)
                except json.JSONDecodeError:
                    self.log_test("Apps Script upload_file", False, f"Invalid JSON response: {response.text[:200]}")
            else:
                self.log_test("Apps Script upload_file", False, f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            self.log_test("Apps Script upload_file", False, f"Request failed: {str(e)}")
        
        return False

    def test_backend_gdrive_config(self):
        """Test backend Google Drive configuration"""
        print("\n⚙️ TESTING BACKEND GDRIVE CONFIGURATION")
        print("=" * 50)
        
        # Test 1: Get current config
        response = self.make_request('GET', 'gdrive/config')
        if response and response.status_code == 200:
            try:
                config = response.json()
                self.log_test(
                    "Get Google Drive Config",
                    True,
                    f"Configured: {config.get('configured')} | Auth Method: {config.get('auth_method')} | Folder ID: {config.get('folder_id')}"
                )
            except Exception as e:
                self.log_test("Get Google Drive Config", False, f"JSON parse error: {str(e)}")
        else:
            status = response.status_code if response else "No response"
            self.log_test("Get Google Drive Config", False, f"Status: {status}")
        
        # Test 2: Configure Apps Script proxy
        response = self.make_request('POST', 'gdrive/configure-proxy', {
            'web_app_url': self.apps_script_url,
            'folder_id': self.folder_id
        })
        
        if response and response.status_code == 200:
            try:
                result = response.json()
                self.log_test(
                    "Configure Apps Script Proxy",
                    result.get('success', False),
                    f"Message: {result.get('message')} | Service Account: {result.get('service_account_email')}"
                )
                return True
            except Exception as e:
                self.log_test("Configure Apps Script Proxy", False, f"JSON parse error: {str(e)}")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', response.text[:200])
                except:
                    error_msg = response.text[:200]
            self.log_test("Configure Apps Script Proxy", False, f"Status: {status} | Error: {error_msg}")
        
        return False

    def create_test_files(self):
        """Create test files for multi-file upload"""
        test_files = []
        
        # Create different types of test files
        file_types = [
            ("test_certificate.txt", "This is a test certificate document for testing category mapping.", "text/plain"),
            ("test_other_document.txt", "This is a test other document for testing the error case.", "text/plain"),
            ("test_inspection_report.txt", "This is a test inspection report document.", "text/plain")
        ]
        
        for filename, content, mime_type in file_types:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.write(content)
            temp_file.close()
            
            test_files.append({
                'filename': filename,
                'path': temp_file.name,
                'content': content,
                'mime_type': mime_type
            })
        
        return test_files

    def test_multi_file_upload(self):
        """Test multi-file upload to reproduce the error"""
        print("\n📁 TESTING MULTI-FILE UPLOAD")
        print("=" * 50)
        
        # First, get ships to upload files for
        response = self.make_request('GET', 'ships')
        if not response or response.status_code != 200:
            self.log_test("Get Ships for Upload", False, "Cannot get ships list")
            return False
        
        try:
            ships = response.json()
            if not ships:
                self.log_test("Get Ships for Upload", False, "No ships available")
                return False
            
            ship_id = ships[0]['id']
            ship_name = ships[0]['name']
            self.log_test("Get Ships for Upload", True, f"Using ship: {ship_name} (ID: {ship_id})")
        except Exception as e:
            self.log_test("Get Ships for Upload", False, f"JSON parse error: {str(e)}")
            return False
        
        # Create test files
        test_files = self.create_test_files()
        
        try:
            # Prepare files for upload
            files = []
            for i, test_file in enumerate(test_files):
                files.append(('files', (test_file['filename'], open(test_file['path'], 'rb'), test_file['mime_type'])))
            
            # Prepare form data
            form_data = {
                'ship_id': ship_id,
                'ship_name': ship_name
            }
            
            print(f"Uploading {len(files)} files for ship: {ship_name}")
            
            # Test multi-file upload endpoint
            response = self.make_request('POST', 'certificates/upload-multi-files', data=form_data, files=files, timeout=60)
            
            if response and response.status_code == 200:
                try:
                    result = response.json()
                    self.log_test(
                        "Multi-File Upload",
                        True,
                        f"Total files: {result.get('total_files')} | Successful: {result.get('successful_uploads')} | Certificates created: {result.get('certificates_created')}"
                    )
                    
                    # Check for specific error messages
                    if 'results' in result:
                        for file_result in result['results']:
                            filename = file_result.get('filename', 'Unknown')
                            success = file_result.get('success', False)
                            error = file_result.get('error', '')
                            
                            if 'Target folder not found for category' in error:
                                print(f"   🎯 FOUND TARGET ERROR: {filename} - {error}")
                            elif not success:
                                print(f"   ⚠️ File failed: {filename} - {error}")
                            else:
                                print(f"   ✅ File success: {filename}")
                    
                    return True
                except Exception as e:
                    self.log_test("Multi-File Upload", False, f"JSON parse error: {str(e)}")
            else:
                status = response.status_code if response else "No response"
                error_msg = ""
                if response:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('detail', response.text[:500])
                    except:
                        error_msg = response.text[:500]
                self.log_test("Multi-File Upload", False, f"Status: {status} | Error: {error_msg}")
            
        except Exception as e:
            self.log_test("Multi-File Upload", False, f"Upload error: {str(e)}")
        finally:
            # Clean up temporary files
            for test_file in test_files:
                try:
                    os.unlink(test_file['path'])
                except:
                    pass
        
        return False

    def test_category_mapping(self):
        """Test backend category mapping logic"""
        print("\n🗂️ TESTING CATEGORY MAPPING LOGIC")
        print("=" * 50)
        
        # Check if there's an endpoint to get category mappings
        response = self.make_request('GET', 'categories')
        if response and response.status_code == 200:
            try:
                categories = response.json()
                self.log_test("Get Categories", True, f"Found {len(categories)} categories")
                for category in categories:
                    print(f"   - {category}")
            except Exception as e:
                self.log_test("Get Categories", False, f"JSON parse error: {str(e)}")
        else:
            self.log_test("Get Categories", False, "Categories endpoint not available or failed")
        
        # Test specific category mappings that might be causing issues
        category_tests = [
            "certificates",
            "other_documents", 
            "Other Documents",
            "inspection_reports",
            "test_reports",
            "drawings_manuals"
        ]
        
        print("\nTesting category name variations:")
        for category in category_tests:
            print(f"   - Testing category: '{category}'")
            # This would need a specific endpoint to test category validation
            # For now, just log what we're testing

    def test_folder_structure_creation(self):
        """Test folder structure creation and file upload workflow"""
        print("\n📂 TESTING FOLDER STRUCTURE CREATION WORKFLOW")
        print("=" * 50)
        
        # Test the complete workflow
        subfolder_ids = self.test_apps_script_direct()
        
        if subfolder_ids:
            print(f"\nSubfolder IDs received: {subfolder_ids}")
            
            # Test if "other_documents" folder was created
            if "other_documents" in subfolder_ids:
                self.log_test("Other Documents Folder Created", True, f"Folder ID: {subfolder_ids['other_documents']}")
            else:
                self.log_test("Other Documents Folder Created", False, f"Available folders: {list(subfolder_ids.keys())}")
            
            # Test file upload with folder structure
            upload_success = self.test_apps_script_upload_file(subfolder_ids)
            return upload_success
        
        return False

    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("🚢 GOOGLE APPS SCRIPT & MULTI-FILE UPLOAD TESTING")
        print("=" * 80)
        print(f"Testing Apps Script URL: {self.apps_script_url}")
        print(f"Testing Folder ID: {self.folder_id}")
        print("=" * 80)
        
        # Step 1: Login
        if not self.test_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Step 2: Test Apps Script URL directly
        self.test_apps_script_direct()
        
        # Step 3: Test backend Google Drive configuration
        self.test_backend_gdrive_config()
        
        # Step 4: Test multi-file upload to reproduce error
        self.test_multi_file_upload()
        
        # Step 5: Test category mapping logic
        self.test_category_mapping()
        
        # Step 6: Test complete folder structure workflow
        self.test_folder_structure_creation()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️ Some tests failed - check details above")
            return False

def main():
    """Main test execution"""
    tester = AppsScriptMultiFileUploadTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
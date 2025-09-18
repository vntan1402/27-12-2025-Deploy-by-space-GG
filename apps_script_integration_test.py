#!/usr/bin/env python3
"""
Google Apps Script Integration Test
==================================

This test specifically addresses the user's reported issue:
- "Folder creation failed: Ship folder creation failed: None"
- "File upload failed: Ship folder creation failed: None"

User provided:
- Web App URL: https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec
- Google Drive Folder ID: 1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG

The test will:
1. Login as admin/admin123
2. Check company Google Drive configuration
3. Test the Apps Script connection directly
4. Attempt multi-file upload to reproduce the error
5. Analyze what actions the backend expects vs what Apps Script provides
"""

import requests
import json
import sys
import time
import io
from datetime import datetime, timezone

class AppsScriptIntegrationTester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.user_company = None
        
        # User provided Apps Script details
        self.apps_script_url = "https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec"
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

    def make_request(self, method, endpoint, data=None, files=None, expected_status=200):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if files is None and data is not None:
            headers['Content-Type'] = 'application/json'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"text": response.text}
            
            return success, response.status_code, response_data
            
        except Exception as e:
            return False, 0, {"error": str(e)}

    def test_authentication(self):
        """Test login as admin/admin123"""
        print("\n🔐 STEP 1: Testing Authentication")
        
        success, status, response = self.make_request(
            'POST', 
            'auth/login',
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_data = response.get('user', {})
            self.admin_user_id = user_data.get('id')
            self.user_company = user_data.get('company')
            
            self.log_test(
                "Admin Login", 
                True, 
                f"User: {user_data.get('full_name')} ({user_data.get('role')}) - Company: {self.user_company}"
            )
            return True
        else:
            self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")
            return False

    def test_company_gdrive_config(self):
        """Check company Google Drive configuration"""
        print("\n🏢 STEP 2: Checking Company Google Drive Configuration")
        
        # First get companies to find admin's company
        success, status, companies = self.make_request('GET', 'companies')
        
        if not success:
            self.log_test("Get Companies", False, f"Status: {status}")
            return False
        
        self.log_test("Get Companies", True, f"Found {len(companies)} companies")
        
        # Find admin's company
        admin_company = None
        for company in companies:
            if (company.get('name_en') == self.user_company or 
                company.get('name_vn') == self.user_company):
                admin_company = company
                break
        
        if not admin_company:
            self.log_test("Find Admin Company", False, f"Admin company '{self.user_company}' not found in companies list")
            return False
        
        company_id = admin_company['id']
        self.log_test("Find Admin Company", True, f"Company ID: {company_id}")
        
        # Check company's Google Drive config
        success, status, gdrive_config = self.make_request('GET', f'companies/{company_id}/gdrive/config')
        
        if success:
            configured = gdrive_config.get('configured', False)
            self.log_test(
                "Company GDrive Config", 
                True, 
                f"Configured: {configured}, Auth Method: {gdrive_config.get('auth_method', 'N/A')}"
            )
            return configured, company_id
        else:
            self.log_test("Company GDrive Config", False, f"Status: {status}")
            return False, None

    def test_apps_script_direct(self):
        """Test the Apps Script URL directly"""
        print("\n🔗 STEP 3: Testing Apps Script URL Directly")
        
        # Test basic connection
        try:
            response = requests.get(self.apps_script_url, timeout=30)
            self.log_test(
                "Apps Script GET Request", 
                response.status_code == 200,
                f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}"
            )
        except Exception as e:
            self.log_test("Apps Script GET Request", False, f"Error: {str(e)}")
        
        # Test POST with test_connection action
        test_actions = [
            {"action": "test_connection"},
            {"action": "create_folder_structure", "ship_name": "Test Ship", "folder_id": self.folder_id},
            {"action": "upload_file", "ship_name": "Test Ship", "folder_id": self.folder_id, "file_name": "test.txt", "file_content": "test"},
            {"action": "sync_to_drive"},  # Legacy action
        ]
        
        for test_data in test_actions:
            action = test_data["action"]
            try:
                response = requests.post(self.apps_script_url, json=test_data, timeout=30)
                
                # Check response
                content_type = response.headers.get('content-type', '').lower()
                is_json = 'application/json' in content_type
                
                if is_json:
                    try:
                        result = response.json()
                        success = result.get('success', False)
                        message = result.get('message', result.get('error', 'No message'))
                        self.log_test(
                            f"Apps Script {action}",
                            success,
                            f"Status: {response.status_code}, Success: {success}, Message: {message}"
                        )
                    except json.JSONDecodeError:
                        self.log_test(
                            f"Apps Script {action}",
                            False,
                            f"Status: {response.status_code}, Invalid JSON response"
                        )
                else:
                    # Non-JSON response (likely HTML error page)
                    self.log_test(
                        f"Apps Script {action}",
                        False,
                        f"Status: {response.status_code}, Non-JSON response (Content-Type: {content_type})"
                    )
                    
                    # Show first 200 chars of response for debugging
                    print(f"      Response preview: {response.text[:200]}...")
                    
            except Exception as e:
                self.log_test(f"Apps Script {action}", False, f"Error: {str(e)}")

    def test_backend_apps_script_config(self):
        """Test backend Apps Script configuration"""
        print("\n⚙️ STEP 4: Testing Backend Apps Script Configuration")
        
        # Configure Apps Script proxy
        config_data = {
            "web_app_url": self.apps_script_url,
            "folder_id": self.folder_id
        }
        
        success, status, response = self.make_request(
            'POST',
            'gdrive/configure-proxy',
            data=config_data
        )
        
        self.log_test(
            "Configure Apps Script Proxy",
            success,
            f"Status: {status}, Message: {response.get('message', 'No message')}"
        )
        
        if not success:
            print(f"      Full response: {response}")
        
        # Check Google Drive status after configuration
        success, status, gdrive_status = self.make_request('GET', 'gdrive/status')
        
        if success:
            self.log_test(
                "GDrive Status After Config",
                True,
                f"Configured: {gdrive_status.get('configured')}, Local files: {gdrive_status.get('local_files')}, Drive files: {gdrive_status.get('drive_files')}"
            )
        else:
            self.log_test("GDrive Status After Config", False, f"Status: {status}")
        
        return success

    def test_multi_file_upload(self):
        """Test multi-file upload to reproduce the error"""
        print("\n📁 STEP 5: Testing Multi-File Upload (Reproducing Error)")
        
        # First, get or create a ship
        success, status, ships = self.make_request('GET', 'ships')
        
        if not success or not ships:
            # Create a test ship
            ship_data = {
                "name": f"Test Ship {int(time.time())}",
                "imo": f"IMO{int(time.time())}",
                "flag": "Panama",
                "ship_type": "Container",
                "gross_tonnage": 50000.0,
                "year_built": 2020,
                "ship_owner": "Test Owner",
                "company": self.user_company
            }
            
            success, status, ship = self.make_request('POST', 'ships', data=ship_data)
            
            if success:
                ship_id = ship['id']
                self.log_test("Create Test Ship", True, f"Ship ID: {ship_id}")
            else:
                self.log_test("Create Test Ship", False, f"Status: {status}")
                return False
        else:
            ship_id = ships[0]['id']
            self.log_test("Use Existing Ship", True, f"Ship ID: {ship_id}")
        
        # Create test files for upload
        test_files = []
        
        # Create a simple text file
        text_content = "This is a test certificate document."
        text_file = io.BytesIO(text_content.encode('utf-8'))
        test_files.append(('files', ('test_certificate.txt', text_file, 'text/plain')))
        
        # Create another test file
        text_content2 = "This is a test inspection report."
        text_file2 = io.BytesIO(text_content2.encode('utf-8'))
        test_files.append(('files', ('test_inspection.txt', text_file2, 'text/plain')))
        
        # Prepare form data
        form_data = {
            'ship_id': ship_id
        }
        
        # Test multi-file upload endpoint
        success, status, response = self.make_request(
            'POST',
            'certificates/upload-multi-files',
            data=form_data,
            files=test_files
        )
        
        self.log_test(
            "Multi-File Upload",
            success,
            f"Status: {status}, Message: {response.get('message', 'No message')}"
        )
        
        if not success:
            print(f"      Full response: {response}")
            
            # Check if this is the specific error we're looking for
            error_message = response.get('detail', response.get('message', ''))
            if "Ship folder creation failed: None" in str(error_message):
                print("      🎯 REPRODUCED THE EXACT ERROR: 'Ship folder creation failed: None'")
            
        return success

    def analyze_backend_expectations(self):
        """Analyze what the backend expects from Apps Script"""
        print("\n🔍 STEP 6: Analyzing Backend vs Apps Script Compatibility")
        
        # Check the backend code expectations by looking at error patterns
        print("   Backend expects these Apps Script actions:")
        print("   - create_folder_structure: Create ship-specific folders")
        print("   - upload_file: Upload files to specific ship folders")
        print("   - test_connection: Test the connection")
        
        print("\n   Common Apps Script actions (legacy):")
        print("   - sync_to_drive: Sync all data to drive")
        print("   - test_connection: Test connection")
        
        print("\n   🚨 COMPATIBILITY ISSUE IDENTIFIED:")
        print("   The backend is calling 'create_folder_structure' and 'upload_file'")
        print("   but the user's Apps Script may only support older actions like 'sync_to_drive'")
        
        # Test what happens when we call the sync endpoint
        success, status, response = self.make_request('POST', 'gdrive/sync-to-drive-proxy')
        
        self.log_test(
            "Sync to Drive Proxy",
            success,
            f"Status: {status}, Message: {response.get('message', 'No message')}"
        )
        
        if not success:
            print(f"      Full response: {response}")

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🔧 Google Apps Script Integration Diagnostic Test")
        print("=" * 60)
        print(f"Testing Apps Script URL: {self.apps_script_url}")
        print(f"Testing Folder ID: {self.folder_id}")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.test_authentication():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Check company configuration
        configured, company_id = self.test_company_gdrive_config()
        
        # Step 3: Test Apps Script directly
        self.test_apps_script_direct()
        
        # Step 4: Test backend configuration
        self.test_backend_apps_script_config()
        
        # Step 5: Test multi-file upload (reproduce error)
        self.test_multi_file_upload()
        
        # Step 6: Analyze compatibility
        self.analyze_backend_expectations()
        
        # Final summary
        print("\n" + "=" * 60)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print("\n🔍 KEY FINDINGS:")
        print("1. Authentication: ✅ Working" if self.token else "1. Authentication: ❌ Failed")
        print("2. Company Config: ✅ Accessible" if configured else "2. Company Config: ❌ Not configured")
        print("3. Apps Script URL: Check individual test results above")
        print("4. Backend Integration: Check configuration test results")
        print("5. Multi-file Upload: Check upload test results")
        
        print("\n💡 RECOMMENDATIONS:")
        print("- If Apps Script returns HTML instead of JSON, the script has errors")
        print("- If 'create_folder_structure' action fails, the Apps Script needs updating")
        print("- The backend expects specific actions that may not be in the current Apps Script")
        print("- Check Apps Script logs in Google Apps Script editor for detailed errors")
        
        return self.tests_passed > 0

def main():
    """Main test execution"""
    tester = AppsScriptIntegrationTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
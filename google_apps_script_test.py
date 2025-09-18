#!/usr/bin/env python3
"""
Google Apps Script Integration Testing for Certificate Upload Functionality
Review Request: Debug Google Apps Script integration for certificate upload functionality

Testing Requirements:
1. Login as admin/admin123
2. Test direct Apps Script communication:
   - Test `test_connection` action
   - Test `create_folder_structure` action with ship name
   - Test `upload_file` action with base64 content
3. Check what actions the Apps Script actually supports vs what backend expects
4. Test with AMCSC company Google Drive configuration
5. Verify the payload format sent to Apps Script matches expected format
6. Check if the folder structure creation is working correctly
7. Test file upload with different file formats and sizes
8. Examine Apps Script response format and error messages
"""

import requests
import json
import base64
import time
from datetime import datetime, timezone
import sys
import os

class GoogleAppsScriptTester:
    def __init__(self, base_url="https://shipcertdrive.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.amcsc_company_id = None
        
        # User's Google Apps Script URL from review request
        self.apps_script_url = "https://script.google.com/macros/s/AKfycbzgEVRtLEGylJem_1826xgwdf_XYzQfv7IYiPlvZggq-6Yw4fKW3NZ-QG3yE-T-OlnF/exec"
        
        print(f"🔧 Google Apps Script Integration Tester")
        print(f"   Backend URL: {self.base_url}")
        print(f"   Apps Script URL: {self.apps_script_url}")
        print("=" * 80)

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
                print(f"   ERROR: {details}")

    def make_request(self, method, endpoint, data=None, files=None, timeout=30):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Remove Content-Type for file uploads
        if files:
            headers.pop('Content-Type', None)

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
            
            return response
        except Exception as e:
            print(f"   Request failed: {str(e)}")
            return None

    def test_authentication(self):
        """Test login with admin/admin123"""
        print(f"\n🔐 STEP 1: Authentication Testing")
        print("-" * 50)
        
        response = self.make_request(
            "POST", 
            "auth/login", 
            data={"username": "admin", "password": "admin123"}
        )
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get('access_token')
                self.admin_user_id = data.get('user', {}).get('id')
                user_info = data.get('user', {})
                
                self.log_test(
                    "Admin Login", 
                    True, 
                    f"User: {user_info.get('full_name')} ({user_info.get('role')})"
                )
                return True
            except Exception as e:
                self.log_test("Admin Login", False, f"JSON parsing failed: {e}")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("Admin Login", False, f"HTTP {status}")
            return False

    def find_amcsc_company(self):
        """Find AMCSC company in the database"""
        print(f"\n🏢 STEP 2: Finding AMCSC Company")
        print("-" * 50)
        
        response = self.make_request("GET", "companies")
        
        if response and response.status_code == 200:
            try:
                companies = response.json()
                print(f"   Found {len(companies)} companies total")
                
                # Look for AMCSC company
                amcsc_company = None
                for company in companies:
                    name_vn = company.get('name_vn', '').upper()
                    name_en = company.get('name_en', '').upper()
                    name = company.get('name', '').upper()
                    
                    if 'AMCSC' in name_vn or 'AMCSC' in name_en or 'AMCSC' in name:
                        amcsc_company = company
                        break
                
                if amcsc_company:
                    self.amcsc_company_id = amcsc_company['id']
                    self.log_test(
                        "AMCSC Company Found", 
                        True, 
                        f"ID: {self.amcsc_company_id}, Name: {amcsc_company.get('name_en', amcsc_company.get('name', 'Unknown'))}"
                    )
                    return True
                else:
                    self.log_test("AMCSC Company Found", False, "AMCSC company not found in database")
                    return False
                    
            except Exception as e:
                self.log_test("AMCSC Company Found", False, f"JSON parsing failed: {e}")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("AMCSC Company Found", False, f"HTTP {status}")
            return False

    def test_direct_apps_script_communication(self):
        """Test direct communication with Google Apps Script"""
        print(f"\n🔗 STEP 3: Direct Apps Script Communication Testing")
        print("-" * 50)
        
        # Test 1: test_connection action
        print(f"\n   Testing 'test_connection' action...")
        test_payload = {
            "action": "test_connection",
            "folder_id": "test_folder_id_123"
        }
        
        try:
            response = requests.post(self.apps_script_url, json=test_payload, timeout=30)
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   Response JSON: {json.dumps(result, indent=2)}")
                    
                    if result.get("success"):
                        self.log_test("Apps Script test_connection", True, f"Message: {result.get('message', 'Success')}")
                    else:
                        self.log_test("Apps Script test_connection", False, f"Script returned error: {result.get('error', 'Unknown error')}")
                except json.JSONDecodeError:
                    print(f"   Response Text: {response.text}")
                    self.log_test("Apps Script test_connection", False, "Invalid JSON response")
            else:
                print(f"   Response Text: {response.text}")
                self.log_test("Apps Script test_connection", False, f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_test("Apps Script test_connection", False, "Request timeout")
        except Exception as e:
            self.log_test("Apps Script test_connection", False, f"Request failed: {e}")

        # Test 2: create_folder_structure action
        print(f"\n   Testing 'create_folder_structure' action...")
        folder_payload = {
            "action": "create_folder_structure",
            "ship_name": "TEST_SHIP_AMCSC"
        }
        
        try:
            response = requests.post(self.apps_script_url, json=folder_payload, timeout=30)
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   Response JSON: {json.dumps(result, indent=2)}")
                    
                    if result.get("success"):
                        self.log_test("Apps Script create_folder_structure", True, f"Ship folder created: {result.get('ship_folder_id', 'Unknown ID')}")
                    else:
                        self.log_test("Apps Script create_folder_structure", False, f"Script returned error: {result.get('error', 'Unknown error')}")
                except json.JSONDecodeError:
                    print(f"   Response Text: {response.text}")
                    self.log_test("Apps Script create_folder_structure", False, "Invalid JSON response")
            else:
                print(f"   Response Text: {response.text}")
                self.log_test("Apps Script create_folder_structure", False, f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_test("Apps Script create_folder_structure", False, "Request timeout")
        except Exception as e:
            self.log_test("Apps Script create_folder_structure", False, f"Request failed: {e}")

        # Test 3: upload_file action with base64 content
        print(f"\n   Testing 'upload_file' action...")
        
        # Create a small test PDF content
        test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        test_pdf_base64 = base64.b64encode(test_pdf_content).decode('utf-8')
        
        upload_payload = {
            "action": "upload_file",
            "ship_name": "TEST_SHIP_AMCSC",
            "folder_name": "Certificates",
            "filename": "test_certificate.pdf",
            "file_content": test_pdf_base64
        }
        
        try:
            response = requests.post(self.apps_script_url, json=upload_payload, timeout=60)
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   Response JSON: {json.dumps(result, indent=2)}")
                    
                    if result.get("success"):
                        self.log_test("Apps Script upload_file", True, f"File uploaded: {result.get('file_id', 'Unknown ID')}")
                    else:
                        self.log_test("Apps Script upload_file", False, f"Script returned error: {result.get('error', 'Unknown error')}")
                except json.JSONDecodeError:
                    print(f"   Response Text: {response.text}")
                    self.log_test("Apps Script upload_file", False, "Invalid JSON response")
            else:
                print(f"   Response Text: {response.text}")
                self.log_test("Apps Script upload_file", False, f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_test("Apps Script upload_file", False, "Request timeout (60s)")
        except Exception as e:
            self.log_test("Apps Script upload_file", False, f"Request failed: {e}")

    def test_backend_company_gdrive_endpoints(self):
        """Test backend company-specific Google Drive endpoints"""
        print(f"\n🔧 STEP 4: Backend Company Google Drive Endpoints")
        print("-" * 50)
        
        if not self.amcsc_company_id:
            print("   Skipping - AMCSC company not found")
            return False

        # Test 1: Get company Google Drive config
        response = self.make_request("GET", f"companies/{self.amcsc_company_id}/gdrive/config")
        
        if response and response.status_code == 200:
            try:
                config_data = response.json()
                print(f"   Current Config: {json.dumps(config_data, indent=2)}")
                self.log_test("Get Company GDrive Config", True, f"Config retrieved for {config_data.get('company_name', 'Unknown')}")
            except Exception as e:
                self.log_test("Get Company GDrive Config", False, f"JSON parsing failed: {e}")
        else:
            status = response.status_code if response else "No response"
            self.log_test("Get Company GDrive Config", False, f"HTTP {status}")

        # Test 2: Get company Google Drive status
        response = self.make_request("GET", f"companies/{self.amcsc_company_id}/gdrive/status")
        
        if response and response.status_code == 200:
            try:
                status_data = response.json()
                print(f"   Current Status: {json.dumps(status_data, indent=2)}")
                self.log_test("Get Company GDrive Status", True, f"Status: {status_data.get('status', 'Unknown')}")
            except Exception as e:
                self.log_test("Get Company GDrive Status", False, f"JSON parsing failed: {e}")
        else:
            status = response.status_code if response else "No response"
            self.log_test("Get Company GDrive Status", False, f"HTTP {status}")

        # Test 3: Configure company Google Drive with user's Apps Script URL
        config_payload = {
            "web_app_url": self.apps_script_url,
            "folder_id": "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG",  # Test folder ID
            "auth_method": "apps_script"
        }
        
        response = self.make_request("POST", f"companies/{self.amcsc_company_id}/gdrive/configure", data=config_payload)
        
        if response and response.status_code == 200:
            try:
                result = response.json()
                print(f"   Configuration Result: {json.dumps(result, indent=2)}")
                
                if result.get("success"):
                    self.log_test("Configure Company GDrive", True, f"Configuration successful: {result.get('message', 'Success')}")
                else:
                    self.log_test("Configure Company GDrive", False, f"Configuration failed: {result.get('message', 'Unknown error')}")
            except Exception as e:
                self.log_test("Configure Company GDrive", False, f"JSON parsing failed: {e}")
        else:
            status = response.status_code if response else "No response"
            error_text = response.text if response else "No response"
            self.log_test("Configure Company GDrive", False, f"HTTP {status}: {error_text}")

        # Test 4: Test the proxy endpoint
        response = self.make_request("POST", f"companies/{self.amcsc_company_id}/gdrive/configure-proxy", data=config_payload)
        
        if response and response.status_code == 200:
            try:
                result = response.json()
                if result.get("success"):
                    self.log_test("Configure Company GDrive Proxy", True, "Proxy endpoint working")
                else:
                    self.log_test("Configure Company GDrive Proxy", False, f"Proxy failed: {result.get('message', 'Unknown error')}")
            except Exception as e:
                self.log_test("Configure Company GDrive Proxy", False, f"JSON parsing failed: {e}")
        else:
            status = response.status_code if response else "No response"
            self.log_test("Configure Company GDrive Proxy", False, f"HTTP {status}")

    def test_certificate_upload_workflow(self):
        """Test the complete certificate upload workflow"""
        print(f"\n📄 STEP 5: Certificate Upload Workflow Testing")
        print("-" * 50)
        
        # First, get ships to test with
        response = self.make_request("GET", "ships")
        
        if not response or response.status_code != 200:
            self.log_test("Get Ships for Upload Test", False, "Cannot retrieve ships")
            return False
        
        try:
            ships = response.json()
            if not ships:
                self.log_test("Get Ships for Upload Test", False, "No ships available")
                return False
            
            test_ship = ships[0]  # Use first ship
            ship_id = test_ship['id']
            ship_name = test_ship['name']
            
            self.log_test("Get Ships for Upload Test", True, f"Using ship: {ship_name} (ID: {ship_id})")
            
        except Exception as e:
            self.log_test("Get Ships for Upload Test", False, f"JSON parsing failed: {e}")
            return False

        # Create a test certificate PDF file
        test_certificate_content = b"""%PDF-1.4
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
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF"""

        # Test multi-file upload endpoint
        files = {
            'files': ('test_certificate.pdf', test_certificate_content, 'application/pdf')
        }
        
        response = self.make_request("POST", "certificates/upload-multi-files", files=files)
        
        if response and response.status_code == 200:
            try:
                result = response.json()
                print(f"   Upload Result: {json.dumps(result, indent=2)}")
                
                results = result.get('results', [])
                if results and len(results) > 0:
                    first_result = results[0]
                    if first_result.get('status') == 'success':
                        self.log_test("Multi-file Certificate Upload", True, f"File processed: {first_result.get('filename')}")
                    else:
                        self.log_test("Multi-file Certificate Upload", False, f"Upload failed: {first_result.get('message', 'Unknown error')}")
                else:
                    self.log_test("Multi-file Certificate Upload", False, "No results returned")
                    
            except Exception as e:
                self.log_test("Multi-file Certificate Upload", False, f"JSON parsing failed: {e}")
        else:
            status = response.status_code if response else "No response"
            error_text = response.text if response else "No response"
            self.log_test("Multi-file Certificate Upload", False, f"HTTP {status}: {error_text}")

    def test_apps_script_supported_actions(self):
        """Test what actions the Apps Script actually supports"""
        print(f"\n🔍 STEP 6: Apps Script Supported Actions Discovery")
        print("-" * 50)
        
        # Test various actions to see what's supported
        test_actions = [
            {"action": "test_connection", "folder_id": "test"},
            {"action": "create_folder_structure", "ship_name": "TEST_SHIP"},
            {"action": "upload_file", "ship_name": "TEST", "folder_name": "Certificates", "filename": "test.pdf", "file_content": "dGVzdA=="},
            {"action": "list_folders"},
            {"action": "get_folder_info", "folder_id": "test"},
            {"action": "delete_file", "file_id": "test"},
            {"action": "unknown_action"}
        ]
        
        supported_actions = []
        unsupported_actions = []
        
        for test_payload in test_actions:
            action_name = test_payload.get("action")
            print(f"\n   Testing action: {action_name}")
            
            try:
                response = requests.post(self.apps_script_url, json=test_payload, timeout=30)
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"     Response: {json.dumps(result, indent=4)}")
                        
                        if result.get("success") or "error" in result:
                            # Even if there's an error, the action is recognized
                            supported_actions.append(action_name)
                            print(f"     ✅ Action '{action_name}' is supported")
                        else:
                            unsupported_actions.append(action_name)
                            print(f"     ❌ Action '{action_name}' not supported or failed")
                    except json.JSONDecodeError:
                        print(f"     ❌ Invalid JSON response for '{action_name}'")
                        unsupported_actions.append(action_name)
                else:
                    print(f"     ❌ HTTP {response.status_code} for '{action_name}'")
                    unsupported_actions.append(action_name)
                    
            except Exception as e:
                print(f"     ❌ Request failed for '{action_name}': {e}")
                unsupported_actions.append(action_name)
        
        print(f"\n   📊 APPS SCRIPT CAPABILITIES SUMMARY:")
        print(f"   Supported Actions: {supported_actions}")
        print(f"   Unsupported Actions: {unsupported_actions}")
        
        self.log_test("Apps Script Actions Discovery", True, f"Found {len(supported_actions)} supported actions")

    def test_payload_format_validation(self):
        """Test different payload formats to understand what the Apps Script expects"""
        print(f"\n📋 STEP 7: Payload Format Validation")
        print("-" * 50)
        
        # Test different payload formats
        test_formats = [
            {
                "name": "Standard JSON",
                "payload": {"action": "test_connection", "folder_id": "test123"},
                "content_type": "application/json"
            },
            {
                "name": "Form Data",
                "payload": {"action": "test_connection", "folder_id": "test123"},
                "content_type": "application/x-www-form-urlencoded"
            },
            {
                "name": "Text Payload",
                "payload": "action=test_connection&folder_id=test123",
                "content_type": "text/plain"
            }
        ]
        
        for test_format in test_formats:
            print(f"\n   Testing format: {test_format['name']}")
            
            try:
                headers = {"Content-Type": test_format["content_type"]}
                
                if test_format["content_type"] == "application/json":
                    response = requests.post(self.apps_script_url, json=test_format["payload"], timeout=30)
                elif test_format["content_type"] == "application/x-www-form-urlencoded":
                    response = requests.post(self.apps_script_url, data=test_format["payload"], headers=headers, timeout=30)
                else:
                    response = requests.post(self.apps_script_url, data=test_format["payload"], headers=headers, timeout=30)
                
                print(f"     Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"     Response: {json.dumps(result, indent=4)}")
                        self.log_test(f"Payload Format - {test_format['name']}", True, "Format accepted")
                    except json.JSONDecodeError:
                        print(f"     Response Text: {response.text}")
                        self.log_test(f"Payload Format - {test_format['name']}", False, "Invalid JSON response")
                else:
                    print(f"     Response: {response.text}")
                    self.log_test(f"Payload Format - {test_format['name']}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Payload Format - {test_format['name']}", False, f"Request failed: {e}")

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print(f"🚀 Starting Comprehensive Google Apps Script Integration Testing")
        print(f"   Target Apps Script: {self.apps_script_url}")
        print(f"   Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.test_authentication():
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with backend tests")
            return False
        
        # Step 2: Find AMCSC company
        self.find_amcsc_company()
        
        # Step 3: Direct Apps Script communication
        self.test_direct_apps_script_communication()
        
        # Step 4: Backend company Google Drive endpoints
        self.test_backend_company_gdrive_endpoints()
        
        # Step 5: Certificate upload workflow
        self.test_certificate_upload_workflow()
        
        # Step 6: Apps Script supported actions discovery
        self.test_apps_script_supported_actions()
        
        # Step 7: Payload format validation
        self.test_payload_format_validation()
        
        # Final summary
        self.print_final_summary()
        
        return self.tests_passed > 0

    def print_final_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   • Apps Script URL: {self.apps_script_url}")
        print(f"   • AMCSC Company ID: {self.amcsc_company_id or 'Not Found'}")
        print(f"   • Authentication: {'✅ Working' if self.token else '❌ Failed'}")
        
        if success_rate >= 70:
            print(f"\n🎉 OVERALL RESULT: GOOD - Most functionality working")
        elif success_rate >= 50:
            print(f"\n⚠️ OVERALL RESULT: PARTIAL - Some issues found")
        else:
            print(f"\n❌ OVERALL RESULT: CRITICAL ISSUES - Major problems detected")
        
        print("=" * 80)

def main():
    """Main test execution"""
    tester = GoogleAppsScriptTester()
    
    try:
        success = tester.run_comprehensive_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Google Drive Configuration Debug Test
=====================================

This test specifically debugs the System Google Drive configuration issue reported by the user.
User reports "script error" when testing System Google Drive connection.

User's Configuration:
- Google Apps Script URL: https://script.google.com/macros/s/AKfycbwIfwqaegvfi0IEZPdArCvphZNVPcbS_2eIq_aAop08Kc_9TzDngAs-KCDVb-t2xNc/exec
- Google Drive Folder ID: 1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB
"""

import requests
import json
import sys
from datetime import datetime

class GoogleDriveDebugTester:
    def __init__(self):
        self.base_url = "https://ship-cert-manager-1.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # User's specific configuration
        self.user_apps_script_url = "https://script.google.com/macros/s/AKfycbwIfwqaegvfi0IEZPdArCvphZNVPcbS_2eIq_aAop08Kc_9TzDngAs-KCDVb-t2xNc/exec"
        self.user_folder_id = "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"

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

    def test_login(self):
        """Test admin login"""
        print("\n🔐 Testing Authentication")
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                user_info = data.get('user', {})
                self.log_test(
                    "Admin Login", 
                    True, 
                    f"User: {user_info.get('full_name')} ({user_info.get('role')})"
                )
                return True
            else:
                self.log_test("Admin Login", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False

    def test_direct_apps_script_get(self):
        """Test direct GET request to Apps Script URL"""
        print("\n🌐 Testing Direct Apps Script URL - GET Request")
        try:
            response = requests.get(self.user_apps_script_url, timeout=30)
            
            content_type = response.headers.get('content-type', '')
            is_json = 'application/json' in content_type
            is_html = 'text/html' in content_type
            
            self.log_test(
                "Direct Apps Script GET",
                response.status_code == 200,
                f"Status: {response.status_code}, Content-Type: {content_type}"
            )
            
            print(f"   Response Length: {len(response.text)} characters")
            print(f"   Is JSON: {is_json}")
            print(f"   Is HTML: {is_html}")
            
            if is_html:
                print("   ⚠️  WARNING: Apps Script returned HTML instead of JSON")
                print("   This suggests the script may not be deployed correctly")
                
            # Show first 500 characters of response
            print(f"   Response Preview: {response.text[:500]}...")
            
            return response.status_code == 200
            
        except Exception as e:
            self.log_test("Direct Apps Script GET", False, f"Error: {str(e)}")
            return False

    def test_direct_apps_script_test_connection(self):
        """Test direct POST request to Apps Script with test_connection action"""
        print("\n🔗 Testing Direct Apps Script - Test Connection Action")
        try:
            payload = {
                "action": "test_connection",
                "folder_id": self.user_folder_id
            }
            
            response = requests.post(
                self.user_apps_script_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            content_type = response.headers.get('content-type', '')
            is_json = 'application/json' in content_type
            
            self.log_test(
                "Apps Script Test Connection",
                response.status_code == 200,
                f"Status: {response.status_code}, Content-Type: {content_type}"
            )
            
            print(f"   Payload sent: {json.dumps(payload, indent=2)}")
            print(f"   Response Length: {len(response.text)} characters")
            print(f"   Is JSON: {is_json}")
            
            try:
                response_data = response.json()
                print(f"   Response JSON: {json.dumps(response_data, indent=2)}")
                
                # Check for success/error in response
                if 'success' in response_data:
                    success = response_data.get('success', False)
                    message = response_data.get('message', 'No message')
                    print(f"   Apps Script Success: {success}")
                    print(f"   Apps Script Message: {message}")
                    
                    if not success:
                        print("   ⚠️  Apps Script reported failure")
                        
                elif 'error' in response_data:
                    print(f"   ⚠️  Apps Script Error: {response_data.get('error')}")
                    
            except json.JSONDecodeError:
                print("   ⚠️  Response is not valid JSON")
                print(f"   Raw Response: {response.text[:1000]}...")
            
            return response.status_code == 200
            
        except Exception as e:
            self.log_test("Apps Script Test Connection", False, f"Error: {str(e)}")
            return False

    def test_backend_system_gdrive_config(self):
        """Test backend system Google Drive configuration endpoints"""
        print("\n⚙️ Testing Backend System Google Drive Configuration")
        
        if not self.token:
            print("   ❌ No authentication token available")
            return False
            
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Test GET system Google Drive config
        try:
            response = requests.get(
                f"{self.api_url}/gdrive/config",
                headers=headers,
                timeout=30
            )
            
            self.log_test(
                "GET System GDrive Config",
                response.status_code in [200, 404],
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                try:
                    config_data = response.json()
                    print(f"   Current Config: {json.dumps(config_data, indent=2)}")
                except:
                    print(f"   Response: {response.text}")
            elif response.status_code == 404:
                print("   No system Google Drive configuration found (expected for first setup)")
                
        except Exception as e:
            self.log_test("GET System GDrive Config", False, f"Error: {str(e)}")
            
        # Test POST system Google Drive config with user's settings
        try:
            config_payload = {
                "apps_script_url": self.user_apps_script_url,
                "folder_id": self.user_folder_id
            }
            
            response = requests.post(
                f"{self.api_url}/gdrive/configure",
                json=config_payload,
                headers=headers,
                timeout=30
            )
            
            self.log_test(
                "POST System GDrive Configure",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            print(f"   Config Payload: {json.dumps(config_payload, indent=2)}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   Configuration Result: {json.dumps(result, indent=2)}")
                except:
                    print(f"   Response: {response.text}")
            else:
                try:
                    error = response.json()
                    print(f"   Error Response: {json.dumps(error, indent=2)}")
                except:
                    print(f"   Error Response: {response.text}")
                    
            return response.status_code == 200
            
        except Exception as e:
            self.log_test("POST System GDrive Configure", False, f"Error: {str(e)}")
            return False

    def test_backend_gdrive_test_connection(self):
        """Test backend Google Drive test connection endpoint"""
        print("\n🔍 Testing Backend Google Drive Test Connection")
        
        if not self.token:
            print("   ❌ No authentication token available")
            return False
            
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/gdrive/test-connection",
                headers=headers,
                timeout=30
            )
            
            self.log_test(
                "Backend GDrive Test Connection",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   Test Connection Result: {json.dumps(result, indent=2)}")
                    
                    # Check for specific success/failure indicators
                    if 'success' in result:
                        success = result.get('success', False)
                        message = result.get('message', 'No message')
                        print(f"   Backend Success: {success}")
                        print(f"   Backend Message: {message}")
                        
                        if not success:
                            print("   ⚠️  Backend reported test connection failure")
                            
                except:
                    print(f"   Response: {response.text}")
            else:
                try:
                    error = response.json()
                    print(f"   Error Response: {json.dumps(error, indent=2)}")
                    
                    # Look for specific error messages
                    if 'detail' in error:
                        detail = error.get('detail', '')
                        if 'script error' in detail.lower():
                            print("   🎯 FOUND 'script error' - This matches user's report!")
                        print(f"   Error Detail: {detail}")
                        
                except:
                    print(f"   Error Response: {response.text}")
                    
            return response.status_code == 200
            
        except Exception as e:
            self.log_test("Backend GDrive Test Connection", False, f"Error: {str(e)}")
            return False

    def test_backend_gdrive_status(self):
        """Test backend Google Drive status endpoint"""
        print("\n📊 Testing Backend Google Drive Status")
        
        if not self.token:
            print("   ❌ No authentication token available")
            return False
            
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.api_url}/gdrive/status",
                headers=headers,
                timeout=30
            )
            
            self.log_test(
                "Backend GDrive Status",
                response.status_code in [200, 404],
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                try:
                    status_data = response.json()
                    print(f"   Status Data: {json.dumps(status_data, indent=2)}")
                except:
                    print(f"   Response: {response.text}")
            elif response.status_code == 404:
                print("   No Google Drive status found (expected if not configured)")
                
            return response.status_code in [200, 404]
            
        except Exception as e:
            self.log_test("Backend GDrive Status", False, f"Error: {str(e)}")
            return False

    def analyze_error_patterns(self):
        """Analyze common error patterns and provide recommendations"""
        print("\n🔍 ERROR ANALYSIS AND RECOMMENDATIONS")
        print("=" * 50)
        
        print("\n📋 Common Issues and Solutions:")
        print("1. Apps Script returns HTML instead of JSON:")
        print("   - Script may not be deployed as 'Web app'")
        print("   - Script may not have proper doGet/doPost functions")
        print("   - Script execution permissions may be incorrect")
        
        print("\n2. 'script error' in backend:")
        print("   - Backend may be sending wrong payload format")
        print("   - Apps Script may not handle the specific action")
        print("   - Network/timeout issues between backend and Apps Script")
        
        print("\n3. Folder ID access issues:")
        print("   - Folder may not be shared with the Apps Script")
        print("   - Apps Script may not have Drive API permissions")
        print("   - Folder ID may be incorrect or inaccessible")
        
        print("\n4. Authentication/Permission issues:")
        print("   - Apps Script may need to be authorized by the owner")
        print("   - Google Drive API may not be enabled")
        print("   - Service account permissions may be insufficient")

    def run_all_tests(self):
        """Run all Google Drive debug tests"""
        print("🔍 Google Drive Configuration Debug Test")
        print("=" * 60)
        print(f"Apps Script URL: {self.user_apps_script_url}")
        print(f"Folder ID: {self.user_folder_id}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Authentication", self.test_login),
            ("Direct Apps Script GET", self.test_direct_apps_script_get),
            ("Direct Apps Script Test Connection", self.test_direct_apps_script_test_connection),
            ("Backend System GDrive Config", self.test_backend_system_gdrive_config),
            ("Backend GDrive Test Connection", self.test_backend_gdrive_test_connection),
            ("Backend GDrive Status", self.test_backend_gdrive_status),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} - Unexpected error: {str(e)}")
                results.append((test_name, False))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:35} {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {self.tests_passed}/{self.tests_run} individual tests passed")
        print(f"Test Categories: {passed}/{len(results)} categories passed")
        
        # Analyze errors
        self.analyze_error_patterns()
        
        return passed == len(results)

def main():
    """Main execution"""
    tester = GoogleDriveDebugTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
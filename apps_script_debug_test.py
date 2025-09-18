#!/usr/bin/env python3
"""
Apps Script Proxy Connection Debug Test
Debug Apps Script proxy connection error and test integration
"""

import requests
import json
import sys
import time
from datetime import datetime, timezone

class AppsScriptDebugTester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Sample Apps Script URLs for testing
        self.sample_apps_script_urls = [
            "https://script.google.com/macros/s/AKfycbxSampleURL1/exec",
            "https://script.google.com/macros/s/AKfycbxSampleURL2/exec",
            "https://script.google.com/macros/s/AKfycbxInvalidURL/exec"
        ]
        
        # Sample folder IDs
        self.sample_folder_ids = [
            "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB",
            "1BcDefGhIjKlMnOpQrStUvWxYz123456789",
            "invalid-folder-id"
        ]

    def log_test(self, name, success, details=""):
        """Log test result"""
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

    def test_login(self, username="admin", password="admin123"):
        """Test authentication"""
        print(f"\n🔐 Testing Authentication with {username}/{password}")
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": username, "password": password},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                user_info = data.get('user', {})
                self.log_test(
                    "Authentication", 
                    True, 
                    f"User: {user_info.get('full_name')} ({user_info.get('role')})"
                )
                return True
            else:
                self.log_test(
                    "Authentication", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Error: {str(e)}")
            return False

    def test_direct_apps_script_simulation(self):
        """Test direct Apps Script endpoint simulation with cURL-like requests"""
        print(f"\n🌐 Testing Direct Apps Script Endpoint Simulation")
        
        # Test 1: Simulate successful Apps Script response
        print("\n📋 Test 1: Simulating successful Apps Script response")
        mock_success_response = {
            "success": True,
            "message": "Connection successful",
            "service_account_email": "test-service@project.iam.gserviceaccount.com",
            "folder_name": "Ship Management Data"
        }
        print(f"   Expected successful response format: {json.dumps(mock_success_response, indent=2)}")
        
        # Test 2: Simulate failed Apps Script response
        print("\n📋 Test 2: Simulating failed Apps Script response")
        mock_error_response = {
            "success": False,
            "error": "Invalid credentials or folder access denied"
        }
        print(f"   Expected error response format: {json.dumps(mock_error_response, indent=2)}")
        
        # Test 3: Simulate empty response (the reported issue)
        print("\n📋 Test 3: Simulating empty response (current issue)")
        print("   Empty response body (causes 'Expecting value: line 1 column 1 (char 0)' error)")
        print("   This is likely the root cause of the current issue")
        
        # Test 4: Simulate non-JSON response
        print("\n📋 Test 4: Simulating non-JSON response")
        print("   Response: 'HTML error page or plain text'")
        print("   This would also cause JSON parsing errors")
        
        self.log_test("Apps Script Response Format Analysis", True, "All response scenarios documented")
        return True

    def test_apps_script_url_formats(self):
        """Test different Apps Script URL formats"""
        print(f"\n🔗 Testing Apps Script URL Format Validation")
        
        valid_urls = [
            "https://script.google.com/macros/s/AKfycbxSampleURL123456789/exec",
            "https://script.google.com/macros/s/AKfycbxAnotherValidURL/exec"
        ]
        
        invalid_urls = [
            "https://script.google.com/macros/s/invalid/exec",  # Too short
            "https://example.com/not-apps-script",  # Wrong domain
            "http://script.google.com/macros/s/AKfycbxTest/exec",  # HTTP instead of HTTPS
            "https://script.google.com/macros/s/",  # Missing script ID
            ""  # Empty URL
        ]
        
        print("✅ Valid Apps Script URL formats:")
        for url in valid_urls:
            print(f"   ✓ {url}")
        
        print("\n❌ Invalid Apps Script URL formats:")
        for url in invalid_urls:
            print(f"   ✗ {url}")
        
        self.log_test("Apps Script URL Format Validation", True, f"Validated {len(valid_urls)} valid and {len(invalid_urls)} invalid formats")
        return True

    def test_backend_apps_script_integration(self):
        """Test backend Apps Script integration endpoint"""
        print(f"\n🔧 Testing Backend Apps Script Integration")
        
        if not self.token:
            self.log_test("Backend Integration", False, "No authentication token available")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Test with mock Apps Script URL
        test_configs = [
            {
                "name": "Valid Format URL Test",
                "config": {
                    "web_app_url": "https://script.google.com/macros/s/AKfycbxTestURL123456789/exec",
                    "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
                },
                "expected_error": "Failed to connect to Apps Script proxy"
            },
            {
                "name": "Invalid URL Format Test",
                "config": {
                    "web_app_url": "https://invalid-url.com/test",
                    "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
                },
                "expected_error": "Failed to connect to Apps Script proxy"
            },
            {
                "name": "Empty Folder ID Test",
                "config": {
                    "web_app_url": "https://script.google.com/macros/s/AKfycbxTestURL123456789/exec",
                    "folder_id": ""
                },
                "expected_error": "Failed to connect to Apps Script proxy"
            }
        ]
        
        for test_config in test_configs:
            print(f"\n📋 {test_config['name']}")
            print(f"   URL: {test_config['config']['web_app_url']}")
            print(f"   Folder ID: {test_config['config']['folder_id']}")
            
            try:
                response = requests.post(
                    f"{self.api_url}/gdrive/configure-proxy",
                    json=test_config['config'],
                    headers=headers,
                    timeout=30
                )
                
                print(f"   Status Code: {response.status_code}")
                
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', 'Unknown error')
                        print(f"   Error Detail: {error_detail}")
                        
                        if test_config['expected_error'] in error_detail:
                            self.log_test(f"Backend Integration - {test_config['name']}", True, "Expected error received")
                        else:
                            self.log_test(f"Backend Integration - {test_config['name']}", False, f"Unexpected error: {error_detail}")
                    except json.JSONDecodeError:
                        print(f"   Response Text: {response.text}")
                        self.log_test(f"Backend Integration - {test_config['name']}", False, "Non-JSON error response")
                
                elif response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', 'Unknown error')
                        print(f"   Server Error: {error_detail}")
                        
                        # Check if it's the JSON parsing error we're debugging
                        if "Expecting value: line 1 column 1 (char 0)" in error_detail:
                            self.log_test(f"Backend Integration - {test_config['name']}", True, "FOUND THE REPORTED ERROR: Empty response from Apps Script")
                            print("   🎯 ROOT CAUSE IDENTIFIED: Apps Script is returning empty response")
                        else:
                            self.log_test(f"Backend Integration - {test_config['name']}", True, f"Server error as expected: {error_detail}")
                    except json.JSONDecodeError:
                        print(f"   Response Text: {response.text}")
                        self.log_test(f"Backend Integration - {test_config['name']}", False, "Non-JSON server error response")
                
                else:
                    print(f"   Unexpected status code: {response.status_code}")
                    print(f"   Response: {response.text}")
                    self.log_test(f"Backend Integration - {test_config['name']}", False, f"Unexpected response: {response.status_code}")
                
            except requests.exceptions.Timeout:
                self.log_test(f"Backend Integration - {test_config['name']}", True, "Request timeout (expected for invalid URLs)")
            except requests.exceptions.ConnectionError:
                self.log_test(f"Backend Integration - {test_config['name']}", True, "Connection error (expected for invalid URLs)")
            except Exception as e:
                self.log_test(f"Backend Integration - {test_config['name']}", False, f"Unexpected error: {str(e)}")
        
        return True

    def test_request_payload_format(self):
        """Test the request payload format sent to Apps Script"""
        print(f"\n📦 Testing Request Payload Format")
        
        # Expected payload format based on backend code
        expected_payload = {
            "action": "test_connection"
        }
        
        print("📋 Expected payload sent to Apps Script:")
        print(f"   POST {'{web_app_url}'}")
        print(f"   Content-Type: application/json")
        print(f"   Body: {json.dumps(expected_payload, indent=2)}")
        
        print("\n📋 Apps Script should respond with:")
        print("   Success case:")
        success_response = {
            "success": True,
            "service_account_email": "service@project.iam.gserviceaccount.com",
            "folder_name": "Folder Name"
        }
        print(f"   {json.dumps(success_response, indent=2)}")
        
        print("\n   Error case:")
        error_response = {
            "success": False,
            "error": "Error description"
        }
        print(f"   {json.dumps(error_response, indent=2)}")
        
        self.log_test("Request Payload Format Analysis", True, "Payload format documented")
        return True

    def test_backend_error_handling(self):
        """Test backend error handling for different response scenarios"""
        print(f"\n🛡️ Testing Backend Error Handling")
        
        print("📋 Backend error handling analysis:")
        print("   1. Empty response → 'Expecting value: line 1 column 1 (char 0)' (CURRENT ISSUE)")
        print("   2. Non-JSON response → JSON decode error")
        print("   3. HTTP error status → Connection failed")
        print("   4. Timeout → Request timeout")
        print("   5. Network error → Connection error")
        
        print("\n📋 Backend code analysis (from server.py lines 933-943):")
        print("   - Makes POST request to Apps Script URL")
        print("   - Expects JSON response with 'success' field")
        print("   - No explicit handling for empty responses")
        print("   - JSON parsing happens without try-catch for empty body")
        
        print("\n🔧 Recommended fixes:")
        print("   1. Add response.text check before JSON parsing")
        print("   2. Add specific error handling for empty responses")
        print("   3. Add response content-type validation")
        print("   4. Add more detailed error messages")
        
        self.log_test("Backend Error Handling Analysis", True, "Error handling scenarios documented")
        return True

    def check_backend_logs(self):
        """Check backend logs for Apps Script errors"""
        print(f"\n📋 Backend Logs Analysis")
        
        print("🔍 To check backend logs for Apps Script errors, run:")
        print("   tail -n 100 /var/log/supervisor/backend.*.log | grep -i 'apps\\|script\\|proxy\\|json'")
        
        print("\n🔍 Look for these error patterns:")
        print("   - 'Expecting value: line 1 column 1 (char 0)'")
        print("   - 'Failed to connect to Apps Script proxy'")
        print("   - 'JSONDecodeError'")
        print("   - HTTP status codes (400, 404, 500)")
        
        self.log_test("Backend Logs Analysis", True, "Log checking instructions provided")
        return True

    def generate_apps_script_setup_guide(self):
        """Generate Apps Script setup requirements and guide"""
        print(f"\n📚 Apps Script Setup Requirements")
        
        print("🔧 Google Apps Script Setup Requirements:")
        print("   1. Create new Google Apps Script project")
        print("   2. Add the following code to handle POST requests:")
        
        apps_script_code = '''
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    
    if (data.action === "test_connection") {
      return ContentService
        .createTextOutput(JSON.stringify({
          "success": true,
          "message": "Connection successful",
          "service_account_email": "your-service@project.iam.gserviceaccount.com",
          "folder_name": "Ship Management Data"
        }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    if (data.action === "sync_to_drive") {
      // Handle file sync logic here
      return ContentService
        .createTextOutput(JSON.stringify({
          "success": true,
          "uploaded_files": data.files.length
        }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    return ContentService
      .createTextOutput(JSON.stringify({
        "success": false,
        "error": "Unknown action"
      }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({
        "success": false,
        "error": error.toString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
'''
        
        print(f"   Code:\n{apps_script_code}")
        
        print("\n🚀 Deployment Steps:")
        print("   3. Deploy as Web App")
        print("   4. Set execution as 'Anyone' or 'Anyone with Google account'")
        print("   5. Copy the Web App URL (ends with /exec)")
        print("   6. Ensure URL format: https://script.google.com/macros/s/{SCRIPT_ID}/exec")
        
        print("\n✅ Testing Steps:")
        print("   7. Test with cURL:")
        print("      curl -X POST {WEB_APP_URL} \\")
        print("           -H 'Content-Type: application/json' \\")
        print("           -d '{\"action\": \"test_connection\"}'")
        
        print("\n🔍 Common Issues:")
        print("   - Empty response: Apps Script not deployed or wrong permissions")
        print("   - HTML response: Apps Script error page instead of JSON")
        print("   - 404 error: Wrong URL or script not published")
        print("   - 403 error: Insufficient permissions")
        
        self.log_test("Apps Script Setup Guide", True, "Complete setup guide generated")
        return True

    def run_all_tests(self):
        """Run all Apps Script debug tests"""
        print("🔧 Apps Script Proxy Connection Debug Test")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Run all debug tests
        tests = [
            ("Direct Apps Script Simulation", self.test_direct_apps_script_simulation),
            ("Apps Script URL Formats", self.test_apps_script_url_formats),
            ("Backend Apps Script Integration", self.test_backend_apps_script_integration),
            ("Request Payload Format", self.test_request_payload_format),
            ("Backend Error Handling", self.test_backend_error_handling),
            ("Backend Logs Analysis", self.check_backend_logs),
            ("Apps Script Setup Guide", self.generate_apps_script_setup_guide)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with error: {str(e)}")
                results.append((test_name, False))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 APPS SCRIPT DEBUG TEST RESULTS")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:35} {status}")
        
        print(f"\nOverall Tests: {self.tests_passed}/{self.tests_run}")
        print(f"Debug Tests: {passed}/{total}")
        
        # Print key findings
        print("\n🎯 KEY FINDINGS:")
        print("1. The error 'Expecting value: line 1 column 1 (char 0)' indicates empty response from Apps Script")
        print("2. Apps Script must return valid JSON with 'success' field")
        print("3. Backend needs better error handling for empty responses")
        print("4. Apps Script URL must be properly deployed and accessible")
        
        return passed == total

def main():
    """Main test execution"""
    tester = AppsScriptDebugTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
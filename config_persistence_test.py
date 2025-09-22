#!/usr/bin/env python3
"""
System Google Drive Configuration Persistence Debug Test

Specifically testing the issue reported in review request:
"Configuration Status shows 'Not Configured' despite successful Test Connection"

This test will:
1. Login as admin/admin123
2. Configure system Google Drive with user's exact credentials
3. Test the GET /api/gdrive/config endpoint
4. Verify configuration persistence
5. Check for disconnect between save and retrieve operations
"""

import requests
import json
import sys
import time
from datetime import datetime

class ConfigPersistenceDebugTester:
    def __init__(self, base_url="https://continue-session.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # User's exact credentials from review request
        self.user_config = {
            "apps_script_url": "https://script.google.com/macros/s/AKfycbwIfwqaegvfi0IEZPdArCvphZNVPcbS_2eIq_aAop08Kc_9TzDngAs-KCDVb-t2xNc/exec",
            "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        }

    def log(self, message, level="INFO"):
        """Enhanced logging with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run API test with detailed logging"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        self.log(f"🔍 {name}")
        self.log(f"   Method: {method} {url}")
        if data:
            # Mask sensitive data in logs
            safe_data = {k: (v if 'script.google.com' not in str(v) else f"{str(v)[:50]}...") for k, v in data.items()}
            self.log(f"   Data: {json.dumps(safe_data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)

            self.log(f"   Response: {response.status_code}")
            
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {}
                self.log(f"   Raw response: {response.text}")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED")
            else:
                self.log(f"❌ FAILED (Expected {expected_status}, got {response.status_code})")
                
            return success, response_data

        except Exception as e:
            self.log(f"❌ ERROR: {str(e)}")
            return False, {}

    def test_authentication(self):
        """Test admin authentication"""
        self.log("=" * 80)
        self.log("STEP 1: AUTHENTICATION", "STEP")
        self.log("=" * 80)
        
        success, response = self.run_test(
            "Admin Login (admin/admin123)",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_info = response.get('user', {})
            self.log(f"✅ Authenticated as: {user_info.get('full_name')} ({user_info.get('role')})")
            return True
        else:
            self.log("❌ Authentication failed - cannot continue")
            return False

    def test_initial_config_state(self):
        """Check initial configuration state"""
        self.log("=" * 80)
        self.log("STEP 2: INITIAL CONFIGURATION STATE", "STEP")
        self.log("=" * 80)
        
        success, config_data = self.run_test(
            "GET Initial Configuration",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            self.log("Initial configuration state:")
            for key, value in config_data.items():
                if isinstance(value, str) and len(value) > 50:
                    self.log(f"   {key}: {value[:50]}...")
                else:
                    self.log(f"   {key}: {value}")
            return True, config_data
        else:
            self.log("❌ Failed to get initial configuration")
            return False, {}

    def test_save_user_configuration(self):
        """Save user's exact configuration"""
        self.log("=" * 80)
        self.log("STEP 3: SAVE USER'S CONFIGURATION", "STEP")
        self.log("=" * 80)
        
        # Use the exact configuration from review request
        config_data = {
            "web_app_url": self.user_config["apps_script_url"],
            "folder_id": self.user_config["folder_id"]
        }
        
        self.log(f"Saving configuration with:")
        self.log(f"   Apps Script URL: {self.user_config['apps_script_url'][:50]}...")
        self.log(f"   Folder ID: {self.user_config['folder_id']}")
        
        success, response = self.run_test(
            "POST Save Configuration",
            "POST",
            "gdrive/configure-proxy",
            200,
            data=config_data
        )
        
        if success:
            self.log("✅ Configuration saved successfully")
            self.log(f"   Response message: {response.get('message')}")
            self.log(f"   Configuration saved: {response.get('configuration_saved')}")
            return True, response
        else:
            self.log("❌ Failed to save configuration")
            return False, response

    def test_retrieve_saved_configuration(self):
        """Retrieve configuration after saving"""
        self.log("=" * 80)
        self.log("STEP 4: RETRIEVE SAVED CONFIGURATION", "STEP")
        self.log("=" * 80)
        
        success, config_data = self.run_test(
            "GET Configuration After Save",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            self.log("Retrieved configuration:")
            for key, value in config_data.items():
                if isinstance(value, str) and len(value) > 50:
                    self.log(f"   {key}: {value[:50]}...")
                else:
                    self.log(f"   {key}: {value}")
            
            # Check if configuration shows as configured
            is_configured = config_data.get('configured', False)
            self.log(f"Configuration status: {'CONFIGURED' if is_configured else 'NOT CONFIGURED'}")
            
            return True, config_data
        else:
            self.log("❌ Failed to retrieve configuration")
            return False, {}

    def test_configuration_status(self):
        """Test the status endpoint"""
        self.log("=" * 80)
        self.log("STEP 5: CHECK CONFIGURATION STATUS", "STEP")
        self.log("=" * 80)
        
        success, status_data = self.run_test(
            "GET Configuration Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            status = status_data.get('status')
            message = status_data.get('message')
            
            self.log(f"Status: {status}")
            self.log(f"Message: {message}")
            
            if status == 'connected':
                self.log("✅ Status shows CONNECTED")
                return True, status_data
            elif status == 'not_configured':
                self.log("❌ Status shows NOT CONFIGURED - THIS IS THE REPORTED ISSUE")
                return False, status_data
            else:
                self.log(f"⚠️ Unexpected status: {status}")
                return False, status_data
        else:
            self.log("❌ Failed to get status")
            return False, {}

    def test_persistence_consistency(self):
        """Test the consistency between save and retrieve operations"""
        self.log("=" * 80)
        self.log("STEP 6: PERSISTENCE CONSISTENCY CHECK", "STEP")
        self.log("=" * 80)
        
        # Save configuration
        self.log("Sub-test 1: Save configuration")
        save_success, save_response = self.test_save_user_configuration()
        
        # Wait a moment for any async operations
        time.sleep(1)
        
        # Retrieve configuration
        self.log("Sub-test 2: Retrieve configuration")
        get_success, get_response = self.test_retrieve_saved_configuration()
        
        # Check status
        self.log("Sub-test 3: Check status")
        status_success, status_response = self.test_configuration_status()
        
        # Analyze consistency
        self.log("CONSISTENCY ANALYSIS:")
        self.log(f"   Save successful: {save_success}")
        self.log(f"   Retrieve successful: {get_success}")
        self.log(f"   Status check successful: {status_success}")
        
        if save_success and get_success:
            # Check if saved data matches retrieved data
            saved_configured = save_response.get('configuration_saved', False)
            retrieved_configured = get_response.get('configured', False)
            status_connected = status_response.get('status') == 'connected'
            
            self.log(f"   Saved as configured: {saved_configured}")
            self.log(f"   Retrieved as configured: {retrieved_configured}")
            self.log(f"   Status shows connected: {status_connected}")
            
            if saved_configured and retrieved_configured and status_connected:
                self.log("✅ CONSISTENCY CHECK PASSED - All endpoints agree")
                return True
            else:
                self.log("❌ CONSISTENCY CHECK FAILED - Endpoints disagree")
                if saved_configured and not retrieved_configured:
                    self.log("   ISSUE: Configuration saved but not retrieved correctly")
                if retrieved_configured and not status_connected:
                    self.log("   ISSUE: Configuration retrieved but status doesn't reflect it")
                return False
        else:
            self.log("❌ CONSISTENCY CHECK FAILED - Basic operations failed")
            return False

    def test_direct_apps_script_verification(self):
        """Test direct communication with Apps Script to verify it's working"""
        self.log("=" * 80)
        self.log("STEP 7: DIRECT APPS SCRIPT VERIFICATION", "STEP")
        self.log("=" * 80)
        
        apps_script_url = self.user_config["apps_script_url"]
        folder_id = self.user_config["folder_id"]
        
        test_payload = {
            "action": "test_connection",
            "folder_id": folder_id
        }
        
        self.log(f"Testing direct Apps Script communication:")
        self.log(f"   URL: {apps_script_url[:50]}...")
        self.log(f"   Folder ID: {folder_id}")
        
        try:
            response = requests.post(
                apps_script_url,
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    success = response_data.get('success', False)
                    
                    self.log(f"   Apps Script success: {success}")
                    if success:
                        self.log("✅ Direct Apps Script communication working")
                        return True
                    else:
                        self.log("❌ Apps Script returned success=false")
                        self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                        return False
                except:
                    self.log(f"❌ Apps Script response not JSON: {response.text}")
                    return False
            else:
                self.log(f"❌ Apps Script returned status {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Direct Apps Script test failed: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run the complete test suite"""
        self.log("🚢 SYSTEM GOOGLE DRIVE CONFIGURATION PERSISTENCE DEBUG")
        self.log("Review Request: Configuration Status shows 'Not Configured' despite successful Test Connection")
        self.log("=" * 80)
        
        # Test sequence
        test_results = []
        
        # Step 1: Authentication
        auth_success = self.test_authentication()
        if not auth_success:
            self.log("❌ Cannot continue without authentication")
            return False
        test_results.append(("Authentication", auth_success))
        
        # Step 2: Initial state
        initial_success, initial_config = self.test_initial_config_state()
        test_results.append(("Initial State Check", initial_success))
        
        # Step 3: Direct Apps Script verification
        apps_script_success = self.test_direct_apps_script_verification()
        test_results.append(("Direct Apps Script Test", apps_script_success))
        
        # Step 4: Persistence consistency test
        consistency_success = self.test_persistence_consistency()
        test_results.append(("Persistence Consistency", consistency_success))
        
        # Final analysis
        self.log("=" * 80)
        self.log("FINAL ANALYSIS", "RESULT")
        self.log("=" * 80)
        
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        self.log("\nTest Results Summary:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"   {test_name:25} {status}")
        
        # Determine root cause
        if consistency_success:
            self.log("\n✅ CONCLUSION: Configuration persistence is working correctly")
            self.log("   The issue may be in the frontend display logic")
            self.log("   Recommendation: Check frontend code that displays configuration status")
        else:
            self.log("\n❌ CONCLUSION: Configuration persistence has issues")
            self.log("   The backend save/retrieve logic needs investigation")
            self.log("   Recommendation: Check database operations and API endpoint logic")
        
        return consistency_success

def main():
    """Main execution"""
    tester = ConfigPersistenceDebugTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
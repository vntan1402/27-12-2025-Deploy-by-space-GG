#!/usr/bin/env python3
"""
Apps Script Working Configuration Test
Testing with a working Apps Script URL to verify all functionality works correctly.
"""

import requests
import sys
import json
from datetime import datetime, timezone
import time

class AppsScriptWorkingTester:
    def __init__(self, base_url="https://shipcertdrive.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Working Apps Script URL (currently configured)
        self.working_apps_script_url = "https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec"
        self.folder_id = "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {}

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                return True, response_data
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                return False, response_data

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def test_login(self):
        """Test login and get token"""
        print(f"\n🔐 Testing Authentication")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"✅ Login successful")
            return True
        return False

    def test_working_apps_script_configure(self):
        """Test configure-proxy with working Apps Script URL"""
        print(f"\n📝 Testing Apps Script Configure with Working URL")
        
        config_data = {
            "web_app_url": self.working_apps_script_url,
            "folder_id": self.folder_id
        }
        
        success, response = self.run_test(
            "Configure Working Apps Script",
            "POST",
            "gdrive/configure-proxy",
            200,
            data=config_data
        )
        
        if success:
            print(f"✅ Working Apps Script configured successfully")
            print(f"   Message: {response.get('message', 'N/A')}")
        
        return success

    def test_config_verification(self):
        """Test config shows apps_script method"""
        print(f"\n📋 Testing Config Verification")
        
        success, response = self.run_test(
            "Get Config After Apps Script Setup",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            print(f"✅ Config retrieved: configured={response.get('configured')}")
            print(f"   Folder ID: {response.get('folder_id')}")
        
        return success

    def test_status_verification(self):
        """Test status endpoint"""
        print(f"\n📊 Testing Status Verification")
        
        success, response = self.run_test(
            "Get Status with Apps Script",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            print(f"✅ Status retrieved: configured={response.get('configured')}")
            print(f"   Local files: {response.get('local_files', 0)}")
            print(f"   Drive files: {response.get('drive_files', 0)}")
        
        return success

    def test_sync_functionality(self):
        """Test sync via Apps Script proxy"""
        print(f"\n🔄 Testing Sync Functionality")
        
        success, response = self.run_test(
            "Sync via Apps Script Proxy",
            "POST",
            "gdrive/sync-to-drive-proxy",
            200
        )
        
        if success:
            print(f"✅ Sync successful: {response.get('success')}")
            message = response.get('message', '')
            if 'files uploaded' in message:
                print(f"   Files uploaded successfully")
        
        return success

    def run_comprehensive_test(self):
        """Run comprehensive test with working Apps Script"""
        print("🚀 Apps Script Working Configuration Test")
        print("=" * 60)
        print(f"Working Apps Script URL: {self.working_apps_script_url}")
        print(f"Folder ID: {self.folder_id}")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Run all tests
        test_results = []
        
        test_results.append(("Configure Working Apps Script", self.test_working_apps_script_configure()))
        test_results.append(("Config Verification", self.test_config_verification()))
        test_results.append(("Status Verification", self.test_status_verification()))
        test_results.append(("Sync Functionality", self.test_sync_functionality()))
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 WORKING APPS SCRIPT TEST RESULTS")
        print("=" * 60)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:35} {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    tester = AppsScriptWorkingTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
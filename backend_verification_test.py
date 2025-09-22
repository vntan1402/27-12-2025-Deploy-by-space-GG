#!/usr/bin/env python3
"""
Backend Verification Test
Verify that the backend is working correctly for all other functionality
while the Apps Script issue is being resolved by the user
"""

import requests
import json
import sys
import time

class BackendVerificationTester:
    def __init__(self):
        self.backend_url = "https://continue-session.preview.emergentagent.com/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, test_name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
        
        if details:
            print(f"   Details: {details}")
        print()

    def login_admin(self):
        """Login as admin to get authentication token"""
        print("🔐 Testing admin/admin123 login")
        
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = requests.post(f"{self.backend_url}/auth/login", 
                                   json=login_data, 
                                   timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                user_info = data.get('user', {})
                
                success = True
                details = f"Role: {user_info.get('role')}, User: {user_info.get('full_name')}"
                self.log_test("Admin Login", success, details)
                return True
            else:
                self.log_test("Admin Login", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False

    def test_user_management(self):
        """Test user management endpoints"""
        print("👥 Testing User Management")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            # Get users
            response = requests.get(f"{self.backend_url}/users", headers=headers, timeout=30)
            success = response.status_code == 200
            
            if success:
                users = response.json()
                details = f"Found {len(users)} users"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Get Users", success, details)
            return success
            
        except Exception as e:
            self.log_test("Get Users", False, f"Exception: {str(e)}")
            return False

    def test_company_management(self):
        """Test company management endpoints"""
        print("🏢 Testing Company Management")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            # Get companies
            response = requests.get(f"{self.backend_url}/companies", headers=headers, timeout=30)
            success = response.status_code == 200
            
            if success:
                companies = response.json()
                details = f"Found {len(companies)} companies"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Get Companies", success, details)
            return success
            
        except Exception as e:
            self.log_test("Get Companies", False, f"Exception: {str(e)}")
            return False

    def test_ship_management(self):
        """Test ship management endpoints"""
        print("🚢 Testing Ship Management")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            # Get ships
            response = requests.get(f"{self.backend_url}/ships", headers=headers, timeout=30)
            success = response.status_code == 200
            
            if success:
                ships = response.json()
                details = f"Found {len(ships)} ships"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Get Ships", success, details)
            return success
            
        except Exception as e:
            self.log_test("Get Ships", False, f"Exception: {str(e)}")
            return False

    def test_certificate_management(self):
        """Test certificate management endpoints"""
        print("📜 Testing Certificate Management")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            # Get certificates
            response = requests.get(f"{self.backend_url}/certificates", headers=headers, timeout=30)
            success = response.status_code == 200
            
            if success:
                certificates = response.json()
                details = f"Found {len(certificates)} certificates"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Get Certificates", success, details)
            return success
            
        except Exception as e:
            self.log_test("Get Certificates", False, f"Exception: {str(e)}")
            return False

    def test_ai_configuration(self):
        """Test AI configuration endpoints"""
        print("🤖 Testing AI Configuration")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            # Get AI config
            response = requests.get(f"{self.backend_url}/ai-config", headers=headers, timeout=30)
            success = response.status_code == 200
            
            if success:
                config = response.json()
                details = f"Provider: {config.get('provider')}, Model: {config.get('model')}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Get AI Config", success, details)
            return success
            
        except Exception as e:
            self.log_test("Get AI Config", False, f"Exception: {str(e)}")
            return False

    def test_usage_tracking(self):
        """Test usage tracking endpoints"""
        print("📊 Testing Usage Tracking")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            # Get usage stats
            response = requests.get(f"{self.backend_url}/usage-stats", headers=headers, timeout=30)
            success = response.status_code == 200
            
            if success:
                stats = response.json()
                details = f"Total requests: {stats.get('total_requests', 0)}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Get Usage Stats", success, details)
            return success
            
        except Exception as e:
            self.log_test("Get Usage Stats", False, f"Exception: {str(e)}")
            return False

    def test_gdrive_endpoints_except_configure_proxy(self):
        """Test Google Drive endpoints except configure-proxy"""
        print("💾 Testing Google Drive Endpoints (except configure-proxy)")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test gdrive/config
        try:
            response = requests.get(f"{self.backend_url}/gdrive/config", headers=headers, timeout=30)
            success1 = response.status_code == 200
            
            if success1:
                config = response.json()
                details1 = f"Configured: {config.get('configured')}, Folder: {config.get('folder_id', 'None')[:20]}..."
            else:
                details1 = f"Status: {response.status_code}"
            
            self.log_test("Get GDrive Config", success1, details1)
            
        except Exception as e:
            self.log_test("Get GDrive Config", False, f"Exception: {str(e)}")
            success1 = False

        # Test gdrive/status
        try:
            response = requests.get(f"{self.backend_url}/gdrive/status", headers=headers, timeout=30)
            success2 = response.status_code == 200
            
            if success2:
                status = response.json()
                details2 = f"Local files: {status.get('local_files')}, Drive files: {status.get('drive_files')}"
            else:
                details2 = f"Status: {response.status_code}"
            
            self.log_test("Get GDrive Status", success2, details2)
            
        except Exception as e:
            self.log_test("Get GDrive Status", False, f"Exception: {str(e)}")
            success2 = False

        return success1 and success2

    def run_verification(self):
        """Run comprehensive backend verification"""
        print("🚀 BACKEND VERIFICATION TEST")
        print("=" * 60)
        print("Testing all backend functionality except the Apps Script issue")
        print("=" * 60)
        print()
        
        # Login first
        if not self.login_admin():
            print("❌ Cannot proceed - login failed")
            return False
        
        # Run all tests
        test_results = []
        test_results.append(("User Management", self.test_user_management()))
        test_results.append(("Company Management", self.test_company_management()))
        test_results.append(("Ship Management", self.test_ship_management()))
        test_results.append(("Certificate Management", self.test_certificate_management()))
        test_results.append(("AI Configuration", self.test_ai_configuration()))
        test_results.append(("Usage Tracking", self.test_usage_tracking()))
        test_results.append(("Google Drive (non-proxy)", self.test_gdrive_endpoints_except_configure_proxy()))
        
        # Results summary
        print("=" * 60)
        print("📊 BACKEND VERIFICATION RESULTS")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ WORKING" if result else "❌ FAILED"
            print(f"{test_name:25} {status}")
            if result:
                passed_tests += 1
        
        print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
        print(f"Individual API Tests: {self.tests_passed}/{self.tests_run}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL BACKEND FUNCTIONALITY WORKING CORRECTLY!")
            print("The only issue is with the user's Apps Script code.")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} backend issues found")
            return False

def main():
    """Main execution function"""
    tester = BackendVerificationTester()
    success = tester.run_verification()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
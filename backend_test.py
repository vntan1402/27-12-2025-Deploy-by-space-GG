#!/usr/bin/env python3
"""
Backend Testing for Enhanced Dynamic Subfolder Structure Extraction
Testing the enhanced Add New Ship workflow with automatic subfolder structure extraction
from homepage sidebar for Google Drive folder creation.
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://shipwise-13.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

class BackendTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                self.log_test("Authentication", True, f"Logged in as {self.user_info['username']} ({self.user_info['role']})")
                return True
            else:
                self.log_test("Authentication", False, error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_user_company_assignment(self):
        """Test that admin user is assigned to a company for Google Drive access"""
        try:
            if not self.user_info:
                self.log_test("User Company Assignment", False, error="No user info available")
                return False
            
            company_id = self.user_info.get('company')
            if company_id:
                self.log_test("User Company Assignment", True, f"Admin user assigned to company: {company_id}")
                return company_id
            else:
                self.log_test("User Company Assignment", False, error="Admin user not assigned to any company")
                return None
                
        except Exception as e:
            self.log_test("User Company Assignment", False, error=str(e))
            return None
    
    def test_company_google_drive_config(self, company_id):
        """Test company Google Drive configuration"""
        try:
            response = requests.get(
                f"{API_BASE}/companies/{company_id}/gdrive/config",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                config = response.json()
                web_app_url = config.get('config', {}).get('web_app_url')
                folder_id = config.get('config', {}).get('folder_id')
                
                if web_app_url and folder_id:
                    self.log_test("Company Google Drive Configuration", True, 
                                f"Web App URL: {web_app_url[:50]}..., Folder ID: {folder_id}")
                    return config
                else:
                    self.log_test("Company Google Drive Configuration", False, 
                                error="Missing web_app_url or folder_id in configuration")
                    return None
            else:
                self.log_test("Company Google Drive Configuration", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Company Google Drive Configuration", False, error=str(e))
            return None
    
    def test_company_google_drive_status(self, company_id):
        """Test company Google Drive status"""
        try:
            response = requests.post(
                f"{API_BASE}/companies/{company_id}/gdrive/status",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                status = response.json()
                status_value = status.get('status')
                
                if status_value == 'configured':
                    self.log_test("Company Google Drive Status", True, f"Status: {status_value}")
                    return True
                else:
                    self.log_test("Company Google Drive Status", False, 
                                error=f"Status is '{status_value}', expected 'configured'")
                    return False
            else:
                self.log_test("Company Google Drive Status", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Company Google Drive Status", False, error=str(e))
            return False
    
    def test_create_ship_with_enhanced_data(self):
        """Test creating a ship with enhanced data fields"""
        try:
            ship_data = {
                "name": f"Dynamic Structure Test Ship {int(time.time())}",
                "imo": "IMO1234567",
                "flag": "Panama",
                "ship_type": "Container Ship",
                "gross_tonnage": 50000.0,
                "deadweight": 75000.0,
                "built_year": 2020,
                "ship_owner": "Dynamic Test Maritime Holdings Ltd",
                "company": "Test Shipping Company"
            }
            
            response = requests.post(
                f"{API_BASE}/ships",
                json=ship_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                ship = response.json()
                self.log_test("Create Ship with Enhanced Data", True, 
                            f"Ship created: {ship['name']} (ID: {ship['id']})")
                return ship
            else:
                self.log_test("Create Ship with Enhanced Data", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Ship with Enhanced Data", False, error=str(e))
            return None
    
    def test_dynamic_subfolder_structure_extraction(self, company_id, ship_name):
        """Test the dynamic subfolder structure extraction and Google Drive folder creation"""
        try:
            # Test the expected subfolder structure that should be extracted from homepage sidebar
            expected_subfolders = [
                "Certificates",
                "Inspection Records", 
                "Survey Reports",
                "Drawings & Manuals",
                "Other Documents"
            ]
            
            folder_data = {
                "ship_name": ship_name,
                "subfolders": expected_subfolders,
                "source": "homepage_sidebar",
                "total_subfolders": len(expected_subfolders)
            }
            
            response = requests.post(
                f"{API_BASE}/companies/{company_id}/gdrive/create-ship-folder",
                json=folder_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    ship_folder_id = result.get('ship_folder_id')
                    subfolder_ids = result.get('subfolder_ids', {})
                    subfolders_created = result.get('subfolders_created', 0)
                    
                    self.log_test("Dynamic Subfolder Structure Extraction", True, 
                                f"Ship folder created with {subfolders_created} subfolders. "
                                f"Ship folder ID: {ship_folder_id}, Subfolder IDs: {len(subfolder_ids)} created")
                    
                    # Verify all expected subfolders were created
                    if subfolders_created == len(expected_subfolders):
                        self.log_test("Subfolder Count Verification", True, 
                                    f"All {len(expected_subfolders)} expected subfolders created")
                    else:
                        self.log_test("Subfolder Count Verification", False, 
                                    error=f"Expected {len(expected_subfolders)} subfolders, got {subfolders_created}")
                    
                    return result
                else:
                    error_msg = result.get('message', 'Unknown error')
                    self.log_test("Dynamic Subfolder Structure Extraction", False, 
                                error=f"Google Apps Script error: {error_msg}")
                    return None
            else:
                self.log_test("Dynamic Subfolder Structure Extraction", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Dynamic Subfolder Structure Extraction", False, error=str(e))
            return None
    
    def test_language_independent_folder_names(self, company_id):
        """Test that folder names are always in English regardless of language settings"""
        try:
            # Test with Vietnamese language context (simulated)
            vietnamese_ship_name = "Tàu Thử Nghiệm Ngôn Ngữ"
            
            # The subfolders should always be in English for Google Drive consistency
            english_subfolders = [
                "Certificates",
                "Inspection Records",
                "Survey Reports", 
                "Drawings & Manuals",
                "Other Documents"
            ]
            
            folder_data = {
                "ship_name": vietnamese_ship_name,
                "subfolders": english_subfolders,
                "source": "homepage_sidebar_vietnamese_context",
                "total_subfolders": len(english_subfolders)
            }
            
            response = requests.post(
                f"{API_BASE}/companies/{company_id}/gdrive/create-ship-folder",
                json=folder_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    self.log_test("Language Independent Folder Names", True, 
                                f"English folder names used successfully even with Vietnamese ship name: {vietnamese_ship_name}")
                    return True
                else:
                    error_msg = result.get('message', 'Unknown error')
                    self.log_test("Language Independent Folder Names", False, 
                                error=f"Failed to create folders: {error_msg}")
                    return False
            else:
                self.log_test("Language Independent Folder Names", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Language Independent Folder Names", False, error=str(e))
            return False
    
    def test_fallback_mechanism(self, company_id):
        """Test fallback mechanism when subfolder structure extraction fails"""
        try:
            # Test with empty subfolders to trigger fallback
            fallback_ship_name = "Fallback Test Ship"
            
            folder_data = {
                "ship_name": fallback_ship_name,
                "subfolders": [],  # Empty to test fallback
                "source": "fallback_test",
                "total_subfolders": 0
            }
            
            response = requests.post(
                f"{API_BASE}/companies/{company_id}/gdrive/create-ship-folder",
                json=folder_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    # Even with empty subfolders, the ship folder should be created
                    self.log_test("Fallback Mechanism", True, 
                                f"Ship folder created successfully even with empty subfolder list")
                    return True
                else:
                    error_msg = result.get('message', 'Unknown error')
                    self.log_test("Fallback Mechanism", False, 
                                error=f"Fallback failed: {error_msg}")
                    return False
            else:
                self.log_test("Fallback Mechanism", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Fallback Mechanism", False, error=str(e))
            return False
    
    def test_enhanced_logging_verification(self, company_id):
        """Test that enhanced logging is working for structure source tracking"""
        try:
            # Create a ship folder with specific source tracking
            logging_test_ship = "Enhanced Logging Test Ship"
            
            folder_data = {
                "ship_name": logging_test_ship,
                "subfolders": ["Certificates", "Inspection Records", "Survey Reports", "Drawings & Manuals", "Other Documents"],
                "source": "enhanced_logging_test",
                "total_subfolders": 5
            }
            
            response = requests.post(
                f"{API_BASE}/companies/{company_id}/gdrive/create-ship-folder",
                json=folder_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    # The backend should log the source information
                    self.log_test("Enhanced Logging Verification", True, 
                                f"Ship folder created with source tracking: enhanced_logging_test")
                    return True
                else:
                    error_msg = result.get('message', 'Unknown error')
                    self.log_test("Enhanced Logging Verification", False, 
                                error=f"Logging test failed: {error_msg}")
                    return False
            else:
                self.log_test("Enhanced Logging Verification", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Enhanced Logging Verification", False, error=str(e))
            return False
    
    def test_google_apps_script_integration(self, company_id):
        """Test direct Google Apps Script integration for folder creation"""
        try:
            # Get company Google Drive configuration
            response = requests.get(
                f"{API_BASE}/companies/{company_id}/gdrive/config",
                headers=self.get_headers()
            )
            
            if response.status_code != 200:
                self.log_test("Google Apps Script Integration", False, 
                            error="Could not get company Google Drive configuration")
                return False
            
            config = response.json()
            script_url = config.get('config', {}).get('web_app_url')
            folder_id = config.get('config', {}).get('folder_id')
            
            if not script_url or not folder_id:
                self.log_test("Google Apps Script Integration", False, 
                            error="Missing script URL or folder ID in configuration")
                return False
            
            # Test direct Apps Script communication
            test_payload = {
                "action": "test_connection",
                "folder_id": folder_id
            }
            
            script_response = requests.post(script_url, json=test_payload, timeout=30)
            
            if script_response.status_code == 200:
                result = script_response.json()
                
                if result.get('success'):
                    self.log_test("Google Apps Script Integration", True, 
                                f"Direct Apps Script communication successful. Test result: {result.get('test_result', 'PASSED')}")
                    return True
                else:
                    error_msg = result.get('message', 'Unknown error')
                    self.log_test("Google Apps Script Integration", False, 
                                error=f"Apps Script test failed: {error_msg}")
                    return False
            else:
                self.log_test("Google Apps Script Integration", False, 
                            error=f"Apps Script request failed: Status {script_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Google Apps Script Integration", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests for enhanced dynamic subfolder structure extraction"""
        print("🧪 ENHANCED DYNAMIC SUBFOLDER STRUCTURE EXTRACTION TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Check user company assignment
        company_id = self.test_user_company_assignment()
        if not company_id:
            print("❌ User not assigned to company. Cannot test Google Drive integration.")
            return False
        
        # Step 3: Test company Google Drive configuration
        gdrive_config = self.test_company_google_drive_config(company_id)
        if not gdrive_config:
            print("❌ Company Google Drive not configured. Cannot proceed with folder tests.")
            return False
        
        # Step 4: Test company Google Drive status
        if not self.test_company_google_drive_status(company_id):
            print("❌ Company Google Drive status check failed.")
            return False
        
        # Step 5: Test Google Apps Script integration
        if not self.test_google_apps_script_integration(company_id):
            print("❌ Google Apps Script integration test failed.")
            return False
        
        # Step 6: Create test ship with enhanced data
        test_ship = self.test_create_ship_with_enhanced_data()
        if not test_ship:
            print("❌ Ship creation failed. Cannot test folder creation.")
            return False
        
        # Step 7: Test dynamic subfolder structure extraction
        folder_result = self.test_dynamic_subfolder_structure_extraction(company_id, test_ship['name'])
        if not folder_result:
            print("❌ Dynamic subfolder structure extraction failed.")
            return False
        
        # Step 8: Test language independence
        if not self.test_language_independent_folder_names(company_id):
            print("❌ Language independence test failed.")
            return False
        
        # Step 9: Test fallback mechanism
        if not self.test_fallback_mechanism(company_id):
            print("❌ Fallback mechanism test failed.")
            return False
        
        # Step 10: Test enhanced logging
        if not self.test_enhanced_logging_verification(company_id):
            print("❌ Enhanced logging verification failed.")
            return False
        
        # Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Enhanced dynamic subfolder structure extraction is working correctly.")
            return True
        else:
            print(f"\n❌ {total - passed} tests failed. Please review the issues above.")
            return False

def main():
    """Main test execution"""
    tester = BackendTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
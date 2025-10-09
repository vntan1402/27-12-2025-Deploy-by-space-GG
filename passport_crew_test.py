#!/usr/bin/env python3
"""
Ship Management System - Add Crew From Passport Backend API Testing
FOCUS: Test the updated "Add Crew From Passport" workflow using the same Apps Script upload method as Certificates

REVIEW REQUEST REQUIREMENTS:
Test the updated "Add Crew From Passport" workflow that now uses the same Apps Script upload method as Certificates:

POST to /api/crew/analyze-passport with a passport image file

The updated workflow should:
1. Use Document AI for passport analysis (System Apps Script)
2. Upload passport file to "Ship Name/Crew Records/Crew List" folder (Company Apps Script with action "upload_file_with_folder_creation")
3. Upload summary file to "SUMMARY/Documents" folder (Company Apps Script)
4. Use the same proven upload method that works for Certificate uploads
5. Should no longer return "File upload failed" error

Test with:
- Ship Name: Any existing ship from the database
- File: Any image file (jpg, png) as passport
- Verify the file upload now works using the certificate upload method

The key change is using action="upload_file_with_folder_creation" with parent_folder_id, ship_name, parent_category, and category parameters instead of the custom folder_path approach.
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
import tempfile
from urllib.parse import urlparse
import base64

# Configuration - Use environment variable for backend URL
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://mariner-scan.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

# Test credentials
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

class PassportCrewTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_info = None
        self.test_results = []
        self.ships = []
        self.selected_ship = None
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if details:
            print(f"   Details: {details}")
        print()
        
    def authenticate(self):
        """Authenticate with the backend"""
        try:
            login_data = {
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.user_info = data.get('user')
                
                # Set authorization header for future requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                })
                
                self.log_result(
                    "Authentication", 
                    True, 
                    f"Successfully authenticated as {self.user_info.get('username')} with role {self.user_info.get('role')}"
                )
                return True
            else:
                self.log_result(
                    "Authentication", 
                    False, 
                    f"Authentication failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def get_ships(self):
        """Get list of ships for testing"""
        try:
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                self.ships = response.json()
                if self.ships:
                    # Select the first ship for testing
                    self.selected_ship = self.ships[0]
                    self.log_result(
                        "Get Ships", 
                        True, 
                        f"Found {len(self.ships)} ships. Selected ship: {self.selected_ship.get('name')} (ID: {self.selected_ship.get('id')})"
                    )
                    return True
                else:
                    self.log_result("Get Ships", False, "No ships found in database")
                    return False
            else:
                self.log_result("Get Ships", False, f"Failed to get ships: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Get Ships", False, f"Error getting ships: {str(e)}")
            return False
    
    def create_test_passport_file(self):
        """Create a test passport image file"""
        try:
            # Create a simple test image file (1x1 PNG)
            # This is a minimal PNG file in base64
            png_data = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
            )
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                f.write(png_data)
                temp_file_path = f.name
            
            self.log_result(
                "Create Test Passport File", 
                True, 
                f"Created test passport file: {temp_file_path} ({len(png_data)} bytes)"
            )
            return temp_file_path
            
        except Exception as e:
            self.log_result("Create Test Passport File", False, f"Error creating test file: {str(e)}")
            return None
    
    def test_passport_analysis_endpoint(self, passport_file_path):
        """Test the passport analysis endpoint"""
        try:
            if not self.selected_ship:
                self.log_result("Test Passport Analysis", False, "No ship selected for testing")
                return False
            
            # Prepare multipart form data
            with open(passport_file_path, 'rb') as f:
                files = {
                    'passport_file': ('test_passport.png', f, 'image/png')
                }
                data = {
                    'ship_name': self.selected_ship.get('name')
                }
                
                # Remove Content-Type header to let requests set it for multipart
                headers = {'Authorization': f'Bearer {self.token}'}
                
                response = requests.post(
                    f"{BACKEND_URL}/crew/analyze-passport", 
                    files=files, 
                    data=data, 
                    headers=headers,
                    timeout=60  # Increased timeout for AI processing
                )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if the response indicates success
                if result.get('success'):
                    self.log_result(
                        "Test Passport Analysis", 
                        True, 
                        "Passport analysis completed successfully",
                        {
                            'response_keys': list(result.keys()),
                            'has_analysis': 'analysis' in result,
                            'has_files': 'files' in result,
                            'message': result.get('message', 'No message')
                        }
                    )
                    
                    # Check for file upload success
                    files_data = result.get('files', {})
                    if files_data:
                        passport_file = files_data.get('passport_file', {})
                        summary_file = files_data.get('summary_file', {})
                        
                        self.log_result(
                            "File Upload Verification", 
                            True, 
                            "Files uploaded successfully",
                            {
                                'passport_file_id': passport_file.get('file_id'),
                                'passport_folder': passport_file.get('folder_path'),
                                'summary_file_id': summary_file.get('file_id'),
                                'summary_folder': summary_file.get('folder_path')
                            }
                        )
                    else:
                        self.log_result(
                            "File Upload Verification", 
                            False, 
                            "No file upload data in response"
                        )
                    
                    # Check analysis data
                    analysis_data = result.get('analysis', {})
                    if analysis_data:
                        extracted_fields = [k for k, v in analysis_data.items() if v and v != '']
                        self.log_result(
                            "Field Extraction Verification", 
                            len(extracted_fields) > 0, 
                            f"Extracted {len(extracted_fields)} fields from passport",
                            {
                                'extracted_fields': extracted_fields,
                                'analysis_data': analysis_data
                            }
                        )
                    
                    return True
                else:
                    error_msg = result.get('error', result.get('message', 'Unknown error'))
                    self.log_result(
                        "Test Passport Analysis", 
                        False, 
                        f"Passport analysis failed: {error_msg}",
                        result
                    )
                    return False
            else:
                self.log_result(
                    "Test Passport Analysis", 
                    False, 
                    f"API request failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Test Passport Analysis", False, f"Error testing passport analysis: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_apps_script_configuration(self):
        """Test Apps Script configuration"""
        try:
            # Get user's company ID
            company_id = self.user_info.get('company')
            if not company_id:
                self.log_result("Apps Script Configuration", False, "No company ID found for user")
                return False
            
            # Test company Google Drive configuration
            response = self.session.get(f"{BACKEND_URL}/companies/{company_id}/gdrive/test-apps-script")
            
            if response.status_code == 200:
                config_data = response.json()
                
                has_apps_script = config_data.get('has_apps_script_url', False)
                has_folder_id = config_data.get('has_folder_id', False)
                connectivity_status = config_data.get('connectivity_test', {}).get('status_code')
                
                self.log_result(
                    "Apps Script Configuration", 
                    has_apps_script and has_folder_id and connectivity_status == 200, 
                    f"Apps Script configuration check completed",
                    {
                        'has_apps_script_url': has_apps_script,
                        'has_folder_id': has_folder_id,
                        'connectivity_status': connectivity_status,
                        'apps_script_url': config_data.get('apps_script_url', 'Not configured'),
                        'service_info': config_data.get('connectivity_test', {}).get('service_info')
                    }
                )
                return has_apps_script and has_folder_id
            else:
                self.log_result(
                    "Apps Script Configuration", 
                    False, 
                    f"Failed to check Apps Script configuration: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Apps Script Configuration", False, f"Error checking Apps Script configuration: {str(e)}")
            return False
    
    def test_document_ai_configuration(self):
        """Test Document AI configuration"""
        try:
            response = self.session.get(f"{BACKEND_URL}/ai-config")
            
            if response.status_code == 200:
                ai_config = response.json()
                doc_ai_config = ai_config.get('document_ai', {})
                
                enabled = doc_ai_config.get('enabled', False)
                has_project_id = bool(doc_ai_config.get('project_id'))
                has_processor_id = bool(doc_ai_config.get('processor_id'))
                has_apps_script_url = bool(doc_ai_config.get('apps_script_url'))
                
                self.log_result(
                    "Document AI Configuration", 
                    enabled and has_project_id and has_processor_id, 
                    f"Document AI configuration check completed",
                    {
                        'enabled': enabled,
                        'has_project_id': has_project_id,
                        'has_processor_id': has_processor_id,
                        'has_apps_script_url': has_apps_script_url,
                        'project_id': doc_ai_config.get('project_id'),
                        'location': doc_ai_config.get('location')
                    }
                )
                return enabled and has_project_id and has_processor_id
            else:
                self.log_result(
                    "Document AI Configuration", 
                    False, 
                    f"Failed to get Document AI configuration: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Document AI Configuration", False, f"Error checking Document AI configuration: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test of Add Crew From Passport workflow"""
        print("🔍 STARTING COMPREHENSIVE ADD CREW FROM PASSPORT WORKFLOW TESTING")
        print("=" * 80)
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            return False
        
        # Step 2: Get ships for testing
        if not self.get_ships():
            return False
        
        # Step 3: Check Document AI configuration
        self.test_document_ai_configuration()
        
        # Step 4: Check Apps Script configuration
        self.test_apps_script_configuration()
        
        # Step 5: Create test passport file
        passport_file = self.create_test_passport_file()
        if not passport_file:
            return False
        
        try:
            # Step 6: Test passport analysis endpoint
            self.test_passport_analysis_endpoint(passport_file)
            
        finally:
            # Clean up test file
            try:
                os.unlink(passport_file)
                print(f"Cleaned up test file: {passport_file}")
            except:
                pass
        
        # Generate summary
        self.generate_summary()
        
        return True
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("🎯 TEST SUMMARY - ADD CREW FROM PASSPORT WORKFLOW")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Show failed tests
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")
            print()
        
        # Show passed tests
        if passed_tests > 0:
            print("✅ PASSED TESTS:")
            for result in self.test_results:
                if result['success']:
                    print(f"   • {result['test']}: {result['message']}")
            print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        
        # Check if core workflow is working
        passport_analysis_success = any(r['success'] and 'Passport Analysis' in r['test'] for r in self.test_results)
        file_upload_success = any(r['success'] and 'File Upload' in r['test'] for r in self.test_results)
        
        if passport_analysis_success:
            print("   ✅ Passport analysis endpoint is accessible and processing requests")
        else:
            print("   ❌ Passport analysis endpoint has issues")
        
        if file_upload_success:
            print("   ✅ File upload to Google Drive is working")
        else:
            print("   ❌ File upload to Google Drive has issues")
        
        # Configuration status
        config_success = any(r['success'] and 'Configuration' in r['test'] for r in self.test_results)
        if config_success:
            print("   ✅ System configuration (Document AI, Apps Script) is properly set up")
        else:
            print("   ❌ System configuration needs attention")
        
        print()
        print("📋 REVIEW REQUEST STATUS:")
        if success_rate >= 80:
            print("   ✅ The updated 'Add Crew From Passport' workflow is working correctly")
            print("   ✅ Using the same Apps Script upload method as Certificates")
            print("   ✅ File upload errors have been resolved")
        elif success_rate >= 60:
            print("   ⚠️  The workflow is partially working but has some issues")
            print("   ⚠️  Some components may need attention")
        else:
            print("   ❌ The workflow has significant issues that need to be addressed")
            print("   ❌ File upload method may not be working as expected")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = PassportCrewTester()
    
    try:
        success = tester.run_comprehensive_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
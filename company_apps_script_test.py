#!/usr/bin/env python3
"""
Company Apps Script Configuration and Connectivity Test
FOCUS: Test the new Company Apps Script configuration and connectivity endpoint

REVIEW REQUEST REQUIREMENTS:
Test the new Company Apps Script configuration and connectivity endpoint:
POST to /api/companies/cd1951d0-223e-4a09-865b-593047ed8c2d/gdrive/test-apps-script

This endpoint should:
1. Return the current Apps Script URL and folder ID configuration
2. Test connectivity to the Apps Script URL: https://script.google.com/macros/s/AKfycbyIu1HPOBsuRd8eyb93xzkJCJ8-Ij1uiIkCfxZ5BdLF7M_FmHj6zOTOEO5isc_6ityO/exec
3. Show if the configuration is complete for file uploads
4. Return detailed debugging information

The test should reveal why the "Add Crew From Passport" feature is failing with "File upload failed" - 
either due to missing configuration or Apps Script connectivity issues.
"""

import requests
import json
import os
import sys
import time
from datetime import datetime
import traceback

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
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class CompanyAppsScriptTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Company ID from review request
        self.company_id = "cd1951d0-223e-4a09-865b-593047ed8c2d"
        
        # Expected Apps Script URL from review request
        self.expected_apps_script_url = "https://script.google.com/macros/s/AKfycbyIu1HPOBsuRd8eyb93xzkJCJ8-Ij1uiIkCfxZ5BdLF7M_FmHj6zOTOEO5isc_6ityO/exec"
        
        # Test tracking for Company Apps Script testing
        self.apps_script_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_verified': False,
            
            # Company Apps Script Configuration Endpoint
            'test_apps_script_endpoint_accessible': False,
            'apps_script_url_configuration_returned': False,
            'folder_id_configuration_returned': False,
            'configuration_completeness_checked': False,
            'debugging_information_provided': False,
            
            # Apps Script URL Connectivity Testing
            'apps_script_url_connectivity_tested': False,
            'apps_script_url_accessible': False,
            'apps_script_response_valid': False,
            'apps_script_service_identified': False,
            
            # Configuration Analysis
            'configuration_complete_for_uploads': False,
            'missing_configuration_identified': False,
            'file_upload_failure_cause_identified': False,
            
            # Detailed Debugging
            'detailed_debugging_info_returned': False,
            'error_messages_helpful': False,
            'troubleshooting_guidance_provided': False,
        }
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        # Also store in our log collection
        self.backend_logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
    def authenticate(self):
        """Authenticate with admin1/123456 credentials"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.apps_script_tests['authentication_successful'] = True
                
                # Verify user company matches expected company
                user_company = self.current_user.get('company')
                if user_company:
                    self.apps_script_tests['user_company_verified'] = True
                    self.log(f"   ✅ User company verified: {user_company}")
                
                return True
            else:
                self.log(f"   ❌ Authentication failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_company_apps_script_endpoint(self):
        """Test the Company Apps Script configuration and connectivity endpoint"""
        try:
            self.log("🔧 Testing Company Apps Script configuration and connectivity endpoint...")
            
            # Construct the endpoint URL as specified in review request
            endpoint = f"{BACKEND_URL}/companies/{self.company_id}/gdrive/test-apps-script"
            self.log(f"   GET {endpoint}")
            self.log(f"   Company ID: {self.company_id}")
            
            # Make the GET request (endpoint is GET, not POST)
            response = requests.get(endpoint, headers=self.get_headers(), timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.apps_script_tests['test_apps_script_endpoint_accessible'] = True
                self.log("✅ Company Apps Script test endpoint accessible")
                
                try:
                    response_data = response.json()
                    self.log(f"   Response data keys: {list(response_data.keys())}")
                    
                    # Check for Apps Script URL configuration (nested in configuration object)
                    config_data = response_data.get('configuration', {})
                    if config_data.get('apps_script_url') or response_data.get('apps_script_url'):
                        self.apps_script_tests['apps_script_url_configuration_returned'] = True
                        apps_script_url = config_data.get('apps_script_url') or response_data.get('apps_script_url')
                        self.log(f"   ✅ Apps Script URL configuration returned: {apps_script_url}")
                        
                        # Check if it matches expected URL
                        if apps_script_url == self.expected_apps_script_url:
                            self.log("   ✅ Apps Script URL matches expected URL")
                        else:
                            self.log(f"   ⚠️ Apps Script URL differs from expected: {self.expected_apps_script_url}")
                    else:
                        self.log("   ❌ Apps Script URL configuration not found in response")
                    
                    # Check for folder ID configuration (nested in configuration object)
                    if config_data.get('folder_id') or response_data.get('folder_id'):
                        self.apps_script_tests['folder_id_configuration_returned'] = True
                        folder_id = config_data.get('folder_id') or response_data.get('folder_id')
                        self.log(f"   ✅ Folder ID configuration returned: {folder_id}")
                    else:
                        self.log("   ❌ Folder ID configuration not found in response")
                    
                    # Check for configuration completeness (based on has_apps_script_url and has_folder_id)
                    has_apps_script = config_data.get('has_apps_script_url', False)
                    has_folder_id = config_data.get('has_folder_id', False)
                    if has_apps_script is not None and has_folder_id is not None:
                        self.apps_script_tests['configuration_completeness_checked'] = True
                        is_complete = has_apps_script and has_folder_id
                        self.log(f"   ✅ Configuration completeness checked: Apps Script URL={has_apps_script}, Folder ID={has_folder_id}")
                        
                        if is_complete:
                            self.apps_script_tests['configuration_complete_for_uploads'] = True
                            self.log("   ✅ Configuration is complete for file uploads")
                        else:
                            self.apps_script_tests['missing_configuration_identified'] = True
                            self.log("   ⚠️ Configuration is incomplete - missing components identified")
                    
                    # Check for connectivity testing results (apps_script_test object)
                    apps_script_test = response_data.get('apps_script_test', {})
                    if apps_script_test:
                        self.apps_script_tests['apps_script_url_connectivity_tested'] = True
                        connectivity_success = apps_script_test.get('success', False)
                        self.log(f"   ✅ Apps Script connectivity tested: {connectivity_success}")
                        
                        if connectivity_success:
                            self.apps_script_tests['apps_script_url_accessible'] = True
                            self.log("   ✅ Apps Script URL is accessible")
                        else:
                            self.log("   ❌ Apps Script URL is not accessible")
                        
                        # Check for Apps Script response validation
                        parsed_response = apps_script_test.get('parsed_response')
                        if parsed_response:
                            self.apps_script_tests['apps_script_response_valid'] = True
                            self.log(f"   ✅ Apps Script response received and parsed")
                            
                            # Check for service identification
                            if 'service' in parsed_response:
                                self.apps_script_tests['apps_script_service_identified'] = True
                                service_info = parsed_response.get('service')
                                version_info = parsed_response.get('version', '')
                                self.log(f"   ✅ Apps Script service identified: {service_info} {version_info}")
                    
                    # Check for debugging information
                    debug_fields = ['debug_info', 'debugging_info', 'error_details', 'troubleshooting']
                    debug_found = False
                    for field in debug_fields:
                        if field in response_data:
                            debug_found = True
                            self.apps_script_tests['debugging_information_provided'] = True
                            self.apps_script_tests['detailed_debugging_info_returned'] = True
                            debug_info = response_data.get(field)
                            self.log(f"   ✅ Debugging information provided in '{field}': {debug_info}")
                            break
                    
                    if not debug_found:
                        self.log("   ⚠️ No specific debugging information field found")
                    
                    # Check for error messages and troubleshooting guidance
                    if 'error' in response_data or 'errors' in response_data:
                        self.apps_script_tests['error_messages_helpful'] = True
                        error_info = response_data.get('error') or response_data.get('errors')
                        self.log(f"   ✅ Error information provided: {error_info}")
                    
                    if 'troubleshooting' in response_data or 'recommendations' in response_data:
                        self.apps_script_tests['troubleshooting_guidance_provided'] = True
                        guidance = response_data.get('troubleshooting') or response_data.get('recommendations')
                        self.log(f"   ✅ Troubleshooting guidance provided: {guidance}")
                    
                    # Analyze for file upload failure cause
                    if ('error' in response_data or 'errors' in response_data or 
                        'configuration_complete' in response_data and not response_data.get('configuration_complete')):
                        self.apps_script_tests['file_upload_failure_cause_identified'] = True
                        self.log("   ✅ File upload failure cause identified")
                    
                    # Print full response for analysis
                    self.log("   📋 Full response data:")
                    self.log(f"   {json.dumps(response_data, indent=4)}")
                    
                    return response_data
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return None
                    
            elif response.status_code == 404:
                self.log("   ❌ Endpoint not found - may not be implemented yet")
                return None
            elif response.status_code == 401:
                self.log("   ❌ Authentication failed - check credentials")
                return None
            elif response.status_code == 403:
                self.log("   ❌ Access forbidden - check user permissions")
                return None
            else:
                self.log(f"   ❌ Company Apps Script test endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing Company Apps Script endpoint: {str(e)}", "ERROR")
            traceback.print_exc()
            return None
    
    def test_direct_apps_script_connectivity(self):
        """Test direct connectivity to the Apps Script URL"""
        try:
            self.log("🌐 Testing direct connectivity to Apps Script URL...")
            self.log(f"   URL: {self.expected_apps_script_url}")
            
            # Test direct GET request to Apps Script
            response = requests.get(self.expected_apps_script_url, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.log("✅ Apps Script URL is directly accessible")
                
                try:
                    # Try to parse as JSON
                    response_data = response.json()
                    self.log(f"   ✅ Apps Script returned valid JSON: {response_data}")
                    
                    # Check for service identification
                    if 'service' in response_data or 'version' in response_data:
                        service_info = response_data.get('service', 'Unknown') + ' ' + response_data.get('version', '')
                        self.log(f"   ✅ Apps Script service: {service_info}")
                    
                    return True
                    
                except json.JSONDecodeError:
                    # Apps Script might return HTML or plain text
                    response_text = response.text[:200]
                    self.log(f"   ✅ Apps Script returned text response: {response_text}")
                    return True
                    
            else:
                self.log(f"   ❌ Apps Script URL not accessible: {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing direct Apps Script connectivity: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_apps_script_test(self):
        """Run comprehensive test of Company Apps Script configuration and connectivity"""
        try:
            self.log("🚀 STARTING COMPANY APPS SCRIPT CONFIGURATION AND CONNECTIVITY TEST")
            self.log("=" * 80)
            self.log(f"Target Company ID: {self.company_id}")
            self.log(f"Expected Apps Script URL: {self.expected_apps_script_url}")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Test Company Apps Script configuration endpoint
            self.log("\nSTEP 2: Testing Company Apps Script configuration endpoint")
            config_result = self.test_company_apps_script_endpoint()
            
            # Step 3: Test direct Apps Script connectivity
            self.log("\nSTEP 3: Testing direct Apps Script connectivity")
            direct_connectivity = self.test_direct_apps_script_connectivity()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPANY APPS SCRIPT TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 COMPANY APPS SCRIPT CONFIGURATION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.apps_script_tests)
            passed_tests = sum(1 for result in self.apps_script_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_verified', 'User company verified'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.apps_script_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Configuration Endpoint Results
            self.log("\n🔧 COMPANY APPS SCRIPT CONFIGURATION ENDPOINT:")
            config_tests = [
                ('test_apps_script_endpoint_accessible', 'Endpoint accessible'),
                ('apps_script_url_configuration_returned', 'Apps Script URL configuration returned'),
                ('folder_id_configuration_returned', 'Folder ID configuration returned'),
                ('configuration_completeness_checked', 'Configuration completeness checked'),
                ('debugging_information_provided', 'Debugging information provided'),
            ]
            
            for test_key, description in config_tests:
                status = "✅ PASS" if self.apps_script_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Connectivity Testing Results
            self.log("\n🌐 APPS SCRIPT CONNECTIVITY TESTING:")
            connectivity_tests = [
                ('apps_script_url_connectivity_tested', 'Apps Script connectivity tested'),
                ('apps_script_url_accessible', 'Apps Script URL accessible'),
                ('apps_script_response_valid', 'Apps Script response valid'),
                ('apps_script_service_identified', 'Apps Script service identified'),
            ]
            
            for test_key, description in connectivity_tests:
                status = "✅ PASS" if self.apps_script_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Configuration Analysis Results
            self.log("\n📋 CONFIGURATION ANALYSIS:")
            analysis_tests = [
                ('configuration_complete_for_uploads', 'Configuration complete for uploads'),
                ('missing_configuration_identified', 'Missing configuration identified'),
                ('file_upload_failure_cause_identified', 'File upload failure cause identified'),
            ]
            
            for test_key, description in analysis_tests:
                status = "✅ PASS" if self.apps_script_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Debugging Information Results
            self.log("\n🔍 DEBUGGING INFORMATION:")
            debug_tests = [
                ('detailed_debugging_info_returned', 'Detailed debugging info returned'),
                ('error_messages_helpful', 'Error messages helpful'),
                ('troubleshooting_guidance_provided', 'Troubleshooting guidance provided'),
            ]
            
            for test_key, description in debug_tests:
                status = "✅ PASS" if self.apps_script_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            # Check critical functionality
            critical_tests = [
                'test_apps_script_endpoint_accessible',
                'apps_script_url_configuration_returned',
                'apps_script_url_connectivity_tested'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.apps_script_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ COMPANY APPS SCRIPT ENDPOINT IS WORKING")
                self.log("   ✅ Configuration and connectivity testing functional")
            else:
                self.log("   ❌ COMPANY APPS SCRIPT ENDPOINT HAS ISSUES")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Check if file upload failure cause was identified
            if self.apps_script_tests.get('file_upload_failure_cause_identified', False):
                self.log("   ✅ FILE UPLOAD FAILURE CAUSE IDENTIFIED")
                self.log("   ✅ Debugging information should help resolve the issue")
            else:
                self.log("   ❌ FILE UPLOAD FAILURE CAUSE NOT CLEARLY IDENTIFIED")
                self.log("   ❌ May need additional investigation")
            
            if success_rate >= 80:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            # Specific findings for "Add Crew From Passport" issue
            self.log("\n🔍 ADD CREW FROM PASSPORT ISSUE ANALYSIS:")
            if self.apps_script_tests.get('configuration_complete_for_uploads', False):
                self.log("   ✅ Configuration appears complete - issue may be elsewhere")
            elif self.apps_script_tests.get('missing_configuration_identified', False):
                self.log("   ❌ MISSING CONFIGURATION IDENTIFIED - This is likely the cause")
            elif not self.apps_script_tests.get('apps_script_url_accessible', False):
                self.log("   ❌ APPS SCRIPT NOT ACCESSIBLE - This could be the cause")
            else:
                self.log("   ⚠️ Issue cause unclear - need more investigation")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the Company Apps Script tests"""
    tester = CompanyAppsScriptTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_apps_script_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Return appropriate exit code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Google Drive Ship Deletion Debug Testing
FOCUS: Debug why Google Drive folder deletion is not working when deleting ships

REVIEW REQUEST REQUIREMENTS:
1. Authentication: Login with admin1/123456 credentials
2. Company Configuration Check: 
   - Get company Google Drive configuration
   - Verify if google_drive_config contains web_app_url/apps_script_url
   - Check if folder_id is properly configured
3. Create Test Ship: Create a test ship for deletion debugging
4. Test Google Drive Deletion Flow:
   - Use DELETE /api/ships/{ship_id}?delete_google_drive_folder=true
   - Monitor backend logs for Google Apps Script calls
   - Check if GoogleDriveManager.delete_ship_structure() is called
   - Verify if request reaches Google Apps Script
5. Apps Script Communication Test:
   - Test if the Google Apps Script URL is reachable
   - Check payload format sent to Apps Script
   - Verify response from Google Apps Script

KEY DEBUG POINTS:
- Is the delete_google_drive_folder parameter being processed?
- Does company have proper Google Drive configuration?
- Is GoogleDriveManager being called with correct parameters?
- Is the Google Apps Script URL configured and working?
- What response is received from Google Apps Script?
- Are there any timeout or connection issues?

EXPECTED INVESTIGATION:
- Identify why Google Apps Script delete_complete_ship_structure is not being triggered
- Find the exact point of failure in the deletion chain
- Provide specific steps to fix the Google Drive integration
- Confirm if Google Apps Script needs to be redeployed with latest version
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nautical-crew-hub.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class GoogleDriveShipDeletionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Google Drive ship deletion debugging
        self.deletion_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'admin_role_verified': False,
            
            # Company Google Drive Configuration
            'company_gdrive_config_exists': False,
            'web_app_url_configured': False,
            'apps_script_url_configured': False,
            'folder_id_configured': False,
            'gdrive_config_complete': False,
            
            # Test Ship Creation
            'test_ship_created': False,
            'test_ship_id_obtained': False,
            
            # Ship Deletion Flow Testing
            'delete_endpoint_accessible': False,
            'delete_parameter_processed': False,
            'database_deletion_successful': False,
            'gdrive_deletion_requested': False,
            'gdrive_manager_called': False,
            
            # Google Apps Script Communication
            'apps_script_url_reachable': False,
            'payload_format_correct': False,
            'apps_script_response_received': False,
            'delete_complete_ship_structure_called': False,
            
            # Error Analysis
            'timeout_issues_detected': False,
            'connection_issues_detected': False,
            'configuration_issues_detected': False,
            'apps_script_deployment_issues': False,
        }
        
        # Store test data for analysis
        self.user_company = None
        self.company_gdrive_config = {}
        self.test_ship_data = {}
        self.deletion_response = {}
        self.apps_script_logs = []
        
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
        """Authenticate with admin1/123456 credentials as specified in review request"""
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
                
                self.deletion_tests['authentication_successful'] = True
                self.user_company = self.current_user.get('company')
                
                if self.user_company:
                    self.deletion_tests['user_company_identified'] = True
                
                # Verify admin role
                user_role = self.current_user.get('role', '').upper()
                if 'ADMIN' in user_role:
                    self.deletion_tests['admin_role_verified'] = True
                    self.log("✅ Admin role verified")
                else:
                    self.log(f"⚠️ User role is {user_role}, not ADMIN")
                
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
    
    def check_company_gdrive_configuration(self):
        """Check company Google Drive configuration"""
        try:
            self.log("🏢 Checking company Google Drive configuration...")
            
            if not self.user_company:
                self.log("❌ User company not identified")
                return False
            
            # Get company information
            endpoint = f"{BACKEND_URL}/companies"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                companies = response.json()
                user_company_data = None
                
                for company in companies:
                    if company.get('name_en') == self.user_company or company.get('name_vn') == self.user_company:
                        user_company_data = company
                        break
                
                if not user_company_data:
                    self.log(f"❌ Company {self.user_company} not found in companies list")
                    return False
                
                self.log(f"✅ Found company: {user_company_data.get('name_en', user_company_data.get('name_vn'))}")
                
                # Check for Google Drive configuration
                gdrive_config = user_company_data.get('google_drive_config', {})
                self.company_gdrive_config = gdrive_config
                
                if gdrive_config:
                    self.deletion_tests['company_gdrive_config_exists'] = True
                    self.log("✅ Google Drive configuration found")
                    
                    # Check specific configuration fields
                    web_app_url = gdrive_config.get('web_app_url')
                    apps_script_url = gdrive_config.get('apps_script_url')
                    folder_id = gdrive_config.get('folder_id')
                    
                    self.log(f"   Web App URL: {web_app_url}")
                    self.log(f"   Apps Script URL: {apps_script_url}")
                    self.log(f"   Folder ID: {folder_id}")
                    
                    if web_app_url:
                        self.deletion_tests['web_app_url_configured'] = True
                        self.log("   ✅ Web App URL configured")
                    else:
                        self.log("   ❌ Web App URL not configured")
                    
                    if apps_script_url:
                        self.deletion_tests['apps_script_url_configured'] = True
                        self.log("   ✅ Apps Script URL configured")
                    else:
                        self.log("   ❌ Apps Script URL not configured")
                    
                    if folder_id:
                        self.deletion_tests['folder_id_configured'] = True
                        self.log("   ✅ Folder ID configured")
                    else:
                        self.log("   ❌ Folder ID not configured")
                    
                    # Check if configuration is complete
                    if web_app_url and folder_id:
                        self.deletion_tests['gdrive_config_complete'] = True
                        self.log("✅ Google Drive configuration appears complete")
                        return True
                    else:
                        self.deletion_tests['configuration_issues_detected'] = True
                        self.log("❌ Google Drive configuration incomplete")
                        return False
                else:
                    self.log("❌ No Google Drive configuration found for company")
                    self.deletion_tests['configuration_issues_detected'] = True
                    return False
            else:
                self.log(f"❌ Failed to get companies: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking company Google Drive configuration: {str(e)}", "ERROR")
            return False
    
    def create_test_ship(self):
        """Create a test ship for deletion debugging"""
        try:
            self.log("🚢 Creating test ship for deletion debugging...")
            
            # Generate unique test ship name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_ship_name = f"TEST_DELETION_SHIP_{timestamp}"
            
            ship_data = {
                "name": test_ship_name,
                "imo": f"TEST{timestamp[-6:]}",
                "flag": "PANAMA",
                "ship_type": "BULK CARRIER",
                "gross_tonnage": 25000.0,
                "deadweight": 40000.0,
                "built_year": 2020,
                "company": self.user_company
            }
            
            self.log(f"   Creating ship: {test_ship_name}")
            self.log(f"   Company: {self.user_company}")
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.post(endpoint, json=ship_data, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                ship_response = response.json()
                self.test_ship_data = ship_response
                
                ship_id = ship_response.get('id')
                ship_name = ship_response.get('name')
                
                self.log("✅ Test ship created successfully")
                self.log(f"   Ship ID: {ship_id}")
                self.log(f"   Ship Name: {ship_name}")
                
                self.deletion_tests['test_ship_created'] = True
                if ship_id:
                    self.deletion_tests['test_ship_id_obtained'] = True
                
                return True
            else:
                self.log(f"❌ Failed to create test ship: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating test ship: {str(e)}", "ERROR")
            return False
    
    def test_database_only_deletion(self):
        """Test database-only deletion (without Google Drive parameter)"""
        try:
            self.log("🗄️ Testing database-only deletion...")
            
            if not self.test_ship_data or not self.test_ship_data.get('id'):
                self.log("❌ No test ship available for deletion")
                return False
            
            ship_id = self.test_ship_data.get('id')
            ship_name = self.test_ship_data.get('name')
            
            self.log(f"   Deleting ship: {ship_name} (ID: {ship_id})")
            self.log("   WITHOUT delete_google_drive_folder parameter")
            
            endpoint = f"{BACKEND_URL}/ships/{ship_id}"
            self.log(f"   DELETE {endpoint}")
            
            response = requests.delete(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                self.log("✅ Database-only deletion successful")
                self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                
                # Check response structure
                database_deletion = response_data.get('database_deletion')
                gdrive_deletion_requested = response_data.get('google_drive_deletion_requested')
                
                if database_deletion == 'success':
                    self.log("   ✅ Database deletion confirmed successful")
                
                if gdrive_deletion_requested == False:
                    self.log("   ✅ Google Drive deletion correctly NOT requested")
                else:
                    self.log(f"   ⚠️ Google Drive deletion requested: {gdrive_deletion_requested}")
                
                return True
            else:
                self.log(f"❌ Database-only deletion failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing database-only deletion: {str(e)}", "ERROR")
            return False
    
    def test_gdrive_deletion_flow(self):
        """Test Google Drive deletion flow with delete_google_drive_folder=true"""
        try:
            self.log("🗂️ Testing Google Drive deletion flow...")
            
            # First, create a new test ship for this test
            if not self.create_test_ship():
                self.log("❌ Failed to create test ship for Google Drive deletion test")
                return False
            
            ship_id = self.test_ship_data.get('id')
            ship_name = self.test_ship_data.get('name')
            
            self.log(f"   Deleting ship: {ship_name} (ID: {ship_id})")
            self.log("   WITH delete_google_drive_folder=true parameter")
            
            endpoint = f"{BACKEND_URL}/ships/{ship_id}?delete_google_drive_folder=true"
            self.log(f"   DELETE {endpoint}")
            
            # Monitor the request timing
            start_time = time.time()
            response = requests.delete(endpoint, headers=self.get_headers(), timeout=60)
            end_time = time.time()
            request_duration = end_time - start_time
            
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Request duration: {request_duration:.2f} seconds")
            
            if response.status_code == 200:
                response_data = response.json()
                self.deletion_response = response_data
                
                self.log("✅ Google Drive deletion request successful")
                self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                
                # Analyze response structure
                database_deletion = response_data.get('database_deletion')
                gdrive_deletion_requested = response_data.get('google_drive_deletion_requested')
                gdrive_deletion_status = response_data.get('google_drive_deletion_status')
                gdrive_deletion_message = response_data.get('google_drive_deletion_message')
                
                self.deletion_tests['delete_endpoint_accessible'] = True
                
                if gdrive_deletion_requested == True:
                    self.deletion_tests['delete_parameter_processed'] = True
                    self.deletion_tests['gdrive_deletion_requested'] = True
                    self.log("   ✅ delete_google_drive_folder parameter processed correctly")
                else:
                    self.log(f"   ❌ delete_google_drive_folder parameter not processed: {gdrive_deletion_requested}")
                
                if database_deletion == 'success':
                    self.deletion_tests['database_deletion_successful'] = True
                    self.log("   ✅ Database deletion successful")
                else:
                    self.log(f"   ❌ Database deletion failed: {database_deletion}")
                
                # Check Google Drive deletion status
                if gdrive_deletion_status:
                    self.log(f"   Google Drive deletion status: {gdrive_deletion_status}")
                    
                    if gdrive_deletion_status == 'success':
                        self.deletion_tests['gdrive_manager_called'] = True
                        self.log("   ✅ GoogleDriveManager appears to have been called successfully")
                    elif gdrive_deletion_status == 'error':
                        self.log("   ❌ GoogleDriveManager reported an error")
                        if gdrive_deletion_message:
                            self.log(f"      Error message: {gdrive_deletion_message}")
                            
                            # Analyze error message for specific issues
                            if 'timeout' in gdrive_deletion_message.lower():
                                self.deletion_tests['timeout_issues_detected'] = True
                            elif 'connection' in gdrive_deletion_message.lower():
                                self.deletion_tests['connection_issues_detected'] = True
                            elif 'configuration' in gdrive_deletion_message.lower():
                                self.deletion_tests['configuration_issues_detected'] = True
                    elif gdrive_deletion_status == 'config_missing':
                        self.deletion_tests['configuration_issues_detected'] = True
                        self.log("   ❌ Google Drive configuration missing")
                else:
                    self.log("   ⚠️ No Google Drive deletion status in response")
                
                return True
            else:
                self.log(f"❌ Google Drive deletion request failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Google Drive deletion flow: {str(e)}", "ERROR")
            return False
    
    def test_apps_script_communication(self):
        """Test Google Apps Script communication"""
        try:
            self.log("📡 Testing Google Apps Script communication...")
            
            if not self.company_gdrive_config:
                self.log("❌ No Google Drive configuration available for Apps Script testing")
                return False
            
            # Get Apps Script URL
            apps_script_url = self.company_gdrive_config.get('web_app_url') or self.company_gdrive_config.get('apps_script_url')
            
            if not apps_script_url:
                self.log("❌ No Apps Script URL configured")
                return False
            
            self.log(f"   Apps Script URL: {apps_script_url}")
            
            # Test if Apps Script URL is reachable
            try:
                self.log("   Testing Apps Script URL reachability...")
                
                # Create test payload similar to what GoogleDriveManager would send
                test_payload = {
                    'action': 'delete_complete_ship_structure',
                    'parent_folder_id': self.company_gdrive_config.get('folder_id', 'test_folder_id'),
                    'ship_name': 'TEST_SHIP_FOR_DELETION_DEBUG',
                    'permanent_delete': False
                }
                
                self.log(f"   Test payload: {json.dumps(test_payload, indent=2)}")
                
                # Test the Apps Script endpoint
                start_time = time.time()
                response = requests.post(
                    apps_script_url,
                    json=test_payload,
                    timeout=30,
                    headers={'Content-Type': 'application/json'}
                )
                end_time = time.time()
                request_duration = end_time - start_time
                
                self.log(f"   Apps Script response status: {response.status_code}")
                self.log(f"   Apps Script request duration: {request_duration:.2f} seconds")
                
                if response.status_code == 200:
                    self.deletion_tests['apps_script_url_reachable'] = True
                    self.deletion_tests['payload_format_correct'] = True
                    self.deletion_tests['apps_script_response_received'] = True
                    
                    try:
                        response_data = response.json()
                        self.log("✅ Apps Script responded successfully")
                        self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                        
                        # Check if the response indicates the delete_complete_ship_structure function was called
                        if 'delete_complete_ship_structure' in str(response_data).lower():
                            self.deletion_tests['delete_complete_ship_structure_called'] = True
                            self.log("   ✅ delete_complete_ship_structure function appears to be working")
                        
                    except json.JSONDecodeError:
                        self.log(f"   ⚠️ Apps Script response not JSON: {response.text[:200]}")
                        
                elif response.status_code == 404:
                    self.log("   ❌ Apps Script URL not found (404)")
                    self.deletion_tests['apps_script_deployment_issues'] = True
                elif response.status_code == 403:
                    self.log("   ❌ Apps Script access forbidden (403)")
                    self.deletion_tests['apps_script_deployment_issues'] = True
                else:
                    self.log(f"   ❌ Apps Script returned error: {response.status_code}")
                    self.log(f"      Response: {response.text[:200]}")
                    
                    if response.status_code >= 500:
                        self.deletion_tests['apps_script_deployment_issues'] = True
                
            except requests.exceptions.Timeout:
                self.log("   ❌ Apps Script request timed out")
                self.deletion_tests['timeout_issues_detected'] = True
            except requests.exceptions.ConnectionError:
                self.log("   ❌ Apps Script connection error")
                self.deletion_tests['connection_issues_detected'] = True
            except Exception as e:
                self.log(f"   ❌ Apps Script communication error: {str(e)}")
                
            return True
                
        except Exception as e:
            self.log(f"❌ Error testing Apps Script communication: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs_for_gdrive_calls(self):
        """Check backend logs for Google Drive manager calls"""
        try:
            self.log("📋 Checking backend logs for Google Drive manager calls...")
            
            # Try to get backend logs (this might not be available in all environments)
            try:
                # Check supervisor logs for backend
                import subprocess
                result = subprocess.run(
                    ['tail', '-n', '100', '/var/log/supervisor/backend.err.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    log_content = result.stdout
                    self.log("✅ Backend logs retrieved")
                    
                    # Look for Google Drive related log entries
                    gdrive_keywords = [
                        'GoogleDriveManager',
                        'delete_ship_structure',
                        'delete_complete_ship_structure',
                        'google_drive_config',
                        'Apps Script',
                        'web_app_url'
                    ]
                    
                    found_keywords = []
                    for keyword in gdrive_keywords:
                        if keyword in log_content:
                            found_keywords.append(keyword)
                    
                    if found_keywords:
                        self.log(f"   ✅ Found Google Drive related log entries: {found_keywords}")
                        
                        # Extract relevant log lines
                        log_lines = log_content.split('\n')
                        relevant_lines = []
                        
                        for line in log_lines:
                            if any(keyword in line for keyword in gdrive_keywords):
                                relevant_lines.append(line)
                        
                        if relevant_lines:
                            self.log("   Recent Google Drive related log entries:")
                            for line in relevant_lines[-10:]:  # Show last 10 relevant lines
                                self.log(f"      {line}")
                    else:
                        self.log("   ⚠️ No Google Drive related log entries found")
                else:
                    self.log("   ⚠️ Could not retrieve backend logs")
                    
            except Exception as e:
                self.log(f"   ⚠️ Error retrieving backend logs: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_gdrive_deletion_test(self):
        """Run comprehensive Google Drive ship deletion debugging test"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE GOOGLE DRIVE SHIP DELETION DEBUG TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Check company Google Drive configuration
            self.log("\nSTEP 2: Company Google Drive Configuration Check")
            if not self.check_company_gdrive_configuration():
                self.log("❌ CRITICAL: Google Drive configuration check failed")
                # Continue anyway to see what happens
            
            # Step 3: Test database-only deletion first
            self.log("\nSTEP 3: Database-Only Deletion Test")
            if not self.test_database_only_deletion():
                self.log("❌ Database-only deletion test failed")
                # Continue anyway
            
            # Step 4: Test Google Drive deletion flow
            self.log("\nSTEP 4: Google Drive Deletion Flow Test")
            if not self.test_gdrive_deletion_flow():
                self.log("❌ Google Drive deletion flow test failed")
                # Continue anyway
            
            # Step 5: Test Apps Script communication
            self.log("\nSTEP 5: Apps Script Communication Test")
            if not self.test_apps_script_communication():
                self.log("❌ Apps Script communication test failed")
                # Continue anyway
            
            # Step 6: Check backend logs
            self.log("\nSTEP 6: Backend Logs Analysis")
            self.check_backend_logs_for_gdrive_calls()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE GOOGLE DRIVE DELETION DEBUG TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_debug_summary(self):
        """Print comprehensive summary of Google Drive deletion debug results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 GOOGLE DRIVE SHIP DELETION DEBUG SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.deletion_tests)
            passed_tests = sum(1 for result in self.deletion_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION:")
            auth_tests = [
                ('authentication_successful', 'Login with admin1/123456 successful'),
                ('user_company_identified', 'User company identified'),
                ('admin_role_verified', 'Admin role verified'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.deletion_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Google Drive Configuration Results
            self.log("\n🏢 GOOGLE DRIVE CONFIGURATION:")
            config_tests = [
                ('company_gdrive_config_exists', 'Company Google Drive config exists'),
                ('web_app_url_configured', 'Web App URL configured'),
                ('apps_script_url_configured', 'Apps Script URL configured'),
                ('folder_id_configured', 'Folder ID configured'),
                ('gdrive_config_complete', 'Google Drive configuration complete'),
            ]
            
            for test_key, description in config_tests:
                status = "✅ PASS" if self.deletion_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Ship Deletion Flow Results
            self.log("\n🗂️ SHIP DELETION FLOW:")
            deletion_tests = [
                ('test_ship_created', 'Test ship created successfully'),
                ('delete_endpoint_accessible', 'DELETE endpoint accessible'),
                ('delete_parameter_processed', 'delete_google_drive_folder parameter processed'),
                ('database_deletion_successful', 'Database deletion successful'),
                ('gdrive_deletion_requested', 'Google Drive deletion requested'),
                ('gdrive_manager_called', 'GoogleDriveManager called'),
            ]
            
            for test_key, description in deletion_tests:
                status = "✅ PASS" if self.deletion_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Apps Script Communication Results
            self.log("\n📡 APPS SCRIPT COMMUNICATION:")
            apps_script_tests = [
                ('apps_script_url_reachable', 'Apps Script URL reachable'),
                ('payload_format_correct', 'Payload format correct'),
                ('apps_script_response_received', 'Apps Script response received'),
                ('delete_complete_ship_structure_called', 'delete_complete_ship_structure function called'),
            ]
            
            for test_key, description in apps_script_tests:
                status = "✅ PASS" if self.deletion_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Error Analysis
            self.log("\n🚨 ERROR ANALYSIS:")
            error_tests = [
                ('timeout_issues_detected', 'Timeout issues detected'),
                ('connection_issues_detected', 'Connection issues detected'),
                ('configuration_issues_detected', 'Configuration issues detected'),
                ('apps_script_deployment_issues', 'Apps Script deployment issues detected'),
            ]
            
            for test_key, description in error_tests:
                status = "⚠️ DETECTED" if self.deletion_tests.get(test_key, False) else "✅ NONE"
                self.log(f"   {status} - {description}")
            
            # Root Cause Analysis
            self.log("\n🔍 ROOT CAUSE ANALYSIS:")
            
            if not self.deletion_tests.get('gdrive_config_complete', False):
                self.log("   ❌ CRITICAL: Google Drive configuration is incomplete")
                self.log("      - Check if web_app_url and folder_id are properly configured")
                self.log("      - Verify company Google Drive settings")
            
            if not self.deletion_tests.get('apps_script_url_reachable', False):
                self.log("   ❌ CRITICAL: Apps Script URL is not reachable")
                self.log("      - Verify Apps Script deployment")
                self.log("      - Check if Apps Script URL is correct")
                self.log("      - Ensure Apps Script has proper permissions")
            
            if not self.deletion_tests.get('delete_complete_ship_structure_called', False):
                self.log("   ❌ CRITICAL: delete_complete_ship_structure function not working")
                self.log("      - Apps Script may need to be redeployed with latest version")
                self.log("      - Check Apps Script function implementation")
            
            if self.deletion_tests.get('timeout_issues_detected', False):
                self.log("   ⚠️ WARNING: Timeout issues detected")
                self.log("      - Apps Script may be taking too long to respond")
                self.log("      - Consider increasing timeout values")
            
            # Recommendations
            self.log("\n💡 RECOMMENDATIONS:")
            
            if not self.deletion_tests.get('gdrive_config_complete', False):
                self.log("   1. Fix Google Drive configuration:")
                self.log("      - Ensure web_app_url is properly set")
                self.log("      - Ensure folder_id is properly set")
                self.log("      - Update company settings with correct Google Drive config")
            
            if not self.deletion_tests.get('apps_script_url_reachable', False):
                self.log("   2. Fix Apps Script deployment:")
                self.log("      - Redeploy Google Apps Script with latest version")
                self.log("      - Verify Apps Script permissions and sharing settings")
                self.log("      - Test Apps Script URL manually")
            
            if self.deletion_tests.get('gdrive_manager_called', False) and not self.deletion_tests.get('delete_complete_ship_structure_called', False):
                self.log("   3. Update Apps Script function:")
                self.log("      - Ensure delete_complete_ship_structure function exists")
                self.log("      - Verify function parameters and implementation")
                self.log("      - Test function with sample data")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing debug summary: {str(e)}", "ERROR")

def main():
    """Main function to run the Google Drive ship deletion debug test"""
    tester = GoogleDriveShipDeletionTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_gdrive_deletion_test()
        
        # Print detailed summary
        tester.print_debug_summary()
        
        if success:
            print("\n🎉 Google Drive ship deletion debug test completed successfully!")
            return 0
        else:
            print("\n❌ Google Drive ship deletion debug test completed with issues!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
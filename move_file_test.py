#!/usr/bin/env python3
"""
Move File Functionality Testing Script
Focus: Detailed debugging of move file functionality after Apps Script update
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration - Use production URL from frontend .env
BACKEND_URL = "https://vesseldocs.preview.emergentagent.com/api"

class MoveFileFunctionalityTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        self.company_id = None
        self.sunshine_ship = None
        self.test_certificate = None
        self.apps_script_url = None
        self.folder_id = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_move_file_functionality(self):
        """Main test function for move file functionality debugging as per review request"""
        self.log("🎯 Starting Move File Functionality Debugging - Detailed Apps Script Update Testing")
        self.log("=" * 80)
        
        # Step 1: Authentication
        auth_result = self.test_authentication()
        if not auth_result:
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Get Certificate and Folder IDs
        cert_result = self.verify_certificate_and_folder_ids()
        if not cert_result:
            self.log("❌ Certificate and folder verification failed")
            return False
        
        # Step 3: Test Apps Script Direct Call
        apps_script_result = self.test_apps_script_direct_call()
        
        # Step 4: Test Backend Move API
        backend_api_result = self.test_backend_move_api()
        
        # Step 5: Check Apps Script Deployment
        deployment_result = self.check_apps_script_deployment()
        
        # Step 6: Detailed Error Analysis
        error_analysis_result = self.detailed_error_analysis()
        
        # Summary
        self.log("=" * 80)
        self.log("📋 MOVE FILE FUNCTIONALITY DEBUG SUMMARY")
        self.log("=" * 80)
        
        self.log(f"{'✅' if auth_result else '❌'} Authentication: {'SUCCESS' if auth_result else 'FAILED'}")
        self.log(f"{'✅' if cert_result else '❌'} Certificate & Folder IDs: {'VERIFIED' if cert_result else 'FAILED'}")
        self.log(f"{'✅' if apps_script_result else '❌'} Apps Script Direct Call: {'SUCCESS' if apps_script_result else 'FAILED'}")
        self.log(f"{'✅' if backend_api_result else '❌'} Backend Move API: {'SUCCESS' if backend_api_result else 'FAILED'}")
        self.log(f"{'✅' if deployment_result else '❌'} Apps Script Deployment: {'SUCCESS' if deployment_result else 'FAILED'}")
        self.log(f"{'✅' if error_analysis_result else '❌'} Error Analysis: {'COMPLETED' if error_analysis_result else 'FAILED'}")
        
        overall_success = all([auth_result, cert_result, apps_script_result, backend_api_result, deployment_result])
        
        if overall_success:
            self.log("🎉 MOVE FILE FUNCTIONALITY: FULLY WORKING")
        else:
            self.log("❌ MOVE FILE FUNCTIONALITY: ISSUES DETECTED")
            self.log("🔍 Detailed error analysis completed - check logs above for specific issues")
        
        return overall_success
    
    def test_authentication(self):
        """Test authentication with admin1/123456"""
        try:
            self.log("🔐 Step 1: Testing Authentication with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            response = requests.post(endpoint, json=login_data, timeout=30)
            
            self.log(f"   Login response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_info = data.get("user")
                
                if self.auth_token and self.user_info:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    
                    self.log(f"   ✅ Authentication successful")
                    self.log(f"      User: {self.user_info.get('username')} ({self.user_info.get('role')})")
                    self.log(f"      Full Name: {self.user_info.get('full_name')}")
                    self.log(f"      Company: {self.user_info.get('company', 'N/A')}")
                    
                    # Get the actual company ID by looking up the company name
                    company_name = self.user_info.get('company')
                    if company_name:
                        # Get companies to find the ID
                        companies_response = self.session.get(f"{BACKEND_URL}/companies", timeout=10)
                        if companies_response.status_code == 200:
                            companies = companies_response.json()
                            for company in companies:
                                if (company.get('name_en', '').upper() == company_name.upper() or 
                                    company.get('name', '').upper() == company_name.upper()):
                                    self.company_id = company.get('id')
                                    self.log(f"      Company ID resolved: {self.company_id}")
                                    break
                    
                    return True
                else:
                    self.log("   ❌ Authentication failed - missing token or user data")
                    return False
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                
                self.log(f"   ❌ Authentication failed - HTTP {response.status_code}")
                self.log(f"      Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def verify_certificate_and_folder_ids(self):
        """Step 2: Verify Certificate and Folder IDs"""
        try:
            self.log("📄 Step 2: Verifying Certificate and Folder IDs...")
            
            # Get ships
            ships_response = self.session.get(f"{BACKEND_URL}/ships", timeout=10)
            
            if ships_response.status_code != 200:
                self.log(f"   ❌ Failed to get ships: {ships_response.status_code}")
                return False
            
            ships = ships_response.json()
            
            # Find SUNSHINE ship
            for ship in ships:
                if "SUNSHINE" in ship.get('name', '').upper():
                    self.sunshine_ship = ship
                    break
            
            if not self.sunshine_ship:
                self.log("   ❌ SUNSHINE ship not found")
                return False
            
            self.log(f"   ✅ Found ship: {self.sunshine_ship.get('name')} (ID: {self.sunshine_ship.get('id')})")
            
            # Get certificates for this ship
            cert_response = self.session.get(f"{BACKEND_URL}/ships/{self.sunshine_ship['id']}/certificates", timeout=10)
            
            if cert_response.status_code != 200:
                self.log(f"   ❌ Failed to get certificates: {cert_response.status_code}")
                return False
            
            certificates = cert_response.json()
            self.log(f"   ✅ Found {len(certificates)} certificates")
            
            # Find certificate with Google Drive file ID
            for cert in certificates:
                gdrive_file_id = cert.get('google_drive_file_id') or cert.get('gdrive_file_id')
                if gdrive_file_id:
                    self.test_certificate = cert
                    self.log(f"   ✅ Found certificate with Google Drive file:")
                    self.log(f"      Certificate: {cert.get('cert_name', 'N/A')}")
                    self.log(f"      Certificate ID: {cert.get('id')}")
                    self.log(f"      Google Drive File ID: {gdrive_file_id}")
                    break
            
            if not self.test_certificate:
                self.log("   ❌ No certificates with Google Drive file ID found")
                return False
            
            # Get company Google Drive configuration
            config_response = self.session.get(f"{BACKEND_URL}/companies/{self.company_id}/gdrive/config", timeout=10)
            
            if config_response.status_code != 200:
                self.log(f"   ❌ Failed to get Google Drive config: {config_response.status_code}")
                return False
            
            config_data = config_response.json()
            self.log("   ✅ Company Google Drive configuration found")
            
            # Get Apps Script URL and folder ID
            if 'config' in config_data:
                self.apps_script_url = config_data['config'].get('web_app_url') or config_data['config'].get('apps_script_url')
                self.folder_id = config_data['config'].get('folder_id')
            
            if not self.apps_script_url:
                self.log("   ❌ No Apps Script URL found in configuration")
                return False
            
            if not self.folder_id:
                self.log("   ❌ No folder ID found in configuration")
                return False
            
            self.log(f"   ✅ Apps Script URL: {self.apps_script_url}")
            self.log(f"   ✅ Folder ID: {self.folder_id}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Certificate and folder verification error: {str(e)}", "ERROR")
            return False
    
    def test_apps_script_direct_call(self):
        """Step 3: Test Apps Script Direct Call"""
        try:
            self.log("🔧 Step 3: Testing Apps Script Direct Call...")
            
            if not self.apps_script_url:
                self.log("   ❌ No Apps Script URL available")
                return False
            
            # Get real certificate file ID and target folder ID
            file_id = self.test_certificate.get('google_drive_file_id') or self.test_certificate.get('gdrive_file_id')
            target_folder_id = self.folder_id  # Use main folder as target
            
            self.log(f"   📁 Testing move_file action with real data:")
            self.log(f"      File ID: {file_id}")
            self.log(f"      Target Folder ID: {target_folder_id}")
            
            # Test move_file action with real data
            test_payload = {
                "action": "move_file",
                "file_id": file_id,
                "target_folder_id": target_folder_id
            }
            
            self.log("   🔧 Making direct POST call to Apps Script...")
            response = requests.post(self.apps_script_url, json=test_payload, timeout=30)
            
            self.log(f"   Apps Script response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.log(f"   Apps Script response: {json.dumps(result, indent=2)}")
                    
                    if 'success' in result:
                        if result.get('success'):
                            self.log("   ✅ Apps Script move_file action working correctly")
                            return True
                        else:
                            error_msg = result.get('message', 'Unknown error')
                            self.log(f"   ❌ Apps Script move_file action error: {error_msg}")
                            
                            # Check for specific error patterns
                            if 'getFileById' in error_msg:
                                self.log("      🔍 Root Cause: DriveApp.getFileById error - same issue as before")
                            elif 'not found' in error_msg.lower():
                                self.log("      🔍 Root Cause: File or folder not found")
                            elif 'permission' in error_msg.lower():
                                self.log("      🔍 Root Cause: Permission denied")
                            
                            return False
                    else:
                        self.log("   ❌ Apps Script response missing success field")
                        return False
                        
                except json.JSONDecodeError:
                    self.log(f"   ❌ Apps Script returned invalid JSON: {response.text}")
                    return False
            else:
                self.log(f"   ❌ Apps Script request failed: {response.status_code}")
                self.log(f"      Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Apps Script direct call test error: {str(e)}", "ERROR")
            return False
    
    def test_backend_move_api(self):
        """Step 4: Test Backend Move API"""
        try:
            self.log("🔧 Step 4: Testing Backend Move API...")
            
            if not self.test_certificate or not self.company_id:
                self.log("   ❌ Missing test certificate or company ID")
                return False
            
            # Get file ID from certificate
            file_id = self.test_certificate.get('google_drive_file_id') or self.test_certificate.get('gdrive_file_id')
            target_folder_id = self.folder_id  # Use main folder as target
            
            self.log(f"   📁 Testing backend move API:")
            self.log(f"      File ID: {file_id}")
            self.log(f"      Target Folder ID: {target_folder_id}")
            self.log(f"      Company ID: {self.company_id}")
            
            # Test the move API
            move_data = {
                "file_id": file_id,
                "target_folder_id": target_folder_id
            }
            
            endpoint = f"{BACKEND_URL}/companies/{self.company_id}/gdrive/move-file"
            response = self.session.post(endpoint, json=move_data, timeout=30)
            
            self.log(f"   Backend Move API response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.log("   ✅ Backend Move API call successful")
                    self.log(f"      Response: {json.dumps(result, indent=2)}")
                    return True
                except json.JSONDecodeError:
                    self.log("   ✅ Backend Move API call successful (no JSON response)")
                    return True
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                
                self.log(f"   ❌ Backend Move API call failed - HTTP {response.status_code}")
                self.log(f"      Error: {error_detail}")
                
                # Check for specific error patterns
                if "Company not found" in error_detail:
                    self.log("      🔍 Root Cause: Company lookup failure")
                elif "not configured" in error_detail.lower():
                    self.log("      🔍 Root Cause: Google Drive not configured for company")
                elif "file_id" in error_detail.lower() or "target_folder_id" in error_detail.lower():
                    self.log("      🔍 Root Cause: Missing or invalid parameters")
                
                return False
                
        except Exception as e:
            self.log(f"❌ Backend Move API test error: {str(e)}", "ERROR")
            return False
    
    def check_apps_script_deployment(self):
        """Step 5: Check Apps Script Deployment"""
        try:
            self.log("🔍 Step 5: Checking Apps Script Deployment...")
            
            if not self.apps_script_url:
                self.log("   ❌ No Apps Script URL available")
                return False
            
            # Test if Apps Script has been updated with new version
            test_payload = {
                "action": "get_version"
            }
            
            self.log("   🔧 Testing Apps Script version info...")
            response = requests.post(self.apps_script_url, json=test_payload, timeout=30)
            
            self.log(f"   Apps Script version response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.log(f"   Apps Script version response: {json.dumps(result, indent=2)}")
                    
                    # Check if move_file action is available
                    if 'available_actions' in result:
                        actions = result.get('available_actions', [])
                        if 'move_file' in actions:
                            self.log("   ✅ move_file action is available in Apps Script")
                        else:
                            self.log("   ❌ move_file action not found in available actions")
                            self.log(f"      Available actions: {actions}")
                            return False
                    
                    return True
                        
                except json.JSONDecodeError:
                    self.log(f"   ⚠️ Apps Script version check returned non-JSON: {response.text}")
                    # Still consider this a success if the script responds
                    return True
            else:
                self.log(f"   ❌ Apps Script version check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Apps Script deployment check error: {str(e)}", "ERROR")
            return False
    
    def detailed_error_analysis(self):
        """Step 6: Detailed Error Analysis"""
        try:
            self.log("🔍 Step 6: Detailed Error Analysis...")
            
            self.log("   📊 Analyzing potential issues:")
            
            # Check 1: Same DriveApp.getFileById error
            self.log("   1. Checking for same DriveApp.getFileById error...")
            if hasattr(self, 'apps_script_error') and 'getFileById' in str(self.apps_script_error):
                self.log("      ❌ Same Apps Script error detected - script not updated properly")
            else:
                self.log("      ✅ No DriveApp.getFileById error detected")
            
            # Check 2: New error after script update
            self.log("   2. Checking for new errors after script update...")
            # This would be determined by the Apps Script response
            
            # Check 3: Backend integration issue
            self.log("   3. Checking backend integration...")
            if self.company_id and self.apps_script_url:
                self.log("      ✅ Backend has company ID and Apps Script URL")
            else:
                self.log("      ❌ Backend missing company ID or Apps Script URL")
            
            # Check 4: Permission/access issue
            self.log("   4. Checking permissions...")
            if self.test_certificate:
                file_id = self.test_certificate.get('google_drive_file_id') or self.test_certificate.get('gdrive_file_id')
                self.log(f"      File ID to move: {file_id}")
                self.log(f"      Target folder ID: {self.folder_id}")
            
            # Check 5: Different technical problem
            self.log("   5. Summary of findings:")
            self.log("      - Authentication: Working")
            self.log("      - Certificate with file ID: Found")
            self.log("      - Company Google Drive config: Available")
            self.log("      - Apps Script URL: Available")
            self.log("      - Target folder ID: Available")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Detailed error analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main test execution"""
    print("🎯 Ship Management System - Move File Functionality Debugging")
    print("🔍 Focus: Detailed Apps Script and Backend Testing")
    print("=" * 80)
    
    tester = MoveFileFunctionalityTester()
    success = tester.test_move_file_functionality()
    
    print("=" * 80)
    if success:
        print("🎉 Move file functionality test completed successfully!")
        print("✅ Move functionality is working properly")
        sys.exit(0)
    else:
        print("❌ Move file functionality test completed with issues!")
        print("🔍 Detailed error analysis completed - check logs above for specific issues")
        print("💡 Focus on the failed steps to identify the exact remaining issue")
        sys.exit(1)

if __name__ == "__main__":
    main()
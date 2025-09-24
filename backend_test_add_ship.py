#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
Focus: Testing Add New Ship Dynamic Structure vs Fallback Structure
"""

import requests
import json
import os
import sys
from datetime import datetime
import tempfile
import subprocess
import time
import base64
import uuid

# Configuration - Use production URL from frontend .env
BACKEND_URL = "https://shipment-ai-1.preview.emergentagent.com/api"

class AddNewShipDynamicStructureTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_credentials = [
            {"username": "admin1", "password": "123456", "description": "Primary admin account for AMCSC"},
            {"username": "admin", "password": "admin123", "description": "Demo admin account"}
        ]
        self.auth_token = None
        self.test_results = {}
        self.user_data = None
        self.company_id = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def authenticate(self):
        """Authenticate with the backend to get access token"""
        try:
            self.log("🔐 Authenticating with backend...")
            
            for cred in self.test_credentials:
                username = cred["username"]
                password = cred["password"]
                
                login_data = {
                    "username": username,
                    "password": password,
                    "remember_me": False
                }
                
                endpoint = f"{BACKEND_URL}/auth/login"
                self.log(f"   Attempting login to: {endpoint}")
                response = requests.post(endpoint, json=login_data, timeout=60)
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    self.user_data = data.get("user", {})
                    
                    self.log(f"✅ Authentication successful with {username}")
                    self.log(f"   User Role: {self.user_data.get('role')}")
                    self.log(f"   Company: {self.user_data.get('company')}")
                    self.log(f"   User ID: {self.user_data.get('id')}")
                    
                    # Get company ID for Google Drive operations
                    if self.user_data.get('company'):
                        self.company_id = self.get_company_id(self.user_data.get('company'))
                        self.log(f"   Company ID: {self.company_id}")
                    
                    return True
                else:
                    self.log(f"❌ Authentication failed with {username} - Status: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"   Error: {response.text[:200]}")
                    
            self.log("❌ Authentication failed with all credentials")
            return False
            
        except requests.exceptions.RequestException as req_error:
            self.log(f"❌ Network error during authentication: {str(req_error)}", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_company_id(self, company_name):
        """Get company ID from company name"""
        try:
            endpoint = f"{BACKEND_URL}/companies"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                companies = response.json()
                for company in companies:
                    if (company.get('name') == company_name or 
                        company.get('name_en') == company_name or 
                        company.get('name_vn') == company_name):
                        return company.get('id')
            return None
        except Exception as e:
            self.log(f"Error getting company ID: {e}")
            return None
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_add_new_ship_dynamic_structure(self):
        """Main test function for Add New Ship Dynamic Structure"""
        self.log("🚢 Starting Add New Ship Dynamic Structure Testing")
        self.log("🎯 Focus: Testing if Add New Ship uses dynamic structure or fallback structure")
        self.log("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 2: Test Sidebar Structure API (for dynamic structure)
        sidebar_result = self.test_sidebar_structure_api()
        
        # Step 3: Test Add New Ship API
        ship_creation_result = self.test_add_new_ship_api()
        
        # Step 4: Monitor Backend Logs for Folder Creation Process
        folder_creation_result = self.monitor_folder_creation_process()
        
        # Step 5: Check Google Apps Script Integration
        apps_script_result = self.test_google_apps_script_integration()
        
        # Step 6: Analyze Folder Structure Creation
        folder_structure_result = self.analyze_folder_structure_creation()
        
        # Step 7: Debug Backend API Call
        backend_debug_result = self.debug_backend_api_call()
        
        # Step 8: Summary
        self.log("=" * 80)
        self.log("🚢 ADD NEW SHIP DYNAMIC STRUCTURE TESTING SUMMARY")
        self.log("=" * 80)
        
        self.log(f"{'✅' if sidebar_result else '❌'} Sidebar Structure API: {'SUCCESS' if sidebar_result else 'FAILED'}")
        self.log(f"{'✅' if ship_creation_result else '❌'} Ship Creation API: {'SUCCESS' if ship_creation_result else 'FAILED'}")
        self.log(f"{'✅' if folder_creation_result else '❌'} Folder Creation Monitoring: {'SUCCESS' if folder_creation_result else 'FAILED'}")
        self.log(f"{'✅' if apps_script_result else '❌'} Google Apps Script Integration: {'SUCCESS' if apps_script_result else 'FAILED'}")
        self.log(f"{'✅' if folder_structure_result else '❌'} Folder Structure Analysis: {'SUCCESS' if folder_structure_result else 'FAILED'}")
        self.log(f"{'✅' if backend_debug_result else '❌'} Backend API Debug: {'SUCCESS' if backend_debug_result else 'FAILED'}")
        
        overall_success = all([sidebar_result, ship_creation_result, folder_creation_result, 
                              apps_script_result, folder_structure_result, backend_debug_result])
        
        if overall_success:
            self.log("🎉 ADD NEW SHIP DYNAMIC STRUCTURE TESTING: COMPLETED SUCCESSFULLY")
        else:
            self.log("❌ ADD NEW SHIP DYNAMIC STRUCTURE TESTING: ISSUES DETECTED")
            self.log("🔍 Check detailed logs above for specific issues")
        
        return overall_success
    
    def test_sidebar_structure_api(self):
        """Test GET /api/sidebar-structure endpoint for dynamic structure"""
        try:
            self.log("📋 Step 1: Testing Sidebar Structure API for Dynamic Structure...")
            
            endpoint = f"{BACKEND_URL}/sidebar-structure"
            self.log(f"   Testing endpoint: {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   GET /api/sidebar-structure - Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log("   ✅ Sidebar structure API accessible and returns JSON")
                    
                    # Store response for further analysis
                    self.test_results['sidebar_response'] = data
                    
                    # Check for dynamic structure indicators
                    if 'success' in data and data['success']:
                        self.log("   ✅ Response indicates success")
                    else:
                        self.log("   ❌ Response does not indicate success")
                        return False
                    
                    if 'structure' in data:
                        structure = data['structure']
                        self.log(f"   📊 Structure contains {len(structure)} main categories")
                        
                        # Check for expected dynamic structure elements
                        document_portfolio = structure.get("Document Portfolio", [])
                        if "Class Survey Report" in document_portfolio and "Test Report" in document_portfolio:
                            self.log("   ✅ Dynamic structure detected: 'Class Survey Report' and 'Test Report' found")
                            self.test_results['dynamic_structure_available'] = True
                        else:
                            self.log("   ⚠️ Fallback structure detected: Old naming convention found")
                            self.test_results['dynamic_structure_available'] = False
                    else:
                        self.log("   ❌ Response missing 'structure' field")
                        return False
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log("   ❌ Response is not valid JSON")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text[:200]
                
                self.log(f"   ❌ Sidebar structure API failed - HTTP {response.status_code}")
                self.log(f"      Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log(f"❌ Sidebar structure API testing error: {str(e)}", "ERROR")
            return False
    
    def test_add_new_ship_api(self):
        """Test POST /api/ships endpoint with new ship data"""
        try:
            self.log("🚢 Step 2: Testing Add New Ship API...")
            
            # Generate unique ship name for testing
            test_ship_name = f"TEST SHIP DYNAMIC {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            ship_data = {
                "name": test_ship_name,
                "imo": f"IMO{str(uuid.uuid4().int)[:7]}",  # Generate unique IMO
                "flag": "Panama",
                "ship_type": "General Cargo",
                "gross_tonnage": 5000,
                "deadweight": 8000,
                "built_year": 2020,
                "ship_owner": "Test Owner Company",
                "company": self.user_data.get('company', 'AMCSC')
            }
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   Testing endpoint: {endpoint}")
            self.log(f"   Ship data: {json.dumps(ship_data, indent=2)}")
            
            response = requests.post(endpoint, json=ship_data, headers=self.get_headers(), timeout=60)
            self.log(f"   POST /api/ships - Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    created_ship = response.json()
                    self.log("   ✅ Ship created successfully")
                    self.log(f"   Ship ID: {created_ship.get('id')}")
                    self.log(f"   Ship Name: {created_ship.get('name')}")
                    
                    # Store ship data for further testing
                    self.test_results['created_ship'] = created_ship
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log("   ❌ Response is not valid JSON")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text[:200]
                
                self.log(f"   ❌ Ship creation failed - HTTP {response.status_code}")
                self.log(f"      Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log(f"❌ Add new ship API testing error: {str(e)}", "ERROR")
            return False
    
    def monitor_folder_creation_process(self):
        """Monitor backend logs for folder creation process"""
        try:
            self.log("📁 Step 3: Monitoring Folder Creation Process...")
            
            # Check if ship was created
            created_ship = self.test_results.get('created_ship')
            if not created_ship:
                self.log("   ❌ No ship created to monitor folder creation")
                return False
            
            # Test company Google Drive folder creation endpoint
            if self.company_id:
                ship_name = created_ship.get('name')
                endpoint = f"{BACKEND_URL}/companies/{self.company_id}/gdrive/create-ship-folder"
                
                folder_data = {
                    "ship_name": ship_name,
                    "ship_id": created_ship.get('id')
                }
                
                self.log(f"   Testing folder creation endpoint: {endpoint}")
                self.log(f"   Folder data: {json.dumps(folder_data, indent=2)}")
                
                response = requests.post(endpoint, json=folder_data, headers=self.get_headers(), timeout=60)
                self.log(f"   POST /api/companies/{self.company_id}/gdrive/create-ship-folder - Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        folder_result = response.json()
                        self.log("   ✅ Folder creation API call successful")
                        self.log(f"   Folder creation result: {json.dumps(folder_result, indent=2)}")
                        
                        # Store folder creation result
                        self.test_results['folder_creation_result'] = folder_result
                        
                        return True
                        
                    except json.JSONDecodeError:
                        self.log("   ❌ Folder creation response is not valid JSON")
                        return False
                else:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', 'Unknown error')
                    except:
                        error_detail = response.text[:200]
                    
                    self.log(f"   ❌ Folder creation failed - HTTP {response.status_code}")
                    self.log(f"      Error: {error_detail}")
                    return False
            else:
                self.log("   ❌ No company ID available for folder creation testing")
                return False
                
        except Exception as e:
            self.log(f"❌ Folder creation monitoring error: {str(e)}", "ERROR")
            return False
    
    def test_google_apps_script_integration(self):
        """Check Google Apps Script Integration"""
        try:
            self.log("🔗 Step 4: Testing Google Apps Script Integration...")
            
            # Check if backend sends backend_api_url parameter to Apps Script
            if not self.company_id:
                self.log("   ❌ No company ID available for Google Apps Script testing")
                return False
            
            # Test Google Drive configuration
            endpoint = f"{BACKEND_URL}/companies/{self.company_id}/gdrive/config"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   GET /api/companies/{self.company_id}/gdrive/config - Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    config_data = response.json()
                    self.log("   ✅ Google Drive configuration retrieved")
                    
                    # Check if configuration includes Apps Script URL
                    config = config_data.get('config', {})
                    apps_script_url = config.get('web_app_url') or config.get('apps_script_url')
                    
                    if apps_script_url:
                        self.log(f"   ✅ Apps Script URL found: {apps_script_url}")
                        self.test_results['apps_script_url'] = apps_script_url
                        
                        # Test direct Apps Script communication
                        return self.test_apps_script_communication(apps_script_url)
                    else:
                        self.log("   ❌ No Apps Script URL found in configuration")
                        return False
                        
                except json.JSONDecodeError:
                    self.log("   ❌ Configuration response is not valid JSON")
                    return False
            else:
                self.log(f"   ❌ Failed to get Google Drive configuration - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Google Apps Script integration testing error: {str(e)}", "ERROR")
            return False
    
    def test_apps_script_communication(self, apps_script_url):
        """Test direct communication with Google Apps Script"""
        try:
            self.log("   🔗 Testing direct Apps Script communication...")
            
            # Test if Apps Script attempts to call /api/sidebar-structure
            test_payload = {
                "action": "test_connection",
                "backend_api_url": BACKEND_URL,
                "folder_id": "test_folder_id"
            }
            
            self.log(f"   Sending test payload to Apps Script: {json.dumps(test_payload, indent=2)}")
            
            response = requests.post(apps_script_url, json=test_payload, timeout=30)
            self.log(f"   Apps Script response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    apps_script_response = response.json()
                    self.log("   ✅ Apps Script communication successful")
                    self.log(f"   Apps Script response: {json.dumps(apps_script_response, indent=2)}")
                    
                    # Check if Apps Script indicates it can call backend API
                    if apps_script_response.get('success'):
                        self.log("   ✅ Apps Script indicates successful operation")
                        
                        # Store Apps Script response
                        self.test_results['apps_script_response'] = apps_script_response
                        
                        return True
                    else:
                        self.log("   ❌ Apps Script indicates operation failed")
                        return False
                        
                except json.JSONDecodeError:
                    self.log("   ❌ Apps Script response is not valid JSON")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return False
            else:
                self.log(f"   ❌ Apps Script communication failed - HTTP {response.status_code}")
                self.log(f"   Response: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Apps Script communication error: {str(e)}")
            return False
    
    def analyze_folder_structure_creation(self):
        """Analyze what folder structure is actually created"""
        try:
            self.log("📊 Step 5: Analyzing Folder Structure Creation...")
            
            folder_creation_result = self.test_results.get('folder_creation_result')
            if not folder_creation_result:
                self.log("   ❌ No folder creation result available for analysis")
                return False
            
            # Check what structure was created
            if 'folder_structure' in folder_creation_result:
                folder_structure = folder_creation_result['folder_structure']
                self.log("   ✅ Folder structure found in creation result")
                self.log(f"   Folder structure: {json.dumps(folder_structure, indent=2)}")
                
                # Analyze if dynamic structure was used
                dynamic_structure_used = False
                fallback_structure_used = False
                
                # Check for dynamic structure indicators
                if isinstance(folder_structure, dict):
                    for folder_name, subfolders in folder_structure.items():
                        if isinstance(subfolders, list):
                            if "Class Survey Report" in subfolders and "Test Report" in subfolders:
                                dynamic_structure_used = True
                                self.log("   ✅ Dynamic structure detected in created folders")
                                break
                            elif "Inspection Records" in subfolders or "Survey Reports" in subfolders:
                                fallback_structure_used = True
                                self.log("   ⚠️ Fallback structure detected in created folders")
                                break
                
                # Store analysis results
                self.test_results['dynamic_structure_used'] = dynamic_structure_used
                self.test_results['fallback_structure_used'] = fallback_structure_used
                
                if dynamic_structure_used:
                    self.log("   ✅ CONCLUSION: Dynamic structure successfully used for folder creation")
                elif fallback_structure_used:
                    self.log("   ⚠️ CONCLUSION: Fallback structure used - dynamic structure fetch may have failed")
                else:
                    self.log("   ❓ CONCLUSION: Unable to determine structure type from folder creation")
                
                return True
            else:
                self.log("   ❌ No folder structure found in creation result")
                return False
                
        except Exception as e:
            self.log(f"❌ Folder structure analysis error: {str(e)}", "ERROR")
            return False
    
    def debug_backend_api_call(self):
        """Debug Backend API Call for Apps Script folder creation"""
        try:
            self.log("🔍 Step 6: Debugging Backend API Call...")
            
            # Check if backend sends backend_api_url parameter
            apps_script_response = self.test_results.get('apps_script_response')
            if apps_script_response:
                self.log("   ✅ Apps Script response available for debugging")
                
                # Check if backend_api_url was received by Apps Script
                if 'backend_api_url' in str(apps_script_response):
                    self.log("   ✅ backend_api_url parameter detected in Apps Script communication")
                else:
                    self.log("   ❌ backend_api_url parameter NOT detected in Apps Script communication")
                
                # Check for any error messages
                if 'error' in apps_script_response:
                    self.log(f"   ⚠️ Apps Script reported error: {apps_script_response.get('error')}")
                
                return True
            else:
                self.log("   ❌ No Apps Script response available for debugging")
                return False
                
        except Exception as e:
            self.log(f"❌ Backend API call debugging error: {str(e)}", "ERROR")
            return False

def main():
    """Main test execution"""
    print("🚢 Ship Management System - Add New Ship Dynamic Structure Testing")
    print("🎯 Focus: Testing if Add New Ship uses dynamic structure or fallback structure")
    print("=" * 80)
    
    tester = AddNewShipDynamicStructureTester()
    success = tester.test_add_new_ship_dynamic_structure()
    
    print("=" * 80)
    if success:
        print("🎉 Add New Ship Dynamic Structure testing completed successfully!")
        print("✅ All test steps passed - functionality working correctly")
        
        # Print key findings summary
        print("\n🔑 KEY FINDINGS SUMMARY:")
        print("=" * 50)
        
        # Dynamic vs Fallback Structure Analysis
        dynamic_available = tester.test_results.get('dynamic_structure_available', False)
        dynamic_used = tester.test_results.get('dynamic_structure_used', False)
        fallback_used = tester.test_results.get('fallback_structure_used', False)
        
        print(f"📊 Dynamic Structure Available: {'✅ YES' if dynamic_available else '❌ NO'}")
        print(f"📁 Dynamic Structure Used: {'✅ YES' if dynamic_used else '❌ NO'}")
        print(f"🔄 Fallback Structure Used: {'⚠️ YES' if fallback_used else '✅ NO'}")
        
        # Apps Script Integration
        apps_script_url = tester.test_results.get('apps_script_url')
        if apps_script_url:
            print(f"🔗 Apps Script URL: {apps_script_url}")
        
        # Created Ship Info
        created_ship = tester.test_results.get('created_ship')
        if created_ship:
            print(f"🚢 Test Ship Created: {created_ship.get('name')} (ID: {created_ship.get('id')})")
        
        # Folder Structure Analysis
        folder_creation_result = tester.test_results.get('folder_creation_result')
        if folder_creation_result:
            print("📁 Folder Creation: ✅ SUCCESS")
        
        print("\n💡 INVESTIGATION RESULTS:")
        if dynamic_available and dynamic_used:
            print("✅ DYNAMIC STRUCTURE WORKING: Backend successfully sends backend_api_url to Apps Script")
            print("✅ Apps Script successfully calls /api/sidebar-structure for dynamic structure")
            print("✅ Folder creation uses updated names: 'Class Survey Report', 'Test Report'")
        elif dynamic_available and not dynamic_used:
            print("⚠️ DYNAMIC STRUCTURE AVAILABLE BUT NOT USED: Issue with Apps Script integration")
            print("❌ Apps Script may not be calling /api/sidebar-structure endpoint")
            print("❌ Folder creation falls back to old names: 'Inspection Records', 'Survey Reports'")
        else:
            print("❌ DYNAMIC STRUCTURE NOT AVAILABLE: /api/sidebar-structure endpoint issues")
            print("❌ Backend cannot provide dynamic structure to Apps Script")
        
        sys.exit(0)
    else:
        print("❌ Add New Ship Dynamic Structure testing completed with issues!")
        print("🔍 Some test steps failed - check detailed logs above")
        
        # Print diagnostic information
        print("\n🔍 DIAGNOSTIC INFORMATION:")
        print("=" * 50)
        
        if not tester.test_results.get('dynamic_structure_available'):
            print("❌ ISSUE: /api/sidebar-structure endpoint not working properly")
            print("   - Check if endpoint returns correct dynamic structure")
            print("   - Verify 'Class Survey Report' and 'Test Report' are in response")
        
        if not tester.test_results.get('apps_script_response'):
            print("❌ ISSUE: Google Apps Script communication failed")
            print("   - Check if Apps Script URL is correct")
            print("   - Verify Apps Script can receive backend_api_url parameter")
        
        if not tester.test_results.get('folder_creation_result'):
            print("❌ ISSUE: Folder creation failed")
            print("   - Check Google Drive configuration")
            print("   - Verify company has proper Google Drive setup")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
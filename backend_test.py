#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
Focus: Test enhanced ship creation functionality with improved Google Drive integration
Review Request: Test enhanced error handling, timeout improvements, retry logic, and better diagnostics
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import subprocess
import threading

# Configuration - Use external URL since internal has connection issues
BACKEND_URL = "https://shipai-system.preview.emergentagent.com/api"

class ShipCreationDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.log_capture_active = False
        
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
        
    def start_backend_log_monitoring(self):
        """Start monitoring backend logs in real-time"""
        try:
            self.log("🔍 Starting backend log monitoring...")
            self.log_capture_active = True
            
            # Monitor backend logs using tail command
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"   📋 Monitoring log file: {log_file}")
                    # Start background thread to monitor this log file
                    thread = threading.Thread(target=self._monitor_log_file, args=(log_file,))
                    thread.daemon = True
                    thread.start()
                else:
                    self.log(f"   ⚠️ Log file not found: {log_file}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to start backend log monitoring: {str(e)}", "ERROR")
            return False
    
    def _monitor_log_file(self, log_file):
        """Monitor a specific log file for new entries"""
        try:
            # Use tail -f to follow the log file
            process = subprocess.Popen(['tail', '-f', log_file], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     universal_newlines=True)
            
            while self.log_capture_active:
                line = process.stdout.readline()
                if line:
                    # Filter for relevant log entries
                    line = line.strip()
                    if any(keyword in line.lower() for keyword in [
                        'ship', 'google', 'drive', 'folder', 'create', 'error', 
                        '404', 'not configured', 'company', 'gdrive', 'apps script'
                    ]):
                        self.log(f"📋 BACKEND LOG: {line}", "BACKEND")
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
        except Exception as e:
            self.log(f"❌ Error monitoring log file {log_file}: {str(e)}", "ERROR")
    
    def stop_backend_log_monitoring(self):
        """Stop backend log monitoring"""
        self.log_capture_active = False
        self.log("🔍 Stopped backend log monitoring")
        
    def authenticate(self):
        """Authenticate with admin1/123456 credentials as specified in review request"""
        try:
            self.log("🔐 Authenticating with admin1/123456 (AMCSC company user)...")
            
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
                self.log(f"   Full Name: {self.current_user.get('full_name')}")
                
                return True
            else:
                self.log(f"❌ Authentication failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except requests.exceptions.RequestException as req_error:
            self.log(f"❌ Network error during authentication: {str(req_error)}", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def debug_ship_creation_workflow(self):
        """Main debug function for ship creation workflow"""
        self.log("🚢 STARTING SHIP CREATION DEBUG SESSION")
        self.log("🎯 Focus: Debug 'Failed to create ship folder: 404: Company Google Drive not configured'")
        self.log("📋 Review Request: Capture ALL backend logs during ship creation process")
        self.log("=" * 100)
        
        # Step 1: Start backend log monitoring
        if not self.start_backend_log_monitoring():
            self.log("⚠️ Backend log monitoring failed to start, continuing without it...")
        
        # Step 2: Authenticate
        if not self.authenticate():
            return False
        
        # Step 3: Pre-flight checks
        self.log("\n🔍 STEP 1: PRE-FLIGHT CHECKS")
        self.log("=" * 50)
        self.verify_company_configuration()
        
        # Step 4: Create ship and monitor for errors
        self.log("\n🚢 STEP 2: SHIP CREATION WITH FULL MONITORING")
        self.log("=" * 50)
        self.create_ship_with_monitoring()
        
        # Step 5: Analyze captured logs
        self.log("\n📊 STEP 3: LOG ANALYSIS")
        self.log("=" * 50)
        self.analyze_captured_logs()
        
        # Step 6: Test specific Google Drive endpoints
        self.log("\n🔧 STEP 4: GOOGLE DRIVE ENDPOINT TESTING")
        self.log("=" * 50)
        self.test_google_drive_endpoints()
        
        # Step 7: Stop log monitoring
        self.stop_backend_log_monitoring()
        
        # Step 8: Final analysis
        self.log("\n🎯 STEP 5: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_analysis()
        
        return True
    
    def verify_company_configuration(self):
        """Verify AMCSC company Google Drive configuration"""
        try:
            self.log("🏢 Verifying AMCSC company configuration...")
            
            # Get all companies
            endpoint = f"{BACKEND_URL}/companies"
            self.log(f"   GET {endpoint}")
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response: {response.status_code}")
            
            if response.status_code == 200:
                companies = response.json()
                self.log(f"   ✅ Found {len(companies)} companies")
                
                # Find AMCSC company
                amcsc_company = None
                for company in companies:
                    company_names = [
                        company.get('name', ''),
                        company.get('name_en', ''),
                        company.get('name_vn', '')
                    ]
                    if 'AMCSC' in str(company_names).upper():
                        amcsc_company = company
                        break
                
                if amcsc_company:
                    company_id = amcsc_company.get('id')
                    self.log(f"   ✅ Found AMCSC company (ID: {company_id})")
                    self.test_results['amcsc_company_id'] = company_id
                    
                    # Check Google Drive configuration
                    self.check_company_gdrive_config(company_id)
                    
                else:
                    self.log("   ❌ AMCSC company not found")
                    self.log(f"   Available companies: {[c.get('name', c.get('name_en', 'Unknown')) for c in companies]}")
            else:
                self.log(f"   ❌ Failed to get companies: {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Company verification error: {str(e)}", "ERROR")
    
    def check_company_gdrive_config(self, company_id):
        """Check company Google Drive configuration"""
        try:
            self.log(f"   🔧 Checking Google Drive config for company {company_id}...")
            
            # Test config endpoint
            config_endpoint = f"{BACKEND_URL}/companies/{company_id}/gdrive/config"
            self.log(f"      GET {config_endpoint}")
            config_response = requests.get(config_endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"      Response: {config_response.status_code}")
            
            if config_response.status_code == 200:
                config_data = config_response.json()
                self.log("      ✅ Google Drive configuration found")
                self.log(f"      Config: {json.dumps(config_data, indent=6)}")
                self.test_results['gdrive_config'] = config_data
            else:
                self.log(f"      ❌ Google Drive config not found: {config_response.status_code}")
                try:
                    error_data = config_response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown')}")
                except:
                    self.log(f"      Error: {config_response.text[:200]}")
            
            # Test status endpoint
            status_endpoint = f"{BACKEND_URL}/companies/{company_id}/gdrive/status"
            self.log(f"      GET {status_endpoint}")
            status_response = requests.get(status_endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"      Response: {status_response.status_code}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                self.log(f"      ✅ Google Drive status: {status_data.get('status')}")
                self.log(f"      Message: {status_data.get('message', 'No message')}")
                self.test_results['gdrive_status'] = status_data
            else:
                self.log(f"      ❌ Google Drive status check failed: {status_response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Google Drive config check error: {str(e)}", "ERROR")
    
    def create_ship_with_monitoring(self):
        """Create a new ship while monitoring all backend activity"""
        try:
            self.log("🚢 Creating new ship with full backend monitoring...")
            
            # Generate unique ship data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ship_data = {
                "name": f"DEBUG_SHIP_{timestamp}",
                "imo": f"DEBUG{timestamp[-6:]}",
                "company": "AMCSC",
                "flag": "Panama",
                "ship_type": "General Cargo",
                "gross_tonnage": 5000,
                "deadweight": 8000,
                "built_year": 2020,
                "ship_owner": "Debug Test Owner"
            }
            
            self.log(f"   Ship data: {json.dumps(ship_data, indent=3)}")
            
            # Mark the start of ship creation in logs
            self.log("🎬 === SHIP CREATION STARTING - MONITOR ALL BACKEND ACTIVITY ===")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   POST {endpoint}")
            
            # Make the request and capture timing
            start_time = time.time()
            response = requests.post(endpoint, json=ship_data, headers=self.get_headers(), timeout=120)
            end_time = time.time()
            
            self.log(f"🎬 === SHIP CREATION COMPLETED - RESPONSE RECEIVED ===")
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Response time: {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                ship_response = response.json()
                self.log("   ✅ Ship creation successful")
                self.log(f"   Ship ID: {ship_response.get('id')}")
                self.test_results['created_ship'] = ship_response
                
                # Wait a moment for any async operations to complete
                self.log("   ⏳ Waiting 5 seconds for any async Google Drive operations...")
                time.sleep(5)
                
            elif response.status_code == 400:
                self.log("   ❌ Ship creation failed with 400 Bad Request")
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                    self.log(f"   Error: {error_detail}")
                    
                    # Check for our target error
                    if "Failed to create ship folder" in str(error_detail) and "404" in str(error_detail):
                        self.log("   🎯 FOUND TARGET ERROR: 'Failed to create ship folder: 404: Company Google Drive not configured'")
                        self.test_results['target_error_found'] = True
                        self.test_results['target_error_detail'] = error_detail
                        
                except Exception as parse_error:
                    error_detail = response.text[:500]
                    self.log(f"   Error (raw): {error_detail}")
                    
                    if "Failed to create ship folder" in error_detail and "404" in error_detail:
                        self.log("   🎯 FOUND TARGET ERROR: 'Failed to create ship folder: 404: Company Google Drive not configured'")
                        self.test_results['target_error_found'] = True
                        self.test_results['target_error_detail'] = error_detail
                
                self.test_results['ship_creation_error'] = {
                    'status_code': response.status_code,
                    'error': error_detail
                }
                
            else:
                self.log(f"   ❌ Ship creation failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text[:500]
                
                self.log(f"   Error: {error_detail}")
                self.test_results['ship_creation_error'] = {
                    'status_code': response.status_code,
                    'error': error_detail
                }
            
            # Wait additional time to capture any delayed log entries
            self.log("   ⏳ Waiting additional 3 seconds to capture delayed log entries...")
            time.sleep(3)
            
        except Exception as e:
            self.log(f"❌ Ship creation monitoring error: {str(e)}", "ERROR")
    
    def analyze_captured_logs(self):
        """Analyze all captured backend logs for error patterns"""
        try:
            self.log("📊 Analyzing captured backend logs...")
            
            # Filter backend logs
            backend_logs = [log for log in self.backend_logs if log['level'] == 'BACKEND']
            self.log(f"   📋 Captured {len(backend_logs)} backend log entries")
            
            if backend_logs:
                self.log("   🔍 Backend log entries during ship creation:")
                for log_entry in backend_logs:
                    self.log(f"      [{log_entry['timestamp']}] {log_entry['message']}")
                
                # Look for specific error patterns
                error_patterns = [
                    "404",
                    "Company Google Drive not configured",
                    "Failed to create ship folder",
                    "Google Drive",
                    "Apps Script",
                    "folder creation failed",
                    "gdrive"
                ]
                
                found_patterns = []
                for pattern in error_patterns:
                    for log_entry in backend_logs:
                        if pattern.lower() in log_entry['message'].lower():
                            found_patterns.append({
                                'pattern': pattern,
                                'log': log_entry
                            })
                
                if found_patterns:
                    self.log("   🎯 Found relevant error patterns in logs:")
                    for pattern_match in found_patterns:
                        self.log(f"      Pattern '{pattern_match['pattern']}' found in: {pattern_match['log']['message']}")
                else:
                    self.log("   ℹ️ No specific error patterns found in backend logs")
            else:
                self.log("   ⚠️ No backend logs captured - log monitoring may not be working")
                
        except Exception as e:
            self.log(f"❌ Log analysis error: {str(e)}", "ERROR")
    
    def test_google_drive_endpoints(self):
        """Test specific Google Drive endpoints that might be failing"""
        try:
            self.log("🔧 Testing Google Drive endpoints for race conditions and 404 errors...")
            
            company_id = self.test_results.get('amcsc_company_id')
            if not company_id:
                self.log("   ❌ No company ID available for testing")
                return
            
            # Test 1: Direct folder creation endpoint
            self.log("   🧪 Test 1: Direct Google Drive folder creation endpoint")
            folder_endpoint = f"{BACKEND_URL}/companies/{company_id}/gdrive/create-ship-folder"
            folder_data = {
                "ship_name": "TEST_FOLDER_CREATION",
                "ship_id": "test-folder-id"
            }
            
            self.log(f"      POST {folder_endpoint}")
            folder_response = requests.post(folder_endpoint, json=folder_data, headers=self.get_headers(), timeout=60)
            self.log(f"      Response: {folder_response.status_code}")
            
            if folder_response.status_code == 200:
                self.log("      ✅ Direct folder creation successful")
                folder_result = folder_response.json()
                self.log(f"      Result: {json.dumps(folder_result, indent=6)}")
            else:
                self.log(f"      ❌ Direct folder creation failed: {folder_response.status_code}")
                try:
                    error_data = folder_response.json()
                    error_detail = error_data.get('detail', 'Unknown')
                    self.log(f"      Error: {error_detail}")
                    
                    if "404" in str(error_detail) and "Company Google Drive not configured" in str(error_detail):
                        self.log("      🎯 FOUND TARGET ERROR in direct folder creation!")
                        self.test_results['target_error_in_direct_call'] = True
                        
                except:
                    error_detail = folder_response.text[:300]
                    self.log(f"      Error (raw): {error_detail}")
            
            # Test 2: Test multiple rapid calls to check for race conditions
            self.log("   🧪 Test 2: Multiple rapid calls to check for race conditions")
            for i in range(3):
                self.log(f"      Rapid call {i+1}/3...")
                rapid_data = {
                    "ship_name": f"RAPID_TEST_{i+1}",
                    "ship_id": f"rapid-test-{i+1}"
                }
                rapid_response = requests.post(folder_endpoint, json=rapid_data, headers=self.get_headers(), timeout=30)
                self.log(f"      Call {i+1} response: {rapid_response.status_code}")
                
                if rapid_response.status_code != 200:
                    try:
                        error_data = rapid_response.json()
                        error_detail = error_data.get('detail', 'Unknown')
                        if "404" in str(error_detail):
                            self.log(f"      🎯 404 error in rapid call {i+1}: {error_detail}")
                    except:
                        pass
                
                time.sleep(0.5)  # Small delay between calls
            
            # Test 3: Check if there are any backend endpoints that Apps Script might be calling
            self.log("   🧪 Test 3: Testing potential Apps Script callback endpoints")
            potential_endpoints = [
                f"{BACKEND_URL}/companies/{company_id}/gdrive/callback",
                f"{BACKEND_URL}/companies/{company_id}/gdrive/folder-created",
                f"{BACKEND_URL}/gdrive/webhook",
                f"{BACKEND_URL}/companies/{company_id}/gdrive/verify"
            ]
            
            for endpoint in potential_endpoints:
                self.log(f"      Testing: {endpoint}")
                test_response = requests.get(endpoint, headers=self.get_headers(), timeout=10)
                self.log(f"      Response: {test_response.status_code}")
                
                if test_response.status_code == 404:
                    self.log(f"      🎯 Found 404 endpoint: {endpoint}")
                    self.test_results.setdefault('found_404_endpoints', []).append(endpoint)
                
        except Exception as e:
            self.log(f"❌ Google Drive endpoint testing error: {str(e)}", "ERROR")
    
    def provide_final_analysis(self):
        """Provide final analysis of the debugging session"""
        try:
            self.log("🎯 FINAL ANALYSIS - DEBUGGING RESULTS")
            self.log("=" * 60)
            
            # Check if we found the target error
            if self.test_results.get('target_error_found'):
                self.log("✅ TARGET ERROR SUCCESSFULLY IDENTIFIED:")
                self.log("   'Failed to create ship folder: 404: Company Google Drive not configured'")
                self.log(f"   Error detail: {self.test_results.get('target_error_detail', 'No detail')}")
                
                # Analyze the context
                if self.test_results.get('gdrive_config'):
                    self.log("   🔍 ANALYSIS: Google Drive config EXISTS but error still occurs")
                    self.log("   🎯 ROOT CAUSE: Backend logic issue - config exists but not being found during ship creation")
                else:
                    self.log("   🔍 ANALYSIS: No Google Drive config found - error is expected")
                    
            else:
                self.log("❌ TARGET ERROR NOT REPRODUCED in this session")
                
                # Check if ship creation was successful
                if self.test_results.get('created_ship'):
                    self.log("   ✅ Ship creation was successful")
                    self.log("   💡 The error may be intermittent or fixed")
                else:
                    self.log("   ❌ Ship creation failed for other reasons")
            
            # Check for 404 endpoints
            if self.test_results.get('found_404_endpoints'):
                self.log("🔍 FOUND POTENTIAL 404 ENDPOINTS:")
                for endpoint in self.test_results['found_404_endpoints']:
                    self.log(f"   - {endpoint}")
                self.log("   💡 These might be endpoints that Apps Script is trying to call")
            
            # Summary of findings
            self.log("\n📋 SUMMARY OF FINDINGS:")
            self.log("=" * 40)
            
            findings = []
            if self.test_results.get('target_error_found'):
                findings.append("✅ Target error reproduced and captured")
            if self.test_results.get('gdrive_config'):
                findings.append("✅ Google Drive configuration exists")
            if self.test_results.get('gdrive_status'):
                findings.append(f"✅ Google Drive status: {self.test_results['gdrive_status'].get('status')}")
            if self.test_results.get('created_ship'):
                findings.append("✅ Ship creation successful")
            if self.test_results.get('found_404_endpoints'):
                findings.append(f"⚠️ Found {len(self.test_results['found_404_endpoints'])} potential 404 endpoints")
            
            if not findings:
                findings.append("❌ No significant findings in this debug session")
            
            for finding in findings:
                self.log(f"   {finding}")
                
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    print("🚢 Ship Management System - Ship Creation Debug Session")
    print("🎯 Focus: Debug 'Failed to create ship folder: 404: Company Google Drive not configured'")
    print("📋 Review Request: Capture ALL backend logs during ship creation process")
    print("=" * 100)
    
    debugger = ShipCreationDebugger()
    success = debugger.debug_ship_creation_workflow()
    
    print("=" * 100)
    print("🔍 DEBUGGING SESSION RESULTS:")
    print("=" * 60)
    
    # Print detailed analysis
    if debugger.test_results.get('target_error_found'):
        print("🎯 TARGET ERROR SUCCESSFULLY REPRODUCED:")
        print("   'Failed to create ship folder: 404: Company Google Drive not configured'")
        
        error_detail = debugger.test_results.get('target_error_detail', 'No detail available')
        print(f"   Error Detail: {error_detail}")
        
        ship_error = debugger.test_results.get('ship_creation_error', {})
        print(f"   HTTP Status: {ship_error.get('status_code')}")
        
    else:
        print("❌ TARGET ERROR NOT REPRODUCED in this session")
        if debugger.test_results.get('created_ship'):
            print("   ✅ Ship creation was successful - error may be intermittent or fixed")
        else:
            print("   ❌ Ship creation failed for other reasons")
    
    if debugger.test_results.get('gdrive_config'):
        print("\n📋 Google Drive Configuration Status:")
        gdrive_config = debugger.test_results['gdrive_config']
        print(f"   Config exists: ✅ YES")
        print(f"   Config details: {json.dumps(gdrive_config, indent=4)}")
    else:
        print("\n📋 Google Drive Configuration Status:")
        print("   Config exists: ❌ NO")
    
    if debugger.test_results.get('gdrive_status'):
        gdrive_status = debugger.test_results['gdrive_status']
        print(f"\n📊 Google Drive Status: {gdrive_status.get('status')}")
        print(f"   Message: {gdrive_status.get('message')}")
    
    if debugger.test_results.get('found_404_endpoints'):
        print(f"\n🔍 Found {len(debugger.test_results['found_404_endpoints'])} potential 404 endpoints:")
        for endpoint in debugger.test_results['found_404_endpoints']:
            print(f"   - {endpoint}")
        print("   💡 These might be endpoints that Apps Script is trying to call")
    
    print("=" * 100)
    if success:
        print("🎉 Ship creation debugging session completed successfully!")
        print("✅ All debug steps executed - detailed analysis available above")
    else:
        print("❌ Ship creation debugging session completed with issues!")
        print("🔍 Check detailed logs above for specific issues")
    
    if debugger.test_results.get('target_error_found'):
        print("\n💡 NEXT STEPS FOR MAIN AGENT:")
        print("   1. Review the exact error message captured above")
        print("   2. Check backend code for Google Drive folder creation logic")
        print("   3. Verify company ID lookup during ship creation")
        print("   4. Check for race conditions in async Google Drive operations")
        print("   5. Examine Apps Script callback endpoints that might be failing")
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
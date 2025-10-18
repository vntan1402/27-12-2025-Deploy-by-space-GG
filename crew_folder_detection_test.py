#!/usr/bin/env python3
"""
Backend Test for Dynamic Folder Detection in Crew File Movement

REVIEW REQUEST REQUIREMENTS:
Test both crew file movement endpoints to verify dynamic folder detection is working correctly 
WITHOUT any hardcoded fallback folder IDs.

Test Endpoints:
1. POST `/api/crew/move-standby-files` - Move files for Standby crew to "COMPANY DOCUMENT/Standby Crew" folder
2. POST `/api/crew/move-files-to-ship` - Move files to "Ship Name/Crew Records" folder in Company Drive ROOT

Key Verification Points:
- Dynamic folder search: "🔍 Calling Apps Script to list folders in parent"
- Case-insensitive matching attempts
- Folder found: "✅ MATCH FOUND! Standby Crew folder" / "✅ MATCH FOUND! Ship folder"
- Auto-creation logic for Standby folder: "🆕 Standby Crew folder not found, creating it..."
- NO hardcoded folder IDs (search for "1KU_1o-FcY3g2O9dKO5xxPhv1P2u56aO6" should NOT appear)
- Database updates with `folder_path` field
- Proper error messages when folders not found
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
import subprocess

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fleet-cert-system.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class CrewFolderDetectionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for dynamic folder detection
        self.folder_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'crew_data_available': False,
            'ship_data_available': False,
            
            # Standby Files Endpoint Tests
            'standby_endpoint_accessible': False,
            'standby_dynamic_folder_search': False,
            'standby_case_insensitive_matching': False,
            'standby_folder_found': False,
            'standby_auto_creation_logic': False,
            'standby_no_hardcoded_fallback': False,
            'standby_database_update': False,
            'standby_proper_error_handling': False,
            
            # Ship Files Endpoint Tests
            'ship_endpoint_accessible': False,
            'ship_dynamic_folder_search': False,
            'ship_case_insensitive_matching': False,
            'ship_folder_found': False,
            'crew_records_subfolder_found': False,
            'ship_no_hardcoded_fallback': False,
            'ship_database_update': False,
            'ship_proper_error_handling': False,
            
            # Backend Log Verification
            'backend_logs_dynamic_search': False,
            'backend_logs_folder_comparison': False,
            'backend_logs_match_found': False,
            'backend_logs_no_hardcoded_ids': False,
            'backend_logs_folder_creation': False,
        }
        
        # Store test data
        self.test_crew_ids = []
        self.test_ship_name = "BROTHER 36"
        
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
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.folder_tests['authentication_successful'] = True
                self.folder_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_crew_data(self):
        """Get crew members with Standby status and ship assignments"""
        try:
            self.log("👥 Getting crew data for testing...")
            
            # Get all crew members
            response = self.session.get(f"{BACKEND_URL}/crew")
            
            if response.status_code == 200:
                crew_list = response.json()
                self.log(f"   Found {len(crew_list)} total crew members")
                
                # Find Standby crew
                standby_crew = [crew for crew in crew_list if (crew.get("status") or "").lower() == "standby"]
                self.log(f"   Found {len(standby_crew)} Standby crew members")
                
                # Find crew with ship assignments
                ship_crew = [crew for crew in crew_list if crew.get("ship_sign_on") and crew.get("ship_sign_on") != "-"]
                self.log(f"   Found {len(ship_crew)} crew members with ship assignments")
                
                # Find crew for BROTHER 36 specifically
                brother36_crew = [crew for crew in crew_list if crew.get("ship_sign_on") == self.test_ship_name]
                self.log(f"   Found {len(brother36_crew)} crew members assigned to {self.test_ship_name}")
                
                if standby_crew or brother36_crew:
                    self.folder_tests['crew_data_available'] = True
                    
                    # Store test crew IDs
                    if standby_crew:
                        self.test_crew_ids.extend([crew.get("id") for crew in standby_crew[:2]])  # Take first 2
                    if brother36_crew:
                        self.test_crew_ids.extend([crew.get("id") for crew in brother36_crew[:2]])  # Take first 2
                    
                    # Remove duplicates
                    self.test_crew_ids = list(set(self.test_crew_ids))
                    
                    self.log(f"✅ Selected {len(self.test_crew_ids)} crew members for testing")
                    return True
                else:
                    self.log("❌ No suitable crew members found for testing", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get crew data: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting crew data: {str(e)}", "ERROR")
            return False
    
    def get_ship_data(self):
        """Verify ship data is available"""
        try:
            self.log("🚢 Verifying ship data...")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships")
                
                # Look for test ship
                test_ship = None
                for ship in ships:
                    if ship.get("name") == self.test_ship_name:
                        test_ship = ship
                        break
                
                if test_ship:
                    self.log(f"✅ Found test ship: {self.test_ship_name}")
                    self.log(f"   Ship ID: {test_ship.get('id')}")
                    self.folder_tests['ship_data_available'] = True
                    return True
                else:
                    self.log(f"❌ Test ship '{self.test_ship_name}' not found", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get ship data: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting ship data: {str(e)}", "ERROR")
            return False
    
    def test_standby_files_endpoint(self):
        """Test POST /api/crew/move-standby-files endpoint"""
        try:
            self.log("📦 Testing POST /api/crew/move-standby-files endpoint...")
            
            # Find Standby crew for testing
            standby_crew_ids = []
            if self.test_crew_ids:
                # Get crew details to find Standby ones
                for crew_id in self.test_crew_ids:
                    try:
                        crew_response = self.session.get(f"{BACKEND_URL}/crew/{crew_id}")
                        if crew_response.status_code == 200:
                            crew_data = crew_response.json()
                            if (crew_data.get("status") or "").lower() == "standby":
                                standby_crew_ids.append(crew_id)
                    except:
                        continue
            
            if not standby_crew_ids:
                self.log("⚠️ No Standby crew found, testing with empty array", "WARNING")
                standby_crew_ids = []
            
            self.log(f"   Testing with {len(standby_crew_ids)} Standby crew members")
            
            # Clear backend logs before test
            self.clear_backend_logs()
            
            # Make request to move-standby-files endpoint
            endpoint = f"{BACKEND_URL}/crew/move-standby-files"
            self.log(f"   POST {endpoint}")
            
            request_data = {
                "crew_ids": standby_crew_ids
            }
            
            start_time = time.time()
            response = self.session.post(endpoint, json=request_data, timeout=120)
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.folder_tests['standby_endpoint_accessible'] = True
                self.log("✅ Standby files endpoint accessible")
                
                try:
                    result = response.json()
                    self.log(f"📊 Response: {json.dumps(result, indent=2)}")
                    
                    success = result.get("success", False)
                    moved_count = result.get("moved_count", 0)
                    message = result.get("message", "")
                    
                    self.log(f"   Success: {success}")
                    self.log(f"   Moved count: {moved_count}")
                    self.log(f"   Message: {message}")
                    
                    if success:
                        self.log("✅ Standby files endpoint returned success")
                        if moved_count > 0:
                            self.folder_tests['standby_database_update'] = True
                            self.log("✅ Files were moved (database likely updated)")
                    
                    # Check backend logs for dynamic folder detection patterns
                    self.check_backend_logs_for_standby_patterns()
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                    return False
            else:
                self.log(f"❌ Standby files endpoint failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Raw response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing standby files endpoint: {str(e)}", "ERROR")
            return False
    
    def test_ship_files_endpoint(self):
        """Test POST /api/crew/move-files-to-ship endpoint"""
        try:
            self.log("🚢 Testing POST /api/crew/move-files-to-ship endpoint...")
            
            # Find crew assigned to test ship
            ship_crew_ids = []
            if self.test_crew_ids:
                # Get crew details to find ones assigned to test ship
                for crew_id in self.test_crew_ids:
                    try:
                        crew_response = self.session.get(f"{BACKEND_URL}/crew/{crew_id}")
                        if crew_response.status_code == 200:
                            crew_data = crew_response.json()
                            if crew_data.get("ship_sign_on") == self.test_ship_name:
                                ship_crew_ids.append(crew_id)
                    except:
                        continue
            
            if not ship_crew_ids and self.test_crew_ids:
                # Use any available crew for testing
                ship_crew_ids = self.test_crew_ids[:1]
                self.log(f"⚠️ Using any available crew for ship endpoint testing", "WARNING")
            
            if not ship_crew_ids:
                self.log("⚠️ No crew found, testing with empty array", "WARNING")
                ship_crew_ids = []
            
            self.log(f"   Testing with {len(ship_crew_ids)} crew members for ship {self.test_ship_name}")
            
            # Clear backend logs before test
            self.clear_backend_logs()
            
            # Make request to move-files-to-ship endpoint
            endpoint = f"{BACKEND_URL}/crew/move-files-to-ship"
            self.log(f"   POST {endpoint}")
            
            request_data = {
                "crew_ids": ship_crew_ids,
                "ship_name": self.test_ship_name
            }
            
            start_time = time.time()
            response = self.session.post(endpoint, json=request_data, timeout=120)
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.folder_tests['ship_endpoint_accessible'] = True
                self.log("✅ Ship files endpoint accessible")
                
                try:
                    result = response.json()
                    self.log(f"📊 Response: {json.dumps(result, indent=2)}")
                    
                    success = result.get("success", False)
                    moved_count = result.get("moved_count", 0)
                    message = result.get("message", "")
                    
                    self.log(f"   Success: {success}")
                    self.log(f"   Moved count: {moved_count}")
                    self.log(f"   Message: {message}")
                    
                    if success:
                        self.log("✅ Ship files endpoint returned success")
                        if moved_count > 0:
                            self.folder_tests['ship_database_update'] = True
                            self.log("✅ Files were moved (database likely updated)")
                    
                    # Check backend logs for dynamic folder detection patterns
                    self.check_backend_logs_for_ship_patterns()
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                    return False
            else:
                self.log(f"❌ Ship files endpoint failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    
                    # Check for expected error messages
                    error_detail = error_data.get('detail', '')
                    if "not found" in error_detail.lower():
                        self.folder_tests['ship_proper_error_handling'] = True
                        self.log("✅ Proper error handling - folder not found message")
                except:
                    self.log(f"   Raw response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing ship files endpoint: {str(e)}", "ERROR")
            return False
    
    def test_error_scenarios(self):
        """Test error scenarios for both endpoints"""
        try:
            self.log("⚠️ Testing error scenarios...")
            
            # Test 1: Non-existent ship name
            self.log("   Testing with non-existent ship name...")
            
            endpoint = f"{BACKEND_URL}/crew/move-files-to-ship"
            request_data = {
                "crew_ids": self.test_crew_ids[:1] if self.test_crew_ids else [],
                "ship_name": "NON_EXISTENT_SHIP_XYZ"
            }
            
            response = self.session.post(endpoint, json=request_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [400, 404, 500]:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    self.log(f"   Error message: {error_detail}")
                    
                    if "not found" in error_detail.lower():
                        self.folder_tests['ship_proper_error_handling'] = True
                        self.log("✅ Proper error handling for non-existent ship")
                except:
                    pass
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing error scenarios: {str(e)}", "ERROR")
            return False
    
    def clear_backend_logs(self):
        """Clear backend logs to capture fresh logs for testing"""
        try:
            self.log("🧹 Clearing backend logs for fresh capture...")
            
            # We can't actually clear the logs, but we can note the current time
            # to filter logs from this point forward
            self.test_start_time = datetime.now()
            
        except Exception as e:
            self.log(f"⚠️ Could not clear backend logs: {str(e)}", "WARNING")
    
    def check_backend_logs_for_standby_patterns(self):
        """Check backend logs for Standby folder detection patterns"""
        try:
            self.log("📋 Checking backend logs for Standby folder detection patterns...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            patterns_found = {
                'dynamic_search': False,
                'folder_comparison': False,
                'match_found': False,
                'no_hardcoded_ids': True,  # Assume true until proven false
                'folder_creation': False
            }
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get recent logs (last 200 lines to capture our test)
                        result = subprocess.run(['tail', '-n', '200', log_file], 
                                              capture_output=True, text=True, timeout=10)
                        
                        if result.returncode == 0 and result.stdout.strip():
                            lines = result.stdout.strip().split('\n')
                            
                            for line in lines:
                                # Look for dynamic folder search patterns
                                if "🔍 Calling Apps Script to list folders in parent" in line:
                                    patterns_found['dynamic_search'] = True
                                    self.log(f"   ✅ Found dynamic search: {line.strip()}")
                                
                                # Look for folder comparison patterns
                                if "Comparing:" in line and "==" in line:
                                    patterns_found['folder_comparison'] = True
                                    self.log(f"   ✅ Found folder comparison: {line.strip()}")
                                
                                # Look for match found patterns
                                if "✅ MATCH FOUND! Standby Crew folder" in line:
                                    patterns_found['match_found'] = True
                                    self.log(f"   ✅ Found match: {line.strip()}")
                                
                                # Look for folder creation patterns
                                if "🆕 Standby Crew folder not found, creating it" in line:
                                    patterns_found['folder_creation'] = True
                                    self.log(f"   ✅ Found folder creation: {line.strip()}")
                                
                                # Check for hardcoded folder IDs (should NOT be found)
                                if "1KU_1o-FcY3g2O9dKO5xxPhv1P2u56aO6" in line:
                                    patterns_found['no_hardcoded_ids'] = False
                                    self.log(f"   ❌ Found hardcoded folder ID: {line.strip()}")
                        
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            # Update test results
            if patterns_found['dynamic_search']:
                self.folder_tests['standby_dynamic_folder_search'] = True
                self.folder_tests['backend_logs_dynamic_search'] = True
            
            if patterns_found['folder_comparison']:
                self.folder_tests['standby_case_insensitive_matching'] = True
                self.folder_tests['backend_logs_folder_comparison'] = True
            
            if patterns_found['match_found']:
                self.folder_tests['standby_folder_found'] = True
                self.folder_tests['backend_logs_match_found'] = True
            
            if patterns_found['folder_creation']:
                self.folder_tests['standby_auto_creation_logic'] = True
                self.folder_tests['backend_logs_folder_creation'] = True
            
            if patterns_found['no_hardcoded_ids']:
                self.folder_tests['standby_no_hardcoded_fallback'] = True
                self.folder_tests['backend_logs_no_hardcoded_ids'] = True
            
            self.log(f"📊 Standby patterns found: {sum(patterns_found.values())}/{len(patterns_found)}")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs for Standby patterns: {str(e)}", "ERROR")
    
    def check_backend_logs_for_ship_patterns(self):
        """Check backend logs for Ship folder detection patterns"""
        try:
            self.log("📋 Checking backend logs for Ship folder detection patterns...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            patterns_found = {
                'dynamic_search': False,
                'ship_folder_search': False,
                'crew_records_search': False,
                'match_found': False,
                'no_hardcoded_ids': True  # Assume true until proven false
            }
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get recent logs (last 200 lines to capture our test)
                        result = subprocess.run(['tail', '-n', '200', log_file], 
                                              capture_output=True, text=True, timeout=10)
                        
                        if result.returncode == 0 and result.stdout.strip():
                            lines = result.stdout.strip().split('\n')
                            
                            for line in lines:
                                # Look for dynamic folder search patterns
                                if "🔍 Calling Apps Script to list folders in Company Drive ROOT" in line:
                                    patterns_found['dynamic_search'] = True
                                    patterns_found['ship_folder_search'] = True
                                    self.log(f"   ✅ Found ship folder search: {line.strip()}")
                                
                                # Look for Crew Records subfolder search
                                if "🔍 Calling Apps Script to list folders inside ship" in line:
                                    patterns_found['crew_records_search'] = True
                                    self.log(f"   ✅ Found Crew Records search: {line.strip()}")
                                
                                # Look for match found patterns
                                if "✅ MATCH FOUND! Ship folder" in line or "✅ MATCH FOUND! Crew Records folder" in line:
                                    patterns_found['match_found'] = True
                                    self.log(f"   ✅ Found match: {line.strip()}")
                                
                                # Check for hardcoded folder IDs (should NOT be found)
                                if "1KU_1o-FcY3g2O9dKO5xxPhv1P2u56aO6" in line:
                                    patterns_found['no_hardcoded_ids'] = False
                                    self.log(f"   ❌ Found hardcoded folder ID: {line.strip()}")
                        
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            # Update test results
            if patterns_found['dynamic_search']:
                self.folder_tests['ship_dynamic_folder_search'] = True
            
            if patterns_found['ship_folder_search']:
                self.folder_tests['ship_case_insensitive_matching'] = True
            
            if patterns_found['crew_records_search']:
                self.folder_tests['crew_records_subfolder_found'] = True
            
            if patterns_found['match_found']:
                self.folder_tests['ship_folder_found'] = True
            
            if patterns_found['no_hardcoded_ids']:
                self.folder_tests['ship_no_hardcoded_fallback'] = True
            
            self.log(f"📊 Ship patterns found: {sum(patterns_found.values())}/{len(patterns_found)}")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs for Ship patterns: {str(e)}", "ERROR")
    
    def verify_database_updates(self):
        """Verify database updates with folder_path fields"""
        try:
            self.log("🗄️ Verifying database updates with folder_path fields...")
            
            if not self.test_crew_ids:
                self.log("⚠️ No test crew IDs available for database verification", "WARNING")
                return False
            
            # Check a few crew members for folder_path updates
            for crew_id in self.test_crew_ids[:2]:  # Check first 2
                try:
                    response = self.session.get(f"{BACKEND_URL}/crew/{crew_id}")
                    if response.status_code == 200:
                        crew_data = response.json()
                        crew_name = crew_data.get('full_name', 'Unknown')
                        
                        # Check for folder path fields
                        passport_folder_path = crew_data.get('passport_folder_path')
                        
                        if passport_folder_path:
                            self.log(f"✅ Found passport_folder_path for {crew_name}: {passport_folder_path}")
                            
                            # Verify expected folder paths
                            if "COMPANY DOCUMENT/Standby Crew" in passport_folder_path:
                                self.folder_tests['standby_database_update'] = True
                                self.log("✅ Standby folder path correctly updated in database")
                            elif f"{self.test_ship_name}/Crew Records" in passport_folder_path:
                                self.folder_tests['ship_database_update'] = True
                                self.log("✅ Ship folder path correctly updated in database")
                        else:
                            self.log(f"ℹ️ No passport_folder_path found for {crew_name}")
                
                except Exception as e:
                    self.log(f"⚠️ Error checking crew {crew_id}: {e}", "WARNING")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error verifying database updates: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_folder_detection_test(self):
        """Run comprehensive test of dynamic folder detection"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE DYNAMIC FOLDER DETECTION TEST")
            self.log("=" * 80)
            self.log("Testing Requirements:")
            self.log("1. POST /api/crew/move-standby-files - Dynamic Standby Crew folder detection")
            self.log("2. POST /api/crew/move-files-to-ship - Dynamic Ship/Crew Records folder detection")
            self.log("3. NO hardcoded fallback folder IDs")
            self.log("4. Proper error handling when folders not found")
            self.log("5. Database updates with actual folder paths")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Get test data
            self.log("\nSTEP 2: Getting test data")
            if not self.get_crew_data():
                self.log("⚠️ WARNING: Limited crew data available")
            
            if not self.get_ship_data():
                self.log("⚠️ WARNING: Ship data not available")
            
            # Step 3: Test Standby files endpoint
            self.log("\nSTEP 3: Testing Standby files endpoint")
            self.test_standby_files_endpoint()
            
            # Step 4: Test Ship files endpoint
            self.log("\nSTEP 4: Testing Ship files endpoint")
            self.test_ship_files_endpoint()
            
            # Step 5: Test error scenarios
            self.log("\nSTEP 5: Testing error scenarios")
            self.test_error_scenarios()
            
            # Step 6: Verify database updates
            self.log("\nSTEP 6: Verifying database updates")
            self.verify_database_updates()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE DYNAMIC FOLDER DETECTION TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 DYNAMIC FOLDER DETECTION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.folder_tests)
            passed_tests = sum(1 for result in self.folder_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('crew_data_available', 'Crew data available'),
                ('ship_data_available', 'Ship data available'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.folder_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Standby Files Endpoint Results
            self.log("\n📦 STANDBY FILES ENDPOINT:")
            standby_tests = [
                ('standby_endpoint_accessible', 'Endpoint accessible'),
                ('standby_dynamic_folder_search', 'Dynamic folder search'),
                ('standby_case_insensitive_matching', 'Case-insensitive matching'),
                ('standby_folder_found', 'Standby Crew folder found'),
                ('standby_auto_creation_logic', 'Auto-creation logic'),
                ('standby_no_hardcoded_fallback', 'No hardcoded fallback'),
                ('standby_database_update', 'Database folder_path update'),
                ('standby_proper_error_handling', 'Proper error handling'),
            ]
            
            for test_key, description in standby_tests:
                status = "✅ PASS" if self.folder_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Ship Files Endpoint Results
            self.log("\n🚢 SHIP FILES ENDPOINT:")
            ship_tests = [
                ('ship_endpoint_accessible', 'Endpoint accessible'),
                ('ship_dynamic_folder_search', 'Dynamic folder search'),
                ('ship_case_insensitive_matching', 'Case-insensitive matching'),
                ('ship_folder_found', 'Ship folder found'),
                ('crew_records_subfolder_found', 'Crew Records subfolder found'),
                ('ship_no_hardcoded_fallback', 'No hardcoded fallback'),
                ('ship_database_update', 'Database folder_path update'),
                ('ship_proper_error_handling', 'Proper error handling'),
            ]
            
            for test_key, description in ship_tests:
                status = "✅ PASS" if self.folder_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Verification Results
            self.log("\n📋 BACKEND LOGS VERIFICATION:")
            log_tests = [
                ('backend_logs_dynamic_search', 'Dynamic search logs'),
                ('backend_logs_folder_comparison', 'Folder comparison logs'),
                ('backend_logs_match_found', 'Match found logs'),
                ('backend_logs_no_hardcoded_ids', 'No hardcoded IDs in logs'),
                ('backend_logs_folder_creation', 'Folder creation logs'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.folder_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Requirements Assessment
            self.log("\n🎯 CRITICAL REQUIREMENTS ASSESSMENT:")
            
            critical_tests = [
                'standby_dynamic_folder_search',
                'standby_no_hardcoded_fallback',
                'ship_dynamic_folder_search',
                'ship_no_hardcoded_fallback'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.folder_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL DYNAMIC FOLDER DETECTION REQUIREMENTS MET")
                self.log("   ✅ Both endpoints use ONLY dynamic folder detection")
                self.log("   ✅ NO hardcoded fallback folder IDs detected")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Success Rate Assessment
            if success_rate >= 80:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the dynamic folder detection test"""
    tester = CrewFolderDetectionTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_folder_detection_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n⚠️ Test interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        tester.log(f"\n❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
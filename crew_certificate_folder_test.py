#!/usr/bin/env python3
"""
Backend Test for Auto-Determine Certificate Upload Folder Based on Crew's Ship Sign On

REVIEW REQUEST REQUIREMENTS:
Test the new logic where certificate upload folder is automatically determined based on crew's `ship_sign_on` field, 
without requiring ship_id from frontend.

CRITICAL CHANGES TO TEST:
1. POST /api/crew-certificates/manual - No longer requires `ship_id` query parameter
2. Certificate's `ship_id` field set automatically:
   - `ship_id = None` if crew's `ship_sign_on = "-"` (Standby)
   - `ship_id = ship.id` if crew's `ship_sign_on = ship name`
3. File upload to correct folder:
   - Standby crew → `COMPANY DOCUMENT/Standby Crew`
   - Ship-assigned crew → `{Ship Name}/Crew Records`

TEST SCENARIOS:
- Scenario 1: Create Certificate for Standby Crew
- Scenario 2: Create Certificate for Ship-Assigned Crew  
- Scenario 3: Database Verification
- Scenario 4: Error Handling - Invalid Crew ID
- Scenario 5: Error Handling - Missing Crew ID
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
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class CrewCertificateFolderTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for certificate folder determination
        self.folder_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'crew_data_available': False,
            
            # Scenario 1: Standby Crew Certificate
            'standby_crew_found': False,
            'standby_certificate_created_without_ship_id': False,
            'standby_certificate_ship_id_null': False,
            'standby_folder_logs_detected': False,
            'standby_upload_destination_correct': False,
            
            # Scenario 2: Ship-Assigned Crew Certificate
            'ship_assigned_crew_found': False,
            'ship_assigned_certificate_created_without_ship_id': False,
            'ship_assigned_certificate_ship_id_valid': False,
            'ship_assigned_folder_logs_detected': False,
            'ship_assigned_upload_destination_correct': False,
            
            # Database Verification
            'database_ship_id_verification_standby': False,
            'database_ship_id_verification_ship_assigned': False,
            
            # Error Handling
            'invalid_crew_id_returns_404': False,
            'missing_crew_id_returns_400': False,
            'proper_error_messages': False,
            
            # Backend Logs Verification
            'backend_logs_ship_sign_on_detection': False,
            'backend_logs_folder_determination': False,
            'backend_logs_upload_destination': False,
        }
        
        # Store test data
        self.standby_crew = None
        self.ship_assigned_crew = None
        self.created_certificate_ids = []
        
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
    
    def find_crew_members(self):
        """Find crew members for testing - one standby and one ship-assigned"""
        try:
            self.log("🔍 Finding crew members for testing...")
            
            # Get crew list
            response = self.session.get(f"{BACKEND_URL}/crew")
            
            if response.status_code == 200:
                crew_list = response.json()
                self.log(f"   Found {len(crew_list)} crew members")
                
                # Look for standby crew (ship_sign_on = "-")
                for crew in crew_list:
                    ship_sign_on = crew.get("ship_sign_on", "")
                    if ship_sign_on == "-":
                        self.standby_crew = crew
                        self.log(f"✅ Found standby crew: {crew.get('full_name')} (ship_sign_on: '{ship_sign_on}')")
                        self.folder_tests['standby_crew_found'] = True
                        break
                
                # Look for ship-assigned crew (ship_sign_on = ship name)
                for crew in crew_list:
                    ship_sign_on = crew.get("ship_sign_on", "")
                    if ship_sign_on and ship_sign_on != "-":
                        self.ship_assigned_crew = crew
                        self.log(f"✅ Found ship-assigned crew: {crew.get('full_name')} (ship_sign_on: '{ship_sign_on}')")
                        self.folder_tests['ship_assigned_crew_found'] = True
                        break
                
                if self.standby_crew or self.ship_assigned_crew:
                    self.folder_tests['crew_data_available'] = True
                    return True
                else:
                    self.log("❌ No suitable crew members found for testing", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get crew list: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding crew members: {str(e)}", "ERROR")
            return False
    
    def test_standby_crew_certificate_creation(self):
        """Test Scenario 1: Create Certificate for Standby Crew"""
        try:
            self.log("📋 SCENARIO 1: Testing certificate creation for Standby crew...")
            
            if not self.standby_crew:
                self.log("❌ No standby crew available for testing", "ERROR")
                return False
            
            crew_id = self.standby_crew.get("id")
            crew_name = self.standby_crew.get("full_name")
            ship_sign_on = self.standby_crew.get("ship_sign_on")
            
            self.log(f"   Crew: {crew_name}")
            self.log(f"   Crew ID: {crew_id}")
            self.log(f"   Ship Sign On: '{ship_sign_on}'")
            
            # Prepare certificate data (NO ship_id parameter)
            certificate_data = {
                "crew_id": crew_id,
                "crew_name": crew_name,
                "passport": self.standby_crew.get("passport", "TEST_PASSPORT"),
                "date_of_birth": "1990-01-01",
                "cert_name": "Test Certificate - Standby Crew",
                "cert_no": f"STANDBY_TEST_{int(time.time())}",
                "issued_date": "2024-01-01",
                "cert_expiry": "2026-01-01",
                "issued_by": "Test Authority"
            }
            
            # Make request WITHOUT ship_id query parameter
            endpoint = f"{BACKEND_URL}/crew-certificates/manual"
            self.log(f"   POST {endpoint} (WITHOUT ship_id parameter)")
            self.log(f"   Certificate data: {json.dumps(certificate_data, indent=2)}")
            
            start_time = time.time()
            response = self.session.post(endpoint, json=certificate_data, timeout=60)
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Certificate created successfully without ship_id parameter")
                self.folder_tests['standby_certificate_created_without_ship_id'] = True
                
                # Store certificate ID for cleanup
                cert_id = result.get("id")
                if cert_id:
                    self.created_certificate_ids.append(cert_id)
                
                # Check certificate ship_id field
                cert_ship_id = result.get("ship_id")
                self.log(f"   Certificate ship_id: {cert_ship_id}")
                
                if cert_ship_id is None:
                    self.log("✅ Certificate ship_id is None (correct for Standby crew)")
                    self.folder_tests['standby_certificate_ship_id_null'] = True
                else:
                    self.log(f"❌ Certificate ship_id should be None for Standby crew, got: {cert_ship_id}", "ERROR")
                
                # Check backend logs for folder determination
                self.check_backend_logs_for_standby_processing()
                
                return True
            else:
                self.log(f"❌ Certificate creation failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing standby crew certificate creation: {str(e)}", "ERROR")
            return False
    
    def test_ship_assigned_crew_certificate_creation(self):
        """Test Scenario 2: Create Certificate for Ship-Assigned Crew"""
        try:
            self.log("📋 SCENARIO 2: Testing certificate creation for Ship-assigned crew...")
            
            if not self.ship_assigned_crew:
                self.log("❌ No ship-assigned crew available for testing", "ERROR")
                return False
            
            crew_id = self.ship_assigned_crew.get("id")
            crew_name = self.ship_assigned_crew.get("full_name")
            ship_sign_on = self.ship_assigned_crew.get("ship_sign_on")
            
            self.log(f"   Crew: {crew_name}")
            self.log(f"   Crew ID: {crew_id}")
            self.log(f"   Ship Sign On: '{ship_sign_on}'")
            
            # Prepare certificate data (NO ship_id parameter)
            certificate_data = {
                "crew_id": crew_id,
                "crew_name": crew_name,
                "passport": self.ship_assigned_crew.get("passport", "TEST_PASSPORT"),
                "date_of_birth": "1990-01-01",
                "cert_name": "Test Certificate - Ship Assigned Crew",
                "cert_no": f"SHIP_TEST_{int(time.time())}",
                "issued_date": "2024-01-01",
                "cert_expiry": "2026-01-01",
                "issued_by": "Test Authority"
            }
            
            # Make request WITHOUT ship_id query parameter
            endpoint = f"{BACKEND_URL}/crew-certificates/manual"
            self.log(f"   POST {endpoint} (WITHOUT ship_id parameter)")
            self.log(f"   Certificate data: {json.dumps(certificate_data, indent=2)}")
            
            start_time = time.time()
            response = self.session.post(endpoint, json=certificate_data, timeout=60)
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Certificate created successfully without ship_id parameter")
                self.folder_tests['ship_assigned_certificate_created_without_ship_id'] = True
                
                # Store certificate ID for cleanup
                cert_id = result.get("id")
                if cert_id:
                    self.created_certificate_ids.append(cert_id)
                
                # Check certificate ship_id field
                cert_ship_id = result.get("ship_id")
                self.log(f"   Certificate ship_id: {cert_ship_id}")
                
                if cert_ship_id and cert_ship_id != "null":
                    self.log(f"✅ Certificate ship_id is valid UUID (correct for Ship-assigned crew): {cert_ship_id}")
                    self.folder_tests['ship_assigned_certificate_ship_id_valid'] = True
                else:
                    self.log(f"❌ Certificate ship_id should be valid UUID for Ship-assigned crew, got: {cert_ship_id}", "ERROR")
                
                # Check backend logs for folder determination
                self.check_backend_logs_for_ship_assigned_processing(ship_sign_on)
                
                return True
            else:
                self.log(f"❌ Certificate creation failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing ship-assigned crew certificate creation: {str(e)}", "ERROR")
            return False
    
    def test_database_verification(self):
        """Test Scenario 3: Database Verification of ship_id field"""
        try:
            self.log("🗄️ SCENARIO 3: Testing database verification of ship_id field...")
            
            if not self.created_certificate_ids:
                self.log("❌ No certificates created for verification", "ERROR")
                return False
            
            for cert_id in self.created_certificate_ids:
                try:
                    # Get certificate details
                    endpoint = f"{BACKEND_URL}/crew-certificates/{cert_id}"
                    response = self.session.get(endpoint, timeout=30)
                    
                    if response.status_code == 200:
                        cert_data = response.json()
                        cert_name = cert_data.get("cert_name", "")
                        ship_id = cert_data.get("ship_id")
                        
                        self.log(f"   Certificate: {cert_name}")
                        self.log(f"   Database ship_id: {ship_id}")
                        
                        # Verify based on certificate type
                        if "Standby" in cert_name:
                            if ship_id is None or ship_id == "null":
                                self.log("✅ Standby crew certificate has ship_id: null in database")
                                self.folder_tests['database_ship_id_verification_standby'] = True
                            else:
                                self.log(f"❌ Standby crew certificate should have ship_id: null, got: {ship_id}", "ERROR")
                        
                        elif "Ship Assigned" in cert_name:
                            if ship_id and ship_id != "null":
                                self.log(f"✅ Ship-assigned crew certificate has valid ship_id in database: {ship_id}")
                                self.folder_tests['database_ship_id_verification_ship_assigned'] = True
                            else:
                                self.log(f"❌ Ship-assigned crew certificate should have valid ship_id, got: {ship_id}", "ERROR")
                    else:
                        self.log(f"   ❌ Failed to get certificate {cert_id}: {response.status_code}")
                        
                except Exception as e:
                    self.log(f"   ❌ Error verifying certificate {cert_id}: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in database verification: {str(e)}", "ERROR")
            return False
    
    def test_error_handling_invalid_crew_id(self):
        """Test Scenario 4: Error Handling - Invalid Crew ID"""
        try:
            self.log("❌ SCENARIO 4: Testing error handling for invalid crew_id...")
            
            # Prepare certificate data with invalid crew_id
            certificate_data = {
                "crew_id": "invalid-crew-id-12345",
                "crew_name": "Invalid Crew",
                "passport": "INVALID123",
                "date_of_birth": "1990-01-01",
                "cert_name": "Test Certificate - Invalid Crew",
                "cert_no": "INVALID_TEST_123",
                "issued_date": "2024-01-01",
                "cert_expiry": "2026-01-01",
                "issued_by": "Test Authority"
            }
            
            endpoint = f"{BACKEND_URL}/crew-certificates/manual"
            self.log(f"   POST {endpoint} (with invalid crew_id)")
            
            response = self.session.post(endpoint, json=certificate_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 404:
                self.log("✅ Invalid crew_id returns 404 error as expected")
                self.folder_tests['invalid_crew_id_returns_404'] = True
                
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", "")
                    self.log(f"   Error message: {error_message}")
                    
                    if "Crew member not found" in error_message:
                        self.log("✅ Proper error message for invalid crew_id")
                        self.folder_tests['proper_error_messages'] = True
                        
                except Exception as e:
                    self.log(f"   Could not parse error response: {e}")
                
                return True
            else:
                self.log(f"❌ Expected 404 for invalid crew_id, got: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing invalid crew_id handling: {str(e)}", "ERROR")
            return False
    
    def test_error_handling_missing_crew_id(self):
        """Test Scenario 5: Error Handling - Missing Crew ID"""
        try:
            self.log("❌ SCENARIO 5: Testing error handling for missing crew_id...")
            
            # Prepare certificate data without crew_id
            certificate_data = {
                # Missing crew_id field
                "crew_name": "Missing Crew ID",
                "passport": "MISSING123",
                "date_of_birth": "1990-01-01",
                "cert_name": "Test Certificate - Missing Crew ID",
                "cert_no": "MISSING_TEST_123",
                "issued_date": "2024-01-01",
                "cert_expiry": "2026-01-01",
                "issued_by": "Test Authority"
            }
            
            endpoint = f"{BACKEND_URL}/crew-certificates/manual"
            self.log(f"   POST {endpoint} (without crew_id)")
            
            response = self.session.post(endpoint, json=certificate_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 400:
                self.log("✅ Missing crew_id returns 400 error as expected")
                self.folder_tests['missing_crew_id_returns_400'] = True
                
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", "")
                    self.log(f"   Error message: {error_message}")
                    
                    if "crew_id is required" in error_message:
                        self.log("✅ Proper error message for missing crew_id")
                        
                except Exception as e:
                    self.log(f"   Could not parse error response: {e}")
                
                return True
            else:
                self.log(f"❌ Expected 400 for missing crew_id, got: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing missing crew_id handling: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs_for_standby_processing(self):
        """Check backend logs for Standby crew processing"""
        try:
            self.log("📋 Checking backend logs for Standby crew processing...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            standby_patterns = [
                "Crew ship_sign_on: '-'",
                "Crew is Standby",
                "COMPANY DOCUMENT/Standby Crew",
                "Certificate ship_id: None",
                "Upload destination: COMPANY DOCUMENT/Standby Crew"
            ]
            
            found_patterns = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            for pattern in standby_patterns:
                                if pattern in result:
                                    found_patterns.append(pattern)
                                    self.log(f"   ✅ Found log pattern: {pattern}")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            if len(found_patterns) >= 3:  # At least 3 key patterns found
                self.log("✅ Standby crew processing logs detected")
                self.folder_tests['standby_folder_logs_detected'] = True
                self.folder_tests['backend_logs_ship_sign_on_detection'] = True
                self.folder_tests['backend_logs_folder_determination'] = True
                
                if "COMPANY DOCUMENT/Standby Crew" in found_patterns:
                    self.log("✅ Standby upload destination correct")
                    self.folder_tests['standby_upload_destination_correct'] = True
                    self.folder_tests['backend_logs_upload_destination'] = True
            else:
                self.log(f"⚠️ Only found {len(found_patterns)} standby patterns in logs", "WARNING")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs for standby processing: {str(e)}", "ERROR")
    
    def check_backend_logs_for_ship_assigned_processing(self, ship_name):
        """Check backend logs for Ship-assigned crew processing"""
        try:
            self.log(f"📋 Checking backend logs for Ship-assigned crew processing (ship: {ship_name})...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            ship_patterns = [
                f"Crew ship_sign_on: '{ship_name}'",
                f"Found ship: {ship_name}",
                f"{ship_name}/Crew Records",
                "Certificate ship_id:",
                f"Upload destination: {ship_name}/Crew Records"
            ]
            
            found_patterns = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            for pattern in ship_patterns:
                                if pattern in result:
                                    found_patterns.append(pattern)
                                    self.log(f"   ✅ Found log pattern: {pattern}")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            if len(found_patterns) >= 3:  # At least 3 key patterns found
                self.log("✅ Ship-assigned crew processing logs detected")
                self.folder_tests['ship_assigned_folder_logs_detected'] = True
                
                if f"{ship_name}/Crew Records" in found_patterns:
                    self.log("✅ Ship-assigned upload destination correct")
                    self.folder_tests['ship_assigned_upload_destination_correct'] = True
            else:
                self.log(f"⚠️ Only found {len(found_patterns)} ship-assigned patterns in logs", "WARNING")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs for ship-assigned processing: {str(e)}", "ERROR")
    
    def cleanup_test_data(self):
        """Clean up created test certificates"""
        try:
            self.log("🧹 Cleaning up test certificates...")
            
            for cert_id in self.created_certificate_ids[:]:
                try:
                    endpoint = f"{BACKEND_URL}/crew-certificates/{cert_id}"
                    response = self.session.delete(endpoint, timeout=30)
                    if response.status_code in [200, 204]:
                        self.log(f"   ✅ Cleaned up certificate ID: {cert_id}")
                        self.created_certificate_ids.remove(cert_id)
                    else:
                        self.log(f"   ⚠️ Failed to clean up certificate ID: {cert_id}")
                except Exception as e:
                    self.log(f"   ⚠️ Error cleaning up certificate ID {cert_id}: {str(e)}")
            
            self.log("✅ Cleanup completed")
            
        except Exception as e:
            self.log(f"❌ Error during cleanup: {str(e)}", "ERROR")
    
    def run_comprehensive_folder_determination_test(self):
        """Run comprehensive test of certificate folder determination logic"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE CERTIFICATE FOLDER DETERMINATION TEST")
            self.log("=" * 80)
            self.log("Testing NEW logic: Certificate upload folder auto-determined by crew's ship_sign_on")
            self.log("NO ship_id query parameter required from frontend")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find crew members for testing
            self.log("\nSTEP 2: Finding crew members for testing")
            if not self.find_crew_members():
                self.log("❌ CRITICAL: No suitable crew members found - cannot proceed")
                return False
            
            # Step 3: Test Standby crew certificate creation
            self.log("\nSTEP 3: Testing Standby crew certificate creation")
            self.test_standby_crew_certificate_creation()
            
            # Step 4: Test Ship-assigned crew certificate creation
            self.log("\nSTEP 4: Testing Ship-assigned crew certificate creation")
            self.test_ship_assigned_crew_certificate_creation()
            
            # Step 5: Database verification
            self.log("\nSTEP 5: Database verification of ship_id field")
            self.test_database_verification()
            
            # Step 6: Error handling - Invalid crew ID
            self.log("\nSTEP 6: Testing error handling - Invalid crew ID")
            self.test_error_handling_invalid_crew_id()
            
            # Step 7: Error handling - Missing crew ID
            self.log("\nSTEP 7: Testing error handling - Missing crew ID")
            self.test_error_handling_missing_crew_id()
            
            # Step 8: Cleanup
            self.log("\nSTEP 8: Cleanup test data")
            self.cleanup_test_data()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE CERTIFICATE FOLDER DETERMINATION TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 CERTIFICATE FOLDER DETERMINATION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.folder_tests)
            passed_tests = sum(1 for result in self.folder_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('crew_data_available', 'Crew data available'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.folder_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Standby Crew Results
            self.log("\n📋 STANDBY CREW CERTIFICATE TESTING:")
            standby_tests = [
                ('standby_crew_found', 'Standby crew found'),
                ('standby_certificate_created_without_ship_id', 'Certificate created without ship_id'),
                ('standby_certificate_ship_id_null', 'Certificate ship_id is null'),
                ('standby_folder_logs_detected', 'Folder determination logs detected'),
                ('standby_upload_destination_correct', 'Upload destination correct'),
            ]
            
            for test_key, description in standby_tests:
                status = "✅ PASS" if self.folder_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Ship-Assigned Crew Results
            self.log("\n🚢 SHIP-ASSIGNED CREW CERTIFICATE TESTING:")
            ship_tests = [
                ('ship_assigned_crew_found', 'Ship-assigned crew found'),
                ('ship_assigned_certificate_created_without_ship_id', 'Certificate created without ship_id'),
                ('ship_assigned_certificate_ship_id_valid', 'Certificate ship_id is valid'),
                ('ship_assigned_folder_logs_detected', 'Folder determination logs detected'),
                ('ship_assigned_upload_destination_correct', 'Upload destination correct'),
            ]
            
            for test_key, description in ship_tests:
                status = "✅ PASS" if self.folder_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Database Verification Results
            self.log("\n🗄️ DATABASE VERIFICATION:")
            db_tests = [
                ('database_ship_id_verification_standby', 'Standby crew ship_id verification'),
                ('database_ship_id_verification_ship_assigned', 'Ship-assigned crew ship_id verification'),
            ]
            
            for test_key, description in db_tests:
                status = "✅ PASS" if self.folder_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Error Handling Results
            self.log("\n❌ ERROR HANDLING:")
            error_tests = [
                ('invalid_crew_id_returns_404', 'Invalid crew_id returns 404'),
                ('missing_crew_id_returns_400', 'Missing crew_id returns 400'),
                ('proper_error_messages', 'Proper error messages'),
            ]
            
            for test_key, description in error_tests:
                status = "✅ PASS" if self.folder_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Results
            self.log("\n📋 BACKEND LOGS VERIFICATION:")
            log_tests = [
                ('backend_logs_ship_sign_on_detection', 'Ship sign on detection logs'),
                ('backend_logs_folder_determination', 'Folder determination logs'),
                ('backend_logs_upload_destination', 'Upload destination logs'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.folder_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'standby_certificate_created_without_ship_id',
                'standby_certificate_ship_id_null',
                'ship_assigned_certificate_created_without_ship_id',
                'ship_assigned_certificate_ship_id_valid',
                'invalid_crew_id_returns_404',
                'missing_crew_id_returns_400'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.folder_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL REQUIREMENTS MET")
                self.log("   ✅ Certificate folder auto-determination working correctly")
                self.log("   ✅ No ship_id parameter required from frontend")
                self.log("   ✅ Proper folder assignment based on crew's ship_sign_on")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Specific requirements verification
            self.log("\n🔍 KEY REQUIREMENTS VERIFICATION:")
            self.log("   1. POST /api/crew-certificates/manual accepts requests without ship_id")
            self.log("   2. Standby crew (ship_sign_on='-') → ship_id=null, folder='COMPANY DOCUMENT/Standby Crew'")
            self.log("   3. Ship crew (ship_sign_on=ship_name) → ship_id=valid_uuid, folder='{Ship Name}/Crew Records'")
            self.log("   4. Proper error handling for invalid/missing crew_id")
            
            if success_rate >= 85:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 70:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the certificate folder determination test"""
    try:
        print("🚀 Starting Certificate Folder Determination Test")
        print("=" * 80)
        
        tester = CrewCertificateFolderTester()
        
        # Run comprehensive test
        success = tester.run_comprehensive_folder_determination_test()
        
        # Print summary
        tester.print_test_summary()
        
        if success:
            print("\n✅ Certificate folder determination test completed successfully")
            return 0
        else:
            print("\n❌ Certificate folder determination test completed with issues")
            return 1
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
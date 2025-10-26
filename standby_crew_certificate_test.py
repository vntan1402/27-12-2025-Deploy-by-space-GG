#!/usr/bin/env python3
"""
Standby Crew Certificate File Upload Issue Investigation

PROBLEM REPORT:
When adding crew certificate for Standby crew, only the **summary file** is uploaded to Google Drive, 
but the **original certificate file** is NOT uploaded.

INVESTIGATION FOCUS:
1. Test Standby Crew Certificate Upload Flow
2. Compare with Ship-assigned crew upload
3. Check backend logs for upload process
4. Verify database records after upload
5. Check Apps Script responses

EXPECTED BACKEND LOGS:
📍 Upload destination: COMPANY DOCUMENT/Standby Crew (Standby crew)
📤 Uploading certificate to COMPANY DOCUMENT/Standby Crew: {filename}
✅ Found COMPANY DOCUMENT folder: {folder_id}
📤 Uploading certificate file: ...
📋 Uploading certificate summary file: SUMMARY/Crew Records/...
✅ Certificate file uploads completed successfully
📎 Certificate File ID: {file_id}
📋 Summary File ID: {summary_file_id}
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
import base64

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vessel-docs-sys.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class StandbyCertificateUploadTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking
        self.test_results = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'crew_data_found': False,
            'standby_crew_found': False,
            'ship_crew_found': False,
            
            # Standby crew certificate creation
            'standby_cert_creation_successful': False,
            'standby_cert_ship_id_null': False,
            'standby_cert_upload_attempted': False,
            'standby_cert_file_uploaded': False,
            'standby_summary_file_uploaded': False,
            
            # Ship crew certificate creation (comparison)
            'ship_cert_creation_successful': False,
            'ship_cert_ship_id_valid': False,
            'ship_cert_upload_attempted': False,
            'ship_cert_file_uploaded': False,
            'ship_summary_file_uploaded': False,
            
            # Backend logs verification
            'backend_logs_standby_upload': False,
            'backend_logs_company_document_folder': False,
            'backend_logs_certificate_upload_attempt': False,
            'backend_logs_summary_upload_attempt': False,
            'backend_logs_apps_script_response': False,
            
            # Database verification
            'standby_cert_file_id_stored': False,
            'standby_summary_file_id_stored': False,
            'ship_cert_file_id_stored': False,
            'ship_summary_file_id_stored': False,
            
            # Issue identification
            'standby_original_file_missing': False,
            'standby_summary_only_uploaded': False,
            'ship_both_files_uploaded': False,
            'root_cause_identified': False,
        }
        
        # Store test data
        self.standby_crew = None
        self.ship_crew = None
        self.standby_cert_id = None
        self.ship_cert_id = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
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
            response = requests.post(endpoint, json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.test_results['authentication_successful'] = True
                self.test_results['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_test_crew_members(self):
        """Find Standby crew and Ship-assigned crew for testing"""
        try:
            self.log("🔍 Finding test crew members...")
            
            response = self.session.get(f"{BACKEND_URL}/crew")
            
            if response.status_code == 200:
                crew_list = response.json()
                self.log(f"   Found {len(crew_list)} crew members")
                
                # Find Standby crew (ship_sign_on = "-")
                for crew in crew_list:
                    ship_sign_on = crew.get("ship_sign_on", "")
                    if ship_sign_on == "-":
                        self.standby_crew = crew
                        self.log(f"✅ Found Standby crew: {crew.get('full_name')} (ID: {crew.get('id')})")
                        self.log(f"   Ship Sign On: '{ship_sign_on}'")
                        self.test_results['standby_crew_found'] = True
                        break
                
                # Find Ship-assigned crew (ship_sign_on != "-")
                for crew in crew_list:
                    ship_sign_on = crew.get("ship_sign_on", "")
                    if ship_sign_on and ship_sign_on != "-":
                        self.ship_crew = crew
                        self.log(f"✅ Found Ship crew: {crew.get('full_name')} (ID: {crew.get('id')})")
                        self.log(f"   Ship Sign On: '{ship_sign_on}'")
                        self.test_results['ship_crew_found'] = True
                        break
                
                if self.standby_crew and self.ship_crew:
                    self.test_results['crew_data_found'] = True
                    return True
                else:
                    self.log("❌ Could not find both Standby and Ship crew members", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get crew list: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding crew members: {str(e)}", "ERROR")
            return False
    
    def create_certificate_for_standby_crew(self):
        """Create certificate for Standby crew (ship_id should be null)"""
        try:
            self.log("📋 Creating certificate for Standby crew...")
            
            if not self.standby_crew:
                self.log("❌ No Standby crew available", "ERROR")
                return False
            
            # Create certificate data for Standby crew
            cert_data = {
                "crew_id": self.standby_crew.get("id"),
                "crew_name": self.standby_crew.get("full_name"),
                "passport": self.standby_crew.get("passport"),
                "date_of_birth": "1990-01-01",
                "cert_name": "Test Standby Certificate",
                "cert_no": f"STANDBY-{int(time.time())}",
                "issued_date": "2024-01-01",
                "cert_expiry": "2026-01-01",
                "issued_by": "Test Authority"
            }
            
            endpoint = f"{BACKEND_URL}/crew-certificates/manual"
            self.log(f"   POST {endpoint}")
            self.log(f"   Crew: {cert_data['crew_name']} (Standby)")
            
            response = self.session.post(endpoint, json=cert_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.standby_cert_id = result.get("id")
                ship_id = result.get("ship_id")
                
                self.log("✅ Standby certificate created successfully")
                self.log(f"   Certificate ID: {self.standby_cert_id}")
                self.log(f"   Ship ID: {ship_id}")
                
                self.test_results['standby_cert_creation_successful'] = True
                
                # Verify ship_id is null for Standby crew
                if ship_id is None:
                    self.log("✅ Ship ID is null for Standby crew (correct)")
                    self.test_results['standby_cert_ship_id_null'] = True
                else:
                    self.log(f"❌ Ship ID should be null for Standby crew, got: {ship_id}", "ERROR")
                
                return True
            else:
                self.log(f"❌ Failed to create Standby certificate: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating Standby certificate: {str(e)}", "ERROR")
            return False
    
    def create_certificate_for_ship_crew(self):
        """Create certificate for Ship-assigned crew (ship_id should be valid UUID)"""
        try:
            self.log("📋 Creating certificate for Ship crew...")
            
            if not self.ship_crew:
                self.log("❌ No Ship crew available", "ERROR")
                return False
            
            # Create certificate data for Ship crew
            cert_data = {
                "crew_id": self.ship_crew.get("id"),
                "crew_name": self.ship_crew.get("full_name"),
                "passport": self.ship_crew.get("passport"),
                "date_of_birth": "1990-01-01",
                "cert_name": "Test Ship Certificate",
                "cert_no": f"SHIP-{int(time.time())}",
                "issued_date": "2024-01-01",
                "cert_expiry": "2026-01-01",
                "issued_by": "Test Authority"
            }
            
            endpoint = f"{BACKEND_URL}/crew-certificates/manual"
            self.log(f"   POST {endpoint}")
            self.log(f"   Crew: {cert_data['crew_name']} (Ship: {self.ship_crew.get('ship_sign_on')})")
            
            response = self.session.post(endpoint, json=cert_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.ship_cert_id = result.get("id")
                ship_id = result.get("ship_id")
                
                self.log("✅ Ship certificate created successfully")
                self.log(f"   Certificate ID: {self.ship_cert_id}")
                self.log(f"   Ship ID: {ship_id}")
                
                self.test_results['ship_cert_creation_successful'] = True
                
                # Verify ship_id is valid UUID for Ship crew
                if ship_id and len(ship_id) == 36:  # UUID format
                    self.log("✅ Ship ID is valid UUID for Ship crew (correct)")
                    self.test_results['ship_cert_ship_id_valid'] = True
                else:
                    self.log(f"❌ Ship ID should be valid UUID for Ship crew, got: {ship_id}", "ERROR")
                
                return True
            else:
                self.log(f"❌ Failed to create Ship certificate: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating Ship certificate: {str(e)}", "ERROR")
            return False
    
    def upload_certificate_file_standby(self):
        """Upload certificate file for Standby crew and check if both files are uploaded"""
        try:
            self.log("📤 Uploading certificate file for Standby crew...")
            
            if not self.standby_cert_id:
                self.log("❌ No Standby certificate ID available", "ERROR")
                return False
            
            # Create dummy PDF content (base64 encoded)
            dummy_pdf_content = "JVBERi0xLjQKJcOkw7zDtsOfCjIgMCBvYmoKPDwKL0xlbmd0aCAzIDAgUgo+PgpzdHJlYW0KQNC0xLjQKJcOkw7zDtsOfCjIgMCBvYmoKPDwKL0xlbmd0aCAzIDAgUgo+PgpzdHJlYW0K"
            
            upload_data = {
                "file_content": dummy_pdf_content,
                "filename": "standby_test_certificate.pdf",
                "content_type": "application/pdf",
                "summary_text": "Test certificate summary for Standby crew"
            }
            
            endpoint = f"{BACKEND_URL}/crew-certificates/{self.standby_cert_id}/upload-files"
            self.log(f"   POST {endpoint}")
            self.log(f"   Filename: {upload_data['filename']}")
            
            # Clear backend logs before upload to capture fresh logs
            self.clear_recent_backend_logs()
            
            start_time = time.time()
            response = self.session.post(endpoint, json=upload_data, timeout=120)
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", False)
                cert_file_id = result.get("crew_cert_file_id")
                summary_file_id = result.get("crew_cert_summary_file_id")
                
                self.log(f"   Success: {success}")
                self.log(f"   Certificate File ID: {cert_file_id}")
                self.log(f"   Summary File ID: {summary_file_id}")
                
                self.test_results['standby_cert_upload_attempted'] = True
                
                # Check if both files were uploaded
                if cert_file_id:
                    self.log("✅ Standby certificate file uploaded")
                    self.test_results['standby_cert_file_uploaded'] = True
                else:
                    self.log("❌ Standby certificate file NOT uploaded", "ERROR")
                    self.test_results['standby_original_file_missing'] = True
                
                if summary_file_id:
                    self.log("✅ Standby summary file uploaded")
                    self.test_results['standby_summary_file_uploaded'] = True
                else:
                    self.log("❌ Standby summary file NOT uploaded", "ERROR")
                
                # Check for the specific issue: only summary uploaded, not original
                if summary_file_id and not cert_file_id:
                    self.log("🚨 ISSUE CONFIRMED: Only summary file uploaded for Standby crew", "ERROR")
                    self.test_results['standby_summary_only_uploaded'] = True
                
                # Check backend logs for upload process
                self.check_backend_logs_for_standby_upload()
                
                return True
            else:
                self.log(f"❌ Standby certificate upload failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error uploading Standby certificate: {str(e)}", "ERROR")
            return False
    
    def upload_certificate_file_ship(self):
        """Upload certificate file for Ship crew and compare with Standby"""
        try:
            self.log("📤 Uploading certificate file for Ship crew...")
            
            if not self.ship_cert_id:
                self.log("❌ No Ship certificate ID available", "ERROR")
                return False
            
            # Create dummy PDF content (base64 encoded)
            dummy_pdf_content = "JVBERi0xLjQKJcOkw7zDtsOfCjIgMCBvYmoKPDwKL0xlbmd0aCAzIDAgUgo+PgpzdHJlYW0KQNC0xLjQKJcOkw7zDtsOfCjIgMCBvYmoKPDwKL0xlbmd0aCAzIDAgUgo+PgpzdHJlYW0K"
            
            upload_data = {
                "file_content": dummy_pdf_content,
                "filename": "ship_test_certificate.pdf",
                "content_type": "application/pdf",
                "summary_text": "Test certificate summary for Ship crew"
            }
            
            endpoint = f"{BACKEND_URL}/crew-certificates/{self.ship_cert_id}/upload-files"
            self.log(f"   POST {endpoint}")
            self.log(f"   Filename: {upload_data['filename']}")
            
            start_time = time.time()
            response = self.session.post(endpoint, json=upload_data, timeout=120)
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", False)
                cert_file_id = result.get("crew_cert_file_id")
                summary_file_id = result.get("crew_cert_summary_file_id")
                
                self.log(f"   Success: {success}")
                self.log(f"   Certificate File ID: {cert_file_id}")
                self.log(f"   Summary File ID: {summary_file_id}")
                
                self.test_results['ship_cert_upload_attempted'] = True
                
                # Check if both files were uploaded
                if cert_file_id:
                    self.log("✅ Ship certificate file uploaded")
                    self.test_results['ship_cert_file_uploaded'] = True
                else:
                    self.log("❌ Ship certificate file NOT uploaded", "ERROR")
                
                if summary_file_id:
                    self.log("✅ Ship summary file uploaded")
                    self.test_results['ship_summary_file_uploaded'] = True
                else:
                    self.log("❌ Ship summary file NOT uploaded", "ERROR")
                
                # Check if both files uploaded for Ship crew
                if cert_file_id and summary_file_id:
                    self.log("✅ Both files uploaded for Ship crew")
                    self.test_results['ship_both_files_uploaded'] = True
                
                return True
            else:
                self.log(f"❌ Ship certificate upload failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error uploading Ship certificate: {str(e)}", "ERROR")
            return False
    
    def clear_recent_backend_logs(self):
        """Clear recent backend logs to capture fresh upload logs"""
        try:
            # This is a placeholder - in real implementation, we might want to mark a timestamp
            # and only look at logs after this timestamp
            pass
        except Exception as e:
            self.log(f"⚠️ Could not clear backend logs: {str(e)}", "WARNING")
    
    def check_backend_logs_for_standby_upload(self):
        """Check backend logs for Standby upload process"""
        try:
            self.log("📋 Checking backend logs for Standby upload process...")
            
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            expected_patterns = [
                "Upload destination: COMPANY DOCUMENT/Standby Crew",
                "Uploading certificate to COMPANY DOCUMENT/Standby Crew",
                "Found COMPANY DOCUMENT folder",
                "Uploading certificate file:",
                "Uploading certificate summary file:",
                "Certificate file uploads completed",
                "Certificate File ID:",
                "Summary File ID:"
            ]
            
            found_patterns = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            for pattern in expected_patterns:
                                for line in lines:
                                    if pattern in line:
                                        found_patterns.append(pattern)
                                        self.log(f"   ✅ Found: {pattern}")
                                        break
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            # Check specific log patterns
            if "Upload destination: COMPANY DOCUMENT/Standby Crew" in found_patterns:
                self.test_results['backend_logs_standby_upload'] = True
            
            if "Found COMPANY DOCUMENT folder" in found_patterns:
                self.test_results['backend_logs_company_document_folder'] = True
            
            if "Uploading certificate file:" in found_patterns:
                self.test_results['backend_logs_certificate_upload_attempt'] = True
            
            if "Uploading certificate summary file:" in found_patterns:
                self.test_results['backend_logs_summary_upload_attempt'] = True
            
            if len(found_patterns) > 0:
                self.test_results['backend_logs_apps_script_response'] = True
                self.log(f"✅ Found {len(found_patterns)} expected log patterns")
            else:
                self.log("❌ No expected log patterns found", "ERROR")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def verify_database_records(self):
        """Verify database records for both certificates"""
        try:
            self.log("🗄️ Verifying database records...")
            
            # Check Standby certificate record
            if self.standby_cert_id:
                endpoint = f"{BACKEND_URL}/crew-certificates/{self.standby_cert_id}"
                response = self.session.get(endpoint, timeout=30)
                
                if response.status_code == 200:
                    cert_data = response.json()
                    cert_file_id = cert_data.get("crew_cert_file_id")
                    summary_file_id = cert_data.get("crew_cert_summary_file_id")
                    
                    self.log(f"📋 Standby certificate database record:")
                    self.log(f"   Certificate File ID: {cert_file_id}")
                    self.log(f"   Summary File ID: {summary_file_id}")
                    
                    if cert_file_id:
                        self.test_results['standby_cert_file_id_stored'] = True
                    if summary_file_id:
                        self.test_results['standby_summary_file_id_stored'] = True
            
            # Check Ship certificate record
            if self.ship_cert_id:
                endpoint = f"{BACKEND_URL}/crew-certificates/{self.ship_cert_id}"
                response = self.session.get(endpoint, timeout=30)
                
                if response.status_code == 200:
                    cert_data = response.json()
                    cert_file_id = cert_data.get("crew_cert_file_id")
                    summary_file_id = cert_data.get("crew_cert_summary_file_id")
                    
                    self.log(f"📋 Ship certificate database record:")
                    self.log(f"   Certificate File ID: {cert_file_id}")
                    self.log(f"   Summary File ID: {summary_file_id}")
                    
                    if cert_file_id:
                        self.test_results['ship_cert_file_id_stored'] = True
                    if summary_file_id:
                        self.test_results['ship_summary_file_id_stored'] = True
            
        except Exception as e:
            self.log(f"❌ Error verifying database records: {str(e)}", "ERROR")
    
    def analyze_root_cause(self):
        """Analyze the root cause of the issue"""
        try:
            self.log("🔍 Analyzing root cause of Standby crew upload issue...")
            
            # Compare Standby vs Ship upload results
            standby_cert_uploaded = self.test_results.get('standby_cert_file_uploaded', False)
            standby_summary_uploaded = self.test_results.get('standby_summary_file_uploaded', False)
            ship_cert_uploaded = self.test_results.get('ship_cert_file_uploaded', False)
            ship_summary_uploaded = self.test_results.get('ship_summary_file_uploaded', False)
            
            self.log("📊 Upload Results Comparison:")
            self.log(f"   Standby - Certificate File: {'✅' if standby_cert_uploaded else '❌'}")
            self.log(f"   Standby - Summary File: {'✅' if standby_summary_uploaded else '❌'}")
            self.log(f"   Ship - Certificate File: {'✅' if ship_cert_uploaded else '❌'}")
            self.log(f"   Ship - Summary File: {'✅' if ship_summary_uploaded else '❌'}")
            
            # Identify the specific issue
            if standby_summary_uploaded and not standby_cert_uploaded:
                if ship_cert_uploaded and ship_summary_uploaded:
                    self.log("🚨 ROOT CAUSE IDENTIFIED:", "ERROR")
                    self.log("   - Standby crew: Only summary file uploaded, certificate file missing", "ERROR")
                    self.log("   - Ship crew: Both files uploaded correctly", "ERROR")
                    self.log("   - Issue is specific to Standby crew upload path", "ERROR")
                    self.test_results['root_cause_identified'] = True
                    
                    # Potential causes
                    self.log("🔍 Potential Root Causes:")
                    self.log("   1. COMPANY DOCUMENT folder not found → Upload fails silently")
                    self.log("   2. Apps Script error creating Standby Crew subfolder")
                    self.log("   3. File content encoding issue for Standby upload")
                    self.log("   4. Logic error in is_standby branch (doesn't upload certificate?)")
                    self.log("   5. Exception caught but not properly logged")
                else:
                    self.log("⚠️ Both Standby and Ship uploads have issues", "WARNING")
            elif standby_cert_uploaded and standby_summary_uploaded:
                self.log("✅ Standby crew upload working correctly - issue may be resolved")
            else:
                self.log("❓ Upload pattern unclear - need more investigation")
            
        except Exception as e:
            self.log(f"❌ Error analyzing root cause: {str(e)}", "ERROR")
    
    def cleanup_test_data(self):
        """Clean up created test certificates"""
        try:
            self.log("🧹 Cleaning up test data...")
            
            # Note: We're not implementing certificate deletion here
            # as it might not be available or we want to preserve data for further investigation
            self.log("   Test certificates preserved for further investigation")
            
        except Exception as e:
            self.log(f"❌ Error during cleanup: {str(e)}", "ERROR")
    
    def run_comprehensive_test(self):
        """Run comprehensive test of Standby crew certificate upload issue"""
        try:
            self.log("🚀 STARTING STANDBY CREW CERTIFICATE UPLOAD INVESTIGATION")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find test crew members
            self.log("\nSTEP 2: Finding test crew members")
            if not self.find_test_crew_members():
                self.log("❌ CRITICAL: Could not find required crew members")
                return False
            
            # Step 3: Create certificate for Standby crew
            self.log("\nSTEP 3: Creating certificate for Standby crew")
            if not self.create_certificate_for_standby_crew():
                self.log("❌ CRITICAL: Could not create Standby certificate")
                return False
            
            # Step 4: Create certificate for Ship crew (comparison)
            self.log("\nSTEP 4: Creating certificate for Ship crew (comparison)")
            if not self.create_certificate_for_ship_crew():
                self.log("⚠️ WARNING: Could not create Ship certificate for comparison")
            
            # Step 5: Upload certificate file for Standby crew
            self.log("\nSTEP 5: Uploading certificate file for Standby crew")
            self.upload_certificate_file_standby()
            
            # Step 6: Upload certificate file for Ship crew (comparison)
            self.log("\nSTEP 6: Uploading certificate file for Ship crew (comparison)")
            self.upload_certificate_file_ship()
            
            # Step 7: Verify database records
            self.log("\nSTEP 7: Verifying database records")
            self.verify_database_records()
            
            # Step 8: Analyze root cause
            self.log("\nSTEP 8: Root cause analysis")
            self.analyze_root_cause()
            
            # Step 9: Cleanup
            self.log("\nSTEP 9: Cleanup")
            self.cleanup_test_data()
            
            self.log("\n" + "=" * 80)
            self.log("✅ STANDBY CREW CERTIFICATE UPLOAD INVESTIGATION COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in investigation: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of investigation results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 STANDBY CREW CERTIFICATE UPLOAD INVESTIGATION SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Test Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('crew_data_found', 'Test crew data found'),
                ('standby_crew_found', 'Standby crew found'),
                ('ship_crew_found', 'Ship crew found'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Certificate Creation Results
            self.log("\n📋 CERTIFICATE CREATION:")
            creation_tests = [
                ('standby_cert_creation_successful', 'Standby certificate created'),
                ('standby_cert_ship_id_null', 'Standby cert ship_id is null'),
                ('ship_cert_creation_successful', 'Ship certificate created'),
                ('ship_cert_ship_id_valid', 'Ship cert ship_id is valid UUID'),
            ]
            
            for test_key, description in creation_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # File Upload Results
            self.log("\n📤 FILE UPLOAD RESULTS:")
            upload_tests = [
                ('standby_cert_upload_attempted', 'Standby certificate upload attempted'),
                ('standby_cert_file_uploaded', 'Standby certificate file uploaded'),
                ('standby_summary_file_uploaded', 'Standby summary file uploaded'),
                ('ship_cert_upload_attempted', 'Ship certificate upload attempted'),
                ('ship_cert_file_uploaded', 'Ship certificate file uploaded'),
                ('ship_summary_file_uploaded', 'Ship summary file uploaded'),
            ]
            
            for test_key, description in upload_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Results
            self.log("\n📋 BACKEND LOGS VERIFICATION:")
            log_tests = [
                ('backend_logs_standby_upload', 'Standby upload logs found'),
                ('backend_logs_company_document_folder', 'COMPANY DOCUMENT folder logs'),
                ('backend_logs_certificate_upload_attempt', 'Certificate upload attempt logs'),
                ('backend_logs_summary_upload_attempt', 'Summary upload attempt logs'),
                ('backend_logs_apps_script_response', 'Apps Script response logs'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Database Verification Results
            self.log("\n🗄️ DATABASE VERIFICATION:")
            db_tests = [
                ('standby_cert_file_id_stored', 'Standby cert file ID stored'),
                ('standby_summary_file_id_stored', 'Standby summary file ID stored'),
                ('ship_cert_file_id_stored', 'Ship cert file ID stored'),
                ('ship_summary_file_id_stored', 'Ship summary file ID stored'),
            ]
            
            for test_key, description in db_tests:
                status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Issue Identification
            self.log("\n🚨 ISSUE IDENTIFICATION:")
            issue_tests = [
                ('standby_original_file_missing', 'Standby original file missing'),
                ('standby_summary_only_uploaded', 'Only summary uploaded for Standby'),
                ('ship_both_files_uploaded', 'Both files uploaded for Ship'),
                ('root_cause_identified', 'Root cause identified'),
            ]
            
            for test_key, description in issue_tests:
                status = "🚨 CONFIRMED" if self.test_results.get(test_key, False) else "❓ NOT DETECTED"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 INVESTIGATION CONCLUSION:")
            
            if self.test_results.get('standby_summary_only_uploaded', False):
                self.log("   🚨 ISSUE CONFIRMED: Standby crew certificate file upload is broken")
                self.log("   🚨 Only summary file is uploaded, original certificate file is missing")
                self.log("   🚨 This matches the reported problem exactly")
            elif self.test_results.get('standby_cert_file_uploaded', False) and self.test_results.get('standby_summary_file_uploaded', False):
                self.log("   ✅ ISSUE NOT REPRODUCED: Both files uploaded successfully for Standby crew")
                self.log("   ✅ The issue may have been fixed or is intermittent")
            else:
                self.log("   ❓ INCONCLUSIVE: Could not complete full test due to setup issues")
            
            # Recommendations
            self.log("\n💡 RECOMMENDATIONS:")
            if self.test_results.get('root_cause_identified', False):
                self.log("   1. Check COMPANY DOCUMENT folder detection in Apps Script")
                self.log("   2. Verify Standby Crew subfolder creation logic")
                self.log("   3. Review is_standby branch in dual_apps_script_manager.py")
                self.log("   4. Add more detailed logging for Standby upload path")
                self.log("   5. Test with actual Google Drive folder structure")
            else:
                self.log("   1. Repeat test with different crew members")
                self.log("   2. Check backend logs manually for more details")
                self.log("   3. Test with real certificate files")
                self.log("   4. Verify Apps Script deployment status")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing investigation summary: {str(e)}", "ERROR")

def main():
    """Main function to run the Standby crew certificate upload investigation"""
    tester = StandbyCertificateUploadTester()
    
    try:
        # Run comprehensive investigation
        success = tester.run_comprehensive_test()
        
        # Print detailed summary
        tester.print_test_summary()
        
        if success:
            print("\n✅ Investigation completed successfully")
            return 0
        else:
            print("\n❌ Investigation completed with issues")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Investigation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Critical error during investigation: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
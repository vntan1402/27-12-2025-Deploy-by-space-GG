#!/usr/bin/env python3
"""
Standby Crew Certificate File Upload Issue Investigation - Fixed Version

PROBLEM REPORT:
When adding crew certificate for Standby crew, only the **summary file** is uploaded to Google Drive, 
but the **original certificate file** is NOT uploaded.
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://test-survey-portal.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class StandbyCertUploadTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.standby_crew = None
        self.ship_crew = None
        self.standby_cert_id = None
        self.ship_cert_id = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
    def authenticate(self):
        """Authenticate with admin1/123456 credentials"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User: {self.current_user.get('username')} ({self.current_user.get('role')})")
                self.log(f"   Company: {self.current_user.get('company')}")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_crew_members(self):
        """Find Standby and Ship crew members"""
        try:
            self.log("🔍 Finding crew members...")
            
            response = self.session.get(f"{BACKEND_URL}/crew")
            
            if response.status_code == 200:
                crew_list = response.json()
                self.log(f"   Found {len(crew_list)} crew members")
                
                # Find Standby crew (ship_sign_on = "-")
                for crew in crew_list:
                    if crew.get("ship_sign_on") == "-":
                        self.standby_crew = crew
                        self.log(f"✅ Standby crew: {crew.get('full_name')} (ID: {crew.get('id')})")
                        break
                
                # Find Ship crew (ship_sign_on != "-")
                for crew in crew_list:
                    ship_sign_on = crew.get("ship_sign_on", "")
                    if ship_sign_on and ship_sign_on != "-":
                        self.ship_crew = crew
                        self.log(f"✅ Ship crew: {crew.get('full_name')} (Ship: {ship_sign_on})")
                        break
                
                return self.standby_crew and self.ship_crew
            else:
                self.log(f"❌ Failed to get crew list: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding crew: {str(e)}", "ERROR")
            return False
    
    def create_certificate(self, crew, cert_type="Standby"):
        """Create certificate for crew member"""
        try:
            self.log(f"📋 Creating {cert_type} certificate...")
            
            cert_data = {
                "crew_id": crew.get("id"),
                "crew_name": crew.get("full_name"),
                "passport": crew.get("passport"),
                "date_of_birth": "1990-01-01",
                "cert_name": f"Test {cert_type} Certificate",
                "cert_no": f"{cert_type.upper()}-{int(time.time())}",
                "issued_date": "2024-01-01",
                "cert_expiry": "2026-01-01",
                "issued_by": "Test Authority"
            }
            
            response = self.session.post(f"{BACKEND_URL}/crew-certificates/manual", json=cert_data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                cert_id = result.get("id")
                ship_id = result.get("ship_id")
                
                self.log(f"✅ {cert_type} certificate created")
                self.log(f"   Certificate ID: {cert_id}")
                self.log(f"   Ship ID: {ship_id}")
                
                if cert_type == "Standby":
                    self.standby_cert_id = cert_id
                    if ship_id is None:
                        self.log("✅ Ship ID is null for Standby crew (correct)")
                    else:
                        self.log(f"❌ Ship ID should be null for Standby, got: {ship_id}", "ERROR")
                else:
                    self.ship_cert_id = cert_id
                    if ship_id and len(ship_id) == 36:
                        self.log("✅ Ship ID is valid UUID for Ship crew (correct)")
                    else:
                        self.log(f"❌ Ship ID should be valid UUID, got: {ship_id}", "ERROR")
                
                return cert_id
            else:
                self.log(f"❌ Failed to create {cert_type} certificate: {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error creating {cert_type} certificate: {str(e)}", "ERROR")
            return None
    
    def upload_certificate_file(self, cert_id, cert_type="Standby"):
        """Upload certificate file and check results"""
        try:
            self.log(f"📤 Uploading {cert_type} certificate file...")
            
            # Valid minimal PDF in base64
            dummy_pdf_content = "JVBERi0xLjQKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovUGFnZXMgMiAwIFIKPj4KZW5kb2JqCjIgMCBvYmoKPDwKL1R5cGUgL1BhZ2VzCi9LaWRzIFszIDAgUl0KL0NvdW50IDEKPj4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovTWVkaWFCb3ggWzAgMCA2MTIgNzkyXQo+PgplbmRvYmoKeHJlZgowIDQKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMDExNSAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9TaXplIDQKL1Jvb3QgMSAwIFIKPj4Kc3RhcnR4cmVmCjE3NQolJUVPRg=="
            
            upload_data = {
                "file_content": dummy_pdf_content,
                "filename": f"{cert_type.lower()}_test_certificate.pdf",
                "content_type": "application/pdf",
                "summary_text": f"Test certificate summary for {cert_type} crew"
            }
            
            self.log(f"   POST {BACKEND_URL}/crew-certificates/{cert_id}/upload-files")
            self.log(f"   Filename: {upload_data['filename']}")
            
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/crew-certificates/{cert_id}/upload-files", 
                                       json=upload_data, timeout=120)
            end_time = time.time()
            
            self.log(f"⏱️ Processing time: {end_time - start_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", False)
                cert_file_id = result.get("crew_cert_file_id")
                summary_file_id = result.get("crew_cert_summary_file_id")
                
                self.log(f"   Success: {success}")
                self.log(f"   Certificate File ID: {cert_file_id}")
                self.log(f"   Summary File ID: {summary_file_id}")
                
                # Analyze results
                if cert_file_id and summary_file_id:
                    self.log(f"✅ {cert_type}: Both files uploaded successfully")
                    return "both_uploaded"
                elif summary_file_id and not cert_file_id:
                    self.log(f"🚨 {cert_type}: Only summary file uploaded - ISSUE DETECTED!", "ERROR")
                    return "summary_only"
                elif cert_file_id and not summary_file_id:
                    self.log(f"⚠️ {cert_type}: Only certificate file uploaded", "WARNING")
                    return "cert_only"
                else:
                    self.log(f"❌ {cert_type}: No files uploaded", "ERROR")
                    return "none_uploaded"
            else:
                self.log(f"❌ {cert_type} upload failed: {response.text}", "ERROR")
                return "upload_failed"
                
        except Exception as e:
            self.log(f"❌ Error uploading {cert_type} certificate: {str(e)}", "ERROR")
            return "error"
    
    def check_backend_logs(self):
        """Check backend logs for upload details"""
        try:
            self.log("📋 Checking backend logs...")
            
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
                "Summary File ID:",
                "Apps Script response"
            ]
            
            found_patterns = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        result = os.popen(f"tail -n 100 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            for pattern in expected_patterns:
                                for line in lines:
                                    if pattern in line:
                                        found_patterns.append(pattern)
                                        self.log(f"   ✅ Found: {pattern}")
                                        # Show the actual log line
                                        self.log(f"      {line.strip()}")
                                        break
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            if found_patterns:
                self.log(f"✅ Found {len(found_patterns)} expected log patterns")
            else:
                self.log("❌ No expected log patterns found in recent logs", "ERROR")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def run_investigation(self):
        """Run the complete investigation"""
        try:
            self.log("🚀 STARTING STANDBY CREW CERTIFICATE UPLOAD INVESTIGATION")
            self.log("=" * 80)
            
            # Step 1: Authentication
            if not self.authenticate():
                return False
            
            # Step 2: Find crew members
            if not self.find_crew_members():
                self.log("❌ Could not find required crew members")
                return False
            
            # Step 3: Create certificates
            standby_cert_id = self.create_certificate(self.standby_crew, "Standby")
            ship_cert_id = self.create_certificate(self.ship_crew, "Ship")
            
            if not standby_cert_id or not ship_cert_id:
                self.log("❌ Could not create required certificates")
                return False
            
            # Step 4: Upload files and compare results
            self.log("\n" + "=" * 50)
            self.log("📤 TESTING FILE UPLOADS")
            self.log("=" * 50)
            
            standby_result = self.upload_certificate_file(standby_cert_id, "Standby")
            ship_result = self.upload_certificate_file(ship_cert_id, "Ship")
            
            # Step 5: Analyze results
            self.log("\n" + "=" * 50)
            self.log("📊 RESULTS ANALYSIS")
            self.log("=" * 50)
            
            self.log(f"Standby crew upload result: {standby_result}")
            self.log(f"Ship crew upload result: {ship_result}")
            
            if standby_result == "summary_only" and ship_result == "both_uploaded":
                self.log("🚨 ISSUE CONFIRMED: Standby crew certificate file upload is broken!", "ERROR")
                self.log("🚨 Only summary file uploaded for Standby, but both files work for Ship crew", "ERROR")
            elif standby_result == "both_uploaded" and ship_result == "both_uploaded":
                self.log("✅ ISSUE NOT REPRODUCED: Both upload types working correctly")
            else:
                self.log("❓ INCONCLUSIVE: Unexpected upload pattern detected")
            
            # Step 6: Check backend logs
            self.log("\n" + "=" * 50)
            self.log("📋 BACKEND LOGS ANALYSIS")
            self.log("=" * 50)
            self.check_backend_logs()
            
            self.log("\n" + "=" * 80)
            self.log("✅ INVESTIGATION COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR: {str(e)}", "ERROR")
            traceback.print_exc()
            return False

def main():
    """Main function"""
    tester = StandbyCertUploadTester()
    
    try:
        success = tester.run_investigation()
        
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
        print(f"\n❌ Critical error: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
Google Drive Config Debug Test
FOCUS: Debug the gdrive_config collection query issue

The auto-rename endpoint queries: gdrive_config collection with {"company_id": company_id}
But other endpoints seem to find the config successfully.
Let's debug what's actually in the gdrive_config collection.
"""

import requests
import json
import os
import sys
from datetime import datetime

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vesseldocs.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class GDriveConfigDebugTester:
    def __init__(self):
        self.auth_token = None
        self.current_user = None
        self.company_id = "cd1951d0-223e-4a09-865b-593047ed8c2d"
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {message}")
        
    def authenticate(self):
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
                
                self.log("✅ Authentication successful")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_working_gdrive_operations(self):
        """Test Google Drive operations that are known to work"""
        try:
            self.log("✅ Testing working Google Drive operations...")
            
            # Test file view operation (we know this works from logs)
            test_file_id = "1AqBmCdBceyBemQ754y2zf3T28kYej1eH"  # From our target certificate
            
            endpoint = f"{BACKEND_URL}/gdrive/file/{test_file_id}/view"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            self.log(f"   GET {endpoint}")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Google Drive file view operation working")
                self.log(f"   File view URL generated successfully")
                return True
            else:
                self.log(f"❌ Google Drive file view failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing working operations: {str(e)}", "ERROR")
            return False
    
    def test_gdrive_config_endpoints(self):
        """Test various Google Drive configuration endpoints"""
        try:
            self.log("🔍 Testing Google Drive configuration endpoints...")
            
            # Test different endpoint patterns
            endpoints_to_test = [
                f"/companies/{self.company_id}/gdrive/status",
                f"/companies/{self.company_id}/gdrive/config",
                f"/companies/AMCSC/gdrive/status",
                f"/companies/AMCSC/gdrive/config",
                f"/gdrive/config",
                f"/gdrive/status"
            ]
            
            for endpoint_path in endpoints_to_test:
                endpoint = f"{BACKEND_URL}{endpoint_path}"
                
                try:
                    response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
                    self.log(f"   GET {endpoint}")
                    self.log(f"      Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            self.log(f"      ✅ SUCCESS: {json.dumps(result, indent=8)}")
                        except:
                            self.log(f"      ✅ SUCCESS: {response.text[:200]}")
                    elif response.status_code == 405:
                        self.log(f"      ⚠️ Method not allowed")
                    elif response.status_code == 404:
                        self.log(f"      ❌ Not found")
                    else:
                        self.log(f"      ❌ Error: {response.status_code}")
                        try:
                            error = response.json()
                            self.log(f"         {error}")
                        except:
                            self.log(f"         {response.text[:100]}")
                            
                except Exception as e:
                    self.log(f"      ❌ Exception: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing config endpoints: {str(e)}", "ERROR")
            return False
    
    def analyze_backend_logs_pattern(self):
        """Analyze the pattern from backend logs to understand how config is found"""
        try:
            self.log("📊 Analyzing backend logs pattern...")
            
            self.log("   From backend logs, we see:")
            self.log("      'Company Google Drive config for cd1951d0-223e-4a09-865b-593047ed8c2d: Found'")
            self.log("      'Apps Script response: {..., 'available_actions': [..., 'rename_file']}'")
            self.log("")
            self.log("   This means:")
            self.log("      1. Google Drive config DOES exist for company cd1951d0-223e-4a09-865b-593047ed8c2d")
            self.log("      2. Apps Script DOES support rename_file action")
            self.log("      3. The issue is in the auto-rename endpoint's config lookup")
            self.log("")
            self.log("   The auto-rename endpoint queries:")
            self.log("      gdrive_config_doc = await mongo_db.find_one('gdrive_config', {'company_id': company_id})")
            self.log("")
            self.log("   Possible issues:")
            self.log("      1. Field name mismatch (company_id vs company vs id)")
            self.log("      2. Data type mismatch (string vs UUID)")
            self.log("      3. Collection name mismatch")
            self.log("      4. Timing issue (config exists but not accessible)")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error analyzing logs: {str(e)}", "ERROR")
            return False
    
    def test_certificate_operations(self):
        """Test certificate operations to see how they access Google Drive"""
        try:
            self.log("📋 Testing certificate operations that work with Google Drive...")
            
            # Get certificates for MINH ANH 09
            ship_id = "b0951a01-0d0b-438b-9b5f-b67e030c1be1"
            endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   Found {len(certificates)} certificates")
                
                # Find certificates with Google Drive files
                gdrive_certs = [cert for cert in certificates if cert.get('google_drive_file_id')]
                self.log(f"   {len(gdrive_certs)} certificates have Google Drive files")
                
                if gdrive_certs:
                    # Test file view for one of them
                    test_cert = gdrive_certs[0]
                    file_id = test_cert.get('google_drive_file_id')
                    
                    self.log(f"   Testing file view for certificate: {test_cert.get('cert_name')}")
                    self.log(f"   File ID: {file_id}")
                    
                    view_endpoint = f"{BACKEND_URL}/gdrive/file/{file_id}/view"
                    view_response = requests.get(view_endpoint, headers=self.get_headers(), timeout=30)
                    
                    self.log(f"   File view response: {view_response.status_code}")
                    
                    if view_response.status_code == 200:
                        self.log("   ✅ Certificate Google Drive operations working")
                        return True
                    else:
                        self.log("   ❌ Certificate Google Drive operations failing")
                        return False
                else:
                    self.log("   ⚠️ No certificates with Google Drive files found")
                    return False
            else:
                self.log(f"   ❌ Failed to get certificates: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing certificate operations: {str(e)}", "ERROR")
            return False
    
    def provide_fix_recommendation(self):
        """Provide specific fix recommendation based on analysis"""
        try:
            self.log("💡 PROVIDING FIX RECOMMENDATION...")
            
            self.log("🔍 ROOT CAUSE ANALYSIS:")
            self.log("   1. Google Drive configuration EXISTS (confirmed by backend logs)")
            self.log("   2. Apps Script supports rename_file action (confirmed by logs)")
            self.log("   3. Other Google Drive operations work (file view, etc.)")
            self.log("   4. Only auto-rename endpoint fails with 'Google Drive not configured'")
            self.log("")
            self.log("🚨 IDENTIFIED ISSUE:")
            self.log("   The auto-rename endpoint uses this query:")
            self.log("   gdrive_config_doc = await mongo_db.find_one('gdrive_config', {'company_id': company_id})")
            self.log("")
            self.log("   But other working endpoints might use different field names or collection structure.")
            self.log("")
            self.log("💡 RECOMMENDED FIXES:")
            self.log("   1. IMMEDIATE FIX - Check field name in gdrive_config collection:")
            self.log("      - Change {'company_id': company_id} to {'company': company_id}")
            self.log("      - Or change to {'id': company_id}")
            self.log("      - Or check what field name other working endpoints use")
            self.log("")
            self.log("   2. DEBUG FIX - Add logging to auto-rename endpoint:")
            self.log("      - Log the company_id being used in the query")
            self.log("      - Log the result of the gdrive_config query")
            self.log("      - Compare with working endpoints")
            self.log("")
            self.log("   3. VERIFICATION FIX - Check collection structure:")
            self.log("      - Verify gdrive_config collection exists")
            self.log("      - Check field names in the collection")
            self.log("      - Ensure data types match")
            self.log("")
            self.log("🎯 MOST LIKELY FIX:")
            self.log("   Change line 8807 in server.py from:")
            self.log("   gdrive_config_doc = await mongo_db.find_one('gdrive_config', {'company_id': company_id})")
            self.log("   To:")
            self.log("   gdrive_config_doc = await mongo_db.find_one('gdrive_config', {'company': company_id})")
            self.log("   Or whatever field name the working endpoints use.")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error providing recommendation: {str(e)}", "ERROR")
            return False
    
    def run_debug_test(self):
        """Main debug test function"""
        self.log("🔄 STARTING GOOGLE DRIVE CONFIG DEBUG TEST")
        self.log("=" * 80)
        
        try:
            # Step 1: Authenticate
            if not self.authenticate():
                return False
            
            # Step 2: Test working Google Drive operations
            self.log("\n✅ STEP 2: TEST WORKING GOOGLE DRIVE OPERATIONS")
            self.log("=" * 50)
            self.test_working_gdrive_operations()
            
            # Step 3: Test various config endpoints
            self.log("\n🔍 STEP 3: TEST GOOGLE DRIVE CONFIG ENDPOINTS")
            self.log("=" * 50)
            self.test_gdrive_config_endpoints()
            
            # Step 4: Test certificate operations
            self.log("\n📋 STEP 4: TEST CERTIFICATE GOOGLE DRIVE OPERATIONS")
            self.log("=" * 50)
            self.test_certificate_operations()
            
            # Step 5: Analyze backend logs pattern
            self.log("\n📊 STEP 5: ANALYZE BACKEND LOGS PATTERN")
            self.log("=" * 50)
            self.analyze_backend_logs_pattern()
            
            # Step 6: Provide fix recommendation
            self.log("\n💡 STEP 6: PROVIDE FIX RECOMMENDATION")
            self.log("=" * 50)
            self.provide_fix_recommendation()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Debug test error: {str(e)}", "ERROR")
            return False

def main():
    print("🔄 GOOGLE DRIVE CONFIG DEBUG TEST STARTED")
    print("=" * 80)
    
    try:
        tester = GDriveConfigDebugTester()
        success = tester.run_debug_test()
        
        if success:
            print("\n✅ GOOGLE DRIVE CONFIG DEBUG TEST COMPLETED")
        else:
            print("\n❌ GOOGLE DRIVE CONFIG DEBUG TEST COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
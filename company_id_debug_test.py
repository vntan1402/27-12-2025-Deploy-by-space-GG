#!/usr/bin/env python3
"""
Company ID Resolution Debug Test
FOCUS: Debug the company ID resolution issue in auto-rename functionality

The logs show Google Drive config exists for cd1951d0-223e-4a09-865b-593047ed8c2d
but auto-rename returns "Google Drive not configured for this company"
This suggests an issue with company ID resolution in the auto-rename endpoint.
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

class CompanyIdDebugTester:
    def __init__(self):
        self.auth_token = None
        self.current_user = None
        self.target_certificate_id = "0ca0e8e7-6238-4582-be32-2ccb6e687928"
        
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
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def debug_company_resolution(self):
        """Debug company ID resolution process"""
        try:
            self.log("🔍 Debugging company ID resolution...")
            
            user_company = self.current_user.get('company')
            self.log(f"   User company from token: {user_company}")
            
            # Check if it looks like a UUID
            if user_company and len(user_company) > 10 and '-' in user_company:
                self.log(f"   ✅ Company appears to be UUID format: {user_company}")
                company_id = user_company
            else:
                self.log(f"   ⚠️ Company appears to be name format, need to resolve to UUID")
                
                # Get all companies to find the mapping
                response = requests.get(f"{BACKEND_URL}/companies", headers=self.get_headers(), timeout=30)
                if response.status_code == 200:
                    companies = response.json()
                    self.log(f"   Found {len(companies)} companies in database:")
                    
                    company_id = None
                    for company in companies:
                        company_name_vn = company.get('name_vn', '')
                        company_name_en = company.get('name_en', '')
                        company_name = company.get('name', '')
                        company_uuid = company.get('id', '')
                        
                        self.log(f"      Company: {company_uuid}")
                        self.log(f"         name_vn: {company_name_vn}")
                        self.log(f"         name_en: {company_name_en}")
                        self.log(f"         name: {company_name}")
                        
                        # Check if this matches the user's company
                        if (user_company == company_name_vn or 
                            user_company == company_name_en or 
                            user_company == company_name):
                            company_id = company_uuid
                            self.log(f"   ✅ Found matching company UUID: {company_id}")
                            break
                    
                    if not company_id:
                        self.log(f"   ❌ No matching company found for '{user_company}'")
                        return None
                else:
                    self.log(f"   ❌ Failed to get companies: {response.status_code}")
                    return None
            
            return company_id
            
        except Exception as e:
            self.log(f"❌ Error debugging company resolution: {str(e)}", "ERROR")
            return None
    
    def check_gdrive_config_directly(self, company_id):
        """Check Google Drive configuration directly using the resolved company ID"""
        try:
            self.log(f"☁️ Checking Google Drive config for company ID: {company_id}")
            
            # Try the gdrive status endpoint with the resolved company ID
            endpoint = f"{BACKEND_URL}/companies/{company_id}/gdrive/status"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            self.log(f"   GET {endpoint}")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                config = response.json()
                self.log("✅ Google Drive configuration found!")
                self.log(f"   Config: {json.dumps(config, indent=4)}")
                return True
            elif response.status_code == 405:
                self.log("⚠️ Method not allowed - endpoint may not exist")
                return False
            elif response.status_code == 404:
                self.log("❌ Google Drive configuration not found")
                return False
            else:
                self.log(f"❌ Unexpected response: {response.status_code}")
                try:
                    error = response.json()
                    self.log(f"   Error: {error}")
                except:
                    self.log(f"   Error text: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking Google Drive config: {str(e)}", "ERROR")
            return False
    
    def test_auto_rename_with_debug(self, company_id):
        """Test auto-rename endpoint with detailed debugging"""
        try:
            self.log(f"🔄 Testing auto-rename with company ID: {company_id}")
            
            endpoint = f"{BACKEND_URL}/certificates/{self.target_certificate_id}/auto-rename-file"
            response = requests.post(endpoint, headers=self.get_headers(), timeout=60)
            
            self.log(f"   POST {endpoint}")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 404:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                    self.log(f"   Error detail: {error_detail}")
                    
                    if "Google Drive not configured" in error_detail:
                        self.log("   🔍 ISSUE: Auto-rename endpoint thinks Google Drive is not configured")
                        self.log("   🔍 But we know from logs that config exists for cd1951d0-223e-4a09-865b-593047ed8c2d")
                        self.log("   🔍 This suggests company ID resolution issue in the endpoint")
                        return False
                    else:
                        self.log(f"   🔍 Different 404 error: {error_detail}")
                        return False
                        
                except Exception as e:
                    self.log(f"   Error parsing response: {e}")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return False
            else:
                self.log(f"   ✅ Auto-rename endpoint returned: {response.status_code}")
                try:
                    result = response.json()
                    self.log(f"   Result: {json.dumps(result, indent=4)}")
                except:
                    self.log(f"   Response text: {response.text[:500]}")
                return True
                
        except Exception as e:
            self.log(f"❌ Error testing auto-rename: {str(e)}", "ERROR")
            return False
    
    def run_debug_test(self):
        """Main debug test function"""
        self.log("🔄 STARTING COMPANY ID RESOLUTION DEBUG TEST")
        self.log("=" * 80)
        
        try:
            # Step 1: Authenticate
            if not self.authenticate():
                return False
            
            # Step 2: Debug company resolution
            self.log("\n🔍 STEP 2: DEBUG COMPANY ID RESOLUTION")
            self.log("=" * 50)
            company_id = self.debug_company_resolution()
            
            if not company_id:
                self.log("❌ Could not resolve company ID")
                return False
            
            # Step 3: Check Google Drive config directly
            self.log("\n☁️ STEP 3: CHECK GOOGLE DRIVE CONFIG DIRECTLY")
            self.log("=" * 50)
            gdrive_exists = self.check_gdrive_config_directly(company_id)
            
            # Step 4: Test auto-rename with debugging
            self.log("\n🔄 STEP 4: TEST AUTO-RENAME WITH DEBUG INFO")
            self.log("=" * 50)
            auto_rename_works = self.test_auto_rename_with_debug(company_id)
            
            # Step 5: Analysis
            self.log("\n📊 STEP 5: ANALYSIS")
            self.log("=" * 50)
            
            self.log("🎯 FINDINGS:")
            self.log(f"   User company from token: {self.current_user.get('company')}")
            self.log(f"   Resolved company ID: {company_id}")
            self.log(f"   Google Drive config exists: {gdrive_exists}")
            self.log(f"   Auto-rename works: {auto_rename_works}")
            
            if not auto_rename_works and gdrive_exists:
                self.log("\n🚨 ROOT CAUSE IDENTIFIED:")
                self.log("   Google Drive configuration exists for the resolved company ID")
                self.log("   But auto-rename endpoint still returns 'Google Drive not configured'")
                self.log("   This indicates a bug in the company ID resolution within the auto-rename endpoint")
                self.log("\n💡 RECOMMENDED FIX:")
                self.log("   Check the resolve_company_id function call in the auto-rename endpoint")
                self.log("   Verify that the same company ID resolution logic is being used")
                self.log("   Add debug logging to the auto-rename endpoint to see what company ID it's using")
            elif auto_rename_works:
                self.log("\n✅ ISSUE RESOLVED:")
                self.log("   Auto-rename is now working correctly")
            else:
                self.log("\n❌ ISSUE PERSISTS:")
                self.log("   Google Drive configuration is missing")
                self.log("   Need to configure Google Drive for the company")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Debug test error: {str(e)}", "ERROR")
            return False

def main():
    print("🔄 COMPANY ID RESOLUTION DEBUG TEST STARTED")
    print("=" * 80)
    
    try:
        tester = CompanyIdDebugTester()
        success = tester.run_debug_test()
        
        if success:
            print("\n✅ COMPANY ID DEBUG TEST COMPLETED")
        else:
            print("\n❌ COMPANY ID DEBUG TEST COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
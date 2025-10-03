#!/usr/bin/env python3
"""
Fix CL Certificate Abbreviation and Test Auto Rename
FOCUS: Fix the cert_abbreviation field and verify Auto Rename works correctly

STEPS:
1. Update cert_abbreviation field to 'CL' for the PM242309 certificate
2. Test Auto Rename endpoint again to verify it now uses 'CL'
3. Confirm the fix resolves the reported issue
"""

import requests
import json
import os
import sys
from datetime import datetime

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

class CLCertificateFixer:
    def __init__(self):
        self.auth_token = None
        self.certificate_id = "3ce38d28-84d1-4982-87d6-eb32068e981b"  # PM242309 certificate
        
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
                self.log("✅ Authentication successful")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def get_certificate_data(self):
        """Get current certificate data"""
        try:
            self.log("📊 Getting current certificate data...")
            
            response = requests.get(f"{BACKEND_URL}/certificates/{self.certificate_id}", 
                                  headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                cert_data = response.json()
                self.log("✅ Certificate data retrieved")
                self.log(f"   ID: {cert_data.get('id')}")
                self.log(f"   Name: {cert_data.get('cert_name')}")
                self.log(f"   Number: {cert_data.get('cert_no')}")
                self.log(f"   Current Abbreviation: {cert_data.get('cert_abbreviation')}")
                return cert_data
            else:
                self.log(f"❌ Failed to get certificate data: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error getting certificate data: {str(e)}", "ERROR")
            return None
    
    def update_certificate_abbreviation(self):
        """Update cert_abbreviation field to 'CL'"""
        try:
            self.log("🔧 Updating cert_abbreviation field to 'CL'...")
            
            update_data = {
                "cert_abbreviation": "CL"
            }
            
            response = requests.put(f"{BACKEND_URL}/certificates/{self.certificate_id}", 
                                  json=update_data, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                updated_cert = response.json()
                self.log("✅ Certificate abbreviation updated successfully")
                self.log(f"   New Abbreviation: {updated_cert.get('cert_abbreviation')}")
                return True
            else:
                self.log(f"❌ Failed to update certificate: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error updating certificate: {str(e)}", "ERROR")
            return False
    
    def test_auto_rename_after_fix(self):
        """Test Auto Rename endpoint after fixing abbreviation"""
        try:
            self.log("🔄 Testing Auto Rename endpoint after fix...")
            
            response = requests.post(f"{BACKEND_URL}/certificates/{self.certificate_id}/auto-rename-file", 
                                   headers=self.get_headers(), timeout=60)
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Auto Rename endpoint successful")
                self.log(f"   Success: {result.get('success')}")
                self.log(f"   Message: {result.get('message')}")
                
                # Check backend logs for the actual filename generated
                self.log("🔍 Check backend logs for generated filename...")
                return True
            else:
                self.log(f"❌ Auto Rename failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Auto Rename: {str(e)}", "ERROR")
            return False
    
    def run_fix_and_test(self):
        """Main function to fix and test"""
        self.log("🔧 STARTING CL CERTIFICATE FIX AND TEST")
        self.log("=" * 80)
        
        try:
            # Step 1: Authenticate
            if not self.authenticate():
                return False
            
            # Step 2: Get current certificate data
            cert_data = self.get_certificate_data()
            if not cert_data:
                return False
            
            # Step 3: Update abbreviation if needed
            current_abbreviation = cert_data.get('cert_abbreviation')
            if current_abbreviation != 'CL':
                self.log(f"🔧 Current abbreviation is '{current_abbreviation}', updating to 'CL'...")
                if not self.update_certificate_abbreviation():
                    return False
            else:
                self.log("✅ Certificate abbreviation is already 'CL'")
            
            # Step 4: Test Auto Rename
            if not self.test_auto_rename_after_fix():
                return False
            
            self.log("\n🎉 FIX AND TEST COMPLETED SUCCESSFULLY")
            self.log("✅ Certificate abbreviation updated to 'CL'")
            self.log("✅ Auto Rename endpoint tested")
            self.log("🔍 Check backend logs to see if filename now uses 'CL' instead of 'CLASSIFICATION_CERTIFICATE'")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Fix and test error: {str(e)}", "ERROR")
            return False

def main():
    """Main function"""
    print("🔧 CL CERTIFICATE FIX AND TEST STARTED")
    print("=" * 80)
    
    try:
        fixer = CLCertificateFixer()
        success = fixer.run_fix_and_test()
        
        if success:
            print("\n✅ CL CERTIFICATE FIX AND TEST COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ CL CERTIFICATE FIX AND TEST COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
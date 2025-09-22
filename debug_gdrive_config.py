#!/usr/bin/env python3
"""
Debug Google Drive Configuration
Check what Google Drive configurations exist and which one should be used for file viewing
"""

import requests
import json
import os
import sys
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

class GDriveConfigDebugger:
    def __init__(self):
        self.token = None
        self.user_info = None
        
    def authenticate(self):
        """Authenticate with admin1 credentials"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                print(f"✅ Authenticated as {self.user_info['username']} ({self.user_info.get('role', 'Unknown')})")
                print(f"   Company: {self.user_info.get('company', 'None')}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def check_system_gdrive_config(self):
        """Check system Google Drive configuration"""
        print("\n🔍 SYSTEM GOOGLE DRIVE CONFIGURATION:")
        try:
            # Check status
            status_response = requests.get(f"{API_BASE}/gdrive/status", headers=self.get_headers())
            print(f"Status endpoint: {status_response.status_code}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"  Status: {status_data.get('status')}")
                print(f"  Message: {status_data.get('message')}")
            
            # Check config
            config_response = requests.get(f"{API_BASE}/gdrive/config", headers=self.get_headers())
            print(f"Config endpoint: {config_response.status_code}")
            if config_response.status_code == 200:
                config_data = config_response.json()
                print(f"  Configured: {config_data.get('configured')}")
                print(f"  Auth Method: {config_data.get('auth_method')}")
                print(f"  Apps Script URL: {config_data.get('apps_script_url', 'Not set')}")
                print(f"  Folder ID: {config_data.get('folder_id', 'Not set')}")
            
        except Exception as e:
            print(f"❌ Error checking system config: {e}")
    
    def check_company_gdrive_config(self):
        """Check company-specific Google Drive configuration"""
        print("\n🔍 COMPANY GOOGLE DRIVE CONFIGURATION:")
        
        user_company = self.user_info.get('company')
        if not user_company:
            print("❌ User has no company assigned")
            return
        
        print(f"User company ID: {user_company}")
        
        try:
            # Check company config
            config_response = requests.get(f"{API_BASE}/companies/{user_company}/gdrive/config", headers=self.get_headers())
            print(f"Company config endpoint: {config_response.status_code}")
            if config_response.status_code == 200:
                config_data = config_response.json()
                print(f"  Success: {config_data.get('success')}")
                if config_data.get('success'):
                    config = config_data.get('config', {})
                    print(f"  Web App URL: {config.get('web_app_url', 'Not set')}")
                    print(f"  Folder ID: {config.get('folder_id', 'Not set')}")
                else:
                    print(f"  Message: {config_data.get('message')}")
            else:
                print(f"  Error: {config_response.text}")
            
            # Check company status
            status_response = requests.post(f"{API_BASE}/companies/{user_company}/gdrive/status", headers=self.get_headers())
            print(f"Company status endpoint: {status_response.status_code}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"  Status: {status_data.get('status')}")
                print(f"  Configured: {status_data.get('configured')}")
            else:
                print(f"  Status error: {status_response.text}")
            
        except Exception as e:
            print(f"❌ Error checking company config: {e}")
    
    def check_all_companies(self):
        """Check all companies for Google Drive configurations"""
        print("\n🔍 ALL COMPANIES:")
        try:
            response = requests.get(f"{API_BASE}/companies", headers=self.get_headers())
            if response.status_code == 200:
                companies = response.json()
                print(f"Found {len(companies)} companies:")
                
                for company in companies:
                    company_id = company.get('id')
                    company_name = company.get('name_en') or company.get('name') or 'Unknown'
                    print(f"\n  Company: {company_name} (ID: {company_id})")
                    
                    # Check if this company has Google Drive config
                    try:
                        config_response = requests.get(f"{API_BASE}/companies/{company_id}/gdrive/config", headers=self.get_headers())
                        if config_response.status_code == 200:
                            config_data = config_response.json()
                            if config_data.get('success'):
                                config = config_data.get('config', {})
                                print(f"    ✅ Has Google Drive config")
                                print(f"    Web App URL: {config.get('web_app_url', 'Not set')[:50]}...")
                                print(f"    Folder ID: {config.get('folder_id', 'Not set')}")
                            else:
                                print(f"    ❌ No Google Drive config")
                        else:
                            print(f"    ❌ Config check failed: {config_response.status_code}")
                    except Exception as e:
                        print(f"    ❌ Error checking config: {e}")
            else:
                print(f"❌ Failed to get companies: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error checking companies: {e}")
    
    def test_file_view_with_company_config(self):
        """Test if we can modify the file view to work with company config"""
        print("\n🔍 FILE VIEW ENDPOINT ANALYSIS:")
        
        user_company = self.user_info.get('company')
        if not user_company:
            print("❌ Cannot test - user has no company")
            return
        
        # Test the current file view endpoint (should fail)
        test_file_id = "1GxhDHWH0GucMCB2ZAkf9hz55zICbTbki"
        
        try:
            response = requests.get(f"{API_BASE}/gdrive/file/{test_file_id}/view", headers=self.get_headers())
            print(f"Current file view endpoint: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code != 200:
                print("\n💡 ISSUE IDENTIFIED:")
                print("The file view endpoint only checks for system Google Drive config,")
                print("but certificate uploads use company-specific Google Drive config.")
                print("This is why file viewing fails while uploads work.")
                
                print("\n🔧 SOLUTION NEEDED:")
                print("The file view endpoint should be updated to:")
                print("1. First check for company-specific Google Drive config")
                print("2. Fallback to system Google Drive config if no company config")
                print("3. This would match the behavior of certificate upload endpoints")
            
        except Exception as e:
            print(f"❌ Error testing file view: {e}")
    
    def run_debug(self):
        """Run all debug checks"""
        print("🚀 Starting Google Drive Configuration Debug")
        print("=" * 80)
        
        if not self.authenticate():
            return False
        
        self.check_system_gdrive_config()
        self.check_company_gdrive_config()
        self.check_all_companies()
        self.test_file_view_with_company_config()
        
        print("\n" + "=" * 80)
        print("🎯 DEBUG COMPLETE")
        
        return True

def main():
    """Main debug execution"""
    debugger = GDriveConfigDebugger()
    debugger.run_debug()

if __name__ == "__main__":
    main()
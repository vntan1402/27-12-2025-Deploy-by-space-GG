#!/usr/bin/env python3
"""
Debug Apps Script Response for Passport Upload
Focus on understanding why Company Apps Script file upload is failing
"""

import requests
import json
import os
import base64
import time
import sys
sys.path.append('/app/backend')
from mongodb_database import mongo_db
import asyncio

# Configuration
BACKEND_URL = "https://smartcrew.preview.emergentagent.com/api"
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"
PASSPORT_FILE = "/app/3_2O_THUONG_PP.pdf"

class AppsScriptDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.company_id = None
        
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate(self):
        """Authenticate with backend"""
        try:
            self.log("🔐 Authenticating...")
            
            login_data = {
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                user_info = data.get("user")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                
                self.log(f"✅ Authentication successful")
                self.log(f"   User: {user_info.get('username')} ({user_info.get('role')})")
                self.log(f"   Company: {user_info.get('company')}")
                
                # Get company ID for database lookup
                self.company_id = user_info.get('company')
                self.log(f"   Company ID for lookup: {self.company_id}")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {e}", "ERROR")
            return False
    
    async def get_company_apps_script_config(self):
        """Get Company Apps Script configuration from database"""
        try:
            self.log("🔍 Getting Company Apps Script configuration...")
            self.log(f"   Looking for company_id: {self.company_id}")
            
            # First, let's see what's in the company_gdrive_config collection
            try:
                all_configs = await mongo_db.find_all("company_gdrive_config", {})
                if all_configs is None:
                    all_configs = []
                self.log(f"   Found {len(all_configs)} company configs in database")
            except Exception as e:
                self.log(f"   Error getting all configs: {e}")
                all_configs = []
            
            for config in all_configs:
                self.log(f"   Config: company_id={config.get('company_id')}, has_url={bool(config.get('company_apps_script_url') or config.get('web_app_url'))}")
            
            # Look for company configuration
            gdrive_config = await mongo_db.find_one(
                "company_gdrive_config",
                {"company_id": self.company_id}
            )
            
            if gdrive_config:
                company_apps_script_url = gdrive_config.get("company_apps_script_url") or gdrive_config.get("web_app_url")
                parent_folder_id = gdrive_config.get("parent_folder_id") or gdrive_config.get("folder_id")
                
                self.log(f"✅ Company Apps Script URL: {company_apps_script_url}")
                self.log(f"✅ Parent Folder ID: {parent_folder_id}")
                
                return company_apps_script_url, parent_folder_id
            else:
                self.log("❌ No company Google Drive configuration found", "ERROR")
                
                # Try to find by company name instead
                self.log("   Trying to find by company name...")
                gdrive_config_by_name = await mongo_db.find_one(
                    "company_gdrive_config",
                    {"company_name": self.company_id}
                )
                
                if gdrive_config_by_name:
                    company_apps_script_url = gdrive_config_by_name.get("company_apps_script_url") or gdrive_config_by_name.get("web_app_url")
                    parent_folder_id = gdrive_config_by_name.get("parent_folder_id") or gdrive_config_by_name.get("folder_id")
                    
                    self.log(f"✅ Found by name - Company Apps Script URL: {company_apps_script_url}")
                    self.log(f"✅ Found by name - Parent Folder ID: {parent_folder_id}")
                    
                    return company_apps_script_url, parent_folder_id
                
                return None, None
                
        except Exception as e:
            self.log(f"❌ Error getting configuration: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return None, None
    
    async def test_company_apps_script_directly(self, apps_script_url, parent_folder_id):
        """Test Company Apps Script directly with passport file"""
        try:
            self.log("🧪 Testing Company Apps Script directly...")
            
            # Read passport file
            with open(PASSPORT_FILE, 'rb') as f:
                file_content = f.read()
            
            # Prepare payload exactly as dual_apps_script_manager does
            payload = {
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': parent_folder_id,
                'ship_name': 'BROTHER 36',
                'category': 'Crew Records',
                'filename': '3_2O_THUONG_PP.pdf',
                'file_content': base64.b64encode(file_content).decode('utf-8'),
                'content_type': 'application/pdf'
            }
            
            self.log(f"📤 Calling Company Apps Script...")
            self.log(f"   URL: {apps_script_url}")
            self.log(f"   Action: {payload['action']}")
            self.log(f"   Parent Folder ID: {payload['parent_folder_id']}")
            self.log(f"   Ship Name: {payload['ship_name']}")
            self.log(f"   Category: {payload['category']}")
            self.log(f"   Filename: {payload['filename']}")
            self.log(f"   Content Type: {payload['content_type']}")
            self.log(f"   File Size: {len(file_content):,} bytes")
            
            # Make the call
            start_time = time.time()
            response = requests.post(
                apps_script_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Apps Script response time: {processing_time:.1f} seconds")
            self.log(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.log("✅ Apps Script responded successfully")
                    self.log(f"📋 Response data:")
                    
                    # Analyze response structure
                    for key, value in result.items():
                        if isinstance(value, (str, int, bool, float)):
                            self.log(f"   {key}: {value}")
                        else:
                            self.log(f"   {key}: {type(value).__name__} ({len(str(value))} chars)")
                    
                    # Check for success indicators
                    success = result.get('success', False)
                    message = result.get('message', '')
                    error = result.get('error', '')
                    file_id = result.get('file_id', '')
                    
                    self.log(f"🎯 Key indicators:")
                    self.log(f"   Success: {success}")
                    self.log(f"   Message: {message}")
                    self.log(f"   Error: {error}")
                    self.log(f"   File ID: {file_id}")
                    
                    if success and file_id:
                        self.log("✅ File upload appears successful", "SUCCESS")
                        return True
                    else:
                        self.log("❌ File upload failed or incomplete", "ERROR")
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {e}", "ERROR")
                    self.log(f"   Raw response: {response.text[:500]}...")
                    return False
            else:
                self.log(f"❌ Apps Script HTTP error: {response.status_code}", "ERROR")
                self.log(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Apps Script: {e}", "ERROR")
            return False
    
    async def run_debug_test(self):
        """Run comprehensive debug test"""
        self.log("🚀 Starting Apps Script Debug Test")
        self.log("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            self.log("❌ Authentication failed", "ERROR")
            return False
        
        # Step 2: Get Apps Script configuration
        apps_script_url, parent_folder_id = await self.get_company_apps_script_config()
        if not apps_script_url or not parent_folder_id:
            self.log("❌ Apps Script configuration not found", "ERROR")
            return False
        
        # Step 3: Test Apps Script directly
        success = await self.test_company_apps_script_directly(apps_script_url, parent_folder_id)
        
        self.log("=" * 60)
        if success:
            self.log("✅ APPS SCRIPT DEBUG TEST COMPLETED SUCCESSFULLY", "SUCCESS")
        else:
            self.log("❌ APPS SCRIPT DEBUG TEST FAILED", "ERROR")
        
        return success

async def main():
    """Main debug execution"""
    print("🔍 Apps Script Debug Test for Passport Upload")
    print("📄 Testing with REAL passport file: 3. 2O THUONG - PP.pdf")
    print("🎯 Focus: Debug Company Apps Script file upload failure")
    print("=" * 80)
    
    debugger = AppsScriptDebugger()
    success = await debugger.run_debug_test()
    
    print("=" * 80)
    if success:
        print("✅ DEBUG COMPLETED - Apps Script working")
    else:
        print("❌ DEBUG COMPLETED - Apps Script issue confirmed")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
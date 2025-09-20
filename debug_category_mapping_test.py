#!/usr/bin/env python3
"""
Debug Category Mapping Test
Specifically testing the "Target folder not found for category: other_documents" error
"""

import requests
import json
import tempfile
import os
from datetime import datetime

class CategoryMappingDebugTester:
    def __init__(self, base_url="https://ship-cert-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.apps_script_url = "https://script.google.com/macros/s/AKfycbwphwgJwjyW4V-Y2y0J4uIa40zZwybm7s9maqNemi04EawcOhxRX99rbSXGWxk_D6o/exec"
        self.folder_id = "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG"

    def login(self):
        """Login and get token"""
        response = requests.post(f"{self.api_url}/auth/login", json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('access_token')
            print(f"✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False

    def test_apps_script_folder_creation(self):
        """Test Apps Script folder creation and examine returned structure"""
        print("\n🔍 TESTING APPS SCRIPT FOLDER CREATION")
        print("=" * 60)
        
        try:
            response = requests.post(self.apps_script_url, json={
                "action": "create_folder_structure",
                "folder_id": self.folder_id,
                "ship_name": "Debug Test Ship"
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    subfolder_ids = result.get('subfolder_ids', {})
                    print(f"✅ Folder creation successful")
                    print(f"📁 Subfolder IDs returned:")
                    for folder_name, folder_id in subfolder_ids.items():
                        print(f"   '{folder_name}' -> {folder_id}")
                    
                    # Check specifically for "Other Documents"
                    if "Other Documents" in subfolder_ids:
                        print(f"✅ 'Other Documents' folder found: {subfolder_ids['Other Documents']}")
                    else:
                        print(f"❌ 'Other Documents' folder NOT found")
                        print(f"   Available folders: {list(subfolder_ids.keys())}")
                    
                    return subfolder_ids
                else:
                    print(f"❌ Apps Script returned success=false: {result.get('message')}")
            else:
                print(f"❌ Apps Script HTTP error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Apps Script request failed: {str(e)}")
        
        return {}

    def test_backend_category_mapping(self):
        """Test backend category mapping logic"""
        print("\n🗂️ TESTING BACKEND CATEGORY MAPPING")
        print("=" * 60)
        
        # Test the category mapping that happens in upload_file_to_category_folder
        category_folders = {
            "certificates": "Certificates",
            "test_reports": "Test Reports",
            "survey_reports": "Survey Reports", 
            "drawings_manuals": "Drawings & Manuals",
            "other_documents": "Other Documents"
        }
        
        print("Backend category mapping:")
        for backend_category, folder_name in category_folders.items():
            print(f"   '{backend_category}' -> '{folder_name}'")
        
        # Test the specific problematic category
        test_category = "other_documents"
        expected_folder = category_folders.get(test_category, "Other Documents")
        print(f"\n🎯 Testing problematic category:")
        print(f"   Backend category: '{test_category}'")
        print(f"   Expected folder name: '{expected_folder}'")
        
        return category_folders

    def test_multi_file_upload_with_debug(self):
        """Test multi-file upload with detailed debugging"""
        print("\n📁 TESTING MULTI-FILE UPLOAD WITH DEBUG")
        print("=" * 60)
        
        # Get ships first
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{self.api_url}/ships", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Cannot get ships: {response.status_code}")
            return False
        
        ships = response.json()
        if not ships:
            print(f"❌ No ships available")
            return False
        
        ship_id = ships[0]['id']
        ship_name = ships[0]['name']
        print(f"📋 Using ship: {ship_name} (ID: {ship_id})")
        
        # Create a test file that should be classified as "other_documents"
        test_content = "This is a test document that should be classified as other_documents category."
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(test_content)
        temp_file.close()
        
        try:
            # Upload the file
            with open(temp_file.name, 'rb') as f:
                files = [('files', ('test_other_document.txt', f, 'text/plain'))]
                data = {
                    'ship_id': ship_id,
                    'ship_name': ship_name
                }
                
                print(f"📤 Uploading test file: test_other_document.txt")
                response = requests.post(
                    f"{self.api_url}/certificates/upload-multi-files",
                    data=data,
                    files=files,
                    headers=headers,
                    timeout=60
                )
                
                print(f"📊 Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Upload successful")
                    print(f"   Total files: {result.get('total_files')}")
                    print(f"   Successful uploads: {result.get('successful_uploads')}")
                    
                    # Examine results in detail
                    if 'results' in result:
                        for file_result in result['results']:
                            filename = file_result.get('filename')
                            category = file_result.get('category')
                            errors = file_result.get('errors', [])
                            
                            print(f"\n📄 File: {filename}")
                            print(f"   Category: {category}")
                            print(f"   Errors: {len(errors)}")
                            
                            for error in errors:
                                print(f"   ❌ Error: {error}")
                                if "Target folder not found" in error:
                                    print(f"   🎯 FOUND THE TARGET ERROR!")
                    
                    return True
                else:
                    print(f"❌ Upload failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"   Error: {error_data.get('detail', response.text[:200])}")
                    except:
                        print(f"   Error: {response.text[:200]}")
        
        except Exception as e:
            print(f"❌ Upload error: {str(e)}")
        finally:
            # Clean up
            os.unlink(temp_file.name)
        
        return False

    def test_company_gdrive_config(self):
        """Test company Google Drive configuration"""
        print("\n⚙️ TESTING COMPANY GDRIVE CONFIG")
        print("=" * 60)
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Get companies first
        response = requests.get(f"{self.api_url}/companies", headers=headers)
        if response.status_code != 200:
            print(f"❌ Cannot get companies: {response.status_code}")
            return None
        
        companies = response.json()
        if not companies:
            print(f"❌ No companies available")
            return None
        
        company_id = companies[0]['id']
        company_name = companies[0].get('name_en', companies[0].get('name_vn', 'Unknown'))
        print(f"🏢 Using company: {company_name} (ID: {company_id})")
        
        # Get company Google Drive config
        response = requests.get(f"{self.api_url}/companies/{company_id}/gdrive/config", headers=headers)
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Company GDrive config retrieved")
            print(f"   Configured: {config.get('configured')}")
            print(f"   Auth method: {config.get('auth_method')}")
            print(f"   Folder ID: {config.get('folder_id')}")
            print(f"   Web App URL: {config.get('web_app_url', 'Not set')}")
            return config
        else:
            print(f"❌ Cannot get company GDrive config: {response.status_code}")
        
        return None

    def run_debug_test(self):
        """Run comprehensive debug test"""
        print("🔍 CATEGORY MAPPING DEBUG TEST")
        print("=" * 80)
        print(f"Apps Script URL: {self.apps_script_url}")
        print(f"Folder ID: {self.folder_id}")
        print("=" * 80)
        
        # Step 1: Login
        if not self.login():
            return False
        
        # Step 2: Test Apps Script folder creation
        subfolder_ids = self.test_apps_script_folder_creation()
        
        # Step 3: Test backend category mapping
        category_mapping = self.test_backend_category_mapping()
        
        # Step 4: Test company Google Drive config
        company_config = self.test_company_gdrive_config()
        
        # Step 5: Test multi-file upload with debug
        upload_success = self.test_multi_file_upload_with_debug()
        
        # Step 6: Analysis
        print("\n🔬 ANALYSIS")
        print("=" * 60)
        
        if subfolder_ids and category_mapping:
            print("Checking folder name matching:")
            
            for backend_category, expected_folder in category_mapping.items():
                if expected_folder in subfolder_ids:
                    print(f"   ✅ '{backend_category}' -> '{expected_folder}' -> FOUND")
                else:
                    print(f"   ❌ '{backend_category}' -> '{expected_folder}' -> NOT FOUND")
                    print(f"      Available: {list(subfolder_ids.keys())}")
            
            # Check for exact match issues
            if "Other Documents" in subfolder_ids:
                other_docs_id = subfolder_ids["Other Documents"]
                print(f"\n🎯 'Other Documents' folder analysis:")
                print(f"   Folder ID: {other_docs_id}")
                print(f"   Key in subfolder_ids: 'Other Documents'")
                print(f"   Backend expects: 'Other Documents'")
                print(f"   Should match: YES")
        
        return True

def main():
    tester = CategoryMappingDebugTester()
    success = tester.run_debug_test()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
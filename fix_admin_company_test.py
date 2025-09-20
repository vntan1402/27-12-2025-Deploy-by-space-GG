#!/usr/bin/env python3
"""
Fix Admin Company Association and Test Multi-File Upload
"""

import requests
import json
import tempfile
import os

class AdminCompanyFixTester:
    def __init__(self, base_url="https://certmaster-ship.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_user_id = None

    def login(self):
        """Login and get token"""
        response = requests.post(f"{self.api_url}/auth/login", json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('access_token')
            user_info = data.get('user', {})
            self.admin_user_id = user_info.get('id')
            
            print(f"✅ Login successful")
            print(f"   User: {user_info.get('full_name')}")
            print(f"   Role: {user_info.get('role')}")
            print(f"   Company: {user_info.get('company')}")
            print(f"   User ID: {self.admin_user_id}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False

    def get_companies(self):
        """Get available companies"""
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{self.api_url}/companies", headers=headers)
        
        if response.status_code == 200:
            companies = response.json()
            print(f"✅ Found {len(companies)} companies:")
            for company in companies:
                print(f"   - {company.get('name_en', company.get('name_vn'))} (ID: {company['id']})")
            return companies
        else:
            print(f"❌ Cannot get companies: {response.status_code}")
            return []

    def update_admin_company(self, company_name):
        """Update admin user to associate with a company"""
        headers = {'Authorization': f'Bearer {self.token}'}
        
        update_data = {
            'company': company_name
        }
        
        response = requests.put(
            f"{self.api_url}/users/{self.admin_user_id}",
            json=update_data,
            headers=headers
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Admin user updated successfully")
            print(f"   Company: {user_data.get('company')}")
            return True
        else:
            print(f"❌ Failed to update admin user: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail')}")
            except:
                print(f"   Error: {response.text[:200]}")
            return False

    def test_multi_file_upload_after_fix(self):
        """Test multi-file upload after fixing company association"""
        print("\n📁 TESTING MULTI-FILE UPLOAD AFTER FIX")
        print("=" * 60)
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Get ships
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
        
        # Create test files for different categories
        test_files = [
            ("test_certificate.txt", "This is a test certificate document.", "certificates"),
            ("test_other_document.txt", "This is a test other document.", "other_documents"),
            ("test_inspection_report.txt", "This is a test inspection report.", "test_reports")
        ]
        
        temp_files = []
        
        try:
            # Create temporary files
            for filename, content, expected_category in test_files:
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                temp_file.write(content)
                temp_file.close()
                temp_files.append((temp_file.name, filename, expected_category))
            
            # Prepare files for upload
            files = []
            for temp_path, filename, _ in temp_files:
                files.append(('files', (filename, open(temp_path, 'rb'), 'text/plain')))
            
            data = {
                'ship_id': ship_id,
                'ship_name': ship_name
            }
            
            print(f"📤 Uploading {len(files)} test files...")
            response = requests.post(
                f"{self.api_url}/certificates/upload-multi-files",
                data=data,
                files=files,
                headers=headers,
                timeout=60
            )
            
            # Close file handles
            for file_tuple in files:
                file_tuple[1][1].close()
            
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Upload successful!")
                print(f"   Total files: {result.get('total_files')}")
                print(f"   Successful uploads: {result.get('successful_uploads')}")
                print(f"   Certificates created: {result.get('certificates_created')}")
                
                # Examine results in detail
                if 'results' in result:
                    for i, file_result in enumerate(result['results']):
                        filename = file_result.get('filename')
                        category = file_result.get('category')
                        status = file_result.get('status')
                        errors = file_result.get('errors', [])
                        google_drive_uploaded = file_result.get('google_drive_uploaded', False)
                        
                        expected_category = temp_files[i][2]
                        
                        print(f"\n📄 File {i+1}: {filename}")
                        print(f"   Expected category: {expected_category}")
                        print(f"   Actual category: {category}")
                        print(f"   Status: {status}")
                        print(f"   Google Drive uploaded: {google_drive_uploaded}")
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
            # Clean up temporary files
            for temp_path, _, _ in temp_files:
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        return False

    def run_fix_and_test(self):
        """Run the complete fix and test process"""
        print("🔧 ADMIN COMPANY FIX AND MULTI-FILE UPLOAD TEST")
        print("=" * 80)
        
        # Step 1: Login
        if not self.login():
            return False
        
        # Step 2: Get companies
        companies = self.get_companies()
        if not companies:
            return False
        
        # Step 3: Update admin user with company (use first available company)
        company_name = companies[0].get('name_en', companies[0].get('name_vn'))
        print(f"\n🔧 Updating admin user with company: {company_name}")
        
        if not self.update_admin_company(company_name):
            return False
        
        # Step 4: Re-login to get updated token with company info
        print(f"\n🔄 Re-logging in to get updated user info...")
        if not self.login():
            return False
        
        # Step 5: Test multi-file upload
        success = self.test_multi_file_upload_after_fix()
        
        return success

def main():
    tester = AdminCompanyFixTester()
    success = tester.run_fix_and_test()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
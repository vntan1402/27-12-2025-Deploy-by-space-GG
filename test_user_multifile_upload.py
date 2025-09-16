#!/usr/bin/env python3
"""
Create Test User with Company and Test Multi-File Upload
"""

import requests
import json
import tempfile
import os
import time

class TestUserMultiFileUploadTester:
    def __init__(self, base_url="https://ship-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.test_token = None
        self.test_user_id = None

    def admin_login(self):
        """Login as admin to create test user"""
        response = requests.post(f"{self.api_url}/auth/login", json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data.get('access_token')
            print(f"✅ Admin login successful")
            return True
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return False

    def create_test_user(self):
        """Create a test user with company association"""
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Get companies first
        response = requests.get(f"{self.api_url}/companies", headers=headers)
        if response.status_code != 200:
            print(f"❌ Cannot get companies: {response.status_code}")
            return False
        
        companies = response.json()
        if not companies:
            print(f"❌ No companies available")
            return False
        
        company_name = companies[0].get('name_en', companies[0].get('name_vn'))
        print(f"🏢 Using company: {company_name}")
        
        # Create test user
        test_username = f"test_multifile_{int(time.time())}"
        user_data = {
            'username': test_username,
            'password': 'TestPass123!',
            'email': f'{test_username}@test.com',
            'full_name': 'Test Multi-File User',
            'role': 'editor',  # Editor role can upload files
            'department': 'technical',
            'company': company_name,
            'zalo': '0901234567',
            'gmail': f'{test_username}@gmail.com'
        }
        
        response = requests.post(f"{self.api_url}/users", json=user_data, headers=headers)
        
        if response.status_code == 200:
            user_info = response.json()
            self.test_user_id = user_info.get('id')
            print(f"✅ Test user created: {test_username}")
            print(f"   Company: {user_info.get('company')}")
            print(f"   Role: {user_info.get('role')}")
            return test_username
        else:
            print(f"❌ Failed to create test user: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail')}")
            except:
                print(f"   Error: {response.text[:200]}")
            return None

    def test_user_login(self, username):
        """Login as test user"""
        response = requests.post(f"{self.api_url}/auth/login", json={
            'username': username,
            'password': 'TestPass123!'
        })
        
        if response.status_code == 200:
            data = response.json()
            self.test_token = data.get('access_token')
            user_info = data.get('user', {})
            print(f"✅ Test user login successful")
            print(f"   User: {user_info.get('full_name')}")
            print(f"   Company: {user_info.get('company')}")
            print(f"   Role: {user_info.get('role')}")
            return True
        else:
            print(f"❌ Test user login failed: {response.status_code}")
            return False

    def test_multi_file_upload(self):
        """Test multi-file upload with test user"""
        print("\n📁 TESTING MULTI-FILE UPLOAD WITH TEST USER")
        print("=" * 60)
        
        headers = {'Authorization': f'Bearer {self.test_token}'}
        
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
        
        # Create test files that should trigger different categories
        test_files = [
            ("certificate_document.txt", "This is a safety management certificate for the vessel. Certificate number: SMC-2024-001. Valid until 2025-12-31.", "certificates"),
            ("other_document.txt", "This is a general document that doesn't fit other categories. Contains miscellaneous information.", "other_documents"),
            ("inspection_report.txt", "This is an inspection report. Inspection conducted on 2024-01-15. All systems checked.", "test_reports"),
            ("survey_report.txt", "This is a survey report. Annual survey completed successfully. No deficiencies found.", "survey_reports"),
            ("manual_document.txt", "This is a technical manual. Operating procedures for main engine. Drawing reference: ME-001.", "drawings_manuals")
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
            print("Files to upload:")
            for i, (_, filename, expected_category) in enumerate(temp_files):
                print(f"   {i+1}. {filename} (expected: {expected_category})")
            
            response = requests.post(
                f"{self.api_url}/certificates/upload-multi-files",
                data=data,
                files=files,
                headers=headers,
                timeout=120  # Longer timeout for multiple files
            )
            
            # Close file handles
            for file_tuple in files:
                file_tuple[1][1].close()
            
            print(f"\n📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Upload completed!")
                print(f"   Total files: {result.get('total_files')}")
                print(f"   Successful uploads: {result.get('successful_uploads')}")
                print(f"   Certificates created: {result.get('certificates_created')}")
                
                # Detailed analysis of results
                if 'results' in result:
                    print(f"\n📋 DETAILED RESULTS:")
                    success_count = 0
                    error_count = 0
                    target_folder_errors = 0
                    
                    for i, file_result in enumerate(result['results']):
                        filename = file_result.get('filename')
                        category = file_result.get('category')
                        status = file_result.get('status')
                        errors = file_result.get('errors', [])
                        google_drive_uploaded = file_result.get('google_drive_uploaded', False)
                        certificate_created = file_result.get('certificate_created', False)
                        
                        expected_category = temp_files[i][2]
                        
                        print(f"\n📄 File {i+1}: {filename}")
                        print(f"   Expected category: {expected_category}")
                        print(f"   AI classified as: {category}")
                        print(f"   Status: {status}")
                        print(f"   Google Drive uploaded: {google_drive_uploaded}")
                        print(f"   Certificate created: {certificate_created}")
                        
                        if errors:
                            error_count += 1
                            print(f"   ❌ Errors ({len(errors)}):")
                            for error in errors:
                                print(f"      - {error}")
                                if "Target folder not found" in error:
                                    target_folder_errors += 1
                                    print(f"      🎯 TARGET FOLDER ERROR FOUND!")
                        else:
                            success_count += 1
                            print(f"   ✅ No errors")
                    
                    print(f"\n📊 SUMMARY:")
                    print(f"   Successful files: {success_count}")
                    print(f"   Files with errors: {error_count}")
                    print(f"   Target folder errors: {target_folder_errors}")
                    
                    if target_folder_errors > 0:
                        print(f"\n🎯 TARGET FOLDER ERROR REPRODUCED!")
                        print(f"   This confirms the 'Target folder not found for category: other_documents' issue")
                    else:
                        print(f"\n✅ No target folder errors found - issue may be resolved")
                
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', response.text[:500])}")
                except:
                    print(f"   Error: {response.text[:500]}")
        
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

    def run_comprehensive_test(self):
        """Run comprehensive test with user creation and multi-file upload"""
        print("🧪 COMPREHENSIVE MULTI-FILE UPLOAD TEST")
        print("=" * 80)
        
        # Step 1: Admin login
        if not self.admin_login():
            return False
        
        # Step 2: Create test user with company
        test_username = self.create_test_user()
        if not test_username:
            return False
        
        # Step 3: Login as test user
        if not self.test_user_login(test_username):
            return False
        
        # Step 4: Test multi-file upload
        success = self.test_multi_file_upload()
        
        # Step 5: Cleanup (delete test user)
        if self.test_user_id:
            print(f"\n🧹 Cleaning up test user...")
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = requests.delete(f"{self.api_url}/users/{self.test_user_id}", headers=headers)
            if response.status_code == 200:
                print(f"✅ Test user deleted")
            else:
                print(f"⚠️ Could not delete test user: {response.status_code}")
        
        return success

def main():
    tester = TestUserMultiFileUploadTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
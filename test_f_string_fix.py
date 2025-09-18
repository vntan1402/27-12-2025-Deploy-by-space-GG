#!/usr/bin/env python3
"""
Test F-String Fix for Multi-File Upload
Creates a test user with company association and tests the multi-file upload
"""

import requests
import json
import sys
import time
import tempfile
import os
from datetime import datetime

class FStringFixTester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.test_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}: FAILED")
            if details:
                print(f"   {details}")
        return success

    def test_admin_login(self):
        """Test admin login"""
        print(f"\n🔐 Testing Admin Authentication")
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                
                return self.log_test(
                    "Admin Login", 
                    True, 
                    f"Admin authenticated successfully"
                )
            else:
                return self.log_test("Admin Login", False, f"Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("Admin Login", False, f"Exception: {str(e)}")

    def create_test_user_with_company(self):
        """Create a test user with company association"""
        print(f"\n👤 Creating Test User with Company Association")
        
        if not self.admin_token:
            return self.log_test("Create Test User", False, "No admin token")
        
        try:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            
            # First, get companies to associate with
            companies_response = requests.get(f"{self.api_url}/companies", headers=headers, timeout=30)
            if companies_response.status_code != 200:
                return self.log_test("Create Test User", False, "Failed to get companies")
            
            companies = companies_response.json()
            if not companies:
                return self.log_test("Create Test User", False, "No companies available")
            
            company_name = companies[0].get('name_en', companies[0].get('name_vn', 'Test Company'))
            
            # Create test user
            timestamp = int(time.time())
            user_data = {
                "username": f"test_multifile_{timestamp}",
                "email": f"test_multifile_{timestamp}@example.com",
                "password": "TestPass123!",
                "full_name": f"Test Multi-File User {timestamp}",
                "role": "editor",
                "department": "technical",
                "company": company_name,
                "zalo": f"090{timestamp % 10000000:07d}"
            }
            
            response = requests.post(
                f"{self.api_url}/users",
                json=user_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                user = response.json()
                self.test_user_id = user.get('id')
                
                # Now login as the test user
                login_response = requests.post(
                    f"{self.api_url}/auth/login",
                    json={"username": user_data["username"], "password": user_data["password"]},
                    timeout=30
                )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.test_token = login_data.get('access_token')
                    
                    return self.log_test(
                        "Create Test User", 
                        True, 
                        f"User: {user_data['username']}, Company: {company_name}"
                    )
                else:
                    return self.log_test("Create Test User", False, "Failed to login as test user")
            else:
                return self.log_test("Create Test User", False, f"Status: {response.status_code}, Error: {response.text}")
                
        except Exception as e:
            return self.log_test("Create Test User", False, f"Exception: {str(e)}")

    def download_brother36_pdf(self):
        """Download the BROTHER 36 IAPP certificate PDF for testing"""
        print(f"\n📥 Downloading BROTHER 36 IAPP Certificate PDF")
        
        # URL from the review request context
        pdf_url = "https://shipmanage.preview.emergentagent.com/uploads/certificates/BROTHER%2036%20-%20IAPP%20Certificate.pdf"
        
        try:
            response = requests.get(pdf_url, timeout=60)
            
            if response.status_code == 200:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name
                
                file_size = len(response.content)
                return self.log_test(
                    "Download BROTHER 36 PDF", 
                    True, 
                    f"Size: {file_size:,} bytes"
                ), temp_file_path, file_size
            else:
                return self.log_test("Download BROTHER 36 PDF", False, f"Status: {response.status_code}"), None, 0
                
        except Exception as e:
            return self.log_test("Download BROTHER 36 PDF", False, f"Exception: {str(e)}"), None, 0

    def test_multi_file_upload_f_string_fix(self, pdf_path, file_size):
        """Test the multi-file upload endpoint focusing on f-string formatting fix"""
        print(f"\n🚀 Testing Multi-File Upload F-String Fix")
        
        if not self.test_token:
            return self.log_test("Multi-File Upload F-String Fix", False, "No test user token")
        
        if not pdf_path or not os.path.exists(pdf_path):
            return self.log_test("Multi-File Upload F-String Fix", False, "PDF file not available")
        
        try:
            headers = {'Authorization': f'Bearer {self.test_token}'}
            
            # Prepare file for upload
            with open(pdf_path, 'rb') as pdf_file:
                files = {
                    'files': ('BROTHER 36 - IAPP Certificate.pdf', pdf_file, 'application/pdf')
                }
                
                print(f"   📤 Uploading BROTHER 36 IAPP Certificate PDF ({file_size:,} bytes)")
                
                response = requests.post(
                    f"{self.api_url}/certificates/upload-multi-files",
                    files=files,
                    headers=headers,
                    timeout=120  # Longer timeout for AI processing
                )
                
                print(f"   📊 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract key information
                    total_files = data.get('total_files', 0)
                    successful_uploads = data.get('successful_uploads', 0)
                    certificates_created = data.get('certificates_created', 0)
                    results = data.get('results', [])
                    
                    print(f"   📈 Upload Summary:")
                    print(f"      - Total files: {total_files}")
                    print(f"      - Successful uploads: {successful_uploads}")
                    print(f"      - Certificates created: {certificates_created}")
                    
                    # Analyze first result (should be our BROTHER 36 PDF)
                    if results:
                        result = results[0]
                        category = result.get('category')
                        ship_name = result.get('ship_name')
                        certificate_created = result.get('certificate_created', False)
                        errors = result.get('errors', [])
                        extracted_info = result.get('extracted_info', {})
                        
                        print(f"   🔍 AI Analysis Results:")
                        print(f"      - Category: {category}")
                        print(f"      - Ship Name: {ship_name}")
                        print(f"      - Certificate Created: {certificate_created}")
                        print(f"      - Errors: {len(errors)} error(s)")
                        
                        if errors:
                            for error in errors:
                                print(f"        ⚠️ {error}")
                        
                        if extracted_info:
                            print(f"   📋 Extracted Information:")
                            for key, value in extracted_info.items():
                                if value is not None:
                                    print(f"      - {key}: {value}")
                        
                        # Check for specific f-string formatting issues
                        f_string_errors = [error for error in errors if 'format' in error.lower() or 'specifier' in error.lower()]
                        no_f_string_errors = len(f_string_errors) == 0
                        
                        # Verify expected results from review request
                        expected_category = "certificates"
                        expected_ship_name = "BROTHER 36"
                        expected_cert_created = 1  # 1 record created, not 0
                        
                        category_correct = category == expected_category
                        ship_name_correct = ship_name == expected_ship_name
                        cert_created_correct = certificates_created >= expected_cert_created
                        
                        print(f"\n   ✅ F-String Fix Verification:")
                        print(f"      - No formatting errors: {'✅ PASS' if no_f_string_errors else '❌ FAIL'}")
                        print(f"      - Category 'certificates': {'✅ PASS' if category_correct else '❌ FAIL'} (got: {category})")
                        print(f"      - Ship name 'BROTHER 36': {'✅ PASS' if ship_name_correct else '❌ FAIL'} (got: {ship_name})")
                        print(f"      - Certificate created (≥1): {'✅ PASS' if cert_created_correct else '❌ FAIL'} (got: {certificates_created})")
                        
                        # Overall success if all key requirements met and no f-string errors
                        overall_success = (no_f_string_errors and category_correct and 
                                         ship_name_correct and cert_created_correct)
                        
                        return self.log_test(
                            "Multi-File Upload F-String Fix", 
                            overall_success, 
                            f"F-string fix: {'✅ WORKING' if overall_success else '❌ ISSUES FOUND'}"
                        )
                    else:
                        return self.log_test("Multi-File Upload F-String Fix", False, "No results returned")
                        
                else:
                    error_text = response.text
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', error_text)
                    except:
                        error_detail = error_text
                    
                    # Check if the error is related to f-string formatting
                    is_f_string_error = ('format' in error_detail.lower() or 
                                       'specifier' in error_detail.lower())
                    
                    return self.log_test(
                        "Multi-File Upload F-String Fix", 
                        False, 
                        f"Status: {response.status_code}, F-string error: {is_f_string_error}, Error: {error_detail}"
                    )
                    
        except Exception as e:
            # Check if the exception is related to f-string formatting
            is_f_string_error = ('format' in str(e).lower() or 
                               'specifier' in str(e).lower())
            
            return self.log_test(
                "Multi-File Upload F-String Fix", 
                False, 
                f"F-string error: {is_f_string_error}, Exception: {str(e)}"
            )

    def cleanup_temp_files(self, *file_paths):
        """Clean up temporary files"""
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    print(f"   🗑️ Cleaned up: {file_path}")
                except:
                    pass

    def cleanup_test_user(self):
        """Clean up test user"""
        if self.admin_token and self.test_user_id:
            try:
                headers = {'Authorization': f'Bearer {self.admin_token}'}
                requests.delete(f"{self.api_url}/users/{self.test_user_id}", headers=headers, timeout=30)
                print(f"   🗑️ Cleaned up test user: {self.test_user_id}")
            except:
                pass

def main():
    """Main test execution"""
    print("🔧 F-String Formatting Fix Test - Multi-File Upload")
    print("=" * 60)
    print("Testing the fix for f-string formatting errors when AI returns JSON with curly braces")
    print("Expected: category='certificates', ship_name='BROTHER 36', 1 record created")
    print("=" * 60)
    
    tester = FStringFixTester()
    
    try:
        # Test admin authentication
        admin_login_success = tester.test_admin_login()
        if not admin_login_success:
            print("❌ Admin authentication failed, stopping tests")
            return 1
        
        # Create test user with company association
        user_creation_success = tester.create_test_user_with_company()
        if not user_creation_success:
            print("❌ Failed to create test user, stopping tests")
            return 1
        
        # Download the BROTHER 36 PDF
        download_success, pdf_path, file_size = tester.download_brother36_pdf()
        if not download_success:
            print("❌ Failed to download test PDF, stopping tests")
            return 1
        
        try:
            # Test multi-file upload with focus on f-string fix
            upload_success = tester.test_multi_file_upload_f_string_fix(pdf_path, file_size)
            
            # Print final results
            print("\n" + "=" * 60)
            print("📊 F-STRING FIX TEST RESULTS")
            print("=" * 60)
            
            print(f"Tests Run: {tester.tests_run}")
            print(f"Tests Passed: {tester.tests_passed}")
            print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
            
            if upload_success:
                print("\n🎉 F-STRING FIX TEST: SUCCESS")
                print("✅ F-string formatting fix is working correctly")
                print("✅ AI analysis correctly extracts maritime certificate information")
                print("✅ No formatting errors when AI returns JSON with curly braces")
                print("✅ Multi-file upload processes BROTHER 36 IAPP certificate correctly")
                return 0
            else:
                print("\n⚠️ F-STRING FIX TEST: ISSUES FOUND")
                print("❌ F-string formatting fix may have issues - check logs above")
                return 1
                
        finally:
            # Clean up temporary files
            tester.cleanup_temp_files(pdf_path)
            
    finally:
        # Clean up test user
        tester.cleanup_test_user()

if __name__ == "__main__":
    sys.exit(main())
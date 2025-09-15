#!/usr/bin/env python3
"""
Document Classification Testing for Ship Management System
Testing the document classification improvements with real certificate PDF

Focus: Test that documents are correctly classified as "certificates" instead of "other_documents"
"""

import requests
import sys
import json
import tempfile
import os
import time
from datetime import datetime, timezone

class DocumentClassificationTester:
    def __init__(self, base_url="https://vessel-docs-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.test_user_token = None
        self.test_company_id = None
        self.test_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data
        self.test_pdf_url = "https://customer-assets.emergentagent.com/job_vessel-docs-1/artifacts/nzwrda4b_BROTHER%2036%20-%20IAPP%20-%20PM242838.pdf"
        self.expected_category = "certificates"
        self.expected_ship_name = "BROTHER 36"

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED")
        
        if details:
            print(f"   {details}")

    def test_admin_login(self):
        """Test admin login"""
        print(f"\n🔐 ADMIN AUTHENTICATION")
        print("=" * 40)
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                self.log_test("Admin Login", True, "Admin authenticated successfully")
                return True
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False

    def create_test_company(self):
        """Create a test company for the user"""
        print(f"\n🏢 TEST COMPANY CREATION")
        print("=" * 40)
        
        try:
            company_data = {
                "name_vn": "Công ty Test AI",
                "name_en": "Test AI Company",
                "address_vn": "123 Test Street, Ho Chi Minh City",
                "address_en": "123 Test Street, Ho Chi Minh City",
                "tax_id": f"TEST{int(time.time())}",
                "gmail": "test@testai.com",
                "zalo": "0901234567"
            }
            
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = requests.post(
                f"{self.api_url}/companies",
                json=company_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_company_id = data.get('id')
                self.log_test(
                    "Test Company Creation",
                    True,
                    f"Company ID: {self.test_company_id}"
                )
                return True
            else:
                self.log_test("Test Company Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Test Company Creation", False, f"Error: {str(e)}")
            return False

    def create_test_user(self):
        """Create a test user associated with the company"""
        print(f"\n👤 TEST USER CREATION")
        print("=" * 40)
        
        try:
            user_data = {
                "username": f"testuser_{int(time.time())}",
                "email": f"testuser_{int(time.time())}@testai.com",
                "password": "TestPass123!",
                "full_name": "Test AI User",
                "role": "editor",
                "department": "technical",
                "company": "Test AI Company",
                "zalo": "0901234568"
            }
            
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = requests.post(
                f"{self.api_url}/users",
                json=user_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_user_id = data.get('id')
                
                # Now login as the test user
                login_response = requests.post(
                    f"{self.api_url}/auth/login",
                    json={"username": user_data["username"], "password": user_data["password"]},
                    timeout=30
                )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.test_user_token = login_data.get('access_token')
                    self.log_test(
                        "Test User Creation & Login",
                        True,
                        f"User ID: {self.test_user_id}"
                    )
                    return True
                else:
                    self.log_test("Test User Login", False, f"HTTP {login_response.status_code}")
                    return False
            else:
                self.log_test("Test User Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Test User Creation", False, f"Error: {str(e)}")
            return False

    def download_pdf(self):
        """Download the real certificate PDF"""
        print(f"\n📥 PDF DOWNLOAD")
        print("=" * 40)
        
        try:
            response = requests.get(self.test_pdf_url, timeout=30)
            
            if response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(response.content)
                temp_file.close()
                
                file_size = len(response.content)
                self.log_test(
                    "PDF Download",
                    True,
                    f"Downloaded {file_size} bytes"
                )
                return temp_file.name
            else:
                self.log_test("PDF Download", False, f"HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("PDF Download", False, f"Error: {str(e)}")
            return None

    def test_document_classification(self, pdf_path):
        """Test document classification via multi-file upload"""
        print(f"\n📁 DOCUMENT CLASSIFICATION TEST")
        print("=" * 40)
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                files = {'files': ('BROTHER_36_IAPP_PM242838.pdf', pdf_file, 'application/pdf')}
                headers = {'Authorization': f'Bearer {self.test_user_token}'}
                
                response = requests.post(
                    f"{self.api_url}/certificates/upload-multi-files",
                    files=files,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    if results:
                        first_result = results[0]
                        ai_analysis = first_result.get('ai_analysis', {})
                        
                        # Check document category
                        category = ai_analysis.get('category')
                        category_correct = category == self.expected_category
                        self.log_test(
                            "Document Category Classification",
                            category_correct,
                            f"Expected: '{self.expected_category}', Got: '{category}'"
                        )
                        
                        # Check ship name
                        ship_name = ai_analysis.get('ship_name')
                        ship_name_correct = ship_name == self.expected_ship_name
                        self.log_test(
                            "Ship Name in Classification",
                            ship_name_correct,
                            f"Expected: '{self.expected_ship_name}', Got: '{ship_name}'"
                        )
                        
                        # Check certificate details
                        cert_name = ai_analysis.get('cert_name')
                        cert_no = ai_analysis.get('cert_no')
                        issued_by = ai_analysis.get('issued_by')
                        
                        print(f"\n🧠 COMPLETE AI CLASSIFICATION RESULT:")
                        print(f"   Category: {category}")
                        print(f"   Ship Name: {ship_name}")
                        print(f"   Certificate Name: {cert_name}")
                        print(f"   Certificate Number: {cert_no}")
                        print(f"   Issued By: {issued_by}")
                        print(f"   Issue Date: {ai_analysis.get('issue_date')}")
                        print(f"   Valid Date: {ai_analysis.get('valid_date')}")
                        print(f"   Confidence: {ai_analysis.get('confidence')}")
                        
                        return category_correct and ship_name_correct
                    else:
                        self.log_test("Document Classification", False, "No results returned")
                        return False
                else:
                    self.log_test("Document Classification", False, f"HTTP {response.status_code}: {response.text}")
                    return False
                    
        except Exception as e:
            self.log_test("Document Classification", False, f"Error: {str(e)}")
            return False

    def cleanup_test_data(self):
        """Clean up test company and user"""
        print(f"\n🧹 CLEANUP TEST DATA")
        print("=" * 40)
        
        try:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            
            # Delete test user
            if self.test_user_id:
                requests.delete(f"{self.api_url}/users/{self.test_user_id}", headers=headers, timeout=30)
            
            # Delete test company
            if self.test_company_id:
                requests.delete(f"{self.api_url}/companies/{self.test_company_id}", headers=headers, timeout=30)
            
            self.log_test("Cleanup", True, "Test data cleaned up")
            
        except Exception as e:
            self.log_test("Cleanup", False, f"Error: {str(e)}")

    def run_classification_test(self):
        """Run document classification test"""
        print("📁 DOCUMENT CLASSIFICATION TEST FOR SHIP MANAGEMENT SYSTEM")
        print("=" * 65)
        print(f"Testing: {self.test_pdf_url}")
        print(f"Expected Category: {self.expected_category}")
        print(f"Expected Ship Name: {self.expected_ship_name}")
        print("=" * 65)
        
        try:
            # Setup
            if not self.test_admin_login():
                return False
            
            if not self.create_test_company():
                return False
            
            if not self.create_test_user():
                return False
            
            # Download PDF
            pdf_path = self.download_pdf()
            if not pdf_path:
                return False
            
            try:
                # Test classification
                classification_success = self.test_document_classification(pdf_path)
                
                # Print results
                print("\n" + "=" * 65)
                print("📊 CLASSIFICATION TEST RESULTS")
                print("=" * 65)
                
                print(f"Tests Run: {self.tests_run}")
                print(f"Tests Passed: {self.tests_passed}")
                print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
                
                if classification_success:
                    print("\n🎉 DOCUMENT CLASSIFICATION IMPROVEMENTS VERIFIED!")
                    print("✅ Document correctly classified as 'certificates'")
                    print("✅ Ship name correctly identified in classification")
                    print("✅ The reported classification issue has been RESOLVED")
                else:
                    print("\n⚠️ DOCUMENT CLASSIFICATION ISSUES DETECTED")
                    print("❌ Document classification not working correctly")
                    print("❌ The reported classification issue may still exist")
                
                return classification_success
                
            finally:
                # Clean up PDF
                if pdf_path and os.path.exists(pdf_path):
                    os.unlink(pdf_path)
                    
        finally:
            # Clean up test data
            self.cleanup_test_data()

def main():
    """Main test execution"""
    tester = DocumentClassificationTester()
    success = tester.run_classification_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
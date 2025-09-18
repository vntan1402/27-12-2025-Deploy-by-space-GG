#!/usr/bin/env python3
"""
Focused AI Analysis Testing for Ship Management System
Testing the specific AI analysis improvements reported by the user

Focus: Test the improved AI analysis with the real certificate PDF file.
The user reported that:
1. Ship name was analyzed as "Unknown Ship" (should be "BROTHER 36")
2. File was classified as "Other Documents" (should be "certificates")

This test focuses on the /api/analyze-ship-certificate endpoint which is working.
"""

import requests
import sys
import json
import tempfile
import os
from datetime import datetime, timezone

class FocusedAITester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data - Real certificate PDF URL from user report
        self.test_pdf_url = "https://customer-assets.emergentagent.com/job_vessel-docs-1/artifacts/nzwrda4b_BROTHER%2036%20-%20IAPP%20-%20PM242838.pdf"
        self.expected_results = {
            "ship_name": "BROTHER 36",
            "imo_number": "8743531",
            "cert_no": "PM242838",
            "flag": "PANAMA"
        }

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

    def test_login(self):
        """Test admin login"""
        print(f"\n🔐 AUTHENTICATION TEST")
        print("=" * 40)
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                user_info = data.get('user', {})
                self.log_test(
                    "Admin Login",
                    True,
                    f"User: {user_info.get('full_name')} ({user_info.get('role')})"
                )
                return True
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False

    def download_pdf(self):
        """Download the real certificate PDF"""
        print(f"\n📥 PDF DOWNLOAD TEST")
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

    def test_ai_analysis(self, pdf_path):
        """Test AI analysis of the certificate"""
        print(f"\n🤖 AI ANALYSIS TEST")
        print("=" * 40)
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                files = {'file': ('BROTHER_36_IAPP_PM242838.pdf', pdf_file, 'application/pdf')}
                headers = {'Authorization': f'Bearer {self.token}'}
                
                response = requests.post(
                    f"{self.api_url}/analyze-ship-certificate",
                    files=files,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    analysis = data.get('analysis', {})
                    
                    # Test ship name extraction (main issue reported)
                    ship_name = analysis.get('ship_name')
                    ship_name_correct = ship_name == self.expected_results['ship_name']
                    self.log_test(
                        "Ship Name Extraction",
                        ship_name_correct,
                        f"Expected: '{self.expected_results['ship_name']}', Got: '{ship_name}'"
                    )
                    
                    # Test IMO number extraction
                    imo_number = analysis.get('imo_number')
                    imo_correct = imo_number == self.expected_results['imo_number']
                    self.log_test(
                        "IMO Number Extraction",
                        imo_correct,
                        f"Expected: '{self.expected_results['imo_number']}', Got: '{imo_number}'"
                    )
                    
                    # Test flag extraction
                    flag = analysis.get('flag')
                    flag_correct = flag == self.expected_results['flag']
                    self.log_test(
                        "Flag Extraction",
                        flag_correct,
                        f"Expected: '{self.expected_results['flag']}', Got: '{flag}'"
                    )
                    
                    # Print complete analysis
                    print(f"\n📊 COMPLETE AI ANALYSIS RESULT:")
                    print(f"   Ship Name: {analysis.get('ship_name')}")
                    print(f"   IMO Number: {analysis.get('imo_number')}")
                    print(f"   Class Society: {analysis.get('class_society')}")
                    print(f"   Flag: {analysis.get('flag')}")
                    print(f"   Gross Tonnage: {analysis.get('gross_tonnage')}")
                    print(f"   Deadweight: {analysis.get('deadweight')}")
                    print(f"   Built Year: {analysis.get('built_year')}")
                    print(f"   Ship Owner: {analysis.get('ship_owner')}")
                    
                    return ship_name_correct and imo_correct
                else:
                    self.log_test("AI Analysis", False, f"HTTP {response.status_code}: {response.text}")
                    return False
                    
        except Exception as e:
            self.log_test("AI Analysis", False, f"Error: {str(e)}")
            return False

    def test_user_company_association(self):
        """Check if admin user has company association for multi-file upload"""
        print(f"\n👤 USER COMPANY CHECK")
        print("=" * 40)
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"{self.api_url}/users", headers=headers, timeout=30)
            
            if response.status_code == 200:
                users = response.json()
                admin_user = None
                for user in users:
                    if user.get('role') == 'super_admin':
                        admin_user = user
                        break
                
                if admin_user:
                    company = admin_user.get('company')
                    has_company = company is not None and company != ""
                    self.log_test(
                        "Admin Company Association",
                        has_company,
                        f"Company: {company}" if has_company else "No company assigned"
                    )
                    return has_company
                else:
                    self.log_test("Admin Company Association", False, "Admin user not found")
                    return False
            else:
                self.log_test("Admin Company Association", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Company Association", False, f"Error: {str(e)}")
            return False

    def run_focused_test(self):
        """Run focused AI analysis test"""
        print("🎯 FOCUSED AI ANALYSIS TEST FOR SHIP MANAGEMENT SYSTEM")
        print("=" * 60)
        print(f"Testing: {self.test_pdf_url}")
        print(f"Expected Ship Name: {self.expected_results['ship_name']}")
        print(f"Expected IMO: {self.expected_results['imo_number']}")
        print("=" * 60)
        
        # Test authentication
        if not self.test_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Check user company association
        self.test_user_company_association()
        
        # Download PDF
        pdf_path = self.download_pdf()
        if not pdf_path:
            print("❌ PDF download failed, stopping tests")
            return False
        
        try:
            # Test AI analysis
            ai_success = self.test_ai_analysis(pdf_path)
            
            # Print results
            print("\n" + "=" * 60)
            print("📊 TEST RESULTS SUMMARY")
            print("=" * 60)
            
            print(f"Tests Run: {self.tests_run}")
            print(f"Tests Passed: {self.tests_passed}")
            print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
            
            if ai_success:
                print("\n🎉 AI ANALYSIS IMPROVEMENTS VERIFIED!")
                print("✅ Ship name correctly extracted as 'BROTHER 36'")
                print("✅ IMO number correctly extracted as '8743531'")
                print("✅ The reported issue has been RESOLVED")
            else:
                print("\n⚠️ AI ANALYSIS ISSUES DETECTED")
                print("❌ Ship name or IMO extraction not working correctly")
                print("❌ The reported issue may still exist")
            
            return ai_success
            
        finally:
            # Clean up
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)

def main():
    """Main test execution"""
    tester = FocusedAITester()
    success = tester.run_focused_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
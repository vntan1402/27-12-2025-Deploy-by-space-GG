#!/usr/bin/env python3
"""
BROTHER 36 Multi-File Upload Test - Fixed Version
Testing the ship name validation and MongoDB regex query handling fixes

This test addresses the company association issue and focuses on the core fixes.
"""

import requests
import sys
import json
from datetime import datetime, timezone
import time
import os

class Brother36FixedTester:
    def __init__(self, base_url="https://ship-cert-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_info = None
        self.test_results = []

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })

    def run_api_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=120):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 {name}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {"raw_response": response.text}
            else:
                print(f"❌ Expected: {expected_status}, Got: {response.status_code}")
                if response.text:
                    print(f"   Response: {response.text[:300]}")
                return False, {"error": response.text, "status_code": response.status_code}

        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False, {"error": str(e)}

    def test_authentication_and_setup(self):
        """Test authentication and user setup"""
        print("\n" + "="*80)
        print("🔐 AUTHENTICATION AND SETUP")
        print("="*80)
        
        # Try admin1/123456 first (should have company)
        success, response = self.run_api_test(
            "Login with admin1/123456",
            "POST", "auth/login", 200,
            {"username": "admin1", "password": "123456"}
        )
        
        if success and response.get("access_token"):
            self.token = response["access_token"]
            self.user_info = response.get("user", {})
            print(f"✅ Authentication successful")
            print(f"   User: {self.user_info.get('username')} ({self.user_info.get('full_name')})")
            print(f"   Role: {self.user_info.get('role')}")
            print(f"   Company: {self.user_info.get('company')}")
            
            if self.user_info.get('company'):
                self.log_result("Authentication with Company", True, f"User has company: {self.user_info.get('company')}")
                return True
            else:
                print("⚠️  User has no company - will try to assign one")
                return self.setup_user_company()
        
        # Try admin/admin123 as fallback
        success, response = self.run_api_test(
            "Login with admin/admin123",
            "POST", "auth/login", 200,
            {"username": "admin", "password": "admin123"}
        )
        
        if success and response.get("access_token"):
            self.token = response["access_token"]
            self.user_info = response.get("user", {})
            print(f"✅ Authentication successful")
            print(f"   User: {self.user_info.get('username')} ({self.user_info.get('full_name')})")
            print(f"   Role: {self.user_info.get('role')}")
            print(f"   Company: {self.user_info.get('company')}")
            
            if self.user_info.get('company'):
                self.log_result("Authentication with Company", True, f"User has company: {self.user_info.get('company')}")
                return True
            else:
                print("⚠️  User has no company - will try to assign one")
                return self.setup_user_company()
        
        print("❌ Authentication failed with both accounts")
        self.log_result("Authentication", False, "Both admin accounts failed")
        return False

    def setup_user_company(self):
        """Setup user company if missing"""
        print(f"\n🏢 Setting up user company...")
        
        # Get available companies
        success, response = self.run_api_test(
            "Get companies list",
            "GET", "companies", 200
        )
        
        if not success:
            print("❌ Cannot get companies list")
            return False
        
        companies = response if isinstance(response, list) else []
        if not companies:
            print("❌ No companies available")
            return False
        
        # Use the first available company
        company = companies[0]
        company_name = company.get('name_en') or company.get('name_vn')
        print(f"   Using company: {company_name}")
        
        # Update user with company
        user_id = self.user_info.get('id')
        if not user_id:
            print("❌ Cannot get user ID")
            return False
        
        success, response = self.run_api_test(
            "Update user with company",
            "PUT", f"users/{user_id}", 200,
            {"company": company_name}
        )
        
        if success:
            print(f"✅ User updated with company: {company_name}")
            self.user_info['company'] = company_name
            self.log_result("User Company Setup", True, f"Assigned company: {company_name}")
            return True
        else:
            print("❌ Failed to update user with company")
            self.log_result("User Company Setup", False, "Failed to assign company")
            return False

    def test_brother36_multifile_upload(self):
        """Test multi-file upload with BROTHER 36 EIAPP PDF"""
        print("\n" + "="*80)
        print("📤 BROTHER 36 MULTI-FILE UPLOAD TEST")
        print("="*80)
        
        pdf_path = "/app/BROTHER_36_EIAPP_PM242757.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found: {pdf_path}")
            self.log_result("PDF File Availability", False, "File not found")
            return False
        
        file_size = os.path.getsize(pdf_path)
        print(f"📄 File: BROTHER_36_EIAPP_PM242757.pdf ({file_size:,} bytes)")
        
        try:
            with open(pdf_path, 'rb') as f:
                files = {
                    'files': ('BROTHER_36_EIAPP_PM242757.pdf', f, 'application/pdf')
                }
                
                print(f"\n📤 Uploading BROTHER 36 EIAPP certificate...")
                
                success, response = self.run_api_test(
                    "Multi-file upload with BROTHER 36 EIAPP PDF",
                    "POST", "certificates/upload-multi-files", 200,
                    data=None, files=files, timeout=180
                )
                
                if success:
                    print("✅ Multi-file upload successful!")
                    
                    # Parse response
                    total_files = response.get("total_files", 0)
                    successful_uploads = response.get("successful_uploads", 0)
                    certificates_created = response.get("certificates_created", 0)
                    results = response.get("results", [])
                    
                    print(f"   📊 Results:")
                    print(f"      Total files: {total_files}")
                    print(f"      Successful uploads: {successful_uploads}")
                    print(f"      Certificates created: {certificates_created}")
                    
                    # Analyze results
                    issues_found = []
                    ship_name_extracted = None
                    
                    if results:
                        for result in results:
                            filename = result.get('filename', 'Unknown')
                            status = result.get('status', 'Unknown')
                            ship_name = result.get('ship_name', 'Not extracted')
                            errors = result.get('errors', [])
                            
                            print(f"\n   📄 File: {filename}")
                            print(f"      Status: {status}")
                            print(f"      Ship Name: {ship_name}")
                            print(f"      Certificate Created: {result.get('certificate_created', False)}")
                            print(f"      Google Drive Uploaded: {result.get('google_drive_uploaded', False)}")
                            
                            ship_name_extracted = ship_name
                            
                            # Check for the specific errors mentioned in review request
                            for error in errors:
                                print(f"      ⚠️  Error: {error}")
                                
                                if "ship_name or folder_path is required" in error:
                                    issues_found.append("FOLDER_CREATION_ERROR")
                                elif "$regex has to be a string" in error:
                                    issues_found.append("MONGODB_REGEX_ERROR")
                    
                    # Evaluate results
                    if "FOLDER_CREATION_ERROR" in issues_found:
                        print("\n❌ CRITICAL: 'ship_name or folder_path is required' error still present!")
                        self.log_result("Folder Creation Fix", False, "ship_name or folder_path is required error still present")
                    else:
                        print("\n✅ FIXED: No 'ship_name or folder_path is required' errors")
                        self.log_result("Folder Creation Fix", True, "No folder creation errors")
                    
                    if "MONGODB_REGEX_ERROR" in issues_found:
                        print("❌ CRITICAL: '$regex has to be a string' error still present!")
                        self.log_result("MongoDB Regex Fix", False, "$regex has to be a string error still present")
                    else:
                        print("✅ FIXED: No '$regex has to be a string' errors")
                        self.log_result("MongoDB Regex Fix", True, "No MongoDB regex errors")
                    
                    # Check ship name extraction
                    if ship_name_extracted == "BROTHER 36":
                        print("✅ CORRECT: Ship name correctly extracted as 'BROTHER 36'")
                        self.log_result("Ship Name Extraction", True, "Correctly extracted: BROTHER 36")
                    elif ship_name_extracted and ship_name_extracted != "Unknown_Ship":
                        print(f"⚠️  PARTIAL: Ship name extracted as '{ship_name_extracted}' (expected 'BROTHER 36')")
                        self.log_result("Ship Name Extraction", False, f"Expected 'BROTHER 36', got '{ship_name_extracted}'")
                    else:
                        print("❌ FAILED: Ship name not extracted or defaulted to Unknown_Ship")
                        self.log_result("Ship Name Extraction", False, "Ship name not extracted")
                    
                    # Overall assessment
                    if successful_uploads > 0:
                        self.log_result("Multi-File Upload", True, f"Successfully processed {successful_uploads}/{total_files} files")
                        return True
                    else:
                        self.log_result("Multi-File Upload", False, "No files processed successfully")
                        return False
                
                else:
                    error_msg = response.get("error", "Unknown error")
                    print(f"❌ Multi-file upload failed: {error_msg}")
                    
                    # Check for specific errors
                    if "User not associated with any company" in error_msg:
                        print("   🔍 Issue: User company association problem")
                        self.log_result("Multi-File Upload", False, "User not associated with company")
                    elif "Google Drive not configured" in error_msg:
                        print("   🔍 Issue: Google Drive not configured")
                        self.log_result("Multi-File Upload", False, "Google Drive not configured")
                    else:
                        self.log_result("Multi-File Upload", False, f"Upload failed: {error_msg}")
                    
                    return False
        
        except Exception as e:
            print(f"❌ Exception during upload: {str(e)}")
            self.log_result("Multi-File Upload", False, f"Exception: {str(e)}")
            return False

    def verify_brother36_data(self):
        """Verify BROTHER 36 data was created correctly"""
        print("\n" + "="*80)
        print("🔍 BROTHER 36 DATA VERIFICATION")
        print("="*80)
        
        # Check ships (this should work)
        success, response = self.run_api_test(
            "Get ships list",
            "GET", "ships", 200
        )
        
        if success:
            ships = response if isinstance(response, list) else []
            brother36_ships = [s for s in ships if 'BROTHER' in s.get('name', '').upper() and '36' in s.get('name', '')]
            
            print(f"🚢 Found {len(ships)} total ships")
            if brother36_ships:
                print(f"✅ Found {len(brother36_ships)} BROTHER 36 ship(s)")
                for ship in brother36_ships:
                    print(f"   🚢 {ship.get('name')} (IMO: {ship.get('imo', 'N/A')})")
                self.log_result("Ship Records", True, f"Found {len(brother36_ships)} BROTHER 36 ships")
            else:
                print("⚠️  No BROTHER 36 ships found")
                self.log_result("Ship Records", False, "No BROTHER 36 ships found")
        
        # Try to check certificates (may fail due to validation errors)
        print(f"\n📋 Checking certificates...")
        success, response = self.run_api_test(
            "Get certificates list",
            "GET", "certificates", 200
        )
        
        if success:
            certificates = response if isinstance(response, list) else []
            brother36_certs = [c for c in certificates if 'BROTHER' in c.get('ship_name', '').upper() and '36' in c.get('ship_name', '')]
            
            print(f"✅ Found {len(certificates)} total certificates")
            if brother36_certs:
                print(f"✅ Found {len(brother36_certs)} BROTHER 36 certificate(s)")
                for cert in brother36_certs:
                    print(f"   📋 {cert.get('cert_name', 'Unknown')} - Ship: {cert.get('ship_name', 'Unknown')}")
                self.log_result("Certificate Records", True, f"Found {len(brother36_certs)} BROTHER 36 certificates")
            else:
                print("⚠️  No BROTHER 36 certificates found")
                self.log_result("Certificate Records", False, "No BROTHER 36 certificates found")
        else:
            print("⚠️  Could not fetch certificates (may be due to validation errors)")
            self.log_result("Certificate Records", False, "Could not fetch certificates")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        
        print(f"\n📈 Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "   Success Rate: 0%")
        
        # Review request specific findings
        print(f"\n🎯 REVIEW REQUEST FINDINGS:")
        
        folder_fix = next((r for r in self.test_results if "Folder Creation Fix" in r["test"]), None)
        regex_fix = next((r for r in self.test_results if "MongoDB Regex Fix" in r["test"]), None)
        ship_name = next((r for r in self.test_results if "Ship Name Extraction" in r["test"]), None)
        
        if folder_fix:
            status = "✅ FIXED" if folder_fix["success"] else "❌ NOT FIXED"
            print(f"   {status}: 'ship_name or folder_path is required' error")
        
        if regex_fix:
            status = "✅ FIXED" if regex_fix["success"] else "❌ NOT FIXED"
            print(f"   {status}: '$regex has to be a string' error")
        
        if ship_name:
            status = "✅ WORKING" if ship_name["success"] else "❌ ISSUE"
            print(f"   {status}: Ship name extraction - {ship_name['details']}")
        
        # Overall assessment
        critical_issues = [r for r in self.test_results if not r["success"] and any(x in r["test"] for x in ["Folder Creation Fix", "MongoDB Regex Fix", "Multi-File Upload"])]
        
        print(f"\n🏆 OVERALL ASSESSMENT:")
        if not critical_issues:
            print(f"   ✅ All critical fixes appear to be working")
            print(f"   ✅ Multi-file upload functionality operational")
        else:
            print(f"   ❌ {len(critical_issues)} critical issues remain")
            for issue in critical_issues:
                print(f"      - {issue['test']}: {issue['details']}")

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 BROTHER 36 Multi-File Upload Test - Fixed Version")
        print("Testing ship name validation and MongoDB regex query handling fixes")
        print("="*80)
        
        # Test 1: Authentication and setup
        if not self.test_authentication_and_setup():
            print("❌ Authentication/setup failed - cannot continue")
            self.print_summary()
            return False
        
        # Test 2: Multi-file upload (main test)
        self.test_brother36_multifile_upload()
        
        # Test 3: Verify data
        self.verify_brother36_data()
        
        # Print summary
        self.print_summary()
        
        return True

def main():
    """Main test execution"""
    tester = Brother36FixedTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
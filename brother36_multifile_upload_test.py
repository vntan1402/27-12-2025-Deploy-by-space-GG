#!/usr/bin/env python3
"""
BROTHER 36 Multi-File Upload Test for Ship Management System
Testing the fixed ship name validation and MongoDB regex query handling

Specific Review Request Testing:
1. "Folder creation failed: ship_name or folder_path is required"
2. "Certificate creation failed: $regex has to be a string"

Applied fixes testing:
1. Enhanced ship name validation in create_certificate_from_analysis function
2. Added proper string type checking before MongoDB regex queries
3. Added fallback to exact match if regex fails
4. Enhanced ship name validation in create_ship_folder_structure function
5. Improved ship name extraction and cleaning in multi-file upload endpoint

Test file: BROTHER 36 -EIAPP-PM242757.pdf
Expected ship name: "BROTHER 36"
"""

import requests
import sys
import json
from datetime import datetime, timezone
import time
import os

class Brother36MultiFileUploadTester:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.test_results = []
        self.critical_issues = []
        self.minor_issues = []

    def log_result(self, test_name, success, details="", is_critical=True):
        """Log test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "critical": is_critical
        })
        
        if not success:
            if is_critical:
                self.critical_issues.append(f"{test_name}: {details}")
            else:
                self.minor_issues.append(f"{test_name}: {details}")

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
        print(f"   URL: {url}")
        
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
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

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
                print(f"   Response: {response.text[:500]}")
                return False, {"error": response.text, "status_code": response.status_code}

        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False, {"error": str(e)}

    def test_authentication(self):
        """Test authentication with admin credentials"""
        print("\n" + "="*80)
        print("🔐 AUTHENTICATION TESTING")
        print("="*80)
        
        # Try admin/admin123 first
        success, response = self.run_api_test(
            "Login with admin/admin123",
            "POST", "auth/login", 200,
            {"username": "admin", "password": "admin123"}
        )
        
        if success and response.get("access_token"):
            self.token = response["access_token"]
            self.admin_user_id = response.get("user", {}).get("id")
            user_info = response.get("user", {})
            print(f"✅ Authentication successful")
            print(f"   User: {user_info.get('username')} ({user_info.get('full_name')})")
            print(f"   Role: {user_info.get('role')}")
            print(f"   Company: {user_info.get('company')}")
            self.log_result("Authentication", True, "admin/admin123 successful")
            return True
        
        # Try admin1/123456 as fallback
        success, response = self.run_api_test(
            "Login with admin1/123456",
            "POST", "auth/login", 200,
            {"username": "admin1", "password": "123456"}
        )
        
        if success and response.get("access_token"):
            self.token = response["access_token"]
            self.admin_user_id = response.get("user", {}).get("id")
            user_info = response.get("user", {})
            print(f"✅ Authentication successful")
            print(f"   User: {user_info.get('username')} ({user_info.get('full_name')})")
            print(f"   Role: {user_info.get('role')}")
            print(f"   Company: {user_info.get('company')}")
            self.log_result("Authentication", True, "admin1/123456 successful")
            return True
        
        print("❌ Authentication failed with both admin accounts")
        self.log_result("Authentication", False, "Both admin/admin123 and admin1/123456 failed")
        return False

    def test_brother36_multifile_upload(self):
        """Test multi-file upload with BROTHER 36 EIAPP PDF"""
        print("\n" + "="*80)
        print("📤 BROTHER 36 MULTI-FILE UPLOAD TESTING")
        print("="*80)
        
        pdf_path = "/app/BROTHER_36_EIAPP_PM242757.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found: {pdf_path}")
            self.log_result("PDF File Availability", False, "BROTHER 36 PDF not found")
            return False
        
        file_size = os.path.getsize(pdf_path)
        print(f"📄 Testing with: BROTHER_36_EIAPP_PM242757.pdf")
        print(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
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
                    print("✅ Multi-file upload request successful")
                    
                    # Parse response
                    total_files = response.get("total_files", 0)
                    successful_uploads = response.get("successful_uploads", 0)
                    certificates_created = response.get("certificates_created", 0)
                    results = response.get("results", [])
                    
                    print(f"   📊 Summary:")
                    print(f"      Total files: {total_files}")
                    print(f"      Successful uploads: {successful_uploads}")
                    print(f"      Certificates created: {certificates_created}")
                    
                    # Analyze file processing results
                    if results:
                        for i, result in enumerate(results):
                            filename = result.get('filename', 'Unknown')
                            status = result.get('status', 'Unknown')
                            ship_name = result.get('ship_name', 'Not extracted')
                            category = result.get('category', 'Unknown')
                            errors = result.get('errors', [])
                            
                            print(f"\n   📄 File {i+1}: {filename}")
                            print(f"      Status: {status}")
                            print(f"      Ship Name: {ship_name}")
                            print(f"      Category: {category}")
                            print(f"      Certificate Created: {result.get('certificate_created', False)}")
                            print(f"      Google Drive Uploaded: {result.get('google_drive_uploaded', False)}")
                            print(f"      Folder Created: {result.get('folder_created', False)}")
                            
                            # Check for specific errors mentioned in review request
                            critical_errors = []
                            for error in errors:
                                print(f"      ⚠️  Error: {error}")
                                
                                if "ship_name or folder_path is required" in error:
                                    critical_errors.append("Folder creation error: ship_name or folder_path is required")
                                elif "$regex has to be a string" in error:
                                    critical_errors.append("MongoDB regex error: $regex has to be a string")
                                elif "Folder creation failed" in error:
                                    critical_errors.append(f"Folder creation failed: {error}")
                                elif "Certificate creation failed" in error:
                                    critical_errors.append(f"Certificate creation failed: {error}")
                            
                            # Verify ship name extraction
                            if ship_name == "BROTHER 36":
                                print(f"      ✅ Ship name correctly extracted: {ship_name}")
                                self.log_result("Ship Name Extraction", True, f"Correctly extracted: {ship_name}")
                            elif ship_name and ship_name != "Unknown_Ship":
                                print(f"      ⚠️  Ship name extracted but may be incorrect: {ship_name}")
                                self.log_result("Ship Name Extraction", False, f"Expected 'BROTHER 36', got '{ship_name}'", is_critical=False)
                            else:
                                print(f"      ❌ Ship name not extracted or defaulted to Unknown_Ship")
                                self.log_result("Ship Name Extraction", False, "Ship name not extracted")
                            
                            # Log critical errors
                            if critical_errors:
                                for error in critical_errors:
                                    self.log_result("Critical Upload Error", False, error)
                            
                            # Check extracted information
                            extracted_info = result.get('extracted_info', {})
                            if extracted_info:
                                print(f"      📋 AI Extracted Information:")
                                for key, value in extracted_info.items():
                                    if value:
                                        print(f"         {key}: {value}")
                    
                    # Overall assessment
                    if total_files > 0 and successful_uploads > 0:
                        if certificates_created > 0:
                            self.log_result("Multi-File Upload", True, f"Successfully uploaded {successful_uploads}/{total_files} files, created {certificates_created} certificates")
                        else:
                            self.log_result("Multi-File Upload", False, f"Files uploaded but no certificates created", is_critical=False)
                        return True
                    else:
                        self.log_result("Multi-File Upload", False, "No files uploaded successfully")
                        return False
                
                else:
                    error_msg = response.get("error", "Unknown error")
                    status_code = response.get("status_code", "Unknown")
                    
                    print(f"❌ Multi-file upload failed")
                    print(f"   Status Code: {status_code}")
                    print(f"   Error: {error_msg}")
                    
                    # Check for specific errors mentioned in review request
                    if "ship_name or folder_path is required" in error_msg:
                        print("   🔍 DETECTED: 'ship_name or folder_path is required' error - This was supposed to be fixed!")
                        self.log_result("Folder Creation Fix", False, "ship_name or folder_path is required error still present")
                    elif "$regex has to be a string" in error_msg:
                        print("   🔍 DETECTED: '$regex has to be a string' error - This was supposed to be fixed!")
                        self.log_result("MongoDB Regex Fix", False, "$regex has to be a string error still present")
                    elif "Google Drive not configured" in error_msg:
                        print("   🔍 DETECTED: Google Drive not configured - This is a configuration issue")
                        self.log_result("Multi-File Upload", False, "Google Drive not configured", is_critical=False)
                    else:
                        self.log_result("Multi-File Upload", False, f"Upload failed: {error_msg}")
                    
                    return False
        
        except Exception as e:
            print(f"❌ Exception during multi-file upload: {str(e)}")
            self.log_result("Multi-File Upload", False, f"Exception: {str(e)}")
            return False

    def verify_brother36_records(self):
        """Verify BROTHER 36 records were created correctly"""
        print("\n" + "="*80)
        print("🔍 BROTHER 36 RECORDS VERIFICATION")
        print("="*80)
        
        # Check certificates
        success, response = self.run_api_test(
            "Get certificates list",
            "GET", "certificates", 200
        )
        
        brother36_certificates = []
        if success:
            certificates = response if isinstance(response, list) else []
            print(f"📋 Found {len(certificates)} total certificates")
            
            for cert in certificates:
                ship_name = cert.get('ship_name', '')
                if 'BROTHER' in ship_name.upper() and '36' in ship_name:
                    brother36_certificates.append(cert)
            
            if brother36_certificates:
                print(f"✅ Found {len(brother36_certificates)} BROTHER 36 certificate(s)")
                for cert in brother36_certificates:
                    print(f"   📋 Certificate: {cert.get('cert_name')}")
                    print(f"      Ship Name: {cert.get('ship_name')}")
                    print(f"      Certificate No: {cert.get('cert_no')}")
                    print(f"      File Name: {cert.get('file_name')}")
                self.log_result("Certificate Creation", True, f"Found {len(brother36_certificates)} BROTHER 36 certificates")
            else:
                print("⚠️  No BROTHER 36 certificates found")
                self.log_result("Certificate Creation", False, "No BROTHER 36 certificates found", is_critical=False)
        
        # Check ships
        success, response = self.run_api_test(
            "Get ships list",
            "GET", "ships", 200
        )
        
        brother36_ships = []
        if success:
            ships = response if isinstance(response, list) else []
            print(f"\n🚢 Found {len(ships)} total ships")
            
            for ship in ships:
                ship_name = ship.get('name', '')
                if 'BROTHER' in ship_name.upper() and '36' in ship_name:
                    brother36_ships.append(ship)
            
            if brother36_ships:
                print(f"✅ Found {len(brother36_ships)} BROTHER 36 ship(s)")
                for ship in brother36_ships:
                    print(f"   🚢 Ship: {ship.get('name')}")
                    print(f"      IMO: {ship.get('imo', 'Not specified')}")
                    print(f"      Company: {ship.get('company', 'Not specified')}")
                self.log_result("Ship Creation", True, f"Found {len(brother36_ships)} BROTHER 36 ships")
            else:
                print("⚠️  No BROTHER 36 ships found")
                self.log_result("Ship Creation", False, "No BROTHER 36 ships found", is_critical=False)

    def print_comprehensive_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        # Statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 Test Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "   Success Rate: 0%")
        print(f"   API Calls: {self.tests_run} (Passed: {self.tests_passed})")
        
        # Critical Issues Analysis
        print(f"\n🚨 CRITICAL ISSUES ANALYSIS:")
        if self.critical_issues:
            print(f"   Found {len(self.critical_issues)} critical issues:")
            for issue in self.critical_issues:
                print(f"   ❌ {issue}")
        else:
            print(f"   ✅ No critical issues found")
        
        # Review Request Specific Analysis
        print(f"\n🎯 REVIEW REQUEST SPECIFIC FINDINGS:")
        
        # Check for the specific errors mentioned in review request
        folder_error_found = any("ship_name or folder_path is required" in issue for issue in self.critical_issues)
        regex_error_found = any("$regex has to be a string" in issue for issue in self.critical_issues)
        
        if folder_error_found:
            print(f"   ❌ 'Folder creation failed: ship_name or folder_path is required' - STILL PRESENT")
        else:
            print(f"   ✅ 'Folder creation failed: ship_name or folder_path is required' - FIXED")
        
        if regex_error_found:
            print(f"   ❌ 'Certificate creation failed: $regex has to be a string' - STILL PRESENT")
        else:
            print(f"   ✅ 'Certificate creation failed: $regex has to be a string' - FIXED")
        
        # Ship name extraction
        ship_name_test = next((r for r in self.test_results if "Ship Name Extraction" in r["test"]), None)
        if ship_name_test:
            if ship_name_test["success"]:
                print(f"   ✅ Ship name extraction: Working correctly (BROTHER 36)")
            else:
                print(f"   ❌ Ship name extraction: {ship_name_test['details']}")
        else:
            print(f"   ⚠️  Ship name extraction: Not tested")
        
        # Overall assessment
        print(f"\n🏆 OVERALL ASSESSMENT:")
        if not self.critical_issues:
            print(f"   ✅ All critical functionality working correctly")
            print(f"   ✅ Both reported issues appear to be fixed")
            print(f"   ✅ Multi-file upload with BROTHER 36 EIAPP certificate successful")
        else:
            print(f"   ❌ {len(self.critical_issues)} critical issues remain")
            print(f"   ⚠️  Some fixes may not be working as expected")
        
        # Minor issues
        if self.minor_issues:
            print(f"\n⚠️  MINOR ISSUES ({len(self.minor_issues)}):")
            for issue in self.minor_issues:
                print(f"   ⚠️  {issue}")

    def run_all_tests(self):
        """Run all tests for BROTHER 36 multi-file upload"""
        print("🚀 BROTHER 36 Multi-File Upload Comprehensive Testing")
        print("Testing fixed ship name validation and MongoDB regex query handling")
        print("="*80)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("❌ Authentication failed - cannot continue")
            self.print_comprehensive_summary()
            return False
        
        # Test 2: Multi-file upload (main test)
        self.test_brother36_multifile_upload()
        
        # Test 3: Verify records were created
        self.verify_brother36_records()
        
        # Print comprehensive summary
        self.print_comprehensive_summary()
        
        return len(self.critical_issues) == 0

def main():
    """Main test execution"""
    print("BROTHER 36 Multi-File Upload Test for Ship Management System")
    print("Testing the fixed ship name validation and MongoDB regex query handling")
    print("="*80)
    
    tester = Brother36MultiFileUploadTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All critical tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some critical tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
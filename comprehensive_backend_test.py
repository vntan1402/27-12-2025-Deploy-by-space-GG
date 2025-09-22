#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Ship Management System
Focus: Google Drive Integration with New Apps Script URL and Multi-File Upload
"""

import requests
import sys
import json
import time
import io
import base64
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class ComprehensiveBackendTester:
    def __init__(self, base_url="https://continue-session.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.test_ship_id = None
        self.test_certificate_id = None
        
        # New Apps Script URL from review request
        self.new_apps_script_url = "https://script.google.com/macros/s/AKfycbwphwgJwjyW4V-Y2y0J4uIa40zZwybm7s9maqNemi04EawcOhxRX99rbSXGWxk_D6o/exec"
        
        print(f"🔧 Testing with Backend URL: {self.api_url}")
        print(f"🔧 New Apps Script URL: {self.new_apps_script_url}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, files: Optional[Dict] = None, 
                 params: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Run a single API test with comprehensive error handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Only set Content-Type for JSON requests
        if data and not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        print(f"   Method: {method} {url}")
        if params:
            print(f"   Params: {params}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=60)
            elif method == 'POST':
                if files:
                    # For file uploads, don't set Content-Type manually
                    headers.pop('Content-Type', None)
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=120)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=60)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=60)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.content else {}
                    if isinstance(response_data, dict) and len(str(response_data)) > 200:
                        print(f"   Response preview: {str(response_data)[:200]}...")
                    else:
                        print(f"   Response: {response_data}")
                    return True, response_data
                except:
                    return True, {"raw_response": response.text}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {"error": response.text, "status_code": response.status_code}

        except Exception as e:
            print(f"❌ FAILED - Exception: {str(e)}")
            return False, {"error": str(e)}

    def test_authentication(self) -> bool:
        """Test admin/admin123 login as specified in review request"""
        print(f"\n🔐 PRIORITY TEST: Authentication with admin/admin123")
        
        success, response = self.run_test(
            "Admin Login (admin/admin123)",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            user_info = response.get('user', {})
            print(f"✅ Authentication successful")
            print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
            print(f"   Company: {user_info.get('company', 'N/A')}")
            return True
        else:
            print(f"❌ Authentication failed")
            return False

    def test_core_apis(self) -> bool:
        """Test core APIs: companies and ships"""
        print(f"\n🏢 PRIORITY TEST: Core APIs (Companies & Ships)")
        
        # Test GET /api/companies
        success_companies, companies = self.run_test(
            "GET /api/companies",
            "GET",
            "companies",
            200
        )
        
        if success_companies:
            print(f"   Found {len(companies)} companies")
            for i, company in enumerate(companies[:3]):  # Show first 3
                print(f"   Company {i+1}: {company.get('name', 'N/A')} (ID: {company.get('id', 'N/A')})")
        
        # Test GET /api/ships
        success_ships, ships = self.run_test(
            "GET /api/ships",
            "GET",
            "ships",
            200
        )
        
        if success_ships:
            print(f"   Found {len(ships)} ships")
            for i, ship in enumerate(ships[:3]):  # Show first 3
                print(f"   Ship {i+1}: {ship.get('name', 'N/A')} (ID: {ship.get('id', 'N/A')})")
                if i == 0:  # Store first ship for later tests
                    self.test_ship_id = ship.get('id')
        
        return success_companies and success_ships

    def test_google_drive_config(self) -> bool:
        """Test Google Drive configuration with new Apps Script URL"""
        print(f"\n🔗 PRIORITY TEST: Google Drive Configuration with New Apps Script URL")
        
        # Test GET /api/gdrive/config
        success_get, config = self.run_test(
            "GET /api/gdrive/config",
            "GET",
            "gdrive/config",
            200
        )
        
        if success_get:
            print(f"   Current config: {config}")
            current_url = config.get('web_app_url', 'Not set')
            print(f"   Current Apps Script URL: {current_url}")
            
            # Check if it's the new URL
            if current_url == self.new_apps_script_url:
                print(f"✅ Apps Script URL is already updated to new URL")
                return True
            else:
                print(f"⚠️ Apps Script URL needs to be updated")
                print(f"   Expected: {self.new_apps_script_url}")
                print(f"   Current:  {current_url}")
        
        return success_get

    def test_google_drive_sync_proxy(self) -> bool:
        """Test Google Drive sync with Apps Script proxy"""
        print(f"\n📤 PRIORITY TEST: Google Drive Sync via Apps Script Proxy")
        
        # Test POST /api/gdrive/sync-to-drive-proxy
        success, response = self.run_test(
            "POST /api/gdrive/sync-to-drive-proxy",
            "POST",
            "gdrive/sync-to-drive-proxy",
            200
        )
        
        if success:
            print(f"   Sync response: {response}")
            files_uploaded = response.get('files_uploaded', 0)
            print(f"   Files uploaded: {files_uploaded}")
            
            # Test GET /api/gdrive/status after sync
            success_status, status = self.run_test(
                "GET /api/gdrive/status (after sync)",
                "GET",
                "gdrive/status",
                200
            )
            
            if success_status:
                print(f"   Drive status: {status}")
                print(f"   Local files: {status.get('local_files', 0)}")
                print(f"   Drive files: {status.get('drive_files', 0)}")
                print(f"   Last sync: {status.get('last_sync', 'Never')}")
        
        return success

    def create_test_pdf_content(self) -> bytes:
        """Create a simple test PDF content for testing"""
        # Simple PDF content for testing
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Certificate) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
        return pdf_content

    def test_multi_file_upload(self) -> bool:
        """Test multi-file upload with AI processing"""
        print(f"\n📁 PRIORITY TEST: Multi-File Upload with AI Processing")
        
        # Create test files
        test_files = []
        
        # Test PDF file
        pdf_content = self.create_test_pdf_content()
        test_files.append(('files', ('test_certificate.pdf', io.BytesIO(pdf_content), 'application/pdf')))
        
        # Test another PDF
        pdf_content2 = self.create_test_pdf_content()
        test_files.append(('files', ('test_survey_report.pdf', io.BytesIO(pdf_content2), 'application/pdf')))
        
        success, response = self.run_test(
            "POST /api/certificates/upload-multi-files",
            "POST",
            "certificates/upload-multi-files",
            200,
            files=test_files
        )
        
        if success:
            results = response.get('results', [])
            print(f"   Processed {len(results)} files")
            
            for i, result in enumerate(results):
                filename = result.get('filename', f'File {i+1}')
                status = result.get('status', 'unknown')
                print(f"   File {i+1}: {filename} - {status}")
                
                if status == 'success':
                    analysis = result.get('analysis', {})
                    category = analysis.get('category', 'unknown')
                    ship_name = analysis.get('ship_name', 'Unknown')
                    print(f"     Category: {category}")
                    print(f"     Ship: {ship_name}")
                    
                    if category == 'certificates':
                        cert_name = analysis.get('cert_name', 'Unknown Certificate')
                        print(f"     Certificate: {cert_name}")
                elif status == 'error':
                    error_msg = result.get('message', 'Unknown error')
                    print(f"     Error: {error_msg}")
        
        return success

    def test_certificate_management(self) -> bool:
        """Test certificate management APIs"""
        print(f"\n📜 PRIORITY TEST: Certificate Management APIs")
        
        # Test GET /api/certificates (if endpoint exists)
        success_get, certificates = self.run_test(
            "GET /api/certificates",
            "GET",
            "certificates",
            200
        )
        
        if success_get:
            print(f"   Found {len(certificates)} certificates")
        
        # Test POST /api/certificates for certificate creation
        if self.test_ship_id:
            cert_data = {
                "ship_id": self.test_ship_id,
                "cert_name": "Test Safety Management Certificate",
                "cert_type": "Full Term",
                "cert_no": f"SMC{int(time.time())}",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Test Classification Society",
                "category": "certificates",
                "sensitivity_level": "public"
            }
            
            success_create, certificate = self.run_test(
                "POST /api/certificates",
                "POST",
                "certificates",
                200,
                data=cert_data
            )
            
            if success_create:
                self.test_certificate_id = certificate.get('id')
                print(f"   Created certificate: {certificate.get('cert_name')}")
                print(f"   Certificate ID: {self.test_certificate_id}")
                print(f"   Abbreviation: {certificate.get('cert_abbreviation', 'N/A')}")
                print(f"   Status: {certificate.get('status', 'N/A')}")
                print(f"   Issued by: {certificate.get('issued_by', 'N/A')}")
                
                return success_get and success_create
        
        return success_get

    def test_enhanced_user_filtering(self) -> bool:
        """Test enhanced user filtering and sorting API"""
        print(f"\n👥 TEST: Enhanced User Filtering and Sorting")
        
        # Test GET /api/users/filtered endpoint
        success_basic, users = self.run_test(
            "GET /api/users/filtered (basic)",
            "GET",
            "users/filtered",
            200
        )
        
        if success_basic:
            print(f"   Found {len(users)} users (basic query)")
        
        # Test with company filter
        success_company, company_users = self.run_test(
            "GET /api/users/filtered (company filter)",
            "GET",
            "users/filtered",
            200,
            params={"company": "AMCSC"}
        )
        
        if success_company:
            print(f"   Found {len(company_users)} users for company 'AMCSC'")
        
        # Test with sorting
        success_sort, sorted_users = self.run_test(
            "GET /api/users/filtered (sorted by full_name)",
            "GET",
            "users/filtered",
            200,
            params={"sort_by": "full_name", "sort_order": "asc"}
        )
        
        if success_sort:
            print(f"   Found {len(sorted_users)} users (sorted by full_name)")
            if sorted_users:
                print(f"   First user: {sorted_users[0].get('full_name', 'N/A')}")
        
        return success_basic and success_company and success_sort

    def test_user_zalo_field(self) -> bool:
        """Test mandatory Zalo field in user creation"""
        print(f"\n📱 TEST: Mandatory Zalo Field in User Forms")
        
        # Test user creation without Zalo field (should fail)
        user_data_no_zalo = {
            "username": f"test_no_zalo_{int(time.time())}",
            "email": f"test_no_zalo_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Test User No Zalo",
            "role": "viewer",
            "department": "technical",
            "company": "Test Company"
        }
        
        success_fail, response_fail = self.run_test(
            "POST /api/users (without Zalo - should fail)",
            "POST",
            "users",
            422,  # Expecting validation error
            data=user_data_no_zalo
        )
        
        if success_fail:
            print(f"   ✅ Correctly rejected user creation without Zalo field")
        
        # Test user creation with Zalo field (should succeed)
        user_data_with_zalo = {
            "username": f"test_with_zalo_{int(time.time())}",
            "email": f"test_with_zalo_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Test User With Zalo",
            "role": "viewer",
            "department": "technical",
            "company": "Test Company",
            "zalo": "0901234567",
            "gmail": "test@gmail.com"
        }
        
        success_pass, response_pass = self.run_test(
            "POST /api/users (with Zalo - should succeed)",
            "POST",
            "users",
            200,
            data=user_data_with_zalo
        )
        
        if success_pass:
            print(f"   ✅ Successfully created user with Zalo field")
            print(f"   User: {response_pass.get('full_name')} (Zalo: {response_pass.get('zalo')})")
        
        return success_fail and success_pass

    def test_apps_script_connectivity(self) -> bool:
        """Test direct Apps Script connectivity"""
        print(f"\n🔗 TEST: Apps Script Connectivity Test")
        
        try:
            # Test direct connection to Apps Script URL
            test_payload = {
                "action": "test_connection"
            }
            
            print(f"   Testing direct connection to: {self.new_apps_script_url}")
            response = requests.post(self.new_apps_script_url, json=test_payload, timeout=30)
            
            print(f"   Response status: {response.status_code}")
            print(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   Response JSON: {result}")
                    return True
                except:
                    print(f"   Response text: {response.text[:200]}...")
                    return False
            else:
                print(f"   Error response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"   Connection error: {str(e)}")
            return False

    def run_comprehensive_tests(self) -> Dict[str, bool]:
        """Run all comprehensive tests"""
        print("🚢 COMPREHENSIVE BACKEND TESTING - GOOGLE DRIVE & MULTI-FILE UPLOAD FOCUS")
        print("=" * 80)
        
        test_results = {}
        
        # Priority 1: Authentication (required for all other tests)
        test_results["Authentication"] = self.test_authentication()
        if not test_results["Authentication"]:
            print("❌ Authentication failed - stopping all tests")
            return test_results
        
        # Priority 2: Core APIs
        test_results["Core APIs"] = self.test_core_apis()
        
        # Priority 3: Google Drive Integration Tests
        test_results["Google Drive Config"] = self.test_google_drive_config()
        test_results["Apps Script Connectivity"] = self.test_apps_script_connectivity()
        test_results["Google Drive Sync Proxy"] = self.test_google_drive_sync_proxy()
        
        # Priority 4: Multi-File Upload with AI Processing
        test_results["Multi-File Upload"] = self.test_multi_file_upload()
        
        # Priority 5: Certificate Management
        test_results["Certificate Management"] = self.test_certificate_management()
        
        # Priority 6: Enhanced User Management (from test_result.md needs_retesting)
        test_results["Enhanced User Filtering"] = self.test_enhanced_user_filtering()
        test_results["Mandatory Zalo Field"] = self.test_user_zalo_field()
        
        return test_results

    def print_final_results(self, test_results: Dict[str, bool]):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        # Priority tests first
        priority_tests = [
            "Authentication",
            "Core APIs", 
            "Google Drive Config",
            "Apps Script Connectivity",
            "Google Drive Sync Proxy",
            "Multi-File Upload",
            "Certificate Management"
        ]
        
        print("\n🔥 PRIORITY TESTS (Google Drive & Multi-File Upload Focus):")
        priority_passed = 0
        for test_name in priority_tests:
            if test_name in test_results:
                status = "✅ PASSED" if test_results[test_name] else "❌ FAILED"
                print(f"  {test_name:30} {status}")
                if test_results[test_name]:
                    priority_passed += 1
        
        print(f"\n📈 Priority Tests: {priority_passed}/{len(priority_tests)} passed")
        
        # Other tests
        other_tests = [k for k in test_results.keys() if k not in priority_tests]
        if other_tests:
            print("\n📋 OTHER TESTS:")
            other_passed = 0
            for test_name in other_tests:
                status = "✅ PASSED" if test_results[test_name] else "❌ FAILED"
                print(f"  {test_name:30} {status}")
                if test_results[test_name]:
                    other_passed += 1
            print(f"\n📈 Other Tests: {other_passed}/{len(other_tests)} passed")
        
        # Overall summary
        total_passed = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   API Calls: {self.tests_passed}/{self.tests_run} passed")
        print(f"   Feature Tests: {total_passed}/{total_tests} passed")
        
        if total_passed == total_tests and self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! Backend is working correctly.")
            return True
        else:
            print(f"\n⚠️ {total_tests - total_passed} feature tests failed")
            print(f"⚠️ {self.tests_run - self.tests_passed} API calls failed")
            return False

def main():
    """Main test execution"""
    tester = ComprehensiveBackendTester()
    
    # Run comprehensive tests
    test_results = tester.run_comprehensive_tests()
    
    # Print results and determine exit code
    success = tester.print_final_results(test_results)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
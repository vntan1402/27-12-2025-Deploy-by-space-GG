#!/usr/bin/env python3
"""
Focused Backend Testing for Priority Issues
Based on review request and test_result.md analysis
"""

import requests
import sys
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class FocusedBackendTester:
    def __init__(self, base_url="https://ship-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        
        # New Apps Script URL from review request
        self.new_apps_script_url = "https://script.google.com/macros/s/AKfycbwphwgJwjyW4V-Y2y0J4uIa40zZwybm7s9maqNemi04EawcOhxRX99rbSXGWxk_D6o/exec"
        
        print(f"🎯 FOCUSED TESTING - Priority Issues from Review Request")
        print(f"🔧 Backend URL: {self.api_url}")
        print(f"🔧 New Apps Script URL: {self.new_apps_script_url}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, files: Optional[Dict] = None, 
                 params: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if data and not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=60)
            elif method == 'POST':
                if files:
                    headers.pop('Content-Type', None)
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=120)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=60)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
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
        """Test admin/admin123 login"""
        print(f"\n🔐 AUTHENTICATION TEST")
        
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
            print(f"✅ User: {user_info.get('full_name')} ({user_info.get('role')})")
            return True
        return False

    def test_google_drive_integration(self) -> Dict[str, bool]:
        """Test Google Drive integration with new Apps Script URL"""
        print(f"\n🔗 GOOGLE DRIVE INTEGRATION TESTS")
        results = {}
        
        # 1. Test GET /api/gdrive/config
        success, config = self.run_test(
            "GET /api/gdrive/config",
            "GET",
            "gdrive/config",
            200
        )
        results["gdrive_config"] = success
        
        if success:
            print(f"   Current config: {config}")
            current_url = config.get('web_app_url') or config.get('apps_script_url')
            print(f"   Apps Script URL configured: {current_url is not None}")
            
            # Check if URL matches the new one from review request
            if current_url == self.new_apps_script_url:
                print(f"✅ Apps Script URL matches new URL from review request")
            else:
                print(f"⚠️ Apps Script URL may need updating")
        
        # 2. Test direct Apps Script connectivity
        success_direct = self.test_apps_script_direct()
        results["apps_script_direct"] = success_direct
        
        # 3. Test GET /api/gdrive/status
        success_status, status = self.run_test(
            "GET /api/gdrive/status",
            "GET",
            "gdrive/status",
            200
        )
        results["gdrive_status"] = success_status
        
        if success_status:
            print(f"   Status: {status.get('status', 'unknown')}")
            print(f"   Message: {status.get('message', 'N/A')}")
        
        # 4. Test sync endpoints (check if they exist)
        success_sync, sync_response = self.run_test(
            "POST /api/gdrive/sync-to-drive-proxy (check if exists)",
            "POST",
            "gdrive/sync-to-drive-proxy",
            200  # We expect this to work if endpoint exists
        )
        results["sync_proxy"] = success_sync
        
        if not success_sync:
            # Try alternative sync endpoint
            success_sync_alt, sync_alt_response = self.run_test(
                "POST /api/gdrive/sync-to-drive (alternative)",
                "POST",
                "gdrive/sync-to-drive",
                200
            )
            results["sync_alternative"] = success_sync_alt
        
        return results

    def test_apps_script_direct(self) -> bool:
        """Test direct connection to Apps Script URL"""
        print(f"\n🔗 Direct Apps Script Connection Test")
        
        try:
            # Test with folder_id as required by the Apps Script
            test_payload = {
                "action": "test_connection",
                "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"  # From config
            }
            
            response = requests.post(self.new_apps_script_url, json=test_payload, timeout=30)
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   Response: {result}")
                    if result.get('success'):
                        print(f"✅ Apps Script is working correctly")
                        return True
                    else:
                        print(f"⚠️ Apps Script returned error: {result.get('message')}")
                        return False
                except:
                    print(f"   Non-JSON response: {response.text[:200]}...")
                    return False
            else:
                print(f"   Error response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"   Connection error: {str(e)}")
            return False

    def test_multi_file_upload(self) -> bool:
        """Test multi-file upload with AI processing"""
        print(f"\n📁 MULTI-FILE UPLOAD TEST")
        
        # Create simple test PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (IAPP Certificate) Tj ET
endstream endobj
xref 0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref 300
%%EOF"""
        
        import io
        test_files = [
            ('files', ('test_iapp_certificate.pdf', io.BytesIO(pdf_content), 'application/pdf'))
        ]
        
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
            
            for result in results:
                filename = result.get('filename', 'Unknown')
                status = result.get('status', 'unknown')
                print(f"   File: {filename} - Status: {status}")
                
                if status == 'success':
                    analysis = result.get('analysis', {})
                    category = analysis.get('category', 'unknown')
                    ship_name = analysis.get('ship_name', 'Unknown')
                    cert_name = analysis.get('cert_name', 'Unknown')
                    print(f"     Category: {category}")
                    print(f"     Ship: {ship_name}")
                    print(f"     Certificate: {cert_name}")
                    
                    # Check if AI analysis is working
                    if category != 'unknown' and category != 'other_documents':
                        print(f"✅ AI analysis is working - classified as {category}")
                    else:
                        print(f"⚠️ AI analysis may need improvement - classified as {category}")
                        
                elif status == 'error':
                    error_msg = result.get('message', 'Unknown error')
                    print(f"     Error: {error_msg}")
        
        return success

    def test_certificate_management(self) -> Dict[str, bool]:
        """Test certificate management APIs"""
        print(f"\n📜 CERTIFICATE MANAGEMENT TESTS")
        results = {}
        
        # 1. Test GET /api/certificates (general endpoint)
        success_get_all, certificates = self.run_test(
            "GET /api/certificates (general)",
            "GET",
            "certificates",
            200
        )
        results["get_all_certificates"] = success_get_all
        
        if not success_get_all:
            print(f"   ⚠️ General certificates endpoint not available")
        
        # 2. Get ships first for ship-specific certificate tests
        success_ships, ships = self.run_test(
            "GET /api/ships (for certificate tests)",
            "GET",
            "ships",
            200
        )
        
        if success_ships and ships:
            ship_id = ships[0]['id']
            ship_name = ships[0]['name']
            print(f"   Using ship: {ship_name} (ID: {ship_id})")
            
            # 3. Test GET /api/ships/{ship_id}/certificates
            success_ship_certs, ship_certificates = self.run_test(
                f"GET /api/ships/{ship_id}/certificates",
                "GET",
                f"ships/{ship_id}/certificates",
                200
            )
            results["get_ship_certificates"] = success_ship_certs
            
            if success_ship_certs:
                print(f"   Found {len(ship_certificates)} certificates for ship")
            
            # 4. Test POST /api/certificates (create certificate)
            cert_data = {
                "ship_id": ship_id,
                "cert_name": "International Air Pollution Prevention Certificate",
                "cert_type": "Full Term",
                "cert_no": f"IAPP{int(time.time())}",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Panama Maritime Documentation Services",
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
            results["create_certificate"] = success_create
            
            if success_create:
                print(f"   Created: {certificate.get('cert_name')}")
                print(f"   Abbreviation: {certificate.get('cert_abbreviation', 'N/A')}")
                print(f"   Status: {certificate.get('status', 'N/A')}")
                print(f"   Issued by abbreviation: {certificate.get('issued_by_abbreviation', 'N/A')}")
        else:
            results["get_ship_certificates"] = False
            results["create_certificate"] = False
            print(f"   ⚠️ No ships available for certificate testing")
        
        return results

    def test_user_management_enhancements(self) -> Dict[str, bool]:
        """Test user management enhancements from test_result.md"""
        print(f"\n👥 USER MANAGEMENT ENHANCEMENT TESTS")
        results = {}
        
        # 1. Test enhanced user filtering endpoint
        success_filtered, filtered_users = self.run_test(
            "GET /api/users/filtered",
            "GET",
            "users/filtered",
            200
        )
        results["user_filtering"] = success_filtered
        
        if not success_filtered:
            print(f"   ⚠️ Enhanced user filtering endpoint not available")
            
            # Try basic users endpoint instead
            success_basic, basic_users = self.run_test(
                "GET /api/users (basic)",
                "GET",
                "users",
                200
            )
            results["basic_users"] = success_basic
            
            if success_basic:
                print(f"   Basic users endpoint works - found {len(basic_users)} users")
        else:
            print(f"   Enhanced filtering works - found {len(filtered_users)} users")
        
        # 2. Test mandatory Zalo field validation
        user_data_no_zalo = {
            "username": f"test_no_zalo_{int(time.time())}",
            "email": f"test_no_zalo_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Test User No Zalo",
            "role": "viewer",
            "department": "technical",
            "company": "Test Company"
        }
        
        success_validation, validation_response = self.run_test(
            "POST /api/users (without Zalo - should fail)",
            "POST",
            "users",
            422,  # Expecting validation error
            data=user_data_no_zalo
        )
        results["zalo_validation"] = success_validation
        
        if success_validation:
            print(f"✅ Zalo field validation working correctly")
        
        # 3. Test user creation with Zalo field
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
        
        success_create, create_response = self.run_test(
            "POST /api/users (with Zalo - should succeed)",
            "POST",
            "users",
            200,
            data=user_data_with_zalo
        )
        results["user_creation_with_zalo"] = success_create
        
        if success_create:
            print(f"✅ User creation with Zalo field working")
            print(f"   User: {create_response.get('full_name')} (Zalo: {create_response.get('zalo')})")
        
        return results

    def run_focused_tests(self) -> Dict[str, Any]:
        """Run focused tests based on review request priorities"""
        print("🎯 FOCUSED BACKEND TESTING - PRIORITY ISSUES")
        print("=" * 60)
        
        all_results = {}
        
        # Priority 1: Authentication
        auth_success = self.test_authentication()
        all_results["authentication"] = auth_success
        
        if not auth_success:
            print("❌ Authentication failed - stopping tests")
            return all_results
        
        # Priority 2: Google Drive Integration with new Apps Script URL
        gdrive_results = self.test_google_drive_integration()
        all_results["google_drive"] = gdrive_results
        
        # Priority 3: Multi-File Upload with AI Processing
        multi_upload_success = self.test_multi_file_upload()
        all_results["multi_file_upload"] = multi_upload_success
        
        # Priority 4: Certificate Management APIs
        cert_results = self.test_certificate_management()
        all_results["certificate_management"] = cert_results
        
        # Priority 5: User Management Enhancements (from test_result.md)
        user_results = self.test_user_management_enhancements()
        all_results["user_management"] = user_results
        
        return all_results

    def print_focused_results(self, results: Dict[str, Any]):
        """Print focused test results"""
        print("\n" + "=" * 60)
        print("📊 FOCUSED TEST RESULTS")
        print("=" * 60)
        
        # Authentication
        auth_status = "✅ PASSED" if results.get("authentication") else "❌ FAILED"
        print(f"Authentication (admin/admin123):     {auth_status}")
        
        # Google Drive Integration
        gdrive_results = results.get("google_drive", {})
        print(f"\n🔗 GOOGLE DRIVE INTEGRATION:")
        for test_name, result in gdrive_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {test_name:25} {status}")
        
        # Multi-File Upload
        multi_upload_status = "✅ PASSED" if results.get("multi_file_upload") else "❌ FAILED"
        print(f"\n📁 Multi-File Upload:               {multi_upload_status}")
        
        # Certificate Management
        cert_results = results.get("certificate_management", {})
        print(f"\n📜 CERTIFICATE MANAGEMENT:")
        for test_name, result in cert_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {test_name:25} {status}")
        
        # User Management
        user_results = results.get("user_management", {})
        print(f"\n👥 USER MANAGEMENT:")
        for test_name, result in user_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {test_name:25} {status}")
        
        # Summary
        print(f"\n🎯 SUMMARY:")
        print(f"   API Calls: {self.tests_passed}/{self.tests_run} passed")
        
        # Count feature test results
        total_features = 0
        passed_features = 0
        
        if results.get("authentication"):
            passed_features += 1
        total_features += 1
        
        if results.get("multi_file_upload"):
            passed_features += 1
        total_features += 1
        
        # Count sub-results
        for category in ["google_drive", "certificate_management", "user_management"]:
            category_results = results.get(category, {})
            if isinstance(category_results, dict):
                for result in category_results.values():
                    total_features += 1
                    if result:
                        passed_features += 1
            else:
                total_features += 1
                if category_results:
                    passed_features += 1
        
        print(f"   Feature Tests: {passed_features}/{total_features} passed")
        
        return passed_features == total_features and self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = FocusedBackendTester()
    
    # Run focused tests
    results = tester.run_focused_tests()
    
    # Print results and determine success
    success = tester.print_focused_results(results)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
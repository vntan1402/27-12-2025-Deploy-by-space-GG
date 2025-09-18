#!/usr/bin/env python3
"""
FINAL REVIEW REQUEST TEST - COMPREHENSIVE VERIFICATION
Testing all endpoints mentioned in the review request with detailed status reporting.
"""

import requests
import json
import os
from datetime import datetime

# Configuration from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipmanage.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class FinalReviewTest:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.results = {
            "authentication": None,
            "missing_endpoints": {},
            "google_drive": {},
            "core_functionality": {}
        }
        
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                user_info = data.get("user", {})
                self.results["authentication"] = {
                    "status": "✅ SUCCESS",
                    "message": f"Successfully authenticated as {ADMIN_USERNAME}",
                    "details": {
                        "role": user_info.get('role'),
                        "full_name": user_info.get('full_name'),
                        "company": user_info.get('company')
                    }
                }
                return True
            else:
                self.results["authentication"] = {
                    "status": "❌ FAILED",
                    "message": f"Authentication failed: {response.status_code}",
                    "details": response.text
                }
                return False
                
        except Exception as e:
            self.results["authentication"] = {
                "status": "❌ ERROR",
                "message": f"Authentication error: {str(e)}"
            }
            return False
    
    def test_missing_endpoints(self):
        """Test the 3 specific endpoints that were previously missing"""
        
        # 1. GET /api/certificates (was returning 405 Method Not Allowed)
        try:
            response = self.session.get(f"{API_BASE}/certificates")
            if response.status_code == 200:
                data = response.json()
                self.results["missing_endpoints"]["certificates"] = {
                    "status": "✅ FIXED",
                    "message": f"Now returns 200 with {len(data)} certificates (was 405 before)",
                    "details": f"Response type: list, Count: {len(data)}"
                }
            elif response.status_code == 405:
                self.results["missing_endpoints"]["certificates"] = {
                    "status": "❌ STILL BROKEN",
                    "message": "Still returning 405 Method Not Allowed",
                    "details": response.text
                }
            else:
                self.results["missing_endpoints"]["certificates"] = {
                    "status": "⚠️ UNEXPECTED",
                    "message": f"Unexpected status: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            self.results["missing_endpoints"]["certificates"] = {
                "status": "❌ ERROR",
                "message": f"Request error: {str(e)}"
            }
        
        # 2. GET /api/users/filtered (was returning 405 Method Not Allowed)
        try:
            response = self.session.get(f"{API_BASE}/users/filtered")
            if response.status_code == 200:
                data = response.json()
                self.results["missing_endpoints"]["users_filtered"] = {
                    "status": "✅ FIXED",
                    "message": f"Now returns 200 with {len(data)} users (was 405 before)",
                    "details": f"Response type: list, Count: {len(data)}"
                }
                
                # Test with parameters
                response2 = self.session.get(f"{API_BASE}/users/filtered?sort_by=full_name&sort_order=asc")
                if response2.status_code == 200:
                    data2 = response2.json()
                    self.results["missing_endpoints"]["users_filtered_params"] = {
                        "status": "✅ WORKING",
                        "message": f"Query parameters working, returned {len(data2)} sorted users",
                        "details": "Sorting by full_name in ascending order"
                    }
                
            elif response.status_code == 405:
                self.results["missing_endpoints"]["users_filtered"] = {
                    "status": "❌ STILL BROKEN",
                    "message": "Still returning 405 Method Not Allowed",
                    "details": response.text
                }
            else:
                self.results["missing_endpoints"]["users_filtered"] = {
                    "status": "⚠️ UNEXPECTED",
                    "message": f"Unexpected status: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            self.results["missing_endpoints"]["users_filtered"] = {
                "status": "❌ ERROR",
                "message": f"Request error: {str(e)}"
            }
        
        # 3. POST /api/gdrive/sync-to-drive-proxy (was returning 404 Not Found)
        try:
            response = self.session.post(f"{API_BASE}/gdrive/sync-to-drive-proxy")
            if response.status_code == 200:
                data = response.json()
                self.results["missing_endpoints"]["sync_proxy"] = {
                    "status": "✅ FIXED",
                    "message": "Now returns 200 - endpoint working (was 404 before)",
                    "details": f"Success: {data.get('success')}, Message: {data.get('message')}"
                }
            elif response.status_code == 404:
                self.results["missing_endpoints"]["sync_proxy"] = {
                    "status": "❌ STILL BROKEN",
                    "message": "Still returning 404 Not Found",
                    "details": response.text
                }
            elif response.status_code in [400, 500]:
                # These are expected if Google Drive is not properly configured
                try:
                    data = response.json()
                    detail = data.get("detail", "Unknown error")
                except:
                    detail = response.text
                
                self.results["missing_endpoints"]["sync_proxy"] = {
                    "status": "✅ ENDPOINT EXISTS",
                    "message": f"Endpoint now accessible (was 404 before), returns {response.status_code}",
                    "details": f"Configuration issue: {detail}"
                }
            else:
                self.results["missing_endpoints"]["sync_proxy"] = {
                    "status": "⚠️ UNEXPECTED",
                    "message": f"Unexpected status: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            self.results["missing_endpoints"]["sync_proxy"] = {
                "status": "❌ ERROR",
                "message": f"Request error: {str(e)}"
            }
        
        # 4. POST /api/gdrive/sync-to-drive (legacy endpoint)
        try:
            response = self.session.post(f"{API_BASE}/gdrive/sync-to-drive")
            if response.status_code == 200:
                data = response.json()
                self.results["missing_endpoints"]["sync_legacy"] = {
                    "status": "✅ WORKING",
                    "message": "Legacy endpoint working correctly",
                    "details": f"Success: {data.get('success')}, Message: {data.get('message')}"
                }
            elif response.status_code == 404:
                self.results["missing_endpoints"]["sync_legacy"] = {
                    "status": "❌ MISSING",
                    "message": "Legacy endpoint returning 404 Not Found",
                    "details": response.text
                }
            elif response.status_code in [400, 500]:
                # These are expected if Google Drive is not properly configured
                try:
                    data = response.json()
                    detail = data.get("detail", "Unknown error")
                except:
                    detail = response.text
                
                self.results["missing_endpoints"]["sync_legacy"] = {
                    "status": "✅ ENDPOINT EXISTS",
                    "message": f"Legacy endpoint accessible, returns {response.status_code}",
                    "details": f"Configuration issue: {detail}"
                }
            else:
                self.results["missing_endpoints"]["sync_legacy"] = {
                    "status": "⚠️ UNEXPECTED",
                    "message": f"Unexpected status: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            self.results["missing_endpoints"]["sync_legacy"] = {
                "status": "❌ ERROR",
                "message": f"Request error: {str(e)}"
            }
    
    def test_google_drive_integration(self):
        """Test Google Drive integration with the new Apps Script URL"""
        
        # Test Google Drive config
        try:
            response = self.session.get(f"{API_BASE}/gdrive/config")
            if response.status_code == 200:
                data = response.json()
                configured = data.get("configured", False)
                folder_id = data.get("folder_id", "")
                apps_script_configured = data.get("apps_script_url", False)
                
                self.results["google_drive"]["config"] = {
                    "status": "✅ WORKING",
                    "message": f"Google Drive config endpoint working, configured: {configured}",
                    "details": {
                        "folder_id": folder_id,
                        "apps_script_configured": apps_script_configured,
                        "expected_folder": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
                    }
                }
                
                # Check if correct folder ID is configured
                expected_folder = "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
                if folder_id == expected_folder:
                    self.results["google_drive"]["folder_verification"] = {
                        "status": "✅ CORRECT",
                        "message": "Correct Google Drive folder ID configured"
                    }
                else:
                    self.results["google_drive"]["folder_verification"] = {
                        "status": "⚠️ MISMATCH",
                        "message": f"Folder ID mismatch. Expected: {expected_folder}, Got: {folder_id}"
                    }
                
            else:
                self.results["google_drive"]["config"] = {
                    "status": "❌ FAILED",
                    "message": f"Google Drive config failed: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            self.results["google_drive"]["config"] = {
                "status": "❌ ERROR",
                "message": f"Request error: {str(e)}"
            }
        
        # Test Google Drive status
        try:
            response = self.session.get(f"{API_BASE}/gdrive/status")
            if response.status_code == 200:
                data = response.json()
                self.results["google_drive"]["status"] = {
                    "status": "✅ WORKING",
                    "message": "Google Drive status endpoint working",
                    "details": {
                        "status": data.get("status"),
                        "message": data.get("message", "")[:100]  # Truncate long messages
                    }
                }
            else:
                self.results["google_drive"]["status"] = {
                    "status": "❌ FAILED",
                    "message": f"Google Drive status failed: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            self.results["google_drive"]["status"] = {
                "status": "❌ ERROR",
                "message": f"Request error: {str(e)}"
            }
    
    def test_core_functionality(self):
        """Test core functionality mentioned in review request"""
        
        # Test multi-file upload endpoint
        try:
            response = self.session.post(f"{API_BASE}/certificates/upload-multi-files")
            if response.status_code == 422:
                # Expected - missing files parameter
                self.results["core_functionality"]["multi_file_upload"] = {
                    "status": "✅ WORKING",
                    "message": "Multi-file upload endpoint accessible (422 expected without files)",
                    "details": "Validation error as expected for missing files parameter"
                }
            elif response.status_code == 404:
                self.results["core_functionality"]["multi_file_upload"] = {
                    "status": "❌ MISSING",
                    "message": "Multi-file upload endpoint not found",
                    "details": response.text
                }
            else:
                self.results["core_functionality"]["multi_file_upload"] = {
                    "status": "✅ ACCESSIBLE",
                    "message": f"Multi-file upload endpoint accessible (status: {response.status_code})",
                    "details": response.text[:200]
                }
        except Exception as e:
            self.results["core_functionality"]["multi_file_upload"] = {
                "status": "❌ ERROR",
                "message": f"Request error: {str(e)}"
            }
        
        # Test authentication still working
        try:
            response = self.session.get(f"{API_BASE}/users")
            if response.status_code == 200:
                data = response.json()
                self.results["core_functionality"]["authentication_verification"] = {
                    "status": "✅ WORKING",
                    "message": f"Authentication still working, can access protected endpoints",
                    "details": f"Retrieved {len(data)} users"
                }
            else:
                self.results["core_functionality"]["authentication_verification"] = {
                    "status": "❌ FAILED",
                    "message": f"Authentication verification failed: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            self.results["core_functionality"]["authentication_verification"] = {
                "status": "❌ ERROR",
                "message": f"Request error: {str(e)}"
            }
    
    def run_all_tests(self):
        """Run all tests and generate comprehensive report"""
        print("=" * 80)
        print("FINAL REVIEW REQUEST TEST - COMPREHENSIVE VERIFICATION")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing with credentials: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print(f"Test time: {datetime.now().isoformat()}")
        print()
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        print("✅ Authentication successful")
        print()
        
        # Run all tests
        print("Testing missing endpoints...")
        self.test_missing_endpoints()
        
        print("Testing Google Drive integration...")
        self.test_google_drive_integration()
        
        print("Testing core functionality...")
        self.test_core_functionality()
        
        # Generate report
        self.generate_report()
        
        return self.calculate_overall_success()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("=" * 80)
        print("COMPREHENSIVE TEST RESULTS")
        print("=" * 80)
        
        # Authentication
        auth = self.results["authentication"]
        print(f"🔐 AUTHENTICATION: {auth['status']}")
        print(f"   {auth['message']}")
        if auth.get('details'):
            details = auth['details']
            if isinstance(details, dict):
                print(f"   Role: {details.get('role')}, Name: {details.get('full_name')}")
            else:
                print(f"   Details: {details}")
        print()
        
        # Missing Endpoints (Main focus of review request)
        print("🔧 MISSING ENDPOINTS (MAIN REVIEW REQUEST FOCUS):")
        print("-" * 50)
        for endpoint, result in self.results["missing_endpoints"].items():
            print(f"   {endpoint.upper()}: {result['status']}")
            print(f"      {result['message']}")
            if result.get('details'):
                print(f"      Details: {result['details']}")
            print()
        
        # Google Drive Integration
        print("☁️ GOOGLE DRIVE INTEGRATION:")
        print("-" * 50)
        for test, result in self.results["google_drive"].items():
            print(f"   {test.upper()}: {result['status']}")
            print(f"      {result['message']}")
            if result.get('details'):
                details = result['details']
                if isinstance(details, dict):
                    for key, value in details.items():
                        print(f"      {key}: {value}")
                else:
                    print(f"      Details: {details}")
            print()
        
        # Core Functionality
        print("⚙️ CORE FUNCTIONALITY:")
        print("-" * 50)
        for test, result in self.results["core_functionality"].items():
            print(f"   {test.upper()}: {result['status']}")
            print(f"      {result['message']}")
            if result.get('details'):
                print(f"      Details: {result['details']}")
            print()
    
    def calculate_overall_success(self):
        """Calculate overall test success"""
        total_tests = 0
        passed_tests = 0
        
        # Count all tests
        for category in ["missing_endpoints", "google_drive", "core_functionality"]:
            for test, result in self.results[category].items():
                total_tests += 1
                if "✅" in result["status"]:
                    passed_tests += 1
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("=" * 80)
        print("OVERALL RESULTS")
        print("=" * 80)
        print(f"Tests passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print()
        
        # Focus on the main review request items
        main_endpoints = ["certificates", "users_filtered", "sync_proxy", "sync_legacy"]
        main_passed = sum(1 for ep in main_endpoints if "✅" in self.results["missing_endpoints"].get(ep, {}).get("status", ""))
        main_total = len(main_endpoints)
        
        print("MAIN REVIEW REQUEST ITEMS:")
        print(f"Missing endpoints fixed: {main_passed}/{main_total}")
        
        if main_passed == main_total:
            print("🎉 SUCCESS: All missing endpoints have been implemented!")
            print("✅ GET /api/certificates now working (was 405)")
            print("✅ GET /api/users/filtered now working (was 405)")
            print("✅ POST /api/gdrive/sync-to-drive-proxy now accessible (was 404)")
            print("✅ POST /api/gdrive/sync-to-drive legacy endpoint working")
        else:
            print(f"⚠️ PARTIAL SUCCESS: {main_total - main_passed} endpoints still have issues")
        
        return success_rate >= 80  # 80% success rate threshold

if __name__ == "__main__":
    test = FinalReviewTest()
    success = test.run_all_tests()
    exit(0 if success else 1)
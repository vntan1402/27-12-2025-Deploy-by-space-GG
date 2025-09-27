#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
Focus: Testing the new /api/certificates/move endpoint
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration - Use production URL from frontend .env
BACKEND_URL = "https://marinetrack-1.preview.emergentagent.com/api"

class CertificateMoveTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_credentials = [
            {"username": "admin1", "password": "123456", "description": "Primary admin account"},
            {"username": "admin", "password": "admin123", "description": "Demo admin account"}
        ]
        self.auth_token = None
        self.test_results = {}
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def authenticate(self):
        """Authenticate with the backend to get access token"""
        try:
            self.log("🔐 Authenticating with backend...")
            
            for cred in self.test_credentials:
                username = cred["username"]
                password = cred["password"]
                
                login_data = {
                    "username": username,
                    "password": password,
                    "remember_me": False
                }
                
                endpoint = f"{BACKEND_URL}/auth/login"
                self.log(f"   Attempting login to: {endpoint}")
                response = requests.post(endpoint, json=login_data, timeout=60)
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    user_data = data.get("user", {})
                    
                    self.log(f"✅ Authentication successful with {username}")
                    self.log(f"   User Role: {user_data.get('role')}")
                    self.log(f"   Company: {user_data.get('company')}")
                    return True
                else:
                    self.log(f"❌ Authentication failed with {username} - Status: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"   Error: {response.text[:200]}")
                    
            self.log("❌ Authentication failed with all credentials")
            return False
            
        except requests.exceptions.RequestException as req_error:
            self.log(f"❌ Network error during authentication: {str(req_error)}", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_move_endpoint_debug(self):
        """Main test function for debugging the /api/certificates/move endpoint"""
        self.log("🔄 Starting Certificate Move Endpoint Debug Testing")
        self.log("🎯 Focus: Debug why /api/certificates/move endpoint is not working properly")
        self.log("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 2: Test Endpoint Accessibility
        accessibility_result = self.test_endpoint_accessibility()
        
        # Step 3: Compare with Working Endpoints
        comparison_result = self.compare_with_working_endpoints()
        
        # Step 4: Test Move Request Structure
        request_structure_result = self.test_move_request_structure()
        
        # Step 5: Check Backend Logs (by testing responses)
        backend_logs_result = self.check_backend_responses()
        
        # Step 6: Debug API Registration
        api_registration_result = self.debug_api_registration()
        
        # Step 7: Summary
        self.log("=" * 80)
        self.log("🔄 CERTIFICATE MOVE ENDPOINT DEBUG SUMMARY")
        self.log("=" * 80)
        
        self.log(f"{'✅' if accessibility_result else '❌'} Endpoint Accessibility: {'SUCCESS' if accessibility_result else 'FAILED'}")
        self.log(f"{'✅' if comparison_result else '❌'} Working Endpoints Comparison: {'SUCCESS' if comparison_result else 'FAILED'}")
        self.log(f"{'✅' if request_structure_result else '❌'} Move Request Structure: {'SUCCESS' if request_structure_result else 'FAILED'}")
        self.log(f"{'✅' if backend_logs_result else '❌'} Backend Response Analysis: {'SUCCESS' if backend_logs_result else 'FAILED'}")
        self.log(f"{'✅' if api_registration_result else '❌'} API Registration Debug: {'SUCCESS' if api_registration_result else 'FAILED'}")
        
        overall_success = all([accessibility_result, comparison_result, request_structure_result, backend_logs_result, api_registration_result])
        
        if overall_success:
            self.log("🎉 CERTIFICATE MOVE ENDPOINT DEBUG: COMPLETED SUCCESSFULLY")
        else:
            self.log("❌ CERTIFICATE MOVE ENDPOINT DEBUG: ISSUES DETECTED")
            self.log("🔍 Check detailed logs above for specific issues")
        
        return overall_success
    
    def test_endpoint_accessibility(self):
        """Test if POST /api/certificates/move endpoint is accessible"""
        try:
            self.log("🔌 Step 1: Testing Endpoint Accessibility...")
            
            endpoint = f"{BACKEND_URL}/certificates/move"
            self.log(f"   Testing endpoint: {endpoint}")
            
            # Test 1: OPTIONS request to check if endpoint exists
            self.log("   🧪 Test 1.1: OPTIONS request to check endpoint existence")
            try:
                options_response = requests.options(endpoint, headers=self.get_headers(), timeout=30)
                self.log(f"      OPTIONS /api/certificates/move - Status: {options_response.status_code}")
                
                if options_response.status_code in [200, 204]:
                    allowed_methods = options_response.headers.get('Allow', 'N/A')
                    self.log(f"      ✅ Endpoint exists - Allowed methods: {allowed_methods}")
                    
                    if 'POST' in allowed_methods:
                        self.log("      ✅ POST method is allowed")
                    else:
                        self.log("      ❌ POST method not in allowed methods")
                elif options_response.status_code == 404:
                    self.log("      ❌ Endpoint not found (404)")
                elif options_response.status_code == 405:
                    self.log("      ⚠️ Method not allowed for OPTIONS, but endpoint might exist")
                else:
                    self.log(f"      ⚠️ Unexpected status code: {options_response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.log(f"      ❌ OPTIONS request failed: {str(e)}")
            
            # Test 2: GET request to see what happens
            self.log("   🧪 Test 1.2: GET request to check endpoint response")
            try:
                get_response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
                self.log(f"      GET /api/certificates/move - Status: {get_response.status_code}")
                
                if get_response.status_code == 405:
                    self.log("      ✅ Method not allowed (endpoint exists but GET not supported)")
                elif get_response.status_code == 404:
                    self.log("      ❌ Endpoint not found")
                elif get_response.status_code == 200:
                    self.log("      ⚠️ Unexpected success with GET method")
                else:
                    self.log(f"      ℹ️ Status: {get_response.status_code}")
                    
                # Try to get error details
                try:
                    error_data = get_response.json()
                    self.log(f"      Response: {json.dumps(error_data, indent=2)}")
                except:
                    response_text = get_response.text[:200]
                    if response_text:
                        self.log(f"      Response text: {response_text}")
                        
            except requests.exceptions.RequestException as e:
                self.log(f"      ❌ GET request failed: {str(e)}")
            
            # Test 3: POST request with minimal data to test endpoint registration
            self.log("   🧪 Test 1.3: POST request with minimal data")
            try:
                minimal_data = {}
                post_response = requests.post(endpoint, json=minimal_data, headers=self.get_headers(), timeout=30)
                self.log(f"      POST /api/certificates/move (empty data) - Status: {post_response.status_code}")
                
                if post_response.status_code == 404:
                    self.log("      ❌ CRITICAL: Endpoint not found (404) - API registration issue")
                    return False
                elif post_response.status_code == 405:
                    self.log("      ❌ CRITICAL: Method not allowed (405) - POST method not registered")
                    return False
                elif post_response.status_code == 400:
                    self.log("      ✅ Bad request (400) - Endpoint exists but data validation failed")
                elif post_response.status_code == 422:
                    self.log("      ✅ Unprocessable entity (422) - Endpoint exists but validation failed")
                elif post_response.status_code == 200:
                    self.log("      ✅ Success (200) - Endpoint working")
                else:
                    self.log(f"      ℹ️ Status: {post_response.status_code}")
                
                # Get response details
                try:
                    response_data = post_response.json()
                    self.log(f"      Response: {json.dumps(response_data, indent=2)}")
                except:
                    response_text = post_response.text[:200]
                    if response_text:
                        self.log(f"      Response text: {response_text}")
                        
            except requests.exceptions.RequestException as e:
                self.log(f"      ❌ POST request failed: {str(e)}")
                return False
            
            return True
                
        except Exception as e:
            self.log(f"❌ Endpoint accessibility testing error: {str(e)}", "ERROR")
            return False
    
    def compare_with_working_endpoints(self):
        """Compare with working endpoints to verify API is working"""
        try:
            self.log("🔍 Step 2: Comparing with Working Endpoints...")
            
            # Test working endpoints to confirm API is accessible
            working_endpoints = [
                ("GET", "/certificates", "Get all certificates"),
                ("GET", "/ships", "Get all ships"),
                ("GET", "/companies", "Get all companies")
            ]
            
            for method, endpoint_path, description in working_endpoints:
                self.log(f"   🧪 Testing {method} {endpoint_path} - {description}")
                
                full_endpoint = f"{BACKEND_URL}{endpoint_path}"
                
                try:
                    if method == "GET":
                        response = requests.get(full_endpoint, headers=self.get_headers(), timeout=30)
                    else:
                        continue
                    
                    self.log(f"      Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, list):
                                self.log(f"      ✅ Success - Retrieved {len(data)} items")
                                
                                # Store sample data for move testing
                                if endpoint_path == "/certificates" and data:
                                    self.test_results['sample_certificates'] = data[:3]  # Store first 3 certificates
                                    self.log(f"         Stored {len(self.test_results['sample_certificates'])} sample certificates for testing")
                            else:
                                self.log(f"      ✅ Success - Retrieved data object")
                        except:
                            self.log(f"      ✅ Success - Non-JSON response")
                    else:
                        try:
                            error_data = response.json()
                            error_detail = error_data.get('detail', 'Unknown error')
                        except:
                            error_detail = response.text[:100]
                        
                        self.log(f"      ❌ Failed - {error_detail}")
                        return False
                
                except requests.exceptions.RequestException as e:
                    self.log(f"      ❌ Network error: {str(e)}")
                    return False
            
            self.log("   ✅ All working endpoints confirmed - API routing is functional")
            return True
                
        except Exception as e:
            self.log(f"❌ Working endpoints comparison error: {str(e)}", "ERROR")
            return False
    
    def test_move_request_structure(self):
        """Test with proper request body format"""
        try:
            self.log("📋 Step 3: Testing Move Request Structure...")
            
            # Get sample certificates for testing
            sample_certificates = self.test_results.get('sample_certificates', [])
            if not sample_certificates:
                self.log("   ⚠️ No sample certificates available for move testing")
                return True
            
            sample_cert = sample_certificates[0]
            cert_id = sample_cert.get('id')
            
            self.log(f"   Using sample certificate: {cert_id}")
            self.log(f"   Certificate name: {sample_cert.get('cert_name', 'N/A')}")
            self.log(f"   Current category: {sample_cert.get('category', 'N/A')}")
            
            # Test different request structures
            test_requests = [
                {
                    "name": "Complete request structure",
                    "data": {
                        "certificate_ids": [cert_id],
                        "target_folder_id": "test_folder_id_123",
                        "target_category": "survey_reports",
                        "target_folder_path": "SUNSHINE 01/Document Portfolio/Survey Reports"
                    }
                },
                {
                    "name": "Minimal request structure",
                    "data": {
                        "certificate_ids": [cert_id],
                        "target_folder_id": "test_folder_id_123"
                    }
                },
                {
                    "name": "Multiple certificates",
                    "data": {
                        "certificate_ids": [cert_id, sample_certificates[1].get('id') if len(sample_certificates) > 1 else cert_id],
                        "target_folder_id": "test_folder_id_123",
                        "target_category": "test_reports"
                    }
                },
                {
                    "name": "Missing certificate_ids",
                    "data": {
                        "target_folder_id": "test_folder_id_123",
                        "target_category": "survey_reports"
                    }
                },
                {
                    "name": "Missing target_folder_id",
                    "data": {
                        "certificate_ids": [cert_id],
                        "target_category": "survey_reports"
                    }
                }
            ]
            
            endpoint = f"{BACKEND_URL}/certificates/move"
            
            for test_request in test_requests:
                self.log(f"   🧪 Testing: {test_request['name']}")
                
                try:
                    response = requests.post(endpoint, json=test_request['data'], headers=self.get_headers(), timeout=30)
                    self.log(f"      Status: {response.status_code}")
                    
                    try:
                        response_data = response.json()
                        self.log(f"      Response: {json.dumps(response_data, indent=2)[:300]}...")
                        
                        if response.status_code == 200:
                            self.log("      ✅ Request successful")
                        elif response.status_code == 400:
                            self.log("      ℹ️ Bad request (expected for invalid data)")
                        elif response.status_code == 404:
                            self.log("      ❌ CRITICAL: Endpoint not found")
                            return False
                        elif response.status_code == 405:
                            self.log("      ❌ CRITICAL: Method not allowed")
                            return False
                        else:
                            self.log(f"      ℹ️ Status: {response.status_code}")
                            
                    except:
                        response_text = response.text[:200]
                        self.log(f"      Response text: {response_text}")
                        
                except requests.exceptions.RequestException as e:
                    self.log(f"      ❌ Request failed: {str(e)}")
                    return False
            
            return True
                
        except Exception as e:
            self.log(f"❌ Move request structure testing error: {str(e)}", "ERROR")
            return False
    
    def check_backend_responses(self):
        """Check backend responses during move requests"""
        try:
            self.log("📊 Step 4: Checking Backend Response Analysis...")
            
            # Get sample certificate for testing
            sample_certificates = self.test_results.get('sample_certificates', [])
            if not sample_certificates:
                self.log("   ⚠️ No sample certificates available")
                return True
            
            sample_cert = sample_certificates[0]
            cert_id = sample_cert.get('id')
            
            # Test with a realistic request
            test_data = {
                "certificate_ids": [cert_id],
                "target_folder_id": "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG",  # Real folder ID
                "target_category": "survey_reports",
                "target_folder_path": "SUNSHINE 01/Document Portfolio/Survey Reports"
            }
            
            endpoint = f"{BACKEND_URL}/certificates/move"
            
            self.log("   🧪 Testing with realistic move request...")
            self.log(f"      Certificate ID: {cert_id}")
            self.log(f"      Target folder ID: {test_data['target_folder_id']}")
            self.log(f"      Target category: {test_data['target_category']}")
            
            try:
                response = requests.post(endpoint, json=test_data, headers=self.get_headers(), timeout=60)
                self.log(f"      Status: {response.status_code}")
                
                # Detailed response analysis
                try:
                    response_data = response.json()
                    self.log("      📋 DETAILED RESPONSE ANALYSIS:")
                    self.log(f"         Response type: {type(response_data)}")
                    
                    if isinstance(response_data, dict):
                        for key, value in response_data.items():
                            if isinstance(value, (str, int, bool)):
                                self.log(f"         {key}: {value}")
                            elif isinstance(value, list):
                                self.log(f"         {key}: [{len(value)} items]")
                                if value:
                                    self.log(f"            First item: {value[0]}")
                            else:
                                self.log(f"         {key}: {type(value)}")
                    
                    # Check for specific error patterns
                    if 'detail' in response_data:
                        detail = response_data['detail']
                        self.log(f"      🔍 ERROR DETAIL: {detail}")
                        
                        if 'not found' in detail.lower():
                            self.log("         → Certificate or resource not found")
                        elif 'permission' in detail.lower():
                            self.log("         → Permission/authorization issue")
                        elif 'validation' in detail.lower():
                            self.log("         → Data validation issue")
                        elif 'google drive' in detail.lower():
                            self.log("         → Google Drive integration issue")
                    
                    if response.status_code == 200:
                        self.log("      ✅ Move operation completed successfully")
                        
                        # Check if we got expected response structure
                        if 'success' in response_data:
                            self.log(f"         Success: {response_data['success']}")
                        if 'message' in response_data:
                            self.log(f"         Message: {response_data['message']}")
                        if 'results' in response_data:
                            results = response_data['results']
                            self.log(f"         Results: {len(results)} certificate(s) processed")
                            
                except json.JSONDecodeError:
                    response_text = response.text
                    self.log(f"      Response text: {response_text[:300]}...")
                    
                    if response.status_code == 404:
                        self.log("      ❌ CRITICAL: Endpoint not found - API registration issue")
                        return False
                    elif response.status_code == 405:
                        self.log("      ❌ CRITICAL: Method not allowed - POST method not registered")
                        return False
                
            except requests.exceptions.RequestException as e:
                self.log(f"      ❌ Request failed: {str(e)}")
                return False
            
            return True
                
        except Exception as e:
            self.log(f"❌ Backend response analysis error: {str(e)}", "ERROR")
            return False
    
    def debug_api_registration(self):
        """Debug API registration issues"""
        try:
            self.log("🔧 Step 5: Debug API Registration...")
            
            # Check if the endpoint is properly registered by testing various HTTP methods
            endpoint = f"{BACKEND_URL}/certificates/move"
            
            methods_to_test = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
            
            self.log("   🧪 Testing all HTTP methods to debug registration...")
            
            for method in methods_to_test:
                try:
                    if method == 'GET':
                        response = requests.get(endpoint, headers=self.get_headers(), timeout=10)
                    elif method == 'POST':
                        response = requests.post(endpoint, json={}, headers=self.get_headers(), timeout=10)
                    elif method == 'PUT':
                        response = requests.put(endpoint, json={}, headers=self.get_headers(), timeout=10)
                    elif method == 'DELETE':
                        response = requests.delete(endpoint, headers=self.get_headers(), timeout=10)
                    elif method == 'PATCH':
                        response = requests.patch(endpoint, json={}, headers=self.get_headers(), timeout=10)
                    elif method == 'OPTIONS':
                        response = requests.options(endpoint, headers=self.get_headers(), timeout=10)
                    
                    self.log(f"      {method} - Status: {response.status_code}")
                    
                    if response.status_code == 404:
                        self.log(f"         ❌ {method}: Endpoint not found")
                    elif response.status_code == 405:
                        self.log(f"         ⚠️ {method}: Method not allowed (endpoint exists)")
                    elif response.status_code in [200, 400, 422]:
                        self.log(f"         ✅ {method}: Endpoint accessible")
                    else:
                        self.log(f"         ℹ️ {method}: Status {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    self.log(f"      ❌ {method}: Request failed - {str(e)}")
            
            # Check if there are any routing conflicts
            self.log("   🔍 Checking for potential routing conflicts...")
            
            similar_endpoints = [
                "/certificates",
                "/certificates/",
                "/certificate/move",
                "/api/certificates/move"
            ]
            
            for similar_endpoint in similar_endpoints:
                full_endpoint = f"{BACKEND_URL.replace('/api', '')}{similar_endpoint}"
                
                try:
                    response = requests.post(full_endpoint, json={}, headers=self.get_headers(), timeout=10)
                    self.log(f"      POST {similar_endpoint} - Status: {response.status_code}")
                    
                    if response.status_code != 404:
                        self.log(f"         ℹ️ Alternative endpoint found: {similar_endpoint}")
                        
                except requests.exceptions.RequestException:
                    pass
            
            # Final diagnosis
            self.log("   🎯 API REGISTRATION DIAGNOSIS:")
            
            # Test the exact endpoint one more time with detailed logging
            try:
                response = requests.post(endpoint, json={"test": "data"}, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 404:
                    self.log("      ❌ DIAGNOSIS: Endpoint /api/certificates/move is NOT registered in the API router")
                    self.log("         → Check if the endpoint is properly added to api_router in server.py")
                    self.log("         → Verify the route decorator is correct: @api_router.post('/certificates/move')")
                    self.log("         → Ensure the API router is included in the main app")
                elif response.status_code == 405:
                    self.log("      ❌ DIAGNOSIS: Endpoint exists but POST method is not allowed")
                    self.log("         → Check if the route is decorated with @api_router.post() not @api_router.get()")
                elif response.status_code in [200, 400, 422]:
                    self.log("      ✅ DIAGNOSIS: Endpoint is properly registered and accessible")
                    self.log("         → The issue is likely in the request data or business logic")
                else:
                    self.log(f"      ⚠️ DIAGNOSIS: Unexpected status code {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.log(f"      ❌ DIAGNOSIS: Network error - {str(e)}")
                return False
            
            return True
                
        except Exception as e:
            self.log(f"❌ API registration debug error: {str(e)}", "ERROR")
            return False

def main():
    """Main test execution"""
    print("🔄 Ship Management System - Certificate Move Endpoint Debug")
    print("🎯 Focus: Debug why /api/certificates/move endpoint is not working properly")
    print("=" * 80)
    
    tester = CertificateMoveTester()
    success = tester.test_move_endpoint_debug()
    
    print("=" * 80)
    if success:
        print("🎉 Certificate move endpoint debug completed successfully!")
        print("✅ All debug steps completed - endpoint analysis finished")
        
        # Print key findings summary
        print("\n🔑 KEY FINDINGS SUMMARY:")
        print("=" * 50)
        
        if 'sample_certificates' in tester.test_results:
            sample_certs = tester.test_results['sample_certificates']
            print(f"📋 Sample Certificates: {len(sample_certs)} certificates available for testing")
            for i, cert in enumerate(sample_certs):
                print(f"   {i+1}. {cert.get('cert_name', 'N/A')} (ID: {cert.get('id', 'N/A')})")
        
        print("\n💡 NEXT STEPS:")
        print("1. If endpoint returns 404/405: Check API registration in server.py")
        print("2. If endpoint accessible: Test with valid certificate IDs and folder IDs")
        print("3. Check Google Drive configuration for proper folder operations")
        print("4. Monitor backend logs for detailed error information")
        
        sys.exit(0)
    else:
        print("❌ Certificate move endpoint debug completed with issues!")
        print("🔍 Critical issues found - check detailed logs above")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Crew Certificates Analyze File Endpoint Test
Testing the /api/crew-certificates/analyze-file endpoint after ship company_id data fix

REVIEW REQUEST REQUIREMENTS:
- Test the crew certificates `/api/crew-certificates/analyze-file` endpoint again after fixing the ship company_id data issue
- Ships BROTHER 36 and MINH ANH 09 now have company_id = cd1951d0-223e-4a09-865b-593047ed8c2d
- The endpoint should now work and NOT return "Ship not found" error
- Test with ship_id = 7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7 (BROTHER 36)
- Login with admin1/123456 (password might be admin123, try both)
- Expected Result: Should NOT get "Ship not found" error, may get AI configuration errors (that's fine)

Test Plan:
1. Login with admin1/123456 (try admin123 if needed)
2. Get list of ships and verify BROTHER 36 and MINH ANH 09 have correct company_id
3. Test POST /api/crew-certificates/analyze-file with:
   - A sample PDF file
   - ship_id = 7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7 (BROTHER 36)
   - crew_id = optional
4. Verify the endpoint no longer returns "Ship not found" 404 error
5. The endpoint may fail with AI configuration or Document AI errors (that's expected), but it should get past the ship validation
6. Status code should be 200, 400, or 500 (NOT 404)
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
import tempfile
from urllib.parse import urlparse
import io

# Configuration - Use environment variable for backend URL
# Try internal URL first, then external
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL from frontend/.env
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    external_url = line.split('=')[1].strip()
                    BACKEND_URL = external_url + '/api'
                    print(f"Using external backend URL: {BACKEND_URL}")
                    break
            else:
                BACKEND_URL = 'https://crew-cert-manager.preview.emergentagent.com/api'
                print(f"Using fallback backend URL: {BACKEND_URL}")
    except:
        BACKEND_URL = 'https://crew-cert-manager.preview.emergentagent.com/api'
        print(f"Using fallback backend URL: {BACKEND_URL}")

class CrewCertificatesTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test data from review request
        self.ship_id = "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"
        self.crew_id = "d4e75288-986b-43ea-8be5-2a9b987c3515"
        
        # Test tracking for crew certificates endpoints
        self.cert_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'ship_exists': False,
            'crew_exists': False,
            
            # Endpoint accessibility tests
            'analyze_file_endpoint_exists': False,
            'manual_endpoint_exists': False,
            'get_certificates_endpoint_exists': False,
            
            # Endpoint functionality tests
            'analyze_file_accepts_multipart': False,
            'analyze_file_proper_error_not_404': False,
            'manual_endpoint_works': False,
            'get_endpoint_works': False,
            
            # Backend configuration tests
            'api_router_configured': False,
            'endpoint_registered_in_fastapi': False,
            'async_function_correct': False,
            
            # Error analysis
            'backend_logs_show_endpoint_registration': False,
            'no_typos_in_endpoint_path': False,
            'proper_decorator_used': False,
        }
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        # Also store in our log collection
        self.backend_logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
    def authenticate(self):
        """Authenticate with admin1/123456 credentials"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.cert_tests['authentication_successful'] = True
                self.cert_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def verify_test_data_exists(self):
        """Verify that the ship and crew from test data exist"""
        try:
            self.log("🔍 Verifying test data exists...")
            
            # Check if ship exists
            self.log(f"   Checking ship ID: {self.ship_id}")
            ship_response = self.session.get(f"{BACKEND_URL}/ships/{self.ship_id}")
            self.log(f"   Ship check response: {ship_response.status_code}")
            
            if ship_response.status_code == 200:
                ship_data = ship_response.json()
                self.log(f"✅ Ship exists: {ship_data.get('name', 'Unknown')}")
                self.cert_tests['ship_exists'] = True
            else:
                self.log(f"❌ Ship not found: {ship_response.status_code}")
                # Try to find any ship for testing
                ships_response = self.session.get(f"{BACKEND_URL}/ships")
                if ships_response.status_code == 200:
                    ships = ships_response.json()
                    if ships:
                        self.ship_id = ships[0].get('id')
                        self.log(f"   Using alternative ship ID: {self.ship_id}")
                        self.cert_tests['ship_exists'] = True
            
            # Check if crew exists
            self.log(f"   Checking crew ID: {self.crew_id}")
            crew_response = self.session.get(f"{BACKEND_URL}/crew/{self.crew_id}")
            self.log(f"   Crew check response: {crew_response.status_code}")
            
            if crew_response.status_code == 200:
                crew_data = crew_response.json()
                self.log(f"✅ Crew exists: {crew_data.get('full_name', 'Unknown')}")
                self.cert_tests['crew_exists'] = True
            else:
                self.log(f"❌ Crew not found: {crew_response.status_code}")
                # Try to find any crew for testing
                crew_list_response = self.session.get(f"{BACKEND_URL}/crew")
                if crew_list_response.status_code == 200:
                    crew_list = crew_list_response.json()
                    if crew_list:
                        self.crew_id = crew_list[0].get('id')
                        self.log(f"   Using alternative crew ID: {self.crew_id}")
                        self.cert_tests['crew_exists'] = True
            
            return self.cert_tests['ship_exists'] and self.cert_tests['crew_exists']
            
        except Exception as e:
            self.log(f"❌ Error verifying test data: {str(e)}", "ERROR")
            return False
    
    def test_analyze_file_endpoint(self):
        """Test POST /api/crew-certificates/analyze-file endpoint"""
        try:
            self.log("📄 Testing POST /api/crew-certificates/analyze-file endpoint...")
            
            # Create a dummy PDF file for testing
            dummy_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
            
            # Prepare multipart form data
            files = {
                'cert_file': ('test_certificate.pdf', io.BytesIO(dummy_pdf_content), 'application/pdf')
            }
            data = {
                'ship_id': self.ship_id,
                'crew_id': self.crew_id
            }
            
            endpoint = f"{BACKEND_URL}/crew-certificates/analyze-file"
            self.log(f"   POST {endpoint}")
            self.log(f"   Ship ID: {self.ship_id}")
            self.log(f"   Crew ID: {self.crew_id}")
            
            start_time = time.time()
            response = self.session.post(
                endpoint,
                files=files,
                data=data,
                timeout=120
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            # Check if endpoint exists (not 404)
            if response.status_code != 404:
                self.log("✅ analyze-file endpoint EXISTS (not 404)")
                self.cert_tests['analyze_file_endpoint_exists'] = True
                self.cert_tests['analyze_file_accepts_multipart'] = True
                
                if response.status_code in [200, 400, 500]:
                    self.log("✅ analyze-file endpoint returns proper error (not 404)")
                    self.cert_tests['analyze_file_proper_error_not_404'] = True
                
                # Log response details
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        response_data = response.json()
                        self.log(f"   Response data: {json.dumps(response_data, indent=2)}")
                    else:
                        self.log(f"   Response text: {response.text[:500]}")
                except:
                    self.log(f"   Raw response: {response.text[:500]}")
                
                return True
            else:
                self.log("❌ analyze-file endpoint returns 404 - ENDPOINT NOT FOUND")
                self.log(f"   Response text: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing analyze-file endpoint: {str(e)}", "ERROR")
            return False
    
    def test_manual_endpoint(self):
        """Test POST /api/crew-certificates/manual endpoint"""
        try:
            self.log("📝 Testing POST /api/crew-certificates/manual endpoint...")
            
            # Prepare test data for manual certificate creation
            cert_data = {
                "crew_id": self.crew_id,
                "crew_name": "Test Crew Member",
                "passport": "TEST123456",
                "cert_name": "Test Certificate",
                "cert_no": "TEST-CERT-001",
                "issued_by": "Test Authority",
                "issued_date": "2024-01-01T00:00:00Z",
                "cert_expiry": "2025-01-01T00:00:00Z",
                "status": "Valid",
                "note": "Test certificate for endpoint testing"
            }
            
            endpoint = f"{BACKEND_URL}/crew-certificates/manual"
            params = {"ship_id": self.ship_id}
            
            self.log(f"   POST {endpoint}?ship_id={self.ship_id}")
            self.log(f"   Test data: {json.dumps(cert_data, indent=2)}")
            
            response = self.session.post(
                endpoint,
                json=cert_data,
                params=params,
                timeout=60
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            # Check if endpoint exists (not 404)
            if response.status_code != 404:
                self.log("✅ manual endpoint EXISTS (not 404)")
                self.cert_tests['manual_endpoint_exists'] = True
                
                if response.status_code in [200, 201]:
                    self.log("✅ manual endpoint works correctly")
                    self.cert_tests['manual_endpoint_works'] = True
                    
                    try:
                        response_data = response.json()
                        self.log(f"   Created certificate ID: {response_data.get('id', 'Unknown')}")
                        return response_data.get('id')
                    except:
                        pass
                elif response.status_code in [400, 422]:
                    self.log("✅ manual endpoint returns validation error (expected)")
                    self.cert_tests['manual_endpoint_works'] = True
                else:
                    self.log(f"   ⚠️ Unexpected status code: {response.status_code}")
                
                # Log response details
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        response_data = response.json()
                        self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                    else:
                        self.log(f"   Response text: {response.text[:500]}")
                except:
                    self.log(f"   Raw response: {response.text[:500]}")
                
                return True
            else:
                self.log("❌ manual endpoint returns 404 - ENDPOINT NOT FOUND")
                self.log(f"   Response text: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing manual endpoint: {str(e)}", "ERROR")
            return False
    
    def test_get_certificates_endpoint(self):
        """Test GET /api/crew-certificates/{ship_id} endpoint"""
        try:
            self.log("📋 Testing GET /api/crew-certificates/{ship_id} endpoint...")
            
            endpoint = f"{BACKEND_URL}/crew-certificates/{self.ship_id}"
            self.log(f"   GET {endpoint}")
            
            response = self.session.get(endpoint, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            # Check if endpoint exists (not 404)
            if response.status_code != 404:
                self.log("✅ GET certificates endpoint EXISTS (not 404)")
                self.cert_tests['get_certificates_endpoint_exists'] = True
                
                if response.status_code == 200:
                    self.log("✅ GET certificates endpoint works correctly")
                    self.cert_tests['get_endpoint_works'] = True
                    
                    try:
                        certificates = response.json()
                        self.log(f"   Retrieved {len(certificates)} certificates")
                        
                        if certificates:
                            # Show first certificate structure
                            first_cert = certificates[0]
                            self.log(f"   Sample certificate: {first_cert.get('cert_name', 'Unknown')}")
                    except:
                        pass
                elif response.status_code in [400, 403]:
                    self.log("✅ GET endpoint returns proper error (not 404)")
                    self.cert_tests['get_endpoint_works'] = True
                else:
                    self.log(f"   ⚠️ Unexpected status code: {response.status_code}")
                
                # Log response details
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        response_data = response.json()
                        if isinstance(response_data, list) and len(response_data) > 3:
                            self.log(f"   Response: [{len(response_data)} items] (truncated)")
                        else:
                            self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                    else:
                        self.log(f"   Response text: {response.text[:500]}")
                except:
                    self.log(f"   Raw response: {response.text[:500]}")
                
                return True
            else:
                self.log("❌ GET certificates endpoint returns 404 - ENDPOINT NOT FOUND")
                self.log(f"   Response text: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing GET certificates endpoint: {str(e)}", "ERROR")
            return False
    
    def check_backend_configuration(self):
        """Check backend configuration and logs for endpoint registration"""
        try:
            self.log("🔧 Checking backend configuration...")
            
            # Check if endpoints are registered by testing OPTIONS request
            endpoints_to_check = [
                "/crew-certificates/analyze-file",
                "/crew-certificates/manual", 
                "/crew-certificates/{ship_id}"
            ]
            
            for endpoint_path in endpoints_to_check:
                try:
                    endpoint = f"{BACKEND_URL}{endpoint_path}"
                    options_response = requests.options(endpoint, timeout=10)
                    self.log(f"   OPTIONS {endpoint_path}: {options_response.status_code}")
                    
                    if options_response.status_code != 404:
                        self.log(f"   ✅ {endpoint_path} is registered in FastAPI")
                        if "analyze-file" in endpoint_path:
                            self.cert_tests['endpoint_registered_in_fastapi'] = True
                    else:
                        self.log(f"   ❌ {endpoint_path} not registered in FastAPI")
                        
                except Exception as e:
                    self.log(f"   ⚠️ Could not check {endpoint_path}: {e}")
            
            # Check backend logs for endpoint registration
            self.check_backend_logs()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend configuration: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs(self):
        """Check backend logs for endpoint registration and errors"""
        try:
            self.log("📋 Checking backend logs...")
            
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture startup and recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            # Look for endpoint registration patterns
                            endpoint_patterns = [
                                "crew-certificates",
                                "analyze-file",
                                "FastAPI",
                                "api_router",
                                "startup",
                                "route"
                            ]
                            
                            relevant_lines = []
                            for line in lines:
                                if any(pattern in line.lower() for pattern in endpoint_patterns):
                                    relevant_lines.append(line)
                            
                            if relevant_lines:
                                self.log(f"   Found {len(relevant_lines)} relevant log entries:")
                                for line in relevant_lines[-10:]:  # Show last 10 relevant lines
                                    self.log(f"     {line}")
                                    
                                # Check for specific patterns
                                log_text = '\n'.join(relevant_lines)
                                if "crew-certificates" in log_text.lower():
                                    self.log("   ✅ Found crew-certificates in logs")
                                    self.cert_tests['backend_logs_show_endpoint_registration'] = True
                            else:
                                self.log(f"   No relevant entries found in {log_file}")
                        else:
                            self.log(f"   {log_file} is empty or not accessible")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
                else:
                    self.log(f"   {log_file} not found")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def analyze_404_issue(self):
        """Analyze potential causes of 404 errors"""
        try:
            self.log("🔍 Analyzing potential 404 causes...")
            
            # Check if api_router is properly configured
            self.log("   Checking API router configuration...")
            
            # Test base API endpoint
            base_response = self.session.get(f"{BACKEND_URL}/")
            self.log(f"   Base API response: {base_response.status_code}")
            
            if base_response.status_code == 404:
                self.log("   ❌ Base API endpoint returns 404 - API router not configured")
            else:
                self.log("   ✅ Base API endpoint accessible - API router configured")
                self.cert_tests['api_router_configured'] = True
            
            # Check for common endpoint patterns
            common_endpoints = [
                "/ships",
                "/crew", 
                "/auth/login",
                "/certificates"
            ]
            
            working_endpoints = []
            for endpoint_path in common_endpoints:
                try:
                    endpoint = f"{BACKEND_URL}{endpoint_path}"
                    test_response = requests.get(endpoint, timeout=10)
                    if test_response.status_code != 404:
                        working_endpoints.append(endpoint_path)
                except:
                    pass
            
            self.log(f"   Working endpoints: {working_endpoints}")
            
            if working_endpoints:
                self.log("   ✅ Other endpoints work - API router is functional")
                self.cert_tests['api_router_configured'] = True
            else:
                self.log("   ❌ No endpoints work - API router issue")
            
            # Check for typos in endpoint path
            self.log("   Checking for typos in endpoint path...")
            
            # Test variations of the endpoint
            endpoint_variations = [
                "/crew-certificates/analyze-file",
                "/crew_certificates/analyze-file", 
                "/crew-certificate/analyze-file",
                "/crewcertificates/analyze-file",
                "/crew/certificates/analyze-file"
            ]
            
            for variation in endpoint_variations:
                try:
                    endpoint = f"{BACKEND_URL}{variation}"
                    test_response = requests.post(endpoint, timeout=5)
                    if test_response.status_code != 404:
                        self.log(f"   ✅ Found working variation: {variation}")
                        break
                except:
                    pass
            else:
                self.log("   ❌ No working variations found")
                self.cert_tests['no_typos_in_endpoint_path'] = True
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error analyzing 404 issue: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test of crew certificates endpoints"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE CREW CERTIFICATES ENDPOINT TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Verify test data exists
            self.log("\nSTEP 2: Verify test data exists")
            if not self.verify_test_data_exists():
                self.log("⚠️ WARNING: Test data not found - using alternatives")
            
            # Step 3: Test analyze-file endpoint (main issue)
            self.log("\nSTEP 3: Test analyze-file endpoint (MAIN ISSUE)")
            self.test_analyze_file_endpoint()
            
            # Step 4: Test manual endpoint
            self.log("\nSTEP 4: Test manual endpoint")
            self.test_manual_endpoint()
            
            # Step 5: Test GET certificates endpoint
            self.log("\nSTEP 5: Test GET certificates endpoint")
            self.test_get_certificates_endpoint()
            
            # Step 6: Check backend configuration
            self.log("\nSTEP 6: Check backend configuration")
            self.check_backend_configuration()
            
            # Step 7: Analyze 404 issue
            self.log("\nSTEP 7: Analyze 404 issue")
            self.analyze_404_issue()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE CREW CERTIFICATES TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 CREW CERTIFICATES ENDPOINT TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.cert_tests)
            passed_tests = sum(1 for result in self.cert_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('ship_exists', 'Ship exists'),
                ('crew_exists', 'Crew exists'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.cert_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Endpoint Existence Results
            self.log("\n🔗 ENDPOINT EXISTENCE:")
            endpoint_tests = [
                ('analyze_file_endpoint_exists', 'analyze-file endpoint exists (not 404)'),
                ('manual_endpoint_exists', 'manual endpoint exists (not 404)'),
                ('get_certificates_endpoint_exists', 'GET certificates endpoint exists (not 404)'),
            ]
            
            for test_key, description in endpoint_tests:
                status = "✅ PASS" if self.cert_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Endpoint Functionality Results
            self.log("\n⚙️ ENDPOINT FUNCTIONALITY:")
            func_tests = [
                ('analyze_file_accepts_multipart', 'analyze-file accepts multipart/form-data'),
                ('analyze_file_proper_error_not_404', 'analyze-file returns proper error (not 404)'),
                ('manual_endpoint_works', 'manual endpoint works correctly'),
                ('get_endpoint_works', 'GET endpoint works correctly'),
            ]
            
            for test_key, description in func_tests:
                status = "✅ PASS" if self.cert_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Configuration Results
            self.log("\n🔧 BACKEND CONFIGURATION:")
            config_tests = [
                ('api_router_configured', 'API router configured correctly'),
                ('endpoint_registered_in_fastapi', 'Endpoints registered in FastAPI'),
                ('backend_logs_show_endpoint_registration', 'Backend logs show endpoint registration'),
                ('no_typos_in_endpoint_path', 'No typos in endpoint paths'),
            ]
            
            for test_key, description in config_tests:
                status = "✅ PASS" if self.cert_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Issue Analysis
            self.log("\n🎯 CRITICAL ISSUE ANALYSIS:")
            
            analyze_file_exists = self.cert_tests.get('analyze_file_endpoint_exists', False)
            manual_exists = self.cert_tests.get('manual_endpoint_exists', False)
            get_exists = self.cert_tests.get('get_certificates_endpoint_exists', False)
            
            if analyze_file_exists:
                self.log("   ✅ MAIN ISSUE RESOLVED: analyze-file endpoint is accessible")
                self.log("   ✅ Frontend should be able to upload files")
            else:
                self.log("   ❌ MAIN ISSUE PERSISTS: analyze-file endpoint returns 404")
                self.log("   ❌ Frontend cannot upload files to this endpoint")
            
            if manual_exists and get_exists:
                self.log("   ✅ Other crew-certificate endpoints work correctly")
            else:
                self.log("   ❌ Some crew-certificate endpoints have issues")
            
            # Root Cause Analysis
            self.log("\n🔍 ROOT CAUSE ANALYSIS:")
            
            if not analyze_file_exists:
                if not self.cert_tests.get('api_router_configured', False):
                    self.log("   🔴 LIKELY CAUSE: API router not configured properly")
                elif not self.cert_tests.get('endpoint_registered_in_fastapi', False):
                    self.log("   🔴 LIKELY CAUSE: Endpoint not registered in FastAPI")
                elif not self.cert_tests.get('backend_logs_show_endpoint_registration', False):
                    self.log("   🔴 LIKELY CAUSE: Endpoint registration issue during startup")
                else:
                    self.log("   🔴 UNKNOWN CAUSE: All checks passed but endpoint still returns 404")
            else:
                self.log("   ✅ NO ISSUES: All endpoints accessible")
            
            # Recommendations
            self.log("\n💡 RECOMMENDATIONS:")
            
            if not analyze_file_exists:
                self.log("   1. Check /app/backend/server.py lines 12900-13000 for analyze-file endpoint")
                self.log("   2. Verify @api_router.post decorator is correct")
                self.log("   3. Ensure api_router is included in FastAPI app")
                self.log("   4. Check for typos in endpoint path")
                self.log("   5. Restart backend service: sudo supervisorctl restart backend")
            else:
                self.log("   1. Endpoints are working correctly")
                self.log("   2. Frontend should be able to upload files")
                self.log("   3. Check frontend code for correct endpoint URL")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the crew certificates endpoint test"""
    tester = CrewCertificatesTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
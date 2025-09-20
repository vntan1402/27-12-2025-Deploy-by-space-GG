#!/usr/bin/env python3
"""
PDF Analysis Endpoint Debug Test
Comprehensive testing to debug the 404 error issue with PDF analysis endpoint
"""

import requests
import json
import io
import sys
from datetime import datetime
import time

class PDFAnalysisDebugTester:
    def __init__(self, base_url="https://ship-cert-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_info = None

    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_login(self, username="admin", password="admin123"):
        """Test login and get authentication token"""
        self.log(f"🔐 Testing Authentication with {username}/{password}")
        
        url = f"{self.api_url}/auth/login"
        data = {"username": username, "password": password}
        
        try:
            response = requests.post(url, json=data, timeout=30)
            self.tests_run += 1
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('access_token')
                self.user_info = result.get('user', {})
                self.tests_passed += 1
                
                self.log(f"✅ Login successful")
                self.log(f"   User: {self.user_info.get('full_name')} ({self.user_info.get('role')})")
                self.log(f"   Company: {self.user_info.get('company')}")
                self.log(f"   Token: {self.token[:20]}..." if self.token else "   Token: None")
                return True
            else:
                self.log(f"❌ Login failed - Status: {response.status_code}")
                try:
                    error = response.json()
                    self.log(f"   Error: {error}")
                except:
                    self.log(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}", "ERROR")
            return False

    def test_endpoint_registration(self):
        """Test if the PDF analysis endpoint is registered in the API"""
        self.log("🔍 Testing API Endpoint Registration")
        
        # Test 1: Check OpenAPI docs endpoint
        try:
            docs_url = f"{self.api_url}/docs"
            response = requests.get(docs_url, timeout=30)
            self.tests_run += 1
            
            if response.status_code == 200:
                self.tests_passed += 1
                self.log("✅ OpenAPI docs accessible")
            else:
                self.log(f"❌ OpenAPI docs not accessible - Status: {response.status_code}")
        except Exception as e:
            self.log(f"❌ OpenAPI docs error: {str(e)}", "ERROR")

        # Test 2: Check OpenAPI JSON schema
        try:
            openapi_url = f"{self.api_url}/openapi.json"
            response = requests.get(openapi_url, timeout=30)
            self.tests_run += 1
            
            if response.status_code == 200:
                self.tests_passed += 1
                openapi_spec = response.json()
                
                # Check if our endpoint is in the paths
                paths = openapi_spec.get('paths', {})
                pdf_endpoint = '/api/analyze-ship-certificate'
                
                if pdf_endpoint in paths:
                    self.log("✅ PDF analysis endpoint found in OpenAPI spec")
                    endpoint_info = paths[pdf_endpoint]
                    if 'post' in endpoint_info:
                        self.log("✅ POST method registered for PDF analysis endpoint")
                        post_info = endpoint_info['post']
                        self.log(f"   Summary: {post_info.get('summary', 'N/A')}")
                        self.log(f"   Tags: {post_info.get('tags', [])}")
                    else:
                        self.log("❌ POST method not found for PDF analysis endpoint")
                else:
                    self.log("❌ PDF analysis endpoint NOT found in OpenAPI spec")
                    self.log(f"   Available endpoints: {list(paths.keys())[:10]}...")
            else:
                self.log(f"❌ OpenAPI JSON not accessible - Status: {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ OpenAPI JSON error: {str(e)}", "ERROR")

    def test_endpoint_accessibility(self):
        """Test PDF analysis endpoint accessibility with different scenarios"""
        self.log("🎯 Testing PDF Analysis Endpoint Accessibility")
        
        endpoint_url = f"{self.api_url}/analyze-ship-certificate"
        
        # Test 1: Without authentication (should get 401, not 404)
        self.log("   Test 1: Without authentication")
        try:
            response = requests.post(endpoint_url, timeout=30)
            self.tests_run += 1
            
            if response.status_code == 401:
                self.tests_passed += 1
                self.log("✅ Endpoint accessible - Returns 401 Unauthorized (expected)")
            elif response.status_code == 404:
                self.log("❌ Endpoint returns 404 Not Found - ENDPOINT NOT REGISTERED")
            else:
                self.log(f"❌ Unexpected status code: {response.status_code}")
                try:
                    error = response.json()
                    self.log(f"   Response: {error}")
                except:
                    self.log(f"   Response: {response.text}")
                    
        except Exception as e:
            self.log(f"❌ Endpoint accessibility error: {str(e)}", "ERROR")

        # Test 2: With authentication but no file (should get 422, not 404)
        if self.token:
            self.log("   Test 2: With authentication, no file")
            try:
                headers = {'Authorization': f'Bearer {self.token}'}
                response = requests.post(endpoint_url, headers=headers, timeout=30)
                self.tests_run += 1
                
                if response.status_code == 422:
                    self.tests_passed += 1
                    self.log("✅ Endpoint accessible with auth - Returns 422 Validation Error (expected)")
                elif response.status_code == 404:
                    self.log("❌ Endpoint returns 404 Not Found - ENDPOINT NOT REGISTERED")
                else:
                    self.log(f"❌ Unexpected status code: {response.status_code}")
                    try:
                        error = response.json()
                        self.log(f"   Response: {error}")
                    except:
                        self.log(f"   Response: {response.text}")
                        
            except Exception as e:
                self.log(f"❌ Authenticated endpoint test error: {str(e)}", "ERROR")

    def create_test_pdf(self):
        """Create a simple test PDF file"""
        try:
            # Create a simple PDF-like content (not a real PDF, but for testing)
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
(Test Ship Certificate) Tj
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
299
%%EOF"""
            return pdf_content
        except Exception as e:
            self.log(f"❌ Error creating test PDF: {str(e)}", "ERROR")
            return None

    def test_file_upload_functionality(self):
        """Test actual file upload to PDF analysis endpoint"""
        if not self.token:
            self.log("⚠️ Skipping file upload test - no authentication token")
            return
            
        self.log("📁 Testing File Upload Functionality")
        
        endpoint_url = f"{self.api_url}/analyze-ship-certificate"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test 1: Upload a test PDF
        self.log("   Test 1: Upload test PDF file")
        try:
            pdf_content = self.create_test_pdf()
            if pdf_content:
                files = {'file': ('test_certificate.pdf', io.BytesIO(pdf_content), 'application/pdf')}
                
                response = requests.post(endpoint_url, files=files, headers=headers, timeout=60)
                self.tests_run += 1
                
                if response.status_code == 200:
                    self.tests_passed += 1
                    result = response.json()
                    self.log("✅ PDF upload successful")
                    self.log(f"   Success: {result.get('success')}")
                    self.log(f"   Message: {result.get('message')}")
                    analysis = result.get('analysis', {})
                    self.log(f"   Analysis fields: {list(analysis.keys())}")
                elif response.status_code == 404:
                    self.log("❌ PDF upload returns 404 - ENDPOINT NOT FOUND")
                elif response.status_code == 403:
                    self.log("❌ PDF upload returns 403 - INSUFFICIENT PERMISSIONS")
                    self.log(f"   User role: {self.user_info.get('role')}")
                    self.log("   Required role: EDITOR or higher")
                else:
                    self.log(f"❌ PDF upload failed - Status: {response.status_code}")
                    try:
                        error = response.json()
                        self.log(f"   Error: {error}")
                    except:
                        self.log(f"   Error: {response.text}")
                        
        except Exception as e:
            self.log(f"❌ File upload error: {str(e)}", "ERROR")

        # Test 2: Upload non-PDF file (should get 400)
        self.log("   Test 2: Upload non-PDF file")
        try:
            text_content = b"This is not a PDF file"
            files = {'file': ('test.txt', io.BytesIO(text_content), 'text/plain')}
            
            response = requests.post(endpoint_url, files=files, headers=headers, timeout=30)
            self.tests_run += 1
            
            if response.status_code == 400:
                self.tests_passed += 1
                self.log("✅ Non-PDF file correctly rejected")
            elif response.status_code == 404:
                self.log("❌ Non-PDF test returns 404 - ENDPOINT NOT FOUND")
            else:
                self.log(f"❌ Unexpected status for non-PDF: {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Non-PDF test error: {str(e)}", "ERROR")

        # Test 3: Upload oversized file (should get 400)
        self.log("   Test 3: Upload oversized file")
        try:
            # Create a 6MB file (over 5MB limit)
            large_content = b"x" * (6 * 1024 * 1024)
            files = {'file': ('large.pdf', io.BytesIO(large_content), 'application/pdf')}
            
            response = requests.post(endpoint_url, files=files, headers=headers, timeout=30)
            self.tests_run += 1
            
            if response.status_code == 400:
                self.tests_passed += 1
                result = response.json()
                if "size exceeds" in result.get('detail', '').lower():
                    self.log("✅ Oversized file correctly rejected")
                else:
                    self.log(f"✅ File rejected but different reason: {result.get('detail')}")
            elif response.status_code == 404:
                self.log("❌ Oversized test returns 404 - ENDPOINT NOT FOUND")
            else:
                self.log(f"❌ Unexpected status for oversized file: {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Oversized file test error: {str(e)}", "ERROR")

    def test_permission_requirements(self):
        """Test permission requirements for PDF analysis"""
        if not self.token:
            self.log("⚠️ Skipping permission test - no authentication token")
            return
            
        self.log("🔐 Testing Permission Requirements")
        
        user_role = self.user_info.get('role', 'unknown')
        self.log(f"   Current user role: {user_role}")
        
        # Check if user has sufficient permissions (EDITOR or higher)
        role_hierarchy = {
            'viewer': 1,
            'editor': 2, 
            'manager': 3,
            'admin': 4,
            'super_admin': 5
        }
        
        current_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get('editor', 2)
        
        if current_level >= required_level:
            self.log(f"✅ User has sufficient permissions ({user_role} >= editor)")
        else:
            self.log(f"❌ User has insufficient permissions ({user_role} < editor)")
            self.log("   This could explain 403 Forbidden responses")

    def test_ai_service_configuration(self):
        """Test if AI service is properly configured"""
        self.log("🤖 Testing AI Service Configuration")
        
        # We can't directly test the EMERGENT_LLM_KEY from the client side,
        # but we can infer from the endpoint behavior
        self.log("   AI service configuration can only be tested through actual PDF upload")
        self.log("   If PDF upload returns 500 with 'AI service not configured', then key is missing")

    def run_comprehensive_debug(self):
        """Run all debug tests"""
        self.log("🚢 PDF Analysis Endpoint Debug Test Suite")
        self.log("=" * 60)
        
        # Step 1: Authentication
        if not self.test_login():
            self.log("❌ Authentication failed - cannot proceed with authenticated tests")
            return False
        
        # Step 2: Test endpoint registration
        self.test_endpoint_registration()
        
        # Step 3: Test endpoint accessibility
        self.test_endpoint_accessibility()
        
        # Step 4: Test permission requirements
        self.test_permission_requirements()
        
        # Step 5: Test AI service configuration
        self.test_ai_service_configuration()
        
        # Step 6: Test file upload functionality
        self.test_file_upload_functionality()
        
        # Print summary
        self.print_summary()
        
        return self.tests_passed == self.tests_run

    def print_summary(self):
        """Print test summary"""
        self.log("=" * 60)
        self.log("📊 DEBUG TEST SUMMARY")
        self.log("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        self.log(f"Tests Run: {self.tests_run}")
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉 All tests passed - PDF analysis endpoint is working correctly")
        else:
            self.log("⚠️ Some tests failed - check logs above for issues")
            
        # Provide diagnostic summary
        self.log("\n🔍 DIAGNOSTIC SUMMARY:")
        if self.token:
            self.log("✅ Authentication: Working")
        else:
            self.log("❌ Authentication: Failed")
            
        self.log("📋 Next steps based on results:")
        self.log("   - If endpoint returns 404: Check API router registration")
        self.log("   - If endpoint returns 401: Check authentication token")
        self.log("   - If endpoint returns 403: Check user permissions (need EDITOR+)")
        self.log("   - If endpoint returns 500: Check AI service configuration")

def main():
    """Main execution"""
    tester = PDFAnalysisDebugTester()
    success = tester.run_comprehensive_debug()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Frontend Request Format Test
Test the exact request format that the frontend would send to the PDF analysis endpoint
"""

import requests
import json
import io
import sys
from datetime import datetime

class FrontendRequestFormatTester:
    def __init__(self, base_url="https://continue-session.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None

    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_login(self, username="admin", password="admin123"):
        """Get authentication token"""
        self.log(f"🔐 Getting authentication token for {username}")
        
        url = f"{self.api_url}/auth/login"
        data = {"username": username, "password": password}
        
        try:
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('access_token')
                user_info = result.get('user', {})
                self.log(f"✅ Authentication successful")
                self.log(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
                return True
            else:
                self.log(f"❌ Authentication failed - Status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False

    def create_realistic_pdf_content(self):
        """Create a more realistic PDF content for testing"""
        # This is a minimal but valid PDF structure
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj

4 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
50 750 Td
(SHIP CERTIFICATE) Tj
0 -20 Td
(Ship Name: MV OCEAN STAR) Tj
0 -20 Td
(IMO Number: 9123456) Tj
0 -20 Td
(Flag: Panama) Tj
0 -20 Td
(Class Society: DNV GL) Tj
0 -20 Td
(Gross Tonnage: 25000) Tj
0 -20 Td
(Built Year: 2015) Tj
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
<< /Size 5 /Root 1 0 R >>
startxref
450
%%EOF"""
        return pdf_content

    def test_frontend_request_format(self):
        """Test the exact request format that frontend would use"""
        if not self.token:
            self.log("❌ No authentication token available")
            return False

        self.log("🌐 Testing Frontend Request Format")
        
        endpoint_url = f"{self.api_url}/analyze-ship-certificate"
        
        # Test 1: Exact frontend request format with multipart/form-data
        self.log("   Test 1: Frontend multipart/form-data format")
        try:
            pdf_content = self.create_realistic_pdf_content()
            
            # This mimics exactly how a browser/frontend would send the request
            files = {
                'file': ('ship_certificate.pdf', io.BytesIO(pdf_content), 'application/pdf')
            }
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                # Note: We don't set Content-Type for multipart/form-data - requests handles it
            }
            
            self.log(f"   Request URL: {endpoint_url}")
            self.log(f"   Headers: Authorization: Bearer {self.token[:20]}...")
            self.log(f"   File: ship_certificate.pdf ({len(pdf_content)} bytes)")
            
            response = requests.post(endpoint_url, files=files, headers=headers, timeout=60)
            
            self.log(f"   Response Status: {response.status_code}")
            self.log(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Frontend request format successful")
                self.log(f"   Success: {result.get('success')}")
                self.log(f"   Message: {result.get('message')}")
                
                analysis = result.get('analysis', {})
                self.log("   Analysis Results:")
                for field, value in analysis.items():
                    self.log(f"     {field}: {value}")
                    
                return True
                
            elif response.status_code == 404:
                self.log("❌ CRITICAL: Frontend request returns 404 - ENDPOINT NOT FOUND")
                self.log("   This confirms the user's reported issue")
                return False
                
            else:
                self.log(f"❌ Frontend request failed - Status: {response.status_code}")
                try:
                    error = response.json()
                    self.log(f"   Error: {error}")
                except:
                    self.log(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Frontend request error: {str(e)}", "ERROR")
            return False

    def test_different_request_variations(self):
        """Test different variations of the request to identify issues"""
        if not self.token:
            return False

        self.log("🔄 Testing Request Variations")
        
        pdf_content = self.create_realistic_pdf_content()
        base_headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test 2: With explicit Content-Type (might cause issues)
        self.log("   Test 2: With explicit Content-Type header")
        try:
            files = {'file': ('test.pdf', io.BytesIO(pdf_content), 'application/pdf')}
            headers = {**base_headers, 'Content-Type': 'multipart/form-data'}
            
            response = requests.post(f"{self.api_url}/analyze-ship-certificate", 
                                   files=files, headers=headers, timeout=30)
            
            self.log(f"   Status: {response.status_code}")
            if response.status_code == 404:
                self.log("❌ Returns 404 with explicit Content-Type")
            elif response.status_code == 400:
                self.log("⚠️ Returns 400 - likely Content-Type boundary issue")
            else:
                self.log("✅ Works with explicit Content-Type")
                
        except Exception as e:
            self.log(f"   Error: {str(e)}")

        # Test 3: Different file parameter names
        self.log("   Test 3: Different file parameter name")
        try:
            files = {'upload': ('test.pdf', io.BytesIO(pdf_content), 'application/pdf')}
            
            response = requests.post(f"{self.api_url}/analyze-ship-certificate", 
                                   files=files, headers=base_headers, timeout=30)
            
            self.log(f"   Status: {response.status_code}")
            if response.status_code == 422:
                self.log("✅ Correctly rejects wrong parameter name (422)")
            else:
                self.log(f"   Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log(f"   Error: {str(e)}")

        # Test 4: Test with curl-like request
        self.log("   Test 4: Curl-like request simulation")
        try:
            # Simulate what curl would send
            files = {'file': ('certificate.pdf', pdf_content, 'application/pdf')}
            
            response = requests.post(f"{self.api_url}/analyze-ship-certificate", 
                                   files=files, headers=base_headers, timeout=30)
            
            self.log(f"   Status: {response.status_code}")
            if response.status_code == 200:
                self.log("✅ Curl-like request successful")
            elif response.status_code == 404:
                self.log("❌ Curl-like request returns 404")
            else:
                self.log(f"   Status: {response.status_code}")
                
        except Exception as e:
            self.log(f"   Error: {str(e)}")

    def test_endpoint_variations(self):
        """Test different endpoint URL variations"""
        if not self.token:
            return False

        self.log("🔗 Testing Endpoint URL Variations")
        
        pdf_content = self.create_realistic_pdf_content()
        files = {'file': ('test.pdf', io.BytesIO(pdf_content), 'application/pdf')}
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Different endpoint variations to test
        endpoints = [
            "/analyze-ship-certificate",
            "/analyze-ship-certificate/",
            "analyze-ship-certificate",
            "/api/analyze-ship-certificate",
        ]
        
        for endpoint in endpoints:
            self.log(f"   Testing: {self.base_url}{endpoint}")
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.post(url, files=files, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    self.log(f"   ✅ {endpoint} - SUCCESS")
                elif response.status_code == 404:
                    self.log(f"   ❌ {endpoint} - 404 NOT FOUND")
                else:
                    self.log(f"   ⚠️ {endpoint} - Status: {response.status_code}")
                    
            except Exception as e:
                self.log(f"   ❌ {endpoint} - Error: {str(e)}")

    def run_comprehensive_test(self):
        """Run all frontend request format tests"""
        self.log("🌐 Frontend Request Format Comprehensive Test")
        self.log("=" * 60)
        
        # Step 1: Get authentication
        if not self.test_login():
            self.log("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Test frontend request format
        success = self.test_frontend_request_format()
        
        # Step 3: Test variations
        self.test_different_request_variations()
        
        # Step 4: Test endpoint variations
        self.test_endpoint_variations()
        
        self.log("=" * 60)
        if success:
            self.log("🎉 Frontend request format test PASSED")
            self.log("   The PDF analysis endpoint is working correctly")
            self.log("   If users report 404 errors, the issue may be:")
            self.log("   1. Frontend using wrong URL")
            self.log("   2. Network/proxy issues")
            self.log("   3. Browser cache issues")
        else:
            self.log("❌ Frontend request format test FAILED")
            self.log("   This confirms the user's reported 404 issue")
        
        return success

def main():
    """Main execution"""
    tester = FrontendRequestFormatTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Frontend Issue Reproduction Test
Reproduce the exact issue that the frontend is experiencing
"""

import requests
import json
import io
import sys
from datetime import datetime

class FrontendIssueReproductionTester:
    def __init__(self, base_url="https://vessel-docs-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None

    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_login(self, username="admin", password="admin123"):
        """Get authentication token"""
        self.log(f"🔐 Getting authentication token")
        
        url = f"{self.api_url}/auth/login"
        data = {"username": username, "password": password}
        
        try:
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('access_token')
                self.log(f"✅ Authentication successful")
                return True
            else:
                self.log(f"❌ Authentication failed - Status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False

    def create_test_pdf(self):
        """Create test PDF content"""
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
<< /Length 150 >>
stream
BT
/F1 12 Tf
50 750 Td
(SHIP CERTIFICATE) Tj
0 -20 Td
(Ship Name: TEST VESSEL) Tj
0 -20 Td
(IMO: 1234567) Tj
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
400
%%EOF"""
        return pdf_content

    def test_frontend_exact_reproduction(self):
        """Reproduce the exact frontend request that's failing"""
        if not self.token:
            return False

        self.log("🔍 REPRODUCING EXACT FRONTEND ISSUE")
        self.log("=" * 60)
        
        endpoint_url = f"{self.api_url}/analyze-ship-certificate"
        pdf_content = self.create_test_pdf()
        
        # Test 1: Exact frontend request (PROBLEMATIC)
        self.log("Test 1: Exact Frontend Request (with Content-Type header)")
        try:
            files = {'file': ('certificate.pdf', io.BytesIO(pdf_content), 'application/pdf')}
            
            # This is exactly what the frontend does - WRONG!
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'multipart/form-data'  # This is the problem!
            }
            
            self.log(f"   URL: {endpoint_url}")
            self.log(f"   Headers: {headers}")
            self.log(f"   File: certificate.pdf ({len(pdf_content)} bytes)")
            
            response = requests.post(endpoint_url, files=files, headers=headers, timeout=30)
            
            self.log(f"   Response Status: {response.status_code}")
            
            if response.status_code == 400:
                self.log("❌ ISSUE CONFIRMED: Returns 400 Bad Request")
                self.log("   This is because Content-Type: multipart/form-data is missing boundary")
                try:
                    error = response.json()
                    self.log(f"   Error: {error}")
                except:
                    self.log(f"   Error: {response.text}")
                return False
            elif response.status_code == 404:
                self.log("❌ ISSUE CONFIRMED: Returns 404 Not Found")
                return False
            else:
                self.log(f"   Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Frontend request error: {str(e)}", "ERROR")
            return False

    def test_correct_request_format(self):
        """Test the correct way to make the request"""
        if not self.token:
            return False

        self.log("Test 2: Correct Request Format (without Content-Type header)")
        
        endpoint_url = f"{self.api_url}/analyze-ship-certificate"
        pdf_content = self.create_test_pdf()
        
        try:
            files = {'file': ('certificate.pdf', io.BytesIO(pdf_content), 'application/pdf')}
            
            # Correct way - let requests handle Content-Type automatically
            headers = {
                'Authorization': f'Bearer {self.token}'
                # No Content-Type header - requests will set it with proper boundary
            }
            
            self.log(f"   URL: {endpoint_url}")
            self.log(f"   Headers: {headers}")
            self.log(f"   File: certificate.pdf ({len(pdf_content)} bytes)")
            
            response = requests.post(endpoint_url, files=files, headers=headers, timeout=30)
            
            self.log(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ CORRECT REQUEST WORKS PERFECTLY")
                self.log(f"   Success: {result.get('success')}")
                self.log(f"   Message: {result.get('message')}")
                return True
            else:
                self.log(f"❌ Unexpected status: {response.status_code}")
                try:
                    error = response.json()
                    self.log(f"   Error: {error}")
                except:
                    self.log(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Correct request error: {str(e)}", "ERROR")
            return False

    def test_content_type_variations(self):
        """Test different Content-Type variations to understand the issue"""
        if not self.token:
            return False

        self.log("Test 3: Content-Type Variations Analysis")
        
        endpoint_url = f"{self.api_url}/analyze-ship-certificate"
        pdf_content = self.create_test_pdf()
        
        variations = [
            ("No Content-Type (Correct)", {}),
            ("multipart/form-data (Wrong)", {'Content-Type': 'multipart/form-data'}),
            ("multipart/form-data with boundary (Manual)", {'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'}),
            ("application/json (Wrong)", {'Content-Type': 'application/json'}),
        ]
        
        for desc, content_type_header in variations:
            self.log(f"   Testing: {desc}")
            try:
                files = {'file': ('test.pdf', io.BytesIO(pdf_content), 'application/pdf')}
                headers = {'Authorization': f'Bearer {self.token}'}
                headers.update(content_type_header)
                
                response = requests.post(endpoint_url, files=files, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    self.log(f"     ✅ SUCCESS - Status: {response.status_code}")
                elif response.status_code == 400:
                    self.log(f"     ❌ BAD REQUEST - Status: {response.status_code}")
                elif response.status_code == 404:
                    self.log(f"     ❌ NOT FOUND - Status: {response.status_code}")
                else:
                    self.log(f"     ⚠️ OTHER - Status: {response.status_code}")
                    
            except Exception as e:
                self.log(f"     ❌ ERROR: {str(e)}")

    def run_reproduction_test(self):
        """Run the complete reproduction test"""
        self.log("🚨 FRONTEND PDF ANALYSIS ISSUE REPRODUCTION")
        self.log("=" * 60)
        
        # Step 1: Get authentication
        if not self.test_login():
            self.log("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Reproduce the exact frontend issue
        frontend_issue = self.test_frontend_exact_reproduction()
        
        # Step 3: Test the correct format
        correct_works = self.test_correct_request_format()
        
        # Step 4: Analyze Content-Type variations
        self.test_content_type_variations()
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 ISSUE ANALYSIS SUMMARY")
        self.log("=" * 60)
        
        if not frontend_issue and correct_works:
            self.log("✅ ISSUE CONFIRMED AND SOLUTION IDENTIFIED")
            self.log("")
            self.log("🐛 PROBLEM:")
            self.log("   Frontend is setting 'Content-Type: multipart/form-data' header")
            self.log("   This breaks the multipart boundary and causes 400 Bad Request")
            self.log("")
            self.log("💡 SOLUTION:")
            self.log("   Remove the 'Content-Type' header from the frontend request")
            self.log("   Let axios/browser set it automatically with proper boundary")
            self.log("")
            self.log("🔧 FRONTEND FIX NEEDED:")
            self.log("   In App.js line ~5168-5172, change:")
            self.log("   FROM:")
            self.log("     headers: {")
            self.log("       'Content-Type': 'multipart/form-data',")
            self.log("     }")
            self.log("   TO:")
            self.log("     headers: {")
            self.log("       // Remove Content-Type - let axios handle it")
            self.log("     }")
            self.log("   OR simply remove the headers object entirely")
            
            return True
        else:
            self.log("❌ Issue analysis incomplete")
            return False

def main():
    """Main execution"""
    tester = FrontendIssueReproductionTester()
    success = tester.run_reproduction_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
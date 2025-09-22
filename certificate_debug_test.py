#!/usr/bin/env python3
"""
Certificate Upload Auto-Fill Issue Debug Test
Testing the backend certificate analysis API directly as requested in the review.

This test will:
1. Login as admin1/123456
2. Test the certificate analysis endpoint with the specific PDF file
3. Log the complete API response structure
4. Compare with expected data to identify data mapping issues
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials as specified in review request
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

# PDF file URL from review request
PDF_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/swohyuf9_SS%20STAR%20PM252494416_ImagePDF.pdf"

# Expected data from review request
EXPECTED_DATA = {
    "certificate_name": "Safety Management Certificate",
    "certificate_number": "PM252494416", 
    "issue_date": "August 22, 2025",
    "valid_until": "January 21, 2026",
    "issued_by": "Panama Maritime Documentation Services"
}

class CertificateAnalysisDebugger:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()
    
    def authenticate(self):
        """Authenticate with admin1/123456 credentials"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                
                user_role = self.user_info.get('role', '').upper()
                username = self.user_info.get('username', '')
                
                self.log_test("Authentication Test", True, 
                            f"Logged in as {username} with role {user_role}")
                return True
            else:
                self.log_test("Authentication Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication Test", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def download_pdf_file(self):
        """Download the PDF file from the provided URL"""
        try:
            print(f"📥 Downloading PDF file from: {PDF_URL}")
            response = requests.get(PDF_URL, timeout=30)
            
            if response.status_code == 200:
                file_size = len(response.content)
                self.log_test("PDF Download Test", True, 
                            f"Downloaded PDF file successfully. Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                return response.content
            else:
                self.log_test("PDF Download Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("PDF Download Test", False, error=str(e))
            return None
    
    def find_certificate_analysis_endpoints(self):
        """Find available certificate analysis endpoints"""
        try:
            # Test common endpoint patterns
            endpoints_to_test = [
                "/analyze-pdf",
                "/analyze-certificate", 
                "/analyze-ship-certificate",
                "/certificates/analyze",
                "/certificates/analyze-pdf",
                "/ai/analyze-certificate",
                "/ai/analyze-pdf"
            ]
            
            available_endpoints = []
            
            for endpoint in endpoints_to_test:
                try:
                    # Test with OPTIONS request first
                    response = requests.options(f"{API_BASE}{endpoint}", headers=self.get_headers())
                    if response.status_code in [200, 405]:  # 405 means method not allowed but endpoint exists
                        available_endpoints.append(endpoint)
                except:
                    pass
            
            if available_endpoints:
                self.log_test("Certificate Analysis Endpoints Discovery", True, 
                            f"Found potential endpoints: {', '.join(available_endpoints)}")
                return available_endpoints
            else:
                self.log_test("Certificate Analysis Endpoints Discovery", False, 
                            error="No certificate analysis endpoints found")
                return []
                
        except Exception as e:
            self.log_test("Certificate Analysis Endpoints Discovery", False, error=str(e))
            return []
    
    def test_analyze_ship_certificate_endpoint(self, pdf_content):
        """Test the /analyze-ship-certificate endpoint with the PDF file"""
        try:
            endpoint = f"{API_BASE}/analyze-ship-certificate"
            
            # Prepare file for upload
            files = {
                'file': ('SS_STAR_PM252494416_ImagePDF.pdf', pdf_content, 'application/pdf')
            }
            
            print(f"🔍 Testing endpoint: {endpoint}")
            print(f"📄 File size: {len(pdf_content):,} bytes")
            
            response = requests.post(
                endpoint,
                files=files,
                headers=self.get_headers(),
                timeout=60  # Allow more time for AI analysis
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Log the complete API response structure
                print("=" * 80)
                print("🔍 COMPLETE API RESPONSE STRUCTURE:")
                print("=" * 80)
                print(json.dumps(result, indent=2, default=str))
                print("=" * 80)
                
                # Extract analysis data
                analysis_data = result.get('analysis', {})
                
                # Compare with expected data
                comparison_results = self.compare_with_expected_data(analysis_data)
                
                self.log_test("Certificate Analysis API Test", True, 
                            f"API call successful. Analysis data extracted: {len(analysis_data)} fields")
                
                return result, comparison_results
            else:
                error_text = response.text
                self.log_test("Certificate Analysis API Test", False, 
                            error=f"Status: {response.status_code}, Response: {error_text}")
                return None, None
                
        except Exception as e:
            self.log_test("Certificate Analysis API Test", False, error=str(e))
            return None, None
    
    def compare_with_expected_data(self, analysis_data):
        """Compare extracted data with expected data"""
        try:
            print("=" * 80)
            print("📋 DATA COMPARISON: EXPECTED vs ACTUAL")
            print("=" * 80)
            
            comparison_results = {}
            
            # Map expected fields to possible API response fields
            field_mappings = {
                "certificate_name": ["cert_name", "certificate_name", "name", "cert_type"],
                "certificate_number": ["cert_no", "certificate_number", "cert_number", "number"],
                "issue_date": ["issue_date", "issued_date", "issuance_date", "date_issued"],
                "valid_until": ["valid_date", "expiry_date", "expiration_date", "valid_until"],
                "issued_by": ["issued_by", "issuer", "authority", "organization"]
            }
            
            for expected_field, expected_value in EXPECTED_DATA.items():
                print(f"\n🔍 {expected_field.upper()}:")
                print(f"   Expected: {expected_value}")
                
                # Find matching field in analysis data
                found_value = None
                found_field = None
                
                possible_fields = field_mappings.get(expected_field, [expected_field])
                for field in possible_fields:
                    if field in analysis_data:
                        found_value = analysis_data[field]
                        found_field = field
                        break
                
                if found_value:
                    print(f"   Actual:   {found_value} (field: {found_field})")
                    
                    # Check if values match (case insensitive)
                    if str(expected_value).lower().strip() == str(found_value).lower().strip():
                        print(f"   Status:   ✅ MATCH")
                        comparison_results[expected_field] = {"status": "match", "expected": expected_value, "actual": found_value}
                    else:
                        print(f"   Status:   ❌ MISMATCH")
                        comparison_results[expected_field] = {"status": "mismatch", "expected": expected_value, "actual": found_value}
                else:
                    print(f"   Actual:   NOT FOUND")
                    print(f"   Status:   ❌ MISSING")
                    comparison_results[expected_field] = {"status": "missing", "expected": expected_value, "actual": None}
            
            # Show all available fields in analysis data
            print(f"\n📊 ALL AVAILABLE FIELDS IN ANALYSIS DATA:")
            for field, value in analysis_data.items():
                print(f"   {field}: {value}")
            
            print("=" * 80)
            
            return comparison_results
            
        except Exception as e:
            print(f"❌ Error in data comparison: {e}")
            return {}
    
    def test_alternative_endpoints(self, pdf_content, available_endpoints):
        """Test alternative certificate analysis endpoints"""
        results = {}
        
        for endpoint in available_endpoints:
            if endpoint == "/analyze-ship-certificate":
                continue  # Already tested
                
            try:
                full_endpoint = f"{API_BASE}{endpoint}"
                
                files = {
                    'file': ('SS_STAR_PM252494416_ImagePDF.pdf', pdf_content, 'application/pdf')
                }
                
                response = requests.post(
                    full_endpoint,
                    files=files,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results[endpoint] = {"success": True, "data": result}
                    self.log_test(f"Alternative Endpoint Test: {endpoint}", True, 
                                f"Response received with {len(result)} fields")
                else:
                    results[endpoint] = {"success": False, "status": response.status_code, "error": response.text}
                    self.log_test(f"Alternative Endpoint Test: {endpoint}", False, 
                                error=f"Status: {response.status_code}")
                    
            except Exception as e:
                results[endpoint] = {"success": False, "error": str(e)}
                self.log_test(f"Alternative Endpoint Test: {endpoint}", False, error=str(e))
        
        return results
    
    def run_debug_test(self):
        """Run the complete certificate analysis debug test"""
        print("🔍 CERTIFICATE UPLOAD AUTO-FILL ISSUE DEBUG TEST")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test User: {TEST_USERNAME}")
        print(f"PDF URL: {PDF_URL}")
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Download PDF file
        pdf_content = self.download_pdf_file()
        if not pdf_content:
            print("❌ PDF download failed. Cannot proceed with analysis.")
            return False
        
        # Step 3: Find available certificate analysis endpoints
        available_endpoints = self.find_certificate_analysis_endpoints()
        
        # Step 4: Test the main certificate analysis endpoint
        analysis_result, comparison_results = self.test_analyze_ship_certificate_endpoint(pdf_content)
        
        # Step 5: Test alternative endpoints if available
        if available_endpoints:
            alternative_results = self.test_alternative_endpoints(pdf_content, available_endpoints)
        
        # Step 6: Generate summary report
        print("=" * 80)
        print("📊 DEBUG TEST SUMMARY REPORT")
        print("=" * 80)
        
        if analysis_result:
            print("✅ Certificate analysis API is accessible and working")
            print("✅ PDF file was processed successfully")
            
            if comparison_results:
                matches = sum(1 for r in comparison_results.values() if r["status"] == "match")
                total = len(comparison_results)
                print(f"📊 Data accuracy: {matches}/{total} fields match expected values")
                
                if matches < total:
                    print("\n❌ DATA MAPPING ISSUES IDENTIFIED:")
                    for field, result in comparison_results.items():
                        if result["status"] != "match":
                            print(f"   - {field}: {result['status'].upper()} (expected: {result['expected']}, actual: {result.get('actual', 'N/A')})")
                    
                    print("\n🔧 RECOMMENDED FIXES:")
                    print("   1. Check AI extraction prompt for certificate field mapping")
                    print("   2. Verify field name mapping between backend and frontend")
                    print("   3. Review date format parsing and conversion")
                    print("   4. Check organization name standardization")
                else:
                    print("✅ All expected data fields match - no data mapping issues detected")
            
        else:
            print("❌ Certificate analysis API failed or is not accessible")
            print("🔧 RECOMMENDED ACTIONS:")
            print("   1. Check if the endpoint exists and is properly configured")
            print("   2. Verify AI configuration is set up correctly")
            print("   3. Check backend logs for detailed error information")
        
        # Summary statistics
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"\n📈 TEST STATISTICS:")
        print(f"   Total Tests: {total}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {total - passed}")
        print(f"   Success Rate: {(passed/total)*100:.1f}%")
        
        return analysis_result is not None

def main():
    """Main test execution"""
    debugger = CertificateAnalysisDebugger()
    success = debugger.run_debug_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
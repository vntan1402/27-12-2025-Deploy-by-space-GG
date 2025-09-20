#!/usr/bin/env python3
"""
Certificate Multi-Upload Analysis Test
Testing the correct endpoint for certificate analysis as identified in the debug.

The issue is that the user is trying to use /analyze-ship-certificate (for ship auto-fill)
but should be using /certificates/multi-upload (for certificate auto-fill).
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ship-cert-manager-1.preview.emergentagent.com')
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

class CertificateMultiUploadTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.ship_id = None
        
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
    
    def get_test_ship(self):
        """Get a test ship for certificate upload"""
        try:
            response = requests.get(f"{API_BASE}/ships", headers=self.get_headers())
            
            if response.status_code == 200:
                ships = response.json()
                if ships:
                    # Look for SUNSHINE STAR ship first
                    for ship in ships:
                        if "SUNSHINE STAR" in ship.get('name', '').upper():
                            self.ship_id = ship['id']
                            self.log_test("Test Ship Selection", True, 
                                        f"Found SUNSHINE STAR ship: {ship['name']} (ID: {self.ship_id})")
                            return True
                    
                    # Fallback to first ship
                    self.ship_id = ships[0]['id']
                    self.log_test("Test Ship Selection", True, 
                                f"Using first available ship: {ships[0]['name']} (ID: {self.ship_id})")
                    return True
                else:
                    self.log_test("Test Ship Selection", False, 
                                error="No ships found in database")
                    return False
            else:
                self.log_test("Test Ship Selection", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Test Ship Selection", False, error=str(e))
            return False
    
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
    
    def test_certificate_multi_upload(self, pdf_content):
        """Test the /certificates/multi-upload endpoint with the PDF file"""
        try:
            endpoint = f"{API_BASE}/certificates/multi-upload"
            
            # Prepare file for upload
            files = {
                'files': ('SS_STAR_PM252494416_ImagePDF.pdf', pdf_content, 'application/pdf')
            }
            
            params = {
                'ship_id': self.ship_id
            }
            
            print(f"🔍 Testing endpoint: {endpoint}")
            print(f"📄 File size: {len(pdf_content):,} bytes")
            print(f"🚢 Ship ID: {self.ship_id}")
            
            response = requests.post(
                endpoint,
                files=files,
                params=params,
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
                
                # Extract analysis data from results
                results = result.get('results', [])
                if results:
                    analysis_data = results[0].get('analysis', {})
                    
                    # Compare with expected data
                    comparison_results = self.compare_with_expected_data(analysis_data)
                    
                    self.log_test("Certificate Multi-Upload API Test", True, 
                                f"API call successful. Analysis data extracted: {len(analysis_data)} fields")
                    
                    return result, comparison_results
                else:
                    self.log_test("Certificate Multi-Upload API Test", False, 
                                error="No results found in response")
                    return result, None
            else:
                error_text = response.text
                self.log_test("Certificate Multi-Upload API Test", False, 
                            error=f"Status: {response.status_code}, Response: {error_text}")
                return None, None
                
        except Exception as e:
            self.log_test("Certificate Multi-Upload API Test", False, error=str(e))
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
                "certificate_name": ["cert_name", "certificate_name", "name"],
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
    
    def run_certificate_analysis_test(self):
        """Run the complete certificate analysis test"""
        print("🔍 CERTIFICATE UPLOAD AUTO-FILL ISSUE DEBUG TEST")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test User: {TEST_USERNAME}")
        print(f"PDF URL: {PDF_URL}")
        print()
        print("🎯 TESTING CORRECT ENDPOINT: /certificates/multi-upload")
        print("   (NOT /analyze-ship-certificate which is for ship auto-fill)")
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Get test ship
        if not self.get_test_ship():
            print("❌ No test ship available. Cannot proceed with certificate upload.")
            return False
        
        # Step 3: Download PDF file
        pdf_content = self.download_pdf_file()
        if not pdf_content:
            print("❌ PDF download failed. Cannot proceed with analysis.")
            return False
        
        # Step 4: Test the certificate multi-upload endpoint
        analysis_result, comparison_results = self.test_certificate_multi_upload(pdf_content)
        
        # Step 5: Generate summary report
        print("=" * 80)
        print("📊 DEBUG TEST SUMMARY REPORT")
        print("=" * 80)
        
        if analysis_result:
            print("✅ Certificate multi-upload API is accessible and working")
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
                    
                    print("\n🔧 ROOT CAUSE ANALYSIS:")
                    print("   1. User is using WRONG ENDPOINT for certificate auto-fill")
                    print("   2. /analyze-ship-certificate extracts SHIP information (for ship forms)")
                    print("   3. /certificates/multi-upload extracts CERTIFICATE information (for certificate forms)")
                    print("   4. Frontend should call /certificates/multi-upload for certificate auto-fill")
                    
                    print("\n🔧 RECOMMENDED FIXES:")
                    print("   1. Update frontend to use /certificates/multi-upload endpoint")
                    print("   2. Modify frontend form field mapping for certificate data")
                    print("   3. Update UI to handle multi-upload response format")
                    print("   4. Test certificate auto-fill with correct endpoint")
                else:
                    print("✅ All expected data fields match - certificate analysis working correctly!")
            
        else:
            print("❌ Certificate multi-upload API failed or is not accessible")
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
    tester = CertificateMultiUploadTester()
    success = tester.run_certificate_analysis_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
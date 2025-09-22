#!/usr/bin/env python3
"""
Certificate Name Issue Debug Test
Testing the specific issue where:
- AI analysis extracts correct certificate name: "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE"
- But database shows: "Maritime Certificate - SUNSHINE_01_CSSC_PM25385" 
- Frontend displays: "M" (truncated)

Focus on:
1. POST /api/certificates/multi-upload with SUNSHINE PDF
2. AI Analysis response - check cert_name field
3. Certificate creation logic in create_certificate_from_analysis_with_notes()
4. Identify where "Maritime Certificate - filename" format comes from
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

# SUNSHINE ship ID from review request
SUNSHINE_SHIP_ID = "e21c71a2-9543-4f92-990c-72f54292fde8"

# PDF URL from review request
SUNSHINE_PDF_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/s6nh3s3p_SUNSHINE_01_ImagePDF.pdf"

class CertificateNameDebugTester:
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
        """Authenticate with admin1 credentials"""
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
                self.log_test("Authentication Test", True, 
                            f"Logged in as {self.user_info['username']} ({user_role})")
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
    
    def download_sunshine_pdf(self):
        """Download the SUNSHINE PDF file for testing"""
        try:
            print(f"📥 Downloading SUNSHINE PDF from: {SUNSHINE_PDF_URL}")
            response = requests.get(SUNSHINE_PDF_URL)
            
            if response.status_code == 200:
                pdf_content = response.content
                file_size = len(pdf_content)
                
                # Save to local file for reference
                with open("/app/SUNSHINE_01_CSSC_PM25385.pdf", "wb") as f:
                    f.write(pdf_content)
                
                self.log_test("PDF Download Test", True, 
                            f"Downloaded {file_size:,} bytes successfully")
                return pdf_content
            else:
                self.log_test("PDF Download Test", False, 
                            error=f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("PDF Download Test", False, error=str(e))
            return None
    
    def verify_sunshine_ship(self):
        """Verify SUNSHINE ship exists with correct ID"""
        try:
            response = requests.get(f"{API_BASE}/ships/{SUNSHINE_SHIP_ID}", 
                                  headers=self.get_headers())
            
            if response.status_code == 200:
                ship_data = response.json()
                ship_name = ship_data.get('name', 'Unknown')
                
                self.log_test("SUNSHINE Ship Verification", True, 
                            f"Ship found: {ship_name} (ID: {SUNSHINE_SHIP_ID})")
                return True
            else:
                self.log_test("SUNSHINE Ship Verification", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SUNSHINE Ship Verification", False, error=str(e))
            return False
    
    def test_multi_cert_upload_with_detailed_analysis(self, pdf_content):
        """Test POST /api/certificates/multi-upload with detailed AI analysis logging"""
        try:
            print(f"🔍 TESTING MULTI-CERT UPLOAD WITH DETAILED AI ANALYSIS")
            print(f"📤 Uploading PDF to ship: {SUNSHINE_SHIP_ID}")
            print(f"📄 File size: {len(pdf_content):,} bytes")
            
            # Prepare the multipart form data
            files = {
                'files': ('SUNSHINE_01_CSSC_PM25385.pdf', pdf_content, 'application/pdf')
            }
            
            # Make the API request
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload?ship_id={SUNSHINE_SHIP_ID}",
                files=files,
                headers=self.get_headers()
            )
            processing_time = time.time() - start_time
            
            print(f"⏱️ Processing time: {processing_time:.2f} seconds")
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Print full response for debugging
                print(f"\n🔍 FULL API RESPONSE:")
                print(json.dumps(data, indent=2, default=str))
                
                # Analyze the results
                results = data.get('results', [])
                summary = data.get('summary', {})
                
                print(f"\n📊 UPLOAD SUMMARY:")
                print(f"  Total files: {summary.get('total_files', 0)}")
                print(f"  Marine certificates: {summary.get('marine_certificates', 0)}")
                print(f"  Successfully created: {summary.get('successfully_created', 0)}")
                print(f"  Errors: {summary.get('errors', 0)}")
                
                # Focus on the first result (our PDF)
                if results:
                    result = results[0]
                    print(f"\n🎯 DETAILED ANALYSIS OF FIRST RESULT:")
                    print(f"  Filename: {result.get('filename')}")
                    print(f"  Status: {result.get('status')}")
                    print(f"  Message: {result.get('message')}")
                    
                    # Check AI analysis data
                    analysis = result.get('analysis', {})
                    if analysis:
                        print(f"\n🤖 AI ANALYSIS RESULTS:")
                        print(f"  Category: {analysis.get('category')}")
                        print(f"  Certificate Name: '{analysis.get('cert_name')}'")
                        print(f"  Certificate Number: '{analysis.get('cert_no')}'")
                        print(f"  Issue Date: {analysis.get('issue_date')}")
                        print(f"  Valid Date: {analysis.get('valid_date')}")
                        print(f"  Issued By: '{analysis.get('issued_by')}'")
                        print(f"  Ship Name: '{analysis.get('ship_name')}'")
                        print(f"  Confidence: {analysis.get('confidence')}")
                        
                        # Check if cert_name is correct
                        cert_name = analysis.get('cert_name', '')
                        expected_name = "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE"
                        
                        if expected_name.upper() in cert_name.upper():
                            print(f"  ✅ Certificate name contains expected text")
                        else:
                            print(f"  ❌ Certificate name does NOT contain expected text")
                            print(f"      Expected: {expected_name}")
                            print(f"      Got: {cert_name}")
                    
                    # Check certificate creation result
                    certificate = result.get('certificate', {})
                    if certificate:
                        print(f"\n📋 CERTIFICATE CREATION RESULT:")
                        print(f"  Success: {certificate.get('success')}")
                        print(f"  Certificate ID: {certificate.get('id')}")
                        print(f"  Certificate Name: '{certificate.get('cert_name')}'")
                        print(f"  Ship Name: '{certificate.get('ship_name')}'")
                        
                        # Check if database name matches AI analysis
                        db_cert_name = certificate.get('cert_name', '')
                        ai_cert_name = analysis.get('cert_name', '')
                        
                        if db_cert_name == ai_cert_name:
                            print(f"  ✅ Database cert_name matches AI analysis")
                        else:
                            print(f"  ❌ Database cert_name DIFFERS from AI analysis")
                            print(f"      AI Analysis: '{ai_cert_name}'")
                            print(f"      Database: '{db_cert_name}'")
                
                # Check for the problematic "Maritime Certificate - filename" pattern
                certificates_created = summary.get('certificates_created', [])
                if certificates_created:
                    print(f"\n📝 CERTIFICATES CREATED IN DATABASE:")
                    for cert in certificates_created:
                        cert_name = cert.get('cert_name', '')
                        filename = cert.get('filename', '')
                        
                        print(f"  Certificate: '{cert_name}'")
                        print(f"  Filename: '{filename}'")
                        print(f"  Certificate ID: {cert.get('certificate_id')}")
                        
                        # Check for the problematic pattern
                        if cert_name.startswith("Maritime Certificate -"):
                            print(f"  ❌ FOUND PROBLEMATIC PATTERN: Certificate name starts with 'Maritime Certificate -'")
                            print(f"      This suggests filename-based naming instead of AI extraction")
                        else:
                            print(f"  ✅ Certificate name does not use filename-based pattern")
                
                self.log_test("Multi-Cert Upload with AI Analysis", True,
                            f"Upload successful, processed {len(results)} files")
                return True
                
            else:
                self.log_test("Multi-Cert Upload with AI Analysis", False,
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Multi-Cert Upload with AI Analysis", False, error=str(e))
            return False
    
    def verify_certificate_in_database(self):
        """Verify the created certificate in the database"""
        try:
            # Get certificates for SUNSHINE ship
            response = requests.get(f"{API_BASE}/ships/{SUNSHINE_SHIP_ID}/certificates", 
                                  headers=self.get_headers())
            
            if response.status_code == 200:
                certificates = response.json()
                
                print(f"\n📋 CERTIFICATES IN DATABASE FOR SUNSHINE SHIP:")
                print(f"  Total certificates: {len(certificates)}")
                
                # Look for recently created certificates
                recent_certs = []
                for cert in certificates:
                    cert_name = cert.get('cert_name', '')
                    created_at = cert.get('created_at', '')
                    
                    print(f"\n  Certificate: '{cert_name}'")
                    print(f"    ID: {cert.get('id')}")
                    print(f"    Number: {cert.get('cert_no')}")
                    print(f"    Created: {created_at}")
                    print(f"    File Name: {cert.get('file_name')}")
                    
                    # Check for problematic patterns
                    if cert_name.startswith("Maritime Certificate -"):
                        print(f"    ❌ PROBLEMATIC: Uses 'Maritime Certificate -' pattern")
                        recent_certs.append(cert)
                    elif "CARGO SHIP SAFETY CONSTRUCTION" in cert_name.upper():
                        print(f"    ✅ CORRECT: Contains expected certificate name")
                        recent_certs.append(cert)
                
                if recent_certs:
                    self.log_test("Database Certificate Verification", True,
                                f"Found {len(recent_certs)} relevant certificates")
                else:
                    self.log_test("Database Certificate Verification", False,
                                error="No relevant certificates found in database")
                
                return True
                
            else:
                self.log_test("Database Certificate Verification", False,
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Database Certificate Verification", False, error=str(e))
            return False
    
    def run_debug_tests(self):
        """Run all debug tests for certificate name issue"""
        print("🔍 CERTIFICATE NAME ISSUE DEBUG TESTING")
        print("=" * 80)
        print("PROBLEM: AI extracts correct name but database shows 'Maritime Certificate - filename'")
        print("FOCUS: Multi-cert upload workflow and certificate creation logic")
        print("=" * 80)
        
        # Run tests in sequence
        tests = [
            self.authenticate,
            self.verify_sunshine_ship,
            lambda: self.test_multi_cert_upload_with_detailed_analysis(self.download_sunshine_pdf()),
            self.verify_certificate_in_database
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
                # Continue with other tests even if one fails
        
        # Summary
        print("=" * 80)
        print(f"📊 DEBUG TEST SUMMARY: {passed_tests}/{len(tests)} tests passed")
        
        if passed_tests >= 3:  # At least authentication, ship verification, and upload should work
            print("🎯 DEBUG TESTING COMPLETED - Check detailed logs above for root cause analysis")
        else:
            print(f"⚠️ {len(tests) - passed_tests} critical tests failed - Review required")
        
        # Detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
            if result['error']:
                print(f"    ERROR: {result['error']}")
        
        return passed_tests >= 3

def main():
    """Main test execution"""
    tester = CertificateNameDebugTester()
    success = tester.run_debug_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
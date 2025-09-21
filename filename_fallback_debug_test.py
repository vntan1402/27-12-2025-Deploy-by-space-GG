#!/usr/bin/env python3
"""
Filename-Based Fallback Debug Test - Critical Issue Investigation
Testing the specific issue where AI analysis is using filename-based fallback instead of real PDF extraction.

CRITICAL DEBUG REQUIREMENTS from Review Request:
1. Login as admin/admin123
2. Test certificate analysis with EXACT PDF file: SUNSHINE_01_ImagePDF.pdf
3. Debug OCR processor and AI analysis pipeline
4. Check if OCR is extracting text (~2,479 characters expected)
5. Examine backend logs for text extraction results

Expected vs Actual Data:
- WRONG (Current): Certificate Name: "Maritime Certificate - SUNSHINE_01_ImagePDF"
- CORRECT (Expected): Certificate Name: "International Tonnage Certificate (1969)"
- WRONG (Current): Certificate Number: "CERT_SUNSHINE_01_IMAGEPDF" 
- CORRECT (Expected): Certificate Number: "PM242868"
- WRONG (Current): Issued By: "Maritime Authority (Filename-based classification)"
- CORRECT (Expected): Issued By: "Government of Belize, issued by Panama Maritime Documentation Services Inc."
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import io
from pathlib import Path
import urllib.request

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ship-cert-manager-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

# Exact PDF file from review request
PDF_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/s6nh3s3p_SUNSHINE_01_ImagePDF.pdf"

class FilenameFallbackDebugTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.test_ship_id = None
        self.pdf_content = None
        self.pdf_filename = "SUNSHINE_01_ImagePDF.pdf"
        
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
        """Authenticate with admin/admin123 credentials"""
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
    
    def download_exact_pdf(self):
        """Download the exact PDF file from the review request"""
        try:
            print(f"📥 Downloading PDF from: {PDF_URL}")
            
            # Download the PDF file
            with urllib.request.urlopen(PDF_URL) as response:
                self.pdf_content = response.read()
            
            file_size = len(self.pdf_content)
            self.log_test("PDF Download Test", True, 
                        f"Downloaded {self.pdf_filename} - Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            return True
            
        except Exception as e:
            self.log_test("PDF Download Test", False, error=str(e))
            return False
    
    def find_test_ship(self):
        """Find a ship for testing (preferably SUNSHINE)"""
        try:
            response = requests.get(f"{API_BASE}/ships", headers=self.get_headers())
            
            if response.status_code == 200:
                ships = response.json()
                
                # Look for SUNSHINE ship first
                sunshine_ship = None
                for ship in ships:
                    ship_name = ship.get('name', '').upper()
                    if 'SUNSHINE' in ship_name:
                        sunshine_ship = ship
                        break
                
                if sunshine_ship:
                    self.test_ship_id = sunshine_ship['id']
                    ship_name = sunshine_ship['name']
                    self.log_test("Find Test Ship", True, 
                                f"Found SUNSHINE ship: {ship_name} (ID: {self.test_ship_id})")
                    return True
                elif ships:
                    # Use first available ship if SUNSHINE not found
                    self.test_ship_id = ships[0]['id']
                    ship_name = ships[0]['name']
                    self.log_test("Find Test Ship", True, 
                                f"SUNSHINE ship not found, using: {ship_name} (ID: {self.test_ship_id})")
                    return True
                else:
                    self.log_test("Find Test Ship", False, 
                                error="No ships found in database")
                    return False
            else:
                self.log_test("Find Test Ship", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Find Test Ship", False, error=str(e))
            return False
    
    def test_certificate_analysis_direct(self):
        """Test the /api/analyze-ship-certificate endpoint directly with exact PDF"""
        try:
            if not self.pdf_content:
                self.log_test("Certificate Analysis Direct Test", False, 
                            error="PDF content not available")
                return None
            
            print("🔍 Testing /api/analyze-ship-certificate endpoint with exact PDF...")
            
            # Prepare the file for upload
            files = {
                'file': (self.pdf_filename, io.BytesIO(self.pdf_content), 'application/pdf')
            }
            
            # Call the analysis endpoint
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract analysis data
                success = result.get('success', False)
                analysis_data = result.get('data', {}).get('analysis', {})
                processing_info = result.get('data', {}).get('processing', {})
                
                # Check for filename-based vs real extraction
                ship_name = analysis_data.get('ship_name', '')
                cert_name = analysis_data.get('cert_name', '')
                cert_number = analysis_data.get('cert_no', '')
                issued_by = analysis_data.get('issued_by', '')
                
                print(f"    📋 Analysis Results:")
                print(f"       Ship Name: '{ship_name}'")
                print(f"       Certificate Name: '{cert_name}'")
                print(f"       Certificate Number: '{cert_number}'")
                print(f"       Issued By: '{issued_by}'")
                
                # Check for filename-based fallback indicators
                filename_based_indicators = [
                    'SUNSHINE_01_ImagePDF' in str(cert_name),
                    'CERT_SUNSHINE_01_IMAGEPDF' in str(cert_number),
                    'Maritime Certificate - SUNSHINE_01_ImagePDF' in str(cert_name),
                    'Filename-based classification' in str(issued_by),
                    'Maritime Authority (Filename-based classification)' in str(issued_by)
                ]
                
                # Check for real extraction indicators
                real_extraction_indicators = [
                    'tonnage' in str(cert_name).lower(),
                    'international' in str(cert_name).lower(),
                    'PM242868' in str(cert_number),
                    'PM242' in str(cert_number),  # Partial match
                    'belize' in str(issued_by).lower(),
                    'panama' in str(issued_by).lower(),
                    'government' in str(issued_by).lower()
                ]
                
                if any(filename_based_indicators):
                    self.log_test("Certificate Analysis Direct Test", False, 
                                f"❌ CRITICAL ISSUE CONFIRMED: AI analysis using filename-based fallback!\n"
                                f"    Certificate Name: '{cert_name}'\n"
                                f"    Certificate Number: '{cert_number}'\n"
                                f"    Issued By: '{issued_by}'\n"
                                f"    Expected: 'International Tonnage Certificate (1969)', 'PM242868', 'Government of Belize'")
                    return result
                elif any(real_extraction_indicators):
                    self.log_test("Certificate Analysis Direct Test", True, 
                                f"✅ SUCCESS: Real PDF extraction working!\n"
                                f"    Certificate Name: '{cert_name}'\n"
                                f"    Certificate Number: '{cert_number}'\n"
                                f"    Issued By: '{issued_by}'\n"
                                f"    Ship Name: '{ship_name}'")
                    return result
                else:
                    self.log_test("Certificate Analysis Direct Test", False, 
                                f"⚠️ UNCLEAR: Analysis completed but data doesn't match expected patterns\n"
                                f"    Certificate Name: '{cert_name}'\n"
                                f"    Certificate Number: '{cert_number}'\n"
                                f"    Issued By: '{issued_by}'\n"
                                f"    Ship Name: '{ship_name}'\n"
                                f"    This may indicate OCR extraction failed or returned unexpected data")
                    return result
                
            else:
                self.log_test("Certificate Analysis Direct Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Certificate Analysis Direct Test", False, error=str(e))
            return None
    
    def test_multi_upload_with_exact_pdf(self):
        """Test multi-upload endpoint with the exact PDF file"""
        try:
            if not self.pdf_content or not self.test_ship_id:
                self.log_test("Multi-Upload Test", False, 
                            error="PDF content or ship ID not available")
                return None
            
            print("🔍 Testing /api/certificates/multi-upload with exact PDF...")
            
            # Prepare the file for upload
            files = [
                ('files', (self.pdf_filename, io.BytesIO(self.pdf_content), 'application/pdf'))
            ]
            
            # Call the multi-upload endpoint
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={'ship_id': self.test_ship_id},
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract results
                results = result.get('results', [])
                summary = result.get('summary', {})
                
                if results:
                    file_result = results[0]
                    analysis = file_result.get('analysis', {})
                    
                    # Check analysis results
                    cert_name = analysis.get('cert_name', '')
                    cert_number = analysis.get('cert_no', '')
                    issued_by = analysis.get('issued_by', '')
                    ship_name = analysis.get('ship_name', '')
                    
                    print(f"    📋 Multi-Upload Analysis Results:")
                    print(f"       Ship Name: '{ship_name}'")
                    print(f"       Certificate Name: '{cert_name}'")
                    print(f"       Certificate Number: '{cert_number}'")
                    print(f"       Issued By: '{issued_by}'")
                    
                    # Check for filename-based fallback
                    is_filename_based = (
                        'SUNSHINE_01_ImagePDF' in str(cert_name) or
                        'CERT_SUNSHINE_01_IMAGEPDF' in str(cert_number) or
                        'Filename-based' in str(issued_by)
                    )
                    
                    if is_filename_based:
                        self.log_test("Multi-Upload Test", False, 
                                    f"❌ CRITICAL: Multi-upload also using filename-based fallback!\n"
                                    f"    Certificate Name: '{cert_name}'\n"
                                    f"    Certificate Number: '{cert_number}'\n"
                                    f"    Issued By: '{issued_by}'")
                    else:
                        # Check for real extraction
                        has_real_data = (
                            'tonnage' in str(cert_name).lower() or
                            'PM242' in str(cert_number) or
                            'belize' in str(issued_by).lower() or
                            'panama' in str(issued_by).lower()
                        )
                        
                        if has_real_data:
                            self.log_test("Multi-Upload Test", True, 
                                        f"✅ Multi-upload using real PDF extraction\n"
                                        f"    Certificate Name: '{cert_name}'\n"
                                        f"    Certificate Number: '{cert_number}'\n"
                                        f"    Issued By: '{issued_by}'")
                        else:
                            self.log_test("Multi-Upload Test", False, 
                                        f"⚠️ Multi-upload completed but data unclear\n"
                                        f"    Certificate Name: '{cert_name}'\n"
                                        f"    Certificate Number: '{cert_number}'\n"
                                        f"    Issued By: '{issued_by}'")
                    
                    return result
                else:
                    self.log_test("Multi-Upload Test", False, 
                                error="No results returned from multi-upload")
                    return None
            else:
                self.log_test("Multi-Upload Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Multi-Upload Test", False, error=str(e))
            return None
    
    def check_ocr_processing_logs(self):
        """Check backend logs for OCR processing information"""
        try:
            print("🔍 Checking backend logs for OCR processing...")
            
            import subprocess
            
            try:
                # Check supervisor backend logs for OCR-related entries
                result = subprocess.run(
                    ['tail', '-n', '100', '/var/log/supervisor/backend.err.log'],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    logs = result.stdout
                    
                    # Look for OCR-related log entries
                    ocr_keywords = [
                        'OCR processing',
                        'Enhanced OCR',
                        'Tesseract',
                        'Google Vision',
                        'text extraction',
                        'characters extracted',
                        'confidence',
                        'poppler',
                        'PDF to image',
                        'SUNSHINE_01_ImagePDF'
                    ]
                    
                    ocr_logs = []
                    for line in logs.split('\n'):
                        if any(keyword.lower() in line.lower() for keyword in ocr_keywords):
                            ocr_logs.append(line.strip())
                    
                    if ocr_logs:
                        print(f"    📋 Found {len(ocr_logs)} OCR-related log entries:")
                        for log_entry in ocr_logs[-10:]:  # Show last 10 entries
                            print(f"       {log_entry}")
                        
                        # Check for specific indicators
                        log_text = '\n'.join(ocr_logs)
                        
                        if 'characters extracted' in log_text.lower():
                            # Look for character count
                            import re
                            char_matches = re.findall(r'(\d+)\s*characters', log_text.lower())
                            if char_matches:
                                char_count = char_matches[-1]
                                if int(char_count) > 2000:
                                    self.log_test("OCR Processing Logs Check", True, 
                                                f"OCR extracted {char_count} characters (expected ~2,479)")
                                else:
                                    self.log_test("OCR Processing Logs Check", False, 
                                                f"OCR extracted only {char_count} characters (expected ~2,479)")
                            else:
                                self.log_test("OCR Processing Logs Check", True, 
                                            "OCR processing logs found but character count unclear")
                        else:
                            self.log_test("OCR Processing Logs Check", False, 
                                        "OCR logs found but no character extraction information")
                    else:
                        self.log_test("OCR Processing Logs Check", False, 
                                    "No OCR-related log entries found in recent logs")
                    
                    return ocr_logs
                else:
                    self.log_test("OCR Processing Logs Check", False, 
                                error="Could not read backend logs")
                    return None
                    
            except subprocess.TimeoutExpired:
                self.log_test("OCR Processing Logs Check", False, 
                            error="Timeout reading backend logs")
                return None
                
        except Exception as e:
            self.log_test("OCR Processing Logs Check", False, error=str(e))
            return None
    
    def run_debug_tests(self):
        """Run all debug tests for filename-based fallback issue"""
        print("🚨 FILENAME-BASED FALLBACK DEBUG TEST - CRITICAL ISSUE INVESTIGATION")
        print("=" * 90)
        print("ISSUE: AI analysis using filename-based fallback instead of real PDF extraction")
        print(f"PDF URL: {PDF_URL}")
        print(f"Expected Certificate Name: 'International Tonnage Certificate (1969)'")
        print(f"Expected Certificate Number: 'PM242868'")
        print(f"Expected Issued By: 'Government of Belize, issued by Panama Maritime Documentation Services Inc.'")
        print(f"Backend URL: {BACKEND_URL}")
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed.")
            return False
        
        # Step 2: Download exact PDF file
        if not self.download_exact_pdf():
            print("❌ PDF download failed. Cannot proceed.")
            return False
        
        # Step 3: Find test ship
        if not self.find_test_ship():
            print("❌ Could not find test ship. Cannot proceed.")
            return False
        
        # Step 4: Test certificate analysis API directly
        print("\n" + "="*50)
        print("🔍 DIRECT CERTIFICATE ANALYSIS TEST")
        print("="*50)
        analysis_result = self.test_certificate_analysis_direct()
        
        # Step 5: Test multi-upload with exact PDF
        print("\n" + "="*50)
        print("🔍 MULTI-UPLOAD CERTIFICATE TEST")
        print("="*50)
        upload_result = self.test_multi_upload_with_exact_pdf()
        
        # Step 6: Check backend logs for OCR processing
        print("\n" + "="*50)
        print("🔍 OCR PROCESSING LOGS CHECK")
        print("="*50)
        self.check_ocr_processing_logs()
        
        # Summary and Analysis
        print("\n" + "=" * 90)
        print("🔍 CRITICAL ISSUE ANALYSIS SUMMARY")
        print("=" * 90)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        # Determine if the critical issue is present
        issue_confirmed = False
        issue_resolved = False
        
        if analysis_result:
            analysis_data = analysis_result.get('data', {}).get('analysis', {})
            cert_name = analysis_data.get('cert_name', '')
            cert_number = analysis_data.get('cert_no', '')
            issued_by = analysis_data.get('issued_by', '')
            
            # Check for filename-based indicators
            if ('SUNSHINE_01_ImagePDF' in str(cert_name) or 
                'CERT_SUNSHINE_01_IMAGEPDF' in str(cert_number) or
                'Filename-based' in str(issued_by)):
                issue_confirmed = True
            elif ('tonnage' in str(cert_name).lower() or 
                  'PM242' in str(cert_number) or
                  'belize' in str(issued_by).lower()):
                issue_resolved = True
        
        if issue_confirmed:
            print("\n❌ CRITICAL ISSUE CONFIRMED:")
            print("   AI analysis is using filename-based fallback instead of real PDF extraction")
            print("   This means OCR processor is not working correctly")
            print("\n🔧 IMMEDIATE ACTIONS REQUIRED:")
            print("   1. Check if OCR processor (Tesseract/Poppler) is properly installed")
            print("   2. Verify OCR dependencies are available in the container")
            print("   3. Check if PDF text extraction is working (~2,479 characters expected)")
            print("   4. Examine AI model configuration and prompts")
            print("   5. Test with different PDF files to isolate the issue")
            return False
        elif issue_resolved:
            print("\n✅ ISSUE APPEARS RESOLVED:")
            print("   AI analysis is extracting real data from PDF content")
            print("   OCR processor appears to be working correctly")
            return True
        else:
            print("\n⚠️ INCONCLUSIVE RESULTS:")
            print("   Could not determine if issue is present or resolved")
            print("   Manual verification may be required")
            return False

def main():
    """Main test execution"""
    tester = FilenameFallbackDebugTester()
    success = tester.run_debug_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
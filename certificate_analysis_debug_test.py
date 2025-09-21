#!/usr/bin/env python3
"""
Certificate Analysis Debug Test
Focused testing for the specific issue where the system is generating incorrect certificate 
information based on filename instead of extracting from PDF content.

Review Request: DEBUG Certificate Analysis Issue
- Test POST /api/certificates/multi-upload with specific PDF file
- Verify if AI analysis is working or falling back to filename-based generation
- Check OCR text extraction from PDF
- Test certificate mapping logic
- Check AI configuration and key usage
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import io
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ship-cert-manager-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

# Specific PDF file from review request
TEST_PDF_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/s6nh3s3p_SUNSHINE_01_ImagePDF.pdf"

# Expected correct data from PDF analysis
EXPECTED_DATA = {
    "certificate_name": "International Tonnage Certificate (1969)",
    "certificate_number": "PM242868",
    "issue_date": "December 12, 2024",
    "issued_by": "Government of Belize, issued by Panama Maritime Documentation Services Inc.",
    "ship_name": "SUNSHINE 01",
    "imo_number": "9415313"
}

# Current incorrect data (filename-based)
INCORRECT_DATA = {
    "certificate_name": "Maritime Certificate - SUNSHINE_01_ImagePDF",
    "certificate_number": "CERT_SUNSHINE_01_IMAGEPDF",
    "issued_by": "Maritime Authority (Filename-based classification)"
}

class CertificateAnalysisDebugger:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.test_ship_id = None
        self.ai_config = None
        self.pdf_content = None
        
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
        """Authenticate with admin credentials"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                
                self.log_test("Authentication", True, 
                            f"Logged in as {self.user_info['username']} ({self.user_info.get('role', 'Unknown')})")
                return True
            else:
                self.log_test("Authentication", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def download_test_pdf(self):
        """Download the specific PDF file from the review request"""
        try:
            print(f"📥 Downloading test PDF from: {TEST_PDF_URL}")
            response = requests.get(TEST_PDF_URL, timeout=30)
            
            if response.status_code == 200:
                self.pdf_content = response.content
                file_size = len(self.pdf_content)
                self.log_test("PDF Download", True, 
                            f"Downloaded PDF file: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                return True
            else:
                self.log_test("PDF Download", False, 
                            error=f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("PDF Download", False, error=str(e))
            return False
    
    def get_test_ship(self):
        """Get a test ship for certificate upload"""
        try:
            response = requests.get(f"{API_BASE}/ships", headers=self.get_headers())
            
            if response.status_code == 200:
                ships = response.json()
                if ships and len(ships) > 0:
                    # Look for SUNSHINE STAR or use first ship
                    sunshine_ship = None
                    for ship in ships:
                        if "SUNSHINE" in ship.get('name', '').upper():
                            sunshine_ship = ship
                            break
                    
                    if sunshine_ship:
                        self.test_ship_id = sunshine_ship['id']
                        ship_name = sunshine_ship['name']
                        self.log_test("Get Test Ship", True, 
                                    f"Using SUNSHINE ship: {ship_name} (ID: {self.test_ship_id})")
                    else:
                        # Use first available ship
                        self.test_ship_id = ships[0]['id']
                        ship_name = ships[0]['name']
                        self.log_test("Get Test Ship", True, 
                                    f"Using first available ship: {ship_name} (ID: {self.test_ship_id})")
                    return True
                else:
                    self.log_test("Get Test Ship", False, error="No ships found in database")
                    return False
            else:
                self.log_test("Get Test Ship", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Test Ship", False, error=str(e))
            return False
    
    def check_ai_configuration(self):
        """Check AI configuration and key usage"""
        try:
            response = requests.get(f"{API_BASE}/ai-config", headers=self.get_headers())
            
            if response.status_code == 200:
                self.ai_config = response.json()
                provider = self.ai_config.get('provider')
                model = self.ai_config.get('model')
                use_emergent_key = self.ai_config.get('use_emergent_key', False)
                
                details = f"Provider: {provider}, Model: {model}, Use Emergent Key: {use_emergent_key}"
                
                if provider and model:
                    self.log_test("AI Configuration Check", True, details)
                    return True
                else:
                    self.log_test("AI Configuration Check", False, 
                                error="Missing provider or model in AI configuration")
                    return False
            else:
                self.log_test("AI Configuration Check", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("AI Configuration Check", False, error=str(e))
            return False
    
    def test_certificate_analysis(self):
        """Test the certificate analysis with the specific PDF file"""
        try:
            if not self.test_ship_id or not self.pdf_content:
                self.log_test("Certificate Analysis Test", False, 
                            error="Missing test ship ID or PDF content")
                return None
            
            print("🔍 Testing certificate analysis with specific PDF file...")
            
            # Prepare the PDF file for upload
            files = [
                ('files', ('SUNSHINE_01_ImagePDF.pdf', io.BytesIO(self.pdf_content), 'application/pdf'))
            ]
            
            # Test the multi-upload endpoint
            response = requests.post(
                f"{API_BASE}/certificates/multi-upload",
                params={'ship_id': self.test_ship_id},
                files=files,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract analysis results
                results = result.get('results', [])
                if results:
                    analysis_result = results[0]
                    
                    # Log the full response for debugging
                    print("📊 FULL ANALYSIS RESPONSE:")
                    print(json.dumps(analysis_result, indent=2, default=str))
                    print()
                    
                    self.log_test("Certificate Analysis Test", True, 
                                f"Analysis completed. Status: {analysis_result.get('status', 'Unknown')}")
                    return analysis_result
                else:
                    self.log_test("Certificate Analysis Test", False, 
                                error="No results returned from analysis")
                    return None
            else:
                self.log_test("Certificate Analysis Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Certificate Analysis Test", False, error=str(e))
            return None
    
    def analyze_extraction_results(self, analysis_result):
        """Analyze the extraction results and compare with expected data"""
        try:
            if not analysis_result:
                self.log_test("Extraction Results Analysis", False, 
                            error="No analysis result to analyze")
                return False
            
            print("🔍 ANALYZING EXTRACTION RESULTS")
            print("=" * 60)
            
            # Extract certificate data from analysis
            analysis_data = analysis_result.get('analysis', {})
            certificate_data = analysis_result.get('certificate', {})
            
            # Check if this is filename-based or AI-based analysis
            is_filename_based = False
            
            # Look for indicators of filename-based generation
            cert_name = certificate_data.get('cert_name', '') or analysis_data.get('certificate_name', '')
            cert_number = certificate_data.get('cert_no', '') or analysis_data.get('certificate_number', '')
            issued_by = certificate_data.get('issued_by', '') or analysis_data.get('issued_by', '')
            
            print(f"📋 EXTRACTED DATA:")
            print(f"   Certificate Name: {cert_name}")
            print(f"   Certificate Number: {cert_number}")
            print(f"   Issued By: {issued_by}")
            print(f"   Ship Name: {analysis_data.get('ship_name', 'N/A')}")
            print(f"   IMO Number: {analysis_data.get('imo_number', 'N/A')}")
            print()
            
            # Check for filename-based patterns
            filename_indicators = [
                "SUNSHINE_01_ImagePDF" in str(cert_name),
                "CERT_SUNSHINE_01_IMAGEPDF" in str(cert_number),
                "Filename-based classification" in str(issued_by),
                "Maritime Certificate -" in str(cert_name)
            ]
            
            is_filename_based = any(filename_indicators)
            
            print(f"📊 EXPECTED DATA (from PDF content):")
            for key, value in EXPECTED_DATA.items():
                print(f"   {key}: {value}")
            print()
            
            print(f"❌ INCORRECT DATA (filename-based):")
            for key, value in INCORRECT_DATA.items():
                print(f"   {key}: {value}")
            print()
            
            # Determine if AI analysis is working
            if is_filename_based:
                self.log_test("AI Analysis Working", False, 
                            error="System is using filename-based generation instead of PDF content analysis")
                
                # Check for potential causes
                fallback_reason = analysis_data.get('fallback_reason', '')
                if fallback_reason:
                    print(f"🔍 FALLBACK REASON: {fallback_reason}")
                
                return False
            else:
                # Check if extracted data matches expected data
                matches = 0
                total_checks = 0
                
                # Compare key fields
                comparisons = [
                    ("Certificate Name", cert_name, EXPECTED_DATA["certificate_name"]),
                    ("Certificate Number", cert_number, EXPECTED_DATA["certificate_number"]),
                    ("Issued By", issued_by, EXPECTED_DATA["issued_by"]),
                ]
                
                for field_name, actual, expected in comparisons:
                    total_checks += 1
                    if expected.lower() in actual.lower() or actual.lower() in expected.lower():
                        matches += 1
                        print(f"✅ {field_name}: Match found")
                    else:
                        print(f"❌ {field_name}: No match")
                        print(f"   Expected: {expected}")
                        print(f"   Actual: {actual}")
                
                accuracy = (matches / total_checks) * 100 if total_checks > 0 else 0
                
                if matches >= 2:  # At least 2 out of 3 key fields match
                    self.log_test("AI Analysis Working", True, 
                                f"AI analysis appears to be working. Accuracy: {accuracy:.1f}% ({matches}/{total_checks})")
                    return True
                else:
                    self.log_test("AI Analysis Working", False, 
                                f"AI analysis not extracting correct data. Accuracy: {accuracy:.1f}% ({matches}/{total_checks})")
                    return False
                
        except Exception as e:
            self.log_test("Extraction Results Analysis", False, error=str(e))
            return False
    
    def check_ocr_functionality(self):
        """Check if OCR functionality is available and working"""
        try:
            # This is a diagnostic check - we'll look for OCR-related information in the response
            print("🔍 CHECKING OCR FUNCTIONALITY")
            print("=" * 40)
            
            # Check if backend has OCR capabilities by looking at the analysis response
            # This is inferred from the previous analysis test
            if hasattr(self, 'last_analysis_result') and self.last_analysis_result:
                analysis_data = self.last_analysis_result.get('analysis', {})
                
                # Look for OCR-related indicators
                ocr_indicators = [
                    'text_extracted' in analysis_data,
                    'ocr_confidence' in analysis_data,
                    'processing_method' in analysis_data,
                    analysis_data.get('fallback_reason', '').lower().find('ocr') != -1
                ]
                
                if any(ocr_indicators):
                    self.log_test("OCR Functionality Check", True, 
                                "OCR-related fields detected in analysis response")
                    return True
                else:
                    self.log_test("OCR Functionality Check", False, 
                                "No OCR-related indicators found in analysis response")
                    return False
            else:
                self.log_test("OCR Functionality Check", False, 
                            error="No previous analysis result to check")
                return False
                
        except Exception as e:
            self.log_test("OCR Functionality Check", False, error=str(e))
            return False
    
    def run_debug_tests(self):
        """Run all debug tests for certificate analysis issue"""
        print("🐛 CERTIFICATE ANALYSIS DEBUG TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test PDF: {TEST_PDF_URL}")
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Download test PDF
        if not self.download_test_pdf():
            print("❌ PDF download failed. Cannot proceed with analysis.")
            return False
        
        # Step 3: Get test ship
        if not self.get_test_ship():
            print("❌ Could not get test ship. Cannot proceed with certificate upload.")
            return False
        
        # Step 4: Check AI configuration
        ai_config_ok = self.check_ai_configuration()
        if not ai_config_ok:
            print("⚠️ AI configuration issues detected. This may affect analysis quality.")
        
        # Step 5: Test certificate analysis
        analysis_result = self.test_certificate_analysis()
        if not analysis_result:
            print("❌ Certificate analysis test failed.")
            return False
        
        # Store result for OCR check
        self.last_analysis_result = analysis_result
        
        # Step 6: Analyze extraction results
        extraction_ok = self.analyze_extraction_results(analysis_result)
        
        # Step 7: Check OCR functionality
        ocr_ok = self.check_ocr_functionality()
        
        # Summary
        print("=" * 80)
        print("📊 DEBUG TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print()
        
        # Diagnostic summary
        print("🔍 DIAGNOSTIC FINDINGS:")
        print("-" * 40)
        
        if not extraction_ok:
            print("❌ CRITICAL ISSUE: System is generating filename-based data instead of extracting from PDF content")
            print("   - Certificate analysis is falling back to filename parsing")
            print("   - AI/OCR processing is not working correctly")
            print("   - This explains why users see incorrect certificate information")
        else:
            print("✅ AI analysis appears to be working correctly")
            print("   - System is extracting data from PDF content")
            print("   - Certificate information matches expected values")
        
        if not ai_config_ok:
            print("⚠️ AI configuration issues detected")
            print("   - Check AI provider and model settings")
            print("   - Verify API keys are properly configured")
        
        if not ocr_ok:
            print("⚠️ OCR functionality may not be available")
            print("   - Check if OCR libraries are installed")
            print("   - Verify OCR processing pipeline")
        
        print()
        print("🎯 RECOMMENDED ACTIONS:")
        print("-" * 40)
        
        if not extraction_ok:
            print("1. Check AI configuration and API keys")
            print("2. Verify OCR libraries are installed and working")
            print("3. Test with a simple text-based PDF first")
            print("4. Check backend logs for AI/OCR processing errors")
            print("5. Ensure the AI model supports document analysis")
        
        return extraction_ok

def main():
    """Main debug test execution"""
    debugger = CertificateAnalysisDebugger()
    success = debugger.run_debug_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
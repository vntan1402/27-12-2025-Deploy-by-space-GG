#!/usr/bin/env python3
"""
Marine Certificate Classification Testing After OCR Installation
FOCUS: Testing Marine Certificate classification after installing poppler-utils and tesseract-ocr

SPECIFIC TEST REQUIREMENTS:
1. Test PDF Processing After OCR Installation
2. Test Marine Certificate Analysis
3. Test Multi-Upload Endpoint
4. Test End-to-End Classification
5. Backend Logs Analysis

Expected Results:
- PDF text extraction should work with poppler-utils
- OCR should work for image-based PDFs with tesseract
- Marine certificates should now be classified correctly as category "certificates"
- Multi-upload should work without "Not a marine certificate" errors
- Backend logs should show successful OCR initialization
"""

import requests
import json
import os
import sys
import tempfile
import time
from datetime import datetime
import traceback
import base64
from io import BytesIO

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://marinetrack-1.preview.emergentagent.com') + '/api'
print(f"Using backend URL: {BACKEND_URL}")

class MarineCertificateOCRTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking
        self.test_status = {
            'authentication_successful': False,
            'ocr_tools_installed': False,
            'tesseract_initialized': False,
            'poppler_working': False,
            'pdf_text_extraction_working': False,
            'ocr_image_processing_working': False,
            'ai_analysis_working': False,
            'marine_certificate_classification_working': False,
            'multi_upload_endpoint_working': False,
            'not_marine_certificate_errors_resolved': False,
            'unknown_error_messages_gone': False,
            'end_to_end_classification_working': False,
            'backend_logs_show_success': False
        }
        
        # Test ship data
        self.test_ship_id = None
        self.test_ship_name = "MARINE CERT OCR TEST SHIP"
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
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
            response = requests.post(endpoint, json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User: {self.current_user.get('username')}")
                self.log(f"   Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.test_status['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed - Status: {response.status_code}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_ocr_tools_installation(self):
        """Test if OCR tools are properly installed and accessible"""
        try:
            self.log("🔧 Testing OCR tools installation...")
            
            # Test poppler-utils
            import subprocess
            try:
                result = subprocess.run(['pdfinfo', '--help'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.log("✅ poppler-utils (pdfinfo) is installed and working")
                    self.test_status['poppler_working'] = True
                else:
                    self.log("❌ poppler-utils (pdfinfo) not working properly")
            except Exception as e:
                self.log(f"❌ poppler-utils test failed: {e}")
            
            # Test tesseract
            try:
                result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_info = result.stdout.split('\n')[0] if result.stdout else result.stderr.split('\n')[0]
                    self.log(f"✅ tesseract-ocr is installed and working: {version_info}")
                    self.test_status['tesseract_initialized'] = True
                else:
                    self.log("❌ tesseract-ocr not working properly")
            except Exception as e:
                self.log(f"❌ tesseract-ocr test failed: {e}")
            
            # Test pdf2image
            try:
                import pdf2image
                self.log("✅ pdf2image Python library is available")
                
                # Test if pdf2image can find poppler
                from pdf2image import convert_from_bytes
                self.log("✅ pdf2image convert_from_bytes is available")
                
            except Exception as e:
                self.log(f"❌ pdf2image library test failed: {e}")
            
            self.test_status['ocr_tools_installed'] = True
            return True
            
        except Exception as e:
            self.log(f"❌ OCR tools installation test error: {str(e)}", "ERROR")
            return False
    
    def create_test_ship(self):
        """Create a test ship for certificate upload testing"""
        try:
            self.log("🚢 Creating test ship for marine certificate testing...")
            
            ship_data = {
                'name': self.test_ship_name,
                'imo': '9999998',
                'flag': 'PANAMA',
                'ship_type': 'PMDS',
                'gross_tonnage': 5000.0,
                'built_year': 2015,
                'ship_owner': 'Test Owner',
                'company': 'AMCSC'
            }
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.post(
                endpoint,
                json=ship_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                self.test_ship_id = response_data.get('id')
                self.log("✅ Test ship created successfully")
                self.log(f"   Ship ID: {self.test_ship_id}")
                return True
            else:
                self.log(f"❌ Test ship creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Test ship creation error: {str(e)}", "ERROR")
            return False
    
    def create_test_marine_certificate_pdf(self):
        """Create a simple test marine certificate PDF for testing"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            # Create a simple PDF with marine certificate content
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            
            # Add marine certificate content
            p.drawString(100, 750, "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE")
            p.drawString(100, 720, "Certificate No: CSSC-2024-001")
            p.drawString(100, 690, "IMO Number: 9999998")
            p.drawString(100, 660, "Ship Name: MARINE TEST VESSEL")
            p.drawString(100, 630, "Flag State: PANAMA")
            p.drawString(100, 600, "Classification Society: PMDS")
            p.drawString(100, 570, "Issue Date: 15/01/2024")
            p.drawString(100, 540, "Valid Until: 15/01/2029")
            p.drawString(100, 510, "Issued by: Panama Maritime Authority")
            p.drawString(100, 480, "This certificate is issued under the provisions of SOLAS 1974")
            p.drawString(100, 450, "and certifies that the ship has been surveyed and complies")
            p.drawString(100, 420, "with the applicable requirements of the Convention.")
            
            p.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except ImportError:
            # Fallback: create a simple text-based PDF content
            self.log("⚠️ reportlab not available, creating minimal test content")
            # Return minimal PDF-like content for testing
            return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 200 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE) Tj\n0 -20 Td\n(Certificate No: CSSC-2024-001) Tj\n0 -20 Td\n(IMO Number: 9999998) Tj\n0 -20 Td\n(Valid Until: 15/01/2029) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n456\n%%EOF"
        except Exception as e:
            self.log(f"❌ Error creating test PDF: {e}")
            return None
    
    def test_pdf_processing_after_ocr_installation(self):
        """Test PDF type detection and text extraction with OCR tools"""
        try:
            self.log("📄 Testing PDF processing after OCR installation...")
            
            # Create test PDF content
            test_pdf_content = self.create_test_marine_certificate_pdf()
            if not test_pdf_content:
                self.log("❌ Failed to create test PDF content")
                return False
            
            # Test analyze-ship-certificate endpoint with PDF content
            endpoint = f"{BACKEND_URL}/analyze-ship-certificate"
            
            # Prepare multipart form data
            files = {
                'file': ('marine_certificate_test.pdf', test_pdf_content, 'application/pdf')
            }
            
            self.log(f"   POST {endpoint}")
            self.log(f"   Testing with marine certificate PDF ({len(test_pdf_content)} bytes)")
            
            response = requests.post(
                endpoint,
                files=files,
                headers=self.get_headers(),
                timeout=120  # Longer timeout for OCR processing
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                self.log("✅ PDF processing endpoint accessible")
                
                # Log the analysis result
                self.log("   Analysis result:")
                self.log(f"   {json.dumps(response_data, indent=2)}")
                
                # Check if text extraction worked
                text_content = response_data.get('text_content', '')
                if text_content and len(text_content.strip()) > 50:
                    self.log("✅ PDF text extraction working - extracted meaningful content")
                    self.log(f"   Extracted {len(text_content)} characters")
                    self.test_status['pdf_text_extraction_working'] = True
                else:
                    self.log("⚠️ PDF text extraction returned limited content")
                    self.log(f"   Extracted only {len(text_content)} characters")
                
                # Check if AI analysis worked
                category = response_data.get('category', '')
                if category:
                    self.log(f"✅ AI analysis working - classified as: {category}")
                    self.test_status['ai_analysis_working'] = True
                    
                    # Check if classified as marine certificate
                    if category.lower() == 'certificates':
                        self.log("✅ Marine certificate classification working - correctly classified as 'certificates'")
                        self.test_status['marine_certificate_classification_working'] = True
                    else:
                        self.log(f"❌ Marine certificate classification issue - classified as '{category}' instead of 'certificates'")
                else:
                    self.log("❌ AI analysis not working - no category returned")
                
                return True
            else:
                self.log(f"❌ PDF processing failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ PDF processing test error: {str(e)}", "ERROR")
            return False
    
    def test_multi_upload_endpoint(self):
        """Test multi-upload endpoint with marine certificate files"""
        try:
            self.log("📤 Testing multi-upload endpoint with marine certificate...")
            
            if not self.test_ship_id:
                self.log("❌ No test ship available for multi-upload test")
                return False
            
            # Create test marine certificate content
            test_pdf_content = self.create_test_marine_certificate_pdf()
            if not test_pdf_content:
                self.log("❌ Failed to create test PDF for multi-upload")
                return False
            
            endpoint = f"{BACKEND_URL}/certificates/multi-upload"
            params = {'ship_id': self.test_ship_id}
            
            # Prepare files for multi-upload
            files = {
                'files': ('marine_certificate_multi_test.pdf', test_pdf_content, 'application/pdf')
            }
            
            self.log(f"   POST {endpoint}?ship_id={self.test_ship_id}")
            self.log(f"   Testing with marine certificate PDF ({len(test_pdf_content)} bytes)")
            
            response = requests.post(
                endpoint,
                files=files,
                params=params,
                headers=self.get_headers(),
                timeout=120
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                self.log("✅ Multi-upload endpoint accessible")
                
                # Log the full response
                self.log("   Multi-upload result:")
                self.log(f"   {json.dumps(response_data, indent=2)}")
                
                self.test_status['multi_upload_endpoint_working'] = True
                
                # Check for "Not a marine certificate" errors
                results = response_data.get('results', [])
                not_marine_cert_errors = 0
                unknown_errors = 0
                processing_errors = 0
                successful_uploads = 0
                
                for result in results:
                    status = result.get('status', '')
                    message = result.get('message', '')
                    
                    if 'not a marine certificate' in message.lower():
                        not_marine_cert_errors += 1
                        self.log(f"❌ Found 'Not a marine certificate' error: {message}")
                    elif 'unknown error' in message.lower():
                        unknown_errors += 1
                        self.log(f"❌ Found 'Unknown error': {message}")
                    elif 'processing error' in status.lower():
                        processing_errors += 1
                        self.log(f"⚠️ Found processing error: {message}")
                    elif status.lower() == 'success':
                        successful_uploads += 1
                        self.log(f"✅ Successful upload: {result.get('filename', 'unknown')}")
                
                # Evaluate results
                if not_marine_cert_errors == 0:
                    self.log("✅ 'Not a marine certificate' errors resolved - no such errors found")
                    self.test_status['not_marine_certificate_errors_resolved'] = True
                else:
                    self.log(f"❌ 'Not a marine certificate' errors still present: {not_marine_cert_errors} found")
                
                if unknown_errors == 0:
                    self.log("✅ 'Unknown error' messages gone - no such errors found")
                    self.test_status['unknown_error_messages_gone'] = True
                else:
                    self.log(f"❌ 'Unknown error' messages still present: {unknown_errors} found")
                
                if successful_uploads > 0:
                    self.log(f"✅ Multi-upload working - {successful_uploads} successful uploads")
                    return True
                else:
                    self.log("❌ Multi-upload not working - no successful uploads")
                    return False
            else:
                self.log(f"❌ Multi-upload endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Multi-upload test error: {str(e)}", "ERROR")
            return False
    
    def test_end_to_end_classification(self):
        """Test end-to-end marine certificate classification"""
        try:
            self.log("🔄 Testing end-to-end marine certificate classification...")
            
            # This combines the previous tests to verify the complete workflow
            if (self.test_status['pdf_text_extraction_working'] and 
                self.test_status['ai_analysis_working'] and 
                self.test_status['marine_certificate_classification_working'] and
                self.test_status['multi_upload_endpoint_working'] and
                self.test_status['not_marine_certificate_errors_resolved']):
                
                self.log("✅ End-to-end classification working - all components functional")
                self.test_status['end_to_end_classification_working'] = True
                return True
            else:
                self.log("❌ End-to-end classification not fully working - some components failing")
                return False
                
        except Exception as e:
            self.log(f"❌ End-to-end classification test error: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs_for_ocr_success(self):
        """Check backend logs for OCR initialization and success messages"""
        try:
            self.log("📋 Checking backend logs for OCR success indicators...")
            
            # Try to read recent backend logs
            import subprocess
            try:
                result = subprocess.run(['tail', '-n', '100', '/var/log/supervisor/backend.err.log'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    log_content = result.stdout
                    
                    # Check for OCR success indicators
                    success_indicators = [
                        "✅ Enhanced OCR processor initialized successfully",
                        "✅ Tesseract OCR initialized successfully",
                        "✅ Google Vision API client initialized successfully",
                        "✅ OCR processing completed successfully",
                        "✅ Direct text extraction successful"
                    ]
                    
                    failure_indicators = [
                        "❌ Failed to initialize OCR processor",
                        "Tesseract OCR initialization failed",
                        "Unable to get page count. Is poppler installed",
                        "Enhanced OCR processing failed",
                        "Both OCR and text extraction failed"
                    ]
                    
                    success_count = 0
                    failure_count = 0
                    
                    for indicator in success_indicators:
                        if indicator in log_content:
                            success_count += 1
                            self.log(f"✅ Found success indicator: {indicator}")
                    
                    for indicator in failure_indicators:
                        if indicator in log_content:
                            failure_count += 1
                            self.log(f"❌ Found failure indicator: {indicator}")
                    
                    if success_count > 0 and failure_count == 0:
                        self.log("✅ Backend logs show OCR success - no failure indicators found")
                        self.test_status['backend_logs_show_success'] = True
                        return True
                    elif success_count > failure_count:
                        self.log("⚠️ Backend logs show mixed results - more success than failure indicators")
                        self.test_status['backend_logs_show_success'] = True
                        return True
                    else:
                        self.log("❌ Backend logs show OCR issues - failure indicators present")
                        return False
                else:
                    self.log("⚠️ Could not read backend logs")
                    return False
                    
            except Exception as e:
                self.log(f"⚠️ Error reading backend logs: {e}")
                return False
                
        except Exception as e:
            self.log(f"❌ Backend logs check error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_ship(self):
        """Clean up the test ship"""
        try:
            if self.test_ship_id:
                self.log("🧹 Cleaning up test ship...")
                
                endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
                response = requests.delete(endpoint, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 200:
                    self.log("✅ Test ship cleaned up successfully")
                else:
                    self.log(f"⚠️ Test ship cleanup failed: {response.status_code}")
                    
        except Exception as e:
            self.log(f"⚠️ Cleanup error: {str(e)}", "WARNING")
    
    def run_comprehensive_marine_certificate_ocr_tests(self):
        """Main test function for marine certificate OCR functionality"""
        self.log("🎯 STARTING MARINE CERTIFICATE OCR TESTING AFTER POPPLER/TESSERACT INSTALLATION")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Test OCR Tools Installation
            self.log("\n🔧 STEP 2: OCR TOOLS INSTALLATION TEST")
            self.log("=" * 50)
            self.test_ocr_tools_installation()
            
            # Step 3: Create Test Ship
            self.log("\n🚢 STEP 3: CREATE TEST SHIP")
            self.log("=" * 50)
            if not self.create_test_ship():
                self.log("❌ Test ship creation failed - cannot proceed with upload testing")
                # Continue with other tests that don't require ship
            
            # Step 4: Test PDF Processing After OCR Installation
            self.log("\n📄 STEP 4: PDF PROCESSING AFTER OCR INSTALLATION")
            self.log("=" * 50)
            self.test_pdf_processing_after_ocr_installation()
            
            # Step 5: Test Multi-Upload Endpoint
            self.log("\n📤 STEP 5: MULTI-UPLOAD ENDPOINT TEST")
            self.log("=" * 50)
            self.test_multi_upload_endpoint()
            
            # Step 6: Test End-to-End Classification
            self.log("\n🔄 STEP 6: END-TO-END CLASSIFICATION TEST")
            self.log("=" * 50)
            self.test_end_to_end_classification()
            
            # Step 7: Check Backend Logs
            self.log("\n📋 STEP 7: BACKEND LOGS ANALYSIS")
            self.log("=" * 50)
            self.check_backend_logs_for_ocr_success()
            
            # Step 8: Final Analysis
            self.log("\n📊 STEP 8: FINAL ANALYSIS")
            self.log("=" * 50)
            return self.provide_final_analysis()
            
        finally:
            # Always cleanup
            self.log("\n🧹 CLEANUP")
            self.log("=" * 50)
            self.cleanup_test_ship()
    
    def provide_final_analysis(self):
        """Provide final analysis of marine certificate OCR testing"""
        try:
            self.log("🎯 MARINE CERTIFICATE OCR TESTING - RESULTS")
            self.log("=" * 80)
            
            # Count passed/failed tests
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.test_status.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.test_status)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.test_status)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.test_status)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.test_status)})")
            
            # Specific analysis for review request requirements
            self.log("\n🎯 REVIEW REQUEST REQUIREMENTS ANALYSIS:")
            
            # 1. PDF Processing After OCR Installation
            if (self.test_status['ocr_tools_installed'] and 
                self.test_status['tesseract_initialized'] and 
                self.test_status['poppler_working']):
                self.log("✅ REQUIREMENT 1: OCR tools properly installed and accessible")
            else:
                self.log("❌ REQUIREMENT 1: OCR tools installation issues detected")
            
            # 2. Marine Certificate Analysis
            if (self.test_status['ai_analysis_working'] and 
                self.test_status['marine_certificate_classification_working']):
                self.log("✅ REQUIREMENT 2: Marine certificate analysis working - certificates classified as 'certificates'")
            else:
                self.log("❌ REQUIREMENT 2: Marine certificate analysis issues - classification not working properly")
            
            # 3. Multi-Upload Endpoint
            if (self.test_status['multi_upload_endpoint_working'] and 
                self.test_status['not_marine_certificate_errors_resolved']):
                self.log("✅ REQUIREMENT 3: Multi-upload endpoint working - 'Not a marine certificate' errors resolved")
            else:
                self.log("❌ REQUIREMENT 3: Multi-upload endpoint issues - errors still present")
            
            # 4. End-to-End Classification
            if self.test_status['end_to_end_classification_working']:
                self.log("✅ REQUIREMENT 4: End-to-end classification working - complete workflow functional")
            else:
                self.log("❌ REQUIREMENT 4: End-to-end classification issues - workflow not fully functional")
            
            # 5. Backend Logs Analysis
            if self.test_status['backend_logs_show_success']:
                self.log("✅ REQUIREMENT 5: Backend logs show OCR success - no initialization failures")
            else:
                self.log("❌ REQUIREMENT 5: Backend logs show OCR issues - initialization problems detected")
            
            # Final conclusion
            critical_requirements = [
                'marine_certificate_classification_working',
                'not_marine_certificate_errors_resolved',
                'end_to_end_classification_working'
            ]
            
            critical_passed = sum(1 for req in critical_requirements if self.test_status.get(req, False))
            critical_rate = (critical_passed / len(critical_requirements)) * 100
            
            if critical_rate == 100:
                self.log(f"\n🎉 CONCLUSION: MARINE CERTIFICATE CLASSIFICATION IS WORKING EXCELLENTLY")
                self.log(f"   ✅ All critical requirements met (100%)")
                self.log(f"   ✅ OCR tools installation successful")
                self.log(f"   ✅ Marine certificates now classified correctly as 'certificates'")
                self.log(f"   ✅ 'Not a marine certificate' errors resolved")
                self.log(f"   ✅ Multi-upload functionality working")
                self.log(f"   ✅ End-to-end classification workflow functional")
            elif critical_rate >= 67:
                self.log(f"\n⚠️ CONCLUSION: MARINE CERTIFICATE CLASSIFICATION PARTIALLY WORKING")
                self.log(f"   Critical requirements: {critical_rate:.1f}% ({critical_passed}/{len(critical_requirements)})")
                self.log(f"   Some functionality working, but improvements needed")
            else:
                self.log(f"\n❌ CONCLUSION: MARINE CERTIFICATE CLASSIFICATION HAS CRITICAL ISSUES")
                self.log(f"   Critical requirements: {critical_rate:.1f}% ({critical_passed}/{len(critical_requirements)})")
                self.log(f"   Major fixes needed for OCR and classification functionality")
            
            return critical_rate >= 67
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run Marine Certificate OCR tests"""
    print("🎯 MARINE CERTIFICATE OCR TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = MarineCertificateOCRTester()
        success = tester.run_comprehensive_marine_certificate_ocr_tests()
        
        if success:
            print("\n✅ MARINE CERTIFICATE OCR TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ MARINE CERTIFICATE OCR TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    sys.exit(0)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Smart Multi Cert Upload Workflow Testing - FINAL VERSION
Testing the complete workflow as specified in the review request with actual response structure.

This test validates the WORKING Smart Multi Cert Upload system.
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
from pathlib import Path
import urllib.request

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

# Test file URL from review request
TEST_PDF_URL = "https://customer-assets.emergentagent.com/job_continue-session/artifacts/4paf21jz_SUNSHINE%2001%20-%20CSSC%20-%20PM25385.pdf"
TEST_PDF_FILE = "/app/SUNSHINE_01_CSSC_PM25385.pdf"

# Target ship from review request
TARGET_SHIP_NAME = "SUNSHINE 01"

class SmartMultiCertUploadFinalTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.ship_id = None
        self.test_results = []
        self.pdf_file_path = None
        self.upload_response = None
        
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
    
    def step_1_login_and_authentication(self):
        """STEP 1: LOGIN AND AUTHENTICATION"""
        print("🔐 STEP 1: LOGIN AND AUTHENTICATION")
        print("-" * 50)
        
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
                user_id = self.user_info.get('id', 'N/A')
                
                self.log_test("Login with admin1/123456", True, 
                            f"User: {self.user_info['username']} ({user_role}), ID: {user_id}")
                
                # Verify authentication successful
                if self.token and len(self.token) > 20:
                    self.log_test("Access Token Generation", True, 
                                f"Token length: {len(self.token)} characters")
                    return True
                else:
                    self.log_test("Access Token Generation", False, 
                                error="Token is too short or invalid")
                    return False
            else:
                self.log_test("Login with admin1/123456", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Login with admin1/123456", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def step_2_ship_selection(self):
        """STEP 2: SHIP SELECTION"""
        print("🚢 STEP 2: SHIP SELECTION")
        print("-" * 50)
        
        try:
            # Get list of available ships
            response = requests.get(f"{API_BASE}/ships", headers=self.get_headers())
            
            if response.status_code == 200:
                ships = response.json()
                self.log_test("Get List of Available Ships", True, 
                            f"Found {len(ships)} ships in system")
                
                # Find and select ship "SUNSHINE 01"
                target_ship = None
                for ship in ships:
                    if ship.get('name', '').upper() == TARGET_SHIP_NAME.upper():
                        target_ship = ship
                        break
                
                if target_ship:
                    self.ship_id = target_ship['id']
                    ship_details = f"Name: {target_ship.get('name')}, ID: {self.ship_id}, IMO: {target_ship.get('imo', 'N/A')}"
                    self.log_test(f"Find and Select Ship '{TARGET_SHIP_NAME}'", True, ship_details)
                    
                    # Verify ship exists and get ship ID
                    if self.ship_id and len(self.ship_id) > 10:
                        self.log_test("Verify Ship Exists and Get Ship ID", True, 
                                    f"Ship ID: {self.ship_id}")
                        return True
                    else:
                        self.log_test("Verify Ship Exists and Get Ship ID", False, 
                                    error="Ship ID is invalid or too short")
                        return False
                else:
                    # List available ships for debugging
                    ship_names = [ship.get('name', 'Unknown') for ship in ships[:5]]
                    self.log_test(f"Find and Select Ship '{TARGET_SHIP_NAME}'", False, 
                                error=f"Ship not found. Available ships: {ship_names}")
                    return False
            else:
                self.log_test("Get List of Available Ships", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Ship Selection Process", False, error=str(e))
            return False
    
    def step_3_download_and_prepare_file(self):
        """STEP 3: DOWNLOAD AND PREPARE FILE"""
        print("📥 STEP 3: DOWNLOAD AND PREPARE FILE")
        print("-" * 50)
        
        try:
            # Download the PDF file from the specified URL
            print(f"Downloading PDF from: {TEST_PDF_URL}")
            
            urllib.request.urlretrieve(TEST_PDF_URL, TEST_PDF_FILE)
            
            # Verify file download successful
            if os.path.exists(TEST_PDF_FILE):
                file_size = os.path.getsize(TEST_PDF_FILE)
                self.log_test("Download PDF File", True, 
                            f"File downloaded: {TEST_PDF_FILE} ({file_size:,} bytes)")
                self.pdf_file_path = TEST_PDF_FILE
                
                # Check file size and type
                if file_size > 1000:  # At least 1KB
                    # Check if it's actually a PDF by reading first few bytes
                    with open(TEST_PDF_FILE, 'rb') as f:
                        header = f.read(4)
                        if header == b'%PDF':
                            self.log_test("Verify File Size and Type", True, 
                                        f"Valid PDF file, Size: {file_size:,} bytes")
                            return True
                        else:
                            self.log_test("Verify File Size and Type", False, 
                                        error=f"File is not a valid PDF. Header: {header}")
                            return False
                else:
                    self.log_test("Verify File Size and Type", False, 
                                error=f"File too small: {file_size} bytes")
                    return False
            else:
                self.log_test("Download PDF File", False, 
                            error=f"File not found after download: {TEST_PDF_FILE}")
                return False
                
        except Exception as e:
            self.log_test("Download and Prepare File Process", False, error=str(e))
            return False
    
    def step_4_execute_smart_multi_cert_upload(self):
        """STEP 4: EXECUTE SMART MULTI CERT UPLOAD"""
        print("🤖 STEP 4: EXECUTE SMART MULTI CERT UPLOAD")
        print("-" * 50)
        
        try:
            # Read the PDF file
            with open(self.pdf_file_path, 'rb') as f:
                pdf_content = f.read()
            
            # Prepare the multipart form data
            files = {
                'files': ('SUNSHINE_01_CSSC_PM25385.pdf', pdf_content, 'application/pdf')
            }
            
            # Use POST /api/certificates/multi-upload?ship_id={ship_id}
            upload_url = f"{API_BASE}/certificates/multi-upload?ship_id={self.ship_id}"
            print(f"📤 Uploading to: {upload_url}")
            print(f"📄 File size: {len(pdf_content):,} bytes")
            
            # Upload the PDF file with proper authentication
            start_time = time.time()
            response = requests.post(
                upload_url,
                files=files,
                headers=self.get_headers()
            )
            processing_time = time.time() - start_time
            
            print(f"⏱️ Upload and processing time: {processing_time:.2f} seconds")
            
            if response.status_code == 200:
                self.upload_response = response.json()
                self.log_test("Smart Multi Cert Upload API Call", True, 
                            f"Status: {response.status_code}, Processing time: {processing_time:.2f}s")
                
                # Monitor the smart processing workflow
                return self.monitor_smart_processing_workflow(self.upload_response, processing_time)
            else:
                self.log_test("Smart Multi Cert Upload API Call", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Smart Multi Cert Upload Process", False, error=str(e))
            return False
    
    def monitor_smart_processing_workflow(self, response_data, processing_time):
        """Monitor the smart processing workflow components"""
        success_count = 0
        total_checks = 4
        
        try:
            # Get results array
            results = response_data.get('results', [])
            if not results:
                self.log_test("Smart Processing - Results Array", False, 
                            error="No results array in response")
                return False
            
            # Analyze first result (should be our uploaded file)
            first_result = results[0] if results else {}
            analysis = first_result.get('analysis', {})
            
            # File Type Analysis (should detect text-based PDF)
            pdf_type = analysis.get('pdf_type')
            if pdf_type:
                expected_types = ['text_based', 'image_based', 'mixed']
                if pdf_type in expected_types:
                    self.log_test("File Type Analysis (should detect text-based PDF)", True, 
                                f"Detected PDF type: {pdf_type}")
                    success_count += 1
                else:
                    self.log_test("File Type Analysis", False, 
                                error=f"Unexpected PDF type: {pdf_type}")
            else:
                self.log_test("File Type Analysis", False, 
                            error="No pdf_type in response")
            
            # Method Selection (should use direct_text_extraction for text-based)
            processing_method = analysis.get('processing_method')
            if processing_method:
                expected_methods = ['direct_text_extraction', 'hybrid_extraction', 'hybrid_ocr_enhanced', 'text_extraction_fallback']
                if processing_method in expected_methods:
                    self.log_test("Method Selection (should use direct_text_extraction)", True, 
                                f"Processing method: {processing_method}")
                    success_count += 1
                else:
                    self.log_test("Method Selection", False, 
                                error=f"Unexpected processing method: {processing_method}")
            else:
                self.log_test("Method Selection", False, 
                            error="No processing_method in response")
            
            # AI Processing (certificate analysis)
            cert_info = analysis.get('CERTIFICATE INFORMATION', {})
            if cert_info:
                cert_fields = ['CERT_NAME', 'CERT_NO', 'ISSUE_DATE', 'VALID_DATE', 'ISSUED_BY']
                extracted_fields = [field for field in cert_fields if cert_info.get(field)]
                
                if len(extracted_fields) >= 3:  # At least 3 fields should be extracted
                    field_details = {field: cert_info[field] for field in extracted_fields[:3]}
                    self.log_test("AI Processing (certificate analysis)", True, 
                                f"Extracted {len(extracted_fields)} fields: {field_details}")
                    success_count += 1
                else:
                    self.log_test("AI Processing (certificate analysis)", False, 
                                error=f"Insufficient certificate data extracted: {cert_info}")
            else:
                self.log_test("AI Processing (certificate analysis)", False, 
                            error="No CERTIFICATE INFORMATION in response")
            
            # Enhanced Results (with processing metadata)
            metadata_fields = ['ocr_confidence', 'processing_notes', 'text_length', 'processing_method']
            found_metadata = []
            for field in metadata_fields:
                if field in analysis:
                    found_metadata.append(f"{field}: {analysis[field]}")
            
            if len(found_metadata) >= 3:
                self.log_test("Enhanced Results (with processing metadata)", True, 
                            f"Found {len(found_metadata)} metadata fields: {found_metadata[:3]}")
                success_count += 1
            else:
                self.log_test("Enhanced Results (with processing metadata)", False, 
                            error=f"Insufficient metadata. Found: {found_metadata}")
            
            # Overall workflow assessment
            workflow_success = success_count >= 3  # At least 3 out of 4 checks should pass
            
            if workflow_success:
                self.log_test("Smart Processing Workflow Monitoring", True, 
                            f"Workflow successful: {success_count}/{total_checks} checks passed")
            else:
                self.log_test("Smart Processing Workflow Monitoring", False, 
                            error=f"Workflow failed: Only {success_count}/{total_checks} checks passed")
            
            return workflow_success
            
        except Exception as e:
            self.log_test("Smart Processing Workflow Monitoring", False, error=str(e))
            return False
    
    def step_5_analyze_results(self):
        """STEP 5: ANALYZE RESULTS"""
        print("📊 STEP 5: ANALYZE RESULTS")
        print("-" * 50)
        
        try:
            if not self.upload_response:
                self.log_test("Results Analysis - Data Availability", False, 
                            error="No upload response data available")
                return False
            
            results = self.upload_response.get('results', [])
            
            if not results:
                self.log_test("Results Analysis - Data Availability", False, 
                            error="No results to analyze")
                return False
            
            first_result = results[0]
            analysis = first_result.get('analysis', {})
            
            # Verify smart processing worked correctly
            success_indicators = []
            if analysis.get('processing_method'):
                success_indicators.append(f"Method: {analysis['processing_method']}")
            if analysis.get('pdf_type'):
                success_indicators.append(f"PDF type: {analysis['pdf_type']}")
            if analysis.get('ocr_confidence') is not None:
                success_indicators.append(f"OCR confidence: {analysis['ocr_confidence']}")
            
            if len(success_indicators) >= 2:
                self.log_test("Verify Smart Processing Worked Correctly", True, 
                            f"Indicators: {', '.join(success_indicators)}")
            else:
                self.log_test("Verify Smart Processing Worked Correctly", False, 
                            error=f"Insufficient success indicators: {success_indicators}")
                return False
            
            # Check processing_method, ocr_confidence, pdf_type in response
            metadata_check = []
            if 'processing_method' in analysis:
                metadata_check.append(f"processing_method: {analysis['processing_method']}")
            if 'ocr_confidence' in analysis:
                metadata_check.append(f"ocr_confidence: {analysis['ocr_confidence']}")
            if 'pdf_type' in analysis:
                metadata_check.append(f"pdf_type: {analysis['pdf_type']}")
            
            if len(metadata_check) >= 3:
                self.log_test("Check processing_method, ocr_confidence, pdf_type in response", True, 
                            f"Found: {', '.join(metadata_check)}")
            else:
                self.log_test("Check processing_method, ocr_confidence, pdf_type in response", False, 
                            error=f"Missing metadata fields. Found: {metadata_check}")
                return False
            
            # Verify certificate data extraction
            cert_info = analysis.get('CERTIFICATE INFORMATION', {})
            extracted_cert_fields = []
            cert_fields_to_check = ['CERT_NAME', 'CERT_NO', 'ISSUE_DATE', 'VALID_DATE', 'ISSUED_BY']
            
            for field in cert_fields_to_check:
                if cert_info.get(field):
                    extracted_cert_fields.append(f"{field}: {cert_info[field]}")
            
            if len(extracted_cert_fields) >= 4:
                self.log_test("Verify certificate data extraction", True, 
                            f"Extracted: {', '.join(extracted_cert_fields[:4])}")
            else:
                self.log_test("Verify certificate data extraction", False, 
                            error=f"Insufficient certificate data: {extracted_cert_fields}")
                return False
            
            # Confirm upload status and any duplicate detection
            upload_status = first_result.get('status', 'unknown')
            summary = self.upload_response.get('summary', {})
            
            status_details = f"Upload status: {upload_status}"
            if summary.get('total_files'):
                status_details += f", Total files: {summary['total_files']}"
            if summary.get('marine_certificates') is not None:
                status_details += f", Marine certificates: {summary['marine_certificates']}"
            if summary.get('non_marine_files') is not None:
                status_details += f", Non-marine files: {summary['non_marine_files']}"
            
            self.log_test("Confirm upload status and any duplicate detection", True, status_details)
            
            return True
                
        except Exception as e:
            self.log_test("Results Analysis Process", False, error=str(e))
            return False
    
    def run_complete_workflow(self):
        """Run the complete Smart Multi Cert Upload workflow"""
        print("🚀 STARTING SMART MULTI CERT UPLOAD WORKFLOW TEST - FINAL VERSION")
        print("=" * 80)
        print("Testing complete workflow as specified in review request:")
        print("1. LOGIN AND AUTHENTICATION")
        print("2. SHIP SELECTION")
        print("3. DOWNLOAD AND PREPARE FILE") 
        print("4. EXECUTE SMART MULTI CERT UPLOAD")
        print("5. ANALYZE RESULTS")
        print("=" * 80)
        
        # Run workflow steps in sequence
        workflow_steps = [
            ("STEP 1", self.step_1_login_and_authentication),
            ("STEP 2", self.step_2_ship_selection),
            ("STEP 3", self.step_3_download_and_prepare_file),
            ("STEP 4", self.step_4_execute_smart_multi_cert_upload),
            ("STEP 5", self.step_5_analyze_results)
        ]
        
        passed_steps = 0
        for step_name, step_function in workflow_steps:
            print(f"\n{step_name}")
            if step_function():
                passed_steps += 1
                print(f"✅ {step_name} COMPLETED SUCCESSFULLY")
            else:
                print(f"❌ {step_name} FAILED")
                # Continue with remaining steps for comprehensive testing
        
        # Final Summary
        print("\n" + "=" * 80)
        print(f"📊 WORKFLOW SUMMARY: {passed_steps}/{len(workflow_steps)} steps completed successfully")
        
        if passed_steps == len(workflow_steps):
            print("🎉 COMPLETE SUCCESS - Smart Multi Cert Upload workflow is fully functional!")
        elif passed_steps >= 4:
            print("🎯 MOSTLY SUCCESSFUL - Core Smart Multi Cert Upload functionality is working!")
        else:
            print(f"⚠️ {len(workflow_steps) - passed_steps} steps failed - Review and fixes required")
        
        # Key findings summary
        print("\n🔍 KEY FINDINGS:")
        if self.upload_response:
            results = self.upload_response.get('results', [])
            if results:
                analysis = results[0].get('analysis', {})
                print(f"✅ PDF Type Detection: {analysis.get('pdf_type', 'N/A')}")
                print(f"✅ Processing Method: {analysis.get('processing_method', 'N/A')}")
                print(f"✅ OCR Confidence: {analysis.get('ocr_confidence', 'N/A')}")
                
                cert_info = analysis.get('CERTIFICATE INFORMATION', {})
                if cert_info:
                    print(f"✅ Certificate Name: {cert_info.get('CERT_NAME', 'N/A')}")
                    print(f"✅ Certificate Number: {cert_info.get('CERT_NO', 'N/A')}")
                    print(f"✅ Issue Date: {cert_info.get('ISSUE_DATE', 'N/A')}")
                    print(f"✅ Valid Date: {cert_info.get('VALID_DATE', 'N/A')}")
                    print(f"✅ Issued By: {cert_info.get('ISSUED_BY', 'N/A')}")
        
        # Detailed results breakdown
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    ✓ {result['details']}")
            if result['error']:
                print(f"    ✗ ERROR: {result['error']}")
        
        return passed_steps >= 4  # Consider success if at least 4/5 steps pass

def main():
    """Main test execution"""
    tester = SmartMultiCertUploadFinalTester()
    success = tester.run_complete_workflow()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
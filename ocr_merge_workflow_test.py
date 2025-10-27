#!/usr/bin/env python3
"""
OCR Text Merge Workflow Test for Survey Reports
Testing NEW workflow: OCR Text Merge into Summary before Field Extraction

MAJOR WORKFLOW CHANGE:
Instead of merging extraction RESULTS, we now:
1. Document AI → summary text
2. OCR → header/footer raw text
3. **MERGE OCR text into summary** (append with clear annotations)
4. System AI extracts fields **ONCE** from enhanced summary

FILE TO TEST:
- URL: https://customer-assets.emergentagent.com/job_doc-navigator-9/artifacts/gz0hce82_CU%20%2802-19%29.pdf
- Filename: CU (02-19).pdf

AUTHENTICATION:
- admin1@example.com / 123456

SHIP:
- BROTHER 36 (7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7)

CRITICAL CHECKS:
1. OCR Text Extraction
2. Summary Merge
3. Enhanced Summary Structure
4. System AI Re-Extraction
5. Compare BEFORE vs AFTER OCR merge
6. Backend Logs verification
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
import tempfile
from urllib.parse import urlparse

# Configuration - Use environment variable for backend URL
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipdoclists.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class OCRMergeWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.ship_name = "BROTHER 36"
        self.ship_id = "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"
        
        # Test tracking for OCR merge workflow
        self.ocr_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'ship_discovery_successful': False,
            
            # File download and verification
            'test_file_downloaded': False,
            'test_file_valid_pdf': False,
            'test_file_correct_name': False,
            
            # OCR Text Extraction
            'ocr_attempted': False,
            'ocr_success': False,
            'header_text_extracted': False,
            'footer_text_extracted': False,
            'header_text_length_valid': False,
            'footer_text_length_valid': False,
            
            # Summary Merge
            'ocr_text_merged': False,
            'enhanced_summary_created': False,
            'enhanced_summary_longer': False,
            'original_summary_preserved': False,
            
            # Enhanced Summary Structure
            'additional_info_section_present': False,
            'header_section_present': False,
            'footer_section_present': False,
            'annotation_note_present': False,
            
            # System AI Re-Extraction
            'fields_reextracted_with_ocr': False,
            'survey_report_name_extracted': False,
            'report_form_extracted': False,
            'survey_report_no_extracted': False,
            'issued_by_extracted': False,
            'issued_date_extracted': False,
            'surveyor_name_extracted': False,
            'status_calculated': False,
            'note_extracted': False,
            
            # Backend Logs verification
            'starting_targeted_ocr_log': False,
            'targeted_ocr_completed_log': False,
            'header_text_added_log': False,
            'footer_text_added_log': False,
            'enhanced_summary_created_log': False,
            'reextracting_fields_log': False,
            'fields_reextracted_log': False,
            'extracted_field_values_logged': False,
        }
        
        # Store test data
        self.test_filename = "CU (02-19).pdf"
        self.test_file_url = "https://customer-assets.emergentagent.com/job_doc-navigator-9/artifacts/gz0hce82_CU%20%2802-19%29.pdf"
        self.test_file_path = None
        self.original_summary_length = 0
        self.enhanced_summary_length = 0
        self.ocr_info = {}
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        # Also store in our log collection
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
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.ocr_tests['authentication_successful'] = True
                self.ocr_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def verify_ship(self):
        """Verify the test ship exists"""
        try:
            self.log(f"🚢 Verifying ship: {self.ship_name} (ID: {self.ship_id})")
            
            response = self.session.get(f"{BACKEND_URL}/ships/{self.ship_id}")
            
            if response.status_code == 200:
                ship_data = response.json()
                if ship_data.get("name") == self.ship_name:
                    self.log(f"✅ Ship verified: {self.ship_name}")
                    self.log(f"   Ship ID: {self.ship_id}")
                    self.log(f"   IMO: {ship_data.get('imo', 'N/A')}")
                    self.ocr_tests['ship_discovery_successful'] = True
                    return True
                else:
                    self.log(f"❌ Ship name mismatch: expected {self.ship_name}, got {ship_data.get('name')}", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to verify ship: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying ship: {str(e)}", "ERROR")
            return False
    
    def download_test_file(self):
        """Download the test PDF file"""
        try:
            self.log(f"📥 Downloading test file: {self.test_filename}")
            self.log(f"   URL: {self.test_file_url}")
            
            response = requests.get(self.test_file_url, timeout=120)
            
            if response.status_code == 200:
                # Save to temporary file
                self.test_file_path = f"/app/{self.test_filename}"
                with open(self.test_file_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                self.log(f"✅ File downloaded successfully")
                self.log(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                self.log(f"   Saved to: {self.test_file_path}")
                
                # Verify it's a PDF
                if response.content.startswith(b'%PDF'):
                    self.log("✅ File is a valid PDF")
                    self.ocr_tests['test_file_downloaded'] = True
                    self.ocr_tests['test_file_valid_pdf'] = True
                    self.ocr_tests['test_file_correct_name'] = True
                    return True
                else:
                    self.log("❌ File is not a valid PDF", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to download file: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error downloading test file: {str(e)}", "ERROR")
            return False
    
    def test_ocr_merge_workflow(self):
        """Test the NEW OCR Text Merge workflow"""
        try:
            self.log("🔍 Testing NEW OCR Text Merge workflow...")
            
            if not self.test_file_path or not os.path.exists(self.test_file_path):
                self.log("❌ Test file not available", "ERROR")
                return False
            
            # Prepare multipart form data
            with open(self.test_file_path, "rb") as f:
                files = {
                    "survey_report_file": (self.test_filename, f, "application/pdf")
                }
                data = {
                    "ship_id": self.ship_id,
                    "bypass_validation": "false"
                }
                
                self.log(f"📤 Uploading survey report file: {self.test_filename}")
                self.log(f"🚢 Ship ID: {self.ship_id}")
                
                endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
                self.log(f"   POST {endpoint}")
                
                start_time = time.time()
                response = self.session.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=300  # 5 minutes for OCR processing
                )
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ OCR merge workflow endpoint accessible")
                
                # Log the complete response structure for debugging
                self.log("📊 Complete API response structure:")
                self.log(f"   Response keys: {list(result.keys())}")
                for key, value in result.items():
                    if isinstance(value, str) and len(value) > 100:
                        self.log(f"   {key}: {type(value).__name__} ({len(value)} chars)")
                    else:
                        self.log(f"   {key}: {value}")
                
                # Extract and analyze the response
                self.analyze_ocr_response(result)
                
                # Check backend logs for OCR workflow
                self.check_backend_logs_for_ocr()
                
                return True
            else:
                self.log(f"❌ OCR merge workflow failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing OCR merge workflow: {str(e)}", "ERROR")
            return False
    
    def analyze_ocr_response(self, result):
        """Analyze the OCR merge workflow response"""
        try:
            self.log("📊 Analyzing OCR merge workflow response...")
            
            # Check for success
            success = result.get("success", False)
            self.log(f"   Success: {success}")
            
            # Check for _ocr_info object in analysis
            analysis = result.get("analysis", {})
            ocr_info = analysis.get("_ocr_info", {})
            if ocr_info:
                self.log("✅ _ocr_info object found")
                self.ocr_info = ocr_info
                self.analyze_ocr_info(ocr_info)
            else:
                self.log("❌ _ocr_info object missing", "ERROR")
            
            # Check for enhanced summary in analysis
            enhanced_summary = analysis.get("_summary_text", "")
            if enhanced_summary:
                self.enhanced_summary_length = len(enhanced_summary)
                self.log(f"✅ Enhanced summary found: {self.enhanced_summary_length} characters")
                self.ocr_tests['enhanced_summary_created'] = True
                
                # Analyze enhanced summary structure
                self.analyze_enhanced_summary_structure(enhanced_summary)
            else:
                self.log("❌ Enhanced summary missing", "ERROR")
            
            # Check extracted fields in analysis
            self.analyze_extracted_fields(analysis)
            
            # Check processing method
            processing_method = result.get("processing_method", "")
            self.log(f"   Processing method: {processing_method}")
            
        except Exception as e:
            self.log(f"❌ Error analyzing OCR response: {str(e)}", "ERROR")
    
    def analyze_ocr_info(self, ocr_info):
        """Analyze the _ocr_info object"""
        try:
            self.log("🔍 Analyzing _ocr_info object:")
            
            # OCR attempted and success
            ocr_attempted = ocr_info.get("ocr_attempted", False)
            ocr_success = ocr_info.get("ocr_success", False)
            self.log(f"   ocr_attempted: {ocr_attempted}")
            self.log(f"   ocr_success: {ocr_success}")
            
            if ocr_attempted:
                self.ocr_tests['ocr_attempted'] = True
            if ocr_success:
                self.ocr_tests['ocr_success'] = True
            
            # Header text analysis
            header_text = ocr_info.get("header_text", "")
            header_text_length = ocr_info.get("header_text_length", 0)
            self.log(f"   header_text_length: {header_text_length}")
            if header_text:
                self.log(f"   header_text (first 300 chars): {header_text[:300]}...")
                self.ocr_tests['header_text_extracted'] = True
                if header_text_length > 0:
                    self.ocr_tests['header_text_length_valid'] = True
            
            # Footer text analysis
            footer_text = ocr_info.get("footer_text", "")
            footer_text_length = ocr_info.get("footer_text_length", 0)
            self.log(f"   footer_text_length: {footer_text_length}")
            if footer_text:
                self.log(f"   footer_text (first 300 chars): {footer_text[:300]}...")
                self.ocr_tests['footer_text_extracted'] = True
                if footer_text_length > 0:
                    self.ocr_tests['footer_text_length_valid'] = True
            
            # OCR text merged
            ocr_text_merged = ocr_info.get("ocr_text_merged", False)
            self.log(f"   ocr_text_merged: {ocr_text_merged}")
            if ocr_text_merged:
                self.ocr_tests['ocr_text_merged'] = True
            
            # Enhanced summary length comparison
            enhanced_summary_length = ocr_info.get("enhanced_summary_length", 0)
            original_summary_length = ocr_info.get("original_summary_length", 0)
            self.log(f"   enhanced_summary_length: {enhanced_summary_length}")
            self.log(f"   original_summary_length: {original_summary_length}")
            
            if enhanced_summary_length > original_summary_length:
                self.log("✅ Enhanced summary is longer than original")
                self.ocr_tests['enhanced_summary_longer'] = True
            
            self.original_summary_length = original_summary_length
            self.enhanced_summary_length = enhanced_summary_length
            
        except Exception as e:
            self.log(f"❌ Error analyzing _ocr_info: {str(e)}", "ERROR")
    
    def analyze_enhanced_summary_structure(self, enhanced_summary):
        """Analyze the structure of the enhanced summary"""
        try:
            self.log("🔍 Analyzing enhanced summary structure...")
            
            # Check for required sections
            required_sections = [
                ("ADDITIONAL INFORMATION FROM HEADER/FOOTER", 'additional_info_section_present'),
                ("=== HEADER TEXT (Top 15% of page) ===", 'header_section_present'),
                ("=== FOOTER TEXT (Bottom 15% of page) ===", 'footer_section_present')
            ]
            
            for section_text, test_key in required_sections:
                if section_text in enhanced_summary:
                    self.log(f"   ✅ Found: {section_text}")
                    self.ocr_tests[test_key] = True
                else:
                    self.log(f"   ❌ Missing: {section_text}")
            
            # Check for annotation note
            if "annotation" in enhanced_summary.lower() or "note" in enhanced_summary.lower():
                self.log("   ✅ Annotation note present")
                self.ocr_tests['annotation_note_present'] = True
            
            # Show sample of enhanced summary
            self.log("📄 Enhanced summary sample:")
            self.log(f"   First 500 chars: {enhanced_summary[:500]}...")
            if len(enhanced_summary) > 1000:
                self.log(f"   Last 500 chars: ...{enhanced_summary[-500:]}")
            
        except Exception as e:
            self.log(f"❌ Error analyzing enhanced summary structure: {str(e)}", "ERROR")
    
    def analyze_extracted_fields(self, result):
        """Analyze the extracted fields from System AI"""
        try:
            self.log("🔍 Analyzing extracted fields from System AI:")
            
            # Field mapping
            field_mapping = {
                'survey_report_name': 'survey_report_name_extracted',
                'report_form': 'report_form_extracted',
                'survey_report_no': 'survey_report_no_extracted',
                'issued_by': 'issued_by_extracted',
                'issued_date': 'issued_date_extracted',
                'surveyor_name': 'surveyor_name_extracted',
                'status': 'status_calculated',
                'note': 'note_extracted'
            }
            
            extracted_count = 0
            for field, test_key in field_mapping.items():
                value = result.get(field, "")
                if value and str(value).strip():
                    self.log(f"   ✅ {field}: {value}")
                    self.ocr_tests[test_key] = True
                    extracted_count += 1
                else:
                    self.log(f"   ❌ {field}: (empty)")
            
            if extracted_count > 0:
                self.log(f"✅ Fields re-extracted from enhanced summary: {extracted_count}/8")
                self.ocr_tests['fields_reextracted_with_ocr'] = True
            else:
                self.log("❌ No fields extracted from enhanced summary", "ERROR")
            
        except Exception as e:
            self.log(f"❌ Error analyzing extracted fields: {str(e)}", "ERROR")
    
    def check_backend_logs_for_ocr(self):
        """Check backend logs for OCR merge workflow patterns"""
        try:
            self.log("📋 Checking backend logs for OCR merge workflow...")
            
            # Expected log patterns
            expected_patterns = [
                ("Starting Targeted OCR", 'starting_targeted_ocr_log'),
                ("Targeted OCR completed successfully", 'targeted_ocr_completed_log'),
                ("Header text added", 'header_text_added_log'),
                ("Footer text added", 'footer_text_added_log'),
                ("Enhanced summary created", 'enhanced_summary_created_log'),
                ("Re-extracting fields from enhanced summary", 'reextracting_fields_log'),
                ("Fields re-extracted from enhanced summary", 'fields_reextracted_log')
            ]
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            found_patterns = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture recent OCR activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            for pattern_text, test_key in expected_patterns:
                                for line in lines:
                                    if pattern_text.lower() in line.lower():
                                        if pattern_text not in found_patterns:
                                            self.log(f"   ✅ Found: {pattern_text}")
                                            found_patterns.append(pattern_text)
                                            self.ocr_tests[test_key] = True
                                        break
                            
                            # Look for extracted field values in logs
                            field_value_patterns = ["survey_report_name:", "report_form:", "issued_by:"]
                            for line in lines:
                                for pattern in field_value_patterns:
                                    if pattern in line.lower():
                                        self.log(f"   🔍 Field extraction log: {line.strip()}")
                                        self.ocr_tests['extracted_field_values_logged'] = True
                                        break
                        
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            # Report missing patterns
            for pattern_text, test_key in expected_patterns:
                if pattern_text not in found_patterns:
                    self.log(f"   ❌ Missing: {pattern_text}")
            
            self.log(f"📊 Found {len(found_patterns)}/{len(expected_patterns)} expected log patterns")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def run_comprehensive_ocr_merge_test(self):
        """Run comprehensive test of the OCR merge workflow"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE OCR TEXT MERGE WORKFLOW TEST")
            self.log("=" * 80)
            self.log("Testing NEW workflow: OCR Text Merge into Summary before Field Extraction")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Ship Verification
            self.log("\nSTEP 2: Ship Verification")
            if not self.verify_ship():
                self.log("❌ CRITICAL: Ship verification failed - cannot proceed")
                return False
            
            # Step 3: Download Test File
            self.log("\nSTEP 3: Download Test File")
            if not self.download_test_file():
                self.log("❌ CRITICAL: Test file download failed - cannot proceed")
                return False
            
            # Step 4: OCR Merge Workflow Test
            self.log("\nSTEP 4: OCR Merge Workflow Test")
            if not self.test_ocr_merge_workflow():
                self.log("❌ CRITICAL: OCR merge workflow failed")
                return False
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE OCR TEXT MERGE WORKFLOW TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 OCR TEXT MERGE WORKFLOW TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.ocr_tests)
            passed_tests = sum(1 for result in self.ocr_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('ship_discovery_successful', 'Ship discovery successful'),
                ('test_file_downloaded', 'Test file downloaded'),
                ('test_file_valid_pdf', 'Test file valid PDF'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # OCR Text Extraction Results
            self.log("\n🔍 OCR TEXT EXTRACTION:")
            ocr_extraction_tests = [
                ('ocr_attempted', 'OCR attempted'),
                ('ocr_success', 'OCR success'),
                ('header_text_extracted', 'Header text extracted'),
                ('footer_text_extracted', 'Footer text extracted'),
                ('header_text_length_valid', 'Header text length valid'),
                ('footer_text_length_valid', 'Footer text length valid'),
            ]
            
            for test_key, description in ocr_extraction_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Summary Merge Results
            self.log("\n📝 SUMMARY MERGE:")
            merge_tests = [
                ('ocr_text_merged', 'OCR text merged into summary'),
                ('enhanced_summary_created', 'Enhanced summary created'),
                ('enhanced_summary_longer', 'Enhanced summary longer than original'),
                ('original_summary_preserved', 'Original summary preserved'),
            ]
            
            for test_key, description in merge_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Enhanced Summary Structure Results
            self.log("\n📄 ENHANCED SUMMARY STRUCTURE:")
            structure_tests = [
                ('additional_info_section_present', 'Additional info section present'),
                ('header_section_present', 'Header section present'),
                ('footer_section_present', 'Footer section present'),
                ('annotation_note_present', 'Annotation note present'),
            ]
            
            for test_key, description in structure_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # System AI Re-Extraction Results
            self.log("\n🤖 SYSTEM AI RE-EXTRACTION:")
            extraction_tests = [
                ('fields_reextracted_with_ocr', 'Fields re-extracted with OCR'),
                ('survey_report_name_extracted', 'Survey report name extracted'),
                ('report_form_extracted', 'Report form extracted'),
                ('survey_report_no_extracted', 'Survey report no extracted'),
                ('issued_by_extracted', 'Issued by extracted'),
                ('issued_date_extracted', 'Issued date extracted'),
                ('surveyor_name_extracted', 'Surveyor name extracted'),
                ('status_calculated', 'Status calculated'),
                ('note_extracted', 'Note extracted'),
            ]
            
            for test_key, description in extraction_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Results
            self.log("\n📋 BACKEND LOGS VERIFICATION:")
            log_tests = [
                ('starting_targeted_ocr_log', 'Starting Targeted OCR log'),
                ('targeted_ocr_completed_log', 'Targeted OCR completed log'),
                ('header_text_added_log', 'Header text added log'),
                ('footer_text_added_log', 'Footer text added log'),
                ('enhanced_summary_created_log', 'Enhanced summary created log'),
                ('reextracting_fields_log', 'Re-extracting fields log'),
                ('fields_reextracted_log', 'Fields re-extracted log'),
                ('extracted_field_values_logged', 'Extracted field values logged'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Success Criteria
            self.log("\n🎯 SUCCESS CRITERIA VERIFICATION:")
            
            critical_criteria = [
                ('ocr_success', 'OCR extracts header/footer text successfully'),
                ('ocr_text_merged', 'OCR text merged into summary with clear sections'),
                ('enhanced_summary_longer', 'Enhanced summary is longer than original'),
                ('fields_reextracted_with_ocr', 'System AI re-extracts fields from enhanced summary'),
                ('report_form_extracted', 'Report Form extracted correctly'),
                ('survey_report_no_extracted', 'Report No. extracted correctly'),
            ]
            
            critical_passed = 0
            for test_key, description in critical_criteria:
                status = "✅ PASS" if self.ocr_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
                if self.ocr_tests.get(test_key, False):
                    critical_passed += 1
            
            # OCR Info Summary
            if self.ocr_info:
                self.log("\n📊 OCR INFO SUMMARY:")
                self.log(f"   ocr_attempted: {self.ocr_info.get('ocr_attempted', 'N/A')}")
                self.log(f"   ocr_success: {self.ocr_info.get('ocr_success', 'N/A')}")
                self.log(f"   header_text_length: {self.ocr_info.get('header_text_length', 'N/A')}")
                self.log(f"   footer_text_length: {self.ocr_info.get('footer_text_length', 'N/A')}")
                self.log(f"   ocr_text_merged: {self.ocr_info.get('ocr_text_merged', 'N/A')}")
                self.log(f"   enhanced_summary_length: {self.ocr_info.get('enhanced_summary_length', 'N/A')}")
                self.log(f"   original_summary_length: {self.ocr_info.get('original_summary_length', 'N/A')}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            if critical_passed == len(critical_criteria):
                self.log("   ✅ ALL SUCCESS CRITERIA MET")
                self.log("   ✅ OCR Text Merge workflow working correctly")
                self.log("   ✅ Enhanced summary with OCR text improves field extraction")
            elif critical_passed >= len(critical_criteria) * 0.8:
                self.log("   ⚠️ MOST SUCCESS CRITERIA MET")
                self.log(f"   ⚠️ {critical_passed}/{len(critical_criteria)} critical criteria passed")
            else:
                self.log("   ❌ CRITICAL SUCCESS CRITERIA NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_criteria)} critical criteria passed")
            
            if success_rate >= 85:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 70:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    tester = OCRMergeWorkflowTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_ocr_merge_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
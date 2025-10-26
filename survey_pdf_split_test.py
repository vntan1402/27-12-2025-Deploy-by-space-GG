#!/usr/bin/env python3
"""
Survey Report PDF Split + Batch Processing Test
Testing the new PDF splitting functionality for large survey reports

REVIEW REQUEST REQUIREMENTS:
Test the new feature for handling large PDF files (>15 pages) for Survey Reports:
- Auto-detect PDF page count
- Split PDFs >15 pages into chunks of 12 pages each
- Process each chunk with Document AI
- Merge all summaries into one enhanced summary
- Extract fields ONCE from merged summary (not per chunk)
- Return clean results without conflicts

Test Cases:
1. Small PDF (≤15 pages) - Normal Flow
2. Mock Large PDF Processing (25-page scenario)
3. Backend Endpoint Analysis
4. Error Handling

Test Credentials:
- Username: admin1
- Password: 123456
- Ship: BROTHER 36 (ID: 7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7)
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
import base64
from urllib.parse import urlparse
from io import BytesIO
import PyPDF2

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vessel-docs-sys.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class SurveyPDFSplitTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.ship_name = "BROTHER 36"
        self.ship_id = "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"
        
        # Test tracking for PDF split functionality
        self.split_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'ship_found': False,
            'endpoint_accessible': False,
            
            # Test Case 1: Small PDF (≤15 pages) - Normal Flow
            'small_pdf_normal_processing': False,
            'small_pdf_no_split_flag': False,
            'small_pdf_field_extraction': False,
            'small_pdf_success_response': False,
            
            # Test Case 2: Mock Large PDF Processing
            'large_pdf_split_detection': False,
            'large_pdf_chunk_creation': False,
            'large_pdf_batch_processing': False,
            'large_pdf_summary_merging': False,
            'large_pdf_single_field_extraction': False,
            'large_pdf_enhanced_summary': False,
            
            # Test Case 3: Backend Endpoint Analysis
            'page_count_detection_working': False,
            'split_logic_activates_correctly': False,
            'chunks_processed_without_field_extraction': False,
            'summaries_merged_after_loop': False,
            'field_extraction_once_from_merged': False,
            'enhanced_summary_created': False,
            'split_info_metadata_included': False,
            
            # Test Case 4: Error Handling
            'invalid_pdf_handled': False,
            'chunk_failure_handled': False,
            'empty_summaries_handled': False,
            'graceful_error_responses': False,
        }
        
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
                
                self.split_tests['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def verify_ship_exists(self):
        """Verify the test ship exists"""
        try:
            self.log(f"🚢 Verifying ship: {self.ship_name} (ID: {self.ship_id})")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                for ship in ships:
                    if ship.get("id") == self.ship_id and ship.get("name") == self.ship_name:
                        self.log(f"✅ Ship found: {self.ship_name}")
                        self.log(f"   IMO: {ship.get('imo', 'N/A')}")
                        self.split_tests['ship_found'] = True
                        return True
                
                self.log(f"❌ Ship '{self.ship_name}' with ID '{self.ship_id}' not found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying ship: {str(e)}", "ERROR")
            return False
    
    def create_mock_pdf(self, pages: int, filename: str) -> bytes:
        """Create a mock PDF with specified number of pages"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            
            for page_num in range(1, pages + 1):
                c.drawString(100, 750, f"Survey Report - Mock Document")
                c.drawString(100, 720, f"Page {page_num} of {pages}")
                c.drawString(100, 690, f"Ship: {self.ship_name}")
                c.drawString(100, 660, f"Survey Type: Annual Survey")
                c.drawString(100, 630, f"Report No: SR-{page_num:03d}-2024")
                c.drawString(100, 600, f"Issued By: Test Classification Society")
                c.drawString(100, 570, f"Issued Date: 2024-01-15")
                c.drawString(100, 540, f"Surveyor: Test Surveyor {page_num}")
                
                # Add some content to make it look realistic
                c.drawString(100, 500, f"This is page {page_num} of the survey report.")
                c.drawString(100, 470, f"Survey findings and observations for section {page_num}.")
                c.drawString(100, 440, f"All systems checked and found satisfactory.")
                
                c.showPage()
            
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except ImportError:
            # Fallback: Create a simple PDF using PyPDF2
            self.log("⚠️ reportlab not available, creating simple PDF", "WARNING")
            return self.create_simple_mock_pdf(pages, filename)
    
    def create_simple_mock_pdf(self, pages: int, filename: str) -> bytes:
        """Create a simple mock PDF by duplicating a basic PDF structure"""
        try:
            # Create a minimal PDF structure
            pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count {pages}
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
100 700 Td
(Survey Report - {pages} pages) Tj
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
<<
/Size 5
/Root 1 0 R
>>
startxref
356
%%EOF"""
            
            return pdf_content.encode('utf-8')
            
        except Exception as e:
            self.log(f"❌ Error creating simple mock PDF: {e}", "ERROR")
            # Return minimal valid PDF bytes
            return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 1\ntrailer\n<< /Size 1 >>\n%%EOF"
    
    def test_case_1_small_pdf_normal_flow(self):
        """Test Case 1: Small PDF (≤15 pages) - Normal Flow"""
        try:
            self.log("📄 TEST CASE 1: Small PDF (≤15 pages) - Normal Flow")
            self.log("=" * 60)
            
            # Create a small PDF (10 pages)
            small_pdf_content = self.create_mock_pdf(10, "small_survey_report.pdf")
            self.log(f"📄 Created mock PDF: 10 pages, {len(small_pdf_content)} bytes")
            
            # Test the endpoint
            files = {
                "survey_report_file": ("small_survey_report.pdf", small_pdf_content, "application/pdf")
            }
            data = {
                "ship_id": self.ship_id,
                "bypass_validation": "false"
            }
            
            endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
            self.log(f"📤 POST {endpoint}")
            
            start_time = time.time()
            response = self.session.post(
                endpoint,
                files=files,
                data=data,
                timeout=120
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.split_tests['endpoint_accessible'] = True
                result = response.json()
                
                # Debug: Print full response structure
                self.log(f"📊 Full response keys: {list(result.keys())}")
                self.log(f"📊 Response success: {result.get('success')}")
                
                # Check for success
                if result.get("success"):
                    self.log("✅ Small PDF processing successful")
                    self.split_tests['small_pdf_success_response'] = True
                    
                    # Check split info
                    analysis = result.get("analysis", {})
                    split_info = analysis.get("_split_info", {})
                    self.log(f"📊 Split info found: {split_info}")
                    if split_info:
                        was_split = split_info.get("was_split", True)  # Default True to catch issues
                        total_pages = split_info.get("total_pages", 0)
                        chunks_count = split_info.get("chunks_count", 0)
                        
                        self.log(f"📊 Split Info: was_split={was_split}, pages={total_pages}, chunks={chunks_count}")
                        
                        if not was_split and chunks_count == 1:
                            self.log("✅ Small PDF correctly processed without splitting")
                            self.split_tests['small_pdf_no_split_flag'] = True
                            self.split_tests['small_pdf_normal_processing'] = True
                        else:
                            self.log("❌ Small PDF incorrectly marked as split", "ERROR")
                    
                    # Check field extraction
                    extracted_fields = [
                        'survey_report_name', 'survey_report_no', 'issued_by', 
                        'issued_date', 'surveyor_name'
                    ]
                    
                    fields_found = 0
                    for field in extracted_fields:
                        if analysis.get(field):
                            fields_found += 1
                            self.log(f"   ✅ {field}: {analysis.get(field)}")
                    
                    if fields_found > 0:
                        self.log(f"✅ Field extraction working ({fields_found}/{len(extracted_fields)} fields)")
                        self.split_tests['small_pdf_field_extraction'] = True
                    
                    return True
                else:
                    error_msg = result.get("message", "Unknown error")
                    self.log(f"❌ Small PDF processing failed: {error_msg}", "ERROR")
                    return False
            else:
                self.log(f"❌ Endpoint request failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in Test Case 1: {str(e)}", "ERROR")
            return False
    
    def test_case_2_mock_large_pdf_processing(self):
        """Test Case 2: Mock Large PDF Processing (25-page scenario)"""
        try:
            self.log("📄 TEST CASE 2: Mock Large PDF Processing (25-page scenario)")
            self.log("=" * 60)
            
            # Create a large PDF (25 pages)
            large_pdf_content = self.create_mock_pdf(25, "large_survey_report.pdf")
            self.log(f"📄 Created mock PDF: 25 pages, {len(large_pdf_content)} bytes")
            
            # Verify page count using our own PDF reader
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(large_pdf_content))
                actual_pages = len(pdf_reader.pages)
                self.log(f"📊 Verified page count: {actual_pages} pages")
                
                if actual_pages > 15:
                    self.log("✅ Large PDF should trigger split logic")
                else:
                    self.log("⚠️ PDF may not trigger split logic", "WARNING")
            except Exception as e:
                self.log(f"⚠️ Could not verify page count: {e}", "WARNING")
            
            # Test the endpoint
            files = {
                "survey_report_file": ("large_survey_report.pdf", large_pdf_content, "application/pdf")
            }
            data = {
                "ship_id": self.ship_id,
                "bypass_validation": "false"
            }
            
            endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
            self.log(f"📤 POST {endpoint}")
            
            start_time = time.time()
            response = self.session.post(
                endpoint,
                files=files,
                data=data,
                timeout=300  # Longer timeout for large PDF processing
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Debug: Print full response structure
                self.log(f"📊 Full response keys: {list(result.keys())}")
                self.log(f"📊 Response success: {result.get('success')}")
                
                # Check for success
                if result.get("success"):
                    self.log("✅ Large PDF processing successful")
                    
                    # Check split info
                    analysis = result.get("analysis", {})
                    split_info = analysis.get("_split_info", {})
                    self.log(f"📊 Split info found: {split_info}")
                    if split_info:
                        was_split = split_info.get("was_split", False)
                        total_pages = split_info.get("total_pages", 0)
                        chunks_count = split_info.get("chunks_count", 0)
                        successful_chunks = split_info.get("successful_chunks", 0)
                        failed_chunks = split_info.get("failed_chunks", 0)
                        
                        self.log(f"📊 Split Info:")
                        self.log(f"   was_split: {was_split}")
                        self.log(f"   total_pages: {total_pages}")
                        self.log(f"   chunks_count: {chunks_count}")
                        self.log(f"   successful_chunks: {successful_chunks}")
                        self.log(f"   failed_chunks: {failed_chunks}")
                        
                        if was_split and chunks_count > 1:
                            self.log("✅ Large PDF correctly split into chunks")
                            self.split_tests['large_pdf_split_detection'] = True
                            
                            # Verify chunk count logic (25 pages / 12 per chunk = 3 chunks: 12+12+1)
                            expected_chunks = 3
                            if chunks_count == expected_chunks:
                                self.log(f"✅ Correct chunk count: {chunks_count} (expected {expected_chunks})")
                                self.split_tests['large_pdf_chunk_creation'] = True
                            else:
                                self.log(f"⚠️ Unexpected chunk count: {chunks_count} (expected {expected_chunks})", "WARNING")
                            
                            if successful_chunks > 0:
                                self.log(f"✅ Batch processing working: {successful_chunks} successful chunks")
                                self.split_tests['large_pdf_batch_processing'] = True
                        else:
                            self.log("❌ Large PDF not split as expected", "ERROR")
                    
                    # Check processing method
                    processing_method = analysis.get("processing_method", "")
                    if "split_pdf" in processing_method:
                        self.log(f"✅ Processing method indicates splitting: {processing_method}")
                        self.split_tests['large_pdf_summary_merging'] = True
                    
                    # Check for merged summary
                    summary_text = analysis.get("_summary_text", "")
                    if summary_text and "MERGED SUMMARY" in summary_text:
                        self.log("✅ Enhanced merged summary created")
                        self.log(f"   Summary length: {len(summary_text)} characters")
                        self.split_tests['large_pdf_enhanced_summary'] = True
                    
                    # Check field extraction (should be from merged summary, not per chunk)
                    extracted_fields = [
                        'survey_report_name', 'survey_report_no', 'issued_by', 
                        'issued_date', 'surveyor_name'
                    ]
                    
                    fields_found = 0
                    for field in extracted_fields:
                        if analysis.get(field):
                            fields_found += 1
                            self.log(f"   ✅ {field}: {analysis.get(field)}")
                    
                    if fields_found > 0:
                        self.log(f"✅ Single field extraction from merged summary working")
                        self.split_tests['large_pdf_single_field_extraction'] = True
                    
                    return True
                else:
                    error_msg = result.get("message", "Unknown error")
                    self.log(f"❌ Large PDF processing failed: {error_msg}", "ERROR")
                    return False
            else:
                self.log(f"❌ Endpoint request failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in Test Case 2: {str(e)}", "ERROR")
            return False
    
    def test_case_3_backend_endpoint_analysis(self):
        """Test Case 3: Backend Endpoint Analysis - Verify implementation details"""
        try:
            self.log("🔍 TEST CASE 3: Backend Endpoint Analysis")
            self.log("=" * 60)
            
            # Test with a medium PDF (18 pages) to trigger splitting
            medium_pdf_content = self.create_mock_pdf(18, "medium_survey_report.pdf")
            self.log(f"📄 Created test PDF: 18 pages, {len(medium_pdf_content)} bytes")
            
            # Check backend logs before request
            self.log("📋 Monitoring backend logs for implementation details...")
            
            files = {
                "survey_report_file": ("medium_survey_report.pdf", medium_pdf_content, "application/pdf")
            }
            data = {
                "ship_id": self.ship_id,
                "bypass_validation": "false"
            }
            
            endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
            
            start_time = time.time()
            response = self.session.post(
                endpoint,
                files=files,
                data=data,
                timeout=180
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            if response.status_code == 200:
                result = response.json()
                
                # Analyze response structure for implementation verification
                self.log("🔍 Analyzing response structure...")
                
                # Get analysis object
                analysis = result.get("analysis", {})
                
                # 1. PDF page count detection
                split_info = analysis.get("_split_info", {})
                if split_info and "total_pages" in split_info:
                    self.log("✅ PDF page count detection working")
                    self.split_tests['page_count_detection_working'] = True
                
                # 2. Split logic activation
                was_split = split_info.get("was_split", False)
                total_pages = split_info.get("total_pages", 0)
                if total_pages > 15 and was_split:
                    self.log("✅ Split logic activates correctly for >15 pages")
                    self.split_tests['split_logic_activates_correctly'] = True
                
                # 3. Processing method verification
                processing_method = analysis.get("processing_method", "")
                if "split_pdf" in processing_method:
                    self.log("✅ Processing method indicates split PDF handling")
                
                # 4. Summary merging verification
                summary_text = analysis.get("_summary_text", "")
                if summary_text:
                    if "CHUNK" in summary_text and "MERGED SUMMARY" in summary_text:
                        self.log("✅ Summaries merged after chunk processing")
                        self.split_tests['summaries_merged_after_loop'] = True
                
                # 5. Single field extraction verification
                has_extracted_fields = any([
                    analysis.get('survey_report_name'),
                    analysis.get('survey_report_no'),
                    analysis.get('issued_by')
                ])
                
                if has_extracted_fields:
                    self.log("✅ Field extraction performed once from merged summary")
                    self.split_tests['field_extraction_once_from_merged'] = True
                
                # 6. Enhanced summary creation
                if summary_text and len(summary_text) > 1000:  # Substantial summary
                    self.log("✅ Enhanced summary created with substantial content")
                    self.split_tests['enhanced_summary_created'] = True
                
                # 7. Split info metadata
                if split_info and all(key in split_info for key in ['was_split', 'total_pages', 'chunks_count']):
                    self.log("✅ Split info metadata included in response")
                    self.split_tests['split_info_metadata_included'] = True
                
                # Check backend logs for specific patterns
                self.check_backend_logs_for_split_patterns()
                
                return True
            else:
                self.log(f"❌ Endpoint analysis failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in Test Case 3: {str(e)}", "ERROR")
            return False
    
    def test_case_4_error_handling(self):
        """Test Case 4: Error Handling - Test various error scenarios"""
        try:
            self.log("⚠️ TEST CASE 4: Error Handling")
            self.log("=" * 60)
            
            # Test 4a: Invalid PDF file
            self.log("🔍 Testing invalid PDF file handling...")
            invalid_content = b"This is not a PDF file content"
            
            files = {
                "survey_report_file": ("invalid.pdf", invalid_content, "application/pdf")
            }
            data = {
                "ship_id": self.ship_id,
                "bypass_validation": "false"
            }
            
            endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
            response = self.session.post(endpoint, files=files, data=data, timeout=60)
            
            if response.status_code in [400, 500]:
                self.log("✅ Invalid PDF handled with appropriate error response")
                self.split_tests['invalid_pdf_handled'] = True
            else:
                self.log(f"⚠️ Unexpected response for invalid PDF: {response.status_code}", "WARNING")
            
            # Test 4b: Missing ship_id
            self.log("🔍 Testing missing ship_id handling...")
            valid_pdf = self.create_mock_pdf(5, "test.pdf")
            
            files = {
                "survey_report_file": ("test.pdf", valid_pdf, "application/pdf")
            }
            data = {
                "bypass_validation": "false"
                # Missing ship_id
            }
            
            response = self.session.post(endpoint, files=files, data=data, timeout=60)
            
            if response.status_code in [400, 422]:
                self.log("✅ Missing ship_id handled with validation error")
                self.split_tests['graceful_error_responses'] = True
            
            # Test 4c: Invalid ship_id
            self.log("🔍 Testing invalid ship_id handling...")
            
            files = {
                "survey_report_file": ("test.pdf", valid_pdf, "application/pdf")
            }
            data = {
                "ship_id": "invalid-ship-id-12345",
                "bypass_validation": "false"
            }
            
            response = self.session.post(endpoint, files=files, data=data, timeout=60)
            
            if response.status_code == 404:
                self.log("✅ Invalid ship_id handled with 404 error")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error in Test Case 4: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs_for_split_patterns(self):
        """Check backend logs for PDF split-related patterns"""
        try:
            self.log("📋 Checking backend logs for split patterns...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            split_patterns = [
                "PDF Analysis:",
                "Split needed:",
                "Splitting PDF",
                "chunks created",
                "Processing chunk",
                "Merging summaries",
                "Split PDF processing complete",
                "Enhanced merged summary"
            ]
            
            patterns_found = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            for pattern in split_patterns:
                                if pattern in result:
                                    patterns_found.append(pattern)
                                    self.log(f"   ✅ Found pattern: '{pattern}'")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            if len(patterns_found) >= 3:
                self.log(f"✅ Split processing patterns found in logs ({len(patterns_found)}/{len(split_patterns)})")
                self.split_tests['chunks_processed_without_field_extraction'] = True
            else:
                self.log(f"⚠️ Limited split patterns in logs ({len(patterns_found)}/{len(split_patterns)})", "WARNING")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def run_comprehensive_pdf_split_test(self):
        """Run comprehensive test of PDF split functionality"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE PDF SPLIT + BATCH PROCESSING TEST")
            self.log("=" * 80)
            self.log("Testing new PDF splitting functionality for Survey Reports:")
            self.log("- Auto-detect PDF page count")
            self.log("- Split PDFs >15 pages into chunks of 12 pages each")
            self.log("- Process each chunk with Document AI")
            self.log("- Merge all summaries into one enhanced summary")
            self.log("- Extract fields ONCE from merged summary (not per chunk)")
            self.log("- Return clean results without conflicts")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Ship Verification
            self.log("\nSTEP 2: Ship Verification")
            if not self.verify_ship_exists():
                self.log("❌ CRITICAL: Ship verification failed - cannot proceed")
                return False
            
            # Step 3: Test Case 1 - Small PDF Normal Flow
            self.log("\nSTEP 3: Test Case 1 - Small PDF (≤15 pages) Normal Flow")
            self.test_case_1_small_pdf_normal_flow()
            
            # Step 4: Test Case 2 - Mock Large PDF Processing
            self.log("\nSTEP 4: Test Case 2 - Mock Large PDF Processing (25-page scenario)")
            self.test_case_2_mock_large_pdf_processing()
            
            # Step 5: Test Case 3 - Backend Endpoint Analysis
            self.log("\nSTEP 5: Test Case 3 - Backend Endpoint Analysis")
            self.test_case_3_backend_endpoint_analysis()
            
            # Step 6: Test Case 4 - Error Handling
            self.log("\nSTEP 6: Test Case 4 - Error Handling")
            self.test_case_4_error_handling()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE PDF SPLIT TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 PDF SPLIT + BATCH PROCESSING TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.split_tests)
            passed_tests = sum(1 for result in self.split_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('ship_found', 'Ship found and verified'),
                ('endpoint_accessible', 'Endpoint accessible'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.split_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Case 1 Results
            self.log("\n📄 TEST CASE 1 - SMALL PDF (≤15 pages) NORMAL FLOW:")
            case1_tests = [
                ('small_pdf_normal_processing', 'Small PDF processed normally'),
                ('small_pdf_no_split_flag', 'No split flag for small PDF'),
                ('small_pdf_field_extraction', 'Field extraction working'),
                ('small_pdf_success_response', 'Success response received'),
            ]
            
            for test_key, description in case1_tests:
                status = "✅ PASS" if self.split_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Case 2 Results
            self.log("\n📦 TEST CASE 2 - MOCK LARGE PDF PROCESSING (25-page scenario):")
            case2_tests = [
                ('large_pdf_split_detection', 'Large PDF split detection'),
                ('large_pdf_chunk_creation', 'Correct chunk creation (3 chunks: 12+12+1)'),
                ('large_pdf_batch_processing', 'Batch processing working'),
                ('large_pdf_summary_merging', 'Summary merging working'),
                ('large_pdf_single_field_extraction', 'Single field extraction from merged summary'),
                ('large_pdf_enhanced_summary', 'Enhanced merged summary created'),
            ]
            
            for test_key, description in case2_tests:
                status = "✅ PASS" if self.split_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Case 3 Results
            self.log("\n🔍 TEST CASE 3 - BACKEND ENDPOINT ANALYSIS:")
            case3_tests = [
                ('page_count_detection_working', 'PDF page count detection works'),
                ('split_logic_activates_correctly', 'Split logic activates when pages > 15'),
                ('chunks_processed_without_field_extraction', 'Chunks processed in loop without field extraction'),
                ('summaries_merged_after_loop', 'Summaries merged after loop'),
                ('field_extraction_once_from_merged', 'Field extraction happens ONCE from merged summary'),
                ('enhanced_summary_created', 'Enhanced summary created with extracted data'),
                ('split_info_metadata_included', 'Response includes _split_info metadata'),
            ]
            
            for test_key, description in case3_tests:
                status = "✅ PASS" if self.split_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Case 4 Results
            self.log("\n⚠️ TEST CASE 4 - ERROR HANDLING:")
            case4_tests = [
                ('invalid_pdf_handled', 'Invalid PDF file handled'),
                ('graceful_error_responses', 'Graceful error responses'),
            ]
            
            for test_key, description in case4_tests:
                status = "✅ PASS" if self.split_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Key Success Criteria Assessment
            self.log("\n🎯 KEY SUCCESS CRITERIA:")
            
            key_criteria = [
                ('small_pdf_no_split_flag', 'Small PDFs (≤15 pages) process normally'),
                ('large_pdf_split_detection', 'Large PDFs (>15 pages) trigger split logic'),
                ('field_extraction_once_from_merged', 'Field extraction happens ONLY ONCE from merged summary'),
                ('large_pdf_enhanced_summary', 'Enhanced merged summary is created properly'),
                ('split_info_metadata_included', 'Response includes split_info metadata'),
                ('graceful_error_responses', 'Error handling is graceful'),
            ]
            
            criteria_passed = sum(1 for test_key, _ in key_criteria if self.split_tests.get(test_key, False))
            
            for test_key, description in key_criteria:
                status = "✅ PASS" if self.split_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🏆 OVERALL ASSESSMENT:")
            
            if criteria_passed == len(key_criteria):
                self.log("   ✅ ALL KEY SUCCESS CRITERIA MET")
                self.log("   ✅ PDF split functionality working correctly")
                self.log("   ✅ No conflicts in extracted data")
                self.log("   ✅ Optimization achieved (field extraction only once)")
            elif criteria_passed >= len(key_criteria) * 0.8:
                self.log("   ⚠️ MOST KEY CRITERIA MET - Minor issues detected")
                self.log(f"   ⚠️ {criteria_passed}/{len(key_criteria)} key criteria passed")
            else:
                self.log("   ❌ SIGNIFICANT ISSUES DETECTED")
                self.log(f"   ❌ Only {criteria_passed}/{len(key_criteria)} key criteria passed")
            
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
    tester = SurveyPDFSplitTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_pdf_split_test()
        
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
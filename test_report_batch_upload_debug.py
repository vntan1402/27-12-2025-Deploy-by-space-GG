#!/usr/bin/env python3
"""
Test Report Batch Upload Debug - Chemical Suit.pdf and Co2.pdf Issue Investigation

REVIEW REQUEST REQUIREMENTS:
Test upload lại 2 files Test Report mà user báo lỗi để debug chi tiết.

**CONTEXT:**
User vẫn báo lỗi khi upload batch 2 files Chemical Suit.pdf và Co2.pdf. 
Tôi đã fix graceful degradation cho AI failure nhưng vẫn có vấn đề. 
Cần test thực tế và capture exact error.

**TEST FILES:**
1. Chemical Suit.pdf - https://customer-assets.emergentagent.com/job_test-survey-portal/artifacts/py2c7zgh_Chemical%20Suit.pdf
2. Co2.pdf - https://customer-assets.emergentagent.com/job_test-survey-portal/artifacts/hb2n81o5_Co2.pdf

**DETAILED TEST PLAN:**

**Phase 1: Download & Verify Files**
- Download both PDF files
- Verify file size and validity
- Check page count

**Phase 2: Test Individual Files (Baseline)**
Test mỗi file riêng lẻ:
1. Chemical Suit.pdf:
   - POST /api/test-reports/analyze-file (bypass_validation=false)
   - Log FULL response
   - Check có _file_content không?
   - Check có _summary_text không?
   - Status code?

2. Co2.pdf:
   - Same steps
   - Compare với Chemical Suit

**Phase 3: Simulate Exact Batch Flow**
Simulate chính xác flow của frontend batch processing:

1. Login admin1/123456
2. Get ship BROTHER 36
3. For Chemical Suit.pdf:
   ```
   Step 1: Analyze
   - POST /api/test-reports/analyze-file
   - bypass_validation=true
   - Capture response
   
   Step 2: Create Record
   - POST /api/test-reports?ship_id={ship_id}
   - Use extracted data
   - Capture response
   
   Step 3: Upload Files
   - POST /api/test-reports/{report_id}/upload-files
   - Pass: file_content, filename, content_type, summary_text
   - Capture response
   ```

4. Repeat for Co2.pdf

**Phase 4: Check Backend Logs**
- Tail backend logs during test
- Look for:
  - Rate limiting (429)
  - AI analysis errors
  - Missing field errors
  - Upload failures
  - ANY errors or warnings

**Phase 5: Detailed Error Analysis**
If errors occur:
- Capture exact error message
- Capture request payload
- Capture response body
- Check which step failed
- Check backend logs for root cause

**EXPECTED OUTPUTS:**
1. Exact error message user is seeing
2. Which step fails (analyze/create/upload)?
3. Backend logs showing root cause
4. Specific fix needed

**IMPORTANT:**
- Test WITH actual rate limiting (don't wait)
- Simulate exact frontend flow
- Capture EVERYTHING for debugging
- Don't skip any steps
- Check if _file_content is actually present in response
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
import base64
import subprocess

# Configuration - Use environment variable for backend URL
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://test-survey-portal.preview.emergentagent.com') + '/api'
print(f"Using backend URL: {BACKEND_URL}")

class TestReportBatchUploadDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.ship_name = "BROTHER 36"
        self.ship_id = None
        
        # Test tracking for batch upload debugging
        self.batch_tests = {
            # Phase 1: File verification
            'chemical_suit_file_downloaded': False,
            'co2_file_downloaded': False,
            'chemical_suit_file_valid': False,
            'co2_file_valid': False,
            'chemical_suit_page_count': 0,
            'co2_page_count': 0,
            
            # Phase 2: Individual file testing (baseline)
            'chemical_suit_individual_analyze_success': False,
            'chemical_suit_individual_file_content_present': False,
            'chemical_suit_individual_summary_text_present': False,
            'co2_individual_analyze_success': False,
            'co2_individual_file_content_present': False,
            'co2_individual_summary_text_present': False,
            
            # Phase 3: Batch flow simulation
            'authentication_successful': False,
            'ship_discovery_successful': False,
            'chemical_suit_batch_analyze_success': False,
            'chemical_suit_batch_create_success': False,
            'chemical_suit_batch_upload_success': False,
            'co2_batch_analyze_success': False,
            'co2_batch_create_success': False,
            'co2_batch_upload_success': False,
            
            # Phase 4: Backend logs analysis
            'backend_logs_captured': False,
            'rate_limiting_detected': False,
            'ai_analysis_errors_detected': False,
            'missing_field_errors_detected': False,
            'upload_failures_detected': False,
            
            # Phase 5: Error analysis
            'exact_error_message_captured': False,
            'failed_step_identified': False,
            'root_cause_identified': False,
        }
        
        # Store test data
        self.test_files = {
            'chemical_suit': {
                'filename': 'Chemical_Suit.pdf',
                'path': '/app/Chemical_Suit.pdf',
                'size': 0,
                'valid': False,
                'page_count': 0
            },
            'co2': {
                'filename': 'Co2.pdf', 
                'path': '/app/Co2.pdf',
                'size': 0,
                'valid': False,
                'page_count': 0
            }
        }
        
        # Store responses for analysis
        self.responses = {
            'chemical_suit_individual': None,
            'co2_individual': None,
            'chemical_suit_batch_analyze': None,
            'chemical_suit_batch_create': None,
            'chemical_suit_batch_upload': None,
            'co2_batch_analyze': None,
            'co2_batch_create': None,
            'co2_batch_upload': None,
        }
        
        # Store created test report IDs for cleanup
        self.created_report_ids = []
        
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
        
    def phase_1_verify_files(self):
        """Phase 1: Download & Verify Files"""
        try:
            self.log("🔍 PHASE 1: Download & Verify Files")
            self.log("=" * 60)
            
            # Check Chemical Suit.pdf
            chemical_suit_path = self.test_files['chemical_suit']['path']
            if os.path.exists(chemical_suit_path):
                file_size = os.path.getsize(chemical_suit_path)
                self.test_files['chemical_suit']['size'] = file_size
                self.log(f"✅ Chemical Suit.pdf found: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                self.batch_tests['chemical_suit_file_downloaded'] = True
                
                # Verify it's a valid PDF
                with open(chemical_suit_path, 'rb') as f:
                    header = f.read(8)
                    if header.startswith(b'%PDF'):
                        self.log("✅ Chemical Suit.pdf is a valid PDF")
                        self.test_files['chemical_suit']['valid'] = True
                        self.batch_tests['chemical_suit_file_valid'] = True
                        
                        # Get page count
                        try:
                            import PyPDF2
                            with open(chemical_suit_path, 'rb') as pdf_file:
                                pdf_reader = PyPDF2.PdfReader(pdf_file)
                                page_count = len(pdf_reader.pages)
                                self.test_files['chemical_suit']['page_count'] = page_count
                                self.batch_tests['chemical_suit_page_count'] = page_count
                                self.log(f"   Page count: {page_count}")
                        except Exception as e:
                            self.log(f"   Could not get page count: {e}")
                    else:
                        self.log("❌ Chemical Suit.pdf is not a valid PDF", "ERROR")
            else:
                self.log(f"❌ Chemical Suit.pdf not found at {chemical_suit_path}", "ERROR")
            
            # Check Co2.pdf
            co2_path = self.test_files['co2']['path']
            if os.path.exists(co2_path):
                file_size = os.path.getsize(co2_path)
                self.test_files['co2']['size'] = file_size
                self.log(f"✅ Co2.pdf found: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                self.batch_tests['co2_file_downloaded'] = True
                
                # Verify it's a valid PDF
                with open(co2_path, 'rb') as f:
                    header = f.read(8)
                    if header.startswith(b'%PDF'):
                        self.log("✅ Co2.pdf is a valid PDF")
                        self.test_files['co2']['valid'] = True
                        self.batch_tests['co2_file_valid'] = True
                        
                        # Get page count
                        try:
                            import PyPDF2
                            with open(co2_path, 'rb') as pdf_file:
                                pdf_reader = PyPDF2.PdfReader(pdf_file)
                                page_count = len(pdf_reader.pages)
                                self.test_files['co2']['page_count'] = page_count
                                self.batch_tests['co2_page_count'] = page_count
                                self.log(f"   Page count: {page_count}")
                        except Exception as e:
                            self.log(f"   Could not get page count: {e}")
                    else:
                        self.log("❌ Co2.pdf is not a valid PDF", "ERROR")
            else:
                self.log(f"❌ Co2.pdf not found at {co2_path}", "ERROR")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in Phase 1: {str(e)}", "ERROR")
            return False
    
    def phase_2_test_individual_files(self):
        """Phase 2: Test Individual Files (Baseline)"""
        try:
            self.log("\n🔍 PHASE 2: Test Individual Files (Baseline)")
            self.log("=" * 60)
            
            # Test Chemical Suit.pdf individually
            self.log("📄 Testing Chemical Suit.pdf individually...")
            chemical_result = self.test_individual_file_analysis(
                self.test_files['chemical_suit']['path'],
                self.test_files['chemical_suit']['filename'],
                bypass_validation=False
            )
            
            if chemical_result:
                self.responses['chemical_suit_individual'] = chemical_result
                self.batch_tests['chemical_suit_individual_analyze_success'] = True
                
                # Check for _file_content
                if chemical_result.get('_file_content'):
                    self.log("✅ Chemical Suit: _file_content present")
                    self.batch_tests['chemical_suit_individual_file_content_present'] = True
                else:
                    self.log("❌ Chemical Suit: _file_content MISSING", "ERROR")
                
                # Check for _summary_text
                if chemical_result.get('_summary_text'):
                    self.log("✅ Chemical Suit: _summary_text present")
                    self.batch_tests['chemical_suit_individual_summary_text_present'] = True
                else:
                    self.log("❌ Chemical Suit: _summary_text MISSING", "ERROR")
            
            # Test Co2.pdf individually
            self.log("\n📄 Testing Co2.pdf individually...")
            co2_result = self.test_individual_file_analysis(
                self.test_files['co2']['path'],
                self.test_files['co2']['filename'],
                bypass_validation=False
            )
            
            if co2_result:
                self.responses['co2_individual'] = co2_result
                self.batch_tests['co2_individual_analyze_success'] = True
                
                # Check for _file_content
                if co2_result.get('_file_content'):
                    self.log("✅ Co2: _file_content present")
                    self.batch_tests['co2_individual_file_content_present'] = True
                else:
                    self.log("❌ Co2: _file_content MISSING", "ERROR")
                
                # Check for _summary_text
                if co2_result.get('_summary_text'):
                    self.log("✅ Co2: _summary_text present")
                    self.batch_tests['co2_individual_summary_text_present'] = True
                else:
                    self.log("❌ Co2: _summary_text MISSING", "ERROR")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in Phase 2: {str(e)}", "ERROR")
            return False
    
    def test_individual_file_analysis(self, file_path, filename, bypass_validation=False):
        """Test individual file analysis"""
        try:
            if not os.path.exists(file_path):
                self.log(f"❌ File not found: {file_path}", "ERROR")
                return None
            
            # Prepare multipart form data
            with open(file_path, "rb") as f:
                files = {
                    "file": (filename, f, "application/pdf")
                }
                data = {
                    "ship_id": self.ship_id,
                    "bypass_validation": str(bypass_validation).lower()
                }
                
                self.log(f"📤 Uploading {filename} (bypass_validation={bypass_validation})")
                self.log(f"🚢 Ship ID: {self.ship_id}")
                
                endpoint = f"{BACKEND_URL}/test-reports/analyze-file"
                self.log(f"   POST {endpoint}")
                
                start_time = time.time()
                response = self.session.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=120  # Longer timeout for AI processing
                )
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ File analysis successful")
                
                # Log response structure
                self.log(f"📊 Response keys: {list(result.keys())}")
                
                # Check success field
                success = result.get("success", False)
                self.log(f"   Success: {success}")
                
                # Check extracted fields
                extracted_fields = [
                    'test_report_name', 'report_form', 'test_report_no', 
                    'issued_by', 'issued_date', 'valid_date', 'note'
                ]
                
                self.log("📋 Extracted fields:")
                for field in extracted_fields:
                    value = result.get(field, '')
                    if value:
                        self.log(f"   {field}: {value}")
                    else:
                        self.log(f"   {field}: (empty)")
                
                # Check metadata fields
                metadata_fields = ['_file_content', '_summary_text', '_filename', '_content_type']
                self.log("📋 Metadata fields:")
                for field in metadata_fields:
                    value = result.get(field)
                    if field == '_file_content' and value:
                        self.log(f"   {field}: Present ({len(value)} characters)")
                    elif field == '_summary_text' and value:
                        self.log(f"   {field}: Present ({len(value)} characters)")
                    elif value:
                        self.log(f"   {field}: {value}")
                    else:
                        self.log(f"   {field}: (missing)")
                
                return result
            else:
                self.log(f"❌ File analysis failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}", "ERROR")
                except:
                    self.log(f"   Error text: {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error in individual file analysis: {str(e)}", "ERROR")
            return None
    
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
                
                self.batch_tests['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_ship(self):
        """Find the test ship"""
        try:
            self.log(f"🚢 Finding ship: {self.ship_name}")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                for ship in ships:
                    if ship.get("name") == self.ship_name:
                        self.ship_id = ship.get("id")
                        imo = ship.get("imo", "N/A")
                        self.log(f"✅ Found ship: {self.ship_name} (ID: {self.ship_id}, IMO: {imo})")
                        self.batch_tests['ship_discovery_successful'] = True
                        return True
                
                self.log(f"❌ Ship '{self.ship_name}' not found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def phase_3_simulate_batch_flow(self):
        """Phase 3: Simulate Exact Batch Flow"""
        try:
            self.log("\n🔍 PHASE 3: Simulate Exact Batch Flow")
            self.log("=" * 60)
            
            # Step 1: Authentication
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed", "ERROR")
                return False
            
            # Step 2: Find ship
            if not self.find_ship():
                self.log("❌ Ship discovery failed - cannot proceed", "ERROR")
                return False
            
            # Step 3: Process Chemical Suit.pdf in batch mode
            self.log("\n📄 Processing Chemical Suit.pdf in batch mode...")
            chemical_success = self.simulate_batch_file_processing(
                self.test_files['chemical_suit']['path'],
                self.test_files['chemical_suit']['filename'],
                'chemical_suit'
            )
            
            # Step 4: Process Co2.pdf in batch mode
            self.log("\n📄 Processing Co2.pdf in batch mode...")
            co2_success = self.simulate_batch_file_processing(
                self.test_files['co2']['path'],
                self.test_files['co2']['filename'],
                'co2'
            )
            
            return chemical_success and co2_success
            
        except Exception as e:
            self.log(f"❌ Error in Phase 3: {str(e)}", "ERROR")
            return False
    
    def simulate_batch_file_processing(self, file_path, filename, file_key):
        """Simulate the exact batch processing flow for a single file"""
        try:
            self.log(f"🔄 Simulating batch processing for {filename}")
            
            # Step 1: Analyze file (bypass_validation=true for batch mode)
            self.log("   Step 1: Analyze file...")
            analyze_result = self.test_individual_file_analysis(
                file_path, filename, bypass_validation=True
            )
            
            if not analyze_result:
                self.log(f"❌ Step 1 failed for {filename}", "ERROR")
                return False
            
            self.responses[f'{file_key}_batch_analyze'] = analyze_result
            self.batch_tests[f'{file_key}_batch_analyze_success'] = True
            
            # Check if we have the required fields for next steps
            file_content = analyze_result.get('_file_content')
            summary_text = analyze_result.get('_summary_text', '')
            
            if not file_content:
                self.log(f"❌ Step 1: No _file_content for {filename} - cannot proceed to upload", "ERROR")
                return False
            
            # Step 2: Create test report record
            self.log("   Step 2: Create test report record...")
            create_result = self.create_test_report_record(analyze_result, filename, file_key)
            
            if not create_result:
                self.log(f"❌ Step 2 failed for {filename}", "ERROR")
                return False
            
            report_id = create_result.get('id')
            if not report_id:
                self.log(f"❌ Step 2: No report ID returned for {filename}", "ERROR")
                return False
            
            self.created_report_ids.append(report_id)
            self.batch_tests[f'{file_key}_batch_create_success'] = True
            
            # Step 3: Upload files
            self.log("   Step 3: Upload files...")
            upload_result = self.upload_test_report_files(
                report_id, file_content, filename, summary_text, file_key
            )
            
            if upload_result:
                self.batch_tests[f'{file_key}_batch_upload_success'] = True
                self.log(f"✅ Batch processing completed successfully for {filename}")
                return True
            else:
                self.log(f"❌ Step 3 failed for {filename}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in batch processing for {filename}: {str(e)}", "ERROR")
            return False
    
    def create_test_report_record(self, analyze_result, filename, file_key):
        """Create test report record using analyzed data"""
        try:
            # Extract data from analysis result
            test_report_data = {
                "ship_id": self.ship_id,
                "test_report_name": analyze_result.get('test_report_name', filename),
                "report_form": analyze_result.get('report_form', ''),
                "test_report_no": analyze_result.get('test_report_no', ''),
                "issued_by": analyze_result.get('issued_by', ''),
                "issued_date": analyze_result.get('issued_date'),
                "valid_date": analyze_result.get('valid_date'),
                "status": analyze_result.get('status', 'Valid'),
                "note": analyze_result.get('note', '')
            }
            
            # Remove None values
            test_report_data = {k: v for k, v in test_report_data.items() if v is not None}
            
            self.log(f"📤 Creating test report record for {filename}")
            self.log(f"   Data: {json.dumps(test_report_data, indent=2, default=str)}")
            
            endpoint = f"{BACKEND_URL}/test-reports"
            response = self.session.post(endpoint, json=test_report_data, timeout=60)
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.log(f"✅ Test report created: ID {result.get('id')}")
                self.responses[f'{file_key}_batch_create'] = result
                return result
            else:
                self.log(f"❌ Failed to create test report: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}", "ERROR")
                except:
                    self.log(f"   Error text: {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error creating test report record: {str(e)}", "ERROR")
            return None
    
    def upload_test_report_files(self, report_id, file_content, filename, summary_text, file_key):
        """Upload files to test report"""
        try:
            # Prepare upload data exactly as frontend does
            upload_data = {
                "file_content": file_content,
                "filename": filename,
                "content_type": "application/pdf",
                "summary_text": summary_text
            }
            
            self.log(f"📤 Uploading files for report {report_id}")
            self.log(f"   Filename: {filename}")
            self.log(f"   Content type: application/pdf")
            self.log(f"   File content length: {len(file_content) if file_content else 0}")
            self.log(f"   Summary text length: {len(summary_text) if summary_text else 0}")
            
            endpoint = f"{BACKEND_URL}/test-reports/{report_id}/upload-files"
            response = self.session.post(endpoint, json=upload_data, timeout=120)
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Files uploaded successfully")
                self.log(f"   Response: {json.dumps(result, indent=2)}")
                self.responses[f'{file_key}_batch_upload'] = result
                return result
            else:
                self.log(f"❌ File upload failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}", "ERROR")
                    
                    # Capture exact error message for analysis
                    error_detail = error_data.get('detail', str(error_data))
                    self.batch_tests['exact_error_message_captured'] = True
                    self.log(f"🔍 EXACT ERROR MESSAGE: {error_detail}", "ERROR")
                    
                except:
                    self.log(f"   Error text: {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error uploading files: {str(e)}", "ERROR")
            return None
    
    def phase_4_check_backend_logs(self):
        """Phase 4: Check Backend Logs"""
        try:
            self.log("\n🔍 PHASE 4: Check Backend Logs")
            self.log("=" * 60)
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            patterns_to_find = [
                "429",  # Rate limiting
                "Too Many Requests",
                "AI analysis",
                "Document AI",
                "System AI",
                "Apps Script",
                "upload",
                "ERROR",
                "WARN",
                "failed",
                "exception"
            ]
            
            self.batch_tests['backend_logs_captured'] = True
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture recent activity
                        result = subprocess.run(
                            ["tail", "-n", "200", log_file], 
                            capture_output=True, 
                            text=True, 
                            timeout=10
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            lines = result.stdout.strip().split('\n')
                            self.log(f"   Found {len(lines)} recent log lines")
                            
                            # Look for specific patterns
                            for pattern in patterns_to_find:
                                matching_lines = [line for line in lines if pattern.lower() in line.lower()]
                                if matching_lines:
                                    self.log(f"   🔍 Found {len(matching_lines)} lines with '{pattern}':")
                                    for line in matching_lines[-5:]:  # Show last 5 matches
                                        self.log(f"     {line}")
                                    
                                    # Set specific flags
                                    if pattern in ["429", "Too Many Requests"]:
                                        self.batch_tests['rate_limiting_detected'] = True
                                    elif pattern in ["AI analysis", "Document AI", "System AI"]:
                                        self.batch_tests['ai_analysis_errors_detected'] = True
                                    elif pattern in ["upload", "Apps Script"]:
                                        self.batch_tests['upload_failures_detected'] = True
                        else:
                            self.log(f"   {log_file} is empty or not accessible")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
                else:
                    self.log(f"   {log_file} not found")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in Phase 4: {str(e)}", "ERROR")
            return False
    
    def phase_5_detailed_error_analysis(self):
        """Phase 5: Detailed Error Analysis"""
        try:
            self.log("\n🔍 PHASE 5: Detailed Error Analysis")
            self.log("=" * 60)
            
            # Analyze which step failed for each file
            files_to_analyze = ['chemical_suit', 'co2']
            
            for file_key in files_to_analyze:
                self.log(f"\n📊 Analyzing {file_key.replace('_', ' ').title()} processing:")
                
                # Check individual vs batch results
                individual_success = self.batch_tests.get(f'{file_key}_individual_analyze_success', False)
                batch_analyze_success = self.batch_tests.get(f'{file_key}_batch_analyze_success', False)
                batch_create_success = self.batch_tests.get(f'{file_key}_batch_create_success', False)
                batch_upload_success = self.batch_tests.get(f'{file_key}_batch_upload_success', False)
                
                self.log(f"   Individual analysis: {'✅ SUCCESS' if individual_success else '❌ FAILED'}")
                self.log(f"   Batch analysis: {'✅ SUCCESS' if batch_analyze_success else '❌ FAILED'}")
                self.log(f"   Batch create: {'✅ SUCCESS' if batch_create_success else '❌ FAILED'}")
                self.log(f"   Batch upload: {'✅ SUCCESS' if batch_upload_success else '❌ FAILED'}")
                
                # Identify failed step
                if not batch_analyze_success:
                    self.log(f"   🎯 FAILED STEP: Analysis (Step 1)")
                    self.batch_tests['failed_step_identified'] = True
                elif not batch_create_success:
                    self.log(f"   🎯 FAILED STEP: Create Record (Step 2)")
                    self.batch_tests['failed_step_identified'] = True
                elif not batch_upload_success:
                    self.log(f"   🎯 FAILED STEP: Upload Files (Step 3)")
                    self.batch_tests['failed_step_identified'] = True
                else:
                    self.log(f"   ✅ All steps successful")
                
                # Compare individual vs batch responses
                individual_response = self.responses.get(f'{file_key}_individual')
                batch_response = self.responses.get(f'{file_key}_batch_analyze')
                
                if individual_response and batch_response:
                    self.log(f"   📊 Comparing individual vs batch responses:")
                    
                    # Check _file_content presence
                    individual_has_content = bool(individual_response.get('_file_content'))
                    batch_has_content = bool(batch_response.get('_file_content'))
                    
                    self.log(f"     Individual _file_content: {'✅ Present' if individual_has_content else '❌ Missing'}")
                    self.log(f"     Batch _file_content: {'✅ Present' if batch_has_content else '❌ Missing'}")
                    
                    if individual_has_content != batch_has_content:
                        self.log(f"     🚨 DIFFERENCE DETECTED: _file_content presence differs!", "ERROR")
                        self.batch_tests['root_cause_identified'] = True
                    
                    # Check _summary_text presence
                    individual_has_summary = bool(individual_response.get('_summary_text'))
                    batch_has_summary = bool(batch_response.get('_summary_text'))
                    
                    self.log(f"     Individual _summary_text: {'✅ Present' if individual_has_summary else '❌ Missing'}")
                    self.log(f"     Batch _summary_text: {'✅ Present' if batch_has_summary else '❌ Missing'}")
                    
                    if individual_has_summary != batch_has_summary:
                        self.log(f"     🚨 DIFFERENCE DETECTED: _summary_text presence differs!", "ERROR")
                        self.batch_tests['root_cause_identified'] = True
            
            # Overall analysis
            self.log(f"\n🎯 OVERALL ANALYSIS:")
            
            # Check if rate limiting is the issue
            if self.batch_tests.get('rate_limiting_detected'):
                self.log("   🚨 ROOT CAUSE: Rate limiting detected in backend logs")
                self.log("   💡 SOLUTION: Implement retry logic with exponential backoff")
                self.batch_tests['root_cause_identified'] = True
            
            # Check if AI processing is failing
            if (not self.batch_tests.get('chemical_suit_batch_analyze_success') or 
                not self.batch_tests.get('co2_batch_analyze_success')):
                self.log("   🚨 ROOT CAUSE: AI analysis failing in batch mode")
                self.log("   💡 SOLUTION: Check AI service configuration and error handling")
                self.batch_tests['root_cause_identified'] = True
            
            # Check if upload step is failing
            if (self.batch_tests.get('chemical_suit_batch_analyze_success') and 
                self.batch_tests.get('co2_batch_analyze_success') and
                (not self.batch_tests.get('chemical_suit_batch_upload_success') or 
                 not self.batch_tests.get('co2_batch_upload_success'))):
                self.log("   🚨 ROOT CAUSE: File upload step failing")
                self.log("   💡 SOLUTION: Check file upload endpoint and Google Drive integration")
                self.batch_tests['root_cause_identified'] = True
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in Phase 5: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        try:
            self.log("\n🧹 Cleaning up test data...")
            
            for report_id in self.created_report_ids[:]:
                try:
                    endpoint = f"{BACKEND_URL}/test-reports/{report_id}"
                    response = self.session.delete(endpoint, timeout=30)
                    if response.status_code in [200, 204]:
                        self.log(f"   ✅ Cleaned up test report ID: {report_id}")
                        self.created_report_ids.remove(report_id)
                    else:
                        self.log(f"   ⚠️ Failed to clean up test report ID: {report_id}")
                except Exception as e:
                    self.log(f"   ⚠️ Error cleaning up test report ID {report_id}: {str(e)}")
            
            self.log("✅ Cleanup completed")
            
        except Exception as e:
            self.log(f"❌ Error during cleanup: {str(e)}", "ERROR")
    
    def run_comprehensive_batch_upload_debug(self):
        """Run comprehensive batch upload debugging test"""
        try:
            self.log("🚀 STARTING TEST REPORT BATCH UPLOAD DEBUG")
            self.log("=" * 80)
            self.log("Testing user-reported issue with Chemical Suit.pdf and Co2.pdf batch upload")
            self.log("=" * 80)
            
            # Phase 1: Verify files
            if not self.phase_1_verify_files():
                self.log("❌ CRITICAL: File verification failed - cannot proceed")
                return False
            
            # Phase 2: Test individual files (baseline)
            if not self.phase_2_test_individual_files():
                self.log("❌ WARNING: Individual file testing had issues")
            
            # Phase 3: Simulate batch flow
            if not self.phase_3_simulate_batch_flow():
                self.log("❌ WARNING: Batch flow simulation had issues")
            
            # Phase 4: Check backend logs
            self.phase_4_check_backend_logs()
            
            # Phase 5: Detailed error analysis
            self.phase_5_detailed_error_analysis()
            
            # Cleanup
            self.cleanup_test_data()
            
            self.log("\n" + "=" * 80)
            self.log("✅ TEST REPORT BATCH UPLOAD DEBUG COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive debug: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 TEST REPORT BATCH UPLOAD DEBUG SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.batch_tests)
            passed_tests = sum(1 for result in self.batch_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Phase 1 Results
            self.log("📁 PHASE 1 - FILE VERIFICATION:")
            phase1_tests = [
                ('chemical_suit_file_downloaded', 'Chemical Suit.pdf downloaded'),
                ('chemical_suit_file_valid', 'Chemical Suit.pdf valid'),
                ('co2_file_downloaded', 'Co2.pdf downloaded'),
                ('co2_file_valid', 'Co2.pdf valid'),
            ]
            
            for test_key, description in phase1_tests:
                status = "✅ PASS" if self.batch_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Phase 2 Results
            self.log("\n📄 PHASE 2 - INDIVIDUAL FILE TESTING:")
            phase2_tests = [
                ('chemical_suit_individual_analyze_success', 'Chemical Suit individual analysis'),
                ('chemical_suit_individual_file_content_present', 'Chemical Suit _file_content present'),
                ('chemical_suit_individual_summary_text_present', 'Chemical Suit _summary_text present'),
                ('co2_individual_analyze_success', 'Co2 individual analysis'),
                ('co2_individual_file_content_present', 'Co2 _file_content present'),
                ('co2_individual_summary_text_present', 'Co2 _summary_text present'),
            ]
            
            for test_key, description in phase2_tests:
                status = "✅ PASS" if self.batch_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Phase 3 Results
            self.log("\n🔄 PHASE 3 - BATCH FLOW SIMULATION:")
            phase3_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('ship_discovery_successful', 'Ship discovery successful'),
                ('chemical_suit_batch_analyze_success', 'Chemical Suit batch analysis'),
                ('chemical_suit_batch_create_success', 'Chemical Suit batch create'),
                ('chemical_suit_batch_upload_success', 'Chemical Suit batch upload'),
                ('co2_batch_analyze_success', 'Co2 batch analysis'),
                ('co2_batch_create_success', 'Co2 batch create'),
                ('co2_batch_upload_success', 'Co2 batch upload'),
            ]
            
            for test_key, description in phase3_tests:
                status = "✅ PASS" if self.batch_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Phase 4 & 5 Results
            self.log("\n🔍 PHASE 4 & 5 - ERROR ANALYSIS:")
            analysis_tests = [
                ('backend_logs_captured', 'Backend logs captured'),
                ('rate_limiting_detected', 'Rate limiting detected'),
                ('ai_analysis_errors_detected', 'AI analysis errors detected'),
                ('upload_failures_detected', 'Upload failures detected'),
                ('exact_error_message_captured', 'Exact error message captured'),
                ('failed_step_identified', 'Failed step identified'),
                ('root_cause_identified', 'Root cause identified'),
            ]
            
            for test_key, description in analysis_tests:
                status = "✅ DETECTED" if self.batch_tests.get(test_key, False) else "❌ NOT FOUND"
                self.log(f"   {status} - {description}")
            
            # Critical Analysis
            self.log("\n🎯 CRITICAL ANALYSIS:")
            
            # Check if batch upload is working
            chemical_batch_working = (
                self.batch_tests.get('chemical_suit_batch_analyze_success', False) and
                self.batch_tests.get('chemical_suit_batch_create_success', False) and
                self.batch_tests.get('chemical_suit_batch_upload_success', False)
            )
            
            co2_batch_working = (
                self.batch_tests.get('co2_batch_analyze_success', False) and
                self.batch_tests.get('co2_batch_create_success', False) and
                self.batch_tests.get('co2_batch_upload_success', False)
            )
            
            if chemical_batch_working and co2_batch_working:
                self.log("   ✅ BATCH UPLOAD WORKING - No issues detected")
            elif not chemical_batch_working and not co2_batch_working:
                self.log("   ❌ BATCH UPLOAD COMPLETELY BROKEN - Both files failing")
            else:
                self.log("   ⚠️ PARTIAL BATCH UPLOAD ISSUES - One file working, one failing")
            
            # Root cause summary
            if self.batch_tests.get('root_cause_identified'):
                self.log("   ✅ ROOT CAUSE IDENTIFIED - Check detailed logs above")
            else:
                self.log("   ❌ ROOT CAUSE NOT IDENTIFIED - Further investigation needed")
            
            # File size information
            self.log(f"\n📊 FILE INFORMATION:")
            self.log(f"   Chemical Suit.pdf: {self.test_files['chemical_suit']['size']:,} bytes, {self.test_files['chemical_suit']['page_count']} pages")
            self.log(f"   Co2.pdf: {self.test_files['co2']['size']:,} bytes, {self.test_files['co2']['page_count']} pages")
            
            if success_rate >= 80:
                self.log(f"\n   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"\n   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"\n   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the test"""
    try:
        print("🚀 Starting Test Report Batch Upload Debug")
        print("Testing Chemical Suit.pdf and Co2.pdf batch upload issue")
        print("=" * 80)
        
        # Create tester instance
        tester = TestReportBatchUploadDebugger()
        
        # Run comprehensive test
        success = tester.run_comprehensive_batch_upload_debug()
        
        # Print summary
        tester.print_test_summary()
        
        if success:
            print("\n✅ Test completed successfully")
            return 0
        else:
            print("\n❌ Test completed with issues")
            return 1
            
    except Exception as e:
        print(f"❌ Critical error in main: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
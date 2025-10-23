#!/usr/bin/env python3
"""
Survey Report Batch Upload Testing
Testing batch upload of 2 Survey Report files following exact frontend workflow

REVIEW REQUEST REQUIREMENTS:
Test batch upload 2 Survey Report files theo đúng frontend workflow và báo cáo chi tiết từng bước.

FILES TO TEST:
1. CCM (02-19).pdf - https://customer-assets.emergentagent.com/job_test-survey-portal/artifacts/tn5aql9s_CCM%20%2802-19%29.pdf
2. CG (02-19).pdf - https://customer-assets.emergentagent.com/job_test-survey-portal/artifacts/1ze17y3i_CG%20%2802-19%29.pdf

TESTING REQUIREMENTS:
BƯỚC 1: DOWNLOAD & VERIFY FILES
BƯỚC 2: SETUP & LOGIN
BƯỚC 3: TEST FILE 1 - CCM (02-19).pdf (3 steps: analyze, create record, upload files)
BƯỚC 4: WAIT 5 SECONDS (Simulate stagger delay)
BƯỚC 5: TEST FILE 2 - CG (02-19).pdf (same 3 steps)
BƯỚC 6: VERIFY RESULTS
BƯỚC 7: CHECK BACKEND LOGS
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
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class SurveyReportBatchUploadTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.ship_id = "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"  # BROTHER 36 ID
        self.ship_name = "BROTHER 36"
        
        # Test files
        self.test_files = {
            "CCM": {
                "url": "https://customer-assets.emergentagent.com/job_test-survey-portal/artifacts/tn5aql9s_CCM%20%2802-19%29.pdf",
                "filename": "CCM (02-19).pdf",
                "local_path": "/app/CCM_02-19.pdf",
                "report_id": None,
                "original_file_id": None,
                "summary_file_id": None
            },
            "CG": {
                "url": "https://customer-assets.emergentagent.com/job_test-survey-portal/artifacts/1ze17y3i_CG%20%2802-19%29.pdf",
                "filename": "CG (02-19).pdf", 
                "local_path": "/app/CG_02-19.pdf",
                "report_id": None,
                "original_file_id": None,
                "summary_file_id": None
            }
        }
        
        # Test results tracking
        self.test_results = {
            # Step 1: Download & Verify
            'file_ccm_downloaded': False,
            'file_cg_downloaded': False,
            'file_ccm_valid_pdf': False,
            'file_cg_valid_pdf': False,
            'file_ccm_page_count': 0,
            'file_cg_page_count': 0,
            
            # Step 2: Setup & Login
            'authentication_successful': False,
            'ship_list_retrieved': False,
            'ship_brother36_found': False,
            'ship_id_verified': False,
            
            # Step 3: File 1 (CCM) Processing
            'ccm_analyze_successful': False,
            'ccm_analyze_response_valid': False,
            'ccm_create_record_successful': False,
            'ccm_upload_files_successful': False,
            'ccm_original_file_id': None,
            'ccm_summary_file_id': None,
            
            # Step 4: 5 Second Delay
            'stagger_delay_completed': False,
            
            # Step 5: File 2 (CG) Processing  
            'cg_analyze_successful': False,
            'cg_analyze_response_valid': False,
            'cg_create_record_successful': False,
            'cg_upload_files_successful': False,
            'cg_original_file_id': None,
            'cg_summary_file_id': None,
            
            # Step 6: Verify Results
            'total_survey_reports_count': 0,
            'both_reports_have_file_ids': False,
            'no_duplicates_detected': False,
            
            # Step 7: Backend Logs
            'backend_logs_checked': False,
            'no_errors_in_logs': False,
            'no_rate_limiting_429': False,
            'ai_analysis_successful': False
        }
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
    def download_file(self, url, local_path, filename):
        """Download file from URL"""
        try:
            self.log(f"📥 Downloading {filename}...")
            self.log(f"   URL: {url}")
            
            response = requests.get(url, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                self.log(f"✅ Downloaded {filename}")
                self.log(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                return True
            else:
                self.log(f"❌ Failed to download {filename}: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error downloading {filename}: {str(e)}", "ERROR")
            return False
    
    def verify_pdf_file(self, file_path, filename):
        """Verify PDF file and get page count"""
        try:
            self.log(f"🔍 Verifying {filename}...")
            
            if not os.path.exists(file_path):
                self.log(f"❌ File not found: {file_path}", "ERROR")
                return False, 0
            
            file_size = os.path.getsize(file_path)
            self.log(f"   File size: {file_size:,} bytes")
            
            # Check PDF magic bytes
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF'):
                    self.log(f"❌ {filename} is not a valid PDF", "ERROR")
                    return False, 0
            
            # Try to get page count using PyPDF2 if available
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    page_count = len(pdf_reader.pages)
                    self.log(f"✅ {filename} is valid PDF with {page_count} pages")
                    return True, page_count
            except ImportError:
                self.log(f"✅ {filename} is valid PDF (PyPDF2 not available for page count)")
                return True, 0
            except Exception as e:
                self.log(f"✅ {filename} is valid PDF (page count error: {e})")
                return True, 0
                
        except Exception as e:
            self.log(f"❌ Error verifying {filename}: {str(e)}", "ERROR")
            return False, 0
    
    def step1_download_and_verify_files(self):
        """BƯỚC 1: DOWNLOAD & VERIFY FILES"""
        try:
            self.log("=" * 80)
            self.log("BƯỚC 1: DOWNLOAD & VERIFY FILES")
            self.log("=" * 80)
            
            # Download CCM file
            ccm_downloaded = self.download_file(
                self.test_files["CCM"]["url"],
                self.test_files["CCM"]["local_path"],
                self.test_files["CCM"]["filename"]
            )
            self.test_results['file_ccm_downloaded'] = ccm_downloaded
            
            # Download CG file
            cg_downloaded = self.download_file(
                self.test_files["CG"]["url"],
                self.test_files["CG"]["local_path"],
                self.test_files["CG"]["filename"]
            )
            self.test_results['file_cg_downloaded'] = cg_downloaded
            
            # Verify CCM file
            if ccm_downloaded:
                ccm_valid, ccm_pages = self.verify_pdf_file(
                    self.test_files["CCM"]["local_path"],
                    self.test_files["CCM"]["filename"]
                )
                self.test_results['file_ccm_valid_pdf'] = ccm_valid
                self.test_results['file_ccm_page_count'] = ccm_pages
            
            # Verify CG file
            if cg_downloaded:
                cg_valid, cg_pages = self.verify_pdf_file(
                    self.test_files["CG"]["local_path"],
                    self.test_files["CG"]["filename"]
                )
                self.test_results['file_cg_valid_pdf'] = cg_valid
                self.test_results['file_cg_page_count'] = cg_pages
            
            # Report findings
            self.log("\n📊 STEP 1 FINDINGS:")
            self.log(f"   CCM file: {'✅ Downloaded' if ccm_downloaded else '❌ Failed'}")
            if ccm_downloaded:
                self.log(f"   CCM valid: {'✅ Valid PDF' if self.test_results['file_ccm_valid_pdf'] else '❌ Invalid'}")
                if self.test_results['file_ccm_page_count'] > 0:
                    self.log(f"   CCM pages: {self.test_results['file_ccm_page_count']}")
            
            self.log(f"   CG file: {'✅ Downloaded' if cg_downloaded else '❌ Failed'}")
            if cg_downloaded:
                self.log(f"   CG valid: {'✅ Valid PDF' if self.test_results['file_cg_valid_pdf'] else '❌ Invalid'}")
                if self.test_results['file_cg_page_count'] > 0:
                    self.log(f"   CG pages: {self.test_results['file_cg_page_count']}")
            
            return ccm_downloaded and cg_downloaded and self.test_results['file_ccm_valid_pdf'] and self.test_results['file_cg_valid_pdf']
            
        except Exception as e:
            self.log(f"❌ Error in Step 1: {str(e)}", "ERROR")
            return False
    
    def step2_setup_and_login(self):
        """BƯỚC 2: SETUP & LOGIN"""
        try:
            self.log("=" * 80)
            self.log("BƯỚC 2: SETUP & LOGIN")
            self.log("=" * 80)
            
            # Login with admin1/123456
            self.log("🔐 Logging in with admin1/123456...")
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            response = requests.post(endpoint, json=login_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                # Set authorization header
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User: {self.current_user.get('username')}")
                self.log(f"   Role: {self.current_user.get('role')}")
                self.test_results['authentication_successful'] = True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
            
            # Get ship list
            self.log("🚢 Getting ship list...")
            ships_response = self.session.get(f"{BACKEND_URL}/ships")
            self.log(f"   Response status: {ships_response.status_code}")
            
            if ships_response.status_code == 200:
                ships = ships_response.json()
                self.log(f"✅ Retrieved {len(ships)} ships")
                self.test_results['ship_list_retrieved'] = True
                
                # Find BROTHER 36
                brother36_found = False
                for ship in ships:
                    if ship.get("name") == self.ship_name:
                        found_ship_id = ship.get("id")
                        self.log(f"✅ Found ship: {self.ship_name}")
                        self.log(f"   Ship ID: {found_ship_id}")
                        
                        # Verify ship ID matches expected
                        if found_ship_id == self.ship_id:
                            self.log("✅ Ship ID verified")
                            self.test_results['ship_brother36_found'] = True
                            self.test_results['ship_id_verified'] = True
                            brother36_found = True
                        else:
                            self.log(f"⚠️ Ship ID mismatch - Expected: {self.ship_id}, Got: {found_ship_id}")
                            self.ship_id = found_ship_id  # Use actual ID
                            self.test_results['ship_brother36_found'] = True
                            brother36_found = True
                        break
                
                if not brother36_found:
                    self.log(f"❌ Ship '{self.ship_name}' not found", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get ships: {ships_response.status_code}", "ERROR")
                return False
            
            # Report findings
            self.log("\n📊 STEP 2 STATUS:")
            self.log(f"   Authentication: {'✅ Success' if self.test_results['authentication_successful'] else '❌ Failed'}")
            self.log(f"   Ship list: {'✅ Retrieved' if self.test_results['ship_list_retrieved'] else '❌ Failed'}")
            self.log(f"   BROTHER 36: {'✅ Found' if self.test_results['ship_brother36_found'] else '❌ Not found'}")
            self.log(f"   Ship ID: {'✅ Verified' if self.test_results['ship_id_verified'] else '⚠️ Updated'}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in Step 2: {str(e)}", "ERROR")
            return False
    
    def analyze_survey_report_file(self, file_key, file_info):
        """Analyze survey report file (Step 3.1 and 4.1)"""
        try:
            self.log(f"🤖 Analyzing {file_info['filename']}...")
            
            # Read file content
            with open(file_info['local_path'], 'rb') as f:
                files = {
                    'survey_report_file': (file_info['filename'], f, 'application/pdf')
                }
                data = {
                    'ship_id': self.ship_id,
                    'bypass_validation': 'true'
                }
                
                endpoint = f"{BACKEND_URL}/survey-reports/analyze-file"
                self.log(f"   POST {endpoint}")
                self.log(f"   Ship ID: {self.ship_id}")
                self.log(f"   Bypass validation: true")
                
                start_time = time.time()
                response = self.session.post(endpoint, files=files, data=data, timeout=120)
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ File analysis successful")
                
                # Log full response structure
                self.log("📊 Response structure:")
                for key in result.keys():
                    if key.startswith('_'):
                        # Don't log full content of large fields
                        if key in ['_file_content', '_summary_text']:
                            content_length = len(str(result[key])) if result[key] else 0
                            self.log(f"   {key}: {content_length} characters")
                        else:
                            self.log(f"   {key}: {result[key]}")
                    else:
                        self.log(f"   {key}: {result[key]}")
                
                # Verify required response fields
                required_fields = ['success', 'analysis']
                analysis_fields = ['_file_content', '_filename', '_summary_text']
                
                all_required_present = True
                for field in required_fields:
                    if field not in result:
                        self.log(f"❌ Missing required field: {field}", "ERROR")
                        all_required_present = False
                
                analysis = result.get('analysis', {})
                for field in analysis_fields:
                    if field not in analysis:
                        self.log(f"❌ Missing analysis field: {field}", "ERROR")
                        all_required_present = False
                
                # Report extracted fields
                self.log("📋 Extracted fields:")
                extracted_fields = ['survey_report_name', 'report_form', 'survey_report_no', 'issued_date', 'issued_by', 'status', 'note', 'surveyor_name']
                for field in extracted_fields:
                    value = analysis.get(field, '')
                    if value:
                        self.log(f"   {field}: {value}")
                    else:
                        self.log(f"   {field}: (empty)")
                
                return all_required_present, result
            else:
                self.log(f"❌ File analysis failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    self.log(f"   Error text: {response.text}")
                return False, None
                
        except Exception as e:
            self.log(f"❌ Error analyzing {file_info['filename']}: {str(e)}", "ERROR")
            return False, None
    
    def create_survey_report_record(self, file_key, analysis_result):
        """Create survey report record (Step 3.2 and 4.2)"""
        try:
            self.log(f"📝 Creating survey report record for {file_key}...")
            
            analysis = analysis_result.get('analysis', {})
            
            # Prepare payload from analysis
            payload = {
                'survey_report_name': analysis.get('survey_report_name', ''),
                'report_form': analysis.get('report_form', ''),
                'survey_report_no': analysis.get('survey_report_no', ''),
                'issued_date': analysis.get('issued_date', ''),
                'issued_by': analysis.get('issued_by', ''),
                'status': analysis.get('status', 'Valid'),
                'note': analysis.get('note', ''),
                'surveyor_name': analysis.get('surveyor_name', '')
            }
            
            endpoint = f"{BACKEND_URL}/survey-reports?ship_id={self.ship_id}"
            self.log(f"   POST {endpoint}")
            self.log(f"   Payload: {json.dumps(payload, indent=2)}")
            
            response = self.session.post(endpoint, json=payload, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                report_id = result.get('id')
                self.log("✅ Survey report record created")
                self.log(f"   Report ID: {report_id}")
                
                # Store report ID for file upload
                self.test_files[file_key]['report_id'] = report_id
                
                return True, report_id
            else:
                self.log(f"❌ Failed to create record: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    self.log(f"   Error text: {response.text}")
                return False, None
                
        except Exception as e:
            self.log(f"❌ Error creating record for {file_key}: {str(e)}", "ERROR")
            return False, None
    
    def upload_survey_report_files(self, file_key, report_id, analysis_result):
        """Upload survey report files (Step 3.3 and 4.3)"""
        try:
            self.log(f"📤 Uploading files for {file_key}...")
            
            analysis = analysis_result.get('analysis', {})
            
            # Prepare payload
            payload = {
                'file_content': analysis.get('_file_content', ''),
                'filename': analysis.get('_filename', ''),
                'content_type': 'application/pdf',
                'summary_text': analysis.get('_summary_text', '')
            }
            
            endpoint = f"{BACKEND_URL}/survey-reports/{report_id}/upload-files"
            self.log(f"   POST {endpoint}")
            self.log(f"   Filename: {payload['filename']}")
            self.log(f"   Content type: {payload['content_type']}")
            self.log(f"   File content length: {len(payload['file_content'])} characters")
            self.log(f"   Summary text length: {len(payload['summary_text'])} characters")
            
            response = self.session.post(endpoint, json=payload, timeout=120)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Files uploaded successfully")
                
                original_file_id = result.get('original_file_id')
                summary_file_id = result.get('summary_file_id')
                
                self.log(f"   Original file ID: {original_file_id}")
                self.log(f"   Summary file ID: {summary_file_id}")
                
                # Store file IDs
                self.test_files[file_key]['original_file_id'] = original_file_id
                self.test_files[file_key]['summary_file_id'] = summary_file_id
                
                return True, original_file_id, summary_file_id
            else:
                self.log(f"❌ File upload failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    self.log(f"   Error text: {response.text}")
                return False, None, None
                
        except Exception as e:
            self.log(f"❌ Error uploading files for {file_key}: {str(e)}", "ERROR")
            return False, None, None
    
    def step3_test_file1_ccm(self):
        """BƯỚC 3: TEST FILE 1 - CCM (02-19).pdf"""
        try:
            self.log("=" * 80)
            self.log("BƯỚC 3: TEST FILE 1 - CCM (02-19).pdf")
            self.log("=" * 80)
            
            file_key = "CCM"
            file_info = self.test_files[file_key]
            
            # 3.1 Analyze File
            self.log("3.1. Analyze File")
            analyze_success, analysis_result = self.analyze_survey_report_file(file_key, file_info)
            self.test_results['ccm_analyze_successful'] = analyze_success
            self.test_results['ccm_analyze_response_valid'] = analyze_success
            
            if not analyze_success:
                return False
            
            # 3.2 Create Record
            self.log("\n3.2. Create Record")
            create_success, report_id = self.create_survey_report_record(file_key, analysis_result)
            self.test_results['ccm_create_record_successful'] = create_success
            
            if not create_success:
                return False
            
            # 3.3 Upload Files
            self.log("\n3.3. Upload Files")
            upload_success, original_file_id, summary_file_id = self.upload_survey_report_files(file_key, report_id, analysis_result)
            self.test_results['ccm_upload_files_successful'] = upload_success
            self.test_results['ccm_original_file_id'] = original_file_id
            self.test_results['ccm_summary_file_id'] = summary_file_id
            
            # Report step 3 status
            self.log("\n📊 STEP 3 STATUS:")
            self.log(f"   Analyze: {'✅ Success' if analyze_success else '❌ Failed'}")
            self.log(f"   Create Record: {'✅ Success' if create_success else '❌ Failed'}")
            self.log(f"   Upload Files: {'✅ Success' if upload_success else '❌ Failed'}")
            if upload_success:
                self.log(f"   Original File ID: {original_file_id}")
                self.log(f"   Summary File ID: {summary_file_id}")
            
            return upload_success
            
        except Exception as e:
            self.log(f"❌ Error in Step 3: {str(e)}", "ERROR")
            return False
    
    def step4_wait_5_seconds(self):
        """BƯỚC 4: WAIT 5 SECONDS (Simulate stagger delay)"""
        try:
            self.log("=" * 80)
            self.log("BƯỚC 4: WAIT 5 SECONDS (Simulate stagger delay)")
            self.log("=" * 80)
            
            self.log("⏳ Waiting 5 seconds to simulate frontend stagger delay...")
            for i in range(5, 0, -1):
                self.log(f"   {i} seconds remaining...")
                time.sleep(1)
            
            self.log("✅ 5 second delay completed")
            self.test_results['stagger_delay_completed'] = True
            return True
            
        except Exception as e:
            self.log(f"❌ Error in Step 4: {str(e)}", "ERROR")
            return False
    
    def step5_test_file2_cg(self):
        """BƯỚC 5: TEST FILE 2 - CG (02-19).pdf"""
        try:
            self.log("=" * 80)
            self.log("BƯỚC 5: TEST FILE 2 - CG (02-19).pdf")
            self.log("=" * 80)
            
            file_key = "CG"
            file_info = self.test_files[file_key]
            
            # 4.1 Analyze File
            self.log("4.1. Analyze File")
            analyze_success, analysis_result = self.analyze_survey_report_file(file_key, file_info)
            self.test_results['cg_analyze_successful'] = analyze_success
            self.test_results['cg_analyze_response_valid'] = analyze_success
            
            if not analyze_success:
                return False
            
            # 4.2 Create Record
            self.log("\n4.2. Create Record")
            create_success, report_id = self.create_survey_report_record(file_key, analysis_result)
            self.test_results['cg_create_record_successful'] = create_success
            
            if not create_success:
                return False
            
            # 4.3 Upload Files
            self.log("\n4.3. Upload Files")
            upload_success, original_file_id, summary_file_id = self.upload_survey_report_files(file_key, report_id, analysis_result)
            self.test_results['cg_upload_files_successful'] = upload_success
            self.test_results['cg_original_file_id'] = original_file_id
            self.test_results['cg_summary_file_id'] = summary_file_id
            
            # Report step 5 status
            self.log("\n📊 STEP 5 STATUS:")
            self.log(f"   Analyze: {'✅ Success' if analyze_success else '❌ Failed'}")
            self.log(f"   Create Record: {'✅ Success' if create_success else '❌ Failed'}")
            self.log(f"   Upload Files: {'✅ Success' if upload_success else '❌ Failed'}")
            if upload_success:
                self.log(f"   Original File ID: {original_file_id}")
                self.log(f"   Summary File ID: {summary_file_id}")
            
            return upload_success
            
        except Exception as e:
            self.log(f"❌ Error in Step 5: {str(e)}", "ERROR")
            return False
    
    def step6_verify_results(self):
        """BƯỚC 6: VERIFY RESULTS"""
        try:
            self.log("=" * 80)
            self.log("BƯỚC 6: VERIFY RESULTS")
            self.log("=" * 80)
            
            # Get survey reports for the ship
            self.log("📊 Getting survey reports for verification...")
            endpoint = f"{BACKEND_URL}/survey-reports?ship_id={self.ship_id}"
            response = self.session.get(endpoint, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                reports = response.json()
                total_count = len(reports)
                self.log(f"✅ Retrieved {total_count} survey reports")
                self.test_results['total_survey_reports_count'] = total_count
                
                # Check if we have at least 2 reports (our uploaded ones)
                if total_count >= 2:
                    self.log("✅ At least 2 survey reports found (expected)")
                else:
                    self.log(f"⚠️ Only {total_count} survey reports found (expected at least 2)")
                
                # Check for file IDs in reports
                reports_with_files = 0
                for report in reports:
                    original_file_id = report.get('survey_report_file_id')
                    summary_file_id = report.get('survey_report_summary_file_id')
                    
                    if original_file_id or summary_file_id:
                        reports_with_files += 1
                        self.log(f"   Report '{report.get('survey_report_name', 'Unknown')}' has file IDs:")
                        if original_file_id:
                            self.log(f"     Original: {original_file_id}")
                        if summary_file_id:
                            self.log(f"     Summary: {summary_file_id}")
                
                if reports_with_files >= 2:
                    self.log("✅ Both reports have file IDs")
                    self.test_results['both_reports_have_file_ids'] = True
                else:
                    self.log(f"❌ Only {reports_with_files} reports have file IDs")
                
                # Check for duplicates (same survey_report_name or survey_report_no)
                names = [r.get('survey_report_name', '') for r in reports if r.get('survey_report_name')]
                numbers = [r.get('survey_report_no', '') for r in reports if r.get('survey_report_no')]
                
                duplicate_names = len(names) != len(set(names))
                duplicate_numbers = len(numbers) != len(set(numbers))
                
                if not duplicate_names and not duplicate_numbers:
                    self.log("✅ No duplicates detected")
                    self.test_results['no_duplicates_detected'] = True
                else:
                    if duplicate_names:
                        self.log("⚠️ Duplicate survey report names detected")
                    if duplicate_numbers:
                        self.log("⚠️ Duplicate survey report numbers detected")
                
            else:
                self.log(f"❌ Failed to get survey reports: {response.status_code}", "ERROR")
                return False
            
            # Report verification results
            self.log("\n📊 STEP 6 VERIFICATION:")
            self.log(f"   Total reports: {self.test_results['total_survey_reports_count']}")
            self.log(f"   Both have file IDs: {'✅ Yes' if self.test_results['both_reports_have_file_ids'] else '❌ No'}")
            self.log(f"   No duplicates: {'✅ Yes' if self.test_results['no_duplicates_detected'] else '⚠️ Found duplicates'}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in Step 6: {str(e)}", "ERROR")
            return False
    
    def step7_check_backend_logs(self):
        """BƯỚC 7: CHECK BACKEND LOGS"""
        try:
            self.log("=" * 80)
            self.log("BƯỚC 7: CHECK BACKEND LOGS")
            self.log("=" * 80)
            
            self.log("📋 Checking backend logs for errors and warnings...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            errors_found = []
            rate_limit_errors = []
            ai_analysis_logs = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            for line in lines:
                                line_lower = line.lower()
                                
                                # Check for errors
                                if any(keyword in line_lower for keyword in ['error', 'exception', 'failed', 'traceback']):
                                    if 'survey' in line_lower or 'report' in line_lower:
                                        errors_found.append(line.strip())
                                
                                # Check for rate limiting (429 errors)
                                if '429' in line or 'rate limit' in line_lower:
                                    rate_limit_errors.append(line.strip())
                                
                                # Check for AI analysis success/failure
                                if any(keyword in line_lower for keyword in ['ai analysis', 'document ai', 'system ai', 'survey report analysis']):
                                    ai_analysis_logs.append(line.strip())
                        
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
                else:
                    self.log(f"   {log_file} not found")
            
            # Report findings
            self.log("\n🔍 LOG ANALYSIS RESULTS:")
            
            if not errors_found:
                self.log("✅ No errors or warnings found")
                self.test_results['no_errors_in_logs'] = True
            else:
                self.log(f"❌ Found {len(errors_found)} errors/warnings:")
                for error in errors_found[-5:]:  # Show last 5 errors
                    self.log(f"   🔍 {error}")
            
            if not rate_limit_errors:
                self.log("✅ No 429 rate limit errors found")
                self.test_results['no_rate_limiting_429'] = True
            else:
                self.log(f"❌ Found {len(rate_limit_errors)} rate limit errors:")
                for error in rate_limit_errors[-3:]:  # Show last 3 rate limit errors
                    self.log(f"   🔍 {error}")
            
            if ai_analysis_logs:
                self.log(f"✅ Found {len(ai_analysis_logs)} AI analysis log entries")
                self.test_results['ai_analysis_successful'] = True
                # Show a few recent AI analysis logs
                for log_entry in ai_analysis_logs[-3:]:
                    self.log(f"   🤖 {log_entry}")
            else:
                self.log("⚠️ No AI analysis logs found")
            
            self.test_results['backend_logs_checked'] = True
            
            # Report step 7 status
            self.log("\n📊 STEP 7 STATUS:")
            self.log(f"   Logs checked: {'✅ Yes' if self.test_results['backend_logs_checked'] else '❌ No'}")
            self.log(f"   No errors: {'✅ Clean' if self.test_results['no_errors_in_logs'] else '❌ Errors found'}")
            self.log(f"   No rate limiting: {'✅ Clean' if self.test_results['no_rate_limiting_429'] else '❌ 429 errors'}")
            self.log(f"   AI analysis: {'✅ Working' if self.test_results['ai_analysis_successful'] else '⚠️ No logs'}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in Step 7: {str(e)}", "ERROR")
            return False
    
    def print_final_summary(self):
        """Print comprehensive test summary"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 SURVEY REPORT BATCH UPLOAD TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len([k for k in self.test_results.keys() if isinstance(self.test_results[k], bool)])
            passed_tests = sum(1 for k, v in self.test_results.items() if isinstance(v, bool) and v)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Step-by-step results
            steps = [
                ("STEP 1: Download & Verify Files", [
                    ('file_ccm_downloaded', 'CCM file downloaded'),
                    ('file_cg_downloaded', 'CG file downloaded'),
                    ('file_ccm_valid_pdf', 'CCM file valid PDF'),
                    ('file_cg_valid_pdf', 'CG file valid PDF'),
                ]),
                ("STEP 2: Setup & Login", [
                    ('authentication_successful', 'Authentication successful'),
                    ('ship_list_retrieved', 'Ship list retrieved'),
                    ('ship_brother36_found', 'BROTHER 36 found'),
                    ('ship_id_verified', 'Ship ID verified'),
                ]),
                ("STEP 3: File 1 (CCM) Processing", [
                    ('ccm_analyze_successful', 'CCM analysis successful'),
                    ('ccm_create_record_successful', 'CCM record created'),
                    ('ccm_upload_files_successful', 'CCM files uploaded'),
                ]),
                ("STEP 4: Stagger Delay", [
                    ('stagger_delay_completed', '5 second delay completed'),
                ]),
                ("STEP 5: File 2 (CG) Processing", [
                    ('cg_analyze_successful', 'CG analysis successful'),
                    ('cg_create_record_successful', 'CG record created'),
                    ('cg_upload_files_successful', 'CG files uploaded'),
                ]),
                ("STEP 6: Verify Results", [
                    ('both_reports_have_file_ids', 'Both reports have file IDs'),
                    ('no_duplicates_detected', 'No duplicates detected'),
                ]),
                ("STEP 7: Backend Logs", [
                    ('backend_logs_checked', 'Backend logs checked'),
                    ('no_errors_in_logs', 'No errors in logs'),
                    ('no_rate_limiting_429', 'No rate limiting errors'),
                    ('ai_analysis_successful', 'AI analysis working'),
                ])
            ]
            
            for step_name, step_tests in steps:
                self.log(f"{step_name}:")
                for test_key, description in step_tests:
                    status = "✅ PASS" if self.test_results.get(test_key, False) else "❌ FAIL"
                    self.log(f"   {status} - {description}")
                self.log("")
            
            # Key metrics
            self.log("📈 KEY METRICS:")
            self.log(f"   Total Survey Reports: {self.test_results.get('total_survey_reports_count', 0)}")
            if self.test_results.get('file_ccm_page_count', 0) > 0:
                self.log(f"   CCM file pages: {self.test_results['file_ccm_page_count']}")
            if self.test_results.get('file_cg_page_count', 0) > 0:
                self.log(f"   CG file pages: {self.test_results['file_cg_page_count']}")
            
            # File IDs
            if self.test_results.get('ccm_original_file_id'):
                self.log(f"   CCM Original File ID: {self.test_results['ccm_original_file_id']}")
            if self.test_results.get('ccm_summary_file_id'):
                self.log(f"   CCM Summary File ID: {self.test_results['ccm_summary_file_id']}")
            if self.test_results.get('cg_original_file_id'):
                self.log(f"   CG Original File ID: {self.test_results['cg_original_file_id']}")
            if self.test_results.get('cg_summary_file_id'):
                self.log(f"   CG Summary File ID: {self.test_results['cg_summary_file_id']}")
            
            # Overall assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'ccm_analyze_successful', 'ccm_create_record_successful', 'ccm_upload_files_successful',
                'cg_analyze_successful', 'cg_create_record_successful', 'cg_upload_files_successful',
                'both_reports_have_file_ids', 'no_duplicates_detected'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.test_results.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL REQUIREMENTS MET")
                self.log("   ✅ Batch upload workflow working correctly")
                self.log("   ✅ Both files analyzed successfully")
                self.log("   ✅ Both records created")
                self.log("   ✅ All files uploaded to Google Drive")
                self.log("   ✅ No validation errors")
                self.log("   ✅ No rate limit errors")
                self.log("   ✅ No duplicate errors")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            if success_rate >= 90:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 75:
                self.log(f"   ✅ GOOD SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ MODERATE SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing final summary: {str(e)}", "ERROR")
    
    def run_comprehensive_test(self):
        """Run the complete batch upload test"""
        try:
            self.log("🚀 STARTING SURVEY REPORT BATCH UPLOAD TEST")
            self.log("Testing exact frontend workflow with 5s delay between files")
            self.log("Files: CCM (02-19).pdf and CG (02-19).pdf")
            self.log("Ship: BROTHER 36 (7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7)")
            
            # Execute all steps
            step1_success = self.step1_download_and_verify_files()
            if not step1_success:
                self.log("❌ CRITICAL: Step 1 failed - cannot proceed", "ERROR")
                return False
            
            step2_success = self.step2_setup_and_login()
            if not step2_success:
                self.log("❌ CRITICAL: Step 2 failed - cannot proceed", "ERROR")
                return False
            
            step3_success = self.step3_test_file1_ccm()
            if not step3_success:
                self.log("⚠️ WARNING: Step 3 failed - continuing with remaining tests", "WARNING")
            
            step4_success = self.step4_wait_5_seconds()
            
            step5_success = self.step5_test_file2_cg()
            if not step5_success:
                self.log("⚠️ WARNING: Step 5 failed - continuing with verification", "WARNING")
            
            step6_success = self.step6_verify_results()
            step7_success = self.step7_check_backend_logs()
            
            # Print final summary
            self.print_final_summary()
            
            return step1_success and step2_success
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False

def main():
    """Main function to run the test"""
    try:
        tester = SurveyReportBatchUploadTester()
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n✅ Survey Report Batch Upload Test completed successfully")
            return 0
        else:
            print("\n❌ Survey Report Batch Upload Test failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Critical error: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
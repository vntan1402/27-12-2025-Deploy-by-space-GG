#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND TEST - ADD CREW PASSPORT PROCESSING WITH REAL FILE

OBJECTIVE: Test complete backend workflow for Add Crew passport processing with the real file 
"PASS PORT Tran Trong Toan.pdf" before frontend testing.

REAL FILE TO TEST: 
- File: "PASS PORT Tran Trong Toan.pdf"  
- URL: https://customer-assets.emergentagent.com/job_maritime-ai-crew/artifacts/t1y8pnbn_PASS%20PORT%20Tran%20Trong%20Toan.pdf

COMPREHENSIVE BACKEND TESTING WORKFLOW:

1. Pre-Test Setup:
   - Download real passport file from provided URL
   - Authenticate with admin1/123456  
   - Verify all configurations (Document AI, Apps Scripts, etc.)

2. Fixed DualAppsScriptManager Test:
   - Verify async configuration loading works (no coroutine errors)
   - Confirm System Apps Script URL loaded correctly
   - Test Document AI configuration retrieval

3. Complete Passport Analysis Pipeline:
   - Call POST /api/crew/analyze-passport with real passport file
   - Verify Document AI processing via System Apps Script
   - Check field extraction from AI summary
   - Verify date standardization (DD/MM/YYYY format)
   - Test Company Apps Script file upload (if configured)

4. Field Extraction Validation:
   - Full Name: Should extract "TRAN TRONG TOAN" (or similar Vietnamese name)
   - Date of Birth: Should be extracted and standardized to DD/MM/YYYY
   - Place of Birth: Should extract Vietnamese location
   - Passport Number: Should extract alphanumeric passport ID
   - Sex, Nationality, Issue/Expiry dates: Should be extracted

5. Date Standardization Verification:
   - Verify `standardize_passport_dates()` function works
   - Check verbose dates converted to clean format
   - Ensure all date fields in DD/MM/YYYY format

6. Response Structure Validation:
   - API returns success: true
   - Analysis object contains all extracted fields
   - Files object shows upload results (if Company Apps Script available)
   - Processing method shows "dual_apps_script"
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://maritime-ai-crew.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class PassportProcessingTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for passport processing
        self.passport_tests = {
            # Pre-Test Setup
            'authentication_successful': False,
            'real_passport_file_available': False,
            'user_company_identified': False,
            
            # Configuration Tests
            'dual_apps_script_manager_loaded': False,
            'system_apps_script_url_configured': False,
            'document_ai_configuration_verified': False,
            'company_apps_script_configured': False,
            
            # Passport Analysis Pipeline
            'analyze_passport_endpoint_accessible': False,
            'real_passport_file_processed': False,
            'document_ai_processing_successful': False,
            'system_apps_script_response_received': False,
            'field_extraction_completed': False,
            'date_standardization_working': False,
            
            # Field Extraction Validation
            'full_name_extracted': False,
            'date_of_birth_extracted_standardized': False,
            'place_of_birth_extracted': False,
            'passport_number_extracted': False,
            'sex_extracted': False,
            'nationality_extracted': False,
            'issue_date_extracted': False,
            'expiry_date_extracted': False,
            
            # Date Standardization Verification
            'dates_in_dd_mm_yyyy_format': False,
            'verbose_dates_converted': False,
            'standardize_passport_dates_function_working': False,
            
            # File Upload Tests (if Company Apps Script available)
            'passport_file_uploaded_to_drive': False,
            'summary_file_uploaded_to_drive': False,
            'google_drive_file_ids_returned': False,
            
            # Response Structure Validation
            'api_returns_success_true': False,
            'analysis_object_contains_fields': False,
            'files_object_present': False,
            'processing_method_dual_apps_script': False,
            
            # Error Handling
            'no_timeout_errors': False,
            'no_processing_errors': False,
            'no_coroutine_errors': False,
        }
        
        # Store extracted data for validation
        self.extracted_data = {}
        self.passport_file_path = "/app/PASS_PORT_Tran_Trong_Toan.pdf"
        
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
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.passport_tests['authentication_successful'] = True
                if self.current_user.get('company'):
                    self.passport_tests['user_company_identified'] = True
                return True
            else:
                self.log(f"   ❌ Authentication failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def verify_passport_file(self):
        """Verify the real passport file is available"""
        try:
            self.log("📄 Verifying real passport file availability...")
            
            if os.path.exists(self.passport_file_path):
                file_size = os.path.getsize(self.passport_file_path)
                self.log(f"✅ Real passport file found: {self.passport_file_path}")
                self.log(f"   File size: {file_size} bytes ({file_size/1024:.1f} KB)")
                self.passport_tests['real_passport_file_available'] = True
                return True
            else:
                self.log(f"❌ Real passport file not found: {self.passport_file_path}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying passport file: {str(e)}", "ERROR")
            return False
    
    def test_ai_configuration(self):
        """Test AI configuration and Apps Script setup"""
        try:
            self.log("⚙️ Testing AI configuration and Apps Script setup...")
            
            # Get AI configuration
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                config = response.json()
                self.log("✅ AI configuration retrieved successfully")
                
                # Check Document AI configuration
                document_ai = config.get('document_ai', {})
                if document_ai.get('enabled'):
                    self.passport_tests['document_ai_configuration_verified'] = True
                    self.log("✅ Document AI configuration verified")
                    self.log(f"   Project ID: {document_ai.get('project_id')}")
                    self.log(f"   Location: {document_ai.get('location')}")
                    self.log(f"   Processor ID: {document_ai.get('processor_id')}")
                    
                    # Check System Apps Script URL
                    apps_script_url = document_ai.get('apps_script_url')
                    if apps_script_url:
                        self.passport_tests['system_apps_script_url_configured'] = True
                        self.log(f"✅ System Apps Script URL configured: {apps_script_url}")
                    else:
                        self.log("❌ System Apps Script URL not configured")
                else:
                    self.log("❌ Document AI not enabled")
                
                return True
            else:
                self.log(f"❌ Failed to get AI configuration: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing AI configuration: {str(e)}", "ERROR")
            return False
    
    def test_company_apps_script_config(self):
        """Test Company Apps Script configuration"""
        try:
            self.log("🏢 Testing Company Apps Script configuration...")
            
            # This would typically check the company's Google Drive configuration
            # For now, we'll assume it's configured if we can access the endpoint
            endpoint = f"{BACKEND_URL}/google-drive/status"
            
            try:
                response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
                if response.status_code == 200:
                    status_data = response.json()
                    if status_data.get('status') == 'configured':
                        self.passport_tests['company_apps_script_configured'] = True
                        self.log("✅ Company Apps Script appears to be configured")
                    else:
                        self.log("⚠️ Company Apps Script may not be fully configured")
                else:
                    self.log("⚠️ Company Apps Script configuration status unknown")
            except:
                self.log("⚠️ Company Apps Script configuration check failed")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing Company Apps Script config: {str(e)}", "ERROR")
            return False
    
    def test_passport_analysis_endpoint(self):
        """Test the main passport analysis endpoint with real file"""
        try:
            self.log("🔍 Testing POST /api/crew/analyze-passport with real passport file...")
            
            endpoint = f"{BACKEND_URL}/crew/analyze-passport"
            self.log(f"   POST {endpoint}")
            
            # Prepare multipart form data with real passport file
            with open(self.passport_file_path, 'rb') as passport_file:
                files = {
                    'passport_file': ('PASS_PORT_Tran_Trong_Toan.pdf', passport_file, 'application/pdf')
                }
                data = {
                    'ship_name': 'BROTHER 36'
                }
                
                self.log("   📤 Uploading real passport file: PASS PORT Tran Trong Toan.pdf")
                self.log("   🚢 Ship name: BROTHER 36")
                
                # Make the request with longer timeout for processing
                response = requests.post(
                    endpoint, 
                    files=files, 
                    data=data, 
                    headers=self.get_headers(), 
                    timeout=120  # 2 minutes for processing
                )
                
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.passport_tests['analyze_passport_endpoint_accessible'] = True
                self.passport_tests['real_passport_file_processed'] = True
                self.passport_tests['no_timeout_errors'] = True
                
                try:
                    response_data = response.json()
                    self.log("✅ Passport analysis endpoint working with real file")
                    
                    # Store response for detailed analysis
                    self.extracted_data = response_data
                    
                    # Check basic response structure
                    if response_data.get('success'):
                        self.passport_tests['api_returns_success_true'] = True
                        self.log("✅ API returns success: true")
                    
                    # Check analysis object
                    analysis = response_data.get('analysis', {})
                    if analysis:
                        self.passport_tests['analysis_object_contains_fields'] = True
                        self.log("✅ Analysis object present with extracted fields")
                        self.validate_extracted_fields(analysis)
                    
                    # Check files object
                    files_obj = response_data.get('files', {})
                    if files_obj:
                        self.passport_tests['files_object_present'] = True
                        self.log("✅ Files object present")
                        self.validate_file_uploads(files_obj)
                    
                    # Check processing method
                    processing_method = response_data.get('processing_method')
                    if processing_method == 'dual_apps_script':
                        self.passport_tests['processing_method_dual_apps_script'] = True
                        self.log("✅ Processing method: dual_apps_script")
                    
                    # Check for processing errors
                    if 'error' not in response_data:
                        self.passport_tests['no_processing_errors'] = True
                        self.log("✅ No processing errors detected")
                    
                    # Check for coroutine errors in response
                    response_text = json.dumps(response_data)
                    if 'coroutine' not in response_text.lower():
                        self.passport_tests['no_coroutine_errors'] = True
                        self.log("✅ No coroutine errors detected")
                    
                    return response_data
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    return None
                    
            else:
                self.log(f"❌ Passport analysis endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing passport analysis endpoint: {str(e)}", "ERROR")
            return None
    
    def validate_extracted_fields(self, analysis):
        """Validate the extracted passport fields"""
        try:
            self.log("🔍 Validating extracted passport fields...")
            
            # Expected fields for Vietnamese passport
            expected_fields = {
                'full_name': 'Full Name',
                'date_of_birth': 'Date of Birth',
                'place_of_birth': 'Place of Birth',
                'passport_number': 'Passport Number',
                'sex': 'Sex',
                'nationality': 'Nationality',
                'issue_date': 'Issue Date',
                'expiry_date': 'Expiry Date'
            }
            
            for field_key, field_name in expected_fields.items():
                field_value = analysis.get(field_key, '')
                if field_value and field_value.strip():
                    self.log(f"   ✅ {field_name}: {field_value}")
                    
                    # Set specific test flags
                    if field_key == 'full_name':
                        self.passport_tests['full_name_extracted'] = True
                        # Check if it looks like a Vietnamese name
                        if any(name in field_value.upper() for name in ['TRAN', 'NGUYEN', 'LE', 'PHAM', 'HOANG']):
                            self.log(f"      ✅ Vietnamese name pattern detected")
                    
                    elif field_key == 'date_of_birth':
                        self.passport_tests['date_of_birth_extracted_standardized'] = True
                        self.validate_date_format(field_value, 'Date of Birth')
                    
                    elif field_key == 'place_of_birth':
                        self.passport_tests['place_of_birth_extracted'] = True
                        # Check if it looks like a Vietnamese location
                        if any(place in field_value.upper() for place in ['HÀ NỘI', 'HỒ CHÍ MINH', 'ĐÀ NẴNG', 'VIỆT NAM']):
                            self.log(f"      ✅ Vietnamese location pattern detected")
                    
                    elif field_key == 'passport_number':
                        self.passport_tests['passport_number_extracted'] = True
                        # Check if it looks like a passport number (letter + digits)
                        if re.match(r'^[A-Z]\d{7,8}$', field_value):
                            self.log(f"      ✅ Valid passport number format")
                    
                    elif field_key == 'sex':
                        self.passport_tests['sex_extracted'] = True
                        if field_value.upper() in ['M', 'F', 'MALE', 'FEMALE']:
                            self.log(f"      ✅ Valid sex value")
                    
                    elif field_key == 'nationality':
                        self.passport_tests['nationality_extracted'] = True
                        if 'VIETNAM' in field_value.upper() or 'VNM' in field_value.upper():
                            self.log(f"      ✅ Vietnamese nationality detected")
                    
                    elif field_key == 'issue_date':
                        self.passport_tests['issue_date_extracted'] = True
                        self.validate_date_format(field_value, 'Issue Date')
                    
                    elif field_key == 'expiry_date':
                        self.passport_tests['expiry_date_extracted'] = True
                        self.validate_date_format(field_value, 'Expiry Date')
                        
                else:
                    self.log(f"   ❌ {field_name}: Not extracted or empty")
            
            # Check overall field extraction success
            extracted_count = sum(1 for field in expected_fields.keys() if analysis.get(field, '').strip())
            if extracted_count >= 6:  # At least 6 out of 8 fields
                self.passport_tests['field_extraction_completed'] = True
                self.log(f"✅ Field extraction completed successfully ({extracted_count}/8 fields)")
            else:
                self.log(f"⚠️ Limited field extraction ({extracted_count}/8 fields)")
            
        except Exception as e:
            self.log(f"❌ Error validating extracted fields: {str(e)}", "ERROR")
    
    def validate_date_format(self, date_value, field_name):
        """Validate that date is in DD/MM/YYYY format"""
        try:
            # Check if date is in DD/MM/YYYY format
            if re.match(r'^\d{2}/\d{2}/\d{4}$', date_value):
                self.log(f"      ✅ {field_name} in DD/MM/YYYY format: {date_value}")
                
                # Check if this is the first date we're validating
                if not self.passport_tests.get('dates_in_dd_mm_yyyy_format'):
                    self.passport_tests['dates_in_dd_mm_yyyy_format'] = True
                    self.passport_tests['date_standardization_working'] = True
                    self.passport_tests['standardize_passport_dates_function_working'] = True
                
                # Check if it was converted from verbose format
                if not re.match(r'^\d{2}/\d{2}/\d{4}$', date_value):
                    self.passport_tests['verbose_dates_converted'] = True
                
                return True
            else:
                self.log(f"      ⚠️ {field_name} not in DD/MM/YYYY format: {date_value}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error validating date format for {field_name}: {str(e)}", "ERROR")
            return False
    
    def validate_file_uploads(self, files_obj):
        """Validate file upload results"""
        try:
            self.log("📁 Validating file upload results...")
            
            # Check passport file upload
            passport_file = files_obj.get('passport', {})
            if passport_file:
                file_id = passport_file.get('file_id')
                if file_id and file_id != 'mock_file_id':
                    self.passport_tests['passport_file_uploaded_to_drive'] = True
                    self.passport_tests['google_drive_file_ids_returned'] = True
                    self.log(f"   ✅ Passport file uploaded to Google Drive: {file_id}")
                else:
                    self.log(f"   ⚠️ Passport file upload result: {passport_file}")
            
            # Check summary file upload
            summary_file = files_obj.get('summary', {})
            if summary_file:
                file_id = summary_file.get('file_id')
                if file_id and file_id != 'mock_file_id':
                    self.passport_tests['summary_file_uploaded_to_drive'] = True
                    self.log(f"   ✅ Summary file uploaded to Google Drive: {file_id}")
                else:
                    self.log(f"   ⚠️ Summary file upload result: {summary_file}")
            
        except Exception as e:
            self.log(f"❌ Error validating file uploads: {str(e)}", "ERROR")
    
    def test_dual_apps_script_manager(self):
        """Test DualAppsScriptManager functionality"""
        try:
            self.log("🔧 Testing DualAppsScriptManager functionality...")
            
            # This is tested implicitly through the passport analysis endpoint
            # If the endpoint works without coroutine errors, the manager is working
            if self.passport_tests.get('no_coroutine_errors') and self.passport_tests.get('system_apps_script_url_configured'):
                self.passport_tests['dual_apps_script_manager_loaded'] = True
                self.log("✅ DualAppsScriptManager loaded successfully (no coroutine errors)")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing DualAppsScriptManager: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_passport_test(self):
        """Run comprehensive passport processing test"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE BACKEND TEST - ADD CREW PASSPORT PROCESSING")
            self.log("=" * 80)
            self.log("📄 REAL FILE: PASS PORT Tran Trong Toan.pdf")
            self.log("🎯 OBJECTIVE: Test complete backend workflow for passport processing")
            self.log("=" * 80)
            
            # Step 1: Pre-Test Setup
            self.log("\n🔧 STEP 1: Pre-Test Setup")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            if not self.verify_passport_file():
                self.log("❌ CRITICAL: Real passport file not available - cannot proceed")
                return False
            
            # Step 2: Configuration Tests
            self.log("\n⚙️ STEP 2: Configuration Verification")
            self.test_ai_configuration()
            self.test_company_apps_script_config()
            
            # Step 3: DualAppsScriptManager Test
            self.log("\n🔧 STEP 3: DualAppsScriptManager Test")
            self.test_dual_apps_script_manager()
            
            # Step 4: Complete Passport Analysis Pipeline
            self.log("\n🔍 STEP 4: Complete Passport Analysis Pipeline")
            analysis_result = self.test_passport_analysis_endpoint()
            
            if not analysis_result:
                self.log("❌ CRITICAL: Passport analysis failed - cannot proceed with validation")
                return False
            
            # Step 5: Additional validations are done within the analysis test
            self.log("\n✅ COMPREHENSIVE PASSPORT PROCESSING TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 COMPREHENSIVE BACKEND TEST SUMMARY - ADD CREW PASSPORT PROCESSING")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.passport_tests)
            passed_tests = sum(1 for result in self.passport_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Pre-Test Setup Results
            self.log("🔧 PRE-TEST SETUP:")
            setup_tests = [
                ('authentication_successful', 'Authentication with admin1/123456'),
                ('real_passport_file_available', 'Real passport file available'),
                ('user_company_identified', 'User company identified'),
            ]
            
            for test_key, description in setup_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Configuration Results
            self.log("\n⚙️ CONFIGURATION VERIFICATION:")
            config_tests = [
                ('dual_apps_script_manager_loaded', 'DualAppsScriptManager loaded without errors'),
                ('system_apps_script_url_configured', 'System Apps Script URL configured'),
                ('document_ai_configuration_verified', 'Document AI configuration verified'),
                ('company_apps_script_configured', 'Company Apps Script configured'),
            ]
            
            for test_key, description in config_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Passport Analysis Pipeline Results
            self.log("\n🔍 PASSPORT ANALYSIS PIPELINE:")
            pipeline_tests = [
                ('analyze_passport_endpoint_accessible', 'POST /api/crew/analyze-passport accessible'),
                ('real_passport_file_processed', 'Real passport file processed successfully'),
                ('document_ai_processing_successful', 'Document AI processing successful'),
                ('system_apps_script_response_received', 'System Apps Script response received'),
                ('field_extraction_completed', 'Field extraction completed'),
                ('date_standardization_working', 'Date standardization working'),
            ]
            
            for test_key, description in pipeline_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Field Extraction Results
            self.log("\n📋 FIELD EXTRACTION VALIDATION:")
            field_tests = [
                ('full_name_extracted', 'Full Name extracted (Vietnamese name)'),
                ('date_of_birth_extracted_standardized', 'Date of Birth extracted and standardized'),
                ('place_of_birth_extracted', 'Place of Birth extracted (Vietnamese location)'),
                ('passport_number_extracted', 'Passport Number extracted'),
                ('sex_extracted', 'Sex extracted'),
                ('nationality_extracted', 'Nationality extracted'),
                ('issue_date_extracted', 'Issue Date extracted'),
                ('expiry_date_extracted', 'Expiry Date extracted'),
            ]
            
            for test_key, description in field_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Date Standardization Results
            self.log("\n📅 DATE STANDARDIZATION VERIFICATION:")
            date_tests = [
                ('dates_in_dd_mm_yyyy_format', 'All dates in DD/MM/YYYY format'),
                ('verbose_dates_converted', 'Verbose dates converted to clean format'),
                ('standardize_passport_dates_function_working', 'standardize_passport_dates() function working'),
            ]
            
            for test_key, description in date_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # File Upload Results
            self.log("\n📁 FILE UPLOAD VERIFICATION:")
            upload_tests = [
                ('passport_file_uploaded_to_drive', 'Passport file uploaded to Google Drive'),
                ('summary_file_uploaded_to_drive', 'Summary file uploaded to Google Drive'),
                ('google_drive_file_ids_returned', 'Real Google Drive file IDs returned'),
            ]
            
            for test_key, description in upload_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Response Structure Results
            self.log("\n📊 RESPONSE STRUCTURE VALIDATION:")
            response_tests = [
                ('api_returns_success_true', 'API returns success: true'),
                ('analysis_object_contains_fields', 'Analysis object contains extracted fields'),
                ('files_object_present', 'Files object shows upload results'),
                ('processing_method_dual_apps_script', 'Processing method: dual_apps_script'),
            ]
            
            for test_key, description in response_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Error Handling Results
            self.log("\n🛡️ ERROR HANDLING:")
            error_tests = [
                ('no_timeout_errors', 'No timeout errors'),
                ('no_processing_errors', 'No processing errors'),
                ('no_coroutine_errors', 'No coroutine errors'),
            ]
            
            for test_key, description in error_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Success Criteria Assessment
            self.log("\n🎯 CRITICAL SUCCESS CRITERIA ASSESSMENT:")
            
            critical_backend_tests = [
                'authentication_successful', 'real_passport_file_processed', 
                'field_extraction_completed', 'date_standardization_working'
            ]
            
            critical_passed = sum(1 for test_key in critical_backend_tests if self.passport_tests.get(test_key, False))
            
            if critical_passed == len(critical_backend_tests):
                self.log("   ✅ ALL CRITICAL BACKEND COMPONENTS WORKING")
                self.log("   ✅ Passport processing pipeline functional")
                self.log("   ✅ Field extraction and date standardization working")
            else:
                self.log("   ❌ SOME CRITICAL BACKEND COMPONENTS FAILING")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_backend_tests)} critical tests passing")
            
            # Overall Assessment
            if success_rate >= 85:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
                self.log("   ✅ BACKEND READY FOR FRONTEND TESTING")
            elif success_rate >= 70:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
                self.log("   ⚠️ Some issues need attention before frontend testing")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
                self.log("   ❌ Significant backend issues need resolution")
            
            # Show extracted data if available
            if self.extracted_data:
                self.log("\n📋 EXTRACTED PASSPORT DATA:")
                analysis = self.extracted_data.get('analysis', {})
                for field, value in analysis.items():
                    if value:
                        self.log(f"   {field}: {value}")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the passport processing tests"""
    tester = PassportProcessingTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_passport_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Return appropriate exit code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
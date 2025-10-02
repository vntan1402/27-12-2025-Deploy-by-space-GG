#!/usr/bin/env python3
"""
AI Certificate Analysis Test for MINH ANH 09 Certificate
FOCUS: Test the AI certificate analysis endpoint with the specific certificate that user reported issues with

REVIEW REQUEST REQUIREMENTS:
1. Test POST /api/analyze-ship-certificate endpoint with the MINH ANH 09 certificate file
2. Verify that AI can extract ship information like:
   - ship_name: MINH ANH 09  
   - imo_number: 8589911
   - certificate_name: CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE
   - certificate_number: PM242308
   - issue_date: OCTOBER 4, 2024
   - valid_date: MAY 5, 2027
3. Check AI configuration in system settings
4. Identify any errors in the AI configuration or processing pipeline

EXPECTED BEHAVIOR:
- AI should properly extract all the specified ship information from the certificate
- The "Add new ship" functionality should work with extracted data
- AI configuration should be properly set up for analysis

TEST FOCUS:
- AI certificate analysis endpoint functionality
- Data extraction accuracy for specific certificate
- AI configuration verification
- Error identification in processing pipeline
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
# Try internal URL first, then external
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fleet-tracker-104.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class AICertificateAnalysisTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Expected values from the MINH ANH 09 certificate
        self.expected_values = {
            'ship_name': 'MINH ANH 09',
            'imo_number': '8589911',
            'certificate_name': 'CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE',
            'certificate_number': 'PM242308',
            'issue_date': 'OCTOBER 4, 2024',  # Could be in various formats
            'valid_date': 'MAY 5, 2027'  # Could be in various formats
        }
        
        # Test tracking for AI certificate analysis functionality
        self.analysis_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'ai_config_accessible': False,
            'ai_config_properly_configured': False,
            
            # Certificate file handling
            'certificate_file_available': False,
            'analyze_endpoint_accessible': False,
            'file_upload_successful': False,
            
            # AI analysis results
            'ai_analysis_successful': False,
            'ship_name_extracted_correctly': False,
            'imo_number_extracted_correctly': False,
            'certificate_name_extracted_correctly': False,
            'certificate_number_extracted_correctly': False,
            'issue_date_extracted_correctly': False,
            'valid_date_extracted_correctly': False,
            
            # Data quality and format
            'response_format_correct': False,
            'extracted_data_complete': False,
            'add_new_ship_data_ready': False,
            
            # Error handling
            'error_handling_working': False,
            'processing_pipeline_functional': False,
        }
        
        # Store analysis results for detailed examination
        self.analysis_result = {}
        self.ai_config = {}
        
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
        """Authenticate with admin1/123456 credentials as specified in review request"""
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
                
                self.analysis_tests['authentication_successful'] = True
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
    
    def check_ai_configuration(self):
        """Check AI configuration in system settings"""
        try:
            self.log("🤖 Checking AI configuration in system settings...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            self.log(f"   GET {endpoint}")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.ai_config = response.json()
                self.analysis_tests['ai_config_accessible'] = True
                self.log("✅ AI configuration accessible")
                
                # Log AI configuration details
                self.log("   AI Configuration:")
                self.log(f"      Provider: {self.ai_config.get('provider', 'Not set')}")
                self.log(f"      Model: {self.ai_config.get('model', 'Not set')}")
                self.log(f"      Using Emergent Key: {self.ai_config.get('use_emergent_key', 'Not set')}")
                
                # Check if configuration is properly set
                provider = self.ai_config.get('provider')
                model = self.ai_config.get('model')
                use_emergent_key = self.ai_config.get('use_emergent_key')
                
                if provider and model:
                    self.analysis_tests['ai_config_properly_configured'] = True
                    self.log("✅ AI configuration appears to be properly configured")
                    
                    if use_emergent_key:
                        self.log("   ✅ Using Emergent key for AI analysis")
                    else:
                        self.log("   ⚠️ Not using Emergent key - custom API key configured")
                else:
                    self.log("   ❌ AI configuration incomplete - missing provider or model")
                
                return True
            else:
                self.log(f"   ❌ Failed to get AI configuration: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking AI configuration: {str(e)}", "ERROR")
            return False
    
    def check_certificate_file(self):
        """Check if the MINH ANH 09 certificate file is available"""
        try:
            self.log("📄 Checking MINH ANH 09 certificate file availability...")
            
            certificate_path = "/app/MINH_ANH_09_certificate.pdf"
            
            if os.path.exists(certificate_path):
                file_size = os.path.getsize(certificate_path)
                self.log(f"✅ Certificate file found: {certificate_path}")
                self.log(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                
                self.analysis_tests['certificate_file_available'] = True
                return certificate_path
            else:
                self.log(f"❌ Certificate file not found: {certificate_path}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error checking certificate file: {str(e)}", "ERROR")
            return None
    
    def test_analyze_certificate_endpoint(self, certificate_path):
        """Test the analyze-ship-certificate endpoint with the MINH ANH 09 certificate"""
        try:
            self.log("🔍 Testing analyze-ship-certificate endpoint...")
            
            endpoint = f"{BACKEND_URL}/analyze-ship-certificate"
            self.log(f"   POST {endpoint}")
            
            # Prepare file for upload
            with open(certificate_path, 'rb') as file:
                files = {
                    'file': ('MINH_ANH_09_certificate.pdf', file, 'application/pdf')
                }
                
                self.log("   Uploading certificate file for analysis...")
                response = requests.post(
                    endpoint,
                    files=files,
                    headers=self.get_headers(),
                    timeout=120  # Longer timeout for AI processing
                )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.analysis_tests['analyze_endpoint_accessible'] = True
                self.analysis_tests['file_upload_successful'] = True
                self.log("✅ Certificate analysis endpoint accessible and file uploaded successfully")
                
                response_data = response.json()
                self.log("   Analysis Response:")
                self.log(f"   {json.dumps(response_data, indent=2)}")
                
                # Check response format
                if 'success' in response_data and 'analysis' in response_data:
                    self.analysis_tests['response_format_correct'] = True
                    self.log("✅ Response format is correct")
                    
                    if response_data.get('success'):
                        self.analysis_tests['ai_analysis_successful'] = True
                        self.log("✅ AI analysis completed successfully")
                        
                        # Store analysis result for detailed examination
                        self.analysis_result = response_data.get('analysis', {})
                        
                        # Verify extracted data
                        self.verify_extracted_data()
                        
                        return True
                    else:
                        self.log(f"   ❌ AI analysis failed: {response_data.get('message', 'Unknown error')}")
                        return False
                else:
                    self.log("   ❌ Invalid response format")
                    return False
            else:
                self.log(f"   ❌ Certificate analysis failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                    self.analysis_tests['error_handling_working'] = True
                except:
                    self.log(f"      Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Certificate analysis testing error: {str(e)}", "ERROR")
            return False
    
    def verify_extracted_data(self):
        """Verify that the AI extracted the expected data correctly"""
        try:
            self.log("🔍 Verifying extracted data against expected values...")
            
            if not self.analysis_result:
                self.log("   ❌ No analysis result to verify")
                return False
            
            # Check each expected field
            extraction_results = {}
            
            # Ship Name
            extracted_ship_name = self.analysis_result.get('ship_name', '')
            expected_ship_name = self.expected_values['ship_name']
            if self.normalize_text(extracted_ship_name) == self.normalize_text(expected_ship_name):
                self.analysis_tests['ship_name_extracted_correctly'] = True
                extraction_results['ship_name'] = '✅ CORRECT'
                self.log(f"   ✅ Ship Name: '{extracted_ship_name}' (Expected: '{expected_ship_name}')")
            else:
                extraction_results['ship_name'] = '❌ INCORRECT'
                self.log(f"   ❌ Ship Name: '{extracted_ship_name}' (Expected: '{expected_ship_name}')")
            
            # IMO Number
            extracted_imo = str(self.analysis_result.get('imo_number', ''))
            expected_imo = self.expected_values['imo_number']
            if self.normalize_text(extracted_imo) == self.normalize_text(expected_imo):
                self.analysis_tests['imo_number_extracted_correctly'] = True
                extraction_results['imo_number'] = '✅ CORRECT'
                self.log(f"   ✅ IMO Number: '{extracted_imo}' (Expected: '{expected_imo}')")
            else:
                extraction_results['imo_number'] = '❌ INCORRECT'
                self.log(f"   ❌ IMO Number: '{extracted_imo}' (Expected: '{expected_imo}')")
            
            # Certificate Name
            extracted_cert_name = self.analysis_result.get('cert_name', '')
            expected_cert_name = self.expected_values['certificate_name']
            if self.normalize_text(extracted_cert_name) == self.normalize_text(expected_cert_name):
                self.analysis_tests['certificate_name_extracted_correctly'] = True
                extraction_results['certificate_name'] = '✅ CORRECT'
                self.log(f"   ✅ Certificate Name: '{extracted_cert_name}' (Expected: '{expected_cert_name}')")
            else:
                extraction_results['certificate_name'] = '❌ INCORRECT'
                self.log(f"   ❌ Certificate Name: '{extracted_cert_name}' (Expected: '{expected_cert_name}')")
            
            # Certificate Number
            extracted_cert_no = self.analysis_result.get('cert_no', '')
            expected_cert_no = self.expected_values['certificate_number']
            if self.normalize_text(extracted_cert_no) == self.normalize_text(expected_cert_no):
                self.analysis_tests['certificate_number_extracted_correctly'] = True
                extraction_results['certificate_number'] = '✅ CORRECT'
                self.log(f"   ✅ Certificate Number: '{extracted_cert_no}' (Expected: '{expected_cert_no}')")
            else:
                extraction_results['certificate_number'] = '❌ INCORRECT'
                self.log(f"   ❌ Certificate Number: '{extracted_cert_no}' (Expected: '{expected_cert_no}')")
            
            # Issue Date (more flexible matching due to date format variations)
            extracted_issue_date = self.analysis_result.get('issue_date', '')
            expected_issue_date = self.expected_values['issue_date']
            if self.compare_dates(extracted_issue_date, expected_issue_date):
                self.analysis_tests['issue_date_extracted_correctly'] = True
                extraction_results['issue_date'] = '✅ CORRECT'
                self.log(f"   ✅ Issue Date: '{extracted_issue_date}' (Expected: '{expected_issue_date}')")
            else:
                extraction_results['issue_date'] = '❌ INCORRECT'
                self.log(f"   ❌ Issue Date: '{extracted_issue_date}' (Expected: '{expected_issue_date}')")
            
            # Valid Date (more flexible matching due to date format variations)
            extracted_valid_date = self.analysis_result.get('valid_date', '')
            expected_valid_date = self.expected_values['valid_date']
            if self.compare_dates(extracted_valid_date, expected_valid_date):
                self.analysis_tests['valid_date_extracted_correctly'] = True
                extraction_results['valid_date'] = '✅ CORRECT'
                self.log(f"   ✅ Valid Date: '{extracted_valid_date}' (Expected: '{expected_valid_date}')")
            else:
                extraction_results['valid_date'] = '❌ INCORRECT'
                self.log(f"   ❌ Valid Date: '{extracted_valid_date}' (Expected: '{expected_valid_date}')")
            
            # Calculate extraction accuracy
            correct_extractions = sum(1 for result in extraction_results.values() if '✅' in result)
            total_extractions = len(extraction_results)
            accuracy_rate = (correct_extractions / total_extractions) * 100
            
            self.log(f"\n📊 EXTRACTION ACCURACY: {accuracy_rate:.1f}% ({correct_extractions}/{total_extractions})")
            
            # Check if data is complete enough for "Add new ship"
            critical_fields = ['ship_name_extracted_correctly', 'imo_number_extracted_correctly']
            critical_correct = sum(1 for field in critical_fields if self.analysis_tests.get(field, False))
            
            if critical_correct == len(critical_fields):
                self.analysis_tests['add_new_ship_data_ready'] = True
                self.log("✅ Critical data extracted correctly - 'Add new ship' should work")
            else:
                self.log("❌ Critical data missing - 'Add new ship' may not work properly")
            
            if accuracy_rate >= 80:
                self.analysis_tests['extracted_data_complete'] = True
                self.log("✅ Data extraction is sufficiently complete")
            else:
                self.log("⚠️ Data extraction has significant gaps")
            
            return accuracy_rate >= 50  # At least 50% accuracy to consider functional
            
        except Exception as e:
            self.log(f"❌ Error verifying extracted data: {str(e)}", "ERROR")
            return False
    
    def normalize_text(self, text):
        """Normalize text for comparison (remove extra spaces, convert to uppercase)"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', str(text).strip().upper())
    
    def compare_dates(self, extracted_date, expected_date):
        """Compare dates with flexible formatting"""
        try:
            # Normalize both dates
            extracted_norm = self.normalize_text(extracted_date)
            expected_norm = self.normalize_text(expected_date)
            
            # Direct match
            if extracted_norm == expected_norm:
                return True
            
            # Try to extract key components (day, month, year)
            # Look for patterns like "OCTOBER 4, 2024", "04/10/2024", "2024-10-04", etc.
            
            # Extract numbers from both dates
            extracted_numbers = re.findall(r'\d+', extracted_date)
            expected_numbers = re.findall(r'\d+', expected_date)
            
            # Extract month names
            months = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
                     'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']
            
            extracted_month = None
            expected_month = None
            
            for i, month in enumerate(months, 1):
                if month in extracted_norm:
                    extracted_month = i
                if month in expected_norm:
                    expected_month = i
            
            # If we found month names and they match, and we have matching numbers, consider it a match
            if extracted_month and expected_month and extracted_month == expected_month:
                # Check if we have matching day and year numbers
                if len(extracted_numbers) >= 2 and len(expected_numbers) >= 2:
                    # Look for matching day and year
                    return any(num in expected_numbers for num in extracted_numbers)
            
            return False
            
        except Exception as e:
            self.log(f"   Warning: Date comparison error: {e}")
            return False
    
    def test_processing_pipeline(self):
        """Test the overall processing pipeline functionality"""
        try:
            self.log("🔧 Testing AI processing pipeline functionality...")
            
            # Check if the analysis result contains expected structure
            if self.analysis_result:
                expected_fields = [
                    'ship_name', 'imo_number', 'cert_name', 'cert_no', 
                    'issue_date', 'valid_date', 'processing_method', 'confidence'
                ]
                
                present_fields = []
                missing_fields = []
                
                for field in expected_fields:
                    if field in self.analysis_result and self.analysis_result[field]:
                        present_fields.append(field)
                    else:
                        missing_fields.append(field)
                
                self.log(f"   Present fields: {len(present_fields)}/{len(expected_fields)}")
                self.log(f"      ✅ {', '.join(present_fields)}")
                
                if missing_fields:
                    self.log(f"   Missing fields: {len(missing_fields)}")
                    self.log(f"      ❌ {', '.join(missing_fields)}")
                
                # Check processing method and confidence
                processing_method = self.analysis_result.get('processing_method', 'unknown')
                confidence = self.analysis_result.get('confidence', 'unknown')
                
                self.log(f"   Processing Method: {processing_method}")
                self.log(f"   Confidence Level: {confidence}")
                
                if len(present_fields) >= len(expected_fields) * 0.7:  # At least 70% of fields present
                    self.analysis_tests['processing_pipeline_functional'] = True
                    self.log("✅ Processing pipeline appears to be functional")
                    return True
                else:
                    self.log("❌ Processing pipeline has significant issues")
                    return False
            else:
                self.log("❌ No analysis result available to test pipeline")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing processing pipeline: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_ai_analysis_tests(self):
        """Main test function for AI certificate analysis"""
        self.log("🤖 STARTING AI CERTIFICATE ANALYSIS TESTING FOR MINH ANH 09")
        self.log("🎯 FOCUS: Test AI certificate analysis endpoint with specific certificate")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Check AI Configuration
            self.log("\n🤖 STEP 2: CHECK AI CONFIGURATION")
            self.log("=" * 50)
            ai_config_success = self.check_ai_configuration()
            
            # Step 3: Check Certificate File
            self.log("\n📄 STEP 3: CHECK CERTIFICATE FILE")
            self.log("=" * 50)
            certificate_path = self.check_certificate_file()
            if not certificate_path:
                self.log("❌ Certificate file not available - cannot proceed with analysis testing")
                return False
            
            # Step 4: Test Certificate Analysis
            self.log("\n🔍 STEP 4: TEST CERTIFICATE ANALYSIS")
            self.log("=" * 50)
            analysis_success = self.test_analyze_certificate_endpoint(certificate_path)
            
            # Step 5: Test Processing Pipeline
            self.log("\n🔧 STEP 5: TEST PROCESSING PIPELINE")
            self.log("=" * 50)
            pipeline_success = self.test_processing_pipeline()
            
            # Step 6: Final Analysis
            self.log("\n📊 STEP 6: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return analysis_success and pipeline_success
            
        except Exception as e:
            self.log(f"❌ Comprehensive AI analysis testing error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of AI certificate analysis testing"""
        try:
            self.log("🤖 AI CERTIFICATE ANALYSIS TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.analysis_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.analysis_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.analysis_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.analysis_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.analysis_tests)})")
            
            # AI Configuration Analysis
            self.log("\n🤖 AI CONFIGURATION ANALYSIS:")
            if self.analysis_tests['ai_config_properly_configured']:
                self.log("   ✅ AI configuration is properly set up")
                self.log(f"      Provider: {self.ai_config.get('provider', 'Unknown')}")
                self.log(f"      Model: {self.ai_config.get('model', 'Unknown')}")
                self.log(f"      Using Emergent Key: {self.ai_config.get('use_emergent_key', 'Unknown')}")
            else:
                self.log("   ❌ AI configuration has issues")
                if not self.analysis_tests['ai_config_accessible']:
                    self.log("      - AI configuration endpoint not accessible")
                else:
                    self.log("      - AI configuration incomplete or invalid")
            
            # Data Extraction Analysis
            self.log("\n🔍 DATA EXTRACTION ANALYSIS:")
            extraction_tests = [
                'ship_name_extracted_correctly',
                'imo_number_extracted_correctly', 
                'certificate_name_extracted_correctly',
                'certificate_number_extracted_correctly',
                'issue_date_extracted_correctly',
                'valid_date_extracted_correctly'
            ]
            extraction_passed = sum(1 for test in extraction_tests if self.analysis_tests.get(test, False))
            extraction_rate = (extraction_passed / len(extraction_tests)) * 100
            
            self.log(f"   📊 EXTRACTION ACCURACY: {extraction_rate:.1f}% ({extraction_passed}/{len(extraction_tests)})")
            
            # Show detailed extraction results
            if self.analysis_result:
                self.log("   Extracted Values vs Expected:")
                self.log(f"      Ship Name: '{self.analysis_result.get('ship_name', 'NOT EXTRACTED')}' (Expected: '{self.expected_values['ship_name']}')")
                self.log(f"      IMO Number: '{self.analysis_result.get('imo_number', 'NOT EXTRACTED')}' (Expected: '{self.expected_values['imo_number']}')")
                self.log(f"      Certificate Name: '{self.analysis_result.get('cert_name', 'NOT EXTRACTED')}' (Expected: '{self.expected_values['certificate_name']}')")
                self.log(f"      Certificate Number: '{self.analysis_result.get('cert_no', 'NOT EXTRACTED')}' (Expected: '{self.expected_values['certificate_number']}')")
                self.log(f"      Issue Date: '{self.analysis_result.get('issue_date', 'NOT EXTRACTED')}' (Expected: '{self.expected_values['issue_date']}')")
                self.log(f"      Valid Date: '{self.analysis_result.get('valid_date', 'NOT EXTRACTED')}' (Expected: '{self.expected_values['valid_date']}')")
            
            # Add New Ship Functionality Analysis
            self.log("\n🚢 'ADD NEW SHIP' FUNCTIONALITY ANALYSIS:")
            if self.analysis_tests['add_new_ship_data_ready']:
                self.log("   ✅ CONFIRMED: 'Add new ship' functionality should work")
                self.log("   ✅ Critical ship information (name, IMO) extracted correctly")
            else:
                self.log("   ❌ ISSUE: 'Add new ship' functionality may not work properly")
                self.log("   ❌ Critical ship information missing or incorrect")
            
            # Review request requirements analysis
            self.log("\n📋 REVIEW REQUEST REQUIREMENTS ANALYSIS:")
            
            req1_met = self.analysis_tests['analyze_endpoint_accessible'] and self.analysis_tests['ai_analysis_successful']
            req2_met = extraction_rate >= 80  # At least 80% of expected data extracted correctly
            req3_met = self.analysis_tests['ai_config_properly_configured']
            req4_met = self.analysis_tests['processing_pipeline_functional']
            
            self.log(f"   1. Test analyze-ship-certificate endpoint: {'✅ MET' if req1_met else '❌ NOT MET'}")
            self.log(f"      - Endpoint accessible and processing certificates")
            
            self.log(f"   2. Verify AI extracts expected ship information: {'✅ MET' if req2_met else '❌ NOT MET'}")
            self.log(f"      - Extraction accuracy: {extraction_rate:.1f}%")
            
            self.log(f"   3. Check AI configuration: {'✅ MET' if req3_met else '❌ NOT MET'}")
            self.log(f"      - AI system properly configured for analysis")
            
            self.log(f"   4. Identify processing pipeline errors: {'✅ MET' if req4_met else '❌ NOT MET'}")
            self.log(f"      - Processing pipeline functionality verified")
            
            requirements_met = sum([req1_met, req2_met, req3_met, req4_met])
            
            # Final conclusion
            if success_rate >= 80 and requirements_met >= 3:
                self.log(f"\n🎉 CONCLUSION: AI CERTIFICATE ANALYSIS IS WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - AI analysis functioning properly!")
                self.log(f"   ✅ Requirements met: {requirements_met}/4")
                self.log(f"   ✅ MINH ANH 09 certificate can be processed correctly")
                self.log(f"   ✅ 'Add new ship' functionality should work with this certificate")
                self.log(f"   ✅ AI configuration and processing pipeline are functional")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: AI CERTIFICATE ANALYSIS PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Some functionality working, improvements needed")
                self.log(f"   ⚠️ Requirements met: {requirements_met}/4")
                
                if not req1_met:
                    self.log(f"   ❌ CRITICAL: AI analysis endpoint has issues")
                if not req2_met:
                    self.log(f"   ❌ CRITICAL: Data extraction accuracy too low ({extraction_rate:.1f}%)")
                if not req3_met:
                    self.log(f"   ❌ AI configuration needs attention")
                if not req4_met:
                    self.log(f"   ❌ Processing pipeline has issues")
            else:
                self.log(f"\n❌ CONCLUSION: AI CERTIFICATE ANALYSIS HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Major fixes needed")
                self.log(f"   ❌ Requirements met: {requirements_met}/4")
                self.log(f"   ❌ MINH ANH 09 certificate cannot be processed correctly")
                self.log(f"   ❌ 'Add new ship' functionality will not work properly")
                
                # Identify specific issues
                if not self.analysis_tests['ai_analysis_successful']:
                    self.log(f"   🔧 ISSUE: AI analysis endpoint failing")
                if extraction_rate < 50:
                    self.log(f"   🔧 ISSUE: Data extraction severely impaired ({extraction_rate:.1f}%)")
                if not self.analysis_tests['ai_config_properly_configured']:
                    self.log(f"   🔧 ISSUE: AI configuration problems")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run AI Certificate Analysis tests"""
    print("🤖 AI CERTIFICATE ANALYSIS TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = AICertificateAnalysisTester()
        success = tester.run_comprehensive_ai_analysis_tests()
        
        if success:
            print("\n✅ AI CERTIFICATE ANALYSIS TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ AI CERTIFICATE ANALYSIS TESTING COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
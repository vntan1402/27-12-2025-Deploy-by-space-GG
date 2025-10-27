#!/usr/bin/env python3
"""
Passport AI Field Extraction Testing - Maritime Document Analysis
FOCUS: Test the AI field extraction step specifically for passport analysis

REVIEW REQUEST REQUIREMENTS:
Test the extract_maritime_document_fields_from_summary function:

1. Check if the function is being called at all
2. Verify the summary text is not empty from Apps Script  
3. Test the Google Gen AI SDK integration with Emergent LLM key
4. Check if the extraction prompt is being created correctly
5. Test the API call to Google Gen AI
6. Validate the JSON parsing of the AI response

Use the endpoint: POST /api/crew/analyze-passport with:
- document_file: /app/Ho_chieu_pho_thong.jpg (real Vietnamese passport)
- document_type: passport  
- ship_name: TEST_SHIP

Check backend logs for:
- "AI field extraction" messages
- "extract_maritime_document_fields_from_summary" function calls
- Google Gen AI API errors
- Summary text length and content
- Any import errors for google.genai

The previous test showed Apps Script generates 2,283 character summary successfully, 
but the final analysis has empty passport fields, suggesting the AI extraction step is not working.
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
import subprocess
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

class PassportAIExtractionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for passport AI extraction testing
        self.passport_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'passport_file_exists': False,
            
            # AI Configuration checks
            'ai_config_accessible': False,
            'document_ai_enabled': False,
            'emergent_key_configured': False,
            'google_genai_import_available': False,
            
            # Endpoint accessibility
            'analyze_passport_endpoint_accessible': False,
            'multipart_form_data_accepted': False,
            
            # Document AI Summary Generation (Apps Script)
            'apps_script_called': False,
            'document_ai_summary_generated': False,
            'summary_text_not_empty': False,
            'summary_length_adequate': False,
            'summary_content_valid': False,
            
            # AI Field Extraction Function
            'extract_function_called': False,
            'extraction_prompt_created': False,
            'google_genai_client_initialized': False,
            'genai_api_call_made': False,
            'genai_api_call_successful': False,
            'ai_response_received': False,
            'ai_response_not_empty': False,
            'json_parsing_successful': False,
            'field_validation_successful': False,
            
            # Final Results
            'passport_fields_extracted': False,
            'confidence_score_calculated': False,
            'full_name_extracted': False,
            'passport_number_extracted': False,
            'processing_method_correct': False,
            'no_import_errors': False,
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
    
    def check_passport_file(self):
        """Check if the passport file exists"""
        try:
            self.log("📄 Checking passport file existence...")
            
            passport_path = "/app/Ho_chieu_pho_thong.jpg"
            
            if os.path.exists(passport_path):
                file_size = os.path.getsize(passport_path)
                self.log(f"✅ Passport file exists: {passport_path}")
                self.log(f"   File size: {file_size:,} bytes")
                self.passport_tests['passport_file_exists'] = True
                return True
            else:
                self.log(f"❌ Passport file not found: {passport_path}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking passport file: {str(e)}", "ERROR")
            return False
    
    def check_ai_configuration(self):
        """Check AI configuration for Document AI and Emergent key"""
        try:
            self.log("🤖 Checking AI configuration...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.passport_tests['ai_config_accessible'] = True
                self.log("✅ AI config endpoint accessible")
                
                try:
                    ai_config = response.json()
                    self.log(f"   AI Provider: {ai_config.get('provider', 'Not set')}")
                    self.log(f"   AI Model: {ai_config.get('model', 'Not set')}")
                    self.log(f"   Use Emergent Key: {ai_config.get('use_emergent_key', False)}")
                    
                    # Check Document AI configuration
                    document_ai = ai_config.get('document_ai', {})
                    if document_ai:
                        self.log(f"   Document AI Enabled: {document_ai.get('enabled', False)}")
                        self.log(f"   Project ID: {document_ai.get('project_id', 'Not set')}")
                        self.log(f"   Processor ID: {document_ai.get('processor_id', 'Not set')}")
                        self.log(f"   Apps Script URL: {'Set' if document_ai.get('apps_script_url') else 'Not set'}")
                        
                        if document_ai.get('enabled'):
                            self.passport_tests['document_ai_enabled'] = True
                    
                    if ai_config.get('use_emergent_key'):
                        self.passport_tests['emergent_key_configured'] = True
                    
                    return ai_config
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ AI config endpoint failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error checking AI configuration: {str(e)}", "ERROR")
            return None
    
    def test_google_genai_import(self):
        """Test if google.genai can be imported"""
        try:
            self.log("📦 Testing google.genai import availability...")
            
            # Try to import google.genai in a subprocess to avoid affecting current process
            try:
                result = subprocess.run([
                    sys.executable, '-c', 
                    'from google import genai; print("SUCCESS: google.genai imported"); print(f"Client available: {hasattr(genai, \"Client\")}")'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.log("✅ google.genai import successful")
                    self.log(f"   Output: {result.stdout.strip()}")
                    self.passport_tests['google_genai_import_available'] = True
                    return True
                else:
                    self.log(f"   ❌ google.genai import failed: {result.stderr.strip()}")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.log("   ❌ google.genai import test timed out")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing google.genai import: {str(e)}", "ERROR")
            return False
    
    def test_analyze_passport_endpoint(self):
        """Test the analyze passport endpoint with detailed logging"""
        try:
            self.log("🛂 Testing POST /api/crew/analyze-passport endpoint...")
            
            # Prepare the passport file
            passport_path = "/app/Ho_chieu_pho_thong.jpg"
            
            with open(passport_path, 'rb') as f:
                files = {
                    'passport_file': ('Ho_chieu_pho_thong.jpg', f, 'image/jpeg')
                }
                data = {
                    'ship_name': 'TEST_SHIP'
                }
                
                endpoint = f"{BACKEND_URL}/crew/analyze-passport"
                self.log(f"   POST {endpoint}")
                self.log(f"   Ship name: TEST_SHIP")
                self.log(f"   File: Ho_chieu_pho_thong.jpg")
                
                # Make the request with detailed monitoring
                self.log("   📡 Sending request to backend...")
                response = requests.post(
                    endpoint, 
                    files=files, 
                    data=data, 
                    headers=self.get_headers(), 
                    timeout=120  # Longer timeout for AI processing
                )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.passport_tests['analyze_passport_endpoint_accessible'] = True
                    self.passport_tests['multipart_form_data_accepted'] = True
                    self.log("✅ Analyze passport endpoint accessible")
                    
                    try:
                        response_data = response.json()
                        self.log("✅ Valid JSON response received")
                        
                        # Analyze the response structure
                        self.analyze_response_data(response_data)
                        
                        return response_data
                        
                    except json.JSONDecodeError as e:
                        self.log(f"   ❌ Invalid JSON response: {str(e)}")
                        self.log(f"   Raw response: {response.text[:500]}")
                        return None
                        
                elif response.status_code == 404:
                    self.log("   ❌ Endpoint not found (404) - AI configuration may be missing")
                    try:
                        error_data = response.json()
                        self.log(f"   Error detail: {error_data.get('detail', 'Unknown error')}")
                    except:
                        pass
                    return None
                    
                else:
                    self.log(f"   ❌ Analyze passport endpoint failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"   Error: {response.text[:200]}")
                    return None
                    
        except Exception as e:
            self.log(f"❌ Error testing analyze passport endpoint: {str(e)}", "ERROR")
            return None
    
    def analyze_response_data(self, response_data):
        """Analyze the response data to check AI extraction results"""
        try:
            self.log("🔍 Analyzing response data...")
            
            # Check if we have extracted fields
            full_name = response_data.get('full_name')
            passport_number = response_data.get('passport_number')
            confidence_score = response_data.get('confidence_score')
            processing_method = response_data.get('processing_method')
            
            self.log(f"   Full Name: '{full_name}'")
            self.log(f"   Passport Number: '{passport_number}'")
            self.log(f"   Confidence Score: {confidence_score}")
            self.log(f"   Processing Method: '{processing_method}'")
            
            # Check if AI extraction worked
            if full_name and full_name.strip():
                self.passport_tests['full_name_extracted'] = True
                self.log("   ✅ Full name extracted successfully")
            else:
                self.log("   ❌ Full name not extracted or empty")
            
            if passport_number and passport_number.strip():
                self.passport_tests['passport_number_extracted'] = True
                self.log("   ✅ Passport number extracted successfully")
            else:
                self.log("   ❌ Passport number not extracted or empty")
            
            if confidence_score is not None and confidence_score > 0:
                self.passport_tests['confidence_score_calculated'] = True
                self.log(f"   ✅ Confidence score calculated: {confidence_score}")
            else:
                self.log("   ❌ Confidence score not calculated or zero")
            
            if processing_method == "summary_to_ai_extraction":
                self.passport_tests['processing_method_correct'] = True
                self.log("   ✅ Processing method indicates AI extraction was used")
            elif processing_method == "summary_only":
                self.log("   ⚠️ Processing method indicates AI extraction failed, only summary available")
            else:
                self.log(f"   ⚠️ Unknown processing method: {processing_method}")
            
            # Overall assessment
            if full_name and passport_number and confidence_score:
                self.passport_tests['passport_fields_extracted'] = True
                self.log("   ✅ Overall: Passport fields successfully extracted")
            else:
                self.log("   ❌ Overall: Passport field extraction failed or incomplete")
            
            # Check for raw summary (indicates AI extraction failed)
            raw_summary = response_data.get('raw_summary')
            if raw_summary:
                self.log(f"   📝 Raw summary available ({len(raw_summary)} chars) - AI extraction may have failed")
                self.passport_tests['summary_text_not_empty'] = True
                if len(raw_summary) > 100:
                    self.passport_tests['summary_length_adequate'] = True
                    if len(raw_summary) > 2000:  # Based on review request: 2,283 characters
                        self.passport_tests['summary_content_valid'] = True
                        self.log(f"   ✅ Summary length matches expected: {len(raw_summary)} chars (expected ~2,283)")
            
        except Exception as e:
            self.log(f"❌ Error analyzing response data: {str(e)}", "ERROR")
    
    def check_backend_logs(self):
        """Check backend logs for AI extraction messages"""
        try:
            self.log("📋 Checking backend logs for AI extraction messages...")
            
            # Check supervisor logs for backend
            try:
                # Get recent backend logs
                result = subprocess.run(
                    ['tail', '-n', '200', '/var/log/supervisor/backend.err.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    log_content = result.stdout
                    self.log(f"   📄 Retrieved {len(log_content.splitlines())} log lines")
                    
                    # Search for specific AI extraction messages
                    ai_messages = [
                        "AI field extraction",
                        "extract_maritime_document_fields_from_summary",
                        "Google Gen AI",
                        "genai.Client",
                        "AI extraction response",
                        "Summary length:",
                        "Document AI summary generated",
                        "Apps Script response received",
                        "Using google gemini",
                        "extract passport fields from summary",
                        "AI field extraction completed",
                        "AI field extraction failed",
                        "Failed to parse",
                        "extraction JSON",
                        "No content in",
                        "AI extraction response",
                        "import error",
                        "ImportError"
                    ]
                    
                    found_messages = []
                    for line in log_content.splitlines():
                        for message in ai_messages:
                            if message.lower() in line.lower():
                                found_messages.append(line.strip())
                                break
                    
                    if found_messages:
                        self.log(f"   ✅ Found {len(found_messages)} relevant AI extraction log messages:")
                        for msg in found_messages[-15:]:  # Show last 15 messages
                            self.log(f"      📝 {msg}")
                        
                        # Check for specific indicators
                        log_text = log_content.lower()
                        
                        if "extract_maritime_document_fields_from_summary" in log_text:
                            self.passport_tests['extract_function_called'] = True
                            self.log("   ✅ extract_maritime_document_fields_from_summary function was called")
                        
                        if "document ai summary generated" in log_text:
                            self.passport_tests['document_ai_summary_generated'] = True
                            self.log("   ✅ Document AI summary was generated")
                        
                        if "summary length:" in log_text:
                            self.passport_tests['summary_text_not_empty'] = True
                            self.log("   ✅ Summary text was not empty")
                        
                        if "apps script response received" in log_text:
                            self.passport_tests['apps_script_called'] = True
                            self.log("   ✅ Apps Script was called successfully")
                        
                        if "genai.client" in log_text or "google gen ai" in log_text:
                            self.passport_tests['google_genai_client_initialized'] = True
                            self.log("   ✅ Google Gen AI client was initialized")
                        
                        if "ai extraction response" in log_text:
                            self.passport_tests['ai_response_received'] = True
                            self.log("   ✅ AI extraction response was received")
                        
                        if "extract passport fields from summary" in log_text:
                            self.passport_tests['genai_api_call_made'] = True
                            self.log("   ✅ Gen AI API call was made")
                        
                        if "ai field extraction completed" in log_text:
                            self.passport_tests['genai_api_call_successful'] = True
                            self.log("   ✅ AI field extraction completed successfully")
                        
                        if "failed to parse" in log_text and "extraction json" in log_text:
                            self.log("   ❌ JSON parsing failed - AI response format issue")
                        
                        if "no content in" in log_text and "ai extraction response" in log_text:
                            self.log("   ❌ AI extraction returned no content")
                        
                        if "import error" in log_text or "importerror" in log_text:
                            self.log("   ❌ Import error detected - google.genai may not be available")
                        else:
                            self.passport_tests['no_import_errors'] = True
                            self.log("   ✅ No import errors detected")
                    
                    else:
                        self.log("   ⚠️ No relevant AI extraction messages found in logs")
                
                else:
                    self.log(f"   ⚠️ Failed to retrieve backend logs: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.log("   ⚠️ Timeout retrieving backend logs")
            except Exception as e:
                self.log(f"   ⚠️ Error retrieving backend logs: {str(e)}")
                
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def run_comprehensive_passport_ai_test(self):
        """Run comprehensive test of passport AI field extraction functionality"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE PASSPORT AI FIELD EXTRACTION TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Check passport file
            self.log("\nSTEP 2: Check passport file existence")
            if not self.check_passport_file():
                self.log("❌ CRITICAL: Passport file not found - cannot proceed")
                return False
            
            # Step 3: Check AI configuration
            self.log("\nSTEP 3: Check AI configuration")
            ai_config = self.check_ai_configuration()
            if not ai_config:
                self.log("❌ WARNING: AI configuration not accessible")
            
            # Step 4: Test Google Gen AI import
            self.log("\nSTEP 4: Test Google Gen AI import")
            self.test_google_genai_import()
            
            # Step 5: Test analyze passport endpoint
            self.log("\nSTEP 5: Test analyze passport endpoint")
            response_data = self.test_analyze_passport_endpoint()
            
            # Step 6: Check backend logs
            self.log("\nSTEP 6: Check backend logs for AI extraction messages")
            self.check_backend_logs()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE PASSPORT AI FIELD EXTRACTION TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 PASSPORT AI FIELD EXTRACTION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.passport_tests)
            passed_tests = sum(1 for result in self.passport_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('passport_file_exists', 'Passport file exists'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # AI Configuration Results
            self.log("\n🤖 AI CONFIGURATION:")
            config_tests = [
                ('ai_config_accessible', 'AI config endpoint accessible'),
                ('document_ai_enabled', 'Document AI enabled'),
                ('emergent_key_configured', 'Emergent key configured'),
                ('google_genai_import_available', 'Google Gen AI import available'),
                ('no_import_errors', 'No import errors detected'),
            ]
            
            for test_key, description in config_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Endpoint Accessibility Results
            self.log("\n🛂 ENDPOINT ACCESSIBILITY:")
            endpoint_tests = [
                ('analyze_passport_endpoint_accessible', 'Analyze passport endpoint accessible'),
                ('multipart_form_data_accepted', 'Multipart form data accepted'),
            ]
            
            for test_key, description in endpoint_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Document AI Summary Results
            self.log("\n📄 DOCUMENT AI SUMMARY GENERATION:")
            summary_tests = [
                ('apps_script_called', 'Apps Script called successfully'),
                ('document_ai_summary_generated', 'Document AI summary generated'),
                ('summary_text_not_empty', 'Summary text not empty'),
                ('summary_length_adequate', 'Summary length adequate (>100 chars)'),
                ('summary_content_valid', 'Summary content valid (~2,283 chars)'),
            ]
            
            for test_key, description in summary_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # AI Field Extraction Results
            self.log("\n🧠 AI FIELD EXTRACTION FUNCTION:")
            extraction_tests = [
                ('extract_function_called', 'extract_maritime_document_fields_from_summary called'),
                ('extraction_prompt_created', 'Extraction prompt created'),
                ('google_genai_client_initialized', 'Google Gen AI client initialized'),
                ('genai_api_call_made', 'Gen AI API call made'),
                ('genai_api_call_successful', 'Gen AI API call successful'),
                ('ai_response_received', 'AI response received'),
                ('ai_response_not_empty', 'AI response not empty'),
                ('json_parsing_successful', 'JSON parsing successful'),
                ('field_validation_successful', 'Field validation successful'),
            ]
            
            for test_key, description in extraction_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Final Results
            self.log("\n🎯 FINAL EXTRACTION RESULTS:")
            result_tests = [
                ('passport_fields_extracted', 'Passport fields extracted'),
                ('confidence_score_calculated', 'Confidence score calculated'),
                ('full_name_extracted', 'Full name extracted'),
                ('passport_number_extracted', 'Passport number extracted'),
                ('processing_method_correct', 'Processing method correct'),
            ]
            
            for test_key, description in result_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🔍 OVERALL ASSESSMENT:")
            
            # Check critical path
            critical_tests = [
                'analyze_passport_endpoint_accessible',
                'document_ai_summary_generated', 
                'extract_function_called',
                'passport_fields_extracted'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.passport_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ PASSPORT AI FIELD EXTRACTION IS WORKING END-TO-END")
                self.log("   ✅ Document AI summary generation working")
                self.log("   ✅ AI field extraction function working")
                self.log("   ✅ Passport fields successfully extracted")
            else:
                self.log("   ❌ PASSPORT AI FIELD EXTRACTION HAS ISSUES")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical steps working")
                
                # Identify the failure point
                if not self.passport_tests.get('analyze_passport_endpoint_accessible'):
                    self.log("   🔍 ISSUE: Endpoint not accessible - check AI configuration")
                elif not self.passport_tests.get('document_ai_summary_generated'):
                    self.log("   🔍 ISSUE: Document AI summary generation failing")
                    self.log("   🔧 RECOMMENDATION: Check Apps Script and Document AI configuration")
                elif not self.passport_tests.get('extract_function_called'):
                    self.log("   🔍 ISSUE: AI extraction function not being called")
                    self.log("   🔧 RECOMMENDATION: Check backend code flow and AI configuration")
                elif not self.passport_tests.get('passport_fields_extracted'):
                    self.log("   🔍 ISSUE: AI extraction function called but fields not extracted")
                    self.log("   🔧 RECOMMENDATION: Check Google Gen AI SDK integration and API calls")
                    
                    # More specific diagnostics
                    if not self.passport_tests.get('google_genai_import_available'):
                        self.log("   🔧 SPECIFIC: google.genai import not available - install Google Gen AI SDK")
                    elif not self.passport_tests.get('genai_api_call_made'):
                        self.log("   🔧 SPECIFIC: Gen AI API call not made - check Emergent LLM key")
                    elif not self.passport_tests.get('ai_response_received'):
                        self.log("   🔧 SPECIFIC: No AI response received - check API connectivity")
                    elif not self.passport_tests.get('json_parsing_successful'):
                        self.log("   🔧 SPECIFIC: JSON parsing failed - check AI response format")
            
            if success_rate >= 80:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            # Summary of findings
            self.log("\n📋 KEY FINDINGS:")
            if self.passport_tests.get('summary_content_valid') and not self.passport_tests.get('passport_fields_extracted'):
                self.log("   🔍 CONFIRMED: Apps Script generates adequate summary (~2,283 chars)")
                self.log("   🔍 CONFIRMED: AI field extraction step is failing")
                self.log("   🔧 FOCUS: Debug extract_maritime_document_fields_from_summary function")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the passport AI extraction tests"""
    tester = PassportAIExtractionTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_passport_ai_test()
        
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
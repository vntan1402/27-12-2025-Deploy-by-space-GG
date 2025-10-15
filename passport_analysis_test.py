#!/usr/bin/env python3
"""
Passport Analysis Auto-fill Debug Test
FOCUS: Debug the passport analysis auto-fill issue by testing the exact response structure

PROBLEM DESCRIPTION:
- Frontend shows "Passport analysis successful! Information has been auto-filled" toast message
- But form fields remain empty (not auto-filled)
- This suggests backend returns success=true but analysis data is empty or incorrect structure

DEBUGGING REQUIREMENTS:
1. Test Passport Analysis Response Structure with specific file:
   https://customer-assets.emergentagent.com/job_d040008f-5aae-467d-90f4-4064c1b65ddd/artifacts/m027k3a2_PASS%20PORT%20Tran%20Trong%20Toan.pdf
2. Verify Analysis Data Content - check if response.data.analysis contains extracted information
3. Check Expected vs Actual Response - verify field names match frontend expectations
4. Verify Field Extraction - check if Document AI is extracting correct information
5. Check Apps Script Integration - verify backend is successfully calling Apps Script

CRITICAL FOCUS:
- The issue is that frontend receives success=true but cannot auto-fill form
- This means either analysis object is empty OR field names don't match
- Need exact response structure to debug the disconnect
"""

import requests
import json
import os
import sys
import tempfile
from datetime import datetime
import traceback

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://crew-cert-manager.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class PassportAnalysisDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for passport analysis debugging
        self.debug_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            
            # File Download and Preparation
            'passport_file_download_successful': False,
            'passport_file_prepared': False,
            
            # Passport Analysis Endpoint Testing
            'analyze_passport_endpoint_accessible': False,
            'analyze_passport_request_sent': False,
            'analyze_passport_response_received': False,
            'response_structure_logged': False,
            
            # Response Analysis
            'success_field_true': False,
            'analysis_object_present': False,
            'analysis_object_not_empty': False,
            'expected_fields_present': False,
            'field_names_match_frontend': False,
            
            # Data Content Verification
            'full_name_extracted': False,
            'passport_number_extracted': False,
            'date_of_birth_extracted': False,
            'place_of_birth_extracted': False,
            'sex_extracted': False,
            
            # Integration Verification
            'apps_script_integration_working': False,
            'document_ai_processing_working': False,
            'cache_busting_working': False,
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
                
                self.debug_tests['authentication_successful'] = True
                if self.current_user.get('company'):
                    self.debug_tests['user_company_identified'] = True
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
    
    def download_passport_file(self):
        """Download the specific passport file for testing"""
        try:
            self.log("📄 Downloading passport file for testing...")
            
            passport_url = "https://customer-assets.emergentagent.com/job_d040008f-5aae-467d-90f4-4064c1b65ddd/artifacts/m027k3a2_PASS%20PORT%20Tran%20Trong%20Toan.pdf"
            self.log(f"   Downloading from: {passport_url}")
            
            response = requests.get(passport_url, timeout=30)
            self.log(f"   Download response status: {response.status_code}")
            
            if response.status_code == 200:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name
                
                self.log(f"✅ Passport file downloaded successfully")
                self.log(f"   File size: {len(response.content)} bytes")
                self.log(f"   Temporary file: {temp_file_path}")
                
                self.debug_tests['passport_file_download_successful'] = True
                self.debug_tests['passport_file_prepared'] = True
                return temp_file_path
            else:
                self.log(f"   ❌ Failed to download passport file - Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error downloading passport file: {str(e)}", "ERROR")
            return None
    
    def test_analyze_passport_endpoint(self, passport_file_path):
        """Test the analyze-passport endpoint with the specific passport file"""
        try:
            self.log("🔍 Testing POST /api/crew/analyze-passport endpoint...")
            
            endpoint = f"{BACKEND_URL}/crew/analyze-passport"
            self.log(f"   POST {endpoint}")
            
            # Prepare multipart form data
            with open(passport_file_path, 'rb') as file:
                files = {
                    'passport_file': ('PASS_PORT_Tran_Trong_Toan.pdf', file, 'application/pdf')
                }
                
                # Add ship data as form data (matching frontend implementation)
                data = {
                    'ship_name': 'BROTHER 36',
                    'ship_id': 'test-ship-id',
                    'imo': '8743531'
                }
                
                self.log(f"   Ship data: {json.dumps(data, indent=2)}")
                self.log(f"   File: PASS_PORT_Tran_Trong_Toan.pdf")
                
                self.debug_tests['analyze_passport_endpoint_accessible'] = True
                self.debug_tests['analyze_passport_request_sent'] = True
                
                # Send request
                response = requests.post(
                    endpoint, 
                    files=files, 
                    data=data,
                    headers=self.get_headers(), 
                    timeout=120  # Longer timeout for file processing
                )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.debug_tests['analyze_passport_response_received'] = True
                    self.log("✅ Analyze passport endpoint responded successfully")
                    
                    try:
                        response_data = response.json()
                        self.debug_tests['response_structure_logged'] = True
                        
                        # Log COMPLETE response structure
                        self.log("📋 COMPLETE RESPONSE STRUCTURE:")
                        self.log("=" * 60)
                        self.log(json.dumps(response_data, indent=2, default=str))
                        self.log("=" * 60)
                        
                        # Analyze response structure
                        self.analyze_response_structure(response_data)
                        
                        return response_data
                        
                    except json.JSONDecodeError as e:
                        self.log(f"   ❌ Invalid JSON response: {str(e)}")
                        self.log(f"   Raw response: {response.text[:500]}")
                        return None
                        
                else:
                    self.log(f"   ❌ Analyze passport endpoint failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {json.dumps(error_data, indent=2)}")
                    except:
                        self.log(f"   Error: {response.text[:500]}")
                    return None
                    
        except Exception as e:
            self.log(f"❌ Error testing analyze passport endpoint: {str(e)}", "ERROR")
            traceback.print_exc()
            return None
    
    def analyze_response_structure(self, response_data):
        """Analyze the response structure in detail"""
        try:
            self.log("🔬 ANALYZING RESPONSE STRUCTURE...")
            
            # Check top-level structure
            self.log("📊 TOP-LEVEL FIELDS:")
            for key, value in response_data.items():
                value_type = type(value).__name__
                if isinstance(value, dict):
                    self.log(f"   {key}: {value_type} (keys: {list(value.keys())})")
                elif isinstance(value, list):
                    self.log(f"   {key}: {value_type} (length: {len(value)})")
                else:
                    self.log(f"   {key}: {value_type} = {value}")
            
            # Check success field
            success = response_data.get('success')
            self.log(f"\n✅ SUCCESS FIELD: {success}")
            if success:
                self.debug_tests['success_field_true'] = True
            
            # Check analysis data
            analysis = response_data.get('analysis')
            if analysis is not None:
                self.debug_tests['analysis_object_present'] = True
                self.log(f"\n📋 ANALYSIS DATA FOUND:")
                self.log(f"   Type: {type(analysis).__name__}")
                
                if isinstance(analysis, dict):
                    if analysis:  # Not empty
                        self.debug_tests['analysis_object_not_empty'] = True
                        self.log(f"   Keys: {list(analysis.keys())}")
                        
                        # Check expected fields that frontend expects
                        expected_fields = ['full_name', 'sex', 'date_of_birth', 'place_of_birth', 'passport_number']
                        self.log(f"\n🔍 CHECKING EXPECTED FIELDS:")
                        
                        fields_found = 0
                        for field in expected_fields:
                            if field in analysis:
                                value = analysis[field]
                                self.log(f"   ✅ {field}: {value}")
                                fields_found += 1
                                
                                # Mark specific field extractions
                                if field == 'full_name' and value:
                                    self.debug_tests['full_name_extracted'] = True
                                elif field == 'passport_number' and value:
                                    self.debug_tests['passport_number_extracted'] = True
                                elif field == 'date_of_birth' and value:
                                    self.debug_tests['date_of_birth_extracted'] = True
                                elif field == 'place_of_birth' and value:
                                    self.debug_tests['place_of_birth_extracted'] = True
                                elif field == 'sex' and value:
                                    self.debug_tests['sex_extracted'] = True
                            else:
                                self.log(f"   ❌ {field}: MISSING")
                        
                        if fields_found == len(expected_fields):
                            self.debug_tests['expected_fields_present'] = True
                            self.debug_tests['field_names_match_frontend'] = True
                            self.log(f"\n✅ ALL EXPECTED FIELDS PRESENT")
                        elif fields_found > 0:
                            self.log(f"\n⚠️ PARTIAL FIELDS PRESENT ({fields_found}/{len(expected_fields)})")
                        else:
                            self.log(f"\n❌ NO EXPECTED FIELDS FOUND")
                        
                        # Check for additional fields
                        additional_fields = set(analysis.keys()) - set(expected_fields)
                        if additional_fields:
                            self.log(f"\n📋 ADDITIONAL FIELDS FOUND:")
                            for field in additional_fields:
                                value = analysis[field]
                                self.log(f"   + {field}: {value}")
                    else:
                        self.log(f"   ❌ Analysis object is empty: {analysis}")
                
                else:
                    self.log(f"   ❌ Analysis is not a dictionary: {analysis}")
            else:
                self.log(f"\n❌ NO ANALYSIS DATA FOUND")
                self.log(f"   Analysis field value: {analysis}")
            
            # Check for other relevant fields
            other_fields = ['message', 'error', 'confidence_score', 'processing_time']
            self.log(f"\n📋 OTHER RELEVANT FIELDS:")
            for field in other_fields:
                if field in response_data:
                    value = response_data[field]
                    self.log(f"   {field}: {value}")
            
            # Check cache busting
            if 'cache_busted' in response_data or 'timestamp' in response_data:
                self.debug_tests['cache_busting_working'] = True
                self.log(f"\n✅ CACHE BUSTING DETECTED")
            
            # Check Apps Script integration indicators
            if 'apps_script_response' in response_data or 'document_ai_response' in response_data:
                self.debug_tests['apps_script_integration_working'] = True
                self.log(f"\n✅ APPS SCRIPT INTEGRATION DETECTED")
            
            # Check Document AI processing indicators
            if 'document_ai' in str(response_data).lower() or 'google' in str(response_data).lower():
                self.debug_tests['document_ai_processing_working'] = True
                self.log(f"\n✅ DOCUMENT AI PROCESSING DETECTED")
            
        except Exception as e:
            self.log(f"❌ Error analyzing response structure: {str(e)}", "ERROR")
    
    def cleanup_temp_files(self, file_paths):
        """Clean up temporary files"""
        try:
            for file_path in file_paths:
                if file_path and os.path.exists(file_path):
                    os.unlink(file_path)
                    self.log(f"🧹 Cleaned up temporary file: {file_path}")
        except Exception as e:
            self.log(f"⚠️ Error cleaning up temporary files: {str(e)}")
    
    def run_passport_analysis_debug_test(self):
        """Run comprehensive passport analysis debug test"""
        temp_files = []
        
        try:
            self.log("🚀 STARTING PASSPORT ANALYSIS AUTO-FILL DEBUG TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Download passport file
            self.log("\nSTEP 2: Download passport file")
            passport_file_path = self.download_passport_file()
            if not passport_file_path:
                self.log("❌ CRITICAL: Failed to download passport file")
                return False
            temp_files.append(passport_file_path)
            
            # Step 3: Test analyze-passport endpoint
            self.log("\nSTEP 3: Test analyze-passport endpoint with exact file")
            response_data = self.test_analyze_passport_endpoint(passport_file_path)
            if not response_data:
                self.log("❌ CRITICAL: Analyze passport endpoint failed")
                return False
            
            self.log("\n" + "=" * 80)
            self.log("✅ PASSPORT ANALYSIS DEBUG TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in debug test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
        finally:
            # Cleanup temporary files
            self.cleanup_temp_files(temp_files)
    
    def print_debug_summary(self):
        """Print comprehensive summary of debug results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 PASSPORT ANALYSIS AUTO-FILL DEBUG SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.debug_tests)
            passed_tests = sum(1 for result in self.debug_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # File Preparation Results
            self.log("\n📄 FILE PREPARATION:")
            file_tests = [
                ('passport_file_download_successful', 'Passport file download successful'),
                ('passport_file_prepared', 'Passport file prepared for testing'),
            ]
            
            for test_key, description in file_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Endpoint Testing Results
            self.log("\n🔍 ENDPOINT TESTING:")
            endpoint_tests = [
                ('analyze_passport_endpoint_accessible', 'Analyze passport endpoint accessible'),
                ('analyze_passport_request_sent', 'Analyze passport request sent'),
                ('analyze_passport_response_received', 'Analyze passport response received'),
                ('response_structure_logged', 'Response structure logged'),
            ]
            
            for test_key, description in endpoint_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Response Analysis Results
            self.log("\n📋 RESPONSE ANALYSIS:")
            response_tests = [
                ('success_field_true', 'Success field is true'),
                ('analysis_object_present', 'Analysis object present'),
                ('analysis_object_not_empty', 'Analysis object not empty'),
                ('expected_fields_present', 'Expected fields present'),
                ('field_names_match_frontend', 'Field names match frontend'),
            ]
            
            for test_key, description in response_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Data Extraction Results
            self.log("\n📊 DATA EXTRACTION:")
            extraction_tests = [
                ('full_name_extracted', 'Full name extracted'),
                ('passport_number_extracted', 'Passport number extracted'),
                ('date_of_birth_extracted', 'Date of birth extracted'),
                ('place_of_birth_extracted', 'Place of birth extracted'),
                ('sex_extracted', 'Sex extracted'),
            ]
            
            for test_key, description in extraction_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Integration Results
            self.log("\n🔗 INTEGRATION:")
            integration_tests = [
                ('apps_script_integration_working', 'Apps Script integration working'),
                ('document_ai_processing_working', 'Document AI processing working'),
                ('cache_busting_working', 'Cache busting working'),
            ]
            
            for test_key, description in integration_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Analysis
            self.log("\n🎯 CRITICAL ANALYSIS:")
            
            if self.debug_tests.get('analyze_passport_response_received', False):
                if self.debug_tests.get('success_field_true', False):
                    if self.debug_tests.get('analysis_object_present', False):
                        if self.debug_tests.get('analysis_object_not_empty', False):
                            if self.debug_tests.get('field_names_match_frontend', False):
                                self.log("   ✅ RESPONSE STRUCTURE APPEARS CORRECT")
                                self.log("   ✅ Analysis data contains expected fields")
                                self.log("   ➡️ Issue may be in frontend form auto-fill logic")
                                self.log("   ➡️ Check frontend JavaScript for form population")
                            else:
                                self.log("   ❌ FIELD NAMES DON'T MATCH FRONTEND EXPECTATIONS")
                                self.log("   ➡️ This is likely the root cause of auto-fill failure")
                                self.log("   ➡️ Backend returns different field names than frontend expects")
                        else:
                            self.log("   ❌ ANALYSIS OBJECT IS EMPTY")
                            self.log("   ➡️ This is likely the root cause of auto-fill failure")
                            self.log("   ➡️ Document AI is not extracting data properly")
                    else:
                        self.log("   ❌ ANALYSIS OBJECT IS MISSING")
                        self.log("   ➡️ This is likely the root cause of auto-fill failure")
                        self.log("   ➡️ Backend response structure is incorrect")
                else:
                    self.log("   ❌ SUCCESS FIELD IS FALSE")
                    self.log("   ➡️ Backend is returning failure but frontend shows success")
                    self.log("   ➡️ Check frontend error handling logic")
            else:
                self.log("   ❌ ANALYZE PASSPORT ENDPOINT NOT RESPONDING")
                self.log("   ➡️ Backend integration issue")
                self.log("   ➡️ Check backend logs and configuration")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing debug summary: {str(e)}", "ERROR")

def main():
    """Main function to run the passport analysis debug test"""
    debugger = PassportAnalysisDebugger()
    
    try:
        # Run debug test
        success = debugger.run_passport_analysis_debug_test()
        
        # Print summary
        debugger.print_debug_summary()
        
        # Return appropriate exit code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        debugger.log("\n❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        debugger.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
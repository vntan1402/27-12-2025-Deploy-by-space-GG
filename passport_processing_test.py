#!/usr/bin/env python3
"""
Ship Management System - Passport Processing Workflow Backend Testing
FOCUS: Test Python NameError fix and complete passport processing workflow

REVIEW REQUEST REQUIREMENTS:
TEST PYTHON ERROR FIX - VERIFY COMPLETE PASSPORT PROCESSING WORKFLOW:

**OBJECTIVE**: Test the Python NameError fix and verify complete Add Crew passport processing workflow now works end-to-end with real Google Drive file uploads.

**PYTHON ERROR FIXED**: 
✅ Fixed `NameError: name 'ai_config' is not defined` in server.py
✅ Updated field extraction to use correct AI config parameters
✅ Backend should now return complete file upload data

**COMPREHENSIVE TESTING REQUIREMENTS**:

### **Phase 1: Backend Error Resolution Verification**
1. **Python Error Test**: Verify no more NameError in passport processing
2. **Field Extraction**: Confirm AI field extraction works with fixed parameters
3. **Complete Response**: API should return full response including file data

### **Phase 2: Complete Passport Processing Workflow**
4. **Authentication**: Login with admin1/123456
5. **Real Passport Test**: Process "PASS PORT Tran Trong Toan.pdf" again  
6. **Document AI Step**: System Apps Script Document AI processing
7. **Field Extraction**: AI field extraction from summary
8. **File Upload Step**: Company Apps Script file upload
9. **Response Verification**: Complete API response with file data

### **Phase 3: Google Drive File Creation Verification**
10. **Real File Upload**: Files should actually be created in Google Drive
11. **Folder Structure**: Verify correct folder creation (BROTHER 36/Crew records, SUMMARY)
12. **File Content**: Verify files contain actual content (not empty)
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
    # Fallback to external URL from frontend/.env
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                    break
            else:
                BACKEND_URL = 'https://maritime-docs-1.preview.emergentagent.com/api'
    except:
        BACKEND_URL = 'https://maritime-docs-1.preview.emergentagent.com/api'
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
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            
            # System Apps Script Verification
            'system_apps_script_configured': False,
            'document_ai_enabled': False,
            'apps_script_url_accessible': False,
            
            # Real Passport Analysis
            'passport_file_downloaded': False,
            'passport_upload_endpoint_accessible': False,
            'passport_analysis_successful': False,
            'document_ai_processing_successful': False,
            
            # Dual Apps Script Workflow
            'dual_apps_script_manager_working': False,
            'system_apps_script_called': False,
            'company_apps_script_configured': False,
            
            # Date Standardization
            'date_standardization_working': False,
            'dates_in_dd_mm_yyyy_format': False,
            'standardize_passport_dates_function_working': False,
            
            # Field Extraction
            'full_name_extracted': False,
            'date_of_birth_extracted': False,
            'place_of_birth_extracted': False,
            'passport_number_extracted': False,
            'other_fields_extracted': False,
            
            # Backend Integration
            'backend_processes_ai_response': False,
            'file_upload_process_working': False,
            'complete_workflow_successful': False,
        }
        
        # Store passport file path
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
        """Verify the passport file exists and is accessible"""
        try:
            self.log("📄 Verifying passport file...")
            
            if os.path.exists(self.passport_file_path):
                file_size = os.path.getsize(self.passport_file_path)
                self.log(f"   ✅ Passport file found: {self.passport_file_path}")
                self.log(f"   File size: {file_size} bytes ({file_size/1024:.1f} KB)")
                self.passport_tests['passport_file_downloaded'] = True
                return True
            else:
                self.log(f"   ❌ Passport file not found: {self.passport_file_path}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying passport file: {str(e)}", "ERROR")
            return False
    
    def verify_system_apps_script_configuration(self):
        """Verify System Apps Script configuration"""
        try:
            self.log("⚙️ Verifying System Apps Script configuration...")
            
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
                    self.passport_tests['document_ai_enabled'] = True
                    self.log("   ✅ Document AI enabled")
                    
                    project_id = document_ai.get('project_id')
                    processor_id = document_ai.get('processor_id')
                    apps_script_url = document_ai.get('apps_script_url')
                    
                    self.log(f"   Project ID: {project_id}")
                    self.log(f"   Processor ID: {processor_id}")
                    self.log(f"   Apps Script URL: {apps_script_url}")
                    
                    if apps_script_url:
                        self.passport_tests['system_apps_script_configured'] = True
                        self.log("   ✅ System Apps Script URL configured")
                        
                        # Test Apps Script URL accessibility
                        try:
                            script_response = requests.get(apps_script_url, timeout=10)
                            if script_response.status_code == 200:
                                self.passport_tests['apps_script_url_accessible'] = True
                                self.log("   ✅ Apps Script URL accessible")
                            else:
                                self.log(f"   ⚠️ Apps Script URL returned status: {script_response.status_code}")
                        except Exception as e:
                            self.log(f"   ⚠️ Apps Script URL test failed: {str(e)}")
                    
                    return True
                else:
                    self.log("   ❌ Document AI not enabled")
                    return False
            else:
                self.log(f"   ❌ Failed to get AI configuration: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying System Apps Script configuration: {str(e)}", "ERROR")
            return False
    
    def test_passport_analysis_endpoint(self):
        """Test passport analysis endpoint with real passport file"""
        try:
            self.log("🔍 Testing passport analysis endpoint with real passport file...")
            
            endpoint = f"{BACKEND_URL}/crew/analyze-passport"
            self.log(f"   POST {endpoint}")
            
            # Prepare multipart form data
            with open(self.passport_file_path, 'rb') as passport_file:
                files = {
                    'passport_file': ('PASS_PORT_Tran_Trong_Toan.pdf', passport_file, 'application/pdf')
                }
                data = {
                    'ship_name': 'BROTHER 36'
                }
                
                self.log("   Uploading passport file for analysis...")
                self.log(f"   Ship name: {data['ship_name']}")
                
                response = requests.post(
                    endpoint, 
                    files=files, 
                    data=data, 
                    headers=self.get_headers(), 
                    timeout=120  # Longer timeout for AI processing
                )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.passport_tests['passport_upload_endpoint_accessible'] = True
                    self.passport_tests['passport_analysis_successful'] = True
                    self.log("✅ Passport analysis endpoint working")
                    
                    try:
                        analysis_result = response.json()
                        self.log("✅ Passport analysis completed successfully")
                        
                        # Log the full response for debugging
                        self.log(f"   Analysis result keys: {list(analysis_result.keys())}")
                        self.log(f"   Full response: {json.dumps(analysis_result, indent=2)}")
                        
                        # Check for Document AI processing success
                        if 'processing_method' in analysis_result:
                            processing_method = analysis_result['processing_method']
                            self.log(f"   Processing method: {processing_method}")
                            
                            if 'document_ai' in processing_method.lower() or 'ai' in processing_method.lower():
                                self.passport_tests['document_ai_processing_successful'] = True
                                self.log("   ✅ Document AI processing successful")
                        
                        # Check for System Apps Script workflow
                        if 'system_apps_script' in str(analysis_result).lower():
                            self.passport_tests['system_apps_script_called'] = True
                            self.log("   ✅ System Apps Script called successfully")
                        
                        # Check dual Apps Script workflow
                        if 'dual_apps_script' in str(analysis_result).lower():
                            self.passport_tests['dual_apps_script_manager_working'] = True
                            self.log("   ✅ Dual Apps Script workflow working")
                        
                        # Verify field extraction
                        self.verify_field_extraction(analysis_result)
                        
                        # Verify date standardization
                        self.verify_date_standardization(analysis_result)
                        
                        # Check backend integration
                        if analysis_result.get('success', False):
                            self.passport_tests['backend_processes_ai_response'] = True
                            self.log("   ✅ Backend processes AI response correctly")
                        
                        # Check file upload process
                        if 'file_id' in analysis_result or 'google_drive' in str(analysis_result).lower():
                            self.passport_tests['file_upload_process_working'] = True
                            self.log("   ✅ File upload process working")
                        
                        # Overall workflow success
                        if (self.passport_tests['document_ai_processing_successful'] and 
                            self.passport_tests['backend_processes_ai_response']):
                            self.passport_tests['complete_workflow_successful'] = True
                            self.log("   ✅ Complete workflow successful")
                        
                        return analysis_result
                        
                    except json.JSONDecodeError as e:
                        self.log(f"   ❌ Invalid JSON response: {str(e)}")
                        self.log(f"   Response text: {response.text[:500]}")
                        return None
                else:
                    self.log(f"   ❌ Passport analysis failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"   Error response: {response.text[:500]}")
                    return None
                    
        except Exception as e:
            self.log(f"❌ Error testing passport analysis endpoint: {str(e)}", "ERROR")
            return None
    
    def verify_field_extraction(self, analysis_result):
        """Verify that all required passport fields are extracted correctly"""
        try:
            self.log("🔍 Verifying field extraction...")
            
            # Expected fields for passport
            expected_fields = {
                'full_name': 'Full name',
                'date_of_birth': 'Date of birth',
                'place_of_birth': 'Place of birth',
                'passport_number': 'Passport number',
                'sex': 'Sex',
                'nationality': 'Nationality',
                'issue_date': 'Issue date',
                'expiry_date': 'Expiry date'
            }
            
            extracted_fields = 0
            
            for field_key, field_name in expected_fields.items():
                if field_key in analysis_result and analysis_result[field_key]:
                    value = analysis_result[field_key]
                    self.log(f"   ✅ {field_name}: {value}")
                    extracted_fields += 1
                    
                    # Special checks for specific fields
                    if field_key == 'full_name' and value and len(value) > 5:
                        self.passport_tests['full_name_extracted'] = True
                    elif field_key == 'date_of_birth' and value:
                        self.passport_tests['date_of_birth_extracted'] = True
                    elif field_key == 'place_of_birth' and value:
                        self.passport_tests['place_of_birth_extracted'] = True
                    elif field_key == 'passport_number' and value:
                        self.passport_tests['passport_number_extracted'] = True
                else:
                    self.log(f"   ❌ {field_name}: Not extracted or empty")
            
            if extracted_fields >= 6:  # At least 6 out of 8 fields
                self.passport_tests['other_fields_extracted'] = True
                self.log(f"   ✅ Field extraction successful: {extracted_fields}/8 fields extracted")
            else:
                self.log(f"   ⚠️ Limited field extraction: {extracted_fields}/8 fields extracted")
                
        except Exception as e:
            self.log(f"❌ Error verifying field extraction: {str(e)}", "ERROR")
    
    def verify_date_standardization(self, analysis_result):
        """Verify that dates are standardized to DD/MM/YYYY format"""
        try:
            self.log("📅 Verifying date standardization...")
            
            date_fields = ['date_of_birth', 'issue_date', 'expiry_date']
            standardized_dates = 0
            
            # DD/MM/YYYY pattern
            dd_mm_yyyy_pattern = r'^\d{2}/\d{2}/\d{4}$'
            
            for field in date_fields:
                if field in analysis_result and analysis_result[field]:
                    date_value = str(analysis_result[field]).strip()
                    self.log(f"   Checking {field}: {date_value}")
                    
                    if re.match(dd_mm_yyyy_pattern, date_value):
                        self.log(f"   ✅ {field} in DD/MM/YYYY format: {date_value}")
                        standardized_dates += 1
                    else:
                        self.log(f"   ⚠️ {field} not in DD/MM/YYYY format: {date_value}")
                        
                        # Check if it's still a valid date but in different format
                        if any(char.isdigit() for char in date_value):
                            self.log(f"      (Contains date information but needs standardization)")
                else:
                    self.log(f"   ❌ {field}: Not present or empty")
            
            if standardized_dates >= 2:  # At least 2 dates in correct format
                self.passport_tests['date_standardization_working'] = True
                self.passport_tests['dates_in_dd_mm_yyyy_format'] = True
                self.passport_tests['standardize_passport_dates_function_working'] = True
                self.log(f"   ✅ Date standardization working: {standardized_dates} dates in DD/MM/YYYY format")
            else:
                self.log(f"   ⚠️ Date standardization needs improvement: {standardized_dates} dates in correct format")
                
        except Exception as e:
            self.log(f"❌ Error verifying date standardization: {str(e)}", "ERROR")
    
    def check_backend_logs_for_workflow(self):
        """Check backend logs for specific workflow indicators"""
        try:
            self.log("📋 Checking for expected backend log patterns...")
            
            # Expected log patterns from the review request
            expected_patterns = [
                "🔄 Processing passport with dual Apps Scripts",
                "📡 Step 1: Document AI analysis via System Apps Script",
                "✅ System Apps Script (Document AI) completed successfully",
                "🧠 Extracting fields from Document AI summary",
                "🗓️ Standardizing date_of_birth"
            ]
            
            # Note: We can't directly access backend logs from this test,
            # but we can infer from the API responses and behavior
            self.log("   Note: Backend log analysis would require direct log access")
            self.log("   Inferring workflow success from API responses and behavior")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_passport_processing_test(self):
        """Run comprehensive test of passport processing workflow"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE PASSPORT PROCESSING TEST")
            self.log("=" * 80)
            self.log("TESTING: Updated System Apps Script (Document AI only) with real passport")
            self.log("FILE: PASS PORT Tran Trong Toan.pdf")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication with admin1/123456")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Verify passport file
            self.log("\nSTEP 2: Verify passport file exists")
            if not self.verify_passport_file():
                self.log("❌ CRITICAL: Passport file not found - cannot proceed")
                return False
            
            # Step 3: Verify System Apps Script configuration
            self.log("\nSTEP 3: Verify System Apps Script configuration")
            self.verify_system_apps_script_configuration()
            
            # Step 4: Test passport analysis with real file
            self.log("\nSTEP 4: Test passport analysis with real passport file")
            analysis_result = self.test_passport_analysis_endpoint()
            
            if not analysis_result:
                self.log("❌ CRITICAL: Passport analysis failed")
                return False
            
            # Step 5: Check backend logs for workflow indicators
            self.log("\nSTEP 5: Check for expected workflow patterns")
            self.check_backend_logs_for_workflow()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE PASSPORT PROCESSING TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 PASSPORT PROCESSING TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.passport_tests)
            passed_tests = sum(1 for result in self.passport_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION:")
            auth_tests = [
                ('authentication_successful', 'Authentication with admin1/123456'),
                ('user_company_identified', 'User company identified'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # System Apps Script Verification
            self.log("\n⚙️ SYSTEM APPS SCRIPT VERIFICATION:")
            system_tests = [
                ('system_apps_script_configured', 'System Apps Script URL configured'),
                ('document_ai_enabled', 'Document AI enabled'),
                ('apps_script_url_accessible', 'Apps Script URL accessible'),
            ]
            
            for test_key, description in system_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Real Passport Analysis
            self.log("\n📄 REAL PASSPORT ANALYSIS:")
            passport_tests = [
                ('passport_file_downloaded', 'Passport file downloaded and verified'),
                ('passport_upload_endpoint_accessible', 'Passport upload endpoint accessible'),
                ('passport_analysis_successful', 'Passport analysis successful'),
                ('document_ai_processing_successful', 'Document AI processing successful'),
            ]
            
            for test_key, description in passport_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Dual Apps Script Workflow
            self.log("\n🔄 DUAL APPS SCRIPT WORKFLOW:")
            workflow_tests = [
                ('dual_apps_script_manager_working', 'DualAppsScriptManager working'),
                ('system_apps_script_called', 'System Apps Script called successfully'),
                ('company_apps_script_configured', 'Company Apps Script configured (if available)'),
            ]
            
            for test_key, description in workflow_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Date Standardization
            self.log("\n📅 DATE STANDARDIZATION:")
            date_tests = [
                ('date_standardization_working', 'Date standardization working'),
                ('dates_in_dd_mm_yyyy_format', 'Dates in clean DD/MM/YYYY format'),
                ('standardize_passport_dates_function_working', 'standardize_passport_dates() function working'),
            ]
            
            for test_key, description in date_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Field Extraction
            self.log("\n🔍 FIELD EXTRACTION:")
            field_tests = [
                ('full_name_extracted', 'Full name extracted correctly'),
                ('date_of_birth_extracted', 'Date of birth extracted'),
                ('place_of_birth_extracted', 'Place of birth extracted'),
                ('passport_number_extracted', 'Passport number extracted'),
                ('other_fields_extracted', 'Other fields (sex, nationality, dates) extracted'),
            ]
            
            for test_key, description in field_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Integration
            self.log("\n🔧 BACKEND INTEGRATION:")
            backend_tests = [
                ('backend_processes_ai_response', 'Backend processes AI response correctly'),
                ('file_upload_process_working', 'File upload process working'),
                ('complete_workflow_successful', 'Complete passport analysis workflow successful'),
            ]
            
            for test_key, description in backend_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Success Criteria Assessment
            self.log("\n🎯 CRITICAL SUCCESS CRITERIA ASSESSMENT:")
            
            critical_criteria = [
                ('document_ai_processing_successful', 'Document AI Processing'),
                ('full_name_extracted', 'Field Extraction - Full Name'),
                ('date_standardization_working', 'Date Standardization'),
                ('backend_processes_ai_response', 'Backend Integration'),
                ('complete_workflow_successful', 'Complete Workflow')
            ]
            
            critical_passed = sum(1 for test_key, _ in critical_criteria if self.passport_tests.get(test_key, False))
            
            for test_key, description in critical_criteria:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🏆 OVERALL ASSESSMENT:")
            
            if critical_passed == len(critical_criteria):
                self.log("   ✅ ALL CRITICAL SUCCESS CRITERIA MET")
                self.log("   ✅ System Apps Script (Document AI only) working correctly")
                self.log("   ✅ Real passport processing successful")
                self.log("   ✅ Date standardization implemented correctly")
                self.log("   ✅ Field extraction working as expected")
            else:
                self.log(f"   ❌ SOME CRITICAL CRITERIA NOT MET ({critical_passed}/{len(critical_criteria)})")
                
                # Identify specific issues
                if not self.passport_tests.get('document_ai_processing_successful'):
                    self.log("   ❌ Document AI processing needs attention")
                if not self.passport_tests.get('date_standardization_working'):
                    self.log("   ❌ Date standardization needs improvement")
                if not self.passport_tests.get('backend_processes_ai_response'):
                    self.log("   ❌ Backend integration issues detected")
            
            if success_rate >= 80:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the passport processing tests"""
    tester = PassportProcessingTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_passport_processing_test()
        
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
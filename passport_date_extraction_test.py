#!/usr/bin/env python3
"""
Enhanced Passport Date Extraction Testing
FOCUS: Test the enhanced passport extraction with improved AI prompts and date pattern matching

REVIEW REQUEST REQUIREMENTS:
1. Authentication: Login with admin1/123456 and verify Document AI configuration
2. API Response Analysis: Call /api/crew/analyze-passport and capture EXACT response
3. Date Field Verification: Focus specifically on whether date_of_birth field is now populated
4. Backend Log Analysis: Check if enhanced prompt and patterns are working

EXPECTED IMPROVEMENTS:
- date_of_birth field should now contain a value (not empty string)
- Enhanced AI prompt should help extract dates more reliably  
- Manual extraction fallback should find dates even if JSON parsing fails
- Backend logs should show successful date extraction

COMPARISON WITH PREVIOUS RESULTS:
Before Enhancement: date_of_birth: "" (empty)
After Enhancement (Expected): date_of_birth: "14/02/1983" or similar format
"""

import requests
import json
import os
import sys
import tempfile
import time
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
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class PassportDateExtractionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for passport date extraction
        self.passport_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'document_ai_configuration_verified': False,
            'user_has_proper_permissions': False,
            
            # API Response Analysis
            'analyze_passport_endpoint_accessible': False,
            'passport_analysis_request_successful': False,
            'api_response_captured': False,
            'response_structure_valid': False,
            
            # Date Field Verification (CRITICAL)
            'date_of_birth_field_present': False,
            'date_of_birth_field_populated': False,
            'date_of_birth_format_correct': False,
            'issue_date_field_populated': False,
            'expiry_date_field_populated': False,
            
            # Enhanced AI Prompt Effectiveness
            'enhanced_prompt_working': False,
            'manual_extraction_fallback_working': False,
            'pattern_matching_improved': False,
            'confidence_score_reasonable': False,
            
            # Backend Log Analysis
            'backend_logs_show_date_extraction': False,
            'enhanced_patterns_detected': False,
            'standardization_function_working': False,
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
        """Authenticate with admin1/123456 credentials as specified in review request"""
        try:
            self.log("🔐 Authenticating with admin1/123456 as specified in review request...")
            
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
                
                # Check if user has proper permissions for passport analysis
                user_role = self.current_user.get('role', '').lower()
                if user_role in ['admin', 'super_admin', 'manager']:
                    self.passport_tests['user_has_proper_permissions'] = True
                    self.log(f"   ✅ User role '{user_role}' has passport analysis permissions")
                else:
                    self.log(f"   ⚠️ User role '{user_role}' may not have passport analysis permissions")
                
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
    
    def verify_document_ai_configuration(self):
        """Verify Document AI configuration as specified in review request"""
        try:
            self.log("🤖 Verifying Document AI configuration...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                config_data = response.json()
                self.log("✅ Document AI configuration endpoint accessible")
                
                # Check for Document AI configuration
                document_ai = config_data.get('document_ai', {})
                if document_ai:
                    enabled = document_ai.get('enabled', False)
                    project_id = document_ai.get('project_id', '')
                    processor_id = document_ai.get('processor_id', '')
                    location = document_ai.get('location', '')
                    
                    self.log(f"   Document AI enabled: {enabled}")
                    self.log(f"   Project ID: {project_id}")
                    self.log(f"   Processor ID: {processor_id}")
                    self.log(f"   Location: {location}")
                    
                    if enabled and project_id and processor_id:
                        self.passport_tests['document_ai_configuration_verified'] = True
                        self.log("✅ Document AI configuration is properly set up")
                        return True
                    else:
                        self.log("❌ Document AI configuration is incomplete")
                        return False
                else:
                    self.log("❌ No Document AI configuration found")
                    return False
            else:
                self.log(f"   ❌ Failed to get AI configuration - Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying Document AI configuration: {str(e)}", "ERROR")
            return False
    
    def create_test_passport_file(self):
        """Create a test passport file for analysis"""
        try:
            # Create a temporary file with passport-like content
            # This simulates a passport with date information that should be extracted
            passport_content = """
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
SOCIALIST REPUBLIC OF VIETNAM
HỘ CHIẾU / PASSPORT

Họ / Surname: NGUYEN
Tên đệm và tên / Given names: VAN MINH

Số hộ chiếu / Passport No.: C1571189
Quốc tịch / Nationality: VIỆT NAM / VIETNAMESE

Ngày sinh / Date of birth: 14/02/1983
Nơi sinh / Place of birth: HỒ CHÍ MINH
Giới tính / Sex: M / Nam

Ngày cấp / Date of issue: 15/03/2020
Ngày hết hạn / Date of expiry: 14/03/2030

Cơ quan cấp / Issuing authority: CỤC XUẤT NHẬP CẢNH
"""
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(passport_content)
            temp_file.close()
            
            self.log(f"📄 Created test passport file: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Error creating test passport file: {str(e)}", "ERROR")
            return None
    
    def test_analyze_passport_endpoint(self):
        """Test /api/crew/analyze-passport endpoint and capture EXACT response"""
        try:
            self.log("🔍 Testing /api/crew/analyze-passport endpoint...")
            
            # Create test passport file
            test_file_path = self.create_test_passport_file()
            if not test_file_path:
                self.log("❌ Failed to create test passport file")
                return None
            
            try:
                endpoint = f"{BACKEND_URL}/crew/analyze-passport"
                self.log(f"   POST {endpoint}")
                
                # Prepare multipart form data
                with open(test_file_path, 'rb') as f:
                    files = {'file': ('test_passport.txt', f, 'text/plain')}
                    data = {'ship_name': 'BROTHER 36'}  # Use a known ship for testing
                    
                    self.log("   Sending passport analysis request...")
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
                    self.passport_tests['analyze_passport_endpoint_accessible'] = True
                    self.passport_tests['passport_analysis_request_successful'] = True
                    self.log("✅ Passport analysis endpoint accessible and working")
                    
                    try:
                        response_data = response.json()
                        self.passport_tests['api_response_captured'] = True
                        
                        # Log EXACT response as requested
                        self.log("📋 EXACT API RESPONSE CAPTURED:")
                        self.log("=" * 60)
                        self.log(json.dumps(response_data, indent=2, ensure_ascii=False))
                        self.log("=" * 60)
                        
                        # Verify response structure
                        if isinstance(response_data, dict):
                            self.passport_tests['response_structure_valid'] = True
                            self.log("✅ Response structure is valid (dictionary)")
                            
                            # Analyze date fields (CRITICAL FOCUS)
                            self.analyze_date_fields(response_data)
                            
                            # Analyze other fields
                            self.analyze_response_fields(response_data)
                            
                            return response_data
                        else:
                            self.log("❌ Response structure is invalid (not a dictionary)")
                            return None
                            
                    except json.JSONDecodeError as e:
                        self.log(f"   ❌ Invalid JSON response: {str(e)}")
                        self.log(f"   Raw response: {response.text[:500]}")
                        return None
                        
                else:
                    self.log(f"   ❌ Passport analysis failed - Status: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"   Error: {response.text[:200]}")
                    return None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(test_file_path)
                    self.log(f"   🧹 Cleaned up test file: {test_file_path}")
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Error testing analyze passport endpoint: {str(e)}", "ERROR")
            return None
    
    def analyze_date_fields(self, response_data):
        """Analyze date fields in the response (CRITICAL FOCUS)"""
        try:
            self.log("🗓️ ANALYZING DATE FIELDS (CRITICAL FOCUS):")
            
            # Check for date_of_birth field (PRIMARY FOCUS)
            date_of_birth = response_data.get('date_of_birth', '')
            self.log(f"   date_of_birth: '{date_of_birth}'")
            
            if 'date_of_birth' in response_data:
                self.passport_tests['date_of_birth_field_present'] = True
                self.log("   ✅ date_of_birth field is present")
                
                if date_of_birth and date_of_birth.strip() and date_of_birth != "":
                    self.passport_tests['date_of_birth_field_populated'] = True
                    self.log(f"   ✅ date_of_birth field is populated: '{date_of_birth}'")
                    
                    # Check format (DD/MM/YYYY preferred)
                    if self.validate_date_format(date_of_birth):
                        self.passport_tests['date_of_birth_format_correct'] = True
                        self.log(f"   ✅ date_of_birth format is correct: '{date_of_birth}'")
                    else:
                        self.log(f"   ⚠️ date_of_birth format may need improvement: '{date_of_birth}'")
                else:
                    self.log("   ❌ date_of_birth field is EMPTY - This is the main issue to fix!")
            else:
                self.log("   ❌ date_of_birth field is MISSING")
            
            # Check other date fields
            issue_date = response_data.get('issue_date', '')
            expiry_date = response_data.get('expiry_date', '')
            
            self.log(f"   issue_date: '{issue_date}'")
            self.log(f"   expiry_date: '{expiry_date}'")
            
            if issue_date and issue_date.strip():
                self.passport_tests['issue_date_field_populated'] = True
                self.log("   ✅ issue_date field is populated")
            
            if expiry_date and expiry_date.strip():
                self.passport_tests['expiry_date_field_populated'] = True
                self.log("   ✅ expiry_date field is populated")
            
            # Overall date extraction assessment
            date_fields_populated = sum([
                bool(date_of_birth and date_of_birth.strip()),
                bool(issue_date and issue_date.strip()),
                bool(expiry_date and expiry_date.strip())
            ])
            
            self.log(f"   📊 Date fields populated: {date_fields_populated}/3")
            
            if date_fields_populated >= 2:
                self.passport_tests['enhanced_prompt_working'] = True
                self.log("   ✅ Enhanced AI prompt appears to be working (2+ date fields populated)")
            elif date_fields_populated >= 1:
                self.log("   ⚠️ Enhanced AI prompt partially working (1 date field populated)")
            else:
                self.log("   ❌ Enhanced AI prompt may not be working (no date fields populated)")
                
        except Exception as e:
            self.log(f"❌ Error analyzing date fields: {str(e)}", "ERROR")
    
    def validate_date_format(self, date_string):
        """Validate if date string is in expected format"""
        try:
            if not date_string:
                return False
            
            # Check for DD/MM/YYYY format (preferred)
            import re
            dd_mm_yyyy_pattern = r'^\d{1,2}/\d{1,2}/\d{4}$'
            if re.match(dd_mm_yyyy_pattern, date_string):
                return True
            
            # Check for other acceptable formats
            acceptable_patterns = [
                r'^\d{1,2}-\d{1,2}-\d{4}$',  # DD-MM-YYYY
                r'^\d{4}-\d{1,2}-\d{1,2}$',  # YYYY-MM-DD
                r'^\d{1,2}\.\d{1,2}\.\d{4}$',  # DD.MM.YYYY
            ]
            
            for pattern in acceptable_patterns:
                if re.match(pattern, date_string):
                    return True
            
            return False
            
        except Exception as e:
            self.log(f"Error validating date format: {str(e)}")
            return False
    
    def analyze_response_fields(self, response_data):
        """Analyze other fields in the response"""
        try:
            self.log("📋 ANALYZING OTHER RESPONSE FIELDS:")
            
            # Check confidence score
            confidence_score = response_data.get('confidence_score', 0)
            self.log(f"   confidence_score: {confidence_score}")
            
            if isinstance(confidence_score, (int, float)) and 0 <= confidence_score <= 1:
                if confidence_score >= 0.4:  # Based on enhanced thresholds mentioned
                    self.passport_tests['confidence_score_reasonable'] = True
                    self.log(f"   ✅ Confidence score is reasonable: {confidence_score}")
                else:
                    self.log(f"   ⚠️ Confidence score is low: {confidence_score}")
            
            # Check other extracted fields
            fields_to_check = [
                'full_name', 'sex', 'place_of_birth', 'passport_number', 
                'nationality', 'issue_date', 'expiry_date'
            ]
            
            populated_fields = 0
            for field in fields_to_check:
                value = response_data.get(field, '')
                if value and str(value).strip():
                    populated_fields += 1
                    self.log(f"   ✅ {field}: '{value}'")
                else:
                    self.log(f"   ❌ {field}: empty or missing")
            
            self.log(f"   📊 Total populated fields: {populated_fields}/{len(fields_to_check)}")
            
            # Check for signs of enhanced extraction
            if populated_fields >= 5:  # Most fields populated
                self.passport_tests['manual_extraction_fallback_working'] = True
                self.log("   ✅ Manual extraction fallback appears to be working")
            
        except Exception as e:
            self.log(f"❌ Error analyzing response fields: {str(e)}", "ERROR")
    
    def check_backend_logs(self):
        """Check backend logs for evidence of enhanced date extraction"""
        try:
            self.log("📋 CHECKING BACKEND LOGS FOR DATE EXTRACTION EVIDENCE...")
            
            # Try to get backend logs (this might not be directly accessible)
            # For now, we'll check if the supervisor logs show evidence
            try:
                import subprocess
                result = subprocess.run(
                    ['tail', '-n', '100', '/var/log/supervisor/backend.err.log'],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    log_content = result.stdout
                    self.log("   ✅ Backend logs accessible")
                    
                    # Look for evidence of date extraction
                    date_extraction_keywords = [
                        'Standardizing', 'date_of_birth', 'issue_date', 'expiry_date',
                        'Enhanced AI prompt', 'pattern matching', 'standardize_passport_dates'
                    ]
                    
                    found_evidence = []
                    for keyword in date_extraction_keywords:
                        if keyword.lower() in log_content.lower():
                            found_evidence.append(keyword)
                    
                    if found_evidence:
                        self.passport_tests['backend_logs_show_date_extraction'] = True
                        self.passport_tests['enhanced_patterns_detected'] = True
                        self.log(f"   ✅ Found date extraction evidence: {', '.join(found_evidence)}")
                    else:
                        self.log("   ⚠️ No specific date extraction evidence found in recent logs")
                    
                    # Look for standardization function
                    if 'standardize_passport_dates' in log_content:
                        self.passport_tests['standardization_function_working'] = True
                        self.log("   ✅ standardize_passport_dates function detected in logs")
                    
                else:
                    self.log("   ⚠️ Could not access backend error logs")
                    
            except Exception as e:
                self.log(f"   ⚠️ Could not check backend logs: {str(e)}")
                
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def run_comprehensive_passport_date_test(self):
        """Run comprehensive test of enhanced passport date extraction"""
        try:
            self.log("🚀 STARTING ENHANCED PASSPORT DATE EXTRACTION TEST")
            self.log("=" * 80)
            self.log("FOCUS: Verify improved AI prompts and date pattern matching effectiveness")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication with admin1/123456")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Verify Document AI Configuration
            self.log("\nSTEP 2: Verify Document AI Configuration")
            if not self.verify_document_ai_configuration():
                self.log("❌ CRITICAL: Document AI configuration not properly set up")
                return False
            
            # Step 3: Test Passport Analysis Endpoint
            self.log("\nSTEP 3: Test /api/crew/analyze-passport Endpoint")
            response_data = self.test_analyze_passport_endpoint()
            if not response_data:
                self.log("❌ CRITICAL: Passport analysis endpoint failed")
                return False
            
            # Step 4: Check Backend Logs
            self.log("\nSTEP 4: Check Backend Logs for Date Extraction Evidence")
            self.check_backend_logs()
            
            self.log("\n" + "=" * 80)
            self.log("✅ ENHANCED PASSPORT DATE EXTRACTION TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 ENHANCED PASSPORT DATE EXTRACTION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.passport_tests)
            passed_tests = sum(1 for result in self.passport_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication with admin1/123456'),
                ('document_ai_configuration_verified', 'Document AI configuration verified'),
                ('user_has_proper_permissions', 'User has proper permissions'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # API Response Analysis Results
            self.log("\n🔍 API RESPONSE ANALYSIS:")
            api_tests = [
                ('analyze_passport_endpoint_accessible', 'Analyze passport endpoint accessible'),
                ('passport_analysis_request_successful', 'Passport analysis request successful'),
                ('api_response_captured', 'API response captured'),
                ('response_structure_valid', 'Response structure valid'),
            ]
            
            for test_key, description in api_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Date Field Verification Results (CRITICAL)
            self.log("\n🗓️ DATE FIELD VERIFICATION (CRITICAL):")
            date_tests = [
                ('date_of_birth_field_present', 'date_of_birth field present'),
                ('date_of_birth_field_populated', 'date_of_birth field populated (MAIN FOCUS)'),
                ('date_of_birth_format_correct', 'date_of_birth format correct'),
                ('issue_date_field_populated', 'issue_date field populated'),
                ('expiry_date_field_populated', 'expiry_date field populated'),
            ]
            
            for test_key, description in date_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Enhanced AI Prompt Effectiveness
            self.log("\n🤖 ENHANCED AI PROMPT EFFECTIVENESS:")
            ai_tests = [
                ('enhanced_prompt_working', 'Enhanced AI prompt working'),
                ('manual_extraction_fallback_working', 'Manual extraction fallback working'),
                ('pattern_matching_improved', 'Pattern matching improved'),
                ('confidence_score_reasonable', 'Confidence score reasonable'),
            ]
            
            for test_key, description in ai_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Log Analysis
            self.log("\n📋 BACKEND LOG ANALYSIS:")
            log_tests = [
                ('backend_logs_show_date_extraction', 'Backend logs show date extraction'),
                ('enhanced_patterns_detected', 'Enhanced patterns detected'),
                ('standardization_function_working', 'Standardization function working'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.passport_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Critical Success Criteria Assessment
            self.log("\n🎯 CRITICAL SUCCESS CRITERIA ASSESSMENT:")
            
            # Main focus: date_of_birth field populated
            if self.passport_tests.get('date_of_birth_field_populated', False):
                self.log("   ✅ PRIMARY SUCCESS: date_of_birth field is now populated!")
                self.log("   ✅ Enhanced date extraction is working as expected")
            else:
                self.log("   ❌ PRIMARY FAILURE: date_of_birth field is still empty")
                self.log("   ❌ Enhanced date extraction needs further improvement")
            
            # Secondary criteria
            date_fields_working = sum([
                self.passport_tests.get('date_of_birth_field_populated', False),
                self.passport_tests.get('issue_date_field_populated', False),
                self.passport_tests.get('expiry_date_field_populated', False)
            ])
            
            self.log(f"   📊 Date fields working: {date_fields_working}/3")
            
            if date_fields_working >= 2:
                self.log("   ✅ GOOD: Multiple date fields are working")
            elif date_fields_working >= 1:
                self.log("   ⚠️ PARTIAL: Some date fields are working")
            else:
                self.log("   ❌ POOR: No date fields are working")
            
            # Overall Assessment
            self.log("\n🏆 OVERALL ASSESSMENT:")
            
            if success_rate >= 80:
                self.log(f"   ✅ EXCELLENT: Enhanced passport date extraction is working well ({success_rate:.1f}%)")
            elif success_rate >= 60:
                self.log(f"   ⚠️ GOOD: Enhanced passport date extraction is partially working ({success_rate:.1f}%)")
            else:
                self.log(f"   ❌ NEEDS IMPROVEMENT: Enhanced passport date extraction needs more work ({success_rate:.1f}%)")
            
            # Comparison with previous results
            self.log("\n📈 COMPARISON WITH PREVIOUS RESULTS:")
            if self.passport_tests.get('date_of_birth_field_populated', False):
                self.log("   ✅ IMPROVEMENT: Before - date_of_birth: '' (empty)")
                self.log("   ✅ IMPROVEMENT: After - date_of_birth: populated with actual date")
                self.log("   ✅ SUCCESS: Enhanced AI prompt and pattern matching are effective")
            else:
                self.log("   ❌ NO IMPROVEMENT: date_of_birth field is still empty")
                self.log("   ❌ RECOMMENDATION: Further enhance AI prompts and pattern matching")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the enhanced passport date extraction tests"""
    tester = PassportDateExtractionTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_passport_date_test()
        
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
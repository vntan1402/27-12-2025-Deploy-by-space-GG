#!/usr/bin/env python3
"""
DEBUG PASSPORT DATE OF BIRTH AUTO-FILL ISSUE - DETAILED API RESPONSE ANALYSIS

OBJECTIVE: Debug why the Date of Birth field is not auto-filling in the frontend 
while other fields (Full Name, Sex, Place of Birth, Passport Number) are working correctly.

SPECIFIC DEBUG REQUIREMENTS:
1. Authentication & AI Config: Verify admin1/123456 login and Document AI configuration
2. Passport Analysis API Call: Make actual API call to /api/crew/analyze-passport with test passport
3. API Response Inspection: Capture and analyze the EXACT response format, specifically focusing on:
   - date_of_birth field presence and value
   - Format of the date (should be DD/MM/YYYY after standardization)
   - Check if field is empty, null, or has unexpected format

DETAILED INVESTIGATION:
4. Backend Logs Analysis: Check backend logs during passport analysis
5. Field-by-Field Comparison: Compare why these work but date_of_birth doesn't:
   - ✅ full_name: "VŨ NGỌC TÂN" (working)
   - ✅ sex: "M" (working) 
   - ✅ place_of_birth: "HẢI PHÒNG" (working)
   - ✅ passport_number: "C1571189" (working)
   - ❌ date_of_birth: "" (not working - empty in frontend)
"""

import requests
import json
import os
import sys
import tempfile
import base64
from datetime import datetime
import traceback

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipman-progress.preview.emergentagent.com') + '/api'
print(f"Using backend URL: {BACKEND_URL}")

class PassportDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.debug_results = {}
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
    def authenticate(self):
        """Authenticate with admin1/123456 credentials"""
        try:
            self.log("🔐 STEP 1: Authenticating with admin1/123456...")
            
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
                
                self.debug_results['authentication_successful'] = True
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
        """Check Document AI configuration"""
        try:
            self.log("🤖 STEP 2: Checking Document AI configuration...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                config = response.json()
                self.log("✅ AI Configuration retrieved successfully")
                
                # Check Document AI configuration
                document_ai = config.get('document_ai', {})
                if document_ai:
                    self.log("📄 Document AI Configuration:")
                    self.log(f"   Enabled: {document_ai.get('enabled', False)}")
                    self.log(f"   Project ID: {document_ai.get('project_id', 'Not set')}")
                    self.log(f"   Processor ID: {document_ai.get('processor_id', 'Not set')}")
                    self.log(f"   Location: {document_ai.get('location', 'Not set')}")
                    
                    if document_ai.get('enabled') and document_ai.get('project_id') and document_ai.get('processor_id'):
                        self.log("✅ Document AI is properly configured")
                        self.debug_results['ai_config_valid'] = True
                        return True
                    else:
                        self.log("❌ Document AI configuration incomplete")
                        self.debug_results['ai_config_valid'] = False
                        return False
                else:
                    self.log("❌ No Document AI configuration found")
                    self.debug_results['ai_config_valid'] = False
                    return False
            else:
                self.log(f"❌ Failed to get AI configuration: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking AI configuration: {str(e)}", "ERROR")
            return False
    
    def create_test_passport_file(self):
        """Create a test passport file for analysis"""
        try:
            self.log("📄 STEP 3: Creating test passport file...")
            
            # Create a simple test passport content (simulating Vietnamese passport)
            passport_content = """
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
SOCIALIST REPUBLIC OF VIETNAM
HỘ CHIẾU / PASSPORT

Họ và tên / Surname and given names: VŨ NGỌC TÂN
Ngày sinh / Date of birth: 14/02/1983
Nơi sinh / Place of birth: HẢI PHÒNG
Giới tính / Sex: M / Nam
Quốc tịch / Nationality: VIỆT NAM / VIETNAMESE
Số hộ chiếu / Passport No.: C1571189
Ngày cấp / Date of issue: 15/03/2020
Ngày hết hạn / Date of expiry: 14/03/2030
Nơi cấp / Place of issue: HÀ NỘI
"""
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(passport_content)
            temp_file.close()
            
            self.log(f"✅ Test passport file created: {temp_file.name}")
            self.log("📋 Test passport contains:")
            self.log("   Full Name: VŨ NGỌC TÂN")
            self.log("   Date of Birth: 14/02/1983")
            self.log("   Place of Birth: HẢI PHÒNG")
            self.log("   Sex: M")
            self.log("   Passport Number: C1571189")
            
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Error creating test passport file: {str(e)}", "ERROR")
            return None
    
    def analyze_passport_api_call(self, passport_file_path):
        """Make actual API call to /api/crew/analyze-passport"""
        try:
            self.log("🔍 STEP 4: Making API call to /api/crew/analyze-passport...")
            
            endpoint = f"{BACKEND_URL}/crew/analyze-passport"
            self.log(f"   POST {endpoint}")
            
            # Prepare multipart form data
            with open(passport_file_path, 'rb') as f:
                files = {
                    'passport_file': ('test_passport.txt', f, 'text/plain')
                }
                
                data = {
                    'ship_name': 'BROTHER 36'
                }
                
                self.log("   Request data:")
                self.log(f"     ship_name: {data['ship_name']}")
                self.log(f"     passport_file: test_passport.txt")
                
                response = requests.post(
                    endpoint, 
                    files=files, 
                    data=data,
                    headers=self.get_headers(), 
                    timeout=120
                )
                
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.log("✅ Passport analysis API call successful")
                
                try:
                    response_data = response.json()
                    self.log("📊 CRITICAL: API Response Analysis")
                    self.log("=" * 60)
                    
                    # Print the EXACT response JSON
                    self.log("🔍 EXACT API RESPONSE JSON:")
                    self.log(json.dumps(response_data, indent=2, ensure_ascii=False))
                    
                    self.log("\n🔍 FIELD-BY-FIELD ANALYSIS:")
                    
                    # Check each field specifically
                    fields_to_check = [
                        'full_name', 'sex', 'date_of_birth', 'place_of_birth', 
                        'passport_number', 'nationality', 'issue_date', 'expiry_date'
                    ]
                    
                    for field in fields_to_check:
                        value = response_data.get(field, 'FIELD_NOT_PRESENT')
                        if value == 'FIELD_NOT_PRESENT':
                            self.log(f"   ❌ {field}: FIELD NOT PRESENT IN RESPONSE")
                        elif value == "" or value is None:
                            self.log(f"   ❌ {field}: EMPTY/NULL ('{value}')")
                        else:
                            self.log(f"   ✅ {field}: '{value}' (type: {type(value).__name__})")
                    
                    # CRITICAL: Focus on date_of_birth field
                    self.log("\n🎯 CRITICAL FOCUS: date_of_birth field")
                    self.log("=" * 40)
                    
                    date_of_birth = response_data.get('date_of_birth')
                    if 'date_of_birth' not in response_data:
                        self.log("❌ CRITICAL ISSUE: 'date_of_birth' field is NOT PRESENT in API response")
                        self.debug_results['date_of_birth_present'] = False
                    elif date_of_birth == "" or date_of_birth is None:
                        self.log(f"❌ CRITICAL ISSUE: 'date_of_birth' field is EMPTY/NULL: '{date_of_birth}'")
                        self.debug_results['date_of_birth_present'] = True
                        self.debug_results['date_of_birth_empty'] = True
                    else:
                        self.log(f"✅ 'date_of_birth' field is PRESENT and has value: '{date_of_birth}'")
                        self.log(f"   Type: {type(date_of_birth).__name__}")
                        self.log(f"   Length: {len(str(date_of_birth))}")
                        self.log(f"   Format check: {'DD/MM/YYYY' if '/' in str(date_of_birth) else 'Other format'}")
                        self.debug_results['date_of_birth_present'] = True
                        self.debug_results['date_of_birth_empty'] = False
                        self.debug_results['date_of_birth_value'] = str(date_of_birth)
                    
                    # Compare with working fields
                    self.log("\n📊 COMPARISON WITH WORKING FIELDS:")
                    working_fields = {
                        'full_name': 'VŨ NGỌC TÂN',
                        'sex': 'M',
                        'place_of_birth': 'HẢI PHÒNG',
                        'passport_number': 'C1571189'
                    }
                    
                    for field, expected in working_fields.items():
                        actual = response_data.get(field, 'NOT_PRESENT')
                        if actual == expected:
                            self.log(f"   ✅ {field}: WORKING - Expected '{expected}', Got '{actual}'")
                        else:
                            self.log(f"   ❌ {field}: ISSUE - Expected '{expected}', Got '{actual}'")
                    
                    self.debug_results['api_response'] = response_data
                    return response_data
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    self.log(f"Raw response: {response.text[:500]}")
                    return None
                    
            else:
                self.log(f"❌ Passport analysis API call failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error making passport analysis API call: {str(e)}", "ERROR")
            traceback.print_exc()
            return None
    
    def check_backend_logs(self):
        """Check backend logs for date processing"""
        try:
            self.log("📋 STEP 5: Checking backend logs...")
            
            # Try to get backend logs (this might not be available via API)
            # For now, we'll just note that this should be checked manually
            self.log("⚠️ Backend logs should be checked manually for:")
            self.log("   - Date standardization function execution")
            self.log("   - Original AI extracted date vs standardized date")
            self.log("   - Any errors or warnings during date processing")
            self.log("   - Check: tail -n 100 /var/log/supervisor/backend.*.log")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def test_date_standardization_function(self):
        """Test the date standardization function directly if possible"""
        try:
            self.log("🔧 STEP 6: Testing date standardization logic...")
            
            # Test various date formats that might come from AI
            test_dates = [
                "14/02/1983",
                "February 14, 1983",
                "14 February 1983",
                "Feb 14, 1983",
                "14-Feb-1983",
                "February 14, 1983 (14/02/1983)",  # This is the problematic format mentioned
                "1983-02-14",
                ""
            ]
            
            self.log("📅 Testing date formats that might cause issues:")
            for test_date in test_dates:
                self.log(f"   Input: '{test_date}' -> Expected: '14/02/1983' (DD/MM/YYYY)")
            
            self.log("⚠️ Note: Actual standardization testing requires backend code access")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing date standardization: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_debug_test(self):
        """Run comprehensive debug test for passport date of birth issue"""
        try:
            self.log("🚀 STARTING PASSPORT DATE OF BIRTH DEBUG TEST")
            self.log("=" * 80)
            self.log("OBJECTIVE: Debug why Date of Birth field is not auto-filling")
            self.log("=" * 80)
            
            # Step 1: Authentication
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Check AI Configuration
            if not self.check_ai_configuration():
                self.log("❌ CRITICAL: AI Configuration invalid - cannot proceed")
                return False
            
            # Step 3: Create test passport file
            passport_file = self.create_test_passport_file()
            if not passport_file:
                self.log("❌ CRITICAL: Failed to create test passport file")
                return False
            
            # Step 4: Make API call and analyze response
            api_response = self.analyze_passport_api_call(passport_file)
            if not api_response:
                self.log("❌ CRITICAL: Passport analysis API call failed")
                return False
            
            # Step 5: Check backend logs
            self.check_backend_logs()
            
            # Step 6: Test date standardization
            self.test_date_standardization_function()
            
            # Cleanup
            try:
                os.unlink(passport_file)
                self.log("✅ Cleaned up test passport file")
            except:
                pass
            
            self.log("\n" + "=" * 80)
            self.log("✅ PASSPORT DATE OF BIRTH DEBUG TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in debug test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_debug_summary(self):
        """Print comprehensive summary of debug findings"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 PASSPORT DATE OF BIRTH DEBUG SUMMARY")
            self.log("=" * 80)
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION:")
            if self.debug_results.get('authentication_successful', False):
                self.log("   ✅ Authentication with admin1/123456 successful")
            else:
                self.log("   ❌ Authentication failed")
            
            # AI Configuration Results
            self.log("\n🤖 AI CONFIGURATION:")
            if self.debug_results.get('ai_config_valid', False):
                self.log("   ✅ Document AI configuration is valid")
            else:
                self.log("   ❌ Document AI configuration is invalid or missing")
            
            # API Response Analysis
            self.log("\n🔍 API RESPONSE ANALYSIS:")
            if 'api_response' in self.debug_results:
                self.log("   ✅ API call to /api/crew/analyze-passport successful")
                
                # Date of Birth Field Analysis
                self.log("\n🎯 DATE OF BIRTH FIELD ANALYSIS:")
                if self.debug_results.get('date_of_birth_present', False):
                    if self.debug_results.get('date_of_birth_empty', True):
                        self.log("   ❌ CRITICAL ISSUE: date_of_birth field is EMPTY/NULL")
                        self.log("   🔍 ROOT CAUSE: Backend is returning empty date_of_birth field")
                        self.log("   💡 SOLUTION NEEDED: Check date standardization function in backend")
                    else:
                        date_value = self.debug_results.get('date_of_birth_value', '')
                        self.log(f"   ✅ date_of_birth field has value: '{date_value}'")
                        self.log("   🔍 FRONTEND ISSUE: Check frontend date conversion logic")
                else:
                    self.log("   ❌ CRITICAL ISSUE: date_of_birth field is NOT PRESENT in API response")
                    self.log("   🔍 ROOT CAUSE: Backend is not including date_of_birth in response")
                    self.log("   💡 SOLUTION NEEDED: Fix backend passport analysis endpoint")
            else:
                self.log("   ❌ API call failed - cannot analyze response")
            
            # Field Comparison
            self.log("\n📊 FIELD COMPARISON:")
            self.log("   Working fields: full_name, sex, place_of_birth, passport_number")
            self.log("   Not working: date_of_birth")
            self.log("   🔍 PATTERN: All text fields work, date field doesn't")
            
            # Recommendations
            self.log("\n💡 RECOMMENDATIONS:")
            if self.debug_results.get('date_of_birth_present', False):
                if self.debug_results.get('date_of_birth_empty', True):
                    self.log("   1. Check backend date standardization function")
                    self.log("   2. Verify AI extraction is returning date_of_birth")
                    self.log("   3. Check if date format conversion is failing")
                else:
                    self.log("   1. Check frontend date conversion logic")
                    self.log("   2. Verify HTML date input format (YYYY-MM-DD)")
                    self.log("   3. Check convertPassportDateToInputFormat() function")
            else:
                self.log("   1. Fix backend to include date_of_birth in API response")
                self.log("   2. Check passport analysis endpoint implementation")
                self.log("   3. Verify AI extraction configuration")
            
            self.log("\n🔧 NEXT STEPS:")
            self.log("   1. Check backend logs during passport analysis")
            self.log("   2. Test date standardization function with various formats")
            self.log("   3. Verify frontend auto-fill logic for date fields")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing debug summary: {str(e)}", "ERROR")

def main():
    """Main function to run the passport debug test"""
    tester = PassportDebugTester()
    
    try:
        # Run comprehensive debug test
        success = tester.run_comprehensive_debug_test()
        
        # Print summary
        tester.print_debug_summary()
        
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
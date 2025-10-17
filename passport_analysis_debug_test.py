#!/usr/bin/env python3
"""
Passport Analysis Date of Birth Debug Testing
FOCUS: Debug the Date of Birth auto-fill issue in passport analysis

PROBLEM:
- Passport analysis is working and auto-filling most fields correctly
- Full Name: VŨ NGỌC TÂN ✅
- Place of Birth: HẢI PHÒNG ✅  
- Passport No.: C1571189 ✅
- Date of Birth: NOT auto-filled ❌ (should be 14/02/1983)

DEBUGGING TASKS:
1. Test Passport Analysis API: Call POST /api/crew/analyze-passport with the Vietnamese passport
2. Examine API Response: Check the exact structure and content of the analysis response
3. Check date_of_birth Field: Verify what value is returned for date_of_birth in the response
4. Verify Date Format: Check if the date format from Document AI matches expected format
5. Test Date Conversion: Test if the date conversion logic works with the actual returned value

EXPECTED ANALYSIS RESPONSE STRUCTURE:
{
  "success": true,
  "analysis": {
    "full_name": "VŨ NGỌC TÂN",
    "sex": "M",
    "date_of_birth": "14/02/1983", // This should be present
    "place_of_birth": "HẢI PHÒNG", 
    "passport_number": "C1571189",
    "nationality": "VIETNAMESE",
    "issue_date": "11/04/2016",
    "expiry_date": "11/04/2026",
    "confidence_score": 0.85
  }
}
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipmatrix.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class PassportAnalysisDebugTester:
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
            'ship_selection_successful': False,
            
            # Passport Analysis API Tests
            'passport_analysis_endpoint_accessible': False,
            'passport_analysis_request_successful': False,
            'passport_analysis_response_valid': False,
            'response_structure_correct': False,
            
            # Date of Birth Field Debugging
            'date_of_birth_field_present': False,
            'date_of_birth_field_populated': False,
            'date_of_birth_format_correct': False,
            'date_of_birth_value_matches_expected': False,
            
            # Other Field Verification
            'full_name_field_correct': False,
            'place_of_birth_field_correct': False,
            'passport_number_field_correct': False,
            'sex_field_correct': False,
            
            # API Response Analysis
            'confidence_score_present': False,
            'all_expected_fields_present': False,
            'response_success_flag_true': False,
            
            # Date Format Testing
            'date_format_dd_mm_yyyy_supported': False,
            'date_format_iso_supported': False,
            'date_conversion_logic_working': False,
        }
        
        # Store test results for analysis
        self.user_company = None
        self.selected_ship = None
        self.passport_analysis_response = {}
        self.date_analysis = {}
        
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
                
                self.debug_tests['authentication_successful'] = True
                self.user_company = self.current_user.get('company')
                if self.user_company:
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
    
    def select_test_ship(self):
        """Select a ship for testing (BROTHER 36 as mentioned in review request)"""
        try:
            self.log("🚢 Selecting test ship for passport analysis...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships")
                
                # Look for BROTHER 36 specifically
                brother_36 = None
                for ship in ships:
                    if ship.get('name') == 'BROTHER 36':
                        brother_36 = ship
                        break
                
                if brother_36:
                    self.selected_ship = brother_36
                    self.debug_tests['ship_selection_successful'] = True
                    self.log("✅ Selected BROTHER 36 ship for testing")
                    self.log(f"   Ship ID: {brother_36.get('id')}")
                    self.log(f"   Ship Name: {brother_36.get('name')}")
                    self.log(f"   IMO: {brother_36.get('imo')}")
                    self.log(f"   Flag: {brother_36.get('flag')}")
                    return True
                else:
                    # Fallback to first available ship
                    if ships:
                        self.selected_ship = ships[0]
                        self.debug_tests['ship_selection_successful'] = True
                        self.log(f"⚠️ BROTHER 36 not found, using {ships[0].get('name')} instead")
                        self.log(f"   Ship ID: {ships[0].get('id')}")
                        return True
                    else:
                        self.log("❌ No ships available for testing")
                        return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error selecting test ship: {str(e)}", "ERROR")
            return False
    
    def create_test_passport_file(self):
        """Create a test passport file with Vietnamese passport data"""
        try:
            self.log("📄 Creating test passport file with Vietnamese data...")
            
            # Create a simple text file simulating Vietnamese passport OCR content
            passport_content = """
SOCIALIST REPUBLIC OF VIETNAM
PASSPORT / HỘ CHIẾU

Passport No./Số hộ chiếu: C1571189
Type/Loại: P

Full Name/Họ và tên: VŨ NGỌC TÂN
Sex/Giới tính: M
Date of Birth/Ngày sinh: 14/02/1983
Place of Birth/Nơi sinh: HẢI PHÒNG
Nationality/Quốc tịch: VIETNAMESE

Date of Issue/Ngày cấp: 11/04/2016
Date of Expiry/Ngày hết hạn: 11/04/2026
Place of Issue/Nơi cấp: HÀ NỘI

Authority/Cơ quan cấp: IMMIGRATION DEPARTMENT
"""
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(passport_content)
            temp_file.close()
            
            self.log(f"✅ Created test passport file: {temp_file.name}")
            self.log("   Content includes:")
            self.log("   - Full Name: VŨ NGỌC TÂN")
            self.log("   - Date of Birth: 14/02/1983")
            self.log("   - Place of Birth: HẢI PHÒNG")
            self.log("   - Passport No.: C1571189")
            
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Error creating test passport file: {str(e)}", "ERROR")
            return None
    
    def test_passport_analysis_api(self):
        """Test the passport analysis API with Vietnamese passport data"""
        try:
            self.log("🔍 Testing passport analysis API...")
            
            if not self.selected_ship:
                self.log("❌ No ship selected for testing")
                return False
            
            # Create test passport file
            passport_file_path = self.create_test_passport_file()
            if not passport_file_path:
                self.log("❌ Failed to create test passport file")
                return False
            
            try:
                endpoint = f"{BACKEND_URL}/crew/analyze-passport"
                self.log(f"   POST {endpoint}")
                
                # Prepare multipart form data
                with open(passport_file_path, 'rb') as f:
                    files = {
                        'passport_file': ('vietnamese_passport.txt', f, 'text/plain')
                    }
                    data = {
                        'ship_name': self.selected_ship.get('name', 'BROTHER 36')
                    }
                    
                    self.log(f"   Ship name: {data['ship_name']}")
                    self.log(f"   File: {passport_file_path}")
                    
                    response = requests.post(
                        endpoint, 
                        files=files, 
                        data=data,
                        headers=self.get_headers(), 
                        timeout=120  # Longer timeout for AI processing
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.debug_tests['passport_analysis_endpoint_accessible'] = True
                    self.debug_tests['passport_analysis_request_successful'] = True
                    self.log("✅ Passport analysis API is accessible and responding")
                    
                    try:
                        response_data = response.json()
                        self.passport_analysis_response = response_data
                        self.debug_tests['passport_analysis_response_valid'] = True
                        self.log("✅ Response is valid JSON")
                        
                        # Log the complete response for debugging
                        self.log("📋 COMPLETE API RESPONSE:")
                        self.log(json.dumps(response_data, indent=2, ensure_ascii=False))
                        
                        return True
                    except json.JSONDecodeError as e:
                        self.log(f"❌ Invalid JSON response: {str(e)}")
                        self.log(f"   Raw response: {response.text[:500]}")
                        return False
                else:
                    self.log(f"❌ Passport analysis API failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"   Error: {response.text[:500]}")
                    return False
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(passport_file_path)
                    self.log(f"   Cleaned up temporary file: {passport_file_path}")
                except:
                    pass
                
        except Exception as e:
            self.log(f"❌ Error testing passport analysis API: {str(e)}", "ERROR")
            return False
    
    def analyze_response_structure(self):
        """Analyze the passport analysis response structure"""
        try:
            self.log("🔍 Analyzing passport analysis response structure...")
            
            if not self.passport_analysis_response:
                self.log("❌ No response data to analyze")
                return False
            
            response = self.passport_analysis_response
            
            # Check top-level structure
            self.log("📋 TOP-LEVEL RESPONSE STRUCTURE:")
            for key, value in response.items():
                self.log(f"   {key}: {type(value).__name__}")
                if isinstance(value, str) and len(value) > 100:
                    self.log(f"      Value: {value[:100]}...")
                else:
                    self.log(f"      Value: {value}")
            
            # Check success flag
            success = response.get('success')
            if success is True:
                self.debug_tests['response_success_flag_true'] = True
                self.log("✅ Response success flag is True")
            else:
                self.log(f"❌ Response success flag is {success}")
            
            # Check analysis section
            analysis = response.get('analysis')
            if analysis:
                self.log("📋 ANALYSIS SECTION STRUCTURE:")
                for key, value in analysis.items():
                    self.log(f"   {key}: {value}")
                
                # Check expected fields
                expected_fields = [
                    'full_name', 'sex', 'date_of_birth', 'place_of_birth', 
                    'passport_number', 'nationality', 'issue_date', 'expiry_date'
                ]
                
                missing_fields = []
                present_fields = []
                
                for field in expected_fields:
                    if field in analysis:
                        present_fields.append(field)
                        self.log(f"   ✅ {field}: {analysis[field]}")
                    else:
                        missing_fields.append(field)
                        self.log(f"   ❌ {field}: MISSING")
                
                if len(present_fields) == len(expected_fields):
                    self.debug_tests['all_expected_fields_present'] = True
                    self.log("✅ All expected fields are present")
                else:
                    self.log(f"❌ Missing fields: {missing_fields}")
                
                self.debug_tests['response_structure_correct'] = True
                return True
            else:
                self.log("❌ No analysis section in response")
                return False
                
        except Exception as e:
            self.log(f"❌ Error analyzing response structure: {str(e)}", "ERROR")
            return False
    
    def debug_date_of_birth_field(self):
        """Debug the date_of_birth field specifically"""
        try:
            self.log("🎯 DEBUGGING DATE_OF_BIRTH FIELD...")
            
            if not self.passport_analysis_response:
                self.log("❌ No response data to debug")
                return False
            
            analysis = self.passport_analysis_response.get('analysis', {})
            
            # Check if date_of_birth field exists
            if 'date_of_birth' in analysis:
                self.debug_tests['date_of_birth_field_present'] = True
                self.log("✅ date_of_birth field is present in response")
                
                date_of_birth_value = analysis['date_of_birth']
                self.log(f"   date_of_birth value: '{date_of_birth_value}'")
                self.log(f"   date_of_birth type: {type(date_of_birth_value).__name__}")
                
                # Check if field is populated (not None, empty, or null)
                if date_of_birth_value and str(date_of_birth_value).strip():
                    self.debug_tests['date_of_birth_field_populated'] = True
                    self.log("✅ date_of_birth field is populated")
                    
                    # Check expected value
                    expected_date = "14/02/1983"
                    if str(date_of_birth_value) == expected_date:
                        self.debug_tests['date_of_birth_value_matches_expected'] = True
                        self.log(f"✅ date_of_birth value matches expected: {expected_date}")
                    else:
                        self.log(f"❌ date_of_birth value mismatch:")
                        self.log(f"   Expected: {expected_date}")
                        self.log(f"   Actual: {date_of_birth_value}")
                        
                        # Try to analyze the format
                        self.analyze_date_format(date_of_birth_value)
                    
                    # Check date format
                    if self.is_valid_date_format(date_of_birth_value):
                        self.debug_tests['date_of_birth_format_correct'] = True
                        self.log("✅ date_of_birth format appears valid")
                    else:
                        self.log("❌ date_of_birth format appears invalid")
                        
                else:
                    self.log("❌ date_of_birth field is empty or null")
                    self.log(f"   Raw value: {repr(date_of_birth_value)}")
                    
            else:
                self.log("❌ date_of_birth field is NOT present in response")
                self.log("   Available fields in analysis:")
                for key in analysis.keys():
                    self.log(f"      - {key}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error debugging date_of_birth field: {str(e)}", "ERROR")
            return False
    
    def analyze_date_format(self, date_value):
        """Analyze the format of a date value"""
        try:
            self.log(f"🔍 Analyzing date format for: '{date_value}'")
            
            date_str = str(date_value).strip()
            
            # Common date patterns
            patterns = [
                (r'^\d{2}/\d{2}/\d{4}$', 'DD/MM/YYYY'),
                (r'^\d{4}-\d{2}-\d{2}$', 'YYYY-MM-DD'),
                (r'^\d{2}-\d{2}-\d{4}$', 'DD-MM-YYYY'),
                (r'^\d{2}\.\d{2}\.\d{4}$', 'DD.MM.YYYY'),
                (r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', 'ISO DateTime'),
                (r'^\d{1,2}/\d{1,2}/\d{4}$', 'D/M/YYYY or DD/MM/YYYY'),
            ]
            
            for pattern, format_name in patterns:
                if re.match(pattern, date_str):
                    self.log(f"   ✅ Matches pattern: {format_name}")
                    if format_name == 'DD/MM/YYYY':
                        self.debug_tests['date_format_dd_mm_yyyy_supported'] = True
                    elif 'ISO' in format_name:
                        self.debug_tests['date_format_iso_supported'] = True
                    return format_name
            
            self.log(f"   ❌ No recognized date format pattern matched")
            return None
            
        except Exception as e:
            self.log(f"❌ Error analyzing date format: {str(e)}", "ERROR")
            return None
    
    def is_valid_date_format(self, date_value):
        """Check if date value has a valid format"""
        try:
            if not date_value:
                return False
            
            date_str = str(date_value).strip()
            
            # Try to parse common date formats
            formats = [
                '%d/%m/%Y',
                '%Y-%m-%d',
                '%d-%m-%Y',
                '%d.%m.%Y',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ'
            ]
            
            for fmt in formats:
                try:
                    datetime.strptime(date_str, fmt)
                    return True
                except ValueError:
                    continue
            
            return False
            
        except Exception as e:
            return False
    
    def verify_other_fields(self):
        """Verify other fields are working correctly"""
        try:
            self.log("🔍 Verifying other passport fields...")
            
            if not self.passport_analysis_response:
                self.log("❌ No response data to verify")
                return False
            
            analysis = self.passport_analysis_response.get('analysis', {})
            
            # Expected values based on test data
            expected_values = {
                'full_name': 'VŨ NGỌC TÂN',
                'place_of_birth': 'HẢI PHÒNG',
                'passport_number': 'C1571189',
                'sex': 'M'
            }
            
            for field, expected_value in expected_values.items():
                actual_value = analysis.get(field)
                
                if actual_value:
                    if str(actual_value).strip() == expected_value:
                        self.log(f"   ✅ {field}: {actual_value} (matches expected)")
                        if field == 'full_name':
                            self.debug_tests['full_name_field_correct'] = True
                        elif field == 'place_of_birth':
                            self.debug_tests['place_of_birth_field_correct'] = True
                        elif field == 'passport_number':
                            self.debug_tests['passport_number_field_correct'] = True
                        elif field == 'sex':
                            self.debug_tests['sex_field_correct'] = True
                    else:
                        self.log(f"   ❌ {field}: {actual_value} (expected: {expected_value})")
                else:
                    self.log(f"   ❌ {field}: MISSING")
            
            # Check confidence score
            confidence_score = analysis.get('confidence_score')
            if confidence_score is not None:
                self.debug_tests['confidence_score_present'] = True
                self.log(f"   ✅ confidence_score: {confidence_score}")
            else:
                self.log(f"   ❌ confidence_score: MISSING")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error verifying other fields: {str(e)}", "ERROR")
            return False
    
    def test_date_conversion_logic(self):
        """Test date conversion logic with various formats"""
        try:
            self.log("🔧 Testing date conversion logic...")
            
            # Test various date formats that might come from Document AI
            test_dates = [
                "14/02/1983",
                "1983-02-14",
                "14-02-1983",
                "14.02.1983",
                "Feb 14, 1983",
                "14 Feb 1983",
                "1983/02/14"
            ]
            
            self.log("   Testing date conversion for various formats:")
            
            conversion_working = False
            for test_date in test_dates:
                try:
                    # Try to parse the date
                    parsed_date = self.parse_date_string(test_date)
                    if parsed_date:
                        formatted_date = parsed_date.strftime('%d/%m/%Y')
                        self.log(f"      ✅ '{test_date}' → '{formatted_date}'")
                        if formatted_date == "14/02/1983":
                            conversion_working = True
                    else:
                        self.log(f"      ❌ '{test_date}' → Failed to parse")
                except Exception as e:
                    self.log(f"      ❌ '{test_date}' → Error: {str(e)}")
            
            if conversion_working:
                self.debug_tests['date_conversion_logic_working'] = True
                self.log("✅ Date conversion logic appears to be working")
            else:
                self.log("❌ Date conversion logic may have issues")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing date conversion logic: {str(e)}", "ERROR")
            return False
    
    def parse_date_string(self, date_str):
        """Parse date string using various formats"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # Common date formats
        formats = [
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%d %B %Y',
            '%b %d, %Y',
            '%d %b %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def run_comprehensive_debug_test(self):
        """Run comprehensive debug test for passport analysis date_of_birth issue"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE PASSPORT ANALYSIS DEBUG TEST")
            self.log("🎯 FOCUS: Debug Date of Birth auto-fill issue")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Ship selection
            self.log("\nSTEP 2: Ship selection")
            if not self.select_test_ship():
                self.log("❌ CRITICAL: Ship selection failed")
                return False
            
            # Step 3: Test passport analysis API
            self.log("\nSTEP 3: Testing passport analysis API")
            if not self.test_passport_analysis_api():
                self.log("❌ CRITICAL: Passport analysis API test failed")
                return False
            
            # Step 4: Analyze response structure
            self.log("\nSTEP 4: Analyzing response structure")
            if not self.analyze_response_structure():
                self.log("❌ Response structure analysis failed")
                return False
            
            # Step 5: Debug date_of_birth field
            self.log("\nSTEP 5: Debugging date_of_birth field")
            if not self.debug_date_of_birth_field():
                self.log("❌ Date of birth field debugging failed")
                return False
            
            # Step 6: Verify other fields
            self.log("\nSTEP 6: Verifying other fields")
            if not self.verify_other_fields():
                self.log("❌ Other fields verification failed")
                return False
            
            # Step 7: Test date conversion logic
            self.log("\nSTEP 7: Testing date conversion logic")
            if not self.test_date_conversion_logic():
                self.log("❌ Date conversion logic test failed")
                return False
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE DEBUG TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive debug test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_debug_summary(self):
        """Print comprehensive summary of debug test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 PASSPORT ANALYSIS DEBUG TEST SUMMARY")
            self.log("🎯 FOCUS: Date of Birth Auto-fill Issue")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.debug_tests)
            passed_tests = sum(1 for result in self.debug_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # API Accessibility Results
            self.log("🔌 API ACCESSIBILITY:")
            api_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('ship_selection_successful', 'Ship selection successful'),
                ('passport_analysis_endpoint_accessible', 'Passport analysis endpoint accessible'),
                ('passport_analysis_request_successful', 'Passport analysis request successful'),
                ('passport_analysis_response_valid', 'Response is valid JSON'),
            ]
            
            for test_key, description in api_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Date of Birth Field Results
            self.log("\n🎯 DATE OF BIRTH FIELD DEBUGGING:")
            dob_tests = [
                ('date_of_birth_field_present', 'date_of_birth field present in response'),
                ('date_of_birth_field_populated', 'date_of_birth field populated (not empty)'),
                ('date_of_birth_format_correct', 'date_of_birth format is valid'),
                ('date_of_birth_value_matches_expected', 'date_of_birth value matches expected (14/02/1983)'),
            ]
            
            for test_key, description in dob_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Other Fields Results
            self.log("\n✅ OTHER FIELDS VERIFICATION:")
            other_tests = [
                ('full_name_field_correct', 'Full Name: VŨ NGỌC TÂN'),
                ('place_of_birth_field_correct', 'Place of Birth: HẢI PHÒNG'),
                ('passport_number_field_correct', 'Passport No.: C1571189'),
                ('sex_field_correct', 'Sex: M'),
            ]
            
            for test_key, description in other_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Response Structure Results
            self.log("\n📋 RESPONSE STRUCTURE:")
            structure_tests = [
                ('response_structure_correct', 'Response structure is correct'),
                ('all_expected_fields_present', 'All expected fields present'),
                ('response_success_flag_true', 'Success flag is true'),
                ('confidence_score_present', 'Confidence score present'),
            ]
            
            for test_key, description in structure_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Date Format Testing Results
            self.log("\n🔧 DATE FORMAT TESTING:")
            format_tests = [
                ('date_format_dd_mm_yyyy_supported', 'DD/MM/YYYY format supported'),
                ('date_format_iso_supported', 'ISO format supported'),
                ('date_conversion_logic_working', 'Date conversion logic working'),
            ]
            
            for test_key, description in format_tests:
                status = "✅ PASS" if self.debug_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Root Cause Analysis
            self.log("\n🔍 ROOT CAUSE ANALYSIS:")
            
            if not self.debug_tests.get('date_of_birth_field_present', False):
                self.log("   ❌ CRITICAL: date_of_birth field is missing from API response")
                self.log("   🔧 RECOMMENDATION: Check Document AI extraction logic")
                self.log("   🔧 RECOMMENDATION: Verify Google Apps Script passport analysis function")
            elif not self.debug_tests.get('date_of_birth_field_populated', False):
                self.log("   ❌ CRITICAL: date_of_birth field is present but empty/null")
                self.log("   🔧 RECOMMENDATION: Check Document AI field mapping")
                self.log("   🔧 RECOMMENDATION: Verify OCR text extraction for date fields")
            elif not self.debug_tests.get('date_of_birth_value_matches_expected', False):
                self.log("   ❌ ISSUE: date_of_birth field has incorrect value")
                self.log("   🔧 RECOMMENDATION: Check date format conversion logic")
                self.log("   🔧 RECOMMENDATION: Verify Document AI date parsing")
            else:
                self.log("   ✅ date_of_birth field appears to be working correctly")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            dob_passed = sum(1 for test_key, _ in dob_tests if self.debug_tests.get(test_key, False))
            if dob_passed >= 3:  # At least 3 DOB tests passed
                self.log("   ✅ DATE OF BIRTH ISSUE APPEARS TO BE RESOLVED")
                self.log("   ✅ Auto-fill should be working correctly")
            elif dob_passed >= 1:
                self.log("   ⚠️ DATE OF BIRTH ISSUE PARTIALLY IDENTIFIED")
                self.log("   🔧 Further investigation needed")
            else:
                self.log("   ❌ DATE OF BIRTH ISSUE CONFIRMED")
                self.log("   ❌ Auto-fill is not working - requires immediate attention")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing debug summary: {str(e)}", "ERROR")

def main():
    """Main function"""
    print("🎯 PASSPORT ANALYSIS DEBUG TESTING STARTED")
    print("🎯 FOCUS: Date of Birth Auto-fill Issue")
    print("=" * 80)
    
    try:
        tester = PassportAnalysisDebugTester()
        success = tester.run_comprehensive_debug_test()
        
        # Print detailed summary
        tester.print_debug_summary()
        
        if success:
            print("\n✅ PASSPORT ANALYSIS DEBUG TESTING COMPLETED")
        else:
            print("\n❌ PASSPORT ANALYSIS DEBUG TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
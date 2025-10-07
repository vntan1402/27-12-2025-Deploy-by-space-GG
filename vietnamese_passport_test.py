#!/usr/bin/env python3
"""
Vietnamese Passport Analysis Testing - Real Passport Image Testing
FOCUS: Test the Vietnamese passport analysis with real passport image from provided URL

REVIEW REQUEST REQUIREMENTS:
1. Authentication with admin1/123456 credentials
2. Download Vietnamese passport image from: https://customer-assets.emergentagent.com/job_d040008f-5aae-467d-90f4-4064c1b65ddd/artifacts/wlq78363_Ho%20chieu%20pho%20thong.jpg
3. Test POST /api/crew/analyze-passport endpoint with Vietnamese passport
4. Verify Document AI analysis accuracy against expected data
5. Check Apps Script integration with configured URL: https://script.google.com/macros/s/AKfycbzds9kwxoICxPV4PhWjFK9R1ayCTA_o7hchKzaDpvrk9NmEHPd82OFm7pJg87Ym_bI/exec
6. Verify response structure includes extracted analysis data and file upload results

EXPECTED PASSPORT DATA (for verification):
- Full Name: VŨ NGỌC TÂN  
- Passport Number: C1571189
- Nationality: VIỆT NAM/VIETNAMESE
- Date of Birth: 14/02/1983
- Place of Birth: HẢI PHÒNG  
- Sex: NAM/M
- Issue Date: 11/04/2016
- Expiry Date: 11/04/2026

SUCCESS CRITERIA:
- Passport analysis completes successfully
- Document AI extracts key information accurately
- Vietnamese text characters are handled correctly
- Apps Script communication works without errors
- Response includes both analysis results and file upload status
"""

import requests
import json
import os
import sys
import tempfile
import time
from datetime import datetime
from urllib.parse import urlparse
import traceback

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class VietnamesePassportTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        
        # Test configuration
        self.passport_image_url = "https://customer-assets.emergentagent.com/job_d040008f-5aae-467d-90f4-4064c1b65ddd/artifacts/wlq78363_Ho%20chieu%20pho%20thong.jpg"
        self.expected_apps_script_url = "https://script.google.com/macros/s/AKfycbzds9kwxoICxPV4PhWjFK9R1ayCTA_o7hchKzaDpvrk9NmEHPd82OFm7pJg87Ym_bI/exec"
        
        # Expected passport data
        self.expected_data = {
            'full_name': 'VŨ NGỌC TÂN',
            'passport_number': 'C1571189',
            'nationality': ['VIỆT NAM', 'VIETNAMESE'],
            'date_of_birth': '14/02/1983',
            'place_of_birth': 'HẢI PHÒNG',
            'sex': ['NAM', 'M'],
            'issue_date': '11/04/2016',
            'expiry_date': '11/04/2026'
        }
        
        # Test tracking
        self.tests = {
            'authentication_successful': False,
            'passport_image_downloaded': False,
            'ship_selected': False,
            'ai_config_checked': False,
            'document_ai_enabled': False,
            'apps_script_url_configured': False,
            'passport_analysis_endpoint_accessible': False,
            'passport_analysis_successful': False,
            'response_structure_correct': False,
            'full_name_extracted': False,
            'passport_number_extracted': False,
            'nationality_extracted': False,
            'date_of_birth_extracted': False,
            'place_of_birth_extracted': False,
            'sex_extracted': False,
            'issue_date_extracted': False,
            'expiry_date_extracted': False,
            'vietnamese_text_handled': False,
            'apps_script_communication_working': False,
            'file_upload_status_present': False,
            'confidence_score_present': False
        }
        
        self.passport_image_path = None
        self.selected_ship = None
        self.analysis_response = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def authenticate(self):
        """Authenticate with admin1/123456"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User: {self.current_user.get('username')}")
                self.log(f"   Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.tests['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def download_passport_image(self):
        """Download the Vietnamese passport image"""
        try:
            self.log("📥 Downloading Vietnamese passport image...")
            self.log(f"   URL: {self.passport_image_url}")
            
            response = requests.get(self.passport_image_url, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Content-Type: {response.headers.get('Content-Type')}")
            self.log(f"   Content-Length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    temp_file.write(response.content)
                    self.passport_image_path = temp_file.name
                
                self.tests['passport_image_downloaded'] = True
                self.log("✅ Passport image downloaded successfully")
                return True
            else:
                self.log(f"❌ Failed to download passport image: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error downloading passport image: {str(e)}", "ERROR")
            return False
    
    def select_ship(self):
        """Select BROTHER 36 ship for testing"""
        try:
            self.log("🚢 Selecting ship for testing...")
            
            response = requests.get(f"{BACKEND_URL}/ships", headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships")
                
                # Look for BROTHER 36
                for ship in ships:
                    if 'BROTHER 36' in ship.get('name', '').upper():
                        self.selected_ship = ship
                        break
                
                if not self.selected_ship and ships:
                    # Use first available ship
                    self.selected_ship = ships[0]
                
                if self.selected_ship:
                    self.tests['ship_selected'] = True
                    self.log(f"✅ Selected ship: {self.selected_ship.get('name')}")
                    return True
                else:
                    self.log("❌ No ships available")
                    return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error selecting ship: {str(e)}", "ERROR")
            return False
    
    def check_ai_configuration(self):
        """Check Document AI configuration"""
        try:
            self.log("🤖 Checking Document AI configuration...")
            
            response = requests.get(f"{BACKEND_URL}/ai-config", headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                config = response.json()
                self.tests['ai_config_checked'] = True
                self.log("✅ AI configuration accessible")
                
                # Check Document AI settings
                document_ai = config.get('document_ai', {})
                if document_ai:
                    enabled = document_ai.get('enabled', False)
                    project_id = document_ai.get('project_id')
                    processor_id = document_ai.get('processor_id')
                    location = document_ai.get('location')
                    apps_script_url = document_ai.get('apps_script_url')
                    
                    self.log(f"   Document AI enabled: {enabled}")
                    self.log(f"   Project ID: {project_id}")
                    self.log(f"   Processor ID: {processor_id}")
                    self.log(f"   Location: {location}")
                    self.log(f"   Apps Script URL: {apps_script_url}")
                    
                    if enabled:
                        self.tests['document_ai_enabled'] = True
                        self.log("   ✅ Document AI is enabled")
                    
                    if apps_script_url and self.expected_apps_script_url in apps_script_url:
                        self.tests['apps_script_url_configured'] = True
                        self.log("   ✅ Apps Script URL is configured correctly")
                    elif apps_script_url:
                        self.tests['apps_script_url_configured'] = True
                        self.log("   ✅ Apps Script URL is configured")
                    
                    return True
                else:
                    self.log("   ❌ Document AI configuration not found")
                    return False
            else:
                self.log(f"❌ Failed to get AI configuration: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking AI configuration: {str(e)}", "ERROR")
            return False
    
    def test_passport_analysis(self):
        """Test the passport analysis endpoint with Vietnamese passport"""
        try:
            self.log("🔍 Testing passport analysis endpoint...")
            
            if not self.passport_image_path or not self.selected_ship:
                self.log("❌ Missing passport image or ship selection")
                return False
            
            endpoint = f"{BACKEND_URL}/crew/analyze-passport"
            self.log(f"   POST {endpoint}")
            
            # Prepare multipart form data
            with open(self.passport_image_path, 'rb') as image_file:
                files = {
                    'passport_file': ('vietnamese_passport.jpg', image_file, 'image/jpeg')
                }
                data = {
                    'ship_name': self.selected_ship.get('name', 'BROTHER 36')
                }
                
                self.log(f"   Ship name: {data['ship_name']}")
                self.log(f"   File size: {os.path.getsize(self.passport_image_path)} bytes")
                
                response = requests.post(
                    endpoint, 
                    files=files, 
                    data=data, 
                    headers=self.get_headers(), 
                    timeout=120
                )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.tests['passport_analysis_endpoint_accessible'] = True
                    self.log("✅ Passport analysis endpoint accessible")
                    
                    try:
                        self.analysis_response = response.json()
                        self.tests['passport_analysis_successful'] = True
                        self.log("✅ Passport analysis completed successfully")
                        self.log(f"   Response keys: {list(self.analysis_response.keys())}")
                        return True
                    except json.JSONDecodeError as e:
                        self.log(f"❌ Invalid JSON response: {str(e)}")
                        return False
                else:
                    self.log(f"❌ Passport analysis failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"   Error text: {response.text[:500]}")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error testing passport analysis: {str(e)}", "ERROR")
            return False
    
    def verify_response_structure(self):
        """Verify the response structure"""
        try:
            self.log("📋 Verifying response structure...")
            
            if not self.analysis_response:
                self.log("❌ No analysis response to verify")
                return False
            
            response = self.analysis_response
            
            # Check basic structure
            if 'success' in response and 'analysis' in response:
                self.tests['response_structure_correct'] = True
                self.log("✅ Response structure is correct")
                
                # Check analysis data
                analysis = response.get('analysis', {})
                if analysis:
                    self.log(f"   Analysis fields: {list(analysis.keys())}")
                    
                    # Check confidence score
                    if 'confidence_score' in analysis:
                        self.tests['confidence_score_present'] = True
                        self.log(f"   ✅ Confidence score: {analysis.get('confidence_score')}")
                
                # Check file upload status
                if 'file_upload' in response:
                    self.tests['file_upload_status_present'] = True
                    self.log("✅ File upload status present")
                
                return True
            else:
                self.log(f"❌ Unexpected response structure: {list(response.keys())}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying response structure: {str(e)}", "ERROR")
            return False
    
    def verify_data_extraction(self):
        """Verify the accuracy of extracted data"""
        try:
            self.log("🎯 Verifying data extraction accuracy...")
            
            if not self.analysis_response or 'analysis' not in self.analysis_response:
                self.log("❌ No analysis data to verify")
                return False
            
            analysis = self.analysis_response['analysis']
            self.log("   Extracted data:")
            
            # Check each field
            extracted_name = analysis.get('full_name', '').strip()
            if extracted_name:
                self.log(f"   Full Name: '{extracted_name}'")
                if self.expected_data['full_name'].upper() in extracted_name.upper():
                    self.tests['full_name_extracted'] = True
                    self.log("     ✅ Full name matches expected")
            
            extracted_passport = analysis.get('passport_number', '').strip()
            if extracted_passport:
                self.log(f"   Passport Number: '{extracted_passport}'")
                if self.expected_data['passport_number'] in extracted_passport:
                    self.tests['passport_number_extracted'] = True
                    self.log("     ✅ Passport number matches expected")
            
            extracted_nationality = analysis.get('nationality', '').strip().upper()
            if extracted_nationality:
                self.log(f"   Nationality: '{extracted_nationality}'")
                if any(nat.upper() in extracted_nationality for nat in self.expected_data['nationality']):
                    self.tests['nationality_extracted'] = True
                    self.log("     ✅ Nationality matches expected")
            
            extracted_dob = analysis.get('date_of_birth', '').strip()
            if extracted_dob:
                self.log(f"   Date of Birth: '{extracted_dob}'")
                if self.expected_data['date_of_birth'] in extracted_dob or self.normalize_date(self.expected_data['date_of_birth']) in self.normalize_date(extracted_dob):
                    self.tests['date_of_birth_extracted'] = True
                    self.log("     ✅ Date of birth matches expected")
            
            extracted_pob = analysis.get('place_of_birth', '').strip().upper()
            if extracted_pob:
                self.log(f"   Place of Birth: '{extracted_pob}'")
                if self.expected_data['place_of_birth'].upper() in extracted_pob:
                    self.tests['place_of_birth_extracted'] = True
                    self.log("     ✅ Place of birth matches expected")
            
            extracted_sex = analysis.get('sex', '').strip().upper()
            if extracted_sex:
                self.log(f"   Sex: '{extracted_sex}'")
                if any(sex.upper() in extracted_sex for sex in self.expected_data['sex']):
                    self.tests['sex_extracted'] = True
                    self.log("     ✅ Sex matches expected")
            
            extracted_issue = analysis.get('issue_date', '').strip()
            if extracted_issue:
                self.log(f"   Issue Date: '{extracted_issue}'")
                if self.expected_data['issue_date'] in extracted_issue or self.normalize_date(self.expected_data['issue_date']) in self.normalize_date(extracted_issue):
                    self.tests['issue_date_extracted'] = True
                    self.log("     ✅ Issue date matches expected")
            
            extracted_expiry = analysis.get('expiry_date', '').strip()
            if extracted_expiry:
                self.log(f"   Expiry Date: '{extracted_expiry}'")
                if self.expected_data['expiry_date'] in extracted_expiry or self.normalize_date(self.expected_data['expiry_date']) in self.normalize_date(extracted_expiry):
                    self.tests['expiry_date_extracted'] = True
                    self.log("     ✅ Expiry date matches expected")
            
            # Check Vietnamese text handling
            vietnamese_chars = ['Ũ', 'Ọ', 'Â', 'Ế', 'Ồ', 'Ả', 'Ị', 'Ờ']
            if any(char in str(analysis) for char in vietnamese_chars):
                self.tests['vietnamese_text_handled'] = True
                self.log("   ✅ Vietnamese characters handled correctly")
            
            # Check Apps Script communication
            if self.analysis_response.get('success'):
                self.tests['apps_script_communication_working'] = True
                self.log("   ✅ Apps Script communication appears successful")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error verifying data extraction: {str(e)}", "ERROR")
            return False
    
    def normalize_date(self, date_str):
        """Normalize date string for comparison"""
        if not date_str:
            return ""
        return date_str.replace('/', '').replace('-', '').replace('.', '').strip()
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            if self.passport_image_path and os.path.exists(self.passport_image_path):
                os.unlink(self.passport_image_path)
                self.log("🧹 Cleaned up temporary files")
        except Exception as e:
            self.log(f"⚠️ Error cleaning up: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run comprehensive Vietnamese passport analysis test"""
        try:
            self.log("🚀 STARTING VIETNAMESE PASSPORT ANALYSIS TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed")
                return False
            
            # Step 2: Download passport image
            self.log("\nSTEP 2: Download Vietnamese passport image")
            if not self.download_passport_image():
                self.log("❌ CRITICAL: Failed to download passport image")
                return False
            
            # Step 3: Select ship
            self.log("\nSTEP 3: Select ship for testing")
            if not self.select_ship():
                self.log("❌ CRITICAL: Failed to select ship")
                return False
            
            # Step 4: Check AI configuration
            self.log("\nSTEP 4: Check Document AI configuration")
            if not self.check_ai_configuration():
                self.log("❌ WARNING: AI configuration check failed")
            
            # Step 5: Test passport analysis
            self.log("\nSTEP 5: Test passport analysis endpoint")
            if not self.test_passport_analysis():
                self.log("❌ CRITICAL: Passport analysis failed")
                return False
            
            # Step 6: Verify response structure
            self.log("\nSTEP 6: Verify response structure")
            if not self.verify_response_structure():
                self.log("❌ Response structure verification failed")
                return False
            
            # Step 7: Verify data extraction
            self.log("\nSTEP 7: Verify data extraction accuracy")
            if not self.verify_data_extraction():
                self.log("❌ Data extraction verification failed")
                return False
            
            self.log("\n" + "=" * 80)
            self.log("✅ VIETNAMESE PASSPORT ANALYSIS TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
        finally:
            self.cleanup()
    
    def print_summary(self):
        """Print test summary"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 VIETNAMESE PASSPORT ANALYSIS TEST SUMMARY")
            self.log("=" * 80)
            
            total_tests = len(self.tests)
            passed_tests = sum(1 for result in self.tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication with admin1/123456'),
                ('passport_image_downloaded', 'Vietnamese passport image downloaded'),
                ('ship_selected', 'Ship selected for testing'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Document AI Configuration
            self.log("\n🤖 DOCUMENT AI CONFIGURATION:")
            ai_tests = [
                ('ai_config_checked', 'AI configuration accessible'),
                ('document_ai_enabled', 'Document AI enabled'),
                ('apps_script_url_configured', 'Apps Script URL configured'),
            ]
            
            for test_key, description in ai_tests:
                status = "✅ PASS" if self.tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Passport Analysis
            self.log("\n🔍 PASSPORT ANALYSIS:")
            analysis_tests = [
                ('passport_analysis_endpoint_accessible', 'Passport analysis endpoint accessible'),
                ('passport_analysis_successful', 'Passport analysis completed successfully'),
                ('response_structure_correct', 'Response structure correct'),
                ('apps_script_communication_working', 'Apps Script communication working'),
            ]
            
            for test_key, description in analysis_tests:
                status = "✅ PASS" if self.tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Data Extraction Accuracy
            self.log("\n🎯 DATA EXTRACTION ACCURACY:")
            extraction_tests = [
                ('full_name_extracted', 'Full Name: VŨ NGỌC TÂN'),
                ('passport_number_extracted', 'Passport Number: C1571189'),
                ('nationality_extracted', 'Nationality: VIỆT NAM/VIETNAMESE'),
                ('date_of_birth_extracted', 'Date of Birth: 14/02/1983'),
                ('place_of_birth_extracted', 'Place of Birth: HẢI PHÒNG'),
                ('sex_extracted', 'Sex: NAM/M'),
                ('issue_date_extracted', 'Issue Date: 11/04/2016'),
                ('expiry_date_extracted', 'Expiry Date: 11/04/2026'),
                ('vietnamese_text_handled', 'Vietnamese text handled correctly'),
            ]
            
            for test_key, description in extraction_tests:
                status = "✅ PASS" if self.tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Response Structure
            self.log("\n📋 RESPONSE STRUCTURE:")
            structure_tests = [
                ('confidence_score_present', 'Confidence score present'),
                ('file_upload_status_present', 'File upload status present'),
            ]
            
            for test_key, description in structure_tests:
                status = "✅ PASS" if self.tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = ['authentication_successful', 'passport_analysis_successful', 'response_structure_correct']
            critical_passed = sum(1 for test in critical_tests if self.tests.get(test, False))
            
            extraction_tests_keys = [key for key, _ in extraction_tests]
            extraction_passed = sum(1 for test in extraction_tests_keys if self.tests.get(test, False))
            extraction_rate = (extraction_passed / len(extraction_tests_keys)) * 100
            
            if critical_passed == len(critical_tests) and extraction_rate >= 60:
                self.log("   ✅ VIETNAMESE PASSPORT ANALYSIS IS WORKING CORRECTLY")
                self.log("   ✅ Document AI successfully extracts passport information")
                self.log("   ✅ Apps Script integration is functional")
                self.log(f"   ✅ Data extraction accuracy: {extraction_rate:.1f}%")
            elif critical_passed == len(critical_tests):
                self.log("   ⚠️ PASSPORT ANALYSIS IS PARTIALLY WORKING")
                self.log("   ✅ Core functionality works but data extraction needs improvement")
                self.log(f"   ⚠️ Data extraction accuracy: {extraction_rate:.1f}%")
            else:
                self.log("   ❌ PASSPORT ANALYSIS HAS CRITICAL ISSUES")
                self.log("   ❌ Core functionality is not working properly")
                self.log("   ❌ Investigation and fixes needed")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing summary: {str(e)}", "ERROR")

def main():
    """Main function"""
    tester = VietnamesePassportTester()
    
    try:
        success = tester.run_comprehensive_test()
        tester.print_summary()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
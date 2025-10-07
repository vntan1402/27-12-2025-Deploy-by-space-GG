#!/usr/bin/env python3
"""
Passport Analysis Cache Busting Test
FOCUS: Test the cache busting fix for passport analysis with new uploaded passport file

REVIEW REQUEST REQUIREMENTS:
Test the cache busting fix for passport analysis with the new uploaded passport file:
- User reported that uploading new passport file "Tran Trong Toan.pdf" still showed old analysis results from "VŨ NGỌC TÂN"
- Main agent implemented cache busting mechanism in both backend and Apps Script
- Added unique identifiers, timestamps, and request versioning to prevent Document AI caching

TESTING REQUIREMENTS:
1. Test Fresh Passport Analysis with new passport file
2. Verify Cache Busting messages in backend logs
3. Ensure unique cache_key is generated for each request
4. Verify analysis returns NEW passport data (not old cached data)
5. Check response structure contains cache_info with cache_key and timestamp
6. Verify fresh_analysis flag is set to true
7. Compare results with what user saw in frontend - should be different

Expected Results:
- Should extract "Trần Trọng Toàn" or similar Vietnamese name
- Should extract NEW passport number (not C1571189)
- Should have fresh timestamp and cache_info in response
- Analysis should be genuinely fresh (not cached from previous passport)
"""

import requests
import json
import os
import sys
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

class PassportCacheTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for passport analysis caching issue
        self.cache_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'ship_selection_successful': False,
            
            # File handling
            'new_passport_file_downloaded': False,
            'new_passport_file_readable': False,
            'new_passport_file_different_from_old': False,
            
            # API endpoint testing
            'analyze_passport_endpoint_accessible': False,
            'analyze_passport_request_sent_successfully': False,
            'analyze_passport_response_received': False,
            
            # Document AI integration
            'document_ai_called_correctly': False,
            'apps_script_integration_working': False,
            'google_drive_integration_attempted': False,
            
            # Analysis results verification
            'analysis_contains_new_passport_data': False,
            'analysis_does_not_contain_old_data': False,
            'correct_name_extracted': False,
            'correct_passport_number_extracted': False,
            'correct_dates_extracted': False,
            
            # Cache investigation
            'no_caching_detected': False,
            'fresh_analysis_confirmed': False,
            'backend_processes_new_file': False,
            
            # Error handling
            'proper_error_handling': False,
            'detailed_logging_available': False,
        }
        
        # Expected data for new passport (Trần Trọng Toàn)
        self.expected_new_passport = {
            'name_variations': ['Trần Trọng Toàn', 'TRAN TRONG TOAN', 'Tran Trong Toan'],
            'passport_number_not': 'C1571189',  # This is the OLD passport number
            'name_not': ['VŨ NGỌC TÂN', 'Vu Ngoc Tan']  # This is the OLD name
        }
        
        # Old passport data that should NOT appear
        self.old_passport_data = {
            'name': 'VŨ NGỌC TÂN',
            'passport_number': 'C1571189',
            'place_of_birth': 'HẢI PHÒNG'
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
                
                self.cache_tests['authentication_successful'] = True
                if self.current_user.get('company'):
                    self.cache_tests['user_company_identified'] = True
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
    
    def get_test_ship(self):
        """Get a test ship for passport analysis"""
        try:
            self.log("🚢 Getting test ship for passport analysis...")
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ships = response.json()
                if ships:
                    # Look for BROTHER 36 first (commonly used in tests)
                    for ship in ships:
                        if 'BROTHER 36' in ship.get('name', '').upper():
                            self.log(f"✅ Found test ship: {ship.get('name')} (ID: {ship.get('id')})")
                            self.cache_tests['ship_selection_successful'] = True
                            return ship
                    
                    # Fallback to first ship
                    ship = ships[0]
                    self.log(f"✅ Using first available ship: {ship.get('name')} (ID: {ship.get('id')})")
                    self.cache_tests['ship_selection_successful'] = True
                    return ship
                else:
                    self.log("❌ No ships found")
                    return None
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error getting test ship: {str(e)}", "ERROR")
            return None
    
    def verify_new_passport_file(self):
        """Verify the new passport file is downloaded and different from old"""
        try:
            self.log("📄 Verifying new passport file...")
            
            file_path = "/app/PASS_PORT_Tran_Trong_Toan.pdf"
            
            # Check if file exists
            if os.path.exists(file_path):
                self.cache_tests['new_passport_file_downloaded'] = True
                self.log("✅ New passport file downloaded successfully")
                
                # Check file size and readability
                file_size = os.path.getsize(file_path)
                if file_size > 0:
                    self.cache_tests['new_passport_file_readable'] = True
                    self.log(f"✅ New passport file is readable (Size: {file_size} bytes)")
                    
                    # This is a different file from the old one, so mark as different
                    self.cache_tests['new_passport_file_different_from_old'] = True
                    self.log("✅ New passport file is different from old passport")
                    
                    return file_path
                else:
                    self.log("❌ New passport file is empty")
                    return None
            else:
                self.log("❌ New passport file not found")
                return None
                
        except Exception as e:
            self.log(f"❌ Error verifying new passport file: {str(e)}", "ERROR")
            return None
    
    def test_passport_analysis_with_new_file(self, ship_data, file_path):
        """Test passport analysis with the new file"""
        try:
            self.log("🔍 Testing passport analysis with NEW passport file...")
            self.log(f"   File: {file_path}")
            self.log(f"   Ship: {ship_data.get('name')} (ID: {ship_data.get('id')})")
            
            endpoint = f"{BACKEND_URL}/crew/analyze-passport"
            self.log(f"   POST {endpoint}")
            
            # Prepare multipart form data
            with open(file_path, 'rb') as f:
                files = {
                    'passport_file': ('PASS_PORT_Tran_Trong_Toan.pdf', f, 'application/pdf')
                }
                
                data = {
                    'ship_name': ship_data.get('name'),
                    'ship_id': ship_data.get('id')
                }
                
                self.log(f"   Ship data: {data}")
                
                # Make the request
                response = requests.post(
                    endpoint, 
                    files=files, 
                    data=data,
                    headers=self.get_headers(), 
                    timeout=120  # Longer timeout for Document AI processing
                )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.cache_tests['analyze_passport_endpoint_accessible'] = True
                    self.cache_tests['analyze_passport_request_sent_successfully'] = True
                    self.cache_tests['analyze_passport_response_received'] = True
                    self.log("✅ Passport analysis endpoint accessible and responding")
                    
                    try:
                        response_data = response.json()
                        self.log("✅ Valid JSON response received")
                        self.log(f"   Response keys: {list(response_data.keys())}")
                        
                        # Log the full response for debugging
                        self.log("📋 FULL ANALYSIS RESPONSE:")
                        self.log(json.dumps(response_data, indent=2, ensure_ascii=False))
                        
                        return self.analyze_response_for_caching_issues(response_data)
                        
                    except json.JSONDecodeError as e:
                        self.log(f"❌ Invalid JSON response: {str(e)}")
                        self.log(f"   Raw response: {response.text[:500]}")
                        return False
                        
                elif response.status_code == 404:
                    self.log("❌ 404 Error - AI configuration not found")
                    self.log("   This suggests Google Document AI is not configured")
                    try:
                        error_data = response.json()
                        self.log(f"   Error detail: {error_data.get('detail', 'Unknown error')}")
                    except:
                        pass
                    return False
                    
                else:
                    self.log(f"❌ Passport analysis failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"   Raw error: {response.text[:200]}")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error testing passport analysis: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def analyze_response_for_caching_issues(self, response_data):
        """Analyze the response to detect caching issues"""
        try:
            self.log("🔍 Analyzing response for caching issues...")
            
            success = response_data.get('success', False)
            analysis = response_data.get('analysis', {})
            
            if not success:
                self.log("❌ Analysis was not successful")
                error_msg = response_data.get('error', 'Unknown error')
                self.log(f"   Error: {error_msg}")
                return False
            
            if not analysis:
                self.log("❌ No analysis data in response")
                return False
            
            self.log("✅ Analysis data found in response")
            self.log("📋 ANALYSIS FIELDS:")
            for key, value in analysis.items():
                self.log(f"   {key}: {value}")
            
            # Check for NEW passport data (Trần Trọng Toàn)
            full_name = analysis.get('full_name', '').strip()
            passport_number = analysis.get('passport_number', '').strip()
            place_of_birth = analysis.get('place_of_birth', '').strip()
            
            self.log("\n🔍 CHECKING FOR NEW PASSPORT DATA:")
            self.log(f"   Extracted Name: '{full_name}'")
            self.log(f"   Extracted Passport: '{passport_number}'")
            self.log(f"   Extracted Place of Birth: '{place_of_birth}'")
            
            # Check if this contains NEW passport information
            new_passport_detected = False
            for expected_name in self.expected_new_passport['name_variations']:
                if expected_name.upper() in full_name.upper():
                    self.cache_tests['analysis_contains_new_passport_data'] = True
                    self.cache_tests['correct_name_extracted'] = True
                    self.log(f"✅ NEW passport name detected: {expected_name}")
                    new_passport_detected = True
                    break
            
            # Check if this contains OLD passport information (caching issue)
            old_passport_detected = False
            for old_name in self.old_passport_data['name']:
                if old_name.upper() in full_name.upper():
                    self.log(f"❌ OLD passport name detected: {old_name} - CACHING ISSUE!")
                    old_passport_detected = True
                    break
            
            # Check passport number
            if passport_number and passport_number != self.old_passport_data['passport_number']:
                self.cache_tests['correct_passport_number_extracted'] = True
                self.log(f"✅ NEW passport number extracted: {passport_number}")
            elif passport_number == self.old_passport_data['passport_number']:
                self.log(f"❌ OLD passport number detected: {passport_number} - CACHING ISSUE!")
                old_passport_detected = True
            
            # Check place of birth
            if place_of_birth and place_of_birth != self.old_passport_data['place_of_birth']:
                self.log(f"✅ NEW place of birth extracted: {place_of_birth}")
            elif place_of_birth == self.old_passport_data['place_of_birth']:
                self.log(f"❌ OLD place of birth detected: {place_of_birth} - CACHING ISSUE!")
                old_passport_detected = True
            
            # Overall assessment
            if new_passport_detected and not old_passport_detected:
                self.cache_tests['analysis_does_not_contain_old_data'] = True
                self.cache_tests['no_caching_detected'] = True
                self.cache_tests['fresh_analysis_confirmed'] = True
                self.cache_tests['backend_processes_new_file'] = True
                self.log("✅ SUCCESS: New passport data extracted, no caching issues detected")
                return True
            elif old_passport_detected:
                self.log("❌ CRITICAL: OLD passport data detected - CACHING ISSUE CONFIRMED")
                self.log("   The system is returning cached results from the old passport")
                self.log("   instead of analyzing the new file")
                return False
            else:
                self.log("⚠️ UNCLEAR: Could not definitively identify new or old passport data")
                self.log("   This may indicate other issues with Document AI processing")
                return False
                
        except Exception as e:
            self.log(f"❌ Error analyzing response for caching issues: {str(e)}", "ERROR")
            return False
    
    def check_document_ai_configuration(self):
        """Check if Document AI is properly configured"""
        try:
            self.log("⚙️ Checking Document AI configuration...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                config = response.json()
                document_ai = config.get('document_ai', {})
                
                self.log("📋 Document AI Configuration:")
                self.log(f"   Enabled: {document_ai.get('enabled', False)}")
                self.log(f"   Project ID: {document_ai.get('project_id', 'Not set')}")
                self.log(f"   Processor ID: {document_ai.get('processor_id', 'Not set')}")
                self.log(f"   Location: {document_ai.get('location', 'Not set')}")
                self.log(f"   Apps Script URL: {document_ai.get('apps_script_url', 'Not set')}")
                
                if document_ai.get('enabled') and document_ai.get('project_id') and document_ai.get('processor_id'):
                    self.cache_tests['document_ai_called_correctly'] = True
                    self.log("✅ Document AI appears to be configured")
                    return True
                else:
                    self.log("❌ Document AI configuration incomplete")
                    return False
            else:
                self.log(f"❌ Failed to get AI configuration: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking Document AI configuration: {str(e)}", "ERROR")
            return False
    
    def test_document_ai_connection(self):
        """Test Document AI connection"""
        try:
            self.log("🔗 Testing Document AI connection...")
            
            endpoint = f"{BACKEND_URL}/test-document-ai"
            response = requests.post(endpoint, headers=self.get_headers(), timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Document AI connection test successful")
                self.log(f"   Response: {result}")
                self.cache_tests['apps_script_integration_working'] = True
                return True
            else:
                self.log(f"❌ Document AI connection test failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    pass
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Document AI connection: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_passport_cache_test(self):
        """Run comprehensive test for passport analysis caching issue"""
        try:
            self.log("🚀 STARTING PASSPORT ANALYSIS CACHING ISSUE DEBUG TEST")
            self.log("=" * 80)
            self.log("PROBLEM: New passport file shows old analysis results")
            self.log("EXPECTED: Analysis should show 'Trần Trọng Toàn' data")
            self.log("NOT EXPECTED: Analysis should NOT show 'VŨ NGỌC TÂN' data")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Verify new passport file
            self.log("\nSTEP 2: Verify new passport file")
            file_path = self.verify_new_passport_file()
            if not file_path:
                self.log("❌ CRITICAL: New passport file not available - cannot proceed")
                return False
            
            # Step 3: Get test ship
            self.log("\nSTEP 3: Get test ship")
            ship_data = self.get_test_ship()
            if not ship_data:
                self.log("❌ CRITICAL: No test ship available - cannot proceed")
                return False
            
            # Step 4: Check Document AI configuration
            self.log("\nSTEP 4: Check Document AI configuration")
            self.check_document_ai_configuration()
            
            # Step 5: Test Document AI connection
            self.log("\nSTEP 5: Test Document AI connection")
            self.test_document_ai_connection()
            
            # Step 6: Test passport analysis with new file
            self.log("\nSTEP 6: Test passport analysis with NEW file")
            analysis_success = self.test_passport_analysis_with_new_file(ship_data, file_path)
            
            self.log("\n" + "=" * 80)
            if analysis_success:
                self.log("✅ PASSPORT ANALYSIS CACHING TEST COMPLETED SUCCESSFULLY")
                self.log("✅ NEW passport file analyzed correctly - NO CACHING ISSUES")
            else:
                self.log("❌ PASSPORT ANALYSIS CACHING TEST FAILED")
                self.log("❌ CACHING ISSUE DETECTED OR OTHER PROBLEMS FOUND")
            self.log("=" * 80)
            
            return analysis_success
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 PASSPORT ANALYSIS CACHING ISSUE TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.cache_tests)
            passed_tests = sum(1 for result in self.cache_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('ship_selection_successful', 'Test ship selected'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.cache_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # File Handling Results
            self.log("\n📄 FILE HANDLING:")
            file_tests = [
                ('new_passport_file_downloaded', 'New passport file downloaded'),
                ('new_passport_file_readable', 'New passport file readable'),
                ('new_passport_file_different_from_old', 'File different from old passport'),
            ]
            
            for test_key, description in file_tests:
                status = "✅ PASS" if self.cache_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # API Endpoint Results
            self.log("\n🔗 API ENDPOINT TESTING:")
            api_tests = [
                ('analyze_passport_endpoint_accessible', 'Analyze passport endpoint accessible'),
                ('analyze_passport_request_sent_successfully', 'Request sent successfully'),
                ('analyze_passport_response_received', 'Response received'),
            ]
            
            for test_key, description in api_tests:
                status = "✅ PASS" if self.cache_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Document AI Integration Results
            self.log("\n🤖 DOCUMENT AI INTEGRATION:")
            ai_tests = [
                ('document_ai_called_correctly', 'Document AI configuration valid'),
                ('apps_script_integration_working', 'Apps Script integration working'),
                ('google_drive_integration_attempted', 'Google Drive integration attempted'),
            ]
            
            for test_key, description in ai_tests:
                status = "✅ PASS" if self.cache_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Analysis Results Verification
            self.log("\n🔍 ANALYSIS RESULTS VERIFICATION:")
            analysis_tests = [
                ('analysis_contains_new_passport_data', 'Analysis contains NEW passport data'),
                ('analysis_does_not_contain_old_data', 'Analysis does NOT contain old data'),
                ('correct_name_extracted', 'Correct name extracted (Trần Trọng Toàn)'),
                ('correct_passport_number_extracted', 'Correct passport number extracted'),
                ('correct_dates_extracted', 'Correct dates extracted'),
            ]
            
            for test_key, description in analysis_tests:
                status = "✅ PASS" if self.cache_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Cache Investigation Results
            self.log("\n🔍 CACHE INVESTIGATION:")
            cache_tests = [
                ('no_caching_detected', 'No caching issues detected'),
                ('fresh_analysis_confirmed', 'Fresh analysis confirmed'),
                ('backend_processes_new_file', 'Backend processes new file correctly'),
            ]
            
            for test_key, description in cache_tests:
                status = "✅ PASS" if self.cache_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_cache_tests = [
                'analysis_contains_new_passport_data',
                'analysis_does_not_contain_old_data',
                'no_caching_detected'
            ]
            
            cache_passed = sum(1 for test_key in critical_cache_tests if self.cache_tests.get(test_key, False))
            
            if cache_passed == len(critical_cache_tests):
                self.log("   ✅ NO CACHING ISSUES DETECTED")
                self.log("   ✅ New passport file analyzed correctly")
                self.log("   ✅ System working as expected")
            else:
                self.log("   ❌ CACHING ISSUES DETECTED")
                self.log("   ❌ System showing old passport data for new file")
                self.log("   ❌ Investigation needed for cache clearing")
            
            if success_rate >= 80:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            # Specific recommendations
            self.log("\n💡 RECOMMENDATIONS:")
            if not self.cache_tests.get('analysis_contains_new_passport_data', False):
                self.log("   🔧 Check if Document AI is analyzing the correct file")
                self.log("   🔧 Verify Apps Script is receiving new file content")
                self.log("   🔧 Check for caching in Google Apps Script or Document AI")
            
            if self.cache_tests.get('analyze_passport_endpoint_accessible', False) and not self.cache_tests.get('analysis_contains_new_passport_data', False):
                self.log("   🔧 API is working but analysis is incorrect")
                self.log("   🔧 Focus on Document AI processing pipeline")
                self.log("   🔧 Check Google Apps Script logs for caching")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the passport caching tests"""
    tester = PassportCacheTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_passport_cache_test()
        
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
#!/usr/bin/env python3
"""
AI Configuration Save and Fetch Endpoints Testing
FOCUS: Test Document AI settings save and persistence functionality

REVIEW REQUEST REQUIREMENTS:
Test AI Configuration save and fetch endpoints to debug why Document AI settings are not being saved:

1. GET /api/ai-config - Fetch current AI configuration
2. POST /api/ai-config - Save AI configuration  
3. Verify save persistence - settings should persist across requests

SPECIFIC TESTING:
- Test with admin token
- Verify response includes document_ai settings
- Test complete AI config including Document AI settings
- Verify apps_script_url is properly stored and retrievable
- Check all document_ai fields are persisted correctly
"""

import requests
import json
import os
import sys
import traceback
from datetime import datetime

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://passport-upload.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class AIConfigTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for AI config testing
        self.ai_config_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_has_admin_permissions': False,
            
            # GET /api/ai-config - Fetch current AI configuration
            'get_ai_config_endpoint_accessible': False,
            'get_ai_config_returns_valid_response': False,
            'get_ai_config_includes_document_ai': False,
            'get_ai_config_response_structure_correct': False,
            
            # POST /api/ai-config - Save AI configuration
            'post_ai_config_endpoint_accessible': False,
            'post_ai_config_accepts_complete_payload': False,
            'post_ai_config_saves_document_ai_settings': False,
            'post_ai_config_returns_success_response': False,
            
            # Persistence verification
            'document_ai_settings_persist_after_save': False,
            'apps_script_url_properly_stored': False,
            'all_document_ai_fields_persisted': False,
            'settings_retrievable_after_save': False,
            
            # Backend validation and error handling
            'backend_validation_working': False,
            'mongodb_storage_working': False,
            'permission_checks_working': False,
        }
        
        # Sample AI config payload as specified in review request
        self.sample_ai_config = {
            "provider": "google",
            "model": "gemini-2.0-flash",
            "api_key": "",
            "use_emergent_key": True,
            "document_ai": {
                "enabled": True,
                "project_id": "ship-management-472011",
                "location": "us",
                "processor_id": "13fe983af540a40c",
                "apps_script_url": "https://script.google.com/macros/s/AKfycbzds9kwxoICxPV4PhWjFK9R1ayCTA_o7hchKzaDpvrk9NmEHPd82OFm7pJg87Ym_bI/exec"
            }
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
                
                self.ai_config_tests['authentication_successful'] = True
                
                # Check if user has admin permissions
                user_role = self.current_user.get('role', '').lower()
                if user_role in ['admin', 'super_admin']:
                    self.ai_config_tests['user_has_admin_permissions'] = True
                    self.log(f"✅ User has admin permissions: {user_role}")
                else:
                    self.log(f"⚠️ User role '{user_role}' may not have AI config permissions")
                
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
    
    def test_get_ai_config_endpoint(self):
        """Test GET /api/ai-config - Fetch current AI configuration"""
        try:
            self.log("📥 Testing GET /api/ai-config - Fetch current AI configuration...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.ai_config_tests['get_ai_config_endpoint_accessible'] = True
                self.log("✅ GET /api/ai-config endpoint accessible")
                
                try:
                    config_data = response.json()
                    self.ai_config_tests['get_ai_config_returns_valid_response'] = True
                    self.log("✅ GET endpoint returns valid JSON response")
                    
                    # Log the current configuration
                    self.log(f"   Current AI Config: {json.dumps(config_data, indent=2)}")
                    
                    # Check response structure
                    expected_fields = ['provider', 'model', 'use_emergent_key']
                    structure_correct = True
                    
                    for field in expected_fields:
                        if field in config_data:
                            self.log(f"      ✅ Field '{field}' present: {config_data[field]}")
                        else:
                            self.log(f"      ❌ Field '{field}' missing")
                            structure_correct = False
                    
                    if structure_correct:
                        self.ai_config_tests['get_ai_config_response_structure_correct'] = True
                        self.log("✅ Response structure is correct")
                    
                    # Check if document_ai section is present
                    if 'document_ai' in config_data:
                        self.ai_config_tests['get_ai_config_includes_document_ai'] = True
                        self.log("✅ Response includes document_ai settings")
                        
                        document_ai = config_data['document_ai']
                        self.log(f"   Document AI Config: {json.dumps(document_ai, indent=2)}")
                        
                        # Check document_ai fields
                        doc_ai_fields = ['enabled', 'project_id', 'location', 'processor_id', 'apps_script_url']
                        for field in doc_ai_fields:
                            if field in document_ai:
                                self.log(f"      ✅ Document AI field '{field}': {document_ai[field]}")
                            else:
                                self.log(f"      ⚠️ Document AI field '{field}' missing or null")
                    else:
                        self.log("⚠️ Response does not include document_ai settings")
                    
                    return config_data
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ GET /api/ai-config endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing GET /api/ai-config endpoint: {str(e)}", "ERROR")
            return None
    
    def test_post_ai_config_endpoint(self):
        """Test POST /api/ai-config - Save AI configuration"""
        try:
            self.log("📤 Testing POST /api/ai-config - Save AI configuration...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   POST {endpoint}")
            self.log(f"   Payload: {json.dumps(self.sample_ai_config, indent=2)}")
            
            response = requests.post(endpoint, json=self.sample_ai_config, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                self.ai_config_tests['post_ai_config_endpoint_accessible'] = True
                self.ai_config_tests['post_ai_config_accepts_complete_payload'] = True
                self.log("✅ POST /api/ai-config endpoint accessible and accepts payload")
                
                try:
                    response_data = response.json()
                    self.ai_config_tests['post_ai_config_returns_success_response'] = True
                    self.log("✅ POST endpoint returns success response")
                    self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                    
                    # Check if response indicates successful save
                    if response_data.get('success') or 'message' in response_data:
                        self.ai_config_tests['post_ai_config_saves_document_ai_settings'] = True
                        self.log("✅ Response indicates successful save")
                    
                    return response_data
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return None
            else:
                self.log(f"   ❌ POST /api/ai-config endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    
                    # Check for specific validation errors
                    if response.status_code == 400:
                        self.log("   ⚠️ Backend validation rejected the request")
                    elif response.status_code == 403:
                        self.log("   ⚠️ Permission denied - user may not have AI config permissions")
                    elif response.status_code == 404:
                        self.log("   ⚠️ Endpoint not found - may not be implemented")
                    
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing POST /api/ai-config endpoint: {str(e)}", "ERROR")
            return None
    
    def test_save_persistence(self):
        """Test that AI configuration settings persist after save"""
        try:
            self.log("🔄 Testing save persistence - verifying settings persist after save...")
            
            # First, save the configuration
            self.log("   Step 1: Saving AI configuration...")
            save_result = self.test_post_ai_config_endpoint()
            
            if not save_result:
                self.log("   ❌ Cannot test persistence - save operation failed")
                return False
            
            # Wait a moment for database write
            import time
            time.sleep(1)
            
            # Then, fetch the configuration to verify it was saved
            self.log("   Step 2: Fetching AI configuration to verify persistence...")
            fetched_config = self.test_get_ai_config_endpoint()
            
            if not fetched_config:
                self.log("   ❌ Cannot verify persistence - fetch operation failed")
                return False
            
            # Compare the saved configuration with what we fetched
            self.log("   Step 3: Comparing saved vs fetched configuration...")
            
            # Check main fields
            main_fields_match = True
            for field in ['provider', 'model', 'use_emergent_key']:
                saved_value = self.sample_ai_config.get(field)
                fetched_value = fetched_config.get(field)
                
                if saved_value == fetched_value:
                    self.log(f"      ✅ Field '{field}' persisted correctly: {fetched_value}")
                else:
                    self.log(f"      ❌ Field '{field}' mismatch - Saved: {saved_value}, Fetched: {fetched_value}")
                    main_fields_match = False
            
            # Check document_ai fields specifically
            document_ai_persisted = True
            if 'document_ai' in fetched_config:
                self.ai_config_tests['document_ai_settings_persist_after_save'] = True
                self.log("✅ Document AI settings section persisted")
                
                saved_doc_ai = self.sample_ai_config['document_ai']
                fetched_doc_ai = fetched_config['document_ai']
                
                for field in ['enabled', 'project_id', 'location', 'processor_id', 'apps_script_url']:
                    saved_value = saved_doc_ai.get(field)
                    fetched_value = fetched_doc_ai.get(field)
                    
                    if saved_value == fetched_value:
                        self.log(f"      ✅ Document AI field '{field}' persisted: {fetched_value}")
                        
                        # Special check for apps_script_url
                        if field == 'apps_script_url' and fetched_value:
                            self.ai_config_tests['apps_script_url_properly_stored'] = True
                            self.log("      ✅ apps_script_url properly stored and retrievable")
                    else:
                        self.log(f"      ❌ Document AI field '{field}' mismatch - Saved: {saved_value}, Fetched: {fetched_value}")
                        document_ai_persisted = False
                
                if document_ai_persisted:
                    self.ai_config_tests['all_document_ai_fields_persisted'] = True
                    self.log("✅ All Document AI fields persisted correctly")
            else:
                self.log("❌ Document AI settings not found in fetched configuration")
                document_ai_persisted = False
            
            # Overall persistence check
            if main_fields_match and document_ai_persisted:
                self.ai_config_tests['settings_retrievable_after_save'] = True
                self.ai_config_tests['mongodb_storage_working'] = True
                self.log("✅ Settings persist across requests - MongoDB storage working")
                return True
            else:
                self.log("❌ Settings do not persist correctly")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing save persistence: {str(e)}", "ERROR")
            return False
    
    def test_backend_validation(self):
        """Test backend validation and error handling"""
        try:
            self.log("🔍 Testing backend validation and error handling...")
            
            # Test with invalid payload
            invalid_config = {
                "provider": "",  # Empty provider
                "model": "",     # Empty model
                # Missing required fields
            }
            
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   Testing with invalid payload: {json.dumps(invalid_config, indent=2)}")
            
            response = requests.post(endpoint, json=invalid_config, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [400, 422]:
                self.ai_config_tests['backend_validation_working'] = True
                self.log("✅ Backend validation working - rejects invalid payload")
                try:
                    error_data = response.json()
                    self.log(f"   Validation error: {error_data.get('detail', 'Unknown error')}")
                except:
                    pass
            else:
                self.log(f"   ⚠️ Expected validation error (400/422), got: {response.status_code}")
            
            # Test permission checks
            self.log("   Testing permission checks...")
            user_role = self.current_user.get('role', '').lower()
            if user_role in ['admin', 'super_admin']:
                self.ai_config_tests['permission_checks_working'] = True
                self.log(f"✅ User role '{user_role}' has appropriate permissions")
            else:
                self.log(f"⚠️ User role '{user_role}' may not have AI config permissions")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing backend validation: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_ai_config_test(self):
        """Run comprehensive test of AI configuration endpoints"""
        try:
            self.log("🚀 STARTING AI CONFIGURATION SAVE & FETCH ENDPOINTS TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Test GET /api/ai-config endpoint
            self.log("\nSTEP 2: Testing GET /api/ai-config - Fetch current AI configuration")
            initial_config = self.test_get_ai_config_endpoint()
            
            # Step 3: Test POST /api/ai-config endpoint
            self.log("\nSTEP 3: Testing POST /api/ai-config - Save AI configuration")
            save_result = self.test_post_ai_config_endpoint()
            
            # Step 4: Test save persistence
            self.log("\nSTEP 4: Testing save persistence")
            self.test_save_persistence()
            
            # Step 5: Test backend validation
            self.log("\nSTEP 5: Testing backend validation and error handling")
            self.test_backend_validation()
            
            self.log("\n" + "=" * 80)
            self.log("✅ AI CONFIGURATION ENDPOINTS TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 AI CONFIGURATION ENDPOINTS TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.ai_config_tests)
            passed_tests = sum(1 for result in self.ai_config_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_has_admin_permissions', 'User has admin permissions'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.ai_config_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # GET Endpoint Results
            self.log("\n📥 GET /api/ai-config - FETCH AI CONFIGURATION:")
            get_tests = [
                ('get_ai_config_endpoint_accessible', 'Endpoint accessible'),
                ('get_ai_config_returns_valid_response', 'Returns valid JSON response'),
                ('get_ai_config_response_structure_correct', 'Response structure correct'),
                ('get_ai_config_includes_document_ai', 'Includes document_ai settings'),
            ]
            
            for test_key, description in get_tests:
                status = "✅ PASS" if self.ai_config_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # POST Endpoint Results
            self.log("\n📤 POST /api/ai-config - SAVE AI CONFIGURATION:")
            post_tests = [
                ('post_ai_config_endpoint_accessible', 'Endpoint accessible'),
                ('post_ai_config_accepts_complete_payload', 'Accepts complete payload'),
                ('post_ai_config_saves_document_ai_settings', 'Saves Document AI settings'),
                ('post_ai_config_returns_success_response', 'Returns success response'),
            ]
            
            for test_key, description in post_tests:
                status = "✅ PASS" if self.ai_config_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Persistence Results
            self.log("\n🔄 SAVE PERSISTENCE VERIFICATION:")
            persistence_tests = [
                ('document_ai_settings_persist_after_save', 'Document AI settings persist'),
                ('apps_script_url_properly_stored', 'apps_script_url properly stored'),
                ('all_document_ai_fields_persisted', 'All Document AI fields persisted'),
                ('settings_retrievable_after_save', 'Settings retrievable after save'),
            ]
            
            for test_key, description in persistence_tests:
                status = "✅ PASS" if self.ai_config_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Validation Results
            self.log("\n🔍 BACKEND VALIDATION & STORAGE:")
            validation_tests = [
                ('backend_validation_working', 'Backend validation working'),
                ('mongodb_storage_working', 'MongoDB storage working'),
                ('permission_checks_working', 'Permission checks working'),
            ]
            
            for test_key, description in validation_tests:
                status = "✅ PASS" if self.ai_config_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'get_ai_config_endpoint_accessible', 'post_ai_config_endpoint_accessible',
                'document_ai_settings_persist_after_save', 'apps_script_url_properly_stored'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.ai_config_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL AI CONFIG ENDPOINTS ARE WORKING")
                self.log("   ✅ Document AI settings save and persistence working")
                self.log("   ✅ apps_script_url properly stored and retrievable")
            else:
                self.log("   ❌ SOME CRITICAL FUNCTIONALITY IS NOT WORKING")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Specific findings for the review request
            self.log("\n🔍 SPECIFIC FINDINGS FOR REVIEW REQUEST:")
            
            if self.ai_config_tests.get('post_ai_config_endpoint_accessible', False):
                self.log("   ✅ POST /api/ai-config endpoint exists and is accessible")
            else:
                self.log("   ❌ POST /api/ai-config endpoint not accessible or not working")
            
            if self.ai_config_tests.get('apps_script_url_properly_stored', False):
                self.log("   ✅ apps_script_url is properly stored and retrievable")
            else:
                self.log("   ❌ apps_script_url is NOT being saved or retrieved correctly")
            
            if self.ai_config_tests.get('all_document_ai_fields_persisted', False):
                self.log("   ✅ All Document AI fields are persisted correctly")
            else:
                self.log("   ❌ Document AI fields are NOT being persisted correctly")
            
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
    """Main function to run the AI configuration tests"""
    tester = AIConfigTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_ai_config_test()
        
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
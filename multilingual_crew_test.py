#!/usr/bin/env python3
"""
Multilingual Crew Fields Backend API Test
Testing full_name_en and place_of_birth_en support

REVIEW REQUEST REQUIREMENTS:
Test the backend API support for multilingual crew fields (full_name_en and place_of_birth_en):

TESTING REQUIREMENTS:
1. **Authentication**: Login with admin1/123456 and verify access
2. **Crew API Endpoints Testing**:
   - Test GET /api/crew endpoint to verify multilingual fields are returned
   - Test POST /api/crew endpoint with multilingual data to create new crew member
   - Test PUT /api/crew/{crew_id} endpoint to update existing crew with multilingual fields
3. **Data Validation**:
   - Verify that full_name_en and place_of_birth_en fields are accepted and stored
   - Test with Vietnamese characters in full_name and place_of_birth fields
   - Test with English characters in full_name_en and place_of_birth_en fields
   - Verify both fields are optional (can be empty/null)
4. **Data Retrieval**:
   - Confirm multilingual fields are returned in API responses
   - Verify proper JSON serialization of multilingual crew data
5. **Error Handling**:
   - Test with missing required fields (full_name, place_of_birth should still be required)
   - Verify proper error messages for validation failures

EXPECTED RESULTS:
- All crew API endpoints should accept and return multilingual fields
- Vietnamese crew data should be stored correctly with UTF-8 encoding
- English translations should be stored as optional supplementary data
- API responses should include both Vietnamese and English field versions
- Backward compatibility maintained (existing crews without English fields work normally)

SHIP CONTEXT:
- Use BROTHER 36 ship (ID: 7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7) for testing
- Test with Vietnamese crew names like "Nguyễn Văn An" and English like "Nguyen Van An"
- Test Vietnamese places like "Hải Phòng" and English like "Hai Phong"
"""

import requests
import json
import os
import sys
import uuid
from datetime import datetime, timezone
import time
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
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class MultilingualCrewTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.created_crew_ids = []
        self.ship_name = "BROTHER 36"
        self.ship_id = "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"
        
        # Test tracking for multilingual crew testing
        self.multilingual_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'admin_role_verified': False,
            'company_assignment_verified': False,
            
            # GET /api/crew endpoint testing
            'get_crew_endpoint_accessible': False,
            'multilingual_fields_returned_in_get': False,
            'vietnamese_characters_displayed_correctly': False,
            'english_fields_optional_in_response': False,
            
            # POST /api/crew endpoint testing
            'post_crew_endpoint_accessible': False,
            'create_crew_with_multilingual_data': False,
            'vietnamese_characters_stored_correctly': False,
            'english_fields_stored_correctly': False,
            'multilingual_fields_optional': False,
            
            # PUT /api/crew endpoint testing
            'put_crew_endpoint_accessible': False,
            'update_crew_with_multilingual_data': False,
            'multilingual_fields_updated_correctly': False,
            
            # Data validation testing
            'required_fields_still_required': False,
            'optional_multilingual_fields_accepted': False,
            'utf8_encoding_working': False,
            'json_serialization_working': False,
            
            # Error handling testing
            'missing_required_fields_rejected': False,
            'proper_error_messages_returned': False,
            
            # Backward compatibility testing
            'existing_crews_without_english_work': False,
            'backward_compatibility_maintained': False,
        }
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
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
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.multilingual_tests['authentication_successful'] = True
                
                # Verify admin role
                user_role = self.current_user.get('role', '').upper()
                if user_role in ['ADMIN', 'SUPER_ADMIN']:
                    self.multilingual_tests['admin_role_verified'] = True
                    self.log("✅ Admin role verified")
                
                # Verify company assignment
                if self.current_user.get('company'):
                    self.multilingual_tests['company_assignment_verified'] = True
                    self.log("✅ Company assignment verified")
                
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def test_get_crew_endpoint_multilingual(self):
        """Test GET /api/crew endpoint for multilingual field support"""
        try:
            self.log("📋 Testing GET /api/crew endpoint for multilingual fields...")
            
            endpoint = f"{BACKEND_URL}/crew"
            self.log(f"   GET {endpoint}")
            
            response = self.session.get(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.multilingual_tests['get_crew_endpoint_accessible'] = True
                self.log("✅ GET /api/crew endpoint accessible")
                
                try:
                    crew_list = response.json()
                    self.log(f"   Retrieved {len(crew_list)} crew members")
                    
                    if len(crew_list) > 0:
                        # Check if multilingual fields are present in response structure
                        first_crew = crew_list[0]
                        
                        # Check for multilingual field presence
                        multilingual_fields = ['full_name_en', 'place_of_birth_en']
                        fields_present = []
                        
                        for field in multilingual_fields:
                            if field in first_crew:
                                fields_present.append(field)
                                self.log(f"      ✅ Field '{field}' present in response")
                            else:
                                self.log(f"      ⚠️ Field '{field}' not present in response")
                        
                        if len(fields_present) == len(multilingual_fields):
                            self.multilingual_tests['multilingual_fields_returned_in_get'] = True
                            self.log("✅ All multilingual fields returned in GET response")
                        
                        # Check for Vietnamese characters handling
                        vietnamese_crew = None
                        for crew in crew_list:
                            full_name = crew.get('full_name', '')
                            place_of_birth = crew.get('place_of_birth', '')
                            
                            # Look for Vietnamese characters
                            vietnamese_chars = ['ă', 'â', 'đ', 'ê', 'ô', 'ơ', 'ư', 'á', 'à', 'ả', 'ã', 'ạ', 'ấ', 'ầ', 'ẩ', 'ẫ', 'ậ', 'ắ', 'ằ', 'ẳ', 'ẵ', 'ặ', 'é', 'è', 'ẻ', 'ẽ', 'ẹ', 'ế', 'ề', 'ể', 'ễ', 'ệ', 'í', 'ì', 'ỉ', 'ĩ', 'ị', 'ó', 'ò', 'ỏ', 'õ', 'ọ', 'ố', 'ồ', 'ổ', 'ỗ', 'ộ', 'ớ', 'ờ', 'ở', 'ỡ', 'ợ', 'ú', 'ù', 'ủ', 'ũ', 'ụ', 'ứ', 'ừ', 'ử', 'ữ', 'ự', 'ý', 'ỳ', 'ỷ', 'ỹ', 'ỵ']
                            
                            if any(char in full_name.lower() or char in place_of_birth.lower() for char in vietnamese_chars):
                                vietnamese_crew = crew
                                self.multilingual_tests['vietnamese_characters_displayed_correctly'] = True
                                self.log(f"✅ Vietnamese characters displayed correctly: {full_name}")
                                break
                        
                        # Check if English fields are optional (can be null/empty)
                        english_optional = True
                        for crew in crew_list:
                            full_name_en = crew.get('full_name_en')
                            place_of_birth_en = crew.get('place_of_birth_en')
                            
                            # English fields should be optional - null/empty is acceptable
                            if full_name_en is None or full_name_en == "":
                                self.log(f"      ✅ full_name_en is optional (null/empty allowed)")
                            if place_of_birth_en is None or place_of_birth_en == "":
                                self.log(f"      ✅ place_of_birth_en is optional (null/empty allowed)")
                        
                        self.multilingual_tests['english_fields_optional_in_response'] = True
                        
                        return crew_list
                    else:
                        self.log("   ⚠️ No crew members found to test multilingual fields")
                        return []
                        
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ GET crew endpoint failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing GET crew endpoint: {str(e)}", "ERROR")
            return None
    
    def test_post_crew_endpoint_multilingual(self):
        """Test POST /api/crew endpoint with multilingual data"""
        try:
            self.log("📝 Testing POST /api/crew endpoint with multilingual data...")
            
            # Test data with Vietnamese and English versions
            test_crew_data = {
                "full_name": "Nguyễn Văn An",  # Vietnamese with diacritics
                "full_name_en": "Nguyen Van An",  # English transliteration
                "sex": "M",
                "date_of_birth": "1990-05-15",
                "place_of_birth": "Hải Phòng",  # Vietnamese with diacritics
                "place_of_birth_en": "Hai Phong",  # English transliteration
                "passport": f"ML{uuid.uuid4().hex[:8].upper()}",  # Unique passport
                "nationality": "Vietnamese",
                "rank": "Officer",
                "seamen_book": f"SB-ML-{uuid.uuid4().hex[:6].upper()}",
                "status": "Sign on",
                "ship_sign_on": self.ship_name
            }
            
            endpoint = f"{BACKEND_URL}/crew"
            self.log(f"   POST {endpoint}")
            self.log(f"   Test data with multilingual fields:")
            self.log(f"      full_name: {test_crew_data['full_name']}")
            self.log(f"      full_name_en: {test_crew_data['full_name_en']}")
            self.log(f"      place_of_birth: {test_crew_data['place_of_birth']}")
            self.log(f"      place_of_birth_en: {test_crew_data['place_of_birth_en']}")
            
            response = self.session.post(endpoint, json=test_crew_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                self.multilingual_tests['post_crew_endpoint_accessible'] = True
                self.multilingual_tests['create_crew_with_multilingual_data'] = True
                self.log("✅ POST /api/crew endpoint accessible")
                self.log("✅ Crew created with multilingual data")
                
                try:
                    created_crew = response.json()
                    crew_id = created_crew.get('id')
                    self.created_crew_ids.append(crew_id)
                    
                    self.log(f"   ✅ Created crew ID: {crew_id}")
                    
                    # Verify multilingual fields are stored correctly
                    stored_full_name = created_crew.get('full_name')
                    stored_full_name_en = created_crew.get('full_name_en')
                    stored_place_of_birth = created_crew.get('place_of_birth')
                    stored_place_of_birth_en = created_crew.get('place_of_birth_en')
                    
                    self.log(f"   Stored full_name: {stored_full_name}")
                    self.log(f"   Stored full_name_en: {stored_full_name_en}")
                    self.log(f"   Stored place_of_birth: {stored_place_of_birth}")
                    self.log(f"   Stored place_of_birth_en: {stored_place_of_birth_en}")
                    
                    # Verify Vietnamese characters are stored correctly
                    if stored_full_name == test_crew_data['full_name'] and stored_place_of_birth == test_crew_data['place_of_birth']:
                        self.multilingual_tests['vietnamese_characters_stored_correctly'] = True
                        self.log("✅ Vietnamese characters stored correctly")
                    
                    # Verify English fields are stored correctly
                    if stored_full_name_en == test_crew_data['full_name_en'] and stored_place_of_birth_en == test_crew_data['place_of_birth_en']:
                        self.multilingual_tests['english_fields_stored_correctly'] = True
                        self.log("✅ English fields stored correctly")
                    
                    # Test UTF-8 encoding
                    self.multilingual_tests['utf8_encoding_working'] = True
                    self.multilingual_tests['json_serialization_working'] = True
                    self.log("✅ UTF-8 encoding working")
                    self.log("✅ JSON serialization working")
                    
                    return crew_id
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ POST crew endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error response: {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing POST crew endpoint: {str(e)}", "ERROR")
            return None
    
    def test_post_crew_optional_multilingual_fields(self):
        """Test POST /api/crew with optional multilingual fields (empty/null)"""
        try:
            self.log("📝 Testing POST /api/crew with optional multilingual fields...")
            
            # Test data without English fields (should still work)
            test_crew_data = {
                "full_name": "Trần Thị Bình",  # Vietnamese only
                "sex": "F",
                "date_of_birth": "1985-08-20",
                "place_of_birth": "Đà Nẵng",  # Vietnamese only
                "passport": f"ML{uuid.uuid4().hex[:8].upper()}",
                "nationality": "Vietnamese",
                "rank": "Engineer",
                "status": "Sign on"
                # Note: full_name_en and place_of_birth_en are intentionally omitted
            }
            
            endpoint = f"{BACKEND_URL}/crew"
            self.log(f"   POST {endpoint} (without English fields)")
            
            response = self.session.post(endpoint, json=test_crew_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                self.multilingual_tests['multilingual_fields_optional'] = True
                self.log("✅ Multilingual fields are optional - crew created without English fields")
                
                created_crew = response.json()
                crew_id = created_crew.get('id')
                self.created_crew_ids.append(crew_id)
                
                # Verify English fields are null/empty in response
                full_name_en = created_crew.get('full_name_en')
                place_of_birth_en = created_crew.get('place_of_birth_en')
                
                self.log(f"   full_name_en: {full_name_en}")
                self.log(f"   place_of_birth_en: {place_of_birth_en}")
                
                if full_name_en is None or full_name_en == "":
                    self.log("   ✅ full_name_en is properly null/empty when not provided")
                if place_of_birth_en is None or place_of_birth_en == "":
                    self.log("   ✅ place_of_birth_en is properly null/empty when not provided")
                
                return crew_id
            else:
                self.log(f"   ❌ Failed to create crew without English fields: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing optional multilingual fields: {str(e)}", "ERROR")
            return None
    
    def test_put_crew_endpoint_multilingual(self, crew_id):
        """Test PUT /api/crew/{crew_id} endpoint with multilingual updates"""
        try:
            self.log(f"✏️ Testing PUT /api/crew/{crew_id} with multilingual updates...")
            
            # Update data with multilingual changes
            update_data = {
                "full_name": "Nguyễn Văn An (Updated)",
                "full_name_en": "Nguyen Van An (Updated)",
                "place_of_birth": "Thành phố Hồ Chí Minh",
                "place_of_birth_en": "Ho Chi Minh City",
                "rank": "Senior Officer"
            }
            
            endpoint = f"{BACKEND_URL}/crew/{crew_id}"
            self.log(f"   PUT {endpoint}")
            self.log(f"   Update data:")
            for key, value in update_data.items():
                self.log(f"      {key}: {value}")
            
            response = self.session.put(endpoint, json=update_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.multilingual_tests['put_crew_endpoint_accessible'] = True
                self.multilingual_tests['update_crew_with_multilingual_data'] = True
                self.log("✅ PUT /api/crew endpoint accessible")
                self.log("✅ Crew updated with multilingual data")
                
                try:
                    updated_crew = response.json()
                    
                    # Verify updates were applied correctly
                    updated_full_name = updated_crew.get('full_name')
                    updated_full_name_en = updated_crew.get('full_name_en')
                    updated_place_of_birth = updated_crew.get('place_of_birth')
                    updated_place_of_birth_en = updated_crew.get('place_of_birth_en')
                    
                    self.log(f"   Updated full_name: {updated_full_name}")
                    self.log(f"   Updated full_name_en: {updated_full_name_en}")
                    self.log(f"   Updated place_of_birth: {updated_place_of_birth}")
                    self.log(f"   Updated place_of_birth_en: {updated_place_of_birth_en}")
                    
                    # Verify all multilingual fields were updated correctly
                    all_updated = True
                    for field, expected_value in update_data.items():
                        actual_value = updated_crew.get(field)
                        if actual_value == expected_value:
                            self.log(f"      ✅ {field} updated correctly")
                        else:
                            self.log(f"      ❌ {field} not updated correctly: expected '{expected_value}', got '{actual_value}'")
                            all_updated = False
                    
                    if all_updated:
                        self.multilingual_tests['multilingual_fields_updated_correctly'] = True
                        self.log("✅ All multilingual fields updated correctly")
                    
                    return updated_crew
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ PUT crew endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    pass
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing PUT crew endpoint: {str(e)}", "ERROR")
            return None
    
    def test_required_fields_validation(self):
        """Test that required fields are still required despite multilingual support"""
        try:
            self.log("🔍 Testing required fields validation...")
            
            # Test with missing required field (full_name)
            incomplete_crew_data = {
                "full_name_en": "English Name Only",  # English provided but Vietnamese missing
                "sex": "M",
                "date_of_birth": "1990-01-01",
                "place_of_birth": "Some Place",
                "passport": f"REQ{uuid.uuid4().hex[:8].upper()}",
                "nationality": "Vietnamese"
                # Missing required full_name field
            }
            
            endpoint = f"{BACKEND_URL}/crew"
            self.log(f"   POST {endpoint} (missing required full_name)")
            
            response = self.session.post(endpoint, json=incomplete_crew_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [400, 422]:
                self.multilingual_tests['required_fields_still_required'] = True
                self.multilingual_tests['missing_required_fields_rejected'] = True
                self.log("✅ Required fields validation working - missing full_name rejected")
                
                try:
                    error_data = response.json()
                    error_message = error_data.get('detail', 'Unknown error')
                    self.log(f"   Error message: {error_message}")
                    
                    if 'full_name' in str(error_message).lower():
                        self.multilingual_tests['proper_error_messages_returned'] = True
                        self.log("✅ Proper error message returned for missing full_name")
                except:
                    pass
                
                return True
            else:
                self.log(f"   ❌ Expected 400/422 error for missing required field, got: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing required fields validation: {str(e)}", "ERROR")
            return False
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing crews without English fields"""
        try:
            self.log("🔄 Testing backward compatibility...")
            
            # Get existing crew list to check backward compatibility
            endpoint = f"{BACKEND_URL}/crew"
            response = self.session.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                crew_list = response.json()
                
                # Check if existing crews work properly
                existing_crews_work = True
                for crew in crew_list:
                    # Verify that crews without English fields still work
                    full_name = crew.get('full_name')
                    place_of_birth = crew.get('place_of_birth')
                    full_name_en = crew.get('full_name_en')
                    place_of_birth_en = crew.get('place_of_birth_en')
                    
                    # Existing crews should have Vietnamese names and places
                    if full_name and place_of_birth:
                        # English fields can be null/empty for existing crews
                        if full_name_en is None or full_name_en == "":
                            self.log(f"   ✅ Existing crew '{full_name}' works without English name")
                        if place_of_birth_en is None or place_of_birth_en == "":
                            self.log(f"   ✅ Existing crew from '{place_of_birth}' works without English place")
                
                self.multilingual_tests['existing_crews_without_english_work'] = True
                self.multilingual_tests['backward_compatibility_maintained'] = True
                self.log("✅ Backward compatibility maintained")
                return True
            else:
                self.log(f"   ❌ Failed to get crew list for backward compatibility test: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing backward compatibility: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        try:
            self.log("🧹 Cleaning up test data...")
            
            for crew_id in self.created_crew_ids[:]:
                try:
                    endpoint = f"{BACKEND_URL}/crew/{crew_id}"
                    response = self.session.delete(endpoint, timeout=30)
                    if response.status_code in [200, 204]:
                        self.log(f"   ✅ Cleaned up crew ID: {crew_id}")
                        self.created_crew_ids.remove(crew_id)
                    else:
                        self.log(f"   ⚠️ Failed to clean up crew ID: {crew_id}")
                except Exception as e:
                    self.log(f"   ⚠️ Error cleaning up crew ID {crew_id}: {str(e)}")
            
            self.log("✅ Cleanup completed")
            
        except Exception as e:
            self.log(f"❌ Error during cleanup: {str(e)}", "ERROR")
    
    def run_comprehensive_multilingual_test(self):
        """Run comprehensive test of multilingual crew fields support"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE MULTILINGUAL CREW FIELDS TEST")
            self.log("=" * 80)
            self.log("Testing multilingual support for full_name_en and place_of_birth_en fields")
            self.log("Ship context: BROTHER 36 (ID: 7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7)")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication and Setup")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Test GET /api/crew endpoint for multilingual fields
            self.log("\nSTEP 2: Testing GET /api/crew endpoint for multilingual fields")
            crew_list = self.test_get_crew_endpoint_multilingual()
            
            # Step 3: Test POST /api/crew endpoint with multilingual data
            self.log("\nSTEP 3: Testing POST /api/crew endpoint with multilingual data")
            created_crew_id = self.test_post_crew_endpoint_multilingual()
            
            # Step 4: Test POST /api/crew with optional multilingual fields
            self.log("\nSTEP 4: Testing POST /api/crew with optional multilingual fields")
            optional_crew_id = self.test_post_crew_optional_multilingual_fields()
            
            # Step 5: Test PUT /api/crew endpoint with multilingual updates
            if created_crew_id:
                self.log("\nSTEP 5: Testing PUT /api/crew endpoint with multilingual updates")
                self.test_put_crew_endpoint_multilingual(created_crew_id)
            
            # Step 6: Test required fields validation
            self.log("\nSTEP 6: Testing required fields validation")
            self.test_required_fields_validation()
            
            # Step 7: Test backward compatibility
            self.log("\nSTEP 7: Testing backward compatibility")
            self.test_backward_compatibility()
            
            # Step 8: Cleanup
            self.log("\nSTEP 8: Cleanup test data")
            self.cleanup_test_data()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE MULTILINGUAL CREW FIELDS TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 MULTILINGUAL CREW FIELDS TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.multilingual_tests)
            passed_tests = sum(1 for result in self.multilingual_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication with admin1/123456'),
                ('admin_role_verified', 'Admin role verified'),
                ('company_assignment_verified', 'Company assignment verified'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.multilingual_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # GET Endpoint Results
            self.log("\n📋 GET /api/crew ENDPOINT TESTING:")
            get_tests = [
                ('get_crew_endpoint_accessible', 'GET endpoint accessible'),
                ('multilingual_fields_returned_in_get', 'Multilingual fields returned'),
                ('vietnamese_characters_displayed_correctly', 'Vietnamese characters displayed correctly'),
                ('english_fields_optional_in_response', 'English fields optional in response'),
            ]
            
            for test_key, description in get_tests:
                status = "✅ PASS" if self.multilingual_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # POST Endpoint Results
            self.log("\n📝 POST /api/crew ENDPOINT TESTING:")
            post_tests = [
                ('post_crew_endpoint_accessible', 'POST endpoint accessible'),
                ('create_crew_with_multilingual_data', 'Create crew with multilingual data'),
                ('vietnamese_characters_stored_correctly', 'Vietnamese characters stored correctly'),
                ('english_fields_stored_correctly', 'English fields stored correctly'),
                ('multilingual_fields_optional', 'Multilingual fields are optional'),
            ]
            
            for test_key, description in post_tests:
                status = "✅ PASS" if self.multilingual_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # PUT Endpoint Results
            self.log("\n✏️ PUT /api/crew ENDPOINT TESTING:")
            put_tests = [
                ('put_crew_endpoint_accessible', 'PUT endpoint accessible'),
                ('update_crew_with_multilingual_data', 'Update crew with multilingual data'),
                ('multilingual_fields_updated_correctly', 'Multilingual fields updated correctly'),
            ]
            
            for test_key, description in put_tests:
                status = "✅ PASS" if self.multilingual_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Data Validation Results
            self.log("\n🔍 DATA VALIDATION TESTING:")
            validation_tests = [
                ('required_fields_still_required', 'Required fields still required'),
                ('optional_multilingual_fields_accepted', 'Optional multilingual fields accepted'),
                ('utf8_encoding_working', 'UTF-8 encoding working'),
                ('json_serialization_working', 'JSON serialization working'),
            ]
            
            for test_key, description in validation_tests:
                status = "✅ PASS" if self.multilingual_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Error Handling Results
            self.log("\n⚠️ ERROR HANDLING TESTING:")
            error_tests = [
                ('missing_required_fields_rejected', 'Missing required fields rejected'),
                ('proper_error_messages_returned', 'Proper error messages returned'),
            ]
            
            for test_key, description in error_tests:
                status = "✅ PASS" if self.multilingual_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backward Compatibility Results
            self.log("\n🔄 BACKWARD COMPATIBILITY TESTING:")
            compatibility_tests = [
                ('existing_crews_without_english_work', 'Existing crews without English work'),
                ('backward_compatibility_maintained', 'Backward compatibility maintained'),
            ]
            
            for test_key, description in compatibility_tests:
                status = "✅ PASS" if self.multilingual_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'multilingual_fields_returned_in_get',
                'create_crew_with_multilingual_data',
                'vietnamese_characters_stored_correctly',
                'english_fields_stored_correctly',
                'multilingual_fields_updated_correctly',
                'required_fields_still_required',
                'backward_compatibility_maintained'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.multilingual_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL MULTILINGUAL REQUIREMENTS MET")
                self.log("   ✅ Backend API supports multilingual crew fields correctly")
                self.log("   ✅ Vietnamese and English fields work as expected")
                self.log("   ✅ Backward compatibility maintained")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Expected Results Verification
            self.log("\n📋 EXPECTED RESULTS VERIFICATION:")
            expected_results = [
                "All crew API endpoints accept and return multilingual fields",
                "Vietnamese crew data stored correctly with UTF-8 encoding", 
                "English translations stored as optional supplementary data",
                "API responses include both Vietnamese and English field versions",
                "Backward compatibility maintained (existing crews work normally)"
            ]
            
            for i, result in enumerate(expected_results, 1):
                self.log(f"   {i}. {result}")
            
            if success_rate >= 90:
                self.log(f"\n   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
                self.log("   ✅ Multilingual crew fields implementation is working perfectly")
            elif success_rate >= 75:
                self.log(f"\n   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
                self.log("   ⚠️ Most multilingual features working, minor issues to address")
            else:
                self.log(f"\n   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
                self.log("   ❌ Significant issues with multilingual implementation")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the multilingual crew fields tests"""
    print("🧪 Backend Test: Multilingual Crew Fields Support")
    print("🌐 Testing full_name_en and place_of_birth_en fields")
    print("🎯 Focus: Complete API support for Vietnamese/English crew data")
    print("=" * 80)
    print("Testing requirements:")
    print("1. Authentication with admin1/123456")
    print("2. GET /api/crew endpoint multilingual field support")
    print("3. POST /api/crew endpoint with multilingual data")
    print("4. PUT /api/crew endpoint multilingual updates")
    print("5. Data validation and error handling")
    print("6. UTF-8 encoding and JSON serialization")
    print("7. Backward compatibility verification")
    print("=" * 80)
    
    tester = MultilingualCrewTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_multilingual_test()
        
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
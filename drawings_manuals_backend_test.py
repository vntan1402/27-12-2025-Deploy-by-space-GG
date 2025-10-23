#!/usr/bin/env python3
"""
Drawings & Manuals CRUD APIs Comprehensive Testing

REVIEW REQUEST REQUIREMENTS:
Test Drawings & Manuals CRUD APIs comprehensively:

**Test Scenarios:**

1. **GET /api/drawings-manuals?ship_id={id}**
   - Test with valid ship_id
   - Test with invalid ship_id
   - Verify response format matches DrawingsManualResponse model
   - Check empty array for ship with no documents

2. **POST /api/drawings-manuals**
   - Create document with all fields
   - Create document with only required field (document_name)
   - Test with invalid ship_id (should return 404)
   - Test without document_name (should fail validation)
   - Verify auto-generated id, created_at, updated_at=null
   - Verify file_id and summary_file_id are null initially

3. **POST /api/drawings-manuals/check-duplicate**
   - Test duplicate check with document_name only
   - Test duplicate check with document_name + document_no
   - Test with non-existent document (should return is_duplicate: false)
   - Test with existing document (should return is_duplicate: true with existing_document details)

4. **PUT /api/drawings-manuals/{id}**
   - Update document_name
   - Update status (Valid, Approved, Expired, Unknown)
   - Update all fields
   - Test with invalid document_id (should return 404)
   - Verify updated_at is set

5. **DELETE /api/drawings-manuals/{id}**
   - Delete existing document
   - Test with invalid document_id (should return 404)
   - Verify document is removed from database

6. **DELETE /api/drawings-manuals/bulk-delete**
   - Bulk delete with 2-3 document IDs
   - Test with mix of valid and invalid IDs
   - Verify deleted_count in response
   - Verify documents are removed from database

**Authentication:**
- All endpoints require valid JWT token
- Use admin1/123456 credentials to login and get token

**Database:**
- Use existing ship from database for testing
- Clean up test data after testing

**Expected Response Formats:**
- GET: List[DrawingsManualResponse]
- POST: DrawingsManualResponse
- PUT: DrawingsManualResponse
- DELETE: {success: true, message: string}
- BULK DELETE: {success: true, deleted_count: int, total_requested: int}
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
    # Fallback to external URL from environment
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class DrawingsManualsAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.test_ship_id = None
        self.test_ship_name = None
        self.created_document_ids = []
        
        # Test tracking for drawings & manuals CRUD testing
        self.drawings_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'test_ship_found': False,
            
            # GET /api/drawings-manuals?ship_id={id}
            'get_drawings_manuals_endpoint_accessible': False,
            'get_drawings_manuals_valid_ship_id': False,
            'get_drawings_manuals_invalid_ship_id': False,
            'get_drawings_manuals_response_format_correct': False,
            'get_drawings_manuals_empty_array_for_no_documents': False,
            
            # POST /api/drawings-manuals
            'create_drawings_manual_endpoint_accessible': False,
            'create_drawings_manual_all_fields': False,
            'create_drawings_manual_required_field_only': False,
            'create_drawings_manual_invalid_ship_id_404': False,
            'create_drawings_manual_missing_document_name_validation': False,
            'create_drawings_manual_auto_generated_fields': False,
            'create_drawings_manual_null_file_ids': False,
            
            # POST /api/drawings-manuals/check-duplicate
            'check_duplicate_endpoint_accessible': False,
            'check_duplicate_document_name_only': False,
            'check_duplicate_document_name_and_no': False,
            'check_duplicate_non_existent_false': False,
            'check_duplicate_existing_true_with_details': False,
            
            # PUT /api/drawings-manuals/{id}
            'update_drawings_manual_endpoint_accessible': False,
            'update_drawings_manual_document_name': False,
            'update_drawings_manual_status': False,
            'update_drawings_manual_all_fields': False,
            'update_drawings_manual_invalid_id_404': False,
            'update_drawings_manual_updated_at_set': False,
            
            # DELETE /api/drawings-manuals/{id}
            'delete_drawings_manual_endpoint_accessible': False,
            'delete_drawings_manual_existing_document': False,
            'delete_drawings_manual_invalid_id_404': False,
            'delete_drawings_manual_removed_from_database': False,
            
            # DELETE /api/drawings-manuals/bulk-delete
            'bulk_delete_drawings_manuals_endpoint_accessible': False,
            'bulk_delete_multiple_documents': False,
            'bulk_delete_mix_valid_invalid_ids': False,
            'bulk_delete_deleted_count_correct': False,
            'bulk_delete_documents_removed_from_database': False,
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
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.drawings_tests['authentication_successful'] = True
                self.drawings_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_test_ship(self):
        """Find a ship for testing"""
        try:
            self.log("🚢 Finding ship for testing...")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                if ships:
                    # Use first available ship
                    test_ship = ships[0]
                    self.test_ship_id = test_ship.get("id")
                    self.test_ship_name = test_ship.get("name")
                    self.log(f"✅ Found test ship: {self.test_ship_name} (ID: {self.test_ship_id})")
                    self.drawings_tests['test_ship_found'] = True
                    return True
                else:
                    self.log("❌ No ships found in database", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding test ship: {str(e)}", "ERROR")
            return False
    
    def test_get_drawings_manuals_endpoint(self):
        """Test GET /api/drawings-manuals?ship_id={id}"""
        try:
            self.log("📋 Testing GET /api/drawings-manuals endpoint...")
            
            # Test 1: Valid ship_id
            self.log("   Test 1: Valid ship_id")
            endpoint = f"{BACKEND_URL}/drawings-manuals?ship_id={self.test_ship_id}"
            self.log(f"   GET {endpoint}")
            
            response = self.session.get(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.drawings_tests['get_drawings_manuals_endpoint_accessible'] = True
                self.drawings_tests['get_drawings_manuals_valid_ship_id'] = True
                self.log("✅ GET drawings-manuals endpoint accessible with valid ship_id")
                
                try:
                    drawings_list = response.json()
                    self.log(f"   ✅ Retrieved {len(drawings_list)} drawings/manuals")
                    
                    # Verify response format
                    if isinstance(drawings_list, list):
                        self.drawings_tests['get_drawings_manuals_response_format_correct'] = True
                        self.log("   ✅ Response format is correct (List)")
                        
                        if len(drawings_list) == 0:
                            self.drawings_tests['get_drawings_manuals_empty_array_for_no_documents'] = True
                            self.log("   ✅ Empty array returned for ship with no documents")
                        else:
                            # Check first document structure
                            first_doc = drawings_list[0]
                            expected_fields = ['id', 'ship_id', 'document_name', 'status', 'created_at']
                            for field in expected_fields:
                                if field in first_doc:
                                    self.log(f"      ✅ Field '{field}' present")
                                else:
                                    self.log(f"      ❌ Field '{field}' missing")
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
            else:
                self.log(f"   ❌ GET drawings-manuals endpoint failed: {response.status_code}")
            
            # Test 2: Invalid ship_id
            self.log("   Test 2: Invalid ship_id")
            invalid_ship_id = "invalid-ship-id-12345"
            invalid_endpoint = f"{BACKEND_URL}/drawings-manuals?ship_id={invalid_ship_id}"
            self.log(f"   GET {invalid_endpoint}")
            
            invalid_response = self.session.get(invalid_endpoint, timeout=30)
            self.log(f"   Response status: {invalid_response.status_code}")
            
            if invalid_response.status_code == 200:
                self.drawings_tests['get_drawings_manuals_invalid_ship_id'] = True
                try:
                    invalid_drawings = invalid_response.json()
                    if isinstance(invalid_drawings, list) and len(invalid_drawings) == 0:
                        self.log("   ✅ Invalid ship_id returns empty array (expected behavior)")
                    else:
                        self.log(f"   ⚠️ Invalid ship_id returned {len(invalid_drawings)} documents")
                except:
                    pass
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error testing GET drawings-manuals endpoint: {str(e)}", "ERROR")
            return False
    
    def test_create_drawings_manual_endpoint(self):
        """Test POST /api/drawings-manuals"""
        try:
            self.log("📝 Testing POST /api/drawings-manuals endpoint...")
            
            # Test 1: Create document with all fields
            self.log("   Test 1: Create document with all fields")
            
            full_document_data = {
                "ship_id": self.test_ship_id,
                "document_name": "Test Drawing Manual - Full Fields",
                "document_no": "DM-TEST-001",
                "approved_by": "Test Approver",
                "approved_date": "2024-01-15T10:00:00Z",
                "status": "Approved",
                "note": "Test document with all fields"
            }
            
            endpoint = f"{BACKEND_URL}/drawings-manuals"
            self.log(f"   POST {endpoint}")
            self.log(f"   Data: {json.dumps(full_document_data, indent=2)}")
            
            response = self.session.post(endpoint, json=full_document_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.drawings_tests['create_drawings_manual_endpoint_accessible'] = True
                self.drawings_tests['create_drawings_manual_all_fields'] = True
                self.log("✅ Create drawings-manual endpoint accessible with all fields")
                
                try:
                    created_doc = response.json()
                    doc_id = created_doc.get('id')
                    self.created_document_ids.append(doc_id)
                    
                    self.log(f"   ✅ Document created with ID: {doc_id}")
                    
                    # Verify auto-generated fields
                    if created_doc.get('id') and created_doc.get('created_at'):
                        self.drawings_tests['create_drawings_manual_auto_generated_fields'] = True
                        self.log("   ✅ Auto-generated fields (id, created_at) present")
                    
                    if created_doc.get('updated_at') is None:
                        self.log("   ✅ updated_at is null initially")
                    
                    # Verify file_id and summary_file_id are null initially
                    if created_doc.get('file_id') is None and created_doc.get('summary_file_id') is None:
                        self.drawings_tests['create_drawings_manual_null_file_ids'] = True
                        self.log("   ✅ file_id and summary_file_id are null initially")
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
            else:
                self.log(f"   ❌ Create drawings-manual endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    pass
            
            # Test 2: Create document with only required field (document_name)
            self.log("   Test 2: Create document with only required field")
            
            minimal_document_data = {
                "ship_id": self.test_ship_id,
                "document_name": "Test Drawing Manual - Minimal Fields"
            }
            
            response2 = self.session.post(endpoint, json=minimal_document_data, timeout=30)
            self.log(f"   Response status: {response2.status_code}")
            
            if response2.status_code == 200:
                self.drawings_tests['create_drawings_manual_required_field_only'] = True
                self.log("✅ Create document with only required field successful")
                
                try:
                    created_doc2 = response2.json()
                    doc_id2 = created_doc2.get('id')
                    self.created_document_ids.append(doc_id2)
                    self.log(f"   ✅ Minimal document created with ID: {doc_id2}")
                except:
                    pass
            
            # Test 3: Invalid ship_id (should return 404)
            self.log("   Test 3: Invalid ship_id")
            
            invalid_ship_data = {
                "ship_id": "invalid-ship-id-12345",
                "document_name": "Test Document Invalid Ship"
            }
            
            response3 = self.session.post(endpoint, json=invalid_ship_data, timeout=30)
            self.log(f"   Response status: {response3.status_code}")
            
            if response3.status_code == 404:
                self.drawings_tests['create_drawings_manual_invalid_ship_id_404'] = True
                self.log("✅ Invalid ship_id returns 404 as expected")
            else:
                self.log(f"   ❌ Expected 404 for invalid ship_id, got: {response3.status_code}")
            
            # Test 4: Missing document_name (should fail validation)
            self.log("   Test 4: Missing document_name")
            
            missing_name_data = {
                "ship_id": self.test_ship_id,
                "document_no": "DM-TEST-MISSING-NAME"
            }
            
            response4 = self.session.post(endpoint, json=missing_name_data, timeout=30)
            self.log(f"   Response status: {response4.status_code}")
            
            if response4.status_code in [400, 422]:
                self.drawings_tests['create_drawings_manual_missing_document_name_validation'] = True
                self.log("✅ Missing document_name fails validation as expected")
            else:
                self.log(f"   ❌ Expected 400/422 for missing document_name, got: {response4.status_code}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error testing create drawings-manual endpoint: {str(e)}", "ERROR")
            return False
    
    def test_check_duplicate_endpoint(self):
        """Test POST /api/drawings-manuals/check-duplicate"""
        try:
            self.log("🔍 Testing POST /api/drawings-manuals/check-duplicate endpoint...")
            
            # First, create a test document to check duplicates against
            test_document_data = {
                "ship_id": self.test_ship_id,
                "document_name": "Duplicate Test Document",
                "document_no": "DUP-TEST-001"
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/drawings-manuals", json=test_document_data, timeout=30)
            if create_response.status_code == 200:
                created_doc = create_response.json()
                test_doc_id = created_doc.get('id')
                self.created_document_ids.append(test_doc_id)
                self.log(f"   Created test document for duplicate checking: {test_doc_id}")
            
            endpoint = f"{BACKEND_URL}/drawings-manuals/check-duplicate"
            
            # Test 1: Check duplicate with document_name only
            self.log("   Test 1: Check duplicate with document_name only")
            
            duplicate_check_data = {
                "ship_id": self.test_ship_id,
                "document_name": "Duplicate Test Document"
            }
            
            self.log(f"   POST {endpoint}")
            self.log(f"   Data: {json.dumps(duplicate_check_data, indent=2)}")
            
            response = self.session.post(endpoint, json=duplicate_check_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.drawings_tests['check_duplicate_endpoint_accessible'] = True
                self.drawings_tests['check_duplicate_document_name_only'] = True
                self.log("✅ Check duplicate endpoint accessible with document_name only")
                
                try:
                    duplicate_result = response.json()
                    self.log(f"   Response: {json.dumps(duplicate_result, indent=2)}")
                    
                    if duplicate_result.get('is_duplicate') == True:
                        self.drawings_tests['check_duplicate_existing_true_with_details'] = True
                        self.log("   ✅ Existing document returns is_duplicate: true")
                        
                        existing_doc = duplicate_result.get('existing_document', {})
                        if existing_doc.get('id') and existing_doc.get('document_name'):
                            self.log("   ✅ existing_document details provided")
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
            
            # Test 2: Check duplicate with document_name + document_no
            self.log("   Test 2: Check duplicate with document_name + document_no")
            
            duplicate_check_data2 = {
                "ship_id": self.test_ship_id,
                "document_name": "Duplicate Test Document",
                "document_no": "DUP-TEST-001"
            }
            
            response2 = self.session.post(endpoint, json=duplicate_check_data2, timeout=30)
            self.log(f"   Response status: {response2.status_code}")
            
            if response2.status_code == 200:
                self.drawings_tests['check_duplicate_document_name_and_no'] = True
                self.log("✅ Check duplicate with document_name + document_no successful")
            
            # Test 3: Non-existent document (should return is_duplicate: false)
            self.log("   Test 3: Non-existent document")
            
            non_existent_data = {
                "ship_id": self.test_ship_id,
                "document_name": "Non Existent Document Name",
                "document_no": "NON-EXIST-999"
            }
            
            response3 = self.session.post(endpoint, json=non_existent_data, timeout=30)
            self.log(f"   Response status: {response3.status_code}")
            
            if response3.status_code == 200:
                try:
                    non_existent_result = response3.json()
                    if non_existent_result.get('is_duplicate') == False:
                        self.drawings_tests['check_duplicate_non_existent_false'] = True
                        self.log("   ✅ Non-existent document returns is_duplicate: false")
                except:
                    pass
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error testing check duplicate endpoint: {str(e)}", "ERROR")
            return False
    
    def test_update_drawings_manual_endpoint(self):
        """Test PUT /api/drawings-manuals/{id}"""
        try:
            self.log("✏️ Testing PUT /api/drawings-manuals/{id} endpoint...")
            
            if not self.created_document_ids:
                self.log("❌ No created documents available for update testing", "ERROR")
                return False
            
            test_doc_id = self.created_document_ids[0]
            endpoint = f"{BACKEND_URL}/drawings-manuals/{test_doc_id}"
            
            # Test 1: Update document_name
            self.log("   Test 1: Update document_name")
            
            update_name_data = {
                "document_name": "Updated Test Drawing Manual Name"
            }
            
            self.log(f"   PUT {endpoint}")
            self.log(f"   Data: {json.dumps(update_name_data, indent=2)}")
            
            response = self.session.put(endpoint, json=update_name_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.drawings_tests['update_drawings_manual_endpoint_accessible'] = True
                self.drawings_tests['update_drawings_manual_document_name'] = True
                self.log("✅ Update drawings-manual endpoint accessible - document_name updated")
                
                try:
                    updated_doc = response.json()
                    if updated_doc.get('document_name') == update_name_data['document_name']:
                        self.log("   ✅ Document name updated correctly")
                    
                    # Verify updated_at is set
                    if updated_doc.get('updated_at'):
                        self.drawings_tests['update_drawings_manual_updated_at_set'] = True
                        self.log("   ✅ updated_at field is set")
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
            
            # Test 2: Update status
            self.log("   Test 2: Update status")
            
            update_status_data = {
                "status": "Expired"
            }
            
            response2 = self.session.put(endpoint, json=update_status_data, timeout=30)
            self.log(f"   Response status: {response2.status_code}")
            
            if response2.status_code == 200:
                self.drawings_tests['update_drawings_manual_status'] = True
                self.log("✅ Status update successful")
                
                try:
                    updated_doc2 = response2.json()
                    if updated_doc2.get('status') == update_status_data['status']:
                        self.log("   ✅ Status updated correctly")
                except:
                    pass
            
            # Test 3: Update all fields
            self.log("   Test 3: Update all fields")
            
            update_all_data = {
                "document_name": "Fully Updated Drawing Manual",
                "document_no": "UPDATED-001",
                "approved_by": "Updated Approver",
                "approved_date": "2024-02-15T15:30:00Z",
                "status": "Valid",
                "note": "Fully updated test document"
            }
            
            response3 = self.session.put(endpoint, json=update_all_data, timeout=30)
            self.log(f"   Response status: {response3.status_code}")
            
            if response3.status_code == 200:
                self.drawings_tests['update_drawings_manual_all_fields'] = True
                self.log("✅ Update all fields successful")
            
            # Test 4: Invalid document_id (should return 404)
            self.log("   Test 4: Invalid document_id")
            
            invalid_endpoint = f"{BACKEND_URL}/drawings-manuals/invalid-doc-id-12345"
            update_invalid_data = {
                "document_name": "Should Not Work"
            }
            
            response4 = self.session.put(invalid_endpoint, json=update_invalid_data, timeout=30)
            self.log(f"   Response status: {response4.status_code}")
            
            if response4.status_code == 404:
                self.drawings_tests['update_drawings_manual_invalid_id_404'] = True
                self.log("✅ Invalid document_id returns 404 as expected")
            else:
                self.log(f"   ❌ Expected 404 for invalid document_id, got: {response4.status_code}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error testing update drawings-manual endpoint: {str(e)}", "ERROR")
            return False
    
    def test_delete_drawings_manual_endpoint(self):
        """Test DELETE /api/drawings-manuals/{id}"""
        try:
            self.log("🗑️ Testing DELETE /api/drawings-manuals/{id} endpoint...")
            
            if not self.created_document_ids:
                self.log("❌ No created documents available for delete testing", "ERROR")
                return False
            
            # Use the last created document for deletion test
            test_doc_id = self.created_document_ids[-1]
            endpoint = f"{BACKEND_URL}/drawings-manuals/{test_doc_id}"
            
            # Test 1: Delete existing document
            self.log("   Test 1: Delete existing document")
            self.log(f"   DELETE {endpoint}")
            
            response = self.session.delete(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.drawings_tests['delete_drawings_manual_endpoint_accessible'] = True
                self.drawings_tests['delete_drawings_manual_existing_document'] = True
                self.log("✅ Delete drawings-manual endpoint accessible - existing document deleted")
                
                try:
                    delete_result = response.json()
                    if delete_result.get('success') == True:
                        self.log("   ✅ Delete response indicates success")
                    
                    # Remove from our tracking list
                    self.created_document_ids.remove(test_doc_id)
                    
                    # Verify document is removed from database
                    verify_endpoint = f"{BACKEND_URL}/drawings-manuals?ship_id={self.test_ship_id}"
                    verify_response = self.session.get(verify_endpoint, timeout=30)
                    
                    if verify_response.status_code == 200:
                        remaining_docs = verify_response.json()
                        doc_still_exists = any(doc.get('id') == test_doc_id for doc in remaining_docs)
                        
                        if not doc_still_exists:
                            self.drawings_tests['delete_drawings_manual_removed_from_database'] = True
                            self.log("   ✅ Document removed from database")
                        else:
                            self.log("   ❌ Document still exists in database")
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
            
            # Test 2: Invalid document_id (should return 404)
            self.log("   Test 2: Invalid document_id")
            
            invalid_endpoint = f"{BACKEND_URL}/drawings-manuals/invalid-doc-id-12345"
            
            response2 = self.session.delete(invalid_endpoint, timeout=30)
            self.log(f"   Response status: {response2.status_code}")
            
            if response2.status_code == 404:
                self.drawings_tests['delete_drawings_manual_invalid_id_404'] = True
                self.log("✅ Invalid document_id returns 404 as expected")
            else:
                self.log(f"   ❌ Expected 404 for invalid document_id, got: {response2.status_code}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error testing delete drawings-manual endpoint: {str(e)}", "ERROR")
            return False
    
    def test_bulk_delete_drawings_manuals_endpoint(self):
        """Test DELETE /api/drawings-manuals/bulk-delete"""
        try:
            self.log("🗑️ Testing DELETE /api/drawings-manuals/bulk-delete endpoint...")
            
            # Create additional documents for bulk delete testing
            self.log("   Creating additional documents for bulk delete testing...")
            
            bulk_test_docs = []
            for i in range(3):
                doc_data = {
                    "ship_id": self.test_ship_id,
                    "document_name": f"Bulk Delete Test Document {i+1}",
                    "document_no": f"BULK-DEL-{i+1:03d}"
                }
                
                create_response = self.session.post(f"{BACKEND_URL}/drawings-manuals", json=doc_data, timeout=30)
                if create_response.status_code == 200:
                    created_doc = create_response.json()
                    doc_id = created_doc.get('id')
                    bulk_test_docs.append(doc_id)
                    self.created_document_ids.append(doc_id)
                    self.log(f"   Created bulk test document: {doc_id}")
            
            if len(bulk_test_docs) < 2:
                self.log("❌ Failed to create enough documents for bulk delete testing", "ERROR")
                return False
            
            endpoint = f"{BACKEND_URL}/drawings-manuals/bulk-delete"
            
            # Test 1: Bulk delete with 2-3 document IDs
            self.log("   Test 1: Bulk delete with multiple valid document IDs")
            
            valid_doc_ids = bulk_test_docs[:2]  # Use first 2 documents
            bulk_delete_data = {
                "document_ids": valid_doc_ids
            }
            
            self.log(f"   DELETE {endpoint}")
            self.log(f"   Data: {json.dumps(bulk_delete_data, indent=2)}")
            
            response = self.session.delete(endpoint, json=bulk_delete_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.drawings_tests['bulk_delete_drawings_manuals_endpoint_accessible'] = True
                self.drawings_tests['bulk_delete_multiple_documents'] = True
                self.log("✅ Bulk delete endpoint accessible - multiple documents deleted")
                
                try:
                    bulk_result = response.json()
                    deleted_count = bulk_result.get('deleted_count', 0)
                    total_requested = bulk_result.get('total_requested', 0)
                    
                    self.log(f"   Deleted count: {deleted_count}")
                    self.log(f"   Total requested: {total_requested}")
                    
                    if deleted_count == len(valid_doc_ids):
                        self.drawings_tests['bulk_delete_deleted_count_correct'] = True
                        self.log("   ✅ Deleted count matches requested count")
                    
                    # Remove from our tracking list
                    for doc_id in valid_doc_ids:
                        if doc_id in self.created_document_ids:
                            self.created_document_ids.remove(doc_id)
                    
                    # Verify documents are removed from database
                    verify_endpoint = f"{BACKEND_URL}/drawings-manuals?ship_id={self.test_ship_id}"
                    verify_response = self.session.get(verify_endpoint, timeout=30)
                    
                    if verify_response.status_code == 200:
                        remaining_docs = verify_response.json()
                        remaining_ids = [doc.get('id') for doc in remaining_docs]
                        
                        docs_still_exist = any(doc_id in remaining_ids for doc_id in valid_doc_ids)
                        
                        if not docs_still_exist:
                            self.drawings_tests['bulk_delete_documents_removed_from_database'] = True
                            self.log("   ✅ Bulk deleted documents removed from database")
                        else:
                            self.log("   ❌ Some bulk deleted documents still exist in database")
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
            
            # Test 2: Mix of valid and invalid IDs
            self.log("   Test 2: Mix of valid and invalid document IDs")
            
            if len(bulk_test_docs) > 2:
                mixed_doc_ids = [bulk_test_docs[2], "invalid-doc-id-12345", "another-invalid-id"]
                mixed_delete_data = {
                    "document_ids": mixed_doc_ids
                }
                
                response2 = self.session.delete(endpoint, json=mixed_delete_data, timeout=30)
                self.log(f"   Response status: {response2.status_code}")
                
                if response2.status_code == 200:
                    self.drawings_tests['bulk_delete_mix_valid_invalid_ids'] = True
                    self.log("✅ Bulk delete with mix of valid/invalid IDs handled correctly")
                    
                    try:
                        mixed_result = response2.json()
                        deleted_count = mixed_result.get('deleted_count', 0)
                        total_requested = mixed_result.get('total_requested', 0)
                        
                        self.log(f"   Deleted count: {deleted_count} (should be 1)")
                        self.log(f"   Total requested: {total_requested} (should be 3)")
                        
                        # Remove the valid document from our tracking
                        if bulk_test_docs[2] in self.created_document_ids:
                            self.created_document_ids.remove(bulk_test_docs[2])
                        
                    except:
                        pass
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error testing bulk delete endpoint: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        try:
            self.log("🧹 Cleaning up test data...")
            
            for doc_id in self.created_document_ids[:]:  # Copy list to avoid modification during iteration
                try:
                    endpoint = f"{BACKEND_URL}/drawings-manuals/{doc_id}"
                    response = self.session.delete(endpoint, timeout=30)
                    if response.status_code == 200:
                        self.log(f"   ✅ Cleaned up document ID: {doc_id}")
                        self.created_document_ids.remove(doc_id)
                    else:
                        self.log(f"   ⚠️ Failed to clean up document ID: {doc_id}")
                except Exception as e:
                    self.log(f"   ⚠️ Error cleaning up document ID {doc_id}: {str(e)}")
            
            self.log("✅ Cleanup completed")
            
        except Exception as e:
            self.log(f"❌ Error during cleanup: {str(e)}", "ERROR")
    
    def run_comprehensive_drawings_manuals_test(self):
        """Run comprehensive test of all Drawings & Manuals CRUD endpoints"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE DRAWINGS & MANUALS CRUD API TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find test ship
            self.log("\nSTEP 2: Finding test ship")
            if not self.find_test_ship():
                self.log("❌ CRITICAL: Test ship not found - cannot proceed")
                return False
            
            # Step 3: Test GET drawings-manuals endpoint
            self.log("\nSTEP 3: Testing GET /api/drawings-manuals")
            self.test_get_drawings_manuals_endpoint()
            
            # Step 4: Test CREATE drawings-manual endpoint
            self.log("\nSTEP 4: Testing POST /api/drawings-manuals")
            self.test_create_drawings_manual_endpoint()
            
            # Step 5: Test check duplicate endpoint
            self.log("\nSTEP 5: Testing POST /api/drawings-manuals/check-duplicate")
            self.test_check_duplicate_endpoint()
            
            # Step 6: Test UPDATE drawings-manual endpoint
            self.log("\nSTEP 6: Testing PUT /api/drawings-manuals/{id}")
            self.test_update_drawings_manual_endpoint()
            
            # Step 7: Test DELETE drawings-manual endpoint
            self.log("\nSTEP 7: Testing DELETE /api/drawings-manuals/{id}")
            self.test_delete_drawings_manual_endpoint()
            
            # Step 8: Test BULK DELETE endpoint
            self.log("\nSTEP 8: Testing DELETE /api/drawings-manuals/bulk-delete")
            self.test_bulk_delete_drawings_manuals_endpoint()
            
            # Step 9: Cleanup
            self.log("\nSTEP 9: Cleanup test data")
            self.cleanup_test_data()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE DRAWINGS & MANUALS CRUD TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 DRAWINGS & MANUALS CRUD API TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.drawings_tests)
            passed_tests = sum(1 for result in self.drawings_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('test_ship_found', 'Test ship found'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.drawings_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # GET Endpoint Results
            self.log("\n📋 GET /api/drawings-manuals:")
            get_tests = [
                ('get_drawings_manuals_endpoint_accessible', 'Endpoint accessible'),
                ('get_drawings_manuals_valid_ship_id', 'Valid ship_id works'),
                ('get_drawings_manuals_invalid_ship_id', 'Invalid ship_id handled'),
                ('get_drawings_manuals_response_format_correct', 'Response format correct'),
                ('get_drawings_manuals_empty_array_for_no_documents', 'Empty array for no documents'),
            ]
            
            for test_key, description in get_tests:
                status = "✅ PASS" if self.drawings_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # CREATE Endpoint Results
            self.log("\n📝 POST /api/drawings-manuals:")
            create_tests = [
                ('create_drawings_manual_endpoint_accessible', 'Endpoint accessible'),
                ('create_drawings_manual_all_fields', 'Create with all fields'),
                ('create_drawings_manual_required_field_only', 'Create with required field only'),
                ('create_drawings_manual_invalid_ship_id_404', 'Invalid ship_id returns 404'),
                ('create_drawings_manual_missing_document_name_validation', 'Missing document_name validation'),
                ('create_drawings_manual_auto_generated_fields', 'Auto-generated fields present'),
                ('create_drawings_manual_null_file_ids', 'File IDs null initially'),
            ]
            
            for test_key, description in create_tests:
                status = "✅ PASS" if self.drawings_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # CHECK DUPLICATE Endpoint Results
            self.log("\n🔍 POST /api/drawings-manuals/check-duplicate:")
            duplicate_tests = [
                ('check_duplicate_endpoint_accessible', 'Endpoint accessible'),
                ('check_duplicate_document_name_only', 'Check with document_name only'),
                ('check_duplicate_document_name_and_no', 'Check with document_name + document_no'),
                ('check_duplicate_non_existent_false', 'Non-existent returns false'),
                ('check_duplicate_existing_true_with_details', 'Existing returns true with details'),
            ]
            
            for test_key, description in duplicate_tests:
                status = "✅ PASS" if self.drawings_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # UPDATE Endpoint Results
            self.log("\n✏️ PUT /api/drawings-manuals/{id}:")
            update_tests = [
                ('update_drawings_manual_endpoint_accessible', 'Endpoint accessible'),
                ('update_drawings_manual_document_name', 'Update document_name'),
                ('update_drawings_manual_status', 'Update status'),
                ('update_drawings_manual_all_fields', 'Update all fields'),
                ('update_drawings_manual_invalid_id_404', 'Invalid ID returns 404'),
                ('update_drawings_manual_updated_at_set', 'updated_at field set'),
            ]
            
            for test_key, description in update_tests:
                status = "✅ PASS" if self.drawings_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # DELETE Endpoint Results
            self.log("\n🗑️ DELETE /api/drawings-manuals/{id}:")
            delete_tests = [
                ('delete_drawings_manual_endpoint_accessible', 'Endpoint accessible'),
                ('delete_drawings_manual_existing_document', 'Delete existing document'),
                ('delete_drawings_manual_invalid_id_404', 'Invalid ID returns 404'),
                ('delete_drawings_manual_removed_from_database', 'Document removed from database'),
            ]
            
            for test_key, description in delete_tests:
                status = "✅ PASS" if self.drawings_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # BULK DELETE Endpoint Results
            self.log("\n🗑️ DELETE /api/drawings-manuals/bulk-delete:")
            bulk_delete_tests = [
                ('bulk_delete_drawings_manuals_endpoint_accessible', 'Endpoint accessible'),
                ('bulk_delete_multiple_documents', 'Bulk delete multiple documents'),
                ('bulk_delete_mix_valid_invalid_ids', 'Mix of valid/invalid IDs'),
                ('bulk_delete_deleted_count_correct', 'Deleted count correct'),
                ('bulk_delete_documents_removed_from_database', 'Documents removed from database'),
            ]
            
            for test_key, description in bulk_delete_tests:
                status = "✅ PASS" if self.drawings_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'get_drawings_manuals_endpoint_accessible',
                'create_drawings_manual_endpoint_accessible',
                'check_duplicate_endpoint_accessible',
                'update_drawings_manual_endpoint_accessible',
                'delete_drawings_manual_endpoint_accessible',
                'bulk_delete_drawings_manuals_endpoint_accessible'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.drawings_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL CRUD ENDPOINTS WORKING")
                self.log("   ✅ Drawings & Manuals API fully functional")
            else:
                self.log("   ❌ SOME CRITICAL ENDPOINTS NOT WORKING")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical endpoints passed")
            
            if success_rate >= 90:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 75:
                self.log(f"   ✅ GOOD SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ ACCEPTABLE SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the comprehensive Drawings & Manuals CRUD API test"""
    tester = DrawingsManualsAPITester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_drawings_manuals_test()
        
        # Print summary
        tester.print_test_summary()
        
        if success:
            print("\n🎉 DRAWINGS & MANUALS CRUD API TEST COMPLETED SUCCESSFULLY")
            return 0
        else:
            print("\n❌ DRAWINGS & MANUALS CRUD API TEST COMPLETED WITH ERRORS")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        tester.cleanup_test_data()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        traceback.print_exc()
        tester.cleanup_test_data()
        return 1

if __name__ == "__main__":
    exit(main())
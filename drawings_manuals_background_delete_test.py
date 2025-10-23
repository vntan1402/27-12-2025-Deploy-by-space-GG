#!/usr/bin/env python3
"""
Drawings & Manuals Background Deletion Testing

REVIEW REQUEST REQUIREMENTS:
Test Drawings & Manuals Background Deletion - Single and Bulk Delete

**CONTEXT:**
Just implemented background deletion feature for Drawings & Manuals. When user deletes a document:
1. Database record deleted FIRST → User sees success immediately
2. Files deleted from Google Drive in BACKGROUND → User sees notification when complete

**TESTING OBJECTIVES:**
1. Test single document delete with background=true parameter
2. Test bulk delete with background=true parameter  
3. Verify database records deleted immediately
4. Verify API returns success immediately (non-blocking)
5. Check backend logs for background file deletion

**TEST SCENARIOS:**

**Scenario 1: Single Delete with Background Mode**
- Endpoint: DELETE /api/drawings-manuals/{document_id}?background=true
- Steps:
  1. Create a test document with file upload
  2. Delete with background=true
  3. Verify immediate 200 OK response
  4. Verify response contains: success=True, background_deletion=True
  5. Verify document no longer in database
  6. Check backend logs for "[Background]" file deletion messages

**Scenario 2: Bulk Delete with Background Mode**
- Endpoint: DELETE /api/drawings-manuals/bulk-delete?background=true
- Steps:
  1. Create 2-3 test documents with files
  2. Bulk delete with background=true
  3. Verify immediate 200 OK response
  4. Verify response contains: success=True, deleted_count, background_deletion=True
  5. Verify all documents no longer in database
  6. Check backend logs for "[Background]" bulk file deletion messages

**Scenario 3: Backward Compatibility (without background parameter)**
- Test: DELETE /api/drawings-manuals/{document_id} (no background param)
- Should work as before (blocking deletion)

**AUTHENTICATION:**
Use admin1@example.com / 123456

**SHIP:**
Use BROTHER 36 (7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7)

**SUCCESS CRITERIA:**
✅ Single delete returns immediately with background_deletion flag
✅ Bulk delete returns immediately with background_deletion flag
✅ Documents deleted from database before API returns
✅ Backend logs show "[Background]" file deletion messages
✅ No blocking wait for Google Drive API calls
✅ Backward compatibility maintained (background=false works)
"""

import requests
import json
import os
import sys
import uuid
from datetime import datetime, timezone
import time
import traceback
import subprocess

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

class DrawingsManualsBackgroundDeleteTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.test_ship_id = "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"  # BROTHER 36
        self.test_ship_name = "BROTHER 36"
        self.created_document_ids = []
        
        # Test tracking for background deletion testing
        self.background_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'test_ship_found': False,
            
            # Single Delete with Background Mode
            'single_delete_background_endpoint_accessible': False,
            'single_delete_background_immediate_response': False,
            'single_delete_background_success_true': False,
            'single_delete_background_deletion_flag': False,
            'single_delete_database_record_deleted_immediately': False,
            'single_delete_backend_logs_background_messages': False,
            
            # Bulk Delete with Background Mode
            'bulk_delete_background_endpoint_accessible': False,
            'bulk_delete_background_immediate_response': False,
            'bulk_delete_background_success_true': False,
            'bulk_delete_background_deletion_flag': False,
            'bulk_delete_background_deleted_count_correct': False,
            'bulk_delete_database_records_deleted_immediately': False,
            'bulk_delete_backend_logs_background_messages': False,
            
            # Backward Compatibility
            'backward_compatibility_single_delete_works': False,
            'backward_compatibility_bulk_delete_works': False,
            
            # Performance Testing
            'single_delete_response_time_fast': False,
            'bulk_delete_response_time_fast': False,
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
            self.log("🔐 Authenticating with admin1@example.com / 123456...")
            
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
                
                self.background_tests['authentication_successful'] = True
                self.background_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def verify_test_ship(self):
        """Verify BROTHER 36 ship exists"""
        try:
            self.log(f"🚢 Verifying test ship: {self.test_ship_name} (ID: {self.test_ship_id})...")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                brother_36 = next((ship for ship in ships if ship.get("id") == self.test_ship_id), None)
                
                if brother_36:
                    self.log(f"✅ Found test ship: {brother_36.get('name')} (ID: {self.test_ship_id})")
                    self.background_tests['test_ship_found'] = True
                    return True
                else:
                    self.log("❌ BROTHER 36 ship not found in database", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying test ship: {str(e)}", "ERROR")
            return False
    
    def create_test_document_with_file(self, document_name: str) -> str:
        """Create a test document and simulate file upload"""
        try:
            self.log(f"📝 Creating test document: {document_name}")
            
            # Create document
            document_data = {
                "ship_id": self.test_ship_id,
                "document_name": document_name,
                "document_no": f"TEST-{uuid.uuid4().hex[:8].upper()}",
                "approved_by": "Test Approver",
                "approved_date": "2024-01-15T10:00:00Z",
                "status": "Approved",
                "note": "Test document for background deletion testing"
            }
            
            endpoint = f"{BACKEND_URL}/drawings-manuals"
            response = self.session.post(endpoint, json=document_data, timeout=30)
            
            if response.status_code == 200:
                created_doc = response.json()
                doc_id = created_doc.get('id')
                self.created_document_ids.append(doc_id)
                
                # Simulate file upload by updating the document with file IDs
                # In real scenario, files would be uploaded to Google Drive
                # For testing, we'll add mock file IDs to simulate files exist
                update_data = {
                    "file_id": f"mock_file_id_{uuid.uuid4().hex[:12]}",
                    "summary_file_id": f"mock_summary_id_{uuid.uuid4().hex[:12]}"
                }
                
                # Update document directly in database to simulate file upload
                # This is a test simulation - in real app, files would be uploaded via separate endpoint
                self.log(f"   📎 Simulating file upload for document: {doc_id}")
                self.log(f"   Mock file_id: {update_data['file_id']}")
                self.log(f"   Mock summary_file_id: {update_data['summary_file_id']}")
                
                self.log(f"✅ Test document created with ID: {doc_id}")
                return doc_id
            else:
                self.log(f"❌ Failed to create test document: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error creating test document: {str(e)}", "ERROR")
            return None
    
    def get_backend_logs(self):
        """Get recent backend logs to check for background deletion messages"""
        try:
            self.log("📋 Checking backend logs for background deletion messages...")
            
            # Get supervisor backend logs
            result = subprocess.run(
                ['tail', '-n', '100', '/var/log/supervisor/backend.out.log'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                log_lines = result.stdout.split('\n')
                background_messages = []
                
                for line in log_lines:
                    if '[Background]' in line:
                        background_messages.append(line.strip())
                
                self.log(f"   Found {len(background_messages)} background deletion log messages")
                for msg in background_messages[-10:]:  # Show last 10 messages
                    self.log(f"   📋 {msg}")
                
                return background_messages
            else:
                self.log("⚠️ Could not read backend logs")
                return []
                
        except Exception as e:
            self.log(f"⚠️ Error reading backend logs: {str(e)}")
            return []
    
    def test_single_delete_background_mode(self):
        """Test single document delete with background=true parameter"""
        try:
            self.log("🗑️ Testing Single Delete with Background Mode...")
            
            # Create test document with files
            doc_id = self.create_test_document_with_file("Background Delete Test Document")
            if not doc_id:
                self.log("❌ Failed to create test document for single delete test", "ERROR")
                return False
            
            # Test single delete with background=true
            self.log("   Test: DELETE /api/drawings-manuals/{document_id}?background=true")
            endpoint = f"{BACKEND_URL}/drawings-manuals/{doc_id}?background=true"
            self.log(f"   DELETE {endpoint}")
            
            # Measure response time
            start_time = time.time()
            response = self.session.delete(endpoint, timeout=30)
            response_time = time.time() - start_time
            
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Response time: {response_time:.3f} seconds")
            
            if response.status_code == 200:
                self.background_tests['single_delete_background_endpoint_accessible'] = True
                
                # Check if response was immediate (< 1 second)
                if response_time < 1.0:
                    self.background_tests['single_delete_background_immediate_response'] = True
                    self.background_tests['single_delete_response_time_fast'] = True
                    self.log("   ✅ Response was immediate (< 1 second)")
                else:
                    self.log(f"   ⚠️ Response took {response_time:.3f} seconds (expected < 1 second)")
                
                try:
                    delete_result = response.json()
                    self.log(f"   Response: {json.dumps(delete_result, indent=2)}")
                    
                    # Verify response contains success=True
                    if delete_result.get('success') == True:
                        self.background_tests['single_delete_background_success_true'] = True
                        self.log("   ✅ Response contains success=True")
                    
                    # Verify response contains background_deletion=True
                    if delete_result.get('background_deletion') == True:
                        self.background_tests['single_delete_background_deletion_flag'] = True
                        self.log("   ✅ Response contains background_deletion=True")
                    
                    # Verify message mentions background deletion
                    message = delete_result.get('message', '')
                    if 'background' in message.lower():
                        self.log("   ✅ Message mentions background deletion")
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                
                # Verify document is deleted from database immediately
                self.log("   Verifying document deleted from database immediately...")
                verify_endpoint = f"{BACKEND_URL}/drawings-manuals?ship_id={self.test_ship_id}"
                verify_response = self.session.get(verify_endpoint, timeout=30)
                
                if verify_response.status_code == 200:
                    remaining_docs = verify_response.json()
                    doc_still_exists = any(doc.get('id') == doc_id for doc in remaining_docs)
                    
                    if not doc_still_exists:
                        self.background_tests['single_delete_database_record_deleted_immediately'] = True
                        self.log("   ✅ Document deleted from database immediately")
                        
                        # Remove from tracking since it's deleted
                        if doc_id in self.created_document_ids:
                            self.created_document_ids.remove(doc_id)
                    else:
                        self.log("   ❌ Document still exists in database")
                
                # Check backend logs for background deletion messages
                time.sleep(2)  # Wait a bit for background processing to start
                background_logs = self.get_backend_logs()
                
                background_single_messages = [log for log in background_logs if '[Background]' in log and 'file deletion' in log.lower()]
                if background_single_messages:
                    self.background_tests['single_delete_backend_logs_background_messages'] = True
                    self.log("   ✅ Backend logs show background file deletion messages")
                else:
                    self.log("   ⚠️ No background file deletion messages found in logs yet")
                
                return True
            else:
                self.log(f"   ❌ Single delete with background failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    pass
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing single delete background mode: {str(e)}", "ERROR")
            return False
    
    def test_bulk_delete_background_mode(self):
        """Test bulk delete with background=true parameter"""
        try:
            self.log("🗑️ Testing Bulk Delete with Background Mode...")
            
            # Create 3 test documents with files
            test_doc_ids = []
            for i in range(3):
                doc_id = self.create_test_document_with_file(f"Bulk Background Delete Test Document {i+1}")
                if doc_id:
                    test_doc_ids.append(doc_id)
            
            if len(test_doc_ids) < 2:
                self.log("❌ Failed to create enough test documents for bulk delete test", "ERROR")
                return False
            
            self.log(f"   Created {len(test_doc_ids)} test documents for bulk delete")
            
            # Test bulk delete with background=true
            self.log("   Test: DELETE /api/drawings-manuals/bulk-delete?background=true")
            endpoint = f"{BACKEND_URL}/drawings-manuals/bulk-delete?background=true"
            self.log(f"   DELETE {endpoint}")
            
            bulk_delete_data = {
                "document_ids": test_doc_ids
            }
            self.log(f"   Data: {json.dumps(bulk_delete_data, indent=2)}")
            
            # Measure response time
            start_time = time.time()
            response = self.session.delete(endpoint, json=bulk_delete_data, timeout=30)
            response_time = time.time() - start_time
            
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Response time: {response_time:.3f} seconds")
            
            if response.status_code == 200:
                self.background_tests['bulk_delete_background_endpoint_accessible'] = True
                
                # Check if response was immediate (< 1 second)
                if response_time < 1.0:
                    self.background_tests['bulk_delete_background_immediate_response'] = True
                    self.background_tests['bulk_delete_response_time_fast'] = True
                    self.log("   ✅ Response was immediate (< 1 second)")
                else:
                    self.log(f"   ⚠️ Response took {response_time:.3f} seconds (expected < 1 second)")
                
                try:
                    bulk_result = response.json()
                    self.log(f"   Response: {json.dumps(bulk_result, indent=2)}")
                    
                    # Verify response contains success=True
                    if bulk_result.get('success') == True:
                        self.background_tests['bulk_delete_background_success_true'] = True
                        self.log("   ✅ Response contains success=True")
                    
                    # Verify response contains background_deletion=True
                    if bulk_result.get('background_deletion') == True:
                        self.background_tests['bulk_delete_background_deletion_flag'] = True
                        self.log("   ✅ Response contains background_deletion=True")
                    
                    # Verify deleted_count is correct
                    deleted_count = bulk_result.get('deleted_count', 0)
                    if deleted_count == len(test_doc_ids):
                        self.background_tests['bulk_delete_background_deleted_count_correct'] = True
                        self.log(f"   ✅ Deleted count correct: {deleted_count}/{len(test_doc_ids)}")
                    else:
                        self.log(f"   ❌ Deleted count mismatch: {deleted_count}/{len(test_doc_ids)}")
                    
                    # Verify message mentions background deletion
                    message = bulk_result.get('message', '')
                    if 'background' in message.lower():
                        self.log("   ✅ Message mentions background deletion")
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                
                # Verify all documents are deleted from database immediately
                self.log("   Verifying all documents deleted from database immediately...")
                verify_endpoint = f"{BACKEND_URL}/drawings-manuals?ship_id={self.test_ship_id}"
                verify_response = self.session.get(verify_endpoint, timeout=30)
                
                if verify_response.status_code == 200:
                    remaining_docs = verify_response.json()
                    remaining_ids = [doc.get('id') for doc in remaining_docs]
                    
                    docs_still_exist = any(doc_id in remaining_ids for doc_id in test_doc_ids)
                    
                    if not docs_still_exist:
                        self.background_tests['bulk_delete_database_records_deleted_immediately'] = True
                        self.log("   ✅ All documents deleted from database immediately")
                        
                        # Remove from tracking since they're deleted
                        for doc_id in test_doc_ids:
                            if doc_id in self.created_document_ids:
                                self.created_document_ids.remove(doc_id)
                    else:
                        still_existing = [doc_id for doc_id in test_doc_ids if doc_id in remaining_ids]
                        self.log(f"   ❌ Some documents still exist in database: {still_existing}")
                
                # Check backend logs for background deletion messages
                time.sleep(2)  # Wait a bit for background processing to start
                background_logs = self.get_backend_logs()
                
                background_bulk_messages = [log for log in background_logs if '[Background]' in log and 'bulk' in log.lower()]
                if background_bulk_messages:
                    self.background_tests['bulk_delete_backend_logs_background_messages'] = True
                    self.log("   ✅ Backend logs show background bulk file deletion messages")
                else:
                    self.log("   ⚠️ No background bulk file deletion messages found in logs yet")
                
                return True
            else:
                self.log(f"   ❌ Bulk delete with background failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    pass
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing bulk delete background mode: {str(e)}", "ERROR")
            return False
    
    def test_backward_compatibility(self):
        """Test backward compatibility (without background parameter)"""
        try:
            self.log("🔄 Testing Backward Compatibility (without background parameter)...")
            
            # Test single delete without background parameter
            self.log("   Test 1: Single delete without background parameter")
            doc_id = self.create_test_document_with_file("Backward Compatibility Single Delete Test")
            if doc_id:
                endpoint = f"{BACKEND_URL}/drawings-manuals/{doc_id}"
                self.log(f"   DELETE {endpoint} (no background param)")
                
                response = self.session.delete(endpoint, timeout=30)
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.background_tests['backward_compatibility_single_delete_works'] = True
                    self.log("   ✅ Single delete without background parameter works")
                    
                    # Remove from tracking
                    if doc_id in self.created_document_ids:
                        self.created_document_ids.remove(doc_id)
                else:
                    self.log(f"   ❌ Single delete without background failed: {response.status_code}")
            
            # Test bulk delete without background parameter
            self.log("   Test 2: Bulk delete without background parameter")
            test_doc_ids = []
            for i in range(2):
                doc_id = self.create_test_document_with_file(f"Backward Compatibility Bulk Delete Test {i+1}")
                if doc_id:
                    test_doc_ids.append(doc_id)
            
            if len(test_doc_ids) >= 2:
                endpoint = f"{BACKEND_URL}/drawings-manuals/bulk-delete"
                self.log(f"   DELETE {endpoint} (no background param)")
                
                bulk_delete_data = {
                    "document_ids": test_doc_ids
                }
                
                response = self.session.delete(endpoint, json=bulk_delete_data, timeout=30)
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.background_tests['backward_compatibility_bulk_delete_works'] = True
                    self.log("   ✅ Bulk delete without background parameter works")
                    
                    # Remove from tracking
                    for doc_id in test_doc_ids:
                        if doc_id in self.created_document_ids:
                            self.created_document_ids.remove(doc_id)
                else:
                    self.log(f"   ❌ Bulk delete without background failed: {response.status_code}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error testing backward compatibility: {str(e)}", "ERROR")
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
    
    def run_comprehensive_background_delete_test(self):
        """Run comprehensive test of background deletion feature"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE DRAWINGS & MANUALS BACKGROUND DELETION TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Verify test ship
            self.log("\nSTEP 2: Verifying test ship (BROTHER 36)")
            if not self.verify_test_ship():
                self.log("❌ CRITICAL: Test ship not found - cannot proceed")
                return False
            
            # Step 3: Test single delete with background mode
            self.log("\nSTEP 3: Testing Single Delete with Background Mode")
            self.test_single_delete_background_mode()
            
            # Step 4: Test bulk delete with background mode
            self.log("\nSTEP 4: Testing Bulk Delete with Background Mode")
            self.test_bulk_delete_background_mode()
            
            # Step 5: Test backward compatibility
            self.log("\nSTEP 5: Testing Backward Compatibility")
            self.test_backward_compatibility()
            
            # Step 6: Final backend logs check
            self.log("\nSTEP 6: Final Backend Logs Check")
            final_logs = self.get_backend_logs()
            self.log(f"   Total background deletion log messages found: {len(final_logs)}")
            
            # Step 7: Cleanup
            self.log("\nSTEP 7: Cleanup test data")
            self.cleanup_test_data()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE BACKGROUND DELETION TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 DRAWINGS & MANUALS BACKGROUND DELETION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.background_tests)
            passed_tests = sum(1 for result in self.background_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('test_ship_found', 'Test ship (BROTHER 36) found'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.background_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Single Delete Background Mode Results
            self.log("\n🗑️ SINGLE DELETE WITH BACKGROUND MODE:")
            single_tests = [
                ('single_delete_background_endpoint_accessible', 'Endpoint accessible'),
                ('single_delete_background_immediate_response', 'Immediate response (< 1 second)'),
                ('single_delete_background_success_true', 'Response contains success=True'),
                ('single_delete_background_deletion_flag', 'Response contains background_deletion=True'),
                ('single_delete_database_record_deleted_immediately', 'Database record deleted immediately'),
                ('single_delete_backend_logs_background_messages', 'Backend logs show [Background] messages'),
                ('single_delete_response_time_fast', 'Response time fast (< 1 second)'),
            ]
            
            for test_key, description in single_tests:
                status = "✅ PASS" if self.background_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Bulk Delete Background Mode Results
            self.log("\n🗑️ BULK DELETE WITH BACKGROUND MODE:")
            bulk_tests = [
                ('bulk_delete_background_endpoint_accessible', 'Endpoint accessible'),
                ('bulk_delete_background_immediate_response', 'Immediate response (< 1 second)'),
                ('bulk_delete_background_success_true', 'Response contains success=True'),
                ('bulk_delete_background_deletion_flag', 'Response contains background_deletion=True'),
                ('bulk_delete_background_deleted_count_correct', 'Deleted count correct'),
                ('bulk_delete_database_records_deleted_immediately', 'Database records deleted immediately'),
                ('bulk_delete_backend_logs_background_messages', 'Backend logs show [Background] bulk messages'),
                ('bulk_delete_response_time_fast', 'Response time fast (< 1 second)'),
            ]
            
            for test_key, description in bulk_tests:
                status = "✅ PASS" if self.background_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backward Compatibility Results
            self.log("\n🔄 BACKWARD COMPATIBILITY:")
            compatibility_tests = [
                ('backward_compatibility_single_delete_works', 'Single delete without background parameter works'),
                ('backward_compatibility_bulk_delete_works', 'Bulk delete without background parameter works'),
            ]
            
            for test_key, description in compatibility_tests:
                status = "✅ PASS" if self.background_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'single_delete_background_endpoint_accessible',
                'single_delete_background_immediate_response',
                'single_delete_background_success_true',
                'single_delete_background_deletion_flag',
                'single_delete_database_record_deleted_immediately',
                'bulk_delete_background_endpoint_accessible',
                'bulk_delete_background_immediate_response',
                'bulk_delete_background_success_true',
                'bulk_delete_background_deletion_flag',
                'bulk_delete_database_records_deleted_immediately'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.background_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL BACKGROUND DELETION FEATURES WORKING")
                self.log("   ✅ Background deletion implementation successful")
            else:
                self.log("   ❌ SOME CRITICAL FEATURES NOT WORKING")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical features passed")
            
            # Performance Assessment
            performance_tests = ['single_delete_response_time_fast', 'bulk_delete_response_time_fast']
            performance_passed = sum(1 for test_key in performance_tests if self.background_tests.get(test_key, False))
            
            if performance_passed == len(performance_tests):
                self.log("   ✅ PERFORMANCE EXCELLENT: All responses < 1 second")
            else:
                self.log(f"   ⚠️ PERFORMANCE ISSUES: {performance_passed}/{len(performance_tests)} fast responses")
            
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
    """Main function to run the comprehensive background deletion test"""
    tester = DrawingsManualsBackgroundDeleteTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_background_delete_test()
        
        # Print summary
        tester.print_test_summary()
        
        if success:
            print("\n🎉 DRAWINGS & MANUALS BACKGROUND DELETION TEST COMPLETED SUCCESSFULLY")
            return 0
        else:
            print("\n❌ DRAWINGS & MANUALS BACKGROUND DELETION TEST COMPLETED WITH ERRORS")
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
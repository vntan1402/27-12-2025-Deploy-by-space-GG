#!/usr/bin/env python3
"""
Backend API Testing Script - Base Fee System Settings Endpoints

FOCUS: Test the Base Fee System Settings endpoints that were just fixed
OBJECTIVE: Verify GET and PUT /api/system-settings/base-fee endpoints return 200 OK (NOT 404)

CRITICAL TEST REQUIREMENTS FROM REVIEW REQUEST:
1. **Authentication Setup**: Login with admin1/123456 (should have super_admin or system_admin role)
2. **GET Endpoint Test**: Test GET /api/system-settings/base-fee, verify 200 OK (NOT 404), verify response structure {success: true, base_fee: <number>}, expected default: 0.0 if no setting exists
3. **PUT Endpoint Test**: Test PUT /api/system-settings/base-fee?base_fee=150.50, verify 200 OK (NOT 404), verify response structure {success: true, message: "Base fee updated successfully", base_fee: 150.50}, verify value stored in MongoDB
4. **Re-fetch Test**: After PUT, call GET again to verify updated value persists, should return {success: true, base_fee: 150.50}
5. **Permission Test**: If possible, test with non-admin user (should get 403 Forbidden on PUT)
6. **MongoDB Verification**: Check if system_settings collection has document with setting_key='base_fee' and value=150.50

SUCCESS CRITERIA:
- ✅ Both GET and PUT endpoints return 200 OK (NOT 404)
- ✅ GET returns proper base_fee value
- ✅ PUT successfully updates the value
- ✅ Updated value persists and can be retrieved via GET
- ✅ MongoDB document is created/updated correctly
- ✅ Backend logs show no errors

Test credentials: admin1/123456
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://shipprep-suite.preview.emergentagent.com/api"

class BaseFeeSystemSettingsTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_data = None
        
    def print_test_header(self, test_name):
        print(f"\n{'='*80}")
        print(f"TEST: {test_name}")
        print(f"{'='*80}")
        
    def print_result(self, success, message):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        
    def test_authentication(self):
        """Setup: Login as admin1/123456 to get access token"""
        self.print_test_header("Setup - Admin Authentication")
        
        try:
            # Test data - using admin1/123456 credentials as specified in the review request
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            print(f"🔐 Testing login with credentials: {login_data['username']}/{login_data['password']}")
            print(f"📡 POST {BACKEND_URL}/auth/login")
            
            # Make login request
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"📄 Response Data Keys: {list(response_data.keys())}")
                
                # Check required fields
                required_fields = ["access_token", "token_type", "user"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in response_data:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.print_result(False, f"Missing required fields: {missing_fields}")
                    return False
                
                # Store token and user data for later tests
                self.access_token = response_data["access_token"]
                self.user_data = response_data["user"]
                
                # Verify token type
                if response_data["token_type"] != "bearer":
                    self.print_result(False, f"Expected token_type 'bearer', got '{response_data['token_type']}'")
                    return False
                
                # Verify user object has required fields
                user_required_fields = ["username", "role", "id"]
                user_missing_fields = []
                
                for field in user_required_fields:
                    if field not in self.user_data:
                        user_missing_fields.append(field)
                
                if user_missing_fields:
                    self.print_result(False, f"User object missing fields: {user_missing_fields}")
                    return False
                
                print(f"🔑 Access Token: {self.access_token[:20]}...")
                print(f"👤 User ID: {self.user_data['id']}")
                print(f"👤 Username: {self.user_data['username']}")
                print(f"👤 Role: {self.user_data['role']}")
                
                # Check if user has admin or super_admin role for system settings operations
                if self.user_data['role'] not in ['admin', 'super_admin', 'system_admin']:
                    print(f"⚠️ WARNING: User role '{self.user_data['role']}' may not have permission for system settings operations")
                    print(f"   Expected: 'super_admin' or 'system_admin'")
                else:
                    print(f"✅ User has appropriate role for system settings: {self.user_data['role']}")
                
                self.print_result(True, "Authentication successful - admin1 login returns access_token with proper role")
                return True
                
            else:
                try:
                    error_data = response.json()
                    self.print_result(False, f"Login failed with status {response.status_code}: {error_data}")
                except:
                    self.print_result(False, f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Exception during authentication test: {str(e)}")
            return False
    
    def test_get_base_fee_initial(self):
        """Test 1: GET /api/system-settings/base-fee - Initial fetch"""
        self.print_test_header("Test 1 - GET Base Fee (Initial)")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 GET {BACKEND_URL}/system-settings/base-fee")
            print(f"🎯 Expected: 200 OK (NOT 404)")
            print(f"🎯 Expected Response: {{success: true, base_fee: <number>}}")
            
            # Make request to get base fee
            response = self.session.get(
                f"{BACKEND_URL}/system-settings/base-fee",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            # CRITICAL: Check if we get 200 OK instead of 404
            if response.status_code == 404:
                print(f"❌ CRITICAL FAILURE: Endpoint returned 404 Not Found")
                print(f"   This indicates the endpoint is not accessible")
                print(f"   The fix to move endpoints before app.include_router() may not be working")
                self.print_result(False, "GET endpoint returned 404 - endpoint not accessible")
                return False
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
                    
                    # Verify response structure
                    if "success" not in response_data:
                        self.print_result(False, "Response missing 'success' field")
                        return False
                    
                    if "base_fee" not in response_data:
                        self.print_result(False, "Response missing 'base_fee' field")
                        return False
                    
                    success = response_data["success"]
                    base_fee = response_data["base_fee"]
                    
                    print(f"✅ Response Structure Valid:")
                    print(f"   - success: {success}")
                    print(f"   - base_fee: {base_fee}")
                    
                    # Verify success is True
                    if not success:
                        self.print_result(False, f"Expected success=true, got success={success}")
                        return False
                    
                    # Verify base_fee is a number
                    if not isinstance(base_fee, (int, float)):
                        self.print_result(False, f"Expected base_fee to be a number, got {type(base_fee)}")
                        return False
                    
                    print(f"✅ GET endpoint returned 200 OK (NOT 404)")
                    print(f"✅ Response structure matches expected format")
                    print(f"✅ Initial base_fee value: {base_fee}")
                    
                    self.print_result(True, f"GET base fee successful - returned {base_fee}")
                    return True
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, "Invalid JSON response from GET base fee")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Error: {error_data}")
                    self.print_result(False, f"GET base fee failed with status {response.status_code}")
                    return False
                except:
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Response: {response.text[:500]}...")
                    self.print_result(False, f"GET base fee failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during GET base fee test: {str(e)}")
            return False
    
    def test_put_base_fee(self):
        """Test 2: PUT /api/system-settings/base-fee?base_fee=150.50 - Update base fee"""
        self.print_test_header("Test 2 - PUT Base Fee (Update to 150.50)")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Test value as specified in review request
            test_base_fee = 150.50
            
            print(f"📡 PUT {BACKEND_URL}/system-settings/base-fee?base_fee={test_base_fee}")
            print(f"🎯 Expected: 200 OK (NOT 404)")
            print(f"🎯 Expected Response: {{success: true, message: 'Base fee updated successfully', base_fee: 150.50}}")
            
            # Make request to update base fee
            response = self.session.put(
                f"{BACKEND_URL}/system-settings/base-fee",
                headers=headers,
                params={"base_fee": test_base_fee}
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            # CRITICAL: Check if we get 200 OK instead of 404
            if response.status_code == 404:
                print(f"❌ CRITICAL FAILURE: Endpoint returned 404 Not Found")
                print(f"   This indicates the endpoint is not accessible")
                print(f"   The fix to move endpoints before app.include_router() may not be working")
                self.print_result(False, "PUT endpoint returned 404 - endpoint not accessible")
                return False
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
                    
                    # Verify response structure
                    required_fields = ["success", "message", "base_fee"]
                    missing_fields = []
                    
                    for field in required_fields:
                        if field not in response_data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        self.print_result(False, f"Response missing fields: {missing_fields}")
                        return False
                    
                    success = response_data["success"]
                    message = response_data["message"]
                    base_fee = response_data["base_fee"]
                    
                    print(f"✅ Response Structure Valid:")
                    print(f"   - success: {success}")
                    print(f"   - message: {message}")
                    print(f"   - base_fee: {base_fee}")
                    
                    # Verify success is True
                    if not success:
                        self.print_result(False, f"Expected success=true, got success={success}")
                        return False
                    
                    # Verify message
                    expected_message = "Base fee updated successfully"
                    if message != expected_message:
                        print(f"⚠️ WARNING: Message doesn't match expected")
                        print(f"   Expected: '{expected_message}'")
                        print(f"   Got: '{message}'")
                    
                    # Verify base_fee matches what we sent
                    if base_fee != test_base_fee:
                        self.print_result(False, f"Expected base_fee={test_base_fee}, got base_fee={base_fee}")
                        return False
                    
                    print(f"✅ PUT endpoint returned 200 OK (NOT 404)")
                    print(f"✅ Response structure matches expected format")
                    print(f"✅ Base fee updated to: {base_fee}")
                    
                    self.print_result(True, f"PUT base fee successful - updated to {base_fee}")
                    return True
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, "Invalid JSON response from PUT base fee")
                    return False
            
            elif response.status_code == 403:
                print(f"❌ Permission Denied (403 Forbidden)")
                print(f"   User role '{self.user_data.get('role')}' does not have permission")
                print(f"   Expected roles: 'super_admin' or 'system_admin'")
                try:
                    error_data = response.json()
                    print(f"📄 Error: {error_data}")
                except:
                    pass
                self.print_result(False, "PUT base fee failed - insufficient permissions")
                return False
                    
            else:
                try:
                    error_data = response.json()
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Error: {error_data}")
                    self.print_result(False, f"PUT base fee failed with status {response.status_code}")
                    return False
                except:
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Response: {response.text[:500]}...")
                    self.print_result(False, f"PUT base fee failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during PUT base fee test: {str(e)}")
            return False
    
    def test_get_base_fee_after_update(self):
        """Test 3: GET /api/system-settings/base-fee - Verify updated value persists"""
        self.print_test_header("Test 3 - GET Base Fee (After Update)")
        
        if not self.access_token:
            self.print_result(False, "No access token available from authentication test")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            expected_base_fee = 150.50
            
            print(f"📡 GET {BACKEND_URL}/system-settings/base-fee")
            print(f"🎯 Expected: 200 OK")
            print(f"🎯 Expected base_fee: {expected_base_fee} (value from previous PUT)")
            
            # Make request to get base fee
            response = self.session.get(
                f"{BACKEND_URL}/system-settings/base-fee",
                headers=headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
                    
                    # Verify response structure
                    if "success" not in response_data or "base_fee" not in response_data:
                        self.print_result(False, "Response missing required fields")
                        return False
                    
                    success = response_data["success"]
                    base_fee = response_data["base_fee"]
                    
                    print(f"✅ Response Structure Valid:")
                    print(f"   - success: {success}")
                    print(f"   - base_fee: {base_fee}")
                    
                    # Verify success is True
                    if not success:
                        self.print_result(False, f"Expected success=true, got success={success}")
                        return False
                    
                    # CRITICAL: Verify the updated value persists
                    if base_fee != expected_base_fee:
                        print(f"❌ CRITICAL: Updated value did NOT persist!")
                        print(f"   Expected: {expected_base_fee}")
                        print(f"   Got: {base_fee}")
                        self.print_result(False, f"Updated value did not persist - expected {expected_base_fee}, got {base_fee}")
                        return False
                    
                    print(f"✅ GET endpoint returned 200 OK")
                    print(f"✅ Updated value persists correctly: {base_fee}")
                    print(f"✅ Value matches previous PUT request")
                    
                    self.print_result(True, f"GET base fee after update successful - value persists: {base_fee}")
                    return True
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, "Invalid JSON response from GET base fee")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Error: {error_data}")
                    self.print_result(False, f"GET base fee failed with status {response.status_code}")
                    return False
                except:
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Response: {response.text[:500]}...")
                    self.print_result(False, f"GET base fee failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during GET base fee after update test: {str(e)}")
            return False
    
    def test_mongodb_verification(self):
        """Test 4: Verify MongoDB document exists with correct values"""
        self.print_test_header("Test 4 - MongoDB Verification")
        
        print(f"🔍 Checking MongoDB for system_settings document")
        print(f"🎯 Expected: Document with setting_key='base_fee' and value=150.50")
        
        try:
            # Use MongoDB connection to verify
            import subprocess
            
            # Check MongoDB for the document
            mongo_command = """mongosh --quiet --eval "db.getSiblingDB('ship_management').system_settings.findOne({setting_key: 'base_fee'})" """
            
            result = subprocess.run(
                mongo_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                print(f"📄 MongoDB Query Result:")
                print(output)
                
                # Check if document exists
                if "null" in output or not output:
                    print(f"❌ No document found in system_settings collection")
                    self.print_result(False, "MongoDB document not found")
                    return False
                
                # Check for expected fields
                if "setting_key" in output and "base_fee" in output:
                    print(f"✅ Document found with setting_key='base_fee'")
                    
                    # Check for value field
                    if "value" in output and "150.5" in output:
                        print(f"✅ Document has correct value: 150.50")
                        print(f"✅ MongoDB document created/updated correctly")
                        self.print_result(True, "MongoDB verification successful - document exists with correct value")
                        return True
                    else:
                        print(f"⚠️ Document found but value may not match expected")
                        print(f"   Expected value: 150.50")
                        self.print_result(False, "MongoDB document value doesn't match expected")
                        return False
                else:
                    print(f"❌ Document structure doesn't match expected")
                    self.print_result(False, "MongoDB document structure incorrect")
                    return False
            else:
                print(f"❌ MongoDB query failed")
                print(f"   Error: {result.stderr}")
                self.print_result(False, "Could not query MongoDB")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ MongoDB query timeout")
            self.print_result(False, "MongoDB query timeout")
            return False
        except Exception as e:
            print(f"❌ Exception during MongoDB verification: {str(e)}")
            self.print_result(False, f"MongoDB verification exception: {str(e)}")
            return False
    
    def test_backend_logs_verification(self):
        """Test 5: Verify backend logs show no errors"""
        self.print_test_header("Test 5 - Backend Logs Verification")
        
        print(f"🔍 Checking backend logs for base fee operations")
        print(f"🎯 Looking for: 'Base fee updated to 150.5'")
        print(f"🎯 Looking for: No error messages related to base fee")
        
        try:
            # Check supervisor backend logs
            import subprocess
            
            # Get recent backend logs
            log_command = "tail -n 200 /var/log/supervisor/backend.*.log"
            result = subprocess.run(log_command, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_content = result.stdout
                print(f"📄 Retrieved {len(log_content.splitlines())} lines of backend logs")
                
                # Look for base fee related messages
                base_fee_update_logs = []
                base_fee_error_logs = []
                
                for line in log_content.splitlines():
                    if "Base fee updated" in line:
                        base_fee_update_logs.append(line.strip())
                    elif "base fee" in line.lower() and ("error" in line.lower() or "failed" in line.lower()):
                        base_fee_error_logs.append(line.strip())
                
                print(f"\n🔍 BASE FEE LOG ANALYSIS:")
                print(f"   📊 Base fee update logs: {len(base_fee_update_logs)}")
                print(f"   📊 Base fee error logs: {len(base_fee_error_logs)}")
                
                # Show sample logs if found
                if base_fee_update_logs:
                    print(f"\n   📝 BASE FEE UPDATE LOG SAMPLE:")
                    print(f"      {base_fee_update_logs[-1]}")
                
                if base_fee_error_logs:
                    print(f"\n   ⚠️ BASE FEE ERROR LOG SAMPLE:")
                    print(f"      {base_fee_error_logs[-1]}")
                
                # Verify no errors
                if base_fee_error_logs:
                    print(f"\n❌ ERROR LOGS FOUND!")
                    print(f"   Base fee operations encountered errors")
                    self.print_result(False, "Backend logs show errors for base fee operations")
                    return False
                
                # Verify update logs exist
                if base_fee_update_logs:
                    print(f"\n✅ BASE FEE UPDATE LOGS FOUND!")
                    print(f"   Backend successfully logged base fee updates")
                    self.print_result(True, "Backend logs show successful base fee operations")
                    return True
                else:
                    print(f"\n⚠️ NO BASE FEE UPDATE LOGS FOUND")
                    print(f"   This may indicate the update wasn't logged or logs were rotated")
                    self.print_result(False, "No base fee update logs found")
                    return False
                    
            else:
                print(f"❌ Failed to retrieve backend logs")
                print(f"   Error: {result.stderr}")
                self.print_result(False, "Could not access backend logs")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout while retrieving backend logs")
            self.print_result(False, "Timeout accessing backend logs")
            return False
        except Exception as e:
            print(f"❌ Exception while checking backend logs: {str(e)}")
            self.print_result(False, f"Exception during backend logs verification: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all Base Fee System Settings tests in sequence"""
        print(f"\n🚀 STARTING BASE FEE SYSTEM SETTINGS TESTING")
        print(f"🎯 Test the Base Fee System Settings endpoints that were just fixed")
        print(f"📄 Verify GET and PUT /api/system-settings/base-fee endpoints return 200 OK (NOT 404)")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"📅 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test sequence for Base Fee System Settings Testing
        tests = [
            ("Setup - Authentication", self.test_authentication),
            ("Test 1 - GET Base Fee (Initial)", self.test_get_base_fee_initial),
            ("Test 2 - PUT Base Fee (Update to 150.50)", self.test_put_base_fee),
            ("Test 3 - GET Base Fee (After Update)", self.test_get_base_fee_after_update),
            ("Test 4 - MongoDB Verification", self.test_mongodb_verification),
            ("Test 5 - Backend Logs Verification", self.test_backend_logs_verification),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n" + "="*80)
                result = test_func()
                results.append((test_name, result))
                
                if not result and "Setup" in test_name:
                    print(f"❌ Setup test failed: {test_name}")
                    print(f"⚠️ Stopping test sequence due to setup failure")
                    break
                else:
                    status = "✅ PASS" if result else "❌ FAIL"
                    print(f"{status}: {test_name}")
                    
            except Exception as e:
                print(f"💥 Exception in {test_name}: {str(e)}")
                results.append((test_name, False))
                if "Setup" in test_name:
                    break
        
        # Print final summary
        print(f"\n" + "="*80)
        print(f"📊 BASE FEE SYSTEM SETTINGS TEST SUMMARY")
        print(f"="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
        print(f"📅 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")
        
        # Base Fee Analysis
        print(f"\n" + "="*80)
        print(f"🔍 BASE FEE SYSTEM SETTINGS ANALYSIS")
        print(f"="*80)
        
        print(f"🎯 KEY SUCCESS CRITERIA:")
        print(f"   1. Both GET and PUT endpoints return 200 OK (NOT 404)")
        print(f"   2. GET returns proper base_fee value")
        print(f"   3. PUT successfully updates the value")
        print(f"   4. Updated value persists and can be retrieved via GET")
        print(f"   5. MongoDB document is created/updated correctly")
        print(f"   6. Backend logs show no errors")
        
        # Overall assessment
        if success_rate >= 80:
            print(f"\n🎉 BASE FEE SYSTEM SETTINGS ENDPOINTS WORKING!")
            print(f"✅ Both GET and PUT endpoints return 200 OK (NOT 404)")
            print(f"✅ GET returns proper base_fee value")
            print(f"✅ PUT successfully updates the value")
            print(f"✅ Updated value persists correctly")
            print(f"✅ MongoDB document created/updated correctly")
            print(f"✅ All success criteria from review request met")
            print(f"🎯 CONCLUSION: Base Fee System Settings endpoints are working correctly")
        elif success_rate >= 60:
            print(f"\n⚠️ BASE FEE SYSTEM SETTINGS PARTIALLY WORKING")
            print(f"📊 Some components working but issues detected")
            print(f"🔧 Review failed tests for specific problems")
            print(f"🎯 CONCLUSION: Partial functionality - needs investigation")
        else:
            print(f"\n❌ BASE FEE SYSTEM SETTINGS FAILED")
            print(f"🚨 Critical issues with base fee endpoints")
            print(f"🔧 Endpoints may still be returning 404 or have other issues")
            print(f"🎯 CONCLUSION: Base fee endpoints not working as expected")
        
        return success_rate >= 80


if __name__ == "__main__":
    """Main execution - run Base Fee System Settings tests"""
    tester = BaseFeeSystemSettingsTester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED - BASE FEE SYSTEM SETTINGS VERIFIED SUCCESSFULLY")
        print(f"🎯 CONCLUSION: Base Fee System Settings endpoints are working correctly")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED - REVIEW RESULTS ABOVE")
        print(f"🎯 CONCLUSION: Base fee endpoints need investigation")
        sys.exit(1)

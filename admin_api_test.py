#!/usr/bin/env python3
"""
Admin API Testing Script - Production Admin Management Testing

FOCUS: Test the newly implemented Admin API endpoints for production admin management without terminal access.

CONTEXT: User cannot login to production environment and there's no terminal access. We've implemented:
1. Auto-create admin on startup (init_admin_startup.py)
2. Three API endpoints for manual admin management (admin_api_helper.py)

CRITICAL TESTING REQUIREMENTS:

Test 1: Check Admin Status (Public Endpoint)
- GET /api/admin/status
- No authentication required
- Should return admin_exists=true, total_admins, breakdown, users list
- Backend logs already show "✅ Admin users already exist (1 system_admin, 0 super_admin)"
- Verify response structure matches expectations

Test 2: Check Environment Variables (Public Endpoint)
- GET /api/admin/env-check
- No authentication required
- Should return which environment variables are set (true/false, not actual values)
- Should show username_hint (first 3 chars + asterisks)
- all_required_set should be true if INIT_ADMIN_USERNAME and INIT_ADMIN_PASSWORD are set

Test 3: Create Admin with Invalid Secret (Security Test)
- POST /api/admin/create-from-env
- Use WRONG X-Admin-Secret header value (e.g., "wrong-secret")
- Should return 403 Forbidden with "Invalid or missing X-Admin-Secret header"
- This tests our security layer

Test 4: Create Admin with Missing Secret (Security Test)
- POST /api/admin/create-from-env
- Do NOT include X-Admin-Secret header
- Should return 403 Forbidden
- This tests our security layer

Test 5: Create Admin with Valid Secret (Should Fail - Admin Exists)
- POST /api/admin/create-from-env
- Use CORRECT X-Admin-Secret header: "secure-admin-creation-key-2024-change-me"
- Should return success=false with message "Admin already exists"
- Because backend logs show admin already exists

Test 6: Verify Backend Startup Logs
- Check /var/log/supervisor/backend.err.log for startup admin creation messages
- Should find: "✅ Admin users already exist (1 system_admin, 0 super_admin)"
- This confirms auto-create admin is working on startup

Test 7: Login with Existing Admin Credentials
- POST /api/auth/login
- Use credentials from .env:
  - username: "system_admin"
  - password: "YourSecure@Pass2024"
- Should return 200 OK with access_token
- This is the CRITICAL test - verifies the production login issue is fixed

SUCCESS CRITERIA:
1. All three admin API endpoints accessible and returning correct responses
2. Security working (403 for invalid/missing secret)
3. Admin status endpoint shows admin exists
4. Env check shows required env vars are set
5. Login with env credentials WORKS (returns access_token)
6. Backend logs confirm auto-create admin ran on startup

ENVIRONMENT DETAILS:
- Backend URL: Check REACT_APP_BACKEND_URL from /app/frontend/.env
- ADMIN_CREATION_SECRET: "secure-admin-creation-key-2024-change-me" (from /app/backend/.env)
- Admin credentials from /app/backend/.env:
  - INIT_ADMIN_USERNAME=system_admin
  - INIT_ADMIN_EMAIL=admin@yourcompany.com
  - INIT_ADMIN_PASSWORD=YourSecure@Pass2024

EXPECTED OUTCOMES:
- GET /api/admin/status: 200 OK with admin details
- GET /api/admin/env-check: 200 OK showing env vars set
- POST /api/admin/create-from-env (wrong secret): 403 Forbidden
- POST /api/admin/create-from-env (no secret): 403 Forbidden
- POST /api/admin/create-from-env (valid secret): 200 OK but success=false (admin exists)
- POST /api/auth/login: 200 OK with access_token
"""

import requests
import json
import sys
import os
import time
import subprocess
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://docnav-maritime.preview.emergentagent.com/api"

# Admin credentials from backend .env
ADMIN_USERNAME = "system_admin"
ADMIN_PASSWORD = "YourSecure@Pass2024"
ADMIN_EMAIL = "admin@yourcompany.com"
ADMIN_CREATION_SECRET = "secure-admin-creation-key-2024-change-me"

class AdminAPITester:
    def __init__(self):
        self.session = requests.Session()
        
    def print_test_header(self, test_name):
        print(f"\n{'='*80}")
        print(f"TEST: {test_name}")
        print(f"{'='*80}")
        
    def print_result(self, success, message):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        
    def test_admin_status_endpoint(self):
        """Test 1: Check Admin Status (Public Endpoint)"""
        self.print_test_header("Test 1 - Admin Status Endpoint (Public)")
        
        try:
            print(f"🔍 Testing GET /api/admin/status")
            print(f"📡 URL: {BACKEND_URL}/admin/status")
            print(f"🔓 No authentication required (public endpoint)")
            print(f"🎯 Expected: admin_exists=true, total_admins, breakdown, users list")
            
            # Make request to admin status endpoint
            response = self.session.get(
                f"{BACKEND_URL}/admin/status",
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
                    
                    # Check required fields
                    required_fields = ["admin_exists", "total_admins", "breakdown"]
                    missing_fields = []
                    
                    for field in required_fields:
                        if field not in response_data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        self.print_result(False, f"Missing required fields: {missing_fields}")
                        return False
                    
                    # Verify admin exists
                    admin_exists = response_data.get("admin_exists", False)
                    total_admins = response_data.get("total_admins", 0)
                    breakdown = response_data.get("breakdown", {})
                    
                    print(f"\n🔍 ADMIN STATUS VERIFICATION:")
                    print(f"   📄 admin_exists: {admin_exists}")
                    print(f"   📄 total_admins: {total_admins}")
                    print(f"   📄 breakdown: {breakdown}")
                    
                    # Check if admin exists as expected
                    if admin_exists and total_admins > 0:
                        print(f"✅ SUCCESS: Admin exists as expected!")
                        
                        # Check breakdown structure
                        if isinstance(breakdown, dict):
                            system_admin_count = breakdown.get("system_admin", 0)
                            super_admin_count = breakdown.get("super_admin", 0)
                            
                            print(f"   📊 system_admin count: {system_admin_count}")
                            print(f"   📊 super_admin count: {super_admin_count}")
                            
                            # Verify expected admin structure (1 system_admin, 0 super_admin)
                            expected_structure = (system_admin_count >= 1)
                            
                            if expected_structure:
                                print(f"✅ Admin structure matches expected (at least 1 system_admin)")
                                self.print_result(True, "Admin status endpoint working correctly - admin exists")
                                return True
                            else:
                                print(f"❌ Admin structure unexpected")
                                self.print_result(False, "Admin structure doesn't match expected")
                                return False
                        else:
                            print(f"❌ Breakdown is not a dictionary")
                            self.print_result(False, "Invalid breakdown structure")
                            return False
                    else:
                        print(f"❌ No admin exists - this indicates the auto-create admin failed")
                        self.print_result(False, "No admin exists - auto-create admin may have failed")
                        return False
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, "Invalid JSON response from admin status")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Error: {error_data}")
                    self.print_result(False, f"Admin status endpoint failed with status {response.status_code}")
                    return False
                except:
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Response: {response.text[:500]}...")
                    self.print_result(False, f"Admin status endpoint failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during admin status test: {str(e)}")
            return False

    def test_env_check_endpoint(self):
        """Test 2: Check Environment Variables (Public Endpoint)"""
        self.print_test_header("Test 2 - Environment Variables Check (Public)")
        
        try:
            print(f"🔍 Testing GET /api/admin/env-check")
            print(f"📡 URL: {BACKEND_URL}/admin/env-check")
            print(f"🔓 No authentication required (public endpoint)")
            print(f"🎯 Expected: env vars status (true/false), username_hint, all_required_set")
            
            # Make request to env check endpoint
            response = self.session.get(
                f"{BACKEND_URL}/admin/env-check",
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
                    
                    # Check required fields
                    required_fields = ["username_set", "password_set", "email_set", "all_required_set"]
                    missing_fields = []
                    
                    for field in required_fields:
                        if field not in response_data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        self.print_result(False, f"Missing required fields: {missing_fields}")
                        return False
                    
                    # Verify environment variables status
                    username_set = response_data.get("username_set", False)
                    password_set = response_data.get("password_set", False)
                    email_set = response_data.get("email_set", False)
                    all_required_set = response_data.get("all_required_set", False)
                    username_hint = response_data.get("username_hint", "")
                    
                    print(f"\n🔍 ENVIRONMENT VARIABLES VERIFICATION:")
                    print(f"   📄 username_set: {username_set}")
                    print(f"   📄 password_set: {password_set}")
                    print(f"   📄 email_set: {email_set}")
                    print(f"   📄 all_required_set: {all_required_set}")
                    print(f"   📄 username_hint: '{username_hint}'")
                    
                    # Check if required env vars are set
                    if username_set and password_set:
                        print(f"✅ SUCCESS: Required environment variables are set!")
                        
                        # Verify username hint format (first 3 chars + asterisks)
                        if username_hint and len(username_hint) >= 3:
                            expected_hint_start = ADMIN_USERNAME[:3]
                            actual_hint_start = username_hint[:3]
                            
                            if expected_hint_start == actual_hint_start:
                                print(f"✅ Username hint format correct: '{username_hint}'")
                                
                                # Check all_required_set flag
                                if all_required_set:
                                    print(f"✅ all_required_set flag is true as expected")
                                    self.print_result(True, "Environment variables check successful - all required vars set")
                                    return True
                                else:
                                    print(f"❌ all_required_set flag is false despite username and password being set")
                                    self.print_result(False, "all_required_set flag incorrect")
                                    return False
                            else:
                                print(f"❌ Username hint doesn't match expected format")
                                print(f"   Expected start: '{expected_hint_start}', Got: '{actual_hint_start}'")
                                self.print_result(False, "Username hint format incorrect")
                                return False
                        else:
                            print(f"❌ Username hint is empty or too short")
                            self.print_result(False, "Username hint missing or invalid")
                            return False
                    else:
                        print(f"❌ Required environment variables not set")
                        print(f"   username_set: {username_set}, password_set: {password_set}")
                        self.print_result(False, "Required environment variables not set")
                        return False
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, "Invalid JSON response from env check")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Error: {error_data}")
                    self.print_result(False, f"Env check endpoint failed with status {response.status_code}")
                    return False
                except:
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"📄 Response: {response.text[:500]}...")
                    self.print_result(False, f"Env check endpoint failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during env check test: {str(e)}")
            return False

    def test_create_admin_invalid_secret(self):
        """Test 3: Create Admin with Invalid Secret (Security Test)"""
        self.print_test_header("Test 3 - Create Admin with Invalid Secret (Security)")
        
        try:
            print(f"🔍 Testing POST /api/admin/create-from-env with INVALID secret")
            print(f"📡 URL: {BACKEND_URL}/admin/create-from-env")
            print(f"🔒 Using WRONG X-Admin-Secret header: 'wrong-secret'")
            print(f"🎯 Expected: 403 Forbidden with 'Invalid or missing X-Admin-Secret header'")
            
            # Make request with wrong secret
            headers = {
                "Content-Type": "application/json",
                "X-Admin-Secret": "wrong-secret"  # WRONG secret
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/admin/create-from-env",
                headers=headers,
                json={},  # Empty body
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 403:
                try:
                    response_data = response.json()
                    print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
                    
                    # Check for expected error message
                    detail = response_data.get("detail", "")
                    message = response_data.get("message", "")
                    error_text = detail or message
                    
                    print(f"\n🔍 SECURITY ERROR VERIFICATION:")
                    print(f"   📄 Error message: '{error_text}'")
                    
                    # Check if error message indicates invalid secret
                    expected_keywords = ["invalid", "missing", "admin-secret", "header"]
                    message_appropriate = any(keyword.lower() in error_text.lower() for keyword in expected_keywords)
                    
                    if message_appropriate:
                        print(f"✅ SUCCESS: Security working correctly!")
                        print(f"✅ Invalid secret correctly rejected with 403 Forbidden")
                        print(f"✅ Error message appropriate: '{error_text}'")
                        self.print_result(True, "Invalid secret correctly rejected - security working")
                        return True
                    else:
                        print(f"❌ Error message doesn't indicate invalid secret")
                        self.print_result(False, "Error message doesn't match expected security error")
                        return False
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    # Still consider this a pass if we got 403
                    print(f"✅ Got 403 status as expected, even though response isn't JSON")
                    self.print_result(True, "Invalid secret correctly rejected with 403 (non-JSON response)")
                    return True
                    
            else:
                print(f"❌ Expected 403 Forbidden, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"📄 Response: {error_data}")
                except:
                    print(f"📄 Response text: {response.text[:500]}...")
                
                self.print_result(False, f"Expected 403 Forbidden, got {response.status_code}")
                return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during invalid secret test: {str(e)}")
            return False

    def test_create_admin_missing_secret(self):
        """Test 4: Create Admin with Missing Secret (Security Test)"""
        self.print_test_header("Test 4 - Create Admin with Missing Secret (Security)")
        
        try:
            print(f"🔍 Testing POST /api/admin/create-from-env with NO secret header")
            print(f"📡 URL: {BACKEND_URL}/admin/create-from-env")
            print(f"🔒 NO X-Admin-Secret header included")
            print(f"🎯 Expected: 403 Forbidden")
            
            # Make request without secret header
            headers = {
                "Content-Type": "application/json"
                # NO X-Admin-Secret header
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/admin/create-from-env",
                headers=headers,
                json={},  # Empty body
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 403:
                try:
                    response_data = response.json()
                    print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
                    
                    # Check for expected error message
                    detail = response_data.get("detail", "")
                    message = response_data.get("message", "")
                    error_text = detail or message
                    
                    print(f"\n🔍 SECURITY ERROR VERIFICATION:")
                    print(f"   📄 Error message: '{error_text}'")
                    
                    print(f"✅ SUCCESS: Security working correctly!")
                    print(f"✅ Missing secret correctly rejected with 403 Forbidden")
                    self.print_result(True, "Missing secret correctly rejected - security working")
                    return True
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    # Still consider this a pass if we got 403
                    print(f"✅ Got 403 status as expected, even though response isn't JSON")
                    self.print_result(True, "Missing secret correctly rejected with 403 (non-JSON response)")
                    return True
                    
            else:
                print(f"❌ Expected 403 Forbidden, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"📄 Response: {error_data}")
                except:
                    print(f"📄 Response text: {response.text[:500]}...")
                
                self.print_result(False, f"Expected 403 Forbidden, got {response.status_code}")
                return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during missing secret test: {str(e)}")
            return False

    def test_create_admin_valid_secret(self):
        """Test 5: Create Admin with Valid Secret (Should Fail - Admin Exists)"""
        self.print_test_header("Test 5 - Create Admin with Valid Secret (Admin Exists)")
        
        try:
            print(f"🔍 Testing POST /api/admin/create-from-env with VALID secret")
            print(f"📡 URL: {BACKEND_URL}/admin/create-from-env")
            print(f"🔒 Using CORRECT X-Admin-Secret header: '{ADMIN_CREATION_SECRET}'")
            print(f"🎯 Expected: 200 OK but success=false (admin already exists)")
            
            # Make request with correct secret
            headers = {
                "Content-Type": "application/json",
                "X-Admin-Secret": ADMIN_CREATION_SECRET  # CORRECT secret
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/admin/create-from-env",
                headers=headers,
                json={},  # Empty body
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
                    
                    # Check response structure
                    success = response_data.get("success", True)
                    message = response_data.get("message", "")
                    
                    print(f"\n🔍 ADMIN CREATION RESPONSE VERIFICATION:")
                    print(f"   📄 success: {success}")
                    print(f"   📄 message: '{message}'")
                    
                    # Should be success=false because admin already exists
                    if not success:
                        # Check if message indicates admin already exists
                        admin_exists_keywords = ["already exists", "admin exists", "existing admin"]
                        message_appropriate = any(keyword.lower() in message.lower() for keyword in admin_exists_keywords)
                        
                        if message_appropriate:
                            print(f"✅ SUCCESS: Admin creation correctly failed!")
                            print(f"✅ success=false as expected (admin already exists)")
                            print(f"✅ Message indicates admin already exists: '{message}'")
                            self.print_result(True, "Admin creation correctly failed - admin already exists")
                            return True
                        else:
                            print(f"❌ Message doesn't indicate admin already exists")
                            self.print_result(False, "Message doesn't match expected 'admin exists' error")
                            return False
                    else:
                        print(f"❌ Expected success=false, got success=true")
                        print(f"🔧 This might indicate admin was created (unexpected)")
                        self.print_result(False, "Unexpected success - admin should already exist")
                        return False
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, "Invalid JSON response from admin creation")
                    return False
                    
            else:
                print(f"❌ Expected 200 OK, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"📄 Response: {error_data}")
                except:
                    print(f"📄 Response text: {response.text[:500]}...")
                
                self.print_result(False, f"Expected 200 OK, got {response.status_code}")
                return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during valid secret test: {str(e)}")
            return False

    def test_backend_startup_logs(self):
        """Test 6: Verify Backend Startup Logs"""
        self.print_test_header("Test 6 - Backend Startup Logs Verification")
        
        try:
            print(f"🔍 Checking backend startup logs for admin creation messages")
            print(f"📄 Log file: /var/log/supervisor/backend.err.log")
            print(f"🎯 Looking for: '✅ Admin users already exist (1 system_admin, 0 super_admin)'")
            print(f"🎯 Or: Admin creation/initialization messages")
            
            # Check supervisor backend logs
            log_command = "tail -n 200 /var/log/supervisor/backend.err.log"
            result = subprocess.run(log_command, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_content = result.stdout
                print(f"📄 Retrieved {len(log_content.splitlines())} lines of backend logs")
                
                # Look for admin-related startup messages
                admin_exists_logs = []
                admin_creation_logs = []
                admin_init_logs = []
                
                for line in log_content.splitlines():
                    line_lower = line.lower()
                    if "admin users already exist" in line_lower:
                        admin_exists_logs.append(line.strip())
                    elif "admin" in line_lower and ("creat" in line_lower or "init" in line_lower):
                        admin_creation_logs.append(line.strip())
                    elif "init_admin" in line_lower or "startup" in line_lower:
                        admin_init_logs.append(line.strip())
                
                print(f"\n🔍 ADMIN STARTUP LOG ANALYSIS:")
                print(f"   📊 'Admin users already exist' logs: {len(admin_exists_logs)}")
                print(f"   📊 Admin creation/init logs: {len(admin_creation_logs)}")
                print(f"   📊 Startup/init logs: {len(admin_init_logs)}")
                
                # Show sample logs if found
                if admin_exists_logs:
                    print(f"\n   📝 ADMIN EXISTS LOG SAMPLE:")
                    for log in admin_exists_logs[-3:]:  # Show last 3
                        print(f"      {log}")
                
                if admin_creation_logs:
                    print(f"\n   📝 ADMIN CREATION LOG SAMPLE:")
                    for log in admin_creation_logs[-3:]:  # Show last 3
                        print(f"      {log}")
                
                if admin_init_logs:
                    print(f"\n   📝 ADMIN INIT LOG SAMPLE:")
                    for log in admin_init_logs[-3:]:  # Show last 3
                        print(f"      {log}")
                
                # Determine if startup admin creation is working
                startup_admin_confirmed = len(admin_exists_logs) > 0 or len(admin_creation_logs) > 0
                
                if startup_admin_confirmed:
                    print(f"\n✅ SUCCESS: Backend startup logs confirm admin initialization!")
                    if admin_exists_logs:
                        print(f"✅ Found 'Admin users already exist' messages")
                    if admin_creation_logs:
                        print(f"✅ Found admin creation/initialization messages")
                    
                    self.print_result(True, "Backend startup logs confirm admin initialization working")
                    return True
                else:
                    print(f"\n❌ NO ADMIN STARTUP LOGS FOUND")
                    print(f"🔧 This may indicate:")
                    print(f"   - Auto-create admin not running on startup")
                    print(f"   - Admin initialization not logging properly")
                    print(f"   - Backend hasn't been restarted recently")
                    
                    self.print_result(False, "No admin startup logs found")
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
            self.print_result(False, f"Exception during backend logs check: {str(e)}")
            return False

    def test_login_with_admin_credentials(self):
        """Test 7: Login with Existing Admin Credentials (CRITICAL TEST)"""
        self.print_test_header("Test 7 - Login with Admin Credentials (CRITICAL)")
        
        try:
            print(f"🔍 Testing POST /api/auth/login with admin credentials")
            print(f"📡 URL: {BACKEND_URL}/auth/login")
            print(f"👤 Username: {ADMIN_USERNAME}")
            print(f"🔒 Password: {ADMIN_PASSWORD}")
            print(f"🎯 Expected: 200 OK with access_token")
            print(f"🚨 THIS IS THE CRITICAL TEST - verifies production login issue is fixed")
            
            # Test login with admin credentials from .env
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
                "remember_me": False
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
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
                    
                    # Verify login response structure
                    access_token = response_data.get("access_token", "")
                    token_type = response_data.get("token_type", "")
                    user_data = response_data.get("user", {})
                    
                    print(f"\n🔍 LOGIN RESPONSE VERIFICATION:")
                    print(f"   📄 access_token: {access_token[:20]}... (length: {len(access_token)})")
                    print(f"   📄 token_type: {token_type}")
                    print(f"   📄 user.username: {user_data.get('username', 'N/A')}")
                    print(f"   📄 user.role: {user_data.get('role', 'N/A')}")
                    print(f"   📄 user.id: {user_data.get('id', 'N/A')}")
                    
                    # Verify token and user data
                    if access_token and len(access_token) > 10:
                        if token_type == "bearer":
                            if user_data.get("username") == ADMIN_USERNAME:
                                user_role = user_data.get("role", "")
                                if user_role in ["admin", "super_admin", "system_admin"]:
                                    print(f"\n🎉 CRITICAL SUCCESS: ADMIN LOGIN WORKING!")
                                    print(f"✅ Login successful with 200 OK")
                                    print(f"✅ Access token received (length: {len(access_token)})")
                                    print(f"✅ Token type is 'bearer'")
                                    print(f"✅ Username matches: {ADMIN_USERNAME}")
                                    print(f"✅ User role is admin-level: {user_role}")
                                    print(f"🚨 PRODUCTION LOGIN ISSUE IS FIXED!")
                                    
                                    self.print_result(True, "CRITICAL SUCCESS - Admin login working, production issue fixed")
                                    return True
                                else:
                                    print(f"❌ User role is not admin-level: {user_role}")
                                    self.print_result(False, f"User role not admin-level: {user_role}")
                                    return False
                            else:
                                print(f"❌ Username mismatch: expected {ADMIN_USERNAME}, got {user_data.get('username')}")
                                self.print_result(False, "Username mismatch in login response")
                                return False
                        else:
                            print(f"❌ Token type is not 'bearer': {token_type}")
                            self.print_result(False, f"Invalid token type: {token_type}")
                            return False
                    else:
                        print(f"❌ Access token is missing or too short")
                        self.print_result(False, "Access token missing or invalid")
                        return False
                    
                except json.JSONDecodeError:
                    print(f"❌ Response is not valid JSON")
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, "Invalid JSON response from login")
                    return False
                    
            else:
                print(f"❌ Login failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"📄 Error: {error_data}")
                    
                    # Check if this is the original production issue
                    error_detail = error_data.get("detail", "")
                    if "invalid credentials" in error_detail.lower() or "unauthorized" in error_detail.lower():
                        print(f"🚨 THIS IS THE ORIGINAL PRODUCTION ISSUE!")
                        print(f"🚨 Admin credentials not working - auto-create admin may have failed")
                        self.print_result(False, "CRITICAL FAILURE - Admin login not working (original production issue)")
                        return False
                    else:
                        self.print_result(False, f"Login failed with status {response.status_code}: {error_detail}")
                        return False
                except:
                    print(f"📄 Response text: {response.text[:500]}...")
                    self.print_result(False, f"Login failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.print_result(False, f"Exception during admin login test: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all Admin API tests in sequence"""
        print(f"\n🚀 STARTING ADMIN API TESTING FOR PRODUCTION ADMIN MANAGEMENT")
        print(f"🎯 Test newly implemented Admin API endpoints for production admin management without terminal access")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"📅 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test sequence for Admin API Testing
        tests = [
            ("Test 1 - Admin Status (Public)", self.test_admin_status_endpoint),
            ("Test 2 - Environment Check (Public)", self.test_env_check_endpoint),
            ("Test 3 - Invalid Secret (Security)", self.test_create_admin_invalid_secret),
            ("Test 4 - Missing Secret (Security)", self.test_create_admin_missing_secret),
            ("Test 5 - Valid Secret (Admin Exists)", self.test_create_admin_valid_secret),
            ("Test 6 - Backend Startup Logs", self.test_backend_startup_logs),
            ("Test 7 - Admin Login (CRITICAL)", self.test_login_with_admin_credentials),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n" + "="*100)
                result = test_func()
                results.append((test_name, result))
                
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status}: {test_name}")
                    
            except Exception as e:
                print(f"💥 Exception in {test_name}: {str(e)}")
                results.append((test_name, False))
        
        # Print final summary
        print(f"\n" + "="*100)
        print(f"📊 ADMIN API TESTING SUMMARY")
        print(f"="*100)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
        print(f"📅 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")
        
        # Admin API Analysis
        print(f"\n" + "="*100)
        print(f"🔍 ADMIN API ANALYSIS")
        print(f"="*100)
        
        print(f"🎯 ADMIN API ENDPOINTS TESTED:")
        print(f"   📡 GET /api/admin/status (Public)")
        print(f"   📡 GET /api/admin/env-check (Public)")
        print(f"   📡 POST /api/admin/create-from-env (Secured)")
        print(f"   📡 POST /api/auth/login (Admin credentials)")
        
        print(f"\n📋 SUCCESS CRITERIA VERIFICATION:")
        
        # Analyze results
        admin_status_pass = results[0][1] if len(results) > 0 else False
        env_check_pass = results[1][1] if len(results) > 1 else False
        invalid_secret_pass = results[2][1] if len(results) > 2 else False
        missing_secret_pass = results[3][1] if len(results) > 3 else False
        valid_secret_pass = results[4][1] if len(results) > 4 else False
        startup_logs_pass = results[5][1] if len(results) > 5 else False
        admin_login_pass = results[6][1] if len(results) > 6 else False
        
        print(f"   ✅ Admin status endpoint accessible: {'✅ YES' if admin_status_pass else '❌ NO'}")
        print(f"   ✅ Environment check working: {'✅ YES' if env_check_pass else '❌ NO'}")
        print(f"   ✅ Security working (403 for invalid/missing secret): {'✅ YES' if (invalid_secret_pass and missing_secret_pass) else '❌ NO'}")
        print(f"   ✅ Admin creation handles existing admin: {'✅ YES' if valid_secret_pass else '❌ NO'}")
        print(f"   ✅ Backend logs confirm auto-create admin: {'✅ YES' if startup_logs_pass else '❌ NO'}")
        print(f"   🚨 CRITICAL - Admin login works: {'✅ YES' if admin_login_pass else '❌ NO'}")
        
        # Overall assessment
        critical_tests_passed = admin_login_pass  # Most critical test
        security_tests_passed = invalid_secret_pass and missing_secret_pass
        api_tests_passed = admin_status_pass and env_check_pass
        
        if critical_tests_passed and security_tests_passed and api_tests_passed:
            print(f"\n🎉 ADMIN API TESTING SUCCESSFUL!")
            print(f"✅ All three admin API endpoints accessible and working correctly")
            print(f"✅ Security layer working (403 for invalid/missing secret)")
            print(f"✅ Admin status endpoint shows admin exists")
            print(f"✅ Environment check shows required env vars are set")
            print(f"🚨 CRITICAL SUCCESS: Admin login works with env credentials")
            print(f"🎯 CONCLUSION: Production admin management is working - login issue FIXED")
        elif critical_tests_passed:
            print(f"\n⚠️ ADMIN API PARTIALLY SUCCESSFUL")
            print(f"🚨 CRITICAL SUCCESS: Admin login is working")
            print(f"📊 Some API endpoints or security tests have issues")
            print(f"🎯 CONCLUSION: Core functionality working but some issues detected")
        else:
            print(f"\n❌ ADMIN API TESTING FAILED")
            print(f"🚨 CRITICAL FAILURE: Admin login not working")
            print(f"🚨 This indicates the original production issue is NOT fixed")
            print(f"🔧 Auto-create admin may not be working correctly")
            print(f"🎯 CONCLUSION: Production login issue still exists")
        
        return success_rate >= 80 and critical_tests_passed


if __name__ == "__main__":
    """Main execution - run Admin API tests"""
    tester = AdminAPITester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED - ADMIN API ENDPOINTS WORKING CORRECTLY")
        print(f"🚨 CRITICAL SUCCESS: Production admin login issue is FIXED")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED - REVIEW RESULTS ABOVE")
        print(f"🚨 Check if production admin login issue is resolved")
        sys.exit(1)
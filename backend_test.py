#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
Focus: Login Functionality Debugging - Authentication System Testing
"""

import requests
import json
import os
import sys
from datetime import datetime
import tempfile
import subprocess
import time
import base64

# Configuration - Use production URL from frontend .env
BACKEND_URL = "https://shipment-ai-1.preview.emergentagent.com/api"

class LoginFunctionalityTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_credentials = [
            {"username": "admin1", "password": "123456", "description": "Primary admin account"},
            {"username": "admin", "password": "admin123", "description": "Demo admin account"}
        ]
        self.test_results = {}
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_login_functionality(self):
        """Main test function for login functionality debugging"""
        self.log("🔐 Starting Login Functionality Testing - Debug User Authentication Issues")
        self.log("=" * 80)
        
        # Step 1: Test Login API Directly
        login_api_result = self.test_login_api_directly()
        
        # Step 2: Check User Database
        user_db_result = self.check_user_database()
        
        # Step 3: Test Token Generation
        token_result = self.test_token_generation()
        
        # Step 4: Authentication System Health
        auth_health_result = self.test_authentication_system_health()
        
        # Step 5: Detailed Response Analysis
        response_analysis_result = self.analyze_response_details()
        
        # Step 6: Summary
        self.log("=" * 80)
        self.log("📋 LOGIN FUNCTIONALITY TEST SUMMARY")
        self.log("=" * 80)
        
        self.log(f"{'✅' if login_api_result else '❌'} Login API Direct Testing: {'SUCCESS' if login_api_result else 'FAILED'}")
        self.log(f"{'✅' if user_db_result else '❌'} User Database Check: {'SUCCESS' if user_db_result else 'FAILED'}")
        self.log(f"{'✅' if token_result else '❌'} Token Generation Testing: {'SUCCESS' if token_result else 'FAILED'}")
        self.log(f"{'✅' if auth_health_result else '❌'} Authentication System Health: {'SUCCESS' if auth_health_result else 'FAILED'}")
        self.log(f"{'✅' if response_analysis_result else '❌'} Response Analysis: {'SUCCESS' if response_analysis_result else 'FAILED'}")
        
        overall_success = all([login_api_result, user_db_result, token_result, auth_health_result, response_analysis_result])
        
        if overall_success:
            self.log("🎉 LOGIN FUNCTIONALITY: FULLY TESTED AND WORKING")
        else:
            self.log("❌ LOGIN FUNCTIONALITY: ISSUES DETECTED")
            self.log("🔍 Check detailed logs above for specific issues")
        
        return overall_success
    
    def test_login_api_directly(self):
        """Test POST /api/auth/login with both credential sets"""
        try:
            self.log("🔐 Step 1: Testing Login API Directly...")
            
            all_login_tests_passed = True
            
            for cred in self.test_credentials:
                username = cred["username"]
                password = cred["password"]
                description = cred["description"]
                
                self.log(f"   🧪 Testing {description} ({username}/{password})...")
                
                login_data = {
                    "username": username,
                    "password": password,
                    "remember_me": False
                }
                
                endpoint = f"{BACKEND_URL}/auth/login"
                
                try:
                    response = requests.post(endpoint, json=login_data, timeout=30)
                    
                    self.log(f"      Response Status: {response.status_code}")
                    self.log(f"      Response Headers: {dict(response.headers)}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Check response structure
                        access_token = data.get("access_token")
                        token_type = data.get("token_type")
                        user_data = data.get("user")
                        remember_me = data.get("remember_me")
                        
                        self.log(f"      ✅ Login successful for {username}")
                        self.log(f"         Access Token: {'Present' if access_token else 'Missing'} ({len(access_token) if access_token else 0} chars)")
                        self.log(f"         Token Type: {token_type}")
                        self.log(f"         Remember Me: {remember_me}")
                        
                        if user_data:
                            self.log(f"         User Data:")
                            self.log(f"            ID: {user_data.get('id')}")
                            self.log(f"            Username: {user_data.get('username')}")
                            self.log(f"            Full Name: {user_data.get('full_name')}")
                            self.log(f"            Role: {user_data.get('role')}")
                            self.log(f"            Company: {user_data.get('company')}")
                            self.log(f"            Department: {user_data.get('department')}")
                            self.log(f"            Email: {user_data.get('email')}")
                            self.log(f"            Active: {user_data.get('is_active')}")
                        
                        # Store successful login data for token testing
                        self.test_results[username] = {
                            "success": True,
                            "token": access_token,
                            "user": user_data,
                            "response": data
                        }
                        
                    else:
                        try:
                            error_data = response.json()
                            error_detail = error_data.get('detail', 'Unknown error')
                        except:
                            error_detail = response.text
                        
                        self.log(f"      ❌ Login failed for {username}")
                        self.log(f"         HTTP Status: {response.status_code}")
                        self.log(f"         Error: {error_detail}")
                        
                        self.test_results[username] = {
                            "success": False,
                            "error": error_detail,
                            "status_code": response.status_code
                        }
                        
                        all_login_tests_passed = False
                        
                except requests.exceptions.RequestException as req_error:
                    self.log(f"      ❌ Network error for {username}: {str(req_error)}")
                    self.test_results[username] = {
                        "success": False,
                        "error": f"Network error: {str(req_error)}"
                    }
                    all_login_tests_passed = False
                
                self.log("")  # Add spacing between tests
            
            return all_login_tests_passed
                
        except Exception as e:
            self.log(f"❌ Login API testing error: {str(e)}", "ERROR")
            return False
    
    def check_user_database(self):
        """Check user database to confirm users exist and verify passwords"""
        try:
            self.log("👥 Step 2: Checking User Database...")
            
            # We need to authenticate first to access user endpoints
            successful_login = None
            for username, result in self.test_results.items():
                if result.get("success"):
                    successful_login = result
                    break
            
            if not successful_login:
                self.log("   ⚠️ No successful login available - cannot check user database")
                return True  # Don't fail the test if we can't authenticate
            
            # Set up authenticated session
            auth_token = successful_login.get("token")
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            self.log("   🔍 Fetching all users from database...")
            
            endpoint = f"{BACKEND_URL}/users"
            response = requests.get(endpoint, headers=headers, timeout=30)
            
            self.log(f"   Users API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                users = response.json()
                self.log(f"   ✅ Retrieved {len(users)} users from database")
                
                # Check for our test users
                test_usernames = [cred["username"] for cred in self.test_credentials]
                
                for username in test_usernames:
                    user_found = None
                    for user in users:
                        if user.get("username") == username:
                            user_found = user
                            break
                    
                    if user_found:
                        self.log(f"   ✅ User '{username}' found in database:")
                        self.log(f"      ID: {user_found.get('id')}")
                        self.log(f"      Full Name: {user_found.get('full_name')}")
                        self.log(f"      Role: {user_found.get('role')}")
                        self.log(f"      Company: {user_found.get('company')}")
                        self.log(f"      Active: {user_found.get('is_active')}")
                        self.log(f"      Created: {user_found.get('created_at')}")
                    else:
                        self.log(f"   ❌ User '{username}' NOT found in database")
                        return False
                
                return True
                
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                
                self.log(f"   ❌ Users API failed - HTTP {response.status_code}")
                self.log(f"      Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log(f"❌ User database check error: {str(e)}", "ERROR")
            return False
    
    def test_token_generation(self):
        """Test JWT token generation and validation"""
        try:
            self.log("🎫 Step 3: Testing Token Generation...")
            
            all_tokens_valid = True
            
            for username, result in self.test_results.items():
                if not result.get("success"):
                    continue
                
                token = result.get("token")
                if not token:
                    self.log(f"   ❌ No token found for {username}")
                    all_tokens_valid = False
                    continue
                
                self.log(f"   🔍 Analyzing token for {username}...")
                
                # Basic token structure check
                token_parts = token.split('.')
                self.log(f"      Token parts: {len(token_parts)} (should be 3 for JWT)")
                
                if len(token_parts) != 3:
                    self.log(f"      ❌ Invalid JWT structure for {username}")
                    all_tokens_valid = False
                    continue
                
                try:
                    # Decode header (without verification for inspection)
                    header_data = token_parts[0]
                    # Add padding if needed
                    header_data += '=' * (4 - len(header_data) % 4)
                    header = json.loads(base64.urlsafe_b64decode(header_data))
                    
                    self.log(f"      Token Header: {header}")
                    
                    # Decode payload (without verification for inspection)
                    payload_data = token_parts[1]
                    # Add padding if needed
                    payload_data += '=' * (4 - len(payload_data) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(payload_data))
                    
                    self.log(f"      Token Payload:")
                    self.log(f"         Subject (sub): {payload.get('sub')}")
                    self.log(f"         Username: {payload.get('username')}")
                    self.log(f"         Role: {payload.get('role')}")
                    self.log(f"         Company: {payload.get('company')}")
                    self.log(f"         Full Name: {payload.get('full_name')}")
                    
                    # Check expiration
                    exp = payload.get('exp')
                    if exp:
                        exp_datetime = datetime.fromtimestamp(exp)
                        current_datetime = datetime.now()
                        time_until_exp = exp_datetime - current_datetime
                        
                        self.log(f"         Expires: {exp_datetime}")
                        self.log(f"         Time until expiry: {time_until_exp}")
                        
                        if time_until_exp.total_seconds() > 0:
                            self.log(f"         ✅ Token is valid (not expired)")
                        else:
                            self.log(f"         ❌ Token is expired")
                            all_tokens_valid = False
                    
                    # Test token by making an authenticated request
                    self.log(f"      🧪 Testing token validity with authenticated request...")
                    
                    headers = {"Authorization": f"Bearer {token}"}
                    test_endpoint = f"{BACKEND_URL}/ships"  # Simple endpoint that requires auth
                    
                    test_response = requests.get(test_endpoint, headers=headers, timeout=30)
                    
                    if test_response.status_code == 200:
                        self.log(f"         ✅ Token authentication successful")
                    elif test_response.status_code == 401:
                        self.log(f"         ❌ Token authentication failed - 401 Unauthorized")
                        all_tokens_valid = False
                    else:
                        self.log(f"         ⚠️ Unexpected response: {test_response.status_code}")
                    
                except Exception as token_error:
                    self.log(f"      ❌ Token analysis error for {username}: {str(token_error)}")
                    all_tokens_valid = False
                
                self.log("")  # Add spacing
            
            return all_tokens_valid
                
        except Exception as e:
            self.log(f"❌ Token generation testing error: {str(e)}", "ERROR")
            return False
    
    def test_authentication_system_health(self):
        """Test authentication system health and error handling"""
        try:
            self.log("🏥 Step 4: Testing Authentication System Health...")
            
            # Test 1: Invalid credentials
            self.log("   🧪 Test 1: Invalid credentials...")
            invalid_login = {
                "username": "nonexistent_user",
                "password": "wrong_password",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            response = requests.post(endpoint, json=invalid_login, timeout=30)
            
            if response.status_code == 401:
                self.log("      ✅ Invalid credentials properly rejected (401)")
            else:
                self.log(f"      ❌ Unexpected response for invalid credentials: {response.status_code}")
                return False
            
            # Test 2: Malformed request
            self.log("   🧪 Test 2: Malformed request...")
            malformed_login = {
                "username": "admin1"
                # Missing password field
            }
            
            response = requests.post(endpoint, json=malformed_login, timeout=30)
            
            if response.status_code in [400, 422]:  # Bad request or validation error
                self.log("      ✅ Malformed request properly rejected")
            else:
                self.log(f"      ❌ Unexpected response for malformed request: {response.status_code}")
                return False
            
            # Test 3: Empty credentials
            self.log("   🧪 Test 3: Empty credentials...")
            empty_login = {
                "username": "",
                "password": "",
                "remember_me": False
            }
            
            response = requests.post(endpoint, json=empty_login, timeout=30)
            
            if response.status_code in [400, 401, 422]:
                self.log("      ✅ Empty credentials properly rejected")
            else:
                self.log(f"      ❌ Unexpected response for empty credentials: {response.status_code}")
                return False
            
            # Test 4: Check for any authentication errors in logs (if accessible)
            self.log("   🧪 Test 4: Authentication error handling...")
            
            # Test with correct username but wrong password
            wrong_password_login = {
                "username": "admin1",
                "password": "wrongpassword",
                "remember_me": False
            }
            
            response = requests.post(endpoint, json=wrong_password_login, timeout=30)
            
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    
                    if 'invalid' in error_detail.lower() or 'credentials' in error_detail.lower():
                        self.log("      ✅ Proper error message for wrong password")
                    else:
                        self.log(f"      ⚠️ Generic error message: {error_detail}")
                except:
                    self.log("      ⚠️ No JSON error response")
            else:
                self.log(f"      ❌ Unexpected response for wrong password: {response.status_code}")
                return False
            
            return True
                
        except Exception as e:
            self.log(f"❌ Authentication system health testing error: {str(e)}", "ERROR")
            return False
    
    def analyze_response_details(self):
        """Analyze detailed response format and required fields"""
        try:
            self.log("🔍 Step 5: Analyzing Response Details...")
            
            # Find a successful login to analyze
            successful_result = None
            successful_username = None
            
            for username, result in self.test_results.items():
                if result.get("success"):
                    successful_result = result
                    successful_username = username
                    break
            
            if not successful_result:
                self.log("   ⚠️ No successful login available for response analysis")
                return True
            
            self.log(f"   🔍 Analyzing successful login response for {successful_username}...")
            
            response_data = successful_result.get("response", {})
            
            # Check required fields
            required_fields = ["access_token", "token_type", "user", "remember_me"]
            missing_fields = []
            
            for field in required_fields:
                if field not in response_data:
                    missing_fields.append(field)
                else:
                    value = response_data[field]
                    self.log(f"      ✅ {field}: {type(value).__name__} - {'Present' if value else 'Empty'}")
            
            if missing_fields:
                self.log(f"      ❌ Missing required fields: {missing_fields}")
                return False
            
            # Analyze user object
            user_data = response_data.get("user", {})
            if user_data:
                self.log("      📊 User object analysis:")
                
                user_required_fields = ["id", "username", "role", "full_name", "is_active"]
                user_missing_fields = []
                
                for field in user_required_fields:
                    if field not in user_data:
                        user_missing_fields.append(field)
                    else:
                        value = user_data[field]
                        self.log(f"         ✅ {field}: {repr(value)}")
                
                if user_missing_fields:
                    self.log(f"         ❌ Missing user fields: {user_missing_fields}")
                    return False
                
                # Check optional fields
                optional_fields = ["company", "department", "email", "ship"]
                for field in optional_fields:
                    if field in user_data:
                        value = user_data[field]
                        self.log(f"         📋 {field}: {repr(value)} (optional)")
            
            # Verify token format
            token = response_data.get("access_token")
            if token:
                self.log("      🎫 Token format analysis:")
                self.log(f"         Length: {len(token)} characters")
                self.log(f"         Format: {'JWT' if token.count('.') == 2 else 'Unknown'}")
                self.log(f"         Starts with: {token[:20]}...")
            
            # Check token_type
            token_type = response_data.get("token_type")
            if token_type:
                if token_type.lower() == "bearer":
                    self.log(f"      ✅ Token type: {token_type} (correct)")
                else:
                    self.log(f"      ⚠️ Token type: {token_type} (expected 'bearer')")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Response analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main test execution"""
    print("🔐 Ship Management System - Login Functionality Testing")
    print("🔍 Debug: User authentication and login issues")
    print("=" * 80)
    
    tester = LoginFunctionalityTester()
    success = tester.test_login_functionality()
    
    print("=" * 80)
    if success:
        print("🎉 Login functionality testing completed successfully!")
        print("✅ All authentication tests passed - login system is working correctly")
        sys.exit(0)
    else:
        print("❌ Login functionality testing completed with issues!")
        print("🔍 Some authentication tests failed - check detailed logs above")
        print("💡 Focus on the failed steps to identify the exact login issue")
        sys.exit(1)

if __name__ == "__main__":
    main()
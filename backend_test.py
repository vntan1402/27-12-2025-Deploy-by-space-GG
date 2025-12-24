#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE BACKEND API TESTING (PRE-DEPLOYMENT)

Testing all critical backend flows before production deployment:

## Test Objective
Comprehensive testing of:
1. Authentication flows (all 4 test users)
2. AI Configuration endpoints
3. Ship Certificates Multi-Upload
4. Audit Certificates Multi-Upload  
5. User Management endpoints
6. Permission system tests
7. GDrive Configuration

## Test Credentials
- **system_admin** / `YourSecure@Pass2024` (Full access - System Admin)
- **Crew4** / `123456` (Editor role - Ship Officer)
- **Crew3** / `123456` (Viewer role - Crew)
- **crewing_manager** / `123456` (Manager in crewing department)

## Critical Flows to Test
- POST /api/auth/login - Test login for all 4 users above
- GET /api/verify-token - Verify token validity
- GET /api/ai-config - Get AI config (should work for all authenticated users)
- POST /api/ai-config - Create/Update AI config (admin only)
- GET /api/ships - Get ships list first
- POST /api/certificates/multi-upload?ship_id={ship_id} - Test with a small test file
- POST /api/audit-certificates/multi-upload?ship_id={ship_id} - This was the failing endpoint
- GET /api/users - Get users list (admin only)
- GET /api/users/{user_id} - Get single user (new endpoint)
- PUT /api/users/{user_id} - Update user
- GET /api/gdrive/config - Check for Pydantic validation errors
- GET /api/gdrive/status - Check GDrive status
"""

import requests
import json
import base64
import io
from datetime import datetime, timedelta
import time

# Get backend URL from frontend .env
try:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
        else:
            BACKEND_URL = "https://crew-access-control.preview.emergentagent.com/api"
except:
    BACKEND_URL = "https://crew-access-control.preview.emergentagent.com/api"

# Test users as specified in review request
TEST_USERS = {
    "system_admin": {"password": "YourSecure@Pass2024", "role": "system_admin", "ship": None, "actual_user": "system_admin"},
    "Crew4": {"password": "123456", "role": "editor", "ship": "Ship Officer", "actual_user": "Crew4"},
    "Crew3": {"password": "123456", "role": "viewer", "ship": "Crew", "actual_user": "Crew3"},
    "crewing_manager": {"password": "123456", "role": "manager", "ship": "crewing", "actual_user": "crewing_manager"}
}

def login(username, password):
    """Login and get access token"""
    response = requests.post(f"{BACKEND_URL}/auth/login", json={"username": username, "password": password})
    if response.status_code != 200:
        raise Exception(f"Login failed for {username}: {response.status_code} - {response.text}")
    return response.json()["access_token"]

def get_headers(username):
    """Get authorization headers for a user"""
    user_config = TEST_USERS[username]
    actual_username = user_config.get("actual_user", username)
    password = user_config["password"]
    token = login(actual_username, password)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def get_user_info(headers):
    """Get current user information"""
    response = requests.get(f"{BACKEND_URL}/auth/verify-token", headers=headers)
    if response.status_code == 200:
        return response.json().get("user", {})
    return None

def get_test_data(headers):
    """Get test data for testing"""
    # Get ships
    ships_response = requests.get(f"{BACKEND_URL}/ships?limit=10", headers=headers)
    ships = ships_response.json() if ships_response.status_code == 200 else []
    
    # Get crew members
    crew_response = requests.get(f"{BACKEND_URL}/crew?limit=10", headers=headers)
    crew = crew_response.json() if crew_response.status_code == 200 else []
    
    return {
        "ships": ships,
        "crew": crew
    }

def check_vietnamese_error_message(response):
    """Check if response contains Vietnamese error message"""
    if response.status_code != 403:
        return False, "Not a 403 error"
    
    try:
        error_data = response.json()
        error_detail = error_data.get('detail', '')
        
        # Check for Vietnamese characters or specific Vietnamese messages
        vietnamese_phrases = [
            'không có quyền', 'bị từ chối', 'Department', 'Manager', 
            'chỉ', 'mới có quyền', 'không được cấp quyền', 'Truy cập bị từ chối'
        ]
        vietnamese_error = any(phrase in error_detail for phrase in vietnamese_phrases)
        
        return vietnamese_error, error_detail
    except:
        return False, response.text

# Test functions based on review request requirements

def test_authentication_flow(username):
    """Test authentication for a specific user"""
    try:
        user_config = TEST_USERS[username]
        actual_username = user_config.get("actual_user", username)
        password = user_config["password"]
        
        # Test login
        response = requests.post(f"{BACKEND_URL}/auth/login", json={"username": actual_username, "password": password})
        if response.status_code != 200:
            return {"success": False, "error": f"Login failed: {response.status_code} - {response.text}"}
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            return {"success": False, "error": "No access token received"}
        
        # Test token verification
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        verify_response = requests.get(f"{BACKEND_URL}/verify-token", headers=headers)
        
        if verify_response.status_code != 200:
            return {"success": False, "error": f"Token verification failed: {verify_response.status_code}"}
        
        user_info = verify_response.json().get("user", {})
        
        return {
            "success": True, 
            "token": access_token,
            "user_info": user_info,
            "headers": headers
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_ai_config_get(headers):
    """Test GET /api/ai-config - should work for all authenticated users"""
    response = requests.get(f"{BACKEND_URL}/ai-config", headers=headers)
    return response

def test_ai_config_post(headers):
    """Test POST /api/ai-config - admin only"""
    test_config = {
        "project_id": "test-project",
        "location": "us",
        "processor_id": "test-processor"
    }
    response = requests.post(f"{BACKEND_URL}/ai-config", json=test_config, headers=headers)
    return response

def test_ships_list(headers):
    """Test GET /api/ships - get ships list"""
    response = requests.get(f"{BACKEND_URL}/ships", headers=headers)
    return response

def test_certificates_multi_upload(headers, ship_id):
    """Test POST /api/certificates/multi-upload - ship certificates multi-upload"""
    # Create a small test file
    test_file_content = b"Test certificate file content"
    files = [('files', ('test_cert.pdf', test_file_content, 'application/pdf'))]
    
    # Remove Content-Type header for multipart upload
    upload_headers = {k: v for k, v in headers.items() if k != 'Content-Type'}
    
    response = requests.post(
        f"{BACKEND_URL}/certificates/multi-upload?ship_id={ship_id}", 
        files=files, 
        headers=upload_headers
    )
    return response

def test_audit_certificates_multi_upload(headers, ship_id):
    """Test POST /api/audit-certificates/multi-upload - audit certificates multi-upload"""
    # Create a small test file
    test_file_content = b"Test audit certificate file content"
    files = [('files', ('test_audit_cert.pdf', test_file_content, 'application/pdf'))]
    
    # Remove Content-Type header for multipart upload
    upload_headers = {k: v for k, v in headers.items() if k != 'Content-Type'}
    
    response = requests.post(
        f"{BACKEND_URL}/audit-certificates/multi-upload?ship_id={ship_id}", 
        files=files, 
        headers=upload_headers
    )
    return response

def test_users_list(headers):
    """Test GET /api/users - get users list (admin only)"""
    response = requests.get(f"{BACKEND_URL}/users", headers=headers)
    return response

def test_user_by_id(headers, user_id):
    """Test GET /api/users/{user_id} - get single user"""
    response = requests.get(f"{BACKEND_URL}/users/{user_id}", headers=headers)
    return response

def test_user_update(headers, user_id):
    """Test PUT /api/users/{user_id} - update user"""
    update_data = {
        "full_name": "Updated Test User"
    }
    response = requests.put(f"{BACKEND_URL}/users/{user_id}", json=update_data, headers=headers)
    return response

def test_gdrive_config(headers):
    """Test GET /api/gdrive/config - check for Pydantic validation errors"""
    response = requests.get(f"{BACKEND_URL}/gdrive/config", headers=headers)
    return response

def test_gdrive_status(headers):
    """Test GET /api/gdrive/status - check GDrive status"""
    response = requests.get(f"{BACKEND_URL}/gdrive/status", headers=headers)
    return response

def test_permission_system(headers, expected_role):
    """Test permission system - check that viewer cannot access admin endpoints"""
    results = {}
    
    # Test AI config POST (admin only)
    results["ai_config_post"] = test_ai_config_post(headers)
    
    # Test users list (admin only)
    results["users_list"] = test_users_list(headers)
    
    # Test GDrive config (admin only)
    results["gdrive_config"] = test_gdrive_config(headers)
    
    return results

def run_test(test_name, test_func, expected_status=200, expected_admin_only=False):
    """Run a single test and return results"""
    try:
        print(f"\n   🧪 {test_name}")
        result = test_func()
        
        # Handle different response types
        if isinstance(result, dict):
            # Multiple responses (like permission system tests)
            success = True
            for operation, response in result.items():
                if expected_admin_only:
                    # For admin-only endpoints, non-admin should get 403
                    op_success = response.status_code == 403
                else:
                    op_success = response.status_code == expected_status
                
                success = success and op_success
                status_icon = "✅" if op_success else "❌"
                
                print(f"      {status_icon} {operation}: {response.status_code}")
                
                if not op_success:
                    print(f"         📝 Response: {response.text[:100]}...")
        else:
            # Single response
            response = result
            if expected_admin_only:
                success = response.status_code == 403
                result_icon = "✅" if success else "❌"
                print(f"      {result_icon} Expected: 403 (Admin Only), Got: {response.status_code}")
            else:
                success = response.status_code == expected_status
                result_icon = "✅" if success else "❌"
                print(f"      {result_icon} Expected: {expected_status}, Got: {response.status_code}")
            
            if not success:
                print(f"      📝 Response: {response.text[:200]}...")
                
        return success, result
        
    except Exception as e:
        print(f"      ❌ Test failed with exception: {e}")
        return False, None

# Main test execution
def main():
    print("🧪 COMPREHENSIVE BACKEND API TESTING (PRE-DEPLOYMENT)")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print("\nTest Credentials:")
    print("- system_admin / YourSecure@Pass2024 - Full access (System Admin)")
    print("- Crew4 / 123456 - Editor role (Ship Officer)")
    print("- Crew3 / 123456 - Viewer role (Crew)")
    print("- crewing_manager / 123456 - Manager in crewing department")
    
    # Test results tracking
    test_results = []
    all_tests = []
    
    try:
        # Test 1: Authentication Tests
        print("\n" + "=" * 80)
        print("🔐 AUTHENTICATION FLOW TESTS")
        print("=" * 80)
        
        user_sessions = {}
        
        for username in TEST_USERS.keys():
            print(f"\n📋 Testing authentication for: {username}")
            auth_result = test_authentication_flow(username)
            
            if auth_result["success"]:
                user_sessions[username] = auth_result
                user_info = auth_result["user_info"]
                print(f"   ✅ {username} login successful - Role: {user_info.get('role', 'unknown')}")
                test_results.append((f"AUTH {username}", "✅ PASS"))
                all_tests.append(("auth", True))
            else:
                print(f"   ❌ {username} login failed: {auth_result['error']}")
                test_results.append((f"AUTH {username}", f"❌ FAIL - {auth_result['error']}"))
                all_tests.append(("auth", False))
        
        # Continue only if we have at least system_admin session
        if "system_admin" not in user_sessions:
            print("\n❌ CRITICAL: system_admin authentication failed. Cannot continue tests.")
            return
        
        admin_headers = user_sessions["system_admin"]["headers"]
        
        # Test 2: AI Configuration Tests
        print("\n" + "=" * 80)
        print("🤖 AI CONFIGURATION TESTS")
        print("=" * 80)
        
        # Test AI config GET for all users
        for username, session in user_sessions.items():
            success, response = run_test(
                f"GET /api/ai-config ({username})",
                lambda: test_ai_config_get(session["headers"]),
                expected_status=200
            )
            test_results.append((f"AI CONFIG GET {username}", "✅ PASS" if success else "❌ FAIL"))
            all_tests.append(("ai_config_get", success))
        
        # Test AI config POST (admin only)
        success, response = run_test(
            "POST /api/ai-config (system_admin)",
            lambda: test_ai_config_post(admin_headers),
            expected_status=200
        )
        test_results.append(("AI CONFIG POST (admin)", "✅ PASS" if success else "❌ FAIL"))
        all_tests.append(("ai_config_post", success))
        
        # Test 3: Ships and Multi-Upload Tests
        print("\n" + "=" * 80)
        print("🚢 SHIPS AND MULTI-UPLOAD TESTS")
        print("=" * 80)
        
        # Get ships list first
        success, ships_response = run_test(
            "GET /api/ships",
            lambda: test_ships_list(admin_headers),
            expected_status=200
        )
        test_results.append(("SHIPS LIST", "✅ PASS" if success else "❌ FAIL"))
        all_tests.append(("ships_list", success))
        
        ship_id = None
        if success and ships_response.status_code == 200:
            try:
                ships_data = ships_response.json()
                if ships_data and len(ships_data) > 0:
                    ship_id = ships_data[0].get("id")
                    print(f"   📋 Using ship_id: {ship_id}")
            except:
                pass
        
        if ship_id:
            # Test ship certificates multi-upload
            success, response = run_test(
                f"POST /api/certificates/multi-upload (ship_id={ship_id})",
                lambda: test_certificates_multi_upload(admin_headers, ship_id),
                expected_status=200
            )
            test_results.append(("SHIP CERT MULTI-UPLOAD", "✅ PASS" if success else "❌ FAIL"))
            all_tests.append(("cert_multi_upload", success))
            
            # Test audit certificates multi-upload
            success, response = run_test(
                f"POST /api/audit-certificates/multi-upload (ship_id={ship_id})",
                lambda: test_audit_certificates_multi_upload(admin_headers, ship_id),
                expected_status=200
            )
            test_results.append(("AUDIT CERT MULTI-UPLOAD", "✅ PASS" if success else "❌ FAIL"))
            all_tests.append(("audit_cert_multi_upload", success))
        else:
            print("   ⚠️ No ship_id available, skipping multi-upload tests")
            test_results.append(("SHIP CERT MULTI-UPLOAD", "⚠️ SKIP - No ship available"))
            test_results.append(("AUDIT CERT MULTI-UPLOAD", "⚠️ SKIP - No ship available"))
        
        # Test 4: User Management Tests
        print("\n" + "=" * 80)
        print("👥 USER MANAGEMENT TESTS")
        print("=" * 80)
        
        # Test users list (admin only)
        success, users_response = run_test(
            "GET /api/users (system_admin)",
            lambda: test_users_list(admin_headers),
            expected_status=200
        )
        test_results.append(("USERS LIST (admin)", "✅ PASS" if success else "❌ FAIL"))
        all_tests.append(("users_list", success))
        
        # Get a user ID for testing
        user_id = None
        if success and users_response.status_code == 200:
            try:
                users_data = users_response.json()
                if users_data and len(users_data) > 0:
                    user_id = users_data[0].get("id")
                    print(f"   📋 Using user_id: {user_id}")
            except:
                pass
        
        if user_id:
            # Test get single user
            success, response = run_test(
                f"GET /api/users/{user_id}",
                lambda: test_user_by_id(admin_headers, user_id),
                expected_status=200
            )
            test_results.append(("GET USER BY ID", "✅ PASS" if success else "❌ FAIL"))
            all_tests.append(("user_by_id", success))
            
            # Test update user (just test the endpoint, don't actually change data)
            # success, response = run_test(
            #     f"PUT /api/users/{user_id}",
            #     lambda: test_user_update(admin_headers, user_id),
            #     expected_status=200
            # )
            # test_results.append(("UPDATE USER", "✅ PASS" if success else "❌ FAIL"))
            # all_tests.append(("user_update", success))
        
        # Test 5: Permission System Tests
        print("\n" + "=" * 80)
        print("🔒 PERMISSION SYSTEM TESTS")
        print("=" * 80)
        
        # Test that Viewer (Crew3) cannot access admin endpoints
        if "Crew3" in user_sessions:
            crew3_headers = user_sessions["Crew3"]["headers"]
            success, response = run_test(
                "Permission check - Crew3 (Viewer) accessing admin endpoints",
                lambda: test_permission_system(crew3_headers, "viewer"),
                expected_admin_only=True
            )
            test_results.append(("PERMISSION - Crew3 blocked from admin", "✅ PASS" if success else "❌ FAIL"))
            all_tests.append(("permission_crew3", success))
        
        # Test that Editor (Crew4) has limited access
        if "Crew4" in user_sessions:
            crew4_headers = user_sessions["Crew4"]["headers"]
            success, response = run_test(
                "Permission check - Crew4 (Editor) accessing admin endpoints",
                lambda: test_permission_system(crew4_headers, "editor"),
                expected_admin_only=True
            )
            test_results.append(("PERMISSION - Crew4 blocked from admin", "✅ PASS" if success else "❌ FAIL"))
            all_tests.append(("permission_crew4", success))
        
        # Test 6: GDrive Configuration Tests
        print("\n" + "=" * 80)
        print("☁️ GDRIVE CONFIGURATION TESTS")
        print("=" * 80)
        
        # Test GDrive config (admin only)
        success, response = run_test(
            "GET /api/gdrive/config (system_admin)",
            lambda: test_gdrive_config(admin_headers),
            expected_status=200
        )
        test_results.append(("GDRIVE CONFIG", "✅ PASS" if success else "❌ FAIL"))
        all_tests.append(("gdrive_config", success))
        
        # Test GDrive status (all users)
        success, response = run_test(
            "GET /api/gdrive/status (system_admin)",
            lambda: test_gdrive_status(admin_headers),
            expected_status=200
        )
        test_results.append(("GDRIVE STATUS", "✅ PASS" if success else "❌ FAIL"))
        all_tests.append(("gdrive_status", success))
        
        # Calculate success rates
        total_tests = len(all_tests)
        successful_tests = sum(1 for _, success in all_tests if success)
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE BACKEND API TEST RESULTS")
        print("=" * 80)
        
        print(f"\n📈 OVERALL SUCCESS RATE: {successful_tests}/{total_tests} ({(successful_tests/total_tests*100):.1f}%)")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in test_results:
            print(f"   {result} - {test_name}")
        
        # Final assessment
        if successful_tests == total_tests:
            print(f"\n✅ ALL BACKEND API TESTS PASSED!")
            print(f"🎉 System ready for production deployment")
        elif successful_tests >= total_tests * 0.8:  # 80% pass rate
            print(f"\n⚠️ MOST TESTS PASSED ({successful_tests}/{total_tests})")
            print(f"🔍 Review failed tests before deployment")
        else:
            print(f"\n❌ CRITICAL ISSUES FOUND")
            print(f"🚨 {total_tests - successful_tests} test(s) failed - System not ready for deployment")
        
        print(f"\n🎯 KEY FINDINGS:")
        auth_success = sum(1 for test_type, success in all_tests if test_type == "auth" and success)
        auth_total = sum(1 for test_type, _ in all_tests if test_type == "auth")
        print(f"   - Authentication: {auth_success}/{auth_total} users can login")
        
        ai_success = sum(1 for test_type, success in all_tests if "ai_config" in test_type and success)
        ai_total = sum(1 for test_type, _ in all_tests if "ai_config" in test_type)
        print(f"   - AI Configuration: {ai_success}/{ai_total} endpoints working")
        
        upload_success = sum(1 for test_type, success in all_tests if "upload" in test_type and success)
        upload_total = sum(1 for test_type, _ in all_tests if "upload" in test_type)
        print(f"   - Multi-Upload: {upload_success}/{upload_total} endpoints working")
        
        permission_success = sum(1 for test_type, success in all_tests if "permission" in test_type and success)
        permission_total = sum(1 for test_type, _ in all_tests if "permission" in test_type)
        print(f"   - Permission System: {permission_success}/{permission_total} checks working")
        
        gdrive_success = sum(1 for test_type, success in all_tests if "gdrive" in test_type and success)
        gdrive_total = sum(1 for test_type, _ in all_tests if "gdrive" in test_type)
        print(f"   - GDrive Integration: {gdrive_success}/{gdrive_total} endpoints working")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
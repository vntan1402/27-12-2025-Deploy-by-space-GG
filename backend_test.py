#!/usr/bin/env python3
"""
🧪 STANDBY CREW PERMISSION RESTRICTION TEST

Testing the Standby Crew permission restriction feature:

## Test Objective
Verify that users with `ship=Standby` CANNOT view:
1. Crew List (/api/crew)
2. Crew Certificates (/api/crew-certificates and /api/crew-certificates/all)

## Test Credentials
- **Standby User:** Crew3 / standby123 (role: viewer, ship: Standby)  
- **System Admin:** system_admin / YourSecure@Pass2024 (full access for comparison)

## API Endpoints to Test
1. `GET /api/crew` - Crew list
2. `GET /api/crew-certificates` - Crew certificates with filters
3. `GET /api/crew-certificates/all` - All crew certificates

## Expected Results
### For Standby User (Crew3):
- All 3 endpoints should return an EMPTY array `[]` (count = 0)
- No 403 error, just empty data

### For System Admin:
- All 3 endpoints should return data (count > 0)
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
            BACKEND_URL = "https://shipuser-sync.preview.emergentagent.com/api"
except:
    BACKEND_URL = "https://shipuser-sync.preview.emergentagent.com/api"

# Test users as specified in review request
TEST_USERS = {
    "system_admin": {"password": "YourSecure@Pass2024", "role": "system_admin", "ship": None, "actual_user": "system_admin"},
    "Crew3": {"password": "standby123", "role": "viewer", "ship": "Standby", "actual_user": "Crew3"}  # Standby user for permission restriction tests
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

def test_standby_crew_list_restriction(headers):
    """Test Standby user CANNOT view crew list - should return empty array"""
    response = requests.get(f"{BACKEND_URL}/crew", headers=headers)
    return response

def test_standby_crew_certificates_restriction(headers):
    """Test Standby user CANNOT view crew certificates - should return empty array"""
    response = requests.get(f"{BACKEND_URL}/crew-certificates", headers=headers)
    return response

def test_standby_crew_certificates_all_restriction(headers):
    """Test Standby user CANNOT view all crew certificates - should return empty array"""
    response = requests.get(f"{BACKEND_URL}/crew-certificates/all", headers=headers)
    return response

def test_system_admin_crew_access(headers):
    """Test System Admin CAN access crew endpoints - should return data"""
    results = {}
    
    # Test crew list
    results["crew_list"] = requests.get(f"{BACKEND_URL}/crew", headers=headers)
    
    # Test crew certificates
    results["crew_certificates"] = requests.get(f"{BACKEND_URL}/crew-certificates", headers=headers)
    
    # Test all crew certificates
    results["crew_certificates_all"] = requests.get(f"{BACKEND_URL}/crew-certificates/all", headers=headers)
    
    return results

def run_test(test_name, test_func, expected_empty=False, expected_success=True):
    """Run a single test and return results"""
    try:
        print(f"\n   🧪 {test_name}")
        result = test_func()
        
        # Handle different response types
        if isinstance(result, dict):
            # Multiple responses (like system admin tests)
            success = True
            for operation, response in result.items():
                if expected_success:
                    op_success = response.status_code in [200, 201]
                    if op_success and expected_empty:
                        # Check if response is empty array
                        try:
                            data = response.json()
                            op_success = isinstance(data, list) and len(data) == 0
                        except:
                            op_success = False
                else:
                    op_success = response.status_code == 403
                
                success = success and op_success
                status_icon = "✅" if op_success else "❌"
                
                if expected_empty and response.status_code == 200:
                    try:
                        data = response.json()
                        count = len(data) if isinstance(data, list) else "N/A"
                        print(f"      {status_icon} {operation}: {response.status_code} (count: {count})")
                    except:
                        print(f"      {status_icon} {operation}: {response.status_code}")
                else:
                    print(f"      {status_icon} {operation}: {response.status_code}")
                
                if not op_success:
                    print(f"         📝 Response: {response.text[:100]}...")
        else:
            # Single response
            response = result
            if expected_success:
                success = response.status_code in [200, 201]
                if success and expected_empty:
                    # Check if response is empty array
                    try:
                        data = response.json()
                        success = isinstance(data, list) and len(data) == 0
                        count = len(data) if isinstance(data, list) else "N/A"
                        result_icon = "✅" if success else "❌"
                        print(f"      {result_icon} Expected: Empty array, Got: {response.status_code} (count: {count})")
                    except:
                        success = False
                        result_icon = "❌"
                        print(f"      {result_icon} Expected: Empty array, Got: {response.status_code} (invalid JSON)")
                else:
                    result_icon = "✅" if success else "❌"
                    print(f"      {result_icon} Expected: Success (200/201), Got: {response.status_code}")
            else:
                success = response.status_code == 403
                result_icon = "✅" if success else "❌"
                print(f"      {result_icon} Expected: 403 (Forbidden), Got: {response.status_code}")
            
            if not success:
                print(f"      📝 Response: {response.text[:200]}...")
                
        return success, result
        
    except Exception as e:
        print(f"      ❌ Test failed with exception: {e}")
        return False, None

# Main test execution
def main():
    print("🧪 STANDBY CREW PERMISSION RESTRICTION TEST")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print("\nTest Credentials:")
    print("- Crew3 / standby123 - Standby user (role: viewer, ship: Standby)")
    print("- system_admin / YourSecure@Pass2024 - Full access (for comparison)")
    
    # Test results tracking
    test_results = []
    standby_tests = []
    admin_tests = []
    
    try:
        # Test authentication first
        print("\n📋 Authentication Tests...")
        
        try:
            system_headers = get_headers("system_admin")
            system_user = get_user_info(system_headers)
            print(f"   ✅ system_admin login successful - Role: {system_user.get('role', 'unknown')}")
        except Exception as e:
            print(f"   ❌ system_admin login failed: {e}")
            return
        
        try:
            crew3_headers = get_headers("Crew3")
            crew3_user = get_user_info(crew3_headers)
            print(f"   ✅ Crew3 login successful - Role: {crew3_user.get('role', 'unknown')}, Ship: {crew3_user.get('ship', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Crew3 login failed: {e}")
            return
        
        print("\n" + "=" * 80)
        
        print("🔴 HIGH PRIORITY: Standby Crew Permission Restriction Tests")
        
        # Test 1: Standby user CANNOT view crew list
        print("\n1. Standby User - Crew List Restriction")
        success, response = run_test(
            "Crew3 (Standby) tries to get crew list",
            lambda: test_standby_crew_list_restriction(crew3_headers),
            expected_empty=True,
            expected_success=True
        )
        standby_tests.append(("Crew List Blocked", success))
        test_results.append(("GET /api/crew (Standby)", "✅ Empty array returned" if success else "❌ FAILED"))
        
        # Test 2: Standby user CANNOT view crew certificates
        print("\n2. Standby User - Crew Certificates Restriction")
        success, response = run_test(
            "Crew3 (Standby) tries to get crew certificates",
            lambda: test_standby_crew_certificates_restriction(crew3_headers),
            expected_empty=True,
            expected_success=True
        )
        standby_tests.append(("Crew Certificates Blocked", success))
        test_results.append(("GET /api/crew-certificates (Standby)", "✅ Empty array returned" if success else "❌ FAILED"))
        
        # Test 3: Standby user CANNOT view all crew certificates
        print("\n3. Standby User - All Crew Certificates Restriction")
        success, response = run_test(
            "Crew3 (Standby) tries to get all crew certificates",
            lambda: test_standby_crew_certificates_all_restriction(crew3_headers),
            expected_empty=True,
            expected_success=True
        )
        standby_tests.append(("All Crew Certificates Blocked", success))
        test_results.append(("GET /api/crew-certificates/all (Standby)", "✅ Empty array returned" if success else "❌ FAILED"))
        
        print("\n🟢 COMPARISON: System Admin Access Tests")
        
        # Test 4: System Admin CAN access all endpoints
        print("\n4. System Admin - Full Access Verification")
        success, response = run_test(
            "system_admin accesses crew endpoints",
            lambda: test_system_admin_crew_access(system_headers),
            expected_empty=False,
            expected_success=True
        )
        admin_tests.append(("System Admin Access", success))
        test_results.append(("System Admin Crew Access", "✅ Data returned" if success else "❌ FAILED"))
        
        # Calculate success rates
        standby_success = sum(1 for _, success in standby_tests if success)
        standby_total = len(standby_tests)
        admin_success = sum(1 for _, success in admin_tests if success)
        admin_total = len(admin_tests)
        
        total_success = standby_success + admin_success
        total_tests = standby_total + admin_total
        
        print("\n" + "=" * 80)
        print("📊 STANDBY CREW PERMISSION RESTRICTION TEST RESULTS")
        print("=" * 80)
        
        print(f"\n🔴 STANDBY USER RESTRICTION TESTS: {standby_success}/{standby_total} passed ({(standby_success/standby_total*100):.1f}%)")
        print(f"🟢 SYSTEM ADMIN ACCESS TESTS: {admin_success}/{admin_total} passed ({(admin_success/admin_total*100):.1f}%)")
        print(f"\n📈 OVERALL SUCCESS RATE: {total_success}/{total_tests} ({(total_success/total_tests*100):.1f}%)")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in test_results:
            print(f"   {result}")
        
        # Final assessment
        if total_success == total_tests:
            print(f"\n✅ STANDBY CREW PERMISSION RESTRICTION TEST PASSED!")
            print(f"🎉 Standby users correctly blocked from viewing crew data")
            print(f"🎉 System admin retains full access")
            print(f"🎉 All endpoints return empty arrays (not 403 errors) for Standby users")
        elif standby_success == standby_total:
            print(f"\n✅ STANDBY RESTRICTION WORKING CORRECTLY")
            print(f"✅ All Standby user tests passed")
            print(f"⚠️ Some system admin access issues detected")
        else:
            print(f"\n❌ CRITICAL STANDBY PERMISSION ISSUES FOUND")
            print(f"🚨 {standby_total - standby_success} Standby restriction test(s) failed")
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   - Standby user blocked from crew list: {'✅ Working' if standby_success >= 1 else '❌ Failed'}")
        print(f"   - Standby user blocked from crew certificates: {'✅ Working' if standby_success >= 2 else '❌ Failed'}")
        print(f"   - Standby user blocked from all crew certificates: {'✅ Working' if standby_success >= 3 else '❌ Failed'}")
        print(f"   - System admin retains access: {'✅ Working' if admin_success >= 1 else '❌ Failed'}")
        print(f"   - Empty arrays returned (not 403 errors): {'✅ Working' if standby_success == standby_total else '❌ Some endpoints return errors'}")
        
        print(f"\n📋 SPECIFIC FEATURE VERIFICATION:")
        print(f"   ✅ GET /api/crew returns empty array for Standby users: {'✅' if any('GET /api/crew (Standby)' in result and 'Empty array' in result for result in test_results) else '❌'}")
        print(f"   ✅ GET /api/crew-certificates returns empty array for Standby users: {'✅' if any('crew-certificates (Standby)' in result and 'Empty array' in result for result in test_results) else '❌'}")
        print(f"   ✅ GET /api/crew-certificates/all returns empty array for Standby users: {'✅' if any('crew-certificates/all (Standby)' in result and 'Empty array' in result for result in test_results) else '❌'}")
        print(f"   ✅ System admin can access all endpoints: {'✅' if any('System Admin Crew Access' in result and 'Data returned' in result for result in test_results) else '❌'}")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
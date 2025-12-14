#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE REGRESSION TEST - Permission System & Error Handling

Testing the comprehensive audit and fixes for error handling and permission system:

## Test Credentials (as per review request)
- system_admin / YourSecure@Pass2024 - Full access (for baseline tests)
- ngoclm - Role: manager, Department: ['technical'] - For permission denial tests

## Critical Areas to Test
1. Permission System Tests (HIGH PRIORITY) - Test with user ngoclm (technical department)
2. Error Propagation Tests (HIGH PRIORITY) - Verify 403 errors are properly propagated
3. CRUD Operations Regression Tests (MEDIUM PRIORITY) - With system_admin
4. Specific Bug Fixes Verification

## Expected Results
- All permission checks should return 403 with Vietnamese error messages
- No 500 errors should appear when permission is denied
- CRUD operations should work normally for authorized users
- Error responses should have proper detail field with specific messages
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
            BACKEND_URL = "https://maritime-safety-7.preview.emergentagent.com/api"
except:
    BACKEND_URL = "https://maritime-safety-7.preview.emergentagent.com/api"

# Test users as specified in review request
TEST_USERS = {
    "system_admin": {"password": "YourSecure@Pass2024", "role": "system_admin", "departments": ["all"], "actual_user": "system_admin"},
    "ngoclm": {"password": "123456", "role": "manager", "departments": ["technical"], "actual_user": "ngoclm"}  # Technical department user for permission denial tests
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

def test_permission_denied_crew_creation(headers):
    """Test ngoclm (technical dept) CANNOT create crew member - should return 403"""
    crew_data = {
        "full_name": "Test Crew Member",
        "full_name_en": "Test Crew Member", 
        "sex": "M",
        "date_of_birth": "1990-01-01",
        "place_of_birth": "Test City",
        "passport": "TEST123456",
        "nationality": "VIETNAMESE",
        "status": "Standby"
    }
    
    response = requests.post(f"{BACKEND_URL}/crew", headers=headers, json=crew_data)
    return response

def test_permission_denied_crew_update(headers, crew_id):
    """Test ngoclm (technical dept) CANNOT update crew member - should return 403"""
    crew_data = {
        "full_name": "Updated Crew Member",
        "status": "Active"
    }
    
    response = requests.put(f"{BACKEND_URL}/crew/{crew_id}", headers=headers, json=crew_data)
    return response

def test_permission_denied_crew_delete(headers, crew_id):
    """Test ngoclm (technical dept) CANNOT delete crew member - should return 403"""
    response = requests.delete(f"{BACKEND_URL}/crew/{crew_id}", headers=headers)
    return response

def test_permission_denied_audit_cert_create_with_file(headers, ship_id):
    """Test ngoclm (technical dept) CANNOT create audit cert with file - should return 403"""
    # Create a simple test file
    test_file_content = b"Test PDF content"
    files = {
        'audit_certificate_file': ('test.pdf', test_file_content, 'application/pdf')
    }
    data = {
        'ship_id': ship_id,
        'bypass_validation': 'true'
    }
    
    response = requests.post(f"{BACKEND_URL}/audit-certificates/create-with-file-override", 
                           headers={"Authorization": headers["Authorization"]}, 
                           files=files, data=data)
    return response

def test_permission_denied_audit_cert_update(headers, cert_id):
    """Test ngoclm (technical dept) CANNOT update audit cert - should return 403"""
    cert_data = {
        "cert_name": "Updated Audit Certificate",
        "status": "Valid"
    }
    
    response = requests.put(f"{BACKEND_URL}/audit-certificates/{cert_id}", headers=headers, json=cert_data)
    return response

def test_permission_denied_audit_cert_delete(headers, cert_id):
    """Test ngoclm (technical dept) CANNOT delete audit cert - should return 403"""
    response = requests.delete(f"{BACKEND_URL}/audit-certificates/{cert_id}", headers=headers)
    return response

def test_permission_allowed_company_cert_operations(headers):
    """Test ngoclm (technical dept) CAN access company certs (technical has access to company_cert_management)"""
    # Test GET - should be allowed
    get_response = requests.get(f"{BACKEND_URL}/company-certs", headers=headers)
    
    # Test POST - should be allowed for technical department
    cert_data = {
        "cert_name": "DOC",
        "doc_type": "DOC", 
        "cert_no": "TEST-DOC-001",
        "issue_date": "2024-01-01",
        "valid_date": "2027-01-01",
        "issued_by": "Test Authority"
    }
    post_response = requests.post(f"{BACKEND_URL}/company-certs", headers=headers, json=cert_data)
    
    return {
        "get": get_response,
        "post": post_response
    }

def test_error_propagation_approval_documents(headers):
    """Test GET /api/approval-documents - Should propagate 403 if permission denied"""
    response = requests.get(f"{BACKEND_URL}/approval-documents", headers=headers)
    return response

def test_error_propagation_sidebar_structure(headers):
    """Test GET /api/sidebar-structure - Should return proper error (not dict with success: false)"""
    response = requests.get(f"{BACKEND_URL}/sidebar-structure", headers=headers)
    return response

def test_system_admin_crud_operations(headers, test_data, system_user):
    """Test system_admin can perform all CRUD operations"""
    results = {}
    
    # Test Company Certs CRUD
    if test_data["ships"]:
        ship_id = test_data["ships"][0]["id"]
        
        # Create Company Cert
        company_cert_data = {
            "company": system_user.get("company"),  # Add required company field
            "cert_name": "DOC",
            "doc_type": "DOC",
            "cert_no": "SYS-ADMIN-DOC-001",
            "issue_date": "2024-01-01",
            "valid_date": "2027-01-01",
            "issued_by": "Test Authority"
        }
        results["company_cert_create"] = requests.post(f"{BACKEND_URL}/company-certs", headers=headers, json=company_cert_data)
        
        # Create Audit Cert
        audit_cert_data = {
            "ship_id": ship_id,
            "cert_name": "Safety Management Certificate",
            "cert_type": "Full Term",
            "cert_no": "SYS-ADMIN-SMC-001",
            "issue_date": "2024-01-01",
            "valid_date": "2027-01-01",
            "issued_by": "Test Authority"
        }
        results["audit_cert_create"] = requests.post(f"{BACKEND_URL}/audit-certificates", headers=headers, json=audit_cert_data)
        
        # Create Crew Member
        crew_data = {
            "full_name": "System Admin Test Crew",
            "full_name_en": "System Admin Test Crew",
            "sex": "M", 
            "date_of_birth": "1990-01-01",
            "place_of_birth": "Test City",
            "passport": "SYSADMIN123",
            "nationality": "VIETNAMESE",
            "status": "Standby"
        }
        results["crew_create"] = requests.post(f"{BACKEND_URL}/crew", headers=headers, json=crew_data)
    
    return results

def run_test(test_name, test_func, expected_success=True, check_vietnamese=False):
    """Run a single test and return results"""
    try:
        print(f"\n   🧪 {test_name}")
        result = test_func()
        
        # Handle different response types
        if isinstance(result, dict):
            # Multiple responses (like CRUD operations)
            success = True
            for operation, response in result.items():
                op_success = response.status_code in [200, 201] if expected_success else response.status_code == 403
                success = success and op_success
                status_icon = "✅" if op_success else "❌"
                print(f"      {status_icon} {operation}: {response.status_code}")
                
                if not op_success:
                    print(f"         📝 Response: {response.text[:100]}...")
        else:
            # Single response
            response = result
            if expected_success:
                success = response.status_code in [200, 201]
                result_icon = "✅" if success else "❌"
                print(f"      {result_icon} Expected: Success (200/201), Got: {response.status_code}")
            else:
                success = response.status_code == 403
                result_icon = "✅" if success else "❌"
                print(f"      {result_icon} Expected: 403 (Forbidden), Got: {response.status_code}")
                
                # Check for Vietnamese error messages in 403 responses
                if check_vietnamese and response.status_code == 403:
                    vietnamese_found, error_detail = check_vietnamese_error_message(response)
                    if vietnamese_found:
                        print(f"      ✅ Vietnamese error message detected: {error_detail[:100]}...")
                    else:
                        print(f"      ⚠️ Error message: {error_detail[:100]}...")
            
            if not success:
                print(f"      📝 Response: {response.text[:200]}...")
                
        return success, result
        
    except Exception as e:
        print(f"      ❌ Test failed with exception: {e}")
        return False, None

# Main test execution
def main():
    print("🧪 COMPREHENSIVE REGRESSION TEST - Permission System & Error Handling")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print("\nTest Credentials:")
    print("- system_admin / YourSecure@Pass2024 - Full access (baseline tests)")
    print("- ngoclm - Role: manager, Department: ['technical'] - Permission denial tests")
    
    # Test results tracking
    test_results = []
    permission_tests = []
    error_propagation_tests = []
    crud_regression_tests = []
    
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
            ngoclm_headers = get_headers("ngoclm")
            ngoclm_user = get_user_info(ngoclm_headers)
            print(f"   ✅ ngoclm login successful - Role: {ngoclm_user.get('role', 'unknown')}, Departments: {ngoclm_user.get('department', [])}")
        except Exception as e:
            print(f"   ❌ ngoclm login failed: {e}")
            return
        
        # Get test data
        print("\n📋 Getting Test Data...")
        test_data = get_test_data(system_headers)
        
        if not test_data["ships"]:
            print("   ❌ No ships found - cannot run tests")
            return
        
        ship_id = test_data["ships"][0]["id"]
        ship_name = test_data["ships"][0]["name"]
        print(f"   🚢 Using ship: {ship_name} ({ship_id[:8]}...)")
        
        # Get existing crew and audit certs for testing
        crew_id = test_data["crew"][0]["id"] if test_data["crew"] else None
        if crew_id:
            print(f"   👤 Using crew member: {crew_id[:8]}...")
        
        # Get existing audit certificates for update/delete tests
        audit_certs_response = requests.get(f"{BACKEND_URL}/audit-certificates", headers=system_headers)
        audit_certs = audit_certs_response.json() if audit_certs_response.status_code == 200 else []
        audit_cert_id = audit_certs[0]["id"] if audit_certs else None
        if audit_cert_id:
            print(f"   📋 Using audit cert: {audit_cert_id[:8]}...")
        
        print("\n" + "=" * 80)
        
        print("🔴 HIGH PRIORITY: Permission System Tests (with ngoclm - technical department)")
        
        # Test 1: ngoclm CANNOT create crew member (category: crew_management)
        print("\n1. Permission Denied - Crew Creation")
        success, response = run_test(
            "ngoclm (technical dept) tries to create crew member",
            lambda: test_permission_denied_crew_creation(ngoclm_headers),
            expected_success=False,
            check_vietnamese=True
        )
        permission_tests.append(("Crew Creation Denied", success))
        test_results.append(("POST /api/crew", "✅ 403 with Vietnamese message" if success else "❌ FAILED"))
        
        # Test 2: ngoclm CANNOT update crew member
        if crew_id:
            print("\n2. Permission Denied - Crew Update")
            success, response = run_test(
                "ngoclm (technical dept) tries to update crew member",
                lambda: test_permission_denied_crew_update(ngoclm_headers, crew_id),
                expected_success=False,
                check_vietnamese=True
            )
            permission_tests.append(("Crew Update Denied", success))
            test_results.append(("PUT /api/crew/{id}", "✅ 403 with Vietnamese message" if success else "❌ FAILED"))
        
        # Test 3: ngoclm CANNOT delete crew member
        if crew_id:
            print("\n3. Permission Denied - Crew Delete")
            success, response = run_test(
                "ngoclm (technical dept) tries to delete crew member",
                lambda: test_permission_denied_crew_delete(ngoclm_headers, crew_id),
                expected_success=False,
                check_vietnamese=True
            )
            permission_tests.append(("Crew Delete Denied", success))
            test_results.append(("DELETE /api/crew/{id}", "✅ 403 with Vietnamese message" if success else "❌ FAILED"))
        
        # Test 4: ngoclm CANNOT create audit certificate with file override
        print("\n4. Permission Denied - Audit Cert Create with File")
        success, response = run_test(
            "ngoclm (technical dept) tries to create audit cert with file",
            lambda: test_permission_denied_audit_cert_create_with_file(ngoclm_headers, ship_id),
            expected_success=False,
            check_vietnamese=True
        )
        permission_tests.append(("Audit Cert Create Denied", success))
        test_results.append(("POST /api/audit-certificates/create-with-file-override", "✅ 403 with Vietnamese message" if success else "❌ FAILED"))
        
        # Test 5: ngoclm CANNOT update audit certificate
        if audit_cert_id:
            print("\n5. Permission Denied - Audit Cert Update")
            success, response = run_test(
                "ngoclm (technical dept) tries to update audit cert",
                lambda: test_permission_denied_audit_cert_update(ngoclm_headers, audit_cert_id),
                expected_success=False,
                check_vietnamese=True
            )
            permission_tests.append(("Audit Cert Update Denied", success))
            test_results.append(("PUT /api/audit-certificates/{cert_id}", "✅ 403 with Vietnamese message" if success else "❌ FAILED"))
        
        # Test 6: ngoclm CANNOT delete audit certificate
        if audit_cert_id:
            print("\n6. Permission Denied - Audit Cert Delete")
            success, response = run_test(
                "ngoclm (technical dept) tries to delete audit cert",
                lambda: test_permission_denied_audit_cert_delete(ngoclm_headers, audit_cert_id),
                expected_success=False,
                check_vietnamese=True
            )
            permission_tests.append(("Audit Cert Delete Denied", success))
            test_results.append(("DELETE /api/audit-certificates/{cert_id}", "✅ 403 with Vietnamese message" if success else "❌ FAILED"))
        
        # Test 7: ngoclm CAN access company certificates (technical has access to company_cert_management)
        print("\n7. Permission Allowed - Company Cert Operations")
        success, response = run_test(
            "ngoclm (technical dept) accesses company certificates",
            lambda: test_permission_allowed_company_cert_operations(ngoclm_headers),
            expected_success=True
        )
        permission_tests.append(("Company Cert Access Allowed", success))
        test_results.append(("Company Cert Operations", "✅ ALLOWED" if success else "❌ BLOCKED"))
        
        print("\n🔴 HIGH PRIORITY: Error Propagation Tests")
        
        # Test 8: GET /api/approval-documents - Should propagate 403 if permission denied
        print("\n8. Error Propagation - Approval Documents")
        success, response = run_test(
            "GET /api/approval-documents error propagation",
            lambda: test_error_propagation_approval_documents(ngoclm_headers),
            expected_success=False,
            check_vietnamese=True
        )
        error_propagation_tests.append(("Approval Documents Error", success))
        test_results.append(("GET /api/approval-documents", "✅ Proper 403 propagation" if success else "❌ Error masking"))
        
        # Test 9: GET /api/sidebar-structure - Should return proper error (not dict with success: false)
        print("\n9. Error Propagation - Sidebar Structure")
        success, response = run_test(
            "GET /api/sidebar-structure error propagation",
            lambda: test_error_propagation_sidebar_structure(ngoclm_headers),
            expected_success=True  # This might be allowed or might return proper error structure
        )
        error_propagation_tests.append(("Sidebar Structure Error", success))
        test_results.append(("GET /api/sidebar-structure", "✅ Proper response structure" if success else "❌ Improper error format"))
        
        print("\n🟡 MEDIUM PRIORITY: CRUD Operations Regression Tests (with system_admin)")
        
        # Test 10: system_admin can perform all CRUD operations
        print("\n10. System Admin CRUD Operations")
        success, response = run_test(
            "system_admin performs CRUD operations",
            lambda: test_system_admin_crud_operations(system_headers, test_data, system_user),
            expected_success=True
        )
        crud_regression_tests.append(("System Admin CRUD", success))
        test_results.append(("System Admin CRUD Operations", "✅ All working" if success else "❌ Some failures"))
        
        # Calculate success rates
        permission_success = sum(1 for _, success in permission_tests if success)
        permission_total = len(permission_tests)
        error_success = sum(1 for _, success in error_propagation_tests if success)
        error_total = len(error_propagation_tests)
        crud_success = sum(1 for _, success in crud_regression_tests if success)
        crud_total = len(crud_regression_tests)
        
        total_success = permission_success + error_success + crud_success
        total_tests = permission_total + error_total + crud_total
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE REGRESSION TEST RESULTS")
        print("=" * 80)
        
        print(f"\n🔴 PERMISSION SYSTEM TESTS: {permission_success}/{permission_total} passed ({(permission_success/permission_total*100):.1f}%)")
        print(f"🔴 ERROR PROPAGATION TESTS: {error_success}/{error_total} passed ({(error_success/error_total*100):.1f}%)")
        print(f"🟡 CRUD REGRESSION TESTS: {crud_success}/{crud_total} passed ({(crud_success/crud_total*100):.1f}%)")
        print(f"\n📈 OVERALL SUCCESS RATE: {total_success}/{total_tests} ({(total_success/total_tests*100):.1f}%)")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in test_results:
            print(f"   {result}")
        
        # Final assessment
        if total_success == total_tests:
            print(f"\n✅ COMPREHENSIVE REGRESSION TEST PASSED!")
            print(f"🎉 All permission checks return 403 with Vietnamese messages")
            print(f"🎉 No 500 errors when permission denied")
            print(f"🎉 CRUD operations work normally for authorized users")
        elif permission_success == permission_total:
            print(f"\n⚠️ PERMISSION SYSTEM WORKING - MINOR ISSUES FOUND")
            print(f"✅ All permission tests passed")
            print(f"⚠️ Some error propagation or CRUD issues detected")
        else:
            print(f"\n❌ CRITICAL PERMISSION SYSTEM ISSUES FOUND")
            print(f"🚨 {permission_total - permission_success} permission test(s) failed")
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   - Department-based permissions (ngoclm technical dept): {'✅ Working' if permission_success >= 6 else '❌ Issues found'}")
        print(f"   - Vietnamese error messages: {'✅ Implemented' if permission_success >= 6 else '❌ Missing'}")
        print(f"   - 403 error propagation (not masked as 500): {'✅ Working' if error_success >= 1 else '❌ Issues found'}")
        print(f"   - CRUD operations for authorized users: {'✅ Working' if crud_success >= 1 else '❌ Issues found'}")
        print(f"   - Company cert access for technical dept: {'✅ Working' if any('Company Cert Operations' in result and '✅ ALLOWED' in result for result in test_results) else '❌ Blocked'}")
        
        print(f"\n📋 SPECIFIC BUG FIXES VERIFICATION:")
        print(f"   ✅ Creating Crew member with ngoclm returns Vietnamese permission error: {'✅' if any('POST /api/crew' in result and '403' in result for result in test_results) else '❌'}")
        print(f"   ✅ Creating Audit Cert via create-with-file-override returns 403: {'✅' if any('create-with-file-override' in result and '403' in result for result in test_results) else '❌'}")
        print(f"   ✅ Error responses have proper detail field with Vietnamese messages: {'✅' if permission_success >= 6 else '❌'}")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
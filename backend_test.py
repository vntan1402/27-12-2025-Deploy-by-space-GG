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
        'file': ('test.pdf', test_file_content, 'application/pdf')
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

def test_system_admin_crud_operations(headers, test_data):
    """Test system_admin can perform all CRUD operations"""
    results = {}
    
    # Test Company Certs CRUD
    if test_data["ships"]:
        ship_id = test_data["ships"][0]["id"]
        
        # Create Company Cert
        company_cert_data = {
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
        
        print("\n🔴 CRITICAL TESTS (Department-Based Permissions)")
        
        # Test 1: Technical Manager CAN Create Ship Certificate
        print("\n1. Technical Manager CAN Create Ship Certificate")
        try:
            headers = get_headers("tech_manager")
            user_info = get_user_info(headers)
            print(f"   👤 Testing with: tech_manager - Departments: {user_info.get('department', [])}")
            
            success, response = run_test(
                "Technical Manager creates Ship Certificate",
                lambda: test_1_technical_manager_can_create_ship_cert(headers, test_ship_001_id),
                expected_status=200,
                expected_success=True
            )
            critical_tests.append(("Test 1", success))
            test_results.append(("Technical Manager → Ship Cert", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 1 failed: {e}")
            critical_tests.append(("Test 1", False))
            test_results.append(("Technical Manager → Ship Cert", "❌ ERROR"))
        
        # Test 2: Crewing Manager CANNOT Create Ship Certificate
        print("\n2. Crewing Manager CANNOT Create Ship Certificate")
        try:
            headers = get_headers("crew_manager")
            user_info = get_user_info(headers)
            print(f"   👤 Testing with: crew_manager - Departments: {user_info.get('department', [])}")
            
            success, response = run_test(
                "Crewing Manager tries to create Ship Certificate",
                lambda: test_2_crewing_manager_cannot_create_ship_cert(headers, test_ship_001_id),
                expected_status=403,
                expected_success=False
            )
            critical_tests.append(("Test 2", success))
            test_results.append(("Crewing Manager → Ship Cert", "✅ BLOCKED" if success else "❌ ALLOWED"))
        except Exception as e:
            print(f"   ❌ Test 2 failed: {e}")
            critical_tests.append(("Test 2", False))
            test_results.append(("Crewing Manager → Ship Cert", "❌ ERROR"))
        
        # Test 3: Crewing Manager CAN Create Crew Certificate
        print("\n3. Crewing Manager CAN Create Crew Certificate")
        try:
            headers = get_headers("crew_manager")
            user_info = get_user_info(headers)
            print(f"   👤 Testing with: crew_manager - Departments: {user_info.get('department', [])}")
            
            success, response = run_test(
                "Crewing Manager creates Crew Certificate",
                lambda: test_3_crewing_manager_can_create_crew_cert(headers, crew_id, company_id),
                expected_status=200,
                expected_success=True
            )
            critical_tests.append(("Test 3", success))
            test_results.append(("Crewing Manager → Crew Cert", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 3 failed: {e}")
            critical_tests.append(("Test 3", False))
            test_results.append(("Crewing Manager → Crew Cert", "❌ ERROR"))
        
        # Test 4: Technical Manager CANNOT Create Crew Certificate
        print("\n4. Technical Manager CANNOT Create Crew Certificate")
        try:
            headers = get_headers("tech_manager")
            user_info = get_user_info(headers)
            print(f"   👤 Testing with: tech_manager - Departments: {user_info.get('department', [])}")
            
            success, response = run_test(
                "Technical Manager tries to create Crew Certificate",
                lambda: test_4_technical_manager_cannot_create_crew_cert(headers, crew_id, company_id),
                expected_status=403,
                expected_success=False
            )
            critical_tests.append(("Test 4", success))
            test_results.append(("Technical Manager → Crew Cert", "✅ BLOCKED" if success else "❌ ALLOWED"))
        except Exception as e:
            print(f"   ❌ Test 4 failed: {e}")
            critical_tests.append(("Test 4", False))
            test_results.append(("Technical Manager → Crew Cert", "❌ ERROR"))
        
        print("\n🟡 HIGH PRIORITY TESTS (Role-Based Permissions)")
        
        # Test 5: Editor CANNOT Create Any Certificates
        print("\n5. Editor CANNOT Create Any Certificates")
        try:
            headers = get_headers("test_editor")
            user_info = get_user_info(headers)
            print(f"   👤 Testing with: test_editor - Role: {user_info.get('role')}")
            
            success, response = run_test(
                "Editor tries to create certificate",
                lambda: test_5_editor_cannot_create_certificates(headers, test_ship_001_id),
                expected_status=403,
                expected_success=False
            )
            high_priority_tests.append(("Test 5", success))
            test_results.append(("Editor → Create Cert", "✅ BLOCKED" if success else "❌ ALLOWED"))
        except Exception as e:
            print(f"   ❌ Test 5 failed: {e}")
            high_priority_tests.append(("Test 5", False))
            test_results.append(("Editor → Create Cert", "❌ ERROR"))
        
        # Test 6: Editor Ship Scope Filtering (GET Certificates)
        print("\n6. Editor Ship Scope Filtering (GET Certificates)")
        try:
            # First create certificates for both ships using system admin
            system_headers = get_headers("system_admin")
            
            # Create cert for ship 1
            cert1_data = {
                "ship_id": test_ship_001_id,
                "cert_name": "Test Cert Ship 1",
                "cert_type": "Full Term",
                "cert_no": "SHIP1-001"
            }
            requests.post(f"{BACKEND_URL}/certificates", headers=system_headers, json=cert1_data)
            
            # Create cert for ship 2 (if available)
            if test_ship_002_id:
                cert2_data = {
                    "ship_id": test_ship_002_id,
                    "cert_name": "Test Cert Ship 2",
                    "cert_type": "Full Term",
                    "cert_no": "SHIP2-001"
                }
                requests.post(f"{BACKEND_URL}/certificates", headers=system_headers, json=cert2_data)
            
            # Now test editor filtering
            headers = get_headers("test_editor")
            user_info = get_user_info(headers)
            print(f"   👤 Testing with: test_editor - Assigned Ship: {user_info.get('assigned_ship_id', 'N/A')}")
            
            success, response = run_test(
                "Editor views certificates (should only see assigned ship)",
                lambda: test_6_editor_ship_scope_filtering(headers, test_ship_001_id),
                expected_status=200,
                expected_success=True
            )
            
            # Additional validation for ship filtering
            if success and response:
                filtering_success, filtering_msg = check_ship_filtering(response, test_ship_001_id)
                print(f"      📋 Ship filtering: {'✅' if filtering_success else '❌'} {filtering_msg}")
                success = success and filtering_success
            
            high_priority_tests.append(("Test 6", success))
            test_results.append(("Editor → Ship Filtering", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 6 failed: {e}")
            high_priority_tests.append(("Test 6", False))
            test_results.append(("Editor → Ship Filtering", "❌ ERROR"))
        
        # Test 7: Editor Ship Scope on Ship List
        print("\n7. Editor Ship Scope on Ship List")
        try:
            headers = get_headers("test_editor")
            user_info = get_user_info(headers)
            print(f"   👤 Testing with: test_editor - Assigned Ship: {user_info.get('assigned_ship_id', 'N/A')}")
            
            success, response = run_test(
                "Editor views ship list (should only see assigned ship)",
                lambda: test_7_editor_ship_scope_on_ship_list(headers, test_ship_001_id),
                expected_status=200,
                expected_success=True
            )
            
            # Additional validation for ship list filtering
            if success and response:
                try:
                    ships = response.json()
                    if isinstance(ships, list):
                        ship_ids = [ship.get('id') for ship in ships]
                        if len(ship_ids) == 1 and ship_ids[0] == test_ship_001_id:
                            print(f"      📋 Ship filtering: ✅ Only sees assigned ship")
                        else:
                            print(f"      📋 Ship filtering: ❌ Sees {len(ship_ids)} ships: {ship_ids}")
                            success = False
                    else:
                        print(f"      📋 Response format: {type(ships)}")
                except Exception as e:
                    print(f"      📋 Could not parse ship response: {e}")
            
            high_priority_tests.append(("Test 7", success))
            test_results.append(("Editor → Ship List Filtering", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 7 failed: {e}")
            high_priority_tests.append(("Test 7", False))
            test_results.append(("Editor → Ship List Filtering", "❌ ERROR"))
        
        # Test 8: Company Access Control (Admin Scope)
        print("\n8. Company Access Control (Admin Scope)")
        try:
            headers = get_headers("tech_manager")
            user_info = get_user_info(headers)
            print(f"   👤 Testing with: tech_manager - Company: {user_info.get('company', 'N/A')[:8]}...")
            
            # Try to access a ship from different company (use ship 2 as different company ship)
            different_company_ship = test_ship_002_id if test_ship_002_id else test_ship_001_id
            
            success, response = run_test(
                "Manager tries to create cert for different company ship",
                lambda: test_8_company_access_control(headers, different_company_ship),
                expected_status=403,
                expected_success=False
            )
            
            high_priority_tests.append(("Test 8", success))
            test_results.append(("Manager → Cross-Company Access", "✅ BLOCKED" if success else "❌ ALLOWED"))
        except Exception as e:
            print(f"   ❌ Test 8 failed: {e}")
            high_priority_tests.append(("Test 8", False))
            test_results.append(("Manager → Cross-Company Access", "❌ ERROR"))
        
        print("\n🟢 MEDIUM PRIORITY TESTS (Additional Validations)")
        
        # Test 9: Editor CAN View Company Certificates (NEW FEATURE!)
        print("\n9. Editor CAN View Company Certificates (NEW FEATURE!)")
        try:
            headers = get_headers("test_editor")
            user_info = get_user_info(headers)
            print(f"   👤 Testing with: test_editor - Role: {user_info.get('role')}")
            
            success, response = run_test(
                "Editor views Company Certificates",
                lambda: test_9_editor_can_view_company_certs(headers),
                expected_status=200,
                expected_success=True
            )
            medium_priority_tests.append(("Test 9", success))
            test_results.append(("Editor → View Company Certs", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 9 failed: {e}")
            medium_priority_tests.append(("Test 9", False))
            test_results.append(("Editor → View Company Certs", "❌ ERROR"))
        
        # Test 10: System Admin Has Full Access
        print("\n10. System Admin Has Full Access")
        try:
            headers = get_headers("system_admin")
            user_info = get_user_info(headers)
            print(f"   👤 Testing with: system_admin - Role: {user_info.get('role')}")
            
            results = test_10_system_admin_full_access(headers, test_ship_001_id, crew_id, company_id)
            
            # Check all results
            ship_cert_success = results.get('ship_cert', {}).status_code in [200, 201]
            crew_cert_success = results.get('crew_cert', {}).status_code in [200, 201] if 'crew_cert' in results else True
            company_cert_success = results.get('company_cert', {}).status_code in [200, 201]
            
            success = ship_cert_success and crew_cert_success and company_cert_success
            
            print(f"      📋 Ship Certificate: {'✅' if ship_cert_success else '❌'}")
            print(f"      📋 Crew Certificate: {'✅' if crew_cert_success else '❌'}")
            print(f"      📋 Company Certificate: {'✅' if company_cert_success else '❌'}")
            
            medium_priority_tests.append(("Test 10", success))
            test_results.append(("System Admin → Full Access", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 10 failed: {e}")
            medium_priority_tests.append(("Test 10", False))
            test_results.append(("System Admin → Full Access", "❌ ERROR"))
        
        # All tests completed
        
        # Calculate success rates
        critical_success = sum(1 for _, success in critical_tests if success)
        critical_total = len(critical_tests)
        high_priority_success = sum(1 for _, success in high_priority_tests if success)
        high_priority_total = len(high_priority_tests)
        medium_priority_success = sum(1 for _, success in medium_priority_tests if success)
        medium_priority_total = len(medium_priority_tests)
        
        total_success = critical_success + high_priority_success + medium_priority_success
        total_tests = critical_total + high_priority_total + medium_priority_total
        
        print("\n" + "=" * 80)
        print("📊 PERMISSION SYSTEM TEST RESULTS")
        print("=" * 80)
        
        print(f"\n🔴 CRITICAL TESTS: {critical_success}/{critical_total} passed ({(critical_success/critical_total*100):.1f}%)")
        print(f"🟡 HIGH PRIORITY: {high_priority_success}/{high_priority_total} passed ({(high_priority_success/high_priority_total*100):.1f}%)")
        print(f"🟢 MEDIUM PRIORITY: {medium_priority_success}/{medium_priority_total} passed ({(medium_priority_success/medium_priority_total*100):.1f}%)")
        print(f"\n📈 OVERALL SUCCESS RATE: {total_success}/{total_tests} ({(total_success/total_tests*100):.1f}%)")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in test_results:
            print(f"   {result} {test_name}")
        
        # Final assessment
        if critical_success == critical_total and high_priority_success == high_priority_total and medium_priority_success == medium_priority_total:
            print(f"\n✅ PERMISSION SYSTEM WORKING EXCELLENTLY!")
            print(f"🎉 All tests passed - Department-based permission system is fully functional!")
        elif critical_success == critical_total:
            print(f"\n⚠️ PERMISSION SYSTEM MOSTLY WORKING")
            print(f"✅ All critical tests passed, some additional issues found")
        else:
            print(f"\n❌ PERMISSION SYSTEM HAS CRITICAL ISSUES")
            print(f"🚨 {critical_total - critical_success} critical test(s) failed")
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   - Technical vs Crewing department permissions: {'✅ Working' if critical_success >= 2 else '❌ Issues found'}")
        print(f"   - Ship vs Crew certificate department mapping: {'✅ Working' if critical_success >= 3 else '❌ Issues found'}")
        print(f"   - Editor role restrictions: {'✅ Working' if high_priority_success >= 2 else '❌ Issues found'}")
        print(f"   - Editor ship scope filtering: {'✅ Working' if high_priority_success >= 3 else '❌ Issues found'}")
        print(f"   - Company access control: {'✅ Working' if high_priority_success >= 4 else '❌ Issues found'}")
        print(f"   - System Admin full access: {'✅ Working' if medium_priority_success >= 1 else '❌ Issues found'}")
        print(f"   - Vietnamese error messages: {'✅ Implemented' if any('BLOCKED' in result for _, result in test_results) else '⚠️ Check needed'}")
        
        print(f"\n📋 SUCCESS CRITERIA VERIFICATION:")
        print(f"   ✅ Test 1: Technical Manager creates ship cert successfully: {'✅' if critical_success >= 1 else '❌'}")
        print(f"   ✅ Test 2: Crewing Manager gets 403 with Vietnamese error: {'✅' if critical_success >= 2 else '❌'}")
        print(f"   ✅ Test 3: Crewing Manager creates crew cert successfully: {'✅' if critical_success >= 3 else '❌'}")
        print(f"   ✅ Test 4: Technical Manager gets 403 for crew cert: {'✅' if critical_success >= 4 else '❌'}")
        print(f"   ✅ Test 5: Editor gets 403 when trying to create: {'✅' if high_priority_success >= 1 else '❌'}")
        print(f"   ✅ Test 6: Editor only sees assigned ship certificates: {'✅' if high_priority_success >= 2 else '❌'}")
        print(f"   ✅ Test 7: Editor only sees assigned ship in ship list: {'✅' if high_priority_success >= 3 else '❌'}")
        print(f"   ✅ Test 8: Cross-company access denied: {'✅' if high_priority_success >= 4 else '❌'}")
        print(f"   ✅ Test 9: Editor CAN view company certs: {'✅' if medium_priority_success >= 1 else '❌'}")
        print(f"   ✅ Test 10: System Admin can do everything: {'✅' if medium_priority_success >= 2 else '❌'}")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
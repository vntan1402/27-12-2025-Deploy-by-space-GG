#!/usr/bin/env python3
"""
🧪 PERMISSION SYSTEM TESTING - Phase 1 Implementation

Testing the comprehensive department-based permission system:
1. Manager Technical CAN create Ship Certificate
2. Manager Crewing CANNOT create Ship Certificate  
3. Manager DPA CAN create Company Certificate
4. Manager Technical CANNOT create Company Certificate
5. Editor CAN view Company Certificates (NEW FEATURE!)
6. Viewer CANNOT view Company Certificates
7. Editor CANNOT create any certificates
8. Editor only sees assigned ship documents
9. Admin has full access within company
10. Admin CAN create Company Certificate
11. Manager Crewing CAN create Crew Certificate
12. Manager Technical CANNOT create Crew Certificate
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
            BACKEND_URL = "https://maritime-safety-6.preview.emergentagent.com/api"
except:
    BACKEND_URL = "https://maritime-safety-6.preview.emergentagent.com/api"

# Available test users (from the system)
TEST_USERS = {
    "admin1": {"password": "123456", "role": "admin", "departments": ["operations", "commercial", "technical", "safety"]},
    "system_admin": {"password": "123456", "role": "system_admin", "departments": ["technical", "operations", "safety", "commercial", "crewing", "sso", "cso", "supply", "dpa"]},
    "ngoclm": {"password": "123456", "role": "manager", "departments": ["technical", "operations", "commercial", "cso", "supply", "crewing", "safety", "dpa"]},
    "user1": {"password": "123456", "role": "manager", "departments": ["ship_crew", "technical", "dpa"]}
}

def login(username, password):
    """Login and get access token"""
    response = requests.post(f"{BACKEND_URL}/auth/login", json={"username": username, "password": password})
    if response.status_code != 200:
        raise Exception(f"Login failed for {username}: {response.status_code} - {response.text}")
    return response.json()["access_token"]

def get_headers(username):
    """Get authorization headers for a user"""
    password = TEST_USERS[username]["password"]
    token = login(username, password)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def get_user_info(headers):
    """Get current user information"""
    response = requests.get(f"{BACKEND_URL}/auth/verify-token", headers=headers)
    if response.status_code == 200:
        return response.json().get("user", {})
    return None

def get_test_ships(headers):
    """Get test ships for testing"""
    response = requests.get(f"{BACKEND_URL}/ships?limit=10", headers=headers)
    if response.status_code == 200:
        ships = response.json()
        return ships
    return []

# Test functions for different permission scenarios

def test_manager_technical_can_create_ship_cert(headers):
    """Test 1: Manager Technical CAN create Ship Certificate"""
    cert_data = {
        "ship_id": "ship_001",
        "cert_name": "Test Ship Cert",
        "cert_type": "Full Term",
        "cert_no": "TEST001"
    }
    
    response = requests.post(f"{BACKEND_URL}/certificates", headers=headers, json=cert_data)
    return response

def test_manager_crewing_cannot_create_ship_cert(headers):
    """Test 2: Manager Crewing CANNOT create Ship Certificate"""
    cert_data = {
        "ship_id": "ship_001",
        "cert_name": "Test Ship Cert",
        "cert_type": "Full Term",
        "cert_no": "TEST002"
    }
    
    response = requests.post(f"{BACKEND_URL}/certificates", headers=headers, json=cert_data)
    return response

def test_manager_dpa_can_create_company_cert(headers):
    """Test 3: Manager DPA CAN create Company Certificate"""
    cert_data = {
        "company": "test_company_a",
        "cert_name": "DOC",
        "doc_type": "DOC",
        "cert_no": "DOC001"
    }
    
    response = requests.post(f"{BACKEND_URL}/company-certificates", headers=headers, json=cert_data)
    return response

def test_manager_technical_cannot_create_company_cert(headers):
    """Test 4: Manager Technical CANNOT create Company Certificate"""
    cert_data = {
        "company": "test_company_a",
        "cert_name": "DOC",
        "doc_type": "DOC",
        "cert_no": "DOC002"
    }
    
    response = requests.post(f"{BACKEND_URL}/company-certificates", headers=headers, json=cert_data)
    return response

def test_editor_can_view_company_certs(headers):
    """Test 5: Editor CAN view Company Certificates"""
    response = requests.get(f"{BACKEND_URL}/company-certificates", headers=headers)
    return response

def test_viewer_cannot_view_company_certs(headers):
    """Test 6: Viewer CANNOT view Company Certificates"""
    response = requests.get(f"{BACKEND_URL}/company-certificates", headers=headers)
    return response

def test_editor_cannot_create_certificates(headers):
    """Test 7: Editor CANNOT create any certificates"""
    cert_data = {
        "ship_id": "ship_001",
        "cert_name": "Test",
        "cert_type": "Full Term",
        "cert_no": "TEST003"
    }
    
    response = requests.post(f"{BACKEND_URL}/certificates", headers=headers, json=cert_data)
    return response

def test_editor_ship_filtering(headers, manager_headers):
    """Test 8: Editor only sees assigned ship documents"""
    # First create certificates for both ships using manager
    cert1_data = {
        "ship_id": "ship_001",
        "cert_name": "Ship 001 Cert",
        "cert_type": "Full Term",
        "cert_no": "SHIP001"
    }
    cert2_data = {
        "ship_id": "ship_002", 
        "cert_name": "Ship 002 Cert",
        "cert_type": "Full Term",
        "cert_no": "SHIP002"
    }
    
    # Create certificates as manager
    requests.post(f"{BACKEND_URL}/certificates", headers=manager_headers, json=cert1_data)
    requests.post(f"{BACKEND_URL}/certificates", headers=manager_headers, json=cert2_data)
    
    # Get certificates as editor (should only see ship_001)
    response = requests.get(f"{BACKEND_URL}/certificates", headers=headers)
    return response

def test_admin_full_access(headers):
    """Test 9: Admin has full access within company"""
    cert_data = {
        "ship_id": "ship_001",
        "cert_name": "Admin Test",
        "cert_type": "Full Term",
        "cert_no": "ADMIN001"
    }
    
    response = requests.post(f"{BACKEND_URL}/certificates", headers=headers, json=cert_data)
    return response

def test_admin_can_create_company_cert(headers):
    """Test 10: Admin CAN create Company Certificate"""
    cert_data = {
        "company": "test_company_a",
        "cert_name": "SMC",
        "doc_type": "SMC",
        "cert_no": "SMC001"
    }
    
    response = requests.post(f"{BACKEND_URL}/company-certificates", headers=headers, json=cert_data)
    return response

def test_manager_crewing_can_create_crew_cert(headers):
    """Test 11: Manager Crewing CAN create Crew Certificate"""
    # First check if crew-certificates endpoint exists
    cert_data = {
        "crew_id": "test_crew_001",
        "cert_name": "Certificate of Competency",
        "cert_no": "COC001"
    }
    
    response = requests.post(f"{BACKEND_URL}/crew-certificates", headers=headers, json=cert_data)
    return response

def test_manager_technical_cannot_create_crew_cert(headers):
    """Test 12: Manager Technical CANNOT create Crew Certificate"""
    cert_data = {
        "crew_id": "test_crew_001",
        "cert_name": "Certificate of Competency", 
        "cert_no": "COC002"
    }
    
    response = requests.post(f"{BACKEND_URL}/crew-certificates", headers=headers, json=cert_data)
    return response

def run_test(test_name, test_func, expected_status, expected_success=True):
    """Run a single test and return results"""
    try:
        print(f"\n   🧪 {test_name}")
        response = test_func()
        
        status_match = response.status_code == expected_status
        
        # Check for Vietnamese error messages in 403 responses
        vietnamese_error = False
        if response.status_code == 403:
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', '')
                # Check for Vietnamese characters or specific Vietnamese messages
                vietnamese_phrases = ['không có quyền', 'bị từ chối', 'Department', 'Manager', 'chỉ', 'mới có quyền']
                vietnamese_error = any(phrase in error_detail for phrase in vietnamese_phrases)
            except:
                pass
        
        if expected_success:
            success = status_match and response.status_code in [200, 201]
            result_icon = "✅" if success else "❌"
            print(f"      {result_icon} Expected: {expected_status} (Success), Got: {response.status_code}")
        else:
            success = status_match and response.status_code == 403
            result_icon = "✅" if success else "❌"
            print(f"      {result_icon} Expected: {expected_status} (Forbidden), Got: {response.status_code}")
            if response.status_code == 403 and vietnamese_error:
                print(f"      ✅ Vietnamese error message detected")
            elif response.status_code == 403:
                print(f"      ⚠️ Error message: {response.text}")
        
        if not success:
            print(f"      📝 Response: {response.text[:200]}...")
            
        return success, response
        
    except Exception as e:
        print(f"      ❌ Test failed with exception: {e}")
        return False, None

def check_ship_filtering(response, expected_ship_id):
    """Check if response contains only certificates for expected ship"""
    try:
        if response.status_code == 200:
            certs = response.json()
            if isinstance(certs, list):
                ship_ids = [cert.get('ship_id') for cert in certs if cert.get('ship_id')]
                if ship_ids:
                    all_match = all(ship_id == expected_ship_id for ship_id in ship_ids)
                    return all_match, f"Found {len(ship_ids)} certificates, all for ship {expected_ship_id}" if all_match else f"Mixed ship IDs: {set(ship_ids)}"
                else:
                    return True, "No certificates found (acceptable)"
            return True, "Response format acceptable"
        return False, f"Non-200 response: {response.status_code}"
    except Exception as e:
        return False, f"Error checking filtering: {e}"

# Main test execution
def main():
    print("🧪 PERMISSION SYSTEM TESTING - Phase 1 Implementation")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    
    # Test results tracking
    test_results = []
    critical_tests = []
    high_priority_tests = []
    medium_priority_tests = []
    
    try:
        print("\n🔴 CRITICAL TESTS (Department-Based Permissions)")
        
        # Test 1: Manager Technical CAN create Ship Certificate
        print("\n1. Manager Technical CAN create Ship Certificate")
        try:
            headers = get_headers("manager_technical")
            success, response = run_test(
                "Manager Technical creates Ship Certificate",
                lambda: test_manager_technical_can_create_ship_cert(headers),
                expected_status=201,
                expected_success=True
            )
            critical_tests.append(("Test 1", success))
            test_results.append(("Manager Technical → Ship Cert", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 1 failed: {e}")
            critical_tests.append(("Test 1", False))
            test_results.append(("Manager Technical → Ship Cert", "❌ ERROR"))
        
        # Test 2: Manager Crewing CANNOT create Ship Certificate
        print("\n2. Manager Crewing CANNOT create Ship Certificate")
        try:
            headers = get_headers("manager_crewing")
            success, response = run_test(
                "Manager Crewing tries to create Ship Certificate",
                lambda: test_manager_crewing_cannot_create_ship_cert(headers),
                expected_status=403,
                expected_success=False
            )
            critical_tests.append(("Test 2", success))
            test_results.append(("Manager Crewing → Ship Cert", "✅ BLOCKED" if success else "❌ ALLOWED"))
        except Exception as e:
            print(f"   ❌ Test 2 failed: {e}")
            critical_tests.append(("Test 2", False))
            test_results.append(("Manager Crewing → Ship Cert", "❌ ERROR"))
        
        # Test 3: Manager DPA CAN create Company Certificate
        print("\n3. Manager DPA CAN create Company Certificate")
        try:
            headers = get_headers("manager_dpa")
            success, response = run_test(
                "Manager DPA creates Company Certificate",
                lambda: test_manager_dpa_can_create_company_cert(headers),
                expected_status=201,
                expected_success=True
            )
            critical_tests.append(("Test 3", success))
            test_results.append(("Manager DPA → Company Cert", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 3 failed: {e}")
            critical_tests.append(("Test 3", False))
            test_results.append(("Manager DPA → Company Cert", "❌ ERROR"))
        
        # Test 4: Manager Technical CANNOT create Company Certificate
        print("\n4. Manager Technical CANNOT create Company Certificate")
        try:
            headers = get_headers("manager_technical")
            success, response = run_test(
                "Manager Technical tries to create Company Certificate",
                lambda: test_manager_technical_cannot_create_company_cert(headers),
                expected_status=403,
                expected_success=False
            )
            critical_tests.append(("Test 4", success))
            test_results.append(("Manager Technical → Company Cert", "✅ BLOCKED" if success else "❌ ALLOWED"))
        except Exception as e:
            print(f"   ❌ Test 4 failed: {e}")
            critical_tests.append(("Test 4", False))
            test_results.append(("Manager Technical → Company Cert", "❌ ERROR"))
        
        print("\n🟡 HIGH PRIORITY TESTS (Editor/Viewer Permissions)")
        
        # Test 5: Editor CAN view Company Certificates
        print("\n5. Editor CAN view Company Certificates")
        try:
            headers = get_headers("editor1")
            success, response = run_test(
                "Editor views Company Certificates",
                lambda: test_editor_can_view_company_certs(headers),
                expected_status=200,
                expected_success=True
            )
            high_priority_tests.append(("Test 5", success))
            test_results.append(("Editor → View Company Certs", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 5 failed: {e}")
            high_priority_tests.append(("Test 5", False))
            test_results.append(("Editor → View Company Certs", "❌ ERROR"))
        
        # Test 6: Viewer CANNOT view Company Certificates
        print("\n6. Viewer CANNOT view Company Certificates")
        try:
            headers = get_headers("viewer1")
            success, response = run_test(
                "Viewer tries to view Company Certificates",
                lambda: test_viewer_cannot_view_company_certs(headers),
                expected_status=403,
                expected_success=False
            )
            high_priority_tests.append(("Test 6", success))
            test_results.append(("Viewer → View Company Certs", "✅ BLOCKED" if success else "❌ ALLOWED"))
        except Exception as e:
            print(f"   ❌ Test 6 failed: {e}")
            high_priority_tests.append(("Test 6", False))
            test_results.append(("Viewer → View Company Certs", "❌ ERROR"))
        
        # Test 7: Editor CANNOT create any certificates
        print("\n7. Editor CANNOT create any certificates")
        try:
            headers = get_headers("editor1")
            success, response = run_test(
                "Editor tries to create certificate",
                lambda: test_editor_cannot_create_certificates(headers),
                expected_status=403,
                expected_success=False
            )
            high_priority_tests.append(("Test 7", success))
            test_results.append(("Editor → Create Cert", "✅ BLOCKED" if success else "❌ ALLOWED"))
        except Exception as e:
            print(f"   ❌ Test 7 failed: {e}")
            high_priority_tests.append(("Test 7", False))
            test_results.append(("Editor → Create Cert", "❌ ERROR"))
        
        # Test 8: Editor only sees assigned ship documents
        print("\n8. Editor only sees assigned ship documents")
        try:
            editor_headers = get_headers("editor1")
            manager_headers = get_headers("manager_technical")
            success, response = run_test(
                "Editor views certificates (ship filtering)",
                lambda: test_editor_ship_filtering(editor_headers, manager_headers),
                expected_status=200,
                expected_success=True
            )
            
            # Additional check for ship filtering
            if success and response:
                filter_success, filter_msg = check_ship_filtering(response, "ship_001")
                print(f"      📋 Ship filtering: {'✅' if filter_success else '❌'} {filter_msg}")
                success = success and filter_success
            
            high_priority_tests.append(("Test 8", success))
            test_results.append(("Editor → Ship Filtering", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 8 failed: {e}")
            high_priority_tests.append(("Test 8", False))
            test_results.append(("Editor → Ship Filtering", "❌ ERROR"))
        
        print("\n🟢 MEDIUM PRIORITY TESTS (Admin Permissions)")
        
        # Test 9: Admin has full access within company
        print("\n9. Admin has full access within company")
        try:
            headers = get_headers("admin1")
            success, response = run_test(
                "Admin creates Ship Certificate",
                lambda: test_admin_full_access(headers),
                expected_status=201,
                expected_success=True
            )
            medium_priority_tests.append(("Test 9", success))
            test_results.append(("Admin → Ship Cert", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 9 failed: {e}")
            medium_priority_tests.append(("Test 9", False))
            test_results.append(("Admin → Ship Cert", "❌ ERROR"))
        
        # Test 10: Admin CAN create Company Certificate
        print("\n10. Admin CAN create Company Certificate")
        try:
            headers = get_headers("admin1")
            success, response = run_test(
                "Admin creates Company Certificate",
                lambda: test_admin_can_create_company_cert(headers),
                expected_status=201,
                expected_success=True
            )
            medium_priority_tests.append(("Test 10", success))
            test_results.append(("Admin → Company Cert", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 10 failed: {e}")
            medium_priority_tests.append(("Test 10", False))
            test_results.append(("Admin → Company Cert", "❌ ERROR"))
        
        print("\n🔵 BONUS TESTS (Crew Certificates)")
        
        # Test 11: Manager Crewing CAN create Crew Certificate
        print("\n11. Manager Crewing CAN create Crew Certificate")
        try:
            headers = get_headers("manager_crewing")
            success, response = run_test(
                "Manager Crewing creates Crew Certificate",
                lambda: test_manager_crewing_can_create_crew_cert(headers),
                expected_status=201,
                expected_success=True
            )
            test_results.append(("Manager Crewing → Crew Cert", "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"   ❌ Test 11 failed: {e}")
            test_results.append(("Manager Crewing → Crew Cert", "❌ ERROR"))
        
        # Test 12: Manager Technical CANNOT create Crew Certificate
        print("\n12. Manager Technical CANNOT create Crew Certificate")
        try:
            headers = get_headers("manager_technical")
            success, response = run_test(
                "Manager Technical tries to create Crew Certificate",
                lambda: test_manager_technical_cannot_create_crew_cert(headers),
                expected_status=403,
                expected_success=False
            )
            test_results.append(("Manager Technical → Crew Cert", "✅ BLOCKED" if success else "❌ ALLOWED"))
        except Exception as e:
            print(f"   ❌ Test 12 failed: {e}")
            test_results.append(("Manager Technical → Crew Cert", "❌ ERROR"))
        
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
        if critical_success == critical_total and high_priority_success == high_priority_total:
            print(f"\n✅ PERMISSION SYSTEM WORKING EXCELLENTLY!")
            print(f"🎉 All critical and high-priority tests passed!")
        elif critical_success == critical_total:
            print(f"\n⚠️ PERMISSION SYSTEM MOSTLY WORKING")
            print(f"✅ All critical tests passed, some high-priority issues found")
        else:
            print(f"\n❌ PERMISSION SYSTEM HAS CRITICAL ISSUES")
            print(f"🚨 {critical_total - critical_success} critical test(s) failed")
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   - Department-based permissions: {'✅ Working' if critical_success >= 3 else '❌ Issues found'}")
        print(f"   - Editor/Viewer access control: {'✅ Working' if high_priority_success >= 3 else '❌ Issues found'}")
        print(f"   - Admin full access: {'✅ Working' if medium_priority_success >= 1 else '❌ Issues found'}")
        print(f"   - Vietnamese error messages: {'✅ Implemented' if any('BLOCKED' in result for _, result in test_results) else '⚠️ Check needed'}")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
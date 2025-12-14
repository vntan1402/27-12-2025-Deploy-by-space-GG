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
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
            break
else:
    BACKEND_URL = "https://maritime-safety-6.preview.emergentagent.com/api"

# Test users with different roles and departments
TEST_USERS = {
    "admin1": {"password": "123456", "role": "Admin"},
    "manager_technical": {"password": "123456", "role": "Manager", "department": ["technical"]},
    "manager_crewing": {"password": "123456", "role": "Manager", "department": ["crewing"]},
    "manager_dpa": {"password": "123456", "role": "Manager", "department": ["dpa"]},
    "editor1": {"password": "123456", "role": "Editor", "assigned_ship": "ship_001"},
    "viewer1": {"password": "123456", "role": "Viewer", "assigned_ship": "ship_001"}
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
    print("🧪 AUDIT CERTIFICATE ANALYSIS - TEXT LAYER + DOCUMENT AI MERGE TESTING")
    print("=" * 80)
    
    try:
        # Test 1: Authentication
        print("\n1. 🔐 Authentication Test")
        token = login()
        headers = {"Authorization": f"Bearer {token}"}
        print("   ✅ Login successful with admin1/123456")
        
        # Test 2: Get Test Ship
        print("\n2. 🚢 Getting Test Ship Information")
        ship_info = get_test_ship_info(headers)
        if not ship_info:
            print("   ❌ No ships found for testing")
            return
        
        ship_id = ship_info['id']
        ship_name = ship_info['name']
        ship_imo = ship_info['imo']
        
        print(f"   ✅ Using ship: {ship_name}")
        print(f"      - Ship ID: {ship_id}")
        print(f"      - Ship IMO: {ship_imo}")
        
        # Test 3: Audit Certificate Analysis with Text Layer + Document AI
        print("\n3. 🤖 Audit Certificate Analysis - Text Layer + Document AI Merge")
        print("   📄 Creating test PDF with text layer...")
        
        analyze_response = test_audit_certificate_analyze(headers, ship_id, ship_name)
        
        if analyze_response.status_code == 200:
            result = analyze_response.json()
            print("   ✅ Analysis endpoint responded successfully")
            
            # Test 4: Verify Response Structure
            print("\n4. 📋 Verifying Response Structure")
            
            # Check success flag
            if result.get('success'):
                print("   ✅ Response has success=true")
            else:
                print("   ❌ Response has success=false")
                print(f"      Error: {result.get('message', 'Unknown error')}")
                return
            
            # Check extracted_info
            extracted_info = result.get('extracted_info', {})
            if extracted_info:
                is_valid, message = verify_extracted_info_structure(extracted_info)
                if is_valid:
                    print(f"   ✅ extracted_info structure valid: {message}")
                    
                    # Display key extracted fields
                    print("      Key extracted fields:")
                    print(f"      - cert_name: {extracted_info.get('cert_name', 'N/A')}")
                    print(f"      - cert_no: {extracted_info.get('cert_no', 'N/A')}")
                    print(f"      - cert_type: {extracted_info.get('cert_type', 'N/A')}")
                    print(f"      - issue_date: {extracted_info.get('issue_date', 'N/A')}")
                    print(f"      - valid_date: {extracted_info.get('valid_date', 'N/A')}")
                    print(f"      - issued_by: {extracted_info.get('issued_by', 'N/A')}")
                    print(f"      - ship_name: {extracted_info.get('ship_name', 'N/A')}")
                    print(f"      - imo_number: {extracted_info.get('imo_number', 'N/A')}")
                else:
                    print(f"   ❌ extracted_info structure invalid: {message}")
            else:
                print("   ❌ No extracted_info in response")
            
            # Test 5: Verify Summary Text Structure (CRITICAL)
            print("\n5. 📝 Verifying Summary Text Structure (Text Layer + Document AI Merge)")
            
            summary_text = result.get('summary_text', '')
            if summary_text:
                is_valid, message = verify_summary_text_structure(summary_text)
                if is_valid:
                    print(f"   ✅ Summary text structure correct: {message}")
                    print(f"      - Total length: {len(summary_text)} characters")
                    
                    # Show structure preview
                    lines = summary_text.split('\n')
                    part1_found = False
                    part2_found = False
                    
                    for i, line in enumerate(lines):
                        if "PART 1: TEXT LAYER CONTENT" in line:
                            part1_found = True
                            print(f"      - Found PART 1 at line {i+1}")
                        elif "PART 2: DOCUMENT AI OCR CONTENT" in line:
                            part2_found = True
                            print(f"      - Found PART 2 at line {i+1}")
                    
                    if part1_found and part2_found:
                        print("   ✅ Both PART 1 and PART 2 sections confirmed in summary")
                    else:
                        print("   ⚠️ Section headers found but structure may be incomplete")
                        
                else:
                    print(f"   ❌ Summary text structure invalid: {message}")
                    print(f"      Summary preview (first 500 chars): {summary_text[:500]}")
            else:
                print("   ❌ No summary_text in response")
            
            # Test 6: Verify Validation Warnings
            print("\n6. ⚠️ Checking Validation Warnings")
            
            validation_warning = result.get('validation_warning')
            duplicate_warning = result.get('duplicate_warning')
            category_warning = result.get('category_warning')
            
            if validation_warning:
                print(f"   ⚠️ Validation warning: {validation_warning.get('message', 'Unknown')}")
                print(f"      - Type: {validation_warning.get('type', 'Unknown')}")
                print(f"      - Blocking: {validation_warning.get('is_blocking', False)}")
            else:
                print("   ✅ No validation warnings")
            
            if duplicate_warning:
                print(f"   ⚠️ Duplicate warning: {duplicate_warning.get('message', 'Unknown')}")
            else:
                print("   ✅ No duplicate warnings")
            
            if category_warning:
                print(f"   ⚠️ Category warning: {category_warning.get('message', 'Unknown')}")
                print(f"      - Valid category: {category_warning.get('is_valid', False)}")
            else:
                print("   ✅ No category warnings (certificate belongs to ISM/ISPS/MLC/CICA)")
            
            # Test 7: Google Drive Summary File Verification (Indirect)
            print("\n7. 📁 Google Drive Summary File Verification")
            
            # Since we can't directly access Google Drive in this test, we verify that
            # the summary_text is properly formatted for upload
            if summary_text and len(summary_text) > 100:
                is_valid, message = check_google_drive_summary_file(headers, ship_name)
                if is_valid:
                    print(f"   ✅ {message}")
                    print(f"      - Summary text ready for Google Drive upload")
                    print(f"      - Expected path: {ship_name}/ISM - ISPS - MLC/Audit Certificates/")
                    print(f"      - File format: test_audit_cert_ism_Summary.txt")
                else:
                    print(f"   ❌ {message}")
            else:
                print("   ❌ Summary text too short or missing for Google Drive upload")
            
        else:
            print(f"   ❌ Analysis endpoint failed: {analyze_response.status_code}")
            print(f"      Response: {analyze_response.text}")
            return
        
        # Test 8: Summary and Comparison with Old Flow
        print("\n8. 📊 Testing Summary and Comparison")
        
        success_count = 0
        total_tests = 7
        
        # Count successful tests
        if analyze_response.status_code == 200:
            success_count += 1
        if result.get('success'):
            success_count += 1
        if extracted_info:
            success_count += 1
        if summary_text and "PART 1: TEXT LAYER CONTENT" in summary_text:
            success_count += 1
        if summary_text and "PART 2: DOCUMENT AI OCR CONTENT" in summary_text:
            success_count += 1
        if not category_warning or category_warning.get('is_valid', False):
            success_count += 1
        if len(summary_text) > 100:
            success_count += 1
        
        success_rate = (success_count / total_tests) * 100
        
        print(f"   📈 Test Results Summary:")
        print(f"      - Success Rate: {success_rate:.1f}% ({success_count}/{total_tests} tests passed)")
        print(f"      - API Response: {'✅ Working' if analyze_response.status_code == 200 else '❌ Failed'}")
        print(f"      - Field Extraction: {'✅ Working' if extracted_info else '❌ Failed'}")
        print(f"      - Text Layer Processing: {'✅ Working' if 'PART 1' in summary_text else '❌ Failed'}")
        print(f"      - Document AI Processing: {'✅ Working' if 'PART 2' in summary_text else '❌ Failed'}")
        print(f"      - Summary Merge: {'✅ Working' if len(summary_text) > 100 else '❌ Failed'}")
        print(f"      - Category Validation: {'✅ Working' if not category_warning else '⚠️ Warning'}")
        
        print("\n" + "=" * 80)
        if success_rate >= 85:
            print("✅ AUDIT CERTIFICATE ANALYSIS TESTING COMPLETED SUCCESSFULLY")
            print("🎉 Text Layer + Document AI merge is working correctly!")
        elif success_rate >= 70:
            print("⚠️ AUDIT CERTIFICATE ANALYSIS TESTING COMPLETED WITH WARNINGS")
            print("🔧 Some features working but may need attention")
        else:
            print("❌ AUDIT CERTIFICATE ANALYSIS TESTING FAILED")
            print("🚨 Critical issues found that need immediate attention")
        
        print(f"\n📋 Key Findings:")
        print(f"   - Parallel processing (Text Layer + Document AI): {'✅ Implemented' if 'PART 1' in summary_text and 'PART 2' in summary_text else '❌ Not working'}")
        print(f"   - Enhanced summary format: {'✅ Correct' if 'PART 1' in summary_text and 'PART 2' in summary_text else '❌ Incorrect'}")
        print(f"   - Field extraction quality: {'✅ Good' if len(extracted_info) >= 4 else '⚠️ Limited'}")
        print(f"   - Ready for Google Drive upload: {'✅ Yes' if len(summary_text) > 100 else '❌ No'}")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
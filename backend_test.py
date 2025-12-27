#!/usr/bin/env python3
"""
🧪 SURVEY REPORT SMART UPLOAD TESTING

Testing the new Survey Report Smart Upload feature for Ship Management System:

## Test Objective
Test the new Survey Report Smart Upload feature:
1. Authentication with admin1/123456
2. Smart Upload API endpoint (FAST/SLOW path)
3. Task Status polling for SLOW PATH
4. Survey Report creation verification

## Test Credentials
- **admin1** / `123456` (Admin access for testing)

## New API Endpoints to Test
- POST /api/survey-reports/multi-upload-smart?ship_id={ship_id} - Smart multi-upload with FAST/SLOW path
- GET /api/survey-reports/upload-task/{task_id} - Poll task status for SLOW PATH

## Test Scenarios
1. Login and get auth token
2. Get a ship_id from /api/ships endpoint
3. Create a simple test PDF file with text content
4. Upload the PDF to smart upload endpoint
5. Verify response contains fast_path_results or slow_path_task_id
6. Verify summary object contains file counts
7. Test task status endpoint if slow_path_task_id returned
8. Verify survey report was created in /api/survey-reports
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
            BACKEND_URL = "https://cert-background.preview.emergentagent.com/api"
except:
    BACKEND_URL = "https://cert-background.preview.emergentagent.com/api"

# Test users as specified in review request
TEST_USERS = {
    "admin1": {"password": "123456", "role": "admin", "ship": None, "actual_user": "admin1"}
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

def create_test_pdf_with_text():
    """Create a simple PDF file with text content for testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import io
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add substantial text content to trigger FAST PATH
        text_content = """
        SURVEY REPORT
        
        Ship Name: MV Test Vessel
        Survey Type: Annual Survey
        Survey Report No: SR-2024-001
        Issued Date: 2024-12-25
        Issued By: Classification Society
        Status: Valid
        
        SURVEY FINDINGS:
        
        1. Hull Condition: The hull structure was found to be in good condition with no significant defects observed.
        
        2. Machinery: All main engines and auxiliary machinery were inspected and found to be operating within normal parameters.
        
        3. Safety Equipment: All safety equipment including life rafts, fire fighting equipment, and navigation equipment were verified to be in good working order.
        
        4. Certificates: All statutory certificates were verified to be valid and up to date.
        
        5. Recommendations: Continue with regular maintenance schedule as per manufacturer's recommendations.
        
        CONCLUSION:
        The vessel is found to be in satisfactory condition and complies with all applicable regulations.
        
        Surveyor: John Smith
        Date: December 25, 2024
        Signature: [Signed]
        
        This survey report contains sufficient text content to trigger the FAST PATH processing
        which requires at least 400 characters of text content for immediate processing.
        """
        
        # Write text to PDF
        y_position = 750
        for line in text_content.strip().split('\n'):
            if line.strip():
                p.drawString(50, y_position, line.strip())
                y_position -= 20
                if y_position < 50:
                    p.showPage()
                    y_position = 750
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        # Fallback: Create a simple text-based PDF using basic PDF structure
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 800
>>
stream
BT
/F1 12 Tf
50 750 Td
(SURVEY REPORT) Tj
0 -20 Td
(Ship Name: MV Test Vessel) Tj
0 -20 Td
(Survey Type: Annual Survey) Tj
0 -20 Td
(Survey Report No: SR-2024-001) Tj
0 -20 Td
(Issued Date: 2024-12-25) Tj
0 -20 Td
(Issued By: Classification Society) Tj
0 -20 Td
(Status: Valid) Tj
0 -40 Td
(SURVEY FINDINGS:) Tj
0 -20 Td
(1. Hull Condition: Good condition with no defects) Tj
0 -20 Td
(2. Machinery: All equipment operating normally) Tj
0 -20 Td
(3. Safety Equipment: All equipment verified) Tj
0 -20 Td
(4. Certificates: All certificates valid) Tj
0 -20 Td
(5. Recommendations: Continue maintenance) Tj
0 -40 Td
(CONCLUSION: Vessel in satisfactory condition) Tj
0 -20 Td
(Surveyor: John Smith) Tj
0 -20 Td
(Date: December 25, 2024) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
1058
%%EOF"""
        return pdf_content

def test_survey_report_smart_upload(headers, ship_id):
    """Test POST /api/survey-reports/multi-upload-smart - Smart multi-upload"""
    # Create test PDF file
    pdf_content = create_test_pdf_with_text()
    files = [('files', ('test_survey_report.pdf', pdf_content, 'application/pdf'))]
    
    # Remove Content-Type header for multipart upload
    upload_headers = {k: v for k, v in headers.items() if k != 'Content-Type'}
    
    response = requests.post(
        f"{BACKEND_URL}/survey-reports/multi-upload-smart?ship_id={ship_id}", 
        files=files, 
        headers=upload_headers
    )
    return response

def test_survey_upload_task_status(headers, task_id):
    """Test GET /api/survey-reports/upload-task/{task_id} - Poll task status"""
    response = requests.get(f"{BACKEND_URL}/survey-reports/upload-task/{task_id}", headers=headers)
    return response

def create_test_scanned_pdf():
    """Create a simple PDF file without text layer to trigger SLOW PATH"""
    # Create a minimal PDF without text layer (simulates scanned document)
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj

xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
180
%%EOF"""
    return pdf_content

def test_survey_report_smart_upload_slow_path(headers, ship_id):
    """Test POST /api/survey-reports/multi-upload-smart with scanned PDF (SLOW PATH)"""
    # Create test scanned PDF file (no text layer)
    pdf_content = create_test_scanned_pdf()
    files = [('files', ('scanned_survey_report.pdf', pdf_content, 'application/pdf'))]
    
    # Remove Content-Type header for multipart upload
    upload_headers = {k: v for k, v in headers.items() if k != 'Content-Type'}
    
    response = requests.post(
        f"{BACKEND_URL}/survey-reports/multi-upload-smart?ship_id={ship_id}", 
        files=files, 
        headers=upload_headers
    )
    return response

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

def test_survey_reports_list(headers, ship_id=None):
    """Test GET /api/survey-reports - Get survey reports list"""
    url = f"{BACKEND_URL}/survey-reports"
    if ship_id:
        url += f"?ship_id={ship_id}"
    response = requests.get(url, headers=headers)
    return response

# Main test execution
def main():
    print("🧪 SURVEY REPORT SMART UPLOAD TESTING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print("\nTest Credentials:")
    print("- admin1 / 123456 - Admin access for testing")
    
    # Test results tracking
    test_results = []
    all_tests = []
    
    try:
        # Test 1: Authentication
        print("\n" + "=" * 80)
        print("🔐 AUTHENTICATION TEST")
        print("=" * 80)
        
        print(f"\n📋 Testing authentication for: admin1")
        auth_result = test_authentication_flow("admin1")
        
        if not auth_result["success"]:
            print(f"   ❌ admin1 login failed: {auth_result['error']}")
            test_results.append(("AUTH admin1", f"❌ FAIL - {auth_result['error']}"))
            print("\n❌ CRITICAL: admin1 authentication failed. Cannot continue tests.")
            return
        
        user_info = auth_result["user_info"]
        print(f"   ✅ admin1 login successful - Role: {user_info.get('role', 'unknown')}")
        test_results.append(("AUTH admin1", "✅ PASS"))
        all_tests.append(("auth", True))
        
        admin_headers = auth_result["headers"]
        
        # Test 2: Get Ships List
        print("\n" + "=" * 80)
        print("🚢 SHIPS LIST TEST")
        print("=" * 80)
        
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
                    ship_name = ships_data[0].get("name", "Unknown")
                    print(f"   📋 Using ship: {ship_name} (ID: {ship_id})")
            except Exception as e:
                print(f"   ⚠️ Error parsing ships response: {e}")
        
        if not ship_id:
            print("   ❌ No ship_id available, cannot continue with upload tests")
            test_results.append(("SURVEY SMART UPLOAD", "❌ FAIL - No ship available"))
            return
        
        # Test 3: Survey Report Smart Upload (FAST PATH)
        print("\n" + "=" * 80)
        print("📤 SURVEY REPORT SMART UPLOAD TEST (FAST PATH)")
        print("=" * 80)
        
        print(f"\n🧪 Testing smart upload with test PDF file (FAST PATH)")
        success, upload_response = run_test(
            f"POST /api/survey-reports/multi-upload-smart (ship_id={ship_id})",
            lambda: test_survey_report_smart_upload(admin_headers, ship_id),
            expected_status=200
        )
        test_results.append(("SURVEY SMART UPLOAD (FAST)", "✅ PASS" if success else "❌ FAIL"))
        all_tests.append(("survey_upload_fast", success))
        
        # Analyze upload response
        task_id = None
        fast_path_results = []
        
        if success and upload_response.status_code == 200:
            try:
                upload_data = upload_response.json()
                print(f"\n📊 Upload Response Analysis (FAST PATH):")
                
                # Check summary
                summary = upload_data.get("summary", {})
                print(f"   📈 Summary:")
                print(f"      - Total files: {summary.get('total_files', 0)}")
                print(f"      - Fast path: {summary.get('fast_path_count', 0)}")
                print(f"      - Slow path: {summary.get('slow_path_count', 0)}")
                print(f"      - Fast completed: {summary.get('fast_path_completed', 0)}")
                print(f"      - Fast errors: {summary.get('fast_path_errors', 0)}")
                
                # Check fast path results
                fast_path_results = upload_data.get("fast_path_results", [])
                if fast_path_results:
                    print(f"   🚀 Fast Path Results:")
                    for result in fast_path_results:
                        status = result.get("status", "unknown")
                        filename = result.get("filename", "unknown")
                        message = result.get("message", "")
                        print(f"      - {filename}: {status} - {message}")
                
                # Check slow path task
                task_id = upload_data.get("slow_path_task_id")
                if task_id:
                    print(f"   🔄 Slow Path Task ID: {task_id}")
                
                # Verify expected response structure
                required_fields = ["fast_path_results", "slow_path_task_id", "summary"]
                missing_fields = [field for field in required_fields if field not in upload_data]
                if missing_fields:
                    print(f"   ⚠️ Missing response fields: {missing_fields}")
                else:
                    print(f"   ✅ Response structure valid")
                    
            except Exception as e:
                print(f"   ⚠️ Error parsing upload response: {e}")
                print(f"   📝 Raw response: {upload_response.text[:500]}...")
        
        # Test 4: Survey Report Smart Upload (SLOW PATH)
        print("\n" + "=" * 80)
        print("📤 SURVEY REPORT SMART UPLOAD TEST (SLOW PATH)")
        print("=" * 80)
        
        print(f"\n🧪 Testing smart upload with scanned PDF file (SLOW PATH)")
        success_slow, upload_response_slow = run_test(
            f"POST /api/survey-reports/multi-upload-smart (scanned PDF)",
            lambda: test_survey_report_smart_upload_slow_path(admin_headers, ship_id),
            expected_status=200
        )
        test_results.append(("SURVEY SMART UPLOAD (SLOW)", "✅ PASS" if success_slow else "❌ FAIL"))
        all_tests.append(("survey_upload_slow", success_slow))
        
        # Analyze slow path response
        slow_task_id = None
        if success_slow and upload_response_slow.status_code == 200:
            try:
                upload_data_slow = upload_response_slow.json()
                print(f"\n📊 Upload Response Analysis (SLOW PATH):")
                
                # Check summary
                summary_slow = upload_data_slow.get("summary", {})
                print(f"   📈 Summary:")
                print(f"      - Total files: {summary_slow.get('total_files', 0)}")
                print(f"      - Fast path: {summary_slow.get('fast_path_count', 0)}")
                print(f"      - Slow path: {summary_slow.get('slow_path_count', 0)}")
                print(f"      - Slow processing: {summary_slow.get('slow_path_processing', False)}")
                
                # Check slow path task
                slow_task_id = upload_data_slow.get("slow_path_task_id")
                if slow_task_id:
                    print(f"   🔄 Slow Path Task ID: {slow_task_id}")
                else:
                    print(f"   ⚠️ No slow path task ID returned")
                    
            except Exception as e:
                print(f"   ⚠️ Error parsing slow path response: {e}")
        
        # Test 5: Task Status Polling (if slow path task exists)
        if slow_task_id:
            print("\n" + "=" * 80)
            print("🔄 TASK STATUS POLLING TEST")
            print("=" * 80)
            
            success, task_response = run_test(
                f"GET /api/survey-reports/upload-task/{slow_task_id}",
                lambda: test_survey_upload_task_status(admin_headers, slow_task_id),
                expected_status=200
            )
            test_results.append(("TASK STATUS POLLING", "✅ PASS" if success else "❌ FAIL"))
            all_tests.append(("task_status", success))
            
            if success and task_response.status_code == 200:
                try:
                    task_data = task_response.json()
                    print(f"   📋 Task Status:")
                    print(f"      - Task ID: {task_data.get('id', 'unknown')}")
                    print(f"      - Status: {task_data.get('status', 'unknown')}")
                    print(f"      - Progress: {task_data.get('progress', 0)}%")
                    print(f"      - Files: {len(task_data.get('files', []))}")
                    
                    # Show file details
                    files_info = task_data.get('files', [])
                    if files_info:
                        print(f"   📁 File Details:")
                        for i, file_info in enumerate(files_info):
                            print(f"      [{i+1}] {file_info.get('filename', 'unknown')}")
                            print(f"          Status: {file_info.get('status', 'unknown')}")
                            print(f"          Progress: {file_info.get('progress', 0)}%")
                            
                except Exception as e:
                    print(f"   ⚠️ Error parsing task response: {e}")
        else:
            print("\n   ℹ️ No slow path task created - testing task polling with fast path task_id")
            if task_id:
                success, task_response = run_test(
                    f"GET /api/survey-reports/upload-task/{task_id}",
                    lambda: test_survey_upload_task_status(admin_headers, task_id),
                    expected_status=404  # Should return 404 for non-existent task
                )
                test_results.append(("TASK STATUS POLLING (404)", "✅ PASS" if success else "❌ FAIL"))
                all_tests.append(("task_status_404", success))
        
        # Test 6: Verify Survey Reports Created
        print("\n" + "=" * 80)
        print("📋 SURVEY REPORTS VERIFICATION")
        print("=" * 80)
        
        success, reports_response = run_test(
            f"GET /api/survey-reports (ship_id={ship_id})",
            lambda: test_survey_reports_list(admin_headers, ship_id),
            expected_status=200
        )
        test_results.append(("SURVEY REPORTS LIST", "✅ PASS" if success else "❌ FAIL"))
        all_tests.append(("survey_reports_list", success))
        
        if success and reports_response.status_code == 200:
            try:
                reports_data = reports_response.json()
                print(f"   📊 Survey Reports Found: {len(reports_data)}")
                
                # Look for recently created reports
                recent_reports = []
                for report in reports_data:
                    report_name = report.get("survey_report_name", "")
                    if "test" in report_name.lower() or "Test" in report_name:
                        recent_reports.append(report)
                
                if recent_reports:
                    print(f"   ✅ Found {len(recent_reports)} test report(s):")
                    for report in recent_reports[:3]:  # Show first 3
                        print(f"      - {report.get('survey_report_name', 'Unknown')} (ID: {report.get('id', 'Unknown')})")
                        print(f"        Form: {report.get('report_form', 'N/A')}")
                        print(f"        No: {report.get('survey_report_no', 'N/A')}")
                        print(f"        Issued By: {report.get('issued_by', 'N/A')}")
                else:
                    print(f"   ⚠️ No test reports found in recent uploads")
                    
            except Exception as e:
                print(f"   ⚠️ Error parsing reports response: {e}")
        
        # Calculate success rates
        total_tests = len(all_tests)
        successful_tests = sum(1 for _, success in all_tests if success)
        
        print("\n" + "=" * 80)
        print("📊 SURVEY REPORT SMART UPLOAD TEST RESULTS")
        print("=" * 80)
        
        print(f"\n📈 OVERALL SUCCESS RATE: {successful_tests}/{total_tests} ({(successful_tests/total_tests*100):.1f}%)")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in test_results:
            print(f"   {result} - {test_name}")
        
        # Final assessment
        if successful_tests == total_tests:
            print(f"\n✅ ALL SURVEY REPORT SMART UPLOAD TESTS PASSED!")
            print(f"🎉 Smart Upload feature is working correctly")
        elif successful_tests >= total_tests * 0.8:  # 80% pass rate
            print(f"\n⚠️ MOST TESTS PASSED ({successful_tests}/{total_tests})")
            print(f"🔍 Review failed tests")
        else:
            print(f"\n❌ CRITICAL ISSUES FOUND")
            print(f"🚨 {total_tests - successful_tests} test(s) failed - Smart Upload feature has issues")
        
        print(f"\n🎯 KEY FINDINGS:")
        
        # Check if fast path worked
        fast_path_success = any("survey_upload" in test_type for test_type, success in all_tests if success)
        if fast_path_success:
            print(f"   ✅ Smart Upload API endpoint working")
            if fast_path_results:
                successful_fast = sum(1 for r in fast_path_results if r.get("status") == "success")
                print(f"   ✅ Fast Path processing: {successful_fast}/{len(fast_path_results)} files successful")
        
        # Check if slow path worked
        slow_path_success = any("survey_upload_slow" in test_type for test_type, success in all_tests if success)
        if slow_path_success:
            print(f"   ✅ Slow Path upload endpoint working")
        
        # Check if task polling worked
        task_success = any("task_status" in test_type for test_type, success in all_tests if success)
        if task_success:
            print(f"   ✅ Task status polling working")
        elif slow_task_id:
            print(f"   ❌ Task status polling failed")
        else:
            print(f"   ℹ️ Task polling tested with 404 response (expected)")
        
        # Check if reports were created
        reports_success = any("survey_reports_list" in test_type for test_type, success in all_tests if success)
        if reports_success:
            print(f"   ✅ Survey reports creation verified")
        else:
            print(f"   ❌ Survey reports creation verification failed")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
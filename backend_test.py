import requests
import sys
import json
from datetime import datetime, timezone
import time

class ShipManagementAPITester:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.current_user = None
        self.test_ship_id = None
        self.company_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Remove Content-Type for file uploads
        if files:
            headers.pop('Content-Type', None)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self, username="admin", password="admin123"):
        """Test login and get token"""
        print(f"\n🔐 Testing Authentication with {username}/{password}")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            self.current_user = response.get('user', {})
            self.company_id = self.current_user.get('company')
            print(f"✅ Login successful, token obtained")
            print(f"   User: {response.get('user', {}).get('full_name')} ({response.get('user', {}).get('role')})")
            print(f"   Company: {self.company_id}")
            return True
        return False

    def test_user_management(self):
        """Test user management endpoints"""
        print(f"\n👥 Testing User Management")
        
        # Get users list
        success, users = self.run_test("Get Users", "GET", "users", 200)
        if not success:
            return False
        
        print(f"   Found {len(users)} users")
        
        # Test user registration
        test_user_data = {
            "username": f"test_user_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "role": "viewer",
            "department": "technical"
        }
        
        success, new_user = self.run_test(
            "Create User",
            "POST", 
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success:
            print(f"   Created user: {new_user.get('username')}")
            return True
        return False

    def test_permission_assignment(self):
        """Test permission assignment"""
        print(f"\n🔐 Testing Permission Assignment")
        
        # Get users first
        success, users = self.run_test("Get Users for Permissions", "GET", "users", 200)
        if not success or not users:
            return False
        
        # Test permission assignment
        permission_data = {
            "user_ids": [users[0]['id']] if users else [],
            "categories": ["certificates", "inspection_records"],
            "departments": ["technical", "operations"],
            "sensitivity_levels": ["public", "internal"],
            "permissions": ["read", "write"]
        }
        
        success, response = self.run_test(
            "Assign Permissions",
            "POST",
            "permissions/assign",
            200,
            data=permission_data
        )
        
        return success

    def test_ship_management(self):
        """Test ship management endpoints"""
        print(f"\n🚢 Testing Ship Management")
        
        # Create a test ship with required fields
        ship_data = {
            "name": f"Test Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "ship_type": "DNV GL",  # Changed from class_society to ship_type
            "flag": "Panama",
            "gross_tonnage": 50000.0,
            "deadweight": 75000.0,
            "built_year": 2020,
            "company": "Test Company"  # Added required company field
        }
        
        success, ship = self.run_test(
            "Create Ship",
            "POST",
            "ships",
            200,
            data=ship_data
        )
        
        if not success:
            return False
        
        ship_id = ship.get('id')
        print(f"   Created ship: {ship.get('name')} (ID: {ship_id})")
        
        # Get all ships
        success, ships = self.run_test("Get Ships", "GET", "ships", 200)
        if success:
            print(f"   Found {len(ships)} ships")
        
        # Get specific ship
        if ship_id:
            success, ship_detail = self.run_test(
                "Get Ship Detail",
                "GET",
                f"ships/{ship_id}",
                200
            )
            if success:
                print(f"   Retrieved ship details: {ship_detail.get('name')}")
        
        return success

    def test_certificate_management(self):
        """Test certificate management"""
        print(f"\n📜 Testing Certificate Management")
        
        # First get ships to create certificates for
        success, ships = self.run_test("Get Ships for Certificates", "GET", "ships", 200)
        if not success or not ships:
            print("   No ships available for certificate testing")
            return False
        
        ship_id = ships[0]['id']
        
        # Create a test certificate
        cert_data = {
            "ship_id": ship_id,
            "cert_name": "Safety Management Certificate",
            "cert_no": f"SMC{int(time.time())}",
            "issue_date": "2024-01-01T00:00:00Z",
            "valid_date": "2025-01-01T00:00:00Z",
            "category": "certificates",
            "sensitivity_level": "internal"
        }
        
        success, certificate = self.run_test(
            "Create Certificate",
            "POST",
            "certificates",
            200,
            data=cert_data
        )
        
        if not success:
            return False
        
        print(f"   Created certificate: {certificate.get('cert_name')}")
        
        # Get ship certificates
        success, certificates = self.run_test(
            "Get Ship Certificates",
            "GET",
            f"ships/{ship_id}/certificates",
            200
        )
        
        if success:
            print(f"   Found {len(certificates)} certificates for ship")
        
        return success

    def test_ai_features(self):
        """Test AI analysis and search features"""
        print(f"\n🤖 Testing AI Features")
        
        # First get certificates to analyze
        success, ships = self.run_test("Get Ships for AI", "GET", "ships", 200)
        if not success or not ships:
            print("   No ships available for AI testing")
            return False
        
        ship_id = ships[0]['id']
        success, certificates = self.run_test(
            "Get Certificates for AI",
            "GET",
            f"ships/{ship_id}/certificates",
            200
        )
        
        if not success or not certificates:
            print("   No certificates available for AI testing")
            return False
        
        cert_id = certificates[0]['id']
        
        # Test document analysis
        analysis_data = {
            "document_id": cert_id,
            "analysis_type": "summary"
        }
        
        success, analysis = self.run_test(
            "AI Document Analysis",
            "POST",
            "ai/analyze",
            200,
            data=analysis_data
        )
        
        if success:
            print(f"   AI Analysis completed")
            print(f"   Analysis result preview: {str(analysis.get('analysis', ''))[:100]}...")
        
        # Test smart search
        success, search_results = self.run_test(
            "AI Smart Search",
            "GET",
            "ai/search?query=safety certificate",
            200
        )
        
        if success:
            print(f"   Smart search completed")
            print(f"   Search result preview: {str(search_results.get('search_results', ''))[:100]}...")
        
        return success

    def test_file_upload(self):
        """Test file upload functionality"""
        print(f"\n📁 Testing File Upload")
        
        # Create a simple test image file
        import io
        from PIL import Image
        
        # Create a simple 100x100 red image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {'file': ('test_logo.png', img_bytes, 'image/png')}
        
        success, response = self.run_test(
            "Upload Logo",
            "POST",
            "upload/logo",
            200,
            files=files
        )
        
        if success:
            print(f"   Logo uploaded: {response.get('logo_url')}")
        
        return success

    def test_settings(self):
        """Test company settings"""
        print(f"\n⚙️ Testing Settings")
        
        # Get settings
        success, settings = self.run_test("Get Settings", "GET", "settings", 200)
        if success:
            print(f"   Current settings retrieved")
        
        # Update settings
        settings_data = {
            "company_name": "Test Maritime Company",
            "language_preference": "en"
        }
        
        success, updated_settings = self.run_test(
            "Update Settings",
            "POST",
            "settings",
            200,
            data=settings_data
        )
        
        if success:
            print(f"   Settings updated: {updated_settings.get('company_name')}")
        
        return success

    def test_enhanced_ship_creation_workflow(self):
        """Test enhanced Add New Ship workflow with Google Drive folder creation"""
        print(f"\n🚢 Testing Enhanced Add New Ship Workflow with Google Drive Integration")
        
        # Step 1: Verify user has proper company assignment
        if not self.company_id:
            print("❌ User not assigned to any company - cannot test company Google Drive")
            return False
        
        print(f"✅ User assigned to company: {self.company_id}")
        
        # Step 2: Check company Google Drive configuration
        success, gdrive_config = self.run_test(
            "Get Company Google Drive Config",
            "GET",
            f"companies/{self.company_id}/gdrive/config",
            200
        )
        
        if not success:
            print("❌ Company Google Drive not configured")
            return False
        
        print(f"✅ Company Google Drive configured")
        print(f"   Web App URL: {gdrive_config.get('config', {}).get('web_app_url', 'Not found')}")
        print(f"   Folder ID: {gdrive_config.get('config', {}).get('folder_id', 'Not found')}")
        
        # Step 3: Test ship creation with enhanced data
        ship_data = {
            "name": "Test Ship Integration",
            "imo": f"IMO{int(time.time())}",
            "flag": "Panama",
            "ship_type": "DNV GL",
            "gross_tonnage": 45000.0,
            "deadweight": 68000.0,
            "built_year": 2021,
            "ship_owner": "Test Maritime Holdings Ltd",
            "company": "Global Test Shipping Company"
        }
        
        success, ship = self.run_test(
            "Create Ship with Enhanced Data",
            "POST",
            "ships",
            200,
            data=ship_data
        )
        
        if not success:
            print("❌ Ship creation failed")
            return False
        
        self.test_ship_id = ship.get('id')
        print(f"✅ Ship created successfully: {ship.get('name')} (ID: {self.test_ship_id})")
        
        # Step 4: Test Google Drive folder creation endpoint
        folder_data = {
            "ship_name": ship.get('name'),
            "subfolders": [
                "Certificates",
                "Inspection Records", 
                "Survey Reports",
                "Drawings & Manuals",
                "Other Documents"
            ]
        }
        
        success, folder_result = self.run_test(
            "Create Ship Google Drive Folder",
            "POST",
            f"companies/{self.company_id}/gdrive/create-ship-folder",
            200,
            data=folder_data
        )
        
        if not success:
            print("❌ Google Drive folder creation failed")
            return False
        
        print(f"✅ Google Drive folder created successfully")
        print(f"   Ship Folder ID: {folder_result.get('ship_folder_id')}")
        print(f"   Subfolders Created: {folder_result.get('subfolders_created')}")
        print(f"   Subfolder IDs: {folder_result.get('subfolder_ids', {})}")
        
        # Step 5: Verify ship exists in database
        success, ship_detail = self.run_test(
            "Verify Ship in Database",
            "GET",
            f"ships/{self.test_ship_id}",
            200
        )
        
        if success:
            print(f"✅ Ship verified in database: {ship_detail.get('name')}")
            print(f"   Ship Owner: {ship_detail.get('ship_owner')}")
            print(f"   Company: {ship_detail.get('company')}")
        
        return success
    
    def test_google_drive_integration_details(self):
        """Test detailed Google Drive integration functionality"""
        print(f"\n📁 Testing Google Drive Integration Details")
        
        if not self.company_id:
            print("❌ No company ID available for testing")
            return False
        
        # Test 1: Company Google Drive Status
        success, status = self.run_test(
            "Get Company Google Drive Status",
            "GET",
            f"companies/{self.company_id}/gdrive/status",
            200
        )
        
        if success:
            print(f"✅ Google Drive Status: {status.get('status')}")
            print(f"   Message: {status.get('message', 'No message')}")
        
        # Test 2: Test Connection
        success, test_result = self.run_test(
            "Test Company Google Drive Connection",
            "POST",
            f"companies/{self.company_id}/gdrive/configure-proxy",
            200,
            data={"action": "test_connection"}
        )
        
        if success:
            print(f"✅ Google Drive connection test successful")
            print(f"   Result: {test_result.get('message', 'No message')}")
        
        # Test 3: Create folder with different subfolder combinations
        test_folder_data = {
            "ship_name": "Test Folder Structure Ship",
            "subfolders": [
                "Certificates",
                "Test Reports", 
                "Survey Reports",
                "Drawings & Manuals",
                "Other Documents"
            ]
        }
        
        success, folder_test = self.run_test(
            "Test Folder Structure Creation",
            "POST",
            f"companies/{self.company_id}/gdrive/create-ship-folder",
            200,
            data=test_folder_data
        )
        
        if success:
            print(f"✅ Test folder structure created")
            print(f"   Subfolders: {list(folder_test.get('subfolder_ids', {}).keys())}")
        
        return success
    
    def test_error_handling_scenarios(self):
        """Test error handling in ship creation and Google Drive integration"""
        print(f"\n⚠️ Testing Error Handling Scenarios")
        
        # Test 1: Ship creation without required fields
        invalid_ship_data = {
            "name": "",  # Empty name should fail
            "flag": "Panama"
        }
        
        success, error_response = self.run_test(
            "Create Ship with Invalid Data",
            "POST",
            "ships",
            422,  # Expect validation error
            data=invalid_ship_data
        )
        
        if success:
            print(f"✅ Validation error handled correctly")
        
        # Test 2: Google Drive folder creation without ship name
        if self.company_id:
            invalid_folder_data = {
                "ship_name": "",  # Empty ship name
                "subfolders": ["Certificates"]
            }
            
            success, error_response = self.run_test(
                "Create Folder with Invalid Data",
                "POST",
                f"companies/{self.company_id}/gdrive/create-ship-folder",
                400,  # Expect bad request
                data=invalid_folder_data
            )
            
            if success:
                print(f"✅ Google Drive validation error handled correctly")
        
        # Test 3: Access Google Drive for non-existent company
        fake_company_id = "non-existent-company-id"
        success, error_response = self.run_test(
            "Access Non-existent Company Google Drive",
            "GET",
            f"companies/{fake_company_id}/gdrive/config",
            404,  # Expect not found
        )
        
        if success:
            print(f"✅ Non-existent company error handled correctly")
        
        return True

def main():
    """Main test execution - Focus on Enhanced Add New Ship Workflow"""
    print("🚢 Enhanced Add New Ship Workflow Testing")
    print("=" * 60)
    print("Testing enhanced Add New Ship workflow with Google Drive folder creation")
    print("=" * 60)
    
    tester = ShipManagementAPITester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Run focused tests for the review request
    test_results = []
    
    # Core tests for the enhanced workflow
    test_results.append(("Enhanced Ship Creation Workflow", tester.test_enhanced_ship_creation_workflow()))
    test_results.append(("Google Drive Integration Details", tester.test_google_drive_integration_details()))
    test_results.append(("Error Handling Scenarios", tester.test_error_handling_scenarios()))
    
    # Additional supporting tests
    test_results.append(("Basic Ship Management", tester.test_ship_management()))
    test_results.append(("Certificate Management", tester.test_certificate_management()))
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 ENHANCED ADD NEW SHIP WORKFLOW TEST RESULTS")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:35} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Feature Tests: {passed_tests}/{total_tests}")
    
    # Summary of key findings
    print("\n" + "=" * 60)
    print("🔍 KEY FINDINGS SUMMARY")
    print("=" * 60)
    
    if tester.company_id:
        print(f"✅ User properly assigned to company: {tester.company_id}")
    else:
        print("❌ User not assigned to company - Google Drive integration cannot be tested")
    
    if tester.test_ship_id:
        print(f"✅ Test ship created successfully: {tester.test_ship_id}")
    else:
        print("❌ Ship creation failed")
    
    print("\n📋 REVIEW REQUEST REQUIREMENTS STATUS:")
    print("1. Authentication and Setup: ✅ TESTED")
    print("2. Enhanced Button Text: ⚠️ FRONTEND ONLY (not testable via API)")
    print("3. Ship Creation Workflow: ✅ TESTED")
    print("4. Google Drive Folder Creation: ✅ TESTED")
    print("5. Complete Integration: ✅ TESTED")
    
    if passed_tests == total_tests and tester.tests_passed == tester.tests_run:
        print("\n🎉 All enhanced Add New Ship workflow tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed - check detailed logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
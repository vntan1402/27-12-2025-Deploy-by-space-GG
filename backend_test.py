import requests
import sys
import json
from datetime import datetime, timezone
import time

class ShipManagementAPITester:
    def __init__(self, base_url="https://aicert-analyzer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None

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
            print(f"✅ Login successful, token obtained")
            print(f"   User: {response.get('user', {}).get('full_name')} ({response.get('user', {}).get('role')})")
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
        
        # Create a test ship
        ship_data = {
            "name": f"Test Ship {int(time.time())}",
            "imo_number": f"IMO{int(time.time())}",
            "class_society": "DNV GL",
            "flag": "Panama",
            "gross_tonnage": 50000.0,
            "deadweight": 75000.0,
            "built_year": 2020
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

def main():
    """Main test execution"""
    print("🚢 Ship Management System API Testing")
    print("=" * 50)
    
    tester = ShipManagementAPITester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Run all tests
    test_results = []
    
    test_results.append(("User Management", tester.test_user_management()))
    test_results.append(("Permission Assignment", tester.test_permission_assignment()))
    test_results.append(("Ship Management", tester.test_ship_management()))
    test_results.append(("Certificate Management", tester.test_certificate_management()))
    test_results.append(("Settings", tester.test_settings()))
    
    # Test file upload (requires PIL)
    try:
        test_results.append(("File Upload", tester.test_file_upload()))
    except ImportError:
        print("⚠️ Skipping file upload test (PIL not available)")
    
    # Test AI features (may take longer)
    try:
        test_results.append(("AI Features", tester.test_ai_features()))
    except Exception as e:
        print(f"⚠️ AI Features test failed: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Feature Tests: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests and tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
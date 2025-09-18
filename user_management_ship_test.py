import requests
import sys
import json
from datetime import datetime, timezone
import time

class UserManagementShipTester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.test_user_id = None
        self.test_ship_id = None
        self.test_company_id = None

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

    def test_authentication(self):
        """Test authentication with admin/admin123 credentials and verify Super Admin role"""
        print(f"\n🔐 Testing Authentication with admin/admin123")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            user_role = response.get('user', {}).get('role')
            
            print(f"✅ Login successful, token obtained")
            print(f"   User: {response.get('user', {}).get('full_name')} ({user_role})")
            
            # Verify Super Admin role
            if user_role == 'super_admin':
                print(f"✅ Super Admin role verified")
                return True
            else:
                print(f"❌ Expected super_admin role, got {user_role}")
                return False
        return False

    def test_get_users_with_ship_field(self):
        """Test GET /api/users - verify users list includes ship field"""
        print(f"\n👥 Testing GET /api/users - Ship Field Verification")
        
        success, users = self.run_test("Get Users List", "GET", "users", 200)
        if not success:
            return False
        
        print(f"   Found {len(users)} users")
        
        # Verify ship field is present in user responses
        ship_field_present = True
        users_with_ship = 0
        
        for user in users:
            if 'ship' not in user:
                print(f"❌ Ship field missing in user: {user.get('username', 'Unknown')}")
                ship_field_present = False
            else:
                print(f"   User {user.get('username')}: ship = {user.get('ship', 'None')}")
                if user.get('ship'):
                    users_with_ship += 1
        
        if ship_field_present:
            print(f"✅ Ship field present in all {len(users)} users")
            print(f"   Users with ship assigned: {users_with_ship}")
            return True
        else:
            print(f"❌ Ship field missing in some users")
            return False

    def test_get_companies(self):
        """Test GET /api/companies - verify companies data exists"""
        print(f"\n🏢 Testing GET /api/companies")
        
        success, companies = self.run_test("Get Companies", "GET", "companies", 200)
        if not success:
            return False
        
        print(f"   Found {len(companies)} companies")
        
        if companies:
            # Store first company ID for later use
            self.test_company_id = companies[0].get('id')
            print(f"   Sample company: {companies[0].get('name_en', 'Unknown')} (ID: {self.test_company_id})")
            
            # Verify company structure
            required_fields = ['id', 'name_vn', 'name_en', 'address_vn', 'address_en', 'tax_id']
            for field in required_fields:
                if field not in companies[0]:
                    print(f"❌ Required field '{field}' missing in company data")
                    return False
            
            print(f"✅ Company data structure verified")
            return True
        else:
            print(f"⚠️ No companies found - this may be expected for a new system")
            return True

    def test_get_ships(self):
        """Test GET /api/ships - verify ships data exists"""
        print(f"\n🚢 Testing GET /api/ships")
        
        success, ships = self.run_test("Get Ships", "GET", "ships", 200)
        if not success:
            return False
        
        print(f"   Found {len(ships)} ships")
        
        if ships:
            # Store first ship ID for later use
            self.test_ship_id = ships[0].get('id')
            print(f"   Sample ship: {ships[0].get('name', 'Unknown')} (ID: {self.test_ship_id})")
            
            # Verify ship structure
            required_fields = ['id', 'name', 'imo_number', 'class_society', 'flag']
            for field in required_fields:
                if field not in ships[0]:
                    print(f"❌ Required field '{field}' missing in ship data")
                    return False
            
            print(f"✅ Ship data structure verified")
            return True
        else:
            print(f"⚠️ No ships found - creating test ship for user assignment testing")
            return self.create_test_ship()

    def create_test_ship(self):
        """Create a test ship for user assignment testing"""
        print(f"\n🚢 Creating Test Ship for User Assignment")
        
        ship_data = {
            "name": f"Test Ship for User Assignment {int(time.time())}",
            "imo_number": f"IMO{int(time.time())}",
            "class_society": "DNV GL",
            "flag": "Panama",
            "gross_tonnage": 50000.0,
            "deadweight": 75000.0,
            "built_year": 2020
        }
        
        success, ship = self.run_test(
            "Create Test Ship",
            "POST",
            "ships",
            200,
            data=ship_data
        )
        
        if success:
            self.test_ship_id = ship.get('id')
            print(f"✅ Test ship created: {ship.get('name')} (ID: {self.test_ship_id})")
            return True
        else:
            print(f"❌ Failed to create test ship")
            return False

    def test_user_update_with_ship_field(self):
        """Test PUT /api/users/{user_id} - test updating a user with ship field included"""
        print(f"\n✏️ Testing PUT /api/users/{{user_id}} - Ship Field Update")
        
        # First get a user to update (use admin user for testing)
        if not self.admin_user_id:
            print(f"❌ No admin user ID available for testing")
            return False
        
        # Get current user details
        success, current_user = self.run_test(
            "Get Current User Details",
            "GET",
            f"users/{self.admin_user_id}",
            200
        )
        
        if not success:
            print(f"❌ Failed to get current user details")
            return False
        
        print(f"   Current user: {current_user.get('username')} - Ship: {current_user.get('ship', 'None')}")
        
        # Prepare update data with ship field
        update_data = {
            "username": current_user.get('username'),
            "email": current_user.get('email'),
            "full_name": current_user.get('full_name'),
            "role": current_user.get('role'),
            "department": current_user.get('department'),
            "company": current_user.get('company'),
            "ship": self.test_ship_id,  # Assign the test ship
            "zalo": current_user.get('zalo'),
            "gmail": current_user.get('gmail')
        }
        
        success, updated_user = self.run_test(
            "Update User with Ship Field",
            "PUT",
            f"users/{self.admin_user_id}",
            200,
            data=update_data
        )
        
        if success:
            updated_ship = updated_user.get('ship')
            print(f"✅ User updated successfully")
            print(f"   Updated ship field: {updated_ship}")
            
            # Verify the ship field was updated correctly
            if updated_ship == self.test_ship_id:
                print(f"✅ Ship field updated correctly to: {self.test_ship_id}")
                return True
            else:
                print(f"❌ Ship field not updated correctly. Expected: {self.test_ship_id}, Got: {updated_ship}")
                return False
        else:
            print(f"❌ Failed to update user with ship field")
            return False

    def test_user_models_ship_field(self):
        """Verify that User models properly include the ship field"""
        print(f"\n🔍 Testing User Models Ship Field Support")
        
        # Create a test user with ship field to verify model support
        test_user_data = {
            "username": f"ship_test_user_{int(time.time())}",
            "email": f"ship_test_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Ship Test User",
            "role": "viewer",
            "department": "technical",
            "company": self.test_company_id,
            "ship": self.test_ship_id,
            "zalo": "+84123456789",
            "gmail": "test@gmail.com"
        }
        
        success, new_user = self.run_test(
            "Create User with Ship Field",
            "POST", 
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success:
            self.test_user_id = new_user.get('id')
            created_ship = new_user.get('ship')
            
            print(f"✅ User created with ship field")
            print(f"   Username: {new_user.get('username')}")
            print(f"   Ship: {created_ship}")
            print(f"   Company: {new_user.get('company')}")
            print(f"   Zalo: {new_user.get('zalo')}")
            print(f"   Gmail: {new_user.get('gmail')}")
            
            # Verify ship field matches what we sent
            if created_ship == self.test_ship_id:
                print(f"✅ UserCreate and UserResponse models support ship field correctly")
                return True
            else:
                print(f"❌ Ship field mismatch. Expected: {self.test_ship_id}, Got: {created_ship}")
                return False
        else:
            print(f"❌ Failed to create user with ship field")
            return False

    def test_ship_field_edge_cases(self):
        """Test edge cases with ship field (empty, non-existent ship)"""
        print(f"\n🧪 Testing Ship Field Edge Cases")
        
        if not self.test_user_id:
            print(f"❌ No test user available for edge case testing")
            return False
        
        # Test 1: Update user with empty ship field
        print(f"\n   Test 1: Empty ship field")
        success, user_data = self.run_test(
            "Get Test User for Edge Cases",
            "GET",
            f"users/{self.test_user_id}",
            200
        )
        
        if not success:
            return False
        
        update_data_empty = {
            "username": user_data.get('username'),
            "email": user_data.get('email'),
            "full_name": user_data.get('full_name'),
            "role": user_data.get('role'),
            "department": user_data.get('department'),
            "company": user_data.get('company'),
            "ship": None,  # Empty ship field
            "zalo": user_data.get('zalo'),
            "gmail": user_data.get('gmail')
        }
        
        success, updated_user = self.run_test(
            "Update User with Empty Ship",
            "PUT",
            f"users/{self.test_user_id}",
            200,
            data=update_data_empty
        )
        
        if success:
            updated_ship = updated_user.get('ship')
            print(f"✅ Empty ship field handled correctly: {updated_ship}")
        else:
            print(f"❌ Failed to handle empty ship field")
            return False
        
        # Test 2: Update user with non-existent ship ID
        print(f"\n   Test 2: Non-existent ship ID")
        fake_ship_id = "non-existent-ship-id-12345"
        
        update_data_fake = {
            "username": user_data.get('username'),
            "email": user_data.get('email'),
            "full_name": user_data.get('full_name'),
            "role": user_data.get('role'),
            "department": user_data.get('department'),
            "company": user_data.get('company'),
            "ship": fake_ship_id,  # Non-existent ship
            "zalo": user_data.get('zalo'),
            "gmail": user_data.get('gmail')
        }
        
        success, updated_user = self.run_test(
            "Update User with Non-existent Ship",
            "PUT",
            f"users/{self.test_user_id}",
            200,  # Should still succeed as ship field is optional
            data=update_data_fake
        )
        
        if success:
            updated_ship = updated_user.get('ship')
            print(f"✅ Non-existent ship ID handled: {updated_ship}")
            print(f"   Note: System allows non-existent ship IDs (optional validation)")
        else:
            print(f"❌ Failed to handle non-existent ship ID")
            return False
        
        return True

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print(f"\n🧹 Cleaning up test data")
        
        # Delete test user if created
        if self.test_user_id:
            success, _ = self.run_test(
                "Delete Test User",
                "DELETE",
                f"users/{self.test_user_id}",
                200
            )
            if success:
                print(f"✅ Test user deleted")
            else:
                print(f"⚠️ Failed to delete test user")

def main():
    """Main test execution for User Management with Ship Field"""
    print("👥 User Management with Ship Field Testing")
    print("=" * 60)
    
    tester = UserManagementShipTester()
    
    # Test authentication first
    if not tester.test_authentication():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Run all tests in sequence
    test_results = []
    
    test_results.append(("Authentication with Super Admin Role", True))  # Already passed
    test_results.append(("GET /api/users - Ship Field Verification", tester.test_get_users_with_ship_field()))
    test_results.append(("GET /api/companies - Companies Data", tester.test_get_companies()))
    test_results.append(("GET /api/ships - Ships Data", tester.test_get_ships()))
    test_results.append(("User Models Ship Field Support", tester.test_user_models_ship_field()))
    test_results.append(("PUT /api/users/{user_id} - Ship Field Update", tester.test_user_update_with_ship_field()))
    test_results.append(("Ship Field Edge Cases", tester.test_ship_field_edge_cases()))
    
    # Cleanup
    tester.cleanup_test_data()
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 USER MANAGEMENT SHIP FIELD TEST RESULTS")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:45} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Feature Tests: {passed_tests}/{total_tests}")
    
    # Summary of findings
    print("\n" + "=" * 60)
    print("📋 SUMMARY OF FINDINGS")
    print("=" * 60)
    
    if passed_tests == total_tests and tester.tests_passed == tester.tests_run:
        print("🎉 ALL TESTS PASSED!")
        print("✅ User Management backend functionality with ship field is working correctly")
        print("✅ Authentication with admin/admin123 credentials successful (Super Admin role)")
        print("✅ GET /api/users includes ship field in all user responses")
        print("✅ GET /api/companies and GET /api/ships endpoints working")
        print("✅ PUT /api/users/{user_id} successfully updates users with ship field")
        print("✅ User models (UserCreate, UserUpdate, UserResponse) properly support ship field")
        print("✅ Edge cases with ship field handled appropriately")
        return 0
    else:
        print("⚠️ SOME TESTS FAILED - Issues found:")
        for test_name, result in test_results:
            if not result:
                print(f"❌ {test_name}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
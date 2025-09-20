#!/usr/bin/env python3
"""
MongoDB Backend Migration Testing
=================================

This test suite specifically verifies the MongoDB backend migration as requested:
1. Authentication: Test login with admin/admin123 credentials
2. User Management: GET /api/users (should return users from MongoDB) and verify user data matches what was migrated
3. MongoDB Data Integrity: Verify migrated data is accessible through API and user roles/permissions work correctly
4. Core Functionality: Test basic CRUD operations with MongoDB and verify API responses match expected format
"""

import requests
import sys
import json
from datetime import datetime, timezone
import time

class MongoDBMigrationTester:
    def __init__(self, base_url="https://ship-cert-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_data = None
        self.test_results = []

    def log_test_result(self, test_name, success, details=""):
        """Log test result for summary"""
        self.test_results.append({
            "name": test_name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
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
        """Test 1: Authentication with admin/admin123 credentials"""
        print(f"\n🔐 TEST 1: AUTHENTICATION WITH ADMIN/ADMIN123")
        print("=" * 60)
        
        success, response = self.run_test(
            "Admin Login with admin/admin123",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_data = response.get('user', {})
            print(f"✅ Authentication successful!")
            print(f"   User ID: {self.admin_user_data.get('id')}")
            print(f"   Username: {self.admin_user_data.get('username')}")
            print(f"   Full Name: {self.admin_user_data.get('full_name')}")
            print(f"   Role: {self.admin_user_data.get('role')}")
            print(f"   Company: {self.admin_user_data.get('company')}")
            print(f"   Department: {self.admin_user_data.get('department')}")
            print(f"   Token Type: {response.get('token_type')}")
            
            # Verify token structure
            if response.get('token_type') == 'bearer' and len(self.token) > 50:
                print(f"   Token format: Valid JWT token received")
                self.log_test_result("Authentication", True, f"Successfully authenticated as {self.admin_user_data.get('username')} with role {self.admin_user_data.get('role')}")
                return True
            else:
                print(f"   ❌ Invalid token format")
                self.log_test_result("Authentication", False, "Invalid token format received")
                return False
        else:
            self.log_test_result("Authentication", False, "Failed to authenticate with admin/admin123")
            return False

    def test_user_management_mongodb(self):
        """Test 2: User Management - GET /api/users (should return users from MongoDB)"""
        print(f"\n👥 TEST 2: USER MANAGEMENT - MONGODB DATA RETRIEVAL")
        print("=" * 60)
        
        success, users = self.run_test("Get Users from MongoDB", "GET", "users", 200)
        if not success:
            self.log_test_result("User Management", False, "Failed to retrieve users from MongoDB")
            return False
        
        print(f"✅ Successfully retrieved {len(users)} users from MongoDB")
        
        # Verify user data structure and content
        if not users:
            print("❌ No users found in MongoDB - migration may have failed")
            self.log_test_result("User Management", False, "No users found in MongoDB")
            return False
        
        # Analyze user data structure
        print(f"\n📊 User Data Analysis:")
        for i, user in enumerate(users):
            print(f"   User {i+1}:")
            print(f"     ID: {user.get('id')}")
            print(f"     Username: {user.get('username')}")
            print(f"     Full Name: {user.get('full_name')}")
            print(f"     Role: {user.get('role')}")
            print(f"     Department: {user.get('department')}")
            print(f"     Company: {user.get('company')}")
            print(f"     Email: {user.get('email')}")
            print(f"     Active: {user.get('is_active')}")
            print(f"     Created: {user.get('created_at')}")
            
            # Verify required fields are present
            required_fields = ['id', 'username', 'full_name', 'role', 'department', 'is_active']
            missing_fields = [field for field in required_fields if not user.get(field)]
            if missing_fields:
                print(f"     ❌ Missing required fields: {missing_fields}")
                self.log_test_result("User Management", False, f"User {user.get('username')} missing fields: {missing_fields}")
                return False
        
        # Verify admin user exists and has correct data
        admin_user = next((u for u in users if u.get('username') == 'admin'), None)
        if not admin_user:
            print("❌ Admin user not found in MongoDB")
            self.log_test_result("User Management", False, "Admin user not found in MongoDB")
            return False
        
        print(f"\n✅ Admin user verification:")
        print(f"   Username: {admin_user.get('username')}")
        print(f"   Role: {admin_user.get('role')}")
        print(f"   Full Name: {admin_user.get('full_name')}")
        
        if admin_user.get('role') != 'super_admin':
            print(f"❌ Admin user role incorrect: expected 'super_admin', got '{admin_user.get('role')}'")
            self.log_test_result("User Management", False, f"Admin user role incorrect: {admin_user.get('role')}")
            return False
        
        self.log_test_result("User Management", True, f"Successfully retrieved {len(users)} users from MongoDB with correct data structure")
        return True

    def test_mongodb_data_integrity(self):
        """Test 3: MongoDB Data Integrity - Verify migrated data accessibility and user roles/permissions"""
        print(f"\n🔒 TEST 3: MONGODB DATA INTEGRITY - ROLES AND PERMISSIONS")
        print("=" * 60)
        
        # Test role-based access control
        success, users = self.run_test("Verify Role-based User Access", "GET", "users", 200)
        if not success:
            self.log_test_result("Data Integrity", False, "Failed to access users with role-based filtering")
            return False
        
        # Verify admin can see all users (Super Admin should see all)
        print(f"✅ Admin user can access {len(users)} users (Super Admin sees all)")
        
        # Test user creation (CRUD operation)
        test_user_data = {
            "username": f"mongodb_test_user_{int(time.time())}",
            "email": f"mongodb_test_{int(time.time())}@shipmanagement.com",
            "password": "TestPassword123!",
            "full_name": "MongoDB Test User",
            "role": "viewer",
            "department": "technical",
            "company": "Test Company"
        }
        
        success, new_user = self.run_test(
            "Create User in MongoDB",
            "POST",
            "users",
            200,
            data=test_user_data
        )
        
        if not success:
            self.log_test_result("Data Integrity", False, "Failed to create user in MongoDB")
            return False
        
        created_user_id = new_user.get('id')
        print(f"✅ Successfully created user in MongoDB: {new_user.get('username')} (ID: {created_user_id})")
        
        # Test user update
        update_data = {
            "full_name": "MongoDB Test User Updated",
            "company": "Updated Test Company"
        }
        
        success, updated_user = self.run_test(
            "Update User in MongoDB",
            "PUT",
            f"users/{created_user_id}",
            200,
            data=update_data
        )
        
        if not success:
            self.log_test_result("Data Integrity", False, "Failed to update user in MongoDB")
            return False
        
        print(f"✅ Successfully updated user in MongoDB: {updated_user.get('full_name')}")
        
        # Test user deletion (soft delete)
        success, delete_response = self.run_test(
            "Delete User in MongoDB",
            "DELETE",
            f"users/{created_user_id}",
            200
        )
        
        if not success:
            self.log_test_result("Data Integrity", False, "Failed to delete user in MongoDB")
            return False
        
        print(f"✅ Successfully deleted user in MongoDB")
        
        # Verify user is soft deleted (should not appear in active users list)
        success, users_after_delete = self.run_test("Verify Soft Delete", "GET", "users", 200)
        if success:
            deleted_user = next((u for u in users_after_delete if u.get('id') == created_user_id), None)
            if deleted_user:
                print(f"❌ Deleted user still appears in active users list")
                self.log_test_result("Data Integrity", False, "Soft delete not working properly")
                return False
            else:
                print(f"✅ Soft delete working correctly - user removed from active list")
        
        self.log_test_result("Data Integrity", True, "All CRUD operations working correctly with MongoDB")
        return True

    def test_core_functionality_mongodb(self):
        """Test 4: Core Functionality - Basic CRUD operations and API response format"""
        print(f"\n⚙️ TEST 4: CORE FUNCTIONALITY - CRUD OPERATIONS AND API RESPONSES")
        print("=" * 60)
        
        # Test API response format consistency
        success, users = self.run_test("Verify API Response Format", "GET", "users", 200)
        if not success:
            self.log_test_result("Core Functionality", False, "Failed to get users for response format verification")
            return False
        
        # Verify response format
        if not isinstance(users, list):
            print(f"❌ API response format incorrect: expected list, got {type(users)}")
            self.log_test_result("Core Functionality", False, f"API response format incorrect: {type(users)}")
            return False
        
        print(f"✅ API response format correct: List of {len(users)} users")
        
        # Test each user object structure
        for user in users[:3]:  # Check first 3 users
            expected_fields = ['id', 'username', 'full_name', 'role', 'department', 'is_active', 'created_at']
            for field in expected_fields:
                if field not in user:
                    print(f"❌ User object missing required field: {field}")
                    self.log_test_result("Core Functionality", False, f"User object missing field: {field}")
                    return False
        
        print(f"✅ User object structure correct with all required fields")
        
        # Test data types
        sample_user = users[0] if users else {}
        type_checks = [
            ('id', str),
            ('username', str),
            ('full_name', str),
            ('role', str),
            ('department', str),
            ('is_active', bool)
        ]
        
        for field, expected_type in type_checks:
            if field in sample_user:
                actual_type = type(sample_user[field])
                if actual_type != expected_type:
                    print(f"❌ Field {field} type incorrect: expected {expected_type}, got {actual_type}")
                    self.log_test_result("Core Functionality", False, f"Field {field} type incorrect")
                    return False
        
        print(f"✅ Data types correct for all fields")
        
        # Test MongoDB connection stability with multiple requests
        print(f"\n🔄 Testing MongoDB connection stability...")
        for i in range(5):
            success, _ = self.run_test(f"Stability Test {i+1}", "GET", "users", 200)
            if not success:
                print(f"❌ MongoDB connection unstable at request {i+1}")
                self.log_test_result("Core Functionality", False, f"MongoDB connection unstable")
                return False
        
        print(f"✅ MongoDB connection stable across multiple requests")
        
        self.log_test_result("Core Functionality", True, "All core functionality working correctly with MongoDB")
        return True

    def run_all_tests(self):
        """Run all MongoDB migration tests"""
        print("🚢 MONGODB BACKEND MIGRATION TESTING")
        print("=" * 60)
        print("Testing MongoDB migration verification as requested:")
        print("1. Authentication with admin/admin123 credentials")
        print("2. User Management - GET /api/users from MongoDB")
        print("3. MongoDB Data Integrity - roles and permissions")
        print("4. Core Functionality - CRUD operations and API responses")
        print("=" * 60)
        
        # Run tests in sequence
        test_functions = [
            ("Authentication", self.test_authentication),
            ("User Management", self.test_user_management_mongodb),
            ("Data Integrity", self.test_mongodb_data_integrity),
            ("Core Functionality", self.test_core_functionality_mongodb)
        ]
        
        all_passed = True
        
        for test_name, test_func in test_functions:
            if not test_func():
                all_passed = False
                print(f"\n❌ {test_name} test failed - stopping further tests")
                break
        
        return all_passed

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 MONGODB MIGRATION TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"{result['name']:25} {status}")
            if result['details']:
                print(f"{'':27} {result['details']}")
        
        print(f"\nAPI Tests: {self.tests_passed}/{self.tests_run}")
        print(f"Feature Tests: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests and self.tests_passed == self.tests_run:
            print("\n🎉 ALL MONGODB MIGRATION TESTS PASSED!")
            print("✅ MongoDB backend migration is working correctly")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} tests failed")
            print("❌ MongoDB backend migration has issues")
            return False

def main():
    """Main test execution"""
    tester = MongoDBMigrationTester()
    
    success = tester.run_all_tests()
    final_result = tester.print_summary()
    
    return 0 if final_result else 1

if __name__ == "__main__":
    sys.exit(main())
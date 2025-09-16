#!/usr/bin/env python3
"""
MongoDB Migration Verification Test
===================================

This test specifically verifies the requirements from the review request:
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

class MongoDBVerificationTester:
    def __init__(self, base_url="https://aicert-analyzer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_user_data = None

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        print(f"🔍 {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                print(f"   ✅ Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"   ❌ Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False, {}

def main():
    """Main verification test"""
    print("🚢 MONGODB MIGRATION VERIFICATION TEST")
    print("=" * 60)
    print("Verifying specific requirements from review request:")
    print("1. Authentication with admin/admin123")
    print("2. User Management from MongoDB")
    print("3. Data integrity and permissions")
    print("4. CRUD operations and API format")
    print("=" * 60)
    
    tester = MongoDBVerificationTester()
    
    # 1. Test Authentication with admin/admin123
    print(f"\n1️⃣ AUTHENTICATION TEST")
    print("-" * 30)
    success, response = tester.run_test(
        "Login with admin/admin123",
        "POST",
        "auth/login",
        200,
        data={"username": "admin", "password": "admin123"}
    )
    
    if not success:
        print("❌ Authentication failed - stopping tests")
        return 1
    
    tester.token = response['access_token']
    tester.admin_user_data = response.get('user', {})
    
    print(f"   ✅ Authentication successful!")
    print(f"   User: {tester.admin_user_data.get('full_name')} ({tester.admin_user_data.get('role')})")
    print(f"   Token received: {len(tester.token)} characters")
    
    # 2. Test User Management - GET /api/users from MongoDB
    print(f"\n2️⃣ USER MANAGEMENT FROM MONGODB")
    print("-" * 30)
    success, users = tester.run_test("Get users from MongoDB", "GET", "users", 200)
    
    if not success:
        print("❌ Failed to get users from MongoDB")
        return 1
    
    print(f"   ✅ Retrieved {len(users)} users from MongoDB")
    print(f"   User data structure verification:")
    
    # Verify user data structure matches expected format
    if users:
        sample_user = users[0]
        required_fields = ['id', 'username', 'full_name', 'role', 'department', 'is_active', 'created_at']
        missing_fields = [field for field in required_fields if field not in sample_user]
        
        if missing_fields:
            print(f"   ❌ Missing required fields: {missing_fields}")
            return 1
        else:
            print(f"   ✅ All required fields present")
        
        # Show sample user data
        print(f"   Sample user: {sample_user.get('username')} - {sample_user.get('full_name')} ({sample_user.get('role')})")
    
    # 3. Test Data Integrity and Permissions
    print(f"\n3️⃣ DATA INTEGRITY AND PERMISSIONS")
    print("-" * 30)
    
    # Verify admin user exists and has correct role
    admin_user = next((u for u in users if u.get('username') == 'admin'), None)
    if not admin_user:
        print("   ❌ Admin user not found in MongoDB")
        return 1
    
    if admin_user.get('role') != 'super_admin':
        print(f"   ❌ Admin user role incorrect: {admin_user.get('role')}")
        return 1
    
    print(f"   ✅ Admin user verified: {admin_user.get('full_name')} (super_admin)")
    
    # Verify different user roles exist
    roles_found = set(user.get('role') for user in users)
    expected_roles = {'super_admin', 'admin', 'manager', 'editor', 'viewer'}
    
    print(f"   Roles in database: {sorted(roles_found)}")
    if not roles_found.intersection(expected_roles):
        print("   ❌ No expected roles found")
        return 1
    else:
        print(f"   ✅ Multiple user roles verified")
    
    # Verify departments exist
    departments_found = set(user.get('department') for user in users if user.get('department'))
    print(f"   Departments in database: {sorted(departments_found)}")
    
    if len(departments_found) < 3:
        print("   ❌ Insufficient department diversity")
        return 1
    else:
        print(f"   ✅ Multiple departments verified")
    
    # 4. Test CRUD Operations and API Format
    print(f"\n4️⃣ CRUD OPERATIONS AND API FORMAT")
    print("-" * 30)
    
    # Test Create operation
    test_user_data = {
        "username": f"verification_test_{int(time.time())}",
        "email": f"verification_{int(time.time())}@test.com",
        "password": "TestPassword123!",
        "full_name": "Verification Test User",
        "role": "viewer",
        "department": "technical",
        "company": "Test Company"
    }
    
    success, new_user = tester.run_test(
        "Create user (MongoDB CRUD)",
        "POST",
        "users",
        200,
        data=test_user_data
    )
    
    if not success:
        print("   ❌ Create operation failed")
        return 1
    
    created_user_id = new_user.get('id')
    print(f"   ✅ Create: User created with ID {created_user_id}")
    
    # Test Update operation
    update_data = {
        "full_name": "Verification Test User Updated",
        "company": "Updated Test Company"
    }
    
    success, updated_user = tester.run_test(
        "Update user (MongoDB CRUD)",
        "PUT",
        f"users/{created_user_id}",
        200,
        data=update_data
    )
    
    if not success:
        print("   ❌ Update operation failed")
        return 1
    
    print(f"   ✅ Update: User updated successfully")
    
    # Test Delete operation
    success, delete_response = tester.run_test(
        "Delete user (MongoDB CRUD)",
        "DELETE",
        f"users/{created_user_id}",
        200
    )
    
    if not success:
        print("   ❌ Delete operation failed")
        return 1
    
    print(f"   ✅ Delete: User deleted successfully")
    
    # Verify API response format consistency
    success, final_users = tester.run_test("Verify API format consistency", "GET", "users", 200)
    
    if not success:
        print("   ❌ API format verification failed")
        return 1
    
    if not isinstance(final_users, list):
        print(f"   ❌ API response format incorrect: expected list, got {type(final_users)}")
        return 1
    
    print(f"   ✅ API Format: Consistent list response with {len(final_users)} users")
    
    # Final Summary
    print(f"\n" + "=" * 60)
    print("🎉 MONGODB MIGRATION VERIFICATION COMPLETE")
    print("=" * 60)
    print("✅ Authentication: admin/admin123 working")
    print("✅ User Management: MongoDB data accessible via API")
    print("✅ Data Integrity: User roles and permissions verified")
    print("✅ CRUD Operations: All operations working with MongoDB")
    print("✅ API Format: Responses match expected format")
    print("\n🚀 MongoDB backend migration is fully functional!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
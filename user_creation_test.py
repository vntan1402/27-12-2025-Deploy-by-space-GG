import requests
import sys
import json
from datetime import datetime, timezone
import time

class UserCreationTester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_users = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
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

    def test_admin_login(self):
        """Test admin login and get token"""
        print(f"\n🔐 Testing Admin Authentication")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"✅ Admin login successful")
            print(f"   User: {response.get('user', {}).get('full_name')} ({response.get('user', {}).get('role')})")
            return True
        return False

    def create_test_user(self, user_data, user_description):
        """Create a single test user"""
        print(f"\n👤 Creating {user_description}")
        
        success, response = self.run_test(
            f"Create {user_description}",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        
        if success:
            self.created_users.append({
                'username': user_data['username'],
                'password': user_data['password'],
                'full_name': user_data['full_name'],
                'role': user_data['role'],
                'department': user_data['department'],
                'company': user_data.get('company', ''),
                'ship': user_data.get('ship', ''),
                'user_id': response.get('id')
            })
            print(f"   ✅ Created: {user_data['username']} - {user_data['full_name']}")
            print(f"   Role: {user_data['role']}, Department: {user_data['department']}")
            if user_data.get('company'):
                print(f"   Company: {user_data['company']}")
            if user_data.get('ship'):
                print(f"   Ship: {user_data['ship']}")
            return True
        return False

    def test_user_login(self, username, password, expected_role):
        """Test login for a created user"""
        print(f"\n🔑 Testing login for {username}")
        
        success, response = self.run_test(
            f"Login {username}",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'access_token' in response:
            user_info = response.get('user', {})
            actual_role = user_info.get('role')
            print(f"   ✅ Login successful for {username}")
            print(f"   User: {user_info.get('full_name')} ({actual_role})")
            print(f"   Department: {user_info.get('department')}")
            
            if actual_role == expected_role:
                print(f"   ✅ Role verification passed: {actual_role}")
                return True
            else:
                print(f"   ❌ Role mismatch: expected {expected_role}, got {actual_role}")
                return False
        return False

    def create_all_test_users(self):
        """Create all 5 test users as specified in the requirements"""
        print(f"\n👥 Creating 5 Test Users for Ship Management System")
        print("=" * 60)
        
        # User 1: crew1 (Crew/Thuyền viên)
        crew1_data = {
            "username": "crew1",
            "password": "123456",
            "email": "crew1@shipmanagement.com",
            "full_name": "Nguyễn Văn Crew",
            "role": "viewer",
            "department": "ship_crew",
            "company": "ABC Company Ltd Updated",
            "ship": "COSCO Shanghai"
        }
        
        # User 2: officer1 (Ship Officer/Sĩ quan)
        officer1_data = {
            "username": "officer1",
            "password": "123456",
            "email": "officer1@shipmanagement.com",
            "full_name": "Trần Thị Officer",
            "role": "editor",
            "department": "technical",
            "company": "XYZ Company"
        }
        
        # User 3: manager1 (Company Officer/Cán bộ công ty)
        manager1_data = {
            "username": "manager1",
            "password": "123456",
            "email": "manager1@shipmanagement.com",
            "full_name": "Lê Văn Manager",
            "role": "manager",
            "department": "operations",
            "company": "ABC Company Ltd Updated"
        }
        
        # User 4: admin1 (Admin/Quản trị viên)
        admin1_data = {
            "username": "admin1",
            "password": "123456",
            "email": "admin1@shipmanagement.com",
            "full_name": "Phạm Thị Admin",
            "role": "admin",
            "department": "commercial",
            "company": "XYZ Company"
        }
        
        # User 5: superadmin1 (Super Admin/Siêu quản trị)
        superadmin1_data = {
            "username": "superadmin1",
            "password": "123456",
            "email": "superadmin1@shipmanagement.com",
            "full_name": "Hoàng Văn SuperAdmin",
            "role": "super_admin",
            "department": "safety",
            "company": "ABC Company Ltd Updated"
        }
        
        # Create all users
        users_to_create = [
            (crew1_data, "crew1 (Crew/Thuyền viên)"),
            (officer1_data, "officer1 (Ship Officer/Sĩ quan)"),
            (manager1_data, "manager1 (Company Officer/Cán bộ công ty)"),
            (admin1_data, "admin1 (Admin/Quản trị viên)"),
            (superadmin1_data, "superadmin1 (Super Admin/Siêu quản trị)")
        ]
        
        success_count = 0
        for user_data, description in users_to_create:
            if self.create_test_user(user_data, description):
                success_count += 1
        
        print(f"\n📊 User Creation Summary: {success_count}/{len(users_to_create)} users created successfully")
        return success_count == len(users_to_create)

    def test_all_user_logins(self):
        """Test login for all created users"""
        print(f"\n🔑 Testing Login for All Created Users")
        print("=" * 50)
        
        login_success_count = 0
        for user in self.created_users:
            if self.test_user_login(user['username'], user['password'], user['role']):
                login_success_count += 1
        
        print(f"\n📊 Login Test Summary: {login_success_count}/{len(self.created_users)} users logged in successfully")
        return login_success_count == len(self.created_users)

    def list_all_users(self):
        """List all users to confirm they exist"""
        print(f"\n📋 Listing All Users to Confirm Creation")
        
        success, users = self.run_test("Get All Users", "GET", "users", 200)
        if success:
            print(f"   ✅ Found {len(users)} total users in system")
            print(f"\n   📝 User List:")
            for user in users:
                print(f"   - {user.get('username')} ({user.get('full_name')}) - {user.get('role')} - {user.get('department')}")
                if user.get('company'):
                    print(f"     Company: {user.get('company')}")
                if user.get('ship'):
                    print(f"     Ship: {user.get('ship')}")
            
            # Check if our created users are in the list
            created_usernames = [u['username'] for u in self.created_users]
            found_users = [u for u in users if u.get('username') in created_usernames]
            print(f"\n   ✅ Confirmed {len(found_users)}/{len(self.created_users)} created users exist in system")
            return True
        return False

def main():
    """Main test execution"""
    print("🚢 Ship Management System - User Creation Testing")
    print("=" * 60)
    print("Creating 5 test users for different roles:")
    print("1. crew1 (Crew/Thuyền viên) - viewer role")
    print("2. officer1 (Ship Officer/Sĩ quan) - editor role") 
    print("3. manager1 (Company Officer/Cán bộ công ty) - manager role")
    print("4. admin1 (Admin/Quản trị viên) - admin role")
    print("5. superadmin1 (Super Admin/Siêu quản trị) - super_admin role")
    print("=" * 60)
    
    tester = UserCreationTester()
    
    # Test admin authentication first
    if not tester.test_admin_login():
        print("❌ Admin authentication failed, stopping tests")
        return 1
    
    # Create all test users
    if not tester.create_all_test_users():
        print("❌ User creation failed, stopping tests")
        return 1
    
    # Test login for all created users
    if not tester.test_all_user_logins():
        print("❌ User login testing failed")
        return 1
    
    # List all users to confirm they exist
    if not tester.list_all_users():
        print("❌ Failed to list users")
        return 1
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"Total API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Users Created: {len(tester.created_users)}/5")
    
    if tester.tests_passed == tester.tests_run and len(tester.created_users) == 5:
        print("🎉 All user creation and login tests passed!")
        print("\n✅ EXPECTED RESULT ACHIEVED:")
        print("All 5 users created successfully representing each role level in the system hierarchy:")
        for user in tester.created_users:
            print(f"   - {user['username']}: {user['full_name']} ({user['role']})")
        return 0
    else:
        print("⚠️ Some tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
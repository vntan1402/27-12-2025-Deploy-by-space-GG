import requests
import sys
import json
from datetime import datetime, timezone

class AdminCompanyFixTester:
    def __init__(self, base_url="https://shipgooglesync.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.superadmin1_token = None
        self.admin1_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

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

    def login_user(self, username, password):
        """Login and get token"""
        success, response = self.run_test(
            f"Login {username}",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            return response['access_token'], response.get('user', {})
        return None, None

    def fix_admin1_company_visibility(self):
        """Fix admin1 company visibility by creating matching company"""
        print(f"\n🔧 FIXING ADMIN1 COMPANY VISIBILITY ISSUE")
        print("=" * 60)
        
        # Step 1: Login as superadmin1
        print(f"\n📋 STEP 1: Login as superadmin1")
        self.superadmin1_token, superadmin1_data = self.login_user("superadmin1", "123456")
        if not self.superadmin1_token:
            print("❌ Failed to login as superadmin1")
            return False
        
        # Step 2: Login as admin1 to get their company field
        print(f"\n📋 STEP 2: Get admin1 company field")
        self.admin1_token, admin1_data = self.login_user("admin1", "123456")
        if not self.admin1_token:
            print("❌ Failed to login as admin1")
            return False
        
        admin1_company = admin1_data.get('company')
        print(f"   admin1.company: '{admin1_company}'")
        
        # Step 3: Check if company already exists
        print(f"\n📋 STEP 3: Check existing companies")
        success, companies = self.run_test(
            "Get All Companies",
            "GET",
            "companies",
            200,
            token=self.superadmin1_token
        )
        
        if not success:
            return False
        
        # Check if matching company exists
        matching_company = None
        for company in companies:
            if company.get('name_vn') == admin1_company or company.get('name_en') == admin1_company:
                matching_company = company
                break
        
        if matching_company:
            print(f"   ✅ Matching company already exists: {matching_company.get('name_en')}")
        else:
            print(f"   ❌ No matching company found for '{admin1_company}'")
            
            # Step 4: Create matching company
            print(f"\n📋 STEP 4: Create matching company")
            company_data = {
                "name_vn": f"Công ty {admin1_company}",
                "name_en": admin1_company,
                "address_vn": "123 Đường ABC, Quận 1, TP.HCM",
                "address_en": "123 ABC Street, District 1, Ho Chi Minh City",
                "tax_id": "0123456789",
                "gmail": "admin@xyzcompany.com",
                "zalo": "0901234567",
                "system_expiry": "2025-12-31T23:59:59Z"
            }
            
            success, new_company = self.run_test(
                "Create Matching Company",
                "POST",
                "companies",
                200,
                data=company_data,
                token=self.superadmin1_token
            )
            
            if not success:
                print("❌ Failed to create matching company")
                return False
            
            print(f"   ✅ Created company: {new_company.get('name_en')} (ID: {new_company.get('id')})")
        
        # Step 5: Test admin1 company visibility after fix
        print(f"\n📋 STEP 5: Test admin1 company visibility after fix")
        success, admin1_companies = self.run_test(
            "Get Companies (admin1) - After Fix",
            "GET",
            "companies",
            200,
            token=self.admin1_token
        )
        
        if not success:
            return False
        
        print(f"\n📊 RESULTS AFTER FIX:")
        print(f"   Companies visible to admin1: {len(admin1_companies)}")
        
        if len(admin1_companies) > 0:
            print(f"   ✅ SUCCESS: admin1 can now see their company!")
            for company in admin1_companies:
                print(f"     - {company.get('name_en')} / {company.get('name_vn')}")
        else:
            print(f"   ❌ STILL FAILED: admin1 still cannot see any companies")
            return False
        
        return True

def main():
    """Main fix execution"""
    print("🔧 ADMIN COMPANY VISIBILITY FIX TEST")
    print("=" * 60)
    
    tester = AdminCompanyFixTester()
    
    # Run the fix
    success = tester.fix_admin1_company_visibility()
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 FIX TEST RESULTS")
    print("=" * 60)
    
    if success:
        print("✅ Fix applied successfully - admin1 can now see their company")
        return 0
    else:
        print("❌ Fix failed - admin1 still cannot see their company")
        return 1

if __name__ == "__main__":
    sys.exit(main())
import requests
import sys
import json

class AdminCompanyVerificationTester:
    def __init__(self, base_url="https://aicert-analyzer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def verify_admin1_company_visibility(self):
        """Verify admin1 can now see their company"""
        print(f"\n✅ VERIFYING ADMIN1 COMPANY VISIBILITY FIX")
        print("=" * 60)
        
        # Login as admin1
        success, response = self.run_test(
            "Admin1 Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin1", "password": "123456"}
        )
        
        if not success:
            print("❌ Failed to login as admin1")
            return False
        
        token = response.get('access_token')
        user_data = response.get('user', {})
        
        print(f"\n📊 ADMIN1 USER INFO:")
        print(f"   Username: {user_data.get('username')}")
        print(f"   Full Name: {user_data.get('full_name')}")
        print(f"   Role: {user_data.get('role')}")
        print(f"   Company: '{user_data.get('company')}'")
        
        # Get companies as admin1
        success, companies = self.run_test(
            "Get Companies (admin1)",
            "GET",
            "companies",
            200,
            token=token
        )
        
        if not success:
            print("❌ Failed to get companies as admin1")
            return False
        
        print(f"\n📊 COMPANY VISIBILITY RESULTS:")
        print(f"   Companies visible to admin1: {len(companies)}")
        
        if len(companies) == 0:
            print("   ❌ ISSUE STILL EXISTS: admin1 sees 0 companies!")
            return False
        
        print(f"   ✅ SUCCESS: admin1 can see {len(companies)} company(ies)!")
        
        for i, company in enumerate(companies, 1):
            print(f"\n   Company {i}:")
            print(f"     ID: {company.get('id')}")
            print(f"     Name VN: '{company.get('name_vn')}'")
            print(f"     Name EN: '{company.get('name_en')}'")
            print(f"     Tax ID: {company.get('tax_id')}")
            
            # Verify this matches admin1's company field
            user_company = user_data.get('company')
            name_vn_match = company.get('name_vn') == user_company
            name_en_match = company.get('name_en') == user_company
            
            if name_vn_match or name_en_match:
                print(f"     ✅ MATCHES admin1.company field!")
            else:
                print(f"     ⚠️ Does not match admin1.company field")
        
        return True

def main():
    """Main verification execution"""
    print("✅ ADMIN COMPANY VISIBILITY VERIFICATION TEST")
    print("=" * 60)
    
    tester = AdminCompanyVerificationTester()
    
    # Run verification
    success = tester.verify_admin1_company_visibility()
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 VERIFICATION RESULTS")
    print("=" * 60)
    
    if success:
        print("✅ VERIFICATION PASSED: admin1 can see their company")
        print("🎉 Issue has been successfully resolved!")
        return 0
    else:
        print("❌ VERIFICATION FAILED: admin1 still cannot see their company")
        print("🚨 Issue still exists and needs further investigation")
        return 1

if __name__ == "__main__":
    sys.exit(main())
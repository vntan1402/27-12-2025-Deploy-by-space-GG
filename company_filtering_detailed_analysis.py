import requests
import sys
import json

class DetailedCompanyAnalysis:
    def __init__(self, base_url="https://shipcertdrive.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"

    def login_and_get_token(self, username, password):
        """Login and get token"""
        url = f"{self.api_url}/auth/login"
        response = requests.post(url, json={"username": username, "password": password})
        if response.status_code == 200:
            data = response.json()
            return data['access_token'], data['user']
        return None, None

    def get_companies(self, token):
        """Get companies with token"""
        url = f"{self.api_url}/companies"
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []

    def analyze_role_behavior(self):
        """Analyze the actual role behavior vs expected"""
        print("🔍 DETAILED ROLE BEHAVIOR ANALYSIS")
        print("=" * 80)
        
        # Test admin1
        print("\n1️⃣ ADMIN1 ANALYSIS:")
        print("-" * 40)
        admin_token, admin_user = self.login_and_get_token("admin1", "123456")
        if admin_token:
            admin_companies = self.get_companies(admin_token)
            print(f"✅ Admin1 Login: SUCCESS")
            print(f"   Role: {admin_user.get('role')}")
            print(f"   Company: '{admin_user.get('company')}'")
            print(f"   Companies Retrieved: {len(admin_companies)}")
            
            print(f"\n   COMPANIES SEEN BY ADMIN1:")
            for i, company in enumerate(admin_companies, 1):
                print(f"   {i}. {company.get('name_vn')} / {company.get('name_en')}")
        
        # Test superadmin1
        print("\n2️⃣ SUPERADMIN1 ANALYSIS:")
        print("-" * 40)
        super_token, super_user = self.login_and_get_token("superadmin1", "123456")
        if super_token:
            super_companies = self.get_companies(super_token)
            print(f"✅ SuperAdmin1 Login: SUCCESS")
            print(f"   Role: {super_user.get('role')}")
            print(f"   Company: '{super_user.get('company')}'")
            print(f"   Companies Retrieved: {len(super_companies)}")
            
            print(f"\n   COMPANIES SEEN BY SUPERADMIN1:")
            for i, company in enumerate(super_companies, 1):
                print(f"   {i}. {company.get('name_vn')} / {company.get('name_en')}")
        
        # Analysis
        print("\n🧐 BEHAVIOR ANALYSIS:")
        print("=" * 50)
        
        if admin_companies and super_companies:
            print(f"Admin sees: {len(admin_companies)} companies")
            print(f"Super Admin sees: {len(super_companies)} companies")
            
            if len(admin_companies) == 1 and len(super_companies) == 5:
                print("\n✅ EXPECTED BEHAVIOR CONFIRMED:")
                print("   - Admin sees only their company (1 company)")
                print("   - Super Admin sees all companies (5 companies)")
                print("   - Company filtering is working correctly!")
                
                # Check if admin sees the right company
                admin_company = admin_companies[0]
                user_company = admin_user.get('company')
                
                if (admin_company.get('name_vn') == user_company or 
                    admin_company.get('name_en') == user_company):
                    print("   - Admin sees the correct company matching their profile")
                else:
                    print("   - ⚠️ Admin sees wrong company!")
                    
            elif len(admin_companies) == 0:
                print("\n❌ ISSUE IDENTIFIED:")
                print("   - Admin sees 0 companies (should see 1)")
                print("   - This indicates company name mismatch")
                
            else:
                print(f"\n🤔 UNEXPECTED BEHAVIOR:")
                print(f"   - Admin sees {len(admin_companies)} companies")
                print(f"   - Super Admin sees {len(super_companies)} companies")
        
        # Root cause analysis
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        print("=" * 50)
        
        if admin_user and super_companies:
            user_company = admin_user.get('company')
            print(f"Admin1's company field: '{user_company}'")
            
            matching_companies = []
            for company in super_companies:
                name_vn = company.get('name_vn', '')
                name_en = company.get('name_en', '')
                
                if name_vn == user_company or name_en == user_company:
                    matching_companies.append(company)
                    print(f"✅ MATCH FOUND: {name_vn} / {name_en}")
                else:
                    print(f"❌ NO MATCH: {name_vn} / {name_en}")
            
            print(f"\nExpected companies for admin1: {len(matching_companies)}")
            print(f"Actual companies seen by admin1: {len(admin_companies)}")
            
            if len(matching_companies) != len(admin_companies):
                print("\n🚨 DISCREPANCY DETECTED!")
                print("   The filtering logic may have an issue")
            else:
                print("\n✅ FILTERING LOGIC IS CORRECT!")

def main():
    analyzer = DetailedCompanyAnalysis()
    analyzer.analyze_role_behavior()
    
    print("\n" + "=" * 80)
    print("📋 CONCLUSION")
    print("=" * 80)
    print("The detailed analysis shows the actual behavior of company filtering.")
    print("Check the analysis above to understand if the issue is resolved or")
    print("if there are still discrepancies that need investigation.")

if __name__ == "__main__":
    main()
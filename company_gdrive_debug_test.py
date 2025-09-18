import requests
import sys
import json
from datetime import datetime, timezone
import time

class CompanyGDriveDebugTester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
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

    def debug_company_gdrive_configuration(self):
        """Debug Company Google Drive configuration display issue"""
        print(f"\n🔍 DEBUGGING COMPANY GOOGLE DRIVE CONFIGURATION DISPLAY ISSUE")
        print("=" * 80)
        
        # Step 1: Get all companies and list their IDs and names
        print(f"\n📋 STEP 1: Getting all companies from /api/companies")
        success, companies = self.run_test("Get All Companies", "GET", "companies", 200)
        
        if not success:
            print("❌ Failed to get companies - cannot proceed with debugging")
            return False
        
        print(f"\n📊 FOUND {len(companies)} COMPANIES:")
        company_ids = []
        for i, company in enumerate(companies, 1):
            company_id = company.get('id')
            name_vn = company.get('name_vn', 'N/A')
            name_en = company.get('name_en', 'N/A')
            company_ids.append(company_id)
            print(f"   {i}. ID: {company_id}")
            print(f"      Name (VN): {name_vn}")
            print(f"      Name (EN): {name_en}")
            print(f"      Legacy Name: {company.get('name', 'N/A')}")
            print()
        
        # Step 2: Check MongoDB company_gdrive_config collection
        print(f"\n🗄️ STEP 2: Checking MongoDB for company Google Drive configurations")
        print("Note: This requires direct database access - checking via API endpoints instead")
        
        # Step 3: Test company-specific Google Drive endpoints for each company
        print(f"\n🔧 STEP 3: Testing company-specific Google Drive endpoints")
        
        gdrive_configs_found = []
        
        for company_id in company_ids:
            company_name = next((c.get('name_en', c.get('name_vn', 'Unknown')) for c in companies if c.get('id') == company_id), 'Unknown')
            print(f"\n🏢 Testing Google Drive endpoints for company: {company_name} (ID: {company_id})")
            
            # Test GET /api/companies/{company_id}/gdrive/config
            success, config = self.run_test(
                f"Get GDrive Config for {company_name}",
                "GET",
                f"companies/{company_id}/gdrive/config",
                200
            )
            
            if success:
                print(f"   ✅ Configuration found for {company_name}:")
                print(f"      Configured: {config.get('configured', False)}")
                print(f"      Folder ID: {config.get('folder_id', 'N/A')}")
                print(f"      Service Account: {config.get('service_account_email', 'N/A')}")
                print(f"      Apps Script URL: {config.get('apps_script_url', 'N/A')}")
                gdrive_configs_found.append({
                    'company_id': company_id,
                    'company_name': company_name,
                    'config': config
                })
            else:
                print(f"   ❌ No configuration found or endpoint failed for {company_name}")
            
            # Test GET /api/companies/{company_id}/gdrive/status
            success, status = self.run_test(
                f"Get GDrive Status for {company_name}",
                "GET",
                f"companies/{company_id}/gdrive/status",
                200
            )
            
            if success:
                print(f"   ✅ Status retrieved for {company_name}:")
                print(f"      Status: {status.get('status', 'N/A')}")
                print(f"      Message: {status.get('message', 'N/A')}")
                print(f"      Last Sync: {status.get('last_sync', 'N/A')}")
            else:
                print(f"   ❌ Status endpoint failed for {company_name}")
        
        # Step 4: Check for AMCSC company specifically
        print(f"\n🎯 STEP 4: Checking specifically for AMCSC company")
        amcsc_company = None
        for company in companies:
            name_vn = company.get('name_vn', '').upper()
            name_en = company.get('name_en', '').upper()
            legacy_name = company.get('name', '').upper()
            
            if 'AMCSC' in name_vn or 'AMCSC' in name_en or 'AMCSC' in legacy_name:
                amcsc_company = company
                break
        
        if amcsc_company:
            print(f"   ✅ AMCSC company found:")
            print(f"      ID: {amcsc_company.get('id')}")
            print(f"      Name (VN): {amcsc_company.get('name_vn')}")
            print(f"      Name (EN): {amcsc_company.get('name_en')}")
        else:
            print(f"   ❌ AMCSC company not found in database")
        
        # Step 5: Check system-wide Google Drive settings
        print(f"\n🌐 STEP 5: Checking system-wide Google Drive configuration")
        
        # Test system Google Drive config endpoint
        success, system_config = self.run_test(
            "Get System GDrive Config",
            "GET",
            "gdrive/config",
            200
        )
        
        if success:
            print(f"   ✅ System-wide Google Drive configuration found:")
            print(f"      Configured: {system_config.get('configured', False)}")
            print(f"      Folder ID: {system_config.get('folder_id', 'N/A')}")
            print(f"      Service Account: {system_config.get('service_account_email', 'N/A')}")
        else:
            print(f"   ❌ System-wide Google Drive configuration not found or endpoint failed")
        
        # Test system Google Drive status
        success, system_status = self.run_test(
            "Get System GDrive Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if success:
            print(f"   ✅ System-wide Google Drive status:")
            print(f"      Status: {system_status.get('status', 'N/A')}")
            print(f"      Message: {system_status.get('message', 'N/A')}")
        else:
            print(f"   ❌ System-wide Google Drive status endpoint failed")
        
        # Step 6: Summary and diagnosis
        print(f"\n📋 STEP 6: DIAGNOSIS SUMMARY")
        print("=" * 50)
        
        print(f"🏢 Total companies found: {len(companies)}")
        print(f"🔧 Companies with Google Drive config: {len(gdrive_configs_found)}")
        
        if gdrive_configs_found:
            print(f"\n✅ COMPANIES WITH GOOGLE DRIVE CONFIGURATION:")
            for config_info in gdrive_configs_found:
                print(f"   • {config_info['company_name']} (ID: {config_info['company_id']})")
                print(f"     Configured: {config_info['config'].get('configured', False)}")
                print(f"     Folder ID: {config_info['config'].get('folder_id', 'N/A')}")
        else:
            print(f"\n❌ NO COMPANIES FOUND WITH GOOGLE DRIVE CONFIGURATION")
        
        if amcsc_company:
            amcsc_has_config = any(c['company_id'] == amcsc_company.get('id') for c in gdrive_configs_found)
            if amcsc_has_config:
                print(f"\n✅ AMCSC company HAS Google Drive configuration")
            else:
                print(f"\n❌ AMCSC company does NOT have Google Drive configuration")
                print(f"   This explains why frontend shows 'Not Configured'")
        
        # Step 7: Test connection for configured companies
        if gdrive_configs_found:
            print(f"\n🔗 STEP 7: Testing Google Drive connections for configured companies")
            
            for config_info in gdrive_configs_found:
                company_id = config_info['company_id']
                company_name = config_info['company_name']
                
                print(f"\n🧪 Testing connection for {company_name}...")
                
                # Test connection endpoint
                success, test_result = self.run_test(
                    f"Test GDrive Connection for {company_name}",
                    "POST",
                    f"companies/{company_id}/gdrive/test-connection",
                    200
                )
                
                if success:
                    print(f"   ✅ Connection test result:")
                    print(f"      Success: {test_result.get('success', False)}")
                    print(f"      Message: {test_result.get('message', 'N/A')}")
                else:
                    print(f"   ❌ Connection test failed or endpoint not available")
        
        return len(gdrive_configs_found) > 0

def main():
    """Main test execution"""
    print("🔍 Company Google Drive Configuration Debug Tool")
    print("=" * 60)
    
    tester = CompanyGDriveDebugTester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Run the debugging process
    success = tester.debug_company_gdrive_configuration()
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 DEBUG RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"Total API Tests: {tester.tests_passed}/{tester.tests_run}")
    
    if success:
        print("✅ Google Drive configurations found - check details above")
        print("💡 If frontend still shows 'Not Configured', check:")
        print("   1. Frontend is using correct company ID")
        print("   2. Frontend API calls are working properly")
        print("   3. Frontend is calling the right endpoints")
    else:
        print("❌ No Google Drive configurations found")
        print("💡 This explains why frontend shows 'Not Configured'")
        print("   Solution: Configure Google Drive for the desired company")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
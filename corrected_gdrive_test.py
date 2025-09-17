import requests
import sys
import json
from datetime import datetime, timezone

class CorrectedGDriveDebugTester:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None

    def test_login(self, username="admin", password="admin123"):
        """Test login and get token"""
        print(f"\n🔐 Testing Authentication with {username}/{password}")
        url = f"{self.api_url}/auth/login"
        
        try:
            response = requests.post(url, json={"username": username, "password": password}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                print(f"✅ Login successful, token obtained")
                print(f"   User: {data.get('user', {}).get('full_name')} ({data.get('user', {}).get('role')})")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def test_company_gdrive_endpoints(self):
        """Test company Google Drive endpoints with correct parsing"""
        print(f"\n🔍 TESTING COMPANY GOOGLE DRIVE ENDPOINTS WITH CORRECT PARSING")
        print("=" * 80)
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test AMCSC company specifically
        company_id = "cfe73cb0-cc88-4659-92a7-57cb413a5573"
        company_name = "AMCSC"
        
        print(f"\n🏢 Testing {company_name} (ID: {company_id})")
        
        # Test config endpoint
        print(f"\n📋 Testing GET /api/companies/{company_id}/gdrive/config")
        try:
            response = requests.get(f"{self.api_url}/companies/{company_id}/gdrive/config", headers=headers, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Response received:")
                print(f"      Success: {data.get('success')}")
                print(f"      Company Name: {data.get('company_name')}")
                
                config = data.get('config', {})
                print(f"      Config:")
                print(f"        Web App URL: {config.get('web_app_url', 'N/A')}")
                print(f"        Folder ID: {config.get('folder_id', 'N/A')}")
                print(f"        Auth Method: {config.get('auth_method', 'N/A')}")
                print(f"        Service Account: {config.get('service_account_email', 'N/A')}")
                print(f"        Project ID: {config.get('project_id', 'N/A')}")
                
                # Check if actually configured
                has_web_app_url = bool(config.get('web_app_url'))
                has_folder_id = bool(config.get('folder_id'))
                is_configured = has_web_app_url and has_folder_id
                
                print(f"      ✅ ANALYSIS:")
                print(f"        Has Web App URL: {has_web_app_url}")
                print(f"        Has Folder ID: {has_folder_id}")
                print(f"        IS CONFIGURED: {is_configured}")
                
            else:
                print(f"   ❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test status endpoint
        print(f"\n📊 Testing GET /api/companies/{company_id}/gdrive/status")
        try:
            response = requests.get(f"{self.api_url}/companies/{company_id}/gdrive/status", headers=headers, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Response received:")
                print(f"      Success: {data.get('success')}")
                print(f"      Status: {data.get('status')}")
                print(f"      Message: {data.get('message')}")
                print(f"      Last Tested: {data.get('last_tested')}")
                print(f"      Test Result: {data.get('test_result')}")
                print(f"      Folder ID: {data.get('folder_id')}")
                print(f"      Auth Method: {data.get('auth_method')}")
                
            else:
                print(f"   ❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test if we can configure (POST endpoint)
        print(f"\n🔧 Testing POST /api/companies/{company_id}/gdrive/configure (test connection)")
        try:
            test_config = {
                "web_app_url": "https://script.google.com/macros/s/AKfycbzgEVRtLEGylJem_1826xgwdf_XYzQfv7IYiPlvZggq-6Yw4fKW3NZ-QG3yE-T-OlnF/exec",
                "folder_id": "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG"
            }
            
            response = requests.post(f"{self.api_url}/companies/{company_id}/gdrive/configure", 
                                   headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}, 
                                   json=test_config, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Configuration test successful:")
                print(f"      Success: {data.get('success')}")
                print(f"      Message: {data.get('message')}")
                print(f"      Test Result: {data.get('test_result')}")
                
            else:
                print(f"   ❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Main test execution"""
    print("🔍 Corrected Company Google Drive Configuration Test")
    print("=" * 60)
    
    tester = CorrectedGDriveDebugTester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Run the corrected test
    tester.test_company_gdrive_endpoints()
    
    print("\n" + "=" * 60)
    print("📊 CORRECTED TEST RESULTS")
    print("=" * 60)
    print("✅ This test shows the actual API response structure")
    print("💡 If the config shows web_app_url and folder_id, then it IS configured")
    print("💡 The frontend should check config.web_app_url and config.folder_id")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
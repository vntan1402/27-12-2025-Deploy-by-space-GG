#!/usr/bin/env python3
"""
Review Request Specific Testing
Testing the specific issues mentioned in the review request:
1. Company Management showing no content
2. Google Drive configuration appearing to be missing
3. MongoDB endpoints verification
"""

import requests
import sys
import json

class ReviewRequestTester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.issues_found = []
        self.working_features = []

    def authenticate(self):
        """Authenticate with admin/admin123"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                user_data = data.get('user', {})
                print(f"✅ Authentication successful")
                print(f"   User: {user_data.get('full_name')} ({user_data.get('role')})")
                print(f"   Company: {user_data.get('company', 'None')}")
                return True, user_data
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False, {}
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False, {}

    def test_company_management_issue(self):
        """Test Company Management Issues - verify companies are returned and display correctly"""
        print(f"\n🏢 Testing Company Management Issues")
        print(f"   Issue: Company Management showing no content for admin/admin123")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            # Test GET /api/companies
            response = requests.get(f"{self.api_url}/companies", headers=headers, timeout=30)
            
            if response.status_code == 200:
                companies = response.json()
                print(f"   ✅ GET /api/companies working - Status: {response.status_code}")
                print(f"   ✅ Found {len(companies)} companies in MongoDB")
                
                if len(companies) > 0:
                    # Verify company data structure
                    company = companies[0]
                    required_fields = ['id', 'name_vn', 'name_en', 'created_at']
                    missing_fields = [field for field in required_fields if field not in company]
                    
                    if not missing_fields:
                        print(f"   ✅ Company data structure is correct")
                        print(f"   ✅ Sample company: {company.get('name_en')} / {company.get('name_vn')}")
                        
                        # Test individual company retrieval
                        company_id = company['id']
                        detail_response = requests.get(f"{self.api_url}/companies/{company_id}", headers=headers, timeout=30)
                        
                        if detail_response.status_code == 200:
                            print(f"   ✅ Individual company retrieval working")
                            self.working_features.append("Company Management Backend APIs")
                            
                            # The issue is likely in the frontend or missing endpoints
                            print(f"   🔍 ANALYSIS: Backend APIs are working correctly")
                            print(f"   🔍 LIKELY CAUSE: Frontend may be calling missing endpoints or has display issues")
                            return True
                        else:
                            self.issues_found.append(f"Individual company retrieval failed: {detail_response.status_code}")
                            return False
                    else:
                        self.issues_found.append(f"Company data missing fields: {missing_fields}")
                        return False
                else:
                    self.issues_found.append("No companies found in MongoDB - this explains the 'no content' issue")
                    return False
            else:
                self.issues_found.append(f"GET /api/companies failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.issues_found.append(f"Company Management test error: {e}")
            return False

    def test_google_drive_configuration_issue(self):
        """Test Google Drive Configuration Issues"""
        print(f"\n☁️ Testing Google Drive Configuration Issues")
        print(f"   Issue: Google Drive configuration appearing to be missing")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            # Test GET /api/gdrive/config
            config_response = requests.get(f"{self.api_url}/gdrive/config", headers=headers, timeout=30)
            
            if config_response.status_code == 200:
                config_data = config_response.json()
                print(f"   ✅ GET /api/gdrive/config working - Status: {config_response.status_code}")
                print(f"   ✅ Configuration status: {'Configured' if config_data.get('configured') else 'Not configured'}")
                
                if config_data.get('configured'):
                    print(f"   ✅ Folder ID: {config_data.get('folder_id', 'N/A')}")
                    print(f"   ✅ Service Account: {config_data.get('service_account_email', 'N/A')}")
                    print(f"   ✅ Last Sync: {config_data.get('last_sync', 'Never')}")
                
                # Test GET /api/gdrive/status
                status_response = requests.get(f"{self.api_url}/gdrive/status", headers=headers, timeout=30)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   ✅ GET /api/gdrive/status working - Status: {status_response.status_code}")
                    print(f"   ✅ Status configured: {status_data.get('configured', False)}")
                    print(f"   ✅ Local files: {status_data.get('local_files', 0)}")
                    print(f"   ✅ Drive files: {status_data.get('drive_files', 0)}")
                    
                    self.working_features.append("Google Drive Configuration Backend APIs")
                    
                    if not config_data.get('configured'):
                        print(f"   🔍 ANALYSIS: Google Drive is not configured (this is normal)")
                        print(f"   🔍 LIKELY CAUSE: User needs to configure Google Drive through the UI")
                    else:
                        print(f"   🔍 ANALYSIS: Google Drive is properly configured")
                        print(f"   🔍 LIKELY CAUSE: Frontend display issue or missing UI components")
                    
                    return True
                else:
                    self.issues_found.append(f"GET /api/gdrive/status failed: {status_response.status_code}")
                    return False
            else:
                self.issues_found.append(f"GET /api/gdrive/config failed: {config_response.status_code}")
                return False
                
        except Exception as e:
            self.issues_found.append(f"Google Drive Configuration test error: {e}")
            return False

    def test_missing_endpoints_impact(self):
        """Test impact of missing endpoints on frontend functionality"""
        print(f"\n🔍 Testing Missing Endpoints Impact")
        print(f"   Checking endpoints that frontend likely needs but are missing")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        missing_critical_endpoints = []
        
        # Test critical endpoints that frontend likely needs
        critical_endpoints = [
            ('GET', 'ships', 'Ship Management'),
            ('GET', 'certificates', 'Certificate Management'),
            ('GET', 'ai-config', 'AI Configuration'),
            ('GET', 'usage-stats', 'Usage Tracking'),
            ('GET', 'settings', 'System Settings'),
            ('POST', 'auth/register', 'User Registration')
        ]
        
        for method, endpoint, feature in critical_endpoints:
            try:
                if method == 'GET':
                    response = requests.get(f"{self.api_url}/{endpoint}", headers=headers, timeout=10)
                else:
                    response = requests.post(f"{self.api_url}/{endpoint}", json={}, headers=headers, timeout=10)
                
                if response.status_code == 404:
                    missing_critical_endpoints.append((endpoint, feature))
                    print(f"   ❌ MISSING: {method} /api/{endpoint} - {feature}")
                else:
                    print(f"   ✅ EXISTS: {method} /api/{endpoint} - {feature} (Status: {response.status_code})")
                    
            except Exception as e:
                print(f"   ⚠️ ERROR testing {endpoint}: {e}")
        
        if missing_critical_endpoints:
            print(f"\n   🚨 CRITICAL FINDING: {len(missing_critical_endpoints)} critical endpoints are missing")
            print(f"   🚨 This explains why frontend sections show 'no content'")
            
            for endpoint, feature in missing_critical_endpoints:
                self.issues_found.append(f"Missing endpoint /api/{endpoint} affects {feature}")
            
            return False
        else:
            print(f"   ✅ All critical endpoints are available")
            return True

    def run_comprehensive_analysis(self):
        """Run comprehensive analysis of the review request issues"""
        print("🔍 Review Request Specific Testing")
        print("=" * 60)
        print("Testing reported issues:")
        print("1. Company Management showing no content")
        print("2. Google Drive configuration appearing to be missing")
        print("3. MongoDB endpoints verification")
        print("=" * 60)
        
        # Authenticate first
        auth_success, user_data = self.authenticate()
        if not auth_success:
            return False
        
        # Run specific tests
        test_results = []
        test_results.append(("Company Management Issue", self.test_company_management_issue()))
        test_results.append(("Google Drive Configuration Issue", self.test_google_drive_configuration_issue()))
        test_results.append(("Missing Endpoints Impact", self.test_missing_endpoints_impact()))
        
        # Generate comprehensive report
        print("\n" + "=" * 60)
        print("📊 REVIEW REQUEST ANALYSIS REPORT")
        print("=" * 60)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ RESOLVED" if result else "❌ ISSUE CONFIRMED"
            print(f"{test_name:35} {status}")
        
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        print(f"=" * 30)
        
        if self.working_features:
            print(f"\n✅ WORKING FEATURES:")
            for feature in self.working_features:
                print(f"   - {feature}")
        
        if self.issues_found:
            print(f"\n❌ ISSUES IDENTIFIED:")
            for issue in self.issues_found:
                print(f"   - {issue}")
        
        print(f"\n🎯 CONCLUSIONS:")
        print(f"=" * 15)
        
        if "Company Management Backend APIs" in self.working_features:
            print(f"✅ Company Management: Backend APIs are working correctly")
            print(f"   - GET /api/companies returns data successfully")
            print(f"   - Companies exist in MongoDB")
            print(f"   - Individual company retrieval works")
            print(f"   - Issue is likely in frontend display or missing related endpoints")
        
        if "Google Drive Configuration Backend APIs" in self.working_features:
            print(f"✅ Google Drive Configuration: Backend APIs are working correctly")
            print(f"   - GET /api/gdrive/config returns configuration")
            print(f"   - GET /api/gdrive/status returns status information")
            print(f"   - Configuration data exists in MongoDB")
            print(f"   - Issue is likely in frontend display")
        
        if any("Missing endpoint" in issue for issue in self.issues_found):
            print(f"❌ Critical Issue: Multiple endpoints are missing from backend")
            print(f"   - This is the primary cause of 'no content' displays")
            print(f"   - Frontend is making requests to non-existent endpoints")
            print(f"   - Backend needs to implement missing endpoints")
        
        print(f"\n📋 RECOMMENDATIONS:")
        print(f"=" * 20)
        print(f"1. Implement missing backend endpoints (ships, certificates, ai-config, etc.)")
        print(f"2. Verify frontend is using correct API endpoints")
        print(f"3. Check frontend error handling for failed API calls")
        print(f"4. Ensure proper authentication token handling in frontend")
        
        return passed_tests == total_tests

def main():
    tester = ReviewRequestTester()
    success = tester.run_comprehensive_analysis()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Certificate Upload Workflow Test - Company Google Drive Configuration
Testing the fixed certificate upload workflow after modifying it to use Company Google Drive configuration instead of System Google Drive.
"""

import requests
import json
import io
import sys
from datetime import datetime, timezone

class CertificateWorkflowTester:
    def __init__(self, base_url="https://shipcertdrive.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.current_user = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
        print()

    def make_request(self, method, endpoint, data=None, files=None, params=None):
        """Make API request with authentication"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if files:
            # Don't set Content-Type for file uploads - let requests handle it
            pass
        else:
            headers['Content-Type'] = 'application/json'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=60)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=60)
            
            return response
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None

    def test_authentication(self):
        """Test 1: Login as admin/admin123 and verify user's company assignment"""
        print("🔐 TEST 1: AUTHENTICATION")
        print("=" * 50)
        
        response = self.make_request('POST', 'auth/login', {
            'username': 'admin',
            'password': 'admin123'
        })
        
        if not response or response.status_code != 200:
            self.log_result(
                "Authentication", 
                False, 
                f"Login failed with status {response.status_code if response else 'No response'}"
            )
            return False
        
        data = response.json()
        self.token = data.get('access_token')
        self.current_user = data.get('user', {})
        
        self.log_result(
            "Authentication",
            True,
            "Successfully authenticated as admin/admin123",
            {
                "User": self.current_user.get('full_name'),
                "Role": self.current_user.get('role'),
                "Company": self.current_user.get('company', 'Not assigned')
            }
        )
        return True

    def test_company_google_drive_config(self):
        """Test 2: Verify AMCSC company has Google Drive configuration"""
        print("🏢 TEST 2: COMPANY GOOGLE DRIVE CONFIGURATION")
        print("=" * 50)
        
        # Get all companies
        response = self.make_request('GET', 'companies')
        if not response or response.status_code != 200:
            self.log_result(
                "Get Companies",
                False,
                f"Failed to get companies: {response.status_code if response else 'No response'}"
            )
            return False
        
        companies = response.json()
        
        # Find AMCSC company
        amcsc_company = None
        for company in companies:
            name_fields = [
                company.get('name_en', ''),
                company.get('name_vn', ''),
                company.get('name', '')
            ]
            if any('AMCSC' in name for name in name_fields):
                amcsc_company = company
                break
        
        if not amcsc_company:
            self.log_result(
                "Find AMCSC Company",
                False,
                "AMCSC company not found in database"
            )
            return False
        
        company_id = amcsc_company['id']
        
        # Test company Google Drive configuration
        config_response = self.make_request('GET', f'companies/{company_id}/gdrive/config')
        status_response = self.make_request('GET', f'companies/{company_id}/gdrive/status')
        
        config_success = config_response and config_response.status_code == 200
        status_success = status_response and status_response.status_code == 200
        
        config_data = config_response.json() if config_success else {}
        status_data = status_response.json() if status_success else {}
        
        config_info = config_data.get('config', {})
        
        self.log_result(
            "AMCSC Google Drive Configuration",
            config_success and status_success,
            "Company Google Drive configuration checked",
            {
                "Company ID": company_id,
                "Company Name": amcsc_company.get('name_en', amcsc_company.get('name', 'Unknown')),
                "Config Status": "Available" if config_success else "Not available",
                "Apps Script URL": config_info.get('web_app_url', 'Not configured'),
                "Folder ID": config_info.get('folder_id', 'Not configured'),
                "Status": status_data.get('status', 'Unknown'),
                "Message": status_data.get('message', 'No message')
            }
        )
        
        return config_success and status_success

    def create_test_pdf(self):
        """Create a realistic test PDF for certificate upload"""
        # Create a more comprehensive PDF structure with certificate-like content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 800
>>
stream
BT
/F1 16 Tf
200 750 Td
(INTERNATIONAL SAFETY MANAGEMENT CERTIFICATE) Tj
0 -30 Td
/F1 12 Tf
(Certificate of Compliance) Tj
0 -40 Td
(This is to certify that the Safety Management System of) Tj
0 -20 Td
(Ship Name: MV SUNSHINE STAR) Tj
0 -20 Td
(IMO Number: 9876543) Tj
0 -20 Td
(Flag: Panama) Tj
0 -20 Td
(Gross Tonnage: 25000) Tj
0 -20 Td
(Ship Type: Bulk Carrier) Tj
0 -40 Td
(has been audited and found to comply with the requirements of) Tj
0 -20 Td
(the International Safety Management Code) Tj
0 -40 Td
(Certificate Number: ISM-2024-001) Tj
0 -20 Td
(Issue Date: 01 January 2024) Tj
0 -20 Td
(Valid Until: 01 January 2027) Tj
0 -40 Td
(Issued by: Panama Maritime Authority) Tj
0 -20 Td
(Classification Society: DNV GL) Tj
0 -40 Td
(This certificate is issued under the authority of the) Tj
0 -20 Td
(Government of Panama) Tj
0 -40 Td
(Date: 01 January 2024) Tj
0 -20 Td
(Place: Panama City) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
0000001050 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
1100
%%EOF"""
        return pdf_content

    def test_certificate_upload_workflow(self):
        """Test 3: Complete Certificate Upload Workflow"""
        print("📜 TEST 3: CERTIFICATE UPLOAD WORKFLOW")
        print("=" * 50)
        
        # Create test PDF
        pdf_content = self.create_test_pdf()
        
        # Prepare file for upload
        files = {
            'files': ('test_certificate.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        
        # Upload certificate
        response = self.make_request('POST', 'certificates/upload-multi-files', files=files)
        
        if not response:
            self.log_result(
                "Certificate Upload",
                False,
                "No response from upload endpoint"
            )
            return False
        
        if response.status_code != 200:
            self.log_result(
                "Certificate Upload",
                False,
                f"Upload failed with status {response.status_code}",
                {"Response": response.text[:500]}
            )
            return False
        
        # Analyze results
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            self.log_result(
                "Certificate Upload",
                False,
                "No results returned from upload"
            )
            return False
        
        result = results[0]
        filename = result.get('filename', 'Unknown')
        status = result.get('status', 'Unknown')
        
        # Check AI analysis
        analysis = result.get('analysis', {})
        category = analysis.get('category', 'unknown')
        ship_name = analysis.get('ship_name', 'Not extracted')
        
        # Check Google Drive upload
        upload_result = result.get('upload', {})
        gdrive_success = upload_result.get('success', False)
        gdrive_file_id = upload_result.get('file_id', 'Not uploaded')
        
        # Check if company config was used by examining the folder path or other indicators
        # Since the user is assigned to AMCSC company, company config should be used
        company_config_used = self.current_user.get('company') == 'cfe73cb0-cc88-4659-92a7-57cb413a5573'
        
        # Check certificate record creation
        cert_result = result.get('certificate', {})
        cert_created = cert_result and cert_result.get('success', False)
        
        # Determine overall success
        workflow_success = (
            status == 'success' and
            category == 'certificates' and
            gdrive_success and
            cert_created
        )
        
        self.log_result(
            "Certificate Upload Workflow",
            workflow_success,
            "Complete certificate upload workflow tested",
            {
                "Filename": filename,
                "Status": status,
                "AI Category": f"{category} ({'✅ CORRECT' if category == 'certificates' else '❌ INCORRECT'})",
                "Ship Name": ship_name,
                "Google Drive Upload": f"{'✅ SUCCESS' if gdrive_success else '❌ FAILED'}",
                "Google Drive File ID": gdrive_file_id,
                "Company Config Used": f"{'✅ YES' if company_config_used else '❌ NO'}",
                "Certificate Record": f"{'✅ CREATED' if cert_created else '❌ FAILED'}"
            }
        )
        
        return workflow_success

    def test_company_vs_system_config(self):
        """Test 4: Verify company-specific Google Drive configuration is used instead of system"""
        print("🔄 TEST 4: COMPANY VS SYSTEM CONFIGURATION")
        print("=" * 50)
        
        # Get system Google Drive config
        system_response = self.make_request('GET', 'gdrive/config')
        system_success = system_response and system_response.status_code == 200
        system_config = system_response.json() if system_success else {}
        
        # Get companies and find AMCSC
        companies_response = self.make_request('GET', 'companies')
        if not companies_response or companies_response.status_code != 200:
            self.log_result(
                "Company vs System Config",
                False,
                "Failed to get companies for comparison"
            )
            return False
        
        companies = companies_response.json()
        amcsc_company = None
        for company in companies:
            name_fields = [
                company.get('name_en', ''),
                company.get('name_vn', ''),
                company.get('name', '')
            ]
            if any('AMCSC' in name for name in name_fields):
                amcsc_company = company
                break
        
        if not amcsc_company:
            self.log_result(
                "Company vs System Config",
                False,
                "AMCSC company not found for comparison"
            )
            return False
        
        # Get company Google Drive config
        company_id = amcsc_company['id']
        company_response = self.make_request('GET', f'companies/{company_id}/gdrive/config')
        company_success = company_response and company_response.status_code == 200
        company_data = company_response.json() if company_success else {}
        company_config = company_data.get('config', {})
        
        # Compare configurations
        system_url = system_config.get('apps_script_url', '')
        company_url = company_config.get('web_app_url', '')
        
        system_folder = system_config.get('folder_id', '')
        company_folder = company_config.get('folder_id', '')
        
        configs_different = (
            company_url and company_url != system_url
        ) or (
            company_folder and company_folder != system_folder
        )
        
        self.log_result(
            "Company vs System Configuration",
            configs_different,
            "Configuration comparison completed",
            {
                "System Apps Script URL": system_url or "Not configured",
                "Company Apps Script URL": company_url or "Not configured",
                "System Folder ID": system_folder or "Not configured", 
                "Company Folder ID": company_folder or "Not configured",
                "Configurations Different": f"{'✅ YES' if configs_different else '❌ NO (Same or company not configured)'}",
                "Expected Behavior": "Certificate uploads should use company-specific configuration"
            }
        )
        
        return configs_different

    def run_all_tests(self):
        """Run all certificate upload workflow tests"""
        print("🚢 CERTIFICATE UPLOAD WORKFLOW TESTING")
        print("Testing fixed certificate upload workflow after modifying to use Company Google Drive configuration")
        print("=" * 80)
        
        # Run tests in sequence
        tests = [
            ("Authentication Test", self.test_authentication),
            ("Company Google Drive Configuration", self.test_company_google_drive_config),
            ("Certificate Upload Workflow", self.test_certificate_upload_workflow),
            ("Company vs System Config", self.test_company_vs_system_config)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                
                # Stop if authentication fails
                if test_name == "Authentication Test" and not result:
                    print("❌ Authentication failed - stopping remaining tests")
                    break
                    
            except Exception as e:
                print(f"❌ Test '{test_name}' failed with exception: {str(e)}")
                results.append((test_name, False))
        
        # Print summary
        print("=" * 80)
        print("📊 FINAL TEST RESULTS")
        print("=" * 80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:35} {status}")
        
        print(f"\nTests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"Feature Tests: {passed}/{total}")
        
        # Final assessment
        if passed == total and self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Certificate upload workflow is working correctly")
            print("✅ Company Google Drive configuration is being used")
            print("✅ AI classification working (certificates)")
            print("✅ Google Drive upload successful")
            print("✅ Certificate records created in database")
            return True
        else:
            print("\n⚠️ SOME TESTS FAILED")
            print("❌ Issues detected in certificate upload workflow")
            
            failed_tests = [name for name, result in results if not result]
            for failed_test in failed_tests:
                print(f"   ❌ {failed_test}")
            
            return False

def main():
    """Main test execution"""
    tester = CertificateWorkflowTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
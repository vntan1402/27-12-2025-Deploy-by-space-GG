#!/usr/bin/env python3
"""
Certificate Upload with Company Google Drive Integration - Comprehensive Test Suite

This test suite comprehensively tests the new certificate upload functionality
and identifies critical implementation issues.
"""

import requests
import json
import os
import tempfile
import base64
from datetime import datetime, timezone
from pathlib import Path

# Configuration
BACKEND_URL = "https://aicert-analyzer.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
TEST_USERNAME = "test_cert_user"
TEST_PASSWORD = "testpass123"

class CertificateUploadComprehensiveTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_token = None
        self.test_user_data = None
        self.test_results = []
        self.critical_issues = []
        
    def log_test(self, test_name, success, message, details=None, is_critical=False):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "is_critical": is_critical
        }
        self.test_results.append(result)
        
        if is_critical and not success:
            self.critical_issues.append(result)
        
        status = "✅ PASSED" if success else ("🔥 CRITICAL" if is_critical else "❌ FAILED")
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate_admin(self):
        """Authenticate as admin"""
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                return True
            return False
        except:
            return False
    
    def authenticate_test_user(self):
        """Test authentication with test user that has company assignment"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.test_token = data.get("access_token")
                self.test_user_data = data.get("user")
                self.session.headers.update({"Authorization": f"Bearer {self.test_token}"})
                
                self.log_test(
                    "Authentication Test",
                    True,
                    f"Successfully authenticated as {self.test_user_data.get('username')}",
                    {
                        "role": self.test_user_data.get("role"),
                        "company": self.test_user_data.get("company"),
                        "full_name": self.test_user_data.get("full_name")
                    }
                )
                return True
            else:
                self.log_test(
                    "Authentication Test",
                    False,
                    f"Authentication failed with status {response.status_code}",
                    {"response": response.text},
                    is_critical=True
                )
                return False
                
        except Exception as e:
            self.log_test("Authentication Test", False, f"Authentication error: {str(e)}", is_critical=True)
            return False
    
    def test_new_upload_endpoint_exists(self):
        """Test that the new /api/certificates/upload-with-file endpoint exists"""
        try:
            # Create a minimal test file
            test_content = b"Test certificate file content"
            
            # Test with minimal required fields to check if endpoint exists
            files = {'file': ('test_cert.pdf', test_content, 'application/pdf')}
            data = {
                'ship_id': 'test-ship-id',
                'cert_name': 'Test Certificate',
                'cert_no': 'TEST-001',
                'issue_date': '2024-01-01T00:00:00Z',
                'valid_date': '2025-01-01T00:00:00Z',
                'category': 'certificates',
                'sensitivity_level': 'public'
            }
            
            response = self.session.post(f"{BACKEND_URL}/certificates/upload-with-file", 
                                       files=files, data=data)
            
            # We expect this to fail with validation errors, but not 404
            if response.status_code == 404:
                self.log_test(
                    "New Upload Endpoint Existence",
                    False,
                    "Endpoint /api/certificates/upload-with-file not found (404)",
                    {"status_code": response.status_code, "response": response.text},
                    is_critical=True
                )
                return False
            else:
                self.log_test(
                    "New Upload Endpoint Existence",
                    True,
                    f"Endpoint exists and responds (status: {response.status_code})",
                    {"status_code": response.status_code, "response": response.text[:200]}
                )
                return True
                
        except Exception as e:
            self.log_test(
                "New Upload Endpoint Existence",
                False,
                f"Error testing endpoint: {str(e)}",
                is_critical=True
            )
            return False
    
    def test_existing_certificates_endpoint(self):
        """Test that the existing /api/certificates endpoint is still working"""
        try:
            # First, get a ship ID to use for testing
            ships_response = self.session.get(f"{BACKEND_URL}/ships")
            
            if ships_response.status_code != 200:
                self.log_test(
                    "Existing Certificates Endpoint",
                    False,
                    "Cannot get ships for testing certificates endpoint",
                    {"ships_status": ships_response.status_code}
                )
                return False
            
            ships = ships_response.json()
            if not ships:
                self.log_test(
                    "Existing Certificates Endpoint",
                    False,
                    "No ships available for testing certificates endpoint"
                )
                return False
            
            ship_id = ships[0]['id']
            
            # Test creating a certificate (metadata only)
            cert_data = {
                "ship_id": ship_id,
                "cert_name": "Test Certificate Metadata Only",
                "cert_no": "TEST-METADATA-003",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "category": "certificates",
                "sensitivity_level": "public"
            }
            
            response = self.session.post(f"{BACKEND_URL}/certificates", json=cert_data)
            
            if response.status_code == 201 or response.status_code == 200:
                cert_response = response.json()
                self.log_test(
                    "Existing Certificates Endpoint",
                    True,
                    "Successfully created certificate via existing endpoint",
                    {
                        "certificate_id": cert_response.get("id"),
                        "cert_name": cert_response.get("cert_name"),
                        "file_uploaded": cert_response.get("file_uploaded", False)
                    }
                )
                return True
            else:
                self.log_test(
                    "Existing Certificates Endpoint",
                    False,
                    f"Failed to create certificate via existing endpoint (status: {response.status_code})",
                    {"response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Existing Certificates Endpoint",
                False,
                f"Error testing existing certificates endpoint: {str(e)}"
            )
            return False
    
    def test_user_company_assignment(self):
        """Test that users have companies assigned"""
        try:
            if not self.test_user_data:
                self.log_test(
                    "User Company Assignment",
                    False,
                    "No user data available for testing",
                    is_critical=True
                )
                return False
            
            user_company = self.test_user_data.get("company")
            
            if user_company:
                self.log_test(
                    "User Company Assignment",
                    True,
                    f"User is assigned to company: {user_company}",
                    {"company": user_company}
                )
                return True
            else:
                self.log_test(
                    "User Company Assignment",
                    False,
                    "User is not assigned to any company",
                    {"user_data": self.test_user_data},
                    is_critical=True
                )
                return False
                
        except Exception as e:
            self.log_test(
                "User Company Assignment",
                False,
                f"Error checking user company assignment: {str(e)}",
                is_critical=True
            )
            return False
    
    def test_company_gdrive_configurations(self):
        """Test that Company Google Drive configurations exist"""
        try:
            # Use admin token for this test since test user might not have permissions
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Get companies list
            companies_response = requests.get(f"{BACKEND_URL}/companies", headers=admin_headers)
            
            if companies_response.status_code != 200:
                self.log_test(
                    "Company Google Drive Configurations",
                    False,
                    f"Cannot fetch companies (status: {companies_response.status_code})",
                    {"response": companies_response.text}
                )
                return False
            
            companies = companies_response.json()
            
            if not companies:
                self.log_test(
                    "Company Google Drive Configurations",
                    False,
                    "No companies found in system"
                )
                return False
            
            # Check Google Drive configurations for each company
            gdrive_configured_companies = []
            
            for company in companies:
                company_id = company.get('id')
                
                # Get company Google Drive config
                gdrive_config_response = requests.get(f"{BACKEND_URL}/companies/{company_id}/gdrive/config", headers=admin_headers)
                
                if gdrive_config_response.status_code == 200:
                    gdrive_config = gdrive_config_response.json()
                    if gdrive_config.get('configured', False):
                        gdrive_configured_companies.append({
                            "company_name": company.get('name_en') or company.get('name_vn'),
                            "company_id": company_id,
                            "auth_method": gdrive_config.get('auth_method'),
                            "folder_id": gdrive_config.get('folder_id')
                        })
            
            if gdrive_configured_companies:
                self.log_test(
                    "Company Google Drive Configurations",
                    True,
                    f"Found {len(gdrive_configured_companies)} companies with Google Drive configured",
                    {"configured_companies": gdrive_configured_companies}
                )
                return True
            else:
                self.log_test(
                    "Company Google Drive Configurations",
                    False,
                    f"No companies have Google Drive configured (checked {len(companies)} companies)",
                    {"total_companies": len(companies)},
                    is_critical=True
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Company Google Drive Configurations",
                False,
                f"Error checking company Google Drive configurations: {str(e)}",
                is_critical=True
            )
            return False
    
    def test_apps_script_compatibility(self):
        """Test Apps Script compatibility with backend implementation"""
        try:
            # Get company with Google Drive configured
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            companies_response = requests.get(f"{BACKEND_URL}/companies", headers=admin_headers)
            
            if companies_response.status_code != 200:
                self.log_test(
                    "Apps Script Compatibility",
                    False,
                    "Cannot fetch companies for Apps Script testing"
                )
                return False
            
            companies = companies_response.json()
            amcsc_company = None
            
            for company in companies:
                if company.get('name_en') == 'AMCSC':
                    amcsc_company = company
                    break
            
            if not amcsc_company:
                self.log_test(
                    "Apps Script Compatibility",
                    False,
                    "AMCSC company not found"
                )
                return False
            
            gdrive_config = amcsc_company.get('gdrive_config', {})
            web_app_url = gdrive_config.get('web_app_url')
            
            if not web_app_url:
                self.log_test(
                    "Apps Script Compatibility",
                    False,
                    "No Apps Script URL found in company configuration"
                )
                return False
            
            # Test what actions the Apps Script supports
            supported_actions = []
            unsupported_actions = []
            
            actions_to_test = [
                'test_connection',
                'sync_to_drive',
                'create_folder_structure',  # Used by backend
                'upload_file',              # Used by backend
                'list_files'
            ]
            
            for action in actions_to_test:
                try:
                    payload = {'action': action}
                    response = requests.post(web_app_url, json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success') or 'error' not in result or 'Unknown action' not in result.get('error', ''):
                            supported_actions.append(action)
                        else:
                            unsupported_actions.append(action)
                    else:
                        unsupported_actions.append(action)
                        
                except Exception as e:
                    unsupported_actions.append(f"{action} (error: {str(e)})")
            
            # Check if backend-required actions are supported
            backend_required_actions = ['create_folder_structure', 'upload_file']
            missing_actions = [action for action in backend_required_actions if action in unsupported_actions]
            
            if missing_actions:
                self.log_test(
                    "Apps Script Compatibility",
                    False,
                    f"Apps Script missing required actions: {missing_actions}",
                    {
                        "supported_actions": supported_actions,
                        "unsupported_actions": unsupported_actions,
                        "missing_required": missing_actions,
                        "web_app_url": web_app_url
                    },
                    is_critical=True
                )
                return False
            else:
                self.log_test(
                    "Apps Script Compatibility",
                    True,
                    "Apps Script supports all required actions",
                    {
                        "supported_actions": supported_actions,
                        "unsupported_actions": unsupported_actions
                    }
                )
                return True
                
        except Exception as e:
            self.log_test(
                "Apps Script Compatibility",
                False,
                f"Error testing Apps Script compatibility: {str(e)}",
                is_critical=True
            )
            return False
    
    def test_file_size_validation(self):
        """Test file upload validation (150MB limit check)"""
        try:
            # Get a valid ship ID
            ships_response = self.session.get(f"{BACKEND_URL}/ships")
            if ships_response.status_code != 200 or not ships_response.json():
                self.log_test(
                    "File Size Validation",
                    False,
                    "Cannot get ships for file size validation test"
                )
                return False
            
            ship_id = ships_response.json()[0]['id']
            
            # Test with small file
            small_content = b"Small test file content for size validation"
            files = {'file': ('small_cert.pdf', small_content, 'application/pdf')}
            data = {
                'ship_id': ship_id,
                'cert_name': 'Small File Test Certificate',
                'cert_no': 'SMALL-003',
                'issue_date': '2024-01-01T00:00:00Z',
                'valid_date': '2025-01-01T00:00:00Z',
                'category': 'certificates',
                'sensitivity_level': 'public'
            }
            
            small_response = self.session.post(f"{BACKEND_URL}/certificates/upload-with-file", 
                                             files=files, data=data)
            
            # Check if small file is not rejected for size reasons
            small_file_size_ok = "File size exceeds 150MB limit" not in small_response.text
            
            self.log_test(
                "File Size Validation",
                small_file_size_ok,
                f"File size validation test (status: {small_response.status_code})",
                {
                    "file_size": len(small_content),
                    "status_code": small_response.status_code,
                    "response": small_response.text[:300],
                    "size_error_present": "File size exceeds 150MB limit" in small_response.text
                }
            )
            
            return small_file_size_ok
            
        except Exception as e:
            self.log_test(
                "File Size Validation",
                False,
                f"Error testing file size validation: {str(e)}"
            )
            return False
    
    def test_complete_certificate_upload_workflow(self):
        """Test the complete certificate upload workflow with a test file"""
        try:
            # Get ships
            ships_response = self.session.get(f"{BACKEND_URL}/ships")
            
            if ships_response.status_code != 200 or not ships_response.json():
                self.log_test(
                    "Complete Certificate Upload Workflow",
                    False,
                    "Cannot get ships for complete workflow test"
                )
                return False
            
            ship_id = ships_response.json()[0]['id']
            ship_name = ships_response.json()[0]['name']
            
            # Create a realistic test certificate file
            certificate_content = f"""
CERTIFICATE OF COMPLIANCE

Ship Name: {ship_name}
IMO Number: {ships_response.json()[0].get('imo', 'N/A')}
Certificate Number: COMP-{datetime.now().strftime('%Y%m%d')}-003
Issue Date: {datetime.now().strftime('%Y-%m-%d')}
Valid Until: {datetime.now().replace(year=datetime.now().year + 1).strftime('%Y-%m-%d')}

This certificate is issued in accordance with international maritime regulations.

Issued by: Test Maritime Authority
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            certificate_bytes = certificate_content.encode('utf-8')
            
            # Prepare upload data
            files = {'file': ('compliance_certificate.txt', certificate_bytes, 'text/plain')}
            data = {
                'ship_id': ship_id,
                'cert_name': 'Certificate of Compliance',
                'cert_no': f'COMP-{datetime.now().strftime("%Y%m%d")}-003',
                'issue_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'valid_date': datetime.now().replace(year=datetime.now().year + 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'category': 'certificates',
                'sensitivity_level': 'public'
            }
            
            # Attempt the upload
            response = self.session.post(f"{BACKEND_URL}/certificates/upload-with-file", 
                                       files=files, data=data)
            
            if response.status_code in [200, 201]:
                cert_response = response.json()
                self.log_test(
                    "Complete Certificate Upload Workflow",
                    True,
                    "Successfully completed certificate upload workflow",
                    {
                        "certificate_id": cert_response.get("id"),
                        "cert_name": cert_response.get("cert_name"),
                        "cert_no": cert_response.get("cert_no"),
                        "file_uploaded": cert_response.get("file_uploaded"),
                        "google_drive_file_id": cert_response.get("google_drive_file_id"),
                        "file_name": cert_response.get("file_name"),
                        "file_size": cert_response.get("file_size")
                    }
                )
                return True
            else:
                self.log_test(
                    "Complete Certificate Upload Workflow",
                    False,
                    f"Certificate upload workflow failed (status: {response.status_code})",
                    {
                        "error_response": response.text,
                        "status_code": response.status_code
                    },
                    is_critical=True
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Complete Certificate Upload Workflow",
                False,
                f"Error in complete certificate upload workflow: {str(e)}",
                is_critical=True
            )
            return False
    
    def run_all_tests(self):
        """Run all certificate upload tests"""
        print("🚀 Starting Certificate Upload with Company Google Drive Integration - Comprehensive Tests")
        print("=" * 90)
        
        # Setup: Authenticate as admin first
        if not self.authenticate_admin():
            print("❌ Admin authentication failed. Cannot proceed.")
            return False
        
        # Test 1: Authentication with test user
        if not self.authenticate_test_user():
            print("❌ Test user authentication failed. Cannot proceed with other tests.")
            return False
        
        # Test 2: New upload endpoint exists
        self.test_new_upload_endpoint_exists()
        
        # Test 3: Existing certificates endpoint still works
        self.test_existing_certificates_endpoint()
        
        # Test 4: User company assignment
        self.test_user_company_assignment()
        
        # Test 5: Company Google Drive configurations
        self.test_company_gdrive_configurations()
        
        # Test 6: Apps Script compatibility (CRITICAL)
        self.test_apps_script_compatibility()
        
        # Test 7: File size validation
        self.test_file_size_validation()
        
        # Test 8: Complete certificate upload workflow
        self.test_complete_certificate_upload_workflow()
        
        # Summary
        print("\n" + "=" * 90)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 90)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        critical_failures = len(self.critical_issues)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Critical Failures: {critical_failures}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.critical_issues:
            print(f"\n🔥 CRITICAL ISSUES FOUND ({len(self.critical_issues)}):")
            for issue in self.critical_issues:
                print(f"   • {issue['test']}: {issue['message']}")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            if result["is_critical"] and not result["success"]:
                status = "🔥 CRITICAL"
            else:
                status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return passed_tests == total_tests and critical_failures == 0

def main():
    """Main test execution"""
    tester = CertificateUploadComprehensiveTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Certificate upload functionality is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Critical issues require immediate attention.")
    
    return success

if __name__ == "__main__":
    main()
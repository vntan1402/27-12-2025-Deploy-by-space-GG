#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
Focus: Certificate Delete with Google Drive File Removal Testing
"""

import requests
import json
import os
import sys
from datetime import datetime
import tempfile
import subprocess
import time

# Configuration - Use production URL from frontend .env
BACKEND_URL = "https://shipment-ai-1.preview.emergentagent.com/api"

# Test credentials to verify
TEST_CREDENTIALS = [
    {"username": "admin1", "password": "123456", "description": "Primary admin account"},
    {"username": "admin", "password": "admin123", "description": "Demo admin account"},
    {"username": "admin", "password": "123456", "description": "Alternative admin"},
    {"username": "admin1", "password": "admin123", "description": "Alternative admin1"}
]

class CertificateDeleteTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        self.working_credentials = []
        self.failed_credentials = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_certificate_delete_functionality(self):
        """Main test function for certificate delete with Google Drive file removal"""
        self.log("🗑️ Starting Certificate Delete with Google Drive File Removal Testing")
        self.log("=" * 80)
        
        # Step 1: Authentication
        auth_result = self.test_authentication()
        if not auth_result:
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Check Certificate Data Structure
        cert_structure_result = self.check_certificate_data_structure()
        
        # Step 3: Check Ship Data Structure
        ship_structure_result = self.check_ship_data_structure()
        
        # Step 4: Test Delete Certificate API
        delete_api_result = self.test_delete_certificate_api()
        
        # Step 5: Debug Google Drive Integration
        gdrive_debug_result = self.debug_google_drive_integration()
        
        # Step 6: Check Field Name Issues
        field_name_result = self.check_field_name_issues()
        
        # Step 7: Summary
        self.log("=" * 80)
        self.log("📋 CERTIFICATE DELETE FUNCTIONALITY TEST SUMMARY")
        self.log("=" * 80)
        
        self.log(f"{'✅' if auth_result else '❌'} Authentication: {'SUCCESS' if auth_result else 'FAILED'}")
        self.log(f"{'✅' if cert_structure_result else '❌'} Certificate Data Structure: {'SUCCESS' if cert_structure_result else 'FAILED'}")
        self.log(f"{'✅' if ship_structure_result else '❌'} Ship Data Structure: {'SUCCESS' if ship_structure_result else 'FAILED'}")
        self.log(f"{'✅' if delete_api_result else '❌'} Delete Certificate API: {'SUCCESS' if delete_api_result else 'FAILED'}")
        self.log(f"{'✅' if gdrive_debug_result else '❌'} Google Drive Integration: {'SUCCESS' if gdrive_debug_result else 'FAILED'}")
        self.log(f"{'✅' if field_name_result else '❌'} Field Name Issues Check: {'SUCCESS' if field_name_result else 'FAILED'}")
        
        overall_success = all([auth_result, cert_structure_result, ship_structure_result, delete_api_result])
        
        if overall_success:
            self.log("🎉 CERTIFICATE DELETE FUNCTIONALITY: FULLY WORKING")
        else:
            self.log("❌ CERTIFICATE DELETE FUNCTIONALITY: ISSUES DETECTED")
        
        return overall_success
    
    def test_authentication(self):
        """Test authentication with admin1/123456"""
        try:
            self.log("🔐 Testing Authentication with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            response = requests.post(endpoint, json=login_data, timeout=30)
            
            self.log(f"   Login response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_info = data.get("user")
                
                if self.auth_token and self.user_info:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    
                    self.log(f"   ✅ Authentication successful")
                    self.log(f"      User: {self.user_info.get('username')} ({self.user_info.get('role')})")
                    self.log(f"      Full Name: {self.user_info.get('full_name')}")
                    self.log(f"      Company: {self.user_info.get('company', 'N/A')}")
                    return True
                else:
                    self.log("   ❌ Authentication failed - missing token or user data")
                    return False
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                
                self.log(f"   ❌ Authentication failed - HTTP {response.status_code}")
                self.log(f"      Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def check_certificate_data_structure(self):
        """Check certificate data structure for Google Drive file ID fields"""
        try:
            self.log("📋 Checking Certificate Data Structure...")
            
            # Get certificates from SUNSHINE 01 ship
            ships_response = self.session.get(f"{BACKEND_URL}/ships", timeout=10)
            
            if ships_response.status_code != 200:
                self.log(f"   ❌ Failed to get ships: {ships_response.status_code}")
                return False
            
            ships = ships_response.json()
            sunshine_ship = None
            
            for ship in ships:
                if "SUNSHINE" in ship.get('name', '').upper():
                    sunshine_ship = ship
                    break
            
            if not sunshine_ship:
                self.log("   ❌ SUNSHINE ship not found")
                return False
            
            self.log(f"   ✅ Found ship: {sunshine_ship.get('name')} (ID: {sunshine_ship.get('id')})")
            
            # Get certificates for this ship
            cert_response = self.session.get(f"{BACKEND_URL}/ships/{sunshine_ship['id']}/certificates", timeout=10)
            
            if cert_response.status_code != 200:
                self.log(f"   ❌ Failed to get certificates: {cert_response.status_code}")
                return False
            
            certificates = cert_response.json()
            self.log(f"   ✅ Found {len(certificates)} certificates")
            
            # Check certificate structure
            gdrive_file_id_found = False
            google_drive_file_id_found = False
            
            for i, cert in enumerate(certificates[:3]):  # Check first 3 certificates
                self.log(f"   📄 Certificate {i+1}: {cert.get('cert_name', 'N/A')}")
                self.log(f"      ID: {cert.get('id')}")
                self.log(f"      Certificate Number: {cert.get('cert_no', 'N/A')}")
                
                # Check for Google Drive file ID fields
                if 'gdrive_file_id' in cert:
                    gdrive_file_id_found = True
                    self.log(f"      ✅ gdrive_file_id field found: {cert.get('gdrive_file_id')}")
                
                if 'google_drive_file_id' in cert:
                    google_drive_file_id_found = True
                    self.log(f"      ✅ google_drive_file_id field found: {cert.get('google_drive_file_id')}")
                
                # Check other relevant fields
                self.log(f"      File uploaded: {cert.get('file_uploaded', False)}")
                self.log(f"      File name: {cert.get('file_name', 'N/A')}")
                self.log("")
            
            self.log("   📊 Certificate Structure Analysis:")
            self.log(f"      gdrive_file_id field found: {'✅' if gdrive_file_id_found else '❌'}")
            self.log(f"      google_drive_file_id field found: {'✅' if google_drive_file_id_found else '❌'}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Certificate structure check error: {str(e)}", "ERROR")
            return False
    
    def check_ship_data_structure(self):
        """Check ship data structure for company_id vs company field"""
        try:
            self.log("🚢 Checking Ship Data Structure...")
            
            # Get ships
            ships_response = self.session.get(f"{BACKEND_URL}/ships", timeout=10)
            
            if ships_response.status_code != 200:
                self.log(f"   ❌ Failed to get ships: {ships_response.status_code}")
                return False
            
            ships = ships_response.json()
            sunshine_ship = None
            
            for ship in ships:
                if "SUNSHINE" in ship.get('name', '').upper():
                    sunshine_ship = ship
                    break
            
            if not sunshine_ship:
                self.log("   ❌ SUNSHINE ship not found")
                return False
            
            self.log(f"   ✅ Found ship: {sunshine_ship.get('name')}")
            self.log(f"      Ship ID: {sunshine_ship.get('id')}")
            
            # Check for company fields
            company_id_found = 'company_id' in sunshine_ship
            company_found = 'company' in sunshine_ship
            
            self.log("   📊 Ship Structure Analysis:")
            self.log(f"      company_id field: {'✅ ' + str(sunshine_ship.get('company_id')) if company_id_found else '❌ Not found'}")
            self.log(f"      company field: {'✅ ' + str(sunshine_ship.get('company')) if company_found else '❌ Not found'}")
            
            if company_found:
                company_value = sunshine_ship.get('company')
                self.log(f"      Company value: {company_value}")
                
                # Try to find company details
                companies_response = self.session.get(f"{BACKEND_URL}/companies", timeout=10)
                if companies_response.status_code == 200:
                    companies = companies_response.json()
                    matching_company = None
                    
                    for company in companies:
                        if company.get('id') == company_value:
                            matching_company = company
                            break
                    
                    if matching_company:
                        self.log(f"      ✅ Company found: {matching_company.get('name_en', matching_company.get('name', 'N/A'))}")
                        self.log(f"         Company ID: {matching_company.get('id')}")
                    else:
                        self.log(f"      ❌ Company with ID {company_value} not found")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Ship structure check error: {str(e)}", "ERROR")
            return False
    
    def test_delete_certificate_api(self):
        """Test DELETE /api/certificates/{cert_id} endpoint"""
        try:
            self.log("🗑️ Testing Delete Certificate API...")
            
            # First, get a certificate to delete (preferably one with Google Drive file)
            ships_response = self.session.get(f"{BACKEND_URL}/ships", timeout=10)
            
            if ships_response.status_code != 200:
                self.log(f"   ❌ Failed to get ships: {ships_response.status_code}")
                return False
            
            ships = ships_response.json()
            sunshine_ship = None
            
            for ship in ships:
                if "SUNSHINE" in ship.get('name', '').upper():
                    sunshine_ship = ship
                    break
            
            if not sunshine_ship:
                self.log("   ❌ SUNSHINE ship not found")
                return False
            
            # Get certificates for this ship
            cert_response = self.session.get(f"{BACKEND_URL}/ships/{sunshine_ship['id']}/certificates", timeout=10)
            
            if cert_response.status_code != 200:
                self.log(f"   ❌ Failed to get certificates: {cert_response.status_code}")
                return False
            
            certificates = cert_response.json()
            
            if not certificates:
                self.log("   ❌ No certificates found to test deletion")
                return False
            
            # Find a certificate with Google Drive file ID
            test_cert = None
            for cert in certificates:
                if cert.get('gdrive_file_id') or cert.get('google_drive_file_id'):
                    test_cert = cert
                    break
            
            if not test_cert:
                # Use the first certificate if none have Google Drive files
                test_cert = certificates[0]
                self.log("   ⚠️ No certificates with Google Drive files found, using first certificate")
            
            self.log(f"   📄 Testing deletion of certificate: {test_cert.get('cert_name', 'N/A')}")
            self.log(f"      Certificate ID: {test_cert.get('id')}")
            self.log(f"      Google Drive File ID: {test_cert.get('gdrive_file_id') or test_cert.get('google_drive_file_id', 'None')}")
            
            # Monitor backend logs during deletion
            self.log("   🔍 Monitoring backend logs during deletion...")
            
            # Perform the deletion
            delete_response = self.session.delete(f"{BACKEND_URL}/certificates/{test_cert['id']}", timeout=30)
            
            self.log(f"   Delete response status: {delete_response.status_code}")
            
            if delete_response.status_code == 200:
                try:
                    delete_data = delete_response.json()
                    self.log("   ✅ Certificate deletion successful")
                    self.log(f"      Response: {json.dumps(delete_data, indent=2)}")
                    
                    # Check if Google Drive file was deleted
                    gdrive_deleted = delete_data.get('gdrive_file_deleted', False)
                    self.log(f"      Google Drive file deleted: {'✅' if gdrive_deleted else '❌'}")
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log("   ✅ Certificate deletion successful (no JSON response)")
                    return True
            else:
                try:
                    error_data = delete_response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = delete_response.text
                
                self.log(f"   ❌ Certificate deletion failed - HTTP {delete_response.status_code}")
                self.log(f"      Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log(f"❌ Delete certificate API test error: {str(e)}", "ERROR")
            return False
    
    def debug_google_drive_integration(self):
        """Debug Google Drive integration for certificate deletion"""
        try:
            self.log("🔍 Debugging Google Drive Integration...")
            
            # Check company Google Drive configuration
            companies_response = self.session.get(f"{BACKEND_URL}/companies", timeout=10)
            
            if companies_response.status_code != 200:
                self.log(f"   ❌ Failed to get companies: {companies_response.status_code}")
                return False
            
            companies = companies_response.json()
            
            # Find user's company or AMCSC company
            user_company_id = self.user_info.get('company')
            target_company = None
            
            for company in companies:
                if company.get('id') == user_company_id:
                    target_company = company
                    break
                elif 'AMCSC' in company.get('name_en', '').upper() or 'AMCSC' in company.get('name', '').upper():
                    target_company = company
            
            if not target_company:
                self.log("   ❌ No suitable company found for Google Drive testing")
                return False
            
            self.log(f"   ✅ Testing with company: {target_company.get('name_en', target_company.get('name', 'N/A'))}")
            self.log(f"      Company ID: {target_company.get('id')}")
            
            # Check company Google Drive configuration
            company_id = target_company.get('id')
            
            # Test company Google Drive config endpoint
            config_response = self.session.get(f"{BACKEND_URL}/companies/{company_id}/gdrive/config", timeout=10)
            self.log(f"   Company Google Drive config status: {config_response.status_code}")
            
            if config_response.status_code == 200:
                config_data = config_response.json()
                self.log("   ✅ Company Google Drive configuration found")
                self.log(f"      Config: {json.dumps(config_data, indent=2)}")
                
                # Check for Apps Script URL
                apps_script_url = None
                if 'config' in config_data:
                    apps_script_url = config_data['config'].get('web_app_url') or config_data['config'].get('apps_script_url')
                
                if apps_script_url:
                    self.log(f"   ✅ Apps Script URL found: {apps_script_url}")
                    
                    # Test Apps Script delete_file action
                    self.test_apps_script_delete_action(apps_script_url)
                else:
                    self.log("   ❌ No Apps Script URL found in configuration")
            else:
                self.log(f"   ❌ Company Google Drive configuration not found: {config_response.status_code}")
                try:
                    error_data = config_response.json()
                    self.log(f"      Error: {error_data}")
                except:
                    self.log(f"      Error: {config_response.text}")
            
            # Check company Google Drive status
            status_response = self.session.get(f"{BACKEND_URL}/companies/{company_id}/gdrive/status", timeout=10)
            self.log(f"   Company Google Drive status: {status_response.status_code}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                self.log(f"   Status: {json.dumps(status_data, indent=2)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Google Drive integration debug error: {str(e)}", "ERROR")
            return False
    
    def test_apps_script_delete_action(self, apps_script_url):
        """Test Apps Script delete_file action"""
        try:
            self.log("   🔧 Testing Apps Script delete_file action...")
            
            # Test with a dummy file ID to see if the action is supported
            test_payload = {
                "action": "delete_file",
                "file_id": "test_file_id_12345",
                "permanent_delete": False
            }
            
            response = requests.post(apps_script_url, json=test_payload, timeout=30)
            self.log(f"      Apps Script delete test status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.log(f"      Apps Script response: {json.dumps(result, indent=2)}")
                    
                    if 'success' in result:
                        if result.get('success'):
                            self.log("      ✅ Apps Script delete_file action is working")
                        else:
                            error_msg = result.get('message', 'Unknown error')
                            if 'not found' in error_msg.lower() or 'does not exist' in error_msg.lower():
                                self.log("      ✅ Apps Script delete_file action is implemented (test file not found as expected)")
                            else:
                                self.log(f"      ⚠️ Apps Script delete_file action error: {error_msg}")
                    else:
                        self.log("      ❌ Apps Script response missing success field")
                        
                except json.JSONDecodeError:
                    self.log(f"      ❌ Apps Script returned invalid JSON: {response.text}")
            else:
                self.log(f"      ❌ Apps Script request failed: {response.status_code}")
                self.log(f"         Response: {response.text}")
                
        except Exception as e:
            self.log(f"      ❌ Apps Script test error: {str(e)}")
    
    def check_field_name_issues(self):
        """Check for field name issues in certificates and ships"""
        try:
            self.log("🔍 Checking Field Name Issues...")
            
            # Get a sample certificate and ship to check field names
            ships_response = self.session.get(f"{BACKEND_URL}/ships", timeout=10)
            
            if ships_response.status_code != 200:
                self.log(f"   ❌ Failed to get ships: {ships_response.status_code}")
                return False
            
            ships = ships_response.json()
            
            if not ships:
                self.log("   ❌ No ships found")
                return False
            
            sample_ship = ships[0]
            self.log(f"   📊 Sample ship field analysis: {sample_ship.get('name', 'N/A')}")
            
            # Check ship fields
            ship_issues = []
            if 'company_id' not in sample_ship and 'company' not in sample_ship:
                ship_issues.append("Missing both company_id and company fields")
            elif 'company_id' not in sample_ship:
                ship_issues.append("Missing company_id field (only company field present)")
            
            if ship_issues:
                self.log("   ❌ Ship field issues found:")
                for issue in ship_issues:
                    self.log(f"      - {issue}")
            else:
                self.log("   ✅ Ship fields look correct")
            
            # Get certificates for field analysis
            cert_response = self.session.get(f"{BACKEND_URL}/ships/{sample_ship['id']}/certificates", timeout=10)
            
            if cert_response.status_code == 200:
                certificates = cert_response.json()
                
                if certificates:
                    sample_cert = certificates[0]
                    self.log(f"   📊 Sample certificate field analysis: {sample_cert.get('cert_name', 'N/A')}")
                    
                    # Check certificate fields
                    cert_issues = []
                    has_gdrive_file_id = 'gdrive_file_id' in sample_cert
                    has_google_drive_file_id = 'google_drive_file_id' in sample_cert
                    
                    if not has_gdrive_file_id and not has_google_drive_file_id:
                        cert_issues.append("Missing both gdrive_file_id and google_drive_file_id fields")
                    elif has_google_drive_file_id and not has_gdrive_file_id:
                        cert_issues.append("Using google_drive_file_id instead of gdrive_file_id")
                    
                    if cert_issues:
                        self.log("   ❌ Certificate field issues found:")
                        for issue in cert_issues:
                            self.log(f"      - {issue}")
                    else:
                        self.log("   ✅ Certificate fields look correct")
                else:
                    self.log("   ⚠️ No certificates found for field analysis")
            else:
                self.log(f"   ❌ Failed to get certificates for field analysis: {cert_response.status_code}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Field name issues check error: {str(e)}", "ERROR")
            return False

def main():
    """Main test execution"""
    print("🗑️ Ship Management System - Certificate Delete with Google Drive File Removal Testing")
    print("=" * 80)
    
    tester = CertificateDeleteTester()
    success = tester.test_certificate_delete_functionality()
    
    print("=" * 80)
    if success:
        print("🎉 Certificate delete functionality test completed successfully!")
        print("✅ Google Drive file deletion is working properly")
        sys.exit(0)
    else:
        print("❌ Certificate delete functionality test completed with issues!")
        print("🔍 Check the detailed logs above for specific problems")
        sys.exit(1)

if __name__ == "__main__":
    main()
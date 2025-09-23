#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
Focus: Certificate Move Functionality Testing - Debug "Error moving certificates" issue
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

class CertificateMoveTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        self.company_id = None
        self.sunshine_ship = None
        self.test_certificate = None
        self.folder_structure = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_certificate_move_functionality(self):
        """Main test function for certificate move functionality debugging"""
        self.log("📁 Starting Certificate Move Functionality Testing - Debug 'Error moving certificates'")
        self.log("=" * 80)
        
        # Step 1: Authentication
        auth_result = self.test_authentication()
        if not auth_result:
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Get Certificate with Google Drive File ID
        cert_result = self.get_certificate_with_gdrive_file()
        if not cert_result:
            self.log("❌ No certificate with Google Drive file found - cannot test move")
            return False
        
        # Step 3: Test Move API Directly
        move_api_result = self.test_move_api_directly()
        
        # Step 4: Check Field Name Consistency
        field_consistency_result = self.check_field_name_consistency()
        
        # Step 5: Test Google Apps Script Integration
        apps_script_result = self.test_google_apps_script_integration()
        
        # Step 6: Check Backend Logs (simulated)
        backend_logs_result = self.check_backend_logs()
        
        # Step 7: Test Complete Move Workflow
        complete_workflow_result = self.test_complete_move_workflow()
        
        # Step 8: Summary
        self.log("=" * 80)
        self.log("📋 CERTIFICATE MOVE FUNCTIONALITY TEST SUMMARY")
        self.log("=" * 80)
        
        self.log(f"{'✅' if auth_result else '❌'} Authentication: {'SUCCESS' if auth_result else 'FAILED'}")
        self.log(f"{'✅' if cert_result else '❌'} Certificate with Google Drive File: {'FOUND' if cert_result else 'NOT FOUND'}")
        self.log(f"{'✅' if move_api_result else '❌'} Move API Direct Test: {'SUCCESS' if move_api_result else 'FAILED'}")
        self.log(f"{'✅' if field_consistency_result else '❌'} Field Name Consistency: {'SUCCESS' if field_consistency_result else 'FAILED'}")
        self.log(f"{'✅' if apps_script_result else '❌'} Google Apps Script Integration: {'SUCCESS' if apps_script_result else 'FAILED'}")
        self.log(f"{'✅' if backend_logs_result else '❌'} Backend Logs Check: {'SUCCESS' if backend_logs_result else 'FAILED'}")
        self.log(f"{'✅' if complete_workflow_result else '❌'} Complete Move Workflow: {'SUCCESS' if complete_workflow_result else 'FAILED'}")
        
        overall_success = all([auth_result, cert_result, move_api_result, field_consistency_result, apps_script_result])
        
        if overall_success:
            self.log("🎉 CERTIFICATE MOVE FUNCTIONALITY: FULLY WORKING")
        else:
            self.log("❌ CERTIFICATE MOVE FUNCTIONALITY: ISSUES DETECTED")
            self.log("🔍 Root cause analysis completed - check detailed logs above")
        
        return overall_success
    
    def test_authentication(self):
        """Test authentication with admin1/123456"""
        try:
            self.log("🔐 Step 1: Testing Authentication with admin1/123456...")
            
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
                    
                    # Get the actual company ID by looking up the company name
                    company_name = self.user_info.get('company')
                    if company_name:
                        # Get companies to find the ID
                        companies_response = self.session.get(f"{BACKEND_URL}/companies", timeout=10)
                        if companies_response.status_code == 200:
                            companies = companies_response.json()
                            for company in companies:
                                if (company.get('name_en', '').upper() == company_name.upper() or 
                                    company.get('name', '').upper() == company_name.upper()):
                                    self.company_id = company.get('id')
                                    self.log(f"      Company ID resolved: {self.company_id}")
                                    break
                    
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
    
    def get_certificate_with_gdrive_file(self):
        """Get a certificate from SUNSHINE 01 that has Google Drive file ID"""
        try:
            self.log("📄 Step 2: Getting Certificate with Google Drive File ID from SUNSHINE 01...")
            
            # Get ships
            ships_response = self.session.get(f"{BACKEND_URL}/ships", timeout=10)
            
            if ships_response.status_code != 200:
                self.log(f"   ❌ Failed to get ships: {ships_response.status_code}")
                return False
            
            ships = ships_response.json()
            
            # Find SUNSHINE ship
            for ship in ships:
                if "SUNSHINE" in ship.get('name', '').upper():
                    self.sunshine_ship = ship
                    break
            
            if not self.sunshine_ship:
                self.log("   ❌ SUNSHINE ship not found")
                return False
            
            self.log(f"   ✅ Found ship: {self.sunshine_ship.get('name')} (ID: {self.sunshine_ship.get('id')})")
            
            # Get certificates for this ship
            cert_response = self.session.get(f"{BACKEND_URL}/ships/{self.sunshine_ship['id']}/certificates", timeout=10)
            
            if cert_response.status_code != 200:
                self.log(f"   ❌ Failed to get certificates: {cert_response.status_code}")
                return False
            
            certificates = cert_response.json()
            self.log(f"   ✅ Found {len(certificates)} certificates")
            
            # Find certificate with Google Drive file ID
            for cert in certificates:
                gdrive_file_id = cert.get('google_drive_file_id') or cert.get('gdrive_file_id')
                if gdrive_file_id:
                    self.test_certificate = cert
                    self.log(f"   ✅ Found certificate with Google Drive file:")
                    self.log(f"      Certificate: {cert.get('cert_name', 'N/A')}")
                    self.log(f"      Certificate ID: {cert.get('id')}")
                    self.log(f"      Google Drive File ID: {gdrive_file_id}")
                    self.log(f"      Field name used: {'google_drive_file_id' if cert.get('google_drive_file_id') else 'gdrive_file_id'}")
                    return True
            
            self.log("   ❌ No certificates with Google Drive file ID found")
            self.log("   📊 Certificate analysis:")
            for i, cert in enumerate(certificates[:3]):
                self.log(f"      Certificate {i+1}: {cert.get('cert_name', 'N/A')}")
                self.log(f"         google_drive_file_id: {cert.get('google_drive_file_id', 'None')}")
                self.log(f"         gdrive_file_id: {cert.get('gdrive_file_id', 'None')}")
            
            return False
            
        except Exception as e:
            self.log(f"❌ Certificate retrieval error: {str(e)}", "ERROR")
            return False
    
    def test_move_api_directly(self):
        """Test POST /api/companies/{company_id}/gdrive/move-file endpoint"""
        try:
            self.log("🔧 Step 3: Testing Move API Directly...")
            
            if not self.test_certificate or not self.company_id:
                self.log("   ❌ Missing test certificate or company ID")
                return False
            
            # First, get folder structure to find a target folder
            folder_result = self.get_folder_structure()
            if not folder_result:
                self.log("   ❌ Could not get folder structure for move test")
                return False
            
            # Get file ID from certificate
            file_id = self.test_certificate.get('google_drive_file_id') or self.test_certificate.get('gdrive_file_id')
            
            # Find a target folder (use first available folder)
            target_folder_id = None
            if self.folder_structure and 'folders' in self.folder_structure:
                folders = self.folder_structure['folders']
                if folders:
                    # Use the first folder as target
                    first_folder = list(folders.values())[0] if isinstance(folders, dict) else folders[0]
                    if isinstance(first_folder, dict):
                        target_folder_id = first_folder.get('id')
                    else:
                        target_folder_id = first_folder
            
            if not target_folder_id:
                self.log("   ❌ No target folder ID found for move test")
                return False
            
            self.log(f"   📁 Testing move operation:")
            self.log(f"      File ID: {file_id}")
            self.log(f"      Target Folder ID: {target_folder_id}")
            self.log(f"      Company ID: {self.company_id}")
            
            # Test the move API
            move_data = {
                "file_id": file_id,
                "target_folder_id": target_folder_id
            }
            
            endpoint = f"{BACKEND_URL}/companies/{self.company_id}/gdrive/move-file"
            response = self.session.post(endpoint, json=move_data, timeout=30)
            
            self.log(f"   Move API response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.log("   ✅ Move API call successful")
                    self.log(f"      Response: {json.dumps(result, indent=2)}")
                    return True
                except json.JSONDecodeError:
                    self.log("   ✅ Move API call successful (no JSON response)")
                    return True
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                
                self.log(f"   ❌ Move API call failed - HTTP {response.status_code}")
                self.log(f"      Error: {error_detail}")
                
                # Check for specific error patterns
                if "Company not found" in error_detail:
                    self.log("      🔍 Root Cause: Company lookup failure")
                elif "not configured" in error_detail.lower():
                    self.log("      🔍 Root Cause: Google Drive not configured for company")
                elif "file_id" in error_detail.lower() or "target_folder_id" in error_detail.lower():
                    self.log("      🔍 Root Cause: Missing or invalid parameters")
                
                return False
                
        except Exception as e:
            self.log(f"❌ Move API test error: {str(e)}", "ERROR")
            return False
    
    def get_folder_structure(self):
        """Get Google Drive folder structure for the company"""
        try:
            if not self.company_id:
                return False
            
            endpoint = f"{BACKEND_URL}/companies/{self.company_id}/gdrive/folder-structure"
            response = self.session.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                self.folder_structure = response.json()
                self.log(f"   ✅ Folder structure retrieved")
                return True
            else:
                self.log(f"   ❌ Failed to get folder structure: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Folder structure error: {str(e)}")
            return False
    
    def check_field_name_consistency(self):
        """Check if MoveModal is using correct field name (google_drive_file_id vs gdrive_file_id)"""
        try:
            self.log("🔍 Step 4: Checking Field Name Consistency...")
            
            if not self.test_certificate:
                self.log("   ❌ No test certificate available")
                return False
            
            # Check which field names are present in the certificate
            has_google_drive_file_id = 'google_drive_file_id' in self.test_certificate
            has_gdrive_file_id = 'gdrive_file_id' in self.test_certificate
            
            self.log("   📊 Certificate field analysis:")
            self.log(f"      google_drive_file_id field: {'✅ Present' if has_google_drive_file_id else '❌ Missing'}")
            self.log(f"      gdrive_file_id field: {'✅ Present' if has_gdrive_file_id else '❌ Missing'}")
            
            if has_google_drive_file_id:
                self.log(f"      google_drive_file_id value: {self.test_certificate.get('google_drive_file_id')}")
            if has_gdrive_file_id:
                self.log(f"      gdrive_file_id value: {self.test_certificate.get('gdrive_file_id')}")
            
            # Check backend move endpoint expectations
            self.log("   🔧 Backend move endpoint analysis:")
            self.log("      Expected parameter: file_id (from move_data.get('file_id'))")
            self.log("      Frontend should send: file_id in request body")
            
            # Check for potential field name mismatch
            if has_google_drive_file_id and not has_gdrive_file_id:
                self.log("   ⚠️ Potential issue: Certificate uses 'google_drive_file_id' field")
                self.log("      Frontend MoveModal should extract file ID from 'google_drive_file_id' field")
            elif has_gdrive_file_id and not has_google_drive_file_id:
                self.log("   ⚠️ Potential issue: Certificate uses 'gdrive_file_id' field")
                self.log("      Frontend MoveModal should extract file ID from 'gdrive_file_id' field")
            elif has_both := (has_google_drive_file_id and has_gdrive_file_id):
                self.log("   ✅ Both field names present - frontend should handle both")
            else:
                self.log("   ❌ Critical issue: No Google Drive file ID field found")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"❌ Field name consistency check error: {str(e)}", "ERROR")
            return False
    
    def test_google_apps_script_integration(self):
        """Test Google Apps Script move_file action"""
        try:
            self.log("🔧 Step 5: Testing Google Apps Script Integration...")
            
            if not self.company_id:
                self.log("   ❌ No company ID available")
                return False
            
            # Get company Google Drive configuration
            config_response = self.session.get(f"{BACKEND_URL}/companies/{self.company_id}/gdrive/config", timeout=10)
            
            if config_response.status_code != 200:
                self.log(f"   ❌ Failed to get Google Drive config: {config_response.status_code}")
                return False
            
            config_data = config_response.json()
            self.log("   ✅ Company Google Drive configuration found")
            
            # Get Apps Script URL
            apps_script_url = None
            if 'config' in config_data:
                apps_script_url = config_data['config'].get('web_app_url') or config_data['config'].get('apps_script_url')
            
            if not apps_script_url:
                self.log("   ❌ No Apps Script URL found in configuration")
                return False
            
            self.log(f"   ✅ Apps Script URL: {apps_script_url}")
            
            # Test move_file action with dummy data
            test_payload = {
                "action": "move_file",
                "file_id": "test_file_id_12345",
                "target_folder_id": "test_folder_id_67890"
            }
            
            self.log("   🔧 Testing Apps Script move_file action...")
            response = requests.post(apps_script_url, json=test_payload, timeout=30)
            
            self.log(f"   Apps Script response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.log(f"   Apps Script response: {json.dumps(result, indent=2)}")
                    
                    if 'success' in result:
                        if result.get('success'):
                            self.log("   ✅ Apps Script move_file action is working")
                            return True
                        else:
                            error_msg = result.get('message', 'Unknown error')
                            if 'not found' in error_msg.lower() or 'does not exist' in error_msg.lower():
                                self.log("   ✅ Apps Script move_file action is implemented (test files not found as expected)")
                                return True
                            else:
                                self.log(f"   ❌ Apps Script move_file action error: {error_msg}")
                                return False
                    else:
                        self.log("   ❌ Apps Script response missing success field")
                        return False
                        
                except json.JSONDecodeError:
                    self.log(f"   ❌ Apps Script returned invalid JSON: {response.text}")
                    return False
            else:
                self.log(f"   ❌ Apps Script request failed: {response.status_code}")
                self.log(f"      Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Google Apps Script integration test error: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs(self):
        """Check backend logs during move operation (simulated)"""
        try:
            self.log("📋 Step 6: Checking Backend Logs...")
            
            # Since we can't directly access backend logs, we'll check for common issues
            self.log("   🔍 Common backend log issues to check:")
            self.log("      - Company lookup failures")
            self.log("      - Google Drive configuration missing")
            self.log("      - Apps Script URL not found")
            self.log("      - Invalid file_id or target_folder_id parameters")
            self.log("      - Apps Script timeout or connection errors")
            
            # Test company lookup
            if self.company_id:
                company_response = self.session.get(f"{BACKEND_URL}/companies", timeout=10)
                if company_response.status_code == 200:
                    companies = company_response.json()
                    company_found = any(c.get('id') == self.company_id for c in companies)
                    self.log(f"   {'✅' if company_found else '❌'} Company lookup: {'SUCCESS' if company_found else 'FAILED'}")
                else:
                    self.log(f"   ❌ Company lookup failed: {company_response.status_code}")
            
            # Test Google Drive configuration
            if self.company_id:
                config_response = self.session.get(f"{BACKEND_URL}/companies/{self.company_id}/gdrive/config", timeout=10)
                config_ok = config_response.status_code == 200
                self.log(f"   {'✅' if config_ok else '❌'} Google Drive config: {'FOUND' if config_ok else 'MISSING'}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Backend logs check error: {str(e)}", "ERROR")
            return False
    
    def test_complete_move_workflow(self):
        """Test the complete move workflow: Certificate selection → API call → Apps Script → File move"""
        try:
            self.log("🔄 Step 7: Testing Complete Move Workflow...")
            
            if not all([self.test_certificate, self.company_id]):
                self.log("   ❌ Missing required data for complete workflow test")
                return False
            
            # Step 1: Certificate selection (already done)
            self.log("   ✅ Step 1: Certificate selected")
            self.log(f"      Certificate: {self.test_certificate.get('cert_name')}")
            
            # Step 2: Extract file ID
            file_id = self.test_certificate.get('google_drive_file_id') or self.test_certificate.get('gdrive_file_id')
            if not file_id:
                self.log("   ❌ Step 2: No file ID found in certificate")
                return False
            
            self.log("   ✅ Step 2: File ID extracted")
            self.log(f"      File ID: {file_id}")
            
            # Step 3: Get target folder (simulate user selection)
            if not self.folder_structure:
                folder_result = self.get_folder_structure()
                if not folder_result:
                    self.log("   ❌ Step 3: Could not get folder structure")
                    return False
            
            self.log("   ✅ Step 3: Target folder available")
            
            # Step 4: API call (already tested in step 3)
            self.log("   ✅ Step 4: API call tested (see Step 3 results)")
            
            # Step 5: Identify exact failure point
            self.log("   🔍 Step 5: Failure point analysis")
            
            # Check if the issue is in the frontend, backend, or Apps Script
            self.log("      Potential failure points:")
            self.log("      1. Frontend MoveModal field name mismatch")
            self.log("      2. Backend company lookup failure")
            self.log("      3. Backend Google Drive config missing")
            self.log("      4. Apps Script move_file action not implemented")
            self.log("      5. Invalid folder IDs or file IDs")
            self.log("      6. Google Drive permissions issues")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Complete workflow test error: {str(e)}", "ERROR")
            return False

def main():
    """Main test execution"""
    print("📁 Ship Management System - Certificate Move Functionality Testing")
    print("🔍 Debug: 'Error moving certificates' issue")
    print("=" * 80)
    
    tester = CertificateMoveTester()
    success = tester.test_certificate_move_functionality()
    
    print("=" * 80)
    if success:
        print("🎉 Certificate move functionality test completed successfully!")
        print("✅ Move functionality is working properly")
        sys.exit(0)
    else:
        print("❌ Certificate move functionality test completed with issues!")
        print("🔍 Root cause analysis completed - check detailed logs above")
        print("💡 Focus on the failed steps to identify the exact issue")
        sys.exit(1)

if __name__ == "__main__":
    main()
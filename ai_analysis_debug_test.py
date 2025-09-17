#!/usr/bin/env python3
"""
AI Analysis Debug Test for Certificate Information Extraction Issue
Testing why certificate information extraction returns all "N/A" values
Focus: Debug AI analysis issue where certificate fields show N/A instead of extracted values
"""

import requests
import sys
import json
import os
import tempfile
import io
from datetime import datetime, timezone
import time
import PyPDF2

class AIAnalysisDebugTester:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.issues_found = []
        
        # Test PDF file mentioned in review request
        self.test_pdf_filename = "PM252494430.pdf"

    def log_issue(self, issue_type, description, details=None):
        """Log an issue found during testing"""
        issue = {
            "type": issue_type,
            "description": description,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.issues_found.append(issue)
        print(f"🚨 ISSUE FOUND: {issue_type} - {description}")
        if details:
            print(f"   Details: {details}")

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED")
        
        if details:
            print(f"   Details: {details}")

    def run_api_request(self, method, endpoint, expected_status, data=None, files=None, timeout=60):
        """Run a single API request"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Don't set Content-Type for file uploads - let requests handle it
        if not files:
            headers['Content-Type'] = 'application/json'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            
            if success:
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {"raw_response": response.text}
            else:
                try:
                    error_detail = response.json()
                    return False, {"error": error_detail, "status": response.status_code}
                except:
                    return False, {"error": response.text, "status": response.status_code}

        except Exception as e:
            return False, {"error": str(e)}

    def create_test_maritime_certificate_pdf(self):
        """Create a test maritime certificate PDF with clear certificate information"""
        certificate_content = """
PANAMA MARITIME DOCUMENTATION SERVICES

SAFETY MANAGEMENT CERTIFICATE

This is to certify that the Safety Management System of the ship named below has been audited and found to comply with the requirements of the International Safety Management (ISM) Code.

Ship Name: MV PACIFIC STAR
IMO Number: 9876543210
Certificate Number: SMC-PM-2024-001
Certificate Type: Full Term
Issue Date: 15 January 2024
Valid Until: 15 January 2025
Last Endorsement: 15 July 2024
Next Survey: 15 July 2025

Issued By: Panama Maritime Documentation Services
Classification Society: DNV GL
Flag State: Panama
Gross Tonnage: 25,000
Deadweight: 35,000 MT
Built Year: 2018
Ship Owner: Pacific Maritime Holdings Ltd
Managing Company: Global Shipping Inc

This certificate is issued under the authority of the Government of Panama.

Authorized Officer: Captain John Smith
Date: 15 January 2024
Place: Panama City, Panama
"""
        
        # Create a simple text-based PDF content
        return certificate_content.encode('utf-8')

    def test_authentication(self):
        """Test admin authentication"""
        print(f"\n🔐 Testing Authentication")
        
        success, response = self.run_api_request(
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            user_info = response.get('user', {})
            self.log_test(
                "Admin Authentication", 
                True, 
                f"User: {user_info.get('full_name')} ({user_info.get('role')})"
            )
            return True
        else:
            self.log_test("Admin Authentication", False, f"Response: {response}")
            self.log_issue("AUTHENTICATION", "Login failed", response)
            return False

    def test_ai_configuration(self):
        """Test current AI configuration"""
        print(f"\n🤖 Testing AI Configuration")
        
        success, response = self.run_api_request(
            "GET",
            "ai-config",
            200
        )
        
        if success:
            print(f"   Current AI Configuration:")
            print(f"     Provider: {response.get('provider', 'Not set')}")
            print(f"     Model: {response.get('model', 'Not set')}")
            print(f"     Use Emergent Key: {response.get('use_emergent_key', 'Not set')}")
            
            # Check if configuration looks valid
            provider = response.get('provider')
            model = response.get('model')
            use_emergent = response.get('use_emergent_key', True)
            
            if not provider:
                self.log_issue("AI_CONFIG", "AI provider not configured", response)
            if not model:
                self.log_issue("AI_CONFIG", "AI model not configured", response)
            
            # Check if using Emergent LLM key
            if use_emergent:
                emergent_key = os.environ.get('EMERGENT_LLM_KEY')
                if emergent_key:
                    print(f"     Emergent Key: Available (prefix: {emergent_key[:20]}...)")
                    if not emergent_key.startswith('sk-emergent-'):
                        self.log_issue("EMERGENT_KEY", "Key format may be incorrect", f"Key starts with: {emergent_key[:15]}")
                else:
                    self.log_issue("EMERGENT_KEY", "EMERGENT_LLM_KEY not found in environment", None)
            
            self.log_test("AI Configuration", True, f"Provider: {provider}, Model: {model}")
            return True
        else:
            self.log_test("AI Configuration", False, f"Response: {response}")
            self.log_issue("AI_CONFIG", "Failed to retrieve AI configuration", response)
            return False

    def download_test_pdf(self):
        """Download the specific EIAPP certificate PDF"""
        print(f"\n📥 Downloading Test PDF")
        
        try:
            response = requests.get(self.test_pdf_url, timeout=30)
            
            if response.status_code == 200:
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(response.content)
                temp_file.close()
                
                file_size = len(response.content)
                self.log_test(
                    "PDF Download", 
                    True, 
                    f"Downloaded {file_size} bytes to {temp_file.name}"
                )
                return temp_file.name
            else:
                self.log_test(
                    "PDF Download", 
                    False, 
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return None
                
        except Exception as e:
            self.log_test("PDF Download", False, f"Error: {str(e)}")
            return None

    def test_single_pdf_analysis(self, pdf_path):
        """Test the single PDF analysis endpoint"""
        print(f"\n🤖 Testing Single PDF Analysis Endpoint")
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                files = {'file': ('BROTHER_36_EIAPP.pdf', pdf_file, 'application/pdf')}
                
                success, response = self.run_api_request(
                    "POST",
                    "analyze-ship-certificate",
                    200,
                    files=files,
                    timeout=120  # AI analysis can take time
                )
                
                if success:
                    # Check if ship_name is correctly extracted
                    ship_name = response.get('ship_name', 'NOT_FOUND')
                    
                    print(f"   AI Analysis Response:")
                    print(f"   Ship Name: {ship_name}")
                    print(f"   IMO Number: {response.get('imo_number', 'N/A')}")
                    print(f"   Class Society: {response.get('class_society', 'N/A')}")
                    print(f"   Flag: {response.get('flag', 'N/A')}")
                    print(f"   Gross Tonnage: {response.get('gross_tonnage', 'N/A')}")
                    print(f"   Built Year: {response.get('built_year', 'N/A')}")
                    print(f"   Ship Owner: {response.get('ship_owner', 'N/A')}")
                    print(f"   Company: {response.get('company', 'N/A')}")
                    
                    # Check if ship name matches expected
                    ship_name_correct = ship_name == self.expected_ship_name
                    
                    self.log_test(
                        "Single PDF Analysis - API Call", 
                        True, 
                        f"Analysis completed successfully"
                    )
                    
                    self.log_test(
                        "Ship Name Extraction", 
                        ship_name_correct, 
                        f"Expected: '{self.expected_ship_name}', Got: '{ship_name}'"
                    )
                    
                    # Log full response for debugging
                    print(f"\n   Full AI Response:")
                    print(json.dumps(response, indent=2, default=str))
                    
                    return ship_name_correct, response
                else:
                    self.log_test(
                        "Single PDF Analysis - API Call", 
                        False, 
                        f"API Error: {response}"
                    )
                    return False, response
                    
        except Exception as e:
            self.log_test("Single PDF Analysis", False, f"Error: {str(e)}")
            return False, {"error": str(e)}

    def test_multi_file_upload(self, pdf_path):
        """Test the multi-file upload endpoint"""
        print(f"\n📁 Testing Multi-File Upload with AI Analysis")
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                files = {'files': ('BROTHER_36_EIAPP.pdf', pdf_file, 'application/pdf')}
                data = {
                    'ship_id': 'test-ship-id',  # We'll use a test ship ID
                    'category': 'certificates'
                }
                
                success, response = self.run_api_request(
                    "POST",
                    "upload-files",
                    200,
                    data=data,
                    files=files,
                    timeout=120
                )
                
                if success:
                    print(f"   Multi-file upload response:")
                    print(json.dumps(response, indent=2, default=str))
                    
                    # Check if AI analysis was performed
                    uploaded_files = response.get('uploaded_files', [])
                    ai_analysis_found = False
                    ship_name_from_multi = None
                    
                    for file_info in uploaded_files:
                        if 'ai_analysis' in file_info:
                            ai_analysis_found = True
                            ai_data = file_info['ai_analysis']
                            ship_name_from_multi = ai_data.get('ship_name', 'NOT_FOUND')
                            break
                    
                    self.log_test(
                        "Multi-File Upload - API Call", 
                        True, 
                        f"Upload completed, AI analysis found: {ai_analysis_found}"
                    )
                    
                    if ai_analysis_found:
                        ship_name_correct = ship_name_from_multi == self.expected_ship_name
                        self.log_test(
                            "Multi-File Ship Name Extraction", 
                            ship_name_correct, 
                            f"Expected: '{self.expected_ship_name}', Got: '{ship_name_from_multi}'"
                        )
                    
                    return success, response
                else:
                    self.log_test(
                        "Multi-File Upload - API Call", 
                        False, 
                        f"API Error: {response}"
                    )
                    return False, response
                    
        except Exception as e:
            self.log_test("Multi-File Upload", False, f"Error: {str(e)}")
            return False, {"error": str(e)}

    def test_ai_prompt_analysis(self):
        """Test if we can inspect the AI prompt being used"""
        print(f"\n🔍 Analyzing AI Prompt Configuration")
        
        # Check if there's an AI config endpoint
        success, response = self.run_api_request(
            "GET",
            "ai-config",
            200
        )
        
        if success:
            print(f"   AI Configuration:")
            print(json.dumps(response, indent=2, default=str))
            self.log_test("AI Configuration Check", True, "AI config retrieved")
        else:
            self.log_test("AI Configuration Check", False, f"Could not retrieve AI config: {response}")
        
        return success

    def debug_backend_logs(self):
        """Check backend logs for AI analysis errors"""
        print(f"\n📋 Checking Backend Logs")
        
        try:
            # Try to read supervisor logs
            import subprocess
            result = subprocess.run(
                ['tail', '-n', '50', '/var/log/supervisor/backend.err.log'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"   Recent Backend Error Logs:")
                print(result.stdout)
                self.log_test("Backend Log Check", True, "Logs retrieved")
            else:
                self.log_test("Backend Log Check", False, "Could not read error logs")
                
        except Exception as e:
            self.log_test("Backend Log Check", False, f"Error reading logs: {str(e)}")

    def run_comprehensive_test(self):
        """Run comprehensive AI analysis debugging"""
        print("🚢 AI Analysis Debug Test for Ship Name Extraction")
        print("=" * 60)
        print(f"Target PDF: {self.test_pdf_url}")
        print(f"Expected Ship Name: {self.expected_ship_name}")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.test_authentication():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Step 2: Download test PDF
        pdf_path = self.download_test_pdf()
        if not pdf_path:
            print("❌ PDF download failed, stopping tests")
            return False
        
        try:
            # Step 3: Test single PDF analysis
            single_success, single_response = self.test_single_pdf_analysis(pdf_path)
            
            # Step 4: Test multi-file upload
            multi_success, multi_response = self.test_multi_file_upload(pdf_path)
            
            # Step 5: Check AI configuration
            self.test_ai_prompt_analysis()
            
            # Step 6: Check backend logs
            self.debug_backend_logs()
            
            # Summary
            print("\n" + "=" * 60)
            print("🔍 DEBUG ANALYSIS SUMMARY")
            print("=" * 60)
            
            print(f"Tests Run: {self.tests_run}")
            print(f"Tests Passed: {self.tests_passed}")
            
            # Specific findings
            if single_success:
                ship_name = single_response.get('ship_name', 'NOT_FOUND')
                if ship_name == self.expected_ship_name:
                    print(f"✅ ISSUE RESOLVED: Ship name correctly extracted as '{ship_name}'")
                else:
                    print(f"❌ ISSUE PERSISTS: Ship name extracted as '{ship_name}' instead of '{self.expected_ship_name}'")
                    print(f"   Full AI Response: {json.dumps(single_response, indent=2, default=str)}")
            else:
                print(f"❌ CRITICAL: Single PDF analysis endpoint failed")
                print(f"   Error Details: {single_response}")
            
            return single_success
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(pdf_path)
                print(f"   Cleaned up temporary file: {pdf_path}")
            except:
                pass

def main():
    """Main test execution"""
    tester = AIAnalysisDebugTester()
    
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 AI Analysis debugging completed successfully!")
        return 0
    else:
        print("\n⚠️ AI Analysis debugging found issues - check details above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
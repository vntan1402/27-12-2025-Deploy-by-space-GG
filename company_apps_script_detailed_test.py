#!/usr/bin/env python3
"""
Company Apps Script Detailed Testing with Real PDF File
FOCUS: Test with proper PDF file and analyze the exact issue with file uploads
"""

import requests
import json
import os
import sys
import base64
from datetime import datetime
import tempfile

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://maritime-ai-crew-1.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class DetailedCompanyAppsScriptTester:
    def __init__(self):
        self.auth_token = None
        self.company_apps_script_url = "https://script.google.com/macros/s/AKfycbzzpvHsThfQPjlz7kgr6Uontm-b0y-4AyishYmxPDIB72yxbBK29Zbv9oGiV3BHte2u/exec"
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
    def authenticate(self):
        try:
            self.log("🔐 Authenticating...")
            login_data = {"username": "admin1", "password": "123456", "remember_me": False}
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.log("✅ Authentication successful")
                return True
            else:
                self.log(f"❌ Authentication failed - Status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def create_test_pdf(self):
        """Create a simple PDF file for testing"""
        try:
            # Create a minimal PDF content
            pdf_content = """%PDF-1.4
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
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Passport Document) Tj
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
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name
            
            self.log(f"✅ Created test PDF: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            self.log(f"❌ Error creating test PDF: {str(e)}", "ERROR")
            return None
    
    def test_company_apps_script_with_folder_id(self):
        """Test Company Apps Script with proper folder_id parameter"""
        try:
            self.log("📁 Testing Company Apps Script with folder_id parameter...")
            
            # Test with folder_id parameter (which seems to be required)
            test_payload = {
                "action": "upload_file_with_folder_creation",
                "file_content": base64.b64encode("Test file content".encode()).decode(),
                "filename": "test_file.txt",
                "folder_path": "BROTHER 36/Crew records",
                "folder_id": "test_folder_id",  # Add folder_id
                "category": "passport",
                "timestamp": datetime.now().isoformat()
            }
            
            self.log(f"   Sending payload with folder_id...")
            response = requests.post(
                self.company_apps_script_url,
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                    
                    if response_data.get('success') == True:
                        self.log("   ✅ Company Apps Script accepts upload with folder_id")
                        
                        # Check for actual file ID
                        if 'file_id' in response_data and response_data['file_id']:
                            if 'mock' not in str(response_data['file_id']).lower():
                                self.log(f"   ✅ Real file ID returned: {response_data['file_id']}")
                                return True
                            else:
                                self.log(f"   ❌ Mock file ID returned: {response_data['file_id']}")
                        else:
                            self.log("   ❌ No file_id in response")
                    else:
                        self.log(f"   ❌ Upload failed: {response_data.get('message', 'Unknown error')}")
                        
                except json.JSONDecodeError:
                    self.log(f"   Response text: {response.text}")
                    
            return False
            
        except Exception as e:
            self.log(f"❌ Error testing with folder_id: {str(e)}", "ERROR")
            return False
    
    def test_passport_analysis_with_pdf(self):
        """Test passport analysis with a proper PDF file"""
        try:
            self.log("📄 Testing passport analysis with PDF file...")
            
            # Create test PDF
            pdf_path = self.create_test_pdf()
            if not pdf_path:
                return False
            
            try:
                endpoint = f"{BACKEND_URL}/crew/analyze-passport"
                self.log(f"   POST {endpoint}")
                
                with open(pdf_path, 'rb') as file:
                    files = {
                        'passport_file': ('test_passport.pdf', file, 'application/pdf')
                    }
                    data = {
                        'ship_name': 'BROTHER 36'
                    }
                    
                    self.log("   Uploading PDF passport file...")
                    response = requests.post(
                        endpoint, 
                        files=files, 
                        data=data, 
                        headers=self.get_headers(), 
                        timeout=120
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                        
                        if response_data.get('success') == True:
                            self.log("   ✅ PDF passport analysis successful")
                            
                            # Check for file upload indicators
                            if 'files' in response_data:
                                files_data = response_data['files']
                                self.log(f"   Files data: {files_data}")
                                
                                # Check for real file IDs
                                for file_info in files_data:
                                    file_id = file_info.get('file_id', '')
                                    if file_id and 'mock' not in file_id.lower():
                                        self.log(f"   ✅ Real file uploaded: {file_id}")
                                    else:
                                        self.log(f"   ❌ Mock file ID: {file_id}")
                            else:
                                self.log("   ⚠️ No files data in response")
                                
                        elif response_data.get('success') == False:
                            error_msg = response_data.get('error', 'Unknown error')
                            self.log(f"   ❌ Analysis failed: {error_msg}")
                            
                            # Check for specific errors
                            if 'company apps script' in error_msg.lower():
                                self.log("   ❌ Company Apps Script specific error")
                            if 'not configured' in error_msg.lower():
                                self.log("   ❌ Configuration error")
                                
                    except json.JSONDecodeError:
                        self.log(f"   Response text: {response.text[:500]}")
                        
                else:
                    self.log(f"   ❌ Analysis failed - Status: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data}")
                    except:
                        self.log(f"   Error text: {response.text[:300]}")
                        
            finally:
                # Clean up
                try:
                    os.unlink(pdf_path)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Error in PDF analysis test: {str(e)}", "ERROR")
    
    def test_direct_company_apps_script_upload(self):
        """Test direct upload to Company Apps Script with proper parameters"""
        try:
            self.log("🎯 Testing direct Company Apps Script upload with proper parameters...")
            
            # Test different action types
            actions_to_test = [
                "upload_file_with_folder_creation",
                "upload_file",
                "create_file"
            ]
            
            for action in actions_to_test:
                self.log(f"   Testing action: {action}")
                
                payload = {
                    "action": action,
                    "file_content": base64.b64encode("Test passport content\nName: NGUYEN VAN TEST\nPassport: C1234567".encode()).decode(),
                    "filename": "test_passport_direct.txt",
                    "folder_path": "BROTHER 36/Crew records",
                    "category": "passport",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add folder_id if needed
                if "folder" in action:
                    payload["folder_id"] = "1BqzO8H8yF5xQJ9K2L3M4N5O6P7Q8R9S0T"  # Example folder ID
                
                try:
                    response = requests.post(
                        self.company_apps_script_url,
                        json=payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=60
                    )
                    
                    self.log(f"     Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            self.log(f"     Response: {json.dumps(response_data, indent=4)}")
                            
                            if response_data.get('success') == True:
                                self.log(f"     ✅ Action {action} successful")
                                
                                # Check for file ID
                                if 'file_id' in response_data:
                                    file_id = response_data['file_id']
                                    if file_id and 'mock' not in str(file_id).lower():
                                        self.log(f"     ✅ Real file ID: {file_id}")
                                        return True
                                    else:
                                        self.log(f"     ❌ Mock file ID: {file_id}")
                                        
                            else:
                                message = response_data.get('message', 'Unknown error')
                                self.log(f"     ❌ Failed: {message}")
                                
                        except json.JSONDecodeError:
                            self.log(f"     Response text: {response.text}")
                            
                except Exception as e:
                    self.log(f"     ❌ Request error: {str(e)}")
                    
            return False
            
        except Exception as e:
            self.log(f"❌ Error in direct upload test: {str(e)}", "ERROR")
            return False
    
    def run_detailed_test(self):
        """Run detailed Company Apps Script testing"""
        try:
            self.log("🚀 STARTING DETAILED COMPANY APPS SCRIPT TESTING")
            self.log("=" * 60)
            
            # Authenticate
            if not self.authenticate():
                return False
            
            # Test 1: Company Apps Script with folder_id
            self.log("\n📁 TEST 1: Company Apps Script with folder_id")
            self.test_company_apps_script_with_folder_id()
            
            # Test 2: Direct upload tests
            self.log("\n🎯 TEST 2: Direct Company Apps Script upload")
            self.test_direct_company_apps_script_upload()
            
            # Test 3: Backend integration with PDF
            self.log("\n📄 TEST 3: Backend integration with PDF")
            self.test_passport_analysis_with_pdf()
            
            self.log("\n" + "=" * 60)
            self.log("✅ DETAILED TESTING COMPLETED")
            
        except Exception as e:
            self.log(f"❌ Error in detailed test: {str(e)}", "ERROR")

def main():
    tester = DetailedCompanyAppsScriptTester()
    tester.run_detailed_test()

if __name__ == "__main__":
    main()
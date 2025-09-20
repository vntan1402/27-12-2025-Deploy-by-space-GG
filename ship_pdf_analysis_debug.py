#!/usr/bin/env python3
"""
Ship PDF Analysis Debug Test - Add New Ship Feature
Focused testing to debug the specific issue where PDF analysis shows success message
but form fields remain empty. Testing the exact API call POST /api/analyze-ship-certificate
with the provided PDF file to examine the complete response structure.
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ship-cert-manager-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

# PDF file URL from review request
PDF_FILE_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/7me5c9go_SS%20STAR%20PM252494416_ImagePDF.pdf"

class ShipPDFAnalysisDebugger:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                
                self.log_test("Authentication Test", True, 
                            f"Logged in as {self.user_info['username']} ({self.user_info.get('role', 'Unknown')})")
                return True
            else:
                self.log_test("Authentication Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication Test", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def download_pdf_file(self):
        """Download the PDF file from the provided URL"""
        try:
            print(f"📥 Downloading PDF file from: {PDF_FILE_URL}")
            response = requests.get(PDF_FILE_URL, timeout=30)
            
            if response.status_code == 200:
                file_size = len(response.content)
                self.log_test("PDF File Download", True, 
                            f"Downloaded PDF file successfully. Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                return response.content
            else:
                self.log_test("PDF File Download", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("PDF File Download", False, error=str(e))
            return None
    
    def test_analyze_ship_certificate_api(self, pdf_content):
        """Test the exact API call POST /api/analyze-ship-certificate"""
        try:
            print("🔍 Testing POST /api/analyze-ship-certificate API endpoint")
            
            # Prepare the file for upload
            files = {
                'file': ('SS_STAR_PM252494416_ImagePDF.pdf', pdf_content, 'application/pdf')
            }
            
            # Make the API call
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers(),
                timeout=60  # Allow up to 60 seconds for AI processing
            )
            
            print(f"📊 API Response Status: {response.status_code}")
            print(f"📊 API Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Log the complete response structure
                    print("=" * 80)
                    print("📋 COMPLETE API RESPONSE STRUCTURE:")
                    print("=" * 80)
                    print(json.dumps(response_data, indent=2, default=str))
                    print("=" * 80)
                    
                    # Analyze the response structure
                    self.analyze_response_structure(response_data)
                    
                    self.log_test("Analyze Ship Certificate API", True, 
                                f"API call successful. Response contains {len(response_data)} top-level fields")
                    return response_data
                    
                except json.JSONDecodeError as e:
                    self.log_test("Analyze Ship Certificate API", False, 
                                error=f"Invalid JSON response: {e}. Raw response: {response.text[:500]}")
                    return None
            else:
                self.log_test("Analyze Ship Certificate API", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Analyze Ship Certificate API", False, error=str(e))
            return None
    
    def analyze_response_structure(self, response_data):
        """Analyze the response structure to understand the data format"""
        print("\n🔍 RESPONSE STRUCTURE ANALYSIS:")
        print("-" * 50)
        
        # Check top-level fields
        top_level_fields = list(response_data.keys()) if isinstance(response_data, dict) else []
        print(f"Top-level fields: {top_level_fields}")
        
        # Check for common patterns the frontend might expect
        patterns_to_check = [
            "data.analysis",
            "data", 
            "analysis",
            "result",
            "ship_data",
            "extracted_data"
        ]
        
        print("\n🔍 CHECKING FRONTEND EXPECTED PATTERNS:")
        for pattern in patterns_to_check:
            value = self.get_nested_value(response_data, pattern)
            if value is not None:
                print(f"✅ {pattern}: Found - Type: {type(value).__name__}")
                if isinstance(value, dict):
                    print(f"    Fields: {list(value.keys())}")
            else:
                print(f"❌ {pattern}: Not found")
        
        # Check for ship-related fields at any level
        ship_fields = [
            "ship_name", "name", "vessel_name",
            "imo_number", "imo", 
            "flag", "flag_state",
            "class_society", "classification_society",
            "gross_tonnage", "gt",
            "built_year", "year_built"
        ]
        
        print(f"\n🔍 SEARCHING FOR SHIP FIELDS:")
        found_fields = {}
        self.find_ship_fields_recursive(response_data, ship_fields, found_fields, "")
        
        if found_fields:
            print("✅ Found ship fields:")
            for field, location in found_fields.items():
                print(f"    {field}: {location}")
        else:
            print("❌ No ship fields found in response")
        
        # Check the exact structure the frontend expects
        print(f"\n🔍 FRONTEND COMPATIBILITY CHECK:")
        
        # Frontend expects: response.data.analysis || response.data
        data_analysis = self.get_nested_value(response_data, "data.analysis")
        data_only = self.get_nested_value(response_data, "data")
        
        if data_analysis:
            print("✅ response.data.analysis: Found")
            print(f"    Type: {type(data_analysis).__name__}")
            if isinstance(data_analysis, dict):
                print(f"    Fields: {list(data_analysis.keys())}")
        else:
            print("❌ response.data.analysis: Not found")
        
        if data_only:
            print("✅ response.data: Found")
            print(f"    Type: {type(data_only).__name__}")
            if isinstance(data_only, dict):
                print(f"    Fields: {list(data_only.keys())}")
        else:
            print("❌ response.data: Not found")
        
        # Determine what the frontend would actually get
        extracted_data = data_analysis or data_only
        if extracted_data:
            print(f"\n✅ Frontend would extract: {type(extracted_data).__name__}")
            if isinstance(extracted_data, dict):
                print(f"    Available fields: {list(extracted_data.keys())}")
                
                # Check field mappings the frontend expects
                field_mappings = {
                    "ship_name": "name",
                    "imo_number": "imo_number", 
                    "flag": "flag",
                    "class_society": "ship_type",
                    "gross_tonnage": "gross_tonnage",
                    "built_year": "built_year"
                }
                
                print(f"\n🔍 FIELD MAPPING CHECK:")
                for api_field, form_field in field_mappings.items():
                    if api_field in extracted_data:
                        value = extracted_data[api_field]
                        print(f"✅ {api_field} -> {form_field}: {value}")
                    else:
                        print(f"❌ {api_field} -> {form_field}: Missing")
        else:
            print("❌ Frontend would extract: None (no data found)")
    
    def get_nested_value(self, data, path):
        """Get nested value from dictionary using dot notation"""
        try:
            keys = path.split('.')
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return current
        except:
            return None
    
    def find_ship_fields_recursive(self, data, ship_fields, found_fields, path):
        """Recursively search for ship fields in the response"""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check if this key matches any ship field
                if key.lower() in [field.lower() for field in ship_fields]:
                    found_fields[key] = current_path
                
                # Recurse into nested structures
                self.find_ship_fields_recursive(value, ship_fields, found_fields, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                self.find_ship_fields_recursive(item, ship_fields, found_fields, current_path)
    
    def test_ai_configuration(self):
        """Test AI configuration to ensure it's properly set up"""
        try:
            response = requests.get(f"{API_BASE}/ai-config", headers=self.get_headers())
            
            if response.status_code == 200:
                ai_config = response.json()
                provider = ai_config.get('provider')
                model = ai_config.get('model')
                use_emergent_key = ai_config.get('use_emergent_key', False)
                
                details = f"Provider: {provider}, Model: {model}, Use Emergent Key: {use_emergent_key}"
                self.log_test("AI Configuration Check", True, details)
                return True
            else:
                self.log_test("AI Configuration Check", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("AI Configuration Check", False, error=str(e))
            return False
    
    def run_debug_tests(self):
        """Run all debug tests for PDF analysis issue"""
        print("🐛 SHIP PDF ANALYSIS DEBUG TEST - ADD NEW SHIP FEATURE")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"PDF File URL: {PDF_FILE_URL}")
        print()
        
        # Step 1: Authentication Test
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Check AI Configuration
        self.test_ai_configuration()
        
        # Step 3: Download PDF File
        pdf_content = self.download_pdf_file()
        if not pdf_content:
            print("❌ PDF file download failed. Cannot proceed with API test.")
            return False
        
        # Step 4: Test the exact API call
        response_data = self.test_analyze_ship_certificate_api(pdf_content)
        if not response_data:
            print("❌ API call failed. Cannot analyze response structure.")
            return False
        
        # Summary
        print("=" * 80)
        print("📊 DEBUG TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        print("\n🔍 KEY FINDINGS:")
        print("-" * 40)
        
        if response_data:
            # Check if the issue is in the response structure
            data_analysis = self.get_nested_value(response_data, "data.analysis")
            data_only = self.get_nested_value(response_data, "data")
            extracted_data = data_analysis or data_only
            
            if extracted_data and isinstance(extracted_data, dict):
                ship_fields_found = []
                expected_fields = ["ship_name", "imo_number", "flag", "class_society", "gross_tonnage", "built_year"]
                
                for field in expected_fields:
                    if field in extracted_data and extracted_data[field]:
                        ship_fields_found.append(field)
                
                if ship_fields_found:
                    print(f"✅ Backend returns ship data: {ship_fields_found}")
                    print("🔍 LIKELY ISSUE: Frontend field mapping or data extraction logic")
                else:
                    print("❌ Backend returns empty/null ship data")
                    print("🔍 LIKELY ISSUE: AI analysis not extracting data from PDF")
            else:
                print("❌ Backend response structure doesn't match frontend expectations")
                print("🔍 LIKELY ISSUE: Response structure mismatch")
        
        return True

def main():
    """Main debug test execution"""
    debugger = ShipPDFAnalysisDebugger()
    success = debugger.run_debug_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
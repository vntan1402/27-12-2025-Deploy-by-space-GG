#!/usr/bin/env python3
"""
PDF Analysis Testing for Add New Ship Functionality
Comprehensive testing of the PDF analysis endpoint (/api/analyze-ship-certificate) 
with the user's specific uploaded file to debug the auto-fill issue.
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import io
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ship-cert-manager-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

# User's PDF file URL
PDF_FILE_URL = "https://customer-assets.emergentagent.com/job_ship-cert-manager-1/artifacts/7me5c9go_SS%20STAR%20PM252494416_ImagePDF.pdf"

class PDFAnalysisTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.test_results = []
        self.ai_config = None
        
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
                
                user_role = self.user_info.get('role', '').upper()
                self.log_test("Authentication Test", True, 
                            f"Logged in as {self.user_info['username']} ({user_role})")
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
    
    def test_ai_configuration(self):
        """Test AI configuration and verify Emergent LLM key usage"""
        try:
            response = requests.get(f"{API_BASE}/ai-config", headers=self.get_headers())
            
            if response.status_code == 200:
                self.ai_config = response.json()
                provider = self.ai_config.get('provider')
                model = self.ai_config.get('model')
                use_emergent_key = self.ai_config.get('use_emergent_key', False)
                
                details = f"Provider: {provider}, Model: {model}, Use Emergent Key: {use_emergent_key}"
                
                if provider and model:
                    if use_emergent_key:
                        self.log_test("AI Configuration Test", True, 
                                    f"{details} - Emergent LLM key is being used")
                    else:
                        self.log_test("AI Configuration Test", True, 
                                    f"{details} - Custom API key is being used")
                    return True
                else:
                    self.log_test("AI Configuration Test", False, 
                                error="Missing provider or model in AI configuration")
                    return False
            else:
                self.log_test("AI Configuration Test", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("AI Configuration Test", False, error=str(e))
            return False
    
    def download_pdf_file(self):
        """Download the user's PDF file for testing"""
        try:
            print(f"📥 Downloading PDF file from: {PDF_FILE_URL}")
            response = requests.get(PDF_FILE_URL, timeout=30)
            
            if response.status_code == 200:
                file_size = len(response.content)
                self.log_test("PDF File Download", True, 
                            f"Successfully downloaded PDF file ({file_size:,} bytes)")
                return response.content
            else:
                self.log_test("PDF File Download", False, 
                            error=f"Failed to download PDF: Status {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("PDF File Download", False, error=str(e))
            return None
    
    def test_analyze_ship_certificate_endpoint(self, pdf_content):
        """Test POST /api/analyze-ship-certificate endpoint with the user's PDF"""
        try:
            if not pdf_content:
                self.log_test("PDF Analysis Endpoint Test", False, 
                            error="No PDF content available")
                return None
            
            print("🔍 Testing PDF Analysis Endpoint...")
            
            # Prepare the file for upload
            files = {
                'file': ('SS_STAR_PM252494416_ImagePDF.pdf', io.BytesIO(pdf_content), 'application/pdf')
            }
            
            # Make the API request
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers(),
                timeout=60  # Allow more time for AI analysis
            )
            
            print(f"📊 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Log the complete response for debugging
                print("📋 COMPLETE API RESPONSE:")
                print("=" * 50)
                print(json.dumps(result, indent=2, default=str))
                print("=" * 50)
                
                # Check response structure
                success = result.get('success', False)
                analysis = result.get('data', {}).get('analysis', {}) if result.get('data') else result.get('analysis', {})
                
                if success and analysis:
                    # Verify expected field names
                    expected_fields = [
                        'ship_name', 'imo_number', 'class_society', 'flag', 
                        'gross_tonnage', 'deadweight', 'built_year', 'ship_owner'
                    ]
                    
                    found_fields = []
                    missing_fields = []
                    field_values = {}
                    
                    for field in expected_fields:
                        if field in analysis:
                            found_fields.append(field)
                            field_values[field] = analysis[field]
                        else:
                            missing_fields.append(field)
                    
                    # Log field analysis
                    print("\n🔍 FIELD ANALYSIS:")
                    print("=" * 30)
                    for field, value in field_values.items():
                        print(f"  {field}: {value}")
                    
                    if missing_fields:
                        print(f"\n❌ Missing fields: {missing_fields}")
                    
                    details = (f"Success: {success}, Found fields: {len(found_fields)}/{len(expected_fields)}, "
                             f"Ship Name: {analysis.get('ship_name', 'N/A')}, "
                             f"IMO: {analysis.get('imo_number', 'N/A')}, "
                             f"Flag: {analysis.get('flag', 'N/A')}")
                    
                    self.log_test("PDF Analysis Endpoint Test", True, details)
                    return result
                else:
                    error_msg = f"Success: {success}, Analysis present: {bool(analysis)}"
                    if 'error' in result:
                        error_msg += f", Error: {result['error']}"
                    
                    self.log_test("PDF Analysis Endpoint Test", False, error=error_msg)
                    return result
            else:
                error_text = response.text[:500] if response.text else "No response text"
                self.log_test("PDF Analysis Endpoint Test", False, 
                            error=f"Status: {response.status_code}, Response: {error_text}")
                return None
                
        except Exception as e:
            self.log_test("PDF Analysis Endpoint Test", False, error=str(e))
            return None
    
    def test_response_structure_compatibility(self, api_response):
        """Test if API response structure matches frontend expectations"""
        try:
            if not api_response:
                self.log_test("Response Structure Compatibility", False, 
                            error="No API response to analyze")
                return False
            
            print("🔍 ANALYZING RESPONSE STRUCTURE COMPATIBILITY...")
            
            # Check if response has the expected structure for frontend
            success = api_response.get('success', False)
            
            # Check different possible response structures
            analysis_data = None
            
            # Structure 1: response.data.analysis
            if 'data' in api_response and 'analysis' in api_response['data']:
                analysis_data = api_response['data']['analysis']
                structure_type = "response.data.analysis"
            
            # Structure 2: response.analysis
            elif 'analysis' in api_response:
                analysis_data = api_response['analysis']
                structure_type = "response.analysis"
            
            # Structure 3: Direct fields in response
            else:
                # Check if ship fields are directly in response
                ship_fields = ['ship_name', 'imo_number', 'class_society', 'flag']
                if any(field in api_response for field in ship_fields):
                    analysis_data = api_response
                    structure_type = "direct response fields"
            
            if analysis_data:
                # Frontend expects these specific field names
                frontend_expected_fields = {
                    'ship_name': 'Ship Name',
                    'imo_number': 'IMO Number', 
                    'class_society': 'Class Society',
                    'flag': 'Flag',
                    'gross_tonnage': 'Gross Tonnage',
                    'deadweight': 'Deadweight',
                    'built_year': 'Built Year',
                    'ship_owner': 'Ship Owner'
                }
                
                compatibility_report = []
                field_mapping = {}
                
                for frontend_field, display_name in frontend_expected_fields.items():
                    if frontend_field in analysis_data:
                        value = analysis_data[frontend_field]
                        field_mapping[frontend_field] = value
                        compatibility_report.append(f"✅ {display_name}: {value}")
                    else:
                        compatibility_report.append(f"❌ {display_name}: MISSING")
                
                print(f"\n📋 FRONTEND COMPATIBILITY REPORT (Structure: {structure_type}):")
                print("=" * 60)
                for report_line in compatibility_report:
                    print(f"  {report_line}")
                
                compatible_fields = len(field_mapping)
                total_fields = len(frontend_expected_fields)
                
                details = (f"Structure: {structure_type}, "
                         f"Compatible fields: {compatible_fields}/{total_fields}, "
                         f"Success flag: {success}")
                
                if compatible_fields >= 4:  # At least half the fields should be present
                    self.log_test("Response Structure Compatibility", True, details)
                    return True
                else:
                    self.log_test("Response Structure Compatibility", False, 
                                error=f"Only {compatible_fields}/{total_fields} fields compatible")
                    return False
            else:
                self.log_test("Response Structure Compatibility", False, 
                            error="No analysis data found in any expected structure")
                return False
                
        except Exception as e:
            self.log_test("Response Structure Compatibility", False, error=str(e))
            return False
    
    def test_mock_frontend_auto_fill(self, api_response):
        """Simulate frontend auto-fill logic to identify issues"""
        try:
            if not api_response:
                self.log_test("Mock Frontend Auto-Fill Test", False, 
                            error="No API response to test")
                return False
            
            print("🎯 SIMULATING FRONTEND AUTO-FILL LOGIC...")
            
            # Simulate the frontend handlePdfAnalysis function logic
            success = api_response.get('success', False)
            
            if not success:
                self.log_test("Mock Frontend Auto-Fill Test", False, 
                            error="API response success is false")
                return False
            
            # Try to extract analysis data (multiple possible structures)
            analysis = None
            
            if 'data' in api_response and 'analysis' in api_response['data']:
                analysis = api_response['data']['analysis']
            elif 'analysis' in api_response:
                analysis = api_response['analysis']
            else:
                analysis = api_response  # Fallback to direct response
            
            if not analysis:
                self.log_test("Mock Frontend Auto-Fill Test", False, 
                            error="No analysis data found in response")
                return False
            
            # Simulate form field mapping
            form_fields = {
                'shipName': analysis.get('ship_name', ''),
                'imoNumber': analysis.get('imo_number', ''),
                'classSociety': analysis.get('class_society', ''),
                'flag': analysis.get('flag', ''),
                'grossTonnage': str(analysis.get('gross_tonnage', '')) if analysis.get('gross_tonnage') else '',
                'deadweight': str(analysis.get('deadweight', '')) if analysis.get('deadweight') else '',
                'builtYear': str(analysis.get('built_year', '')) if analysis.get('built_year') else '',
                'shipOwner': analysis.get('ship_owner', '')
            }
            
            # Check which fields would be populated
            populated_fields = []
            empty_fields = []
            
            for field_name, field_value in form_fields.items():
                if field_value and str(field_value).strip() and str(field_value).strip().lower() != 'null':
                    populated_fields.append(f"{field_name}: '{field_value}'")
                else:
                    empty_fields.append(field_name)
            
            print(f"\n📝 FORM FIELD SIMULATION RESULTS:")
            print("=" * 40)
            print(f"✅ Fields that would be populated ({len(populated_fields)}):")
            for field in populated_fields:
                print(f"    {field}")
            
            if empty_fields:
                print(f"\n❌ Fields that would remain empty ({len(empty_fields)}):")
                for field in empty_fields:
                    print(f"    {field}")
            
            # Determine if auto-fill would work
            if len(populated_fields) > 0:
                details = f"Would populate {len(populated_fields)}/8 fields"
                self.log_test("Mock Frontend Auto-Fill Test", True, details)
                return True
            else:
                self.log_test("Mock Frontend Auto-Fill Test", False, 
                            error="No fields would be populated - all values are empty or null")
                return False
                
        except Exception as e:
            self.log_test("Mock Frontend Auto-Fill Test", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all PDF analysis tests"""
        print("🧪 PDF ANALYSIS FUNCTIONALITY COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"PDF File URL: {PDF_FILE_URL}")
        print()
        
        # Step 1: Authentication Test
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Test AI Configuration
        if not self.test_ai_configuration():
            print("❌ AI configuration test failed. PDF analysis may not work.")
            # Continue with tests to see what happens
        
        # Step 3: Download PDF File
        pdf_content = self.download_pdf_file()
        if not pdf_content:
            print("❌ PDF file download failed. Cannot proceed with analysis tests.")
            return False
        
        # Step 4: Test PDF Analysis Endpoint
        api_response = self.test_analyze_ship_certificate_endpoint(pdf_content)
        if not api_response:
            print("❌ PDF analysis endpoint test failed.")
            return False
        
        # Step 5: Test Response Structure Compatibility
        if not self.test_response_structure_compatibility(api_response):
            print("❌ Response structure compatibility test failed.")
            # Continue to see auto-fill simulation
        
        # Step 6: Test Mock Frontend Auto-Fill
        if not self.test_mock_frontend_auto_fill(api_response):
            print("❌ Mock frontend auto-fill test failed.")
        
        # Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Detailed analysis
        print("\n🔍 DETAILED ANALYSIS:")
        print("=" * 30)
        
        if api_response:
            success = api_response.get('success', False)
            has_analysis = bool(api_response.get('data', {}).get('analysis') or api_response.get('analysis'))
            
            print(f"API Success Flag: {success}")
            print(f"Analysis Data Present: {has_analysis}")
            
            if has_analysis:
                analysis = api_response.get('data', {}).get('analysis', {}) or api_response.get('analysis', {})
                non_null_fields = sum(1 for v in analysis.values() if v and str(v).strip().lower() != 'null')
                print(f"Non-null Analysis Fields: {non_null_fields}")
                
                if success and non_null_fields > 0:
                    print("\n✅ CONCLUSION: Backend is working correctly!")
                    print("   The issue is likely in the frontend auto-fill logic.")
                    print("   Frontend may not be correctly accessing response.data.analysis")
                else:
                    print("\n❌ CONCLUSION: Backend analysis is not extracting data correctly.")
                    print("   AI model may need adjustment or PDF content is not readable.")
            else:
                print("\n❌ CONCLUSION: Backend is not returning analysis data.")
                print("   Check AI configuration and PDF processing logic.")
        
        return passed >= (total * 0.6)  # 60% pass rate acceptable for debugging

def main():
    """Main test execution"""
    tester = PDFAnalysisTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
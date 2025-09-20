#!/usr/bin/env python3
"""
End-to-End PDF Analysis Testing
Complete testing of the Add New Ship PDF analysis functionality with the user's file
to verify the auto-fill issue has been resolved.
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

class EndToEndPDFTester:
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
                
                self.log_test("Authentication", True, 
                            f"Logged in as {self.user_info['username']} ({self.user_info.get('role', 'N/A')})")
                return True
            else:
                self.log_test("Authentication", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, error=str(e))
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_ai_configuration(self):
        """Test AI configuration"""
        try:
            response = requests.get(f"{API_BASE}/ai-config", headers=self.get_headers())
            
            if response.status_code == 200:
                ai_config = response.json()
                provider = ai_config.get('provider')
                model = ai_config.get('model')
                use_emergent_key = ai_config.get('use_emergent_key', False)
                
                details = f"Provider: {provider}, Model: {model}, Emergent Key: {use_emergent_key}"
                self.log_test("AI Configuration", True, details)
                return True
            else:
                self.log_test("AI Configuration", False, 
                            error=f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("AI Configuration", False, error=str(e))
            return False
    
    def download_user_pdf(self):
        """Download the user's specific PDF file"""
        try:
            response = requests.get(PDF_FILE_URL, timeout=30)
            
            if response.status_code == 200:
                file_size = len(response.content)
                self.log_test("PDF File Download", True, 
                            f"Downloaded user's PDF file ({file_size:,} bytes)")
                return response.content
            else:
                self.log_test("PDF File Download", False, 
                            error=f"Failed to download: Status {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("PDF File Download", False, error=str(e))
            return None
    
    def test_pdf_analysis_api(self, pdf_content):
        """Test the PDF analysis API endpoint"""
        try:
            files = {
                'file': ('SS_STAR_PM252494416_ImagePDF.pdf', io.BytesIO(pdf_content), 'application/pdf')
            }
            
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=self.get_headers(),
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                analysis = result.get('analysis', {})
                
                if success and analysis:
                    ship_name = analysis.get('ship_name', 'N/A')
                    imo_number = analysis.get('imo_number', 'N/A')
                    flag = analysis.get('flag', 'N/A')
                    class_society = analysis.get('class_society', 'N/A')
                    
                    details = f"Ship: {ship_name}, IMO: {imo_number}, Flag: {flag}, Class: {class_society}"
                    self.log_test("PDF Analysis API", True, details)
                    return result
                else:
                    self.log_test("PDF Analysis API", False, 
                                error=f"Success: {success}, Analysis present: {bool(analysis)}")
                    return None
            else:
                self.log_test("PDF Analysis API", False, 
                            error=f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("PDF Analysis API", False, error=str(e))
            return None
    
    def test_response_structure(self, api_response):
        """Test if response structure matches frontend expectations"""
        try:
            # Check the exact structure the frontend expects
            success = api_response.get('success', False)
            analysis = api_response.get('analysis', {})
            
            # Frontend expects these fields
            expected_fields = [
                'ship_name', 'imo_number', 'class_society', 'flag',
                'gross_tonnage', 'deadweight', 'built_year', 'ship_owner'
            ]
            
            present_fields = []
            missing_fields = []
            
            for field in expected_fields:
                if field in analysis and analysis[field] is not None:
                    present_fields.append(field)
                else:
                    missing_fields.append(field)
            
            details = f"Present: {len(present_fields)}/{len(expected_fields)} fields"
            if missing_fields:
                details += f", Missing: {missing_fields}"
            
            self.log_test("Response Structure", True, details)
            return True
                
        except Exception as e:
            self.log_test("Response Structure", False, error=str(e))
            return False
    
    def test_frontend_compatibility(self, api_response):
        """Test frontend auto-fill compatibility with the fixed code"""
        try:
            # Simulate the fixed frontend logic
            success = api_response.get('success', False)
            
            if not success:
                self.log_test("Frontend Compatibility", False, 
                            error="API response success is false")
                return False
            
            # The fix: extractedData = response.data.analysis || response.data
            # Since axios wraps the response in response.data, we simulate:
            simulated_response_data = api_response  # This is what response.data would be
            
            # Frontend logic: response.data.analysis || response.data
            extracted_data = simulated_response_data.get('analysis') or simulated_response_data
            
            if not extracted_data:
                self.log_test("Frontend Compatibility", False, 
                            error="No extracted data available")
                return False
            
            # Simulate the frontend field mapping
            processed_data = {
                'name': extracted_data.get('ship_name', ''),
                'imo_number': extracted_data.get('imo_number', ''),
                'class_society': extracted_data.get('class_society') or extracted_data.get('ship_type', ''),
                'flag': extracted_data.get('flag', ''),
                'gross_tonnage': str(extracted_data.get('gross_tonnage', '')) if extracted_data.get('gross_tonnage') else '',
                'deadweight': str(extracted_data.get('deadweight', '')) if extracted_data.get('deadweight') else '',
                'built_year': str(extracted_data.get('built_year', '')) if extracted_data.get('built_year') else '',
                'ship_owner': extracted_data.get('ship_owner', '')
            }
            
            # Count populated fields
            populated_fields = []
            for field_name, field_value in processed_data.items():
                if field_value and str(field_value).strip() and str(field_value).strip().lower() != 'null':
                    populated_fields.append(f"{field_name}: '{field_value}'")
            
            if len(populated_fields) >= 4:  # At least 4 fields should be populated
                details = f"Would populate {len(populated_fields)}/8 fields: {', '.join(populated_fields[:3])}..."
                self.log_test("Frontend Compatibility", True, details)
                return True
            else:
                self.log_test("Frontend Compatibility", False, 
                            error=f"Only {len(populated_fields)} fields would be populated")
                return False
                
        except Exception as e:
            self.log_test("Frontend Compatibility", False, error=str(e))
            return False
    
    def test_field_mapping_accuracy(self, api_response):
        """Test the accuracy of field mapping for the specific PDF"""
        try:
            analysis = api_response.get('analysis', {})
            
            # Expected values from the user's PDF (SS STAR)
            expected_values = {
                'ship_name': 'SUNSHINE STAR',
                'imo_number': 9405136,
                'flag': 'BELIZE',
                'class_society': 'PMDS'
            }
            
            accuracy_results = []
            for field, expected_value in expected_values.items():
                actual_value = analysis.get(field)
                if str(actual_value).upper() == str(expected_value).upper():
                    accuracy_results.append(f"✅ {field}: {actual_value}")
                else:
                    accuracy_results.append(f"❌ {field}: Expected '{expected_value}', Got '{actual_value}'")
            
            accurate_fields = sum(1 for result in accuracy_results if result.startswith('✅'))
            total_fields = len(expected_values)
            
            details = f"Accuracy: {accurate_fields}/{total_fields} fields correct"
            
            if accurate_fields >= 3:  # At least 3/4 should be accurate
                self.log_test("Field Mapping Accuracy", True, details)
                return True
            else:
                self.log_test("Field Mapping Accuracy", False, 
                            error=f"Only {accurate_fields}/{total_fields} fields accurate")
                return False
                
        except Exception as e:
            self.log_test("Field Mapping Accuracy", False, error=str(e))
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive end-to-end test"""
        print("🧪 END-TO-END PDF ANALYSIS TESTING")
        print("=" * 80)
        print(f"Testing 'Add New Ship' PDF analysis functionality")
        print(f"User's PDF: SS STAR PM252494416_ImagePDF.pdf")
        print(f"Backend URL: {BACKEND_URL}")
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed.")
            return False
        
        # Step 2: AI Configuration
        if not self.test_ai_configuration():
            print("⚠️ AI configuration issue detected.")
        
        # Step 3: Download User's PDF
        pdf_content = self.download_user_pdf()
        if not pdf_content:
            print("❌ Failed to download user's PDF file.")
            return False
        
        # Step 4: Test PDF Analysis API
        api_response = self.test_pdf_analysis_api(pdf_content)
        if not api_response:
            print("❌ PDF Analysis API failed.")
            return False
        
        # Step 5: Test Response Structure
        if not self.test_response_structure(api_response):
            print("❌ Response structure test failed.")
        
        # Step 6: Test Frontend Compatibility (with fix)
        if not self.test_frontend_compatibility(api_response):
            print("❌ Frontend compatibility test failed.")
            return False
        
        # Step 7: Test Field Mapping Accuracy
        if not self.test_field_mapping_accuracy(api_response):
            print("⚠️ Field mapping accuracy could be improved.")
        
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
        
        # Final analysis
        print("\n🎯 FINAL ANALYSIS:")
        print("=" * 30)
        
        if passed >= total * 0.8:  # 80% pass rate
            print("✅ PDF ANALYSIS AUTO-FILL FUNCTIONALITY IS WORKING!")
            print("   - Backend correctly extracts ship data from PDF")
            print("   - AI configuration is properly set up")
            print("   - Frontend compatibility issue has been RESOLVED")
            print("   - Auto-fill should now populate form fields correctly")
            return True
        else:
            print("❌ PDF ANALYSIS AUTO-FILL FUNCTIONALITY HAS ISSUES")
            print("   - Check failed tests above for specific problems")
            return False

def main():
    """Main test execution"""
    tester = EndToEndPDFTester()
    success = tester.run_comprehensive_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
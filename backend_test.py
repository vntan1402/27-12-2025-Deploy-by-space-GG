#!/usr/bin/env python3
"""
Backend Testing Script for AI Configuration & Certificate Analysis
Tests the newly implemented AI Configuration and Real Certificate Analysis features.
"""

import requests
import json
import os
import sys
from pathlib import Path

# Configuration
BACKEND_URL = "https://seadocs-migration.preview.emergentagent.com/api"
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def authenticate(self):
        """Authenticate with the backend"""
        print("\n🔐 Testing Authentication...")
        
        try:
            # Login
            login_data = {
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_info = data.get("user")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log_test("User Authentication", True, 
                             f"User: {self.user_info.get('username')}, Role: {self.user_info.get('role')}")
                return True
            else:
                self.log_test("User Authentication", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_ai_config_get(self):
        """Test GET /api/ai-config endpoint"""
        print("\n🤖 Testing AI Configuration GET...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/ai-config")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["provider", "model", "api_key_configured"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("AI Config GET - Structure", True, 
                                 f"Provider: {data.get('provider')}, Model: {data.get('model')}")
                    
                    # Check if using EMERGENT_LLM_KEY
                    if data.get("api_key_configured"):
                        self.log_test("AI Config GET - API Key", True, "API key is configured")
                    else:
                        self.log_test("AI Config GET - API Key", False, "API key not configured")
                    
                    return data
                else:
                    self.log_test("AI Config GET - Structure", False, 
                                 f"Missing fields: {missing_fields}")
                    return None
            else:
                self.log_test("AI Config GET", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("AI Config GET", False, f"Exception: {str(e)}")
            return None
    
    def test_ai_config_update(self):
        """Test PUT /api/ai-config endpoint"""
        print("\n🔧 Testing AI Configuration UPDATE...")
        
        try:
            # First get current config
            current_config = self.test_ai_config_get()
            if not current_config:
                self.log_test("AI Config UPDATE - Prerequisites", False, "Could not get current config")
                return False
            
            # Test update with new settings
            update_data = {
                "provider": "google",
                "model": "gemini-2.0-flash",
                "api_key": "test-key-update",
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            response = self.session.put(f"{BACKEND_URL}/ai-config", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify update
                if (data.get("provider") == update_data["provider"] and 
                    data.get("model") == update_data["model"]):
                    self.log_test("AI Config UPDATE", True, 
                                 f"Updated to Provider: {data.get('provider')}, Model: {data.get('model')}")
                    return True
                else:
                    self.log_test("AI Config UPDATE", False, "Update not reflected in response")
                    return False
            else:
                self.log_test("AI Config UPDATE", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("AI Config UPDATE", False, f"Exception: {str(e)}")
            return False
    
    def test_certificate_analyze_file(self):
        """Test POST /api/certificates/analyze-file endpoint"""
        print("\n📄 Testing Certificate AI Analysis...")
        
        # Look for test certificate files
        test_files = [
            "/app/test_coc_certificate.pdf",
            "/app/MINH_ANH_09_certificate.pdf",
            "/app/test_poor_quality_cert.pdf"
        ]
        
        test_file = None
        for file_path in test_files:
            if os.path.exists(file_path):
                test_file = file_path
                break
        
        if not test_file:
            # Create a simple test file
            test_content = """
            CERTIFICATE OF COMPETENCY
            Ship Name: TEST SHIP 01
            IMO Number: 1234567
            Certificate Number: TEST-COC-2025-001
            Issue Date: January 15, 2025
            Valid Date: January 15, 2028
            Issued By: Test Maritime Authority
            """
            
            test_file = "/app/test_certificate_analysis.txt"
            with open(test_file, "w") as f:
                f.write(test_content)
            
            self.log_test("Certificate Analysis - Test File", True, f"Created test file: {test_file}")
        
        try:
            # Test without ship_id (standby analysis)
            with open(test_file, "rb") as f:
                files = {"file": (os.path.basename(test_file), f, "application/pdf")}
                response = self.session.post(f"{BACKEND_URL}/certificates/analyze-file", files=files)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                expected_fields = ["success", "analysis_result"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    analysis = data.get("analysis_result", {})
                    
                    # Check if AI analysis was performed (not mock)
                    if "confidence" in analysis or "extracted_data" in analysis:
                        self.log_test("Certificate Analysis - AI Processing", True, 
                                     f"AI analysis completed with confidence: {analysis.get('confidence', 'N/A')}")
                        
                        # Check for extracted data
                        extracted_data = analysis.get("extracted_data", {})
                        if extracted_data:
                            extracted_fields = list(extracted_data.keys())
                            self.log_test("Certificate Analysis - Data Extraction", True, 
                                         f"Extracted fields: {extracted_fields}")
                        else:
                            self.log_test("Certificate Analysis - Data Extraction", False, 
                                         "No extracted data found")
                        
                        return True
                    else:
                        self.log_test("Certificate Analysis - AI Processing", False, 
                                     "Response appears to be mock data")
                        return False
                else:
                    self.log_test("Certificate Analysis - Structure", False, 
                                 f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Certificate Analysis", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Certificate Analysis", False, f"Exception: {str(e)}")
            return False
    
    def test_certificate_analyze_with_ship_id(self):
        """Test certificate analysis with ship_id parameter"""
        print("\n🚢 Testing Certificate Analysis with Ship ID...")
        
        try:
            # First, get a list of ships to use a valid ship_id
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                if ships and len(ships) > 0:
                    ship_id = ships[0].get("id")
                    ship_name = ships[0].get("name", "Unknown")
                    
                    self.log_test("Certificate Analysis - Ship ID Setup", True, 
                                 f"Using ship: {ship_name} (ID: {ship_id})")
                    
                    # Test with ship_id
                    test_file = "/app/test_certificate_analysis.txt"
                    if os.path.exists(test_file):
                        with open(test_file, "rb") as f:
                            files = {"file": (os.path.basename(test_file), f, "application/pdf")}
                            params = {"ship_id": ship_id}
                            response = self.session.post(f"{BACKEND_URL}/certificates/analyze-file", 
                                                       files=files, params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            self.log_test("Certificate Analysis with Ship ID", True, 
                                         f"Analysis completed for ship: {ship_name}")
                            return True
                        else:
                            self.log_test("Certificate Analysis with Ship ID", False, 
                                         f"Status: {response.status_code}")
                            return False
                    else:
                        self.log_test("Certificate Analysis with Ship ID", False, 
                                     "Test file not available")
                        return False
                else:
                    self.log_test("Certificate Analysis - Ship ID Setup", False, 
                                 "No ships available for testing")
                    return False
            else:
                self.log_test("Certificate Analysis - Ship ID Setup", False, 
                             f"Could not fetch ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Certificate Analysis with Ship ID", False, f"Exception: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        print("\n⚠️  Testing Error Handling...")
        
        try:
            # Test with invalid file
            invalid_content = b"This is not a valid certificate file"
            files = {"file": ("invalid.txt", invalid_content, "text/plain")}
            
            response = self.session.post(f"{BACKEND_URL}/certificates/analyze-file", files=files)
            
            # Should handle gracefully (either success with low confidence or proper error)
            if response.status_code in [200, 400, 422]:
                self.log_test("Error Handling - Invalid File", True, 
                             f"Handled gracefully with status: {response.status_code}")
                return True
            else:
                self.log_test("Error Handling - Invalid File", False, 
                             f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Error Handling - Invalid File", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Backend Testing for AI Configuration & Certificate Analysis")
        print("=" * 80)
        
        # Authentication is required for all tests
        if not self.authenticate():
            print("\n❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run AI Configuration tests
        self.test_ai_config_get()
        self.test_ai_config_update()
        
        # Run Certificate Analysis tests
        self.test_certificate_analyze_file()
        self.test_certificate_analyze_with_ship_id()
        
        # Run Error Handling tests
        self.test_error_handling()
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"  - {result['test']}")

def main():
    """Main function"""
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Backend testing completed!")
    else:
        print("\n💥 Backend testing failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
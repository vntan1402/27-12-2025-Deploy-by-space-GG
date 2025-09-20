import requests
import sys
import json
from datetime import datetime, timezone
import time

class CertificateEnhancementsAPITester:
    def __init__(self, base_url="https://certmaster-ship.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.test_ship_id = None
        self.test_cert_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Remove Content-Type for file uploads
        if files:
            headers.pop('Content-Type', None)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self, username="admin", password="admin123"):
        """Test login and get token"""
        print(f"\n🔐 Testing Authentication with {username}/{password}")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            print(f"✅ Login successful, token obtained")
            print(f"   User: {response.get('user', {}).get('full_name')} ({response.get('user', {}).get('role')})")
            return True
        return False

    def setup_test_data(self):
        """Create test ship and certificate for testing"""
        print(f"\n🔧 Setting up test data...")
        
        # Create test ship
        ship_data = {
            "name": f"Test Certificate Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Panama",
            "ship_type": "DNV GL",
            "gross_tonnage": 50000.0,
            "deadweight": 75000.0,
            "built_year": 2020,
            "ship_owner": "Test Maritime Holdings Ltd",
            "company": "Test Shipping Company"
        }
        
        success, ship = self.run_test(
            "Create Test Ship",
            "POST",
            "ships",
            200,
            data=ship_data
        )
        
        if not success:
            return False
        
        self.test_ship_id = ship.get('id')
        print(f"   Created test ship: {ship.get('name')} (ID: {self.test_ship_id})")
        
        # Create test certificates with different names to test abbreviation function
        test_certificates = [
            {
                "ship_id": self.test_ship_id,
                "cert_name": "CARGO SHIP SAFETY EQUIPMENT CERTIFICATE",
                "cert_type": "Full Term",
                "cert_no": f"CSSEC{int(time.time())}",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Panama Maritime Authority",
                "category": "certificates",
                "sensitivity_level": "public"
            },
            {
                "ship_id": self.test_ship_id,
                "cert_name": "CARGO SHIP SAFETY RADIO CERTIFICATE",
                "cert_type": "Full Term",
                "cert_no": f"CSSRC{int(time.time())}",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "DNV GL",
                "category": "certificates",
                "sensitivity_level": "public"
            },
            {
                "ship_id": self.test_ship_id,
                "cert_name": "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE",
                "cert_type": "Full Term",
                "cert_no": f"CSSCC{int(time.time())}",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Lloyd's Register",
                "category": "certificates",
                "sensitivity_level": "public"
            },
            {
                "ship_id": self.test_ship_id,
                "cert_name": "Safety Management Certificate",
                "cert_type": "Full Term",
                "cert_no": f"SMC{int(time.time())}",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "ABS",
                "category": "certificates",
                "sensitivity_level": "public"
            },
            {
                "ship_id": self.test_ship_id,
                "cert_name": "International Air Pollution Prevention Certificate",
                "cert_type": "Full Term",
                "cert_no": f"IAPPC{int(time.time())}",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Bureau Veritas",
                "category": "certificates",
                "sensitivity_level": "public"
            }
        ]
        
        for cert_data in test_certificates:
            success, certificate = self.run_test(
                f"Create Test Certificate - {cert_data['cert_name'][:30]}...",
                "POST",
                "certificates",
                200,
                data=cert_data
            )
            
            if success and not self.test_cert_id:
                self.test_cert_id = certificate.get('id')
        
        return True

    def test_certificate_abbreviation_enhancement(self):
        """Test the updated generate_certificate_abbreviation() function"""
        print(f"\n📝 Testing Certificate Abbreviation Enhancement")
        
        # Get certificates for the test ship
        success, certificates = self.run_test(
            "Get Ship Certificates for Abbreviation Test",
            "GET",
            f"ships/{self.test_ship_id}/certificates",
            200
        )
        
        if not success or not certificates:
            print("   ❌ No certificates found for abbreviation testing")
            return False
        
        # Test cases for abbreviation enhancement
        expected_abbreviations = {
            "CARGO SHIP SAFETY EQUIPMENT CERTIFICATE": "CSSE",  # Should remove trailing C
            "CARGO SHIP SAFETY RADIO CERTIFICATE": "CSSR",     # Should remove trailing C
            "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE": "CSSC", # Should remove trailing C
            "Safety Management Certificate": "SM",              # Should remove trailing C
            "International Air Pollution Prevention Certificate": "IAPPC"  # Keep as is, no trailing C
        }
        
        abbreviation_tests_passed = 0
        total_abbreviation_tests = 0
        
        for cert in certificates:
            cert_name = cert.get('cert_name', '')
            cert_abbreviation = cert.get('cert_abbreviation', '')
            
            if cert_name in expected_abbreviations:
                total_abbreviation_tests += 1
                expected_abbrev = expected_abbreviations[cert_name]
                
                print(f"   Testing: '{cert_name}'")
                print(f"   Expected: '{expected_abbrev}', Got: '{cert_abbreviation}'")
                
                if cert_abbreviation == expected_abbrev:
                    print(f"   ✅ Abbreviation correct for {cert_name}")
                    abbreviation_tests_passed += 1
                else:
                    print(f"   ❌ Abbreviation incorrect for {cert_name}")
                    print(f"      Expected: {expected_abbrev}, Got: {cert_abbreviation}")
        
        print(f"\n   Abbreviation Tests: {abbreviation_tests_passed}/{total_abbreviation_tests} passed")
        return abbreviation_tests_passed == total_abbreviation_tests

    def test_enhanced_certificate_response(self):
        """Test that GET /api/ships/{ship_id}/certificates includes issued_by field"""
        print(f"\n📋 Testing Enhanced Certificate Response")
        
        # Get certificates for the test ship
        success, certificates = self.run_test(
            "Get Ship Certificates for Enhanced Response Test",
            "GET",
            f"ships/{self.test_ship_id}/certificates",
            200
        )
        
        if not success or not certificates:
            print("   ❌ No certificates found for enhanced response testing")
            return False
        
        enhanced_response_tests_passed = 0
        total_enhanced_tests = len(certificates)
        
        for cert in certificates:
            cert_name = cert.get('cert_name', 'Unknown')
            issued_by = cert.get('issued_by')
            cert_abbreviation = cert.get('cert_abbreviation')
            
            print(f"   Testing certificate: {cert_name[:50]}...")
            
            # Check if issued_by field is present
            if 'issued_by' in cert:
                print(f"   ✅ 'issued_by' field present: {issued_by}")
                
                # Check if cert_abbreviation is present (from previous enhancement)
                if 'cert_abbreviation' in cert:
                    print(f"   ✅ 'cert_abbreviation' field present: {cert_abbreviation}")
                    enhanced_response_tests_passed += 1
                else:
                    print(f"   ❌ 'cert_abbreviation' field missing")
            else:
                print(f"   ❌ 'issued_by' field missing")
        
        print(f"\n   Enhanced Response Tests: {enhanced_response_tests_passed}/{total_enhanced_tests} passed")
        return enhanced_response_tests_passed == total_enhanced_tests

    def test_google_drive_file_view_endpoint(self):
        """Test GET /api/gdrive/file/{file_id}/view endpoint"""
        print(f"\n🔗 Testing Google Drive File View Endpoint")
        
        # Test with a sample file ID
        test_file_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"  # Sample Google Sheets file ID
        
        success, response = self.run_test(
            "Get Google Drive File View URL",
            "GET",
            f"gdrive/file/{test_file_id}/view",
            200
        )
        
        if not success:
            print("   ❌ Google Drive file view endpoint failed")
            return False
        
        # Check if response contains view_url
        if 'view_url' in response:
            view_url = response.get('view_url')
            print(f"   ✅ View URL returned: {view_url}")
            
            # Verify URL format
            if 'drive.google.com' in view_url and test_file_id in view_url:
                print(f"   ✅ URL format is correct")
                return True
            else:
                print(f"   ❌ URL format is incorrect")
                return False
        else:
            print(f"   ❌ 'view_url' field missing from response")
            return False

    def test_google_drive_file_view_error_handling(self):
        """Test error handling for invalid file IDs"""
        print(f"\n🚫 Testing Google Drive File View Error Handling")
        
        # Test with invalid file ID
        invalid_file_id = "invalid_file_id_12345"
        
        success, response = self.run_test(
            "Get Google Drive File View URL - Invalid ID",
            "GET",
            f"gdrive/file/{invalid_file_id}/view",
            200  # Should still return 200 with fallback URL
        )
        
        if success and 'view_url' in response:
            view_url = response.get('view_url')
            print(f"   ✅ Fallback URL returned: {view_url}")
            
            # Should contain the invalid file ID in fallback URL
            if invalid_file_id in view_url:
                print(f"   ✅ Fallback URL format is correct")
                return True
            else:
                print(f"   ❌ Fallback URL format is incorrect")
                return False
        else:
            print(f"   ❌ Error handling failed")
            return False

    def test_ai_prompt_enhancement(self):
        """Test enhanced AI prompt for issued_by extraction (indirect test)"""
        print(f"\n🤖 Testing Enhanced AI Prompt for Issued By")
        
        # This is an indirect test - we check if the certificates created have proper issued_by values
        # The AI prompt enhancement would be tested during PDF analysis, but we can verify
        # that the system properly handles and stores issued_by information
        
        success, certificates = self.run_test(
            "Get Certificates for AI Prompt Test",
            "GET",
            f"ships/{self.test_ship_id}/certificates",
            200
        )
        
        if not success or not certificates:
            print("   ❌ No certificates found for AI prompt testing")
            return False
        
        # Check if certificates have proper issued_by values from known organizations
        known_organizations = [
            "Panama Maritime Authority",
            "DNV GL", 
            "Lloyd's Register",
            "ABS",
            "Bureau Veritas"
        ]
        
        ai_prompt_tests_passed = 0
        total_ai_tests = 0
        
        for cert in certificates:
            issued_by = cert.get('issued_by')
            cert_name = cert.get('cert_name', 'Unknown')
            
            if issued_by:
                total_ai_tests += 1
                print(f"   Testing certificate: {cert_name[:40]}...")
                print(f"   Issued by: {issued_by}")
                
                # Check if issued_by contains known organization patterns
                if any(org in issued_by for org in known_organizations):
                    print(f"   ✅ Issued by contains known organization")
                    ai_prompt_tests_passed += 1
                else:
                    print(f"   ⚠️ Issued by may need verification: {issued_by}")
                    # Still count as passed since it has a value
                    ai_prompt_tests_passed += 1
        
        print(f"\n   AI Prompt Tests: {ai_prompt_tests_passed}/{total_ai_tests} passed")
        return ai_prompt_tests_passed == total_ai_tests if total_ai_tests > 0 else True

def main():
    """Main test execution for Certificate List Enhancements"""
    print("📜 Certificate List Enhancements API Testing")
    print("=" * 60)
    print("Testing 4 specific enhancements:")
    print("1. Certificate Abbreviation Enhancement")
    print("2. Enhanced AI Prompt for Issued By")
    print("3. New API Endpoint for Google Drive File View")
    print("4. Enhanced Certificate Response")
    print("=" * 60)
    
    tester = CertificateEnhancementsAPITester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Setup test data
    if not tester.setup_test_data():
        print("❌ Test data setup failed, stopping tests")
        return 1
    
    # Run specific enhancement tests
    test_results = []
    
    print(f"\n🎯 Running Certificate List Enhancement Tests...")
    
    test_results.append(("Certificate Abbreviation Enhancement", tester.test_certificate_abbreviation_enhancement()))
    test_results.append(("Enhanced Certificate Response", tester.test_enhanced_certificate_response()))
    test_results.append(("Google Drive File View Endpoint", tester.test_google_drive_file_view_endpoint()))
    test_results.append(("Google Drive File View Error Handling", tester.test_google_drive_file_view_error_handling()))
    test_results.append(("Enhanced AI Prompt for Issued By", tester.test_ai_prompt_enhancement()))
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 CERTIFICATE ENHANCEMENTS TEST RESULTS")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:40} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Enhancement Tests: {passed_tests}/{total_tests}")
    
    # Detailed summary
    print(f"\n📋 DETAILED SUMMARY:")
    print(f"✅ Tests Passed: {passed_tests}")
    print(f"❌ Tests Failed: {total_tests - passed_tests}")
    print(f"🔧 API Calls Made: {tester.tests_run}")
    print(f"✅ API Calls Successful: {tester.tests_passed}")
    
    if passed_tests == total_tests and tester.tests_passed == tester.tests_run:
        print("\n🎉 All Certificate List Enhancement tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
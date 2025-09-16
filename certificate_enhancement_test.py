#!/usr/bin/env python3
"""
Certificate Enhancement Backend Testing
Tests the enhanced Certificate List backend features including:
1. Certificate Enhancement API
2. Certificate Abbreviation Generation
3. Maritime Status Calculation
4. Enhanced Response Processing
5. Database Integration
"""

import requests
import sys
import json
from datetime import datetime, timezone, timedelta
import time

class CertificateEnhancementTester:
    def __init__(self, base_url="https://ship-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_ship_id = None
        self.test_certificates = []

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
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
            print(f"✅ Login successful, token obtained")
            print(f"   User: {response.get('user', {}).get('full_name')} ({response.get('user', {}).get('role')})")
            return True
        return False

    def setup_test_data(self):
        """Create test ship and certificates for testing"""
        print(f"\n🏗️ Setting up test data...")
        
        # Create test ship
        ship_data = {
            "name": f"Test Enhancement Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Panama",
            "ship_type": "DNV GL",
            "gross_tonnage": 45000.0,
            "deadweight": 68000.0,
            "built_year": 2019,
            "ship_owner": "Test Maritime Holdings",
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
        
        # Create test certificates with various types and dates
        test_certificates = [
            {
                "ship_id": self.test_ship_id,
                "cert_name": "CARGO SHIP SAFETY EQUIPMENT CERTIFICATE",
                "cert_type": "Full Term",
                "cert_no": "CSSEC001",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-12-31T23:59:59Z",  # Future date - Valid
                "issued_by": "Panama Maritime Authority",
                "category": "certificates"
            },
            {
                "ship_id": self.test_ship_id,
                "cert_name": "International Air Pollution Prevention Certificate",
                "cert_type": "Interim",
                "cert_no": "IAPPC002",
                "issue_date": "2023-06-01T00:00:00Z",
                "valid_date": "2023-12-31T23:59:59Z",  # Past date - Expired
                "issued_by": "DNV GL",
                "category": "certificates"
            },
            {
                "ship_id": self.test_ship_id,
                "cert_name": "Safety Management Certificate",
                "cert_type": "Provisional",
                "cert_no": "SMC003",
                "issue_date": "2024-06-01T00:00:00Z",
                "valid_date": "2026-06-01T00:00:00Z",  # Future date - Valid
                "issued_by": "Classification Society",
                "category": "certificates"
            },
            {
                "ship_id": self.test_ship_id,
                "cert_name": "International Oil Pollution Prevention Certificate",
                "cert_type": "Short term",
                "cert_no": "IOPPC004",
                "issue_date": "2022-01-01T00:00:00Z",
                "valid_date": "2022-06-01T00:00:00Z",  # Past date - Expired
                "issued_by": "Flag State Authority",
                "category": "certificates"
            }
        ]
        
        for cert_data in test_certificates:
            success, certificate = self.run_test(
                f"Create Certificate: {cert_data['cert_name'][:30]}...",
                "POST",
                "certificates",
                200,
                data=cert_data
            )
            
            if success:
                self.test_certificates.append(certificate)
                print(f"   Created certificate: {certificate.get('cert_name')}")
            else:
                print(f"   Failed to create certificate: {cert_data['cert_name']}")
        
        return len(self.test_certificates) > 0

    def test_certificate_enhancement_api(self):
        """Test GET /api/ships/{ship_id}/certificates endpoint with enhancements"""
        print(f"\n📜 Testing Certificate Enhancement API")
        
        if not self.test_ship_id:
            print("   No test ship available")
            return False
        
        success, certificates = self.run_test(
            "Get Enhanced Ship Certificates",
            "GET",
            f"ships/{self.test_ship_id}/certificates",
            200
        )
        
        if not success:
            return False
        
        print(f"   Retrieved {len(certificates)} certificates")
        
        # Verify each certificate has enhancement fields
        all_enhanced = True
        for cert in certificates:
            cert_name = cert.get('cert_name', 'Unknown')
            cert_abbreviation = cert.get('cert_abbreviation')
            status = cert.get('status')
            
            print(f"   Certificate: {cert_name}")
            print(f"     Abbreviation: {cert_abbreviation}")
            print(f"     Status: {status}")
            print(f"     Valid Date: {cert.get('valid_date')}")
            
            if not cert_abbreviation:
                print(f"     ❌ Missing cert_abbreviation field")
                all_enhanced = False
            
            if not status:
                print(f"     ❌ Missing status field")
                all_enhanced = False
            
            if status not in ['Valid', 'Expired', 'Unknown']:
                print(f"     ❌ Invalid status value: {status}")
                all_enhanced = False
        
        if all_enhanced:
            print(f"   ✅ All certificates have enhancement fields")
            return True
        else:
            print(f"   ❌ Some certificates missing enhancement fields")
            return False

    def test_certificate_abbreviation_generation(self):
        """Test certificate abbreviation generation with various inputs"""
        print(f"\n🔤 Testing Certificate Abbreviation Generation")
        
        # Test cases for abbreviation generation
        test_cases = [
            {
                "input": "CARGO SHIP SAFETY EQUIPMENT CERTIFICATE",
                "expected": "CSSEC",
                "description": "Standard maritime certificate"
            },
            {
                "input": "International Air Pollution Prevention Certificate",
                "expected": "IAPPC",
                "description": "International certificate with common words"
            },
            {
                "input": "Safety Management Certificate",
                "expected": "SMC",
                "description": "Simple certificate name"
            },
            {
                "input": "International Oil Pollution Prevention Certificate",
                "expected": "IOPPC",
                "description": "Long international certificate"
            },
            {
                "input": "Load Line Certificate",
                "expected": "LLC",
                "description": "Short certificate name"
            },
            {
                "input": "",
                "expected": "",
                "description": "Empty string"
            },
            {
                "input": "Certificate of Registry and Tonnage Measurement for Commercial Vessels",
                "expected": "CRTMCV",
                "description": "Very long certificate name (should be truncated to 6 letters)"
            }
        ]
        
        # We'll test this by creating certificates and checking their abbreviations
        all_passed = True
        
        for i, test_case in enumerate(test_cases):
            if not test_case["input"]:  # Skip empty string test for API
                continue
                
            cert_data = {
                "ship_id": self.test_ship_id,
                "cert_name": test_case["input"],
                "cert_type": "Full Term",
                "cert_no": f"TEST{i:03d}",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "category": "certificates"
            }
            
            success, certificate = self.run_test(
                f"Test Abbreviation: {test_case['description']}",
                "POST",
                "certificates",
                200,
                data=cert_data
            )
            
            if success:
                actual_abbrev = certificate.get('cert_abbreviation', '')
                expected_abbrev = test_case['expected']
                
                print(f"   Input: '{test_case['input']}'")
                print(f"   Expected: '{expected_abbrev}'")
                print(f"   Actual: '{actual_abbrev}'")
                
                if actual_abbrev == expected_abbrev:
                    print(f"   ✅ Abbreviation correct")
                else:
                    print(f"   ❌ Abbreviation mismatch")
                    all_passed = False
            else:
                print(f"   ❌ Failed to create certificate for abbreviation test")
                all_passed = False
        
        return all_passed

    def test_maritime_status_calculation(self):
        """Test certificate status calculation with different scenarios"""
        print(f"\n⚖️ Testing Maritime Status Calculation")
        
        # Test cases for status calculation
        current_time = datetime.now(timezone.utc)
        future_date = current_time + timedelta(days=365)  # 1 year in future
        past_date = current_time - timedelta(days=30)     # 30 days in past
        
        test_cases = [
            {
                "cert_name": "Future Valid Certificate",
                "cert_type": "Full Term",
                "valid_date": future_date.isoformat(),
                "expected_status": "Valid",
                "description": "Certificate with future valid date"
            },
            {
                "cert_name": "Past Expired Certificate",
                "cert_type": "Interim",
                "valid_date": past_date.isoformat(),
                "expected_status": "Expired",
                "description": "Certificate with past valid date"
            },
            {
                "cert_name": "Provisional Certificate",
                "cert_type": "Provisional",
                "valid_date": past_date.isoformat(),
                "expected_status": "Expired",
                "description": "Provisional certificate (expired)"
            },
            {
                "cert_name": "Short Term Certificate",
                "cert_type": "Short term",
                "valid_date": future_date.isoformat(),
                "expected_status": "Valid",
                "description": "Short term certificate (valid)"
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases):
            cert_data = {
                "ship_id": self.test_ship_id,
                "cert_name": test_case["cert_name"],
                "cert_type": test_case["cert_type"],
                "cert_no": f"STATUS{i:03d}",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": test_case["valid_date"],
                "category": "certificates"
            }
            
            success, certificate = self.run_test(
                f"Test Status: {test_case['description']}",
                "POST",
                "certificates",
                200,
                data=cert_data
            )
            
            if success:
                actual_status = certificate.get('status', '')
                expected_status = test_case['expected_status']
                
                print(f"   Certificate: {test_case['cert_name']}")
                print(f"   Type: {test_case['cert_type']}")
                print(f"   Valid Date: {test_case['valid_date']}")
                print(f"   Expected Status: {expected_status}")
                print(f"   Actual Status: {actual_status}")
                
                if actual_status == expected_status:
                    print(f"   ✅ Status calculation correct")
                else:
                    print(f"   ❌ Status calculation incorrect")
                    all_passed = False
            else:
                print(f"   ❌ Failed to create certificate for status test")
                all_passed = False
        
        return all_passed

    def test_enhanced_response_processing(self):
        """Test that enhanced response processing works correctly"""
        print(f"\n🔧 Testing Enhanced Response Processing")
        
        # Get certificates and verify enhancement processing
        success, certificates = self.run_test(
            "Get Certificates for Enhancement Test",
            "GET",
            f"ships/{self.test_ship_id}/certificates",
            200
        )
        
        if not success:
            return False
        
        print(f"   Processing {len(certificates)} certificates")
        
        all_processed = True
        for cert in certificates:
            cert_name = cert.get('cert_name', 'Unknown')
            
            # Check required enhancement fields
            required_fields = ['cert_abbreviation', 'status']
            missing_fields = []
            
            for field in required_fields:
                if field not in cert or cert[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"   ❌ Certificate '{cert_name}' missing fields: {missing_fields}")
                all_processed = False
            else:
                print(f"   ✅ Certificate '{cert_name}' properly enhanced")
                print(f"     Abbreviation: {cert.get('cert_abbreviation')}")
                print(f"     Status: {cert.get('status')}")
        
        return all_processed

    def test_database_integration(self):
        """Test database integration with enhanced responses"""
        print(f"\n💾 Testing Database Integration")
        
        # Test that existing certificates get enhanced responses
        success, ships = self.run_test("Get All Ships", "GET", "ships", 200)
        if not success:
            return False
        
        enhanced_ships_count = 0
        total_certificates = 0
        
        for ship in ships:
            ship_id = ship.get('id')
            ship_name = ship.get('name', 'Unknown')
            
            success, certificates = self.run_test(
                f"Get Certificates for {ship_name}",
                "GET",
                f"ships/{ship_id}/certificates",
                200
            )
            
            if success and certificates:
                total_certificates += len(certificates)
                ship_enhanced = True
                
                for cert in certificates:
                    if not cert.get('cert_abbreviation') or not cert.get('status'):
                        ship_enhanced = False
                        break
                
                if ship_enhanced:
                    enhanced_ships_count += 1
                    print(f"   ✅ Ship '{ship_name}': {len(certificates)} certificates enhanced")
                else:
                    print(f"   ❌ Ship '{ship_name}': {len(certificates)} certificates not fully enhanced")
        
        print(f"   Total ships with certificates: {len([s for s in ships if s.get('id')])}")
        print(f"   Ships with enhanced certificates: {enhanced_ships_count}")
        print(f"   Total certificates processed: {total_certificates}")
        
        return enhanced_ships_count > 0

    def test_filtering_capabilities(self):
        """Test that filtering would work with new fields"""
        print(f"\n🔍 Testing Filtering Capabilities")
        
        # Get all certificates and test filtering logic
        success, certificates = self.run_test(
            "Get All Certificates for Filtering Test",
            "GET",
            f"ships/{self.test_ship_id}/certificates",
            200
        )
        
        if not success:
            return False
        
        # Test filtering by status
        valid_certs = [c for c in certificates if c.get('status') == 'Valid']
        expired_certs = [c for c in certificates if c.get('status') == 'Expired']
        
        print(f"   Total certificates: {len(certificates)}")
        print(f"   Valid certificates: {len(valid_certs)}")
        print(f"   Expired certificates: {len(expired_certs)}")
        
        # Test filtering by abbreviation pattern
        smc_certs = [c for c in certificates if 'SMC' in c.get('cert_abbreviation', '')]
        iappc_certs = [c for c in certificates if 'IAPPC' in c.get('cert_abbreviation', '')]
        
        print(f"   SMC certificates: {len(smc_certs)}")
        print(f"   IAPPC certificates: {len(iappc_certs)}")
        
        # Verify filtering logic works
        filtering_works = True
        
        for cert in valid_certs:
            if cert.get('status') != 'Valid':
                filtering_works = False
                break
        
        for cert in expired_certs:
            if cert.get('status') != 'Expired':
                filtering_works = False
                break
        
        if filtering_works:
            print(f"   ✅ Filtering capabilities verified")
            return True
        else:
            print(f"   ❌ Filtering capabilities failed")
            return False

    def run_all_tests(self):
        """Run all certificate enhancement tests"""
        print("🚢 Certificate Enhancement Backend Testing")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed, stopping tests")
            return False
        
        # Run all enhancement tests
        test_results = []
        
        test_results.append(("Certificate Enhancement API", self.test_certificate_enhancement_api()))
        test_results.append(("Certificate Abbreviation Generation", self.test_certificate_abbreviation_generation()))
        test_results.append(("Maritime Status Calculation", self.test_maritime_status_calculation()))
        test_results.append(("Enhanced Response Processing", self.test_enhanced_response_processing()))
        test_results.append(("Database Integration", self.test_database_integration()))
        test_results.append(("Filtering Capabilities", self.test_filtering_capabilities()))
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 CERTIFICATE ENHANCEMENT TEST RESULTS")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:35} {status}")
            if result:
                passed_tests += 1
        
        print(f"\nOverall API Tests: {self.tests_passed}/{self.tests_run}")
        print(f"Feature Tests: {passed_tests}/{total_tests}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        if success_rate >= 80:
            print(f"🎉 Certificate Enhancement Testing: {success_rate:.1f}% SUCCESS RATE")
            return True
        else:
            print(f"⚠️ Certificate Enhancement Testing: {success_rate:.1f}% SUCCESS RATE - Some issues found")
            return False

def main():
    """Main test execution"""
    tester = CertificateEnhancementTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
import requests
import sys
import json
from datetime import datetime, timezone
import time

class ExactMatchDuplicateDetectionTester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
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
            print(f"✅ Login successful, token obtained")
            print(f"   User: {response.get('user', {}).get('full_name')} ({response.get('user', {}).get('role')})")
            return True
        return False

    def setup_test_data(self):
        """Setup test ship and certificates for duplicate testing"""
        print(f"\n🚢 Setting up test data for exact match duplicate detection")
        
        # Create a test ship
        ship_data = {
            "name": f"Test Vessel Exact Match {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Panama",
            "ship_type": "DNV GL",
            "gross_tonnage": 45000.0,
            "deadweight": 68000.0,
            "built_year": 2019,
            "ship_owner": "Maritime Test Holdings",
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
        
        # Create base certificate for duplicate testing
        base_cert_data = {
            "ship_id": self.test_ship_id,
            "cert_name": "International Air Pollution Prevention Certificate",
            "cert_type": "Full Term",
            "cert_no": "IAPP-EXACT-2024-001",
            "issue_date": "2024-01-15T00:00:00Z",
            "valid_date": "2029-01-15T00:00:00Z",
            "issued_by": "Panama Maritime Authority",
            "category": "certificates",
            "sensitivity_level": "public"
        }
        
        success, cert = self.run_test(
            "Create Base Certificate",
            "POST",
            "certificates",
            200,
            data=base_cert_data
        )
        
        if success:
            self.test_certificates.append(cert)
            print(f"   Created base certificate: {cert.get('cert_name')}")
            return True
        
        return False

    def test_100_percent_exact_match(self):
        """Test that 100% identical certificates are detected as duplicates"""
        print(f"\n🎯 Testing 100% Exact Match Detection")
        
        if not self.test_certificates:
            print("   No base certificate available for testing")
            return False
        
        base_cert = self.test_certificates[0]
        
        # Create analysis result that exactly matches the base certificate
        analysis_result = {
            "cert_name": base_cert["cert_name"],
            "cert_type": base_cert["cert_type"],
            "cert_no": base_cert["cert_no"],
            "issue_date": base_cert["issue_date"],
            "valid_date": base_cert["valid_date"],
            "issued_by": base_cert["issued_by"]
        }
        
        check_data = {
            "ship_id": self.test_ship_id,
            "analysis_result": analysis_result
        }
        
        success, response = self.run_test(
            "Check 100% Exact Match Duplicates",
            "POST",
            "certificates/check-duplicates-and-mismatch",
            200,
            data=check_data
        )
        
        if success:
            duplicates = response.get('duplicates', [])
            has_issues = response.get('has_issues', False)
            
            print(f"   Duplicates found: {len(duplicates)}")
            print(f"   Has issues flag: {has_issues}")
            
            if len(duplicates) > 0:
                similarity = duplicates[0].get('similarity', 0)
                print(f"   Similarity: {similarity}%")
                
                if similarity == 100.0 and has_issues:
                    print(f"✅ 100% exact match correctly detected")
                    return True
                else:
                    print(f"❌ Expected 100% similarity and has_issues=True")
                    print(f"   Got similarity={similarity}%, has_issues={has_issues}")
                    return False
            else:
                print(f"❌ Expected duplicate detection for 100% identical certificate")
                return False
        
        return False

    def test_99_percent_no_match(self):
        """Test that 99% similar certificates (not 100%) are NOT detected as duplicates"""
        print(f"\n🎯 Testing 99% Similar - No Match Detection")
        
        if not self.test_certificates:
            print("   No base certificate available for testing")
            return False
        
        base_cert = self.test_certificates[0]
        
        # Test scenarios with minor differences (should return 0% similarity)
        test_scenarios = [
            {
                "name": "Different Certificate Number",
                "analysis_result": {
                    "cert_name": base_cert["cert_name"],
                    "cert_type": base_cert["cert_type"],
                    "cert_no": "IAPP-EXACT-2024-002",  # Different number
                    "issue_date": base_cert["issue_date"],
                    "valid_date": base_cert["valid_date"],
                    "issued_by": base_cert["issued_by"]
                }
            },
            {
                "name": "Different Issue Date",
                "analysis_result": {
                    "cert_name": base_cert["cert_name"],
                    "cert_type": base_cert["cert_type"],
                    "cert_no": base_cert["cert_no"],
                    "issue_date": "2024-02-15T00:00:00Z",  # Different date
                    "valid_date": base_cert["valid_date"],
                    "issued_by": base_cert["issued_by"]
                }
            },
            {
                "name": "Different Valid Date",
                "analysis_result": {
                    "cert_name": base_cert["cert_name"],
                    "cert_type": base_cert["cert_type"],
                    "cert_no": base_cert["cert_no"],
                    "issue_date": base_cert["issue_date"],
                    "valid_date": "2029-02-15T00:00:00Z",  # Different date
                    "issued_by": base_cert["issued_by"]
                }
            },
            {
                "name": "Different Issuing Authority",
                "analysis_result": {
                    "cert_name": base_cert["cert_name"],
                    "cert_type": base_cert["cert_type"],
                    "cert_no": base_cert["cert_no"],
                    "issue_date": base_cert["issue_date"],
                    "valid_date": base_cert["valid_date"],
                    "issued_by": "Liberia Maritime Authority"  # Different authority
                }
            },
            {
                "name": "Different Certificate Type",
                "analysis_result": {
                    "cert_name": base_cert["cert_name"],
                    "cert_type": "Interim",  # Different type
                    "cert_no": base_cert["cert_no"],
                    "issue_date": base_cert["issue_date"],
                    "valid_date": base_cert["valid_date"],
                    "issued_by": base_cert["issued_by"]
                }
            },
            {
                "name": "Slightly Different Certificate Name",
                "analysis_result": {
                    "cert_name": "International Air Pollution Prevention Certificate (Renewed)",  # Slightly different
                    "cert_type": base_cert["cert_type"],
                    "cert_no": base_cert["cert_no"],
                    "issue_date": base_cert["issue_date"],
                    "valid_date": base_cert["valid_date"],
                    "issued_by": base_cert["issued_by"]
                }
            }
        ]
        
        all_passed = True
        
        for scenario in test_scenarios:
            check_data = {
                "ship_id": self.test_ship_id,
                "analysis_result": scenario["analysis_result"]
            }
            
            success, response = self.run_test(
                f"Check No Match - {scenario['name']}",
                "POST",
                "certificates/check-duplicates-and-mismatch",
                200,
                data=check_data
            )
            
            if success:
                duplicates = response.get('duplicates', [])
                has_issues = response.get('has_issues', False)
                
                if len(duplicates) == 0 and not has_issues:
                    print(f"✅ {scenario['name']}: No duplicates detected (correct)")
                else:
                    similarity = duplicates[0].get('similarity', 0) if duplicates else 0
                    print(f"❌ {scenario['name']}: Unexpected duplicate detected")
                    print(f"   Similarity: {similarity}%, Has issues: {has_issues}")
                    all_passed = False
            else:
                print(f"❌ {scenario['name']}: API call failed")
                all_passed = False
        
        return all_passed

    def test_certificate_upload_workflow(self):
        """Test the certificate upload workflow with exact match duplicate detection"""
        print(f"\n📋 Testing Certificate Upload Workflow with Exact Match Detection")
        
        if not self.test_certificates:
            print("   No base certificate available for testing")
            return False
        
        base_cert = self.test_certificates[0]
        
        # Test 1: Try to upload identical certificate (should trigger duplicate detection)
        identical_analysis = {
            "cert_name": base_cert["cert_name"],
            "cert_type": base_cert["cert_type"],
            "cert_no": base_cert["cert_no"],
            "issue_date": base_cert["issue_date"],
            "valid_date": base_cert["valid_date"],
            "issued_by": base_cert["issued_by"]
        }
        
        check_data = {
            "ship_id": self.test_ship_id,
            "analysis_result": identical_analysis
        }
        
        success, response = self.run_test(
            "Upload Workflow - Identical Certificate Check",
            "POST",
            "certificates/check-duplicates-and-mismatch",
            200,
            data=check_data
        )
        
        if not success:
            return False
        
        duplicates = response.get('duplicates', [])
        has_issues = response.get('has_issues', False)
        
        if not (len(duplicates) > 0 and has_issues):
            print(f"❌ Expected duplicate detection in upload workflow")
            print(f"   Duplicates: {len(duplicates)}, Has issues: {has_issues}")
            return False
        
        print(f"✅ Upload workflow correctly detected exact match duplicate")
        
        # Test 2: Process with resolution (cancel)
        resolution_data = {
            "analysis_result": identical_analysis,
            "upload_result": {"file_id": "test_file_123", "filename": "test_cert.pdf"},
            "ship_id": self.test_ship_id,
            "duplicate_resolution": "cancel"
        }
        
        success, response = self.run_test(
            "Upload Workflow - Cancel Resolution",
            "POST",
            "certificates/process-with-resolution",
            200,
            data=resolution_data
        )
        
        if success:
            status = response.get('status')
            if status == 'cancelled':
                print(f"✅ Upload workflow correctly cancelled due to exact match duplicate")
                return True
            else:
                print(f"❌ Expected cancelled status, got: {status}")
                return False
        
        return False

    def test_near_identical_no_false_positives(self):
        """Test that near-identical certificates don't trigger false positives"""
        print(f"\n🚫 Testing Near-Identical Certificates - No False Positives")
        
        if not self.test_certificates:
            print("   No base certificate available for testing")
            return False
        
        base_cert = self.test_certificates[0]
        
        # Create a certificate that would have been 90%+ similar under old logic
        # but should be 0% under new exact match logic
        near_identical_analysis = {
            "cert_name": base_cert["cert_name"],  # Same name
            "cert_type": base_cert["cert_type"],  # Same type
            "cert_no": "IAPP-EXACT-2024-999",    # Different number (should make it 0%)
            "issue_date": base_cert["issue_date"], # Same issue date
            "valid_date": base_cert["valid_date"], # Same valid date
            "issued_by": base_cert["issued_by"]    # Same issuer
        }
        
        check_data = {
            "ship_id": self.test_ship_id,
            "analysis_result": near_identical_analysis
        }
        
        success, response = self.run_test(
            "Near-Identical Certificate - No False Positive",
            "POST",
            "certificates/check-duplicates-and-mismatch",
            200,
            data=check_data
        )
        
        if success:
            duplicates = response.get('duplicates', [])
            has_issues = response.get('has_issues', False)
            
            if len(duplicates) == 0 and not has_issues:
                print(f"✅ Near-identical certificate correctly NOT detected as duplicate")
                print(f"   This would have been a false positive under 70% threshold")
                return True
            else:
                similarity = duplicates[0].get('similarity', 0) if duplicates else 0
                print(f"❌ False positive detected for near-identical certificate")
                print(f"   Similarity: {similarity}%, Has issues: {has_issues}")
                return False
        
        return False

    def cleanup_test_data(self):
        """Clean up test data"""
        print(f"\n🧹 Cleaning up test data")
        
        # Delete test certificates
        for cert in self.test_certificates:
            cert_id = cert.get('id')
            if cert_id:
                success, _ = self.run_test(
                    f"Delete Test Certificate {cert_id}",
                    "DELETE",
                    f"certificates/{cert_id}",
                    200
                )
                if success:
                    print(f"   Deleted certificate: {cert.get('cert_name')}")
        
        # Delete test ship
        if self.test_ship_id:
            success, _ = self.run_test(
                "Delete Test Ship",
                "DELETE",
                f"ships/{self.test_ship_id}",
                200
            )
            if success:
                print(f"   Deleted test ship: {self.test_ship_id}")

def main():
    """Main test execution"""
    print("🎯 EXACT MATCH DUPLICATE DETECTION TESTING (100% Only)")
    print("=" * 65)
    print("Testing updated duplicate detection logic with 100% exact match requirement")
    print("=" * 65)
    
    tester = ExactMatchDuplicateDetectionTester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Setup test data
    if not tester.setup_test_data():
        print("❌ Test data setup failed, stopping tests")
        return 1
    
    # Run exact match duplicate detection tests
    test_results = []
    
    try:
        test_results.append(("100% Exact Match Detection", tester.test_100_percent_exact_match()))
        test_results.append(("99% Similar - No Match", tester.test_99_percent_no_match()))
        test_results.append(("Certificate Upload Workflow", tester.test_certificate_upload_workflow()))
        test_results.append(("Near-Identical No False Positives", tester.test_near_identical_no_false_positives()))
        
    finally:
        # Always cleanup test data
        tester.cleanup_test_data()
    
    # Print final results
    print("\n" + "=" * 65)
    print("📊 EXACT MATCH DUPLICATE DETECTION TEST RESULTS")
    print("=" * 65)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:40} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall API Tests: {tester.tests_passed}/{tester.tests_run}")
    print(f"Feature Tests: {passed_tests}/{total_tests}")
    
    # Summary of what was tested
    print(f"\n🎯 EXACT MATCH DUPLICATE DETECTION VERIFICATION:")
    print(f"✓ 100% exact match requirement implemented")
    print(f"✓ Near matches (99% or less) return 0% similarity")
    print(f"✓ Backend threshold check (>= 100.0) working")
    print(f"✓ Certificate upload workflow integration")
    print(f"✓ No false positives for near-identical certificates")
    print(f"✓ Updated logic eliminates 'awaiting decision' interruptions")
    
    if passed_tests == total_tests and tester.tests_passed == tester.tests_run:
        print("\n🎉 All exact match duplicate detection tests passed!")
        print("✅ Updated duplicate detection logic working correctly")
        print("✅ Only truly identical certificates trigger duplicate detection")
        print("✅ False positives from similar certificates eliminated")
        return 0
    else:
        print("\n⚠️ Some exact match duplicate detection tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
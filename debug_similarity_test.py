import requests
import sys
import json
from datetime import datetime, timezone
import time

class SimilarityDebugTester:
    def __init__(self, base_url="https://continue-session.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
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
            return True
        return False

    def debug_similarity_calculation(self):
        """Debug the similarity calculation with real data"""
        print(f"\n🔍 Debugging Similarity Calculation")
        
        # Get existing certificates to work with
        success, certificates = self.run_test("Get All Certificates", "GET", "certificates", 200)
        if not success or not certificates:
            print("   No certificates available for debugging")
            return False
        
        # Find a certificate to test with
        test_cert = certificates[0]
        ship_id = test_cert.get('ship_id')
        
        print(f"\n📋 Using certificate for debugging:")
        print(f"   Name: {test_cert.get('cert_name')}")
        print(f"   Number: {test_cert.get('cert_no')}")
        print(f"   Type: {test_cert.get('cert_type')}")
        print(f"   Issue Date: {test_cert.get('issue_date')}")
        print(f"   Valid Date: {test_cert.get('valid_date')}")
        print(f"   Issued By: {test_cert.get('issued_by')}")
        print(f"   Ship ID: {ship_id}")
        
        # Test 1: Exact match with same data
        print(f"\n🎯 Test 1: Exact Match with Same Data")
        exact_match_analysis = {
            "cert_name": test_cert.get('cert_name'),
            "cert_type": test_cert.get('cert_type'),
            "cert_no": test_cert.get('cert_no'),
            "issue_date": test_cert.get('issue_date'),
            "valid_date": test_cert.get('valid_date'),
            "issued_by": test_cert.get('issued_by')
        }
        
        print(f"   Analysis data being sent:")
        for key, value in exact_match_analysis.items():
            print(f"     {key}: {repr(value)}")
        
        check_data = {
            "ship_id": ship_id,
            "analysis_result": exact_match_analysis
        }
        
        success, response = self.run_test(
            "Debug Exact Match",
            "POST",
            "certificates/check-duplicates-and-mismatch",
            200,
            data=check_data
        )
        
        if success:
            duplicates = response.get('duplicates', [])
            has_issues = response.get('has_issues', False)
            
            print(f"   Response:")
            print(f"     Duplicates found: {len(duplicates)}")
            print(f"     Has issues: {has_issues}")
            
            if duplicates:
                for i, dup in enumerate(duplicates):
                    similarity = dup.get('similarity', 0)
                    cert = dup.get('certificate', {})
                    print(f"     Duplicate {i+1}: {similarity}% similarity")
                    print(f"       Certificate ID: {cert.get('id')}")
                    print(f"       Certificate Name: {cert.get('cert_name')}")
                    print(f"       Certificate Number: {cert.get('cert_no')}")
            else:
                print(f"   ❌ No duplicates found for exact match!")
        
        # Test 2: Different certificate number
        print(f"\n🎯 Test 2: Different Certificate Number")
        different_number_analysis = exact_match_analysis.copy()
        different_number_analysis['cert_no'] = 'DIFFERENT-NUMBER-123'
        
        check_data = {
            "ship_id": ship_id,
            "analysis_result": different_number_analysis
        }
        
        success, response = self.run_test(
            "Debug Different Number",
            "POST",
            "certificates/check-duplicates-and-mismatch",
            200,
            data=check_data
        )
        
        if success:
            duplicates = response.get('duplicates', [])
            print(f"   Different number test: {len(duplicates)} duplicates (should be 0)")
            if duplicates:
                similarity = duplicates[0].get('similarity', 0)
                print(f"     Unexpected similarity: {similarity}%")
        
        # Test 3: Check date format issues
        print(f"\n🎯 Test 3: Date Format Testing")
        
        # Try different date formats
        date_formats = [
            test_cert.get('issue_date'),  # Original format
            "2024-01-15T00:00:00Z",       # ISO format with Z
            "2024-01-15T00:00:00+00:00",  # ISO format with timezone
            "2024-01-15",                 # Date only
        ]
        
        for i, date_format in enumerate(date_formats):
            if date_format is None:
                continue
                
            print(f"   Testing date format {i+1}: {repr(date_format)}")
            
            date_test_analysis = exact_match_analysis.copy()
            date_test_analysis['issue_date'] = date_format
            
            check_data = {
                "ship_id": ship_id,
                "analysis_result": date_test_analysis
            }
            
            success, response = self.run_test(
                f"Debug Date Format {i+1}",
                "POST",
                "certificates/check-duplicates-and-mismatch",
                200,
                data=check_data
            )
            
            if success:
                duplicates = response.get('duplicates', [])
                if duplicates:
                    similarity = duplicates[0].get('similarity', 0)
                    print(f"     Date format {i+1}: {similarity}% similarity")
                else:
                    print(f"     Date format {i+1}: No match")
        
        return True

def main():
    """Main test execution"""
    print("🔍 SIMILARITY CALCULATION DEBUG")
    print("=" * 50)
    
    tester = SimilarityDebugTester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Debug similarity calculation
    if not tester.debug_similarity_calculation():
        print("❌ Similarity debugging failed")
        return 1
    
    print("\n✅ Similarity debugging completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
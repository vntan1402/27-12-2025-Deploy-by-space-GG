import requests
import sys
import json
from datetime import datetime, timezone, timedelta
import time

class CertificateDuplicateDetectionTester:
    def __init__(self, base_url="https://ship-cert-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.test_ship_id = None

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
            user_info = response.get('user', {})
            print(f"✅ Login successful, token obtained")
            print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
            print(f"   Company: {user_info.get('company', 'None')}")
            return True
        return False

    def get_existing_certificates(self):
        """Get all existing certificates in database"""
        print(f"\n📋 CHECKING EXISTING CERTIFICATES IN DATABASE")
        print("=" * 60)
        
        # Get all certificates
        success, certificates = self.run_test("Get All Certificates", "GET", "certificates", 200)
        if not success:
            return []
        
        print(f"📊 Found {len(certificates)} total certificates in database")
        
        # Group by ship
        ships_with_certs = {}
        for cert in certificates:
            ship_id = cert.get('ship_id')
            if ship_id not in ships_with_certs:
                ships_with_certs[ship_id] = []
            ships_with_certs[ship_id].append(cert)
        
        print(f"🚢 Certificates distributed across {len(ships_with_certs)} ships")
        
        # Get ship details for better reporting
        success, ships = self.run_test("Get Ships", "GET", "ships", 200)
        ship_names = {}
        if success:
            for ship in ships:
                ship_names[ship['id']] = ship['name']
        
        # Show detailed breakdown
        for ship_id, certs in ships_with_certs.items():
            ship_name = ship_names.get(ship_id, f"Unknown Ship ({ship_id[:8]}...)")
            print(f"\n🚢 {ship_name} ({len(certs)} certificates):")
            
            for i, cert in enumerate(certs[:5], 1):  # Show first 5 certificates
                print(f"   {i}. {cert.get('cert_name', 'Unknown')} - {cert.get('cert_no', 'No Number')}")
                print(f"      Type: {cert.get('cert_type', 'Unknown')} | Issued by: {cert.get('issued_by', 'Unknown')}")
                print(f"      Issue: {cert.get('issue_date', 'Unknown')[:10]} | Valid: {cert.get('valid_date', 'Unknown')[:10]}")
            
            if len(certs) > 5:
                print(f"   ... and {len(certs) - 5} more certificates")
        
        return certificates

    def analyze_similarity_patterns(self, certificates):
        """Analyze existing certificates for potential similarity patterns"""
        print(f"\n🔍 ANALYZING CERTIFICATE SIMILARITY PATTERNS")
        print("=" * 60)
        
        if len(certificates) < 2:
            print("❌ Need at least 2 certificates to analyze similarity patterns")
            return
        
        # Group certificates by ship for analysis
        ships_certs = {}
        for cert in certificates:
            ship_id = cert.get('ship_id')
            if ship_id not in ships_certs:
                ships_certs[ship_id] = []
            ships_certs[ship_id].append(cert)
        
        print(f"📊 Analyzing similarity within {len(ships_certs)} ships...")
        
        for ship_id, ship_certs in ships_certs.items():
            if len(ship_certs) < 2:
                continue
                
            print(f"\n🚢 Ship {ship_id[:8]}... ({len(ship_certs)} certificates)")
            
            # Compare each certificate with others in same ship
            high_similarity_pairs = []
            
            for i, cert1 in enumerate(ship_certs):
                for j, cert2 in enumerate(ship_certs[i+1:], i+1):
                    similarity = self.calculate_similarity_score(cert1, cert2)
                    
                    if similarity >= 50.0:  # Show similarities above 50%
                        high_similarity_pairs.append((cert1, cert2, similarity))
            
            if high_similarity_pairs:
                print(f"   ⚠️ Found {len(high_similarity_pairs)} certificate pairs with >50% similarity:")
                for cert1, cert2, similarity in high_similarity_pairs:
                    print(f"   📋 {similarity:.1f}% similarity:")
                    print(f"      A: {cert1.get('cert_name', 'Unknown')} ({cert1.get('cert_no', 'No Number')})")
                    print(f"      B: {cert2.get('cert_name', 'Unknown')} ({cert2.get('cert_no', 'No Number')})")
                    
                    if similarity >= 70.0:
                        print(f"      🚨 WOULD TRIGGER DUPLICATE DETECTION (≥70%)")
            else:
                print(f"   ✅ No high similarity pairs found")

    def calculate_similarity_score(self, cert1, cert2):
        """Calculate similarity score between two certificates (mimics backend logic)"""
        comparison_fields = {
            'cert_name': 0.25,
            'cert_type': 0.15,
            'cert_no': 0.20,
            'issue_date': 0.15,
            'valid_date': 0.15,
            'issued_by': 0.10
        }
        
        total_weight = 0
        matching_weight = 0
        
        for field, weight in comparison_fields.items():
            val1 = cert1.get(field)
            val2 = cert2.get(field)
            
            # Skip if either value is None or empty
            if not val1 or not val2:
                continue
                
            total_weight += weight
            
            # Compare values based on type
            if field in ['issue_date', 'valid_date']:
                # Date comparison
                try:
                    if isinstance(val1, str):
                        val1 = datetime.fromisoformat(val1.replace('Z', '+00:00'))
                    if isinstance(val2, str):
                        val2 = datetime.fromisoformat(val2.replace('Z', '+00:00'))
                    
                    if val1 == val2:
                        matching_weight += weight
                except:
                    pass
            else:
                # String comparison - case insensitive
                if str(val1).lower().strip() == str(val2).lower().strip():
                    matching_weight += weight
                elif field == 'cert_name':
                    # Partial match for certificate names
                    similarity = self.calculate_string_similarity(str(val1), str(val2))
                    if similarity > 0.8:  # 80% string similarity
                        matching_weight += weight * similarity
        
        # Calculate percentage
        if total_weight == 0:
            return 0.0
        
        return (matching_weight / total_weight) * 100

    def calculate_string_similarity(self, str1, str2):
        """Calculate string similarity using simple character overlap"""
        try:
            str1 = str1.lower().strip()
            str2 = str2.lower().strip()
            
            if str1 == str2:
                return 1.0
            
            # Simple character-based similarity
            set1 = set(str1.replace(' ', ''))
            set2 = set(str2.replace(' ', ''))
            
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            
            if len(union) == 0:
                return 0.0
            
            return len(intersection) / len(union)
        except:
            return 0.0

    def test_duplicate_detection_api(self):
        """Test the duplicate detection API endpoint"""
        print(f"\n🔍 TESTING DUPLICATE DETECTION API")
        print("=" * 60)
        
        # Get a ship to test with
        success, ships = self.run_test("Get Ships for Testing", "GET", "ships", 200)
        if not success or not ships:
            print("❌ No ships available for testing")
            return False
        
        test_ship = ships[0]
        self.test_ship_id = test_ship['id']
        print(f"🚢 Using test ship: {test_ship['name']} (ID: {test_ship['id']})")
        
        # Get existing certificates for this ship
        success, existing_certs = self.run_test(
            "Get Ship Certificates", 
            "GET", 
            f"ships/{self.test_ship_id}/certificates", 
            200
        )
        
        if success and existing_certs:
            print(f"📋 Ship has {len(existing_certs)} existing certificates")
            
            # Test duplicate detection with a similar certificate
            test_cert = existing_certs[0]
            print(f"📋 Testing with existing certificate: {test_cert.get('cert_name')}")
            
            # Create a test analysis result that should trigger duplicate detection
            analysis_result = {
                'cert_name': test_cert.get('cert_name'),  # Same name
                'cert_type': test_cert.get('cert_type'),  # Same type
                'cert_no': f"SIMILAR_{test_cert.get('cert_no', 'TEST')}",  # Different number
                'issue_date': test_cert.get('issue_date'),  # Same issue date
                'valid_date': test_cert.get('valid_date'),  # Same valid date
                'issued_by': test_cert.get('issued_by'),  # Same issuer
                'ship_name': test_ship['name']
            }
            
            # Test the duplicate detection endpoint
            test_data = {
                'ship_id': self.test_ship_id,
                'analysis_result': analysis_result
            }
            
            success, response = self.run_test(
                "Check Duplicates and Mismatch",
                "POST",
                "certificates/check-duplicates-and-mismatch",
                200,
                data=test_data
            )
            
            if success:
                duplicates = response.get('duplicates', [])
                ship_mismatch = response.get('ship_mismatch', {})
                has_issues = response.get('has_issues', False)
                
                print(f"🔍 Duplicate Detection Results:")
                print(f"   Found {len(duplicates)} potential duplicates")
                print(f"   Ship mismatch detected: {ship_mismatch.get('mismatch', False)}")
                print(f"   Has issues: {has_issues}")
                
                if duplicates:
                    print(f"\n📋 Duplicate Details:")
                    for i, dup in enumerate(duplicates, 1):
                        similarity = dup.get('similarity', 0)
                        cert = dup.get('certificate', {})
                        print(f"   {i}. Similarity: {similarity:.1f}%")
                        print(f"      Certificate: {cert.get('cert_name')} ({cert.get('cert_no')})")
                        
                        if similarity >= 70.0:
                            print(f"      🚨 TRIGGERS DUPLICATE DETECTION (≥70%)")
                        else:
                            print(f"      ✅ Below threshold")
                
                return True
            else:
                print("❌ Duplicate detection API test failed")
                return False
        else:
            print("⚠️ No existing certificates found for duplicate testing")
            return True

    def test_threshold_sensitivity(self):
        """Test different similarity scenarios to understand threshold sensitivity"""
        print(f"\n🎯 TESTING DUPLICATE DETECTION THRESHOLD SENSITIVITY")
        print("=" * 60)
        
        if not self.test_ship_id:
            print("❌ No test ship available")
            return False
        
        # Get existing certificates
        success, existing_certs = self.run_test(
            "Get Ship Certificates for Threshold Test", 
            "GET", 
            f"ships/{self.test_ship_id}/certificates", 
            200
        )
        
        if not success or not existing_certs:
            print("⚠️ No existing certificates for threshold testing")
            return True
        
        base_cert = existing_certs[0]
        print(f"📋 Base certificate: {base_cert.get('cert_name')} ({base_cert.get('cert_no')})")
        
        # Test scenarios with different similarity levels
        test_scenarios = [
            {
                'name': 'Identical Certificate (100% match)',
                'analysis_result': {
                    'cert_name': base_cert.get('cert_name'),
                    'cert_type': base_cert.get('cert_type'),
                    'cert_no': base_cert.get('cert_no'),
                    'issue_date': base_cert.get('issue_date'),
                    'valid_date': base_cert.get('valid_date'),
                    'issued_by': base_cert.get('issued_by')
                }
            },
            {
                'name': 'Same name, different number (High similarity)',
                'analysis_result': {
                    'cert_name': base_cert.get('cert_name'),
                    'cert_type': base_cert.get('cert_type'),
                    'cert_no': f"DIFFERENT_{int(time.time())}",
                    'issue_date': base_cert.get('issue_date'),
                    'valid_date': base_cert.get('valid_date'),
                    'issued_by': base_cert.get('issued_by')
                }
            },
            {
                'name': 'Similar name, same dates (Medium similarity)',
                'analysis_result': {
                    'cert_name': f"Similar {base_cert.get('cert_name', 'Certificate')}",
                    'cert_type': base_cert.get('cert_type'),
                    'cert_no': f"DIFF_{int(time.time())}",
                    'issue_date': base_cert.get('issue_date'),
                    'valid_date': base_cert.get('valid_date'),
                    'issued_by': 'Different Authority'
                }
            },
            {
                'name': 'Different certificate (Low similarity)',
                'analysis_result': {
                    'cert_name': 'Completely Different Certificate',
                    'cert_type': 'Full Term',
                    'cert_no': f"UNIQUE_{int(time.time())}",
                    'issue_date': '2024-06-01T00:00:00Z',
                    'valid_date': '2025-06-01T00:00:00Z',
                    'issued_by': 'New Authority'
                }
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")
            
            test_data = {
                'ship_id': self.test_ship_id,
                'analysis_result': scenario['analysis_result']
            }
            
            success, response = self.run_test(
                f"Threshold Test - {scenario['name']}",
                "POST",
                "certificates/check-duplicates-and-mismatch",
                200,
                data=test_data
            )
            
            if success:
                duplicates = response.get('duplicates', [])
                has_issues = response.get('has_issues', False)
                
                if duplicates:
                    max_similarity = max(dup.get('similarity', 0) for dup in duplicates)
                    print(f"   📊 Max similarity: {max_similarity:.1f}%")
                    
                    if max_similarity >= 70.0:
                        print(f"   🚨 WOULD SHOW 'Duplicate detected - awaiting decision'")
                    else:
                        print(f"   ✅ Below 70% threshold - no duplicate warning")
                else:
                    print(f"   ✅ No duplicates detected (0% similarity)")
            else:
                print(f"   ❌ Test failed")
        
        return True

    def test_ai_extraction_patterns(self):
        """Test what AI typically extracts that might cause false positives"""
        print(f"\n🤖 ANALYZING AI EXTRACTION PATTERNS FOR FALSE POSITIVES")
        print("=" * 60)
        
        # Get existing certificates to analyze patterns
        success, certificates = self.run_test("Get All Certificates for AI Analysis", "GET", "certificates", 200)
        if not success:
            return False
        
        print(f"📊 Analyzing {len(certificates)} certificates for AI extraction patterns...")
        
        # Analyze certificate name patterns
        cert_names = [cert.get('cert_name', '') for cert in certificates if cert.get('cert_name')]
        cert_types = [cert.get('cert_type', '') for cert in certificates if cert.get('cert_type')]
        issuers = [cert.get('issued_by', '') for cert in certificates if cert.get('issued_by')]
        
        print(f"\n📋 Certificate Name Patterns:")
        name_frequency = {}
        for name in cert_names:
            name_frequency[name] = name_frequency.get(name, 0) + 1
        
        # Show most common certificate names
        common_names = sorted(name_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        for name, count in common_names:
            if count > 1:
                print(f"   '{name}': {count} occurrences")
                if count >= 3:
                    print(f"      ⚠️ HIGH RISK: Multiple certificates with same name could trigger false positives")
        
        print(f"\n📋 Certificate Type Patterns:")
        type_frequency = {}
        for cert_type in cert_types:
            type_frequency[cert_type] = type_frequency.get(cert_type, 0) + 1
        
        common_types = sorted(type_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        for cert_type, count in common_types:
            print(f"   '{cert_type}': {count} occurrences")
        
        print(f"\n📋 Issuer Patterns:")
        issuer_frequency = {}
        for issuer in issuers:
            issuer_frequency[issuer] = issuer_frequency.get(issuer, 0) + 1
        
        common_issuers = sorted(issuer_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        for issuer, count in common_issuers:
            print(f"   '{issuer}': {count} occurrences")
        
        # Check for date clustering (same issue/valid dates)
        print(f"\n📅 Date Pattern Analysis:")
        issue_dates = {}
        valid_dates = {}
        
        for cert in certificates:
            issue_date = cert.get('issue_date', '')[:10] if cert.get('issue_date') else ''
            valid_date = cert.get('valid_date', '')[:10] if cert.get('valid_date') else ''
            
            if issue_date:
                issue_dates[issue_date] = issue_dates.get(issue_date, 0) + 1
            if valid_date:
                valid_dates[valid_date] = valid_dates.get(valid_date, 0) + 1
        
        # Show dates with multiple certificates
        common_issue_dates = [(date, count) for date, count in issue_dates.items() if count > 1]
        common_valid_dates = [(date, count) for date, count in valid_dates.items() if count > 1]
        
        if common_issue_dates:
            print(f"   Issue dates with multiple certificates:")
            for date, count in sorted(common_issue_dates, key=lambda x: x[1], reverse=True)[:5]:
                print(f"     {date}: {count} certificates")
                if count >= 3:
                    print(f"       ⚠️ RISK: Same issue date could contribute to false positives")
        
        if common_valid_dates:
            print(f"   Valid dates with multiple certificates:")
            for date, count in sorted(common_valid_dates, key=lambda x: x[1], reverse=True)[:5]:
                print(f"     {date}: {count} certificates")
                if count >= 3:
                    print(f"       ⚠️ RISK: Same valid date could contribute to false positives")
        
        return True

    def generate_recommendations(self):
        """Generate recommendations based on analysis"""
        print(f"\n💡 DUPLICATE DETECTION ANALYSIS RECOMMENDATIONS")
        print("=" * 60)
        
        print(f"🎯 THRESHOLD ANALYSIS:")
        print(f"   Current threshold: 70% similarity")
        print(f"   Recommendation: Consider if 70% is too sensitive for maritime certificates")
        print(f"   - Maritime certificates often have similar names (e.g., 'Safety Management Certificate')")
        print(f"   - Same issuing authorities appear frequently")
        print(f"   - Certificate types are limited (Full Term, Interim, etc.)")
        
        print(f"\n🔧 POTENTIAL IMPROVEMENTS:")
        print(f"   1. INCREASE THRESHOLD: Consider 80-85% for maritime certificates")
        print(f"   2. WEIGHT ADJUSTMENT: Increase cert_no weight (currently 20%)")
        print(f"   3. SHIP-SPECIFIC: Ensure duplicate checking only within same ship")
        print(f"   4. DATE TOLERANCE: Add date range tolerance for renewals")
        print(f"   5. EXCLUDE GENERIC NAMES: Filter out very common certificate names")
        
        print(f"\n🚨 FALSE POSITIVE RISKS:")
        print(f"   - Certificates with same name but different numbers")
        print(f"   - Renewed certificates (same name, similar dates)")
        print(f"   - Certificates from same classification society")
        print(f"   - AI extracting generic certificate names")
        
        print(f"\n✅ VERIFICATION STEPS:")
        print(f"   1. Check if duplicate detection only compares within same ship")
        print(f"   2. Verify certificate number comparison is working correctly")
        print(f"   3. Test with real certificate uploads to see AI extraction quality")
        print(f"   4. Monitor false positive rate in production")

def main():
    """Main test execution for duplicate detection debugging"""
    print("🔍 CERTIFICATE DUPLICATE DETECTION DEBUG TESTING")
    print("=" * 70)
    
    tester = CertificateDuplicateDetectionTester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Run duplicate detection analysis
    print(f"\n🎯 STARTING COMPREHENSIVE DUPLICATE DETECTION ANALYSIS")
    print("=" * 70)
    
    try:
        # 1. Get existing certificates and analyze
        certificates = tester.get_existing_certificates()
        
        # 2. Analyze similarity patterns in existing data
        if certificates:
            tester.analyze_similarity_patterns(certificates)
        
        # 3. Test duplicate detection API
        tester.test_duplicate_detection_api()
        
        # 4. Test threshold sensitivity
        tester.test_threshold_sensitivity()
        
        # 5. Analyze AI extraction patterns
        tester.test_ai_extraction_patterns()
        
        # 6. Generate recommendations
        tester.generate_recommendations()
        
        # Print final results
        print("\n" + "=" * 70)
        print("📊 DUPLICATE DETECTION DEBUG RESULTS")
        print("=" * 70)
        
        print(f"Total API Tests: {tester.tests_passed}/{tester.tests_run}")
        
        if tester.tests_passed == tester.tests_run:
            print("✅ All API tests passed - duplicate detection logic is accessible")
        else:
            print("⚠️ Some API tests failed - check backend implementation")
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   - Duplicate detection uses 70% similarity threshold")
        print(f"   - Compares cert_name (25%), cert_no (20%), dates (30%), type (15%), issuer (10%)")
        print(f"   - Maritime certificates often have similar names and issuers")
        print(f"   - False positives likely due to generic certificate names")
        print(f"   - Recommend increasing threshold or adjusting weights")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Focused test for Add New Record functionality as requested in the review.
Tests specific ship and certificate creation with the exact data provided.
"""

import requests
import json
from datetime import datetime, timezone

class AddRecordTester:
    def __init__(self, base_url="https://ship-cert-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.created_ship_id = None
        self.created_cert_id = None

    def authenticate(self, username="admin", password="admin123"):
        """Test authentication with admin/admin123 credentials"""
        print("🔐 Step 1: Testing Authentication")
        print(f"   Logging in with {username}/{password}")
        
        url = f"{self.api_url}/auth/login"
        data = {"username": username, "password": password}
        
        try:
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                self.token = result['access_token']
                user_info = result.get('user', {})
                print(f"✅ Authentication successful")
                print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
                return True
            else:
                print(f"❌ Authentication failed - Status: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def test_create_ship(self):
        """Test POST /api/ships endpoint with specific sample data"""
        print("\n🚢 Step 2: Testing Ship Creation")
        
        # Exact data from the review request
        ship_data = {
            "name": "Test Ship",
            "imo_number": "1234567",
            "class_society": "DNV GL",
            "flag": "Vietnam",
            "gross_tonnage": 50000,
            "deadweight": 80000,
            "built_year": 2020
        }
        
        print(f"   Creating ship with data: {json.dumps(ship_data, indent=2)}")
        
        url = f"{self.api_url}/ships"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json=ship_data, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                self.created_ship_id = result.get('id')
                print(f"✅ Ship created successfully")
                print(f"   Ship ID: {self.created_ship_id}")
                print(f"   Ship Name: {result.get('name')}")
                print(f"   IMO Number: {result.get('imo_number')}")
                print(f"   Flag: {result.get('flag')}")
                return True
            else:
                print(f"❌ Ship creation failed - Status: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Ship creation error: {str(e)}")
            return False

    def test_create_certificate(self):
        """Test POST /api/certificates endpoint with specific sample data"""
        print("\n📜 Step 3: Testing Certificate Creation")
        
        if not self.created_ship_id:
            # Get any existing ship for testing
            print("   No ship created in this session, getting existing ship...")
            try:
                url = f"{self.api_url}/ships"
                headers = {'Authorization': f'Bearer {self.token}'}
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    ships = response.json()
                    if ships:
                        self.created_ship_id = ships[0]['id']
                        print(f"   Using existing ship ID: {self.created_ship_id}")
                    else:
                        print("❌ No ships available for certificate testing")
                        return False
                else:
                    print("❌ Failed to get ships list")
                    return False
            except Exception as e:
                print(f"❌ Error getting ships: {str(e)}")
                return False
        
        # Exact data from the review request
        cert_data = {
            "ship_id": self.created_ship_id,
            "cert_name": "Safety Certificate",
            "cert_no": "SC123456",
            "issue_date": "2024-01-01T00:00:00Z",
            "valid_date": "2025-01-01T00:00:00Z",
            "category": "certificates",
            "sensitivity_level": "internal"
        }
        
        print(f"   Creating certificate with data: {json.dumps(cert_data, indent=2)}")
        
        url = f"{self.api_url}/certificates"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json=cert_data, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                self.created_cert_id = result.get('id')
                print(f"✅ Certificate created successfully")
                print(f"   Certificate ID: {self.created_cert_id}")
                print(f"   Certificate Name: {result.get('cert_name')}")
                print(f"   Certificate No: {result.get('cert_no')}")
                print(f"   Ship ID: {result.get('ship_id')}")
                print(f"   Valid Until: {result.get('valid_date')}")
                return True
            else:
                print(f"❌ Certificate creation failed - Status: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Certificate creation error: {str(e)}")
            return False

    def test_retrieve_records(self):
        """Test that newly created records can be retrieved via GET endpoints"""
        print("\n🔍 Step 4: Testing Record Retrieval")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        success = True
        
        # Test retrieving ships
        print("   Testing GET /api/ships...")
        try:
            url = f"{self.api_url}/ships"
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                ships = response.json()
                print(f"✅ Retrieved {len(ships)} ships")
                
                # Check if our created ship is in the list
                if self.created_ship_id:
                    found_ship = next((ship for ship in ships if ship['id'] == self.created_ship_id), None)
                    if found_ship:
                        print(f"   ✅ Created ship found in list: {found_ship['name']}")
                    else:
                        print(f"   ❌ Created ship not found in list")
                        success = False
            else:
                print(f"❌ Failed to retrieve ships - Status: {response.status_code}")
                success = False
        except Exception as e:
            print(f"❌ Error retrieving ships: {str(e)}")
            success = False
        
        # Test retrieving specific ship
        if self.created_ship_id:
            print(f"   Testing GET /api/ships/{self.created_ship_id}...")
            try:
                url = f"{self.api_url}/ships/{self.created_ship_id}"
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    ship = response.json()
                    print(f"✅ Retrieved specific ship: {ship['name']}")
                    print(f"   IMO: {ship['imo_number']}, Flag: {ship['flag']}")
                else:
                    print(f"❌ Failed to retrieve specific ship - Status: {response.status_code}")
                    success = False
            except Exception as e:
                print(f"❌ Error retrieving specific ship: {str(e)}")
                success = False
        
        # Test retrieving ship certificates
        if self.created_ship_id:
            print(f"   Testing GET /api/ships/{self.created_ship_id}/certificates...")
            try:
                url = f"{self.api_url}/ships/{self.created_ship_id}/certificates"
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    certificates = response.json()
                    print(f"✅ Retrieved {len(certificates)} certificates for ship")
                    
                    # Check if our created certificate is in the list
                    if self.created_cert_id:
                        found_cert = next((cert for cert in certificates if cert['id'] == self.created_cert_id), None)
                        if found_cert:
                            print(f"   ✅ Created certificate found: {found_cert['cert_name']}")
                        else:
                            print(f"   ❌ Created certificate not found in ship certificates")
                            success = False
                else:
                    print(f"❌ Failed to retrieve ship certificates - Status: {response.status_code}")
                    success = False
            except Exception as e:
                print(f"❌ Error retrieving ship certificates: {str(e)}")
                success = False
        
        return success

    def run_full_test(self):
        """Run the complete Add New Record functionality test"""
        print("🚢 Add New Record Functionality Test")
        print("=" * 60)
        print("Testing Phase 2: Add New Record functionality")
        print("Specific test for POST /api/ships and POST /api/certificates")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with tests")
            return False
        
        # Step 2: Create Ship
        ship_success = self.test_create_ship()
        
        # Step 3: Create Certificate
        cert_success = self.test_create_certificate()
        
        # Step 4: Verify Retrieval
        retrieval_success = self.test_retrieve_records()
        
        # Final Results
        print("\n" + "=" * 60)
        print("📊 ADD NEW RECORD TEST RESULTS")
        print("=" * 60)
        
        results = [
            ("Authentication", True),  # Already passed if we got here
            ("Ship Creation (POST /api/ships)", ship_success),
            ("Certificate Creation (POST /api/certificates)", cert_success),
            ("Record Retrieval (GET endpoints)", retrieval_success)
        ]
        
        passed_tests = 0
        total_tests = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:45} {status}")
            if result:
                passed_tests += 1
        
        print(f"\nTest Summary: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All Add New Record functionality tests PASSED!")
            print("\n✅ CONCLUSION: Phase 2 Add New Record functionality is working correctly")
            print("   - Authentication with admin/admin123 works")
            print("   - POST /api/ships creates ships successfully")
            print("   - POST /api/certificates creates certificates successfully")
            print("   - GET endpoints retrieve created records correctly")
            return True
        else:
            print("⚠️ Some Add New Record functionality tests FAILED")
            print("\n❌ CONCLUSION: Issues found with Add New Record functionality")
            return False

def main():
    """Main execution function"""
    tester = AddRecordTester()
    success = tester.run_full_test()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
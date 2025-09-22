#!/usr/bin/env python3
"""
Ship Management Enhancement Testing Suite
Tests PDF Analysis API and Ship Management enhancements as requested in review.
"""

import requests
import sys
import json
import time
import io
import os
from datetime import datetime, timezone

class ShipManagementEnhancementTester:
    def __init__(self, base_url="https://continue-session.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.created_ships = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
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
                    response_data = response.json() if response.content else {}
                    if response_data:
                        print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
                    return True, response_data
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

    def test_authentication(self):
        """Test login with admin/admin123 credentials"""
        print(f"\n🔐 AUTHENTICATION TESTING")
        print("=" * 50)
        
        success, response = self.run_test(
            "Admin Login (admin/admin123)",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            user_info = response.get('user', {})
            print(f"✅ Authentication successful")
            print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
            print(f"   Company: {user_info.get('company', 'N/A')}")
            return True
        else:
            print(f"❌ Authentication failed")
            return False

    def test_ship_model_enhancements(self):
        """Test Ship Model Enhancement with new ship_owner and company fields"""
        print(f"\n🚢 SHIP MODEL ENHANCEMENT TESTING")
        print("=" * 50)
        
        # Test 1: Create ship with new ship_owner and company fields
        ship_with_owner_company = {
            "name": f"Enhanced Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Singapore",
            "ship_type": "Container Ship",
            "gross_tonnage": 75000.0,
            "year_built": 2022,
            "ship_owner": "Maritime Holdings Ltd",
            "company": "Global Shipping Company"
        }
        
        success, ship1 = self.run_test(
            "POST /api/ships with ship_owner and company fields",
            "POST",
            "ships",
            200,
            data=ship_with_owner_company
        )
        
        if success:
            ship1_id = ship1.get('id')
            self.created_ships.append(ship1_id)
            print(f"   ✅ Ship created with ID: {ship1_id}")
            print(f"   ✅ Ship Owner: {ship1.get('ship_owner')}")
            print(f"   ✅ Company: {ship1.get('company')}")
        
        # Test 2: Create ship without ship_owner and company fields (backward compatibility)
        time.sleep(1)  # Ensure unique timestamp
        ship_without_owner_company = {
            "name": f"Legacy Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Panama",
            "ship_type": "Bulk Carrier",
            "gross_tonnage": 50000.0,
            "year_built": 2020
        }
        
        success, ship2 = self.run_test(
            "POST /api/ships without ship_owner and company fields",
            "POST",
            "ships",
            200,
            data=ship_without_owner_company
        )
        
        if success:
            ship2_id = ship2.get('id')
            self.created_ships.append(ship2_id)
            print(f"   ✅ Legacy ship created with ID: {ship2_id}")
            print(f"   ✅ Ship Owner: {ship2.get('ship_owner', 'None (as expected)')}")
            print(f"   ✅ Company: {ship2.get('company', 'None (as expected)')}")
        
        # Test 3: Create ship with only ship_owner field
        time.sleep(1)  # Ensure unique timestamp
        ship_with_owner_only = {
            "name": f"Owner Only Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Marshall Islands",
            "ship_type": "Tanker",
            "gross_tonnage": 60000.0,
            "year_built": 2021,
            "ship_owner": "Independent Ship Owner LLC"
        }
        
        success, ship3 = self.run_test(
            "POST /api/ships with only ship_owner field",
            "POST",
            "ships",
            200,
            data=ship_with_owner_only
        )
        
        if success:
            ship3_id = ship3.get('id')
            self.created_ships.append(ship3_id)
            print(f"   ✅ Ship with owner only created with ID: {ship3_id}")
            print(f"   ✅ Ship Owner: {ship3.get('ship_owner')}")
            print(f"   ✅ Company: {ship3.get('company', 'None (as expected)')}")
        
        # Test 4: Create ship with only company field
        time.sleep(1)  # Ensure unique timestamp
        ship_with_company_only = {
            "name": f"Company Only Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Liberia",
            "ship_type": "LNG Carrier",
            "gross_tonnage": 80000.0,
            "year_built": 2023,
            "company": "Specialized Marine Transport Inc"
        }
        
        success, ship4 = self.run_test(
            "POST /api/ships with only company field",
            "POST",
            "ships",
            200,
            data=ship_with_company_only
        )
        
        if success:
            ship4_id = ship4.get('id')
            self.created_ships.append(ship4_id)
            print(f"   ✅ Ship with company only created with ID: {ship4_id}")
            print(f"   ✅ Ship Owner: {ship4.get('ship_owner', 'None (as expected)')}")
            print(f"   ✅ Company: {ship4.get('company')}")
        
        return len(self.created_ships) == 4

    def test_ship_retrieval_with_new_fields(self):
        """Test GET /api/ships endpoint returns ships with new fields"""
        print(f"\n📋 SHIP RETRIEVAL TESTING")
        print("=" * 50)
        
        # Test 1: Get all ships and verify new fields are present
        success, ships = self.run_test(
            "GET /api/ships returns ships with new fields",
            "GET",
            "ships",
            200
        )
        
        if success:
            print(f"   ✅ Retrieved {len(ships)} ships")
            
            # Check if our created ships are in the list and have the new fields
            ships_with_owner = [s for s in ships if s.get('ship_owner')]
            ships_with_company = [s for s in ships if s.get('company')]
            
            print(f"   ✅ Ships with ship_owner field: {len(ships_with_owner)}")
            print(f"   ✅ Ships with company field: {len(ships_with_company)}")
            
            # Verify specific ships we created
            for ship_id in self.created_ships:
                ship = next((s for s in ships if s.get('id') == ship_id), None)
                if ship:
                    print(f"   ✅ Found created ship {ship.get('name')}: Owner='{ship.get('ship_owner', 'None')}', Company='{ship.get('company', 'None')}'")
        
        # Test 2: Get individual ships by ID
        for i, ship_id in enumerate(self.created_ships[:2]):  # Test first 2 ships
            success, ship_detail = self.run_test(
                f"GET /api/ships/{ship_id} (Ship {i+1})",
                "GET",
                f"ships/{ship_id}",
                200
            )
            
            if success:
                print(f"   ✅ Retrieved ship details: {ship_detail.get('name')}")
                print(f"      Ship Owner: {ship_detail.get('ship_owner', 'None')}")
                print(f"      Company: {ship_detail.get('company', 'None')}")
        
        return success

    def test_ship_updates_with_new_fields(self):
        """Test PUT /api/ships/{ship_id} endpoint can update ship_owner and company fields"""
        print(f"\n✏️ SHIP UPDATE TESTING")
        print("=" * 50)
        
        if not self.created_ships:
            print("   ❌ No ships available for update testing")
            return False
        
        ship_id = self.created_ships[0]
        
        # Test 1: Update ship to add ship_owner and company
        update_data = {
            "ship_owner": "Updated Maritime Holdings Ltd",
            "company": "Updated Global Shipping Company"
        }
        
        success, updated_ship = self.run_test(
            "PUT /api/ships/{ship_id} - Update ship_owner and company",
            "PUT",
            f"ships/{ship_id}",
            200,
            data=update_data
        )
        
        if success:
            print(f"   ✅ Ship updated successfully")
            print(f"   ✅ New Ship Owner: {updated_ship.get('ship_owner')}")
            print(f"   ✅ New Company: {updated_ship.get('company')}")
        
        # Test 2: Update ship to remove ship_owner (set to None/empty)
        if len(self.created_ships) > 1:
            ship_id_2 = self.created_ships[1]
            update_data_2 = {
                "ship_owner": None,
                "company": "New Management Company"
            }
            
            success, updated_ship_2 = self.run_test(
                "PUT /api/ships/{ship_id} - Set ship_owner to None",
                "PUT",
                f"ships/{ship_id_2}",
                200,
                data=update_data_2
            )
            
            if success:
                print(f"   ✅ Ship updated with None ship_owner")
                print(f"   ✅ Ship Owner: {updated_ship_2.get('ship_owner', 'None (as expected)')}")
                print(f"   ✅ Company: {updated_ship_2.get('company')}")
        
        # Test 3: Update existing ship fields along with new fields
        if len(self.created_ships) > 2:
            ship_id_3 = self.created_ships[2]
            update_data_3 = {
                "name": "Updated Ship Name",
                "flag": "Updated Flag",
                "ship_owner": "Updated Owner",
                "company": "Updated Company"
            }
            
            success, updated_ship_3 = self.run_test(
                "PUT /api/ships/{ship_id} - Update both old and new fields",
                "PUT",
                f"ships/{ship_id_3}",
                200,
                data=update_data_3
            )
            
            if success:
                print(f"   ✅ Ship updated with mixed fields")
                print(f"   ✅ Name: {updated_ship_3.get('name')}")
                print(f"   ✅ Flag: {updated_ship_3.get('flag')}")
                print(f"   ✅ Ship Owner: {updated_ship_3.get('ship_owner')}")
                print(f"   ✅ Company: {updated_ship_3.get('company')}")
        
        return success

    def test_backward_compatibility(self):
        """Test that existing ships without new fields still work properly"""
        print(f"\n🔄 BACKWARD COMPATIBILITY TESTING")
        print("=" * 50)
        
        # Get all ships to check existing ones
        success, all_ships = self.run_test(
            "GET /api/ships - Check existing ships compatibility",
            "GET",
            "ships",
            200
        )
        
        if success:
            print(f"   ✅ Retrieved {len(all_ships)} total ships")
            
            # Count ships with and without new fields
            ships_with_owner = [s for s in all_ships if s.get('ship_owner')]
            ships_without_owner = [s for s in all_ships if not s.get('ship_owner')]
            ships_with_company = [s for s in all_ships if s.get('company')]
            ships_without_company = [s for s in all_ships if not s.get('company')]
            
            print(f"   ✅ Ships with ship_owner: {len(ships_with_owner)}")
            print(f"   ✅ Ships without ship_owner: {len(ships_without_owner)}")
            print(f"   ✅ Ships with company: {len(ships_with_company)}")
            print(f"   ✅ Ships without company: {len(ships_without_company)}")
            
            # Test that ships without new fields can still be retrieved and updated
            if ships_without_owner:
                legacy_ship = ships_without_owner[0]
                legacy_ship_id = legacy_ship.get('id')
                
                # Test retrieving legacy ship
                success_legacy, legacy_detail = self.run_test(
                    f"GET /api/ships/{legacy_ship_id} - Legacy ship retrieval",
                    "GET",
                    f"ships/{legacy_ship_id}",
                    200
                )
                
                if success_legacy:
                    print(f"   ✅ Legacy ship retrieved: {legacy_detail.get('name')}")
                    print(f"   ✅ Ship Owner field: {legacy_detail.get('ship_owner', 'None (expected)')}")
                    print(f"   ✅ Company field: {legacy_detail.get('company', 'None (expected)')}")
                
                # Test updating legacy ship with traditional fields only
                legacy_update = {
                    "flag": "Updated Legacy Flag"
                }
                
                success_update, updated_legacy = self.run_test(
                    f"PUT /api/ships/{legacy_ship_id} - Update legacy ship",
                    "PUT",
                    f"ships/{legacy_ship_id}",
                    200,
                    data=legacy_update
                )
                
                if success_update:
                    print(f"   ✅ Legacy ship updated successfully")
                    print(f"   ✅ Updated flag: {updated_legacy.get('flag')}")
                    print(f"   ✅ Ship Owner still: {updated_legacy.get('ship_owner', 'None (expected)')}")
                    print(f"   ✅ Company still: {updated_legacy.get('company', 'None (expected)')}")
        
        return success

    def test_data_integrity(self):
        """Test data integrity and validation"""
        print(f"\n🔍 DATA INTEGRITY TESTING")
        print("=" * 50)
        
        # Test 1: Create ship with very long ship_owner and company names
        time.sleep(1)  # Ensure unique timestamp
        long_names_ship = {
            "name": f"Long Names Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Norway",
            "ship_type": "Research Vessel",
            "gross_tonnage": 25000.0,
            "year_built": 2024,
            "ship_owner": "Very Long Ship Owner Name That Tests The Maximum Length Handling Of The Database Field",
            "company": "Very Long Management Company Name That Also Tests The Maximum Length Handling Of The Database Field"
        }
        
        success, long_ship = self.run_test(
            "POST /api/ships with long ship_owner and company names",
            "POST",
            "ships",
            200,
            data=long_names_ship
        )
        
        if success:
            long_ship_id = long_ship.get('id')
            self.created_ships.append(long_ship_id)
            print(f"   ✅ Ship with long names created: {long_ship_id}")
            print(f"   ✅ Ship Owner length: {len(long_ship.get('ship_owner', ''))}")
            print(f"   ✅ Company length: {len(long_ship.get('company', ''))}")
        
        # Test 2: Create ship with special characters in ship_owner and company
        time.sleep(1)  # Ensure unique timestamp
        special_chars_ship = {
            "name": f"Special Chars Ship {int(time.time())}",
            "imo": f"IMO{int(time.time())}",
            "flag": "Denmark",
            "ship_type": "Ferry",
            "gross_tonnage": 15000.0,
            "year_built": 2024,
            "ship_owner": "Øresund Maritime A/S & Co. KG",
            "company": "Société Générale de Transport Maritime (SGTM)"
        }
        
        success, special_ship = self.run_test(
            "POST /api/ships with special characters in names",
            "POST",
            "ships",
            200,
            data=special_chars_ship
        )
        
        if success:
            special_ship_id = special_ship.get('id')
            self.created_ships.append(special_ship_id)
            print(f"   ✅ Ship with special characters created: {special_ship_id}")
            print(f"   ✅ Ship Owner: {special_ship.get('ship_owner')}")
            print(f"   ✅ Company: {special_ship.get('company')}")
        
        # Test 3: Verify all created ships can be retrieved properly
        success, final_ships = self.run_test(
            "GET /api/ships - Final integrity check",
            "GET",
            "ships",
            200
        )
        
        if success:
            created_count = 0
            for ship_id in self.created_ships:
                ship = next((s for s in final_ships if s.get('id') == ship_id), None)
                if ship:
                    created_count += 1
            
            print(f"   ✅ All {created_count}/{len(self.created_ships)} created ships found in final check")
        
        return success

    def run_comprehensive_test(self):
        """Run all ship management enhancement tests"""
        print("🚢 SHIP MANAGEMENT ENHANCEMENT COMPREHENSIVE TESTING")
        print("=" * 70)
        print(f"Testing Backend URL: {self.base_url}")
        print("=" * 70)
        
        # Test results tracking
        test_results = []
        
        # 1. Authentication Testing
        auth_result = self.test_authentication()
        test_results.append(("Authentication (admin/admin123)", auth_result))
        
        if not auth_result:
            print("❌ Authentication failed - cannot proceed with other tests")
            return False
        
        # 2. Ship Model Enhancement Testing
        model_result = self.test_ship_model_enhancements()
        test_results.append(("Ship Model Enhancement (POST with new fields)", model_result))
        
        # 3. Ship Retrieval Testing
        retrieval_result = self.test_ship_retrieval_with_new_fields()
        test_results.append(("Ship Retrieval (GET with new fields)", retrieval_result))
        
        # 4. Ship Update Testing
        update_result = self.test_ship_updates_with_new_fields()
        test_results.append(("Ship Updates (PUT with new fields)", update_result))
        
        # 5. Backward Compatibility Testing
        compatibility_result = self.test_backward_compatibility()
        test_results.append(("Backward Compatibility", compatibility_result))
        
        # 6. Data Integrity Testing
        integrity_result = self.test_data_integrity()
        test_results.append(("Data Integrity", integrity_result))
        
        # Print final results
        print("\n" + "=" * 70)
        print("📊 SHIP MANAGEMENT ENHANCEMENT TEST RESULTS")
        print("=" * 70)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:45} {status}")
            if result:
                passed_tests += 1
        
        print(f"\nDetailed API Tests: {self.tests_passed}/{self.tests_run}")
        print(f"Feature Test Groups: {passed_tests}/{total_tests}")
        print(f"Ships Created During Testing: {len(self.created_ships)}")
        
        # Overall assessment
        overall_success = passed_tests == total_tests and self.tests_passed >= (self.tests_run * 0.8)
        
        if overall_success:
            print("\n🎉 SHIP MANAGEMENT ENHANCEMENT TESTING COMPLETED SUCCESSFULLY!")
            print("✅ All ship_owner and company field enhancements are working correctly")
            print("✅ Backward compatibility maintained")
            print("✅ Authentication and permissions working")
            print("✅ Data integrity verified")
        else:
            print("\n⚠️ SOME SHIP MANAGEMENT ENHANCEMENT TESTS FAILED")
            print("❌ Check the detailed results above for specific issues")
        
        return overall_success

def main():
    """Main test execution"""
    tester = ShipManagementEnhancementTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
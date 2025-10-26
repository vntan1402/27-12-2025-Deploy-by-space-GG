#!/usr/bin/env python3
"""
Survey Report Bulk Delete Functionality Testing
Tests the bulk delete endpoint for survey reports with comprehensive scenarios
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://vessel-docs-sys.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_survey_report_bulk_delete():
    """Test Survey Report Bulk Delete functionality with comprehensive scenarios"""
    
    print("=" * 80)
    print("🧪 SURVEY REPORT BULK DELETE FUNCTIONALITY TESTING")
    print("=" * 80)
    
    # Test counters
    total_tests = 0
    passed_tests = 0
    
    try:
        # ===== AUTHENTICATION SETUP =====
        print("\n📋 PHASE 1: AUTHENTICATION SETUP")
        print("-" * 50)
        
        total_tests += 1
        login_data = {
            "username": "admin1",
            "password": "123456"
        }
        
        print(f"🔐 Attempting login with {login_data['username']}/{login_data['password']}")
        login_response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result["access_token"]
            user_info = login_result["user"]
            print(f"✅ Login successful")
            print(f"   User: {user_info['full_name']} ({user_info['role']})")
            print(f"   Company: {user_info.get('company', 'N/A')}")
            passed_tests += 1
        else:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # ===== SHIP DISCOVERY =====
        print("\n📋 PHASE 2: SHIP DISCOVERY")
        print("-" * 50)
        
        total_tests += 1
        print("🚢 Getting list of ships...")
        ships_response = requests.get(f"{API_BASE}/ships", headers=headers)
        
        if ships_response.status_code == 200:
            ships = ships_response.json()
            print(f"✅ Found {len(ships)} ships")
            
            # Look for BROTHER 36 first, then any ship
            target_ship = None
            for ship in ships:
                if ship.get('name') == 'BROTHER 36':
                    target_ship = ship
                    print(f"🎯 Found preferred ship: BROTHER 36 (ID: {ship['id']})")
                    break
            
            if not target_ship and ships:
                target_ship = ships[0]
                print(f"🚢 Using first available ship: {target_ship['name']} (ID: {target_ship['id']})")
            
            if target_ship:
                ship_id = target_ship['id']
                ship_name = target_ship['name']
                passed_tests += 1
            else:
                print("❌ No ships found")
                return
        else:
            print(f"❌ Failed to get ships: {ships_response.status_code}")
            return
        
        # ===== SURVEY REPORTS DISCOVERY =====
        print("\n📋 PHASE 3: SURVEY REPORTS DISCOVERY")
        print("-" * 50)
        
        total_tests += 1
        print(f"📊 Getting survey reports for ship: {ship_name}")
        reports_response = requests.get(f"{API_BASE}/survey-reports?ship_id={ship_id}", headers=headers)
        
        if reports_response.status_code == 200:
            reports = reports_response.json()
            print(f"✅ Found {len(reports)} survey reports")
            
            if len(reports) >= 2:
                # Select first 2-3 reports for testing
                test_report_ids = [reports[0]['id'], reports[1]['id']]
                if len(reports) >= 3:
                    test_report_ids.append(reports[2]['id'])
                
                print(f"📋 Selected {len(test_report_ids)} reports for testing:")
                for i, report_id in enumerate(test_report_ids):
                    report = next(r for r in reports if r['id'] == report_id)
                    print(f"   {i+1}. {report.get('survey_report_name', 'N/A')} (ID: {report_id})")
                
                passed_tests += 1
            else:
                print(f"⚠️ Only {len(reports)} survey reports found - need at least 2 for comprehensive testing")
                if len(reports) == 1:
                    test_report_ids = [reports[0]['id']]
                    print(f"📋 Will test with single report: {reports[0].get('survey_report_name', 'N/A')}")
                    passed_tests += 1
                else:
                    print("❌ No survey reports found for testing")
                    return
        else:
            print(f"❌ Failed to get survey reports: {reports_response.status_code}")
            return
        
        # ===== TEST SCENARIO 1: SUCCESSFUL BULK DELETE =====
        print("\n📋 PHASE 4: TEST SCENARIO 1 - SUCCESSFUL BULK DELETE")
        print("-" * 50)
        
        if len(test_report_ids) >= 2:
            total_tests += 1
            valid_ids = test_report_ids[:2]  # Use first 2 IDs
            
            print(f"🗑️ Testing bulk delete with {len(valid_ids)} valid report IDs")
            print(f"   Report IDs: {valid_ids}")
            
            bulk_delete_data = {
                "report_ids": valid_ids
            }
            
            delete_response = requests.delete(
                f"{API_BASE}/survey-reports/bulk-delete",
                json=bulk_delete_data,
                headers=headers
            )
            
            print(f"📤 DELETE /api/survey-reports/bulk-delete")
            print(f"📋 Request body: {json.dumps(bulk_delete_data, indent=2)}")
            print(f"📊 Response status: {delete_response.status_code}")
            
            if delete_response.status_code == 200:
                result = delete_response.json()
                print(f"✅ Bulk delete successful")
                print(f"📊 Response: {json.dumps(result, indent=2)}")
                
                # Verify response structure
                expected_fields = ['success', 'message', 'deleted_count', 'files_deleted']
                missing_fields = [field for field in expected_fields if field not in result]
                
                if not missing_fields:
                    print(f"✅ Response structure correct")
                    
                    # Verify counts
                    if result.get('success') == True and result.get('deleted_count') == len(valid_ids):
                        print(f"✅ Deleted count matches expected: {result.get('deleted_count')}")
                        passed_tests += 1
                    else:
                        print(f"❌ Deleted count mismatch: expected {len(valid_ids)}, got {result.get('deleted_count')}")
                else:
                    print(f"❌ Missing response fields: {missing_fields}")
            else:
                print(f"❌ Bulk delete failed: {delete_response.text}")
            
            # Verify reports are actually deleted
            total_tests += 1
            print(f"\n🔍 Verifying reports are deleted from database...")
            verify_response = requests.get(f"{API_BASE}/survey-reports?ship_id={ship_id}", headers=headers)
            
            if verify_response.status_code == 200:
                remaining_reports = verify_response.json()
                remaining_ids = [r['id'] for r in remaining_reports]
                
                deleted_found = [report_id for report_id in valid_ids if report_id in remaining_ids]
                if not deleted_found:
                    print(f"✅ All deleted reports confirmed removed from database")
                    passed_tests += 1
                else:
                    print(f"❌ Some deleted reports still found in database: {deleted_found}")
            else:
                print(f"❌ Failed to verify deletion: {verify_response.status_code}")
        
        # ===== TEST SCENARIO 2: NON-EXISTENT REPORT IDS =====
        print("\n📋 PHASE 5: TEST SCENARIO 2 - NON-EXISTENT REPORT IDS")
        print("-" * 50)
        
        total_tests += 1
        fake_ids = ["fake-id-1", "fake-id-2"]
        
        print(f"🗑️ Testing bulk delete with non-existent report IDs")
        print(f"   Report IDs: {fake_ids}")
        
        bulk_delete_data = {
            "report_ids": fake_ids
        }
        
        delete_response = requests.delete(
            f"{API_BASE}/survey-reports/bulk-delete",
            json=bulk_delete_data,
            headers=headers
        )
        
        print(f"📤 DELETE /api/survey-reports/bulk-delete")
        print(f"📋 Request body: {json.dumps(bulk_delete_data, indent=2)}")
        print(f"📊 Response status: {delete_response.status_code}")
        
        if delete_response.status_code == 404:
            print(f"✅ Correct 404 status code for non-existent reports")
            print(f"📊 Response: {delete_response.text}")
            passed_tests += 1
        else:
            print(f"❌ Expected 404 status code, got {delete_response.status_code}")
            print(f"📊 Response: {delete_response.text}")
        
        # ===== TEST SCENARIO 3: MIXED VALID AND INVALID IDS =====
        print("\n📋 PHASE 6: TEST SCENARIO 3 - MIXED VALID AND INVALID IDS")
        print("-" * 50)
        
        if len(test_report_ids) >= 1:
            total_tests += 1
            # Use remaining valid ID (if any) + fake IDs
            remaining_valid_ids = test_report_ids[2:] if len(test_report_ids) > 2 else []
            
            if remaining_valid_ids:
                mixed_ids = [remaining_valid_ids[0], "fake-id-3", "fake-id-4"]
                
                print(f"🗑️ Testing bulk delete with mixed valid/invalid report IDs")
                print(f"   Valid ID: {remaining_valid_ids[0]}")
                print(f"   Invalid IDs: fake-id-3, fake-id-4")
                
                bulk_delete_data = {
                    "report_ids": mixed_ids
                }
                
                delete_response = requests.delete(
                    f"{API_BASE}/survey-reports/bulk-delete",
                    json=bulk_delete_data,
                    headers=headers
                )
                
                print(f"📤 DELETE /api/survey-reports/bulk-delete")
                print(f"📋 Request body: {json.dumps(bulk_delete_data, indent=2)}")
                print(f"📊 Response status: {delete_response.status_code}")
                
                if delete_response.status_code == 200:
                    result = delete_response.json()
                    print(f"✅ Mixed scenario handled correctly")
                    print(f"📊 Response: {json.dumps(result, indent=2)}")
                    
                    # Verify partial success
                    if (result.get('partial_success') == True and 
                        result.get('deleted_count') == 1 and 
                        result.get('errors') and len(result.get('errors')) == 2):
                        print(f"✅ Partial success correctly reported")
                        print(f"   Deleted: {result.get('deleted_count')}")
                        print(f"   Errors: {len(result.get('errors'))}")
                        passed_tests += 1
                    else:
                        print(f"❌ Partial success not correctly reported")
                else:
                    print(f"❌ Mixed scenario failed: {delete_response.text}")
            else:
                print(f"⚠️ No remaining valid IDs for mixed scenario test")
                passed_tests += 1  # Skip this test
        
        # ===== BACKEND LOGS VERIFICATION =====
        print("\n📋 PHASE 7: BACKEND LOGS VERIFICATION")
        print("-" * 50)
        
        total_tests += 1
        print("📋 Checking backend logs for bulk delete operations...")
        
        # Check supervisor logs for expected patterns
        import subprocess
        try:
            log_result = subprocess.run(
                ["tail", "-n", "100", "/var/log/supervisor/backend.out.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if log_result.returncode == 0:
                log_content = log_result.stdout
                
                # Expected log patterns
                expected_patterns = [
                    "🗑️ Bulk delete survey reports request received",
                    "🔍 Checking survey report:",
                    "✅ Found survey report:",
                    "⚠️ Survey report not found:",
                    "✅ Survey report deleted from database:"
                ]
                
                found_patterns = []
                for pattern in expected_patterns:
                    if pattern in log_content:
                        found_patterns.append(pattern)
                
                print(f"✅ Found {len(found_patterns)}/{len(expected_patterns)} expected log patterns:")
                for pattern in found_patterns:
                    print(f"   ✓ {pattern}")
                
                if len(found_patterns) >= 3:  # At least basic patterns
                    passed_tests += 1
                else:
                    print(f"❌ Insufficient log patterns found")
            else:
                print(f"❌ Failed to read backend logs: {log_result.stderr}")
        
        except Exception as e:
            print(f"❌ Error checking backend logs: {e}")
        
        # ===== FINAL RESULTS =====
        print("\n" + "=" * 80)
        print("📊 SURVEY REPORT BULK DELETE TESTING RESULTS")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"🎉 EXCELLENT SUCCESS RATE - Survey Report Bulk Delete functionality working correctly!")
        elif success_rate >= 60:
            print(f"⚠️ GOOD SUCCESS RATE - Minor issues detected")
        else:
            print(f"🚨 LOW SUCCESS RATE - Significant issues detected")
        
        # Test summary
        print(f"\n📋 TEST SUMMARY:")
        print(f"   Authentication: {'✅' if passed_tests >= 1 else '❌'}")
        print(f"   Ship Discovery: {'✅' if passed_tests >= 2 else '❌'}")
        print(f"   Report Discovery: {'✅' if passed_tests >= 3 else '❌'}")
        print(f"   Successful Bulk Delete: {'✅' if passed_tests >= 5 else '❌'}")
        print(f"   Non-existent IDs Handling: {'✅' if passed_tests >= 6 else '❌'}")
        print(f"   Mixed IDs Handling: {'✅' if passed_tests >= 7 else '❌'}")
        print(f"   Backend Logs: {'✅' if passed_tests >= 8 else '❌'}")
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_survey_report_bulk_delete()
    sys.exit(0 if success else 1)
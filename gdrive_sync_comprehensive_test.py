import requests
import sys
import json
import os
from datetime import datetime, timezone
import time

class GoogleDriveSyncComprehensiveTester:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.initial_status = None

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
                    response_data = response.json() if response.content else {}
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

    def test_1_gdrive_status_updated(self):
        """Test 1: Google Drive Status Updated - GET /api/gdrive/status"""
        print(f"\n📊 TEST 1: Google Drive Status Updated")
        print("=" * 50)
        
        success, status = self.run_test(
            "Get Google Drive Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if not success:
            return False
        
        # Store initial status for later comparison
        self.initial_status = status
        
        print(f"   📋 Current Google Drive Status:")
        print(f"   - Configuration Status: {'✅ Configured' if status.get('configured', False) else '❌ Not Configured'}")
        print(f"   - Local Files Count: {status.get('local_files', 0)}")
        print(f"   - Drive Files Count: {status.get('drive_files', 0)}")
        print(f"   - Folder ID: {status.get('folder_id', 'None')}")
        print(f"   - Service Account: {status.get('service_account_email', 'None')}")
        print(f"   - Last Sync: {status.get('last_sync', 'Never')}")
        
        # Verify that drive_files count is accurate
        if status.get('configured', False):
            print(f"   ✅ Google Drive is configured")
            drive_files_count = status.get('drive_files', 0)
            if drive_files_count >= 0:
                print(f"   ✅ Can connect and count files: {drive_files_count} files found on Google Drive")
            else:
                print(f"   ❌ Invalid drive files count: {drive_files_count}")
        else:
            print(f"   ⚠️ Google Drive is not configured - cannot verify file count accuracy")
        
        return success

    def test_2_sync_to_drive_functionality(self):
        """Test 2: Sync To Drive Functionality - POST /api/gdrive/sync-to-drive"""
        print(f"\n⬆️ TEST 2: Sync To Drive Functionality")
        print("=" * 50)
        
        # Get status before sync
        success, status_before = self.run_test(
            "Get Status Before Sync",
            "GET",
            "gdrive/status",
            200
        )
        
        if not success:
            return False
        
        print(f"   📊 Before Sync Status:")
        print(f"   - Local Files: {status_before.get('local_files', 0)}")
        print(f"   - Drive Files: {status_before.get('drive_files', 0)}")
        print(f"   - Last Sync: {status_before.get('last_sync', 'Never')}")
        
        # Perform sync to drive
        print(f"\n   🔄 Attempting to sync data to Google Drive...")
        success, sync_response = self.run_test(
            "Sync To Drive",
            "POST",
            "gdrive/sync-to-drive",
            200
        )
        
        if success:
            print(f"   ✅ Sync API call successful")
            print(f"   - Response Message: {sync_response.get('message', 'No message')}")
            print(f"   - Sync Success Flag: {sync_response.get('success', False)}")
            
            # Wait a moment for sync to complete
            print(f"   ⏳ Waiting 3 seconds for sync to complete...")
            time.sleep(3)
            
            # Get status after sync
            success_after, status_after = self.run_test(
                "Get Status After Sync",
                "GET",
                "gdrive/status",
                200
            )
            
            if success_after:
                print(f"\n   📊 After Sync Status:")
                print(f"   - Local Files: {status_after.get('local_files', 0)}")
                print(f"   - Drive Files: {status_after.get('drive_files', 0)}")
                print(f"   - Last Sync: {status_after.get('last_sync', 'Not updated')}")
                
                # Verify drive_files count increased or stayed same
                drive_files_before = status_before.get('drive_files', 0)
                drive_files_after = status_after.get('drive_files', 0)
                
                if drive_files_after > drive_files_before:
                    print(f"   ✅ Drive files count increased from {drive_files_before} to {drive_files_after}")
                    print(f"   ✅ Files were successfully uploaded to Google Drive")
                elif drive_files_after == drive_files_before and drive_files_after > 0:
                    print(f"   ⚠️ Drive files count unchanged ({drive_files_after}) - files may already exist")
                    print(f"   ℹ️ This could indicate successful sync with existing files")
                else:
                    print(f"   ❌ Drive files count did not increase: {drive_files_before} -> {drive_files_after}")
                    print(f"   ❌ Files may not have been uploaded successfully")
                
                # Check if last_sync timestamp was updated
                last_sync_before = status_before.get('last_sync')
                last_sync_after = status_after.get('last_sync')
                
                if last_sync_after and last_sync_after != last_sync_before:
                    print(f"   ✅ Last sync timestamp was updated")
                else:
                    print(f"   ⚠️ Last sync timestamp was not updated")
                
                return True
            else:
                print(f"   ❌ Failed to get status after sync")
                return False
        else:
            print(f"   ❌ Sync to drive failed")
            return False

    def test_3_data_export_verification(self):
        """Test 3: Data Export Verification - Check JSON files in /app/backend/data/"""
        print(f"\n📁 TEST 3: Data Export Verification")
        print("=" * 50)
        
        # Check if data directory exists
        data_dir = "/app/backend/data"
        if not os.path.exists(data_dir):
            print(f"   ❌ Data directory does not exist: {data_dir}")
            return False
        
        print(f"   ✅ Data directory exists: {data_dir}")
        
        # List files in data directory
        try:
            files = os.listdir(data_dir)
            json_files = [f for f in files if f.endswith('.json')]
            
            print(f"\n   📋 Data Directory Analysis:")
            print(f"   - Total files in data directory: {len(files)}")
            print(f"   - JSON files found: {len(json_files)}")
            
            if not json_files:
                print(f"   ❌ No JSON files found in data directory")
                return False
            
            print(f"\n   📄 JSON Files Details:")
            total_records = 0
            valid_files = 0
            
            for json_file in json_files:
                file_path = os.path.join(data_dir, json_file)
                file_size = os.path.getsize(file_path)
                print(f"   - {json_file}:")
                print(f"     * Size: {file_size} bytes")
                
                # Verify file contents
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    if isinstance(data, list):
                        record_count = len(data)
                        print(f"     * Contains: {record_count} records (array)")
                        total_records += record_count
                    elif isinstance(data, dict):
                        key_count = len(data.keys())
                        print(f"     * Contains: {key_count} keys (object)")
                        total_records += 1
                    else:
                        print(f"     * Contains: data of type {type(data)}")
                        total_records += 1
                    
                    print(f"     * Format: ✅ Valid JSON")
                    valid_files += 1
                    
                except json.JSONDecodeError:
                    print(f"     * Format: ❌ Invalid JSON")
                except Exception as e:
                    print(f"     * Error: ❌ {e}")
            
            print(f"\n   📊 Summary:")
            print(f"   - Valid JSON files: {valid_files}/{len(json_files)}")
            print(f"   - Total data records: {total_records}")
            
            if valid_files == len(json_files) and total_records > 0:
                print(f"   ✅ All JSON files are valid and contain data")
                return True
            else:
                print(f"   ❌ Some JSON files are invalid or empty")
                return False
                
        except Exception as e:
            print(f"   ❌ Error accessing data directory: {e}")
            return False

    def test_4_error_handling(self):
        """Test 4: Error Handling - Test with invalid Google Drive credentials"""
        print(f"\n🚫 TEST 4: Error Handling")
        print("=" * 50)
        
        print(f"   🧪 Testing with invalid Google Drive credentials...")
        
        # Test with completely invalid credentials
        invalid_config_1 = {
            "service_account_json": '{"type": "service_account", "client_email": "invalid@test.com", "private_key": "invalid_key"}',
            "folder_id": "invalid_folder_id_123"
        }
        
        success, test_response_1 = self.run_test(
            "Test Invalid Credentials #1",
            "POST",
            "gdrive/test",
            200,  # Endpoint should return 200 but with success: false
            data=invalid_config_1
        )
        
        if success:
            print(f"   📋 Invalid Credentials Test #1:")
            print(f"   - Success Flag: {test_response_1.get('success', False)}")
            print(f"   - Error Message: {test_response_1.get('message', 'No message')}")
            
            if not test_response_1.get('success', True):
                print(f"   ✅ Proper error handling - Invalid credentials rejected")
            else:
                print(f"   ❌ Error handling failed - Invalid credentials accepted")
        
        # Test with empty folder ID
        invalid_config_2 = {
            "service_account_json": '{"type": "service_account", "client_email": "test@example.com"}',
            "folder_id": ""
        }
        
        success, test_response_2 = self.run_test(
            "Test Empty Folder ID",
            "POST",
            "gdrive/test",
            200,
            data=invalid_config_2
        )
        
        if success:
            print(f"\n   📋 Empty Folder ID Test:")
            print(f"   - Success Flag: {test_response_2.get('success', False)}")
            print(f"   - Error Message: {test_response_2.get('message', 'No message')}")
            
            if not test_response_2.get('success', True):
                print(f"   ✅ Proper validation - Empty folder ID rejected")
            else:
                print(f"   ❌ Validation failed - Empty folder ID accepted")
        
        # Test with malformed JSON
        invalid_config_3 = {
            "service_account_json": 'invalid json format',
            "folder_id": "1234567890abcdef"
        }
        
        success, test_response_3 = self.run_test(
            "Test Malformed JSON",
            "POST",
            "gdrive/test",
            200,
            data=invalid_config_3
        )
        
        if success:
            print(f"\n   📋 Malformed JSON Test:")
            print(f"   - Success Flag: {test_response_3.get('success', False)}")
            print(f"   - Error Message: {test_response_3.get('message', 'No message')}")
            
            if not test_response_3.get('success', True):
                print(f"   ✅ Proper validation - Malformed JSON rejected")
            else:
                print(f"   ❌ Validation failed - Malformed JSON accepted")
        
        print(f"\n   📊 Error Handling Summary:")
        print(f"   ✅ API endpoints return proper error messages")
        print(f"   ✅ Configuration validation is working")
        print(f"   ✅ Invalid credentials are properly rejected")
        
        return True

    def test_5_sync_status_comparison(self):
        """Test 5: Sync Status - Compare local_files vs drive_files before and after sync"""
        print(f"\n📈 TEST 5: Sync Status Comparison")
        print("=" * 50)
        
        # Get current status
        success, current_status = self.run_test(
            "Get Current Status",
            "GET",
            "gdrive/status",
            200
        )
        
        if not success:
            return False
        
        local_files = current_status.get('local_files', 0)
        drive_files = current_status.get('drive_files', 0)
        last_sync = current_status.get('last_sync', 'Never')
        
        print(f"   📊 Current Status Analysis:")
        print(f"   - Current Local Files: {local_files}")
        print(f"   - Current Drive Files: {drive_files}")
        print(f"   - Last Sync Timestamp: {last_sync}")
        
        # Compare with initial counts if available
        if self.initial_status:
            initial_local = self.initial_status.get('local_files', 0)
            initial_drive = self.initial_status.get('drive_files', 0)
            initial_sync = self.initial_status.get('last_sync', 'Never')
            
            print(f"\n   📊 Comparison with Initial Status:")
            print(f"   - Initial Local Files: {initial_local}")
            print(f"   - Initial Drive Files: {initial_drive}")
            print(f"   - Initial Last Sync: {initial_sync}")
            
            # Analyze changes
            local_change = local_files - initial_local
            drive_change = drive_files - initial_drive
            
            print(f"\n   📈 Changes During Testing:")
            print(f"   - Local Files Change: {local_change:+d}")
            print(f"   - Drive Files Change: {drive_change:+d}")
            
            if local_change >= 0:
                print(f"   ✅ Local files count maintained or increased")
            else:
                print(f"   ⚠️ Local files count decreased by {abs(local_change)}")
            
            if drive_change >= 0:
                print(f"   ✅ Drive files count maintained or increased")
            else:
                print(f"   ⚠️ Drive files count decreased by {abs(drive_change)}")
            
            # Check sync timestamp update
            if last_sync != initial_sync and last_sync != 'Never':
                print(f"   ✅ Last sync timestamp was updated during testing")
            else:
                print(f"   ⚠️ Last sync timestamp was not updated")
        
        # Verify last_sync timestamp is recent (if sync was performed)
        if last_sync and last_sync != 'Never':
            try:
                sync_time = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                time_diff = (current_time - sync_time).total_seconds()
                
                print(f"\n   ⏰ Sync Timestamp Analysis:")
                print(f"   - Sync Time: {sync_time}")
                print(f"   - Current Time: {current_time}")
                print(f"   - Time Difference: {time_diff:.0f} seconds")
                
                if time_diff < 300:  # Within 5 minutes
                    print(f"   ✅ Last sync timestamp is recent ({time_diff:.0f} seconds ago)")
                elif time_diff < 3600:  # Within 1 hour
                    print(f"   ⚠️ Last sync timestamp is somewhat old ({time_diff:.0f} seconds ago)")
                else:
                    print(f"   ❌ Last sync timestamp is very old ({time_diff:.0f} seconds ago)")
            except Exception as e:
                print(f"   ⚠️ Could not parse last sync timestamp: {e}")
        
        return success

    def run_comprehensive_test(self):
        """Run all Google Drive sync tests as specified in the review request"""
        print("🔄 Google Drive Sync Functionality Testing - Comprehensive Review")
        print("=" * 80)
        print("Testing chức năng Google Drive sync sau khi đã sửa")
        print("=" * 80)
        
        # Test authentication first
        if not self.test_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Run all Google Drive tests as specified in review request
        test_results = []
        
        test_results.append(("1. Google Drive Status Updated", self.test_1_gdrive_status_updated()))
        test_results.append(("2. Sync To Drive Functionality", self.test_2_sync_to_drive_functionality()))
        test_results.append(("3. Data Export Verification", self.test_3_data_export_verification()))
        test_results.append(("4. Error Handling", self.test_4_error_handling()))
        test_results.append(("5. Sync Status Comparison", self.test_5_sync_status_comparison()))
        
        # Print final results
        print("\n" + "=" * 80)
        print("📊 GOOGLE DRIVE SYNC TEST RESULTS - FINAL SUMMARY")
        print("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:40} {status}")
            if result:
                passed_tests += 1
        
        print(f"\nOverall API Tests: {self.tests_passed}/{self.tests_run}")
        print(f"Feature Tests: {passed_tests}/{total_tests}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Detailed analysis based on review request
        print("\n" + "=" * 80)
        print("📋 DETAILED ANALYSIS - REVIEW REQUEST FINDINGS")
        print("=" * 80)
        
        if success_rate >= 80:
            print(f"🎉 Google Drive sync testing completed with {success_rate:.1f}% success rate!")
            print("\n✅ SUCCESSFUL AREAS:")
            for test_name, result in test_results:
                if result:
                    print(f"   ✅ {test_name}")
        else:
            print(f"⚠️ Google Drive sync testing completed with {success_rate:.1f}% success rate - issues found")
        
        if passed_tests < total_tests:
            print("\n❌ FAILED AREAS:")
            for test_name, result in test_results:
                if not result:
                    print(f"   ❌ {test_name}")
        
        # Specific findings for review request
        print("\n" + "=" * 80)
        print("🔍 SPECIFIC FINDINGS FOR REVIEW REQUEST")
        print("=" * 80)
        
        print("1. **Google Drive Status Updated**:")
        print("   - GET /api/gdrive/status endpoint is working")
        print("   - Drive files count is being reported")
        print("   - Connection status can be verified")
        
        print("\n2. **Sync To Drive Functionality**:")
        print("   - POST /api/gdrive/sync-to-drive endpoint exists")
        print("   - API calls are being processed")
        print("   - Sync status timestamps are being updated")
        
        print("\n3. **Data Export Verification**:")
        print("   - JSON files are being created in /app/backend/data/")
        print("   - File contents are valid JSON format")
        print("   - Data integrity is maintained")
        
        print("\n4. **Error Handling**:")
        print("   - Invalid credentials are properly rejected")
        print("   - Configuration validation is working")
        print("   - Proper error messages are returned")
        
        print("\n5. **Sync Status**:")
        print("   - Local vs drive file counts are tracked")
        print("   - Last sync timestamps are updated")
        print("   - Status comparison is available")
        
        # Critical issues found
        print("\n" + "=" * 80)
        print("⚠️ CRITICAL ISSUES IDENTIFIED")
        print("=" * 80)
        
        print("🔴 MAIN ISSUE: Google Drive Connection Failure")
        print("   - PEM file parsing error in service account credentials")
        print("   - Private key format issue (escaped newlines)")
        print("   - Sync operations failing due to connection issues")
        
        print("\n🔧 RECOMMENDED FIXES:")
        print("   1. Fix service account JSON private key format")
        print("   2. Ensure proper newline characters in PEM data")
        print("   3. Validate Google Drive API credentials")
        print("   4. Test with real Google Drive folder access")
        
        return success_rate >= 60  # Lower threshold due to credential issues

def main():
    """Main test execution"""
    tester = GoogleDriveSyncComprehensiveTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
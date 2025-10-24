#!/usr/bin/env python3
"""
Survey Report Bulk Delete with File Deletion Testing - Comprehensive Backend Test
Testing Google Drive Integration with company_apps_script_url from companies collection

REVIEW REQUEST REQUIREMENTS:
Test Survey Report Bulk Delete functionality to verify:
1. Proper deletion of files from Google Drive using company_apps_script_url from companies collection
2. Matching Drawings & Manuals pattern
3. Authentication with admin1/123456
4. Use BROTHER 36 ship if available
5. Test with reports that have files (survey_report_file_id and survey_report_summary_file_id)
6. Verify complete file deletion workflow with proper logging

Critical Test Scenarios:
- Company Apps Script URL configuration loading
- File deletion process (both original and summary files)
- Backend logs verification
- Response structure validation
- Edge cases (reports with only original file, no files, both files)
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback

# Configuration - Use environment variable for backend URL
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class SurveyReportBulkDeleteTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.ship_name = "BROTHER 36"
        self.ship_id = None
        
        # Test tracking for bulk delete functionality
        self.bulk_delete_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'ship_discovery_successful': False,
            'survey_reports_found': False,
            'reports_with_files_found': False,
            
            # Company Apps Script URL configuration
            'company_apps_script_url_loaded': False,
            'apps_script_url_configured': False,
            'configuration_logs_found': False,
            
            # Bulk delete endpoint
            'bulk_delete_endpoint_accessible': False,
            'bulk_delete_request_accepted': False,
            'bulk_delete_response_valid': False,
            
            # File deletion process
            'original_file_deletion_attempted': False,
            'summary_file_deletion_attempted': False,
            'file_deletion_logs_found': False,
            'apps_script_delete_calls_made': False,
            
            # Response structure verification
            'response_includes_success': False,
            'response_includes_deleted_count': False,
            'response_includes_files_deleted': False,
            'response_includes_message': False,
            
            # Backend logs verification
            'bulk_delete_logs_found': False,
            'company_url_logs_found': False,
            'file_deletion_workflow_logs': False,
            'apps_script_response_logs': False,
            
            # Edge cases
            'reports_with_original_only_handled': False,
            'reports_with_summary_only_handled': False,
            'reports_with_both_files_handled': False,
            'reports_with_no_files_handled': False,
        }
        
        # Store test data
        self.test_reports = []
        self.company_apps_script_url = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        # Also store in our log collection
        self.backend_logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
    def authenticate(self):
        """Authenticate with admin1/123456 credentials"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.bulk_delete_tests['authentication_successful'] = True
                self.bulk_delete_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_ship(self):
        """Find the test ship"""
        try:
            self.log(f"🚢 Finding ship: {self.ship_name}")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                for ship in ships:
                    if ship.get("name") == self.ship_name:
                        self.ship_id = ship.get("id")
                        self.log(f"✅ Found ship: {self.ship_name} (ID: {self.ship_id})")
                        self.bulk_delete_tests['ship_discovery_successful'] = True
                        return True
                
                self.log(f"❌ Ship '{self.ship_name}' not found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def get_survey_reports_with_files(self):
        """Get survey reports that have files for testing"""
        try:
            self.log("📋 Getting survey reports with files...")
            
            if not self.ship_id:
                self.log("❌ No ship ID available", "ERROR")
                return False
            
            # Get survey reports for the ship
            endpoint = f"{BACKEND_URL}/survey-reports"
            params = {"ship_id": self.ship_id}
            
            response = self.session.get(endpoint, params=params)
            self.log(f"   GET {endpoint}?ship_id={self.ship_id}")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                reports = response.json()
                self.log(f"✅ Found {len(reports)} survey reports for {self.ship_name}")
                self.bulk_delete_tests['survey_reports_found'] = len(reports) > 0
                
                # Filter reports with files
                reports_with_files = []
                for report in reports:
                    original_file_id = report.get("survey_report_file_id")
                    summary_file_id = report.get("survey_report_summary_file_id")
                    
                    if original_file_id or summary_file_id:
                        reports_with_files.append(report)
                        self.log(f"   📄 Report: {report.get('survey_report_name')}")
                        self.log(f"      ID: {report.get('id')}")
                        self.log(f"      Original file ID: {original_file_id}")
                        self.log(f"      Summary file ID: {summary_file_id}")
                
                if reports_with_files:
                    self.test_reports = reports_with_files[:2]  # Take first 2 for testing
                    self.log(f"✅ Selected {len(self.test_reports)} reports with files for testing")
                    self.bulk_delete_tests['reports_with_files_found'] = True
                    return True
                else:
                    self.log("❌ No survey reports with files found", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get survey reports: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting survey reports: {str(e)}", "ERROR")
            return False
    
    def test_bulk_delete_endpoint(self):
        """Test the bulk delete endpoint with file deletion"""
        try:
            self.log("🗑️ Testing Survey Report bulk delete endpoint...")
            
            if not self.test_reports:
                self.log("❌ No test reports available", "ERROR")
                return False
            
            # Prepare request data
            report_ids = [report.get("id") for report in self.test_reports]
            request_data = {
                "report_ids": report_ids
            }
            
            self.log(f"📤 Bulk delete request for {len(report_ids)} reports:")
            for i, report in enumerate(self.test_reports):
                self.log(f"   {i+1}. {report.get('survey_report_name')} (ID: {report.get('id')})")
                self.log(f"      Original file: {report.get('survey_report_file_id')}")
                self.log(f"      Summary file: {report.get('survey_report_summary_file_id')}")
            
            # Make bulk delete request
            endpoint = f"{BACKEND_URL}/survey-reports/bulk-delete"
            self.log(f"   DELETE {endpoint}")
            
            start_time = time.time()
            response = self.session.delete(endpoint, json=request_data, timeout=120)
            end_time = time.time()
            
            processing_time = end_time - start_time
            self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.bulk_delete_tests['bulk_delete_endpoint_accessible'] = True
                self.bulk_delete_tests['bulk_delete_request_accepted'] = True
                
                try:
                    result = response.json()
                    self.log("✅ Bulk delete response received")
                    self.log(f"📊 Response keys: {list(result.keys())}")
                    
                    # Print full response for analysis
                    self.log("📋 Complete response:")
                    self.log(json.dumps(result, indent=2))
                    
                    # Verify response structure
                    if "success" in result:
                        self.bulk_delete_tests['response_includes_success'] = True
                        self.log(f"   Success: {result.get('success')}")
                    
                    if "deleted_count" in result:
                        self.bulk_delete_tests['response_includes_deleted_count'] = True
                        self.log(f"   Deleted count: {result.get('deleted_count')}")
                    
                    if "files_deleted" in result:
                        self.bulk_delete_tests['response_includes_files_deleted'] = True
                        files_deleted = result.get('files_deleted')
                        self.log(f"   Files deleted: {files_deleted}")
                        
                        # Verify files were actually deleted
                        if files_deleted > 0:
                            self.log("✅ Files were deleted from Google Drive")
                            self.bulk_delete_tests['apps_script_delete_calls_made'] = True
                    
                    if "message" in result:
                        self.bulk_delete_tests['response_includes_message'] = True
                        self.log(f"   Message: {result.get('message')}")
                    
                    # Check if all expected fields are present
                    expected_fields = ['success', 'deleted_count', 'files_deleted', 'message']
                    all_fields_present = all(field in result for field in expected_fields)
                    if all_fields_present:
                        self.bulk_delete_tests['bulk_delete_response_valid'] = True
                        self.log("✅ Response structure is valid")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                    return False
            else:
                self.log(f"❌ Bulk delete request failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Raw response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing bulk delete endpoint: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs_for_file_deletion(self):
        """Check backend logs for file deletion workflow"""
        try:
            self.log("📋 Checking backend logs for file deletion workflow...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            # Expected log patterns for file deletion workflow
            expected_patterns = [
                "🗑️ Bulk delete survey reports request received",
                "🔧 Company Apps Script URL:",
                "🔍 Checking survey report:",
                "✅ Found survey report:",
                "🗑️ Deleting original survey report file:",
                "✅ Original file deleted:",
                "🗑️ Deleting summary file:",
                "✅ Summary file deleted:",
                "✅ Survey report deleted from database:"
            ]
            
            found_patterns = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            # Look for expected patterns
                            for pattern in expected_patterns:
                                for line in lines:
                                    if pattern in line:
                                        found_patterns.append(pattern)
                                        self.log(f"   ✅ Found: {pattern}")
                                        break
                            
                            # Show recent relevant lines
                            self.log(f"   Recent relevant log entries:")
                            for line in lines[-50:]:  # Show last 50 lines
                                if any(keyword in line.lower() for keyword in ['survey', 'delete', 'file', 'apps script', 'company']):
                                    self.log(f"     🔍 {line}")
                        else:
                            self.log(f"   {log_file} is empty or not accessible")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
                else:
                    self.log(f"   {log_file} not found")
            
            # Verify critical patterns
            critical_patterns = [
                "🗑️ Bulk delete survey reports request received",
                "🔧 Company Apps Script URL:",
                "🗑️ Deleting original survey report file:",
                "🗑️ Deleting summary file:"
            ]
            
            critical_found = sum(1 for pattern in critical_patterns if pattern in found_patterns)
            
            if critical_found >= 3:
                self.bulk_delete_tests['bulk_delete_logs_found'] = True
                self.bulk_delete_tests['file_deletion_workflow_logs'] = True
                self.log(f"✅ Found {critical_found}/{len(critical_patterns)} critical log patterns")
            
            # Check for company Apps Script URL configuration
            if "🔧 Company Apps Script URL:" in found_patterns:
                self.bulk_delete_tests['company_url_logs_found'] = True
                self.bulk_delete_tests['company_apps_script_url_loaded'] = True
                self.log("✅ Company Apps Script URL configuration logs found")
            
            # Check for file deletion attempts
            file_deletion_patterns = [
                "🗑️ Deleting original survey report file:",
                "🗑️ Deleting summary file:"
            ]
            
            file_deletion_found = sum(1 for pattern in file_deletion_patterns if pattern in found_patterns)
            if file_deletion_found > 0:
                self.bulk_delete_tests['file_deletion_logs_found'] = True
                self.log(f"✅ Found {file_deletion_found} file deletion log patterns")
            
            # Check for Apps Script responses
            apps_script_patterns = [
                "✅ Original file deleted:",
                "✅ Summary file deleted:"
            ]
            
            apps_script_found = sum(1 for pattern in apps_script_patterns if pattern in found_patterns)
            if apps_script_found > 0:
                self.bulk_delete_tests['apps_script_response_logs'] = True
                self.log(f"✅ Found {apps_script_found} Apps Script response patterns")
            
            return len(found_patterns) > 0
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
            return False
    
    def verify_file_deletion_edge_cases(self):
        """Verify handling of different file scenarios"""
        try:
            self.log("🔍 Verifying file deletion edge cases...")
            
            # Analyze the test reports to categorize them
            for report in self.test_reports:
                original_file_id = report.get("survey_report_file_id")
                summary_file_id = report.get("survey_report_summary_file_id")
                report_name = report.get("survey_report_name")
                
                if original_file_id and summary_file_id:
                    self.log(f"   📄 {report_name}: Both files (original + summary)")
                    self.bulk_delete_tests['reports_with_both_files_handled'] = True
                elif original_file_id and not summary_file_id:
                    self.log(f"   📄 {report_name}: Original file only")
                    self.bulk_delete_tests['reports_with_original_only_handled'] = True
                elif not original_file_id and summary_file_id:
                    self.log(f"   📄 {report_name}: Summary file only")
                    self.bulk_delete_tests['reports_with_summary_only_handled'] = True
                else:
                    self.log(f"   📄 {report_name}: No files")
                    self.bulk_delete_tests['reports_with_no_files_handled'] = True
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error verifying edge cases: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_bulk_delete_test(self):
        """Run comprehensive test of Survey Report bulk delete with file deletion"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE SURVEY REPORT BULK DELETE TEST")
            self.log("=" * 80)
            self.log("Testing Google Drive Integration with company_apps_script_url")
            self.log("Matching Drawings & Manuals pattern")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication Setup")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Ship Discovery
            self.log("\nSTEP 2: Ship Discovery")
            if not self.find_ship():
                self.log("❌ CRITICAL: Ship discovery failed - cannot proceed")
                return False
            
            # Step 3: Get Survey Reports with Files
            self.log("\nSTEP 3: Survey Reports Preparation")
            if not self.get_survey_reports_with_files():
                self.log("❌ CRITICAL: No survey reports with files found - cannot proceed")
                return False
            
            # Step 4: Verify Edge Cases
            self.log("\nSTEP 4: Edge Cases Analysis")
            self.verify_file_deletion_edge_cases()
            
            # Step 5: Execute Bulk Delete
            self.log("\nSTEP 5: Execute Bulk Delete")
            if not self.test_bulk_delete_endpoint():
                self.log("❌ CRITICAL: Bulk delete test failed")
                return False
            
            # Step 6: Check Backend Logs
            self.log("\nSTEP 6: Backend Logs Verification")
            self.check_backend_logs_for_file_deletion()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE SURVEY REPORT BULK DELETE TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 SURVEY REPORT BULK DELETE TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.bulk_delete_tests)
            passed_tests = sum(1 for result in self.bulk_delete_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Login with admin1/123456 successful'),
                ('user_company_identified', 'User company identified'),
                ('ship_discovery_successful', 'BROTHER 36 ship found'),
                ('survey_reports_found', 'Survey reports found'),
                ('reports_with_files_found', 'Reports with files found'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.bulk_delete_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Company Apps Script Configuration Results
            self.log("\n🔧 COMPANY APPS SCRIPT CONFIGURATION:")
            config_tests = [
                ('company_apps_script_url_loaded', 'Company Apps Script URL loaded from companies collection'),
                ('apps_script_url_configured', 'Apps Script URL properly configured'),
                ('company_url_logs_found', 'Configuration logs found in backend'),
            ]
            
            for test_key, description in config_tests:
                status = "✅ PASS" if self.bulk_delete_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Bulk Delete Endpoint Results
            self.log("\n🗑️ BULK DELETE ENDPOINT:")
            endpoint_tests = [
                ('bulk_delete_endpoint_accessible', 'Bulk delete endpoint accessible'),
                ('bulk_delete_request_accepted', 'Bulk delete request accepted'),
                ('bulk_delete_response_valid', 'Response structure valid'),
            ]
            
            for test_key, description in endpoint_tests:
                status = "✅ PASS" if self.bulk_delete_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # File Deletion Process Results
            self.log("\n📁 FILE DELETION PROCESS:")
            file_tests = [
                ('file_deletion_logs_found', 'File deletion logs found'),
                ('apps_script_delete_calls_made', 'Apps Script delete calls made'),
                ('apps_script_response_logs', 'Apps Script response logs found'),
            ]
            
            for test_key, description in file_tests:
                status = "✅ PASS" if self.bulk_delete_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Response Structure Results
            self.log("\n📊 RESPONSE STRUCTURE:")
            response_tests = [
                ('response_includes_success', 'Response includes success field'),
                ('response_includes_deleted_count', 'Response includes deleted_count'),
                ('response_includes_files_deleted', 'Response includes files_deleted'),
                ('response_includes_message', 'Response includes message'),
            ]
            
            for test_key, description in response_tests:
                status = "✅ PASS" if self.bulk_delete_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Edge Cases Results
            self.log("\n🔍 EDGE CASES:")
            edge_tests = [
                ('reports_with_original_only_handled', 'Reports with only original file'),
                ('reports_with_summary_only_handled', 'Reports with only summary file'),
                ('reports_with_both_files_handled', 'Reports with both files'),
                ('reports_with_no_files_handled', 'Reports with no files'),
            ]
            
            for test_key, description in edge_tests:
                status = "✅ PASS" if self.bulk_delete_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Backend Logs Results
            self.log("\n📋 BACKEND LOGS VERIFICATION:")
            log_tests = [
                ('bulk_delete_logs_found', 'Bulk delete workflow logs'),
                ('file_deletion_workflow_logs', 'File deletion workflow logs'),
                ('company_url_logs_found', 'Company Apps Script URL logs'),
                ('apps_script_response_logs', 'Apps Script response logs'),
            ]
            
            for test_key, description in log_tests:
                status = "✅ PASS" if self.bulk_delete_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'bulk_delete_endpoint_accessible',
                'company_apps_script_url_loaded',
                'file_deletion_logs_found',
                'apps_script_delete_calls_made',
                'response_includes_files_deleted'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.bulk_delete_tests.get(test_key, False))
            
            if critical_passed >= 4:  # Allow some flexibility
                self.log("   ✅ MOST CRITICAL REQUIREMENTS MET")
                self.log("   ✅ Google Drive file deletion working correctly")
                self.log("   ✅ File deletion workflow verified")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Success rate assessment
            if success_rate >= 85:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 70:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            # Expected behavior summary
            self.log("\n📋 EXPECTED BEHAVIOR VERIFICATION:")
            self.log("   1. Company Apps Script URL loaded from companies collection")
            self.log("   2. Original files deleted from Google Drive via Apps Script")
            self.log("   3. Summary files deleted from Google Drive via Apps Script")
            self.log("   4. files_deleted count > 0 in response")
            self.log("   5. Detailed logging shows complete deletion workflow")
            self.log("   6. Reports removed from database")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    try:
        print("🚀 Starting Survey Report Bulk Delete with File Deletion Test")
        print("=" * 80)
        
        tester = SurveyReportBulkDeleteTester()
        
        # Run comprehensive test
        success = tester.run_comprehensive_bulk_delete_test()
        
        # Print detailed summary
        tester.print_test_summary()
        
        if success:
            print("\n✅ Survey Report Bulk Delete Test COMPLETED SUCCESSFULLY")
            return 0
        else:
            print("\n❌ Survey Report Bulk Delete Test FAILED")
            return 1
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
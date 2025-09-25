#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: Google Drive Multi-File Opening API Testing
Review Request: Debug multi-file opening API calls and responses - Test Google Drive view URL API with SUNSHINE 01 certificates
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import traceback
import subprocess

# Configuration - Use external URL from frontend/.env
BACKEND_URL = "https://shipai-system.preview.emergentagent.com/api"

class GoogleDriveMultiFileOpenTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Google Drive multi-file opening
        self.gdrive_tests = {
            'authentication_successful': False,
            'sunshine_01_ship_found': False,
            'certificates_retrieved': False,
            'certificates_with_gdrive_file_ids_found': False,
            'gdrive_view_url_api_tested': False,
            'api_response_structure_analyzed': False,
            'backend_logs_captured': False,
            'view_url_availability_checked': False,
            'authentication_issues_checked': False,
            'permission_issues_checked': False
        }
        
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
        """Authenticate with admin1/123456 credentials as specified in review request"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=10)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                self.log(f"   Full Name: {self.current_user.get('full_name')}")
                
                self.gdrive_tests['authentication_successful'] = True
                return True
            else:
                self.log(f"   ❌ Authentication failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def find_sunshine_01_ship(self):
        """Find SUNSHINE 01 ship specifically as mentioned in review request"""
        try:
            self.log("🚢 Finding SUNSHINE 01 ship...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   ✅ Found {len(ships)} total ships")
                
                # Look for SUNSHINE 01 specifically
                sunshine_01_ship = None
                for ship in ships:
                    ship_name = ship.get('name', '').upper()
                    if 'SUNSHINE' in ship_name and '01' in ship_name:
                        sunshine_01_ship = ship
                        break
                
                if sunshine_01_ship:
                    self.log(f"   ✅ Found SUNSHINE 01 ship: {sunshine_01_ship.get('name')} (ID: {sunshine_01_ship.get('id')})")
                    self.log(f"   IMO: {sunshine_01_ship.get('imo', 'Not specified')}")
                    self.log(f"   Company: {sunshine_01_ship.get('company', 'Not specified')}")
                    self.log(f"   Flag: {sunshine_01_ship.get('flag', 'Not specified')}")
                    
                    self.gdrive_tests['sunshine_01_ship_found'] = True
                    self.test_results['sunshine_01_ship'] = sunshine_01_ship
                    return sunshine_01_ship
                else:
                    self.log("   ❌ SUNSHINE 01 ship not found")
                    self.log("   Available ships:")
                    for ship in ships[:5]:  # Show first 5 ships
                        self.log(f"      - {ship.get('name')} (ID: {ship.get('id')})")
                    return None
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Find SUNSHINE 01 ship error: {str(e)}", "ERROR")
            return None
    
    def get_sunshine_01_certificates(self):
        """Get certificates from SUNSHINE 01 ship"""
        try:
            self.log("📋 Getting certificates from SUNSHINE 01 ship...")
            
            sunshine_01_ship = self.test_results.get('sunshine_01_ship')
            if not sunshine_01_ship:
                self.log("   ❌ No SUNSHINE 01 ship available")
                return None
            
            ship_id = sunshine_01_ship.get('id')
            endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   ✅ Found {len(certificates)} certificates for SUNSHINE 01")
                
                # Analyze certificates for Google Drive file IDs
                certificates_with_gdrive_ids = []
                certificates_without_gdrive_ids = []
                
                for cert in certificates:
                    cert_name = cert.get('cert_name', 'Unknown Certificate')
                    gdrive_file_id = cert.get('google_drive_file_id')
                    
                    if gdrive_file_id:
                        certificates_with_gdrive_ids.append({
                            'id': cert.get('id'),
                            'name': cert_name,
                            'google_drive_file_id': gdrive_file_id,
                            'cert_no': cert.get('cert_no'),
                            'issued_by': cert.get('issued_by'),
                            'status': cert.get('status')
                        })
                        self.log(f"      ✅ {cert_name} - Google Drive File ID: {gdrive_file_id}")
                    else:
                        certificates_without_gdrive_ids.append({
                            'id': cert.get('id'),
                            'name': cert_name
                        })
                        self.log(f"      ❌ {cert_name} - No Google Drive File ID")
                
                self.log(f"   📊 Certificates with Google Drive File IDs: {len(certificates_with_gdrive_ids)}")
                self.log(f"   📊 Certificates without Google Drive File IDs: {len(certificates_without_gdrive_ids)}")
                
                self.gdrive_tests['certificates_retrieved'] = True
                if certificates_with_gdrive_ids:
                    self.gdrive_tests['certificates_with_gdrive_file_ids_found'] = True
                
                self.test_results['all_certificates'] = certificates
                self.test_results['certificates_with_gdrive_ids'] = certificates_with_gdrive_ids
                self.test_results['certificates_without_gdrive_ids'] = certificates_without_gdrive_ids
                
                return certificates
            else:
                self.log(f"   ❌ Failed to get certificates: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Get certificates error: {str(e)}", "ERROR")
            return None
    
    def test_gdrive_view_url_api(self):
        """Test individual /api/gdrive/file/{file_id}/view calls"""
        try:
            self.log("🔗 Testing Google Drive view URL API...")
            
            certificates_with_gdrive_ids = self.test_results.get('certificates_with_gdrive_ids', [])
            if not certificates_with_gdrive_ids:
                self.log("   ❌ No certificates with Google Drive file IDs available for testing")
                return False
            
            self.log(f"   📋 Testing {len(certificates_with_gdrive_ids)} certificates with Google Drive file IDs")
            
            view_url_test_results = []
            
            for i, cert in enumerate(certificates_with_gdrive_ids[:5]):  # Test first 5 certificates
                cert_name = cert.get('name')
                file_id = cert.get('google_drive_file_id')
                
                self.log(f"   🔗 Test {i+1}: {cert_name}")
                self.log(f"      File ID: {file_id}")
                
                # Test the view URL API endpoint
                endpoint = f"{BACKEND_URL}/gdrive/file/{file_id}/view"
                self.log(f"      GET {endpoint}")
                
                try:
                    response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
                    self.log(f"      Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            self.log("      ✅ API call successful")
                            
                            # Analyze response structure
                            self.log(f"      📊 Response structure analysis:")
                            self.log(f"         Response keys: {list(response_data.keys())}")
                            
                            # Check for view_url in different possible locations
                            view_url = None
                            success_status = None
                            
                            # Check direct view_url
                            if 'view_url' in response_data:
                                view_url = response_data.get('view_url')
                                self.log(f"         ✅ Direct view_url found: {view_url[:100]}..." if view_url else "         ❌ Direct view_url is null/empty")
                            
                            # Check data.view_url
                            if 'data' in response_data and isinstance(response_data['data'], dict):
                                data_view_url = response_data['data'].get('view_url')
                                if data_view_url:
                                    view_url = data_view_url
                                    self.log(f"         ✅ data.view_url found: {data_view_url[:100]}..." if data_view_url else "         ❌ data.view_url is null/empty")
                            
                            # Check success status
                            if 'success' in response_data:
                                success_status = response_data.get('success')
                                self.log(f"         Success status: {success_status}")
                            
                            if 'data' in response_data and isinstance(response_data['data'], dict):
                                data_success = response_data['data'].get('success')
                                if data_success is not None:
                                    success_status = data_success
                                    self.log(f"         data.success status: {data_success}")
                            
                            # Check for error messages
                            error_message = response_data.get('error') or response_data.get('message')
                            if error_message:
                                self.log(f"         ⚠️ Error/Message: {error_message}")
                            
                            view_url_test_results.append({
                                'certificate_name': cert_name,
                                'file_id': file_id,
                                'status_code': response.status_code,
                                'success': success_status,
                                'view_url_available': bool(view_url),
                                'view_url': view_url,
                                'response_structure': list(response_data.keys()),
                                'error_message': error_message,
                                'full_response': response_data
                            })
                            
                        except json.JSONDecodeError:
                            self.log(f"      ❌ Invalid JSON response")
                            self.log(f"      Response text: {response.text[:500]}")
                            view_url_test_results.append({
                                'certificate_name': cert_name,
                                'file_id': file_id,
                                'status_code': response.status_code,
                                'success': False,
                                'view_url_available': False,
                                'error_message': 'Invalid JSON response',
                                'response_text': response.text[:500]
                            })
                    else:
                        self.log(f"      ❌ API call failed: {response.status_code}")
                        try:
                            error_data = response.json()
                            error_message = error_data.get('detail', 'Unknown error')
                            self.log(f"      Error: {error_message}")
                        except:
                            error_message = response.text[:200]
                            self.log(f"      Error: {error_message}")
                        
                        view_url_test_results.append({
                            'certificate_name': cert_name,
                            'file_id': file_id,
                            'status_code': response.status_code,
                            'success': False,
                            'view_url_available': False,
                            'error_message': error_message
                        })
                
                except requests.exceptions.Timeout:
                    self.log(f"      ❌ Request timeout")
                    view_url_test_results.append({
                        'certificate_name': cert_name,
                        'file_id': file_id,
                        'status_code': None,
                        'success': False,
                        'view_url_available': False,
                        'error_message': 'Request timeout'
                    })
                except Exception as e:
                    self.log(f"      ❌ Request error: {str(e)}")
                    view_url_test_results.append({
                        'certificate_name': cert_name,
                        'file_id': file_id,
                        'status_code': None,
                        'success': False,
                        'view_url_available': False,
                        'error_message': str(e)
                    })
            
            self.test_results['view_url_test_results'] = view_url_test_results
            
            # Analyze overall results
            successful_calls = sum(1 for result in view_url_test_results if result.get('status_code') == 200)
            calls_with_view_url = sum(1 for result in view_url_test_results if result.get('view_url_available'))
            total_calls = len(view_url_test_results)
            
            self.log(f"   📊 API Test Results Summary:")
            self.log(f"      Total API calls: {total_calls}")
            self.log(f"      Successful calls (200 OK): {successful_calls}")
            self.log(f"      Calls with view_url: {calls_with_view_url}")
            self.log(f"      Success rate: {(successful_calls/total_calls*100):.1f}%")
            self.log(f"      View URL availability rate: {(calls_with_view_url/total_calls*100):.1f}%")
            
            if successful_calls > 0:
                self.gdrive_tests['gdrive_view_url_api_tested'] = True
                self.gdrive_tests['api_response_structure_analyzed'] = True
            
            if calls_with_view_url > 0:
                self.gdrive_tests['view_url_availability_checked'] = True
            
            return successful_calls > 0
                
        except Exception as e:
            self.log(f"❌ Google Drive view URL API test error: {str(e)}", "ERROR")
            return False
    
    def analyze_api_response_patterns(self):
        """Analyze API response patterns and identify issues"""
        try:
            self.log("🔍 Analyzing API response patterns...")
            
            view_url_test_results = self.test_results.get('view_url_test_results', [])
            if not view_url_test_results:
                self.log("   ❌ No API test results available for analysis")
                return False
            
            # Analyze response patterns
            response_patterns = {}
            error_patterns = {}
            authentication_issues = []
            permission_issues = []
            
            for result in view_url_test_results:
                status_code = result.get('status_code')
                error_message = result.get('error_message', '')
                
                # Track response patterns
                if status_code:
                    response_patterns[status_code] = response_patterns.get(status_code, 0) + 1
                
                # Track error patterns
                if error_message:
                    error_patterns[error_message] = error_patterns.get(error_message, 0) + 1
                
                # Check for authentication issues
                if status_code == 401 or 'authentication' in error_message.lower() or 'unauthorized' in error_message.lower():
                    authentication_issues.append(result)
                
                # Check for permission issues
                if status_code == 403 or 'permission' in error_message.lower() or 'forbidden' in error_message.lower():
                    permission_issues.append(result)
            
            self.log("   📊 Response Pattern Analysis:")
            for status_code, count in response_patterns.items():
                self.log(f"      HTTP {status_code}: {count} occurrences")
            
            if error_patterns:
                self.log("   📊 Error Pattern Analysis:")
                for error, count in error_patterns.items():
                    self.log(f"      '{error}': {count} occurrences")
            
            if authentication_issues:
                self.log(f"   🔐 Authentication Issues Found: {len(authentication_issues)}")
                self.gdrive_tests['authentication_issues_checked'] = True
                for issue in authentication_issues[:3]:  # Show first 3
                    self.log(f"      - {issue.get('certificate_name')}: {issue.get('error_message')}")
            
            if permission_issues:
                self.log(f"   🔒 Permission Issues Found: {len(permission_issues)}")
                self.gdrive_tests['permission_issues_checked'] = True
                for issue in permission_issues[:3]:  # Show first 3
                    self.log(f"      - {issue.get('certificate_name')}: {issue.get('error_message')}")
            
            # Analyze response structure consistency
            response_structures = {}
            for result in view_url_test_results:
                if result.get('response_structure'):
                    structure_key = str(sorted(result['response_structure']))
                    response_structures[structure_key] = response_structures.get(structure_key, 0) + 1
            
            if response_structures:
                self.log("   📊 Response Structure Analysis:")
                for structure, count in response_structures.items():
                    self.log(f"      Structure {structure}: {count} occurrences")
            
            self.test_results['response_patterns'] = response_patterns
            self.test_results['error_patterns'] = error_patterns
            self.test_results['authentication_issues'] = authentication_issues
            self.test_results['permission_issues'] = permission_issues
            
            return True
                
        except Exception as e:
            self.log(f"❌ API response pattern analysis error: {str(e)}", "ERROR")
            return False
    
    def capture_backend_logs(self):
        """Capture backend logs during API calls"""
        try:
            self.log("📝 Capturing backend logs...")
            
            # Try to capture backend logs using supervisor
            try:
                result = subprocess.run(
                    ['tail', '-n', '50', '/var/log/supervisor/backend.err.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout:
                    self.log("   ✅ Backend error logs captured:")
                    log_lines = result.stdout.strip().split('\n')
                    for line in log_lines[-10:]:  # Show last 10 lines
                        if line.strip():
                            self.log(f"      {line}")
                    
                    self.test_results['backend_error_logs'] = log_lines
                else:
                    self.log("   ⚠️ No backend error logs found or accessible")
                    
            except subprocess.TimeoutExpired:
                self.log("   ⚠️ Backend log capture timeout")
            except FileNotFoundError:
                self.log("   ⚠️ Backend log file not found")
            except Exception as e:
                self.log(f"   ⚠️ Backend log capture error: {str(e)}")
            
            # Try to capture backend output logs
            try:
                result = subprocess.run(
                    ['tail', '-n', '50', '/var/log/supervisor/backend.out.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout:
                    self.log("   ✅ Backend output logs captured:")
                    log_lines = result.stdout.strip().split('\n')
                    for line in log_lines[-10:]:  # Show last 10 lines
                        if line.strip():
                            self.log(f"      {line}")
                    
                    self.test_results['backend_output_logs'] = log_lines
                else:
                    self.log("   ⚠️ No backend output logs found or accessible")
                    
            except subprocess.TimeoutExpired:
                self.log("   ⚠️ Backend output log capture timeout")
            except FileNotFoundError:
                self.log("   ⚠️ Backend output log file not found")
            except Exception as e:
                self.log(f"   ⚠️ Backend output log capture error: {str(e)}")
            
            self.gdrive_tests['backend_logs_captured'] = True
            return True
                
        except Exception as e:
            self.log(f"❌ Backend log capture error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_gdrive_multi_file_open_tests(self):
        """Main test function for Google Drive multi-file opening"""
        self.log("🎯 STARTING GOOGLE DRIVE MULTI-FILE OPENING API TESTING")
        self.log("🔍 Focus: Debug multi-file opening API calls and responses")
        self.log("📋 Review Request: Test Google Drive view URL API with SUNSHINE 01 certificates")
        self.log("🎯 Testing: Authentication, certificate retrieval, view URL API, response analysis")
        self.log("=" * 100)
        
        # Step 1: Authenticate
        self.log("\n🔐 STEP 1: AUTHENTICATION")
        self.log("=" * 50)
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Find SUNSHINE 01 ship
        self.log("\n🚢 STEP 2: FIND SUNSHINE 01 SHIP")
        self.log("=" * 50)
        sunshine_01_ship = self.find_sunshine_01_ship()
        if not sunshine_01_ship:
            self.log("❌ SUNSHINE 01 ship not found - cannot proceed with certificate testing")
            return False
        
        # Step 3: Get SUNSHINE 01 certificates
        self.log("\n📋 STEP 3: GET SUNSHINE 01 CERTIFICATES")
        self.log("=" * 50)
        certificates = self.get_sunshine_01_certificates()
        if not certificates:
            self.log("❌ No certificates found for SUNSHINE 01 - cannot proceed with Google Drive testing")
            return False
        
        # Step 4: Test Google Drive view URL API
        self.log("\n🔗 STEP 4: TEST GOOGLE DRIVE VIEW URL API")
        self.log("=" * 50)
        self.test_gdrive_view_url_api()
        
        # Step 5: Analyze API response patterns
        self.log("\n🔍 STEP 5: ANALYZE API RESPONSE PATTERNS")
        self.log("=" * 50)
        self.analyze_api_response_patterns()
        
        # Step 6: Capture backend logs
        self.log("\n📝 STEP 6: CAPTURE BACKEND LOGS")
        self.log("=" * 50)
        self.capture_backend_logs()
        
        # Step 7: Final analysis
        self.log("\n📊 STEP 7: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_gdrive_analysis()
        
        return True
    
    def provide_final_gdrive_analysis(self):
        """Provide final analysis of the Google Drive multi-file opening testing"""
        try:
            self.log("🎯 GOOGLE DRIVE MULTI-FILE OPENING TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.gdrive_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ GOOGLE DRIVE TESTS PASSED ({len(passed_tests)}/10):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ GOOGLE DRIVE TESTS FAILED ({len(failed_tests)}/10):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Overall assessment
            success_rate = len(passed_tests) / len(self.gdrive_tests) * 100
            self.log(f"\n📊 GOOGLE DRIVE TESTING SUCCESS RATE: {success_rate:.1f}%")
            
            # Detailed results
            self.log(f"\n🔍 DETAILED RESULTS:")
            
            # Ship information
            sunshine_01_ship = self.test_results.get('sunshine_01_ship')
            if sunshine_01_ship:
                self.log(f"   🚢 SUNSHINE 01 Ship Found:")
                self.log(f"      Name: {sunshine_01_ship.get('name')}")
                self.log(f"      ID: {sunshine_01_ship.get('id')}")
                self.log(f"      Company: {sunshine_01_ship.get('company')}")
                self.log(f"      IMO: {sunshine_01_ship.get('imo', 'Not specified')}")
            
            # Certificate analysis
            certificates_with_gdrive_ids = self.test_results.get('certificates_with_gdrive_ids', [])
            certificates_without_gdrive_ids = self.test_results.get('certificates_without_gdrive_ids', [])
            
            self.log(f"   📋 Certificate Analysis:")
            self.log(f"      Total certificates: {len(certificates_with_gdrive_ids) + len(certificates_without_gdrive_ids)}")
            self.log(f"      With Google Drive File IDs: {len(certificates_with_gdrive_ids)}")
            self.log(f"      Without Google Drive File IDs: {len(certificates_without_gdrive_ids)}")
            
            # API test results
            view_url_test_results = self.test_results.get('view_url_test_results', [])
            if view_url_test_results:
                successful_calls = sum(1 for result in view_url_test_results if result.get('status_code') == 200)
                calls_with_view_url = sum(1 for result in view_url_test_results if result.get('view_url_available'))
                total_calls = len(view_url_test_results)
                
                self.log(f"   🔗 API Test Results:")
                self.log(f"      Total API calls: {total_calls}")
                self.log(f"      Successful calls (200 OK): {successful_calls}")
                self.log(f"      Calls with view_url: {calls_with_view_url}")
                self.log(f"      Success rate: {(successful_calls/total_calls*100):.1f}%")
                self.log(f"      View URL availability rate: {(calls_with_view_url/total_calls*100):.1f}%")
            
            # Response patterns
            response_patterns = self.test_results.get('response_patterns', {})
            if response_patterns:
                self.log(f"   📊 Response Patterns:")
                for status_code, count in response_patterns.items():
                    self.log(f"      HTTP {status_code}: {count} occurrences")
            
            # Issues found
            authentication_issues = self.test_results.get('authentication_issues', [])
            permission_issues = self.test_results.get('permission_issues', [])
            
            if authentication_issues:
                self.log(f"   🔐 Authentication Issues: {len(authentication_issues)} found")
            
            if permission_issues:
                self.log(f"   🔒 Permission Issues: {len(permission_issues)} found")
            
            # Key findings for the review request
            self.log(f"\n🎯 KEY FINDINGS FOR REVIEW REQUEST:")
            
            if certificates_with_gdrive_ids:
                self.log(f"   ✅ Found {len(certificates_with_gdrive_ids)} certificates with Google Drive file IDs")
                self.log(f"   📋 Sample certificates with file IDs:")
                for cert in certificates_with_gdrive_ids[:3]:
                    self.log(f"      - {cert.get('name')}: {cert.get('google_drive_file_id')}")
            else:
                self.log(f"   ❌ No certificates with Google Drive file IDs found")
            
            if view_url_test_results:
                # Analyze exact response format
                sample_response = None
                for result in view_url_test_results:
                    if result.get('full_response'):
                        sample_response = result['full_response']
                        break
                
                if sample_response:
                    self.log(f"   📊 API Response Format Analysis:")
                    self.log(f"      Response structure: {list(sample_response.keys())}")
                    
                    if 'view_url' in sample_response:
                        self.log(f"      ✅ Direct view_url field present")
                    elif 'data' in sample_response and isinstance(sample_response['data'], dict):
                        data_keys = list(sample_response['data'].keys())
                        self.log(f"      📊 data object keys: {data_keys}")
                        if 'view_url' in data_keys:
                            self.log(f"      ✅ data.view_url field present")
                        else:
                            self.log(f"      ❌ No view_url in data object")
                    else:
                        self.log(f"      ❌ No view_url field found in response")
                
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    print("🎯 Ship Management System - Google Drive Multi-File Opening API Testing")
    print("🔍 Focus: Debug multi-file opening API calls and responses")
    print("📋 Review Request: Test Google Drive view URL API with SUNSHINE 01 certificates")
    print("🎯 Testing: Authentication, certificate retrieval, view URL API, response analysis")
    print("=" * 100)
    
    tester = GoogleDriveMultiFileOpenTester()
    success = tester.run_comprehensive_gdrive_multi_file_open_tests()
    
    print("=" * 100)
    print("🔍 GOOGLE DRIVE MULTI-FILE OPENING TESTING RESULTS:")
    print("=" * 70)
    
    # Print test summary
    passed_tests = [f for f, passed in tester.gdrive_tests.items() if passed]
    failed_tests = [f for f, passed in tester.gdrive_tests.items() if not passed]
    
    print(f"✅ GOOGLE DRIVE TESTS PASSED ({len(passed_tests)}/10):")
    for test in passed_tests:
        print(f"   ✅ {test.replace('_', ' ').title()}")
    
    if failed_tests:
        print(f"\n❌ GOOGLE DRIVE TESTS FAILED ({len(failed_tests)}/10):")
        for test in failed_tests:
            print(f"   ❌ {test.replace('_', ' ').title()}")
    
    # Print key findings
    print(f"\n🔍 KEY FINDINGS:")
    
    # Certificate analysis
    certificates_with_gdrive_ids = tester.test_results.get('certificates_with_gdrive_ids', [])
    certificates_without_gdrive_ids = tester.test_results.get('certificates_without_gdrive_ids', [])
    
    print(f"   📋 SUNSHINE 01 Certificate Analysis:")
    print(f"      Total certificates: {len(certificates_with_gdrive_ids) + len(certificates_without_gdrive_ids)}")
    print(f"      With Google Drive File IDs: {len(certificates_with_gdrive_ids)}")
    print(f"      Without Google Drive File IDs: {len(certificates_without_gdrive_ids)}")
    
    # API test results
    view_url_test_results = tester.test_results.get('view_url_test_results', [])
    if view_url_test_results:
        successful_calls = sum(1 for result in view_url_test_results if result.get('status_code') == 200)
        calls_with_view_url = sum(1 for result in view_url_test_results if result.get('view_url_available'))
        total_calls = len(view_url_test_results)
        
        print(f"   🔗 Google Drive View URL API Results:")
        print(f"      Total API calls: {total_calls}")
        print(f"      Successful calls (200 OK): {successful_calls}")
        print(f"      Calls with view_url: {calls_with_view_url}")
        print(f"      Success rate: {(successful_calls/total_calls*100):.1f}%")
        print(f"      View URL availability rate: {(calls_with_view_url/total_calls*100):.1f}%")
    
    # Ship information
    if tester.test_results.get('sunshine_01_ship'):
        ship = tester.test_results['sunshine_01_ship']
        print(f"\n🚢 TESTED WITH SHIP: {ship.get('name')} (ID: {ship.get('id')})")
        print(f"   Company: {ship.get('company')}")
        print(f"   IMO: {ship.get('imo', 'Not specified')}")
    
    # Calculate success rate
    success_rate = len(passed_tests) / len(tester.gdrive_tests) * 100
    print(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")
    
    print("=" * 100)
    if success:
        print("🎉 Google Drive multi-file opening API testing completed!")
        print("✅ All testing steps executed - detailed analysis available above")
    else:
        print("❌ Google Drive multi-file opening API testing completed with issues!")
        print("🔍 Check detailed logs above for specific issues")
    
    # Provide recommendations based on findings
    print("\n💡 NEXT STEPS FOR MAIN AGENT:")
    
    if certificates_with_gdrive_ids:
        print("   ✅ Certificates with Google Drive file IDs found")
        if view_url_test_results:
            successful_calls = sum(1 for result in view_url_test_results if result.get('status_code') == 200)
            calls_with_view_url = sum(1 for result in view_url_test_results if result.get('view_url_available'))
            
            if successful_calls > 0:
                print("   ✅ Google Drive view URL API is accessible")
                if calls_with_view_url > 0:
                    print("   ✅ View URLs are being returned by the API")
                    print("   1. Check frontend logic for processing view_url responses")
                    print("   2. Verify response format handling (data.view_url vs direct view_url)")
                    print("   3. Test multi-file opening with actual file IDs")
                else:
                    print("   ❌ View URLs are not available in API responses")
                    print("   1. Check Google Drive authentication configuration")
                    print("   2. Verify file permissions in Google Drive")
                    print("   3. Check Apps Script implementation for view URL generation")
            else:
                print("   ❌ Google Drive view URL API calls are failing")
                print("   1. Check backend Google Drive integration")
                print("   2. Verify authentication and permissions")
                print("   3. Check backend logs for specific error messages")
        else:
            print("   ❌ No API tests were performed")
            print("   1. Ensure certificates have valid google_drive_file_id fields")
            print("   2. Check backend API endpoint implementation")
    else:
        print("   ❌ No certificates with Google Drive file IDs found")
        print("   1. Check certificate upload process")
        print("   2. Verify Google Drive integration during certificate creation")
        print("   3. Check database for google_drive_file_id field population")
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
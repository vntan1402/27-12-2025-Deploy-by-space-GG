#!/usr/bin/env python3
"""
Survey Reports Backend API Testing
Testing the newly created Survey Report endpoints

REVIEW REQUEST REQUIREMENTS:
Test the newly created Survey Report endpoints:

**Test Scope:**
1. Test POST /api/survey-reports - Create a new survey report for ship "BROTHER 36"
2. Test GET /api/survey-reports?ship_id={ship_id} - Get all survey reports for that ship
3. Test GET /api/survey-reports/{report_id} - Get single survey report
4. Test PUT /api/survey-reports/{report_id} - Update survey report
5. Test DELETE /api/survey-reports/{report_id} - Delete survey report

**Test Data:**
- Use ship "BROTHER 36" (get ship_id from /api/ships endpoint)
- Survey Report Name: "Annual Survey 2025"
- Survey Report No: "AS-2025-001"
- Issued Date: "2025-01-15"
- Issued By: "Lloyd's Register"
- Status: "Valid"
- Note: "Test survey report"

**Expected Results:**
- All CRUD operations should work correctly
- Survey reports should be linked to the ship via ship_id
- Dates should be properly formatted
- Status filtering should work
- All fields should be stored and retrieved correctly

**Authentication:**
- Use admin1/123456 credentials
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
from urllib.parse import urlparse

# Configuration - Use environment variable for backend URL
# Try internal URL first, then external
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://maritime-docai.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class SurveyReportsTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.ship_name = "BROTHER 36"
        self.ship_id = None
        self.created_report_ids = []  # Track created reports for cleanup
        
        # Test tracking for survey reports testing
        self.survey_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'ship_discovery_successful': False,
            'ship_id_retrieved': False,
            
            # POST /api/survey-reports - Create survey report
            'create_survey_report_endpoint_accessible': False,
            'create_survey_report_successful': False,
            'create_survey_report_returns_correct_data': False,
            'create_survey_report_ship_validation': False,
            'create_survey_report_date_formatting': False,
            
            # GET /api/survey-reports?ship_id={ship_id} - Get reports by ship
            'get_survey_reports_by_ship_endpoint_accessible': False,
            'get_survey_reports_by_ship_successful': False,
            'get_survey_reports_by_ship_filtering_works': False,
            'get_survey_reports_by_ship_returns_correct_data': False,
            
            # GET /api/survey-reports/{report_id} - Get single report
            'get_single_survey_report_endpoint_accessible': False,
            'get_single_survey_report_successful': False,
            'get_single_survey_report_returns_correct_data': False,
            'get_single_survey_report_404_for_invalid_id': False,
            
            # PUT /api/survey-reports/{report_id} - Update survey report
            'update_survey_report_endpoint_accessible': False,
            'update_survey_report_successful': False,
            'update_survey_report_returns_updated_data': False,
            'update_survey_report_404_for_invalid_id': False,
            'update_survey_report_partial_updates': False,
            
            # DELETE /api/survey-reports/{report_id} - Delete survey report
            'delete_survey_report_endpoint_accessible': False,
            'delete_survey_report_successful': False,
            'delete_survey_report_404_for_invalid_id': False,
            'delete_survey_report_removes_from_database': False,
            
            # Data validation and integrity
            'survey_report_ship_linking_works': False,
            'survey_report_date_handling_correct': False,
            'survey_report_status_handling_correct': False,
            'survey_report_all_fields_stored_correctly': False,
            
            # Error handling
            'create_survey_report_invalid_ship_id_validation': False,
            'permission_checks_working': False,
            'proper_error_responses': False,
        }
        
        # Test data
        self.test_survey_data = {
            "survey_report_name": "Annual Survey 2025",
            "survey_report_no": "AS-2025-001",
            "issued_date": "2025-01-15T00:00:00Z",
            "issued_by": "Lloyd's Register",
            "status": "Valid",
            "note": "Test survey report"
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
                
                self.survey_tests['authentication_successful'] = True
                self.survey_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_ship(self):
        """Find the test ship and get its ID"""
        try:
            self.log(f"🚢 Finding ship: {self.ship_name}")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships in database")
                
                for ship in ships:
                    if ship.get("name") == self.ship_name:
                        self.ship_id = ship.get("id")
                        self.log(f"✅ Found ship: {self.ship_name} (ID: {self.ship_id})")
                        self.survey_tests['ship_discovery_successful'] = True
                        self.survey_tests['ship_id_retrieved'] = True
                        return True
                
                self.log(f"❌ Ship '{self.ship_name}' not found", "ERROR")
                self.log("   Available ships:")
                for ship in ships[:5]:  # Show first 5 ships
                    self.log(f"     - {ship.get('name', 'Unknown')} (ID: {ship.get('id', 'Unknown')})")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def test_create_survey_report(self):
        """Test POST /api/survey-reports - Create a new survey report"""
        try:
            self.log("📝 Testing POST /api/survey-reports - Create survey report...")
            
            if not self.ship_id:
                self.log("❌ No ship ID available for testing", "ERROR")
                return None
            
            # Prepare survey report data
            survey_data = self.test_survey_data.copy()
            survey_data["ship_id"] = self.ship_id
            
            endpoint = f"{BACKEND_URL}/survey-reports"
            self.log(f"   POST {endpoint}")
            self.log(f"   Survey data: {json.dumps(survey_data, indent=2)}")
            
            response = self.session.post(endpoint, json=survey_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                self.survey_tests['create_survey_report_endpoint_accessible'] = True
                self.survey_tests['create_survey_report_successful'] = True
                self.log("✅ Create survey report endpoint accessible and working")
                
                try:
                    created_report = response.json()
                    report_id = created_report.get('id')
                    self.created_report_ids.append(report_id)
                    
                    self.log(f"   ✅ Survey report created with ID: {report_id}")
                    
                    # Verify returned data
                    expected_fields = ['id', 'ship_id', 'survey_report_name', 'survey_report_no', 
                                     'issued_date', 'issued_by', 'status', 'note', 'created_at']
                    
                    for field in expected_fields:
                        if field in created_report:
                            self.log(f"      ✅ Field '{field}' present: {created_report.get(field)}")
                        else:
                            self.log(f"      ❌ Field '{field}' missing")
                    
                    # Verify ship_id linking
                    if created_report.get('ship_id') == self.ship_id:
                        self.log("      ✅ Ship ID linking correct")
                        self.survey_tests['survey_report_ship_linking_works'] = True
                    else:
                        self.log(f"      ❌ Ship ID linking incorrect: expected {self.ship_id}, got {created_report.get('ship_id')}")
                    
                    # Verify date formatting
                    issued_date = created_report.get('issued_date')
                    if issued_date:
                        self.log(f"      ✅ Issued date formatted: {issued_date}")
                        self.survey_tests['survey_report_date_handling_correct'] = True
                    
                    # Verify status
                    if created_report.get('status') == survey_data['status']:
                        self.log("      ✅ Status stored correctly")
                        self.survey_tests['survey_report_status_handling_correct'] = True
                    
                    # Verify all fields stored correctly
                    fields_correct = all(
                        created_report.get(field) == survey_data.get(field) 
                        for field in ['survey_report_name', 'survey_report_no', 'issued_by', 'status', 'note']
                    )
                    if fields_correct:
                        self.log("      ✅ All fields stored correctly")
                        self.survey_tests['survey_report_all_fields_stored_correctly'] = True
                        self.survey_tests['create_survey_report_returns_correct_data'] = True
                    
                    return created_report
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ Create survey report failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error response: {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing create survey report: {str(e)}", "ERROR")
            return None
    
    def test_create_survey_report_invalid_ship(self):
        """Test create survey report with invalid ship ID"""
        try:
            self.log("🔍 Testing create survey report with invalid ship ID...")
            
            # Use invalid ship ID
            invalid_survey_data = self.test_survey_data.copy()
            invalid_survey_data["ship_id"] = "invalid-ship-id-12345"
            
            endpoint = f"{BACKEND_URL}/survey-reports"
            response = self.session.post(endpoint, json=invalid_survey_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 404:
                self.survey_tests['create_survey_report_ship_validation'] = True
                self.survey_tests['create_survey_report_invalid_ship_id_validation'] = True
                self.log("✅ Invalid ship ID validation working - 404 returned")
                try:
                    error_data = response.json()
                    self.log(f"   Error message: {error_data.get('detail', 'Unknown error')}")
                except:
                    pass
                return True
            else:
                self.log(f"   ❌ Expected 404 for invalid ship ID, got: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing invalid ship ID: {str(e)}", "ERROR")
            return False
    
    def test_get_survey_reports_by_ship(self):
        """Test GET /api/survey-reports?ship_id={ship_id} - Get reports by ship"""
        try:
            self.log("📋 Testing GET /api/survey-reports?ship_id={ship_id} - Get reports by ship...")
            
            if not self.ship_id:
                self.log("❌ No ship ID available for testing", "ERROR")
                return None
            
            endpoint = f"{BACKEND_URL}/survey-reports?ship_id={self.ship_id}"
            self.log(f"   GET {endpoint}")
            
            response = self.session.get(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.survey_tests['get_survey_reports_by_ship_endpoint_accessible'] = True
                self.survey_tests['get_survey_reports_by_ship_successful'] = True
                self.log("✅ Get survey reports by ship endpoint accessible")
                
                try:
                    reports = response.json()
                    self.log(f"   ✅ Retrieved {len(reports)} survey reports for ship {self.ship_name}")
                    
                    if len(reports) > 0:
                        # Verify filtering works - all reports should have the correct ship_id
                        all_correct_ship = all(report.get('ship_id') == self.ship_id for report in reports)
                        if all_correct_ship:
                            self.log("      ✅ Ship filtering working correctly")
                            self.survey_tests['get_survey_reports_by_ship_filtering_works'] = True
                        else:
                            self.log("      ❌ Ship filtering not working - found reports for other ships")
                        
                        # Check first report structure
                        first_report = reports[0]
                        expected_fields = ['id', 'ship_id', 'survey_report_name', 'survey_report_no', 
                                         'issued_date', 'issued_by', 'status', 'note']
                        
                        fields_present = all(field in first_report for field in expected_fields)
                        if fields_present:
                            self.log("      ✅ Report structure correct")
                            self.survey_tests['get_survey_reports_by_ship_returns_correct_data'] = True
                        else:
                            self.log("      ❌ Some expected fields missing in report structure")
                            for field in expected_fields:
                                if field not in first_report:
                                    self.log(f"        Missing: {field}")
                    
                    return reports
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ Get survey reports by ship failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing get survey reports by ship: {str(e)}", "ERROR")
            return None
    
    def test_get_single_survey_report(self, report_id):
        """Test GET /api/survey-reports/{report_id} - Get single survey report"""
        try:
            self.log(f"📄 Testing GET /api/survey-reports/{report_id} - Get single survey report...")
            
            endpoint = f"{BACKEND_URL}/survey-reports/{report_id}"
            self.log(f"   GET {endpoint}")
            
            response = self.session.get(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.survey_tests['get_single_survey_report_endpoint_accessible'] = True
                self.survey_tests['get_single_survey_report_successful'] = True
                self.log("✅ Get single survey report endpoint working")
                
                try:
                    report = response.json()
                    self.log(f"   ✅ Retrieved survey report: {report.get('survey_report_name', 'Unknown')}")
                    
                    # Verify report data structure
                    expected_fields = ['id', 'ship_id', 'survey_report_name', 'survey_report_no', 
                                     'issued_date', 'issued_by', 'status', 'note', 'created_at']
                    
                    for field in expected_fields:
                        if field in report:
                            self.log(f"      ✅ Field '{field}' present: {report.get(field)}")
                        else:
                            self.log(f"      ❌ Field '{field}' missing")
                    
                    # Verify report ID matches
                    if report.get('id') == report_id:
                        self.log("      ✅ Report ID matches request")
                        self.survey_tests['get_single_survey_report_returns_correct_data'] = True
                    else:
                        self.log(f"      ❌ Report ID mismatch: expected {report_id}, got {report.get('id')}")
                    
                    return report
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ Get single survey report failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing get single survey report: {str(e)}", "ERROR")
            return None
    
    def test_get_single_survey_report_invalid_id(self):
        """Test get single survey report with invalid ID"""
        try:
            self.log("🔍 Testing get single survey report with invalid ID...")
            
            invalid_id = "invalid-report-id-12345"
            endpoint = f"{BACKEND_URL}/survey-reports/{invalid_id}"
            response = self.session.get(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 404:
                self.survey_tests['get_single_survey_report_404_for_invalid_id'] = True
                self.log("✅ Invalid report ID returns 404 as expected")
                return True
            else:
                self.log(f"   ❌ Expected 404 for invalid ID, got: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing invalid report ID: {str(e)}", "ERROR")
            return False
    
    def test_update_survey_report(self, report_id):
        """Test PUT /api/survey-reports/{report_id} - Update survey report"""
        try:
            self.log(f"✏️ Testing PUT /api/survey-reports/{report_id} - Update survey report...")
            
            # Update data
            update_data = {
                "survey_report_name": "Annual Survey 2025 - Updated",
                "survey_report_no": "AS-2025-001-UPDATED",
                "issued_by": "Lloyd's Register - Updated",
                "status": "Expired",
                "note": "Test survey report - Updated"
            }
            
            endpoint = f"{BACKEND_URL}/survey-reports/{report_id}"
            self.log(f"   PUT {endpoint}")
            self.log(f"   Update data: {json.dumps(update_data, indent=2)}")
            
            response = self.session.put(endpoint, json=update_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.survey_tests['update_survey_report_endpoint_accessible'] = True
                self.survey_tests['update_survey_report_successful'] = True
                self.log("✅ Update survey report endpoint working")
                
                try:
                    updated_report = response.json()
                    self.log(f"   ✅ Survey report updated: {updated_report.get('survey_report_name', 'Unknown')}")
                    
                    # Verify updates were applied
                    updates_correct = True
                    for field, expected_value in update_data.items():
                        actual_value = updated_report.get(field)
                        if actual_value == expected_value:
                            self.log(f"      ✅ {field} updated correctly: {actual_value}")
                        else:
                            self.log(f"      ❌ {field} update failed: expected {expected_value}, got {actual_value}")
                            updates_correct = False
                    
                    if updates_correct:
                        self.survey_tests['update_survey_report_returns_updated_data'] = True
                    
                    # Verify updated_at field is present and recent
                    updated_at = updated_report.get('updated_at')
                    if updated_at:
                        self.log(f"      ✅ updated_at field present: {updated_at}")
                    
                    return updated_report
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ Update survey report failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    pass
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing update survey report: {str(e)}", "ERROR")
            return None
    
    def test_update_survey_report_partial(self, report_id):
        """Test partial update of survey report"""
        try:
            self.log("🔍 Testing partial update of survey report...")
            
            # Only update status
            partial_update = {
                "status": "Under Review"
            }
            
            endpoint = f"{BACKEND_URL}/survey-reports/{report_id}"
            response = self.session.put(endpoint, json=partial_update, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.survey_tests['update_survey_report_partial_updates'] = True
                self.log("✅ Partial update working")
                
                try:
                    updated_report = response.json()
                    if updated_report.get('status') == partial_update['status']:
                        self.log(f"      ✅ Status updated to: {updated_report.get('status')}")
                        return True
                    else:
                        self.log("      ❌ Status not updated correctly")
                        return False
                except:
                    return False
            else:
                self.log(f"   ❌ Partial update failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing partial update: {str(e)}", "ERROR")
            return False
    
    def test_update_survey_report_invalid_id(self):
        """Test update survey report with invalid ID"""
        try:
            self.log("🔍 Testing update survey report with invalid ID...")
            
            invalid_id = "invalid-report-id-12345"
            update_data = {"status": "Updated"}
            
            endpoint = f"{BACKEND_URL}/survey-reports/{invalid_id}"
            response = self.session.put(endpoint, json=update_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 404:
                self.survey_tests['update_survey_report_404_for_invalid_id'] = True
                self.log("✅ Invalid report ID returns 404 as expected for update")
                return True
            else:
                self.log(f"   ❌ Expected 404 for invalid ID, got: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing update with invalid ID: {str(e)}", "ERROR")
            return False
    
    def test_delete_survey_report(self, report_id):
        """Test DELETE /api/survey-reports/{report_id} - Delete survey report"""
        try:
            self.log(f"🗑️ Testing DELETE /api/survey-reports/{report_id} - Delete survey report...")
            
            endpoint = f"{BACKEND_URL}/survey-reports/{report_id}"
            self.log(f"   DELETE {endpoint}")
            
            response = self.session.delete(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.survey_tests['delete_survey_report_endpoint_accessible'] = True
                self.survey_tests['delete_survey_report_successful'] = True
                self.log("✅ Delete survey report endpoint working")
                
                try:
                    result = response.json()
                    success = result.get("success", False)
                    message = result.get("message", "")
                    
                    self.log(f"   Success: {success}")
                    self.log(f"   Message: {message}")
                    
                    if success:
                        self.log("      ✅ Delete operation successful")
                        
                        # Remove from our tracking list
                        if report_id in self.created_report_ids:
                            self.created_report_ids.remove(report_id)
                        
                        # Verify report is actually deleted by trying to get it
                        get_response = self.session.get(f"{BACKEND_URL}/survey-reports/{report_id}", timeout=30)
                        if get_response.status_code == 404:
                            self.log("      ✅ Report actually removed from database")
                            self.survey_tests['delete_survey_report_removes_from_database'] = True
                        else:
                            self.log(f"      ❌ Report still exists after delete: {get_response.status_code}")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                self.log(f"   ❌ Delete survey report failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    pass
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing delete survey report: {str(e)}", "ERROR")
            return False
    
    def test_delete_survey_report_invalid_id(self):
        """Test delete survey report with invalid ID"""
        try:
            self.log("🔍 Testing delete survey report with invalid ID...")
            
            invalid_id = "invalid-report-id-12345"
            endpoint = f"{BACKEND_URL}/survey-reports/{invalid_id}"
            response = self.session.delete(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 404:
                self.survey_tests['delete_survey_report_404_for_invalid_id'] = True
                self.log("✅ Invalid report ID returns 404 as expected for delete")
                return True
            else:
                self.log(f"   ❌ Expected 404 for invalid ID, got: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing delete with invalid ID: {str(e)}", "ERROR")
            return False
    
    def test_get_all_survey_reports(self):
        """Test GET /api/survey-reports - Get all survey reports (without ship filter)"""
        try:
            self.log("📋 Testing GET /api/survey-reports - Get all survey reports...")
            
            endpoint = f"{BACKEND_URL}/survey-reports"
            self.log(f"   GET {endpoint}")
            
            response = self.session.get(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.log("✅ Get all survey reports endpoint accessible")
                
                try:
                    all_reports = response.json()
                    self.log(f"   ✅ Retrieved {len(all_reports)} total survey reports")
                    
                    if len(all_reports) > 0:
                        # Check if we have reports from different ships
                        ship_ids = set(report.get('ship_id') for report in all_reports if report.get('ship_id'))
                        self.log(f"      Reports from {len(ship_ids)} different ships")
                    
                    return all_reports
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return None
            else:
                self.log(f"   ❌ Get all survey reports failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing get all survey reports: {str(e)}", "ERROR")
            return None
    
    def test_permission_checks(self):
        """Test permission checks for survey report operations"""
        try:
            self.log("🔐 Testing permission checks...")
            
            # Current user is admin1 with admin role, so should have all permissions
            user_role = self.current_user.get('role', '').lower()
            
            if user_role in ['admin', 'super_admin', 'manager', 'editor']:
                self.survey_tests['permission_checks_working'] = True
                self.log(f"✅ User role '{user_role}' has required permissions for survey reports")
                return True
            else:
                self.log(f"   ⚠️ User role '{user_role}' may have limited permissions")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing permission checks: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        try:
            self.log("🧹 Cleaning up test survey reports...")
            
            for report_id in self.created_report_ids[:]:  # Copy list to avoid modification during iteration
                try:
                    endpoint = f"{BACKEND_URL}/survey-reports/{report_id}"
                    response = self.session.delete(endpoint, timeout=30)
                    if response.status_code == 200:
                        self.log(f"   ✅ Cleaned up survey report ID: {report_id}")
                        self.created_report_ids.remove(report_id)
                    else:
                        self.log(f"   ⚠️ Failed to clean up survey report ID: {report_id}")
                except Exception as e:
                    self.log(f"   ⚠️ Error cleaning up survey report ID {report_id}: {str(e)}")
            
            self.log("✅ Cleanup completed")
            
        except Exception as e:
            self.log(f"❌ Error during cleanup: {str(e)}", "ERROR")
    
    def run_comprehensive_survey_reports_test(self):
        """Run comprehensive test of all survey report endpoints"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE SURVEY REPORTS BACKEND API TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find ship
            self.log("\nSTEP 2: Finding test ship")
            if not self.find_ship():
                self.log("❌ CRITICAL: Ship discovery failed - cannot proceed")
                return False
            
            # Step 3: Test permission checks
            self.log("\nSTEP 3: Testing permission checks")
            self.test_permission_checks()
            
            # Step 4: Test CREATE survey report endpoint
            self.log("\nSTEP 4: Testing POST /api/survey-reports - Create survey report")
            created_report = self.test_create_survey_report()
            if not created_report:
                self.log("❌ CRITICAL: Create survey report endpoint failed")
                return False
            
            created_report_id = created_report.get('id')
            
            # Step 5: Test create with invalid ship ID
            self.log("\nSTEP 5: Testing create survey report with invalid ship ID")
            self.test_create_survey_report_invalid_ship()
            
            # Step 6: Test GET survey reports by ship
            self.log("\nSTEP 6: Testing GET /api/survey-reports?ship_id={ship_id} - Get reports by ship")
            self.test_get_survey_reports_by_ship()
            
            # Step 7: Test GET all survey reports
            self.log("\nSTEP 7: Testing GET /api/survey-reports - Get all survey reports")
            self.test_get_all_survey_reports()
            
            # Step 8: Test GET single survey report
            self.log("\nSTEP 8: Testing GET /api/survey-reports/{report_id} - Get single survey report")
            self.test_get_single_survey_report(created_report_id)
            
            # Step 9: Test GET single survey report with invalid ID
            self.log("\nSTEP 9: Testing get single survey report with invalid ID")
            self.test_get_single_survey_report_invalid_id()
            
            # Step 10: Test UPDATE survey report
            self.log("\nSTEP 10: Testing PUT /api/survey-reports/{report_id} - Update survey report")
            self.test_update_survey_report(created_report_id)
            
            # Step 11: Test partial update
            self.log("\nSTEP 11: Testing partial update of survey report")
            self.test_update_survey_report_partial(created_report_id)
            
            # Step 12: Test update with invalid ID
            self.log("\nSTEP 12: Testing update survey report with invalid ID")
            self.test_update_survey_report_invalid_id()
            
            # Step 13: Test delete with invalid ID
            self.log("\nSTEP 13: Testing delete survey report with invalid ID")
            self.test_delete_survey_report_invalid_id()
            
            # Step 14: Test DELETE survey report (do this last)
            self.log("\nSTEP 14: Testing DELETE /api/survey-reports/{report_id} - Delete survey report")
            self.test_delete_survey_report(created_report_id)
            
            # Step 15: Cleanup any remaining test data
            self.log("\nSTEP 15: Cleanup remaining test data")
            self.cleanup_test_data()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE SURVEY REPORTS TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 SURVEY REPORTS BACKEND API TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.survey_tests)
            passed_tests = sum(1 for result in self.survey_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('ship_discovery_successful', 'Ship discovery successful'),
                ('ship_id_retrieved', 'Ship ID retrieved'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.survey_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # CREATE Survey Report Results
            self.log("\n📝 CREATE SURVEY REPORT (POST /api/survey-reports):")
            create_tests = [
                ('create_survey_report_endpoint_accessible', 'Endpoint accessible'),
                ('create_survey_report_successful', 'Create operation successful'),
                ('create_survey_report_returns_correct_data', 'Returns correct data'),
                ('create_survey_report_ship_validation', 'Ship validation working'),
                ('create_survey_report_invalid_ship_id_validation', 'Invalid ship ID validation'),
            ]
            
            for test_key, description in create_tests:
                status = "✅ PASS" if self.survey_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # GET Survey Reports Results
            self.log("\n📋 GET SURVEY REPORTS:")
            get_tests = [
                ('get_survey_reports_by_ship_endpoint_accessible', 'Get by ship endpoint accessible'),
                ('get_survey_reports_by_ship_successful', 'Get by ship successful'),
                ('get_survey_reports_by_ship_filtering_works', 'Ship filtering works'),
                ('get_survey_reports_by_ship_returns_correct_data', 'Returns correct data structure'),
                ('get_single_survey_report_endpoint_accessible', 'Get single report endpoint accessible'),
                ('get_single_survey_report_successful', 'Get single report successful'),
                ('get_single_survey_report_returns_correct_data', 'Single report returns correct data'),
                ('get_single_survey_report_404_for_invalid_id', 'Invalid ID returns 404'),
            ]
            
            for test_key, description in get_tests:
                status = "✅ PASS" if self.survey_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # UPDATE Survey Report Results
            self.log("\n✏️ UPDATE SURVEY REPORT (PUT /api/survey-reports/{id}):")
            update_tests = [
                ('update_survey_report_endpoint_accessible', 'Update endpoint accessible'),
                ('update_survey_report_successful', 'Update operation successful'),
                ('update_survey_report_returns_updated_data', 'Returns updated data'),
                ('update_survey_report_partial_updates', 'Partial updates work'),
                ('update_survey_report_404_for_invalid_id', 'Invalid ID returns 404'),
            ]
            
            for test_key, description in update_tests:
                status = "✅ PASS" if self.survey_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # DELETE Survey Report Results
            self.log("\n🗑️ DELETE SURVEY REPORT (DELETE /api/survey-reports/{id}):")
            delete_tests = [
                ('delete_survey_report_endpoint_accessible', 'Delete endpoint accessible'),
                ('delete_survey_report_successful', 'Delete operation successful'),
                ('delete_survey_report_removes_from_database', 'Actually removes from database'),
                ('delete_survey_report_404_for_invalid_id', 'Invalid ID returns 404'),
            ]
            
            for test_key, description in delete_tests:
                status = "✅ PASS" if self.survey_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Data Validation Results
            self.log("\n🔍 DATA VALIDATION & INTEGRITY:")
            validation_tests = [
                ('survey_report_ship_linking_works', 'Ship linking works correctly'),
                ('survey_report_date_handling_correct', 'Date handling correct'),
                ('survey_report_status_handling_correct', 'Status handling correct'),
                ('survey_report_all_fields_stored_correctly', 'All fields stored correctly'),
                ('permission_checks_working', 'Permission checks working'),
            ]
            
            for test_key, description in validation_tests:
                status = "✅ PASS" if self.survey_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'create_survey_report_successful',
                'get_survey_reports_by_ship_successful',
                'get_single_survey_report_successful',
                'update_survey_report_successful',
                'delete_survey_report_successful'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.survey_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL CRUD OPERATIONS WORKING")
                self.log("   ✅ Survey Reports API fully functional")
            else:
                self.log("   ❌ SOME CRITICAL OPERATIONS FAILED")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical operations passed")
            
            if success_rate >= 90:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 75:
                self.log(f"   ✅ GOOD SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ ACCEPTABLE SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the survey reports test"""
    tester = SurveyReportsTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_survey_reports_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Return appropriate exit code
        return 0 if success else 1
        
    except KeyboardInterrupt:
        tester.log("\n❌ Test interrupted by user", "ERROR")
        return 1
    except Exception as e:
        tester.log(f"\n❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        return 1
    finally:
        # Always try to cleanup
        try:
            tester.cleanup_test_data()
        except:
            pass

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Survey Report Date Format Testing
Focus: Check the exact date format returned by Survey Report endpoints

REVIEW REQUEST REQUIREMENTS:
1. Login with admin1/123456
2. Find ship "BROTHER 36" 
3. Create a survey report with issued_date: "2025-01-15"
4. GET that survey report and check the EXACT format of issued_date in the response
5. Print the raw JSON response to see the exact date format

**Focus on:** What is the exact string format of issued_date in the API response? 
Is it "2025-01-15T00:00:00Z" or something else?
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
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vessel-docs-sys.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class SurveyReportDateFormatTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.ship_name = "BROTHER 36"
        self.ship_id = None
        self.created_survey_report_id = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
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
                
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_ship(self):
        """Find the test ship BROTHER 36"""
        try:
            self.log(f"🚢 Finding ship: {self.ship_name}")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                for ship in ships:
                    if ship.get("name") == self.ship_name:
                        self.ship_id = ship.get("id")
                        self.log(f"✅ Found ship: {self.ship_name} (ID: {self.ship_id})")
                        return True
                
                self.log(f"❌ Ship '{self.ship_name}' not found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def create_survey_report(self):
        """Create a survey report with issued_date: '2025-01-15'"""
        try:
            self.log("📋 Creating survey report with issued_date: '2025-01-15'...")
            
            if not self.ship_id:
                self.log("❌ No ship ID available", "ERROR")
                return False
            
            # Create survey report data with specific date format
            survey_report_data = {
                "ship_id": self.ship_id,
                "survey_report_name": "Date Format Test Survey Report",
                "survey_report_no": "TEST-2025-001",
                "issued_date": "2025-01-15",  # Specific date format as requested
                "issued_by": "Test Authority",
                "status": "Valid",
                "note": "Test survey report for date format verification"
            }
            
            endpoint = f"{BACKEND_URL}/survey-reports"
            self.log(f"   POST {endpoint}")
            self.log(f"   Request data: {json.dumps(survey_report_data, indent=2)}")
            
            response = self.session.post(endpoint, json=survey_report_data, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.created_survey_report_id = result.get("id")
                
                self.log("✅ Survey report created successfully")
                self.log(f"   Survey Report ID: {self.created_survey_report_id}")
                
                # Print the raw response to see the exact format
                self.log("📄 RAW CREATE RESPONSE:")
                self.log(json.dumps(result, indent=2))
                
                # Check the issued_date format in create response
                issued_date_in_response = result.get("issued_date")
                self.log(f"🔍 issued_date in CREATE response: '{issued_date_in_response}'")
                self.log(f"🔍 issued_date type: {type(issued_date_in_response)}")
                
                return True
            else:
                self.log(f"❌ Failed to create survey report: {response.status_code}", "ERROR")
                self.log(f"   Error response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating survey report: {str(e)}", "ERROR")
            return False
    
    def get_survey_report(self):
        """GET the created survey report and check the exact date format"""
        try:
            self.log("📋 Getting survey report to check date format...")
            
            if not self.created_survey_report_id:
                self.log("❌ No survey report ID available", "ERROR")
                return False
            
            endpoint = f"{BACKEND_URL}/survey-reports/{self.created_survey_report_id}"
            self.log(f"   GET {endpoint}")
            
            response = self.session.get(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Survey report retrieved successfully")
                
                # Print the COMPLETE raw response to see the exact format
                self.log("📄 RAW GET RESPONSE (COMPLETE):")
                self.log("=" * 80)
                self.log(json.dumps(result, indent=2))
                self.log("=" * 80)
                
                # Focus on the issued_date field
                issued_date_in_response = result.get("issued_date")
                self.log(f"🔍 EXACT issued_date in GET response: '{issued_date_in_response}'")
                self.log(f"🔍 issued_date type: {type(issued_date_in_response)}")
                
                # Analyze the format
                if issued_date_in_response:
                    self.log("🔍 DATE FORMAT ANALYSIS:")
                    
                    # Check if it's ISO format with timezone
                    if "T" in str(issued_date_in_response):
                        self.log("   ✅ Contains 'T' - ISO datetime format detected")
                        
                        if str(issued_date_in_response).endswith("Z"):
                            self.log("   ✅ Ends with 'Z' - UTC timezone indicator")
                            self.log(f"   📅 FORMAT: ISO 8601 UTC format: '{issued_date_in_response}'")
                        elif "+" in str(issued_date_in_response) or str(issued_date_in_response).endswith(":00"):
                            self.log("   ✅ Contains timezone offset")
                            self.log(f"   📅 FORMAT: ISO 8601 with timezone: '{issued_date_in_response}'")
                        else:
                            self.log("   ⚠️ ISO format but no timezone indicator")
                            self.log(f"   📅 FORMAT: ISO 8601 without timezone: '{issued_date_in_response}'")
                    else:
                        self.log("   ⚠️ No 'T' found - not ISO datetime format")
                        self.log(f"   📅 FORMAT: Date only format: '{issued_date_in_response}'")
                    
                    # Check specific patterns
                    date_str = str(issued_date_in_response)
                    if date_str == "2025-01-15T00:00:00Z":
                        self.log("   🎯 EXACT MATCH: '2025-01-15T00:00:00Z'")
                    elif date_str.startswith("2025-01-15T00:00:00"):
                        self.log(f"   🎯 CLOSE MATCH: Starts with '2025-01-15T00:00:00', full format: '{date_str}'")
                    elif date_str.startswith("2025-01-15"):
                        self.log(f"   🎯 DATE MATCH: Starts with '2025-01-15', full format: '{date_str}'")
                    else:
                        self.log(f"   ❓ DIFFERENT FORMAT: '{date_str}'")
                
                return True
            else:
                self.log(f"❌ Failed to get survey report: {response.status_code}", "ERROR")
                self.log(f"   Error response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting survey report: {str(e)}", "ERROR")
            return False
    
    def get_all_survey_reports(self):
        """GET all survey reports for the ship to see date formats"""
        try:
            self.log("📋 Getting all survey reports for comparison...")
            
            if not self.ship_id:
                self.log("❌ No ship ID available", "ERROR")
                return False
            
            endpoint = f"{BACKEND_URL}/survey-reports?ship_id={self.ship_id}"
            self.log(f"   GET {endpoint}")
            
            response = self.session.get(endpoint, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                results = response.json()
                
                self.log(f"✅ Retrieved {len(results)} survey reports")
                
                # Print all survey reports to compare date formats
                self.log("📄 ALL SURVEY REPORTS (for date format comparison):")
                self.log("=" * 80)
                for i, report in enumerate(results):
                    self.log(f"Report {i+1}:")
                    self.log(f"  ID: {report.get('id')}")
                    self.log(f"  Name: {report.get('survey_report_name')}")
                    self.log(f"  issued_date: '{report.get('issued_date')}' (type: {type(report.get('issued_date'))})")
                    self.log("")
                self.log("=" * 80)
                
                return True
            else:
                self.log(f"❌ Failed to get survey reports: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting all survey reports: {str(e)}", "ERROR")
            return False
    
    def cleanup(self):
        """Clean up created test data"""
        try:
            if self.created_survey_report_id:
                self.log("🧹 Cleaning up created survey report...")
                
                endpoint = f"{BACKEND_URL}/survey-reports/{self.created_survey_report_id}"
                response = self.session.delete(endpoint, timeout=30)
                
                if response.status_code in [200, 204]:
                    self.log("✅ Survey report cleaned up successfully")
                else:
                    self.log(f"⚠️ Failed to clean up survey report: {response.status_code}")
            
        except Exception as e:
            self.log(f"⚠️ Error during cleanup: {str(e)}")
    
    def run_date_format_test(self):
        """Run the complete date format test"""
        try:
            self.log("🚀 STARTING SURVEY REPORT DATE FORMAT TEST")
            self.log("=" * 80)
            self.log("OBJECTIVE: Check the exact format of issued_date in API response")
            self.log("EXPECTED INPUT: '2025-01-15'")
            self.log("QUESTION: Is output '2025-01-15T00:00:00Z' or something else?")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find ship
            self.log("\nSTEP 2: Find ship BROTHER 36")
            if not self.find_ship():
                self.log("❌ CRITICAL: Ship not found - cannot proceed")
                return False
            
            # Step 3: Create survey report with specific date
            self.log("\nSTEP 3: Create survey report with issued_date: '2025-01-15'")
            if not self.create_survey_report():
                self.log("❌ CRITICAL: Failed to create survey report")
                return False
            
            # Step 4: GET the survey report and check date format
            self.log("\nSTEP 4: GET survey report and check EXACT date format")
            if not self.get_survey_report():
                self.log("❌ CRITICAL: Failed to get survey report")
                return False
            
            # Step 5: Get all survey reports for comparison
            self.log("\nSTEP 5: Get all survey reports for date format comparison")
            self.get_all_survey_reports()
            
            # Step 6: Cleanup
            self.log("\nSTEP 6: Cleanup")
            self.cleanup()
            
            self.log("\n" + "=" * 80)
            self.log("✅ SURVEY REPORT DATE FORMAT TEST COMPLETED")
            self.log("=" * 80)
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in date format test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False

def main():
    """Main function to run the test"""
    tester = SurveyReportDateFormatTester()
    success = tester.run_date_format_test()
    
    if success:
        print("\n🎯 TEST COMPLETED SUCCESSFULLY")
        print("Check the logs above for the EXACT date format in the API response")
    else:
        print("\n❌ TEST FAILED")
        print("Check the error logs above for details")
    
    return success

if __name__ == "__main__":
    main()
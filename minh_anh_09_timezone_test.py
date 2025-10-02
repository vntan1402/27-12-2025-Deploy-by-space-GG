#!/usr/bin/env python3
"""
CRITICAL DATE TIMEZONE BUG INVESTIGATION - Multi Cert Upload
MINH ANH 09 CSSC Certificate Testing

OBJECTIVE: Test MINH ANH 09 CSSC certificate upload to trace exactly where dates get timezone shift.

TEST CREDENTIALS: admin1/123456
TEST FILE: "10. SC- MINH ANH 09-CSSC- PM242308.pdf"
URL: https://customer-assets.emergentagent.com/job_fleet-tracker-104/artifacts/j8whyi0q_10.%20SC-%20MINH%20ANH%2009-CSSC-%20PM242308.pdf

EXPECTED DATES (from PDF):
- Issue Date: OCTOBER 4, 2024 (04/10/2024)
- Valid Date: MAY 5, 2027 (05/05/2027)

SUCCESS CRITERIA:
✅ issue_date in DB = "2024-10-04T00:00:00Z" (OCTOBER 4)
✅ valid_date in DB = "2027-05-05T00:00:00Z" (MAY 5)
❌ Any other date = BUG CONFIRMED
"""

import requests
import json
import os
import sys
import tempfile
from datetime import datetime
import traceback
from urllib.parse import urlparse

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fleet-tracker-104.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class MinHAnh09TimezoneTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.minh_anh_ship = None
        self.certificate_file_path = None
        self.upload_response = None
        self.certificate_id = None
        self.test_results = {}
        
        # Expected dates from PDF
        self.expected_issue_date = "2024-10-04"  # OCTOBER 4, 2024
        self.expected_valid_date = "2027-05-05"  # MAY 5, 2027
        
        # Certificate URL
        self.cert_url = "https://customer-assets.emergentagent.com/job_fleet-tracker-104/artifacts/j8whyi0q_10.%20SC-%20MINH%20ANH%2009-CSSC-%20PM242308.pdf"
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
    def authenticate(self):
        """Step 1: Login and Get Auth Token"""
        try:
            self.log("🔐 STEP 1: LOGIN AND GET AUTH TOKEN")
            self.log("=" * 60)
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            self.log(f"POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=60)
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                self.log(f"   Token: {self.auth_token[:20]}...")
                
                return True
            else:
                self.log(f"❌ Authentication failed - Status: {response.status_code}")
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
    
    def find_minh_anh_09_ship(self):
        """Step 2: Get MINH ANH 09 Ship ID"""
        try:
            self.log("\n🚢 STEP 2: GET MINH ANH 09 SHIP ID")
            self.log("=" * 60)
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"Found {len(ships)} total ships")
                
                # Look for MINH ANH 09
                for ship in ships:
                    ship_name = ship.get('name', '').upper()
                    if 'MINH ANH' in ship_name and '09' in ship_name:
                        self.minh_anh_ship = ship
                        break
                
                if self.minh_anh_ship:
                    ship_id = self.minh_anh_ship.get('id')
                    ship_name = self.minh_anh_ship.get('name')
                    imo = self.minh_anh_ship.get('imo')
                    
                    self.log(f"✅ Found MINH ANH 09 ship:")
                    self.log(f"   Ship ID: {ship_id}")
                    self.log(f"   Ship Name: {ship_name}")
                    self.log(f"   IMO: {imo}")
                    
                    return True
                else:
                    self.log("❌ MINH ANH 09 ship not found")
                    # List available ships for debugging
                    self.log("   Available ships:")
                    for ship in ships[:10]:
                        ship_name = ship.get('name', 'Unknown')
                        if 'MINH' in ship_name.upper() or 'ANH' in ship_name.upper():
                            self.log(f"      - {ship_name} (potential match)")
                        else:
                            self.log(f"      - {ship_name}")
                    return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding MINH ANH 09 ship: {str(e)}", "ERROR")
            return False
    
    def download_certificate_file(self):
        """Step 3: Download Certificate File"""
        try:
            self.log("\n📥 STEP 3: DOWNLOAD CERTIFICATE FILE")
            self.log("=" * 60)
            
            self.log(f"Downloading from: {self.cert_url}")
            
            # Download the certificate file
            response = requests.get(self.cert_url, timeout=120)
            self.log(f"Download response status: {response.status_code}")
            
            if response.status_code == 200:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(response.content)
                    self.certificate_file_path = temp_file.name
                
                file_size = len(response.content)
                self.log(f"✅ Certificate downloaded successfully")
                self.log(f"   File size: {file_size} bytes")
                self.log(f"   Saved to: {self.certificate_file_path}")
                
                return True
            else:
                self.log(f"❌ Failed to download certificate: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error downloading certificate: {str(e)}", "ERROR")
            return False
    
    def upload_certificate_multi_upload(self):
        """Step 4: Upload Certificate via Multi-Upload Endpoint"""
        try:
            self.log("\n📤 STEP 4: UPLOAD CERTIFICATE VIA MULTI-UPLOAD ENDPOINT")
            self.log("=" * 60)
            
            if not self.minh_anh_ship or not self.certificate_file_path:
                self.log("❌ Missing ship data or certificate file")
                return False
            
            ship_id = self.minh_anh_ship.get('id')
            endpoint = f"{BACKEND_URL}/certificates/multi-upload?ship_id={ship_id}"
            
            self.log(f"POST {endpoint}")
            self.log(f"Ship ID: {ship_id}")
            self.log(f"File: {self.certificate_file_path}")
            
            # Prepare file for upload
            with open(self.certificate_file_path, 'rb') as file:
                files = {'files': ('minh_anh_09_cssc.pdf', file, 'application/pdf')}
                
                response = requests.post(
                    endpoint,
                    headers=self.get_headers(),
                    files=files,
                    timeout=300  # 5 minutes for AI processing
                )
            
            self.log(f"Upload response status: {response.status_code}")
            
            if response.status_code == 200:
                self.upload_response = response.json()
                self.log("✅ Certificate upload successful")
                
                # Log the full response for analysis
                self.log("📊 UPLOAD RESPONSE ANALYSIS:")
                self.log(json.dumps(self.upload_response, indent=2))
                
                return True
            else:
                self.log(f"❌ Certificate upload failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error uploading certificate: {str(e)}", "ERROR")
            return False
    
    def analyze_upload_response(self):
        """Step 5: Analyze Response - CRITICAL CHECK"""
        try:
            self.log("\n🔍 STEP 5: ANALYZE RESPONSE - CRITICAL CHECK")
            self.log("=" * 60)
            
            if not self.upload_response:
                self.log("❌ No upload response to analyze")
                return False
            
            # Look for analysis section in response
            analysis = None
            certificate_data = None
            
            # Check different response structures
            if 'results' in self.upload_response:
                results = self.upload_response['results']
                if isinstance(results, list) and len(results) > 0:
                    first_result = results[0]
                    analysis = first_result.get('analysis')
                    certificate_data = first_result.get('certificate')
            elif 'analysis' in self.upload_response:
                analysis = self.upload_response['analysis']
                certificate_data = self.upload_response.get('certificate')
            
            self.log("🔍 AI EXTRACTION ANALYSIS:")
            if analysis:
                issue_date = analysis.get('issue_date')
                valid_date = analysis.get('valid_date')
                
                self.log(f"   AI Extracted Issue Date: {issue_date}")
                self.log(f"   AI Extracted Valid Date: {valid_date}")
                self.log(f"   Expected Issue Date: {self.expected_issue_date}")
                self.log(f"   Expected Valid Date: {self.expected_valid_date}")
                
                # Check AI extraction format
                if issue_date:
                    self.log(f"   Issue Date Format: {type(issue_date).__name__} - '{issue_date}'")
                if valid_date:
                    self.log(f"   Valid Date Format: {type(valid_date).__name__} - '{valid_date}'")
                    
                # Store for later comparison
                self.test_results['ai_issue_date'] = issue_date
                self.test_results['ai_valid_date'] = valid_date
            else:
                self.log("   ❌ No analysis section found in response")
            
            # Check certificate data
            if certificate_data:
                self.certificate_id = certificate_data.get('id')
                cert_issue_date = certificate_data.get('issue_date')
                cert_valid_date = certificate_data.get('valid_date')
                
                self.log("📋 CERTIFICATE DATA:")
                self.log(f"   Certificate ID: {self.certificate_id}")
                self.log(f"   Certificate Issue Date: {cert_issue_date}")
                self.log(f"   Certificate Valid Date: {cert_valid_date}")
                
                # Store for comparison
                self.test_results['cert_issue_date'] = cert_issue_date
                self.test_results['cert_valid_date'] = cert_valid_date
            else:
                self.log("   ❌ No certificate data found in response")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error analyzing upload response: {str(e)}", "ERROR")
            return False
    
    def check_database_storage(self):
        """Step 6: Check Database - Get Created Certificate"""
        try:
            self.log("\n🗄️ STEP 6: CHECK DATABASE - GET CREATED CERTIFICATE")
            self.log("=" * 60)
            
            if not self.certificate_id:
                self.log("❌ No certificate ID available for database check")
                return False
            
            endpoint = f"{BACKEND_URL}/certificates/{self.certificate_id}"
            self.log(f"GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                cert_data = response.json()
                
                db_issue_date = cert_data.get('issue_date')
                db_valid_date = cert_data.get('valid_date')
                
                self.log("✅ Certificate retrieved from database")
                self.log("📊 DATABASE STORAGE ANALYSIS:")
                self.log(f"   Database Issue Date: {db_issue_date}")
                self.log(f"   Database Valid Date: {db_valid_date}")
                
                # Store for final comparison
                self.test_results['db_issue_date'] = db_issue_date
                self.test_results['db_valid_date'] = db_valid_date
                
                # Log full certificate data for debugging
                self.log("📋 FULL CERTIFICATE DATA:")
                self.log(json.dumps(cert_data, indent=2))
                
                return True
            else:
                self.log(f"❌ Failed to retrieve certificate from database: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking database storage: {str(e)}", "ERROR")
            return False
    
    def compare_dates_final_analysis(self):
        """Step 7: Compare Dates - FINAL ANALYSIS"""
        try:
            self.log("\n🎯 STEP 7: COMPARE DATES - FINAL ANALYSIS")
            self.log("=" * 60)
            
            self.log("📊 COMPLETE DATE COMPARISON:")
            self.log(f"   Expected Issue Date: {self.expected_issue_date} (OCTOBER 4, 2024)")
            self.log(f"   Expected Valid Date: {self.expected_valid_date} (MAY 5, 2027)")
            
            # AI Extraction Results
            ai_issue = self.test_results.get('ai_issue_date')
            ai_valid = self.test_results.get('ai_valid_date')
            self.log(f"   AI Issue Date: {ai_issue}")
            self.log(f"   AI Valid Date: {ai_valid}")
            
            # Certificate Response Results
            cert_issue = self.test_results.get('cert_issue_date')
            cert_valid = self.test_results.get('cert_valid_date')
            self.log(f"   Certificate Issue Date: {cert_issue}")
            self.log(f"   Certificate Valid Date: {cert_valid}")
            
            # Database Results
            db_issue = self.test_results.get('db_issue_date')
            db_valid = self.test_results.get('db_valid_date')
            self.log(f"   Database Issue Date: {db_issue}")
            self.log(f"   Database Valid Date: {db_valid}")
            
            # Critical Bug Analysis
            self.log("\n🔍 CRITICAL BUG ANALYSIS:")
            
            # Check for 1-day timezone shift
            issue_date_correct = self.check_date_correctness(db_issue, self.expected_issue_date, "Issue Date")
            valid_date_correct = self.check_date_correctness(db_valid, self.expected_valid_date, "Valid Date")
            
            # Final verdict
            if issue_date_correct and valid_date_correct:
                self.log("\n✅ SUCCESS CRITERIA MET:")
                self.log(f"   ✅ Issue Date in DB = correct (OCTOBER 4, 2024)")
                self.log(f"   ✅ Valid Date in DB = correct (MAY 5, 2027)")
                self.log("\n🎉 NO TIMEZONE BUG DETECTED - DATES ARE CORRECT!")
                return True
            else:
                self.log("\n❌ BUG CONFIRMED:")
                if not issue_date_correct:
                    self.log(f"   ❌ Issue Date has timezone shift")
                if not valid_date_correct:
                    self.log(f"   ❌ Valid Date has timezone shift")
                self.log("\n🚨 TIMEZONE BUG DETECTED - DATES ARE SHIFTED!")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in final date comparison: {str(e)}", "ERROR")
            return False
    
    def check_date_correctness(self, actual_date, expected_date, date_name):
        """Check if actual date matches expected date (accounting for timezone formats)"""
        try:
            if not actual_date:
                self.log(f"   ❌ {date_name}: No date found in database")
                return False
            
            # Extract date part from various formats
            actual_date_str = str(actual_date)
            
            # Handle ISO format with timezone
            if 'T' in actual_date_str:
                actual_date_part = actual_date_str.split('T')[0]
            else:
                actual_date_part = actual_date_str
            
            # Compare dates
            if actual_date_part == expected_date:
                self.log(f"   ✅ {date_name}: CORRECT - {actual_date_part} matches {expected_date}")
                return True
            else:
                self.log(f"   ❌ {date_name}: INCORRECT - {actual_date_part} does not match {expected_date}")
                
                # Check for 1-day shift (common timezone bug)
                from datetime import datetime, timedelta
                try:
                    expected_dt = datetime.strptime(expected_date, '%Y-%m-%d')
                    actual_dt = datetime.strptime(actual_date_part, '%Y-%m-%d')
                    
                    diff = (expected_dt - actual_dt).days
                    if abs(diff) == 1:
                        self.log(f"   🚨 {date_name}: 1-DAY TIMEZONE SHIFT DETECTED (difference: {diff} days)")
                    else:
                        self.log(f"   ⚠️ {date_name}: Date difference: {diff} days")
                except:
                    self.log(f"   ⚠️ {date_name}: Could not parse dates for shift analysis")
                
                return False
                
        except Exception as e:
            self.log(f"   ❌ Error checking {date_name} correctness: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            if self.certificate_file_path and os.path.exists(self.certificate_file_path):
                os.unlink(self.certificate_file_path)
                self.log(f"🧹 Cleaned up temporary file: {self.certificate_file_path}")
        except Exception as e:
            self.log(f"⚠️ Error cleaning up: {str(e)}")
    
    def run_timezone_bug_investigation(self):
        """Main test function for MINH ANH 09 timezone bug investigation"""
        self.log("🚨 CRITICAL DATE TIMEZONE BUG INVESTIGATION - Multi Cert Upload")
        self.log("🎯 MINH ANH 09 CSSC Certificate Testing")
        self.log("=" * 80)
        
        try:
            # Step 1: Login and Get Auth Token
            if not self.authenticate():
                return False
            
            # Step 2: Get MINH ANH 09 Ship ID
            if not self.find_minh_anh_09_ship():
                return False
            
            # Step 3: Download Certificate File
            if not self.download_certificate_file():
                return False
            
            # Step 4: Upload Certificate via Multi-Upload Endpoint
            if not self.upload_certificate_multi_upload():
                return False
            
            # Step 5: Analyze Response - CRITICAL CHECK
            if not self.analyze_upload_response():
                return False
            
            # Step 6: Check Database - Get Created Certificate
            if not self.check_database_storage():
                return False
            
            # Step 7: Compare Dates - FINAL ANALYSIS
            result = self.compare_dates_final_analysis()
            
            return result
            
        except Exception as e:
            self.log(f"❌ Critical error in timezone bug investigation: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
        finally:
            self.cleanup()

def main():
    """Main function to run MINH ANH 09 timezone bug investigation"""
    print("🚨 CRITICAL DATE TIMEZONE BUG INVESTIGATION STARTED")
    print("🎯 MINH ANH 09 CSSC Certificate Testing")
    print("=" * 80)
    
    try:
        tester = MinHAnh09TimezoneTester()
        success = tester.run_timezone_bug_investigation()
        
        if success:
            print("\n✅ TIMEZONE BUG INVESTIGATION COMPLETED - NO BUG DETECTED")
            print("🎉 Dates are stored correctly in database!")
        else:
            print("\n❌ TIMEZONE BUG INVESTIGATION COMPLETED - BUG CONFIRMED")
            print("🚨 Timezone shift detected in date storage!")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
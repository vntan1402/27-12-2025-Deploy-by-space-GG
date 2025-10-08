#!/usr/bin/env python3
"""
Certificate Update Backend API Testing
FOCUS: Test the certificate update backend API functionality to confirm if the backend works correctly

REVIEW REQUEST REQUIREMENTS:
1. Authentication: Login with admin1/123456 to get a valid token
2. Get Ships: Fetch ships to get a valid ship with certificates  
3. Get Certificates: Fetch certificates for a ship to get a valid certificate ID
4. Test Certificate Update: Test PUT /api/certificates/{cert_id} endpoint to update a certificate's Next Survey date
5. Verify Update: Confirm the update was persisted by fetching the same certificate

Expected results:
- Login should return valid token
- Certificate update should return 200 status 
- Updated certificate should show the new Next Survey date when fetched again
- This will confirm the backend API works, so the issue is purely frontend
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import time
import traceback

# Configuration - Use environment variable for backend URL
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://maritime-ai-crew.preview.emergentagent.com') + '/api'
print(f"Using backend URL: {BACKEND_URL}")

class CertificateUpdateTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for certificate update functionality
        self.update_tests = {
            # Authentication
            'authentication_successful': False,
            'valid_token_received': False,
            
            # Ships and Certificates Discovery
            'ships_fetched_successfully': False,
            'ship_with_certificates_found': False,
            'certificates_fetched_successfully': False,
            'valid_certificate_id_obtained': False,
            
            # Certificate Update Testing
            'put_endpoint_accessible': False,
            'certificate_update_successful': False,
            'update_response_200_status': False,
            'update_response_contains_new_data': False,
            
            # Persistence Verification
            'updated_certificate_fetched': False,
            'next_survey_date_persisted': False,
            'database_update_confirmed': False,
            
            # Overall Assessment
            'backend_api_working': False,
            'issue_is_frontend_only': False
        }
        
        # Store test data
        self.test_ship = None
        self.test_certificate = None
        self.original_next_survey = None
        self.new_next_survey = None
        self.update_response = None
        
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
            self.log("🔐 Step 1: Authenticating with admin1/123456...")
            
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
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                self.log(f"   Token received: {self.auth_token[:20]}...")
                
                self.update_tests['authentication_successful'] = True
                self.update_tests['valid_token_received'] = bool(self.auth_token)
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
    
    def get_ships(self):
        """Get ships to find one with certificates"""
        try:
            self.log("🚢 Step 2: Fetching ships to get a valid ship with certificates...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships")
                
                self.update_tests['ships_fetched_successfully'] = True
                
                # Find a ship with certificates
                for ship in ships:
                    ship_name = ship.get('name', 'Unknown')
                    ship_id = ship.get('id')
                    company = ship.get('company', 'Unknown')
                    
                    self.log(f"   Checking ship: {ship_name} (Company: {company})")
                    
                    # Get certificates for this ship
                    cert_endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
                    cert_response = requests.get(cert_endpoint, headers=self.get_headers(), timeout=30)
                    
                    if cert_response.status_code == 200:
                        certificates = cert_response.json()
                        self.log(f"      Found {len(certificates)} certificates")
                        
                        if certificates:
                            self.test_ship = ship
                            self.update_tests['ship_with_certificates_found'] = True
                            self.log(f"   ✅ Selected ship: {ship_name} with {len(certificates)} certificates")
                            return True
                    else:
                        self.log(f"      Failed to get certificates: {cert_response.status_code}")
                
                self.log("   ❌ No ships with certificates found")
                return False
            else:
                self.log(f"   ❌ Failed to fetch ships: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error fetching ships: {str(e)}", "ERROR")
            return False
    
    def get_certificates(self):
        """Get certificates for the selected ship to get a valid certificate ID"""
        try:
            self.log("📋 Step 3: Fetching certificates for ship to get a valid certificate ID...")
            
            if not self.test_ship:
                self.log("   ❌ No test ship selected")
                return False
            
            ship_id = self.test_ship.get('id')
            ship_name = self.test_ship.get('name')
            
            endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
            self.log(f"   GET {endpoint}")
            self.log(f"   Ship: {ship_name} (ID: {ship_id})")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   Found {len(certificates)} certificates")
                
                self.update_tests['certificates_fetched_successfully'] = True
                
                # Find a suitable certificate for testing (one with a next_survey date)
                for cert in certificates:
                    cert_id = cert.get('id')
                    cert_name = cert.get('cert_name', 'Unknown')
                    next_survey = cert.get('next_survey')
                    
                    self.log(f"   Certificate: {cert_name}")
                    self.log(f"      ID: {cert_id}")
                    self.log(f"      Next Survey: {next_survey}")
                    
                    if cert_id:  # Any certificate with an ID will work
                        self.test_certificate = cert
                        self.original_next_survey = next_survey
                        self.update_tests['valid_certificate_id_obtained'] = True
                        self.log(f"   ✅ Selected certificate: {cert_name}")
                        self.log(f"      Original Next Survey: {self.original_next_survey}")
                        return True
                
                self.log("   ❌ No suitable certificates found")
                return False
            else:
                self.log(f"   ❌ Failed to fetch certificates: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error fetching certificates: {str(e)}", "ERROR")
            return False
    
    def test_certificate_update(self):
        """Test PUT /api/certificates/{cert_id} endpoint to update a certificate's Next Survey date"""
        try:
            self.log("🔄 Step 4: Testing certificate update (PUT /api/certificates/{cert_id})...")
            
            if not self.test_certificate:
                self.log("   ❌ No test certificate selected")
                return False
            
            cert_id = self.test_certificate.get('id')
            cert_name = self.test_certificate.get('cert_name', 'Unknown')
            
            # Generate a new next survey date (30 days from now)
            new_date = datetime.now() + timedelta(days=30)
            self.new_next_survey = new_date.strftime('%Y-%m-%d')
            
            update_data = {
                "next_survey": self.new_next_survey
            }
            
            endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
            self.log(f"   PUT {endpoint}")
            self.log(f"   Certificate: {cert_name}")
            self.log(f"   Original Next Survey: {self.original_next_survey}")
            self.log(f"   New Next Survey: {self.new_next_survey}")
            self.log(f"   Update data: {update_data}")
            
            response = requests.put(endpoint, json=update_data, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            self.update_tests['put_endpoint_accessible'] = True
            
            if response.status_code == 200:
                self.update_tests['certificate_update_successful'] = True
                self.update_tests['update_response_200_status'] = True
                
                try:
                    response_data = response.json()
                    self.update_response = response_data
                    self.log("   ✅ Certificate update successful")
                    self.log(f"   Response data keys: {list(response_data.keys())}")
                    
                    # Check if response contains the updated data
                    response_next_survey = response_data.get('next_survey')
                    if response_next_survey:
                        self.log(f"   Response Next Survey: {response_next_survey}")
                        
                        # Check if the new date is in the response (handle different date formats)
                        if (self.new_next_survey in str(response_next_survey) or 
                            response_next_survey.startswith(self.new_next_survey)):
                            self.update_tests['update_response_contains_new_data'] = True
                            self.log("   ✅ Response contains updated Next Survey date")
                        else:
                            self.log(f"   ⚠️ Response Next Survey doesn't match expected: {response_next_survey} vs {self.new_next_survey}")
                    else:
                        self.log("   ⚠️ No next_survey field in response")
                    
                    return True
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                self.log(f"   ❌ Certificate update failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing certificate update: {str(e)}", "ERROR")
            return False
    
    def verify_update_persistence(self):
        """Verify the update was persisted by fetching the same certificate"""
        try:
            self.log("✅ Step 5: Verifying update persistence by fetching the same certificate...")
            
            if not self.test_certificate:
                self.log("   ❌ No test certificate to verify")
                return False
            
            cert_id = self.test_certificate.get('id')
            cert_name = self.test_certificate.get('cert_name', 'Unknown')
            
            endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
            self.log(f"   GET {endpoint}")
            self.log(f"   Certificate: {cert_name}")
            self.log(f"   Expected Next Survey: {self.new_next_survey}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.update_tests['updated_certificate_fetched'] = True
                
                try:
                    cert_data = response.json()
                    fetched_next_survey = cert_data.get('next_survey')
                    
                    self.log(f"   Fetched Next Survey: {fetched_next_survey}")
                    self.log(f"   Original Next Survey: {self.original_next_survey}")
                    self.log(f"   Expected Next Survey: {self.new_next_survey}")
                    
                    # Check if the update was persisted (handle different date formats)
                    if fetched_next_survey and (
                        self.new_next_survey in str(fetched_next_survey) or 
                        str(fetched_next_survey).startswith(self.new_next_survey)
                    ):
                        self.update_tests['next_survey_date_persisted'] = True
                        self.update_tests['database_update_confirmed'] = True
                        self.log("   ✅ Update was persisted - Next Survey date updated in database")
                        return True
                    else:
                        self.log(f"   ❌ Update was NOT persisted - fetched: {fetched_next_survey}, expected: {self.new_next_survey}")
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                self.log(f"   ❌ Failed to fetch updated certificate: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying update persistence: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive certificate update backend API test"""
        try:
            self.log("🚀 STARTING CERTIFICATE UPDATE BACKEND API TEST")
            self.log("=" * 80)
            self.log("FOCUS: Test the certificate update backend API functionality")
            self.log("PURPOSE: Confirm if the backend works correctly before debugging frontend issues")
            self.log("=" * 80)
            
            # Step 1: Authentication
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Get Ships
            if not self.get_ships():
                self.log("❌ CRITICAL: Failed to get ships - cannot proceed")
                return False
            
            # Step 3: Get Certificates
            if not self.get_certificates():
                self.log("❌ CRITICAL: Failed to get certificates - cannot proceed")
                return False
            
            # Step 4: Test Certificate Update
            if not self.test_certificate_update():
                self.log("❌ CRITICAL: Certificate update test failed")
                return False
            
            # Step 5: Verify Update Persistence
            if not self.verify_update_persistence():
                self.log("❌ CRITICAL: Update persistence verification failed")
                return False
            
            # Overall assessment
            self.update_tests['backend_api_working'] = True
            self.update_tests['issue_is_frontend_only'] = True
            
            self.log("\n" + "=" * 80)
            self.log("✅ CERTIFICATE UPDATE BACKEND API TEST COMPLETED SUCCESSFULLY")
            self.log("✅ BACKEND API IS WORKING CORRECTLY")
            self.log("✅ THE ISSUE IS PURELY FRONTEND")
            self.log("=" * 80)
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of certificate update test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 CERTIFICATE UPDATE BACKEND API TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.update_tests)
            passed_tests = sum(1 for result in self.update_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION:")
            auth_tests = [
                ('authentication_successful', 'Login with admin1/123456 successful'),
                ('valid_token_received', 'Valid token received'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.update_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Discovery Results
            self.log("\n🔍 SHIPS AND CERTIFICATES DISCOVERY:")
            discovery_tests = [
                ('ships_fetched_successfully', 'Ships fetched successfully'),
                ('ship_with_certificates_found', 'Ship with certificates found'),
                ('certificates_fetched_successfully', 'Certificates fetched successfully'),
                ('valid_certificate_id_obtained', 'Valid certificate ID obtained'),
            ]
            
            for test_key, description in discovery_tests:
                status = "✅ PASS" if self.update_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Update Testing Results
            self.log("\n🔄 CERTIFICATE UPDATE TESTING:")
            update_tests = [
                ('put_endpoint_accessible', 'PUT /api/certificates/{cert_id} endpoint accessible'),
                ('certificate_update_successful', 'Certificate update successful'),
                ('update_response_200_status', 'Update returned 200 status'),
                ('update_response_contains_new_data', 'Update response contains new data'),
            ]
            
            for test_key, description in update_tests:
                status = "✅ PASS" if self.update_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Persistence Verification Results
            self.log("\n💾 PERSISTENCE VERIFICATION:")
            persistence_tests = [
                ('updated_certificate_fetched', 'Updated certificate fetched successfully'),
                ('next_survey_date_persisted', 'Next Survey date persisted in database'),
                ('database_update_confirmed', 'Database update confirmed'),
            ]
            
            for test_key, description in persistence_tests:
                status = "✅ PASS" if self.update_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Test Data Summary
            if self.test_ship and self.test_certificate:
                self.log("\n📋 TEST DATA SUMMARY:")
                self.log(f"   Ship: {self.test_ship.get('name')} (ID: {self.test_ship.get('id')})")
                self.log(f"   Certificate: {self.test_certificate.get('cert_name')}")
                self.log(f"   Certificate ID: {self.test_certificate.get('id')}")
                self.log(f"   Original Next Survey: {self.original_next_survey}")
                self.log(f"   New Next Survey: {self.new_next_survey}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            if self.update_tests.get('backend_api_working', False):
                self.log("   ✅ BACKEND API IS WORKING CORRECTLY")
                self.log("   ✅ Certificate update endpoint is functional")
                self.log("   ✅ Database persistence is working")
                self.log("   ✅ All backend operations successful")
                self.log("")
                self.log("   🔍 CONCLUSION: THE ISSUE IS PURELY FRONTEND")
                self.log("   📝 RECOMMENDATION: Debug frontend JavaScript issue")
                self.log("   🎯 FOCUS: Frontend Save button click handler not triggering PUT request")
            else:
                self.log("   ❌ BACKEND API HAS ISSUES")
                self.log("   ❌ Certificate update functionality not working properly")
                self.log("   🔍 FURTHER BACKEND INVESTIGATION NEEDED")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the certificate update test"""
    tester = CertificateUpdateTester()
    
    try:
        # Run the comprehensive test
        success = tester.run_comprehensive_test()
        
        # Print detailed summary
        tester.print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
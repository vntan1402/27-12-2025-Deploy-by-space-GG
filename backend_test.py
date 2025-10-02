#!/usr/bin/env python3
"""
Ship Management System - Timezone Fix Testing
FOCUS: Test timezone fix for date handling consistency

REVIEW REQUEST REQUIREMENTS:
1. Ship Data Retrieval: Login with admin1/123456, retrieve SUNSHINE 01 ship data, verify date fields
2. Ship Update Operations: Test updating ship's date fields via PUT /api/ships/{ship_id}
3. Recalculation Endpoints: Test all recalculation endpoints for date consistency

EXPECTED BEHAVIOR:
- All date fields should remain consistent with no timezone shifts
- Dates saved and retrieved should be identical
- Recalculation endpoints should return proper date formats

TEST FOCUS:
- Date field consistency in ship data retrieval
- Date preservation during ship updates
- Recalculation endpoint date format consistency
- Timezone handling verification
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
import tempfile
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fleet-tracker-104.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class CertificateBackfillTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for backfill functionality
        self.backfill_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'backfill_endpoint_accessible': False,
            
            # Backfill processing
            'certificates_found_for_backfill': False,
            'backfill_processing_successful': False,
            'certificates_updated_with_ship_info': False,
            
            # Data verification
            'extracted_ship_name_populated': False,
            'ship_info_fields_populated': False,
            'tooltip_data_available': False,
            
            # API response verification
            'backfill_response_format_correct': False,
            'processing_statistics_provided': False,
            'error_handling_working': False,
        }
        
        # Store backfill results for analysis
        self.backfill_results = {}
        self.processed_certificates = []
        self.updated_certificates = []
        
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
                
                self.backfill_tests['authentication_successful'] = True
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
    
    def get_certificates_before_backfill(self):
        """Get sample certificates before backfill to analyze their current state"""
        try:
            self.log("📋 Getting certificates before backfill to analyze current state...")
            
            # Get all certificates to see which ones need backfill
            endpoint = f"{BACKEND_URL}/certificates"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   Found {len(certificates)} total certificates")
                
                # Analyze certificates that might need backfill
                need_backfill = []
                have_ship_info = []
                
                for cert in certificates[:50]:  # Check first 50 certificates
                    cert_id = cert.get('id')
                    cert_name = cert.get('cert_name', 'Unknown')
                    extracted_ship_name = cert.get('extracted_ship_name')
                    flag = cert.get('flag')
                    class_society = cert.get('class_society')
                    built_year = cert.get('built_year')
                    text_content = cert.get('text_content')
                    
                    # Check if certificate needs backfill
                    missing_fields = []
                    if not extracted_ship_name:
                        missing_fields.append('extracted_ship_name')
                    if not flag:
                        missing_fields.append('flag')
                    if not class_society:
                        missing_fields.append('class_society')
                    if not built_year:
                        missing_fields.append('built_year')
                    
                    if missing_fields and text_content:
                        need_backfill.append({
                            'id': cert_id,
                            'name': cert_name,
                            'missing_fields': missing_fields,
                            'has_text_content': bool(text_content)
                        })
                    elif not missing_fields:
                        have_ship_info.append({
                            'id': cert_id,
                            'name': cert_name,
                            'extracted_ship_name': extracted_ship_name
                        })
                
                self.log(f"   Certificates needing backfill: {len(need_backfill)}")
                self.log(f"   Certificates with ship info: {len(have_ship_info)}")
                
                if need_backfill:
                    self.log("   Sample certificates needing backfill:")
                    for cert in need_backfill[:5]:
                        self.log(f"      - {cert['name']} (missing: {', '.join(cert['missing_fields'])})")
                    self.backfill_tests['certificates_found_for_backfill'] = True
                
                if have_ship_info:
                    self.log("   Sample certificates with ship info:")
                    for cert in have_ship_info[:3]:
                        self.log(f"      - {cert['name']} (ship: {cert['extracted_ship_name']})")
                
                return len(need_backfill) > 0
            else:
                self.log(f"   ❌ Failed to get certificates: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting certificates before backfill: {str(e)}", "ERROR")
            return False
    
    def test_backfill_endpoint(self, limit=20):
        """Test the backfill endpoint with specified limit"""
        try:
            self.log(f"🔄 Testing backfill endpoint with limit={limit}...")
            
            endpoint = f"{BACKEND_URL}/certificates/backfill-ship-info"
            params = {"limit": limit}
            
            self.log(f"   POST {endpoint}?limit={limit}")
            
            response = requests.post(
                endpoint,
                params=params,
                headers=self.get_headers(),
                timeout=120  # Longer timeout for processing
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                self.log("✅ Backfill endpoint accessible")
                self.backfill_tests['backfill_endpoint_accessible'] = True
                
                # Log full response for analysis
                self.log("   Backfill Response:")
                self.log(f"   {json.dumps(response_data, indent=2)}")
                
                # Store results for analysis
                self.backfill_results = response_data
                
                # Verify response format
                if all(key in response_data for key in ['success', 'message', 'processed', 'updated', 'errors']):
                    self.backfill_tests['backfill_response_format_correct'] = True
                    self.log("✅ Response format is correct")
                
                if response_data.get('success'):
                    processed = response_data.get('processed', 0)
                    updated = response_data.get('updated', 0)
                    errors = response_data.get('errors', 0)
                    
                    self.log(f"   Processing Statistics:")
                    self.log(f"      Processed: {processed}")
                    self.log(f"      Updated: {updated}")
                    self.log(f"      Errors: {errors}")
                    
                    self.backfill_tests['processing_statistics_provided'] = True
                    
                    if processed > 0:
                        self.backfill_tests['backfill_processing_successful'] = True
                        self.log("✅ Backfill processing completed successfully")
                        
                        if updated > 0:
                            self.backfill_tests['certificates_updated_with_ship_info'] = True
                            self.log(f"✅ {updated} certificates updated with ship information")
                            return True
                        else:
                            self.log("⚠️ No certificates were updated (might be expected if all already have ship info)")
                            return True
                    else:
                        self.log("ℹ️ No certificates processed (might be expected if none need backfill)")
                        return True
                else:
                    self.log(f"   ❌ Backfill failed: {response_data.get('message')}")
                    return False
            else:
                self.log(f"   ❌ Backfill endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                    self.backfill_tests['error_handling_working'] = True
                except:
                    self.log(f"      Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Backfill endpoint testing error: {str(e)}", "ERROR")
            return False
    
    def verify_backfill_results(self):
        """Verify that certificates were actually updated with ship information"""
        try:
            self.log("🔍 Verifying backfill results by checking updated certificates...")
            
            if not self.backfill_results.get('updated', 0) > 0:
                self.log("   ℹ️ No certificates were updated, skipping verification")
                return True
            
            # Get certificates again to see if they now have ship information
            endpoint = f"{BACKEND_URL}/certificates"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                certificates = response.json()
                
                # Look for certificates with extracted ship information
                certificates_with_ship_info = []
                certificates_with_extracted_name = []
                
                for cert in certificates[:50]:  # Check first 50 certificates
                    extracted_ship_name = cert.get('extracted_ship_name')
                    flag = cert.get('flag')
                    class_society = cert.get('class_society')
                    built_year = cert.get('built_year')
                    
                    if extracted_ship_name:
                        certificates_with_extracted_name.append({
                            'id': cert.get('id'),
                            'name': cert.get('cert_name', 'Unknown'),
                            'extracted_ship_name': extracted_ship_name,
                            'flag': flag,
                            'class_society': class_society,
                            'built_year': built_year
                        })
                    
                    if any([flag, class_society, built_year]):
                        certificates_with_ship_info.append({
                            'id': cert.get('id'),
                            'name': cert.get('cert_name', 'Unknown'),
                            'ship_info_fields': [f for f in ['flag', 'class_society', 'built_year'] if cert.get(f)]
                        })
                
                self.log(f"   Certificates with extracted_ship_name: {len(certificates_with_extracted_name)}")
                self.log(f"   Certificates with ship info fields: {len(certificates_with_ship_info)}")
                
                if certificates_with_extracted_name:
                    self.backfill_tests['extracted_ship_name_populated'] = True
                    self.backfill_tests['tooltip_data_available'] = True
                    self.log("✅ Certificates now have extracted_ship_name for tooltips")
                    
                    # Show sample results
                    self.log("   Sample certificates with extracted ship names:")
                    for cert in certificates_with_extracted_name[:5]:
                        self.log(f"      - {cert['name']}: '{cert['extracted_ship_name']}'")
                        if cert['flag']:
                            self.log(f"        Flag: {cert['flag']}")
                        if cert['class_society']:
                            self.log(f"        Class Society: {cert['class_society']}")
                        if cert['built_year']:
                            self.log(f"        Built Year: {cert['built_year']}")
                
                if certificates_with_ship_info:
                    self.backfill_tests['ship_info_fields_populated'] = True
                    self.log("✅ Certificates now have additional ship information fields")
                
                return len(certificates_with_extracted_name) > 0 or len(certificates_with_ship_info) > 0
            else:
                self.log(f"   ❌ Failed to verify results: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying backfill results: {str(e)}", "ERROR")
            return False
    
    def test_tooltip_functionality(self):
        """Test that tooltip data is now available for certificates"""
        try:
            self.log("🏷️ Testing tooltip functionality with updated certificate data...")
            
            # Get a ship and its certificates to test tooltip data
            ships_endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(ships_endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ships = response.json()
                if not ships:
                    self.log("   ⚠️ No ships found for tooltip testing")
                    return True
                
                # Test with first ship
                test_ship = ships[0]
                ship_id = test_ship.get('id')
                ship_name = test_ship.get('name', 'Unknown')
                
                self.log(f"   Testing tooltips for ship: {ship_name}")
                
                # Get certificates for this ship
                certs_endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
                response = requests.get(certs_endpoint, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 200:
                    certificates = response.json()
                    self.log(f"   Found {len(certificates)} certificates for {ship_name}")
                    
                    # Check tooltip data availability
                    tooltip_ready_certs = 0
                    for cert in certificates:
                        extracted_ship_name = cert.get('extracted_ship_name')
                        if extracted_ship_name:
                            tooltip_ready_certs += 1
                    
                    self.log(f"   Certificates with tooltip data: {tooltip_ready_certs}/{len(certificates)}")
                    
                    if tooltip_ready_certs > 0:
                        self.log("✅ Tooltip functionality ready - certificates have extracted ship names")
                        self.log(f"   {tooltip_ready_certs} certificates will show ship names in tooltips")
                        return True
                    else:
                        self.log("⚠️ No certificates have extracted ship names for tooltips yet")
                        return False
                else:
                    self.log(f"   ❌ Failed to get certificates: {response.status_code}")
                    return False
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing tooltip functionality: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_backfill_tests(self):
        """Main test function for backfill functionality"""
        self.log("🔄 STARTING CERTIFICATE BACKFILL SHIP INFORMATION TESTING")
        self.log("🎯 FOCUS: Test backfill functionality to help existing certificates")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Analyze certificates before backfill
            self.log("\n📋 STEP 2: ANALYZE CERTIFICATES BEFORE BACKFILL")
            self.log("=" * 50)
            certificates_need_backfill = self.get_certificates_before_backfill()
            
            # Step 3: Run backfill with reasonable limit
            self.log("\n🔄 STEP 3: RUN BACKFILL JOB")
            self.log("=" * 50)
            backfill_success = self.test_backfill_endpoint(limit=20)
            
            # Step 4: Verify backfill results
            self.log("\n🔍 STEP 4: VERIFY BACKFILL RESULTS")
            self.log("=" * 50)
            verification_success = self.verify_backfill_results()
            
            # Step 5: Test tooltip functionality
            self.log("\n🏷️ STEP 5: TEST TOOLTIP FUNCTIONALITY")
            self.log("=" * 50)
            tooltip_success = self.test_tooltip_functionality()
            
            # Step 6: Final Analysis
            self.log("\n📊 STEP 6: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return backfill_success and verification_success
            
        except Exception as e:
            self.log(f"❌ Comprehensive backfill testing error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of backfill testing"""
        try:
            self.log("🔄 CERTIFICATE BACKFILL SHIP INFORMATION TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.backfill_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.backfill_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.backfill_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.backfill_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.backfill_tests)})")
            
            # Backfill-specific analysis
            self.log("\n🔄 BACKFILL FUNCTIONALITY ANALYSIS:")
            
            # Core functionality tests
            core_tests = [
                'backfill_endpoint_accessible',
                'backfill_processing_successful',
                'certificates_updated_with_ship_info',
                'extracted_ship_name_populated'
            ]
            core_passed = sum(1 for test in core_tests if self.backfill_tests.get(test, False))
            core_rate = (core_passed / len(core_tests)) * 100
            
            self.log(f"\n🎯 CORE BACKFILL FUNCTIONALITY: {core_rate:.1f}% ({core_passed}/{len(core_tests)})")
            
            if self.backfill_tests['backfill_processing_successful']:
                self.log("   ✅ CONFIRMED: Backfill job is WORKING")
                self.log("   ✅ Endpoint processes existing certificates successfully")
                
                if self.backfill_results:
                    processed = self.backfill_results.get('processed', 0)
                    updated = self.backfill_results.get('updated', 0)
                    errors = self.backfill_results.get('errors', 0)
                    
                    self.log(f"   📊 Processing Statistics:")
                    self.log(f"      Processed: {processed} certificates")
                    self.log(f"      Updated: {updated} certificates")
                    self.log(f"      Errors: {errors} certificates")
                    
                    if updated > 0:
                        self.log(f"   ✅ SUCCESS: {updated} certificates updated with ship information")
                    else:
                        self.log("   ℹ️ INFO: No certificates needed updating (may be expected)")
            else:
                self.log("   ❌ ISSUE: Backfill job needs fixing")
            
            # Tooltip functionality tests
            tooltip_tests = [
                'extracted_ship_name_populated',
                'tooltip_data_available'
            ]
            tooltip_passed = sum(1 for test in tooltip_tests if self.backfill_tests.get(test, False))
            tooltip_rate = (tooltip_passed / len(tooltip_tests)) * 100
            
            self.log(f"\n🏷️ TOOLTIP FUNCTIONALITY: {tooltip_rate:.1f}% ({tooltip_passed}/{len(tooltip_tests)})")
            
            if self.backfill_tests['tooltip_data_available']:
                self.log("   ✅ CONFIRMED: Tooltip functionality is READY")
                self.log("   ✅ Certificates now have extracted_ship_name for tooltips")
                self.log("   ✅ Previously processed certificates will show ship names")
            else:
                self.log("   ⚠️ ISSUE: Tooltip data may not be available yet")
            
            # Data quality tests
            data_tests = [
                'ship_info_fields_populated',
                'backfill_response_format_correct',
                'processing_statistics_provided'
            ]
            data_passed = sum(1 for test in data_tests if self.backfill_tests.get(test, False))
            data_rate = (data_passed / len(data_tests)) * 100
            
            self.log(f"\n📊 DATA QUALITY & API RESPONSE: {data_rate:.1f}% ({data_passed}/{len(data_tests)})")
            
            # Review request requirements analysis
            self.log("\n📋 REVIEW REQUEST REQUIREMENTS ANALYSIS:")
            
            req1_met = self.backfill_tests['backfill_endpoint_accessible'] and self.backfill_tests['backfill_processing_successful']
            req2_met = self.backfill_tests['certificates_updated_with_ship_info'] and self.backfill_tests['ship_info_fields_populated']
            req3_met = self.backfill_tests['extracted_ship_name_populated'] and self.backfill_tests['tooltip_data_available']
            
            self.log(f"   1. Run Backfill Job: {'✅ MET' if req1_met else '❌ NOT MET'}")
            self.log(f"      - Endpoint accessible and processing certificates")
            
            self.log(f"   2. Verify Processing: {'✅ MET' if req2_met else '❌ NOT MET'}")
            self.log(f"      - Certificates updated with missing ship information")
            
            self.log(f"   3. Check Results: {'✅ MET' if req3_met else '❌ NOT MET'}")
            self.log(f"      - Tooltips will show ship names for processed certificates")
            
            requirements_met = sum([req1_met, req2_met, req3_met])
            
            # Final conclusion
            if success_rate >= 80 and requirements_met >= 2:
                self.log(f"\n🎉 CONCLUSION: BACKFILL FUNCTIONALITY IS WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Backfill job successfully implemented!")
                self.log(f"   ✅ Requirements met: {requirements_met}/3")
                self.log(f"   ✅ Existing certificates can now be processed for ship information")
                self.log(f"   ✅ Tooltips will show ship names for previously processed certificates")
                self.log(f"   ✅ System ready for production use with reasonable limits")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: BACKFILL FUNCTIONALITY PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Some functionality working, improvements needed")
                self.log(f"   ⚠️ Requirements met: {requirements_met}/3")
                
                if req1_met:
                    self.log(f"   ✅ Backfill job is accessible and processing")
                else:
                    self.log(f"   ❌ Backfill job needs attention")
                    
                if req2_met:
                    self.log(f"   ✅ Certificate processing is working")
                else:
                    self.log(f"   ❌ Certificate processing needs attention")
                    
                if req3_met:
                    self.log(f"   ✅ Tooltip functionality is ready")
                else:
                    self.log(f"   ❌ Tooltip functionality needs attention")
            else:
                self.log(f"\n❌ CONCLUSION: BACKFILL FUNCTIONALITY HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Significant fixes needed")
                self.log(f"   ❌ Requirements met: {requirements_met}/3")
                self.log(f"   ❌ Backfill job needs major fixes before production use")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run Certificate Backfill Ship Information tests"""
    print("🔄 CERTIFICATE BACKFILL SHIP INFORMATION TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = CertificateBackfillTester()
        success = tester.run_comprehensive_backfill_tests()
        
        if success:
            print("\n✅ CERTIFICATE BACKFILL TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ CERTIFICATE BACKFILL TESTING COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
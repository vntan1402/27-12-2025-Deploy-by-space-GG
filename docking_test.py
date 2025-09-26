#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: Docking Date Extraction Logic Testing from CSSC and DD Certificates
Review Request: Test auto-extraction logic cho Last Docking 1 & 2 từ CSSC và DD certificates
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import time
import traceback

# Configuration - Use production backend URL for testing
BACKEND_URL = "https://marine-cert-system.preview.emergentagent.com/api"

class DockingDateExtractionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Docking Date Extraction Logic
        self.docking_tests = {
            'authentication_successful': False,
            'docking_endpoint_working': False,
            'cssc_certificate_found': False,
            'certificate_filtering_working': False,
            'date_extraction_patterns_working': False,
            'assignment_logic_working': False,
            'last_docking_1_extracted': False,
            'last_docking_2_extracted': False,
            'date_validation_working': False,
            'duplicates_removed': False,
            'sorting_working': False,
            'ship_update_working': False,
            'error_handling_working': False
        }
        
        # Test ship ID for SUNSHINE 01 as specified in review request
        self.test_ship_id = "e21c71a2-9543-4f92-990c-72f54292fde8"
        self.test_ship_name = "SUNSHINE 01"
        
        # Expected results from review request
        self.expected_certificate = "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE"
        self.expected_keywords = ['safety construction', 'cssc', 'dry dock', 'dd', 'docking survey']
        self.expected_date_patterns = [
            'dry dock date', 'docking survey date', 'construction survey', 'issued date'
        ]
        
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
            
            response = requests.post(endpoint, json=login_data, timeout=30)
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
                
                self.docking_tests['authentication_successful'] = True
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
    
    def test_docking_date_extraction_endpoint(self):
        """Test the Docking Date Extraction Function"""
        try:
            self.log("🎯 Testing Docking Date Extraction Function...")
            self.log(f"   Target Ship: {self.test_ship_name} (ID: {self.test_ship_id})")
            self.log(f"   FOCUS: Extract Last Docking 1 & 2 from CSSC and DD certificates")
            self.log(f"   Expected: Find CSSC certificates and extract docking dates")
            
            # Test the POST /api/ships/{ship_id}/calculate-docking-dates endpoint
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}/calculate-docking-dates"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Docking Date Extraction endpoint responded successfully")
                self.log(f"   📊 Response: {json.dumps(result, indent=2)}")
                
                # Check if the function is working
                success = result.get('success', False)
                message = result.get('message', '')
                docking_dates = result.get('docking_dates')
                
                self.log(f"   Success: {success}")
                self.log(f"   Message: {message}")
                
                # Check if we got a successful calculation
                if success and docking_dates:
                    self.log("   ✅ Docking Date Extraction successful")
                    self.docking_tests['docking_endpoint_working'] = True
                    
                    # Extract docking dates for verification
                    last_docking_1 = docking_dates.get('last_docking')
                    last_docking_2 = docking_dates.get('last_docking_2')
                    
                    self.log(f"   📊 Extracted Docking Dates:")
                    self.log(f"      Last Docking 1 (Most Recent): {last_docking_1}")
                    self.log(f"      Last Docking 2 (Second Most Recent): {last_docking_2}")
                    
                    # Verify assignment logic
                    if last_docking_1:
                        self.log("   ✅ Last Docking 1 (Most Recent) extracted successfully")
                        self.docking_tests['last_docking_1_extracted'] = True
                        self.docking_tests['assignment_logic_working'] = True
                    
                    if last_docking_2:
                        self.log("   ✅ Last Docking 2 (Second Most Recent) extracted successfully")
                        self.docking_tests['last_docking_2_extracted'] = True
                    
                    # Verify date format (dd/MM/yyyy)
                    if last_docking_1:
                        try:
                            # Check if date is in dd/MM/yyyy format
                            datetime.strptime(last_docking_1, '%d/%m/%Y')
                            self.log("   ✅ Date format verification passed (dd/MM/yyyy)")
                            self.docking_tests['date_validation_working'] = True
                        except ValueError:
                            self.log(f"   ⚠️ Date format may not be dd/MM/yyyy: {last_docking_1}")
                    
                    # Check if dates are properly sorted (most recent first)
                    if last_docking_1 and last_docking_2:
                        try:
                            date1 = datetime.strptime(last_docking_1, '%d/%m/%Y')
                            date2 = datetime.strptime(last_docking_2, '%d/%m/%Y')
                            if date1 >= date2:
                                self.log("   ✅ Sorting verification passed (most recent first)")
                                self.docking_tests['sorting_working'] = True
                            else:
                                self.log("   ❌ Sorting issue: Last Docking 1 should be more recent than Last Docking 2")
                        except ValueError:
                            self.log("   ⚠️ Could not verify sorting due to date format issues")
                
                else:
                    self.log("   ❌ Docking Date Extraction failed or returned no data")
                    self.log(f"      Success: {success}")
                    self.log(f"      Message: {message}")
                
                self.test_results['docking_response'] = result
                return True
                
            else:
                self.log(f"   ❌ Docking Date Extraction failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Docking Date Extraction test error: {str(e)}", "ERROR")
            return False
    
    def test_certificate_filtering_logic(self):
        """Test Certificate Filtering Logic for CSSC and DD certificates"""
        try:
            self.log("🔍 Testing Certificate Filtering Logic...")
            self.log(f"   Expected Keywords: {self.expected_keywords}")
            self.log(f"   Expected Certificate: {self.expected_certificate}")
            
            # Get certificates for SUNSHINE 01 ship
            endpoint = f"{BACKEND_URL}/certificates"
            params = {"ship_id": self.test_ship_id}
            self.log(f"   GET {endpoint}?ship_id={self.test_ship_id}")
            
            response = requests.get(endpoint, params=params, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   ✅ Retrieved {len(certificates)} certificates for {self.test_ship_name}")
                
                # Filter certificates using the same logic as backend
                docking_certs = []
                cssc_cert_found = False
                
                for cert in certificates:
                    cert_name = cert.get('cert_name', '').lower()
                    
                    # Check if it's a docking-related certificate
                    is_docking_cert = any(keyword in cert_name for keyword in self.expected_keywords)
                    
                    if is_docking_cert:
                        docking_certs.append(cert)
                        self.log(f"   ✅ Found docking certificate: {cert.get('cert_name')}")
                        
                        # Check for specific CSSC certificate
                        if "cargo ship safety construction certificate" in cert_name:
                            cssc_cert_found = True
                            self.log(f"   ✅ Found CSSC certificate: {cert.get('cert_name')}")
                            self.log(f"      Certificate Type: {cert.get('cert_type')}")
                            self.log(f"      Valid Date: {cert.get('valid_date')}")
                            self.log(f"      Has Text Content: {bool(cert.get('text_content'))}")
                
                self.log(f"   📊 Certificate Filtering Results:")
                self.log(f"      Total Certificates: {len(certificates)}")
                self.log(f"      Docking-related Certificates: {len(docking_certs)}")
                self.log(f"      CSSC Certificate Found: {cssc_cert_found}")
                
                if len(docking_certs) > 0:
                    self.log("   ✅ Certificate filtering logic working")
                    self.docking_tests['certificate_filtering_working'] = True
                
                if cssc_cert_found:
                    self.log("   ✅ Expected CSSC certificate found")
                    self.docking_tests['cssc_certificate_found'] = True
                
                self.test_results['certificate_filtering'] = {
                    'total_certificates': len(certificates),
                    'docking_certificates': len(docking_certs),
                    'cssc_found': cssc_cert_found,
                    'docking_certs': docking_certs
                }
                
                return True
                
            else:
                self.log(f"   ❌ Certificate retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Certificate filtering test error: {str(e)}", "ERROR")
            return False

    def test_date_extraction_patterns(self):
        """Test Date Extraction Patterns from certificate text content"""
        try:
            self.log("🔍 Testing Date Extraction Patterns...")
            self.log(f"   Expected Patterns: {self.expected_date_patterns}")
            
            # Get certificates with text content
            certificate_filtering = self.test_results.get('certificate_filtering', {})
            docking_certs = certificate_filtering.get('docking_certs', [])
            
            if not docking_certs:
                self.log("   ⚠️ No docking certificates available for pattern testing")
                return False
            
            patterns_found = []
            dates_extracted = []
            
            for cert in docking_certs:
                cert_name = cert.get('cert_name', 'Unknown')
                text_content = cert.get('text_content', '')
                
                if text_content:
                    self.log(f"   📄 Analyzing certificate: {cert_name}")
                    
                    # Test common date patterns
                    import re
                    date_patterns = [
                        r"dry\s*dock(?:ing)?\s*date[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                        r"docking\s*survey\s*date[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                        r"construction\s*survey[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                        r"issued[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                        r"certificate\s*date[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
                    ]
                    
                    for pattern in date_patterns:
                        matches = re.finditer(pattern, text_content, re.IGNORECASE)
                        for match in matches:
                            date_str = match.group(1)
                            pattern_name = pattern.split('\\')[0].replace('r"', '').replace('[:\\s]+', '')
                            patterns_found.append(pattern_name)
                            dates_extracted.append(date_str)
                            self.log(f"      ✅ Found pattern '{pattern_name}': {date_str}")
                else:
                    self.log(f"   ⚠️ No text content in certificate: {cert_name}")
            
            self.log(f"   📊 Date Extraction Pattern Results:")
            self.log(f"      Patterns Found: {len(set(patterns_found))}")
            self.log(f"      Dates Extracted: {len(dates_extracted)}")
            self.log(f"      Unique Patterns: {list(set(patterns_found))}")
            
            if len(patterns_found) > 0:
                self.log("   ✅ Date extraction patterns working")
                self.docking_tests['date_extraction_patterns_working'] = True
            
            # Test date validation (1980 - current year + 1)
            current_year = datetime.now().year
            valid_dates = []
            
            for date_str in dates_extracted:
                try:
                    # Try to parse the date
                    for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%d/%m/%y', '%d-%m-%y', '%d.%m.%y']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            if parsed_date.year < 100:  # Handle 2-digit years
                                if parsed_date.year > 50:
                                    parsed_date = parsed_date.replace(year=parsed_date.year + 1900)
                                else:
                                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                            
                            if 1980 <= parsed_date.year <= current_year + 1:
                                valid_dates.append(parsed_date)
                                self.log(f"      ✅ Valid date: {date_str} -> {parsed_date.strftime('%Y-%m-%d')}")
                            else:
                                self.log(f"      ⚠️ Date out of range: {date_str} -> {parsed_date.year}")
                            break
                        except ValueError:
                            continue
                except:
                    self.log(f"      ❌ Could not parse date: {date_str}")
            
            if len(valid_dates) > 0:
                self.log("   ✅ Date validation working (1980 - current year + 1)")
                self.docking_tests['date_validation_working'] = True
            
            self.test_results['date_extraction'] = {
                'patterns_found': patterns_found,
                'dates_extracted': dates_extracted,
                'valid_dates': len(valid_dates)
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ Date extraction pattern test error: {str(e)}", "ERROR")
            return False

    def test_assignment_logic(self):
        """Test Assignment Logic for Last Docking 1 & 2"""
        try:
            self.log("🎯 Testing Assignment Logic...")
            self.log("   Expected: Last Docking 1 = Most recent, Last Docking 2 = Second most recent")
            
            # Get the docking response from previous test
            docking_response = self.test_results.get('docking_response', {})
            
            if not docking_response.get('success'):
                self.log("   ⚠️ No successful docking response available for assignment testing")
                return False
            
            docking_dates = docking_response.get('docking_dates', {})
            last_docking_1 = docking_dates.get('last_docking')
            last_docking_2 = docking_dates.get('last_docking_2')
            
            self.log(f"   📊 Assignment Results:")
            self.log(f"      Last Docking 1 (Most Recent): {last_docking_1}")
            self.log(f"      Last Docking 2 (Second Most Recent): {last_docking_2}")
            
            # Test assignment logic
            if last_docking_1:
                self.log("   ✅ Last Docking 1 assigned successfully")
                self.docking_tests['last_docking_1_extracted'] = True
            
            if last_docking_2:
                self.log("   ✅ Last Docking 2 assigned successfully")
                self.docking_tests['last_docking_2_extracted'] = True
            
            # Test chronological order (most recent first)
            if last_docking_1 and last_docking_2:
                try:
                    date1 = datetime.strptime(last_docking_1, '%d/%m/%Y')
                    date2 = datetime.strptime(last_docking_2, '%d/%m/%Y')
                    
                    if date1 >= date2:
                        self.log("   ✅ Assignment logic correct: Last Docking 1 is more recent than Last Docking 2")
                        self.docking_tests['assignment_logic_working'] = True
                    else:
                        self.log("   ❌ Assignment logic error: Last Docking 1 should be more recent")
                        
                    # Calculate time difference
                    time_diff = abs((date1 - date2).days)
                    self.log(f"   📊 Time difference between dockings: {time_diff} days")
                    
                except ValueError as e:
                    self.log(f"   ⚠️ Could not verify chronological order: {e}")
            
            elif last_docking_1 and not last_docking_2:
                self.log("   ✅ Only one docking date found - assignment logic working")
                self.docking_tests['assignment_logic_working'] = True
            
            return True
            
        except Exception as e:
            self.log(f"❌ Assignment logic test error: {str(e)}", "ERROR")
            return False

    def test_integration_and_ship_update(self):
        """Test Integration and Ship Update with calculated docking dates"""
        try:
            self.log("🔗 Testing Integration and Ship Update...")
            
            # Get current ship data before update
            ship_endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
            self.log(f"   GET {ship_endpoint} (before update)")
            
            before_response = requests.get(ship_endpoint, headers=self.get_headers(), timeout=30)
            
            if before_response.status_code == 200:
                before_data = before_response.json()
                before_last_docking = before_data.get('last_docking')
                before_last_docking_2 = before_data.get('last_docking_2')
                
                self.log(f"   📊 Ship data before docking calculation:")
                self.log(f"      Last Docking: {before_last_docking}")
                self.log(f"      Last Docking 2: {before_last_docking_2}")
                
                # Trigger docking date calculation (should update ship)
                calc_endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}/calculate-docking-dates"
                calc_response = requests.post(calc_endpoint, headers=self.get_headers(), timeout=30)
                
                if calc_response.status_code == 200:
                    calc_result = calc_response.json()
                    
                    if calc_result.get('success'):
                        self.log("   ✅ Docking date calculation successful")
                        
                        # Get ship data after update
                        after_response = requests.get(ship_endpoint, headers=self.get_headers(), timeout=30)
                        
                        if after_response.status_code == 200:
                            after_data = after_response.json()
                            after_last_docking = after_data.get('last_docking')
                            after_last_docking_2 = after_data.get('last_docking_2')
                            
                            self.log(f"   📊 Ship data after docking calculation:")
                            self.log(f"      Last Docking: {after_last_docking}")
                            self.log(f"      Last Docking 2: {after_last_docking_2}")
                            
                            # Check if ship was updated
                            ship_updated = False
                            if (str(before_last_docking) != str(after_last_docking) or 
                                str(before_last_docking_2) != str(after_last_docking_2)):
                                ship_updated = True
                                self.log("   ✅ Ship updated with calculated docking dates")
                                self.docking_tests['ship_update_working'] = True
                            else:
                                self.log("   ⚠️ Ship data unchanged - may already have correct dates")
                            
                            # Verify response format
                            calc_docking_dates = calc_result.get('docking_dates', {})
                            expected_fields = ['last_docking', 'last_docking_2']
                            
                            response_format_ok = True
                            for field in expected_fields:
                                if field in calc_docking_dates:
                                    value = calc_docking_dates[field]
                                    if value:
                                        try:
                                            # Verify dd/MM/yyyy format
                                            datetime.strptime(value, '%d/%m/%Y')
                                            self.log(f"   ✅ Response format correct for {field}: {value}")
                                        except ValueError:
                                            self.log(f"   ❌ Response format incorrect for {field}: {value}")
                                            response_format_ok = False
                            
                            if response_format_ok:
                                self.log("   ✅ Response format verification passed")
                            
                            self.test_results['integration_test'] = {
                                'before_data': before_data,
                                'after_data': after_data,
                                'ship_updated': ship_updated,
                                'calc_result': calc_result
                            }
                            
                            return True
                        else:
                            self.log(f"   ❌ Could not get ship data after update: {after_response.status_code}")
                    else:
                        self.log(f"   ❌ Docking calculation failed: {calc_result.get('message')}")
                else:
                    self.log(f"   ❌ Docking calculation request failed: {calc_response.status_code}")
            else:
                self.log(f"   ❌ Could not get ship data before update: {before_response.status_code}")
            
            return False
            
        except Exception as e:
            self.log(f"❌ Integration test error: {str(e)}", "ERROR")
            return False

    def test_error_handling(self):
        """Test Error Handling for edge cases"""
        try:
            self.log("🧪 Testing Error Handling...")
            
            # Test 1: Non-existent ship ID
            fake_ship_id = "00000000-0000-0000-0000-000000000000"
            fake_endpoint = f"{BACKEND_URL}/ships/{fake_ship_id}/calculate-docking-dates"
            self.log(f"   Testing with non-existent ship ID: {fake_ship_id}")
            
            fake_response = requests.post(fake_endpoint, headers=self.get_headers(), timeout=10)
            
            if fake_response.status_code == 404:
                self.log("   ✅ Proper error handling for non-existent ship (404)")
                self.docking_tests['error_handling_working'] = True
            else:
                self.log(f"   ⚠️ Unexpected response for non-existent ship: {fake_response.status_code}")
            
            # Test 2: Ship with no certificates
            # We'll create a test ship without certificates
            test_ship_data = {
                "name": "TEST SHIP NO CERTS",
                "imo": "9999999",
                "flag": "PANAMA",
                "ship_type": "General Cargo",
                "company": "AMCSC"
            }
            
            create_endpoint = f"{BACKEND_URL}/ships"
            create_response = requests.post(create_endpoint, json=test_ship_data, headers=self.get_headers(), timeout=10)
            
            if create_response.status_code == 200:
                test_ship = create_response.json()
                test_ship_id = test_ship.get('id')
                
                self.log(f"   Created test ship without certificates: {test_ship_id}")
                
                # Test docking calculation on ship with no certificates
                no_cert_endpoint = f"{BACKEND_URL}/ships/{test_ship_id}/calculate-docking-dates"
                no_cert_response = requests.post(no_cert_endpoint, headers=self.get_headers(), timeout=10)
                
                if no_cert_response.status_code == 200:
                    no_cert_result = no_cert_response.json()
                    
                    if not no_cert_result.get('success'):
                        expected_message = "No docking dates found in CSSC or Dry Docking certificates"
                        actual_message = no_cert_result.get('message', '')
                        
                        if expected_message in actual_message:
                            self.log("   ✅ Proper error handling for ship with no certificates")
                        else:
                            self.log(f"   ⚠️ Unexpected message: {actual_message}")
                    else:
                        self.log("   ⚠️ Expected failure for ship with no certificates")
                
                # Clean up test ship
                delete_endpoint = f"{BACKEND_URL}/ships/{test_ship_id}"
                requests.delete(delete_endpoint, headers=self.get_headers(), timeout=10)
                self.log(f"   Cleaned up test ship: {test_ship_id}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error handling test error: {str(e)}", "ERROR")
            return False

    def run_comprehensive_docking_tests(self):
        """Main test function for Docking Date Extraction Logic"""
        self.log("🎯 STARTING DOCKING DATE EXTRACTION TESTING")
        self.log("🔍 Focus: Test auto-extraction logic cho Last Docking 1 & 2 từ CSSC và DD certificates")
        self.log("📋 Review Request: Test docking date extraction function")
        self.log("🎯 Expected: Find CSSC certificates and extract docking dates")
        self.log("🎯 Target: Last Docking 1 = Most recent, Last Docking 2 = Second most recent")
        self.log("=" * 100)
        
        # Step 1: Authenticate
        self.log("\n🔐 STEP 1: AUTHENTICATION")
        self.log("=" * 50)
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Test Certificate Filtering Logic
        self.log("\n🔍 STEP 2: CERTIFICATE FILTERING LOGIC")
        self.log("=" * 50)
        self.test_certificate_filtering_logic()
        
        # Step 3: Test Date Extraction Patterns
        self.log("\n🔍 STEP 3: DATE EXTRACTION PATTERNS")
        self.log("=" * 50)
        self.test_date_extraction_patterns()
        
        # Step 4: Test Docking Date Extraction Endpoint
        self.log("\n🎯 STEP 4: DOCKING DATE EXTRACTION ENDPOINT")
        self.log("=" * 50)
        self.test_docking_date_extraction_endpoint()
        
        # Step 5: Test Assignment Logic
        self.log("\n🎯 STEP 5: ASSIGNMENT LOGIC")
        self.log("=" * 50)
        self.test_assignment_logic()
        
        # Step 6: Test Integration and Ship Update
        self.log("\n🔗 STEP 6: INTEGRATION AND SHIP UPDATE")
        self.log("=" * 50)
        self.test_integration_and_ship_update()
        
        # Step 7: Test Error Handling
        self.log("\n🧪 STEP 7: ERROR HANDLING")
        self.log("=" * 50)
        self.test_error_handling()
        
        # Step 8: Final analysis
        self.log("\n📊 STEP 8: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_analysis()
        
        return True
    
    def provide_final_analysis(self):
        """Provide final analysis of the Docking Date Extraction testing"""
        try:
            self.log("🎯 DOCKING DATE EXTRACTION TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.docking_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ DOCKING TESTS PASSED ({len(passed_tests)}/{len(self.docking_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test}")
            
            if failed_tests:
                self.log(f"\n❌ DOCKING TESTS FAILED ({len(failed_tests)}/{len(self.docking_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.docking_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")
            
            # Provide specific analysis
            self.log("\n🎯 SPECIFIC ANALYSIS:")
            
            if self.docking_tests['docking_endpoint_working']:
                self.log("   ✅ Docking Date Extraction Function is working correctly")
            else:
                self.log("   ❌ Docking Date Extraction Function has issues")
            
            if self.docking_tests['certificate_filtering_working']:
                self.log("   ✅ Certificate filtering logic is working (finds CSSC/DD certificates)")
            else:
                self.log("   ❌ Certificate filtering logic needs attention")
            
            if self.docking_tests['date_extraction_patterns_working']:
                self.log("   ✅ Date extraction patterns are working")
            else:
                self.log("   ❌ Date extraction patterns need improvement")
            
            if self.docking_tests['assignment_logic_working']:
                self.log("   ✅ Assignment logic is correct (Last Docking 1 = most recent, Last Docking 2 = second most recent)")
            else:
                self.log("   ❌ Assignment logic needs fixing")
            
            if self.docking_tests['ship_update_working']:
                self.log("   ✅ Ship update integration is working")
            else:
                self.log("   ❌ Ship update integration has issues")
            
            # Review request compliance
            self.log("\n📋 REVIEW REQUEST COMPLIANCE:")
            
            review_requirements = [
                ('Authentication with admin1/123456', self.docking_tests['authentication_successful']),
                ('Docking Date Extraction Function working', self.docking_tests['docking_endpoint_working']),
                ('CSSC certificate found', self.docking_tests['cssc_certificate_found']),
                ('Certificate filtering working', self.docking_tests['certificate_filtering_working']),
                ('Date extraction patterns working', self.docking_tests['date_extraction_patterns_working']),
                ('Assignment logic working', self.docking_tests['assignment_logic_working']),
                ('Error handling working', self.docking_tests['error_handling_working'])
            ]
            
            for requirement, status in review_requirements:
                status_icon = "✅" if status else "❌"
                self.log(f"   {status_icon} {requirement}")
            
            # Final recommendation
            if success_rate >= 80:
                self.log("\n🎉 CONCLUSION: Docking Date Extraction logic is working well!")
                self.log("   The system successfully extracts Last Docking 1 & 2 from CSSC and DD certificates.")
            elif success_rate >= 60:
                self.log("\n⚠️ CONCLUSION: Docking Date Extraction logic is partially working.")
                self.log("   Some components need attention but core functionality is present.")
            else:
                self.log("\n❌ CONCLUSION: Docking Date Extraction logic needs significant work.")
                self.log("   Multiple components are not working as expected.")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run the docking date extraction tests"""
    print("🚀 Starting Docking Date Extraction Testing...")
    
    tester = DockingDateExtractionTester()
    
    try:
        success = tester.run_comprehensive_docking_tests()
        
        if success:
            print("\n✅ Docking Date Extraction testing completed successfully!")
        else:
            print("\n❌ Docking Date Extraction testing completed with issues!")
            
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed with error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
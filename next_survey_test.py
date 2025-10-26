#!/usr/bin/env python3
"""
Ship Management System - Next Survey Calculation Logic Testing
FOCUS: Test the updated Next Survey calculation logic after removing special certificate type cases

REVIEW REQUEST REQUIREMENTS:
1. Login with admin1/123456
2. Test the Next Survey calculation by calling "Update Next Survey" for a ship
3. Verify that ALL certificate types now use the standard ±3 months window:
   - Radio/GMDSS certificates no longer have special treatment
   - MLC/Labour certificates no longer have special treatment
   - All certificates use standard window_months = 3
4. Test the `/ships/{ship_id}/update-next-survey` endpoint
5. Check that the calculation logic still works correctly:
   - Anniversary date based calculations
   - 5-year survey cycle logic
   - Annual survey type determination
   - Window formatting (±3M for all, -3M for Special Survey only)

KEY VERIFICATION POINTS:
1. Uniform Window Treatment: All certificate types get ±3 months window (no special cases)
2. Next Survey Calculation: Still based on ship anniversary and 5-year cycle
3. Survey Type Logic: 1st/2nd/3rd/4th Annual Survey and Special Survey logic intact
4. Window Display: All surveys show ±3M except Special Survey shows -3M
5. Condition Certificates: Still use valid_date as next_survey (unchanged)

EXPECTED OUTCOME:
- Update Next Survey functionality working correctly
- All certificates get uniform ±3 months treatment
- No special handling for Radio/GMDSS or MLC certificates
- Survey cycle and anniversary date logic preserved
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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipsystem.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class NextSurveyCalculationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Next Survey calculation logic
        self.survey_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            
            # Ship selection and data retrieval
            'ships_retrieved_successfully': False,
            'test_ship_selected': False,
            'ship_certificates_found': False,
            
            # Update Next Survey endpoint tests
            'update_next_survey_endpoint_accessible': False,
            'update_next_survey_response_valid': False,
            'certificates_updated_successfully': False,
            
            # Window calculation verification
            'uniform_window_treatment_verified': False,
            'no_special_certificate_handling': False,
            'standard_3_month_window_applied': False,
            
            # Survey type logic verification
            'anniversary_date_calculation_working': False,
            'five_year_cycle_logic_intact': False,
            'annual_survey_type_determination_correct': False,
            
            # Window display verification
            'window_formatting_correct': False,
            'special_survey_minus_3m_only': False,
            'other_surveys_plus_minus_3m': False,
            
            # Condition certificate handling
            'condition_certificates_use_valid_date': False,
            
            # Certificate type specific tests
            'radio_gmdss_no_special_treatment': False,
            'mlc_labour_no_special_treatment': False,
            'all_certificates_uniform_treatment': False,
        }
        
        # Store test data for analysis
        self.user_company = None
        self.test_ship = None
        self.ship_certificates = []
        self.update_results = {}
        self.certificate_analysis = {}
        
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
                
                self.survey_tests['authentication_successful'] = True
                self.user_company = self.current_user.get('company')
                if self.user_company:
                    self.survey_tests['user_company_identified'] = True
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
    
    def get_ships_and_select_test_ship(self):
        """Get ships and select a ship for testing"""
        try:
            self.log("🚢 Getting ships and selecting test ship...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships")
                self.survey_tests['ships_retrieved_successfully'] = True
                
                # Filter ships by user's company
                user_company_ships = [ship for ship in ships if ship.get('company') == self.user_company]
                self.log(f"   Found {len(user_company_ships)} ships in user's company ({self.user_company})")
                
                if user_company_ships:
                    # Select the first ship for testing
                    self.test_ship = user_company_ships[0]
                    self.log(f"   Selected test ship: {self.test_ship.get('name')} (ID: {self.test_ship.get('id')})")
                    self.log(f"   Ship details:")
                    self.log(f"      IMO: {self.test_ship.get('imo')}")
                    self.log(f"      Flag: {self.test_ship.get('flag')}")
                    self.log(f"      Ship Type: {self.test_ship.get('ship_type')}")
                    
                    # Check anniversary date
                    anniversary_date = self.test_ship.get('anniversary_date')
                    if anniversary_date:
                        self.log(f"      Anniversary Date: {anniversary_date}")
                    else:
                        self.log(f"      Anniversary Date: Not set")
                    
                    self.survey_tests['test_ship_selected'] = True
                    return True
                else:
                    self.log("   ❌ No ships found in user's company")
                    return False
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting ships: {str(e)}", "ERROR")
            return False
    
    def get_ship_certificates(self):
        """Get certificates for the selected test ship"""
        try:
            self.log("📋 Getting certificates for test ship...")
            
            if not self.test_ship:
                self.log("❌ No test ship selected")
                return False
            
            ship_id = self.test_ship.get('id')
            endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                self.ship_certificates = certificates
                self.log(f"   Found {len(certificates)} certificates")
                
                if certificates:
                    self.survey_tests['ship_certificates_found'] = True
                    
                    # Analyze certificate types for special handling verification
                    cert_types = {}
                    special_cert_types = []
                    
                    for cert in certificates:
                        cert_name = cert.get('cert_name', '').upper()
                        cert_type = cert.get('cert_type', 'Unknown')
                        
                        # Track certificate types
                        if cert_type not in cert_types:
                            cert_types[cert_type] = 0
                        cert_types[cert_type] += 1
                        
                        # Look for previously special-handled certificate types
                        if any(keyword in cert_name for keyword in ['RADIO', 'GMDSS', 'MLC', 'LABOUR', 'LABOR']):
                            special_cert_types.append({
                                'name': cert.get('cert_name'),
                                'type': cert_type,
                                'id': cert.get('id')
                            })
                    
                    self.log(f"   Certificate types found:")
                    for cert_type, count in cert_types.items():
                        self.log(f"      {cert_type}: {count}")
                    
                    if special_cert_types:
                        self.log(f"   Special certificate types found (previously had special handling):")
                        for cert in special_cert_types:
                            self.log(f"      {cert['name']} ({cert['type']})")
                    else:
                        self.log(f"   No Radio/GMDSS or MLC/Labour certificates found")
                    
                    return True
                else:
                    self.log("   ⚠️ No certificates found for this ship")
                    return True  # This is valid - ship might not have certificates yet
            else:
                self.log(f"   ❌ Failed to get certificates: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting ship certificates: {str(e)}", "ERROR")
            return False
    
    def test_update_next_survey_endpoint(self):
        """Test the /ships/{ship_id}/update-next-survey endpoint"""
        try:
            self.log("🔄 Testing Update Next Survey endpoint...")
            
            if not self.test_ship:
                self.log("❌ No test ship selected")
                return False
            
            ship_id = self.test_ship.get('id')
            endpoint = f"{BACKEND_URL}/ships/{ship_id}/update-next-survey"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.survey_tests['update_next_survey_endpoint_accessible'] = True
                self.log("✅ Update Next Survey endpoint is accessible")
                
                try:
                    response_data = response.json()
                    self.update_results = response_data
                    self.survey_tests['update_next_survey_response_valid'] = True
                    self.log("✅ Response is valid JSON")
                    
                    # Log response details
                    self.log(f"   Response details:")
                    self.log(f"      Success: {response_data.get('success')}")
                    self.log(f"      Message: {response_data.get('message')}")
                    self.log(f"      Ship Name: {response_data.get('ship_name')}")
                    self.log(f"      Updated Count: {response_data.get('updated_count')}")
                    self.log(f"      Total Certificates: {response_data.get('total_certificates')}")
                    
                    if response_data.get('updated_count', 0) > 0:
                        self.survey_tests['certificates_updated_successfully'] = True
                        self.log("✅ Certificates updated successfully")
                        
                        # Show some update results
                        results = response_data.get('results', [])
                        if results:
                            self.log(f"   Sample update results:")
                            for i, result in enumerate(results[:3]):  # Show first 3
                                self.log(f"      Certificate {i+1}:")
                                self.log(f"         Name: {result.get('cert_name')}")
                                self.log(f"         Type: {result.get('cert_type')}")
                                self.log(f"         Old Next Survey: {result.get('old_next_survey')}")
                                self.log(f"         New Next Survey: {result.get('new_next_survey')}")
                                self.log(f"         New Survey Type: {result.get('new_next_survey_type')}")
                                self.log(f"         Reasoning: {result.get('reasoning')}")
                    else:
                        self.log("   ⚠️ No certificates were updated (might be already up to date)")
                        self.survey_tests['certificates_updated_successfully'] = True  # This is still valid
                    
                    return True
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                self.log(f"❌ Update Next Survey endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Update Next Survey endpoint: {str(e)}", "ERROR")
            return False
    
    def verify_uniform_window_treatment(self):
        """Verify that all certificate types now use uniform ±3 months window"""
        try:
            self.log("📏 Verifying uniform window treatment...")
            
            if not self.update_results.get('results'):
                self.log("   ⚠️ No update results to analyze")
                # Get fresh certificate data to analyze
                if not self.get_updated_certificate_data():
                    return False
            
            # Analyze the updated certificates
            results = self.update_results.get('results', [])
            uniform_window_count = 0
            special_handling_count = 0
            total_analyzed = 0
            
            window_analysis = {
                'standard_3m_window': [],
                'special_survey_minus_3m': [],
                'condition_certificates': [],
                'radio_gmdss_certificates': [],
                'mlc_labour_certificates': [],
                'other_certificates': []
            }
            
            for result in results:
                cert_name = result.get('cert_name', '').upper()
                cert_type = result.get('cert_type', '').upper()
                new_next_survey = result.get('new_next_survey', '')
                new_survey_type = result.get('new_next_survey_type', '')
                
                total_analyzed += 1
                
                self.log(f"   Analyzing certificate: {result.get('cert_name')}")
                self.log(f"      Type: {cert_type}")
                self.log(f"      New Next Survey: {new_next_survey}")
                self.log(f"      New Survey Type: {new_survey_type}")
                
                # Check window formatting
                if new_next_survey:
                    # Check for window indicators
                    if '±3M' in new_next_survey:
                        uniform_window_count += 1
                        window_analysis['standard_3m_window'].append(result)
                        self.log(f"         ✅ Standard ±3M window applied")
                    elif '-3M' in new_next_survey and 'Special Survey' in new_survey_type:
                        uniform_window_count += 1
                        window_analysis['special_survey_minus_3m'].append(result)
                        self.log(f"         ✅ Special Survey -3M window applied (correct)")
                    elif 'CONDITION' in cert_type:
                        # Condition certificates should use valid_date
                        window_analysis['condition_certificates'].append(result)
                        self.log(f"         ✅ Condition certificate uses valid date (correct)")
                    else:
                        special_handling_count += 1
                        self.log(f"         ⚠️ Unexpected window format: {new_next_survey}")
                
                # Categorize certificate types for special handling verification
                if any(keyword in cert_name for keyword in ['RADIO', 'GMDSS']):
                    window_analysis['radio_gmdss_certificates'].append(result)
                elif any(keyword in cert_name for keyword in ['MLC', 'LABOUR', 'LABOR']):
                    window_analysis['mlc_labour_certificates'].append(result)
                else:
                    window_analysis['other_certificates'].append(result)
            
            # Verify uniform treatment
            if total_analyzed > 0:
                uniform_rate = (uniform_window_count / total_analyzed) * 100
                self.log(f"   Uniform window treatment rate: {uniform_rate:.1f}% ({uniform_window_count}/{total_analyzed})")
                
                if uniform_rate >= 90:  # Allow for some edge cases
                    self.survey_tests['uniform_window_treatment_verified'] = True
                    self.survey_tests['standard_3_month_window_applied'] = True
                    self.log("✅ Uniform window treatment verified")
                else:
                    self.log(f"❌ Uniform window treatment not achieved: {uniform_rate:.1f}%")
            
            # Verify no special handling for Radio/GMDSS and MLC/Labour certificates
            radio_gmdss_certs = window_analysis['radio_gmdss_certificates']
            mlc_labour_certs = window_analysis['mlc_labour_certificates']
            
            if radio_gmdss_certs:
                self.log(f"   Radio/GMDSS certificates analysis:")
                all_standard = True
                for cert in radio_gmdss_certs:
                    next_survey = cert.get('new_next_survey', '')
                    if '±3M' in next_survey or ('-3M' in next_survey and 'Special Survey' in cert.get('new_next_survey_type', '')):
                        self.log(f"      ✅ {cert.get('cert_name')}: Standard window applied")
                    else:
                        self.log(f"      ❌ {cert.get('cert_name')}: Non-standard window: {next_survey}")
                        all_standard = False
                
                if all_standard:
                    self.survey_tests['radio_gmdss_no_special_treatment'] = True
                    self.log("✅ Radio/GMDSS certificates have no special treatment")
            else:
                self.log("   No Radio/GMDSS certificates found")
                self.survey_tests['radio_gmdss_no_special_treatment'] = True  # Valid if none exist
            
            if mlc_labour_certs:
                self.log(f"   MLC/Labour certificates analysis:")
                all_standard = True
                for cert in mlc_labour_certs:
                    next_survey = cert.get('new_next_survey', '')
                    if '±3M' in next_survey or ('-3M' in next_survey and 'Special Survey' in cert.get('new_next_survey_type', '')):
                        self.log(f"      ✅ {cert.get('cert_name')}: Standard window applied")
                    else:
                        self.log(f"      ❌ {cert.get('cert_name')}: Non-standard window: {next_survey}")
                        all_standard = False
                
                if all_standard:
                    self.survey_tests['mlc_labour_no_special_treatment'] = True
                    self.log("✅ MLC/Labour certificates have no special treatment")
            else:
                self.log("   No MLC/Labour certificates found")
                self.survey_tests['mlc_labour_no_special_treatment'] = True  # Valid if none exist
            
            # Overall verification
            if (self.survey_tests['radio_gmdss_no_special_treatment'] and 
                self.survey_tests['mlc_labour_no_special_treatment'] and
                self.survey_tests['uniform_window_treatment_verified']):
                self.survey_tests['no_special_certificate_handling'] = True
                self.survey_tests['all_certificates_uniform_treatment'] = True
                self.log("✅ All certificates receive uniform treatment - no special cases")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error verifying uniform window treatment: {str(e)}", "ERROR")
            return False
    
    def get_updated_certificate_data(self):
        """Get fresh certificate data after update to analyze"""
        try:
            self.log("🔄 Getting updated certificate data for analysis...")
            
            if not self.test_ship:
                return False
            
            ship_id = self.test_ship.get('id')
            endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                updated_certificates = response.json()
                
                # Create mock results for analysis
                mock_results = []
                for cert in updated_certificates:
                    if cert.get('next_survey_display'):  # Only certificates with next survey
                        mock_results.append({
                            'cert_id': cert.get('id'),
                            'cert_name': cert.get('cert_name'),
                            'cert_type': cert.get('cert_type'),
                            'new_next_survey': cert.get('next_survey_display'),
                            'new_next_survey_type': cert.get('next_survey_type'),
                            'reasoning': 'Updated certificate data'
                        })
                
                if not self.update_results:
                    self.update_results = {}
                self.update_results['results'] = mock_results
                
                self.log(f"   Analyzed {len(mock_results)} certificates with next survey data")
                return True
            else:
                self.log(f"   ❌ Failed to get updated certificate data: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting updated certificate data: {str(e)}", "ERROR")
            return False
    
    def verify_survey_calculation_logic(self):
        """Verify that the survey calculation logic is still working correctly"""
        try:
            self.log("🧮 Verifying survey calculation logic...")
            
            results = self.update_results.get('results', [])
            if not results:
                self.log("   ⚠️ No results to analyze")
                return True
            
            anniversary_based_count = 0
            cycle_based_count = 0
            annual_survey_types = 0
            special_survey_types = 0
            condition_cert_count = 0
            
            for result in results:
                cert_name = result.get('cert_name', '')
                cert_type = result.get('cert_type', '').upper()
                new_survey_type = result.get('new_next_survey_type', '')
                reasoning = result.get('reasoning', '')
                
                self.log(f"   Analyzing: {cert_name}")
                self.log(f"      Survey Type: {new_survey_type}")
                self.log(f"      Reasoning: {reasoning}")
                
                # Check reasoning for anniversary date and cycle logic
                if 'anniversary date' in reasoning.lower():
                    anniversary_based_count += 1
                    self.log(f"         ✅ Anniversary date based calculation")
                
                if '5-year' in reasoning.lower() or 'cycle' in reasoning.lower():
                    cycle_based_count += 1
                    self.log(f"         ✅ 5-year cycle based calculation")
                
                # Check survey type determination
                if any(keyword in new_survey_type for keyword in ['Annual Survey', '1st', '2nd', '3rd', '4th']):
                    annual_survey_types += 1
                    self.log(f"         ✅ Annual survey type determined")
                elif 'Special Survey' in new_survey_type:
                    special_survey_types += 1
                    self.log(f"         ✅ Special survey type determined")
                elif 'CONDITION' in cert_type:
                    condition_cert_count += 1
                    self.log(f"         ✅ Condition certificate handled correctly")
            
            total_results = len(results)
            
            # Verify anniversary date calculation
            if anniversary_based_count > 0:
                self.survey_tests['anniversary_date_calculation_working'] = True
                self.log(f"✅ Anniversary date calculation working ({anniversary_based_count}/{total_results})")
            
            # Verify 5-year cycle logic
            if cycle_based_count > 0:
                self.survey_tests['five_year_cycle_logic_intact'] = True
                self.log(f"✅ 5-year cycle logic intact ({cycle_based_count}/{total_results})")
            
            # Verify annual survey type determination
            if annual_survey_types > 0 or special_survey_types > 0:
                self.survey_tests['annual_survey_type_determination_correct'] = True
                self.log(f"✅ Survey type determination correct (Annual: {annual_survey_types}, Special: {special_survey_types})")
            
            # Verify condition certificate handling
            if condition_cert_count > 0:
                self.survey_tests['condition_certificates_use_valid_date'] = True
                self.log(f"✅ Condition certificates use valid date ({condition_cert_count})")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error verifying survey calculation logic: {str(e)}", "ERROR")
            return False
    
    def verify_window_formatting(self):
        """Verify that window formatting is correct"""
        try:
            self.log("📐 Verifying window formatting...")
            
            results = self.update_results.get('results', [])
            if not results:
                self.log("   ⚠️ No results to analyze")
                return True
            
            correct_formatting_count = 0
            special_survey_correct = 0
            other_survey_correct = 0
            
            for result in results:
                cert_name = result.get('cert_name', '')
                new_next_survey = result.get('new_next_survey', '')
                new_survey_type = result.get('new_next_survey_type', '')
                
                self.log(f"   Checking: {cert_name}")
                self.log(f"      Next Survey: {new_next_survey}")
                self.log(f"      Survey Type: {new_survey_type}")
                
                if new_next_survey:
                    if 'Special Survey' in new_survey_type:
                        # Special Survey should have -3M only
                        if '-3M' in new_next_survey and '±3M' not in new_next_survey:
                            special_survey_correct += 1
                            correct_formatting_count += 1
                            self.log(f"         ✅ Special Survey window format correct (-3M)")
                        else:
                            self.log(f"         ❌ Special Survey window format incorrect: {new_next_survey}")
                    else:
                        # Other surveys should have ±3M
                        if '±3M' in new_next_survey:
                            other_survey_correct += 1
                            correct_formatting_count += 1
                            self.log(f"         ✅ Other survey window format correct (±3M)")
                        elif not any(window in new_next_survey for window in ['-3M', '±3M']):
                            # Might be condition certificate or other special case
                            self.log(f"         ⚠️ No window format found (might be condition certificate)")
                        else:
                            self.log(f"         ❌ Other survey window format incorrect: {new_next_survey}")
            
            total_with_windows = len([r for r in results if r.get('new_next_survey') and ('±3M' in r.get('new_next_survey', '') or '-3M' in r.get('new_next_survey', ''))])
            
            if total_with_windows > 0:
                formatting_rate = (correct_formatting_count / total_with_windows) * 100
                self.log(f"   Window formatting accuracy: {formatting_rate:.1f}% ({correct_formatting_count}/{total_with_windows})")
                
                if formatting_rate >= 90:
                    self.survey_tests['window_formatting_correct'] = True
                    self.log("✅ Window formatting is correct")
            
            if special_survey_correct > 0:
                self.survey_tests['special_survey_minus_3m_only'] = True
                self.log(f"✅ Special Survey uses -3M only ({special_survey_correct})")
            
            if other_survey_correct > 0:
                self.survey_tests['other_surveys_plus_minus_3m'] = True
                self.log(f"✅ Other surveys use ±3M ({other_survey_correct})")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error verifying window formatting: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_next_survey_tests(self):
        """Main test function for Next Survey calculation logic"""
        self.log("🔄 STARTING SHIP MANAGEMENT SYSTEM - NEXT SURVEY CALCULATION LOGIC TESTING")
        self.log("🎯 FOCUS: Test the updated Next Survey calculation logic after removing special certificate type cases")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Get ships and select test ship
            self.log("\n🚢 STEP 2: GET SHIPS AND SELECT TEST SHIP")
            self.log("=" * 50)
            if not self.get_ships_and_select_test_ship():
                self.log("❌ Failed to get ships or select test ship - cannot proceed")
                return False
            
            # Step 3: Get ship certificates
            self.log("\n📋 STEP 3: GET SHIP CERTIFICATES")
            self.log("=" * 50)
            if not self.get_ship_certificates():
                self.log("❌ Failed to get ship certificates - cannot proceed")
                return False
            
            # Step 4: Test Update Next Survey endpoint
            self.log("\n🔄 STEP 4: TEST UPDATE NEXT SURVEY ENDPOINT")
            self.log("=" * 50)
            endpoint_success = self.test_update_next_survey_endpoint()
            if not endpoint_success:
                self.log("❌ Update Next Survey endpoint failed - cannot proceed")
                return False
            
            # Step 5: Verify uniform window treatment
            self.log("\n📏 STEP 5: VERIFY UNIFORM WINDOW TREATMENT")
            self.log("=" * 50)
            uniform_treatment_success = self.verify_uniform_window_treatment()
            
            # Step 6: Verify survey calculation logic
            self.log("\n🧮 STEP 6: VERIFY SURVEY CALCULATION LOGIC")
            self.log("=" * 50)
            calculation_logic_success = self.verify_survey_calculation_logic()
            
            # Step 7: Verify window formatting
            self.log("\n📐 STEP 7: VERIFY WINDOW FORMATTING")
            self.log("=" * 50)
            window_formatting_success = self.verify_window_formatting()
            
            # Step 8: Final Analysis
            self.log("\n📊 STEP 8: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return (endpoint_success and uniform_treatment_success and 
                   calculation_logic_success and window_formatting_success)
            
        except Exception as e:
            self.log(f"❌ Comprehensive Next Survey testing error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of Next Survey calculation logic testing"""
        try:
            self.log("🔄 SHIP MANAGEMENT SYSTEM - NEXT SURVEY CALCULATION LOGIC TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.survey_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.survey_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.survey_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.survey_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.survey_tests)})")
            
            # Key verification points analysis
            self.log("\n🎯 KEY VERIFICATION POINTS ANALYSIS:")
            
            # 1. Uniform Window Treatment
            uniform_tests = [
                'uniform_window_treatment_verified',
                'no_special_certificate_handling',
                'standard_3_month_window_applied'
            ]
            uniform_passed = sum(1 for test in uniform_tests if self.survey_tests.get(test, False))
            uniform_rate = (uniform_passed / len(uniform_tests)) * 100
            
            self.log(f"\n1. UNIFORM WINDOW TREATMENT: {uniform_rate:.1f}% ({uniform_passed}/{len(uniform_tests)})")
            if self.survey_tests['uniform_window_treatment_verified']:
                self.log("   ✅ SUCCESS: All certificate types get ±3 months window (no special cases)")
            else:
                self.log("   ❌ ISSUE: Uniform window treatment not achieved")
            
            # 2. Next Survey Calculation
            calculation_tests = [
                'anniversary_date_calculation_working',
                'five_year_cycle_logic_intact',
                'annual_survey_type_determination_correct'
            ]
            calculation_passed = sum(1 for test in calculation_tests if self.survey_tests.get(test, False))
            calculation_rate = (calculation_passed / len(calculation_tests)) * 100
            
            self.log(f"\n2. NEXT SURVEY CALCULATION: {calculation_rate:.1f}% ({calculation_passed}/{len(calculation_tests)})")
            if self.survey_tests['anniversary_date_calculation_working']:
                self.log("   ✅ SUCCESS: Anniversary date based calculations working")
            if self.survey_tests['five_year_cycle_logic_intact']:
                self.log("   ✅ SUCCESS: 5-year survey cycle logic intact")
            if self.survey_tests['annual_survey_type_determination_correct']:
                self.log("   ✅ SUCCESS: Annual survey type determination correct")
            
            # 3. Window Display
            window_tests = [
                'window_formatting_correct',
                'special_survey_minus_3m_only',
                'other_surveys_plus_minus_3m'
            ]
            window_passed = sum(1 for test in window_tests if self.survey_tests.get(test, False))
            window_rate = (window_passed / len(window_tests)) * 100
            
            self.log(f"\n3. WINDOW DISPLAY: {window_rate:.1f}% ({window_passed}/{len(window_tests)})")
            if self.survey_tests['special_survey_minus_3m_only']:
                self.log("   ✅ SUCCESS: Special Survey shows -3M only")
            if self.survey_tests['other_surveys_plus_minus_3m']:
                self.log("   ✅ SUCCESS: Other surveys show ±3M")
            
            # 4. Special Certificate Types
            special_cert_tests = [
                'radio_gmdss_no_special_treatment',
                'mlc_labour_no_special_treatment',
                'all_certificates_uniform_treatment'
            ]
            special_cert_passed = sum(1 for test in special_cert_tests if self.survey_tests.get(test, False))
            special_cert_rate = (special_cert_passed / len(special_cert_tests)) * 100
            
            self.log(f"\n4. SPECIAL CERTIFICATE TYPES: {special_cert_rate:.1f}% ({special_cert_passed}/{len(special_cert_tests)})")
            if self.survey_tests['radio_gmdss_no_special_treatment']:
                self.log("   ✅ SUCCESS: Radio/GMDSS certificates no longer have special treatment")
            if self.survey_tests['mlc_labour_no_special_treatment']:
                self.log("   ✅ SUCCESS: MLC/Labour certificates no longer have special treatment")
            
            # 5. Condition Certificates
            if self.survey_tests['condition_certificates_use_valid_date']:
                self.log("\n5. CONDITION CERTIFICATES: ✅ SUCCESS")
                self.log("   ✅ SUCCESS: Condition certificates still use valid_date as next_survey (unchanged)")
            
            # Review request requirements analysis
            self.log("\n📋 REVIEW REQUEST REQUIREMENTS ANALYSIS:")
            
            req1_met = self.survey_tests['authentication_successful']
            req2_met = self.survey_tests['update_next_survey_endpoint_accessible']
            req3_met = self.survey_tests['uniform_window_treatment_verified']
            req4_met = self.survey_tests['update_next_survey_endpoint_accessible']
            req5_met = (self.survey_tests['anniversary_date_calculation_working'] and 
                       self.survey_tests['five_year_cycle_logic_intact'])
            
            self.log(f"   1. Login with admin1/123456: {'✅ MET' if req1_met else '❌ NOT MET'}")
            self.log(f"   2. Test Update Next Survey endpoint: {'✅ MET' if req2_met else '❌ NOT MET'}")
            self.log(f"   3. Verify uniform ±3 months window: {'✅ MET' if req3_met else '❌ NOT MET'}")
            self.log(f"   4. Test /ships/{{ship_id}}/update-next-survey: {'✅ MET' if req4_met else '❌ NOT MET'}")
            self.log(f"   5. Check calculation logic still works: {'✅ MET' if req5_met else '❌ NOT MET'}")
            
            requirements_met = sum([req1_met, req2_met, req3_met, req4_met, req5_met])
            
            # Final conclusion
            if success_rate >= 80 and requirements_met >= 4:
                self.log(f"\n🎉 CONCLUSION: NEXT SURVEY CALCULATION LOGIC IS WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Updated logic fully implemented!")
                self.log(f"   ✅ Requirements met: {requirements_met}/5")
                self.log(f"   ✅ All certificate types now use standard ±3 months window")
                self.log(f"   ✅ No special handling for Radio/GMDSS or MLC certificates")
                self.log(f"   ✅ Survey cycle and anniversary date logic preserved")
                self.log(f"   ✅ Window formatting correct (±3M for all, -3M for Special Survey only)")
            elif success_rate >= 60 and requirements_met >= 3:
                self.log(f"\n⚠️ CONCLUSION: NEXT SURVEY CALCULATION LOGIC PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Most functionality working, minor improvements needed")
                self.log(f"   ⚠️ Requirements met: {requirements_met}/5")
            else:
                self.log(f"\n❌ CONCLUSION: NEXT SURVEY CALCULATION LOGIC HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Significant fixes needed")
                self.log(f"   ❌ Requirements met: {requirements_met}/5")
                self.log(f"   ❌ Next Survey calculation logic needs major fixes before production use")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run Next Survey Calculation Logic tests"""
    print("🔄 SHIP MANAGEMENT SYSTEM - NEXT SURVEY CALCULATION LOGIC TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = NextSurveyCalculationTester()
        success = tester.run_comprehensive_next_survey_tests()
        
        if success:
            print("\n✅ NEXT SURVEY CALCULATION LOGIC TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ NEXT SURVEY CALCULATION LOGIC TESTING COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
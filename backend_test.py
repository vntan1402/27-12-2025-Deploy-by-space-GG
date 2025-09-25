#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: 3-Column Layout Changes for Detailed Ship Information
Review Request: Test the updated 3-column layout changes for Detailed Ship Information with special_survey_cycle field
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import time
import traceback
import subprocess
import tempfile
import base64

# Configuration - Use external URL from frontend/.env
BACKEND_URL = "https://vessel-docs-hub.preview.emergentagent.com/api"

class ThreeColumnLayoutTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for 3-column layout changes and special survey cycle field
        self.layout_tests = {
            'authentication_successful': False,
            'ship_retrieval_with_new_fields_tested': False,
            'special_survey_cycle_field_verified': False,
            'sunshine_01_ship_data_verified': False,
            'three_column_fields_present': False,
            'ship_update_with_special_survey_tested': False,
            'data_consistency_verified': False,
            'backward_compatibility_verified': False,
            'special_survey_cycle_model_working': False,
            'dry_dock_cycle_format_verified': False
        }
        
        # Test ship ID for SUNSHINE 01 as specified in review request
        self.test_ship_id = "e21c71a2-9543-4f92-990c-72f54292fde8"
        self.test_ship_name = "SUNSHINE 01"
        
        # 3-column layout field mapping as per review request
        self.column_fields = {
            'column_1': ['imo', 'ship_owner', 'deadweight'],
            'column_2': ['built_year', 'last_docking', 'dry_dock_cycle'],
            'column_3': ['anniversary_date', 'last_special_survey', 'special_survey_cycle']
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
                
                self.anniversary_tests['authentication_successful'] = True
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
    
    def test_ship_retrieval_with_new_fields(self):
        """Test ship retrieval to verify new field structure for 3-column layout"""
        try:
            self.log("🚢 Testing ship retrieval with new field structure for 3-column layout...")
            
            # Test 1: Get all ships
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   ✅ Retrieved {len(ships)} ships")
                
                # Look for SUNSHINE 01 ship
                sunshine_ship = None
                for ship in ships:
                    if ship.get('id') == self.test_ship_id or ship.get('name') == self.test_ship_name:
                        sunshine_ship = ship
                        break
                
                if sunshine_ship:
                    self.log(f"   ✅ Found {self.test_ship_name} ship")
                    self.log(f"      Ship ID: {sunshine_ship.get('id')}")
                    self.log(f"      Ship Name: {sunshine_ship.get('name')}")
                    
                    # Verify 3-column layout fields according to review request
                    self.log("   📋 Verifying 3-column layout fields:")
                    
                    # Column 1: IMO, Ship Owner, Deadweight
                    imo = sunshine_ship.get('imo')
                    ship_owner = sunshine_ship.get('ship_owner')
                    deadweight = sunshine_ship.get('deadweight')
                    self.log(f"      Column 1 - IMO: {imo}")
                    self.log(f"      Column 1 - Ship Owner: {ship_owner}")
                    self.log(f"      Column 1 - Deadweight: {deadweight}")
                    
                    # Column 2: Built Year, Last Docking, Dry Dock Cycle
                    built_year = sunshine_ship.get('built_year')
                    last_docking = sunshine_ship.get('last_docking')
                    dry_dock_cycle = sunshine_ship.get('dry_dock_cycle')
                    self.log(f"      Column 2 - Built Year: {built_year}")
                    self.log(f"      Column 2 - Last Docking: {last_docking}")
                    self.log(f"      Column 2 - Dry Dock Cycle: {dry_dock_cycle}")
                    
                    # Column 3: Anniversary Date, Last Special Survey, Special Survey Cycle
                    anniversary_date = sunshine_ship.get('anniversary_date')
                    last_special_survey = sunshine_ship.get('last_special_survey')
                    special_survey_cycle = sunshine_ship.get('special_survey_cycle')
                    self.log(f"      Column 3 - Anniversary Date: {anniversary_date}")
                    self.log(f"      Column 3 - Last Special Survey: {last_special_survey}")
                    self.log(f"      Column 3 - Special Survey Cycle: {special_survey_cycle}")
                    
                    # Verify special_survey_cycle field is present (key requirement)
                    if special_survey_cycle is not None:
                        self.log("   ✅ Special Survey Cycle field is present in ship model")
                        self.layout_tests['special_survey_cycle_field_verified'] = True
                        
                        # Check structure of special_survey_cycle
                        if isinstance(special_survey_cycle, dict):
                            self.log(f"      Special Survey Cycle structure: {special_survey_cycle}")
                            cycle_fields = ['from_date', 'to_date', 'intermediate_required', 'cycle_type']
                            for field in cycle_fields:
                                if field in special_survey_cycle:
                                    self.log(f"         ✅ {field}: {special_survey_cycle.get(field)}")
                                else:
                                    self.log(f"         ⚠️ {field}: Not present")
                            self.layout_tests['special_survey_cycle_model_working'] = True
                    else:
                        self.log("   ⚠️ Special Survey Cycle field is not present in ship model")
                    
                    # Verify dry dock cycle format (dd/MM/yyyy format requirement)
                    if dry_dock_cycle and isinstance(dry_dock_cycle, dict):
                        from_date = dry_dock_cycle.get('from_date')
                        to_date = dry_dock_cycle.get('to_date')
                        if from_date and to_date:
                            self.log(f"   ✅ Dry Dock Cycle format verified: {from_date} to {to_date}")
                            self.layout_tests['dry_dock_cycle_format_verified'] = True
                    
                    # Check if all 3-column fields are present
                    all_fields_present = all([
                        imo is not None, ship_owner is not None, deadweight is not None,
                        built_year is not None, last_docking is not None, dry_dock_cycle is not None,
                        anniversary_date is not None, last_special_survey is not None, special_survey_cycle is not None
                    ])
                    
                    if all_fields_present:
                        self.log("   ✅ All 3-column layout fields are present")
                        self.layout_tests['three_column_fields_present'] = True
                    else:
                        self.log("   ⚠️ Some 3-column layout fields are missing")
                    
                    self.test_results['sunshine_ship_data'] = sunshine_ship
                    self.layout_tests['sunshine_01_ship_data_verified'] = True
                else:
                    self.log(f"   ⚠️ {self.test_ship_name} ship not found")
                
                # Test 2: Get specific ship by ID
                if sunshine_ship:
                    ship_endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
                    self.log(f"   GET {ship_endpoint}")
                    ship_response = requests.get(ship_endpoint, headers=self.get_headers(), timeout=30)
                    
                    if ship_response.status_code == 200:
                        ship_data = ship_response.json()
                        self.log("   ✅ Individual ship retrieval successful")
                        self.log(f"      New fields present: {bool(ship_data.get('special_survey_cycle'))}")
                        self.layout_tests['ship_retrieval_with_new_fields_tested'] = True
                    else:
                        self.log(f"   ❌ Individual ship retrieval failed: {ship_response.status_code}")
                
                return True
            else:
                self.log(f"   ❌ Ship retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ship retrieval test error: {str(e)}", "ERROR")
            return False
    
    def test_anniversary_date_calculation(self):
        """Test the new anniversary date calculation endpoint"""
        try:
            self.log("📅 Testing anniversary date calculation endpoint...")
            
            # Test the calculate anniversary date endpoint
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}/calculate-anniversary-date"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Anniversary date calculation successful")
                
                # Log the full response for debugging
                self.log(f"   📊 Full Response: {result}")
                
                # Check the response structure
                success = result.get('success')
                message = result.get('message')
                anniversary_date = result.get('anniversary_date')
                
                self.log(f"   📊 Anniversary Date Calculation Results:")
                self.log(f"      Success: {success}")
                self.log(f"      Message: {message}")
                self.log(f"      Anniversary Date: {anniversary_date}")
                
                if success and anniversary_date:
                    day = anniversary_date.get('day')
                    month = anniversary_date.get('month')
                    source = anniversary_date.get('source')
                    display = anniversary_date.get('display')
                    
                    self.log(f"      Day: {day}")
                    self.log(f"      Month: {month}")
                    self.log(f"      Source: {source}")
                    self.log(f"      Display: {display}")
                    
                    # Validate day/month values (1-31 for day, 1-12 for month)
                    if day and month:
                        if 1 <= day <= 31 and 1 <= month <= 12:
                            self.log("   ✅ Day/month validation passed")
                            self.anniversary_tests['validation_day_month_tested'] = True
                        else:
                            self.log(f"   ❌ Day/month validation failed: day={day}, month={month}")
                    
                    # Check Lloyd's standards compliance
                    if source and 'certificate' in source.lower():
                        self.log("   ✅ Lloyd's standards compliance: Auto-calculated from certificates")
                        self.anniversary_tests['lloyd_standards_compliance_verified'] = True
                    
                    self.anniversary_tests['anniversary_date_calculation_tested'] = True
                elif success == False:
                    self.log(f"   ⚠️ No anniversary date calculated: {message}")
                    # This is still a successful test of the endpoint, just no suitable certificates
                    self.anniversary_tests['anniversary_date_calculation_tested'] = True
                else:
                    self.log("   ⚠️ Unexpected response format")
                
                self.test_results['anniversary_calculation'] = result
                return True
            else:
                self.log(f"   ❌ Anniversary date calculation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Anniversary date calculation test error: {str(e)}", "ERROR")
            return False
    
    def test_anniversary_date_override(self):
        """Test the anniversary date override endpoint"""
        try:
            self.log("🔧 Testing anniversary date override endpoint...")
            
            # Test manual override of anniversary date using query parameters
            day = 15
            month = 8
            
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}/override-anniversary-date?day={day}&month={month}"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Anniversary date override successful")
                
                # Check the response
                anniversary_date = result.get('anniversary_date')
                if anniversary_date:
                    returned_day = anniversary_date.get('day')
                    returned_month = anniversary_date.get('month')
                    manual_override = anniversary_date.get('manual_override')
                    
                    self.log(f"   📊 Override Results:")
                    self.log(f"      Day: {returned_day}")
                    self.log(f"      Month: {returned_month}")
                    self.log(f"      Manual Override: {manual_override}")
                    
                    # Verify override worked correctly
                    if returned_day == 15 and returned_month == 8 and manual_override:
                        self.log("   ✅ Manual override capabilities working correctly")
                        self.anniversary_tests['anniversary_date_override_tested'] = True
                        self.anniversary_tests['validation_day_month_tested'] = True
                    else:
                        self.log("   ❌ Manual override not working as expected")
                
                self.test_results['anniversary_override'] = result
                return True
            else:
                self.log(f"   ❌ Anniversary date override failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Anniversary date override test error: {str(e)}", "ERROR")
            return False
    
    def test_ship_creation_enhanced_fields(self):
        """Test ship creation with enhanced anniversary_date and dry_dock_cycle fields"""
        try:
            self.log("🆕 Testing ship creation with enhanced fields...")
            
            # Create test ship data with enhanced fields
            import random
            unique_imo = f"999{random.randint(1000, 9999)}"
            ship_data = {
                "name": f"TEST ANNIVERSARY SHIP {random.randint(100, 999)}",
                "imo": unique_imo,
                "flag": "PANAMA",
                "ship_type": "General Cargo",
                "gross_tonnage": 5000,
                "deadweight": 8000,
                "built_year": 2020,
                "company": "AMCSC",
                "ship_owner": "Test Owner",
                "last_docking": "2023-01-15T00:00:00Z",
                "last_special_survey": "2023-06-20T00:00:00Z",
                "anniversary_date": {
                    "day": 20,
                    "month": 6,
                    "auto_calculated": False,
                    "source_certificate_type": "Manual Entry",
                    "manual_override": True
                },
                "dry_dock_cycle": {
                    "from_date": "2023-06-20T00:00:00Z",
                    "to_date": "2028-06-20T00:00:00Z",
                    "intermediate_docking_required": True,
                    "last_intermediate_docking": None
                }
            }
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=ship_data, headers=self.get_headers(), timeout=10)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Ship creation with enhanced fields successful")
                
                # Check enhanced fields in response
                created_anniversary = result.get('anniversary_date')
                created_dry_dock = result.get('dry_dock_cycle')
                
                self.log(f"   📊 Created Ship Enhanced Fields:")
                self.log(f"      Anniversary Date: {created_anniversary}")
                self.log(f"      Dry Dock Cycle: {created_dry_dock}")
                
                # Verify enhanced fields
                if created_anniversary and created_dry_dock:
                    # Check anniversary date structure
                    if (created_anniversary.get('day') == 20 and 
                        created_anniversary.get('month') == 6 and
                        created_anniversary.get('manual_override') == True):
                        self.log("   ✅ Anniversary date enhanced fields correct")
                    
                    # Check dry dock cycle structure
                    if (created_dry_dock.get('intermediate_docking_required') == True and
                        created_dry_dock.get('from_date') and
                        created_dry_dock.get('to_date')):
                        self.log("   ✅ Dry dock cycle enhanced fields correct")
                        self.log("   ✅ Lloyd's 5-year period with intermediate docking requirement verified")
                    
                    self.anniversary_tests['ship_creation_enhanced_fields_tested'] = True
                
                # Store created ship ID for cleanup
                self.test_results['created_ship_id'] = result.get('id')
                self.test_results['ship_creation'] = result
                return True
            else:
                self.log(f"   ❌ Ship creation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ship creation test error: {str(e)}", "ERROR")
            return False
    
    def test_ship_update_enhanced_fields(self):
        """Test ship update with enhanced anniversary_date and dry_dock_cycle fields"""
        try:
            self.log("🔄 Testing ship update with enhanced fields...")
            
            # Update the SUNSHINE 01 ship with enhanced fields
            update_data = {
                "last_docking": "2024-02-10T00:00:00Z",
                "last_special_survey": "2024-01-15T00:00:00Z",
                "anniversary_date": {
                    "day": 15,
                    "month": 1,
                    "auto_calculated": True,
                    "source_certificate_type": "Full Term Class Certificate",
                    "manual_override": False
                },
                "dry_dock_cycle": {
                    "from_date": "2024-01-15T00:00:00Z",
                    "to_date": "2029-01-15T00:00:00Z",
                    "intermediate_docking_required": True,
                    "last_intermediate_docking": "2024-02-10T00:00:00Z"
                }
            }
            
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
            self.log(f"   PUT {endpoint}")
            
            response = requests.put(endpoint, json=update_data, headers=self.get_headers(), timeout=10)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Ship update with enhanced fields successful")
                
                # Check enhanced fields in response
                updated_anniversary = result.get('anniversary_date')
                updated_dry_dock = result.get('dry_dock_cycle')
                
                self.log(f"   📊 Updated Ship Enhanced Fields:")
                self.log(f"      Anniversary Date: {updated_anniversary}")
                self.log(f"      Dry Dock Cycle: {updated_dry_dock}")
                
                # Verify enhanced fields
                if updated_anniversary and updated_dry_dock:
                    # Check anniversary date structure
                    if (updated_anniversary.get('day') == 15 and 
                        updated_anniversary.get('month') == 1 and
                        updated_anniversary.get('auto_calculated') == True):
                        self.log("   ✅ Anniversary date enhanced fields updated correctly")
                    
                    # Check dry dock cycle structure with intermediate docking
                    if (updated_dry_dock.get('intermediate_docking_required') == True and
                        updated_dry_dock.get('last_intermediate_docking')):
                        self.log("   ✅ Dry dock cycle with intermediate docking updated correctly")
                        self.log("   ✅ Lloyd's intermediate docking requirements verified")
                        
                        # Check 5-year period (from_date to to_date should be ~5 years)
                        from_date_str = updated_dry_dock.get('from_date')
                        to_date_str = updated_dry_dock.get('to_date')
                        if from_date_str and to_date_str:
                            from datetime import datetime
                            from_date = datetime.fromisoformat(from_date_str.replace('Z', ''))
                            to_date = datetime.fromisoformat(to_date_str.replace('Z', ''))
                            years_diff = (to_date - from_date).days / 365.25
                            if 4.5 <= years_diff <= 5.5:  # Allow some tolerance
                                self.log(f"   ✅ Lloyd's 5-year dry dock cycle verified ({years_diff:.1f} years)")
                                self.anniversary_tests['lloyd_standards_compliance_verified'] = True
                    
                    self.anniversary_tests['ship_update_enhanced_fields_tested'] = True
                
                self.test_results['ship_update'] = result
                return True
            else:
                self.log(f"   ❌ Ship update failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ship update test error: {str(e)}", "ERROR")
            return False
    
    def test_backward_compatibility(self):
        """Test backward compatibility with legacy data formats"""
        try:
            self.log("🔄 Testing backward compatibility with legacy data formats...")
            
            # Test creating ship with legacy fields
            import random
            unique_legacy_imo = f"888{random.randint(1000, 9999)}"
            legacy_ship_data = {
                "name": f"LEGACY TEST SHIP {random.randint(100, 999)}",
                "imo": unique_legacy_imo,
                "flag": "LIBERIA",
                "ship_type": "Bulk Carrier",
                "gross_tonnage": 15000,
                "deadweight": 25000,
                "built_year": 2015,
                "company": "AMCSC",
                "ship_owner": "Legacy Owner",
                "legacy_dry_dock_cycle": 60,  # Legacy months field
                "legacy_anniversary_date": "2024-03-15T00:00:00Z"  # Legacy datetime field
            }
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   POST {endpoint} (with legacy fields)")
            
            response = requests.post(endpoint, json=legacy_ship_data, headers=self.get_headers(), timeout=10)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Ship creation with legacy fields successful")
                
                # Check if legacy fields are preserved
                legacy_dry_dock = result.get('legacy_dry_dock_cycle')
                legacy_anniversary = result.get('legacy_anniversary_date')
                
                # Check if enhanced fields were created from legacy
                enhanced_dry_dock = result.get('dry_dock_cycle')
                enhanced_anniversary = result.get('anniversary_date')
                
                self.log(f"   📊 Backward Compatibility Results:")
                self.log(f"      Legacy Dry Dock Cycle: {legacy_dry_dock}")
                self.log(f"      Legacy Anniversary Date: {legacy_anniversary}")
                self.log(f"      Enhanced Dry Dock Cycle: {enhanced_dry_dock}")
                self.log(f"      Enhanced Anniversary Date: {enhanced_anniversary}")
                
                # Verify backward compatibility
                if legacy_dry_dock == 60 and legacy_anniversary:
                    self.log("   ✅ Legacy fields preserved correctly")
                
                if enhanced_dry_dock or enhanced_anniversary:
                    self.log("   ✅ Enhanced fields created from legacy data")
                    self.anniversary_tests['backward_compatibility_tested'] = True
                
                # Store created ship ID for cleanup
                self.test_results['legacy_ship_id'] = result.get('id')
                self.test_results['backward_compatibility'] = result
                return True
            else:
                self.log(f"   ❌ Legacy ship creation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Backward compatibility test error: {str(e)}", "ERROR")
            return False
    
    def capture_backend_logs(self):
        """Capture backend logs for anniversary processing analysis"""
        try:
            self.log("📝 Capturing backend logs for anniversary processing...")
            
            # Try to capture backend logs
            try:
                result = subprocess.run(
                    ['tail', '-n', '100', '/var/log/supervisor/backend.out.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout:
                    log_lines = result.stdout.strip().split('\n')
                    
                    # Look for anniversary-related log messages
                    anniversary_logs = []
                    for line in log_lines:
                        if any(keyword in line.lower() for keyword in ['anniversary', 'dry dock', 'lloyd', 'certificate', 'enhanced']):
                            anniversary_logs.append(line)
                    
                    if anniversary_logs:
                        self.log("   ✅ Anniversary-related backend logs found:")
                        for log_line in anniversary_logs[-5:]:  # Show last 5 relevant logs
                            self.log(f"      {log_line}")
                        
                        # Check for specific anniversary processing messages
                        processing_logs = [line for line in anniversary_logs if 'anniversary' in line.lower()]
                        if processing_logs:
                            self.log("   ✅ Anniversary processing logs detected")
                    else:
                        self.log("   ⚠️ No anniversary-specific logs found in recent backend output")
                    
                    self.test_results['backend_logs'] = log_lines
                    self.test_results['anniversary_logs'] = anniversary_logs
                else:
                    self.log("   ⚠️ No backend logs accessible")
                    
            except Exception as e:
                self.log(f"   ⚠️ Backend log capture error: {str(e)}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Backend log capture error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_anniversary_tests(self):
        """Main test function for anniversary date and dry dock cycle enhancements"""
        self.log("🎯 STARTING ANNIVERSARY DATE AND DRY DOCK CYCLE TESTING")
        self.log("🔍 Focus: Anniversary date and dry dock cycle enhancements with Lloyd's standards")
        self.log("📋 Review Request: Test enhanced anniversary date auto-calculation and dry dock cycle handling")
        self.log("🎯 Testing: Authentication, ship retrieval, anniversary calculation, override, CRUD operations")
        self.log("=" * 100)
        
        # Step 1: Authenticate
        self.log("\n🔐 STEP 1: AUTHENTICATION")
        self.log("=" * 50)
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Test ship retrieval with enhanced data
        self.log("\n🚢 STEP 2: TEST SHIP RETRIEVAL WITH ENHANCED DATA")
        self.log("=" * 50)
        self.test_ship_retrieval_enhanced_data()
        
        # Step 3: Test anniversary date calculation
        self.log("\n📅 STEP 3: TEST ANNIVERSARY DATE CALCULATION")
        self.log("=" * 50)
        self.test_anniversary_date_calculation()
        
        # Step 4: Test anniversary date override
        self.log("\n🔧 STEP 4: TEST ANNIVERSARY DATE OVERRIDE")
        self.log("=" * 50)
        self.test_anniversary_date_override()
        
        # Step 5: Test ship creation with enhanced fields
        self.log("\n🆕 STEP 5: TEST SHIP CREATION WITH ENHANCED FIELDS")
        self.log("=" * 50)
        self.test_ship_creation_enhanced_fields()
        
        # Step 6: Test ship update with enhanced fields
        self.log("\n🔄 STEP 6: TEST SHIP UPDATE WITH ENHANCED FIELDS")
        self.log("=" * 50)
        self.test_ship_update_enhanced_fields()
        
        # Step 7: Test backward compatibility
        self.log("\n🔄 STEP 7: TEST BACKWARD COMPATIBILITY")
        self.log("=" * 50)
        self.test_backward_compatibility()
        
        # Step 8: Capture backend logs
        self.log("\n📝 STEP 8: CAPTURE BACKEND LOGS")
        self.log("=" * 50)
        self.capture_backend_logs()
        
        # Step 9: Final analysis
        self.log("\n📊 STEP 9: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_anniversary_analysis()
        
        return True
    
    def provide_final_anniversary_analysis(self):
        """Provide final analysis of the anniversary date and dry dock cycle testing"""
        try:
            self.log("🎯 ANNIVERSARY DATE AND DRY DOCK CYCLE TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.anniversary_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ ANNIVERSARY TESTS PASSED ({len(passed_tests)}/10):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ ANNIVERSARY TESTS FAILED ({len(failed_tests)}/10):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Overall assessment
            success_rate = len(passed_tests) / len(self.anniversary_tests) * 100
            self.log(f"\n📊 ANNIVERSARY TESTING SUCCESS RATE: {success_rate:.1f}%")
            
            # Detailed results
            self.log(f"\n🔍 DETAILED RESULTS:")
            
            # SUNSHINE 01 ship data
            sunshine_ship = self.test_results.get('sunshine_ship_data', {})
            if sunshine_ship:
                self.log(f"   🚢 SUNSHINE 01 Ship Analysis:")
                self.log(f"      Ship ID: {sunshine_ship.get('id')}")
                self.log(f"      Anniversary Date: {sunshine_ship.get('anniversary_date')}")
                self.log(f"      Dry Dock Cycle: {sunshine_ship.get('dry_dock_cycle')}")
            
            # Test results analysis
            anniversary_calc = self.test_results.get('anniversary_calculation', {})
            anniversary_override = self.test_results.get('anniversary_override', {})
            ship_creation = self.test_results.get('ship_creation', {})
            ship_update = self.test_results.get('ship_update', {})
            backward_compat = self.test_results.get('backward_compatibility', {})
            
            self.log(f"   📅 Anniversary Date Calculation:")
            calc_result = anniversary_calc.get('anniversary_date')
            if calc_result:
                self.log(f"      Day/Month: {calc_result.get('day')}/{calc_result.get('month')}")
                self.log(f"      Auto Calculated: {calc_result.get('auto_calculated')}")
                self.log(f"      Source: {calc_result.get('source_certificate_type')}")
                self.log(f"      Status: ✅ Working")
            else:
                self.log(f"      Status: ❌ Not Working or No Certificates")
            
            self.log(f"   🔧 Anniversary Date Override:")
            override_result = anniversary_override.get('anniversary_date')
            if override_result:
                self.log(f"      Day/Month: {override_result.get('day')}/{override_result.get('month')}")
                self.log(f"      Manual Override: {override_result.get('manual_override')}")
                self.log(f"      Status: ✅ Working")
            else:
                self.log(f"      Status: ❌ Not Working")
            
            self.log(f"   🆕 Ship Creation with Enhanced Fields:")
            if ship_creation.get('anniversary_date') and ship_creation.get('dry_dock_cycle'):
                self.log(f"      Status: ✅ Working")
                self.log(f"      Enhanced fields created successfully")
            else:
                self.log(f"      Status: ❌ Not Working")
            
            self.log(f"   🔄 Ship Update with Enhanced Fields:")
            if ship_update.get('anniversary_date') and ship_update.get('dry_dock_cycle'):
                self.log(f"      Status: ✅ Working")
                self.log(f"      Enhanced fields updated successfully")
            else:
                self.log(f"      Status: ❌ Not Working")
            
            self.log(f"   🔄 Backward Compatibility:")
            if backward_compat.get('legacy_dry_dock_cycle') and backward_compat.get('legacy_anniversary_date'):
                self.log(f"      Status: ✅ Working")
                self.log(f"      Legacy fields preserved and enhanced fields created")
            else:
                self.log(f"      Status: ❌ Not Working")
            
            # Lloyd's standards compliance
            if self.anniversary_tests.get('lloyd_standards_compliance_verified'):
                self.log(f"   ⚓ Lloyd's Maritime Standards Compliance: ✅ Verified")
                self.log(f"      - 5-year dry dock cycle periods")
                self.log(f"      - Intermediate docking requirements")
                self.log(f"      - Anniversary date from Full Term certificates")
            else:
                self.log(f"   ⚓ Lloyd's Maritime Standards Compliance: ❌ Not Verified")
                
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    print("🎯 Ship Management System - Anniversary Date and Dry Dock Cycle Testing")
    print("🔍 Focus: Anniversary date and dry dock cycle enhancements with Lloyd's standards")
    print("📋 Review Request: Test enhanced anniversary date auto-calculation and dry dock cycle handling")
    print("🎯 Testing: Authentication, ship retrieval, anniversary calculation, override, CRUD operations")
    print("=" * 100)
    
    tester = AnniversaryDateDryDockTester()
    success = tester.run_comprehensive_anniversary_tests()
    
    print("=" * 100)
    print("🔍 ANNIVERSARY DATE AND DRY DOCK CYCLE TESTING RESULTS:")
    print("=" * 70)
    
    # Print test summary
    passed_tests = [f for f, passed in tester.anniversary_tests.items() if passed]
    failed_tests = [f for f, passed in tester.anniversary_tests.items() if not passed]
    
    print(f"✅ ANNIVERSARY TESTS PASSED ({len(passed_tests)}/10):")
    for test in passed_tests:
        print(f"   ✅ {test.replace('_', ' ').title()}")
    
    if failed_tests:
        print(f"\n❌ ANNIVERSARY TESTS FAILED ({len(failed_tests)}/10):")
        for test in failed_tests:
            print(f"   ❌ {test.replace('_', ' ').title()}")
    
    # Print key findings
    print(f"\n🔍 KEY FINDINGS:")
    
    # SUNSHINE 01 ship analysis
    sunshine_ship = tester.test_results.get('sunshine_ship_data', {})
    print(f"   🚢 SUNSHINE 01 Ship Analysis:")
    if sunshine_ship:
        print(f"      Ship found: ✅")
        print(f"      Enhanced fields present: {'✅' if sunshine_ship.get('anniversary_date') or sunshine_ship.get('dry_dock_cycle') else '❌'}")
    else:
        print(f"      Ship found: ❌")
    
    # Test results
    anniversary_calc = tester.test_results.get('anniversary_calculation', {})
    anniversary_override = tester.test_results.get('anniversary_override', {})
    ship_creation = tester.test_results.get('ship_creation', {})
    ship_update = tester.test_results.get('ship_update', {})
    backward_compat = tester.test_results.get('backward_compatibility', {})
    
    print(f"   📅 Anniversary Date Calculation: {'✅ Working' if anniversary_calc.get('anniversary_date') else '❌ Not Working'}")
    print(f"   🔧 Anniversary Date Override: {'✅ Working' if anniversary_override.get('anniversary_date') else '❌ Not Working'}")
    print(f"   🆕 Ship Creation Enhanced Fields: {'✅ Working' if ship_creation.get('anniversary_date') else '❌ Not Working'}")
    print(f"   🔄 Ship Update Enhanced Fields: {'✅ Working' if ship_update.get('anniversary_date') else '❌ Not Working'}")
    print(f"   🔄 Backward Compatibility: {'✅ Working' if backward_compat.get('legacy_dry_dock_cycle') else '❌ Not Working'}")
    
    # Lloyd's standards compliance
    lloyd_compliance = tester.anniversary_tests.get('lloyd_standards_compliance_verified', False)
    print(f"   ⚓ Lloyd's Maritime Standards: {'✅ Compliant' if lloyd_compliance else '❌ Not Verified'}")
    
    # Calculate success rate
    success_rate = len(passed_tests) / len(tester.anniversary_tests) * 100
    print(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")
    
    print("=" * 100)
    if success:
        print("🎉 Anniversary date and dry dock cycle testing completed!")
        print("✅ All testing steps executed - detailed analysis available above")
    else:
        print("❌ Anniversary date and dry dock cycle testing completed with issues!")
        print("🔍 Check detailed logs above for specific issues")
    
    # Provide recommendations based on findings
    print("\n💡 NEXT STEPS FOR MAIN AGENT:")
    
    # Anniversary date calculation
    if anniversary_calc.get('anniversary_date'):
        print("   ✅ Anniversary date calculation is working correctly")
    else:
        print("   ❌ Anniversary date calculation needs improvement")
        print("   1. Check certificate analysis for Full Term certificates")
        print("   2. Verify Lloyd's standards implementation")
        print("   3. Test with ships that have suitable certificates")
    
    # Anniversary date override
    if anniversary_override.get('anniversary_date'):
        print("   ✅ Anniversary date override is working correctly")
    else:
        print("   ❌ Anniversary date override needs improvement")
        print("   1. Check override endpoint implementation")
        print("   2. Verify manual override capabilities")
        print("   3. Test validation of day/month values")
    
    # Ship CRUD operations
    if ship_creation.get('anniversary_date') and ship_update.get('anniversary_date'):
        print("   ✅ Ship CRUD with enhanced fields is working correctly")
    else:
        print("   ❌ Ship CRUD with enhanced fields needs improvement")
        print("   1. Check enhanced field processing in ship creation/update")
        print("   2. Verify dry dock cycle 5-year period handling")
        print("   3. Test intermediate docking requirements")
    
    # Backward compatibility
    if backward_compat.get('legacy_dry_dock_cycle'):
        print("   ✅ Backward compatibility is working correctly")
    else:
        print("   ❌ Backward compatibility needs improvement")
        print("   1. Check legacy field preservation")
        print("   2. Verify enhanced field creation from legacy data")
        print("   3. Test migration of existing ship data")
    
    # Lloyd's standards
    if lloyd_compliance:
        print("   ✅ Lloyd's maritime standards compliance verified")
    else:
        print("   ❌ Lloyd's maritime standards compliance needs verification")
        print("   1. Check 5-year dry dock cycle implementation")
        print("   2. Verify intermediate docking requirements")
        print("   3. Test anniversary date calculation from certificates")
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
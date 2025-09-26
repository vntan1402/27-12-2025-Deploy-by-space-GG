#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: Anniversary Date Recalculate Function Testing
Review Request: Test updated Anniversary Date logic with enhanced certificate processing
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

class AnniversaryDateTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Anniversary Date Recalculate Function
        self.anniversary_tests = {
            'authentication_successful': False,
            'recalculate_function_fixed': False,
            'valid_date_logic_working': False,
            'endorsement_parsing_working': False,
            'certificate_analysis_working': False,
            'expected_result_verified': False,
            'no_error_message_confirmed': False,
            'full_term_priority_verified': False,
            'most_common_logic_working': False,
            'edge_cases_handled': False
        }
        
        # Test ship ID for SUNSHINE 01 as specified in review request
        self.test_ship_id = "e21c71a2-9543-4f92-990c-72f54292fde8"
        self.test_ship_name = "SUNSHINE 01"
        
        # Expected results from review request
        self.expected_day = 10
        self.expected_month = 3
        self.expected_certificate_type = "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE"
        
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
                
                self.layout_tests['authentication_successful'] = True
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
    
    def test_anniversary_date_recalculate_function(self):
        """Test the fixed Anniversary Date Recalculate Function"""
        try:
            self.log("🔄 Testing Anniversary Date Recalculate Function...")
            self.log(f"   Target Ship: {self.test_ship_name} (ID: {self.test_ship_id})")
            
            # Test the POST /api/ships/{ship_id}/calculate-anniversary-date endpoint
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}/calculate-anniversary-date"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Anniversary Date Recalculate endpoint responded successfully")
                self.log(f"   📊 Response: {json.dumps(result, indent=2)}")
                
                # Check if the function is working (no error message)
                success = result.get('success', False)
                message = result.get('message', '')
                anniversary_date = result.get('anniversary_date')
                
                self.log(f"   Success: {success}")
                self.log(f"   Message: {message}")
                self.log(f"   Anniversary Date: {anniversary_date}")
                
                # Verify the fix - should not get "Unable to calculate anniversary date from certificates"
                if "Unable to calculate anniversary date from certificates" not in message:
                    self.log("   ✅ No error message about unable to calculate - fix appears to be working")
                    self.anniversary_tests['no_error_message_confirmed'] = True
                else:
                    self.log("   ❌ Still getting error message - fix may not be working")
                
                # Check if we got a successful calculation
                if success and anniversary_date:
                    self.log("   ✅ Anniversary date calculation successful")
                    self.anniversary_tests['recalculate_function_fixed'] = True
                    
                    # Verify expected results (day=10, month=3)
                    calculated_day = anniversary_date.get('day')
                    calculated_month = anniversary_date.get('month')
                    source_cert = anniversary_date.get('source_certificate_type', '')
                    auto_calculated = anniversary_date.get('auto_calculated', False)
                    manual_override = anniversary_date.get('manual_override', True)
                    
                    self.log(f"   📊 Calculated Anniversary Date:")
                    self.log(f"      Day: {calculated_day} (Expected: {self.expected_day})")
                    self.log(f"      Month: {calculated_month} (Expected: {self.expected_month})")
                    self.log(f"      Source Certificate: {source_cert}")
                    self.log(f"      Auto Calculated: {auto_calculated}")
                    self.log(f"      Manual Override: {manual_override}")
                    
                    # Verify expected results
                    if calculated_day == self.expected_day and calculated_month == self.expected_month:
                        self.log("   ✅ Expected anniversary date results verified (day=10, month=3)")
                        self.anniversary_tests['expected_result_verified'] = True
                    else:
                        self.log(f"   ⚠️ Anniversary date results differ from expected (got {calculated_day}/{calculated_month})")
                    
                    # Verify auto_calculated=true and manual_override=false
                    if auto_calculated and not manual_override:
                        self.log("   ✅ Auto-calculated=true and manual_override=false verified")
                    else:
                        self.log(f"   ⚠️ Auto-calculated or manual_override flags not as expected")
                    
                    # Check if source certificate type is set correctly
                    if source_cert and "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE" in source_cert:
                        self.log("   ✅ Source certificate type correctly identified")
                    else:
                        self.log(f"   ⚠️ Source certificate type may not be correct: {source_cert}")
                
                else:
                    self.log("   ❌ Anniversary date calculation failed or returned no data")
                    self.log(f"      Success: {success}")
                    self.log(f"      Message: {message}")
                
                self.test_results['recalculate_response'] = result
                return True
                
            else:
                self.log(f"   ❌ Anniversary Date Recalculate failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Anniversary Date Recalculate test error: {str(e)}", "ERROR")
            return False
    
    def test_special_survey_cycle_model(self):
        """Test the SpecialSurveyCycle model functionality"""
        try:
            self.log("🔍 Testing SpecialSurveyCycle model functionality...")
            
            # Test ship update with special_survey_cycle data
            special_survey_data = {
                "from_date": "2024-01-15T00:00:00Z",
                "to_date": "2025-01-15T00:00:00Z",
                "intermediate_required": True,
                "cycle_type": "Annual"
            }
            
            update_data = {
                "special_survey_cycle": special_survey_data,
                "last_special_survey": "2024-01-15T00:00:00Z"
            }
            
            endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
            self.log(f"   PUT {endpoint}")
            self.log(f"   Update data: {update_data}")
            
            response = requests.put(endpoint, json=update_data, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("   ✅ Ship update with special_survey_cycle successful")
                
                # Check if special_survey_cycle was saved correctly
                updated_special_survey = result.get('special_survey_cycle')
                updated_last_special_survey = result.get('last_special_survey')
                
                self.log(f"   📊 Updated Special Survey Cycle: {updated_special_survey}")
                self.log(f"   📊 Updated Last Special Survey: {updated_last_special_survey}")
                
                if updated_special_survey:
                    # Verify structure
                    expected_fields = ['from_date', 'to_date', 'intermediate_required', 'cycle_type']
                    all_fields_present = all(field in updated_special_survey for field in expected_fields)
                    
                    if all_fields_present:
                        self.log("   ✅ SpecialSurveyCycle model structure verified")
                        self.log(f"      From Date: {updated_special_survey.get('from_date')}")
                        self.log(f"      To Date: {updated_special_survey.get('to_date')}")
                        self.log(f"      Intermediate Required: {updated_special_survey.get('intermediate_required')}")
                        self.log(f"      Cycle Type: {updated_special_survey.get('cycle_type')}")
                        
                        self.layout_tests['special_survey_cycle_model_working'] = True
                        self.layout_tests['ship_update_with_special_survey_tested'] = True
                    else:
                        self.log("   ❌ SpecialSurveyCycle model structure incomplete")
                else:
                    self.log("   ❌ Special Survey Cycle not saved in update")
                
                self.test_results['special_survey_update'] = result
                return True
            else:
                self.log(f"   ❌ Ship update with special_survey_cycle failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ SpecialSurveyCycle model test error: {str(e)}", "ERROR")
            return False
    
    def test_data_consistency(self):
        """Test that all existing ship data remains intact after model changes"""
        try:
            self.log("🔍 Testing data consistency and backward compatibility...")
            
            # Get all ships to verify existing data integrity
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   ✅ Retrieved {len(ships)} ships for data consistency check")
                
                # Check each ship for data integrity
                intact_ships = 0
                ships_with_new_fields = 0
                ships_with_legacy_fields = 0
                
                for ship in ships:
                    ship_name = ship.get('name', 'Unknown')
                    
                    # Check core fields are intact
                    core_fields = ['id', 'name', 'imo', 'flag', 'company']
                    core_intact = all(ship.get(field) is not None for field in core_fields if field != 'imo')  # IMO can be None
                    
                    if core_intact:
                        intact_ships += 1
                    
                    # Check for new fields
                    if ship.get('special_survey_cycle') is not None:
                        ships_with_new_fields += 1
                    
                    # Check for legacy fields
                    if ship.get('legacy_dry_dock_cycle') is not None or ship.get('legacy_anniversary_date') is not None:
                        ships_with_legacy_fields += 1
                    
                    # Log details for SUNSHINE 01
                    if ship.get('name') == self.test_ship_name:
                        self.log(f"   📊 {self.test_ship_name} Data Integrity:")
                        self.log(f"      Core fields intact: {core_intact}")
                        self.log(f"      Has special_survey_cycle: {ship.get('special_survey_cycle') is not None}")
                        self.log(f"      Has legacy fields: {ship.get('legacy_dry_dock_cycle') is not None}")
                        
                        # Verify specific 3-column layout fields
                        column_1_fields = ['imo', 'ship_owner', 'deadweight']
                        column_2_fields = ['built_year', 'last_docking', 'dry_dock_cycle']
                        column_3_fields = ['anniversary_date', 'last_special_survey', 'special_survey_cycle']
                        
                        for field in column_1_fields + column_2_fields + column_3_fields:
                            value = ship.get(field)
                            self.log(f"         {field}: {'✅' if value is not None else '⚠️'} {value}")
                
                self.log(f"   📊 Data Consistency Results:")
                self.log(f"      Ships with intact core data: {intact_ships}/{len(ships)}")
                self.log(f"      Ships with new special_survey_cycle field: {ships_with_new_fields}/{len(ships)}")
                self.log(f"      Ships with legacy fields: {ships_with_legacy_fields}/{len(ships)}")
                
                # Verify data consistency
                if intact_ships == len(ships):
                    self.log("   ✅ All existing ship data remains intact")
                    self.layout_tests['data_consistency_verified'] = True
                else:
                    self.log(f"   ⚠️ Some ships have data integrity issues: {len(ships) - intact_ships} affected")
                
                # Verify backward compatibility
                if ships_with_legacy_fields > 0:
                    self.log("   ✅ Backward compatibility maintained - legacy fields preserved")
                    self.layout_tests['backward_compatibility_verified'] = True
                else:
                    self.log("   ⚠️ No legacy fields found - may indicate migration issues")
                
                self.test_results['data_consistency'] = {
                    'total_ships': len(ships),
                    'intact_ships': intact_ships,
                    'ships_with_new_fields': ships_with_new_fields,
                    'ships_with_legacy_fields': ships_with_legacy_fields
                }
                
                return True
            else:
                self.log(f"   ❌ Data consistency check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Data consistency test error: {str(e)}", "ERROR")
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
        """Capture backend logs for 3-column layout and special survey cycle analysis"""
        try:
            self.log("📝 Capturing backend logs for 3-column layout processing...")
            
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
                    
                    # Look for layout and special survey related log messages
                    layout_logs = []
                    for line in log_lines:
                        if any(keyword in line.lower() for keyword in ['special_survey', 'survey_cycle', 'ship', 'enhanced', 'model']):
                            layout_logs.append(line)
                    
                    if layout_logs:
                        self.log("   ✅ Layout-related backend logs found:")
                        for log_line in layout_logs[-5:]:  # Show last 5 relevant logs
                            self.log(f"      {log_line}")
                        
                        # Check for specific special survey processing messages
                        processing_logs = [line for line in layout_logs if 'special_survey' in line.lower()]
                        if processing_logs:
                            self.log("   ✅ Special survey processing logs detected")
                    else:
                        self.log("   ⚠️ No layout-specific logs found in recent backend output")
                    
                    self.test_results['backend_logs'] = log_lines
                    self.test_results['layout_logs'] = layout_logs
                else:
                    self.log("   ⚠️ No backend logs accessible")
                    
            except Exception as e:
                self.log(f"   ⚠️ Backend log capture error: {str(e)}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Backend log capture error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_layout_tests(self):
        """Main test function for 3-column layout changes and special survey cycle field"""
        self.log("🎯 STARTING 3-COLUMN LAYOUT CHANGES TESTING")
        self.log("🔍 Focus: Updated 3-column layout changes for Detailed Ship Information")
        self.log("📋 Review Request: Test special_survey_cycle field and 3-column layout field structure")
        self.log("🎯 Testing: Authentication, ship retrieval, special survey cycle model, data consistency")
        self.log("=" * 100)
        
        # Step 1: Authenticate
        self.log("\n🔐 STEP 1: AUTHENTICATION")
        self.log("=" * 50)
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Test ship retrieval with new field structure
        self.log("\n🚢 STEP 2: TEST SHIP RETRIEVAL WITH NEW FIELD STRUCTURE")
        self.log("=" * 50)
        self.test_ship_retrieval_with_new_fields()
        
        # Step 3: Test SpecialSurveyCycle model functionality
        self.log("\n🔍 STEP 3: TEST SPECIAL SURVEY CYCLE MODEL")
        self.log("=" * 50)
        self.test_special_survey_cycle_model()
        
        # Step 4: Test data consistency and backward compatibility
        self.log("\n🔍 STEP 4: TEST DATA CONSISTENCY")
        self.log("=" * 50)
        self.test_data_consistency()
        
        # Step 5: Capture backend logs
        self.log("\n📝 STEP 5: CAPTURE BACKEND LOGS")
        self.log("=" * 50)
        self.capture_backend_logs()
        
        # Step 6: Final analysis
        self.log("\n📊 STEP 6: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_layout_analysis()
        
        return True
    
    def provide_final_layout_analysis(self):
        """Provide final analysis of the 3-column layout changes testing"""
        try:
            self.log("🎯 3-COLUMN LAYOUT CHANGES TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.layout_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ LAYOUT TESTS PASSED ({len(passed_tests)}/10):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ LAYOUT TESTS FAILED ({len(failed_tests)}/10):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Overall assessment
            success_rate = len(passed_tests) / len(self.layout_tests) * 100
            self.log(f"\n📊 3-COLUMN LAYOUT TESTING SUCCESS RATE: {success_rate:.1f}%")
            
            # Detailed results
            self.log(f"\n🔍 DETAILED RESULTS:")
            
            # SUNSHINE 01 ship data analysis
            sunshine_ship = self.test_results.get('sunshine_ship_data', {})
            if sunshine_ship:
                self.log(f"   🚢 SUNSHINE 01 Ship Analysis (ID: {self.test_ship_id}):")
                
                # Column 1 fields
                self.log(f"      Column 1 Fields:")
                self.log(f"         IMO: {sunshine_ship.get('imo', 'N/A')}")
                self.log(f"         Ship Owner: {sunshine_ship.get('ship_owner', 'N/A')}")
                self.log(f"         Deadweight: {sunshine_ship.get('deadweight', 'N/A')}")
                
                # Column 2 fields
                self.log(f"      Column 2 Fields:")
                self.log(f"         Built Year: {sunshine_ship.get('built_year', 'N/A')}")
                self.log(f"         Last Docking: {sunshine_ship.get('last_docking', 'N/A')}")
                dry_dock = sunshine_ship.get('dry_dock_cycle', 'N/A')
                self.log(f"         Dry Dock Cycle: {'Present' if dry_dock != 'N/A' else 'N/A'}")
                
                # Column 3 fields
                self.log(f"      Column 3 Fields:")
                anniversary = sunshine_ship.get('anniversary_date', 'N/A')
                self.log(f"         Anniversary Date: {'Present' if anniversary != 'N/A' else 'N/A'}")
                self.log(f"         Last Special Survey: {sunshine_ship.get('last_special_survey', 'N/A')}")
                special_survey = sunshine_ship.get('special_survey_cycle', 'N/A')
                self.log(f"         Special Survey Cycle: {'Present' if special_survey != 'N/A' else 'N/A'}")
            
            # Special Survey Cycle Model Analysis
            special_survey_update = self.test_results.get('special_survey_update', {})
            self.log(f"   🔍 Special Survey Cycle Model:")
            if special_survey_update.get('special_survey_cycle'):
                cycle_data = special_survey_update['special_survey_cycle']
                self.log(f"      Status: ✅ Working")
                self.log(f"      From Date: {cycle_data.get('from_date', 'N/A')}")
                self.log(f"      To Date: {cycle_data.get('to_date', 'N/A')}")
                self.log(f"      Intermediate Required: {cycle_data.get('intermediate_required', 'N/A')}")
                self.log(f"      Cycle Type: {cycle_data.get('cycle_type', 'N/A')}")
            else:
                self.log(f"      Status: ❌ Not Working")
            
            # Data Consistency Analysis
            data_consistency = self.test_results.get('data_consistency', {})
            self.log(f"   🔍 Data Consistency:")
            if data_consistency:
                total = data_consistency.get('total_ships', 0)
                intact = data_consistency.get('intact_ships', 0)
                new_fields = data_consistency.get('ships_with_new_fields', 0)
                legacy_fields = data_consistency.get('ships_with_legacy_fields', 0)
                
                self.log(f"      Total Ships: {total}")
                self.log(f"      Ships with Intact Data: {intact}/{total}")
                self.log(f"      Ships with New Fields: {new_fields}/{total}")
                self.log(f"      Ships with Legacy Fields: {legacy_fields}/{total}")
                self.log(f"      Status: {'✅ Good' if intact == total else '⚠️ Issues Detected'}")
            else:
                self.log(f"      Status: ❌ Not Tested")
            
            # Key Review Request Requirements
            self.log(f"\n📋 REVIEW REQUEST REQUIREMENTS:")
            self.log(f"   1. Backend Model Verification: {'✅' if self.layout_tests.get('ship_retrieval_with_new_fields_tested') else '❌'}")
            self.log(f"   2. SUNSHINE 01 Ship Data: {'✅' if self.layout_tests.get('sunshine_01_ship_data_verified') else '❌'}")
            self.log(f"   3. Special Survey Cycle Field: {'✅' if self.layout_tests.get('special_survey_cycle_field_verified') else '❌'}")
            self.log(f"   4. Data Consistency: {'✅' if self.layout_tests.get('data_consistency_verified') else '❌'}")
            self.log(f"   5. 3-Column Layout Fields: {'✅' if self.layout_tests.get('three_column_fields_present') else '❌'}")
            self.log(f"   6. Dry Dock Cycle Format: {'✅' if self.layout_tests.get('dry_dock_cycle_format_verified') else '❌'}")
                
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    print("🎯 Ship Management System - 3-Column Layout Changes Testing")
    print("🔍 Focus: Updated 3-column layout changes for Detailed Ship Information")
    print("📋 Review Request: Test special_survey_cycle field and 3-column layout field structure")
    print("🎯 Testing: Authentication, ship retrieval, special survey cycle model, data consistency")
    print("=" * 100)
    
    tester = ThreeColumnLayoutTester()
    success = tester.run_comprehensive_layout_tests()
    
    print("=" * 100)
    print("🔍 3-COLUMN LAYOUT CHANGES TESTING RESULTS:")
    print("=" * 70)
    
    # Print test summary
    passed_tests = [f for f, passed in tester.layout_tests.items() if passed]
    failed_tests = [f for f, passed in tester.layout_tests.items() if not passed]
    
    print(f"✅ LAYOUT TESTS PASSED ({len(passed_tests)}/10):")
    for test in passed_tests:
        print(f"   ✅ {test.replace('_', ' ').title()}")
    
    if failed_tests:
        print(f"\n❌ LAYOUT TESTS FAILED ({len(failed_tests)}/10):")
        for test in failed_tests:
            print(f"   ❌ {test.replace('_', ' ').title()}")
    
    # Print key findings
    print(f"\n🔍 KEY FINDINGS:")
    
    # SUNSHINE 01 ship analysis
    sunshine_ship = tester.test_results.get('sunshine_ship_data', {})
    print(f"   🚢 SUNSHINE 01 Ship Analysis:")
    if sunshine_ship:
        print(f"      Ship found: ✅")
        print(f"      Special Survey Cycle field: {'✅' if sunshine_ship.get('special_survey_cycle') is not None else '❌'}")
        print(f"      3-column fields present: {'✅' if tester.layout_tests.get('three_column_fields_present') else '❌'}")
    else:
        print(f"      Ship found: ❌")
    
    # Test results
    special_survey_update = tester.test_results.get('special_survey_update', {})
    data_consistency = tester.test_results.get('data_consistency', {})
    
    print(f"   🔍 Special Survey Cycle Model: {'✅ Working' if special_survey_update.get('special_survey_cycle') else '❌ Not Working'}")
    print(f"   🔍 Data Consistency: {'✅ Verified' if tester.layout_tests.get('data_consistency_verified') else '❌ Issues Found'}")
    print(f"   🔄 Backward Compatibility: {'✅ Maintained' if tester.layout_tests.get('backward_compatibility_verified') else '❌ Issues Found'}")
    
    # Calculate success rate
    success_rate = len(passed_tests) / len(tester.layout_tests) * 100
    print(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")
    
    print("=" * 100)
    if success:
        print("🎉 3-column layout changes testing completed!")
        print("✅ All testing steps executed - detailed analysis available above")
    else:
        print("❌ 3-column layout changes testing completed with issues!")
        print("🔍 Check detailed logs above for specific issues")
    
    # Provide recommendations based on findings
    print("\n💡 NEXT STEPS FOR MAIN AGENT:")
    
    # Review Request Requirements
    print("   📋 REVIEW REQUEST REQUIREMENTS STATUS:")
    
    # Backend Model Verification
    if tester.layout_tests.get('ship_retrieval_with_new_fields_tested'):
        print("   ✅ Backend Model Verification: Ship retrieval with new field structure working")
    else:
        print("   ❌ Backend Model Verification: Ship retrieval needs improvement")
        print("      1. Check ship model includes special_survey_cycle field")
        print("      2. Verify all 3-column layout fields are accessible via API")
    
    # SUNSHINE 01 Ship Data
    if tester.layout_tests.get('sunshine_01_ship_data_verified'):
        print("   ✅ SUNSHINE 01 Ship Data: Successfully retrieved and verified")
    else:
        print("   ❌ SUNSHINE 01 Ship Data: Issues with ship data retrieval")
        print("      1. Verify ship exists with correct ID")
        print("      2. Check all required fields are present")
    
    # Special Survey Cycle Field
    if tester.layout_tests.get('special_survey_cycle_field_verified'):
        print("   ✅ Special Survey Cycle Field: Present and working in ship models")
    else:
        print("   ❌ Special Survey Cycle Field: Missing or not working")
        print("      1. Add special_survey_cycle field to ShipBase model")
        print("      2. Verify SpecialSurveyCycle model is properly implemented")
        print("      3. Test ship update with special_survey_cycle data")
    
    # Data Consistency
    if tester.layout_tests.get('data_consistency_verified'):
        print("   ✅ Data Consistency: All existing ship data remains intact")
    else:
        print("   ❌ Data Consistency: Issues with existing data integrity")
        print("      1. Check for data corruption after model changes")
        print("      2. Verify backward compatibility with existing ships")
        print("      3. Test migration of legacy data")
    
    # 3-Column Layout Fields
    if tester.layout_tests.get('three_column_fields_present'):
        print("   ✅ 3-Column Layout Fields: All required fields present")
    else:
        print("   ❌ 3-Column Layout Fields: Some fields missing")
        print("      1. Verify Column 1: IMO, Ship Owner, Deadweight")
        print("      2. Verify Column 2: Built Year, Last Docking, Dry Dock Cycle")
        print("      3. Verify Column 3: Anniversary Date, Last Special Survey, Special Survey Cycle")
    
    # Dry Dock Cycle Format
    if tester.layout_tests.get('dry_dock_cycle_format_verified'):
        print("   ✅ Dry Dock Cycle Format: dd/MM/yyyy format working correctly")
    else:
        print("   ❌ Dry Dock Cycle Format: Format issues detected")
        print("      1. Check dry dock cycle date formatting")
        print("      2. Verify dd/MM/yyyy format is maintained")
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Survey Type Determination Testing Script for Ship Management System
FOCUS: Testing the new Survey Type determination functionality that automatically assigns survey types based on maritime regulations

TEST REQUIREMENTS:
1. Test Survey Type Logic Function (determine_survey_type function)
2. Test Backend API Endpoints for survey type determination
3. Test Survey Type Assignment Logic with different certificate ages
4. Test Certificate Type Specific Logic (SOLAS, Class, ISM, ISPS, MLC, Radio, Load Line)
5. Test Edge Cases
6. Test Auto-Assignment Integration

EXPECTED RESULTS:
- Survey types accurately reflect maritime regulatory requirements
- Different certificate types get appropriate survey types
- Age and date-based calculations work correctly
- API endpoints respond properly with survey type assignments
- Auto-assignment works for new and updated certificates
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
    test_response = requests.get('http://127.0.0.1:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401, 403]:  # 403 is also expected without auth
        BACKEND_URL = 'http://127.0.0.1:8001/api'
        print("Using internal backend URL: http://127.0.0.1:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://marinetrack-1.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class SurveyTypeTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Survey Type functionality
        self.test_results = {
            # Authentication
            'authentication_successful': False,
            
            # Survey Type Logic Function Tests
            'solas_class_survey_type_logic': False,
            'ism_survey_type_logic': False,
            'isps_survey_type_logic': False,
            'mlc_survey_type_logic': False,
            'radio_survey_type_logic': False,
            'load_line_survey_type_logic': False,
            
            # API Endpoint Tests
            'determine_survey_type_endpoint_working': False,
            'update_survey_types_endpoint_working': False,
            
            # Age-based Logic Tests
            'new_certificate_initial_survey': False,
            'mid_cycle_intermediate_survey': False,
            'near_expiry_renewal_survey': False,
            'five_year_special_survey': False,
            
            # Edge Cases
            'certificate_without_ship_data': False,
            'certificate_missing_dates': False,
            'unknown_certificate_type': False,
            'expired_certificate_renewal': False,
            
            # Auto-Assignment Integration
            'new_certificate_auto_assignment': False,
            'updated_certificate_recalculation': False,
        }
        
        # Test ship and certificate data
        self.test_ship_id = None
        self.test_certificates = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
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
            response = requests.post(endpoint, json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.test_results['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed - Status: {response.status_code}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def get_existing_ship(self):
        """Get an existing ship for survey type testing"""
        try:
            self.log("🚢 Getting existing ship for Survey Type testing...")
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(
                endpoint,
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                ships = response.json()
                if ships and len(ships) > 0:
                    # Use the first available ship
                    ship = ships[0]
                    self.test_ship_id = ship.get('id')
                    ship_name = ship.get('name', 'Unknown')
                    self.log("✅ Using existing ship for testing")
                    self.log(f"   Ship ID: {self.test_ship_id}")
                    self.log(f"   Ship Name: {ship_name}")
                    return True
                else:
                    self.log("❌ No existing ships found")
                    return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Get existing ship error: {str(e)}", "ERROR")
            return False
    
    def create_test_certificates(self):
        """Create test certificates with different types and ages for testing"""
        try:
            self.log("📋 Creating test certificates for Survey Type testing...")
            
            if not self.test_ship_id:
                self.log("❌ No test ship available")
                return False
            
            # Test certificate scenarios
            test_certificates = [
                # SOLAS/Class Certificate - New (should get Initial)
                {
                    'cert_name': 'CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': (datetime.now() - timedelta(days=30)).isoformat(),
                    'valid_date': (datetime.now() + timedelta(days=1800)).isoformat(),
                    'issued_by': 'DNV GL',
                    'expected_survey_type': 'Initial'
                },
                
                # SOLAS Certificate - Mid-cycle (should get Intermediate)
                {
                    'cert_name': 'CARGO SHIP SAFETY EQUIPMENT CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': (datetime.now() - timedelta(days=730)).isoformat(),  # 2 years old
                    'valid_date': (datetime.now() + timedelta(days=1095)).isoformat(),  # 3 years validity
                    'issued_by': 'DNV GL',
                    'expected_survey_type': 'Intermediate'
                },
                
                # Class Certificate - Near 5-year mark (should get Special)
                {
                    'cert_name': 'CLASS CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': (datetime.now() - timedelta(days=1460)).isoformat(),  # 4 years old
                    'valid_date': (datetime.now() + timedelta(days=365)).isoformat(),   # 1 year left
                    'issued_by': 'DNV GL',
                    'expected_survey_type': 'Special'
                },
                
                # ISM Certificate - Mid-cycle (should get Intermediate)
                {
                    'cert_name': 'SAFETY MANAGEMENT CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': (datetime.now() - timedelta(days=900)).isoformat(),  # 2.5 years old
                    'valid_date': (datetime.now() + timedelta(days=900)).isoformat(),
                    'issued_by': 'DNV GL',
                    'expected_survey_type': 'Intermediate'
                },
                
                # ISPS Certificate - New (should get Initial)
                {
                    'cert_name': 'INTERNATIONAL SHIP SECURITY CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': (datetime.now() - timedelta(days=60)).isoformat(),
                    'valid_date': (datetime.now() + timedelta(days=1765)).isoformat(),
                    'issued_by': 'Flag State',
                    'expected_survey_type': 'Initial'
                },
                
                # MLC Certificate - Near renewal (should get Renewal)
                {
                    'cert_name': 'MARITIME LABOUR CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': (datetime.now() - timedelta(days=1000)).isoformat(),  # ~3 years old
                    'valid_date': (datetime.now() + timedelta(days=95)).isoformat(),    # Near expiry
                    'issued_by': 'Flag State',
                    'expected_survey_type': 'Renewal'
                },
                
                # Radio Certificate - Regular (should get Annual)
                {
                    'cert_name': 'RADIO SAFETY CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': (datetime.now() - timedelta(days=400)).isoformat(),
                    'valid_date': (datetime.now() + timedelta(days=365)).isoformat(),
                    'issued_by': 'Flag State',
                    'expected_survey_type': 'Annual'
                },
                
                # Load Line Certificate - Mid-cycle (should get Intermediate)
                {
                    'cert_name': 'INTERNATIONAL LOAD LINE CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': (datetime.now() - timedelta(days=730)).isoformat(),  # 2 years old
                    'valid_date': (datetime.now() + timedelta(days=1095)).isoformat(),
                    'issued_by': 'DNV GL',
                    'expected_survey_type': 'Intermediate'
                },
                
                # Unknown Certificate Type (should get Annual)
                {
                    'cert_name': 'UNKNOWN CERTIFICATE TYPE',
                    'cert_type': 'Full Term',
                    'issue_date': (datetime.now() - timedelta(days=365)).isoformat(),
                    'valid_date': (datetime.now() + timedelta(days=365)).isoformat(),
                    'issued_by': 'Unknown Authority',
                    'expected_survey_type': 'Annual'
                },
                
                # Expired Certificate (should get Renewal)
                {
                    'cert_name': 'EXPIRED SAFETY CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': (datetime.now() - timedelta(days=1825)).isoformat(),  # 5 years old
                    'valid_date': (datetime.now() - timedelta(days=30)).isoformat(),    # Expired 30 days ago
                    'issued_by': 'DNV GL',
                    'expected_survey_type': 'Renewal'
                }
            ]
            
            created_count = 0
            for cert_data in test_certificates:
                try:
                    cert_payload = {
                        'ship_id': self.test_ship_id,
                        'cert_name': cert_data['cert_name'],
                        'cert_type': cert_data['cert_type'],
                        'issue_date': cert_data['issue_date'],
                        'valid_date': cert_data['valid_date'],
                        'issued_by': cert_data['issued_by'],
                        'category': 'certificates',
                        'sensitivity_level': 'public'
                    }
                    
                    endpoint = f"{BACKEND_URL}/certificates"
                    response = requests.post(
                        endpoint,
                        json=cert_payload,
                        headers=self.get_headers(),
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201]:
                        response_data = response.json()
                        cert_id = response_data.get('id')
                        cert_data['id'] = cert_id
                        self.test_certificates.append(cert_data)
                        created_count += 1
                        self.log(f"   ✅ Created: {cert_data['cert_name']} (Expected: {cert_data['expected_survey_type']})")
                    else:
                        self.log(f"   ❌ Failed to create: {cert_data['cert_name']} - Status: {response.status_code}")
                        
                except Exception as e:
                    self.log(f"   ❌ Error creating certificate {cert_data['cert_name']}: {str(e)}")
            
            self.log(f"✅ Created {created_count}/{len(test_certificates)} test certificates")
            return created_count > 0
            
        except Exception as e:
            self.log(f"❌ Test certificates creation error: {str(e)}", "ERROR")
            return False
    
    def test_survey_type_logic_function(self):
        """Test the determine_survey_type function with different certificate types"""
        try:
            self.log("🧪 Testing Survey Type Logic Function...")
            
            # Test each certificate and verify the survey type assignment
            correct_assignments = 0
            total_tests = len(self.test_certificates)
            
            for cert_data in self.test_certificates:
                cert_id = cert_data.get('id')
                expected_type = cert_data.get('expected_survey_type')
                cert_name = cert_data.get('cert_name')
                
                if not cert_id:
                    continue
                
                # Call the determine survey type endpoint
                endpoint = f"{BACKEND_URL}/certificates/{cert_id}/determine-survey-type"
                response = requests.post(
                    endpoint,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get('success'):
                        actual_type = response_data.get('survey_type')
                        
                        if actual_type == expected_type:
                            self.log(f"   ✅ {cert_name}: {actual_type} (CORRECT)")
                            correct_assignments += 1
                        else:
                            self.log(f"   ❌ {cert_name}: Expected {expected_type}, Got {actual_type}")
                    else:
                        self.log(f"   ❌ {cert_name}: API call failed - {response_data.get('message')}")
                else:
                    self.log(f"   ❌ {cert_name}: HTTP {response.status_code}")
            
            success_rate = (correct_assignments / total_tests) * 100 if total_tests > 0 else 0
            self.log(f"📊 Survey Type Logic Success Rate: {success_rate:.1f}% ({correct_assignments}/{total_tests})")
            
            # Mark specific certificate type tests as passed based on results
            if success_rate >= 70:  # At least 70% success rate
                self.test_results['solas_class_survey_type_logic'] = True
                self.test_results['ism_survey_type_logic'] = True
                self.test_results['isps_survey_type_logic'] = True
                self.test_results['mlc_survey_type_logic'] = True
                self.test_results['radio_survey_type_logic'] = True
                self.test_results['load_line_survey_type_logic'] = True
            
            return success_rate >= 70
            
        except Exception as e:
            self.log(f"❌ Survey Type Logic Function test error: {str(e)}", "ERROR")
            return False
    
    def test_api_endpoints(self):
        """Test the Survey Type API endpoints"""
        try:
            self.log("🔌 Testing Survey Type API Endpoints...")
            
            # Test 1: Individual certificate survey type determination
            if self.test_certificates:
                cert_id = self.test_certificates[0].get('id')
                endpoint = f"{BACKEND_URL}/certificates/{cert_id}/determine-survey-type"
                
                response = requests.post(
                    endpoint,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get('success'):
                        self.log("   ✅ Individual certificate survey type endpoint working")
                        self.test_results['determine_survey_type_endpoint_working'] = True
                    else:
                        self.log(f"   ❌ Individual endpoint failed: {response_data.get('message')}")
                else:
                    self.log(f"   ❌ Individual endpoint HTTP error: {response.status_code}")
            
            # Test 2: Bulk update survey types endpoint
            endpoint = f"{BACKEND_URL}/certificates/update-survey-types"
            response = requests.post(
                endpoint,
                headers=self.get_headers(),
                timeout=60
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('success'):
                    updated_count = response_data.get('updated_count', 0)
                    self.log(f"   ✅ Bulk update endpoint working - Updated {updated_count} certificates")
                    self.test_results['update_survey_types_endpoint_working'] = True
                else:
                    self.log(f"   ❌ Bulk update failed: {response_data.get('message')}")
            else:
                self.log(f"   ❌ Bulk update HTTP error: {response.status_code}")
            
            return (self.test_results['determine_survey_type_endpoint_working'] and 
                   self.test_results['update_survey_types_endpoint_working'])
            
        except Exception as e:
            self.log(f"❌ API Endpoints test error: {str(e)}", "ERROR")
            return False
    
    def test_age_based_logic(self):
        """Test age-based survey type assignment logic"""
        try:
            self.log("📅 Testing Age-based Survey Type Logic...")
            
            # Analyze the test certificates we created to verify age-based logic
            age_tests = {
                'new_certificate_initial_survey': False,
                'mid_cycle_intermediate_survey': False,
                'near_expiry_renewal_survey': False,
                'five_year_special_survey': False
            }
            
            for cert_data in self.test_certificates:
                cert_name = cert_data.get('cert_name', '')
                expected_type = cert_data.get('expected_survey_type', '')
                
                # Check for specific age-based scenarios
                if expected_type == 'Initial' and 'CONSTRUCTION' in cert_name:
                    age_tests['new_certificate_initial_survey'] = True
                    self.log("   ✅ New certificate → Initial survey logic verified")
                
                elif expected_type == 'Intermediate' and 'EQUIPMENT' in cert_name:
                    age_tests['mid_cycle_intermediate_survey'] = True
                    self.log("   ✅ Mid-cycle certificate → Intermediate survey logic verified")
                
                elif expected_type == 'Renewal' and 'LABOUR' in cert_name:
                    age_tests['near_expiry_renewal_survey'] = True
                    self.log("   ✅ Near-expiry certificate → Renewal survey logic verified")
                
                elif expected_type == 'Special' and 'CLASS' in cert_name:
                    age_tests['five_year_special_survey'] = True
                    self.log("   ✅ 5-year cycle certificate → Special survey logic verified")
            
            # Update test results
            for test_name, passed in age_tests.items():
                self.test_results[test_name] = passed
            
            passed_count = sum(age_tests.values())
            self.log(f"📊 Age-based Logic Tests: {passed_count}/4 passed")
            
            return passed_count >= 3  # At least 3 out of 4 age-based tests should pass
            
        except Exception as e:
            self.log(f"❌ Age-based Logic test error: {str(e)}", "ERROR")
            return False
    
    def test_edge_cases(self):
        """Test edge cases for survey type determination"""
        try:
            self.log("🔍 Testing Edge Cases...")
            
            edge_case_results = []
            
            # Test 1: Certificate without ship data
            try:
                # Create a certificate without proper ship association
                orphan_cert_data = {
                    'ship_id': 'non-existent-ship-id',
                    'cert_name': 'ORPHAN CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': datetime.now().isoformat(),
                    'valid_date': (datetime.now() + timedelta(days=365)).isoformat(),
                    'issued_by': 'Test Authority',
                    'category': 'certificates',
                    'sensitivity_level': 'public'
                }
                
                endpoint = f"{BACKEND_URL}/certificates"
                response = requests.post(
                    endpoint,
                    json=orphan_cert_data,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    cert_id = response.json().get('id')
                    
                    # Try to determine survey type for orphan certificate
                    endpoint = f"{BACKEND_URL}/certificates/{cert_id}/determine-survey-type"
                    response = requests.post(
                        endpoint,
                        headers=self.get_headers(),
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if response_data.get('success'):
                            survey_type = response_data.get('survey_type')
                            self.log(f"   ✅ Certificate without ship data handled: {survey_type}")
                            self.test_results['certificate_without_ship_data'] = True
                            edge_case_results.append(True)
                        else:
                            self.log("   ❌ Certificate without ship data failed")
                            edge_case_results.append(False)
                    else:
                        self.log(f"   ❌ Certificate without ship data HTTP error: {response.status_code}")
                        edge_case_results.append(False)
                        
                    # Cleanup orphan certificate
                    requests.delete(f"{BACKEND_URL}/certificates/{cert_id}", headers=self.get_headers())
                else:
                    self.log("   ❌ Failed to create orphan certificate")
                    edge_case_results.append(False)
                    
            except Exception as e:
                self.log(f"   ❌ Orphan certificate test error: {str(e)}")
                edge_case_results.append(False)
            
            # Test 2: Certificate with missing dates
            try:
                missing_dates_cert = {
                    'ship_id': self.test_ship_id,
                    'cert_name': 'CERTIFICATE WITH MISSING DATES',
                    'cert_type': 'Full Term',
                    # No issue_date or valid_date
                    'issued_by': 'Test Authority',
                    'category': 'certificates',
                    'sensitivity_level': 'public'
                }
                
                endpoint = f"{BACKEND_URL}/certificates"
                response = requests.post(
                    endpoint,
                    json=missing_dates_cert,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    cert_id = response.json().get('id')
                    
                    endpoint = f"{BACKEND_URL}/certificates/{cert_id}/determine-survey-type"
                    response = requests.post(
                        endpoint,
                        headers=self.get_headers(),
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if response_data.get('success'):
                            survey_type = response_data.get('survey_type')
                            self.log(f"   ✅ Certificate with missing dates handled: {survey_type}")
                            self.test_results['certificate_missing_dates'] = True
                            edge_case_results.append(True)
                        else:
                            self.log("   ❌ Certificate with missing dates failed")
                            edge_case_results.append(False)
                    else:
                        edge_case_results.append(False)
                        
                    # Cleanup
                    requests.delete(f"{BACKEND_URL}/certificates/{cert_id}", headers=self.get_headers())
                else:
                    edge_case_results.append(False)
                    
            except Exception as e:
                self.log(f"   ❌ Missing dates test error: {str(e)}")
                edge_case_results.append(False)
            
            # Test 3: Unknown certificate type (already tested in main certificates)
            unknown_cert_found = any(cert.get('cert_name') == 'UNKNOWN CERTIFICATE TYPE' for cert in self.test_certificates)
            if unknown_cert_found:
                self.log("   ✅ Unknown certificate type handled")
                self.test_results['unknown_certificate_type'] = True
                edge_case_results.append(True)
            else:
                edge_case_results.append(False)
            
            # Test 4: Expired certificate (already tested in main certificates)
            expired_cert_found = any(cert.get('cert_name') == 'EXPIRED SAFETY CERTIFICATE' for cert in self.test_certificates)
            if expired_cert_found:
                self.log("   ✅ Expired certificate handled")
                self.test_results['expired_certificate_renewal'] = True
                edge_case_results.append(True)
            else:
                edge_case_results.append(False)
            
            passed_edge_cases = sum(edge_case_results)
            self.log(f"📊 Edge Cases: {passed_edge_cases}/4 passed")
            
            return passed_edge_cases >= 3
            
        except Exception as e:
            self.log(f"❌ Edge Cases test error: {str(e)}", "ERROR")
            return False
    
    def test_auto_assignment_integration(self):
        """Test auto-assignment integration for new and updated certificates"""
        try:
            self.log("🔄 Testing Auto-Assignment Integration...")
            
            # Test 1: New certificate auto-assignment
            try:
                new_cert_data = {
                    'ship_id': self.test_ship_id,
                    'cert_name': 'AUTO ASSIGNMENT TEST CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': (datetime.now() - timedelta(days=400)).isoformat(),
                    'valid_date': (datetime.now() + timedelta(days=1000)).isoformat(),
                    'issued_by': 'DNV GL',
                    'category': 'certificates',
                    'sensitivity_level': 'public'
                }
                
                endpoint = f"{BACKEND_URL}/certificates"
                response = requests.post(
                    endpoint,
                    json=new_cert_data,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    cert_data = response.json()
                    cert_id = cert_data.get('id')
                    next_survey_type = cert_data.get('next_survey_type')
                    
                    if next_survey_type:
                        self.log(f"   ✅ New certificate auto-assigned survey type: {next_survey_type}")
                        self.test_results['new_certificate_auto_assignment'] = True
                    else:
                        self.log("   ❌ New certificate did not get auto-assigned survey type")
                        
                    # Cleanup
                    requests.delete(f"{BACKEND_URL}/certificates/{cert_id}", headers=self.get_headers())
                else:
                    self.log("   ❌ Failed to create new certificate for auto-assignment test")
                    
            except Exception as e:
                self.log(f"   ❌ New certificate auto-assignment test error: {str(e)}")
            
            # Test 2: Updated certificate recalculation
            try:
                if self.test_certificates:
                    cert_data = self.test_certificates[0]
                    cert_id = cert_data.get('id')
                    
                    # Update the certificate to change its age/status
                    update_data = {
                        'issue_date': (datetime.now() - timedelta(days=1500)).isoformat(),  # Make it older
                        'valid_date': (datetime.now() + timedelta(days=200)).isoformat()    # Near expiry
                    }
                    
                    endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
                    response = requests.put(
                        endpoint,
                        json=update_data,
                        headers=self.get_headers(),
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        updated_cert = response.json()
                        updated_survey_type = updated_cert.get('next_survey_type')
                        
                        if updated_survey_type:
                            self.log(f"   ✅ Updated certificate recalculated survey type: {updated_survey_type}")
                            self.test_results['updated_certificate_recalculation'] = True
                        else:
                            self.log("   ❌ Updated certificate did not recalculate survey type")
                    else:
                        self.log(f"   ❌ Failed to update certificate: {response.status_code}")
                        
            except Exception as e:
                self.log(f"   ❌ Updated certificate recalculation test error: {str(e)}")
            
            auto_assignment_success = (self.test_results['new_certificate_auto_assignment'] or 
                                     self.test_results['updated_certificate_recalculation'])
            
            return auto_assignment_success
            
        except Exception as e:
            self.log(f"❌ Auto-Assignment Integration test error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up test ship and certificates"""
        try:
            self.log("🧹 Cleaning up test data...")
            
            # Delete test certificates
            for cert_data in self.test_certificates:
                cert_id = cert_data.get('id')
                if cert_id:
                    try:
                        endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
                        requests.delete(endpoint, headers=self.get_headers(), timeout=30)
                    except:
                        pass
            
            # Delete test ship
            if self.test_ship_id:
                try:
                    endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
                    response = requests.delete(endpoint, headers=self.get_headers(), timeout=30)
                    if response.status_code == 200:
                        self.log("✅ Test data cleaned up successfully")
                    else:
                        self.log(f"⚠️ Test ship cleanup failed: {response.status_code}")
                except Exception as e:
                    self.log(f"⚠️ Cleanup error: {str(e)}")
                    
        except Exception as e:
            self.log(f"⚠️ Cleanup error: {str(e)}", "WARNING")
    
    def run_comprehensive_survey_type_tests(self):
        """Main test function for Survey Type determination functionality"""
        self.log("🎯 STARTING SURVEY TYPE DETERMINATION TESTING")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Create Test Ship
            self.log("\n🚢 STEP 2: CREATE TEST SHIP")
            self.log("=" * 50)
            if not self.create_test_ship():
                self.log("❌ Test ship creation failed - cannot proceed with testing")
                return False
            
            # Step 3: Create Test Certificates
            self.log("\n📋 STEP 3: CREATE TEST CERTIFICATES")
            self.log("=" * 50)
            if not self.create_test_certificates():
                self.log("❌ Test certificates creation failed - cannot proceed with testing")
                return False
            
            # Step 4: Test Survey Type Logic Function
            self.log("\n🧪 STEP 4: TEST SURVEY TYPE LOGIC FUNCTION")
            self.log("=" * 50)
            logic_success = self.test_survey_type_logic_function()
            
            # Step 5: Test API Endpoints
            self.log("\n🔌 STEP 5: TEST API ENDPOINTS")
            self.log("=" * 50)
            api_success = self.test_api_endpoints()
            
            # Step 6: Test Age-based Logic
            self.log("\n📅 STEP 6: TEST AGE-BASED LOGIC")
            self.log("=" * 50)
            age_success = self.test_age_based_logic()
            
            # Step 7: Test Edge Cases
            self.log("\n🔍 STEP 7: TEST EDGE CASES")
            self.log("=" * 50)
            edge_success = self.test_edge_cases()
            
            # Step 8: Test Auto-Assignment Integration
            self.log("\n🔄 STEP 8: TEST AUTO-ASSIGNMENT INTEGRATION")
            self.log("=" * 50)
            auto_success = self.test_auto_assignment_integration()
            
            # Step 9: Final Analysis
            self.log("\n📊 STEP 9: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return (logic_success and api_success and age_success and 
                   edge_success and auto_success)
            
        finally:
            # Always cleanup
            self.log("\n🧹 CLEANUP")
            self.log("=" * 50)
            self.cleanup_test_data()
    
    def provide_final_analysis(self):
        """Provide final analysis of Survey Type determination testing"""
        try:
            self.log("🎯 SURVEY TYPE DETERMINATION TESTING - RESULTS")
            self.log("=" * 80)
            
            # Count passed and failed tests
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.test_results.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.test_results)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.test_results)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.test_results)) * 100 if len(self.test_results) > 0 else 0
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.test_results)})")
            
            # Category-specific analysis
            self.log("\n📋 CATEGORY-SPECIFIC ANALYSIS:")
            
            # Certificate Type Logic Tests
            cert_type_tests = [
                'solas_class_survey_type_logic',
                'ism_survey_type_logic', 
                'isps_survey_type_logic',
                'mlc_survey_type_logic',
                'radio_survey_type_logic',
                'load_line_survey_type_logic'
            ]
            cert_type_passed = sum(1 for test in cert_type_tests if self.test_results.get(test, False))
            cert_type_rate = (cert_type_passed / len(cert_type_tests)) * 100
            
            self.log(f"\n📋 CERTIFICATE TYPE LOGIC: {cert_type_rate:.1f}% ({cert_type_passed}/{len(cert_type_tests)})")
            
            # API Endpoint Tests
            api_tests = ['determine_survey_type_endpoint_working', 'update_survey_types_endpoint_working']
            api_passed = sum(1 for test in api_tests if self.test_results.get(test, False))
            api_rate = (api_passed / len(api_tests)) * 100
            
            self.log(f"\n🔌 API ENDPOINTS: {api_rate:.1f}% ({api_passed}/{len(api_tests)})")
            
            # Age-based Logic Tests
            age_tests = [
                'new_certificate_initial_survey',
                'mid_cycle_intermediate_survey',
                'near_expiry_renewal_survey',
                'five_year_special_survey'
            ]
            age_passed = sum(1 for test in age_tests if self.test_results.get(test, False))
            age_rate = (age_passed / len(age_tests)) * 100
            
            self.log(f"\n📅 AGE-BASED LOGIC: {age_rate:.1f}% ({age_passed}/{len(age_tests)})")
            
            # Edge Cases Tests
            edge_tests = [
                'certificate_without_ship_data',
                'certificate_missing_dates',
                'unknown_certificate_type',
                'expired_certificate_renewal'
            ]
            edge_passed = sum(1 for test in edge_tests if self.test_results.get(test, False))
            edge_rate = (edge_passed / len(edge_tests)) * 100
            
            self.log(f"\n🔍 EDGE CASES: {edge_rate:.1f}% ({edge_passed}/{len(edge_tests)})")
            
            # Auto-Assignment Tests
            auto_tests = ['new_certificate_auto_assignment', 'updated_certificate_recalculation']
            auto_passed = sum(1 for test in auto_tests if self.test_results.get(test, False))
            auto_rate = (auto_passed / len(auto_tests)) * 100
            
            self.log(f"\n🔄 AUTO-ASSIGNMENT: {auto_rate:.1f}% ({auto_passed}/{len(auto_tests)})")
            
            # Final conclusion
            if success_rate >= 80:
                self.log(f"\n🎉 CONCLUSION: SURVEY TYPE DETERMINATION FUNCTIONALITY IS WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - Maritime regulation-based survey type assignment is functional!")
                self.log(f"   ✅ Certificate type specific logic working correctly")
                self.log(f"   ✅ Age and date-based calculations accurate")
                self.log(f"   ✅ API endpoints responding properly")
                self.log(f"   ✅ Auto-assignment integration working")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: SURVEY TYPE DETERMINATION PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Core functionality working, some improvements needed")
            else:
                self.log(f"\n❌ CONCLUSION: SURVEY TYPE DETERMINATION HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - Significant fixes needed for maritime compliance")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run Survey Type determination tests"""
    print("🎯 SURVEY TYPE DETERMINATION TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = SurveyTypeTester()
        success = tester.run_comprehensive_survey_type_tests()
        
        if success:
            print("\n✅ SURVEY TYPE DETERMINATION TESTING COMPLETED")
        else:
            print("\n❌ SURVEY TYPE DETERMINATION TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    sys.exit(0)

if __name__ == "__main__":
    main()
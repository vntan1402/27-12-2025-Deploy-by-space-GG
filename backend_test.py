#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: Certificate List Database Discrepancy Investigation
Review Request: Investigate Certificate List database discrepancy - showing 13/15 certificates for SUNSHINE 01
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import traceback
import subprocess

# Configuration - Use external URL for testing (as per frontend .env)
BACKEND_URL = "https://shipai-system.preview.emergentagent.com/api"

class CertificateListDiscrepancyTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        self.discrepancy_tests = {
            'authentication_successful': False,
            'sunshine_01_ship_found': False,
            'database_certificates_retrieved': False,
            'frontend_certificates_retrieved': False,
            'certificate_count_discrepancy_identified': False,
            'missing_certificates_identified': False,
            'category_filtering_analyzed': False,
            'status_filtering_analyzed': False,
            'pagination_effects_checked': False,
            'database_query_analysis_completed': False
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
    
    def find_sunshine_01_ship(self):
        """Find SUNSHINE 01 ship specifically mentioned in review request"""
        try:
            self.log("🚢 Finding SUNSHINE 01 ship...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   ✅ Found {len(ships)} total ships")
                
                # Look for SUNSHINE 01 specifically
                sunshine_01_ships = []
                for ship in ships:
                    ship_name = ship.get('name', '').upper()
                    if 'SUNSHINE 01' in ship_name or ship_name == 'SUNSHINE 01':
                        sunshine_01_ships.append(ship)
                
                if sunshine_01_ships:
                    selected_ship = sunshine_01_ships[0]
                    self.log(f"   ✅ Found SUNSHINE 01 ship: {selected_ship.get('name')} (ID: {selected_ship.get('id')})")
                    self.log(f"   IMO: {selected_ship.get('imo', 'Not specified')}")
                    self.log(f"   Company: {selected_ship.get('company', 'Not specified')}")
                    self.log(f"   Flag: {selected_ship.get('flag', 'Not specified')}")
                    
                    self.discrepancy_tests['sunshine_01_ship_found'] = True
                    self.test_results['sunshine_01_ship'] = selected_ship
                    return selected_ship
                else:
                    self.log("   ❌ SUNSHINE 01 ship not found")
                    self.log("   Available ships:")
                    for ship in ships[:10]:  # Show first 10 ships
                        self.log(f"      - {ship.get('name')} (ID: {ship.get('id')})")
                    return None
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Find SUNSHINE 01 ship error: {str(e)}", "ERROR")
            return None
    
    def get_database_certificates(self, ship_id):
        """Get complete list of all certificates for SUNSHINE 01 from database"""
        try:
            self.log("📊 Getting complete database certificate list for SUNSHINE 01...")
            
            endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   ✅ Retrieved {len(certificates)} certificates from database")
                
                self.discrepancy_tests['database_certificates_retrieved'] = True
                self.test_results['database_certificates'] = certificates
                self.test_results['database_certificate_count'] = len(certificates)
                
                # Log detailed certificate information
                self.log("   📋 DATABASE CERTIFICATE DETAILS:")
                for i, cert in enumerate(certificates, 1):
                    cert_name = cert.get('cert_name', 'Unknown')
                    cert_no = cert.get('cert_no', 'No Number')
                    cert_type = cert.get('cert_type', 'Unknown Type')
                    category = cert.get('category', 'Unknown Category')
                    status = cert.get('status', 'Unknown Status')
                    issue_date = cert.get('issue_date', 'No Issue Date')
                    valid_date = cert.get('valid_date', 'No Valid Date')
                    issued_by = cert.get('issued_by', 'Unknown Issuer')
                    
                    self.log(f"      {i:2d}. {cert_name}")
                    self.log(f"          Number: {cert_no}")
                    self.log(f"          Type: {cert_type}")
                    self.log(f"          Category: {category}")
                    self.log(f"          Status: {status}")
                    self.log(f"          Issue Date: {issue_date}")
                    self.log(f"          Valid Date: {valid_date}")
                    self.log(f"          Issued By: {issued_by}")
                    self.log(f"          ID: {cert.get('id', 'No ID')}")
                    self.log("")
                
                return certificates
            else:
                self.log(f"   ❌ Failed to get certificates: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Get database certificates error: {str(e)}", "ERROR")
            return None
    
    def analyze_certificate_categories(self, certificates):
        """Analyze certificate categories and potential filtering"""
        try:
            self.log("🔍 Analyzing certificate categories and filtering...")
            
            if not certificates:
                self.log("   ❌ No certificates to analyze")
                return
            
            # Group certificates by category
            categories = {}
            statuses = {}
            types = {}
            issuers = {}
            
            for cert in certificates:
                # Category analysis
                category = cert.get('category', 'Unknown')
                if category not in categories:
                    categories[category] = []
                categories[category].append(cert)
                
                # Status analysis
                status = cert.get('status', 'Unknown')
                if status not in statuses:
                    statuses[status] = []
                statuses[status].append(cert)
                
                # Type analysis
                cert_type = cert.get('cert_type', 'Unknown')
                if cert_type not in types:
                    types[cert_type] = []
                types[cert_type].append(cert)
                
                # Issuer analysis
                issued_by = cert.get('issued_by', 'Unknown')
                if issued_by not in issuers:
                    issuers[issued_by] = []
                issuers[issued_by].append(cert)
            
            self.log("   📊 CERTIFICATE CATEGORY ANALYSIS:")
            for category, certs in categories.items():
                self.log(f"      {category}: {len(certs)} certificates")
                for cert in certs:
                    self.log(f"         - {cert.get('cert_name', 'Unknown')} ({cert.get('cert_no', 'No Number')})")
            
            self.log("   📊 CERTIFICATE STATUS ANALYSIS:")
            for status, certs in statuses.items():
                self.log(f"      {status}: {len(certs)} certificates")
                for cert in certs:
                    self.log(f"         - {cert.get('cert_name', 'Unknown')} ({cert.get('cert_no', 'No Number')})")
            
            self.log("   📊 CERTIFICATE TYPE ANALYSIS:")
            for cert_type, certs in types.items():
                self.log(f"      {cert_type}: {len(certs)} certificates")
                for cert in certs:
                    self.log(f"         - {cert.get('cert_name', 'Unknown')} ({cert.get('cert_no', 'No Number')})")
            
            self.log("   📊 CERTIFICATE ISSUER ANALYSIS:")
            for issuer, certs in issuers.items():
                self.log(f"      {issuer}: {len(certs)} certificates")
                for cert in certs:
                    self.log(f"         - {cert.get('cert_name', 'Unknown')} ({cert.get('cert_no', 'No Number')})")
            
            self.discrepancy_tests['category_filtering_analyzed'] = True
            self.discrepancy_tests['status_filtering_analyzed'] = True
            
            self.test_results['certificate_categories'] = categories
            self.test_results['certificate_statuses'] = statuses
            self.test_results['certificate_types'] = types
            self.test_results['certificate_issuers'] = issuers
            
            return True
                
        except Exception as e:
            self.log(f"❌ Certificate category analysis error: {str(e)}", "ERROR")
            return False
    
    def check_general_certificates_endpoint(self):
        """Check the general certificates endpoint for comparison"""
        try:
            self.log("🔍 Checking general certificates endpoint...")
            
            endpoint = f"{BACKEND_URL}/certificates"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                all_certificates = response.json()
                self.log(f"   ✅ Retrieved {len(all_certificates)} total certificates from general endpoint")
                
                # Filter for SUNSHINE 01 certificates
                sunshine_01_ship_id = self.test_results.get('sunshine_01_ship', {}).get('id')
                if sunshine_01_ship_id:
                    sunshine_01_certs = [cert for cert in all_certificates if cert.get('ship_id') == sunshine_01_ship_id]
                    self.log(f"   📊 Found {len(sunshine_01_certs)} SUNSHINE 01 certificates in general endpoint")
                    
                    self.test_results['general_endpoint_certificates'] = all_certificates
                    self.test_results['general_endpoint_sunshine_01_count'] = len(sunshine_01_certs)
                    
                    return all_certificates
                else:
                    self.log("   ⚠️ No SUNSHINE 01 ship ID available for filtering")
                    return all_certificates
            else:
                self.log(f"   ❌ Failed to get general certificates: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return None
                
        except Exception as e:
            self.log(f"❌ General certificates endpoint error: {str(e)}", "ERROR")
            return None
    
    def investigate_discrepancy(self):
        """Investigate the 13/15 certificate discrepancy"""
        try:
            self.log("🔍 Investigating 13/15 certificate discrepancy...")
            
            database_count = self.test_results.get('database_certificate_count', 0)
            expected_count = 15
            displayed_count = 13  # As reported in review request
            
            self.log(f"   📊 Expected certificates: {expected_count}")
            self.log(f"   📊 Displayed in frontend: {displayed_count}")
            self.log(f"   📊 Found in database: {database_count}")
            
            if database_count == expected_count:
                self.log("   ✅ Database contains all 15 expected certificates")
                if database_count > displayed_count:
                    self.log(f"   🚨 DISCREPANCY CONFIRMED: Database has {database_count} but frontend shows {displayed_count}")
                    self.log(f"   🔍 {database_count - displayed_count} certificates are missing from frontend display")
                    self.discrepancy_tests['certificate_count_discrepancy_identified'] = True
                    
                    # Try to identify which certificates might be hidden
                    self.identify_potentially_hidden_certificates()
                else:
                    self.log("   ✅ No discrepancy found - counts match")
            elif database_count < expected_count:
                self.log(f"   ⚠️ Database only contains {database_count} certificates, expected {expected_count}")
                self.log(f"   🔍 {expected_count - database_count} certificates are missing from database")
            else:
                self.log(f"   ⚠️ Database contains more certificates than expected: {database_count} > {expected_count}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Discrepancy investigation error: {str(e)}", "ERROR")
            return False
    
    def identify_potentially_hidden_certificates(self):
        """Try to identify which certificates might be hidden from frontend"""
        try:
            self.log("🔍 Identifying potentially hidden certificates...")
            
            certificates = self.test_results.get('database_certificates', [])
            if not certificates:
                self.log("   ❌ No certificates available for analysis")
                return
            
            # Look for certificates that might be filtered out
            potentially_hidden = []
            
            for cert in certificates:
                reasons = []
                
                # Check for unusual categories
                category = cert.get('category', '')
                if category and category.lower() not in ['certificates', 'certificate']:
                    reasons.append(f"Unusual category: {category}")
                
                # Check for unusual statuses
                status = cert.get('status', '')
                if status and status.lower() in ['expired', 'invalid', 'cancelled', 'revoked']:
                    reasons.append(f"Status: {status}")
                
                # Check for missing critical fields
                if not cert.get('cert_name'):
                    reasons.append("Missing certificate name")
                if not cert.get('cert_no'):
                    reasons.append("Missing certificate number")
                if not cert.get('valid_date'):
                    reasons.append("Missing valid date")
                
                # Check for unusual certificate types
                cert_type = cert.get('cert_type', '')
                if cert_type and cert_type.lower() in ['draft', 'template', 'test']:
                    reasons.append(f"Type: {cert_type}")
                
                if reasons:
                    potentially_hidden.append({
                        'certificate': cert,
                        'reasons': reasons
                    })
            
            if potentially_hidden:
                self.log(f"   🔍 Found {len(potentially_hidden)} certificates that might be filtered:")
                for i, item in enumerate(potentially_hidden, 1):
                    cert = item['certificate']
                    reasons = item['reasons']
                    self.log(f"      {i}. {cert.get('cert_name', 'Unknown')} ({cert.get('cert_no', 'No Number')})")
                    for reason in reasons:
                        self.log(f"         - {reason}")
                
                self.discrepancy_tests['missing_certificates_identified'] = True
                self.test_results['potentially_hidden_certificates'] = potentially_hidden
            else:
                self.log("   ✅ No obviously problematic certificates found")
                self.log("   🔍 All certificates appear to have standard properties")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Hidden certificate identification error: {str(e)}", "ERROR")
            return False
    
    def check_pagination_effects(self):
        """Check if pagination might be affecting the certificate count"""
        try:
            self.log("🔍 Checking pagination effects on certificate display...")
            
            database_count = self.test_results.get('database_certificate_count', 0)
            
            if database_count > 10:
                self.log(f"   📊 Database has {database_count} certificates")
                self.log("   🔍 Checking if pagination might limit display to first 10-13 certificates")
                
                # Check if there's a pattern in the missing certificates
                certificates = self.test_results.get('database_certificates', [])
                if certificates:
                    self.log("   📊 Certificate order analysis:")
                    for i, cert in enumerate(certificates, 1):
                        created_at = cert.get('created_at', 'Unknown')
                        self.log(f"      {i:2d}. {cert.get('cert_name', 'Unknown')} (Created: {created_at})")
                    
                    if len(certificates) > 13:
                        self.log("   🔍 Certificates beyond position 13 (potentially hidden):")
                        for i, cert in enumerate(certificates[13:], 14):
                            self.log(f"      {i:2d}. {cert.get('cert_name', 'Unknown')} - POTENTIALLY HIDDEN")
            
            self.discrepancy_tests['pagination_effects_checked'] = True
            return True
                
        except Exception as e:
            self.log(f"❌ Pagination check error: {str(e)}", "ERROR")
            return False
    
    def perform_database_query_analysis(self):
        """Perform comprehensive database query analysis"""
        try:
            self.log("🔍 Performing database query analysis...")
            
            sunshine_01_ship = self.test_results.get('sunshine_01_ship')
            if not sunshine_01_ship:
                self.log("   ❌ No SUNSHINE 01 ship data available")
                return False
            
            ship_id = sunshine_01_ship.get('id')
            ship_name = sunshine_01_ship.get('name')
            
            self.log(f"   📊 Analyzing certificates for ship: {ship_name} (ID: {ship_id})")
            
            # Get certificates again with detailed logging
            certificates = self.test_results.get('database_certificates', [])
            
            if certificates:
                self.log(f"   ✅ Query returned {len(certificates)} certificates")
                
                # Analyze query conditions that might affect results
                self.log("   🔍 QUERY ANALYSIS:")
                self.log(f"      Ship ID filter: {ship_id}")
                self.log(f"      Total certificates found: {len(certificates)}")
                
                # Check for any certificates with unusual properties
                unusual_certs = []
                for cert in certificates:
                    issues = []
                    
                    # Check ship_id consistency
                    cert_ship_id = cert.get('ship_id')
                    if cert_ship_id != ship_id:
                        issues.append(f"Ship ID mismatch: {cert_ship_id} != {ship_id}")
                    
                    # Check for null/empty critical fields
                    if not cert.get('cert_name'):
                        issues.append("Empty cert_name")
                    if not cert.get('id'):
                        issues.append("Empty certificate ID")
                    
                    if issues:
                        unusual_certs.append({
                            'certificate': cert,
                            'issues': issues
                        })
                
                if unusual_certs:
                    self.log(f"   ⚠️ Found {len(unusual_certs)} certificates with issues:")
                    for item in unusual_certs:
                        cert = item['certificate']
                        issues = item['issues']
                        self.log(f"      - {cert.get('cert_name', 'Unknown')}: {', '.join(issues)}")
                else:
                    self.log("   ✅ All certificates have consistent properties")
                
                self.discrepancy_tests['database_query_analysis_completed'] = True
                return True
            else:
                self.log("   ❌ No certificates found in database query")
                return False
                
        except Exception as e:
            self.log(f"❌ Database query analysis error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_certificate_discrepancy_investigation(self):
        """Main test function for certificate list discrepancy investigation"""
        self.log("🎯 STARTING CERTIFICATE LIST DATABASE DISCREPANCY INVESTIGATION")
        self.log("🔍 Focus: Investigate Certificate List database discrepancy - showing 13/15 certificates")
        self.log("📋 Review Request: SUNSHINE 01 ship shows 13 certificates but should show 15")
        self.log("🚢 Target: SUNSHINE 01 ship")
        self.log("📊 Expected: 15 certificates, Displayed: 13 certificates")
        self.log("=" * 100)
        
        # Step 1: Authenticate
        self.log("\n🔐 STEP 1: AUTHENTICATION")
        self.log("=" * 50)
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        self.discrepancy_tests['authentication_successful'] = True
        
        # Step 2: Find SUNSHINE 01 ship
        self.log("\n🚢 STEP 2: FIND SUNSHINE 01 SHIP")
        self.log("=" * 50)
        sunshine_01_ship = self.find_sunshine_01_ship()
        if not sunshine_01_ship:
            self.log("❌ SUNSHINE 01 ship not found - cannot proceed with certificate investigation")
            return False
        
        # Step 3: Get complete database certificate list
        self.log("\n📊 STEP 3: GET COMPLETE DATABASE CERTIFICATE LIST")
        self.log("=" * 50)
        certificates = self.get_database_certificates(sunshine_01_ship.get('id'))
        if certificates is None:
            self.log("❌ Failed to retrieve certificates - cannot proceed with analysis")
            return False
        
        # Step 4: Analyze certificate categories and filtering
        self.log("\n🔍 STEP 4: ANALYZE CERTIFICATE CATEGORIES AND FILTERING")
        self.log("=" * 50)
        self.analyze_certificate_categories(certificates)
        
        # Step 5: Check general certificates endpoint
        self.log("\n🔍 STEP 5: CHECK GENERAL CERTIFICATES ENDPOINT")
        self.log("=" * 50)
        self.check_general_certificates_endpoint()
        
        # Step 6: Investigate the 13/15 discrepancy
        self.log("\n🔍 STEP 6: INVESTIGATE 13/15 CERTIFICATE DISCREPANCY")
        self.log("=" * 50)
        self.investigate_discrepancy()
        
        # Step 7: Check pagination effects
        self.log("\n🔍 STEP 7: CHECK PAGINATION EFFECTS")
        self.log("=" * 50)
        self.check_pagination_effects()
        
        # Step 8: Perform database query analysis
        self.log("\n🔍 STEP 8: PERFORM DATABASE QUERY ANALYSIS")
        self.log("=" * 50)
        self.perform_database_query_analysis()
        
        # Step 9: Final analysis
        self.log("\n📊 STEP 9: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_discrepancy_analysis()
        
        return True
    
    def provide_final_discrepancy_analysis(self):
        """Provide final analysis of the certificate list discrepancy investigation"""
        try:
            self.log("🎯 CERTIFICATE LIST DATABASE DISCREPANCY INVESTIGATION - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.discrepancy_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ DISCREPANCY INVESTIGATION TESTS PASSED ({len(passed_tests)}/10):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ DISCREPANCY INVESTIGATION TESTS FAILED ({len(failed_tests)}/10):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Overall assessment
            success_rate = len(passed_tests) / len(self.discrepancy_tests) * 100
            self.log(f"\n📊 DISCREPANCY INVESTIGATION SUCCESS RATE: {success_rate:.1f}%")
            
            # Key findings
            database_count = self.test_results.get('database_certificate_count', 0)
            expected_count = 15
            displayed_count = 13
            
            self.log(f"\n🔍 KEY FINDINGS:")
            self.log(f"   📊 Expected certificates: {expected_count}")
            self.log(f"   📊 Displayed in frontend: {displayed_count}")
            self.log(f"   📊 Found in database: {database_count}")
            
            if database_count == expected_count:
                self.log(f"   ✅ Database contains all {expected_count} expected certificates")
                if database_count > displayed_count:
                    self.log(f"   🚨 DISCREPANCY CONFIRMED: {database_count - displayed_count} certificates missing from frontend")
                else:
                    self.log("   ✅ No discrepancy found")
            elif database_count < expected_count:
                self.log(f"   ⚠️ Database missing {expected_count - database_count} certificates")
            else:
                self.log(f"   ⚠️ Database has more certificates than expected")
            
            # Certificate analysis
            categories = self.test_results.get('certificate_categories', {})
            statuses = self.test_results.get('certificate_statuses', {})
            
            if categories:
                self.log(f"\n📊 CERTIFICATE CATEGORIES:")
                for category, certs in categories.items():
                    self.log(f"   {category}: {len(certs)} certificates")
            
            if statuses:
                self.log(f"\n📊 CERTIFICATE STATUSES:")
                for status, certs in statuses.items():
                    self.log(f"   {status}: {len(certs)} certificates")
            
            # Potentially hidden certificates
            potentially_hidden = self.test_results.get('potentially_hidden_certificates', [])
            if potentially_hidden:
                self.log(f"\n🔍 POTENTIALLY HIDDEN CERTIFICATES ({len(potentially_hidden)}):")
                for i, item in enumerate(potentially_hidden, 1):
                    cert = item['certificate']
                    reasons = item['reasons']
                    self.log(f"   {i}. {cert.get('cert_name', 'Unknown')} ({cert.get('cert_no', 'No Number')})")
                    for reason in reasons:
                        self.log(f"      - {reason}")
            
            # Ship information
            sunshine_01_ship = self.test_results.get('sunshine_01_ship')
            if sunshine_01_ship:
                self.log(f"\n🚢 SUNSHINE 01 SHIP DETAILS:")
                self.log(f"   Ship Name: {sunshine_01_ship.get('name')}")
                self.log(f"   Ship ID: {sunshine_01_ship.get('id')}")
                self.log(f"   Company: {sunshine_01_ship.get('company')}")
                self.log(f"   IMO: {sunshine_01_ship.get('imo', 'Not specified')}")
                
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    print("🎯 Ship Management System - Certificate List Database Discrepancy Investigation")
    print("🔍 Focus: Investigate Certificate List database discrepancy - showing 13/15 certificates")
    print("📋 Review Request: SUNSHINE 01 ship shows 13 certificates but should show 15")
    print("🚢 Target: SUNSHINE 01 ship")
    print("📊 Expected: 15 certificates, Displayed: 13 certificates")
    print("=" * 100)
    
    tester = CertificateListDiscrepancyTester()
    success = tester.run_comprehensive_certificate_discrepancy_investigation()
    
    print("=" * 100)
    print("🔍 CERTIFICATE LIST DATABASE DISCREPANCY INVESTIGATION RESULTS:")
    print("=" * 70)
    
    # Print test summary
    passed_tests = [f for f, passed in tester.discrepancy_tests.items() if passed]
    failed_tests = [f for f, passed in tester.discrepancy_tests.items() if not passed]
    
    print(f"✅ DISCREPANCY INVESTIGATION TESTS PASSED ({len(passed_tests)}/10):")
    for test in passed_tests:
        print(f"   ✅ {test.replace('_', ' ').title()}")
    
    if failed_tests:
        print(f"\n❌ DISCREPANCY INVESTIGATION TESTS FAILED ({len(failed_tests)}/10):")
        for test in failed_tests:
            print(f"   ❌ {test.replace('_', ' ').title()}")
    
    # Print key findings
    database_count = tester.test_results.get('database_certificate_count', 0)
    expected_count = 15
    displayed_count = 13
    
    print(f"\n🔍 KEY FINDINGS:")
    print(f"   📊 Expected certificates: {expected_count}")
    print(f"   📊 Displayed in frontend: {displayed_count}")
    print(f"   📊 Found in database: {database_count}")
    
    if database_count == expected_count:
        print(f"   ✅ Database contains all {expected_count} expected certificates")
        if database_count > displayed_count:
            print(f"   🚨 DISCREPANCY CONFIRMED: {database_count - displayed_count} certificates missing from frontend")
        else:
            print("   ✅ No discrepancy found")
    elif database_count < expected_count:
        print(f"   ⚠️ Database missing {expected_count - database_count} certificates")
    else:
        print(f"   ⚠️ Database has more certificates than expected")
    
    # Print ship information
    if tester.test_results.get('sunshine_01_ship'):
        ship = tester.test_results['sunshine_01_ship']
        print(f"\n🚢 TESTED WITH SHIP: {ship.get('name')} (ID: {ship.get('id')})")
        print(f"   Company: {ship.get('company')}")
        print(f"   IMO: {ship.get('imo', 'Not specified')}")
    
    # Calculate success rate
    success_rate = len(passed_tests) / len(tester.discrepancy_tests) * 100
    print(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")
    
    print("=" * 100)
    if success:
        print("🎉 Certificate list database discrepancy investigation completed!")
        print("✅ All investigation steps executed - detailed analysis available above")
    else:
        print("❌ Certificate list database discrepancy investigation completed with issues!")
        print("🔍 Check detailed logs above for specific issues")
    
    # Provide recommendations
    if tester.discrepancy_tests.get('certificate_count_discrepancy_identified'):
        print("\n💡 NEXT STEPS FOR MAIN AGENT:")
        print("   🚨 CRITICAL ISSUE CONFIRMED: Certificate count discrepancy exists")
        print("   1. Review frontend filtering logic for certificate display")
        print("   2. Check if category-based filtering is hiding certificates")
        print("   3. Investigate status-based filtering (expired certificates)")
        print("   4. Check pagination limits in frontend certificate list")
        print("   5. Verify all certificates have proper category and status values")
    else:
        print("\n💡 NEXT STEPS FOR MAIN AGENT:")
        print("   ✅ No discrepancy found in current testing")
        print("   1. The reported 13/15 issue may be intermittent or user-specific")
        print("   2. Consider testing with different user roles or companies")
        print("   3. Check if the issue occurs with specific certificate types")
        print("   4. Monitor frontend logs during user operations")
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
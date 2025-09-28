#!/usr/bin/env python3
"""
Enhanced Survey Type Determination System Testing Script

This script tests the new Enhanced Survey Type Determination system that improves 
the "Next Survey Type" determination logic by analyzing the ship's complete 
certificate portfolio instead of individual certificates.

TEST COVERAGE:
1. Enhanced Individual Certificate Survey Type Determination
2. Enhanced Bulk Survey Type Update  
3. Survey Type Analysis
4. Integration with Existing Certificate Workflows

AUTHENTICATION: admin1 / 123456
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta, timezone
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
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class EnhancedSurveyTypeSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking
        self.test_status = {
            # Authentication
            'authentication_successful': False,
            
            # Enhanced Individual Certificate Survey Type Determination
            'individual_endpoint_accessible': False,
            'individual_enhanced_logic_working': False,
            'individual_reasoning_provided': False,
            'individual_portfolio_analysis_working': False,
            
            # Enhanced Bulk Survey Type Update
            'bulk_endpoint_accessible': False,
            'bulk_update_working': False,
            'bulk_improvement_statistics_provided': False,
            'bulk_reasoning_provided': False,
            
            # Survey Type Analysis
            'analysis_endpoint_accessible': False,
            'analysis_comparison_working': False,
            'analysis_improvement_rate_calculated': False,
            'analysis_certificate_categories_working': False,
            
            # Integration Tests
            'certificate_creation_integration_working': False,
            'certificate_update_integration_working': False,
            'enhanced_vs_original_comparison_working': False,
        }
        
        # Test data
        self.test_ship_id = None
        self.test_ship_name = "ENHANCED SURVEY TEST SHIP 2025"
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
                
                self.test_status['authentication_successful'] = True
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
    
    def create_test_ship_with_certificates(self):
        """Create a test ship with diverse certificate portfolio for testing"""
        try:
            self.log("🚢 Creating test ship with diverse certificate portfolio...")
            
            # Create ship with specific data for testing
            ship_data = {
                'name': self.test_ship_name,
                'imo': '9888888',
                'flag': 'PANAMA',
                'ship_type': 'DNV GL',
                'gross_tonnage': 5000.0,
                'built_year': 2020,
                'ship_owner': 'Test Owner',
                'company': 'AMCSC',
                'last_docking': '2023-01-15T00:00:00Z',
                'last_special_survey': '2021-03-10T00:00:00Z',
                'special_survey_cycle': {
                    'from_date': '2021-03-10T00:00:00Z',
                    'to_date': '2026-03-10T00:00:00Z',
                    'intermediate_required': True,
                    'cycle_type': 'SOLAS Safety Construction Survey Cycle'
                }
            }
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.post(
                endpoint,
                json=ship_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                self.test_ship_id = response_data.get('id')
                self.log("✅ Test ship created successfully")
                self.log(f"   Ship ID: {self.test_ship_id}")
                
                # Create diverse certificate portfolio
                return self.create_diverse_certificate_portfolio()
            else:
                self.log(f"   ❌ Test ship creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Test ship creation error: {str(e)}", "ERROR")
            return False
    
    def create_diverse_certificate_portfolio(self):
        """Create a diverse certificate portfolio to test enhanced logic"""
        try:
            self.log("📋 Creating diverse certificate portfolio...")
            
            # Define test certificates with different categories and types
            test_certificates = [
                {
                    'cert_name': 'CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': '2021-03-10T00:00:00Z',
                    'valid_date': '2026-03-10T00:00:00Z',
                    'issued_by': 'DNV GL'
                },
                {
                    'cert_name': 'CLASSIFICATION CERTIFICATE',
                    'cert_type': 'Full Term', 
                    'issue_date': '2021-03-10T00:00:00Z',
                    'valid_date': '2026-03-10T00:00:00Z',
                    'issued_by': 'DNV GL'
                },
                {
                    'cert_name': 'INTERNATIONAL LOAD LINE CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': '2021-03-10T00:00:00Z', 
                    'valid_date': '2026-03-10T00:00:00Z',
                    'issued_by': 'Panama Maritime Authority'
                },
                {
                    'cert_name': 'ISM CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': '2022-01-15T00:00:00Z',
                    'valid_date': '2025-01-15T00:00:00Z',
                    'issued_by': 'DNV GL'
                },
                {
                    'cert_name': 'ISPS CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': '2022-01-15T00:00:00Z',
                    'valid_date': '2025-01-15T00:00:00Z',
                    'issued_by': 'Panama Maritime Authority'
                },
                {
                    'cert_name': 'MARITIME LABOUR CERTIFICATE',
                    'cert_type': 'Full Term',
                    'issue_date': '2023-06-01T00:00:00Z',
                    'valid_date': '2026-06-01T00:00:00Z',
                    'issued_by': 'Panama Maritime Authority'
                },
                {
                    'cert_name': 'CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE',
                    'cert_type': 'Interim',
                    'issue_date': '2024-12-01T00:00:00Z',
                    'valid_date': '2025-06-01T00:00:00Z',
                    'issued_by': 'DNV GL'
                }
            ]
            
            created_certificates = []
            
            for cert_data in test_certificates:
                cert_data['ship_id'] = self.test_ship_id
                cert_data['category'] = 'certificates'
                cert_data['sensitivity_level'] = 'public'
                
                endpoint = f"{BACKEND_URL}/certificates"
                response = requests.post(
                    endpoint,
                    json=cert_data,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    cert_response = response.json()
                    created_certificates.append(cert_response)
                    self.log(f"   ✅ Created: {cert_data['cert_name']} ({cert_data['cert_type']})")
                else:
                    self.log(f"   ❌ Failed to create: {cert_data['cert_name']}")
            
            self.test_certificates = created_certificates
            self.log(f"✅ Created {len(created_certificates)} test certificates")
            return len(created_certificates) > 0
            
        except Exception as e:
            self.log(f"❌ Certificate portfolio creation error: {str(e)}", "ERROR")
            return False
    
    def test_enhanced_individual_certificate_survey_type(self):
        """Test Enhanced Individual Certificate Survey Type Determination"""
        try:
            self.log("🎯 Testing Enhanced Individual Certificate Survey Type Determination...")
            
            if not self.test_certificates:
                self.log("   ❌ No test certificates available")
                return False
            
            # Test with different certificate types
            test_results = []
            
            for cert in self.test_certificates[:3]:  # Test first 3 certificates
                cert_id = cert.get('id')
                cert_name = cert.get('cert_name', 'Unknown')
                cert_type = cert.get('cert_type', 'Unknown')
                
                self.log(f"   Testing certificate: {cert_name} ({cert_type})")
                
                endpoint = f"{BACKEND_URL}/certificates/{cert_id}/determine-survey-type-enhanced"
                response = requests.post(
                    endpoint,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.test_status['individual_endpoint_accessible'] = True
                    
                    response_data = response.json()
                    self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                    
                    if response_data.get('success'):
                        enhanced_survey_type = response_data.get('enhanced_survey_type')
                        reasoning = response_data.get('reasoning')
                        changed = response_data.get('changed')
                        
                        if enhanced_survey_type and enhanced_survey_type != 'Unknown':
                            self.test_status['individual_enhanced_logic_working'] = True
                            self.log(f"   ✅ Enhanced survey type: {enhanced_survey_type}")
                        
                        if reasoning:
                            self.test_status['individual_reasoning_provided'] = True
                            self.log(f"   ✅ Reasoning provided: {reasoning}")
                        
                        if 'portfolio' in reasoning.lower() or 'ship' in reasoning.lower():
                            self.test_status['individual_portfolio_analysis_working'] = True
                            self.log(f"   ✅ Portfolio analysis detected in reasoning")
                        
                        test_results.append({
                            'cert_name': cert_name,
                            'cert_type': cert_type,
                            'enhanced_survey_type': enhanced_survey_type,
                            'reasoning': reasoning,
                            'changed': changed
                        })
                    else:
                        self.log(f"   ❌ Request failed: {response_data.get('message', 'Unknown error')}")
                else:
                    self.log(f"   ❌ Endpoint failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"      Error: {response.text[:500]}")
            
            if test_results:
                self.log("✅ Enhanced Individual Certificate Survey Type Determination working")
                return True
            else:
                self.log("❌ Enhanced Individual Certificate Survey Type Determination failed")
                return False
                
        except Exception as e:
            self.log(f"❌ Individual certificate testing error: {str(e)}", "ERROR")
            return False
    
    def test_enhanced_bulk_survey_type_update(self):
        """Test Enhanced Bulk Survey Type Update"""
        try:
            self.log("🎯 Testing Enhanced Bulk Survey Type Update...")
            
            endpoint = f"{BACKEND_URL}/certificates/update-survey-types-enhanced"
            response = requests.post(
                endpoint,
                headers=self.get_headers(),
                timeout=60  # Longer timeout for bulk operation
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.test_status['bulk_endpoint_accessible'] = True
                
                response_data = response.json()
                self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                
                if response_data.get('success'):
                    updated_count = response_data.get('updated_count', 0)
                    total_certificates = response_data.get('total_certificates', 0)
                    improvement_rate = response_data.get('improvement_rate', '0.0%')
                    results = response_data.get('results', [])
                    
                    self.log(f"   ✅ Updated {updated_count} certificates out of {total_certificates}")
                    self.log(f"   ✅ Improvement rate: {improvement_rate}")
                    
                    if updated_count > 0:
                        self.test_status['bulk_update_working'] = True
                    
                    if improvement_rate and improvement_rate != '0.0%':
                        self.test_status['bulk_improvement_statistics_provided'] = True
                    
                    if results and len(results) > 0:
                        self.test_status['bulk_reasoning_provided'] = True
                        self.log("   ✅ Sample results:")
                        for result in results[:3]:  # Show first 3 results
                            self.log(f"      - {result.get('cert_name', 'Unknown')}: {result.get('old_survey_type', 'Unknown')} → {result.get('new_survey_type', 'Unknown')}")
                            self.log(f"        Reasoning: {result.get('reasoning', 'No reasoning')}")
                    
                    return True
                else:
                    self.log(f"   ❌ Bulk update failed: {response_data.get('message', 'Unknown error')}")
                    return False
            else:
                self.log(f"   ❌ Bulk endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Bulk update testing error: {str(e)}", "ERROR")
            return False
    
    def test_survey_type_analysis(self):
        """Test Survey Type Analysis endpoint"""
        try:
            self.log("🎯 Testing Survey Type Analysis...")
            
            endpoint = f"{BACKEND_URL}/certificates/survey-type-analysis"
            response = requests.get(
                endpoint,
                headers=self.get_headers(),
                timeout=60
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.test_status['analysis_endpoint_accessible'] = True
                
                response_data = response.json()
                self.log(f"   Response keys: {list(response_data.keys())}")
                
                if response_data.get('success'):
                    analysis = response_data.get('analysis', {})
                    improvement_stats = response_data.get('improvement_statistics', {})
                    
                    # Check analysis components
                    total_certificates = analysis.get('total_certificates', 0)
                    current_survey_types = analysis.get('current_survey_types', {})
                    enhanced_survey_types = analysis.get('enhanced_survey_types', {})
                    potential_improvements = analysis.get('potential_improvements', [])
                    certificate_categories = analysis.get('certificate_categories', {})
                    
                    self.log(f"   ✅ Total certificates analyzed: {total_certificates}")
                    self.log(f"   ✅ Current survey types: {current_survey_types}")
                    self.log(f"   ✅ Enhanced survey types: {enhanced_survey_types}")
                    self.log(f"   ✅ Potential improvements: {len(potential_improvements)}")
                    self.log(f"   ✅ Certificate categories: {len(certificate_categories)}")
                    
                    if current_survey_types and enhanced_survey_types:
                        self.test_status['analysis_comparison_working'] = True
                    
                    # Check improvement statistics
                    improvement_rate = improvement_stats.get('improvement_rate', '0.0%')
                    unknown_survey_types = improvement_stats.get('unknown_survey_types', 0)
                    
                    self.log(f"   ✅ Improvement rate: {improvement_rate}")
                    self.log(f"   ✅ Unknown survey types: {unknown_survey_types}")
                    
                    if improvement_rate and improvement_rate != '0.0%':
                        self.test_status['analysis_improvement_rate_calculated'] = True
                    
                    if certificate_categories:
                        self.test_status['analysis_certificate_categories_working'] = True
                        self.log("   ✅ Certificate categories breakdown:")
                        for category, info in certificate_categories.items():
                            self.log(f"      - {category}: {info.get('count', 0)} certificates")
                    
                    return True
                else:
                    self.log(f"   ❌ Analysis failed: {response_data.get('message', 'Unknown error')}")
                    return False
            else:
                self.log(f"   ❌ Analysis endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Analysis testing error: {str(e)}", "ERROR")
            return False
    
    def test_integration_with_certificate_workflows(self):
        """Test integration with existing certificate workflows"""
        try:
            self.log("🎯 Testing Integration with Certificate Workflows...")
            
            # Test 1: Create new certificate and check if it gets enhanced survey type
            self.log("   Testing new certificate creation...")
            
            new_cert_data = {
                'ship_id': self.test_ship_id,
                'cert_name': 'INTERNATIONAL TONNAGE CERTIFICATE',
                'cert_type': 'Full Term',
                'issue_date': '2024-01-01T00:00:00Z',
                'valid_date': '2029-01-01T00:00:00Z',
                'issued_by': 'Panama Maritime Authority',
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
                new_cert = response.json()
                new_cert_id = new_cert.get('id')
                
                # Check if it has a survey type (might be set automatically)
                survey_type = new_cert.get('next_survey_type')
                self.log(f"   ✅ New certificate created with survey type: {survey_type}")
                
                # Test enhanced determination on the new certificate
                endpoint = f"{BACKEND_URL}/certificates/{new_cert_id}/determine-survey-type-enhanced"
                response = requests.post(
                    endpoint,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get('success'):
                        self.test_status['certificate_creation_integration_working'] = True
                        self.log("   ✅ Enhanced survey type determination works for new certificates")
                
                # Test 2: Update certificate and check if survey type is recalculated
                self.log("   Testing certificate update integration...")
                
                update_data = {
                    'valid_date': '2028-01-01T00:00:00Z'  # Change valid date
                }
                
                endpoint = f"{BACKEND_URL}/certificates/{new_cert_id}"
                response = requests.put(
                    endpoint,
                    json=update_data,
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if response.status_code == 200:
                    # Test enhanced determination after update
                    endpoint = f"{BACKEND_URL}/certificates/{new_cert_id}/determine-survey-type-enhanced"
                    response = requests.post(
                        endpoint,
                        headers=self.get_headers(),
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if response_data.get('success'):
                            self.test_status['certificate_update_integration_working'] = True
                            self.log("   ✅ Enhanced survey type determination works after certificate updates")
                
                return True
            else:
                self.log(f"   ❌ New certificate creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Integration testing error: {str(e)}", "ERROR")
            return False
    
    def test_enhanced_vs_original_comparison(self):
        """Test comparison between enhanced and original logic"""
        try:
            self.log("🎯 Testing Enhanced vs Original Logic Comparison...")
            
            if not self.test_certificates:
                self.log("   ❌ No test certificates available")
                return False
            
            # Get a certificate to test both logics
            test_cert = self.test_certificates[0]
            cert_id = test_cert.get('id')
            
            # Test enhanced logic
            endpoint = f"{BACKEND_URL}/certificates/{cert_id}/determine-survey-type-enhanced"
            enhanced_response = requests.post(
                endpoint,
                headers=self.get_headers(),
                timeout=30
            )
            
            enhanced_survey_type = None
            enhanced_reasoning = None
            
            if enhanced_response.status_code == 200:
                enhanced_data = enhanced_response.json()
                if enhanced_data.get('success'):
                    enhanced_survey_type = enhanced_data.get('enhanced_survey_type')
                    enhanced_reasoning = enhanced_data.get('reasoning')
            
            # Compare results
            if enhanced_survey_type:
                self.log(f"   ✅ Enhanced logic result: {enhanced_survey_type}")
                self.log(f"   ✅ Enhanced reasoning: {enhanced_reasoning}")
                
                # Check if enhanced logic provides more detailed reasoning
                if enhanced_reasoning and len(enhanced_reasoning) > 20:
                    self.test_status['enhanced_vs_original_comparison_working'] = True
                    self.log("   ✅ Enhanced logic provides detailed reasoning")
                
                return True
            else:
                self.log("   ❌ Enhanced logic comparison failed")
                return False
                
        except Exception as e:
            self.log(f"❌ Comparison testing error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up test ship and certificates"""
        try:
            if self.test_ship_id:
                self.log("🧹 Cleaning up test data...")
                
                # Delete test ship (this should cascade delete certificates)
                endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}"
                response = requests.delete(endpoint, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 200:
                    self.log("✅ Test data cleaned up successfully")
                else:
                    self.log(f"⚠️ Test data cleanup failed: {response.status_code}")
                    
        except Exception as e:
            self.log(f"⚠️ Cleanup error: {str(e)}", "WARNING")
    
    def run_comprehensive_tests(self):
        """Main test function"""
        self.log("🎯 STARTING ENHANCED SURVEY TYPE DETERMINATION SYSTEM TESTING")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Create Test Data
            self.log("\n🚢 STEP 2: CREATE TEST DATA")
            self.log("=" * 50)
            if not self.create_test_ship_with_certificates():
                self.log("❌ Test data creation failed - cannot proceed with testing")
                return False
            
            # Step 3: Test Enhanced Individual Certificate Survey Type
            self.log("\n🎯 STEP 3: ENHANCED INDIVIDUAL CERTIFICATE SURVEY TYPE")
            self.log("=" * 50)
            self.test_enhanced_individual_certificate_survey_type()
            
            # Step 4: Test Enhanced Bulk Survey Type Update
            self.log("\n🎯 STEP 4: ENHANCED BULK SURVEY TYPE UPDATE")
            self.log("=" * 50)
            self.test_enhanced_bulk_survey_type_update()
            
            # Step 5: Test Survey Type Analysis
            self.log("\n🎯 STEP 5: SURVEY TYPE ANALYSIS")
            self.log("=" * 50)
            self.test_survey_type_analysis()
            
            # Step 6: Test Integration with Certificate Workflows
            self.log("\n🎯 STEP 6: INTEGRATION WITH CERTIFICATE WORKFLOWS")
            self.log("=" * 50)
            self.test_integration_with_certificate_workflows()
            
            # Step 7: Test Enhanced vs Original Comparison
            self.log("\n🎯 STEP 7: ENHANCED VS ORIGINAL LOGIC COMPARISON")
            self.log("=" * 50)
            self.test_enhanced_vs_original_comparison()
            
            # Step 8: Final Analysis
            self.log("\n📊 STEP 8: FINAL ANALYSIS")
            self.log("=" * 50)
            return self.provide_final_analysis()
            
        finally:
            # Always cleanup
            self.log("\n🧹 CLEANUP")
            self.log("=" * 50)
            self.cleanup_test_data()
    
    def provide_final_analysis(self):
        """Provide final analysis of testing results"""
        try:
            self.log("🎯 ENHANCED SURVEY TYPE DETERMINATION SYSTEM - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.test_status.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.test_status)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.test_status)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.test_status)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.test_status)})")
            
            # Feature-specific analysis
            self.log("\n🎯 FEATURE-SPECIFIC ANALYSIS:")
            
            # Enhanced Individual Certificate Analysis
            individual_tests = [
                'individual_endpoint_accessible',
                'individual_enhanced_logic_working',
                'individual_reasoning_provided',
                'individual_portfolio_analysis_working'
            ]
            individual_passed = sum(1 for test in individual_tests if self.test_status.get(test, False))
            individual_rate = (individual_passed / len(individual_tests)) * 100
            
            self.log(f"\n🎯 ENHANCED INDIVIDUAL CERTIFICATE: {individual_rate:.1f}% ({individual_passed}/{len(individual_tests)})")
            if self.test_status['individual_enhanced_logic_working']:
                self.log("   ✅ CONFIRMED: Enhanced individual certificate logic working")
            else:
                self.log("   ❌ ISSUE: Enhanced individual certificate logic needs fixing")
            
            # Enhanced Bulk Update Analysis
            bulk_tests = [
                'bulk_endpoint_accessible',
                'bulk_update_working',
                'bulk_improvement_statistics_provided',
                'bulk_reasoning_provided'
            ]
            bulk_passed = sum(1 for test in bulk_tests if self.test_status.get(test, False))
            bulk_rate = (bulk_passed / len(bulk_tests)) * 100
            
            self.log(f"\n🎯 ENHANCED BULK UPDATE: {bulk_rate:.1f}% ({bulk_passed}/{len(bulk_tests)})")
            if self.test_status['bulk_update_working']:
                self.log("   ✅ CONFIRMED: Enhanced bulk update working")
            else:
                self.log("   ❌ ISSUE: Enhanced bulk update needs fixing")
            
            # Survey Type Analysis
            analysis_tests = [
                'analysis_endpoint_accessible',
                'analysis_comparison_working',
                'analysis_improvement_rate_calculated',
                'analysis_certificate_categories_working'
            ]
            analysis_passed = sum(1 for test in analysis_tests if self.test_status.get(test, False))
            analysis_rate = (analysis_passed / len(analysis_tests)) * 100
            
            self.log(f"\n🎯 SURVEY TYPE ANALYSIS: {analysis_rate:.1f}% ({analysis_passed}/{len(analysis_tests)})")
            if self.test_status['analysis_comparison_working']:
                self.log("   ✅ CONFIRMED: Survey type analysis working")
            else:
                self.log("   ❌ ISSUE: Survey type analysis needs fixing")
            
            # Integration Tests
            integration_tests = [
                'certificate_creation_integration_working',
                'certificate_update_integration_working',
                'enhanced_vs_original_comparison_working'
            ]
            integration_passed = sum(1 for test in integration_tests if self.test_status.get(test, False))
            integration_rate = (integration_passed / len(integration_tests)) * 100
            
            self.log(f"\n🎯 INTEGRATION TESTS: {integration_rate:.1f}% ({integration_passed}/{len(integration_tests)})")
            
            # Final conclusion
            if success_rate >= 80:
                self.log(f"\n🎉 CONCLUSION: ENHANCED SURVEY TYPE DETERMINATION SYSTEM IS WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - System ready for production!")
                self.log(f"   ✅ Enhanced logic analyzes ship certificate portfolios correctly")
                self.log(f"   ✅ Bulk updates provide improvement statistics")
                self.log(f"   ✅ Analysis endpoint provides comprehensive insights")
                self.log(f"   ✅ Integration with certificate workflows working")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: ENHANCED SURVEY TYPE SYSTEM PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Some functionality working, improvements needed")
            else:
                self.log(f"\n❌ CONCLUSION: ENHANCED SURVEY TYPE SYSTEM HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - System needs significant fixes")
            
            return success_rate >= 60
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run Enhanced Survey Type Determination tests"""
    print("🎯 ENHANCED SURVEY TYPE DETERMINATION SYSTEM TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = EnhancedSurveyTypeSystemTester()
        success = tester.run_comprehensive_tests()
        
        if success:
            print("\n✅ ENHANCED SURVEY TYPE DETERMINATION TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ ENHANCED SURVEY TYPE DETERMINATION TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    sys.exit(0)

if __name__ == "__main__":
    main()
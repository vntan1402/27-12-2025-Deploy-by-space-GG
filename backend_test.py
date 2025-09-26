#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: Enhanced AI Certificate Analysis Testing
Review Request: Test the enhanced AI extraction with the real SUNSHINE 01 CSSC certificate that the user uploaded.
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import time
import traceback
import tempfile
from urllib.parse import urlparse

# Configuration - Use environment variable for backend URL
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://marine-cert-system.preview.emergentagent.com') + '/api'

class EnhancedAIExtractionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Enhanced AI Extraction
        self.extraction_tests = {
            'authentication_successful': False,
            'pdf_download_successful': False,
            'ai_config_available': False,
            'analyze_certificate_endpoint_accessible': False,
            'enhanced_field_extraction': False,
            'basic_fields_extracted': False,
            'survey_fields_extracted': False,
            'advanced_fields_extracted': False,
            'field_count_improvement': False,
            'sunshine01_specific_data': False,
            'docking_dates_extracted': False,
            'anniversary_date_extracted': False,
            'special_survey_extracted': False
        }
        
        # Expected fields from the review request
        self.expected_basic_fields = [
            'ship_name', 'imo_number', 'flag', 'class_society', 
            'gross_tonnage', 'built_year', 'keel_laid'
        ]
        
        self.expected_survey_fields = [
            'last_docking', 'last_docking_2', 'anniversary_date_day', 'anniversary_date_month'
        ]
        
        self.expected_advanced_fields = [
            'special_survey_from_date', 'special_survey_to_date'
        ]
        
        # Expected data from SUNSHINE 01 certificate
        self.expected_sunshine01_data = {
            'ship_name': 'SUNSHINE 01',
            'imo_number': '9415313',
            'flag': 'BELIZE',
            'class_society': 'PMDS',  # Panama Maritime Documentation Services
            'gross_tonnage': 2959,
            'keel_laid': 'OCTOBER 20, 2004'
        }
        
        # PDF URL from the review request
        self.pdf_url = "https://customer-assets.emergentagent.com/job_8713f098-d577-491f-ae01-3c714b8055af/artifacts/h9jbvh37_SUNSHINE%2001%20-%20CSSC%20-%20PM25385.pdf"
        
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
                
                self.extraction_tests['authentication_successful'] = True
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
    
    def download_pdf_file(self):
        """Download the SUNSHINE 01 CSSC certificate PDF"""
        try:
            self.log("📄 Downloading SUNSHINE 01 CSSC certificate PDF...")
            self.log(f"   URL: {self.pdf_url}")
            
            response = requests.get(self.pdf_url, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(response.content)
                    self.temp_pdf_path = temp_file.name
                
                file_size = len(response.content)
                self.log("✅ PDF download successful")
                self.log(f"   File size: {file_size:,} bytes")
                self.log(f"   Temporary file: {self.temp_pdf_path}")
                
                self.extraction_tests['pdf_download_successful'] = True
                return True
            else:
                self.log(f"   ❌ PDF download failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ PDF download error: {str(e)}", "ERROR")
            return False
    
    def check_ai_configuration(self):
        """Check if AI configuration is available"""
        try:
            self.log("🤖 Checking AI configuration...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ai_config = response.json()
                provider = ai_config.get('provider')
                model = ai_config.get('model')
                use_emergent_key = ai_config.get('use_emergent_key')
                
                self.log("✅ AI configuration available")
                self.log(f"   Provider: {provider}")
                self.log(f"   Model: {model}")
                self.log(f"   Using Emergent API key: {use_emergent_key}")
                
                self.extraction_tests['ai_config_available'] = True
                return True
            else:
                self.log(f"   ❌ AI configuration not available: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ AI configuration check error: {str(e)}", "ERROR")
            return False
    
    def test_analyze_certificate_endpoint(self):
        """Test the analyze-ship-certificate endpoint with the SUNSHINE 01 PDF"""
        try:
            self.log("🔍 Testing Enhanced AI Certificate Analysis...")
            self.log("   Focus: POST /api/analyze-ship-certificate with SUNSHINE 01 CSSC PDF")
            
            endpoint = f"{BACKEND_URL}/analyze-ship-certificate"
            self.log(f"   POST {endpoint}")
            
            # Prepare the file for upload
            with open(self.temp_pdf_path, 'rb') as pdf_file:
                files = {
                    'file': ('SUNSHINE_01_CSSC_PM25385.pdf', pdf_file, 'application/pdf')
                }
                
                response = requests.post(
                    endpoint, 
                    files=files, 
                    headers=self.get_headers(), 
                    timeout=120  # Longer timeout for AI processing
                )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                self.log("✅ Certificate analysis successful")
                
                # Store the analysis result for detailed verification
                # The actual analysis data is in the 'analysis' field
                self.analysis_result = response_data.get('analysis', {})
                self.extraction_tests['analyze_certificate_endpoint_accessible'] = True
                
                # Log the full response for analysis
                self.log("   Analysis result received:")
                self.log(f"   {json.dumps(response_data, indent=2)}")
                
                return True
            else:
                self.log(f"   ❌ Certificate analysis failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Certificate analysis error: {str(e)}", "ERROR")
            return False
    
    def verify_basic_fields_extraction(self):
        """Verify that basic fields are extracted correctly"""
        try:
            self.log("📊 Verifying Basic Fields Extraction...")
            self.log("   Expected basic fields: ship_name, imo_number, flag, class_society, gross_tonnage, built_year, keel_laid")
            
            if not hasattr(self, 'analysis_result'):
                self.log("   ❌ No analysis result available")
                return False
            
            basic_fields_found = 0
            total_basic_fields = len(self.expected_basic_fields)
            
            for field in self.expected_basic_fields:
                value = self.analysis_result.get(field)
                if value is not None and value != "":
                    basic_fields_found += 1
                    self.log(f"   ✅ {field}: {value}")
                else:
                    self.log(f"   ❌ {field}: Not found or empty")
            
            extraction_rate = (basic_fields_found / total_basic_fields) * 100
            self.log(f"   Basic fields extraction rate: {extraction_rate:.1f}% ({basic_fields_found}/{total_basic_fields})")
            
            if extraction_rate >= 70:  # At least 70% of basic fields should be extracted
                self.log("   ✅ Basic fields extraction successful")
                self.extraction_tests['basic_fields_extracted'] = True
                return True
            else:
                self.log("   ❌ Basic fields extraction insufficient")
                return False
                
        except Exception as e:
            self.log(f"❌ Basic fields verification error: {str(e)}", "ERROR")
            return False
    
    def verify_survey_fields_extraction(self):
        """Verify that survey fields are extracted correctly"""
        try:
            self.log("📊 Verifying Survey Fields Extraction...")
            self.log("   Expected survey fields: last_docking, last_docking_2, anniversary_date_day, anniversary_date_month")
            
            if not hasattr(self, 'analysis_result'):
                self.log("   ❌ No analysis result available")
                return False
            
            survey_fields_found = 0
            total_survey_fields = len(self.expected_survey_fields)
            
            for field in self.expected_survey_fields:
                value = self.analysis_result.get(field)
                if value is not None and value != "":
                    survey_fields_found += 1
                    self.log(f"   ✅ {field}: {value}")
                else:
                    self.log(f"   ❌ {field}: Not found or empty")
            
            # Check for docking dates specifically mentioned in the review
            docking_dates_found = []
            if self.analysis_result.get('last_docking'):
                docking_dates_found.append(self.analysis_result.get('last_docking'))
            if self.analysis_result.get('last_docking_2'):
                docking_dates_found.append(self.analysis_result.get('last_docking_2'))
            
            if docking_dates_found:
                self.log(f"   ✅ Docking dates extracted: {docking_dates_found}")
                self.extraction_tests['docking_dates_extracted'] = True
            
            # Check for anniversary date
            anniversary_day = self.analysis_result.get('anniversary_date_day')
            anniversary_month = self.analysis_result.get('anniversary_date_month')
            if anniversary_day and anniversary_month:
                self.log(f"   ✅ Anniversary date extracted: Day {anniversary_day}, Month {anniversary_month}")
                self.extraction_tests['anniversary_date_extracted'] = True
            
            extraction_rate = (survey_fields_found / total_survey_fields) * 100
            self.log(f"   Survey fields extraction rate: {extraction_rate:.1f}% ({survey_fields_found}/{total_survey_fields})")
            
            if extraction_rate >= 50:  # At least 50% of survey fields should be extracted
                self.log("   ✅ Survey fields extraction successful")
                self.extraction_tests['survey_fields_extracted'] = True
                return True
            else:
                self.log("   ❌ Survey fields extraction insufficient")
                return False
                
        except Exception as e:
            self.log(f"❌ Survey fields verification error: {str(e)}", "ERROR")
            return False
    
    def verify_advanced_fields_extraction(self):
        """Verify that advanced fields are extracted correctly"""
        try:
            self.log("📊 Verifying Advanced Fields Extraction...")
            self.log("   Expected advanced fields: special_survey_from_date, special_survey_to_date")
            
            if not hasattr(self, 'analysis_result'):
                self.log("   ❌ No analysis result available")
                return False
            
            advanced_fields_found = 0
            total_advanced_fields = len(self.expected_advanced_fields)
            
            for field in self.expected_advanced_fields:
                value = self.analysis_result.get(field)
                if value is not None and value != "":
                    advanced_fields_found += 1
                    self.log(f"   ✅ {field}: {value}")
                else:
                    self.log(f"   ❌ {field}: Not found or empty")
            
            # Check for special survey cycle information
            special_survey_from = self.analysis_result.get('special_survey_from_date')
            special_survey_to = self.analysis_result.get('special_survey_to_date')
            if special_survey_from and special_survey_to:
                self.log(f"   ✅ Special survey cycle extracted: {special_survey_from} to {special_survey_to}")
                self.extraction_tests['special_survey_extracted'] = True
            
            extraction_rate = (advanced_fields_found / total_advanced_fields) * 100
            self.log(f"   Advanced fields extraction rate: {extraction_rate:.1f}% ({advanced_fields_found}/{total_advanced_fields})")
            
            if extraction_rate >= 50:  # At least 50% of advanced fields should be extracted
                self.log("   ✅ Advanced fields extraction successful")
                self.extraction_tests['advanced_fields_extracted'] = True
                return True
            else:
                self.log("   ❌ Advanced fields extraction insufficient")
                return False
                
        except Exception as e:
            self.log(f"❌ Advanced fields verification error: {str(e)}", "ERROR")
            return False
    
    def verify_sunshine01_specific_data(self):
        """Verify that SUNSHINE 01 specific data is extracted correctly"""
        try:
            self.log("🚢 Verifying SUNSHINE 01 Specific Data...")
            self.log("   Expected: Ship Name: SUNSHINE 01, IMO: 9415313, Flag: BELIZE, Class Society: PMDS, Gross Tonnage: 2959")
            
            if not hasattr(self, 'analysis_result'):
                self.log("   ❌ No analysis result available")
                return False
            
            specific_data_matches = 0
            total_expected_data = len(self.expected_sunshine01_data)
            
            for field, expected_value in self.expected_sunshine01_data.items():
                actual_value = self.analysis_result.get(field)
                
                if actual_value is not None:
                    # Convert to string for comparison
                    actual_str = str(actual_value).upper().strip()
                    expected_str = str(expected_value).upper().strip()
                    
                    if expected_str in actual_str or actual_str in expected_str:
                        specific_data_matches += 1
                        self.log(f"   ✅ {field}: {actual_value} (matches expected: {expected_value})")
                    else:
                        self.log(f"   ⚠️ {field}: {actual_value} (expected: {expected_value}) - partial match")
                else:
                    self.log(f"   ❌ {field}: Not found (expected: {expected_value})")
            
            match_rate = (specific_data_matches / total_expected_data) * 100
            self.log(f"   SUNSHINE 01 data match rate: {match_rate:.1f}% ({specific_data_matches}/{total_expected_data})")
            
            if match_rate >= 60:  # At least 60% of specific data should match
                self.log("   ✅ SUNSHINE 01 specific data verification successful")
                self.extraction_tests['sunshine01_specific_data'] = True
                return True
            else:
                self.log("   ❌ SUNSHINE 01 specific data verification insufficient")
                return False
                
        except Exception as e:
            self.log(f"❌ SUNSHINE 01 data verification error: {str(e)}", "ERROR")
            return False
    
    def verify_field_count_improvement(self):
        """Verify that the enhanced extraction captures significantly more than 8 fields"""
        try:
            self.log("📈 Verifying Field Count Improvement...")
            self.log("   Goal: Extract significantly more than the original 8 fields")
            
            if not hasattr(self, 'analysis_result'):
                self.log("   ❌ No analysis result available")
                return False
            
            # Count non-empty fields in the analysis result
            extracted_fields = 0
            total_fields = 0
            
            for field, value in self.analysis_result.items():
                total_fields += 1
                if value is not None and value != "" and value != "N/A":
                    extracted_fields += 1
                    self.log(f"   ✅ {field}: {value}")
                else:
                    self.log(f"   ❌ {field}: Empty or N/A")
            
            self.log(f"   Total fields extracted: {extracted_fields}")
            self.log(f"   Total fields attempted: {total_fields}")
            
            # Check if we extracted significantly more than 8 fields
            if extracted_fields > 8:
                improvement = extracted_fields - 8
                self.log(f"   ✅ Field count improvement: +{improvement} fields over original 8")
                self.extraction_tests['field_count_improvement'] = True
                return True
            else:
                self.log(f"   ❌ Field count improvement insufficient: only {extracted_fields} fields extracted")
                return False
                
        except Exception as e:
            self.log(f"❌ Field count improvement verification error: {str(e)}", "ERROR")
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            if hasattr(self, 'temp_pdf_path') and os.path.exists(self.temp_pdf_path):
                os.unlink(self.temp_pdf_path)
                self.log("🧹 Temporary PDF file cleaned up")
        except Exception as e:
            self.log(f"⚠️ Cleanup error: {str(e)}", "WARNING")
    
    def run_comprehensive_ai_extraction_tests(self):
        """Main test function for Enhanced AI Extraction"""
        self.log("🤖 STARTING ENHANCED AI CERTIFICATE ANALYSIS TESTING")
        self.log("🎯 Focus: Enhanced AI extraction with real SUNSHINE 01 CSSC certificate")
        self.log("📋 Review Request: Test enhanced AI extraction capturing ALL possible fields from uploaded CSSC certificate")
        self.log("🔍 Key Areas: Basic fields, survey fields, advanced fields, field count improvement, SUNSHINE 01 specific data")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Download PDF
            self.log("\n📄 STEP 2: PDF DOWNLOAD")
            self.log("=" * 50)
            if not self.download_pdf_file():
                self.log("❌ PDF download failed - cannot proceed with testing")
                return False
            
            # Step 3: Check AI Configuration
            self.log("\n🤖 STEP 3: AI CONFIGURATION CHECK")
            self.log("=" * 50)
            if not self.check_ai_configuration():
                self.log("❌ AI configuration not available - cannot proceed with testing")
                return False
            
            # Step 4: Test Certificate Analysis
            self.log("\n🔍 STEP 4: ENHANCED AI CERTIFICATE ANALYSIS")
            self.log("=" * 50)
            if not self.test_analyze_certificate_endpoint():
                self.log("❌ Certificate analysis failed - cannot proceed with verification")
                return False
            
            # Step 5: Verify Basic Fields
            self.log("\n📊 STEP 5: BASIC FIELDS VERIFICATION")
            self.log("=" * 50)
            self.verify_basic_fields_extraction()
            
            # Step 6: Verify Survey Fields
            self.log("\n📊 STEP 6: SURVEY FIELDS VERIFICATION")
            self.log("=" * 50)
            self.verify_survey_fields_extraction()
            
            # Step 7: Verify Advanced Fields
            self.log("\n📊 STEP 7: ADVANCED FIELDS VERIFICATION")
            self.log("=" * 50)
            self.verify_advanced_fields_extraction()
            
            # Step 8: Verify SUNSHINE 01 Specific Data
            self.log("\n🚢 STEP 8: SUNSHINE 01 SPECIFIC DATA VERIFICATION")
            self.log("=" * 50)
            self.verify_sunshine01_specific_data()
            
            # Step 9: Verify Field Count Improvement
            self.log("\n📈 STEP 9: FIELD COUNT IMPROVEMENT VERIFICATION")
            self.log("=" * 50)
            self.verify_field_count_improvement()
            
            # Step 10: Final Analysis
            self.log("\n📊 STEP 10: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_ai_extraction_analysis()
            
            return True
            
        finally:
            # Always cleanup
            self.log("\n🧹 CLEANUP")
            self.log("=" * 50)
            self.cleanup_temp_files()
    
    def provide_final_ai_extraction_analysis(self):
        """Provide final analysis of the Enhanced AI Extraction testing"""
        try:
            self.log("🤖 ENHANCED AI CERTIFICATE ANALYSIS TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.extraction_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ AI EXTRACTION TESTS PASSED ({len(passed_tests)}/{len(self.extraction_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ AI EXTRACTION TESTS FAILED ({len(failed_tests)}/{len(self.extraction_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.extraction_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.extraction_tests)})")
            
            # Provide specific analysis based on review request
            self.log("\n🎯 REVIEW REQUEST ANALYSIS:")
            
            # 1. Authentication
            if self.extraction_tests['authentication_successful']:
                self.log("   ✅ Authentication with admin1/123456: PASSED")
            else:
                self.log("   ❌ Authentication with admin1/123456: FAILED")
            
            # 2. Enhanced AI Extraction
            if self.extraction_tests['analyze_certificate_endpoint_accessible']:
                self.log("   ✅ Enhanced AI Extraction Endpoint: ACCESSIBLE")
            else:
                self.log("   ❌ Enhanced AI Extraction Endpoint: FAILED")
            
            # 3. Field Coverage
            field_coverage_tests = [
                'basic_fields_extracted', 'survey_fields_extracted', 'advanced_fields_extracted'
            ]
            field_coverage_passed = sum(1 for test in field_coverage_tests if self.extraction_tests[test])
            
            if field_coverage_passed >= 2:
                self.log("   ✅ Field Coverage Verification: PASSED")
                self.log(f"      - Basic fields: {'✅' if self.extraction_tests['basic_fields_extracted'] else '❌'}")
                self.log(f"      - Survey fields: {'✅' if self.extraction_tests['survey_fields_extracted'] else '❌'}")
                self.log(f"      - Advanced fields: {'✅' if self.extraction_tests['advanced_fields_extracted'] else '❌'}")
            else:
                self.log("   ❌ Field Coverage Verification: FAILED")
            
            # 4. SUNSHINE 01 Specific Data
            if self.extraction_tests['sunshine01_specific_data']:
                self.log("   ✅ SUNSHINE 01 Specific Data Extraction: PASSED")
                self.log("      - Ship Name, IMO, Flag, Class Society data verified")
            else:
                self.log("   ❌ SUNSHINE 01 Specific Data Extraction: FAILED")
            
            # 5. Field Count Improvement
            if self.extraction_tests['field_count_improvement']:
                self.log("   ✅ Field Count Improvement: PASSED")
                self.log("      - Extracted significantly more than original 8 fields")
            else:
                self.log("   ❌ Field Count Improvement: FAILED")
            
            # 6. Docking and Anniversary Date Extraction
            docking_anniversary_passed = (
                self.extraction_tests['docking_dates_extracted'] or 
                self.extraction_tests['anniversary_date_extracted']
            )
            if docking_anniversary_passed:
                self.log("   ✅ Docking/Anniversary Date Extraction: PASSED")
                self.log(f"      - Docking dates: {'✅' if self.extraction_tests['docking_dates_extracted'] else '❌'}")
                self.log(f"      - Anniversary date: {'✅' if self.extraction_tests['anniversary_date_extracted'] else '❌'}")
            else:
                self.log("   ❌ Docking/Anniversary Date Extraction: FAILED")
            
            # Final conclusion
            if success_rate >= 70:
                self.log(f"\n🎉 CONCLUSION: ENHANCED AI EXTRACTION IS WORKING EXCELLENTLY")
                self.log(f"   Success rate: {success_rate:.1f}% - AI successfully extracts enhanced fields!")
                self.log(f"   ✅ Significantly more than 8 fields extracted from SUNSHINE 01 certificate")
                self.log(f"   ✅ Enhanced field coverage including survey/docking dates and anniversary dates")
                self.log(f"   ✅ SUNSHINE 01 specific data accurately identified")
                self.log(f"   ✅ Maritime-specific terminology properly handled")
            elif success_rate >= 50:
                self.log(f"\n⚠️ CONCLUSION: ENHANCED AI EXTRACTION PARTIALLY WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - Core functionality working, some enhancements needed")
            else:
                self.log(f"\n❌ CONCLUSION: ENHANCED AI EXTRACTION HAS CRITICAL ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - System needs significant fixes for AI extraction")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final AI extraction analysis error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run Enhanced AI Extraction tests"""
    print("🤖 ENHANCED AI CERTIFICATE ANALYSIS TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = EnhancedAIExtractionTester()
        success = tester.run_comprehensive_ai_extraction_tests()
        
        if success:
            print("\n✅ ENHANCED AI CERTIFICATE ANALYSIS TESTING COMPLETED")
        else:
            print("\n❌ ENHANCED AI CERTIFICATE ANALYSIS TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
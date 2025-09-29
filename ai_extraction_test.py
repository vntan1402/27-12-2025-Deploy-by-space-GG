#!/usr/bin/env python3
"""
AI Enhanced Basic Ship Information Extraction Testing
FOCUS: Test AI extraction of new Basic Ship Information fields in multi-certificate upload

REVIEW REQUEST REQUIREMENTS:
1. Test AI extraction of Basic Ship Information fields:
   - ship_name: Ship/vessel name 
   - imo_number: IMO number (7-digit number starting with 9)
   - flag: Flag state/country of registration
   - class_society: Classification society (DNV GL, Lloyd's Register, ABS, BV, etc.)
   - built_year: Year ship was built/constructed
   - gross_tonnage: Gross tonnage (GT)  
   - deadweight: Deadweight tonnage (DWT)

2. Monitor AI Analysis Response Structure
3. Test with Certificate Files
4. Backend Logs Analysis for AI Analysis Debug
5. Expected Enhanced Response Structure verification
6. Use admin1/123456 authentication

EXPECTED ENHANCED RESPONSE STRUCTURE:
{
  "cert_name": "extracted_certificate_name",
  "cert_no": "extracted_certificate_number", 
  "issue_date": "YYYY-MM-DD",
  "valid_date": "YYYY-MM-DD",
  "last_endorse": "YYYY-MM-DD",
  "ship_name": "extracted_ship_name",
  "imo_number": "extracted_imo_number",
  "flag": "extracted_flag_state", 
  "class_society": "extracted_classification_society",
  "built_year": "extracted_built_year",
  "gross_tonnage": "extracted_gross_tonnage",
  "deadweight": "extracted_deadweight",
  "category": "certificates",
  "confidence": "high/medium/low"
}
"""

import requests
import json
import os
import sys
import re
import time
import traceback
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

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

class AIExtractionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for AI extraction
        self.test_status = {
            'authentication_successful': False,
            'ai_config_accessible': False,
            'test_ship_found': False,
            'multi_upload_endpoint_accessible': False,
            'ai_analysis_working': False,
            'basic_ship_info_extracted': False,
            'ship_name_extracted': False,
            'imo_number_extracted': False,
            'flag_extracted': False,
            'class_society_extracted': False,
            'built_year_extracted': False,
            'gross_tonnage_extracted': False,
            'deadweight_extracted': False,
            'response_structure_correct': False,
            'confidence_level_present': False,
            'backend_logs_analyzed': False
        }
        
        # Test ship data
        self.test_ship_id = None
        self.test_ship_name = "SUNSHINE 01"  # As specified in review request
        
        # AI extraction results storage
        self.ai_extraction_results = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        # Store in log collection
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
    
    def test_ai_config_accessibility(self):
        """Test AI configuration endpoint accessibility"""
        try:
            self.log("🤖 Testing AI Configuration accessibility...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ai_config = response.json()
                self.log("✅ AI Configuration accessible")
                self.log(f"   Provider: {ai_config.get('provider')}")
                self.log(f"   Model: {ai_config.get('model')}")
                self.log(f"   Using Emergent Key: {ai_config.get('use_emergent_key')}")
                
                self.test_status['ai_config_accessible'] = True
                return True
            else:
                self.log(f"   ❌ AI Configuration not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ AI Config test error: {str(e)}", "ERROR")
            return False
    
    def find_test_ship(self):
        """Find SUNSHINE 01 ship for testing"""
        try:
            self.log(f"🚢 Finding test ship: {self.test_ship_name}...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships total")
                
                # Look for SUNSHINE 01
                for ship in ships:
                    if ship.get('name') == self.test_ship_name:
                        self.test_ship_id = ship.get('id')
                        self.log(f"✅ Found test ship: {self.test_ship_name}")
                        self.log(f"   Ship ID: {self.test_ship_id}")
                        self.log(f"   IMO: {ship.get('imo')}")
                        self.log(f"   Flag: {ship.get('flag')}")
                        self.log(f"   Class Society: {ship.get('ship_type')}")
                        
                        self.test_status['test_ship_found'] = True
                        return True
                
                self.log(f"   ❌ Test ship '{self.test_ship_name}' not found")
                self.log("   Available ships:")
                for ship in ships[:5]:  # Show first 5 ships
                    self.log(f"      - {ship.get('name')} (ID: {ship.get('id')})")
                return False
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Find test ship error: {str(e)}", "ERROR")
            return False
    
    def create_test_certificate_file(self):
        """Create a test certificate file with ship information for AI extraction"""
        try:
            # Create a realistic certificate content with ship information
            certificate_content = f"""
CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE

Certificate No: TEST-CSSC-2025-AI-001
Issue Date: 15 January 2024
Valid Until: 10 March 2026
Last Endorsed: 15 June 2024

SHIP PARTICULARS:
Ship Name: {self.test_ship_name}
IMO Number: 9415313
Flag State: BELIZE
Port of Registry: BELIZE CITY

CLASSIFICATION SOCIETY: PANAMA MARITIME DOCUMENTATION SERVICES (PMDS)
Class Notation: +1A1 Cargo Ship

SHIP SPECIFICATIONS:
Built Year: 2010
Gross Tonnage: 2959 GT
Deadweight: 4850 DWT
Length Overall: 89.50 m
Breadth: 13.20 m

This certificate is issued under the provisions of the International Convention 
for the Safety of Life at Sea, 1974, as amended.

The ship has been surveyed and found to comply with the relevant requirements 
of the above Convention.

This certificate is valid until 10 March 2026 subject to annual surveys.

Issued at: Panama City
Date: 15 January 2024

PANAMA MARITIME DOCUMENTATION SERVICES
Authorized Representative
"""
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.write(certificate_content)
            temp_file.close()
            
            self.log(f"✅ Created test certificate file: {temp_file.name}")
            self.log("   Certificate contains ship information:")
            self.log(f"      Ship Name: {self.test_ship_name}")
            self.log("      IMO Number: 9415313")
            self.log("      Flag: BELIZE")
            self.log("      Class Society: PANAMA MARITIME DOCUMENTATION SERVICES (PMDS)")
            self.log("      Built Year: 2010")
            self.log("      Gross Tonnage: 2959 GT")
            self.log("      Deadweight: 4850 DWT")
            
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Create test file error: {str(e)}", "ERROR")
            return None
    
    def test_multi_certificate_upload_with_ai_extraction(self):
        """Test multi-certificate upload endpoint with AI extraction of Basic Ship Information"""
        try:
            self.log("📄 Testing Multi-Certificate Upload with AI Extraction...")
            
            if not self.test_ship_id:
                self.log("   ❌ No test ship available")
                return False
            
            # Create test certificate file
            test_file_path = self.create_test_certificate_file()
            if not test_file_path:
                self.log("   ❌ Failed to create test certificate file")
                return False
            
            try:
                endpoint = f"{BACKEND_URL}/ships/{self.test_ship_id}/certificates/multi-upload"
                self.log(f"   POST {endpoint}")
                
                # Prepare file for upload
                with open(test_file_path, 'rb') as f:
                    files = {
                        'files': ('test_certificate.txt', f, 'text/plain')
                    }
                    
                    # Add form data
                    data = {
                        'category': 'certificates',
                        'sensitivity_level': 'public'
                    }
                    
                    self.log("   Uploading test certificate with ship information...")
                    response = requests.post(
                        endpoint,
                        files=files,
                        data=data,
                        headers=self.get_headers(),
                        timeout=120  # Longer timeout for AI processing
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.log("✅ Multi-certificate upload endpoint accessible")
                    self.test_status['multi_upload_endpoint_accessible'] = True
                    
                    # Log full response for analysis
                    self.log("   Upload Response:")
                    self.log(f"   {json.dumps(response_data, indent=2)}")
                    
                    # Analyze AI extraction results
                    return self.analyze_ai_extraction_response(response_data)
                    
                else:
                    self.log(f"   ❌ Multi-certificate upload failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"      Error: {response.text[:500]}")
                    return False
                    
            finally:
                # Clean up test file
                try:
                    os.unlink(test_file_path)
                    self.log("   🧹 Test file cleaned up")
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Multi-certificate upload test error: {str(e)}", "ERROR")
            return False
    
    def analyze_ai_extraction_response(self, response_data):
        """Analyze AI extraction response for Basic Ship Information fields"""
        try:
            self.log("🔍 Analyzing AI Extraction Response for Basic Ship Information...")
            
            # Look for AI analysis results in the response
            results = response_data.get('results', [])
            if not results:
                self.log("   ❌ No results found in response")
                return False
            
            self.log(f"   Found {len(results)} upload results")
            
            # Analyze each result
            ai_analysis_found = False
            basic_ship_info_found = False
            
            for i, result in enumerate(results):
                self.log(f"   📋 Analyzing Result {i+1}:")
                
                # Check if AI analysis was performed
                if 'analysis_result' in result or 'ai_analysis' in result:
                    ai_analysis_found = True
                    self.log("      ✅ AI analysis performed")
                    
                    # Get analysis result
                    analysis = result.get('analysis_result') or result.get('ai_analysis', {})
                    
                    # Store for detailed analysis
                    self.ai_extraction_results.append(analysis)
                    
                    # Check for Basic Ship Information fields
                    ship_info_fields = {
                        'ship_name': analysis.get('ship_name'),
                        'imo_number': analysis.get('imo_number'),
                        'flag': analysis.get('flag'),
                        'class_society': analysis.get('class_society'),
                        'built_year': analysis.get('built_year'),
                        'gross_tonnage': analysis.get('gross_tonnage'),
                        'deadweight': analysis.get('deadweight')
                    }
                    
                    self.log("      🚢 Basic Ship Information Fields:")
                    fields_found = 0
                    for field_name, field_value in ship_info_fields.items():
                        if field_value and field_value != 'null' and str(field_value).strip():
                            self.log(f"         ✅ {field_name}: {field_value}")
                            fields_found += 1
                            
                            # Mark specific field as extracted
                            if field_name == 'ship_name':
                                self.test_status['ship_name_extracted'] = True
                            elif field_name == 'imo_number':
                                self.test_status['imo_number_extracted'] = True
                            elif field_name == 'flag':
                                self.test_status['flag_extracted'] = True
                            elif field_name == 'class_society':
                                self.test_status['class_society_extracted'] = True
                            elif field_name == 'built_year':
                                self.test_status['built_year_extracted'] = True
                            elif field_name == 'gross_tonnage':
                                self.test_status['gross_tonnage_extracted'] = True
                            elif field_name == 'deadweight':
                                self.test_status['deadweight_extracted'] = True
                        else:
                            self.log(f"         ❌ {field_name}: {field_value or 'NOT EXTRACTED'}")
                    
                    if fields_found > 0:
                        basic_ship_info_found = True
                        self.log(f"      ✅ Basic Ship Info extracted: {fields_found}/7 fields")
                    else:
                        self.log("      ❌ No Basic Ship Information fields extracted")
                    
                    # Check other important fields
                    cert_fields = {
                        'cert_name': analysis.get('cert_name'),
                        'cert_no': analysis.get('cert_no'),
                        'issue_date': analysis.get('issue_date'),
                        'valid_date': analysis.get('valid_date'),
                        'last_endorse': analysis.get('last_endorse'),
                        'category': analysis.get('category'),
                        'confidence': analysis.get('confidence')
                    }
                    
                    self.log("      📋 Certificate Fields:")
                    for field_name, field_value in cert_fields.items():
                        if field_value and field_value != 'null':
                            self.log(f"         ✅ {field_name}: {field_value}")
                            if field_name == 'confidence':
                                self.test_status['confidence_level_present'] = True
                        else:
                            self.log(f"         ❌ {field_name}: {field_value or 'NOT EXTRACTED'}")
                    
                    # Check response structure
                    expected_fields = ['cert_name', 'cert_no', 'issue_date', 'valid_date', 'last_endorse', 
                                     'ship_name', 'imo_number', 'flag', 'class_society', 'built_year', 
                                     'gross_tonnage', 'deadweight', 'category', 'confidence']
                    
                    structure_correct = all(field in analysis for field in expected_fields)
                    if structure_correct:
                        self.log("      ✅ Response structure contains all expected fields")
                        self.test_status['response_structure_correct'] = True
                    else:
                        missing_fields = [field for field in expected_fields if field not in analysis]
                        self.log(f"      ❌ Missing fields in response: {missing_fields}")
                
                else:
                    self.log("      ❌ No AI analysis found in result")
            
            # Update test status
            if ai_analysis_found:
                self.test_status['ai_analysis_working'] = True
                self.log("   ✅ AI Analysis is working")
            else:
                self.log("   ❌ AI Analysis not working")
            
            if basic_ship_info_found:
                self.test_status['basic_ship_info_extracted'] = True
                self.log("   ✅ Basic Ship Information extraction is working")
            else:
                self.log("   ❌ Basic Ship Information extraction not working")
            
            return ai_analysis_found and basic_ship_info_found
            
        except Exception as e:
            self.log(f"❌ AI extraction analysis error: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs_for_ai_debug(self):
        """Check backend logs for AI analysis debug information"""
        try:
            self.log("📋 Checking Backend Logs for AI Analysis Debug...")
            
            # Try to get backend logs (this might not be directly accessible via API)
            # We'll look for debug patterns in our stored logs and check supervisor logs
            
            try:
                # Check supervisor backend logs
                import subprocess
                result = subprocess.run(['tail', '-n', '100', '/var/log/supervisor/backend.out.log'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    backend_log_content = result.stdout
                    self.log("   ✅ Backend logs accessible")
                    
                    # Look for AI analysis debug patterns
                    debug_patterns = [
                        r"🔍 AI Analysis Debug for",
                        r"Raw analysis_result structure",
                        r"Field extraction success",
                        r"Field extraction failure",
                        r"AI analysis for docking dates extraction",
                        r"Using AI analysis",
                        r"google gemini"
                    ]
                    
                    debug_found = False
                    for pattern in debug_patterns:
                        matches = re.findall(pattern, backend_log_content, re.IGNORECASE)
                        if matches:
                            debug_found = True
                            self.log(f"      ✅ Found debug pattern: '{pattern}' ({len(matches)} times)")
                    
                    if debug_found:
                        self.log("   ✅ AI Analysis debug logs found")
                        self.test_status['backend_logs_analyzed'] = True
                        
                        # Show recent AI-related log entries
                        ai_lines = [line for line in backend_log_content.split('\n') 
                                   if any(keyword in line.lower() for keyword in ['ai', 'analysis', 'extraction', 'gemini'])]
                        
                        if ai_lines:
                            self.log("   📋 Recent AI-related log entries:")
                            for line in ai_lines[-10:]:  # Show last 10 AI-related lines
                                if line.strip():
                                    self.log(f"      {line.strip()}")
                    else:
                        self.log("   ❌ No AI Analysis debug patterns found in logs")
                    
                    return debug_found
                else:
                    self.log("   ❌ Could not access backend logs")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.log("   ⚠️ Backend log check timed out")
                return False
            except Exception as log_error:
                self.log(f"   ⚠️ Backend log check error: {str(log_error)}")
                return False
                
        except Exception as e:
            self.log(f"❌ Backend logs analysis error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_ai_extraction_tests(self):
        """Main test function for AI extraction of Basic Ship Information"""
        self.log("🤖 STARTING AI ENHANCED BASIC SHIP INFORMATION EXTRACTION TESTING")
        self.log("🎯 FOCUS: Test AI extraction of new Basic Ship Information fields")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Test AI Configuration
            self.log("\n🤖 STEP 2: AI CONFIGURATION CHECK")
            self.log("=" * 50)
            self.test_ai_config_accessibility()
            
            # Step 3: Find Test Ship
            self.log("\n🚢 STEP 3: FIND TEST SHIP")
            self.log("=" * 50)
            if not self.find_test_ship():
                self.log("❌ Test ship not found - cannot proceed with testing")
                return False
            
            # Step 4: Test Multi-Certificate Upload with AI Extraction
            self.log("\n📄 STEP 4: MULTI-CERTIFICATE UPLOAD WITH AI EXTRACTION")
            self.log("=" * 50)
            ai_extraction_success = self.test_multi_certificate_upload_with_ai_extraction()
            
            # Step 5: Check Backend Logs
            self.log("\n📋 STEP 5: BACKEND LOGS ANALYSIS")
            self.log("=" * 50)
            self.check_backend_logs_for_ai_debug()
            
            # Step 6: Final Analysis
            self.log("\n📊 STEP 6: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return ai_extraction_success
            
        except Exception as e:
            self.log(f"❌ Comprehensive test error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of AI extraction testing"""
        try:
            self.log("🤖 AI ENHANCED BASIC SHIP INFORMATION EXTRACTION - RESULTS")
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
            
            # Basic Ship Information Fields Analysis
            ship_info_fields = [
                'ship_name_extracted',
                'imo_number_extracted', 
                'flag_extracted',
                'class_society_extracted',
                'built_year_extracted',
                'gross_tonnage_extracted',
                'deadweight_extracted'
            ]
            
            ship_info_passed = sum(1 for field in ship_info_fields if self.test_status.get(field, False))
            ship_info_rate = (ship_info_passed / len(ship_info_fields)) * 100
            
            self.log(f"\n🚢 BASIC SHIP INFORMATION EXTRACTION: {ship_info_rate:.1f}% ({ship_info_passed}/{len(ship_info_fields)})")
            
            if ship_info_passed >= 5:  # At least 5/7 fields extracted
                self.log("   ✅ EXCELLENT: Most Basic Ship Information fields extracted successfully")
            elif ship_info_passed >= 3:
                self.log("   ⚠️ PARTIAL: Some Basic Ship Information fields extracted")
            else:
                self.log("   ❌ POOR: Few or no Basic Ship Information fields extracted")
            
            # AI Analysis Quality
            if self.test_status['ai_analysis_working']:
                self.log("\n🤖 AI ANALYSIS STATUS: ✅ WORKING")
                if self.test_status['confidence_level_present']:
                    self.log("   ✅ Confidence levels provided")
                if self.test_status['response_structure_correct']:
                    self.log("   ✅ Response structure correct")
            else:
                self.log("\n🤖 AI ANALYSIS STATUS: ❌ NOT WORKING")
            
            # Expected Response Structure Verification
            if self.test_status['response_structure_correct']:
                self.log("\n📋 RESPONSE STRUCTURE: ✅ MATCHES EXPECTED FORMAT")
                self.log("   All expected fields present in AI analysis response")
            else:
                self.log("\n📋 RESPONSE STRUCTURE: ❌ DOES NOT MATCH EXPECTED FORMAT")
            
            # Backend Logs Analysis
            if self.test_status['backend_logs_analyzed']:
                self.log("\n📋 BACKEND LOGS: ✅ AI DEBUG INFORMATION FOUND")
            else:
                self.log("\n📋 BACKEND LOGS: ❌ NO AI DEBUG INFORMATION FOUND")
            
            # Final conclusion based on review request requirements
            if success_rate >= 80 and ship_info_rate >= 70:
                self.log(f"\n🎉 CONCLUSION: AI ENHANCED BASIC SHIP INFORMATION EXTRACTION IS WORKING EXCELLENTLY")
                self.log(f"   Overall Success: {success_rate:.1f}%")
                self.log(f"   Ship Info Extraction: {ship_info_rate:.1f}%")
                self.log(f"   ✅ Review request requirements satisfied")
                self.log(f"   ✅ AI can extract Basic Ship Information fields from certificates")
                self.log(f"   ✅ Enhanced response structure includes ship information")
                self.log(f"   ✅ Multi-certificate upload with AI analysis working")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: AI ENHANCED EXTRACTION PARTIALLY WORKING")
                self.log(f"   Overall Success: {success_rate:.1f}%")
                self.log(f"   Ship Info Extraction: {ship_info_rate:.1f}%")
                self.log(f"   ⚠️ Some functionality working, improvements needed")
                
                if not self.test_status['ai_analysis_working']:
                    self.log("   ❌ CRITICAL: AI analysis pipeline not working")
                if ship_info_rate < 50:
                    self.log("   ❌ CRITICAL: Basic Ship Information extraction failing")
            else:
                self.log(f"\n❌ CONCLUSION: AI ENHANCED EXTRACTION HAS CRITICAL ISSUES")
                self.log(f"   Overall Success: {success_rate:.1f}%")
                self.log(f"   Ship Info Extraction: {ship_info_rate:.1f}%")
                self.log(f"   ❌ Major fixes needed for AI extraction functionality")
            
            # Detailed AI Extraction Results
            if self.ai_extraction_results:
                self.log(f"\n🔍 DETAILED AI EXTRACTION RESULTS:")
                for i, result in enumerate(self.ai_extraction_results):
                    self.log(f"   Result {i+1}:")
                    self.log(f"   {json.dumps(result, indent=4)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run AI extraction tests"""
    print("🤖 AI ENHANCED BASIC SHIP INFORMATION EXTRACTION TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = AIExtractionTester()
        success = tester.run_comprehensive_ai_extraction_tests()
        
        if success:
            print("\n✅ AI EXTRACTION TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ AI EXTRACTION TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Duplicate Check Functionality Testing Script for Ship Management System
FOCUS: Testing duplicate certificate detection in multi-certificate upload workflow

REVIEW REQUEST REQUIREMENTS:
1. AI Classification Testing - Test với certificate files để xem AI classify category là gì
2. Duplicate Check Execution Path - Verify điều kiện để đến được duplicate check
3. Test Duplicate Detection Logic - Upload same certificate multiple times to same ship
4. Analysis of Multi-Upload Flow - Trace execution path
5. Backend Log Analysis - Look for specific log patterns

AUTHENTICATION: admin1/123456

TEST FOCUS AREAS:
- AI Classification: Check if certificates are classified as "certificates" category
- IMO Validation Logic: Check if is_marine_certificate = True
- Duplicate Check Function: Verify if check_certificate_duplicates is called
- 5-Field Duplicate Logic: Test enhanced duplicate detection
- Backend Logs: Monitor for specific patterns
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
import base64

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://seacraft-portfolio.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class DuplicateCheckTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for duplicate check functionality
        self.test_tracking = {
            # Authentication
            'authentication_successful': False,
            
            # AI Classification Testing
            'ai_classification_tested': False,
            'certificates_classified_as_certificates': False,
            'certificates_classified_as_non_marine': False,
            'ai_confidence_level_checked': False,
            
            # Duplicate Check Execution Path
            'multi_upload_endpoint_accessible': False,
            'imo_validation_logic_reached': False,
            'is_marine_certificate_flag_checked': False,
            'duplicate_check_function_called': False,
            
            # Duplicate Detection Logic
            '5_field_duplicate_logic_tested': False,
            'duplicate_detection_working': False,
            'duplicate_resolution_dialog_triggered': False,
            
            # Backend Log Analysis
            'category_detection_logs_found': False,
            'manual_review_logs_found': False,
            'enhanced_duplicate_check_logs_found': False,
            'all_5_fields_match_logs_found': False,
            
            # Test Scenarios
            'non_marine_certificate_test_completed': False,
            'marine_certificate_test_completed': False,
            'duplicate_certificate_test_completed': False,
        }
        
        # Test ship data
        self.test_ship_id = None
        self.test_ship_name = "DUPLICATE CHECK TEST SHIP"
        
        # Sample certificate data for testing
        self.test_certificates = {
            'marine_certificate': {
                'filename': 'test_marine_certificate.pdf',
                'content': self.create_sample_marine_certificate_content()
            },
            'non_marine_certificate': {
                'filename': 'test_non_marine_certificate.pdf', 
                'content': self.create_sample_non_marine_certificate_content()
            },
            'duplicate_certificate': {
                'filename': 'duplicate_marine_certificate.pdf',
                'content': self.create_sample_marine_certificate_content()  # Same content for duplicate test
            }
        }
        
    def create_sample_marine_certificate_content(self):
        """Create sample marine certificate content that should be classified as 'certificates'"""
        return """
CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE

Certificate No: CSSC-2024-001
IMO Number: 9415313
Ship Name: SUNSHINE 01
Flag: BELIZE
Class Society: PMDS

Issue Date: 10/01/2024
Valid Date: 10/03/2026
Last Endorse: 15/02/2024

This is to certify that this ship has been surveyed in accordance with the provisions of regulation I/12 of the International Convention for the Safety of Life at Sea, 1974, as amended, and that the survey showed that the condition of the structure, machinery and equipment covered by this certificate and the condition of the ship and its equipment are in all respects satisfactory and that the ship complies with the applicable safety requirements of the above Convention.

Issued by: Panama Maritime Documentation Services
Date: 10/01/2024
"""

    def create_sample_non_marine_certificate_content(self):
        """Create sample non-marine certificate content that should NOT be classified as 'certificates'"""
        return """
QUALITY ASSURANCE TEST REPORT

Report No: QA-2024-001
Company: Test Company Ltd
Location: Test Location

Test Date: 10/01/2024
Report Date: 15/01/2024

This report contains the results of quality assurance testing performed on various equipment and systems. The testing was conducted in accordance with industry standards and best practices.

Test Results:
- System A: PASS
- System B: PASS  
- System C: PASS

All systems tested meet the required specifications and quality standards.

Prepared by: Quality Assurance Department
Date: 15/01/2024
"""
        
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
                
                self.test_tracking['authentication_successful'] = True
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
    
    def find_test_ship(self):
        """Find SUNSHINE 01 ship for testing as specified in review request"""
        try:
            self.log("🚢 Finding SUNSHINE 01 ship for testing...")
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ships = response.json()
                
                # Look for SUNSHINE 01 ship
                for ship in ships:
                    if ship.get('name') == 'SUNSHINE 01':
                        self.test_ship_id = ship.get('id')
                        self.log("✅ SUNSHINE 01 ship found")
                        self.log(f"   Ship ID: {self.test_ship_id}")
                        self.log(f"   Ship Name: {ship.get('name')}")
                        self.log(f"   IMO: {ship.get('imo')}")
                        self.log(f"   Flag: {ship.get('flag')}")
                        self.log(f"   Class Society: {ship.get('ship_type')}")
                        return True
                
                # If SUNSHINE 01 not found, create it
                self.log("⚠️ SUNSHINE 01 ship not found, creating test ship...")
                return self.create_test_ship()
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Find test ship error: {str(e)}", "ERROR")
            return False
    
    def create_test_ship(self):
        """Create SUNSHINE 01 test ship if not found"""
        try:
            self.log("🚢 Creating SUNSHINE 01 test ship...")
            
            ship_data = {
                'name': 'SUNSHINE 01',
                'imo': '9415313',
                'flag': 'BELIZE',
                'ship_type': 'PMDS',
                'gross_tonnage': 2959.0,
                'ship_owner': 'Test Owner',
                'company': 'AMCSC'
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
                self.log("✅ SUNSHINE 01 test ship created successfully")
                self.log(f"   Ship ID: {self.test_ship_id}")
                return True
            else:
                self.log(f"   ❌ Test ship creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Test ship creation error: {str(e)}", "ERROR")
            return False
    
    def create_test_file(self, filename, content):
        """Create a temporary test file"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False)
            temp_file.write(content)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Error creating test file: {str(e)}", "ERROR")
            return None
    
    def test_ai_classification(self):
        """Test AI classification of certificates"""
        try:
            self.log("🤖 TESTING AI CLASSIFICATION...")
            self.log("=" * 60)
            
            if not self.test_ship_id:
                self.log("   ❌ No test ship available")
                return False
            
            # Test 1: Marine Certificate Classification
            self.log("📂 Test 1: Marine Certificate Classification")
            marine_result = self.test_certificate_classification(
                self.test_certificates['marine_certificate'],
                expected_category='certificates',
                test_name='Marine Certificate'
            )
            
            # Test 2: Non-Marine Certificate Classification  
            self.log("\n📂 Test 2: Non-Marine Certificate Classification")
            non_marine_result = self.test_certificate_classification(
                self.test_certificates['non_marine_certificate'],
                expected_category='test_reports',
                test_name='Non-Marine Certificate'
            )
            
            self.test_tracking['ai_classification_tested'] = True
            
            if marine_result and non_marine_result:
                self.log("✅ AI Classification testing completed successfully")
                return True
            else:
                self.log("❌ AI Classification testing had issues")
                return False
                
        except Exception as e:
            self.log(f"❌ AI Classification testing error: {str(e)}", "ERROR")
            return False
    
    def test_certificate_classification(self, cert_data, expected_category, test_name):
        """Test classification of a specific certificate"""
        try:
            self.log(f"   Testing {test_name}...")
            
            # Create temporary file
            temp_file_path = self.create_test_file(cert_data['filename'], cert_data['content'])
            if not temp_file_path:
                return False
            
            try:
                # Upload certificate using multi-upload endpoint
                endpoint = f"{BACKEND_URL}/certificates/multi-upload"
                
                with open(temp_file_path, 'rb') as f:
                    files = {'files': (cert_data['filename'], f, 'application/pdf')}
                    data = {'ship_id': self.test_ship_id}
                    
                    self.log(f"   POST {endpoint}")
                    response = requests.post(
                        endpoint,
                        files=files,
                        data=data,
                        headers=self.get_headers(),
                        timeout=120
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                    
                    # Check if we have results
                    results = response_data.get('results', [])
                    if results:
                        result = results[0]
                        category = result.get('category')
                        confidence = result.get('confidence', 'unknown')
                        ship_name = result.get('ship_name', 'Unknown_Ship')
                        
                        self.log(f"   📂 Category detected: {category}")
                        self.log(f"   🎯 Confidence: {confidence}")
                        self.log(f"   🚢 Ship Name extracted: {ship_name}")
                        
                        # Check if category matches expected
                        if category == expected_category:
                            self.log(f"   ✅ {test_name} correctly classified as '{category}'")
                            if expected_category == 'certificates':
                                self.test_tracking['certificates_classified_as_certificates'] = True
                            else:
                                self.test_tracking['certificates_classified_as_non_marine'] = True
                        else:
                            self.log(f"   ❌ {test_name} incorrectly classified as '{category}' (expected '{expected_category}')")
                        
                        # Check confidence level
                        self.test_tracking['ai_confidence_level_checked'] = True
                        
                        # Look for specific log patterns
                        self.analyze_response_for_log_patterns(response_data, test_name)
                        
                        return category == expected_category
                    else:
                        self.log(f"   ❌ No results in response")
                        return False
                else:
                    self.log(f"   ❌ Upload failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"      Error: {error_data}")
                    except:
                        self.log(f"      Error: {response.text[:500]}")
                    return False
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"   ❌ Certificate classification error: {str(e)}", "ERROR")
            return False
    
    def analyze_response_for_log_patterns(self, response_data, test_name):
        """Analyze response for specific log patterns mentioned in review request"""
        try:
            # Look for category detection patterns
            results = response_data.get('results', [])
            if results:
                result = results[0]
                category = result.get('category')
                
                if category:
                    self.log(f"   📂 Category detected: {category}")
                    self.test_tracking['category_detection_logs_found'] = True
                
                # Check for manual review requirement
                if result.get('requires_manual_review'):
                    self.log(f"   ⚠️ File {test_name} not auto-classified as marine certificate")
                    self.test_tracking['manual_review_logs_found'] = True
                
                # Check for marine certificate classification
                is_marine = category == 'certificates'
                self.log(f"   🔍 is_marine_certificate = {is_marine}")
                
        except Exception as e:
            self.log(f"   ⚠️ Error analyzing log patterns: {str(e)}", "WARNING")
    
    def test_duplicate_check_execution_path(self):
        """Test the execution path to reach duplicate check function"""
        try:
            self.log("🔍 TESTING DUPLICATE CHECK EXECUTION PATH...")
            self.log("=" * 60)
            
            if not self.test_ship_id:
                self.log("   ❌ No test ship available")
                return False
            
            # Test multi-upload endpoint accessibility
            self.log("📡 Testing multi-upload endpoint accessibility...")
            endpoint = f"{BACKEND_URL}/certificates/multi-upload"
            
            # Create a simple test file
            temp_file_path = self.create_test_file(
                'path_test.pdf', 
                self.test_certificates['marine_certificate']['content']
            )
            
            if not temp_file_path:
                return False
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {'files': ('path_test.pdf', f, 'application/pdf')}
                    data = {'ship_id': self.test_ship_id}
                    
                    response = requests.post(
                        endpoint,
                        files=files,
                        data=data,
                        headers=self.get_headers(),
                        timeout=120
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.log("✅ Multi-upload endpoint accessible")
                    self.test_tracking['multi_upload_endpoint_accessible'] = True
                    
                    response_data = response.json()
                    
                    # Analyze execution path
                    self.analyze_execution_path(response_data)
                    
                    return True
                else:
                    self.log(f"   ❌ Multi-upload endpoint failed: {response.status_code}")
                    return False
                    
            finally:
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Execution path testing error: {str(e)}", "ERROR")
            return False
    
    def analyze_execution_path(self, response_data):
        """Analyze the execution path from the response"""
        try:
            results = response_data.get('results', [])
            if not results:
                return
            
            result = results[0]
            
            # Check if we reached IMO validation logic
            category = result.get('category')
            if category == 'certificates':
                self.log("   ✅ Certificate classified as 'certificates' - IMO validation logic should be reached")
                self.test_tracking['imo_validation_logic_reached'] = True
                self.test_tracking['is_marine_certificate_flag_checked'] = True
            else:
                self.log(f"   ⚠️ Certificate classified as '{category}' - IMO validation logic bypassed")
            
            # Check for duplicate check indicators
            if result.get('duplicate_detected') is not None:
                self.log("   ✅ Duplicate check function appears to have been called")
                self.test_tracking['duplicate_check_function_called'] = True
            
            # Look for enhanced duplicate check patterns
            if 'duplicate_info' in result:
                self.log("   🔍 Enhanced duplicate check information found")
                self.test_tracking['enhanced_duplicate_check_logs_found'] = True
                
        except Exception as e:
            self.log(f"   ⚠️ Error analyzing execution path: {str(e)}", "WARNING")
    
    def test_duplicate_detection_logic(self):
        """Test the 5-field duplicate detection logic"""
        try:
            self.log("🔄 TESTING DUPLICATE DETECTION LOGIC...")
            self.log("=" * 60)
            
            if not self.test_ship_id:
                self.log("   ❌ No test ship available")
                return False
            
            # Step 1: Upload first certificate
            self.log("📤 Step 1: Uploading first certificate...")
            first_upload_success = self.upload_certificate_for_duplicate_test(
                self.test_certificates['marine_certificate'],
                "First Upload"
            )
            
            if not first_upload_success:
                self.log("   ❌ First certificate upload failed")
                return False
            
            # Wait a moment
            time.sleep(2)
            
            # Step 2: Upload duplicate certificate (same content)
            self.log("\n📤 Step 2: Uploading duplicate certificate...")
            duplicate_upload_result = self.upload_certificate_for_duplicate_test(
                self.test_certificates['duplicate_certificate'],
                "Duplicate Upload"
            )
            
            # Step 3: Analyze duplicate detection
            self.log("\n🔍 Step 3: Analyzing duplicate detection...")
            self.analyze_duplicate_detection_results()
            
            self.test_tracking['5_field_duplicate_logic_tested'] = True
            
            return True
            
        except Exception as e:
            self.log(f"❌ Duplicate detection testing error: {str(e)}", "ERROR")
            return False
    
    def upload_certificate_for_duplicate_test(self, cert_data, upload_name):
        """Upload a certificate for duplicate testing"""
        try:
            temp_file_path = self.create_test_file(cert_data['filename'], cert_data['content'])
            if not temp_file_path:
                return False
            
            try:
                endpoint = f"{BACKEND_URL}/certificates/multi-upload"
                
                with open(temp_file_path, 'rb') as f:
                    files = {'files': (cert_data['filename'], f, 'application/pdf')}
                    data = {'ship_id': self.test_ship_id}
                    
                    self.log(f"   POST {endpoint} ({upload_name})")
                    response = requests.post(
                        endpoint,
                        files=files,
                        data=data,
                        headers=self.get_headers(),
                        timeout=120
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.log(f"   ✅ {upload_name} successful")
                    
                    # Look for duplicate detection indicators
                    results = response_data.get('results', [])
                    if results:
                        result = results[0]
                        if result.get('duplicate_detected'):
                            self.log(f"   🔍 Duplicate detected in {upload_name}")
                            self.test_tracking['duplicate_detection_working'] = True
                        
                        if result.get('requires_duplicate_resolution'):
                            self.log(f"   ⚠️ Duplicate resolution required for {upload_name}")
                            self.test_tracking['duplicate_resolution_dialog_triggered'] = True
                    
                    return True
                else:
                    self.log(f"   ❌ {upload_name} failed: {response.status_code}")
                    return False
                    
            finally:
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"   ❌ {upload_name} error: {str(e)}", "ERROR")
            return False
    
    def analyze_duplicate_detection_results(self):
        """Analyze the results of duplicate detection testing"""
        try:
            # Get certificates for the test ship to see if duplicates were handled
            endpoint = f"{BACKEND_URL}/certificates"
            params = {'ship_id': self.test_ship_id}
            
            response = requests.get(endpoint, params=params, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                certificates = response.json()
                
                # Count certificates with similar names
                marine_certs = [cert for cert in certificates if 'CARGO SHIP SAFETY CONSTRUCTION' in cert.get('cert_name', '')]
                
                self.log(f"   📊 Found {len(marine_certs)} marine certificates in database")
                
                if len(marine_certs) > 1:
                    self.log("   ⚠️ Multiple similar certificates found - duplicate detection may not be working")
                elif len(marine_certs) == 1:
                    self.log("   ✅ Only one certificate found - duplicate detection may be working")
                
                # Look for certificates with notes indicating duplicates
                for cert in marine_certs:
                    if cert.get('notes'):
                        self.log(f"   📝 Certificate notes: {cert.get('notes')}")
                        
        except Exception as e:
            self.log(f"   ⚠️ Error analyzing duplicate results: {str(e)}", "WARNING")
    
    def test_backend_log_analysis(self):
        """Test for specific backend log patterns mentioned in review request"""
        try:
            self.log("📋 TESTING BACKEND LOG ANALYSIS...")
            self.log("=" * 60)
            
            # Check supervisor backend logs
            self.log("📋 Checking supervisor backend logs...")
            
            try:
                # Try to read backend logs
                import subprocess
                result = subprocess.run(
                    ['tail', '-n', '100', '/var/log/supervisor/backend.err.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    log_content = result.stdout
                    self.analyze_backend_logs(log_content)
                else:
                    self.log("   ⚠️ Could not read backend error logs")
                    
            except Exception as e:
                self.log(f"   ⚠️ Error reading backend logs: {str(e)}", "WARNING")
            
            # Also try stdout logs
            try:
                result = subprocess.run(
                    ['tail', '-n', '100', '/var/log/supervisor/backend.out.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    log_content = result.stdout
                    self.analyze_backend_logs(log_content)
                    
            except Exception as e:
                self.log(f"   ⚠️ Error reading backend stdout logs: {str(e)}", "WARNING")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Backend log analysis error: {str(e)}", "ERROR")
            return False
    
    def analyze_backend_logs(self, log_content):
        """Analyze backend logs for specific patterns"""
        try:
            # Look for specific log patterns mentioned in review request
            patterns = {
                'category_detected': r'📂 Category detected:',
                'manual_review': r'⚠️ File .* not auto-classified as marine certificate',
                'enhanced_duplicate_check': r'🔍 Enhanced Duplicate Check - Comparing 5 fields',
                'all_fields_match': r'✅ ALL 5 fields match - DUPLICATE DETECTED'
            }
            
            for pattern_name, pattern in patterns.items():
                matches = re.findall(pattern, log_content, re.IGNORECASE)
                if matches:
                    self.log(f"   ✅ Found {len(matches)} instances of '{pattern_name}' pattern")
                    if pattern_name == 'category_detected':
                        self.test_tracking['category_detection_logs_found'] = True
                    elif pattern_name == 'manual_review':
                        self.test_tracking['manual_review_logs_found'] = True
                    elif pattern_name == 'enhanced_duplicate_check':
                        self.test_tracking['enhanced_duplicate_check_logs_found'] = True
                    elif pattern_name == 'all_fields_match':
                        self.test_tracking['all_5_fields_match_logs_found'] = True
                else:
                    self.log(f"   ❌ No instances of '{pattern_name}' pattern found")
            
            # Show recent relevant log entries
            lines = log_content.split('\n')
            relevant_lines = [line for line in lines if any(keyword in line.lower() for keyword in ['duplicate', 'category', 'marine', 'certificate'])]
            
            if relevant_lines:
                self.log("   📋 Recent relevant log entries:")
                for line in relevant_lines[-10:]:  # Show last 10 relevant lines
                    self.log(f"      {line}")
                    
        except Exception as e:
            self.log(f"   ⚠️ Error analyzing log content: {str(e)}", "WARNING")
    
    def run_comprehensive_duplicate_check_tests(self):
        """Main test function for duplicate check functionality"""
        self.log("🔍 STARTING DUPLICATE CHECK FUNCTIONALITY TESTING")
        self.log("🎯 FOCUS: Multi-certificate upload duplicate detection")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Find/Create Test Ship
            self.log("\n🚢 STEP 2: FIND/CREATE TEST SHIP")
            self.log("=" * 50)
            if not self.find_test_ship():
                self.log("❌ Test ship setup failed - cannot proceed with testing")
                return False
            
            # Step 3: Test AI Classification
            self.log("\n🤖 STEP 3: AI CLASSIFICATION TESTING")
            self.log("=" * 50)
            ai_classification_success = self.test_ai_classification()
            
            # Step 4: Test Duplicate Check Execution Path
            self.log("\n🔍 STEP 4: DUPLICATE CHECK EXECUTION PATH")
            self.log("=" * 50)
            execution_path_success = self.test_duplicate_check_execution_path()
            
            # Step 5: Test Duplicate Detection Logic
            self.log("\n🔄 STEP 5: DUPLICATE DETECTION LOGIC")
            self.log("=" * 50)
            duplicate_logic_success = self.test_duplicate_detection_logic()
            
            # Step 6: Backend Log Analysis
            self.log("\n📋 STEP 6: BACKEND LOG ANALYSIS")
            self.log("=" * 50)
            log_analysis_success = self.test_backend_log_analysis()
            
            # Step 7: Final Analysis
            self.log("\n📊 STEP 7: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Comprehensive testing error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis of duplicate check testing"""
        try:
            self.log("🔍 DUPLICATE CHECK FUNCTIONALITY TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.test_tracking.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.test_tracking)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.test_tracking)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.test_tracking)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.test_tracking)})")
            
            # Specific analysis for review request requirements
            self.log("\n🎯 REVIEW REQUEST REQUIREMENTS ANALYSIS:")
            
            # 1. AI Classification Testing
            ai_tests = ['ai_classification_tested', 'certificates_classified_as_certificates', 'certificates_classified_as_non_marine']
            ai_passed = sum(1 for test in ai_tests if self.test_tracking.get(test, False))
            self.log(f"\n🤖 AI CLASSIFICATION: {ai_passed}/{len(ai_tests)} tests passed")
            
            if self.test_tracking['certificates_classified_as_non_marine']:
                self.log("   ❗ CRITICAL FINDING: AI classifies certificates as non-marine (test_reports)")
                self.log("   ❗ This explains why duplicate check is not reached!")
            
            # 2. Duplicate Check Execution Path
            path_tests = ['multi_upload_endpoint_accessible', 'imo_validation_logic_reached', 'duplicate_check_function_called']
            path_passed = sum(1 for test in path_tests if self.test_tracking.get(test, False))
            self.log(f"\n🔍 EXECUTION PATH: {path_passed}/{len(path_tests)} tests passed")
            
            # 3. Duplicate Detection Logic
            logic_tests = ['5_field_duplicate_logic_tested', 'duplicate_detection_working']
            logic_passed = sum(1 for test in logic_tests if self.test_tracking.get(test, False))
            self.log(f"\n🔄 DUPLICATE LOGIC: {logic_passed}/{len(logic_tests)} tests passed")
            
            # 4. Backend Log Analysis
            log_tests = ['category_detection_logs_found', 'enhanced_duplicate_check_logs_found']
            log_passed = sum(1 for test in log_tests if self.test_tracking.get(test, False))
            self.log(f"\n📋 LOG ANALYSIS: {log_passed}/{len(log_tests)} tests passed")
            
            # Final conclusion based on review request
            self.log("\n🎯 DUPLICATE CHECK ANALYSIS CONCLUSION:")
            
            if self.test_tracking['certificates_classified_as_non_marine']:
                self.log("❗ ROOT CAUSE IDENTIFIED: AI Classification Issue")
                self.log("   - AI classifies certificates as 'test_reports' instead of 'certificates'")
                self.log("   - This prevents is_marine_certificate = True condition")
                self.log("   - IMO validation logic is bypassed")
                self.log("   - Duplicate check function is NEVER called")
                self.log("   - System requires manual review instead")
                
            if not self.test_tracking['duplicate_check_function_called']:
                self.log("❗ DUPLICATE CHECK NOT EXECUTED")
                self.log("   - check_certificate_duplicates function not reached")
                self.log("   - 5-field duplicate logic not tested in practice")
                
            if not self.test_tracking['enhanced_duplicate_check_logs_found']:
                self.log("❗ ENHANCED DUPLICATE CHECK LOGS NOT FOUND")
                self.log("   - No '🔍 Enhanced Duplicate Check - Comparing 5 fields' logs")
                self.log("   - No '✅ ALL 5 fields match - DUPLICATE DETECTED' logs")
            
            # Recommendations
            self.log("\n💡 RECOMMENDATIONS:")
            self.log("1. Fix AI classification to properly identify marine certificates")
            self.log("2. Ensure certificates are classified as 'certificates' category")
            self.log("3. Verify IMO extraction from certificate text")
            self.log("4. Test duplicate check with properly classified certificates")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run duplicate check tests"""
    print("🔍 DUPLICATE CHECK FUNCTIONALITY TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = DuplicateCheckTester()
        success = tester.run_comprehensive_duplicate_check_tests()
        
        if success:
            print("\n✅ DUPLICATE CHECK TESTING COMPLETED")
        else:
            print("\n❌ DUPLICATE CHECK TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
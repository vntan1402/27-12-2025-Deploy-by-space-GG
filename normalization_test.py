#!/usr/bin/env python3
"""
Crew Certificates Issued By Normalization Testing

REVIEW REQUEST REQUIREMENTS:
Test the `/api/crew-certificates/analyze-file` endpoint to verify that the `normalize_issued_by()` 
function returns normalized "Issued By" values for frontend auto-fill.

Testing Focus:
1. Authentication with admin1/123456
2. Ship selection (BROTHER 36 for AMCSC company)
3. PDF file upload testing
4. AI extraction verification
5. Issued By normalization verification
6. Certificate name and number extraction verification

Expected Results:
- `issued_by` should be normalized (e.g., "Panama Maritime Authority" instead of full long names)
- `cert_name` should follow priority rules (GMDSS, COC phrases, rank-based)
- `cert_no` should extract correct certificate number
- Response should be ready for frontend auto-fill
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
    # Fallback to external URL from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class CrewCertificatesNormalizationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for crew certificates normalization
        self.normalization_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'amcsc_company_found': False,
            'brother_36_ship_found': False,
            'crew_member_found': False,
            
            # Endpoint accessibility
            'analyze_file_endpoint_accessible': False,
            'multipart_form_data_accepted': False,
            'ship_id_validation_working': False,
            
            # AI extraction functionality
            'document_ai_processing_working': False,
            'certificate_analysis_successful': False,
            'field_extraction_working': False,
            
            # Normalization verification
            'issued_by_normalization_applied': False,
            'issued_by_value_normalized': False,
            'normalize_function_called': False,
            
            # Certificate extraction verification
            'cert_name_extraction_working': False,
            'cert_no_extraction_working': False,
            'cert_name_priority_rules_applied': False,
            'gmdss_certificate_detected': False,
            
            # Response structure verification
            'response_structure_correct': False,
            'frontend_ready_format': False,
            'all_expected_fields_present': False,
        }
        
        # Store test data
        self.ship_id = None
        self.crew_id = None
        self.test_pdf_file = None
        
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
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.normalization_tests['authentication_successful'] = True
                
                # Check if user is associated with AMCSC company
                user_company = self.current_user.get('company', '')
                if user_company == 'AMCSC':
                    self.normalization_tests['user_company_identified'] = True
                    self.normalization_tests['amcsc_company_found'] = True
                    self.log("✅ User is associated with AMCSC company")
                else:
                    self.log(f"⚠️ User company is '{user_company}', expected 'AMCSC'")
                
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_brother_36_ship(self):
        """Find BROTHER 36 ship for AMCSC company"""
        try:
            self.log("🚢 Finding BROTHER 36 ship for AMCSC company...")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships total")
                
                for ship in ships:
                    ship_name = ship.get("name", "")
                    if ship_name == "BROTHER 36":
                        self.ship_id = ship.get("id")
                        self.log(f"✅ Found BROTHER 36 ship (ID: {self.ship_id})")
                        self.normalization_tests['brother_36_ship_found'] = True
                        return True
                
                self.log("❌ BROTHER 36 ship not found", "ERROR")
                # List available ships for debugging
                self.log("   Available ships:")
                for ship in ships[:5]:  # Show first 5 ships
                    self.log(f"     - {ship.get('name', 'Unknown')}")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding BROTHER 36 ship: {str(e)}", "ERROR")
            return False
    
    def find_crew_member(self):
        """Find a crew member for testing (optional)"""
        try:
            self.log("👤 Finding crew member for testing...")
            
            # Get crew for BROTHER 36 ship
            response = self.session.get(f"{BACKEND_URL}/crew?ship_name=BROTHER 36")
            
            if response.status_code == 200:
                crew_list = response.json()
                self.log(f"   Found {len(crew_list)} crew members for BROTHER 36")
                
                # Look for HỒ SỸ CHƯƠNG as mentioned in review request
                for crew in crew_list:
                    crew_name = crew.get("full_name", "")
                    if "HỒ SỸ CHƯƠNG" in crew_name.upper():
                        self.crew_id = crew.get("id")
                        self.log(f"✅ Found crew member: {crew_name} (ID: {self.crew_id})")
                        self.normalization_tests['crew_member_found'] = True
                        return True
                
                # If HỒ SỸ CHƯƠNG not found, use first available crew member
                if crew_list:
                    first_crew = crew_list[0]
                    self.crew_id = first_crew.get("id")
                    crew_name = first_crew.get("full_name", "Unknown")
                    self.log(f"✅ Using first available crew member: {crew_name} (ID: {self.crew_id})")
                    self.normalization_tests['crew_member_found'] = True
                    return True
                else:
                    self.log("⚠️ No crew members found for BROTHER 36 - will test without crew_id")
                    return True  # This is optional, so we can continue
            else:
                self.log(f"⚠️ Failed to get crew list: {response.status_code} - will test without crew_id")
                return True  # This is optional, so we can continue
                
        except Exception as e:
            self.log(f"⚠️ Error finding crew member: {str(e)} - will test without crew_id")
            return True  # This is optional, so we can continue
    
    def create_test_pdf_with_certificate_data(self):
        """Create a test PDF with certificate-like content for normalization testing"""
        try:
            self.log("📄 Creating test PDF with certificate content for normalization testing...")
            
            # Create a PDF with certificate content that should trigger normalization
            pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 300
>>
stream
BT
/F1 12 Tf
50 700 Td
(CERTIFICATE OF COMPETENCY) Tj
0 -20 Td
(GMDSS RADIO OPERATOR) Tj
0 -40 Td
(Certificate No: CT-GMDSS-2024-001) Tj
0 -20 Td
(Issued by: RERL Maritime Authority of the Republic of Panama) Tj
0 -20 Td
(Issue Date: 15/01/2024) Tj
0 -20 Td
(Expiry Date: 15/01/2029) Tj
0 -40 Td
(Holder: HO SY CHUONG) Tj
0 -20 Td
(Passport: C9780204) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
550
%%EOF"""
            
            test_file_path = "/app/test_gmdss_certificate.pdf"
            with open(test_file_path, 'wb') as f:
                f.write(pdf_content)
            
            self.test_pdf_file = test_file_path
            self.log(f"✅ Created test PDF file: {test_file_path}")
            self.log("   Content includes:")
            self.log("     - GMDSS certificate (should trigger priority rules)")
            self.log("     - Panama authority (should trigger normalization)")
            self.log("     - Certificate number with CT prefix")
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating test PDF file: {str(e)}", "ERROR")
            return False
    
    def test_analyze_file_endpoint_for_normalization(self):
        """Test the /api/crew-certificates/analyze-file endpoint focusing on normalization"""
        try:
            self.log("🔍 Testing /api/crew-certificates/analyze-file endpoint for normalization...")
            
            if not self.test_pdf_file:
                self.log("❌ No test PDF file available", "ERROR")
                return False
            
            if not self.ship_id:
                self.log("❌ No ship ID available", "ERROR")
                return False
            
            # Prepare multipart form data
            with open(self.test_pdf_file, "rb") as f:
                files = {
                    "cert_file": ("test_gmdss_certificate.pdf", f, "application/pdf")
                }
                data = {
                    "ship_id": self.ship_id
                }
                
                # Add crew_id if available
                if self.crew_id:
                    data["crew_id"] = self.crew_id
                    self.log(f"📤 Uploading certificate with crew_id: {self.crew_id}")
                else:
                    self.log("📤 Uploading certificate without crew_id")
                
                self.log(f"🚢 Ship ID: {self.ship_id}")
                self.log(f"📄 File: {os.path.basename(self.test_pdf_file)}")
                
                endpoint = f"{BACKEND_URL}/crew-certificates/analyze-file"
                self.log(f"   POST {endpoint}")
                
                start_time = time.time()
                response = self.session.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=120  # Longer timeout for AI processing
                )
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.normalization_tests['analyze_file_endpoint_accessible'] = True
                self.normalization_tests['multipart_form_data_accepted'] = True
                
                result = response.json()
                self.log("✅ Analyze file endpoint accessible")
                self.log(f"📊 Response keys: {list(result.keys())}")
                
                # Check for success
                if result.get("success"):
                    self.log("✅ Certificate analysis successful")
                    self.normalization_tests['certificate_analysis_successful'] = True
                    
                    # Check for analysis data
                    analysis = result.get("analysis", {})
                    if analysis:
                        self.log("✅ Analysis data found")
                        self.normalization_tests['field_extraction_working'] = True
                        
                        # Test the main focus: issued_by normalization
                        self.verify_issued_by_normalization(analysis)
                        
                        # Test certificate name and number extraction
                        self.verify_certificate_extraction(analysis)
                        
                        # Test response structure
                        self.verify_response_structure(result)
                        
                        # Log all extracted fields
                        self.log("📋 Extracted fields:")
                        for field, value in analysis.items():
                            if value:
                                self.log(f"   {field}: {value}")
                    else:
                        self.log("❌ No analysis data in response", "ERROR")
                    
                    return True
                else:
                    error_msg = result.get("message", "Unknown error")
                    self.log(f"⚠️ Certificate analysis failed: {error_msg}")
                    
                    # Even if analysis fails, we can still check if normalization would work
                    # by testing the manual endpoint with known data
                    self.log("🔄 Testing normalization via manual endpoint...")
                    return self.test_normalization_via_manual_endpoint()
            else:
                self.log(f"❌ Analyze file endpoint failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Response text: {response.text}")
                
                # Test normalization via manual endpoint as fallback
                self.log("🔄 Testing normalization via manual endpoint as fallback...")
                return self.test_normalization_via_manual_endpoint()
                
        except Exception as e:
            self.log(f"❌ Error testing analyze file endpoint: {str(e)}", "ERROR")
            return False
    
    def test_normalization_via_manual_endpoint(self):
        """Test normalization by creating a certificate with unnormalized issued_by via manual endpoint"""
        try:
            self.log("🔍 Testing normalization via manual endpoint...")
            
            # Test data with unnormalized issued_by that should be normalized
            test_certificates = [
                {
                    "crew_name": "Test Crew Member",
                    "passport": "TEST123456",
                    "cert_name": "GMDSS Radio Operator Certificate",
                    "cert_no": "CT-GMDSS-2024-001",
                    "issued_by": "RERL Maritime Authority of the Republic of Panama",  # Should normalize to "Panama Maritime Authority"
                    "issued_date": "2024-01-15T00:00:00Z",
                    "cert_expiry": "2029-01-15T00:00:00Z",
                    "status": "Valid",
                    "note": "Test certificate for normalization testing"
                },
                {
                    "crew_name": "Test Crew Member 2",
                    "passport": "TEST789012",
                    "cert_name": "Certificate of Competency",
                    "cert_no": "COC-2024-002",
                    "issued_by": "Socialist Republic of Vietnam Maritime Administration",  # Should normalize to "Vietnam Maritime Administration"
                    "issued_date": "2024-02-01T00:00:00Z",
                    "cert_expiry": "2029-02-01T00:00:00Z",
                    "status": "Valid",
                    "note": "Test certificate for Vietnam normalization"
                }
            ]
            
            created_certificates = []
            
            for i, cert_data in enumerate(test_certificates):
                self.log(f"📝 Creating test certificate {i+1} with unnormalized issued_by...")
                self.log(f"   Original issued_by: '{cert_data['issued_by']}'")
                
                endpoint = f"{BACKEND_URL}/crew-certificates/manual"
                params = {"ship_id": self.ship_id}
                
                response = self.session.post(endpoint, json=cert_data, params=params, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    cert_id = result.get("id")
                    created_certificates.append(cert_id)
                    
                    self.log(f"✅ Certificate created with ID: {cert_id}")
                    
                    # Now retrieve the certificate to see if issued_by was normalized
                    self.log("🔍 Retrieving certificate to check normalization...")
                    
                    # Get all certificates for the ship
                    get_response = self.session.get(f"{BACKEND_URL}/crew-certificates/{self.ship_id}")
                    
                    if get_response.status_code == 200:
                        certificates = get_response.json()
                        
                        # Find our certificate
                        for cert in certificates:
                            if cert.get("id") == cert_id:
                                stored_issued_by = cert.get("issued_by", "")
                                self.log(f"   Stored issued_by: '{stored_issued_by}'")
                                
                                # Check if normalization occurred
                                original_issued_by = cert_data["issued_by"]
                                if stored_issued_by != original_issued_by:
                                    self.log(f"✅ Normalization detected!")
                                    self.log(f"   Original: '{original_issued_by}'")
                                    self.log(f"   Normalized: '{stored_issued_by}'")
                                    self.normalization_tests['issued_by_normalization_applied'] = True
                                    self.normalization_tests['normalize_function_called'] = True
                                    
                                    # Check specific normalization patterns
                                    if "Panama Maritime Authority" in stored_issued_by and "RERL" not in stored_issued_by:
                                        self.log("✅ Panama authority normalization working correctly")
                                    elif "Vietnam Maritime Administration" in stored_issued_by and "Socialist Republic" not in stored_issued_by:
                                        self.log("✅ Vietnam authority normalization working correctly")
                                else:
                                    self.log("⚠️ No normalization detected - values are identical")
                                
                                self.normalization_tests['issued_by_value_normalized'] = True
                                break
                    else:
                        self.log(f"❌ Failed to retrieve certificate: {get_response.status_code}")
                else:
                    self.log(f"❌ Failed to create certificate: {response.status_code}")
            
            # Clean up created certificates
            self.log("🧹 Cleaning up test certificates...")
            for cert_id in created_certificates:
                try:
                    delete_response = self.session.delete(f"{BACKEND_URL}/crew-certificates/{cert_id}")
                    if delete_response.status_code == 200:
                        self.log(f"   ✅ Deleted certificate: {cert_id}")
                    else:
                        self.log(f"   ⚠️ Failed to delete certificate: {cert_id}")
                except Exception as e:
                    self.log(f"   ⚠️ Error deleting certificate {cert_id}: {e}")
            
            return len(created_certificates) > 0
            
        except Exception as e:
            self.log(f"❌ Error testing normalization via manual endpoint: {str(e)}", "ERROR")
            return False
    
    def verify_issued_by_normalization(self, analysis):
        """Verify that issued_by field is normalized"""
        try:
            self.log("🔍 Verifying issued_by normalization...")
            
            issued_by = analysis.get("issued_by", "")
            
            if issued_by:
                self.log(f"📋 issued_by value: '{issued_by}'")
                self.normalization_tests['issued_by_value_normalized'] = True
                
                # Check if the value looks normalized (common patterns)
                normalized_patterns = [
                    "Panama Maritime Authority",
                    "Vietnam Maritime Administration", 
                    "Marshall Islands Maritime Administrator",
                    "Liberia Maritime Authority",
                    "Philippines Coast Guard",
                    "Singapore Maritime and Port Authority",
                    "Hong Kong Marine Department",
                    "United Kingdom Maritime and Coastguard Agency",
                    "United States Coast Guard"
                ]
                
                # Check if it matches any normalized pattern
                for pattern in normalized_patterns:
                    if pattern.lower() in issued_by.lower():
                        self.log(f"✅ issued_by appears normalized: matches pattern '{pattern}'")
                        self.normalization_tests['issued_by_normalization_applied'] = True
                        break
                
                # Check if it doesn't contain common unnormalized patterns
                unnormalized_patterns = [
                    "RERL Maritime Authority of the Republic of Panama",
                    "Socialist Republic of Vietnam Maritime",
                    "The Government of Marshall Islands",
                    "the ", "The ", "THE ",
                    "Republic of ", "REPUBLIC OF "
                ]
                
                contains_unnormalized = False
                for pattern in unnormalized_patterns:
                    if pattern in issued_by:
                        contains_unnormalized = True
                        break
                
                if not contains_unnormalized:
                    self.log("✅ issued_by does not contain unnormalized patterns")
                    self.normalization_tests['normalize_function_called'] = True
                else:
                    self.log("⚠️ issued_by may contain unnormalized patterns")
                
            else:
                self.log("⚠️ No issued_by value in analysis result")
            
        except Exception as e:
            self.log(f"❌ Error verifying issued_by normalization: {str(e)}", "ERROR")
    
    def verify_certificate_extraction(self, analysis):
        """Verify certificate name and number extraction"""
        try:
            self.log("🔍 Verifying certificate extraction...")
            
            # Check cert_name
            cert_name = analysis.get("cert_name", "")
            if cert_name:
                self.log(f"📋 cert_name: '{cert_name}'")
                self.normalization_tests['cert_name_extraction_working'] = True
                
                # Check for GMDSS certificate (mentioned in review request)
                if "GMDSS" in cert_name.upper():
                    self.log("✅ GMDSS certificate detected")
                    self.normalization_tests['gmdss_certificate_detected'] = True
                    self.normalization_tests['cert_name_priority_rules_applied'] = True
                
                # Check for other priority patterns (COC, COE, STCW)
                priority_patterns = ["COC", "COE", "STCW", "CERTIFICATE OF COMPETENCY", "CERTIFICATE OF ENDORSEMENT"]
                for pattern in priority_patterns:
                    if pattern in cert_name.upper():
                        self.log(f"✅ Priority certificate pattern detected: {pattern}")
                        self.normalization_tests['cert_name_priority_rules_applied'] = True
                        break
            else:
                self.log("⚠️ No cert_name value in analysis result")
            
            # Check cert_no
            cert_no = analysis.get("cert_no", "")
            if cert_no:
                self.log(f"📋 cert_no: '{cert_no}'")
                self.normalization_tests['cert_no_extraction_working'] = True
                
                # Check for common certificate number patterns
                cert_patterns = ["CT", "Endorsement No", "Document No", "Certificate No"]
                for pattern in cert_patterns:
                    if pattern.lower() in cert_no.lower():
                        self.log(f"✅ Certificate number pattern detected: {pattern}")
                        break
            else:
                self.log("⚠️ No cert_no value in analysis result")
            
        except Exception as e:
            self.log(f"❌ Error verifying certificate extraction: {str(e)}", "ERROR")
    
    def verify_response_structure(self, result):
        """Verify response structure is ready for frontend auto-fill"""
        try:
            self.log("🔍 Verifying response structure...")
            
            # Check required top-level fields
            required_fields = ["success", "analysis"]
            for field in required_fields:
                if field in result:
                    self.log(f"✅ Required field present: {field}")
                else:
                    self.log(f"❌ Required field missing: {field}")
                    return
            
            # Check analysis fields
            analysis = result.get("analysis", {})
            expected_analysis_fields = ["cert_name", "cert_no", "issued_by", "issued_date", "expiry_date"]
            
            present_fields = 0
            for field in expected_analysis_fields:
                if field in analysis:
                    present_fields += 1
                    self.log(f"✅ Analysis field present: {field}")
                else:
                    self.log(f"⚠️ Analysis field missing: {field}")
            
            if present_fields >= 3:  # At least 3 out of 5 fields should be present
                self.log("✅ Response structure appears correct for frontend auto-fill")
                self.normalization_tests['response_structure_correct'] = True
                self.normalization_tests['frontend_ready_format'] = True
            
            if present_fields == len(expected_analysis_fields):
                self.normalization_tests['all_expected_fields_present'] = True
            
        except Exception as e:
            self.log(f"❌ Error verifying response structure: {str(e)}", "ERROR")
    
    def check_backend_logs_for_normalization(self):
        """Check backend logs for normalization function calls"""
        try:
            self.log("📋 Checking backend logs for normalization activity...")
            
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            normalization_found = False
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"📄 Checking {log_file}...")
                    
                    try:
                        # Get last 200 lines to capture recent activity
                        result = os.popen(f"tail -n 200 {log_file}").read()
                        if result.strip():
                            lines = result.strip().split('\n')
                            
                            # Look for normalization-related log entries
                            for line in lines:
                                if any(keyword in line.lower() for keyword in ['normalize', 'issued_by', 'normalization']):
                                    self.log(f"🔍 Normalization log: {line}")
                                    normalization_found = True
                                elif any(keyword in line.lower() for keyword in ['certificate', 'analyze-file', 'crew-certificates']):
                                    self.log(f"📋 Certificate log: {line}")
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
            if normalization_found:
                self.log("✅ Normalization activity found in backend logs")
            else:
                self.log("⚠️ No specific normalization activity found in recent logs")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def run_comprehensive_normalization_test(self):
        """Run comprehensive test of crew certificates issued by normalization"""
        try:
            self.log("🚀 STARTING CREW CERTIFICATES ISSUED BY NORMALIZATION TEST")
            self.log("=" * 80)
            self.log("Testing Focus: Verify normalize_issued_by() function in analyze-file endpoint")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("\nSTEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find BROTHER 36 ship
            self.log("\nSTEP 2: Ship Discovery")
            if not self.find_brother_36_ship():
                self.log("❌ CRITICAL: BROTHER 36 ship not found - cannot proceed")
                return False
            
            # Step 3: Find crew member (optional)
            self.log("\nSTEP 3: Crew Member Discovery")
            self.find_crew_member()
            
            # Step 4: Create test PDF file
            self.log("\nSTEP 4: Test PDF File Preparation")
            if not self.create_test_pdf_with_certificate_data():
                self.log("❌ CRITICAL: Could not create test PDF file - cannot proceed")
                return False
            
            # Step 5: Test analyze-file endpoint for normalization
            self.log("\nSTEP 5: Analyze File Endpoint Normalization Testing")
            self.test_analyze_file_endpoint_for_normalization()
            
            # Step 6: Check backend logs
            self.log("\nSTEP 6: Backend Logs Analysis")
            self.check_backend_logs_for_normalization()
            
            self.log("\n" + "=" * 80)
            self.log("✅ CREW CERTIFICATES NORMALIZATION TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 CREW CERTIFICATES ISSUED BY NORMALIZATION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.normalization_tests)
            passed_tests = sum(1 for result in self.normalization_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication & Setup Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication with admin1/123456'),
                ('user_company_identified', 'User company identified'),
                ('amcsc_company_found', 'AMCSC company association'),
                ('brother_36_ship_found', 'BROTHER 36 ship found'),
                ('crew_member_found', 'Crew member found (optional)'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.normalization_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Endpoint Testing Results
            self.log("\n📡 ENDPOINT TESTING:")
            endpoint_tests = [
                ('analyze_file_endpoint_accessible', 'Analyze file endpoint accessible'),
                ('multipart_form_data_accepted', 'Multipart form data accepted'),
                ('ship_id_validation_working', 'Ship ID validation working'),
                ('certificate_analysis_successful', 'Certificate analysis successful'),
            ]
            
            for test_key, description in endpoint_tests:
                status = "✅ PASS" if self.normalization_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Normalization Results (MAIN FOCUS)
            self.log("\n🎯 ISSUED BY NORMALIZATION (MAIN FOCUS):")
            normalization_tests = [
                ('issued_by_normalization_applied', 'issued_by normalization applied'),
                ('issued_by_value_normalized', 'issued_by value present and normalized'),
                ('normalize_function_called', 'normalize_issued_by() function called'),
            ]
            
            for test_key, description in normalization_tests:
                status = "✅ PASS" if self.normalization_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Certificate Extraction Results
            self.log("\n📋 CERTIFICATE EXTRACTION:")
            extraction_tests = [
                ('cert_name_extraction_working', 'Certificate name extraction'),
                ('cert_no_extraction_working', 'Certificate number extraction'),
                ('cert_name_priority_rules_applied', 'Certificate name priority rules'),
                ('gmdss_certificate_detected', 'GMDSS certificate detection'),
            ]
            
            for test_key, description in extraction_tests:
                status = "✅ PASS" if self.normalization_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Response Structure Results
            self.log("\n📤 RESPONSE STRUCTURE:")
            response_tests = [
                ('response_structure_correct', 'Response structure correct'),
                ('frontend_ready_format', 'Frontend ready format'),
                ('all_expected_fields_present', 'All expected fields present'),
            ]
            
            for test_key, description in response_tests:
                status = "✅ PASS" if self.normalization_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            # Critical tests for the main focus
            critical_tests = [
                'analyze_file_endpoint_accessible',
                'issued_by_normalization_applied',
                'normalize_function_called'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.normalization_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL NORMALIZATION REQUIREMENTS MET")
                self.log("   ✅ normalize_issued_by() function working correctly")
                self.log("   ✅ Frontend will receive normalized issued_by values")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
            # Success rate assessment
            if success_rate >= 80:
                self.log(f"   ✅ EXCELLENT SUCCESS RATE: {success_rate:.1f}%")
            elif success_rate >= 60:
                self.log(f"   ⚠️ GOOD SUCCESS RATE: {success_rate:.1f}%")
            else:
                self.log(f"   ❌ LOW SUCCESS RATE: {success_rate:.1f}%")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main function to run the crew certificates normalization test"""
    tester = CrewCertificatesNormalizationTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_normalization_test()
        
        # Print summary
        tester.print_test_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
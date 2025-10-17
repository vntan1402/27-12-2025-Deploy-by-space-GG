#!/usr/bin/env python3
"""
Date of Birth AI Extraction and Validation Testing
Testing the new DOB validation functionality for crew certificates

REVIEW REQUEST REQUIREMENTS:
Test the Date of Birth extraction and validation for crew certificates:

1. AI Extraction Verification - Upload certificate and verify AI extracts date_of_birth field
2. DOB Match Scenario - Test matching DOB between crew and certificate
3. DOB Mismatch Scenario - Test mismatch detection and error response
4. Bypass DOB Validation - Test bypass parameter functionality
5. Skip DOB Validation (No Crew DOB) - Test when crew has no DOB
6. Skip DOB Validation (AI Didn't Extract) - Test when AI can't extract DOB

Test Credentials: admin1/123456
Test Ships: BROTHER 36, MINH ANH 09
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
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break
    print(f"Using external backend URL: {BACKEND_URL}")

class DOBValidationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for DOB validation functionality
        self.dob_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_company_identified': False,
            'test_ships_found': False,
            'test_crew_found': False,
            
            # AI Extraction Verification
            'ai_extraction_endpoint_accessible': False,
            'ai_extracts_dob_field': False,
            'dob_format_yyyy_mm_dd': False,
            'backend_logs_show_dob_extraction': False,
            
            # DOB Match Scenario
            'dob_match_returns_200': False,
            'dob_match_logs_success': False,
            'dob_match_includes_certificate_fields': False,
            
            # DOB Mismatch Scenario
            'dob_mismatch_returns_400': False,
            'dob_mismatch_error_code_correct': False,
            'dob_mismatch_includes_comparison_data': False,
            'dob_mismatch_logs_error': False,
            
            # Bypass DOB Validation
            'bypass_parameter_works': False,
            'bypass_returns_200_on_mismatch': False,
            'bypass_logs_warning': False,
            'bypass_completes_analysis': False,
            
            # Skip DOB Validation (No Crew DOB)
            'skip_validation_no_crew_dob': False,
            'skip_no_crew_dob_returns_200': False,
            'skip_no_crew_dob_logs_warning': False,
            
            # Skip DOB Validation (AI Didn't Extract)
            'skip_validation_no_ai_extraction': False,
            'skip_no_ai_extraction_returns_200': False,
            'skip_no_ai_extraction_logs_warning': False,
        }
        
        # Store test data
        self.test_ships = []
        self.test_crew_with_dob = None
        self.test_crew_without_dob = None
        
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
                
                self.dob_tests['authentication_successful'] = True
                self.dob_tests['user_company_identified'] = bool(self.current_user.get('company'))
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_test_ships(self):
        """Find test ships BROTHER 36 and MINH ANH 09"""
        try:
            self.log("🚢 Finding test ships: BROTHER 36, MINH ANH 09...")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                target_ships = ["BROTHER 36", "MINH ANH 09"]
                
                for ship in ships:
                    if ship.get("name") in target_ships:
                        self.test_ships.append(ship)
                        self.log(f"✅ Found ship: {ship.get('name')} (ID: {ship.get('id')})")
                
                if len(self.test_ships) >= 1:
                    self.dob_tests['test_ships_found'] = True
                    return True
                else:
                    self.log("❌ No test ships found", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding test ships: {str(e)}", "ERROR")
            return False
    
    def find_test_crew(self):
        """Find crew members for testing - one with DOB and one without"""
        try:
            self.log("👥 Finding crew members for testing...")
            
            response = self.session.get(f"{BACKEND_URL}/crew")
            
            if response.status_code == 200:
                crew_list = response.json()
                self.log(f"   Found {len(crew_list)} crew members")
                
                # Look for crew with and without date_of_birth
                for crew in crew_list:
                    dob = crew.get("date_of_birth")
                    crew_name = crew.get("full_name", "Unknown")
                    
                    if dob and not self.test_crew_with_dob:
                        self.test_crew_with_dob = crew
                        self.log(f"✅ Found crew WITH DOB: {crew_name} (DOB: {dob})")
                    elif not dob and not self.test_crew_without_dob:
                        self.test_crew_without_dob = crew
                        self.log(f"✅ Found crew WITHOUT DOB: {crew_name}")
                
                if self.test_crew_with_dob or self.test_crew_without_dob:
                    self.dob_tests['test_crew_found'] = True
                    return True
                else:
                    self.log("❌ No suitable crew members found", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get crew list: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding test crew: {str(e)}", "ERROR")
            return False
    
    def create_test_certificate_file(self, holder_name, date_of_birth=None):
        """Create a test certificate file with specified holder name and DOB"""
        try:
            # Create a simple text file that mimics a certificate
            certificate_content = f"""
CERTIFICATE OF COMPETENCY

This is to certify that {holder_name}
has been found competent to perform duties as specified.

Certificate Number: COC-TEST-{int(time.time())}
Issued By: Test Maritime Authority
Issue Date: {datetime.now().strftime('%d/%m/%Y')}
Expiry Date: {(datetime.now() + timedelta(days=365*5)).strftime('%d/%m/%Y')}
"""
            
            if date_of_birth:
                certificate_content += f"\nDate of Birth: {date_of_birth}\n"
            
            certificate_content += """
This certificate is valid for all vessels.

Signed: Test Authority
Date: """ + datetime.now().strftime('%d/%m/%Y')
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.write(certificate_content)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Error creating test certificate: {str(e)}", "ERROR")
            return None
    
    def test_ai_extraction_verification(self):
        """Test 1: AI Extraction Verification"""
        try:
            self.log("📄 TEST 1: AI Extraction Verification")
            self.log("   Testing AI extraction of date_of_birth field from certificate...")
            
            if not self.test_ships or not self.test_crew_with_dob:
                self.log("❌ Missing test data", "ERROR")
                return False
            
            ship = self.test_ships[0]
            crew = self.test_crew_with_dob
            
            # Create test certificate with DOB
            test_dob = "15/08/1985"
            holder_name = crew.get("full_name", "TEST HOLDER")
            cert_file = self.create_test_certificate_file(holder_name, test_dob)
            
            if not cert_file:
                return False
            
            try:
                # Upload certificate for analysis
                with open(cert_file, "rb") as f:
                    files = {
                        "cert_file": ("test_certificate.txt", f, "text/plain")
                    }
                    data = {
                        "ship_id": ship.get("id"),
                        "crew_id": crew.get("id")
                    }
                    
                    endpoint = f"{BACKEND_URL}/crew-certificates/analyze-file"
                    self.log(f"   POST {endpoint}")
                    
                    start_time = time.time()
                    response = self.session.post(
                        endpoint,
                        files=files,
                        data=data,
                        timeout=120
                    )
                    end_time = time.time()
                    
                    processing_time = end_time - start_time
                    self.log(f"⏱️ Processing time: {processing_time:.1f} seconds")
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.dob_tests['ai_extraction_endpoint_accessible'] = True
                    self.log("✅ AI extraction endpoint accessible")
                    
                    try:
                        result = response.json()
                        
                        # Check if AI extracted date_of_birth
                        extracted_dob = result.get("date_of_birth")
                        if extracted_dob:
                            self.log(f"✅ AI extracted date_of_birth: {extracted_dob}")
                            self.dob_tests['ai_extracts_dob_field'] = True
                            
                            # Check format (should be YYYY-MM-DD)
                            if re.match(r'\d{4}-\d{2}-\d{2}', extracted_dob):
                                self.log("✅ DOB format is YYYY-MM-DD")
                                self.dob_tests['dob_format_yyyy_mm_dd'] = True
                        else:
                            self.log("⚠️ AI did not extract date_of_birth field")
                        
                        # Check backend logs
                        self.check_backend_logs_for_dob()
                        
                        return True
                        
                    except json.JSONDecodeError as e:
                        self.log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                        return False
                else:
                    self.log(f"❌ AI extraction failed: {response.status_code}", "ERROR")
                    self.log(f"   Response: {response.text}")
                    return False
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(cert_file)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Error in AI extraction test: {str(e)}", "ERROR")
            return False
    
    def test_dob_match_scenario(self):
        """Test 2: DOB Match Scenario"""
        try:
            self.log("✅ TEST 2: DOB Match Scenario")
            self.log("   Testing matching DOB between crew and certificate...")
            
            if not self.test_ships or not self.test_crew_with_dob:
                self.log("❌ Missing test data", "ERROR")
                return False
            
            ship = self.test_ships[0]
            crew = self.test_crew_with_dob
            
            # Get crew's actual DOB and use it in certificate
            crew_dob = crew.get("date_of_birth", "")
            if isinstance(crew_dob, str) and "T" in crew_dob:
                crew_dob_date = crew_dob.split("T")[0]  # Extract date part
            else:
                crew_dob_date = "15/08/1985"  # Fallback
            
            # Convert to DD/MM/YYYY format for certificate
            try:
                if "-" in crew_dob_date:
                    # Convert YYYY-MM-DD to DD/MM/YYYY
                    parts = crew_dob_date.split("-")
                    cert_dob = f"{parts[2]}/{parts[1]}/{parts[0]}"
                else:
                    cert_dob = crew_dob_date
            except:
                cert_dob = "15/08/1985"
            
            holder_name = crew.get("full_name", "TEST HOLDER")
            cert_file = self.create_test_certificate_file(holder_name, cert_dob)
            
            if not cert_file:
                return False
            
            try:
                # Upload certificate for analysis
                with open(cert_file, "rb") as f:
                    files = {
                        "cert_file": ("test_certificate.txt", f, "text/plain")
                    }
                    data = {
                        "ship_id": ship.get("id"),
                        "crew_id": crew.get("id")
                    }
                    
                    endpoint = f"{BACKEND_URL}/crew-certificates/analyze-file"
                    response = self.session.post(
                        endpoint,
                        files=files,
                        data=data,
                        timeout=120
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.dob_tests['dob_match_returns_200'] = True
                    self.log("✅ DOB match returns 200 success")
                    
                    try:
                        result = response.json()
                        
                        # Check if response includes certificate fields
                        if result.get("cert_name") or result.get("cert_no"):
                            self.log("✅ Response includes certificate fields")
                            self.dob_tests['dob_match_includes_certificate_fields'] = True
                        
                        # Check backend logs for success message
                        self.check_backend_logs_for_dob_match()
                        
                        return True
                        
                    except json.JSONDecodeError as e:
                        self.log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                        return False
                else:
                    self.log(f"❌ DOB match test failed: {response.status_code}", "ERROR")
                    self.log(f"   Response: {response.text}")
                    return False
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(cert_file)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Error in DOB match test: {str(e)}", "ERROR")
            return False
    
    def test_dob_mismatch_scenario(self):
        """Test 3: DOB Mismatch Scenario"""
        try:
            self.log("❌ TEST 3: DOB Mismatch Scenario")
            self.log("   Testing DOB mismatch detection and error response...")
            
            if not self.test_ships or not self.test_crew_with_dob:
                self.log("❌ Missing test data", "ERROR")
                return False
            
            ship = self.test_ships[0]
            crew = self.test_crew_with_dob
            
            # Use a different DOB that doesn't match crew's DOB
            mismatch_dob = "01/01/1990"  # Different from crew's actual DOB
            holder_name = crew.get("full_name", "TEST HOLDER")
            cert_file = self.create_test_certificate_file(holder_name, mismatch_dob)
            
            if not cert_file:
                return False
            
            try:
                # Upload certificate for analysis
                with open(cert_file, "rb") as f:
                    files = {
                        "cert_file": ("test_certificate.txt", f, "text/plain")
                    }
                    data = {
                        "ship_id": ship.get("id"),
                        "crew_id": crew.get("id")
                    }
                    
                    endpoint = f"{BACKEND_URL}/crew-certificates/analyze-file"
                    response = self.session.post(
                        endpoint,
                        files=files,
                        data=data,
                        timeout=120
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 400:
                    self.dob_tests['dob_mismatch_returns_400'] = True
                    self.log("✅ DOB mismatch returns 400 Bad Request")
                    
                    try:
                        result = response.json()
                        
                        # Check error code
                        error_code = result.get("error")
                        if error_code == "DATE_OF_BIRTH_MISMATCH":
                            self.log("✅ Error code is DATE_OF_BIRTH_MISMATCH")
                            self.dob_tests['dob_mismatch_error_code_correct'] = True
                        
                        # Check comparison data
                        ai_extracted_dob = result.get("ai_extracted_dob")
                        crew_dob = result.get("crew_dob")
                        crew_name = result.get("crew_name")
                        
                        if ai_extracted_dob and crew_dob and crew_name:
                            self.log("✅ Response includes comparison data")
                            self.log(f"   AI extracted DOB: {ai_extracted_dob}")
                            self.log(f"   Crew DOB: {crew_dob}")
                            self.log(f"   Crew name: {crew_name}")
                            self.dob_tests['dob_mismatch_includes_comparison_data'] = True
                        
                        # Check backend logs for mismatch message
                        self.check_backend_logs_for_dob_mismatch()
                        
                        return True
                        
                    except json.JSONDecodeError as e:
                        self.log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                        return False
                else:
                    self.log(f"❌ Expected 400 for DOB mismatch, got: {response.status_code}", "ERROR")
                    self.log(f"   Response: {response.text}")
                    return False
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(cert_file)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Error in DOB mismatch test: {str(e)}", "ERROR")
            return False
    
    def test_bypass_dob_validation(self):
        """Test 4: Bypass DOB Validation"""
        try:
            self.log("⚠️ TEST 4: Bypass DOB Validation")
            self.log("   Testing bypass_dob_validation=true parameter...")
            
            if not self.test_ships or not self.test_crew_with_dob:
                self.log("❌ Missing test data", "ERROR")
                return False
            
            ship = self.test_ships[0]
            crew = self.test_crew_with_dob
            
            # Use a different DOB that doesn't match crew's DOB
            mismatch_dob = "01/01/1990"
            holder_name = crew.get("full_name", "TEST HOLDER")
            cert_file = self.create_test_certificate_file(holder_name, mismatch_dob)
            
            if not cert_file:
                return False
            
            try:
                # Upload certificate with bypass parameter
                with open(cert_file, "rb") as f:
                    files = {
                        "cert_file": ("test_certificate.txt", f, "text/plain")
                    }
                    data = {
                        "ship_id": ship.get("id"),
                        "crew_id": crew.get("id"),
                        "bypass_dob_validation": "true"  # Bypass parameter
                    }
                    
                    endpoint = f"{BACKEND_URL}/crew-certificates/analyze-file"
                    response = self.session.post(
                        endpoint,
                        files=files,
                        data=data,
                        timeout=120
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.dob_tests['bypass_parameter_works'] = True
                    self.dob_tests['bypass_returns_200_on_mismatch'] = True
                    self.log("✅ Bypass parameter works - returns 200 on mismatch")
                    
                    try:
                        result = response.json()
                        
                        # Check if certificate analysis completed
                        if result.get("cert_name") or result.get("cert_no"):
                            self.log("✅ Certificate analysis completed successfully")
                            self.dob_tests['bypass_completes_analysis'] = True
                        
                        # Check backend logs for bypass warning
                        self.check_backend_logs_for_bypass()
                        
                        return True
                        
                    except json.JSONDecodeError as e:
                        self.log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                        return False
                else:
                    self.log(f"❌ Bypass test failed: {response.status_code}", "ERROR")
                    self.log(f"   Response: {response.text}")
                    return False
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(cert_file)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Error in bypass DOB validation test: {str(e)}", "ERROR")
            return False
    
    def test_skip_dob_validation_no_crew_dob(self):
        """Test 5: Skip DOB Validation (No Crew DOB)"""
        try:
            self.log("⚠️ TEST 5: Skip DOB Validation (No Crew DOB)")
            self.log("   Testing validation skip when crew has no date_of_birth...")
            
            if not self.test_ships or not self.test_crew_without_dob:
                self.log("❌ Missing test data - need crew without DOB", "ERROR")
                return False
            
            ship = self.test_ships[0]
            crew = self.test_crew_without_dob
            
            # Create certificate with DOB (but crew has no DOB to compare)
            cert_dob = "15/08/1985"
            holder_name = crew.get("full_name", "TEST HOLDER")
            cert_file = self.create_test_certificate_file(holder_name, cert_dob)
            
            if not cert_file:
                return False
            
            try:
                # Upload certificate for analysis
                with open(cert_file, "rb") as f:
                    files = {
                        "cert_file": ("test_certificate.txt", f, "text/plain")
                    }
                    data = {
                        "ship_id": ship.get("id"),
                        "crew_id": crew.get("id")
                    }
                    
                    endpoint = f"{BACKEND_URL}/crew-certificates/analyze-file"
                    response = self.session.post(
                        endpoint,
                        files=files,
                        data=data,
                        timeout=120
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.dob_tests['skip_validation_no_crew_dob'] = True
                    self.dob_tests['skip_no_crew_dob_returns_200'] = True
                    self.log("✅ Skip validation works - returns 200 when crew has no DOB")
                    
                    # Check backend logs for skip message
                    self.check_backend_logs_for_skip_no_crew_dob()
                    
                    return True
                else:
                    self.log(f"❌ Skip validation test failed: {response.status_code}", "ERROR")
                    self.log(f"   Response: {response.text}")
                    return False
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(cert_file)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Error in skip DOB validation (no crew DOB) test: {str(e)}", "ERROR")
            return False
    
    def test_skip_dob_validation_no_ai_extraction(self):
        """Test 6: Skip DOB Validation (AI Didn't Extract)"""
        try:
            self.log("⚠️ TEST 6: Skip DOB Validation (AI Didn't Extract)")
            self.log("   Testing validation skip when AI cannot extract DOB...")
            
            if not self.test_ships or not self.test_crew_with_dob:
                self.log("❌ Missing test data", "ERROR")
                return False
            
            ship = self.test_ships[0]
            crew = self.test_crew_with_dob
            
            # Create certificate WITHOUT DOB (so AI can't extract it)
            holder_name = crew.get("full_name", "TEST HOLDER")
            cert_file = self.create_test_certificate_file(holder_name, None)  # No DOB
            
            if not cert_file:
                return False
            
            try:
                # Upload certificate for analysis
                with open(cert_file, "rb") as f:
                    files = {
                        "cert_file": ("test_certificate.txt", f, "text/plain")
                    }
                    data = {
                        "ship_id": ship.get("id"),
                        "crew_id": crew.get("id")
                    }
                    
                    endpoint = f"{BACKEND_URL}/crew-certificates/analyze-file"
                    response = self.session.post(
                        endpoint,
                        files=files,
                        data=data,
                        timeout=120
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    self.dob_tests['skip_validation_no_ai_extraction'] = True
                    self.dob_tests['skip_no_ai_extraction_returns_200'] = True
                    self.log("✅ Skip validation works - returns 200 when AI didn't extract DOB")
                    
                    # Check backend logs for skip message
                    self.check_backend_logs_for_skip_no_ai_extraction()
                    
                    return True
                else:
                    self.log(f"❌ Skip validation test failed: {response.status_code}", "ERROR")
                    self.log(f"   Response: {response.text}")
                    return False
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(cert_file)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Error in skip DOB validation (no AI extraction) test: {str(e)}", "ERROR")
            return False
    
    def check_backend_logs_for_dob(self):
        """Check backend logs for DOB extraction messages"""
        try:
            self.log("📋 Checking backend logs for DOB extraction...")
            
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            dob_patterns = [
                "🎂 Date of Birth:",
                "NOT EXTRACTED",
                "date_of_birth"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        result = os.popen(f"tail -n 50 {log_file}").read()
                        for pattern in dob_patterns:
                            if pattern in result:
                                self.log(f"✅ Found DOB extraction log: {pattern}")
                                self.dob_tests['backend_logs_show_dob_extraction'] = True
                                break
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def check_backend_logs_for_dob_match(self):
        """Check backend logs for DOB match messages"""
        try:
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            match_patterns = [
                "✅ Date of Birth matches crew data",
                "DOB matches"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        result = os.popen(f"tail -n 50 {log_file}").read()
                        for pattern in match_patterns:
                            if pattern in result:
                                self.log(f"✅ Found DOB match log: {pattern}")
                                self.dob_tests['dob_match_logs_success'] = True
                                break
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def check_backend_logs_for_dob_mismatch(self):
        """Check backend logs for DOB mismatch messages"""
        try:
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            mismatch_patterns = [
                "❌ Date of Birth MISMATCH detected",
                "DOB MISMATCH"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        result = os.popen(f"tail -n 50 {log_file}").read()
                        for pattern in mismatch_patterns:
                            if pattern in result:
                                self.log(f"✅ Found DOB mismatch log: {pattern}")
                                self.dob_tests['dob_mismatch_logs_error'] = True
                                break
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def check_backend_logs_for_bypass(self):
        """Check backend logs for bypass messages"""
        try:
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            bypass_patterns = [
                "⚠️ DOB VALIDATION BYPASSED",
                "BYPASSED"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        result = os.popen(f"tail -n 50 {log_file}").read()
                        for pattern in bypass_patterns:
                            if pattern in result:
                                self.log(f"✅ Found bypass log: {pattern}")
                                self.dob_tests['bypass_logs_warning'] = True
                                break
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def check_backend_logs_for_skip_no_crew_dob(self):
        """Check backend logs for skip messages when crew has no DOB"""
        try:
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            skip_patterns = [
                "⚠️ Skipping DOB validation: Crew has no date of birth",
                "Skipping DOB validation"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        result = os.popen(f"tail -n 50 {log_file}").read()
                        for pattern in skip_patterns:
                            if pattern in result:
                                self.log(f"✅ Found skip log (no crew DOB): {pattern}")
                                self.dob_tests['skip_no_crew_dob_logs_warning'] = True
                                break
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def check_backend_logs_for_skip_no_ai_extraction(self):
        """Check backend logs for skip messages when AI didn't extract DOB"""
        try:
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            skip_patterns = [
                "⚠️ Skipping DOB validation: AI did not extract date of birth",
                "AI did not extract"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        result = os.popen(f"tail -n 50 {log_file}").read()
                        for pattern in skip_patterns:
                            if pattern in result:
                                self.log(f"✅ Found skip log (no AI extraction): {pattern}")
                                self.dob_tests['skip_no_ai_extraction_logs_warning'] = True
                                break
                    except Exception as e:
                        self.log(f"   Error reading {log_file}: {e}")
            
        except Exception as e:
            self.log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def run_comprehensive_dob_validation_test(self):
        """Run comprehensive test of DOB validation functionality"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE DOB VALIDATION TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Find test ships
            self.log("\nSTEP 2: Finding test ships")
            if not self.find_test_ships():
                self.log("❌ CRITICAL: Test ships not found - cannot proceed")
                return False
            
            # Step 3: Find test crew
            self.log("\nSTEP 3: Finding test crew")
            if not self.find_test_crew():
                self.log("❌ CRITICAL: Test crew not found - cannot proceed")
                return False
            
            # Step 4: Test AI extraction verification
            self.log("\nSTEP 4: AI Extraction Verification")
            self.test_ai_extraction_verification()
            
            # Step 5: Test DOB match scenario
            self.log("\nSTEP 5: DOB Match Scenario")
            self.test_dob_match_scenario()
            
            # Step 6: Test DOB mismatch scenario
            self.log("\nSTEP 6: DOB Mismatch Scenario")
            self.test_dob_mismatch_scenario()
            
            # Step 7: Test bypass DOB validation
            self.log("\nSTEP 7: Bypass DOB Validation")
            self.test_bypass_dob_validation()
            
            # Step 8: Test skip DOB validation (no crew DOB)
            self.log("\nSTEP 8: Skip DOB Validation (No Crew DOB)")
            self.test_skip_dob_validation_no_crew_dob()
            
            # Step 9: Test skip DOB validation (no AI extraction)
            self.log("\nSTEP 9: Skip DOB Validation (No AI Extraction)")
            self.test_skip_dob_validation_no_ai_extraction()
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE DOB VALIDATION TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 DOB VALIDATION TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.dob_tests)
            passed_tests = sum(1 for result in self.dob_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION & SETUP:")
            auth_tests = [
                ('authentication_successful', 'Authentication successful'),
                ('user_company_identified', 'User company identified'),
                ('test_ships_found', 'Test ships found'),
                ('test_crew_found', 'Test crew found'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.dob_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # AI Extraction Results
            self.log("\n📄 AI EXTRACTION VERIFICATION:")
            extraction_tests = [
                ('ai_extraction_endpoint_accessible', 'Endpoint accessible'),
                ('ai_extracts_dob_field', 'AI extracts DOB field'),
                ('dob_format_yyyy_mm_dd', 'DOB format YYYY-MM-DD'),
                ('backend_logs_show_dob_extraction', 'Backend logs show extraction'),
            ]
            
            for test_key, description in extraction_tests:
                status = "✅ PASS" if self.dob_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # DOB Match Results
            self.log("\n✅ DOB MATCH SCENARIO:")
            match_tests = [
                ('dob_match_returns_200', 'Returns 200 success'),
                ('dob_match_logs_success', 'Logs success message'),
                ('dob_match_includes_certificate_fields', 'Includes certificate fields'),
            ]
            
            for test_key, description in match_tests:
                status = "✅ PASS" if self.dob_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # DOB Mismatch Results
            self.log("\n❌ DOB MISMATCH SCENARIO:")
            mismatch_tests = [
                ('dob_mismatch_returns_400', 'Returns 400 Bad Request'),
                ('dob_mismatch_error_code_correct', 'Error code DATE_OF_BIRTH_MISMATCH'),
                ('dob_mismatch_includes_comparison_data', 'Includes comparison data'),
                ('dob_mismatch_logs_error', 'Logs mismatch error'),
            ]
            
            for test_key, description in mismatch_tests:
                status = "✅ PASS" if self.dob_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Bypass Validation Results
            self.log("\n⚠️ BYPASS DOB VALIDATION:")
            bypass_tests = [
                ('bypass_parameter_works', 'Bypass parameter works'),
                ('bypass_returns_200_on_mismatch', 'Returns 200 on mismatch'),
                ('bypass_logs_warning', 'Logs bypass warning'),
                ('bypass_completes_analysis', 'Completes analysis'),
            ]
            
            for test_key, description in bypass_tests:
                status = "✅ PASS" if self.dob_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Skip Validation Results
            self.log("\n⚠️ SKIP DOB VALIDATION:")
            skip_tests = [
                ('skip_validation_no_crew_dob', 'Skip when crew has no DOB'),
                ('skip_no_crew_dob_returns_200', 'Returns 200 (no crew DOB)'),
                ('skip_no_crew_dob_logs_warning', 'Logs warning (no crew DOB)'),
                ('skip_validation_no_ai_extraction', 'Skip when AI didn\'t extract'),
                ('skip_no_ai_extraction_returns_200', 'Returns 200 (no AI extraction)'),
                ('skip_no_ai_extraction_logs_warning', 'Logs warning (no AI extraction)'),
            ]
            
            for test_key, description in skip_tests:
                status = "✅ PASS" if self.dob_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'ai_extracts_dob_field',
                'dob_match_returns_200',
                'dob_mismatch_returns_400',
                'dob_mismatch_error_code_correct',
                'bypass_parameter_works'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.dob_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ ALL CRITICAL DOB VALIDATION REQUIREMENTS MET")
                self.log("   ✅ DOB extraction and validation working correctly")
                self.log("   ✅ Error handling and bypass functionality working")
            else:
                self.log("   ❌ SOME CRITICAL REQUIREMENTS NOT MET")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
            
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
    """Main function to run DOB validation tests"""
    tester = DOBValidationTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_dob_validation_test()
        
        # Print summary
        tester.print_test_summary()
        
        if success:
            print("\n🎉 DOB VALIDATION TESTING COMPLETED SUCCESSFULLY")
            sys.exit(0)
        else:
            print("\n❌ DOB VALIDATION TESTING COMPLETED WITH ERRORS")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
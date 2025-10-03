#!/usr/bin/env python3
"""
CL Certificate Verification Test for MINH ANH 09 Ship
FOCUS: Verify EXACT cert_abbreviation data for CL (Classification Certificate) in database

REVIEW REQUEST REQUIREMENTS:
1. Find the CL (Classification Certificate) for MINH ANH 09 ship
2. Get the EXACT database record and show the cert_abbreviation field value
3. Do NOT assume or guess - show the actual database field value
4. Display the certificate ID, cert_name, and cert_abbreviation exactly as stored
5. Use admin1/123456 credentials

PURPOSE: Verify if CL certificate truly has "CL" abbreviation or if it's null/empty like the ITC certificate was.
"""

import requests
import json
import os
import sys
from datetime import datetime
import traceback

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vesseldocs.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class CLCertificateVerifier:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.minh_anh_09_ship = None
        self.cl_certificates = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
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
    
    def find_minh_anh_09_ship(self):
        """Find MINH ANH 09 ship"""
        try:
            self.log("🚢 Finding MINH ANH 09 ship...")
            
            # Get all ships to find MINH ANH 09
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} total ships")
                
                # Look for MINH ANH 09
                minh_anh_ship = None
                for ship in ships:
                    ship_name = ship.get('name', '').upper()
                    if 'MINH ANH' in ship_name and '09' in ship_name:
                        minh_anh_ship = ship
                        break
                
                if minh_anh_ship:
                    self.minh_anh_09_ship = minh_anh_ship
                    ship_id = minh_anh_ship.get('id')
                    ship_name = minh_anh_ship.get('name')
                    imo = minh_anh_ship.get('imo')
                    
                    self.log(f"✅ Found MINH ANH 09 ship:")
                    self.log(f"   Ship ID: {ship_id}")
                    self.log(f"   Ship Name: {ship_name}")
                    self.log(f"   IMO: {imo}")
                    
                    return True
                else:
                    self.log("❌ MINH ANH 09 ship not found")
                    # List available ships for debugging
                    self.log("   Available ships:")
                    for ship in ships[:10]:
                        self.log(f"      - {ship.get('name', 'Unknown')}")
                    return False
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding MINH ANH 09 ship: {str(e)}", "ERROR")
            return False
    
    def get_cl_certificates(self):
        """Get all CL (Classification Certificate) certificates for MINH ANH 09"""
        try:
            self.log("📋 Getting CL certificates for MINH ANH 09...")
            
            if not self.minh_anh_09_ship:
                self.log("❌ No MINH ANH 09 ship data available")
                return False
            
            ship_id = self.minh_anh_09_ship.get('id')
            
            # Get all certificates for this ship
            endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   Found {len(certificates)} total certificates for MINH ANH 09")
                
                # Filter for CL (Classification Certificate) certificates
                cl_certificates = []
                for cert in certificates:
                    cert_name = cert.get('cert_name', '').upper()
                    # Look for Classification Certificate patterns
                    if ('CLASSIFICATION' in cert_name and 'CERTIFICATE' in cert_name) or 'CLASSIFICATION CERTIFICATE' in cert_name:
                        cl_certificates.append(cert)
                
                self.cl_certificates = cl_certificates
                self.log(f"✅ Found {len(cl_certificates)} CL (Classification Certificate) certificates")
                
                return len(cl_certificates) > 0
            else:
                self.log(f"   ❌ Failed to get certificates: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting CL certificates: {str(e)}", "ERROR")
            return False
    
    def display_exact_cl_certificate_data(self):
        """Display EXACT database record for CL certificates with cert_abbreviation field"""
        try:
            self.log("🔍 DISPLAYING EXACT CL CERTIFICATE DATABASE RECORDS:")
            self.log("=" * 80)
            
            if not self.cl_certificates:
                self.log("❌ No CL certificates found to display")
                return False
            
            for i, cert in enumerate(self.cl_certificates, 1):
                self.log(f"\n📋 CL CERTIFICATE #{i}:")
                self.log("-" * 50)
                
                # Display the EXACT fields as requested
                cert_id = cert.get('id', 'NOT_FOUND')
                cert_name = cert.get('cert_name', 'NOT_FOUND')
                cert_abbreviation = cert.get('cert_abbreviation')  # This is the key field we're checking
                
                self.log(f"   Certificate ID: {cert_id}")
                self.log(f"   Certificate Name: {cert_name}")
                
                # Special handling for cert_abbreviation to show EXACT value
                if cert_abbreviation is None:
                    self.log(f"   Certificate Abbreviation: NULL")
                elif cert_abbreviation == "":
                    self.log(f"   Certificate Abbreviation: EMPTY_STRING")
                else:
                    self.log(f"   Certificate Abbreviation: '{cert_abbreviation}'")
                
                # Additional relevant fields for context
                cert_type = cert.get('cert_type', 'NOT_FOUND')
                cert_no = cert.get('cert_no', 'NOT_FOUND')
                issue_date = cert.get('issue_date', 'NOT_FOUND')
                valid_date = cert.get('valid_date', 'NOT_FOUND')
                
                self.log(f"   Certificate Type: {cert_type}")
                self.log(f"   Certificate Number: {cert_no}")
                self.log(f"   Issue Date: {issue_date}")
                self.log(f"   Valid Date: {valid_date}")
                
                # Show the raw JSON for complete transparency
                self.log(f"\n   RAW CERTIFICATE DATA (JSON):")
                self.log(f"   {json.dumps(cert, indent=6, default=str)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error displaying CL certificate data: {str(e)}", "ERROR")
            return False
    
    def analyze_cert_abbreviation_status(self):
        """Analyze the cert_abbreviation status for all CL certificates"""
        try:
            self.log("\n🔍 CERT_ABBREVIATION ANALYSIS:")
            self.log("=" * 50)
            
            if not self.cl_certificates:
                self.log("❌ No CL certificates to analyze")
                return False
            
            null_count = 0
            empty_count = 0
            populated_count = 0
            cl_count = 0
            
            for cert in self.cl_certificates:
                cert_abbreviation = cert.get('cert_abbreviation')
                
                if cert_abbreviation is None:
                    null_count += 1
                elif cert_abbreviation == "":
                    empty_count += 1
                else:
                    populated_count += 1
                    if cert_abbreviation == "CL":
                        cl_count += 1
            
            total_certs = len(self.cl_certificates)
            
            self.log(f"   Total CL certificates found: {total_certs}")
            self.log(f"   Certificates with NULL cert_abbreviation: {null_count}")
            self.log(f"   Certificates with EMPTY cert_abbreviation: {empty_count}")
            self.log(f"   Certificates with POPULATED cert_abbreviation: {populated_count}")
            self.log(f"   Certificates with 'CL' abbreviation: {cl_count}")
            
            # Determine the status
            if cl_count == total_certs:
                self.log(f"\n✅ RESULT: ALL CL certificates have 'CL' abbreviation")
            elif populated_count == total_certs:
                self.log(f"\n⚠️ RESULT: All CL certificates have abbreviations, but not all are 'CL'")
            elif null_count > 0 or empty_count > 0:
                self.log(f"\n❌ RESULT: Some CL certificates have NULL/EMPTY cert_abbreviation")
                self.log(f"   This matches the ITC certificate issue pattern")
            else:
                self.log(f"\n🔍 RESULT: Mixed abbreviation status")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error analyzing cert_abbreviation status: {str(e)}", "ERROR")
            return False
    
    def run_cl_certificate_verification(self):
        """Main function to verify CL certificate abbreviation data"""
        self.log("🔍 CL CERTIFICATE VERIFICATION TEST FOR MINH ANH 09 SHIP")
        self.log("🎯 FOCUS: Verify EXACT cert_abbreviation data for CL certificates")
        self.log("=" * 80)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with verification")
                return False
            
            # Step 2: Find MINH ANH 09 ship
            self.log("\n🚢 STEP 2: FIND MINH ANH 09 SHIP")
            self.log("=" * 50)
            ship_found = self.find_minh_anh_09_ship()
            if not ship_found:
                self.log("❌ MINH ANH 09 ship not found - cannot proceed with verification")
                return False
            
            # Step 3: Get CL certificates
            self.log("\n📋 STEP 3: GET CL CERTIFICATES")
            self.log("=" * 50)
            cl_found = self.get_cl_certificates()
            if not cl_found:
                self.log("❌ No CL certificates found - cannot proceed with verification")
                return False
            
            # Step 4: Display exact certificate data
            self.log("\n🔍 STEP 4: DISPLAY EXACT CERTIFICATE DATA")
            self.log("=" * 50)
            display_success = self.display_exact_cl_certificate_data()
            
            # Step 5: Analyze abbreviation status
            self.log("\n📊 STEP 5: ANALYZE ABBREVIATION STATUS")
            self.log("=" * 50)
            analysis_success = self.analyze_cert_abbreviation_status()
            
            # Step 6: Final conclusion
            self.log("\n🎯 FINAL CONCLUSION:")
            self.log("=" * 50)
            
            if display_success and analysis_success:
                self.log("✅ CL CERTIFICATE VERIFICATION COMPLETED SUCCESSFULLY")
                self.log("   All requested data has been displayed exactly as stored in database")
                self.log("   User can now verify if CL certificates have proper abbreviations")
                return True
            else:
                self.log("❌ CL CERTIFICATE VERIFICATION COMPLETED WITH ISSUES")
                return False
            
        except Exception as e:
            self.log(f"❌ CL certificate verification error: {str(e)}", "ERROR")
            return False

def main():
    """Main function to run CL Certificate Verification"""
    print("🔍 CL CERTIFICATE VERIFICATION TEST STARTED")
    print("=" * 80)
    
    try:
        verifier = CLCertificateVerifier()
        success = verifier.run_cl_certificate_verification()
        
        if success:
            print("\n✅ CL CERTIFICATE VERIFICATION COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ CL CERTIFICATE VERIFICATION COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
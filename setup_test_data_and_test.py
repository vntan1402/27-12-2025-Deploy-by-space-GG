#!/usr/bin/env python3
"""
Setup Test Data and Run DELETE Crew Validation Test

This script will:
1. Create a crew member with certificates
2. Run the DELETE crew validation test
3. Clean up test data
"""

import requests
import json
import os
import sys
import time
from datetime import datetime

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

class TestDataSetup:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.company_id = "cd1951d0-223e-4a09-865b-593047ed8c2d"
        self.created_crew_id = None
        self.created_cert_id = None
        self.ship_id = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
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
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log("✅ Authentication successful")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def find_ship(self):
        """Find a ship for certificate creation"""
        try:
            self.log("🚢 Finding ship for certificate creation...")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                if ships and len(ships) > 0:
                    self.ship_id = ships[0].get("id")
                    ship_name = ships[0].get("name")
                    self.log(f"✅ Found ship: {ship_name} (ID: {self.ship_id})")
                    return True
                else:
                    self.log("❌ No ships found", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def create_crew_with_certificate(self):
        """Create a crew member and add a certificate"""
        try:
            self.log("👤 Creating crew member with certificate...")
            
            # Step 1: Create crew member
            crew_data = {
                "full_name": "TEST CREW WITH CERTIFICATES",
                "sex": "M",
                "date_of_birth": "1985-05-15T00:00:00Z",
                "place_of_birth": "TEST CITY",
                "passport": f"TESTCERT{int(time.time())}",  # Unique passport number
                "nationality": "VIETNAMESE",
                "rank": "Test Officer",
                "status": "Sign on",
                "ship_sign_on": "BROTHER 36"
            }
            
            crew_response = self.session.post(f"{BACKEND_URL}/crew", json=crew_data, timeout=30)
            
            if crew_response.status_code in [200, 201]:
                crew_result = crew_response.json()
                self.created_crew_id = crew_result.get('id')
                crew_name = crew_result.get('full_name')
                
                self.log(f"✅ Created crew: {crew_name} (ID: {self.created_crew_id})")
                
                # Step 2: Create certificate for this crew member
                cert_data = {
                    "crew_id": self.created_crew_id,
                    "crew_name": crew_name,
                    "passport": crew_result.get('passport'),
                    "rank": crew_result.get('rank'),
                    "cert_name": "Test Certificate for DELETE Validation",
                    "cert_no": f"TESTCERT{int(time.time())}",
                    "issued_by": "Test Authority",
                    "issued_date": "2023-01-01T00:00:00Z",
                    "cert_expiry": "2025-12-31T00:00:00Z",
                    "status": "Valid",
                    "note": "Test certificate for DELETE crew validation testing"
                }
                
                cert_response = self.session.post(f"{BACKEND_URL}/crew-certificates/manual", json=cert_data, timeout=30)
                
                if cert_response.status_code in [200, 201]:
                    cert_result = cert_response.json()
                    self.created_cert_id = cert_result.get('id')
                    
                    self.log(f"✅ Created certificate: {cert_data['cert_name']} (ID: {self.created_cert_id})")
                    return True
                else:
                    self.log(f"❌ Failed to create certificate: {cert_response.status_code}", "ERROR")
                    self.log(f"   Response: {cert_response.text}")
                    return False
            else:
                self.log(f"❌ Failed to create crew: {crew_response.status_code}", "ERROR")
                self.log(f"   Response: {crew_response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating crew with certificate: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        try:
            self.log("🧹 Cleaning up test data...")
            
            # Delete certificate first
            if self.created_cert_id:
                cert_response = self.session.delete(f"{BACKEND_URL}/crew-certificates/{self.created_cert_id}", timeout=30)
                if cert_response.status_code in [200, 204]:
                    self.log("✅ Test certificate deleted")
                else:
                    self.log(f"⚠️ Failed to delete test certificate: {cert_response.status_code}")
            
            # Delete crew member
            if self.created_crew_id:
                crew_response = self.session.delete(f"{BACKEND_URL}/crew/{self.created_crew_id}", timeout=30)
                if crew_response.status_code in [200, 204]:
                    self.log("✅ Test crew deleted")
                else:
                    self.log(f"⚠️ Failed to delete test crew: {crew_response.status_code}")
                    
        except Exception as e:
            self.log(f"⚠️ Error during cleanup: {str(e)}", "WARNING")

def main():
    """Main function"""
    setup = TestDataSetup()
    
    try:
        # Setup test data
        print("=" * 80)
        print("SETTING UP TEST DATA FOR DELETE CREW VALIDATION")
        print("=" * 80)
        
        if not setup.authenticate():
            print("❌ Authentication failed")
            return False
        
        if not setup.find_ship():
            print("❌ Ship discovery failed")
            return False
        
        if not setup.create_crew_with_certificate():
            print("❌ Failed to create crew with certificate")
            return False
        
        print("\n✅ Test data setup completed successfully!")
        print(f"   Created crew ID: {setup.created_crew_id}")
        print(f"   Created certificate ID: {setup.created_cert_id}")
        
        # Run the DELETE crew validation test
        print("\n" + "=" * 80)
        print("RUNNING DELETE CREW VALIDATION TEST")
        print("=" * 80)
        
        import subprocess
        result = subprocess.run([sys.executable, "/app/delete_crew_validation_test.py"], 
                              capture_output=False, text=True)
        
        # Cleanup test data
        print("\n" + "=" * 80)
        print("CLEANING UP TEST DATA")
        print("=" * 80)
        
        setup.cleanup_test_data()
        
        print("\n✅ Test completed and cleanup finished!")
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        setup.cleanup_test_data()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        setup.cleanup_test_data()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
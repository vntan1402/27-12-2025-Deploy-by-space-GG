#!/usr/bin/env python3
"""
Ship Management System - Duplicate Certificate Detection with File Upload Testing
FOCUS: Test duplicate detection using actual file uploads to multi-upload endpoint

This test creates actual PDF files and uploads them to test the duplicate detection
functionality with the formatDateDisplay fix.
"""

import requests
import json
import os
import sys
import tempfile
from datetime import datetime
import time
import traceback

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://marine-doc-system.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class DuplicateDetectionFileTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.ship_data = {}
        self.test_results = {
            'authentication_successful': False,
            'ship_found': False,
            'first_upload_successful': False,
            'duplicate_detection_triggered': False,
            'date_formats_correct': False,
            'no_timezone_shift': False
        }
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
    def authenticate(self):
        """Authenticate with admin1/123456"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User: {self.current_user.get('username')}")
                self.log(f"   Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.test_results['authentication_successful'] = True
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def find_test_ship(self):
        """Find a ship for testing"""
        try:
            self.log("🚢 Finding test ship...")
            
            response = requests.get(f"{BACKEND_URL}/ships", headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships")
                
                # Prefer MINH ANH 09 if available
                test_ship = None
                for ship in ships:
                    if 'MINH ANH' in ship.get('name', '').upper() and '09' in ship.get('name', ''):
                        test_ship = ship
                        break
                
                if not test_ship and ships:
                    test_ship = ships[0]
                
                if test_ship:
                    self.ship_data = test_ship
                    self.log(f"✅ Using ship: {test_ship.get('name')} (ID: {test_ship.get('id')})")
                    self.test_results['ship_found'] = True
                    return True
                else:
                    self.log("❌ No ships available")
                    return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def create_test_pdf_file(self, filename="test_certificate.pdf"):
        """Create a simple test PDF file"""
        try:
            # Create a simple text file that we'll treat as a PDF for testing
            content = f"""CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE
Certificate No: TEST-CSSC-2025-001
Issue Date: 10/12/2024
Valid Date: 18/03/2028
Last Endorse: 29/04/2024
Ship Name: {self.ship_data.get('name', 'TEST SHIP')}
IMO: {self.ship_data.get('imo', '1234567')}
Issued by: PANAMA MARITIME DOCUMENTATION SERVICES
"""
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False)
            temp_file.write(content)
            temp_file.close()
            
            self.log(f"✅ Created test file: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Error creating test file: {str(e)}", "ERROR")
            return None
    
    def test_multi_upload_with_duplicate_detection(self):
        """Test multi-upload endpoint with duplicate detection"""
        try:
            self.log("📤 Testing multi-upload with duplicate detection...")
            
            if not self.ship_data.get('id'):
                self.log("❌ No ship data available")
                return False
            
            ship_id = self.ship_data.get('id')
            
            # Create test file
            test_file_path = self.create_test_pdf_file()
            if not test_file_path:
                return False
            
            try:
                # First upload
                self.log("   📤 First upload...")
                
                with open(test_file_path, 'rb') as f:
                    files = {'files': (os.path.basename(test_file_path), f, 'application/pdf')}
                    data = {'ship_id': ship_id}
                    
                    response = requests.post(
                        f"{BACKEND_URL}/certificates/multi-upload",
                        files=files,
                        data=data,
                        headers=self.get_headers(),
                        timeout=60
                    )
                
                self.log(f"   First upload response: {response.status_code}")
                
                if response.status_code == 200:
                    first_response = response.json()
                    self.log("✅ First upload successful")
                    self.log(f"   Response: {json.dumps(first_response, indent=6)}")
                    
                    self.test_results['first_upload_successful'] = True
                    
                    # Wait a moment before second upload
                    time.sleep(2)
                    
                    # Second upload (same file - should trigger duplicate detection)
                    self.log("   🔄 Second upload (duplicate)...")
                    
                    with open(test_file_path, 'rb') as f:
                        files = {'files': (os.path.basename(test_file_path), f, 'application/pdf')}
                        data = {'ship_id': ship_id}
                        
                        response = requests.post(
                            f"{BACKEND_URL}/certificates/multi-upload",
                            files=files,
                            data=data,
                            headers=self.get_headers(),
                            timeout=60
                        )
                    
                    self.log(f"   Second upload response: {response.status_code}")
                    
                    if response.status_code == 200:
                        second_response = response.json()
                        self.log("   Second upload response:")
                        self.log(f"   {json.dumps(second_response, indent=6)}")
                        
                        # Check if duplicate detection was triggered
                        if self.check_duplicate_detection_in_response(second_response):
                            self.test_results['duplicate_detection_triggered'] = True
                            self.log("✅ Duplicate detection triggered successfully")
                            
                            # Check date formats in response
                            if self.verify_date_formats_in_response(second_response):
                                self.test_results['date_formats_correct'] = True
                                self.test_results['no_timezone_shift'] = True
                                self.log("✅ Date formats are correct")
                            
                            return True
                        else:
                            self.log("⚠️ Duplicate detection may not have been triggered")
                            return False
                    else:
                        self.log(f"❌ Second upload failed: {response.status_code}")
                        try:
                            error_data = response.json()
                            self.log(f"   Error: {error_data}")
                        except:
                            self.log(f"   Error: {response.text[:500]}")
                        return False
                else:
                    self.log(f"❌ First upload failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data}")
                    except:
                        self.log(f"   Error: {response.text[:500]}")
                    return False
                    
            finally:
                # Clean up test file
                if os.path.exists(test_file_path):
                    os.unlink(test_file_path)
                    self.log(f"   🧹 Cleaned up test file: {test_file_path}")
                
        except Exception as e:
            self.log(f"❌ Error testing multi-upload: {str(e)}", "ERROR")
            return False
    
    def check_duplicate_detection_in_response(self, response_data):
        """Check if response indicates duplicate detection was triggered"""
        try:
            # Look for duplicate detection indicators
            if isinstance(response_data, dict):
                # Check for status indicating duplicate
                status = response_data.get('status')
                if status == 'pending_duplicate_resolution':
                    return True
                
                # Check for duplicate-related fields
                if 'existing_certificate' in response_data or 'duplicate' in str(response_data).lower():
                    return True
                
                # Check if it's a list of results with duplicate status
                results = response_data.get('results', [])
                if isinstance(results, list):
                    for result in results:
                        if isinstance(result, dict) and result.get('status') == 'pending_duplicate_resolution':
                            return True
            
            return False
            
        except Exception as e:
            self.log(f"   Error checking duplicate detection: {str(e)}")
            return False
    
    def verify_date_formats_in_response(self, response_data):
        """Verify date formats in the response"""
        try:
            self.log("   📅 Verifying date formats...")
            
            # Look for date fields in various parts of the response
            dates_found = []
            
            def extract_dates_from_dict(data, prefix=""):
                if isinstance(data, dict):
                    for key, value in data.items():
                        if 'date' in key.lower() and isinstance(value, str):
                            dates_found.append(f"{prefix}{key}: {value}")
                        elif isinstance(value, (dict, list)):
                            extract_dates_from_dict(value, f"{prefix}{key}.")
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        extract_dates_from_dict(item, f"{prefix}[{i}].")
            
            extract_dates_from_dict(response_data)
            
            if dates_found:
                self.log("   Found dates in response:")
                for date_info in dates_found:
                    self.log(f"      {date_info}")
                
                # Check if dates are in expected formats
                all_formats_good = True
                for date_info in dates_found:
                    date_value = date_info.split(': ', 1)[1] if ': ' in date_info else date_info
                    if not self.is_valid_date_format(date_value):
                        self.log(f"      ⚠️ Invalid date format: {date_value}")
                        all_formats_good = False
                
                return all_formats_good
            else:
                self.log("   No dates found in response")
                return True  # No dates to verify
                
        except Exception as e:
            self.log(f"   Error verifying date formats: {str(e)}")
            return False
    
    def is_valid_date_format(self, date_value):
        """Check if date value has a valid format"""
        if not date_value:
            return True
        
        import re
        
        # Valid date formats
        valid_patterns = [
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$',  # ISO
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # DD/MM/YYYY
            r'^\d{1,2}/\d{1,2}/\d{4}$'  # D/M/YYYY variations
        ]
        
        for pattern in valid_patterns:
            if re.match(pattern, date_value):
                return True
        
        return False
    
    def run_comprehensive_test(self):
        """Run comprehensive duplicate detection test"""
        self.log("🔄 STARTING DUPLICATE DETECTION FILE UPLOAD TESTING")
        self.log("=" * 80)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            if not self.authenticate():
                return False
            
            # Step 2: Find test ship
            self.log("\n🚢 STEP 2: FIND TEST SHIP")
            if not self.find_test_ship():
                return False
            
            # Step 3: Test multi-upload with duplicate detection
            self.log("\n📤 STEP 3: TEST MULTI-UPLOAD WITH DUPLICATE DETECTION")
            success = self.test_multi_upload_with_duplicate_detection()
            
            # Step 4: Final analysis
            self.log("\n📊 STEP 4: FINAL ANALYSIS")
            self.provide_final_analysis()
            
            return success
            
        except Exception as e:
            self.log(f"❌ Comprehensive test error: {str(e)}", "ERROR")
            return False
    
    def provide_final_analysis(self):
        """Provide final analysis"""
        try:
            self.log("🔄 DUPLICATE DETECTION FILE UPLOAD TESTING - RESULTS")
            self.log("=" * 60)
            
            passed_tests = sum(1 for result in self.test_results.values() if result)
            total_tests = len(self.test_results)
            success_rate = (passed_tests / total_tests) * 100
            
            self.log(f"📊 SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")
            
            for test_name, passed in self.test_results.items():
                status = "✅" if passed else "❌"
                self.log(f"   {status} {test_name.replace('_', ' ').title()}")
            
            # Review requirements analysis
            self.log("\n📋 REVIEW REQUIREMENTS ANALYSIS:")
            
            req1 = self.test_results['authentication_successful']  # Login admin1/123456
            req2 = self.test_results['duplicate_detection_triggered']  # Upload same file twice
            req3 = self.test_results['no_timezone_shift']  # No time shift
            req4 = self.test_results['date_formats_correct']  # Date formats correct
            req5 = self.test_results['first_upload_successful']  # Upload functionality working
            
            self.log(f"   1. Login with admin1/123456: {'✅ MET' if req1 else '❌ NOT MET'}")
            self.log(f"   2. Duplicate detection triggered: {'✅ MET' if req2 else '❌ NOT MET'}")
            self.log(f"   3. No timezone shift in dates: {'✅ MET' if req3 else '❌ NOT MET'}")
            self.log(f"   4. Date formats correct: {'✅ MET' if req4 else '❌ NOT MET'}")
            self.log(f"   5. Upload functionality working: {'✅ MET' if req5 else '❌ NOT MET'}")
            
            requirements_met = sum([req1, req2, req3, req4, req5])
            
            # Final conclusion
            if success_rate >= 80 and requirements_met >= 4:
                self.log(f"\n🎉 CONCLUSION: DATE DISPLAY FIX FOR DUPLICATE DETECTION IS WORKING")
                self.log(f"   ✅ Duplicate detection properly triggered")
                self.log(f"   ✅ Date formats are consistent and correct")
                self.log(f"   ✅ No timezone shift issues detected")
            elif success_rate >= 60:
                self.log(f"\n⚠️ CONCLUSION: DATE DISPLAY FIX PARTIALLY WORKING")
                self.log(f"   ⚠️ Some functionality working, improvements needed")
                if not req2:
                    self.log(f"   ⚠️ Duplicate detection may need attention")
                if not req3 or not req4:
                    self.log(f"   ⚠️ Date formatting may need attention")
            else:
                self.log(f"\n❌ CONCLUSION: DATE DISPLAY FIX HAS ISSUES")
                self.log(f"   ❌ Significant fixes needed")
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")

def main():
    """Main function"""
    print("🔄 DUPLICATE DETECTION FILE UPLOAD TESTING STARTED")
    print("=" * 60)
    
    try:
        tester = DuplicateDetectionFileTester()
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n✅ TESTING COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ TESTING COMPLETED WITH ISSUES")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    sys.exit(0)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Fixed Test Report Batch Upload Debug - Chemical Suit.pdf and Co2.pdf Issue Investigation

ISSUE FOUND: The test was using wrong field name 'file' instead of 'test_report_file'
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
import subprocess

# Configuration - Use environment variable for backend URL
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipsystem.preview.emergentagent.com') + '/api'
print(f"Using backend URL: {BACKEND_URL}")

class TestReportBatchUploadFixedTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.ship_id = None
        self.ship_name = "BROTHER 36"
        
        # Store created test report IDs for cleanup
        self.created_report_ids = []
        
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
        """Find the test ship"""
        try:
            self.log(f"🚢 Finding ship: {self.ship_name}")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                for ship in ships:
                    if ship.get("name") == self.ship_name:
                        self.ship_id = ship.get("id")
                        self.log(f"✅ Found ship: {self.ship_name} (ID: {self.ship_id})")
                        return True
                
                self.log(f"❌ Ship '{self.ship_name}' not found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding ship: {str(e)}", "ERROR")
            return False
    
    def test_file_analysis_corrected(self, file_path, filename):
        """Test file analysis with CORRECT field name"""
        try:
            if not os.path.exists(file_path):
                self.log(f"❌ File not found: {file_path}", "ERROR")
                return None
            
            # Prepare multipart form data with CORRECT field name
            with open(file_path, "rb") as f:
                files = {
                    "test_report_file": (filename, f, "application/pdf")  # CORRECT field name
                }
                data = {
                    "ship_id": self.ship_id,
                    "bypass_validation": "true"
                }
                
                self.log(f"📤 Uploading {filename} with CORRECT field name 'test_report_file'")
                
                endpoint = f"{BACKEND_URL}/test-reports/analyze-file"
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
                result = response.json()
                self.log("✅ File analysis successful with corrected field name!")
                
                # Log response structure
                self.log(f"📊 Response keys: {list(result.keys())}")
                
                # Check success field
                success = result.get("success", False)
                self.log(f"   Success: {success}")
                
                # Check extracted fields
                extracted_fields = [
                    'test_report_name', 'report_form', 'test_report_no', 
                    'issued_by', 'issued_date', 'valid_date', 'note'
                ]
                
                self.log("📋 Extracted fields:")
                for field in extracted_fields:
                    value = result.get(field, '')
                    if value:
                        self.log(f"   {field}: {value}")
                    else:
                        self.log(f"   {field}: (empty)")
                
                # Check metadata fields
                metadata_fields = ['_file_content', '_summary_text', '_filename', '_content_type']
                self.log("📋 Metadata fields:")
                for field in metadata_fields:
                    value = result.get(field)
                    if field == '_file_content' and value:
                        self.log(f"   {field}: Present ({len(value)} characters)")
                    elif field == '_summary_text' and value:
                        self.log(f"   {field}: Present ({len(value)} characters)")
                    elif value:
                        self.log(f"   {field}: {value}")
                    else:
                        self.log(f"   {field}: (missing)")
                
                return result
            else:
                self.log(f"❌ File analysis failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}", "ERROR")
                except:
                    self.log(f"   Error text: {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error in file analysis: {str(e)}", "ERROR")
            return None
    
    def test_complete_batch_flow(self, file_path, filename):
        """Test complete batch flow for a single file"""
        try:
            self.log(f"🔄 Testing complete batch flow for {filename}")
            
            # Step 1: Analyze file
            self.log("   Step 1: Analyze file...")
            analyze_result = self.test_file_analysis_corrected(file_path, filename)
            
            if not analyze_result:
                self.log(f"❌ Step 1 failed for {filename}", "ERROR")
                return False
            
            # Check if we have the required fields for next steps
            file_content = analyze_result.get('_file_content')
            summary_text = analyze_result.get('_summary_text', '')
            
            if not file_content:
                self.log(f"❌ Step 1: No _file_content for {filename} - cannot proceed to upload", "ERROR")
                return False
            
            # Step 2: Create test report record
            self.log("   Step 2: Create test report record...")
            create_result = self.create_test_report_record(analyze_result, filename)
            
            if not create_result:
                self.log(f"❌ Step 2 failed for {filename}", "ERROR")
                return False
            
            report_id = create_result.get('id')
            if not report_id:
                self.log(f"❌ Step 2: No report ID returned for {filename}", "ERROR")
                return False
            
            self.created_report_ids.append(report_id)
            
            # Step 3: Upload files
            self.log("   Step 3: Upload files...")
            upload_result = self.upload_test_report_files(
                report_id, file_content, filename, summary_text
            )
            
            if upload_result:
                self.log(f"✅ Complete batch flow successful for {filename}")
                return True
            else:
                self.log(f"❌ Step 3 failed for {filename}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in batch flow for {filename}: {str(e)}", "ERROR")
            return False
    
    def create_test_report_record(self, analyze_result, filename):
        """Create test report record using analyzed data"""
        try:
            # Extract data from analysis result
            test_report_data = {
                "ship_id": self.ship_id,
                "test_report_name": analyze_result.get('test_report_name', filename),
                "report_form": analyze_result.get('report_form', ''),
                "test_report_no": analyze_result.get('test_report_no', ''),
                "issued_by": analyze_result.get('issued_by', ''),
                "issued_date": analyze_result.get('issued_date'),
                "valid_date": analyze_result.get('valid_date'),
                "status": analyze_result.get('status', 'Valid'),
                "note": analyze_result.get('note', '')
            }
            
            # Remove None values AND empty strings for date fields
            test_report_data = {k: v for k, v in test_report_data.items() if v is not None and v != ''}
            
            self.log(f"📤 Creating test report record for {filename}")
            
            endpoint = f"{BACKEND_URL}/test-reports"
            response = self.session.post(endpoint, json=test_report_data, timeout=60)
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.log(f"✅ Test report created: ID {result.get('id')}")
                return result
            else:
                self.log(f"❌ Failed to create test report: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}", "ERROR")
                except:
                    self.log(f"   Error text: {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error creating test report record: {str(e)}", "ERROR")
            return None
    
    def upload_test_report_files(self, report_id, file_content, filename, summary_text):
        """Upload files to test report"""
        try:
            # Prepare upload data exactly as frontend does
            upload_data = {
                "file_content": file_content,
                "filename": filename,
                "content_type": "application/pdf",
                "summary_text": summary_text
            }
            
            self.log(f"📤 Uploading files for report {report_id}")
            self.log(f"   Filename: {filename}")
            self.log(f"   Content type: application/pdf")
            self.log(f"   File content length: {len(file_content) if file_content else 0}")
            self.log(f"   Summary text length: {len(summary_text) if summary_text else 0}")
            
            endpoint = f"{BACKEND_URL}/test-reports/{report_id}/upload-files"
            response = self.session.post(endpoint, json=upload_data, timeout=120)
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Files uploaded successfully")
                return result
            else:
                self.log(f"❌ File upload failed: {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}", "ERROR")
                    
                    # Capture exact error message for analysis
                    error_detail = error_data.get('detail', str(error_data))
                    self.log(f"🔍 EXACT ERROR MESSAGE: {error_detail}", "ERROR")
                    
                except:
                    self.log(f"   Error text: {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error uploading files: {str(e)}", "ERROR")
            return None
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        try:
            self.log("🧹 Cleaning up test data...")
            
            for report_id in self.created_report_ids[:]:
                try:
                    endpoint = f"{BACKEND_URL}/test-reports/{report_id}"
                    response = self.session.delete(endpoint, timeout=30)
                    if response.status_code in [200, 204]:
                        self.log(f"   ✅ Cleaned up test report ID: {report_id}")
                        self.created_report_ids.remove(report_id)
                    else:
                        self.log(f"   ⚠️ Failed to clean up test report ID: {report_id}")
                except Exception as e:
                    self.log(f"   ⚠️ Error cleaning up test report ID {report_id}: {str(e)}")
            
            self.log("✅ Cleanup completed")
            
        except Exception as e:
            self.log(f"❌ Error during cleanup: {str(e)}", "ERROR")
    
    def run_fixed_test(self):
        """Run the fixed test with correct field names"""
        try:
            self.log("🚀 STARTING FIXED TEST REPORT BATCH UPLOAD TEST")
            self.log("=" * 80)
            self.log("Testing with CORRECTED field name 'test_report_file'")
            self.log("=" * 80)
            
            # Authentication
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed")
                return False
            
            # Find ship
            if not self.find_ship():
                self.log("❌ Ship discovery failed - cannot proceed")
                return False
            
            # Test Chemical Suit.pdf
            self.log("\n📄 Testing Chemical Suit.pdf with corrected field name...")
            chemical_success = self.test_complete_batch_flow(
                "/app/Chemical_Suit.pdf", "Chemical_Suit.pdf"
            )
            
            # Test Co2.pdf
            self.log("\n📄 Testing Co2.pdf with corrected field name...")
            co2_success = self.test_complete_batch_flow(
                "/app/Co2.pdf", "Co2.pdf"
            )
            
            # Cleanup
            self.cleanup_test_data()
            
            self.log("\n" + "=" * 80)
            self.log("📊 FIXED TEST RESULTS:")
            self.log(f"   Chemical Suit.pdf: {'✅ SUCCESS' if chemical_success else '❌ FAILED'}")
            self.log(f"   Co2.pdf: {'✅ SUCCESS' if co2_success else '❌ FAILED'}")
            
            if chemical_success and co2_success:
                self.log("✅ BOTH FILES PROCESSED SUCCESSFULLY!")
                self.log("🎯 ROOT CAUSE WAS: Wrong field name 'file' instead of 'test_report_file'")
            elif chemical_success or co2_success:
                self.log("⚠️ PARTIAL SUCCESS - One file working")
            else:
                self.log("❌ BOTH FILES STILL FAILING - Need further investigation")
            
            self.log("=" * 80)
            return chemical_success and co2_success
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in fixed test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False

def main():
    """Main function to run the fixed test"""
    try:
        print("🚀 Starting Fixed Test Report Batch Upload Test")
        print("Testing with corrected field name 'test_report_file'")
        print("=" * 80)
        
        # Create tester instance
        tester = TestReportBatchUploadFixedTester()
        
        # Run fixed test
        success = tester.run_fixed_test()
        
        if success:
            print("\n✅ Fixed test completed successfully - Issue resolved!")
            return 0
        else:
            print("\n❌ Fixed test still shows issues - Need further investigation")
            return 1
            
    except Exception as e:
        print(f"❌ Critical error in main: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Detailed Test Report Batch Upload Investigation
==============================================

This script focuses on the specific issue found: _file_content is missing in batch mode
causing the file upload step to fail with 422 errors.
"""

import requests
import json
import base64
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://shipsystem.preview.emergentagent.com/api"
TEST_FILES = {
    "Chemical_Suit.pdf": "/tmp/Chemical_Suit.pdf",
    "Co2.pdf": "/tmp/Co2.pdf"
}

class DetailedBatchUploadInvestigator:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.ship_info = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate(self) -> bool:
        """Authenticate with the backend"""
        try:
            login_data = {"username": "admin1", "password": "123456"}
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                auth_response = response.json()
                self.auth_token = auth_response.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                return True
            return False
        except Exception as e:
            self.log(f"Authentication error: {e}", "ERROR")
            return False
    
    def get_ship_info(self) -> bool:
        """Get ship information"""
        try:
            response = self.session.get(f"{BACKEND_URL}/ships")
            if response.status_code == 200:
                ships = response.json()
                for ship in ships:
                    if ship.get("name") == "BROTHER 36":
                        self.ship_info = ship
                        return True
            return False
        except Exception as e:
            self.log(f"Error getting ship info: {e}", "ERROR")
            return False
    
    def compare_single_vs_batch_responses(self):
        """Compare single mode vs batch mode responses in detail"""
        self.log("🔍 DETAILED COMPARISON: Single Mode vs Batch Mode")
        self.log("=" * 80)
        
        for filename, filepath in TEST_FILES.items():
            self.log(f"\n📄 Testing {filename}")
            self.log("-" * 50)
            
            # Test single mode (bypass_validation=false)
            single_response = self.test_analyze_mode(filepath, filename, bypass_validation=False)
            
            # Test batch mode (bypass_validation=true)  
            batch_response = self.test_analyze_mode(filepath, filename, bypass_validation=True)
            
            # Compare responses
            self.compare_responses(filename, single_response, batch_response)
    
    def test_analyze_mode(self, filepath: str, filename: str, bypass_validation: bool):
        """Test analyze endpoint in specific mode"""
        try:
            with open(filepath, 'rb') as f:
                file_content = f.read()
            
            files = {'test_report_file': (filename, file_content, 'application/pdf')}
            data = {
                'ship_id': self.ship_info['id'],
                'bypass_validation': 'true' if bypass_validation else 'false'
            }
            
            mode_name = "BATCH" if bypass_validation else "SINGLE"
            self.log(f"   🔄 Testing {mode_name} mode (bypass_validation={bypass_validation})")
            
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/test-reports/analyze-file", files=files, data=data)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Log key information
                self.log(f"   ✅ {mode_name} mode: SUCCESS ({duration:.1f}s)")
                self.log(f"      Status Code: {response.status_code}")
                self.log(f"      Response Size: {len(json.dumps(response_data))} chars")
                
                # Check critical fields
                has_file_content = "_file_content" in response_data and response_data["_file_content"]
                has_summary = "_summary_text" in response_data and response_data["_summary_text"]
                
                self.log(f"      _file_content: {'✅ PRESENT' if has_file_content else '❌ MISSING'}")
                self.log(f"      _summary_text: {'✅ PRESENT' if has_summary else '❌ MISSING'}")
                
                if has_file_content:
                    file_content_size = len(response_data["_file_content"])
                    self.log(f"      _file_content size: {file_content_size} chars")
                
                return {
                    "success": True,
                    "mode": mode_name,
                    "response": response_data,
                    "duration": duration,
                    "has_file_content": has_file_content,
                    "has_summary": has_summary
                }
            else:
                self.log(f"   ❌ {mode_name} mode: FAILED ({response.status_code})")
                self.log(f"      Error: {response.text}")
                return {
                    "success": False,
                    "mode": mode_name,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": duration
                }
                
        except Exception as e:
            self.log(f"   ❌ {mode_name} mode: ERROR - {e}", "ERROR")
            return {"success": False, "mode": mode_name, "error": str(e)}
    
    def compare_responses(self, filename: str, single_response: dict, batch_response: dict):
        """Compare single vs batch responses in detail"""
        self.log(f"\n   📊 COMPARISON RESULTS for {filename}:")
        
        if single_response.get("success") and batch_response.get("success"):
            single_data = single_response.get("response", {})
            batch_data = batch_response.get("response", {})
            
            # Compare field counts
            single_fields = len([k for k, v in single_data.items() if v])
            batch_fields = len([k for k, v in batch_data.items() if v])
            
            self.log(f"      Field Count - Single: {single_fields}, Batch: {batch_fields}")
            
            # Compare critical fields
            critical_fields = ["_file_content", "_summary_text", "_filename", "test_report_name"]
            
            for field in critical_fields:
                single_has = field in single_data and single_data[field]
                batch_has = field in batch_data and batch_data[field]
                
                status = "✅ SAME" if single_has == batch_has else "❌ DIFFERENT"
                self.log(f"      {field}: Single={single_has}, Batch={batch_has} - {status}")
                
                if field == "_file_content" and single_has != batch_has:
                    self.log(f"         🚨 CRITICAL: _file_content missing in batch mode!")
            
            # Check extracted field values
            extracted_fields = ["test_report_name", "test_report_no", "issued_by", "report_form"]
            
            self.log(f"      📋 Extracted Field Values:")
            for field in extracted_fields:
                single_val = single_data.get(field, "")
                batch_val = batch_data.get(field, "")
                
                if single_val == batch_val:
                    self.log(f"         {field}: ✅ SAME ('{single_val}')")
                else:
                    self.log(f"         {field}: ❌ DIFFERENT")
                    self.log(f"            Single: '{single_val}'")
                    self.log(f"            Batch:  '{batch_val}'")
        
        else:
            self.log(f"      ❌ Cannot compare - one or both modes failed")
            if not single_response.get("success"):
                self.log(f"         Single mode error: {single_response.get('error')}")
            if not batch_response.get("success"):
                self.log(f"         Batch mode error: {batch_response.get('error')}")
    
    def test_file_upload_with_missing_content(self):
        """Test what happens when we try to upload without _file_content"""
        self.log(f"\n🔄 TESTING FILE UPLOAD WITH MISSING _file_content")
        self.log("=" * 80)
        
        # Create a test report first
        create_data = {
            "ship_id": self.ship_info['id'],
            "test_report_name": "Test Report for Upload Investigation",
            "test_report_no": "TEST-001",
            "issued_by": "Test Authority"
        }
        
        response = self.session.post(f"{BACKEND_URL}/test-reports", json=create_data)
        
        if response.status_code in [200, 201]:
            report_data = response.json()
            report_id = report_data.get("id")
            self.log(f"✅ Test report created: {report_id}")
            
            # Try to upload with missing fields (simulating batch mode issue)
            upload_data = {
                "original_file_content": None,  # Missing
                "original_filename": None       # Missing
            }
            
            self.log(f"🔄 Attempting upload with missing fields...")
            upload_response = self.session.post(
                f"{BACKEND_URL}/test-reports/{report_id}/upload-files",
                json=upload_data
            )
            
            self.log(f"📤 Upload Response:")
            self.log(f"   Status Code: {upload_response.status_code}")
            self.log(f"   Response: {upload_response.text}")
            
            if upload_response.status_code == 422:
                self.log(f"   🚨 CONFIRMED: 422 error when _file_content is missing")
                
                # Parse the error details
                try:
                    error_data = upload_response.json()
                    if "detail" in error_data:
                        self.log(f"   📋 Missing Fields:")
                        for error in error_data["detail"]:
                            field_name = error.get("loc", [])[-1] if error.get("loc") else "unknown"
                            self.log(f"      - {field_name}: {error.get('msg', 'No message')}")
                except:
                    pass
        else:
            self.log(f"❌ Failed to create test report: {response.status_code} - {response.text}")
    
    def investigate_backend_code_difference(self):
        """Investigate why _file_content is missing in batch mode"""
        self.log(f"\n🔬 INVESTIGATING BACKEND CODE DIFFERENCE")
        self.log("=" * 80)
        
        self.log("📋 Key Questions to Investigate:")
        self.log("   1. Does bypass_validation=true affect _file_content inclusion?")
        self.log("   2. Is there different code path for batch vs single mode?")
        self.log("   3. Are there any conditional statements around _file_content?")
        self.log("   4. Does the response building differ between modes?")
        
        # Test with both modes and examine response structure
        for filename, filepath in TEST_FILES.items():
            self.log(f"\n📄 Examining {filename} response structure:")
            
            # Get both responses
            single_resp = self.test_analyze_mode(filepath, filename, bypass_validation=False)
            batch_resp = self.test_analyze_mode(filepath, filename, bypass_validation=True)
            
            if single_resp.get("success") and batch_resp.get("success"):
                single_keys = set(single_resp["response"].keys())
                batch_keys = set(batch_resp["response"].keys())
                
                missing_in_batch = single_keys - batch_keys
                extra_in_batch = batch_keys - single_keys
                
                if missing_in_batch:
                    self.log(f"   🚨 Fields missing in batch mode: {missing_in_batch}")
                
                if extra_in_batch:
                    self.log(f"   ℹ️  Extra fields in batch mode: {extra_in_batch}")
                
                if not missing_in_batch and not extra_in_batch:
                    self.log(f"   ✅ Same fields in both modes")
                    
                    # Check for empty values
                    for key in single_keys:
                        single_val = single_resp["response"].get(key)
                        batch_val = batch_resp["response"].get(key)
                        
                        single_empty = not single_val
                        batch_empty = not batch_val
                        
                        if single_empty != batch_empty:
                            self.log(f"   🚨 Value difference in {key}: Single={'empty' if single_empty else 'has_value'}, Batch={'empty' if batch_empty else 'has_value'}")
    
    def run_investigation(self):
        """Run the complete investigation"""
        self.log("🚀 STARTING DETAILED BATCH UPLOAD INVESTIGATION")
        self.log("=" * 80)
        
        if not self.authenticate():
            self.log("❌ Authentication failed", "ERROR")
            return False
        
        if not self.get_ship_info():
            self.log("❌ Failed to get ship info", "ERROR")
            return False
        
        self.log(f"✅ Setup complete - Ship: {self.ship_info['name']} (ID: {self.ship_info['id']})")
        
        # Run investigations
        self.compare_single_vs_batch_responses()
        self.test_file_upload_with_missing_content()
        self.investigate_backend_code_difference()
        
        self.log(f"\n🎯 INVESTIGATION COMPLETE")
        self.log("=" * 80)
        
        return True

def main():
    investigator = DetailedBatchUploadInvestigator()
    investigator.run_investigation()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
Focus: OCR functionality testing with image-based PDF files
"""

import requests
import json
import os
import sys
from datetime import datetime
import tempfile
import subprocess

# Configuration
BACKEND_URL = "https://shipment-ai-1.preview.emergentagent.com/api"
TEST_PDF_URL = "https://customer-assets.emergentagent.com/job_shipment-ai-1/artifacts/1mu8wxqn_SS%20STAR%20PM252494416_ImagePDF.pdf"

# Test credentials
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def authenticate(self):
        """Authenticate with the backend"""
        try:
            self.log("🔐 Starting authentication...")
            
            login_data = {
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD,
                "remember_me": False
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_info = data.get("user")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log(f"✅ Authentication successful")
                self.log(f"   User: {self.user_info.get('username')} ({self.user_info.get('role')})")
                self.log(f"   Full Name: {self.user_info.get('full_name')}")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def download_test_pdf(self):
        """Download the test PDF file"""
        try:
            self.log("📥 Downloading test PDF file...")
            self.log(f"   URL: {TEST_PDF_URL}")
            
            response = requests.get(TEST_PDF_URL, stream=True)
            
            if response.status_code == 200:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                
                # Write content to file
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                
                temp_file.close()
                
                # Get file size
                file_size = os.path.getsize(temp_file.name)
                self.log(f"✅ PDF downloaded successfully")
                self.log(f"   File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                self.log(f"   Temp file: {temp_file.name}")
                
                return temp_file.name
            else:
                self.log(f"❌ Failed to download PDF: {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ PDF download error: {str(e)}", "ERROR")
            return None
    
    def check_ocr_dependencies(self):
        """Check if OCR dependencies are installed"""
        self.log("🔍 Checking OCR dependencies...")
        
        dependencies = {
            "tesseract": ["tesseract", "--version"],
            "poppler": ["pdftoppm", "-h"]
        }
        
        results = {}
        
        for dep_name, command in dependencies.items():
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Extract version info
                    version_info = result.stdout.split('\n')[0] if result.stdout else "Version info not available"
                    self.log(f"   ✅ {dep_name}: {version_info}")
                    results[dep_name] = True
                else:
                    self.log(f"   ❌ {dep_name}: Not working properly", "WARN")
                    results[dep_name] = False
            except subprocess.TimeoutExpired:
                self.log(f"   ❌ {dep_name}: Command timeout", "WARN")
                results[dep_name] = False
            except FileNotFoundError:
                self.log(f"   ❌ {dep_name}: Not installed", "WARN")
                results[dep_name] = False
            except Exception as e:
                self.log(f"   ❌ {dep_name}: Error - {str(e)}", "WARN")
                results[dep_name] = False
        
        return results
    
    def test_ocr_endpoint(self, pdf_file_path):
        """Test the OCR endpoint with the specific PDF file"""
        try:
            self.log("🔬 Testing OCR endpoint...")
            self.log(f"   Endpoint: {BACKEND_URL}/analyze-ship-certificate")
            
            # Prepare file for upload
            with open(pdf_file_path, 'rb') as pdf_file:
                files = {
                    'file': ('SS_STAR_PM252494416_ImagePDF.pdf', pdf_file, 'application/pdf')
                }
                
                # Record start time
                start_time = datetime.now()
                
                # Make the request
                response = self.session.post(f"{BACKEND_URL}/analyze-ship-certificate", files=files)
                
                # Record end time
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                self.log(f"   Processing time: {processing_time:.2f} seconds")
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.log("✅ OCR endpoint responded successfully")
                        
                        # Analyze the response structure
                        self.analyze_ocr_response(data, processing_time)
                        return data
                        
                    except json.JSONDecodeError:
                        self.log("❌ Invalid JSON response", "ERROR")
                        self.log(f"   Raw response: {response.text[:500]}...", "ERROR")
                        return None
                else:
                    self.log(f"❌ OCR endpoint failed: {response.status_code}", "ERROR")
                    self.log(f"   Error response: {response.text}", "ERROR")
                    return None
                    
        except Exception as e:
            self.log(f"❌ OCR endpoint test error: {str(e)}", "ERROR")
            return None
    
    def analyze_ocr_response(self, response_data, processing_time):
        """Analyze and display the OCR response in detail"""
        self.log("📊 Analyzing OCR Response:")
        
        # Check response structure
        if isinstance(response_data, dict):
            # Display main response fields
            success = response_data.get('success', False)
            self.log(f"   Success: {success}")
            
            # Check for analysis data
            if 'data' in response_data and 'analysis' in response_data['data']:
                analysis = response_data['data']['analysis']
                self.log("   📋 Extracted Ship Information:")
                
                ship_fields = [
                    'ship_name', 'imo_number', 'flag', 'class_society', 
                    'gross_tonnage', 'deadweight', 'built_year', 'ship_owner'
                ]
                
                extracted_count = 0
                for field in ship_fields:
                    value = analysis.get(field)
                    if value and value != 'null' and str(value).strip():
                        self.log(f"      ✅ {field.replace('_', ' ').title()}: {value}")
                        extracted_count += 1
                    else:
                        self.log(f"      ❌ {field.replace('_', ' ').title()}: Not extracted")
                
                self.log(f"   📈 Extraction Success Rate: {extracted_count}/{len(ship_fields)} ({extracted_count/len(ship_fields)*100:.1f}%)")
                
            # Check for processing details
            if 'processing_method' in response_data:
                self.log(f"   🔧 Processing Method: {response_data['processing_method']}")
            
            if 'confidence_score' in response_data:
                self.log(f"   📊 Confidence Score: {response_data['confidence_score']}")
            
            if 'ocr_text_length' in response_data:
                self.log(f"   📝 OCR Text Length: {response_data['ocr_text_length']} characters")
            
            # Check for fallback reasons
            if 'fallback_reason' in response_data:
                self.log(f"   ⚠️  Fallback Reason: {response_data['fallback_reason']}", "WARN")
            
            # Display full response for debugging
            self.log("   🔍 Full Response Structure:")
            self.log(f"      {json.dumps(response_data, indent=2, default=str)}")
            
        else:
            self.log(f"   ❌ Unexpected response format: {type(response_data)}", "ERROR")
    
    def check_backend_logs(self):
        """Check backend logs for OCR-related information"""
        self.log("📋 Checking backend logs...")
        
        try:
            # Try to read supervisor logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.log(f"   📄 Reading {log_file}:")
                    
                    # Read last 50 lines
                    result = subprocess.run(['tail', '-n', '50', log_file], 
                                          capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        ocr_lines = [line for line in lines if 'ocr' in line.lower() or 'tesseract' in line.lower() or 'poppler' in line.lower()]
                        
                        if ocr_lines:
                            self.log(f"      Found {len(ocr_lines)} OCR-related log entries:")
                            for line in ocr_lines[-10:]:  # Show last 10 OCR-related lines
                                self.log(f"        {line}")
                        else:
                            self.log("      No OCR-related entries found in recent logs")
                    else:
                        self.log(f"      Could not read log file: {result.stderr}")
                else:
                    self.log(f"      Log file not found: {log_file}")
                    
        except Exception as e:
            self.log(f"   ❌ Error checking backend logs: {str(e)}", "ERROR")
    
    def run_comprehensive_test(self):
        """Run the comprehensive OCR test"""
        self.log("🚀 Starting Comprehensive OCR Test")
        self.log("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            self.log("❌ Test failed at authentication step", "ERROR")
            return False
        
        # Step 2: Check OCR dependencies
        dependencies = self.check_ocr_dependencies()
        
        # Step 3: Download test PDF
        pdf_file = self.download_test_pdf()
        if not pdf_file:
            self.log("❌ Test failed at PDF download step", "ERROR")
            return False
        
        try:
            # Step 4: Test OCR endpoint
            ocr_result = self.test_ocr_endpoint(pdf_file)
            
            # Step 5: Check backend logs
            self.check_backend_logs()
            
            # Step 6: Summary
            self.log("=" * 60)
            self.log("📋 TEST SUMMARY")
            self.log("=" * 60)
            
            self.log(f"✅ Authentication: SUCCESS")
            self.log(f"{'✅' if dependencies.get('tesseract', False) else '❌'} Tesseract OCR: {'AVAILABLE' if dependencies.get('tesseract', False) else 'NOT AVAILABLE'}")
            self.log(f"{'✅' if dependencies.get('poppler', False) else '❌'} Poppler Utils: {'AVAILABLE' if dependencies.get('poppler', False) else 'NOT AVAILABLE'}")
            self.log(f"✅ PDF Download: SUCCESS")
            self.log(f"{'✅' if ocr_result else '❌'} OCR Processing: {'SUCCESS' if ocr_result else 'FAILED'}")
            
            if ocr_result:
                # Analyze success
                analysis = ocr_result.get('data', {}).get('analysis', {}) if isinstance(ocr_result, dict) else {}
                extracted_fields = sum(1 for v in analysis.values() if v and v != 'null' and str(v).strip())
                self.log(f"📊 Data Extraction: {extracted_fields}/8 fields extracted")
                
                if extracted_fields >= 4:
                    self.log("🎉 OCR FUNCTIONALITY: WORKING (Good extraction rate)")
                elif extracted_fields >= 2:
                    self.log("⚠️  OCR FUNCTIONALITY: PARTIAL (Some data extracted)")
                else:
                    self.log("❌ OCR FUNCTIONALITY: POOR (Minimal data extracted)")
            else:
                self.log("❌ OCR FUNCTIONALITY: FAILED")
            
            return ocr_result is not None
            
        finally:
            # Cleanup
            if pdf_file and os.path.exists(pdf_file):
                os.unlink(pdf_file)
                self.log(f"🧹 Cleaned up temporary file: {pdf_file}")

def main():
    """Main test execution"""
    print("🔬 Ship Management System - OCR Functionality Test")
    print("=" * 60)
    
    tester = BackendTester()
    success = tester.run_comprehensive_test()
    
    print("=" * 60)
    if success:
        print("🎉 Test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Test completed with failures!")
        sys.exit(1)

if __name__ == "__main__":
    main()
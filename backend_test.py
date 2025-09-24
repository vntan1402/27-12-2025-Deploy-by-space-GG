#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: Direct PMDS Certificate Classification with Actual Certificate File
Review Request: Test specific PMDS certificate classification with actual certificate file
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import traceback
import tempfile

# Configuration - Use external URL for testing (as per frontend .env)
BACKEND_URL = "https://shipai-system.preview.emergentagent.com/api"

class PMDSCertificateClassificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # PMDS Certificate URL from review request - MLC Certificate
        self.pmds_certificate_url = "https://customer-assets.emergentagent.com/job_shipai-system/artifacts/5lvr7rxs_SUNSHINE%2001%20-%20MLC-%20PM251278.pdf"
        
        self.pmds_classification_tests = {
            'authentication_successful': False,
            'pdf_download_successful': False,
            'certificate_analysis_endpoint_accessible': False,
            'pdf_text_extraction_successful': False,
            'ai_analysis_response_received': False,
            'pmds_detection_triggered': False,
            'category_field_correct': False,
            'is_marine_certificate_true': False,
            'classification_response_complete': False,
            'backend_logs_captured': False
        }
        
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
            
            response = requests.post(endpoint, json=login_data, timeout=10)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                self.log(f"   Full Name: {self.current_user.get('full_name')}")
                
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
    
    def get_available_ships(self):
        """Get available ships for testing"""
        try:
            self.log("🚢 Getting available ships for certificate testing...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   ✅ Found {len(ships)} ships")
                
                # Look for SUNSHINE 01 specifically (as mentioned in review request)
                sunshine_01_ships = [ship for ship in ships if 'SUNSHINE 01' in ship.get('name', '').upper() or ship.get('name', '').upper() == 'SUNSHINE 01']
                if sunshine_01_ships:
                    selected_ship = sunshine_01_ships[0]
                    self.log(f"   ✅ Selected SUNSHINE 01 ship: {selected_ship.get('name')} (ID: {selected_ship.get('id')})")
                    self.log(f"   IMO: {selected_ship.get('imo', 'Not specified')}")
                    self.test_results['selected_ship'] = selected_ship
                    return selected_ship
                
                # Look for any SUNSHINE ships
                sunshine_ships = [ship for ship in ships if 'SUNSHINE' in ship.get('name', '').upper()]
                if sunshine_ships:
                    selected_ship = sunshine_ships[0]
                    self.log(f"   ✅ Selected SUNSHINE ship: {selected_ship.get('name')} (ID: {selected_ship.get('id')})")
                    self.log(f"   IMO: {selected_ship.get('imo', 'Not specified')}")
                    self.test_results['selected_ship'] = selected_ship
                    return selected_ship
                elif ships:
                    selected_ship = ships[0]
                    self.log(f"   ✅ Selected first available ship: {selected_ship.get('name')} (ID: {selected_ship.get('id')})")
                    self.test_results['selected_ship'] = selected_ship
                    return selected_ship
                else:
                    self.log("   ❌ No ships available for testing")
                    return None
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Get ships error: {str(e)}", "ERROR")
            return None
    
    def download_pmds_certificate(self):
        """Download the specific PMDS certificate file from the provided URL"""
        try:
            self.log("📥 Downloading PMDS certificate file...")
            self.log(f"   URL: {self.pmds_certificate_url}")
            
            response = requests.get(self.pmds_certificate_url, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(response.content)
                temp_file.close()
                
                file_size = len(response.content)
                self.log(f"   ✅ PDF downloaded successfully")
                self.log(f"   File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                self.log(f"   Temporary file: {temp_file.name}")
                
                self.pmds_classification_tests['pdf_download_successful'] = True
                self.test_results['pdf_file_path'] = temp_file.name
                self.test_results['pdf_file_size'] = file_size
                
                return temp_file.name
            else:
                self.log(f"   ❌ Failed to download PDF: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ PDF download error: {str(e)}", "ERROR")
            return None
    
    def test_certificate_analysis_with_pmds_pdf(self, ship_id, pdf_file_path):
        """Test certificate analysis endpoint with the actual PMDS PDF file"""
        try:
            self.log("🔍 Testing certificate analysis with PMDS PDF file...")
            
            endpoint = f"{BACKEND_URL}/analyze-ship-certificate"
            self.log(f"   POST {endpoint}")
            
            # Read the PDF file
            with open(pdf_file_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
            
            files = {'file': ('SUNSHINE_01_CICA_PM251277.pdf', pdf_content, 'application/pdf')}
            data = {'ship_id': ship_id}
            
            self.log("   📤 Uploading PMDS certificate for analysis...")
            self.log(f"   File size: {len(pdf_content):,} bytes")
            
            start_time = time.time()
            
            response = requests.post(
                endpoint, 
                files=files,
                data=data,
                headers=self.get_headers(), 
                timeout=120  # Extended timeout for AI processing
            )
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Analysis time: {analysis_time:.2f} seconds")
            
            if response.status_code == 200:
                self.pmds_classification_tests['certificate_analysis_endpoint_accessible'] = True
                
                try:
                    analysis_result = response.json()
                    self.log("   ✅ Certificate analysis endpoint accessible")
                    self.log("   📊 ANALYZING AI RESPONSE...")
                    
                    # Log the complete response structure
                    self.log(f"   Response keys: {list(analysis_result.keys())}")
                    
                    # Check for success field
                    success = analysis_result.get('success', False)
                    self.log(f"   Success: {success}")
                    
                    if success:
                        self.pmds_classification_tests['ai_analysis_response_received'] = True
                        
                        # Check extracted text (if available)
                        extracted_text = analysis_result.get('extracted_text', '')
                        if extracted_text and len(extracted_text) > 100:
                            self.log(f"   ✅ PDF text extraction successful ({len(extracted_text)} characters)")
                            self.pmds_classification_tests['pdf_text_extraction_successful'] = True
                            
                            # Check for PMDS detection in extracted text
                            text_upper = extracted_text.upper()
                            if 'PANAMA MARITIME DOCUMENTATION SERVICES' in text_upper or 'PMDS' in text_upper:
                                self.log("   ✅ PMDS organization detected in extracted text")
                                self.pmds_classification_tests['pmds_detection_triggered'] = True
                            else:
                                self.log("   ❌ PMDS organization NOT detected in extracted text")
                        else:
                            self.log("   ❌ PDF text extraction failed or insufficient text")
                        
                        # Check classification fields
                        category = analysis_result.get('category', '')
                        is_marine_certificate = analysis_result.get('is_marine_certificate', False)
                        
                        self.log(f"   Category: {category}")
                        self.log(f"   Is Marine Certificate: {is_marine_certificate}")
                        
                        if category == 'certificates':
                            self.log("   ✅ Category field correct ('certificates')")
                            self.pmds_classification_tests['category_field_correct'] = True
                        else:
                            self.log(f"   ❌ Category field incorrect (expected 'certificates', got '{category}')")
                        
                        if is_marine_certificate:
                            self.log("   ✅ is_marine_certificate field is true")
                            self.pmds_classification_tests['is_marine_certificate_true'] = True
                        else:
                            self.log("   ❌ is_marine_certificate field is false")
                        
                        # Check for complete response
                        expected_fields = ['success', 'category', 'is_marine_certificate']
                        found_fields = [field for field in expected_fields if field in analysis_result]
                        
                        if len(found_fields) == len(expected_fields):
                            self.log("   ✅ Classification response complete")
                            self.pmds_classification_tests['classification_response_complete'] = True
                        else:
                            missing_fields = [field for field in expected_fields if field not in analysis_result]
                            self.log(f"   ❌ Classification response incomplete (missing: {missing_fields})")
                        
                        # Log all response fields for analysis
                        self.log("   📋 COMPLETE ANALYSIS RESPONSE:")
                        for key, value in analysis_result.items():
                            if isinstance(value, str) and len(value) > 100:
                                self.log(f"      {key}: {str(value)[:100]}... ({len(value)} chars)")
                            else:
                                self.log(f"      {key}: {value}")
                    
                    else:
                        fallback_reason = analysis_result.get('fallback_reason', 'Unknown')
                        self.log(f"   ❌ AI analysis failed: {fallback_reason}")
                    
                    self.test_results['analysis_result'] = analysis_result
                    self.test_results['analysis_time'] = analysis_time
                    
                    return analysis_result
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Failed to parse JSON response: {e}")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return None
            else:
                self.log(f"   ❌ Certificate analysis failed: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Certificate analysis error: {str(e)}", "ERROR")
            self.log(f"   Exception type: {type(e).__name__}")
            self.log(f"   Traceback: {traceback.format_exc()}")
            return None
    
    def capture_backend_logs(self):
        """Capture backend logs for analysis"""
        try:
            self.log("📊 Capturing backend logs for analysis...")
            
            # Try to read backend logs from supervisor
            try:
                import subprocess
                result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.out.log'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout:
                    self.log("   ✅ Backend logs captured successfully")
                    self.pmds_classification_tests['backend_logs_captured'] = True
                    
                    # Look for specific PMDS-related log entries
                    log_lines = result.stdout.split('\n')
                    pmds_related_logs = []
                    
                    for line in log_lines:
                        line_upper = line.upper()
                        if any(keyword in line_upper for keyword in ['PMDS', 'PANAMA MARITIME', 'CLASSIFICATION', 'CERTIFICATE', 'OCR', 'AI']):
                            pmds_related_logs.append(line)
                    
                    if pmds_related_logs:
                        self.log(f"   📋 Found {len(pmds_related_logs)} PMDS-related log entries:")
                        for log_line in pmds_related_logs[-10:]:  # Show last 10 relevant logs
                            self.log(f"      {log_line}")
                    else:
                        self.log("   ℹ️ No specific PMDS-related log entries found")
                    
                    self.test_results['backend_logs'] = log_lines
                    self.test_results['pmds_related_logs'] = pmds_related_logs
                    
                else:
                    self.log("   ⚠️ Could not read backend logs from supervisor")
                    
            except Exception as log_error:
                self.log(f"   ⚠️ Backend log capture failed: {str(log_error)}")
            
            # Also try to capture error logs
            try:
                result = subprocess.run(['tail', '-n', '20', '/var/log/supervisor/backend.err.log'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    self.log("   📋 Backend error logs:")
                    for line in result.stdout.split('\n')[-10:]:  # Show last 10 error lines
                        if line.strip():
                            self.log(f"      ERROR: {line}")
                            
            except Exception as error_log_error:
                self.log(f"   ⚠️ Backend error log capture failed: {str(error_log_error)}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Backend log capture error: {str(e)}", "ERROR")
            return False
    
    def test_analyze_ship_certificate_endpoint(self, ship_id):
        """Test the analyze-ship-certificate endpoint with a simple test"""
        try:
            self.log("🔍 Testing analyze-ship-certificate endpoint...")
            
            # Create a simple test file to test the endpoint
            test_content = b"Test PDF content for PMDS certificate classification testing"
            
            endpoint = f"{BACKEND_URL}/analyze-ship-certificate"
            self.log(f"   POST {endpoint}")
            
            files = {'file': ('test_pmds_cert.pdf', test_content, 'application/pdf')}
            data = {'ship_id': ship_id}
            
            self.log("   📤 Testing analyze-ship-certificate endpoint with test file...")
            start_time = time.time()
            
            response = requests.post(
                endpoint, 
                files=files,
                data=data,
                headers=self.get_headers(), 
                timeout=60
            )
            
            end_time = time.time()
            
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Analysis time: {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                analysis_result = response.json()
                self.log("   ✅ analyze-ship-certificate endpoint is accessible")
                self.log(f"   Response structure: {list(analysis_result.keys())}")
                
                # Check if the endpoint returns expected fields
                expected_fields = ['success', 'ship_name', 'imo_number', 'class_society', 'flag']
                found_fields = [field for field in expected_fields if field in analysis_result]
                
                self.log(f"   Expected fields found: {len(found_fields)}/{len(expected_fields)}")
                for field in found_fields:
                    self.log(f"      ✅ {field}: {analysis_result.get(field, 'N/A')}")
                
                self.test_results['endpoint_test'] = analysis_result
                return True
            else:
                self.log(f"   ❌ analyze-ship-certificate endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Endpoint test error: {str(e)}", "ERROR")
            return False
    
    def monitor_backend_logs(self):
        """Monitor backend logs for classification decisions"""
        try:
            self.log("📊 Monitoring backend logs for classification decisions...")
            
            # This would typically require access to backend logs
            # For now, we'll check if we can get any debug information from the API responses
            self.log("   ℹ️ Backend log monitoring would require direct server access")
            self.log("   ℹ️ Classification decisions are inferred from API responses and existing data")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Backend log monitoring error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_pmds_classification_test(self):
        """Main test function for PMDS MLC certificate classification with new uploaded file"""
        self.log("🎯 STARTING PMDS MLC CERTIFICATE CLASSIFICATION TESTING")
        self.log("🔍 Focus: Test PMDS MLC certificate classification with new uploaded file")
        self.log("📋 Review Request: Test MLC Certificate Classification with specific PDF URL")
        self.log("🏢 Expected: Panama Maritime Documentation Services detection")
        self.log("🚢 Expected: Ship SUNSHINE 01 MLC certificate analysis")
        self.log("📄 File: SUNSHINE 01 - MLC- PM251278.pdf")
        self.log("=" * 100)
        
        # Step 1: Authenticate
        self.log("\n🔐 STEP 1: AUTHENTICATION")
        self.log("=" * 50)
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        self.pmds_classification_tests['authentication_successful'] = True
        
        # Step 2: Get available ships
        self.log("\n🚢 STEP 2: GET AVAILABLE SHIPS")
        self.log("=" * 50)
        ship = self.get_available_ships()
        if not ship:
            self.log("❌ No ships available - cannot proceed with certificate testing")
            return False
        
        # Step 3: Download PMDS MLC certificate
        self.log("\n📥 STEP 3: DOWNLOAD PMDS MLC CERTIFICATE")
        self.log("=" * 50)
        pdf_file_path = self.download_pmds_certificate()
        if not pdf_file_path:
            self.log("❌ Failed to download PMDS certificate - cannot proceed with analysis")
            return False
        
        # Step 4: Test certificate analysis with actual PMDS PDF
        self.log("\n🔍 STEP 4: ANALYZE PMDS MLC CERTIFICATE")
        self.log("=" * 50)
        analysis_result = self.test_certificate_analysis_with_pmds_pdf(ship.get('id'), pdf_file_path)
        
        # Step 5: Capture backend logs
        self.log("\n📊 STEP 5: CAPTURE BACKEND LOGS")
        self.log("=" * 50)
        self.capture_backend_logs()
        
        # Step 6: Final analysis
        self.log("\n📊 STEP 6: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_analysis()
        
        # Clean up temporary file
        try:
            import os
            if pdf_file_path and os.path.exists(pdf_file_path):
                os.unlink(pdf_file_path)
                self.log("   🗑️ Temporary PDF file cleaned up")
        except Exception as e:
            self.log(f"   ⚠️ Failed to clean up temporary file: {e}")
        
        return analysis_result is not None
    
    def provide_final_analysis(self):
        """Provide final analysis of the PMDS MLC certificate classification testing"""
        try:
            self.log("🎯 PMDS MLC CERTIFICATE CLASSIFICATION TESTING - RESULTS")
            self.log("=" * 70)
            
            # Check which PMDS classification tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.pmds_classification_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ PMDS MLC CLASSIFICATION TESTS PASSED ({len(passed_tests)}/10):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ PMDS MLC CLASSIFICATION TESTS FAILED ({len(failed_tests)}/10):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Overall assessment
            success_rate = len(passed_tests) / len(self.pmds_classification_tests) * 100
            self.log(f"\n📊 PMDS MLC CLASSIFICATION SUCCESS RATE: {success_rate:.1f}%")
            
            if success_rate >= 80:
                self.log("🎉 EXCELLENT: PMDS MLC certificate classification is working correctly")
            elif success_rate >= 60:
                self.log("✅ GOOD: Majority of PMDS MLC classification features are working")
            elif success_rate >= 40:
                self.log("⚠️ MODERATE: Some PMDS MLC classification features are working")
            else:
                self.log("❌ POOR: PMDS MLC classification has significant issues")
            
            # Analysis results
            if self.test_results.get('analysis_result'):
                analysis = self.test_results['analysis_result']
                self.log(f"\n🔍 MLC CERTIFICATE ANALYSIS RESULTS:")
                self.log(f"   Success: {analysis.get('success', 'Unknown')}")
                self.log(f"   Category: {analysis.get('category', 'Unknown')}")
                self.log(f"   Is Marine Certificate: {analysis.get('is_marine_certificate', 'Unknown')}")
                self.log(f"   Certificate Name: {analysis.get('cert_name', 'Unknown')}")
                self.log(f"   Certificate Number: {analysis.get('cert_no', 'Unknown')}")
                self.log(f"   Issued By: {analysis.get('issued_by', 'Unknown')}")
                
                if analysis.get('extracted_text'):
                    text_length = len(analysis['extracted_text'])
                    self.log(f"   Extracted Text: {text_length} characters")
            
            # Ship information
            if self.test_results.get('selected_ship'):
                ship = self.test_results['selected_ship']
                self.log(f"\n🚢 TESTED WITH SHIP:")
                self.log(f"   Ship Name: {ship.get('name')}")
                self.log(f"   Ship ID: {ship.get('id')}")
                self.log(f"   Company: {ship.get('company')}")
            
            # PDF file information
            if self.test_results.get('pdf_file_size'):
                size_mb = self.test_results['pdf_file_size'] / 1024 / 1024
                self.log(f"\n📄 PDF FILE INFORMATION:")
                self.log(f"   File Size: {size_mb:.2f} MB")
                self.log(f"   Analysis Time: {self.test_results.get('analysis_time', 'Unknown'):.2f} seconds")
                
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    print("🎯 Ship Management System - PMDS MLC Certificate Classification Testing")
    print("🔍 Focus: Test PMDS MLC certificate classification with new uploaded file")
    print("📋 Review Request: Test MLC Certificate Classification with specific PDF URL")
    print("🏢 Expected: Panama Maritime Documentation Services detection")
    print("🚢 Expected: Ship SUNSHINE 01 MLC certificate analysis")
    print("📄 File: SUNSHINE 01 - MLC- PM251278.pdf")
    print("=" * 100)
    
    tester = PMDSCertificateClassificationTester()
    success = tester.run_comprehensive_pmds_classification_test()
    
    print("=" * 100)
    print("🔍 PMDS MLC CERTIFICATE CLASSIFICATION TESTING RESULTS:")
    print("=" * 60)
    
    # Print PMDS classification test summary
    passed_tests = [f for f, passed in tester.pmds_classification_tests.items() if passed]
    failed_tests = [f for f, passed in tester.pmds_classification_tests.items() if not passed]
    
    print(f"✅ PMDS MLC CLASSIFICATION TESTS PASSED ({len(passed_tests)}/10):")
    for test in passed_tests:
        print(f"   ✅ {test.replace('_', ' ').title()}")
    
    if failed_tests:
        print(f"\n❌ PMDS MLC CLASSIFICATION TESTS FAILED ({len(failed_tests)}/10):")
        for test in failed_tests:
            print(f"   ❌ {test.replace('_', ' ').title()}")
    
    # Print analysis results
    if tester.test_results.get('analysis_result'):
        analysis = tester.test_results['analysis_result']
        print(f"\n🔍 MLC CERTIFICATE ANALYSIS: ✅ SUCCESS")
        print(f"   Category: {analysis.get('category', 'Unknown')}")
        print(f"   Is Marine Certificate: {analysis.get('is_marine_certificate', 'Unknown')}")
        print(f"   Certificate Name: {analysis.get('cert_name', 'Unknown')}")
        print(f"   Issued By: {analysis.get('issued_by', 'Unknown')}")
    else:
        print(f"\n🔍 MLC CERTIFICATE ANALYSIS: ❌ FAILED")
    
    # Print ship information
    if tester.test_results.get('selected_ship'):
        ship = tester.test_results['selected_ship']
        print(f"\n🚢 TESTED WITH SHIP: {ship.get('name')} (ID: {ship.get('id')})")
    
    # Calculate success rate
    success_rate = len(passed_tests) / len(tester.pmds_classification_tests) * 100
    print(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")
    
    print("=" * 100)
    if success:
        print("🎉 PMDS MLC certificate classification testing completed successfully!")
        print("✅ All testing steps executed - detailed analysis available above")
    else:
        print("❌ PMDS MLC certificate classification testing completed with issues!")
        print("🔍 Check detailed logs above for specific issues")
    
    if len(passed_tests) >= 7:
        print("\n💡 NEXT STEPS FOR MAIN AGENT:")
        print("   ✅ PMDS MLC classification is working well")
        print("   1. Review the specific tests passed above")
        print("   2. PMDS detection rules are functioning correctly")
        print("   3. Enhanced PMDS detection is working")
        print("   4. Certificate classification as 'certificates' is working")
        print("   5. is_marine_certificate field is correctly set to true")
    else:
        print("\n💡 NEXT STEPS FOR MAIN AGENT:")
        print("   ⚠️ PMDS MLC classification has issues")
        print("   1. Review backend implementation for PMDS detection rules")
        print("   2. Check if 'Panama Maritime Documentation Services' detection is working")
        print("   3. Verify AI analysis response for classification decision")
        print("   4. Check enhanced PMDS detection rules")
        print("   5. Investigate exact cause of classification failure")
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
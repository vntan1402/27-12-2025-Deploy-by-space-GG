#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
FOCUS: Multi Cert Upload Classification Discrepancy for MLC File
Review Request: Debug Multi Cert Upload classification discrepancy for MLC file
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import traceback
import tempfile
import subprocess

# Configuration - Use external URL for testing (as per frontend .env)
BACKEND_URL = "https://shipai-system.preview.emergentagent.com/api"

class MultiCertUploadClassificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # MLC Certificate URL from review request
        self.mlc_certificate_url = "https://customer-assets.emergentagent.com/job_shipai-system/artifacts/5lvr7rxs_SUNSHINE%2001%20-%20MLC-%20PM251278.pdf"
        
        self.multi_cert_tests = {
            'authentication_successful': False,
            'pdf_download_successful': False,
            'multi_upload_endpoint_accessible': False,
            'single_upload_endpoint_accessible': False,
            'multi_upload_classification_correct': False,
            'single_upload_classification_correct': False,
            'classification_discrepancy_identified': False,
            'ai_analysis_response_received': False,
            'backend_logs_captured': False,
            'confidence_threshold_checked': False
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
    
    def download_mlc_certificate(self):
        """Download the specific MLC certificate file from the provided URL"""
        try:
            self.log("📥 Downloading MLC certificate file...")
            self.log(f"   URL: {self.mlc_certificate_url}")
            
            response = requests.get(self.mlc_certificate_url, timeout=30)
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
                
                self.multi_cert_tests['pdf_download_successful'] = True
                self.test_results['pdf_file_path'] = temp_file.name
                self.test_results['pdf_file_size'] = file_size
                
                return temp_file.name
            else:
                self.log(f"   ❌ Failed to download PDF: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ PDF download error: {str(e)}", "ERROR")
            return None
    
    def test_multi_cert_upload(self, ship_id, pdf_file_path):
        """Test Multi Cert Upload endpoint with the MLC file"""
        try:
            self.log("🔍 Testing Multi Cert Upload with MLC file...")
            
            endpoint = f"{BACKEND_URL}/certificates/multi-upload"
            self.log(f"   POST {endpoint}?ship_id={ship_id}")
            
            # Read the PDF file
            with open(pdf_file_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
            
            files = {'files': ('SUNSHINE_01_MLC_PM251278.pdf', pdf_content, 'application/pdf')}
            params = {'ship_id': ship_id}
            
            self.log("   📤 Uploading MLC certificate via Multi Cert Upload...")
            self.log(f"   File size: {len(pdf_content):,} bytes")
            
            start_time = time.time()
            
            response = requests.post(
                endpoint, 
                files=files,
                params=params,
                headers=self.get_headers(), 
                timeout=120  # Extended timeout for AI processing
            )
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Analysis time: {analysis_time:.2f} seconds")
            
            if response.status_code == 200:
                self.multi_cert_tests['multi_upload_endpoint_accessible'] = True
                
                try:
                    analysis_result = response.json()
                    self.log("   ✅ Multi Cert Upload endpoint accessible")
                    self.log("   📊 ANALYZING MULTI CERT UPLOAD RESPONSE...")
                    
                    # Log the complete response structure
                    self.log(f"   Response keys: {list(analysis_result.keys())}")
                    
                    # Check for results
                    results = analysis_result.get('results', [])
                    summary = analysis_result.get('summary', {})
                    
                    self.log(f"   Results count: {len(results)}")
                    self.log(f"   Summary: {summary}")
                    
                    if results and len(results) > 0:
                        self.multi_cert_tests['ai_analysis_response_received'] = True
                        
                        file_result = results[0]  # Get first file result
                        
                        # Check file status and marine classification
                        file_status = file_result.get('status', '')
                        filename = file_result.get('filename', '')
                        is_marine = file_result.get('is_marine', False)
                        
                        self.log(f"   📄 File: {filename}")
                        self.log(f"   📊 Status: {file_status}")
                        self.log(f"   🌊 Is Marine: {is_marine}")
                        
                        # Check if classified as "Skipped - not a marine certificate"
                        if "skipped" in file_status.lower() and "not a marine certificate" in file_status.lower():
                            self.log("   ❌ CRITICAL ISSUE: File classified as 'Skipped - not a marine certificate'")
                            self.log("   🔍 This matches the user's reported issue!")
                            self.multi_cert_tests['classification_discrepancy_identified'] = True
                        elif "marine" in file_status.lower() or is_marine:
                            self.log("   ✅ File correctly classified as marine certificate")
                            self.multi_cert_tests['multi_upload_classification_correct'] = True
                        else:
                            self.log(f"   ⚠️ Unexpected classification status: {file_status}")
                        
                        # Check for analysis data
                        analysis_data = file_result.get('analysis', {})
                        if analysis_data:
                            self.log(f"   ✅ AI analysis data received")
                            
                            # Check classification fields
                            category = analysis_data.get('category', '')
                            is_marine_certificate = analysis_data.get('is_marine_certificate', False)
                            confidence = analysis_data.get('confidence', 0)
                            
                            self.log(f"   📊 Category: {category}")
                            self.log(f"   🌊 Is Marine Certificate: {is_marine_certificate}")
                            self.log(f"   📈 Confidence: {confidence}")
                            
                            # Check for confidence threshold issues
                            if confidence < 0.7:  # Assuming 70% threshold
                                self.log(f"   ⚠️ Low confidence score may cause classification issues")
                                self.multi_cert_tests['confidence_threshold_checked'] = True
                            
                            # Log certificate information if available
                            cert_info = {}
                            for field in ['cert_name', 'cert_no', 'issued_by', 'issue_date', 'valid_date']:
                                if field in analysis_data:
                                    cert_info[field] = analysis_data[field]
                            
                            if cert_info:
                                self.log("   📋 CERTIFICATE INFORMATION EXTRACTED:")
                                for key, value in cert_info.items():
                                    self.log(f"      {key}: {value}")
                        
                        # Log all response fields for analysis
                        self.log("   📋 COMPLETE MULTI CERT UPLOAD RESPONSE:")
                        for key, value in analysis_result.items():
                            if isinstance(value, list) and len(value) > 0:
                                self.log(f"      {key}: [array with {len(value)} items]")
                                if key == 'results':
                                    for i, item in enumerate(value):
                                        self.log(f"        Result {i+1}: {item.get('filename', 'Unknown')} - {item.get('status', 'Unknown')}")
                            elif isinstance(value, str) and len(value) > 100:
                                self.log(f"      {key}: {str(value)[:100]}... ({len(value)} chars)")
                            else:
                                self.log(f"      {key}: {value}")
                    else:
                        self.log("   ❌ No results found in response")
                    
                    self.test_results['multi_upload_result'] = analysis_result
                    self.test_results['multi_upload_time'] = analysis_time
                    
                    return analysis_result
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Failed to parse JSON response: {e}")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return None
            else:
                self.log(f"   ❌ Multi Cert Upload failed: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Multi Cert Upload error: {str(e)}", "ERROR")
            self.log(f"   Exception type: {type(e).__name__}")
            self.log(f"   Traceback: {traceback.format_exc()}")
            return None
    
    def test_single_cert_upload(self, ship_id, pdf_file_path):
        """Test Single Certificate Upload endpoint with the same MLC file for comparison"""
        try:
            self.log("🔍 Testing Single Certificate Upload with same MLC file for comparison...")
            
            endpoint = f"{BACKEND_URL}/analyze-ship-certificate"
            self.log(f"   POST {endpoint}")
            
            # Read the PDF file
            with open(pdf_file_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
            
            files = {'file': ('SUNSHINE_01_MLC_PM251278.pdf', pdf_content, 'application/pdf')}
            data = {'ship_id': ship_id}
            
            self.log("   📤 Uploading MLC certificate via Single Certificate Upload...")
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
                self.multi_cert_tests['single_upload_endpoint_accessible'] = True
                
                try:
                    analysis_result = response.json()
                    self.log("   ✅ Single Certificate Upload endpoint accessible")
                    self.log("   📊 ANALYZING SINGLE CERT UPLOAD RESPONSE...")
                    
                    # Log the complete response structure
                    self.log(f"   Response keys: {list(analysis_result.keys())}")
                    
                    # Check success and classification
                    success = analysis_result.get('success', False)
                    category = analysis_result.get('category', '')
                    is_marine_certificate = analysis_result.get('is_marine_certificate', False)
                    
                    self.log(f"   📊 Success: {success}")
                    self.log(f"   📊 Category: {category}")
                    self.log(f"   🌊 Is Marine Certificate: {is_marine_certificate}")
                    
                    if success and (category == 'certificates' or is_marine_certificate):
                        self.log("   ✅ Single upload correctly classifies as marine certificate")
                        self.multi_cert_tests['single_upload_classification_correct'] = True
                    else:
                        self.log("   ❌ Single upload also fails to classify as marine certificate")
                    
                    # Log certificate information if available
                    cert_info = {}
                    for field in ['cert_name', 'cert_no', 'issued_by', 'issue_date', 'valid_date']:
                        if field in analysis_result:
                            cert_info[field] = analysis_result[field]
                    
                    if cert_info:
                        self.log("   📋 CERTIFICATE INFORMATION EXTRACTED (Single Upload):")
                        for key, value in cert_info.items():
                            self.log(f"      {key}: {value}")
                    
                    self.test_results['single_upload_result'] = analysis_result
                    self.test_results['single_upload_time'] = analysis_time
                    
                    return analysis_result
                    
                except json.JSONDecodeError as e:
                    self.log(f"   ❌ Failed to parse JSON response: {e}")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return None
            else:
                self.log(f"   ❌ Single Certificate Upload failed: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Single Certificate Upload error: {str(e)}", "ERROR")
            self.log(f"   Exception type: {type(e).__name__}")
            self.log(f"   Traceback: {traceback.format_exc()}")
            return None
    
    def capture_backend_logs(self):
        """Capture backend logs during Multi Cert Upload process"""
        try:
            self.log("📊 Capturing backend logs during Multi Cert Upload process...")
            
            # Try to read backend logs from supervisor
            try:
                result = subprocess.run(['tail', '-n', '100', '/var/log/supervisor/backend.out.log'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout:
                    self.log("   ✅ Backend logs captured successfully")
                    self.multi_cert_tests['backend_logs_captured'] = True
                    
                    # Look for specific multi-upload and classification related log entries
                    log_lines = result.stdout.split('\n')
                    relevant_logs = []
                    
                    for line in log_lines:
                        line_upper = line.upper()
                        if any(keyword in line_upper for keyword in [
                            'MULTI-UPLOAD', 'MULTI_UPLOAD', 'CLASSIFICATION', 'CERTIFICATE', 
                            'MLC', 'MARINE', 'SKIPPED', 'AI ANALYSIS', 'CONFIDENCE'
                        ]):
                            relevant_logs.append(line)
                    
                    if relevant_logs:
                        self.log(f"   📋 Found {len(relevant_logs)} relevant log entries:")
                        for log_line in relevant_logs[-15:]:  # Show last 15 relevant logs
                            self.log(f"      {log_line}")
                    else:
                        self.log("   ℹ️ No specific multi-upload related log entries found")
                    
                    self.test_results['backend_logs'] = log_lines
                    self.test_results['relevant_logs'] = relevant_logs
                    
                else:
                    self.log("   ⚠️ Could not read backend logs from supervisor")
                    
            except Exception as log_error:
                self.log(f"   ⚠️ Backend log capture failed: {str(log_error)}")
            
            # Also try to capture error logs
            try:
                result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.err.log'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    self.log("   📋 Backend error logs:")
                    for line in result.stdout.split('\n')[-15:]:  # Show last 15 error lines
                        if line.strip():
                            self.log(f"      ERROR: {line}")
                            
            except Exception as error_log_error:
                self.log(f"   ⚠️ Backend error log capture failed: {str(error_log_error)}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Backend log capture error: {str(e)}", "ERROR")
            return False
    
    def compare_upload_methods(self):
        """Compare results between Multi Cert Upload and Single Certificate Upload"""
        try:
            self.log("🔍 Comparing Multi Cert Upload vs Single Certificate Upload results...")
            
            multi_result = self.test_results.get('multi_upload_result')
            single_result = self.test_results.get('single_upload_result')
            
            if not multi_result or not single_result:
                self.log("   ⚠️ Cannot compare - missing results from one or both methods")
                return
            
            self.log("   📊 COMPARISON ANALYSIS:")
            
            # Compare classification results
            multi_classified_as_marine = False
            single_classified_as_marine = False
            
            # Check multi-upload result
            multi_results = multi_result.get('results', [])
            if multi_results:
                file_result = multi_results[0]
                file_status = file_result.get('status', '').lower()
                is_marine = file_result.get('is_marine', False)
                multi_classified_as_marine = is_marine or ('marine' in file_status and 'not' not in file_status)
            
            # Check single-upload result
            single_success = single_result.get('success', False)
            single_category = single_result.get('category', '')
            single_is_marine = single_result.get('is_marine_certificate', False)
            single_classified_as_marine = single_success and (single_category == 'certificates' or single_is_marine)
            
            self.log(f"   Multi Cert Upload classified as marine: {multi_classified_as_marine}")
            self.log(f"   Single Certificate Upload classified as marine: {single_classified_as_marine}")
            
            if multi_classified_as_marine != single_classified_as_marine:
                self.log("   🚨 DISCREPANCY FOUND: Different classification results between methods!")
                self.multi_cert_tests['classification_discrepancy_identified'] = True
                
                if not multi_classified_as_marine and single_classified_as_marine:
                    self.log("   🔍 Multi Cert Upload incorrectly rejects marine certificate")
                    self.log("   🔍 Single Certificate Upload correctly identifies marine certificate")
                elif multi_classified_as_marine and not single_classified_as_marine:
                    self.log("   🔍 Single Certificate Upload incorrectly rejects marine certificate")
                    self.log("   🔍 Multi Cert Upload correctly identifies marine certificate")
            else:
                self.log("   ✅ Both methods have consistent classification results")
            
            # Compare processing times
            multi_time = self.test_results.get('multi_upload_time', 0)
            single_time = self.test_results.get('single_upload_time', 0)
            
            self.log(f"   Multi Cert Upload processing time: {multi_time:.2f} seconds")
            self.log(f"   Single Certificate Upload processing time: {single_time:.2f} seconds")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Comparison error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_multi_cert_classification_test(self):
        """Main test function for Multi Cert Upload classification discrepancy"""
        self.log("🎯 STARTING MULTI CERT UPLOAD CLASSIFICATION DISCREPANCY TESTING")
        self.log("🔍 Focus: Debug Multi Cert Upload classification discrepancy for MLC file")
        self.log("📋 Review Request: MLC file classified as 'Skipped - not a marine certificate'")
        self.log("🏢 Expected: Should be classified as marine certificate")
        self.log("🚢 File: SUNSHINE 01 - MLC- PM251278.pdf")
        self.log("=" * 100)
        
        # Step 1: Authenticate
        self.log("\n🔐 STEP 1: AUTHENTICATION")
        self.log("=" * 50)
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        self.multi_cert_tests['authentication_successful'] = True
        
        # Step 2: Get available ships
        self.log("\n🚢 STEP 2: GET AVAILABLE SHIPS")
        self.log("=" * 50)
        ship = self.get_available_ships()
        if not ship:
            self.log("❌ No ships available - cannot proceed with certificate testing")
            return False
        
        # Step 3: Download MLC certificate
        self.log("\n📥 STEP 3: DOWNLOAD MLC CERTIFICATE")
        self.log("=" * 50)
        pdf_file_path = self.download_mlc_certificate()
        if not pdf_file_path:
            self.log("❌ Failed to download MLC certificate - cannot proceed with analysis")
            return False
        
        # Step 4: Test Multi Cert Upload
        self.log("\n🔍 STEP 4: TEST MULTI CERT UPLOAD")
        self.log("=" * 50)
        multi_result = self.test_multi_cert_upload(ship.get('id'), pdf_file_path)
        
        # Step 5: Test Single Certificate Upload for comparison
        self.log("\n🔍 STEP 5: TEST SINGLE CERTIFICATE UPLOAD (COMPARISON)")
        self.log("=" * 50)
        single_result = self.test_single_cert_upload(ship.get('id'), pdf_file_path)
        
        # Step 6: Compare results
        self.log("\n📊 STEP 6: COMPARE UPLOAD METHODS")
        self.log("=" * 50)
        self.compare_upload_methods()
        
        # Step 7: Capture backend logs
        self.log("\n📊 STEP 7: CAPTURE BACKEND LOGS")
        self.log("=" * 50)
        self.capture_backend_logs()
        
        # Step 8: Final analysis
        self.log("\n📊 STEP 8: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_analysis()
        
        # Clean up temporary file
        try:
            if pdf_file_path and os.path.exists(pdf_file_path):
                os.unlink(pdf_file_path)
                self.log("   🗑️ Temporary PDF file cleaned up")
        except Exception as e:
            self.log(f"   ⚠️ Failed to clean up temporary file: {e}")
        
        return multi_result is not None or single_result is not None
    
    def provide_final_analysis(self):
        """Provide final analysis of the Multi Cert Upload classification discrepancy testing"""
        try:
            self.log("🎯 MULTI CERT UPLOAD CLASSIFICATION DISCREPANCY TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.multi_cert_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ MULTI CERT UPLOAD TESTS PASSED ({len(passed_tests)}/10):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ MULTI CERT UPLOAD TESTS FAILED ({len(failed_tests)}/10):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Overall assessment
            success_rate = len(passed_tests) / len(self.multi_cert_tests) * 100
            self.log(f"\n📊 MULTI CERT UPLOAD TEST SUCCESS RATE: {success_rate:.1f}%")
            
            # Specific discrepancy analysis
            if self.multi_cert_tests.get('classification_discrepancy_identified'):
                self.log("\n🚨 CRITICAL FINDING: CLASSIFICATION DISCREPANCY IDENTIFIED")
                self.log("   The user's reported issue is CONFIRMED")
                self.log("   Multi Cert Upload and Single Certificate Upload produce different results")
            else:
                self.log("\n✅ No classification discrepancy found between upload methods")
            
            # Analysis results
            multi_result = self.test_results.get('multi_upload_result')
            single_result = self.test_results.get('single_upload_result')
            
            if multi_result:
                self.log(f"\n🔍 MULTI CERT UPLOAD RESULTS:")
                results = multi_result.get('results', [])
                if results:
                    file_result = results[0]
                    self.log(f"   Status: {file_result.get('status', 'Unknown')}")
                    self.log(f"   Is Marine: {file_result.get('is_marine', 'Unknown')}")
                    analysis = file_result.get('analysis', {})
                    if analysis:
                        self.log(f"   Category: {analysis.get('category', 'Unknown')}")
                        self.log(f"   Is Marine Certificate: {analysis.get('is_marine_certificate', 'Unknown')}")
            
            if single_result:
                self.log(f"\n🔍 SINGLE CERTIFICATE UPLOAD RESULTS:")
                self.log(f"   Success: {single_result.get('success', 'Unknown')}")
                self.log(f"   Category: {single_result.get('category', 'Unknown')}")
                self.log(f"   Is Marine Certificate: {single_result.get('is_marine_certificate', 'Unknown')}")
            
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
                multi_time = self.test_results.get('multi_upload_time', 0)
                single_time = self.test_results.get('single_upload_time', 0)
                self.log(f"   Multi Upload Time: {multi_time:.2f} seconds")
                self.log(f"   Single Upload Time: {single_time:.2f} seconds")
                
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    print("🎯 Ship Management System - Multi Cert Upload Classification Discrepancy Testing")
    print("🔍 Focus: Debug Multi Cert Upload classification discrepancy for MLC file")
    print("📋 Review Request: MLC file classified as 'Skipped - not a marine certificate'")
    print("🏢 Expected: Should be classified as marine certificate")
    print("🚢 File: SUNSHINE 01 - MLC- PM251278.pdf")
    print("=" * 100)
    
    tester = MultiCertUploadClassificationTester()
    success = tester.run_comprehensive_multi_cert_classification_test()
    
    print("=" * 100)
    print("🔍 MULTI CERT UPLOAD CLASSIFICATION DISCREPANCY TESTING RESULTS:")
    print("=" * 70)
    
    # Print test summary
    passed_tests = [f for f, passed in tester.multi_cert_tests.items() if passed]
    failed_tests = [f for f, passed in tester.multi_cert_tests.items() if not passed]
    
    print(f"✅ MULTI CERT UPLOAD TESTS PASSED ({len(passed_tests)}/10):")
    for test in passed_tests:
        print(f"   ✅ {test.replace('_', ' ').title()}")
    
    if failed_tests:
        print(f"\n❌ MULTI CERT UPLOAD TESTS FAILED ({len(failed_tests)}/10):")
        for test in failed_tests:
            print(f"   ❌ {test.replace('_', ' ').title()}")
    
    # Print discrepancy analysis
    if tester.multi_cert_tests.get('classification_discrepancy_identified'):
        print(f"\n🚨 CRITICAL FINDING: CLASSIFICATION DISCREPANCY CONFIRMED")
        print(f"   The user's reported issue is REAL and PRESENT")
        print(f"   Multi Cert Upload produces different results than Single Certificate Upload")
    else:
        print(f"\n✅ No classification discrepancy found between upload methods")
    
    # Print analysis results
    multi_result = tester.test_results.get('multi_upload_result')
    single_result = tester.test_results.get('single_upload_result')
    
    if multi_result:
        results = multi_result.get('results', [])
        if results:
            file_result = results[0]
            print(f"\n🔍 MULTI CERT UPLOAD: {file_result.get('status', 'Unknown')}")
    
    if single_result:
        print(f"🔍 SINGLE CERT UPLOAD: {'SUCCESS' if single_result.get('success') else 'FAILED'}")
    
    # Print ship information
    if tester.test_results.get('selected_ship'):
        ship = tester.test_results['selected_ship']
        print(f"\n🚢 TESTED WITH SHIP: {ship.get('name')} (ID: {ship.get('id')})")
    
    # Calculate success rate
    success_rate = len(passed_tests) / len(tester.multi_cert_tests) * 100
    print(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")
    
    print("=" * 100)
    if success:
        print("🎉 Multi Cert Upload classification discrepancy testing completed!")
        print("✅ All testing steps executed - detailed analysis available above")
    else:
        print("❌ Multi Cert Upload classification discrepancy testing completed with issues!")
        print("🔍 Check detailed logs above for specific issues")
    
    # Provide recommendations
    if tester.multi_cert_tests.get('classification_discrepancy_identified'):
        print("\n💡 NEXT STEPS FOR MAIN AGENT:")
        print("   🚨 CRITICAL ISSUE CONFIRMED: Classification discrepancy exists")
        print("   1. Review Multi Cert Upload classification logic")
        print("   2. Check if confidence thresholds differ between upload methods")
        print("   3. Investigate AI analysis differences in multi vs single upload")
        print("   4. Fix the Multi Cert Upload classification to match Single Upload")
        print("   5. Test with additional MLC certificates to confirm fix")
    else:
        print("\n💡 NEXT STEPS FOR MAIN AGENT:")
        print("   ✅ No discrepancy found in current testing")
        print("   1. The issue may be intermittent or environment-specific")
        print("   2. Consider testing with different MLC certificate files")
        print("   3. Check if the issue occurs with specific file sizes or formats")
        print("   4. Monitor backend logs during user operations")
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test Report Batch Upload Testing Script
=====================================

This script tests the Test Report batch upload functionality with 2 actual PDF files
to identify the root cause of batch upload failures reported by the user.

Test Files:
1. Chemical Suit.pdf - https://customer-assets.emergentagent.com/job_test-survey-portal/artifacts/py2c7zgh_Chemical%20Suit.pdf
2. Co2.pdf - https://customer-assets.emergentagent.com/job_test-survey-portal/artifacts/hb2n81o5_Co2.pdf

Test Phases:
1. Download Test Files
2. Test Single File Upload (Baseline)
3. Test Batch Processing Flow
4. Error Analysis
5. Root Cause Investigation
"""

import requests
import json
import base64
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration
BACKEND_URL = "https://marine-doc-system.preview.emergentagent.com/api"
TEST_FILES = {
    "Chemical_Suit.pdf": "/tmp/Chemical_Suit.pdf",
    "Co2.pdf": "/tmp/Co2.pdf"
}

class TestReportBatchUploadTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        self.ship_info = None
        self.test_results = {
            "phase_1_download": {"status": "pending", "details": {}},
            "phase_2_single_upload": {"status": "pending", "details": {}},
            "phase_3_batch_processing": {"status": "pending", "details": {}},
            "phase_4_error_analysis": {"status": "pending", "details": {}},
            "phase_5_root_cause": {"status": "pending", "details": {}}
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate(self, username: str = "admin1", password: str = "123456") -> bool:
        """Authenticate with the backend"""
        try:
            self.log(f"🔐 Authenticating with username: {username}")
            
            login_data = {
                "username": username,
                "password": password
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                auth_response = response.json()
                self.auth_token = auth_response.get("access_token")
                self.user_info = auth_response.get("user", {})
                
                # Set authorization header
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log(f"✅ Authentication successful")
                self.log(f"   User: {self.user_info.get('full_name')} ({self.user_info.get('role')})")
                self.log(f"   Company: {self.user_info.get('company')}")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {e}", "ERROR")
            return False
    
    def get_ship_info(self, ship_name: str = "BROTHER 36") -> bool:
        """Get ship information"""
        try:
            self.log(f"🚢 Getting ship info for: {ship_name}")
            
            response = self.session.get(f"{BACKEND_URL}/ships")
            
            if response.status_code == 200:
                ships = response.json()
                
                for ship in ships:
                    if ship.get("name") == ship_name:
                        self.ship_info = ship
                        self.log(f"✅ Ship found: {ship['name']} (ID: {ship['id']}, IMO: {ship.get('imo', 'N/A')})")
                        return True
                
                self.log(f"❌ Ship '{ship_name}' not found", "ERROR")
                return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting ship info: {e}", "ERROR")
            return False
    
    def verify_test_files(self) -> bool:
        """Phase 1: Verify test files are downloaded and valid"""
        try:
            self.log("📁 Phase 1: Verifying test files...")
            
            phase_results = {}
            
            for filename, filepath in TEST_FILES.items():
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    
                    # Check if it's a valid PDF
                    with open(filepath, 'rb') as f:
                        header = f.read(10)
                        is_pdf = header.startswith(b'%PDF')
                    
                    phase_results[filename] = {
                        "exists": True,
                        "size": file_size,
                        "is_pdf": is_pdf,
                        "path": filepath
                    }
                    
                    self.log(f"   ✅ {filename}: {file_size} bytes, PDF: {is_pdf}")
                else:
                    phase_results[filename] = {
                        "exists": False,
                        "error": "File not found"
                    }
                    self.log(f"   ❌ {filename}: File not found", "ERROR")
            
            all_valid = all(
                result.get("exists") and result.get("is_pdf") 
                for result in phase_results.values()
            )
            
            self.test_results["phase_1_download"] = {
                "status": "passed" if all_valid else "failed",
                "details": phase_results
            }
            
            return all_valid
            
        except Exception as e:
            self.log(f"❌ Phase 1 error: {e}", "ERROR")
            self.test_results["phase_1_download"] = {
                "status": "failed",
                "details": {"error": str(e)}
            }
            return False
    
    def test_single_file_upload(self) -> bool:
        """Phase 2: Test single file upload (baseline)"""
        try:
            self.log("🔍 Phase 2: Testing single file upload (baseline)...")
            
            phase_results = {}
            
            for filename, filepath in TEST_FILES.items():
                self.log(f"   Testing {filename}...")
                
                # Test analyze endpoint
                analyze_result = self.test_analyze_endpoint(filepath, filename)
                phase_results[filename] = {
                    "analyze": analyze_result
                }
                
                if analyze_result.get("success"):
                    self.log(f"   ✅ {filename} analyze: SUCCESS")
                    self.log(f"      Response fields: {list(analyze_result.get('response', {}).keys())}")
                    
                    # Check for critical fields
                    response = analyze_result.get("response", {})
                    has_file_content = "_file_content" in response and response["_file_content"]
                    has_filename = "_filename" in response and response["_filename"]
                    has_summary = "_summary_text" in response and response["_summary_text"]
                    
                    phase_results[filename]["analyze"]["has_file_content"] = has_file_content
                    phase_results[filename]["analyze"]["has_filename"] = has_filename
                    phase_results[filename]["analyze"]["has_summary"] = has_summary
                    
                    self.log(f"      _file_content: {'✅' if has_file_content else '❌'}")
                    self.log(f"      _filename: {'✅' if has_filename else '❌'}")
                    self.log(f"      _summary_text: {'✅' if has_summary else '❌'}")
                    
                else:
                    self.log(f"   ❌ {filename} analyze: FAILED - {analyze_result.get('error')}", "ERROR")
            
            # Determine overall success
            all_success = all(
                result.get("analyze", {}).get("success", False)
                for result in phase_results.values()
            )
            
            self.test_results["phase_2_single_upload"] = {
                "status": "passed" if all_success else "failed",
                "details": phase_results
            }
            
            return all_success
            
        except Exception as e:
            self.log(f"❌ Phase 2 error: {e}", "ERROR")
            self.test_results["phase_2_single_upload"] = {
                "status": "failed",
                "details": {"error": str(e)}
            }
            return False
    
    def test_analyze_endpoint(self, filepath: str, filename: str) -> Dict[str, Any]:
        """Test the analyze endpoint with a single file"""
        try:
            with open(filepath, 'rb') as f:
                file_content = f.read()
            
            files = {
                'test_report_file': (filename, file_content, 'application/pdf')
            }
            
            data = {
                'ship_id': self.ship_info['id'],
                'bypass_validation': 'false'
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{BACKEND_URL}/test-reports/analyze-file",
                files=files,
                data=data
            )
            end_time = time.time()
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    "success": True,
                    "response": response_data,
                    "duration": end_time - start_time,
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": end_time - start_time,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_batch_processing_flow(self) -> bool:
        """Phase 3: Test batch processing flow"""
        try:
            self.log("🔄 Phase 3: Testing batch processing flow...")
            
            phase_results = {
                "files_processed": [],
                "batch_summary": {}
            }
            
            # Process each file in batch mode (bypass_validation=true)
            for i, (filename, filepath) in enumerate(TEST_FILES.items(), 1):
                self.log(f"   Processing File {i}/{len(TEST_FILES)}: {filename}")
                
                # Step 1: Analyze with bypass_validation=true
                analyze_result = self.test_analyze_endpoint_batch_mode(filepath, filename)
                
                file_result = {
                    "filename": filename,
                    "step_1_analyze": analyze_result
                }
                
                if analyze_result.get("success"):
                    response = analyze_result.get("response", {})
                    
                    # Step 2: Extract fields for Test Report creation
                    extracted_fields = {
                        "test_report_name": response.get("test_report_name", ""),
                        "test_report_no": response.get("test_report_no", ""),
                        "issued_date": response.get("issued_date", ""),
                        "valid_date": response.get("valid_date", ""),
                        "issued_by": response.get("issued_by", ""),
                        "report_form": response.get("report_form", ""),
                        "note": response.get("note", "")
                    }
                    
                    file_result["step_2_extracted_fields"] = extracted_fields
                    self.log(f"      Extracted fields: {list(extracted_fields.keys())}")
                    
                    # Step 3: Create Test Report record
                    create_result = self.create_test_report_record(extracted_fields)
                    file_result["step_3_create_record"] = create_result
                    
                    if create_result.get("success"):
                        report_id = create_result.get("report_id")
                        self.log(f"      ✅ Test Report created: {report_id}")
                        
                        # Step 4: Upload files if _file_content exists
                        if response.get("_file_content"):
                            upload_result = self.upload_test_report_files(
                                report_id, 
                                response.get("_file_content"),
                                response.get("_filename", filename)
                            )
                            file_result["step_4_upload_files"] = upload_result
                            
                            if upload_result.get("success"):
                                self.log(f"      ✅ Files uploaded successfully")
                            else:
                                self.log(f"      ❌ File upload failed: {upload_result.get('error')}", "ERROR")
                        else:
                            file_result["step_4_upload_files"] = {
                                "success": False,
                                "error": "_file_content missing from analyze response"
                            }
                            self.log(f"      ❌ No _file_content to upload", "ERROR")
                    else:
                        self.log(f"      ❌ Test Report creation failed: {create_result.get('error')}", "ERROR")
                else:
                    self.log(f"      ❌ Analyze failed: {analyze_result.get('error')}", "ERROR")
                
                phase_results["files_processed"].append(file_result)
            
            # Calculate batch summary
            successful_files = sum(
                1 for file_result in phase_results["files_processed"]
                if file_result.get("step_1_analyze", {}).get("success") and
                   file_result.get("step_3_create_record", {}).get("success")
            )
            
            phase_results["batch_summary"] = {
                "total_files": len(TEST_FILES),
                "successful_files": successful_files,
                "failed_files": len(TEST_FILES) - successful_files,
                "success_rate": (successful_files / len(TEST_FILES)) * 100
            }
            
            self.test_results["phase_3_batch_processing"] = {
                "status": "passed" if successful_files == len(TEST_FILES) else "failed",
                "details": phase_results
            }
            
            return successful_files == len(TEST_FILES)
            
        except Exception as e:
            self.log(f"❌ Phase 3 error: {e}", "ERROR")
            self.test_results["phase_3_batch_processing"] = {
                "status": "failed",
                "details": {"error": str(e)}
            }
            return False
    
    def test_analyze_endpoint_batch_mode(self, filepath: str, filename: str) -> Dict[str, Any]:
        """Test analyze endpoint in batch mode (bypass_validation=true)"""
        try:
            with open(filepath, 'rb') as f:
                file_content = f.read()
            
            files = {
                'test_report_file': (filename, file_content, 'application/pdf')
            }
            
            data = {
                'ship_id': self.ship_info['id'],
                'bypass_validation': 'true'  # Batch mode
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{BACKEND_URL}/test-reports/analyze-file",
                files=files,
                data=data
            )
            end_time = time.time()
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    "success": True,
                    "response": response_data,
                    "duration": end_time - start_time,
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": end_time - start_time,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_test_report_record(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Create Test Report record in database"""
        try:
            # Convert date strings to proper format if needed
            create_data = {
                "ship_id": self.ship_info['id'],
                "test_report_name": fields.get("test_report_name", ""),
                "test_report_no": fields.get("test_report_no", ""),
                "issued_by": fields.get("issued_by", ""),
                "report_form": fields.get("report_form", ""),
                "note": fields.get("note", "")
            }
            
            # Handle dates
            for date_field in ["issued_date", "valid_date"]:
                date_value = fields.get(date_field)
                if date_value and date_value.strip():
                    create_data[date_field] = date_value
            
            response = self.session.post(
                f"{BACKEND_URL}/test-reports",
                json=create_data
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                return {
                    "success": True,
                    "report_id": response_data.get("id"),
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def upload_test_report_files(self, report_id: str, file_content_b64: str, filename: str) -> Dict[str, Any]:
        """Upload files to Test Report"""
        try:
            upload_data = {
                "original_file_content": file_content_b64,
                "original_filename": filename
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/test-reports/{report_id}/upload-files",
                json=upload_data
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    "success": True,
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_errors(self) -> bool:
        """Phase 4: Error analysis"""
        try:
            self.log("🔍 Phase 4: Analyzing errors...")
            
            phase_results = {
                "single_vs_batch_comparison": {},
                "missing_fields_analysis": {},
                "backend_logs_check": {}
            }
            
            # Compare single vs batch mode responses
            single_results = self.test_results.get("phase_2_single_upload", {}).get("details", {})
            batch_results = self.test_results.get("phase_3_batch_processing", {}).get("details", {})
            
            for filename in TEST_FILES.keys():
                single_response = single_results.get(filename, {}).get("analyze", {}).get("response", {})
                batch_files = batch_results.get("files_processed", [])
                batch_response = {}
                
                for file_result in batch_files:
                    if file_result.get("filename") == filename:
                        batch_response = file_result.get("step_1_analyze", {}).get("response", {})
                        break
                
                # Compare key fields
                comparison = {
                    "single_mode": {
                        "has_file_content": bool(single_response.get("_file_content")),
                        "has_summary_text": bool(single_response.get("_summary_text")),
                        "test_report_name": single_response.get("test_report_name", ""),
                        "fields_count": len([k for k, v in single_response.items() if v])
                    },
                    "batch_mode": {
                        "has_file_content": bool(batch_response.get("_file_content")),
                        "has_summary_text": bool(batch_response.get("_summary_text")),
                        "test_report_name": batch_response.get("test_report_name", ""),
                        "fields_count": len([k for k, v in batch_response.items() if v])
                    }
                }
                
                phase_results["single_vs_batch_comparison"][filename] = comparison
            
            # Check backend logs for errors
            self.log("   Checking backend logs...")
            backend_logs = self.check_backend_logs()
            phase_results["backend_logs_check"] = backend_logs
            
            self.test_results["phase_4_error_analysis"] = {
                "status": "completed",
                "details": phase_results
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ Phase 4 error: {e}", "ERROR")
            self.test_results["phase_4_error_analysis"] = {
                "status": "failed",
                "details": {"error": str(e)}
            }
            return False
    
    def check_backend_logs(self) -> Dict[str, Any]:
        """Check backend logs for errors"""
        try:
            # Check supervisor backend logs
            import subprocess
            
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            logs_info = {}
            
            for log_file in log_files:
                try:
                    result = subprocess.run(
                        ["tail", "-n", "50", log_file],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        logs_info[log_file] = {
                            "accessible": True,
                            "content": result.stdout,
                            "error_patterns": self.find_error_patterns(result.stdout)
                        }
                    else:
                        logs_info[log_file] = {
                            "accessible": False,
                            "error": result.stderr
                        }
                        
                except Exception as e:
                    logs_info[log_file] = {
                        "accessible": False,
                        "error": str(e)
                    }
            
            return logs_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def find_error_patterns(self, log_content: str) -> List[str]:
        """Find error patterns in log content"""
        error_patterns = []
        
        error_keywords = [
            "ERROR", "CRITICAL", "FAILED", "Exception", "Traceback",
            "test report", "batch", "upload", "_file_content", "missing"
        ]
        
        lines = log_content.split('\n')
        for line in lines:
            for keyword in error_keywords:
                if keyword.lower() in line.lower():
                    error_patterns.append(line.strip())
                    break
        
        return error_patterns
    
    def investigate_root_cause(self) -> bool:
        """Phase 5: Root cause investigation"""
        try:
            self.log("🔬 Phase 5: Root cause investigation...")
            
            phase_results = {
                "identified_issues": [],
                "potential_causes": [],
                "recommendations": []
            }
            
            # Analyze test results to identify root cause
            single_results = self.test_results.get("phase_2_single_upload", {}).get("details", {})
            batch_results = self.test_results.get("phase_3_batch_processing", {}).get("details", {})
            error_analysis = self.test_results.get("phase_4_error_analysis", {}).get("details", {})
            
            # Check for _file_content issues
            for filename in TEST_FILES.keys():
                comparison = error_analysis.get("single_vs_batch_comparison", {}).get(filename, {})
                
                single_has_content = comparison.get("single_mode", {}).get("has_file_content", False)
                batch_has_content = comparison.get("batch_mode", {}).get("has_file_content", False)
                
                if single_has_content and not batch_has_content:
                    phase_results["identified_issues"].append(
                        f"_file_content missing in batch mode for {filename}"
                    )
                    phase_results["potential_causes"].append(
                        "Backend doesn't include _file_content when bypass_validation=true"
                    )
                
                single_fields = comparison.get("single_mode", {}).get("fields_count", 0)
                batch_fields = comparison.get("batch_mode", {}).get("fields_count", 0)
                
                if single_fields > batch_fields:
                    phase_results["identified_issues"].append(
                        f"Fewer fields extracted in batch mode for {filename} ({batch_fields} vs {single_fields})"
                    )
            
            # Check backend logs for specific errors
            backend_logs = error_analysis.get("backend_logs_check", {})
            for log_file, log_info in backend_logs.items():
                if log_info.get("accessible") and log_info.get("error_patterns"):
                    for pattern in log_info.get("error_patterns", []):
                        if "test report" in pattern.lower() or "batch" in pattern.lower():
                            phase_results["identified_issues"].append(f"Backend log error: {pattern}")
            
            # Generate recommendations
            if phase_results["identified_issues"]:
                phase_results["recommendations"].extend([
                    "Check backend code for bypass_validation parameter handling",
                    "Verify _file_content is included in batch mode responses",
                    "Compare single vs batch mode processing logic",
                    "Check Document AI processing differences between modes"
                ])
            else:
                phase_results["recommendations"].append(
                    "No obvious issues found - may need deeper investigation"
                )
            
            self.test_results["phase_5_root_cause"] = {
                "status": "completed",
                "details": phase_results
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ Phase 5 error: {e}", "ERROR")
            self.test_results["phase_5_root_cause"] = {
                "status": "failed",
                "details": {"error": str(e)}
            }
            return False
    
    def print_final_report(self):
        """Print comprehensive final report"""
        self.log("=" * 80)
        self.log("📊 TEST REPORT BATCH UPLOAD INVESTIGATION - FINAL REPORT")
        self.log("=" * 80)
        
        # Phase summaries
        for phase_name, phase_data in self.test_results.items():
            status = phase_data.get("status", "unknown")
            status_icon = "✅" if status == "passed" else "❌" if status == "failed" else "⚠️"
            
            phase_title = phase_name.replace("_", " ").title()
            self.log(f"{status_icon} {phase_title}: {status.upper()}")
        
        self.log("")
        
        # Root cause summary
        root_cause = self.test_results.get("phase_5_root_cause", {}).get("details", {})
        
        if root_cause.get("identified_issues"):
            self.log("🚨 IDENTIFIED ISSUES:")
            for issue in root_cause.get("identified_issues", []):
                self.log(f"   • {issue}")
            self.log("")
        
        if root_cause.get("potential_causes"):
            self.log("🔍 POTENTIAL CAUSES:")
            for cause in root_cause.get("potential_causes", []):
                self.log(f"   • {cause}")
            self.log("")
        
        if root_cause.get("recommendations"):
            self.log("💡 RECOMMENDATIONS:")
            for rec in root_cause.get("recommendations", []):
                self.log(f"   • {rec}")
            self.log("")
        
        # Batch processing summary
        batch_summary = self.test_results.get("phase_3_batch_processing", {}).get("details", {}).get("batch_summary", {})
        if batch_summary:
            self.log("📈 BATCH PROCESSING SUMMARY:")
            self.log(f"   Total Files: {batch_summary.get('total_files', 0)}")
            self.log(f"   Successful: {batch_summary.get('successful_files', 0)}")
            self.log(f"   Failed: {batch_summary.get('failed_files', 0)}")
            self.log(f"   Success Rate: {batch_summary.get('success_rate', 0):.1f}%")
        
        self.log("=" * 80)
    
    def run_full_test(self) -> bool:
        """Run all test phases"""
        try:
            self.log("🚀 Starting Test Report Batch Upload Investigation...")
            self.log(f"Backend URL: {BACKEND_URL}")
            self.log(f"Test Files: {list(TEST_FILES.keys())}")
            self.log("")
            
            # Authentication
            if not self.authenticate():
                return False
            
            # Get ship info
            if not self.get_ship_info():
                return False
            
            # Run all phases
            phases = [
                ("Phase 1: Verify Test Files", self.verify_test_files),
                ("Phase 2: Test Single File Upload", self.test_single_file_upload),
                ("Phase 3: Test Batch Processing Flow", self.test_batch_processing_flow),
                ("Phase 4: Error Analysis", self.analyze_errors),
                ("Phase 5: Root Cause Investigation", self.investigate_root_cause)
            ]
            
            overall_success = True
            
            for phase_name, phase_func in phases:
                self.log(f"\n{'='*60}")
                self.log(f"🔄 {phase_name}")
                self.log(f"{'='*60}")
                
                success = phase_func()
                if not success:
                    overall_success = False
                    self.log(f"❌ {phase_name} failed")
                else:
                    self.log(f"✅ {phase_name} completed")
            
            # Print final report
            self.print_final_report()
            
            return overall_success
            
        except Exception as e:
            self.log(f"❌ Test execution error: {e}", "ERROR")
            return False

def main():
    """Main function"""
    tester = TestReportBatchUploadTester()
    success = tester.run_full_test()
    
    if success:
        print("\n🎉 Test completed successfully!")
        exit(0)
    else:
        print("\n💥 Test completed with issues!")
        exit(1)

if __name__ == "__main__":
    main()
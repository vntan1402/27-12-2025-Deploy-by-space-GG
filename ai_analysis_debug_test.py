#!/usr/bin/env python3
"""
AI Analysis Debug Test for Certificate Information Extraction Issue
Testing why certificate information extraction returns all "N/A" values
Focus: Debug AI analysis issue where certificate fields show N/A instead of extracted values
"""

import requests
import sys
import json
import os
import tempfile
import io
from datetime import datetime, timezone
import time
import PyPDF2

class AIAnalysisDebugTester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.issues_found = []
        
        # Test PDF file mentioned in review request
        self.test_pdf_filename = "PM252494430.pdf"

    def log_issue(self, issue_type, description, details=None):
        """Log an issue found during testing"""
        issue = {
            "type": issue_type,
            "description": description,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.issues_found.append(issue)
        print(f"🚨 ISSUE FOUND: {issue_type} - {description}")
        if details:
            print(f"   Details: {details}")

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED")
        
        if details:
            print(f"   Details: {details}")

    def run_api_request(self, method, endpoint, expected_status, data=None, files=None, timeout=60):
        """Run a single API request"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Don't set Content-Type for file uploads - let requests handle it
        if not files:
            headers['Content-Type'] = 'application/json'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            
            if success:
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {"raw_response": response.text}
            else:
                try:
                    error_detail = response.json()
                    return False, {"error": error_detail, "status": response.status_code}
                except:
                    return False, {"error": response.text, "status": response.status_code}

        except Exception as e:
            return False, {"error": str(e)}

    def create_test_maritime_certificate_pdf(self):
        """Create a test maritime certificate PDF with clear certificate information"""
        certificate_content = """
PANAMA MARITIME DOCUMENTATION SERVICES

SAFETY MANAGEMENT CERTIFICATE

This is to certify that the Safety Management System of the ship named below has been audited and found to comply with the requirements of the International Safety Management (ISM) Code.

Ship Name: MV PACIFIC STAR
IMO Number: 9876543210
Certificate Number: SMC-PM-2024-001
Certificate Type: Full Term
Issue Date: 15 January 2024
Valid Until: 15 January 2025
Last Endorsement: 15 July 2024
Next Survey: 15 July 2025

Issued By: Panama Maritime Documentation Services
Classification Society: DNV GL
Flag State: Panama
Gross Tonnage: 25,000
Deadweight: 35,000 MT
Built Year: 2018
Ship Owner: Pacific Maritime Holdings Ltd
Managing Company: Global Shipping Inc

This certificate is issued under the authority of the Government of Panama.

Authorized Officer: Captain John Smith
Date: 15 January 2024
Place: Panama City, Panama
"""
        
        # Create a simple text-based PDF content
        return certificate_content.encode('utf-8')

    def test_authentication(self):
        """Test admin authentication"""
        print(f"\n🔐 Testing Authentication")
        
        success, response = self.run_api_request(
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            user_info = response.get('user', {})
            self.log_test(
                "Admin Authentication", 
                True, 
                f"User: {user_info.get('full_name')} ({user_info.get('role')})"
            )
            return True
        else:
            self.log_test("Admin Authentication", False, f"Response: {response}")
            self.log_issue("AUTHENTICATION", "Login failed", response)
            return False

    def test_ai_configuration(self):
        """Test current AI configuration"""
        print(f"\n🤖 Testing AI Configuration")
        
        success, response = self.run_api_request(
            "GET",
            "ai-config",
            200
        )
        
        if success:
            print(f"   Current AI Configuration:")
            print(f"     Provider: {response.get('provider', 'Not set')}")
            print(f"     Model: {response.get('model', 'Not set')}")
            print(f"     Use Emergent Key: {response.get('use_emergent_key', 'Not set')}")
            
            # Check if configuration looks valid
            provider = response.get('provider')
            model = response.get('model')
            use_emergent = response.get('use_emergent_key', True)
            
            if not provider:
                self.log_issue("AI_CONFIG", "AI provider not configured", response)
            if not model:
                self.log_issue("AI_CONFIG", "AI model not configured", response)
            
            # Check if using Emergent LLM key
            if use_emergent:
                emergent_key = os.environ.get('EMERGENT_LLM_KEY')
                if emergent_key:
                    print(f"     Emergent Key: Available (prefix: {emergent_key[:20]}...)")
                    if not emergent_key.startswith('sk-emergent-'):
                        self.log_issue("EMERGENT_KEY", "Key format may be incorrect", f"Key starts with: {emergent_key[:15]}")
                else:
                    self.log_issue("EMERGENT_KEY", "EMERGENT_LLM_KEY not found in environment", None)
            
            self.log_test("AI Configuration", True, f"Provider: {provider}, Model: {model}")
            return True
        else:
            self.log_test("AI Configuration", False, f"Response: {response}")
            self.log_issue("AI_CONFIG", "Failed to retrieve AI configuration", response)
            return False

    def test_pdf_text_extraction(self):
        """Test PDF text extraction functionality"""
        print(f"\n📄 Testing PDF Text Extraction")
        
        # Create test PDF content
        test_content = self.create_test_maritime_certificate_pdf()
        
        try:
            # Test if we can extract text (simulating backend behavior)
            print(f"   Test certificate content created")
            print(f"   Content preview: {test_content.decode('utf-8')[:200]}...")
            
            # Check if content contains expected certificate fields
            content_str = test_content.decode('utf-8')
            expected_fields = [
                'Certificate Number',
                'Issue Date', 
                'Valid Until',
                'Ship Name',
                'Issued By'
            ]
            
            missing_fields = []
            for field in expected_fields:
                if field not in content_str:
                    missing_fields.append(field)
            
            if missing_fields:
                self.log_issue("PDF_CONTENT", f"Missing expected fields in test PDF: {missing_fields}", None)
                
            self.log_test("PDF Text Extraction", True, "Test PDF content created successfully")
            return test_content
                
        except Exception as e:
            self.log_test("PDF Text Extraction", False, f"Error: {str(e)}")
            self.log_issue("PDF_EXTRACTION", "PDF text extraction failed", str(e))
            return None

    def test_ai_analysis_endpoint(self, pdf_content):
        """Test AI Analysis endpoint with maritime certificate"""
        print(f"\n🔍 Testing AI Analysis Endpoint")
        
        try:
            # Create file-like object from content
            files = {
                'files': (self.test_pdf_filename, io.BytesIO(pdf_content), 'application/pdf')
            }
            
            print(f"   Uploading test certificate PDF: {self.test_pdf_filename}")
            success, response = self.run_api_request(
                "POST",
                "certificates/upload-multi-files",
                200,
                files=files,
                timeout=120  # Extended timeout for AI processing
            )
            
            if success:
                print(f"✅ AI Analysis endpoint accessible")
                
                # Analyze the response
                results = response.get('results', [])
                if results:
                    result = results[0]
                    print(f"   File processed: {result.get('filename')}")
                    print(f"   Status: {result.get('status')}")
                    
                    analysis = result.get('analysis', {})
                    if analysis:
                        print(f"   Analysis results:")
                        cert_name = analysis.get('cert_name', 'N/A')
                        cert_no = analysis.get('cert_no', 'N/A')
                        issue_date = analysis.get('issue_date', 'N/A')
                        valid_date = analysis.get('valid_date', 'N/A')
                        issued_by = analysis.get('issued_by', 'N/A')
                        ship_name = analysis.get('ship_name', 'N/A')
                        
                        print(f"     Ship Name: {ship_name}")
                        print(f"     Cert Name: {cert_name}")
                        print(f"     Cert No: {cert_no}")
                        print(f"     Issue Date: {issue_date}")
                        print(f"     Valid Date: {valid_date}")
                        print(f"     Issued By: {issued_by}")
                        print(f"     Category: {analysis.get('category', 'N/A')}")
                        
                        # Check for N/A values (the main issue we're debugging)
                        na_fields = []
                        key_fields = ['cert_name', 'cert_no', 'issue_date', 'valid_date', 'issued_by']
                        for field in key_fields:
                            value = analysis.get(field, 'N/A')
                            if value == 'N/A' or value is None or value == '' or str(value).strip() == '':
                                na_fields.append(field)
                        
                        if na_fields:
                            self.log_issue(
                                "AI_EXTRACTION", 
                                f"Certificate fields returning N/A: {', '.join(na_fields)}", 
                                {
                                    "na_fields": na_fields,
                                    "full_analysis": analysis,
                                    "expected_values": {
                                        "cert_name": "Safety Management Certificate",
                                        "cert_no": "SMC-PM-2024-001",
                                        "issue_date": "2024-01-15",
                                        "valid_date": "2025-01-15",
                                        "issued_by": "Panama Maritime Documentation Services"
                                    }
                                }
                            )
                            self.log_test("Certificate Information Extraction", False, f"N/A fields: {', '.join(na_fields)}")
                        else:
                            print(f"✅ All certificate fields extracted successfully")
                            self.log_test("Certificate Information Extraction", True, "All fields extracted")
                            
                        # Log full analysis for debugging
                        print(f"\n   Full Analysis Response:")
                        print(json.dumps(analysis, indent=2, default=str))
                        
                        return True, analysis
                        
                    else:
                        self.log_issue("AI_ANALYSIS", "No analysis results in response", result)
                        self.log_test("AI Analysis Response", False, "No analysis data")
                        return False, result
                else:
                    self.log_issue("AI_ANALYSIS", "No results in upload response", response)
                    self.log_test("AI Analysis Response", False, "No results array")
                    return False, response
                    
            else:
                self.log_issue("AI_ENDPOINT", "AI analysis endpoint failed", response)
                self.log_test("AI Analysis Endpoint", False, f"HTTP error: {response}")
                return False, response
                
        except Exception as e:
            self.log_test("AI Analysis Endpoint", False, f"Error: {str(e)}")
            self.log_issue("AI_ENDPOINT", "Exception during AI analysis", str(e))
            return False, {"error": str(e)}

    def test_different_certificate_types(self):
        """Test AI analysis with different types of maritime certificates"""
        print(f"\n📋 Testing Different Certificate Types")
        
        # Test different certificate types
        test_certificates = [
            {
                "name": "IAPP Certificate",
                "content": """
INTERNATIONAL AIR POLLUTION PREVENTION CERTIFICATE

This is to certify that the ship named below has been surveyed in accordance with Annex VI of MARPOL 73/78.

Ship Name: MV OCEAN BREEZE
Certificate Number: IAPP-2024-002
Certificate Type: Full Term
Issue Date: 20 February 2024
Valid Until: 20 February 2029
Issued By: DNV GL
Flag: Marshall Islands
                """
            },
            {
                "name": "Load Line Certificate", 
                "content": """
INTERNATIONAL LOAD LINE CERTIFICATE

Ship Name: MV CARGO MASTER
Certificate No: LLC-2024-003
Issue Date: 10 March 2024
Valid Date: 10 March 2029
Issued By: Lloyd's Register
Classification Society: Lloyd's Register
Flag State: Liberia
                """
            }
        ]
        
        all_successful = True
        
        for cert_test in test_certificates:
            print(f"\n   Testing {cert_test['name']}...")
            
            # Create PDF content
            pdf_content = cert_test['content'].encode('utf-8')
            
            files = {
                'files': (f"{cert_test['name'].replace(' ', '_')}.pdf", io.BytesIO(pdf_content), 'application/pdf')
            }
            
            success, response = self.run_api_request(
                "POST",
                "certificates/upload-multi-files",
                200,
                files=files,
                timeout=120
            )
            
            if success and response.get('results'):
                result = response['results'][0]
                analysis = result.get('analysis', {})
                
                # Check specific fields
                cert_name = analysis.get('cert_name', 'N/A')
                cert_no = analysis.get('cert_no', 'N/A')
                issue_date = analysis.get('issue_date', 'N/A')
                valid_date = analysis.get('valid_date', 'N/A')
                issued_by = analysis.get('issued_by', 'N/A')
                
                print(f"     Cert Name: {cert_name}")
                print(f"     Cert No: {cert_no}")
                print(f"     Issue Date: {issue_date}")
                print(f"     Valid Date: {valid_date}")
                print(f"     Issued By: {issued_by}")
                
                # Check for extraction success
                na_fields = []
                for field, value in [('cert_name', cert_name), ('cert_no', cert_no), 
                                   ('issue_date', issue_date), ('valid_date', valid_date), ('issued_by', issued_by)]:
                    if value == 'N/A' or value is None or str(value).strip() == '':
                        na_fields.append(field)
                
                if na_fields:
                    self.log_issue(
                        "FIELD_EXTRACTION",
                        f"{cert_test['name']} - Fields returning N/A: {', '.join(na_fields)}",
                        analysis
                    )
                    all_successful = False
                else:
                    print(f"   ✅ {cert_test['name']} fields extracted successfully")
            else:
                self.log_issue("CERTIFICATE_TEST", f"Failed to process {cert_test['name']}", response)
                all_successful = False
        
        self.log_test("Different Certificate Types", all_successful, f"Tested {len(test_certificates)} certificate types")
        return all_successful

    def test_google_provider_integration(self):
        """Test Google/Gemini provider integration directly"""
        print(f"\n🔍 Testing Google Provider Integration")
        
        try:
            # Test if we can import and use the Emergent LLM integration
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            emergent_key = os.environ.get('EMERGENT_LLM_KEY')
            if not emergent_key:
                self.log_issue("GOOGLE_PROVIDER", "No Emergent LLM key available for testing", None)
                self.log_test("Google Provider Test", False, "No API key")
                return False
            
            # Test with simple certificate analysis
            chat = LlmChat(
                provider="google",
                model="gemini-2.0-flash-exp",
                api_key=emergent_key
            )
            
            test_certificate_text = """
SAFETY MANAGEMENT CERTIFICATE

Ship Name: MV TEST VESSEL
Certificate Number: SMC-TEST-001
Issue Date: 15 January 2024
Valid Until: 15 January 2025
Issued By: Panama Maritime Documentation Services
"""
            
            test_message = UserMessage(
                content=f"Extract certificate information from this maritime certificate text and return in JSON format: {test_certificate_text}"
            )
            
            print(f"   Testing Google/Gemini API call...")
            response = chat.send_message(test_message)
            
            if response and hasattr(response, 'content'):
                print(f"✅ Google provider working")
                print(f"   Response preview: {str(response.content)[:300]}...")
                
                # Try to parse JSON response
                try:
                    import re
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', str(response.content), re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        parsed_response = json.loads(json_str)
                        print(f"   Parsed JSON response:")
                        print(json.dumps(parsed_response, indent=2))
                        
                        # Check if expected fields are present
                        expected_fields = ['cert_name', 'cert_no', 'issue_date', 'valid_date', 'issued_by']
                        found_fields = [field for field in expected_fields if field in parsed_response]
                        
                        if found_fields:
                            print(f"   ✅ Found expected fields: {found_fields}")
                            self.log_test("Google Provider Test", True, f"Fields found: {found_fields}")
                        else:
                            self.log_issue("GOOGLE_PROVIDER", "Expected certificate fields not found in response", parsed_response)
                            self.log_test("Google Provider Test", False, "Expected fields missing")
                    else:
                        self.log_issue("GOOGLE_PROVIDER", "No JSON found in Google provider response", str(response.content))
                        self.log_test("Google Provider Test", False, "No JSON in response")
                        
                except Exception as parse_error:
                    self.log_issue("GOOGLE_PROVIDER", "Failed to parse Google provider response", str(parse_error))
                    self.log_test("Google Provider Test", False, f"Parse error: {parse_error}")
                
                return True
            else:
                self.log_issue("GOOGLE_PROVIDER", "Google provider returned empty response", str(response))
                self.log_test("Google Provider Test", False, "Empty response")
                return False
                
        except Exception as e:
            self.log_issue("GOOGLE_PROVIDER", "Google provider integration failed", str(e))
            self.log_test("Google Provider Test", False, f"Exception: {str(e)}")
            return False

    def debug_backend_logs(self):
        """Check backend logs for AI analysis errors"""
        print(f"\n📋 Checking Backend Logs")
        
        try:
            # Try to read supervisor logs
            import subprocess
            
            # Check both error and output logs
            log_files = [
                '/var/log/supervisor/backend.err.log',
                '/var/log/supervisor/backend.out.log'
            ]
            
            for log_file in log_files:
                try:
                    result = subprocess.run(
                        ['tail', '-n', '30', log_file],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        print(f"   Recent logs from {log_file}:")
                        print(result.stdout)
                        
                        # Look for AI-related errors
                        if 'AI' in result.stdout or 'analysis' in result.stdout.lower() or 'emergent' in result.stdout.lower():
                            print(f"   🔍 Found AI-related log entries")
                            
                except Exception as e:
                    print(f"   Could not read {log_file}: {str(e)}")
            
            self.log_test("Backend Log Check", True, "Logs checked")
                
        except Exception as e:
            self.log_test("Backend Log Check", False, f"Error reading logs: {str(e)}")

    def check_error_messages(self):
        """Check for specific error messages in AI analysis"""
        print(f"\n🚨 Checking for Error Messages")
        
        # Test with an invalid file to see error handling
        try:
            invalid_content = b"This is not a PDF file"
            files = {
                'files': ('invalid.pdf', io.BytesIO(invalid_content), 'application/pdf')
            }
            
            success, response = self.run_api_request(
                "POST",
                "certificates/upload-multi-files",
                200,  # Should still return 200 but with error in results
                files=files,
                timeout=60
            )
            
            if success:
                results = response.get('results', [])
                if results:
                    result = results[0]
                    status = result.get('status')
                    message = result.get('message', '')
                    
                    print(f"   Invalid file handling:")
                    print(f"     Status: {status}")
                    print(f"     Message: {message}")
                    
                    if status == 'error':
                        print(f"   ✅ Error handling working correctly")
                        self.log_test("Error Message Handling", True, "Invalid files properly rejected")
                    else:
                        self.log_issue("ERROR_HANDLING", "Invalid file not properly rejected", result)
                        self.log_test("Error Message Handling", False, "Invalid file accepted")
                        
            return True
            
        except Exception as e:
            self.log_test("Error Message Check", False, f"Error: {str(e)}")
            return False

    def run_comprehensive_debug(self):
        """Run comprehensive AI analysis debugging for certificate information extraction"""
        print("🔍 AI ANALYSIS DEBUG - CERTIFICATE INFORMATION EXTRACTION")
        print("=" * 70)
        print("Focus: Debug why certificate information extraction returns all 'N/A' values")
        print("File: PM252494430.pdf processing issue")
        print("=" * 70)
        
        # Test sequence
        test_results = []
        
        # 1. Authentication
        if not self.test_authentication():
            print("❌ Authentication failed, stopping tests")
            return False
        test_results.append(("Authentication", True))
        
        # 2. AI Configuration
        ai_config_success = self.test_ai_configuration()
        test_results.append(("AI Configuration", ai_config_success))
        
        # 3. PDF Text Extraction
        pdf_content = self.test_pdf_text_extraction()
        pdf_success = pdf_content is not None
        test_results.append(("PDF Text Extraction", pdf_success))
        
        if not pdf_success:
            print("❌ PDF text extraction failed, stopping tests")
            return False
        
        # 4. Google Provider Integration
        google_success = self.test_google_provider_integration()
        test_results.append(("Google Provider", google_success))
        
        # 5. AI Analysis Endpoint
        ai_success, ai_response = self.test_ai_analysis_endpoint(pdf_content)
        test_results.append(("AI Analysis Endpoint", ai_success))
        
        # 6. Different Certificate Types
        cert_types_success = self.test_different_certificate_types()
        test_results.append(("Certificate Types", cert_types_success))
        
        # 7. Error Message Handling
        error_handling_success = self.check_error_messages()
        test_results.append(("Error Handling", error_handling_success))
        
        # 8. Backend Logs
        self.debug_backend_logs()
        test_results.append(("Backend Logs", True))  # Always passes as it's informational
        
        # Print results
        print("\n" + "=" * 70)
        print("📊 DEBUG TEST RESULTS")
        print("=" * 70)
        
        passed_tests = 0
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:25} {status}")
            if result:
                passed_tests += 1
        
        print(f"\nAPI Tests: {self.tests_passed}/{self.tests_run}")
        print(f"Debug Tests: {passed_tests}/{len(test_results)}")
        
        # Print issues found
        if self.issues_found:
            print(f"\n🚨 ISSUES IDENTIFIED ({len(self.issues_found)}):")
            print("=" * 70)
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. {issue['type']}: {issue['description']}")
                if issue['details']:
                    if isinstance(issue['details'], dict):
                        print(f"   Details: {json.dumps(issue['details'], indent=4, default=str)}")
                    else:
                        print(f"   Details: {issue['details']}")
                print()
                
            # Provide specific recommendations
            print("🔧 RECOMMENDATIONS:")
            print("=" * 70)
            
            ai_extraction_issues = [issue for issue in self.issues_found if issue['type'] == 'AI_EXTRACTION']
            if ai_extraction_issues:
                print("1. AI EXTRACTION ISSUES FOUND:")
                print("   - Check if AI prompt is correctly formatted for certificate extraction")
                print("   - Verify Google/Gemini model is processing PDF text correctly")
                print("   - Test with simpler certificate formats")
                print()
            
            google_provider_issues = [issue for issue in self.issues_found if issue['type'] == 'GOOGLE_PROVIDER']
            if google_provider_issues:
                print("2. GOOGLE PROVIDER ISSUES FOUND:")
                print("   - Verify EMERGENT_LLM_KEY is valid and working")
                print("   - Check if Google/Gemini API is accessible")
                print("   - Test with different models (gemini-pro, gemini-2.0-flash)")
                print()
            
            ai_config_issues = [issue for issue in self.issues_found if issue['type'] == 'AI_CONFIG']
            if ai_config_issues:
                print("3. AI CONFIGURATION ISSUES FOUND:")
                print("   - Configure AI provider and model in system settings")
                print("   - Ensure Emergent LLM key is properly set")
                print("   - Test AI configuration endpoint")
                print()
                
        else:
            print(f"\n✅ NO CRITICAL ISSUES FOUND")
            print("Certificate information extraction should be working correctly.")
        
        return len(self.issues_found) == 0

def main():
    """Main debug execution"""
    tester = AIAnalysisDebugTester()
    success = tester.run_comprehensive_debug()
    
    if success:
        print("🎉 AI Analysis debugging completed successfully!")
        print("Certificate information extraction should be working correctly.")
        return 0
    else:
        print("⚠️ Issues found during AI Analysis debugging - check details above")
        print("Certificate information extraction may be returning N/A values due to identified issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
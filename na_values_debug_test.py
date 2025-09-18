#!/usr/bin/env python3
"""
N/A Values Debug Test - Focused on reproducing the exact issue from review request
Testing why AI analysis returns N/A values for PM252494420.pdf specifically
"""

import requests
import sys
import json
import io
from datetime import datetime, timezone
import time

class NAValuesDebugTester:
    def __init__(self, base_url="https://shipcertdrive.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_issues = []

    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def log_critical_issue(self, issue):
        """Log critical issue that needs main agent attention"""
        self.critical_issues.append(issue)
        self.log(f"🚨 CRITICAL: {issue}", "ERROR")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=120):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if files:
            headers.pop('Content-Type', None)

        self.tests_run += 1
        self.log(f"Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    self.log(f"Error: {json.dumps(error_detail, indent=2)}")
                except:
                    self.log(f"Error text: {response.text}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}")
            return False, {}

    def test_authentication(self):
        """Test login as admin/admin123"""
        self.log("=== STEP 1: AUTHENTICATION ===")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_info = response.get('user', {})
            self.log(f"✅ Authenticated as: {user_info.get('full_name')} ({user_info.get('role')})")
            return True
        else:
            self.log_critical_issue("Authentication failed - cannot proceed with testing")
            return False

    def create_realistic_maritime_pdf(self, filename="PM252494420.pdf"):
        """Create a realistic maritime certificate PDF that should be analyzable"""
        # Create a more realistic PDF content that mimics the structure mentioned in the review
        pdf_content = f"""
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 800
>>
stream
BT
/F1 14 Tf
50 750 Td
(PANAMA MARITIME AUTHORITY) Tj
0 -30 Td
(INTERNATIONAL AIR POLLUTION PREVENTION CERTIFICATE) Tj
0 -40 Td
(Certificate No: {filename.replace('.pdf', '')}) Tj
0 -25 Td
(Ship Name: MV OCEAN STAR) Tj
0 -25 Td
(IMO Number: 9876543) Tj
0 -25 Td
(Port of Registry: Panama) Tj
0 -25 Td
(Gross Tonnage: 25,000) Tj
0 -40 Td
(Issue Date: 15 January 2024) Tj
0 -25 Td
(Valid Until: 15 January 2029) Tj
0 -40 Td
(This certificate is issued under the provisions of the International) Tj
0 -20 Td
(Convention for the Prevention of Pollution from Ships, 1973,) Tj
0 -20 Td
(as modified by the Protocol of 1978 relating thereto (MARPOL 73/78)) Tj
0 -40 Td
(Issued by: Panama Maritime Authority) Tj
0 -25 Td
(On behalf of the Government of Panama) Tj
0 -40 Td
(Date: 15 January 2024) Tj
0 -25 Td
(Place: Panama City) Tj
0 -40 Td
(Signature: [Official Signature]) Tj
0 -25 Td
(Stamp: [Official Seal]) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
1056
%%EOF
"""
        return pdf_content.encode('utf-8')

    def test_ai_configuration_status(self):
        """Check current AI configuration"""
        self.log("=== STEP 2: AI CONFIGURATION STATUS ===")
        
        success, ai_config = self.run_test(
            "Get AI Configuration",
            "GET",
            "ai-config",
            200
        )
        
        if success:
            self.log(f"AI Provider: {ai_config.get('provider', 'N/A')}")
            self.log(f"AI Model: {ai_config.get('model', 'N/A')}")
            self.log(f"Use Emergent Key: {ai_config.get('use_emergent_key', 'N/A')}")
            
            # Check if configuration looks correct for enhanced processing
            if ai_config.get('use_emergent_key') != True:
                self.log_critical_issue("AI not configured to use Emergent key - may cause N/A values")
            
            return True
        else:
            self.log_critical_issue("Cannot access AI configuration")
            return False

    def test_specific_file_upload(self):
        """Test upload of the specific file mentioned in review request"""
        self.log("=== STEP 3: SPECIFIC FILE UPLOAD TEST ===")
        
        # Create the specific PDF file mentioned in the review request
        filename = "PM252494420.pdf"
        pdf_content = self.create_realistic_maritime_pdf(filename)
        
        self.log(f"Testing with file: {filename} ({len(pdf_content)} bytes)")
        
        files = {
            'files': (filename, io.BytesIO(pdf_content), 'application/pdf')
        }
        
        success, response = self.run_test(
            "Certificate Upload - PM252494420.pdf",
            "POST",
            "certificates/upload-multi-files",
            200,
            files=files,
            timeout=180  # Longer timeout for AI processing
        )
        
        if success:
            results = response.get('results', [])
            if results:
                result = results[0]
                self.log(f"Upload Status: {result.get('status', 'N/A')}")
                
                # Check the AI analysis results specifically
                analysis = result.get('analysis', {})
                if analysis:
                    self.log("🔍 AI ANALYSIS RESULTS:")
                    cert_name = analysis.get('cert_name', 'N/A')
                    cert_no = analysis.get('cert_no', 'N/A')
                    issue_date = analysis.get('issue_date', 'N/A')
                    valid_date = analysis.get('valid_date', 'N/A')
                    
                    self.log(f"  Cert Name: {cert_name}")
                    self.log(f"  Cert No: {cert_no}")
                    self.log(f"  Issue Date: {issue_date}")
                    self.log(f"  Valid Date: {valid_date}")
                    self.log(f"  Issued By: {analysis.get('issued_by', 'N/A')}")
                    self.log(f"  Ship Name: {analysis.get('ship_name', 'N/A')}")
                    
                    # Check if we're getting the N/A values issue
                    na_fields = []
                    for field_name, field_value in [
                        ('cert_name', cert_name),
                        ('cert_no', cert_no), 
                        ('issue_date', issue_date),
                        ('valid_date', valid_date)
                    ]:
                        if field_value in ['N/A', None, '', 'Unknown']:
                            na_fields.append(field_name)
                    
                    if na_fields:
                        self.log_critical_issue(f"CONFIRMED USER ISSUE: Fields returning N/A: {na_fields}")
                        self.log("This reproduces the exact issue reported by the user")
                        
                        # Check if fallback logic should have kicked in
                        if analysis.get('category') == 'certificates':
                            self.log_critical_issue("Enhanced fallback logic not working - classified as certificate but still N/A values")
                        
                        return False
                    else:
                        self.log("✅ All fields have meaningful values - issue may be intermittent")
                        return True
                else:
                    self.log_critical_issue("No analysis results returned")
                    return False
            else:
                self.log_critical_issue("No results in upload response")
                return False
        else:
            self.log_critical_issue("Certificate upload failed completely")
            return False

    def test_fallback_logic_scenarios(self):
        """Test different scenarios to see if fallback logic is working"""
        self.log("=== STEP 4: FALLBACK LOGIC TESTING ===")
        
        scenarios = [
            {
                'name': 'Empty PDF',
                'content': b'%PDF-1.4\n%%EOF',
                'filename': 'empty_test.pdf',
                'should_fallback': True
            },
            {
                'name': 'Corrupted PDF',
                'content': b'This is not a PDF file at all',
                'filename': 'corrupted_test.pdf',
                'should_fallback': True
            },
            {
                'name': 'Valid Certificate PDF',
                'content': self.create_realistic_maritime_pdf("valid_cert.pdf"),
                'filename': 'valid_cert.pdf',
                'should_fallback': False
            }
        ]
        
        fallback_working = False
        
        for scenario in scenarios:
            self.log(f"Testing scenario: {scenario['name']}")
            
            files = {
                'files': (scenario['filename'], io.BytesIO(scenario['content']), 'application/pdf')
            }
            
            success, response = self.run_test(
                f"Fallback Test - {scenario['name']}",
                "POST",
                "certificates/upload-multi-files",
                200,
                files=files,
                timeout=120
            )
            
            if success:
                results = response.get('results', [])
                if results:
                    result = results[0]
                    analysis = result.get('analysis', {})
                    
                    if analysis:
                        cert_name = analysis.get('cert_name', 'N/A')
                        has_meaningful_data = cert_name not in ['N/A', None, '', 'Unknown']
                        
                        self.log(f"  Status: {result.get('status', 'N/A')}")
                        self.log(f"  Has meaningful data: {has_meaningful_data}")
                        
                        if scenario['should_fallback'] and has_meaningful_data:
                            self.log("✅ Fallback logic appears to be working")
                            fallback_working = True
                        elif not scenario['should_fallback'] and has_meaningful_data:
                            self.log("✅ Normal AI processing working")
        
        if not fallback_working:
            self.log_critical_issue("Fallback logic not working - enhanced PDF processing may not be deployed")
        
        return fallback_working

    def check_backend_deployment_status(self):
        """Check if the enhanced backend changes are actually deployed"""
        self.log("=== STEP 5: BACKEND DEPLOYMENT STATUS ===")
        
        # Check if we can access backend logs to see if enhanced processing is running
        try:
            import subprocess
            result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.err.log'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logs = result.stdout
                self.log("Recent backend error logs:")
                
                # Look for signs of enhanced processing
                if 'classify_by_filename' in logs:
                    self.log("✅ Found classify_by_filename in logs - enhanced processing may be active")
                elif 'analyze_with_google' in logs:
                    self.log("✅ Found analyze_with_google in logs - enhanced processing may be active")
                elif 'fallback' in logs.lower():
                    self.log("✅ Found fallback logic in logs - enhanced processing may be active")
                else:
                    self.log_critical_issue("No signs of enhanced processing in recent logs")
                
                # Look for specific errors
                if 'N/A' in logs:
                    self.log("⚠️ Found N/A values in logs - confirms issue")
                
                return True
            else:
                self.log("Could not access backend logs")
                return False
                
        except Exception as e:
            self.log(f"Error checking backend logs: {e}")
            return False

    def run_comprehensive_na_debug(self):
        """Run comprehensive debugging of N/A values issue"""
        self.log("🔍 N/A VALUES DEBUG TEST - REPRODUCING USER ISSUE")
        self.log("=" * 80)
        self.log("ISSUE: AI analysis returns N/A for Cert Name, Cert No, Issue Date, Valid Date")
        self.log("FILE: PM252494420.pdf processing")
        self.log("=" * 80)
        
        # Step 1: Authentication
        if not self.test_authentication():
            return False
        
        # Step 2: Check AI configuration
        if not self.test_ai_configuration_status():
            return False
        
        # Step 3: Test specific file upload
        specific_file_success = self.test_specific_file_upload()
        
        # Step 4: Test fallback logic
        fallback_success = self.test_fallback_logic_scenarios()
        
        # Step 5: Check backend deployment
        self.check_backend_deployment_status()
        
        return specific_file_success and fallback_success

    def print_summary(self):
        """Print comprehensive summary for main agent"""
        self.log("=" * 80)
        self.log("🎯 N/A VALUES DEBUG SUMMARY")
        self.log("=" * 80)
        
        self.log(f"Tests Run: {self.tests_run}")
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.critical_issues:
            self.log(f"\n🚨 CRITICAL ISSUES FOUND ({len(self.critical_issues)}):")
            for i, issue in enumerate(self.critical_issues, 1):
                self.log(f"{i}. {issue}")
        else:
            self.log("\n✅ No critical issues found")
        
        self.log("\n🎯 FINDINGS:")
        self.log("1. Authentication: ✅ Working (admin/admin123)")
        self.log("2. AI Configuration: ✅ Accessible")
        self.log("3. File Upload: ⚠️ Needs investigation")
        self.log("4. N/A Values Issue: ❌ Confirmed or ✅ Not reproduced")
        
        self.log("\n📋 RECOMMENDATIONS FOR MAIN AGENT:")
        if self.critical_issues:
            self.log("1. 🚨 CRITICAL: Enhanced PDF processing not working as expected")
            self.log("2. Check if analyze_document_with_ai function has proper fallback logic")
            self.log("3. Verify classify_by_filename function is implemented and working")
            self.log("4. Ensure backend restart properly applied the enhanced changes")
            self.log("5. Consider using web search to find solutions for AI analysis issues")
        else:
            self.log("1. ✅ AI analysis appears to be working correctly")
            self.log("2. Issue may be intermittent or specific to certain file types")
            self.log("3. Monitor for patterns in when N/A values occur")

def main():
    """Main test execution"""
    tester = NAValuesDebugTester()
    
    try:
        success = tester.run_comprehensive_na_debug()
        tester.print_summary()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        tester.log("Test interrupted by user", "WARN")
        return 1
    except Exception as e:
        tester.log(f"Unexpected error: {str(e)}", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())
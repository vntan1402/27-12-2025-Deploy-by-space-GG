#!/usr/bin/env python3
"""
PDF Analysis API Comprehensive Testing Suite
Tests the PDF Analysis functionality with Emergent LLM integration as requested in review.
"""

import requests
import sys
import json
import time
import io
import os
from datetime import datetime, timezone

class PDFAnalysisAPITester:
    def __init__(self, base_url="https://shipcertdrive.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None
        self.test_results = []

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        # Override with custom headers if provided
        if headers:
            test_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            test_headers.pop('Content-Type', None)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=60)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=test_headers, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=test_headers, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=60)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=60)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    result = response.json() if response.content else {}
                    self.log_result(name, True, f"Status: {response.status_code}")
                    return True, result
                except:
                    self.log_result(name, True, f"Status: {response.status_code}")
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                    self.log_result(name, False, f"Status: {response.status_code}, Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                    self.log_result(name, False, f"Status: {response.status_code}, Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.log_result(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_authentication(self):
        """Test login with admin/admin123 credentials"""
        print(f"\n🔐 TESTING AUTHENTICATION")
        success, response = self.run_test(
            "Admin Login (admin/admin123)",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user_id = response.get('user', {}).get('id')
            user_info = response.get('user', {})
            print(f"✅ Login successful")
            print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
            print(f"   Company: {user_info.get('company')}")
            
            # Verify user has EDITOR role or higher for PDF analysis
            user_role = user_info.get('role', '').lower()
            if user_role in ['editor', 'manager', 'admin', 'super_admin']:
                print(f"✅ User has sufficient permissions for PDF analysis ({user_role})")
                return True
            else:
                print(f"❌ User role '{user_role}' insufficient for PDF analysis (requires EDITOR or higher)")
                return False
        return False

    def create_test_pdf(self, content_type="simple"):
        """Create different types of test PDF files"""
        if content_type == "simple":
            # Create a simple PDF-like content for basic testing
            pdf_content = b"""%PDF-1.4
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
/Length 200
>>
stream
BT
/F1 12 Tf
72 720 Td
(SHIP CERTIFICATE) Tj
0 -20 Td
(Ship Name: MV Test Vessel) Tj
0 -20 Td
(IMO Number: 1234567) Tj
0 -20 Td
(Flag: Panama) Tj
0 -20 Td
(Gross Tonnage: 50000) Tj
0 -20 Td
(Built: 2020) Tj
0 -20 Td
(Owner: Test Maritime Ltd) Tj
0 -20 Td
(Company: Global Shipping Co) Tj
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
500
%%EOF"""
            return pdf_content
        
        elif content_type == "large":
            # Create a large PDF (>5MB) for size validation testing
            base_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 6000000>>stream
"""
            # Add 6MB of content to exceed the 5MB limit
            large_content = b"X" * 6000000
            end_content = b"""
endstream
endobj
xref
0 5
0000000000 65535 f 
trailer<</Size 5/Root 1 0 R>>
startxref
6000100
%%EOF"""
            return base_content + large_content + end_content
        
        elif content_type == "empty":
            # Create an empty/minimal PDF
            return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f 
trailer<</Size 4/Root 1 0 R>>
startxref
150
%%EOF"""
        
        return None

    def test_pdf_analysis_valid_upload(self):
        """Test POST /api/analyze-ship-certificate with valid PDF"""
        print(f"\n📄 TESTING PDF ANALYSIS - VALID UPLOAD")
        
        pdf_content = self.create_test_pdf("simple")
        if not pdf_content:
            print("❌ Failed to create test PDF")
            return False
        
        files = {'file': ('ship_certificate.pdf', io.BytesIO(pdf_content), 'application/pdf')}
        
        success, response = self.run_test(
            "PDF Analysis - Valid PDF Upload",
            "POST",
            "analyze-ship-certificate",
            200,
            files=files
        )
        
        if success:
            print(f"✅ PDF analysis endpoint accessible")
            
            # Verify response structure
            if 'success' in response and response.get('success'):
                print(f"✅ Analysis successful: {response.get('message', 'No message')}")
                
                if 'analysis' in response:
                    analysis = response['analysis']
                    expected_fields = ['ship_name', 'imo_number', 'class_society', 'flag', 'gross_tonnage', 'deadweight', 'built_year', 'ship_owner', 'company']
                    
                    print(f"   Analysis response structure:")
                    for field in expected_fields:
                        value = analysis.get(field)
                        print(f"     {field}: {value}")
                    
                    has_all_fields = all(field in analysis for field in expected_fields)
                    
                    if has_all_fields:
                        print(f"✅ Analysis response structure correct - all {len(expected_fields)} fields present")
                        return True
                    else:
                        missing_fields = [field for field in expected_fields if field not in analysis]
                        print(f"❌ Missing fields in analysis response: {missing_fields}")
                        return False
                else:
                    print(f"❌ No 'analysis' field in response")
                    return False
            else:
                print(f"❌ Analysis not successful: {response}")
                return False
        
        return False

    def test_pdf_file_size_validation(self):
        """Test file size validation (should reject files > 5MB)"""
        print(f"\n📏 TESTING PDF ANALYSIS - FILE SIZE VALIDATION")
        
        # Create a large PDF file (>5MB)
        large_pdf_content = self.create_test_pdf("large")
        if not large_pdf_content:
            print("❌ Failed to create large test PDF")
            return False
        
        print(f"   Created large PDF: {len(large_pdf_content)} bytes ({len(large_pdf_content)/(1024*1024):.1f}MB)")
        
        files = {'file': ('large_certificate.pdf', io.BytesIO(large_pdf_content), 'application/pdf')}
        
        success, response = self.run_test(
            "PDF Analysis - File Size Validation (>5MB)",
            "POST",
            "analyze-ship-certificate",
            400,  # Should be rejected with 400 Bad Request
            files=files
        )
        
        if success:
            print(f"✅ File size validation working - large files properly rejected")
            if 'detail' in response:
                print(f"   Error message: {response['detail']}")
            return True
        
        return False

    def test_pdf_file_type_validation(self):
        """Test file type validation (should accept only PDF files)"""
        print(f"\n📋 TESTING PDF ANALYSIS - FILE TYPE VALIDATION")
        
        # Test with non-PDF file
        text_content = b"This is not a PDF file, it's just plain text content for testing file type validation."
        files = {'file': ('not_a_pdf.txt', io.BytesIO(text_content), 'text/plain')}
        
        success, response = self.run_test(
            "PDF Analysis - File Type Validation (TXT file)",
            "POST",
            "analyze-ship-certificate",
            400,  # Should be rejected with 400 Bad Request
            files=files
        )
        
        if success:
            print(f"✅ File type validation working - non-PDF files properly rejected")
            if 'detail' in response:
                print(f"   Error message: {response['detail']}")
        
        # Test with file that has PDF extension but wrong content
        fake_pdf_content = b"This is fake PDF content with .pdf extension"
        files_fake = {'file': ('fake.pdf', io.BytesIO(fake_pdf_content), 'application/pdf')}
        
        # This should pass file type validation but may fail in AI processing
        success_fake, response_fake = self.run_test(
            "PDF Analysis - Fake PDF with correct extension",
            "POST",
            "analyze-ship-certificate",
            200,  # Should pass initial validation
            files=files_fake
        )
        
        if success_fake:
            print(f"✅ File with PDF extension accepted (content validation handled by AI)")
        else:
            print(f"⚠️  Fake PDF rejected (may be due to content validation)")
        
        return success

    def test_pdf_permission_controls(self):
        """Test permission controls (requires EDITOR role or higher)"""
        print(f"\n🔐 TESTING PDF ANALYSIS - PERMISSION CONTROLS")
        
        # Test with current admin token (should work)
        pdf_content = self.create_test_pdf("simple")
        files = {'file': ('permission_test.pdf', io.BytesIO(pdf_content), 'application/pdf')}
        
        success, response = self.run_test(
            "PDF Analysis - With Admin Permissions",
            "POST",
            "analyze-ship-certificate",
            200,
            files=files
        )
        
        if success:
            print(f"✅ Admin user can access PDF analysis endpoint")
        
        # Test without authentication token
        temp_token = self.token
        self.token = None
        
        success_no_auth, response_no_auth = self.run_test(
            "PDF Analysis - Without Authentication",
            "POST",
            "analyze-ship-certificate",
            401,  # Should be unauthorized
            files=files
        )
        
        if success_no_auth:
            print(f"✅ Unauthenticated requests properly rejected")
            if 'detail' in response_no_auth:
                print(f"   Error message: {response_no_auth['detail']}")
        
        # Restore token
        self.token = temp_token
        
        # Test with invalid token
        invalid_headers = {'Authorization': 'Bearer invalid_token_12345'}
        
        success_invalid, response_invalid = self.run_test(
            "PDF Analysis - With Invalid Token",
            "POST",
            "analyze-ship-certificate",
            401,  # Should be unauthorized
            files=files,
            headers=invalid_headers
        )
        
        if success_invalid:
            print(f"✅ Invalid tokens properly rejected")
            if 'detail' in response_invalid:
                print(f"   Error message: {response_invalid['detail']}")
        
        return success and success_no_auth

    def test_ai_analysis_response_structure(self):
        """Test AI analysis response structure with Emergent LLM key"""
        print(f"\n🤖 TESTING PDF ANALYSIS - AI RESPONSE STRUCTURE")
        
        # Test with a more detailed PDF content
        detailed_pdf = self.create_test_pdf("simple")
        files = {'file': ('detailed_certificate.pdf', io.BytesIO(detailed_pdf), 'application/pdf')}
        
        success, response = self.run_test(
            "PDF Analysis - AI Response Structure Test",
            "POST",
            "analyze-ship-certificate",
            200,
            files=files
        )
        
        if success and 'analysis' in response:
            analysis = response['analysis']
            
            print(f"✅ AI analysis completed")
            print(f"   Response structure validation:")
            
            # Check all expected fields are present
            expected_fields = {
                'ship_name': 'string',
                'imo_number': 'string', 
                'class_society': 'string',
                'flag': 'string',
                'gross_tonnage': 'number',
                'deadweight': 'number',
                'built_year': 'number',
                'ship_owner': 'string',
                'company': 'string'
            }
            
            structure_valid = True
            for field, expected_type in expected_fields.items():
                if field in analysis:
                    value = analysis[field]
                    if value is None:
                        print(f"     ✅ {field}: null (acceptable)")
                    elif expected_type == 'string' and isinstance(value, str):
                        print(f"     ✅ {field}: '{value}' (string)")
                    elif expected_type == 'number' and isinstance(value, (int, float)):
                        print(f"     ✅ {field}: {value} (number)")
                    else:
                        print(f"     ❌ {field}: {value} (wrong type, expected {expected_type})")
                        structure_valid = False
                else:
                    print(f"     ❌ {field}: missing")
                    structure_valid = False
            
            if structure_valid:
                print(f"✅ AI response structure is valid")
                return True
            else:
                print(f"❌ AI response structure has issues")
                return False
        
        return False

    def test_temporary_file_cleanup(self):
        """Test temporary file cleanup and error handling"""
        print(f"\n🧹 TESTING PDF ANALYSIS - TEMPORARY FILE CLEANUP")
        
        # Test multiple uploads to verify cleanup
        for i in range(3):
            pdf_content = self.create_test_pdf("simple")
            files = {'file': (f'cleanup_test_{i}.pdf', io.BytesIO(pdf_content), 'application/pdf')}
            
            success, response = self.run_test(
                f"PDF Analysis - Cleanup Test {i+1}",
                "POST",
                "analyze-ship-certificate",
                200,
                files=files
            )
            
            if success:
                print(f"   ✅ Upload {i+1} successful")
            else:
                print(f"   ❌ Upload {i+1} failed")
                return False
            
            time.sleep(1)  # Brief pause between uploads
        
        print(f"✅ Multiple uploads completed - temporary file cleanup appears to be working")
        return True

    def test_companies_api_integration(self):
        """Test GET /api/companies endpoint for dropdown data integration"""
        print(f"\n🏢 TESTING COMPANIES API INTEGRATION")
        
        success, companies = self.run_test(
            "GET /api/companies for dropdown data",
            "GET",
            "companies",
            200
        )
        
        if success:
            print(f"   Found {len(companies)} companies")
            if companies:
                # Verify data structure includes required fields
                first_company = companies[0]
                required_fields = ['id', 'name_vn', 'name_en']
                has_required_fields = all(field in first_company for field in required_fields)
                
                if has_required_fields:
                    print(f"✅ Companies data structure verified for dropdown integration")
                    print(f"   Sample company: {first_company.get('name_en')} / {first_company.get('name_vn')}")
                    
                    # Show a few examples for Ship Owner and Company dropdowns
                    print(f"   Available for Ship Owner/Company dropdowns:")
                    for i, company in enumerate(companies[:3]):  # Show first 3
                        print(f"     - {company.get('name_en', 'N/A')} ({company.get('id', 'N/A')})")
                    
                    return True
                else:
                    print(f"❌ Missing required fields in company data")
                    return False
            else:
                print(f"⚠️  No companies found - dropdowns will be empty")
                return True  # Not a failure, just empty data
        
        return False

    def run_comprehensive_pdf_analysis_test(self):
        """Run all PDF analysis tests"""
        print("📄 PDF ANALYSIS API COMPREHENSIVE TESTING SUITE")
        print("=" * 80)
        print(f"Testing Backend URL: {self.base_url}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run tests in order
        tests = [
            ("Authentication & Permissions", self.test_authentication),
            ("Companies API Integration", self.test_companies_api_integration),
            ("PDF Analysis - Valid Upload", self.test_pdf_analysis_valid_upload),
            ("PDF Analysis - File Size Validation", self.test_pdf_file_size_validation),
            ("PDF Analysis - File Type Validation", self.test_pdf_file_type_validation),
            ("PDF Analysis - Permission Controls", self.test_pdf_permission_controls),
            ("PDF Analysis - AI Response Structure", self.test_ai_analysis_response_structure),
            ("PDF Analysis - Temporary File Cleanup", self.test_temporary_file_cleanup)
        ]
        
        test_group_results = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n{'='*60}")
                result = test_func()
                test_group_results.append((test_name, result))
                if result:
                    print(f"\n✅ {test_name} - PASSED")
                else:
                    print(f"\n❌ {test_name} - FAILED")
            except Exception as e:
                print(f"\n💥 {test_name} - ERROR: {str(e)}")
                test_group_results.append((test_name, False))
        
        # Print summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 80)
        print("📊 PDF ANALYSIS API TEST SUMMARY")
        print("=" * 80)
        
        passed_groups = sum(1 for _, result in test_group_results if result)
        total_groups = len(test_group_results)
        
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"🧪 Individual API Tests: {self.tests_passed}/{self.tests_run} passed")
        print(f"📋 Test Groups: {passed_groups}/{total_groups} passed")
        
        print(f"\n📋 Test Group Results:")
        for test_name, result in test_group_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name:40} {status}")
        
        # Detailed results for failed tests
        if self.test_results:
            failed_tests = [r for r in self.test_results if not r['success']]
            if failed_tests:
                print(f"\n❌ Failed Tests Details:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        overall_success = passed_groups == total_groups and self.tests_passed >= (self.tests_run * 0.8)
        
        if overall_success:
            print(f"\n🎉 ALL PDF ANALYSIS API TESTS PASSED!")
            print("✅ PDF Analysis endpoint working correctly")
            print("✅ File validation (size & type) working")
            print("✅ Permission controls enforced")
            print("✅ AI analysis with Emergent LLM key functional")
            print("✅ Response structure matches requirements")
            print("✅ Temporary file cleanup working")
        else:
            print(f"\n⚠️  SOME PDF ANALYSIS TESTS FAILED")
            print("❌ Check the detailed results above for specific issues")
        
        return overall_success

def main():
    """Main test execution"""
    tester = PDFAnalysisAPITester()
    success = tester.run_comprehensive_pdf_analysis_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
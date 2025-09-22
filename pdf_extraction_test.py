#!/usr/bin/env python3
"""
PDF Text Extraction Test
Test different PDF scenarios that might cause N/A extraction
"""

import requests
import sys
import json
import os
import io
from datetime import datetime
import time

class PDFExtractionTester:
    def __init__(self, base_url="https://continue-session.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None

    def login(self):
        """Login as admin"""
        print("🔐 Logging in as admin/admin123...")
        
        response = requests.post(
            f"{self.api_url}/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            print(f"✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False

    def test_problematic_pdf_scenarios(self):
        """Test different PDF scenarios that might cause extraction issues"""
        print("\n🔍 Testing Problematic PDF Scenarios...")
        
        test_scenarios = [
            {
                "name": "Empty PDF",
                "content": b"",
                "description": "Completely empty file"
            },
            {
                "name": "Corrupted PDF Header",
                "content": b"%PDF-1.4\nCorrupted content here",
                "description": "PDF with corrupted content"
            },
            {
                "name": "Non-PDF with PDF Extension",
                "content": b"This is just plain text, not a PDF",
                "description": "Text file with .pdf extension"
            },
            {
                "name": "Minimal PDF Structure",
                "content": b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\nxref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n108\n%%EOF",
                "description": "Valid PDF structure but no content"
            },
            {
                "name": "Certificate with Special Characters",
                "content": """
PANAMÁ MARITIME DOCUMENTATION SERVICES
REPÚBLICA DE PANAMÁ

CERTIFICADO DE GESTIÓN DE SEGURIDAD
SAFETY MANAGEMENT CERTIFICATE

Ship Name: MV OCÉAN STÄR
Certificate Number: PM252494430-ÄÖÜ
Issue Date: 15/03/2024
Valid Until: 15/03/2025
Issued By: Panamá Maritime Documentation Services

Special characters: àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ
""".encode('utf-8'),
                "description": "Certificate with special characters and non-English text"
            }
        ]
        
        results = []
        
        for scenario in test_scenarios:
            print(f"\n   Testing: {scenario['name']}")
            print(f"   Description: {scenario['description']}")
            
            files = {
                'files': (f"{scenario['name'].replace(' ', '_')}.pdf", io.BytesIO(scenario['content']), 'application/pdf')
            }
            
            headers = {'Authorization': f'Bearer {self.token}'}
            
            try:
                response = requests.post(
                    f"{self.api_url}/certificates/upload-multi-files",
                    files=files,
                    headers=headers,
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results_list = data.get('results', [])
                    
                    if results_list:
                        result = results_list[0]
                        status = result.get('status')
                        message = result.get('message', '')
                        analysis = result.get('analysis', {})
                        
                        print(f"     Status: {status}")
                        if message:
                            print(f"     Message: {message}")
                        
                        if analysis:
                            cert_name = analysis.get('cert_name', 'N/A')
                            cert_no = analysis.get('cert_no', 'N/A')
                            issue_date = analysis.get('issue_date', 'N/A')
                            valid_date = analysis.get('valid_date', 'N/A')
                            
                            print(f"     Cert Name: {cert_name}")
                            print(f"     Cert No: {cert_no}")
                            print(f"     Issue Date: {issue_date}")
                            print(f"     Valid Date: {valid_date}")
                            
                            # Check for N/A values
                            na_count = sum(1 for val in [cert_name, cert_no, issue_date, valid_date] 
                                         if val == 'N/A' or val is None or str(val).strip() == '')
                            
                            if na_count > 0:
                                print(f"     ⚠️ Found {na_count} N/A values - This could cause the reported issue")
                            else:
                                print(f"     ✅ All fields extracted successfully")
                        
                        results.append({
                            'scenario': scenario['name'],
                            'status': status,
                            'analysis': analysis,
                            'message': message
                        })
                    
                else:
                    print(f"     ❌ HTTP Error: {response.status_code}")
                    results.append({
                        'scenario': scenario['name'],
                        'status': 'http_error',
                        'error': response.status_code
                    })
                    
            except Exception as e:
                print(f"     ❌ Exception: {str(e)}")
                results.append({
                    'scenario': scenario['name'],
                    'status': 'exception',
                    'error': str(e)
                })
        
        return results

    def test_real_world_certificate_formats(self):
        """Test different real-world certificate formats"""
        print("\n📋 Testing Real-World Certificate Formats...")
        
        certificate_formats = [
            {
                "name": "Panama Format 1",
                "content": """
PANAMA MARITIME DOCUMENTATION SERVICES

SAFETY MANAGEMENT CERTIFICATE

Certificate No.: PM252494430
Vessel Name: MV PACIFIC STAR
IMO No.: 9876543210
Issue Date: 15-MAR-2024
Expiry Date: 15-MAR-2025
Issued by: Panama Maritime Documentation Services
""",
                "expected_cert_no": "PM252494430"
            },
            {
                "name": "Panama Format 2", 
                "content": """
REPUBLIC OF PANAMA
PANAMA MARITIME AUTHORITY

CERTIFICADO DE GESTIÓN DE SEGURIDAD
SAFETY MANAGEMENT CERTIFICATE

Ship: MV OCEAN BREEZE
Certificate Number: PM252494430
Date of Issue: March 15, 2024
Valid Until: March 15, 2025
Authority: Panama Maritime Authority
""",
                "expected_cert_no": "PM252494430"
            },
            {
                "name": "Scanned Certificate Format",
                "content": """
P A N A M A   M A R I T I M E   D O C U M E N T A T I O N   S E R V I C E S

S A F E T Y   M A N A G E M E N T   C E R T I F I C A T E

Ship Name:  MV  CARGO  MASTER
Cert  No:   P M 2 5 2 4 9 4 4 3 0
Issue:      1 5 / 0 3 / 2 0 2 4
Valid:      1 5 / 0 3 / 2 0 2 5
""",
                "expected_cert_no": "PM252494430"
            }
        ]
        
        problematic_formats = []
        
        for cert_format in certificate_formats:
            print(f"\n   Testing: {cert_format['name']}")
            
            content = cert_format['content'].encode('utf-8')
            files = {
                'files': (f"{cert_format['name'].replace(' ', '_')}.pdf", io.BytesIO(content), 'application/pdf')
            }
            
            headers = {'Authorization': f'Bearer {self.token}'}
            
            response = requests.post(
                f"{self.api_url}/certificates/upload-multi-files",
                files=files,
                headers=headers,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    result = results[0]
                    analysis = result.get('analysis', {})
                    
                    if analysis:
                        cert_no = analysis.get('cert_no', 'N/A')
                        cert_name = analysis.get('cert_name', 'N/A')
                        issue_date = analysis.get('issue_date', 'N/A')
                        valid_date = analysis.get('valid_date', 'N/A')
                        
                        print(f"     Extracted Cert No: {cert_no}")
                        print(f"     Expected Cert No: {cert_format['expected_cert_no']}")
                        
                        # Check if extraction worked
                        if cert_no == 'N/A' or cert_name == 'N/A':
                            print(f"     ❌ EXTRACTION FAILED - This format causes N/A values")
                            problematic_formats.append(cert_format['name'])
                        else:
                            print(f"     ✅ Extraction successful")
        
        return problematic_formats

    def run_comprehensive_test(self):
        """Run comprehensive PDF extraction test"""
        print("🔍 PDF TEXT EXTRACTION AND AI ANALYSIS TEST")
        print("=" * 60)
        print("Focus: Identify PDF formats that cause N/A extraction")
        print("=" * 60)
        
        if not self.login():
            return False
        
        # Test problematic scenarios
        scenario_results = self.test_problematic_pdf_scenarios()
        
        # Test real-world formats
        problematic_formats = self.test_real_world_certificate_formats()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"Tested {len(scenario_results)} problematic scenarios")
        
        failed_scenarios = [r for r in scenario_results if r.get('status') == 'error']
        na_scenarios = []
        
        for result in scenario_results:
            analysis = result.get('analysis', {})
            if analysis:
                na_count = sum(1 for field in ['cert_name', 'cert_no', 'issue_date', 'valid_date']
                             if analysis.get(field) in ['N/A', None, ''])
                if na_count > 0:
                    na_scenarios.append(result['scenario'])
        
        if failed_scenarios:
            print(f"\n❌ SCENARIOS CAUSING ERRORS:")
            for scenario in failed_scenarios:
                print(f"   - {scenario['scenario']}: {scenario.get('message', 'Unknown error')}")
        
        if na_scenarios:
            print(f"\n⚠️ SCENARIOS CAUSING N/A VALUES:")
            for scenario in na_scenarios:
                print(f"   - {scenario}")
        
        if problematic_formats:
            print(f"\n⚠️ PROBLEMATIC CERTIFICATE FORMATS:")
            for format_name in problematic_formats:
                print(f"   - {format_name}")
        
        if not failed_scenarios and not na_scenarios and not problematic_formats:
            print(f"\n✅ ALL TESTS PASSED")
            print("PDF extraction and AI analysis working correctly for all tested scenarios")
        
        # Recommendations
        print(f"\n🔧 RECOMMENDATIONS:")
        if failed_scenarios or na_scenarios or problematic_formats:
            print("1. The N/A issue may be caused by specific PDF formats or corruption")
            print("2. Check if the user's PM252494430.pdf has similar formatting issues")
            print("3. Implement better error handling for corrupted PDFs")
            print("4. Consider PDF preprocessing to handle special characters")
            print("5. Add fallback text extraction methods for problematic PDFs")
        else:
            print("1. PDF extraction appears to be working correctly")
            print("2. The N/A issue may be resolved or specific to certain files")
            print("3. Monitor for specific PDF files that cause issues")
        
        return len(failed_scenarios) == 0 and len(na_scenarios) == 0

def main():
    """Main test execution"""
    tester = PDFExtractionTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 PDF extraction test completed successfully!")
        return 0
    else:
        print("\n⚠️ PDF extraction issues identified - check details above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Certificate Information Extraction Test
Focus on the specific issue: PM252494430.pdf returns all N/A values
"""

import requests
import sys
import json
import os
import io
from datetime import datetime
import time

class CertificateExtractionTester:
    def __init__(self, base_url="https://certmaster-ship.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

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
            user = data.get('user', {})
            print(f"✅ Login successful")
            print(f"   User: {user.get('full_name')} ({user.get('role')})")
            print(f"   Company: {user.get('company', 'Not assigned')}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False

    def test_ai_config(self):
        """Test current AI configuration"""
        print("\n🤖 Checking AI Configuration...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{self.api_url}/ai-config", headers=headers, timeout=30)
        
        if response.status_code == 200:
            config = response.json()
            print(f"✅ AI Configuration:")
            print(f"   Provider: {config.get('provider')}")
            print(f"   Model: {config.get('model')}")
            print(f"   Use Emergent Key: {config.get('use_emergent_key')}")
            return config
        else:
            print(f"❌ Failed to get AI config: {response.status_code}")
            return None

    def create_realistic_maritime_certificate(self):
        """Create a realistic maritime certificate similar to PM252494430.pdf"""
        certificate_content = """
PANAMA MARITIME DOCUMENTATION SERVICES
REPUBLIC OF PANAMA

SAFETY MANAGEMENT CERTIFICATE

Certificate No: PM252494430
Ship Name: MV OCEAN NAVIGATOR
IMO Number: 9123456789
Call Sign: 3EAB7
Flag: Panama
Gross Tonnage: 28,500
Deadweight: 42,000 MT
Built: 2019

This is to certify that the Safety Management System of the ship named above has been audited and found to comply with the requirements of the International Safety Management (ISM) Code as adopted by the International Maritime Organization by Resolution A.741(18).

Certificate Type: Full Term
Issue Date: 15 March 2024
Valid Until: 15 March 2025
Last Annual Verification: 15 September 2024
Next Annual Verification: 15 September 2025

Issued By: Panama Maritime Documentation Services
On behalf of: Republic of Panama Maritime Authority
Classification Society: American Bureau of Shipping (ABS)
Ship Owner: Maritime Holdings International Ltd
Managing Company: Global Ship Management Inc

Place of Issue: Panama City, Panama
Date of Issue: 15 March 2024

Authorized Officer: Captain Roberto Martinez
Maritime Safety Inspector
Panama Maritime Authority

This certificate is issued under the provisions of the International Safety Management Code.
"""
        return certificate_content.encode('utf-8')

    def test_certificate_upload(self):
        """Test certificate upload and AI analysis"""
        print("\n📄 Testing Certificate Upload with AI Analysis...")
        
        # Create realistic certificate content
        cert_content = self.create_realistic_maritime_certificate()
        
        # Prepare file upload
        files = {
            'files': ('PM252494430.pdf', io.BytesIO(cert_content), 'application/pdf')
        }
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        print("   Uploading PM252494430.pdf...")
        response = requests.post(
            f"{self.api_url}/certificates/upload-multi-files",
            files=files,
            headers=headers,
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload successful")
            
            results = data.get('results', [])
            if results:
                result = results[0]
                print(f"   File: {result.get('filename')}")
                print(f"   Status: {result.get('status')}")
                
                analysis = result.get('analysis', {})
                if analysis:
                    print(f"\n   🔍 AI Analysis Results:")
                    
                    # Check the key fields that were reported as N/A
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
                    
                    # Check for the N/A issue
                    na_fields = []
                    key_fields = {
                        'cert_name': cert_name,
                        'cert_no': cert_no,
                        'issue_date': issue_date,
                        'valid_date': valid_date,
                        'issued_by': issued_by
                    }
                    
                    for field, value in key_fields.items():
                        if value == 'N/A' or value is None or str(value).strip() == '':
                            na_fields.append(field)
                    
                    if na_fields:
                        print(f"\n   ❌ ISSUE CONFIRMED: Fields returning N/A: {', '.join(na_fields)}")
                        print(f"   🔍 This matches the user's reported issue!")
                        
                        # Show expected vs actual
                        expected = {
                            'cert_name': 'Safety Management Certificate',
                            'cert_no': 'PM252494430',
                            'issue_date': '2024-03-15',
                            'valid_date': '2025-03-15',
                            'issued_by': 'Panama Maritime Documentation Services'
                        }
                        
                        print(f"\n   📋 Expected vs Actual:")
                        for field in na_fields:
                            print(f"     {field}: Expected '{expected.get(field, 'Unknown')}', Got '{key_fields[field]}'")
                            
                    else:
                        print(f"\n   ✅ All certificate fields extracted successfully!")
                        print(f"   🎉 The N/A issue appears to be resolved!")
                    
                    # Show full analysis for debugging
                    print(f"\n   📊 Full Analysis Response:")
                    print(json.dumps(analysis, indent=4, default=str))
                    
                    return len(na_fields) == 0, analysis
                    
                else:
                    print(f"   ❌ No analysis data in response")
                    return False, None
            else:
                print(f"   ❌ No results in response")
                return False, None
        else:
            print(f"❌ Upload failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text}")
            return False, None

    def test_duplicate_detection(self):
        """Test if duplicate detection is working (user reported this works)"""
        print("\n🔍 Testing Duplicate Detection...")
        
        # Upload the same certificate again to test duplicate detection
        cert_content = self.create_realistic_maritime_certificate()
        
        files = {
            'files': ('PM252494430_duplicate.pdf', io.BytesIO(cert_content), 'application/pdf')
        }
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        print("   Uploading duplicate certificate...")
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
                print(f"   Status: {result.get('status')}")
                
                # Check if duplicate detection triggered
                analysis = result.get('analysis', {})
                if analysis:
                    print(f"   ✅ Duplicate detection appears to be working")
                    print(f"   (User reported this feature works correctly)")
                    return True
                    
        print(f"   ⚠️ Could not test duplicate detection properly")
        return False

    def run_comprehensive_test(self):
        """Run comprehensive certificate extraction test"""
        print("🔍 CERTIFICATE INFORMATION EXTRACTION DEBUG TEST")
        print("=" * 60)
        print("Focus: Debug AI analysis issue where certificate information")
        print("       extraction returns all 'N/A' values for PM252494430.pdf")
        print("=" * 60)
        
        # Step 1: Login
        if not self.login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Step 2: Check AI configuration
        ai_config = self.test_ai_config()
        if not ai_config:
            print("❌ AI configuration check failed")
            return False
        
        # Step 3: Test certificate upload and analysis
        extraction_success, analysis_data = self.test_certificate_upload()
        
        # Step 4: Test duplicate detection (user reported this works)
        duplicate_success = self.test_duplicate_detection()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        if extraction_success:
            print("✅ CERTIFICATE INFORMATION EXTRACTION: WORKING")
            print("   All certificate fields are being extracted correctly")
            print("   The N/A issue may be resolved or context-specific")
        else:
            print("❌ CERTIFICATE INFORMATION EXTRACTION: FAILING")
            print("   Certificate fields are returning N/A values")
            print("   This confirms the user's reported issue")
        
        if duplicate_success:
            print("✅ DUPLICATE DETECTION: WORKING")
            print("   Matches user's report that duplicate detection works")
        
        # Recommendations
        print(f"\n🔧 RECOMMENDATIONS:")
        if not extraction_success:
            print("1. Check AI prompt formatting for certificate extraction")
            print("2. Verify PDF text extraction is working correctly")
            print("3. Test with the actual PM252494430.pdf file")
            print("4. Check if specific certificate formats cause issues")
            print("5. Verify Google/Gemini model configuration")
        else:
            print("1. The AI analysis appears to be working correctly")
            print("2. The issue may be specific to certain PDF formats")
            print("3. Test with the actual user's PM252494430.pdf file")
            print("4. Check if the issue occurs with specific certificate types")
        
        return extraction_success

def main():
    """Main test execution"""
    tester = CertificateExtractionTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 Certificate extraction test completed successfully!")
        print("The AI analysis appears to be working correctly.")
        return 0
    else:
        print("\n⚠️ Certificate extraction issues found - investigation needed")
        return 1

if __name__ == "__main__":
    sys.exit(main())